# -*- coding: utf-8 -*-
"""红丝绒金边地毯贴图（程序化）：深红绒面 + 两道金边菱格纹 + 暗花"""
import bpy, numpy as np, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tex")
os.makedirs(OUT, exist_ok=True)


def save_png(name, rgb):
    h, w, _ = rgb.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(rgba.ravel())
    p = os.path.join(OUT, name + ".png")
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    print("TEX_SAVED", p, w, "x", h)


def make_carpet(w=640, h=2816, seed=91):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx / w          # 横向 0..1
    v = yy / h          # 纵向 0..1

    # 绒面底色：深红，带低频斑驳
    base = np.empty((h, w, 3), dtype=np.float32)
    base[:] = (0.205, 0.013, 0.018)

    cell = 16
    low = rng.normal(0, 1, (h // cell + 2, w // cell + 2)).astype(np.float32)
    low = np.repeat(np.repeat(low, cell, 0), cell, 1)[:h, :w]
    base *= (1.0 + 0.13 * low)[..., None]

    # 细绒噪点
    fine = rng.normal(0, 1, (h, w)).astype(np.float32)
    base *= (1.0 + 0.045 * fine)[..., None]

    # 场内心：暗金缠枝（很淡），用小尺度菱形格
    du = np.abs(((u * 7.0) % 1.0) - 0.5)
    dv = np.abs(((v * 30.0) % 1.0) - 0.5)
    dam = np.clip((0.52 - (du + dv * 0.55)) * 3.0, 0.0, 1.0)
    base += dam[..., None] * np.array([0.075, 0.052, 0.018], np.float32)

    # 两道金边：外沿 + 内沿各一条细金线，中间是菱格花纹
    GOLD = np.array([0.560, 0.365, 0.086], np.float32)
    GOLD_HI = np.array([0.860, 0.660, 0.230], np.float32)

    def paint_band(u0, u1):
        m = (u > u0) & (u < u1)
        uc = (u - u0) / (u1 - u0)
        # 菱格：横向 3 列、纵向按比例
        a = np.abs(((uc * 3.0) % 1.0) - 0.5) * 2.0
        b = np.abs(((v * 44.0) % 1.0) - 0.5) * 2.0
        dia = (a + b) < 1.0
        c = np.where(dia, 1.0, 0.42)[..., None]
        base[m] = (GOLD * c)[m]

    paint_band(0.055, 0.145)
    paint_band(0.855, 0.945)

    for uu in (0.048, 0.152, 0.848, 0.952):
        m = np.abs(u - uu) < 0.0035
        base[m] = GOLD_HI

    # 两端收边
    for vv in (0.0, 1.0):
        m = np.abs(v - vv) < 0.004
        base[m] = GOLD_HI

    save_png("carpet", base)


make_carpet()
print("CARPET_DONE", OUT)
