"""Merge the AI "before/after" shots with the tutorial footage into one cinematic film.

Run from demo/build/ after assemble.sh:   python cinematic.py
Output: ../readme-forge-cinematic.mp4  (1280x720, 30 fps, AAC audio)
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI_BEFORE = Path("sources/ai-before.mp4")   # rainy night, frustrated
AI_AFTER = Path("sources/ai-after.mp4")    # golden hour, smiling
OUT = Path("../readme-forge-cinematic.mp4")
ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30"]


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


# ---------- 1. AI shots: trim, 30 fps, slow push-in, text overlay fading in/out
def ai_shot(src, start, length, overlay, out, text_in, text_out, zoom=0.07):
    vf = (f"[0:v]trim={start}:{start + length},setpts=PTS-STARTPTS,fps=30,"
          f"scale=w='trunc(1280*(1+{zoom}*t/{length})/2)*2':h=-2:eval=frame,crop=1280:720,setsar=1[v];"
          f"[1:v]format=rgba,fade=in:st={text_in}:d=0.6:alpha=1,fade=out:st={text_out}:d=0.5:alpha=1[o];"
          f"[v][o]overlay=0:0:shortest=1,format=yuv420p")
    run(["-i", str(src), "-loop", "1", "-framerate", "30", "-t", str(length), "-i", overlay,
         "-filter_complex", vf, "-t", str(length), *ENC, "-an", out])


Path("cine").mkdir(exist_ok=True)
ai_shot(AI_BEFORE, 0.4, 5.5, "ov-hook.png", "cine/a_before.mp4", text_in=0.9, text_out=4.8)
# the after shot pulls OUT (zoom from 107% to 100%) for an "exhale" feel
vf_after = ("[0:v]trim=0.2:5.7,setpts=PTS-STARTPTS,fps=30,"
            "scale=w='trunc(1280*(1.07-0.07*t/5.5)/2)*2':h=-2:eval=frame,crop=1280:720,setsar=1[v];"
            "[1:v]format=rgba,fade=in:st=1.0:d=0.6:alpha=1,fade=out:st=4.9:d=0.5:alpha=1[o];"
            "[v][o]overlay=0:0:shortest=1,format=yuv420p")
run(["-i", str(AI_AFTER), "-loop", "1", "-framerate", "30", "-t", "5.5", "-i", "ov-after.png",
     "-filter_complex", vf_after, "-t", "5.5", *ENC, "-an", "cine/a_after.mp4"])

# ---------- 2. Timeline: (clip, transition INTO the next clip, transition length)
timeline = [
    ("cine/a_before.mp4", "fade", 0.6),
    ("parts/s_before.mp4", "fade", 0.15),
    ("parts/s_type.mp4", "fade", 0.15),
    ("parts/s_work.mp4", "slideleft", 0.35),
    ("parts/s_scroll.mp4", "fade", 0.4),
    ("parts/c_split.mp4", "fadewhite", 0.5),
    ("cine/a_after.mp4", "fade", 0.6),
    ("parts/c_end.mp4", None, 0),
]
durs = [dur(c) for c, _, _ in timeline]

inputs, chain, starts = [], [], []
t = 0.0
for i, (clip, _, _) in enumerate(timeline):
    inputs += ["-i", clip]
    starts.append(t)
    if i < len(timeline) - 1:
        t += durs[i] - timeline[i][2]
total = starts[-1] + durs[-1]

prev = "[0:v]"
offset = 0.0
for i in range(1, len(timeline)):
    trans, tlen = timeline[i - 1][1], timeline[i - 1][2]
    offset = starts[i]
    label = f"[x{i}]"
    chain.append(f"{prev}[{i}:v]xfade=transition={trans}:duration={tlen}:offset={offset:.3f}{label}")
    prev = label
video_graph = ";".join(chain)

# ---------- 3. Audio: real Veo ambience + rain bed under the terminal part + two low hits
i_before, i_term_end = starts[0], starts[5]          # rain from film start until the 43→95 card
i_split, i_after, i_end = starts[5], starts[6], starts[7]
n = len(timeline)
audio_inputs = ["-stream_loop", "3", "-i", str(AI_BEFORE), "-i", str(AI_AFTER)]
A_BEFORE, A_AFTER = n, n + 1
S1 = starts[1]  # first terminal shot: rain goes muffled + quieter here
audio = [
    # rain bed: Veo ambience (~-45 LUFS, so +18 dB), looped, until the 43→95 card
    f"[{A_BEFORE}:a]atrim=0.4,asetpts=PTS-STARTPTS,volume=18dB,atrim=0:{i_term_end + 0.6:.2f},asplit[ra][rb]",
    f"[ra]volume='clip(({S1:.2f}+0.5-t)/0.5,0,1)':eval=frame[rfull]",
    f"[rb]lowpass=f=2200,volume='0.45*clip((t-{S1:.2f})/0.5,0,1)':eval=frame[rmuff]",
    f"[rfull][rmuff]amix=inputs=2:normalize=0,afade=t=in:d=0.8,afade=t=out:st={i_term_end - 0.4:.2f}:d=1.0[rain]",
    # warm ambience from the after shot through the end card
    f"[{A_AFTER}:a]atrim=0.2,asetpts=PTS-STARTPTS,volume=20dB,afade=t=in:d=0.6,"
    f"afade=t=out:st={total - i_after - 1.5:.2f}:d=1.5,atrim=0:{total - i_after:.2f},adelay={int(i_after * 1000)}:all=1[warm]",
    # low "impact" on the 43→95 reveal and a softer one on the end card
    f"sine=f=52:d=1.6,afade=t=out:st=0:d=1.6,volume=0.55,adelay={int((i_split + 0.15) * 1000)}:all=1[hit1]",
    f"sine=f=65:d=1.2,afade=t=out:st=0:d=1.2,volume=0.30,adelay={int((i_end + 0.2) * 1000)}:all=1[hit2]",
    f"[rain][warm][hit1][hit2]amix=inputs=4:normalize=0:duration=longest,"
    f"atrim=0:{total:.2f},alimiter=limit=0.89,aformat=sample_rates=48000:channel_layouts=stereo[aout]",
]

graph = video_graph + ";" + ";".join(audio)
run([*inputs, *audio_inputs, "-filter_complex", graph, "-map", prev, "-map", "[aout]",
     *ENC, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(OUT)])

print(f"{OUT.name}: {dur(OUT):.1f} s, {OUT.stat().st_size // 1024} KB")
for (clip, tr, tl), s in zip(timeline, starts):
    print(f"  {s:5.2f}s  {Path(clip).name:<16} -> {tr or 'end'} {tl}")
