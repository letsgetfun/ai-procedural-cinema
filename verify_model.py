#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验仓库内的角色模型是否完整（SHA256 + 面数）。

    "Space Marine" by Janovich (https://sketchfab.com/janovich3D)
    License: CC-BY-4.0 — 见 docs/THIRD-PARTY.md

模型已随仓库分发；若校验失败，请从 Sketchfab 重新下载同名文件。
"""
import hashlib
import json
import os
import struct
import sys

DEST = os.path.join("model", "SM_tex270k.glb")
SHA256 = "d0dcf3b26355cf3e1d915d699a5e03975a8f7e2d984251b5ecbdd4c7eca78d3d"
FACES = 270268


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gltf_meta(path):
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        js = json.loads(f.read(clen).decode("utf-8"))
    return js.get("asset", {}).get("extras", {}), len(js.get("images", []))


def main():
    if not os.path.exists(DEST):
        sys.exit("missing %s — 见 model/README.md" % DEST)

    got = sha256(DEST)
    size = os.path.getsize(DEST)
    meta, nimg = gltf_meta(DEST)

    print("file   :", DEST)
    print("size   :", size)
    print("sha256 :", got)
    print("author :", meta.get("author"))
    print("license:", meta.get("license"))
    print("source :", meta.get("source"))
    print("images :", nimg)

    ok = True
    if got != SHA256:
        print("MISMATCH: 期望 %s" % SHA256)
        ok = False
    if meta.get("license", "").find("CC-BY") < 0:
        print("WARNING: 内嵌许可字段不是 CC-BY")
        ok = False

    print("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
