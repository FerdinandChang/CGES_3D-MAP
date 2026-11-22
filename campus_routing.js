/**
 * 新北市板橋區重慶國小 115 學年度 3D 校園步行導引與動線規劃引擎
 * 支援三大校門起點、♿ 無障礙電梯優先模式、單一樓梯連貫搜尋、精確 2D 向量左右轉判斷與 3D 路徑點生成
 */

export const ROUTE_STARTS = [
  {
    id: "gate_main",
    label: "廣和街 31 號主校門",
    shortLabel: "🚪 主校門 (廣和街)",
    icon: "🏫",
  },
  {
    id: "gate_back3",
    label: "廣和街 3 號大後門",
    shortLabel: "🚪 3號大後門 (南側)",
    icon: "🚪",
  },
  {
    id: "gate_heping147b",
    label: "和平路 147B 操場側門",
    shortLabel: "🏃 147B 操場側門 (和平路)",
    icon: "🏃",
  },
];

function floorWalkZ(zoneId, floorNum) {
  if (zoneId === "Bldg_Guanghe") {
    return floorNum <= 1 ? 1.35 : 4.2 + (floorNum - 2) * 3.4 + 0.30;
  }
  if (zoneId === "Bldg_Gym_Skybridge") {
    if (floorNum === 1) return 0.55;
    if (floorNum === 2) return 5.15;
    return 10.6;
  }
  return floorNum <= 1 ? 0.45 : 3.6 + (floorNum - 2) * 3.4 + 0.30;
}

function buildCampusNavGraph() {
  const nodes = new Map();
  const adj = new Map();

  const addNode = (id, x, y, z, meta = {}) => {
    nodes.set(id, { id, x, y, z, ...meta });
    if (!adj.has(id)) adj.set(id, []);
  };

  const addEdge = (a, b, opts = {}) => {
    const na = nodes.get(a);
    const nb = nodes.get(b);
    if (!na || !nb) return;
    const dist = Math.hypot(nb.x - na.x, nb.y - na.y, nb.z - na.z);
    const forward = { to: b, dist, ...opts };
    const reverse = { to: a, dist, ...opts, reverseOf: true };
    adj.get(a).push(forward);
    if (!opts.oneWay) adj.get(b).push(reverse);
  };

  // --- 1. 地面入口、廣場、穿堂與戶外場域節點 ---
  addNode("gate_main", -69.0, 5.8, 0.25, { floor: 1, label: "廣和街 31 號主校門（行人入口）", zoneId: "Zone_Outdoor" });
  addNode("plaza_gate", -59.5, 0.5, 0.25, { floor: 1, label: "校門前庭廣場", zoneId: "Zone_Outdoor" });
  addNode("gh_1f_breeze", -51.5, 0.5, 1.35, { floor: 1, label: "廣和樓 1F 穿堂", zoneId: "Bldg_Guanghe" });

  // 北側通道（往和平樓 2梯 / 1F）
  addNode("nw_garden_path", -57.5, 18.0, 0.25, { floor: 1, label: "廣和樓北側通道", zoneId: "Zone_Outdoor" });
  // 南側 10 級大階梯（往南連廊與重慶樓 1F）
  addNode("south_stairs_foot", -56.6, -21.2, 0.25, { floor: 1, label: "前庭 10 級大階梯前", zoneId: "Zone_Outdoor" });
  addNode("south_stairs_top", -50.6, -21.2, 1.35, { floor: 1, label: "廣和南連廊 1F 平台", zoneId: "Bldg_Chongqing" });
  addNode("south_bridge_1f_s", -46.4, -30.5, 1.35, { floor: 1, label: "重慶樓 1F 圖書室前廊", zoneId: "Bldg_Chongqing" });

  // 中庭與操場主幹道
  addNode("cy_mid", -23.0, 0.5, 0.25, { floor: 1, label: "中央椰林中庭", zoneId: "Zone_Outdoor" });
  addNode("cy_north_pond", -18.5, 22.0, 0.25, { floor: 1, label: "生態池南側中庭步道", zoneId: "Zone_Outdoor" });
  addNode("cy_south_mid", -23.0, -24.0, 0.25, { floor: 1, label: "南中庭廣場", zoneId: "Zone_Outdoor" });

  // 後門與側門
  addNode("gate_back3", 12.5, -69.5, 0.25, { floor: 1, label: "廣和街 3 號大後門", zoneId: "Zone_Outdoor" });
  addNode("wq_south_apron", 8.5, -63.0, 0.25, { floor: 1, label: "五權樓南端（8梯前）", zoneId: "Zone_Outdoor" });
  addNode("gate_heping147b", 8.7, 46.2, 0.25, { floor: 1, label: "和平路 147B 操場側門", zoneId: "Zone_Outdoor" });
  addNode("wq_north_apron", 8.5, 35.4, 0.25, { floor: 1, label: "五權樓北端彩繪穿堂（9梯前）", zoneId: "Bldg_Wuquan" });
  addNode("wq_stage_apron", 11.8, -13.75, 0.25, { floor: 1, label: "升旗司令台・五權樓穿堂前大道", zoneId: "Zone_Outdoor" });
  addNode("heping_b1_ramp", 1.2, 41.5, 0.25, { floor: 1, label: "和平路 B1 雙鐵捲門通道", zoneId: "Zone_Outdoor" });

  // 戶外景點節點
  addNode("track_center", 42.0, -12.0, 0.25, { floor: 1, label: "200m 紅 PU 操場中央", zoneId: "Zone_Outdoor" });
  addNode("east_fitness", 64.5, -32.0, 0.25, { floor: 1, label: "操場東側體健區", zoneId: "Zone_Outdoor" });
  addNode("north_court", 48.3, 40.2, 0.25, { floor: 1, label: "東北角水泥雙籃球場", zoneId: "Zone_Outdoor" });
  addNode("south_bball", -27.0, -52.5, 0.25, { floor: 1, label: "南側露天雙籃球場", zoneId: "Zone_Outdoor" });
  addNode("south_playground", -56.0, -54.0, 0.25, { floor: 1, label: "西南側兒童遊戲場", zoneId: "Zone_Outdoor" });

  // --- 2. 廣和樓 1F~5F（東側走廊 x = -32.8）---
  for (let f = 1; f <= 5; f++) {
    const z = floorWalkZ("Bldg_Guanghe", f);
    addNode(`gh_s3_f${f}`, -32.8, 9.5, z, { floor: f, zoneId: "Bldg_Guanghe", stairName: "3梯", exitDir: [1, 0], label: `廣和樓 ${f}F 北側（3梯口）` });
    addNode(`gh_mid_f${f}`, -32.8, 0.5, z, { floor: f, zoneId: "Bldg_Guanghe", label: `廣和樓 ${f}F 東走廊中段` });
    addNode(`gh_s4_f${f}`, -32.8, -8.8, z, { floor: f, zoneId: "Bldg_Guanghe", stairName: "4梯・電梯", exitDir: [1, 0], label: `廣和樓 ${f}F 南側（4梯・電梯口）` });

    addEdge(`gh_s3_f${f}`, `gh_mid_f${f}`, { kind: "corridor", segTag: "廣和樓走廊" });
    addEdge(`gh_mid_f${f}`, `gh_s4_f${f}`, { kind: "corridor", segTag: "廣和樓走廊" });

    if (f > 1) {
      addEdge(`gh_s3_f${f - 1}`, `gh_s3_f${f}`, { kind: "stair", stairName: "3梯", bldgIds: ["Bldg_Guanghe"], exitDir: [1, 0], dirName: "廣和樓北側 3梯" });
      addEdge(`gh_s4_f${f - 1}`, `gh_s4_f${f}`, { kind: "stair", stairName: "4梯", bldgIds: ["Bldg_Guanghe"], exitDir: [1, 0], dirName: "廣和樓南側 4梯" });
      addEdge(`gh_s4_f${f - 1}`, `gh_s4_f${f}`, { kind: "lift", stairName: "廣和樓無障礙電梯", exitDir: [1, 0], dirName: "廣和樓無障礙電梯" });
    }
  }

  // --- 3. 和平樓 1F~5F（南側走廊 y = 26.6）---
  for (let f = 1; f <= 5; f++) {
    const z = floorWalkZ("Bldg_Heping", f);
    addNode(`hp_s2_f${f}`, -55.0, 26.6, z, { floor: f, zoneId: "Bldg_Heping", stairName: "2梯", exitDir: [0, -1], label: `和平樓 ${f}F 2梯口` });
    addNode(`hp_br_f${f}`, -46.4, 26.6, z, { floor: f, zoneId: "Bldg_Heping", label: `和平樓 ${f}F 北連廊口` });
    addNode(`hp_s1_f${f}`, -23.0, 26.6, z, { floor: f, zoneId: "Bldg_Heping", stairName: "1梯", exitDir: [0, -1], label: `和平樓 ${f}F 1梯口` });
    addNode(`hp_sky_f${f}`, -17.5, 26.6, z, { floor: f, zoneId: "Bldg_Heping", label: `和平樓 ${f}F 海豚天橋前` });
    addNode(`hp_ne_f${f}`, -7.2, 26.6, z, { floor: f, zoneId: "Bldg_Heping", label: `和平樓 ${f}F 東北轉角` });

    addEdge(`hp_s2_f${f}`, `hp_br_f${f}`, { kind: "corridor", segTag: "和平樓走廊" });
    addEdge(`hp_br_f${f}`, `hp_s1_f${f}`, { kind: "corridor", segTag: "和平樓走廊" });
    addEdge(`hp_s1_f${f}`, `hp_sky_f${f}`, { kind: "corridor", segTag: "和平樓走廊" });
    addEdge(`hp_sky_f${f}`, `hp_ne_f${f}`, { kind: "corridor", segTag: "和平樓走廊" });

    if (f > 1) {
      addEdge(`hp_s2_f${f - 1}`, `hp_s2_f${f}`, { kind: "stair", stairName: "2梯", bldgIds: ["Bldg_Heping"], exitDir: [0, -1], dirName: "和平樓西側 2梯" });
      addEdge(`hp_s1_f${f - 1}`, `hp_s1_f${f}`, { kind: "stair", stairName: "1梯", bldgIds: ["Bldg_Heping"], exitDir: [0, -1], dirName: "和平樓中段 1梯" });
    }
  }

  // --- 4. 五權樓 1F~5F（東側操場走廊 x = 5.3 + 西側轉角連通節點 x = -5.8）---
  for (let f = 1; f <= 5; f++) {
    const z = floorWalkZ("Bldg_Wuquan", f);
    addNode(`wq_s9_w_f${f}`, -5.8, 27.2, z, { floor: f, zoneId: "Bldg_Wuquan", label: `五權樓 ${f}F 北轉角` });
    addNode(`wq_s9_f${f}`, 5.3, 27.2, z, { floor: f, zoneId: "Bldg_Wuquan", stairName: "9梯", exitDir: [1, 0], label: `五權樓 ${f}F 北端（9梯口）` });
    addNode(`wq_mid_f${f}`, 5.3, -13.75, z, { floor: f, zoneId: "Bldg_Wuquan", label: `五權樓 ${f}F 司令台上方走廊` });
    addNode(`wq_s7_f${f}`, 5.3, -42.5, z, { floor: f, zoneId: "Bldg_Wuquan", stairName: "7梯", exitDir: [1, 0], label: `五權樓 ${f}F 南中段（7梯口）` });
    addNode(`wq_s7_w_f${f}`, -5.8, -42.5, z, { floor: f, zoneId: "Bldg_Wuquan", stairName: "7梯", exitDir: [1, 0], label: `五權樓 ${f}F 重慶轉角` });
    addNode(`wq_s8_f${f}`, 5.3, -63.0, z, { floor: f, zoneId: "Bldg_Wuquan", stairName: "8梯", exitDir: [1, 0], label: `五權樓 ${f}F 南端（8梯口）` });

    addEdge(`wq_s9_w_f${f}`, `wq_s9_f${f}`, { kind: "corridor", segTag: "五權樓北穿堂" });
    addEdge(`wq_s9_f${f}`, `wq_mid_f${f}`, { kind: "corridor", segTag: "五權樓東側走廊" });
    addEdge(`wq_mid_f${f}`, `wq_s7_f${f}`, { kind: "corridor", segTag: "五權樓東側走廊" });
    addEdge(`wq_s7_f${f}`, `wq_s8_f${f}`, { kind: "corridor", segTag: "五權樓東側走廊" });
    addEdge(`wq_s7_w_f${f}`, `wq_s7_f${f}`, { kind: "corridor", segTag: "五權樓轉角走廊" });
    addEdge(`hp_ne_f${f}`, `wq_s9_w_f${f}`, { kind: "corridor", segTag: "和平・五權轉角連廊" });

    if (f > 1) {
      addEdge(`wq_s9_f${f - 1}`, `wq_s9_f${f}`, { kind: "stair", stairName: "9梯", bldgIds: ["Bldg_Wuquan", "Bldg_Heping"], exitDir: [1, 0], dirName: "五權樓北端 9梯" });
      addEdge(`wq_s8_f${f - 1}`, `wq_s8_f${f}`, { kind: "stair", stairName: "8梯", bldgIds: ["Bldg_Wuquan"], exitDir: [1, 0], dirName: "五權樓南端 8梯" });
    }
  }
  addNode("wq_mid_w_f1", -5.8, -13.75, 0.45, { floor: 1, zoneId: "Bldg_Wuquan", label: "五權樓 1F 穿堂西口" });
  addEdge("wq_s9_w_f1", "wq_mid_w_f1", { kind: "corridor", segTag: "五權樓 1F 西走廊" });
  addEdge("wq_mid_w_f1", "wq_s7_w_f1", { kind: "corridor", segTag: "五權樓 1F 西走廊" });
  addEdge("wq_mid_w_f1", "wq_mid_f1", { kind: "corridor", segTag: "五權樓 1F 穿堂" });

  // --- 5. 重慶樓 1F~5F（南側走廊 y = -41.8）---
  for (let f = 1; f <= 5; f++) {
    const z = floorWalkZ("Bldg_Chongqing", f);
    addNode(`cq_s5_f${f}`, -68.5, -41.8, z, { floor: f, zoneId: "Bldg_Chongqing", stairName: "5梯", exitDir: [0, -1], label: `重慶樓 ${f}F 西端（5梯口）` });
    addNode(`cq_br_f${f}`, -46.4, -41.8, z, { floor: f, zoneId: "Bldg_Chongqing", label: `重慶樓 ${f}F 南連廊口` });
    addNode(`cq_s6_f${f}`, -42.5, -41.8, z, { floor: f, zoneId: "Bldg_Chongqing", stairName: "6梯", exitDir: [0, -1], label: `重慶樓 ${f}F 中段（6梯口）` });
    addNode(`cq_breeze_f${f}`, -27.8, -41.8, z, { floor: f, zoneId: "Bldg_Chongqing", label: `重慶樓 ${f}F 穿堂` });
    addNode(`cq_s7_f${f}`, -7.8, -41.8, z, { floor: f, zoneId: "Bldg_Chongqing", stairName: "7梯", exitDir: [0, -1], label: `重慶樓 ${f}F 東端（7梯口）` });

    addEdge(`cq_s5_f${f}`, `cq_br_f${f}`, { kind: "corridor", segTag: "重慶樓南走廊" });
    addEdge(`cq_br_f${f}`, `cq_s6_f${f}`, { kind: "corridor", segTag: "重慶樓南走廊" });
    addEdge(`cq_s6_f${f}`, `cq_breeze_f${f}`, { kind: "corridor", segTag: "重慶樓南走廊" });
    addEdge(`cq_breeze_f${f}`, `cq_s7_f${f}`, { kind: "corridor", segTag: "重慶樓南走廊" });
    addEdge(`cq_s7_f${f}`, `wq_s7_w_f${f}`, { kind: "corridor", segTag: "重慶・五權轉角連廊" });

    if (f > 1) {
      addEdge(`cq_s5_f${f - 1}`, `cq_s5_f${f}`, { kind: "stair", stairName: "5梯", bldgIds: ["Bldg_Chongqing"], exitDir: [0, -1], dirName: "重慶樓西端 5梯" });
      addEdge(`cq_s6_f${f - 1}`, `cq_s6_f${f}`, { kind: "stair", stairName: "6梯", bldgIds: ["Bldg_Chongqing"], exitDir: [0, -1], dirName: "重慶樓中段 6梯" });
      addEdge(`cq_s7_f${f - 1}`, `cq_s7_f${f}`, { kind: "stair", stairName: "7梯", bldgIds: ["Bldg_Chongqing", "Bldg_Wuquan"], exitDir: [0, -1], dirName: "重慶・五權轉角 7梯" });
    }
  }

  // --- 6. 廣和樓 <-> 和平 / 重慶 2F~5F 立體雙圓洞空中連廊（x = -46.4）---
  for (let f = 2; f <= 5; f++) {
    const zN = floorWalkZ("Bldg_Heping", f);
    addNode(`br_n_s_f${f}`, -46.4, 9.5, zN, { floor: f, zoneId: "Bldg_Guanghe" });
    addEdge(`gh_s3_f${f}`, `br_n_s_f${f}`, { kind: "bridge", bridgeName: `${f}F 廣和↔和平圓洞連廊` });
    addEdge(`br_n_s_f${f}`, `hp_br_f${f}`, { kind: "bridge", bridgeName: `${f}F 廣和↔和平圓洞連廊` });

    addNode(`br_s_n_f${f}`, -46.4, -8.8, zN, { floor: f, zoneId: "Bldg_Guanghe" });
    addNode(`br_s_s_f${f}`, -46.4, -30.5, zN, { floor: f, zoneId: "Bldg_Chongqing" });
    addEdge(`gh_s4_f${f}`, `br_s_n_f${f}`, { kind: "bridge", bridgeName: `${f}F 廣和↔重慶圓洞連廊` });
    addEdge(`br_s_n_f${f}`, `br_s_s_f${f}`, { kind: "bridge", bridgeName: `${f}F 廣和↔重慶圓洞連廊` });
    addEdge(`br_s_s_f${f}`, `cq_br_f${f}`, { kind: "corridor", segTag: "重慶樓連廊" });
  }

  // --- 7. 跨和平路海豚天橋 & 重慶國小綜合運動中心 ---
  addNode("sky_s", -17.5, 39.2, 4.95, { floor: 2, zoneId: "Bldg_Heping", label: "和平樓 2F 海豚天橋口" });
  addNode("sky_n", -17.5, 64.2, 4.95, { floor: 2, zoneId: "Bldg_Gym_Skybridge", label: "海豚天橋北端（運動中心）" });
  addNode("gym_1f_front", -28.0, 62.5, 0.25, { floor: 1, zoneId: "Bldg_Gym_Skybridge", label: "運動中心和平路前庭廣場" });
  addNode("gym_1f_pool", -34.5, 80.0, 1.2, { floor: 1, zoneId: "Bldg_Gym_Skybridge", label: "運動中心 1F 溫水游泳池" });
  addNode("gym_2f_lobby", -26.0, 66.0, 5.15, { floor: 2, zoneId: "Bldg_Gym_Skybridge", label: "運動中心 2F 主入口大廳" });
  addNode("gym_2f_rhythm", -44.0, 66.0, 5.15, { floor: 2, zoneId: "Bldg_Gym_Skybridge", label: "運動中心 2F 韻律教室" });
  addNode("gym_3f_court", -34.5, 84.0, 10.6, { floor: 3, zoneId: "Bldg_Gym_Skybridge", label: "運動中心 3F 綜合室內球場" });

  addEdge("hp_sky_f2", "sky_s", { kind: "corridor", segTag: "1梯旁天橋入口" });
  addEdge("sky_s", "sky_n", { kind: "bridge", bridgeName: "跨和平路海豚彩繪人行天橋" });
  addEdge("sky_n", "gym_2f_lobby", { kind: "corridor", segTag: "運動中心 2F 門廳" });
  addEdge("gym_1f_front", "gym_1f_pool", { kind: "corridor", segTag: "運動中心 1F 通道" });
  addEdge("gym_1f_front", "gym_2f_lobby", { kind: "stair", stairName: "運動中心前庭寬階梯", dirName: "運動中心室外寬階梯" });
  addEdge("gym_2f_lobby", "gym_2f_rhythm", { kind: "corridor", segTag: "運動中心 2F 走廊" });
  addEdge("gym_2f_lobby", "gym_3f_court", { kind: "stair", stairName: "運動中心室內階梯", dirName: "運動中心室內階梯" });

  // --- 8. 地面層全網連通（校門 <-> 前庭 <-> 穿堂 <-> 中庭 <-> 操場 <-> 側門／後門） ---
  addEdge("gate_main", "plaza_gate", { kind: "outdoor" });
  addEdge("plaza_gate", "gh_1f_breeze", { kind: "steps", dirName: "廣和樓正門 11 階寬階梯" });
  addEdge("gh_1f_breeze", "gh_mid_f1", { kind: "corridor", segTag: "廣和樓 1F 穿堂" });
  addEdge("gh_mid_f1", "cy_mid", { kind: "steps", dirName: "廣和樓東側階梯" });

  // 主校門直接北行 -> 和平樓 1F（無需經正門階梯）；或由前庭無障礙斜坡進出廣和樓電梯
  addEdge("plaza_gate", "nw_garden_path", { kind: "outdoor" });
  addEdge("nw_garden_path", "hp_s2_f1", { kind: "outdoor" });
  addEdge("gh_s3_f1", "hp_br_f1", { kind: "outdoor" });
  addEdge("plaza_gate", "gh_s4_f1", { kind: "outdoor", accessibleOnly: true });

  // 主校門南行 -> 10 級磨石子大階梯 -> 重慶樓 1F 圖書室前廊 -> 5梯/6梯/穿堂
  addEdge("plaza_gate", "south_stairs_foot", { kind: "outdoor" });
  addEdge("south_stairs_foot", "south_stairs_top", { kind: "steps", dirName: "通往重慶樓 10 級寬階梯" });
  addEdge("south_stairs_top", "south_bridge_1f_s", { kind: "corridor", segTag: "廣和南連廊 1F" });
  addEdge("south_bridge_1f_s", "cq_s5_f1", { kind: "corridor", segTag: "重慶樓 1F 西走廊" });
  addEdge("south_bridge_1f_s", "cq_br_f1", { kind: "corridor", segTag: "重慶樓 1F 走廊" });

  // 中庭網狀通行（中庭開放無阻擋，鼓勵由廣和穿堂直走中庭前往五權樓）
  addEdge("cy_mid", "cy_north_pond", { kind: "outdoor" });
  addEdge("cy_north_pond", "hp_s1_f1", { kind: "outdoor" });
  addEdge("cy_mid", "cy_south_mid", { kind: "outdoor" });
  addEdge("cy_south_mid", "cq_breeze_f1", { kind: "outdoor" });
  addEdge("cy_mid", "wq_mid_w_f1", { kind: "outdoor" });
  addEdge("cy_south_mid", "cq_s7_f1", { kind: "outdoor" });
  addEdge("cy_south_mid", "wq_s7_w_f1", { kind: "outdoor" });
  addEdge("cy_north_pond", "wq_s9_w_f1", { kind: "outdoor" });

  // 重慶樓 1F 穿堂 <-> 雙籃球場 <-> 遊戲場 <-> 3號門
  addEdge("cq_breeze_f1", "south_bball", { kind: "outdoor" });
  addEdge("cq_s5_f1", "south_playground", { kind: "outdoor" });
  addEdge("south_playground", "south_bball", { kind: "outdoor" });
  addEdge("south_bball", "wq_south_apron", { kind: "outdoor" });

  // 五權樓東側／操場／3號大後門／147B 側門
  addEdge("gate_back3", "wq_south_apron", { kind: "outdoor" });
  addEdge("wq_south_apron", "wq_s8_f1", { kind: "outdoor" });
  addEdge("wq_south_apron", "wq_stage_apron", { kind: "outdoor" });
  addEdge("wq_mid_f1", "wq_stage_apron", { kind: "corridor", segTag: "五權樓穿堂・司令台前" });
  addEdge("wq_stage_apron", "wq_north_apron", { kind: "outdoor" });
  addEdge("wq_north_apron", "wq_s9_f1", { kind: "outdoor" });
  addEdge("wq_north_apron", "gate_heping147b", { kind: "outdoor" });
  addEdge("wq_north_apron", "heping_b1_ramp", { kind: "outdoor" });
  addEdge("wq_stage_apron", "track_center", { kind: "outdoor" });
  addEdge("track_center", "east_fitness", { kind: "outdoor" });
  addEdge("wq_north_apron", "north_court", { kind: "outdoor" });
  addEdge("gate_heping147b", "north_court", { kind: "outdoor" });
  addEdge("gate_heping147b", "gym_1f_front", { kind: "outdoor", streetCrossPenalty: 18 });
  // 校外和平路斑馬線往運動中心 1F 前庭（較校內海豚天橋多一段過馬路成本）
  addEdge("nw_garden_path", "gym_1f_front", { kind: "outdoor", streetCrossPenalty: 58 });

  return { nodes, adj };
}

const GRAPH = buildCampusNavGraph();

function parseFloorNum(floorStr) {
  const m = String(floorStr || "").match(/^(\d+)F/i);
  return m ? parseInt(m[1], 10) : 1;
}

function resolveRoomAttachPoint(room) {
  const [rx, ry, rz] = room.pos;
  const fl = parseFloorNum(room.floor);
  const z = floorWalkZ(room.zoneId, fl);

  if (room.zoneId === "Zone_Outdoor") {
    if (room.name.includes("司令台")) return { x: 11.8, y: -13.75, z: 0.45, doorPt: [rx, ry, 1.2], anchors: ["wq_stage_apron", "wq_mid_f1"] };
    if (room.name.includes("體健區")) return { x: 64.5, y: -32.0, z: 0.35, doorPt: [rx, ry, 0.8], anchors: ["east_fitness"] };
    if (room.name.includes("PU 操場") || room.name.includes("足球場")) return { x: 42.0, y: -12.0, z: 0.35, doorPt: [rx, ry, 0.5], anchors: ["track_center"] };
    if (room.name.includes("生態水生植物池")) return { x: -18.5, y: 18.5, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["cy_north_pond"] };
    if (room.name.includes("椰子中庭")) return { x: -22.0, y: -16.5, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["cy_mid", "cy_south_mid"] };
    if (room.name.includes("薄荷綠雙籃球場")) return { x: -27.0, y: -52.5, z: 0.35, doorPt: [rx, ry, 0.5], anchors: ["south_bball"] };
    if (room.name.includes("3號大後門")) return { x: 12.5, y: -69.5, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["gate_back3"] };
    if (room.name.includes("兒童遊戲場")) return { x: -56.0, y: -54.0, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["south_playground"] };
    if (room.name.includes("主校門")) return { x: -69.0, y: 5.8, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["gate_main"] };
    if (room.name.includes("前庭紅磚廣場")) return { x: -60.5, y: 0.5, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["plaza_gate"] };
    if (room.name.includes("東北角雙半場")) return { x: 48.3, y: 40.2, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["north_court"] };
    if (room.name.includes("B1 雙鐵捲門")) return { x: 1.2, y: 41.5, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["heping_b1_ramp"] };
    if (room.name.includes("147B 操場側門")) return { x: 8.7, y: 46.2, z: 0.35, doorPt: [rx, ry, 0.6], anchors: ["gate_heping147b"] };
  }

  if (room.zoneId === "Bldg_Gym_Skybridge") {
    if (room.name.includes("海豚")) return { x: -17.5, y: 52.0, z: 4.95, doorPt: [-17.5, 52.0, 5.1], anchors: ["sky_s", "sky_n"] };
    if (room.name.includes("綜合室內球場") || room.name.includes("玻璃金字塔")) return { x: -34.5, y: 84.0, z: 10.6, doorPt: [rx, ry, 10.6], anchors: ["gym_3f_court"] };
    if (room.name.includes("韻律")) return { x: -44.0, y: 66.0, z: 5.15, doorPt: [rx, ry, 5.15], anchors: ["gym_2f_rhythm"] };
    if (room.name.includes("主入口大廳")) return { x: -26.0, y: 66.0, z: 5.15, doorPt: [rx, ry, 5.15], anchors: ["gym_2f_lobby"] };
    if (room.name.includes("游泳池")) return { x: -34.5, y: 80.0, z: 1.2, doorPt: [rx, ry, 1.2], anchors: ["gym_1f_pool"] };
    return { x: -28.0, y: 62.5, z: 0.35, doorPt: [rx, ry, 0.8], anchors: ["gym_1f_front"] };
  }

  if (room.zoneId === "Bldg_Guanghe") {
    const anchors = [`gh_s3_f${fl}`, `gh_mid_f${fl}`, `gh_s4_f${fl}`];
    return { x: -32.8, y: ry, z, doorPt: [-34.6, ry, z + 0.35], anchors, roomVec: [-1, 0] };
  }
  if (room.zoneId === "Bldg_Heping") {
    if (room.name.includes("海豚天橋")) {
      return { x: -17.5, y: 39.2, z: 4.95, doorPt: [-17.5, 39.2, 5.05], anchors: ["sky_s"], roomVec: [0, 1] };
    }
    const anchors = [`hp_s2_f${fl}`, `hp_br_f${fl}`, `hp_s1_f${fl}`, `hp_sky_f${fl}`, `hp_ne_f${fl}`];
    return { x: rx, y: 26.6, z, doorPt: [rx, 28.4, z + 0.35], anchors, roomVec: [0, 1] };
  }
  if (room.zoneId === "Bldg_Chongqing") {
    const anchors = [`cq_s5_f${fl}`, `cq_br_f${fl}`, `cq_s6_f${fl}`, `cq_breeze_f${fl}`, `cq_s7_f${fl}`];
    return { x: rx, y: -41.8, z, doorPt: [rx, -39.8, z + 0.35], anchors, roomVec: [0, 1] };
  }
  if (room.zoneId === "Bldg_Wuquan") {
    if (fl === 1 && ry < -20.0) {
      const anchors = ["wq_mid_w_f1", "wq_s7_w_f1"];
      return { x: -5.8, y: ry, z, doorPt: [-4.0, ry, z + 0.35], anchors, roomVec: [1, 0] };
    }
    const anchors = [`wq_s9_f${fl}`, `wq_mid_f${fl}`, `wq_s7_f${fl}`, `wq_s8_f${fl}`];
    return { x: 5.3, y: ry, z, doorPt: [3.5, ry, z + 0.35], anchors, roomVec: [-1, 0] };
  }

  return { x: rx, y: ry, z, doorPt: [rx, ry, z], anchors: ["cy_mid"], roomVec: null };
}

function edgeCost(edge, accessible, curStair, usedAnyStair, targetZoneId) {
  if (edge.accessibleOnly && !accessible) return Infinity;
  let c = edge.dist + (edge.streetCrossPenalty || 0);

  if (edge.kind === "stair") {
    if (accessible) {
      c += 2400;
    } else {
      // 同一座樓梯連續爬多層不重複加懲罰；切換不同樓梯或優先使用目標棟別本身樓梯
      if (curStair === edge.stairName) {
        c += 2;
      } else {
        const wrongBldg = edge.bldgIds && targetZoneId && !edge.bldgIds.includes(targetZoneId) && targetZoneId !== "Bldg_Gym_Skybridge";
        c += (usedAnyStair ? 65 : 14) + (wrongBldg ? 28 : 0);
      }
    }
  } else if (edge.kind === "lift") {
    if (accessible) {
      c += curStair === edge.stairName ? 1 : 4;
    } else {
      c += curStair === edge.stairName ? 4 : 36;
    }
  } else if (edge.kind === "steps") {
    c += accessible ? 180 : 3;
  } else if (edge.kind === "bridge") {
    c += 2;
  }
  return c;
}

function classifyTurn(u, v) {
  const lenU = Math.hypot(u[0], u[1]);
  const lenV = Math.hypot(v[0], v[1]);
  if (lenU < 0.5 || lenV < 0.5) return "直走";
  const ux = u[0] / lenU;
  const uy = u[1] / lenU;
  const vx = v[0] / lenV;
  const vy = v[1] / lenV;
  const dot = ux * vx + uy * vy;
  const cross = ux * vy - uy * vx; // +1 = 左轉, -1 = 右轉
  if (dot > 0.86) return "直走";
  if (dot < -0.75) return "迴轉";
  return cross > 0 ? "左轉" : "右轉";
}

function classifySide(heading, toRoomVec) {
  if (!heading || !toRoomVec) return "";
  const lenH = Math.hypot(heading[0], heading[1]);
  if (lenH < 0.3) return "";
  const ux = heading[0] / lenH;
  const uy = heading[1] / lenH;
  const cross = ux * toRoomVec[1] - uy * toRoomVec[0];
  if (Math.abs(cross) < 0.35) return "";
  return cross > 0 ? "左手邊" : "右手邊";
}

/**
 * 計算由指定起點（預設為主校門）前往目標空間之最短合理步行路線與分步文字導引
 */
export function computeCampusRoute(room, startId = "gate_main", accessible = false) {
  if (!room || !GRAPH.nodes.has(startId)) return null;

  const targetMeta = resolveRoomAttachPoint(room);
  const { nodes, adj } = GRAPH;

  const targetId = "__TARGET__";
  const tempEdges = targetMeta.anchors
    .filter((aid) => nodes.has(aid))
    .map((aid) => {
      const n = nodes.get(aid);
      const d = Math.hypot(targetMeta.x - n.x, targetMeta.y - n.y, targetMeta.z - n.z);
      return { id: aid, dist: d };
    })
    .sort((a, b) => a.dist - b.dist);

  if (tempEdges.length === 0) return null;

  // 狀態擴展 Dijkstra：stateKey = `${nodeId}|${curStair}`，避免無意義分段轉搭不同樓梯
  const startKey = `${startId}|`;
  const distMap = new Map([[startKey, 0]]);
  const prevMap = new Map();
  const visited = new Set();
  const queue = [{ key: startKey, id: startId, curStair: "", usedAnyStair: false, cost: 0 }];
  let finalKey = null;

  const getNeighbors = (id) => {
    const base = adj.get(id) || [];
    const hit = tempEdges.find((e) => e.id === id);
    if (!hit) return base;
    return [...base, { to: targetId, dist: hit.dist, kind: "corridor", isFinalAttach: true }];
  };

  while (queue.length > 0) {
    queue.sort((a, b) => a.cost - b.cost);
    const { key: uKey, id: u, curStair, usedAnyStair, cost: uCost } = queue.shift();
    if (visited.has(uKey)) continue;
    visited.add(uKey);
    if (u === targetId) {
      finalKey = uKey;
      break;
    }

    for (const edge of getNeighbors(u)) {
      const eCost = edgeCost(edge, accessible, curStair, usedAnyStair, room.zoneId);
      if (!Number.isFinite(eCost)) continue;
      const isVertical = edge.kind === "stair" || edge.kind === "lift";
      const nextStair = isVertical ? edge.stairName || "" : curStair;
      const nextUsedAny = usedAnyStair || isVertical;
      const vKey = edge.to === targetId ? targetId : `${edge.to}|${nextStair}`;
      if (visited.has(vKey)) continue;

      const alt = uCost + eCost;
      if (alt < (distMap.get(vKey) ?? Infinity)) {
        distMap.set(vKey, alt);
        prevMap.set(vKey, { fromKey: uKey, fromId: u, edge });
        queue.push({ key: vKey, id: edge.to, curStair: nextStair, usedAnyStair: nextUsedAny, cost: alt });
      }
    }
  }

  if (!finalKey || !prevMap.has(finalKey)) return null;

  // 回溯節點鏈
  const rawSteps = [];
  let cursorKey = finalKey;
  while (cursorKey) {
    const prev = prevMap.get(cursorKey);
    const nodeId = cursorKey === targetId ? targetId : cursorKey.split("|")[0];
    if (nodeId === targetId) {
      rawSteps.unshift({
        id: targetId,
        zoneId: room.zoneId,
        x: targetMeta.x,
        y: targetMeta.y,
        z: targetMeta.z,
        floor: parseFloorNum(room.floor),
        label: room.short,
        edgeFromPrev: prev ? prev.edge : null,
      });
    } else {
      const nd = nodes.get(nodeId);
      rawSteps.unshift({
        ...nd,
        edgeFromPrev: prev ? prev.edge : null,
      });
    }
    cursorKey = prev ? prev.fromKey : null;
  }

  // 組裝 3D 繪製點序列（末端加上教室門口點，並移除相鄰重複座標）
  const points3D = [];
  for (const s of rawSteps) {
    const last = points3D[points3D.length - 1];
    if (!last || Math.hypot(s.x - last[0], s.y - last[1], s.z - last[2]) > 0.25) {
      points3D.push([s.x, s.y, s.z + 0.15]);
    }
  }
  if (targetMeta.doorPt) {
    const last = points3D[points3D.length - 1];
    const [dx, dy, dz] = targetMeta.doorPt;
    if (!last || Math.hypot(dx - last[0], dy - last[1]) > 0.6) {
      points3D.push([dx, dy, dz]);
    }
  }

  let totalMeters = 0;
  for (let i = 1; i < points3D.length; i++) {
    totalMeters += Math.hypot(
      points3D[i][0] - points3D[i - 1][0],
      points3D[i][1] - points3D[i - 1][1],
      points3D[i][2] - points3D[i - 1][2]
    );
  }
  totalMeters = Math.max(5, Math.round(totalMeters));
  const estMinutes = Math.max(1, Math.round(totalMeters / 65));

  // --- 將節點鏈轉譯為自然中文 Turn-by-Turn 分步指引 ---
  const normDir = (v) => {
    const l = Math.hypot(v[0], v[1]);
    return l > 0.01 ? [v[0] / l, v[1] / l] : [1, 0];
  };
  const isIndoorZone = (zId) => Boolean(zId && zId !== "Zone_Outdoor");
  const steps = [];
  const startMeta = ROUTE_STARTS.find((s) => s.id === startId) || ROUTE_STARTS[0];
  let heading = startId === "gate_main" ? [1, 0] : startId === "gate_back3" ? [0, 1] : [0, -1];
  let i = 0;

  while (i < rawSteps.length - 1) {
    const cur = rawSteps[i];
    const nxt = rawSteps[i + 1];
    const edge = nxt.edgeFromPrev;

    // 1. 合併同一座樓梯／電梯的連續跨樓層移動
    if (edge?.kind === "stair" || edge?.kind === "lift") {
      const stairLabel = edge.stairName || edge.dirName || "樓梯";
      const startFloor = cur.floor || 1;
      let j = i + 1;
      while (j < rawSteps.length - 1 && rawSteps[j + 1].edgeFromPrev?.stairName === edge.stairName) {
        j++;
      }
      const endNode = rawSteps[j];
      const endFloor = endNode.floor || startFloor;
      const isUp = endFloor >= startFloor;
      const verb = edge.kind === "lift" ? "搭乘" : "走";
      if (endNode.exitDir) {
        heading = [...endNode.exitDir];
      }
      steps.push({
        icon: edge.kind === "lift" ? "🛗" : "🪜",
        action: `${verb} ${stairLabel}`,
        text: `${verb} <strong>${stairLabel}</strong> ${isUp ? "上" : "下"}至 <strong>${endFloor}F</strong>（共 ${Math.abs(endFloor - startFloor)} 層）`,
        pos: [endNode.x, endNode.y, endNode.z],
        badge: `${endFloor}F`,
        zoneId: endNode.zoneId || cur.zoneId || room.zoneId,
        floor: endFloor,
        dir: normDir(heading),
        indoor: true,
      });
      i = j;
      continue;
    }

    // 2. 合併同一條連廊／天橋
    if (edge?.kind === "bridge") {
      const bName = edge.bridgeName;
      let j = i + 1;
      let segLen = Math.hypot(nxt.x - cur.x, nxt.y - cur.y);
      while (j < rawSteps.length - 1 && rawSteps[j + 1].edgeFromPrev?.bridgeName === bName) {
        j++;
        segLen += Math.hypot(rawSteps[j].x - rawSteps[j - 1].x, rawSteps[j].y - rawSteps[j - 1].y);
      }
      const endNode = rawSteps[j];
      const vec = [endNode.x - cur.x, endNode.y - cur.y];
      const turn = classifyTurn(heading, vec);
      if (Math.hypot(vec[0], vec[1]) > 0.5) heading = vec;
      steps.push({
        icon: "🌉",
        action: `${turn === "直走" ? "直行" : turn}過連廊／天橋`,
        text: `${turn === "直走" ? "直行" : turn}經 <strong>${bName}</strong>（約 ${Math.round(segLen)}m）至 ${endNode.label || "對側校舍"}`,
        pos: [(cur.x + endNode.x) * 0.5, (cur.y + endNode.y) * 0.5, (cur.z + endNode.z) * 0.5],
        badge: `${Math.round(segLen)}m`,
        zoneId: endNode.zoneId || cur.zoneId || room.zoneId,
        floor: endNode.floor || cur.floor || 2,
        dir: normDir(heading),
        indoor: true,
      });
      i = j;
      continue;
    }

    if (edge?.kind === "steps") {
      const vec = [nxt.x - cur.x, nxt.y - cur.y];
      const turn = classifyTurn(heading, vec);
      const dSteps = Math.max(3, Math.round(Math.hypot(vec[0], vec[1])));
      if (Math.hypot(vec[0], vec[1]) > 0.4) heading = vec;
      const stepZone = nxt.zoneId || cur.zoneId || "Zone_Outdoor";
      steps.push({
        icon: "🪜",
        action: "踏上階梯",
        text: `${turn === "直走" ? "" : `${turn}後`}踏上 <strong>${edge.dirName}</strong>（約 ${dSteps}m）`,
        pos: [nxt.x, nxt.y, nxt.z],
        badge: `${dSteps}m`,
        zoneId: stepZone,
        floor: nxt.floor || 1,
        dir: normDir(heading),
        indoor: isIndoorZone(stepZone),
      });
      i++;
      continue;
    }

    // 3. 一般平面步行（走廊／戶外廣場），合併共線微節點
    let j = i + 1;
    let runVec = [nxt.x - cur.x, nxt.y - cur.y];
    let runLen = Math.hypot(runVec[0], runVec[1]);
    while (j < rawSteps.length - 1) {
      const eNext = rawSteps[j + 1].edgeFromPrev;
      if (eNext?.kind !== "corridor" && eNext?.kind !== "outdoor") break;
      const vNext = [rawSteps[j + 1].x - rawSteps[j].x, rawSteps[j + 1].y - rawSteps[j].y];
      const lNext = Math.hypot(vNext[0], vNext[1]);
      if (runLen > 0.3 && lNext > 0.3) {
        const dot = (runVec[0] * vNext[0] + runVec[1] * vNext[1]) / (runLen * lNext);
        if (dot > 0.90) {
          j++;
          runLen += lNext;
          runVec = [rawSteps[j].x - cur.x, rawSteps[j].y - cur.y];
          continue;
        }
      }
      break;
    }

    const endNode = rawSteps[j];
    const distM = Math.max(2, Math.round(runLen));
    const isFirstLeg = i === 0;
    const isFinalLeg = j === rawSteps.length - 1;
    const turn = isFirstLeg ? "直走" : classifyTurn(heading, runVec);
    if (Math.hypot(runVec[0], runVec[1]) > 0.3) heading = runVec;
    const midPos = [(cur.x + endNode.x) * 0.5, (cur.y + endNode.y) * 0.5, (cur.z + endNode.z) * 0.5];
    const segZone = isFinalLeg ? room.zoneId : endNode.zoneId || cur.zoneId || "Zone_Outdoor";
    const segFloor = endNode.floor || cur.floor || 1;
    const segIndoor = edge?.kind === "corridor" || isIndoorZone(segZone);

    if (isFirstLeg) {
      const destLabel = endNode.id === targetId ? `<strong>${room.short}</strong>` : `<strong>${endNode.label || "校內廣場"}</strong>`;
      steps.push({
        icon: startMeta.icon,
        action: "進校門",
        text: isFinalLeg
          ? `從 <strong>${startMeta.label}</strong> 進入後直走約 ${distM}m，即達 ${destLabel}`
          : `從 <strong>${startMeta.label}</strong> 進入校園直走約 ${distM}m 至 ${destLabel}`,
        pos: [cur.x, cur.y, cur.z],
        badge: `${distM}m`,
        zoneId: cur.zoneId || "Zone_Outdoor",
        floor: 1,
        dir: normDir(heading),
        indoor: false,
      });
    } else if (isFinalLeg) {
      const side = classifySide(heading, targetMeta.roomVec);
      const turnText = turn === "直走" ? "沿走廊直走" : `<strong>${turn}</strong>沿走廊直走`;
      const sideText = side ? `，<strong>${side}</strong>即達` : "即達";
      const usedStairBefore = steps.some((s) => s.icon === "🪜" || s.icon === "🛗");
      const prefix = usedStairBefore ? "出梯口後" : "";
      steps.push({
        icon: turn === "左轉" ? "↩️" : turn === "右轉" ? "↪️" : "🎯",
        action: turn,
        text: `${prefix}${turnText}約 ${distM}m${sideText} <strong>${room.short}</strong>`,
        pos: midPos,
        badge: "抵達",
        zoneId: room.zoneId,
        floor: parseFloorNum(room.floor),
        dir: normDir(heading),
        indoor: isIndoorZone(room.zoneId),
      });
    } else {
      const turnArrow = turn === "左轉" ? "↩️" : turn === "右轉" ? "↪️" : "🚶";
      const turnPhrase = turn === "直走" ? "繼續直走" : `<strong>${turn}</strong>直走`;
      const targetName = endNode.label || "前方路口";
      steps.push({
        icon: turnArrow,
        action: turn,
        text: `${turnPhrase}約 ${distM}m 至 <strong>${targetName}</strong>`,
        pos: midPos,
        badge: `${distM}m`,
        zoneId: segZone,
        floor: segFloor,
        dir: normDir(heading),
        indoor: segIndoor,
      });
    }

    i = j;
  }

  if (steps.length > 0 && steps[steps.length - 1].badge !== "抵達") {
    const lastSide = classifySide(heading, targetMeta.roomVec);
    steps.push({
      icon: "🎯",
      action: "抵達",
      text: `出梯口${lastSide ? `<strong>${lastSide}</strong>` : "前方"}即達 <strong>${room.short}</strong>`,
      pos: [targetMeta.x, targetMeta.y, targetMeta.z],
      badge: "抵達",
      zoneId: room.zoneId,
      floor: parseFloorNum(room.floor),
      dir: normDir(heading),
      indoor: isIndoorZone(room.zoneId),
    });
  }

  const waypoints = [
    { label: `🚩 起點：${startMeta.label.replace(/（.*）/, "")}`, pos: [rawSteps[0].x, rawSteps[0].y, rawSteps[0].z + 1.1] },
  ];
  for (const s of steps) {
    if (s.icon === "🪜" || s.icon === "🛗" || s.icon === "🌉") {
      waypoints.push({ label: `${s.icon} ${s.action}`, pos: [s.pos[0], s.pos[1], s.pos[2] + 1.0] });
    }
  }

  return {
    startId,
    startLabel: startMeta.label,
    accessible,
    destZoneId: room.zoneId,
    destFloor: parseFloorNum(room.floor),
    totalMeters,
    estMinutes,
    steps,
    points3D,
    waypoints,
  };
}
