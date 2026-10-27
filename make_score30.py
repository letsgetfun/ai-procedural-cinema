# -*- coding: utf-8 -*-
"""30s 配乐：D 小调管风琴持续音 + 与 2.6s 步态循环同步的重甲落脚声"""
import numpy as np, wave, os
from scipy.signal import butter, lfilter, fftconvolve

SR = 48000
DUR = 30.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def bp(x, lo, hi, o=2):
    b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], btype='band')
    return lfilter(b, a, x)


def lp(x, f, o=2):
    b, a = butter(o, f / (SR / 2), btype='low')
    return lfilter(b, a, x)


def hp(x, f, o=2):
    b, a = butter(o, f / (SR / 2), btype='high')
    return lfilter(b, a, x)


# ---------------------------------------------------------------- 管风琴
mus = np.zeros(N)
notes = [(73.42, 0.42), (110.00, 0.30), (146.83, 0.22),
         (174.61, 0.15), (220.00, 0.10), (293.66, 0.05)]
for f0, amp in notes:
    for det in (-0.35, 0.0, 0.35):
        f = f0 * (1 + det / 100.0)
        ph = rng.uniform(0, 2 * np.pi)
        mus += amp * np.sin(2 * np.pi * f * t + ph)
# 缓慢呼吸 + 整体淡入淡出
lfo = 0.80 + 0.20 * np.sin(2 * np.pi * 0.055 * t + 0.7)
mus *= lfo
fade = np.ones(N)
fi = int(3.0 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 1.6
fo = int(3.5 * SR)
fade[-fo:] = np.linspace(1, 0, fo) ** 1.3
mus *= fade
mus = np.tanh(mus * 1.25) / 1.25          # 软饱和，加"管风琴管"的厚
mus = lp(mus, 5200)
mus *= 0.42

# ---------------------------------------------------------------- 落脚声
CYCLE = 3.08
step_times = []
k = 0
while k * (CYCLE / 2) < DUR - 0.6:
    step_times.append(k * (CYCLE / 2))
    k += 1

steps = np.zeros(N)
for i, st in enumerate(step_times):
    s0 = int(st * SR)
    if s0 >= N:
        continue
    L = int(0.55 * SR)
    n = min(L, N - s0)
    tt = np.arange(n) / SR
    # 低频冲击
    thump = np.sin(2 * np.pi * (48 + 26 * np.exp(-tt * 26)) * tt) * np.exp(-tt * 9.0)
    # 装甲金属声（短促高频）
    clank = bp(rng.normal(0, 1, n), 1400, 4200) * np.exp(-tt * 60) * 0.30
    # 鞋底摩擦（中频噪声）
    scuff = bp(rng.normal(0, 1, n), 240, 1100) * np.exp(-tt * 22) * 0.55
    hit = thump * 1.0 + clank + scuff
    side = 1.0 if i % 2 == 0 else 0.82     # 左右脚轻微差异
    steps[s0:s0 + n] += hit * 0.55 * side

steps = hp(steps, 32)
steps *= 0.55

# ---------------------------------------------------------------- 混响（暗尾巴）
ir_len = int(2.8 * SR)
ir = rng.normal(0, 1, ir_len) * np.exp(-np.arange(ir_len) / (0.62 * SR))
ir = lp(ir, 3200)
ir /= np.sqrt((ir ** 2).sum())
wet_steps = fftconvolve(steps, ir)[:N] * 0.55
wet_mus = fftconvolve(mus, ir)[:N] * 0.22

mix = mus + steps + wet_steps + wet_mus
mix = hp(mix, 30)
mix = lp(mix, 15500)

# 归一化
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.82
mix = np.tanh(mix * 1.02) * 0.95

pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "score30.wav")
stereo = np.stack([pcm, pcm], axis=1)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print("WAV", out, "steps", len(step_times), "dur", DUR)
