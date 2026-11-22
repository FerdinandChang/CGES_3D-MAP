"""重慶國小高細節地標模組（v3）：精雕紅磚半圓拱警衛室、廣和街南側花磚馬賽克圍牆、外露廊柱運動中心、海豚彩繪鋼構天橋與分層半圓弧形轉角陽台塔樓。"""
import math
from typing import Dict, List

import bmesh
import bpy

import coords as mg
import geom_primitives as gp
import studio_utils as su

_add_plane_uv = gp.add_plane_uv


def build_main_gate_and_walls(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """還原廣和街 31 號主校門警衛室、金色校名牌、以及廣和街南側花磚馬賽克特色圍牆（對照 final_step_105.png）。"""
    col = "Landmark_MainGate"
    gcfg = spec["grounds"]["main_gate"]
    gx = gcfg["x"]
    gy = gcfg["y_center"]
    gw = gcfg["gate_width"]

    objs: List[bpy.types.Object] = []
    bm_brick = bmesh.new()
    bm_gh = bmesh.new()
    bm_stone = bmesh.new()
    bm_orange = bmesh.new()
    bm_trim = bmesh.new()
    bm_metal = bmesh.new()
    bm_frame = bmesh.new()
    bm_glass = bmesh.new()
    bm_south_wall = bmesh.new()
    bm_south_mesh = bmesh.new()

    # === v11.6 52 廣和街 EXACT MAIN GATE GUARDHOUSE + ROOF BARREL ARCH + HOLLOW TERRACOTTA TOWER + SIGN WALL! ===
    # Unified coordinate frame rotated by ang_g = mg.GUANGHE_ROT_Z (-8.5°) so guardhouse, tower, gate & wall are 100% parallel to Guanghe St!
    ang_g = mg.GUANGHE_ROT_Z
    ca_g, sa_g = math.cos(ang_g), math.sin(ang_g)
    # Anchor at south edge of guardhouse/tower complex (y = 5.45, right where main sliding gate meets terracotta tower!)
    y_anc = 5.45
    x_anc = mg.wall_x(y_anc)

    def g_loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (x_anc + lx * ca_g - ly * sa_g, y_anc + lx * sa_g + ly * ca_g, lz)

    bm_arch_bush = bmesh.new()
    bm_lat_gh = bmesh.new()
    bm_addr = bmesh.new()
    bm_cam_w = bmesh.new()
    bm_cam_r = bmesh.new()

    # 1. NORTH ENTRY LINK WALL (ly = +4.6 .. +6.75 -> seamlessly joins bronze grille fence at y=12.0!, H=3.65m, cream tile + diamond brick vent + planter!)
    gp.bm_box(bm_gh, g_loc(0.32, 5.65, 1.82), (0.64, 2.25, 3.64), rot_z=ang_g)
    gp.bm_box(bm_trim, g_loc(0.32, 5.65, 3.68), (0.74, 2.32, 0.12), rot_z=ang_g)
    # Recessed terracotta diamond lattice vent window inside north cream wall (exact step_6_shot_1!)
    _add_plane_uv(bm_lat_gh, g_loc(-0.02, 5.55, 1.35), g_loc(-0.02, 4.70, 1.35), g_loc(-0.02, 4.70, 2.55), g_loc(-0.02, 5.55, 2.55))
    # Address plaque "廣和街 31 號" on north cream wall pillar + low cream planter box w/ dark-green shrubs!
    _add_plane_uv(bm_addr, g_loc(-0.02, 6.45, 2.15), g_loc(-0.02, 5.88, 2.15), g_loc(-0.02, 5.88, 2.50), g_loc(-0.02, 6.45, 2.50))
    gp.bm_box(bm_gh, g_loc(-0.55, 5.35, 0.28), (0.95, 2.15, 0.56), rot_z=ang_g)
    for ky_b in (4.75, 5.35, 5.95):
        ret_gb = bmesh.ops.create_icosphere(bm_arch_bush, subdivisions=2, radius=1.0)
        cx_b, cy_b, cz_b = g_loc(-0.55, ky_b, 0.72)
        for v in ret_gb["verts"]:
            v.co.x = cx_b + v.co.x * 0.44
            v.co.y = cy_b + v.co.y * 0.46
            v.co.z = cz_b + v.co.z * 0.30

    # 2. 1F GUARDHOUSE CABIN + THICK PROJECTING CREAM-TILE FLAT ROOF EAVE (ly = +1.45 .. +4.65, lx = 0.0 .. +3.25, H=3.40m!)
    # Lower solid cream square-tile sill walls (z=0..1.05m) + back/north solid walls
    gp.bm_box(bm_gh, g_loc(1.62, 3.05, 0.52), (3.25, 3.20, 1.04), rot_z=ang_g)
    gp.bm_box(bm_gh, g_loc(2.98, 3.05, 1.80), (0.52, 3.20, 1.56), rot_z=ang_g)
    gp.bm_box(bm_gh, g_loc(1.62, 4.42, 1.80), (3.25, 0.46, 1.56), rot_z=ang_g)
    # Corner narrow column + Expansive L-shaped Aluminum-Framed Glass Windows wrapping West (road) & South (pedestrian gate) faces!
    gp.bm_box(bm_gh, g_loc(0.18, 4.25, 1.80), (0.36, 0.65, 1.56), rot_z=ang_g)
    gp.bm_box(bm_glass, g_loc(0.06, 2.72, 1.80), (0.08, 2.45, 1.48), rot_z=ang_g)
    gp.bm_box(bm_glass, g_loc(1.38, 1.50, 1.80), (2.60, 0.08, 1.48), rot_z=ang_g)
    # Crisp aluminum window mullions & corner post
    gp.bm_box(bm_frame, g_loc(0.04, 1.48, 1.80), (0.12, 0.12, 1.54), rot_z=ang_g)
    for my_w in (2.10, 2.75, 3.40, 3.92):
        gp.bm_box(bm_frame, g_loc(0.03, my_w, 1.80), (0.10, 0.055, 1.52), rot_z=ang_g)
    for mx_w in (0.70, 1.40, 2.10, 2.66):
        gp.bm_box(bm_frame, g_loc(mx_w, 1.47, 1.80), (0.055, 0.10, 1.52), rot_z=ang_g)
    gp.bm_box(bm_frame, g_loc(0.03, 2.72, 1.06), (0.14, 2.55, 0.06), rot_z=ang_g)
    gp.bm_box(bm_frame, g_loc(1.38, 1.47, 1.06), (2.70, 0.14, 0.06), rot_z=ang_g)
    # Signature THICK overhanging cream-tile flat roof slab/eave (z=2.56..3.42m, projecting proudly toward road & gate! step_6_shot_1!)
    gp.bm_box(bm_gh, g_loc(1.52, 2.95, 2.99), (3.95, 3.72, 0.86), rot_z=ang_g)
    gp.bm_box(bm_trim, g_loc(1.52, 2.95, 3.44), (4.05, 3.82, 0.08), rot_z=ang_g)

    # 3. SIGNATURE INTERLOCKING ROOF BARREL VAULT ARCH (E-W axis running lx=-0.45..+4.25 across roof & THROUGH terracotta tower! step_10_shot_1!)
    arch_ly = 2.35
    arch_lx0, arch_lx1 = -0.42, 4.18
    arch_lcx = 0.5 * (arch_lx0 + arch_lx1)
    arch_llen = arch_lx1 - arch_lx0
    arch_z0 = 3.44
    arch_r_out = 1.48
    arch_thick = 0.28
    # Projecting rectangular cream-tile arch springer ledge extending across roof & into terracotta tower!
    gp.bm_box(bm_gh, g_loc(arch_lcx, arch_ly, arch_z0 + 0.24), (arch_llen + 0.18, arch_r_out * 2.16, 0.48), rot_z=ang_g)
    # 20-segment smooth cream-tile barrel vault shell (axis along local X -> cross-section in local Y-Z!)
    segs_a = 20
    for i in range(segs_a):
        a0 = math.pi * i / segs_a
        a1 = math.pi * (i + 1) / segs_a
        am = 0.5 * (a0 + a1)
        seg_arc = (arch_r_out - arch_thick * 0.5) * (a1 - a0) + 0.05
        cy_a = arch_ly + math.cos(am) * (arch_r_out - arch_thick * 0.5)
        cz_a = arch_z0 + 0.42 + math.sin(am) * (arch_r_out - arch_thick * 0.5)
        # Rotate segment around local X (matching barrel slope) then local Z (ang_g)!
        gp.bm_box(bm_gh, g_loc(arch_lcx, cy_a, cz_a), (arch_llen, seg_arc, arch_thick), rot_x=am - math.pi * 0.5, rot_z=ang_g)
        # Subtle protruding west arch trim ring facing Guanghe St
        cy_t = arch_ly + math.cos(am) * (arch_r_out + 0.02)
        cz_t = arch_z0 + 0.42 + math.sin(am) * (arch_r_out + 0.02)
        gp.bm_box(bm_trim, g_loc(arch_lx0 - 0.04, cy_t, cz_t), (0.10, seg_arc + 0.02, 0.12), rot_x=am - math.pi * 0.5, rot_z=ang_g)
    # Recessed terracotta-orange semicircular tympanum end walls (facing West -X & East +X!)
    for tx_end in (arch_lx0 + 0.24, arch_lx1 - 0.24):
        pts_semi = [g_loc(tx_end, arch_ly + math.cos(math.pi * k / 16.0) * (arch_r_out - 0.22), arch_z0 + 0.42 + math.sin(math.pi * k / 16.0) * (arch_r_out - 0.22)) for k in range(17)]
        for k in range(16):
            # Extrude thin solid triangular fan wedges along X
            p_c = g_loc(tx_end, arch_ly, arch_z0 + 0.42)
            p_a, p_b = pts_semi[k], pts_semi[k + 1]
            # Thickness along X (+/- 0.08)
            off_v = (0.08 * ca_g, 0.08 * sa_g, 0.0)
            va0 = bm_orange.verts.new((p_c[0] - off_v[0], p_c[1] - off_v[1], p_c[2]))
            va1 = bm_orange.verts.new((p_a[0] - off_v[0], p_a[1] - off_v[1], p_a[2]))
            va2 = bm_orange.verts.new((p_b[0] - off_v[0], p_b[1] - off_v[1], p_b[2]))
            vb0 = bm_orange.verts.new((p_c[0] + off_v[0], p_c[1] + off_v[1], p_c[2]))
            vb1 = bm_orange.verts.new((p_a[0] + off_v[0], p_a[1] + off_v[1], p_a[2]))
            vb2 = bm_orange.verts.new((p_b[0] + off_v[0], p_b[1] + off_v[1], p_b[2]))
            bm_orange.faces.new((va0, va2, va1))
            bm_orange.faces.new((vb0, vb1, vb2))

    # 4. TALL HOLLOW TERRACOTTA-BRICK OPEN-FRAME GATE TOWER (4 columns + 4 open top sky-frame beams, H=6.30m! exact step_6 & step_10!)
    tw_x0, tw_x1 = 0.55, 3.65   # East-West depth 3.10m
    tw_y0, tw_y1 = 0.00, 3.35   # North-South width 3.35m (south piers at ly=0.0 right beside main gate!)
    tw_cx, tw_cy = 0.5 * (tw_x0 + tw_x1), 0.5 * (tw_y0 + tw_y1)
    tw_h = 6.30
    # 4 sturdy terracotta-brick square columns (0.64 x 0.64m)
    gp.bm_box(bm_brick, g_loc(tw_x0, tw_y0, tw_h * 0.5), (0.64, 0.64, tw_h), rot_z=ang_g)  # Hero front-south main gate pier!
    gp.bm_box(bm_brick, g_loc(tw_x1, tw_y0, tw_h * 0.5), (0.64, 0.64, tw_h), rot_z=ang_g)  # Rear-south pier
    gp.bm_box(bm_brick, g_loc(tw_x0, tw_y1, (3.30 + tw_h) * 0.5), (0.64, 0.64, tw_h - 3.30), rot_z=ang_g)  # Front-north pier rising from roof!
    gp.bm_box(bm_brick, g_loc(tw_x1, tw_y1, tw_h * 0.5), (0.64, 0.64, tw_h), rot_z=ang_g)  # Rear-north pier
    # 4 open-sky top frame horizontal terracotta beams (z=5.62..6.30m, framing the open sky square!)
    gp.bm_box(bm_brick, g_loc(tw_x0, tw_cy, tw_h - 0.34), (0.66, (tw_y1 - tw_y0) + 0.64, 0.68), rot_z=ang_g)
    gp.bm_box(bm_brick, g_loc(tw_x1, tw_cy, tw_h - 0.34), (0.66, (tw_y1 - tw_y0) + 0.64, 0.68), rot_z=ang_g)
    gp.bm_box(bm_brick, g_loc(tw_cx, tw_y0, tw_h - 0.34), ((tw_x1 - tw_x0) + 0.64, 0.66, 0.68), rot_z=ang_g)
    gp.bm_box(bm_brick, g_loc(tw_cx, tw_y1, tw_h - 0.34), ((tw_x1 - tw_x0) + 0.64, 0.66, 0.68), rot_z=ang_g)
    # Mid-level terracotta horizontal crossbeam spanning pedestrian gate (z=2.68..3.34m) & connecting front/rear south piers!
    gp.bm_box(bm_brick, g_loc(tw_cx, tw_y0, 3.00), ((tw_x1 - tw_x0) + 0.50, 0.58, 0.64), rot_z=ang_g)
    gp.bm_box(bm_brick, g_loc(tw_x0, 0.85, 3.00), (0.58, 1.55, 0.64), rot_z=ang_g)
    # Second small green "31" address plaque + vertical school wood plaque on front-south terracotta pier + white intercom box!
    _add_plane_uv(bm_addr, g_loc(tw_x0 - 0.34, tw_y0 + 0.16, 1.72), g_loc(tw_x0 - 0.34, tw_y0 - 0.16, 1.72), g_loc(tw_x0 - 0.34, tw_y0 - 0.16, 1.94), g_loc(tw_x0 - 0.34, tw_y0 + 0.16, 1.94))
    gp.bm_box(bm_cam_w, g_loc(tw_x0 + 0.05, tw_y0 - 0.35, 1.38), (0.20, 0.08, 0.32), rot_z=ang_g)

    # 5. PEDESTRIAN SIDE IRON GATE (ly=+0.34..+1.44 between terracotta tower & guardhouse) + MAIN SLIDING IRON GATE (y=-3.25..+5.12!)
    # Pedestrian small dark iron gate + white printed notice sheet
    gp.bm_box(bm_metal, g_loc(0.55, 0.89, 1.72), (0.08, 1.12, 0.08), rot_z=ang_g)
    gp.bm_box(bm_metal, g_loc(0.55, 0.89, 0.28), (0.08, 1.12, 0.08), rot_z=ang_g)
    for k in range(7):
        gp.bm_box(bm_metal, g_loc(0.55, 0.38 + k * 0.17, 1.00), (0.045, 0.045, 1.50), rot_z=ang_g)
    gp.bm_box(bm_cam_w, g_loc(0.50, 0.89, 1.35), (0.02, 0.30, 0.38), rot_z=ang_g)

    # Main horizontal-sliding dark iron gate aligned cleanly along Guanghe St (y = -3.25 .. +5.10!)
    gate_y0 = gy - gw * 0.5
    gate_y1 = y_anc - 0.35
    g_mid_y = 0.5 * (gate_y0 + gate_y1)
    g_mid_x = mg.wall_x(g_mid_y) + 0.55
    g_span = gate_y1 - gate_y0
    gp.bm_box(bm_metal, (g_mid_x, g_mid_y, 1.70), (0.14, g_span, 0.10), rot_z=ang_g)
    gp.bm_box(bm_metal, (g_mid_x, g_mid_y, 0.98), (0.10, g_span, 0.07), rot_z=ang_g)
    gp.bm_box(bm_metal, (g_mid_x, g_mid_y, 0.28), (0.14, g_span, 0.10), rot_z=ang_g)
    n_bars = 26
    for i in range(n_bars + 1):
        by_b = gate_y0 + g_span * i / n_bars
        gp.bm_box(bm_metal, (mg.wall_x(by_b) + 0.55, by_b, 0.99), (0.055, 0.055, 1.52), rot_z=ang_g)
    # Enrollment banner mounted neatly along angled main sliding gate (facing -X -> UV left=+Y, right=-Y!)
    bm_gbanner = bmesh.new()
    _add_plane_uv(
        bm_gbanner,
        (mg.wall_x(gate_y1 - 0.35) + 0.42, gate_y1 - 0.35, 0.46),
        (mg.wall_x(gate_y0 + 0.65) + 0.42, gate_y0 + 0.65, 0.46),
        (mg.wall_x(gate_y0 + 0.65) + 0.42, gate_y0 + 0.65, 1.48),
        (mg.wall_x(gate_y1 - 0.35) + 0.42, gate_y1 - 0.35, 1.48),
    )
    objs.append(su.create_mesh_object("Landmark_MainGate_EnrollmentBanner", bm_gbanner, palette["gate_banner"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_MainGate_Address31", bm_addr, palette["house_num_31"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_MainGate_NorthLattice", bm_lat_gh, palette["brick_lattice_band"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_MainGate_NorthShrubs", bm_arch_bush, palette["tree_foliage_a"], col, smooth=True))

    # 6. Right cream-tile framed School Name Sign Wall (proportional low height 2.28m + CCTV camera & red warning light on north end! final_step_20!)
    sw_y0 = gate_y0 - 11.5
    sw_y1 = gate_y0 - 0.25
    sw_cy = (sw_y0 + sw_y1) * 0.5
    sw_cx = mg.wall_x(sw_cy)
    sw_len = sw_y1 - sw_y0
    gp.bm_box(bm_gh, (sw_cx + 0.25, sw_cy, 1.14), (0.68, sw_len, 2.28), rot_z=ang_g)
    gp.bm_box(bm_trim, (sw_cx + 0.25, sw_cy, 2.32), (0.76, sw_len + 0.14, 0.10), rot_z=ang_g)
    gp.bm_box(bm_gh, (sw_cx - 0.56, sw_cy, 0.30), (1.02, sw_len + 0.15, 0.60), rot_z=ang_g)
    # White bullet CCTV camera + small red beacon light on north corner top of school sign wall (exact final_step_20 detail!)
    gp.bm_cyl_axis(bm_cam_r, (mg.wall_x(sw_y1 - 0.35) + 0.18, sw_y1 - 0.35, 2.48), 0.075, 0.20, axis="Z", segments=10)
    gp.bm_cyl_axis(bm_cam_w, (mg.wall_x(sw_y1 - 0.85) + 0.22, sw_y1 - 0.85, 2.55), 0.03, 0.34, axis="Z", segments=8)
    gp.bm_box(bm_cam_w, (mg.wall_x(sw_y1 - 0.85) + 0.05, sw_y1 - 0.72, 2.74), (0.36, 0.14, 0.14), rot_z=math.radians(38.0))
    objs.append(su.create_mesh_object("Landmark_MainGate_CCTVWhite", bm_cam_w, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_WarningBeacon", bm_cam_r, palette["signal_red"], col))

    bm_sign = bmesh.new()
    _add_plane_uv(
        bm_sign,
        (mg.wall_x(sw_y1 - 0.45) - 0.12, sw_y1 - 0.45, 0.64),
        (mg.wall_x(sw_y0 + 0.45) - 0.12, sw_y0 + 0.45, 0.64),
        (mg.wall_x(sw_y0 + 0.45) - 0.12, sw_y0 + 0.45, 2.02),
        (mg.wall_x(sw_y1 - 0.45) - 0.12, sw_y1 - 0.45, 2.02),
    )
    objs.append(su.create_mesh_object("Landmark_MainGate_SchoolSign", bm_sign, palette["school_sign"], col, auto_uv=False))

    # 4. Perimeter walls — v8 Exact Unified wall_x(y) Alignment (ZERO gap / ZERO overlap with sidewalks!)
    bm_bronze = bmesh.new()

    def _add_open_grille_fence(p0: tuple[float, float], p1: tuple[float, float], base_h: float = 0.58, rail_h: float = 1.65) -> None:
        """低矮白磁磚花台基座 ＋ 深棕色弧頂金屬垂直格柵透空圍欄（還原 10 / 27 / 50 廣和街！）。"""
        x0, y0 = p0
        x1, y1 = p1
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        gp.bm_box(bm_gh, (mx, my, base_h * 0.5), (length, 0.44, base_h), rot_z=ang)
        gp.bm_box(bm_bronze, (mx, my, base_h + rail_h - 0.12), (length, 0.055, 0.055), rot_z=ang)
        gp.bm_box(bm_bronze, (mx, my, base_h + 0.14), (length, 0.055, 0.055), rot_z=ang)
        bay_w = 2.4
        n_bays = max(2, int(round(length / bay_w)))
        for b in range(n_bays):
            t0, t1 = b / n_bays, (b + 1) / n_bays
            tm = 0.5 * (t0 + t1)
            bx0, by0 = x0 + dx * t0, y0 + dy * t0
            bx1, by1 = x0 + dx * t1, y0 + dy * t1
            bm_x, bm_y = x0 + dx * tm, y0 + dy * tm
            gp.bm_box(bm_gh, (bx0, by0, base_h + rail_h * 0.5), (0.20, 0.20, rail_h), rot_z=ang)
            if b == n_bays - 1:
                gp.bm_box(bm_gh, (bx1, by1, base_h + rail_h * 0.5), (0.20, 0.20, rail_h), rot_z=ang)
            q0 = (bx0, by0, base_h + rail_h - 0.10)
            qm = (bm_x, bm_y, base_h + rail_h + 0.18)
            q1 = (bx1, by1, base_h + rail_h - 0.10)
            gp.bm_cyl_p2p(bm_bronze, q0, qm, 0.028, 0.028, segments=6)
            gp.bm_cyl_p2p(bm_bronze, qm, q1, 0.028, 0.028, segments=6)
            for k in range(1, 6):
                tk = t0 + (t1 - t0) * k / 6.0
                px, py = x0 + dx * tk, y0 + dy * tk
                arch_lift = 0.26 * (1.0 - ((k - 3) / 3.0) ** 2)
                ph = rail_h + arch_lift
                gp.bm_box(bm_bronze, (px, py, base_h + ph * 0.5), (0.032, 0.032, ph), rot_z=ang)

    # (a) North Front Segment (Guardhouse north y=12.0 -> NW corner plaza junction y=35.6) + red enrollment banner!
    _add_open_grille_fence((mg.wall_x(12.0), 12.0), (mg.wall_x(35.6), 35.6), base_h=0.56, rail_h=1.55)
    bm_fban = bmesh.new()
    _add_plane_uv(
        bm_fban,
        (mg.wall_x(25.2) - 0.26, 25.2, 0.95),
        (mg.wall_x(21.4) - 0.26, 21.4, 0.95),
        (mg.wall_x(21.4) - 0.26, 21.4, 1.95),
        (mg.wall_x(25.2) - 0.26, 25.2, 1.95),
    )
    objs.append(su.create_mesh_object("Landmark_NorthFence_RedBanner", bm_fban, palette["fence_red_banner"], col, auto_uv=False))

    # Low white-tile curved/angled planter rim cleanly bordering 10 廣和街 NW diagonal-brick plaza (exact step_111!)
    nw_rim_pts = [
        (mg.wall_x(35.6), 35.6),
        (-65.2, 39.65),
        (-60.5, 40.35),
        (-55.0, 41.05),
    ]
    for i in range(len(nw_rim_pts) - 1):
        rx0, ry0 = nw_rim_pts[i]
        rx1, ry1 = nw_rim_pts[i + 1]
        rlen = math.hypot(rx1 - rx0, ry1 - ry0)
        rang = math.atan2(ry1 - ry0, rx1 - rx0)
        gp.bm_box(bm_gh, ((rx0 + rx1) * 0.5, (ry0 + ry1) * 0.5, 0.28), (rlen + 0.16, 0.36, 0.56), rot_z=rang)

    # (b) Mid Front Segment (South of School Sign y=-14.75 -> 60 廣和街 green side gate y=-30.5)
    _add_open_grille_fence((mg.wall_x(sw_y0), sw_y0), (mg.wall_x(-30.5), -30.5), base_h=0.68, rail_h=1.55)

    # (b2) Dark-green double-leaf metal service/side gate at 60 廣和街 crosswalk (y=-30.5..-35.2)
    bm_sgate = bmesh.new()
    sg_x0, sg_y0 = mg.wall_x(-30.5), -30.5
    sg_x1, sg_y1 = mg.wall_x(-35.2), -35.2
    sg_mx, sg_my = 0.5 * (sg_x0 + sg_x1), 0.5 * (sg_y0 + sg_y1)
    gp.bm_box(bm_sgate, (sg_mx, sg_my, 2.25), (0.14, 4.75, 0.12), rot_z=ang_g)
    gp.bm_box(bm_sgate, (sg_mx, sg_my, 0.32), (0.14, 4.75, 0.12), rot_z=ang_g)
    for k in range(14):
        tk = k / 13.0
        gp.bm_box(bm_sgate, (sg_x0 + (sg_x1 - sg_x0) * tk, sg_y0 + (sg_y1 - sg_y0) * tk, 1.28), (0.07, 0.07, 2.05), rot_z=ang_g)

    # (c) South-West Front Mosaic Wall ending cleanly at SW Brick Garage Portal north edge (y=-63.6, final_step_14!)
    wx0, wy0 = mg.wall_x(-35.2), -35.2
    wx1, wy1 = mg.wall_x(-63.6), -63.6
    wdx, wdy = wx1 - wx0, wy1 - wy0
    wlen = math.hypot(wdx, wdy)
    wang = math.atan2(wdy, wdx)
    gp.bm_box(bm_south_wall, ((wx0 + wx1) * 0.5, (wy0 + wy1) * 0.5, 1.25), (wlen, 0.36, 2.50), rot_z=wang)

    # === 43 廣和街 SW CORNER BRICK GARAGE PORTAL — OPENING FACING WEST (-X along Guanghe St, y=-69.8..-63.6, exact final_step_14!) ===
    sy_wall = mg.SOUTH_WALL_Y
    pg_y0, pg_y1 = -69.8, -63.6
    pg_cy = 0.5 * (pg_y0 + pg_y1)
    pg_len = pg_y1 - pg_y0
    pg_cx = mg.wall_x(pg_cy) + 0.35  # Seated flush on west wall line!
    ca_g, sa_g = math.cos(ang_g), math.sin(ang_g)

    def pg_loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (pg_cx + lx * ca_g - ly * sa_g, pg_cy + lx * sa_g + ly * ca_g, lz)

    # Full terracotta-brick portal box + dark-brown overhanging roof coping (H=3.35m)
    gp.bm_box(bm_brick, pg_loc(0.0, 0.0, 1.62), (0.86, pg_len, 3.24), rot_z=ang_g)
    gp.bm_box(bm_brick, pg_loc(-0.06, 0.0, 3.30), (1.06, pg_len + 0.28, 0.22), rot_z=ang_g)
    gp.bm_box(bm_bronze, pg_loc(-0.08, 0.0, 3.43), (1.10, pg_len + 0.32, 0.06), rot_z=ang_g)
    # Left (north, ly=+1.75..+2.65) dark-green pedestrian side door + red spring couplet notice!
    gp.bm_box(bm_sgate, pg_loc(-0.44, 2.15, 1.22), (0.08, 0.96, 2.44), rot_z=ang_g)
    bm_redpaper = bmesh.new()
    gp.bm_box(bm_redpaper, pg_loc(-0.49, 2.15, 1.72), (0.02, 0.26, 0.62), rot_z=ang_g)
    gp.bm_box(bm_redpaper, pg_loc(-0.49, 2.15, 2.48), (0.02, 0.88, 0.14), rot_z=ang_g)
    objs.append(su.create_mesh_object("Landmark_SWPortal_RedNotice", bm_redpaper, palette["flag_red"], col))
    # Right (south, ly=-2.65..+1.15) wide brown roll-up garage shutter "車輛出入 請勿停車" facing WEST (-X -> viewer left=+Y, right=-Y!)
    bm_shutter_sw = bmesh.new()
    _add_plane_uv(
        bm_shutter_sw,
        pg_loc(-0.45, +1.15, 0.06),
        pg_loc(-0.45, -2.65, 0.06),
        pg_loc(-0.45, -2.65, 2.76),
        pg_loc(-0.45, +1.15, 2.76),
    )
    objs.append(su.create_mesh_object("Landmark_SWPortal_RollupShutter", bm_shutter_sw, palette["south_shutter"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_Guanghe_GreenSideGate", bm_sgate, palette["side_gate_green"], col))

    # Low dark-green corrugated sloped-roof utility shed tucked cleanly south of Chongqing Bldg west gable (y=-47.2, step_133!)
    bm_shed = bmesh.new()
    sh_x = mg.wall_x(-47.2) + 3.6
    gp.bm_box(bm_gh, (sh_x, -47.2, 1.32), (4.6, 5.2, 2.64))
    gp.bm_box(bm_shed, (sh_x, -47.2, 2.78), (5.2, 5.6, 0.18), rot_y=math.radians(-12.0))
    objs.append(su.create_mesh_object("Landmark_WestUtilityShedRoof", bm_shed, palette["side_gate_green"], col))

    # 1F Translucent green walkway canopy (Guanghe north only; SW Annex west canopy removed to clear SW brick garage portal!)
    bm_gcan = bmesh.new()
    gp.bm_box(bm_gcan, (-60.5, 22.8, 3.35), (14.5, 2.4, 0.14), rot_x=math.radians(14.0))
    objs.append(su.create_mesh_object("Landmark_FrontGreenCanopies", bm_gcan, palette["canopy_green_glass"], col))

    bm_arch_can = bmesh.new()
    bm_arch_rib = bmesh.new()
    # Barrel-vault arched dark-green polycarbonate roof starting cleanly flush against SW brick garage portal east face (x=-80.65..-53.5!)
    ac_x0, ac_x1, ac_yc, ac_r, ac_zb = -80.65, -53.5, -67.6, 1.55, 2.20
    ac_len = ac_x1 - ac_x0
    ac_cx = (ac_x0 + ac_x1) * 0.5
    n_arc = 10
    for i in range(n_arc):
        a0 = math.pi * i / n_arc
        a1 = math.pi * (i + 1) / n_arc
        am = 0.5 * (a0 + a1)
        seg_w = ac_r * (a1 - a0) + 0.04
        gp.bm_box(bm_arch_can, (ac_cx, ac_yc + math.cos(am) * ac_r, ac_zb + math.sin(am) * ac_r), (ac_len, seg_w, 0.08), rot_x=am - math.pi * 0.5)
    for rx_i in range(11):
        rx = ac_x0 + ac_len * rx_i / 10.0
        for sy_p in (ac_yc - ac_r + 0.1, ac_yc + ac_r - 0.1):
            gp.bm_cyl_axis(bm_arch_rib, (rx, sy_p, ac_zb * 0.5), 0.055, ac_zb, axis="Z", segments=6)
        for i in range(n_arc):
            a0 = math.pi * i / n_arc
            a1 = math.pi * (i + 1) / n_arc
            gp.bm_cyl_p2p(
                bm_arch_rib,
                (rx, ac_yc + math.cos(a0) * (ac_r + 0.03), ac_zb + math.sin(a0) * (ac_r + 0.03)),
                (rx, ac_yc + math.cos(a1) * (ac_r + 0.03), ac_zb + math.sin(a1) * (ac_r + 0.03)),
                0.04, 0.04, segments=6,
            )
    objs.append(su.create_mesh_object("Landmark_SouthArchedCanopy", bm_arch_can, palette["canopy_arch_darkgreen"], col))
    objs.append(su.create_mesh_object("Landmark_SouthArchedCanopyRibs", bm_arch_rib, palette["metal_dark"], col))

    # === SOUTH GUANGHE ST 4-SEGMENT STEPPED MOSAIC WALL + GATE 3 RIGHT BESIDE WUQUAN SE CORNER + SE CURVED WALL! ===
    # Seg 1: Low wall starting seamlessly from SW Brick Garage Portal SE corner (x=-81.5..-52.0, H=2.35m, exact final_step_14!)
    gp.bm_box(bm_south_wall, ((-81.5 - 52.0) * 0.5, sy_wall, 1.18), (29.5, 0.36, 2.36))
    # Seg 2: Stepped-UP HIGH WALL along basketball courts & Wuquan south end (x=-52.0..+6.5, H=2.98m + high dark-green ball-stop mesh! final_step_15!)
    gp.bm_box(bm_south_wall, ((-52.0 + 6.5) * 0.5, sy_wall, 1.49), (58.5, 0.38, 2.98))
    mx0, mx1 = -52.0, 6.5
    mlen = mx1 - mx0
    gp.bm_box(bm_south_mesh, ((mx0 + mx1) * 0.5, sy_wall, 3.92), (mlen, 0.04, 1.85))
    n_posts = int(mlen // 4.0) + 1
    for i in range(n_posts):
        px = mx0 + mlen * i / max(1, n_posts - 1)
        gp.bm_box(bm_metal, (px, sy_wall, 3.92), (0.09, 0.09, 1.88))
    gp.bm_box(bm_metal, ((mx0 + mx1) * 0.5, sy_wall, 4.84), (mlen, 0.07, 0.07))
    # Seg 3: EXACT 1 single bay of low mosaic wall between Wuquan SE corner high wall (+6.5) and Gate 3 west pier (+8.7)! (final_step_15!)
    gp.bm_box(bm_south_wall, ((6.5 + 8.7) * 0.5, sy_wall, 1.18), (2.2, 0.36, 2.36))

    # === 3 廣和街 GATE 3: TRUE OPEN STAINLESS STEEL DOUBLE-LEAF GATE IMMEDIATELY EAST OF WUQUAN BLDG (x=+8.7..+16.3, final_step_15!) ===
    bg_x0, bg_x1 = 8.7, 16.3
    bg_cx = (bg_x0 + bg_x1) * 0.5
    bg_w = bg_x1 - bg_x0
    bm_bg_pillars = bmesh.new()
    bm_bg_steel = bmesh.new()
    bm_bg_paper = bmesh.new()
    # Thick washed-concrete flanking gate piers
    for px_p in (bg_x0 - 0.28, bg_x1 + 0.28):
        gp.bm_box(bm_bg_pillars, (px_p, sy_wall, 1.28), (0.68, 0.68, 2.56))
        gp.bm_box(bm_bg_pillars, (px_p, sy_wall, 2.60), (0.78, 0.78, 0.14))
    # Stainless-steel double-leaf grille gate (horizontals, middle split frame & 26 vertical pickets!)
    for gz in (0.28, 1.12, 1.98):
        gp.bm_box(bm_bg_steel, (bg_cx, sy_wall, gz), (bg_w - 0.12, 0.09, 0.09))
    for gx_f in (bg_x0 + 0.08, bg_cx - 0.06, bg_cx + 0.06, bg_x1 - 0.08):
        gp.bm_box(bm_bg_steel, (gx_f, sy_wall, 1.14), (0.09, 0.10, 1.84))
    for k in range(1, 26):
        bx_p = bg_x0 + bg_w * k / 26.0
        if abs(bx_p - bg_cx) < 0.14:
            continue
        gp.bm_box(bm_bg_steel, (bx_p, sy_wall, 1.13), (0.04, 0.04, 1.72))
    # White printed notice sheet taped on Gate 3 (exact final_step_15 detail!)
    gp.bm_box(bm_bg_paper, (bg_cx - 0.6, sy_wall - 0.06, 1.48), (0.34, 0.02, 0.44))
    objs.append(su.create_mesh_object("Landmark_BackGate_Piers", bm_bg_pillars, palette["curb_concrete"], col))
    objs.append(su.create_mesh_object("Landmark_BackGate_StainlessGrille", bm_bg_steel, palette["stainless_gate"], col))
    objs.append(su.create_mesh_object("Landmark_BackGate_PaperNotice", bm_bg_paper, palette["road_white"], col))

    # Blue dual nameplate "重慶國小 3號門 | 學童接送區" on right gate pier + Green campus opening-hours plaque on right wall!
    bm_bg_blue = bmesh.new()
    _add_plane_uv(bm_bg_blue, (bg_x1 + 0.05, sy_wall - 0.36, 1.92), (bg_x1 + 1.35, sy_wall - 0.36, 1.92), (bg_x1 + 1.35, sy_wall - 0.36, 2.26), (bg_x1 + 0.05, sy_wall - 0.36, 2.26))
    objs.append(su.create_mesh_object("Landmark_BackGate_BlueNameplate", bm_bg_blue, palette["sign_backgate_blue"], col, auto_uv=False))

    bm_bg_rules = bmesh.new()
    _add_plane_uv(bm_bg_rules, (bg_x1 + 2.25, sy_wall - 0.21, 1.18), (bg_x1 + 3.25, sy_wall - 0.21, 1.18), (bg_x1 + 3.25, sy_wall - 0.21, 1.88), (bg_x1 + 2.25, sy_wall - 0.21, 1.88))
    objs.append(su.create_mesh_object("Landmark_BackGate_GreenRules", bm_bg_rules, palette["sign_campus_rules"], col, auto_uv=False))

    # Seg 4: East of Gate 3 to SE Curved Corner start (x=+16.3..+66.5, H=2.35m)
    gp.bm_box(bm_south_wall, ((16.3 + 66.5) * 0.5, sy_wall, 1.18), (50.2, 0.36, 2.36))

    # === 12 廣和街 SE GRAND CURVED MOSAIC WALL (12-segment R=7.0m smooth curve, final_step_157!) ===
    se_cx, se_cy, se_r = 66.5, -62.8, 7.0
    n_se = 12
    for i in range(n_se):
        a0 = -math.pi * 0.5 + (math.pi * 0.5) * (i / n_se)
        a1 = -math.pi * 0.5 + (math.pi * 0.5) * ((i + 1) / n_se)
        p0 = (se_cx + math.cos(a0) * se_r, se_cy + math.sin(a0) * se_r)
        p1 = (se_cx + math.cos(a1) * se_r, se_cy + math.sin(a1) * se_r)
        seg_l = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + 0.08
        seg_ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        gp.bm_box(bm_south_wall, ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, 1.18), (seg_l, 0.38, 2.36), rot_z=seg_ang)

    # (d) v10 EAST WUQUAN ST CONTINUOUS MOSAIC WALL (y=-62.8..+40.5) + NE LIGHT-GREEN DOUBLE GATE + NORTH MESH FENCE!
    ex0, ey0 = mg.east_wall_x(-62.8), -62.8
    ex1, ey1 = mg.east_wall_x(40.5), 40.5
    edx, edy = ex1 - ex0, ey1 - ey0
    elen = math.hypot(edx, edy)
    eang = math.atan2(edy, edx)
    # 1.98m-tall signature gray-frame red-lattice + pastel mosaic wall (matching step_163..180 exact sightline into track!)
    gp.bm_box(bm_south_wall, ((ex0 + ex1) * 0.5, (ey0 + ey1) * 0.5, 0.99), (elen, 0.36, 1.98), rot_z=eang)

    # 1 五權街: Glass-enclosed Campus Bulletin Board mounted on east face of mosaic wall (y=-15.5, step_170!)
    bul_y = -15.5
    bul_x = mg.east_wall_x(bul_y) + 0.24
    gp.bm_box(bm_bronze, (bul_x, bul_y, 1.48), (0.14, 2.25, 1.45), rot_z=mg.EAST_ROT_Z)
    bm_bul = bmesh.new()
    # Facing +X (east road viewer): viewer left=-Y (south), viewer right=+Y (north)!
    _add_plane_uv(bm_bul, (bul_x + 0.08, bul_y - 1.05, 0.82), (bul_x + 0.08, bul_y + 1.05, 0.82), (bul_x + 0.08, bul_y + 1.05, 2.12), (bul_x + 0.08, bul_y - 1.05, 2.12))
    objs.append(su.create_mesh_object("Landmark_EastWall_BulletinBoard", bm_bul, palette["campus_bulletin"], col, auto_uv=False))

    # 2 五權街北 C: Wet-track red-text notice + Blue "學童接送區" plaque + Green opening-hours plaque (step_180!)
    bm_wet = bmesh.new()
    wx_n = mg.east_wall_x(37.2) + 0.21
    _add_plane_uv(bm_wet, (wx_n, 36.4, 0.85), (wx_n, 37.9, 0.85), (wx_n, 37.9, 1.75), (wx_n, 36.4, 1.75))
    objs.append(su.create_mesh_object("Landmark_EastWall_WetTrackNotice", bm_wet, palette["sign_wet_track"], col, auto_uv=False))

    bm_spu = bmesh.new()
    px_n = mg.east_wall_x(39.4) + 0.21
    _add_plane_uv(bm_spu, (px_n, 38.8, 1.62), (px_n, 40.0, 1.62), (px_n, 40.0, 1.98), (px_n, 38.8, 1.98))
    objs.append(su.create_mesh_object("Landmark_EastWall_StudentPickup", bm_spu, palette["sign_student_pickup"], col, auto_uv=False))

    bm_ne_rules = bmesh.new()
    rx_n = mg.east_wall_x(40.1) + 0.21
    _add_plane_uv(bm_ne_rules, (rx_n, 39.6, 0.92), (rx_n, 40.45, 0.92), (rx_n, 40.45, 1.56), (rx_n, 39.6, 1.56))
    objs.append(su.create_mesh_object("Landmark_EastWall_NERules", bm_ne_rules, palette["sign_campus_rules"], col, auto_uv=False))

    # 2 五權街北 C / 15 五權街: Wide 7.3m Light-Green Vertical-Picket Double-Leaf NE Side Gate (y=+40.5..+47.8, step_180 & final_step_182!)
    bm_negate = bmesh.new()
    ne_y0, ne_y1 = 40.5, 47.8
    ne_x0, ne_x1 = mg.east_wall_x(ne_y0), mg.east_wall_x(ne_y1)
    ne_mx, ne_my = 0.5 * (ne_x0 + ne_x1), 0.5 * (ne_y0 + ne_y1)
    ne_len = math.hypot(ne_x1 - ne_x0, ne_y1 - ne_y0)
    # Flanking low concrete gate piers
    bm_ne_piers = bmesh.new()
    for py_p in (ne_y0, ne_y1):
        gp.bm_box(bm_ne_piers, (mg.east_wall_x(py_p), py_p, 1.05), (0.52, 0.52, 2.10), rot_z=mg.EAST_ROT_Z)
    objs.append(su.create_mesh_object("Landmark_NEGate_Piers", bm_ne_piers, palette["curb_concrete"], col))
    # Horizontal top/mid/bottom rails & 26 slim vertical light-green pickets
    for gz in (0.28, 1.02, 1.76):
        gp.bm_box(bm_negate, (ne_mx, ne_my, gz), (0.09, ne_len - 0.16, 0.08), rot_z=mg.EAST_ROT_Z)
    for k in range(1, 26):
        tk = k / 26.0
        gp.bm_box(bm_negate, (ne_x0 + (ne_x1 - ne_x0) * tk, ne_y0 + (ne_y1 - ne_y0) * tk, 1.02), (0.045, 0.045, 1.56), rot_z=mg.EAST_ROT_Z)
    objs.append(su.create_mesh_object("Landmark_NEGate_LightGreenPicket", bm_negate, palette["side_gate_lightgreen"], col))

    # v11 Track-North Heping Rd Perimeter (166 / 147 A / 147 B 和平路):
    #   (1) Angled NE corner join from NE light-green gate (east_wall_x(47.8), 47.8) to (60.5, y(60.5)-1.65)
    #   (2) Main track north green chain-link fence with mossy concrete plinth (x=+7.8..+60.5)
    #   (3) 147 和平路 B Double-Leaf Dark-Green Chain-Link Side Gate (x=+3.5..+7.8) + inner gray-tile stepped ramp!
    #   (4) Short west stub (x=+2.2..+3.5) transitioning to silver double-rail guardrails along Wuquan/Heping!
    def _add_north_chainlink_seg(p0: tuple[float, float], p1: tuple[float, float], base_h: float = 0.56, mesh_h: float = 2.18) -> None:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        slen = math.hypot(dx, dy)
        if slen < 0.2:
            return
        sang = math.atan2(dy, dx)
        smx, smy = 0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1])
        gp.bm_box(bm_stone, (smx, smy, base_h * 0.5), (slen, 0.28, base_h), rot_z=sang)
        gp.bm_box(bm_south_mesh, (smx, smy, base_h + mesh_h * 0.5), (slen, 0.04, mesh_h), rot_z=sang)
        n_p = max(2, int(slen // 3.4) + 1)
        for i in range(n_p):
            tp = i / max(1, n_p - 1)
            gp.bm_box(bm_metal, (p0[0] + dx * tp, p0[1] + dy * tp, base_h + mesh_h * 0.5), (0.08, 0.08, mesh_h + 0.04), rot_z=sang)
        gp.bm_box(bm_metal, (smx, smy, base_h + mesh_h), (slen, 0.06, 0.06), rot_z=sang)
        gp.bm_box(bm_metal, (smx, smy, base_h + mesh_h * 0.48), (slen, 0.05, 0.05), rot_z=sang)

    p_ne_end = (mg.east_wall_x(47.8), 47.8)
    p_n60 = (60.5, mg.heping_south_edge_y(60.5) - mg.HEPING_EAST_WALK_W)
    p_ng1 = (10.8, mg.heping_south_edge_y(10.8) - mg.HEPING_EAST_WALK_W)
    p_ng0 = (6.6, mg.heping_south_edge_y(6.6) - mg.HEPING_EAST_WALK_W)
    _add_north_chainlink_seg(p_n60, p_ne_end)
    _add_north_chainlink_seg(p_ng1, p_n60)
    # Short south-turning mesh wing tying west gate post cleanly into Wuquan NE corner pier (exact step_29.png!)
    _add_north_chainlink_seg((6.6, 39.6), p_ng0)

    # 147 和平路 B Double-Leaf Dark-Green Chain-Link Side Gate (x=6.6..10.8, right beside Wuquan east shutter! step_29!)
    bm_ngate_f = bmesh.new()
    bm_ngate_s = bmesh.new()
    gx_m, gy_m = 0.5 * (p_ng0[0] + p_ng1[0]), 0.5 * (p_ng0[1] + p_ng1[1])
    g_len = math.hypot(p_ng1[0] - p_ng0[0], p_ng1[1] - p_ng0[1])
    g_ang = mg.HEPING_ROT_Z
    for gp_pt in (p_ng0, p_ng1):
        gp.bm_box(bm_ngate_f, (gp_pt[0], gp_pt[1], 1.38), (0.14, 0.14, 2.50), rot_z=g_ang)
    for gz in (0.28, 1.32, 2.48):
        gp.bm_box(bm_ngate_f, (gx_m, gy_m, gz), (g_len - 0.14, 0.08, 0.08), rot_z=g_ang)
    gp.bm_box(bm_ngate_f, (gx_m - 0.05, gy_m, 1.38), (0.07, 0.08, 2.25), rot_z=g_ang)
    gp.bm_box(bm_ngate_f, (gx_m + 0.05, gy_m, 1.38), (0.07, 0.08, 2.25), rot_z=g_ang)
    gp.bm_box(bm_south_mesh, (gx_m, gy_m, 1.38), (g_len - 0.24, 0.04, 2.15), rot_z=g_ang)
    # Concrete entrance apron inside 147 B gate connecting straight to red track apron (step_29!)
    gp.bm_box(bm_ngate_s, (gx_m, gy_m - 2.6, 0.05), (4.2, 5.2, 0.10), rot_z=g_ang)
    objs.append(su.create_mesh_object("Landmark_NorthSideGate_Frame", bm_ngate_f, palette["side_gate_green"], col))
    objs.append(su.create_mesh_object("Landmark_NorthSideGate_Steps", bm_ngate_s, palette["sidewalk_south"], col, uv_scale=0.45))

    # === v11.3 147 和平路 WUQUAN NORTH DUAL BASEMENT ROLL-UP SHUTTERS + GREEN ANTI-SLIP RAMP (step_27/29/31 & final_step_64!) ===
    wy_n = 39.56
    bm_sh_silv = bmesh.new()
    bm_sh_tri = bmesh.new()
    bm_sh_lat = bmesh.new()
    bm_sh_cl = bmesh.new()
    bm_sh_ramp = bmesh.new()
    bm_sh_red = bmesh.new()
    bm_sh_wht = bmesh.new()
    bm_sh_trk = bmesh.new()
    bm_sh_ac = bmesh.new()

    # Terracotta structural portal piers & lintels framing the two basement shutters (x=-4.3..+6.5, z=0..3.95)
    for px_sh, pw_sh in [(-4.15, 0.72), (0.55, 0.88), (6.18, 0.72)]:
        gp.bm_box(bm_brick, (px_sh, wy_n + 0.06, 1.98), (pw_sh, 0.34, 3.96))
    gp.bm_box(bm_brick, (1.02, wy_n + 0.06, 3.16), (11.1, 0.34, 0.24))
    gp.bm_box(bm_brick, (1.02, wy_n + 0.06, 3.90), (11.1, 0.34, 0.22))
    # East WIDE Silver-Gray Ribbed Roll-up Shutter (x=+0.98..+5.82, facing +Y -> UV left=+X, right=-X!)
    _add_plane_uv(bm_sh_silv, (5.82, wy_n + 0.04, 0.04), (0.98, wy_n + 0.04, 0.04), (0.98, wy_n + 0.04, 3.08), (5.82, wy_n + 0.04, 3.08))
    # West NARROW 3-Tone Roll-up Shutter (Cream+Vents / Pale Pink / Charcoal Gray, x=-3.78..+0.12, final_step_64!)
    _add_plane_uv(bm_sh_tri, (0.12, wy_n + 0.04, 0.04), (-3.78, wy_n + 0.04, 0.04), (-3.78, wy_n + 0.04, 3.08), (0.12, wy_n + 0.04, 3.08))
    # Iconic Terracotta Diamond Lattice Ventilation Brick Bands above BOTH shutters + extending west toward skybridge (step_31!)
    for lx0_b, lx1_b, ly_b in [(0.98, 5.82, wy_n + 0.08), (-3.78, 0.12, wy_n + 0.08), (-9.6, -4.55, 39.26), (-15.0, -10.2, 39.26)]:
        _add_plane_uv(bm_sh_lat, (lx1_b, ly_b, 3.26), (lx0_b, ly_b, 3.26), (lx0_b, ly_b, 3.82), (lx1_b, ly_b, 3.82))
    # Vertical Calligraphy Scroll "吉龍舞春" on center divider pier + Red-White Cylindrical Warning Beacon + Conduit!
    _add_plane_uv(bm_sh_cl, (0.72, wy_n + 0.25, 1.15), (0.38, wy_n + 0.25, 1.15), (0.38, wy_n + 0.25, 2.28), (0.72, wy_n + 0.25, 2.28))
    gp.bm_cyl_axis(bm_sh_red, (0.20, wy_n + 0.26, 3.32), 0.055, 0.14, axis="Z", segments=10)
    gp.bm_cyl_axis(bm_sh_wht, (0.20, wy_n + 0.26, 3.18), 0.055, 0.14, axis="Z", segments=10)
    # Small circular No-Smoking sign on right brick pier (-4.08) + Silver shutter side rails
    gp.bm_cyl_axis(bm_sh_wht, (-4.06, wy_n + 0.24, 1.92), 0.13, 0.025, axis="Y", segments=14)
    gp.bm_cyl_axis(bm_sh_red, (-4.06, wy_n + 0.255, 1.92), 0.10, 0.015, axis="Y", segments=14)
    for tx_r in (-3.76, 0.10, 0.99, 5.80):
        gp.bm_box(bm_sh_trk, (tx_r, wy_n + 0.09, 1.56), (0.09, 0.10, 3.06))
    # Sunken Green Anti-Slip Driveway Ramp directly in front of West 3-Tone Shutter (step_27 & step_31!)
    mg._quad_extrude(
        bm_sh_ramp,
        [
            (-3.88, wy_n + 0.10),
            (0.22, wy_n + 0.10),
            (0.22, mg.heping_south_edge_y(0.22) - 0.16),
            (-3.88, mg.heping_south_edge_y(-3.88) - 0.16),
        ],
        -0.02,
        0.058,
    )
    # Concrete low curb cheeks flanking the green driveway ramp + horizontal storm drain grating at shutter sill!
    gp.bm_box(bm_stone, (-4.02, 43.8, 0.12), (0.24, 8.2, 0.24))
    gp.bm_box(bm_stone, (0.36, 43.8, 0.12), (0.24, 8.2, 0.24))
    # Wall-mounted AC unit right west of shutter bays (step_31!)
    gp.bm_box(bm_sh_ac, (-10.8, 39.42, 1.65), (0.88, 0.38, 0.64))

    objs.append(su.create_mesh_object("Landmark_WuquanB1_ShutterSilver", bm_sh_silv, palette["b1_shutter_silver"], "Bldg_Wuquan", auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_ShutterTri", bm_sh_tri, palette["b1_shutter_tri"], "Bldg_Wuquan", auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_BrickLattice", bm_sh_lat, palette["brick_lattice_band"], "Bldg_Wuquan", auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_Chunlian", bm_sh_cl, palette["pillar_chunlian"], "Bldg_Wuquan", auto_uv=False))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_GreenRamp", bm_sh_ramp, palette["ramp_green_antislip"], "Bldg_Wuquan"))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_BeaconRed", bm_sh_red, palette["signal_red"], "Bldg_Wuquan"))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_BeaconWhite", bm_sh_wht, palette["railing_white"], "Bldg_Wuquan"))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_ShutterRails", bm_sh_trk, palette["steel_silver"], "Bldg_Wuquan"))
    objs.append(su.create_mesh_object("Landmark_WuquanB1_ACUnit", bm_sh_ac, palette["ac_unit"], "Bldg_Wuquan"))

    # === v11.3 HEPING BLDG NORTH 1F/B1 FACADE UPGRADE (129 和平路: Cream Tile Base + B1 Louvers + Long Tiled Stair Retaining Wall West of Round Tower!) ===
    bm_hp_louver = bmesh.new()
    bm_hp_drain = bmesh.new()
    bm_hp_pipe = bmesh.new()
    hp_y = 39.04
    # Low cream square-tile architectural wainscot base (z=0..2.84m) along Heping Bldg north facade (x=-60.5..-4.5)
    gp.bm_box(bm_gh, (-32.5, hp_y + 0.06, 1.42), (56.0, 0.26, 2.84))
    gp.bm_box(bm_trim, (-32.5, hp_y + 0.12, 2.86), (56.1, 0.32, 0.12))
    # Continuous row of B1 dark-gray louvered basement ventilation windows (skipping round tower x=-26..-20 & stair wall -37..-27)
    for bx_v in range(-59, -5, 3):
        if -38 <= bx_v <= -20:
            continue
        gp.bm_box(bm_hp_louver, (bx_v, hp_y + 0.20, 0.78), (2.15, 0.08, 0.76))
        for lz_v in (0.54, 0.70, 0.86, 1.02):
            gp.bm_box(bm_frame, (bx_v, hp_y + 0.25, lz_v), (2.12, 0.04, 0.035))
        gp.bm_box(bm_trim, (bx_v, hp_y + 0.22, 1.18), (2.26, 0.12, 0.07))
        gp.bm_box(bm_trim, (bx_v, hp_y + 0.22, 0.38), (2.26, 0.12, 0.07))
    # Galvanized drainage gutter grating tucked along north wall foot + vertical silver downspouts + shutter sill drain!
    gp.bm_box(bm_hp_drain, (-32.5, hp_y + 0.52, 0.035), (56.0, 0.42, 0.04))
    gp.bm_box(bm_hp_drain, (-1.85, wy_n + 0.35, 0.062), (3.95, 0.32, 0.03))
    for px_ds in (-56.0, -48.5, -39.0, -19.8, -10.5):
        gp.bm_cyl_axis(bm_hp_pipe, (px_ds, hp_y + 0.24, 8.2), 0.055, 16.4, axis="Z", segments=8)

    # 129 和平路 (step_6.png right!): Long Cream-Tile Outdoor Terrace Wall & Ascending Staircase West of Semicircular Balcony Tower (x=-38.0..-26.4!)
    gp.bm_box(bm_gh, (-33.5, 40.75, 1.28), (9.2, 2.8, 2.56))
    gp.bm_box(bm_trim, (-33.5, 40.75, 2.60), (9.35, 2.95, 0.12))
    gp.bm_cyl_p2p(bm_hp_pipe, (-38.0, 42.15, 2.88), (-28.9, 42.15, 2.88), 0.032, 0.032, segments=6)
    for si in range(9):
        sx_st = -28.9 + si * 0.48
        sh_st = 2.48 * (9 - si) / 9.0
        gp.bm_box(bm_gh, (sx_st, 40.45, sh_st * 0.5), (0.50, 1.95, sh_st))
    gp.bm_box(bm_gh, (-26.8, 41.48, 1.48), (4.6, 0.28, 1.12), rot_y=math.radians(24.0))
    gp.bm_cyl_p2p(bm_hp_pipe, (-29.0, 41.48, 2.75), (-24.6, 41.48, 0.90), 0.032, 0.032, segments=6)

    objs.append(su.create_mesh_object("Landmark_HepingNorth_B1Louvers", bm_hp_louver, palette["b1_louver"], "Bldg_Heping"))
    objs.append(su.create_mesh_object("Landmark_HepingNorth_WallDrain", bm_hp_drain, palette["drain_grate"], "Bldg_Heping", uv_scale=1.2))
    objs.append(su.create_mesh_object("Landmark_HepingNorth_Downspouts", bm_hp_pipe, palette["steel_silver"], "Bldg_Heping"))

    objs.append(su.create_mesh_object("Landmark_MainGate_BronzeFence", bm_bronze, palette["fence_bronze"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_GuardhouseCream", bm_gh, palette["wall_guanghe"], col, uv_scale=0.38))
    objs.append(su.create_mesh_object("Landmark_MainGate_GuardhouseBrick", bm_brick, palette["wall_brick_red"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object("Landmark_MainGate_ArchOrange", bm_orange, palette["arch_orange"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_WhiteTrim", bm_trim, palette["concrete_trim"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_WallsStone", bm_stone, palette["wall_stone_cream"], col, uv_scale=0.4))
    objs.append(su.create_mesh_object("Landmark_MainGate_MetalGate", bm_metal, palette["metal_dark"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_GuardFrame", bm_frame, palette["window_frame"], col))
    objs.append(su.create_mesh_object("Landmark_MainGate_GuardGlass", bm_glass, palette["window_glass"], col))
    objs.append(su.create_mesh_object("Landmark_SouthWall_MosaicLattice", bm_south_wall, palette["wall_south_mosaic"], col, uv_scale=0.22))
    objs.append(su.create_mesh_object("Landmark_SouthWall_BallMesh", bm_south_mesh, palette["fence_mesh_green"], col))
    return objs


def build_gym_and_skybridge(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """高細節重慶國小運動中心（外露混凝土廊柱框架、寬大階梯＋斜扶手、捲門、鋁框玻璃金字塔天窗）＋海豚天橋＋分層半圓轉角陽台。"""
    col = "Bldg_Gym_Skybridge"
    gcfg = spec["gym_and_skybridge"]["gym"]
    scfg = spec["gym_and_skybridge"]["skybridge"]

    objs: List[bpy.types.Object] = []

    # 1. Comprehensive Sports Center / Gym (verified via step_63.png & step_65_shot_1.png!)
    x0, x1 = gcfg["x_min"], gcfg["x_max"]
    y0, y1 = gcfg["y_min"], gcfg["y_max"]
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    wx, wy = x1 - x0, y1 - y0
    gh = gcfg["height"]

    bm_wall = bmesh.new()
    bm_accent = bmesh.new()
    bm_roof = bmesh.new()
    bm_glass = bmesh.new()
    bm_sky = bmesh.new()
    bm_frame = bmesh.new()
    bm_shutter = bmesh.new()

    # Main gymnasium hall box
    gp.bm_box(bm_wall, (cx, cy, gh * 0.5), (wx, wy, gh))

    # Open structural concrete colonnade portico along south facade (depth 5.0m, 2F & 3F exposed beams & pillars!)
    arc_y0 = y0 - 5.0
    arc_y1 = y0
    # 2F landing slab + 3F open colonnade beam grid
    gp.bm_box(bm_wall, (cx, (arc_y0 + arc_y1) * 0.5, 3.25), (wx * 0.94, 5.0, 0.36))
    gp.bm_box(bm_wall, (cx, arc_y0 + 0.22, 6.95), (wx * 0.94, 0.44, 0.52))
    gp.bm_box(bm_wall, (cx, arc_y0 + 0.22, 9.65), (wx * 0.94, 0.44, 0.48))
    # Exposed structural columns along south colonnade + cross tie beams
    n_cols = 6
    for i in range(n_cols):
        px = (x0 + 1.4) + i * ((wx - 2.8) / (n_cols - 1))
        gp.bm_box(bm_wall, (px, arc_y0 + 0.25, 4.95), (0.58, 0.58, 9.9))
        gp.bm_box(bm_wall, (px, (arc_y0 + arc_y1) * 0.5, 6.95), (0.42, 5.0, 0.46))
        gp.bm_box(bm_wall, (px, (arc_y0 + arc_y1) * 0.5, 9.65), (0.42, 5.0, 0.42))

    # Recessed 2F entrance metal shutters (behind grand stairs, step_63.png!)
    stair_cx = cx + 4.2
    gp.bm_box(bm_shutter, (stair_cx, y0 - 0.12, 5.0), (14.6, 0.18, 3.2))
    gp.bm_box(bm_shutter, (cx - 10.5, y0 - 0.12, 1.6), (8.5, 0.18, 3.0))

    # Wide grand staircase ascending from ground apron to 2F entrance (kept strictly north of Heping Rd!)
    stair_w = 13.8
    for i in range(11):
        sh = 3.2 * (i + 1) / 11.0
        sy_step = arc_y0 - 2.9 + i * 0.28
        gp.bm_box(bm_wall, (stair_cx, sy_step, sh * 0.5), (stair_w, 0.32, sh))
    for side_x in (stair_cx - stair_w * 0.5 - 0.22, stair_cx + stair_w * 0.5 + 0.22):
        gp.bm_box(bm_wall, (side_x, arc_y0 - 1.5, 1.95), (0.42, 3.4, 1.4), rot_x=math.radians(42.0))
    # West side exterior staircase (visible on left of step_63.png!)
    for i in range(10):
        sh = 3.2 * (i + 1) / 10.0
        gp.bm_box(bm_wall, (x0 + 2.2, arc_y0 - 2.8 + i * 0.28, sh * 0.5), (2.6, 0.32, sh))

    # 4 translucent glass pyramid skylights with crisp aluminum ridge frames crowning south colonnade!
    for kx in (cx - 10.8, cx - 3.6, cx + 3.6, cx + 10.8):
        ky = (arc_y0 + arc_y1) * 0.5
        kz0, kz1 = 9.85, 11.55
        gp.bm_cyl_p2p(bm_sky, (kx, ky, kz0), (kx, ky, kz1), 2.55, 0.04, segments=4)
        # 4 aluminum hip ribs on each pyramid
        for a_deg in (45, 135, 225, 315):
            ar = math.radians(a_deg)
            gp.bm_cyl_p2p(bm_frame, (kx + math.cos(ar) * 2.55, ky + math.sin(ar) * 2.55, kz0), (kx, ky, kz1), 0.06, 0.06, segments=6)

    # Blue-orange "重慶國小運動中心" banner mounted on 2F colonnade beam (step_63.png!)
    bm_gban = bmesh.new()
    _add_plane_uv(bm_gban, (stair_cx - 7.6, arc_y0 - 0.08, 4.95), (stair_cx + 7.6, arc_y0 - 0.08, 4.95), (stair_cx + 7.6, arc_y0 - 0.08, 6.85), (stair_cx - 7.6, arc_y0 - 0.08, 6.85))
    objs.append(su.create_mesh_object("Bldg_Gym_Banner", bm_gban, palette["gym_banner"], col, auto_uv=False))

    # Upper 3F recessed ribbon windows with mullions on south, west & east walls
    gp.bm_box(bm_glass, (cx, y0 - 0.08, 10.8), (wx * 0.80, 0.14, 2.0))
    for i in range(9):
        mx = (x0 + 4.0) + i * ((wx - 8.0) / 8.0)
        gp.bm_box(bm_frame, (mx, y0 - 0.12, 10.8), (0.10, 0.16, 2.05))
    gp.bm_box(bm_glass, (x0 - 0.08, cy, 9.2), (0.14, wy * 0.72, 2.2))
    gp.bm_box(bm_glass, (x1 + 0.08, cy, 9.2), (0.14, wy * 0.72, 2.2))
    gp.bm_box(bm_accent, (cx, cy, gh - 0.28), (wx + 0.4, wy + 0.4, 0.56))

    # Green chain-link fence aligned cleanly along NORTH edge of v11 Heping Rd (off_n=+10.90, leaving entrance opening!)
    bm_gmesh = bmesh.new()
    bm_gpost = bmesh.new()
    for gx0, gx1 in [(x0 + 1.5, x0 + 14.0), (x1 - 7.5, x1 - 1.0)]:
        gy0_f = mg.heping_south_edge_y(gx0) + 10.90
        gy1_f = mg.heping_south_edge_y(gx1) + 10.90
        glen = math.hypot(gx1 - gx0, gy1_f - gy0_f)
        gp.bm_box(bm_gmesh, (0.5 * (gx0 + gx1), 0.5 * (gy0_f + gy1_f), 0.92), (glen, 0.05, 1.75), rot_z=mg.HEPING_ROT_Z)
        n_gp = max(2, int(glen // 3.0) + 1)
        for i in range(n_gp):
            t_g = i / max(1, n_gp - 1)
            gp.bm_cyl_axis(bm_gpost, (gx0 + (gx1 - gx0) * t_g, gy0_f + (gy1_f - gy0_f) * t_g, 0.94), 0.045, 1.84, axis="Z", segments=6)
        gp.bm_box(bm_gpost, (0.5 * (gx0 + gx1), 0.5 * (gy0_f + gy1_f), 1.82), (glen, 0.07, 0.07), rot_z=mg.HEPING_ROT_Z)
    objs.append(su.create_mesh_object("Bldg_Gym_FrontFence", bm_gmesh, palette["fence_mesh_green"], col))
    objs.append(su.create_mesh_object("Bldg_Gym_FrontFencePosts", bm_gpost, palette["metal_dark"], col))

    # Shallow-gable metal gymnasium roof + rooftop HVAC units
    pitch_ang = math.radians(6.5)
    half_w = wx * 0.52
    gp.bm_box(bm_roof, (cx - wx * 0.25, cy, gh + 0.95), (half_w, wy + 0.8, 0.35), rot_y=-pitch_ang)
    gp.bm_box(bm_roof, (cx + wx * 0.25, cy, gh + 0.95), (half_w, wy + 0.8, 0.35), rot_y=pitch_ang)
    for hx in (cx - 4.5, cx, cx + 4.5):
        gp.bm_cyl_axis(bm_accent, (hx, y1 - 3.5, gh + 1.3), 1.4, 2.0, axis="Z", segments=12)

    objs.append(su.create_mesh_object("Bldg_Gym_Walls", bm_wall, palette["gym_wall"], col, uv_scale=0.25))
    objs.append(su.create_mesh_object("Bldg_Gym_Accent", bm_accent, palette["gym_accent"], col))
    objs.append(su.create_mesh_object("Bldg_Gym_Roof", bm_roof, palette["roof_gym_metal"], col, uv_scale=0.15))
    objs.append(su.create_mesh_object("Bldg_Gym_Windows", bm_glass, palette["window_glass"], col))
    objs.append(su.create_mesh_object("Bldg_Gym_Skylights", bm_sky, palette["skylight_glass"], col))
    objs.append(su.create_mesh_object("Bldg_Gym_Frames", bm_frame, palette["window_frame"], col))
    objs.append(su.create_mesh_object("Bldg_Gym_Shutters", bm_shutter, palette["gym_shutter"], col, uv_scale=0.35))

    # 2. Skybridge spanning Heping Rd (detailed steel underside girders + leaping dolphin art + arched roof)
    sx = scfg["x_center"]
    sw = scfg["width"]
    sy0, sy1 = scfg["y_start"], scfg["y_end"]
    scy = (sy0 + sy1) * 0.5
    slen = sy1 - sy0
    dz = scfg["deck_z"]
    ch = scfg["clear_h"]

    bm_sb_body = bmesh.new()
    bm_sb_steel = bmesh.new()
    bm_sb_roof = bmesh.new()
    bm_sb_glass = bmesh.new()

    gp.bm_box(bm_sb_body, (sx, scy, dz), (sw, slen, 0.45))
    # Dark steel underside longitudinal & transverse I-beams (step_59.png!)
    for gx_b in (sx - sw * 0.42, sx, sx + sw * 0.42):
        gp.bm_box(bm_sb_steel, (gx_b, scy, dz - 0.34), (0.20, slen, 0.32))
    for i in range(10):
        gy_b = sy0 + slen * i / 9.0
        gp.bm_box(bm_sb_steel, (sx, gy_b, dz - 0.34), (sw, 0.16, 0.28))

    # Side parapets & v11.3 Ocean-Wave Mural Portal Support Piers (129 和平路 step_60 & step_58 EXACT position x=-17.5!)
    gp.bm_box(bm_sb_body, (sx - sw * 0.46, scy, dz + 0.78), (0.24, slen, 1.12))
    gp.bm_box(bm_sb_body, (sx + sw * 0.46, scy, dz + 0.78), (0.24, slen, 1.12))
    bm_sb_pillars = bmesh.new()
    bm_sb_base = bmesh.new()
    # South portal piers on Heping green strip (mg.heping_south_edge_y(sx)-2.2) & North portal piers inside Gym fence (+12.1)!
    py_south_pier = mg.heping_south_edge_y(sx) - 2.25
    py_north_pier = mg.heping_south_edge_y(sx) + 12.10
    for py in (py_south_pier, py_north_pier):
        gp.bm_box(bm_sb_pillars, (sx - sw * 0.38, py, dz * 0.5), (0.72, 0.72, dz))
        gp.bm_box(bm_sb_pillars, (sx + sw * 0.38, py, dz * 0.5), (0.72, 0.72, dz))
        gp.bm_box(bm_sb_pillars, (sx, py, dz - 0.42), (sw * 0.92, 0.68, 0.58))
        # Iconic sloped portal haunches & connecting low concrete tie-beam at bottom (exact step_60!)
        gp.bm_box(bm_sb_pillars, (sx - sw * 0.24, py, dz - 0.85), (0.68, 0.62, 0.62), rot_y=math.radians(-42.0))
        gp.bm_box(bm_sb_pillars, (sx + sw * 0.24, py, dz - 0.85), (0.68, 0.62, 0.62), rot_y=math.radians(42.0))
        gp.bm_box(bm_sb_base, (sx, py, 0.24), (sw * 0.92, 0.80, 0.48))
    objs.append(su.create_mesh_object("Landmark_Skybridge_WavePillars", bm_sb_pillars, palette["skybridge_pillar_wave"], col, uv_scale=0.32))
    objs.append(su.create_mesh_object("Landmark_Skybridge_PillarPlinth", bm_sb_base, palette["curb_concrete"], col, uv_scale=0.5))

    n_seg = 8
    for i in range(n_seg + 1):
        py = sy0 + slen * i / n_seg
        gp.bm_box(bm_sb_body, (sx - sw * 0.46, py, dz + ch * 0.55), (0.18, 0.18, ch))
        gp.bm_box(bm_sb_body, (sx + sw * 0.46, py, dz + ch * 0.55), (0.18, 0.18, ch))
    gp.bm_box(bm_sb_glass, (sx - sw * 0.46, scy, dz + 2.05), (0.06, slen - 0.6, 1.30))
    gp.bm_box(bm_sb_glass, (sx + sw * 0.46, scy, dz + 2.05), (0.06, slen - 0.6, 1.30))
    gp.bm_box(bm_sb_roof, (sx - sw * 0.26, scy, dz + ch + 0.32), (sw * 0.58, slen + 0.6, 0.14), rot_y=-math.radians(11.0))
    gp.bm_box(bm_sb_roof, (sx + sw * 0.26, scy, dz + ch + 0.32), (sw * 0.58, slen + 0.6, 0.14), rot_y=math.radians(11.0))

    bm_sb_art = bmesh.new()
    _add_plane_uv(bm_sb_art, (sx - sw * 0.5 - 0.14, sy0 + 0.3, dz - 0.35), (sx - sw * 0.5 - 0.14, sy1 - 0.3, dz - 0.35), (sx - sw * 0.5 - 0.14, sy1 - 0.3, dz + 1.42), (sx - sw * 0.5 - 0.14, sy0 + 0.3, dz + 1.42))
    _add_plane_uv(bm_sb_art, (sx + sw * 0.5 + 0.14, sy1 - 0.3, dz - 0.35), (sx + sw * 0.5 + 0.14, sy0 + 0.3, dz - 0.35), (sx + sw * 0.5 + 0.14, sy0 + 0.3, dz + 1.42), (sx + sw * 0.5 + 0.14, sy1 - 0.3, dz + 1.42))
    objs.append(su.create_mesh_object("Landmark_Skybridge_DolphinArt", bm_sb_art, palette["skybridge_dolphin"], col, auto_uv=False))

    objs.append(su.create_mesh_object("Landmark_Skybridge_Structure", bm_sb_body, palette["skybridge_body"], col))
    objs.append(su.create_mesh_object("Landmark_Skybridge_SteelGirders", bm_sb_steel, palette["metal_dark"], col))
    objs.append(su.create_mesh_object("Landmark_Skybridge_Roof", bm_sb_roof, palette["skybridge_roof"], col))
    objs.append(su.create_mesh_object("Landmark_Skybridge_Glass", bm_sb_glass, palette["skylight_glass"], col))

    # 3. Tiered Semicircular Balcony Towers:
    #    (a) North Heping Tower at (-23.0, 39.2) IMMEDIATELY WEST of Dolphin Skybridge (exact step_6.png & step_60.png!)
    bm_tw_core = bmesh.new()
    bm_tw_bal = bmesh.new()
    bm_tw_canopy = bmesh.new()
    bm_tw_glass = bmesh.new()
    bm_tw_rail = bmesh.new()
    tx, ty = -23.0, 39.2
    gp.bm_cyl_axis(bm_tw_core, (tx, ty, 8.6), 2.15, 17.2, axis="Z", segments=18)
    # 1F cream base + recessed curved floor-to-ceiling glass + iconic 1F translucent green curved canopy (step_60.png!)
    gp.bm_cyl_axis(bm_tw_bal, (tx, ty, 0.85), 3.25, 1.70, axis="Z", segments=20)
    gp.bm_cyl_axis(bm_tw_glass, (tx, ty, 2.55), 3.08, 1.65, axis="Z", segments=20)
    gp.bm_cyl_axis(bm_tw_canopy, (tx, ty, 3.48), 3.68, 0.16, axis="Z", segments=20)
    # 5 cantilevered circular cream-tile balcony slabs + silver stainless upper guardrail rings!
    for fl in range(1, 5):
        zf = 3.6 + (fl - 1) * 3.4
        gp.bm_cyl_axis(bm_tw_bal, (tx, ty, zf + 0.14), 3.35, 0.28, axis="Z", segments=20)
        gp.bm_cyl_axis(bm_tw_bal, (tx, ty, zf + 0.65), 3.32, 0.85, axis="Z", segments=20)
        for i_r in range(12):
            a0 = math.pi * i_r / 12.0
            a1 = math.pi * (i_r + 1) / 12.0
            gp.bm_cyl_p2p(
                bm_tw_rail,
                (tx + math.cos(a0) * 3.34, ty + math.sin(a0) * 3.34, zf + 1.24),
                (tx + math.cos(a1) * 3.34, ty + math.sin(a1) * 3.34, zf + 1.24),
                0.032, 0.032, segments=6,
            )
    gp.bm_cyl_axis(bm_tw_canopy, (tx, ty, 17.5), 3.55, 0.22, axis="Z", segments=20)
    objs.append(su.create_mesh_object("Landmark_CornerTowers_Core", bm_tw_core, palette["wall_salmon"], "Bldg_Heping", uv_scale=0.35))
    objs.append(su.create_mesh_object("Landmark_CornerTowers_Balconies", bm_tw_bal, palette["wall_guanghe"], "Bldg_Heping", uv_scale=0.35))
    objs.append(su.create_mesh_object("Landmark_CornerTowers_GreenCanopy", bm_tw_canopy, palette["canopy_green_glass"], "Bldg_Heping"))
    objs.append(su.create_mesh_object("Landmark_CornerTowers_1FGlass", bm_tw_glass, palette["window_glass"], "Bldg_Heping"))
    objs.append(su.create_mesh_object("Landmark_CornerTowers_SilverRails", bm_tw_rail, palette["steel_silver"], "Bldg_Heping"))

    #    (b) v12.3 3 廣和街 37.8° FOV EXACT REBUILD: Chongqing East End HOLLOW Open Semicircular Balcony Tower
    #        + 5F Full-Height White Square-Grid Safety Cage + Recessed L-Shaped Junction Corridor into Wuquan Bldg!
    #        (Verified 1:1 in final_step_14.png, step_6_shot_1.png, step_10_shot_1.png & campus_07.jpg!)
    bm_sc_salmon = bmesh.new()
    bm_sc_cream = bmesh.new()
    bm_sc_slab = bmesh.new()
    bm_sc_rail = bmesh.new()
    bm_sc_white = bmesh.new()
    bm_sc_canopy = bmesh.new()

    sx_c, sy_c = -12.55, -42.98  # Centered cleanly inside Chongqing east bay b=7 (x=-15.375..-7.0), leaving x=-9.9..-7.0 for recessed L-junction!
    r_out, r_in = 2.45, 2.18
    arc_segs = 18

    def _add_semi_disk(bm: bmesh.types.BMesh, cx: float, cy: float, r: float, z0: float, z1: float, segs: int = 18) -> None:
        """建立朝南 (-Y, angle pi..2pi) 的實心半圓弧形懸挑樓板。"""
        pts = [(cx + math.cos(math.pi + math.pi * i / segs) * r, cy + math.sin(math.pi + math.pi * i / segs) * r) for i in range(segs + 1)]
        # Extend straight back 0.45m north into corridor slab so junction is 100% airtight!
        pts.append((cx + r, cy + 0.45))
        pts.append((cx - r, cy + 0.45))
        vb = [bm.verts.new((px, py, z0)) for px, py in pts]
        vt = [bm.verts.new((px, py, z1)) for px, py in pts]
        new_f = [bm.faces.new(vt), bm.faces.new(list(reversed(vb)))]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            new_f.append(bm.faces.new((vb[i], vb[j], vt[j], vt[i])))
        bmesh.ops.recalc_face_normals(bm, faces=new_f)

    def _add_semi_ring_wall(bm: bmesh.types.BMesh, cx: float, cy: float, r0: float, r1: float, z0: float, z1: float, segs: int = 18) -> None:
        """建立真正中空開放的朝南 (-Y) 半圓弧形米白方磚陽台護牆！"""
        new_f = []
        for i in range(segs):
            a0 = math.pi + math.pi * i / segs
            a1 = math.pi + math.pi * (i + 1) / segs
            p_o0 = (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1)
            p_o1 = (cx + math.cos(a1) * r1, cy + math.sin(a1) * r1)
            p_i0 = (cx + math.cos(a0) * r0, cy + math.sin(a0) * r0)
            p_i1 = (cx + math.cos(a1) * r0, cy + math.sin(a1) * r0)
            vob0 = bm.verts.new((*p_o0, z0))
            vob1 = bm.verts.new((*p_o1, z0))
            vot0 = bm.verts.new((*p_o0, z1))
            vot1 = bm.verts.new((*p_o1, z1))
            vib0 = bm.verts.new((*p_i0, z0))
            vib1 = bm.verts.new((*p_i1, z0))
            vit0 = bm.verts.new((*p_i0, z1))
            vit1 = bm.verts.new((*p_i1, z1))
            new_f.append(bm.faces.new((vob0, vob1, vot1, vot0)))
            new_f.append(bm.faces.new((vib1, vib0, vit0, vit1)))
            new_f.append(bm.faces.new((vot0, vot1, vit1, vit0)))
            new_f.append(bm.faces.new((vib0, vib1, vob1, vob0)))
            if i == 0:
                new_f.append(bm.faces.new((vib0, vob0, vot0, vit0)))
            if i == segs - 1:
                new_f.append(bm.faces.new((vob1, vib1, vit1, vot1)))
        bmesh.ops.recalc_face_normals(bm, faces=new_f)

    # Full-height Salmon-Brick Flanking Structural Columns bracketing the hollow semicircular tower (exact step_10_shot_1.png!)
    for px_col in (-15.12, -9.95):
        gp.bm_box(bm_sc_salmon, (px_col, -42.92, 9.20), (0.56, 0.62, 18.40))
    # Two iconic exposed vertical silver drainage downspouts tucked immediately east of the right salmon pier (exact step_10_shot_1.png!)
    for px_dp in (-9.56, -9.36):
        gp.bm_cyl_axis(bm_sc_rail, (px_dp, -42.68, 8.75), 0.048, 17.50, axis="Z", segments=8)
        for z_cl in (2.5, 5.8, 9.2, 12.6, 16.0):
            gp.bm_box(bm_sc_rail, (px_dp - 0.05, -42.68, z_cl), (0.14, 0.12, 0.06))

    # 1F - 5F Hollow Semicircular Open Balconies + Recessed L-Shaped Connector Corridor into Wuquan West Corridor (x=-9.95..-6.85)
    for fl in range(5):
        zf = 0.0 if fl == 0 else (3.6 + (fl - 1) * 3.4)
        fh = 3.6 if fl == 0 else 3.4

        # Cantilevered semicircular balcony slab + solid hollow cream-tile curved parapet wall (1.22m tall)
        if fl >= 1:
            _add_semi_disk(bm_sc_slab, sx_c, sy_c, r_out, zf - 0.10, zf + 0.16, segs=arc_segs)
            # Recessed L-shaped junction corridor floor slab connecting Chongqing south corridor <-> Wuquan west corridor!
            gp.bm_box(bm_sc_slab, (-8.35, -41.45, zf + 0.08), (3.45, 2.75, 0.26))
        _add_semi_ring_wall(bm_sc_cream, sx_c, sy_c, r_in, r_out, zf + 0.08, zf + 1.24, segs=arc_segs)

        # Top transverse salmon beam behind semicircular balcony + recessed L-corridor lintel beam (x=-9.95..-6.85, recessed at y=-41.65!)
        if fl < 4:
            gp.bm_box(bm_sc_salmon, (sx_c, -42.75, zf + fh - 0.24), (5.2, 0.44, 0.48))
            gp.bm_box(bm_sc_salmon, (-8.38, -41.65, zf + fh - 0.24), (3.25, 0.40, 0.48))

        # Recessed L-shaped junction corridor cream parapet & twin silver rails (2F-5F, stepped cleanly 1.35m north of south wall!)
        if fl >= 1:
            gp.bm_box(bm_sc_cream, (-8.45, -41.65, zf + 0.62), (2.75, 0.24, 1.02))
            gp.bm_box(bm_sc_rail, (-8.45, -41.65, zf + 1.28), (2.75, 0.05, 0.05))
            gp.bm_box(bm_sc_rail, (-8.45, -41.65, zf + 1.44), (2.75, 0.05, 0.05))

        if fl < 4:
            # 1F-4F: Gleaming twin silver curved stainless-steel handrail tubes mounted above cream-tile curved parapet!
            r_rail = 2.34
            for z_r in (zf + 1.38, zf + 1.54):
                for i_r in range(arc_segs):
                    a0 = math.pi + math.pi * i_r / arc_segs
                    a1 = math.pi + math.pi * (i_r + 1) / arc_segs
                    gp.bm_cyl_p2p(
                        bm_sc_rail,
                        (sx_c + math.cos(a0) * r_rail, sy_c + math.sin(a0) * r_rail, z_r),
                        (sx_c + math.cos(a1) * r_rail, sy_c + math.sin(a1) * r_rail, z_r),
                        0.024, 0.024, segments=6,
                    )
            for i_p in range(0, arc_segs + 1, 2):
                a = math.pi + math.pi * i_p / arc_segs
                gp.bm_cyl_axis(bm_sc_rail, (sx_c + math.cos(a) * r_rail, sy_c + math.sin(a) * r_rail, zf + 1.39), 0.018, 0.34, axis="Z", segments=6)
        else:
            # 5F ICONIC DETAIL (step_10_shot_1.png!): Full-height WHITE SQUARE-GRID METAL SAFETY CAGE wrapping entire 5F semicircle + L-junction!
            r_cage = 2.34
            z_c0, z_c1 = zf + 1.24, zf + 3.24  # 15.04 .. 17.04m
            # 19 vertical white grid bars around semicircle
            for i_v in range(19):
                a = math.pi + math.pi * i_v / 18.0
                gp.bm_cyl_axis(bm_sc_white, (sx_c + math.cos(a) * r_cage, sy_c + math.sin(a) * r_cage, 0.5 * (z_c0 + z_c1)), 0.024, z_c1 - z_c0, axis="Z", segments=6)
            # 7 horizontal curved white grid rings forming crisp square mesh!
            for i_h in range(7):
                zh = z_c0 + (z_c1 - z_c0) * (i_h / 6.0)
                rad_h = 0.032 if i_h in (0, 6) else 0.020
                for i_s in range(arc_segs):
                    a0 = math.pi + math.pi * i_s / arc_segs
                    a1 = math.pi + math.pi * (i_s + 1) / arc_segs
                    gp.bm_cyl_p2p(
                        bm_sc_white,
                        (sx_c + math.cos(a0) * r_cage, sy_c + math.sin(a0) * r_cage, zh),
                        (sx_c + math.cos(a1) * r_cage, sy_c + math.sin(a1) * r_cage, zh),
                        rad_h, rad_h, segments=6,
                    )
            # Matching white square safety grid extending into the 5F recessed L-junction corridor (x=-9.8..-7.0, y=-41.65)!
            for i_jv in range(8):
                jx = -9.75 + 2.65 * (i_jv / 7.0)
                gp.bm_cyl_axis(bm_sc_white, (jx, -41.65, 0.5 * (z_c0 + z_c1)), 0.022, z_c1 - z_c0, axis="Z", segments=6)
            for i_jh in range(7):
                zh = z_c0 + (z_c1 - z_c0) * (i_jh / 6.0)
                gp.bm_box(bm_sc_white, (-8.42, -41.65, zh), (2.70, 0.04, 0.04))

            # Light white semicircular roof canopy capping ONLY the 5F safety cage cleanly (NO floating oversized green disc!)
            _add_semi_disk(bm_sc_canopy, sx_c, sy_c, r_out + 0.08, z_c1 + 0.02, z_c1 + 0.14, segs=arc_segs)
            for i_rib in (0, 4, 9, 14, 18):
                a = math.pi + math.pi * i_rib / 18.0
                gp.bm_cyl_p2p(
                    bm_sc_white,
                    (sx_c, sy_c + 0.15, z_c1 + 0.06),
                    (sx_c + math.cos(a) * (r_out + 0.06), sy_c + math.sin(a) * (r_out + 0.06), z_c1 + 0.04),
                    0.032, 0.028, segments=6,
                )
            # 5F roof parapet wall behind tower + L-junction roof slab tying Chongqing roof & Wuquan roof cleanly!
            gp.bm_box(bm_sc_slab, (-8.35, -41.45, 17.25), (3.45, 2.75, 0.28))
            gp.bm_box(bm_sc_cream, (sx_c, -42.78, 17.80), (5.2, 0.34, 1.15))
            gp.bm_box(bm_sc_cream, (-8.40, -41.65, 17.80), (3.15, 0.34, 1.15))

    objs.append(su.create_mesh_object("Landmark_SouthCorner_Columns", bm_sc_salmon, palette["wall_salmon"], "Bldg_Chongqing", uv_scale=0.35))
    objs.append(su.create_mesh_object("Landmark_SouthCorner_ArcParapets", bm_sc_cream, palette["wall_guanghe"], "Bldg_Chongqing", uv_scale=0.38))
    objs.append(su.create_mesh_object("Landmark_SouthCorner_ArcSlabs", bm_sc_slab, palette["concrete_floor"], "Bldg_Chongqing", uv_scale=0.35))
    objs.append(su.create_mesh_object("Landmark_SouthCorner_SteelRails", bm_sc_rail, palette["steel_silver"], "Bldg_Chongqing", smooth=True))
    objs.append(su.create_mesh_object("Landmark_SouthCorner_5FCageWhite", bm_sc_white, palette["railing_white"], "Bldg_Chongqing", smooth=True))
    objs.append(su.create_mesh_object("Landmark_SouthCorner_5FCanopy", bm_sc_canopy, palette["skylight_glass"], "Bldg_Chongqing"))

    # 4. v11.5 43 廣和街 SW CORNER 2-3F STEPPED ANNEX BUILDING (1:1 rebuild matching final_step_14.png!)
    #    - Front 2F clean cream-tile volume w/ wrapping L-shaped 2F balcony + deep dark-bronze security iron cage + recessed AC units
    #    - Rear NW 3F wing + 4F terracotta-framed stair penthouse tower w/ exterior metal roof-access ladder + U-shaped handrails + lightning rods!
    bm_sw_wall = bmesh.new()
    bm_sw_brick = bmesh.new()
    bm_sw_glass = bmesh.new()
    bm_sw_iron = bmesh.new()
    bm_sw_steel = bmesh.new()
    bm_sw_bush = bmesh.new()
    bm_sw_ac = bmesh.new()

    # (a) Front 2F Main Volume (x=-80.0..-65.5, y=-67.2..-58.5, H=7.85m, clean cream tile w/ crisp parapet — NO fake thick red corner outlines!)
    gp.bm_box(bm_sw_wall, (-72.75, -62.85, 3.92), (14.5, 8.7, 7.84))
    gp.bm_box(bm_sw_iron, (-72.75, -62.85, 7.88), (14.62, 8.82, 0.08))  # subtle dark roof coping line
    # 2F Wrapping L-shaped SW Corner Balcony (solid cream tile lower half z=3.6..4.75 + overhanging 2F top roof slab z=6.65..7.84!)
    # West projecting balcony half (x=-81.2..-80.0, y=-67.4..-60.6)
    gp.bm_box(bm_sw_wall, (-80.60, -64.0, 4.18), (1.20, 6.8, 1.16))
    gp.bm_box(bm_sw_wall, (-80.60, -64.0, 7.25), (1.26, 6.9, 1.18))
    # South projecting balcony half (x=-81.2..-67.8, y=-68.3..-67.1)
    gp.bm_box(bm_sw_wall, (-74.50, -67.70, 4.18), (13.4, 1.20, 1.16))
    gp.bm_box(bm_sw_wall, (-74.50, -67.70, 7.25), (13.5, 1.26, 1.18))
    # Recessed dark glazing + internal balcony columns & tucked-in AC units inside L-shaped cage!
    gp.bm_box(bm_sw_glass, (-80.04, -64.0, 5.70), (0.10, 6.2, 1.85))
    gp.bm_box(bm_sw_glass, (-74.50, -67.24, 5.70), (12.2, 0.10, 1.85))
    gp.bm_box(bm_sw_wall, (-80.15, -67.35, 5.70), (0.48, 0.48, 1.92))  # Cream structural corner pier inside cage!
    gp.bm_box(bm_sw_wall, (-74.2, -67.35, 5.70), (0.42, 0.42, 1.92))
    gp.bm_box(bm_sw_ac, (-71.2, -67.62, 5.25), (0.95, 0.42, 0.68))     # Recessed AC outdoor unit inside south cage!
    gp.bm_box(bm_sw_ac, (-76.8, -67.62, 5.25), (0.95, 0.42, 0.68))
    # Deep Dark-Bronze Vertical-Bar Box Security Iron Grilles wrapping BOTH west & south sides of 2F L-balcony (final_step_14!)
    for i in range(25):
        by_b = -68.25 + 7.60 * i / 24.0
        gp.bm_box(bm_sw_iron, (-81.22, by_b, 5.70), (0.03, 0.028, 1.92))
    for i in range(42):
        bx_b = -81.22 + 13.40 * i / 41.0
        gp.bm_box(bm_sw_iron, (bx_b, -68.28, 5.70), (0.028, 0.03, 1.92))
    for hz in (4.82, 5.42, 6.02, 6.62):
        gp.bm_box(bm_sw_iron, (-81.22, -64.45, hz), (0.035, 7.64, 0.032))
        gp.bm_box(bm_sw_iron, (-74.52, -68.28, hz), (13.44, 0.035, 0.032))

    # (b) Rear NW 3F Wing (x=-79.8..-68.5, y=-60.6..-52.6, H=10.5m) w/ authentic terracotta bands & vertical edge piers!
    gp.bm_box(bm_sw_wall, (-74.15, -56.60, 5.25), (11.3, 8.0, 10.5))
    # Terracotta horizontal waist bands & north-edge corner pier (matching final_step_14 left!)
    for z_b in (3.6, 6.95, 10.25):
        gp.bm_box(bm_sw_brick, (-79.82, -56.60, z_b), (0.14, 8.10, 0.36))
    gp.bm_box(bm_sw_brick, (-79.82, -52.82, 5.25), (0.16, 0.56, 10.6))
    gp.bm_box(bm_sw_brick, (-79.82, -60.38, 5.25), (0.16, 0.56, 10.6))
    # 2F West-North Projecting Box Security Grille Window + Small Metal Sunshade Canopy (y=-55.0, z=5.55, final_step_14 left!)
    gp.bm_box(bm_sw_glass, (-79.84, -55.0, 5.55), (0.10, 2.35, 1.48))
    gp.bm_box(bm_sw_iron, (-80.18, -55.0, 6.38), (0.76, 2.55, 0.08), rot_y=math.radians(-14.0))  # small sloped metal canopy
    for i in range(9):
        gp.bm_box(bm_sw_iron, (-80.46, -56.18 + 2.36 * i / 8.0, 5.55), (0.03, 0.025, 1.52))
    for hz in (4.82, 5.55, 6.26):
        gp.bm_box(bm_sw_iron, (-80.46, -55.0, hz), (0.03, 2.40, 0.028))
        gp.bm_box(bm_sw_iron, (-80.15, -56.18, hz), (0.64, 0.028, 0.028))
        gp.bm_box(bm_sw_iron, (-80.15, -53.82, hz), (0.64, 0.028, 0.028))
    # Flush dark-grilled square windows on 2F & 3F just south of projecting cage (y=-58.6, final_step_14!)
    for wz_sq in (5.05, 8.65):
        gp.bm_box(bm_sw_glass, (-79.84, -58.65, wz_sq), (0.10, 1.38, 1.15))
        for i in range(6):
            gp.bm_box(bm_sw_iron, (-79.92, -59.34 + 1.38 * i / 5.0, wz_sq), (0.03, 0.025, 1.18))
        for dz_s in (-0.56, 0.0, 0.56):
            gp.bm_box(bm_sw_iron, (-79.92, -58.65, wz_sq + dz_s), (0.03, 1.42, 0.025))
    # 2F roof terrace organic multi-tuft green bushes peeking behind parapet corner (final_step_14!)
    for bx_r, by_r, br_x, br_y, br_z in [
        (-78.8, -61.8, 0.65, 0.60, 0.58), (-78.0, -61.3, 0.58, 0.52, 0.48),
        (-78.4, -62.4, 0.52, 0.56, 0.45), (-77.5, -62.0, 0.48, 0.48, 0.40),
    ]:
        ret_b = bmesh.ops.create_icosphere(bm_sw_bush, subdivisions=2, radius=1.0)
        for v in ret_b["verts"]:
            n = 1.0 + 0.18 * math.sin(v.co.x * 7.2 + bx_r) * math.cos(v.co.y * 6.8 + by_r)
            v.co.x = bx_r + v.co.x * br_x * n
            v.co.y = by_r + v.co.y * br_y * n
            v.co.z = 8.18 + v.co.z * br_z * n

    # (c) 4F Terracotta-Framed Stair Penthouse Tower (x=-79.2..-73.0, y=-62.4..-56.4, z=10.2..13.8m, HERO silhouette of final_step_14!)
    tw_x0, tw_x1 = -79.2, -73.0
    tw_y0, tw_y1 = -62.4, -56.4
    tw_cx, tw_cy = 0.5 * (tw_x0 + tw_x1), 0.5 * (tw_y0 + tw_y1)
    gp.bm_box(bm_sw_wall, (tw_cx, tw_cy, 12.0), (tw_x1 - tw_x0, tw_y1 - tw_y0, 3.6))
    # Bold terracotta corner pilasters & top/bottom horizontal trim framing the cream tile penthouse tower!
    for py_tw in (tw_y0 + 0.30, tw_y1 - 0.30):
        gp.bm_box(bm_sw_brick, (tw_x0 - 0.04, py_tw, 12.0), (0.18, 0.68, 3.68))
    gp.bm_box(bm_sw_brick, (tw_x0 - 0.04, tw_cy, 13.68), (0.18, tw_y1 - tw_y0 + 0.10, 0.34))
    gp.bm_box(bm_sw_brick, (tw_x0 - 0.04, tw_cy, 10.35), (0.18, tw_y1 - tw_y0 + 0.10, 0.36))
    gp.bm_box(bm_sw_brick, (tw_cx, tw_y0 - 0.04, 13.68), (tw_x1 - tw_x0 + 0.10, 0.18, 0.34))
    gp.bm_box(bm_sw_brick, (tw_x1 - 0.30, tw_y0 - 0.04, 12.0), (0.66, 0.18, 3.68))
    # Iconic Exterior Vertical Galvanized Metal Roof-Access Ladder on Tower West Face + Top U-Shaped Safety Handrails + Lightning Rods!
    lad_x = tw_x0 - 0.24
    for ly_r in (tw_cy - 0.28, tw_cy + 0.28):
        gp.bm_cyl_axis(bm_sw_steel, (lad_x, ly_r, 11.45), 0.025, 6.2, axis="Z", segments=8)
        # U-shaped top safety return loops arching over parapet wall (exact final_step_14!)
        gp.bm_cyl_p2p(bm_sw_steel, (lad_x, ly_r, 14.55), (lad_x + 0.45, ly_r, 14.55), 0.025, 0.025, segments=6)
        gp.bm_cyl_axis(bm_sw_steel, (lad_x + 0.45, ly_r, 14.15), 0.025, 0.80, axis="Z", segments=6)
    for rung_i in range(14):
        rz_l = 8.65 + rung_i * 0.40
        gp.bm_cyl_axis(bm_sw_steel, (lad_x, tw_cy, rz_l), 0.016, 0.56, axis="Y", segments=6)
    # Rooftop lightning rods & antenna masts
    for rx_m, ry_m in [(tw_x0 + 0.8, tw_y0 + 0.8), (tw_x0 + 1.4, tw_y1 - 0.9)]:
        gp.bm_cyl_axis(bm_sw_steel, (rx_m, ry_m, 14.9), 0.025, 2.4, axis="Z", segments=6)

    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexWalls", bm_sw_wall, palette["wall_guanghe"], "Bldg_Chongqing", uv_scale=0.40))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexBrick", bm_sw_brick, palette["wall_brick_red"], "Bldg_Chongqing", uv_scale=0.45))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexGlass", bm_sw_glass, palette["window_glass"], "Bldg_Chongqing"))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexIronGrilles", bm_sw_iron, palette["fence_bronze"], "Bldg_Chongqing"))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexLadder", bm_sw_steel, palette["steel_silver"], "Bldg_Chongqing"))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexBushes", bm_sw_bush, palette["tree_foliage_a"], "Bldg_Chongqing"))
    objs.append(su.create_mesh_object("Bldg_Chongqing_SWAnnexAC", bm_sw_ac, palette["ac_unit"], "Bldg_Chongqing"))

    # Colorful yellow-and-blue domed children's playground set peeking above 43 廣和街 stepped wall (step_149!)
    bm_play_a = bmesh.new()
    bm_play_b = bmesh.new()
    px, py = -51.5, -62.0
    gp.bm_box(bm_play_a, (px, py, 1.6), (3.2, 3.2, 3.2))
    gp.bm_cyl_axis(bm_play_a, (px, py, 3.8), 2.1, 1.2, axis="Z", segments=8)
    gp.bm_cyl_p2p(bm_play_b, (px, py, 4.25), (px, py, 5.15), 2.15, 0.45, segments=8)
    gp.bm_box(bm_play_b, (px + 2.6, py, 1.25), (3.2, 1.15, 0.24), rot_y=math.radians(32.0))
    objs.append(su.create_mesh_object("Zone_Playground_Frame", bm_play_a, palette["road_yellow"], "Zone_Courtyard"))
    objs.append(su.create_mesh_object("Zone_Playground_Slide", bm_play_b, palette["flag_blue"], "Zone_Courtyard"))

    return objs
