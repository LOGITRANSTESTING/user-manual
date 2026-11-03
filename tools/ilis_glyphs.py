"""Letter library: learn the app's real letters from screenshots and write new text with them.

A font = fonts/<name>/meta.json + one PNG per glyph (alpha mask, white = ink).
Glyphs are stored relative to the baseline, so text can be written on any background
(antialiasing is remapped to the background under it)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFont, ImageDraw

DESC = set('gjpqy,;')
ROOT = Path(__file__).resolve().parent.parent / 'fonts'


def _alpha(a, bg, ink):
    """ink coverage 0..1 of each pixel between background and ink colour."""
    v = ink - bg; n = (v * v).sum()
    if n == 0: return np.zeros(a.shape[:2])
    return np.clip(((a - bg) * v).sum(2) / n, 0, 1)


def _alpha3(a, bg, ink):
    """Per-channel ink coverage, so ClearType colour fringes are kept."""
    base = _alpha(a, bg, ink)
    out = np.repeat(base[..., None], 3, 2)
    for c in range(3):
        d = ink[c] - bg[c]
        if abs(d) >= 40: out[..., c] = np.clip((a[..., c] - bg[c]) / d, 0, 1)
    return out


def _bg_ink(a):
    flat = a.reshape(-1, 3)
    vals, cnt = np.unique(flat, axis=0, return_counts=True)
    bg = vals[np.argmax(cnt)].astype(float)
    dist = np.abs(flat - bg).sum(1)
    far = flat[dist >= np.percentile(dist, 99.5)]
    ink = np.median(far, axis=0).astype(float)
    return bg, ink


def _segments(cols, thr=0.2):
    on = cols > thr; segs = []; x = 0
    while x < len(on):
        if on[x]:
            s = x
            while x < len(on) and on[x]: x += 1
            segs.append([s, x - 1])
        x += 1
    return segs


def _split_widest(alpha, seg):
    s, e = seg
    if e - s < 4: return None
    cols = alpha[:, s:e + 1].sum(0)
    k = 2 + int(np.argmin(cols[2:-2]))  # weakest column inside the segment
    return [s, s + k - 1], [s + k, e]


def _ttf_path(bold=False):
    reg = ['arial.ttf', 'C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
           'LiberationSans-Regular.ttf', '/Library/Fonts/Arial.ttf']
    bld = ['arialbd.ttf', 'C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
           'LiberationSans-Bold.ttf', '/Library/Fonts/Arial Bold.ttf']
    for f in (bld if bold else reg):
        try: ImageFont.truetype(f, 12); return f
        except OSError: pass
    return None


class Font:
    def __init__(self, name):
        self.name = name; self.dir = ROOT / name
        self.meta = {'glyphs': {}, 'words': {}, 'ink': None, 'gap': 1, 'space': 4, 'cap': None, 'xh': None}
        if (self.dir / 'meta.json').exists():
            self.meta = json.loads((self.dir / 'meta.json').read_text(encoding='utf-8'))

    def save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / 'meta.json').write_text(json.dumps(self.meta, indent=1, ensure_ascii=False), encoding='utf-8')

    def _store(self, key, alpha, top, kind, gap=None, overwrite=False, lpad=0, rpad=0, off=None):
        table = self.meta['glyphs' if kind == 'g' else 'words']
        if key in table and not overwrite: return False
        fn = ('g_' if kind == 'g' else 'w_') + '_'.join('%04x' % ord(c) for c in key)[:120] + '.png'
        Image.fromarray((np.clip(alpha, 0, 1) * 255).round().astype(np.uint8)).save(self.dir / fn)
        table[key] = {'file': fn, 'top': int(top), 'w': int(alpha.shape[1]), 'h': int(alpha.shape[0])}
        if gap is not None: table[key]['gap'] = int(gap)
        table[key]['lpad'] = int(lpad); table[key]['core'] = int(alpha.shape[1] - lpad - rpad)
        if off is not None: table[key]['off'] = round(float(off), 2)
        return True

    # ------------------------------------------------------------ learn
    def learn(self, im, box, text, overwrite=False, bold=None):
        """Learn letters (and whole words) from a text line whose content is known.
        Touching letters are separated using Arial's letter widths as a guide, snapped to the
        lightest column of the real text."""
        self.dir.mkdir(parents=True, exist_ok=True)
        if bold is not None: self.meta['bold'] = bool(bold)
        x0, y0, x1, y1 = box
        a = np.array(im.crop((x0, y0, x1 + 1, y1 + 1)).convert('RGB')).astype(float)
        bg, ink = _bg_ink(a)
        al = _alpha(a, bg, ink); al3 = _alpha3(a, bg, ink)
        rows = np.where(al.max(1) > 0.15)[0]
        if len(rows) == 0: return {'ok': False, 'msg': 'no ink in box'}
        al = al[rows.min():rows.max() + 1]; al3 = al3[rows.min():rows.max() + 1]
        cols = al.max(0); core = cols > 0.2
        segs = _segments(cols)
        words = text.split()
        if not segs: return {'ok': False, 'msg': 'no letters found'}
        # words: split at the (k-1) widest gaps
        gaps = sorted([(segs[i + 1][0] - segs[i][1] - 1, i) for i in range(len(segs) - 1)], reverse=True)
        k = len(words)
        cut = sorted(g[1] for g in gaps[:k - 1]) if k > 1 else []
        spaces = [g[0] for g in gaps[:k - 1]]
        groups = []; st = 0
        for c in cut: groups.append(segs[st:c + 1]); st = c + 1
        groups.append(segs[st:])
        ttf = _ttf_path(self.meta.get('bold'))
        report = {'ok': True, 'learned': [], 'kept': [], 'warnings': []}
        obs_w = segs[-1][1] - segs[0][0] + 1
        size = None
        if ttf:
            best = None
            for s4 in range(32, 96):
                Fs = ImageFont.truetype(ttf, s4 / 4); bb = Fs.getbbox(' '.join(words))
                err = abs((bb[2] - bb[0]) - obs_w)
                if best is None or err < best[0]: best = (err, s4 / 4)
            size = best[1]
            if self.meta.get('ttf_size') is None: self.meta['ttf_size'] = size
            FT = ImageFont.truetype(ttf, size)
        letters = []  # (word_index, char, s, e)
        for wi, (w, g) in enumerate(zip(words, groups)):
            ws, we = g[0][0], g[-1][1]
            if len(g) == len(w) and ttf is None:
                for ch, sg in zip(w, g): letters.append((wi, ch, sg[0], sg[1]))
                continue
            if ttf is None:
                report['warnings'].append('%s: letters touch and no Arial font found; word kept whole' % w); continue
            F = ImageFont.truetype(ttf, 40)
            bx = F.getbbox(w); scale = (we - ws + 1) / max(1, (bx[2] - bx[0]))
            # letter widths from Arial, then the best cut positions by dynamic programming:
            # cuts prefer light columns, widths stay close to Arial's (local, so no drift on long words)
            starts = [F.getlength(w[:i]) + F.getbbox(w[i])[0] - bx[0] for i in range(len(w))] + [bx[2] - bx[0]]
            wid = [(starts[i + 1] - starts[i]) * scale for i in range(len(w))]
            n_ = len(w); span = we + 1 - ws; INF = 1e9; lam = 0.25
            cost = {0: {0: 0.0}}; back = {}
            for i in range(1, n_ + 1):
                cost[i] = {}; back[i] = {}
                cand = [span] if i == n_ else range(1, span)
                for bpos in cand:
                    best = (INF, None)
                    for bp, cv in cost[i - 1].items():
                        if bp >= bpos: continue
                        c = cv + lam * abs((bpos - bp) - wid[i - 1]) + (cols[ws + bpos] if i < n_ else 0)
                        if c < best[0]: best = (c, bp)
                    if best[1] is not None: cost[i][bpos] = best[0]; back[i][bpos] = best[1]
                # keep it small: only the best positions per letter
                if i < n_ and len(cost[i]) > 40:
                    keep = sorted(cost[i].items(), key=lambda kv: kv[1])[:40]; cost[i] = dict(keep)
            if span not in cost[n_]:
                report['warnings'].append('%s: could not separate letters; word kept whole' % w); continue
            cuts = [span]
            for i in range(n_, 0, -1): cuts.append(back[i][cuts[-1]])
            bounds = [ws + c for c in reversed(cuts)]
            for i in range(1, len(bounds)):
                bounds[i] = max(bounds[i], bounds[i - 1] + 1)
            for i, ch in enumerate(w):
                s0, e0 = bounds[i], bounds[i + 1] - 1
                if not core[s0:e0 + 1].any():
                    report['warnings'].append('could not cut %r in %s' % (ch, w)); continue
                while s0 < e0 and not core[s0]: s0 += 1
                while e0 > s0 and not core[e0]: e0 -= 1
                if e0 < s0 or s0 >= len(cols): report['warnings'].append('could not cut %r in %s' % (ch, w)); continue
                letters.append((wi, ch, s0, min(e0, len(cols) - 1)))
        # baseline = bottom of non-descender letters
        bottoms = []
        for wi, ch, s0, e0 in letters:
            if ch.isalnum() and ch not in DESC:
                r = np.where(al[:, s0:e0 + 1].max(1) > 0.3)[0]
                if len(r): bottoms.append(r.max())
        base = int(np.median(bottoms)) if bottoms else al.shape[0] - 1
        self.meta['ink'] = [int(v) for v in ink]
        offs = {}
        if size:
            for wi, w in enumerate(words):
                wl = [L for L in letters if L[0] == wi]
                if len(wl) != len(w): continue
                wb = FT.getbbox(w)
                for i, (_, ch, s0, e0) in enumerate(wl):
                    pred = wl[0][2] + (FT.getlength(w[:i]) + FT.getbbox(w[i])[0] - wb[0])
                    offs.setdefault((wi, i), s0 - pred)
        intra = []
        for j, (wi, ch, s0, e0) in enumerate(letters):
            nxt = letters[j + 1] if j + 1 < len(letters) and letters[j + 1][0] == wi else None
            gap = (nxt[2] - e0 - 1) if nxt else None
            if gap is not None: intra.append(gap)
            lp = 1 if s0 > 0 and cols[s0 - 1] > 0.02 and not core[s0 - 1] else 0
            rp = 1 if e0 + 1 < len(cols) and cols[e0 + 1] > 0.02 and not core[e0 + 1] else 0
            wl = [L for L in letters if L[0] == wi]; idx = wl.index((wi, ch, s0, e0))
            off = offs.get((wi, idx))
            if self._store(ch, al3[:, s0 - lp:e0 + 1 + rp], -base, 'g', gap=gap, overwrite=overwrite, lpad=lp, rpad=rp, off=off):
                report['learned'].append(ch)
            else: report['kept'].append(ch)
        for w, g in zip(words, groups):
            ws, we = g[0][0], g[-1][1]
            lp = 1 if ws > 0 and cols[ws - 1] > 0.02 else 0
            rp = 1 if we + 1 < len(cols) and cols[we + 1] > 0.02 else 0
            self._store(w, al3[:, ws - lp:we + 1 + rp], -base, 'w', overwrite=overwrite, lpad=lp, rpad=rp)
        if intra: self.meta['gap'] = int(np.median(intra))
        if spaces: self.meta['space'] = int(np.median(spaces))
        self.save()
        return report

    # ------------------------------------------------------------ render
    def _glyph(self, key, kind='g'):
        t = self.meta['glyphs' if kind == 'g' else 'words'].get(key)
        if not t: return None
        a = np.array(Image.open(self.dir / t['file'])).astype(float) / 255
        if a.ndim == 2: a = np.repeat(a[..., None], 3, 2)
        return a, t

    def _fallback(self, ch, ttf=None):
        """Render a missing letter with a TTF font sized to the learned letters."""
        hx = None
        for c in 'xaeonsu':
            if c in self.meta['glyphs']:
                a, t = self._glyph(c); r = np.where(a.max(axis=(1, 2)) > 0.15)[0]; hx = r.max() - r.min() + 1; break
        size = 12
        cands = [ttf] if ttf else []
        cands += ['arial.ttf', 'C:/Windows/Fonts/arial.ttf', 'LiberationSans-Regular.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 'DejaVuSans.ttf']
        bold = self.meta.get('bold')
        if bold:
            cands = ['arialbd.ttf', 'C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'] + cands
        font = None
        for f in cands:
            try: font = f; ImageFont.truetype(f, 12); break
            except (OSError, TypeError): font = None
        if not font: return None
        best = None
        for s in [x / 2 for x in range(16, 40)]:
            F = ImageFont.truetype(font, s); bb = F.getbbox('x')
            if hx is None or abs((bb[3] - bb[1]) - hx) < (abs(best[1]) if best else 99): best = (s, (bb[3] - bb[1]) - (hx or 0))
        F = ImageFont.truetype(font, self.meta.get('ttf_size') or best[0])
        img = Image.new('L', (60, 60), 0); d = ImageDraw.Draw(img)
        d.text((10, 40), ch, fill=255, font=F, anchor='ls')
        a = np.array(img).astype(float) / 255
        cols = np.where(a.max(0) > 0.06)[0]
        if not len(cols): return None
        a = a[:, cols.min():cols.max() + 1]
        rows = np.where(a.max(1) > 0.02)[0]
        top = rows.min() - 39
        a = a[rows.min():rows.max() + 1]
        return np.repeat(a[..., None], 3, 2), {'top': int(top), 'gap': self.meta.get('gap', 1), 'lpad': 0, 'core': int(a.shape[1])}

    def layout(self, text, ttf=None):
        """Returns (pieces, width, missing). With a fitted Arial size, letters sit at Arial's positions
        (+ each letter's learned offset), so spacing matches the app; otherwise learned gaps are used."""
        size = self.meta.get('ttf_size'); path = ttf or _ttf_path(self.meta.get('bold'))
        if size and path:
            F = ImageFont.truetype(path, size)
            tb = F.getbbox(text) if text.strip() else (0, 0, 0, 0)
            pieces = []; missing = []
            def pred(i): return F.getlength(text[:i]) + F.getbbox(text[i])[0] - tb[0]
            i = 0; n = len(text)
            while i < n:
                if text[i] == ' ': i += 1; continue
                j = i
                while j < n and text[j] != ' ': j += 1
                w = text[i:j]
                g = self._glyph(w, 'w')
                first = self.meta['glyphs'].get(w[0], {})
                if g:
                    a, t = g; x = int(round(pred(i) + first.get('off', 0)))
                    pieces.append((a, x - t.get('lpad', 0), None, t))
                else:
                    for k in range(i, j):
                        ch = text[k]
                        gg = self._glyph(ch, 'g')
                        if not gg:
                            gg = self._fallback(ch, ttf); missing.append(ch)
                            if not gg: continue
                        a, t = gg
                        x = int(round(pred(k) + t.get('off', 0)))
                        pieces.append((a, x - t.get('lpad', 0), None, t))
                i = j
            width = int(round(tb[2] - tb[0]))
            return pieces, width, missing
        pieces = []; missing = []; x = 0
        words = text.split(' ')
        for wi, w in enumerate(words):
            if w == '':
                x += self.meta.get('space', 4); continue
            g = self._glyph(w, 'w')
            if g:
                a, t = g; pieces.append((a, x - t.get('lpad', 0), None, t)); x += t.get('core', a.shape[1])
            else:
                for ci, ch in enumerate(w):
                    gg = self._glyph(ch, 'g') or self._glyph(ch, 'w')
                    if not gg:
                        gg = self._fallback(ch, ttf); missing.append(ch)
                        if not gg: x += 4; continue
                    a, t = gg; pieces.append((a, x - t.get('lpad', 0), None, t)); x += t.get('core', a.shape[1])
                    if ci < len(w) - 1: x += t['gap'] if t.get('gap') is not None else self.meta.get('gap', 1)
            if wi < len(words) - 1: x += self.meta.get('space', 4)
        return pieces, x, missing

    def write(self, im, text, x, baseline, color=None, align='left', width=None, ttf=None):
        pieces, total, missing = self.layout(text, ttf)
        if align == 'center' and width: x = x + (width - total) // 2
        if align == 'right' and width: x = x + width - total
        a = np.array(im).astype(float)
        ink = np.array(color or self.meta.get('ink') or [0, 0, 0], float)
        for al, px, _, t in pieces:
            top = baseline + t['top']
            h, w = al.shape[:2]
            X, Y = x + px, top
            y0, x0 = max(0, Y), max(0, X); y1, x1 = min(a.shape[0], Y + h), min(a.shape[1], X + w)
            if y1 <= y0 or x1 <= x0: continue
            sub = al[y0 - Y:y1 - Y, x0 - X:x1 - X]
            a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - sub) + ink * sub
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), total, missing

    def baseline_of(self, im, box):
        """Baseline row of existing text in box (bottom of non-descender ink)."""
        x0, y0, x1, y1 = box
        a = np.array(im.crop((x0, y0, x1 + 1, y1 + 1)).convert('RGB')).astype(float)
        bg, ink = _bg_ink(a); al = _alpha(a, bg, ink)
        rows = al.max(1) > 0.15
        r = np.where(rows)[0]
        if not len(r): return y1
        # the row with the most ink near the bottom is the baseline area; descenders are sparse
        dens = (al > 0.3).sum(1)
        bottom = r.max()
        while bottom > r.min() and dens[bottom] < 0.25 * dens[r.min():r.max() + 1].max(): bottom -= 1
        return y0 + bottom


def list_fonts():
    if not ROOT.exists(): return {}
    out = {}
    for d in sorted(ROOT.iterdir()):
        if (d / 'meta.json').exists():
            m = json.loads((d / 'meta.json').read_text(encoding='utf-8'))
            out[d.name] = {'letters': ''.join(sorted(m['glyphs'])), 'words': len(m['words']), 'note': m.get('note', '')}
    return out
