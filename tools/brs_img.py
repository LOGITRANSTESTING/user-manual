"""BRS image tools: unmarked UI-design images for the BRS, and rebuilding parts of a screen from
neighbouring screenshots of the same screen.

  unmark  SRC DST [--donors F ...] [--donor-dir D] [--inline F ...] [--blue] [--keep-border]
          Remove the blue frame (any style), red boxes, numbered circles, stubs, cut-off box segments and
          drawn blue boxes the user confirmed (--blue-box; --blue only lists candidates), then repair
          every covered spot seamlessly. The app's own elements are never removed (guarded):
            1 similar element copied whole (same screen / neighbours / step crops) - exact fit only
            1b element rebuild from the most similar same-style element (layout-aware edges)
            2 inline step crops (small images in --donor-dir / --inline) - only where they fit exactly
            3 neighbour screenshots, then the same screen elsewhere - only exact agreement
            4 row/column continuation - only where provably plain
          Prints a JSON report; "seamless": true only when nothing is left unresolved. Writes DST_check.png.
  fill    SRC DST --box x0,y0,x1,y1 [--donors F ...] [--donor-dir D] [--min 0.90] [--no-fallback]
          Edit something out of a screen (a value, a pop-up, a highlight, a mark that left a smudge)
          by copying the same area from a neighbouring screenshot where it is clean. Falls back to
          row/column continuation when no neighbour matches (prints FALLBACK - show it to the user).
  rank    SRC [--donors F ...] [--donor-dir D]
          Rank neighbour screenshots by how much of the same screen they show.
  remove-rows SRC DST --box x0,y0,x1,y1 --until Y
          Delete grid rows (band y0..y1 inside x0..x1): rows below, down to Y (bottom of the grid body),
          move up; the freed band is rebuilt as empty grid.
  copy    SRC DST --from-box x0,y0,x1,y1 --to x,y [--donor D]
          Deterministic copy of a known-good element (e.g. the left end of the Cancel button onto the
          smudged left end of Submit, or a field edge from the field below). No --donor = same screen.
          --flip h|v|hv mirrors the piece; --recolor FROM:TO[,..] swaps exact colours in it. Both make
          a piece that is no longer a plain copy, so they only write DST_proposal.png (before | after)
          until the user approves that piece; then re-run with --approved. They need --marks MARKED.png
          (the original marked screenshot) and are placed ONLY inside its marked area.
  sheet   FILES ... --out sheet.png [--labels "Image I,Image II"]

How neighbour filling works (same screen, different moment):
  1. Context: a ring of pixels around the box (default 24 px) is taken from SRC. The box itself is
     masked out, so whatever is inside (the thing to remove) does not influence the match.
  2. Search: the ring is matched (masked normalised cross-correlation) over every donor, at the same
     scale and at the pop-up dimming scale (0.549), so dimmed and undimmed shots can feed each other.
  3. Accept: the best donor/location with score >= --min AND ring difference < 1.5% wins. Its pixels inside the box are copied in
     (re-dimmed/undimmed to SRC's brightness when needed).
  4. Verify: the seam (2 px inside the box edge) is compared with SRC's ring; a hard seam is reported.
  5. Fallback: no donor good enough -> each masked pixel continues the nearest straight row/column
     (backgrounds, grid lines, panel edges), which is right for empty areas and wrong for text.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ilis_img as I  # house toolkit: load/save, strip_border, clear_marks, axis_fill, red_mask, find_circles, spot_sheet, preview

DIM = I.DIM
IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp'}


# ------------------------------------------------------------------ donors
def is_inline(im):
    return im.width < 400 and im.height < 120


def donor_list(a, want='screens'):
    """screens: full screenshots (frame stripped, marks cleared); inline: the manual's small step crops
    (buttons, check boxes, icons), used as they are - they are cut from unmarked screenshots."""
    files = list(a.donors or []) + list(getattr(a, 'inline', None) or [])
    if getattr(a, 'donor_dir', None):
        files += sorted(str(p) for p in Path(a.donor_dir).rglob('*') if p.suffix.lower() in IMG_EXT)
    src = str(Path(a.src).resolve())
    screens, inline, seen = [], [], set()
    for f in files:
        rp = str(Path(f).resolve())
        if rp == src or rp in seen or f.endswith('_check.png'): continue
        seen.add(rp); im = I.load(f)
        if is_inline(im):
            if im.width >= 12 and im.height >= 12: inline.append((f, im))
            continue
        im, _ = strip_frame(im)
        if I.red_mask(np.array(im)).sum() > 50:
            im, _ = I.clear_marks(im, unborder=False)
        screens.append((f, im))
    return (screens, inline) if want == 'both' else screens


def similarity(a, b, size=(320, 200)):
    ga = cv2.resize(np.array(a.convert('L')), size, interpolation=cv2.INTER_AREA).astype(np.float32)
    gb = cv2.resize(np.array(b.convert('L')), size, interpolation=cv2.INTER_AREA).astype(np.float32)
    ea, eb = cv2.Canny(ga.astype(np.uint8), 50, 150), cv2.Canny(gb.astype(np.uint8), 50, 150)
    inter = np.logical_and(cv2.dilate(ea, np.ones((3, 3))) > 0, eb > 0).sum()
    return float(inter / max(1, (eb > 0).sum()))


# ------------------------------------------------------------------ neighbour fill
def match_ring(src_a, donor_a, box, ctx, exclude=False):
    x0, y0, x1, y1 = box; H, W = src_a.shape[:2]
    X0, Y0, X1, Y1 = max(x0 - ctx, 0), max(y0 - ctx, 0), min(x1 + 1 + ctx, W), min(y1 + 1 + ctx, H)
    tpl = src_a[Y0:Y1, X0:X1].astype(np.float32)
    m = np.ones(tpl.shape[:2], np.uint8) * 255
    m[y0 - Y0:y1 + 1 - Y0, x0 - X0:x1 + 1 - X0] = 0
    best = (-1, None, None, 1.0)
    for scale in (1.0, DIM, 1 / DIM):
        d = np.clip(donor_a.astype(np.float32) * scale, 0, 255)
        if d.shape[0] < tpl.shape[0] or d.shape[1] < tpl.shape[1]: continue
        res = np.nan_to_num(cv2.matchTemplate(d, tpl, cv2.TM_CCORR_NORMED, mask=np.dstack([m] * 3)))
        if exclude:  # same image: never match the spot itself (or a shift that overlaps it)
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            res[max(0, Y0 - bh):Y0 + bh + 1, max(0, X0 - bw):X0 + bw + 1] = -1
            if scale != 1.0: continue
        _, sc, _, loc = cv2.minMaxLoc(res)
        # CCORR_NORMED is generous on flat areas: confirm with mean abs difference on the ring
        bx, by = loc
        cand = d[by:by + tpl.shape[0], bx:bx + tpl.shape[1]]
        diff = np.abs(cand - tpl)[m > 0].mean() / 255.0
        score = sc * (1 - diff)
        if score > best[0]: best = (score, (bx, by), scale, diff)
    if best[1] is None: return None
    bx, by = best[1]
    return {'score': float(best[0]), 'x': bx + (x0 - X0), 'y': by + (y0 - Y0), 'scale': best[2], 'ring_diff': float(best[3])}


def fill_from_neighbours(src, donors, box, min_score=0.90, ctx=24, fallback=True, self_donor=False, max_ring_diff=0.015):
    a = np.array(src).copy(); x0, y0, x1, y1 = box
    results = []
    for name, d in donors:
        r = match_ring(a, np.array(d), box, ctx)
        if r: r['donor'] = name; results.append((r, d))
    if self_donor:  # a matching element elsewhere on the same screen (another field/button edge, grid row)
        r = match_ring(a, a, box, ctx, exclude=True)
        if r: r['donor'] = 'SELF (same screen)'; results.append((r, src))
    results.sort(key=lambda t: -t[0]['score'])
    if results and results[0][0]['score'] >= min_score and results[0][0]['ring_diff'] < max_ring_diff:
        r, d = results[0]
        piece = np.array(d).astype(np.float32)[r['y']:r['y'] + (y1 - y0 + 1), r['x']:r['x'] + (x1 - x0 + 1)] * r['scale']
        a[y0:y1 + 1, x0:x1 + 1] = np.clip(piece, 0, 255).astype(np.uint8)
        seam = seam_error(np.array(src), a, box)
        return Image.fromarray(a), dict(r, method='neighbour', seam=seam, tried=[t[0]['donor'] + ' %.3f' % t[0]['score'] for t in results])
    info = {'method': 'none', 'tried': [t[0]['donor'] + ' %.3f' % t[0]['score'] for t in results]}
    if fallback:
        mask = np.zeros(a.shape[:2], np.uint8); mask[y0:y1 + 1, x0:x1 + 1] = 1
        a = I.axis_fill(a, mask); info['method'] = 'FALLBACK row/column continuation'
    return Image.fromarray(a), info


def seam_error(orig, new, box):
    x0, y0, x1, y1 = box; H, W = orig.shape[:2]
    errs = []
    if y0 > 0: errs.append(np.abs(new[y0, x0:x1 + 1].astype(int) - orig[y0 - 1, x0:x1 + 1].astype(int)).mean())
    if y1 < H - 1: errs.append(np.abs(new[y1, x0:x1 + 1].astype(int) - orig[y1 + 1, x0:x1 + 1].astype(int)).mean())
    if x0 > 0: errs.append(np.abs(new[y0:y1 + 1, x0].astype(int) - orig[y0:y1 + 1, x0 - 1].astype(int)).mean())
    if x1 < W - 1: errs.append(np.abs(new[y0:y1 + 1, x1].astype(int) - orig[y0:y1 + 1, x1 + 1].astype(int)).mean())
    return round(float(max(errs) if errs else 0), 1)


# ------------------------------------------------------------------ blue boxes
def blue_box_mask(a):
    """Thin drawn blue rectangles (annotation boxes), not the app's solid blue bars/buttons."""
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    blue = ((b > 150) & (r < 90) & (g < 170) & (b - r > 90)).astype(np.uint8)
    solid = cv2.morphologyEx(blue, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))  # filled areas
    solid = cv2.dilate(solid, np.ones((5, 5), np.uint8))
    thin = blue & (1 - solid)
    hor = cv2.morphologyEx(thin, cv2.MORPH_OPEN, np.ones((1, 30), np.uint8))
    ver = cv2.morphologyEx(thin, cv2.MORPH_OPEN, np.ones((30, 1), np.uint8))
    mask = hor | ver
    # keep only components that look like rectangle outlines (both directions present)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(mask, np.ones((3, 3), np.uint8)))
    keep = np.zeros_like(mask)
    for i in range(1, n):
        x, y, w, h, area = st[i]
        comp = lab == i
        if w >= 20 and h >= 12 and (hor[comp].any() and ver[comp].any()): keep[comp] = 1
    return cv2.dilate(keep & (mask | thin), np.ones((3, 3), np.uint8))


def spots_from_mask(mask, pad=4, max_side=60):
    """Small patches along the removed marks, for neighbour repair."""
    spots = []
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    for i in range(1, n):
        x, y, w, h, _ = st[i]
        for yy in range(y, y + h, max_side):
            for xx in range(x, x + w, max_side):
                sub = (lab[yy:yy + max_side, xx:xx + max_side] == i)
                if not sub.any(): continue
                ys, xs = np.where(sub)
                spots.append([int(xx + xs.min() - pad), int(yy + ys.min() - pad), int(xx + xs.max() + pad), int(yy + ys.max() + pad)])
    return spots


def strip_frame(im, search=40, max_pad=16):
    """Remove the manual's blue frame whatever its style: house 21/17 px border, or the older
    shadow + thin blue line + inner shadow. Each side is cropped just inside the frame."""
    im2, b = I.strip_border(im)
    if b: return im2, b
    a = np.array(im).astype(int); H, W = a.shape[:2]
    def isblue(px): return (px[..., 2] > 140) & (px[..., 0] < 80) & (px[..., 2] - px[..., 0] > 90)
    cuts = []
    for side in ('top', 'bottom', 'left', 'right'):
        lines = []
        for k in range(min(search, H // 4 if side in ('top', 'bottom') else W // 4)):
            if side == 'top': px = a[k, W // 4:3 * W // 4]
            elif side == 'bottom': px = a[H - 1 - k, W // 4:3 * W // 4]
            elif side == 'left': px = a[H // 4:3 * H // 4, k]
            else: px = a[H // 4:3 * H // 4, W - 1 - k]
            if isblue(px).mean() > 0.6: lines.append(k)
        if not lines: cuts.append(0); continue
        j = max(lines) + 1
        while j < max(lines) + 1 + max_pad:
            if side == 'top': px = a[j, W // 4:3 * W // 4]
            elif side == 'bottom': px = a[H - 1 - j, W // 4:3 * W // 4]
            elif side == 'left': px = a[H // 4:3 * H // 4, j]
            else: px = a[H // 4:3 * H // 4, W - 1 - j]
            if px.mean() >= 252.5: break
            j += 1
        cuts.append(j)
    t, bt, l, r = cuts
    if not all(cuts): return im, 0   # a frame is a closed rectangle; a blue line on one side is the app's
    return im.crop((l, t, W - r, H - bt)), max(cuts)


# ------------------------------------------------------------------ seamless repair
def known_agree(target, piece, known, tol_mean=2.5, tol_p99=24):
    """piece fits if it agrees with every undamaged target pixel it covers."""
    k = known > 0
    if k.sum() < max(150, 0.12 * known.size): return False, 999.0
    if target[k].astype(float).std() < 10: return False, 999.0   # nothing distinctive to match on
    d = np.abs(target.astype(int) - piece.astype(int)).max(2)[k]
    return bool(d.mean() <= tol_mean and np.percentile(d, 99) <= tol_p99), float(d.mean())


def masked_sqdiff(target, known, tpl):
    """Mean squared difference of tpl against target at every position, counting only known target
    pixels (exact, via correlations): sum K(T-C)^2 = sum K T^2 - 2 sum (K T) C + sum K C^2."""
    T = target.astype(np.float32); C = tpl.astype(np.float32); K = known.astype(np.float32)
    ones = np.ones(C.shape[:2], np.float32); tot = 0
    for ch in range(3):
        t, c_ = T[..., ch], C[..., ch]
        tot = tot + cv2.matchTemplate(K * t * t, ones, cv2.TM_CCORR) - 2 * cv2.matchTemplate(K * t, c_, cv2.TM_CCORR) \
            + cv2.matchTemplate(K, c_ * c_, cv2.TM_CCORR)
    n = cv2.matchTemplate(K, ones, cv2.TM_CCORR)
    return tot / np.maximum(n, 1) / 3, n / ones.size


def fit_inline(a, damage, crops):
    """Place a step crop (e.g. the Submit button) over the damaged spot only where it fits perfectly:
    it must match every undamaged pixel it covers. Only damaged pixels are taken from it."""
    ys, xs = np.where(damage > 0)
    if not len(ys): return a, None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max(); H, W = damage.shape
    best = None
    for name, im in crops:
        c = np.array(im); ch, cw = c.shape[:2]
        X0, Y0 = max(0, x0 - cw + 1), max(0, y0 - ch + 1)
        X1, Y1 = min(W - cw, x1), min(H - ch, y1)
        if X1 < X0 or Y1 < Y0: continue
        reg = a[Y0:Y1 + ch, X0:X1 + cw]; kn = 1 - damage[Y0:Y1 + ch, X0:X1 + cw]
        err, frac = masked_sqdiff(reg, kn, c)
        err[frac < 0.12] = 1e9
        for idx in np.argsort(err, axis=None)[:5]:
            ry, rx = np.unravel_index(idx, err.shape); x, y = X0 + rx, Y0 + ry
            dmg = damage[y:y + ch, x:x + cw]
            if not dmg.any(): continue
            ok, e = known_agree(a[y:y + ch, x:x + cw], c, 1 - dmg)
            if ok and (best is None or e < best[0]): best = (e, name, x, y, c)
    if not best: return a, None
    err, name, x, y, c = best; ch, cw = c.shape[:2]
    a = a.copy(); dmg = damage[y:y + ch, x:x + cw] > 0
    a[y:y + ch, x:x + cw][dmg] = c[dmg]
    covered = np.zeros_like(damage); covered[y:y + ch, x:x + cw] = dmg
    return a, {'method': 'inline crop', 'donor': name, 'at': [int(x), int(y)], 'err': round(err, 2), 'covered': covered}


def fit_screen(a, damage, box, screens, ctx, min_score, self_img=None):
    """Neighbour screenshot (or same screen elsewhere): locate the box by its surrounding ring,
    then accept only if the donor also agrees with every undamaged pixel inside the box."""
    x0, y0, x1, y1 = box
    cands = list(screens) + ([('SELF (same screen)', self_img)] if self_img is not None else [])
    tried = []
    for name, d in cands:
        da = np.array(d)
        r = match_ring(a, da, box, ctx, exclude=(name.startswith('SELF')))
        if not r or r['score'] < min_score: tried.append('%s %.3f' % (name, r['score'] if r else 0)); continue
        piece = np.clip(da.astype(np.float32)[r['y']:r['y'] + (y1 - y0 + 1), r['x']:r['x'] + (x1 - x0 + 1)] * r['scale'], 0, 255).astype(np.uint8)
        if piece.shape[:2] != (y1 - y0 + 1, x1 - x0 + 1): continue
        dmg = damage[y0:y1 + 1, x0:x1 + 1]
        ok, err = known_agree(a[y0:y1 + 1, x0:x1 + 1], piece, 1 - dmg)
        tried.append('%s %.3f err %.1f' % (name, r['score'], err))
        if ok:
            out = a.copy(); out[y0:y1 + 1, x0:x1 + 1][dmg > 0] = piece[dmg > 0]
            return out, {'method': 'neighbour', 'donor': name, 'score': round(r['score'], 3), 'err': round(err, 2)}
    return a, {'method': None, 'tried': tried}


# ------------------------------------------------------------------ element rebuild (same-style reference)
def _local_bg(a, box):
    x0, y0, x1, y1 = box; H, W = a.shape[:2]
    ring = np.concatenate([a[max(0, y0 - 6):y0, x0:x1 + 1].reshape(-1, 3), a[y1 + 1:min(H, y1 + 7), x0:x1 + 1].reshape(-1, 3),
                           a[y0:y1 + 1, max(0, x0 - 6):x0].reshape(-1, 3), a[y0:y1 + 1, x1 + 1:min(W, x1 + 7)].reshape(-1, 3)])
    if not len(ring): return np.array([255, 255, 255])
    v, n = np.unique(ring, axis=0, return_counts=True); return v[np.argmax(n)].astype(int)


def _elements(a, bg, near=None, min_h=14, max_h=70, min_w=18):
    """Rounded rectangles of the UI (buttons, input boxes, drop downs): connected non-background areas."""
    m = (np.abs(a.astype(int) - bg).max(2) > 22).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    filled = m.copy(); cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for cn in cnts:
        x, y, w, h = cv2.boundingRect(cn)
        if min_h <= h <= max_h and w >= min_w and w <= 900:
            if near is not None and not near[y:y + h, x:x + w].any(): continue
            out.append([x, y, x + w - 1, y + h - 1])
    return out


def _signature(a, b):
    x0, y0, x1, y1 = b; e = a[y0:y1 + 1, x0:x1 + 1].astype(int)
    border = np.concatenate([e[0], e[-1], e[:, 0], e[:, -1]]); inner = e[2:-2, 2:-2].reshape(-1, 3)
    v, n = np.unique(inner, axis=0, return_counts=True) if len(inner) else (np.array([[0, 0, 0]]), [1])
    return np.median(border, 0), v[int(np.argmax(n))]


def _synth(ref, h, w):
    """Draw an element of size h x w in the reference's style: its two end caps (only the rounded
    corner/border columns, never its text) + its plainest middle column."""
    rh, rw = ref.shape[:2]
    if abs(rh - h) > 1 or rw < 8: return None
    if rh != h: ref = cv2.resize(ref, (rw, h), interpolation=cv2.INTER_NEAREST)
    r = ref.astype(int)
    mid = min(range(rw // 4, 3 * rw // 4 + 1), key=lambda j: len(np.unique(ref[:, j], axis=0)))
    plain = r[:, mid]
    def cap(cols):
        k = 0
        for j in cols:
            if np.abs(r[:, j] - plain).max() <= 12: break
            k += 1
        return k
    kl = cap(range(rw)); kr = cap(range(rw - 1, -1, -1))
    if kl > rw // 3 or kr > rw // 3 or kl + kr >= w: return None
    S = np.repeat(ref[:, mid:mid + 1], w, axis=1).copy()
    if kl: S[:, :kl] = ref[:, :kl]
    if kr: S[:, w - kr:] = ref[:, rw - kr:]
    return S, max(kl, kr, 2)


def _edge(a, damage, bg, start, step, axis, fixed, lo, hi, limit=400):
    """Walk outwards from inside an element along one row/column. The edge is the last non-background
    pixel before 2 background pixels, after at least one non-background pixel (fill or border) was seen.
    Returns None when the walk runs into damage first (edge hidden under a mark)."""
    p = start; run = 0; seen = False; last = None; n = 0
    while lo <= p <= hi and n < limit:
        y, x = (fixed, p) if axis == 'x' else (p, fixed)
        if damage[y, x]: return last if (seen and run >= 1) else None
        isbg = np.abs(a[y, x].astype(int) - bg).max() <= 22
        if not isbg: seen = True; last = p; run = 0
        elif seen:
            run += 1
            if run == 2: return last
        p += step; n += 1
    return None


def _content_span(a, damage, fsig, y, x0, x1):
    """First/last text-or-icon pixel on a button's middle row. Each end must be followed (outwards) by
    3 clean fill pixels, so we know the content really ends there and is not cut by a mark."""
    isfill = lambda x: (not damage[y, x]) and np.abs(a[y, x].astype(int) - fsig).max() <= 40
    xs = [x for x in range(x0, x1 + 1) if not damage[y, x] and not isfill(x)]
    if not xs: return None
    s_, e_ = xs[0], xs[-1]
    if not all(isfill(x) for x in range(e_ + 1, min(x1, e_ + 3) + 1)): return None
    if not all(isfill(x) for x in range(max(x0, s_ - 3), s_)): return None
    return s_, e_


import os
def _dbg(i, b):
    if os.environ.get('BRS_DEBUG'): print('element', b, 'skipped at line', i, file=sys.stderr)


def element_library(sources, exclude=None, max_n=400):
    """Every button / input box / drop-down / check box found on the given screenshots, cut out with a
    2 px margin. Used as whole-element donors: a damaged element is replaced only by an element that
    matches every pixel the mark left visible (same size, border, fill, text and icons)."""
    lib, seen = [], set()
    for name, im in sources:
        a = np.array(im); H, W = a.shape[:2]
        bg = _local_bg(a, [0, 0, W - 1, H - 1])
        for b in _elements(a, bg, min_h=10, max_h=80, min_w=10):
            if exclude is not None and exclude[b[1]:b[3] + 1, b[0]:b[2] + 1].any(): continue
            x0, y0, x1, y1 = max(0, b[0] - 2), max(0, b[1] - 2), min(W - 1, b[2] + 2), min(H - 1, b[3] + 2)
            crop = a[y0:y1 + 1, x0:x1 + 1]
            key = hashlib.sha1(crop.tobytes()).hexdigest()
            if key in seen: continue
            seen.add(key); lib.append(('%s @%d,%d' % (name, x0, y0), Image.fromarray(crop)))
            if len(lib) >= max_n: return lib
    return lib


def rebuild_elements(c, damage):
    """Buttons / input boxes / drop downs hit by a mark are redrawn from an undamaged element of the same
    style on the same screen (e.g. Submit from Cancel, the Container box from Tare Weight).
    Hidden edges come from layout: elements in the same row share top/bottom, elements in the same
    column share left/right. Every pixel the mark did not touch is kept from the screenshot itself."""
    a = c.copy(); H, W = damage.shape; done = []
    near = cv2.dilate(damage, np.ones((7, 7), np.uint8))
    ys, xs = np.where(damage > 0)
    if not len(ys): return a, done, np.zeros_like(damage)
    bg = _local_bg(a, [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
    hit = _elements(a, bg, near)
    refs = [b for b in _elements(a, bg) if not near[b[1]:b[3] + 1, b[0]:b[2] + 1].any()]
    covered = np.zeros_like(damage)
    for b in hit:
        bx0, by0, bx1, by1 = b
        _, fsig = _signature(a, b)
        filled = np.abs(fsig - bg).max() > 22
        cand = [r for r in refs if np.abs(_signature(a, r)[1] - fsig).max() < 30]
        if not cand: _dbg(0, b); continue
        nonbg = lambda px: np.abs(px.astype(int) - bg).max(-1) > 22

        def row_edge_ok(y, x0_, x1_):   # a real top/bottom edge: undamaged and drawn along most of it
            xs_ = slice(x0_ + (x1_ - x0_) // 4, x1_ - (x1_ - x0_) // 4 + 1)
            dm = damage[y, xs_] > 0
            return dm.mean() < 0.2 and nonbg(a[y, xs_][~dm]).mean() > 0.7

        def col_edge_ok(x, y0_, y1_, step):  # a real side: drawn down most of it, background outside
            ys_ = slice(y0_ + 3, y1_ - 2)
            dm = damage[ys_, x] > 0
            if dm.mean() > 0.2 or nonbg(a[ys_, x][~dm]).mean() < 0.7: return False
            checked = 0
            for k_ in (1, 2, 3):
                x_ = x + step * k_
                if not (0 <= x_ < W): break
                d2 = damage[ys_, x_] > 0
                if d2.mean() > 0.4: continue
                if nonbg(a[ys_, x_][~d2]).any(): return False
                checked += 1
            return checked >= 1

        T = by0 if row_edge_ok(by0, bx0, bx1) else None
        Bm = by1 if row_edge_ok(by1, bx0, bx1) else None
        cy = (by0 + by1) // 2
        if T is None or Bm is None:  # same row of the screen: share top and bottom
            rowref = [r for r in cand if abs((r[1] + r[3]) / 2 - cy) <= 4 and (T is None or abs(r[1] - T) <= 1) and (Bm is None or abs(r[3] - Bm) <= 1)]
            if not rowref: _dbg(1, b); continue
            T, Bm = rowref[0][1], rowref[0][3]
        h = Bm - T + 1
        same_h = [r for r in cand if abs((r[3] - r[1] + 1) - h) <= 1]
        if not same_h: _dbg(2, b); continue
        L = bx0 if col_edge_ok(bx0, T, Bm, -1) else None
        R = bx1 if col_edge_ok(bx1, T, Bm, 1) else None
        if L is None and R is None: _dbg(3, b); continue
        if L is None or R is None:
            col = [r for r in same_h if (L is None and abs(r[2] - R) <= 1) or (R is None and abs(r[0] - L) <= 1)]
            if col:  # same column of a form: same width
                wd = col[0][2] - col[0][0]
                L, R = (R - wd, R) if L is None else (L, L + wd)
            elif filled:  # button: content padded like the reference button's content
                cs = _content_span(a, damage, fsig, cy, (L + 1) if L is not None else bx0, (R - 1) if R is not None else bx1)
                rr = same_h[0]; rs = _content_span(a, np.zeros_like(damage), fsig, (rr[1] + rr[3]) // 2, rr[0] + 1, rr[2] - 1)
                if not cs or not rs: _dbg(4, b); continue
                if R is None: R = cs[1] + (rr[2] - rs[1])
                else: L = cs[0] - (rs[0] - rr[0])
            else:
                _dbg(5, b); continue
        x0, y0, x1, y1 = max(0, L), max(0, T), min(W - 1, R), min(H - 1, Bm); w = x1 - x0 + 1; h = y1 - y0 + 1
        # most similar first: same width, then closest width; the first that passes every check wins
        cur = a[y0:y1 + 1, x0:x1 + 1]; dmg = damage[y0:y1 + 1, x0:x1 + 1] > 0
        chosen = None
        for ref in sorted(same_h, key=lambda r: abs((r[2] - r[0] + 1) - w))[:8]:
            syn = _synth(c[ref[1]:ref[3] + 1, ref[0]:ref[2] + 1], h, w)
            if syn is None: continue
            S, k = syn
            # verify the drawn style on the element's own undamaged border band
            band = np.zeros(dmg.shape, bool); band[:2] = band[-2:] = True; band[:, :k] = band[:, -k:] = True
            chk = band & ~dmg
            if chk.sum() < 8: continue
            err = np.abs(S[chk].astype(int) - cur[chk].astype(int)).max(1)
            if err.mean() > 8 or np.percentile(err, 90) > 60: continue
            # never invent text/icons: refuse if the mark covered any part of the content area
            inner = np.zeros(dmg.shape, bool); inner[3:-3, k:-k] = True
            content = inner & ~dmg & (np.abs(cur.astype(int) - S.astype(int)).max(2) > 40)
            if content.any():
                cxs = np.where(content.any(0))[0]; cys = np.where(content.any(1))[0]
                zone = np.zeros(dmg.shape, bool); zone[cys.min():cys.max() + 1, cxs.min():cxs.max() + 1] = True
                core = cv2.erode(dmg.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0  # the safety margin added around marks is not real damage
                if (zone & core).any(): _dbg(6, b); break
            chosen = (ref, S, err); break
        if chosen is None: _dbg(7, b); continue
        ref, S, err = chosen
        out = cur.copy(); out[dmg] = S[dmg]
        a[y0:y1 + 1, x0:x1 + 1] = out
        covered[y0:y1 + 1, x0:x1 + 1] = 1
        done.append({'method': 'element rebuilt', 'box': [int(x0), int(y0), int(x1), int(y1)], 'style_from': [int(v) for v in ref], 'err': round(float(err.mean()), 2)})
    return a, done, covered


def continuation_ok(c, comp, tol=18, need=0.995):
    ys, xs = np.where(comp > 0); H, W = comp.shape; a = c.astype(int); good = 0
    for y, x in zip(ys, xs):
        l = x - 1
        while l >= 0 and comp[y, l]: l -= 1
        r = x + 1
        while r < W and comp[y, r]: r += 1
        u = y - 1
        while u >= 0 and comp[u, x]: u -= 1
        d = y + 1
        while d < H and comp[d, x]: d += 1
        ok = False
        if l >= 0 and r < W and np.abs(a[y, l] - a[y, r]).max() <= tol and np.abs(a[y, x] - a[y, l]).max() <= tol: ok = True
        if not ok and u >= 0 and d < H and np.abs(a[u, x] - a[d, x]).max() <= tol and np.abs(a[y, x] - a[u, x]).max() <= tol: ok = True
        good += ok
    return good >= need * len(ys)


def refill_background(c, damage, protect):
    """Damaged pixels outside rebuilt elements: row/column continuation that never borrows from an element."""
    mask = ((damage > 0) | (protect > 0)).astype(np.uint8)
    out = line_fill(c, mask)
    out[protect > 0] = c[protect > 0]
    return out


def line_fill(a, mask, tol=30):
    """Row/column continuation (as the house axis_fill) with one change: when both a row and a column
    could continue through a pixel, the one carrying a line (the colour further from the background)
    wins, so panel lines and grid lines run unbroken under a removed circle."""
    a = a.copy(); H, W = mask.shape
    ys, xs = np.where(mask > 0)
    if not len(ys): return a
    src = a.astype(int)
    bgc = _local_bg(a, [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
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
            a[y, x] = L if np.abs(L - bgc).sum() >= np.abs(U - bgc).sum() else U
        elif vv: a[y, x] = U
        elif hv: a[y, x] = L
        else:
            c_ = [t for t in [(x - l, L), (r - x, R), (y - u, U), (d - y, D)] if t[1] is not None]
            a[y, x] = min(c_, key=lambda t: t[0])[1]
    return a


def clear_marks_mask(im):
    """Same as the house clear_marks, but also returns the exact mask it filled (a filled pixel can come
    out the same colour as the mark, e.g. a white circle body over white, so a pixel diff misses it)."""
    a = np.array(im)
    red = I.red_mask(a)
    hor = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((1, 25), np.uint8))
    ver = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((25, 1), np.uint8))
    mask = hor | ver
    circles = I.find_circles(a, red)
    for cx, cy, rad in circles: cv2.circle(mask, (int(cx), int(cy)), int(rad) + 3, 1, -1)
    near = cv2.dilate(mask, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((red & (1 - mask)).astype(np.uint8))
    for i in range(1, n):
        w_, h_, area = st[i][2], st[i][3], st[i][4]; comp = lab == i
        if (comp & (near > 0)).any() and area < 400 and (w_ >= 3 * h_ or h_ >= 3 * w_): mask[comp] = 1
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    return line_fill(a, mask), mask.astype(np.uint8), circles


def unmark(src_path, dst, screens, inline=(), blue=False, keep_border=False, min_score=0.92, ctx=40, blue_boxes=None):
    src = I.load(src_path)
    base, removed = (src, 0) if keep_border else strip_frame(src)
    a0 = np.array(base)
    c, changed, circles = clear_marks_mask(base)
    # mark pieces clear_marks missed (short line segments cut by a circle): red components touching
    # what was removed. The app's own red (asterisks, icons) never touches a mark, so it stays.
    for _ in range(3):
        rm = I.red_mask(c)
        if not rm.any(): break
        n_, lab_, st_, _ = cv2.connectedComponentsWithStats(rm)
        touch = cv2.dilate(changed, np.ones((3, 3), np.uint8)) > 0
        ids = set(np.unique(lab_[touch & (rm > 0)])) - {0}
        # only line-like pieces or specks are mark leftovers; compact red shapes (asterisks, icons) are app
        ids = {i for i in ids if (lambda w_, h_, ar: ar <= 12 or w_ >= 3 * h_ or h_ >= 3 * w_)(st_[i][2], st_[i][3], st_[i][4])}
        if not ids: break
        extra = np.isin(lab_, list(ids)).astype(np.uint8)
        extra = cv2.dilate(extra, np.ones((3, 3), np.uint8))
        c = line_fill(c, extra); changed |= extra
    near = np.zeros_like(changed)
    for cx, cy, rad in circles: cv2.circle(near, (int(cx), int(cy)), int(rad) + 10, 1, -1)
    left = I.red_mask(c) & near
    if left.any():
        lm = cv2.dilate(left, np.ones((3, 3), np.uint8)); c = I.axis_fill(c, lm); changed |= lm
    blue_candidates = []
    if blue:  # detection only: the app has its own blue panels/lines, so nothing blue is removed unasked
        bm = blue_box_mask(c)
        if bm.any():
            n_, _, st2, _ = cv2.connectedComponentsWithStats(bm)
            blue_candidates = [[int(x), int(y), int(x + w - 1), int(y + h - 1)] for x, y, w, h, _ in st2[1:]]
    for bb in blue_boxes or []:  # user-confirmed drawn blue boxes: remove only their outline band
        x0, y0, x1, y1 = bb; band = np.zeros(c.shape[:2], np.uint8)
        band[max(0, y0 - 2):y1 + 3, max(0, x0 - 2):x1 + 3] = 1; band[y0 + 4:y1 - 3, x0 + 4:x1 - 3] = 0
        r_, g_, b_ = [c[..., k].astype(int) for k in range(3)]
        bl = ((b_ > 140) & (b_ - r_ > 80)).astype(np.uint8) & band
        if bl.any():
            bl = cv2.dilate(bl, np.ones((3, 3), np.uint8)) & band; c = line_fill(c, bl); changed |= bl
    changed0 = changed.copy()
    # damaged = pixels that were under a mark AND whose surroundings are not plain (plain areas are
    # already exact after row/column continuation: background, straight panel lines)
    g = cv2.cvtColor(a0, cv2.COLOR_RGB2GRAY).astype(np.float32)
    plain_ref = cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32)
    texture = cv2.dilate((cv2.morphologyEx(plain_ref, cv2.MORPH_GRADIENT, np.ones((3, 3))) > 25).astype(np.uint8), np.ones((9, 9), np.uint8))
    damage = (cv2.dilate(changed, np.ones((3, 3), np.uint8)) & texture).astype(np.uint8)
    report = {'blue_box_candidates': blue_candidates, 'frame_removed_px': removed, 'mark_px': int(changed.sum()), 'circles': [(int(x), int(y)) for x, y, _ in circles], 'repairs': [], 'unresolved': []}
    H, W = damage.shape
    # 0a. element similarity: a whole identical element (same screen elsewhere, a neighbour screenshot,
    #     or a step crop) replaces the damaged one when it matches every pixel the mark left visible
    allmask = (damage | cv2.dilate(changed, np.ones((3, 3), np.uint8))).astype(np.uint8)
    lib = list(inline) + element_library([('SELF', Image.fromarray(c))], exclude=cv2.dilate(allmask, np.ones((9, 9), np.uint8))) \
        + element_library(screens)
    if lib:
        n0, lab0, _, _ = cv2.connectedComponentsWithStats(cv2.dilate(damage, np.ones((5, 5), np.uint8)))
        for i in range(1, n0):
            comp = ((lab0 == i) & (damage > 0)).astype(np.uint8)
            if comp.sum() < 4: continue
            comp = (cv2.dilate(comp, np.ones((15, 15), np.uint8)) & allmask).astype(np.uint8)
            while comp.sum() >= 4:
                c2, info = fit_inline(c, comp, lib)
                if not info: break
                cov = info.pop('covered'); c = c2
                info['method'] = 'similar element' if '@' in info['donor'] else 'inline crop'
                ys_, xs_ = np.where(cov > 0)
                report['repairs'].append(dict(info, box=[int(xs_.min()), int(ys_.min()), int(xs_.max()), int(ys_.max())]))
                comp = comp & (1 - cov); damage = damage & (1 - cov); allmask = allmask & (1 - cov); changed = changed & (1 - cov)
    # 0b. UI elements hit by a mark are redrawn in their own style; the plain area around is re-continued
    c, rebuilt, covered = rebuild_elements(c, (damage | cv2.dilate(changed, np.ones((3, 3), np.uint8))).astype(np.uint8))
    if rebuilt:
        report['repairs'] += rebuilt
        out_dmg = (damage | cv2.dilate(changed, np.ones((3, 3), np.uint8))) & (1 - covered)
        c = refill_background(c, out_dmg, covered)
        texture = cv2.dilate((cv2.morphologyEx(cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32), cv2.MORPH_GRADIENT, np.ones((3, 3))) > 25).astype(np.uint8), np.ones((9, 9), np.uint8))
        damage = out_dmg & texture & (1 - cv2.dilate(covered, np.ones((3, 3), np.uint8)))
    unknown = (cv2.dilate(changed, np.ones((3, 3), np.uint8)) & (1 - covered if rebuilt else 1)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(damage, np.ones((5, 5), np.uint8)))
    for i in range(1, n):
        comp = ((lab == i) & (damage > 0)).astype(np.uint8)
        if comp.sum() < 4: continue
        # everything the mark removed near this spot is unknown (also plain pixels already continued)
        comp = (comp | (cv2.dilate(comp, np.ones((15, 15), np.uint8)) & unknown)).astype(np.uint8)
        x, y, w, h, _ = st[i]
        box = [max(0, x - 3), max(0, y - 3), min(W - 1, x + w + 2), min(H - 1, y + h + 2)]
        # 1. a step crop that fits perfectly
        c2, info = fit_inline(c, comp, inline) if inline else (c, None)
        if info:
            c = c2; comp = comp & (1 - info.pop('covered')); report['repairs'].append(dict(info, box=box))
            if comp.sum() < 4: continue
            c = line_fill(c, comp)  # re-continue the rest from the now-correct surroundings
        # 2. a neighbour screenshot, then the same screen elsewhere
        c2, info = fit_screen(c, comp, box, screens, ctx, min_score, self_img=Image.fromarray(c))
        if info['method']:
            c = c2; report['repairs'].append(dict(info, box=box)); continue
        # 3. plain area: row/column continuation is exact when every repaired pixel agrees with the
        #    undamaged pixels on both sides along a row or a column
        if continuation_ok(c, comp):
            report['repairs'].append({'method': 'continuation (plain area)', 'box': box}); continue
        report['unresolved'].append({'box': box, 'tried': info['tried'][:4]})
    # GUARD: the app's own elements are never removed. Any pixel outside the marks' footprint that differs
    # from the screenshot is put back, and reported.
    allowed = cv2.dilate(changed0, np.ones((5, 5), np.uint8)) > 0
    diff = np.abs(c.astype(int) - a0.astype(int)).max(2) > 0
    stray = diff & ~allowed
    if stray.any():
        c[stray] = a0[stray]
        report['guard_restored_px'] = int(stray.sum())
    I.save(Image.fromarray(c), dst)
    spots = [((b['box'][0] + b['box'][2]) // 2, (b['box'][1] + b['box'][3]) // 2) for b in report['repairs'] + report['unresolved']] or report['circles']
    report['check_sheet'] = I.spot_sheet(base, Image.fromarray(c), spots[:16], str(Path(dst).with_name(Path(dst).stem + '_check.png')))
    report['seamless'] = not report['unresolved']
    if report['unresolved']:
        report['NEXT'] = 'Not seamless yet: fix each unresolved box (fill/copy with a donor, or ask the user for an unmarked screenshot). Do not use this image until seamless is true.'
    return report


# ------------------------------------------------------------------ grid rows
def remove_rows(src, box, until=None):
    """Delete the band y0..y1 inside x0..x1; everything below (down to `until`, the bottom of the grid
    body - top of the scrollbar/footer) moves up; the freed band at the bottom is rebuilt as empty grid
    (row/column continuation of the grid lines and background)."""
    a = np.array(src).copy(); x0, y0, x1, y1 = box; H = a.shape[0]
    h = y1 - y0 + 1; end = min(until or H, H)
    a[y0:end - h, x0:x1 + 1] = a[y0 + h:end, x0:x1 + 1].copy()
    mask = np.zeros(a.shape[:2], np.uint8); mask[end - h:end, x0:x1 + 1] = 1
    a[end - h:end, x0:x1 + 1] = 255
    a = I.axis_fill(a, mask)
    return Image.fromarray(a)


# ------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd')
    p = sp.add_parser('copy'); p.add_argument('src'); p.add_argument('dst')
    p.add_argument('--from-box', required=True, help='x0,y0,x1,y1 in the donor (or in SRC with no --donor)')
    p.add_argument('--to', required=True, help='x,y top-left in SRC'); p.add_argument('--donor')
    p.add_argument('--flip', choices=['h', 'v', 'hv'], help='mirror the piece (h = left-right, v = top-bottom) before placing it')
    p.add_argument('--recolor', help='FROM:TO[,FROM:TO] hex colours; pixels of exactly FROM become TO (e.g. f7f7f7:99ccff)')
    p.add_argument('--approved', action='store_true', help='apply a flipped/recoloured piece. Without it only a preview is written. Pass it ONLY after the user approved this exact piece')
    p.add_argument('--marks', help='the original MARKED screenshot (same size as SRC). Required with --flip/--recolor: the piece is placed only inside its marked area')
    for c in ('unmark', 'fill', 'rank', 'remove-rows'):
        p = sp.add_parser(c); p.add_argument('src')
        if c != 'rank': p.add_argument('dst')
        p.add_argument('--donors', nargs='*'); p.add_argument('--donor-dir')
        p.add_argument('--inline', nargs='*', help='step crops (buttons/icons) that may be placed only where they fit perfectly')
        p.add_argument('--box'); p.add_argument('--min', type=float, default=0.90)
        p.add_argument('--blue', action='store_true', help='only REPORT possible drawn blue boxes (nothing removed)')
        p.add_argument('--blue-box', action='append', help='x0,y0,x1,y1 of a drawn blue box the USER confirmed; only its outline is removed'); p.add_argument('--keep-border', action='store_true')
        p.add_argument('--no-fallback', action='store_true'); p.add_argument('--ctx', type=int, default=24)
        p.add_argument('--until', type=int, help='remove-rows: bottom y of the grid body')
        p.add_argument('--self', action='store_true', help='also look for a matching element elsewhere on the same screen')
    p = sp.add_parser('sheet'); p.add_argument('files', nargs='+'); p.add_argument('--out', required=True); p.add_argument('--labels')
    a = ap.parse_args()
    if not a.cmd: ap.print_help(); return

    if a.cmd == 'copy':
        src = I.load(a.src); d = I.load(a.donor) if a.donor else src
        fb = I.box_arg(a.from_box); x, y = [int(v) for v in a.to.split(',')]
        piece = d.crop((fb[0], fb[1], fb[2] + 1, fb[3] + 1)).convert('RGB')
        changed = []
        if a.flip:
            if 'h' in a.flip: piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
            if 'v' in a.flip: piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            changed.append('flip ' + a.flip)
        if a.recolor:
            arr = np.asarray(piece).copy()
            for pair in a.recolor.split(','):
                f, t = [c.strip().lstrip('#') for c in pair.split(':')]
                fc = np.array([int(f[i:i + 2], 16) for i in (0, 2, 4)]); tc = [int(t[i:i + 2], 16) for i in (0, 2, 4)]
                hit = (np.abs(arr.astype(int) - fc).max(2) == 0); arr[hit] = tc
                changed.append('recolor %s->%s (%d px)' % (f, t, int(hit.sum())))
            piece = Image.fromarray(arr)
        out = src.copy(); out.paste(piece, (x, y))
        if changed:
            # A flipped/recoloured piece may only touch the marked area: every pixel outside the marks'
            # footprint (red boxes, circles, stubs of the ORIGINAL marked screenshot) stays as in SRC.
            if not a.marks: sys.exit('--flip/--recolor need --marks MARKED.png (the original marked screenshot, same size as SRC): the piece is placed only inside the marked area')
            mk = I.load(a.marks)
            if mk.size != src.size: sys.exit('--marks image is %s but SRC is %s: they must be the same screenshot' % (mk.size, src.size))
            mask = clear_marks_mask(mk)[1] > 0
            box_m = np.zeros(mask.shape, bool); box_m[y:y + piece.height, x:x + piece.width] = True
            inside = int((mask & box_m).sum()); skipped = int((~mask & box_m).sum())
            if inside == 0: sys.exit('the piece does not touch the marked area: nothing to do')
            o = np.array(out.convert('RGB')); s = np.array(src.convert('RGB')); o[~mask] = s[~mask]; out = Image.fromarray(o)
            changed.append('marked area only: %d px placed, %d px outside the marks left untouched' % (inside, skipped))
        if changed and not a.approved:
            # A flipped or recoloured piece is not a plain copy of real pixels: show it, change nothing.
            pad = 24; bx = (max(0, x - pad), max(0, y - pad), min(src.width, x + piece.width + pad), min(src.height, y + piece.height + pad))
            z = 4; b4 = src.crop(bx).convert('RGB'); a4 = out.crop(bx).convert('RGB')
            b4 = b4.resize((b4.width * z, b4.height * z), Image.NEAREST); a4 = a4.resize((a4.width * z, a4.height * z), Image.NEAREST)
            sheet = Image.new('RGB', (b4.width + a4.width + 12, b4.height), 'white'); sheet.paste(b4, (0, 0)); sheet.paste(a4, (b4.width + 12, 0))
            prop = str(Path(a.dst).with_name(Path(a.dst).stem + '_proposal.png')); sheet.save(prop)
            print('NEEDS APPROVAL (%s): nothing written to %s. Before | after preview: %s' % ('; '.join(changed), a.dst, prop))
            print('Show the preview to the user. Re-run with --approved only after the user says yes to this piece.'); return
        I.save(out, a.dst)
        print('copied %s -> (%d,%d) into %s%s' % (fb, x, y, a.dst, (' [' + '; '.join(changed) + ', approved by user]') if changed else '')); return
    if a.cmd == 'sheet':
        print(I.preview(a.files, a.out, a.labels.split(',') if a.labels else None)); return
    if a.cmd == 'rank':
        s = I.strip_border(I.load(a.src))[0]
        for name, d in sorted(donor_list(a), key=lambda t: -similarity(s, t[1])):
            print('%.3f  %s' % (similarity(s, d), name))
        return
    if a.cmd == 'unmark':
        scr, inl = donor_list(a, 'both')
        me = strip_frame(I.load(a.src))[0]
        scr = sorted(scr, key=lambda t: -similarity(me, t[1]))[:6]  # the 6 closest shots of this screen
        rep = unmark(a.src, a.dst, scr, inl, blue=a.blue, blue_boxes=[I.box_arg(x) for x in (a.blue_box or [])], keep_border=a.keep_border, min_score=max(a.min, 0.92), ctx=max(a.ctx, 40))
        print(json.dumps(rep, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))); return
    if not a.box: sys.exit('--box x0,y0,x1,y1 is required')
    box = I.box_arg(a.box)
    src = I.load(a.src)
    if a.cmd == 'fill':
        im, info = fill_from_neighbours(src, donor_list(a), box, a.min, a.ctx, fallback=not a.no_fallback, self_donor=a.self)
        I.save(im, a.dst)
        x0, y0, x1, y1 = box; pad = 60
        crop = [max(0, x0 - pad), max(0, y0 - pad), min(src.width, x1 + pad), min(src.height, y1 + pad)]
        chk = str(Path(a.dst).with_name(Path(a.dst).stem + '_check.png'))
        Path(chk).parent.mkdir(parents=True, exist_ok=True)
        b, f = src.crop(crop), im.crop(crop)
        can = Image.new('RGB', (b.width * 2 + 10, b.height), (200, 0, 0)); can.paste(b, (0, 0)); can.paste(f, (b.width + 10, 0)); can.save(chk)
        info['check'] = chk
        print(json.dumps(info, indent=1))
        if info['method'] != 'neighbour': print('NOTE: no neighbour matched well enough - show the check image to the user before using it.')
        return
    if a.cmd == 'remove-rows':
        I.save(remove_rows(src, box, a.until), a.dst); print('saved', a.dst); return


if __name__ == '__main__':
    main()
