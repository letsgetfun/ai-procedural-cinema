#!/usr/bin/env bash
# 配乐链：合成 → 重定时到 1.25s 步距 → 拼成 30s
# 依赖：python(numpy, scipy) + ffmpeg
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python}"

mkdir -p out/aud

echo "[1/3] 合成原始配乐（步距 1.54s）"
"$PY" make_score30.py

echo "[2/3] 截取 8 个完整步 + 重定时（atempo 1.232 → 步距 1.25s）"
ffmpeg -hide_banner -loglevel error -y -ss 0.008 -t 12.32 -i out/score30.wav \
       -c:a pcm_s16le out/aud/seg8.wav
ffmpeg -hide_banner -loglevel error -y -i out/aud/seg8.wav \
       -af "atempo=1.232" -c:a pcm_s16le out/aud/loop10.wav

echo "[3/3] 3× 循环拼接 + 对齐自检"
"$PY" tile_audio.py

echo "OK -> out/aud/score.wav"
