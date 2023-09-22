from vstools import get_prop,vs

__all__ = [ "Y4mFile" ]

class Y4mFile:
    def __init__(self, name:str,node: vs.VideoNode):
        self.name = name
        frame_count = len(node)

        #https://github.com/Irrational-Encoding-Wizardry/vs-engine/blob/ddbb6284d4556c623c144f4a402e2665dccb0338/vsengine/video.py#L83
        y4mformat = ""
        if node.format.color_family == vs.GRAY:
            y4mformat = 'mono'
            if node.format.bits_per_sample > 8:
                y4mformat = y4mformat + str(node.format.bits_per_sample)
        elif node.format.color_family == vs.YUV:
            if node.format.subsampling_w == 1 and node.format.subsampling_h == 1:
                y4mformat = '420'
            elif node.format.subsampling_w == 1 and node.format.subsampling_h == 0:
                y4mformat = '422'
            elif node.format.subsampling_w == 0 and node.format.subsampling_h == 0:
                y4mformat = '444'
            elif node.format.subsampling_w == 2 and node.format.subsampling_h == 2:
                y4mformat = '410'
            elif node.format.subsampling_w == 2 and node.format.subsampling_h == 0:
                y4mformat = '411'
            elif node.format.subsampling_w == 0 and node.format.subsampling_h == 1:
                y4mformat = '440'
            if node.format.bits_per_sample > 8:
                y4mformat = y4mformat + 'p' + str(node.format.bits_per_sample)
        else:
            raise ValueError("Can only use GRAY and YUV for Y4M-Streams")

        if len(y4mformat) > 0:
            y4mformat = 'C' + y4mformat + ' '

        f0 = node.get_frame(0)
        try:
            p1 = get_prop(f0,"_SARDen",t=int)
            p2 = get_prop(f0,"_SARNum",t=int)
        
            aspen = "A{}:{}".format(p2,p1)
            #aspen = "A1:1"
        except:
            aspen = "A0:0"

        self.header = 'YUV4MPEG2 {y4mformat}W{width} H{height} F{fps_num}:{fps_den} Ip {aspen} XLENGTH={length}\n'.format(
            y4mformat=y4mformat,
            width=node.width,
            height=node.height,
            fps_num=node.fps_num,
            fps_den=node.fps_den,
            length=frame_count,
            aspen=aspen,
        ).encode("utf-8")
        
        self.y4mframheader = b"FRAME\x0A"
        #planesize = 1920 * 1080 * 1
        framesize = 0
        for p in f0:
            framesize += len(bytes(p))
        self.y4mframesize = len(self.y4mframheader) + framesize

        self.full_file_len = len(self.header) + (self.y4mframesize * len(node))
        self.cached_frame = None
        self.node = node
        self.fetch_buffer_size = f0.width * f0.height * 2 * 10 


    def read(self, offset, size):
        if True:
            y4m = self

            slen = len(y4m.header)
            origsize = size
            buf = bytearray()
            while size > 0:
                if offset + size > y4m.full_file_len:
                    size = y4m.full_file_len - offset
                if size <= 0:
                    break

                if offset < slen:
                    dedda = y4m.header[offset:min(offset+size,len(y4m.header))]
                    buf.extend(dedda)

                    offset += len(dedda)
                    size -= len(dedda)
                elif offset >= slen:
                    mm = offset - slen

                    wav_block_idx = mm // y4m.y4mframesize
                    wav_block_offset = mm % y4m.y4mframesize
                    if wav_block_offset < len(y4m.y4mframheader):
                        innerrd = y4m.y4mframheader[wav_block_offset: min(size-wav_block_offset,len(y4m.y4mframheader))]
                        buf.extend(innerrd)

                        offset += len(innerrd)
                        size -= len(innerrd)
                    else:
                        if self.cached_frame is None or self.cached_frame[0] != wav_block_idx:
                            dst: vs.VideoFrame = self.node.get_frame(wav_block_idx)
                            bb = bytearray()
                            for chunk in dst.readchunks():
                                bb.extend(chunk)
                            self.cached_frame = (wav_block_idx,bb)

                        frm = self.cached_frame[1]

                        offst = wav_block_offset - len(y4m.y4mframheader)
                        deda = frm[offst:]
                        deda = deda[:min(size,len(deda))]
                        buf.extend(deda)

                        offset += len(deda)
                        size -= len(deda)
                else:
                    break
            assert len(buf) <= origsize
            return bytes(buf)
