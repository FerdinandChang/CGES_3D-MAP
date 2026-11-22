import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const THREE_ROOT = path.resolve(ROOT, "vendor", "three");
const PORT = Number(process.env.PORT || 8777);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".glb": "model/gltf-binary",
  ".wasm": "application/wasm",
  ".webp": "image/webp",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".gif": "image/gif",
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url || "/", `http://localhost:${PORT}`);
  let p = decodeURIComponent(url.pathname);
  if (p === "/" || p === "/preview.html") p = "/index.html";

  let fullPath;
  if (p.startsWith("/three/")) {
    fullPath = path.resolve(THREE_ROOT, p.slice("/three/".length));
    if (!fullPath.startsWith(THREE_ROOT + path.sep)) {
      res.writeHead(403);
      return res.end("Forbidden");
    }
  } else {
    fullPath = path.resolve(ROOT, p.replace(/^\/+/, ""));
    if (!fullPath.startsWith(ROOT + path.sep) && fullPath !== ROOT) {
      res.writeHead(403);
      return res.end("Forbidden");
    }
  }

  fs.stat(fullPath, (err, st) => {
    if (err || !st.isFile()) {
      res.writeHead(404);
      return res.end("Not Found: " + p);
    }
    const ext = path.extname(fullPath).toLowerCase();
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    fs.createReadStream(fullPath).pipe(res);
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`CGES_PREVIEW_READY: http://localhost:${PORT}`);
});
