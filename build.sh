#!/usr/bin/env bash
# 端到端构建：模型 → 贴图 → 角色版本链 → 720 帧渲染 → 配乐 → 编码
# 依赖：blender 4.5（PATH 或 BLENDER=<绝对路径>）、python(numpy,scipy)、ffmpeg
set -euo pipefail
cd "$(dirname "$0")"

BLENDER="${BLENDER:-blender}"
PY="${PYTHON:-python}"
FRAMES="${FRAMES:-720}"       # 720 = 30s @24fps
SAMPLES="${SAMPLES:-28}"

echo "== 0/6 校验模型（CC-BY-4.0，随仓库分发）"
"$PY" verify_model.py

echo "== 1/6 程序化贴图"
[ -f tex/glass_rose.png ] || "$BLENDER" -b -P gen_glass_tex.py
[ -f tex/carpet.png ]     || "$BLENDER" -b -P gen_carpet.py
[ -f tex/brocade.png ]    || "$BLENDER" -b -P gen_brocade.py

echo "== 2/6 角色版本链 hero4 → hero9 → hero20 → hero22"
[ -f hero4.blend ]  || "$BLENDER" -b -P build_hero4.py
[ -f hero9.blend ]  || "$BLENDER" -b -P build_hero9.py
[ -f hero20.blend ] || "$BLENDER" -b -P build_hero20.py
[ -f hero22.blend ] || "$BLENDER" -b -P build_hero22.py

echo "== 3/6 渲染 ${FRAMES} 帧 1080p"
mkdir -p out/frames
"$BLENDER" -b -P lux_scene.py -- \
  --anim 1 --secs 30 --fps 24 --engine EEVEE --csamples "$SAMPLES" \
  --key 620 --fill 90 --halo 1100 --nb 12 \
  --heroy 52 --herox 0 --dist 6.4 --lens 26 --camz 0.32 --aimz 2.35 \
  --armsway 0.40 \
  --outdir out/frames --fstart 1 --fend "$FRAMES"

echo "== 4/6 配乐"
bash build_audio.sh

echo "== 5/6 调色 + 编码"
ffmpeg -hide_banner -loglevel error -y \
  -framerate 24 -i out/frames/f_%04d.png \
  -i out/hald_grade.png \
  -i out/aud/score.wav \
  -filter_complex "[0:v][1:v]haldclut=interp=trilinear,vignette=PI/4.6[v];[2:a]volume=-5.6dB,alimiter=limit=0.86:level=false[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 16 -pix_fmt yuv420p -color_range tv -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  out/astartes-imperial-angel-1080p.mp4

echo "== 6/6 完成"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 out/astartes-imperial-angel-1080p.mp4
echo "见 out/astartes-imperial-angel-1080p.mp4"
