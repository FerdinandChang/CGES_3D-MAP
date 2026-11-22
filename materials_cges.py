"""新北市板橋區重慶國小 3D 場景材質庫（含 Normal Map 凹凸貼圖、真實玻璃反光與戶外日光設定）。"""
import math
import os
from typing import Dict, Optional, Sequence, Tuple

import bpy
import studio_utils as su

TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
REFS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs")


def _make_pbr(
    name: str,
    rgba: Tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.55,
    emission: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    emission_strength: float = 0.0,
    double_sided: bool = False,
) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_backface_culling = not (double_sided or rgba[3] < 0.99)
    bsdf = su.get_principled_bsdf(mat)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if rgba[3] < 0.99 and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = rgba[3]
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
        if emission_strength > 0.0 and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def _make_tex_pbr(
    name: str,
    tex_path: str,
    nrm_path: Optional[str] = None,
    normal_strength: float = 0.65,
    metallic: float = 0.0,
    roughness: float = 0.65,
    alpha: float = 1.0,
    double_sided: bool = False,
    emission_strength: float = 0.0,
    use_tex_alpha: bool = False,
) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_backface_culling = not (double_sided or alpha < 0.99 or use_tex_alpha)
    nt = su.ensure_material_nodes(mat)
    bsdf = su.get_principled_bsdf(mat)
    if bsdf:
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if alpha < 0.99 and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
        if os.path.exists(tex_path):
            img = bpy.data.images.load(tex_path, check_existing=True)
            tex_node = nt.nodes.new("ShaderNodeTexImage")
            tex_node.image = img
            tex_node.location = (-420, 260)
            nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
            if use_tex_alpha or alpha < 0.99 or tex_path.endswith("chainlink_green.png"):
                if "Alpha" in bsdf.inputs:
                    nt.links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
                    if hasattr(mat, "surface_render_method"):
                        mat.surface_render_method = "BLENDED"
            if emission_strength > 0.0 and "Emission Color" in bsdf.inputs:
                nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Emission Color"])
                bsdf.inputs["Emission Strength"].default_value = emission_strength
        if nrm_path and os.path.exists(nrm_path):
            nimg = bpy.data.images.load(nrm_path, check_existing=True)
            try:
                nimg.colorspace_settings.name = "Non-Color"
            except Exception:
                pass
            ntex = nt.nodes.new("ShaderNodeTexImage")
            ntex.image = nimg
            ntex.location = (-520, -140)
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = normal_strength
            nmap.location = (-220, -140)
            nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_palette() -> Dict[str, bpy.types.Material]:
    t = lambda fn: os.path.join(TEX_DIR, fn)
    return {
        # 外牆磁磚（含 Normal Map 凹凸細節）
        "wall_guanghe": _make_tex_pbr("CGES_Wall_Guanghe", t("tex_wall_guanghe.png"), t("tex_wall_guanghe_nrm.png"), 0.55, roughness=0.58),
        "wall_brick_red": _make_tex_pbr("CGES_Wall_BrickRed", t("tex_wall_brick_red.png"), t("tex_wall_brick_red_nrm.png"), 0.72, roughness=0.66),
        "wall_salmon": _make_tex_pbr("CGES_Wall_Salmon", t("tex_wall_salmon.png"), t("tex_wall_salmon_nrm.png"), 0.62, roughness=0.62),
        "wall_stone_cream": _make_tex_pbr("CGES_Wall_StoneCream", t("tex_wall_stone_cream.png"), t("tex_wall_stone_cream_nrm.png"), 0.68, roughness=0.72),
        "wall_south_mosaic": _make_tex_pbr("CGES_Wall_SouthMosaic", t("tex_wall_south_mosaic.png"), t("tex_wall_south_mosaic_nrm.png"), 0.85, roughness=0.74),
        # 建築構件
        "concrete_floor": _make_pbr("CGES_Concrete_Floor", (0.66, 0.65, 0.62, 1.0), roughness=0.80),
        "concrete_trim": _make_pbr("CGES_Concrete_Trim", (0.78, 0.76, 0.72, 1.0), roughness=0.72),
        "roof_gym_metal": _make_pbr("CGES_Roof_GymMetal", (0.64, 0.67, 0.69, 1.0), metallic=0.35, roughness=0.42),
        "gym_wall": _make_pbr("CGES_Gym_Wall", (0.80, 0.79, 0.76, 1.0), roughness=0.72),
        "gym_accent": _make_pbr("CGES_Gym_Accent", (0.34, 0.40, 0.48, 1.0), metallic=0.18, roughness=0.52),
        "gym_shutter": _make_tex_pbr("CGES_Gym_Shutter", t("tex_gym_shutter.png"), metallic=0.45, roughness=0.45),
        "solar_panel": _make_tex_pbr("CGES_Solar_Panel", t("tex_solar_panel.png"), t("tex_solar_panel_nrm.png"), 0.50, metallic=0.42, roughness=0.18),
        # 寫實深灰綠玻璃（高反光低粗糙，擺脫塑膠藍感！）
        "window_glass": _make_pbr("CGES_Window_Glass", (0.07, 0.12, 0.15, 1.0), metallic=0.38, roughness=0.08),
        "skylight_glass": _make_pbr("CGES_Skylight_Glass", (0.48, 0.64, 0.68, 0.62), metallic=0.18, roughness=0.10, double_sided=True),
        "canopy_green_glass": _make_pbr("CGES_Canopy_GreenGlass", (0.32, 0.62, 0.50, 0.65), metallic=0.12, roughness=0.15, double_sided=True),
        "window_frame": _make_pbr("CGES_Window_Frame", (0.62, 0.64, 0.66, 1.0), metallic=0.68, roughness=0.32),
        "ac_unit": _make_pbr("CGES_AC_Unit", (0.84, 0.83, 0.80, 1.0), metallic=0.18, roughness=0.46),
        "ac_grille": _make_pbr("CGES_AC_Grille", (0.14, 0.15, 0.16, 1.0), metallic=0.25, roughness=0.60),
        "corridor_light": _make_pbr("CGES_Corridor_Light", (0.98, 0.99, 1.0, 1.0), roughness=0.2, emission=(0.95, 0.98, 1.0), emission_strength=1.4),
        "railing_white": _make_pbr("CGES_Railing_White", (0.89, 0.90, 0.89, 1.0), metallic=0.25, roughness=0.34),
        "metal_dark": _make_pbr("CGES_Metal_Dark", (0.16, 0.17, 0.19, 1.0), metallic=0.62, roughness=0.36),
        "steel_silver": _make_pbr("CGES_Steel_Silver", (0.76, 0.78, 0.80, 1.0), metallic=0.82, roughness=0.24),
        "fitness_stainless": _make_pbr("CGES_Fitness_Stainless", (0.56, 0.59, 0.62, 1.0), metallic=0.84, roughness=0.28),
        "fitness_sand_pad": _make_pbr("CGES_Fitness_SandPad", (0.76, 0.73, 0.67, 1.0), roughness=0.92),
        "arch_orange": _make_pbr("CGES_Arch_Orange", (0.74, 0.32, 0.18, 1.0), roughness=0.62),
        "pad_green": _make_pbr("CGES_Pad_Green", (0.14, 0.42, 0.22, 1.0), roughness=0.68),
        # 校門與招牌特色貼圖
        "school_sign": _make_tex_pbr("CGES_School_Sign", t("tex_school_sign.png"), roughness=0.38),
        "emblem_cges": _make_tex_pbr("CGES_Emblem", t("tex_emblem_cges.png"), roughness=0.48),
        "banner_3f": _make_tex_pbr("CGES_Banner_3F", t("tex_banner_3f.png"), roughness=0.52),
        "banner_4f": _make_tex_pbr("CGES_Banner_4F", t("tex_banner_4f.png"), roughness=0.52),
        "banner_5f": _make_tex_pbr("CGES_Banner_5F", t("tex_banner_5f.png"), roughness=0.52),
        "breezeway_header": _make_tex_pbr("CGES_Breezeway_Header", t("tex_breezeway_header.png"), roughness=0.48),
        "led_screen": _make_tex_pbr("CGES_LED_Screen", t("tex_led_campus.png"), roughness=0.25, emission_strength=0.45),
        # 地面、操場與球場
        "paving_redbrick": _make_tex_pbr("CGES_Paving_RedBrick", t("tex_paving_redbrick.png"), t("tex_paving_redbrick_nrm.png"), 0.65, roughness=0.80),
        "track_pu": _make_tex_pbr("CGES_Track_PU", t("tex_track_pu.png"), t("tex_track_pu_nrm.png"), 0.45, roughness=0.74),
        "track_line": _make_pbr("CGES_Track_Line", (0.95, 0.95, 0.93, 1.0), roughness=0.60),
        "grass": _make_tex_pbr("CGES_Grass", t("tex_grass.png"), roughness=0.90),
        "court_bball": _make_tex_pbr("CGES_Court_BBall", t("tex_court_bball.png"), roughness=0.70),
        "asphalt": _make_tex_pbr("CGES_Asphalt", t("tex_asphalt.png"), t("tex_asphalt_nrm.png"), 0.45, roughness=0.88),
        "sidewalk": _make_pbr("CGES_Sidewalk", (0.54, 0.53, 0.50, 1.0), roughness=0.86),
        "road_white": _make_pbr("CGES_Road_White", (0.93, 0.93, 0.91, 1.0), roughness=0.68),
        "road_yellow": _make_pbr("CGES_Road_Yellow", (0.92, 0.74, 0.14, 1.0), roughness=0.68),
        "road_red": _make_pbr("CGES_Road_Red", (0.78, 0.14, 0.14, 1.0), roughness=0.68),
        "crosswalk_green": _make_pbr("CGES_Crosswalk_Green", (0.12, 0.48, 0.36, 1.0), roughness=0.74),
        # 中庭水池與自然多層次植栽
        "pond_water": _make_pbr("CGES_Pond_Water", (0.09, 0.25, 0.20, 0.88), metallic=0.12, roughness=0.06),
        "wood_bridge": _make_pbr("CGES_Wood_Bridge", (0.42, 0.28, 0.17, 1.0), roughness=0.76),
        "tree_trunk": _make_pbr("CGES_Tree_Trunk", (0.30, 0.24, 0.19, 1.0), roughness=0.90),
        "palm_trunk": _make_tex_pbr("CGES_Palm_Trunk", t("tex_palm_bark.png"), t("tex_palm_bark_nrm.png"), 0.75, roughness=0.84),
        "palm_sheath": _make_pbr("CGES_Palm_Sheath", (0.24, 0.48, 0.18, 1.0), roughness=0.58),
        "sky_ceiling": _make_tex_pbr("CGES_Sky_Ceiling", t("tex_sky_ceiling.png"), roughness=0.68, double_sided=True),
        "honor_wall": _make_tex_pbr("CGES_Honor_Wall", t("tex_honor_wall.png"), roughness=0.48, double_sided=True),
        "pillar_mosaic": _make_tex_pbr("CGES_Pillar_Mosaic", t("tex_pillar_mosaic.png"), roughness=0.55),
        "terrazzo_corridor": _make_tex_pbr("CGES_Terrazzo_Corridor", t("tex_terrazzo_corridor.png"), roughness=0.44),
        "train_mural": _make_tex_pbr("CGES_Train_Mural", t("tex_train_mural.png"), roughness=0.52, double_sided=True),
        "classroom_door": _make_pbr("CGES_Classroom_Door", (0.62, 0.48, 0.34, 1.0), roughness=0.55),
        "water_tank_steel": _make_pbr("CGES_WaterTank_Steel", (0.80, 0.82, 0.85, 1.0), metallic=0.88, roughness=0.22),
        "horizon_ground": _make_pbr("CGES_Horizon_Ground", (0.76, 0.77, 0.75, 1.0), roughness=0.95),
        "tree_foliage_a": _make_pbr("CGES_Tree_Foliage_A", (0.13, 0.34, 0.12, 1.0), roughness=0.84),
        "tree_foliage_b": _make_pbr("CGES_Tree_Foliage_B", (0.19, 0.42, 0.15, 1.0), roughness=0.82),
        "tree_foliage_c": _make_pbr("CGES_Tree_Foliage_C", (0.25, 0.48, 0.18, 1.0), roughness=0.80),
        "shrub_red": _make_pbr("CGES_Shrub_Red", (0.38, 0.12, 0.16, 1.0), roughness=0.82),
        "palm_frond": _make_pbr("CGES_Palm_Frond", (0.20, 0.46, 0.17, 1.0), roughness=0.68, double_sided=True),
        # 周邊民宅低對比帶樓層微紋理
        "city_block": _make_tex_pbr("CGES_City_Block", t("tex_city_facade.png"), roughness=0.88),
        # 天橋與運動中心橫幅
        "skybridge_body": _make_pbr("CGES_Skybridge_Body", (0.50, 0.72, 0.86, 1.0), roughness=0.54),
        "skybridge_dolphin": _make_tex_pbr("CGES_Skybridge_Dolphin", t("tex_skybridge_dolphin.png"), roughness=0.48, double_sided=True),
        "skybridge_roof": _make_pbr("CGES_Skybridge_Roof", (0.52, 0.56, 0.58, 1.0), metallic=0.32, roughness=0.42),
        "gym_banner": _make_tex_pbr("CGES_Gym_Banner", t("tex_gym_banner.png"), roughness=0.48, double_sided=True),
        "fence_mesh_green": _make_tex_pbr("CGES_Fence_MeshGreen", t("tex_chainlink_green.png"), metallic=0.45, roughness=0.45, alpha=0.98, double_sided=True),
        "flag_red": _make_pbr("CGES_Flag_Red", (0.78, 0.12, 0.14, 1.0), roughness=0.65, double_sided=True),
        "flag_blue": _make_pbr("CGES_Flag_Blue", (0.14, 0.34, 0.66, 1.0), roughness=0.65, double_sided=True),
        "flag_yellow": _make_pbr("CGES_Flag_Yellow", (0.90, 0.74, 0.12, 1.0), roughness=0.65, double_sided=True),
        "walkway_gray_paver": _make_tex_pbr("CGES_Walkway_GrayPaver", t("tex_walkway_terrazzo.png"), t("tex_granite_gray_nrm.png"), 0.35, roughness=0.78),
        # 棟別名牌、走廊門牌、樓層指引與車輛街具
        "sign_guanghe": _make_tex_pbr("CGES_Sign_Guanghe", t("tex_sign_guanghe.png"), roughness=0.40, double_sided=True),
        "sign_heping": _make_tex_pbr("CGES_Sign_Heping", t("tex_sign_heping.png"), roughness=0.40, double_sided=True),
        "sign_wuquan": _make_tex_pbr("CGES_Sign_Wuquan", t("tex_sign_wuquan.png"), roughness=0.40, double_sided=True),
        "sign_chongqing": _make_tex_pbr("CGES_Sign_Chongqing", t("tex_sign_chongqing.png"), roughness=0.40, double_sided=True),
        "room_plaque": _make_tex_pbr("CGES_Room_Plaque", t("tex_room_plaque.png"), roughness=0.42, double_sided=False),
        "room_plaque_atlas": _make_tex_pbr("CGES_Room_PlaqueAtlas", t("tex_room_plaques_atlas.png"), roughness=0.38, double_sided=False),
        "floor_dir": _make_tex_pbr("CGES_Floor_Dir", t("tex_floor_dir.png"), roughness=0.42, double_sided=False),
        "bus_yellow": _make_pbr("CGES_Bus_Yellow", (0.94, 0.72, 0.08, 1.0), metallic=0.18, roughness=0.32),
        "bus_side": _make_tex_pbr("CGES_Bus_Side", t("tex_bus_side.png"), metallic=0.15, roughness=0.32, double_sided=True),
        "car_silver": _make_pbr("CGES_Car_Silver", (0.64, 0.66, 0.69, 1.0), metallic=0.65, roughness=0.24),
        "car_black": _make_pbr("CGES_Car_Black", (0.09, 0.10, 0.12, 1.0), metallic=0.55, roughness=0.22),
        "car_white": _make_pbr("CGES_Car_White", (0.90, 0.91, 0.92, 1.0), metallic=0.25, roughness=0.26),
        "car_red": _make_pbr("CGES_Car_Red", (0.68, 0.12, 0.14, 1.0), metallic=0.45, roughness=0.26),
        "car_blue": _make_pbr("CGES_Car_Blue", (0.14, 0.28, 0.56, 1.0), metallic=0.48, roughness=0.26),
        "tire_rubber": _make_pbr("CGES_Tire_Rubber", (0.08, 0.08, 0.09, 1.0), roughness=0.88),
        "mirror_orange": _make_pbr("CGES_Mirror_Orange", (0.88, 0.28, 0.08, 1.0), roughness=0.42),
        "mirror_chrome": _make_pbr("CGES_Mirror_Chrome", (0.92, 0.94, 0.96, 1.0), metallic=0.96, roughness=0.05),
        "signal_red": _make_pbr("CGES_Signal_Red", (0.95, 0.12, 0.10, 1.0), emission=(1.0, 0.12, 0.08), emission_strength=2.2),
        "signal_green": _make_pbr("CGES_Signal_Green", (0.10, 0.88, 0.36, 1.0), emission=(0.12, 1.0, 0.38), emission_strength=2.2),
        "curb_concrete": _make_tex_pbr("CGES_Curb_Concrete", t("tex_curb_concrete.png"), t("tex_curb_concrete_nrm.png"), 0.60, roughness=0.84),
        "granite_gray": _make_tex_pbr("CGES_Granite_Gray", t("tex_granite_gray.png"), t("tex_granite_gray_nrm.png"), 0.50, roughness=0.72),
        "sidewalk_south": _make_tex_pbr("CGES_Sidewalk_South", t("tex_sidewalk_south.png"), t("tex_sidewalk_south_nrm.png"), 0.55, roughness=0.80),
        "tree_soil": _make_pbr("CGES_Tree_Soil", (0.20, 0.15, 0.11, 1.0), roughness=0.95),
        # v6 正面街景精修專屬材質
        "heping_vert_sign": _make_tex_pbr("CGES_Heping_VertSign", t("tex_heping_vert_sign.png"), roughness=0.42, double_sided=True),
        "sidewalk_checker": _make_tex_pbr("CGES_Sidewalk_Checker", t("tex_sidewalk_checker.png"), t("tex_sidewalk_checker_nrm.png"), 0.55, roughness=0.78),
        "sidewalk_diag_brick": _make_tex_pbr("CGES_Sidewalk_DiagBrick", t("tex_sidewalk_diag_brick.png"), t("tex_sidewalk_diag_brick_nrm.png"), 0.62, roughness=0.80),
        "roadsign_guanghe": _make_tex_pbr("CGES_RoadSign_Guanghe", t("tex_roadsign_guanghe.png"), roughness=0.35, double_sided=True),
        "roadsign_heping": _make_tex_pbr("CGES_RoadSign_Heping", t("tex_roadsign_heping.png"), roughness=0.35, double_sided=True),
        "sign_children": _make_tex_pbr("CGES_Sign_Children", t("tex_sign_children.png"), roughness=0.35, double_sided=True, use_tex_alpha=True),
        "tactile_yellow": _make_pbr("CGES_Tactile_Yellow", (0.86, 0.72, 0.34, 1.0), roughness=0.74),
        "lamp_globe": _make_pbr("CGES_Lamp_Globe", (0.94, 0.86, 0.64, 1.0), roughness=0.22, emission=(1.0, 0.90, 0.62), emission_strength=0.65),
        "transformer_gray": _make_pbr("CGES_Transformer_Gray", (0.58, 0.60, 0.62, 1.0), metallic=0.35, roughness=0.52),
        "cone_orange": _make_pbr("CGES_Cone_Orange", (0.94, 0.34, 0.08, 1.0), roughness=0.45),
        "fence_bronze": _make_pbr("CGES_Fence_Bronze", (0.28, 0.24, 0.21, 1.0), metallic=0.55, roughness=0.42),
        # v7/v8 廣和街正面透明熱拌漆標線與智慧停車收費柱材質
        "smart_parking": _make_tex_pbr("CGES_Smart_Parking", t("tex_smart_parking.png"), roughness=0.76, use_tex_alpha=True),
        "smart_parking_south": _make_tex_pbr("CGES_Smart_ParkingSouth", t("tex_smart_parking_south.png"), roughness=0.76, use_tex_alpha=True),
        "moto_wait_box": _make_tex_pbr("CGES_Moto_WaitBox", t("tex_moto_wait_box.png"), roughness=0.76, use_tex_alpha=True),
        "manhole": _make_tex_pbr("CGES_Manhole", t("tex_manhole.png"), metallic=0.55, roughness=0.65, use_tex_alpha=True),
        "drain_grate": _make_tex_pbr("CGES_Drain_Grate", t("tex_drain_grate.png"), metallic=0.65, roughness=0.48),
        "pole_hazard": _make_tex_pbr("CGES_Pole_Hazard", t("tex_pole_hazard.png"), metallic=0.25, roughness=0.48),
        "pillar_front": _make_tex_pbr("CGES_Pillar_Front", t("tex_pillar_front.png"), metallic=0.15, roughness=0.18),
        "pillar_silver": _make_pbr("CGES_Pillar_Silver", (0.74, 0.76, 0.79, 1.0), metallic=0.78, roughness=0.30),
        "pillar_black_glass": _make_pbr("CGES_Pillar_BlackGlass", (0.04, 0.05, 0.06, 1.0), metallic=0.25, roughness=0.10),
        "pillar_led_green": _make_pbr("CGES_Pillar_LEDGreen", (0.14, 0.92, 0.42, 1.0), emission=(0.14, 0.95, 0.44), emission_strength=1.8),
        "sign_pickup": _make_tex_pbr("CGES_Sign_Pickup", t("tex_sign_pickup.png"), roughness=0.38, double_sided=True),
        "gate_banner": _make_tex_pbr("CGES_Gate_Banner", t("tex_gate_banner.png"), roughness=0.52, double_sided=True),
        "fence_red_banner": _make_tex_pbr("CGES_Fence_RedBanner", t("tex_fence_red_banner.png"), roughness=0.58, double_sided=True),
        "house_num_31": _make_tex_pbr("CGES_House_Num31", t("tex_house_num_31.png"), roughness=0.35, double_sided=True),
        "side_gate_green": _make_pbr("CGES_SideGate_Green", (0.12, 0.32, 0.22, 1.0), metallic=0.45, roughness=0.46),
        "shed_roof_gray": _make_pbr("CGES_Shed_RoofGray", (0.48, 0.50, 0.52, 1.0), metallic=0.35, roughness=0.52),
        # v9 南側街景專屬材質（92/43/76/3/12 廣和街）
        "south_shutter": _make_tex_pbr("CGES_South_Shutter", t("tex_south_shutter.png"), metallic=0.42, roughness=0.56, double_sided=True),
        "disabled_parking": _make_tex_pbr("CGES_Disabled_Parking", t("tex_disabled_parking.png"), roughness=0.76, use_tex_alpha=True),
        "rect_manhole": _make_tex_pbr("CGES_Rect_Manhole", t("tex_rect_manhole.png"), metallic=0.52, roughness=0.66),
        "sign_wuquan30": _make_tex_pbr("CGES_Sign_Wuquan30", t("tex_sign_wuquan30.png"), roughness=0.36, double_sided=True),
        "sign_campus_rules": _make_tex_pbr("CGES_Sign_CampusRules", t("tex_sign_campus_rules.png"), roughness=0.38, double_sided=True),
        "sign_backgate_blue": _make_tex_pbr("CGES_Sign_BackgateBlue", t("tex_sign_backgate_blue.png"), roughness=0.38, double_sided=True),
        "sign_guanghe_wuquan": _make_tex_pbr("CGES_Sign_GuangheWuquan", t("tex_sign_guanghe_wuquan.png"), roughness=0.36, double_sided=True),
        "youbike_pillar": _make_tex_pbr("CGES_YouBike_Pillar", t("tex_youbike_pillar.png"), metallic=0.22, roughness=0.40),
        "youbike_yellow": _make_pbr("CGES_YouBike_Yellow", (0.95, 0.72, 0.10, 1.0), metallic=0.20, roughness=0.34),
        "youbike_orange": _make_pbr("CGES_YouBike_Orange", (0.92, 0.38, 0.08, 1.0), metallic=0.20, roughness=0.36),
        "stainless_gate": _make_pbr("CGES_Stainless_Gate", (0.74, 0.76, 0.78, 1.0), metallic=0.86, roughness=0.28),
        "canopy_arch_darkgreen": _make_pbr("CGES_Canopy_ArchDarkGreen", (0.09, 0.25, 0.19, 0.88), metallic=0.18, roughness=0.24, double_sided=True),
        "taipower_green": _make_pbr("CGES_Taipower_Green", (0.64, 0.70, 0.65, 1.0), metallic=0.30, roughness=0.50),
        # v10 東側五權街實景專屬材質（2/9/1/中北段/15 五權街）
        "smart_parking_east": _make_tex_pbr("CGES_Smart_ParkingEast", t("tex_smart_parking_east.png"), roughness=0.76, use_tex_alpha=True),
        "disabled_moto_east": _make_tex_pbr("CGES_Disabled_MotoEast", t("tex_disabled_moto_east.png"), roughness=0.76, use_tex_alpha=True),
        "car_bays_east": _make_tex_pbr("CGES_Car_BaysEast", t("tex_car_bays_east.png"), roughness=0.76, use_tex_alpha=True),
        "bus_stop_box": _make_tex_pbr("CGES_Bus_StopBox", t("tex_bus_stop_box.png"), roughness=0.76, use_tex_alpha=True),
        "sign_wuquan_alley": _make_tex_pbr("CGES_Sign_WuquanAlley", t("tex_sign_wuquan_alley.png"), roughness=0.36, double_sided=True),
        "sign_heping_vert": _make_tex_pbr("CGES_Sign_HepingVert", t("tex_sign_heping_vert.png"), roughness=0.36, double_sided=True),
        "sign_wuquan_horiz": _make_tex_pbr("CGES_Sign_WuquanHoriz", t("tex_sign_wuquan_horiz.png"), roughness=0.36, double_sided=True),
        "campus_bulletin": _make_tex_pbr("CGES_Campus_Bulletin", t("tex_campus_bulletin.png"), roughness=0.32, double_sided=True),
        "sign_wet_track": _make_tex_pbr("CGES_Sign_WetTrack", t("tex_sign_wet_track.png"), roughness=0.45, double_sided=True),
        "sign_student_pickup": _make_tex_pbr("CGES_Sign_StudentPickup", t("tex_sign_student_pickup.png"), roughness=0.38, double_sided=True),
        "hydrant_red": _make_pbr("CGES_Hydrant_Red", (0.82, 0.12, 0.12, 1.0), metallic=0.35, roughness=0.36),
        "side_gate_lightgreen": _make_pbr("CGES_SideGate_LightGreen", (0.36, 0.56, 0.36, 1.0), metallic=0.42, roughness=0.44),
        "amber_flash": _make_pbr("CGES_Amber_Flash", (0.98, 0.72, 0.08, 1.0), emission=(1.0, 0.74, 0.06), emission_strength=2.2),
        "box_darkgreen": _make_pbr("CGES_Box_DarkGreen", (0.12, 0.30, 0.18, 1.0), metallic=0.35, roughness=0.48),
        # v11 北側和平路實景專屬材質（166/147/129 和平路）
        "skybridge_pillar_wave": _make_tex_pbr("CGES_Skybridge_PillarWave", t("tex_skybridge_pillar_wave.png"), roughness=0.62),
        "speed_30_yellow": _make_tex_pbr("CGES_Speed30_Yellow", t("tex_speed_30_yellow.png"), roughness=0.76, use_tex_alpha=True),
        "bus_only_box": _make_tex_pbr("CGES_Bus_OnlyBox", t("tex_bus_only_box.png"), roughness=0.76, use_tex_alpha=True),
        # v12.5 五權樓東立面實景專屬材質（9/2 五權街：大型直立布條、2F 深藍橫牌、北穿堂彩繪壁畫、霧灰鐵捲門、9 梯淺藍反光玻璃）
        "wuquan_vertical_banner": _make_tex_pbr("CGES_Wuquan_VertBanner", t("tex_wuquan_vertical_banner.png"), roughness=0.52, double_sided=False),
        "wuquan_blue_banner": _make_tex_pbr("CGES_Wuquan_BlueBanner", t("tex_wuquan_blue_banner.png"), roughness=0.38, double_sided=False),
        "wuquan_north_mural": _make_tex_pbr("CGES_Wuquan_NorthMural", t("tex_wuquan_north_mural.png"), roughness=0.58, double_sided=True),
        "wuquan_shutter_gray": _make_tex_pbr("CGES_Wuquan_ShutterGray", t("tex_wuquan_shutter_gray.png"), metallic=0.45, roughness=0.46, double_sided=False),
        "glass_frosted_blue": _make_pbr("CGES_Glass_FrostedBlue", (0.54, 0.68, 0.78, 1.0), metallic=0.32, roughness=0.15),
        # v12.6 操場北側籃球場與淡綠緩衝地坪專屬材質（2 五權街 & 147 和平路！）
        "court_north_concrete": _make_tex_pbr("CGES_Court_NorthConcrete", t("tex_court_north_concrete.png"), roughness=0.84),
        "court_north_mint": _make_pbr("CGES_Court_NorthMint", (0.56, 0.72, 0.56, 1.0), roughness=0.80),
        "backboard_white": _make_tex_pbr("CGES_Backboard_White", t("tex_backboard_white.png"), roughness=0.36, double_sided=False),
        "hoop_pad_blue": _make_pbr("CGES_HoopPad_Blue", (0.12, 0.34, 0.74, 1.0), roughness=0.52),
        "hoop_rim_orange": _make_pbr("CGES_HoopRim_Orange", (0.86, 0.30, 0.08, 1.0), metallic=0.55, roughness=0.38),
        "heping_moto_box": _make_tex_pbr("CGES_Heping_MotoBox", t("tex_heping_moto_box.png"), roughness=0.76, use_tex_alpha=True),
        "bus_led_board": _make_tex_pbr("CGES_Bus_LEDBoard", t("tex_bus_led_board.png"), roughness=0.25, emission_strength=0.65, double_sided=True),
        "rock_landscape": _make_tex_pbr("CGES_Rock_Landscape", t("tex_rock_landscape.png"), t("tex_rock_landscape_nrm.png"), 0.85, roughness=0.92),
        "lamp_skyblue": _make_pbr("CGES_Lamp_SkyBlue", (0.26, 0.56, 0.82, 1.0), metallic=0.22, roughness=0.42),
        "shelter_navy": _make_pbr("CGES_Shelter_Navy", (0.12, 0.22, 0.44, 1.0), metallic=0.42, roughness=0.40),
        "b1_louver": _make_pbr("CGES_B1_Louver", (0.16, 0.20, 0.20, 1.0), metallic=0.38, roughness=0.52),
        # v11.3 147 和平路地下室雙鐵捲門、紅磚花格帶、春聯與防滑綠斜坡材質
        "b1_shutter_tri": _make_tex_pbr("CGES_B1_ShutterTri", t("tex_b1_shutter_tri.png"), metallic=0.36, roughness=0.48, double_sided=True),
        "b1_shutter_silver": _make_tex_pbr("CGES_B1_ShutterSilver", t("tex_b1_shutter_silver.png"), metallic=0.52, roughness=0.44, double_sided=True),
        "brick_lattice_band": _make_tex_pbr("CGES_Brick_LatticeBand", t("tex_brick_lattice_band.png"), roughness=0.72, double_sided=True),
        "pillar_chunlian": _make_tex_pbr("CGES_Pillar_Chunlian", t("tex_pillar_chunlian.png"), roughness=0.70, double_sided=True),
        "ramp_green_antislip": _make_pbr("CGES_Ramp_GreenAntiSlip", (0.17, 0.34, 0.24, 1.0), roughness=0.82),
        # 衛星校準底板
        "sat_ref": _make_tex_pbr("CGES_Sat_Ref", os.path.join(REFS_DIR, "sat_aligned_220m.png"), roughness=0.95),
    }


def setup_daylight(center: Sequence[float] = (0.0, 0.0, 6.0), use_nishita: bool = False) -> None:
    """設定高質感晴朗日光（Cycles 宣傳圖啟用物理 Nishita 天空，EEVEE 保持輕快自然藍天）。"""
    scene = bpy.context.scene
    world = bpy.data.worlds.new("CGES_DaylightWorld")
    scene.world = world
    nt = su.ensure_material_nodes(world)
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")

    if use_nishita:
        sky = nt.nodes.new("ShaderNodeTexSky")
        for candidate in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
            try:
                sky.sky_type = candidate
                break
            except Exception:
                continue
        for attr, val in [
            ("sun_disc", True),
            ("sun_elevation", math.radians(34.0)),
            ("sun_rotation", math.radians(138.0)),
            ("air_density", 1.15),
            ("dust_density", 0.90),
        ]:
            if hasattr(sky, attr):
                try:
                    setattr(sky, attr, val)
                except Exception:
                    pass
        # Physical MULTIPLE_SCATTERING sky carries a full real-world sun (~40+ EV); keep strength ~0.14 with NO duplicate Sun lamp!
        bg.inputs["Strength"].default_value = 0.14
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
        return

    bg.inputs["Color"].default_value = (0.55, 0.74, 0.95, 1.0)
    bg.inputs["Strength"].default_value = 0.92
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    sun_data = bpy.data.lights.new("CGES_Sun", type="SUN")
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.95, 0.87)
    sun_data.angle = math.radians(1.0)
    sun_obj = bpy.data.objects.new("CGES_Sun", sun_data)
    sun_obj.location = (center[0] - 90.0, center[1] - 70.0, 120.0)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(-16.0), math.radians(-42.0))
    su.link_object(sun_obj, "Lighting")

    fill_data = bpy.data.lights.new("CGES_Fill", type="SUN")
    fill_data.energy = 0.82
    fill_data.color = (0.72, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("CGES_Fill", fill_data)
    fill_obj.rotation_euler = (math.radians(58.0), math.radians(24.0), math.radians(140.0))
    su.link_object(fill_obj, "Lighting")
