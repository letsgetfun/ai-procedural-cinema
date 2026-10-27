# -*- coding: utf-8 -*-
"""hero9 = hero4 + 握拳(含拇指) + 裆部三角改绑 hips"""
import bpy, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "hero4.blend"))
body = bpy.data.objects["AstartesBody"]
me = body.data
mw = body.matrix_world.copy(); inv = mw.inverted()

# ---------- 1) 握拳：指根以下的顶点向掌心连续收拢 ----------
ZK, ZB = 1.335, 1.175
C = Vector((0.655, -0.145, 1.275))
n_f = 0
for v in me.vertices:
    w = mw @ v.co
    if abs(w.x) < 0.555 or w.z > ZK or w.z < 1.02:
        continue
    t = max(0.0, min(1.0, (ZK - w.z) / (ZK - ZB)))
    k = 0.90 * (t ** 1.1)
    c = Vector((math.copysign(C.x, w.x), C.y, C.z))
    v.co = inv @ w.lerp(c, k)
    n_f += 1

# ---------- 1b) 拇指：单独朝掌心再收一次 ----------
n_t = 0
for v in me.vertices:
    w = mw @ v.co
    if abs(w.x) < 0.50 or abs(w.x) > 0.625 or w.z > 1.36 or w.z < 1.15 or w.y > -0.20:
        continue
    c = Vector((math.copysign(0.60, w.x), -0.16, 1.255))
    v.co = inv @ (w.lerp(c, 0.55))
    n_t += 1
me.update()
print("FIST verts", n_f, "THUMB verts", n_t)

# ---------- 2) 裆部三角：改绑 hips ----------
gi = {g.name: g.index for g in body.vertex_groups}
vg_hips = body.vertex_groups["hips"]
n_c = 0
zs = []
for v in me.vertices:
    w = mw @ v.co
    if abs(w.x) < 0.225 and 1.00 < w.z < 1.345 and w.y < -0.175:
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        vg_hips.add([v.index], 1.0, 'REPLACE')
        n_c += 1; zs.append(w.z)
print("CODpiece rebound", n_c, "z", round(min(zs),3) if zs else 0, round(max(zs),3) if zs else 0)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "hero9.blend"))
print("SAVED hero9.blend")
