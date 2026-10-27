# -*- coding: utf-8 -*-
"""hero20 = hero9 + 膝骨（poleyn_L/R）
膝骨：与 shin 同朝向、父级 thigh、渲染时取 shin 屈曲的一半，
     膝关节带（z 0.68–1.04）权重按平滑斜坡转移给它。
"""
import bpy, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "hero9.blend"))

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
ob = max([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: len(o.data.vertices))
print("ARM", arm.name, "MESH", ob.name, len(ob.data.vertices))

# ---------------- 1) 加膝骨
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for side in ("L", "R"):
    sh, th = eb["shin_" + side], eb["thigh_" + side]
    nm = "poleyn_" + side
    if nm in eb:
        eb.remove(eb[nm])
    nb = eb.new(nm)
    nb.head = sh.head.copy()
    nb.tail = sh.head + (sh.tail - sh.head).normalized() * 0.12
    nb.roll = sh.roll
    nb.parent = th
    nb.use_connect = False
    print("BONE %s head=%s dir=%s roll=%.3f" % (nm, tuple(round(v, 3) for v in nb.head),
          tuple(round(v, 3) for v in (sh.tail - sh.head).normalized()), nb.roll))
bpy.ops.object.mode_set(mode='OBJECT')


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ---------------- 2) 膝盖带权重转移
tot_moved = 0
for side, sx in (("L", -1), ("R", 1)):
    g_th = ob.vertex_groups["thigh_" + side]
    g_sh = ob.vertex_groups["shin_" + side]
    gp = ob.vertex_groups.new(name="poleyn_" + side)
    moved = 0
    for v in ob.data.vertices:
        if v.co.x * sx <= 0.08:
            continue
        z = v.co.z
        if z < 0.68 or z > 1.04:
            continue
        tw = sw = 0.0
        for g in v.groups:
            if g.group == g_th.index:
                tw = g.weight
            elif g.group == g_sh.index:
                sw = g.weight
        if tw + sw < 0.20:
            continue
        if z < 0.80:
            w = smooth((z - 0.68) / 0.12)
        elif z <= 0.90:
            w = 1.0
        else:
            w = smooth((1.04 - z) / 0.14)
        if w <= 0.001:
            continue
        gp.add([v.index], w, 'REPLACE')
        g_th.add([v.index], tw * (1.0 - w), 'REPLACE')
        g_sh.add([v.index], sw * (1.0 - w), 'REPLACE')
        moved += 1
    print("WEIGHTS %s moved=%d" % (side, moved))
    tot_moved += moved

print("TOTAL_MOVED", tot_moved)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "hero20.blend"))
print("SAVED hero20.blend")
