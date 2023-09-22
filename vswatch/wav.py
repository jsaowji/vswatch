import struct
import numpy as np
from enum import IntEnum
from typing import BinaryIO, Optional
from vstools import get_render_progress, vs

__all__ = [ "Wav"]


#Stolen from 
#https://github.com/Irrational-Encoding-Wizardry/vs-muxtools/blob/master/vsmuxtools/utils/audio.py
#Which 
#Most if not everything in this file is stolen from this because I don't feel like waiting for setsu to add it to vapoursynth itself.
#https://github.com/Ichunjo/vardautomation/blob/fae054956b3611e641276dc92f4a8c4060a3d8e2/vardautomation/render.py



class WaveFormat(IntEnum):
    """
    WAVE form wFormatTag IDs
    Complete list is in mmreg.h in Windows 10 SDK.
    """

    PCM = 0x0001
    IEEE_FLOAT = 0x0003
    EXTENSIBLE = 0xFFFE


class WaveHeader(IntEnum):
    """
    Wave headers
    """

    WAVE = 0
    WAVE64 = 1
    AUTO = 2


WAVE_RIFF_TAG = b"RIFF"
WAVE_WAVE_TAG = b"WAVE"
WAVE_FMT_TAG = b"fmt "
WAVE_DATA_TAG = b"data"

WAVE64_RIFF_UUID = (0x72, 0x69, 0x66, 0x66, 0x2E, 0x91, 0xCF, 0x11, 0xA5, 0xD6, 0x28, 0xDB, 0x04, 0xC1, 0x00, 0x00)
WAVE64_WAVE_UUID = (0x77, 0x61, 0x76, 0x65, 0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A)
WAVE64_FMT_UUID = (0x66, 0x6D, 0x74, 0x20, 0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A)
WAVE64_DATA_UUID = (0x64, 0x61, 0x74, 0x61, 0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A)
WAVE_FMT_EXTENSIBLE_SUBFORMAT = (
    (WaveFormat.PCM, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x80, 0x00, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71),
    (WaveFormat.IEEE_FLOAT, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x80, 0x00, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71),
)


def audio_async_render(
    audio: vs.AudioNode, outfile: BinaryIO, header: WaveHeader = WaveHeader.AUTO
) -> None:
    bytes_per_output_sample = (audio.bits_per_sample + 7) // 8
    block_align = audio.num_channels * bytes_per_output_sample
    bytes_per_second = audio.sample_rate * block_align
    data_size = audio.num_samples * block_align

    if header == WaveHeader.AUTO:
        conditions = (audio.num_channels > 2, audio.bits_per_sample > 16, audio.num_samples > 44100)
        header_func, use_w64 = (w64_header, WaveHeader.WAVE64) if any(conditions) else (wav_header, WaveHeader.WAVE)
    else:
        use_w64 = header
        header_func = (wav_header, w64_header)[header]

    outfile.write(header_func(audio, bytes_per_second, block_align, data_size))

    for f in audio.frames(close=True):
        finish_frame_audio(f, outfile, audio.bits_per_sample == 24)
    size = outfile.tell()
    if use_w64:
        outfile.seek(16)
        outfile.write(struct.pack("<Q", size))
    else:
        outfile.seek(4)
        outfile.write(struct.pack("<I", size - 8))


def wav_header(audio: vs.AudioNode, bps: int, block_align: int, data_size: int,total_file_size: int) -> bytes:
    header = WAVE_RIFF_TAG
    header += struct.pack("<I", total_file_size)
    header += WAVE_WAVE_TAG

    header += WAVE_FMT_TAG
    format_tag = WaveFormat.IEEE_FLOAT if audio.sample_type == vs.FLOAT else WaveFormat.PCM

    fmt_chunk_data = struct.pack("<HHIIHH", format_tag, audio.num_channels, audio.sample_rate, bps, block_align, audio.bits_per_sample)
    header += struct.pack("<I", len(fmt_chunk_data))
    header += fmt_chunk_data

    if len(header) + data_size > 0xFFFFFFFE:
        raise ValueError("Data exceeds wave file size limit")

    header += WAVE_DATA_TAG
    header += struct.pack("<I", data_size)
    return header


def w64_header(audio: vs.AudioNode, bps: int, block_align: int, data_size: int,total_file_size: int) -> bytes:
    header = bytes(WAVE64_RIFF_UUID)
    header += struct.pack("<Q", total_file_size)
    header += bytes(WAVE64_WAVE_UUID)
    fmt_guid = bytes(WAVE64_FMT_UUID)
    header += fmt_guid

    format_tag = WaveFormat.EXTENSIBLE

    cb_size = 22
    fmt_chunk_data = struct.pack(
        "<HHIIHHHHI",
        format_tag,
        audio.num_channels,
        audio.sample_rate,
        bps,
        block_align,
        audio.bits_per_sample,
        cb_size,
        audio.bits_per_sample,
        audio.channel_layout,
    )
    fmt_chunk_data += bytes(WAVE_FMT_EXTENSIBLE_SUBFORMAT[audio.sample_type])

    header += struct.pack("<Q", len(fmt_guid) + 8 + len(fmt_chunk_data))
    header += fmt_chunk_data

    data_uuid = bytes(WAVE64_DATA_UUID)
    header += data_uuid
    header += struct.pack("<Q", data_size + len(data_uuid) + 8)
    return header


def finish_frame_audio(frame: vs.AudioFrame, outfile: BinaryIO, _24bit: bool) -> None:
    data = np.stack([frame[i] for i in range(frame.num_channels)], axis=1)

    if _24bit:
        if data.ndim == 1:
            data.shape += (1,)
        data = (data // 2**8).reshape(data.shape + (1,)) >> np.array([0, 8, 16], np.uint32)
        outfile.write(data.ravel().astype(np.uint8).tobytes())
    else:
        outfile.write(data.ravel().view(np.int8).tobytes())

#Not stole anymore


class WavFile:
    def __init__(self, name:str, audio: vs.AudioNode):
            self.name = name
            header = WaveHeader.AUTO
            bytes_per_output_sample = (audio.bits_per_sample + 7) // 8
            block_align = audio.num_channels * bytes_per_output_sample
            bytes_per_second = audio.sample_rate * block_align
            data_size = audio.num_samples * block_align

            if header == WaveHeader.AUTO:
                conditions = (audio.num_channels > 2, audio.bits_per_sample > 16, audio.num_samples > 44100)
                header_func, use_w64 = (w64_header, WaveHeader.WAVE64) if any(conditions) else (wav_header, WaveHeader.WAVE)
            else:
                use_w64 = header
                header_func = (wav_header, w64_header)[header]

            self.header = header_func(audio, bytes_per_second, block_align, data_size,123)
            self.total_filesize = data_size + len(self.header)
            self.header = header_func(audio, bytes_per_second, block_align,data_size, len(self.header) + data_size)

            self.block_align = block_align
            self.bytes_per_output_sample = bytes_per_output_sample

            self.full_file_len = self.total_filesize

            self.node = audio
            self.fetch_buffer_size = 1024 * 32

    def read(self, offset,size):
        origsize = size

        if True:
            wav = self
            buf = bytearray()

            slen = len(wav.header)

            while size>0:
                if offset + size > wav.total_filesize:
                    size = wav.total_filesize - offset
                if size <= 0:
                    break
                if offset < slen:
                    dedda = wav.header[offset:min(offset+size,len(wav.header))]
                    buf.extend(dedda)

                    offset += len(dedda)
                    size -= len(dedda)
                elif offset >= slen:
                    mm = offset - slen

                    wav_block_idx = mm // wav.block_align
                    wav_block_offset = mm % wav.block_align

                    import io
                    vs_frame_idx = wav_block_idx // 3072
                    vs_framediscard = wav_block_idx % 3072

                    vs_frame = self.node.get_frame(vs_frame_idx)

                    bufer = io.BytesIO()
                    finish_frame_audio(vs_frame, bufer, False)#audio.bits_per_sample == 24)

                    bufer = bufer.getvalue()
                    dedda = bufer
                    dedda = dedda[wav_block_offset:]
                    dedda = dedda[vs_framediscard * wav.block_align:]

                    dedda = dedda[:min(size,len(dedda))]
                 #   assert len(dedda) != 0

                    buf.extend(dedda)

                    offset += len(dedda)
                    size -= len(dedda)
                else:
                    assert False

            assert len(buf) <= origsize
            #assert len(buf) == origsize
        
            return bytes(buf)

