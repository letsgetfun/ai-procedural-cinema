# -*- coding: utf-8 -*-
"""hero22 = hero20 + 内侧大腿解冻
原 hero9 把 |x|<0.225、z 1.00-1.345、y<-0.175 全绑给 hips（hips 不摆动）→ 腿内侧被钉死。
现在：中缝 |x|<0.055 仍归 hips（保住整体蓝三角），向外按 smoothstep 渐变回同侧 thigh。
"""
import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "hero20.blend"))
body = bpy.data.objects["AstartesBody"]
me = body.data
mw = body.matrix_world.copy()
vg = {g.name: g for g in body.vertex_groups}
g_h = vg["hips"]; g_l = vg["thigh_L"]; g_r = vg["thigh_R"]
idx_h, idx_l, idx_r = g_h.index, g_l.index, g_r.index


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


n_mid = n_blend = 0
for v in me.vertices:
    w = mw @ v.co
    if abs(w.x) >= 0.245 or not (1.00 < w.z < 1.36) or w.y >= -0.17:
        continue
    ax = abs(w.x)
    t = smooth((ax - 0.055) / 0.105)      # 0=中缝 1=大腿
    if t <= 0.002:
        n_mid += 1
        continue
    # 只处理当前挂在 hips 上的点（其余本来就在腿上，不动）
    cur = 0.0
    for g in v.groups:
        if g.group == idx_h:
            cur = g.weight
    if cur <= 0.02:
        continue
    g_h.add([v.index], cur * (1.0 - t), 'REPLACE')
    (g_l if w.x < 0 else g_r).add([v.index], cur * t, 'REPLACE')
    n_blend += 1

print("COD mid(留hips)", n_mid, " 渐变回大腿", n_blend)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "hero22.blend"))
print("SAVED hero22.blend")
