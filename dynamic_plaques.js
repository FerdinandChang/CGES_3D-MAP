/**
 * 免開 Blender 前端動態 3D 走廊雙面門牌熱更新引擎
 * 直接讀取 campus_cges.json（單一真相來源），以 HTML5 Canvas 即時重繪 8×16 雙面門牌 UV Atlas
 * 並熱替換 GLB 內 Campus_CorridorRoomPlaques 的材質貼圖。
 * 未來跨學年度異動班級／處室名稱時，僅需編輯 campus_cges.json 即可同步更新全校 127 面 3D 實體門牌。
 */
import * as THREE from "three";

const CAT_RGB = {
  grade1: "#a855f7",
  grade2: "#ec4899",
  grade3: "#f97316",
  grade4: "#eab308",
  grade5: "#65a30d",
  grade6: "#0284c7",
  youxue: "#ea8a2e",
  kinder: "#f43f5e",
  admin: "#4f46e5",
  special: "#0d9488",
  public: "#64748b",
};

const SHORT_OVERRIDE = {
  "健康中心（保健室）": "健康中心",
  "圖書室（彩繪火車廊道）": "圖書室",
  "五權樓穿堂（連建司令台）": "五權樓穿堂",
  "五權樓 2F 陽台／無障礙廁所": "無障礙廁所",
  "表演準備室／教師會辦公室": "表演準備室",
  "幼兒園辦公室／親職中心": "幼兒園辦公室",
  "往體育館海豚天橋連通口": "往體育館天橋",
  "社會科／自然科辦公室": "社會自然室",
  "無障礙男女廁所": "無障礙廁所",
  "北側無障礙廁所": "無障礙廁所",
  "中段無障礙廁所": "無障礙廁所",
  "北側男女廁所": "男女廁所",
  "中段男女廁所": "男女廁所",
};

const FONT_STACK = '"Microsoft JhengHei", "PingFang TC", "Noto Sans TC", system-ui, -apple-system, sans-serif';

/**
 * 依 campus_cges.json 繪製與 GLB 走廊門牌 UV 100% 像素對齊的動態 CanvasTexture
 */
export function buildDynamicPlaqueAtlasTexture(spec, { maxAniso = 8, isMobile = false } = {}) {
  const cols = 8;
  const rows = 16;
  // Desktop: 2048×2048 (256×128/cell, 4x less VRAM & instant GPU upload); Mobile: 1024×1024
  const scale = isMobile ? 0.25 : 0.5;
  const cw = 512 * scale;
  const ch = 256 * scale;

  const canvas = document.createElement("canvas");
  canvas.width = cols * cw;
  canvas.height = rows * ch;
  const ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) return null;

  ctx.fillStyle = "#f2f5f8";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const schoolShort = spec?.meta?.school_short || "重慶國小";
  const schoolFont = `700 ${Math.round(34 * scale)}px ${FONT_STACK}`;
  const codeFont = `800 ${Math.round(40 * scale)}px ${FONT_STACK}`;
  const borderW = Math.max(1.5, 6 * scale);
  let slot = 0;

  for (const b of spec?.buildings || []) {
    for (const rm of b.rooms_115_detailed || []) {
      if (slot >= cols * rows) break;
      const c = slot % cols;
      const r = Math.floor(slot / cols);
      const x0 = c * cw;
      const y0 = r * ch;

      const code = rm.code || "";
      const rawName = rm.name || "教室";
      const disp = rm.plaque_name || SHORT_OVERRIDE[rawName] || rawName;
      const fl = rm.floor || "";
      const accent = CAT_RGB[rm.cat || "public"] || "#366094";

      // 1. Crisp white body + outer navy frame
      ctx.fillStyle = "#f7f9fc";
      ctx.fillRect(x0, y0, cw, ch);
      ctx.strokeStyle = "#1c4884";
      ctx.lineWidth = borderW;
      ctx.strokeRect(x0 + 4 * scale, y0 + 4 * scale, cw - 8 * scale, ch - 8 * scale);

      // 2. Top navy school header band
      ctx.fillStyle = "#164486";
      ctx.fillRect(x0 + 6 * scale, y0 + 6 * scale, cw - 12 * scale, 74 * scale);

      ctx.fillStyle = "#ffffff";
      ctx.font = schoolFont;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(schoolShort, x0 + 24 * scale, y0 + 44 * scale);

      // 3. Top-right room code (gold) or floor badge
      const tagTxt = code || fl;
      ctx.fillStyle = "#fee876";
      ctx.font = codeFont;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(tagTxt, x0 + cw - 24 * scale, y0 + 44 * scale);

      // 4. Main classroom / class name auto-fitted in single measurement pass
      const nCh = disp.length;
      const baseSz = (nCh <= 3 ? 92 : nCh === 4 ? 78 : nCh === 5 ? 64 : nCh === 6 ? 54 : 46) * scale;
      const maxTextW = cw - 44 * scale;
      ctx.font = `800 ${Math.round(baseSz)}px ${FONT_STACK}`;
      const measuredW = ctx.measureText(disp).width;
      if (measuredW > maxTextW && measuredW > 1) {
        const fittedSz = Math.max(26 * scale, Math.floor(baseSz * (maxTextW / measuredW)));
        ctx.font = `800 ${fittedSz}px ${FONT_STACK}`;
      }
      ctx.fillStyle = "#142034";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(disp, x0 + cw * 0.5, y0 + 158 * scale);

      // 5. Bottom category color stripe
      ctx.fillStyle = accent;
      ctx.fillRect(x0 + 7 * scale, y0 + ch - 24 * scale, cw - 14 * scale, 17 * scale);

      slot++;
    }
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.flipY = false; // Match GLTF 2.0 top-left UV origin
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = Math.min(16, maxAniso);
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.generateMipmaps = true;
  tex.needsUpdate = true;
  return { texture: tex, count: slot };
}

/**
 * 將動態門牌貼圖熱替換至 GLB 場景中的 Campus_CorridorRoomPlaques 網格
 */
export function applyDynamicRoomPlaques(rootModel, spec, { maxAniso = 8, isMobile = false } = {}) {
  if (!rootModel || !spec?.buildings?.length) return null;
  let targetMesh = null;
  rootModel.traverse((obj) => {
    if (obj.isMesh && obj.name === "Campus_CorridorRoomPlaques") {
      targetMesh = obj;
    }
  });
  if (!targetMesh) return null;

  const built = buildDynamicPlaqueAtlasTexture(spec, { maxAniso, isMobile });
  if (!built) return null;

  const mats = Array.isArray(targetMesh.material) ? targetMesh.material : [targetMesh.material];
  for (const m of mats) {
    if (!m) continue;
    const oldMap = m.map;
    m.map = built.texture;
    m.needsUpdate = true;
    if (oldMap && oldMap !== built.texture) {
      oldMap.dispose?.();
    }
  }
  return built;
}
