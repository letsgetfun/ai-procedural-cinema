# -*- coding: utf-8 -*-
"""
阿斯塔特 v3：Objaverse「Space Marine」270k 面 / 10 张 PBR 贴图 / A 字站姿
保留原贴图（战损、鹰徽、白肩甲都是贴图做的，程序化复刻不了）。
刚性绑骨：每块甲片壳体整体绑一根骨；跨关节大块走软权重。
手臂不单独绑（跟着 chest），动力甲行进手臂本来就不摆。
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "model", "SM_tex270k.glb")
OUT = os.path.join(HERE, "hero4.blend")
HEIGHT = 2.78

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("IMPORTED meshes", len(meshes))
for o in bpy.context.view_layer.objects:
    o.select_set(False)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "AstartesBody"
print("JOINED verts", len(body.data.vertices), "polys", len(body.data.polygons),
      "mats", len(body.data.materials), "uv", [u.name for u in body.data.uv_layers])

# 先把顶层空物体的变换烤进网格
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o.type == 'EMPTY']:
    bpy.data.objects.remove(o, do_unlink=True)

def sample(step=29):
    n = len(body.data.vertices)
    return [body.matrix_world @ body.data.vertices[i].co for i in range(0, n, step)]

vs = sample()
zs = [p.z for p in vs]; xs = [p.x for p in vs]; ys = [p.y for p in vs]
s = HEIGHT / (max(zs) - min(zs))
body.scale = (s, s, s)
bpy.context.view_layer.update()
vs = sample()
zs = [p.z for p in vs]; xs = [p.x for p in vs]; ys = [p.y for p in vs]
body.location = (-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
_n = len(body.data.vertices)
allz = [body.data.vertices[i].co.z for i in range(0, _n, 7)]
print("NORM z %.3f..%.3f" % (min(allz), max(allz)))

# ---------------------------------------------------------------- 壳体
me = body.data
nv = len(me.vertices)
par = list(range(nv))
def find(a):
    r = a
    while par[r] != r:
        r = par[r]
    while par[a] != r:
        par[a], a = r, par[a]
    return r
for e in me.edges:
    a, b = e.vertices
    ra, rb = find(a), find(b)
    if ra != rb:
        par[ra] = rb
groups = {}
for i in range(nv):
    groups.setdefault(find(i), []).append(i)
print("ISLANDS", len(groups))

BONES = [
    ("root",    (0, 0, 0.00), (0, 0, 0.18), None),
    ("hips",    (0, 0, 1.44), (0, 0, 1.66), "root"),
    ("spine",   (0, 0, 1.66), (0, 0, 1.94), "hips"),
    ("chest",   (0, 0, 1.94), (0, 0, 2.26), "spine"),
    ("head",    (0, 0, 2.32), (0, 0, 2.66), "chest"),
    ("thigh_L", (-0.22, 0, 1.45), (-0.24, 0, 0.85), "hips"),
    ("shin_L",  (-0.24, 0, 0.85), (-0.25, 0, 0.30), "thigh_L"),
    ("foot_L",  (-0.25, 0, 0.30), (-0.25, -0.34, 0.12), "shin_L"),
    ("thigh_R", (0.22, 0, 1.45), (0.24, 0, 0.85), "hips"),
    ("shin_R",  (0.24, 0, 0.85), (0.25, 0, 0.30), "thigh_R"),
    ("foot_R",  (0.25, 0, 0.30), (0.25, -0.34, 0.12), "shin_R"),
    # 手臂：上臂 + 前臂（肘关节）。肩甲仍归 chest，动力甲行进时肩甲基本不动
    ("uparm_L",    (-0.46, 0, 2.02), (-0.50, 0, 1.58), "chest"),
    ("forearm_L",  (-0.50, 0, 1.58), (-0.52, -0.06, 1.16), "uparm_L"),
    ("uparm_R",    (0.46, 0, 2.02), (0.50, 0, 1.58), "chest"),
    ("forearm_R",  (0.50, 0, 1.58), (0.52, -0.06, 1.16), "uparm_R"),
]
arm = bpy.data.armatures.new("MarineRig")
rig = bpy.data.objects.new("MarineRig", arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for nm, hd, tl, p in BONES:
    b = arm.edit_bones.new(nm)
    b.head = Vector(hd); b.tail = Vector(tl); b.roll = 0.0
    if p:
        b.parent = arm.edit_bones[p]
        b.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')

def bone_for(cx, cy, cz):
    ax = abs(cx)
    side = "L" if cx < 0 else "R"
    # 手臂区（|x| 大且在中段高度）：肩甲以上归 chest，再往下分上臂/前臂
    if ax > 0.44 and 1.02 < cz < 2.30:
        if cz > 1.88:
            return "chest"          # 肩甲：留给躯干，避免肩甲跟着手臂甩
        if cz > 1.50:
            return f"uparm_{side}"
        return f"forearm_{side}"
    if cz > 2.28 and ax < 0.27:
        return "head"
    if ax > 0.33 and cz > 1.50:
        return "chest"          # 手臂 / 肩甲
    if cz > 1.95:
        return "chest"
    if cz > 1.66:
        return "spine"
    if cz > 1.45:
        return "hips"
    if cz > 0.85:
        return f"thigh_{side}"
    if cz > 0.30:
        return f"shin_{side}"
    return f"foot_{side}"

JOINTS = [(0.30, "foot", "shin"), (0.85, "shin", "thigh"), (1.45, "thigh", "hips"),
          (1.66, "hips", "spine"), (1.94, "spine", "chest"), (2.28, "chest", "head")]
BAND = 0.20

def soft_weights(x, z):
    side = "L" if x < 0 else "R"
    def nm(b):
        return f"{b}_{side}" if b in ("foot", "shin", "thigh") else b
    level = sum(1 for jz, _, _ in JOINTS if z > jz)
    names = ["foot", "shin", "thigh", "hips", "spine", "chest", "head"]
    for jz, lo, hi in JOINTS:
        d = z - jz
        if abs(d) < BAND:
            t = (d + BAND) / (2 * BAND)
            return {nm(lo): 1.0 - t, nm(hi): t}
    return {nm(names[level]): 1.0}

co = [v.co for v in me.vertices]
assign = {}
counts = {}
split_n = 0
for root_i, idxs in groups.items():
    n = len(idxs)
    step = max(1, n // 30)
    sub = idxs[::step]
    cx = sum(co[i].x for i in sub) / len(sub)
    cy = sum(co[i].y for i in sub) / len(sub)
    cz = sum(co[i].z for i in sub) / len(sub)
    zs_i = [co[i].z for i in sub]
    zlo, zhi = min(zs_i), max(zs_i)
    ax_i = abs(cx)
    # 手臂壳体：整块刚性绑，不能走 z 向软权重（否则会被分到 hips/thigh）
    # 低处阈值放宽到 0.52，避开大腿甲（大腿甲最外到 |x|≈0.44）
    is_arm = (zlo > 1.02) and ((cz > 1.50 and ax_i > 0.44) or (cz <= 1.50 and ax_i > 0.52))
    if is_arm:
        b = bone_for(cx, cy, cz)
        assign[root_i] = b
        counts[b] = counts.get(b, 0) + 1
    elif zhi - zlo > 0.12 and any(zlo + 0.02 < jz < zhi - 0.02 for jz, _, _ in JOINTS):
        assign[root_i] = None
        split_n += 1
    else:
        b = bone_for(cx, cy, cz)
        assign[root_i] = b
        counts[b] = counts.get(b, 0) + 1
print("ISLAND_BONES", {k: v for k, v in sorted(counts.items())})
print("SPLIT_ISLANDS", split_n)

for nm, _, _, _ in BONES:
    body.vertex_groups.new(name=nm)
by_bone = {}
for root_i, idxs in groups.items():
    b = assign[root_i]
    if b is None:
        for i in idxs:
            ci = co[i]
            for bn, w in soft_weights(ci.x, ci.z).items():
                by_bone.setdefault(bn, []).append((i, w))
    else:
        for i in idxs:
            by_bone.setdefault(b, []).append((i, 1.0))
for bname, pairs in by_bone.items():
    vg = body.vertex_groups[bname]
    plain = [i for i, w in pairs if w >= 0.999]
    if plain:
        vg.add(plain, 1.0, 'REPLACE')
    for i, w in pairs:
        if w < 0.999:
            vg.add([i], w, 'REPLACE')

for p in body.data.polygons:
    p.use_smooth = True

bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_NAME')

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HERO3_SAVED", OUT, "islands", len(groups), "verts", len(me.vertices))
