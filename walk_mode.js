/**
 * 重慶國小 3D 校園「自由步行」模式（桌機）
 * - 第一人稱／第三人稱小人切換（V）、WASD／方向鍵移動、Shift 跑、拖曳或指標鎖定轉向
 * - 碰撞：圓柱體 vs. Blender 輸出的牆／隔間／欄杆碰撞盒（walk_data_chongqing.json）＋其他校舍外框；地面高度以射線取樣真實樓板、階梯與廣場
 * - 重慶樓（示範棟）：中空教室＋黑板、課桌椅（前端依 campus_cges.json 動態生成），走廊梯口按 E／Q 自動爬升至上／下一層
 */
import * as THREE from "three";

const b2t = (x, y, z) => new THREE.Vector3(x, z, -y);

const GROUND_RE =
  /^(Base_(CampusPaving|Forecourt|Gate(Apron|Curb|Pedestrian|Threshold)|GuangheSidewalk|NWCorner|Roads|SurroundingGround)|Bldg_.*(Slabs|Terrazzo|Stairs|Ramps)|Zone_Basketball_(Deck|Walkway|CorridorSteps|Court)|Zone_Courtyard_(Lawns|Bridge|BrickCurbs)|Zone_Track_(PU|Infield|East|North)|Landmark_WuquanB1_GreenRamp|Landmark_SouthCorner_ArcSlabs)/;
const GROUND_EXCLUDE_RE = /Foliage|Trunk|Frond|Shrub|Handrail|Fence/;

const BOUNDS = { x0: -78, x1: 72, y0: -72, y1: 48 };
const BODY_R = 0.26;
const WALK_SPEED = 3.6;
const RUN_SPEED = 6.5;
const CQ_FOOTPRINT = { x0: -74.4, x1: -6.6, y0: -43.6, y1: -29.0 };

const SPAWNS = {
  gate: { label: "🏫 校門前庭（廣和街 31 號）", x: -63.5, y: 2.5, yaw: 0 },
  court: { label: "🏀 重慶樓南側球場", x: -38.0, y: -47.0, yaw: Math.PI / 2 },
  cq1: { label: "🏢 重慶樓 1F 穿堂", x: -27.8, y: -41.8, floor: 1, yaw: Math.PI / 2 },
  cq2: { label: "🏢 重慶樓 2F 走廊", x: -27.8, y: -41.8, floor: 2, yaw: Math.PI },
  cq3: { label: "🏢 重慶樓 3F 走廊", x: -27.8, y: -41.8, floor: 3, yaw: Math.PI },
  cq4: { label: "🏢 重慶樓 4F 走廊", x: -27.8, y: -41.8, floor: 4, yaw: Math.PI },
  cq5: { label: "🏢 重慶樓 5F 走廊", x: -27.8, y: -41.8, floor: 5, yaw: Math.PI },
};

class InstBox {
  constructor(color, opts = {}) {
    this.color = color;
    this.items = [];
    this.opts = opts;
  }
  /** 以 Blender 座標 (x, y, z) 與尺寸 (sx, sy, sz) 加入一個長方體；yaw 為繞 Blender Z 軸旋轉 */
  add(bx, by, bz, sx, sy, sz, yaw = 0, color = null) {
    this.items.push([bx, by, bz, sx, sy, sz, yaw, color]);
  }
  build() {
    if (this.items.length === 0) return null;
    const geo = new THREE.BoxGeometry(1, 1, 1);
    const mat = new THREE.MeshStandardMaterial({
      color: this.opts.perInstance ? 0xffffff : this.color,
      roughness: this.opts.roughness ?? 0.8,
      metalness: this.opts.metalness ?? 0.0,
      emissive: this.opts.emissive ? new THREE.Color(this.opts.emissive) : new THREE.Color(0x000000),
      emissiveIntensity: this.opts.emissive ? 1.0 : 0.0,
    });
    const mesh = new THREE.InstancedMesh(geo, mat, this.items.length);
    const m4 = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const pos = new THREE.Vector3();
    const scl = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    const col = new THREE.Color();
    this.items.forEach((it, i) => {
      const [bx, by, bz, sx, sy, sz, yaw, c] = it;
      pos.set(bx, bz, -by);
      q.setFromAxisAngle(up, yaw);
      scl.set(sx, sz, sy);
      m4.compose(pos, q, scl);
      mesh.setMatrixAt(i, m4);
      if (this.opts.perInstance) {
        col.set(c || this.color);
        mesh.setColorAt(i, col);
      }
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.castShadow = false;
    mesh.receiveShadow = false;
    mesh.frustumCulled = false;
    return mesh;
  }
}

function buildAvatar() {
  const g = new THREE.Group();
  const M = (c, r = 0.7) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const shirt = M(0x3b9ae1);
  const pants = M(0x334155);
  const skin = M(0xf2c7a3, 0.55);
  const hair = M(0x2a1f17, 0.9);
  const bag = M(0xef4444);
  const shoe = M(0x1f2937);
  const dark = new THREE.MeshBasicMaterial({ color: 0x111827 });

  const box = (mat, sx, sy, sz, x, y, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
    m.position.set(x, y, z);
    return m;
  };

  // 前方為 +X；側向為 Z
  g.add(box(shirt, 0.24, 0.48, 0.38, 0, 0.98, 0));
  g.add(box(bag, 0.14, 0.34, 0.3, -0.18, 1.0, 0));
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 18, 14), skin);
  head.position.set(0, 1.42, 0);
  g.add(head);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.215, 18, 10, 0, Math.PI * 2, 0, Math.PI * 0.55), hair);
  cap.position.set(-0.01, 1.44, 0);
  g.add(cap);
  g.add(box(dark, 0.02, 0.05, 0.05, 0.195, 1.43, 0.08));
  g.add(box(dark, 0.02, 0.05, 0.05, 0.195, 1.43, -0.08));

  const mkLimb = (mat, sx, sy, sz, px, py, pz, footMat) => {
    const pivot = new THREE.Group();
    pivot.position.set(px, py, pz);
    pivot.add(box(mat, sx, sy, sz, 0, -sy * 0.5, 0));
    if (footMat) pivot.add(box(footMat, sx + 0.08, 0.07, sz + 0.02, 0.04, -sy + 0.035, 0));
    g.add(pivot);
    return pivot;
  };
  const legL = mkLimb(pants, 0.14, 0.64, 0.15, 0, 0.74, 0.1, shoe);
  const legR = mkLimb(pants, 0.14, 0.64, 0.15, 0, 0.74, -0.1, shoe);
  const armL = mkLimb(shirt, 0.11, 0.42, 0.11, 0, 1.2, 0.25, skin);
  const armR = mkLimb(shirt, 0.11, 0.42, 0.11, 0, 1.2, -0.25, skin);

  g.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = false;
      o.receiveShadow = false;
    }
  });

  const blob = new THREE.Mesh(
    new THREE.CircleGeometry(0.42, 20),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.26, depthWrite: false })
  );
  blob.rotation.x = -Math.PI / 2;
  blob.position.y = 0.025;

  const root = new THREE.Group();
  root.add(g);
  root.add(blob);
  root.userData = { body: g, legL, legR, armL, armR, blob };
  return root;
}

export function createWalkMode(opts) {
  const { scene, camera, renderer, controls, getMeshes, getRooms, spec, buildHash, requestRender, onEnter, onExit } = opts;
  const canvas = renderer.domElement;

  const S = {
    active: false,
    loaded: false,
    loading: null,
    data: null,
    colliders: [],
    groundMeshes: [],
    interior: null,
    avatar: null,
    light: null,
    view: "third",
    camDist: 4.2,
    yaw: Math.PI / 2,
    pitch: -0.12,
    avatarYaw: Math.PI / 2,
    walkPhase: 0,
    moving: 0,
    P: { x: -63.5, y: 2.5, z: 0.3 },
    gz: 0.3,
    riding: null,
    keys: new Set(),
    dragging: false,
    dragMoved: 0,
    hudTimer: 0,
    saved: null,
    abort: null,
    fade: 0,
  };

  const raycaster = new THREE.Raycaster();
  const rayDir = new THREE.Vector3(0, -1, 0);
  const rayOrg = new THREE.Vector3();

  const el = {
    hud: () => document.getElementById("walkHud"),
    info: () => document.getElementById("walkInfo"),
    prompt: () => document.getElementById("walkPrompt"),
    fade: () => document.getElementById("walkFade"),
    viewBtn: () => document.getElementById("btnWalkView"),
    spawn: () => document.getElementById("walkSpawnSelect"),
    exit: () => document.getElementById("btnWalkExit"),
    toolBtn: () => document.getElementById("btnWalk"),
  };

  // ---------- 資料載入 ----------
  async function ensureLoaded() {
    if (S.loaded) return true;
    if (S.loading) return S.loading;
    S.loading = (async () => {
      try {
        const res = await fetch(`./walk_data_chongqing.json?v=${buildHash || "1"}`);
        if (!res.ok) throw new Error(`walk data HTTP ${res.status}`);
        S.data = await res.json();
      } catch (e) {
        console.warn("walk data load failed", e);
        S.loading = null;
        return false;
      }
      // 碰撞盒：重慶樓詳細碰撞 + 其他校舍外框（不可進入）
      const cols = [];
      for (const c of S.data.colliders) cols.push(c);
      for (const b of spec?.buildings || []) {
        if (b.id === "Bldg_Chongqing") continue;
        cols.push([b.x_min, b.x_max, b.y_min, b.y_max, -5, 60]);
      }
      S.colliders = cols;
      S.floors = S.data.floors;
      buildInterior();
      S.loaded = true;
      return true;
    })();
    return S.loading;
  }

  function collectGroundMeshes() {
    const out = [];
    for (const m of getMeshes()) {
      const n = m.name || "";
      if (GROUND_RE.test(n) && !GROUND_EXCLUDE_RE.test(n)) out.push(m);
    }
    S.groundMeshes = out;
  }

  // ---------- 室內物件（黑板、課桌椅、書架）----------
  function buildInterior() {
    const wood = new InstBox(0xc79a62, { roughness: 0.7 });
    const metal = new InstBox(0x6b7280, { roughness: 0.5, metalness: 0.4 });
    const chair = new InstBox(0x3b82f6, { roughness: 0.6 });
    const board = new InstBox(0x1f4d3a, { roughness: 0.9 });
    const white = new InstBox(0xf1f5f9, { roughness: 0.6 });
    const books = new InstBox(0xffffff, { perInstance: true, roughness: 0.8 });
    const lamp = new InstBox(0xffffff, { emissive: 0xfff6dc, roughness: 0.4 });
    const shelf = new InstBox(0xd9d2c3, { roughness: 0.7 });

    const rooms = getRooms ? getRooms() : [];
    const bySpecKey = new Map();
    for (const r of rooms) if (r.specKey) bySpecKey.set(r.specKey, r);

    const palette = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#14b8a6", "#f43f5e", "#64748b"];
    let pi = 0;

    const addDesk = (x, y, z, yaw = 0) => {
      // 學生課桌：長邊沿 Y（面向西側黑板）
      const c = Math.cos(yaw);
      const s = Math.sin(yaw);
      const rot = (dx, dy) => [x + dx * c - dy * s, y + dx * s + dy * c];
      const [tx, ty] = rot(0, 0);
      wood.add(tx, ty, z + 0.72, 0.46, 0.62, 0.035, yaw);
      for (const [lx, ly] of [
        [-0.2, -0.27],
        [0.2, -0.27],
        [-0.2, 0.27],
        [0.2, 0.27],
      ]) {
        const [px, py] = rot(lx, ly);
        metal.add(px, py, z + 0.355, 0.035, 0.035, 0.7, yaw);
      }
      // 椅子（在桌子後方 +X）
      const [cx, cy] = rot(0.62, 0);
      chair.add(cx, cy, z + 0.44, 0.4, 0.4, 0.04, yaw);
      const [bx, by] = rot(0.8, 0);
      chair.add(bx, by, z + 0.66, 0.04, 0.4, 0.4, yaw);
      for (const [lx, ly] of [
        [0.47, -0.17],
        [0.77, -0.17],
        [0.47, 0.17],
        [0.77, 0.17],
      ]) {
        const [px, py] = rot(lx, ly);
        metal.add(px, py, z + 0.21, 0.03, 0.03, 0.42, yaw);
      }
    };

    for (const rm of S.data.rooms) {
      const info = rm.key ? bySpecKey.get(rm.key) : null;
      const name = info?.name || "";
      const cat = info?.cat || "";
      if (rm.kind !== "room") continue;
      const width = rm.x1 - rm.x0;
      const depth = rm.y1 - rm.y0;
      const zf = rm.z_floor;
      const cy = 0.5 * (rm.y0 + rm.y1);
      let layout = "classroom";
      if (name.includes("廁")) layout = "toilet";
      else if (name.includes("圖書")) layout = "library";
      else if (cat === "admin" || /辦公室|資料室|諮商/.test(name)) layout = "office";
      else if (name.includes("唱遊") || cat === "kinder") layout = "hall";
      if (layout === "toilet") continue;

      if (layout === "classroom" || layout === "hall") {
        // 西側隔間牆黑板
        const bw = Math.min(4.4, depth * 0.55);
        board.add(rm.x0 + 0.14, cy, zf + 1.6, 0.03, bw, 1.15);
        wood.add(rm.x0 + 0.13, cy, zf + 1.6, 0.025, bw + 0.14, 1.29);
        wood.add(rm.x0 + 0.2, cy, zf + 0.98, 0.14, bw, 0.04);
      }
      if (layout === "classroom") {
        // 講桌
        wood.add(rm.x0 + 0.95, cy - 1.4, zf + 0.75, 0.6, 1.3, 0.05);
        wood.add(rm.x0 + 0.95, cy - 1.4, zf + 0.37, 0.5, 1.2, 0.7);
        // 學生課桌椅
        const gx0 = rm.x0 + 2.4;
        const gx1 = rm.x1 - 1.0;
        const gy0 = rm.y0 + 0.95;
        const gy1 = rm.y1 - 0.95;
        const rows = Math.max(1, Math.floor((gx1 - gx0) / 1.35) + 1);
        const colsN = Math.max(1, Math.min(6, Math.floor((gy1 - gy0) / 1.4) + 1));
        for (let i = 0; i < rows; i++) {
          const x = rows === 1 ? 0.5 * (gx0 + gx1) : gx0 + (i * (gx1 - gx0 - 0.9)) / Math.max(1, rows - 1);
          for (let j = 0; j < colsN; j++) {
            const y = colsN === 1 ? cy : gy0 + (j * (gy1 - gy0)) / (colsN - 1);
            addDesk(x, y, zf);
          }
        }
        // 後方置物櫃
        shelf.add(rm.x1 - 0.35, cy, zf + 0.5, 0.4, Math.min(5.5, depth * 0.7), 1.0);
      } else if (layout === "library") {
        const nShelf = Math.max(2, Math.floor((width - 0.8) / 1.15));
        for (let i = 0; i < nShelf; i++) {
          const x = rm.x0 + 0.7 + i * ((width - 1.4) / Math.max(1, nShelf - 1));
          const y = rm.y1 - 0.45;
          shelf.add(x, y, zf + 0.95, 0.9, 0.34, 1.9);
          for (let k = 0; k < 4; k++) {
            books.add(x, y - 0.18, zf + 0.35 + k * 0.45, 0.82, 0.03, 0.34, 0, palette[(pi++) % palette.length]);
          }
        }
        for (let t = 0; t < 2; t++) {
          const x = rm.x0 + width * (0.3 + 0.4 * t);
          wood.add(x, cy - 0.6, zf + 0.74, 2.2, 1.0, 0.05);
          metal.add(x, cy - 0.6, zf + 0.37, 2.0, 0.8, 0.7);
          chair.add(x - 0.6, cy - 1.35, zf + 0.44, 0.4, 0.4, 0.04);
          chair.add(x + 0.6, cy - 1.35, zf + 0.44, 0.4, 0.4, 0.04);
        }
      } else if (layout === "office") {
        const nDesk = Math.max(1, Math.floor(width / 2.2));
        for (let i = 0; i < nDesk; i++) {
          const x = rm.x0 + (width * (i + 0.5)) / nDesk;
          wood.add(x, cy + 0.6, zf + 0.74, 1.4, 0.7, 0.05);
          metal.add(x, cy + 0.6, zf + 0.37, 1.3, 0.6, 0.7);
          chair.add(x, cy - 0.1, zf + 0.46, 0.45, 0.45, 0.05);
          white.add(x, cy + 0.7, zf + 0.9, 0.35, 0.03, 0.25);
        }
        shelf.add(rm.x1 - 0.35, cy, zf + 0.95, 0.4, Math.min(4.5, depth * 0.55), 1.9);
      }
      // 天花燈已由 GLB 提供；補一組室內補光面板感
      lamp.add(0.5 * (rm.x0 + rm.x1), cy, rm.z_ceil - 0.05, Math.min(1.6, width * 0.3), 0.3, 0.04);
    }

    const group = new THREE.Group();
    group.name = "WalkInterior";
    for (const b of [wood, metal, chair, board, white, books, lamp, shelf]) {
      const m = b.build();
      if (m) group.add(m);
    }
    group.visible = false;
    scene.add(group);
    S.interior = group;
  }

  // ---------- 碰撞與地面 ----------
  function resolveCollisions(x, y, z) {
    const zlo = z + 0.4;
    const zhi = z + 1.65;
    const r = BODY_R;
    const cols = S.colliders;
    for (let iter = 0; iter < 3; iter++) {
      let moved = false;
      for (let i = 0; i < cols.length; i++) {
        const c = cols[i];
        if (c[5] <= zlo || c[4] >= zhi) continue;
        if (x < c[0] - r || x > c[1] + r || y < c[2] - r || y > c[3] + r) continue;
        const cx = x < c[0] ? c[0] : x > c[1] ? c[1] : x;
        const cy = y < c[2] ? c[2] : y > c[3] ? c[3] : y;
        const dx = x - cx;
        const dy = y - cy;
        const d2 = dx * dx + dy * dy;
        if (d2 >= r * r) continue;
        if (d2 > 1e-9) {
          const d = Math.sqrt(d2);
          const push = r - d;
          x += (dx / d) * push;
          y += (dy / d) * push;
        } else {
          const pl = x - c[0] + r;
          const pr = c[1] - x + r;
          const pb = y - c[2] + r;
          const pt = c[3] - y + r;
          const m = Math.min(pl, pr, pb, pt);
          if (m === pl) x = c[0] - r;
          else if (m === pr) x = c[1] + r;
          else if (m === pb) y = c[2] - r;
          else y = c[3] + r;
        }
        moved = true;
      }
      if (!moved) break;
    }
    x = Math.min(BOUNDS.x1, Math.max(BOUNDS.x0, x));
    y = Math.min(BOUNDS.y1, Math.max(BOUNDS.y0, y));
    return [x, y];
  }

  function insideCollider(x, y, z, margin = 0.12) {
    const cols = S.colliders;
    for (let i = 0; i < cols.length; i++) {
      const c = cols[i];
      if (z < c[4] - margin || z > c[5] + margin) continue;
      if (x > c[0] - margin && x < c[1] + margin && y > c[2] - margin && y < c[3] + margin) return true;
    }
    return false;
  }

  function groundAt(x, y, z) {
    rayOrg.set(x, z + 0.8, -y);
    raycaster.set(rayOrg, rayDir);
    raycaster.near = 0;
    raycaster.far = 2.6;
    const hits = raycaster.intersectObjects(S.groundMeshes, false);
    if (hits.length === 0) return null;
    return hits[0].point.y;
  }

  // ---------- 房間／樓層判定 ----------
  function floorAtZ(z) {
    if (!S.floors) return null;
    let best = null;
    let bd = 1e9;
    for (const f of S.floors) {
      const d = Math.abs(z - f.z_top);
      if (d < bd) {
        bd = d;
        best = f;
      }
    }
    return bd < 1.8 ? best : null;
  }

  function inChongqing(x, y) {
    return x > CQ_FOOTPRINT.x0 && x < CQ_FOOTPRINT.x1 && y > CQ_FOOTPRINT.y0 && y < CQ_FOOTPRINT.y1;
  }

  function describeLocation() {
    const { x, y, z } = S.P;
    if (!inChongqing(x, y)) return "校園戶外";
    const fl = floorAtZ(z);
    if (!fl) return "重慶樓";
    const rooms = S.data.rooms;
    const infoList = getRooms ? getRooms() : [];
    for (const r of rooms) {
      if (r.floor !== fl.floor) continue;
      if (x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1) {
        if (r.key) {
          const info = infoList.find((i) => i.specKey === r.key);
          if (info) return `重慶樓 ${fl.floor}F・${info.short || info.name}`;
        }
        if (r.kind === "stair") return `重慶樓 ${fl.floor}F・6梯 梯間`;
        return `重慶樓 ${fl.floor}F・儲藏空間`;
      }
    }
    if (y <= S.data.corridor_y + 1.4 && y >= -43.4) return `重慶樓 ${fl.floor}F・南側走廊`;
    if (y >= -32.2) return `重慶樓 ${fl.floor}F・北側走廊`;
    return `重慶樓 ${fl.floor}F`;
  }

  function nearStair() {
    if (!S.data || !inChongqing(S.P.x, S.P.y)) return null;
    for (const s of S.data.stairs) {
      if (Math.hypot(S.P.x - s.x, S.P.y - s.y) <= s.r) return s;
    }
    return null;
  }

  // ---------- 輸入 ----------
  function isTyping() {
    const t = document.activeElement?.tagName;
    return t === "INPUT" || t === "TEXTAREA" || t === "SELECT";
  }

  function startRide(dir) {
    if (S.riding) return;
    const st = nearStair();
    const fl = floorAtZ(S.P.z);
    if (!st || !fl) return;
    const target = S.floors.find((f) => f.floor === fl.floor + dir);
    if (!target) return;
    S.riding = {
      t: 0,
      dur: 1.35,
      z0: S.P.z,
      z1: target.z_top,
      x0: S.P.x,
      y0: S.P.y,
      x1: st.x,
      y1: st.y,
      switched: false,
      label: `${st.name} ${dir > 0 ? "上樓" : "下樓"} → ${target.floor}F`,
    };
    S.walkPhase = 0;
  }

  function onKeyDown(e) {
    if (!S.active || isTyping()) return;
    const code = e.code;
    if (["KeyW", "KeyA", "KeyS", "KeyD", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "ShiftLeft", "ShiftRight", "Space"].includes(code)) {
      S.keys.add(code);
      e.preventDefault();
    } else if (code === "KeyV") {
      toggleView();
    } else if (code === "KeyE") {
      startRide(+1);
    } else if (code === "KeyQ") {
      startRide(-1);
    } else if (code === "Escape") {
      if (!document.pointerLockElement) exit();
    }
  }
  function onKeyUp(e) {
    S.keys.delete(e.code);
  }
  function onBlur() {
    S.keys.clear();
    S.dragging = false;
  }

  function look(dx, dy) {
    S.yaw -= dx * 0.0032;
    S.pitch -= dy * 0.0028;
    S.pitch = Math.max(-1.15, Math.min(0.85, S.pitch));
  }

  function onPointerDown(e) {
    if (!S.active || e.button !== 0) return;
    S.dragging = true;
    S.dragMoved = 0;
  }
  function onPointerMove(e) {
    if (!S.active) return;
    if (document.pointerLockElement === canvas) {
      look(e.movementX || 0, e.movementY || 0);
    } else if (S.dragging) {
      S.dragMoved += Math.abs(e.movementX || 0) + Math.abs(e.movementY || 0);
      look(e.movementX || 0, e.movementY || 0);
    }
  }
  function onPointerUp() {
    if (!S.active) return;
    const wasClick = S.dragging && S.dragMoved < 4;
    S.dragging = false;
    if (wasClick && document.pointerLockElement !== canvas && canvas.requestPointerLock) {
      try {
        const p = canvas.requestPointerLock();
        if (p && p.catch) p.catch(() => {});
      } catch (_) {
        // pointer lock unavailable: keep drag-look only
      }
    }
  }
  function onWheel(e) {
    if (!S.active) return;
    e.preventDefault();
    if (S.view === "third") {
      S.camDist = Math.max(1.6, Math.min(9, S.camDist + e.deltaY * 0.004));
    }
  }

  function bindInput() {
    S.abort = new AbortController();
    const sig = { signal: S.abort.signal };
    window.addEventListener("keydown", onKeyDown, sig);
    window.addEventListener("keyup", onKeyUp, sig);
    window.addEventListener("blur", onBlur, sig);
    canvas.addEventListener("pointerdown", onPointerDown, sig);
    window.addEventListener("pointermove", onPointerMove, sig);
    window.addEventListener("pointerup", onPointerUp, sig);
    canvas.addEventListener("wheel", onWheel, { passive: false, signal: S.abort.signal });
  }
  function unbindInput() {
    S.abort?.abort();
    S.abort = null;
    S.keys.clear();
    if (document.pointerLockElement === canvas && document.exitPointerLock) document.exitPointerLock();
  }

  // ---------- 生成點 ----------
  function placeAt(x, y, floorNo, yaw) {
    S.P.x = x;
    S.P.y = y;
    let z = 0.45;
    if (floorNo && S.floors) {
      const f = S.floors.find((fl) => fl.floor === floorNo);
      if (f) z = f.z_top;
    }
    S.P.z = z;
    const g = groundAt(x, y, z);
    S.gz = g !== null ? g : z;
    S.P.z = S.gz;
    if (typeof yaw === "number") {
      S.yaw = yaw;
      S.avatarYaw = yaw;
    }
    S.pitch = -0.1;
    S.riding = null;
  }

  function spawnByKey(key) {
    const sp = SPAWNS[key] || SPAWNS.court;
    placeAt(sp.x, sp.y, sp.floor || 0, sp.yaw);
  }

  function roomEntry(roomRec) {
    // roomRec：tour_app 的 allRooms 紀錄（含 specKey、floor）
    if (!S.data) return null;
    const rm = S.data.rooms.find((r) => r.key === roomRec.specKey);
    const flNum = parseInt(String(roomRec.floor), 10);
    if (rm) return { x: rm.door_x, y: S.data.corridor_y, floor: rm.floor, yaw: Math.PI / 2 };
    if (!Number.isNaN(flNum)) {
      const x = Math.max(-72, Math.min(-9, roomRec.pos?.[0] ?? -27.8));
      return { x, y: S.data.corridor_y, floor: flNum, yaw: Math.PI / 2 };
    }
    return null;
  }

  // ---------- 進出 ----------
  function showHud(on) {
    const hud = el.hud();
    if (hud) hud.hidden = !on;
    el.toolBtn()?.classList.toggle("active", on);
  }

  function refreshViewBtn() {
    const b = el.viewBtn();
    if (b) b.textContent = S.view === "third" ? "👤 第三人稱" : "👁 第一人稱";
  }

  function toggleView() {
    S.view = S.view === "third" ? "first" : "third";
    if (S.avatar) S.avatar.visible = S.view === "third";
    refreshViewBtn();
  }

  async function enter(spec2) {
    const ok = await ensureLoaded();
    if (!ok) return false;
    if (!S.avatar) {
      S.avatar = buildAvatar();
      S.avatar.visible = false;
      scene.add(S.avatar);
      S.light = new THREE.PointLight(0xfff1d6, 7, 9, 1.6);
      S.light.visible = false;
      scene.add(S.light);
    }
    collectGroundMeshes();
    if (!S.active) {
      S.saved = {
        pos: camera.position.clone(),
        tgt: controls.target.clone(),
        near: camera.near,
        controlsEnabled: controls.enabled,
      };
      bindInput();
    }
    S.active = true;
    controls.enabled = false;
    camera.near = 0.15;
    camera.clearViewOffset();
    camera.updateProjectionMatrix();
    if (spec2?.x !== undefined) placeAt(spec2.x, spec2.y, spec2.floor || 0, spec2.yaw);
    else spawnByKey(spec2?.key || "court");
    if (S.interior) S.interior.visible = true;
    if (S.light) S.light.visible = true;
    S.avatar.visible = S.view === "third";
    showHud(true);
    refreshViewBtn();
    const sel = el.spawn();
    if (sel && spec2?.key) sel.value = spec2.key;
    onEnter?.();
    requestRender(4);
    return true;
  }

  function exit() {
    if (!S.active) return;
    S.active = false;
    unbindInput();
    showHud(false);
    if (S.interior) S.interior.visible = false;
    if (S.avatar) S.avatar.visible = false;
    if (S.light) S.light.visible = false;
    controls.enabled = S.saved?.controlsEnabled ?? true;
    camera.near = S.saved?.near ?? 0.5;
    camera.updateProjectionMatrix();
    // 回到鳥瞰：以玩家所在位置為中心的環視角
    const p = b2t(S.P.x, S.P.y, S.P.z + 1);
    controls.target.copy(p);
    camera.position.set(p.x - 26, p.y + 22, p.z + 30);
    controls.update();
    const fade = el.fade();
    if (fade) fade.style.opacity = "0";
    onExit?.();
    requestRender(8);
  }

  // ---------- 每幀更新 ----------
  function updateRide(dt) {
    const r = S.riding;
    r.t += dt / r.dur;
    const t = Math.min(1, r.t);
    const e = (u) => u * u * (3 - 2 * u);
    const walkU = Math.min(1, t / 0.28);
    S.P.x = r.x0 + (r.x1 - r.x0) * e(walkU);
    S.P.y = r.y0 + (r.y1 - r.y0) * e(walkU);
    const climbU = Math.max(0, Math.min(1, (t - 0.28) / 0.57));
    S.P.z = r.z0 + (r.z1 - r.z0) * e(climbU);
    S.gz = S.P.z;
    S.moving = 1;
    S.walkPhase += dt * 9;
    // 轉場淡出入
    let fade = 0;
    if (t >= 0.3 && t <= 0.52) fade = Math.min(1, (t - 0.3) / 0.14);
    else if (t > 0.52 && t < 0.92) fade = Math.max(0, 1 - (t - 0.52) / 0.34);
    const fadeEl = el.fade();
    if (fadeEl) fadeEl.style.opacity = String(Math.min(1, fade));
    if (t >= 1) {
      S.riding = null;
      S.P.z = r.z1;
      const g = groundAt(S.P.x, S.P.y, S.P.z);
      S.gz = g !== null ? g : S.P.z;
      S.P.z = S.gz;
      if (fadeEl) fadeEl.style.opacity = "0";
    }
  }

  function updateMove(dt) {
    const k = S.keys;
    const fwd = (k.has("KeyW") || k.has("ArrowUp") ? 1 : 0) - (k.has("KeyS") || k.has("ArrowDown") ? 1 : 0);
    const side = (k.has("KeyD") ? 1 : 0) - (k.has("KeyA") ? 1 : 0);
    const turn = (k.has("ArrowLeft") ? 1 : 0) - (k.has("ArrowRight") ? 1 : 0);
    if (turn) S.yaw += turn * 1.9 * dt;

    const cs = Math.cos(S.yaw);
    const sn = Math.sin(S.yaw);
    let dx = cs * fwd + sn * side;
    let dy = sn * fwd - cs * side;
    const len = Math.hypot(dx, dy);
    let moving = 0;
    if (len > 0.001) {
      dx /= len;
      dy /= len;
      const speed = k.has("ShiftLeft") || k.has("ShiftRight") ? RUN_SPEED : WALK_SPEED;
      const step = speed * dt;
      const nx = S.P.x + dx * step;
      const ny = S.P.y + dy * step;
      const attempt = (tx, ty) => {
        const [rx, ry] = resolveCollisions(tx, ty, S.P.z);
        const g = groundAt(rx, ry, S.P.z);
        if (g === null) return false;
        if (g - S.P.z > 0.52 || S.P.z - g > 1.1) return false;
        S.P.x = rx;
        S.P.y = ry;
        S.gz = g;
        return true;
      };
      if (attempt(nx, ny) || attempt(nx, S.P.y) || attempt(S.P.x, ny)) moving = 1;
      // 第三人稱：小人面向移動方向
      const target = Math.atan2(dy, dx);
      let diff = target - S.avatarYaw;
      while (diff > Math.PI) diff -= Math.PI * 2;
      while (diff < -Math.PI) diff += Math.PI * 2;
      S.avatarYaw += diff * Math.min(1, dt * 12);
      S.walkPhase += dt * (speed / WALK_SPEED) * 7.5;
    }
    S.moving += (moving - S.moving) * Math.min(1, dt * 10);
    // 垂直吸附（上樓梯平順、下階緩降）
    if (S.gz > S.P.z) S.P.z = Math.min(S.gz, S.P.z + dt * 4.5);
    else if (S.gz < S.P.z) S.P.z = Math.max(S.gz, S.P.z - dt * 9);
  }

  function updateAvatar() {
    const av = S.avatar;
    if (!av) return;
    av.position.copy(b2t(S.P.x, S.P.y, S.P.z));
    av.rotation.y = S.view === "third" ? S.avatarYaw : S.yaw;
    const u = av.userData;
    const sw = Math.sin(S.walkPhase) * 0.75 * S.moving;
    u.legL.rotation.z = sw;
    u.legR.rotation.z = -sw;
    u.armL.rotation.z = -sw * 0.8;
    u.armR.rotation.z = sw * 0.8;
    u.body.position.y = Math.abs(Math.sin(S.walkPhase)) * 0.035 * S.moving;
  }

  const _dir = new THREE.Vector3();
  function updateCamera() {
    const cp = Math.cos(S.pitch);
    const lx = Math.cos(S.yaw) * cp;
    const ly = Math.sin(S.yaw) * cp;
    const lz = Math.sin(S.pitch);
    if (S.view === "first") {
      const head = b2t(S.P.x, S.P.y, S.P.z + 1.55);
      camera.position.copy(head);
      _dir.set(lx, lz, -ly);
      camera.lookAt(head.x + _dir.x, head.y + _dir.y, head.z + _dir.z);
    } else {
      const pivotZ = S.P.z + 1.3;
      // 相機沿視線反方向退後，碰到牆就縮短距離
      let dist = S.camDist;
      for (let t = 0.3; t <= S.camDist; t += 0.2) {
        const px = S.P.x - lx * t;
        const py = S.P.y - ly * t;
        const pz = pivotZ - lz * t;
        if (insideCollider(px, py, pz, 0.18)) {
          dist = Math.max(0.5, t - 0.3);
          break;
        }
      }
      const cx = S.P.x - lx * dist;
      const cy = S.P.y - ly * dist;
      const cz = Math.max(S.P.z + 0.25, pivotZ - lz * dist);
      camera.position.copy(b2t(cx, cy, cz));
      const tgt = b2t(S.P.x, S.P.y, pivotZ);
      camera.lookAt(tgt);
      if (S.avatar) S.avatar.visible = dist > 0.9;
    }
    if (S.light) {
      const lp = b2t(S.P.x, S.P.y, S.P.z + 2.6);
      S.light.position.copy(lp);
    }
  }

  function updateHud(dt) {
    S.hudTimer -= dt;
    if (S.hudTimer > 0) return;
    S.hudTimer = 0.15;
    const info = el.info();
    if (info) info.textContent = `📍 ${describeLocation()}`;
    const pr = el.prompt();
    if (!pr) return;
    if (S.riding) {
      pr.hidden = false;
      pr.textContent = `🪜 ${S.riding.label}…`;
      return;
    }
    const st = nearStair();
    const fl = floorAtZ(S.P.z);
    if (st && fl) {
      const parts = [];
      if (S.floors.some((f) => f.floor === fl.floor + 1)) parts.push(`<kbd>E</kbd> 上樓 ▲ ${fl.floor + 1}F`);
      if (S.floors.some((f) => f.floor === fl.floor - 1)) parts.push(`<kbd>Q</kbd> 下樓 ▼ ${fl.floor - 1}F`);
      pr.hidden = false;
      pr.innerHTML = `🪜 ${st.name}　${parts.join("　")}`;
    } else {
      pr.hidden = true;
    }
  }

  function update(dt) {
    if (!S.active) return;
    dt = Math.min(dt, 0.05);
    if (S.riding) updateRide(dt);
    else updateMove(dt);
    updateAvatar();
    updateCamera();
    updateHud(dt);
    requestRender(2);
  }

  // ---------- HUD 綁定 ----------
  function bindHud() {
    const sel = el.spawn();
    if (sel && sel.options.length === 0) {
      for (const [k, v] of Object.entries(SPAWNS)) {
        const o = document.createElement("option");
        o.value = k;
        o.textContent = v.label;
        sel.appendChild(o);
      }
      sel.value = "court";
      sel.addEventListener("change", () => {
        if (S.active) {
          spawnByKey(sel.value);
          sel.blur();
        }
      });
    }
    el.viewBtn()?.addEventListener("click", () => toggleView());
    el.exit()?.addEventListener("click", () => exit());
  }
  bindHud();

  return {
    get active() {
      return S.active;
    },
    get ready() {
      return S.loaded;
    },
    enter,
    exit,
    update,
    toggleView,
    ensureLoaded,
    roomEntry,
    spawns: SPAWNS,
    async enterAtRoom(roomRec) {
      const ok = await ensureLoaded();
      if (!ok) return false;
      const ent = roomEntry(roomRec);
      if (!ent) return false;
      return enter({ x: ent.x, y: ent.y, floor: ent.floor, yaw: ent.yaw });
    },
    canWalkRoom(roomRec) {
      return roomRec?.zoneId === "Bldg_Chongqing";
    },
  };
}
