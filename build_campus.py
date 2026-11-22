"""新北市板橋區重慶國小 3D 場景總裝管線：建置模型、匯出壓縮 GLB (Draco + WebP)、EEVEE 驗證圖與 Cycles 寫實光追靜態宣傳圖。"""
import argparse
import hashlib
import json
import os
import sys

import bpy

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import materials_cges as mc  # noqa: E402
import mod_campus_bldg as mb  # noqa: E402
import mod_campus_grounds as mg  # noqa: E402
import mod_campus_landmarks as ml  # noqa: E402
import mod_campus_street_details as ms  # noqa: E402
import studio_utils as su  # noqa: E402


def load_spec() -> dict:
    with open(os.path.join(ROOT_DIR, "campus_cges.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def assemble_campus(show_sat_ref: bool = False, use_nishita: bool = False) -> list[bpy.types.Object]:
    su.reset_scene()
    spec = load_spec()
    palette = mc.build_palette()

    objs: list[bpy.types.Object] = []
    objs.extend(mg.build_base_roads_and_city(spec, palette, show_sat_ref=show_sat_ref, include_horizon=use_nishita))

    for bcfg in spec["buildings"]:
        if bcfg["style"] == "guanghe_hero":
            objs.extend(mb.build_guanghe_building(bcfg, palette))
        else:
            objs.extend(mb.build_corridor_building(bcfg, palette))
    objs.extend(mb.build_guanghe_connector_bridges(spec, palette))

    objs.extend(mg.build_track_and_stage(spec, palette))
    objs.extend(mg.build_basketball_courts(spec, palette))
    objs.extend(mg.build_courtyard_and_trees(spec, palette))
    objs.extend(ml.build_main_gate_and_walls(spec, palette))
    objs.extend(ml.build_gym_and_skybridge(spec, palette))
    objs.extend(ms.build_vehicles_and_street_furniture(spec, palette))
    objs.extend(ms.build_building_signs_and_room_plaques(spec, palette))

    mc.setup_daylight(center=(-10.0, -5.0, 8.0), use_nishita=use_nishita)
    return objs


def render_perspective(
    name: str,
    loc: tuple[float, float, float],
    target: tuple[float, float, float],
    out_path: str,
    width: int = 1280,
    height: int = 720,
    lens: float = 30.0,
    samples: int = 24,
    engine: str = "BLENDER_EEVEE",
) -> None:
    backend = su.configure_render(engine=engine, width=width, height=height, samples=samples)
    if engine == "CYCLES":
        bpy.context.scene.view_settings.exposure = -0.35
        print(f"CYCLES_BACKEND ({name}): {backend}")
    cam = su.create_camera(name, loc, target, lens=lens)
    cam.data.clip_end = 1200.0
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    cam_data = cam.data
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-only", action="store_true", help="僅匯出 GLB 與 build_meta.json，跳過算圖")
    parser.add_argument("--no-draco", action="store_true", help="停用 Draco 幾何壓縮")
    parser.add_argument("--shots", type=str, default="", help="僅算指定機位關鍵字（逗號分隔）")
    parser.add_argument("--cycles-promo", action="store_true")
    parser.add_argument("--cycles-samples", type=int, default=64)
    args = parser.parse_args(argv)

    renders_dir = os.path.join(ROOT_DIR, "renders")
    exports_dir = os.path.join(ROOT_DIR, "exports")
    os.makedirs(renders_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)

    # 1. Clean campus assembly & compressed GLB export (WebP textures + Draco mesh compression)
    objs = assemble_campus(show_sat_ref=False, use_nishita=False)
    glb_path = os.path.join(exports_dir, "cges_campus.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_apply=True,
        export_image_format="WEBP",
        export_image_quality=88,
        export_draco_mesh_compression_enable=not args.no_draco,
        export_draco_mesh_compression_level=6,
    )

    with open(glb_path, "rb") as gf:
        glb_hash = hashlib.md5(gf.read()).hexdigest()[:10]
    glb_bytes = os.path.getsize(glb_path)
    meta_info = {
        "version": "12.7",
        "hash": glb_hash,
        "glb_bytes": glb_bytes,
        "glb_mb": round(glb_bytes / (1024 * 1024), 2),
        "objects": len(objs),
        "draco": not args.no_draco,
        "image_format": "WEBP",
    }
    with open(os.path.join(ROOT_DIR, "build_meta.json"), "w", encoding="utf-8") as mf:
        json.dump(meta_info, mf, ensure_ascii=False, indent=2)

    if args.export_only:
        print("CGES_EXPORT_DONE:" + json.dumps(meta_info, ensure_ascii=False))
        return

    # 2. Fast EEVEE verification renders
    shots = [
        ("Shot_V12_11_Gate_Forecourt_User", (-88.5, 4.0, 9.6), (-52.0, -15.0, 2.8), "cges_v12_11_gate_forecourt_user.png", 1280, 900, 35.0),
        ("Shot_V12_11_Gate_StreetView", (-78.0, 3.5, 2.75), (-51.5, -20.5, 2.3), "cges_v12_11_gate_streetview.png", 1280, 900, 36.0),
    ]
    shot_filters = [s.strip().lower() for s in args.shots.split(",") if s.strip()]
    for s_name, loc, tgt, fname, w, h, lens in shots:
        if shot_filters and not any(f in s_name.lower() or f in fname.lower() for f in shot_filters):
            continue
        render_perspective(s_name, loc, tgt, os.path.join(renders_dir, fname), width=w, height=h, lens=lens, samples=20, engine="BLENDER_EEVEE")

    # 3. Cycles Photorealistic Raytraced Promotional Renders (Nishita Physical Sky + GPU Denoise)
    cycles_files = []
    if args.cycles_promo:
        assemble_campus(show_sat_ref=False, use_nishita=True)
        promo_shots = [
            ("Cycles_Promo_Aerial", (-122.0, -104.0, 82.0), (-8.0, -2.0, 6.0), "cges_cycles_hero_aerial.png", 1920, 1080, 32.0),
            ("Cycles_Promo_Gate", (-88.5, -3.2, 4.2), (-46.0, 2.5, 9.8), "cges_cycles_gate_hero.png", 1920, 1080, 24.0),
            ("Cycles_Promo_Skybridge", (4.0, 52.0, 5.2), (-20.0, 52.0, 6.2), "cges_cycles_skybridge_hero.png", 1920, 1080, 24.0),
        ]
        for s_name, loc, tgt, fname, w, h, lens in promo_shots:
            out_p = os.path.join(renders_dir, fname)
            render_perspective(
                s_name,
                loc,
                tgt,
                out_p,
                width=w,
                height=h,
                lens=lens,
                samples=args.cycles_samples,
                engine="CYCLES",
            )
            cycles_files.append(out_p)

    report = {
        "glb": glb_path,
        "glb_bytes": os.path.getsize(glb_path),
        "objects": len(objs),
        "cycles_files": cycles_files,
        "renders_dir": renders_dir,
    }
    print("CGES_BUILD_REPORT:" + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
