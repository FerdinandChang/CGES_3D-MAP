"""重慶國小地面、周邊道路、高細節 200m 操場司令台、露天雙籃球場、中庭生態池與自然多分支植栽（v3）。"""
import math
import random
from typing import Dict, List, Tuple

import bmesh
import bpy
from mathutils import Matrix, Vector

import geom_primitives as gp
import studio_utils as su
from coords import (
    EAST_ROT_Z,
    EAST_SIDEWALK_W,
    EAST_SLOPE_DEG,
    EAST_TAN,
    GUANGHE_ROT_Z,
    GUANGHE_SLOPE_DEG,
    GUANGHE_TAN,
    HEPING_EAST_WALK_W,
    HEPING_ROT_Z,
    HEPING_SLOPE_DEG,
    HEPING_TAN,
    SIDEWALK_W,
    SOUTH_CURB_Y,
    SOUTH_WALL_Y,
    STAGE_SY,
    curb_x,
    east_curb_x,
    east_wall_x,
    heping_curb_y,
    heping_south_edge_y,
    wall_x,
    _add_strip_along_guanghe,
    _add_strip_along_heping,
    _add_strip_along_wuquan,
    _quad_extrude,
)

_add_uv_quad_world = gp.add_plane_uv


def _add_green_crosswalk_heping(
    bm_green: bmesh.types.BMesh,
    bm_white: bmesh.types.BMesh,
    x_center: float,
    off_s: float = 0.26,
    off_n: float = 10.18,
    width_x: float = 3.6,
    n_stripes: int = 5,
) -> None:
    """沿北側和平路精準對齊、100% 位於柏油車道內之跨路綠底白色斑馬線！"""
    hx = width_x * 0.5
    _add_strip_along_heping(bm_green, x_center - hx, x_center + hx, off_s, off_n, 0.008, 0.018)
    stripe_w = width_x / (n_stripes * 2.05)
    span_x = width_x - 0.55
    for i in range(n_stripes):
        sx = x_center - span_x * 0.5 + span_x * i / max(1, n_stripes - 1)
        _add_strip_along_heping(bm_white, sx - stripe_w * 0.5, sx + stripe_w * 0.5, off_s + 0.16, off_n - 0.16, 0.012, 0.024)


def _add_clipped_yellow_grid_wuquan(
    bm: bmesh.types.BMesh,
    y_center: float,
    half_len_y: float,
    off_w: float,
    off_e: float,
    pitch: float = 1.90,
    border_w: float = 0.20,
    line_w: float = 0.13,
    z_top: float = 0.022,
) -> None:
    """沿東側五權街斜率精準裁切 45° 黃網線（1 五權街路口，零超框！）。"""
    z0 = 0.008
    _add_strip_along_wuquan(bm, y_center - half_len_y, y_center + half_len_y, off_w, off_w + border_w, z0, z_top)
    _add_strip_along_wuquan(bm, y_center - half_len_y, y_center + half_len_y, off_e - border_w, off_e, z0, z_top)
    _add_strip_along_wuquan(bm, y_center - half_len_y, y_center - half_len_y + border_w, off_w, off_e, z0, z_top)
    _add_strip_along_wuquan(bm, y_center + half_len_y - border_w, y_center + half_len_y, off_w, off_e, z0, z_top)

    u0, u1 = off_w + border_w * 0.6, off_e - border_w * 0.6
    v0, v1 = -half_len_y + border_w * 0.6, half_len_y - border_w * 0.6

    def to_world(u: float, v: float) -> Tuple[float, float]:
        wy = y_center + v
        return (east_curb_x(wy) + u, wy)

    def add_seg(a: Tuple[float, float], b: Tuple[float, float]) -> None:
        p0, p1 = to_world(*a), to_world(*b)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 0.15:
            return
        nx, ny = -dy / L * (line_w * 0.5), dx / L * (line_w * 0.5)
        _quad_extrude(bm, [(p0[0] - nx, p0[1] - ny), (p1[0] - nx, p1[1] - ny), (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)], z0, z_top)

    for sign in (1, -1):
        c_lo = (u0 + v0) if sign == 1 else (u0 - v1)
        c_hi = (u1 + v1) if sign == 1 else (u1 - v0)
        k = int(math.floor(c_lo / pitch))
        while k * pitch <= c_hi:
            c = k * pitch
            pts: List[Tuple[float, float]] = []
            for ut in (u0, u1):
                vt = (c - ut) if sign == 1 else (ut - c)
                if v0 - 1e-5 <= vt <= v1 + 1e-5:
                    pts.append((ut, max(v0, min(v1, vt))))
            for vt in (v0, v1):
                ut = (c - vt) if sign == 1 else (c + vt)
                if u0 - 1e-5 <= ut <= u1 + 1e-5:
                    pts.append((max(u0, min(u1, ut)), vt))
            uniq: List[Tuple[float, float]] = []
            for pt in pts:
                if all(math.hypot(pt[0] - q[0], pt[1] - q[1]) > 1e-3 for q in uniq):
                    uniq.append(pt)
            if len(uniq) == 2:
                add_seg(uniq[0], uniq[1])
            k += 1


def _add_green_crosswalk_wuquan(
    bm_green: bmesh.types.BMesh,
    bm_white: bmesh.types.BMesh,
    y_center: float,
    off_w: float = 0.25,
    off_e: float = 8.4,
    width_y: float = 3.5,
    n_stripes: int = 5,
) -> None:
    """沿東側五權街精準對齊且 100% 位於柏油車道內之綠底白色斑馬線！"""
    hy = width_y * 0.5
    _add_strip_along_wuquan(bm_green, y_center - hy, y_center + hy, off_w, off_e, 0.008, 0.018)
    stripe_h = width_y / (n_stripes * 2.05)
    span_y = width_y - 0.55
    for i in range(n_stripes):
        sy = y_center - span_y * 0.5 + span_y * i / max(1, n_stripes - 1)
        _add_strip_along_wuquan(bm_white, sy - stripe_h * 0.5, sy + stripe_h * 0.5, off_w + 0.16, off_e - 0.16, 0.012, 0.024)


def _add_polyline_ribbon(
    bm: bmesh.types.BMesh,
    spine: List[Tuple[float, float]],
    off_left: float,
    off_right: float,
    z0: float,
    z1: float,
) -> None:
    """沿任意 2D 折線／圓弧以左右法向偏移建立平滑連續帶狀實體（用於圓弧水泥路緣石與圓弧紅線！）。"""
    n = len(spine)
    if n < 2:
        return
    left_pts: List[Tuple[float, float]] = []
    right_pts: List[Tuple[float, float]] = []
    for i in range(n):
        p_prev = spine[max(0, i - 1)]
        p_next = spine[min(n - 1, i + 1)]
        dx, dy = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
        L = max(1e-6, math.hypot(dx, dy))
        # Left normal (-dy/L, dx/L)
        nx, ny = -dy / L, dx / L
        px, py = spine[i]
        left_pts.append((px + nx * off_left, py + ny * off_left))
        right_pts.append((px + nx * off_right, py + ny * off_right))
    for i in range(n - 1):
        quad = [right_pts[i], right_pts[i + 1], left_pts[i + 1], left_pts[i]]
        _quad_extrude(bm, quad, z0, z1)


def _add_clipped_yellow_grid(
    bm: bmesh.types.BMesh,
    y_center: float,
    half_len_y: float,
    off_w: float,
    off_e: float,
    pitch: float = 1.85,
    border_w: float = 0.20,
    line_w: float = 0.13,
    z_top: float = 0.022,
) -> None:
    """精準裁切於矩形外框內的 45° 黃網線（100% 沿廣和街斜率、零超框突出！）。"""
    z0 = 0.008
    # 4 outer borders
    _add_strip_along_guanghe(bm, y_center - half_len_y, y_center + half_len_y, off_w, off_w + border_w, z0, z_top)
    _add_strip_along_guanghe(bm, y_center - half_len_y, y_center + half_len_y, off_e - border_w, off_e, z0, z_top)
    _add_strip_along_guanghe(bm, y_center - half_len_y, y_center - half_len_y + border_w, off_w, off_e, z0, z_top)
    _add_strip_along_guanghe(bm, y_center + half_len_y - border_w, y_center + half_len_y, off_w, off_e, z0, z_top)

    u0, u1 = off_w + border_w * 0.6, off_e - border_w * 0.6
    v0, v1 = -half_len_y + border_w * 0.6, half_len_y - border_w * 0.6

    def to_world(u: float, v: float) -> Tuple[float, float]:
        wy = y_center + v
        return (curb_x(wy) + u, wy)

    def add_seg(a: Tuple[float, float], b: Tuple[float, float]) -> None:
        p0, p1 = to_world(*a), to_world(*b)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 0.15:
            return
        nx, ny = -dy / L * (line_w * 0.5), dx / L * (line_w * 0.5)
        _quad_extrude(bm, [(p0[0] - nx, p0[1] - ny), (p1[0] - nx, p1[1] - ny), (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)], z0, z_top)

    # Clip u + v = c and u - v = c against [u0, u1] x [v0, v1]
    c_min_p, c_max_p = u0 + v0, u1 + v1
    k = int(math.floor(c_min_p / pitch))
    while k * pitch <= c_max_p:
        c = k * pitch
        pts: List[Tuple[float, float]] = []
        for u_t in (u0, u1):
            v_t = c - u_t
            if v0 - 1e-5 <= v_t <= v1 + 1e-5:
                pts.append((u_t, max(v0, min(v1, v_t))))
        for v_t in (v0, v1):
            u_t = c - v_t
            if u0 - 1e-5 <= u_t <= u1 + 1e-5:
                pts.append((max(u0, min(u1, u_t)), v_t))
        # Deduplicate close points
        uniq: List[Tuple[float, float]] = []
        for pt in pts:
            if all(math.hypot(pt[0] - q[0], pt[1] - q[1]) > 1e-3 for q in uniq):
                uniq.append(pt)
        if len(uniq) == 2:
            add_seg(uniq[0], uniq[1])
        k += 1

    c_min_m, c_max_m = u0 - v1, u1 - v0
    k = int(math.floor(c_min_m / pitch))
    while k * pitch <= c_max_m:
        c = k * pitch
        pts = []
        for u_t in (u0, u1):
            v_t = u_t - c
            if v0 - 1e-5 <= v_t <= v1 + 1e-5:
                pts.append((u_t, max(v0, min(v1, v_t))))
        for v_t in (v0, v1):
            u_t = c + v_t
            if u0 - 1e-5 <= u_t <= u1 + 1e-5:
                pts.append((max(u0, min(u1, u_t)), v_t))
        uniq = []
        for pt in pts:
            if all(math.hypot(pt[0] - q[0], pt[1] - q[1]) > 1e-3 for q in uniq):
                uniq.append(pt)
        if len(uniq) == 2:
            add_seg(uniq[0], uniq[1])
        k += 1


def _add_green_crosswalk_guanghe(
    bm_green: bmesh.types.BMesh,
    bm_white: bmesh.types.BMesh,
    y_center: float,
    off_w: float = -8.0,
    off_e: float = -0.22,
    width_y: float = 3.5,
    n_stripes: int = 5,
) -> None:
    """沿廣和街精準對齊、100% 位於柏油車道內（絕不壓上人行道）的綠底白色斑馬線！"""
    hy = width_y * 0.5
    _add_strip_along_guanghe(bm_green, y_center - hy, y_center + hy, off_w, off_e, 0.008, 0.018)
    stripe_h = width_y / (n_stripes * 2.05)
    span_y = width_y - 0.55
    for i in range(n_stripes):
        sy = y_center - span_y * 0.5 + span_y * i / max(1, n_stripes - 1)
        _add_strip_along_guanghe(bm_white, sy - stripe_h * 0.5, sy + stripe_h * 0.5, off_w + 0.16, off_e - 0.16, 0.012, 0.024)


def _add_clipped_yellow_grid_rect(
    bm: bmesh.types.BMesh,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    pitch: float = 1.90,
    border_w: float = 0.20,
    line_w: float = 0.13,
    z_top: float = 0.022,
) -> None:
    """軸對齊矩形精準裁切 45° 黃網線（用於西南角 92、五權街 30 巷、3 廣和街 B 24 弄，零超框突出！）。"""
    z0 = 0.008
    _quad_extrude(bm, [(x0, y0), (x1, y0), (x1, y0 + border_w), (x0, y0 + border_w)], z0, z_top)
    _quad_extrude(bm, [(x0, y1 - border_w), (x1, y1 - border_w), (x1, y1), (x0, y1)], z0, z_top)
    _quad_extrude(bm, [(x0, y0), (x0 + border_w, y0), (x0 + border_w, y1), (x0, y1)], z0, z_top)
    _quad_extrude(bm, [(x1 - border_w, y0), (x1, y0), (x1, y1), (x1 - border_w, y1)], z0, z_top)

    ax0, ax1 = x0 + border_w * 0.6, x1 - border_w * 0.6
    ay0, ay1 = y0 + border_w * 0.6, y1 - border_w * 0.6

    def add_seg(p0: Tuple[float, float], p1: Tuple[float, float]) -> None:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 0.15:
            return
        nx, ny = -dy / L * (line_w * 0.5), dx / L * (line_w * 0.5)
        _quad_extrude(bm, [(p0[0] - nx, p0[1] - ny), (p1[0] - nx, p1[1] - ny), (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)], z0, z_top)

    for sign in (1, -1):
        c_lo = (ax0 + ay0) if sign == 1 else (ax0 - ay1)
        c_hi = (ax1 + ay1) if sign == 1 else (ax1 - ay0)
        k = int(math.floor(c_lo / pitch))
        while k * pitch <= c_hi:
            c = k * pitch
            pts: List[Tuple[float, float]] = []
            for xt in (ax0, ax1):
                yt = (c - xt) if sign == 1 else (xt - c)
                if ay0 - 1e-5 <= yt <= ay1 + 1e-5:
                    pts.append((xt, max(ay0, min(ay1, yt))))
            for yt in (ay0, ay1):
                xt = (c - yt) if sign == 1 else (c + yt)
                if ax0 - 1e-5 <= xt <= ax1 + 1e-5:
                    pts.append((max(ax0, min(ax1, xt)), yt))
            uniq: List[Tuple[float, float]] = []
            for pt in pts:
                if all(math.hypot(pt[0] - q[0], pt[1] - q[1]) > 1e-3 for q in uniq):
                    uniq.append(pt)
            if len(uniq) == 2:
                add_seg(uniq[0], uniq[1])
            k += 1


def _add_green_crosswalk_ns(
    bm_green: bmesh.types.BMesh,
    bm_white: bmesh.types.BMesh,
    x_center: float,
    y0: float,
    y1: float,
    width_x: float = 3.4,
    n_stripes: int = 5,
) -> None:
    """跨東西向道路（南北通行）之綠底白色斑馬線（43 廣和街與 3 廣和街 B 後門旁！）。"""
    hx = width_x * 0.5
    _quad_extrude(bm_green, [(x_center - hx, y0), (x_center + hx, y0), (x_center + hx, y1), (x_center - hx, y1)], 0.008, 0.018)
    stripe_w = width_x / (n_stripes * 2.05)
    span_x = width_x - 0.55
    for i in range(n_stripes):
        sx = x_center - span_x * 0.5 + span_x * i / max(1, n_stripes - 1)
        _quad_extrude(bm_white, [(sx - stripe_w * 0.5, y0 + 0.18), (sx + stripe_w * 0.5, y0 + 0.18), (sx + stripe_w * 0.5, y1 - 0.18), (sx - stripe_w * 0.5, y1 - 0.18)], 0.012, 0.024)


def _add_curved_sidewalk_with_fillet(
    bm_pave: bmesh.types.BMesh,
    bm_curb: bmesh.types.BMesh,
    bm_red: bmesh.types.BMesh,
    y_start: float,
    y_end: float,
    fillet_south: bool = False,
    fillet_north: bool = False,
    fillet_r: float = 1.35,
    red_south_len: float = 0.0,
    red_north_len: float = 0.0,
    z_top: float = 0.135,
) -> None:
    """建置滿鋪至圍牆腳且端點帶真實圓弧導角水泥路緣石的人行道板塊（零白邊、零尖角！）。"""
    # Compute outer edge spine along curb_x(y) with smooth quarter-circle fillet turning east (+X) at gate opening
    curb_w = 0.30
    segs = 10
    pave_pts: List[Tuple[float, float]] = []
    curb_spine: List[Tuple[float, float]] = []

    if fillet_south:
        # Quarter-circle turning from east (+X inside gate) to north (+Y along curb)
        # Center of fillet arc at (curb_x(y_start + R) + R, y_start + R)
        r = fillet_r
        yc = y_start + r
        xc = curb_x(yc) + r
        for i in range(segs + 1):
            # angle from -90 deg (south-facing gate side) to 180 deg (west-facing curb side)?
            # Wait: at i=0, point is (xc, y_start) on south edge; at i=segs, point is (xc - r, yc) on west curb!
            a = -math.pi * 0.5 - (math.pi * 0.5) * (i / segs)
            px = xc + math.cos(a) * r
            py = yc + math.sin(a) * r
            curb_spine.append((px, py))
            pave_pts.append((px + curb_w * 0.7 * (-math.cos(a)), py + curb_w * 0.7 * (-math.sin(a))))
        # Add east wall start corner before arc
        pave_pts.insert(0, (wall_x(y_start), y_start))
        # Straight curb from (xc, y_start) to wall_x(y_start) along gate edge
        curb_spine.insert(0, (wall_x(y_start) - 0.15, y_start))
    else:
        pave_pts.append((wall_x(y_start), y_start))
        pave_pts.append((curb_x(y_start) + curb_w * 0.85, y_start))
        curb_spine.append((curb_x(y_start), y_start))

    if fillet_north:
        r = fillet_r
        yc = y_end - r
        xc = curb_x(yc) + r
        for i in range(segs + 1):
            # from west curb (180 deg) to north edge (90 deg)
            a = math.pi - (math.pi * 0.5) * (i / segs)
            px = xc + math.cos(a) * r
            py = yc + math.sin(a) * r
            curb_spine.append((px, py))
            pave_pts.append((px + curb_w * 0.7 * (-math.cos(a)), py + curb_w * 0.7 * (-math.sin(a))))
        curb_spine.append((wall_x(y_end) - 0.15, y_end))
        pave_pts.append((wall_x(y_end), y_end))
    else:
        curb_spine.append((curb_x(y_end), y_end))
        pave_pts.append((curb_x(y_end) + curb_w * 0.85, y_end))
        pave_pts.append((wall_x(y_end), y_end))

    _quad_extrude(bm_pave, pave_pts, 0.0, z_top)
    # Build curb along curb_spine: spine goes south->north (so inside/east is RIGHT normal = +dy, -dx -> wait!)
    # Check normal: for spine moving +Y (dx=0, dy=1), left normal (-dy, dx)=(-1, 0) is WEST (asphalt), right normal (+1, 0) is EAST (sidewalk)!
    # In _add_polyline_ribbon: off_left is along (-dy, dx)=WEST, off_right is along (+dy, -dx) when negative!
    # So off_left = 0.0 (exact outer curb edge), off_right = -curb_w (inward EAST into sidewalk)!
    _add_polyline_ribbon(bm_curb, curb_spine, 0.02, -curb_w, 0.0, z_top + 0.016)

    # Optional crisp red no-parking curb stripe along road-facing outer edge
    if red_south_len > 0.1:
        _add_strip_along_guanghe(bm_red, y_start + (fillet_r if fillet_south else 0.0), y_start + red_south_len, -0.18, -0.04, 0.008, 0.020)
    if red_north_len > 0.1:
        _add_strip_along_guanghe(bm_red, y_end - red_north_len, y_end - (fillet_r if fillet_north else 0.0), -0.18, -0.04, 0.008, 0.020)


def _add_granite_bollard(bm_granite: bmesh.types.BMesh, bm_groove: bmesh.types.BMesh, x: float, y: float, z0: float = 0.135) -> None:
    """還原 27 廣和街實景深暖灰花崗岩磨石子圓柱車阻（頂部圓倒角＋上段兩道深色凹槽環！）。"""
    r = 0.135
    h = 0.64
    gp.bm_cyl_axis(bm_granite, (x, y, z0 + h * 0.44), r, h * 0.88, axis="Z", segments=16)
    # Slight rounded dome cap
    gp.bm_cyl_p2p(bm_granite, (x, y, z0 + h * 0.88), (x, y, z0 + h), r, r * 0.78, segments=16)
    # Two iconic recessed dark groove rings near upper shaft (visible clearly in step_113 & step_135!)
    for gz in (z0 + h * 0.72, z0 + h * 0.80):
        gp.bm_cyl_axis(bm_groove, (x, y, gz), r + 0.004, 0.022, axis="Z", segments=16)


def _add_stadium_ring_prism(
    bm: bmesh.types.BMesh,
    cx: float,
    cy: float,
    straight_len: float,
    r_inner: float,
    r_outer: float,
    z_bot: float,
    z_top: float,
    segs_arc: int = 32,
) -> None:
    half_s = straight_len * 0.5

    def _stadium_pts(r: float) -> List[Tuple[float, float]]:
        pts: List[Tuple[float, float]] = []
        for i in range(segs_arc + 1):
            a = math.pi * i / segs_arc
            pts.append((cx + math.cos(a) * r, cy + half_s + math.sin(a) * r))
        for i in range(segs_arc + 1):
            a = math.pi + math.pi * i / segs_arc
            pts.append((cx + math.cos(a) * r, cy - half_s + math.sin(a) * r))
        return pts

    outer_pts = _stadium_pts(r_outer)
    n = len(outer_pts)

    if r_inner <= 1e-4:
        v_bot = [bm.verts.new((x, y, z_bot)) for x, y in outer_pts]
        v_top = [bm.verts.new((x, y, z_top)) for x, y in outer_pts]
        bm.faces.new(v_top)
        bm.faces.new(list(reversed(v_bot)))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((v_bot[i], v_bot[j], v_top[j], v_top[i]))
    else:
        inner_pts = _stadium_pts(r_inner)
        vo_b = [bm.verts.new((x, y, z_bot)) for x, y in outer_pts]
        vo_t = [bm.verts.new((x, y, z_top)) for x, y in outer_pts]
        vi_b = [bm.verts.new((x, y, z_bot)) for x, y in inner_pts]
        vi_t = [bm.verts.new((x, y, z_top)) for x, y in inner_pts]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vi_t[i], vo_t[i], vo_t[j], vi_t[j]))
            bm.faces.new((vo_b[i], vo_b[j], vo_t[j], vo_t[i]))
            bm.faces.new((vi_b[j], vi_b[i], vi_t[i], vi_t[j]))


def _add_organic_tree(
    bm_trunk: bmesh.types.BMesh,
    bm_fol_list: List[bmesh.types.BMesh],
    x: float,
    y: float,
    h: float,
    r_crown: float,
    rng: random.Random,
) -> None:
    """D-06：高質感有機細碎葉叢喬木（多分支主幹＋9團錯落葉叢＋頂點微噪點擾動消除光滑氣球感）。"""
    trunk_h = h * 0.44
    lean_x = rng.uniform(-0.35, 0.35)
    lean_y = rng.uniform(-0.35, 0.35)
    top_trunk = (x + lean_x, y + lean_y, trunk_h)
    gp.bm_cyl_p2p(bm_trunk, (x, y, 0.0), top_trunk, 0.28, 0.17, segments=8)

    def _add_ruffled_tuft(bm_c: bmesh.types.BMesh, center: tuple[float, float, float], rx: float, ry: float, rz: float) -> None:
        ret = bmesh.ops.create_icosphere(bm_c, subdivisions=2, radius=1.0)
        cx, cy, cz = center
        for v in ret["verts"]:
            # Deterministic organic leaf-cluster surface bumpiness (breaks smooth balloon look!)
            n = 1.0 + 0.16 * math.sin(v.co.x * 7.3 + cx) * math.cos(v.co.y * 6.9 + cy) + rng.uniform(-0.08, 0.08)
            v.co.x = cx + v.co.x * rx * n
            v.co.y = cy + v.co.y * ry * n
            v.co.z = cz + v.co.z * rz * n

    n_branches = 5
    base_ang = rng.uniform(0.0, math.pi * 2.0)
    z_crown = trunk_h + r_crown * 0.45
    for i in range(n_branches):
        ang = base_ang + i * (2.0 * math.pi / n_branches) + rng.uniform(-0.25, 0.25)
        dist = r_crown * rng.uniform(0.45, 0.68)
        bx = top_trunk[0] + math.cos(ang) * dist
        by = top_trunk[1] + math.sin(ang) * dist
        bz = trunk_h + r_crown * rng.uniform(0.28, 0.56)
        gp.bm_cyl_p2p(bm_trunk, (top_trunk[0], top_trunk[1], trunk_h * 0.85), (bx, by, bz), 0.12, 0.055, segments=6)
        bm_c = bm_fol_list[(i + rng.randint(0, 2)) % len(bm_fol_list)]
        sc = r_crown * rng.uniform(0.46, 0.64)
        _add_ruffled_tuft(bm_c, (bx, by, bz + sc * 0.25), sc * 1.12, sc * 1.04, sc * 0.78)

    for dz, sc, bm_idx in [
        (r_crown * 0.48, r_crown * 0.68, 1),
        (r_crown * 0.12, r_crown * 0.74, 0),
        (r_crown * 0.78, r_crown * 0.48, 2),
        (r_crown * 0.34, r_crown * 0.52, 2),
    ]:
        bm_c = bm_fol_list[bm_idx % len(bm_fol_list)]
        ox, oy = rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45)
        _add_ruffled_tuft(bm_c, (top_trunk[0] + ox, top_trunk[1] + oy, z_crown + dz), sc * 1.08, sc, sc * 0.74)


def _add_royal_palm(
    bm_palm_trunk: bmesh.types.BMesh,
    bm_sheath: bmesh.types.BMesh,
    bm_frond: bmesh.types.BMesh,
    x: float,
    y: float,
    h: float = 11.0,
    seed: int = 0,
) -> None:
    """高細節大王椰子／酒瓶椰子（還原 final_step_32.png 與 campus_08.jpg：微膨灰白樹幹＋亮綠葉鞘＋14片三段彎曲羽葉）。"""
    rng = random.Random(seed + int(x * 13 + y * 7))
    # Slightly swollen lower/mid trunk + taper to crownshaft
    h1, h2, h3 = h * 0.18, h * 0.78, h * 0.94
    gp.bm_cyl_p2p(bm_palm_trunk, (x, y, 0.0), (x, y, h1), 0.36, 0.42, segments=10)
    gp.bm_cyl_p2p(bm_palm_trunk, (x, y, h1), (x, y, h2), 0.42, 0.25, segments=10)
    # Bright green smooth crownshaft (葉鞘)
    gp.bm_cyl_p2p(bm_sheath, (x, y, h2), (x, y, h3), 0.26, 0.21, segments=10)

    # 14 arching 3-segment pinnate fronds in 2 whorls (upper ascending, lower drooping)
    crown_z = h3 - 0.15
    for tier, n_fronds, base_pitch, length in [
        (0, 8, 22.0, 2.85),   # lower sweeping fronds
        (1, 6, 48.0, 2.35),   # upper lively fronds
    ]:
        for k in range(n_fronds):
            ang = k * (2.0 * math.pi / n_fronds) + tier * 0.42 + rng.uniform(-0.12, 0.12)
            dx, dy = math.cos(ang), math.sin(ang)
            # 3 curved segments per frond tapering to tip
            p0 = Vector((x, y, crown_z + tier * 0.28))
            pitches = [base_pitch, base_pitch - 32.0, base_pitch - 66.0]
            seg_lens = [length * 0.34, length * 0.36, length * 0.32]
            seg_widths = [0.68, 0.56, 0.28]
            curr = p0
            for s_idx in range(3):
                pr = math.radians(pitches[s_idx])
                sl = seg_lens[s_idx]
                nxt = curr + Vector((dx * math.cos(pr) * sl, dy * math.cos(pr) * sl, math.sin(pr) * sl))
                mid = (curr + nxt) * 0.5
                # Flattened leaf blade segment oriented along frond tangent
                gp.bm_box(bm_frond, (mid.x, mid.y, mid.z), (sl + 0.08, seg_widths[s_idx], 0.055), rot_y=-pr, rot_z=ang)
                curr = nxt


def build_base_roads_and_city(spec: dict, palette: Dict[str, bpy.types.Material], show_sat_ref: bool = False, include_horizon: bool = False) -> List[bpy.types.Object]:
    """建立修齊邊界之基地展示台、廣和街 v8 精準斜率路面標線、圓弧轉角人行道、透明智慧停車格與花崗岩街具。"""
    col = "Base_Ground"
    objs: List[bpy.types.Object] = []

    # Base architectural slab sunk slightly below road asphalt (z_top=-0.04) so it NEVER bleeds white edges onto roads/sidewalks!
    bm_surr = bmesh.new()
    gp.bm_box(bm_surr, (-6.0, 10.0, -0.22), (206.0, 214.0, 0.36))
    objs.append(su.create_mesh_object("Base_SurroundingGround", bm_surr, palette["sidewalk"], col, uv_scale=0.12))

    if include_horizon:
        bm_hor = bmesh.new()
        gp.bm_box(bm_hor, (0.0, 0.0, -0.45), (1400.0, 1400.0, 0.08))
        objs.append(su.create_mesh_object("Base_CyclesHorizon", bm_hor, palette["horizon_ground"], col))

    # Inner campus red-brick / courtyard paving clipped cleanly INSIDE west wall_x(y)
    bm_brick_pave = bmesh.new()
    _quad_extrude(
        bm_brick_pave,
        [
            (wall_x(-30.0) + 0.1, -30.0),
            (-52.0, -30.0),
            (-52.0, 38.5),
            (wall_x(38.5) + 0.1, 38.5),
        ],
        -0.05,
        0.04,
    )
    gp.bm_box(bm_brick_pave, (13.8, -12.0, -0.02), (16.5, 108.0, 0.08))
    gp.bm_box(bm_brick_pave, (-25.0, -19.0, -0.02), (46.0, 22.0, 0.06))
    gp.bm_box(bm_brick_pave, (42.0, -12.0, -0.03), (50.0, 102.0, 0.06))
    objs.append(su.create_mesh_object("Base_CampusPaving", bm_brick_pave, palette["paving_redbrick"], col, uv_scale=0.45))

    # v12.11 27 廣和街 Inner Main Gate Forecourt Warm-Cream Square-Tile Plaza with White Geometric Guiding Lines (step_22_shot_1.png & step_18_shot_1.png!)
    bm_forecourt = bmesh.new()
    _quad_extrude(
        bm_forecourt,
        [
            (wall_x(-29.2) + 0.45, -29.2),
            (-51.2, -29.2),
            (-51.2, 16.5),
            (wall_x(16.5) + 0.45, 16.5),
        ],
        0.005,
        0.046,
    )
    objs.append(su.create_mesh_object("Base_ForecourtPlaza", bm_forecourt, palette["forecourt_plaza"], col, uv_scale=0.065))

    # === 1. Asphalt Road Network (Exact +8.5° West Guanghe St + widened South Guanghe St & East Wuquan St!) ===
    bm_road = bmesh.new()
    # West Guanghe St (extended to y=-84 so SW intersection asphalt is 100% seamless!)
    _add_strip_along_guanghe(bm_road, -84.0, 52.0, -13.8, 0.35, -0.06, 0.008)
    # South Guanghe St (y=-84.0..-72.9, x=-96.0..+88.0) + corner asphalt underlays so SW/SE curved curbs NEVER expose gray gaps!
    _quad_extrude(bm_road, [(-96.0, -84.0), (88.0, -84.0), (88.0, SOUTH_CURB_Y + 0.30), (-96.0, SOUTH_CURB_Y + 0.30)], -0.06, 0.008)
    _quad_extrude(bm_road, [(-96.0, -84.0), (-71.0, -84.0), (-71.0, -66.0), (-96.0, -66.0)], -0.06, 0.007)
    _quad_extrude(bm_road, [(66.0, -84.0), (88.0, -84.0), (88.0, -61.5), (66.0, -61.5)], -0.06, 0.007)
    # North Heping Rd (v11 exact +4.28° slope matching NW/NE corners!) + East Wuquan St (-3.2°) + NW/NE intersection underlays!
    _add_strip_along_heping(bm_road, -88.0, 88.0, -0.35, 10.60, -0.06, 0.008)
    _quad_extrude(bm_road, [(-86.0, 34.0), (-58.0, 34.0), (-58.0, 56.0), (-86.0, 56.0)], -0.06, 0.007)
    _add_strip_along_wuquan(bm_road, -84.0, 68.0, -0.35, 14.5, -0.06, 0.008)
    _quad_extrude(bm_road, [(58.0, 44.0), (88.0, 44.0), (88.0, 68.0), (58.0, 68.0)], -0.06, 0.007)
    objs.append(su.create_mesh_object("Base_Roads_Asphalt", bm_road, palette["asphalt"], col, uv_scale=0.22))

    # === 2. Sidewalks with TRUE Curved Corner Fillets, Weathered Curbs & Red Curb Lines ===
    bm_checker = bmesh.new()
    bm_south_walk = bmesh.new()
    bm_gate_ext = bmesh.new()
    bm_nw_plaza = bmesh.new()
    bm_curb = bmesh.new()
    bm_red = bmesh.new()
    bm_tactile = bmesh.new()

    # (a) North Guanghe Checkerboard Sidewalk (y=+8.8..+35.6) + Dark Washed-Stone Tree-Pit Zone (y=+6.95..+8.8, step_22_shot_1.png!)
    _add_curved_sidewalk_with_fillet(
        bm_checker, bm_curb, bm_red,
        y_start=8.8, y_end=35.6,
        fillet_south=False, fillet_north=False, fillet_r=1.35,
        red_south_len=4.2, red_north_len=10.0, z_top=0.135,
    )
    _add_curved_sidewalk_with_fillet(
        bm_south_walk, bm_curb, bm_red,
        y_start=6.95, y_end=8.85,
        fillet_south=True, fillet_north=False, fillet_r=1.15,
        red_south_len=1.8, red_north_len=0.0, z_top=0.136,
    )
    # (b) South Guanghe Checkerboard Sidewalk (y=-31.0..-14.8, starting south of School Sign Wall!)
    _add_curved_sidewalk_with_fillet(
        bm_checker, bm_curb, bm_red,
        y_start=-31.0, y_end=-14.8,
        fillet_south=False, fillet_north=False, fillet_r=1.35,
        red_south_len=5.4, red_north_len=0.0, z_top=0.135,
    )
    # School Sign Wall Front Sidewalk (y=-14.8..-3.8, Red-Brick Paver w/ Gray Geometric Border Bands matching final_step_30.png bottom-right!)
    _add_curved_sidewalk_with_fillet(
        bm_gate_ext, bm_curb, bm_red,
        y_start=-14.8, y_end=-3.8,
        fillet_south=False, fillet_north=True, fillet_r=1.25,
        red_south_len=0.0, red_north_len=8.4, z_top=0.135,
    )
    # (b2) East Wuquan St Full-Width (3.3m) Checkerboard Sidewalk (2/9/1/中北段 五權街, y=-62.5..+45.5!)
    _add_strip_along_wuquan(bm_checker, -62.5, 45.5, -EAST_SIDEWALK_W, -0.28, 0.0, 0.135)
    _add_strip_along_wuquan(bm_curb, -62.5, 45.5, -0.30, 0.02, 0.0, 0.150)
    objs.append(su.create_mesh_object("Base_GuangheSidewalk_Checker", bm_checker, palette["sidewalk_checker"], col, uv_scale=0.58))

    # (c) Main Gate Driveway Apron (y=-3.82..+5.18 Red-Brick + Gray Paver Geometric Grid) & North Pedestrian Gate Light-Cream Stone Slab Ramp (y=+5.18..+6.95, step_22_shot_1.png!)
    bm_gate_ped = bmesh.new()
    bm_gate_gray = bmesh.new()
    bm_gate_track = bmesh.new()
    _add_strip_along_guanghe(bm_gate_ext, -3.82, 5.18, -0.05, SIDEWALK_W + 0.45, 0.0, 0.048)
    _add_strip_along_guanghe(bm_curb, -3.82, 6.95, -0.22, 0.02, 0.0, 0.032)
    # 4-row wide light-cream large square stone slab walkway leading straight through open pedestrian gate (y=+5.18..+6.95!)
    _add_strip_along_guanghe(bm_gate_ped, 5.18, 6.95, 0.05, SIDEWALK_W + 1.95, 0.005, 0.054)
    # Gray concrete border strips flanking the pedestrian stone-slab ramp + geometric gray paver grid bands across red-brick driveway & school-sign sidewalk!
    _add_strip_along_guanghe(bm_gate_gray, 5.02, 5.20, 0.02, SIDEWALK_W + 1.95, 0.006, 0.055)
    _add_strip_along_guanghe(bm_gate_gray, 6.88, 7.04, 0.02, SIDEWALK_W + 1.45, 0.006, 0.055)
    # Roadside 3-course gray paver header band & 2 longitudinal gray paver bands across main gate driveway (step_18_shot_1.png!)
    for off_g0, off_g1 in [(0.02, 0.56), (1.78, 2.14), (3.36, 3.72), (4.58, 5.12)]:
        _add_strip_along_guanghe(bm_gate_gray, -3.80, 5.18, off_g0, off_g1, 0.006, 0.052)
    # Transverse gray paver divider bands forming crisp rectangular bays on driveway & school-sign sidewalk (final_step_30.png!)
    for y_gb in (-2.05, 0.55, 2.95):
        _add_strip_along_guanghe(bm_gate_gray, y_gb - 0.18, y_gb + 0.18, 0.54, 4.62, 0.006, 0.052)
    # Gray paver border frame around School Sign Wall red-brick sidewalk (y=-14.8..-3.8, final_step_30.png bottom-right!)
    _add_strip_along_guanghe(bm_gate_gray, -14.75, -3.95, 0.30, 0.62, 0.006, 0.138)
    _add_strip_along_guanghe(bm_gate_gray, -14.75, -3.95, 3.35, 3.72, 0.006, 0.138)
    for y_sb in (-13.2, -10.2, -7.2, -4.3):
        _add_strip_along_guanghe(bm_gate_gray, y_sb - 0.18, y_sb + 0.18, 0.58, 3.40, 0.006, 0.138)
    # Sliding iron gate dark metal ground track rail at gate threshold
    _add_strip_along_guanghe(bm_gate_track, -3.65, 5.15, 4.92, 5.06, 0.008, 0.056)

    objs.append(su.create_mesh_object("Base_GateCurbExtension_RedBrick", bm_gate_ext, palette["paving_redbrick"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Base_GatePedestrian_StoneSlabs", bm_gate_ped, palette["gate_ped_slab"], col, uv_scale=0.42))
    objs.append(su.create_mesh_object("Base_GateApron_GrayBands", bm_gate_gray, palette["walkway_gray_paver"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Base_GateThreshold_Track", bm_gate_track, palette["metal_dark"], col))

    # (d) West-South Gray Concrete Sidewalk (60 / 78 / 88 廣和街, y=-66.5..-31.0)
    _add_curved_sidewalk_with_fillet(
        bm_south_walk, bm_curb, bm_red,
        y_start=-66.5, y_end=-31.0,
        fillet_south=False, fillet_north=False,
        red_south_len=0.0, red_north_len=11.0, z_top=0.135,
    )

    # (d2) 92 廣和街 SW GRAND CURVED CORNER SIDEWALK — Diagonal Red-Brown Brick + Driveway Ramp + Tactile Yellow (step_145!)
    sw_p0 = (curb_x(-66.5), -66.5)       # (-86.06, -66.50)
    sw_pc = (curb_x(SOUTH_CURB_Y), SOUTH_CURB_Y)  # (-87.07, -73.20)
    sw_p2 = (-71.6, SOUTH_CURB_Y)        # (-71.60, -73.20)
    sw_spine: List[Tuple[float, float]] = []
    for i in range(17):
        t = i / 16.0
        omt = 1.0 - t
        sw_spine.append((
            omt * omt * sw_p0[0] + 2 * omt * t * sw_pc[0] + t * t * sw_p2[0],
            omt * omt * sw_p0[1] + 2 * omt * t * sw_pc[1] + t * t * sw_p2[1],
        ))
    # Moving south then east -> left normal is INWARD (campus NE), right normal (negative) is OUTWARD (SW road)!
    _add_polyline_ribbon(bm_curb, sw_spine, 0.34, -0.02, 0.0, 0.150)
    _add_polyline_ribbon(bm_red, sw_spine, -0.06, -0.22, 0.008, 0.020)
    sw_pave_outer: List[Tuple[float, float]] = []
    for i in range(len(sw_spine)):
        p_prev = sw_spine[max(0, i - 1)]
        p_next = sw_spine[min(len(sw_spine) - 1, i + 1)]
        dx, dy = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
        L = max(1e-6, math.hypot(dx, dy))
        ix, iy = -dy / L, dx / L  # left normal = inward NE!
        sw_pave_outer.append((sw_spine[i][0] + ix * 0.28, sw_spine[i][1] + iy * 0.28))
    sw_pave_poly = sw_pave_outer + [(-71.6, SOUTH_WALL_Y), (wall_x(-69.8), SOUTH_WALL_Y), (wall_x(-66.5), -66.5)]
    _quad_extrude(bm_nw_plaza, sw_pave_poly, 0.0, 0.135)
    # Diagonal light-gray stone-paver driveway apron slanting SW from WEST-facing garage shutter to SW curved curb (exact final_step_14!)
    _quad_extrude(
        bm_curb,
        [
            (sw_spine[6][0] + 0.25, sw_spine[6][1] + 0.25),
            (sw_spine[11][0] + 0.20, sw_spine[11][1] + 0.30),
            (-81.8, -69.5),
            (-81.3, -65.7),
        ],
        0.0,
        0.141,
    )
    # SW Corner L-shaped Yellow Tactile paving running along south of garage portal toward 43 廣和街 green crosswalk (final_step_14!)
    gp.bm_box(bm_tactile, (-76.2, -71.35, 0.141), (8.6, 0.55, 0.014))
    gp.bm_box(bm_tactile, (-72.0, -72.05, 0.141), (0.55, 1.85, 0.014))

    # (d3) South Guanghe St Full-Width (3.4m) Gray Concrete Tile Sidewalk + Gate 3 Diagonal Brick (x=+6.8..+20.0) + SE Grand Curved Corner!
    # West-to-Gate-3 gray sidewalk (x=-71.6..+6.8)
    _quad_extrude(bm_south_walk, [(-71.6, SOUTH_CURB_Y + 0.28), (6.8, SOUTH_CURB_Y + 0.28), (6.8, SOUTH_WALL_Y), (-71.6, SOUTH_WALL_Y)], 0.0, 0.135)
    # Gate 3 (3 廣和街) Diagonal Red-Brown Brick plaza + LEFT-side L-shaped Yellow Tactile guiding to green crosswalk (x=+6.8..+20.0, final_step_15!)
    _quad_extrude(bm_nw_plaza, [(6.8, SOUTH_CURB_Y + 0.28), (20.0, SOUTH_CURB_Y + 0.28), (20.0, SOUTH_WALL_Y), (6.8, SOUTH_WALL_Y)], 0.0, 0.135)
    gp.bm_box(bm_tactile, (9.8, -71.30, 0.141), (4.2, 0.56, 0.014))
    gp.bm_box(bm_tactile, (8.0, -72.10, 0.141), (0.56, 1.75, 0.014))
    # Gate-3-to-SE-corner gray sidewalk (x=+20.0..+66.5)
    _quad_extrude(bm_south_walk, [(20.0, SOUTH_CURB_Y + 0.28), (66.5, SOUTH_CURB_Y + 0.28), (66.5, SOUTH_WALL_Y), (20.0, SOUTH_WALL_Y)], 0.0, 0.135)
    # Continuous South Guanghe St weathered concrete curb (x=-71.6..+66.5)
    _quad_extrude(bm_curb, [(-71.6, SOUTH_CURB_Y), (66.5, SOUTH_CURB_Y), (66.5, SOUTH_CURB_Y + 0.30), (-71.6, SOUTH_CURB_Y + 0.30)], 0.0, 0.150)

    # (d4) 12 廣和街 SE GRAND CURVED CORNER SIDEWALK — Diagonal Red-Brown Brick + Curved Curb & Red Line (final_step_157!)
    se_p0 = (66.5, SOUTH_CURB_Y)
    se_pc = (76.8, SOUTH_CURB_Y)
    se_p2 = (76.8, -62.5)
    se_spine: List[Tuple[float, float]] = []
    for i in range(17):
        t = i / 16.0
        omt = 1.0 - t
        se_spine.append((
            omt * omt * se_p0[0] + 2 * omt * t * se_pc[0] + t * t * se_p2[0],
            omt * omt * se_p0[1] + 2 * omt * t * se_pc[1] + t * t * se_p2[1],
        ))
    # Moving east then north -> left normal is INWARD (campus NW), right normal (negative) is OUTWARD (SE road)!
    _add_polyline_ribbon(bm_curb, se_spine, 0.34, -0.02, 0.0, 0.150)
    _add_polyline_ribbon(bm_red, se_spine, -0.06, -0.22, 0.008, 0.020)
    se_pave_outer: List[Tuple[float, float]] = []
    for i in range(len(se_spine)):
        p_prev = se_spine[max(0, i - 1)]
        p_next = se_spine[min(len(se_spine) - 1, i + 1)]
        dx, dy = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
        L = max(1e-6, math.hypot(dx, dy))
        ix, iy = -dy / L, dx / L  # left normal = inward NW!
        se_pave_outer.append((se_spine[i][0] + ix * 0.28, se_spine[i][1] + iy * 0.28))
    # Inner arc matches SE curved wall (center (66.5, -62.8), R=7.0 -> from (66.5, -69.8) to (73.5, -62.8))
    se_wall_inner: List[Tuple[float, float]] = []
    for i in range(12, -1, -1):
        a = -math.pi * 0.5 + (math.pi * 0.5) * (i / 12.0)
        se_wall_inner.append((66.5 + math.cos(a) * 7.0, -62.8 + math.sin(a) * 7.0))
    _quad_extrude(bm_nw_plaza, se_pave_outer + se_wall_inner, 0.0, 0.135)
    # SE corner tactile guide strip & L-shaped tactile guiding toward East Wuquan St crosswalk (2 五權街 step_163!)
    gp.bm_box(bm_tactile, (73.4, -70.6, 0.141), (2.4, 0.55, 0.014), rot_z=math.radians(38.0))
    gp.bm_box(bm_tactile, (74.8, -65.2, 0.141), (3.4, 0.55, 0.014), rot_z=math.radians(-18.0))

    # (d5) 15 五權街 NE GRAND CURVED CORNER SIDEWALK (Gray concrete curved accessible apron, step_180 & final_step_182!)
    ne_p0 = (east_curb_x(45.5), 45.5)      # (70.75, 45.50) — seamless join with Wuquan checkerboard!
    ne_pc = (70.27, 54.12)                 # Exact Wuquan curb / Heping curb intersection!
    ne_p2 = (60.5, 52.84)                  # Exact Heping Rd south curb at x=60.5!
    ne_spine: List[Tuple[float, float]] = []
    for i in range(17):
        t = i / 16.0
        omt = 1.0 - t
        ne_spine.append((
            omt * omt * ne_p0[0] + 2 * omt * t * ne_pc[0] + t * t * ne_p2[0],
            omt * omt * ne_p0[1] + 2 * omt * t * ne_pc[1] + t * t * ne_p2[1],
        ))
    # Moving north then west -> left normal (-dy, dx) is INWARD (campus SW), right normal (negative) is OUTWARD (NE road)!
    _add_polyline_ribbon(bm_curb, ne_spine, 0.34, -0.02, 0.0, 0.150)
    _add_polyline_ribbon(bm_red, ne_spine, -0.06, -0.22, 0.008, 0.020)
    ne_pave_outer: List[Tuple[float, float]] = []
    for i in range(len(ne_spine)):
        p_prev = ne_spine[max(0, i - 1)]
        p_next = ne_spine[min(len(ne_spine) - 1, i + 1)]
        dx, dy = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
        L = max(1e-6, math.hypot(dx, dy))
        ix, iy = -dy / L, dx / L  # left normal = inward SW!
        ne_pave_outer.append((ne_spine[i][0] + ix * 0.28, ne_spine[i][1] + iy * 0.28))
    ne_poly = ne_pave_outer + [
        (60.5, heping_south_edge_y(60.5) - HEPING_EAST_WALK_W),
        (east_wall_x(47.8), 47.8),
        (east_wall_x(45.5), 45.5),
    ]
    _quad_extrude(bm_south_walk, ne_poly, 0.0, 0.135)
    # v11.3 Heping Rd East Segment (166 / 147 和平路, x=+6.6..+60.5): authentic 1.65m narrow concrete sidewalk + 147 B side-gate apron!
    _add_strip_along_heping(bm_south_walk, 6.6, 60.5, -HEPING_EAST_WALK_W, -0.26, 0.0, 0.130)
    _add_strip_along_heping(bm_south_walk, 6.6, 10.8, -HEPING_EAST_WALK_W - 2.6, -HEPING_EAST_WALK_W + 0.05, 0.0, 0.125)
    # Opposite north-side Heping Rd sidewalk strip (166/147/129 對側北人行道與運動中心前庭邊帶)
    _add_strip_along_heping(bm_south_walk, -60.5, 60.5, 10.65, 12.80, 0.0, 0.125)
    objs.append(su.create_mesh_object("Base_GuangheSidewalk_SouthGray", bm_south_walk, palette["sidewalk_south"], col, uv_scale=0.45))

    # (e) 10 廣和街 NW GRAND CURVED CORNER SIDEWALK (100% matching step_111_shot_1_sv_1_10_guanghe.png!)
    nw_p0 = (curb_x(35.6), 35.6)
    nw_pc = (-69.85, 43.15)
    nw_p2 = (-60.5, heping_curb_y(-60.5))
    nw_spine: List[Tuple[float, float]] = []
    for i in range(19):
        t = i / 18.0
        omt = 1.0 - t
        nw_spine.append((
            omt * omt * nw_p0[0] + 2 * omt * t * nw_pc[0] + t * t * nw_p2[0],
            omt * omt * nw_p0[1] + 2 * omt * t * nw_pc[1] + t * t * nw_p2[1],
        ))
    _add_polyline_ribbon(bm_curb, nw_spine, 0.02, -0.38, 0.0, 0.152)
    _add_polyline_ribbon(bm_red, nw_spine, 0.22, 0.06, 0.008, 0.020)
    nw_pave_outer: List[Tuple[float, float]] = []
    for i in range(len(nw_spine)):
        p_prev = nw_spine[max(0, i - 1)]
        p_next = nw_spine[min(len(nw_spine) - 1, i + 1)]
        dx, dy = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
        L = max(1e-6, math.hypot(dx, dy))
        ix, iy = dy / L, -dx / L
        nw_pave_outer.append((nw_spine[i][0] + ix * 0.30, nw_spine[i][1] + iy * 0.30))
    nw_pave_poly = nw_pave_outer + [(-60.5, 40.35), (-65.2, 39.65), (wall_x(35.6), 35.6)]
    _quad_extrude(bm_nw_plaza, nw_pave_poly, 0.0, 0.135)
    objs.append(su.create_mesh_object("Base_NWCornerPlaza_DiagBrick", bm_nw_plaza, palette["sidewalk_diag_brick"], col, uv_scale=0.45))

    # v11.3 Heping Rd South Curb & Red Lines:
    #   - East segment (x=+6.6..+60.5): concrete curb along 1.65m track sidewalk
    #   - West segment (x=-60.5..+6.6): low concrete lawn border flush with boulders & green B1 ramp!
    #   - Opposite north curb (x=-60.5..+60.5) & continuous red no-parking curb lines!
    _add_strip_along_heping(bm_curb, 6.6, 60.5, -0.28, 0.02, 0.0, 0.145)
    _add_strip_along_heping(bm_curb, -60.5, 6.6, -0.18, 0.00, 0.0, 0.055)
    _add_strip_along_heping(bm_curb, -60.5, 60.5, 10.42, 10.72, 0.0, 0.145)
    _add_strip_along_heping(bm_red, -60.5, 60.5, 0.06, 0.22, 0.008, 0.020)
    _add_strip_along_heping(bm_red, -60.5, 60.5, 10.20, 10.36, 0.008, 0.020)
    # 129 和平路 D / B / 166 和平路 White-concrete-framed rectangular storm drain pads right beside red line!
    for dx_hp in (-58.2, -19.2, 24.5, 53.5):
        _add_strip_along_heping(bm_curb, dx_hp - 0.85, dx_hp + 0.85, -0.45, 0.24, 0.0, 0.028)
    # East Wuquan St Red Curb Lines:
    #   (1) SE crosswalk north stub (-62.5..-58.0)
    #   (2) 1 五權街 green crosswalk & yellow grid zone (-23.8..-8.2)
    #   (3) North of smart parking bay 01 to NE curved corner (+40.8..+45.5)
    for ry0, ry1 in [(-62.5, -57.8), (-23.8, -8.2), (40.8, 45.5)]:
        _add_strip_along_wuquan(bm_red, ry0, ry1, 0.04, 0.20, 0.008, 0.020)
    # South Guanghe St Red Curb Lines:
    #   (1) East of 43 廣和街 crosswalk to disabled bay (-67.8..-62.4)
    #   (2) Wuquan St Ln 30 intersection (-26.2..-13.8)
    #   (3) East of scooter row through Back Gate all the way to SE corner (+14.2..+66.5!)
    #   (4) Opposite south road edge red line (-68.0..+72.0 at y=-83.2) for authentic street framing!
    for rx0, rx1 in [(-67.8, -62.4), (-26.2, -13.8), (5.2, 66.5)]:
        _quad_extrude(bm_red, [(rx0, SOUTH_CURB_Y - 0.20), (rx1, SOUTH_CURB_Y - 0.20), (rx1, SOUTH_CURB_Y - 0.05), (rx0, SOUTH_CURB_Y - 0.05)], 0.008, 0.020)
    _quad_extrude(bm_red, [(-68.0, -83.35), (74.0, -83.35), (74.0, -83.18), (-68.0, -83.18)], 0.008, 0.020)

    # NW Corner L-shaped Yellow Tactile Paving + Utility Inspection Hatch
    gp.bm_box(bm_tactile, (-68.25, 38.65, 0.141), (0.62, 3.0, 0.014), rot_z=GUANGHE_ROT_Z)
    gp.bm_box(bm_tactile, (-67.15, 39.95, 0.141), (2.75, 0.62, 0.014), rot_z=GUANGHE_ROT_Z)
    objs.append(su.create_mesh_object("Base_NWCorner_TactileYellow", bm_tactile, palette["tactile_yellow"], col))
    gp.bm_box(bm_curb, (-64.1, 41.4, 0.140), (0.95, 0.72, 0.012), rot_z=math.radians(7.5))

    objs.append(su.create_mesh_object("Base_GuangheCurbs_Unified", bm_curb, palette["curb_concrete"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Base_RoadMark_RedCurb", bm_red, palette["road_red"], col))

    # === 3. Crisp Road Markings: Clipped Yellow Grids, Green Crosswalks, Stop Lines & Segmented Double-Yellow ===
    bm_yellow = bmesh.new()
    bm_green = bmesh.new()
    bm_white = bmesh.new()

    # West Front Markings (Main Gate, 10 NW Corner, 60 Alley, 88 SW)
    _add_clipped_yellow_grid(bm_yellow, y_center=1.5, half_len_y=4.25, off_w=-8.0, off_e=-0.30, pitch=1.90)
    _add_green_crosswalk_guanghe(bm_green, bm_white, y_center=7.75, off_w=-8.0, off_e=-0.28, width_y=3.3, n_stripes=5)
    _add_green_crosswalk_guanghe(bm_green, bm_white, y_center=-4.75, off_w=-8.0, off_e=-0.28, width_y=3.3, n_stripes=5)
    _add_strip_along_guanghe(bm_white, -10.0, -9.52, -5.08, -0.32, 0.010, 0.022)
    _add_green_crosswalk_guanghe(bm_green, bm_white, y_center=37.6, off_w=-9.2, off_e=-0.35, width_y=3.5, n_stripes=5)
    _add_green_crosswalk_heping(bm_green, bm_white, x_center=-63.4, off_s=0.28, off_n=10.16, width_x=3.5, n_stripes=5)
    _add_clipped_yellow_grid(bm_yellow, y_center=-36.6, half_len_y=4.0, off_w=-8.2, off_e=-0.30, pitch=1.90)
    _add_green_crosswalk_guanghe(bm_green, bm_white, y_center=-30.4, off_w=-8.2, off_e=-0.28, width_y=3.3, n_stripes=5)
    _add_green_crosswalk_guanghe(bm_green, bm_white, y_center=-43.2, off_w=-8.2, off_e=-0.28, width_y=3.3, n_stripes=5)

    # South Guanghe St Markings (92 SW Corner -> 43 -> 76 -> 3 A/B Back Gate -> 12 SE Corner!)
    # (1) 92 廣和街 SW Intersection Large Yellow Grid Box (step_145!)
    _add_clipped_yellow_grid_rect(bm_yellow, -92.0, -81.0, -82.0, -73.8, pitch=2.10)
    # (2) 43 廣和街 Green Crosswalk (east of SW corner red-brick ramp!)
    _add_green_crosswalk_ns(bm_green, bm_white, x_center=-69.6, y0=-82.6, y1=SOUTH_CURB_Y - 0.25, width_x=3.4, n_stripes=5)
    # (3) 76 / 3A 廣和街 Wuquan St Ln 30 Intersection Yellow Grid Box (step_151 & step_153!)
    _add_clipped_yellow_grid_rect(bm_yellow, -25.2, -14.8, -82.4, SOUTH_CURB_Y - 0.35, pitch=1.95)
    # (4) 3 廣和街 Gate 3 Green Crosswalk (west half of Gate 3!) + Ln 30 Alley 24 Yellow Grid Box (immediately east of crosswalk! final_step_15!)
    _add_green_crosswalk_ns(bm_green, bm_white, x_center=10.6, y0=-82.6, y1=SOUTH_CURB_Y - 0.25, width_x=3.4, n_stripes=5)
    _add_clipped_yellow_grid_rect(bm_yellow, 12.8, 22.8, -82.4, SOUTH_CURB_Y - 0.35, pitch=1.95)
    # (5) 2 五權街 SE Crosswalk + Stop Line + 1 五權街 Mid Crosswalk & Large Yellow Grid + 15 五權街 NE Dual Crosswalks!
    _add_green_crosswalk_wuquan(bm_green, bm_white, y_center=-60.5, off_w=0.25, off_e=8.6, width_y=3.5, n_stripes=5)
    _add_strip_along_wuquan(bm_white, -57.8, -57.42, 0.25, 5.2, 0.010, 0.022)  # Stop line north of SE crosswalk (step_163!)
    _add_green_crosswalk_wuquan(bm_green, bm_white, y_center=-21.6, off_w=0.25, off_e=8.6, width_y=3.5, n_stripes=5)
    _add_clipped_yellow_grid_wuquan(bm_yellow, y_center=-14.2, half_len_y=4.8, off_w=0.30, off_e=8.6, pitch=1.95)
    # 2 五權街 Mid-A white transverse speed-reduction bars (step_176!)
    for sy_spd in (6.5, 7.1, 7.7, 8.3, 8.9):
        _add_strip_along_wuquan(bm_white, sy_spd, sy_spd + 0.16, 2.55, 5.15, 0.010, 0.022)
    # 15 五權街 / 166 和平路 NE Intersection dual green crosswalks + Eastbound Stop Line!
    _add_green_crosswalk_wuquan(bm_green, bm_white, y_center=49.0, off_w=0.35, off_e=9.4, width_y=3.6, n_stripes=5)
    _add_green_crosswalk_heping(bm_green, bm_white, x_center=63.6, off_s=0.28, off_n=10.16, width_x=3.6, n_stripes=5)
    _add_strip_along_heping(bm_white, 58.65, 59.15, 0.28, 4.96, 0.010, 0.022)  # 166 和平路 stop line before NE crosswalk!

    # Segmented Double-Yellow Centerlines (v11 exact 4.28° Heping Rd + West Guanghe St + East Wuquan St!)
    _add_strip_along_heping(bm_yellow, -60.2, 60.2, 5.06, 5.20, 0.010, 0.020)
    _add_strip_along_heping(bm_yellow, -60.2, 60.2, 5.34, 5.48, 0.010, 0.020)
    for y_seg0, y_seg1 in [(10.2, 35.4), (-28.3, -9.8), (-69.5, -45.4)]:
        _add_strip_along_guanghe(bm_yellow, y_seg0, y_seg1, -5.28, -5.14, 0.010, 0.020)
        _add_strip_along_guanghe(bm_yellow, y_seg0, y_seg1, -5.58, -5.44, 0.010, 0.020)
    # East Wuquan St center double-yellow line (north of 1 五權街 yellow grid up to NE crosswalk!)
    _add_strip_along_wuquan(bm_yellow, -8.5, 46.5, 5.25, 5.39, 0.010, 0.020)
    _add_strip_along_wuquan(bm_yellow, -8.5, 46.5, 5.55, 5.69, 0.010, 0.020)

    objs.append(su.create_mesh_object("Base_RoadMark_Yellow", bm_yellow, palette["road_yellow"], col))
    objs.append(su.create_mesh_object("Base_RoadMark_Green", bm_green, palette["crosswalk_green"], col))
    objs.append(su.create_mesh_object("Base_RoadMark_White", bm_white, palette["road_white"], col))

    # === 4. PURE TRANSPARENT RGBA Thermoplastic Markings (Smart Parking, Moto Wait Box & 43 廣和街 Blue Disabled Bay!) ===
    def _add_road_decal(name: str, mat_key: str, y0: float, y1: float, off_w: float, off_e: float, z: float = 0.022) -> None:
        bm_d = bmesh.new()
        _add_uv_quad_world(
            bm_d,
            (curb_x(y0) + off_w, y0, z),
            (curb_x(y0) + off_e, y0, z),
            (curb_x(y1) + off_e, y1, z),
            (curb_x(y1) + off_w, y1, z),
        )
        objs.append(su.create_mesh_object(name, bm_d, palette[mat_key], col, auto_uv=False))

    _add_road_decal("Base_RoadMark_SmartParkingNorth", "smart_parking", 13.0, 25.4, -3.10, -0.14)
    _add_road_decal("Base_RoadMark_SmartParkingSouth", "smart_parking_south", -25.4, -12.6, -3.10, -0.14)
    _add_road_decal("Base_RoadMark_MotoWaitBox", "moto_wait_box", 29.2, 34.4, -4.92, -0.58)

    # 43 廣和街 Blue-Border Accessible Parking Bay (PURE RGBA directly on asphalt, step_149!)
    bm_dis = bmesh.new()
    _add_uv_quad_world(
        bm_dis,
        (-62.2, SOUTH_CURB_Y - 2.45, 0.022),
        (-56.6, SOUTH_CURB_Y - 2.45, 0.022),
        (-56.6, SOUTH_CURB_Y - 0.16, 0.022),
        (-62.2, SOUTH_CURB_Y - 0.16, 0.022),
    )
    objs.append(su.create_mesh_object("Base_RoadMark_SouthDisabledBay", bm_dis, palette["disabled_parking"], col, auto_uv=False))

    # === 4b. East Wuquan St PURE TRANSPARENT RGBA Markings (Disabled Moto, Car Bays 10-07, Smart Parking 05-01 & Heping Bus Box!) ===
    def _add_east_decal(name: str, mat_key: str, y0: float, y1: float, off_w: float, off_e: float, z: float = 0.022) -> None:
        bm_d = bmesh.new()
        _add_uv_quad_world(
            bm_d,
            (east_curb_x(y0) + off_w, y0, z),
            (east_curb_x(y0) + off_e, y0, z),
            (east_curb_x(y1) + off_e, y1, z),
            (east_curb_x(y1) + off_w, y1, z),
        )
        objs.append(su.create_mesh_object(name, bm_d, palette[mat_key], col, auto_uv=False))

    # 9 五權街 Blue "身障專用" Disabled Moto Stall (step_165!)
    _add_east_decal("Base_RoadMark_EastDisabledMoto", "disabled_moto_east", -39.8, -36.4, 0.14, 3.05)
    # 2 五權街中段 A Regular Numbered Car Bays 10 | 09 | 08 | 07 (step_176!)
    _add_east_decal("Base_RoadMark_EastCarBays10_07", "car_bays_east", -8.0, 12.2, 0.14, 2.38)
    # 2 五權街中北段 B & C Smart Parent Drop-off Parking Bays 05 -> 01 (step_178 & step_180!)
    _add_east_decal("Base_RoadMark_EastSmartParking05_01", "smart_parking_east", 16.2, 40.8, 0.14, 3.15)

    # === 4c. v11 North Heping Rd PURE TRANSPARENT RGBA Markings (Moto Wait, Bus Stop, Bus Only & Dual Speed "30"!) ===
    def _add_heping_decal(
        name: str,
        mat_key: str,
        x0: float,
        x1: float,
        off_s: float,
        off_n: float,
        eastbound: bool = True,
        z: float = 0.022,
    ) -> None:
        bm_d = bmesh.new()
        if eastbound:
            # Driver moving +X (east): left = north (off_n, U=0), right = south (off_s, U=1), top = east (x1, V=1)
            _add_uv_quad_world(
                bm_d,
                (x0, heping_south_edge_y(x0) + off_n, z),
                (x0, heping_south_edge_y(x0) + off_s, z),
                (x1, heping_south_edge_y(x1) + off_s, z),
                (x1, heping_south_edge_y(x1) + off_n, z),
            )
        else:
            # Driver moving -X (west): left = south (off_s, U=0), right = north (off_n, U=1), top = west (x0, V=1)
            _add_uv_quad_world(
                bm_d,
                (x1, heping_south_edge_y(x1) + off_s, z),
                (x1, heping_south_edge_y(x1) + off_n, z),
                (x0, heping_south_edge_y(x0) + off_n, z),
                (x0, heping_south_edge_y(x0) + off_s, z),
            )
        objs.append(su.create_mesh_object(name, bm_d, palette[mat_key], col, auto_uv=False))

    # 166 和平路 Eastbound Motorcycle Waiting Box (step_2 foreground!)
    _add_heping_decal("Base_RoadMark_HepingMotoWait", "heping_moto_box", 53.0, 58.1, 0.36, 4.86, eastbound=True)
    # 166 和平路 Bus Stop Box "公車停靠區" in front of bus shelter (step_2 mid-left!)
    _add_heping_decal("Base_RoadMark_HepingBusStopBox", "bus_stop_box", 39.0, 52.0, 0.28, 3.22, eastbound=True)
    # 166 和平路 Opposite Westbound Lane "公車專用" Box (step_2 mid-right!)
    _add_heping_decal("Base_RoadMark_HepingBusOnlyBox", "bus_only_box", 36.5, 49.5, 7.12, 10.06, eastbound=False)
    # 129 和平路 D / 166 和平路 Yellow Speed Limit "30" markings!
    _add_heping_decal("Base_RoadMark_HepingSpeed30West", "speed_30_yellow", -53.2, -49.6, 1.05, 3.85, eastbound=True)
    _add_heping_decal("Base_RoadMark_HepingSpeed30East", "speed_30_yellow", 51.0, 54.6, 6.20, 9.00, eastbound=False)

    # === 5. Cast-Iron Manhole Covers, Double-Leaf Telecom Handhole & Galvanized Curb Storm Drain Grates ===
    bm_mh = bmesh.new()
    for mx, my, mz, mr in [
        (curb_x(-3.2) - 0.85, -3.2, 0.025, 0.42),
        (curb_x(-5.4) - 5.2, -5.4, 0.025, 0.46),
        (curb_x(18.0) + 0.65, 18.0, 0.140, 0.36),
        (curb_x(27.0) + 0.65, 27.0, 0.140, 0.36),
        (curb_x(-17.8) + 0.65, -17.8, 0.140, 0.36),
        # 92 廣和街 SW intersection round manhole inside yellow grid (step_145!)
        (-86.2, -77.6, 0.025, 0.44),
        # 3 廣和街 A sidewalk round manhole near bike (step_153!)
        (-22.5, SOUTH_CURB_Y + 0.85, 0.140, 0.34),
        # East Wuquan St manholes (2 五權街 SE diag-brick, 1 五權街 crosswalk, 15 五權街 NE intersection!)
        (74.8, -68.2, 0.140, 0.42),
        (east_curb_x(-21.6) + 2.8, -21.6, 0.026, 0.44),
        (72.5, 51.8, 0.025, 0.44),
    ]:
        _add_uv_quad_world(bm_mh, (mx - mr, my - mr, mz), (mx + mr, my - mr, mz), (mx + mr, my + mr, mz), (mx - mr, my + mr, mz))
    objs.append(su.create_mesh_object("Base_ManholeCovers", bm_mh, palette["manhole"], col, auto_uv=False))

    # Double-Leaf Large Rectangular Cast-Iron Telecom Handhole Covers (12 廣和街 final_step_157 & 92 廣和街 SW!)
    bm_rmh = bmesh.new()
    # 12 廣和街 SE approach sidewalk foreground double-leaf cover
    _add_uv_quad_world(bm_rmh, (60.8, SOUTH_CURB_Y + 0.42, 0.141), (62.8, SOUTH_CURB_Y + 0.42, 0.141), (62.8, SOUTH_CURB_Y + 1.32, 0.141), (60.8, SOUTH_CURB_Y + 1.32, 0.141))
    # 92 廣和街 SW intersection foreground square cast-iron grate cover (step_145 bottom-left!)
    _add_uv_quad_world(bm_rmh, (-88.8, -81.2, 0.024), (-87.4, -81.2, 0.024), (-87.4, -79.8, 0.024), (-88.8, -79.8, 0.024))
    objs.append(su.create_mesh_object("Base_RectHandholeCovers", bm_rmh, palette["rect_manhole"], col, auto_uv=False))

    bm_drain = bmesh.new()
    for dy_g in (-52.0, -34.0, -21.0, -11.5, -5.0, 6.2, 8.2, 9.8, 16.5, 23.0, 31.5):
        _add_uv_quad_world(
            bm_drain,
            (curb_x(dy_g - 0.32) - 0.34, dy_g - 0.32, 0.016),
            (curb_x(dy_g - 0.32) - 0.02, dy_g - 0.32, 0.016),
            (curb_x(dy_g + 0.32) - 0.02, dy_g + 0.32, 0.016),
            (curb_x(dy_g + 0.32) - 0.34, dy_g + 0.32, 0.016),
        )
    # South Guanghe St curb storm drain grates (including Gate 3 right curb x=17.5 matching final_step_15!)
    for dx_s in (-65.0, -45.0, -25.0, -5.0, 17.5, 34.0, 50.0, 64.5):
        _add_uv_quad_world(
            bm_drain,
            (dx_s - 0.35, SOUTH_CURB_Y - 0.34, 0.016),
            (dx_s + 0.35, SOUTH_CURB_Y - 0.34, 0.016),
            (dx_s + 0.35, SOUTH_CURB_Y - 0.02, 0.016),
            (dx_s - 0.35, SOUTH_CURB_Y - 0.02, 0.016),
        )
    # NW, SW & SE curved corner central curb storm grates!
    gx_nw, gy_nw = nw_spine[9]
    gp.bm_box(bm_drain, (gx_nw - 0.12, gy_nw + 0.12, 0.045), (0.68, 0.28, 0.06), rot_z=math.radians(44.0))
    gx_sw, gy_sw = sw_spine[8]
    gp.bm_box(bm_drain, (gx_sw - 0.10, gy_sw - 0.10, 0.045), (0.68, 0.28, 0.06), rot_z=math.radians(-42.0))
    gx_se, gy_se = se_spine[8]
    gp.bm_box(bm_drain, (gx_se + 0.10, gy_se - 0.10, 0.045), (0.68, 0.28, 0.06), rot_z=math.radians(42.0))
    # East Wuquan St curb storm drain grates + NE curved corner grate!
    for dy_e in (-62.0, -49.5, -40.5, -24.0, -14.0, 2.0, 18.0, 27.5, 36.5, 44.0):
        _add_uv_quad_world(
            bm_drain,
            (east_curb_x(dy_e - 0.32) + 0.02, dy_e - 0.32, 0.016),
            (east_curb_x(dy_e - 0.32) + 0.34, dy_e - 0.32, 0.016),
            (east_curb_x(dy_e + 0.32) + 0.34, dy_e + 0.32, 0.016),
            (east_curb_x(dy_e + 0.32) + 0.02, dy_e + 0.32, 0.016),
        )
    gx_ne, gy_ne = ne_spine[8]
    gp.bm_box(bm_drain, (gx_ne + 0.10, gy_ne + 0.10, 0.045), (0.68, 0.28, 0.06), rot_z=math.radians(-42.0))
    # v11 North Heping Rd Rectangular Galvanized Storm Drain Grates set inside white concrete frames (129 D final_step_14 & 166!)
    for dx_hp in (-58.2, -19.2, 24.5, 53.5):
        _add_uv_quad_world(
            bm_drain,
            (dx_hp - 0.52, heping_south_edge_y(dx_hp - 0.52) - 0.28, 0.032),
            (dx_hp + 0.52, heping_south_edge_y(dx_hp + 0.52) - 0.28, 0.032),
            (dx_hp + 0.52, heping_south_edge_y(dx_hp + 0.52) + 0.08, 0.032),
            (dx_hp - 0.52, heping_south_edge_y(dx_hp - 0.52) + 0.08, 0.032),
        )
    objs.append(su.create_mesh_object("Base_CurbDrainGrates", bm_drain, palette["drain_grate"], col, auto_uv=False))

    # === 6. Granite Round Bollards with Double Groove Rings + Concrete Tree Planters with Soil ===
    bm_bol_granite = bmesh.new()
    bm_bol_groove = bmesh.new()
    for by in (-4.4, -7.8, -10.0, 8.2, 10.6, 27.6):
        _add_granite_bollard(bm_bol_granite, bm_bol_groove, curb_x(by) + 0.68, by, z0=0.135)
    objs.append(su.create_mesh_object("Base_GraniteBollards", bm_bol_granite, palette["granite_gray"], col, smooth=True, uv_scale=1.2))
    objs.append(su.create_mesh_object("Base_GraniteBollardGrooves", bm_bol_groove, palette["metal_dark"], col, smooth=True))

    bm_planter_curb = bmesh.new()
    bm_planter_soil = bmesh.new()
    for ty in (-6.1, -12.8, -21.2, 10.4, 20.6, 28.4, -46.5, -58.5):
        tx = curb_x(ty) + 1.20
        gp.bm_box(bm_planter_curb, (tx, ty - 0.66, 0.20), (1.42, 0.15, 0.16), rot_z=GUANGHE_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx, ty + 0.66, 0.20), (1.42, 0.15, 0.16), rot_z=GUANGHE_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx - 0.64, ty, 0.20), (0.15, 1.32, 0.16), rot_z=GUANGHE_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx + 0.64, ty, 0.20), (0.15, 1.32, 0.16), rot_z=GUANGHE_ROT_Z)
        gp.bm_box(bm_planter_soil, (tx, ty, 0.165), (1.16, 1.18, 0.08), rot_z=GUANGHE_ROT_Z)
    # Continuous South Guanghe St soil planter strips tucked against mosaic wall (avoiding YouBike bay, Gate 3 x=7.6..17.0 & Taipower x=19.8..21.6!)
    for px0, px1 in [(-47.5, 7.6), (17.0, 19.8), (21.6, 66.2)]:
        gp.bm_box(bm_planter_soil, ((px0 + px1) * 0.5, SOUTH_WALL_Y - 0.62, 0.155), (px1 - px0, 1.12, 0.06))
        gp.bm_box(bm_planter_curb, ((px0 + px1) * 0.5, SOUTH_WALL_Y - 1.20, 0.165), (px1 - px0 + 0.12, 0.12, 0.08))
    # East Wuquan St iconic square concrete-framed tree planter pits along checkerboard sidewalk (step_163..180!)
    east_tree_ys = (-60.2, -51.5, -42.5, -31.5, -18.5, -10.5, -1.5, 7.5, 19.5, 28.5, 36.2, 43.2)
    for ty_e in east_tree_ys:
        tx_e = east_curb_x(ty_e) - 0.96
        gp.bm_box(bm_planter_curb, (tx_e, ty_e - 0.58, 0.20), (1.24, 0.14, 0.15), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx_e, ty_e + 0.58, 0.20), (1.24, 0.14, 0.15), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx_e - 0.55, ty_e, 0.20), (0.14, 1.16, 0.15), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_planter_curb, (tx_e + 0.55, ty_e, 0.20), (0.14, 1.16, 0.15), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_planter_soil, (tx_e, ty_e, 0.165), (1.00, 1.02, 0.08), rot_z=EAST_ROT_Z)
    objs.append(su.create_mesh_object("Base_TreePlanterCurbs", bm_planter_curb, palette["curb_concrete"], col, uv_scale=0.6))
    objs.append(su.create_mesh_object("Base_TreePlanterSoil", bm_planter_soil, palette["tree_soil"], col))

    # West tall silver street lamps (South/East hazard lamps & North Heping skyblue-white lamps are built in mod_campus_street_details!)
    bm_lamps = bmesh.new()
    for ly in (23.8, -14.2, -33.5, -54.0):
        lx = curb_x(ly) + 0.65
        gp.bm_cyl_axis(bm_lamps, (lx, ly, 3.6), 0.075, 7.2, axis="Z", segments=8)
        gp.bm_box(bm_lamps, (lx - 0.85, ly, 7.1), (1.7, 0.14, 0.12), rot_z=GUANGHE_ROT_Z)
    objs.append(su.create_mesh_object("Base_StreetLamps", bm_lamps, palette["steel_silver"], col))

    if show_sat_ref:
        bm_sat = bmesh.new()
        uv_layer = bm_sat.loops.layers.uv.verify()
        half = 220.16 * 0.5
        v0 = bm_sat.verts.new((-half, -half, 0.03))
        v1 = bm_sat.verts.new((half, -half, 0.03))
        v2 = bm_sat.verts.new((half, half, 0.03))
        v3 = bm_sat.verts.new((-half, half, 0.03))
        f = bm_sat.faces.new((v0, v1, v2, v3))
        for loop, uv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv_layer].uv = uv
        objs.append(su.create_mesh_object("Ref_SatelliteOrtho", bm_sat, palette["sat_ref"], col, auto_uv=False))

    return objs


def build_track_and_stage(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置東側 200m 六跑道操場（含灰色透水連鎖磚大道、起跑線、草坪球場標線）與五權樓 1:1 連建式升旗司令台（雙側東西向米白斜牆階梯、2F 八角截角懸挑露台遮雨棚、號角喇叭與三旗桿）。"""
    col = "Zone_Track"
    cfg = spec["grounds"]["track"]
    cx, cy = cfg["center"]
    w_out = cfg["outer_width_x"]
    l_out = cfg["outer_length_y"]
    tw = cfg["track_width"]
    lanes = cfg["lanes"]

    r_out = w_out * 0.5
    r_in = r_out - tw
    straight = l_out - 2.0 * r_out

    objs: List[bpy.types.Object] = []

    # v12.6 Exact 147 和平路 & 3 廣和街 Street-View Detail:
    # Full-Width (x=6.45..21.05) Light-Warm-Gray Terrazzo / Concrete Grid Walkway running STRAIGHT from South Wall to North Heping Fence (Gate 147B)!
    bm_walk = bmesh.new()
    _quad_extrude(
        bm_walk,
        [
            (6.45, -69.55),
            (21.05, -69.55),
            (21.05, heping_south_edge_y(21.05) - HEPING_EAST_WALK_W - 0.08),
            (6.45, heping_south_edge_y(6.45) - HEPING_EAST_WALK_W - 0.08),
        ],
        0.015,
        0.042,
    )
    objs.append(su.create_mesh_object("Zone_Track_EastWalkway", bm_walk, palette["walkway_gray_paver"], col, uv_scale=0.32))

    # 200m Oval PU Track + v12.6 Exact 100m North Straight Sprint Extension (x=21.0..28.6 running straight to Heping Rd green mesh fence, step_8_shot_1.png!)
    bm_track = bmesh.new()
    _add_stadium_ring_prism(bm_track, cx, cy, straight, r_in, r_out, 0.0, 0.052, segs_arc=32)
    ext_x0, ext_x1 = cx - r_out, cx - r_in  # 21.00 .. 28.60
    ext_y_s = cy + straight * 0.5           # +12.00
    ext_y_n0 = heping_south_edge_y(ext_x0) - HEPING_EAST_WALK_W - 0.32
    ext_y_n1 = heping_south_edge_y(ext_x1) - HEPING_EAST_WALK_W - 0.32
    _quad_extrude(
        bm_track,
        [(ext_x0, ext_y_s), (ext_x1, ext_y_s), (ext_x1, ext_y_n1), (ext_x0, ext_y_n0)],
        0.002,
        0.0525,
    )
    objs.append(su.create_mesh_object("Zone_Track_PU", bm_track, palette["track_pu"], col, uv_scale=0.25))

    bm_lines = bmesh.new()
    for i in range(lanes + 1):
        r_line = r_in + (tw * i / lanes)
        _add_stadium_ring_prism(bm_lines, cx, cy, straight, max(0.05, r_line - 0.045), r_line + 0.045, 0.052, 0.068, segs_arc=32)
        # 100m straight sprint extension lane lines running cleanly up to north fence!
        xl_ext = ext_x0 + tw * i / lanes
        yl_top = heping_south_edge_y(xl_ext) - HEPING_EAST_WALK_W - 0.42
        _quad_extrude(
            bm_lines,
            [(xl_ext - 0.045, ext_y_s), (xl_ext + 0.045, ext_y_s), (xl_ext + 0.045, yl_top), (xl_ext - 0.045, yl_top)],
            0.0525,
            0.0685,
        )
    # 100m North Start/Finish Transverse White Bar + Full-Length West & North Concrete Drainage Curbs!
    # Note: at x=ext_x1+0.14 (28.74), outer north track curve sits at y = 12 + sqrt(21^2 - 13.26^2) = 28.28 -> start east curb cleanly at y=28.55!
    gp.bm_box(bm_lines, (0.5 * (ext_x0 + ext_x1), 46.2, 0.062), (tw, 0.16, 0.016))
    gp.bm_box(bm_lines, (ext_x0 - 0.14, 0.5 * (-36.0 + ext_y_n0), 0.048), (0.28, ext_y_n0 + 36.0, 0.018))
    gp.bm_box(bm_lines, (ext_x1 + 0.14, 0.5 * (28.55 + ext_y_n1), 0.048), (0.26, ext_y_n1 - 28.55, 0.018))
    _quad_extrude(
        bm_lines,
        [(ext_x0 - 0.25, ext_y_n0), (ext_x1 + 0.25, ext_y_n1), (ext_x1 + 0.25, ext_y_n1 + 0.26), (ext_x0 - 0.25, ext_y_n0 + 0.26)],
        0.042,
        0.062,
    )
    # Start/finish line on west straight + infield center soccer line & circle
    gp.bm_box(bm_lines, (cx - r_in - tw * 0.5, cy - straight * 0.45, 0.062), (tw, 0.14, 0.015))
    gp.bm_box(bm_lines, (cx, cy, 0.058), (r_in * 1.75, 0.12, 0.015))
    _add_stadium_ring_prism(bm_lines, cx, cy, 0.01, 4.2, 4.35, 0.052, 0.064, segs_arc=24)
    objs.append(su.create_mesh_object("Zone_Track_Lines", bm_lines, palette["track_line"], col))

    bm_grass = bmesh.new()
    _add_stadium_ring_prism(bm_grass, cx, cy, straight, 0.0, r_in - 0.04, 0.0, 0.046, segs_arc=32)
    objs.append(su.create_mesh_object("Zone_Track_InfieldGrass", bm_grass, palette["grass"], col, uv_scale=0.10))

    bm_metal = bmesh.new()
    bm_dark = bmesh.new()
    for gy_end in (cy + straight * 0.5 + 4.5, cy - straight * 0.5 - 4.5):
        gp.bm_cyl_axis(bm_metal, (cx - 2.4, gy_end, 1.05), 0.06, 2.1, axis="Z", segments=8)
        gp.bm_cyl_axis(bm_metal, (cx + 2.4, gy_end, 1.05), 0.06, 2.1, axis="Z", segments=8)
        gp.bm_cyl_axis(bm_metal, (cx, gy_end, 2.1), 0.06, 4.9, axis="X", segments=8)

    # =========================================================================
    # v11.8 INTEGRATED WUQUAN BLDG ASSEMBLY STAGE (1:1 3 廣和街 15° FOV final_step_8.png + sat_track.png!)
    # Directly attached to Wuquan Bldg east wall (x_back=6.30, centered at bay b=6 sy=-13.75):
    #   - 1F central chamfered terracotta-brick protruding stage body (z=0.34..1.32) with recessed shadow plinth + vertical stainless fence
    #   - Symmetric South & North EAST-WEST facing stairs (descending +X toward track) with solid cream-tile sloped side walls + twin stainless handrails
    #   - Integrated 2F cantilevered flat-topped chamfered concrete balcony canopy (NO front columns!) connecting cleanly to Wuquan 2F corridor
    #     with lower terracotta fascia + middle cream-tile parapet + terracotta coping + twin silver top guardrails + 2 horn loudspeakers
    #   - 3 tall flagpoles (South Yellow, Center ROC Red/Blue, North Blue) mounted cleanly on the 2F balcony deck inside the railing!
    # =========================================================================
    sy = -13.75
    x_back = 6.30  # Embeds 0.30m cleanly inside Wuquan east corridor line (x_max=6.5, outer pillar=6.60)

    def _chamfer_pts(xb: float, xs: float, xf: float, yc: float, hy_b: float, hy_f: float) -> List[Tuple[float, float]]:
        return [
            (xb, yc - hy_b),
            (xs, yc - hy_b),
            (xf, yc - hy_f),
            (xf, yc + hy_f),
            (xs, yc + hy_b),
            (xb, yc + hy_b),
        ]

    def _add_chamfer_parapet(
        bm: bmesh.types.BMesh,
        xb: float,
        xs: float,
        xf: float,
        yc: float,
        hy_b: float,
        hy_f: float,
        thick: float,
        z0: float,
        z1: float,
    ) -> None:
        """沿八角截角露台外輪廓（南邊、南45°斜角、東正面、北45°斜角、北邊）建立厚 thick 的無縫中空女兒牆。"""
        outer = _chamfer_pts(xb, xs, xf, yc, hy_b, hy_f)
        # Inner offset (keeping open west side at x=xb so Wuquan 2F corridor walks straight out!)
        inset_diag = thick * 1.15
        inner = [
            (xb, yc - (hy_b - thick)),
            (xs - thick * 0.42, yc - (hy_b - thick)),
            (xf - thick, yc - (hy_f - thick * 0.42)),
            (xf - thick, yc + (hy_f - thick * 0.42)),
            (xs - thick * 0.42, yc + (hy_b - thick)),
            (xb, yc + (hy_b - thick)),
        ]
        # 5 perimeter wall segments: (0->1), (1->2), (2->3), (3->4), (4->5)
        for idx_s in range(5):
            o0, o1 = outer[idx_s], outer[idx_s + 1]
            i0, i1 = inner[idx_s], inner[idx_s + 1]
            _quad_extrude(bm, [o0, o1, i1, i0], z0, z1)

    def _add_sloped_wall_y(
        bm: bmesh.types.BMesh,
        y0: float,
        y1: float,
        xz_profile: List[Tuple[float, float]],
    ) -> None:
        """沿 X-Z 平面輪廓擠出 Y=[y0, y1] 的實心斜坡護牆，自動校準朝外法線。"""
        vs_s = [bm.verts.new((px, y0, pz)) for px, pz in xz_profile]
        vs_n = [bm.verts.new((px, y1, pz)) for px, pz in xz_profile]
        faces_new = []
        faces_new.append(bm.faces.new(vs_s))
        faces_new.append(bm.faces.new(list(reversed(vs_n))))
        n = len(xz_profile)
        for i in range(n):
            j = (i + 1) % n
            faces_new.append(bm.faces.new((vs_s[i], vs_n[i], vs_n[j], vs_s[j])))
        bmesh.ops.recalc_face_normals(bm, faces=faces_new)

    def _add_railing_polyline(
        bm_r: bmesh.types.BMesh,
        pts_2d: List[Tuple[float, float]],
        z_base: float,
        z_mid: float,
        z_top: float,
        post_spacing: float = 0.95,
        r_rail: float = 0.026,
        r_post: float = 0.022,
    ) -> None:
        for i in range(len(pts_2d) - 1):
            p0, p1 = pts_2d[i], pts_2d[i + 1]
            seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if seg_len < 1e-4:
                continue
            gp.bm_cyl_p2p(bm_r, (p0[0], p0[1], z_top), (p1[0], p1[1], z_top), r_rail, r_rail, segments=8)
            if z_mid > z_base + 0.05:
                gp.bm_cyl_p2p(bm_r, (p0[0], p0[1], z_mid), (p1[0], p1[1], z_mid), r_rail * 0.85, r_rail * 0.85, segments=8)
            n_posts = max(1, int(round(seg_len / post_spacing)))
            for k in range(n_posts + (1 if i == len(pts_2d) - 2 else 0)):
                t = k / n_posts
                px = p0[0] + (p1[0] - p0[0]) * t
                py = p0[1] + (p1[1] - p0[1]) * t
                gp.bm_cyl_p2p(bm_r, (px, py, z_base), (px, py, z_top), r_post, r_post, segments=6)

    bm_stage_cream = bmesh.new()
    bm_stage_brick = bmesh.new()
    bm_stage_trim = bmesh.new()
    bm_stage_deck = bmesh.new()
    bm_stage_plinth = bmesh.new()
    bm_stage_shrub = bmesh.new()

    # --- 1. 1F Central Attached Stage Platform & Protruding Chamfered Brick Body ---
    # Recessed dark-concrete shadow plinth under protruding brick stage base (exact final_step_8.png deep shadow!)
    _quad_extrude(bm_stage_plinth, _chamfer_pts(x_back, 9.65, 11.12, sy, 3.60, 2.35), 0.02, 0.34)
    # Protruding chamfered terracotta-brick central podium wall (z=0.34..1.32)
    _quad_extrude(bm_stage_brick, _chamfer_pts(x_back, 9.95, 11.45, sy, 3.70, 2.50), 0.34, 1.32)
    # Upper stage coping rim (cream stone trim) & terrazzo standing deck
    _quad_extrude(bm_stage_trim, _chamfer_pts(x_back, 9.98, 11.49, sy, 3.74, 2.53), 1.32, 1.40)
    _quad_extrude(bm_stage_deck, _chamfer_pts(x_back + 0.05, 9.75, 11.18, sy, 3.55, 2.36), 1.38, 1.42)
    # Recessed podium back connection steps down toward Wuquan 1F breezeway floor (z=0.36 -> 1.38)
    for bi in range(4):
        bh = 0.36 + 1.02 * (bi + 1) / 4.0
        gp.bm_box(bm_stage_trim, (x_back + 0.12 + bi * 0.28, sy, bh * 0.5), (0.30, 5.2, bh))
    # Compact brick-and-trim speaker lectern at stage front center
    gp.bm_box(bm_stage_brick, (10.30, sy, 1.88), (0.58, 0.88, 0.96))
    gp.bm_box(bm_stage_trim, (10.32, sy, 2.38), (0.66, 0.96, 0.08))

    # Iconic dense vertical stainless-steel picket balustrade along central protruding brick front (exact final_step_8.png center!)
    fence_pts = [
        (9.88, sy - 3.52),
        (11.30, sy - 2.40),
        (11.30, sy + 2.40),
        (9.88, sy + 3.52),
    ]
    _add_railing_polyline(bm_metal, fence_pts, z_base=1.40, z_mid=1.50, z_top=2.24, post_spacing=0.20, r_rail=0.028, r_post=0.018)

    # --- 2. Symmetric South & North EAST-WEST Facing Stairs (solid cream-tile sloped side walls + twin stainless handrails!) ---
    # Each stair wing sits right beside the central protruding brick podium: y_center = sy +- 5.15 (width 2.90m: |dy| = 3.70..6.60)
    wall_t = 0.30
    xz_slope_wall = [
        (x_back, 0.02),
        (11.65, 0.02),
        (11.65, 0.94),
        (11.35, 0.94),
        (8.05, 2.18),
        (x_back, 2.18),
    ]
    for side_sgn in (-1.0, 1.0):
        y_in = sy + side_sgn * 3.70   # inner edge touching central podium
        y_out = sy + side_sgn * 6.60  # outer edge toward south palms / north walkway
        y_mid_st = 0.5 * (y_in + y_out)
        # Solid cream-tile outer & inner sloped cheek walls (exact final_step_8.png!)
        if side_sgn < 0:
            wall_pairs = [(y_out, y_out + wall_t), (y_in - wall_t, y_in)]
        else:
            wall_pairs = [(y_in, y_in + wall_t), (y_out - wall_t, y_out)]
        for wy0, wy1 in wall_pairs:
            _add_sloped_wall_y(bm_stage_cream, wy0, wy1, xz_slope_wall)
            # Crisp light concrete coping cap along flat top, sloped run & bottom flat nose
            wyc = 0.5 * (wy0 + wy1)
            gp.bm_box(bm_stage_trim, (0.5 * (x_back + 8.05), wyc, 2.21), (8.05 - x_back + 0.06, wall_t + 0.06, 0.07))
            gp.bm_box(bm_stage_trim, (11.50, wyc, 0.97), (0.36, wall_t + 0.06, 0.07))
            slope_dx = 11.35 - 8.05
            slope_dz = 2.18 - 0.94
            slope_len = math.hypot(slope_dx, slope_dz)
            slope_ang = math.atan2(slope_dz, slope_dx)
            gp.bm_box(
                bm_stage_trim,
                (0.5 * (8.05 + 11.35), wyc, 0.5 * (2.18 + 0.94) + 0.03),
                (slope_len + 0.06, wall_t + 0.06, 0.07),
                rot_y=slope_ang,
            )
            # Iconic gleaming stainless-steel sloped handrail running right above each sloped cheek wall!
            gp.bm_cyl_p2p(bm_metal, (8.05, wyc, 2.34), (11.42, wyc, 1.08), 0.028, 0.028, segments=8)
            gp.bm_cyl_p2p(bm_metal, (6.65, wyc, 2.34), (8.05, wyc, 2.34), 0.028, 0.028, segments=8)
            for hx_p, hz_p in [(6.75, 2.18), (8.05, 2.18), (9.70, 1.56), (11.35, 0.94)]:
                gp.bm_cyl_p2p(bm_metal, (hx_p, wyc, hz_p), (hx_p, wyc, hz_p + 0.16), 0.018, 0.018, segments=6)

        # Upper stair landing flush with stage deck (x=6.30..8.05, z=0.02..1.38)
        gp.bm_box(bm_stage_trim, (0.5 * (x_back + 8.05), y_mid_st, 0.70), (8.05 - x_back, 2.34, 1.36))
        # 8 clean non-slip steps descending EAST (+X) from x=8.05 (z=1.36) down to x=11.45 (z=0.04)
        n_steps = 8
        step_dx = (11.45 - 8.05) / n_steps
        for si in range(n_steps):
            sh = 1.36 * (n_steps - si) / n_steps
            sx_st = 8.05 + (si + 0.5) * step_dx
            gp.bm_box(bm_stage_trim, (sx_st, y_mid_st, 0.02 + sh * 0.5), (step_dx + 0.04, 2.34, sh))

        # Low horizontal cream-tile wing planter wall abutting Wuquan east wall just outside each stair wing (exact final_step_8.png lower-left behind palms!)
        y_wing_0 = sy + side_sgn * 6.60
        y_wing_1 = sy + side_sgn * 9.30
        gp.bm_box(bm_stage_cream, (0.5 * (x_back + 8.45), 0.5 * (y_wing_0 + y_wing_1), 0.62), (8.45 - x_back, abs(y_wing_1 - y_wing_0), 1.20))
        gp.bm_box(bm_stage_trim, (0.5 * (x_back + 8.48), 0.5 * (y_wing_0 + y_wing_1), 1.24), (8.48 - x_back + 0.04, abs(y_wing_1 - y_wing_0) + 0.06, 0.07))

    # Lush manicured rounded dark-green shrub clusters flanking central brick stage shoulders & base corners (exact final_step_8.png!)
    rng_st = random.Random(118)

    def _add_stage_shrub(scx: float, scy: float, scz: float, rx: float, ry: float, rz: float) -> None:
        ret = bmesh.ops.create_icosphere(bm_stage_shrub, subdivisions=2, radius=1.0)
        for v in ret["verts"]:
            n = 1.0 + 0.18 * math.sin(v.co.x * 7.2 + scx) * math.cos(v.co.y * 6.8 + scy) + rng_st.uniform(-0.07, 0.07)
            v.co.x = scx + v.co.x * rx * n
            v.co.y = scy + v.co.y * ry * n
            v.co.z = scz + v.co.z * rz * n

    for side_sgn in (-1.0, 1.0):
        # Upper shoulder planter shrubs tucked cleanly INSIDE the chamfer pocket between stair inner cheek wall (|dy|=3.70) & stainless picket fence (zero wall/rail clipping!)
        _add_stage_shrub(9.82, sy + side_sgn * 3.16, 1.72, 0.48, 0.42, 0.36)
        _add_stage_shrub(10.48, sy + side_sgn * 2.74, 1.66, 0.44, 0.38, 0.32)
        # Lower base corner round shrubs sitting cleanly outside the protruding brick base (zero brick clipping!)
        _add_stage_shrub(11.18, sy + side_sgn * 3.22, 0.36, 0.46, 0.42, 0.32)
        _add_stage_shrub(11.62, sy + side_sgn * 2.86, 0.32, 0.38, 0.36, 0.28)

    # --- 3. 2F Integrated Cantilevered Flat-Topped Chamfered Balcony Canopy (NO front columns! Connects flush to Wuquan 2F!) ---
    # Exact 5-tier elevation matching final_step_8.png:
    #   (a) Smooth gray-cream soffit underside (z=3.54..3.58)
    _quad_extrude(bm_stage_trim, _chamfer_pts(x_back, 9.45, 10.70, sy, 4.45, 3.00), 3.54, 3.58)
    #   (b) Thick lower terracotta-brick cantilevered fascia beam slab (z=3.58..4.18)
    _quad_extrude(bm_stage_brick, _chamfer_pts(x_back, 9.55, 10.85, sy, 4.55, 3.10), 3.58, 4.18)
    #   (c) Walkable 2F terrace light-gray terrazzo deck sitting cleanly ON TOP of fascia slab (z=4.17..4.22, zero brick bleed-through!)
    _quad_extrude(bm_stage_deck, _chamfer_pts(x_back, 9.35, 10.55, sy, 4.25, 2.86), 4.17, 4.22)
    #   (d) Middle cream square-tile hollow balcony parapet wall (z=4.18..4.78) — seamlessly aligned with Wuquan 2F white parapet!
    _add_chamfer_parapet(bm_stage_cream, x_back, 9.55, 10.85, sy, 4.55, 3.10, thick=0.28, z0=4.18, z1=4.78)
    #   (e) Crisp top terracotta-brick coping band (z=4.78..4.92)
    _add_chamfer_parapet(bm_stage_brick, x_back, 9.57, 10.87, sy, 4.57, 3.12, thick=0.32, z0=4.78, z1=4.92)
    #   (f) Top silver twin-bar stainless safety railing circling the entire 2F chamfered terrace (z=4.92..5.56)
    rail_2f_pts = _chamfer_pts(x_back + 0.25, 9.42, 10.71, sy, 4.41, 2.98)
    _add_railing_polyline(bm_metal, rail_2f_pts, z_base=4.92, z_mid=5.24, z_top=5.56, post_spacing=1.15, r_rail=0.025, r_post=0.022)

    #   (g) 2 Iconic Dark-Gray Horn Loudspeakers mounted on the 2F canopy front chamfer corners (exact final_step_8.png!)
    for side_sgn in (-1.0, 1.0):
        sp_base = (10.72, sy + side_sgn * 2.98, 4.82)
        sp_dir_x, sp_dir_y, sp_dir_z = 0.88, side_sgn * 0.36, -0.26
        sp_neck = (sp_base[0] + sp_dir_x * 0.22, sp_base[1] + sp_dir_y * 0.22, sp_base[2] + sp_dir_z * 0.22)
        sp_mouth = (sp_base[0] + sp_dir_x * 0.56, sp_base[1] + sp_dir_y * 0.56, sp_base[2] + sp_dir_z * 0.56)
        gp.bm_cyl_p2p(bm_metal, sp_base, sp_neck, 0.025, 0.025, segments=6)
        gp.bm_cyl_p2p(bm_dark, sp_neck, sp_mouth, 0.075, 0.23, segments=14)

    # --- 4. 3 Tall Silver Flagpoles Mounted on 2F Balcony Deck Inside Railing (cleanly ABOVE 2F canopy, zero clash below!) ---
    # Exact final_step_8.png flag order: South = Yellow, Center = ROC Red+Blue Canton (tallest), North = Blue/White
    bm_flag_r = bmesh.new()
    bm_flag_b = bmesh.new()
    bm_flag_y = bmesh.new()
    pole_x = 10.12
    for idx, (fy, z_top_pole) in enumerate([(sy - 1.90, 11.8), (sy, 13.0), (sy + 1.90, 11.8)]):
        # Mounting flange base seated cleanly on 2F terrace deck (z=4.22)
        gp.bm_cyl_axis(bm_metal, (pole_x, fy, 4.34), 0.10, 0.26, axis="Z", segments=10)
        gp.bm_cyl_p2p(bm_metal, (pole_x, fy, 4.42), (pole_x, fy, z_top_pole), 0.052, 0.032, segments=10)
        # Silver finial ball at pole tip
        mat_fin = Matrix.Translation(Vector((pole_x, fy, z_top_pole + 0.08))) @ Matrix.Diagonal((0.08, 0.08, 0.08, 1.0))
        bmesh.ops.create_icosphere(bm_metal, subdivisions=1, radius=1.0, matrix=mat_fin)
        if idx == 0:
            # South Yellow Flag (natural slight drape + gentle breeze)
            gp.bm_box(bm_flag_y, (pole_x + 0.68, fy + 0.05, z_top_pole - 0.85), (1.32, 0.04, 0.92), rot_y=math.radians(14.0), rot_z=math.radians(6.0))
        elif idx == 1:
            # Center ROC National Flag (Red field + upper-hoist Blue canton)
            gp.bm_box(bm_flag_r, (pole_x + 0.78, fy + 0.05, z_top_pole - 0.90), (1.52, 0.04, 1.02), rot_y=math.radians(12.0), rot_z=math.radians(6.0))
            gp.bm_box(bm_flag_b, (pole_x + 0.42, fy + 0.05, z_top_pole - 0.56), (0.76, 0.055, 0.52), rot_y=math.radians(12.0), rot_z=math.radians(6.0))
        else:
            # North Blue School Flag
            gp.bm_box(bm_flag_b, (pole_x + 0.68, fy + 0.05, z_top_pole - 0.85), (1.32, 0.04, 0.92), rot_y=math.radians(14.0), rot_z=math.radians(6.0))

    objs.append(su.create_mesh_object("Zone_Track_SteelFixtures", bm_metal, palette["steel_silver"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_StageSpeakers", bm_dark, palette["metal_dark"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_FlagMain", bm_flag_r, palette["flag_red"], col))
    objs.append(su.create_mesh_object("Zone_Track_FlagSide", bm_flag_b, palette["flag_blue"], col))
    objs.append(su.create_mesh_object("Zone_Track_FlagYellow", bm_flag_y, palette["flag_yellow"], col))
    objs.append(su.create_mesh_object("Zone_Track_StageBody", bm_stage_cream, palette["wall_guanghe"], col, uv_scale=0.38))
    objs.append(su.create_mesh_object("Zone_Track_StageBrick", bm_stage_brick, palette["wall_brick_red"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Zone_Track_StageTrim", bm_stage_trim, palette["concrete_trim"], col, uv_scale=0.40))
    objs.append(su.create_mesh_object("Zone_Track_StageDeck", bm_stage_deck, palette["terrazzo_corridor"], col, uv_scale=0.40))
    objs.append(su.create_mesh_object("Zone_Track_StagePlinth", bm_stage_plinth, palette["curb_concrete"], col, uv_scale=0.45))
    objs.append(su.create_mesh_object("Zone_Track_StageShrubs", bm_stage_shrub, palette["tree_foliage_b"], col, smooth=True))

    objs.extend(_build_east_track_fitness(palette, col))
    objs.extend(_build_north_basketball_court(palette, col))
    return objs


def _build_east_track_fitness(palette: Dict[str, bpy.types.Material], col: str) -> List[bpy.types.Object]:
    """建置 11 & 9 五權街操場東側體健與器材區（器材遮雨棚、6 支爬竿架、4 跨 4 層肋木伸展架、4 跨階梯式高低單槓與安全緩衝沙墊）。"""
    objs: List[bpy.types.Object] = []
    bm_fit_steel = bmesh.new()
    bm_fit_dark = bmesh.new()
    bm_fit_base = bmesh.new()
    bm_fit_pad = bmesh.new()
    bm_shed_roof = bmesh.new()
    bm_shed_mat_blue = bmesh.new()

    def _east_pt(y_val: float, inset_from_wall: float) -> Tuple[float, float]:
        return (east_wall_x(y_val) - inset_from_wall, y_val)

    def _add_pole_cap(bm_s: bmesh.types.BMesh, px: float, py: float, pz: float, rad: float) -> None:
        mat_c = Matrix.Translation(Vector((px, py, pz))) @ Matrix.Diagonal((rad * 1.15, rad * 1.15, rad * 1.15, 1.0))
        bmesh.ops.create_icosphere(bm_s, subdivisions=1, radius=1.0, matrix=mat_c)

    def _add_safety_pad(y0_p: float, y1_p: float, inset_c: float, width_x: float) -> None:
        yc_p = 0.5 * (y0_p + y1_p)
        xc_p = east_wall_x(yc_p) - inset_c
        ly_p = y1_p - y0_p
        # Main sand/rubber safety surface slightly above grass (z=0.056m)
        gp.bm_box(bm_fit_pad, (xc_p, yc_p, 0.036), (width_x, ly_p, 0.044), rot_z=EAST_ROT_Z)
        # Clean concrete border curb framing all 4 sides of safety zone
        gp.bm_box(bm_fit_base, (xc_p - width_x * 0.5 - 0.08, yc_p, 0.048), (0.16, ly_p + 0.32, 0.068), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_fit_base, (xc_p + width_x * 0.5 + 0.08, yc_p, 0.048), (0.16, ly_p + 0.32, 0.068), rot_z=EAST_ROT_Z)
        p_s = _east_pt(y0_p - 0.08, inset_c)
        p_n = _east_pt(y1_p + 0.08, inset_c)
        gp.bm_box(bm_fit_base, (p_s[0], p_s[1], 0.048), (width_x + 0.32, 0.16, 0.068), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_fit_base, (p_n[0], p_n[1], 0.048), (width_x + 0.32, 0.16, 0.068), rot_z=EAST_ROT_Z)

    # Safety pads under climbing poles & fitness bars
    _add_safety_pad(-53.2, -44.8, 3.75, 2.45)
    _add_safety_pad(-33.1, -11.9, 3.55, 2.35)

    # --- 1. SE Corner Dark-Steel Corrugated Metal Equipment Shelter Shed (exact 11 五權街 step_12_shot_1.png far-left!) ---
    sh_y0, sh_y1 = -61.2, -55.0
    sh_yc = 0.5 * (sh_y0 + sh_y1)
    sh_xc = east_wall_x(sh_yc) - 2.65
    # Concrete slab floor under shed
    gp.bm_box(bm_fit_base, (sh_xc, sh_yc, 0.045), (3.45, sh_y1 - sh_y0 + 0.30, 0.09), rot_z=EAST_ROT_Z)
    # 6 dark charcoal structural steel legs + top eaves purlins
    for sy_p in (sh_y0 + 0.25, sh_yc, sh_y1 - 0.25):
        for off_x, h_leg in ((-1.35, 2.58), (1.35, 2.38)):
            px_s = east_wall_x(sy_p) - 2.65 + off_x
            gp.bm_cyl_axis(bm_fit_dark, (px_s, sy_p, h_leg * 0.5), 0.052, h_leg, axis="Z", segments=8)
            gp.bm_cyl_axis(bm_fit_base, (px_s, sy_p, 0.10), 0.14, 0.16, axis="Z", segments=8)
        # Cross-rafter connecting west & east leg tops
        p_w = (east_wall_x(sy_p) - 2.65 - 1.35, sy_p, 2.55)
        p_e = (east_wall_x(sy_p) - 2.65 + 1.35, sy_p, 2.36)
        gp.bm_cyl_p2p(bm_fit_dark, p_w, p_e, 0.036, 0.036, segments=6)
    gp.bm_box(bm_fit_dark, (sh_xc - 1.35, sh_yc, 2.52), (0.09, sh_y1 - sh_y0, 0.10), rot_z=EAST_ROT_Z)
    gp.bm_box(bm_fit_dark, (sh_xc + 1.35, sh_yc, 2.34), (0.09, sh_y1 - sh_y0, 0.10), rot_z=EAST_ROT_Z)
    # Sloped corrugated gray metal roof deck + rhythmic standing-seam corrugation ribs
    gp.bm_box(bm_shed_roof, (sh_xc, sh_yc, 2.52), (3.45, sh_y1 - sh_y0 + 0.45, 0.07), rot_y=math.radians(4.2), rot_z=EAST_ROT_Z)
    for k_rib in range(13):
        yr = (sh_y0 - 0.15) + k_rib * ((sh_y1 - sh_y0 + 0.30) / 12.0)
        xr = east_wall_x(yr) - 2.65
        gp.bm_box(bm_shed_roof, (xr, yr, 2.57), (3.45, 0.07, 0.055), rot_y=math.radians(4.2), rot_z=EAST_ROT_Z)
    # Sports equipment neatly stored underneath (stacked blue high-jump foam crash mats + dark steel cart/hurdles!)
    gp.bm_box(bm_shed_mat_blue, (east_wall_x(sh_yc - 1.45) - 2.45, sh_yc - 1.45, 0.48), (1.75, 2.20, 0.72), rot_z=EAST_ROT_Z)
    gp.bm_box(bm_fit_dark, (east_wall_x(sh_yc + 1.40) - 2.35, sh_yc + 1.40, 0.56), (1.35, 1.95, 0.92), rot_z=EAST_ROT_Z)

    # --- 2. 6-Pole Brushed-Stainless Climbing Poles Frame (exact 11 五權街 step_12_shot_1.png center-left!) ---
    cp_y0, cp_y1 = -52.2, -45.8
    cp_inset = 3.75
    cp_p0 = _east_pt(cp_y0, cp_inset)
    cp_p1 = _east_pt(cp_y1, cp_inset)
    # Outer portal legs (H=3.44m) + horizontal top header beam at z=3.35m
    for px_c, py_c in (cp_p0, cp_p1):
        gp.bm_cyl_axis(bm_fit_steel, (px_c, py_c, 1.72), 0.058, 3.44, axis="Z", segments=10)
        _add_pole_cap(bm_fit_steel, px_c, py_c, 3.45, 0.062)
        gp.bm_cyl_axis(bm_fit_base, (px_c, py_c, 0.11), 0.19, 0.18, axis="Z", segments=10)
    gp.bm_cyl_p2p(bm_fit_steel, (cp_p0[0], cp_p0[1], 3.35), (cp_p1[0], cp_p1[1], 3.35), 0.054, 0.054, segments=10)
    # 6 evenly spaced vertical stainless climbing poles protruding cleanly 0.50m ABOVE the top beam (z=0..3.85m!)
    for idx_cp in range(6):
        t_cp = (idx_cp + 0.5) / 6.0
        py_p = cp_y0 + (cp_y1 - cp_y0) * t_cp
        px_p = east_wall_x(py_p) - cp_inset
        gp.bm_cyl_axis(bm_fit_steel, (px_p, py_p, 1.925), 0.038, 3.85, axis="Z", segments=10)
        _add_pole_cap(bm_fit_steel, px_p, py_p, 3.86, 0.042)
        gp.bm_cyl_axis(bm_fit_base, (px_p, py_p, 0.10), 0.14, 0.16, axis="Z", segments=8)
        # Cross-clamp collar where each pole passes through z=3.35m header beam
        gp.bm_box(bm_fit_steel, (px_p, py_p, 3.35), (0.14, 0.14, 0.14), rot_z=EAST_ROT_Z)

    # --- 3. 4-Bay 4-Rail Stainless Stretching / Rib-Bar Frame (exact 9 五權街 step_10_shot_1.png left half!) ---
    bar_inset = 3.55
    tr_y0 = -32.2
    tr_bay = 2.25
    tr_posts = [tr_y0 + i * tr_bay for i in range(5)]  # y = -32.2 .. -23.2 (4 bays)
    for py_t in tr_posts:
        px_t = east_wall_x(py_t) - bar_inset
        gp.bm_cyl_axis(bm_fit_steel, (px_t, py_t, 1.35), 0.056, 2.70, axis="Z", segments=10)
        _add_pole_cap(bm_fit_steel, px_t, py_t, 2.71, 0.060)
        gp.bm_cyl_axis(bm_fit_base, (px_t, py_t, 0.10), 0.16, 0.16, axis="Z", segments=8)
    for i in range(4):
        ya, yb = tr_posts[i], tr_posts[i + 1]
        pa, pb = _east_pt(ya, bar_inset), _east_pt(yb, bar_inset)
        # 4 parallel stainless rails matching step_10_shot_1.png exact 4-tier horizontal spacing!
        for z_rail in (1.12, 1.56, 2.00, 2.44):
            gp.bm_cyl_p2p(bm_fit_steel, (pa[0], pa[1], z_rail), (pb[0], pb[1], z_rail), 0.032, 0.032, segments=10)
            gp.bm_cyl_axis(bm_fit_steel, (pa[0], pa[1], z_rail), 0.064, 0.09, axis="Z", segments=8)
            gp.bm_cyl_axis(bm_fit_steel, (pb[0], pb[1], z_rail), 0.064, 0.09, axis="Z", segments=8)

    # --- 4. 4-Bay Stepped High-Mid-Low Stainless Pull-Up Bars (exact 9 五權街 step_10_shot_1.png right half!) ---
    pb_y0 = -21.8
    pb_bay = 2.25
    pb_ys = [pb_y0 + i * pb_bay for i in range(5)]  # y = -21.8 .. -12.8 (4 stepped bays right across from Wuquan Stage!)
    pb_post_hs = [2.68, 2.68, 2.38, 2.06, 1.76]
    pb_bar_zs = [2.56, 2.24, 1.92, 1.62]
    for py_p, ph_p in zip(pb_ys, pb_post_hs):
        px_p = east_wall_x(py_p) - bar_inset
        gp.bm_cyl_axis(bm_fit_steel, (px_p, py_p, ph_p * 0.5), 0.056, ph_p, axis="Z", segments=10)
        _add_pole_cap(bm_fit_steel, px_p, py_p, ph_p + 0.01, 0.060)
        gp.bm_cyl_axis(bm_fit_base, (px_p, py_p, 0.10), 0.16, 0.16, axis="Z", segments=8)
    for i, bz_p in enumerate(pb_bar_zs):
        pa, pb = _east_pt(pb_ys[i], bar_inset), _east_pt(pb_ys[i + 1], bar_inset)
        gp.bm_cyl_p2p(bm_fit_steel, (pa[0], pa[1], bz_p), (pb[0], pb[1], bz_p), 0.032, 0.032, segments=10)
        gp.bm_cyl_axis(bm_fit_steel, (pa[0], pa[1], bz_p), 0.064, 0.09, axis="Z", segments=8)
        gp.bm_cyl_axis(bm_fit_steel, (pb[0], pb[1], bz_p), 0.064, 0.09, axis="Z", segments=8)

    objs.append(su.create_mesh_object("Zone_Track_EastFitnessSteel", bm_fit_steel, palette["fitness_stainless"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_EastFitnessDark", bm_fit_dark, palette["metal_dark"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_EastFitnessBases", bm_fit_base, palette["curb_concrete"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_EastFitnessPads", bm_fit_pad, palette["fitness_sand_pad"], col, uv_scale=0.5))
    objs.append(su.create_mesh_object("Zone_Track_EastShedRoof", bm_shed_roof, palette["shed_roof_gray"], col))
    objs.append(su.create_mesh_object("Zone_Track_EastShedMats", bm_shed_mat_blue, palette["flag_blue"], col))
    return objs


def _build_north_basketball_court(palette: Dict[str, bpy.types.Material], col: str) -> List[bpy.types.Object]:
    """建置 2 五權街 & 147 和平路操場東北角雙半場露天水泥籃球場、淡草綠緩衝地坪、2 座藍防撞墊籃球架、12 座ㄇ字銀欄杆、泥土樹穴帶與東北角涼亭。"""
    objs: List[bpy.types.Object] = []
    bm_nc_mint = bmesh.new()
    bm_nc_conc = bmesh.new()
    bm_nc_wline = bmesh.new()
    bm_nc_soil = bmesh.new()
    bm_nc_steel = bmesh.new()
    bm_nc_pad = bmesh.new()
    bm_nc_bb_face = bmesh.new()
    bm_nc_bb_back = bmesh.new()
    bm_nc_rim = bmesh.new()
    bm_nc_net = bmesh.new()
    bm_nc_pav_dark = bmesh.new()
    bm_nc_pav_wood = bmesh.new()
    bm_nc_pav_base = bmesh.new()

    def _add_uv_quad_nc(bm_q: bmesh.types.BMesh, p0: Tuple[float, float, float], p1: Tuple[float, float, float], p2: Tuple[float, float, float], p3: Tuple[float, float, float]) -> None:
        uv_l = bm_q.loops.layers.uv.verify()
        vs = [bm_q.verts.new(p) for p in (p0, p1, p2, p3)]
        f = bm_q.faces.new(vs)
        for lp, uv in zip(f.loops, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
            lp[uv_l].uv = uv

    # (1) Light-Mint Buffer Apron tucked cleanly beneath track curve (z=0.0475 < track 0.052, > lawn 0.036!)
    _quad_extrude(
        bm_nc_mint,
        [
            (28.80, 27.00),
            (35.80, 32.20),
            (35.80, 46.60),
            (28.80, 46.60),
        ],
        0.042,
        0.0475,
    )
    # Crisp white dividing line between Mint Buffer Apron & Concrete Basketball Court
    gp.bm_box(bm_nc_wline, (35.80, 40.20, 0.050), (0.14, 12.80, 0.008))

    # (2) Dual Half-Court Weathered Concrete Basketball Court (x=35.80..60.80, y=33.80..46.60, z=0.0485)
    nc_x0, nc_x1, nc_y0, nc_y1 = 35.80, 60.80, 33.80, 46.60
    gp.bm_box(bm_nc_pav_base, (0.5 * (nc_x0 + nc_x1), 0.5 * (nc_y0 + nc_y1), 0.038), (nc_x1 - nc_x0 + 0.24, nc_y1 - nc_y0 + 0.24, 0.018))
    _add_uv_quad_nc(
        bm_nc_conc,
        (nc_x0, nc_y0, 0.0485), (nc_x1, nc_y0, 0.0485),
        (nc_x1, nc_y1, 0.0485), (nc_x0, nc_y1, 0.0485),
    )

    # (3) 2 Side-by-Side Single-Pole Basketball Hoops on SOUTH baseline (y=34.45) facing NORTH (+Y toward Heping Rd!)
    for hx in (42.05, 54.55):
        hy = 34.45
        # Concrete footing + Silver main cylindrical pole (z=0.05..3.52) + Iconic Royal-Blue cylindrical safety pad (z=0.10..1.98)!
        gp.bm_cyl_axis(bm_nc_pav_base, (hx, hy, 0.09), 0.22, 0.14, axis="Z", segments=12)
        gp.bm_cyl_axis(bm_nc_steel, (hx, hy, 1.80), 0.082, 3.50, axis="Z", segments=12)
        gp.bm_cyl_axis(bm_nc_pad, (hx, hy, 1.04), 0.145, 1.88, axis="Z", segments=14)
        # Forward-cantilevered north-facing silver boom arms + rectangular rear mounting frame
        gp.bm_cyl_p2p(bm_nc_steel, (hx, hy, 3.45), (hx, hy + 1.18, 3.45), 0.052, 0.052, segments=10)
        gp.bm_cyl_p2p(bm_nc_steel, (hx, hy, 2.75), (hx, hy + 1.15, 3.18), 0.038, 0.038, segments=8)
        for sx_b in (-0.52, 0.52):
            gp.bm_cyl_p2p(bm_nc_steel, (hx, hy + 0.65, 3.45), (hx + sx_b, hy + 1.18, 3.62), 0.024, 0.024, segments=6)
            gp.bm_cyl_p2p(bm_nc_steel, (hx, hy + 0.65, 3.05), (hx + sx_b, hy + 1.18, 3.10), 0.024, 0.024, segments=6)
        # White Rectangular Backboard (1.80m x 1.05m, facing NORTH +Y!)
        bb_y = hy + 1.22
        bb_zc = 3.42
        gp.bm_box(bm_nc_bb_back, (hx, bb_y - 0.03, bb_zc), (1.82, 0.05, 1.07))
        # Outward +Y face: p0=(+X, z0), p1=(-X, z0), p2=(-X, z1), p3=(+X, z1) -> normal = +Y!
        _add_uv_quad_nc(
            bm_nc_bb_face,
            (hx + 0.90, bb_y, bb_zc - 0.525), (hx - 0.90, bb_y, bb_zc - 0.525),
            (hx - 0.90, bb_y, bb_zc + 0.525), (hx + 0.90, bb_y, bb_zc + 0.525),
        )
        # Orange steel hoop rim + mounting bracket + conical white nylon net!
        rim_y = bb_y + 0.28
        rim_z = 3.05
        gp.bm_box(bm_nc_rim, (hx, bb_y + 0.04, rim_z), (0.14, 0.08, 0.10))
        r_rim = 0.23
        n_rim = 12
        for ri in range(n_rim):
            a0 = 2.0 * math.pi * ri / n_rim
            a1 = 2.0 * math.pi * ((ri + 1) % n_rim) / n_rim
            p_r0 = (hx + math.cos(a0) * r_rim, rim_y + math.sin(a0) * r_rim, rim_z)
            p_r1 = (hx + math.cos(a1) * r_rim, rim_y + math.sin(a1) * r_rim, rim_z)
            gp.bm_cyl_p2p(bm_nc_rim, p_r0, p_r1, 0.016, 0.016, segments=6)
            if ri % 2 == 0:
                a_bot = a0 + math.pi / n_rim
                p_b = (hx + math.cos(a_bot) * 0.13, rim_y + math.sin(a_bot) * 0.13, rim_z - 0.42)
                gp.bm_cyl_p2p(bm_nc_net, p_r0, p_b, 0.008, 0.008, segments=4)
                gp.bm_cyl_p2p(bm_nc_net, p_r1, p_b, 0.008, 0.008, segments=4)

    # (4) 12 Iconic Low Silver U-Shaped Divider Railings along South Court Edge (y=33.82, exact step_6_shot_1.png & step_4.png!)
    for idx_u in range(12):
        ux0 = 36.15 + idx_u * 2.04
        ux1 = ux0 + 1.68
        uy = 33.82
        gp.bm_cyl_p2p(bm_nc_steel, (ux0, uy, 0.04), (ux0, uy, 0.72), 0.028, 0.028, segments=8)
        gp.bm_cyl_p2p(bm_nc_steel, (ux1, uy, 0.04), (ux1, uy, 0.72), 0.028, 0.028, segments=8)
        gp.bm_cyl_p2p(bm_nc_steel, (ux0, uy, 0.72), (ux1, uy, 0.72), 0.028, 0.028, segments=8)

    # (5) Bare Dark-Soil Tree Strip along Heping Rd green mesh fence (x=28.8..62.5, y=46.60..fence!)
    _quad_extrude(
        bm_nc_soil,
        [
            (28.80, 46.60),
            (62.50, 46.60),
            (61.50, heping_south_edge_y(61.50) - HEPING_EAST_WALK_W - 0.12),
            (28.80, heping_south_edge_y(28.80) - HEPING_EAST_WALK_W - 0.12),
        ],
        0.036,
        0.045,
    )

    # (6) NE Corner Shade Rest Pavilion under trees + Benches + Courtyard Tall Lamp (exact 2 五權街 step_4.png right!)
    pv_x, pv_y = 63.6, 41.2
    gp.bm_box(bm_nc_pav_base, (pv_x, pv_y, 0.08), (4.0, 4.0, 0.14), rot_z=EAST_ROT_Z)
    for dx_p in (-1.55, 1.55):
        for dy_p in (-1.55, 1.55):
            gp.bm_cyl_axis(bm_nc_pav_dark, (pv_x + dx_p, pv_y + dy_p, 1.48), 0.072, 2.75, axis="Z", segments=8)
    # Dark-charcoal pitched pyramid roof + eaves fascia
    gp.bm_box(bm_nc_pav_dark, (pv_x, pv_y, 2.90), (4.45, 4.45, 0.16), rot_z=EAST_ROT_Z)
    gp.bm_box(bm_nc_pav_dark, (pv_x, pv_y, 3.22), (3.10, 3.10, 0.48), rot_z=EAST_ROT_Z)
    gp.bm_box(bm_nc_pav_dark, (pv_x, pv_y, 3.58), (1.45, 1.45, 0.28), rot_z=EAST_ROT_Z)
    # Wood benches tucked cleanly inside pavilion
    for dy_b in (-1.15, 1.15):
        gp.bm_box(bm_nc_pav_wood, (pv_x, pv_y + dy_b, 0.50), (2.45, 0.48, 0.09), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_nc_pav_dark, (pv_x - 0.85, pv_y + dy_b, 0.28), (0.12, 0.40, 0.40), rot_z=EAST_ROT_Z)
        gp.bm_box(bm_nc_pav_dark, (pv_x + 0.85, pv_y + dy_b, 0.28), (0.12, 0.40, 0.40), rot_z=EAST_ROT_Z)
    # Tall white-silver courtyard lamp post beside pavilion (exact step_4.png right!)
    gp.bm_cyl_axis(bm_nc_steel, (65.8, 36.8, 2.35), 0.058, 4.70, axis="Z", segments=10)
    gp.bm_cyl_axis(bm_nc_pav_dark, (65.8, 36.8, 0.22), 0.15, 0.44, axis="Z", segments=10)
    gp.bm_box(bm_nc_steel, (65.4, 36.8, 4.65), (0.90, 0.24, 0.10))

    objs.append(su.create_mesh_object("Zone_Track_NorthMintApron", bm_nc_mint, palette["court_north_mint"], col))
    objs.append(su.create_mesh_object("Zone_Track_NorthBasketballCourt", bm_nc_conc, palette["court_north_concrete"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Zone_Track_NorthCourtLine", bm_nc_wline, palette["track_line"], col))
    objs.append(su.create_mesh_object("Zone_Track_NorthSoilStrip", bm_nc_soil, palette["tree_soil"], col))
    objs.append(su.create_mesh_object("Zone_Track_NorthCourtSteel", bm_nc_steel, palette["steel_silver"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_NorthHoopPads", bm_nc_pad, palette["hoop_pad_blue"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_NorthBackboardFaces", bm_nc_bb_face, palette["backboard_white"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Zone_Track_NorthBackboardBacks", bm_nc_bb_back, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Zone_Track_NorthHoopRims", bm_nc_rim, palette["hoop_rim_orange"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Track_NorthHoopNets", bm_nc_net, palette["track_line"], col))
    objs.append(su.create_mesh_object("Zone_Track_NEPavilionDark", bm_nc_pav_dark, palette["metal_dark"], col))
    objs.append(su.create_mesh_object("Zone_Track_NEPavilionWood", bm_nc_pav_wood, palette["wood_bridge"], col))
    objs.append(su.create_mesh_object("Zone_Track_NEPavilionBase", bm_nc_pav_base, palette["curb_concrete"], col))

    return objs


def build_basketball_courts(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置重慶樓南側／五權樓西側高細節雙全場壓克力籃球場（4 座藍護墊懸臂籃球架＋黑框紅準星籃板＋橘色籃框與立體籃網＋走廊步下階梯＋排水明溝＋磨石子緩衝步道）。"""
    col = "Zone_Basketball"
    cfg = spec["grounds"]["basketball_courts"]
    x0, x1 = cfg["x_min"], cfg["x_max"]
    y0, y1 = cfg["y_min"], cfg["y_max"]
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    wx, wy = x1 - x0, y1 - y0
    objs: List[bpy.types.Object] = []

    def _add_uv_quad_bb(
        bm_q: bmesh.types.BMesh,
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        p3: Tuple[float, float, float],
    ) -> None:
        uv_l = bm_q.loops.layers.uv.verify()
        vs = [bm_q.verts.new(p) for p in (p0, p1, p2, p3)]
        f = bm_q.faces.new(vs)
        for lp, uv in zip(f.loops, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
            lp[uv_l].uv = uv

    # 1. Light-warm-gray terrazzo transition walkway apron connecting Chongqing 1F south corridor (y=-43.0) & Wuquan 1F west corridor (x=-7.0)
    #    Layered at z=0.044 (< court deck 0.050, < semicircular balcony 0.080 -> ZERO clipping on semicircular tower!)
    bm_walk = bmesh.new()
    _quad_extrude(
        bm_walk,
        [
            (x0 - 0.35, y0 - 0.35),
            (-7.00, y0 - 0.35),
            (-7.00, -43.00),
            (x0 - 0.35, -43.00),
        ],
        0.020,
        0.044,
    )
    objs.append(su.create_mesh_object("Zone_Basketball_Walkway", bm_walk, palette["walkway_gray_paver"], col, uv_scale=0.32))

    # 2. 1F Corridor Step-Down Stairs (from z=0.36m 1F corridor plinth down to z=0.044m court walkway) + Storm Drain Grating!
    bm_steps = bmesh.new()
    bm_drain = bmesh.new()
    # North side along Chongqing 1F open south corridor & breezeway (x=-32.1..-15.5, clear of semicircular tower at x=-15.1..-9.9!)
    for step_i, (sz_top, sy_off) in enumerate(((0.25, -43.16), (0.14, -43.46))):
        gp.bm_box(bm_steps, (-23.80, sy_off, sz_top * 0.5), (16.50, 0.30, sz_top))
    gp.bm_box(bm_drain, (-26.60, -43.82, 0.046), (38.80, 0.28, 0.012))
    # East side along Wuquan 1F open west corridor (y=-66.8..-43.2)
    for step_i, (sz_top, sx_off) in enumerate(((0.25, -7.16), (0.14, -7.46))):
        gp.bm_box(bm_steps, (sx_off, -55.00, sz_top * 0.5), (0.30, 23.40, sz_top))
    gp.bm_box(bm_drain, (-7.82, -55.80, 0.046), (0.28, 25.00, 0.012))
    # Subtle concrete border curb framing the acrylic dual basketball court deck
    gp.bm_box(bm_steps, (cx, cy, 0.036), (wx + 0.28, wy + 0.28, 0.022))
    objs.append(su.create_mesh_object("Zone_Basketball_CorridorSteps", bm_steps, palette["curb_concrete"], col, uv_scale=0.40))
    objs.append(su.create_mesh_object("Zone_Basketball_DrainGrates", bm_drain, palette["drain_grate"], col, uv_scale=1.2))

    # 3. Main Dual Full-Court Acrylic Basketball Deck (z=0.050m, mapped 1:1 to 2048x1280 tex_court_bball.png)
    bm_deck = bmesh.new()
    _add_uv_quad_bb(
        bm_deck,
        (x0, y0, 0.050), (x1, y0, 0.050),
        (x1, y1, 0.050), (x0, y1, 0.050),
    )
    objs.append(su.create_mesh_object("Zone_Basketball_Deck", bm_deck, palette["court_bball"], col, auto_uv=False))

    # 4. 4 Detailed Full-Court Cantilevered Basketball Hoops (centered at U=0.275 & U=0.725 to match court texture key axes!)
    bm_steel = bmesh.new()
    bm_pad = bmesh.new()
    bm_bb_face = bmesh.new()
    bm_bb_back = bmesh.new()
    bm_rim = bmesh.new()
    bm_net = bmesh.new()
    bm_base = bmesh.new()
    bm_wood = bmesh.new()
    bm_dark = bmesh.new()

    for hx in (x0 + wx * 0.275, x0 + wx * 0.725):
        for hy, dir_y in ((y0 + 0.86, 1.0), (y1 - 0.86, -1.0)):
            # Concrete foundation pier + main silver upright post (z=0.05..3.52m) + Royal-Blue cylindrical safety pad (z=0.12..2.00m)
            gp.bm_cyl_axis(bm_base, (hx, hy, 0.09), 0.24, 0.12, axis="Z", segments=12)
            gp.bm_cyl_axis(bm_steel, (hx, hy, 1.80), 0.086, 3.50, axis="Z", segments=12)
            gp.bm_cyl_axis(bm_pad, (hx, hy, 1.06), 0.152, 1.88, axis="Z", segments=14)

            # Upper horizontal boom arm + lower diagonal strut + 4-bar V-truss rear backboard mounting frame
            gp.bm_cyl_p2p(bm_steel, (hx, hy, 3.45), (hx, hy + dir_y * 1.16, 3.45), 0.054, 0.054, segments=10)
            gp.bm_cyl_p2p(bm_steel, (hx, hy, 2.74), (hx, hy + dir_y * 1.13, 3.18), 0.040, 0.040, segments=8)
            for sx_b in (-0.54, 0.54):
                gp.bm_cyl_p2p(bm_steel, (hx, hy + dir_y * 0.62, 3.45), (hx + sx_b, hy + dir_y * 1.16, 3.64), 0.024, 0.024, segments=6)
                gp.bm_cyl_p2p(bm_steel, (hx, hy + dir_y * 0.62, 3.04), (hx + sx_b, hy + dir_y * 1.16, 3.10), 0.024, 0.024, segments=6)

            # White Rectangular Backboard (1.80m x 1.05m) + dark metal outer frame + rear center mounting plate + bottom royal-blue safety edge padding!
            bb_y = hy + dir_y * 1.20
            bb_zc = 3.42
            gp.bm_box(bm_bb_back, (hx, bb_y - dir_y * 0.03, bb_zc), (1.80, 0.045, 1.05))
            gp.bm_box(bm_steel, (hx, bb_y - dir_y * 0.03, bb_zc + 0.535), (1.84, 0.06, 0.035))
            gp.bm_box(bm_steel, (hx - 0.91, bb_y - dir_y * 0.03, bb_zc), (0.035, 0.06, 1.08))
            gp.bm_box(bm_steel, (hx + 0.91, bb_y - dir_y * 0.03, bb_zc), (0.035, 0.06, 1.08))
            gp.bm_box(bm_steel, (hx, bb_y - dir_y * 0.055, bb_zc - 0.14), (0.36, 0.04, 0.34))
            gp.bm_box(bm_pad, (hx, bb_y - dir_y * 0.025, bb_zc - 0.535), (1.84, 0.075, 0.075))
            if dir_y > 0:
                # Facing NORTH (+Y)
                _add_uv_quad_bb(
                    bm_bb_face,
                    (hx + 0.90, bb_y, bb_zc - 0.525), (hx - 0.90, bb_y, bb_zc - 0.525),
                    (hx - 0.90, bb_y, bb_zc + 0.525), (hx + 0.90, bb_y, bb_zc + 0.525),
                )
            else:
                # Facing SOUTH (-Y)
                _add_uv_quad_bb(
                    bm_bb_face,
                    (hx - 0.90, bb_y, bb_zc - 0.525), (hx + 0.90, bb_y, bb_zc - 0.525),
                    (hx + 0.90, bb_y, bb_zc + 0.525), (hx - 0.90, bb_y, bb_zc + 0.525),
                )

            # Breakaway orange steel rim (z=3.05m, r=0.23m) + mounting bracket + 12-strand 3D conical white nylon net
            rim_y = bb_y + dir_y * 0.28
            rim_z = 3.05
            gp.bm_box(bm_rim, (hx, bb_y + dir_y * 0.04, rim_z), (0.14, 0.08, 0.10))
            r_rim = 0.23
            n_rim = 12
            for ri in range(n_rim):
                a0 = 2.0 * math.pi * ri / n_rim
                a1 = 2.0 * math.pi * ((ri + 1) % n_rim) / n_rim
                p_r0 = (hx + math.cos(a0) * r_rim, rim_y + math.sin(a0) * r_rim, rim_z)
                p_r1 = (hx + math.cos(a1) * r_rim, rim_y + math.sin(a1) * r_rim, rim_z)
                gp.bm_cyl_p2p(bm_rim, p_r0, p_r1, 0.016, 0.016, segments=6)
                if ri % 2 == 0:
                    a_bot = a0 + math.pi / n_rim
                    p_b = (hx + math.cos(a_bot) * 0.13, rim_y + math.sin(a_bot) * 0.13, rim_z - 0.42)
                    gp.bm_cyl_p2p(bm_net, p_r0, p_b, 0.008, 0.008, segments=4)
                    gp.bm_cyl_p2p(bm_net, p_r1, p_b, 0.008, 0.008, segments=4)

    # 5. Sideline Players' Rest Benches along North Apron Center & West Apron (clear of court lines & corridor stairs!)
    for bx_b, by_b, brot in [(-27.40, -44.65, 0.0), (-41.50, -44.65, 0.0)]:
        gp.bm_box(bm_wood, (bx_b, by_b, 0.46), (2.40, 0.46, 0.08), rot_z=brot)
        for lx_off in (-0.88, 0.88):
            gp.bm_box(bm_dark, (bx_b + lx_off, by_b, 0.24), (0.10, 0.40, 0.42), rot_z=brot)

    objs.append(su.create_mesh_object("Zone_Basketball_Poles", bm_steel, palette["metal_dark"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Basketball_HoopPads", bm_pad, palette["hoop_pad_blue"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Basketball_BackboardFaces", bm_bb_face, palette["backboard_white"], col, auto_uv=False))
    objs.append(su.create_mesh_object("Zone_Basketball_Backboards", bm_bb_back, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Zone_Basketball_HoopRims", bm_rim, palette["hoop_rim_orange"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Basketball_HoopNets", bm_net, palette["track_line"], col))
    objs.append(su.create_mesh_object("Zone_Basketball_HoopBases", bm_base, palette["curb_concrete"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Basketball_BenchesWood", bm_wood, palette["wood_bridge"], col))
    objs.append(su.create_mesh_object("Zone_Basketball_BenchesLegs", bm_dark, palette["metal_dark"], col))

    return objs


def build_courtyard_and_trees(spec: dict, palette: Dict[str, bpy.types.Material]) -> List[bpy.types.Object]:
    """建置中庭生態池、小拱橋、高細節大王椰子與平滑有機多層次喬木林蔭。"""
    col = "Zone_Courtyard"
    objs: List[bpy.types.Object] = []

    bm_lawn = bmesh.new()
    gp.bm_box(bm_lawn, (-19.5, 16.5, 0.02), (24.0, 16.0, 0.08))
    gp.bm_box(bm_lawn, (-22.0, -18.5, 0.02), (26.0, 18.0, 0.08))
    gp.bm_box(bm_lawn, (-62.0, -56.0, 0.02), (28.0, 22.0, 0.08))
    # v12.6 Unified Continuous Track-Perimeter Lawn (covers ENTIRE east/north/south track surround strictly INSIDE walls & Heping fence — ZERO stray red-brick triangles!)
    # Layered cleanly at z=0.036 (< walkway 0.042 < north court 0.0485 < PU track 0.052)!
    _quad_extrude(
        bm_lawn,
        [
            (20.80, -69.55),
            (66.50, -69.55),
            (east_wall_x(-62.5) - 0.12, -62.5),
            (east_wall_x(47.8) - 0.12, 47.8),
            (60.50, heping_south_edge_y(60.50) - HEPING_EAST_WALK_W - 0.06),
            (20.80, heping_south_edge_y(20.80) - HEPING_EAST_WALK_W - 0.06),
        ],
        -0.02,
        0.036,
    )
    # Heping Bldg / Wuquan North natural boulder-lined green strip clipped cleanly around West B1 green driveway ramp (x=-3.9..+0.25)!
    _quad_extrude(
        bm_lawn,
        [
            (-60.5, 39.0),
            (-3.92, 39.0),
            (-3.92, heping_south_edge_y(-3.92) - 0.18),
            (-60.5, heping_south_edge_y(-60.5) - 0.18),
        ],
        -0.02,
        0.045,
    )
    _quad_extrude(
        bm_lawn,
        [
            (0.26, 39.5),
            (6.6, 39.5),
            (6.6, heping_south_edge_y(6.6) - 0.18),
            (0.26, heping_south_edge_y(0.26) - 0.18),
        ],
        -0.02,
        0.045,
    )
    # v11.8 Wuquan Bldg East Royal Palm & Manicured Round-Hedge Lawn Strip leading right up to Stage South Cheek Wall (final_step_8.png!)
    _quad_extrude(
        bm_lawn,
        [
            (6.48, -63.8),
            (9.45, -63.8),
            (9.45, -20.42),
            (6.48, -20.42),
        ],
        0.036,
        0.064,
    )
    objs.append(su.create_mesh_object("Zone_Courtyard_Lawns", bm_lawn, palette["grass"], col, uv_scale=0.14))

    # Ecological pond + white picket fence + arch bridge + lotus pads (campus_08.jpg)
    pcfg = spec["grounds"]["pond"]
    px, py = pcfg["center"]
    rx, ry = pcfg["rx"], pcfg["ry"]
    bm_water = bmesh.new()
    bm_stone = bmesh.new()
    bm_fence = bmesh.new()
    bm_bridge = bmesh.new()
    bm_lotus = bmesh.new()

    segs = 32
    v_top, v_bot = [], []
    for i in range(segs):
        a = 2.0 * math.pi * i / segs
        vx, vy = px + math.cos(a) * rx, py + math.sin(a) * ry
        v_top.append(bm_water.verts.new((vx, vy, 0.14)))
        v_bot.append(bm_water.verts.new((vx, vy, 0.02)))
        gp.bm_box(bm_stone, (px + math.cos(a) * (rx + 0.28), py + math.sin(a) * (ry + 0.28), 0.18), (0.85, 0.72, 0.34), rot_z=a)
        fx, fy = px + math.cos(a) * (rx + 0.92), py + math.sin(a) * (ry + 0.92)
        gp.bm_box(bm_fence, (fx, fy, 0.38), (0.075, 0.075, 0.76))
        a_next = 2.0 * math.pi * ((i + 1) % segs) / segs
        nx, ny = px + math.cos(a_next) * (rx + 0.92), py + math.sin(a_next) * (ry + 0.92)
        gp.bm_cyl_p2p(bm_fence, (fx, fy, 0.65), (nx, ny, 0.65), 0.032, 0.032, segments=6)
    bm_water.faces.new(v_top)
    bm_water.faces.new(list(reversed(v_bot)))

    # Floating aquatic plant bowls in pond
    for lx, ly in [(px + 1.8, py + 0.8), (px + 3.2, py - 0.6), (px + 0.6, py - 1.5), (px + 4.1, py + 1.2)]:
        gp.bm_cyl_axis(bm_lotus, (lx, ly, 0.20), 0.65, 0.12, axis="Z", segments=10)

    # Arched wooden footbridge with rope railings
    for i in range(11):
        t = (i - 5) / 5.0
        by_step = py + t * (ry * 0.96)
        bz = 0.24 + (1.0 - t * t) * 0.60
        gp.bm_box(bm_bridge, (px - 1.6, by_step, bz), (1.85, 0.78, 0.14))
        for side_x in (px - 2.48, px - 0.72):
            gp.bm_box(bm_bridge, (side_x, by_step, bz + 0.45), (0.085, 0.085, 0.90))
            if i < 10:
                t2 = (i + 1 - 5) / 5.0
                by2 = py + t2 * (ry * 0.96)
                bz2 = 0.24 + (1.0 - t2 * t2) * 0.60
                gp.bm_cyl_p2p(bm_bridge, (side_x, by_step, bz + 0.82), (side_x, by2, bz2 + 0.82), 0.035, 0.035, segments=6)

    objs.append(su.create_mesh_object("Zone_Courtyard_PondWater", bm_water, palette["pond_water"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_PondRim", bm_stone, palette["wall_stone_cream"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_PondFence", bm_fence, palette["railing_white"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_Bridge", bm_bridge, palette["wood_bridge"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_Lotus", bm_lotus, palette["tree_foliage_c"], col))

    # D-04: Guanghe east courtyard steps + accessible ramp with handrails, brick planter curbs & circular tree benches
    bm_ramp = bmesh.new()
    bm_ramp_rail = bmesh.new()
    bm_curb_brick = bmesh.new()
    # East steps descending from Guanghe 1F breezeway (x=-31.5, z=1.15) into courtyard
    for si in range(6):
        sh = 1.15 * (6 - si) / 6.0
        gp.bm_box(bm_ramp, (-31.3 + si * 0.36, 0.5, sh * 0.5), (0.38, 9.6, sh))
    # Accessible side ramp with double stainless steel handrails
    gp.bm_box(bm_ramp, (-29.8, -5.8, 0.52), (5.2, 1.5, 0.20), rot_y=math.radians(12.0))
    for ry in (-6.5, -5.1):
        gp.bm_cyl_p2p(bm_ramp_rail, (-32.2, ry, 1.95), (-27.4, ry, 0.92), 0.03, 0.03, segments=6)
        gp.bm_cyl_axis(bm_ramp_rail, (-32.2, ry, 1.45), 0.025, 0.95, axis="Z", segments=6)
        gp.bm_cyl_axis(bm_ramp_rail, (-27.4, ry, 0.46), 0.025, 0.92, axis="Z", segments=6)
    # Brick low planter borders framing north & south courtyard lawns (act_12/22!)
    for cx_l, cy_l, lw, ld in [(-19.5, 16.5, 24.0, 16.0), (-22.0, -18.5, 26.0, 18.0)]:
        gp.bm_box(bm_curb_brick, (cx_l, cy_l - ld * 0.5, 0.24), (lw + 0.3, 0.28, 0.48))
        gp.bm_box(bm_curb_brick, (cx_l, cy_l + ld * 0.5, 0.24), (lw + 0.3, 0.28, 0.48))
        gp.bm_box(bm_curb_brick, (cx_l - lw * 0.5, cy_l, 0.24), (0.28, ld, 0.48))
        gp.bm_box(bm_curb_brick, (cx_l + lw * 0.5, cy_l, 0.24), (0.28, ld, 0.48))
    # Circular stone tree-pit seating benches under courtyard shade trees
    for bx_t, by_t in [(-26.0, -16.5), (-16.0, -20.5)]:
        gp.bm_cyl_axis(bm_ramp, (bx_t, by_t, 0.26), 1.65, 0.52, axis="Z", segments=16)

    objs.append(su.create_mesh_object("Zone_Courtyard_StepsRampBenches", bm_ramp, palette["wall_stone_cream"], col, uv_scale=0.4))
    objs.append(su.create_mesh_object("Zone_Courtyard_RampHandrails", bm_ramp_rail, palette["steel_silver"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_BrickCurbs", bm_curb_brick, palette["wall_brick_red"], col, uv_scale=0.5))

    # Realistic Royal Palms + Multi-branch Organic Smooth Trees + Gate Planter Shrubs
    rng = random.Random(2026)
    bm_trunk = bmesh.new()
    bm_palm_tr = bmesh.new()
    bm_palm_sh = bmesh.new()
    bm_palm_fr = bmesh.new()
    bm_fol_a = bmesh.new()
    bm_fol_b = bmesh.new()
    bm_fol_c = bmesh.new()
    bm_shrub_r = bmesh.new()

    # Full row of towering Royal Palms along Guanghe St front (strictly INSIDE wall_x(ty) + 1.6m!) + Pond palms
    for idx, (tx, ty, th) in enumerate([
        (px - 6.8, py - 3.6, 8.2),
        (px - 5.2, py + 4.2, 7.5),
        (px + 5.8, py + 3.5, 8.6),
        # North front row (10 廣和街 along Heping west gable & north fence!)
        (wall_x(36.2) + 1.8, 36.2, 13.8),
        (wall_x(31.8) + 1.8, 31.8, 14.2),
        (wall_x(26.8) + 1.8, 26.8, 13.4),
        (wall_x(21.8) + 1.8, 21.8, 13.0),
        # Mid front row (27 廣和街 behind school sign & south grille fence! Clear of y=-5.5 gate sightline to South Connector stairs!)
        (wall_x(-9.5) + 1.9, -9.5, 13.4),
        (wall_x(-13.5) + 1.9, -13.5, 12.6),
        (wall_x(-18.5) + 1.9, -18.5, 13.2),
        (wall_x(-23.5) + 1.9, -23.5, 12.8),
        (wall_x(-28.0) + 1.9, -28.0, 12.4),
        # v11 Heping Bldg North Royal Palms (129 和平路 D final_step_14 iconic palm!)
        (-48.6, 42.1, 9.6),
        (-36.2, 43.2, 10.2),
        # v12.5 Exact 9 五權街 step_6_shot_1.png: Royal Palms ONLY along south wing solid facade (clear of vertical banner & accessible ramp!)
        (8.85, -60.5, 13.4),
        (8.85, -53.2, 13.8),
        (8.85, -45.8, 13.2),
    ]):
        _add_royal_palm(bm_palm_tr, bm_palm_sh, bm_palm_fr, tx, ty, th, seed=idx)

    # v11 Heping Bldg North Natural Mossy Landscape Boulders + Standing Monolith Rock + Lush Hedges (129 和平路 A/B/C/D!)
    bm_rocks = bmesh.new()

    def _add_landscape_boulder(cx: float, cy: float, cz: float, rx: float, ry: float, rz: float, seed_off: float = 0.0) -> None:
        ret = bmesh.ops.create_icosphere(bm_rocks, subdivisions=2, radius=1.0)
        for v in ret["verts"]:
            # Faceted rough natural stone perturbation + flattened base seated cleanly in grass!
            ang_f = math.sin(v.co.x * 5.2 + seed_off) * math.cos(v.co.y * 4.8 + seed_off * 1.3) + 0.5 * math.sin(v.co.z * 6.5 - seed_off)
            n = 1.0 + 0.24 * ang_f + rng.uniform(-0.08, 0.08)
            vx = v.co.x * rx * n
            vy = v.co.y * ry * n
            vz = v.co.z * rz * n
            if vz < -rz * 0.45:
                vz = -rz * 0.45
            v.co.x = cx + vx
            v.co.y = cy + vy
            v.co.z = cz + vz

    # Row of 36 rough gray-brown landscape boulders tightly bordering Heping Rd red curb line (x=-55.2..-19.8, west of skybridge at -17.5!)
    for idx_rk in range(30):
        rx_pos = -55.2 + idx_rk * 1.22 + rng.uniform(-0.14, 0.14)
        ry_pos = heping_south_edge_y(rx_pos) - rng.uniform(0.46, 0.68)
        _add_landscape_boulder(
            rx_pos, ry_pos, 0.24,
            rng.uniform(0.36, 0.62), rng.uniform(0.30, 0.48), rng.uniform(0.26, 0.44),
            seed_off=idx_rk * 2.13,
        )
    # Iconic 1.42m-tall rounded natural monolithic standing boulder at 129 和平路 D west end (final_step_14!)
    ret_mono = bmesh.ops.create_icosphere(bm_rocks, subdivisions=3, radius=1.0)
    for v in ret_mono["verts"]:
        # Smooth organic tapered standing monolith (rounded crown, NO sharp spike!)
        taper = 1.0 - 0.28 * max(0.0, v.co.z)
        ang_m = 0.08 * math.sin(v.co.x * 4.2 + 1.1) * math.cos(v.co.y * 4.0) + 0.05 * math.sin(v.co.z * 5.0)
        vx = v.co.x * 0.44 * taper * (1.0 + ang_m)
        vy = v.co.y * 0.34 * taper * (1.0 + ang_m)
        vz = v.co.z * 0.78 * (1.0 + ang_m * 0.4)
        if vz < -0.52:
            vz = -0.52
        v.co.x = -56.15 + vx
        v.co.y = 40.92 + vy
        v.co.z = 0.68 + vz
    objs.append(su.create_mesh_object("Zone_Heping_LandscapeRocks", bm_rocks, palette["rock_landscape"], col, smooth=True, uv_scale=0.8))

    # Continuous lush ruffled hedges & spilling dark-green groundcover tucked tightly behind Heping boulders (129 A/B/C/D!)
    def _add_heping_bush(bm_t: bmesh.types.BMesh, cx: float, cy: float, cz: float, rx: float, ry: float, rz: float, flat_top: bool = False) -> None:
        ret = bmesh.ops.create_icosphere(bm_t, subdivisions=2, radius=1.0)
        for v in ret["verts"]:
            n = 1.0 + 0.18 * math.sin(v.co.x * 7.5 + cx * 1.4) * math.cos(v.co.y * 6.8 + cy * 1.3) + rng.uniform(-0.07, 0.07)
            vx = v.co.x * rx * n
            vy = v.co.y * ry * n
            vz = v.co.z * rz * n
            if flat_top and vz > rz * 0.55:
                vz = rz * 0.55 + (vz - rz * 0.55) * 0.25
            v.co.x = cx + vx
            v.co.y = cy + vy
            v.co.z = cz + vz

    for hx_i in range(44):
        hx_p = -55.4 + hx_i * 0.84
        if -19.8 <= hx_p <= -15.2:
            continue
        hy_p = heping_south_edge_y(hx_p) - 1.08 + rng.uniform(-0.06, 0.06)
        if -38.5 <= hx_p <= -24.5:
            # Continuous manicured flat-topped box hedge along terrace retaining wall & stairs (step_6!)
            _add_heping_bush(bm_fol_b if hx_i % 2 == 0 else bm_fol_a, hx_p, hy_p, 0.44, 0.66, 0.54, 0.42, flat_top=True)
        else:
            # Lush natural spilling green shrubs hugging landscape boulders (129 D final_step_14!)
            _add_heping_bush(bm_fol_a if hx_i % 2 == 0 else bm_fol_c, hx_p, hy_p, 0.40, 0.72, 0.60, 0.36, flat_top=False)
    # Low lush shrubs framing East silver shutter & West 3-tone shutter sides (exact step_27 & step_31 detail!)
    for sx_sh in (1.4, 2.5, 3.8, 5.2, -5.2, -7.2, -9.4, -11.6, -13.6):
        _add_heping_bush(bm_fol_a, sx_sh, heping_south_edge_y(sx_sh) - 1.35, 0.38, 0.68, 0.52, 0.34, flat_top=False)
    # Bright lime-green manicured shrub inside 129 D NW corner white-tile planter right next to standing monolith!
    for ix_c in range(4):
        _add_heping_bush(bm_fol_c, -59.2 + ix_c * 0.72, 40.35 + ix_c * 0.08, 0.72, 0.55, 0.48, 0.34, flat_top=False)
    # Lush layered burgundy + bright green shrubs in 10 廣和街 NW corner white-tile curved planter (step_111!)
    for i in range(10):
        t_sh = i / 9.0
        sx_nw = -65.2 + t_sh * 5.0
        sy_nw = 39.2 + t_sh * 0.95
        target_bm = bm_shrub_r if i % 3 == 0 else bm_fol_c
        mat = Matrix.Translation(Vector((sx_nw, sy_nw, 0.78))) @ Matrix.Diagonal((0.55, 0.52, 0.44, 1.0))
        bmesh.ops.create_icosphere(target_bm, subdivisions=1, radius=1.0, matrix=mat)
    # Lush hedges tucked inside north bronze fence (10/50 廣和街!)
    for hy_n in range(15, 36, 3):
        gp.bm_box(bm_fol_b, (wall_x(hy_n) + 0.72, hy_n, 0.78), (0.90, 2.6, 0.68), rot_z=GUANGHE_ROT_Z)
    # Colorful green + burgundy shrubs inside main gate sign planter (wall_x - 0.68m!)
    for i in range(11):
        sy = -14.2 + i * 0.98
        target_bm = bm_shrub_r if i % 2 == 0 else bm_fol_c
        mat = Matrix.Translation(Vector((wall_x(sy) - 0.55, sy, 0.82))) @ Matrix.Diagonal((0.44, 0.50, 0.34, 1.0))
        bmesh.ops.create_icosphere(target_bm, subdivisions=1, radius=1.0, matrix=mat)

    def _add_ruffled_shrub(bm_t: bmesh.types.BMesh, cx: float, cy: float, cz: float, rx: float, ry: float, rz: float) -> None:
        ret = bmesh.ops.create_icosphere(bm_t, subdivisions=2, radius=1.0)
        for v in ret["verts"]:
            n = 1.0 + 0.22 * math.sin(v.co.x * 8.1 + cx * 1.7) * math.cos(v.co.y * 7.4 + cy * 1.3) + rng.uniform(-0.10, 0.10)
            v.co.x = cx + v.co.x * rx * n
            v.co.y = cy + v.co.y * ry * n
            v.co.z = cz + v.co.z * rz * n

    # v12.11 27 廣和街 Forecourt South Garden Planter Topiary Ball Shrubs & Cloud-Pruned Podocarpus strictly NORTH of stair cheek wall (step_18_shot_1.png & final_step_30.png!)
    for tx_g, ty_g, tz_g, rx_g, ry_g, rz_g, bm_g in [
        (-59.6, -13.6, 1.05, 0.58, 0.58, 0.54, bm_fol_c),
        (-58.2, -14.2, 1.12, 0.55, 0.55, 0.52, bm_fol_c),
        (-56.6, -14.4, 1.08, 0.64, 0.62, 0.54, bm_fol_a),
        (-55.0, -14.6, 1.18, 0.52, 0.52, 0.50, bm_fol_c),
        (-57.6, -11.5, 2.35, 1.55, 1.45, 1.38, bm_fol_a),
        (-55.2, -12.4, 2.55, 1.70, 1.60, 1.50, bm_fol_b),
        (-53.2, -13.4, 2.35, 1.45, 1.40, 1.32, bm_fol_a),
        # Cloud-pruned layered topiary tree right beside Chongqing 1F Library white-column portico (final_step_30.png right!)
        (-52.4, -27.2, 1.45, 0.95, 0.72, 0.36, bm_fol_a),
        (-51.8, -26.8, 2.15, 1.05, 0.78, 0.38, bm_fol_b),
        (-52.2, -27.0, 2.78, 0.88, 0.68, 0.34, bm_fol_a),
    ]:
        _add_ruffled_shrub(bm_g, tx_g, ty_g, tz_g, rx_g, ry_g, rz_g)
    # Wooden support props under forecourt garden trees (visible in step_18_shot_1.png!)
    for px_pr, py_pr in [(-56.6, -14.4), (-55.0, -14.6)]:
        gp.bm_cyl_p2p(bm_trunk, (px_pr - 0.45, py_pr - 0.35, 0.45), (px_pr, py_pr, 1.55), 0.045, 0.04, segments=6)
        gp.bm_cyl_p2p(bm_trunk, (px_pr + 0.45, py_pr - 0.35, 0.45), (px_pr, py_pr, 1.55), 0.045, 0.04, segments=6)
    gp.bm_cyl_p2p(bm_trunk, (-52.1, -27.0, 0.05), (-52.0, -26.9, 2.70), 0.14, 0.08, segments=8)

    # v9 South Guanghe St iconic continuous layered bright-green + dark-burgundy organic shrub beds (76/3/12 廣和街!)
    for sx_s in (-70.0, -69.1, -68.2):
        _add_ruffled_shrub(bm_fol_c, sx_s, SOUTH_WALL_Y - 0.72, 0.42, 0.58, 0.46, 0.32)
        _add_ruffled_shrub(bm_shrub_r, sx_s + 0.30, SOUTH_WALL_Y - 0.44, 0.56, 0.42, 0.34, 0.40)
    for bx0, bx1 in [(-47.2, 7.5), (17.1, 19.6), (21.8, 66.2)]:
        x_cur = bx0
        idx_sh = 0
        while x_cur <= bx1:
            jit_y = rng.uniform(-0.08, 0.08)
            jit_r = rng.uniform(0.88, 1.16)
            _add_ruffled_shrub(
                bm_fol_c if idx_sh % 2 == 0 else bm_fol_b,
                x_cur, SOUTH_WALL_Y - 0.86 + jit_y, 0.40,
                0.68 * jit_r, 0.44 * jit_r, 0.30 * jit_r,
            )
            if idx_sh % 2 == 0:
                _add_ruffled_shrub(
                    bm_shrub_r,
                    x_cur + rng.uniform(0.15, 0.48), SOUTH_WALL_Y - 0.42 + jit_y * 0.5, 0.58,
                    0.50 * jit_r, 0.34 * jit_r, 0.42 * jit_r,
                )
            x_cur += 0.92
            idx_sh += 1
    # v12.5 Exact 9 & 2 五權街 manicured shrubs along south solid facade (clear of accessible ramp!) + north flank of stage beside 3-bay grand stairs!
    for py_sh in (-62.5, -57.5, -52.5, -47.5, -42.5, -37.5, -6.2, -5.0):
        _add_ruffled_shrub(bm_fol_b, 8.25 if py_sh < -30 else 8.85, py_sh, 0.56 if py_sh > -10 else 0.48, 0.85, 1.05, 0.58 if py_sh > -10 else 0.48)
    for i in range(13):
        a_se = -math.pi * 0.5 + (math.pi * 0.5) * (i / 12.0)
        cx_se = 66.5 + math.cos(a_se) * 7.65
        cy_se = -62.8 + math.sin(a_se) * 7.65
        _add_ruffled_shrub(bm_fol_c if i % 2 == 0 else bm_fol_b, cx_se, cy_se, 0.44, 0.65, 0.58, 0.36)
        cx_r = 66.5 + math.cos(a_se) * 7.28
        cy_r = -62.8 + math.sin(a_se) * 7.28
        _add_ruffled_shrub(bm_shrub_r, cx_r, cy_r, 0.64, 0.46, 0.42, 0.44)

    tree_pts: List[Tuple[float, float, float, float]] = []
    # East track-side shade trees carefully spaced AROUND the SE shed, climbing poles (y=-52..-46) & pull-up bars (y=-32..-12.8) so zero trunks clip equipment!
    for tx_et, ty_et, th_et, tr_et in [
        (67.2, -62.5, 11.8, 3.6),   # SE corner dense canopy behind shed
        (68.2, -53.8, 12.2, 3.4),   # Framing south edge of climbing poles
        (67.5, -40.2, 13.4, 4.1),   # Iconic large banyan tree between climbing poles & stretching bars (step_12_shot_1.png!)
        (69.8, -22.5, 12.5, 3.3),   # Tree tucked near east wall between triple-bars & stepped pull-up bars (step_10_shot_1.png!)
        (67.2, -6.5, 11.6, 3.5),
        (66.8, 2.5, 12.0, 3.6),
        (66.5, 11.5, 11.4, 3.5),
        (66.2, 20.5, 12.6, 3.8),
        (65.8, 29.5, 11.8, 3.5),
        (65.8, 35.2, 12.0, 3.4),    # Framing south edge of NE pavilion (zero clip!)
    ]:
        tree_pts.append((tx_et, ty_et, th_et, tr_et))
    # v12.6 Track-North & North Basketball Court Shade Trees strictly inside north soil strip (x=31..62) + banyan behind hoops — ZERO trunks on walkway, 100m sprint track or concrete court!
    for tx_nt, th_nt, tr_nt in [
        (31.8, 12.0, 3.5),
        (38.2, 12.6, 3.8),
        (44.8, 13.0, 3.9),
        (51.2, 12.4, 3.7),
        (57.4, 12.8, 3.8),
        (62.4, 12.2, 3.6),
    ]:
        tree_pts.append((tx_nt, heping_south_edge_y(tx_nt) - HEPING_EAST_WALK_W - 1.45, th_nt, tr_nt))
    # Iconic large banyan trees strictly OUTSIDE north track curve (r > 22.1m > r_out=21.0m) & south of court (y < 33.4) — ZERO track clipping!
    tree_pts.append((51.5, 32.0, 12.6, 3.6))
    tree_pts.append((58.2, 30.2, 11.4, 3.3))
    # Wooden support props leaning under central banyan tree strictly in grass pocket (r > 21.8m, y < 33.2)!
    gp.bm_cyl_p2p(bm_trunk, (50.6, 32.6, 0.0), (51.3, 32.1, 2.8), 0.08, 0.07, segments=6)
    gp.bm_cyl_p2p(bm_trunk, (52.6, 32.2, 0.0), (51.7, 32.0, 2.9), 0.08, 0.07, segments=6)
    for hx_t, hy_off, th_h, tr_h in [
        (-53.0, -1.65, 8.8, 2.8), (-46.5, -1.55, 8.4, 2.6), (-38.5, -1.55, 9.2, 2.9),
        (-28.5, -1.60, 8.2, 2.5), (-11.5, -2.05, 9.6, 3.0), (-5.8, -2.15, 8.8, 2.6), (3.8, -2.05, 8.6, 2.6),
    ]:
        tree_pts.append((hx_t, heping_south_edge_y(hx_t) + hy_off, th_h, tr_h))
    # Opposite north-side Heping Rd sidewalk trees for authentic street framing (166/147 step_2/4/6 right edge!)
    for ox_t in (46.0, 34.0, 22.0, 10.0, -4.0):
        tree_pts.append((ox_t, heping_south_edge_y(ox_t) + 11.9, rng.uniform(8.8, 11.2), rng.uniform(2.6, 3.3)))
    for x in range(30, 62, 8):
        tree_pts.append((x + rng.uniform(-1.5, 1.5), -64.5 + rng.uniform(-1.5, 1.5), rng.uniform(8.5, 12.0), rng.uniform(2.9, 3.8)))
    # South Guanghe St tall shade trees planted right inside wall shrub strip (framing Gate 3 at x=6.2 & x=23.6, final_step_15!)
    for sx_t in (-68.2, -46.2, -37.5, -28.5, -19.5, -10.5, -1.5, 6.2, 23.6, 33.5, 43.5, 53.5, 63.5):
        tree_pts.append((sx_t, SOUTH_WALL_Y - 0.65, rng.uniform(10.2, 13.6), rng.uniform(2.8, 3.6)))
    # SE curved corner shade tree (final_step_157!)
    tree_pts.append((72.8, -68.2, 11.4, 3.1))
    # East Wuquan St tree-pit low green shrubs + tall street-tree colonnade (exact step_163..180!)
    east_tree_ys = (-60.2, -51.5, -42.5, -31.5, -18.5, -10.5, -1.5, 7.5, 19.5, 28.5, 36.2, 43.2)
    for idx_e, ty_e in enumerate(east_tree_ys):
        tx_e = east_curb_x(ty_e) - 0.96
        _add_ruffled_shrub(bm_fol_b if idx_e % 2 == 0 else bm_fol_c, tx_e, ty_e, 0.44, 0.62, 0.60, 0.34)
        if idx_e == 0:
            _add_ruffled_shrub(bm_shrub_r, tx_e - 0.25, ty_e + 0.25, 0.62, 0.42, 0.40, 0.44)
        tree_pts.append((tx_e, ty_e, rng.uniform(10.6, 13.8), rng.uniform(2.5, 3.3)))
    # NE corner lush banyan-style shade tree strictly behind pavilion & clear of north basketball court!
    tree_pts.append((64.8, 46.8, 12.2, 3.6))

    # Street trees centered 100% INSIDE their concrete square tree pits on Guanghe St sidewalk!
    for ty in (-6.1, -12.8, -21.2, 10.4, 20.6, 28.4, -46.5, -58.5):
        tree_pts.append((curb_x(ty) + 1.20, ty, rng.uniform(8.8, 11.6), rng.uniform(2.0, 2.6)))
    for tx, ty in [
        (-63.5, 24.5), (-64.5, -24.5),
        (-28.0, 20.5), (-13.0, 11.0), (-26.0, -16.5), (-16.0, -20.5),
        (-38.0, -20.0), (-54.0, -52.0), (-56.0, -64.0),
    ]:
        tree_pts.append((tx, ty, rng.uniform(7.5, 10.8), rng.uniform(2.6, 3.5)))

    fol_bms = [bm_fol_a, bm_fol_b, bm_fol_c]
    for tx, ty, th, tr in tree_pts:
        _add_organic_tree(bm_trunk, fol_bms, tx, ty, th, tr, rng)

    objs.append(su.create_mesh_object("Zone_Courtyard_TreeTrunks", bm_trunk, palette["tree_trunk"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_PalmTrunks", bm_palm_tr, palette["palm_trunk"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_PalmSheaths", bm_palm_sh, palette["palm_sheath"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_PalmFronds", bm_palm_fr, palette["palm_frond"], col))
    objs.append(su.create_mesh_object("Zone_Courtyard_FoliageA", bm_fol_a, palette["tree_foliage_a"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_FoliageB", bm_fol_b, palette["tree_foliage_b"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_FoliageC", bm_fol_c, palette["tree_foliage_c"], col, smooth=True))
    objs.append(su.create_mesh_object("Zone_Courtyard_ShrubsRed", bm_shrub_r, palette["shrub_red"], col, smooth=True))

    return objs
