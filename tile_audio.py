# -*- coding: utf-8 -*-
"""把 10s 的循环段拼成 30s 配乐，脚步锁在 1.25s 网格上。

输入：out/aud/loop10.wav   (10.0s，脚step 间隔 1.25s)
输出：out/aud/score.wav    (30.0s，24 次脚步，-14 LUFS 附近)

做法：3 份拷贝，间隔固定 10.0s（保持网格），接缝 40ms 等功率交叉淡化
     —— 接缝两侧是同相位的同一次脚步，混合后不会出现双击。
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, find_peaks, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "aud")
SRC = os.path.join(OUT, "loop10.wav")
DST = os.path.join(OUT, "score.wav")

TOTAL = 30.0
STEP = 10.0        # 循环间隔（秒）
XFADE = 0.040      # 交叉淡化
FADE_IN = 0.015
FADE_OUT = 1.30


def main():
    sr, seg = wavfile.read(SRC)
    seg = seg.astype(np.float32) / 32768.0
    if seg.ndim == 1:
        seg = np.stack([seg, seg], 1)

    n = int(TOTAL * sr)
    xf = int(XFADE * sr)
    out = np.zeros((n, 2), np.float32)

    for k in range(int(round(TOTAL / STEP))):
        st = int(round(k * STEP * sr))
        if k == 0:
            take = min(seg.shape[0], n - st)
            out[st:st + take] += seg[:take]
            continue
        head = min(xf, n - st)
        prev = st - head
        ramp = np.linspace(0.0, 1.0, head)[:, None]
        out[prev:prev + head] *= 1.0 - ramp
        out[st:st + head] += seg[:head] * ramp
        take = min(seg.shape[0] - head, n - (st + head))
        out[st + head:st + head + take] += seg[head:head + take]

    fi = int(FADE_IN * sr)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(FADE_OUT * sr)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]

    out = out / (np.abs(out).max() + 1e-9) * 0.95
    out = np.tanh(out * 1.05) / 1.05
    out *= 0.84 / np.abs(out).max()

    os.makedirs(OUT, exist_ok=True)
    wavfile.write(DST, sr, (out * 32767).astype(np.int16))

    # ---- 自检：脚步是否落在 1.25s 网格
    m = out.mean(1)
    sos = butter(3, [1500 / (sr / 2), 7000 / (sr / 2)], btype="band", output="sos")
    env = np.abs(sosfilt(sos, m))
    k = int(0.005 * sr)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    pk, _ = find_peaks(env, distance=int(0.6 * sr), height=env.max() * 0.10)
    t = pk / sr
    print("written:", DST)
    print("impacts: %d   first %.3f" % (len(t), t[0] if len(t) else -1))
    if len(t) > 1:
        print("mean interval: %.4f s" % np.diff(t).mean())
        print("max deviation from 1.25s grid: %.3f s" % (t % 1.25).max())


if __name__ == "__main__":
    main()
