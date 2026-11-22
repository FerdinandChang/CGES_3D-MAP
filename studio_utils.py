import math
import os
import time
from typing import Iterable, Optional, Sequence, Tuple

import bpy
import numpy as np
from mathutils import Vector


def reset_scene() -> None:
    """清空場景內所有物件與孤立資料塊，確保每次腳本執行皆為乾淨狀態。"""
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    collections = (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.images,
        bpy.data.node_groups,
        bpy.data.curves,
    )
    for data_block in collections:
        for item in list(data_block):
            if item.users == 0:
                data_block.remove(item)


def ensure_collection(name: str, parent: Optional[bpy.types.Collection] = None) -> bpy.types.Collection:
    """取得或建立指定名稱的 Collection。"""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    target_parent = parent or bpy.context.scene.collection
    target_parent.children.link(col)
    return col


def link_object(obj: bpy.types.Object, collection_name: Optional[str] = None) -> bpy.types.Object:
    """將物件連結至指定 Collection（或場景根 Collection）。"""
    col = ensure_collection(collection_name) if collection_name else bpy.context.scene.collection
    if obj.name not in col.objects:
        col.objects.link(obj)
    return obj


def detect_cycles_gpu() -> Tuple[str, list[str]]:
    """偵測可用的 Cycles GPU 後端，若無可用 GPU 則回退為 CPU。"""
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except Exception:
        return "CPU", ["CPU"]

    for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            devices = list(prefs.get_devices_for_type(backend))
            usable = [d for d in devices if d.type == backend]
            if usable:
                for d in prefs.devices:
                    d.use = d.type == backend or d.type == "CPU"
                return backend, [d.name for d in usable]
        except Exception:
            continue

    prefs.compute_device_type = "NONE"
    return "CPU", ["CPU"]


def configure_render(
    engine: str = "BLENDER_EEVEE",
    width: int = 1024,
    height: int = 1024,
    samples: int = 32,
    look: str = "AgX - Medium High Contrast",
) -> Tuple[str, list[str]]:
    """設定渲染引擎、解析度、採樣、降噪與 AgX 色彩管理。"""
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"

    backend_info: Tuple[str, list[str]] = ("GPU_RASTER", ["Viewport/EEVEE"])

    if engine == "CYCLES":
        backend, devs = detect_cycles_gpu()
        backend_info = (backend, devs)
        scene.cycles.device = "CPU" if backend == "CPU" else "GPU"
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.02
        scene.cycles.use_denoising = True
        if hasattr(scene.cycles, "denoiser"):
            scene.cycles.denoiser = "OPENIMAGEDENOISE"
    elif engine == "BLENDER_EEVEE":
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = samples
        if hasattr(scene.eevee, "use_raytracing"):
            scene.eevee.use_raytracing = True

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = look
    except Exception:
        pass
    scene.view_settings.exposure = 0.0

    return backend_info


def ensure_material_nodes(mat: bpy.types.Material) -> bpy.types.NodeTree:
    """語系無關且相容 Blender 5.3+：取得材質的 NodeTree。"""
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    return mat.node_tree


def get_principled_bsdf(mat: bpy.types.Material) -> Optional[bpy.types.Node]:
    """透過 bl_idname 尋找 Principled BSDF，避免受 Blender 語系翻譯節點名稱影響。"""
    nt = ensure_material_nodes(mat)
    for node in nt.nodes:
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            return node
    return None


def assign_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    """清除既有空材質槽（如 Boolean 後殘留的 None），將指定材質安全指派到全部面。"""
    if obj.type != "MESH" or obj.data is None:
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.material_index = 0


def apply_box_uv(bm, uv_scale: float = 1.0) -> None:
    """用三平面 Box UV 投影替 bmesh 產生比例一致的 UV，確保 glTF 貼圖正確縮放。"""
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            co = loop.vert.co
            if az >= ax and az >= ay:
                u, v = co.x, co.y
            elif ax >= ay and ax >= az:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            loop[uv_layer].uv = (u * uv_scale, v * uv_scale)


def create_mesh_object(
    name: str,
    bm,
    mat: Optional[bpy.types.Material] = None,
    collection_name: Optional[str] = None,
    location: Sequence[float] = (0.0, 0.0, 0.0),
    rotation: Sequence[float] = (0.0, 0.0, 0.0),
    smooth: bool = False,
    auto_uv: bool = True,
    uv_scale: float = 0.5,
) -> bpy.types.Object:
    """從 bmesh 建立 Mesh 物件、自動生成 UV、指派材質與 Collection 並釋放 bmesh。"""
    bm.normal_update()
    if auto_uv:
        apply_box_uv(bm, uv_scale=uv_scale)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(location)
    obj.rotation_euler = tuple(rotation)
    link_object(obj, collection_name)
    if mat is not None:
        assign_material(obj, mat)
    return obj


def create_pivot_empty(
    name: str,
    collection_name: Optional[str] = None,
    parent: Optional[bpy.types.Object] = None,
    location: Sequence[float] = (0.0, 0.0, 0.0),
    rotation: Sequence[float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    """建立動畫樞軸控制用 Empty 空物件並連結至指定 Collection 與父節點。"""
    piv = bpy.data.objects.new(name, None)
    piv.empty_display_type = "PLAIN_AXES"
    piv.empty_display_size = 0.20
    link_object(piv, collection_name)
    if parent is not None:
        piv.parent = parent
    piv.location = Vector(location)
    if any(abs(r) > 1e-6 for r in rotation):
        piv.rotation_euler = tuple(rotation)
    return piv


def create_pivoted_mesh_object(
    name: str,
    bm,
    mat: Optional[bpy.types.Material],
    collection_name: Optional[str],
    pivot_obj: bpy.types.Object,
    origin_world: Sequence[float] = (0.0, 0.0, 0.0),
    smooth: bool = False,
    auto_uv: bool = True,
    uv_scale: float = 0.5,
    recalc_normals: bool = False,
) -> bpy.types.Object:
    """將世界空間 BMesh 頂點轉換為相對樞軸原點的局部座標後掛載於樞軸物件底下。"""
    import bmesh
    from mathutils import Matrix

    if recalc_normals:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ox, oy, oz = origin_world
    if ox != 0.0 or oy != 0.0 or oz != 0.0:
        bmesh.ops.transform(bm, matrix=Matrix.Translation((-ox, -oy, -oz)), verts=bm.verts)
    obj = create_mesh_object(name, bm, mat, collection_name, smooth=smooth, auto_uv=auto_uv, uv_scale=uv_scale)
    obj.parent = pivot_obj
    return obj


def create_textured_quad(
    name: str,
    center: Sequence[float],
    width: float,
    height: float,
    facing: str = "-Y",
    mat: Optional[bpy.types.Material] = None,
    collection_name: Optional[str] = None,
    rot_z: float = 0.0,
    u_repeat: float = 1.0,
    v_repeat: float = 1.0,
) -> bpy.types.Object:
    """建立具有完整 [0, u_repeat] x [0, v_repeat] 正向 UV 的單面/看板圖元。"""
    import bmesh
    from mathutils import Matrix

    bm = bmesh.new()
    hw, hh = width * 0.5, height * 0.5
    # 預設在 XZ 平面面向 -Y
    v0 = bm.verts.new((-hw, 0.0, -hh))
    v1 = bm.verts.new((hw, 0.0, -hh))
    v2 = bm.verts.new((hw, 0.0, hh))
    v3 = bm.verts.new((-hw, 0.0, hh))
    face = bm.faces.new((v0, v1, v2, v3))
    uv_layer = bm.loops.layers.uv.verify()
    uvs = [(0.0, 0.0), (u_repeat, 0.0), (u_repeat, v_repeat), (0.0, v_repeat)]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv

    yaw = rot_z
    if facing == "+Y":
        yaw += math.pi
    elif facing == "+X":
        yaw += math.pi * 0.5
    elif facing == "-X":
        yaw -= math.pi * 0.5
    elif facing == "+Z":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi * 0.5, 3, "X"), verts=bm.verts)

    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(yaw, 3, "Z"), verts=bm.verts)
    return create_mesh_object(name, bm, mat=mat, collection_name=collection_name, location=center, auto_uv=False)


def create_contact_ao_object(
    name: str,
    footprints: Sequence[Tuple[float, float, float, float, float]],
    mat: Optional[bpy.types.Material],
    collection_name: Optional[str] = None,
) -> bpy.types.Object:
    """建立多點貼地接觸環境光遮蔽 (Contact AO Decal) 網格並自動關閉陰影投射。
    footprints: [(cx, cy, width, depth, z), ...]
    """
    import bmesh

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for cx, cy, fw, fd, fz in footprints:
        hw, hd = fw * 0.5, fd * 0.5
        v0 = bm.verts.new((cx - hw, cy - hd, fz))
        v1 = bm.verts.new((cx + hw, cy - hd, fz))
        v2 = bm.verts.new((cx + hw, cy + hd, fz))
        v3 = bm.verts.new((cx - hw, cy + hd, fz))
        face = bm.faces.new((v0, v1, v2, v3))
        for loop, uv in zip(face.loops, uvs):
            loop[uv_layer].uv = uv
    obj = create_mesh_object(name, bm, mat=mat, collection_name=collection_name, auto_uv=False)
    obj.visible_shadow = False
    return obj


def create_dust_wisp_object(
    name: str,
    puffs: Sequence[Tuple[float, float, float, float, float, float, float]],
    mat: Optional[bpy.types.Material],
    collection_name: Optional[str] = None,
    seed: int = 42,
) -> bpy.types.Object:
    """建立無硬邊氣泡感之柔和交叉霧氣貼片與微粒擴散粉塵雲（UV 對應漸層透明貼圖）。
    puffs: [(cx, cy, cz, radius, scale_x, scale_y, scale_z), ...]
    """
    import random
    import bmesh
    from mathutils import Euler, Matrix

    rng = random.Random(seed)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

    def _add_card(center: Tuple[float, float, float], w: float, h: float, rx: float, ry: float, rz: float) -> None:
        hw, hh = w * 0.5, h * 0.5
        rot = Euler((rx, ry, rz), "XYZ").to_matrix().to_4x4()
        xf = Matrix.Translation(center) @ rot
        pts = [Vector((-hw, 0.0, -hh)), Vector((hw, 0.0, -hh)), Vector((hw, 0.0, hh)), Vector((-hw, 0.0, hh))]
        verts = [bm.verts.new(xf @ p) for p in pts]
        face = bm.faces.new(verts)
        for loop, uv in zip(face.loops, uvs):
            loop[uv_layer].uv = uv

    for cx, cy, cz, rad, sx, sy, sz in puffs:
        base_size = rad * 2.55
        # 主霧氣：6 個不同空間方位角交錯的柔和羽化雲片
        for k in range(6):
            ang_z = (math.pi * k / 6.0) + rng.uniform(-0.18, 0.18)
            ang_x = rng.uniform(-0.48, 0.48) if k < 4 else (math.pi * 0.42 + rng.uniform(-0.20, 0.20))
            ang_y = rng.uniform(-0.22, 0.22)
            ox = cx + rng.uniform(-0.18, 0.18) * rad * sx
            oy = cy + rng.uniform(-0.18, 0.18) * rad * sy
            oz = cz + rng.uniform(-0.14, 0.22) * rad * sz
            cw = base_size * max(sx, sy) * rng.uniform(0.86, 1.16)
            ch = base_size * sz * rng.uniform(0.84, 1.14)
            _add_card((ox, oy, oz), cw, ch, ang_x, ang_y, ang_z)

        # 外圍飄散小粉塵絲絮（交叉雙片，形成自然向外消散）
        for _ in range(8):
            ox = cx + rng.uniform(-0.78, 0.78) * rad * sx
            oy = cy + rng.uniform(-0.78, 0.78) * rad * sy
            oz = cz + rng.uniform(-0.22, 0.95) * rad * sz
            sub_s = rad * rng.uniform(0.55, 1.05)
            rz = rng.uniform(0.0, math.pi)
            rx = rng.uniform(-0.55, 0.55)
            _add_card((ox, oy, oz), sub_s, sub_s * rng.uniform(0.85, 1.2), rx, 0.0, rz)
            _add_card((ox, oy, oz), sub_s, sub_s * rng.uniform(0.85, 1.2), rx + 0.35, 0.0, rz + math.pi * 0.5)

    obj = create_mesh_object(name, bm, mat=mat, collection_name=collection_name, auto_uv=False, smooth=False)
    obj.visible_shadow = False
    return obj


def add_spray_fan_bm(
    bm,
    origin: Sequence[float],
    target: Sequence[float],
    end_width: float = 0.52,
    start_width: float = 0.075,
    roll_rad: float = 0.0,
    cross_ratio: float = 0.48,
    arc_lift: float = 0.0,
) -> None:
    """在固定噴嘴 origin -> target 建立交叉羽化扇形水霧卡片 (UV: v=0 固定噴口 -> v=1 霧化消散)。"""
    from mathutils import Matrix

    v0, v1 = Vector(origin), Vector(target)
    axis = v1 - v0
    length = axis.length
    if length < 1e-4:
        return
    rot = axis.normalized().to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(roll_rad, 3, "Z")
    uv_layer = bm.loops.layers.uv.verify()

    steps = (0.0, 0.33, 0.67, 1.0)
    widths = [start_width + (end_width - start_width) * (s ** 0.78) for s in steps]

    def _build_ribbon(perp_local: Vector, w_scale: float) -> None:
        rows = []
        for t, w in zip(steps, widths):
            hw = w * 0.5 * w_scale
            z_off = length * t
            lift = arc_lift * 4.0 * t * (1.0 - t)
            center = v0 + rot @ Vector((0.0, 0.0, z_off)) + Vector((0.0, 0.0, lift))
            side = rot @ (perp_local * hw)
            rows.append((bm.verts.new(center - side), bm.verts.new(center + side), t))
        for i in range(len(rows) - 1):
            a0, b0, t0 = rows[i]
            a1, b1, t1 = rows[i + 1]
            face = bm.faces.new((a0, b0, b1, a1))
            for loop, uv in zip(face.loops, ((0.0, t0), (1.0, t0), (1.0, t1), (0.0, t1))):
                loop[uv_layer].uv = uv

    _build_ribbon(Vector((1.0, 0.0, 0.0)), 1.0)
    if cross_ratio > 0.05:
        _build_ribbon(Vector((0.0, 1.0, 0.0)), cross_ratio)


def setup_world_gradient(strength: float = 0.35) -> None:
    """設定柔和冷暖微漸層世界背景，避免純黑死影。"""
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("StudioWorld")
    scene.world = world
    if getattr(world, "node_tree", None) is None:
        world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")

    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.04, 0.045, 0.055, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.14, 0.16, 0.20, 1.0)
    bg.inputs["Strength"].default_value = strength

    nt.links.new(tex_coord.outputs["Generated"], sep_xyz.inputs["Vector"])
    nt.links.new(sep_xyz.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def _aim_object_at(obj: bpy.types.Object, target: Sequence[float]) -> None:
    direction = Vector(target) - obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot_quat.to_euler()


def _add_area_light(
    name: str,
    location: Sequence[float],
    target: Sequence[float],
    energy: float,
    size: float,
    color: Tuple[float, float, float],
    collection_name: str = "Studio",
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name=name, type="AREA")
    light_data.energy = energy
    light_data.size = size
    light_data.color = color
    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    light_obj.location = Vector(location)
    _aim_object_at(light_obj, target)
    return link_object(light_obj, collection_name)


def setup_studio_lighting(
    center: Sequence[float] = (0.0, 0.0, 0.5),
    radius: float = 2.0,
    floor_z: float = 0.0,
    add_floor: bool = True,
) -> None:
    """依目標包圍盒半徑自動縮放的三點光攝影棚與啞光地板。"""
    setup_world_gradient(strength=0.4)
    cx, cy, cz = center
    r = max(radius, 0.5)
    # 面積光能量隨距離平方約略放大
    scale_e = (r / 2.0) ** 2

    _add_area_light(
        "Studio_KeyLight",
        location=(cx + 2.2 * r, cy - 2.0 * r, cz + 2.4 * r),
        target=center,
        energy=260.0 * scale_e,
        size=1.4 * r,
        color=(1.0, 0.96, 0.90),
    )
    _add_area_light(
        "Studio_FillLight",
        location=(cx - 2.4 * r, cy - 1.5 * r, cz + 1.2 * r),
        target=center,
        energy=95.0 * scale_e,
        size=2.2 * r,
        color=(0.82, 0.90, 1.0),
    )
    _add_area_light(
        "Studio_RimLight",
        location=(cx - 0.6 * r, cy + 2.6 * r, cz + 2.0 * r),
        target=center,
        energy=220.0 * scale_e,
        size=1.0 * r,
        color=(0.95, 0.98, 1.0),
    )

    if add_floor:
        bpy.ops.mesh.primitive_plane_add(size=80.0 * r, location=(cx, cy, floor_z))
        floor = bpy.context.active_object
        floor.name = "Studio_Floor"
        mat = bpy.data.materials.new("Studio_Floor_Mat")
        bsdf = get_principled_bsdf(mat)
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.09, 0.10, 0.12, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.72
        floor.data.materials.append(mat)
        # 移到 Studio collection
        for col in list(floor.users_collection):
            col.objects.unlink(floor)
        link_object(floor, "Studio")


def compute_bounds(objects: Iterable[bpy.types.Object]) -> Tuple[Vector, float, float]:
    """計算物件群的世界空間包圍盒中心、半徑與最低 Z 值。"""
    pts: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(corner))

    if not pts:
        return Vector((0.0, 0.0, 0.5)), 1.5, 0.0

    min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (min_v + max_v) * 0.5
    radius = max((max_v - min_v).length * 0.5, 0.25)
    return center, radius, min_v.z


def create_camera(
    name: str,
    location: Sequence[float],
    target: Sequence[float],
    lens: float = 50.0,
    ortho_scale: Optional[float] = None,
) -> bpy.types.Object:
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.lens = lens
    if ortho_scale is not None:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho_scale
    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    cam_obj.location = Vector(location)
    _aim_object_at(cam_obj, target)
    return link_object(cam_obj, "Studio")


def _stitch_2x2(image_paths: list[str], out_path: str) -> None:
    """利用 Blender 內建 Image + NumPy 將 4 張同尺寸 PNG 拼成 2x2 Contact Sheet。"""
    loaded = [bpy.data.images.load(p, check_existing=False) for p in image_paths]
    w, h = loaded[0].size[0], loaded[0].size[1]
    canvas = np.zeros((h * 2, w * 2, 4), dtype=np.float32)

    # Blender image pixels 順序為由下而上 (bottom-to-top)
    # 上排 (row 1 in bottom-up coords): [0]=左上(ISO), [1]=右上(Front)
    # 下排 (row 0 in bottom-up coords): [2]=左下(Side), [3]=右下(Top)
    offsets = [(h, 0), (h, w), (0, 0), (0, w)]
    for img, (y0, x0) in zip(loaded, offsets):
        arr = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(arr)
        arr = arr.reshape((h, w, 4))
        canvas[y0 : y0 + h, x0 : x0 + w, :] = arr

    sheet = bpy.data.images.new("InspectSheet", width=w * 2, height=h * 2, alpha=True)
    sheet.pixels.foreach_set(canvas.ravel())
    sheet.filepath_raw = out_path
    sheet.file_format = "PNG"
    sheet.save()

    for img in loaded:
        bpy.data.images.remove(img)
    bpy.data.images.remove(sheet)


def render_inspection_sheet(
    objects: Iterable[bpy.types.Object],
    output_dir: str,
    prefix: str = "inspect",
    engine: str = "BLENDER_EEVEE",
    tile_size: int = 512,
    samples: int = 24,
) -> dict:
    """自動計算包圍盒，渲染 Iso/Front/Side/Top 四視角並拼成 2x2 檢查圖。"""
    os.makedirs(output_dir, exist_ok=True)
    scene = bpy.context.scene
    center, radius, _ = compute_bounds(objects)
    dist = radius * 3.1

    prev_cam = scene.camera
    prev_res_x, prev_res_y = scene.render.resolution_x, scene.render.resolution_y
    prev_engine = scene.render.engine

    backend_info = configure_render(engine=engine, width=tile_size, height=tile_size, samples=samples)

    ortho = radius * 2.5
    views = [
        ("iso", (center.x - dist * 0.78, center.y - dist * 0.78, center.z + dist * 0.54), 50.0, None),
        ("front", (center.x, center.y - dist, center.z), 50.0, ortho),
        ("side", (center.x - dist, center.y, center.z), 50.0, ortho),
        ("top", (center.x, center.y - 0.001, center.z + dist), 50.0, ortho),
    ]

    tile_paths: list[str] = []
    created_cams: list[bpy.types.Object] = []
    t0 = time.perf_counter()

    for tag, loc, lens, ortho_scale in views:
        cam = create_camera(f"InspectCam_{tag}", loc, center, lens=lens, ortho_scale=ortho_scale)
        created_cams.append(cam)
        scene.camera = cam
        out_file = os.path.join(output_dir, f"{prefix}_{tag}.png")
        scene.render.filepath = out_file
        bpy.ops.render.render(write_still=True)
        tile_paths.append(out_file)

    sheet_path = os.path.join(output_dir, f"{prefix}_sheet.png")
    _stitch_2x2(tile_paths, sheet_path)
    elapsed = time.perf_counter() - t0

    scene.camera = prev_cam
    scene.render.resolution_x = prev_res_x
    scene.render.resolution_y = prev_res_y
    scene.render.engine = prev_engine
    for cam in created_cams:
        cam_data = cam.data
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cam_data)

    return {
        "sheet": sheet_path,
        "tiles": tile_paths,
        "elapsed_sec": round(elapsed, 2),
        "backend": backend_info,
        "center": tuple(round(v, 3) for v in center),
        "radius": round(radius, 3),
    }


def render_wireframe_check(
    objects: Iterable[bpy.types.Object],
    out_path: str,
    width: int = 1024,
    height: int = 1024,
) -> float:
    """利用 Workbench 引擎與 Wireframe Overlay 快速輸出拓撲檢查圖。"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene = bpy.context.scene
    center, radius, _ = compute_bounds(objects)
    dist = radius * 3.0

    prev_cam = scene.camera
    prev_engine = scene.render.engine
    prev_rx, prev_ry = scene.render.resolution_x, scene.render.resolution_y

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (0.72, 0.75, 0.78)
    scene.display.shading.show_cavity = True

    cam = create_camera(
        "WireCam_iso",
        (center.x + dist * 0.72, center.y - dist * 0.78, center.z + dist * 0.52),
        center,
        lens=50.0,
    )
    scene.camera = cam
    scene.render.filepath = out_path

    # 暫時替所有目標 mesh 開啟 show_wire 以便在 Workbench 看見線框（若支援）或純 Clay+Cavity 檢視
    prev_wires = []
    for obj in objects:
        if obj.type == "MESH":
            prev_wires.append((obj, obj.show_wire, obj.show_all_edges))
            obj.show_wire = True
            obj.show_all_edges = True

    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    elapsed = time.perf_counter() - t0

    for obj, w, e in prev_wires:
        obj.show_wire = w
        obj.show_all_edges = e

    scene.camera = prev_cam
    scene.render.engine = prev_engine
    scene.render.resolution_x = prev_rx
    scene.render.resolution_y = prev_ry
    cam_data = cam.data
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)

    return round(elapsed, 2)
