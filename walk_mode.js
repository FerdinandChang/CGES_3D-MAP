/**
 * 重慶國小 3D 校園「全校四棟自由步行」模式（桌機）
 * - 涵蓋廣和樓、和平樓、五權樓、重慶樓全部中空教室（1F–5F）與戶外操場／球場／中庭
 * - 第一人稱／第三人稱紅書包小人切換（V）、WASD／方向鍵移動、Shift 跑步、滑鼠拖曳／PointerLock 轉向
 * - 互動對內開啟木門：點擊門板或走近按 F 鍵觸發合頁向室內旋轉 95° 開關動畫＋動態門板碰撞
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
  cq2: { label: "📚 重慶樓 2F 圖書室走廊", x: -58.288, y: -41.7, bldg: "Bldg_Chongqing", floor: 2, yaw: Math.PI / 2 },
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

const OUTFITS = [
  { key: "pe", btn: "👕 運動服" },
  { key: "boy", btn: "👔 男生制服" },
  { key: "girl", btn: "👗 女生制服" },
];
const OUTFIT_STORAGE_KEY = "cges_walk_outfit_v1";

function drawCgesCrest(ctx, x, y, scale = 1) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(scale, scale);
  ctx.beginPath();
  ctx.moveTo(-42, -44);
  ctx.lineTo(42, -44);
  ctx.lineTo(42, 4);
  ctx.quadraticCurveTo(42, 44, 0, 50);
  ctx.quadraticCurveTo(-42, 44, -42, 4);
  ctx.closePath();
  ctx.fillStyle = "#ffffff";
  ctx.fill();
  ctx.lineWidth = 6.5;
  ctx.strokeStyle = "#00693c";
  ctx.stroke();

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
  ctx.fillStyle = "#044d2d";
  ctx.font = "900 24px 'Microsoft JhengHei', 'Noto Sans TC', sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("重慶", 0, 32);
  ctx.restore();
}

function makeCanvasTex(canvas) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
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
    drawCgesCrest(ctx, 358, 194, 1.24);
  } else if (side === "back") {
    ctx.beginPath();
    ctx.ellipse(256, -4, 114, 38, 0, 0, Math.PI);
    ctx.fillStyle = "#007443";
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(256, -4, 86, 18, 0, 0, Math.PI);
    ctx.fillStyle = "#e8bc97";
    ctx.fill();
  }
  return makeCanvasTex(c);
}

function fillGingham(ctx, x, y, w, h) {
  ctx.save();
  ctx.fillStyle = "#f4f8ff";
  ctx.fillRect(x, y, w, h);
  const step = 12;
  ctx.fillStyle = "rgba(44, 92, 160, 0.36)";
  for (let gx = x; gx < x + w; gx += step * 2) ctx.fillRect(gx, y, step, h);
  for (let gy = y; gy < y + h; gy += step * 2) ctx.fillRect(x, gy, w, step);
  ctx.fillStyle = "rgba(28, 63, 122, 0.48)";
  for (let gx = x; gx < x + w; gx += step * 2) {
    for (let gy = y; gy < y + h; gy += step * 2) ctx.fillRect(gx, gy, step, step);
  }
  ctx.restore();
}

function makeBoyUniformShirtTexture(side) {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d");

  // 純白短袖襯衫底色
  ctx.fillStyle = "#f7f8fa";
  ctx.fillRect(0, 0, 512, 512);
  const g = ctx.createLinearGradient(0, 0, 0, 512);
  g.addColorStop(0, "rgba(255,255,255,0.2)");
  g.addColorStop(1, "rgba(180,195,215,0.16)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 512, 512);

  if (side === "front") {
    // 門襟與 4 顆鈕扣
    ctx.fillStyle = "rgba(220,228,238,0.55)";
    ctx.fillRect(241, 126, 30, 386);
    ctx.strokeStyle = "rgba(148,163,184,0.6)";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(241, 126);
    ctx.lineTo(241, 512);
    ctx.moveTo(271, 126);
    ctx.lineTo(271, 512);
    ctx.stroke();
    for (let i = 0; i < 4; i++) {
      const by = 188 + i * 86;
      ctx.beginPath();
      ctx.arc(256, by, 7.5, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#94a3b8";
      ctx.stroke();
    }

    // 領口 V 字膚色開襟
    ctx.beginPath();
    ctx.moveTo(192, 0);
    ctx.lineTo(320, 0);
    ctx.lineTo(256, 132);
    ctx.closePath();
    ctx.fillStyle = "#e8bc97";
    ctx.fill();

    // 左右藍白細格紋開領翻領（重慶國小男生夏季制服標誌特色）
    const drawLapel = (pts) => {
      ctx.save();
      ctx.beginPath();
      pts.forEach(([px, py], idx) => (idx === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)));
      ctx.closePath();
      ctx.clip();
      fillGingham(ctx, 90, 0, 340, 175);
      ctx.restore();
      ctx.beginPath();
      pts.forEach(([px, py], idx) => (idx === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)));
      ctx.closePath();
      ctx.strokeStyle = "#2b4d82";
      ctx.lineWidth = 3.5;
      ctx.stroke();
    };
    drawLapel([
      [192, 0],
      [118, 12],
      [148, 134],
      [252, 132],
    ]);
    drawLapel([
      [320, 0],
      [394, 12],
      [364, 134],
      [260, 132],
    ]);

    // 左胸白襯衫口袋＋上方重慶盾牌校徽
    ctx.strokeStyle = "rgba(148,163,184,0.75)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(316, 206);
    ctx.lineTo(426, 206);
    ctx.lineTo(426, 304);
    ctx.quadraticCurveTo(371, 326, 316, 304);
    ctx.closePath();
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    ctx.fill();
    ctx.stroke();
    drawCgesCrest(ctx, 371, 250, 0.82);
  } else if (side === "back") {
    // 背後藍白細格紋翻領
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(116, 0);
    ctx.lineTo(396, 0);
    ctx.lineTo(382, 74);
    ctx.quadraticCurveTo(256, 94, 130, 74);
    ctx.closePath();
    ctx.clip();
    fillGingham(ctx, 100, 0, 320, 100);
    ctx.restore();
    ctx.beginPath();
    ctx.moveTo(116, 0);
    ctx.lineTo(396, 0);
    ctx.lineTo(382, 74);
    ctx.quadraticCurveTo(256, 94, 130, 74);
    ctx.closePath();
    ctx.strokeStyle = "#2b4d82";
    ctx.lineWidth = 3.5;
    ctx.stroke();
  }
  return makeCanvasTex(c);
}

function makeGirlUniformTopTexture(side) {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d");

  // 深丈青連身吊帶背心裙上半身底色
  ctx.fillStyle = "#182644";
  ctx.fillRect(0, 0, 512, 512);
  // 細微立體修身剪裁線
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(120, 160);
  ctx.lineTo(132, 512);
  ctx.moveTo(392, 160);
  ctx.lineTo(380, 512);
  ctx.stroke();

  // 腰部拼接線
  ctx.fillStyle = "rgba(8,14,28,0.45)";
  ctx.fillRect(0, 468, 512, 14);

  if (side === "front") {
    // 背心 U 領內的白色襯衫區塊
    ctx.beginPath();
    ctx.ellipse(256, 12, 128, 124, 0, 0, Math.PI);
    ctx.fillStyle = "#f7f8fa";
    ctx.fill();

    // 頸口露出一點膚色
    ctx.beginPath();
    ctx.ellipse(256, -4, 72, 46, 0, 0, Math.PI);
    ctx.fillStyle = "#e8bc97";
    ctx.fill();

    // 經典圓弧白色娃娃領（Peter Pan Collar，左右兩瓣翻在深丈青背心上）
    const drawPeterPan = (sign) => {
      ctx.beginPath();
      ctx.moveTo(256, 48);
      ctx.quadraticCurveTo(256 + sign * 42, 144, 256 + sign * 144, 118);
      ctx.quadraticCurveTo(256 + sign * 194, 96, 256 + sign * 176, 8);
      ctx.lineTo(256 + sign * 70, 0);
      ctx.quadraticCurveTo(256 + sign * 56, 44, 256, 48);
      ctx.closePath();
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 3.5;
      ctx.stroke();
    };
    drawPeterPan(-1);
    drawPeterPan(1);

    // 左胸精緻小名牌條＋校徽
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(322, 178, 86, 28);
    ctx.strokeStyle = "#94a3b8";
    ctx.lineWidth = 2;
    ctx.strokeRect(322, 178, 86, 28);
    ctx.fillStyle = "#0b5c38";
    ctx.fillRect(330, 185, 16, 14);
    ctx.fillStyle = "#334155";
    ctx.fillRect(354, 189, 44, 6);
  } else if (side === "back") {
    // 背後圓弧純白後娃娃領
    ctx.beginPath();
    ctx.moveTo(96, 0);
    ctx.lineTo(416, 0);
    ctx.quadraticCurveTo(426, 88, 336, 94);
    ctx.quadraticCurveTo(278, 96, 256, 62);
    ctx.quadraticCurveTo(234, 96, 176, 94);
    ctx.quadraticCurveTo(86, 88, 96, 0);
    ctx.closePath();
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = "#cbd5e1";
    ctx.lineWidth = 3.5;
    ctx.stroke();
  }
  return makeCanvasTex(c);
}

function makePleatedSkirtTexture() {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 256;
  const ctx = c.getContext("2d");

  // 16 道深丈青立體百褶陰影
  const pleats = 16;
  const pw = 512 / pleats;
  for (let i = 0; i < pleats; i++) {
    const x0 = i * pw;
    const g = ctx.createLinearGradient(x0, 0, x0 + pw, 0);
    g.addColorStop(0.0, "#0e172a");
    g.addColorStop(0.22, "#1c2d50");
    g.addColorStop(0.68, "#253963");
    g.addColorStop(0.92, "#15223d");
    g.addColorStop(1.0, "#0c1424");
    ctx.fillStyle = g;
    ctx.fillRect(x0, 0, pw + 1, 256);
  }

  // 裙襬底端雙條淺色細飾線（還原照片女生制服裙底細節）
  ctx.fillStyle = "rgba(226, 232, 240, 0.52)";
  ctx.fillRect(0, 224, 512, 4);
  ctx.fillRect(0, 236, 512, 4);
  return makeCanvasTex(c);
}

function makeShortsLegTexture(isOuterSide) {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 256;
  const ctx = c.getContext("2d");

  // 重慶夏季運動短褲鮮明飽滿翠綠（考量戶外日光與 ACES 色調映射稍微壓深飽和）
  ctx.fillStyle = "#00854e";
  ctx.fillRect(0, 0, 256, 256);

  const g = ctx.createLinearGradient(0, 0, 256, 0);
  g.addColorStop(0, "rgba(0,0,0,0.08)");
  g.addColorStop(0.5, "rgba(255,255,255,0.06)");
  g.addColorStop(1, "rgba(0,0,0,0.08)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 226, 256, 7);
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 233, 256, 23);

  if (isOuterSide) {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(108, 0, 40, 233);
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(114, 0, 28, 256);

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
  return makeCanvasTex(c);
}

function buildAvatar(initialOutfit = "pe") {
  const g = new THREE.Group();
  const M = (c, r = 0.78) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const shirtWhite = M(0xf4f5f2, 0.84);
  const collarGreen = M(0x007443, 0.76);
  const shortsGreen = M(0x00854e, 0.74);
  const uniformNavy = M(0x182644, 0.76);
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

  // 三套上衣材質快取（BoxGeometry 6 面：[+X 正, -X 背, +Y 頂, -Y 底, +Z 右, -Z 左]）
  const peTorsoMats = [
    new THREE.MeshStandardMaterial({ map: makeShirtTexture("front"), roughness: 0.84 }),
    new THREE.MeshStandardMaterial({ map: makeShirtTexture("back"), roughness: 0.84 }),
    shirtWhite,
    shirtWhite,
    shirtWhite,
    shirtWhite,
  ];
  const boyTorsoMats = [
    new THREE.MeshStandardMaterial({ map: makeBoyUniformShirtTexture("front"), roughness: 0.82 }),
    new THREE.MeshStandardMaterial({ map: makeBoyUniformShirtTexture("back"), roughness: 0.82 }),
    shirtWhite,
    shirtWhite,
    shirtWhite,
    shirtWhite,
  ];
  const girlTorsoMats = [
    new THREE.MeshStandardMaterial({ map: makeGirlUniformTopTexture("front"), roughness: 0.8 }),
    new THREE.MeshStandardMaterial({ map: makeGirlUniformTopTexture("back"), roughness: 0.8 }),
    shirtWhite,
    uniformNavy,
    uniformNavy,
    uniformNavy,
  ];

  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.45, 0.38), peTorsoMats);
  torso.position.set(0, 1.0, 0);
  g.add(torso);

  // 膚色脖子＋運動服專屬翠綠圓領環
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.068, 0.074, 0.09, 16), skin);
  neck.position.set(0, 1.25, 0);
  g.add(neck);
  const collarRing = new THREE.Mesh(new THREE.TorusGeometry(0.088, 0.016, 10, 22), collarGreen);
  collarRing.rotation.x = Math.PI / 2;
  collarRing.position.set(-0.015, 1.224, 0);
  g.add(collarRing);

  // 骨盆／褲頭段＋運動服專屬側邊滾條
  const pelvis = box(shortsGreen, 0.235, 0.14, 0.365, 0, 0.72, 0);
  g.add(pelvis);
  const peHipTrims = new THREE.Group();
  for (const sz of [0.184, -0.184]) {
    peHipTrims.add(box(trimWhite, 0.056, 0.14, 0.006, 0, 0.72, sz));
    peHipTrims.add(box(trimNavy, 0.036, 0.14, 0.01, 0, 0.72, sz));
  }
  g.add(peHipTrims);

  // 女生制服專屬：立體 A 字深丈青百褶裙擺（橢圓截面自然貼合腰臀、底部露出膚色小腿）
  const skirtMat = new THREE.MeshStandardMaterial({
    map: makePleatedSkirtTexture(),
    roughness: 0.76,
    side: THREE.DoubleSide,
  });
  const skirt = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.285, 0.38, 28, 1, true), skirtMat);
  skirt.scale.set(0.84, 1, 1.1);
  skirt.position.set(0, 0.59, 0);
  g.add(skirt);

  // 頭部、短髮與五官
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.195, 18, 14), skin);
  head.position.set(0, 1.435, 0);
  g.add(head);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.208, 18, 10, 0, Math.PI * 2, 0, Math.PI * 0.49), hair);
  cap.position.set(-0.012, 1.455, 0);
  g.add(cap);
  g.add(box(dark, 0.02, 0.038, 0.036, 0.19, 1.405, 0.068));
  g.add(box(dark, 0.02, 0.038, 0.036, 0.19, 1.405, -0.068));
  g.add(box(M(0xd97766, 0.6), 0.015, 0.014, 0.046, 0.188, 1.335, 0));

  // 女生制服專屬：自然披肩長髮＋頭頂深藍蝴蝶結髮飾
  const girlHair = new THREE.Group();
  girlHair.add(box(hair, 0.11, 0.36, 0.35, -0.155, 1.33, 0));
  girlHair.add(box(hair, 0.11, 0.25, 0.065, -0.04, 1.36, 0.185));
  girlHair.add(box(hair, 0.11, 0.25, 0.065, -0.04, 1.36, -0.185));
  const bowMat = M(0x1e3a5f, 0.65);
  girlHair.add(box(bowMat, 0.04, 0.055, 0.15, -0.02, 1.66, 0));
  girlHair.add(box(trimWhite, 0.046, 0.035, 0.036, -0.02, 1.66, 0));
  g.add(girlHair);

  // 雙腿（短褲管材質支援一鍵切換：運動服翠綠滾邊／制服深丈青）
  const shortsOuterMat = new THREE.MeshStandardMaterial({ map: makeShortsLegTexture(true), roughness: 0.74 });
  const shortsPlainMat = new THREE.MeshStandardMaterial({ map: makeShortsLegTexture(false), roughness: 0.74 });
  const shortLegMeshes = [];
  const mkLeg = (pz) => {
    const pivot = new THREE.Group();
    pivot.position.set(0, 0.68, pz);
    const peLegMats = [
      shortsPlainMat,
      shortsPlainMat,
      shortsGreen,
      shortsGreen,
      pz > 0 ? shortsOuterMat : shortsPlainMat,
      pz < 0 ? shortsOuterMat : shortsPlainMat,
    ];
    const shortLeg = new THREE.Mesh(new THREE.BoxGeometry(0.185, 0.25, 0.178), peLegMats);
    shortLeg.position.set(0, -0.115, 0);
    shortLeg.userData.peLegMats = peLegMats;
    shortLegMeshes.push(shortLeg);
    pivot.add(shortLeg);

    pivot.add(box(skin, 0.11, 0.24, 0.11, 0, -0.35, 0));
    pivot.add(box(sockWhite, 0.118, 0.11, 0.118, 0, -0.525, 0));
    pivot.add(box(shoeUpper, 0.19, 0.068, 0.132, 0.035, -0.612, 0));
    pivot.add(box(shoeSole, 0.205, 0.028, 0.14, 0.038, -0.66, 0));
    g.add(pivot);
    return pivot;
  };
  const legL = mkLeg(0.098);
  const legR = mkLeg(-0.098);

  // 雙臂：白色短袖 → 袖口滾邊（運動服為翠綠、制服為白襯衫袖口）→ 膚色前臂
  const cuffMeshes = [];
  const mkArm = (pz) => {
    const pivot = new THREE.Group();
    pivot.position.set(0, 1.19, pz);
    pivot.add(box(shirtWhite, 0.14, 0.165, 0.135, 0, -0.075, 0));
    const cuff = box(collarGreen, 0.146, 0.03, 0.141, 0, -0.168, 0);
    cuffMeshes.push(cuff);
    pivot.add(cuff);
    pivot.add(box(skin, 0.092, 0.24, 0.092, 0, -0.30, 0));
    g.add(pivot);
    return pivot;
  };
  const armL = mkArm(0.255);
  const armR = mkArm(-0.255);

  const applyOutfit = (key) => {
    const k = OUTFITS.some((o) => o.key === key) ? key : "pe";
    torso.material = k === "pe" ? peTorsoMats : k === "boy" ? boyTorsoMats : girlTorsoMats;
    collarRing.visible = k === "pe";
    pelvis.material = k === "pe" ? shortsGreen : uniformNavy;
    peHipTrims.visible = k === "pe";
    skirt.visible = k === "girl";
    girlHair.visible = k === "girl";
    for (const m of shortLegMeshes) {
      m.material = k === "pe" ? m.userData.peLegMats : uniformNavy;
      // 男生制服短褲略長直筒；女生藏於百褶裙內稍窄避免擺腿穿裙
      m.scale.set(k === "girl" ? 0.88 : 1, k === "boy" ? 1.12 : 1, k === "girl" ? 0.88 : 1);
    }
    for (const c of cuffMeshes) {
      c.material = k === "pe" ? collarGreen : shirtWhite;
    }
  };
  applyOutfit(initialOutfit);

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
  root.userData = { body: g, legL, legR, armL, armR, blob, applyOutfit };
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
    outfit: (() => {
      try {
        const saved = localStorage.getItem(OUTFIT_STORAGE_KEY);
        return OUTFITS.some((o) => o.key === saved) ? saved : "pe";
      } catch (_) {
        return "pe";
      }
    })(),
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
    outfitBtn: () => document.getElementById("btnWalkOutfit"),
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

  // ---------- 動態互動教室門（依 607 班實景：淺原木實心平面門＋銀色水平壓把＋深灰金屬門框＋門頂鋁框氣窗）----------
  function buildDoors() {
    const grp = new THREE.Group();
    grp.name = "WalkInteractiveDoors";

    // 淺原木直紋平面實心木門貼圖（無門扇玻璃，還原重慶國小真實教室門）
    const woodDoorTex = (() => {
      const c = document.createElement("canvas");
      c.width = 256;
      c.height = 512;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#d9bc8e";
      ctx.fillRect(0, 0, 256, 512);
      for (let x = 0; x < 256; x += 4) {
        const tone = ((x * 29) % 19) - 9;
        ctx.fillStyle = tone > 0 ? `rgba(255,248,232,${tone * 0.015})` : `rgba(145,105,58,${-tone * 0.018})`;
        ctx.fillRect(x, 0, 4, 512);
      }
      ctx.strokeStyle = "rgba(130,96,54,0.22)";
      ctx.lineWidth = 4;
      ctx.strokeRect(4, 4, 248, 504);
      return makeCanvasTex(c);
    })();

    const woodMat = new THREE.MeshStandardMaterial({ map: woodDoorTex, roughness: 0.62, metalness: 0.04 });
    const metalFrameMat = new THREE.MeshStandardMaterial({ color: 0x6b7280, roughness: 0.48, metalness: 0.55 });
    const alumMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.35, metalness: 0.65 });
    const transomGlassMat = new THREE.MeshStandardMaterial({
      color: 0x94c5df,
      roughness: 0.16,
      metalness: 0.15,
      transparent: true,
      opacity: 0.55,
    });
    const handleMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.22, metalness: 0.88 });
    const hingeMat = new THREE.MeshStandardMaterial({ color: 0x4b5563, roughness: 0.4, metalness: 0.75 });

    // 共用幾何（門寬 1.06m 嚴密嵌入深灰金屬門框內，絕不外凸重疊相鄰窗戶）
    const doorW = 1.06;
    const panelGeo = new THREE.BoxGeometry(doorW, 2.1, 0.05);
    const latchPlateGeo = new THREE.BoxGeometry(0.048, 0.15, 0.072);
    const leverGeo = new THREE.BoxGeometry(0.135, 0.022, 0.14);
    const hingeGeo = new THREE.BoxGeometry(0.026, 0.13, 0.068);
    // 深灰金屬門框包邊（固定於 pivot 不隨門旋轉）
    const jambGeo = new THREE.BoxGeometry(0.04, 2.14, 0.31);
    const headerGeo = new THREE.BoxGeometry(1.16, 0.05, 0.31);
    // 門頂獨立銀鋁框透明氣窗（貼附門洞上方內外兩側，呈現教室門頂透光氣窗特徵）
    const transomFrameGeo = new THREE.BoxGeometry(1.14, 0.34, 0.34);
    const transomGlassGeo = new THREE.BoxGeometry(1.04, 0.25, 0.355);
    const transomBarGeo = new THREE.BoxGeometry(0.032, 0.26, 0.365);

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

      const bMeta = S.buildings[rm.bldg];
      const flMeta = bMeta?.floors?.find((f) => f.floor === rm.floor);
      const openH = flMeta ? Math.max(1.86, Math.min(2.14, flMeta.zf + 2.25 - dr.z)) : 2.0;

      // 統一局部座標：local +Z 永遠指向走廊、local -Z 永遠指向教室內部
      const theta = Math.atan2(nx, -ny);
      const slide = dr.slide || 1;
      const wallSideDot = dr.axis === "X" ? -slide * Math.cos(theta) : -slide * Math.sin(theta);
      const hingeSide = wallSideDot >= 0 ? 1 : -1;
      const leafOffsetX = -hingeSide * (doorW * 0.5);
      const openAngle = -hingeSide * (Math.PI * 0.53);

      const pivot = new THREE.Group();

      // 深灰金屬門框（覆蓋門洞左右與頂緣）
      const jL = new THREE.Mesh(jambGeo, metalFrameMat);
      jL.position.set(-0.56, 1.07, 0);
      const jR = new THREE.Mesh(jambGeo, metalFrameMat);
      jR.position.set(0.56, 1.07, 0);
      const hdr = new THREE.Mesh(headerGeo, metalFrameMat);
      hdr.position.set(0, 2.13, 0);
      pivot.add(jL, jR, hdr);

      // 門頂獨立銀鋁框透明氣窗
      const trFrame = new THREE.Mesh(transomFrameGeo, alumMat);
      trFrame.position.set(0, 2.33, 0);
      const trGlass = new THREE.Mesh(transomGlassGeo, transomGlassMat);
      trGlass.position.set(0, 2.33, 0);
      const trMid = new THREE.Mesh(transomBarGeo, alumMat);
      trMid.position.set(0, 2.33, 0);
      pivot.add(trFrame, trGlass, trMid);

      const hinge = new THREE.Group();
      hinge.position.set(hingeSide * (doorW * 0.5), 0, -0.09);

      const leaf = new THREE.Group();
      leaf.position.set(leafOffsetX, 0, 0);

      // 淺原木平面實心門扇（無門扇玻璃）
      const panel = new THREE.Mesh(panelGeo, woodMat);
      panel.position.set(0, 1.05, 0);

      // 銀色水平長條壓把（槓桿鎖）
      const handleX = -hingeSide * (doorW * 0.5 - 0.09);
      const latch = new THREE.Mesh(latchPlateGeo, handleMat);
      latch.position.set(handleX, 0.99, 0);
      const lever = new THREE.Mesh(leverGeo, handleMat);
      lever.position.set(handleX + hingeSide * 0.045, 1.0, 0);

      // 上下合頁鉸鏈
      const h1 = new THREE.Mesh(hingeGeo, hingeMat);
      h1.position.set(hingeSide * (doorW * 0.5 - 0.01), 0.38, -0.01);
      const h2 = new THREE.Mesh(hingeGeo, hingeMat);
      h2.position.set(hingeSide * (doorW * 0.5 - 0.01), 1.72, -0.01);

      for (const m of [panel, latch, lever, h1, h2]) {
        m.userData.doorIdx = idx;
        S.doorPickMeshes.push(m);
        leaf.add(m);
      }

      hinge.add(leaf);
      pivot.add(hinge);
      pivot.scale.y = openH / 2.12;
      pivot.position.copy(b2t(dr.x, dr.y, dr.z));
      pivot.rotation.y = theta;

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
        normal: [nx, ny],
        width: dr.width || 1.1,
        hinge,
        openAngle,
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
      door.hinge.rotation.y = door.openAngle * door.anim;
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
        const step = dt * 4.2;
        d.anim = d.anim < tgt ? Math.min(tgt, d.anim + step) : Math.max(tgt, d.anim - step);
        const eased = d.anim * d.anim * (3 - 2 * d.anim);
        d.hinge.rotation.y = d.openAngle * eased;
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

  // ---------- 全校 4 棟動態室內家具（依 607 班實景：電子黑板、莫蘭迪綠窗簾、原木課桌椅、雙管吊燈、藍粉黃置物櫃）----------
  function buildInterior() {
    const wood = new InstBox(0xcfa56e, { roughness: 0.68 });
    const woodDark = new InstBox(0xb88b52, { roughness: 0.74 });
    const yellowPeg = new InstBox(0xfacc15, { roughness: 0.5 });
    const hookGreen = new InstBox(0x22c55e, { roughness: 0.55 });
    const metal = new InstBox(0x6b7280, { roughness: 0.48, metalness: 0.42 });
    const silver = new InstBox(0xcfd6de, { roughness: 0.35, metalness: 0.55 });
    const darkMetal = new InstBox(0x262c36, { roughness: 0.52, metalness: 0.35 });
    const chair = new InstBox(0x3b82f6, { roughness: 0.6 });
    const seatRed = new InstBox(0xb91c1c, { roughness: 0.75 });
    const board = new InstBox(0x1e4a38, { roughness: 0.88 });
    const bulletinGreen = new InstBox(0x2c6648, { roughness: 0.84 });
    const white = new InstBox(0xf3f6fa, { roughness: 0.58 });
    const concrete = new InstBox(0xc2c8ce, { roughness: 0.82 });
    const curtainGreen = new InstBox(0x729484, { roughness: 0.88 });
    const curtainTie = new InstBox(0x557566, { roughness: 0.84 });
    const lockerBody = new InstBox(0xe6e8ec, { roughness: 0.72 });
    const lockerDoors = new InstBox(0xffffff, { perInstance: true, roughness: 0.58 });
    const lamp = new InstBox(0xffffff, { emissive: 0xf7fbff, roughness: 0.25 });
    const shelf = new InstBox(0xd9d2c3, { roughness: 0.7 });

    // 共用智慧電子觸控大螢幕貼圖（白框內嵌教學大屏）
    const smartScreenTex = (() => {
      const c = document.createElement("canvas");
      c.width = 512;
      c.height = 320;
      const ctx = c.getContext("2d");
      // 白色外框＋細黑內邊
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, 512, 320);
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(10, 10, 492, 286);
      // 柔和教學簡報畫面底色
      const bg = ctx.createLinearGradient(0, 16, 0, 290);
      bg.addColorStop(0, "#7dd3fc");
      bg.addColorStop(1, "#bae6fd");
      ctx.fillStyle = bg;
      ctx.fillRect(16, 16, 480, 260);
      // 頂部課程標題列
      ctx.fillStyle = "#0369a1";
      ctx.fillRect(16, 16, 480, 34);
      ctx.fillStyle = "#ffffff";
      ctx.font = "700 18px 'Microsoft JhengHei', sans-serif";
      ctx.fillText("重慶國小 智慧互動教室", 30, 39);
      // 簡報卡片圖解（5 張彩色教學卡片）
      const cards = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"];
      for (let i = 0; i < 5; i++) {
        const cx0 = 42 + i * 86;
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(cx0, 74, 72, 118);
        ctx.fillStyle = cards[i];
        ctx.fillRect(cx0 + 6, 80, 60, 52);
        ctx.fillStyle = "#94a3b8";
        ctx.fillRect(cx0 + 8, 142, 56, 8);
        ctx.fillRect(cx0 + 8, 156, 42, 8);
      }
      // 左下浮動工具條＋底部 Windows 工作列
      ctx.fillStyle = "#1d4ed8";
      ctx.fillRect(24, 206, 48, 56);
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(16, 276, 480, 14);
      // 白色下緣觸控快捷鍵圓點
      ctx.fillStyle = "#94a3b8";
      for (let i = 0; i < 5; i++) ctx.fillRect(210 + i * 20, 303, 10, 5);
      return makeCanvasTex(c);
    })();
    const smartScreenMat = new THREE.MeshStandardMaterial({
      map: smartScreenTex,
      roughness: 0.25,
      emissive: new THREE.Color(0x60a5fa),
      emissiveMap: smartScreenTex,
      emissiveIntensity: 0.42,
    });
    const smartScreenGeo = new THREE.PlaneGeometry(1, 1);

    const rooms = getRooms ? getRooms() : [];
    const bySpecKey = new Map();
    for (const r of rooms) if (r.specKey) bySpecKey.set(r.specKey, r);

    const lockerPalette = ["#fae17d", "#8ecae6", "#f7b2c4"]; // 鵝黃、粉藍、粉紅斜向循環

    // 全原木單人獨立課桌椅（還原 607 班實木桌面＋開放木抽屜＋3 根黃色擋書插梢＋原木條椅面與靠背）
    const addWoodenDesk = (x, y, z, yaw = 0, door = null) => {
      // 自動避開對內推開 95° 教室門扇之掃掠半徑，杜絕開門撞桌穿模
      if (door) {
        const [dnx, dny] = door.normal || [0, -1];
        const swX = door.x - dnx * 0.65;
        const swY = door.y - dny * 0.65;
        if (Math.hypot(x - swX, y - swY) < 1.18) return;
      }
      const c = Math.cos(yaw);
      const s = Math.sin(yaw);
      const rot = (dx, dy) => [x + dx * c - dy * s, y + dx * s + dy * c];
      // 原木桌面
      wood.add(x, y, z + 0.725, 0.48, 0.64, 0.032, yaw);
      // 開放木抽屜箱（左右側板＋底板＋靠講台前擋板）
      const [dbx, dby] = rot(0, 0);
      woodDark.add(dbx, dby, z + 0.59, 0.42, 0.56, 0.022, yaw);
      for (const sy of [-0.275, 0.275]) {
        const [sx, spy] = rot(0, sy);
        wood.add(sx, spy, z + 0.655, 0.42, 0.024, 0.115, yaw);
      }
      const [fx, fy] = rot(-0.2, 0);
      wood.add(fx, fy, z + 0.655, 0.022, 0.54, 0.11, yaw);
      // 抽屜口前緣 3 根亮黃色擋書圓柱插梢（607 班實景細節！）
      for (const py of [-0.14, 0, 0.14]) {
        const [px, ppy] = rot(0.2, py);
        yellowPeg.add(px, ppy, z + 0.645, 0.018, 0.018, 0.095, yaw);
      }
      // 側邊綠色書包小掛鉤
      const [hx, hy] = rot(0.02, 0.31);
      hookGreen.add(hx, hy, z + 0.64, 0.022, 0.045, 0.022, yaw);
      // 4 支方形原木桌腳＋下橫撐
      for (const [lx, ly] of [
        [-0.21, -0.28],
        [0.21, -0.28],
        [-0.21, 0.28],
        [0.21, 0.28],
      ]) {
        const [px, py] = rot(lx, ly);
        woodDark.add(px, py, z + 0.355, 0.04, 0.04, 0.71, yaw);
      }
      for (const ly of [-0.28, 0.28]) {
        const [px, py] = rot(0, ly);
        woodDark.add(px, py, z + 0.14, 0.4, 0.028, 0.032, yaw);
      }
      // 全原木單人椅（橫木條椅面＋雙橫條鏤空手提孔椅背＋原木四腳）
      const [cx, cy] = rot(0.6, 0);
      wood.add(cx, cy, z + 0.43, 0.39, 0.39, 0.032, yaw);
      // 上下雙橫木椅背（中間留長橢圓手提孔透空感）
      const [b1x, b1y] = rot(0.775, 0);
      wood.add(b1x, b1y, z + 0.74, 0.028, 0.38, 0.11, yaw);
      wood.add(b1x, b1y, z + 0.59, 0.028, 0.38, 0.08, yaw);
      for (const [lx, ly, hh] of [
        [0.44, -0.17, 0.42],
        [0.44, 0.17, 0.42],
        [0.77, -0.17, 0.79],
        [0.77, 0.17, 0.79],
      ]) {
        const [px, py] = rot(lx, ly);
        woodDark.add(px, py, z + hh * 0.5, 0.034, 0.034, hh, yaw);
      }
    };

    // 雙管懸吊式銀鋁槽教室日光燈（每盞附 2 根金屬吊桿）
    const addHangingLamp = (x, y, zc, yaw = 0, len = 1.24, drop = 0.44) => {
      const c = Math.cos(yaw);
      const s = Math.sin(yaw);
      const zLamp = zc - drop;
      silver.add(x, y, zLamp + 0.025, len, 0.18, 0.045, yaw);
      lamp.add(x, y, zLamp - 0.004, len - 0.06, 0.12, 0.018, yaw);
      for (const o of [-len * 0.36, len * 0.36]) {
        silver.add(x + o * c, y + o * s, zc - drop * 0.5, 0.016, 0.016, drop, 0);
      }
    };

    // 霧灰綠／莫蘭迪淺綠布質打褶對開窗簾（掛於窗間柱旁，避開門洞）
    const addGreenCurtain = (x, y, zf, zc, alongXWall) => {
      const topZ = zc - 0.16;
      const botZ = zf + 0.54;
      const midZ = zf + 1.28;
      const hUp = Math.max(0.4, topZ - midZ);
      const hDn = Math.max(0.35, midZ - botZ);
      const sxU = alongXWall ? 0.34 : 0.12;
      const syU = alongXWall ? 0.12 : 0.34;
      const sxT = alongXWall ? 0.22 : 0.13;
      const syT = alongXWall ? 0.13 : 0.22;
      const sxD = alongXWall ? 0.38 : 0.13;
      const syD = alongXWall ? 0.13 : 0.38;
      curtainGreen.add(x, y, midZ + hUp * 0.5, sxU, syU, hUp);
      curtainTie.add(x, y, midZ, sxT, syT, 0.08);
      curtainGreen.add(x, y, botZ + hDn * 0.5, sxD, syD, hDn);
    };

    const group = new THREE.Group();
    group.name = "WalkInterior";
    const libRooms = [];

    for (const rm of S.data.rooms || []) {
      if (rm.kind !== "room") continue;
      const info = rm.key ? bySpecKey.get(rm.key) : null;
      const name = info?.name || "";
      const cat = info?.cat || "";
      const wx = rm.x1 - rm.x0;
      const wy = rm.y1 - rm.y0;
      if (wx < 1.8 || wy < 1.8) continue;

      const zf = rm.z_floor;
      const zc = rm.z_ceil;
      const cx = 0.5 * (rm.x0 + rm.x1);
      const cy = 0.5 * (rm.y0 + rm.y1);
      const alongY = rm.bldg === "Bldg_Wuquan" || rm.bldg === "Bldg_Guanghe";

      let layout = "classroom";
      if (name.includes("廁") || name.includes("廚房")) layout = "empty";
      else if (name.includes("圖書")) layout = "library";
      else if (name.includes("視聽")) layout = "auditorium";
      else if (cat === "admin" || (/辦公室|資料室|諮商|處|室/.test(name) && !/教室|唱遊/.test(name))) layout = "office";
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
        lamp.add(cx, cy, zc - 0.05, Math.min(1.5, wx * 0.25), 0.28, 0.04);
      } else if (layout === "library") {
        // 交由專屬實景圖書館模組精細建置（音符矮書架、粉彩矮桌圓凳、悅讀重慶火車牆、雙白拱門與好書區）
        libRooms.push(rm);
        continue;
      } else if (layout === "office") {
        // 行政處室／辦公室：辦公桌＋螢幕＋檔案櫃＋懸吊日光燈
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
        addHangingLamp(cx, cy, zc, alongY ? Math.PI / 2 : 0, Math.min(1.4, (alongY ? wy : wx) * 0.35), 0.36);
      } else if (!alongY) {
        // ===== 沿 X 軸教室（和平樓、重慶樓）：西牆前電子黑板、東牆藍粉黃置物櫃、南北窗莫蘭迪綠窗簾 =====
        const bw = Math.min(4.9, wy * 0.66);
        const scrW = Math.min(2.05, bw * 0.43);
        const sideW = Math.max(0.5, (bw - scrW) * 0.5);
        // 1) 電子黑板：左右深綠黑板＋霧面銀鋁外框＋銀鋁粉筆槽＋中央嵌入式觸控大屏＋3 盞黑板專用吊燈＋左右廣播喇叭
        silver.add(rm.x0 + 0.125, cy, zf + 1.56, 0.035, bw + 0.12, 1.26);
        board.add(rm.x0 + 0.148, cy - (scrW + sideW) * 0.5, zf + 1.56, 0.025, sideW, 1.16);
        board.add(rm.x0 + 0.148, cy + (scrW + sideW) * 0.5, zf + 1.56, 0.025, sideW, 1.16);
        silver.add(rm.x0 + 0.2, cy, zf + 0.94, 0.12, bw + 0.12, 0.045);
        // 中央智慧電子螢幕（面向 +X）
        const scr = new THREE.Mesh(smartScreenGeo, smartScreenMat);
        scr.scale.set(scrW, 1.14, 1);
        scr.rotation.y = Math.PI / 2;
        scr.position.copy(b2t(rm.x0 + 0.17, cy, zf + 1.56));
        group.add(scr);
        // 黑板上方 3 盞灰銀色專用吊燈＋左右黑色教學廣播喇叭＋無線接收盒
        for (const oy of [-bw * 0.32, 0, bw * 0.32]) {
          addHangingLamp(rm.x0 + 0.68, cy + oy, zc, Math.PI / 2, Math.min(1.15, bw * 0.28), 0.48);
        }
        darkMetal.add(rm.x0 + 0.2, cy - bw * 0.52, zf + 2.42, 0.16, 0.2, 0.28);
        darkMetal.add(rm.x0 + 0.2, cy + bw * 0.52, zf + 2.42, 0.16, 0.2, 0.28);
        darkMetal.add(rm.x0 + 0.16, cy, zf + 2.26, 0.1, 0.28, 0.07);
        // 右側深綠葉飾公佈欄
        if (wy > bw + 1.4) {
          bulletinGreen.add(rm.x0 + 0.135, rm.y1 - 0.55, zf + 1.58, 0.03, 0.85, 1.05);
        }
        // 淺灰磨石子墊高講台＋前右角教師電腦桌
        concrete.add(rm.x0 + 0.58, cy, zf + 0.07, 0.96, Math.min(wy - 0.6, bw + 0.6), 0.14);

        if (layout === "classroom") {
          wood.add(rm.x0 + 1.18, rm.y1 - 0.9, zf + 0.76, 0.62, 1.15, 0.045);
          metal.add(rm.x0 + 1.18, rm.y1 - 0.9, zf + 0.38, 0.54, 1.05, 0.72);
          darkMetal.add(rm.x0 + 1.05, rm.y1 - 0.85, zf + 0.96, 0.04, 0.44, 0.3);

          // 3) 全原木實木單人課桌椅（整齊獨立排布）
          const gx0 = rm.x0 + 2.15;
          const gx1 = rm.x1 - 1.15;
          const gy0 = rm.y0 + 0.9;
          const gy1 = rm.y1 - 0.9;
          const rows = Math.max(1, Math.min(4, Math.floor((gx1 - gx0) / 1.32) + 1));
          const colsN = Math.max(1, Math.min(5, Math.floor((gy1 - gy0) / 1.25) + 1));
          for (let i = 0; i < rows; i++) {
            const x = rows === 1 ? 0.5 * (gx0 + gx1) : gx0 + (i * (gx1 - gx0 - 0.55)) / (rows - 1);
            for (let j = 0; j < colsN; j++) {
              const y = colsN === 1 ? cy : gy0 + (j * (gy1 - gy0)) / (colsN - 1);
              addWoodenDesk(x, y, zf, 0, rm.door);
            }
          }

          // 6) 後牆（東牆）藍・粉・黃 3x12 錯落格學生置物櫃＋上方綠色後公佈欄
          const lkCols = Math.max(6, Math.min(12, Math.floor((wy - 1.2) / 0.38)));
          const lkW = lkCols * 0.38;
          const lkX = rm.x1 - 0.31; // 避開東隔間牆 0.10m 厚
          darkMetal.add(lkX, cy, zf + 0.04, 0.34, lkW, 0.08); // 黑色踢腳底座
          lockerBody.add(lkX, cy, zf + 0.61, 0.38, lkW + 0.04, 1.06);
          const cellW = lkW / lkCols;
          for (let c = 0; c < lkCols; c++) {
            const ly = cy - lkW * 0.5 + (c + 0.5) * cellW;
            for (let r = 0; r < 3; r++) {
              const lz = zf + 0.25 + r * 0.345;
              const hex = lockerPalette[(c + r) % 3];
              lockerDoors.add(lkX - 0.195, ly, lz, 0.018, cellW - 0.025, 0.315, 0, hex);
              white.add(lkX - 0.208, ly, lz + 0.095, 0.008, 0.11, 0.042); // 白色號碼牌框
              white.add(lkX - 0.208, ly - cellW * 0.32, lz - 0.02, 0.01, 0.036, 0.055); // 白色內嵌把槽
            }
          }
          // 置物櫃上方綠色後公佈欄＋銀框
          silver.add(rm.x1 - 0.125, cy, zf + 1.88, 0.025, Math.min(wy - 1.4, lkW * 0.86), 1.04);
          bulletinGreen.add(rm.x1 - 0.14, cy, zf + 1.88, 0.02, Math.min(wy - 1.5, lkW * 0.84), 0.98);
        }

        // 2) 南北兩側窗戶之莫蘭迪霧灰綠布質打褶對開窗簾（自動避開門洞）＋外窗上冷氣機
        const drX = rm.door?.x ?? -999;
        const nCurt = Math.max(2, Math.floor(wx / 2.9));
        for (let k = 0; k <= nCurt; k++) {
          const cxK = rm.x0 + 0.45 + k * ((wx - 0.9) / nCurt);
          addGreenCurtain(cxK, rm.y1 - 0.08, zf, zc, true);
          if (Math.abs(cxK - drX) > 1.15) addGreenCurtain(cxK, rm.y0 + 0.08, zf, zc, true);
        }
        for (const acX of [rm.x0 + wx * 0.32, rm.x0 + wx * 0.68]) {
          white.add(acX, rm.y1 - 0.14, zc - 0.34, 0.95, 0.22, 0.28);
        }

        // 4) 天花板雙管懸吊式銀鋁槽日光燈（3 排 × 2~3 列）＋黑色圓網吸頂旋轉循環扇
        const nLx = Math.max(2, Math.min(3, Math.floor(wx / 2.4)));
        const nLy = Math.max(2, Math.min(3, Math.floor(wy / 2.2)));
        for (let ix = 0; ix < nLx; ix++) {
          const lx = rm.x0 + 1.5 + ix * ((wx - 2.6) / Math.max(1, nLx - 1));
          for (let iy = 0; iy < nLy; iy++) {
            const ly = rm.y0 + 1.25 + iy * ((wy - 2.5) / Math.max(1, nLy - 1));
            addHangingLamp(lx, ly, zc, 0, 1.18, 0.44);
          }
        }
        for (const fx of [rm.x0 + wx * 0.38, rm.x0 + wx * 0.7]) {
          for (const fy of [cy - wy * 0.2, cy + wy * 0.2]) {
            darkMetal.add(fx, fy, zc - 0.14, 0.44, 0.44, 0.08);
          }
        }
      } else {
        // ===== 沿 Y 軸教室（五權樓、廣和樓）：北牆前電子黑板、南牆藍粉黃置物櫃、東西窗莫蘭迪綠窗簾 =====
        const bw = Math.min(4.9, wx * 0.66);
        const scrW = Math.min(2.05, bw * 0.43);
        const sideW = Math.max(0.5, (bw - scrW) * 0.5);
        // 1) 電子黑板（掛北牆面向 -Y）
        silver.add(cx, rm.y1 - 0.125, zf + 1.56, bw + 0.12, 0.035, 1.26);
        board.add(cx - (scrW + sideW) * 0.5, rm.y1 - 0.148, zf + 1.56, sideW, 0.025, 1.16);
        board.add(cx + (scrW + sideW) * 0.5, rm.y1 - 0.148, zf + 1.56, sideW, 0.025, 1.16);
        silver.add(cx, rm.y1 - 0.2, zf + 0.94, bw + 0.12, 0.12, 0.045);
        const scr = new THREE.Mesh(smartScreenGeo, smartScreenMat);
        scr.scale.set(scrW, 1.14, 1);
        scr.rotation.y = 0; // PlaneGeometry 預設面向 Three.js +Z = Blender -Y（室內方向）
        scr.position.copy(b2t(cx, rm.y1 - 0.17, zf + 1.56));
        group.add(scr);
        for (const ox of [-bw * 0.32, 0, bw * 0.32]) {
          addHangingLamp(cx + ox, rm.y1 - 0.68, zc, 0, Math.min(1.15, bw * 0.28), 0.48);
        }
        darkMetal.add(cx - bw * 0.52, rm.y1 - 0.2, zf + 2.42, 0.2, 0.16, 0.28);
        darkMetal.add(cx + bw * 0.52, rm.y1 - 0.2, zf + 2.42, 0.2, 0.16, 0.28);
        darkMetal.add(cx, rm.y1 - 0.16, zf + 2.26, 0.28, 0.1, 0.07);
        if (wx > bw + 1.4) {
          bulletinGreen.add(rm.x1 - 0.55, rm.y1 - 0.135, zf + 1.58, 0.85, 0.03, 1.05);
        }
        concrete.add(cx, rm.y1 - 0.58, zf + 0.07, Math.min(wx - 0.6, bw + 0.6), 0.96, 0.14);

        if (layout === "classroom") {
          wood.add(rm.x1 - 0.9, rm.y1 - 1.18, zf + 0.76, 1.15, 0.62, 0.045);
          metal.add(rm.x1 - 0.9, rm.y1 - 1.18, zf + 0.38, 1.05, 0.54, 0.72);
          darkMetal.add(rm.x1 - 0.85, rm.y1 - 1.05, zf + 0.96, 0.44, 0.04, 0.3);

          // 3) 全原木實木單人課桌椅（面向北 yaw = -PI/2）
          const gy1 = rm.y1 - 2.15;
          const gy0 = rm.y0 + 1.15;
          const gx0 = rm.x0 + 0.9;
          const gx1 = rm.x1 - 0.9;
          const rows = Math.max(1, Math.min(4, Math.floor((gy1 - gy0) / 1.32) + 1));
          const colsN = Math.max(1, Math.min(5, Math.floor((gx1 - gx0) / 1.25) + 1));
          for (let i = 0; i < rows; i++) {
            const y = rows === 1 ? 0.5 * (gy0 + gy1) : gy1 - (i * (gy1 - gy0 - 0.55)) / (rows - 1);
            for (let j = 0; j < colsN; j++) {
              const x = colsN === 1 ? cx : gx0 + (j * (gx1 - gx0)) / (colsN - 1);
              addWoodenDesk(x, y, zf, -Math.PI / 2, rm.door);
            }
          }

          // 6) 後牆（南牆）藍・粉・黃 3x12 錯落格學生置物櫃＋上方綠色後公佈欄
          const lkCols = Math.max(6, Math.min(12, Math.floor((wx - 1.2) / 0.38)));
          const lkW = lkCols * 0.38;
          const lkY = rm.y0 + 0.31;
          darkMetal.add(cx, lkY, zf + 0.04, lkW, 0.34, 0.08);
          lockerBody.add(cx, lkY, zf + 0.61, lkW + 0.04, 0.38, 1.06);
          const cellW = lkW / lkCols;
          for (let c = 0; c < lkCols; c++) {
            const lx = cx - lkW * 0.5 + (c + 0.5) * cellW;
            for (let r = 0; r < 3; r++) {
              const lz = zf + 0.25 + r * 0.345;
              const hex = lockerPalette[(c + r) % 3];
              lockerDoors.add(lx, lkY + 0.195, lz, cellW - 0.025, 0.018, 0.315, 0, hex);
              white.add(lx, lkY + 0.208, lz + 0.095, 0.11, 0.008, 0.042);
              white.add(lx - cellW * 0.32, lkY + 0.208, lz - 0.02, 0.036, 0.01, 0.055);
            }
          }
          silver.add(cx, rm.y0 + 0.125, zf + 1.88, Math.min(wx - 1.4, lkW * 0.86), 0.025, 1.04);
          bulletinGreen.add(cx, rm.y0 + 0.14, zf + 1.88, Math.min(wx - 1.5, lkW * 0.84), 0.02, 0.98);
        }

        // 2) 東西兩側窗戶莫蘭迪綠打褶窗簾（自動避開門洞）＋冷氣機
        const drY = rm.door?.y ?? -999;
        const drOnEast = (rm.door?.normal?.[0] ?? 0) > 0;
        const nCurt = Math.max(2, Math.floor(wy / 2.9));
        for (let k = 0; k <= nCurt; k++) {
          const cyK = rm.y0 + 0.45 + k * ((wy - 0.9) / nCurt);
          if (!drOnEast || Math.abs(cyK - drY) > 1.15) addGreenCurtain(rm.x1 - 0.08, cyK, zf, zc, false);
          if (drOnEast || Math.abs(cyK - drY) > 1.15) addGreenCurtain(rm.x0 + 0.08, cyK, zf, zc, false);
        }
        const acXWall = drOnEast ? rm.x0 + 0.14 : rm.x1 - 0.14;
        for (const acY of [rm.y0 + wy * 0.32, rm.y0 + wy * 0.68]) {
          white.add(acXWall, acY, zc - 0.34, 0.22, 0.95, 0.28);
        }

        // 4) 天花板雙管懸吊式銀鋁槽日光燈＋黑色圓網吸頂旋轉循環扇
        const nLy = Math.max(2, Math.min(3, Math.floor(wy / 2.4)));
        const nLx = Math.max(2, Math.min(3, Math.floor(wx / 2.2)));
        for (let iy = 0; iy < nLy; iy++) {
          const ly = rm.y0 + 1.5 + iy * ((wy - 2.6) / Math.max(1, nLy - 1));
          for (let ix = 0; ix < nLx; ix++) {
            const lx = rm.x0 + 1.25 + ix * ((wx - 2.5) / Math.max(1, nLx - 1));
            addHangingLamp(lx, ly, zc, Math.PI / 2, 1.18, 0.44);
          }
        }
        for (const fy of [rm.y0 + wy * 0.38, rm.y0 + wy * 0.7]) {
          for (const fx of [cx - wx * 0.2, cx + wx * 0.2]) {
            darkMetal.add(fx, fy, zc - 0.14, 0.44, 0.44, 0.08);
          }
        }
      }
    }

    for (const b of [
      wood,
      woodDark,
      yellowPeg,
      hookGreen,
      metal,
      silver,
      darkMetal,
      chair,
      seatRed,
      board,
      bulletinGreen,
      white,
      concrete,
      curtainGreen,
      curtainTie,
      lockerBody,
      lockerDoors,
      lamp,
      shelf,
    ]) {
      const m = b.build();
      if (m) group.add(m);
    }
    for (const rm of libRooms) {
      buildLibraryInterior(rm, group);
    }
    group.visible = false;
    scene.add(group);
    S.interior = group;
  }

  // ---------- 重慶國小圖書館實景專屬渲染（依《用愛陪讀》相簿 1:1 還原）----------
  function buildLibraryInterior(rm, parentGroup) {
    const lib = new THREE.Group();
    lib.name = "WalkLibraryDetail";
    const { x0, x1, y0, y1, z_floor: zf, z_ceil: zc } = rm;
    const wx = x1 - x0;
    const wy = y1 - y0;
    const cx = 0.5 * (x0 + x1);
    const cy = 0.5 * (y0 + y1);
    const h = zc - zf;

    const M = (color, opts = {}) =>
      new THREE.MeshStandardMaterial({
        color,
        roughness: opts.roughness ?? 0.75,
        metalness: opts.metalness ?? 0.0,
        emissive: opts.emissive ? new THREE.Color(opts.emissive) : new THREE.Color(0x000000),
        emissiveIntensity: opts.emissiveIntensity ?? 0,
        side: opts.side ?? THREE.FrontSide,
      });

    const oakMat = M(0xd8ba8c, { roughness: 0.68 });
    const oakDarkMat = M(0xb89462, { roughness: 0.74 });
    const skyWallMat = M(0x95c8e3, { roughness: 0.85 });
    const whiteMat = M(0xf8fafc, { roughness: 0.65 });
    const mintPadMat = M(0x52c7b1, { roughness: 0.58 });
    const curtainMat = M(0xeae6dc, { roughness: 0.9 });
    const tealDeskMat = M(0x1b6e78, { roughness: 0.6 });
    const darkMat = M(0x1f2937, { roughness: 0.55, metalness: 0.25 });
    const purpleMat = M(0x7c4da8, { roughness: 0.62 });
    const yellowMat = M(0xfacc15, { roughness: 0.62 });
    const limeMat = M(0x84cc16, { roughness: 0.55 });
    const cartBlueMat = M(0x2563eb, { roughness: 0.45, metalness: 0.35 });
    const chromeMat = M(0xd1d5db, { roughness: 0.3, metalness: 0.75 });

    const addBox = (mat, bx, by, bz, sx, sy, sz, rotY = 0) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sz, sy), mat);
      m.position.copy(b2t(bx, by, bz));
      if (rotY) m.rotation.y = rotY;
      lib.add(m);
      return m;
    };

    const addCyl = (mat, bx, by, bz, rt, rb, ch, seg = 20) => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, ch, seg), mat);
      m.position.copy(b2t(bx, by, bz));
      lib.add(m);
      return m;
    };

    // 1. 淺灰白霧面無縫 PVC 地板（微帶柔和窗光反射）
    const floorTex = (() => {
      const c = document.createElement("canvas");
      c.width = 256;
      c.height = 256;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#eceff1";
      ctx.fillRect(0, 0, 256, 256);
      for (let i = 0; i < 420; i++) {
        ctx.fillStyle = i % 2 ? "rgba(255,255,255,0.22)" : "rgba(180,192,202,0.12)";
        ctx.fillRect((i * 53) % 256, (i * 97) % 256, 18, 6);
      }
      const t = makeCanvasTex(c);
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(4, 3);
      return t;
    })();
    const floorMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(wx - 0.04, wy - 0.04),
      new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.34, metalness: 0.04 })
    );
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.copy(b2t(cx, cy, zf + 0.012));
    lib.add(floorMesh);

    // 2. 白色輕鋼架天花板（T-Bar 格線）＋嵌入式 LED 格柵燈＋四向白色吸頂循環扇
    const ceilTex = (() => {
      const c = document.createElement("canvas");
      c.width = 512;
      c.height = 512;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#f4f6f8";
      ctx.fillRect(0, 0, 512, 512);
      ctx.strokeStyle = "#cfd8e3";
      ctx.lineWidth = 4;
      for (let i = 0; i <= 4; i++) {
        const p = i * 128;
        ctx.beginPath();
        ctx.moveTo(p, 0);
        ctx.lineTo(p, 512);
        ctx.moveTo(0, p);
        ctx.lineTo(512, p);
        ctx.stroke();
      }
      const t = makeCanvasTex(c);
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(5, 4);
      return t;
    })();
    const ceilMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(wx - 0.04, wy - 0.04),
      new THREE.MeshStandardMaterial({ map: ceilTex, roughness: 0.85 })
    );
    ceilMesh.rotation.x = Math.PI / 2;
    ceilMesh.position.copy(b2t(cx, cy, zc - 0.03));
    lib.add(ceilMesh);

    const ledMat = M(0xffffff, { emissive: 0xf8fbff, emissiveIntensity: 1.15, roughness: 0.25 });
    for (let ix = 0; ix < 4; ix++) {
      const lx = x0 + 1.6 + ix * ((wx - 3.2) / 3);
      for (let iy = 0; iy < 3; iy++) {
        const ly = y0 + 1.45 + iy * ((wy - 2.9) / 2);
        addBox(ledMat, lx, ly, zc - 0.045, 0.95, 0.48, 0.025);
      }
    }
    // 吸頂節能循環扇（3 台）
    for (let ix = 0; ix < 3; ix++) {
      const fx = x0 + 2.8 + ix * ((wx - 5.6) / 2);
      addBox(whiteMat, fx, cy, zc - 0.06, 0.62, 0.62, 0.05);
      addCyl(M(0xe2e8f0, { roughness: 0.5 }), fx, cy, zc - 0.095, 0.24, 0.24, 0.02, 18);
    }

    // 3. 柔和淺天藍牆面（避開東側 0.1m 隔間牆厚）、北側窗間天藍結構柱、沙漏形綁帶落地窗簾、靠窗薄荷綠矮櫃與冷氣
    addBox(skyWallMat, x0 + 0.03, cy, zf + h * 0.5, 0.05, wy - 0.08, h - 0.06);
    // 東牆隔間內表面在 x1 - 0.10，將天藍飾牆內移至 x1 - 0.125 避免被隔間牆遮蔽
    addBox(skyWallMat, x1 - 0.125, cy, zf + h * 0.5, 0.04, wy - 0.08, h - 0.06);
    // 北牆下緣窗台與頂部樑刷天藍（避開 -63.45..-57.13 採光大窗玻璃）
    addBox(skyWallMat, cx, y1 - 0.03, zf + 0.62, wx - 0.24, 0.05, 1.24);
    addBox(skyWallMat, cx, y1 - 0.03, zc - 0.24, wx - 0.24, 0.05, 0.44);
    // 北側實牆窗間結構柱（精準避開窗洞）與沙漏形束帶米白落地窗簾（底部收於坐墊上方不穿模）
    for (const px of [x0 + 0.35, x0 + 1.55, x1 - 1.85, x1 - 0.35]) {
      addBox(skyWallMat, px, y1 - 0.14, zf + h * 0.5, 0.46, 0.24, h - 0.06);
    }
    for (const curX of [x0 + 1.98, x1 - 2.3]) {
      // 上半垂褶（上寬下收束）＋綁帶環＋下半垂褶（上束下展，底緣止於 zf + 0.51 不穿入坐墊）
      addCyl(curtainMat, curX, y1 - 0.15, zf + 2.02, 0.16, 0.075, 1.32, 14);
      addCyl(M(0xcbd5e1), curX, y1 - 0.15, zf + 1.34, 0.084, 0.084, 0.065, 14);
      addCyl(curtainMat, curX, y1 - 0.15, zf + 0.91, 0.075, 0.155, 0.8, 14);
    }
    // 靠北窗長條原木矮櫃＋薄荷綠皮質軟墊（Window Bench，完整貼齊北牆不被柱或窗簾穿過）
    for (const [bx0, bx1] of [
      [x0 + 1.85, x1 - 2.15],
      [x1 - 1.55, x1 - 0.6],
    ]) {
      const bw = bx1 - bx0;
      const bc = 0.5 * (bx0 + bx1);
      addBox(oakMat, bc, y1 - 0.27, zf + 0.22, bw, 0.48, 0.42);
      addBox(mintPadMat, bc, y1 - 0.27, zf + 0.46, bw - 0.04, 0.44, 0.07);
    }
    // 壁掛式白色分離式冷氣室內機（2 台）
    for (const ax of [cx - 2.3, cx + 1.6]) {
      addBox(whiteMat, ax, y1 - 0.14, zf + 2.66, 1.05, 0.24, 0.28);
      addBox(M(0xdbeafe), ax, y1 - 0.265, zf + 2.6, 0.92, 0.02, 0.05);
    }

    // 4. 西牆：「悅讀重慶」繪本小火車彩繪主題牆 ＋ 亮黃／橘／紅跳色 5 層靠牆高書架
    const muralTex = (() => {
      const c = document.createElement("canvas");
      c.width = 1024;
      c.height = 320;
      const ctx = c.getContext("2d");
      // 藍天白雲綠草地背景
      const sky = ctx.createLinearGradient(0, 0, 0, 260);
      sky.addColorStop(0, "#7ec4ea");
      sky.addColorStop(1, "#bae4f8");
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, 1024, 320);
      // 白雲
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      for (const [ux, uy, r] of [
        [290, 68, 28],
        [322, 62, 34],
        [356, 72, 24],
        [680, 58, 30],
        [716, 54, 36],
        [752, 66, 26],
        [910, 82, 26],
      ]) {
        ctx.beginPath();
        ctx.arc(ux, uy, r, 0, Math.PI * 2);
        ctx.fill();
      }
      // 翠綠波浪山丘草地
      ctx.fillStyle = "#65c466";
      ctx.beginPath();
      ctx.moveTo(0, 320);
      ctx.lineTo(0, 248);
      ctx.quadraticCurveTo(240, 210, 512, 246);
      ctx.quadraticCurveTo(780, 282, 1024, 232);
      ctx.lineTo(1024, 320);
      ctx.closePath();
      ctx.fill();

      // 彩色立體大字「悅讀重慶」（錯落活潑排布）
      const titleChars = [
        { ch: "悅", x: 112, y: 122, bg: "#ef4444" },
        { ch: "讀", x: 186, y: 146, bg: "#f59e0b" },
        { ch: "重", x: 260, y: 118, bg: "#10b981" },
        { ch: "慶", x: 334, y: 142, bg: "#3b82f6" },
      ];
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "900 46px 'Microsoft JhengHei', 'Noto Sans TC', sans-serif";
      for (const it of titleChars) {
        ctx.beginPath();
        ctx.arc(it.x, it.y, 35, 0, Math.PI * 2);
        ctx.fillStyle = it.bg;
        ctx.fill();
        ctx.lineWidth = 4;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();
        ctx.fillStyle = "#ffffff";
        ctx.fillText(it.ch, it.x, it.y + 3);
      }

      // 紅橘色系繪本小火車（車頭＋兩節載滿繪本與小動物的車廂）
      const drawWheel = (wx0, wy0) => {
        ctx.beginPath();
        ctx.arc(wx0, wy0, 22, 0, Math.PI * 2);
        ctx.fillStyle = "#334155";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(wx0, wy0, 10, 0, Math.PI * 2);
        ctx.fillStyle = "#facc15";
        ctx.fill();
      };
      // 車頭（紅橘色）
      ctx.fillStyle = "#ea580c";
      ctx.fillRect(420, 152, 130, 92);
      ctx.fillStyle = "#dc2626";
      ctx.fillRect(496, 106, 62, 138);
      ctx.fillStyle = "#fde047";
      ctx.fillRect(438, 114, 24, 42);
      ctx.fillStyle = "#e0f2fe";
      ctx.fillRect(508, 124, 38, 42);
      // 煙霧愛心/白雲
      ctx.fillStyle = "rgba(255,255,255,0.88)";
      for (const [sx, sy, sr] of [
        [446, 94, 14],
        [466, 72, 18],
        [496, 56, 20],
      ]) {
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI * 2);
        ctx.fill();
      }
      drawWheel(450, 248);
      drawWheel(528, 248);

      // 第一節橘黃車廂
      ctx.fillStyle = "#f97316";
      ctx.fillRect(584, 156, 160, 88);
      ctx.fillStyle = "#fef08a";
      ctx.fillRect(600, 172, 128, 46);
      // 車窗小熊剪影＋彩書
      ctx.fillStyle = "#92400e";
      ctx.beginPath();
      ctx.arc(642, 198, 17, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#22c55e";
      ctx.fillRect(680, 182, 34, 32);
      drawWheel(620, 248);
      drawWheel(708, 248);

      // 第二節粉紅／天空藍繪本車廂
      ctx.fillStyle = "#ef4444";
      ctx.fillRect(772, 156, 174, 88);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(788, 172, 142, 46);
      ctx.fillStyle = "#3b82f6";
      ctx.fillRect(804, 180, 32, 34);
      ctx.fillStyle = "#facc15";
      ctx.fillRect(844, 182, 32, 32);
      ctx.fillStyle = "#ec4899";
      ctx.fillRect(884, 180, 32, 34);
      drawWheel(812, 248);
      drawWheel(908, 248);
      return makeCanvasTex(c);
    })();
    const muralPlane = new THREE.Mesh(
      new THREE.PlaneGeometry(wy - 0.9, 1.28),
      new THREE.MeshStandardMaterial({ map: muralTex, roughness: 0.78 })
    );
    muralPlane.rotation.y = Math.PI / 2;
    muralPlane.position.copy(b2t(x0 + 0.065, cy, zf + 2.34));
    lib.add(muralPlane);

    // 彩色書脊共用 InstBox（讓全圖書館書架塞滿高矮錯落的五彩繪本！）
    const libBooks = new InstBox(0xffffff, { perInstance: true, roughness: 0.78 });
    const bookColors = [
      "#ef4444",
      "#f97316",
      "#facc15",
      "#22c55e",
      "#14b8a6",
      "#3b82f6",
      "#8b5cf6",
      "#ec4899",
      "#f43f5e",
      "#06b6d4",
      "#84cc16",
      "#f59e0b",
    ];
    let bIdx = 0;
    const fillBookRowX = (xa, xb, y, zBase, depth = 0.2, hMin = 0.19, hMax = 0.28) => {
      for (let x = xa + 0.06; x < xb - 0.06; x += 0.055) {
        const bh = hMin + ((bIdx * 37) % 100) / 100 * (hMax - hMin);
        const bw = 0.036 + ((bIdx * 19) % 10) * 0.0014;
        libBooks.add(x, y, zBase + bh * 0.5, bw, depth, bh, 0, bookColors[bIdx++ % bookColors.length]);
      }
    };
    const fillBookRowY = (x, ya, yb, zBase, depth = 0.2, hMin = 0.19, hMax = 0.28) => {
      for (let y = ya + 0.06; y < yb - 0.06; y += 0.055) {
        const bh = hMin + ((bIdx * 41) % 100) / 100 * (hMax - hMin);
        const bw = 0.036 + ((bIdx * 23) % 10) * 0.0014;
        libBooks.add(x, y, zBase + bh * 0.5, depth, bw, bh, 0, bookColors[bIdx++ % bookColors.length]);
      }
    };

    // 西牆下方：5 層跳色靠牆高書架（亮黃／橘／紅跳色立板）
    const accentMats = [M(0xfacc15), M(0xfb923c), M(0xef4444), M(0xfacc15), M(0xfb923c), M(0xef4444)];
    const wShelfY0 = y0 + 0.6;
    const wShelfY1 = y1 - 0.7;
    const wShelfN = 5;
    const wBay = (wShelfY1 - wShelfY0) / wShelfN;
    addBox(oakMat, x0 + 0.09, 0.5 * (wShelfY0 + wShelfY1), zf + 0.84, 0.04, wShelfY1 - wShelfY0, 1.66);
    for (let k = 0; k <= 4; k++) {
      addBox(oakMat, x0 + 0.25, 0.5 * (wShelfY0 + wShelfY1), zf + 0.08 + k * 0.39, 0.34, wShelfY1 - wShelfY0, 0.035);
    }
    for (let i = 0; i <= wShelfN; i++) {
      const py = wShelfY0 + i * wBay;
      addBox(accentMats[i % accentMats.length], x0 + 0.26, py, zf + 0.84, 0.36, 0.045, 1.68);
      if (i < wShelfN) {
        for (let lv = 0; lv < 4; lv++) {
          fillBookRowY(x0 + 0.29, py + 0.05, py + wBay - 0.05, zf + 0.1 + lv * 0.39, 0.22);
        }
      }
    }

    // 5. 全場視覺核心：中央「音符鏤空欄板」淺原木雙面島型矮書架
    const islX0 = x0 + 1.85;
    const islX1 = x1 - 2.35;
    const islLen = islX1 - islX0;
    const islCx = 0.5 * (islX0 + islX1);
    const islY = cy + 0.05;
    // 矮書架本體（高 0.76m，雙面 2 層滿載繪本）
    addBox(oakMat, islCx, islY, zf + 0.05, islLen, 0.62, 0.06);
    addBox(oakMat, islCx, islY, zf + 0.4, islLen, 0.6, 0.035);
    addBox(oakMat, islCx, islY, zf + 0.76, islLen + 0.04, 0.66, 0.04);
    addBox(oakDarkMat, islCx, islY, zf + 0.4, islLen - 0.04, 0.04, 0.7);
    const islBays = 6;
    const islBayW = islLen / islBays;
    for (let i = 0; i <= islBays; i++) {
      const px = islX0 + i * islBayW;
      addBox(oakMat, px, islY, zf + 0.4, 0.04, 0.62, 0.74);
      if (i < islBays) {
        for (const sideY of [islY - 0.18, islY + 0.18]) {
          fillBookRowX(px + 0.04, px + islBayW - 0.04, sideY, zf + 0.08, 0.22, 0.2, 0.28);
          fillBookRowX(px + 0.04, px + islBayW - 0.04, sideY, zf + 0.42, 0.22, 0.2, 0.28);
        }
      }
    }
    // 頂部經典「圓角矩形鏤空音符欄板」（淺原木框＋半透明壓克力＋彩色立體音符與高音譜記號）
    const noteTex = (() => {
      const c = document.createElement("canvas");
      c.width = 1024;
      c.height = 160;
      const ctx = c.getContext("2d");
      // 淺原木外框面板
      ctx.fillStyle = "#d9bc8e";
      ctx.fillRect(0, 0, 1024, 160);
      const panels = 6;
      const pw = 1024 / panels;
      const noteCols = ["#dc2626", "#f59e0b", "#1e293b", "#2563eb", "#16a34a", "#ea580c", "#7c3aed"];
      const drawNote = (nx, ny, col, kind) => {
        ctx.save();
        ctx.fillStyle = col;
        ctx.strokeStyle = col;
        ctx.lineWidth = 6;
        ctx.lineCap = "round";
        if (kind === 0) {
          // 單八分音符
          ctx.beginPath();
          ctx.ellipse(nx, ny + 26, 12, 9, -0.35, 0, Math.PI * 2);
          ctx.fill();
          ctx.beginPath();
          ctx.moveTo(nx + 9, ny + 24);
          ctx.lineTo(nx + 9, ny - 24);
          ctx.quadraticCurveTo(nx + 28, ny - 12, nx + 22, ny + 4);
          ctx.stroke();
        } else if (kind === 1) {
          // 雙八分連音符
          for (const ox of [-14, 14]) {
            ctx.beginPath();
            ctx.ellipse(nx + ox, ny + 26, 10, 8, -0.35, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(nx + ox + 8, ny + 24);
            ctx.lineTo(nx + ox + 8, ny - 18);
            ctx.stroke();
          }
          ctx.lineWidth = 8;
          ctx.beginPath();
          ctx.moveTo(nx - 6, ny - 18);
          ctx.lineTo(nx + 22, ny - 25);
          ctx.stroke();
        } else {
          // 高音譜記號風格符號
          ctx.font = "900 72px Georgia, serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("𝄞", nx, ny + 4);
        }
        ctx.restore();
      };
      for (let i = 0; i < panels; i++) {
        const rx = i * pw + 14;
        const rw = pw - 28;
        // 圓角矩形視窗（半透明霧白壓克力質感）
        ctx.save();
        ctx.beginPath();
        ctx.roundRect(rx, 20, rw, 120, 22);
        ctx.fillStyle = "rgba(248, 250, 252, 0.72)";
        ctx.fill();
        ctx.lineWidth = 5;
        ctx.strokeStyle = "#b89462";
        ctx.stroke();
        ctx.clip();
        // 淡綠葉片裝飾
        ctx.fillStyle = "rgba(74, 222, 128, 0.35)";
        ctx.beginPath();
        ctx.ellipse(rx + rw * 0.25, 134, 28, 16, -0.3, 0, Math.PI * 2);
        ctx.ellipse(rx + rw * 0.78, 136, 26, 14, 0.25, 0, Math.PI * 2);
        ctx.fill();
        // 每格 3 個彩色音符
        drawNote(rx + rw * 0.22, 82, noteCols[(i * 3) % noteCols.length], i % 3);
        drawNote(rx + rw * 0.52, 78, noteCols[(i * 3 + 1) % noteCols.length], (i + 1) % 3);
        drawNote(rx + rw * 0.82, 82, noteCols[(i * 3 + 2) % noteCols.length], (i + 2) % 3);
        ctx.restore();
      }
      return makeCanvasTex(c);
    })();
    const notePanel = new THREE.Mesh(
      new THREE.PlaneGeometry(islLen, 0.42),
      new THREE.MeshStandardMaterial({ map: noteTex, transparent: true, roughness: 0.48, side: THREE.DoubleSide })
    );
    notePanel.position.copy(b2t(islCx, islY, zf + 0.99));
    lib.add(notePanel);
    addBox(oakDarkMat, islCx, islY, zf + 1.21, islLen + 0.04, 0.06, 0.035);

    // 6. 前景主閱覽區（南側門內左方）：2x3 粉彩拼色模組矮閱讀桌＋攤開繪本＋彩色圓柱形軟墊矮凳
    const tblX = x0 + 4.05;
    const tblY = y0 + 1.95;
    const pastelHex = [0x8ad2f2, 0xf7e57b, 0xa8e6b4, 0xf7ece6, 0xfbd3dc, 0x8ad2f2];
    const modW = 0.84;
    const modD = 0.74;
    for (let r = 0; r < 2; r++) {
      for (let c = 0; c < 3; c++) {
        const mx = tblX + (c - 1) * (modW + 0.015);
        const my = tblY + (r - 0.5) * (modD + 0.015);
        addBox(M(pastelHex[r * 3 + c], { roughness: 0.52 }), mx, my, zf + 0.44, modW, modD, 0.036);
        addBox(oakMat, mx - modW * 0.44, my, zf + 0.21, 0.04, modD - 0.08, 0.42);
        addBox(oakMat, mx + modW * 0.44, my, zf + 0.21, 0.04, modD - 0.08, 0.42);
      }
    }
    // 桌面上擺放數本攤開的彩色繪本
    for (const [bx, by, col, yaw] of [
      [tblX - 0.7, tblY - 0.25, 0xef4444, 0.15],
      [tblX + 0.1, tblY + 0.28, 0x3b82f6, -0.22],
      [tblX + 0.75, tblY - 0.18, 0x22c55e, 0.08],
      [tblX - 0.2, tblY - 0.34, 0xf59e0b, -0.12],
    ]) {
      addBox(M(col, { roughness: 0.6 }), bx, by, zf + 0.466, 0.36, 0.24, 0.014, yaw);
      addBox(whiteMat, bx, by, zf + 0.476, 0.33, 0.21, 0.008, yaw);
    }
    // 圓柱形軟墊矮凳（湖水綠為主＋亮黃、天藍、淺粉，含頂緣滾邊）
    const addDrumStool = (sx, sy, hex) => {
      addCyl(M(hex, { roughness: 0.45 }), sx, sy, zf + 0.17, 0.21, 0.21, 0.34, 22);
      addCyl(M(0xf8fafc, { roughness: 0.6 }), sx, sy, zf + 0.335, 0.214, 0.214, 0.014, 22);
    };
    const drumPositions = [
      [tblX - 1.55, tblY - 0.35, 0x4dc5b0],
      [tblX - 1.55, tblY + 0.35, 0x4dc5b0],
      [tblX - 0.75, tblY - 1.05, 0x4dc5b0],
      [tblX + 0.1, tblY - 1.05, 0xf5d04c],
      [tblX + 0.9, tblY - 1.05, 0x6ec4ea],
      [tblX - 0.65, tblY + 1.05, 0xf4a7b9],
      [tblX + 0.55, tblY + 1.05, 0x4dc5b0],
    ];
    for (const [sx, sy, hex] of drumPositions) addDrumStool(sx, sy, hex);

    // 7. 東南閱讀角（進門右手邊）：米白色圓形矮閱讀桌＋軟墊圓凳＋藍色雙層鐵製書車（書車 1）
    const rtX = x1 - 1.95;
    const rtY = y0 + 1.95;
    addCyl(M(0xf5f4ef, { roughness: 0.55 }), rtX, rtY, zf + 0.42, 0.58, 0.58, 0.036, 28);
    for (const [ox, oy] of [
      [-0.3, -0.3],
      [0.3, -0.3],
      [-0.3, 0.3],
      [0.3, 0.3],
    ]) {
      addCyl(oakMat, rtX + ox, rtY + oy, zf + 0.2, 0.028, 0.028, 0.4, 10);
    }
    addDrumStool(rtX + 0.85, rtY - 0.2, 0x4dc5b0);
    addDrumStool(rtX + 0.15, rtY - 0.88, 0xf5d04c);
    addDrumStool(rtX + 0.78, rtY + 0.62, 0x6ec4ea);

    // 藍色雙層書車（通道旁）
    const ctX = x1 - 1.15;
    const ctY = cy - 0.05;
    addBox(cartBlueMat, ctX, ctY, zf + 0.16, 0.82, 0.42, 0.04);
    addBox(cartBlueMat, ctX, ctY, zf + 0.56, 0.82, 0.42, 0.04);
    addBox(cartBlueMat, ctX - 0.4, ctY, zf + 0.5, 0.035, 0.42, 0.74);
    addBox(cartBlueMat, ctX + 0.4, ctY, zf + 0.5, 0.035, 0.42, 0.74);
    fillBookRowX(ctX - 0.35, ctX + 0.35, ctY, zf + 0.58, 0.24, 0.18, 0.25);

    // 8. 東牆背景：雙白色古典圓拱門框＋溝槽立柱＋紅黃藍綠彩色慶典小旗（Bunting）
    const archTex = (() => {
      const c = document.createElement("canvas");
      c.width = 1024;
      c.height = 512;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#8dc5e2";
      ctx.fillRect(0, 0, 1024, 512);
      // 拱門內深一階天空藍與遠景書架意象
      for (const acx of [280, 744]) {
        ctx.fillStyle = "#5b9dc4";
        ctx.beginPath();
        ctx.arc(acx, 220, 188, Math.PI, 0);
        ctx.lineTo(acx + 188, 512);
        ctx.lineTo(acx - 188, 512);
        ctx.closePath();
        ctx.fill();
        // 拱內淡色遠景書牆
        ctx.fillStyle = "#d9c29c";
        ctx.fillRect(acx - 150, 260, 300, 252);
        for (let r = 0; r < 4; r++) {
          ctx.fillStyle = "#b89462";
          ctx.fillRect(acx - 150, 290 + r * 56, 300, 8);
          for (let b = 0; b < 18; b++) {
            ctx.fillStyle = bookColors[(b + r * 5) % bookColors.length];
            ctx.fillRect(acx - 142 + b * 16, 266 + r * 56, 11, 24);
          }
        }
      }
      // 白色古典圓拱頂與門框（遮罩拱上方）
      ctx.fillStyle = "#f8fafc";
      ctx.beginPath();
      ctx.rect(0, 0, 1024, 512);
      for (const acx of [280, 744]) {
        ctx.moveTo(acx - 182, 512);
        ctx.lineTo(acx - 182, 220);
        ctx.arc(acx, 220, 182, Math.PI, 0, false);
        ctx.lineTo(acx + 182, 512);
        ctx.closePath();
      }
      ctx.fill("evenodd");
      // 古典羅馬溝槽柱線條
      for (const px of [48, 496, 944]) {
        ctx.fillStyle = "#e2e8f0";
        ctx.fillRect(px, 190, 32, 322);
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(px - 10, 174, 52, 24);
      }
      // 右座圓拱懸掛彩色三角慶典小旗（Bunting）
      const flagCols = ["#ef4444", "#facc15", "#3b82f6", "#22c55e", "#f97316", "#ec4899"];
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(564, 154);
      ctx.quadraticCurveTo(744, 232, 924, 154);
      ctx.stroke();
      for (let i = 0; i < 11; i++) {
        const t = (i + 0.5) / 11;
        const fx = 564 + t * 360;
        const fy = 154 + Math.sin(t * Math.PI) * 39;
        ctx.fillStyle = flagCols[i % flagCols.length];
        ctx.beginPath();
        ctx.moveTo(fx - 13, fy);
        ctx.lineTo(fx + 13, fy);
        ctx.lineTo(fx, fy + 28);
        ctx.closePath();
        ctx.fill();
      }
      return makeCanvasTex(c);
    })();
    const archPlane = new THREE.Mesh(
      new THREE.PlaneGeometry(wy - 0.4, h - 0.14),
      new THREE.MeshStandardMaterial({ map: archTex, roughness: 0.72 })
    );
    archPlane.rotation.y = -Math.PI / 2;
    // 東牆隔間內表面在 x1 - 0.10，置於 x1 - 0.155 清晰呈現雙白色古典圓拱門與彩色三角小旗
    archPlane.position.copy(b2t(x1 - 0.155, cy, zf + (h - 0.14) * 0.5));
    lib.add(archPlane);

    // 9. 北側後方服務區：藍綠色借還書櫃檯（含 2 台電腦螢幕）＋「好書區」紫色拱頂展示書架＋螢光草綠兒童椅
    const deskX = x1 - 2.3;
    const deskY = y1 - 1.55;
    addBox(tealDeskMat, deskX, deskY, zf + 0.44, 2.2, 0.72, 0.86);
    addBox(oakMat, deskX, deskY, zf + 0.89, 2.28, 0.78, 0.04);
    for (const mx of [deskX - 0.52, deskX + 0.48]) {
      addBox(darkMat, mx, deskY + 0.05, zf + 1.13, 0.48, 0.04, 0.32);
      addBox(chromeMat, mx, deskY + 0.06, zf + 0.94, 0.06, 0.06, 0.12);
      addBox(darkMat, mx, deskY - 0.16, zf + 0.92, 0.36, 0.14, 0.02);
    }

    // 「好書區」紫色弧形拱頂展示書架（西北後區）
    const gbX = x0 + 3.1;
    const gbY = y1 - 1.45;
    addBox(oakMat, gbX, gbY, zf + 0.72, 2.1, 0.48, 1.42);
    addBox(limeMat, gbX + 1.12, gbY, zf + 0.55, 0.14, 0.44, 1.06);
    // 紫色半圓弧頂蓋（軸沿 Z 深 0.52m、寬沿 X 2.12m、向上拱起高 0.38m）
    const purpleArch = new THREE.Mesh(
      new THREE.CylinderGeometry(1.06, 1.06, 0.52, 24, 1, false, -Math.PI / 2, Math.PI),
      purpleMat
    );
    purpleArch.scale.set(1, 1, 0.36);
    purpleArch.rotation.x = -Math.PI / 2;
    purpleArch.position.copy(b2t(gbX, gbY, zf + 1.43));
    lib.add(purpleArch);
    // 鮮黃色「好書區」招牌橫樑
    const goodBookTex = (() => {
      const c = document.createElement("canvas");
      c.width = 512;
      c.height = 96;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#facc15";
      ctx.fillRect(0, 0, 512, 96);
      // 白底紅框「好書區」字牌＋兩側小紅花
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(140, 14, 232, 68);
      ctx.strokeStyle = "#dc2626";
      ctx.lineWidth = 5;
      ctx.strokeRect(140, 14, 232, 68);
      ctx.fillStyle = "#dc2626";
      ctx.font = "900 44px 'Microsoft JhengHei', 'Noto Sans TC', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("好書區", 256, 50);
      for (const fx of [72, 440]) {
        ctx.beginPath();
        ctx.arc(fx, 48, 22, 0, Math.PI * 2);
        ctx.fillStyle = "#ef4444";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(fx, 48, 8, 0, Math.PI * 2);
        ctx.fillStyle = "#fde047";
        ctx.fill();
      }
      return makeCanvasTex(c);
    })();
    const gbBanner = new THREE.Mesh(
      new THREE.PlaneGeometry(2.1, 0.34),
      new THREE.MeshStandardMaterial({ map: goodBookTex, roughness: 0.55 })
    );
    gbBanner.position.copy(b2t(gbX, gbY - 0.25, zf + 1.38));
    lib.add(gbBanner);
    // 斜插繪本封面展示
    for (let lv = 0; lv < 3; lv++) {
      fillBookRowX(gbX - 0.96, gbX + 0.96, gbY - 0.22, zf + 0.16 + lv * 0.34, 0.12, 0.22, 0.26);
    }
    // 2 張螢光草綠兒童靠背塑膠椅
    for (const [cx0, cy0] of [
      [gbX - 0.45, gbY - 0.9],
      [gbX + 0.55, gbY - 0.9],
    ]) {
      addBox(limeMat, cx0, cy0, zf + 0.32, 0.34, 0.34, 0.04);
      addBox(limeMat, cx0, cy0 - 0.15, zf + 0.52, 0.34, 0.04, 0.36);
      for (const [lx, ly] of [
        [-0.14, -0.14],
        [0.14, -0.14],
        [-0.14, 0.14],
        [0.14, 0.14],
      ]) {
        addBox(limeMat, cx0 + lx, cy0 + ly, zf + 0.16, 0.035, 0.035, 0.32);
      }
    }

    const builtBooks = libBooks.build();
    if (builtBooks) lib.add(builtBooks);

    // 柔和室內補光（還原圖書館明亮清透氛圍）
    const libLight = new THREE.PointLight(0xf6fbff, 6.5, 14, 1.35);
    libLight.position.copy(b2t(cx, cy, zc - 0.35));
    lib.add(libLight);

    lib.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = false;
        o.receiveShadow = false;
      }
    });
    parentGroup.add(lib);
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
    } else if (code === "KeyC") {
      cycleOutfit();
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

  function refreshOutfitBtn() {
    const b = el.outfitBtn();
    const cur = OUTFITS.find((o) => o.key === S.outfit) || OUTFITS[0];
    if (b) b.textContent = cur.btn;
  }

  function setOutfit(key) {
    const found = OUTFITS.find((o) => o.key === key) || OUTFITS[0];
    S.outfit = found.key;
    try {
      localStorage.setItem(OUTFIT_STORAGE_KEY, S.outfit);
    } catch (_) {
      // ignore storage errors
    }
    S.avatar?.userData?.applyOutfit?.(S.outfit);
    refreshOutfitBtn();
    requestRender(4);
  }

  function cycleOutfit() {
    const idx = OUTFITS.findIndex((o) => o.key === S.outfit);
    const next = OUTFITS[(idx + 1) % OUTFITS.length];
    setOutfit(next.key);
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
      S.avatar = buildAvatar(S.outfit);
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
    refreshOutfitBtn();
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
    el.outfitBtn()?.addEventListener("click", () => cycleOutfit());
    el.viewBtn()?.addEventListener("click", () => toggleView());
    el.exit()?.addEventListener("click", () => exit());
    refreshOutfitBtn();
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
    cycleOutfit,
    setOutfit,
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
