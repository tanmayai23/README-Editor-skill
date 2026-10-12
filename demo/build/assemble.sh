#!/usr/bin/env bash
# Builds both demo videos from the recorded clips. Run from demo/build/:  bash assemble.sh
# Inputs: ../before.mp4 sources/run.mp4 ../after.mp4 readme-scroll.mp4 card-*.png
# Outputs: ../readme-forge-demo.mp4 (README loop, silent) · ../readme-forge-demo.gif · ../readme-forge-reel.mp4 (30 s)
set -euo pipefail

# --- timings inside run.mp4 (seconds); set from the real recording
RUN_TYPE_START=${RUN_TYPE_START:-10}   # when the /readme-forge command starts being typed
RUN_TYPE_END=${RUN_TYPE_END:-15}       # command submitted
RUN_WORK_END=${RUN_WORK_END:-200}      # Claude finished
RUN_FAST=${RUN_FAST:-8}               # speed-up for the "working" part

FONT="C\\:/Windows/Fonts/segoeuib.ttf"
ENC="-c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -r 30 -an"

caption() {  # caption <in> <out> "text" [extra filters before caption]
  local in=$1 out=$2 text=$3 pre=${4:-}
  ffmpeg -v error -y -i "$in" -vf "${pre}scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x1e1e2e,fps=30,drawtext=fontfile='$FONT':text='$text':fontsize=36:fontcolor=white:box=1:boxcolor=0x0B1020@0.88:boxborderw=20:x=(w-tw)/2:y=h-th-46" $ENC "$out"
}
still() {  # still <png> <seconds> <out>
  ffmpeg -v error -y -loop 1 -framerate 30 -t "$2" -i "$1" -vf "scale=1280:720,fade=in:0:9,fade=out:st=$(python -c "print($2-0.3)"):d=0.3" $ENC "$3"
}

mkdir -p parts

# ---------- shared shots
caption ../before.mp4 parts/s_before.mp4 "Before\: 43/100"
ffmpeg -v error -y -ss "$RUN_TYPE_START" -to "$RUN_TYPE_END" -i sources/run.mp4 -an -c copy parts/run_type_raw.mp4
caption parts/run_type_raw.mp4 parts/s_type.mp4 "One command"
ffmpeg -v error -y -ss "$RUN_TYPE_END" -to "$RUN_WORK_END" -i sources/run.mp4 -an -c copy parts/run_work_raw.mp4
caption parts/run_work_raw.mp4 parts/s_work.mp4 "Reads your real code, writes, scores, fixes" "setpts=PTS/$RUN_FAST,"
caption readme-scroll.mp4 parts/s_scroll.mp4 "Full README + architecture diagram, from facts" "setpts=PTS/1.5,"
ffmpeg -v error -y -sseof -1.6 -i ../after.mp4 -an -c:v libx264 -crf 18 parts/after_tail.mp4
caption parts/after_tail.mp4 parts/s_after.mp4 "After\: 95/100" "tpad=stop_mode=clone:stop_duration=1.6,"

# ---------- A. README loop (silent)
printf "file '%s'\n" s_before.mp4 s_type.mp4 s_work.mp4 s_scroll.mp4 s_after.mp4 > parts/loop.txt
ffmpeg -v error -y -f concat -safe 0 -i parts/loop.txt $ENC -movflags +faststart ../readme-forge-demo.mp4
ffmpeg -v error -y -i ../readme-forge-demo.mp4 -vf "fps=12,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 ../readme-forge-demo.gif

# ---------- B. Cinematic reel (add music + AI clips in your editor)
still card-hook.png 3 parts/c_hook.mp4
still card-split.png 3.5 parts/c_split.mp4
still card-end.png 4 parts/c_end.mp4
printf "file '%s'\n" c_hook.mp4 s_before.mp4 s_type.mp4 s_work.mp4 s_scroll.mp4 c_split.mp4 c_end.mp4 > parts/reel.txt
ffmpeg -v error -y -f concat -safe 0 -i parts/reel.txt $ENC -movflags +faststart ../readme-forge-reel.mp4

for f in ../readme-forge-demo.mp4 ../readme-forge-demo.gif ../readme-forge-reel.mp4; do
  printf "%-28s %6.1f s  %6d KB\n" "$(basename "$f")" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")" $(( $(stat -c %s "$f") / 1024 ))
done
