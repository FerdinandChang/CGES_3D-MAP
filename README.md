# 新北市板橋區重慶國民小學 115 學年度 3D 校園數位雙生導覽系統 (`CGES_3D-MAP`)

以 **Blender 5.3 Headless (`bpy` / `bmesh`) 程式化 3D 建模**、**程式化 PBR 貼圖管線**與 **Three.js WebGL 互動導覽前端**打造之「新北市板橋區重慶國民小學（220 新北市板橋區廣和街 31 號）」1:1 寫實 3D 校園空間與 115 學年度教室配置導覽系統。

---

## 🌐 線上瀏覽網址與深層連結 (GitHub Pages)

- **線上 3D 導覽首頁**：https://ferdinandchang.github.io/CGES_3D-MAP/
- **指定空間直達連結範例（Deep Linking）**：
  - 校長室：https://ferdinandchang.github.io/CGES_3D-MAP/#room=305
  - 指定班級：https://ferdinandchang.github.io/CGES_3D-MAP/#room=六年7班
  - 指定樓棟樓層：https://ferdinandchang.github.io/CGES_3D-MAP/#zone=Bldg_Wuquan&floor=3F
- **GitHub 專案儲存庫**：https://github.com/FerdinandChang/CGES_3D-MAP
- **學校官網參考基準**：https://www.cges.ntpc.edu.tw/（站點圖示 `favicon.ico` 與官網同步）

---

## ✨ 核心功能與實景重製亮點

### 1. 115 學年度全校 148 處空間 1:1 定位＋深層分享
- **單一真相來源（Single Source of Truth）**：由 `campus_cges.json` 統一驅動建築規格、6 大分區邊界、預設鏡頭與全校 **148 處空間**（4 棟 5F 校舍 **127 間**室內空間＋運動中心與戶外操場球場 **21 處**空間）。
- **雙面正字走廊門牌 Atlas**：走廊懸掛 **4096×4096 雙面無反字班級門牌**，正反雙向皆呈現端正繁體班級與房號。
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
- **Draco (Level 6) + WebP (q88) 壓縮 GLB**：全校 **386 個 3D 物件**壓縮至 **5.28 MB**（gzip 傳輸低於 5 MB），載入畫面具備即時進度條與 Gzip Chunked 精準百分比回退。
- **完全自託管資源**：Three.js r187 核心、Addons 與 Draco WASM 解碼器完整打包於 `vendor/three/`，全站採用相對路徑，無外部 CDN 單點故障。
- **按需渲染（On-Demand Rendering）＋ 靜態 4096² 陰影圖**：視角靜止時停止重繪以節省電力與 GPU 資源。

---

## 🗂 專案檔案結構

| 檔案／目錄 | 說明 |
|---|---|
| `index.html` / `preview.html` | 3D 校園導覽網頁入口（含官方重慶國小校徽 `favicon.ico` / `apple-touch-icon.png` 與 OpenGraph 預覽設定） |
| `tour_app.js` / `tour_ui.css` | Three.js 導覽核心、115 學年度分類篩選、URL Hash 深層連結分享、載入進度條、3D 樓層高亮、測距尺與三時段日照切換 |
| `campus_cges.json` | 單一真相來源資料庫（4 棟建築幾何規格、6 大分區邊界鏡頭＋全校 148 處空間 3D 座標） |
| `exports/cges_campus.glb` | Draco + WebP 壓縮後之全校 3D 模型（5.28 MB，386 物件） |
| `build_meta.json` | 建置版本、檔案位元組與 MD5 雜湊（供前端進度條與快取驗證） |
| `coords.py` / `geom_primitives.py` | 四面街道斜率基準線、校園座標常數與共用 `bmesh` 幾何／UV 原語 |
| `gen_cges_textures.py` / `materials_cges.py` | 程式化 PBR 貼圖產生器（含 4K 班級門牌 Atlas、校徽馬賽克、雙籃球場、前庭廣場與招牌）與 Blender 材質庫 |
| `mod_campus_bldg.py` | 四棟教學／行政大樓、雙圓洞連廊與前庭通往重慶樓大階梯建模模組 |
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
node --check tour_app.js
```
