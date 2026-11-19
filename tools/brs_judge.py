"""BRS donor judging - MEASUREMENT ONLY. It never writes or changes an image.

  python tools/brs_judge.py marks  MARKED.png
        Where the marks are: red line rows/columns, mark components, circles, footprint size.
  python tools/brs_judge.py scan   DIR_OR_FILES...
        Sort screenshots into: unmarked / marked with a clean same-size twin / marked, no twin.
  python tools/brs_judge.py judge  MARKED.png --box x0,y0,x1,y1 --donors F [F ...] [--range 8] [--dy A:B] [--top 5]
        Rank donors for ONE damaged part. A donor is judged on the UNTOUCHED pixels of the box only
        (everything outside the marks' footprint). diff 0 = it agrees on every untouched pixel.
        It is rejected for the part when it has a mark of its own inside the footprint (dirty).
        --range N tries offsets -N..N in x and y; --dy A:B widens the vertical search (e.g. repeated
        grid rows / menu items, or a cropped screenshot). Boxes are INCLUSIVE, like `brs_img.py copy`.
  python tools/brs_judge.py gate   MARKED.png RESULT.png [--twin UNMARKED.png]
        The final gate: pixels changed outside the marked area (must be 0), red mark pixels left
        (must be 0 apart from the app's own red), and - if a twin is given - pixels that differ from it.

Why: `unmark` reports "seamless" from its own repairs and can be wrong when a donor shows the same
screen in another state. These checks are independent of how the image was repaired.
"""
import argparse, glob, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ilis_img as I
import brs_img as B


def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.int16)


def footprint(path):
    """marked area of a marked screenshot: red boxes, circles (with their inside), stubs."""
    _, mask, circles = B.clear_marks_mask(I.load(path))
    return mask > 0, circles


def red(a): return I.red_mask(np.asarray(a, dtype=np.uint8)) > 0


def cmd_marks(a):
    arr = load(a.src); r = red(arr); fp, circles = footprint(a.src)
    print('h-lines (row, red px):', [(i, int(v)) for i, v in enumerate(r.sum(1)) if v > 40])
    print('v-lines (col, red px):', [(i, int(v)) for i, v in enumerate(r.sum(0)) if v > 25])
    st = cv2.connectedComponentsWithStats(r.astype(np.uint8), 8)[2][1:]
    print('components x,y,w,h,area:', [tuple(int(v) for v in s) for s in st if s[4] > 60])
    print('circles cx,cy,r:', [tuple(int(v) for v in c) for c in circles])
    print('marked area px:', int(fp.sum()))


def files_of(args):
    out = []
    for p in args:
        out += sorted(glob.glob(str(Path(p) / '**' / '*.png'), recursive=True)) if Path(p).is_dir() else [p]
    seen = {}
    for f in out: seen.setdefault(Path(f).name, f)
    return list(seen.values())


def cmd_scan(a):
    info = {}
    for f in files_of(a.files):
        im = Image.open(f)
        if im.size[0] < 600 or im.size[1] < 120: continue      # inline crops are not screenshots
        fp, _ = footprint(f); info[f] = (load(f), fp)
    for f, (arr, fp) in info.items():
        if fp.sum() < 200: print('unmarked   ', f); continue
        twin = None
        for g, (brr, gp) in info.items():
            if g == f or brr.shape != arr.shape or (gp & fp).any(): continue
            if ((np.abs(arr[::4, ::4] - brr[::4, ::4]).max(2) > 0) & ~fp[::4, ::4]).any(): continue
            if not ((np.abs(arr - brr).max(2) > 0) & ~fp).any(): twin = g; break
        print(('twin       %s  <- %s' % (f, twin)) if twin else ('NO TWIN    ' + f))


def cmd_judge(a):
    arr = load(a.src); fp, _ = footprint(a.src)
    x0, y0, x1, y1 = [int(v) for v in a.box.split(',')]; x1 += 1; y1 += 1
    A = arr[y0:y1, x0:x1]; un = ~fp[y0:y1, x0:x1]; hid = fp[y0:y1, x0:x1]
    dxs = sorted(range(-a.range, a.range + 1), key=abs)
    lo, hi = [int(v) for v in a.dy.split(':')] if a.dy else (-a.range, a.range)
    dys = sorted(range(lo, hi + 1), key=abs)
    rows = []
    for f in files_of(a.donors):
        if Path(f).resolve() == Path(a.src).resolve(): continue
        b = load(f); best = None
        for dy in dys:
            if y0 + dy < 0 or y1 + dy > b.shape[0]: continue
            for dx in dxs:
                if x0 + dx < 0 or x1 + dx > b.shape[1]: continue
                Bq = b[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                n = int((np.abs(A - Bq).max(2)[un] > 0).sum())
                dirty = int((red(Bq) & hid).sum()) if n == 0 else 0
                key = (n, dirty)
                if best is None or key < best[0]: best = (key, dx, dy)
                if key == (0, 0): break
            if best and best[0] == (0, 0): break
        if best: rows.append((best[0][0], best[0][1], f, best[1], best[2]))
    rows.sort()
    print('part %s: %d untouched px to agree on, %d hidden px' % (a.box, int(un.sum()), int(hid.sum())))
    if un.sum() < 40: print('WARNING: fewer than 40 untouched px in this box - widen it by a pixel or two, the judgement is weak')
    for n, dirty, f, dx, dy in rows[:a.top]:
        verdict = 'EXACT' if n == 0 and dirty == 0 else ('exact but DIRTY (own mark/red in the hidden area: %d px)' % dirty if n == 0 else 'differs on %d untouched px' % n)
        print('  %-48s offset (%d,%d)  %s' % (Path(f).name[:48], dx, dy, verdict))


def cmd_gate(a):
    m = load(a.marked); r = load(a.result)
    if m.shape != r.shape: sys.exit('sizes differ %s vs %s: run the gate on the repaired image BEFORE the frame is stripped' % (m.shape, r.shape))
    fp, _ = footprint(a.marked)
    ch = np.abs(m - r).max(2) > 0; out = ch & ~fp
    rr = (red(r) & fp).astype(np.uint8)       # red inside the marked area: a leftover mark is line-shaped,
    left = (cv2.morphologyEx(rr, cv2.MORPH_OPEN, np.ones((1, 12), np.uint8)) | cv2.morphologyEx(rr, cv2.MORPH_OPEN, np.ones((12, 1), np.uint8))) > 0
    print('changed px: %d' % int(ch.sum()))   # the app's own red (icons, asterisks) is compact and is not counted
    print('changed OUTSIDE the marked area: %d (must be 0)' % int(out.sum()))
    if out.any():
        ys, xs = np.nonzero(out); print('  first:', list(zip(xs.tolist(), ys.tolist()))[:12])
    print('mark lines still inside the marked area: %d px (must be 0); other red there: %d px (the app\'s own icons - look at them)' % (int(left.sum()), int(rr.sum()) - int(left.sum())))
    if a.twin:
        t = load(a.twin); d = np.abs(r - t).max(2)
        print('differs from the twin: %d px, largest difference %d of 255' % (int((d > 0).sum()), int(d.max())))
    print('GATE ' + ('PASSED' if not out.any() and not left.any() else 'FAILED'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd')
    p = sp.add_parser('marks'); p.add_argument('src')
    p = sp.add_parser('scan'); p.add_argument('files', nargs='+')
    p = sp.add_parser('judge'); p.add_argument('src'); p.add_argument('--box', required=True); p.add_argument('--donors', nargs='+', required=True)
    p.add_argument('--range', type=int, default=8); p.add_argument('--dy'); p.add_argument('--top', type=int, default=5)
    p = sp.add_parser('gate'); p.add_argument('marked'); p.add_argument('result'); p.add_argument('--twin')
    a = ap.parse_args()
    if not a.cmd: ap.print_help(); return
    {'marks': cmd_marks, 'scan': cmd_scan, 'judge': cmd_judge, 'gate': cmd_gate}[a.cmd](a)


if __name__ == '__main__':
    main()
