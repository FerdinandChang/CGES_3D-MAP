import math
from typing import Sequence

import bmesh
from mathutils import Matrix, Vector


def bm_box(
    bm: bmesh.types.BMesh,
    center: Sequence[float],
    size: Sequence[float],
    rot_x: float = 0.0,
    rot_y: float = 0.0,
    rot_z: float = 0.0,
) -> None:
    """於 bmesh 中建立支援三軸旋轉之長方體原語。"""
    mat = (
        Matrix.Translation(Vector(center))
        @ Matrix.Rotation(rot_z, 4, "Z")
        @ Matrix.Rotation(rot_y, 4, "Y")
        @ Matrix.Rotation(rot_x, 4, "X")
        @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    )
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def bm_cyl_p2p(
    bm: bmesh.types.BMesh,
    p0: Sequence[float],
    p1: Sequence[float],
    r1: float,
    r2: float | None = None,
    segments: int = 14,
) -> None:
    """沿端點 p0 -> p1 建立圓柱或圓錐體原語。"""
    v0, v1 = Vector(p0), Vector(p1)
    diff = v1 - v0
    length = diff.length
    if length < 1e-4:
        return
    if r2 is None:
        r2 = r1
    mid = (v0 + v1) * 0.5
    quat = diff.normalized().to_track_quat("Z", "Y")
    mat = Matrix.Translation(mid) @ quat.to_matrix().to_4x4()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=r1,
        radius2=r2,
        depth=length,
        matrix=mat,
    )


def bm_cyl_axis(
    bm: bmesh.types.BMesh,
    center: Sequence[float],
    radius: float,
    depth: float,
    axis: str = "Z",
    segments: int = 20,
) -> None:
    """依中心點與指定軸向 (X/Y/Z) 建立圓柱原語。"""
    rot = Matrix.Identity(4)
    if axis == "X":
        rot = Matrix.Rotation(math.pi * 0.5, 4, "Y")
    elif axis == "Y":
        rot = Matrix.Rotation(math.pi * 0.5, 4, "X")
    mat = Matrix.Translation(Vector(center)) @ rot
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
        matrix=mat,
    )


def bm_oriented_box(
    bm: bmesh.types.BMesh,
    p0: Sequence[float],
    p1: Sequence[float],
    w: float,
    h: float,
) -> None:
    """沿兩端點軸向建立截面為 w×h 的矩形樑柱原語。"""
    v0, v1 = Vector(p0), Vector(p1)
    diff = v1 - v0
    length = diff.length
    if length < 1e-4:
        return
    mid = (v0 + v1) * 0.5
    quat = diff.normalized().to_track_quat("X", "Z")
    mat = Matrix.Translation(mid) @ quat.to_matrix().to_4x4() @ Matrix.Diagonal((length, w, h, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def bm_red_outline(
    bm: bmesh.types.BMesh,
    cx: float,
    cy: float,
    z: float,
    w: float,
    d: float,
    thick: float = 0.08,
) -> None:
    """於水平面 (cx, cy, z) 建立矩形警示紅框原語。"""
    bm_box(bm, (cx, cy - d * 0.5, z), (w, thick, thick))
    bm_box(bm, (cx, cy + d * 0.5, z), (w, thick, thick))
    bm_box(bm, (cx - w * 0.5, cy, z), (thick, d, thick))
    bm_box(bm, (cx + w * 0.5, cy, z), (thick, d, thick))


def add_plane_uv(
    bm: bmesh.types.BMesh,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    p3: tuple[float, float, float],
) -> None:
    """建立含標準 [0,1]² UV 貼圖座標之四邊形面片（共用原語）。"""
    uv_layer = bm.loops.layers.uv.verify()
    v0 = bm.verts.new(p0)
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    v3 = bm.verts.new(p3)
    face = bm.faces.new((v0, v1, v2, v3))
    for loop, uv in zip(face.loops, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        loop[uv_layer].uv = uv


def add_plane_uv_rect(
    bm: bmesh.types.BMesh,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    p3: tuple[float, float, float],
    u0: float,
    v0: float,
    u1: float,
    v1: float,
) -> None:
    """建立含自訂子區域 UV [u0..u1, v0..v1] 之四邊形面片（供 4K 門牌 Atlas 使用）。"""
    uv_layer = bm.loops.layers.uv.verify()
    verts = [bm.verts.new(p) for p in (p0, p1, p2, p3)]
    face = bm.faces.new(verts)
    for loop, uv in zip(face.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
        loop[uv_layer].uv = uv


def quad_extrude(
    bm: bmesh.types.BMesh,
    pts_2d: Sequence[tuple[float, float]],
    z0: float,
    z1: float,
) -> None:
    """由任意 2D 多邊形（自動正規化為逆時針 CCW）擠出 3D 柱體。"""
    area2 = 0.0
    n = len(pts_2d)
    for i in range(n):
        x0, y0 = pts_2d[i]
        x1, y1 = pts_2d[(i + 1) % n]
        area2 += x0 * y1 - x1 * y0
    pts = list(pts_2d) if area2 >= 0 else list(reversed(pts_2d))
    vb = [bm.verts.new((x, y, z0)) for x, y in pts]
    vt = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
