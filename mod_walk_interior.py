"""全校 4 棟校舍（廣和樓、和平樓、五權樓、重慶樓）通用中空教室建模與步行碰撞資料匯出模組。

職責：
1. 將各棟實心開間盒替換為帶真實門洞、窗洞與隔間牆的中空室體（保留原外觀風格與街景細節）。
2. 為每一間可進入空間計算不與窗洞重疊的門位、進出法向與橫拉滑門方向，供前端產生可開關門板動畫與室內黑板／桌椅。
3. 統一收集 4 棟之樓層高度、樓梯／電梯自動爬升觸發區與牆體／欄杆碰撞盒，輸出 walk_data_campus.json。
"""
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

import bmesh

import geom_primitives as gp

# 全校步行資料暫存器（於 assemble_campus 開頭清空，總裝完成後寫出）
WALK_REGISTRY: Dict[str, Any] = {
    "version": 2,
    "buildings": {},
    "rooms": [],
    "colliders": [],
}


def reset_walk_registry() -> None:
    WALK_REGISTRY["version"] = 2
    WALK_REGISTRY["buildings"] = {}
    WALK_REGISTRY["rooms"] = []
    WALK_REGISTRY["colliders"] = []


def export_walk_data(root_dir: str) -> str:
    payload = {
        "version": WALK_REGISTRY["version"],
        "buildings": WALK_REGISTRY["buildings"],
        "rooms": WALK_REGISTRY["rooms"],
        "colliders": [[round(v, 3) for v in c] for c in WALK_REGISTRY["colliders"]],
    }
    out_path = os.path.join(root_dir, "walk_data_campus.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    return out_path


def wall_rects(ua: float, ub: float, openings: Sequence[Tuple[float, float, float, float]], z_lo: float, z_hi: float) -> List[Tuple[float, float, float, float]]:
    """沿任意主軸 U 將牆面依 openings=[(u0, u1, z0, z1)] 切為合併後的實心矩形 (u0, u1, z0, z1)。"""
    us = {ua, ub}
    for o in openings:
        us.add(min(max(o[0], ua), ub))
        us.add(min(max(o[1], ua), ub))
    us_sorted = sorted(us)
    segs = []
    for i in range(len(us_sorted) - 1):
        s0, s1 = us_sorted[i], us_sorted[i + 1]
        if s1 - s0 < 1e-4:
            continue
        mid = 0.5 * (s0 + s1)
        opens = sorted((o[2], o[3]) for o in openings if o[0] <= mid <= o[1])
        zs = []
        cur = z_lo
        for a, b in opens:
            if a > cur:
                zs.append((cur, min(a, z_hi)))
            cur = max(cur, b)
        if cur < z_hi:
            zs.append((cur, z_hi))
        segs.append((s0, s1, tuple((round(a, 4), round(b, 4)) for a, b in zs)))
    merged = []
    for s0, s1, zs in segs:
        if merged and merged[-1][2] == zs and abs(merged[-1][1] - s0) < 1e-4:
            merged[-1] = (merged[-1][0], s1, zs)
        else:
            merged.append((s0, s1, zs))
    rects = []
    for s0, s1, zs in merged:
        for a, b in zs:
            if b - a > 1e-3:
                rects.append((s0, s1, a, b))
    return rects


def pick_door_u(a: float, b: float, win_spans: Sequence[Tuple[float, float]], door_w: float = 1.1) -> float:
    """在區間 [a, b] 內挑選最靠近中央、且不與窗洞重疊的門中心位置。"""
    c = 0.5 * (a + b)
    lo, hi = a + 0.55 + door_w * 0.5, b - 0.55 - door_w * 0.5
    if hi < lo:
        return c
    cands = [c]
    k = 1
    while c + k * 0.15 <= hi or c - k * 0.15 >= lo:
        for s in (1.0, -1.0):
            u = c + s * k * 0.15
            if lo <= u <= hi:
                cands.append(u)
        k += 1
    for u in cands:
        if all(u + door_w * 0.5 + 0.10 <= w0 or u - door_w * 0.5 - 0.10 >= w1 for (w0, w1) in win_spans):
            return u
    return c


def floor_rooms_along(cfg: dict, fl: int, axis: str, exclude_faces: Optional[set] = None) -> List[Dict[str, Any]]:
    """取出指定樓層（0-based fl）沿 X 或 Y 軸排列之 115 學年度空間列表。"""
    out = []
    ax_i = 0 if axis == "X" else 1
    for idx, rm in enumerate(cfg.get("rooms_115_detailed", [])):
        if exclude_faces and rm.get("face") in exclude_faces:
            continue
        try:
            f = int(str(rm.get("floor", "")).rstrip("Ff"))
        except ValueError:
            continue
        if f != fl + 1:
            continue
        pu = rm["pos"][ax_i]
        sz = rm.get("size") or [5.2, 4.6, 3.1]
        w = sz[ax_i]
        out.append({"idx": idx, "u0": pu - w * 0.5, "u1": pu + w * 0.5, "cu": pu, "name": rm.get("name", "")})
    return sorted(out, key=lambda r: r["cu"])


def plan_interval_rooms(ua: float, ub: float, cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """將連續可進入區間 [ua, ub] 依候選空間分割為無縫房間段。"""
    items = []
    for r in cands:
        a, b = max(r["u0"], ua), min(r["u1"], ub)
        if b - a >= 1.6:
            items.append({"idx": r["idx"], "a": a, "b": b, "name": r.get("name", "")})
    if not items:
        return [{"idx": None, "a": ua, "b": ub, "name": ""}]
    segs = []
    first = items[0]
    if first["a"] - ua > 1.5:
        segs.append({"idx": None, "a": ua, "b": first["a"], "name": ""})
    else:
        first["a"] = ua
    for i, it in enumerate(items):
        if i > 0:
            prev = items[i - 1]
            gap = it["a"] - prev["b"]
            if gap <= 1.5:
                mid = 0.5 * (it["a"] + prev["b"])
                prev["b"] = mid
                it["a"] = mid
            else:
                segs.append({"idx": None, "a": prev["b"], "b": it["a"], "name": ""})
        segs.append(it)
    last = items[-1]
    if ub - last["b"] > 1.5:
        segs.append({"idx": None, "a": last["b"], "b": ub, "name": ""})
    else:
        last["b"] = ub
    return segs


def _door_slide_sign(door_u: float, seg_a: float, seg_b: float) -> int:
    """門板往房間較寬側滑動，避免滑穿隔間牆。"""
    return 1 if (seg_b - door_u) >= (door_u - seg_a) else -1


def _add_wall_segment_x(
    bm_out: bmesh.types.BMesh,
    bm_in: bmesh.types.BMesh,
    a: float,
    b: float,
    za: float,
    zb: float,
    y_face: float,
    inward_y: float,
    t_o: float,
    t_i: float,
    colliders: list,
) -> None:
    """建立平行 X 軸之雙層外牆（y_face 為外表面，inward_y = +1 表示往 +Y 進入室內，-1 表示往 -Y 進入室內）。"""
    yc_o = y_face + inward_y * (t_o * 0.5)
    yc_i = y_face + inward_y * (t_o + t_i * 0.5)
    gp.bm_box(bm_out, (0.5 * (a + b), yc_o, 0.5 * (za + zb)), (b - a, t_o, zb - za))
    gp.bm_box(bm_in, (0.5 * (a + b), yc_i, 0.5 * (za + zb)), (b - a, t_i, zb - za))
    y_a = y_face
    y_b = y_face + inward_y * (t_o + t_i)
    colliders.append((a, b, min(y_a, y_b), max(y_a, y_b), za, zb))


def _add_wall_segment_y(
    bm_out: bmesh.types.BMesh,
    bm_in: bmesh.types.BMesh,
    a: float,
    b: float,
    za: float,
    zb: float,
    x_face: float,
    inward_x: float,
    t_o: float,
    t_i: float,
    colliders: list,
) -> None:
    """建立平行 Y 軸之雙層外牆（x_face 為外表面，inward_x = +1 表示往 +X 進入室內，-1 表示往 -X 進入室內）。"""
    xc_o = x_face + inward_x * (t_o * 0.5)
    xc_i = x_face + inward_x * (t_o + t_i * 0.5)
    gp.bm_box(bm_out, (xc_o, 0.5 * (a + b), 0.5 * (za + zb)), (t_o, b - a, zb - za))
    gp.bm_box(bm_in, (xc_i, 0.5 * (a + b), 0.5 * (za + zb)), (t_i, b - a, zb - za))
    x_a = x_face
    x_b = x_face + inward_x * (t_o + t_i)
    colliders.append((min(x_a, x_b), max(x_a, x_b), a, b, za, zb))


# =============================================================================
# 1. 走廊棟（along_x = True：重慶樓、和平樓；along_x = False：五權樓）
# =============================================================================
def build_corridor_floor_interior_x(ctx: dict, fl: int, zf: float, fh: float) -> None:
    """沿 X 軸走廊校舍（重慶樓、和平樓）單層中空教室、門洞、門框、隔間牆與欄杆碰撞。"""
    cfg = ctx["cfg"]
    prefix = cfg["id"]
    bays, bay_len, x0 = ctx["bays"], ctx["bay_len"], ctx["x0"]
    y0, y1 = ctx["y0"], ctx["y1"]
    core_y0, core_y1 = ctx["core_y0"], ctx["core_y1"]
    corridor_sides = ctx["corridor_sides"]
    cols = ctx["colliders"]
    t_o, t_i = 0.14, 0.16
    z_lo, z_hi = zf + 0.15, zf + fh + 0.04
    z_floor = zf + (0.36 if fl == 0 else 0.27)
    z_corr = zf + (0.385 if fl == 0 else 0.315)
    ctx["floors"].append({"floor": fl + 1, "zf": round(zf, 3), "z_floor": round(z_floor, 3), "z_top": round(z_corr, 3), "fh": round(fh, 3)})

    # 走廊外緣結構柱與女兒牆碰撞
    for b in range(bays):
        bx0 = x0 + b * bay_len
        bcx = bx0 + 0.5 * bay_len
        for side in ("south", "north"):
            if side not in corridor_sides:
                continue
            edge_y = (y0 + 0.16) if side == "south" else (y1 - 0.16)
            cols.append((bx0 + 0.25 - 0.26, bx0 + 0.25 + 0.26, edge_y - 0.26, edge_y + 0.26, zf, zf + fh))
            if b == bays - 1:
                cols.append((bx0 + bay_len - 0.25 - 0.26, bx0 + bay_len - 0.25 + 0.26, edge_y - 0.26, edge_y + 0.26, zf, zf + fh))
            if fl >= 1:
                is_solid = b in ctx["solid_bays"]
                has_parapet = (side == "north") or (not is_solid)
                if has_parapet:
                    cols.append((bcx - (bay_len - 0.48) * 0.5, bcx + (bay_len - 0.48) * 0.5, edge_y - 0.12, edge_y + 0.12, zf + 0.08, zf + 1.04))

    hollow_bays = [b for b in range(bays) if b not in ctx["solid_bays"] and not (fl == 0 and b in ctx["breezeways"])]
    if not hollow_bays:
        return

    intervals = []
    for b in hollow_bays:
        if intervals and intervals[-1][1] == b - 1:
            intervals[-1][1] = b
        else:
            intervals.append([b, b])

    win_w = bay_len * 0.76 * 0.78
    win_h = 1.48
    win_z = zf + fh * 0.58
    open_w, open_h = win_w - 0.12, win_h - 0.08
    win_spans = [(x0 + (b + 0.5) * bay_len - win_w * 0.5, x0 + (b + 0.5) * bay_len + win_w * 0.5) for b in hollow_bays]

    ya, yb = core_y0 + t_o + t_i, core_y1 - t_o - t_i
    bm_outer = ctx["bm_cream"] if prefix == "Bldg_Heping" else ctx["bm_salmon"]
    bm_cream, bm_dado, bm_door, bm_light = ctx["bm_cream"], ctx["bm_dado"], ctx["bm_door"], ctx["bm_light"]
    cand_rooms = floor_rooms_along(cfg, fl, "X", exclude_faces={"N"})

    for ba, bb in intervals:
        xa = x0 + ba * bay_len
        xb = x0 + (bb + 1) * bay_len
        segs = plan_interval_rooms(xa, xb, cand_rooms)
        window_open = []
        for b in range(ba, bb + 1):
            bcx = x0 + (b + 0.5) * bay_len
            window_open.append((bcx - open_w * 0.5, bcx + open_w * 0.5, win_z - open_h * 0.5, win_z + open_h * 0.5))

        door_open = []
        for s in segs:
            s["door_x"] = pick_door_u(s["a"], s["b"], win_spans)
            door_open.append((s["door_x"] - 0.55, s["door_x"] + 0.55, z_lo - 0.2, zf + 2.25))

        for a, b, za, zb in wall_rects(xa, xb, window_open + door_open, z_lo, z_hi):
            _add_wall_segment_x(bm_outer, bm_cream, a, b, za, zb, core_y0, +1.0, t_o, t_i, cols)
        for a, b, za, zb in wall_rects(xa, xb, window_open, z_lo, z_hi):
            _add_wall_segment_x(bm_outer, bm_cream, a, b, za, zb, core_y1, -1.0, t_o, t_i, cols)

        # 走廊側磁磚腰帶（門洞處斷開）與木門框
        if "south" in corridor_sides:
            for a, b, za, zb in wall_rects(xa, xb, door_open, zf + 0.03, zf + 1.21):
                gp.bm_box(bm_dado, (0.5 * (a + b), core_y0 - 0.03, 0.5 * (za + zb)), (b - a, 0.06, zb - za))
        if "north" in corridor_sides:
            for a, b, za, zb in wall_rects(xa, xb, [], zf + 0.03, zf + 1.21):
                gp.bm_box(bm_dado, (0.5 * (a + b), core_y1 + 0.03, 0.5 * (za + zb)), (b - a, 0.06, zb - za))

        wall_c = core_y0 + 0.5 * (t_o + t_i)
        for s in segs:
            dx = s["door_x"]
            for jx in (dx - 0.58, dx + 0.58):
                gp.bm_box(bm_door, (jx, wall_c, zf + 1.28), (0.06, t_o + t_i + 0.04, 2.16))
            gp.bm_box(bm_door, (dx, wall_c, zf + 2.28), (1.18, t_o + t_i + 0.04, 0.06))

        # 教室隔間牆與端牆
        boundaries = [s["b"] for s in segs[:-1]]
        if ba - 1 >= 0 and ba - 1 not in ctx["solid_bays"]:
            boundaries.append(xa)
        if bb + 1 < bays and bb + 1 not in ctx["solid_bays"]:
            boundaries.append(xb)
        if bb == bays - 1:
            boundaries.append(xb - 0.1)
        for px in boundaries:
            gp.bm_box(bm_cream, (px, 0.5 * (ya + yb), 0.5 * (z_lo + z_hi)), (0.2, yb - ya, z_hi - z_lo))
            cols.append((px - 0.1, px + 0.1, ya, yb, z_lo, z_hi))

        for s in segs:
            width = s["b"] - s["a"]
            if s["idx"] is not None:
                kind = "room"
            elif ctx.get("stair_mid_x") is not None and s["a"] - 0.2 <= ctx["stair_mid_x"] <= s["b"] + 0.2:
                kind = "stair"
            else:
                kind = "void"
            ctx["rooms"].append(
                {
                    "bldg": prefix,
                    "key": f"{prefix}:{s['idx']}" if s["idx"] is not None else None,
                    "kind": kind,
                    "floor": fl + 1,
                    "x0": round(s["a"], 3),
                    "x1": round(s["b"], 3),
                    "y0": round(ya, 3),
                    "y1": round(yb, 3),
                    "z_floor": round(z_floor, 3),
                    "z_ceil": round(zf + fh + 0.01, 3),
                    "door_x": round(s["door_x"], 3),
                    "door": {
                        "x": round(s["door_x"], 3),
                        "y": round(wall_c, 3),
                        "z": round(z_floor, 3),
                        "axis": "X",
                        "normal": [0, -1],
                        "width": 1.1,
                        "height": 2.12,
                        "slide": _door_slide_sign(s["door_x"], s["a"], s["b"]),
                    },
                }
            )
            if width >= 2.5:
                nx = 2 if width > 4.2 else 1
                for i in range(nx):
                    lx = s["a"] + width * (i + 1) / (nx + 1)
                    for ly in (ya + (yb - ya) * 0.3, ya + (yb - ya) * 0.7):
                        gp.bm_box(bm_light, (lx, ly, zf + fh - 0.035), (1.3, 0.28, 0.05))


def build_wuquan_floor_interior(ctx: dict, fl: int, zf: float, fh: float) -> None:
    """五權樓（沿 Y 軸）單層中空教室、門洞、隔間牆與雙側走廊欄杆碰撞。
    - 南翼 b=0..4（1F–5F）：門開西側走廊 (x=-4.6)，東側保持平齊雙格窗牆與 1F-5F 直立彩繪布條。
    - 中北翼 b=5..10：2F–5F 門開東側操場走廊 (x=4.1)；1F 門開西側中庭走廊 (x=-4.6) 避開東側實景鐵捲門與大階梯。
    """
    cfg = ctx["cfg"]
    prefix = cfg["id"]
    bays, bay_len, y0 = ctx["bays"], ctx["bay_len"], ctx["y0"]
    x0, x1 = ctx["x0"], ctx["x1"]
    core_x0, core_x1 = ctx["core_x0"], ctx["core_x1"]
    cols = ctx["colliders"]
    t_o, t_i = 0.14, 0.16
    z_lo, z_hi = zf + 0.15, zf + fh + 0.04
    z_floor = zf + (0.36 if fl == 0 else 0.27)
    z_corr = zf + (0.385 if fl == 0 else 0.315)
    ctx["floors"].append({"floor": fl + 1, "zf": round(zf, 3), "z_floor": round(z_floor, 3), "z_top": round(z_corr, 3), "fh": round(fh, 3)})

    # 雙側走廊柱與女兒牆碰撞（西走廊 b=3 重慶轉角口與東走廊 2F b=6 司令台露台保持暢通）
    for b in range(bays):
        by0 = y0 + b * bay_len
        bcy = by0 + 0.5 * bay_len
        is_south_solid = b <= 4
        for side in ("west", "east"):
            if side == "east" and is_south_solid:
                continue
            edge_x = (x0 + 0.16) if side == "west" else (x1 - 0.16)
            cols.append((edge_x - 0.26, edge_x + 0.26, by0 + 0.25 - 0.26, by0 + 0.25 + 0.26, zf, zf + fh))
            if b == bays - 1:
                cols.append((edge_x - 0.26, edge_x + 0.26, by0 + bay_len - 0.25 - 0.26, by0 + bay_len - 0.25 + 0.26, zf, zf + fh))
            if fl >= 1:
                is_stage_open = side == "east" and fl == 1 and b == 6
                is_cq_open = side == "west" and b == 3
                if not is_stage_open and not is_cq_open:
                    cols.append((edge_x - 0.12, edge_x + 0.12, bcy - (bay_len - 0.48) * 0.5, bcy + (bay_len - 0.48) * 0.5, zf + 0.08, zf + 1.04))

    bm_salmon, bm_cream, bm_dado, bm_door, bm_light = ctx["bm_salmon"], ctx["bm_cream"], ctx["bm_dado"], ctx["bm_door"], ctx["bm_light"]
    cand_rooms = floor_rooms_along(cfg, fl, "Y")

    # 區段分組：南翼 b=0..4 一段，中北翼 b=5..10（1F 扣掉穿堂 b=6, 8）分段
    south_bays = [b for b in range(0, 5) if not (fl == 0 and b in ctx["breezeways"])]
    north_bays = [b for b in range(5, 11) if not (fl == 0 and b in ctx["breezeways"])]

    def _build_wing_intervals(wing_bays: List[int], is_south: bool) -> None:
        if not wing_bays:
            return
        intervals = []
        for b in wing_bays:
            if intervals and intervals[-1][1] == b - 1:
                intervals[-1][1] = b
            else:
                intervals.append([b, b])

        cx0 = core_x0
        cx1 = (x1 - 0.14) if is_south else core_x1
        xa, xb = cx0 + t_o + t_i, cx1 - t_o - t_i
        door_side = "W" if (is_south or fl == 0) else "E"
        outer_bm = bm_cream if is_south else bm_salmon

        win_w = bay_len * 0.76 * 0.78
        win_h = 1.48
        win_z = zf + fh * 0.58
        open_w, open_h = win_w - 0.12, win_h - 0.08

        for ba, bb in intervals:
            ya = y0 + ba * bay_len
            yb = y0 + (bb + 1) * bay_len
            segs = plan_interval_rooms(ya, yb, cand_rooms)

            west_wins = []
            east_wins = []
            for b in range(ba, bb + 1):
                by0_b = y0 + b * bay_len
                bcy_b = by0_b + 0.5 * bay_len
                west_wins.append((bcy_b - open_w * 0.5, bcy_b + open_w * 0.5, win_z - open_h * 0.5, win_z + open_h * 0.5))
                if is_south:
                    sub_cs = [by0_b + bay_len * 0.25] if b == 4 else [by0_b + bay_len * 0.25, by0_b + bay_len * 0.75]
                    sw = bay_len * 0.39 - 0.10
                    sz_c = zf + fh * 0.48
                    for sy_w in sub_cs:
                        east_wins.append((sy_w - sw * 0.5, sy_w + sw * 0.5, sz_c - 0.67, sz_c + 0.67))
                elif fl >= 1:
                    east_wins.append((bcy_b - open_w * 0.5, bcy_b + open_w * 0.5, win_z - open_h * 0.5, win_z + open_h * 0.5))

            door_win_spans = [(w[0] - 0.06, w[1] + 0.06) for w in (west_wins if door_side == "W" else east_wins)]
            door_open = []
            for s in segs:
                s["door_y"] = pick_door_u(s["a"], s["b"], door_win_spans)
                door_open.append((s["door_y"] - 0.55, s["door_y"] + 0.55, z_lo - 0.2, zf + 2.25))

            # 西牆與東牆
            w_opens = west_wins + (door_open if door_side == "W" else [])
            e_opens = east_wins + (door_open if door_side == "E" else [])
            for a, b, za, zb in wall_rects(ya, yb, w_opens, z_lo, z_hi):
                _add_wall_segment_y(outer_bm, bm_cream, a, b, za, zb, cx0, +1.0, t_o, t_i, cols)
            for a, b, za, zb in wall_rects(ya, yb, e_opens, z_lo, z_hi):
                _add_wall_segment_y(outer_bm, bm_cream, a, b, za, zb, cx1, -1.0, t_o, t_i, cols)

            # 走廊側磁磚腰帶（門洞處斷開）
            for a, b, za, zb in wall_rects(ya, yb, door_open if door_side == "W" else [], zf + 0.03, zf + 1.21):
                gp.bm_box(bm_dado, (cx0 - 0.03, 0.5 * (a + b), 0.5 * (za + zb)), (0.06, b - a, zb - za))
            if not is_south and fl >= 1:
                for a, b, za, zb in wall_rects(ya, yb, door_open if door_side == "E" else [], zf + 0.03, zf + 1.21):
                    gp.bm_box(bm_dado, (cx1 + 0.03, 0.5 * (a + b), 0.5 * (za + zb)), (0.06, b - a, zb - za))

            # 木門框
            wall_x = (cx0 + 0.5 * (t_o + t_i)) if door_side == "W" else (cx1 - 0.5 * (t_o + t_i))
            normal_x = -1 if door_side == "W" else 1
            for s in segs:
                dy = s["door_y"]
                for jy in (dy - 0.58, dy + 0.58):
                    gp.bm_box(bm_door, (wall_x, jy, zf + 1.28), (t_o + t_i + 0.04, 0.06, 2.16))
                gp.bm_box(bm_door, (wall_x, dy, zf + 2.28), (t_o + t_i + 0.04, 1.18, 0.06))

            # 隔間牆與端牆
            boundaries = [s["b"] for s in segs[:-1]]
            if ba == 0 or (ba - 1 in ctx["breezeways"] and fl == 0) or ba == 5:
                boundaries.append(ya + 0.1)
            if bb == 4 or bb == 10 or (bb + 1 in ctx["breezeways"] and fl == 0):
                boundaries.append(yb - 0.1)
            for py in boundaries:
                gp.bm_box(bm_cream, (0.5 * (xa + xb), py, 0.5 * (z_lo + z_hi)), (xb - xa, 0.2, z_hi - z_lo))
                cols.append((xa, xb, py - 0.1, py + 0.1, z_lo, z_hi))

            for s in segs:
                length_y = s["b"] - s["a"]
                kind = "room" if s["idx"] is not None else "void"
                ctx["rooms"].append(
                    {
                        "bldg": prefix,
                        "key": f"{prefix}:{s['idx']}" if s["idx"] is not None else None,
                        "kind": kind,
                        "floor": fl + 1,
                        "x0": round(xa, 3),
                        "x1": round(xb, 3),
                        "y0": round(s["a"], 3),
                        "y1": round(s["b"], 3),
                        "z_floor": round(z_floor, 3),
                        "z_ceil": round(zf + fh + 0.01, 3),
                        "door": {
                            "x": round(wall_x, 3),
                            "y": round(s["door_y"], 3),
                            "z": round(z_floor, 3),
                            "axis": "Y",
                            "normal": [normal_x, 0],
                            "width": 1.1,
                            "height": 2.12,
                            "slide": _door_slide_sign(s["door_y"], s["a"], s["b"]),
                        },
                    }
                )
                if length_y >= 2.5:
                    ny = 2 if length_y > 4.2 else 1
                    for i in range(ny):
                        ly = s["a"] + length_y * (i + 1) / (ny + 1)
                        for lx in (xa + (xb - xa) * 0.3, xa + (xb - xa) * 0.7):
                            gp.bm_box(bm_light, (lx, ly, zf + fh - 0.035), (0.28, 1.3, 0.05))

    _build_wing_intervals(south_bays, True)
    _build_wing_intervals(north_bays, False)


# =============================================================================
# 2. 廣和樓（行政主棟：1F 穿堂兩翼 + 2F 退縮層 + 3F–5F 全開間）
# =============================================================================
def build_guanghe_interiors(
    cfg: dict,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    h1: float,
    hu: float,
    plinth_h: float,
    breezeway_half: float,
    corridor_w: float,
    bm_wall: bmesh.types.BMesh,
    bm_door: bmesh.types.BMesh,
    bm_light: bmesh.types.BMesh,
    bm_terrazzo: bmesh.types.BMesh,
    bm_brick: bmesh.types.BMesh,
    bm_rail: bmesh.types.BMesh,
    bm_glass: bmesh.types.BMesh,
    bm_frame: bmesh.types.BMesh,
    add_window_fn: Any,
) -> None:
    """建置廣和樓 1F–5F 中空處室／辦公室牆體、門洞、隔間牆、東側走廊地坪與碰撞資料。"""
    prefix = cfg["id"]
    cy = 0.5 * (y0 + y1)
    core_x1 = x1 - corridor_w  # -34.0
    corr_cx = x1 - corridor_w * 0.5  # -32.75
    t_o, t_i = 0.14, 0.16
    t_tot = t_o + t_i
    floors_meta: List[Dict[str, Any]] = []
    rooms_out: List[Dict[str, Any]] = []
    cols: List[Tuple[float, float, float, float, float, float]] = []

    def _add_gh_room_shell(
        fl_idx: int,
        zf: float,
        fh: float,
        z_floor: float,
        rx0: float,
        rx1: float,
        ry0: float,
        ry1: float,
        door_side: str,  # "E" | "S" | "N"
        door_pos: float,
        west_wins: Sequence[Tuple[float, float, float, float]],
        north_wins: Sequence[Tuple[float, float, float, float]],
        south_wins: Sequence[Tuple[float, float, float, float]],
        east_wins: Sequence[Tuple[float, float, float, float]],
        segs: List[Dict[str, Any]],
        add_south_wall: bool = True,
        add_north_wall: bool = True,
    ) -> None:
        z_lo, z_hi = zf + 0.12, zf + fh + 0.04
        # 門洞清單
        if door_side == "E":
            east_doors = [(s["door_u"] - 0.55, s["door_u"] + 0.55, z_lo - 0.2, zf + 2.25) for s in segs]
            south_doors = []
            north_doors = []
        elif door_side == "S":
            east_doors = []
            south_doors = [(door_pos - 0.55, door_pos + 0.55, z_lo - 0.2, zf + 2.25)]
            north_doors = []
        else:
            east_doors = []
            south_doors = []
            north_doors = [(door_pos - 0.55, door_pos + 0.55, z_lo - 0.2, zf + 2.25)]

        # 西牆（x = rx0）
        for a, b, za, zb in wall_rects(ry0, ry1, west_wins, z_lo, z_hi):
            _add_wall_segment_y(bm_wall, bm_wall, a, b, za, zb, rx0, +1.0, t_o, t_i, cols)
        # 東牆（x = rx1）
        for a, b, za, zb in wall_rects(ry0, ry1, list(east_wins) + east_doors, z_lo, z_hi):
            _add_wall_segment_y(bm_wall, bm_wall, a, b, za, zb, rx1, -1.0, t_o, t_i, cols)
        # 南牆（y = ry0）
        if add_south_wall:
            for a, b, za, zb in wall_rects(rx0 + t_tot, rx1 - t_tot, list(south_wins) + south_doors, z_lo, z_hi):
                _add_wall_segment_x(bm_wall, bm_wall, a, b, za, zb, ry0, +1.0, t_o, t_i, cols)
        # 北牆（y = ry1）
        if add_north_wall:
            for a, b, za, zb in wall_rects(rx0 + t_tot, rx1 - t_tot, list(north_wins) + north_doors, z_lo, z_hi):
                _add_wall_segment_x(bm_wall, bm_wall, a, b, za, zb, ry1, -1.0, t_o, t_i, cols)

        # 隔間牆（沿 Y 分隔 segs）
        in_x0, in_x1 = rx0 + t_tot, rx1 - t_tot
        for s in segs[:-1]:
            py = s["b"]
            gp.bm_box(bm_wall, (0.5 * (in_x0 + in_x1), py, 0.5 * (z_lo + z_hi)), (in_x1 - in_x0, 0.2, z_hi - z_lo))
            cols.append((in_x0, in_x1, py - 0.1, py + 0.1, z_lo, z_hi))

        # 木門框、天花燈與房間資料
        for s in segs:
            if door_side == "E":
                dx, dy = rx1 - t_tot * 0.5, s["door_u"]
                for jy in (dy - 0.58, dy + 0.58):
                    gp.bm_box(bm_door, (dx, jy, zf + 1.28), (t_tot + 0.04, 0.06, 2.16))
                gp.bm_box(bm_door, (dx, dy, zf + 2.28), (t_tot + 0.04, 1.18, 0.06))
                door_obj = {
                    "x": round(dx, 3),
                    "y": round(dy, 3),
                    "z": round(z_floor, 3),
                    "axis": "Y",
                    "normal": [1, 0],
                    "width": 1.1,
                    "height": 2.12,
                    "slide": _door_slide_sign(dy, s["a"], s["b"]),
                }
            else:
                dy = (ry0 + t_tot * 0.5) if door_side == "S" else (ry1 - t_tot * 0.5)
                dx = door_pos
                for jx in (dx - 0.58, dx + 0.58):
                    gp.bm_box(bm_door, (jx, dy, zf + 1.28), (0.06, t_tot + 0.04, 2.16))
                gp.bm_box(bm_door, (dx, dy, zf + 2.28), (1.18, t_tot + 0.04, 0.06))
                door_obj = {
                    "x": round(dx, 3),
                    "y": round(dy, 3),
                    "z": round(z_floor, 3),
                    "axis": "X",
                    "normal": [0, -1 if door_side == "S" else 1],
                    "width": 1.1,
                    "height": 2.12,
                    "slide": 1,
                }

            in_y0 = s["a"] + (t_tot if s["a"] <= ry0 + 0.05 else 0.1)
            in_y1 = s["b"] - (t_tot if s["b"] >= ry1 - 0.05 else 0.1)
            rooms_out.append(
                {
                    "bldg": prefix,
                    "key": f"{prefix}:{s['idx']}" if s["idx"] is not None else None,
                    "kind": "room" if s["idx"] is not None else "void",
                    "floor": fl_idx + 1,
                    "x0": round(in_x0, 3),
                    "x1": round(in_x1, 3),
                    "y0": round(in_y0, 3),
                    "y1": round(in_y1, 3),
                    "z_floor": round(z_floor, 3),
                    "z_ceil": round(zf + fh + 0.01, 3),
                    "door": door_obj,
                }
            )
            # 天花燈
            for lx in (in_x0 + (in_x1 - in_x0) * 0.3, in_x0 + (in_x1 - in_x0) * 0.7):
                gp.bm_box(bm_light, (lx, 0.5 * (in_y0 + in_y1), zf + fh - 0.04), (1.4, 0.28, 0.05))

    # --- 1F (fl=0): 中央穿堂開放，南北兩翼中空並開門面向中央穿堂 ---
    floors_meta.append({"floor": 1, "zf": round(plinth_h, 3), "z_floor": round(plinth_h + 0.03, 3), "z_top": round(plinth_h + 0.045, 3), "fh": round(h1 - plinth_h, 3)})
    cands_1f = floor_rooms_along(cfg, 0, "Y")
    # 穿堂內移動電視架碰撞
    cols.append((x0 + 10.8, x0 + 11.6, cy - 1.25, cy + 1.25, plinth_h, plinth_h + 2.2))
    # 北翼（學務處 y=5.8..11.5）與南翼（健康中心 y=-10.5..-4.8）
    wing_n_y0, wing_n_y1 = cy + breezeway_half, y1
    wing_s_y0, wing_s_y1 = y0, cy - breezeway_half
    n_cands = [r for r in cands_1f if r["cu"] > cy + 2.0]
    s_cands = [r for r in cands_1f if r["cu"] < cy - 2.0]
    n_segs = plan_interval_rooms(wing_n_y0, wing_n_y1, n_cands)
    s_segs = plan_interval_rooms(wing_s_y0, wing_s_y1, s_cands)
    w_n_win = [(0.5 * (wing_n_y0 + wing_n_y1) - (wing_n_y1 - wing_n_y0) * 0.33, 0.5 * (wing_n_y0 + wing_n_y1) + (wing_n_y1 - wing_n_y0) * 0.33, plinth_h + 0.92, plinth_h + 2.38)]
    w_s_win = [(0.5 * (wing_s_y0 + wing_s_y1) - (wing_s_y1 - wing_s_y0) * 0.33, 0.5 * (wing_s_y0 + wing_s_y1) + (wing_s_y1 - wing_s_y0) * 0.33, plinth_h + 0.92, plinth_h + 2.38)]
    # 1F 兩翼門開在 x = -36.8（避開穿堂榮譽牆 x=-49.0..-39.0 與東側列柱 x=-33.7）
    _add_gh_room_shell(0, plinth_h, h1 - plinth_h, plinth_h + 0.03, x0 + 0.2, core_x1, wing_n_y0, wing_n_y1, "S", -36.8, w_n_win, [], [], [], n_segs)
    _add_gh_room_shell(0, plinth_h, h1 - plinth_h, plinth_h + 0.03, x0 + 0.2, core_x1, wing_s_y0, wing_s_y1, "N", -36.8, w_s_win, [], [], [], s_segs)

    # --- 2F (fl=1): 退縮挑空門廳 + 兩翼 + 東側開放走廊 ---
    z2 = h1
    floors_meta.append({"floor": 2, "zf": round(z2, 3), "z_floor": round(z2 + 0.30, 3), "z_top": round(z2 + 0.33, 3), "fh": round(hu, 3)})
    gp.bm_box(bm_terrazzo, (corr_cx, cy, z2 + 0.31), (corridor_w - 0.3, y1 - y0 - 0.2, 0.03))
    gp.bm_box(bm_brick, (x1 - 0.14, cy, z2 + 0.58), (0.24, y1 - y0, 1.02))
    gp.bm_box(bm_rail, (x1 - 0.14, cy, z2 + 1.22), (0.07, y1 - y0, 0.07))
    cols.append((x1 - 0.28, x1, y0, y1, z2, z2 + 1.3))
    cols.append((core_x1, x1, y0 - 0.1, y0 + 0.25, z2, z2 + 1.3))
    cols.append((core_x1, x1, y1 - 0.25, y1 + 0.1, z2, z2 + 1.3))
    cands_2f = floor_rooms_along(cfg, 1, "Y")
    # 2F 分成北翼（人事/主計）、中段退縮（輔導室）、南翼（廁所）
    for (wy0, wy1, rx0_w, w_wins) in [
        (wing_n_y0, wing_n_y1, x0, [(y1 - 2.8 - 1.65, y1 - 2.8 + 1.65, z2 + 1.18, z2 + 2.62)]),
        (wing_s_y1, wing_n_y0, x0 + 5.2, []),
        (wing_s_y0, wing_s_y1, x0, []),
    ]:
        sub_cands = [r for r in cands_2f if wy0 - 0.8 <= r["cu"] <= wy1 + 0.8]
        segs = plan_interval_rooms(wy0, wy1, sub_cands)
        e_wins_2f = []
        for s in segs:
            s["door_u"] = pick_door_u(s["a"], s["b"], [])
            if s["b"] - s["a"] > 3.4:
                wa, wb = (s["door_u"] + 0.72, s["b"] - 0.35) if (s["b"] - s["door_u"]) >= (s["door_u"] - s["a"]) else (s["a"] + 0.35, s["door_u"] - 0.72)
                if wb - wa > 1.0:
                    e_wins_2f.append((wa, wb, z2 + 1.32, z2 + 2.68))
                    add_window_fn(bm_glass, bm_frame, (core_x1 + 0.04, 0.5 * (wa + wb), z2 + 2.0), wb - wa, 1.38, axis="Y", cols=max(2, int((wb - wa) // 1.1)))
        _add_gh_room_shell(1, z2, hu, z2 + 0.30, rx0_w, core_x1, wy0, wy1, "E", 0.0, w_wins, [], [], e_wins_2f, segs)

    # --- 3F ~ 5F (fl=2, 3, 4): 全寬中空處室與教室 + 東走廊 ---
    for fl in range(2, 5):
        zf = h1 + (fl - 1) * hu
        floors_meta.append({"floor": fl + 1, "zf": round(zf, 3), "z_floor": round(zf + 0.27, 3), "z_top": round(zf + 0.315, 3), "fh": round(hu, 3)})
        gp.bm_box(bm_terrazzo, (corr_cx, cy, zf + 0.295), (corridor_w - 0.3, y1 - y0 - 0.2, 0.03))
        cols.append((x1 - 0.28, x1, y0, y1, zf, zf + 1.3))
        cols.append((core_x1, x1, y0 - 0.1, y0 + 0.25, zf, zf + 1.3))
        cols.append((core_x1, x1, y1 - 0.25, y1 + 0.1, zf, zf + 1.3))

        win_z = zf + 2.02
        win_h = 1.48
        w_wins = [
            (y0 + 2.65 - 1.60, y0 + 2.65 + 1.60, win_z - win_h * 0.46, win_z + win_h * 0.46),
            (y1 - 2.65 - 1.60, y1 - 2.65 + 1.60, win_z - win_h * 0.46, win_z + win_h * 0.46),
        ]
        if fl < 4:
            w_wins.append((cy - 5.65, cy + 5.65, win_z - win_h * 0.46, win_z + win_h * 0.46))
        flank_wins = [(x0 + 14.2 - 2.75, x0 + 14.2 + 2.75, win_z - win_h * 0.46, win_z + win_h * 0.46)]

        cands_f = floor_rooms_along(cfg, fl, "Y")
        segs = plan_interval_rooms(y0, y1, cands_f)
        east_wins = []
        for s in segs:
            s["door_u"] = pick_door_u(s["a"], s["b"], [])
            # 在每間處室東側留一段與門錯開的走廊窗洞＋實際鋁窗
            room_len = s["b"] - s["a"]
            if room_len > 3.2:
                if (s["b"] - s["door_u"]) >= (s["door_u"] - s["a"]):
                    wa, wb = s["door_u"] + 0.72, s["b"] - 0.35
                else:
                    wa, wb = s["a"] + 0.35, s["door_u"] - 0.72
                if wb - wa > 0.9:
                    east_wins.append((wa, wb, zf + 1.32, zf + 2.68))
                    add_window_fn(bm_glass, bm_frame, (core_x1 + 0.04, 0.5 * (wa + wb), zf + 2.0), wb - wa, 1.38, axis="Y", cols=max(2, int((wb - wa) // 1.1)))

        _add_gh_room_shell(fl, zf, hu, zf + 0.27, x0, core_x1, y0, y1, "E", 0.0, w_wins, flank_wins, flank_wins, east_wins, segs)

    register_building_walk_data(
        prefix,
        {
            "name": "廣和樓",
            "bounds": [x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5],
            "corridor_axis": "Y",
            "corridor_val": round(corr_cx, 3),
            "floors": floors_meta,
            "stairs": [
                {"name": "3梯", "x": round(corr_cx, 3), "y": 9.2, "r": 3.4},
                {"name": "4梯・電梯", "x": round(corr_cx, 3), "y": -8.5, "r": 3.6},
            ],
        },
        rooms_out,
        cols,
    )


def register_building_walk_data(bldg_id: str, meta: dict, rooms: List[dict], colliders: List[tuple]) -> None:
    WALK_REGISTRY["buildings"][bldg_id] = meta
    WALK_REGISTRY["rooms"].extend(rooms)
    WALK_REGISTRY["colliders"].extend(colliders)
