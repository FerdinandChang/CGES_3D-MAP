# 新北市板橋區重慶國民小學 115 學年度 3D 校園數位雙生導覽系統 (`CGES_3D-MAP`)

以 **Blender 5.3 Headless (`bpy` / `bmesh`) 程式化 3D 建模**、**程式化 PBR 貼圖管線**與 **Three.js WebGL 互動導覽前端**打造之「新北市板橋區重慶國民小學（220 新北市板橋區廣和街 31 號）」1:1 寫實 3D 校園空間與 115 學年度教室配置導覽系統。

---

## 🌐 線上瀏覽網址與深層連結 (GitHub Pages)

- **線上 3D 導覽首頁**：https://ferdinandchang.github.io/CGES_3D-MAP/
- **指定空間與路線直達連結範例（Deep Linking）**：
  - 校長室：https://ferdinandchang.github.io/CGES_3D-MAP/#room=305
  - 指定班級：https://ferdinandchang.github.io/CGES_3D-MAP/#room=六年7班
  - **校門出發無障礙路線分享**：https://ferdinandchang.github.io/CGES_3D-MAP/#route=408&from=gate_main&acc=1
  - **教室 ➔ 教室點對點路線分享**：https://ferdinandchang.github.io/CGES_3D-MAP/#route=208&from=305&acc=0
  - **全校四棟 3D 自由步行＋點擊開關門（桌機）**：
    - 廣和樓 3F 校長室門口：https://ferdinandchang.github.io/CGES_3D-MAP/#walk=305
    - 和平樓 5F 六年 2 班門口：https://ferdinandchang.github.io/CGES_3D-MAP/#walk=502
    - 五權樓 5F 六年 7 班門口：https://ferdinandchang.github.io/CGES_3D-MAP/#walk=516
    - 重慶樓 2F 圖書室走廊：https://ferdinandchang.github.io/CGES_3D-MAP/#walk=cq2
  - 指定樓棟樓層：https://ferdinandchang.github.io/CGES_3D-MAP/#zone=Bldg_Wuquan&floor=3F
- **GitHub 專案儲存庫**：https://github.com/FerdinandChang/CGES_3D-MAP
- **學校官網參考基準**：https://www.cges.ntpc.edu.tw/（站點圖示 `favicon.ico` 與官網同步）

---

## ✨ 核心功能與實景重製亮點

### 1. 115 學年度全校 148 處空間 1:1 定位、步行導引＋深層分享
- **單一真相來源（Single Source of Truth）**：由 `campus_cges.json` 統一驅動建築規格、6 大分區邊界、預設鏡頭與全校 **148 處空間**（4 棟 5F 校舍 **127 間**室內空間＋運動中心與戶外操場球場 **21 處**空間）。
- **🧭 左側一體化導覽面板＋3D 樓層走廊實景剖視**：
  - **點對點教室導航（3 校門 + 全校 148 處空間任選起點）**：支援任一教室出發前往另一教室、`⇅` 一鍵起終點互換、**♿ 無障礙電梯優先模式**、`1梯～9梯／電梯` 精確左右轉分步文字，以及 **`🔗 分享路線`**（`#route=<終點>&from=<起點>&acc=<0|1>`）。
  - **分棟獨立剖視（Per-Building Cutaway）＋ 流動方向箭頭光帶**：導航或點擊單一步驟時，僅剖開路線所經之目標棟樓板，其餘未經過校舍保留完整屋頂天際線；3D 路徑以動態流動白色箭頭光帶呈現方向，並提供 **`▶ 走廊實境` 進度拖曳條與 `0.5x / 1x / 2x` 倍速控制**。
  - **3D 畫布直點單室＋行動端 RWD 底部抽屜**：拉近或剖層時可直接點擊 3D 走廊上的單一教室鎖定；手機版（`≤ 900px`）支援觸控拖曳高度切換與頂部極薄迷你步驟條，保留 84%+ 3D 視野；桌機支援 `/` 搜尋、`Esc` 退出、`←`/`→` 切換步驟與最近搜尋紀錄。
- **🚶 全校四棟自由步行進出＋互動開關教室門板（桌機限定，`walk_mode.js`）**：
  - **四棟全面中空化、360° 跨棟連通與實景教室／圖書館／視聽中心還原**：廣和樓、和平樓、五權樓、重慶樓 1F–5F 全校 **124/124 間實體室 100% 開門覆蓋（含梯間與開間共 164 扇互動內推門）** 皆以 `mod_walk_interior.py` 建為真實中空室體（含避門裁切窗洞、隔間牆、門框、天花燈與牆體／欄杆碰撞盒）；**2F–5F 四大跨棟連接處全面打通無縫連通**（和平↔五權東北轉角、重慶↔五權東南 L 轉角、和平↔北雙圓洞連廊↔廣和北端 2.0m 轉折通廊、重慶 6 梯貫通口↔南雙圓洞連廊↔廣和南端 2.0m 轉折通廊，雙圓洞連廊接廣和樓並設 3 階磨石子平滑踏階抹平 0.58m 樓板高差）。前端依實景還原全校一般教室 **6 大內部細節**（組合式**電子智慧黑板**＋3 盞黑板吊燈＋講台、莫蘭迪霧灰綠布質打褶對開**窗簾**、**全原木單人課桌椅**附 3 根黃色擋書插梢、**雙管懸吊銀鋁槽日光吊燈**與吸頂循環扇、淺原木實心平面**教室門**配銀色水平壓把與門頂鋁框氣窗、以及後牆 **3×12 藍・粉・黃錯落格學生置物櫃**與綠色公佈欄），並 1:1 精細重製**重慶樓 2F 圖書室**與**廣和樓 5F 505 視聽中心**（雙階淺金黃實木舞台、深酒紅重磅絨布大幕與平台鋼琴、可實際上下步行的 8 排深酒紅地毯階梯觀眾席與 88 席胡桃木扶手劇院排椅、隨坡斜降木質吸音格柵側牆、折板聲學天花與後牆透明音控室）。
  - **互動對內開啟合頁木門**：全校 164 扇教室／處室門皆嚴密嵌於門框洞口內（不外凸、不與走廊窗戶重疊，並徹底清除所有舊版靜態實心假門塊）；**滑鼠直接點擊門板**或走近按 **`F` 鍵**即可觸發合頁向室內側平滑旋轉 95° 開關動畫，關門時具動態碰撞阻擋、開門即順暢走入。
  - **第一／第三人稱小人與全校梯口自動上下樓**：點左側 `🚶 步行` 或於四棟任一教室卡片按 `🚶 進教室` 進入；提供 13 個全校快速傳送點，支援 `WASD`／方向鍵移動、`Shift` 跑步、滑鼠拖曳／PointerLock 準心轉頭、滾輪縮放、`V` 鍵切換第一／第三人稱，並內建**一鍵換裝鈕（`👕 運動服`／`👔 男生制服`／`👗 女生制服`，快捷鍵 `C`）**還原重慶國小夏季運動服、藍白格紋領男生制服與白娃娃領深丈青百褶裙女生制服；全校 **1 梯～9 梯＋廣和樓電梯**梯口可按 `E` 上樓／`Q` 下樓自動爬升轉場。
- **🔄 免開 Blender 前端動態門牌熱更新（`dynamic_plaques.js`）**：前端載入 GLB 後於背景非同步依 `campus_cges.json` 即時重繪全校 **127 面走廊 3D 雙面門牌貼圖**並熱替換至 `Campus_CorridorRoomPlaques`（桌機 2048²／手機 1024²），未來跨學年度異動班級只需修改 `campus_cges.json`，免重跑 Blender 與 GLB 即刻同步更新。
- **URL Hash 深層連結＆一鍵分享（`🔗 分享`）**：點選任一教室即更新網址 Hash（支援瀏覽器上一頁／下一頁與 RWD 響應式版面），並可一鍵複製直達該教室的 3D 導覽連結。

### 2. 四面實景建築與校園場域 1:1 精細還原
- **西側廣和街（31 號正門與廣和樓）**：
  - 紅磚半圓拱警衛室、雙色連鎖磚與灰磚分隔帶入口退縮車道、警衛室旁 4 格寬淺米白石板磚行人緩坡、門內暖淺米黃前庭廣場＋白色導引框線。
  - **廣和樓屋頂半圓拱山牆**：1:1 重製 **1024×1024 馬賽克小方磚 6 條雙色灰綠校徽 LOGO**、淡粉紅磚矩形截面半圓鏤空拱圈、兩側雙格粉磚凹龕、階梯抬升女兒牆與屋頂避雷針。
  - 廣和樓↔和平／重慶 **5F 雙圓洞立體連廊**，以及前庭南側通往重慶樓 1F「**圖書室 Library**」門廊之 **10 級磨石子大寬階梯＋白磚斜護牆扶手**。
- **南側廣和街（重慶樓南翼＆ 3 號後門）**：
  - 重慶樓東端 **5F 中空半圓弧開放陽台塔**＋L 型深凹連廊、馬賽克花磚與紅磚鏤空圍牆。
  - **露天雙全場壓克力籃球場（2048×1280）**：標準三分線、禁區罰球實虛線、搶籃板分位格與籃下免責半圓，搭配 4 座深鐵灰懸臂＋寶藍防撞墊籃球架與立體籃網；貼齊重慶／五權 1F 走廊補齊步下階梯、排水明溝與磨石子緩衝步道。
- **東側五權街（五權樓＆ 200m 操場）**：
  - 五權樓 1F–5F 直立彩繪宣傳布條、1F 無障礙長斜坡步道、**連建式八角升旗司令台**、中北段三開間寬階梯＋雙鐵捲門大穿堂、9 梯服務立面與北端彩繪寬階梯。
  - 200m 六線道紅 PU 操場（含 100m 直線延長衝刺道）、東側全寬磨石子大道、東北角雙半場水泥籃球場與涼亭、東南角器材遮雨棚、爬竿架與高低單槓體健區。
- **北側和平路（和平樓、海豚天橋＆運動中心）**：
  - 和平樓北側半圓弧陽台塔、B1 雙鐵捲門與 147B 操場側門、藍色海豚彩繪跨路人行天橋與重慶國小綜合運動中心玻璃金字塔天窗。

### 3. 前端效能與自給自足架構
- **Draco (Level 6) + WebP (q88) 壓縮 GLB**：全校 **388 個 3D 物件**（含四棟中空室內與門框）壓縮至 **5.53 MB**，載入畫面具備即時進度條與 Gzip Chunked 精準百分比回退。
- **完全自託管資源**：Three.js r187 核心、Addons 與 Draco WASM 解碼器完整打包於 `vendor/three/`，全站採用相對路徑，無外部 CDN 單點故障。
- **按需渲染（On-Demand Rendering）＋ 靜態 4096² 陰影圖**：視角靜止時停止重繪以節省電力與 GPU 資源。

---

## 🗂 專案檔案結構

| 檔案／目錄 | 說明 |
|---|---|
| `index.html` / `preview.html` | 3D 校園導覽網頁入口（含官方重慶國小校徽 `favicon.ico` / `apple-touch-icon.png` 與 OpenGraph 預覽設定） |
| `tour_app.js` / `tour_ui.css` | Three.js 導覽核心、115 學年度分類篩選、URL Hash 深層連結分享、載入進度條、3D 樓層高亮、測距尺與三時段日照切換 |
| `campus_routing.js` | 全校 148 處空間跨棟跨樓層點對點步行導引引擎（3 校門 + 148 空間任選起點、狀態擴展 Dijkstra、`1梯～9梯／電梯` 與無障礙模式） |
| `dynamic_plaques.js` | 免開 Blender 前端動態 3D 走廊雙面門牌熱更新引擎（依 `campus_cges.json` 背景重繪 8×16 UV Atlas 並熱替換貼圖） |
| `walk_mode.js` / `walk_data_campus.json` | 桌機全校四棟自由步行控制器（第一／第三人稱去積木感圓潤三態制服小人、門框內嵌式對內推開木門點擊／`F` 鍵開關動畫與門板碰撞、全校 1–9 梯／電梯 `E`/`Q` 自動上下樓、2F–5F 四棟雙圓洞連廊與轉角跨棟連通定位、InstancedMesh 黑板桌椅／圖書室／視聽中心家具）及 Blender 輸出之全校 164 扇互動門與牆體碰撞資料 |
| `campus_cges.json` | 單一真相來源資料庫（4 棟建築幾何規格、6 大分區邊界鏡頭＋全校 148 處空間 3D 座標） |
| `exports/cges_campus.glb` | Draco + WebP 壓縮後之全校 3D 模型（5.53 MB，388 物件） |
| `build_meta.json` | 建置版本、檔案位元組與 MD5 雜湊（供前端進度條與快取驗證） |
| `coords.py` / `geom_primitives.py` | 四面街道斜率基準線、校園座標常數與共用 `bmesh` 幾何／UV 原語 |
| `gen_cges_textures.py` / `materials_cges.py` | 程式化 PBR 貼圖產生器（含 4K 班級門牌 Atlas、校徽馬賽克、雙籃球場、前庭廣場與招牌）與 Blender 材質庫 |
| `mod_campus_bldg.py` / `mod_walk_interior.py` | 四棟教學／行政大樓、雙圓洞連廊、前庭大階梯，以及全校 4 棟中空教室開洞、門框與步行碰撞匯出模組 |
| `mod_campus_grounds.py` | 四周道路與雙色地磚廣場、200m+100m 跑道、司令台、南北雙籃球場、體健器材、中庭生態池與植栽模組 |
| `mod_campus_landmarks.py` | 主校門警衛室、馬賽克圍牆、運動中心、海豚天橋與重慶／和平半圓弧陽台塔模組 |
| `mod_campus_street_details.py` | 雙面走廊門牌、街道標誌、汽機車與公車候車亭細節模組 |
| `build_campus.py` | Blender 5.3 Headless 總裝、Draco/WebP GLB 匯出與 EEVEE/Cycles 算圖驗證管線 |
| `test_campus_integrity.py` | 自動化完整性測試腳本（Python 語法編譯、`zones` 與 127 門牌 Atlas 映射、GLB Hash 與前端資源檢查） |
| `serve_preview.mjs` | 本地零相依 Node.js 靜態預覽伺服器（預設 `http://localhost:8777`） |
| `.github/workflows/pages.yml` | GitHub Pages 自動部署工作流（同步發布至 `gh-pages` 分支） |

---

## 🚀 本地啟動、驗證與重建指令

### 1. 啟動本地 3D 導覽伺服器
```powershell
node serve_preview.mjs
# 開啟瀏覽器造訪 http://localhost:8777
```

### 2. 重新生成貼圖並重建匯出壓縮 GLB
```powershell
python gen_cges_textures.py
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python-exit-code 1 --python build_campus.py -- --export-only
```

### 3. 執行自動化完整性測試與 JS 語法檢查
```powershell
python test_campus_integrity.py
node --check campus_routing.js
node --check dynamic_plaques.js
node --check walk_mode.js
node --check tour_app.js
```
