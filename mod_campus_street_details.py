"""重慶國小街景生命力與校內導引細節模組：黃色校車、周邊汽機車、人行道緣石／紅綠燈／反射鏡／機車格、棟別牌與走廊門牌。"""
import math
import os
from typing import Dict, List

import bmesh
import bpy

import coords as mg
import geom_primitives as gp
import studio_utils as su

_add_plane_uv = gp.add_plane_uv
_add_plane_uv_rect = gp.add_plane_uv_rect


def _add_smart_parking_pillar(
    bm_silver: bmesh.types.BMesh,
    bm_dark: bmesh.types.BMesh,
    bm_glass: bmesh.types.BMesh,
    bm_front_uv: bmesh.types.BMesh,
    bm_led: bmesh.types.BMesh,
    x: float,
    y: float,
    z0: float = 0.135,
    rot_z: float = 0.0,
) -> None:
    """高細節新北市智慧化停車收費柱（金屬底座法蘭＋鋁合金銀灰柱框＋正面亮黑雙鏡頭光學面板＋雙側車牌辨識窗＋防雨斜帽＋LED 燈條）。"""
    ca, sa = math.cos(rot_z), math.sin(rot_z)

    def loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z0 + lz)

    # 1. Heavy dark-gray anchor flange base + 4 corner bolts
    gp.bm_box(bm_dark, loc(0.0, 0.0, 0.025), (0.28, 0.20, 0.05), rot_z=rot_z)
    for bx in (-0.10, 0.10):
        for by in (-0.07, 0.07):
            gp.bm_cyl_axis(bm_silver, loc(bx, by, 0.058), 0.014, 0.018, axis="Z", segments=6)

    # 2. Main brushed-aluminum silver column housing (depth X=0.20m, width Y=0.115m, height 1.44m)
    gp.bm_box(bm_silver, loc(0.0, 0.0, 0.76), (0.20, 0.115, 1.42), rot_z=rot_z)
    # Recessed black glossy optical front/back fascia strips & beveled side bezel rails
    gp.bm_box(bm_glass, loc(-0.095, 0.0, 0.80), (0.025, 0.096, 1.24), rot_z=rot_z)
    gp.bm_box(bm_glass, loc(0.095, 0.0, 0.80), (0.020, 0.092, 1.18), rot_z=rot_z)

    # 3. Road-facing (-X) high-res UV optical sensor panel (camera lenses + OLED screen + QR code)
    # Facing -X -> viewer left is +Y, viewer right is -Y so text reads forward!
    _add_plane_uv(
        bm_front_uv,
        loc(-0.112, +0.054, 0.16),
        loc(-0.112, -0.054, 0.16),
        loc(-0.112, -0.054, 1.42),
        loc(-0.112, +0.054, 1.42),
    )

    # 4. Dual side-angled ANPR license-plate camera windows (facing +Y and -Y parking stalls!)
    for sy in (-0.062, 0.062):
        gp.bm_box(bm_dark, loc(-0.01, sy, 1.20), (0.135, 0.022, 0.34), rot_z=rot_z)
        gp.bm_box(bm_glass, loc(-0.01, sy * 1.12, 1.20), (0.105, 0.014, 0.28), rot_z=rot_z)

    # 5. Sloped rain-shedding dark cap + crisp glowing green LED status bar
    gp.bm_box(bm_dark, loc(0.0, 0.0, 1.49), (0.225, 0.132, 0.055), rot_y=math.radians(8.0), rot_z=rot_z)
    gp.bm_box(bm_led, loc(-0.105, 0.0, 1.445), (0.018, 0.072, 0.022), rot_z=rot_z)


def _add_sedan(
    bm_body: bmesh.types.BMesh,
    bm_glass: bmesh.types.BMesh,
    bm_tire: bmesh.types.BMesh,
    pos: tuple[float, float, float],
    yaw_deg: float,
    length: float = 4.4,
    width: float = 1.82,
    height: float = 1.48,
) -> None:
    """低面數精巧現代轎車／休旅車（含車身、斜風擋玻璃座艙與四輪）。"""
    x, y, z = pos
    ang = math.radians(yaw_deg)
    ca, sa = math.cos(ang), math.sin(ang)

    def loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz)

    # Lower chassis body
    gp.bm_box(bm_body, loc(0.0, 0.0, 0.62), (length, width, 0.68), rot_z=ang)
    # Upper cabin greenhouse
    gp.bm_box(bm_body, loc(-0.18, 0.0, 1.18), (length * 0.54, width * 0.86, 0.54), rot_z=ang)
    gp.bm_box(bm_glass, loc(-0.18, 0.0, 1.18), (length * 0.56, width * 0.88, 0.44), rot_z=ang)
    # 4 Wheels
    for wx in (-length * 0.31, length * 0.31):
        for wy in (-width * 0.47, width * 0.47):
            p0 = loc(wx, wy - 0.11, 0.34)
            p1 = loc(wx, wy + 0.11, 0.34)
            gp.bm_cyl_p2p(bm_tire, p0, p1, 0.34, 0.34, segments=10)


def _add_scooter(
    bm_body: bmesh.types.BMesh,
    bm_tire: bmesh.types.BMesh,
    bm_metal: bmesh.types.BMesh,
    pos: tuple[float, float, float],
    yaw_deg: float,
    bm_plate: bmesh.types.BMesh = None,
    bm_taillight: bmesh.types.BMesh = None,
) -> None:
    """台灣街頭標配速克達機車（含白底車牌、紅尾燈、雙鏡、座墊與輪胎，還原 78/88 廣和街整排停放機車！）。"""
    x, y, z = pos
    ang = math.radians(yaw_deg)
    ca, sa = math.cos(ang), math.sin(ang)

    def loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz)

    # Front leg shield + floorboard + rear seat fairing
    gp.bm_box(bm_body, loc(0.42, 0.0, 0.62), (0.28, 0.48, 0.68), rot_z=ang)
    gp.bm_box(bm_body, loc(0.0, 0.0, 0.32), (0.65, 0.42, 0.14), rot_z=ang)
    gp.bm_box(bm_body, loc(-0.42, 0.0, 0.60), (0.72, 0.44, 0.36), rot_z=ang)
    # Dark seat, rear fender & handlebars + twin mirrors
    gp.bm_box(bm_tire, loc(-0.34, 0.0, 0.82), (0.64, 0.34, 0.14), rot_z=ang)
    gp.bm_box(bm_tire, loc(-0.78, 0.0, 0.46), (0.08, 0.24, 0.30), rot_z=ang)
    gp.bm_box(bm_metal, loc(0.40, 0.0, 1.02), (0.14, 0.62, 0.10), rot_z=ang)
    for my in (-0.28, 0.28):
        gp.bm_cyl_axis(bm_metal, loc(0.42, my, 1.14), 0.014, 0.18, axis="Z", segments=6)
        gp.bm_box(bm_tire, loc(0.42, my, 1.24), (0.04, 0.11, 0.07), rot_z=ang)
    # Rear white license plate + red taillight (iconic 78/88 廣和街 streetview rear-row detail!)
    if bm_plate is not None:
        gp.bm_box(bm_plate, loc(-0.83, 0.0, 0.44), (0.025, 0.22, 0.13), rot_z=ang)
    if bm_taillight is not None:
        gp.bm_box(bm_taillight, loc(-0.79, 0.0, 0.68), (0.04, 0.24, 0.09), rot_z=ang)
    # Front & rear tires
    for wx in (-0.56, 0.54):
        gp.bm_cyl_p2p(bm_tire, loc(wx, -0.07, 0.24), loc(wx, 0.07, 0.24), 0.24, 0.24, segments=8)


def _add_youbike(
    bm_frame: bmesh.types.BMesh,
    bm_orange: bmesh.types.BMesh,
    bm_yellow: bmesh.types.BMesh,
    bm_tire: bmesh.types.BMesh,
    bm_metal: bmesh.types.BMesh,
    pos: tuple[float, float, float],
    yaw_deg: float,
) -> None:
    """精緻台灣 YouBike 2.0 微笑單車（白色低跨車架＋亮橘後輪護蓋泥除＋鮮黃前置菜籃＋雙輪龍頭！對照 43/76 廣和街！）。"""
    x, y, z = pos
    ang = math.radians(yaw_deg)
    ca, sa = math.cos(ang), math.sin(ang)

    def loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz)

    # Front & rear wheels (r=0.31m)
    for wx in (-0.52, 0.52):
        gp.bm_cyl_p2p(bm_tire, loc(wx, -0.032, 0.31), loc(wx, 0.032, 0.31), 0.31, 0.31, segments=12)
        gp.bm_cyl_p2p(bm_metal, loc(wx, -0.04, 0.31), loc(wx, 0.04, 0.31), 0.06, 0.06, segments=8)
    # Iconic bright orange half-moon rear wheel fender & chain guard
    gp.bm_box(bm_orange, loc(-0.50, 0.0, 0.44), (0.58, 0.09, 0.28), rot_z=ang)
    # White step-through main frame + fork + seatpost tube
    gp.bm_cyl_p2p(bm_frame, loc(-0.52, 0.0, 0.32), loc(-0.08, 0.0, 0.36), 0.032, 0.032, segments=6)
    gp.bm_cyl_p2p(bm_frame, loc(-0.08, 0.0, 0.36), loc(0.42, 0.0, 0.72), 0.035, 0.035, segments=6)
    gp.bm_cyl_p2p(bm_frame, loc(-0.18, 0.0, 0.36), loc(-0.28, 0.0, 0.82), 0.028, 0.024, segments=6)
    gp.bm_cyl_p2p(bm_frame, loc(0.52, 0.0, 0.32), loc(0.38, 0.0, 0.94), 0.026, 0.024, segments=6)
    # Handlebar + dark seat
    gp.bm_cyl_p2p(bm_metal, loc(0.38, -0.26, 0.96), loc(0.38, 0.26, 0.96), 0.018, 0.018, segments=6)
    gp.bm_box(bm_tire, loc(-0.29, 0.0, 0.85), (0.24, 0.16, 0.06), rot_z=ang)
    # Iconic bright yellow front basket!
    gp.bm_box(bm_yellow, loc(0.56, 0.0, 0.80), (0.28, 0.34, 0.24), rot_z=ang)


def _add_south_hazard_lamp(
    bm_silver: bmesh.types.BMesh,
    bm_hazard: bmesh.types.BMesh,
    bm_dark: bmesh.types.BMesh,
    bm_plinth: bmesh.types.BMesh,
    x: float,
    y: float,
    z0: float = 0.135,
    arm_yaw_deg: float = -90.0,
    pole_h: float = 4.65,
) -> None:
    """還原南側廣和街（92/43/76/3/12 號）標配細鍍鋅路燈桿（水泥底座＋下半段黃黑斜紋警示貼帶＋扁平 LED 燈頭！）。"""
    gp.bm_box(bm_plinth, (x, y, z0 + 0.08), (0.34, 0.34, 0.16))
    # Lower silver base, mid yellow-black hazard sleeve (z=0.95..2.05), upper silver shaft
    gp.bm_cyl_axis(bm_silver, (x, y, z0 + 0.52), 0.052, 0.90, axis="Z", segments=8)
    gp.bm_cyl_axis(bm_hazard, (x, y, z0 + 1.50), 0.058, 1.12, axis="Z", segments=8)
    upper_h = pole_h - 2.02
    gp.bm_cyl_axis(bm_silver, (x, y, z0 + 2.02 + upper_h * 0.5), 0.048, upper_h, axis="Z", segments=8)
    # Angled slim arm & modern flat gray LED lamp head
    rad = math.radians(arm_yaw_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    gp.bm_cyl_p2p(bm_silver, (x, y, z0 + pole_h - 0.12), (x + ca * 1.15, y + sa * 1.15, z0 + pole_h + 0.10), 0.036, 0.030, segments=6)
    gp.bm_box(bm_dark, (x + ca * 1.25, y + sa * 1.25, z0 + pole_h + 0.10), (0.48, 0.22, 0.09), rot_z=rad)


def build_vehicles_and_street_furniture(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置黃色重慶國小校車、周邊汽機車、高細節智慧停車收費柱、10 廣和街雙號誌群、花崗岩石凳與機車格。"""
    col = "Street_Life"
    objs: List[bpy.types.Object] = []

    ang_g = mg.GUANGHE_ROT_Z
    # 1. Yellow CGES School Bus driving south in west lane (clean of gate & 60 廣和街 views!)
    bm_bus_y = bmesh.new()
    bm_bus_g = bmesh.new()
    bm_bus_t = bmesh.new()
    bm_bus_s = bmesh.new()
    by_bus = -49.5
    bx, by, bz = mg.curb_x(by_bus) - 7.8, by_bus, 0.015
    blen, bw, bh = 7.4, 2.25, 2.65
    # Aligned along Guanghe St heading south (-Y along slope -> yaw = -90 - 8.5 = -98.5 deg)
    bang = math.radians(-90.0 - mg.GUANGHE_SLOPE_DEG)
    ca, sa = math.cos(bang), math.sin(bang)

    def bloc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (bx + lx * ca - ly * sa, by + lx * sa + ly * ca, bz + lz)

    gp.bm_box(bm_bus_y, bloc(0.0, 0.0, 1.48), (blen, bw, bh - 0.35), rot_z=bang)
    gp.bm_box(bm_bus_g, bloc(blen * 0.5 + 0.02, 0.0, 1.85), (0.06, bw * 0.88, 0.95), rot_z=bang)
    gp.bm_box(bm_bus_g, bloc(-blen * 0.5 - 0.02, 0.0, 1.85), (0.06, bw * 0.84, 0.85), rot_z=bang)
    _add_plane_uv(bm_bus_s, bloc(-3.55, -bw * 0.5 - 0.03, 0.52), bloc(3.55, -bw * 0.5 - 0.03, 0.52), bloc(3.55, -bw * 0.5 - 0.03, 2.48), bloc(-3.55, -bw * 0.5 - 0.03, 2.48))
    _add_plane_uv(bm_bus_s, bloc(3.55, bw * 0.5 + 0.03, 0.52), bloc(-3.55, bw * 0.5 + 0.03, 0.52), bloc(-3.55, bw * 0.5 + 0.03, 2.48), bloc(3.55, bw * 0.5 + 0.03, 2.48))
    for wx in (-2.2, 2.2):
        for wy in (-bw * 0.48, bw * 0.48):
            gp.bm_cyl_p2p(bm_bus_t, bloc(wx, wy - 0.14, 0.45), bloc(wx, wy + 0.14, 0.45), 0.45, 0.45, segments=12)

    objs.append(su.create_mesh_object("Street_SchoolBus_Body", bm_bus_y, palette["bus_yellow"], col))
    objs.append(su.create_mesh_object("Street_SchoolBus_SideArt", bm_bus_s, palette["bus_side"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Street_SchoolBus_Glass", bm_bus_g, palette["window_glass"], col))
    objs.append(su.create_mesh_object("Street_SchoolBus_Tires", bm_bus_t, palette["tire_rubber"], col))

    # 2. Surrounding cars (keep main gate apron & smart parking bays unobstructed so markings shine!)
    bm_car_s = bmesh.new()
    bm_car_k = bmesh.new()
    bm_car_w = bmesh.new()
    bm_car_r = bmesh.new()
    bm_car_b = bmesh.new()
    bm_v_glass = bmesh.new()
    bm_v_tire = bmesh.new()
    bm_v_metal = bmesh.new()

    hp_yaw_e = mg.HEPING_SLOPE_DEG
    hp_yaw_w = 180.0 + mg.HEPING_SLOPE_DEG
    _add_sedan(bm_car_s, bm_v_glass, bm_v_tire, (-47.0, mg.heping_south_edge_y(-47.0) + 2.55, 0.015), hp_yaw_e, 4.5, 1.84, 1.54)  # Silver SUV eastbound on Heping Rd
    _add_sedan(bm_car_k, bm_v_glass, bm_v_tire, (34.5, mg.heping_south_edge_y(34.5) + 2.55, 0.015), hp_yaw_e, 4.6, 1.86, 1.58)  # Dark SUV approaching 166 bus stop (step_2!)
    _add_sedan(bm_car_w, bm_v_glass, bm_v_tire, (-46.5, 59.8, 0.015), hp_yaw_e, 4.4, 1.80, 1.48)  # White car in Gym north apron
    _add_sedan(bm_car_b, bm_v_glass, bm_v_tire, (-6.5, mg.heping_south_edge_y(-6.5) + 2.55, 0.015), hp_yaw_e, 4.4, 1.80, 1.46)  # Blue car eastbound on Heping Rd
    _add_sedan(bm_car_w, bm_v_glass, bm_v_tire, (12.0, mg.heping_south_edge_y(12.0) + 7.75, 0.015), hp_yaw_w, 4.5, 1.82, 1.50)  # White car westbound on Heping Rd
    # Silver MPV driving west on South Guanghe St (cleanly clear of blue disabled bay & scooters!)
    _add_sedan(bm_car_s, bm_v_glass, bm_v_tire, (-42.0, -79.2, 0.015), 180.0, 4.35, 1.78, 1.58)
    # 2 五權街中段 A: 3 cars parked neatly in bays 10, 09, 08 (black SUV + two white sedans, exact step_176!)
    east_car_yaw = 90.0 + mg.EAST_SLOPE_DEG
    _add_sedan(bm_car_k, bm_v_glass, bm_v_tire, (mg.east_curb_x(-5.4) + 1.25, -5.4, 0.015), east_car_yaw, 4.65, 1.88, 1.62)
    _add_sedan(bm_car_w, bm_v_glass, bm_v_tire, (mg.east_curb_x(-0.2) + 1.25, -0.2, 0.015), east_car_yaw, 4.45, 1.80, 1.46)
    _add_sedan(bm_car_w, bm_v_glass, bm_v_tire, (mg.east_curb_x(4.9) + 1.25, 4.9, 0.015), east_car_yaw, 4.30, 1.78, 1.48)
    # Yellow taxi driving through 15 五權街 NE intersection (final_step_182!)
    bm_taxi = bmesh.new()
    _add_sedan(bm_taxi, bm_v_glass, bm_v_tire, (mg.east_curb_x(44.5) + 3.6, 44.5, 0.015), east_car_yaw, 4.45, 1.80, 1.48)
    objs.append(su.create_mesh_object("Street_Cars_Taxi", bm_taxi, palette["bus_yellow"], col))

    # Parked scooters along South Guanghe St (TWO long dense rows: West 18 + East 15 = 33 scooters, matching 43/76/3A 廣和街!)
    scooter_bms = [bm_car_k, bm_car_w, bm_car_s, bm_car_r, bm_car_b]
    sc_y_south = mg.SOUTH_CURB_Y - 1.25  # -74.45m, cleanly ON asphalt!
    for i in range(18):
        sx = -55.2 + i * 1.58
        jitter = ((i * 11) % 9 - 4) * 2.1
        _add_scooter(scooter_bms[i % len(scooter_bms)], bm_v_tire, bm_v_metal, (sx, sc_y_south, 0.015), 90.0 + jitter, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    for i in range(11):
        sx = -12.8 + i * 1.68
        jitter = ((i * 7) % 9 - 4) * 2.2
        _add_scooter(scooter_bms[(i + 2) % len(scooter_bms)], bm_v_tire, bm_v_metal, (sx, sc_y_south, 0.015), 90.0 + jitter, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    # West Guanghe St SW segment (78/88 廣和街, 14 scooters nose-in!)
    for i in range(14):
        sy_sw = -47.2 - i * 1.35
        jitter = ((i * 7) % 9 - 4) * 1.8
        _add_scooter(scooter_bms[(i + 1) % len(scooter_bms)], bm_v_tire, bm_v_metal, (mg.curb_x(sy_sw) - 1.25, sy_sw, 0.015), -8.5 + jitter, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    # East Wuquan St 3 scooter rows (2/9/中段A 五權街: 11 + 7 + 3 = 21 scooters nose-in facing West -X toward school!)
    for i in range(11):
        sy_e = -56.4 + i * 1.48
        jitter = ((i * 7) % 9 - 4) * 1.9
        _add_scooter(scooter_bms[i % len(scooter_bms)], bm_v_tire, bm_v_metal, (mg.east_curb_x(sy_e) + 1.25, sy_e, 0.015), 183.2 + jitter, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    for i in range(7):
        sy_e = -35.0 + i * 1.52
        jitter = ((i * 11) % 9 - 4) * 1.9
        _add_scooter(scooter_bms[(i + 2) % len(scooter_bms)], bm_v_tire, bm_v_metal, (mg.east_curb_x(sy_e) + 1.25, sy_e, 0.015), 183.2 + jitter, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    for i in range(3):
        sy_e = 13.0 + i * 1.15
        _add_scooter(scooter_bms[(i + 1) % len(scooter_bms)], bm_v_tire, bm_v_metal, (mg.east_curb_x(sy_e) + 1.25, sy_e, 0.015), 183.2, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    _add_scooter(bm_car_k, bm_v_tire, bm_v_metal, (-34.0, mg.heping_south_edge_y(-34.0) + 8.35, 0.015), hp_yaw_w, bm_plate=bm_car_w, bm_taillight=bm_car_r)
    _add_scooter(bm_car_w, bm_v_tire, bm_v_metal, (-55.0, mg.heping_south_edge_y(-55.0) + 1.85, 0.015), hp_yaw_e, bm_plate=bm_car_w, bm_taillight=bm_car_r)

    objs.append(su.create_mesh_object("Street_Cars_Silver", bm_car_s, palette["car_silver"], col))
    objs.append(su.create_mesh_object("Street_Cars_Black", bm_car_k, palette["car_black"], col))
    objs.append(su.create_mesh_object("Street_Cars_White", bm_car_w, palette["car_white"], col))
    objs.append(su.create_mesh_object("Street_Cars_Red", bm_car_r, palette["car_red"], col))
    objs.append(su.create_mesh_object("Street_Cars_Blue", bm_car_b, palette["car_blue"], col))
    objs.append(su.create_mesh_object("Street_Vehicles_Glass", bm_v_glass, palette["window_glass"], col))
    objs.append(su.create_mesh_object("Street_Vehicles_Tires", bm_v_tire, palette["tire_rubber"], col))
    objs.append(su.create_mesh_object("Street_Vehicles_Metal", bm_v_metal, palette["steel_silver"], col))

    # === 2b. 43 廣和街 YOUBIKE 2.0 STATION (12 Docking Pillars + 6 Signature White/Orange/Yellow Bicycles!) + 3A Alley Bicycle ===
    bm_yb_pil = bmesh.new()
    bm_yb_y = bmesh.new()
    bm_yb_o = bmesh.new()
    bm_yb_w = bmesh.new()
    bm_yb_t = bmesh.new()
    bm_yb_m = bmesh.new()
    yb_y = mg.SOUTH_WALL_Y - 0.78  # -70.58m on gray sidewalk right beside mosaic wall!
    for i in range(12):
        px_yb = -66.0 + i * 1.48
        gp.bm_box(bm_yb_pil, (px_yb, yb_y, 0.135 + 0.50), (0.14, 0.18, 1.00))
        gp.bm_box(bm_yb_y, (px_yb, yb_y, 0.135 + 1.02), (0.15, 0.20, 0.06))
        gp.bm_box(bm_yb_m, (px_yb, yb_y, 0.135 + 0.025), (0.24, 0.26, 0.05))
        # Dock YouBike 2.0 bicycles on alternating pillars (matching step_149 & step_151!)
        if i in (0, 2, 4, 5, 8, 10):
            _add_youbike(bm_yb_w, bm_yb_o, bm_yb_y, bm_yb_t, bm_yb_m, (px_yb + 0.35, yb_y - 0.62, 0.135), -58.0)
    # Blue-white casual bicycle parked on sidewalk next to Wuquan Ln 30 yellow grid (exact step_153 detail!)
    _add_youbike(bm_yb_w, bm_yb_m, bm_yb_t, bm_yb_t, bm_yb_m, (-21.0, mg.SOUTH_CURB_Y + 0.88, 0.135), 22.0)
    # Two bicycles parked beside 9 五權街 amber flashing warning pole (exact step_165 detail!)
    _add_youbike(bm_yb_w, bm_yb_o, bm_yb_y, bm_yb_t, bm_yb_m, (mg.east_curb_x(-35.2) - 0.82, -35.2, 0.135), 112.0)
    _add_youbike(bm_yb_w, bm_yb_m, bm_yb_t, bm_yb_t, bm_yb_m, (mg.east_curb_x(-34.6) - 1.15, -34.6, 0.135), 102.0)
    objs.append(su.create_mesh_object("Street_YouBike_Pillars", bm_yb_pil, palette["youbike_pillar"], col))
    objs.append(su.create_mesh_object("Street_YouBike_Yellow", bm_yb_y, palette["youbike_yellow"], col))
    objs.append(su.create_mesh_object("Street_YouBike_Orange", bm_yb_o, palette["youbike_orange"], col))
    objs.append(su.create_mesh_object("Street_YouBike_Frames", bm_yb_w, palette["car_white"], col))
    objs.append(su.create_mesh_object("Street_YouBike_Tires", bm_yb_t, palette["tire_rubber"], col))
    objs.append(su.create_mesh_object("Street_YouBike_Metal", bm_yb_m, palette["steel_silver"], col))

    # 3. Motorcycle bay lines, traffic signals, convex street mirror & detailed v8/v9 Street Furniture!
    bm_lines = bmesh.new()
    bm_pole = bmesh.new()
    bm_silver_pole = bmesh.new()
    bm_hazard_pole = bmesh.new()
    bm_mirror_o = bmesh.new()
    bm_mirror_c = bmesh.new()
    bm_sig_r = bmesh.new()
    bm_sig_g = bmesh.new()

    # White motorcycle parking bay lines on South Guanghe St (West row -56.2..-26.4 & East row -13.6..+4.8 ending cleanly before Gate 3!)
    for rx0, rx1, n_stalls in [(-56.2, -26.4, 20), (-13.6, 4.8, 12)]:
        gp.bm_box(bm_lines, ((rx0 + rx1) * 0.5, mg.SOUTH_CURB_Y - 2.35, 0.018), (rx1 - rx0, 0.11, 0.014))
        for k in range(n_stalls + 1):
            lx_m = rx0 + (rx1 - rx0) * k / n_stalls
            gp.bm_box(bm_lines, (lx_m, mg.SOUTH_CURB_Y - 1.25, 0.018), (0.09, 2.25, 0.014))
    # Outer longitudinal white line + 15 dividers for 78/88 廣和街 West scooter row
    mg._add_strip_along_guanghe(bm_lines, -66.2, -46.4, -2.35, -2.25, 0.010, 0.020)
    for i in range(15):
        sy_sw = -46.5 - i * 1.35
        mg._add_strip_along_guanghe(bm_lines, sy_sw - 0.045, sy_sw + 0.045, -2.32, -0.18, 0.010, 0.020)
    # East Wuquan St white motorcycle bay lines (3 rows: -57.2..-40.2, -36.0..-24.2, +12.4..+15.9!)
    for ey0, ey1, n_st in [(-57.2, -40.2, 11), (-36.0, -24.2, 8), (12.4, 15.9, 3)]:
        mg._add_strip_along_wuquan(bm_lines, ey0, ey1, 2.25, 2.35, 0.010, 0.020)
        for k in range(n_st + 1):
            sy_m = ey0 + (ey1 - ey0) * k / n_st
            mg._add_strip_along_wuquan(bm_lines, sy_m - 0.045, sy_m + 0.045, 0.16, 2.32, 0.010, 0.020)

    # === v8/v10 HIGH-DETAIL SMART PARKING PILLARS (西側 6 支 ＋ 東側五權街 5 支朝東收費柱 = 共 11 支!) ===
    bm_pil_silver = bmesh.new()
    bm_pil_dark = bmesh.new()
    bm_pil_glass = bmesh.new()
    bm_pil_front = bmesh.new()
    bm_pil_led = bmesh.new()
    for spy in (13.0, 19.2, 25.4, -12.8, -19.0, -25.4):
        spx = mg.curb_x(spy) + 0.44
        _add_smart_parking_pillar(
            bm_pil_silver, bm_pil_dark, bm_pil_glass, bm_pil_front, bm_pil_led,
            spx, spy, z0=0.135, rot_z=ang_g,
        )
    # East Wuquan St North 5 Smart Parking Pillars (aligned with bays 05..01, facing East +X toward Wuquan St!)
    ang_e_face = mg.EAST_ROT_Z + math.pi
    for spy_e in (16.5, 22.0, 27.5, 33.8, 39.8):
        spx_e = mg.east_curb_x(spy_e) - 0.42
        _add_smart_parking_pillar(
            bm_pil_silver, bm_pil_dark, bm_pil_glass, bm_pil_front, bm_pil_led,
            spx_e, spy_e, z0=0.135, rot_z=ang_e_face,
        )
    objs.append(su.create_mesh_object("Street_SmartPillars_SilverBody", bm_pil_silver, palette["pillar_silver"], col))
    objs.append(su.create_mesh_object("Street_SmartPillars_DarkTrim", bm_pil_dark, palette["metal_dark"], col))
    objs.append(su.create_mesh_object("Street_SmartPillars_Glass", bm_pil_glass, palette["pillar_black_glass"], col))
    objs.append(su.create_mesh_object("Street_SmartPillars_FrontPanel", bm_pil_front, palette["pillar_front"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Street_SmartPillars_LED", bm_pil_led, palette["pillar_led_green"], col))

    # === v8 Street Furniture: Double-Globe Corner Lamp, Granite Benches, Traffic Cones, Control Cabinet, Transformers ===
    bm_trans = bmesh.new()
    bm_globe = bmesh.new()
    bm_cone = bmesh.new()
    bm_cone_w = bmesh.new()
    bm_bench = bmesh.new()

    # 10 廣和街 NW corner planter double-globe warm bronze courtyard lamp (step_111 left!)
    gp.bm_cyl_axis(bm_pole, (-63.5, 39.8, 1.55), 0.055, 2.9, axis="Z", segments=8)
    gp.bm_box(bm_pole, (-63.5, 39.8, 2.88), (0.95, 0.08, 0.08), rot_z=math.radians(7.5))
    gp.bm_cyl_axis(bm_globe, (-63.95, 39.74, 3.16), 0.23, 0.42, axis="Z", segments=12)
    gp.bm_cyl_axis(bm_globe, (-63.05, 39.86, 3.16), 0.23, 0.42, axis="Z", segments=12)

    # Granite double-leg sidewalk stone benches (dark warm granite, NOT white tile! Exact final_step_137 & step_113 spots!)
    for by_s in (16.2, 33.8, -15.6, -22.8, -39.5, -54.5):
        bx_s = mg.curb_x(by_s) + 1.05
        gp.bm_box(bm_bench, (bx_s, by_s, 0.56), (0.50, 1.72, 0.13), rot_z=ang_g)
        gp.bm_box(bm_bench, (bx_s, by_s - 0.56, 0.31), (0.42, 0.20, 0.37), rot_z=ang_g)
        gp.bm_box(bm_bench, (bx_s, by_s + 0.56, 0.31), (0.42, 0.20, 0.37), rot_z=ang_g)

    # Two bright orange traffic cones with white reflective collars + gray utility control box (exact step_113!)
    for cy_c in (-11.1, -11.75):
        cx_c = mg.curb_x(cy_c) + 0.88
        gp.bm_cyl_p2p(bm_cone, (cx_c, cy_c, 0.135), (cx_c, cy_c, 0.82), 0.17, 0.038, segments=12)
        gp.bm_box(bm_cone, (cx_c, cy_c, 0.155), (0.34, 0.34, 0.04), rot_z=ang_g)
        gp.bm_cyl_p2p(bm_cone_w, (cx_c, cy_c, 0.48), (cx_c, cy_c, 0.62), 0.105, 0.078, segments=12)
    # Gray electrical/signal control box mounted on steel post right behind south smart pillar #1 (step_113!)
    gp.bm_cyl_axis(bm_silver_pole, (mg.curb_x(-13.1) + 1.15, -13.1, 1.25), 0.055, 2.25, axis="Z", segments=8)
    gp.bm_box(bm_trans, (mg.curb_x(-13.1) + 1.15, -13.1, 1.55), (0.36, 0.44, 0.62), rot_z=ang_g)

    # Parent Drop-off Zone Signboards on yellow-black hazard poles (West Guanghe St + East Wuquan St 05..01!)
    bm_psign = bmesh.new()
    for psy in (26.4, 11.4, -26.8):
        psx = mg.curb_x(psy) + 0.52
        gp.bm_cyl_axis(bm_hazard_pole, (psx, psy, 1.48), 0.036, 2.70, axis="Z", segments=8)
        _add_plane_uv(
            bm_psign,
            (psx - 0.06, psy + 0.26, 1.72),
            (psx - 0.06, psy - 0.26, 1.72),
            (psx - 0.06, psy - 0.26, 2.72),
            (psx - 0.06, psy + 0.26, 2.72),
        )
    # East Wuquan St Parent Drop-off Signboards facing East (+X -> UV left=-Y, right=+Y so text reads forward! step_178 & 180!)
    for psy_e in (21.2, 38.4):
        psx_e = mg.east_curb_x(psy_e) - 0.55
        gp.bm_cyl_axis(bm_hazard_pole, (psx_e, psy_e, 1.48), 0.036, 2.70, axis="Z", segments=8)
        _add_plane_uv(
            bm_psign,
            (psx_e + 0.06, psy_e - 0.26, 1.72),
            (psx_e + 0.06, psy_e + 0.26, 1.72),
            (psx_e + 0.06, psy_e + 0.26, 2.72),
            (psx_e + 0.06, psy_e - 0.26, 2.72),
        )
    objs.append(su.create_mesh_object("Street_Sign_ParentPickup", bm_psign, palette["sign_pickup"], col, auto_uv=False))

    # 88 廣和街: 3 iconic gray Taipower transformer boxes strictly ON south gray-tile sidewalk!
    for i in range(3):
        ty_b = -42.5 - i * 1.35
        gp.bm_box(bm_trans, (mg.curb_x(ty_b) + 1.45, ty_b, 0.80), (0.95, 1.05, 1.35), rot_z=ang_g)

    # East Wuquan St 6 Granite Double-Leg Stone Benches along checkerboard sidewalk (step_163..180!)
    for by_e in (-55.5, -34.2, -14.2, 11.8, 23.8, 37.2):
        bx_e = mg.east_curb_x(by_e) - 1.55
        gp.bm_box(bm_bench, (bx_e, by_e, 0.56), (0.50, 1.72, 0.13), rot_z=mg.EAST_ROT_Z)
        gp.bm_box(bm_bench, (bx_e, by_e - 0.56, 0.31), (0.42, 0.20, 0.37), rot_z=mg.EAST_ROT_Z)
        gp.bm_box(bm_bench, (bx_e, by_e + 0.56, 0.31), (0.42, 0.20, 0.37), rot_z=mg.EAST_ROT_Z)

    objs.append(su.create_mesh_object("Street_Transformers", bm_trans, palette["transformer_gray"], col))
    objs.append(su.create_mesh_object("Street_GlobeLamps", bm_globe, palette["lamp_globe"], col, smooth=True))
    objs.append(su.create_mesh_object("Street_TrafficCones", bm_cone, palette["cone_orange"], col, smooth=True))
    objs.append(su.create_mesh_object("Street_TrafficConeCollars", bm_cone_w, palette["road_white"], col, smooth=True))
    objs.append(su.create_mesh_object("Street_StoneBenches", bm_bench, palette["granite_gray"], col, uv_scale=0.8))

    # === v9 SOUTH GUANGHE ST STREET DETAILS (92 / 43 / 76 / 3A / 3B / 12 廣和街!) ===
    bm_plinth = bmesh.new()
    # 1. Iconic orange-rimmed convex traffic mirror on yellow-black hazard pole at Wuquan Ln 30 corner (exact step_153 center!)
    mx, my = -25.2, mg.SOUTH_WALL_Y - 1.30
    gp.bm_cyl_axis(bm_hazard_pole, (mx, my, 1.25), 0.048, 2.25, axis="Z", segments=8)
    gp.bm_cyl_axis(bm_silver_pole, (mx, my, 2.55), 0.042, 0.55, axis="Z", segments=8)
    gp.bm_cyl_axis(bm_mirror_o, (mx, my - 0.10, 2.55), 0.44, 0.10, axis="Y", segments=16)
    gp.bm_cyl_axis(bm_mirror_c, (mx, my - 0.15, 2.55), 0.38, 0.05, axis="Y", segments=16)

    # 2. Full row of signature slim LED street lamps with lower yellow-black hazard wraps (92 -> 43 -> 76 -> 3 -> 12 廣和街!)
    # (a) 43/92 廣和街 SW corner lamp trio (exact final_step_14.png: foreground hazard lamp on SW curved apron + short pole by green side door + PA speaker pole north!)
    _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, -81.8, -72.0, arm_yaw_deg=-130.0, pole_h=4.65)
    _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, mg.curb_x(-62.5) + 0.55, -62.5, arm_yaw_deg=-170.0, pole_h=5.2)
    gp.bm_cyl_p2p(bm_silver_pole, (mg.curb_x(-62.5) + 0.48, -62.5, 3.85), (mg.curb_x(-62.5) + 0.12, -62.7, 3.92), 0.06, 0.18, segments=10)  # PA horn
    # Slim silver pedestrian bollard lamp right next to green small door (final_step_14 left of brick portal!)
    gp.bm_cyl_axis(bm_silver_pole, (mg.wall_x(-63.2) - 0.55, -63.2, 1.65), 0.042, 3.05, axis="Z", segments=8)
    gp.bm_box(bm_pole, (mg.wall_x(-63.2) - 0.85, -63.2, 3.16), (0.62, 0.16, 0.08))
    # East corner lamp right past tactile & street sign
    _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, -70.6, -72.55, arm_yaw_deg=-90.0, pole_h=4.65)
    # (b) South wall mid & east lamps tucked along shrub strip edge (framing Gate 3 at x=5.5 & 25.2!) + SE curved corner lamp
    for lx_s in (-51.5, -36.5, -18.5, -4.5, 5.5, 25.2, 41.2, 58.2, 68.4):
        _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, lx_s, mg.SOUTH_WALL_Y - 1.32, arm_yaw_deg=-90.0, pole_h=4.65)
    _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, 74.2, -67.8, arm_yaw_deg=-25.0, pole_h=4.65)

    # 3. 3 廣和街 Gate 3 Right Assembly (exact final_step_15 order: "◀廣和街|五權街▶" pole -> Taipower w/ hazard plinth -> "五權街30巷24弄 ▶"!)
    # (a) Dual directional green street sign "◀ 廣和街 | 五權街 ▶" at x=18.4 (just east of Gate 3 right pier!)
    gw_x, gw_y = 18.4, mg.SOUTH_WALL_Y - 1.15
    gp.bm_cyl_axis(bm_silver_pole, (gw_x, gw_y, 1.55), 0.042, 2.85, axis="Z", segments=8)
    bm_gw_sign = bmesh.new()
    _add_plane_uv(bm_gw_sign, (gw_x - 0.85, gw_y - 0.06, 2.42), (gw_x + 0.85, gw_y - 0.06, 2.42), (gw_x + 0.85, gw_y - 0.06, 2.86), (gw_x - 0.85, gw_y - 0.06, 2.86))
    objs.append(su.create_mesh_object("Street_Sign_GuangheWuquanDual", bm_gw_sign, palette["sign_guanghe_wuquan"], col, auto_uv=False))

    # (b) Pale-Green Taipower Transformer Cabinet seated on Yellow-Black Hazard-Striped Plinth (x=20.6, exact final_step_15!)
    bm_tp_green = bmesh.new()
    tx_tp, ty_tp = 20.6, mg.SOUTH_WALL_Y - 0.92
    gp.bm_box(bm_hazard_pole, (tx_tp, ty_tp, 0.27), (1.42, 1.12, 0.28))  # Yellow-black striped concrete plinth!
    gp.bm_box(bm_tp_green, (tx_tp, ty_tp, 1.16), (1.30, 0.98, 1.52))     # Pale-green Taipower enclosure
    gp.bm_box(bm_pole, (tx_tp, ty_tp - 0.50, 1.16), (0.03, 0.02, 1.32))  # Door seam
    objs.append(su.create_mesh_object("Street_SouthBackGate_Taipower", bm_tp_green, palette["taipower_green"], col))

    # (c) Green street sign "五權街30巷24弄 ▶" on striped pole right next to Taipower cabinet (x=22.4!) + SW corner sign
    bm_wq_sign = bmesh.new()
    sg_x, sg_y = 22.4, mg.SOUTH_WALL_Y - 1.25
    gp.bm_cyl_axis(bm_hazard_pole, (sg_x, sg_y, 1.75), 0.042, 3.25, axis="Z", segments=8)
    _add_plane_uv(bm_wq_sign, (sg_x - 0.55, sg_y - 0.06, 2.75), (sg_x + 0.55, sg_y - 0.06, 2.75), (sg_x + 0.55, sg_y - 0.06, 3.18), (sg_x - 0.55, sg_y - 0.06, 3.18))
    # Also one small green street sign at 92 廣和街 SW corner (step_145!)
    gp.bm_cyl_axis(bm_silver_pole, (-70.2, mg.SOUTH_WALL_Y - 1.25, 1.65), 0.038, 3.05, axis="Z", segments=8)
    _add_plane_uv(bm_wq_sign, (-70.72, mg.SOUTH_WALL_Y - 1.31, 2.68), (-69.68, mg.SOUTH_WALL_Y - 1.31, 2.68), (-69.68, mg.SOUTH_WALL_Y - 1.31, 3.08), (-70.72, mg.SOUTH_WALL_Y - 1.31, 3.08))
    objs.append(su.create_mesh_object("Street_Sign_Wuquan30Ln24", bm_wq_sign, palette["sign_wuquan30"], col, auto_uv=False))

    # === v10 EAST WUQUAN ST STREET DETAILS (2 / 9 / 1 / Mid / 15 五權街 NE Corner!) ===
    # 1. 2 五權街 SE corner Children-Warning triangle + PA speaker pole (step_163!)
    tx_e2, ty_e2 = mg.east_curb_x(-58.2) - 0.55, -58.2
    gp.bm_cyl_axis(bm_silver_pole, (tx_e2, ty_e2, 2.45), 0.055, 4.65, axis="Z", segments=8)
    gp.bm_cyl_p2p(bm_silver_pole, (tx_e2 + 0.08, ty_e2, 3.85), (tx_e2 + 0.42, ty_e2 - 0.15, 3.92), 0.06, 0.18, segments=10)
    bm_e_child = bmesh.new()
    _add_plane_uv(bm_e_child, (tx_e2 - 0.38, ty_e2 - 0.08, 2.35), (tx_e2 + 0.38, ty_e2 - 0.08, 2.35), (tx_e2 + 0.38, ty_e2 - 0.08, 3.08), (tx_e2 - 0.38, ty_e2 - 0.08, 3.08))
    objs.append(su.create_mesh_object("Street_East_ChildrenWarning", bm_e_child, palette["sign_children"], col, auto_uv=False))

    # 2. 9 五權街 Single-Lens Amber Flashing Warning Beacon + Gray Control Box on hazard pole (exact step_165!)
    fx_e, fy_e = mg.east_curb_x(-35.8) - 0.52, -35.8
    gp.bm_cyl_axis(bm_hazard_pole, (fx_e, fy_e, 1.05), 0.048, 1.85, axis="Z", segments=8)
    gp.bm_cyl_axis(bm_silver_pole, (fx_e, fy_e, 2.65), 0.042, 1.45, axis="Z", segments=8)
    gp.bm_box(bm_pole, (fx_e, fy_e, 3.35), (0.34, 0.28, 0.42))
    bm_amber = bmesh.new()
    gp.bm_cyl_axis(bm_amber, (fx_e, fy_e - 0.15, 3.35), 0.125, 0.05, axis="Y", segments=12)
    objs.append(su.create_mesh_object("Street_East_AmberBeacon", bm_amber, palette["amber_flash"], col))
    bm_e_ctrl = bmesh.new()
    gp.bm_box(bm_e_ctrl, (fx_e - 0.18, fy_e + 0.25, 1.45), (0.34, 0.40, 0.55))
    objs.append(su.create_mesh_object("Street_East_ControlBox", bm_e_ctrl, palette["transformer_gray"], col))

    # 3. 1 五權街 Iconic Cluster: Dark-Green Transformer + Utility Pole + Convex Mirror + RED FIRE HYDRANT + Alley Signs (step_170!)
    bm_e_dgreen = bmesh.new()
    gx_b, gy_b = mg.east_curb_x(-23.2) - 1.15, -23.2
    gp.bm_box(bm_e_dgreen, (gx_b, gy_b, 0.92), (0.95, 1.25, 1.56), rot_z=mg.EAST_ROT_Z)
    gp.bm_cyl_axis(bm_plinth, (mg.east_curb_x(-22.2) - 0.62, -22.2, 3.2), 0.16, 6.2, axis="Z", segments=10)  # Utility pole
    objs.append(su.create_mesh_object("Street_East_DarkGreenBox", bm_e_dgreen, palette["box_darkgreen"], col))

    # Convex traffic mirror at 1 五權街 (y=-11.6)
    mx_e, my_e = mg.east_curb_x(-11.6) - 0.55, -11.6
    gp.bm_cyl_axis(bm_hazard_pole, (mx_e, my_e, 1.30), 0.045, 2.35, axis="Z", segments=8)
    gp.bm_cyl_axis(bm_mirror_o, (mx_e + 0.10, my_e, 2.55), 0.42, 0.10, axis="X", segments=16)
    gp.bm_cyl_axis(bm_mirror_c, (mx_e + 0.15, my_e, 2.55), 0.36, 0.05, axis="X", segments=16)

    # Iconic RED FIRE HYDRANT right beside curb (y=-9.6, exact step_170 detail!)
    bm_hyd = bmesh.new()
    hx_e, hy_e = mg.east_curb_x(-9.6) - 0.48, -9.6
    gp.bm_cyl_axis(bm_hyd, (hx_e, hy_e, 0.135 + 0.42), 0.115, 0.84, axis="Z", segments=12)
    gp.bm_cyl_axis(bm_hyd, (hx_e, hy_e, 0.135 + 0.86), 0.145, 0.12, axis="Z", segments=12)
    gp.bm_cyl_axis(bm_hyd, (hx_e, hy_e, 0.135 + 0.58), 0.068, 0.34, axis="Y", segments=10)
    gp.bm_cyl_axis(bm_hyd, (hx_e + 0.12, hy_e, 0.135 + 0.58), 0.062, 0.12, axis="X", segments=10)
    objs.append(su.create_mesh_object("Street_East_FireHydrant", bm_hyd, palette["hydrant_red"], col, smooth=True))

    # Dual Green Alley Sign ("← 和平路174巷1弄 / 壽德街 →") + PA speaker at y=-8.4 (step_170!)
    ax_s, ay_s = mg.east_curb_x(-8.4) - 0.55, -8.4
    gp.bm_cyl_axis(bm_silver_pole, (ax_s, ay_s, 2.65), 0.055, 5.1, axis="Z", segments=8)
    bm_e_alley = bmesh.new()
    _add_plane_uv(bm_e_alley, (ax_s - 0.62, ay_s - 0.08, 2.65), (ax_s + 0.62, ay_s - 0.08, 2.65), (ax_s + 0.62, ay_s - 0.08, 3.38), (ax_s - 0.62, ay_s - 0.08, 3.38))
    objs.append(su.create_mesh_object("Street_East_AlleySign", bm_e_alley, palette["sign_wuquan_alley"], col, auto_uv=False))

    # 4. East Wuquan St Slim Street Lamps facing East (+X) along sidewalk
    for ly_e in (-45.5, -27.5, -4.5, 14.5, 31.5):
        _add_south_hazard_lamp(bm_silver_pole, bm_hazard_pole, bm_pole, bm_plinth, mg.east_curb_x(ly_e) - 0.52, ly_e, arm_yaw_deg=3.0, pole_h=5.2)

    # 5. 15 五權街 NE GRAND CURVED CORNER L-SHAPED TRAFFIC SIGNAL GANTRY + STREET SIGNS (final_step_182 hero!)
    nx_s, ny_s = 68.8, 51.4
    gp.bm_box(bm_plinth, (nx_s, ny_s, 0.24), (0.62, 0.62, 0.22))
    gp.bm_cyl_axis(bm_silver_pole, (nx_s, ny_s, 3.25), 0.095, 6.2, axis="Z", segments=10)
    # Signal arm extending NW along Heping Rd approach
    gp.bm_cyl_p2p(bm_silver_pole, (nx_s, ny_s, 5.85), (nx_s - 4.6, ny_s + 0.6, 5.85), 0.07, 0.055, segments=8)
    gp.bm_box(bm_pole, (nx_s - 3.2, ny_s + 0.42, 5.65), (1.15, 0.36, 0.42), rot_z=math.radians(-7.5))
    gp.bm_cyl_axis(bm_sig_r, (nx_s - 3.46, ny_s + 0.62, 5.65), 0.11, 0.06, axis="Y", segments=10)
    gp.bm_cyl_axis(bm_sig_g, (nx_s - 2.94, ny_s + 0.62, 5.65), 0.11, 0.06, axis="Y", segments=10)
    # Pedestrian signal box facing NE intersection
    gp.bm_box(bm_pole, (nx_s + 0.22, ny_s + 0.18, 2.45), (0.28, 0.32, 0.54))
    gp.bm_cyl_axis(bm_sig_g, (nx_s + 0.37, ny_s + 0.18, 2.34), 0.07, 0.04, axis="X", segments=8)
    gp.bm_cyl_axis(bm_sig_r, (nx_s + 0.37, ny_s + 0.18, 2.56), 0.07, 0.04, axis="X", segments=8)
    # Vertical green "▲ 和平路 Heping Rd." + Horizontal green "五權街 Wuquan St." facing NE viewer (+X/+Y -> left=+X, right=-X!)
    bm_ne_hp = bmesh.new()
    _add_plane_uv(bm_ne_hp, (nx_s + 0.28, ny_s + 0.22, 3.05), (nx_s - 0.26, ny_s + 0.22, 3.05), (nx_s - 0.26, ny_s + 0.22, 4.45), (nx_s + 0.28, ny_s + 0.22, 4.45))
    objs.append(su.create_mesh_object("Street_NE_SignHepingVert", bm_ne_hp, palette["sign_heping_vert"], col, auto_uv=False))

    bm_ne_wq = bmesh.new()
    _add_plane_uv(bm_ne_wq, (nx_s + 0.65, ny_s - 0.35, 2.55), (nx_s + 0.65, ny_s + 0.55, 2.55), (nx_s + 0.65, ny_s + 0.55, 2.95), (nx_s + 0.65, ny_s - 0.35, 2.95))
    objs.append(su.create_mesh_object("Street_NE_SignWuquanHoriz", bm_ne_wq, palette["sign_wuquan_horiz"], col, auto_uv=False))

    # === 10 廣和街 NW Corner Dual Galvanized Traffic Signal & Street-Sign Pole Assembly (exact step_111!) ===
    tx1, ty1 = mg.curb_x(35.8) + 0.72, 35.8
    gp.bm_box(bm_plinth, (tx1, ty1, 0.24), (0.62, 0.62, 0.22), rot_z=ang_g)
    objs.append(su.create_mesh_object("Street_SignalPlinth", bm_plinth, palette["curb_concrete"], col))
    gp.bm_cyl_axis(bm_silver_pole, (tx1, ty1, 3.25), 0.095, 6.2, axis="Z", segments=10)
    # Curved cantilevered signal arm pointing NW over intersection
    arm_ang = math.radians(112.0)
    ca2, sa2 = math.cos(arm_ang), math.sin(arm_ang)
    gp.bm_cyl_p2p(bm_silver_pole, (tx1, ty1, 5.85), (tx1 + ca2 * 4.8, ty1 + sa2 * 4.8, 5.85), 0.07, 0.055, segments=8)
    sx_box, sy_box = tx1 + ca2 * 3.4, ty1 + sa2 * 3.4
    gp.bm_box(bm_pole, (sx_box, sy_box, 5.65), (1.15, 0.36, 0.42), rot_z=arm_ang)
    gp.bm_cyl_axis(bm_sig_r, (sx_box - ca2 * 0.26, sy_box - sa2 * 0.26 - 0.19, 5.65), 0.11, 0.06, axis="Y", segments=10)
    gp.bm_cyl_axis(bm_sig_g, (sx_box + ca2 * 0.26, sy_box + sa2 * 0.26 - 0.19, 5.65), 0.11, 0.06, axis="Y", segments=10)
    # Pedestrian small green/red signal box on main pole (step_111 right!)
    gp.bm_box(bm_pole, (tx1 - 0.22, ty1 + 0.10, 2.35), (0.28, 0.34, 0.54))
    gp.bm_cyl_axis(bm_sig_g, (tx1 - 0.37, ty1 + 0.10, 2.24), 0.07, 0.04, axis="X", segments=8)
    gp.bm_cyl_axis(bm_sig_r, (tx1 - 0.37, ty1 + 0.10, 2.46), 0.07, 0.04, axis="X", segments=8)

    # Vertical green "廣和街 Guanghe St." sign on outer pole + Horizontal green "和平路 Heping Rd." sign on arm!
    bm_rsign = bmesh.new()
    _add_plane_uv(bm_rsign, (tx1 - 0.14, ty1 + 0.30, 3.05), (tx1 - 0.14, ty1 - 0.24, 3.05), (tx1 - 0.14, ty1 - 0.24, 4.45), (tx1 - 0.14, ty1 + 0.30, 4.45))
    objs.append(su.create_mesh_object("Street_Sign_GuangheSt", bm_rsign, palette["roadsign_guanghe"], col, auto_uv=False))

    bm_hsign = bmesh.new()
    # Facing NW intersection viewer -> viewer left is East/North (-0.15, +1.65), viewer right is West/South (-1.35, +1.10) so "和 平 路" reads forward!
    _add_plane_uv(bm_hsign, (tx1 - 0.15, ty1 + 1.65, 5.25), (tx1 - 1.35, ty1 + 1.10, 5.25), (tx1 - 1.35, ty1 + 1.10, 5.80), (tx1 - 0.15, ty1 + 1.65, 5.80))
    objs.append(su.create_mesh_object("Street_Sign_HepingRd", bm_hsign, palette["roadsign_heping"], col, auto_uv=False))

    # Secondary inner signpost with yellow triangle "當心兒童" sign (exact step_111 & final_step_137!)
    tx2, ty2 = mg.curb_x(36.7) + 1.35, 36.7
    gp.bm_cyl_axis(bm_silver_pole, (tx2, ty2, 2.20), 0.048, 4.15, axis="Z", segments=8)
    bm_csign = bmesh.new()
    _add_plane_uv(bm_csign, (tx2 - 0.08, ty2 + 0.32, 2.28), (tx2 - 0.08, ty2 - 0.32, 2.28), (tx2 - 0.08, ty2 - 0.32, 2.90), (tx2 - 0.08, ty2 + 0.32, 2.90))
    objs.append(su.create_mesh_object("Street_Sign_ChildrenWarning", bm_csign, palette["sign_children"], col, auto_uv=False))

    # === v11 NORTH HEPING RD STREET FURNITURE (166 / 147 A / 147 B / 129 A-D 和平路!) ===
    hp_ang = mg.HEPING_ROT_Z
    ca_h, sa_h = math.cos(hp_ang), math.sin(hp_ang)

    # 1. 166 和平路 Chongqing Elementary Bus Shelter (4 Navy Steel Pillars + Roof Canopy + Bench + Glowing Orange LED Board! step_2!)
    bm_sh_navy = bmesh.new()
    bm_sh_roof = bmesh.new()
    bm_sh_led = bmesh.new()
    sh_cx = 45.2
    sh_cy = mg.heping_south_edge_y(sh_cx) - 0.96
    sh_z0 = 0.130

    def sh_loc(lx: float, ly: float, lz: float) -> tuple[float, float, float]:
        return (sh_cx + lx * ca_h - ly * sa_h, sh_cy + lx * sa_h + ly * ca_h, sh_z0 + lz)

    # 4 Navy steel columns (2 front near road with yellow-black hazard wraps, 2 rear near chain-link fence)
    for lx_p in (-2.75, 2.75):
        gp.bm_box(bm_sh_navy, sh_loc(lx_p, -0.52, 1.28), (0.14, 0.14, 2.56), rot_z=hp_ang)
        gp.bm_box(bm_sh_navy, sh_loc(lx_p, +0.52, 1.28), (0.14, 0.14, 2.56), rot_z=hp_ang)
        # Yellow-black reflective hazard wrap on road-facing front columns (step_2!)
        gp.bm_box(bm_hazard_pole, sh_loc(lx_p, +0.52, 1.12), (0.16, 0.16, 0.95), rot_z=hp_ang)
    # Cross top frame beams + rear glass/frame backrest + bench inside shelter
    gp.bm_box(bm_sh_navy, sh_loc(0.0, +0.52, 2.48), (5.8, 0.12, 0.14), rot_z=hp_ang)
    gp.bm_box(bm_sh_navy, sh_loc(0.0, -0.52, 2.42), (5.8, 0.12, 0.14), rot_z=hp_ang)
    gp.bm_box(bm_sh_navy, sh_loc(0.0, -0.34, 0.44), (4.2, 0.42, 0.08), rot_z=hp_ang)
    for bx_leg in (-1.65, 0.0, 1.65):
        gp.bm_box(bm_sh_navy, sh_loc(bx_leg, -0.34, 0.22), (0.09, 0.36, 0.44), rot_z=hp_ang)
    # Sloped light-gray overhanging shelter roof canopy
    gp.bm_box(bm_sh_roof, sh_loc(0.0, 0.05, 2.64), (6.5, 1.68, 0.13), rot_x=math.radians(4.5), rot_z=hp_ang)
    # Dual-sided Hanging Electronic LED Bus Route Signboard tucked cleanly inside East bay of shelter (unobstructed by lamp!)
    gp.bm_box(bm_pole, sh_loc(2.10, 0.0, 2.15), (0.14, 1.18, 0.46), rot_z=hp_ang)
    _add_plane_uv(bm_sh_led, sh_loc(2.18, -0.55, 1.94), sh_loc(2.18, +0.55, 1.94), sh_loc(2.18, +0.55, 2.36), sh_loc(2.18, -0.55, 2.36))
    _add_plane_uv(bm_sh_led, sh_loc(2.02, +0.55, 1.94), sh_loc(2.02, -0.55, 1.94), sh_loc(2.02, -0.55, 2.36), sh_loc(2.02, +0.55, 2.36))
    objs.append(su.create_mesh_object("Street_Heping_BusShelterNavy", bm_sh_navy, palette["shelter_navy"], col))
    objs.append(su.create_mesh_object("Street_Heping_BusShelterRoof", bm_sh_roof, palette["shed_roof_gray"], col))
    objs.append(su.create_mesh_object("Street_Heping_BusShelterLED", bm_sh_led, palette["bus_led_board"], col, auto_uv=False))

    # 2. 166 和平路 NE Corner Iconic Red Fire Hydrant (step_2 bottom-left!)
    bm_n_hyd = bmesh.new()
    hx_n, hy_n = 59.35, mg.heping_south_edge_y(59.35) - 0.62
    gp.bm_cyl_axis(bm_n_hyd, (hx_n, hy_n, 0.130 + 0.42), 0.115, 0.84, axis="Z", segments=12)
    gp.bm_cyl_axis(bm_n_hyd, (hx_n, hy_n, 0.130 + 0.86), 0.145, 0.12, axis="Z", segments=12)
    gp.bm_cyl_axis(bm_n_hyd, (hx_n, hy_n, 0.130 + 0.58), 0.068, 0.34, axis="X", segments=10)
    gp.bm_cyl_axis(bm_n_hyd, (hx_n, hy_n + 0.12, 0.130 + 0.58), 0.062, 0.12, axis="Y", segments=10)
    objs.append(su.create_mesh_object("Street_Heping_FireHydrant", bm_n_hyd, palette["hydrant_red"], col, smooth=True))

    # 3. 166 / 147 和平路 Row of 12 Yellow-Black Inverted-U Steel Pipe Bollards along Track Sidewalk (east of 147 B gate x=10.8!)
    bm_ubol_y = bmesh.new()
    bm_ubol_k = bmesh.new()
    ubol_xs = [57.2, 54.2, 51.2, 39.2, 36.2, 33.2, 30.2, 27.2, 24.2, 20.6, 16.8, 12.8]
    for ux in ubol_xs:
        uy = mg.heping_south_edge_y(ux) - 0.46
        uz = 0.130
        hw_u = 0.54
        # Left & right vertical legs (lower black base + upper yellow)
        for sgn in (-1.0, 1.0):
            lx_u = ux + sgn * hw_u * ca_h
            ly_u = uy + sgn * hw_u * sa_h
            gp.bm_cyl_axis(bm_ubol_k, (lx_u, ly_u, uz + 0.18), 0.036, 0.36, axis="Z", segments=8)
            gp.bm_cyl_axis(bm_ubol_y, (lx_u, ly_u, uz + 0.52), 0.036, 0.34, axis="Z", segments=8)
        # Segmented alternating yellow-black horizontal top bar (5 crisp bands!)
        for bi in range(5):
            t0 = -1.0 + 2.0 * (bi / 5.0)
            t1 = -1.0 + 2.0 * ((bi + 1) / 5.0)
            p0 = (ux + t0 * hw_u * ca_h, uy + t0 * hw_u * sa_h, uz + 0.69)
            p1 = (ux + t1 * hw_u * ca_h, uy + t1 * hw_u * sa_h, uz + 0.69)
            gp.bm_cyl_p2p(bm_ubol_y if bi % 2 == 0 else bm_ubol_k, p0, p1, 0.036, 0.036, segments=8)
    objs.append(su.create_mesh_object("Street_Heping_UBollardsYellow", bm_ubol_y, palette["road_yellow"], col))
    objs.append(su.create_mesh_object("Street_Heping_UBollardsBlack", bm_ubol_k, palette["metal_dark"], col))

    # 4. 147 和平路 Silver Double-Rail Metal Guardrails opening cleanly at West 3-Tone Shutter Green Ramp (x=-3.9..+0.25! step_27/31!)
    for gx_r in (-14.2, -12.0, -9.8, -7.6, -5.2, 1.5, 4.2):
        gy_r = mg.heping_south_edge_y(gx_r) - 0.36
        # Left & right vertical posts + top & lower horizontal bars + 4 slim inner pickets
        for sgn in (-0.90, 0.90):
            gp.bm_cyl_axis(bm_silver_pole, (gx_r + sgn * ca_h, gy_r + sgn * sa_h, 0.48), 0.030, 0.86, axis="Z", segments=8)
        for rz_g in (0.34, 0.86):
            p0 = (gx_r - 0.90 * ca_h, gy_r - 0.90 * sa_h, rz_g)
            p1 = (gx_r + 0.90 * ca_h, gy_r + 0.90 * sa_h, rz_g)
            gp.bm_cyl_p2p(bm_silver_pole, p0, p1, 0.026, 0.026, segments=6)
        for pk in (-0.52, -0.17, 0.17, 0.52):
            gp.bm_cyl_axis(bm_silver_pole, (gx_r + pk * ca_h, gy_r + pk * sa_h, 0.60), 0.014, 0.52, axis="Z", segments=6)

    # 5. Signature Heping Rd Sky-Blue Lower Sleeve + White Upper Shaft Street Lamps (aligned w/ step_6 & step_29!)
    bm_hp_blue = bmesh.new()
    bm_hp_white = bmesh.new()
    for lx_l, off_l, arm_dir in [
        (49.85, -0.45, +1.0), (29.2, -0.45, +1.0), (11.8, -0.45, +1.0),
        (-13.8, -0.48, +1.0), (-25.8, -0.52, +1.0), (-49.8, -0.52, +1.0),
        # Opposite north-side lamps for authentic street-corridor perspective!
        (38.0, 10.95, -1.0), (4.0, 10.95, -1.0), (-26.5, 10.95, -1.0),
    ]:
        ly_l = mg.heping_south_edge_y(lx_l) + off_l
        gp.bm_cyl_axis(bm_hp_blue, (lx_l, ly_l, 0.98), 0.092, 1.88, axis="Z", segments=10)
        gp.bm_cyl_axis(bm_hp_white, (lx_l, ly_l, 4.38), 0.056, 4.95, axis="Z", segments=10)
        gp.bm_cyl_p2p(
            bm_hp_white,
            (lx_l, ly_l, 6.68),
            (lx_l - arm_dir * sa_h * 1.45, ly_l + arm_dir * ca_h * 1.45, 6.96),
            0.038, 0.032, segments=8,
        )
        gp.bm_box(
            bm_pole,
            (lx_l - arm_dir * sa_h * 1.55, ly_l + arm_dir * ca_h * 1.55, 6.96),
            (0.24, 0.56, 0.10),
            rot_z=hp_ang,
        )
    objs.append(su.create_mesh_object("Street_Heping_LampsSkyBlue", bm_hp_blue, palette["lamp_skyblue"], col, smooth=True))
    objs.append(su.create_mesh_object("Street_Heping_LampsWhite", bm_hp_white, palette["railing_white"], col, smooth=True))

    objs.append(su.create_mesh_object("Street_MotoBayLines", bm_lines, palette["road_white"], col))
    objs.append(su.create_mesh_object("Street_SignalPoles", bm_pole, palette["metal_dark"], col))
    objs.append(su.create_mesh_object("Street_GalvPoles", bm_silver_pole, palette["steel_silver"], col))
    objs.append(su.create_mesh_object("Street_HazardPoles", bm_hazard_pole, palette["pole_hazard"], col, uv_scale=1.5))
    objs.append(su.create_mesh_object("Street_ConvexMirrorRim", bm_mirror_o, palette["mirror_orange"], col))
    objs.append(su.create_mesh_object("Street_ConvexMirrorGlass", bm_mirror_c, palette["mirror_chrome"], col))
    objs.append(su.create_mesh_object("Street_SignalRed", bm_sig_r, palette["signal_red"], col))
    objs.append(su.create_mesh_object("Street_SignalGreen", bm_sig_g, palette["signal_green"], col))

    return objs


def build_building_signs_and_room_plaques(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """加裝四棟校舍醒目棟別名牌、走廊懸掛式教室門牌與樓梯間 1F–5F 樓層指示牌。"""
    col = "Campus_Signage"
    objs: List[bpy.types.Object] = []

    # 1. Prominent Building Name Signs (Guanghe sign moved cleanly off 3F banner onto east courtyard face + 2F north clean wall!)
    bm_s_gh = bmesh.new()
    _add_plane_uv(bm_s_gh, (-31.32, -2.6, 17.5), (-31.32, 2.6, 17.5), (-31.32, 2.6, 19.3), (-31.32, -2.6, 19.3))
    _add_plane_uv(bm_s_gh, (-53.72, 10.6, 4.7), (-53.72, 6.2, 4.7), (-53.72, 6.2, 6.0), (-53.72, 10.6, 6.0))
    objs.append(su.create_mesh_object("Bldg_Guanghe_NameSign", bm_s_gh, palette["sign_guanghe"], "Bldg_Guanghe", auto_uv=False))

    # Heping Bldg (south courtyard face + north Heping Rd face)
    bm_s_hp = bmesh.new()
    _add_plane_uv(bm_s_hp, (-36.5, 25.32, 17.5), (-30.5, 25.32, 17.5), (-30.5, 25.32, 19.3), (-36.5, 25.32, 19.3))
    _add_plane_uv(bm_s_hp, (-30.5, 39.20, 17.5), (-36.5, 39.20, 17.5), (-36.5, 39.20, 19.3), (-30.5, 39.20, 19.3))
    objs.append(su.create_mesh_object("Bldg_Heping_NameSign", bm_s_hp, palette["sign_heping"], "Bldg_Heping", auto_uv=False))

    # Wuquan Bldg (west courtyard face only — exact 9 & 2 五權街 street views confirm NO giant green roof sign on east track facade!)
    bm_s_wq = bmesh.new()
    _add_plane_uv(bm_s_wq, (-7.20, -8.5, 17.5), (-7.20, -15.5, 17.5), (-7.20, -15.5, 19.5), (-7.20, -8.5, 19.5))
    objs.append(su.create_mesh_object("Bldg_Wuquan_NameSign", bm_s_wq, palette["sign_wuquan"], "Bldg_Wuquan", auto_uv=False))

    # Chongqing Bldg (north courtyard face + south basketball court face)
    bm_s_cq = bmesh.new()
    _add_plane_uv(bm_s_cq, (-47.0, -43.20, 17.5), (-40.0, -43.20, 17.5), (-40.0, -43.20, 19.5), (-47.0, -43.20, 19.5))
    _add_plane_uv(bm_s_cq, (-40.0, -29.30, 17.5), (-47.0, -29.30, 17.5), (-47.0, -29.30, 19.5), (-40.0, -29.30, 19.5))
    objs.append(su.create_mesh_object("Bldg_Chongqing_NameSign", bm_s_cq, palette["sign_chongqing"], "Bldg_Chongqing", auto_uv=False))

    # 2. v12.2 Dual-Sided Solid 115 Academic Year Real-Class Hanging Corridor Plaques (ZERO mirrored text from either side!)
    import json

    atlas_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures", "room_plaques_atlas_map.json")
    atlas_entries = {}
    atlas_cols, atlas_rows = 8, 16
    if os.path.exists(atlas_map_path):
        with open(atlas_map_path, "r", encoding="utf-8") as af:
            adata = json.load(af)
            atlas_cols = adata.get("cols", 8)
            atlas_rows = adata.get("rows", 16)
            atlas_entries = adata.get("entries", {})

    def _add_dual_plaque(
        bm_p: bmesh.types.BMesh,
        bm_b: bmesh.types.BMesh,
        cx: float,
        cy: float,
        cz: float,
        face_axis: str,
        col_i: int,
        row_i: int,
    ) -> None:
        """建立實心雙面走廊懸吊門牌（銀灰金屬板芯＋頂部吊桿＋正反兩面獨立正向朝外 UV，無論從走廊哪端看皆 100% 正字！）。"""
        hw, hh = 0.45, 0.22  # 0.90m x 0.44m crisp readable plaque
        off = 0.022
        pad_u, pad_v = 0.010, 0.014
        u0 = (col_i + pad_u) / atlas_cols
        u1 = (col_i + 1.0 - pad_u) / atlas_cols
        v0 = 1.0 - (row_i + 1.0 - pad_v) / atlas_rows  # PIL bottom -> OpenGL v_bot
        v1 = 1.0 - (row_i + pad_v) / atlas_rows        # PIL top -> OpenGL v_top

        if face_axis == "X":
            # Lies in Y-Z plane (perpendicular to E-W corridor), faces +X (east) and -X (west)
            gp.bm_box(bm_b, (cx, cy, cz), (0.036, hw * 2.0 + 0.02, hh * 2.0 + 0.02))
            gp.bm_box(bm_b, (cx, cy, cz + hh + 0.14), (0.04, 0.56, 0.28))
            # +X face (viewer from east looking west -> left=-Y, right=+Y)
            _add_plane_uv_rect(
                bm_p,
                (cx + off, cy - hw, cz - hh), (cx + off, cy + hw, cz - hh),
                (cx + off, cy + hw, cz + hh), (cx + off, cy - hw, cz + hh),
                u0, v0, u1, v1,
            )
            # -X face (viewer from west looking east -> left=+Y, right=-Y)
            _add_plane_uv_rect(
                bm_p,
                (cx - off, cy + hw, cz - hh), (cx - off, cy - hw, cz - hh),
                (cx - off, cy - hw, cz + hh), (cx - off, cy + hw, cz + hh),
                u0, v0, u1, v1,
            )
        else:
            # Lies in X-Z plane (perpendicular to N-S corridor), faces -Y (south) and +Y (north)
            gp.bm_box(bm_b, (cx, cy, cz), (hw * 2.0 + 0.02, 0.036, hh * 2.0 + 0.02))
            gp.bm_box(bm_b, (cx, cy, cz + hh + 0.14), (0.56, 0.04, 0.28))
            # -Y face (viewer from south looking north -> left=-X, right=+X)
            _add_plane_uv_rect(
                bm_p,
                (cx - hw, cy - off, cz - hh), (cx + hw, cy - off, cz - hh),
                (cx + hw, cy - off, cz + hh), (cx - hw, cy - off, cz + hh),
                u0, v0, u1, v1,
            )
            # +Y face (viewer from north looking south -> left=+X, right=-X)
            _add_plane_uv_rect(
                bm_p,
                (cx + hw, cy + off, cz - hh), (cx - hw, cy + off, cz - hh),
                (cx - hw, cy + off, cz + hh), (cx + hw, cy + off, cz + hh),
                u0, v0, u1, v1,
            )

    bm_plaques = bmesh.new()
    bm_dirs = bmesh.new()
    bm_brackets = bmesh.new()

    for bcfg in spec["buildings"]:
        bid = bcfg["id"]
        x0, x1 = bcfg["x_min"], bcfg["x_max"]
        y0, y1 = bcfg["y_min"], bcfg["y_max"]
        wx, wy = x1 - x0, y1 - y0
        along_x = wx >= wy
        corridor_sides = set(bcfg.get("corridor_sides", []))
        h1, hu = bcfg["ground_floor_h"], bcfg["upper_floor_h"]

        # Place real 115 classroom plaques along each building's corridor(s) at every room's exact location!
        for r_idx, rm in enumerate(bcfg.get("rooms_115_detailed", [])):
            rname = rm.get("name", "")
            if "穿堂" in rname or "天橋" in rname:
                continue
            entry = atlas_entries.get(f"{bid}:{r_idx}")
            if not entry:
                continue
            fl_num = int(rm["floor"][0]) if rm.get("floor", "")[:1].isdigit() else 1
            zf = 0.0 if fl_num == 1 else (h1 + (fl_num - 2) * hu)
            fh = h1 if fl_num == 1 else hu
            pz = zf + fh - 0.68
            rx, ry, _ = rm["pos"]

            if bid == "Bldg_Guanghe":
                # Guanghe east courtyard corridor (3F-5F) + 1F/2F inner breezeway wing flanks
                py_clamped = max(y0 + 1.4, min(y1 - 1.4, ry))
                if fl_num >= 3:
                    _add_dual_plaque(bm_plaques, bm_brackets, x1 - 1.25, py_clamped, pz, "Y", entry["col"], entry["row"])
                else:
                    _add_dual_plaque(bm_plaques, bm_brackets, x0 + 3.4, py_clamped, pz, "Y", entry["col"], entry["row"])
            elif along_x:
                px_clamped = max(x0 + 2.2, min(x1 - 2.2, rx))
                for side in corridor_sides:
                    if side == "north":
                        _add_dual_plaque(bm_plaques, bm_brackets, px_clamped, y1 - 1.25, pz, "X", entry["col"], entry["row"])
                    elif side == "south":
                        _add_dual_plaque(bm_plaques, bm_brackets, px_clamped, y0 + 1.25, pz, "X", entry["col"], entry["row"])
            else:
                py_clamped = max(y0 + 2.2, min(y1 - 2.2, ry))
                for side in corridor_sides:
                    if side == "east":
                        # v12.5 Wuquan Bldg south wing (y < -25.8) & 1F east facade have NO open east corridor (flush windows/stairs/ramps)
                        if bid == "Bldg_Wuquan" and (py_clamped < -25.8 or fl_num == 1):
                            continue
                        _add_dual_plaque(bm_plaques, bm_brackets, x1 - 1.25, py_clamped, pz, "Y", entry["col"], entry["row"])
                    elif side == "west":
                        _add_dual_plaque(bm_plaques, bm_brackets, x0 + 1.25, py_clamped, pz, "Y", entry["col"], entry["row"])

        # Ground floor stairwell Floor Directory boards (outward-facing single-sided UV, zero mirroring!)
        if bcfg["style"] == "salmon_corridor":
            bays = bcfg["bays"]
            stairs = set(bcfg.get("stair_bays", []))
            span = wx if along_x else wy
            bay_len = span / bays
            for b in stairs:
                if along_x:
                    dx = x0 + (b + 0.5) * bay_len
                    if "south" in corridor_sides:
                        dy = y0 + 0.36
                        gp.bm_box(bm_brackets, (dx, dy + 0.03, 1.75), (0.86, 0.04, 1.22))
                        _add_plane_uv(bm_dirs, (dx - 0.42, dy, 1.15), (dx + 0.42, dy, 1.15), (dx + 0.42, dy, 2.35), (dx - 0.42, dy, 2.35))
                    elif "north" in corridor_sides:
                        dy = y1 - 0.36
                        gp.bm_box(bm_brackets, (dx, dy - 0.03, 1.75), (0.86, 0.04, 1.22))
                        _add_plane_uv(bm_dirs, (dx + 0.42, dy, 1.15), (dx - 0.42, dy, 1.15), (dx - 0.42, dy, 2.35), (dx + 0.42, dy, 2.35))
                else:
                    dy = y0 + (b + 0.5) * bay_len
                    # Mount on west courtyard corridor wall cleanly so east facade stairs/solid walls remain unblocked!
                    dx = x0 + 0.36
                    gp.bm_box(bm_brackets, (dx + 0.03, dy, 1.75), (0.04, 0.86, 1.22))
                    _add_plane_uv(bm_dirs, (dx, dy + 0.42, 1.15), (dx, dy - 0.42, 1.15), (dx, dy - 0.42, 2.35), (dx, dy + 0.42, 2.35))

    objs.append(su.create_mesh_object("Campus_CorridorRoomPlaques", bm_plaques, palette["room_plaque_atlas"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Campus_FloorDirectories", bm_dirs, palette["floor_dir"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Campus_PlaqueBrackets", bm_brackets, palette["steel_silver"], col))
    return objs
