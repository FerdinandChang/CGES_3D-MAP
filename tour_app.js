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

const ZONE_META = [
  {
    id: "Bldg_Guanghe",
    name: "廣和樓（行政大樓）",
    shortName: "廣和樓",
    badge: "5F・行政",
    color: "#ef4444",
    prefixes: ["Bldg_Guanghe_"],
    summary: "校長室・各處室・視聽中心・11階穿堂",
    axisHint: "由北 → 南排列｜面對廣和街主校門",
    stairsInfo: "樓梯／電梯：3梯（北側）｜4梯（南側）｜電梯（1F–5F 南側無障礙）",
    bounds: { x0: -53.5, x1: -31.5, y0: -10.5, y1: 11.5, h1: 4.2, hu: 3.4 },
    labelPos: [-42.5, 0.5, 22.8],
    cam: { pos: [-88, -3, 14], tgt: [-42, 0.5, 9.2] },
  },
  {
    id: "Bldg_Heping",
    name: "和平樓（北翼校舍）",
    shortName: "和平樓",
    badge: "5F・北翼",
    color: "#38bdf8",
    prefixes: ["Bldg_Heping_", "Landmark_CornerTowers_"],
    summary: "一/三/五/六年級・優學・幼兒園・海豚天橋",
    axisHint: "由東 → 西排列｜1梯 2F 直連海豚天橋",
    stairsInfo: "樓梯：1梯（東中段・2F 通往體育館海豚天橋）｜2梯（西側）",
    bounds: { x0: -60.5, x1: -7.0, y0: 25.5, y1: 39.0, h1: 3.6, hu: 3.4 },
    labelPos: [-34.0, 32.0, 22.8],
    cam: { pos: [-35, -8, 20], tgt: [-33, 28, 9.2] },
  },
  {
    id: "Bldg_Wuquan",
    name: "五權樓（東側主棟）",
    shortName: "五權樓",
    badge: "5F・主棟",
    color: "#34d399",
    prefixes: ["Bldg_Wuquan_", "Landmark_CornerTowers_"],
    summary: "各年級・電腦/美勞/英語・穿堂連建司令台",
    axisHint: "由北 → 南排列｜1F 穿堂東接升旗司令台",
    stairsInfo: "樓梯：9梯（北端・近和平樓）｜8梯（南端・近 3號大後門）",
    bounds: { x0: -7.0, x1: 6.5, y0: -67.0, y1: 39.5, h1: 3.6, hu: 3.4 },
    labelPos: [0.0, -14.0, 22.8],
    cam: { pos: [122, -20, 28], tgt: [4, -18, 9.5] },
  },
  {
    id: "Bldg_Chongqing",
    name: "重慶樓（南翼校舍）",
    shortName: "重慶樓",
    badge: "5F・南翼",
    color: "#f59e0b",
    prefixes: ["Bldg_Chongqing_", "Landmark_SouthCorner_"],
    summary: "二/四年級・208 圖書室・自然/音樂/英語",
    axisHint: "由東 → 西排列｜南臨露天雙籃球場",
    stairsInfo: "樓梯：7梯（東端接五權樓）｜6梯（中段）｜5梯（西端近廣和街）",
    bounds: { x0: -74.0, x1: -7.0, y0: -43.0, y1: -29.5, h1: 3.6, hu: 3.4 },
    labelPos: [-42.0, -36.0, 22.8],
    cam: { pos: [-44, -84, 19], tgt: [-42, -38, 9.0] },
  },
  {
    id: "Bldg_Gym_Skybridge",
    name: "運動中心＆海豚天橋",
    shortName: "運動中心",
    badge: "體育館＋空橋",
    color: "#60a5fa",
    prefixes: ["Bldg_Gym_", "Landmark_Skybridge_"],
    summary: "室內溫水游泳池・綜合球場・跨和平路空橋",
    axisHint: "位於和平路北側｜2F 海豚空橋直連和平樓",
    stairsInfo: "動線：和平樓 2F 1梯出口直行海豚天橋，或由和平路前庭階梯進出",
    labelPos: [-34.5, 86.0, 17.5],
    cam: { pos: [2, 34, 12], tgt: [-32, 68, 7.5] },
    extraDetailed: [
      { floor: "3F", code: "3F", name: "綜合室內球場", short: "綜合室內球場", cat: "special", pos: [-34.5, 86.0, 10.6], size: [26, 26, 4.2], face: "S", stairs: "運動中心 3F 主場館" },
      { floor: "3F", code: "3F", name: "看台與玻璃金字塔天窗", short: "看台・天窗", cat: "public", pos: [-46.0, 74.0, 11.8], size: [12, 10, 3.6], face: "S", stairs: "屋頂四座採光天窗" },
      { floor: "2F", code: "2F", name: "跨和平路海豚彩繪人行天橋", short: "海豚彩繪空橋", cat: "public", pos: [-17.5, 52.0, 6.2], size: [4.6, 24.0, 3.2], face: "E", stairs: "連接和平樓 2F 1梯與運動中心" },
      { floor: "2F", code: "2F", name: "運動中心主入口大廳", short: "主入口大廳", cat: "public", pos: [-26.0, 66.0, 5.8], size: [14, 6, 3.6], face: "S", stairs: "海豚天橋直達・前庭寬階梯" },
      { floor: "2F", code: "2F", name: "韻律／體適能中心", short: "韻律體適能", cat: "special", pos: [-44.0, 66.0, 5.8], size: [12, 6, 3.6], face: "S", stairs: "2F 西側" },
      { floor: "1F", code: "1F", name: "室內溫水游泳池", short: "室內游泳池", cat: "special", pos: [-34.5, 82.0, 2.2], size: [22, 18, 3.6], face: "S", stairs: "運動中心 1F" },
      { floor: "1F", code: "1F", name: "前庭入口與階梯廣場", short: "運動中心前庭", cat: "public", pos: [-34.5, 64.5, 2.0], size: [24, 6, 3.2], face: "S", stairs: "和平路北側臨路入口" },
    ],
  },
  {
    id: "Zone_Outdoor",
    name: "操場・籃球場・生態池・校門",
    shortName: "戶外空間",
    badge: "運動與景觀",
    color: "#a3e635",
    prefixes: ["Zone_Track_", "Zone_Basketball_", "Zone_Courtyard_", "Zone_Playground_", "Landmark_MainGate_", "Landmark_SouthWall_"],
    summary: "200m 跑道・連建司令台・雙籃球場・生態池",
    axisHint: "四大戶外活動分區｜含三處主要出入口",
    stairsInfo: "出入口：廣和街31號正門（西）｜廣和街 3號大後門（南）｜147B 操場側門（北）",
    labelPos: [42.0, -12.0, 7.5],
    cam: { pos: [88, -68, 46], tgt: [16, -16, 4] },
    extraDetailed: [
      { floor: "東側", code: "", name: "升旗司令台（五權樓連建式）", short: "升旗司令台", cat: "public", pos: [9.8, -13.75, 2.8], size: [5.5, 19.0, 5.4], face: "E", stairs: "連建於五權樓 1F 穿堂與 2F 露台" },
      { floor: "東側", code: "", name: "不鏽鋼爬竿架＆高低單槓體健區", short: "爬竿・高低單槓", cat: "special", pos: [68.2, -32.0, 1.8], size: [4.0, 38.0, 3.6], face: "W", stairs: "跑道東側五權街圍牆內樹蔭帶" },
      { floor: "東側", code: "", name: "200m 六跑道紅 PU 操場", short: "200m PU 跑道", cat: "special", pos: [42.0, -12.0, 1.0], size: [42, 86, 2.0], face: "E", stairs: "五權樓東側灰色透水磚大道" },
      { floor: "東側", code: "", name: "中央草坪足球場", short: "草坪足球場", cat: "special", pos: [42.0, -12.0, 1.0], size: [24, 52, 2.0], face: "E", stairs: "跑道內圈中央" },
      { floor: "中庭", code: "", name: "生態水生植物池＆拱形小木橋", short: "生態水生池", cat: "public", pos: [-18.5, 16.5, 1.4], size: [14, 10, 2.4], face: "S", stairs: "四棟校舍合圍之北中庭" },
      { floor: "中庭", code: "", name: "酒瓶椰子中庭花園", short: "中庭花園", cat: "public", pos: [-22.0, -16.5, 1.4], size: [22, 16, 2.4], face: "S", stairs: "廣和樓穿堂東側直達" },
      { floor: "南側", code: "", name: "露天薄荷綠雙籃球場", short: "雙籃球場", cat: "special", pos: [-27.0, -55.5, 1.8], size: [36, 22, 3.2], face: "S", stairs: "重慶樓南側・無內側圍欄開闊連通" },
      { floor: "南側", code: "", name: "廣和街 3號大後門（學童接送區）", short: "3號大後門", cat: "public", pos: [12.5, -69.8, 1.8], size: [8.0, 3.2, 3.2], face: "S", stairs: "緊鄰五權樓 8梯・直通操場與椰林" },
      { floor: "南側", code: "", name: "兒童遊戲場＆花磚馬賽克圍牆", short: "兒童遊戲場", cat: "public", pos: [-56.0, -58.0, 1.8], size: [14, 12, 3.0], face: "S", stairs: "西南角重慶樓南側" },
      { floor: "西側", code: "", name: "廣和街 31 號主校門＆半圓拱警衛室", short: "主校門・警衛室", cat: "public", pos: [-69.5, 2.8, 3.0], size: [8.0, 16.0, 6.2], face: "W", stairs: "正對廣和樓 11 階寬階梯穿堂" },
      { floor: "西側", code: "", name: "前庭紅磚廣場＆幼童車接送區", short: "前庭廣場", cat: "public", pos: [-61.0, 0.5, 1.2], size: [12, 22, 2.2], face: "W", stairs: "主校門內側" },
      { floor: "北側", code: "", name: "東北角雙半場籃球場＆涼亭", short: "北側雙半場籃球場", cat: "special", pos: [48.3, 40.2, 1.8], size: [26.0, 13.0, 3.4], face: "S", stairs: "100m 延長跑道東側" },
      { floor: "北側", code: "", name: "和平路 B1 雙鐵捲門通道", short: "B1 雙鐵捲門", cat: "public", pos: [1.2, 41.5, 2.0], size: [10.0, 4.5, 3.4], face: "N", stairs: "五權樓北牆 1F（147 和平路）" },
      { floor: "北側", code: "", name: "147B 操場側門＆公車亭", short: "147B 操場側門", cat: "public", pos: [8.7, 47.0, 2.0], size: [6.0, 4.0, 3.0], face: "N", stairs: "和平路北側・操場西北角" },
    ],
  },
];

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
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.04;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;
wrap.appendChild(renderer.domElement);

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
};

function updateCameraViewportOffset() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const sidebarEl = document.getElementById("sidebar");
  const isCollapsed = sidebarEl?.classList.contains("collapsed");
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

function focusRoomByUid(uid, keepFloorAll = false) {
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

  // Update Room Inspector Bar
  updateRoomInspector(room);
  refresh3DLabels();
  renderSidebar();

  const { camPos, tgt } = computeCameraForRoom(room, false);
  flyTo(camPos, tgt);
}

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
    if (!state.selectedZoneId) {
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
  applyVisualModes();
  updateFloorBand();
  refresh3DLabels();
  renderSidebar();
  if (zoneId && shouldFly) {
    const z = ZONE_META.find((item) => item.id === zoneId);
    if (z) flyTo(z.cam.pos, z.cam.tgt);
  }
}

function selectFloor(floorKey) {
  state.selectedFloor = floorKey;
  clearRoomPin();
  updateFloorBand();
  refresh3DLabels();
  renderSidebar();
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
        <span class="sr-badge" style="border-left: 3px solid ${r.zone.color}">${r.floor}</span>
      `;
      item.addEventListener("click", () => focusRoomByUid(r.uid, true));
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
  { mode: "smart", text: "🏷 標牌：智慧", active: true },
  { mode: "all", text: "🏷 標牌：全校教室", active: true },
  { mode: "off", text: "🏷 標牌：隱藏", active: false },
];

document.getElementById("btnLabelMode").addEventListener("click", (e) => {
  const curIdx = LABEL_MODE_CYCLE.findIndex((x) => x.mode === state.labelMode);
  const nxt = LABEL_MODE_CYCLE[(curIdx + 1) % LABEL_MODE_CYCLE.length];
  state.labelMode = nxt.mode;
  e.currentTarget.textContent = nxt.text;
  e.currentTarget.classList.toggle("active", nxt.active);
  refresh3DLabels();
});

document.getElementById("btnXray").addEventListener("click", (e) => {
  state.xrayOn = !state.xrayOn;
  e.currentTarget.classList.toggle("active", state.xrayOn);
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

// Room Inspector Actions
document.getElementById("btnRoomPrev").addEventListener("click", () => stepActiveRoom(-1));
document.getElementById("btnRoomNext").addEventListener("click", () => stepActiveRoom(1));
document.getElementById("btnRoomViewToggle").addEventListener("click", () => {
  const room = state.allRooms.find((r) => r.uid === state.activeRoomUid);
  if (!room) return;
  state.roomViewAerial = !state.roomViewAerial;
  document.getElementById("btnRoomViewToggle").textContent = state.roomViewAerial ? "🎯 平視" : "🦅 鳥瞰";
  const { camPos, tgt } = computeCameraForRoom(room, state.roomViewAerial);
  flyTo(camPos, tgt);
});
document.getElementById("btnCloseInspector").addEventListener("click", () => {
  clearRoomPin();
  refresh3DLabels();
  renderSidebar();
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

// Official 115 Classroom Layout Modal
const mapModal = document.getElementById("mapModal");
const mapModalImg = document.getElementById("mapModalImg");
const openMapModal = () => {
  mapModal.hidden = false;
  mapModalImg.classList.remove("zoomed");
};
const closeMapModal = () => {
  mapModal.hidden = true;
};
document.getElementById("btnOpenMap").addEventListener("click", openMapModal);
document.getElementById("btnOpenMapSide").addEventListener("click", openMapModal);
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
];

// --- Load Spec & Compressed GLB (with Build-Hash Cache & Draco Decoder) ---
async function init() {
  let buildHash = "12.7";
  try {
    const metaRes = await fetch("./build_meta.json");
    if (metaRes.ok) {
      const meta = await metaRes.json();
      if (meta?.hash) buildHash = `${meta.version || "12.7"}-${meta.hash}`;
    }
  } catch (_) {
    // Fallback to static version string
  }

  try {
    const res = await fetch(`./campus_cges.json?v=${buildHash}`);
    state.spec = await res.json();
  } catch (e) {
    console.warn("Spec load failed:", e);
  }
  hydrateAllRooms();
  buildZoneLabels();
  renderCategoryPills();
  refresh3DLabels();
  renderSidebar();
  requestRender(12);

  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  const dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath("./vendor/three/examples/jsm/libs/draco/gltf/");
  const loader = new GLTFLoader();
  loader.setDRACOLoader(dracoLoader);
  loader.load(
    `./exports/cges_campus.glb?v=${buildHash}`,
    (gltf) => {
      state.rootModel = gltf.scene;
      gltf.scene.traverse((obj) => {
        if (obj.isMesh) {
          const isGroundDecal = GROUND_ONLY_RECEIVE_PATTERNS.some((p) => obj.name.startsWith(p));
          obj.castShadow = !isGroundDecal;
          obj.receiveShadow = true;
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
      statusEl.remove();
      dracoLoader.dispose();
      requestShadowUpdate();
    },
    (xhr) => {
      if (xhr.total) {
        statusEl.textContent = `載入重慶國小 3D 模型中… ${Math.round((xhr.loaded / xhr.total) * 100)}%`;
      }
    },
    (err) => {
      console.error(err);
      statusEl.textContent = "載入模型失敗：" + err.message;
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
