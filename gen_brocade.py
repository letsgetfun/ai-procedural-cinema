# -*- coding: utf-8 -*-
"""红丝绒织花贴图（程序化）：深红底 + 金线缠枝纹 + 菱形格"""
import bpy, numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tex")
os.makedirs(OUT, exist_ok=True)
S = 512
x = np.linspace(0, 1, S, endpoint=False)
u, v = np.meshgrid(x, x)
a = np.abs(u * 2 - 1); b = np.abs(v * 2 - 1)
r = np.sqrt(a * a + b * b)
th = np.arctan2(b, a)
# 中心玫瑰花
ring = np.exp(-((r - 0.42) / 0.055) ** 2) * (0.55 + 0.45 * np.cos(8 * th))
core = np.exp(-(r / 0.16) ** 2) * 0.9
# 缠枝：极坐标谐波
vine = 0.5 + 0.5 * np.cos(6 * th + 9 * r)
vine = np.exp(-((r - 0.68) / 0.08) ** 2) * vine ** 3
# 菱形格
lat = np.abs(np.sin(np.pi * (a + b))) * np.abs(np.sin(np.pi * (a - b)))
lat = lat ** 4
# 四角小卷草
corner = np.exp(-(((a - 0.90) ** 2 + (b - 0.90) ** 2) / 0.010))
f = np.clip(ring * 1.15 + core + vine * 0.85 + lat * 0.5 + corner * 0.8, 0, 1)
f = f ** 0.85
base = np.array([0.215, 0.024, 0.032])
gold = np.array([0.66, 0.46, 0.16])
rgb = base[None, None, :] + (gold - base)[None, None, :] * np.clip(f * 1.35, 0, 1)[..., None]
# 细噪（丝绒绒毛）
rng = np.random.default_rng(7)
rgb *= (0.94 + 0.12 * rng.random((S, S, 1)))
img = bpy.data.images.new("brocade", S, S, alpha=False)
rgba = np.ones((S, S, 4), dtype=np.float32)
rgba[:, :, :3] = np.clip(rgb, 0, 1)
img.pixels.foreach_set(rgba.ravel())
p = os.path.join(OUT, "brocade.png")
img.filepath_raw = p; img.file_format = 'PNG'; img.save()
print("BROCADE_SAVED", p)
