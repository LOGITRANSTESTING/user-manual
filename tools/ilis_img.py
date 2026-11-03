"""ILISCyber screenshot tools: prep (grey side crop, border, grey padding), marking with
automatic circle placement, clearing old marks, number stripping (mapping), find/snap/OCR,
crop, copy, erase, dim, preview sheets."""
import json, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RED = (255, 0, 0)
BLUE = (0, 102, 204)
GREY_PAD = (153, 153, 153)
B = 21  # 1px margin + 2px line + 18px padding
DIM = 0.549  # measured from ILISCyber dimmed pop-up screenshots


# ---------------------------------------------------------------- basics
def load(p):
    im = Image.open(p)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGB', im.size, 'white'); bg.paste(im, mask=im.split()[3]); return bg
    return im.convert('RGB')


def save(im, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True); im.save(p)


def sidecar(p):
    s = Path(str(p) + '.json')
    return json.loads(s.read_text()) if s.exists() else {}


def write_sidecar(p, d):
    Path(str(p) + '.json').write_text(json.dumps(d, indent=1))


def box_arg(s):
    v = [int(round(float(x))) for x in str(s).replace(' ', '').split(',')]
    if len(v) != 4: raise ValueError('box must be x0,y0,x1,y1: %s' % s)
    return v


def _font(size):
    for f in ('arialbd.ttf', 'Arial Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'DejaVuSans-Bold.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        try: return ImageFont.truetype(f, size)
        except OSError: pass
    return ImageFont.load_default()


# ---------------------------------------------------------------- prep
def side_crop(img):
    """(left, right) pixels of grey side area (shadow / grey strip / dimmed background / blank padding)."""
    a = np.array(img.convert('L')).astype(int); H, W = a.shape
    full = a.min(0) >= 254
    padR = 0
    while padR < W and full[W - 1 - padR]: padR += 1
    if padR < 20: padR = 0
    seg = a[int(H * .25):int(H * .9)]
    col = seg.mean(0); std = seg.std(0)
    # real grey only (shadow, grey strip, dimmed background). The app's own light page background
    # (about 245-250) is content and is never cropped.
    grey = (col < 238) & (col > 120) & (std < 10) & ~((col > 132) & (col < 146))  # ~140 = the light page background dimmed: content
    white = col >= 250

    def run(order):
        i = 0
        while i < 3 and i < len(order) and white[order[i]]: i += 1
        start = i; last = None; gap = 0
        while i < len(order):
            if grey[order[i]]: last = i; gap = 0
            elif white[order[i]]:
                gap += 1
                if gap > 2: break
            else: break
            i += 1
        if last is None or last - start + 1 < 3: return 0
        return last + 1
    return run(list(range(W))), padR + run(list(range(W - 1 - padR, -1, -1)))


def is_dimmed(im):
    w, h = im.size; o = 25
    if w < 60 or h < 60: return False
    edge = [im.getpixel((x, o)) for x in range(o, w - o, 7)] + [im.getpixel((o, y)) for y in range(o, h - o, 7)]
    lum = sorted(sum(p) / 3 for p in edge)
    return lum[len(lum) // 2] < 200


def add_border(im, pad=18, line=2, radius=12, color=BLUE, fill='white'):
    w, h = im.size
    W, H = w + 2 * (1 + line + pad), h + 2 * (1 + line + pad)
    can = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(can)
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=radius, outline=color, width=line, fill=fill)
    can.paste(im, (1 + line + pad, 1 + line + pad))
    return can


def prep(src, dst, side=False, border=True, crop=True):
    """Crop grey sides (not for side-function shots), add the house border; grey padding if dimmed."""
    im = load(src)
    l = r = 0
    if crop and not side:
        l, r = side_crop(im)
        if l or r: im = im.crop((l, 0, im.width - r, im.height))
    dim = is_dimmed(im)
    if border:
        im = add_border(im, fill=GREY_PAD if dim else 'white')
    save(im, dst)
    meta = {'source': str(src), 'crop_left': l, 'crop_right': r, 'border': B if border else 0,
            'dimmed': dim, 'marked': False, 'size': im.size}
    write_sidecar(dst, meta)
    return meta


def strip_border(im):
    """Remove the house blue border (21px, or 17px in older manuals). Returns (image, removed)."""
    a = np.array(im).astype(int)
    for b in (21, 17):
        top = a[1:4, a.shape[1] // 4:3 * a.shape[1] // 4].reshape(-1, 3)
        isblue = np.mean((abs(top[:, 1] - 102) < 45) & (abs(top[:, 2] - 204) < 45) & (top[:, 0] < 60)) > 0.3
        if isblue:
            # decide 21 vs 17 by where the padding ends (first non-padding row)
            pad = a[b - 1, a.shape[1] // 4:3 * a.shape[1] // 4]
            return im.crop((b, b, im.width - b, im.height - b)), b
    return im, 0


# ---------------------------------------------------------------- ink / free test
def ink_map(im):
    g = im.convert('L').filter(ImageFilter.FIND_EDGES)
    e8 = (np.array(g) > 50).astype(np.uint8)
    # long straight lines (panel borders, grid lines, separators) do not block a circle - only text/icons do
    lines = cv2.morphologyEx(e8, cv2.MORPH_OPEN, np.ones((1, 21), np.uint8)) | cv2.morphologyEx(e8, cv2.MORPH_OPEN, np.ones((21, 1), np.uint8))
    e = (e8 & (1 - cv2.dilate(lines, np.ones((3, 3), np.uint8)))).astype(np.float32)
    hsv = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2HSV)
    sat = ((hsv[..., 1] > 80) & (hsv[..., 2] > 60)).astype(np.float32)
    return e + 0.25 * sat


def circle_mask(shape, cx, cy, r):
    H, W = shape
    yy, xx = np.ogrid[:H, :W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


def box_line_mask(shape, box, w=3):
    m = np.zeros(shape, bool); x0, y0, x1, y1 = box
    m[max(y0, 0):y0 + w, max(x0, 0):x1 + 1] = True; m[max(y1 - w + 1, 0):y1 + 1, max(x0, 0):x1 + 1] = True
    m[max(y0, 0):y1 + 1, max(x0, 0):x0 + w] = True; m[max(y0, 0):y1 + 1, max(x1 - w + 1, 0):x1 + 1] = True
    return m


def contains(a, b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3]


# ---------------------------------------------------------------- marking
def classify(box):
    w, h = box[2] - box[0], box[3] - box[1]
    if h >= 60: return 'tall'
    if w <= 160 and h <= 45: return 'button'
    return 'line'


def candidates(box, kind):
    x0, y0, x1, y1 = box; my = (y0 + y1) / 2; h = y1 - y0
    P = {'left': (x0 + 1, my), 'right': (x1 - 1, my), 'bottomleft': (x0 + 1, y1 - 1), 'bottomright': (x1 - 1, y1 - 1),
         'topleft': (x0 + 1, y0 + 1), 'topright': (x1 - 1, y0 + 1), 'left60': (x0 + 1, y0 + 0.6 * h)}
    if kind == 'button': order = ['left', 'right', 'topleft', 'topright']
    elif kind == 'tall': order = ['left', 'left60', 'bottomleft', 'bottomright', 'topleft', 'topright']
    else: order = ['bottomleft', 'bottomright', 'topleft', 'topright']
    return [(k, P[k]) for k in order], P


def content_bbox(im, box):
    """Tight bbox of non-background content inside box (used for padding buttons)."""
    x0, y0, x1, y1 = box
    a = np.array(im.crop((x0, y0, x1, y1)).convert('L')).astype(int)
    if a.size == 0: return None
    bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]))
    m = np.abs(a - bg) > 40
    ys, xs = np.where(m)
    if len(xs) == 0: return None
    return [x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max()]


def draw_circle(d, cx, cy, n, r=14):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='white', outline=RED, width=2)
    d.text((cx, cy + 1), str(n), fill=RED, font=_font(16 if n < 10 else 13), anchor='mm')


def mark(src, dst, spec, coords='raw', r=14, report=True):
    """spec: list of entries
       {"box":[x0,y0,x1,y1], "n":5, "kind":"button|tall|line", "pos":"left|right|bottomleft|bottomright|topleft|topright"}
       {"box":[...], "n":null}                       unnumbered context box
       {"pair":{"big":[...],"btn":[...]}, "n":3, "type":"query|popup"}   two-box / one-number rule
       coords='raw' -> coordinates are on the ORIGINAL screenshot; converted using the prep sidecar."""
    im = load(src); meta = sidecar(src)
    off_x = off_y = 0
    if coords == 'raw' and meta:
        off_x = meta.get('border', 0) - meta.get('crop_left', 0); off_y = meta.get('border', 0)
    T = lambda b: [b[0] + off_x, b[1] + off_y, b[2] + off_x, b[3] + off_y]
    ink = ink_map(im); H, W = ink.shape
    entries = []
    for e in spec:
        e = dict(e)
        if 'pair' in e:
            e['pair'] = {'big': T(e['pair']['big']), 'btn': T(e['pair']['btn'])}
        else:
            e['box'] = T(e['box'])
        entries.append(e)
    # pad buttons so the circle clears the content
    for e in entries:
        if 'box' in e and e.get('n') is not None:
            kind = e.get('kind') or classify(e['box']); e['kind'] = kind
            if kind == 'button' and e.get('pos', 'left') in ('left', None):
                cb = content_bbox(im, e['box'])
                if cb and cb[0] - e['box'][0] < r + 2:
                    e['box'][0] = max(0, cb[0] - (r + 3))
    boxes = [e['box'] for e in entries if 'box' in e] + [b for e in entries if 'pair' in e for b in (e['pair']['big'], e['pair']['btn'])]
    d = ImageDraw.Draw(im)
    for e in entries:
        for b in ([e['box']] if 'box' in e else [e['pair']['big'], e['pair']['btn']]):
            d.rectangle(b, outline=RED, width=int(e.get('width', 3)))
    circles = []; log = []
    for e in entries:
        n = e.get('n')
        if n is None: continue
        if 'pair' in e:
            big, btn = e['pair']['big'], e['pair']['btn']
            cx = (btn[0] + btn[2]) / 2
            cy = (btn[3] + big[3]) / 2 if e.get('type', 'query') == 'query' else (big[3] + btn[1]) / 2
            circles.append((cx, cy, n)); log.append((n, 'pair-' + e.get('type', 'query'), cx, cy)); continue
        box = e['box']; kind = e['kind']
        cands, P = candidates(box, kind)
        if e.get('pos'):
            k = e['pos']; cx, cy = P[k]; chosen = k
        else:
            chosen = None
            for k, (cx, cy) in cands:
                if cx - r < 0 or cy - r < 0 or cx + r >= W or cy + r >= H: continue
                cm = circle_mask((H, W), cx, cy, r)
                own = box_line_mask((H, W), box)
                score = (ink * cm * ~own).sum() / cm.sum()
                clash = False
                for b in boxes:
                    if b is box or contains(b, box): continue
                    if (cm & box_line_mask((H, W), b)).any(): clash = True; break
                for (ox, oy, _) in circles:
                    if (ox - cx) ** 2 + (oy - cy) ** 2 < (2 * r + 2) ** 2: clash = True
                if not clash and score < 0.06: chosen = k; break
            if chosen is None:
                chosen, (cx, cy) = cands[0]; log.append((n, 'WARNING no free spot, used ' + chosen, cx, cy))
        circles.append((cx, cy, n)); log.append((n, chosen, cx, cy))
    for cx, cy, n in circles: draw_circle(d, cx, cy, n, r)
    save(im, dst)
    m2 = dict(meta); m2['marked'] = True; m2['marks'] = spec; write_sidecar(dst, m2)
    return log


# ---------------------------------------------------------------- clearing old marks
def red_mask(a):
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    return ((r > 180) & (g < 130) & (b < 100)).astype(np.uint8)


def find_circles(a, red):
    H, W = red.shape; found = []
    for p2 in (11, 9):
        cs = cv2.HoughCircles(cv2.GaussianBlur(red * 255, (3, 3), 0), cv2.HOUGH_GRADIENT, dp=1, minDist=16,
                              param1=60, param2=p2, minRadius=10, maxRadius=17)
        for cx0, cy0, _ in ([] if cs is None else cs[0]):
            best = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for rad in range(10, 18):
                        cx, cy = int(round(cx0)) + dx, int(round(cy0)) + dy; ok = 0
                        for t in np.deg2rad(np.arange(0, 360, 10)):
                            x, y = int(round(cx + rad * np.cos(t))), int(round(cy + rad * np.sin(t)))
                            ok += (not (0 <= x < W and 0 <= y < H)) or red[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2].any()
                        if best is None or ok > best[0]: best = (ok, cx, cy, rad)
            ok, cx, cy, rad = best
            inner = [a[y, x].mean() > 200 and not red[y, x] for t in np.deg2rad(np.arange(0, 360, 10))
                     for x, y in [(int(round(cx + 0.75 * rad * np.cos(t))), int(round(cy + 0.75 * rad * np.sin(t))))]
                     if 0 <= x < W and 0 <= y < H]
            if ok >= 30 and inner and np.mean(inner) >= 0.6:
                if not any((cx - fx) ** 2 + (cy - fy) ** 2 < 100 for fx, fy, _ in found): found.append((cx, cy, rad))
    return found


def axis_fill(a, mask, tol=30):
    """Fill masked pixels the way UI screens are built: continue straight rows/columns.
    For each pixel, look left/right and up/down to the nearest unmasked pixels; if the pair on one
    axis agrees (background, a grid line running through), use it; otherwise use the nearest one."""
    a = a.copy(); H, W = mask.shape
    ys, xs = np.where(mask > 0)
    src = a.astype(int)
    for y, x in zip(ys, xs):
        l = x - 1
        while l >= 0 and mask[y, l]: l -= 1
        r = x + 1
        while r < W and mask[y, r]: r += 1
        u = y - 1
        while u >= 0 and mask[u, x]: u -= 1
        d = y + 1
        while d < H and mask[d, x]: d += 1
        L = src[y, l] if l >= 0 else None; R = src[y, r] if r < W else None
        U = src[u, x] if u >= 0 else None; D = src[d, x] if d < H else None
        hv = L is not None and R is not None and np.abs(L - R).sum() < tol
        vv = U is not None and D is not None and np.abs(U - D).sum() < tol
        if hv and vv:
            a[y, x] = L if (r - l) <= (d - u) else U
        elif vv: a[y, x] = U
        elif hv: a[y, x] = L
        else:
            c = [(x - l, L), (r - x, R), (y - u, U), (d - y, D)]
            c = [t for t in c if t[1] is not None]
            a[y, x] = min(c, key=lambda t: t[0])[1]
    return a


def clear_marks(im, unborder=True):
    """Remove red boxes, numbered circles and stubs (inpaint). Keeps the app's own red UI where possible."""
    if unborder: im, _ = strip_border(im)
    a = np.array(im)
    red = red_mask(a)
    hor = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((1, 25), np.uint8))
    ver = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((25, 1), np.uint8))
    mask = hor | ver
    for cx, cy, rad in find_circles(a, red): cv2.circle(mask, (cx, cy), rad + 3, 1, -1)
    near = cv2.dilate(mask, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((red & (1 - mask)).astype(np.uint8))
    for i in range(1, n):
        w_, h_, area = st[i][2], st[i][3], st[i][4]; comp = lab == i
        if (comp & (near > 0)).any() and area < 400 and (w_ >= 3 * h_ or h_ >= 3 * w_): mask[comp] = 1
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    return Image.fromarray(axis_fill(a, mask)), int(mask.sum())


def strip_numbers(im, unborder=True):
    """Mapping-document conversion: remove the border and the numbered circles, keep the red boxes.
    Boxes are cleared with the circles and redrawn as whole rectangles, so no line is left broken."""
    removed = 0
    if unborder: im, removed = strip_border(im)
    a = np.array(im).copy()
    red = red_mask(a); H, W = red.shape
    circles = find_circles(a, red)
    if not circles: return im, [], removed
    lines = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((1, 15), np.uint8)) | cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((15, 1), np.uint8))
    mask = lines.copy()
    for cx, cy, rad in circles: cv2.circle(mask, (cx, cy), rad + 3, 1, -1)
    near = cv2.dilate(mask, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((red & (1 - mask)).astype(np.uint8))
    for i in range(1, n):  # small red stubs next to removed marks
        w_, h_, area = st[i][2], st[i][3], st[i][4]; comp = lab == i
        if (comp & (near > 0)).any() and area < 400 and (w_ >= 3 * h_ or h_ >= 3 * w_): mask[comp] = 1
    clean = axis_fill(a, cv2.dilate(mask, np.ones((3, 3), np.uint8)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(lines, np.ones((2, 2), np.uint8)))
    boxes_to_draw = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        comp = (lab == i) & (lines > 0)
        if w < 8 or h < 8: continue
        band = np.zeros_like(comp); band[y:y + 5, x:x + w] = 1; band[y + h - 5:y + h, x:x + w] = 1; band[y:y + h, x:x + 5] = 1; band[y:y + h, x + w - 5:x + w] = 1
        frac = (comp & (band > 0)).sum() / max(1, comp.sum())
        if frac >= 0.9:
            col = comp[y:y + h, x + w // 2]; t = int(max(2, min(5, col[:h // 2].sum())))
            boxes_to_draw.append(([int(x), int(y), int(x + w - 1), int(y + h - 1)], t))
        else:
            clean[comp] = a[comp]
    out = Image.fromarray(clean); d = ImageDraw.Draw(out)
    for b, t in boxes_to_draw: d.rectangle(b, outline=RED, width=t)
    return out, [(int(c[0]), int(c[1])) for c in circles], removed


def patch_from_similar(clean, donor, region, ctx=20, min_score=0.9):
    """Rebuild a smudged spot from a similar unmarked screenshot of the same screen."""
    a = np.array(clean).copy(); d = np.array(donor)
    x0, y0, x1, y1 = region; H, W = a.shape[:2]
    X0, Y0, X1, Y1 = max(x0 - ctx, 0), max(y0 - ctx, 0), min(x1 + ctx, W), min(y1 + ctx, H)
    tpl = a[Y0:Y1, X0:X1]; m = np.ones(tpl.shape[:2], np.uint8) * 255
    m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = 0
    res = cv2.matchTemplate(d, tpl, cv2.TM_CCORR_NORMED, mask=np.dstack([m] * 3))
    _, score, _, (bx, by) = cv2.minMaxLoc(np.nan_to_num(res))
    if score >= min_score:
        a[y0:y1, x0:x1] = d[by + (y0 - Y0):by + (y1 - Y0), bx + (x0 - X0):bx + (x1 - X0)]
    return Image.fromarray(a), float(score)


def spot_sheet(before, after, spots, out, r=26, zoom=4):
    """Zoomed before/after crops of every spot (circle positions) for a quick visual check."""
    tiles = []
    for (x, y) in spots:
        b = (int(x - r), int(y - r), int(x + r), int(y + r))
        t = Image.new('RGB', (4 * r * zoom + 10, 2 * r * zoom), 'white')
        t.paste(before.crop(b).resize((2 * r * zoom, 2 * r * zoom), Image.NEAREST), (0, 0))
        t.paste(after.crop(b).resize((2 * r * zoom, 2 * r * zoom), Image.NEAREST), (2 * r * zoom + 10, 0))
        tiles.append(t)
    if not tiles: return None
    can = Image.new('RGB', (tiles[0].width, sum(t.height + 8 for t in tiles)), (200, 200, 200)); y = 0
    for t in tiles: can.paste(t, (0, y)); y += t.height + 8
    save(can, out); return out


def find_red_boxes(im):
    a = np.array(im); red = red_mask(a)
    lines = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((1, 25), np.uint8)) | cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((25, 1), np.uint8))
    lines = cv2.dilate(lines, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(lines)
    return [[int(x), int(y), int(x + w - 1), int(y + h - 1)] for x, y, w, h, a_ in st[1:] if w > 10 and h > 10]


# ---------------------------------------------------------------- find / snap / OCR
def tesseract_exe():
    for c in (shutil.which('tesseract'), r'C:\Program Files\Tesseract-OCR\tesseract.exe',
              r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe', os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')):
        if c and os.path.exists(c): return c
    return None


def ocr_words(im, scale=3):
    """Words with boxes. Runs on the normal and the inverted image, so white text on blue
    (buttons, grid headers, title bars) is read too."""
    exe = tesseract_exe()
    if not exe: raise RuntimeError('Tesseract OCR is not installed - use find --crop, snap or grid instead (see README).')
    g = im.convert('L').resize((im.width * scale, im.height * scale), Image.LANCZOS)
    a = np.array(g); bgm = cv2.medianBlur(a, 31)
    ink = np.where(np.abs(a.astype(int) - bgm.astype(int)) > 45, 0, 255).astype(np.uint8)  # any polarity -> black on white
    words = []
    for k, img in enumerate((g, Image.fromarray(ink))):
        tmp = Path(os.environ.get('TEMP', '/tmp')) / ('ilis_ocr_%d.png' % k); img.save(tmp)
        out = subprocess.run([exe, str(tmp), 'stdout', '--psm', '11', 'tsv'], capture_output=True, text=True, encoding='utf-8').stdout
        for line in out.splitlines()[1:]:
            p = line.split('\t')
            if len(p) == 12 and p[11].strip() and float(p[10]) > 30:
                x, y, w, h = [int(v) / scale for v in p[6:10]]
                bx = [int(x), int(y), int(x + w), int(y + h)]
                if not any(abs(bx[0] - o['box'][0]) < 4 and abs(bx[1] - o['box'][1]) < 4 and o['text'] == p[11] for o in words):
                    words.append({'text': p[11], 'box': bx, 'conf': float(p[10])})
    words.sort(key=lambda w: (round(w['box'][1] / 8), w['box'][0]))
    return words


def _sim(a, b):
    import difflib
    a = a.lower().strip('.,:;"\'()[]'); b = b.lower().strip('.,:;"\'()[]')
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_text(im, phrase, region=None):
    """Boxes of a word or phrase found by OCR (best matches first)."""
    sub = im.crop(region) if region else im
    ox, oy = (region[0], region[1]) if region else (0, 0)
    words = ocr_words(sub)
    target = phrase.split(); hits = []
    for i, w0 in enumerate(words):
        seq = [w0]
        for w in words[i + 1:]:
            if len(seq) == len(target): break
            if abs(w['box'][1] - seq[-1]['box'][1]) < 6 and 0 <= w['box'][0] - seq[-1]['box'][2] < 25: seq.append(w)
        if len(seq) != len(target): continue
        score = sum(_sim(t, s['text']) for t, s in zip(target, seq)) / len(target)
        if score >= 0.8:
            b = [min(s['box'][0] for s in seq), min(s['box'][1] for s in seq), max(s['box'][2] for s in seq), max(s['box'][3] for s in seq)]
            hits.append((score, [b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy]))
    hits.sort(key=lambda h: -h[0])
    return [h[1] for h in hits]


def find_crop(im, crop, thresh=0.9):
    a = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR); t = cv2.cvtColor(np.array(load(crop) if isinstance(crop, (str, Path)) else crop), cv2.COLOR_RGB2BGR)
    res = cv2.matchTemplate(a, t, cv2.TM_CCOEFF_NORMED)
    hits = []
    while True:
        _, mx, _, (x, y) = cv2.minMaxLoc(res)
        if mx < thresh or len(hits) > 20: break
        hits.append({'box': [x, y, x + t.shape[1] - 1, y + t.shape[0] - 1], 'score': round(float(mx), 3)})
        res[max(0, y - t.shape[0] // 2):y + t.shape[0] // 2 + 1, max(0, x - t.shape[1] // 2):x + t.shape[1] // 2 + 1] = -1
    return hits


def snap(im, box, grow=12):
    """Refine a rough box to the UI element under it (button, field, menu item) and pad by 3px."""
    x0, y0, x1, y1 = box; W, H = im.size
    X0, Y0, X1, Y1 = max(0, x0 - grow), max(0, y0 - grow), min(W, x1 + grow), min(H, y1 + grow)
    a = np.array(im.crop((X0, Y0, X1, Y1)).convert('RGB')).astype(int)
    bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    m = (np.abs(a - bg).sum(2) > 45).astype(np.uint8)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    rb = [x0 - X0, y0 - Y0, x1 - X0, y1 - Y0]; pick = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        ix = max(0, min(x + w, rb[2]) - max(x, rb[0])) * max(0, min(y + h, rb[3]) - max(y, rb[1]))
        if ix > 0.5 * w * h or ix > 0.5 * (rb[2] - rb[0]) * (rb[3] - rb[1]): pick.append((x, y, x + w - 1, y + h - 1))
    if not pick: return box
    bx = [min(p[0] for p in pick), min(p[1] for p in pick), max(p[2] for p in pick), max(p[3] for p in pick)]
    return [int(max(0, bx[0] + X0 - 3)), int(max(0, bx[1] + Y0 - 3)), int(min(W - 1, bx[2] + X0 + 3)), int(min(H - 1, bx[3] + Y0 + 3))]


def button_box(im, text_box, tol=40, max_w=420, max_h=70):
    """Whole button/menu item around a text box: flood the background colour of the text area."""
    x0, y0, x1, y1 = text_box
    a = np.array(im).astype(int); H, W = a.shape[:2]
    reg = a[y0:y1 + 1, x0:x1 + 1].reshape(-1, 3)
    vals, cnt = np.unique(reg, axis=0, return_counts=True); bg = vals[np.argmax(cnt)]
    m = (np.abs(a - bg).sum(2) < tol).astype(np.uint8)
    m[y0:y1 + 1, x0:x1 + 1] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    i = lab[(y0 + y1) // 2, (x0 + x1) // 2]
    x, y, w, h, _ = st[i]
    if i == 0 or w > max_w or h > max_h:
        return [x0 - 4, y0 - 4, x1 + 4, y1 + 4]
    return [int(x) - 1, int(y) - 1, int(x + w), int(y + h)]


def grid(im, step=50):
    g = im.copy(); d = ImageDraw.Draw(g); f = _font(11)
    for x in range(0, im.width, step):
        d.line([(x, 0), (x, im.height)], fill=(0, 160, 255) if x % 100 else (255, 0, 255), width=1)
        if x % 100 == 0: d.text((x + 2, 2), str(x), fill=(255, 0, 255), font=f)
    for y in range(0, im.height, step):
        d.line([(0, y), (im.width, y)], fill=(0, 160, 255) if y % 100 else (255, 0, 255), width=1)
        if y % 100 == 0: d.text((2, y + 2), str(y), fill=(255, 0, 255), font=f)
    return g


# ---------------------------------------------------------------- composition blocks
def dim(im, f=DIM):
    return Image.fromarray(np.clip(np.array(im).astype(np.float32) * f, 0, 255).astype(np.uint8))


def undim(im, f=DIM):
    return Image.fromarray(np.clip(np.array(im).astype(np.float32) / f, 0, 255).astype(np.uint8))


def align(donor, target, region=None):
    """Offset (dx,dy) so that donor pixel (x,y) corresponds to target (x+dx, y+dy). Uses the donor area
    outside `region` (e.g. a pop-up) - the top band of the screen (tabs/header) by default."""
    D = np.array(donor).astype(np.float32); T = np.array(target).astype(np.float32)
    h, w = D.shape[:2]
    y0 = 40; y1 = max(y0 + 40, min(h // 3, (region[1] - 5) if region and region[1] > 100 else h // 3))
    x0 = int(w * 0.1)
    patch = D[y0:y1, x0:int(w * 0.6)]
    best = None
    for scale in (1.0, DIM, 1 / DIM):
        p = np.clip(patch * scale, 0, 255)
        if p.shape[0] > T.shape[0] or p.shape[1] > T.shape[1]: continue
        res = cv2.matchTemplate(T, p, cv2.TM_SQDIFF_NORMED); mn, _, loc, _ = cv2.minMaxLoc(res)
        if best is None or mn < best[0]: best = (mn, loc[0] - x0, loc[1] - y0)
    return best[1], best[2], best[0]


def overlay_box(donor, margin=1):
    """Bounding box of the pop-up / alert in a dimmed screenshot. A dimmed screen never has a channel
    above ~145, so any brighter pixel belongs to the pop-up (white body, blue title bar, buttons)."""
    a = np.array(donor).astype(int)
    m = (a.max(2) > 160).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: raise RuntimeError('no pop-up found in donor (is it a dimmed screenshot?)')
    i = 1 + int(np.argmax(st[1:, 4])); x, y, w, h, _ = st[i]
    H, W = m.shape
    return [max(0, int(x) - margin), max(0, int(y) - margin), min(W - 1, int(x + w - 1) + margin), min(H - 1, int(y + h - 1) + margin)]


def color_box(im, color, tol=40, min_area=400):
    """Largest region of a colour (e.g. the green success bar)."""
    a = np.array(im).astype(int); c = np.array(color)
    m = (np.abs(a - c).sum(2) < tol).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: return None
    i = 1 + int(np.argmax(st[1:, 4]))
    x, y, w, h, area = st[i]
    return [int(x), int(y), int(x + w - 1), int(y + h - 1)] if area >= min_area else None


def paste_region(target, donor, region, dx, dy):
    x0, y0, x1, y1 = region
    piece = donor.crop((x0, y0, x1 + 1, y1 + 1)); target = target.copy(); target.paste(piece, (x0 + dx, y0 + dy))
    return target


def bg_color(im, box):
    a = np.array(im.crop((box[0], box[1], box[2] + 1, box[3] + 1))).reshape(-1, 3)
    vals, counts = np.unique(a, axis=0, return_counts=True)
    return tuple(int(v) for v in vals[np.argmax(counts)])


def erase(im, box, color=None):
    im = im.copy(); c = color or bg_color(im, box)
    ImageDraw.Draw(im).rectangle(box, fill=tuple(c)); return im


def ink_bbox(im, box, thr=60):
    x0, y0, x1, y1 = box
    a = np.array(im.crop((x0, y0, x1 + 1, y1 + 1))).astype(int)
    bg = np.array(bg_color(im, box))
    m = np.abs(a - bg).sum(2) > thr
    ys, xs = np.where(m)
    if len(xs) == 0: return None
    return [x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()), y0 + int(ys.max())]


def text_lines(im, box, thr=40, gap=25):
    """Text blocks inside box, top to bottom: [x0,y0,x1,y1]. Frame lines and borders are ignored;
    blocks on the same row separated by more than `gap` px are returned separately."""
    x0, y0, x1, y1 = box
    g = np.array(im.crop((x0, y0, x1 + 1, y1 + 1)).convert('L'))
    bgm = cv2.medianBlur(g, 15)
    ink = (np.abs(g.astype(int) - bgm.astype(int)) > thr).astype(np.uint8)
    H, W = ink.shape
    e = min(8, W // 10)
    ink[:, :e] = 0; ink[:, W - e:] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink)
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if (w > 40 and h <= 3) or (h > 25 and w <= 3) or (w > 0.6 * W) or (h > 30):
            ink[lab == i] = 0
    # icons next to text (check marks, gear icons): blobs clearly taller than the letters around them
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink)
    hs = [st[i][3] for i in range(1, n) if st[i][4] > 3]
    if hs:
        mh = float(np.median(hs))
        hsv = cv2.cvtColor(np.array(im.crop((x0, y0, x1 + 1, y1 + 1)).convert('RGB')), cv2.COLOR_RGB2HSV)
        for i in range(1, n):
            x, y, w, h, area = st[i]
            if w < 0.8 * h or area < 0.35 * w * h: continue
            sat = hsv[..., 1][lab == i].mean()
            if (h > 1.4 * mh and sat > 90) or h > 1.8 * mh: ink[lab == i] = 0
    rows = ink.any(1); out = []; y = 0
    while y < H:
        if rows[y]:
            s0 = y
            while y < H and rows[y]: y += 1
            band = ink[s0:y]; xs = np.where(band.any(0))[0]
            if len(xs) and y - s0 >= 4:
                start = xs[0]; prev = xs[0]
                for xx in list(xs[1:]) + [None]:
                    if xx is None or xx - prev > gap:
                        sub = band[:, start:prev + 1]; r = np.where(sub.any(1))[0]
                        if prev - start >= 3:
                            out.append([x0 + int(start), y0 + s0 + int(r.min()), x0 + int(prev), y0 + s0 + int(r.max())])
                        if xx is not None: start = xx
                    if xx is not None: prev = xx
        y += 1
    return out


# ---------------------------------------------------------------- preview
def preview(files, out, labels=None, maxw=1400):
    ims = [load(f) for f in files]
    f = _font(15); pad = 34
    scale = [min(1.0, maxw / i.width) for i in ims]
    W = maxw if any(i.width >= maxw for i in ims) else max(i.width for i in ims)
    H = sum(int(i.height * s) + pad + 10 for i, s in zip(ims, scale))
    can = Image.new('RGB', (W, H), (235, 235, 235)); d = ImageDraw.Draw(can); y = 0
    for k, (i, s) in enumerate(zip(ims, scale)):
        lab = (labels[k] if labels and k < len(labels) else Path(files[k]).name)
        d.text((8, y + 8), lab, fill=(0, 0, 0), font=f); y += pad
        can.paste(i.resize((int(i.width * s), int(i.height * s)), Image.LANCZOS), (0, y)); y += int(i.height * s) + 10
    save(can, out)
    return out


def open_in_editor(path):
    exe = shutil.which('code') or shutil.which('code.cmd')
    if exe:
        try: subprocess.Popen([exe, '-r', str(path)]); return True
        except OSError: pass
    return False
