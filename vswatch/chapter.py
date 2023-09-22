from typing import *

__all__ = [ "ChapterFileInfo", "generate_chapters" ]


def generate_chapters(chapter_points: List[int],fps:float,total_frames:int) -> str:
    stra = ";FFMETADATA1\n"
    crnt = 0.0
    ii = 0
    for ii,c in enumerate(chapter_points): 
        c0 = float(c / fps)
        timebase = 100000

        endf = total_frames-1
        if ii != len(chapter_points)-1:
            endf = chapter_points[ii+1]
        start = int(( c0 ) * timebase)
        end   = int(( endf ) * timebase)

        stra += "[CHAPTER]\n"
        stra += f"TIMEBASE=1/{timebase}\n"
        stra += f"START={start}\n"
        stra += f"END={end}\n"
        stra += f"title={ii}"
        stra += "\n\n"
    ii += 1

    return stra

class ChapterFileInfo:
    def __init__(self, name: str,content: str):
        self.name = name
        self.content = content.encode("utf-8")
        self.full_file_len = len(self.content)
        self.fetch_buffer_size = 1024

    def read(self, offset, size):
        read_size = min(size, len(self.content) - offset)
        bb =  bytes(self.content[offset:offset + read_size])
        return bb

