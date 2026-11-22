/**
 * 新北市板橋區重慶國小 115 學年度 3D 實景校園導覽系統（v12 UI/UX + 全校教室 3D 精準標示版）
 * 依學校官網最新《115學年度班級配置圖》（https://www.cges.ntpc.edu.tw/p/404-1000-7000.php）逐間核對
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { computeCampusRoute, ROUTE_STARTS } from "./campus_routing.js";

// Blender (X, Y, Z) -> Three.js (X, Z, -Y)
const b2t = (x, y, z) => new THREE.Vector3(x, z, -y);

const CAT_META = {
  all: { label: "全部", shortLabel: "全部", color: "#38bdf8" },
  admin: { label: "行政處室", shortLabel: "行政", color: "#818cf8" },
  grade1: { label: "一年級", shortLabel: "一年", color: "#c084fc" },
  grade2: { label: "二年級", shortLabel: "二年", color: "#f472b6" },
  grade3: { label: "三年級", shortLabel: "三年", color: "#fb923c" },
  grade4: { label: "四年級", shortLabel: "四年", color: "#facc15" },
  grade5: { label: "五年級", shortLabel: "五年", color: "#84cc16" },
  grade6: { label: "六年級", shortLabel: "六年", color: "#38bdf8" },
  youxue: { label: "優學班", shortLabel: "優學", color: "#fdba74" },
  kinder: { label: "幼兒園", shortLabel: "幼兒園", color: "#fb7185" },
  special: { label: "專科教室", shortLabel: "專科", color: "#2dd4bf" },
  public: { label: "穿堂・廁所", shortLabel: "穿堂/廁所", color: "#94a3b8" },
};

const FILTER_ORDER = ["all", "admin", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6", "youxue", "kinder", "special", "public"];

// Dynamic zone metadata loaded from single-source-of-truth campus_cges.json ("zones")
let ZONE_META = [];

const GUIDED_TOUR = [
  {
    title: "① 廣和街 31 號主校門與半圓拱警衛室",
    zoneId: "Bldg_Guanghe",
    pos: [-90, -4, 5.2],
    tgt: [-46, 2.5, 9.2],
    desc: "校門左側為紅褐磚中空門塔與貫穿式米白半圓筒拱警衛室，右側是校名牌牆與金色字牌，門前設有黃網線、綠底行穿線與幼童專用校車停靠區。",
  },
  {
    title: "② 廣和樓挑高穿堂與行政中樞",
    zoneId: "Bldg_Guanghe",
    pos: [-70, -1, 7.5],
    tgt: [-42, 0.5, 9.5],
    desc: "踏上 11 階寬階梯進入廣和樓穿堂（1F 學務處／健康中心），2F–5F 依序為人事、主計、輔導室、304-2 總務處、304-3 教務處、305 校長室、405 教師大辦公室與 505 視聽中心。",
  },
  {
    title: "③ 和平樓北翼校舍與中庭生態池",
    zoneId: "Bldg_Heping",
    pos: [-32, -4, 12.0],
    tgt: [-26, 25.0, 7.5],
    desc: "和平樓由東至西涵蓋幼兒園（陽光／雲朵／星空班）、優學 1–3 班及一／三／五／六年級教室，2F 1梯口直接連通跨和平路海豚天橋；中庭設有生態水生池與拱形小木橋。",
  },
  {
    title: "④ 五權樓連建式升旗司令台與 200m 操場",
    zoneId: "Bldg_Wuquan",
    pos: [52, -46, 15.0],
    tgt: [8, -14, 5.5],
    desc: "升旗司令台與五權樓中段穿堂及 2F 露台一體連建（雙側米白斜牆階梯＋2F 無柱懸挑遮雨棚＋三支旗桿），前方為開闊灰色透水磚大道與 200m 六跑道紅 PU 操場。",
  },
  {
    title: "⑤ 重慶樓南翼專科教室與露天雙籃球場",
    zoneId: "Bldg_Chongqing",
    pos: [-38, -82, 13.0],
    tgt: [-38, -42, 8.2],
    desc: "重慶樓南臨開闊露天雙籃球場與特色馬賽克花磚圍牆，內含 107/108 唱遊教室、208 彩繪火車圖書室、二／四年級班級，以及 3–5F 自然、英語與音樂專科教室。",
  },
  {
    title: "⑥ 和平路海豚彩繪空橋與重慶國小運動中心",
    zoneId: "Bldg_Gym_Skybridge",
    pos: [2, 42, 6.8],
    tgt: [-24, 58, 7.2],
    desc: "從和平樓 2F 1梯延伸出橫跨和平路的藍色海豚彩繪人行天橋，安全直達對面綜合運動中心（內含室內溫水游泳池、韻律教室與 3F 綜合室內球場）。",
  },
  {
    title: "⑦ 全校區 360° 鳥瞰總覽",
    zoneId: null,
    pos: [-122, -104, 82],
    tgt: [-6, -2, 6],
    desc: "鳥瞰重慶國小完整 115 學年度校園配置：四棟 5 層樓校舍（共 127 處室內空間）、中庭生態池、雙籃球場、200m 操場與跨和平路運動中心一覽無遺。",
  },
];

// --- Three.js Scene Setup ---
const wrap = document.getElementById("canvas-wrap");
const statusEl = document.getElementById("status");

const scene = new THREE.Scene();

const skyGeo = new THREE.SphereGeometry(680, 32, 20);
const skyUniforms = {
  topColor: { value: new THREE.Color(0x3574cc) },
  horizonColor: { value: new THREE.Color(0xd8e9f8) },
  bottomColor: { value: new THREE.Color(0xc8d2dc) },
};
const skyMat = new THREE.ShaderMaterial({
  uniforms: skyUniforms,
  side: THREE.BackSide,
  depthWrite: false,
  vertexShader: `
    varying vec3 vWorldPos;
    void main() {
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }
  `,
  fragmentShader: `
    uniform vec3 topColor;
    uniform vec3 horizonColor;
    uniform vec3 bottomColor;
    varying vec3 vWorldPos;
    void main() {
      float h = normalize(vWorldPos).y;
      vec3 col = h >= 0.0
        ? mix(horizonColor, topColor, pow(clamp(h, 0.0, 1.0), 0.55))
        : mix(horizonColor, bottomColor, clamp(-h * 4.0, 0.0, 1.0));
      gl_FragColor = vec4(col, 1.0);
    }
  `,
});
scene.add(new THREE.Mesh(skyGeo, skyMat));
scene.fog = new THREE.FogExp2(0xd4e4f4, 0.00105);

const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.5, 1400);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth <= 900 ? 1.5 : 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.04;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;
renderer.localClippingEnabled = true;
wrap.appendChild(renderer.domElement);

// Horizontal Floor Cutaway Plane (clips Y > constant in Three.js world space)
const floorClipPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 999);
const clippedMatCache = new WeakMap();

let renderFramesLeft = 16;
function requestRender(frames = 6) {
  renderFramesLeft = Math.max(renderFramesLeft, frames);
}
function requestShadowUpdate() {
  renderer.shadowMap.needsUpdate = true;
  requestRender(8);
}

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(window.innerWidth, window.innerHeight);
labelRenderer.domElement.style.position = "fixed";
labelRenderer.domElement.style.top = "0";
labelRenderer.domElement.style.left = "0";
labelRenderer.domElement.style.pointerEvents = "none";
labelRenderer.domElement.style.zIndex = "10";
document.body.appendChild(labelRenderer.domElement);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.55;

const hemi = new THREE.HemisphereLight(0xdbeafe, 0x7c756c, 0.85);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xfff4df, 2.7);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
sun.shadow.camera.near = 15;
sun.shadow.camera.far = 480;
const d = 148;
sun.shadow.camera.left = -d;
sun.shadow.camera.right = d;
sun.shadow.camera.top = d;
sun.shadow.camera.bottom = -d;
sun.shadow.bias = -0.00035;
sun.shadow.normalBias = 0.03;
scene.add(sun);

const SUN_MODES = {
  morning: { pos: [120, 115, 75], color: 0xfff7e8, intensity: 2.5, top: 0x3b82f6, horizon: 0xe0f2fe, fog: 0xdbeafe, hemiSky: 0xe0f2fe },
  afternoon: { pos: [-110, 130, 88], color: 0xfff4df, intensity: 2.7, top: 0x3574cc, horizon: 0xd8e9f8, fog: 0xd4e4f4, hemiSky: 0xdbeafe },
  sunset: { pos: [-155, 42, 48], color: 0xffb36b, intensity: 2.9, top: 0x314a7a, horizon: 0xfbd3a8, fog: 0xe8c7a6, hemiSky: 0xfed7aa },
};

function applySun(mode) {
  const s = SUN_MODES[mode];
  if (!s) return;
  sun.position.set(...s.pos);
  sun.color.setHex(s.color);
  sun.intensity = s.intensity;
  skyUniforms.topColor.value.setHex(s.top);
  skyUniforms.horizonColor.value.setHex(s.horizon);
  scene.fog.color.setHex(s.fog);
  hemi.color.setHex(s.hemiSky);
  document.querySelectorAll("[data-sun]").forEach((b) => b.classList.toggle("active", b.dataset.sun === mode));
  requestShadowUpdate();
}
applySun("afternoon");

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.075;
controls.maxPolarAngle = Math.PI * 0.492;
controls.minDistance = 6;
controls.maxDistance = 380;
controls.addEventListener("change", () => requestRender(4));
window.addEventListener("pointerdown", () => requestRender(6), { passive: true });
window.addEventListener("wheel", () => requestRender(12), { passive: true });
window.addEventListener("keydown", () => requestRender(8), { passive: true });
document.addEventListener("click", () => requestRender(10), { passive: true });

// --- Application State ---
const state = {
  spec: null,
  allRooms: [], // Flattened 147+ verified room records with unique uid & zone ref
  rootModel: null,
  allMeshes: [],
  origMaterials: new Map(),
  dimMat: new THREE.MeshStandardMaterial({ color: 0xb8c0ca, roughness: 0.9, metalness: 0.0, transparent: true, opacity: 0.16 }),
  selectedZoneId: null,
  selectedFloor: "ALL", // "ALL" | "5F" | "4F" | ...
  selectedCategory: "all",
  activeRoomUid: null,
  roomViewAerial: false,
  labelMode: "smart", // "smart" | "all" | "off"
  xrayOn: false,
  rulerMode: false,
  rulerPts: [],
  tourActive: false,
  tourPlaying: true,
  tourIndex: 0,
  tourTimer: null,
  searchQuery: "",
  sidebarTab: "dir", // "dir" | "route"
  routeOpen: false,
  routeStartId: "gate_main",
  routeAccessible: false,
  autoSliceRoute: true,
  sliceTargetZ: null,
  sliceCurrentZ: 999,
  sliceLabel: "",
  routeData: null,
  routeFlyAlong: false,
  routeFlyProgress: 0,
};

function updateCameraViewportOffset() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const sidebarEl = document.getElementById("sidebar");
  const isCollapsed = sidebarEl?.classList.contains("collapsed");
  const collapseBtn = document.getElementById("btnCollapse");
  const footerTip = document.querySelector(".footer-tip");
  if (collapseBtn) collapseBtn.textContent = w <= 900 ? "▼" : "◀";
  if (footerTip) footerTip.textContent = w <= 900 ? "單指旋轉・雙指平移與縮放" : "左鍵旋轉・右鍵平移・滾輪縮放";
  if (w > 900 && !isCollapsed) {
    // Shift projection center right by half the sidebar width so 3D campus & room pins stay centered in open canvas!
    camera.setViewOffset(w, h, -190, 0, w, h);
  } else {
    camera.clearViewOffset();
  }
  camera.updateProjectionMatrix();
}

// Default hero landing perspective (NW corner framing Heping vertical sign, N/S oculus bridges, Guanghe emblem & main gate!)
const DEFAULT_VIEW = {
  pos: [-118, 44, 15.5],
  tgt: [-52, 13, 10.0],
};

let tweenPos = null;
let tweenTgt = null;
function flyTo(posArr, tgtArr) {
  tweenPos = b2t(...posArr);
  tweenTgt = b2t(...tgtArr);
  requestRender(20);
}

camera.position.copy(b2t(...DEFAULT_VIEW.pos));
controls.target.copy(b2t(...DEFAULT_VIEW.tgt));
updateCameraViewportOffset();
controls.update();

controls.addEventListener("start", () => {
  tweenPos = null;
  tweenTgt = null;
  if (typeof stopRouteFlyAlong === "function") stopRouteFlyAlong();
});

// --- Data Hydration & Search Normalization ---
function buildSearchHaystack(room, zone) {
  const alias = [];
  const full = `${room.code} ${room.name} ${room.short}`;
  // Allow shorthand queries like "六6" / "6年6班" / "6-6" / "保健室" (avoid 3-digit room-number collisions like "305"!)
  const mGrade = room.name.match(/^([一二三四五六])年(\d+)班/);
  if (mGrade) {
    const gMap = { 一: "1", 二: "2", 三: "3", 四: "4", 五: "5", 六: "6" };
    const gn = gMap[mGrade[1]];
    alias.push(`${mGrade[1]}${mGrade[2]}`, `${gn}年${mGrade[2]}班`, `${gn}-${mGrade[2]}`);
  }
  if (room.name.includes("健康中心")) alias.push("保健室", "醫護室", "護理師");
  if (room.name.includes("圖書室")) alias.push("圖書館", "閱讀");
  if (room.name.includes("天橋")) alias.push("空橋", "海豚");
  if (room.name.includes("司令台")) alias.push("升旗台", "講台");
  if (room.name.includes("廁")) alias.push("洗手間", "廁所", "wc");
  const catLabel = CAT_META[room.cat]?.label || "";
  return `${full} ${room.floor} ${room.stairs} ${zone.name} ${zone.shortName} ${catLabel} ${alias.join(" ")}`.toLowerCase();
}

function hydrateAllRooms() {
  state.allRooms = [];
  let seq = 0;
  for (const z of ZONE_META) {
    const bSpec = state.spec?.buildings?.find((b) => b.id === z.id);
    const list = bSpec?.rooms_115_detailed || z.extraDetailed || [];
    for (const r of list) {
      const rec = {
        uid: `r_${seq++}`,
        zoneId: z.id,
        zone: z,
        floor: r.floor,
        code: r.code || "",
        name: r.name,
        short: r.short || (r.code ? `${r.code} ${r.name}` : r.name),
        cat: r.cat || "public",
        pos: r.pos,
        size: r.size || [5.2, 4.6, 3.1],
        face: r.face || "S",
        stairs: r.stairs || "",
      };
      rec.haystack = buildSearchHaystack(rec, z);
      state.allRooms.push(rec);
    }
  }
}

function getRoomsForZone(zoneId) {
  return state.allRooms.filter((r) => r.zoneId === zoneId);
}

function getFloorsForZone(zoneId) {
  const seen = [];
  for (const r of getRoomsForZone(zoneId)) {
    if (!seen.includes(r.floor)) seen.push(r.floor);
  }
  return seen.sort((a, b) => {
    const na = parseInt(a, 10);
    const nb = parseInt(b, 10);
    if (!Number.isNaN(na) && !Number.isNaN(nb)) return nb - na;
    return 0;
  });
}

function getFilteredGlobalRooms() {
  const q = state.searchQuery.trim().toLowerCase();
  const cat = state.selectedCategory;
  return state.allRooms.filter((r) => {
    if (cat !== "all" && r.cat !== cat) return false;
    if (q && !r.haystack.includes(q)) return false;
    return true;
  });
}

// --- 3D Floating Labels (Zone Bubbles + Per-Room Plaques + Floor Band + Active Pin) ---
const zoneLabelsGroup = new THREE.Group();
const roomLabelsGroup = new THREE.Group();
scene.add(zoneLabelsGroup);
scene.add(roomLabelsGroup);

let activeRoomPin = null;
let activeRoomBox = null;
let activeFloorBand = null;
const activeRouteGroup = new THREE.Group();
scene.add(activeRouteGroup);
let routeCurve = null;
let routePulseOrb = null;
const routeWaypointLabels = [];

function isSliceableBuildingMesh(name) {
  return (
    name.startsWith("Bldg_") ||
    name.startsWith("Campus_") ||
    name.startsWith("Landmark_CornerTowers") ||
    name.startsWith("Landmark_SouthCorner") ||
    name.startsWith("Landmark_Skybridge") ||
    name.startsWith("Landmark_Guanghe") ||
    name.startsWith("Landmark_HepingNorth") ||
    name.startsWith("Landmark_WuquanB1") ||
    name.startsWith("Landmark_SWPortal") ||
    name.startsWith("Landmark_FrontGreenCanopies") ||
    name.startsWith("Landmark_SouthArchedCanopy")
  );
}

function getFloorSliceZ(zoneId, floorInput) {
  const f = typeof floorInput === "number" ? floorInput : parseInt(String(floorInput || ""), 10);
  if (Number.isNaN(f) || !zoneId || zoneId === "Zone_Outdoor") return null;
  if (zoneId === "Bldg_Guanghe") {
    if (f <= 1) return 3.85;
    if (f >= 5) return 17.65;
    return 4.2 + (f - 1) * 3.4 - 0.35;
  }
  if (zoneId === "Bldg_Gym_Skybridge") {
    if (f <= 1) return 4.6;
    if (f === 2) return 9.6;
    return 16.8;
  }
  if (f <= 1) return 3.25;
  if (f >= 5) return 17.05;
  return 3.6 + (f - 1) * 3.4 - 0.35;
}

function updateSliceCutaway(sliceZ, labelText = "", immediate = false) {
  const changed = state.sliceTargetZ !== sliceZ;
  state.sliceTargetZ = sliceZ;
  state.sliceLabel = labelText;
  if (immediate || sliceZ === null) {
    state.sliceCurrentZ = sliceZ === null ? 999 : sliceZ;
    floorClipPlane.constant = state.sliceCurrentZ;
  }
  const statusEl = document.getElementById("sliceStatus");
  const xrayBtn = document.getElementById("btnXray");
  const isSliced = sliceZ !== null;
  if (statusEl) {
    statusEl.classList.toggle("active", isSliced || state.xrayOn);
    if (isSliced) {
      statusEl.textContent = `🔪 已剖開：${labelText || "走廊"}`;
    } else if (state.xrayOn) {
      statusEl.textContent = "👁 已透視屋頂";
    } else {
      statusEl.textContent = "🏠 完整校舍";
    }
  }
  if (xrayBtn) {
    xrayBtn.classList.toggle("active", state.xrayOn || isSliced);
    xrayBtn.textContent = isSliced ? "🔪 復原" : state.xrayOn ? "👁 屋頂透視" : "🔪 剖層";
  }
  if (changed) refresh3DLabels();
  requestRender(8);
}

function setSidebarTab(tab, ensureOpen = false) {
  state.sidebarTab = tab;
  const isRoute = tab === "route";
  document.getElementById("tabDir")?.classList.toggle("active", !isRoute);
  document.getElementById("tabRoute")?.classList.toggle("active", isRoute);
  document.getElementById("tabDir")?.setAttribute("aria-selected", String(!isRoute));
  document.getElementById("tabRoute")?.setAttribute("aria-selected", String(isRoute));

  const paneDir = document.getElementById("paneDir");
  const paneRoute = document.getElementById("paneRoute");
  if (paneDir) paneDir.hidden = isRoute;
  if (paneRoute) paneRoute.hidden = !isRoute;

  if (ensureOpen) {
    const sidebar = document.getElementById("sidebar");
    if (sidebar?.classList.contains("collapsed")) {
      sidebar.classList.remove("collapsed");
      updateCameraViewportOffset();
    }
  }
}

function stopRouteFlyAlong() {
  state.routeFlyAlong = false;
  const btn = document.getElementById("btnRouteFlyAlong");
  if (btn) {
    btn.textContent = "▶ 走廊實境";
    btn.classList.remove("active");
  }
}

function clearRouteVisuals() {
  stopRouteFlyAlong();
  while (activeRouteGroup.children.length > 0) {
    const child = activeRouteGroup.children[0];
    child.geometry?.dispose();
    child.material?.dispose();
    activeRouteGroup.remove(child);
  }
  while (routeWaypointLabels.length > 0) {
    const lbl = routeWaypointLabels.pop();
    scene.remove(lbl);
    lbl.element?.remove();
  }
  routeCurve = null;
  routePulseOrb = null;
}

function renderActiveRoute(room, shouldOpenPanel = false) {
  clearRouteVisuals();
  const emptyEl = document.getElementById("routeEmptyState");
  const activeBodyEl = document.getElementById("routeActiveBody");
  const badgeEl = document.getElementById("tabRouteBadge");

  if (!room) {
    state.routeData = null;
    if (emptyEl) emptyEl.hidden = false;
    if (activeBodyEl) activeBodyEl.hidden = true;
    if (badgeEl) badgeEl.hidden = true;
    return;
  }

  const data = computeCampusRoute(room, state.routeStartId, state.routeAccessible);
  state.routeData = data;
  if (shouldOpenPanel) {
    state.routeOpen = true;
    setSidebarTab("route", true);
  }

  const routeBtn = document.getElementById("btnRoomRoute");
  if (routeBtn) routeBtn.classList.toggle("active", state.routeOpen);

  if (!state.routeOpen || !data) {
    if (emptyEl) emptyEl.hidden = false;
    if (activeBodyEl) activeBodyEl.hidden = true;
    if (badgeEl) badgeEl.hidden = true;
    return;
  }

  if (emptyEl) emptyEl.hidden = true;
  if (activeBodyEl) activeBodyEl.hidden = false;
  if (badgeEl) {
    badgeEl.hidden = false;
    badgeEl.textContent = `${room.floor} · ${data.totalMeters}m`;
  }

  const destMetaEl = document.getElementById("routeDestMeta");
  const destNameEl = document.getElementById("routeDestName");
  if (destMetaEl) destMetaEl.textContent = `${room.zone.shortName}・${room.floor}${state.routeAccessible ? "・♿ 無障礙優先" : ""}`;
  if (destNameEl) destNameEl.textContent = room.short || room.name;

  document.getElementById("routeSummary").textContent = `約 ${data.totalMeters}m · ${data.estMinutes}分`;
  document.getElementById("btnRouteAccess").classList.toggle("active", state.routeAccessible);
  document.getElementById("btnRouteSliceAuto")?.classList.toggle("active", state.autoSliceRoute);

  if (state.autoSliceRoute && data.destZoneId && data.destZoneId !== "Zone_Outdoor") {
    const destSlice = getFloorSliceZ(data.destZoneId, data.destFloor);
    updateSliceCutaway(destSlice, `${room.zone.shortName} ${room.floor} 走廊`);
  } else if (!state.xrayOn) {
    updateSliceCutaway(null, "");
  }

  const listEl = document.getElementById("routeStepsList");
  listEl.innerHTML = "";
  data.steps.forEach((step, idx) => {
    const li = document.createElement("li");
    li.className = "route-step-item";
    li.innerHTML = `
      <span class="route-step-num">${idx + 1}</span>
      <div class="route-step-body">${step.icon} ${step.text}</div>
      <span class="route-step-badge">${step.badge}</span>
    `;
    li.addEventListener("click", () => {
      stopRouteFlyAlong();
      document.querySelectorAll(".route-step-item").forEach((el) => el.classList.remove("active"));
      li.classList.add("active");

      const [sx, sy, sz] = step.pos;
      const [dx, dy] = step.dir || [1, 0];
      if (state.autoSliceRoute && step.indoor && step.zoneId && step.zoneId !== "Zone_Outdoor") {
        const sSlice = getFloorSliceZ(step.zoneId, step.floor);
        updateSliceCutaway(sSlice, `${step.floor}F 走廊`);
      } else if (!state.autoSliceRoute || !step.indoor) {
        if (!state.xrayOn) updateSliceCutaway(null, "");
      }

      if (step.indoor) {
        // Sloped corridor-eye view looking down the sliced open hallway along direction of travel
        flyTo([sx - dx * 12.5, sy - dy * 12.5, sz + 5.8], [sx + dx * 5.0, sy + dy * 5.0, sz + 0.4]);
      } else {
        flyTo([sx - dx * 16.0, sy - dy * 16.0, Math.max(7.5, sz + 8.5)], [sx + dx * 4.0, sy + dy * 4.0, sz + 0.6]);
      }
    });
    listEl.appendChild(li);
  });

  // Build 3D Glowing Route Tube + Moving Golden Orb + Waypoint Chips
  if (data.points3D.length >= 2) {
    const pts = data.points3D.map(([x, y, z]) => b2t(x, y, z));
    routeCurve = new THREE.CurvePath();
    for (let k = 0; k < pts.length - 1; k++) {
      routeCurve.add(new THREE.LineCurve3(pts[k], pts[k + 1]));
    }
    const segCount = Math.max(24, pts.length * 10);
    const tubeGeo = new THREE.TubeGeometry(routeCurve, segCount, 0.24, 8, false);
    const tubeMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee });
    activeRouteGroup.add(new THREE.Mesh(tubeGeo, tubeMat));

    const haloGeo = new THREE.TubeGeometry(routeCurve, segCount, 0.44, 8, false);
    const haloMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.24, depthWrite: false });
    activeRouteGroup.add(new THREE.Mesh(haloGeo, haloMat));

    const nodeGeo = new THREE.SphereGeometry(0.36, 10, 10);
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0xfde047 });
    for (const p of pts) {
      const m = new THREE.Mesh(nodeGeo.clone(), nodeMat.clone());
      m.position.copy(p);
      activeRouteGroup.add(m);
    }

    routePulseOrb = new THREE.Mesh(
      new THREE.SphereGeometry(0.56, 14, 14),
      new THREE.MeshBasicMaterial({ color: 0xfde047 })
    );
    routePulseOrb.position.copy(pts[0]);
    activeRouteGroup.add(routePulseOrb);

    for (const wp of data.waypoints) {
      const el = document.createElement("div");
      el.className = "label-route-wp";
      el.textContent = wp.label;
      const obj = new CSS2DObject(el);
      obj.position.copy(b2t(...wp.pos));
      scene.add(obj);
      routeWaypointLabels.push(obj);
    }
    requestRender(12);
  }
}

function flyToRouteOverview() {
  if (!state.routeData || state.routeData.points3D.length < 2) return;
  stopRouteFlyAlong();
  if (state.autoSliceRoute && state.routeData.destZoneId && state.routeData.destZoneId !== "Zone_Outdoor") {
    const destSlice = getFloorSliceZ(state.routeData.destZoneId, state.routeData.destFloor);
    updateSliceCutaway(destSlice, `${state.routeData.destFloor}F 走廊`);
  }
  const pts = state.routeData.points3D;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, maxZ = 2;
  for (const [x, y, z] of pts) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (z > maxZ) maxZ = z;
  }
  const cx = (minX + maxX) * 0.5;
  const cy = (minY + maxY) * 0.5;
  const span = Math.max(36, Math.hypot(maxX - minX, maxY - minY));
  flyTo([cx - span * 0.62, cy - span * 0.62, Math.max(24, span * 0.58 + maxZ * 0.5)], [cx, cy, maxZ * 0.45]);
}

function clearGroupLabels(grp) {
  while (grp.children.length > 0) {
    const child = grp.children[0];
    child.element?.remove();
    grp.remove(child);
  }
}

function clearFloorBand() {
  if (activeFloorBand) {
    scene.remove(activeFloorBand);
    activeFloorBand.traverse((o) => {
      o.geometry?.dispose();
      o.material?.dispose();
    });
    activeFloorBand = null;
  }
}

function updateFloorBand() {
  clearFloorBand();
  if (!state.selectedZoneId || state.selectedFloor === "ALL") return;
  const z = ZONE_META.find((item) => item.id === state.selectedZoneId);
  if (!z?.bounds) return;
  const flNum = parseInt(state.selectedFloor, 10);
  if (Number.isNaN(flNum)) return;

  const { x0, x1, y0, y1, h1, hu } = z.bounds;
  const flH = flNum === 1 ? h1 : hu;
  const zMid = flNum === 1 ? h1 * 0.5 : h1 + (flNum - 2) * hu + hu * 0.5;
  const pad = 0.85;
  const bw = x1 - x0 + pad * 2;
  const bd = y1 - y0 + pad * 2;
  const cx = (x0 + x1) * 0.5;
  const cy = (y0 + y1) * 0.5;

  const grp = new THREE.Group();
  const fillGeo = new THREE.BoxGeometry(bw, flH - 0.1, bd);
  const fill = new THREE.Mesh(
    fillGeo,
    new THREE.MeshBasicMaterial({ color: 0xfde047, transparent: true, opacity: 0.16, depthWrite: false })
  );
  fill.position.copy(b2t(cx, cy, zMid));
  grp.add(fill);

  // Thick 3D glowing perimeter bars on floor top & bottom (clearly visible unlike 1px WebGL lines!)
  const barMat = new THREE.MeshBasicMaterial({ color: 0xfde047 });
  const barT = 0.18;
  for (const dz of [-flH * 0.5 + 0.08, flH * 0.5 - 0.08]) {
    const zb = zMid + dz;
    for (const sy of [-bd * 0.5, bd * 0.5]) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(bw + barT, barT, barT), barMat);
      m.position.copy(b2t(cx, cy + sy, zb));
      grp.add(m);
    }
    for (const sx of [-bw * 0.5, bw * 0.5]) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(barT, barT, bd + barT), barMat);
      m.position.copy(b2t(cx + sx, cy, zb));
      grp.add(m);
    }
  }
  scene.add(grp);
  activeFloorBand = grp;
}

function buildZoneLabels() {
  clearGroupLabels(zoneLabelsGroup);
  ZONE_META.forEach((z) => {
    const el = document.createElement("div");
    el.className = "label-3d";
    el.innerHTML = `<span style="color:${z.color}">●</span> ${z.shortName}`;
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      selectZone(z.id, true);
    });
    const obj = new CSS2DObject(el);
    obj.position.copy(b2t(...z.labelPos));
    zoneLabelsGroup.add(obj);
  });
}

function computeVisibleRoomsFor3D() {
  if (state.labelMode === "off") return [];
  const q = state.searchQuery.trim();
  const hasFilter = q.length > 0 || state.selectedCategory !== "all";

  if (state.labelMode === "all") {
    // Show all classrooms & offices across entire campus (skip generic restrooms only if no explicit filter)
    if (hasFilter) return getFilteredGlobalRooms();
    return state.allRooms.filter((r) => !(r.cat === "public" && r.name.includes("廁")));
  }

  // Smart mode:
  if (hasFilter) return getFilteredGlobalRooms();
  if (state.selectedZoneId) {
    const inZone = getRoomsForZone(state.selectedZoneId);
    if (state.selectedFloor !== "ALL") {
      return inZone.filter((r) => r.floor === state.selectedFloor);
    }
    // When full building is selected without floor filter, show all classrooms/offices (keep restrooms out of dense 5F stack)
    return inZone.filter((r) => !(r.cat === "public" && r.name.includes("廁")));
  }
  return [];
}

function refresh3DLabels() {
  clearGroupLabels(roomLabelsGroup);

  if (state.labelMode === "off") {
    zoneLabelsGroup.visible = false;
    return;
  }

  const roomsToShow = computeVisibleRoomsFor3D();
  const compact = state.labelMode === "all" || roomsToShow.length > 16;

  // Keep zone bubbles visible in overview, or fade/keep them unobtrusive when drilling down
  zoneLabelsGroup.visible = roomsToShow.length === 0 || state.labelMode === "all";

  for (const r of roomsToShow) {
    if (r.uid === state.activeRoomUid) continue; // Active room gets its own elevated golden pin
    if (state.sliceTargetZ !== null && r.pos[2] > state.sliceTargetZ + 0.5) continue; // Hide 3D labels above cutaway floor
    const el = document.createElement("div");
    el.className = `label-room-chip ${compact ? "compact" : ""}`;
    const catCol = CAT_META[r.cat]?.color || "#38bdf8";
    el.style.setProperty("--cat-color", catCol);
    el.textContent = r.short;
    el.title = `${r.zone.shortName} ${r.floor}｜${r.code ? r.code + " " : ""}${r.name}（${r.stairs}）`;
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      focusRoomByUid(r.uid, false);
    });
    const obj = new CSS2DObject(el);
    // Offset slightly outward from wall face so plaques never clip inside building geometry
    const off = faceOutwardVector(r.face, 1.35);
    obj.position.copy(b2t(r.pos[0] + off[0], r.pos[1] + off[1], r.pos[2]));
    roomLabelsGroup.add(obj);
  }
}

function faceOutwardVector(face, dist) {
  switch (face) {
    case "W":
      return [-dist, 0, 0];
    case "E":
      return [dist, 0, 0];
    case "N":
      return [0, dist, 0];
    case "S":
    default:
      return [0, -dist, 0];
  }
}

function clearRoomPin() {
  if (activeRoomPin) {
    scene.remove(activeRoomPin);
    activeRoomPin.element?.remove();
    activeRoomPin = null;
  }
  if (activeRoomBox) {
    scene.remove(activeRoomBox);
    activeRoomBox.traverse((o) => {
      o.geometry?.dispose();
      o.material?.dispose();
    });
    activeRoomBox = null;
  }
  state.activeRoomUid = null;
  document.getElementById("roomInspector").hidden = true;
  clearRouteVisuals();
  state.routeOpen = false;
  state.routeData = null;
  document.getElementById("btnRoomRoute")?.classList.remove("active");
  const emptyEl = document.getElementById("routeEmptyState");
  const activeBodyEl = document.getElementById("routeActiveBody");
  const badgeEl = document.getElementById("tabRouteBadge");
  if (emptyEl) emptyEl.hidden = false;
  if (activeBodyEl) activeBodyEl.hidden = true;
  if (badgeEl) badgeEl.hidden = true;
  if (!state.xrayOn) updateSliceCutaway(null, "");
}

function computeCameraForRoom(room, aerial = false) {
  const [x, y, z] = room.pos;
  const dist = aerial ? 40 : room.zoneId === "Zone_Outdoor" || room.zoneId === "Bldg_Gym_Skybridge" ? 32 : 24;
  const dz = aerial ? 18 : 2.2;
  const off = faceOutwardVector(room.face, dist);
  // Slight oblique angle so facade depth & neighboring plaques read naturally
  const side = room.face === "E" || room.face === "W" ? [0, -6, 0] : [5, 0, 0];
  return {
    camPos: [x + off[0] + side[0], y + off[1] + side[1], Math.max(3.0, z + dz)],
    tgt: [x, y, z],
  };
}

function focusRoomByUid(uid, keepFloorAll = false, openRoute = false) {
  const room = state.allRooms.find((r) => r.uid === uid);
  if (!room) return;

  stopTour();
  clearRoomPin();

  state.selectedZoneId = room.zoneId;
  if (!keepFloorAll) state.selectedFloor = room.floor;
  state.activeRoomUid = room.uid;
  state.roomViewAerial = false;

  applyVisualModes();
  updateFloorBand();

  // Glowing 3D wireframe + translucent room highlight box at exact room coordinates
  const [sx, sy, sz] = room.size;
  const grp = new THREE.Group();
  const geo = new THREE.BoxGeometry(sx, sz, sy);
  const fillMat = new THREE.MeshBasicMaterial({ color: 0xfde047, transparent: true, opacity: 0.25, depthWrite: false });
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0xfde047 }));
  grp.add(new THREE.Mesh(geo, fillMat), edges);
  grp.position.copy(b2t(room.pos[0], room.pos[1], room.pos[2]));
  scene.add(grp);
  activeRoomBox = grp;

  // Elevated active room pin
  const el = document.createElement("div");
  el.className = "label-room-pin";
  const labelTitle = room.code && !room.name.startsWith(room.code) ? `${room.code} ${room.name}` : room.name;
  el.textContent = `📍 ${room.zone.shortName} ${room.floor}｜${labelTitle}`;
  const pin = new CSS2DObject(el);
  const off = faceOutwardVector(room.face, 1.8);
  pin.position.copy(b2t(room.pos[0] + off[0], room.pos[1] + off[1], room.pos[2] + sz * 0.56));
  scene.add(pin);
  activeRoomPin = pin;

  // Update Room Inspector Bar, 3D Wayfinding Route & URL Deep Link Hash
  updateRoomInspector(room);
  renderActiveRoute(room, openRoute);
  applyVisualModes();
  refresh3DLabels();
  renderSidebar();
  syncUrlHash();

  if (openRoute && state.routeData) {
    flyToRouteOverview();
  } else {
    const { camPos, tgt } = computeCameraForRoom(room, false);
    flyTo(camPos, tgt);
  }
}

// --- URL Hash Deep Linking (#room=305, #route=305&from=gate_main&acc=1, or #zone=Bldg_Wuquan&floor=3F) ---
let suppressHashSync = false;

function getRoomSlug(room) {
  return room.code || room.short || room.name;
}

function findRoomBySlug(query) {
  const q = (query || "").trim().toLowerCase();
  if (!q) return null;
  return (
    state.allRooms.find(
      (r) => (r.code && r.code.toLowerCase() === q) || r.short.toLowerCase() === q || r.name.toLowerCase() === q
    ) || state.allRooms.find((r) => r.haystack.includes(q))
  );
}

function syncUrlHash() {
  if (suppressHashSync) return;
  let newHash = "";
  if (state.activeRoomUid) {
    const r = state.allRooms.find((item) => item.uid === state.activeRoomUid);
    if (r) {
      if (state.routeOpen) {
        newHash = `#route=${encodeURIComponent(getRoomSlug(r))}&from=${encodeURIComponent(state.routeStartId)}&acc=${state.routeAccessible ? 1 : 0}`;
      } else {
        newHash = `#room=${encodeURIComponent(getRoomSlug(r))}`;
      }
    }
  } else if (state.selectedZoneId) {
    newHash = `#zone=${encodeURIComponent(state.selectedZoneId)}`;
    if (state.selectedFloor && state.selectedFloor !== "ALL") {
      newHash += `&floor=${encodeURIComponent(state.selectedFloor)}`;
    }
  }
  const curHash = window.location.hash || "";
  if (curHash !== newHash) {
    history.replaceState(null, "", newHash || window.location.pathname + window.location.search);
  }
}

function applyUrlHash() {
  const raw = (window.location.hash || "").replace(/^#/, "").trim();
  if (!raw) return;
  const params = new URLSearchParams(raw);
  const routeQuery = (params.get("route") || "").trim();
  const roomQuery = (params.get("room") || "").trim();
  const fromQuery = (params.get("from") || "").trim();
  const accQuery = (params.get("acc") || "").trim();
  const zoneQuery = (params.get("zone") || "").trim();
  const floorQuery = (params.get("floor") || "").trim();

  suppressHashSync = true;
  try {
    if (routeQuery || roomQuery) {
      const isRouteLink = Boolean(routeQuery);
      if (isRouteLink) {
        if (fromQuery && ROUTE_STARTS.some((s) => s.id === fromQuery)) {
          state.routeStartId = fromQuery;
          const sel = document.getElementById("routeStartSelect");
          if (sel) sel.value = fromQuery;
        }
        if (accQuery === "1" || accQuery === "true") {
          state.routeAccessible = true;
        } else if (accQuery === "0" || accQuery === "false") {
          state.routeAccessible = false;
        }
      }
      const target = findRoomBySlug(routeQuery || roomQuery);
      if (target) {
        focusRoomByUid(target.uid, isRouteLink, isRouteLink);
        return;
      }
    }
    if (zoneQuery && ZONE_META.some((z) => z.id === zoneQuery)) {
      selectZone(zoneQuery, true);
      if (floorQuery) selectFloor(floorQuery);
    }
  } finally {
    suppressHashSync = false;
  }
}

window.addEventListener("hashchange", applyUrlHash);

function updateRoomInspector(room) {
  const bar = document.getElementById("roomInspector");
  const cat = CAT_META[room.cat] || CAT_META.public;
  document.getElementById("riCatBar").style.background = cat.color;
  document.getElementById("riMeta").textContent = `${room.zone.name}・${room.floor}・${cat.label}`;

  const codeEl = document.getElementById("riCode");
  if (room.code) {
    codeEl.textContent = room.code;
    codeEl.hidden = false;
  } else {
    codeEl.hidden = true;
  }
  document.getElementById("riName").textContent = room.name;
  document.getElementById("riStairs").textContent = room.stairs ? `動線：${room.stairs}` : `位置：${room.zone.axisHint}`;
  document.getElementById("btnRoomViewToggle").textContent = state.roomViewAerial ? "🎯 平視" : "🦅 鳥瞰";
  bar.hidden = false;
}

function stepActiveRoom(delta) {
  if (!state.activeRoomUid) return;
  const cur = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (!cur) return;
  const siblings = state.allRooms.filter((r) => r.zoneId === cur.zoneId && r.floor === cur.floor);
  if (siblings.length <= 1) return;
  const idx = siblings.findIndex((r) => r.uid === cur.uid);
  const next = siblings[(idx + delta + siblings.length) % siblings.length];
  focusRoomByUid(next.uid, false);
}

// --- Zone Highlighting & X-Ray Roof Mode ---
function getZoneForMeshName(name) {
  for (const z of ZONE_META) {
    if (z.prefixes.some((p) => name.startsWith(p))) return z;
  }
  return null;
}

function applyVisualModes() {
  for (const mesh of state.allMeshes) {
    const n = mesh.name || "";
    const isRoofOrSolar = n.includes("SolarPanels") || n.includes("SolarFrames") || n.includes("Gym_Roof") || n.includes("Skybridge_Roof");
    mesh.visible = !(state.xrayOn && isRoofOrSolar);

    const orig = state.origMaterials.get(mesh);
    // Keep all buildings solid & crisp when showing multi-building wayfinding route
    if (!state.selectedZoneId || state.routeOpen) {
      mesh.material = orig;
      continue;
    }
    const z = getZoneForMeshName(n);
    const isBaseOrStreet = n.startsWith("Base_") || n.startsWith("Street_") || n.startsWith("Campus_");
    if (isBaseOrStreet || (z && z.id === state.selectedZoneId)) {
      mesh.material = orig;
    } else {
      mesh.material = state.dimMat;
    }
  }
}

function selectZone(zoneId, shouldFly = true) {
  state.selectedZoneId = zoneId;
  state.selectedFloor = "ALL";
  clearRoomPin();
  setSidebarTab("dir");
  if (!state.xrayOn) updateSliceCutaway(null, "");
  applyVisualModes();
  updateFloorBand();
  refresh3DLabels();
  renderSidebar();
  syncUrlHash();
  if (zoneId && shouldFly) {
    const z = ZONE_META.find((item) => item.id === zoneId);
    if (z) flyTo(z.cam.pos, z.cam.tgt);
  }
}

function selectFloor(floorKey) {
  state.selectedFloor = floorKey;
  clearRoomPin();
  if (state.xrayOn && state.selectedZoneId && floorKey !== "ALL") {
    const sZ = getFloorSliceZ(state.selectedZoneId, floorKey);
    updateSliceCutaway(sZ, `${floorKey} 走廊`);
  } else if (!state.xrayOn) {
    updateSliceCutaway(null, "");
  }
  updateFloorBand();
  refresh3DLabels();
  renderSidebar();
  syncUrlHash();
}

// --- Sidebar UI Rendering ---
function renderCategoryPills() {
  const bar = document.getElementById("catFilterBar");
  bar.innerHTML = "";
  for (const key of FILTER_ORDER) {
    const meta = CAT_META[key];
    const btn = document.createElement("button");
    btn.className = `cat-pill ${state.selectedCategory === key ? "active" : ""}`;
    btn.title = meta.label;
    btn.innerHTML =
      key === "all" ? meta.shortLabel : `<span class="cat-dot" style="background:${meta.color}"></span>${meta.shortLabel}`;
    btn.addEventListener("click", () => {
      state.selectedCategory = key;
      clearRoomPin();
      if (key !== "all") {
        state.selectedZoneId = null;
        state.selectedFloor = "ALL";
        applyVisualModes();
        updateFloorBand();
      }
      renderCategoryPills();
      refresh3DLabels();
      renderSidebar();
    });
    bar.appendChild(btn);
  }
}

function renderContextBar() {
  const bar = document.getElementById("contextBar");
  const q = state.searchQuery.trim();
  const hasFilter = q.length > 0 || state.selectedCategory !== "all";

  if (!state.selectedZoneId || hasFilter) {
    bar.hidden = true;
    return;
  }

  const z = ZONE_META.find((item) => item.id === state.selectedZoneId);
  if (!z) {
    bar.hidden = true;
    return;
  }

  const floors = getFloorsForZone(z.id);
  bar.hidden = false;
  bar.innerHTML = `
    <div class="crumb-row">
      <button class="back-btn" id="btnBackZones">← 全區棟別</button>
      <div class="crumb-title"><span class="zone-dot" style="background:${z.color}"></span>${z.name}</div>
    </div>
    <div class="crumb-axis">${z.axisHint}</div>
    <div class="floor-tabs" id="floorTabs"></div>
  `;

  document.getElementById("btnBackZones").addEventListener("click", () => {
    selectZone(null, false);
    flyTo(DEFAULT_VIEW.pos, DEFAULT_VIEW.tgt);
  });

  const tabsEl = document.getElementById("floorTabs");
  const allBtn = document.createElement("button");
  allBtn.className = `floor-tab ${state.selectedFloor === "ALL" ? "active" : ""}`;
  allBtn.textContent = "全棟";
  allBtn.addEventListener("click", () => selectFloor("ALL"));
  tabsEl.appendChild(allBtn);

  for (const fl of floors) {
    const btn = document.createElement("button");
    btn.className = `floor-tab ${state.selectedFloor === fl ? "active" : ""}`;
    btn.textContent = fl;
    btn.addEventListener("click", () => selectFloor(fl));
    tabsEl.appendChild(btn);
  }
}

function renderSidebar() {
  renderContextBar();
  const container = document.getElementById("zoneList");
  container.innerHTML = "";

  const q = state.searchQuery.trim();
  const hasFilter = q.length > 0 || state.selectedCategory !== "all";

  // 1. Cross-building Search or Category Filter View
  if (hasFilter) {
    const hits = getFilteredGlobalRooms();
    const summary = document.createElement("div");
    summary.className = "result-summary";
    const catLabel = state.selectedCategory !== "all" ? `【${CAT_META[state.selectedCategory].label}】` : "";
    summary.innerHTML = `<span>${catLabel}${q ? `「${q}」` : ""} 共找到 <strong>${hits.length}</strong> 處空間（3D 已同步標示）</span>`;
    container.appendChild(summary);

    if (hits.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = "找不到符合的教室或處室。<br/>試試搜尋：<code>305</code>、<code>六6</code>、<code>圖書室</code>、<code>天橋</code>、<code>司令台</code>";
      container.appendChild(empty);
      return;
    }

    for (const r of hits) {
      const cat = CAT_META[r.cat] || CAT_META.public;
      const item = document.createElement("div");
      item.className = `search-result-card ${state.activeRoomUid === r.uid ? "active" : ""}`;
      item.style.setProperty("--cat-color", cat.color);
      item.innerHTML = `
        <div class="sr-main">
          <div class="sr-title">
            ${r.code ? `<span class="room-code">${r.code}</span>` : ""}
            <span>${r.name}</span>
          </div>
          <div class="sr-loc">${r.zone.shortName}・${r.stairs || cat.label}</div>
        </div>
        <div class="sr-right">
          <span class="sr-badge" style="border-left: 3px solid ${r.zone.color}">${r.floor}</span>
          <span class="sr-route-hint">🧭 看路線</span>
        </div>
      `;
      item.addEventListener("click", () => focusRoomByUid(r.uid, true, true));
      container.appendChild(item);
    }
    return;
  }

  // 2. Single-Building Drill-down Floor & Room Grid View
  if (state.selectedZoneId) {
    const z = ZONE_META.find((item) => item.id === state.selectedZoneId);
    if (!z) return;
    const allZoneRooms = getRoomsForZone(z.id);
    const floors = state.selectedFloor === "ALL" ? getFloorsForZone(z.id) : [state.selectedFloor];

    for (const fl of floors) {
      const roomsInFl = allZoneRooms.filter((r) => r.floor === fl);
      if (roomsInFl.length === 0) continue;

      const sec = document.createElement("div");
      sec.className = "floor-section";
      sec.innerHTML = `
        <div class="floor-section-head">
          <div class="floor-section-left">
            <span class="floor-tag">${fl}</span>
            <span class="floor-count">${roomsInFl.length} 處空間</span>
          </div>
        </div>
      `;

      const grid = document.createElement("div");
      grid.className = "room-grid";

      for (const r of roomsInFl) {
        const cat = CAT_META[r.cat] || CAT_META.public;
        const card = document.createElement("button");
        card.type = "button";
        card.className = `room-card ${state.activeRoomUid === r.uid ? "active" : ""}`;
        card.style.setProperty("--cat-color", cat.color);
        card.innerHTML = `
          <div class="room-card-top">
            ${r.code ? `<span class="room-code">${r.code}</span>` : ""}
            <span class="room-name" title="${r.name}">${r.name}</span>
          </div>
          <div class="room-sub">${r.stairs || cat.label}</div>
        `;
        card.addEventListener("click", () => focusRoomByUid(r.uid, false));
        grid.appendChild(card);
      }
      sec.appendChild(grid);
      container.appendChild(sec);
    }

    if (z.stairsInfo) {
      const note = document.createElement("div");
      note.className = "stairs-note";
      note.textContent = z.stairsInfo;
      container.appendChild(note);
    }
    return;
  }

  // 3. Default Compact Campus Overview (6 Zones)
  for (const z of ZONE_META) {
    const cnt = getRoomsForZone(z.id).length;
    const card = document.createElement("div");
    card.className = "zone-card";
    card.style.setProperty("--zone-color", z.color);
    card.innerHTML = `
      <div class="zone-head">
        <span class="zone-name"><span class="zone-dot" style="background:${z.color}"></span>${z.name}</span>
        <span class="zone-badge">${z.badge}</span>
      </div>
      <div class="zone-meta-line">
        <span class="zone-summary">${z.summary}</span>
        <span class="zone-count">${cnt} 空間 ›</span>
      </div>
    `;
    card.addEventListener("click", () => selectZone(z.id, true));
    container.appendChild(card);
  }
}

// --- 3D Ruler Tool ---
const rulerGroup = new THREE.Group();
scene.add(rulerGroup);
let rulerLabelObj = null;

function clearRuler() {
  state.rulerPts = [];
  while (rulerGroup.children.length) rulerGroup.remove(rulerGroup.children[0]);
  if (rulerLabelObj) {
    rulerLabelObj.element?.remove();
    rulerLabelObj = null;
  }
  document.getElementById("rulerDist").textContent = "等待第一點";
}

function addRulerPoint(pt) {
  if (state.rulerPts.length >= 2) clearRuler();
  state.rulerPts.push(pt.clone());

  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.42, 12, 12),
    new THREE.MeshBasicMaterial({ color: 0x34d399 })
  );
  dot.position.copy(pt);
  rulerGroup.add(dot);

  if (state.rulerPts.length === 1) {
    document.getElementById("rulerDist").textContent = "已選起點，請點第二點";
  } else {
    const [p1, p2] = state.rulerPts;
    const dist = p1.distanceTo(p2);
    const geo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
    const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0x34d399 }));
    rulerGroup.add(line);

    const el = document.createElement("div");
    el.className = "label-ruler";
    el.textContent = `📏 ${dist.toFixed(1)} 公尺`;
    rulerLabelObj = new CSS2DObject(el);
    rulerLabelObj.position.copy(p1.clone().add(p2).multiplyScalar(0.5)).add(new THREE.Vector3(0, 1.2, 0));
    rulerGroup.add(rulerLabelObj);
    document.getElementById("rulerDist").textContent = `實測距離：${dist.toFixed(2)} 公尺`;
  }
}

// --- Guided Tour Controller ---
function showTourStop(idx) {
  state.tourIndex = (idx + GUIDED_TOUR.length) % GUIDED_TOUR.length;
  const stop = GUIDED_TOUR[state.tourIndex];
  document.getElementById("tourStepBadge").textContent = `自動導覽 第 ${state.tourIndex + 1} / ${GUIDED_TOUR.length} 站`;
  document.getElementById("tourTitle").textContent = stop.title;
  document.getElementById("tourDesc").textContent = stop.desc;
  state.selectedZoneId = stop.zoneId;
  state.selectedFloor = "ALL";
  clearRoomPin();
  applyVisualModes();
  updateFloorBand();
  refresh3DLabels();
  renderSidebar();
  flyTo(stop.pos, stop.tgt);
}

function scheduleNextTourStop() {
  if (state.tourTimer) clearInterval(state.tourTimer);
  if (state.tourActive && state.tourPlaying) {
    state.tourTimer = setInterval(() => showTourStop(state.tourIndex + 1), 6500);
  }
}

function startTour() {
  clearRoomPin();
  state.tourActive = true;
  state.tourPlaying = true;
  document.getElementById("tourCard").classList.add("show");
  document.getElementById("btnTourPlayPause").textContent = "⏸ 暫停輪播";
  document.getElementById("btnStartTour").classList.add("active");
  showTourStop(0);
  scheduleNextTourStop();
}

function stopTour() {
  state.tourActive = false;
  if (state.tourTimer) clearInterval(state.tourTimer);
  document.getElementById("tourCard").classList.remove("show");
  document.getElementById("btnStartTour").classList.remove("active");
}

// --- Pointer Raycasting (Click 3D Building / Ruler) ---
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downPos = { x: 0, y: 0 };

renderer.domElement.addEventListener("pointerdown", (e) => {
  downPos = { x: e.clientX, y: e.clientY };
});

renderer.domElement.addEventListener("pointerup", (e) => {
  if (e.button !== 0) return;
  if (Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y) > 5) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const hits = raycaster.intersectObjects(state.allMeshes, false);
  if (state.rulerMode) {
    if (hits.length > 0) addRulerPoint(hits[0].point);
    return;
  }
  if (hits.length > 0) {
    const z = getZoneForMeshName(hits[0].object.name);
    if (z) {
      selectZone(z.id, true);
      return;
    }
  }
});

// --- UI Bindings ---
document.getElementById("btnCollapse").addEventListener("click", () => {
  document.getElementById("sidebar").classList.add("collapsed");
  updateCameraViewportOffset();
});
document.getElementById("btnExpand").addEventListener("click", () => {
  document.getElementById("sidebar").classList.remove("collapsed");
  updateCameraViewportOffset();
});

const searchInput = document.getElementById("roomSearch");
const clearSearchBtn = document.getElementById("btnClearSearch");

searchInput.addEventListener("input", (e) => {
  state.searchQuery = e.target.value;
  clearSearchBtn.hidden = state.searchQuery.length === 0;
  refresh3DLabels();
  renderSidebar();
});

clearSearchBtn.addEventListener("click", () => {
  state.searchQuery = "";
  searchInput.value = "";
  clearSearchBtn.hidden = true;
  refresh3DLabels();
  renderSidebar();
  searchInput.focus();
});

document.getElementById("btnResetAll").addEventListener("click", () => {
  stopTour();
  state.searchQuery = "";
  searchInput.value = "";
  clearSearchBtn.hidden = true;
  state.selectedCategory = "all";
  renderCategoryPills();
  selectZone(null, false);
  flyTo(DEFAULT_VIEW.pos, DEFAULT_VIEW.tgt);
});

const LABEL_MODE_CYCLE = [
  { mode: "smart", text: "🏷 智慧", active: true },
  { mode: "all", text: "🏷 全校", active: true },
  { mode: "off", text: "🏷 隱藏", active: false },
];

document.getElementById("btnLabelMode").addEventListener("click", (e) => {
  const curIdx = LABEL_MODE_CYCLE.findIndex((x) => x.mode === state.labelMode);
  const nxt = LABEL_MODE_CYCLE[(curIdx + 1) % LABEL_MODE_CYCLE.length];
  state.labelMode = nxt.mode;
  e.currentTarget.textContent = nxt.text;
  e.currentTarget.classList.toggle("active", nxt.active);
  refresh3DLabels();
});

document.getElementById("tabDir").addEventListener("click", () => setSidebarTab("dir"));
document.getElementById("tabRoute").addEventListener("click", () => setSidebarTab("route"));

document.getElementById("btnXray").addEventListener("click", () => {
  if (state.sliceTargetZ !== null && !state.xrayOn) {
    // Restore full building if currently floor-sliced
    state.autoSliceRoute = false;
    document.getElementById("btnRouteSliceAuto")?.classList.remove("active");
    updateSliceCutaway(null, "", false);
  } else {
    state.xrayOn = !state.xrayOn;
    if (state.xrayOn && state.selectedZoneId && state.selectedFloor !== "ALL") {
      const sZ = getFloorSliceZ(state.selectedZoneId, state.selectedFloor);
      updateSliceCutaway(sZ, `${state.selectedFloor} 走廊`, false);
    } else if (state.xrayOn && state.routeOpen && state.routeData?.destZoneId && state.routeData.destZoneId !== "Zone_Outdoor") {
      state.autoSliceRoute = true;
      document.getElementById("btnRouteSliceAuto")?.classList.add("active");
      const sZ = getFloorSliceZ(state.routeData.destZoneId, state.routeData.destFloor);
      updateSliceCutaway(sZ, `${state.routeData.destFloor}F 走廊`, false);
    } else if (!state.xrayOn) {
      updateSliceCutaway(null, "", false);
    } else {
      updateSliceCutaway(null, "", false);
    }
  }
  applyVisualModes();
  requestShadowUpdate();
});

document.getElementById("btnRuler").addEventListener("click", (e) => {
  state.rulerMode = !state.rulerMode;
  e.currentTarget.classList.toggle("active", state.rulerMode);
  document.getElementById("rulerBanner").classList.toggle("show", state.rulerMode);
  if (!state.rulerMode) clearRuler();
});
document.getElementById("btnClearRuler").addEventListener("click", clearRuler);
document.querySelectorAll("[data-sun]").forEach((btn) => btn.addEventListener("click", () => applySun(btn.dataset.sun)));

// Room Inspector & Integrated Wayfinding Tab Actions
document.getElementById("btnRoomPrev").addEventListener("click", () => stepActiveRoom(-1));
document.getElementById("btnRoomNext").addEventListener("click", () => stepActiveRoom(1));
document.getElementById("btnRoomRoute").addEventListener("click", () => {
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (!room) return;
  if (state.routeOpen && state.sidebarTab === "route") {
    state.routeOpen = false;
    setSidebarTab("dir");
    renderActiveRoute(room, false);
    if (!state.xrayOn) updateSliceCutaway(null, "");
  } else {
    state.routeOpen = true;
    renderActiveRoute(room, true);
    flyToRouteOverview();
  }
  applyVisualModes();
  syncUrlHash();
});
document.getElementById("btnCloseRoute").addEventListener("click", () => {
  state.routeOpen = false;
  clearRouteVisuals();
  document.getElementById("btnRoomRoute")?.classList.remove("active");
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  renderActiveRoute(room, false);
  setSidebarTab("dir");
  if (!state.xrayOn) updateSliceCutaway(null, "");
  applyVisualModes();
  syncUrlHash();
});

document.querySelectorAll("[data-quick-room]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const q = btn.dataset.quickRoom;
    const target = findRoomBySlug(q);
    if (target) focusRoomByUid(target.uid, true, true);
  });
});

const routeStartSelect = document.getElementById("routeStartSelect");
for (const st of ROUTE_STARTS) {
  const opt = document.createElement("option");
  opt.value = st.id;
  opt.textContent = st.shortLabel;
  routeStartSelect.appendChild(opt);
}
routeStartSelect.value = state.routeStartId;
routeStartSelect.addEventListener("change", (e) => {
  state.routeStartId = e.target.value;
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (room) {
    renderActiveRoute(room, true);
    flyToRouteOverview();
    syncUrlHash();
  }
});

document.getElementById("btnRouteAccess").addEventListener("click", () => {
  state.routeAccessible = !state.routeAccessible;
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (room) {
    renderActiveRoute(room, true);
    flyToRouteOverview();
    syncUrlHash();
  }
});
document.getElementById("btnRouteSliceAuto")?.addEventListener("click", (e) => {
  state.autoSliceRoute = !state.autoSliceRoute;
  e.currentTarget.classList.toggle("active", state.autoSliceRoute);
  if (state.autoSliceRoute && state.routeData?.destZoneId && state.routeData.destZoneId !== "Zone_Outdoor") {
    const sZ = getFloorSliceZ(state.routeData.destZoneId, state.routeData.destFloor);
    updateSliceCutaway(sZ, `${state.routeData.destFloor}F 走廊`);
  } else if (!state.autoSliceRoute && !state.xrayOn) {
    updateSliceCutaway(null, "");
  }
});
document.getElementById("btnRouteOverview").addEventListener("click", flyToRouteOverview);
document.getElementById("btnRouteFlyAlong").addEventListener("click", (e) => {
  if (!routeCurve) return;
  state.routeFlyAlong = !state.routeFlyAlong;
  if (state.routeFlyAlong) {
    state.routeFlyProgress = 0;
    tweenPos = null;
    tweenTgt = null;
    e.currentTarget.textContent = "⏸ 暫停實境";
    e.currentTarget.classList.add("active");
    requestRender(20);
  } else {
    stopRouteFlyAlong();
  }
});

async function copyShareUrlWithFeedback(btn, promptMsg) {
  syncUrlHash();
  const shareUrl = window.location.href;
  try {
    await navigator.clipboard.writeText(shareUrl);
    const orig = btn.textContent;
    btn.textContent = "✓ 已複製";
    setTimeout(() => {
      btn.textContent = orig;
    }, 1800);
  } catch (_) {
    window.prompt(promptMsg, shareUrl);
  }
}

document.getElementById("btnRouteShare")?.addEventListener("click", (e) => {
  copyShareUrlWithFeedback(e.currentTarget, "複製此到達路線 3D 導覽連結：");
});
document.getElementById("btnRoomViewToggle").addEventListener("click", () => {
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (!room) return;
  state.roomViewAerial = !state.roomViewAerial;
  document.getElementById("btnRoomViewToggle").textContent = state.roomViewAerial ? "🎯 平視" : "🦅 鳥瞰";
  const { camPos, tgt } = computeCameraForRoom(room, state.roomViewAerial);
  flyTo(camPos, tgt);
});
document.getElementById("btnRoomShare").addEventListener("click", (e) => {
  copyShareUrlWithFeedback(e.currentTarget, "複製此 3D 校園導覽連結：");
});
document.getElementById("btnCloseInspector").addEventListener("click", () => {
  clearRoomPin();
  refresh3DLabels();
  renderSidebar();
  syncUrlHash();
});

// Guided Tour Buttons
document.getElementById("btnStartTour").addEventListener("click", () => (state.tourActive ? stopTour() : startTour()));
document.getElementById("btnCloseTour").addEventListener("click", stopTour);
document.getElementById("btnTourPrev").addEventListener("click", () => {
  showTourStop(state.tourIndex - 1);
  scheduleNextTourStop();
});
document.getElementById("btnTourNext").addEventListener("click", () => {
  showTourStop(state.tourIndex + 1);
  scheduleNextTourStop();
});
document.getElementById("btnTourPlayPause").addEventListener("click", (e) => {
  state.tourPlaying = !state.tourPlaying;
  e.currentTarget.textContent = state.tourPlaying ? "⏸ 暫停輪播" : "▶ 繼續輪播";
  e.currentTarget.classList.toggle("active", state.tourPlaying);
  scheduleNextTourStop();
});

// Official 115 Classroom Layout Modal (On-Demand Lazy Load saves 325KB on initial boot!)
const mapModal = document.getElementById("mapModal");
const mapModalImg = document.getElementById("mapModalImg");
const openMapModal = () => {
  if (!mapModalImg.getAttribute("src") && mapModalImg.dataset.src) {
    mapModalImg.src = mapModalImg.dataset.src;
  }
  mapModal.hidden = false;
  mapModalImg.classList.remove("zoomed");
};
const closeMapModal = () => {
  mapModal.hidden = true;
};
document.getElementById("btnOpenMap").addEventListener("click", openMapModal);
document.getElementById("btnCloseMapModal").addEventListener("click", closeMapModal);
document.getElementById("mapModalBackdrop").addEventListener("click", closeMapModal);
mapModalImg.addEventListener("click", () => mapModalImg.classList.toggle("zoomed"));
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !mapModal.hidden) closeMapModal();
});

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  updateCameraViewportOffset();
  renderer.setSize(window.innerWidth, window.innerHeight);
  labelRenderer.setSize(window.innerWidth, window.innerHeight);
  requestRender(6);
});

const GROUND_ONLY_RECEIVE_PATTERNS = [
  "Base_CampusPaving",
  "Base_Road",
  "Base_GuangheSidewalk",
  "Base_GuangheCurbs",
  "Base_NWCorner",
  "Base_GateCurb",
  "Base_GatePedestrian",
  "Base_GateApron",
  "Base_GateThreshold",
  "Base_ForecourtPlaza",
  "Base_Manhole",
  "Base_RectHandhole",
  "Base_CurbDrain",
  "Zone_Track_PU",
  "Zone_Track_Lines",
  "Zone_Track_InfieldGrass",
  "Zone_Track_EastWalkway",
  "Zone_Track_EastFitnessPads",
  "Zone_Track_NorthMintApron",
  "Zone_Track_NorthBasketballCourt",
  "Zone_Track_NorthCourtLine",
  "Zone_Track_NorthSoilStrip",
  "Zone_Courtyard_Lawns",
  "Zone_Courtyard_PondWater",
  "Zone_Basketball_Court",
  "Zone_Basketball_Deck",
  "Zone_Basketball_Walkway",
  "Zone_Basketball_Drain",
];

// --- Load Spec & Compressed GLB (with Build-Hash Cache, Progress Bar & Draco Decoder) ---
async function init() {
  let buildHash = "12.7";
  let expectedGlbBytes = 5349084;
  try {
    const metaRes = await fetch("./build_meta.json");
    if (metaRes.ok) {
      const meta = await metaRes.json();
      if (meta?.hash) buildHash = `${meta.version || "12.7"}-${meta.hash}`;
      if (meta?.glb_bytes) expectedGlbBytes = meta.glb_bytes;
    }
  } catch (_) {
    // Fallback to static version string
  }

  try {
    const res = await fetch(`./campus_cges.json?v=${buildHash}`);
    state.spec = await res.json();
    if (Array.isArray(state.spec?.zones) && state.spec.zones.length > 0) {
      ZONE_META = state.spec.zones;
    }
  } catch (e) {
    console.warn("Spec load failed:", e);
  }
  hydrateAllRooms();
  buildZoneLabels();
  renderCategoryPills();
  refresh3DLabels();
  renderSidebar();
  applyUrlHash();
  requestRender(12);

  const statusTextEl = document.getElementById("statusText");
  const statusPctEl = document.getElementById("statusPct");
  const statusBarEl = document.getElementById("statusBar");

  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  const dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath("./vendor/three/examples/jsm/libs/draco/gltf/");
  const loader = new GLTFLoader();
  loader.setDRACOLoader(dracoLoader);
  loader.load(
    `./exports/cges_campus.glb?v=${buildHash}`,
    (gltf) => {
      if (statusPctEl) statusPctEl.textContent = "100%";
      if (statusBarEl) statusBarEl.style.width = "100%";
      state.rootModel = gltf.scene;
      gltf.scene.traverse((obj) => {
        if (obj.isMesh) {
          const isGroundDecal = GROUND_ONLY_RECEIVE_PATTERNS.some((p) => obj.name.startsWith(p));
          obj.castShadow = !isGroundDecal;
          obj.receiveShadow = true;
          const canSlice = isSliceableBuildingMesh(obj.name);
          const wrapSliceMat = (m) => {
            if (!m || !canSlice) return m;
            let cm = clippedMatCache.get(m);
            if (!cm) {
              cm = m.clone();
              cm.clippingPlanes = [floorClipPlane];
              cm.clipShadows = false;
              clippedMatCache.set(m, cm);
            }
            return cm;
          };
          obj.material = Array.isArray(obj.material) ? obj.material.map(wrapSliceMat) : wrapSliceMat(obj.material);
          state.allMeshes.push(obj);
          state.origMaterials.set(obj, obj.material);
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          for (const m of mats) {
            if (m?.map) m.map.anisotropy = Math.min(16, maxAniso);
            if (m?.normalMap) m.normalMap.anisotropy = Math.min(16, maxAniso);
          }
        }
      });
      scene.add(gltf.scene);
      applyVisualModes();
      statusEl.remove();
      dracoLoader.dispose();
      requestShadowUpdate();
    },
    (xhr) => {
      const total = xhr.total > 0 ? xhr.total : expectedGlbBytes;
      const pct = Math.min(99, Math.max(1, Math.round((xhr.loaded / total) * 100)));
      if (statusPctEl) statusPctEl.textContent = `${pct}%`;
      if (statusBarEl) statusBarEl.style.width = `${pct}%`;
      if (statusTextEl) statusTextEl.textContent = "載入重慶國小 3D 實景模型中…";
    },
    (err) => {
      console.error(err);
      if (statusTextEl) statusTextEl.textContent = "載入模型失敗：" + err.message;
      else statusEl.textContent = "載入模型失敗：" + err.message;
    }
  );
}

const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  let needsDraw = renderFramesLeft > 0;
  if (renderFramesLeft > 0) renderFramesLeft--;

  if (activeRoomBox) {
    const t = clock.getElapsedTime();
    const fill = activeRoomBox.children[0];
    if (fill?.material) fill.material.opacity = 0.18 + 0.1 * Math.sin(t * 4.0);
    needsDraw = true;
  }
  // Smoothly animate horizontal floor cutaway clipping plane
  const goalSlice = state.sliceTargetZ !== null ? state.sliceTargetZ : 999;
  if (Math.abs(state.sliceCurrentZ - goalSlice) > 0.03) {
    if (goalSlice > 100 || state.sliceCurrentZ > 100) {
      state.sliceCurrentZ = goalSlice;
    } else {
      state.sliceCurrentZ += (goalSlice - state.sliceCurrentZ) * 0.16;
    }
    floorClipPlane.constant = state.sliceCurrentZ;
    needsDraw = true;
  }

  if (routeCurve && routePulseOrb) {
    const len = routeCurve.getLength();
    const duration = Math.max(4.5, len / 18.0);
    const u = ((clock.getElapsedTime() % duration) / duration);
    const pt = routeCurve.getPointAt(u);
    routePulseOrb.position.copy(pt);
    needsDraw = true;

    if (state.routeFlyAlong) {
      const stepDelta = Math.max(0.0022, Math.min(0.0042, 0.36 / Math.max(45, len)));
      state.routeFlyProgress = Math.min(1, state.routeFlyProgress + stepDelta);
      const uCam = state.routeFlyProgress;
      const curP = routeCurve.getPointAt(uCam);
      const aheadU = Math.min(1, uCam + 0.055);
      const aheadP = routeCurve.getPointAt(aheadU);

      // Dynamically adjust building cutaway as the walk climbs stairs & enters target floor corridor
      if (state.autoSliceRoute && state.routeData?.destZoneId && state.routeData.destZoneId !== "Zone_Outdoor") {
        const walkZ = curP.y; // Three.js Y === Blender Z
        if (walkZ > 1.05 || uCam > 0.28) {
          const liveSlice = Math.max(3.6, walkZ + 2.75);
          state.sliceTargetZ = liveSlice;
          state.sliceCurrentZ += (liveSlice - state.sliceCurrentZ) * 0.14;
          floorClipPlane.constant = state.sliceCurrentZ;
        }
      }

      const tan = aheadP.clone().sub(curP);
      if (tan.lengthSq() < 0.01) tan.set(1, 0, 0);
      tan.y = 0;
      if (tan.lengthSq() < 0.001) tan.set(0, 0, -1);
      tan.normalize();

      const inCorridor = curP.y > 1.05;
      const backDist = inCorridor ? 7.2 : 11.5;
      const upHeight = inCorridor ? 4.1 : 6.0;
      const desiredPos = curP.clone().addScaledVector(tan, -backDist).add(new THREE.Vector3(0, upHeight, 0));
      camera.position.lerp(desiredPos, 0.085);
      controls.target.lerp(aheadP.clone().add(new THREE.Vector3(0, 0.5, 0)), 0.12);
      if (state.routeFlyProgress >= 1) {
        stopRouteFlyAlong();
      }
    }
  }
  if (tweenPos && tweenTgt) {
    camera.position.lerp(tweenPos, 0.085);
    controls.target.lerp(tweenTgt, 0.085);
    needsDraw = true;
    if (camera.position.distanceTo(tweenPos) < 0.22) {
      tweenPos = null;
      tweenTgt = null;
      requestRender(4);
    }
  }
  if (controls.update()) {
    needsDraw = true;
  }
  if (needsDraw) {
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
  }
}

init();
animate();
