/**
 * 重慶國小 3D 校園「全校四棟自由步行」模式（桌機）
 * - 涵蓋廣和樓、和平樓、五權樓、重慶樓全部中空教室（1F–5F）與戶外操場／球場／中庭
 * - 第一人稱／第三人稱紅書包小人切換（V）、WASD／方向鍵移動、Shift 跑步、滑鼠拖曳／PointerLock 轉向
 * - 互動橫拉教室木門：點擊門板或走近按 F 鍵觸發平滑滑動開關動畫＋動態門板碰撞
 * - 全校 1 梯～9 梯與廣和樓無障礙電梯：走近梯口按 E 上樓／Q 下樓自動爬升轉場
 * - 室內家具：依 campus_cges.json 以 InstancedMesh 動態鋪設黑板、講桌、課桌椅、書架、辦公桌與視聽中心座位
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
const WALKABLE_BLDGS = new Set(["Bldg_Guanghe", "Bldg_Heping", "Bldg_Wuquan", "Bldg_Chongqing"]);

const SPAWNS = {
  gate: { label: "🏫 廣和街 31 號主校門前庭", x: -63.5, y: 2.5, yaw: 0 },
  gh1: { label: "🏛 廣和樓 1F 彩繪穿堂", x: -46.0, y: 0.5, bldg: "Bldg_Guanghe", floor: 1, yaw: 0 },
  gh3: { label: "🏛 廣和樓 3F 行政區（校長室）", x: -32.75, y: -2.0, bldg: "Bldg_Guanghe", floor: 3, yaw: Math.PI },
  gh5: { label: "🏛 廣和樓 5F 視聽中心走廊", x: -32.75, y: 0.5, bldg: "Bldg_Guanghe", floor: 5, yaw: Math.PI },
  hp2: { label: "🏫 和平樓 2F 南側走廊", x: -36.8, y: 26.75, bldg: "Bldg_Heping", floor: 2, yaw: Math.PI / 2 },
  hp5: { label: "🏫 和平樓 5F 六年級走廊", x: -36.8, y: 26.75, bldg: "Bldg_Heping", floor: 5, yaw: Math.PI / 2 },
  wq1: { label: "🏫 五權樓 1F 西側中庭走廊", x: -5.8, y: -22.0, bldg: "Bldg_Wuquan", floor: 1, yaw: 0 },
  wq3: { label: "🏫 五權樓 3F 東側操場走廊", x: 5.3, y: -12.0, bldg: "Bldg_Wuquan", floor: 3, yaw: Math.PI },
  wq5: { label: "🏫 五權樓 5F 六年級走廊", x: 5.3, y: -20.5, bldg: "Bldg_Wuquan", floor: 5, yaw: Math.PI },
  cq2: { label: "📚 重慶樓 2F 圖書室走廊", x: -55.0, y: -41.8, bldg: "Bldg_Chongqing", floor: 2, yaw: Math.PI / 2 },
  cq3: { label: "🏫 重慶樓 3F 南側走廊", x: -27.8, y: -41.8, bldg: "Bldg_Chongqing", floor: 3, yaw: Math.PI / 2 },
  court: { label: "🏀 重慶樓南側雙籃球場", x: -38.0, y: -47.0, yaw: Math.PI / 2 },
  track: { label: "🏃 操場與升旗司令台大道", x: 16.0, y: -13.8, yaw: Math.PI },
};

class InstBox {
  constructor(color, opts = {}) {
    this.color = color;
    this.items = [];
    this.opts = opts;
  }
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

function makeShirtTexture(side) {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d");

  // 白色純棉運動服底色＋細緻布面微陰影
  ctx.fillStyle = "#f5f6f3";
  ctx.fillRect(0, 0, 512, 512);
  const grad = ctx.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0, "rgba(255,255,255,0.22)");
  grad.addColorStop(0.84, "rgba(210,218,212,0.06)");
  grad.addColorStop(0.86, "rgba(180,190,184,0.28)");
  grad.addColorStop(1, "rgba(235,238,234,0.18)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 512, 512);

  // 下擺羅紋收口車線
  ctx.strokeStyle = "rgba(170,180,174,0.45)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(0, 444);
  ctx.lineTo(512, 444);
  ctx.stroke();

  if (side === "front") {
    // 領口：貼齊頂緣之翠綠羅紋圓領滾邊＋內側膚色鎖骨區
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(256, -4, 118, 84, 0, 0, Math.PI);
    ctx.fillStyle = "#007443";
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(256, -4, 88, 56, 0, 0, Math.PI);
    ctx.fillStyle = "#e8bc97";
    ctx.fill();
    ctx.restore();

    // 左胸重慶國小盾牌校徽（正面看位於畫面右側 x≈358，對應人物左胸 -Z 側）
    ctx.save();
    ctx.translate(358, 194);
    ctx.scale(1.24, 1.24);
    // 盾牌輪廓（上平下圓弧）
    const drawShield = (r) => {
      ctx.beginPath();
      ctx.moveTo(-42 * r, -44 * r);
      ctx.lineTo(42 * r, -44 * r);
      ctx.lineTo(42 * r, 4 * r);
      ctx.quadraticCurveTo(42 * r, 44 * r, 0, 50 * r);
      ctx.quadraticCurveTo(-42 * r, 44 * r, -42 * r, 4 * r);
      ctx.closePath();
    };
    drawShield(1);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.lineWidth = 6.5;
    ctx.strokeStyle = "#00693c";
    ctx.stroke();

    // 校徽中央：深綠＋翠綠分岔飛揚葉羽圖騰
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const leftStripes = [
      { col: "#044d2d", dx: -4, w: 7.5 },
      { col: "#0e8f56", dx: 2, w: 6.5 },
      { col: "#044d2d", dx: 8, w: 5.5 },
    ];
    for (const s of leftStripes) {
      ctx.strokeStyle = s.col;
      ctx.lineWidth = s.w;
      ctx.beginPath();
      ctx.moveTo(-4 + s.dx * 0.45, 14);
      ctx.quadraticCurveTo(-4 + s.dx * 0.45, -14, -22 + s.dx * 0.85, -24 + s.dx * 0.4);
      ctx.stroke();
    }
    const rightStripes = [
      { col: "#044d2d", dy: -6, w: 7 },
      { col: "#0e8f56", dy: 1, w: 6.5 },
      { col: "#044d2d", dy: 8, w: 5.8 },
    ];
    for (const s of rightStripes) {
      ctx.strokeStyle = s.col;
      ctx.lineWidth = s.w;
      ctx.beginPath();
      ctx.moveTo(4, 14 + s.dy * 0.35);
      ctx.quadraticCurveTo(8, -8 + s.dy * 0.6, 26, -15 + s.dy * 0.85);
      ctx.stroke();
    }
    // 校徽下方「重慶」字樣
    ctx.fillStyle = "#044d2d";
    ctx.font = "900 24px 'Microsoft JhengHei', 'Noto Sans TC', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("重慶", 0, 32);
    ctx.restore();
  } else if (side === "back") {
    // 背後淺圓領翠綠滾邊
    ctx.beginPath();
    ctx.ellipse(256, -4, 114, 38, 0, 0, Math.PI);
    ctx.fillStyle = "#007443";
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(256, -4, 86, 18, 0, 0, Math.PI);
    ctx.fillStyle = "#e8bc97";
    ctx.fill();
  }

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function makeShortsLegTexture(isOuterSide) {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 256;
  const ctx = c.getContext("2d");

  // 重慶夏季運動短褲鮮明飽滿翠綠（考量戶外日光與 ACES 色調映射稍微壓深飽和）
  ctx.fillStyle = "#00854e";
  ctx.fillRect(0, 0, 256, 256);

  // 細微褲管布褶層次
  const g = ctx.createLinearGradient(0, 0, 256, 0);
  g.addColorStop(0, "rgba(0,0,0,0.08)");
  g.addColorStop(0.5, "rgba(255,255,255,0.06)");
  g.addColorStop(1, "rgba(0,0,0,0.08)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);

  // 褲腳底緣：白色細滾線＋深丈青黑寬邊
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 226, 256, 7);
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 233, 256, 23);

  if (isOuterSide) {
    // 外側經典垂直深丈青條＋左右白細邊，底部呈弧形開衩接往褲腳黑邊
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(108, 0, 40, 233);
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(114, 0, 28, 256);

    // 側邊弧形開衩滾邊過渡（還原圖一短褲下襬圓弧白黑包邊）
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(0, 230);
    ctx.quadraticCurveTo(108, 228, 113, 198);
    ctx.moveTo(256, 230);
    ctx.quadraticCurveTo(148, 228, 143, 198);
    ctx.stroke();

    ctx.strokeStyle = "#0f172a";
    ctx.lineWidth = 18;
    ctx.beginPath();
    ctx.moveTo(0, 244);
    ctx.quadraticCurveTo(116, 240, 128, 214);
    ctx.quadraticCurveTo(140, 240, 256, 244);
    ctx.stroke();
  }

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function buildAvatar() {
  const g = new THREE.Group();
  const M = (c, r = 0.78) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const shirtWhite = M(0xf4f5f2, 0.84);
  const collarGreen = M(0x007443, 0.76);
  const shortsGreen = M(0x00854e, 0.74);
  const trimNavy = M(0x0f172a, 0.7);
  const trimWhite = M(0xffffff, 0.82);
  const skin = M(0xf2c7a3, 0.56);
  const hair = M(0x2a1f17, 0.9);
  const sockWhite = M(0xf8fafc, 0.85);
  const shoeUpper = M(0x1f2937, 0.72);
  const shoeSole = M(0xf1f5f9, 0.8);
  const dark = new THREE.MeshBasicMaterial({ color: 0x111827 });

  const box = (mat, sx, sy, sz, x, y, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
    m.position.set(x, y, z);
    return m;
  };

  // 上衣軀幹（正背面使用高解析 CanvasTexture：翠綠圓領＋左胸重慶盾牌校徽）
  const shirtFrontMat = new THREE.MeshStandardMaterial({ map: makeShirtTexture("front"), roughness: 0.84 });
  const shirtBackMat = new THREE.MeshStandardMaterial({ map: makeShirtTexture("back"), roughness: 0.84 });
  // BoxGeometry 6 面順序：[+X 正面, -X 背面, +Y 頂, -Y 底, +Z 右側, -Z 左側]
  const torsoMats = [shirtFrontMat, shirtBackMat, shirtWhite, shirtWhite, shirtWhite, shirtWhite];
  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.45, 0.38), torsoMats);
  torso.position.set(0, 1.0, 0);
  g.add(torso);

  // 膚色脖子＋肩領頂緣翠綠滾邊（貼齊衣領不與正面 U 領重疊成雙環）
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.068, 0.074, 0.09, 16), skin);
  neck.position.set(0, 1.25, 0);
  g.add(neck);
  const collarRing = new THREE.Mesh(new THREE.TorusGeometry(0.088, 0.016, 10, 22), collarGreen);
  collarRing.rotation.x = Math.PI / 2;
  collarRing.position.set(-0.015, 1.224, 0);
  g.add(collarRing);

  // 運動短褲鬆緊腰頭＋骨盆段（兩側帶深丈青滾白邊直條）
  g.add(box(shortsGreen, 0.235, 0.14, 0.365, 0, 0.72, 0));
  for (const sz of [0.184, -0.184]) {
    g.add(box(trimWhite, 0.056, 0.14, 0.006, 0, 0.72, sz));
    g.add(box(trimNavy, 0.036, 0.14, 0.01, 0, 0.72, sz));
  }

  // 頭部、頭髮與五官（劉海微抬避免遮蓋雙眼）
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.195, 18, 14), skin);
  head.position.set(0, 1.435, 0);
  g.add(head);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.208, 18, 10, 0, Math.PI * 2, 0, Math.PI * 0.49), hair);
  cap.position.set(-0.012, 1.455, 0);
  g.add(cap);
  g.add(box(dark, 0.02, 0.038, 0.036, 0.19, 1.405, 0.068));
  g.add(box(dark, 0.02, 0.038, 0.036, 0.19, 1.405, -0.068));
  g.add(box(M(0xd97766, 0.6), 0.015, 0.014, 0.046, 0.188, 1.335, 0));

  // 雙腿：翠綠寬短褲管（外側丈青白滾邊＋弧形褲腳）→ 膚色小腿 → 白襪 → 運動鞋
  const shortsOuterMat = new THREE.MeshStandardMaterial({ map: makeShortsLegTexture(true), roughness: 0.74 });
  const shortsPlainMat = new THREE.MeshStandardMaterial({ map: makeShortsLegTexture(false), roughness: 0.74 });
  const mkLeg = (pz) => {
    const pivot = new THREE.Group();
    pivot.position.set(0, 0.68, pz);
    // pz > 0 為右腿（外側在 +Z 面 index 4）；pz < 0 為左腿（外側在 -Z 面 index 5）
    const legMats = [
      shortsPlainMat,
      shortsPlainMat,
      shortsGreen,
      shortsGreen,
      pz > 0 ? shortsOuterMat : shortsPlainMat,
      pz < 0 ? shortsOuterMat : shortsPlainMat,
    ];
    const shortLeg = new THREE.Mesh(new THREE.BoxGeometry(0.185, 0.25, 0.178), legMats);
    shortLeg.position.set(0, -0.115, 0);
    pivot.add(shortLeg);

    // 露出之膚色小腿
    pivot.add(box(skin, 0.11, 0.24, 0.11, 0, -0.35, 0));
    // 白色運動短襪
    pivot.add(box(sockWhite, 0.118, 0.11, 0.118, 0, -0.525, 0));
    // 黑白國小運動鞋（白色鞋底＋深灰鞋面）
    pivot.add(box(shoeUpper, 0.19, 0.068, 0.132, 0.035, -0.612, 0));
    pivot.add(box(shoeSole, 0.205, 0.028, 0.14, 0.038, -0.66, 0));
    g.add(pivot);
    return pivot;
  };
  const legL = mkLeg(0.098);
  const legR = mkLeg(-0.098);

  // 雙臂：白色短袖 → 翠綠袖口滾邊 → 膚色前臂與小手
  const mkArm = (pz) => {
    const pivot = new THREE.Group();
    pivot.position.set(0, 1.19, pz);
    // 白色短袖
    pivot.add(box(shirtWhite, 0.14, 0.165, 0.135, 0, -0.075, 0));
    // 翠綠袖口羅紋滾邊
    pivot.add(box(collarGreen, 0.146, 0.03, 0.141, 0, -0.168, 0));
    // 膚色手臂與手掌
    pivot.add(box(skin, 0.092, 0.24, 0.092, 0, -0.30, 0));
    g.add(pivot);
    return pivot;
  };
  const armL = mkArm(0.255);
  const armR = mkArm(-0.255);

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
    buildings: {},
    colliders: [],
    groundMeshes: [],
    interior: null,
    doorsGroup: null,
    doors: [],
    doorPickMeshes: [],
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
  };

  const raycaster = new THREE.Raycaster();
  const rayDir = new THREE.Vector3(0, -1, 0);
  const rayOrg = new THREE.Vector3();
  const pickNdc = new THREE.Vector2();

  const el = {
    hud: () => document.getElementById("walkHud"),
    info: () => document.getElementById("walkInfo"),
    prompt: () => document.getElementById("walkPrompt"),
    fade: () => document.getElementById("walkFade"),
    crosshair: () => document.getElementById("walkCrosshair"),
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
        const res = await fetch(`./walk_data_campus.json?v=${buildHash || "2"}`);
        if (!res.ok) throw new Error(`walk data HTTP ${res.status}`);
        S.data = await res.json();
      } catch (e) {
        console.warn("walk_data_campus.json load failed", e);
        S.loading = null;
        return false;
      }
      S.buildings = S.data.buildings || {};
      const cols = [];
      for (const c of S.data.colliders || []) cols.push(c);
      // 尚未中空化之其他建物（運動中心）保留外框碰撞
      const gym = spec?.gym_and_skybridge?.gym;
      if (gym) cols.push([gym.x_min, gym.x_max, gym.y_min, gym.y_max, -5, 40]);
      S.colliders = cols;
      buildInterior();
      buildDoors();
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

  // ---------- 動態互動木拉門（可點擊／按 F 鍵滑動開關＋門板碰撞）----------
  function buildDoors() {
    const grp = new THREE.Group();
    grp.name = "WalkInteractiveDoors";
    const woodMat = new THREE.MeshStandardMaterial({ color: 0xb07d4f, roughness: 0.62, metalness: 0.05 });
    const trimMat = new THREE.MeshStandardMaterial({ color: 0x7a502d, roughness: 0.72 });
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0xbfe2ff,
      roughness: 0.15,
      metalness: 0.1,
      transparent: true,
      opacity: 0.42,
    });
    const handleMat = new THREE.MeshStandardMaterial({ color: 0xd1d5db, roughness: 0.25, metalness: 0.85 });

    // 共用幾何（標準門寬沿 X、厚度沿 Z、高度沿 Y；若門沿 Blender Y 軸則將群組旋轉 90°）
    // 採台灣小學外掛吊軌拉門：門寬 1.18m 完整覆蓋 1.10m 門洞，沿走廊外牆平滑橫移 1.08m 不插牆
    const topBarGeo = new THREE.BoxGeometry(1.18, 0.22, 0.055);
    const botPanelGeo = new THREE.BoxGeometry(1.18, 1.04, 0.055);
    const stileGeo = new THREE.BoxGeometry(0.24, 0.86, 0.055);
    const glassGeo = new THREE.BoxGeometry(0.7, 0.86, 0.022);
    const handleGeo = new THREE.BoxGeometry(0.035, 0.34, 0.11);
    const railGeo = new THREE.BoxGeometry(2.3, 0.07, 0.08);

    const roomsInfo = getRooms ? getRooms() : [];
    const bySpecKey = new Map();
    for (const r of roomsInfo) if (r.specKey) bySpecKey.set(r.specKey, r);

    S.doors = [];
    S.doorPickMeshes = [];

    for (const rm of S.data.rooms || []) {
      const dr = rm.door;
      if (!dr) continue;
      const idx = S.doors.length;
      const info = rm.key ? bySpecKey.get(rm.key) : null;
      const label = info ? info.short || info.name : rm.kind === "stair" ? "梯間" : "教室";
      const [nx, ny] = dr.normal || [0, -1];

      // 依樓層門洞實際淨空縮放門高，貼齊門框頂樑不穿模
      const bMeta = S.buildings[rm.bldg];
      const flMeta = bMeta?.floors?.find((f) => f.floor === rm.floor);
      const openH = flMeta ? Math.max(1.86, Math.min(2.14, flMeta.zf + 2.25 - dr.z)) : 2.0;

      const pivot = new THREE.Group();
      const leaf = new THREE.Group();

      // 門板構成（標準高度 0 .. 2.12m，再依 openH 精準縮放）
      const bot = new THREE.Mesh(botPanelGeo, woodMat);
      bot.position.set(0, 0.52, 0);
      const top = new THREE.Mesh(topBarGeo, woodMat);
      top.position.set(0, 2.01, 0);
      const stL = new THREE.Mesh(stileGeo, woodMat);
      stL.position.set(-0.47, 1.47, 0);
      const stR = new THREE.Mesh(stileGeo, woodMat);
      stR.position.set(0.47, 1.47, 0);
      const gl = new THREE.Mesh(glassGeo, glassMat);
      gl.position.set(0, 1.47, 0);
      const hd = new THREE.Mesh(handleGeo, handleMat);
      hd.position.set(dr.slide > 0 ? -0.46 : 0.46, 1.02, 0);

      for (const m of [bot, top, stL, stR, gl, hd]) {
        m.userData.doorIdx = idx;
        S.doorPickMeshes.push(m);
        leaf.add(m);
      }

      // 固定吊軌（外掛於門框走廊側上方，不隨門板移動）
      const rail = new THREE.Mesh(railGeo, trimMat);
      rail.position.set(dr.slide * 0.52, 2.13, 0);
      pivot.add(rail);
      pivot.add(leaf);
      pivot.scale.y = openH / 2.12;

      // 外推 0.19m 貼齊走廊牆面（避免門板開門滑動時插進旁邊實心牆體）
      pivot.position.copy(b2t(dr.x + nx * 0.19, dr.y + ny * 0.19, dr.z));
      // axis === "X"：門寬沿 Three.js +X；axis === "Y"：門寬沿 Three.js -Z（對應 Blender +Y，旋轉 +PI/2）
      if (dr.axis === "Y") {
        pivot.rotation.y = Math.PI / 2;
      }

      grp.add(pivot);
      S.doors.push({
        idx,
        bldg: rm.bldg,
        floor: rm.floor,
        key: rm.key,
        label,
        x: dr.x,
        y: dr.y,
        z: dr.z,
        axis: dr.axis,
        normal: dr.normal || [0, -1],
        width: dr.width || 1.1,
        slide: dr.slide || 1,
        leaf,
        open: false,
        anim: 0,
      });
    }

    grp.visible = false;
    scene.add(grp);
    S.doorsGroup = grp;
  }

  function setDoorOpen(door, isOpen, instant = false) {
    if (!door) return;
    door.open = Boolean(isOpen);
    if (instant) {
      door.anim = door.open ? 1 : 0;
      door.leaf.position.x = door.slide * 1.08 * door.anim;
    }
    requestRender(8);
  }

  function toggleDoor(door) {
    if (!door) return;
    setDoorOpen(door, !door.open, false);
  }

  function updateDoors(dt) {
    let anyMoving = false;
    for (const d of S.doors) {
      const tgt = d.open ? 1 : 0;
      if (Math.abs(d.anim - tgt) > 0.002) {
        const step = dt * 4.6;
        d.anim = d.anim < tgt ? Math.min(tgt, d.anim + step) : Math.max(tgt, d.anim - step);
        const eased = d.anim * d.anim * (3 - 2 * d.anim);
        d.leaf.position.x = d.slide * 1.08 * eased;
        anyMoving = true;
      }
    }
    if (anyMoving) requestRender(2);
  }

  function nearestDoor(maxDist = 2.6) {
    let best = null;
    let bestD = maxDist;
    for (const d of S.doors) {
      if (Math.abs(d.z - S.P.z) > 1.3) continue;
      const dist = Math.hypot(S.P.x - d.x, S.P.y - d.y);
      if (dist < bestD) {
        bestD = dist;
        best = d;
      }
    }
    return best;
  }

  function raycastDoor(clientX = null, clientY = null) {
    if (!S.doorPickMeshes.length) return null;
    if (document.pointerLockElement === canvas || clientX === null) {
      pickNdc.set(0, 0);
    } else {
      const rect = canvas.getBoundingClientRect();
      pickNdc.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      pickNdc.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    }
    raycaster.setFromCamera(pickNdc, camera);
    raycaster.near = 0.1;
    raycaster.far = 7.5;
    const hits = raycaster.intersectObjects(S.doorPickMeshes, false);
    if (!hits.length) return null;
    const idx = hits[0].object.userData.doorIdx;
    const door = S.doors[idx];
    if (!door) return null;
    // 限制玩家與門的實際步行距離 <= 5.5m 才允許開關，避免隔空誤觸對面棟
    if (Math.hypot(S.P.x - door.x, S.P.y - door.y) > 5.8 || Math.abs(S.P.z - door.z) > 2.2) return null;
    return door;
  }

  // ---------- 全校 4 棟動態室內家具（黑板、講桌、課桌椅、書架、辦公室、視聽中心）----------
  function buildInterior() {
    const wood = new InstBox(0xc79a62, { roughness: 0.7 });
    const metal = new InstBox(0x6b7280, { roughness: 0.5, metalness: 0.4 });
    const chair = new InstBox(0x3b82f6, { roughness: 0.6 });
    const seatRed = new InstBox(0xb91c1c, { roughness: 0.75 });
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

    for (const rm of S.data.rooms || []) {
      if (rm.kind !== "room") continue;
      const info = rm.key ? bySpecKey.get(rm.key) : null;
      const name = info?.name || "";
      const cat = info?.cat || "";
      const wx = rm.x1 - rm.x0;
      const wy = rm.y1 - rm.y0;
      if (wx < 1.8 || wy < 1.8) continue;

      const zf = rm.z_floor;
      const cx = 0.5 * (rm.x0 + rm.x1);
      const cy = 0.5 * (rm.y0 + rm.y1);
      const alongY = rm.bldg === "Bldg_Wuquan" || rm.bldg === "Bldg_Guanghe";

      let layout = "classroom";
      if (name.includes("廁") || name.includes("廚房")) layout = "empty";
      else if (name.includes("圖書")) layout = "library";
      else if (name.includes("視聽")) layout = "auditorium";
      else if (cat === "admin" || /辦公室|資料室|諮商|處|室/.test(name) && !/教室|唱遊/.test(name)) layout = "office";
      else if (name.includes("唱遊") || cat === "kinder") layout = "hall";
      if (layout === "empty") continue;

      if (layout === "auditorium") {
        // 505 視聽中心：西牆大銀幕＋多排紅色階梯式劇院座椅
        white.add(rm.x0 + 0.18, cy, zf + 1.85, 0.05, Math.min(5.2, wy * 0.68), 2.1);
        wood.add(rm.x0 + 1.1, cy, zf + 0.14, 1.8, wy - 0.8, 0.28);
        const rows = Math.max(2, Math.min(6, Math.floor((wx - 3.6) / 1.35)));
        const cols = Math.max(3, Math.min(8, Math.floor((wy - 1.6) / 0.8)));
        for (let r = 0; r < rows; r++) {
          const sx = rm.x0 + 3.1 + r * 1.35;
          for (let c = 0; c < cols; c++) {
            const sy = rm.y0 + 0.9 + (c * (wy - 1.8)) / Math.max(1, cols - 1);
            seatRed.add(sx, sy, zf + 0.44, 0.46, 0.5, 0.1);
            seatRed.add(sx + 0.2, sy, zf + 0.72, 0.1, 0.5, 0.52);
          }
        }
      } else if (layout === "library") {
        const nShelf = Math.max(2, Math.floor((wx - 0.8) / 1.15));
        for (let i = 0; i < nShelf; i++) {
          const x = rm.x0 + 0.7 + i * ((wx - 1.4) / Math.max(1, nShelf - 1));
          const y = rm.y1 - 0.45;
          shelf.add(x, y, zf + 0.95, 0.9, 0.34, 1.9);
          for (let k = 0; k < 4; k++) {
            books.add(x, y - 0.18, zf + 0.35 + k * 0.45, 0.82, 0.03, 0.34, 0, palette[pi++ % palette.length]);
          }
        }
        for (let t = 0; t < 2; t++) {
          const x = rm.x0 + wx * (0.3 + 0.4 * t);
          wood.add(x, cy - 0.6, zf + 0.74, 2.2, 1.0, 0.05);
          metal.add(x, cy - 0.6, zf + 0.37, 2.0, 0.8, 0.7);
          chair.add(x - 0.6, cy - 1.35, zf + 0.44, 0.4, 0.4, 0.04);
          chair.add(x + 0.6, cy - 1.35, zf + 0.44, 0.4, 0.4, 0.04);
        }
      } else if (layout === "office") {
        // 行政處室／辦公室：依房間長寬自動排辦公桌＋螢幕＋檔案櫃
        const nX = Math.max(1, Math.min(3, Math.floor((wx - 1.4) / 2.6)));
        const nY = Math.max(1, Math.min(3, Math.floor((wy - 1.4) / 2.2)));
        for (let i = 0; i < nX; i++) {
          const ox = nX === 1 ? cx : rm.x0 + 1.4 + (i * (wx - 2.8)) / (nX - 1);
          for (let j = 0; j < nY; j++) {
            const oy = nY === 1 ? cy : rm.y0 + 1.2 + (j * (wy - 2.4)) / (nY - 1);
            wood.add(ox, oy, zf + 0.74, 1.35, 0.68, 0.05);
            metal.add(ox, oy, zf + 0.37, 1.25, 0.58, 0.7);
            chair.add(ox, oy - 0.56, zf + 0.46, 0.44, 0.44, 0.05);
            white.add(ox, oy + 0.14, zf + 0.92, 0.38, 0.03, 0.26);
          }
        }
        shelf.add(rm.x0 + 0.35, cy, zf + 0.95, 0.4, Math.min(4.2, wy * 0.55), 1.9);
      } else if (!alongY) {
        // 沿 X 軸教室（和平樓、重慶樓）：黑板掛西側隔間牆，課桌面向西（yaw = 0）
        const bw = Math.min(4.4, wy * 0.55);
        board.add(rm.x0 + 0.14, cy, zf + 1.6, 0.03, bw, 1.15);
        wood.add(rm.x0 + 0.13, cy, zf + 1.6, 0.025, bw + 0.14, 1.29);
        wood.add(rm.x0 + 0.2, cy, zf + 0.98, 0.14, bw, 0.04);
        if (layout === "classroom") {
          wood.add(rm.x0 + 0.95, cy - 1.2, zf + 0.75, 0.6, 1.3, 0.05);
          wood.add(rm.x0 + 0.95, cy - 1.2, zf + 0.37, 0.5, 1.2, 0.7);
          const gx0 = rm.x0 + 2.3;
          const gx1 = rm.x1 - 1.0;
          const gy0 = rm.y0 + 0.95;
          const gy1 = rm.y1 - 0.95;
          const rows = Math.max(1, Math.min(4, Math.floor((gx1 - gx0) / 1.35) + 1));
          const colsN = Math.max(1, Math.min(5, Math.floor((gy1 - gy0) / 1.4) + 1));
          for (let i = 0; i < rows; i++) {
            const x = rows === 1 ? 0.5 * (gx0 + gx1) : gx0 + (i * (gx1 - gx0 - 0.8)) / (rows - 1);
            for (let j = 0; j < colsN; j++) {
              const y = colsN === 1 ? cy : gy0 + (j * (gy1 - gy0)) / (colsN - 1);
              addDesk(x, y, zf, 0);
            }
          }
          shelf.add(rm.x1 - 0.35, cy, zf + 0.5, 0.4, Math.min(5.2, wy * 0.65), 1.0);
        }
      } else {
        // 沿 Y 軸教室（五權樓、廣和樓）：黑板掛北側隔間牆，課桌面向北（yaw = -PI/2）
        const bw = Math.min(4.4, wx * 0.55);
        board.add(cx, rm.y1 - 0.14, zf + 1.6, bw, 0.03, 1.15);
        wood.add(cx, rm.y1 - 0.13, zf + 1.6, bw + 0.14, 0.025, 1.29);
        wood.add(cx, rm.y1 - 0.2, zf + 0.98, bw, 0.14, 0.04);
        if (layout === "classroom") {
          wood.add(cx - 1.2, rm.y1 - 0.95, zf + 0.75, 1.3, 0.6, 0.05);
          wood.add(cx - 1.2, rm.y1 - 0.95, zf + 0.37, 1.2, 0.5, 0.7);
          const gy1 = rm.y1 - 2.3;
          const gy0 = rm.y0 + 1.0;
          const gx0 = rm.x0 + 0.95;
          const gx1 = rm.x1 - 0.95;
          const rows = Math.max(1, Math.min(4, Math.floor((gy1 - gy0) / 1.35) + 1));
          const colsN = Math.max(1, Math.min(5, Math.floor((gx1 - gx0) / 1.4) + 1));
          for (let i = 0; i < rows; i++) {
            const y = rows === 1 ? 0.5 * (gy0 + gy1) : gy1 - (i * (gy1 - gy0 - 0.8)) / (rows - 1);
            for (let j = 0; j < colsN; j++) {
              const x = colsN === 1 ? cx : gx0 + (j * (gx1 - gx0)) / (colsN - 1);
              addDesk(x, y, zf, -Math.PI / 2);
            }
          }
          shelf.add(cx, rm.y0 + 0.35, zf + 0.5, Math.min(5.2, wx * 0.65), 0.4, 1.0);
        }
      }
      lamp.add(cx, cy, rm.z_ceil - 0.05, Math.min(1.5, wx * 0.25), 0.28, 0.04);
    }

    const group = new THREE.Group();
    group.name = "WalkInterior";
    for (const b of [wood, metal, chair, seatRed, board, white, books, lamp, shelf]) {
      const m = b.build();
      if (m) group.add(m);
    }
    group.visible = false;
    scene.add(group);
    S.interior = group;
  }

  // ---------- 碰撞（靜態牆＋關閉中之動態門板）與地面 ----------
  function resolveCollisions(x, y, z) {
    const zlo = z + 0.4;
    const zhi = z + 1.65;
    const r = BODY_R;
    const cols = S.colliders;

    const pushOutBox = (c0, c1, c2, c3) => {
      if (x < c0 - r || x > c1 + r || y < c2 - r || y > c3 + r) return false;
      const cx = x < c0 ? c0 : x > c1 ? c1 : x;
      const cy = y < c2 ? c2 : y > c3 ? c3 : y;
      const dx = x - cx;
      const dy = y - cy;
      const d2 = dx * dx + dy * dy;
      if (d2 >= r * r) return false;
      if (d2 > 1e-9) {
        const d = Math.sqrt(d2);
        const push = r - d;
        x += (dx / d) * push;
        y += (dy / d) * push;
      } else {
        const pl = x - c0 + r;
        const pr = c1 - x + r;
        const pb = y - c2 + r;
        const pt = c3 - y + r;
        const m = Math.min(pl, pr, pb, pt);
        if (m === pl) x = c0 - r;
        else if (m === pr) x = c1 + r;
        else if (m === pb) y = c2 - r;
        else y = c3 + r;
      }
      return true;
    };

    for (let iter = 0; iter < 3; iter++) {
      let moved = false;
      for (let i = 0; i < cols.length; i++) {
        const c = cols[i];
        if (c[5] <= zlo || c[4] >= zhi) continue;
        if (pushOutBox(c[0], c[1], c[2], c[3])) moved = true;
      }
      // 關閉中的教室木拉門動態碰撞（門打開超過 55% 即完全通行）
      for (let i = 0; i < S.doors.length; i++) {
        const d = S.doors[i];
        if (d.anim >= 0.55) continue;
        if (d.z + 2.15 <= zlo || d.z >= zhi) continue;
        const hw = d.width * 0.5;
        if (d.axis === "X") {
          if (pushOutBox(d.x - hw, d.x + hw, d.y - 0.1, d.y + 0.1)) moved = true;
        } else {
          if (pushOutBox(d.x - 0.1, d.x + 0.1, d.y - hw, d.y + hw)) moved = true;
        }
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
    rayOrg.set(x, z + 0.85, -y);
    raycaster.set(rayOrg, rayDir);
    raycaster.near = 0;
    raycaster.far = 2.6;
    const hits = raycaster.intersectObjects(S.groundMeshes, false);
    if (hits.length === 0) return null;
    return hits[0].point.y;
  }

  // ---------- 所在校舍／樓層／房間判定 ----------
  function currentBuilding(x = S.P.x, y = S.P.y) {
    for (const [id, meta] of Object.entries(S.buildings)) {
      const [bx0, bx1, by0, by1] = meta.bounds;
      if (x >= bx0 && x <= bx1 && y >= by0 && y <= by1) return { id, meta };
    }
    return null;
  }

  function floorForBuilding(meta, z) {
    if (!meta?.floors?.length) return null;
    let best = null;
    let bd = 1e9;
    for (const f of meta.floors) {
      const d = Math.abs(z - f.z_top);
      if (d < bd) {
        bd = d;
        best = f;
      }
    }
    return bd < 1.9 ? best : null;
  }

  function describeLocation() {
    const { x, y, z } = S.P;
    const curB = currentBuilding(x, y);
    if (!curB) return "校園戶外";
    const fl = floorForBuilding(curB.meta, z);
    if (!fl) return curB.meta.name;

    const infoList = getRooms ? getRooms() : [];
    for (const r of S.data.rooms || []) {
      if (r.bldg !== curB.id || r.floor !== fl.floor) continue;
      if (x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1) {
        if (r.key) {
          const info = infoList.find((i) => i.specKey === r.key);
          if (info) return `${curB.meta.name} ${fl.floor}F・${info.short || info.name}`;
        }
        if (r.kind === "stair") return `${curB.meta.name} ${fl.floor}F・梯間`;
        return `${curB.meta.name} ${fl.floor}F・室內空間`;
      }
    }
    return `${curB.meta.name} ${fl.floor}F・走廊`;
  }

  function nearStair() {
    const curB = currentBuilding();
    if (!curB) return null;
    for (const s of curB.meta.stairs || []) {
      if (Math.hypot(S.P.x - s.x, S.P.y - s.y) <= s.r) return { ...s, bldg: curB };
    }
    return null;
  }

  // ---------- 輸入與互動 ----------
  function isTyping() {
    const t = document.activeElement?.tagName;
    return t === "INPUT" || t === "TEXTAREA" || t === "SELECT";
  }

  function startRide(dir) {
    if (S.riding) return;
    const st = nearStair();
    if (!st) return;
    const fl = floorForBuilding(st.bldg.meta, S.P.z);
    if (!fl) return;
    const target = st.bldg.meta.floors.find((f) => f.floor === fl.floor + dir);
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
      label: `${st.bldg.meta.name} ${st.name} ${dir > 0 ? "上樓" : "下樓"} → ${target.floor}F`,
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
    } else if (code === "KeyF") {
      const dr = raycastDoor() || nearestDoor(2.7);
      if (dr) toggleDoor(dr);
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
  function onPointerLockChange() {
    const ch = el.crosshair();
    if (ch) ch.hidden = !(S.active && document.pointerLockElement === canvas);
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
    } else {
      const hoverDoor = raycastDoor(e.clientX, e.clientY);
      canvas.style.cursor = hoverDoor ? "pointer" : "";
    }
  }
  function onPointerUp(e) {
    if (!S.active) return;
    const wasClick = S.dragging && S.dragMoved < 5;
    S.dragging = false;
    if (!wasClick) return;

    // 優先檢測是否點擊到教室門板 -> 立即開／關門動畫！
    const hitDoor = raycastDoor(e.clientX, e.clientY);
    if (hitDoor) {
      toggleDoor(hitDoor);
      return;
    }
    // 否則進入滑鼠鎖定視角
    if (document.pointerLockElement !== canvas && canvas.requestPointerLock) {
      try {
        const p = canvas.requestPointerLock();
        if (p && p.catch) p.catch(() => {});
      } catch (_) {
        // pointer lock unavailable
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
    document.addEventListener("pointerlockchange", onPointerLockChange, sig);
    canvas.addEventListener("pointerdown", onPointerDown, sig);
    window.addEventListener("pointermove", onPointerMove, sig);
    window.addEventListener("pointerup", onPointerUp, sig);
    canvas.addEventListener("wheel", onWheel, { passive: false, signal: S.abort.signal });
  }
  function unbindInput() {
    S.abort?.abort();
    S.abort = null;
    S.keys.clear();
    canvas.style.cursor = "";
    const ch = el.crosshair();
    if (ch) ch.hidden = true;
    if (document.pointerLockElement === canvas && document.exitPointerLock) document.exitPointerLock();
  }

  // ---------- 傳送點與進入教室 ----------
  function placeAt(x, y, bldgId, floorNo, yaw) {
    S.P.x = x;
    S.P.y = y;
    let z = 0.45;
    const bMeta = bldgId ? S.buildings[bldgId] : null;
    if (floorNo && bMeta?.floors) {
      const f = bMeta.floors.find((fl) => fl.floor === floorNo);
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
    const sp = SPAWNS[key] || SPAWNS.cq2;
    placeAt(sp.x, sp.y, sp.bldg || null, sp.floor || 0, sp.yaw);
  }

  function roomEntry(roomRec) {
    if (!S.data || !roomRec) return null;
    const rm = (S.data.rooms || []).find((r) => r.key === roomRec.specKey);
    if (rm?.door) {
      const [nx, ny] = rm.door.normal || [0, -1];
      // 站在門外走廊 1.25m 處正面對教室門
      return {
        x: rm.door.x + nx * 1.25,
        y: rm.door.y + ny * 1.25,
        bldg: rm.bldg,
        floor: rm.floor,
        yaw: Math.atan2(-ny, -nx),
        doorKey: rm.key,
      };
    }
    const bMeta = S.buildings[roomRec.zoneId];
    const flNum = parseInt(String(roomRec.floor), 10);
    if (bMeta && !Number.isNaN(flNum)) {
      if (bMeta.corridor_axis === "X") {
        return { x: roomRec.pos?.[0] ?? -35, y: bMeta.corridor_val, bldg: roomRec.zoneId, floor: flNum, yaw: Math.PI / 2 };
      }
      return { x: bMeta.corridor_val, y: roomRec.pos?.[1] ?? 0, bldg: roomRec.zoneId, floor: flNum, yaw: Math.PI };
    }
    return null;
  }

  // ---------- 進出控制 ----------
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
    if (spec2?.x !== undefined) placeAt(spec2.x, spec2.y, spec2.bldg || null, spec2.floor || 0, spec2.yaw);
    else spawnByKey(spec2?.key || "cq2");

    if (S.interior) S.interior.visible = true;
    if (S.doorsGroup) S.doorsGroup.visible = true;
    if (S.light) S.light.visible = true;
    S.avatar.visible = S.view === "third";
    showHud(true);
    refreshViewBtn();
    const sel = el.spawn();
    if (sel && spec2?.key && SPAWNS[spec2.key]) sel.value = spec2.key;
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
    if (S.doorsGroup) S.doorsGroup.visible = false;
    if (S.avatar) S.avatar.visible = false;
    if (S.light) S.light.visible = false;
    controls.enabled = S.saved?.controlsEnabled ?? true;
    camera.near = S.saved?.near ?? 0.5;
    camera.updateProjectionMatrix();
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
        if (g - S.P.z > 0.55 || S.P.z - g > 1.2) return false;
        S.P.x = rx;
        S.P.y = ry;
        S.gz = g;
        return true;
      };
      if (attempt(nx, ny) || attempt(nx, S.P.y) || attempt(S.P.x, ny)) moving = 1;
      const target = Math.atan2(dy, dx);
      let diff = target - S.avatarYaw;
      while (diff > Math.PI) diff -= Math.PI * 2;
      while (diff < -Math.PI) diff += Math.PI * 2;
      S.avatarYaw += diff * Math.min(1, dt * 12);
      S.walkPhase += dt * (speed / WALK_SPEED) * 7.5;
    }
    S.moving += (moving - S.moving) * Math.min(1, dt * 10);
    if (S.gz > S.P.z) S.P.z = Math.min(S.gz, S.P.z + dt * 4.8);
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
      S.light.position.copy(b2t(S.P.x, S.P.y, S.P.z + 2.6));
    }
  }

  function updateHud(dt) {
    S.hudTimer -= dt;
    if (S.hudTimer > 0) return;
    S.hudTimer = 0.14;
    const info = el.info();
    if (info) info.textContent = `📍 ${describeLocation()}`;
    const pr = el.prompt();
    if (!pr) return;

    if (S.riding) {
      pr.hidden = false;
      pr.textContent = `🪜 ${S.riding.label}…`;
      return;
    }

    const parts = [];
    const dr = nearestDoor(2.6);
    if (dr) {
      parts.push(`🚪 ${dr.label}　<kbd>F</kbd> ${dr.open ? "關門" : "開門"}（或點擊門板）`);
    }
    const st = nearStair();
    if (st) {
      const fl = floorForBuilding(st.bldg.meta, S.P.z);
      if (fl) {
        const sp = [];
        if (st.bldg.meta.floors.some((f) => f.floor === fl.floor + 1)) sp.push(`<kbd>E</kbd> 上樓 ▲ ${fl.floor + 1}F`);
        if (st.bldg.meta.floors.some((f) => f.floor === fl.floor - 1)) sp.push(`<kbd>Q</kbd> 下樓 ▼ ${fl.floor - 1}F`);
        if (sp.length) parts.push(`🪜 ${st.name}　${sp.join("　")}`);
      }
    }

    if (parts.length > 0) {
      pr.hidden = false;
      pr.innerHTML = parts.join("　｜　");
    } else {
      pr.hidden = true;
    }
  }

  function update(dt) {
    if (!S.active) return;
    dt = Math.min(dt, 0.05);
    updateDoors(dt);
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
      sel.value = "cq2";
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
      return enter({ x: ent.x, y: ent.y, bldg: ent.bldg, floor: ent.floor, yaw: ent.yaw });
    },
    canWalkRoom(roomRec) {
      return Boolean(roomRec && WALKABLE_BLDGS.has(roomRec.zoneId));
    },
    get doorsCount() {
      return S.doors.length;
    },
  };
}
