"""新北市板橋區重慶國小 3D 數位雙生 — 四面街道斜率與校園共用座標基準模組。

集中管理所有經衛星正射圖 (sat_aligned_220m.png) 與 2025/05 實景街景校準之座標常數與基準線函式，
供 mod_campus_grounds / mod_campus_landmarks / mod_campus_street_details / mod_campus_bldg 共用。
"""
import math

# === 西側廣和街（往北 +Y 時 X 往東 +X 傾斜 8.5°） ===
GUANGHE_SLOPE_DEG = 8.5
GUANGHE_TAN = math.tan(math.radians(GUANGHE_SLOPE_DEG))
GUANGHE_ROT_Z = -math.radians(GUANGHE_SLOPE_DEG)
SIDEWALK_W = 4.5  # 西側圍牆腳至路緣石外緣總寬 4.5m

# === 南側廣和街（後門 3 號門段） ===
SOUTH_WALL_Y = -69.8  # 南側廣和街圍牆基準線 Y 座標
SOUTH_CURB_Y = -73.2  # 南側廣和街北路緣石外緣線 Y 座標（人行道寬 3.4m）

# === 東側五權街（南接東南圓弧終點 (73.5, -62.8)，往北微向西斜 3.2° 至和平路口） ===
EAST_SLOPE_DEG = 3.2
EAST_TAN = math.tan(math.radians(EAST_SLOPE_DEG))
EAST_ROT_Z = math.radians(EAST_SLOPE_DEG)
EAST_SIDEWALK_W = 3.30

# === 北側和平路（鎖定 NW 圓弧 (-60.5, 43.78) 與 NE 圓弧 (+60.5, 52.84)） ===
HEPING_TAN = (52.84 - 43.78) / 121.0
HEPING_SLOPE_DEG = math.degrees(math.atan(HEPING_TAN))  # ~4.282°
HEPING_ROT_Z = math.atan(HEPING_TAN)
HEPING_EAST_WALK_W = 1.65  # 操場北緣 166/147 和平路窄幅水泥人行道寬度 1.65m

# === 校園核心設施錨點 ===
STAGE_SY = -13.75  # 五權樓連建式升旗司令台中心 Y 座標（b=6）
TRACK_CENTER = (42.0, -12.0)


def wall_x(y: float) -> float:
    """西側廣和街校園圍牆基準線 X 座標（於校門中心 y=1.5 處恰為 -71.5）。"""
    return -71.5 + (y - 1.5) * GUANGHE_TAN


def curb_x(y: float) -> float:
    """西側廣和街東路緣石外緣線 X 座標（比圍牆線偏西 4.5m）。"""
    return wall_x(y) - SIDEWALK_W


def east_wall_x(y: float) -> float:
    """東側五權街校園圍牆基準線 X 座標（於 y=-62.8 處恰為 73.50）。"""
    return 73.5 - (y + 62.8) * EAST_TAN


def east_curb_x(y: float) -> float:
    """東側五權街西路緣石外緣線 X 座標（比圍牆線偏東 3.30m）。"""
    return east_wall_x(y) + EAST_SIDEWALK_W


def heping_south_edge_y(x: float) -> float:
    """北側和平路南側路緣基準線 Y 座標（於 x=-60.5 為 43.78，於 x=+60.5 為 52.84）。"""
    return 48.31 + x * HEPING_TAN


def heping_curb_y(x: float) -> float:
    """北側和平路南路緣石外緣線 Y 座標別名。"""
    return heping_south_edge_y(x)


def _quad_extrude(bm, pts_2d, z0: float, z1: float) -> None:
    """由任意 2D 多邊形（自動正規化為 CCW）擠出 3D 實體。"""
    import geom_primitives as gp

    gp.quad_extrude(bm, pts_2d, z0, z1)


def _add_strip_along_guanghe(bm, y0: float, y1: float, off_w: float, off_e: float, z0: float, z1: float) -> None:
    """沿西側廣和街斜率建立 [y0, y1] × [curb_x+off_w, curb_x+off_e] 條帶實體。"""
    pts = [
        (curb_x(y0) + off_w, y0),
        (curb_x(y0) + off_e, y0),
        (curb_x(y1) + off_e, y1),
        (curb_x(y1) + off_w, y1),
    ]
    _quad_extrude(bm, pts, z0, z1)


def _add_strip_along_wuquan(bm, y0: float, y1: float, off_w: float, off_e: float, z0: float, z1: float) -> None:
    """沿東側五權街斜率建立 [y0, y1] × [east_curb_x+off_w, east_curb_x+off_e] 條帶實體。"""
    pts = [
        (east_curb_x(y0) + off_w, y0),
        (east_curb_x(y0) + off_e, y0),
        (east_curb_x(y1) + off_e, y1),
        (east_curb_x(y1) + off_w, y1),
    ]
    _quad_extrude(bm, pts, z0, z1)


def _add_strip_along_heping(bm, x0: float, x1: float, off_s: float, off_n: float, z0: float, z1: float) -> None:
    """沿北側和平路斜率建立 [x0, x1] × [heping_south_edge_y+off_s, +off_n] 條帶實體。"""
    pts = [
        (x0, heping_south_edge_y(x0) + off_s),
        (x1, heping_south_edge_y(x1) + off_s),
        (x1, heping_south_edge_y(x1) + off_n),
        (x0, heping_south_edge_y(x0) + off_n),
    ]
    _quad_extrude(bm, pts, z0, z1)
