"""Recipe runner: a recipe is a JSON list of building-block steps. Saved recipes live in recipes/.
Values like "${name}" are filled from --set name=value or from earlier steps (as: name)."""
import json, re
from pathlib import Path
import ilis_img as I
import ilis_glyphs as G

ROOT = Path(__file__).resolve().parent.parent


def _sub(v, ctx):
    if isinstance(v, str):
        m = re.fullmatch(r'\$\{(\w+)\}', v)
        if m:
            if m.group(1) not in ctx: raise SystemExit('recipe needs a value for %s (use --set %s=...)' % (m.group(1), m.group(1)))
            return ctx[m.group(1)]
        return re.sub(r'\$\{(\w+)\}', lambda mm: str(ctx[mm.group(1)]) if mm.group(1) in ctx else mm.group(0), v)
    if isinstance(v, list): return [_sub(x, ctx) for x in v]
    if isinstance(v, dict): return {k: _sub(x, ctx) for k, x in v.items()}
    return v


def _box(v):
    if isinstance(v, str): return I.box_arg(v)
    return [int(round(float(x))) for x in v]


def _shift(b, dx, dy): return [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]


def pad(b, p): return [b[0] - p, b[1] - p, b[2] + p, b[3] + p]


def op_load(ctx, s): ctx[s['as']] = I.load(s['file'])
def op_save(ctx, s):
    I.save(ctx[s['img']], s['file']); ctx.setdefault('_saved', []).append(s['file'])
def op_clear_marks(ctx, s):
    im, n = I.clear_marks(ctx[s['img']], unborder=s.get('unborder', True)); ctx[s.get('as', s['img'])] = im
def op_strip_border(ctx, s):
    im, b = I.strip_border(ctx[s['img']]); ctx[s.get('as', s['img'])] = im
def op_dim(ctx, s): ctx[s.get('as', s['img'])] = I.dim(ctx[s['img']], s.get('factor', I.DIM))
def op_undim(ctx, s): ctx[s.get('as', s['img'])] = I.undim(ctx[s['img']], s.get('factor', I.DIM))
def op_border(ctx, s):
    im = ctx[s['img']]; ctx[s.get('as', s['img'])] = I.add_border(im, fill=I.GREY_PAD if I.is_dimmed(im) else 'white')


def op_copy_popup(ctx, s):
    """Copy the pop-up / alert of a dimmed donor screenshot onto the target (aligned on the screen)."""
    donor, tgt = ctx[s['from']], ctx[s['to']]
    src_box = _box(s['region']) if s.get('region') else I.overlay_box(donor)
    dx, dy, err = I.align(donor, tgt, src_box)
    if s.get('place') == 'center':
        w, h = src_box[2] - src_box[0], src_box[3] - src_box[1]
        dx = (tgt.width - w) // 2 - src_box[0]; dy = (tgt.height - h) // 2 - src_box[1]
    ctx[s.get('as', s['to'])] = I.paste_region(tgt, donor, src_box, dx, dy)
    ctx[s.get('box_as', 'popup')] = _shift(src_box, dx, dy)
    ctx[s.get('donor_box_as', 'donor_popup')] = src_box
    ctx['_dx'], ctx['_dy'] = dx, dy
    ctx['_log'].append('popup %s -> %s (align error %.4f)' % (src_box, ctx[s.get('box_as', 'popup')], err))


def op_copy_region(ctx, s):
    donor, tgt = ctx[s['from']], ctx[s['to']]
    if s.get('color'):
        src_box = I.color_box(donor, s['color'], s.get('tol', 40))
        if not src_box: raise SystemExit('colour %s not found in donor' % s['color'])
        src_box = pad(src_box, s.get('pad', 1))
    else: src_box = _box(s['region'])
    mode = s.get('align', 'auto')
    piece = donor.crop((src_box[0], src_box[1], src_box[2] + 1, src_box[3] + 1))
    if mode == 'auto': dx, dy, _ = I.align(donor, tgt, src_box)
    elif mode == 'bottom':
        # same distance from the bottom/left edge; a full-width bar is stretched to the new screen width
        dx = 0; dy = tgt.height - donor.height
        right_gap = donor.width - 1 - src_box[2]
        new_w = tgt.width - right_gap - src_box[0]
        if new_w != piece.width and new_w > 120:
            L, Rr = 60, 40
            mid = piece.crop((L, 0, piece.width - Rr, piece.height)).resize((new_w - L - Rr, piece.height))
            p2 = I.Image.new('RGB', (new_w, piece.height)); p2.paste(piece.crop((0, 0, L, piece.height)), (0, 0))
            p2.paste(mid, (L, 0)); p2.paste(piece.crop((piece.width - Rr, 0, piece.width, piece.height)), (new_w - Rr, 0)); piece = p2
    else: dx, dy = s.get('offset', [0, 0])
    out = tgt.copy(); out.paste(piece, (src_box[0] + dx, src_box[1] + dy)); ctx[s.get('as', s['to'])] = out
    src_box = [src_box[0], src_box[1], src_box[0] + piece.width - 1, src_box[3]]
    ctx[s.get('box_as', 'region')] = _shift(src_box, dx, dy)
    ctx[s.get('donor_box_as', 'donor_region')] = src_box
    ctx['_dx'], ctx['_dy'] = dx, dy


def op_text_blocks(ctx, s):
    blocks = I.text_lines(ctx[s['img']], _box(s['region']))
    which = s.get('pick', 'widest')
    if not blocks: raise SystemExit('no text found in %s' % s['region'])
    if which == 'widest': b = max(blocks, key=lambda b: b[2] - b[0])
    elif which == 'first': b = blocks[0]
    elif which == 'last': b = blocks[-1]
    else: b = blocks[int(which)]
    ctx[s['as']] = b
    ctx['_log'].append('text blocks %s -> picked %s' % (blocks, b))


def op_shift(ctx, s):
    ctx[s['as']] = _shift(_box(ctx[s['box']] if isinstance(s['box'], str) and s['box'] in ctx else s['box']),
                          s.get('dx', ctx.get('_dx', 0)), s.get('dy', ctx.get('_dy', 0)))


def op_learn(ctx, s):
    F = G.Font(s['font']); b = pad(_box(s['box']), s.get('pad', 2))
    r = F.learn(ctx[s['img']], [b[0], b[1] - 1, b[2], b[3] + 1], s['text'], bold=s.get('bold'))
    ctx['_log'].append('learned %s: %s' % (s['font'], ''.join(r.get('learned', []))) + (' WARN ' + '; '.join(r['warnings']) if r.get('warnings') else ''))


def op_replace_text(ctx, s):
    """Erase the text inside `box` and write `text` at the same place (same left edge / centre and baseline).
    If old_text is given, its letters are learned first."""
    im = ctx[s['img']]; F = G.Font(s['font'])
    b = _box(s['box'])
    ref = ctx[s['ref_img']] if s.get('ref_img') else im
    ref_box = _box(s['ref_box']) if s.get('ref_box') else b
    if s.get('old_text'):
        rb = pad(ref_box, 2)
        r = F.learn(ref, [rb[0], rb[1] - 1, rb[2], rb[3] + 1], s['old_text'], bold=s.get('bold'))
        ctx['_log'].append('learned %s from old text: %s' % (s['font'], ''.join(r.get('learned', []))) + (' WARN ' + '; '.join(r['warnings']) if r.get('warnings') else ''))
    ink = I.ink_bbox(im, pad(b, 2)) or b
    base = F.baseline_of(im, pad(ink, 2))
    area = s.get('erase') and _box(s['erase']) or [ink[0] - 2, ink[1] - 3, ink[2] + 2, ink[3] + 3]
    im = I.erase(im, area, s.get('bg'))
    align = s.get('align', 'left')
    if align == 'center':
        cb = _box(s.get('center_in', b)); out, w, miss = F.write(im, s['text'], cb[0], base, s.get('color'), 'center', cb[2] - cb[0])
    elif align == 'right':
        out, w, miss = F.write(im, s['text'], ink[2] - 0, base, s.get('color'), 'right', 0)
    else:
        out, w, miss = F.write(im, s['text'], ink[0], base, s.get('color'))
    if miss: ctx['_log'].append('WARNING letters not in the %s library, drawn with Arial: %s' % (s['font'], ''.join(sorted(set(miss)))))
    ctx[s.get('as', s['img'])] = out


def op_write(ctx, s):
    F = G.Font(s['font'])
    out, w, miss = F.write(ctx[s['img']], s['text'], int(s['x']), int(s['baseline']), s.get('color'), s.get('align', 'left'), s.get('width'))
    if miss: ctx['_log'].append('WARNING letters drawn with Arial: %s' % ''.join(sorted(set(miss))))
    ctx[s.get('as', s['img'])] = out


def op_erase(ctx, s): ctx[s.get('as', s['img'])] = I.erase(ctx[s['img']], _box(s['box']), s.get('color'))


def op_paste(ctx, s):
    """Paste a crop file (or a region of another image) at a position."""
    piece = I.load(s['file']) if s.get('file') else ctx[s['from']].crop(tuple(_box(s['region'])))
    im = ctx[s['img']].copy(); im.paste(piece, tuple(int(v) for v in s['at'])); ctx[s.get('as', s['img'])] = im


def op_mark(ctx, s):
    tmp = ROOT / 'work' / '_recipe_tmp.png'; I.save(ctx[s['img']], tmp)
    I.mark(tmp, tmp, s['spec'], coords='bordered'); ctx[s.get('as', s['img'])] = I.load(tmp)


OPS = {k[3:]: v for k, v in globals().items() if k.startswith('op_')}


def run(recipe_file, values):
    R = json.loads(Path(recipe_file).read_text(encoding='utf-8'))
    ctx = dict(R.get('defaults', {})); ctx.update(values); ctx['_log'] = []
    for name, desc in R.get('inputs', {}).items():
        if name not in ctx: raise SystemExit('missing input %s: %s  (use --set %s=...)' % (name, desc, name))
    for i, step in enumerate(R['steps']):
        s = _sub(step, ctx)
        op = s.pop('op')
        if op not in OPS: raise SystemExit('unknown op %s (known: %s)' % (op, ', '.join(sorted(OPS))))
        OPS[op](ctx, s)
    return ctx.get('_saved', []), ctx['_log']
