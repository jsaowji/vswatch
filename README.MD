# vswatch

Serves vapoursynth scipt audio and video outputs over http as .y4m and .wav for consumption by mpv.
Automatically launches mpv with all output audio/video nodes.
Special output index can support chapter also.  
Only supports constant format consant framerate.
SAR obtained from frame 0

Probably not http spec conform.

## Example

```
python -m vswatch <script> [argument selection passed to script]
```