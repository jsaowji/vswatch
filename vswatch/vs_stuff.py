from typing import List
from vstools import core,vs
from vsengine.vpy import script, variables
from vsengine.policy import Policy,GlobalStore

from .chapter import *
from .wav import WavFile
from .y4m import Y4mFile

__all__ = [ "load_script" ]

def load_script(scriptfile: str, selection: str) -> List[object]:
    env = variables({ "selection" : selection }).result()
    env2 = script(scriptfile,environment=env).result()
    #print(env.get_variable("chapter_points").result())
    #print(env2.get_variable("chapter_points").result())

    files = []

    videos = 0
    audios = 0

    v0 = None
    for k,v in vs.get_outputs().items():
        if k == 1337:
            import json
            points = json.loads(v.clip.get_frame(0).props["chapter_points"])
            stra = generate_chapters(points, float(v0.fps),len(v0))
            files += [ChapterFileInfo("0.ffmetadata",stra)]
        elif isinstance(v,vs.VideoOutputTuple):
            files += [ Y4mFile("{}.y4m".format(videos),v.clip) ]
            videos += 1
            if k == 0:
                v0 = v.clip
        elif isinstance(v,vs.AudioNode):
            files += [ WavFile("{}.wav".format(audios),v) ]
            audios += 1

    return files