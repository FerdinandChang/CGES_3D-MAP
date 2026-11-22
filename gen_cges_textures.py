"""生成新北市板橋區重慶國小高細節 PBR 貼圖與法線貼圖（對照官網校景與 2025/05 街景）。"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
os.makedirs(TEX_DIR, exist_ok=True)


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\msjhbd.ttc" if bold else r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\kaiu.ttf",
        r"C:\Windows\Fonts\mingliu.ttc",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _height_to_normal(height_img: Image.Image, strength: float = 2.2) -> Image.Image:
    """將灰階高度圖轉為切線空間法線貼圖 (Tangent-Space Normal Map)。"""
    w, h = height_img.size
    hp = height_img.load()
    nrm = Image.new("RGB", (w, h), (128, 128, 255))
    npix = nrm.load()
    for y in range(h):
        ym = (y - 1) % h
        yp = (y + 1) % h
        for x in range(w):
            xm = (x - 1) % w
            xp = (x + 1) % w
            dx = (hp[xp, y] - hp[xm, y]) / 255.0 * strength
            dy = (hp[x, yp] - hp[x, ym]) / 255.0 * strength
            nx, ny, nz = -dx, -dy, 1.0
            inv = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
            npix[x, y] = (
                int((nx * inv * 0.5 + 0.5) * 255),
                int((ny * inv * 0.5 + 0.5) * 255),
                int((nz * inv * 0.5 + 0.5) * 255),
            )
    return nrm


def gen_tile_wall_pbr(
    base_name: str,
    base_rgb: tuple[int, int, int],
    grout_rgb: tuple[int, int, int],
    cols: int = 16,
    rows: int = 16,
    jitter: int = 7,
    size: int = 512,
    seed: int = 42,
    stagger: bool = False,
) -> None:
    """產出磁磚 Base Color + Normal Map（含微細灰縫凹陷與微氣候污漬變化）。"""
    rng = random.Random(seed)
    im = Image.new("RGB", (size, size), grout_rgb)
    hmap = Image.new("L", (size, size), 70)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    cw = size / cols
    rh = size / rows
    gap = max(2, int(size / 220))

    for r in range(rows):
        off = (cw * 0.5) if (stagger and r % 2 == 1) else 0.0
        for c in range(-1, cols + 1):
            d = rng.randint(-jitter, jitter)
            # Subtle warm/cool weathering variance
            w_shift = rng.randint(-4, 4)
            col = (
                max(0, min(255, base_rgb[0] + d + w_shift)),
                max(0, min(255, base_rgb[1] + d)),
                max(0, min(255, base_rgb[2] + d - w_shift // 2)),
            )
            x0 = int(c * cw + off) + gap
            y0 = int(r * rh) + gap
            x1 = int((c + 1) * cw + off) - gap
            y1 = int((r + 1) * rh) - gap
            draw.rectangle([x0, y0, x1, y1], fill=col)
            h_val = 215 + rng.randint(-12, 12)
            hdraw.rectangle([x0, y0, x1, y1], fill=h_val)

    # Subtle vertical rain-streak weathering
    for _ in range(45):
        sx = rng.randint(0, size - 1)
        sy = rng.randint(0, size - 40)
        slen = rng.randint(25, 110)
        draw.line([(sx, sy), (sx, min(size - 1, sy + slen))], fill=grout_rgb, width=1)

    im.save(os.path.join(TEX_DIR, f"{base_name}.png"))
    nrm = _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.4)
    nrm.save(os.path.join(TEX_DIR, f"{base_name}_nrm.png"))


def gen_south_mosaic_wall() -> None:
    """還原廣和街南側極具特色之混凝土柱＋紅磚斜格花磚＋粉彩馬賽克圍牆（對照 final_step_105.png）。"""
    w, h = 1024, 512
    im = Image.new("RGB", (w, h), (138, 136, 132))  # gray concrete frame
    hmap = Image.new("L", (w, h), 200)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    rng = random.Random(305)

    # Subtle concrete grain
    for _ in range(6000):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(-14, 14)
        draw.point((x, y), fill=(138 + d, 136 + d, 132 + d))

    # 3 bays across texture width: [lattice] [mosaic center + upper lattice] [lattice]
    def draw_red_lattice(x0: int, y0: int, x1: int, y1: int) -> None:
        bw, bh = x1 - x0, y1 - y0
        sub = Image.new("RGB", (bw, bh), (54, 44, 42))
        hsub = Image.new("L", (bw, bh), 45)
        sd = ImageDraw.Draw(sub)
        hsd = ImageDraw.Draw(hsub)
        step = 26
        for k in range(-bh, bw + bh, step):
            sd.line([(k, 0), (k + bh, bh)], fill=(158, 86, 72), width=7)
            sd.line([(k + bh, 0), (k, bh)], fill=(158, 86, 72), width=7)
            hsd.line([(k, 0), (k + bh, bh)], fill=175, width=7)
            hsd.line([(k + bh, 0), (k, bh)], fill=175, width=7)
        im.paste(sub, (x0, y0))
        hmap.paste(hsub, (x0, y0))
        draw.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], outline=(136, 134, 130), width=8)

    def draw_pastel_mosaic(x0: int, y0: int, x1: int, y1: int) -> None:
        palette = [
            (132, 152, 184),
            (218, 206, 168),
            (172, 168, 162),
            (226, 222, 212),
            (156, 174, 198),
            (204, 186, 146),
        ]
        tile = 24
        for ty in range(y0, y1, tile):
            for tx in range(x0, x1, tile):
                col = rng.choice(palette)
                draw.rectangle([tx + 1, ty + 1, min(x1, tx + tile - 1), min(y1, ty + tile - 1)], fill=col)
                hdraw.rectangle([tx + 1, ty + 1, min(x1, tx + tile - 1), min(y1, ty + tile - 1)], fill=195)

    # Top concrete coping & lower wall plinth
    draw.rectangle([0, 0, w, 46], fill=(122, 120, 116))
    draw.rectangle([0, h - 70, w, h], fill=(128, 126, 122))

    # Left bay: upper + lower red brick lattice
    draw_red_lattice(36, 68, 300, 195)
    draw_red_lattice(36, 225, 300, 425)
    # Center bay: upper red lattice + lower pastel mosaic panel!
    draw_red_lattice(360, 68, 664, 195)
    draw_pastel_mosaic(360, 225, 664, 425)
    # Right bay: upper + lower red brick lattice
    draw_red_lattice(724, 68, 988, 195)
    draw_red_lattice(724, 225, 988, 425)

    # Vertical concrete columns between bays
    for cx in (0, 315, 680, 1002):
        draw.rectangle([cx, 0, cx + 30, h], fill=(134, 132, 128))
        hdraw.rectangle([cx, 0, cx + 30, h], fill=245)

    im.save(os.path.join(TEX_DIR, "tex_wall_south_mosaic.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=1.0)), strength=2.6).save(
        os.path.join(TEX_DIR, "tex_wall_south_mosaic_nrm.png")
    )


def gen_solar_panel() -> None:
    size = 512
    im = Image.new("RGB", (size, size), (196, 204, 212))
    hmap = Image.new("L", (size, size), 230)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    cols, rows = 2, 4
    pw, ph = size // cols, size // rows
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * pw + 5, r * ph + 5
            x1, y1 = (c + 1) * pw - 5, (r + 1) * ph - 5
            draw.rectangle([x0, y0, x1, y1], fill=(18, 30, 56))
            hdraw.rectangle([x0, y0, x1, y1], fill=140)
            for sc in range(1, 6):
                sx = x0 + int((x1 - x0) * sc / 6)
                draw.line([(sx, y0), (sx, y1)], fill=(48, 72, 112), width=1)
            for sr in range(1, 4):
                sy = y0 + int((y1 - y0) * sr / 4)
                draw.line([(x0, sy), (x1, sy)], fill=(48, 72, 112), width=1)
    im.save(os.path.join(TEX_DIR, "tex_solar_panel.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.0).save(
        os.path.join(TEX_DIR, "tex_solar_panel_nrm.png")
    )


def gen_school_sign() -> None:
    w, h = 1024, 256
    im = Image.new("RGB", (w, h), (72, 52, 38))
    draw = ImageDraw.Draw(im)
    rng = random.Random(101)
    for _ in range(4500):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(-12, 12)
        draw.point((x, y), fill=(max(0, 72 + d), max(0, 52 + d), max(0, 38 + d)))

    draw.rectangle([8, 8, w - 9, h - 9], outline=(168, 148, 122), width=4)
    draw.rectangle([32, 46, 308, 210], fill=(88, 70, 56), outline=(188, 168, 142), width=3)
    f_en = _get_font(16, bold=False)
    draw.text((46, 86), "Chongqing Elementary School,", fill=(238, 228, 206), font=f_en)
    draw.text((46, 120), "Banqiao Dist., New Taipei City", fill=(238, 228, 206), font=f_en)

    f_zh = _get_font(82, bold=True)
    text = "重 慶 國 民 小 學"
    draw.text((349, 83), text, fill=(32, 20, 10), font=f_zh)
    draw.text((344, 78), text, fill=(232, 194, 92), font=f_zh)
    im.save(os.path.join(TEX_DIR, "tex_school_sign.png"))


def gen_emblem_cges() -> None:
    size = 512
    im = Image.new("RGB", (size, size), (232, 226, 220))
    draw = ImageDraw.Draw(im)
    # Subtle stone tile lines on emblem plaque
    for i in range(0, size, 64):
        draw.line([(i, 0), (i, size)], fill=(214, 208, 202), width=1)
        draw.line([(0, i), (size, i)], fill=(214, 208, 202), width=1)

    green = (108, 142, 122)
    shadow = (76, 98, 86)
    # Drop shadow then raised geometric green '重' emblem
    for off, col in [((6, 6), shadow), ((0, 0), green)]:
        ox, oy = off
        draw.polygon([(140 + ox, 430 + oy), (195 + ox, 430 + oy), (195 + ox, 210 + oy), (140 + ox, 210 + oy)], fill=col)
        draw.polygon([(80 + ox, 140 + oy), (225 + ox, 140 + oy), (200 + ox, 190 + oy), (110 + ox, 190 + oy)], fill=col)
        draw.polygon([(225 + ox, 430 + oy), (275 + ox, 430 + oy), (275 + ox, 240 + oy), (420 + ox, 175 + oy), (420 + ox, 125 + oy), (225 + ox, 210 + oy)], fill=col)
        draw.polygon([(295 + ox, 430 + oy), (345 + ox, 430 + oy), (345 + ox, 290 + oy), (425 + ox, 255 + oy), (425 + ox, 205 + oy), (295 + ox, 260 + oy)], fill=col)
        draw.polygon([(170 + ox, 90 + oy), (370 + ox, 90 + oy), (350 + ox, 130 + oy), (190 + ox, 130 + oy)], fill=col)
    im.save(os.path.join(TEX_DIR, "tex_emblem_cges.png"))


def gen_facade_banner(filename: str, word: str, en_word: str, bg_grad: tuple[tuple[int, int, int], tuple[int, int, int]], accent: tuple[int, int, int]) -> None:
    w, h = 1024, 192
    im = Image.new("RGB", (w, h), bg_grad[0])
    draw = ImageDraw.Draw(im)
    for x in range(w):
        t = x / (w - 1)
        col = tuple(int(bg_grad[0][i] * (1 - t) + bg_grad[1][i] * t) for i in range(3))
        draw.line([(x, 0), (x, h)], fill=col)

    rng = random.Random(hash(word) & 0xFFFF)
    palette = [(252, 214, 78), (105, 198, 238), (244, 138, 172), (138, 214, 128), (255, 252, 246), (252, 168, 92)]
    # Richer circular photo-collage rings matching campus_01.jpg
    for i in range(42):
        cx = rng.randint(30, w - 265)
        cy = rng.randint(22, h - 22)
        r = rng.randint(16, 44)
        col = palette[i % len(palette)]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(255, 255, 255), width=3)
        if r > 26:
            # Inner mini stylized silhouette circle
            draw.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2], fill=palette[(i + 2) % len(palette)])

    draw.rounded_rectangle([w - 252, 20, w - 26, h - 20], radius=24, fill=accent, outline=(255, 255, 255), width=5)
    f = _get_font(72, bold=True)
    draw.text((w - 224, 30), word, fill=(255, 255, 255), font=f)
    fe = _get_font(22, bold=True)
    draw.text((w - 208, 126), en_word, fill=(255, 245, 230), font=fe)
    im.save(os.path.join(TEX_DIR, filename))


def gen_led_campus() -> None:
    """廣和樓 2F 右側大型戶外電子看板畫面（還原 final_step_32.png）。"""
    w, h = 512, 320
    im = Image.new("RGB", (w, h), (34, 48, 72))
    draw = ImageDraw.Draw(im)
    draw.rectangle([12, 12, w - 12, h - 12], fill=(224, 76, 62))
    draw.rectangle([28, 28, w - 28, h - 92], fill=(248, 238, 214))
    # Stylized colorful student celebration poster inside LED screen
    for i, col in enumerate([(242, 108, 78), (248, 196, 62), (76, 178, 122), (68, 148, 216)]):
        draw.ellipse([48 + i * 95, 58, 132 + i * 95, 142], fill=col)
    f1 = _get_font(34, bold=True)
    f2 = _get_font(26, bold=True)
    draw.text((54, 160), "重慶國小  活力校園", fill=(42, 48, 66), font=f1)
    draw.text((78, 248), "勤學 • 健康 • 快樂", fill=(255, 244, 176), font=f2)
    im.save(os.path.join(TEX_DIR, "tex_led_campus.png"))


def gen_breezeway_header() -> None:
    w, h = 1024, 256
    im = Image.new("RGB", (w, h), (192, 180, 166))
    draw = ImageDraw.Draw(im)
    for x in range(0, w, 32):
        draw.line([(x, 0), (x, h)], fill=(162, 150, 138), width=1)
    for y in range(0, h, 32):
        draw.line([(0, y), (w, y)], fill=(162, 150, 138), width=1)
    f_big = _get_font(54, bold=True)
    draw.text((144, 34), "勤學     快樂     健康", fill=(128, 114, 96), font=f_big)
    draw.text((140, 30), "勤學     快樂     健康", fill=(166, 152, 130), font=f_big)
    draw.rectangle([175, 146, 849, 210], fill=(20, 18, 18), outline=(72, 72, 72), width=4)
    f_led = _get_font(34, bold=True)
    draw.text((222, 158), "歡迎蒞臨 新北市板橋區重慶國民小學", fill=(255, 58, 42), font=f_led)
    im.save(os.path.join(TEX_DIR, "tex_breezeway_header.png"))


def gen_basketball_court() -> None:
    """高細節 2048x1280 雙全場壓克力 PU 籃球場貼圖（含三分線直線＋圓弧、罰球圈實虛線、禁區搶籃板分位格、免責半圓與水泥伸縮縫）。"""
    w, h = 2048, 1280
    apron_col = (196, 108, 82)
    court_col = (134, 178, 150)
    key_col = (204, 112, 84)
    wline = (246, 248, 246)

    im = Image.new("RGB", (w, h), apron_col)
    draw = ImageDraw.Draw(im)
    pad_x, pad_y = 82, 74
    draw.rectangle([pad_x, pad_y, w - pad_x, h - pad_y], fill=court_col)

    # Subtle weathered acrylic colour variation patches before drawing lines
    rng = random.Random(88)
    for _ in range(260):
        px = rng.randint(pad_x + 20, w - pad_x - 20)
        py = rng.randint(pad_y + 20, h - pad_y - 20)
        rw, rh = rng.randint(45, 160), rng.randint(45, 160)
        d = rng.randint(-6, 6)
        draw.ellipse([px - rw, py - rh, px + rw, py + rh], fill=(court_col[0] + d, court_col[1] + d, court_col[2] + d))
    im = im.filter(ImageFilter.GaussianBlur(radius=8))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w - 1, pad_y], fill=apron_col)
    draw.rectangle([0, h - pad_y, w - 1, h - 1], fill=apron_col)
    draw.rectangle([0, 0, pad_x, h - 1], fill=apron_col)
    draw.rectangle([w - pad_x, 0, w - 1, h - 1], fill=apron_col)
    draw.rectangle([pad_x, pad_y, w - pad_x, h - pad_y], outline=(232, 236, 232), width=3)

    # Concrete sub-base expansion joint grid lines across apron & court
    for gx in range(128, w, 256):
        draw.line([(gx, 0), (gx, h)], fill=(120, 158, 134), width=2)
    for gy in range(128, h, 256):
        draw.line([(0, gy), (w, gy)], fill=(120, 158, 134), width=2)

    # Fine anti-slip silica grit texture
    for _ in range(36000):
        x, y = rng.randint(4, w - 5), rng.randint(4, h - 5)
        d = rng.randint(-7, 7)
        in_green = (pad_x < x < w - pad_x) and (pad_y < y < h - pad_y)
        base = court_col if in_green else apron_col
        draw.point((x, y), fill=(base[0] + d, base[1] + d, base[2] + d))

    # Two full-size courts centered at U = 0.275 (563px) & U = 0.725 (1485px) — exact match with 3D hoop X positions!
    for mid_x in (int(w * 0.275), int(w * 0.725)):
        half_cw = 392
        cx0, cx1 = mid_x - half_cw, mid_x + half_cw
        cy0, cy1 = 118, h - 118
        mid_y = (cy0 + cy1) // 2

        # 1. North & South Ends (3-point line, key paint, free-throw solid/dashed circle, lane hash marks, restricted arc)
        kw, kh = 216, 276
        r3 = 312
        dx3 = 298
        dy3_join = int(math.sqrt(max(1, r3 * r3 - dx3 * dx3)))
        r_ft = 96
        r_nc = 60

        for is_top in (True, False):
            yb = cy0 if is_top else cy1
            sgn = 1 if is_top else -1
            hoop_y = yb + sgn * 80
            ft_y = yb + sgn * kh

            # 3-point straight corner lines + main arc
            y_join = hoop_y + sgn * dy3_join
            draw.line([(mid_x - dx3, yb), (mid_x - dx3, y_join)], fill=wline, width=8)
            draw.line([(mid_x + dx3, yb), (mid_x + dx3, y_join)], fill=wline, width=8)
            ang_deg = math.degrees(math.atan2(dy3_join, dx3))
            if is_top:
                draw.arc([mid_x - r3, hoop_y - r3, mid_x + r3, hoop_y + r3], ang_deg, 180 - ang_deg, fill=wline, width=8)
            else:
                draw.arc([mid_x - r3, hoop_y - r3, mid_x + r3, hoop_y + r3], 180 + ang_deg, 360 - ang_deg, fill=wline, width=8)

            # Terracotta painted key rectangle
            ky0, ky1 = (yb, ft_y) if is_top else (ft_y, yb)
            draw.rectangle([mid_x - kw // 2, ky0, mid_x + kw // 2, ky1], fill=key_col, outline=wline, width=8)

            # Free-throw circle: outer half solid white, inner half (inside key) 7-segment dashed white!
            ft_box = [mid_x - r_ft, ft_y - r_ft, mid_x + r_ft, ft_y + r_ft]
            if is_top:
                draw.arc(ft_box, 0, 180, fill=wline, width=7)
                for d_idx in range(7):
                    a0 = 188 + d_idx * 25
                    draw.arc(ft_box, a0, a0 + 14, fill=wline, width=7)
            else:
                draw.arc(ft_box, 180, 360, fill=wline, width=7)
                for d_idx in range(7):
                    a0 = 8 + d_idx * 25
                    draw.arc(ft_box, a0, a0 + 14, fill=wline, width=7)

            # Rebound lane hash marks & low-post neutral-zone block on both sides of the key
            for lx_side, l_sgn in ((mid_x - kw // 2, -1), (mid_x + kw // 2, 1)):
                # Low-post wide block at 96..118px from baseline
                by0_blk = yb + sgn * 96
                by1_blk = yb + sgn * 116
                bx0_b, bx1_b = sorted((lx_side, lx_side + l_sgn * 22))
                by0_b, by1_b = sorted((by0_blk, by1_blk))
                draw.rectangle([bx0_b, by0_b, bx1_b, by1_b], fill=wline)
                # 3 standard rebound ticks
                for tick_off in (156, 196, 236):
                    ty = yb + sgn * tick_off
                    draw.line([(lx_side, ty), (lx_side + l_sgn * 20, ty)], fill=wline, width=7)

            # No-charge restricted area open semicircle + short legs + hoop ring marker (clean open U-shape, not a closed D!)
            r_nc_open = 48
            nc_box = [mid_x - r_nc_open, hoop_y - r_nc_open, mid_x + r_nc_open, hoop_y + r_nc_open]
            if is_top:
                draw.arc(nc_box, 0, 180, fill=wline, width=6)
            else:
                draw.arc(nc_box, 180, 360, fill=wline, width=6)
            draw.line([(mid_x - r_nc_open, yb + sgn * 54), (mid_x - r_nc_open, hoop_y)], fill=wline, width=6)
            draw.line([(mid_x + r_nc_open, yb + sgn * 54), (mid_x + r_nc_open, hoop_y)], fill=wline, width=6)

        # 2. Outer Court Boundary, Half-Court Line, Sideline Throw-in Ticks & Center Jump Circle
        draw.rectangle([cx0, cy0, cx1, cy1], outline=wline, width=9)
        draw.line([(cx0 - 18, mid_y), (cx1 + 18, mid_y)], fill=wline, width=8)
        cr = 78
        draw.ellipse([mid_x - cr, mid_y - cr, mid_x + cr, mid_y + cr], fill=key_col, outline=wline, width=8)
        draw.line([(mid_x - cr, mid_y), (mid_x + cr, mid_y)], fill=wline, width=7)
        draw.ellipse([mid_x - 24, mid_y - 24, mid_x + 24, mid_y + 24], outline=wline, width=6)
        # Sideline coaching box & throw-in hash marks
        for sy_tick in (cy0 + 390, cy1 - 390):
            draw.line([(cx0 - 18, sy_tick), (cx0, sy_tick)], fill=wline, width=7)
            draw.line([(cx1, sy_tick), (cx1 + 18, sy_tick)], fill=wline, width=7)

    im.save(os.path.join(TEX_DIR, "tex_court_bball.png"), optimize=True)


def gen_track_pu() -> None:
    size = 512
    im = Image.new("RGB", (size, size), (148, 66, 62))
    hmap = Image.new("L", (size, size), 128)
    rng = random.Random(99)
    px = im.load()
    hp = hmap.load()
    for y in range(size):
        for x in range(size):
            d = rng.randint(-12, 12)
            px[x, y] = (148 + d, 66 + d // 2, 62 + d // 2)
            hp[x, y] = 128 + d * 4
    im.save(os.path.join(TEX_DIR, "tex_track_pu.png"))
    _height_to_normal(hmap, strength=1.2).save(os.path.join(TEX_DIR, "tex_track_pu_nrm.png"))


def gen_grass() -> None:
    """自然有機草坪紋理（自然草叢斑駁＋淡雅修剪紋理，避免人工粗條紋）。"""
    size = 512
    im = Image.new("RGB", (size, size), (84, 122, 64))
    rng = random.Random(123)
    px = im.load()
    for y in range(size):
        mow = int(math.sin(y * math.pi / 48.0) * 3.5)
        for x in range(size):
            patch = int(math.sin(x * 0.04) * math.cos(y * 0.04) * 7.0)
            d = rng.randint(-12, 12) + mow + patch
            px[x, y] = (
                max(0, min(255, 84 + d)),
                max(0, min(255, 124 + d)),
                max(0, min(255, 62 + d // 2)),
            )
    im = im.filter(ImageFilter.GaussianBlur(radius=0.4))
    im.save(os.path.join(TEX_DIR, "tex_grass.png"))


def gen_skybridge_dolphin() -> None:
    """精緻還原和平路天橋水藍海浪＋躍起海豚彩繪（對照 step_59.png）。"""
    w, h = 1024, 192
    im = Image.new("RGB", (w, h), (138, 186, 222))
    draw = ImageDraw.Draw(im)
    # Soft sky-blue gradient background
    for y in range(h):
        t = y / (h - 1)
        col = (int(156 - 46 * t), int(202 - 44 * t), int(234 - 30 * t))
        draw.line([(0, y), (w, y)], fill=col)

    # Multi-layer sweeping ocean waves
    for y_off, amp, freq, col in [
        (112, 15, 0.022, (86, 148, 196)),
        (134, 14, 0.028, (56, 114, 168)),
        (156, 10, 0.036, (36, 84, 138)),
    ]:
        pts = [(0, h)]
        for x in range(0, w + 12, 12):
            y = int(y_off + math.sin(x * freq + y_off) * amp)
            pts.append((x, y))
        pts.append((w, h))
        draw.polygon(pts, fill=col)
        # White foam crest line
        crest = [(x, int(y_off + math.sin(x * freq + y_off) * amp)) for x in range(0, w + 12, 12)]
        draw.line(crest, fill=(224, 240, 252), width=3)

    # Graceful leaping dolphin silhouettes (4 dolphins along span)
    def draw_dolphin(cx: int, cy: int, scale: float = 1.0, flip: bool = False) -> None:
        s = -scale if flip else scale
        # Streamlined arched body polygon
        body = [
            (cx - 56 * s, cy + 16 * scale),  # tail fluke base
            (cx - 32 * s, cy - 6 * scale),   # lower back
            (cx - 4 * s, cy - 22 * scale),   # dorsal crest
            (cx + 28 * s, cy - 16 * scale),  # forehead
            (cx + 52 * s, cy + 2 * scale),   # rostrum / snout tip
            (cx + 34 * s, cy + 8 * scale),   # jaw
            (cx + 8 * s, cy + 2 * scale),    # belly arch
            (cx - 24 * s, cy + 12 * scale),  # tail underside
        ]
        # Dorsal fin + tail fluke + pectoral fin
        dorsal = [(cx - 6 * s, cy - 20 * scale), (cx - 18 * s, cy - 38 * scale), (cx + 6 * s, cy - 19 * scale)]
        tail = [
            (cx - 54 * s, cy + 14 * scale),
            (cx - 72 * s, cy + 4 * scale),
            (cx - 64 * s, cy + 20 * scale),
            (cx - 70 * s, cy + 32 * scale),
            (cx - 48 * s, cy + 18 * scale),
        ]
        belly_hi = [
            (cx + 32 * s, cy + 5 * scale),
            (cx + 8 * s, cy - 2 * scale),
            (cx - 20 * s, cy + 8 * scale),
            (cx + 10 * s, cy + 4 * scale),
        ]
        dark = (26, 64, 108)
        draw.polygon(body, fill=dark)
        draw.polygon(dorsal, fill=dark)
        draw.polygon(tail, fill=dark)
        draw.polygon(belly_hi, fill=(214, 236, 250))

    draw_dolphin(170, 82, 1.05, flip=False)
    draw_dolphin(420, 74, 0.92, flip=True)
    draw_dolphin(660, 82, 1.08, flip=False)
    draw_dolphin(885, 76, 0.90, flip=True)

    # Top/bottom structural blue trim frame
    draw.rectangle([0, 0, w - 1, 10], fill=(78, 126, 168))
    draw.rectangle([0, h - 10, w - 1, h - 1], fill=(56, 98, 138))
    im.save(os.path.join(TEX_DIR, "tex_skybridge_dolphin.png"))


def gen_gym_banner() -> None:
    w, h = 1024, 224
    im = Image.new("RGB", (w, h), (46, 118, 188))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 142, w, h], fill=(238, 138, 42))
    f_big = _get_font(74, bold=True)
    draw.text((48, 34), "重慶國小運動中心", fill=(255, 255, 255), font=f_big)
    f_sub = _get_font(34, bold=True)
    draw.text((52, 158), "室內溫水游泳池  •  綜合球場  •  體適能中心", fill=(255, 255, 255), font=f_sub)
    im.save(os.path.join(TEX_DIR, "tex_gym_banner.png"))


def gen_gym_shutter() -> None:
    """運動中心入口深灰金屬捲門與玻璃大廳格紋（對照 step_63.png）。"""
    w, h = 512, 256
    im = Image.new("RGB", (w, h), (96, 94, 90))
    draw = ImageDraw.Draw(im)
    for y in range(0, h, 8):
        col = (108, 106, 102) if (y // 8) % 2 == 0 else (84, 82, 78)
        draw.line([(0, y), (w, y)], fill=col, width=4)
    # Upper ventilated grille band
    draw.rectangle([0, 0, w, 68], fill=(42, 46, 52))
    for x in range(0, w, 16):
        draw.line([(x, 0), (x, 68)], fill=(120, 124, 128), width=2)
    for y in range(0, 68, 14):
        draw.line([(0, y), (w, y)], fill=(120, 124, 128), width=2)
    im.save(os.path.join(TEX_DIR, "tex_gym_shutter.png"))


def gen_building_name_plaques() -> None:
    """產出 4 棟校舍立體棟別名牌與走廊教室門牌／樓層指示牌貼圖。"""
    for key, label, bg in [
        ("guanghe", "廣 和 樓", (142, 68, 56)),
        ("heping", "和 平 樓", (62, 108, 146)),
        ("wuquan", "五 權 樓", (74, 128, 86)),
        ("chongqing", "重 慶 樓", (156, 92, 62)),
    ]:
        w, h = 512, 160
        im = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(im)
        draw.rectangle([8, 8, w - 9, h - 9], outline=(245, 232, 198), width=5)
        f = _get_font(76, bold=True)
        draw.text((88, 36), label, fill=(255, 248, 224), font=f)
        im.save(os.path.join(TEX_DIR, f"tex_sign_{key}.png"))

    # Classroom hanging corridor plaque (藍白校園標準門牌樣式)
    w, h = 256, 128
    im = Image.new("RGB", (w, h), (246, 248, 252))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, 44], fill=(42, 106, 174))
    draw.rectangle([4, 4, w - 5, h - 5], outline=(42, 106, 174), width=4)
    f_top = _get_font(24, bold=True)
    f_num = _get_font(44, bold=True)
    draw.text((54, 8), "重慶國小", fill=(255, 255, 255), font=f_top)
    draw.text((52, 58), "教 室", fill=(32, 48, 72), font=f_num)
    im.save(os.path.join(TEX_DIR, "tex_room_plaque.png"))

    # Floor directory sign (1F-5F 樓層指示牌)
    w, h = 256, 384
    im = Image.new("RGB", (w, h), (242, 245, 248))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, 58], fill=(54, 96, 148))
    draw.rectangle([4, 4, w - 5, h - 5], outline=(54, 96, 148), width=4)
    ft = _get_font(28, bold=True)
    draw.text((48, 12), "樓層指引", fill=(255, 255, 255), font=ft)
    fl_font = _get_font(26, bold=True)
    labels = ["5F 高年級/專科", "4F 中高年級", "3F 中年級/行政", "2F 低年級/圖書", "1F 穿堂/幼兒園"]
    for idx, txt in enumerate(labels):
        y = 74 + idx * 58
        draw.rounded_rectangle([16, y, 64, y + 42], radius=8, fill=(176, 86, 68))
        draw.text((22, y + 6), txt[:2], fill=(255, 255, 255), font=fl_font)
        draw.text((76, y + 8), txt[3:], fill=(36, 44, 56), font=_get_font(22, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_floor_dir.png"))


def gen_v5_campus_interior_textures() -> None:
    """v5 新增：廣和樓藍天白雲穿堂天花板、亮橘框榮譽牆、馬賽克柱面、走廊水磨石地磚、小火車壁畫與椰子樹環紋皮。"""
    # 1. Sky-blue painted ceiling with fluffy white clouds (matching act_01/02/03/07/21/24!)
    size = 512
    im = Image.new("RGB", (size, size), (122, 178, 224))
    draw = ImageDraw.Draw(im)
    for y in range(size):
        t = y / (size - 1)
        col = (int(114 + 26 * t), int(172 + 22 * t), int(222 + 12 * t))
        draw.line([(0, y), (size, y)], fill=col)
    rng = random.Random(501)
    for cx, cy, rx, ry in [(120, 140, 88, 42), (340, 120, 96, 46), (220, 320, 110, 50), (410, 390, 82, 38), (90, 410, 74, 34)]:
        for _ in range(7):
            ox, oy = rng.randint(-rx // 2, rx // 2), rng.randint(-ry // 2, ry // 2)
            r = rng.randint(24, 48)
            draw.ellipse([cx + ox - r, cy + oy - r * 0.7, cx + ox + r, cy + oy + r * 0.7], fill=(242, 248, 254))
    im = im.filter(ImageFilter.GaussianBlur(radius=4.5))
    im.save(os.path.join(TEX_DIR, "tex_sky_ceiling.png"))

    # 2. Breezeway orange-framed honor wall (matching campus_11.jpg!)
    w, h = 1024, 384
    im = Image.new("RGB", (w, h), (236, 128, 32))  # bright orange frame
    draw = ImageDraw.Draw(im)
    # Sky & meadow mural inside orange frame
    draw.rectangle([18, 18, w - 18, h - 18], fill=(128, 206, 242))
    draw.polygon([(18, h - 18), (18, 210), (340, 155), (680, 195), (w - 18, 145), (w - 18, h - 18)], fill=(122, 194, 78))
    # Colorful school life photo collages
    rng2 = random.Random(502)
    cols = [(248, 214, 76), (242, 112, 146), (86, 168, 232), (246, 162, 74), (176, 126, 224)]
    for i in range(18):
        px = 55 + i * 50
        py = rng2.randint(150, 265)
        draw.rectangle([px, py, px + 44, py + 62], fill=cols[i % len(cols)], outline=(255, 255, 255), width=3)
    f = _get_font(62, bold=True)
    draw.text((88, 48), "勤學", fill=(42, 134, 62), font=f)
    draw.text((410, 62), "健康", fill=(228, 86, 52), font=f)
    draw.text((712, 48), "快樂", fill=(238, 132, 34), font=f)
    im.save(os.path.join(TEX_DIR, "tex_honor_wall.png"))

    # 3. Breezeway mosaic column art (matching act_06.jpg right!)
    im = Image.new("RGB", (256, 512), (82, 154, 198))
    draw = ImageDraw.Draw(im)
    rng3 = random.Random(503)
    m_cols = [(72, 148, 196), (118, 188, 122), (242, 208, 92), (228, 238, 244), (62, 128, 168), (156, 206, 108)]
    for y in range(0, 512, 16):
        for x in range(0, 256, 16):
            draw.rectangle([x + 1, y + 1, x + 15, y + 15], fill=rng3.choice(m_cols))
    im.save(os.path.join(TEX_DIR, "tex_pillar_mosaic.png"))

    # 4. Corridor gray speckled terrazzo floor + white center walking line (matching act_23.jpg!)
    size = 512
    im = Image.new("RGB", (size, size), (168, 168, 164))
    draw = ImageDraw.Draw(im)
    rng4 = random.Random(504)
    for _ in range(9000):
        x, y = rng4.randint(0, size - 1), rng4.randint(0, size - 1)
        v = rng4.choice([126, 144, 188, 204, 152])
        draw.point((x, y), fill=(v, v, v - 2))
    # Terrazzo brass expansion joints
    for i in range(0, size, 128):
        draw.line([(i, 0), (i, size)], fill=(132, 130, 126), width=2)
        draw.line([(0, i), (size, i)], fill=(132, 130, 126), width=2)
    # Iconic white center keep-right divider line
    draw.rectangle([size // 2 - 5, 0, size // 2 + 5, size], fill=(242, 244, 246))
    im.save(os.path.join(TEX_DIR, "tex_terrazzo_corridor.png"))

    # 5. Library corridor colorful train mural (matching campus_15.jpg & act_16.jpg!)
    w, h = 1024, 320
    im = Image.new("RGB", (w, h), (156, 212, 244))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 248, w, h], fill=(116, 182, 86))
    # Locomotive + 3 colorful library train cars
    cars = [
        (36, 260, (46, 148, 216), (238, 112, 52)),
        (292, 512, (238, 178, 42), (76, 168, 92)),
        (544, 764, (232, 88, 112), (248, 216, 78)),
        (796, 996, (92, 182, 114), (68, 142, 212)),
    ]
    for x0, x1, body_c, roof_c in cars:
        draw.rounded_rectangle([x0, 74, x1, 232], radius=18, fill=body_c, outline=(42, 52, 68), width=5)
        draw.rectangle([x0 - 8, 56, x1 + 8, 84], fill=roof_c, outline=(42, 52, 68), width=4)
        # Train windows
        draw.rectangle([x0 + 26, 102, x0 + 96, 168], fill=(246, 250, 255), outline=(42, 52, 68), width=4)
        draw.rectangle([x0 + 116, 102, x1 - 24, 168], fill=(246, 250, 255), outline=(42, 52, 68), width=4)
        # Wheels
        for wx in (x0 + 52, x1 - 52):
            draw.ellipse([wx - 28, 212, wx + 28, 268], fill=(64, 54, 48), outline=(238, 152, 48), width=7)
            draw.ellipse([wx - 10, 230, wx + 10, 250], fill=(245, 245, 245))
    im.save(os.path.join(TEX_DIR, "tex_train_mural.png"))

    # 6. Royal palm ringed trunk bark + Normal Map (D-06!)
    w, h = 256, 512
    im = Image.new("RGB", (w, h), (156, 150, 142))
    hmap = Image.new("L", (w, h), 170)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    rng6 = random.Random(506)
    for y in range(0, h, 24):
        d = rng6.randint(-8, 8)
        draw.rectangle([0, y, w, y + 20], fill=(158 + d, 152 + d, 144 + d))
        draw.line([(0, y + 21), (w, y + 21)], fill=(108, 102, 96), width=3)
        hdraw.line([(0, y + 21), (w, y + 21)], fill=65, width=3)
    im.save(os.path.join(TEX_DIR, "tex_palm_bark.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.2).save(
        os.path.join(TEX_DIR, "tex_palm_bark_nrm.png")
    )


def gen_v6_front_streetview_textures() -> None:
    """v6 正面街景精修專屬貼圖：和平樓直書「重慶國小」大招牌、灰白棋盤格人行道、紅褐斜格導盲磚轉角與「廣和街」路牌。"""
    # 1. Heping Bldg West Gable Vertical Sign (10 廣和街: 深咖啡直紋木格＋金色直書「重慶國小」)
    w, h = 256, 768
    im = Image.new("RGB", (w, h), (58, 42, 32))
    draw = ImageDraw.Draw(im)
    # Fine vertical wood/metal slats
    for x in range(0, w, 10):
        col = (68, 50, 38) if (x // 10) % 2 == 0 else (46, 33, 24)
        draw.rectangle([x, 0, x + 7, h], fill=col)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(98, 76, 58), width=4)
    f = _get_font(118, bold=True)
    chars = ["重", "慶", "國", "小"]
    for idx, ch in enumerate(chars):
        y = 72 + idx * 162
        draw.text((70, y + 4), ch, fill=(24, 16, 10), font=f)
        draw.text((66, y), ch, fill=(214, 178, 86), font=f)
    im.save(os.path.join(TEX_DIR, "tex_heping_vert_sign.png"))

    # 2. Guanghe St Checkerboard Sidewalk Tile + Normal Map (27 廣和街寫實霧面灰白棋盤格方磚!)
    size = 512
    im = Image.new("RGB", (size, size), (126, 126, 124))
    hmap = Image.new("L", (size, size), 85)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    rng = random.Random(602)
    cells = 8
    cw = size // cells
    for r in range(cells):
        for c in range(cells):
            is_light = (r + c) % 2 == 0
            # Match realistic weathered Taipei sidewalk tone (soft light warm-gray vs medium slate-gray)
            base = (192, 190, 184) if is_light else (118, 120, 122)
            d = rng.randint(-7, 7)
            col = tuple(max(0, min(255, ch + d)) for ch in base)
            x0, y0 = c * cw + 2, r * cw + 2
            x1, y1 = (c + 1) * cw - 2, (r + 1) * cw - 2
            draw.rectangle([x0, y0, x1, y1], fill=col)
            hdraw.rectangle([x0, y0, x1, y1], fill=215)
    # Subtle stone speckle & weathering
    for _ in range(9000):
        px, py = rng.randint(0, size - 1), rng.randint(0, size - 1)
        cur = im.getpixel((px, py))
        d = rng.randint(-10, 10)
        im.putpixel((px, py), tuple(max(0, min(255, ch + d)) for ch in cur))
    im.save(os.path.join(TEX_DIR, "tex_sidewalk_checker.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.2).save(
        os.path.join(TEX_DIR, "tex_sidewalk_checker_nrm.png")
    )

    # 3. NW Corner Plaza Diagonal Red-Brown Anti-slip Brick Tile + Normal Map (10 廣和街轉角暖紅褐斜格地磚!)
    size = 512
    im = Image.new("RGB", (size, size), (150, 100, 74))
    hmap = Image.new("L", (size, size), 205)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    rng3 = random.Random(603)
    for _ in range(10000):
        px, py = rng3.randint(0, size - 1), rng3.randint(0, size - 1)
        d = rng3.randint(-12, 12)
        im.putpixel((px, py), (max(0, min(255, 150 + d)), max(0, min(255, 100 + d)), max(0, min(255, 74 + d))))
    step = 28
    for k in range(-size, size * 2, step):
        draw.line([(k, 0), (k + size, size)], fill=(116, 76, 56), width=3)
        draw.line([(k + size, 0), (k, size)], fill=(116, 76, 56), width=3)
        hdraw.line([(k, 0), (k + size, size)], fill=85, width=3)
        hdraw.line([(k + size, 0), (k, size)], fill=85, width=3)
    im.save(os.path.join(TEX_DIR, "tex_sidewalk_diag_brick.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.7)), strength=2.2).save(
        os.path.join(TEX_DIR, "tex_sidewalk_diag_brick_nrm.png")
    )

    # 4. Street Sign "廣和街 Guanghe St." (10 廣和街綠底白字直牌!)
    w, h = 160, 420
    im = Image.new("RGB", (w, h), (18, 118, 72))
    draw = ImageDraw.Draw(im)
    draw.rectangle([6, 6, w - 7, h - 7], outline=(245, 248, 245), width=5)
    # Up arrow
    draw.polygon([(w // 2, 22), (w // 2 - 26, 66), (w // 2 + 26, 66)], fill=(255, 255, 255))
    f_zh = _get_font(62, bold=True)
    for i, ch in enumerate(["廣", "和", "街"]):
        draw.text((48, 84 + i * 74), ch, fill=(255, 255, 255), font=f_zh)
    f_en = _get_font(22, bold=True)
    draw.text((22, 326), "Guanghe", fill=(255, 255, 255), font=f_en)
    draw.text((58, 356), "St.", fill=(255, 255, 255), font=f_en)
    im.save(os.path.join(TEX_DIR, "tex_roadsign_guanghe.png"))


def _draw_smart_parking_rgba(filename: str, bay_top: str, bay_bot: str) -> None:
    """純 RGBA 透明底熱拌白／黃漆智慧化停車格貼圖（100% 貼合柏油路面，絕無黑色貼紙邊框感！）。"""
    # Horizontal canvas: x=0..2048 (North -> South), y=0..512 (East curb -> West road center)
    hw, hh = 2048, 512
    t_im = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
    td = ImageDraw.Draw(t_im)

    white = (242, 244, 246, 242)
    yellow = (242, 198, 44, 248)

    # Stall outer white line (along y=365, leaving y=380..512 OUTSIDE box for yellow drop-off text!)
    # Curb edge is near y=24; stall spans y=24..365 (width ~2.1m), outer yellow zone y=375..495 (~0.75m)
    y_curb = 22
    y_line = 358
    td.line([(16, y_line), (hw - 16, y_line)], fill=white, width=16)
    # North end, mid divider, South end white transverse bars
    for vx in (20, hw // 2, hw - 20):
        td.line([(vx, y_curb), (vx, y_line + 8)], fill=white, width=16)

    f_big = _get_font(64, bold=True)
    f_num = _get_font(68, bold=True)
    f_time = _get_font(38, bold=True)
    f_yel = _get_font(56, bold=True)

    for bx_off, num in [(36, bay_top), (hw // 2 + 32, bay_bot)]:
        # Inner near-curb white text: "智 慧 化 停 車 格"
        td.text((bx_off + 190, 96), "智  慧  化  停  車  格", fill=white, font=f_big)
        # Inner near-road white text: bay number + time windows
        td.text((bx_off + 20, 260), num, fill=white, font=f_num)
        td.text((bx_off + 132, 276), "07:00-08:00  11:30-12:30  15:20-16:30", fill=white, font=f_time)
        # Outside-box yellow text (matching final_step_137.png exact placement!)
        td.text((bx_off + 96, 392), "接  送  時  段   限  停  15  分  鐘", fill=yellow, font=f_yel)

    # Rotate -90 deg (clockwise):
    #   orig left (bay_top, North) -> TOP (UV v=1, +Y North)
    #   orig right (bay_bot, South) -> BOTTOM (UV v=0, -Y South)
    #   orig top (curb side) -> RIGHT (UV u=1, +X East curb)
    #   orig bottom (yellow outside text) -> LEFT (UV u=0, -X West road)
    out = t_im.rotate(-90, expand=True)
    out.save(os.path.join(TEX_DIR, filename))


def gen_v7_front_ground_and_signs() -> None:
    """v7/v8 廣和街正面路面標線（全 RGBA 透明熱拌漆）、告示牌、大門招生紅布條與廣和街31號門牌。"""
    # 1. Smart Parent Drop-off Parking Bays (North 16/15 & South 14/13, PURE TRANSPARENT RGBA!)
    _draw_smart_parking_rgba("tex_smart_parking.png", "16", "15")
    _draw_smart_parking_rgba("tex_smart_parking_south.png", "14", "13")

    # 2. Motorcycle + Bicycle Waiting Box at NW Heping Intersection (PURE TRANSPARENT RGBA!)
    size = 512
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    wcol = (242, 244, 246, 244)
    draw.rectangle([14, 14, size - 14, size - 14], outline=wcol, width=18)
    # Left (West): Taiwan standard crisp hollow-line Motorcycle / Scooter symbol facing North (up, matching final_step_137!)
    cx_m = 148
    # Front tire + fender
    draw.rounded_rectangle([cx_m - 12, 82, cx_m + 12, 162], radius=8, fill=wcol)
    # Handlebars + mirrors
    draw.line([(cx_m - 64, 152), (cx_m + 64, 152)], fill=wcol, width=12)
    draw.line([(cx_m - 58, 152), (cx_m - 74, 134)], fill=wcol, width=8)
    draw.line([(cx_m + 58, 152), (cx_m + 74, 134)], fill=wcol, width=8)
    # Front fairing cowl & rider shoulders/helmet (clean hollow stencil look)
    draw.rounded_rectangle([cx_m - 36, 162, cx_m + 36, 224], radius=16, outline=wcol, width=11)
    draw.ellipse([cx_m - 22, 198, cx_m + 22, 244], fill=wcol)  # Rider helmet
    # Scooter seat & rear body shell
    draw.rounded_rectangle([cx_m - 34, 246, cx_m + 34, 344], radius=18, outline=wcol, width=12)
    # Rear tire
    draw.rounded_rectangle([cx_m - 14, 344, cx_m + 14, 412], radius=8, fill=wcol)
    # Right (East): White Bicycle icon facing North (up)
    cx_b = 360
    draw.ellipse([cx_b - 42, 290, cx_b + 42, 374], outline=wcol, width=12)  # Rear wheel
    draw.ellipse([cx_b - 42, 128, cx_b + 42, 212], outline=wcol, width=12)  # Front wheel
    draw.line([(cx_b, 170), (cx_b, 332)], fill=wcol, width=12)  # Spine frame
    draw.line([(cx_b - 48, 178), (cx_b + 48, 178)], fill=wcol, width=12)  # Handlebar
    draw.line([(cx_b - 34, 258), (cx_b + 34, 258)], fill=wcol, width=10)  # Pedals
    im.save(os.path.join(TEX_DIR, "tex_moto_wait_box.png"))

    # 3. Parent Drop-off Zone Signboard (10 / 27 / 50 廣和街藍白黃「家長接送區」告示牌 + 亮橘黃副牌!)
    w, h = 256, 448
    im = Image.new("RGB", (w, h), (244, 246, 250))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, 64], fill=(24, 92, 168))
    draw.rectangle([6, 6, w - 7, 344], outline=(24, 92, 168), width=6)
    draw.text((28, 14), "家長接送區", fill=(255, 255, 255), font=_get_font(38, bold=True))
    # No-parking red/blue circle icon
    draw.ellipse([78, 82, 178, 182], fill=(24, 88, 168), outline=(216, 34, 34), width=14)
    draw.line([(96, 100), (160, 164)], fill=(216, 34, 34), width=12)
    draw.text((28, 198), "接送時段 限停15分", fill=(28, 36, 48), font=_get_font(22, bold=True))
    draw.text((34, 232), "07:00 - 08:00", fill=(24, 92, 168), font=_get_font(24, bold=True))
    draw.text((34, 264), "11:30 - 12:30", fill=(24, 92, 168), font=_get_font(24, bold=True))
    draw.text((34, 296), "15:20 - 16:30", fill=(24, 92, 168), font=_get_font(24, bold=True))
    # Bottom separate bright orange-amber warning plaque (matching final_step_137.png!)
    draw.rectangle([0, 356, w, h], fill=(238, 152, 22))
    draw.rectangle([6, 362, w - 7, h - 7], outline=(42, 32, 18), width=4)
    draw.text((26, 378), "智慧化停車收費", fill=(24, 24, 24), font=_get_font(28, bold=True))
    draw.text((40, 412), "新北市政府交通局", fill=(36, 28, 20), font=_get_font(20, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_sign_pickup.png"))

    # 4. Main Gate Enrollment Banner + Fence Red Banner (27 & 50 廣和街招生紅布條!)
    w, h = 768, 160
    im = Image.new("RGB", (w, h), (242, 244, 246))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, 260, h], fill=(204, 28, 36))
    draw.text((22, 26), "重慶國小", fill=(255, 255, 255), font=_get_font(34, bold=True))
    draw.text((16, 86), "附設幼兒園", fill=(255, 232, 128), font=_get_font(34, bold=True))
    draw.text((280, 34), "招生囉！", fill=(208, 28, 34), font=_get_font(62, bold=True))
    draw.rectangle([545, 16, w - 16, h - 16], fill=(42, 118, 178))
    draw.text((565, 52), "活力重慶 歡迎您", fill=(255, 255, 255), font=_get_font(24, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_gate_banner.png"))

    im_red = Image.new("RGB", (512, 128), (196, 36, 38))
    dr = ImageDraw.Draw(im_red)
    dr.rectangle([6, 6, 505, 121], outline=(248, 224, 148), width=4)
    dr.text((34, 34), "重慶國小附設幼兒園熱烈招生中", fill=(255, 248, 230), font=_get_font(30, bold=True))
    im_red.save(os.path.join(TEX_DIR, "tex_fence_red_banner.png"))

    # 5. Green Address Plaque "廣和街 31 號" (27 廣和街左側警衛室門牌!)
    w, h = 256, 160
    im = Image.new("RGB", (w, h), (16, 114, 68))
    draw = ImageDraw.Draw(im)
    draw.rectangle([6, 6, w - 7, h - 7], outline=(245, 248, 245), width=6)
    draw.text((48, 18), "板橋區廣和街", fill=(255, 255, 255), font=_get_font(26, bold=True))
    draw.text((64, 64), "31 號", fill=(255, 255, 255), font=_get_font(56, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_house_num_31.png"))


def gen_v8_street_realism_textures() -> None:
    """v8 正面街景實景精修：顆粒柏油、花崗岩車阻石凳、深灰路緣石、智慧停車收費柱光學面板、鑄鐵人孔蓋、排水格柵與路口標誌。"""
    # 1. Realistic Asphalt + Normal Map (深炭灰微粗糙瀝青路面，含細骨材與微弱老化肌理)
    size = 512
    im = Image.new("RGB", (size, size), (64, 67, 72))
    hmap = Image.new("L", (size, size), 128)
    px = im.load()
    hp = hmap.load()
    rng = random.Random(801)
    for y in range(size):
        for x in range(size):
            grain = rng.randint(-14, 14)
            patch = int(math.sin(x * 0.035) * math.cos(y * 0.035) * 5.0)
            v = grain + patch
            px[x, y] = (
                max(28, min(115, 64 + v)),
                max(30, min(118, 67 + v)),
                max(33, min(122, 71 + v)),
            )
            hp[x, y] = max(0, min(255, 128 + grain * 4))
    im.save(os.path.join(TEX_DIR, "tex_asphalt.png"))
    _height_to_normal(hmap, strength=1.5).save(os.path.join(TEX_DIR, "tex_asphalt_nrm.png"))

    # 2. Warm Dark-Gray Granite / Terrazzo (給實景圓柱車阻與花崗岩石凳！不再用白磁磚！)
    size = 256
    im = Image.new("RGB", (size, size), (126, 122, 115))
    hmap = Image.new("L", (size, size), 128)
    px = im.load()
    hp = hmap.load()
    rng2 = random.Random(802)
    for y in range(size):
        for x in range(size):
            r = rng2.random()
            if r < 0.14:
                d = rng2.randint(-46, -24)
            elif r < 0.24:
                d = rng2.randint(18, 36)
            else:
                d = rng2.randint(-12, 12)
            px[x, y] = (
                max(40, min(220, 126 + d)),
                max(38, min(215, 122 + d)),
                max(36, min(208, 115 + d)),
            )
            hp[x, y] = max(0, min(255, 128 + d * 2))
    im.save(os.path.join(TEX_DIR, "tex_granite_gray.png"))
    _height_to_normal(hmap, strength=1.4).save(os.path.join(TEX_DIR, "tex_granite_gray_nrm.png"))

    # 3. Weathered Concrete Curb with vertical expansion joints (深暖灰水泥路緣石)
    w, h = 512, 128
    im = Image.new("RGB", (w, h), (148, 146, 140))
    hmap = Image.new("L", (w, h), 180)
    draw = ImageDraw.Draw(im)
    hdraw = ImageDraw.Draw(hmap)
    rng3 = random.Random(803)
    for _ in range(7000):
        x, y = rng3.randint(0, w - 1), rng3.randint(0, h - 1)
        d = rng3.randint(-15, 15)
        im.putpixel((x, y), (max(60, min(220, 148 + d)), max(58, min(218, 146 + d)), max(55, min(214, 140 + d))))
    for jx in (0, 256):
        draw.rectangle([jx, 0, jx + 6, h], fill=(92, 90, 86))
        hdraw.rectangle([jx, 0, jx + 6, h], fill=70)
    im.save(os.path.join(TEX_DIR, "tex_curb_concrete.png"))
    _height_to_normal(hmap.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.0).save(
        os.path.join(TEX_DIR, "tex_curb_concrete_nrm.png")
    )

    # 4. South Segment Plain Gray Concrete Sidewalk Tiles (60/78/88 廣和街素面淺灰方磚人行道)
    gen_tile_wall_pbr("tex_sidewalk_south", (168, 166, 160), (124, 122, 118), cols=8, rows=8, jitter=8, size=512, seed=804)

    # 5. Smart Parking Meter Pillar Front Optical Panel (新北市智慧停車收費柱亮黑正面光學面板!)
    w, h = 192, 768
    im = Image.new("RGB", (w, h), (18, 22, 26))
    draw = ImageDraw.Draw(im)
    # Metallic brushed-silver thin side bezel
    draw.rectangle([0, 0, 14, h], fill=(162, 168, 174))
    draw.rectangle([w - 15, 0, w - 1, h], fill=(162, 168, 174))
    draw.rectangle([0, 0, w - 1, 14], fill=(154, 160, 166))
    # Top status green LED bar
    draw.rounded_rectangle([36, 26, w - 36, 44], radius=6, fill=(42, 226, 124))
    # Upper dual ANPR camera lens housing (dark glossy glass + concentric lens rings)
    draw.rounded_rectangle([28, 66, w - 28, 210], radius=14, fill=(10, 12, 16), outline=(56, 62, 70), width=3)
    draw.ellipse([64, 84, 128, 148], fill=(24, 34, 48), outline=(92, 108, 124), width=4)
    draw.ellipse([80, 100, 112, 132], fill=(8, 16, 28), outline=(48, 92, 136), width=2)
    draw.ellipse([78, 162, 114, 198], fill=(28, 28, 34), outline=(72, 76, 82), width=3)
    # Mid OLED mini status screen (New Taipei Smart Parking info)
    draw.rounded_rectangle([32, 240, w - 32, 360], radius=10, fill=(16, 44, 72), outline=(88, 136, 178), width=3)
    draw.text((42, 256), "智慧停車", fill=(238, 246, 255), font=_get_font(26, bold=True))
    draw.text((44, 294), "偵測計費中", fill=(116, 234, 162), font=_get_font(20, bold=True))
    draw.text((52, 326), "NTPC", fill=(168, 206, 240), font=_get_font(20, bold=True))
    # Lower QR / contactless payment icon & reflective strip
    draw.rounded_rectangle([46, 410, w - 46, 510], radius=8, fill=(234, 238, 242))
    draw.rectangle([62, 426, 130, 494], fill=(28, 32, 38))
    draw.rectangle([74, 438, 118, 482], fill=(234, 238, 242))
    draw.rectangle([86, 450, 106, 470], fill=(28, 32, 38))
    draw.rectangle([28, 560, w - 28, 578], fill=(234, 196, 42))  # Safety yellow band
    im.save(os.path.join(TEX_DIR, "tex_pillar_front.png"))

    # 6. Cast-Iron Round Manhole Cover RGBA (圓形鑄鐵人孔蓋，對照 step_135 & final_step_137!)
    size = 256
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse([8, 8, size - 8, size - 8], fill=(74, 70, 68, 255), outline=(44, 42, 40, 255), width=8)
    draw.ellipse([26, 26, size - 26, size - 26], outline=(98, 94, 90, 255), width=4)
    for k in range(36, size - 36, 22):
        draw.line([(k, 36), (k, size - 36)], fill=(54, 52, 50, 255), width=3)
        draw.line([(36, k), (size - 36, k)], fill=(54, 52, 50, 255), width=3)
    draw.ellipse([96, 96, size - 96, size - 96], fill=(66, 62, 60, 255), outline=(104, 100, 96, 255), width=4)
    im.save(os.path.join(TEX_DIR, "tex_manhole.png"))

    # 7. Galvanized Curb Storm Drain Grate (路緣金屬排水溝格柵，對照 step_111 & final_step_137!)
    w, h = 256, 128
    im = Image.new("RGB", (w, h), (30, 32, 34))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w - 1, h - 1], outline=(138, 142, 146), width=10)
    for x in range(18, w - 14, 16):
        draw.rectangle([x, 8, x + 7, h - 9], fill=(124, 128, 132))
    draw.rectangle([8, h // 2 - 4, w - 9, h // 2 + 4], fill=(134, 138, 142))
    im.save(os.path.join(TEX_DIR, "tex_drain_grate.png"))

    # 8. Yellow-Black Hazard Pole Stripe (家長接送區告示牌黃黑斜紋桿!)
    w, h = 128, 256
    im = Image.new("RGB", (w, h), (236, 186, 26))
    draw = ImageDraw.Draw(im)
    for k in range(-h, w + h, 44):
        draw.polygon([(k, 0), (k + 22, 0), (k + 22 - h // 2, h), (k - h // 2, h)], fill=(28, 28, 30))
    im.save(os.path.join(TEX_DIR, "tex_pole_hazard.png"))

    # 9. Horizontal Green Street Sign "和平路 Heping Rd." + Yellow Triangle "當心兒童"
    w, h = 384, 144
    im = Image.new("RGB", (w, h), (18, 118, 72))
    draw = ImageDraw.Draw(im)
    draw.rectangle([6, 6, w - 7, h - 7], outline=(245, 248, 245), width=5)
    draw.text((48, 14), "和 平 路", fill=(255, 255, 255), font=_get_font(62, bold=True))
    draw.text((92, 92), "Heping Rd.", fill=(255, 255, 255), font=_get_font(30, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_roadsign_heping.png"))

    size = 256
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    tri = [(size // 2, 16), (size - 16, size - 20), (16, size - 20)]
    draw.polygon(tri, fill=(242, 194, 24, 255), outline=(204, 28, 28, 255))
    draw.line(tri + [tri[0]], fill=(204, 28, 28, 255), width=16)
    # Stylized silhouettes of two running children
    draw.ellipse([96, 112, 122, 138], fill=(24, 24, 28, 255))
    draw.rectangle([96, 140, 122, 186], fill=(24, 24, 28, 255))
    draw.line([(100, 184), (86, 218)], fill=(24, 24, 28, 255), width=10)
    draw.line([(118, 184), (128, 218)], fill=(24, 24, 28, 255), width=10)
    draw.ellipse([142, 126, 164, 148], fill=(24, 24, 28, 255))
    draw.rectangle([142, 150, 164, 190], fill=(24, 24, 28, 255))
    draw.line([(146, 188), (136, 218)], fill=(24, 24, 28, 255), width=9)
    draw.line([(160, 188), (172, 218)], fill=(24, 24, 28, 255), width=9)
    im.save(os.path.join(TEX_DIR, "tex_sign_children.png"))


def gen_v9_south_streetview_textures() -> None:
    """v9 南側街景精修專屬貼圖（92/43/76/3/12 廣和街）：鐵捲門、藍框無障礙車格、雙片矩形手孔蓋、五權街30巷路牌與高牆貼圖。"""
    # 1. SW Corner Brown Roll-up Metal Gate with yellow stencil "車輛出入 請勿停車" (92 廣和街 step_145!)
    w, h = 512, 384
    im = Image.new("RGB", (w, h), (96, 68, 56))
    draw = ImageDraw.Draw(im)
    rng = random.Random(901)
    for y in range(0, h, 10):
        d = rng.randint(-8, 8)
        draw.rectangle([0, y, w, y + 6], fill=(102 + d, 72 + d, 58 + d))
        draw.line([(0, y + 8), (w, y + 8)], fill=(54, 38, 30), width=2)
    # Subtle weathered patina
    for _ in range(4500):
        px, py = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(-12, 12)
        c = im.getpixel((px, py))
        im.putpixel((px, py), tuple(max(0, min(255, ch + d)) for ch in c))
    # Yellow vertical Chinese stencil text matching step_145
    f_v = _get_font(44, bold=True)
    for i, ch in enumerate(["車", "輛", "出", "入"]):
        draw.text((346, 56 + i * 64), ch, fill=(214, 178, 58), font=f_v)
    for i, ch in enumerate(["請", "勿", "停", "車"]):
        draw.text((134, 62 + i * 64), ch, fill=(208, 172, 54), font=f_v)
    im.save(os.path.join(TEX_DIR, "tex_south_shutter.png"))

    # 2. Pure Transparent RGBA Blue-Border Accessible Parking Bay (43 廣和街 step_149!)
    w, h = 1024, 512
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    blue = (42, 132, 214, 242)
    white = (242, 245, 248, 245)
    # Blue thick box outline
    draw.rectangle([18, 18, w - 18, h - 18], outline=blue, width=28)
    # Blue center square with white wheelchair symbol
    cx, cy = w // 2, h // 2
    draw.rounded_rectangle([cx - 115, cy - 115, cx + 115, cy + 115], radius=16, fill=blue, outline=white, width=8)
    # Wheelchair head, back, seat, leg & wheel
    draw.ellipse([cx - 18, cy - 84, cx + 22, cy - 44], fill=white)
    draw.line([(cx + 2, cy - 42), (cx + 2, cy + 12), (cx + 52, cy + 12), (cx + 68, cy + 68)], fill=white, width=16)
    draw.line([(cx + 2, cy - 16), (cx + 46, cy - 16)], fill=white, width=13)
    draw.arc([cx - 66, cy - 8, cx + 34, cy + 92], 35, 315, fill=white, width=16)
    im.save(os.path.join(TEX_DIR, "tex_disabled_parking.png"))

    # 3. Large Double-Leaf Rectangular Cast-Iron Telecom Handhole Cover (12 廣和街 final_step_157!)
    w, h = 512, 256
    im = Image.new("RGB", (w, h), (86, 80, 76))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w - 1, h - 1], outline=(146, 144, 140), width=14)
    draw.line([(w // 2, 10), (w // 2, h - 10)], fill=(42, 38, 36), width=8)
    for half_x in (14, w // 2 + 6):
        hw = w // 2 - 20
        draw.rectangle([half_x, 14, half_x + hw, h - 14], fill=(78, 72, 68), outline=(52, 48, 46), width=4)
        for k in range(half_x + 12, half_x + hw - 6, 18):
            draw.line([(k, 18), (k, h - 18)], fill=(62, 58, 54), width=3)
        for k in range(24, h - 18, 18):
            draw.line([(half_x + 8, k), (half_x + hw - 8, k)], fill=(62, 58, 54), width=3)
        # Weathered white painted stencil markings
        draw.rectangle([half_x + hw // 2 - 22, 46, half_x + hw // 2 + 22, h - 46], fill=(178, 174, 168))
    im.save(os.path.join(TEX_DIR, "tex_rect_manhole.png"))

    # 4. Green Street Sign "五權街30巷24弄" (3 廣和街 B 後門旁 step_155!)
    w, h = 384, 144
    im = Image.new("RGB", (w, h), (18, 118, 72))
    draw = ImageDraw.Draw(im)
    draw.rectangle([6, 6, w - 7, h - 7], outline=(245, 248, 245), width=5)
    draw.text((28, 16), "五權街30巷", fill=(255, 255, 255), font=_get_font(46, bold=True))
    draw.text((92, 78), "24 弄  →", fill=(255, 255, 255), font=_get_font(40, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_sign_wuquan30.png"))

    # 5. Back-Gate Green Campus Notice Plaque & Blue Pillar Nameplate (3 廣和街 B step_155!)
    w, h = 320, 224
    im = Image.new("RGB", (w, h), (22, 126, 72))
    draw = ImageDraw.Draw(im)
    draw.rectangle([6, 6, w - 7, h - 7], outline=(242, 248, 242), width=6)
    draw.text((34, 24), "校園開放時間", fill=(255, 242, 148), font=_get_font(38, bold=True))
    draw.text((28, 86), "平日 05:30-07:00", fill=(255, 255, 255), font=_get_font(26, bold=True))
    draw.text((28, 124), "     18:00-21:00", fill=(255, 255, 255), font=_get_font(26, bold=True))
    draw.text((28, 166), "假日 05:30-21:00", fill=(255, 255, 255), font=_get_font(26, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_sign_campus_rules.png"))

    w, h = 420, 112
    im = Image.new("RGB", (w, h), (34, 72, 134))
    draw = ImageDraw.Draw(im)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(235, 240, 248), width=4)
    draw.line([(w // 2, 6), (w // 2, h - 6)], fill=(235, 240, 248), width=3)
    draw.text((16, 14), "重慶國小", fill=(255, 255, 255), font=_get_font(32, bold=True))
    draw.text((34, 58), "3 號 門", fill=(255, 236, 136), font=_get_font(34, bold=True))
    draw.text((w // 2 + 16, 18), "學童接送區", fill=(255, 255, 255), font=_get_font(34, bold=True))
    draw.text((w // 2 + 14, 68), "Student Pick-Up", fill=(220, 234, 250), font=_get_font(20, bold=True))
    im.save(os.path.join(TEX_DIR, "tex_sign_backgate_blue.png"))

    # Dual directional green street sign "◀ 廣和街 | 五權街 ▶" right beside Gate 3 (crisp drawn vector arrows, NO missing glyph box!)
    w_gw, h_gw = 512, 128
    im_gw = Image.new("RGB", (w_gw, h_gw), (18, 118, 72))
    d_gw = ImageDraw.Draw(im_gw)
    d_gw.rectangle([5, 5, w_gw // 2 - 14, h_gw - 6], outline=(245, 248, 245), width=5)
    d_gw.rectangle([w_gw // 2 + 14, 5, w_gw - 6, h_gw - 6], outline=(245, 248, 245), width=5)
    d_gw.rectangle([w_gw // 2 - 10, 0, w_gw // 2 + 10, h_gw - 1], fill=(112, 108, 102))
    d_gw.polygon([(22, 64), (56, 40), (56, 88)], fill=(255, 255, 255))
    d_gw.text((66, 30), "廣和街", fill=(255, 255, 255), font=_get_font(48, bold=True))
    d_gw.text((w_gw // 2 + 30, 30), "五權街", fill=(255, 255, 255), font=_get_font(48, bold=True))
    d_gw.polygon([(w_gw - 22, 64), (w_gw - 56, 40), (w_gw - 56, 88)], fill=(255, 255, 255))
    im_gw.save(os.path.join(TEX_DIR, "tex_sign_guanghe_wuquan.png"))

    # 6. YouBike 2.0 Station Pillar Side Graphic (white upper + yellow stripe + orange triangle base!)
    w, h = 128, 512
    im = Image.new("RGB", (w, h), (236, 236, 232))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, 72], fill=(238, 186, 28))
    draw.rectangle([0, h - 135, w, h], fill=(232, 118, 32))
    draw.polygon([(0, h - 135), (w, h - 135), (w, h - 195)], fill=(232, 118, 32))
    draw.text((16, 16), "2.0", fill=(36, 32, 28), font=_get_font(38, bold=True))
    draw.rectangle([28, 110, w - 28, 220], fill=(34, 42, 54))
    im.save(os.path.join(TEX_DIR, "tex_youbike_pillar.png"))


def gen_v10_east_wuquan_textures() -> None:
    """v10 東側五權街實景貼圖（2/9/1/中北段/15 五權街）：朝東閱讀智慧化停車格 05-01、身障專用機車格、10-07 汽車格、公車停靠區、路牌與校園公告欄。"""
    # 1. East Wuquan St Smart Parking Bays 05 -> 01 (PURE RGBA! Left=South 05 -> Right=North 01, Top=West curb, Bot=East road)
    hw, hh = 2560, 512
    t_im = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
    td = ImageDraw.Draw(t_im)
    white = (242, 244, 246, 244)
    yellow = (242, 198, 44, 248)
    y_curb = 20
    y_line = 356
    td.line([(16, y_line), (hw - 16, y_line)], fill=white, width=16)
    n_bays = 5
    bay_w = (hw - 32) / n_bays
    for i in range(n_bays + 1):
        vx = int(16 + i * bay_w)
        td.line([(vx, y_curb), (vx, y_line + 8)], fill=white, width=16)
    f_big = _get_font(54, bold=True)
    f_num = _get_font(62, bold=True)
    f_time = _get_font(30, bold=True)
    f_yel = _get_font(44, bold=True)
    nums = ["05", "04", "03", "02", "01"]
    for i, num in enumerate(nums):
        bx = int(16 + i * bay_w)
        td.text((bx + 68, 92), "智慧化停車格", fill=white, font=f_big)
        td.text((bx + 18, 266), num, fill=white, font=f_num)
        td.text((bx + 102, 282), "07:00-08:00 11:30-12:30 15:30-16:30", fill=yellow, font=f_time)
        td.text((bx + 26, 396), "接送時段 限停10分鐘 接送區", fill=yellow, font=f_yel)
    # Rotate +90 deg CCW -> left(South 05) to bottom(-Y), right(North 01) to top(+Y), top(curb) to left(-X)!
    t_im.rotate(90, expand=True).save(os.path.join(TEX_DIR, "tex_smart_parking_east.png"))

    # 2. East Wuquan St Disabled Moto Bay "身障專用" (9 五權街 step_165, PURE RGBA!)
    hw2, hh2 = 640, 512
    im2 = Image.new("RGBA", (hw2, hh2), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(im2)
    blue = (42, 132, 214, 245)
    d2.rectangle([28, 28, hw2 - 28, 355], fill=blue, outline=white, width=18)
    # White wheelchair symbol inside blue stall
    cx, cy = hw2 // 2, 192
    d2.ellipse([cx - 18, cy - 82, cx + 22, cy - 42], fill=white)
    d2.line([(cx + 2, cy - 40), (cx + 2, cy + 12), (cx + 50, cy + 12), (cx + 66, cy + 64)], fill=white, width=16)
    d2.line([(cx + 2, cy - 14), (cx + 44, cy - 14)], fill=white, width=13)
    d2.arc([cx - 64, cy - 6, cx + 32, cy + 90], 35, 315, fill=white, width=16)
    # Crisp white "身 障 專 用" painted outside blue stall on road side!
    d2.text((104, 386), "身 障 專 用", fill=white, font=_get_font(76, bold=True))
    im2.rotate(90, expand=True).save(os.path.join(TEX_DIR, "tex_disabled_moto_east.png"))

    # 3. East Wuquan St Regular Car Parking Bays 10 | 09 | 08 | 07 (2 五權街中段 A step_176, PURE RGBA!)
    hw3, hh3 = 2048, 384
    im3 = Image.new("RGBA", (hw3, hh3), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(im3)
    d3.line([(16, hh3 - 26), (hw3 - 16, hh3 - 26)], fill=white, width=16)
    bw3 = (hw3 - 32) / 4.0
    for i in range(5):
        vx = int(16 + i * bw3)
        d3.line([(vx, 18), (vx, hh3 - 20)], fill=white, width=16)
    f_cnum = _get_font(68, bold=True)
    for i, cnum in enumerate(["10", "09", "08", "07"]):
        bx = int(16 + i * bw3)
        d3.text((bx + 24, hh3 - 118), cnum, fill=white, font=f_cnum)
    im3.rotate(90, expand=True).save(os.path.join(TEX_DIR, "tex_car_bays_east.png"))

    # 4. Heping Rd NE Bus Stop Box "公車停靠區" — vertical along driving lane matching 166 和平路 step_2! (PURE RGBA!)
    w4, h4 = 320, 1024
    im4 = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(im4)
    d4.rectangle([16, 16, w4 - 16, h4 - 16], outline=white, width=16)
    f_bus = _get_font(128, bold=True)
    for idx, ch in enumerate(["公", "車", "停", "靠", "區"]):
        d4.text((96, 62 + idx * 184), ch, fill=white, font=f_bus)
    im4.save(os.path.join(TEX_DIR, "tex_bus_stop_box.png"))

    # 5. Green Street Signs: "和平路174巷1弄 ← / 壽德街 →" (1 五權街), Vertical "▲ 和平路" & Horizontal "五權街" (15 五權街 NE!)
    w5, h5 = 384, 224
    im5 = Image.new("RGB", (w5, h5), (18, 118, 72))
    d5 = ImageDraw.Draw(im5)
    d5.rectangle([6, 6, w5 - 7, h5 - 7], outline=(245, 248, 245), width=5)
    d5.line([(12, h5 // 2), (w5 - 12, h5 // 2)], fill=(245, 248, 245), width=4)
    d5.text((22, 24), "← 和平路174巷1弄", fill=(255, 255, 255), font=_get_font(38, bold=True))
    d5.text((76, 134), "壽 德 街  →", fill=(255, 255, 255), font=_get_font(44, bold=True))
    im5.save(os.path.join(TEX_DIR, "tex_sign_wuquan_alley.png"))

    w6, h6 = 160, 420
    im6 = Image.new("RGB", (w6, h6), (18, 118, 72))
    d6 = ImageDraw.Draw(im6)
    d6.rectangle([6, 6, w6 - 7, h6 - 7], outline=(245, 248, 245), width=5)
    d6.polygon([(w6 // 2, 22), (w6 // 2 - 26, 66), (w6 // 2 + 26, 66)], fill=(255, 255, 255))
    for i, ch in enumerate(["和", "平", "路"]):
        d6.text((48, 84 + i * 74), ch, fill=(255, 255, 255), font=_get_font(62, bold=True))
    d6.text((28, 326), "Heping", fill=(255, 255, 255), font=_get_font(22, bold=True))
    d6.text((54, 356), "Rd.", fill=(255, 255, 255), font=_get_font(22, bold=True))
    im6.save(os.path.join(TEX_DIR, "tex_sign_heping_vert.png"))

    w7, h7 = 320, 128
    im7 = Image.new("RGB", (w7, h7), (18, 118, 72))
    d7 = ImageDraw.Draw(im7)
    d7.rectangle([6, 6, w7 - 7, h7 - 7], outline=(245, 248, 245), width=5)
    d7.text((38, 14), "五 權 街", fill=(255, 255, 255), font=_get_font(54, bold=True))
    d7.text((76, 82), "Wuquan St.", fill=(255, 255, 255), font=_get_font(24, bold=True))
    im7.save(os.path.join(TEX_DIR, "tex_sign_wuquan_horiz.png"))

    # 6. Glass-Enclosed Campus Bulletin Board on East Wall (1 五權街 step_170!)
    wb, hb = 384, 288
    imb = Image.new("RGB", (wb, hb), (72, 58, 48))
    db = ImageDraw.Draw(imb)
    db.rectangle([16, 16, wb - 17, hb - 17], fill=(208, 198, 182), outline=(44, 36, 30), width=6)
    for px, py, col in [(34, 34, (242, 232, 186)), (152, 34, (226, 240, 248)), (264, 34, (248, 224, 224)), (34, 158, (230, 246, 226)), (180, 158, (246, 238, 210))]:
        db.rectangle([px, py, px + 96, py + 104], fill=col, outline=(140, 134, 126), width=2)
    imb.save(os.path.join(TEX_DIR, "tex_campus_bulletin.png"))

    # 7. Wet-Track Red-Text Warning Notice + Blue "學童接送區" Plaque (2 五權街北 C step_180!)
    wn, hn = 320, 224
    imn = Image.new("RGB", (wn, hn), (242, 240, 234))
    dn = ImageDraw.Draw(imn)
    dn.rectangle([6, 6, wn - 7, hn - 7], outline=(188, 38, 38), width=5)
    dn.text((22, 26), "雨後跑道溼滑", fill=(188, 34, 34), font=_get_font(42, bold=True))
    dn.text((22, 86), "請來校運動人士", fill=(188, 34, 34), font=_get_font(36, bold=True))
    dn.text((48, 134), "多 加 注 意", fill=(188, 34, 34), font=_get_font(38, bold=True))
    dn.text((62, 184), "重慶國小總務處", fill=(54, 48, 44), font=_get_font(22, bold=True))
    imn.save(os.path.join(TEX_DIR, "tex_sign_wet_track.png"))

    wp, hp = 320, 112
    imp = Image.new("RGB", (wp, hp), (36, 78, 146))
    dp = ImageDraw.Draw(imp)
    dp.rectangle([5, 5, wp - 6, hp - 6], outline=(238, 244, 252), width=4)
    dp.text((42, 12), "學童接送區", fill=(255, 255, 255), font=_get_font(44, bold=True))
    dp.text((28, 70), "Student Pick-Up Area", fill=(224, 236, 252), font=_get_font(22, bold=True))
    imp.save(os.path.join(TEX_DIR, "tex_sign_student_pickup.png"))


def gen_v11_north_heping_textures() -> None:
    """v11 北側和平路實景專屬貼圖（166/147/129 和平路）：天橋波紋門框柱、黃漆30速限、公車專用、和平路機慢車格、公車LED看板與天然景觀石塊。"""
    # 1. Skybridge Portal Pillar Blue-White Ocean Wave Mural (129 和平路 A step_8!)
    w, h = 256, 512
    im = Image.new("RGB", (w, h), (186, 206, 222))
    draw = ImageDraw.Draw(im)
    rng = random.Random(1101)
    # Subtle weathered concrete noise base
    for _ in range(5500):
        px, py = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(-12, 12)
        im.putpixel((px, py), (max(0, min(255, 186 + d)), max(0, min(255, 206 + d)), max(0, min(255, 222 + d))))
    # Repeating horizontal undulating dark-blue wave ribbons from bottom to top!
    for y_base in range(18, h, 34):
        pts_top = []
        pts_bot = []
        for x in range(0, w + 8, 8):
            wy = int(y_base + math.sin(x * 0.048 + y_base * 0.08) * 9.0)
            pts_top.append((x, wy))
            pts_bot.append((x, wy + 13))
        col = (66, 108, 148) if (y_base // 34) % 2 == 0 else (48, 86, 126)
        draw.polygon(pts_top + list(reversed(pts_bot)), fill=col)
    im.save(os.path.join(TEX_DIR, "tex_skybridge_pillar_wave.png"))

    # 2. Pure Transparent RGBA Yellow Speed Limit "30" (129 和平路 C/D step_12 & final_step_14!)
    size = 512
    im2 = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(im2)
    f30 = _get_font(270, bold=True)
    # Slightly weathered road yellow
    d2.text((88, 110), "30", fill=(232, 194, 62, 236), font=f30)
    im2.save(os.path.join(TEX_DIR, "tex_speed_30_yellow.png"))

    # 3. Pure Transparent RGBA "公 車 專 用" Box — vertical along westbound lane (166 和平路 step_2!)
    w3, h3 = 320, 1024
    im3 = Image.new("RGBA", (w3, h3), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(im3)
    white = (242, 244, 246, 242)
    d3.rectangle([16, 16, w3 - 16, h3 - 16], outline=white, width=16)
    f_bus2 = _get_font(138, bold=True)
    for idx, ch in enumerate(["公", "車", "專", "用"]):
        d3.text((90, 88 + idx * 218), ch, fill=white, font=f_bus2)
    im3.save(os.path.join(TEX_DIR, "tex_bus_only_box.png"))

    # 4. Pure Transparent RGBA Heping Rd Eastbound Motorcycle Wait Box (front pointing UP = V=1 = driving direction!)
    size4 = 512
    im4 = Image.new("RGBA", (size4, size4), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(im4)
    d4.rectangle([14, 14, size4 - 14, size4 - 14], outline=white, width=18)
    cx = size4 // 2
    d4.rounded_rectangle([cx - 14, 88, cx + 14, 174], radius=8, fill=white)
    d4.line([(cx - 72, 164), (cx + 72, 164)], fill=white, width=14)
    d4.rounded_rectangle([cx - 42, 174, cx + 42, 242], radius=18, outline=white, width=12)
    d4.ellipse([cx - 26, 212, cx + 26, 264], fill=white)
    d4.rounded_rectangle([cx - 38, 266, cx + 38, 364], radius=18, outline=white, width=13)
    d4.rounded_rectangle([cx - 16, 364, cx + 16, 430], radius=8, fill=white)
    im4.save(os.path.join(TEX_DIR, "tex_heping_moto_box.png"))

    # 5. Bus Shelter Electronic LED Route Display Board (166 和平路 step_2!)
    w5, h5 = 384, 128
    im5 = Image.new("RGB", (w5, h5), (26, 30, 36))
    d5 = ImageDraw.Draw(im5)
    d5.rectangle([6, 6, w5 - 7, h5 - 7], outline=(58, 72, 92), width=6)
    d5.text((22, 18), "重慶國小站  245  657", fill=(255, 162, 46), font=_get_font(30, bold=True))
    d5.text((26, 68), "即將進站  約 3 分鐘", fill=(255, 92, 48), font=_get_font(32, bold=True))
    im5.save(os.path.join(TEX_DIR, "tex_bus_led_board.png"))

    # 6. Natural Weathered Mossy Landscape Boulder PBR + Normal Map (129 和平路 A/B/C/D!)
    size6 = 256
    im6 = Image.new("RGB", (size6, size6), (112, 108, 98))
    hmap6 = Image.new("L", (size6, size6), 128)
    px6 = im6.load()
    hp6 = hmap6.load()
    rng6 = random.Random(1106)
    for y in range(size6):
        for x in range(size6):
            wave = int(math.sin(x * 0.08) * math.cos(y * 0.07) * 18)
            grain = rng6.randint(-18, 18)
            moss = 12 if (wave > 6 and rng6.random() < 0.35) else 0
            v = wave + grain
            px6[x, y] = (
                max(36, min(200, 110 + v - moss)),
                max(40, min(205, 108 + v + moss)),
                max(32, min(190, 96 + v - moss)),
            )
            hp6[x, y] = max(0, min(255, 128 + wave * 3 + grain * 2))
    im6.save(os.path.join(TEX_DIR, "tex_rock_landscape.png"))
    _height_to_normal(hmap6.filter(ImageFilter.GaussianBlur(radius=0.8)), strength=2.6).save(
        os.path.join(TEX_DIR, "tex_rock_landscape_nrm.png")
    )

    # 7. v11.3 147 和平路 West Basement 3-Tone Roll-up Shutter (Cream w/ 10x5 Vent Slots + Pale Pink + Charcoal Gray! final_step_64!)
    w7, h7 = 512, 512
    im7 = Image.new("RGB", (w7, h7), (206, 202, 180))
    d7 = ImageDraw.Draw(im7)
    y_pink = int(h7 * 0.56)
    y_dark = int(h7 * 0.74)
    # Horizontal ribbed shutter slats across 3 distinct color bands
    for y in range(0, h7, 10):
        if y < y_pink:
            base = (204, 200, 178)
            line = (168, 164, 144)
        elif y < y_dark:
            base = (196, 168, 166)
            line = (158, 134, 132)
        else:
            base = (76, 78, 80)
            line = (48, 50, 52)
        d7.rectangle([0, y, w7 - 1, y + 7], fill=base)
        d7.line([(0, y + 8), (w7 - 1, y + 8)], fill=line, width=2)
    # Iconic 10 columns x 5 rows rectangular ventilation slots in upper cream section!
    for r in range(5):
        sy = 28 + r * 30
        for c in range(10):
            sx = 64 + c * 39
            d7.rectangle([sx, sy, sx + 24, sy + 9], fill=(28, 30, 32))
    # Metallic silver side guide tracks
    d7.rectangle([0, 0, 18, h7 - 1], fill=(164, 168, 170))
    d7.rectangle([w7 - 19, 0, w7 - 1, h7 - 1], fill=(164, 168, 170))
    im7.save(os.path.join(TEX_DIR, "tex_b1_shutter_tri.png"))

    # 8. v11.3 147 和平路 East Wide Silver-Gray Ribbed Basement Roll-up Shutter (step_27 & step_29!)
    w8, h8 = 512, 512
    im8 = Image.new("RGB", (w8, h8), (156, 158, 154))
    d8 = ImageDraw.Draw(im8)
    rng8 = random.Random(1138)
    for y in range(0, h8, 10):
        jit = rng8.randint(-6, 6)
        d8.rectangle([0, y, w8 - 1, y + 7], fill=(154 + jit, 156 + jit, 150 + jit))
        d8.line([(0, y + 8), (w8 - 1, y + 8)], fill=(96, 98, 94), width=2)
    d8.rectangle([0, 0, 14, h8 - 1], fill=(122, 124, 122))
    d8.rectangle([w8 - 15, 0, w8 - 1, h8 - 1], fill=(122, 124, 122))
    im8.save(os.path.join(TEX_DIR, "tex_b1_shutter_silver.png"))

    # 9. v11.3 Terracotta Diamond Lattice Ventilation Brick Band above 147 Heping shutters & windows (final_step_64!)
    w9, h9 = 512, 128
    im9 = Image.new("RGB", (w9, h9), (42, 26, 22))
    d9 = ImageDraw.Draw(im9)
    step9 = 24
    for k in range(-h9, w9 + h9, step9):
        d9.line([(k, 0), (k + h9, h9)], fill=(142, 72, 58), width=7)
        d9.line([(k + h9, 0), (k, h9)], fill=(142, 72, 58), width=7)
    d9.rectangle([0, 0, w9 - 1, h9 - 1], outline=(146, 78, 64), width=6)
    im9.save(os.path.join(TEX_DIR, "tex_brick_lattice_band.png"))

    # 10. v11.3 Vertical Calligraphy Banner "吉龍舞春" on divider pier between shutters (final_step_64!)
    w10, h10 = 96, 320
    im10 = Image.new("RGB", (w10, h10), (192, 186, 174))
    d10 = ImageDraw.Draw(im10)
    d10.rectangle([4, 4, w10 - 5, h10 - 5], outline=(136, 128, 118), width=3)
    f_cl = _get_font(52, bold=True)
    for idx_c, ch in enumerate(["吉", "龍", "舞", "春"]):
        d10.text((22, 18 + idx_c * 72), ch, fill=(44, 42, 40), font=f_cl)
    im10.save(os.path.join(TEX_DIR, "tex_pillar_chunlian.png"))


def gen_bus_side() -> None:
    """台灣黃色國小校車／幼童專用車側身貼圖。"""
    w, h = 512, 192
    im = Image.new("RGB", (w, h), (244, 192, 26))
    draw = ImageDraw.Draw(im)
    # Dark glass window band
    draw.rectangle([28, 22, w - 28, 92], fill=(32, 46, 62))
    for x in range(88, w - 40, 66):
        draw.rectangle([x, 22, x + 8, 92], fill=(244, 192, 26))
    # Iconic red safety stripe & text
    draw.rectangle([0, 108, w, 128], fill=(208, 36, 36))
    f = _get_font(28, bold=True)
    draw.text((112, 138), "重慶國小  幼童專用車", fill=(32, 32, 36), font=f)
    im.save(os.path.join(TEX_DIR, "tex_bus_side.png"))


def gen_chainlink_mesh() -> None:
    """真正透空的墨綠色菱形防球鐵絲網 RGBA 貼圖（取代半透明玻璃板感）。"""
    size = 256
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    wire_col = (34, 72, 46, 235)
    step = 24
    for k in range(-size, size * 2, step):
        draw.line([(k, 0), (k + size, size)], fill=wire_col, width=3)
        draw.line([(k + size, 0), (k, size)], fill=wire_col, width=3)
    im.save(os.path.join(TEX_DIR, "tex_chainlink_green.png"))


def gen_city_facade() -> None:
    """低對比暖灰民宅樓層窗帶紋理（取代純白紙盒，襯托校園主體）。"""
    size = 512
    im = Image.new("RGB", (size, size), (204, 202, 198))
    draw = ImageDraw.Draw(im)
    rows, cols = 6, 4
    rh, cw = size // rows, size // cols
    for r in range(rows):
        y0 = r * rh
        draw.line([(0, y0), (size, y0)], fill=(178, 176, 172), width=3)
        for c in range(cols):
            x0 = c * cw
            draw.rectangle([x0 + 18, y0 + 20, x0 + cw - 18, y0 + rh - 24], fill=(162, 170, 176), outline=(182, 182, 180), width=2)
    im.save(os.path.join(TEX_DIR, "tex_city_facade.png"))


def gen_room_plaque_atlas() -> None:
    """v12.2：從 campus_cges.json（115 學年度班級配置圖）自動產生 4096x4096 高清全校真實教室門牌圖集（8x16=128 格，每格 512x256）。"""
    import json

    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus_cges.json")
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    cols, rows = 8, 16
    cw, ch = 512, 256
    atlas = Image.new("RGB", (cols * cw, rows * ch), (242, 245, 248))
    draw = ImageDraw.Draw(atlas)

    cat_rgb = {
        "grade1": (168, 85, 247),
        "grade2": (236, 72, 153),
        "grade3": (249, 115, 22),
        "grade4": (234, 179, 8),
        "grade5": (101, 163, 13),
        "grade6": (2, 132, 199),
        "youxue": (234, 138, 46),
        "kinder": (244, 63, 94),
        "admin": (79, 70, 229),
        "special": (13, 148, 136),
        "public": (100, 116, 139),
    }

    short_override = {
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
    }

    index_map = {}
    slot = 0
    f_school = _get_font(34, bold=True)
    f_code = _get_font(40, bold=True)

    for b in spec.get("buildings", []):
        bid = b["id"]
        for r_idx, rm in enumerate(b.get("rooms_115_detailed", [])):
            if slot >= cols * rows:
                break
            c = slot % cols
            r = slot // cols
            x0, y0 = c * cw, r * ch
            x1, y1 = x0 + cw, y0 + ch

            code = rm.get("code", "")
            raw_name = rm.get("name", "教室")
            disp = short_override.get(raw_name, raw_name)
            fl = rm.get("floor", "")
            accent = cat_rgb.get(rm.get("cat", "public"), (54, 96, 148))

            # Clean crisp white plaque body + outer navy border
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(247, 249, 252))
            draw.rectangle([x0 + 4, y0 + 4, x1 - 5, y1 - 5], outline=(28, 72, 132), width=6)

            # Top navy school header band (height 74px)
            draw.rectangle([x0 + 6, y0 + 6, x1 - 7, y0 + 80], fill=(22, 68, 134))
            draw.text((x0 + 24, y0 + 22), "重慶國小", fill=(255, 255, 255), font=f_school)

            # Top-right room code badge (gold) or floor tag
            tag_txt = code if code else fl
            tb = draw.textbbox((0, 0), tag_txt, font=f_code)
            tw = tb[2] - tb[0]
            draw.text((x1 - tw - 26, y0 + 18), tag_txt, fill=(254, 232, 118), font=f_code)

            # Main classroom / class name centered dynamically to fit cleanly with crisp contrast
            n_ch = len(disp)
            f_sz = 92 if n_ch <= 3 else (78 if n_ch == 4 else (64 if n_ch == 5 else (54 if n_ch == 6 else 46)))
            f_main = _get_font(f_sz, bold=True)
            mb = draw.textbbox((0, 0), disp, font=f_main)
            mw, mh = mb[2] - mb[0], mb[3] - mb[1]
            while mw > cw - 44 and f_sz > 30:
                f_sz -= 4
                f_main = _get_font(f_sz, bold=True)
                mb = draw.textbbox((0, 0), disp, font=f_main)
                mw, mh = mb[2] - mb[0], mb[3] - mb[1]
            tx = x0 + (cw - mw) // 2 - mb[0]
            ty = y0 + 84 + (148 - mh) // 2 - mb[1]
            draw.text((tx, ty), disp, fill=(20, 32, 52), font=f_main)

            # Bottom grade / category color stripe (16px)
            draw.rectangle([x0 + 7, y1 - 24, x1 - 8, y1 - 7], fill=accent)

            key = f"{bid}:{r_idx}"
            index_map[key] = {"col": c, "row": r, "cols": cols, "rows": rows, "label": f"{tag_txt} {disp}"}
            slot += 1

    atlas.save(os.path.join(TEX_DIR, "tex_room_plaques_atlas.png"), optimize=True)
    with open(os.path.join(TEX_DIR, "room_plaques_atlas_map.json"), "w", encoding="utf-8") as mf:
        json.dump({"cols": cols, "rows": rows, "entries": index_map}, mf, ensure_ascii=False, indent=2)


def gen_v12_5_wuquan_east_textures() -> None:
    """v12.5 9/2 五權街實景 1:1 五權樓東立面特色貼圖：
    1. tex_wuquan_vertical_banner.png (1024x4096, 1F-5F 大型直立彩繪宣傳布條: 溪瀑綠林/重慶國民小學/藍天彩虹/CCES/校徽樹苗/草丘)
    2. tex_wuquan_blue_banner.png (1024x256, 2F 欄杆深藍底白字標語橫牌)
    3. tex_wuquan_north_mural.png (1024x1024, 北端 1F 穿堂藍天彩繪壁畫)
    4. tex_wuquan_shutter_gray.png (512x512, 1F 霧面淺灰金屬鐵捲門)
    """
    # --- 1. 1F-5F Tall Vertical Illustrated School Banner (exact step_18_shot_1.png!) ---
    W, H = 1024, 4096
    im = Image.new("RGB", (W, H), (174, 212, 232))
    draw = ImageDraw.Draw(im)

    # Background vertical gradient: soft misty sky-blue top -> bright sky middle -> sunlit mint-green lower
    for y in range(H):
        t = y / (H - 1)
        if t < 0.42:
            k = t / 0.42
            c = (int(186 - 24 * k), int(214 - 8 * k), int(224 + 14 * k))
        elif t < 0.72:
            k = (t - 0.42) / 0.30
            c = (int(162 + 28 * k), int(206 + 18 * k), int(238 - 10 * k))
        else:
            k = (t - 0.72) / 0.28
            c = (int(190 - 20 * k), int(224 - 4 * k), int(228 - 44 * k))
        draw.line([(0, y), (W, y)], fill=c)

    # TOP SECTION (y=0..1680, 4F-5F): Flowing deep-blue cascading stream/waterfall flanked by lush green trees & warm sunlit foliage!
    # Left & right forest canopies
    for cx, cy, rx, ry, col in [
        (130, 320, 260, 290, (132, 174, 128)),
        (890, 290, 240, 270, (124, 168, 120)),
        (95, 760, 250, 360, (144, 184, 134)),
        (915, 810, 240, 340, (138, 178, 128)),
        (210, 1350, 290, 240, (152, 192, 138)),
        (830, 1380, 270, 230, (148, 188, 134)),
        (512, 1680, 560, 240, (156, 198, 146)),
        # Warm golden-yellow sunlit hill & figure glow (top-left/mid-left of waterfall, exact step_18_shot_1.png!)
        (360, 460, 150, 180, (236, 206, 128)),
        (650, 520, 110, 150, (242, 224, 158)),
    ]:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col)

    # Flowing cascading blue river/waterfall ribbon down center of upper half
    river_pts = [
        (465, 220), (620, 240), (745, 580), (780, 1080), (720, 1460), (650, 1660),
        (385, 1660), (265, 1420), (225, 1060), (275, 620), (380, 310),
    ]
    draw.polygon(river_pts, fill=(102, 134, 184))
    river_inner = [
        (485, 270), (595, 295), (695, 630), (720, 1080), (660, 1440), (590, 1610),
        (420, 1610), (335, 1400), (305, 1060), (345, 650), (425, 340),
    ]
    draw.polygon(river_inner, fill=(122, 154, 202))
    # White waterfall foam streaks on right edge (exact step_18_shot_1.png!)
    for x_off, y0_s, y1_s, w_s in [(700, 360, 1480, 42), (640, 480, 1380, 24), (355, 640, 1320, 18), (520, 420, 1120, 20)]:
        draw.rounded_rectangle([x_off - w_s // 2, y0_s, x_off + w_s // 2, y1_s], radius=w_s // 2, fill=(238, 245, 250))

    # Yellow storybook accent arcs at base of waterfall (y=1240..1580)
    draw.polygon([(260, 1550), (350, 1280), (420, 1550)], fill=(232, 208, 122))
    draw.ellipse([435, 1320, 595, 1580], fill=(166, 138, 184))
    draw.ellipse([540, 1400, 740, 1620], fill=(184, 210, 154))

    # 4F Horizontal School Title Ribbon: "重慶國民小學" (exact step_18_shot_1.png upper-mid!)
    draw.rounded_rectangle([32, 740, W - 32, 930], radius=36, fill=(238, 244, 248))
    draw.rounded_rectangle([44, 752, W - 44, 918], radius=30, fill=(142, 182, 218))
    f_title = _get_font(128, bold=True)
    title_txt = "重慶國民小學"
    tb = draw.textbbox((0, 0), title_txt, font=f_title)
    tw_t, th_t = tb[2] - tb[0], tb[3] - tb[1]
    tx_t = (W - tw_t) // 2 - tb[0]
    ty_t = 752 + (166 - th_t) // 2 - tb[1]
    # Crisp white outline + warm colorful lettering
    for ox in (-5, 0, 5):
        for oy in (-5, 0, 5):
            if ox or oy:
                draw.text((tx_t + ox, ty_t + oy), title_txt, fill=(252, 252, 252), font=f_title)
    draw.text((tx_t, ty_t), title_txt, fill=(224, 118, 92), font=f_title)

    # MIDDLE SECTION (y=1820..2680, 3F): Fluffy white clouds + bright 7-color Rainbow Arc!
    for cx, cy, rx, ry in [(180, 2020, 170, 95), (340, 1980, 150, 88), (820, 2040, 185, 102), (650, 2080, 140, 82)]:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(244, 248, 252))
    rb_colors = [
        (236, 98, 98),    # Red
        (244, 156, 78),   # Orange
        (246, 218, 86),   # Yellow
        (124, 202, 128),  # Green
        (96, 178, 232),   # Sky Blue
        (142, 134, 216),  # Violet
    ]
    rb_cx, rb_cy = 560, 2720
    for idx_rb, rcol in enumerate(rb_colors):
        rad = 450 - idx_rb * 34
        draw.pieslice([rb_cx - rad, rb_cy - rad, rb_cx + rad, rb_cy + rad], start=195, end=345, fill=rcol)
    rad_in = 450 - len(rb_colors) * 34
    draw.pieslice([rb_cx - rad_in, rb_cy - rad_in, rb_cx + rad_in, rb_cy + rad_in], start=195, end=345, fill=(182, 218, 236))

    # LOWER-MID SECTION (y=2640..3460, 2F): Big Stylized "CGES" + Campus Arched Gate & Iconic Green-Teal Y School Emblem!
    # Cloud backdrop behind CGES
    for cx, cy, rx, ry in [(220, 2860, 220, 160), (512, 2840, 310, 185), (810, 2870, 210, 160)]:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(234, 244, 250))

    # Stylized "CGES" multicolor-outlined pastel-blue/purple letters (exact step_18_shot_1.png!)
    f_cges = _get_font(215, bold=True)
    cges_txt = "CGES"
    cb = draw.textbbox((0, 0), cges_txt, font=f_cges)
    cw_c, ch_c = cb[2] - cb[0], cb[3] - cb[1]
    cx_c = (W - cw_c) // 2 - cb[0]
    cy_c = 2690 - cb[1]
    for ox in (-7, 0, 7):
        for oy in (-7, 0, 7):
            if ox or oy:
                draw.text((cx_c + ox, cy_c + oy), cges_txt, fill=(252, 252, 252), font=f_cges)
    draw.text((cx_c, cy_c), cges_txt, fill=(136, 166, 214), font=f_cges)

    # Small subtitle pill "重慶國小"
    f_sub = _get_font(74, bold=True)
    sub_txt = "重慶國小"
    sb = draw.textbbox((0, 0), sub_txt, font=f_sub)
    draw.text(((W - (sb[2] - sb[0])) // 2 - sb[0], 2945 - sb[1]), sub_txt, fill=(146, 118, 178), font=f_sub)

    # Pastel pink/lavender campus archway building silhouette & palm tufts framing central white-and-green Y school emblem
    draw.rounded_rectangle([185, 3120, 840, 3620], radius=24, fill=(216, 178, 198))
    draw.rounded_rectangle([245, 3060, 780, 3580], radius=28, fill=(238, 224, 232))
    # Iconic CGES Green Y-Sprout School Emblem centered in 2F-1F transition!
    em_cx, em_cy = 512, 3300
    draw.ellipse([em_cx - 148, em_cy - 148, em_cx + 148, em_cy + 148], fill=(248, 250, 248), outline=(112, 178, 134), width=12)
    # Left green arm, right teal arm, central trunk of CGES emblem
    draw.line([(em_cx, em_cy + 98), (em_cx, em_cy - 8)], fill=(66, 148, 102), width=30)
    draw.line([(em_cx, em_cy - 8), (em_cx - 78, em_cy - 76)], fill=(66, 148, 102), width=28)
    draw.line([(em_cx, em_cy - 8), (em_cx + 78, em_cy - 76)], fill=(58, 142, 132), width=28)
    draw.line([(em_cx - 92, em_cy - 34), (em_cx - 28, em_cy + 26)], fill=(92, 174, 118), width=22)
    draw.line([(em_cx + 92, em_cy - 34), (em_cx + 28, em_cy + 26)], fill=(78, 166, 148), width=22)

    # Flanking mini green palm/tree accents
    for px_t in (130, 895):
        draw.ellipse([px_t - 110, 3040, px_t + 110, 3260], fill=(144, 196, 138))
        draw.rectangle([px_t - 20, 3220, px_t + 20, 3580], fill=(176, 152, 132))

    # BOTTOM SECTION (y=3540..4096, 1F): Rolling sunlit green hills + cheerful yellow/orange children motif!
    draw.ellipse([-140, 3580, 1160, 4340], fill=(156, 198, 128))
    draw.ellipse([180, 3720, 1220, 4420], fill=(134, 184, 114))
    for fx, fy, fr, fc in [
        (360, 3820, 56, (242, 198, 108)),
        (510, 3760, 62, (238, 146, 118)),
        (670, 3860, 52, (244, 214, 116)),
        (230, 3940, 36, (246, 236, 158)),
        (790, 3930, 38, (232, 162, 142)),
    ]:
        draw.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=fc)

    # Subtle weathered outdoor banner fabric sheen + horizontal hem borders
    draw.rectangle([0, 0, W - 1, 22], fill=(224, 228, 232))
    draw.rectangle([0, H - 22, W - 1, H - 1], fill=(224, 228, 232))
    im.save(os.path.join(TEX_DIR, "tex_wuquan_vertical_banner.png"), optimize=True)

    # --- 2. 2F Corridor Deep-Navy White-Text Horizontal Plaque (exact step_18_shot_1.png & step_16_shot_1.png!) ---
    im_b = Image.new("RGB", (1024, 256), (34, 62, 108))
    db = ImageDraw.Draw(im_b)
    db.rectangle([10, 10, 1013, 245], outline=(236, 242, 248), width=8)
    fb = _get_font(74, bold=True)
    btxt = "友善校園・健康快樂成長"
    bb = db.textbbox((0, 0), btxt, font=fb)
    db.text(((1024 - (bb[2] - bb[0])) // 2 - bb[0], (256 - (bb[3] - bb[1])) // 2 - bb[1]), btxt, fill=(248, 250, 252), font=fb)
    im_b.save(os.path.join(TEX_DIR, "tex_wuquan_blue_banner.png"), optimize=True)

    # --- 3. North Breezeway 1F Painted Sky & Hills Mural (exact step_14_shot_1.png far right!) ---
    im_m = Image.new("RGB", (1024, 1024), (118, 184, 232))
    dm = ImageDraw.Draw(im_m)
    for y in range(1024):
        t = y / 1023.0
        dm.line([(0, y), (1024, y)], fill=(int(96 + 74 * t), int(168 + 48 * t), int(234 - 16 * t)))
    # Fluffy clouds + rainbow ribbon + rolling green/yellow hills + colorful school motifs
    for cx, cy, rx, ry in [(220, 220, 150, 75), (760, 190, 170, 82), (500, 310, 130, 62)]:
        dm.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(246, 250, 254))
    for i_r, rcol in enumerate([(238, 102, 102), (246, 174, 82), (244, 222, 92), (116, 198, 128), (94, 172, 234)]):
        r_m = 420 - i_r * 28
        dm.pieslice([520 - r_m, 760 - r_m, 520 + r_m, 760 + r_m], start=195, end=345, fill=rcol)
    dm.pieslice([520 - 280, 760 - 280, 520 + 280, 760 + 280], start=195, end=345, fill=(154, 204, 234))
    dm.ellipse([-120, 640, 720, 1200], fill=(122, 186, 114))
    dm.ellipse([360, 690, 1180, 1220], fill=(146, 202, 124))
    for cx, cy, rad, fc in [(260, 790, 48, (246, 206, 98)), (540, 820, 54, (238, 126, 136)), (790, 770, 44, (112, 178, 236))]:
        dm.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=fc)
    im_m.save(os.path.join(TEX_DIR, "tex_wuquan_north_mural.png"), optimize=True)

    # --- 4. 1F Matte Light-Gray Corrugated Metal Roll-Up Shutter (exact step_16_shot_1.png!) ---
    im_s = Image.new("RGB", (512, 512), (186, 186, 182))
    ds = ImageDraw.Draw(im_s)
    slat_h = 16
    for y0_s in range(0, 512, slat_h):
        shade = 178 + ((y0_s // slat_h) % 2) * 6
        ds.rectangle([0, y0_s, 511, y0_s + slat_h - 1], fill=(shade, shade, shade - 3))
        ds.line([(0, y0_s), (511, y0_s)], fill=(138, 138, 134), width=2)
        ds.line([(0, y0_s + 3), (511, y0_s + 3)], fill=(208, 208, 204), width=2)
    # Bottom heavy steel sill bar + central recessed pull handle
    ds.rectangle([0, 480, 511, 511], fill=(132, 134, 136))
    ds.rectangle([216, 448, 296, 470], fill=(92, 94, 98), outline=(210, 212, 214), width=2)
    # Subtle side guide channels
    ds.rectangle([0, 0, 14, 511], fill=(142, 142, 138))
    ds.rectangle([497, 0, 511, 511], fill=(142, 142, 138))
    im_s.save(os.path.join(TEX_DIR, "tex_wuquan_shutter_gray.png"), optimize=True)


def gen_v12_6_north_court_textures() -> None:
    """v12.6 2 五權街 & 147 和平路實景 1:1 操場北側空間專屬貼圖：
    1. tex_court_north_concrete.png (2048x1024, 東北角雙半場舊化水泥籃球場＋白線＋北緣粗白虛線區塊帶)
    2. tex_backboard_white.png (512x320, 實景白底黑框紅方框籃板)
    3. tex_walkway_terrazzo.png (1024x1024, 五權樓東側淺暖灰伸縮縫方格磨石子水泥大道)
    """
    # --- 1. North Dual Half-Court Weathered Gray Concrete Basketball Court (exact step_6_shot_1.png & step_4.png!) ---
    W, H = 2048, 1024
    rng = random.Random(1261)
    im = Image.new("RGB", (W, H), (178, 180, 176))
    draw = ImageDraw.Draw(im)
    # Subtle weathered concrete slab patches & fine aggregate mottling
    for _ in range(360):
        px = rng.randint(0, W)
        py = rng.randint(0, H)
        rw = rng.randint(45, 220)
        rh = rng.randint(35, 160)
        v = rng.randint(-12, 10)
        draw.ellipse([px - rw, py - rh, px + rw, py + rh], fill=(176 + v, 178 + v, 174 + v))
    im = im.filter(ImageFilter.GaussianBlur(radius=14))
    draw = ImageDraw.Draw(im)
    # Subtle concrete expansion grid joints (realistic outdoor concrete court!)
    for gx in range(0, W, 256):
        draw.line([(gx, 0), (gx, H)], fill=(150, 152, 148), width=3)
    for gy in range(0, H, 256):
        draw.line([(0, gy), (W, gy)], fill=(150, 152, 148), width=3)

    # Note: In OpenGL UV, top of PIL image (y=0) maps to V=1 (NORTH / Heping Rd fence), bottom (y=H) maps to V=0 (SOUTH / basketball poles!)
    wline = (238, 240, 236)
    # Iconic thick white dashed rectangular blocks along NORTH edge next to tree-soil strip (exact step_6_shot_1.png!)
    for bx in range(44, W - 44, 128):
        draw.rectangle([bx, 34, bx + 78, 72], fill=(234, 236, 232))

    # Outer white court perimeter boundary + center dividing line separating East & West half-courts
    m_x, m_top, m_bot = 52, 118, 960
    draw.rectangle([m_x, m_top, W - m_x, m_bot], outline=wline, width=10)
    draw.line([(W // 2, m_top), (W // 2, m_bot)], fill=wline, width=10)

    # Two side-by-side Half-Courts (both baskets sit along SOUTH baseline y=m_bot, arcs open toward NORTH y=m_top!)
    for hc_x in (W // 4, (3 * W) // 4):
        # 3-point arc opening northward from south baseline
        r3 = 415
        draw.arc([hc_x - r3, m_bot - 90 - r3, hc_x + r3, m_bot - 90 + r3], start=192, end=348, fill=wline, width=9)
        draw.line([(hc_x - r3 + 8, m_bot - 90), (hc_x - r3 + 8, m_bot)], fill=wline, width=9)
        draw.line([(hc_x + r3 - 8, m_bot - 90), (hc_x + r3 - 8, m_bot)], fill=wline, width=9)
        # Rectangular paint / key box + free-throw top semicircle
        kw, kh = 185, 365
        draw.rectangle([hc_x - kw, m_bot - kh, hc_x + kw, m_bot], outline=wline, width=9)
        r_ft = 128
        draw.ellipse([hc_x - r_ft, m_bot - kh - r_ft, hc_x + r_ft, m_bot - kh + r_ft], outline=wline, width=8)
        # Restricted area small arc near hoop
        draw.arc([hc_x - 86, m_bot - 150, hc_x + 86, m_bot + 22], start=180, end=360, fill=wline, width=7)
        # Lane hash marks
        for hy_off in (110, 175, 240, 300):
            draw.line([(hc_x - kw - 18, m_bot - hy_off), (hc_x - kw, m_bot - hy_off)], fill=wline, width=7)
            draw.line([(hc_x + kw, m_bot - hy_off), (hc_x + kw + 18, m_bot - hy_off)], fill=wline, width=7)

    im.save(os.path.join(TEX_DIR, "tex_court_north_concrete.png"), optimize=True)

    # --- 2. Crisp White Backboard with Black Outer Border & Red Target Square (exact step_6_shot_1.png!) ---
    bw, bh = 512, 320
    im_bb = Image.new("RGB", (bw, bh), (242, 244, 246))
    dbb = ImageDraw.Draw(im_bb)
    dbb.rectangle([10, 10, bw - 11, bh - 11], outline=(34, 38, 42), width=12)
    # Center red shooter's square above rim
    dbb.rectangle([bw // 2 - 78, bh - 138, bw // 2 + 78, bh - 26], outline=(206, 44, 42), width=10)
    im_bb.save(os.path.join(TEX_DIR, "tex_backboard_white.png"), optimize=True)

    # --- 3. Wuquan East Light-Warm-Gray Terrazzo / Concrete Grid Walkway (exact step_8_shot_1.png right!) ---
    tw, th = 1024, 1024
    rng2 = random.Random(1262)
    im_w = Image.new("RGB", (tw, th), (178, 179, 176))
    dw = ImageDraw.Draw(im_w)
    cell = 256
    for r in range(4):
        for c in range(4):
            v = rng2.randint(-5, 5)
            x0, y0 = c * cell, r * cell
            dw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=(178 + v, 179 + v, 176 + v))
    for _ in range(1800):
        px = rng2.randint(0, tw - 1)
        py = rng2.randint(0, th - 1)
        v = rng2.randint(-14, 12)
        dw.point((px, py), fill=(176 + v, 177 + v, 174 + v))
    # Crisp expansion joint grid lines
    for i in range(0, tw, cell):
        dw.line([(i, 0), (i, th)], fill=(138, 140, 138), width=4)
        dw.line([(0, i), (tw, i)], fill=(138, 140, 138), width=4)
    im_w.save(os.path.join(TEX_DIR, "tex_walkway_terrazzo.png"), optimize=True)


def main() -> None:
    gen_tile_wall_pbr("tex_wall_guanghe", (232, 224, 218), (182, 174, 168), cols=16, rows=16, jitter=6, seed=11)
    gen_tile_wall_pbr("tex_wall_brick_red", (166, 98, 86), (116, 70, 62), cols=16, rows=16, jitter=9, seed=22)
    gen_tile_wall_pbr("tex_wall_salmon", (204, 144, 126), (160, 112, 98), cols=16, rows=16, jitter=8, seed=33)
    gen_tile_wall_pbr("tex_wall_stone_cream", (218, 212, 202), (168, 162, 152), cols=12, rows=12, jitter=7, seed=44)
    gen_tile_wall_pbr("tex_paving_redbrick", (162, 100, 90), (122, 108, 102), cols=8, rows=16, jitter=11, seed=77, stagger=True)

    gen_south_mosaic_wall()
    gen_solar_panel()
    gen_school_sign()
    gen_emblem_cges()
    gen_facade_banner("tex_banner_3f.png", "快樂", "Happiness", ((214, 152, 210), (242, 114, 168)), (226, 76, 134))
    gen_facade_banner("tex_banner_4f.png", "健康", "Healthy", ((106, 194, 216), (144, 182, 226)), (58, 162, 142))
    gen_facade_banner("tex_banner_5f.png", "勤學", "Diligent", ((146, 178, 228), (178, 142, 214)), (88, 122, 206))
    gen_led_campus()
    gen_breezeway_header()
    gen_basketball_court()
    gen_track_pu()
    gen_grass()
    gen_skybridge_dolphin()
    gen_gym_banner()
    gen_gym_shutter()
    gen_chainlink_mesh()
    gen_building_name_plaques()
    gen_bus_side()
    gen_v5_campus_interior_textures()
    gen_v6_front_streetview_textures()
    gen_v7_front_ground_and_signs()
    gen_v8_street_realism_textures()
    gen_v9_south_streetview_textures()
    gen_v10_east_wuquan_textures()
    gen_v11_north_heping_textures()
    gen_city_facade()
    gen_room_plaque_atlas()
    gen_v12_5_wuquan_east_textures()
    gen_v12_6_north_court_textures()
    print(f"Generated PBR textures + normal maps in {TEX_DIR}: {len(os.listdir(TEX_DIR))} files")


if __name__ == "__main__":
    main()
