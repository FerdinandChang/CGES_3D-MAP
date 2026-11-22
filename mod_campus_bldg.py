"""重慶國小高細節校舍建模模組（v3）：深凹細鋁窗、冷氣室外機群、走廊花台綠植、日光燈具、立體拱形山牆與穿堂扶手。"""
import math
from typing import Dict, List, Tuple

import bmesh
import bpy

import geom_primitives as gp
import studio_utils as su

_add_plane_uv = gp.add_plane_uv


def _add_detailed_window(
    bm_glass: bmesh.types.BMesh,
    bm_frame: bmesh.types.BMesh,
    center: tuple[float, float, float],
    width: float,
    height: float,
    axis: str = "Y",
    cols: int = 4,
    has_transom: bool = True,
) -> None:
    """建立真實台灣校園鋁門窗：外框＋多格直欞＋上部氣窗橫欞＋窗台遮陽線腳。"""
    cx, cy, cz = center
    depth = 0.14
    t = 0.055
    if axis == "Y":
        # Window plane lies in Y-Z, facing +-X
        gp.bm_box(bm_glass, (cx, cy, cz), (0.06, width - 0.10, height - 0.10))
        # Outer aluminum perimeter frame
        gp.bm_box(bm_frame, (cx, cy, cz + height * 0.5), (depth, width, t * 1.4))
        gp.bm_box(bm_frame, (cx, cy, cz - height * 0.5), (depth + 0.08, width + 0.08, t * 1.6))  # sill
        gp.bm_box(bm_frame, (cx, cy - width * 0.5, cz), (depth, t * 1.3, height))
        gp.bm_box(bm_frame, (cx, cy + width * 0.5, cz), (depth, t * 1.3, height))
        # Vertical mullions
        for i in range(1, cols):
            wy = cy - width * 0.5 + width * i / cols
            gp.bm_box(bm_frame, (cx, wy, cz), (depth * 0.85, t, height - 0.06))
        if has_transom:
            gp.bm_box(bm_frame, (cx, cy, cz + height * 0.22), (depth * 0.9, width - 0.06, t * 1.1))
    else:
        # Window plane lies in X-Z, facing +-Y
        gp.bm_box(bm_glass, (cx, cy, cz), (width - 0.10, 0.06, height - 0.10))
        gp.bm_box(bm_frame, (cx, cy, cz + height * 0.5), (width, depth, t * 1.4))
        gp.bm_box(bm_frame, (cx, cy, cz - height * 0.5), (width + 0.08, depth + 0.08, t * 1.6))
        gp.bm_box(bm_frame, (cx - width * 0.5, cy, cz), (t * 1.3, depth, height))
        gp.bm_box(bm_frame, (cx + width * 0.5, cy, cz), (t * 1.3, depth, height))
        for i in range(1, cols):
            wx = cx - width * 0.5 + width * i / cols
            gp.bm_box(bm_frame, (wx, cy, cz), (t, depth * 0.85, height - 0.06))
        if has_transom:
            gp.bm_box(bm_frame, (cx, cy, cz + height * 0.22), (width - 0.06, depth * 0.9, t * 1.1))


def _add_ac_unit(
    bm_body: bmesh.types.BMesh,
    bm_grille: bmesh.types.BMesh,
    pos: tuple[float, float, float],
    facing: str = "S",
) -> None:
    """建立台灣校舍標配之外掛冷氣室外機（主機箱＋圓形黑風扇格柵）。"""
    x, y, z = pos
    if facing in ("N", "S"):
        gp.bm_box(bm_body, (x, y, z), (0.86, 0.36, 0.62))
        dy = 0.19 if facing == "N" else -0.19
        gp.bm_cyl_axis(bm_grille, (x - 0.12, y + dy, z), 0.22, 0.05, axis="Y", segments=10)
    else:
        gp.bm_box(bm_body, (x, y, z), (0.36, 0.86, 0.62))
        dx = 0.19 if facing == "E" else -0.19
        gp.bm_cyl_axis(bm_grille, (x + dx, y - 0.12, z), 0.22, 0.05, axis="X", segments=10)


def _build_solar_array(
    name: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_roof: float,
    palette: Dict[str, bpy.types.Material],
    col: str,
    along_x: bool = True,
) -> List[bpy.types.Object]:
    objs: List[bpy.types.Object] = []
    bm_panels = bmesh.new()
    bm_frames = bmesh.new()

    margin = 1.2
    ax0, ax1 = x_min + margin, x_max - margin
    ay0, ay1 = y_min + margin, y_max - margin
    span_x = ax1 - ax0
    span_y = ay1 - ay0
    if span_x < 2.5 or span_y < 2.5:
        bm_panels.free()
        bm_frames.free()
        return objs

    if along_x:
        rows = max(2, int(span_y // 3.4))
        row_step = span_y / rows
        panel_d = min(2.6, row_step * 0.78)
        for r in range(rows):
            cy = ay0 + (r + 0.5) * row_step
            gp.bm_box(bm_panels, ((ax0 + ax1) * 0.5, cy, z_roof + 0.62), (span_x, panel_d, 0.08), rot_x=math.radians(8.0))
            n_posts = max(2, int(span_x // 6.0) + 1)
            for i in range(n_posts):
                px = ax0 + (span_x * i / max(1, n_posts - 1))
                gp.bm_box(bm_frames, (px, cy - panel_d * 0.3, z_roof + 0.30), (0.12, 0.12, 0.60))
                gp.bm_box(bm_frames, (px, cy + panel_d * 0.3, z_roof + 0.40), (0.12, 0.12, 0.80))
    else:
        cols = max(2, int(span_x // 3.4))
        col_step = span_x / cols
        panel_w = min(2.6, col_step * 0.78)
        n_seg = max(1, int(span_y // 18.0))
        seg_len = span_y / n_seg
        for s in range(n_seg):
            sy0 = ay0 + s * seg_len + 0.6
            sy1 = ay0 + (s + 1) * seg_len - 0.6
            slen = sy1 - sy0
            if slen < 2.0:
                continue
            for c in range(cols):
                cx = ax0 + (c + 0.5) * col_step
                gp.bm_box(bm_panels, (cx, (sy0 + sy1) * 0.5, z_roof + 0.62), (panel_w, slen, 0.08), rot_y=math.radians(-8.0))
                n_posts = max(2, int(slen // 6.0) + 1)
                for i in range(n_posts):
                    py = sy0 + (slen * i / max(1, n_posts - 1))
                    gp.bm_box(bm_frames, (cx - panel_w * 0.3, py, z_roof + 0.30), (0.12, 0.12, 0.60))
                    gp.bm_box(bm_frames, (cx + panel_w * 0.3, py, z_roof + 0.40), (0.12, 0.12, 0.80))

    objs.append(su.create_mesh_object(f"{name}_SolarPanels", bm_panels, palette["solar_panel"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object(f"{name}_SolarFrames", bm_frames, palette["steel_silver"], col, uv_scale=0.5))
    return objs


def _build_roof_water_tanks(
    name: str,
    anchor_pts: List[tuple[float, float]],
    z_roof: float,
    palette: Dict[str, bpy.types.Material],
    col: str,
) -> List[bpy.types.Object]:
    """D-05：在屋頂樓梯間屋突旁建置台灣校舍必備之亮面不鏽鋼圓柱儲水塔群、避雷針與太陽能逆變器箱。"""
    bm_tanks = bmesh.new()
    bm_frames = bmesh.new()
    for tx, ty in anchor_pts:
        # Pair of stainless steel cylindrical water tanks on legs
        for off in (-1.2, 1.2):
            gp.bm_cyl_axis(bm_tanks, (tx + off, ty, z_roof + 1.55), 0.72, 2.05, axis="Z", segments=14)
            gp.bm_cyl_p2p(bm_tanks, (tx + off, ty, z_roof + 2.58), (tx + off, ty, z_roof + 2.86), 0.72, 0.14, segments=14)
            # 4 support legs
            for lx, ly in [(-0.42, -0.42), (0.42, -0.42), (-0.42, 0.42), (0.42, 0.42)]:
                gp.bm_box(bm_frames, (tx + off + lx, ty + ly, z_roof + 0.30), (0.08, 0.08, 0.60))
        # Inverter cabinet & lightning rod mast
        gp.bm_box(bm_frames, (tx, ty + 1.45, z_roof + 0.62), (1.1, 0.45, 1.22))
        gp.bm_cyl_axis(bm_frames, (tx, ty - 1.55, z_roof + 2.4), 0.035, 4.8, axis="Z", segments=6)
    return [
        su.create_mesh_object(f"{name}_WaterTanks", bm_tanks, palette["water_tank_steel"], col, smooth=True),
        su.create_mesh_object(f"{name}_RoofEquip", bm_frames, palette["steel_silver"], col),
    ]


def build_guanghe_building(cfg: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置高細節廣和樓（5F 行政主棟）：止滑寬階梯＋不鏽鋼扶手、多格鋁窗、立體弧框校徽山牆、LED 畫面與屋頂太陽能板。"""
    col = "Bldg_Guanghe"
    prefix = cfg["id"]
    x0, x1 = cfg["x_min"], cfg["x_max"]
    y0, y1 = cfg["y_min"], cfg["y_max"]
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    wx, wy = x1 - x0, y1 - y0
    h1 = cfg["ground_floor_h"]
    hu = cfg["upper_floor_h"]
    floors = cfg["floors"]
    parapet = cfg["parapet_h"]
    z_roof = h1 + (floors - 1) * hu

    objs: List[bpy.types.Object] = []
    bm_wall = bmesh.new()
    bm_brick = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_floor = bmesh.new()
    bm_rail = bmesh.new()
    bm_steel = bmesh.new()
    bm_light = bmesh.new()

    # 1. 入口 11 階寬階梯 ＋ 兩側與中央不鏽鋼無障礙扶手（對照 campus_04.jpg）
    plinth_h = 1.15
    stair_w = 13.4
    stair_depth = 3.9
    steps = 11
    for i in range(steps):
        sh = plinth_h * (i + 1) / steps
        sd = stair_depth / steps
        sx = x0 - stair_depth + (i + 0.5) * sd
        gp.bm_box(bm_floor, (sx, cy, sh * 0.5), (sd + 0.04, stair_w, sh))
    # Stainless steel stair handrails
    for ry in (cy - stair_w * 0.48, cy - 2.4, cy + 2.4, cy + stair_w * 0.48):
        gp.bm_cyl_p2p(bm_steel, (x0 - stair_depth, ry, 0.95), (x0, ry, plinth_h + 0.95), 0.032, 0.032, segments=8)
        gp.bm_cyl_axis(bm_steel, (x0 - stair_depth + 0.1, ry, 0.48), 0.025, 0.95, axis="Z", segments=6)
        gp.bm_cyl_axis(bm_steel, (x0 - 0.1, ry, plinth_h + 0.48), 0.025, 0.95, axis="Z", segments=6)
    gp.bm_box(bm_floor, (cx, cy, plinth_h * 0.5), (wx, wy, plinth_h))

    # 2. 1F 結構：中央開放大穿堂＋兩翼（附細鋁窗）＋ 穿堂天花板日光燈
    breezeway_half = 5.3
    wing_y_n = (cy + breezeway_half, y1)
    wing_y_s = (y0, cy - breezeway_half)
    for wy0, wy1 in (wing_y_n, wing_y_s):
        gp.bm_box(bm_wall, (cx, (wy0 + wy1) * 0.5, plinth_h + (h1 - plinth_h) * 0.5), (wx - 0.4, wy1 - wy0, h1 - plinth_h))
        _add_detailed_window(bm_glass, bm_frame, (x0 - 0.05, (wy0 + wy1) * 0.5, plinth_h + 1.65), (wy1 - wy0) * 0.68, 1.48, axis="Y", cols=3)

    # 挑高 1-2F 川堂門廳 4 根厚實列柱 ＋ 穿堂內部柱列（外擴微偏移防 Cycles 共面黑塊！）＋ 馬賽克柱基（act_06.jpg）
    bm_mosaic = bmesh.new()
    bm_fan = bmesh.new()
    portico_h = h1 + hu
    col_ys = [cy - 5.2, cy - 2.0, cy + 2.0, cy + 5.2]
    for py in col_ys:
        # Upper column above plinth collar (non-overlapping Z to prevent Cycles Z-fighting!)
        gp.bm_box(bm_wall, (x0 + 0.45, py, plinth_h + 0.86 + (portico_h - plinth_h - 0.86) * 0.5), (0.86, 0.86, portico_h - plinth_h - 0.86))
        gp.bm_box(bm_brick, (x0 + 0.45, py, plinth_h + 0.43), (0.94, 0.94, 0.84))
        # Inner breezeway columns with colorful ecological mosaic lower halves (act_06.jpg)
        gp.bm_box(bm_mosaic, (x0 + 6.5, py, plinth_h + 0.90), (0.80, 0.80, 1.80))
        gp.bm_box(bm_wall, (x0 + 6.5, py, plinth_h + 1.80 + (h1 - plinth_h - 1.80) * 0.5), (0.74, 0.74, h1 - plinth_h - 1.80))
        gp.bm_box(bm_mosaic, (x1 - 2.2, py, plinth_h + 0.90), (0.80, 0.80, 1.80))
        gp.bm_box(bm_wall, (x1 - 2.2, py, plinth_h + 1.80 + (h1 - plinth_h - 1.80) * 0.5), (0.74, 0.74, h1 - plinth_h - 1.80))

    # D-01: Iconic Sky-Blue & Fluffy White Clouds Painted Breezeway Ceiling (act_01/02/03/07/21/24!)
    bm_sky_ceil = bmesh.new()
    zc = h1 - 0.06
    _add_plane_uv(bm_sky_ceil, (x0 + 0.8, cy - 5.1, zc), (x1 - 0.6, cy - 5.1, zc), (x1 - 0.6, cy + 5.1, zc), (x0 + 0.8, cy + 5.1, zc))
    # Painted blue transverse ceiling beams
    for bx_beam in (x0 + 6.5, x0 + 12.2, x1 - 2.2):
        gp.bm_box(bm_sky_ceil, (bx_beam, cy, h1 - 0.24), (0.48, 10.2, 0.34))
    objs.append(su.create_mesh_object(f"{prefix}_SkyCeiling", bm_sky_ceil, palette["sky_ceiling"], col, auto_uv=False))

    # Breezeway gray terrazzo floor overlay
    bm_terrazzo = bmesh.new()
    gp.bm_box(bm_terrazzo, (cx, cy, plinth_h + 0.025), (wx - 0.4, breezeway_half * 2.0, 0.04))
    objs.append(su.create_mesh_object(f"{prefix}_BreezewayTerrazzo", bm_terrazzo, palette["terrazzo_corridor"], col, uv_scale=0.35))

    # D-01: Orange-framed "勤學 健康 快樂" Honor Wall on inner breezeway north/south walls (campus_11.jpg!)
    bm_honor = bmesh.new()
    _add_plane_uv(bm_honor, (x0 + 4.5, cy + 5.12, plinth_h + 0.85), (x0 + 14.5, cy + 5.12, plinth_h + 0.85), (x0 + 14.5, cy + 5.12, plinth_h + 2.75), (x0 + 4.5, cy + 5.12, plinth_h + 2.75))
    _add_plane_uv(bm_honor, (x0 + 14.5, cy - 5.12, plinth_h + 0.85), (x0 + 4.5, cy - 5.12, plinth_h + 0.85), (x0 + 4.5, cy - 5.12, plinth_h + 2.75), (x0 + 14.5, cy - 5.12, plinth_h + 2.75))
    objs.append(su.create_mesh_object(f"{prefix}_HonorWalls", bm_honor, palette["honor_wall"], col, auto_uv=False))

    # D-01: Mobile award ceremony TV stand in breezeway center + 4 ceiling fans (act_03/04/05!)
    gp.bm_box(bm_fan, (x0 + 11.2, cy, plinth_h + 1.45), (0.16, 2.4, 1.45))
    gp.bm_box(bm_fan, (x0 + 11.2, cy, plinth_h + 0.45), (0.65, 1.8, 0.85))
    for fx in (x0 + 4.2, x0 + 9.2, x0 + 14.8):
        for fy in (cy - 2.4, cy + 2.4):
            gp.bm_cyl_axis(bm_fan, (fx, fy, h1 - 0.34), 0.14, 0.28, axis="Z", segments=8)
            for fa in (0, 60, 120):
                gp.bm_box(bm_fan, (fx, fy, h1 - 0.46), (1.15, 0.12, 0.025), rot_z=math.radians(fa))
    objs.append(su.create_mesh_object(f"{prefix}_PillarMosaic", bm_mosaic, palette["pillar_mosaic"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_BreezewayFansTV", bm_fan, palette["metal_dark"], col))

    # Breezeway ceiling linear LED tube fixtures
    for lx in (x0 + 3.5, x0 + 10.0, x0 + 16.5):
        for ly in (cy - 3.6, cy + 3.6):
            gp.bm_box(bm_light, (lx, ly, h1 - 0.16), (2.2, 0.16, 0.06))

    # 3. 2F（中央門廳退縮雙層挑空 + 陽台女兒牆 + 兩翼與深框 LED 螢幕）
    z2 = h1
    gp.bm_box(bm_floor, (cx + 1.8, cy, z2 + 0.15), (wx - 3.6, wy, 0.30))
    for wy0, wy1 in (wing_y_n, wing_y_s):
        gp.bm_box(bm_wall, (cx, (wy0 + wy1) * 0.5, z2 + hu * 0.5), (wx, wy1 - wy0, hu))
    gp.bm_box(bm_wall, (cx + 2.6, cy, z2 + hu * 0.5), (wx - 5.2, breezeway_half * 2.0, hu))
    gp.bm_box(bm_brick, (x0 + 2.4, cy, z2 + 0.55), (0.24, breezeway_half * 2.0, 1.0))
    gp.bm_box(bm_rail, (x0 + 2.4, cy, z2 + 1.15), (0.07, breezeway_half * 2.0, 0.07))
    # 2F north wing detailed window
    _add_detailed_window(bm_glass, bm_frame, (x0 - 0.04, y1 - 2.8, z2 + 1.9), 3.4, 1.48, axis="Y", cols=3)

    bm_salmon_gh = bmesh.new()
    bm_dark_gh = bmesh.new()

    # 4. 3F ~ 5F 主體（深凹鋁框細格窗＋磚紅水平飾帶＋雨庇＋東側半開放走廊）
    corridor_w = 2.5
    core_x1 = x1 - corridor_w
    for fl in range(2, floors):
        zf = h1 + (fl - 1) * hu
        gp.bm_box(bm_floor, (cx, cy, zf + 0.14), (wx - 0.16, wy - 0.16, 0.26))
        gp.bm_box(bm_wall, ((x0 + core_x1) * 0.5, cy, zf + hu * 0.5), (core_x1 - x0, wy, hu))
        win_z = zf + 2.02
        win_h = 1.48
        if fl < 4:
            # 3F & 4F: Central 6-bay aluminum ribbon window
            _add_detailed_window(bm_glass, bm_frame, (x0 - 0.05, cy, win_z), 11.4, win_h, axis="Y", cols=8)
        else:
            # 5F (exact 27 廣和街 step_4_shot_2.png & final_step_6.png!):
            # Flanking the central white emblem tower (cy +- 2.65) are recessed salmon-tile twin-tier blind panels (cy +- 2.65 .. cy +- 5.45)
            # bordered by full-height crisp white square-tile vertical pilasters at cy +- 5.70!
            for sgn_y in (-1.0, 1.0):
                rec_yc = cy + sgn_y * 4.05
                rec_w = 2.76
                # Recessed salmon-tile blind panel (lower 5F tier + upper parapet tier)
                gp.bm_box(bm_salmon_gh, (x0 - 0.06, rec_yc, zf + 2.38), (0.12, rec_w, 2.12))
                gp.bm_box(bm_salmon_gh, (x0 - 0.06, rec_yc, z_roof + 0.96), (0.12, rec_w, 1.48))
                # Projecting terracotta mid-transom band & top dark shadow eave over recessed bay
                gp.bm_box(bm_brick, (x0 - 0.20, rec_yc, z_roof + 0.04), (0.34, rec_w + 0.06, 0.36))
                gp.bm_box(bm_dark_gh, (x0 - 0.26, rec_yc, z_roof + 1.76), (0.44, rec_w + 0.08, 0.18))
                gp.bm_box(bm_wall, (x0 - 0.30, rec_yc, z_roof + 1.90), (0.50, rec_w + 0.12, 0.12))
                # Outer vertical white square-tile pilaster separating recessed bay from side wing
                gp.bm_box(bm_wall, (x0 - 0.24, cy + sgn_y * 5.72, 0.5 * (zf + 1.28 + z_roof + 2.18)), (0.44, 0.58, (z_roof + 2.18) - (zf + 1.28)))
        # Side wings: 2 crisp windows with projecting drip lintels
        for wy_mid in (y0 + 2.65, y1 - 2.65):
            _add_detailed_window(bm_glass, bm_frame, (x0 - 0.05, wy_mid, win_z), 3.3, win_h, axis="Y", cols=3)
            gp.bm_box(bm_wall, (x0 - 0.22, wy_mid, win_z + win_h * 0.5 + 0.08), (0.36, 3.55, 0.14))
        # North & south flank windows on east half (clear of x=-49.2..-43.6 North/South connector bridges!) + D-03 projecting sunshade!
        for side_y, sdir in ((y0 - 0.05, -1.0), (y1 + 0.05, 1.0)):
            _add_detailed_window(bm_glass, bm_frame, (x0 + 14.2, side_y, win_z), 5.6, win_h, axis="X", cols=4)
            gp.bm_box(bm_wall, (x0 + 14.2, side_y + sdir * 0.28, win_z + win_h * 0.5 + 0.09), (6.4, 0.56, 0.14))
        # Brick-red horizontal accent bands (extruded cleanly outside wall perimeter, zero Cycles Z-fighting!)
        gp.bm_box(bm_brick, (x0 - 0.06, cy, zf + 0.44), (0.12, wy + 0.24, 0.34))
        gp.bm_box(bm_brick, ((x0 + core_x1) * 0.5, y0 - 0.06, zf + 0.44), (core_x1 - x0 + 0.20, 0.12, 0.34))
        gp.bm_box(bm_brick, ((x0 + core_x1) * 0.5, y1 + 0.06, zf + 0.44), (core_x1 - x0 + 0.20, 0.12, 0.34))
        # East corridor facing courtyard
        gp.bm_box(bm_brick, (x1 - 0.14, cy, zf + 0.58), (0.24, wy, 1.02))
        gp.bm_box(bm_rail, (x1 - 0.14, cy, zf + 1.22), (0.07, wy, 0.07))
        for ci in range(5):
            py = y0 + 0.6 + ci * ((wy - 1.2) / 4.0)
            gp.bm_box(bm_wall, (x1 - 0.25, py, zf + hu * 0.5), (0.48, 0.48, hu))
        _add_detailed_window(bm_glass, bm_frame, (core_x1 + 0.04, cy, win_z), wy - 3.0, 1.42, axis="Y", cols=10)

    # 5. 屋頂四周女兒牆與兩翼階梯抬升女兒牆 ＋ 1:1 27 廣和街純白方磚校徽山牆＆淡粉紅磚矩形截面半圓鏤空拱圈
    gp.bm_box(bm_floor, (cx, cy, z_roof + 0.15), (wx, wy, 0.30))
    gp.bm_box(bm_wall, (cx, y0 + 0.2, z_roof + parapet * 0.5), (wx, 0.4, parapet))
    gp.bm_box(bm_wall, (cx, y1 - 0.2, z_roof + parapet * 0.5), (wx, 0.4, parapet))
    gp.bm_box(bm_wall, (x1 - 0.2, cy, z_roof + parapet * 0.5), (0.4, wy, parapet))
    gp.bm_box(bm_brick, (cx, y0 + 0.2, z_roof + parapet + 0.12), (wx + 0.24, 0.52, 0.24))
    gp.bm_box(bm_brick, (cx, y1 - 0.2, z_roof + parapet + 0.12), (wx + 0.24, 0.52, 0.24))
    gp.bm_box(bm_brick, (x1 - 0.2, cy, z_roof + parapet + 0.12), (0.52, wy + 0.24, 0.24))

    # Stepped-up outer wing parapets on west facade (y0..cy-5.45 & cy+5.45..y1, H=2.18m above roof + salmon waist band + dark red coping!)
    for sgn_w in (-1.0, 1.0):
        wy_c = 0.5 * ((cy + sgn_w * 5.45) + (y1 if sgn_w > 0 else y0))
        wy_l = abs((y1 if sgn_w > 0 else y0) - (cy + sgn_w * 5.45))
        gp.bm_box(bm_wall, (x0 + 0.16, wy_c, z_roof + 1.09), (0.44, wy_l, 2.18))
        gp.bm_box(bm_salmon_gh, (x0 - 0.08, wy_c, z_roof + 0.42), (0.12, wy_l + 0.04, 0.36))
        gp.bm_box(bm_brick, (x0 + 0.12, wy_c, z_roof + 2.24), (0.56, wy_l + 0.12, 0.14))
    # Rear rooftop lightning arrestor rods visible behind stepped parapets (step_4_shot_2.png!)
    for ly_rod in (cy - 8.2, cy - 6.4, cy - 3.8, cy + 3.8, cy + 6.4, cy + 8.2):
        gp.bm_cyl_axis(bm_dark_gh, (x0 + 0.55, ly_rod, z_roof + 2.55), 0.018, 2.40, axis="Z", segments=6)

    # Central protruding pure-white square-tile Emblem Tower Box (NO red brick side borders! exact final_step_6.png & step_2.png!)
    gable_w = 5.30
    z_emb_bot = z_roof - 2.10   # Sits cleanly right above 5F '勤學' banner top (15.70m)
    z_emb_top = z_roof + 2.15   # Arch springline (19.95m)
    emb_h = z_emb_top - z_emb_bot
    x_emb_front = x0 - 0.72
    x_emb_back = x0 + 0.18
    gp.bm_box(bm_wall, (0.5 * (x_emb_front + x_emb_back), cy, 0.5 * (z_emb_bot + z_emb_top)), (x_emb_back - x_emb_front, gable_w, emb_h))
    # Dark underside shadow reveal at bottom sill of white emblem box & top of arch sill
    gp.bm_box(bm_dark_gh, (0.5 * (x_emb_front + x0), cy, z_emb_bot - 0.03), (x0 - x_emb_front - 0.04, gable_w - 0.06, 0.06))
    gp.bm_box(bm_dark_gh, (0.5 * (x_emb_front + x_emb_back), cy, z_emb_top + 0.02), (x_emb_back - x_emb_front - 0.04, 3.80, 0.05))

    # True Rectangular-Cross-Section Semicircular Hollow Arch Ring in Salmon-Pink Tile (exact final_step_6.png!)
    # Outer width matches white emblem box width (r_out = gable_w * 0.5 = 2.65m), inner radius r_in = 1.98m (arch ring thickness 0.67m)!
    r_out_a = gable_w * 0.5
    r_in_a = 1.98
    r_intrados = 1.93
    spring_h = 0.34
    arch_zc = z_emb_top + spring_h
    # Short vertical springer legs at left/right before curving into semicircle
    leg_w = r_out_a - r_in_a
    for sgn_a in (-1.0, 1.0):
        ly_a = cy + sgn_a * (r_in_a + leg_w * 0.5)
        gp.bm_box(bm_salmon_gh, (0.5 * (x_emb_front + x_emb_back), ly_a, z_emb_top + spring_h * 0.5), (x_emb_back - x_emb_front, leg_w, spring_h))
        gp.bm_box(bm_dark_gh, (0.5 * (x_emb_front + x_emb_back), cy + sgn_a * (r_in_a - 0.025), z_emb_top + spring_h * 0.5), (x_emb_back - x_emb_front - 0.06, 0.05, spring_h))

    segs_arch = 28
    arch_faces = []
    intr_faces = []
    for i in range(segs_arch):
        a0 = math.pi * i / segs_arch
        a1 = math.pi * (i + 1) / segs_arch
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        # 8 vertices of rectangular-section salmon arch voussoir block
        yf_o0, zf_o0 = cy + c0 * r_out_a, arch_zc + s0 * r_out_a
        yf_o1, zf_o1 = cy + c1 * r_out_a, arch_zc + s1 * r_out_a
        yf_i0, zf_i0 = cy + c0 * r_in_a, arch_zc + s0 * r_in_a
        yf_i1, zf_i1 = cy + c1 * r_in_a, arch_zc + s1 * r_in_a
        vf_o0 = bm_salmon_gh.verts.new((x_emb_front, yf_o0, zf_o0))
        vf_o1 = bm_salmon_gh.verts.new((x_emb_front, yf_o1, zf_o1))
        vf_i1 = bm_salmon_gh.verts.new((x_emb_front, yf_i1, zf_i1))
        vf_i0 = bm_salmon_gh.verts.new((x_emb_front, yf_i0, zf_i0))
        vb_o0 = bm_salmon_gh.verts.new((x_emb_back, yf_o0, zf_o0))
        vb_o1 = bm_salmon_gh.verts.new((x_emb_back, yf_o1, zf_o1))
        vb_i1 = bm_salmon_gh.verts.new((x_emb_back, yf_i1, zf_i1))
        vb_i0 = bm_salmon_gh.verts.new((x_emb_back, yf_i0, zf_i0))
        arch_faces.extend([
            bm_salmon_gh.faces.new((vf_o0, vf_o1, vf_i1, vf_i0)),
            bm_salmon_gh.faces.new((vb_i0, vb_i1, vb_o1, vb_o0)),
            bm_salmon_gh.faces.new((vf_o0, vb_o0, vb_o1, vf_o1)),
            bm_salmon_gh.faces.new((vf_i1, vb_i1, vb_i0, vf_i0)),
        ])
        # Dark intrados inner soffit liner inside arch opening (exact dark inner shadow rim in final_step_6.png!)
        yi_0, zi_0 = cy + c0 * r_intrados, arch_zc + s0 * r_intrados
        yi_1, zi_1 = cy + c1 * r_intrados, arch_zc + s1 * r_intrados
        xf0, xf1 = x_emb_front + 0.03, x_emb_back - 0.03
        d_fo0 = bm_dark_gh.verts.new((xf0, yf_i0, zf_i0))
        d_fo1 = bm_dark_gh.verts.new((xf0, yf_i1, zf_i1))
        d_fi1 = bm_dark_gh.verts.new((xf0, yi_1, zi_1))
        d_fi0 = bm_dark_gh.verts.new((xf0, yi_0, zi_0))
        d_bo0 = bm_dark_gh.verts.new((xf1, yf_i0, zf_i0))
        d_bo1 = bm_dark_gh.verts.new((xf1, yf_i1, zf_i1))
        d_bi1 = bm_dark_gh.verts.new((xf1, yi_1, zi_1))
        d_bi0 = bm_dark_gh.verts.new((xf1, yi_0, zi_0))
        intr_faces.extend([
            bm_dark_gh.faces.new((d_fo0, d_fo1, d_fi1, d_fi0)),
            bm_dark_gh.faces.new((d_bi0, d_bi1, d_bo1, d_bo0)),
            bm_dark_gh.faces.new((d_fi1, d_bi1, d_bi0, d_fi0)),
        ])
    bmesh.ops.recalc_face_normals(bm_salmon_gh, faces=arch_faces)
    bmesh.ops.recalc_face_normals(bm_dark_gh, faces=intr_faces)
    objs.append(su.create_mesh_object(f"{prefix}_ArchSalmonTile", bm_salmon_gh, palette["wall_salmon"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object(f"{prefix}_ArchDarkTrim", bm_dark_gh, palette["metal_dark"], col))

    # 2F right-side LED screen frame (dark metal housing)
    bm_led_box = bmesh.new()
    gp.bm_box(bm_led_box, (x0 - 0.22, cy - 7.6, h1 + 1.85), (0.32, 3.6, 2.35))
    objs.append(su.create_mesh_object(f"{prefix}_LEDFrame", bm_led_box, palette["metal_dark"], col))
    bm_led_face = bmesh.new()
    lx = x0 - 0.40
    _add_plane_uv(bm_led_face, (lx, cy - 5.95, h1 + 0.80), (lx, cy - 9.25, h1 + 0.80), (lx, cy - 9.25, h1 + 2.90), (lx, cy - 5.95, h1 + 2.90))
    objs.append(su.create_mesh_object(f"{prefix}_LEDScreen", bm_led_face, palette["led_screen"], col, auto_uv=False))

    objs.append(su.create_mesh_object(f"{prefix}_Walls", bm_wall, palette["wall_guanghe"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object(f"{prefix}_BrickTrim", bm_brick, palette["wall_brick_red"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object(f"{prefix}_Windows", bm_glass, palette["window_glass"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_WindowFrames", bm_frame, palette["window_frame"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_SlabsStairs", bm_floor, palette["concrete_floor"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object(f"{prefix}_Railings", bm_rail, palette["railing_white"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_Handrails", bm_steel, palette["steel_silver"], col))
    objs.append(su.create_mesh_object(f"{prefix}_Lights", bm_light, palette["corridor_light"], col))

    # Emblem, 3F-5F banners & breezeway header
    bm_emb = bmesh.new()
    ex = x_emb_front - 0.012
    hw_emb = gable_w * 0.5 - 0.02
    _add_plane_uv(bm_emb, (ex, cy + hw_emb, z_emb_bot + 0.02), (ex, cy - hw_emb, z_emb_bot + 0.02), (ex, cy - hw_emb, z_emb_top - 0.02), (ex, cy + hw_emb, z_emb_top - 0.02))
    objs.append(su.create_mesh_object(f"{prefix}_Emblem", bm_emb, palette["emblem_cges"], col, auto_uv=False))

    for fl_idx, key in ((2, "banner_3f"), (3, "banner_4f"), (4, "banner_5f")):
        zf = h1 + (fl_idx - 1) * hu
        bm_b = bmesh.new()
        bx = x0 - 0.16
        _add_plane_uv(bm_b, (bx, cy + 5.8, zf + 0.12), (bx, cy - 5.8, zf + 0.12), (bx, cy - 5.8, zf + 1.28), (bx, cy + 5.8, zf + 1.28))
        objs.append(su.create_mesh_object(f"{prefix}_{key}", bm_b, palette[key], col, auto_uv=False))

    # Breezeway header placed slightly proud of recess beam (no coplanar Z-fighting!)
    bm_hdr = bmesh.new()
    hx = x0 - 0.04
    _add_plane_uv(bm_hdr, (hx, cy + 4.8, h1 + 0.12), (hx, cy - 4.8, h1 + 0.12), (hx, cy - 4.8, h1 + 2.08), (hx, cy + 4.8, h1 + 2.08))
    objs.append(su.create_mesh_object(f"{prefix}_BreezewayHeader", bm_hdr, palette["breezeway_header"], col, auto_uv=False))

    if cfg.get("has_solar"):
        objs.extend(_build_solar_array(prefix, x0 + 1.5, x1 - 0.8, y0 + 0.8, y1 - 0.8, z_roof + 0.28, palette, col, along_x=True))
    # D-05 Roof stainless steel water tanks on SE corner of Guanghe roof
    objs.extend(_build_roof_water_tanks(prefix, [(x1 - 3.0, y0 + 2.8)], z_roof + 0.28, palette, col))

    return objs


def build_corridor_building(cfg: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置高細節 5F 半開放走廊教學棟（含細鋁框橫拉窗、冷氣室外機群、走廊花台綠植、天花板燈具與屋頂太陽能板）。"""
    prefix = cfg["id"]
    col = prefix
    x0, x1 = cfg["x_min"], cfg["x_max"]
    y0, y1 = cfg["y_min"], cfg["y_max"]
    wx, wy = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    along_x = wx >= wy

    floors = cfg["floors"]
    h1 = cfg["ground_floor_h"]
    hu = cfg["upper_floor_h"]
    parapet = cfg["parapet_h"]
    corridor_w = cfg.get("corridor_w", 2.4)
    corridor_sides = set(cfg.get("corridor_sides", []))
    bays = cfg.get("bays", 8)
    breezeways = set(cfg.get("breezeway_bay_indices", []))
    stairs = set(cfg.get("stair_bays", []))

    z_roof = h1 + (floors - 1) * hu

    core_x0 = x0 + (corridor_w if "west" in corridor_sides else 0.0)
    core_x1 = x1 - (corridor_w if "east" in corridor_sides else 0.0)
    core_y0 = y0 + (corridor_w if "south" in corridor_sides else 0.0)
    core_y1 = y1 - (corridor_w if "north" in corridor_sides else 0.0)

    objs: List[bpy.types.Object] = []
    bm_salmon = bmesh.new()
    bm_cream = bmesh.new()
    bm_brick = bmesh.new()
    bm_floor = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_rail = bmesh.new()
    bm_pad = bmesh.new()
    bm_ac = bmesh.new()
    bm_ac_g = bmesh.new()
    bm_light = bmesh.new()
    bm_plant = bmesh.new()
    bm_door = bmesh.new()
    bm_dado = bmesh.new()
    bm_terrazzo = bmesh.new()

    gp.bm_box(bm_floor, (cx, cy, 0.18), (wx, wy, 0.36))

    span_len = wx if along_x else wy
    bay_len = span_len / bays

    for fl in range(floors):
        zf = 0.0 if fl == 0 else (h1 + (fl - 1) * hu)
        fh = h1 if fl == 0 else hu

        if fl > 0:
            gp.bm_box(bm_floor, (cx, cy, zf + 0.14), (wx - 0.16, wy - 0.16, 0.26))

        for b in range(bays):
            if along_x:
                bx0 = x0 + b * bay_len
                bx1 = bx0 + bay_len
                bcx = (bx0 + bx1) * 0.5
                is_breezeway = (fl == 0 and b in breezeways)
                is_stair = (b in stairs)

                if not is_breezeway:
                    # Chongqing Bldg west bay (b=0) keeps its north corridor OPEN (56 廣和街 final_step_4.png!)
                    # Chongqing Bldg east bay (b=7, x=-15.375..-7.0) keeps its south corridor OPEN into the hollow semicircular balcony tower
                    # and recesses east of x=-9.85 to form the deep recessed L-shaped connector corridor into Wuquan Bldg! (3 廣和街 step_10_shot_1.png!)
                    is_cq_west_end = (prefix == "Bldg_Chongqing" and b == 0)
                    is_cq_east_end = (prefix == "Bldg_Chongqing" and b == bays - 1)
                    if is_cq_west_end:
                        c_y0, c_y1 = y0, core_y1
                    elif is_cq_east_end:
                        c_y0, c_y1 = core_y0, core_y1
                    else:
                        c_y0, c_y1 = (y0, y1) if is_stair else (core_y0, core_y1)
                    # Heping north street-facing wall uses cream tile + red brick structural frames (step_59.png!)
                    wall_bm = bm_cream if (prefix == "Bldg_Heping" and not is_stair) else bm_salmon
                    box_x0 = (bx0 + 0.10) if is_cq_west_end else bx0
                    box_x1 = (bx1 - 2.75) if is_cq_east_end else bx1
                    box_w = (box_x1 - box_x0) - 0.08
                    box_cx = 0.5 * (box_x0 + box_x1)
                    gp.bm_box(wall_bm, (box_cx, (c_y0 + c_y1) * 0.5, zf + fh * 0.5), (box_w, c_y1 - c_y0, fh))
                    win_w = (box_w * 0.78) if is_cq_east_end else (bay_len * 0.76)
                    win_h = 1.48 if (not is_stair or is_cq_east_end) else 2.25
                    win_z = zf + fh * 0.58
                    for side_y, face_dir in ((c_y0 - 0.05, "S"), (c_y1 + 0.05, "N")):
                        _add_detailed_window(bm_glass, bm_frame, (box_cx, side_y, win_z), win_w * 0.78 if not is_stair else win_w, win_h, axis="X", cols=3 if (is_stair or is_cq_east_end) else 4)
                        # D-02: Classroom corridor 1.2m lower light-gray tile dado + wooden sliding door (act_23.jpg!)
                        is_corr_face = (face_dir == "S" and "south" in corridor_sides) or (face_dir == "N" and "north" in corridor_sides)
                        sdir = -1.0 if face_dir == "S" else 1.0
                        if is_corr_face and (not is_stair or is_cq_west_end or is_cq_east_end):
                            gp.bm_box(bm_dado, (box_cx, side_y + sdir * 0.03, zf + 0.62), (box_w - 0.16, 0.06, 1.18))
                            if not is_cq_east_end:
                                gp.bm_box(bm_door, (bx0 + 0.88, side_y + sdir * 0.05, zf + 1.15), (1.05, 0.08, 2.15))
                        elif not is_stair:
                            # D-03: Deep projecting 0.55m concrete sunshade canopy above exterior windows (act_12/22!)
                            gp.bm_box(bm_cream, (bcx, side_y + sdir * 0.28, win_z + win_h * 0.5 + 0.09), (bay_len - 0.32, 0.56, 0.14))
                        # Projecting window planter boxes + greenery on Heping north facade (matching step_59.png!)
                        if prefix == "Bldg_Heping" and face_dir == "N" and fl >= 1 and not is_stair:
                            gp.bm_box(bm_cream, (bcx - bay_len * 0.22, side_y + 0.34, zf + 0.85), (2.2, 0.58, 0.65))
                            gp.bm_box(bm_plant, (bcx - bay_len * 0.22, side_y + 0.34, zf + 1.32), (2.0, 0.48, 0.42))
                            gp.bm_box(bm_brick, (bx0 + 0.25, side_y + 0.14, zf + fh * 0.5), (0.52, 0.26, fh))
                            gp.bm_box(bm_brick, (bcx, side_y + 0.12, zf + fh - 0.22), (bay_len, 0.24, 0.42))
                    # D-02: Terrazzo corridor floor strip with white center keep-right line (act_23.jpg!)
                    for side in corridor_sides:
                        if side in ("north", "south"):
                            in_y = (y1 - corridor_w * 0.5) if side == "north" else (y0 + corridor_w * 0.5)
                            gp.bm_box(bm_terrazzo, (bcx, in_y, zf + (0.37 if fl == 0 else 0.30)), (bay_len - 0.04, corridor_w - 0.35, 0.03))
                    # AC outdoor units mounted under corridor ceiling / beside windows (iconic Taiwan school look!)
                    if fl >= 1 and not is_stair:
                        if "south" in corridor_sides:
                            _add_ac_unit(bm_ac, bm_ac_g, (bx0 + 1.15, c_y0 - 0.24, zf + fh - 0.72), facing="S")
                        if "north" in corridor_sides:
                            _add_ac_unit(bm_ac, bm_ac_g, (bx1 - 1.15, c_y1 + 0.24, zf + fh - 0.72), facing="N")

                for side in corridor_sides:
                    if side not in ("north", "south"):
                        continue
                    is_cq_west_north = (prefix == "Bldg_Chongqing" and b == 0 and side == "north")
                    is_cq_east_south = (prefix == "Bldg_Chongqing" and b == bays - 1 and side == "south")
                    is_cq_east_north = (prefix == "Bldg_Chongqing" and b == bays - 1 and side == "north")
                    edge_y = (y1 - 0.16) if side == "north" else (y0 + 0.16)
                    in_y = (y1 - corridor_w * 0.5) if side == "north" else (y0 + corridor_w * 0.5)
                    # v12.3: On Chongqing b=7 south face, the hollow semicircular balcony tower + recessed L-corridor own x=-15.375..-7.0!
                    if is_cq_east_south:
                        gp.bm_box(bm_salmon, (bx0 + 0.25, edge_y, zf + fh * 0.5), (0.52, 0.52, fh))
                        gp.bm_box(bm_light, (bcx - 1.2, in_y, zf + fh - 0.18), (1.4, 0.14, 0.06))
                        continue
                    # v6 Street-View Exact Palette (27 廣和街): Salmon-pink outer structural columns & beams + Cream-white corridor parapet!
                    gp.bm_box(bm_salmon, (bx0 + 0.25, edge_y, zf + fh * 0.5), (0.52, 0.52, fh))
                    if b == bays - 1:
                        gp.bm_box(bm_salmon, (bx1 - 0.25, edge_y, zf + fh * 0.5), (0.52, 0.52, fh))
                    gp.bm_box(bm_light, (bcx, in_y, zf + fh - 0.18), (1.4, 0.14, 0.06))
                    if fl >= 1 and (not is_stair or is_cq_west_north or is_cq_east_north):
                        gp.bm_box(bm_cream, (bcx, edge_y, zf + 0.56), (bay_len - 0.48, 0.24, 0.96))
                        gp.bm_box(bm_rail, (bcx, edge_y, zf + 1.24), (bay_len - 0.48, 0.065, 0.065))
                        gp.bm_box(bm_rail, (bcx, edge_y, zf + 1.08), (bay_len - 0.48, 0.045, 0.045))
                        gp.bm_box(bm_salmon, (bcx, edge_y, zf + fh - 0.24), (bay_len, 0.42, 0.48))
                        if (b + fl) % 2 == 0 and not is_cq_east_north:
                            gp.bm_box(bm_plant, (bcx, edge_y + (0.18 if side == "north" else -0.18), zf + 1.08), (1.8, 0.32, 0.28))
                    elif fl == 0:
                        gp.bm_box(bm_salmon, (bcx, edge_y, zf + fh - 0.24), (bay_len, 0.42, 0.48))
            else:
                by0 = y0 + b * bay_len
                by1 = by0 + bay_len
                bcy = (by0 + by1) * 0.5
                is_wq = (prefix == "Bldg_Wuquan")
                is_wq_south_solid = (is_wq and b <= 4)
                # Read open 1F breezeway indices directly from JSON spec (synchronized: Wuquan=[6, 8, 12]!)
                is_breezeway = (fl == 0 and b in breezeways)
                is_stair = False if is_wq else (b in stairs)

                if not is_breezeway:
                    if is_wq_south_solid:
                        # South wing (b=0..4, 9 五權街 step_6_shot_1.png): west corridor open, EAST face is flush classroom wall (NO east corridor!)
                        c_x0, c_x1 = core_x0, x1 - 0.14
                    else:
                        c_x0, c_x1 = (x0, x1) if is_stair else (core_x0, core_x1)
                    body_bm = bm_cream if is_wq_south_solid else bm_salmon
                    gp.bm_box(body_bm, ((c_x0 + c_x1) * 0.5, bcy, zf + fh * 0.5), (c_x1 - c_x0, bay_len - 0.08, fh))
                    win_w = bay_len * 0.76
                    win_h = 1.48 if not is_stair else 2.25
                    win_z = zf + fh * 0.58
                    for side_x, face_dir in ((c_x0 - 0.05, "W"), (c_x1 + 0.05, "E")):
                        is_corr_face = (face_dir == "W" and "west" in corridor_sides) or (face_dir == "E" and "east" in corridor_sides and not is_wq_south_solid)
                        sdir = -1.0 if face_dir == "W" else 1.0
                        if is_wq and face_dir == "E" and fl == 0 and b >= 5:
                            # v12.5: Wuquan 1F mid-north east facade (shutters, classrooms, Stair 9 glass/lattice) is built in dedicated 1:1 block below!
                            continue
                        if is_wq_south_solid and face_dir == "E":
                            # 9 五權街 exact east-facing twin-sub-bay windows (b=4 leaves north half solid for 1F-5F vertical school banner!)
                            sub_centers = [by0 + bay_len * 0.25] if b == 4 else [by0 + bay_len * 0.25, by0 + bay_len * 0.75]
                            for sy_w in sub_centers:
                                _add_detailed_window(bm_glass, bm_frame, (side_x, sy_w, zf + fh * 0.48), bay_len * 0.39, 1.42, axis="Y", cols=3)
                            continue
                        _add_detailed_window(bm_glass, bm_frame, (side_x, bcy, win_z), win_w * 0.78 if not is_stair else win_w, win_h, axis="Y", cols=4 if not is_stair else 3)
                        if is_corr_face and not is_stair:
                            gp.bm_box(bm_dado, (side_x + sdir * 0.03, bcy, zf + 0.62), (0.06, bay_len - 0.16, 1.18))
                            gp.bm_box(bm_door, (side_x + sdir * 0.05, by0 + 0.88, zf + 1.15), (0.08, 1.05, 2.15))
                        elif not is_stair:
                            gp.bm_box(bm_cream, (side_x + sdir * 0.28, bcy, win_z + win_h * 0.5 + 0.09), (0.56, bay_len - 0.32, 0.14))
                    for side in corridor_sides:
                        if side in ("west", "east"):
                            if side == "east" and is_wq_south_solid:
                                continue
                            in_x = (x1 - corridor_w * 0.5) if side == "east" else (x0 + corridor_w * 0.5)
                            gp.bm_box(bm_terrazzo, (in_x, bcy, zf + (0.37 if fl == 0 else 0.30)), (corridor_w - 0.35, bay_len - 0.04, 0.03))
                    if fl >= 1 and not is_stair:
                        if "east" in corridor_sides and not is_wq_south_solid:
                            _add_ac_unit(bm_ac, bm_ac_g, (c_x1 + 0.24, by0 + 1.15, zf + fh - 0.72), facing="E")
                        if "west" in corridor_sides:
                            _add_ac_unit(bm_ac, bm_ac_g, (c_x0 - 0.24, by1 - 1.15, zf + fh - 0.72), facing="W")

                for side in corridor_sides:
                    if side not in ("west", "east"):
                        continue
                    edge_x = (x1 - 0.16) if side == "east" else (x0 + 0.16)
                    in_x = (x1 - corridor_w * 0.5) if side == "east" else (x0 + corridor_w * 0.5)
                    # Outer structural columns + mid-bay sub-column on Wuquan east face for exact 9/2 五權街 pillar rhythm!
                    col_bm_outer = bm_cream if (is_wq_south_solid and side == "east" and b <= 3) else bm_salmon
                    gp.bm_box(col_bm_outer, (edge_x, by0 + 0.25, zf + fh * 0.5), (0.52, 0.52, fh))
                    if is_wq and side == "east":
                        if b <= 3:
                            gp.bm_box(bm_cream, (edge_x + 0.04, bcy, zf + fh * 0.5), (0.42, 0.42, fh))
                        elif b >= 5 and b != 6 and b != 8 and not (b == 12 and fl == 0):
                            gp.bm_box(bm_salmon, (edge_x, bcy, zf + fh * 0.5), (0.48, 0.48, fh))
                    if b == bays - 1:
                        gp.bm_box(bm_salmon, (edge_x, by1 - 0.25, zf + fh * 0.5), (0.52, 0.52, fh))
                    if not (is_wq_south_solid and side == "east"):
                        gp.bm_box(bm_light, (in_x, bcy, zf + fh - 0.18), (0.14, 1.4, 0.06))
                    if fl >= 1 and not is_stair:
                        # v11.8: Keep Wuquan Bldg 2F east corridor bay b=6 (y=-17.85..-9.65) OPEN into the attached assembly stage 2F terrace!
                        # v12.3: Keep Wuquan Bldg west corridor bay b=3 (y=-42.42..-34.23) OPEN into Chongqing Bldg L-shaped corner junction!
                        is_stage_terrace_open = (is_wq and side == "east" and fl == 1 and b == 6)
                        is_cq_junction_open = (is_wq and side == "west" and b == 3)
                        if is_wq_south_solid and side == "east":
                            # Flush classroom wall spandrel beam only (no open corridor parapet!)
                            gp.bm_box(bm_salmon, (edge_x, bcy, zf + fh - 0.22), (0.44, bay_len, 0.44))
                        elif is_wq and side == "east":
                            # v12.5 2 五權街 EXACT 2F-5F EAST CORRIDOR: recessed cream-tile wall + alternating projecting wide cream planter boxes & red-brick decorative squares!
                            if not is_stage_terrace_open:
                                gp.bm_box(bm_cream, (edge_x - 0.02, bcy, zf + 0.52), (0.22, bay_len - 0.44, 0.94))
                                if 5 <= b <= 11:
                                    # Split bay into 2 architectural sub-bays matching exact 9/2 五權街 cadence (aligned vertically 2F-5F!)
                                    for sub_i, sub_yc in enumerate((by0 + bay_len * 0.25, by0 + bay_len * 0.75)):
                                        if (b * 2 + sub_i) % 2 == 0:
                                            # Wide projecting cream-tile planter box (+0.38m proud) + organic foliage tufts
                                            gp.bm_box(bm_cream, (edge_x + 0.26, sub_yc, zf + 0.50), (0.42, 3.10, 0.78))
                                            gp.bm_box(bm_plant, (edge_x + 0.26, sub_yc - 0.55, zf + 0.98), (0.34, 1.35, 0.34))
                                            gp.bm_box(bm_plant, (edge_x + 0.28, sub_yc + 0.62, zf + 0.94), (0.30, 0.95, 0.28))
                                        else:
                                            # Projecting cream-tile frame with iconic centered recessed dark-red brick decorative square!
                                            gp.bm_box(bm_cream, (edge_x + 0.22, sub_yc, zf + 0.52), (0.34, 2.35, 0.78))
                                            gp.bm_box(bm_brick, (edge_x + 0.38, sub_yc, zf + 0.52), (0.08, 0.58, 0.50))
                            gp.bm_box(bm_salmon, (edge_x, bcy, zf + fh - 0.24), (0.44, bay_len, 0.48))
                        else:
                            if not is_stage_terrace_open and not is_cq_junction_open:
                                gp.bm_box(bm_cream, (edge_x, bcy, zf + 0.56), (0.24, bay_len - 0.48, 0.96))
                                gp.bm_box(bm_rail, (edge_x, bcy, zf + 1.24), (0.065, bay_len - 0.48, 0.065))
                                gp.bm_box(bm_rail, (edge_x, bcy, zf + 1.08), (0.045, bay_len - 0.48, 0.045))
                                if (b + fl) % 2 == 0:
                                    gp.bm_box(bm_plant, (edge_x + (0.18 if side == "east" else -0.18), bcy, zf + 1.08), (0.32, 1.8, 0.28))
                            gp.bm_box(bm_salmon, (edge_x, bcy, zf + fh - 0.24), (0.42, bay_len, 0.48))
                    elif fl == 0:
                        gp.bm_box(bm_salmon, (edge_x, bcy, zf + fh - 0.24), (0.42, bay_len, 0.48))

    # Roof slab, parapet walls & stair towers
    gp.bm_box(bm_floor, (cx, cy, z_roof + 0.15), (wx, wy, 0.30))
    gp.bm_box(bm_salmon, (cx, y0 + 0.18, z_roof + parapet * 0.5), (wx, 0.36, parapet))
    gp.bm_box(bm_salmon, (cx, y1 - 0.18, z_roof + parapet * 0.5), (wx, 0.36, parapet))
    gp.bm_box(bm_salmon, (x0 + 0.18, cy, z_roof + parapet * 0.5), (0.36, wy, parapet))
    gp.bm_box(bm_salmon, (x1 - 0.18, cy, z_roof + parapet * 0.5), (0.36, wy, parapet))
    if prefix == "Bldg_Wuquan":
        # Exact 2 五權街 step_10_shot_1.png: Single salmon-pink roof stair penthouse above north-mid section (Stair 9, y=+20.5)
        gp.bm_box(bm_salmon, (cx + 1.2, 20.5, z_roof + 1.75), (6.4, 5.4, 3.3))
        gp.bm_box(bm_cream, (cx + 1.2, 20.5, z_roof + 3.45), (6.6, 5.6, 0.18))
    else:
        for sb in stairs:
            if along_x:
                scx = x0 + (sb + 0.5) * bay_len
                gp.bm_box(bm_cream, (scx, cy, z_roof + 1.65), (min(5.2, bay_len * 0.8), min(6.0, wy * 0.65), 3.1))
            else:
                scy = y0 + (sb + 0.5) * bay_len
                gp.bm_box(bm_cream, (cx, scy, z_roof + 1.65), (min(6.0, wx * 0.65), min(5.2, bay_len * 0.8), 3.1))

    objs.append(su.create_mesh_object(f"{prefix}_Walls", bm_salmon, palette["wall_salmon"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object(f"{prefix}_ColumnsBeams", bm_cream, palette["wall_guanghe"], col, uv_scale=0.35))
    if len(bm_brick.verts) > 0:
        objs.append(su.create_mesh_object(f"{prefix}_CorridorParapet", bm_brick, palette["wall_brick_red"], col, uv_scale=0.45))
    else:
        bm_brick.free()
    objs.append(su.create_mesh_object(f"{prefix}_Slabs", bm_floor, palette["concrete_floor"], col, uv_scale=0.3))
    objs.append(su.create_mesh_object(f"{prefix}_Windows", bm_glass, palette["window_glass"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_WindowFrames", bm_frame, palette["window_frame"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_Railings", bm_rail, palette["metal_dark"], col, uv_scale=0.5))

    # v6 Front NW Corner (10 廣和街): Heping Bldg West Gable Solid Cream Tile Facade + Vertical Gold "重慶國小" Sign!
    if prefix == "Bldg_Heping":
        bm_gable = bmesh.new()
        bm_gwin = bmesh.new()
        bm_gfrm = bmesh.new()
        # Solid cream tile west end-wall cladding covering stair core
        gp.bm_box(bm_gable, (x0 - 0.14, cy + 0.8, z_roof * 0.5 + 0.5), (0.28, wy - 2.2, z_roof + 1.0))
        # Narrow horizontal clerestory strip windows on north side of west gable (10 廣和街 left!)
        for fl_g in range(1, floors):
            zg = h1 + (fl_g - 1) * hu + 2.0
            _add_detailed_window(bm_gwin, bm_gfrm, (x0 - 0.30, y1 - 2.3, zg), 2.2, 0.88, axis="Y", cols=3, has_transom=False)
        objs.append(su.create_mesh_object(f"{prefix}_WestGableWall", bm_gable, palette["wall_guanghe"], col, uv_scale=0.35))
        objs.append(su.create_mesh_object(f"{prefix}_WestGableWin", bm_gwin, palette["window_glass"], col))
        objs.append(su.create_mesh_object(f"{prefix}_WestGableFrame", bm_gfrm, palette["window_frame"], col))
        # Iconic vertical dark-brown slat board with gold vertical "重慶國小" (spanning 2F-4F!)
        bm_vsign = bmesh.new()
        vx = x0 - 0.36
        _add_plane_uv(bm_vsign, (vx, cy + 2.3, 4.4), (vx, cy - 1.3, 4.4), (vx, cy - 1.3, 14.6), (vx, cy + 2.3, 14.6))
        objs.append(su.create_mesh_object(f"{prefix}_VerticalSchoolSign", bm_vsign, palette["heping_vert_sign"], col, auto_uv=False))
    objs.append(su.create_mesh_object(f"{prefix}_ACUnits", bm_ac, palette["ac_unit"], col))
    objs.append(su.create_mesh_object(f"{prefix}_ACGrilles", bm_ac_g, palette["ac_grille"], col))
    objs.append(su.create_mesh_object(f"{prefix}_CorridorLights", bm_light, palette["corridor_light"], col))
    objs.append(su.create_mesh_object(f"{prefix}_ClassroomDoors", bm_door, palette["classroom_door"], col))
    objs.append(su.create_mesh_object(f"{prefix}_CorridorDado", bm_dado, palette["wall_guanghe"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object(f"{prefix}_CorridorTerrazzo", bm_terrazzo, palette["terrazzo_corridor"], col, uv_scale=0.45))

    if prefix == "Bldg_Chongqing":
        objs.extend(_build_chongqing_west_gable(prefix, x0, y0, y1, core_y0, core_y1, floors, h1, hu, z_roof, palette, col))

    if prefix == "Bldg_Wuquan":
        objs.extend(_build_wuquan_end_gables(prefix, y0, y1, core_x0, core_x1, floors, h1, hu, z_roof, parapet, palette, col))
        objs.extend(_build_wuquan_east_facade(prefix, x1, y0, cx, wx, core_x1, bays, bay_len, floors, h1, hu, z_roof, palette, col))

    if len(bm_plant.verts) > 0:
        objs.append(su.create_mesh_object(f"{prefix}_CorridorPlanters", bm_plant, palette["tree_foliage_b"], col))
    else:
        bm_plant.free()
    if len(bm_pad.verts) > 0:
        objs.append(su.create_mesh_object(f"{prefix}_CourtPads", bm_pad, palette["pad_green"], col))
    else:
        bm_pad.free()

    if cfg.get("has_solar"):
        objs.extend(_build_solar_array(prefix, x0 + 0.8, x1 - 0.8, y0 + 0.8, y1 - 0.8, z_roof + 0.28, palette, col, along_x=along_x))

    # D-05: Roof stainless steel water tanks beside stair headhouses
    tank_pts = []
    for sb in sorted(stairs)[:2]:
        if along_x:
            tank_pts.append((x0 + (sb + 0.5) * bay_len, cy + 3.4))
        else:
            tank_pts.append((cx - 3.2, y0 + (sb + 0.5) * bay_len))
    if tank_pts:
        objs.extend(_build_roof_water_tanks(prefix, tank_pts, z_roof + 0.28, palette, col))

    return objs


def _build_chongqing_west_gable(
    prefix: str,
    x0: float,
    y0: float,
    y1: float,
    core_y0: float,
    core_y1: float,
    floors: int,
    h1: float,
    hu: float,
    z_roof: float,
    palette: Dict[str, bpy.types.Material],
    col: str,
) -> List[bpy.types.Object]:
    """建置重慶樓 2F 彩繪火車壁畫與 56 廣和街西山牆（雙開間米白方磚嵌板＋紅磚結構框＋2-4F 方窗＋開放北走廊＋綠鐵皮斜頂棚）。"""
    objs: List[bpy.types.Object] = []
    bm_train = bmesh.new()
    ty_m = core_y0 - 0.10
    _add_plane_uv(bm_train, (-62.0, ty_m, 3.85), (-46.0, ty_m, 3.85), (-46.0, ty_m, 6.45), (-62.0, ty_m, 6.45))
    objs.append(su.create_mesh_object(f"{prefix}_LibraryTrainMural", bm_train, palette["train_mural"], col, auto_uv=False))

    bm_wg_frame = bmesh.new()
    bm_wg_panel = bmesh.new()
    bm_wg_seam = bmesh.new()
    bm_wg_win = bmesh.new()
    bm_wg_wfrm = bmesh.new()
    bm_wg_steel = bmesh.new()
    bm_wg_green = bmesh.new()
    bm_wg_blue = bmesh.new()
    bm_wg_lantern = bmesh.new()

    z_top_gable = z_roof + 2.0
    y_col_n_outer = y1 - 0.28
    y_col_n_inner = core_y1 - 0.30
    y_col_mid = -38.65
    y_col_s_outer = y0 + 0.30
    for yc in (y_col_n_inner, y_col_mid, y_col_s_outer):
        gp.bm_box(bm_wg_frame, (x0 - 0.03, yc, z_top_gable * 0.5), (0.28, 0.60, z_top_gable))
    gp.bm_box(bm_wg_frame, (x0 - 0.03, y_col_n_outer, z_top_gable * 0.5), (0.28, 0.56, z_top_gable))

    beam_zs = [0.20, h1, h1 + hu, h1 + 2 * hu, h1 + 3 * hu, z_roof, z_top_gable - 0.20]
    for idx_b, bz in enumerate(beam_zs):
        bh = 0.52 if idx_b not in (0, len(beam_zs) - 1) else 0.42
        gp.bm_box(bm_wg_frame, (x0 - 0.03, (y0 + core_y1) * 0.5, bz), (0.28, core_y1 - y0 + 0.02, bh))
        if idx_b >= 1:
            gp.bm_box(bm_wg_frame, (x0 - 0.03, (core_y1 + y1) * 0.5, bz), (0.28, y1 - core_y1, bh * 0.92))

    tier_ranges = [
        (0.40, h1 - 0.26),
        (h1 + 0.26, h1 + hu - 0.26),
        (h1 + hu + 0.26, h1 + 2 * hu - 0.26),
        (h1 + 2 * hu + 0.26, h1 + 3 * hu - 0.26),
        (h1 + 3 * hu + 0.26, z_roof - 0.26),
        (z_roof + 0.26, z_top_gable - 0.40),
    ]
    y_wide_0, y_wide_1 = y_col_mid + 0.29, y_col_n_inner - 0.29
    y_narr_0, y_narr_1 = y_col_s_outer + 0.29, y_col_mid - 0.29
    for t_idx, (zt0, zt1) in enumerate(tier_ranges):
        th = zt1 - zt0
        tz = (zt0 + zt1) * 0.5
        gp.bm_box(bm_wg_panel, (x0 + 0.02, (y_wide_0 + y_wide_1) * 0.5, tz), (0.14, y_wide_1 - y_wide_0, th))
        for frac in (1.0 / 3.0, 2.0 / 3.0):
            ys = y_wide_0 + (y_wide_1 - y_wide_0) * frac
            gp.bm_box(bm_wg_seam, (x0 - 0.055, ys, tz), (0.015, 0.035, th - 0.04))
        gp.bm_box(bm_wg_panel, (x0 + 0.02, (y_narr_0 + y_narr_1) * 0.5, tz), (0.14, y_narr_1 - y_narr_0, th))
        gp.bm_box(bm_wg_seam, (x0 - 0.055, (y_narr_0 + y_narr_1) * 0.5, tz), (0.015, 0.035, th - 0.04))
        if t_idx in (1, 2, 3):
            win_y = y_narr_1 - 0.80
            win_z = zt0 + 0.64
            _add_detailed_window(bm_wg_win, bm_wg_wfrm, (x0 - 0.08, win_y, win_z), 1.32, 1.12, axis="Y", cols=2, has_transom=False)

    corr_cy = (core_y1 + y1) * 0.5
    corr_span = (y1 - core_y1) - 0.58
    gp.bm_box(bm_wg_panel, (x0 + 0.02, corr_cy, (z_roof + 0.26 + z_top_gable - 0.40) * 0.5), (0.14, corr_span, (z_top_gable - 0.40) - (z_roof + 0.26)))
    for fl_c in range(1, floors):
        zfc = h1 + (fl_c - 1) * hu
        gp.bm_box(bm_wg_panel, (x0 - 0.02, corr_cy, zfc + 0.52), (0.20, corr_span, 0.96))
        gp.bm_box(bm_wg_steel, (x0 - 0.02, corr_cy, zfc + 1.12), (0.05, corr_span + 0.04, 0.05))
        gp.bm_box(bm_wg_steel, (x0 - 0.02, corr_cy, zfc + 1.28), (0.05, corr_span + 0.04, 0.05))
    gp.bm_box(bm_wg_blue, (x0 + 2.4, corr_cy, h1 + 2 * hu - 0.08), (4.6, corr_span + 0.3, 0.06))
    gp.bm_box(bm_wg_green, (x0 - 1.15, corr_cy + 0.1, 3.02), (2.25, 2.75, 0.12), rot_y=math.radians(-14.0))
    gp.bm_box(bm_wg_steel, (x0 - 2.24, corr_cy + 0.1, 2.74), (0.06, 2.78, 0.12))
    for ly_lan in (corr_cy - 0.55, corr_cy + 0.55):
        gp.bm_cyl_axis(bm_wg_steel, (x0 - 1.45, ly_lan, 2.78), 0.015, 0.36, axis="Z", segments=6)
        gp.bm_cyl_axis(bm_wg_lantern, (x0 - 1.45, ly_lan, 2.46), 0.22, 0.34, axis="Z", segments=12)

    gp.bm_box(bm_wg_green, (x0 - 1.45, -40.2, 2.86), (2.95, 6.4, 0.14), rot_y=math.radians(-16.0))
    gp.bm_box(bm_wg_steel, (x0 - 2.86, -40.2, 2.46), (0.07, 6.46, 0.14))
    for sy_p in (-43.1, -40.2, -37.3):
        gp.bm_cyl_axis(bm_wg_steel, (x0 - 2.65, sy_p, 1.24), 0.055, 2.48, axis="Z", segments=8)

    objs.append(su.create_mesh_object(f"{prefix}_WestGableBrickGrid", bm_wg_frame, palette["wall_brick_red"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableCreamPanels", bm_wg_panel, palette["wall_guanghe"], col, uv_scale=0.42))
    objs.append(su.create_mesh_object(f"{prefix}_WestGablePanelSeams", bm_wg_seam, palette["metal_dark"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableSmallWins", bm_wg_win, palette["window_glass"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableWinFrames", bm_wg_wfrm, palette["window_frame"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableSteelRails", bm_wg_steel, palette["steel_silver"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableGreenCanopies", bm_wg_green, palette["side_gate_green"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableBlueCeil", bm_wg_blue, palette["shelter_navy"], col))
    objs.append(su.create_mesh_object(f"{prefix}_WestGableLanterns", bm_wg_lantern, palette["lamp_globe"], col, smooth=True))
    return objs


def _build_wuquan_end_gables(
    prefix: str,
    y0: float,
    y1: float,
    core_x0: float,
    core_x1: float,
    floors: int,
    h1: float,
    hu: float,
    z_roof: float,
    parapet: float,
    palette: Dict[str, bpy.types.Material],
    col: str,
) -> List[bpy.types.Object]:
    """建置五權樓南端山牆（y=-67.0）與北端和平路 2F–5F 雙開間紅磚花格窗面（y=+39.5）。"""
    objs: List[bpy.types.Object] = []
    bm_wq_f = bmesh.new()
    bm_wq_p = bmesh.new()
    bm_wq_s = bmesh.new()
    bm_wq_w = bmesh.new()
    bm_wq_wf = bmesh.new()
    bm_wq_lat = bmesh.new()
    z_top_wq = z_roof + parapet
    x_w0, x_w1 = core_x0 + 0.10, core_x1 - 0.10
    x_wm = (x_w0 + x_w1) * 0.5

    gy, sgn = y0 - 0.02, -1.0
    for xc in (x_w0, x_wm, x_w1):
        gp.bm_box(bm_wq_f, (xc, gy + sgn * 0.04, z_top_wq * 0.5), (0.56, 0.24, z_top_wq))
    for bz in (0.20, h1, h1 + hu, h1 + 2 * hu, h1 + 3 * hu, z_roof, z_top_wq - 0.18):
        gp.bm_box(bm_wq_f, (x_wm, gy + sgn * 0.04, bz), (x_w1 - x_w0 + 0.56, 0.24, 0.46))
    for zt0, zt1 in [
        (0.42, h1 - 0.24), (h1 + 0.24, h1 + hu - 0.24), (h1 + hu + 0.24, h1 + 2 * hu - 0.24),
        (h1 + 2 * hu + 0.24, h1 + 3 * hu - 0.24), (h1 + 3 * hu + 0.24, z_roof - 0.24), (z_roof + 0.24, z_top_wq - 0.36),
    ]:
        tz, th = 0.5 * (zt0 + zt1), zt1 - zt0
        for px0, px1 in ((x_w0 + 0.28, x_wm - 0.28), (x_wm + 0.28, x_w1 - 0.28)):
            gp.bm_box(bm_wq_p, (0.5 * (px0 + px1), gy - sgn * 0.02, tz), (px1 - px0, 0.14, th))
            gp.bm_box(bm_wq_s, (0.5 * (px0 + px1), gy + sgn * 0.055, tz), (0.03, 0.015, th - 0.04))

    gy_n = y1 + 0.04
    for xc_n in (-6.65, -4.10, 0.55, 6.20):
        gp.bm_box(bm_wq_f, (xc_n, gy_n + 0.06, (h1 + z_top_wq) * 0.5), (0.62, 0.28, z_top_wq - h1))
    for bz_n in (h1 + 0.15, h1 + hu, h1 + 2 * hu, h1 + 3 * hu, z_roof, z_top_wq - 0.16):
        gp.bm_box(bm_wq_f, (-0.22, gy_n + 0.06, bz_n), (13.45, 0.28, 0.42))
    for fl_n in range(1, floors):
        zfn = h1 + (fl_n - 1) * hu
        for bx0_n, bx1_n in [(-3.75, 0.18), (0.92, 5.85)]:
            bcx_n = 0.5 * (bx0_n + bx1_n)
            bw_n = bx1_n - bx0_n
            gp.bm_box(bm_wq_p, (bcx_n, gy_n - 0.01, zfn + 0.65), (bw_n, 0.16, 0.92))
            _add_detailed_window(bm_wq_w, bm_wq_wf, (bcx_n, gy_n + 0.03, zfn + 1.82), bw_n - 0.14, 1.38, axis="X", cols=4, has_transom=False)
            _add_plane_uv(bm_wq_lat, (bx1_n - 0.04, gy_n + 0.10, zfn + 2.56), (bx0_n + 0.04, gy_n + 0.10, zfn + 2.56), (bx0_n + 0.04, gy_n + 0.10, zfn + 3.16), (bx1_n - 0.04, gy_n + 0.10, zfn + 3.16))
    objs.append(su.create_mesh_object(f"{prefix}_EndGablesBrickGrid", bm_wq_f, palette["wall_brick_red"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object(f"{prefix}_EndGablesCreamPanels", bm_wq_p, palette["wall_guanghe"], col, uv_scale=0.42))
    objs.append(su.create_mesh_object(f"{prefix}_EndGablesPanelSeams", bm_wq_s, palette["metal_dark"], col))
    objs.append(su.create_mesh_object(f"{prefix}_NorthGableWindows", bm_wq_w, palette["window_glass"], col))
    objs.append(su.create_mesh_object(f"{prefix}_NorthGableWinFrames", bm_wq_wf, palette["window_frame"], col))
    objs.append(su.create_mesh_object(f"{prefix}_NorthGableLattice", bm_wq_lat, palette["brick_lattice_band"], col, auto_uv=False))
    return objs


def _build_wuquan_east_facade(
    prefix: str,
    x1: float,
    y0: float,
    cx: float,
    wx: float,
    core_x1: float,
    bays: int,
    bay_len: float,
    floors: int,
    h1: float,
    hu: float,
    z_roof: float,
    palette: Dict[str, bpy.types.Material],
    col: str,
) -> List[bpy.types.Object]:
    """建置五權樓東立面 1:1 實景細節（南翼紅磚花格帶、1F–5F 直立彩繪宣傳布條、無障礙長斜坡、三開間大寬階梯、9 梯服務立面與北端彩繪寬階梯）。"""
    objs: List[bpy.types.Object] = []
    bm_e_cream = bmesh.new()
    bm_e_slab = bmesh.new()
    bm_e_trim = bmesh.new()
    bm_e_dark = bmesh.new()
    bm_e_steel = bmesh.new()
    bm_e_lat = bmesh.new()
    bm_e_shut = bmesh.new()
    bm_e_fglass = bmesh.new()
    bm_e_wglass = bmesh.new()
    bm_e_wfrm = bmesh.new()
    bm_e_vban = bmesh.new()
    bm_e_bban = bmesh.new()
    bm_e_mural = bmesh.new()

    def _add_sloped_cheek_x(bm_c: bmesh.types.BMesh, y_s: float, y_n: float, xz_pts: List[Tuple[float, float]]) -> None:
        vs0 = [bm_c.verts.new((px_v, y_s, pz_v)) for px_v, pz_v in xz_pts]
        vs1 = [bm_c.verts.new((px_v, y_n, pz_v)) for px_v, pz_v in xz_pts]
        f_new = [bm_c.faces.new(vs0), bm_c.faces.new(list(reversed(vs1)))]
        nn = len(xz_pts)
        for ii in range(nn):
            jj = (ii + 1) % nn
            f_new.append(bm_c.faces.new((vs0[ii], vs1[ii], vs1[jj], vs0[jj])))
        bmesh.ops.recalc_face_normals(bm_c, faces=f_new)

    def _add_sloped_wall_along_y(bm_c: bmesh.types.BMesh, x_in: float, x_out: float, yz_pts: List[Tuple[float, float]]) -> None:
        vs0 = [bm_c.verts.new((x_in, py_v, pz_v)) for py_v, pz_v in yz_pts]
        vs1 = [bm_c.verts.new((x_out, py_v, pz_v)) for py_v, pz_v in yz_pts]
        f_new = [bm_c.faces.new(vs0), bm_c.faces.new(list(reversed(vs1)))]
        nn = len(yz_pts)
        for ii in range(nn):
            jj = (ii + 1) % nn
            f_new.append(bm_c.faces.new((vs0[ii], vs1[ii], vs1[jj], vs0[jj])))
        bmesh.ops.recalc_face_normals(bm_c, faces=f_new)

    # (1) South Wing (b=0..4) Red-Brick Lattice Clerestory Bands above every east window
    for fl_l in range(floors):
        zf_l = 0.0 if fl_l == 0 else (h1 + (fl_l - 1) * hu)
        fh_l = h1 if fl_l == 0 else hu
        zl0 = zf_l + fh_l * 0.48 + 0.72
        zl1 = zf_l + fh_l - 0.44
        if zl1 > zl0 + 0.14:
            for b_l in range(5):
                by0_l = y0 + b_l * bay_len
                sub_cs = [by0_l + bay_len * 0.25] if b_l == 4 else [by0_l + bay_len * 0.25, by0_l + bay_len * 0.75]
                hw_l = bay_len * 0.195
                for sy_l in sub_cs:
                    _add_plane_uv(
                        bm_e_lat,
                        (x1 - 0.08, sy_l - hw_l, zl0), (x1 - 0.08, sy_l + hw_l, zl0),
                        (x1 - 0.08, sy_l + hw_l, zl1), (x1 - 0.08, sy_l - hw_l, zl1),
                    )

    # (2) Full-Height 1F-5F Vertical Illustrated School Banner (b=4 north half: y=-30.55..-26.85, z=0.88..17.06!)
    vb_y0, vb_y1 = -30.55, -26.85
    vb_z0, vb_z1 = 0.88, z_roof - 0.12
    vb_x = x1 + 0.12
    gp.bm_box(bm_e_cream, (x1 - 0.02, 0.5 * (vb_y0 + vb_y1), 0.5 * (vb_z0 + vb_z1)), (0.24, vb_y1 - vb_y0 + 0.08, vb_z1 - vb_z0 + 0.10))
    _add_plane_uv(bm_e_vban, (vb_x, vb_y0, vb_z0), (vb_x, vb_y1, vb_z0), (vb_x, vb_y1, vb_z1), (vb_x, vb_y0, vb_z1))
    for bz_bar in (vb_z0 - 0.03, vb_z1 + 0.03):
        gp.bm_box(bm_e_steel, (vb_x - 0.02, 0.5 * (vb_y0 + vb_y1), bz_bar), (0.08, vb_y1 - vb_y0 + 0.14, 0.07))

    # Two Iconic 2F Deep-Blue White-Text Horizontal Plaques
    for by_s0, by_s1, bx_s in [(-25.45, -22.55, x1 + 0.38), (10.75, 13.75, x1 + 0.38)]:
        gp.bm_box(bm_e_dark, (bx_s - 0.04, 0.5 * (by_s0 + by_s1), h1 + 0.52), (0.06, by_s1 - by_s0 + 0.06, 0.54))
        _add_plane_uv(bm_e_bban, (bx_s, by_s0, h1 + 0.28), (bx_s, by_s1, h1 + 0.28), (bx_s, by_s1, h1 + 0.76), (bx_s, by_s0, h1 + 0.76))

    # (3) 1F Accessible Long Ramp Walkway (y=-34.2..-20.55)
    rp_y0, rp_y_top, rp_y1 = -34.20, -23.00, -20.55
    rp_x_in, rp_x_out = x1 - 0.04, x1 + 1.68
    rp_z_lo, rp_z_hi = 0.04, 1.12
    _add_sloped_wall_along_y(bm_e_slab, rp_x_in, rp_x_out - 0.22, [
        (rp_y0, 0.02), (rp_y_top, 0.02), (rp_y_top, rp_z_hi), (rp_y0, rp_z_lo + 0.04),
    ])
    gp.bm_box(bm_e_slab, (0.5 * (rp_x_in + rp_x_out - 0.22), 0.5 * (rp_y_top + rp_y1), rp_z_hi - 0.14), (rp_x_out - 0.22 - rp_x_in, rp_y1 - rp_y_top, 0.28))
    gp.bm_box(bm_e_dark, (rp_x_out - 0.55, 0.5 * (rp_y_top + rp_y1), 0.44), (0.85, rp_y1 - rp_y_top - 0.28, 0.84))
    gp.bm_box(bm_e_trim, (rp_x_out - 0.16, 0.5 * (rp_y_top + rp_y1), 0.18), (0.32, rp_y1 - rp_y_top - 0.45, 0.30))
    gp.bm_box(bm_e_cream, (rp_x_out - 0.12, rp_y1 - 0.12, rp_z_hi * 0.5), (0.24, 0.24, rp_z_hi))
    _add_sloped_wall_along_y(bm_e_cream, rp_x_out - 0.24, rp_x_out, [
        (rp_y0, 0.02), (rp_y_top, 0.02), (rp_y_top, rp_z_hi + 0.86), (rp_y0, rp_z_lo + 0.86),
    ])
    gp.bm_box(bm_e_cream, (rp_x_out - 0.12, 0.5 * (rp_y_top + rp_y1), rp_z_hi + 0.31), (0.24, rp_y1 - rp_y_top, 1.10))
    for hx_r, hz_off in ((rp_x_out - 0.12, 0.94), (rp_x_in + 0.14, 0.88)):
        gp.bm_cyl_p2p(bm_e_steel, (hx_r, rp_y0, rp_z_lo + hz_off), (hx_r, rp_y_top, rp_z_hi + hz_off), 0.028, 0.028, segments=8)
        gp.bm_cyl_p2p(bm_e_steel, (hx_r, rp_y_top, rp_z_hi + hz_off), (hx_r, rp_y1, rp_z_hi + hz_off), 0.028, 0.028, segments=8)
        for k_rp in range(6):
            ty_k = rp_y0 + (rp_y_top - rp_y0) * (k_rp / 5.0)
            tz_k = rp_z_lo + (rp_z_hi - rp_z_lo) * (k_rp / 5.0)
            gp.bm_cyl_p2p(bm_e_steel, (hx_r, ty_k, tz_k + (0.84 if hx_r > x1 + 1.0 else 0.02)), (hx_r, ty_k, tz_k + hz_off), 0.020, 0.020, segments=6)

    # (4) 2F-5F Mid-North East Corridor Twin Silver Stainless Guardrails + Stair 9 Rainwater Pipe
    for fl_r in range(1, floors):
        zf_r = h1 + (fl_r - 1) * hu
        for b_r in range(5, bays):
            if fl_r == 1 and b_r == 6:
                continue
            by0_r = y0 + b_r * bay_len + 0.24
            by1_r = y0 + (b_r + 1) * bay_len - 0.24
            for rz_off in (1.06, 1.22):
                gp.bm_cyl_p2p(bm_e_steel, (x1 - 0.14, by0_r, zf_r + rz_off), (x1 - 0.14, by1_r, zf_r + rz_off), 0.024, 0.024, segments=8)
            for p_frac in (0.12, 0.37, 0.63, 0.88):
                py_p = by0_r + (by1_r - by0_r) * p_frac
                gp.bm_cyl_p2p(bm_e_steel, (x1 - 0.14, py_p, zf_r + 0.92), (x1 - 0.14, py_p, zf_r + 1.24), 0.018, 0.018, segments=6)
    gp.bm_cyl_p2p(bm_e_steel, (x1 + 0.14, 27.38, 0.10), (x1 + 0.14, 27.38, z_roof + 0.15), 0.065, 0.065, segments=10)
    for rz_c in (2.2, 5.4, 8.8, 12.2, 15.6):
        gp.bm_box(bm_e_steel, (x1 + 0.06, 27.38, rz_c), (0.18, 0.16, 0.07))

    # (5a) b=5 South 1F Gray Metal Roll-Up Shutter behind Accessible Ramp Landing
    gp.bm_box(bm_e_cream, (core_x1 + 0.08, -23.2, 1.80), (0.18, 4.95, 3.55))
    _add_plane_uv(bm_e_shut, (core_x1 + 0.20, -25.10, 1.05), (core_x1 + 0.20, -21.20, 1.05), (core_x1 + 0.20, -21.20, 3.35), (core_x1 + 0.20, -25.10, 3.35))
    gp.bm_box(bm_e_slab, (0.5 * (core_x1 + x1), -23.2, 0.52), (x1 - core_x1, 5.10, 1.04))

    # (5b) 2 五權街 GRAND 3-BAY WIDE STAIRCASE + TWIN GRAY SHUTTERS + OPEN CENTER BREEZEWAY
    gs_y0, gs_y1 = -4.20, 10.20
    gs_x0, gs_x1 = x1 - 0.05, x1 + 2.85
    gs_h = 1.08
    n_gs = 7
    for si in range(n_gs):
        sh = gs_h * (si + 1) / n_gs
        sd = (gs_x1 - gs_x0) / n_gs
        sx_c = gs_x1 - (si + 0.5) * sd
        gp.bm_box(bm_e_slab, (sx_c, 0.5 * (gs_y0 + gs_y1), sh * 0.5), (sd + 0.04, gs_y1 - gs_y0 - 0.52, sh))
    xz_gs_cheek = [
        (gs_x0, 0.02), (gs_x1 + 0.12, 0.02), (gs_x1 + 0.12, 0.72),
        (gs_x0 + 0.35, gs_h + 0.88), (gs_x0, gs_h + 0.88),
    ]
    _add_sloped_cheek_x(bm_e_cream, gs_y0, gs_y0 + 0.28, xz_gs_cheek)
    _add_sloped_cheek_x(bm_e_cream, gs_y1 - 0.28, gs_y1, xz_gs_cheek)
    gp.bm_box(bm_e_slab, (0.5 * (core_x1 + x1), 0.5 * (gs_y0 + gs_y1), gs_h * 0.5), (x1 - core_x1 + 0.10, gs_y1 - gs_y0, gs_h))
    gp.bm_box(bm_e_slab, (cx, 2.63, 0.52), (wx - 0.2, 8.10, 1.04))
    for sh_y0_g, sh_y1_g in [(-3.80, -1.65), (6.95, 9.75)]:
        gp.bm_box(bm_e_cream, (core_x1 + 0.06, 0.5 * (sh_y0_g + sh_y1_g), 2.30), (0.16, sh_y1_g - sh_y0_g + 0.30, 2.60))
        _add_plane_uv(bm_e_shut, (core_x1 + 0.18, sh_y0_g, gs_h), (core_x1 + 0.18, sh_y1_g, gs_h), (core_x1 + 0.18, sh_y1_g, 3.32), (core_x1 + 0.18, sh_y0_g, 3.32))

    # (5c) Mid-North 1F Cream Classroom Facade
    gp.bm_box(bm_e_cream, (x1 - 0.26, 0.5 * (10.20 + 23.12), 1.80), (0.28, 23.12 - 10.20, 3.56))
    for wy_c, ww_c in [(12.25, 3.10), (15.55, 2.55), (21.15, 2.85)]:
        _add_detailed_window(bm_e_wglass, bm_e_wfrm, (x1 - 0.08, wy_c, 2.48), ww_c, 1.48, axis="Y", cols=3)
    for vy_b in (12.15, 15.60):
        _add_detailed_window(bm_e_wglass, bm_e_wfrm, (x1 - 0.08, vy_b, 0.48), 1.48, 0.44, axis="Y", cols=2, has_transom=False)
    _add_plane_uv(bm_e_shut, (x1 - 0.08, 17.35, 0.08), (x1 - 0.08, 19.35, 0.08), (x1 - 0.08, 19.35, 2.65), (x1 - 0.08, 17.35, 2.65))

    # (5d) Stair 9 Special 1F Service Facade
    gp.bm_box(bm_e_cream, (x1 - 0.26, 0.5 * (23.12 + 31.31), 1.80), (0.28, 31.31 - 23.12, 3.56))
    for dy_9 in (23.75, 30.65):
        _add_detailed_window(bm_e_wglass, bm_e_wfrm, (x1 - 0.08, dy_9, 1.06), 0.96, 2.02, axis="Y", cols=1, has_transom=False)
    for fwi in range(3):
        fwy = 24.05 + fwi * 1.22
        gp.bm_box(bm_e_wfrm, (x1 - 0.10, fwy, 2.66), (0.09, 1.18, 1.54))
        gp.bm_box(bm_e_fglass, (x1 - 0.06, fwy, 2.66), (0.05, 1.08, 1.42))
    for lwi in range(3):
        lwy = 28.25 + lwi * 1.10
        gp.bm_box(bm_e_dark, (x1 - 0.12, lwy, 2.68), (0.08, 0.78, 1.48))
        _add_plane_uv(bm_e_lat, (x1 - 0.06, lwy - 0.36, 1.96), (x1 - 0.06, lwy + 0.36, 1.96), (x1 - 0.06, lwy + 0.36, 3.40), (x1 - 0.06, lwy - 0.36, 3.40))
    gp.bm_box(bm_e_trim, (x1 - 0.07, 28.85, 1.58), (0.06, 0.88, 0.42))
    gp.bm_box(bm_e_trim, (x1 + 0.16, 27.20, 0.50), (0.48, 5.55, 0.14))
    for bleg_y in (25.10, 27.20, 29.30):
        gp.bm_box(bm_e_dark, (x1 + 0.10, bleg_y, 0.22), (0.34, 0.22, 0.42))

    # (5e) North End Wide Staircase + Open 1F Breezeway + Painted Sky & Hills Mural
    ns_y0, ns_y1 = 31.90, 39.00
    ns_x0, ns_x1 = x1 - 0.05, x1 + 2.60
    ns_h = 1.02
    n_ns = 6
    for si in range(n_ns):
        sh = ns_h * (si + 1) / n_ns
        sd = (ns_x1 - ns_x0) / n_ns
        sx_c = ns_x1 - (si + 0.5) * sd
        gp.bm_box(bm_e_slab, (sx_c, 0.5 * (ns_y0 + ns_y1), sh * 0.5), (sd + 0.04, ns_y1 - ns_y0 - 0.50, sh))
    xz_ns_cheek = [
        (ns_x0, 0.02), (ns_x1 + 0.10, 0.02), (ns_x1 + 0.10, 0.68),
        (ns_x0 + 0.32, ns_h + 0.86), (ns_x0, ns_h + 0.86),
    ]
    _add_sloped_cheek_x(bm_e_cream, ns_y0, ns_y0 + 0.26, xz_ns_cheek)
    _add_sloped_cheek_x(bm_e_cream, ns_y1 - 0.26, ns_y1, xz_ns_cheek)
    for ry_ns in (ns_y0 + 0.13, ns_y1 - 0.13):
        gp.bm_cyl_p2p(bm_e_steel, (ns_x1 + 0.05, ry_ns, 0.78), (ns_x0 + 0.32, ry_ns, ns_h + 0.96), 0.024, 0.024, segments=8)
    gp.bm_box(bm_e_slab, (cx, 35.45, 0.50), (wx - 0.2, 7.20, 1.00))
    _add_plane_uv(bm_e_mural, (1.80, 39.02, 1.04), (6.15, 39.02, 1.04), (6.15, 39.02, 3.32), (1.80, 39.02, 3.32))

    objs.append(su.create_mesh_object(f"{prefix}_East1FCreamWalls", bm_e_cream, palette["wall_guanghe"], col, uv_scale=0.38))
    objs.append(su.create_mesh_object(f"{prefix}_EastStairsRamps", bm_e_slab, palette["concrete_floor"], col, uv_scale=0.36))
    objs.append(su.create_mesh_object(f"{prefix}_EastTrimBench", bm_e_trim, palette["concrete_trim"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object(f"{prefix}_EastDarkRecess", bm_e_dark, palette["metal_dark"], col))
    objs.append(su.create_mesh_object(f"{prefix}_EastSilverRailsPipes", bm_e_steel, palette["steel_silver"], col, smooth=True))
    objs.append(su.create_mesh_object(f"{prefix}_EastBrickLattice", bm_e_lat, palette["brick_lattice_band"], col, auto_uv=False))
    objs.append(su.create_mesh_object(f"{prefix}_EastGrayShutters", bm_e_shut, palette["wuquan_shutter_gray"], col, auto_uv=False))
    objs.append(su.create_mesh_object(f"{prefix}_EastStair9FrostedGlass", bm_e_fglass, palette["glass_frosted_blue"], col))
    objs.append(su.create_mesh_object(f"{prefix}_East1FWindows", bm_e_wglass, palette["window_glass"], col))
    objs.append(su.create_mesh_object(f"{prefix}_East1FWinFrames", bm_e_wfrm, palette["window_frame"], col))
    objs.append(su.create_mesh_object(f"{prefix}_EastVerticalBanner", bm_e_vban, palette["wuquan_vertical_banner"], col, auto_uv=False))
    objs.append(su.create_mesh_object(f"{prefix}_EastBlueSigns", bm_e_bban, palette["wuquan_blue_banner"], col, auto_uv=False))
    objs.append(su.create_mesh_object(f"{prefix}_EastNorthMural", bm_e_mural, palette["wuquan_north_mural"], col, auto_uv=False))
    return objs


def _add_oculus_wall_x(
    bm_wall: bmesh.types.BMesh,
    bm_rim: bmesh.types.BMesh,
    x_center: float,
    thick_x: float,
    y_center: float,
    width_y: float,
    z_center: float,
    height_z: float,
    radius: float,
    segs: int = 24,
) -> None:
    """建立面向 +-X 之實心厚牆（正中央真正實體鏤空大型圓形窗洞 Oculus ＋ 淺米白圓弧內圈收邊環），零 Boolean 破面。"""
    hy = width_y * 0.5
    hz = height_z * 0.5
    hx = thick_x * 0.5
    x0, x1 = x_center - hx, x_center + hx

    # Merge uniform circle angles with exact 4 rectangle-corner rays so outer perimeter forms a razor-sharp rectangle!
    corner_angs = [
        math.atan2(hz, hy),
        math.pi - math.atan2(hz, hy),
        math.pi + math.atan2(hz, hy),
        2.0 * math.pi - math.atan2(hz, hy),
    ]
    raw_angs = [2.0 * math.pi * i / segs for i in range(segs)] + corner_angs
    raw_angs.sort()
    angs: List[float] = []
    for a in raw_angs:
        if not angs or abs(a - angs[-1]) > 0.025:
            angs.append(a)
    if len(angs) > 1 and (2.0 * math.pi - angs[-1] + angs[0]) < 0.025:
        angs.pop()

    out_pts: List[tuple[float, float]] = []
    in_pts: List[tuple[float, float]] = []
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        sc = min(hy / max(abs(ca), 1e-6), hz / max(abs(sa), 1e-6))
        out_pts.append((y_center + ca * sc, z_center + sa * sc))
        in_pts.append((y_center + ca * radius, z_center + sa * radius))

    n = len(angs)
    vo0 = [bm_wall.verts.new((x0, py, pz)) for py, pz in out_pts]
    vi0 = [bm_wall.verts.new((x0, py, pz)) for py, pz in in_pts]
    vo1 = [bm_wall.verts.new((x1, py, pz)) for py, pz in out_pts]
    vi1 = [bm_wall.verts.new((x1, py, pz)) for py, pz in in_pts]

    new_faces = []
    for i in range(n):
        j = (i + 1) % n
        # West face (x0), East face (x1), outer perimeter & inner hollow circular bore
        new_faces.append(bm_wall.faces.new((vo0[i], vo0[j], vi0[j], vi0[i])))
        new_faces.append(bm_wall.faces.new((vo1[j], vo1[i], vi1[i], vi1[j])))
        new_faces.append(bm_wall.faces.new((vo0[i], vo1[i], vo1[j], vo0[j])))
        new_faces.append(bm_wall.faces.new((vi0[j], vi1[j], vi1[i], vi0[i])))
    bmesh.ops.recalc_face_normals(bm_wall, faces=new_faces)

    # Crisp cream-tile circular inner reveal trim ring slightly proud of wall faces (exact step_2 & step_13 detail!)
    r_in = radius - 0.075
    r_out = radius + 0.035
    rx0, rx1 = x0 - 0.02, x1 + 0.02
    ro0 = [bm_rim.verts.new((rx0, y_center + math.cos(a) * r_out, z_center + math.sin(a) * r_out)) for a in angs]
    ri0 = [bm_rim.verts.new((rx0, y_center + math.cos(a) * r_in, z_center + math.sin(a) * r_in)) for a in angs]
    ro1 = [bm_rim.verts.new((rx1, y_center + math.cos(a) * r_out, z_center + math.sin(a) * r_out)) for a in angs]
    ri1 = [bm_rim.verts.new((rx1, y_center + math.cos(a) * r_in, z_center + math.sin(a) * r_in)) for a in angs]
    rim_faces = []
    for i in range(n):
        j = (i + 1) % n
        rim_faces.append(bm_rim.faces.new((ro0[i], ro0[j], ri0[j], ri0[i])))
        rim_faces.append(bm_rim.faces.new((ro1[j], ro1[i], ri1[i], ri1[j])))
        rim_faces.append(bm_rim.faces.new((ro0[i], ro1[i], ro1[j], ro0[j])))
        rim_faces.append(bm_rim.faces.new((ri0[j], ri1[j], ri1[i], ri0[i])))
    bmesh.ops.recalc_face_normals(bm_rim, faces=rim_faces)


def build_guanghe_connector_bridges(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """v11.9 精準重建廣和樓↔和平樓（北側）與廣和樓↔重慶樓（南側）5F 立體連通走廊與 3F/4F 招牌大型圓洞鏤空立面（1:1 對照 50/52 廣和街街景！）。"""
    col = "Bldg_Guanghe"
    objs: List[bpy.types.Object] = []

    # Shared setback X corridor axis matching satellite ortho & 50/52 Guanghe street views:
    # Recessed ~4.3m east behind Guanghe west hero facade (x=-53.5) -> x = -49.2 (west) .. -43.6 (east), width 5.6m!
    xw, xe = -49.2, -43.6
    xc = 0.5 * (xw + xe)
    bw = xe - xw  # 5.6m
    h1, hu = 3.6, 3.4  # Matches Heping & Chongqing 1F-5F corridor elevations (2F=3.6, 3F=7.0, 4F=10.4, 5F=13.8, roof=17.2)

    def _build_corridor_span_railing(
        bm_parapet: bmesh.types.BMesh,
        bm_rail: bmesh.types.BMesh,
        bm_steel: bmesh.types.BMesh,
        x_face: float,
        y0: float,
        y1: float,
        zf: float,
    ) -> None:
        slen = y1 - y0
        if slen < 0.3:
            return
        yc = 0.5 * (y0 + y1)
        # Cream-tile solid low parapet wall (z = zf+0.34 .. zf+1.06) + crisp twin white/silver horizontal safety rails!
        gp.bm_box(bm_parapet, (x_face, yc, zf + 0.70), (0.24, slen, 0.76))
        gp.bm_box(bm_rail, (x_face, yc, zf + 1.18), (0.06, slen, 0.05))
        gp.bm_box(bm_rail, (x_face, yc, zf + 1.34), (0.06, slen, 0.055))
        # Slim vertical railing posts every ~1.6m
        n_p = max(2, int(round(slen / 1.6)))
        for k in range(1, n_p):
            py = y0 + slen * (k / n_p)
            gp.bm_cyl_axis(bm_steel, (x_face, py, zf + 1.21), 0.02, 0.30, axis="Z", segments=6)

    # =========================================================================
    # 1. NORTH CONNECTOR BRIDGE: Guanghe Bldg (y=+11.5) <-> Heping Bldg (y=+25.5)
    #    Verified in 50 廣和街 step_2_shot_1.png:
    #      - 1F open ground passageway + wide translucent green sloped canopy extending west!
    #      - 2F & 5F full-span open corridors (salmon slab band + cream parapet + white rails)
    #      - 3F & 4F centered salmon brick wall bay (y=16.2..20.8) with TRUE hollow circular Oculus (R=1.08m) + symmetric north/south open bays!
    #      - 5F top clean white slender tie beam framing open sky above
    # =========================================================================
    bm_n_salmon = bmesh.new()
    bm_n_cream = bmesh.new()
    bm_n_floor = bmesh.new()
    bm_n_terrazzo = bmesh.new()
    bm_n_rail = bmesh.new()
    bm_n_steel = bmesh.new()
    bm_n_light = bmesh.new()
    bm_n_glass = bmesh.new()

    ny0, ny1 = 11.2, 25.8  # Embeds 0.3m into both Guanghe & Heping walls (0.000mm gap!)
    nyc = 0.5 * (ny0 + ny1)
    nlen = ny1 - ny0
    oc_n0, oc_n1 = 16.2, 20.8  # Centered 4.6m Oculus pier bay!
    oc_nc = 0.5 * (oc_n0 + oc_n1)

    # 1F ground columns supporting bridge (open ground passage straight to courtyard!)
    for py_c in (11.7, 16.4, 20.6, 25.3):
        gp.bm_box(bm_n_salmon, (xw + 0.28, py_c, h1 * 0.5), (0.56, 0.56, h1))
        gp.bm_box(bm_n_salmon, (xe - 0.28, py_c, h1 * 0.5), (0.56, 0.56, h1))

    # 1F Iconic Translucent Green Glazed Canopy projecting west over north passage (exact 50 廣和街 step_2_shot_1.png!)
    gp.bm_box(bm_n_glass, (xw - 1.32, nyc, 2.98), (2.72, nlen - 1.0, 0.09), rot_y=math.radians(-6.0))
    # Canopy front & rear white/silver metal frame fascia + rafters + 4 slim support posts
    gp.bm_box(bm_n_rail, (xw - 2.66, nyc, 2.83), (0.10, nlen - 0.92, 0.16))
    gp.bm_box(bm_n_rail, (xw - 0.04, nyc, 3.12), (0.10, nlen - 0.92, 0.16))
    for ry_c in (12.0, 14.6, 17.2, 19.8, 22.4, 25.0):
        gp.bm_box(bm_n_steel, (xw - 1.32, ry_c, 2.92), (2.68, 0.08, 0.09), rot_y=math.radians(-6.0))
    for py_p in (12.0, 16.4, 20.6, 25.0):
        gp.bm_cyl_axis(bm_n_steel, (xw - 2.55, py_p, 1.42), 0.055, 2.84, axis="Z", segments=8)

    # 2F - 5F North Connector Floors
    for fl in range(1, 5):
        zf = h1 + (fl - 1) * hu
        # Floor structural slab + walkable terrazzo deck + ceiling linear LED lights
        gp.bm_box(bm_n_floor, (xc, nyc, zf + 0.14), (bw - 0.12, nlen, 0.28))
        gp.bm_box(bm_n_terrazzo, (xc, nyc, zf + 0.295), (bw - 0.50, nlen - 0.1, 0.03))
        for ly_l in (13.8, 18.5, 23.2):
            gp.bm_box(bm_n_light, (xc, ly_l, zf + hu - 0.16), (0.18, 1.8, 0.06))

        # Horizontal salmon-brick floor edge fascia bands on BOTH west & east faces
        gp.bm_box(bm_n_salmon, (xw + 0.20, nyc, zf + 0.18), (0.42, nlen, 0.56))
        gp.bm_box(bm_n_salmon, (xe - 0.20, nyc, zf + 0.18), (0.42, nlen, 0.56))
        # Structural columns along east face (courtyard side stays clean open corridor!)
        for py_c in (11.7, 16.4, 20.6, 25.3):
            gp.bm_box(bm_n_salmon, (xe - 0.26, py_c, zf + hu * 0.5), (0.52, 0.52, hu))
        gp.bm_box(bm_n_salmon, (xe - 0.20, nyc, zf + hu - 0.22), (0.42, nlen, 0.44))
        _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xe - 0.18, ny0 + 0.5, oc_n0 - 0.05, zf)
        _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xe - 0.18, oc_n0 + 0.45, oc_n1 - 0.45, zf)
        _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xe - 0.18, oc_n1 + 0.05, ny1 - 0.5, zf)

        # West (street-facing) elevation differs cleanly by floor (exact 50 廣和街 step_2_shot_1.png!):
        if fl in (2, 3):  # 3F & 4F: Centered Salmon Oculus Wall Pier + Flanking Open Corridor Bays!
            # True hollow circular oculus wall centered at y=18.5, radius=1.06m (diameter 2.12m!)
            _add_oculus_wall_x(
                bm_n_salmon, bm_n_cream,
                x_center=xw + 0.22, thick_x=0.44,
                y_center=oc_nc, width_y=(oc_n1 - oc_n0),
                z_center=zf + hu * 0.52, height_z=hu - 0.12,
                radius=1.06, segs=24,
            )
            # Raised terracotta frame molding strips framing the oculus bay (exact shadow relief!)
            gp.bm_box(bm_n_salmon, (xw - 0.04, oc_n0 + 0.14, zf + hu * 0.52), (0.10, 0.28, hu - 0.10))
            gp.bm_box(bm_n_salmon, (xw - 0.04, oc_n1 - 0.14, zf + hu * 0.52), (0.10, 0.28, hu - 0.10))
            gp.bm_box(bm_n_salmon, (xw - 0.04, oc_nc, zf + 0.36), (0.10, oc_n1 - oc_n0 + 0.04, 0.26))
            gp.bm_box(bm_n_salmon, (xw - 0.04, oc_nc, zf + hu - 0.20), (0.10, oc_n1 - oc_n0 + 0.04, 0.28))
            # Flanking north & south open corridor spans with low salmon fascia + inner cream parapet + top lintel
            gp.bm_box(bm_n_salmon, (xw + 0.26, 11.7, zf + hu * 0.5), (0.52, 0.52, hu))
            gp.bm_box(bm_n_salmon, (xw + 0.26, 25.3, zf + hu * 0.5), (0.52, 0.52, hu))
            gp.bm_box(bm_n_salmon, (xw + 0.20, nyc, zf + hu - 0.24), (0.42, nlen, 0.48))
            _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xw + 0.20, ny0 + 0.55, oc_n0 - 0.05, zf)
            _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xw + 0.20, oc_n1 + 0.05, ny1 - 0.55, zf)
        else:  # 2F (fl=1) & 5F (fl=4): Full-span open corridor without oculus!
            for py_c in (11.7, 16.4, 20.6, 25.3):
                gp.bm_box(bm_n_salmon, (xw + 0.26, py_c, zf + hu * 0.5), (0.48, 0.48, hu))
            _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xw + 0.20, ny0 + 0.52, 16.14, zf)
            _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xw + 0.20, 16.66, 20.34, zf)
            _build_corridor_span_railing(bm_n_cream, bm_n_rail, bm_n_steel, xw + 0.20, 20.86, ny1 - 0.52, zf)
            if fl == 1:
                gp.bm_box(bm_n_salmon, (xw + 0.20, nyc, zf + hu - 0.24), (0.42, nlen, 0.48))
            else:
                # 5F roof slab + clean slender light-cream horizontal top tie beam (exact step_2_shot_1.png!)
                z_ntop = h1 + 4 * hu
                gp.bm_box(bm_n_floor, (xc, nyc, z_ntop + 0.14), (bw - 0.12, nlen, 0.26))
                gp.bm_box(bm_n_cream, (xw + 0.18, nyc, z_ntop + 0.34), (0.36, nlen, 0.56))
                gp.bm_box(bm_n_cream, (xe - 0.18, nyc, z_ntop + 0.34), (0.36, nlen, 0.56))

    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Walls", bm_n_salmon, palette["wall_salmon"], col, uv_scale=0.36))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Cream", bm_n_cream, palette["wall_guanghe"], col, uv_scale=0.38))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Slabs", bm_n_floor, palette["concrete_floor"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Terrazzo", bm_n_terrazzo, palette["terrazzo_corridor"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Rails", bm_n_rail, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Steel", bm_n_steel, palette["steel_silver"], col, smooth=True))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_Lights", bm_n_light, palette["corridor_light"], col))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NorthBridge_CanopyGlass", bm_n_glass, palette["canopy_green_glass"], col))

    # =========================================================================
    # 2. SOUTH CONNECTOR BRIDGE: Guanghe Bldg (y=-10.5) <-> Chongqing Bldg (y=-29.5)
    #    Verified in 52 廣和街 long-lens step_13_shot_1.png:
    #      - 1F open tall passageway with thick salmon brick square piers (NO green canopy!)
    #      - Asymmetric elevation:
    #          * North bay abutting Guanghe (y=-15.6..-10.2): 3F & 4F TRUE hollow circular Oculus (R=1.08m), 2F & 5F open corridor!
    #          * Prominent continuous salmon brick rectangular main pier (y=-16.5..-15.6) running full 1F->roof height!
    #          * South open twin-bay corridor reaching Chongqing Bldg (y=-29.8..-16.5, mid column at y=-23.2): 2F-5F open corridors!
    #      - 5F top crowned with continuous salmon brick roof parapet band (aligned with Chongqing roof, stepped just below Guanghe roof!)
    # =========================================================================
    bm_s_salmon = bmesh.new()
    bm_s_cream = bmesh.new()
    bm_s_floor = bmesh.new()
    bm_s_terrazzo = bmesh.new()
    bm_s_rail = bmesh.new()
    bm_s_steel = bmesh.new()
    bm_s_light = bmesh.new()

    sy0, sy1 = -29.8, -10.2  # Embeds 0.3m into both Chongqing & Guanghe walls (0.000mm gap!)
    syc = 0.5 * (sy0 + sy1)
    slen_tot = sy1 - sy0
    oc_s0, oc_s1 = -15.6, -10.4  # 5.2m oculus bay directly abutting Guanghe south wall!
    oc_sc = 0.5 * (oc_s0 + oc_s1)
    pier_mid_y = -16.05  # Continuous full-height 0.90m salmon rectangular pier!
    south_mid_y = -23.15  # Intermediate open corridor column splitting south half cleanly into 2 bays

    # 1F Open Passageway & Thick Salmon Square Piers + v12.11 27 廣和街 Raised 1.15m Plinth Deck, Column Plinth Collars,
    # 10-Step Forecourt Grand Staircase to Chongqing/South Connector, Sloped White-Tile Cheek Wall + Handrail & Chongqing 1F Library Portico!
    s_plinth_h = 1.15
    for py_c, pw_c in [(-29.2, 0.62), (south_mid_y, 0.58), (pier_mid_y, 0.92), (-10.6, 0.62)]:
        # Lower light-gray concrete column plinth collar (z=1.15..2.18m, exact final_step_30.png!)
        gp.bm_box(bm_s_floor, (xw + 0.30, py_c, s_plinth_h + 0.52), (0.68, pw_c + 0.08, 1.04))
        gp.bm_box(bm_s_floor, (xe - 0.30, py_c, s_plinth_h + 0.52), (0.68, pw_c + 0.08, 1.04))
        # Upper salmon-brick column shaft (z=2.18..3.60m)
        gp.bm_box(bm_s_salmon, (xw + 0.30, py_c, 2.18 + (h1 - 2.18) * 0.5), (0.60, pw_c, h1 - 2.18))
        gp.bm_box(bm_s_salmon, (xe - 0.30, py_c, 2.18 + (h1 - 2.18) * 0.5), (0.60, pw_c, h1 - 2.18))

    # Raised 1F Connector Plinth Deck (x=-51.2..-43.6, y=-29.6..-10.4, z=0..1.15m) + Walkable Terrazzo Top
    gp.bm_box(bm_s_floor, (0.5 * (-51.2 + xe), syc, s_plinth_h * 0.5), (xe - (-51.2), slen_tot - 0.2, s_plinth_h))
    gp.bm_box(bm_s_terrazzo, (0.5 * (-51.1 + xe), syc, s_plinth_h + 0.02), (xe - (-51.1) - 0.1, slen_tot - 0.3, 0.03))

    # 10-Step Grand Staircase Ascending East (+X) from Forecourt Plaza (x=-56.4 -> -51.2, y=-26.8..-15.8, z=0..1.15m, exact final_step_30.png!)
    st_x0, st_x1 = -56.40, -51.20
    st_y0, st_y1 = -26.80, -15.80
    st_yc = 0.5 * (st_y0 + st_y1)
    st_wy = st_y1 - st_y0
    n_st_s = 10
    for si in range(n_st_s):
        sh = s_plinth_h * (si + 1) / n_st_s
        sd = (st_x1 - st_x0) / n_st_s
        sx_c = st_x0 + (si + 0.5) * sd
        gp.bm_box(bm_s_floor, (sx_c, st_yc, sh * 0.5), (sd + 0.04, st_wy, sh))

    # Sloped White Square-Tile Cheek Wall along North Edge of Stairs (y=-15.80..-15.42) + Concrete Sloped Coping + Stainless Double Handrail!
    chk_y0, chk_y1 = st_y1, st_y1 + 0.38
    chk_yc = 0.5 * (chk_y0 + chk_y1)
    chk_xz = [
        (st_x0 - 0.15, 0.02),
        (st_x1 + 0.20, 0.02),
        (st_x1 + 0.20, s_plinth_h + 0.68),
        (st_x0 - 0.15, 0.68),
    ]
    vs_c0 = [bm_s_cream.verts.new((px_v, chk_y0, pz_v)) for px_v, pz_v in chk_xz]
    vs_c1 = [bm_s_cream.verts.new((px_v, chk_y1, pz_v)) for px_v, pz_v in chk_xz]
    f_chk = [bm_s_cream.faces.new(vs_c0), bm_s_cream.faces.new(list(reversed(vs_c1)))]
    for ii in range(4):
        jj = (ii + 1) % 4
        f_chk.append(bm_s_cream.faces.new((vs_c0[ii], vs_c1[ii], vs_c1[jj], vs_c0[jj])))
    bmesh.ops.recalc_face_normals(bm_s_cream, faces=f_chk)
    # Sloped gray concrete coping cap & stainless handrail above cheek wall
    sl_dx = (st_x1 + 0.20) - (st_x0 - 0.15)
    sl_dz = s_plinth_h
    sl_len = math.hypot(sl_dx, sl_dz)
    sl_ang = math.atan2(sl_dz, sl_dx)
    gp.bm_box(
        bm_s_floor,
        (0.5 * (st_x0 - 0.15 + st_x1 + 0.20), chk_yc, 0.68 + s_plinth_h * 0.5 + 0.04),
        (sl_len + 0.08, 0.46, 0.08),
        rot_y=-sl_ang,
    )
    gp.bm_cyl_p2p(bm_s_steel, (st_x0 - 0.08, chk_yc, 1.06), (st_x1 + 0.15, chk_yc, s_plinth_h + 1.06), 0.028, 0.028, segments=8)
    gp.bm_cyl_p2p(bm_s_steel, (st_x0 - 0.08, chk_yc, 0.88), (st_x1 + 0.15, chk_yc, s_plinth_h + 0.88), 0.020, 0.020, segments=6)
    for k_p in range(5):
        tk_p = k_p / 4.0
        px_p = (st_x0 - 0.08) + ((st_x1 + 0.15) - (st_x0 - 0.08)) * tk_p
        pz_p = 0.72 + s_plinth_h * tk_p
        gp.bm_cyl_p2p(bm_s_steel, (px_p, chk_yc, pz_p), (px_p, chk_yc, pz_p + 0.35), 0.020, 0.020, segments=6)

    # Forecourt South Garden White-Tile Low Planter Wall & Decorative Round Ceramic Planter Pot strictly NORTH of stair cheek wall (y=-15.42..-7.45, step_18_shot_1.png!)
    gp.bm_box(bm_s_cream, (-58.6, -15.25, 0.34), (4.6, 0.36, 0.64))
    gp.bm_box(bm_s_floor, (-58.6, -15.25, 0.68), (4.72, 0.44, 0.07))
    gp.bm_box(bm_s_cream, (-60.8, -11.35, 0.38), (0.38, 7.8, 0.72))
    gp.bm_box(bm_s_floor, (-60.8, -11.35, 0.76), (0.46, 7.9, 0.07))
    # Sloped white-tile side cheek wall + silver handrail beside Guanghe south wing (visible behind '31' gate pier in step_18_shot_1.png!)
    gp.bm_box(bm_s_cream, (-59.2, -7.45, 0.68), (4.2, 0.32, 0.82), rot_y=math.radians(-14.0))
    gp.bm_cyl_p2p(bm_s_steel, (-61.2, -7.45, 0.96), (-57.1, -7.45, 1.98), 0.026, 0.026, segments=8)
    # Large cream round planter pot seated on SW corner of garden retaining wall
    gp.bm_cyl_p2p(bm_s_cream, (-60.4, -15.05, 0.68), (-60.4, -15.05, 1.16), 0.34, 0.46, segments=14)
    gp.bm_cyl_axis(bm_s_floor, (-60.4, -15.05, 1.18), 0.48, 0.06, axis="Z", segments=14)

    # Chongqing Bldg North 1F White Square-Tile Twin-Column Portico + Illustrated "圖書室 Library" Header Sign (right of grand stairs in final_step_30.png!)
    lib_x0, lib_x1 = -58.6, -51.4
    lib_xc = 0.5 * (lib_x0 + lib_x1)
    lib_y = -27.55
    for lx_p in (lib_x0 + 0.32, lib_x0 + 2.55, lib_x1 - 0.32):
        gp.bm_box(bm_s_cream, (lx_p, lib_y, 2.05), (0.58, 0.58, 4.10))
    gp.bm_box(bm_s_cream, (lib_xc, lib_y, 3.65), (lib_x1 - lib_x0 + 0.12, 0.62, 0.96))
    gp.bm_box(bm_s_floor, (lib_xc, -28.5, s_plinth_h * 0.5), (lib_x1 - lib_x0 + 0.8, 2.2, s_plinth_h))
    bm_lib_ban = bmesh.new()
    # Facing WEST-NORTHWEST toward main gate (-X / +Y): viewer left is +Y/-X, right is -X
    _add_plane_uv(
        bm_lib_ban,
        (lib_x1 - 0.05, lib_y + 0.33, 3.18),
        (lib_x0 + 0.05, lib_y + 0.33, 3.18),
        (lib_x0 + 0.05, lib_y + 0.33, 4.12),
        (lib_x1 - 0.05, lib_y + 0.33, 4.12),
    )
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_LibraryBanner", bm_lib_ban, palette["library_banner"], "Bldg_Chongqing", auto_uv=False))

    # 2F - 5F South Connector Floors
    for fl in range(1, 5):
        zf = h1 + (fl - 1) * hu
        gp.bm_box(bm_s_floor, (xc, syc, zf + 0.14), (bw - 0.12, slen_tot, 0.28))
        gp.bm_box(bm_s_terrazzo, (xc, syc, zf + 0.295), (bw - 0.50, slen_tot - 0.1, 0.03))
        for ly_l in (-26.5, -19.8, -13.0):
            gp.bm_box(bm_s_light, (xc, ly_l, zf + hu - 0.16), (0.18, 2.0, 0.06))

        # Horizontal salmon-brick floor fascia bands on BOTH west & east faces
        gp.bm_box(bm_s_salmon, (xw + 0.22, syc, zf + 0.18), (0.44, slen_tot, 0.56))
        gp.bm_box(bm_s_salmon, (xe - 0.22, syc, zf + 0.18), (0.44, slen_tot, 0.56))

        # East (courtyard-facing) open corridor colonnade & railings
        for py_c, pw_c in [(-29.2, 0.56), (south_mid_y, 0.54), (pier_mid_y, 0.86), (-10.6, 0.56)]:
            gp.bm_box(bm_s_salmon, (xe - 0.28, py_c, zf + hu * 0.5), (0.56, pw_c, hu))
        gp.bm_box(bm_s_salmon, (xe - 0.22, syc, zf + hu - 0.22), (0.44, slen_tot, 0.44))
        _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xe - 0.18, -28.9, south_mid_y - 0.30, zf)
        _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xe - 0.18, south_mid_y + 0.30, pier_mid_y - 0.45, zf)
        _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xe - 0.18, pier_mid_y + 0.45, -10.9, zf)

        # West (street-facing) elevation (exact 52 廣和街 step_13_shot_1.png!):
        # Continuous full-height rectangular salmon pier at y=-16.05 + south intermediate & end columns
        gp.bm_box(bm_s_salmon, (xw + 0.28, pier_mid_y, zf + hu * 0.5), (0.56, 0.90, hu))
        gp.bm_box(bm_s_salmon, (xw + 0.28, south_mid_y, zf + hu * 0.5), (0.54, 0.54, hu))
        gp.bm_box(bm_s_salmon, (xw + 0.28, -29.2, zf + hu * 0.5), (0.54, 0.56, hu))
        gp.bm_box(bm_s_salmon, (xw + 0.22, syc, zf + hu - 0.24), (0.44, slen_tot, 0.48))

        # South twin open corridor bays (y=-28.9..-23.45 & y=-22.85..-16.52) open on ALL 2F-5F floors!
        _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xw + 0.20, -28.90, south_mid_y - 0.28, zf)
        _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xw + 0.20, south_mid_y + 0.28, pier_mid_y - 0.46, zf)

        # North bay abutting Guanghe (y=-15.6..-10.4): 3F & 4F TRUE Oculus Wall, 2F & 5F Open Corridor!
        if fl in (2, 3):  # 3F & 4F Oculus!
            _add_oculus_wall_x(
                bm_s_salmon, bm_s_cream,
                x_center=xw + 0.22, thick_x=0.44,
                y_center=oc_sc, width_y=(oc_s1 - oc_s0),
                z_center=zf + hu * 0.52, height_z=hu - 0.12,
                radius=1.08, segs=24,
            )
            # Crisp raised terracotta border frames around oculus bay
            gp.bm_box(bm_s_salmon, (xw - 0.04, oc_s0 + 0.16, zf + hu * 0.52), (0.10, 0.30, hu - 0.10))
            gp.bm_box(bm_s_salmon, (xw - 0.04, oc_s1 - 0.16, zf + hu * 0.52), (0.10, 0.30, hu - 0.10))
            gp.bm_box(bm_s_salmon, (xw - 0.04, oc_sc, zf + 0.36), (0.10, oc_s1 - oc_s0 + 0.04, 0.28))
            gp.bm_box(bm_s_salmon, (xw - 0.04, oc_sc, zf + hu - 0.20), (0.10, oc_s1 - oc_s0 + 0.04, 0.28))
        else:  # 2F & 5F Open Corridor abutting Guanghe!
            gp.bm_box(bm_s_salmon, (xw + 0.28, -10.6, zf + hu * 0.5), (0.54, 0.54, hu))
            _build_corridor_span_railing(bm_s_cream, bm_s_rail, bm_s_steel, xw + 0.20, pier_mid_y + 0.46, -10.90, zf)

    # 5F Top Roof Slab + Continuous Salmon-Brick Roof Parapet Band (aligned w/ Chongqing roof, stepped neatly below Guanghe!)
    z_stop = h1 + 4 * hu  # 17.2m
    gp.bm_box(bm_s_floor, (xc, syc, z_stop + 0.14), (bw - 0.10, slen_tot, 0.28))
    gp.bm_box(bm_s_cream, (xw + 0.18, syc, z_stop + 0.06), (0.40, slen_tot, 0.16))  # Light underside drip edge
    gp.bm_box(bm_s_salmon, (xw + 0.20, syc, z_stop + 0.64), (0.42, slen_tot, 1.02))
    gp.bm_box(bm_s_salmon, (xe - 0.20, syc, z_stop + 0.64), (0.42, slen_tot, 1.02))

    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Walls", bm_s_salmon, palette["wall_salmon"], col, uv_scale=0.36))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Cream", bm_s_cream, palette["wall_guanghe"], col, uv_scale=0.38))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Slabs", bm_s_floor, palette["concrete_floor"], col, uv_scale=0.35))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Terrazzo", bm_s_terrazzo, palette["terrazzo_corridor"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Rails", bm_s_rail, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Steel", bm_s_steel, palette["steel_silver"], col, smooth=True))
    objs.append(su.create_mesh_object("Bldg_Guanghe_SouthBridge_Lights", bm_s_light, palette["corridor_light"], col))

    return objs
