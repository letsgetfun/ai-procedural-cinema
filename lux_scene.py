# -*- coding: utf-8 -*-
"""
圣礼拜堂式哥特中厅（静帧）
  · 侧墙整面彩窗（5m→16m），每跨三扇尖拱窗 + 石棂
  · 交叉肋拱顶：横向拱 + 四道对角肋 + 脊线
   · 深蓝撒金顶棚
   · 尽头玫瑰窗（半径 4.3m，石棂环 + 12 辐射棂 + 花瓣）
用法：
  blender -b -P lux_scene.py -- --still out/lux/a.png --csamples 32
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(k, d=None, n=1):
    if k in argv:
        i = argv.index(k)
        if n == 1:
            return argv[i + 1] if i + 1 < len(argv) else d
        return argv[i + 1:i + 1 + n]
    return d

# ---------------------------------------------------------------- 尺度
BAY      = 6.0
NB       = int(arg("--nb", "5"))
HALF_W   = 5.5
ARC_H    = 3.8            # 裙墙 = 窗台（比烛台焰尖 2.89m 高 0.91m）
GLASS_LO = 3.8            # 窗台（比上一版高 0.8m ≈ 窗高 5%）
GLASS_SH = 15.9           # 窗身与尖拱的分界（肩线）
GLASS_APEX = 18.8         # 尖拱顶点（略低于拱脚 19.0，不穿出壳体）
GLASS_HI = 19.0
SPRING   = 19.0
RIDGE    = 27.2
ROSE_R   = 4.3
LEN      = NB * BAY
TEX      = os.path.join(HERE, "tex")

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def mat(name, base, metallic=0.0, rough=0.5, emis=None, es=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1)
        b.inputs["Emission Strength"].default_value = es
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.blend_method = 'BLEND'
        except Exception:
            pass
    return m


M_STONE = mat("stone", (0.118, 0.082, 0.048), 0.0, 0.84)
M_STONE_D = mat("stone_d", (0.062, 0.041, 0.023), 0.0, 0.90)
M_ENDWALL = mat("stone_endwall", (0.037, 0.025, 0.014), 0.0, 0.92)
M_GOLD = mat("gold", (0.72, 0.52, 0.16), 1.0, 0.28)
M_RIB = mat("rib_stone", (0.235, 0.184, 0.122), 0.0, 0.72)   # 肋拱专用：比墙体亮，才读得出来
M_FLOOR = mat("floor", (0.135, 0.103, 0.070), 0.18, 0.20)


def _fin(o, m, smooth=True):
    o.data.materials.append(m)
    if hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = smooth
    return o


def box(name, size, loc, m, rot=(0, 0, 0), parent=None, smooth=False):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.scale = size; o.location = loc; o.rotation_euler = Euler(rot)
    if parent: o.parent = parent
    return _fin(o, m, smooth)


def cyl(name, r, h, loc, m, verts=16, rot=(0, 0, 0), parent=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                                            radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = Euler(rot)
    if parent: o.parent = parent
    return _fin(o, m)


def rib(name, pts, depth, m, parent=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
    cu.bevel_depth = depth
    cu.bevel_resolution = 2
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o


# ---------------------------------------------------------------- 材质：彩窗
def glass_mat(name, tex_file, strength, tint=(1, 1, 1)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.35
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(TEX, tex_file))
    tx.extension = 'EXTEND'
    b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
    # 亮度随纹理轻微起伏，玻璃才有远近层次
    b.inputs["Emission Strength"].default_value = strength
    return m


M_GLASS = glass_mat("stained", "glass_tri.png", float(arg("--glow", "2.6")), tint=(1.00, 0.94, 0.84))
M_ROSE = glass_mat("stained_rose", "glass_rose.png", float(arg("--roeglow", "2.2")), tint=(1.00, 0.72, 0.34))


# 顶棚：深蓝 + 金星
def ceil_mat():
    m = bpy.data.materials.new("vault_ceiling")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 26.0
    vor.feature = 'F1'
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.00
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    ramp.color_ramp.elements[1].position = 0.055
    ramp.color_ramp.elements[1].color = (1, 0.82, 0.35, 1)
    # 反转：距离小的地方是星点
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    ramp2 = nt.nodes.new("ShaderNodeValToRGB")
    ramp2.color_ramp.elements[0].position = 0.045
    ramp2.color_ramp.elements[0].color = (1, 0.80, 0.36, 1)
    ramp2.color_ramp.elements[1].position = 0.095
    ramp2.color_ramp.elements[1].color = (0.016, 0.026, 0.085, 1)
    nt.links.new(vor.outputs["Distance"], ramp2.inputs["Fac"])
    nt.links.new(ramp2.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(ramp2.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.9
    return m


M_CEIL = ceil_mat()

# 石材：程序化石纹
def stone_detail(m, scale, bump):
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = scale
    n1.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (0.048, 0.043, 0.038, 1)
    r.color_ramp.elements[1].color = (0.115, 0.104, 0.092, 1)
    nt.links.new(n1.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.02
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = scale * 9
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n2.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])


stone_detail(M_STONE, 2.2, 0.35)
stone_detail(M_STONE_D, 3.0, 0.25)

# ---------------------------------------------------------------- 地面
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, LEN / 2 - 4, 0))
fl = bpy.context.object
fl.name = "floor"; fl.scale = (HALF_W * 2 + 10, LEN + 20, 1)
_fin(fl, M_FLOOR, False)


def vault_z(u):
    t = abs(2 * u - 1)
    return SPRING + (RIDGE - SPRING) * (1 - t ** 0.80)


# ---------------------------------------------------------------- 拱顶面
def build_vault():
    nx, ny = 28, 60
    verts, faces = [], []
    for j in range(ny + 1):
        y = -2 + (LEN + 4) * j / ny
        for i in range(nx + 1):
            u = i / nx
            verts.append((-HALF_W + 2 * HALF_W * u, y, vault_z(u) + 0.55))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new("vault")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new("vault", me)
    bpy.context.collection.objects.link(o)
    # 用整体抬高 0.55m 代替 solidify：solidify 向内挤会把肋拱整个盖住
    return _fin(o, M_CEIL, True)


build_vault()

# ---------------------------------------------------------------- 柱 / 拱 / 彩窗
for i in range(NB + 1):
    y = i * BAY
    for s in (-1, 1):
        x = s * HALF_W
        box(f"plinth_{i}_{s}", (1.15, 1.15, 0.42), (x, y, 0.21), M_STONE_D)
        cyl(f"pier_{i}_{s}", 0.36, SPRING - 0.4, (x, y, (SPRING - 0.4) / 2 + 0.4), M_STONE, 20)
        for k in range(6):          # 束柱
            a = k * math.pi / 3 + math.pi / 6
            cyl(f"shaft_{i}_{s}_{k}", 0.095, SPRING - 1.2,
                (x + math.cos(a) * 0.39, y + math.sin(a) * 0.39, (SPRING - 1.2) / 2 + 0.6),
                M_STONE, 10)
        box(f"cap_{i}_{s}", (1.02, 1.02, 0.34), (x, y, SPRING - 0.30), M_STONE_D)

    # 下部盲拱（尖拱轮廓）
    if i < NB:
        for s in (-1, 1):
            x = s * HALF_W
            pts = []
            for k in range(13):
                t = k / 12
                yy = y + t * BAY
                u = 0.5 + 0.5 * math.sin((t - 0.5) * math.pi)   # 只是轮廓用
                pts.append((x - s * 0.1, yy, 0))
            rib(f"blind_{i}_{s}", [(x - s * 0.35, y + BAY * k / 12,
                                    ARC_H - 0.9 * math.sin(math.pi * k / 12) ** 0.8)
                                   for k in range(13)], 0.10, M_STONE_D)

# 彩窗：每跨一整块 + 石棂
for i in range(NB):
    y0 = i * BAY
    yc = y0 + BAY / 2
    for s in (-1, 1):
        x = s * (HALF_W + 0.06)
        w = BAY - 0.86
        sh = GLASS_SH
        ap = GLASS_APEX
        bh = sh - GLASS_LO
        # 下部实墙 + 盲拱龛（避免柱间是黑洞）
        box(f"lowwall_{i}_{s}", (0.30, BAY, ARC_H),
            (x, yc, ARC_H / 2), M_STONE_D)
        for k in (-1, 0, 1):
            box(f"niche_{i}_{s}_{k}", (0.16, 0.85, ARC_H * 0.62),
                (x - s * 0.20, yc + k * (BAY - 2.2) / 3.2, ARC_H * 0.34), M_STONE)
        # 彩窗：五边形（矩形窗身 + 尖拱窗头），UV 铺满整个轮廓
        vs = [(-w / 2, GLASS_LO), (w / 2, GLASS_LO), (w / 2, sh), (0.0, ap), (-w / 2, sh)]
        verts = [(0.0, yc + yy, zz) for (yy, zz) in vs]
        me = bpy.data.meshes.new(f"glass_{i}_{s}")
        me.from_pydata(verts, [], [(0, 1, 2, 3, 4)])
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for li, (yy, zz) in enumerate(vs):
            uvl.data[li].uv = ((yy + w / 2) / w, (zz - GLASS_LO) / (ap - GLASS_LO))
        g = bpy.data.objects.new(f"glass_{i}_{s}", me)
        bpy.context.collection.objects.link(g)
        g.location = (x, 0, 0)
        _fin(g, M_GLASS, False)
        # 窗身竖棂（三扇窗的分隔）+ 横梃
        for k in (-1, 0, 1):
            box(f"mull_{i}_{s}_{k}", (0.085, 0.10, bh), (x - s * 0.01, yc + k * w / 3.0,
                                                       (GLASS_LO + sh) / 2), M_STONE)
        box(f"trans_{i}_{s}", (0.085, w, 0.10), (x - s * 0.01, yc, GLASS_LO + bh * 0.62), M_STONE)
        # 窗头：中梃 + 两道斜棂（尖拱）
        box(f"mullH_{i}_{s}", (0.085, 0.09, ap - sh), (x - s * 0.01, yc, (sh + ap) / 2), M_STONE)
        rib(f"rakeL_{i}_{s}", [(x, yc - w / 2, sh), (x, yc, ap)], 0.055, M_STONE)
        rib(f"rakeR_{i}_{s}", [(x, yc + w / 2, sh), (x, yc, ap)], 0.055, M_STONE)
        # 窗框：与玻璃同平面、做薄，玻璃才"铺满"
        box(f"frmL_{i}_{s}", (0.10, 0.10, bh), (x, yc - w / 2, (GLASS_LO + sh) / 2), M_STONE)
        box(f"frmR_{i}_{s}", (0.10, 0.10, bh), (x, yc + w / 2, (GLASS_LO + sh) / 2), M_STONE)
        box(f"frmB_{i}_{s}", (0.10, w, 0.10), (x, yc, GLASS_LO), M_STONE)

# 窗台与束腰线（只留薄边，别挡住玻璃）
for s in (-1, 1):
    box(f"sill_{s}", (0.30, LEN, 0.16), (s * HALF_W, LEN / 2, GLASS_LO - 0.08), M_STONE_D)
    box(f"course2_{s}", (0.26, LEN, 0.18), (s * HALF_W, LEN / 2, SPRING - 0.05), M_STONE_D)

# ---------------------------------------------------------------- 肋拱
def cross_pts(y, n=22):
    return [(-HALF_W + 2 * HALF_W * k / n, y, vault_z(k / n)) for k in range(n + 1)]


for i in range(NB + 1):
    y = i * BAY
    rib(f"trans_{i}", cross_pts(y), 0.30, M_RIB)          # 横向拱（拱圈）
    # 双拱：第二条稍细的并列拱
    rib(f"trans2_{i}", [(p[0] * 0.985, p[1] + 0.46, p[2] - 0.04) for p in cross_pts(y)], 0.17, M_RIB)

for i in range(NB):
    yc = i * BAY + BAY / 2
    for s in (-1, 1):
        for dy in (0.0, 1.0):
            y0 = i * BAY + dy * BAY
            pts = []
            for k in range(17):
                t = k / 16
                xx = s * HALF_W * (1 - t)
                yy = y0 + (yc - y0) * t
                zz = SPRING + (RIDGE - SPRING) * (t ** 0.62)
                pts.append((xx, yy, zz))
            rib(f"diag_{i}_{s}_{int(dy)}", pts, 0.24, M_RIB)

# 脊线
rib("ridge", [(0, -2 + (LEN + 4) * k / 40, RIDGE - 0.12) for k in range(41)], 0.13, M_GOLD)

# 拱心石：对角肋交汇处的金色节点
M_BOSS = mat("boss_gold", (0.88, 0.64, 0.26), 0.85, 0.24, emis=(1.0, 0.74, 0.32), es=1.8)
for i in range(NB):
    yc = i * BAY + BAY / 2
    cyl(f"boss_{i}", 0.20, 0.42, (0, yc, RIDGE + 0.29), M_BOSS, 16,
        rot=(math.radians(90), 0, 0))

# ---------------------------------------------------------------- 玫瑰窗（尽头）
RY = LEN
RC = 16.0
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=ROSE_R, fill_type='NGON',
                                  location=(0, RY - 0.15, RC), rotation=(math.radians(90), 0, 0))
rose = bpy.context.object
rose.name = "rose_glass"
_fin(rose, M_ROSE, False)
# UV：平面映射到 0..1
me = rose.data
uv = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        uv.data[li].uv = (0.5 + v.x / (2 * ROSE_R), 0.5 + v.z / (2 * ROSE_R))

# 石棂：外环 + 内环 + 12 辐射
for rr, dep in ((ROSE_R, 0.20), (ROSE_R * 0.72, 0.12), (ROSE_R * 0.46, 0.11), (ROSE_R * 0.20, 0.10)):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=dep, major_segments=64,
                                     minor_segments=8, location=(0, RY - 0.10, RC),
                                     rotation=(math.radians(90), 0, 0))
    _fin(bpy.context.object, M_STONE)
for k in range(12):
    a = 2 * math.pi * k / 12
    box(f"rose_spoke_{k}", (0.16, 0.14, ROSE_R * 1.0),
        (math.sin(a) * ROSE_R * 0.5, RY - 0.10, RC + math.cos(a) * ROSE_R * 0.5),
        M_STONE, rot=(0, a, 0))

# 尽端墙：按拱顶轮廓放样，把屋顶真正封住（之前只做到 z=22，上面漏一个大洞）
def end_wall(y_pos, nx=44, thick=0.7):
    verts, faces = [], []
    for i in range(nx + 1):
        u = i / nx
        x = -HALF_W + 2 * HALF_W * u
        verts.append((x, y_pos, 0.0))
        verts.append((x, y_pos, vault_z(u)))
    for i in range(nx):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    me = bpy.data.meshes.new("endwall")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new("endwall", me)
    bpy.context.collection.objects.link(o)
    sol = o.modifiers.new("sol", 'SOLIDIFY')
    sol.thickness = thick
    return _fin(o, M_ENDWALL, True)


end_wall(RY + 0.4)

# 玫瑰窗石框（外圈厚环，把窗"嵌"进墙里）
bpy.ops.mesh.primitive_torus_add(major_radius=ROSE_R + 0.34, minor_radius=0.30, major_segments=64,
                                 minor_segments=10, location=(0, RY - 0.05, RC),
                                 rotation=(math.radians(90), 0, 0))
_fin(bpy.context.object, M_ENDWALL)

# ---------------------------------------------------------------- 红毯（丝绒 + 金边）
def carpet_mat():
    m = bpy.data.materials.new("velvet")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.74
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 1.0
        b.inputs["Sheen Roughness"].default_value = 0.28
        try:
            b.inputs["Sheen Tint"].default_value = (0.90, 0.42, 0.36, 1.0)
        except Exception:
            pass
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(TEX, "carpet.png"))
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    return m


M_CARPET = carpet_mat()

# ---------------------------------------------------------------- 王椅（尽头墙下）
M_THRONE_GOLD = mat("throne_gold", (0.62, 0.44, 0.15), 1.0, 0.40)
def velvet_mat():
    m = bpy.data.materials.new("velvet_brocade")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.60
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 1.0
        b.inputs["Sheen Roughness"].default_value = 0.30
        try:
            b.inputs["Sheen Tint"].default_value = (0.95, 0.50, 0.42, 1.0)
        except Exception:
            pass
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.95, 0.95, 0.95)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(TEX, "brocade.png"))
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.55
    bp.inputs["Distance"].default_value = 0.012
    nt.links.new(tx.outputs["Color"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M_VELVET = velvet_mat()


def arch_panel(name, w, h_rect, apex_h, depth, loc, m):
    """尖拱面板：5 顶点轮廓沿 Y 拉伸（与教堂窗同形制）"""
    bm = bmesh.new()
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h_rect), (0.0, apex_h), (-w / 2, h_rect)]
    vs = [bm.verts.new((x, -depth / 2, z)) for (x, z) in pts]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0.0, depth, 0.0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return _fin(o, m, False)


def tube_band(x1, z1, x2, z2, y, name, r=0.22, beads=9, bead_scale=0.42):
    """圆券滚边：一根圆柱 + 沿券面的连续珠饰（比方线脚立体）"""
    dx, dz = x2 - x1, z2 - z1
    ln = math.hypot(dx, dz)
    if ln < 1e-6:
        return
    ang = math.atan2(dz, dx)
    cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
    cyl(name + "_tube", r, ln, (cx, y, cz), M_THRONE_GOLD, 24,
        rot=(0, math.radians(90) - ang, 0))
    for k in range(beads):
        t = (k + 0.5) / beads
        px = x1 + dx * t
        pz = z1 + dz * t
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * bead_scale, segments=14, ring_count=10,
                                             location=(px, y - r * 0.72, pz))
        _fin(bpy.context.object, M_THRONE_GOLD, True)


def moulded_band(x1, z1, x2, z2, y, name, w0=0.46, dep=0.66, end_block=True):
    """带线脚的拱券构件：三层叠出剖面 + 两端接合块"""
    dx, dz = x2 - x1, z2 - z1
    ln = math.hypot(dx, dz)
    if ln < 1e-6:
        return
    ux, uz = dx / ln, dz / ln
    nx, nz = -uz, ux                      # 构件外法线（XZ 平面）
    ang = math.atan2(dz, dx)
    cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
    # 三层：底带最宽最靠后，中段前移，前压线最细最靠前
    for k, (wo, dstart, th) in enumerate(((1.00, 0.00, w0),
                                          (0.72, 0.055, w0 * 0.72),
                                          (0.46, 0.105, w0 * 0.46))):
        o = (wo - 0.46) * w0 * 0.5
        box("%s_L%d" % (name, k), (ln + w0 * 0.5, dep - dstart, th),
            (cx + nx * o, y - dstart / 2, cz + nz * o), M_THRONE_GOLD, rot=(0, -ang, 0))
    if end_block:
        box("%s_E0" % name, (0.66, dep + 0.12, 0.66), (x1, y, z1), M_THRONE_GOLD, rot=(0, -ang, 0))


def throne(y_pos):
    """王座：三级台基 / 双层券拱 / 凹槽立柱 / 织花丝绒 + 金织带 / 浮雕 / 冠饰 / 烛台"""
    STEP = 0.24
    for i, (wd, dp) in enumerate(((8.0, 3.5), (7.1, 3.1), (6.2, 2.7))):
        box("thr_step_%d" % i, (wd, dp, STEP), (0, y_pos + 0.32 * i, STEP * (i + 0.5)),
            M_STONE_D if "M_STONE_D" in globals() else M_GOLD)
        box("thr_nose_%d" % i, (wd, 0.08, 0.06), (0, y_pos + 0.32 * i - dp / 2, STEP * (i + 1)),
            M_THRONE_GOLD)
        box("thr_run_%d" % i, (wd - 0.30, dp - 0.34, 0.012), (0, y_pos + 0.32 * i, STEP * (i + 1) + 0.010),
            M_CARPET)
    top = STEP * 3.0
    FY = y_pos + 1.55                    # 主券平面
    BO = y_pos + 2.35                    # 外层券平面（后退）

    # ---- 外层券拱（更大、后退，形成层次）----
    for sx in (-1, 1):
        # 外侧立柱：圆柱 + 柱础/柱头线脚 + 三道箍 + 正面竖珠链
        XO = sx * 2.28
        box("thr_opbase_%d" % sx, (1.15, 1.10, 0.30), (XO, BO, top + 0.18), M_THRONE_GOLD)
        cyl("thr_opbase2_%d" % sx, 0.42, 0.16, (XO, BO, top + 0.40), M_THRONE_GOLD, 24)
        cyl("thr_ocol_%d" % sx, 0.345, 3.80, (XO, BO, top + 2.32), M_THRONE_GOLD, 28)
        for _k in range(3):
            cyl("thr_oring_%d_%d" % (sx, _k), 0.395, 0.10, (XO, BO, top + 1.10 + _k * 1.15), M_THRONE_GOLD, 28)
        cyl("thr_ocap_%d" % sx, 0.42, 0.16, (XO, BO, top + 4.26), M_THRONE_GOLD, 24)
        box("thr_ocap2_%d" % sx, (0.98, 0.94, 0.20), (XO, BO, top + 4.42), M_THRONE_GOLD)
        for _k in range(9):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, segments=14, ring_count=10,
                                                 location=(XO, BO - 0.30, top + 0.72 + _k * 0.42))
            _fin(bpy.context.object, M_THRONE_GOLD, True)
        x1, z1 = sx * 2.28, top + 4.52
        x2, z2 = 0.0, top + 6.85
        ln = math.hypot(x2 - x1, z2 - z1)
        ang = math.atan2(z2 - z1, x2 - x1)
        tube_band(x1, z1, x2, z2, BO, "thr_orake_%d" % sx, r=0.32, beads=13, bead_scale=0.38)

    # ---- 内券：凹槽圆柱 + 柱础柱头 + 斜拱 + 底梁 ----
    box("thr_rail0", (3.70, 0.74, 0.40), (0, FY, top + 0.16), M_THRONE_GOLD)
    tube_band(-1.62, top + 0.44, 1.62, top + 0.44, FY - 0.06, "thr_rail", r=0.20, beads=13)
    for sx in (-1, 1):
        X = sx * 1.555
        cyl("thr_pst_%d" % sx, 0.235, 3.30, (X, FY, top + 1.98), M_THRONE_GOLD, 24)
        cyl("thr_pbase_%d" % sx, 0.33, 0.22, (X, FY, top + 0.42), M_THRONE_GOLD, 24)
        box("thr_pbase2_%d" % sx, (0.88, 0.80, 0.12), (X, FY, top + 0.30), M_THRONE_GOLD)
        cyl("thr_pcap_%d" % sx, 0.33, 0.22, (X, FY, top + 3.58), M_THRONE_GOLD, 24)
        box("thr_pcap2_%d" % sx, (0.62, 0.62, 0.16), (X, FY, top + 3.74), M_THRONE_GOLD)
        box("thr_pcap3_%d" % sx, (0.74, 0.72, 0.12), (X, FY, top + 3.87), M_THRONE_GOLD)
        # 柱身三道金箍
        for k in (-1, 0, 1):
            cyl("thr_ring_%d_%d" % (sx, k), 0.26, 0.06, (X, FY, top + 1.98 + k * 0.95), M_THRONE_GOLD, 24)
        x1, z1 = sx * 1.555, top + 3.74
        x2, z2 = 0.0, top + 6.05
        ln = math.hypot(x2 - x1, z2 - z1)
        ang = math.atan2(z2 - z1, x2 - x1)
        tube_band(x1, z1, x2, z2, FY, "thr_rake_%d" % sx, r=0.23, beads=11)

    # ---- 拱心石 ----
    box("thr_key0", (1.02, 0.86, 1.02), (0, FY, top + 6.02), M_THRONE_GOLD, rot=(0, math.radians(45), 0))
    box("thr_key1", (0.62, 1.00, 0.62), (0, FY - 0.08, top + 6.02), M_THRONE_GOLD, rot=(0, math.radians(45), 0))

    # ---- 织花丝绒背板（退到券后 0.62）----
    arch_panel("thr_back_v", 3.34, 3.70, 5.85, 0.24, (0, FY + 0.62, top + 0.05), M_VELVET)
    # ---- 金织带：沿绒面内缘一圈 ----
    BX, BZ = 1.36, FY + 0.50
    for sx in (-1, 1):
        box("thr_brd_v_%d" % sx, (0.11, 0.11, 3.15), (sx * BX, BZ, top + 1.90), M_THRONE_GOLD)
        x1, z1 = sx * BX, top + 3.50
        x2, z2 = 0.0, top + 5.62
        ln = math.hypot(x2 - x1, z2 - z1)
        ang = math.atan2(z2 - z1, x2 - x1)
        box("thr_brd_r_%d" % sx, (ln, 0.11, 0.11), ((x1 + x2) / 2, BZ, (z1 + z2) / 2),
            M_THRONE_GOLD, rot=(0, -ang, 0))
    box("thr_brd_b", (2.78, 0.11, 0.11), (0, BZ, top + 0.40), M_THRONE_GOLD)

    # ---- 中央浮雕（多层圆盘 + 放射齿）----
    cyl("thr_med1", 0.52, 0.08, (0, FY + 0.46, top + 2.55), M_THRONE_GOLD, 32, rot=(math.radians(90), 0, 0))
    cyl("thr_med2", 0.34, 0.10, (0, FY + 0.40, top + 2.55), M_THRONE_GOLD, 28, rot=(math.radians(90), 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, segments=20, ring_count=12,
                                         location=(0, FY + 0.36, top + 2.55))
    _fin(bpy.context.object, M_THRONE_GOLD, True)
    for k in range(12):
        aa = k * math.pi / 6.0
        cyl("thr_ray_%d" % k, 0.055, 0.16, (math.cos(aa) * 0.60, FY + 0.44, top + 2.55 + math.sin(aa) * 0.60),
            M_THRONE_GOLD, 10, rot=(math.radians(90), 0, -aa))

    # ---- 座：金框 + 织花垫 + 靠垫 ----
    box("thr_seat_f", (2.95, 1.60, 0.36), (0, y_pos + 0.30, top + 0.32), M_THRONE_GOLD)
    box("thr_seat_c", (2.55, 1.30, 0.22), (0, y_pos + 0.30, top + 0.60), M_VELVET)
    box("thr_seat_b", (2.45, 0.22, 0.75), (0, y_pos + 0.92, top + 0.95), M_VELVET)
    # ---- 扶手：立柱 + 托板 + 织花垫 + 球端 ----
    for sx in (-1, 1):
        box("thr_arm_%d" % sx, (0.38, 1.60, 0.20), (sx * 1.52, y_pos + 0.30, top + 1.20), M_THRONE_GOLD)
        box("thr_armp_%d" % sx, (0.30, 1.24, 0.12), (sx * 1.52, y_pos + 0.30, top + 1.34), M_VELVET)
        cyl("thr_post_%d" % sx, 0.12, 0.85, (sx * 1.52, y_pos + 1.02, top + 0.82), M_THRONE_GOLD, 14)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=18, ring_count=12,
                                             location=(sx * 1.52, y_pos - 0.45, top + 1.28))
        _fin(bpy.context.object, M_THRONE_GOLD, True)

    # ---- 冠饰：三节塔尖 ----
    cyl("thr_cr1", 0.26, 0.35, (0, FY, top + 6.20), M_THRONE_GOLD, 16)
    cyl("thr_cr2", 0.18, 0.42, (0, FY, top + 6.58), M_THRONE_GOLD, 16)
    cyl("thr_cr3", 0.10, 0.40, (0, FY, top + 6.98), M_THRONE_GOLD, 12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, segments=16, ring_count=10,
                                         location=(0, FY, top + 7.24))
    _fin(bpy.context.object, M_THRONE_GOLD, True)

    # ---- 两侧烛台 ----
    try:
        candelabrum(90, -3.30, y_pos - 1.10, 0.62)
        candelabrum(91, 3.30, y_pos - 1.10, 0.62)
    except Exception as _e:
        print("cand skip", _e)

    # ---- 王座专用暖光 ----
    _td = bpy.data.lights.new("throne_lit", "AREA")
    _td.energy = 430.0; _td.size = 3.4; _td.color = (1.0, 0.74, 0.46)
    _to = bpy.data.objects.new("throne_lit", _td)
    _to.location = (0.0, y_pos - 4.6, 3.4)
    _to.rotation_euler = (Vector((0, y_pos + 1.0, 2.8)) - _to.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(_to)
    print("THRONE at y=%.2f top=%.2f" % (y_pos, top))



CAR_W = float(arg("--carpetw", "3.7"))
_c0, _c1 = -1.6, LEN - 3.2
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, (_c0 + _c1) / 2, 0.014))
_cp = bpy.context.object
_cp.name = "carpet"
_cp.scale = (CAR_W, _c1 - _c0, 1)
_fin(_cp, M_CARPET, False)

# ---------------------------------------------------------------- 烛台（三层立式）
M_WAX = mat("wax", (0.82, 0.78, 0.70), 0.0, 0.55)
M_FLAME = mat("flame", (1.0, 0.78, 0.38), 0.0, 1.0, emis=(1.0, 0.70, 0.28), es=26.0)
M_F_OUT = mat("flame_out", (1.00, 0.46, 0.10), 0.0, 1.0, emis=(1.00, 0.40, 0.05), es=9.0, alpha=0.55)
M_F_IN = mat("flame_in", (0.45, 0.66, 1.00), 0.0, 1.0, emis=(0.36, 0.58, 1.00), es=26.0, alpha=0.85)


def rev_mesh(name, prof, r_max, h, seg=18, rings=16, mat_=None):
    """按母线 prof(u) 绕 Z 轴回转生成水滴形（u: 0=底 1=顶）"""
    verts, faces = [], []
    for j in range(rings + 1):
        u = j / rings
        rr = max(prof(u) * r_max, 1e-4)
        z = u * h
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((math.cos(a) * rr, math.sin(a) * rr, z))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b = j * seg + (i + 1) % seg
            c = (j + 1) * seg + (i + 1) % seg
            d = (j + 1) * seg + i
            faces.append((a, b, c, d))
    # 底封口
    faces.append(tuple(range(seg - 1, -1, -1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return _fin(o, mat_, True)


# 烛焰母线：底部窄 → 1/3 处最宽 → 收成尖（真实烛焰是水滴形，不是圆锥）
def _flame_prof(u):
    return math.sin(math.pi * (u ** 0.60)) ** 1.05


_pm = max(_flame_prof(k / 60.0) for k in range(1, 60))
def flame_prof(u):
    return _flame_prof(u) / _pm


def flame_2layer(x, y, z0, s=1.0):
    """水滴形双层烛焰：外焰橙黄（发光主体）+ 内焰蓝（底部清洁燃烧区）"""
    o1 = rev_mesh("fl_out", flame_prof, 0.0215 * s, 0.086 * s, 16, 14, M_F_OUT)
    o1.location = (x, y, z0)
    o2 = rev_mesh("fl_in", flame_prof, 0.0092 * s, 0.036 * s, 14, 12, M_F_IN)
    o2.location = (x, y, z0 + 0.002 * s)

THRONE_Y = None
if arg("--throne", "1") == "1":
    THRONE_Y = RY - 3.4
    throne(THRONE_Y)


def candelabrum(idx, x, y, s):
    tag = f"cb_{idx}_{s}"
    box(f"{tag}_base", (0.82, 0.82, 0.10), (x, y, 0.05), M_GOLD)
    cyl(f"{tag}_b2", 0.26, 0.14, (x, y, 0.17), M_GOLD, 20)
    cyl(f"{tag}_b3", 0.17, 0.30, (x, y, 0.40), M_GOLD, 16)
    cyl(f"{tag}_shaft", 0.055, 1.95, (x, y, 1.52), M_GOLD, 12)
    for zz in (0.95, 1.75, 2.42):                      # 节球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=(x, y, zz))
        _fin(bpy.context.object, M_GOLD)
    tiers = ((2.48, 0.62, 6), (2.15, 0.40, 6))
    for ti, (tz, tr, n) in enumerate(tiers):
        for k in range(n):
            a = 2 * math.pi * k / n + (math.pi / n if ti else 0)
            ax = x + math.cos(a) * tr
            ay = y + math.sin(a) * tr
            # 弯臂：用小段圆柱拼出外弯
            nx_ = math.cos(a); ny_ = math.sin(a)
            box(f"{tag}_arm_{ti}_{k}", (0.035, 0.035, 0.30), (x + nx_ * tr * 0.5, y + ny_ * tr * 0.5, tz - 0.10),
                M_GOLD, rot=(math.radians(20) * ny_, math.radians(-20) * nx_, 0))
            cyl(f"{tag}_cup_{ti}_{k}", 0.075, 0.07, (ax, ay, tz + 0.02), M_GOLD, 12)
            cyl(f"{tag}_wax_{ti}_{k}", 0.032, 0.30, (ax, ay, tz + 0.20), M_WAX, 10)
            flame_2layer(ax, ay, tz + 0.355)
    # 中心高烛
    cyl(f"{tag}_waxC", 0.038, 0.34, (x, y, 2.62), M_WAX, 10)
    flame_2layer(x, y, 2.795, 1.06)


for i in range(0, NB + 1, 1):
    for s in (-1, 1):
        candelabrum(i, s * (HALF_W - 1.05), i * BAY + 0.9, s)
if THRONE_Y is not None:
    candelabrum(90, -3.30, THRONE_Y - 1.10, 0.62)
    candelabrum(91, 3.30, THRONE_Y - 1.10, 0.62)

# ---------------------------------------------------------------- 角色
with bpy.data.libraries.load(os.path.join(HERE, "hero22.blend"), link=False) as (df, dt):
    dt.objects = list(df.objects)
got = [o for o in dt.objects if o is not None]
for o in got:
    if o.name not in bpy.context.scene.collection.all_objects:
        try:
            bpy.context.collection.objects.link(o)
        except RuntimeError:
            pass
rig_o = bpy.data.objects.get("MarineRig")
body = bpy.data.objects.get("AstartesBody")
print("HERO", len(got), "rig", bool(rig_o), "body", bool(body))

scn.frame_set(int(arg("--frame", "18")))
cy = float(rig_o.location.y) if rig_o else 0.0
if body:
    rig_o.location.y = 0.0
    cy = 0.0
    # 放大到 1.25 倍（脚仍在 z=0，因为缩放中心在原点）
    _sc = float(arg("--scale", "1.25"))
    rig_o.scale = (_sc, _sc, _sc)
    bpy.context.view_layer.update()
    print("HERO_SCALE", _sc)

# 暗红发光眼：直接把模型自带的 "eyes" 镜片材质改成自发光（比贴球干净、位置天然正确）
if body:
    try:
        _hit = 0
        for _m in body.data.materials:
            if _m and _m.use_nodes and _m.name.lower().startswith("eyes"):
                _b = _m.node_tree.nodes.get("Principled BSDF")
                if _b:
                    _b.inputs["Base Color"].default_value = (0.55, 0.02, 0.01, 1)
                    _b.inputs["Roughness"].default_value = 0.18
                    _b.inputs["Metallic"].default_value = 0.0
                    _b.inputs["Emission Color"].default_value = (1.0, 0.055, 0.02, 1)
                    _b.inputs["Emission Strength"].default_value = float(arg("--eyeglow", "13.0"))
                    _hit += 1
        print("EYES_MAT", _hit)
    except Exception as _e:
        print("EYES fail", _e)

# 眼睛外溢光晕（加色、软边）：让"发光"有散射感，而不是两条死白条
if body and rig_o and float(arg("--eyehaze", "0.0")) > 0:
    try:
        _hz = float(arg("--hazer", "0.115"))
        _hm = bpy.data.materials.new("eye_haze")
        _hm.use_nodes = True
        _nt = _hm.node_tree
        for _n in list(_nt.nodes):
            if _n.type != 'OUTPUT_MATERIAL':
                _nt.nodes.remove(_n)
        _out = _nt.nodes["Material Output"]
        _add = _nt.nodes.new("ShaderNodeAddShader")
        _tr = _nt.nodes.new("ShaderNodeBsdfTransparent")
        _em = _nt.nodes.new("ShaderNodeEmission")
        _em.inputs["Color"].default_value = (1.0, 0.10, 0.04, 1)
        _em.inputs["Strength"].default_value = float(arg("--eyehaze", "0.0")) * 7.0
        _lw = _nt.nodes.new("ShaderNodeLayerWeight")
        _lw.inputs["Blend"].default_value = 0.5
        _inv = _nt.nodes.new("ShaderNodeMath")
        _inv.operation = 'SUBTRACT'
        _inv.inputs[0].default_value = 1.0
        _pw = _nt.nodes.new("ShaderNodeMath")
        _pw.operation = 'POWER'
        _pw.inputs[1].default_value = float(arg("--hazepow", "2.6"))
        _mix = _nt.nodes.new("ShaderNodeMixShader")
        _nt.links.new(_lw.outputs["Facing"], _inv.inputs[1])
        _nt.links.new(_inv.outputs[0], _pw.inputs[0])
        _nt.links.new(_pw.outputs[0], _mix.inputs[0])
        _nt.links.new(_tr.outputs[0], _mix.inputs[1])
        _nt.links.new(_em.outputs[0], _mix.inputs[2])
        _nt.links.new(_mix.outputs[0], _out.inputs["Surface"])
        try:
            _hm.blend_method = 'BLEND'
            _hm.shadow_method = 'NONE'
        except Exception:
            pass
        for _ex, _ez in ((-0.050, 0.0), (0.080, 0.0)):
            _bm = bmesh.new()
            bmesh.ops.create_uvsphere(_bm, u_segments=20, v_segments=14, radius=_hz)
            _me = bpy.data.meshes.new("haze")
            _bm.to_mesh(_me); _bm.free()
            _ho = bpy.data.objects.new("haze", _me)
            bpy.context.collection.objects.link(_ho)
            _fin(_ho, _hm, True)
            _ho.location = (_ex * _sc, -0.300 * _sc, 2.585 * _sc)
            bpy.context.view_layer.update()
            _mw = _ho.matrix_world.copy()
            _ho.parent = rig_o
            _ho.parent_type = 'BONE'
            _ho.parent_bone = 'head'
            _ho.matrix_world = _mw
        print("HAZE ok")
    except Exception as _e:
        print("HAZE fail", _e)

# 釉面
if body:
    for m in body.data.materials:
        if not m or not m.use_nodes:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        for nm, val in (("Coat Weight", 1.0), ("Coat Roughness", 0.030),
                        ("Coat IOR", 1.58), ("Specular IOR Level", 0.55), ("Metallic", 0.0)):
            if nm in b.inputs and not b.inputs[nm].is_linked:
                b.inputs[nm].default_value = val
        if "Roughness" in b.inputs and not b.inputs["Roughness"].is_linked:
            b.inputs["Roughness"].default_value = 0.30
        if b.inputs["Base Color"].is_linked:
            src = b.inputs["Base Color"].links[0].from_socket
            mix = m.node_tree.nodes.new("ShaderNodeMix")
            mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs["Factor"].default_value = 0.45
            mix.inputs[7].default_value = (0.34, 0.44, 0.78, 1.0)
            m.node_tree.links.new(src, mix.inputs[6])
            m.node_tree.links.new(mix.outputs[2], b.inputs["Base Color"])

# 脚尖拧正（网格主轴 PCA）
if rig_o and body:
    import numpy as np
    rpb = rig_o.pose.bones
    for _b in rpb:
        _b.rotation_mode = 'XYZ'      # 默认是 QUATERNION，不设的话 rotation_euler 无效
    me_ = body.data
    arm = rig_o.data
    for tag in ("L", "R"):
        gi = body.vertex_groups[f"foot_{tag}"].index
        pts = []
        for v in me_.vertices:
            for g in v.groups:
                if g.group == gi and g.weight > 0.5:
                    if v.co.z < 0.17:
                        pts.append((v.co.x, v.co.y, v.co.z))
                    break
        if len(pts) < 40:
            continue
        P0 = np.array(pts)
        def ang():
            M = rig_o.matrix_world @ rpb[f"foot_{tag}"].matrix @ arm.bones[f"foot_{tag}"].matrix_local.inverted()
            Pw = P0 @ np.array(M.to_3x3()).T + np.array(M.translation)
            Q = Pw[:, :2] - Pw[:, :2].mean(axis=0)
            w_, v_ = np.linalg.eigh(Q.T @ Q)
            d = v_[:, int(np.argmax(w_))]
            if d[1] > 0:
                d = -d
            return math.degrees(math.atan2(float(d[0]), float(-d[1])))
        th = rpb[f"thigh_{tag}"]
        orig = th.rotation_euler.copy()
        best = (1e9, 0.0, 0.0)
        for kk in range(-140, 141):
            th.rotation_euler = Euler((orig.x, kk * 0.01, orig.z))
            bpy.context.view_layer.update()
            a = ang()
            if abs(a) < best[0]:
                best = (abs(a), kk * 0.01, a)
        th.rotation_euler = Euler((orig.x, best[1], orig.z))
        print("FOOT", tag, round(best[2], 2), round(best[1], 3))

# ---------------------------------------------------------------- 灯光
def area(nm, loc, aim, size, energy, color, sy=None):
    d = bpy.data.lights.new(nm, 'AREA')
    d.shape = 'RECTANGLE' if sy else 'SQUARE'
    d.size = size
    if sy: d.size_y = sy
    d.energy = energy; d.color = color
    o = bpy.data.objects.new(nm, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


# 窗外天光（让彩窗真的往内投光 + 制造光柱）
for i in range(NB):
    for s in (-1, 1):
        yc2 = i * BAY + BAY / 2
        area(f"sun_{i}_{s}", (s * (HALF_W + 2.6), yc2, 13.0), (0, yc2 - 1.2, 3.0),
             4.0, float(arg("--sun", "0")), (1.0, 0.94, 0.86), 7.0)

# 烛火补光
for i in range(0, NB + 1, 1):
    for s in (-1, 1):
        d = bpy.data.lights.new(f"candle_{i}_{s}", 'POINT')
        d.energy = 95; d.color = (1.0, 0.52, 0.16); d.shadow_soft_size = 0.08
        d.use_shadow = False
        o = bpy.data.objects.new(f"candle_{i}_{s}", d)
        bpy.context.collection.objects.link(o)
        o.location = (s * (HALF_W - 1.5), i * BAY + 0.9, 2.5)

# 玫瑰窗补光（背光）
area("rose_glow", (0, RY - 1.2, RC), (0, 0, 6.0), 5.0, float(arg("--roseglow", "26000")), (1.0, 0.86, 0.62))

# 向上洗墙：让肋拱和顶棚从黑里浮出来
for i in range(NB + 1):
    for s in (-1, 1):
        d = bpy.data.lights.new(f"up_{i}_{s}", 'SPOT')
        d.energy = float(arg("--uplight", "900"))
        d.spot_size = math.radians(55)
        d.spot_blend = 0.6
        d.color = (1.0, 0.60, 0.24)
        d.use_shadow = False
        o = bpy.data.objects.new(f"up_{i}_{s}", d)
        bpy.context.collection.objects.link(o)
        lo = Vector((s * (HALF_W - 0.7), i * BAY + 3.0, 8.5))
        o.location = lo
        tg = Vector((-s * 1.2, i * BAY + 3.0, 23.5))
        o.rotation_euler = (tg - lo).to_track_quat('-Z', 'Y').to_euler()

# 角色主光 / 轮廓 / 正面补光（胸甲长期偏暗）
area("key", (-2.6, cy - 2.4, 4.2), (0, cy, 2.0), 2.2, float(arg("--key", "520")), (1.0, 0.88, 0.70), 2.6)
area("rim", (1.0, cy + 2.6, 4.6), (0, cy, 2.2), 1.2, float(arg("--rim", "900")), (1.0, 0.70, 0.36), 2.6)
area("fill", (0.6, cy - 3.6, 2.3), (0, cy, 2.2), 2.6, float(arg("--fill", "70")), (0.86, 0.92, 1.0), 4.0)
# 背后顶光：压出头部与肩甲的圣光轮廓（参考图的关键）
area("halo", (0, cy + 2.4, 3.6), (0, cy, 2.6), 1.6, float(arg("--halo", "1500")), (1.0, 0.80, 0.48), 1.6)
# 腿部前补光：低角度正面光，让膝甲/胫甲读出鼓起的体积（背光会把同一块甲读成凹碗）
area("kneefill", (0.0, cy - 2.05, 1.15), (0.0, cy, 0.92), 1.9,
     float(arg("--kneefill", "190")), (1.00, 0.94, 0.86), 2.2)

# 尽头圣坛金光（参考图核心：末端过曝的金色光源）+ 中厅光柱光斑
area("blaze", (0, RY + 2.0, RC + 0.5), (0, 6.0, 4.0), 10.0,
     float(arg("--blaze", "0")), (1.00, 0.54, 0.15), 1.0)
def blade_mat():
    m = bpy.data.materials.new("light_blade")
    m.use_nodes = True
    m.blend_method = 'BLEND'
    m.show_transparent_back = False
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.87, 0.66, 1.0)
    em.inputs["Strength"].default_value = float(arg("--bladebright", "0.46"))
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixn = nt.nodes.new("ShaderNodeMixShader")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    # 横向：中间实、两侧渐隐
    rx = nt.nodes.new("ShaderNodeValToRGB")
    e = rx.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0, 0, 0, 1)
    e[1].position, e[1].color = 1.0, (0, 0, 0, 1)
    e2 = rx.color_ramp.elements.new(0.5)
    e2.color = (0.90, 0.90, 0.90, 1)
    # 纵向：入端淡入、落地端略衰减
    rz = nt.nodes.new("ShaderNodeValToRGB")
    f = rz.color_ramp.elements
    f[0].position, f[0].color = 0.0, (0, 0, 0, 1)
    f[1].position, f[1].color = 1.0, (0.0, 0.0, 0.0, 1)
    f2 = rz.color_ramp.elements.new(0.18)
    f2.color = (0.82, 0.82, 0.82, 1)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.2
    nz.inputs["Detail"].default_value = 3.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nzr = nt.nodes.new("ShaderNodeValToRGB")
    nzr.color_ramp.elements[0].position = 0.28
    nzr.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
    nzr.color_ramp.elements[1].position = 0.72
    nzr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], nzr.inputs["Fac"])
    mul = nt.nodes.new("ShaderNodeMixRGB")
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["X"], rx.inputs["Fac"])
    nt.links.new(sep.outputs["Z"], rz.inputs["Fac"])
    mul2 = nt.nodes.new("ShaderNodeMixRGB")
    mul2.blend_type = 'MULTIPLY'
    mul2.inputs[0].default_value = 1.0
    nt.links.new(rx.outputs["Color"], mul.inputs[1])
    nt.links.new(rz.outputs["Color"], mul.inputs[2])
    nt.links.new(mul.outputs["Color"], mul2.inputs[1])
    nt.links.new(nzr.outputs["Color"], mul2.inputs[2])
    mul = mul2
    nt.links.new(mul.outputs["Color"], mixn.inputs[0])
    nt.links.new(tr.outputs[0], mixn.inputs[1])
    nt.links.new(em.outputs[0], mixn.inputs[2])
    nt.links.new(mixn.outputs[0], out.inputs["Surface"])
    return m


def light_blade(p0, p1, w0, w1, name, mat_):
    d = (p1 - p0)
    d.normalize()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
    a = d.cross(up).normalized()
    b = d.cross(a).normalized()
    vs, fs = [], []
    for k in range(3):
        th = math.radians(60.0 * k)
        n = a * math.cos(th) + b * math.sin(th)
        base = len(vs)
        vs += [p0 + n * w0 * 0.5, p0 - n * w0 * 0.5, p1 - n * w1 * 0.5, p1 + n * w1 * 0.5]
        fs.append((base, base + 1, base + 2, base + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vs], [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    scn.collection.objects.link(ob)
    ob.data.materials.append(mat_)
    return ob


# 玫瑰窗丁达尔光刃（交叉薄片 + 渐变透明，形状可控）
if arg("--blades", "1") == "1":
    _MB = blade_mat()
    _bd = Vector((0.0, -0.52, -1.0)).normalized()
    # 避开中轴（中轴留空，王座才看得见）
    _XS = [-3.65, -2.85, -2.05, 2.05, 2.85, 3.65]
    _WD = [(0.13, 0.40), (0.16, 0.50), (0.12, 0.36), (0.12, 0.36), (0.16, 0.50), (0.13, 0.40)]
    for _i, _x0 in enumerate(_XS):
        _z0 = RC + (1.0 - abs(_x0) / 4.0) * 1.1
        _p0 = Vector((_x0, RY - 2.30, _z0))
        _t = (_z0 - 0.15) / (-_bd.z)
        _p1 = _p0 + _bd * _t
        _w0, _w1 = _WD[_i]
        light_blade(_p0, _p1, _w0, _w1, "blade_%d" % _i, _MB)

# 玫瑰窗丁达尔光柱：多而细的平行窄束（粗束会糊成一片泛光）
_GR_N = int(arg("--rays", "0"))
_GR_E = float(arg("--rayenergy", "92000"))
_GR_DIR = Vector((0.0, -0.52, -1.0)).normalized()
_GR_Q = _GR_DIR.to_track_quat('-Z', 'Y')
for _i in range(_GR_N):
    _u = (_i / max(_GR_N - 1, 1)) * 2.0 - 1.0
    _sp = bpy.data.lights.new("gr_%d" % _i, 'SPOT')
    _sp.energy = _GR_E * (0.45 + 0.55 * math.cos(_u * 1.9))
    _sp.spot_size = math.radians(2.4)
    _sp.spot_blend = 0.12
    _sp.color = (1.00, 0.83, 0.58)
    _sp.shadow_soft_size = 0.12
    _so = bpy.data.objects.new("gr_%d" % _i, _sp)
    bpy.context.collection.objects.link(_so)
    _so.location = (_u * 3.6, RY - 3.4, RC + _u * 1.1)
    _so.rotation_euler = _GR_Q.to_euler()
    _so.visible_camera = False

# 所有灯光对相机不可见（否则 Cycles 会把灯本体渲染成发光方块）
for _o in bpy.context.scene.objects:
    if _o.type == 'LIGHT':
        _o.visible_camera = False

# ---------------------------------------------------------------- 世界 / 雾
w = bpy.data.worlds.new("W"); scn.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.055, 0.030, 0.011, 1.0)
bg.inputs[1].default_value = float(arg("--world", "0.030"))
vol = w.node_tree.nodes.new("ShaderNodeVolumePrincipled")
# 世界雾关掉：改用「中厅体积盒」，末端 10 m（玫瑰窗所在）留空，
# 否则那层均匀的雾膜会把窗格细节压掉 65%。
vol.inputs["Density"].default_value = 0.0
vol.inputs["Anisotropy"].default_value = 0.55
w.node_tree.links.new(vol.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])

_FOG_D = float(arg("--fog", "0.0038"))
_FOG_END = float(arg("--fogend", "62.0"))
if _FOG_D > 0:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, (_FOG_END - 2.0) / 2.0 - 1.0, 14.0))
    _fb = bpy.context.object
    _fb.name = "fog_box"
    _fb.scale = (HALF_W * 2.06, _FOG_END + 2.0, 28.0)
    _fb.visible_shadow = False
    _fm = bpy.data.materials.new("fog_vol")
    _fm.use_nodes = True
    _fnt = _fm.node_tree
    for _n in list(_fnt.nodes):
        if _n.type == 'BSDF_PRINCIPLED':
            _fnt.nodes.remove(_n)
    _pv = _fnt.nodes.new("ShaderNodeVolumePrincipled")
    _pv.inputs["Density"].default_value = _FOG_D
    _pv.inputs["Anisotropy"].default_value = 0.55
    _fnt.links.new(_pv.outputs[0], _fnt.nodes["Material Output"].inputs["Volume"])
    _fb.data.materials.append(_fm)

# ---------------------------------------------------------------- 相机（仰视）
cam_d = bpy.data.cameras.new("C")
cam_d.lens = float(arg("--lens", "26"))
cam_d.sensor_width = 36
cam = bpy.data.objects.new("C", cam_d)
bpy.context.collection.objects.link(cam)
scn.camera = cam
D = float(arg("--dist", "7.2"))
CZ = float(arg("--camz", "0.40"))
AIMZ = float(arg("--aimz", "2.70"))
if arg("--headcam"):
    # 调试用：贴到头盔前拍特写，检查红眼位置
    _hz = 2.508 * _sc if body else 3.1
    cam.location = Vector((0.0, -1.35, _hz + 0.02))
    cam.rotation_euler = (Vector((0, 0, _hz)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    print("HEADCAM", tuple(round(v, 2) for v in cam.location))
else:
    cam.location = Vector((0, cy - D, CZ))
    cam.rotation_euler = (Vector((0, cy, AIMZ)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
print("CAM", tuple(round(v, 2) for v in cam.location), "aimz", AIMZ,
      "pitch", round(math.degrees(math.atan2(AIMZ - CZ, D)), 1))

# ---------------------------------------------------------------- 动画（走路 + 前进）
ANIM = bool(arg("--anim"))
FPS_ = int(arg("--fps", "24"))
SECS = float(arg("--secs", "30"))
TOTAL = int(FPS_ * SECS)
CYCLE_S = float(arg("--gait", "2.5"))      # 一个完整步态循环（两步）的秒数
SWING = float(arg("--swing", "0.46"))       # 大腿摆幅（弧度）
KNEE = float(arg("--knee", "0.95"))         # 膝屈最大角（弧度）
BOB = float(arg("--bob", "0.030"))          # 上下起伏半幅（骨骼局部单位，×scale 后为米）
LEAN = float(arg("--lean", "-0.050"))       # 上身恒定前倾
ARM_SWAY = float(arg("--armsway", "0.30")) # 肩部前后微摆（人眼几乎看不出）
ELBOW = float(arg("--elbow", "0.22"))       # 肘部基础弯曲
HERO_Y0 = float(arg("--heroy", "20.0"))
HERO_X = float(arg("--herox", "0.0"))      # 角色横向偏移（让开中轴，露出王椅）     # 起始位置（镜头在 -3.8，走到 3.4 结束）
SWAY = float(arg("--sway", "0.075"))
HIP_ROLL = float(arg("--hiproll", "0.013"))  # 骨盆侧倾（转向支撑腿，不是平移）       # 重心左右晃（骨骼局部 X）
CF = float(arg("--cf", "1.0"))             # 镜头跟速系数（1.0=完全跟死）
# 前进速度由步幅反推，保证脚不打滑（运动速度与前进速度自洽）
STRIDE_W = float(arg("--stride", "2.2"))     # 一个完整循环（两步）前进的世界距离
INPLACE = arg("--inplace", "0") == "1"       # 1 = 原地循环（预览用，脚会像跑步机一样后滑）
SPEED = float(arg("--speed", "0"))           # 0 = 由步幅/周期反推
if SPEED <= 0:
    SPEED = STRIDE_W / CYCLE_S
PHOFF = float(arg("--phoff", "0.0"))        # 动捕曲线相位偏移（0..1）
SURGE = float(arg("--surge", "0.070"))      # 前后冲劲幅度（骨骼局部 Z）

# CMU 07_04「slow walk」抽出的髋部重心曲线（归一化 -1..1，48 点/周期）
# X=左右  Y=前后  Z=上下；用 scipy 0.5-3Hz 带通后取一个完整周期
TAB_X = [-0.776, -0.8, -0.818, -0.834, -0.854, -0.878, -0.908, -0.942, -0.976, -0.997,
         -0.996, -0.964, -0.893, -0.782, -0.629, -0.439, -0.221, 0.012, 0.238, 0.442,
         0.613, 0.745, 0.837, 0.89, 0.91, 0.899, 0.866, 0.819, 0.763, 0.702,
         0.64, 0.581, 0.525, 0.473, 0.425, 0.381, 0.339, 0.3, 0.263, 0.228,
         0.196, 0.166, 0.139, 0.114, 0.092, 0.072, 0.055, 0.042]
TAB_Y = [0.318, 0.39, 0.458, 0.521, 0.579, 0.63, 0.67, 0.696, 0.701, 0.673,
         0.612, 0.518, 0.397, 0.254, 0.099, -0.058, -0.207, -0.343, -0.467, -0.582,
         -0.69, -0.791, -0.882, -0.955, -1.0, -1.0, -0.957, -0.875, -0.764, -0.635,
         -0.5, -0.367, -0.243, -0.135, -0.04, 0.042, 0.113, 0.174, 0.227, 0.272,
         0.312, 0.345, 0.373, 0.396, 0.415, 0.428, 0.437, 0.442]
TAB_Z = [-1.0, -0.854, -0.68, -0.461, -0.2, 0.08, 0.343, 0.545, 0.645, 0.595,
         0.422, 0.162, -0.135, -0.412, -0.62, -0.727, -0.72, -0.592, -0.391, -0.147,
         0.109, 0.348, 0.545, 0.682, 0.749, 0.741, 0.687, 0.603, 0.506, 0.407,
         0.315, 0.234, 0.164, 0.107, 0.058, 0.015, -0.023, -0.059, -0.092, -0.123,
         -0.151, -0.177, -0.2, -0.221, -0.238, -0.252, -0.264, -0.271]
_TZ_MIN = min(TAB_Z)


def _tab(ph, tab):
    i = int((ph % 1.0) * len(tab)) % len(tab)
    return tab[i]


MOCAP = bool(rig_o and rig_o.animation_data and rig_o.animation_data.action)
if MOCAP:
    scn.frame_start = int(arg("--fstart", "1"))
    scn.frame_end = int(arg("--fend", str(TOTAL)))
    for _f in range(1, TOTAL + 1):
        _t = (_f - 1) / FPS_
        rig_o.delta_location = Vector((0.0, HERO_Y0 - SPEED * _t, 0.0))
        rig_o.keyframe_insert("delta_location", frame=_f)
        cam.location = Vector((0.010 * math.sin(_t * 0.8),
                               (HERO_Y0 - D) - CF * SPEED * _t, CZ))
        cam.keyframe_insert("location", frame=_f)
        cam.rotation_euler = (Vector((0, HERO_Y0 - SPEED * _t, AIMZ)) - cam.location)             .to_track_quat('-Z', 'Y').to_euler()
        cam.keyframe_insert("rotation_euler", frame=_f)
    _HERO_LIGHTS = ("key", "rim", "fill", "halo")
    for _o in list(bpy.data.objects):
        if _o.type != 'LIGHT' or _o.name not in _HERO_LIGHTS:
            continue
        _y0 = _o.location.y
        for _f in range(1, TOTAL + 1, 4):
            _o.location.y = _y0 + HERO_Y0 - SPEED * ((_f - 1) / FPS_)
            _o.keyframe_insert("location", frame=_f)
    print("MOCAP mode", TOTAL, "frames, speed", SPEED)

if ANIM and rig_o and not MOCAP:
    pb = rig_o.pose.bones
    for _b in pb:
        _b.rotation_mode = 'XYZ'

    # ================= 腿长与坐标系校准 =================
    L1 = (pb["thigh_L"].tail - pb["thigh_L"].head).length     # 大腿
    L2 = (pb["shin_L"].tail - pb["shin_L"].head).length      # 小腿
    L  = L1 + L2
    HZ0 = pb["hips"].head.z                                  # 静止髋高（骨架空间）
    AZ0 = pb["foot_L"].head.z                                # 静止脚踝高 = 着地时的高度

    def _rel_ankle():
        return (pb["shin_L"].tail - pb["thigh_L"].head).copy()

    for _b in ("thigh_L", "shin_L"):
        pb[_b].rotation_euler = Euler((0, 0, 0))
    bpy.context.view_layer.update()
    _a0 = _rel_ankle()
    pb["thigh_L"].rotation_euler = Euler((0.3, 0, 0))
    bpy.context.view_layer.update()
    _a1 = _rel_ankle()
    S_TH = 1.0 if (_a1.y - _a0.y) < 0 else -1.0      # 正角度应让脚向 -y（前方）
    pb["thigh_L"].rotation_euler = Euler((0, 0, 0))
    pb["shin_L"].rotation_euler = Euler((0.3, 0, 0))
    bpy.context.view_layer.update()
    _a2 = _rel_ankle()
    S_KN = 1.0 if (_a2.y - _a0.y) > 0 else -1.0      # 屈膝应让脚相对大腿往回
    pb["shin_L"].rotation_euler = Euler((0, 0, 0))
    bpy.context.view_layer.update()
    print("IKCAL L1 %.3f L2 %.3f L %.3f HZ0 %.3f AZ0 %.3f S_TH %+.0f S_KN %+.0f"
          % (L1, L2, L, HZ0, AZ0, S_TH, S_KN))

    # ================= 步幅 / 抬脚 =================
    _SC = rig_o.scale.x if abs(rig_o.scale.x) > 1e-6 else 1.0
    S_W = STRIDE_W / _SC          # 一个完整循环（两步）在骨架空间里的距离
    LIFT = 0.085                  # 摆动脚最大抬升（骨架空间）
    DUTY = 0.5                    # 支撑期占半个周期

    def _foot_target(q):
        """q=该脚自己的相位 0..1 → (前向偏移, 抬升)。支撑期脚相对髋匀速后移＝世界静止"""
        if q < DUTY:
            u = q / DUTY
            return 0.25 * S_W - 0.5 * S_W * u, 0.0
        u = (q - DUTY) / (1.0 - DUTY)
        # Hermite：起点/终点都是「支撑期的后退速度」，交接瞬间速度连续，不再顿一下
        p0, p1 = -0.25 * S_W, 0.25 * S_W
        m0 = m1 = -0.5 * S_W
        u2, u3 = u * u, u * u * u
        f = ((2*u3 - 3*u2 + 1) * p0 + (u3 - 2*u2 + u) * m0
             + (-2*u3 + 3*u2) * p1 + (u3 - u2) * m1)
        lift = LIFT * (0.5 - 0.5 * math.cos(2 * math.pi * u))   # 两端抬升速度都为 0
        return f, lift

    # 髋高用光滑余弦：振幅取「双脚最开时腿刚好够到」的精确差值，
    # 全程都在可达范围内，且没有 min() 切换造成的折角
    HMAX = L - 0.010
    FMAX = 0.25 * S_W
    CEIL = math.sqrt(max(L * L - FMAX * FMAX, 0.0))
    DROP = max(HMAX - CEIL, 0.0)

    def _hip_z(p):
        return AZ0 + HMAX - DROP * (0.5 + 0.5 * math.cos(4 * math.pi * p))

    def _ik(fw, dz):
        """两骨逆解：目标 (前向, 向下) → (大腿角, 膝屈角)"""
        d = math.hypot(fw, dz)
        d = max(min(d, L - 0.004), abs(L1 - L2) + 0.004)
        phi = math.atan2(fw, dz)
        c1 = (d * d + L1 * L1 - L2 * L2) / (2 * d * L1)
        th = phi + math.acos(max(-1.0, min(1.0, c1)))
        c2 = (L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2)
        kn = math.pi - math.acos(max(-1.0, min(1.0, c2)))
        return th, kn

    _STAT = []
    for f in range(1, TOTAL + 1):
        t = (f - 1) / FPS_
        p = (t / CYCLE_S) % 1.0
        w = 2 * math.pi * p
        hz = _hip_z(p)
        # 先算出两条腿的脚尖前后位置，手臂按「同侧腿的实际位移」反相摆动 —— 完全同步
        _FMAX = max(0.25 * S_W, 1e-6)
        _fw = {}
        for _i, _tg in enumerate(("L", "R")):
            _q = (p + (0.0 if _i == 0 else 0.5)) % 1.0
            _fw[_tg] = _foot_target(_q)[0]
        for i, tag in enumerate(("L", "R")):
            off = 0.0 if i == 0 else 0.5
            q = (p + off) % 1.0
            fw, lift = _foot_target(q)
            th, kn = _ik(fw, hz - (AZ0 + lift))
            pb["thigh_" + tag].rotation_euler = Euler((th * S_TH, 0, 0))
            pb["shin_" + tag].rotation_euler = Euler((kn * S_KN, 0, 0))
            # 膝骨：取小腿屈曲的一半（真实甲片的膝盖只转一半）
            _pbk = pb.get("poleyn_" + tag)
            if _pbk is not None:
                _pbk.rotation_mode = 'XYZ'
                _pbk.rotation_euler = Euler((kn * S_KN * 0.2, 0, 0))
                _pbk.keyframe_insert("rotation_euler", frame=f)
            # 脚掌保持水平（抵消大腿+小腿的俯仰）
            pb["foot_" + tag].rotation_euler = Euler((-(th * S_TH + kn * S_KN), 0, 0))
            for bn in ("thigh_" + tag, "shin_" + tag, "foot_" + tag):
                pb[bn].keyframe_insert("rotation_euler", frame=f)
            # 手臂：跟同侧腿的真实摆动同步（腿在前 → 同侧手在后）
            _r = _fw[tag] / _FMAX
            arm = -ARM_SWAY * _r
            elb = ELBOW + 0.10 * _r
            pb["uparm_" + tag].rotation_euler = Euler((arm, 0, 0))
            pb["forearm_" + tag].rotation_euler = Euler((elb, 0, 0))
            pb["uparm_" + tag].keyframe_insert("rotation_euler", frame=f)
            pb["forearm_" + tag].keyframe_insert("rotation_euler", frame=f)
        # 骨盆：只转不移
        hitab = _tab((p + PHOFF) % 1.0, TAB_X)
        pb["spine"].rotation_euler = Euler((0.0, 0.0, HIP_ROLL * hitab))   # 侧倾放在脊柱：骨盆不动，腿根不受影响
        pb["spine"].keyframe_insert("rotation_euler", frame=f)
        # 上身三轴
        pb["chest"].rotation_euler = Euler((LEAN + 0.022 * math.cos(2 * w),
                                            0.050 * math.sin(w),
                                            0.016 * hitab))
        pb["chest"].keyframe_insert("rotation_euler", frame=f)
        pb["head"].rotation_euler = Euler((0.03 - 0.013 * math.cos(2 * w),
                                           -0.0375 * math.sin(w),
                                           0.004 * math.sin(w)))
        pb["head"].keyframe_insert("rotation_euler", frame=f)
        _ty = HERO_Y0 if INPLACE else HERO_Y0 - SPEED * t
        # 整机：先按解算髋高就位，再实测支撑脚把误差补掉（保证踩实、不随相位起伏）
        rig_o.location = Vector((HERO_X, _ty, hz - HZ0))
        bpy.context.view_layer.update()
        _pz = [(rig_o.matrix_world @ pb["foot_" + _g].head).z
               for _g in ("L", "R")
               if ((p + (0.0 if _g == "L" else 0.5)) % 1.0) < DUTY]
        if _pz:
            rig_o.location.z += AZ0 * _SC - min(_pz)
        rig_o.keyframe_insert("location", frame=f)
        cam.location = Vector((0.010 * math.sin(2 * math.pi * (t / CYCLE_S)),
                               (HERO_Y0 - D) - (0.0 if INPLACE else CF * SPEED * t), CZ))
        cam.keyframe_insert("location", frame=f)
        cam.rotation_euler = (Vector((0, _ty, AIMZ)) - cam.location)             .to_track_quat('-Z', 'Y').to_euler()
        cam.keyframe_insert("rotation_euler", frame=f)
    # ---- 姿态周期性证明：比较第 1 / 61 / 121 帧的骨骼矩阵 ----
    _snap = {}
    for _f in (1, 61, 121):
        if _f <= TOTAL:
            scn.frame_set(_f)
            bpy.context.view_layer.update()
            _snap[_f] = {_b.name: _b.matrix.copy() for _b in pb}
    _ks = sorted(_snap.keys())
    for _i in range(len(_ks) - 1):
        _a, _b2 = _ks[_i], _ks[_i + 1]
        _mx = 0.0
        for _n2 in _snap[_a]:
            for _r in range(4):
                for _c in range(4):
                    _mx = max(_mx, abs(_snap[_a][_n2][_r][_c] - _snap[_b2][_n2][_r][_c]))
        print("POSE f%d vs f%d  max|dMatrix| = %.3e" % (_a, _b2, _mx))

    for _tg in ("L", "R"):
        _ys, _zs, _n = [], [], 0
        for _f in range(1, min(TOTAL, 60) + 1):
            scn.frame_set(_f)
            bpy.context.view_layer.update()
            _q = (((_f - 1) / FPS_) / CYCLE_S + (0.0 if _tg == "L" else 0.5)) % 1.0
            if _q < DUTY:
                _w = rig_o.matrix_world @ pb["foot_" + _tg].head
                _ys.append(_w.y); _zs.append(_w.z); _n += 1
        if _n:
            print("PLANT %s %d/%d frames  Y drift %.2f mm  Z range %.2f mm  (Z %.4f)"
                  % (_tg, _n, min(TOTAL, 60), (max(_ys) - min(_ys)) * 1000,
                     (max(_zs) - min(_zs)) * 1000, _zs[0]))
    _hz = []
    for _f in range(1, min(TOTAL, 62) + 1):
        scn.frame_set(_f)
        bpy.context.view_layer.update()
        _hz.append((rig_o.matrix_world @ pb["hips"].head).z)
    print("BOB %.1f mm (%.2f%% of height)  SEAM dz %.3f mm  d(59-60) %.2f  d(60-61) %.2f mm"
          % ((max(_hz) - min(_hz)) * 1000, (max(_hz) - min(_hz)) * 1000 / 3480 * 100,
             abs(_hz[0] - _hz[60]) * 1000, (_hz[59] - _hz[58]) * 1000, (_hz[60] - _hz[59]) * 1000))
    # 只让"打角色"的灯跟随；洗墙灯(up_)、烛火、圣坛金光是建筑照明，留在世界里
    _HERO_LIGHTS = ("key", "rim", "fill", "halo")
    for _o in list(bpy.data.objects):
        if _o.type != 'LIGHT' or _o.name not in _HERO_LIGHTS:
            continue
        _y0 = _o.location.y
        for f in range(1, TOTAL + 1, 4):
            _o.location.y = _y0 + HERO_Y0 - SPEED * ((f - 1) / FPS_)
            _o.keyframe_insert("location", frame=f)
    scn.frame_start = int(arg("--fstart", "1"))
    scn.frame_end = int(arg("--fend", str(TOTAL)))
    print("ANIM", TOTAL, "frames", FPS_, "fps speed", SPEED, "cycle", CYCLE_S,
          "range", scn.frame_start, scn.frame_end,
          "travel", round(SPEED * TOTAL / FPS_, 2))


# ---------------------------------------------------------------- 渲染
scn.render.engine = 'CYCLES'
dev = "CPU"
ENG = arg("--engine", "CYCLES").upper()
if ENG == "EEVEE":
    scn.render.engine = 'BLENDER_EEVEE_NEXT'
    try:
        scn.eevee.taa_render_samples = int(arg("--csamples", "48"))
        scn.eevee.use_raytracing = True
        scn.eevee.volumetric_tile_size = '8'
        scn.eevee.volumetric_samples = 32
    except Exception as _e:
        print("EEVEE cfg", _e)
    print("ENGINE EEVEE", scn.render.engine)
else:
  prefs = bpy.context.preferences.addons["cycles"].preferences
  for t in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = t
        prefs.get_devices()
        if any(dd.type != 'CPU' for dd in prefs.devices):
            for dd in prefs.devices:
                dd.use = True
            scn.cycles.device = 'GPU'
            dev = t
            break
    except Exception:
        continue
  scn.cycles.samples = int(arg("--csamples", "256" if dev != "CPU" else "48"))
  scn.cycles.use_adaptive_sampling = True
  scn.cycles.adaptive_threshold = 0.01
  scn.cycles.use_denoising = True
  scn.cycles.max_bounces = 8
  scn.cycles.glossy_bounces = 6
  scn.cycles.volume_bounces = 2
scn.render.resolution_x = int(arg("--rw", "1920"))
scn.render.resolution_y = int(arg("--rh", "1080"))
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGB'
scn.view_settings.view_transform = 'AgX'
try:
    scn.view_settings.look = arg("--look", "AgX - Punchy")
except Exception as _e:
    print("LOOK fail", _e)
scn.view_settings.exposure = float(arg("--expo", "-0.30"))
out = os.path.abspath(arg("--still", "out/lux/lux1.png"))

# 后期：Fog Glow 泛光（参考图里窗光溢出的关键）
try:
    scn.use_nodes = True
    _nt = scn.node_tree
    _rl = _nt.nodes.get("Render Layers")
    _cmp = _nt.nodes.get("Composite")
    _gl = _nt.nodes.new("CompositorNodeGlare")
    _gl.glare_type = 'FOG_GLOW'
    _gl.quality = 'HIGH'
    _gl.threshold = float(arg("--glare_t", "0.90"))
    _gl.size = int(arg("--glare_s", "8"))
    _gl.mix = float(arg("--glare_m", "-0.38"))
    _nt.links.new(_rl.outputs["Image"], _gl.inputs["Image"])
    _nt.links.new(_gl.outputs["Image"], _cmp.inputs["Image"])
    print("GLARE ok")
except Exception as _e:
    print("GLARE fail", _e)
os.makedirs(os.path.dirname(out), exist_ok=True)
scn.render.filepath = out
try:
    scn.render.use_motion_blur = True
    scn.render.motion_blur_shutter = float(arg("--shutter", "0.35"))
except Exception:
    pass
if ANIM:
    _od = os.path.abspath(arg("--outdir", "out/anim"))
    os.makedirs(_od, exist_ok=True)
    scn.render.filepath = os.path.join(_od, "f_")
    scn.render.use_file_extension = True
    print("ANIM_RENDER", _od, scn.frame_start, scn.frame_end, "engine", scn.render.engine)
    bpy.ops.render.render(animation=True)
    print("ANIM_DONE", _od)
else:
    print("LUX_DEV", dev, "samples", scn.cycles.samples)
    bpy.ops.render.render(write_still=True)
    print("LUX_DONE", out)
