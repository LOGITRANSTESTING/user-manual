#!/usr/bin/env python3
"""ILISCyber manual / mapping toolkit.  Run:  python tools/ilis.py <command> -h

Screenshots
  prep SRC DST [--side]             grey side crop + house border (+ grey padding if dimmed)
  crop SRC DST --box | --text | --find   inline button/icon crop (from the UNMARKED screenshot)
  find SRC --text "Process" | --crop f.png | --red | --popup | --lines BOX | --color R,G,B
  snap SRC --box x0,y0,x1,y1        tighten a rough box to the UI element
  grid SRC DST                       coordinate grid overlay (to read positions)
  mark SRC DST --spec spec.json      red boxes + numbered circles (automatic placement)
  clear SRC DST                      remove old boxes/numbers (+ border)
  patch SRC DST --donor D --box B    rebuild a smudged spot from a similar unmarked screenshot
  to-mapping SRC DST                 mapping style: remove border + numbers, keep boxes
  learn SRC --box B --text T --font NAME [--bold]    add real letters to the letter library
  write SRC DST --font NAME --text T (--replace BOX [--old-text T] [--align center] | --at X,BASELINE)
  erase SRC DST --box B [--color R,G,B]
  dim / undim SRC DST
  recipe list | recipe run FILE --set k=v ...      build images from saved recipes
  fonts                              list the letter library
  preview FILES... --out sheet.png   one sheet for the user to check (opened in VS Code)
Dr.Explain files
  gui info FILE [--text N] [--depth N]   tree summary (never open a .gui directly)
  gui page FILE --title T --out DIR       export one page as markup + images
  gui export FILE --out DIR               whole manual -> project folder (lossless for untouched pages)
  gui build DIR --out FILE.gui            project folder -> .gui
  gui widths SRC DST                      every full screenshot 1250 px wide (properties only)
  gui remove SRC DST --match REGEX        delete pages by title (e.g. "Trouble ?shooting")
  gui keywords SRC DST [--mapping]        index (keywords) mirroring the topic tree (house rules)
"""
import argparse, json, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ilis_img as I, ilis_glyphs as G, ilis_gui as U, ilis_recipe as R

ROOT = Path(__file__).resolve().parent.parent


def show(path, args):
    print('PREVIEW:', path)
    if not getattr(args, 'no_open', False): I.open_in_editor(path)


def main():
    try: sys.stdout.reconfigure(errors='replace')
    except Exception: pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--no-open', action='store_true', help='do not open previews in VS Code')
    sp = ap.add_subparsers(dest='cmd')

    p = sp.add_parser('prep'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--side', action='store_true', help='side-function shot: no grey side crop')
    p.add_argument('--no-crop', action='store_true'); p.add_argument('--no-border', action='store_true')
    p = sp.add_parser('crop'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--box'); p.add_argument('--text'); p.add_argument('--pad', type=int, default=0)
    p.add_argument('--snap', action='store_true', help='tighten --box to the button edge first')
    p = sp.add_parser('find'); p.add_argument('src'); p.add_argument('--text'); p.add_argument('--crop'); p.add_argument('--red', action='store_true')
    p.add_argument('--popup', action='store_true'); p.add_argument('--lines'); p.add_argument('--color'); p.add_argument('--region')
    p.add_argument('--button', action='store_true', help='with --text: return the whole button/menu item box')
    p = sp.add_parser('snap'); p.add_argument('src'); p.add_argument('--box', required=True)
    p = sp.add_parser('grid'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--step', type=int, default=50)
    p = sp.add_parser('mark'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--spec', required=True, help='JSON file or JSON text')
    p.add_argument('--coords', default='raw', choices=['raw', 'bordered'], help='raw = coordinates on the original screenshot (default)')
    p = sp.add_parser('clear'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--keep-border', action='store_true')
    p = sp.add_parser('to-mapping'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--donor', help='unmarked screenshot of the same screen to repair circle spots')
    p = sp.add_parser('patch'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--donor', required=True); p.add_argument('--box', required=True)
    p = sp.add_parser('learn'); p.add_argument('src'); p.add_argument('--box', required=True); p.add_argument('--text', required=True)
    p.add_argument('--font', required=True); p.add_argument('--bold', action='store_true')
    p = sp.add_parser('write'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--font', required=True); p.add_argument('--text', required=True)
    p.add_argument('--replace'); p.add_argument('--old-text'); p.add_argument('--align', default='left'); p.add_argument('--at'); p.add_argument('--color')
    p = sp.add_parser('erase'); p.add_argument('src'); p.add_argument('dst'); p.add_argument('--box', required=True); p.add_argument('--color')
    for c in ('dim', 'undim'):
        p = sp.add_parser(c); p.add_argument('src'); p.add_argument('dst')
    p = sp.add_parser('recipe'); p.add_argument('action', choices=['list', 'run', 'show']); p.add_argument('file', nargs='?')
    p.add_argument('--set', action='append', default=[], help='name=value')
    sp.add_parser('fonts')
    p = sp.add_parser('preview'); p.add_argument('files', nargs='+'); p.add_argument('--out', required=True); p.add_argument('--labels')
    p = sp.add_parser('gui'); p.add_argument('action', choices=['info', 'page', 'export', 'build', 'widths', 'remove', 'keywords'])
    p.add_argument('src'); p.add_argument('dst', nargs='?'); p.add_argument('--title'); p.add_argument('--out'); p.add_argument('--text', type=int, default=80)
    p.add_argument('--depth', type=int, default=99); p.add_argument('--match')
    p.add_argument('--mapping', action='store_true', help='keywords: mapping document rules')
    a = ap.parse_args()
    if not a.cmd: ap.print_help(); return

    if a.cmd == 'prep':
        m = I.prep(a.src, a.dst, side=a.side, border=not a.no_border, crop=not a.no_crop)
        print(json.dumps(m)); return
    if a.cmd == 'crop':
        meta = I.sidecar(a.src)
        if meta.get('marked'): sys.exit('REFUSED: %s is a marked image. Crop buttons from the original, unmarked screenshot.' % a.src)
        im = I.load(a.src)
        if a.text:
            hits = I.find_text(im, a.text)
            if not hits: sys.exit('text not found: %s' % a.text)
            b = I.button_box(im, hits[0])
        else:
            b = I.box_arg(a.box)
            if a.snap: b = I.snap(im, b); b = [b[0] + 3, b[1] + 3, b[2] - 3, b[3] - 3]
        b = [b[0] - a.pad, b[1] - a.pad, b[2] + a.pad, b[3] + a.pad]
        I.save(im.crop((b[0], b[1], b[2] + 1, b[3] + 1)), a.dst); print('crop', b, '->', a.dst); return
    if a.cmd == 'find':
        im = I.load(a.src); reg = I.box_arg(a.region) if a.region else None
        if a.text:
            hits = I.find_text(im, a.text, reg)
            print(json.dumps([I.button_box(im, h) for h in hits] if a.button else hits))
        elif a.crop: print(json.dumps(I.find_crop(im, a.crop)))
        elif a.red: print(json.dumps(I.find_red_boxes(im)))
        elif a.popup: print(json.dumps(I.overlay_box(im)))
        elif a.lines: print(json.dumps(I.text_lines(im, I.box_arg(a.lines))))
        elif a.color: print(json.dumps(I.color_box(im, [int(v) for v in a.color.split(',')])))
        return
    if a.cmd == 'snap': print(json.dumps(I.snap(I.load(a.src), I.box_arg(a.box)))); return
    if a.cmd == 'grid': I.save(I.grid(I.load(a.src), a.step), a.dst); show(a.dst, a); return
    if a.cmd == 'mark':
        inline = a.spec.lstrip().startswith(('[', '{'))
        spec = json.loads(a.spec) if inline else json.loads(Path(a.spec).read_text())
        for l in I.mark(a.src, a.dst, spec, coords=a.coords): print('step %s: %s at (%d,%d)' % (l[0], l[1], l[2], l[3]))
        show(a.dst, a); return
    if a.cmd == 'clear':
        src = I.load(a.src); im, n = I.clear_marks(src, unborder=not a.keep_border); I.save(im, a.dst); print('cleared', n, 'px')
        sb, _ = I.strip_border(src) if not a.keep_border else (src, 0)
        spots = [(c[0], c[1]) for c in I.find_circles(np.array(sb), I.red_mask(np.array(sb)))]
        sheet = I.spot_sheet(sb, im, spots, str(Path(a.dst).with_name(Path(a.dst).stem + '_check.png')))
        if sheet: print('CHECK the old number spots (left = before, right = after):', spots)
        show(sheet or a.dst, a); return
    if a.cmd == 'to-mapping':
        src = I.load(a.src); im, spots, b = I.strip_numbers(src)
        if a.donor:
            for (x, y) in spots:
                im, sc = I.patch_from_similar(im, I.load(a.donor), [x - 17, y - 17, x + 18, y + 18]); print('patched (%d,%d) score %.3f' % (x, y, sc))
        I.save(im, a.dst)
        before, _ = I.strip_border(src)
        sheet = I.spot_sheet(before, im, spots, str(Path(a.dst).with_name(Path(a.dst).stem + '_check.png')))
        print('removed %d numbers at %s, border %d px' % (len(spots), spots, b))
        if sheet: print('CHECK the spots (left = before, right = after):'); show(sheet, a)
        return
    if a.cmd == 'patch':
        im, sc = I.patch_from_similar(I.load(a.src), I.load(a.donor), I.box_arg(a.box)); I.save(im, a.dst)
        print('match score %.3f %s' % (sc, '(patched)' if sc >= 0.9 else '(NOT patched - no reliable match)')); return
    if a.cmd == 'learn':
        r = G.Font(a.font).learn(I.load(a.src), I.box_arg(a.box), a.text, bold=a.bold or None); print(json.dumps(r)); return
    if a.cmd == 'write':
        im = I.load(a.src); ctx = {'img': im, '_log': []}
        if a.replace:
            s = {'img': 'img', 'font': a.font, 'box': a.replace, 'text': a.text, 'align': a.align}
            if a.old_text: s['old_text'] = a.old_text
            if a.color: s['color'] = [int(v) for v in a.color.split(',')]
            R.op_replace_text(ctx, s)
        else:
            x, base = [int(v) for v in a.at.split(',')]
            R.op_write(ctx, {'img': 'img', 'font': a.font, 'text': a.text, 'x': x, 'baseline': base})
        I.save(ctx['img'], a.dst); print('\n'.join(ctx['_log'])); show(a.dst, a); return
    if a.cmd == 'erase':
        I.save(I.erase(I.load(a.src), I.box_arg(a.box), [int(v) for v in a.color.split(',')] if a.color else None), a.dst); return
    if a.cmd in ('dim', 'undim'):
        I.save((I.dim if a.cmd == 'dim' else I.undim)(I.load(a.src)), a.dst); return
    if a.cmd == 'recipe':
        if a.action == 'list':
            for f in sorted((ROOT / 'recipes').glob('*.json')):
                r = json.loads(f.read_text(encoding='utf-8')); print('%s: %s\n   inputs: %s' % (f.name, r.get('description', ''), ', '.join(r.get('inputs', {}))))
            return
        if a.action == 'show': print(Path(a.file).read_text(encoding='utf-8')); return
        vals = dict(kv.split('=', 1) for kv in a.set)
        saved, log = R.run(a.file, vals)
        print('\n'.join(log))
        for f in saved: print('SAVED:', f)
        if saved:
            pv = str(Path(saved[-1]).with_name(Path(saved[-1]).stem + '_preview.png'))
            I.preview(saved, pv); show(pv, a)
        return
    if a.cmd == 'fonts':
        for k, v in G.list_fonts().items(): print('%s: %s  (+%d words) %s' % (k, v['letters'], v['words'], v['note']))
        return
    if a.cmd == 'preview':
        I.preview(a.files, a.out, a.labels.split('|') if a.labels else None); show(a.out, a); return
    if a.cmd == 'gui':
        if a.action == 'info': print(U.info(a.src, a.text, a.depth)); return
        if a.action == 'page':
            f, n = U.export_page(a.src, a.title, a.out); print('exported', f, '' if n == 1 else '(%d pages share this title; first one exported)' % n); return
        if a.action == 'export': print('exported %d pages to %s' % (U.export_all(a.src, a.out), a.out)); return
        if a.action == 'build':
            n, probs = U.build(a.src, a.out); print('built %s with %d topics' % (a.out, n)); print('\n'.join(probs))
            print(U.info(a.out, 60)); return
        if a.action == 'widths': print(json.dumps(U.widths(a.src, a.dst))); return
        if a.action == 'remove': print('removed:', U.remove_pages(a.src, a.dst, a.match)); return
        if a.action == 'keywords': print(U.keywords_report(a.src, a.dst, a.mapping)); return


if __name__ == '__main__':
    main()
