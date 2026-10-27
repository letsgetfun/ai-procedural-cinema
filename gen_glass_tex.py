# -*- coding: utf-8 -*-
"""
彩窗 / 玫瑰窗 程序化贴图生成（numpy Voronoi，无外部图片依赖）
输出：glass_wall.png（竖长条彩窗）、glass_rose.png（玫瑰窗花瓣）
"""
import bpy, numpy as np, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tex")
os.makedirs(OUT, exist_ok=True)

# 圣礼拜堂式配色：深蓝紫为主，红宝石与琥珀做跳跃，少量翡翠
PALETTE = np.array([
    [0.030, 0.045, 0.230],   # 深蓝
    [0.045, 0.070, 0.330],   # 蓝
    [0.110, 0.050, 0.380],   # 紫
    [0.180, 0.045, 0.330],   # 紫红
    [0.520, 0.035, 0.075],   # 红宝石
    [0.780, 0.480, 0.080],   # 琥珀
    [0.040, 0.300, 0.170],   # 翡翠
    [0.300, 0.520, 0.850],   # 淡蓝
], dtype=np.float32)
WEIGHT = np.array([0.26, 0.14, 0.14, 0.10, 0.22, 0.08, 0.01, 0.05], dtype=np.float32)
LEAD = np.array([0.020, 0.018, 0.018], dtype=np.float32)


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


def voronoi(w, h, seeds, seed=7):
    """返回 (最近种子索引, 是否边缘)。坐标采样为像素中心"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d1 = np.full((h, w), 1e18, dtype=np.float32)
    d2 = np.full((h, w), 1e18, dtype=np.float32)
    idx = np.zeros((h, w), dtype=np.int32)
    for i, (sx, sy) in enumerate(seeds):
        d = (xx - sx) ** 2 + (yy - sy) ** 2
        m = d < d1
        d2 = np.where(m, d1, np.minimum(d2, d))
        d1 = np.where(m, d, d1)
        idx = np.where(m, i, idx)
    edge = (np.sqrt(d2 + 1e-6) - np.sqrt(d1 + 1e-6)) < 2.2
    return idx, edge


# ---------------------------------------------------------------- 竖长条彩窗
def make_wall(w=768, h=1152, ncol=20, nrow=42, seed=11):
    rng = np.random.default_rng(seed)
    seeds = []
    for c in range(ncol):
        for r in range(nrow):
            cx = (c + 0.5) * w / ncol + rng.uniform(-0.16, 0.16) * w / ncol
            cy = (r + 0.5) * h / nrow + rng.uniform(-0.16, 0.16) * h / nrow
            seeds.append((cx, cy))
    idx, edge = voronoi(w, h, seeds, seed)

    ci = rng.choice(len(PALETTE), size=len(seeds), p=WEIGHT / WEIGHT.sum())
    cols = PALETTE[ci].copy()
    # 每格亮度微扰，避免死板
    cols *= rng.uniform(0.65, 1.25, size=(len(seeds), 1)).astype(np.float32)

    rgb = cols[idx]
    # 竖向条窗的明暗节奏（模拟每扇窗的独立亮度）
    xx = np.arange(w, dtype=np.float32)[None, :] / w
    band = 0.72 + 0.28 * np.sin(xx * ncol * math.pi * 2.0 + 0.6)
    rgb *= band[:, :, None] if band.ndim == 2 else band[..., None]

    # 每格中心加一点柔光，玻璃才有"透光"的层次
    yy = np.arange(h, dtype=np.float32)[:, None] / h
    g = np.clip(1.0 - ((xx - 0.5) ** 2) * 1.6, 0.0, 1.0) * 0.25 + 0.85
    rgb *= g[..., None]

    rgb[edge] = LEAD
    save_png("glass_wall", rgb)


# ---------------------------------------------------------------- 玫瑰窗花瓣
def make_rose(size=1024, rings=(0.08, 0.20, 0.34, 0.50, 0.68, 0.84, 0.97),
              per=(4, 8, 16, 24, 32, 40, 48), seed=23):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = cy = size / 2.0
    x = (xx - cx) / (size / 2.0)
    y = (yy - cy) / (size / 2.0)
    r = np.sqrt(x * x + y * y)
    th = np.arctan2(y, x)

    # 极坐标下的种子：同心环
    seeds = [(0.0, 0.0, 0.0)]        # (r, theta, ring_index)
    for ri, (rr, nn) in enumerate(zip(rings, per)):
        for k in range(nn):
            tt = 2 * math.pi * k / nn + rng.uniform(-0.5, 0.5) * (2 * math.pi / nn) * 0.35
            seeds.append((rr + rng.uniform(-0.012, 0.012), tt, ri + 1))

    sr = np.array([s[0] for s in seeds], dtype=np.float32)
    st = np.array([s[1] for s in seeds], dtype=np.float32)
    sring = np.array([s[2] for s in seeds], dtype=np.int32)

    d1 = np.full((size, size), 1e18, dtype=np.float32)
    d2 = np.full((size, size), 1e18, dtype=np.float32)
    idx = np.zeros((size, size), dtype=np.int32)
    for i in range(len(seeds)):
        dr = r - sr[i]
        dt = np.abs(np.arctan2(np.sin(th - st[i]), np.cos(th - st[i])))
        dd = (dr * 2.2) ** 2 + (dt * np.clip(r, 0.10, 1.0)) ** 2
        m = dd < d1
        d2 = np.where(m, d1, np.minimum(d2, dd))
        d1 = np.where(m, dd, d1)
        idx = np.where(m, i, idx)
    edge = (np.sqrt(d2 + 1e-6) - np.sqrt(d1 + 1e-6)) < 0.010

    # 颜色按环：中心花心蓝白 → 内圈翡翠 → 中圈蓝 → 外圈琥珀
    ring_cols = np.array([
        [0.30, 0.45, 0.95],
        [0.10, 0.32, 0.72],
        [0.06, 0.42, 0.46],
        [0.05, 0.30, 0.70],
        [0.10, 0.24, 0.62],
        [0.72, 0.55, 0.16],
        [0.62, 0.45, 0.14],
        [0.55, 0.40, 0.12],
    ], dtype=np.float32)
    ci = np.clip(sring, 0, len(ring_cols) - 1)
    cols = ring_cols[ci] * rng.uniform(0.75, 1.20, size=(len(seeds), 1)).astype(np.float32)
    rgb = cols[idx]

    # 石制窗棂：环线 + 辐射线
    rib = np.zeros((size, size), dtype=bool)
    for rr in rings:
        rib |= np.abs(r - rr) < 0.011
    for k in range(12):
        a = 2 * math.pi * k / 12
        dth = np.abs(np.arctan2(np.sin(th - a), np.cos(th - a)))
        rib |= (dth * r < 0.017) & (r > 0.10)
    rgb[rib | edge] = LEAD

    # 圆外全黑
    rgb[r > 1.0] = 0.0
    save_png("glass_rose", rgb)


def make_tri(w=768, h=1152, nx=14, ny=24, seed=31):
    """三角面片拼接彩窗：抖动三角网格 + 铅条描边（不是 Voronoi 马赛克）"""
    rng = np.random.default_rng(seed)
    P = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = i * w / nx + rng.uniform(-0.34, 0.34) * w / nx
            y = j * h / ny + rng.uniform(-0.34, 0.34) * h / ny
            P[(i, j)] = (x, y)

    img = np.empty((h, w, 3), dtype=np.float32)
    img[:] = LEAD

    tris = []
    for j in range(ny):
        for i in range(nx):
            a, b = P[(i, j)], P[(i + 1, j)]
            c, d = P[(i + 1, j + 1)], P[(i, j + 1)]
            if rng.random() < 0.5:
                tris.append((a, b, c))
                tris.append((a, c, d))
            else:
                tris.append((a, b, d))
                tris.append((b, c, d))

    for (p0, p1, p2) in tris:
        xs = (p0[0], p1[0], p2[0])
        ys = (p0[1], p1[1], p2[1])
        x0 = max(0, int(min(xs)) - 1); x1 = min(w, int(max(xs)) + 2)
        y0 = max(0, int(min(ys)) - 1); y1 = min(h, int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        Y, X = np.mgrid[y0:y1, x0:x1]
        X = X.astype(np.float32) + 0.5
        Y = Y.astype(np.float32) + 0.5
        w0 = (X - p1[0]) * (p2[1] - p1[1]) - (Y - p1[1]) * (p2[0] - p1[0])
        w1 = (X - p2[0]) * (p0[1] - p2[1]) - (Y - p2[1]) * (p0[0] - p2[0])
        w2 = (X - p0[0]) * (p1[1] - p0[1]) - (Y - p0[1]) * (p1[0] - p0[0])
        area = w0 + w1 + w2
        if abs(area.mean()) < 1e-6:
            continue
        b0, b1, b2 = w0 / area, w1 / area, w2 / area
        inside = (b0 > 0.055) & (b1 > 0.055) & (b2 > 0.055)
        if not inside.any():
            continue
        cxp = (p0[0] + p1[0] + p2[0]) / 3.0
        cyp = (p0[1] + p1[1] + p2[1]) / 3.0
        # 不做上下色调分区：整扇窗亮度要均匀，否则下半段读成"空窗"
        k = rng.choice(len(PALETTE), p=WEIGHT / WEIGHT.sum())
        col = PALETTE[k] * 2.15 * rng.uniform(0.80, 1.20)
        col = np.clip(np.maximum(col, 0.085), 0.0, 1.0)       # 抬底线，避免出现近黑的三角
        sub = img[y0:y1, x0:x1]
        sub[inside] = col
        img[y0:y1, x0:x1] = sub

    save_png("glass_tri", img)


make_tri()
make_wall()
make_rose()
print("GLASS_TEX_DONE", OUT)
