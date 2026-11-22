# 新北市板橋區重慶國民小學 115 學年度 3D 校園數位雙生導覽系統 (`CGES_3D-MAP`)

以 **Blender 5.3 Headless (`bpy` / `bmesh`) 程式化 3D 建模**、**程式化 PBR 貼圖管線**與 **Three.js WebGL 互動導覽前端**打造之「新北市板橋區重慶國民小學（新北市板橋區廣和街 31 號）」1:1 寫實 3D 校園空間與 115 學年度教室配置導覽系統。

## 🌐 線上瀏覽網址 (GitHub Pages)

- **線上 3D 導覽網站**：https://ferdinandchang.github.io/CGES_3D-MAP/
- **GitHub 專案儲存庫**：https://github.com/FerdinandChang/CGES_3D-MAP

> 若首次推送後 GitHub Pages 尚未自動開啟，請至 GitHub Repo → **Settings** → **Pages** → **Build and deployment** 將 **Source** 選為 **GitHub Actions**（或選 **Deploy from a branch** → `main` / `/ (root)`），約 30 秒即可發布上線。

---

## ✨ 核心特色

1. **115 學年度全校 148 處空間 1:1 定位與雙面正字走廊門牌**：
   - 依據重慶國小官網最新《115 學年度班級配置圖》完整收錄 **廣和樓、和平樓、五權樓、重慶樓、運動中心＆海豚天橋、操場與戶外空間** 共 148 處空間（含一至六年級 50 班、優學班、附設幼兒園、行政處室、專科教室、樓梯與穿堂）。
   - 走廊懸掛 **4096×4096 雙面實體無反字教室門牌 Atlas**，正反雙向皆呈現端正繁體班級與房號。
2. **四面街景與校園建築 1:1 實景校準**：
   - **西側廣和街（31 號正門）**：半圓拱紅磚警衛室、廣和樓挑高穿堂與弧形校徽山牆、廣和↔和平／重慶 5F 雙圓洞立體連廊、智慧化停車柱與綠底行穿線。
   - **北側和平路**：跨路藍色海豚彩繪人行天橋、運動中心玻璃金字塔天窗、和平樓北側半圓弧陽台塔、B1 雙鐵捲門與 147B 操場側門。
   - **東側五權街**：五權樓 1F–5F 直立彩繪大型宣傳布條、1F 無障礙長斜坡步道、連建式八角升旗司令台、中北段三開間大寬階梯＋雙鐵捲門大穿堂、9 梯服務立面、北端彩繪寬階梯、全寬淺灰方格磨石子大道、200m 六線道紅 PU 跑道（含 100m 直線延長衝刺道）、東北角雙半場露天水泥籃球場與涼亭、東側不鏽鋼爬竿架＆高低單槓體健區。
   - **南側廣和街（3 號後門）**：紅磚鏤空花格與馬賽克拼貼圍牆、重慶樓東端 5F 中空半圓弧開放陽台塔與 L 型深凹連廊、南側露天薄荷綠雙籃球場與兒童遊戲場。
3. **高效能 WebGL 前端優化**：
   - **Draco + WebP 壓縮 GLB**：模型體積由 21.5 MB 壓縮至 **5.1 MB**（縮減 76%）。
   - **Build-Hash 智慧快取（`build_meta.json`）**：僅於模型重建時更新雜湊，重複開啟零等待。
   - **靜態 4096² 陰影圖 ＋ 按需渲染（On-Demand Rendering）**：視角靜止時自動暫停重繪，GPU 閒置負載降至 0%。

---

## 🗂 專案檔案結構

| 檔案／目錄 | 說明 |
|---|---|
| `index.html` / `preview.html` | 3D 校園導覽系統網頁入口（使用相對路徑，支援 GitHub Pages 子目錄與本地伺服器） |
| `tour_app.js` / `tour_ui.css` | Three.js 導覽核心、115 學年度分類篩選、即時搜尋、3D 樓層高亮、測距尺與三時段日照切換 |
| `campus_cges.json` | 全校建築幾何規格與 148 處空間 3D 座標資料庫 |
| `exports/cges_campus.glb` | Draco + WebP 壓縮後之全校 3D 模型（5.1 MB，372 物件） |
| `build_meta.json` | 建置版本與 MD5 雜湊資訊（供前端快取控制） |
| `coords.py` / `geom_primitives.py` | 四面街道斜率基準線、校園座標常數與共用 bmesh 幾何／UV 原語 |
| `gen_cges_textures.py` / `materials_cges.py` | 程式化 PBR 貼圖產生器（含 4K 班級門牌 Atlas）與 Blender 材質庫 |
| `mod_campus_bldg.py` | 四棟教學／行政大樓與雙圓洞連廊建模模組 |
| `mod_campus_grounds.py` | 周邊道路、200m+100m 跑道、連建司令台、南北籃球場、體健器材、中庭生態池與植栽模組 |
| `mod_campus_landmarks.py` | 校門警衛室、馬賽克圍牆、運動中心、海豚天橋與重慶樓半圓弧陽台塔模組 |
| `mod_campus_street_details.py` | 雙面走廊門牌、街道標誌、汽機車與公車候車亭細節模組 |
| `build_campus.py` | Blender 5.3 Headless 總裝、Draco/WebP GLB 匯出與 EEVEE/Cycles 算圖管線 |
| `serve_preview.mjs` | 本地零相依 Node.js 靜態預覽伺服器（預設 `http://localhost:8777`） |

---

## 🚀 本地啟動與重建指令

### 1. 啟動本地 3D 導覽伺服器
```powershell
node serve_preview.mjs
# 開啟瀏覽器造訪 http://localhost:8777
```

### 2. 重新生成程式化貼圖並匯出壓縮 GLB
```powershell
python gen_cges_textures.py
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python-exit-code 1 --python build_campus.py -- --export-only
```
