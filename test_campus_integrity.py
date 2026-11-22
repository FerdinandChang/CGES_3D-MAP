"""重慶國小 3D 校園導覽系統 — 自動化規格、門牌 Atlas、壓縮 GLB 與網頁資源完整性驗證腳本。"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    # 1. Verify campus_cges.json & room plaque atlas mapping
    spec = json.load(open(os.path.join(ROOT, "campus_cges.json"), encoding="utf-8"))
    atlas_map = json.load(open(os.path.join(ROOT, "textures", "room_plaques_atlas_map.json"), encoding="utf-8"))["entries"]
    total_rooms = 0
    missing_plaques = []
    for b in spec["buildings"]:
        bid = b["id"]
        for idx, rm in enumerate(b.get("rooms_115_detailed", [])):
            total_rooms += 1
            rname = rm.get("name", "")
            if "穿堂" in rname or "天橋" in rname:
                continue
            if f"{bid}:{idx}" not in atlas_map:
                missing_plaques.append(f"{bid}:{idx} ({rname})")
    assert total_rooms >= 127, f"Expected >=127 building rooms, got {total_rooms}"
    assert not missing_plaques, f"Missing room plaques in atlas: {missing_plaques}"

    # 2. Verify compressed GLB & build_meta.json synchronization
    meta = json.load(open(os.path.join(ROOT, "build_meta.json"), encoding="utf-8"))
    glb_path = os.path.join(ROOT, "exports", "cges_campus.glb")
    assert os.path.exists(glb_path), "Missing exports/cges_campus.glb"
    glb_bytes = os.path.getsize(glb_path)
    glb_hash = hashlib.md5(open(glb_path, "rb").read()).hexdigest()[:10]
    assert glb_bytes == meta["glb_bytes"], f"GLB size mismatch: {glb_bytes} != {meta['glb_bytes']}"
    assert glb_hash == meta["hash"], f"GLB hash mismatch: {glb_hash} != {meta['hash']}"
    assert glb_bytes < 8 * 1024 * 1024, f"Expected compressed GLB < 8MB, got {glb_bytes}"

    # 3. Verify index.html relative paths, OpenGraph meta & lazy map modal image
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for required in ('property="og:title"', 'property="og:image"', 'name="description"', 'data-src="./refs/cges_115_map.jpg"', '"./vendor/three/build/three.module.js"'):
        assert required in html, f"index.html missing required token: {required}"

    print(
        f"ALL_INTEGRITY_CHECKS_PASSED: {total_rooms} building rooms, "
        f"{len(atlas_map)} plaque entries, GLB={meta['glb_mb']}MB (hash={glb_hash})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
