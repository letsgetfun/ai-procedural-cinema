# 第三方素材与署名 / Third-party assets

本仓库的最终影像包含 **1 件**第三方素材，其余全部为本项目原创。

---

## 1. 角色模型 + 贴图（唯一第三方素材）

| 项 | 内容 |
|---|---|
| 标题 | Space Marine |
| 作者 | **Janovich** — <https://sketchfab.com/janovich3D> |
| 来源 | <https://sketchfab.com/3d-models/space-marine-650166abbb3448e9adece85e30b59c06> |
| Objaverse uid | `650166abbb3448e9adece85e30b59c06` |
| 许可 | **CC-BY-4.0** — <https://creativecommons.org/licenses/by/4.0/> |
| 规模 | 270,268 面 / 136,692 顶点 / 10 张 PBR 贴图 / 16 个材质 |
| 文件 | `model/SM_tex270k.glb` — **随本仓库分发**（CC-BY-4.0 允许再分发，保留署名即可） |
| SHA256 | `d0dcf3b26355cf3e1d915d699a5e03975a8f7e2d984251b5ecbdd4c7eca78d3d` |

### 本项目对该模型所做的修改

- 重新绑定骨骼与顶点权重（13 根骨骼，逐壳体判定 + 0.20 m 关节带过渡）
- 手势改为握拳、裆部中缝整体化、内侧大腿解冻
- 重建行走动作（IK 解算，非原始动画——该模型 `animationCount = 0`）
- 调整整体比例（×1.25）与朝向（面朝 −Y）
- 重做灯光、材质参数与色彩分级

### 建议的署名文本

```
"Space Marine" by Janovich (https://sketchfab.com/janovich3D)
Source: https://sketchfab.com/3d-models/space-marine-650166abbb3448e9adece85e30b59c06
License: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
Changes: re-rigged, re-weighted, new animation, retextured parameters, rescaled.
```

---

## 2. 本项目原创（无第三方权利）

| 内容 | 说明 |
|---|---|
| 哥特教堂几何（束柱 / 尖拱 / 肋拱 / 玫瑰窗 / 侧高窗 / 烛台） | 全部由 `lux_scene.py` 程序生成 |
| 王座（三层线脚 / 圆券滚边 / 珠链 / 织花丝绒） | 同上 |
| 丁达尔光刃、体积雾盒 | 同上 |
| 彩窗 / 玫瑰窗 / 红毯 / 织花 / 石材贴图 | `gen_*.py` 用 numpy 程序生成，无外部图片 |
| 骨骼、权重、动作 | `build_hero*.py` + `lux_scene.py` |
| 配乐与脚步音效 | `make_score30.py` 程序合成（正弦堆叠 + 卷积混响 + 限幅），无采样、无商业音乐 |
| 后期 LUT | `out/hald_grade.png`，本项目生成 |

---

## 3. 工具许可（不影响产出物的版权）

| 工具 | 许可 |
|---|---|
| Blender | GPL-2.0-or-later（**渲染产物不受 GPL 传染**，图像/视频归创作者） |
| ffmpeg | LGPL / GPL（视编译选项） |
| Python / numpy / scipy | PSF / BSD-3-Clause |

---

## 4. 已弃用、不包含在最终影像中的素材

| 素材 | 许可 | 说明 |
|---|---|---|
| OpenGameArt「Spacemarine」by Julius Krischan Makowka (jkm) | GPL-2.0-or-later **或** CC-BY-SA 3.0 | 早期 3,314 面版本使用，最终版**未使用**。注意 SA 条款具传染性 |
| CMU Graphics Lab Motion Capture Database | 允许任何用途 | 只在中期做过技术验证，未进入任何成片 |

---

## 5. 知识产权提醒

上述 CC-BY-4.0 仅覆盖 **模型作者对其建模成果** 的权利。
星际战士 / 动力甲 / 帝国鹰徽等视觉设计属于 **Games Workshop** 的《战锤 40,000》知识产权。
本许可不能替代 GW 的授权；商业化使用前请自行评估风险。
