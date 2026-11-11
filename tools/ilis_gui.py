"""Dr.Explain .gui tools: read (info, page export), build from page files, image widths, cleanup.
Never load a .gui into the chat - use these commands."""
import base64, hashlib, io, json, re, uuid
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'assets' / 'ILISCyber_Template.gui'
ICONS = ROOT / 'assets' / 'icons'
MAXW = 1250

_E = [('&', '&A'), ('<', '&B'), ('>', '&C'), ('"', '&E'), ('\r', '&F'), ('\n', '&G')]
_U = {'&B': '<', '&C': '>', '&E': '"', '&F': '\r', '&G': '\n', '&A': '&'}


def esc(s):
    for a, b in _E: s = s.replace(a, b)
    return s


def unesc(s):
    return re.sub(r'&[ABCEFG]', lambda m: _U[m.group()], s)


# ------------------------------------------------------------------ reading
def load_tree(path):
    return ET.parse(path).getroot()


def _nodes(el, depth=0):
    pages = el.find('pages')
    if pages is None: return
    for n in pages:
        yield n, depth
        yield from _nodes(n, depth + 1)


def page_text(desc, limit=None):
    d = unesc(desc or '')
    t = re.findall(r'<item type = "normal"><!\[CDATA\[(.*?)\]\]>', d, re.S)
    txt = unesc(' '.join(x for x in t if x.strip()))
    return re.sub(r'\s+', ' ', txt).strip()[:limit] if limit else re.sub(r'\s+', ' ', txt).strip()


def info(path, text=80, depth=99):
    root = load_tree(path); out = []
    for n, dep in _nodes(root):
        if dep > depth: continue
        d = n.findtext('m_description') or ''
        u = unesc(d)
        full = len(re.findall(r'<add>0</add>', u)); inline = len(re.findall(r'<add>1</add>', u))
        st = n.findtext('page_state_flags/page_state_status') or ''
        line = '%s- %s  [%s, %d shots, %d icons]' % ('  ' * dep, n.findtext('m_title'), st, full, inline)
        if text: line += ' :: ' + page_text(d, text)
        out.append(line)
    return '\n'.join(out)


def find_node(root, title):
    hits = [n for n, _ in _nodes(root) if (n.findtext('m_title') or '').strip().lower() == title.strip().lower()]
    return hits


# ------------------------------------------------------------------ description -> markup (export)
def desc_to_markup(desc, img_dir, prefix):
    """Convert a page body to the markup used by `build`. Images are written to img_dir."""
    d = unesc(desc or '')
    img_dir = Path(img_dir); img_dir.mkdir(parents=True, exist_ok=True)
    lines = []; k = 0
    body = d.split('</item></p>', 1)[1] if 'title_region' in d else d
    for p in re.findall(r'<p>(.*?)</p>', body, re.S):
        align = re.search(r'<para_align>(\d)</para_align>', p)
        num = re.search(r'<para_numbering_level>(\d)</para_numbering_level>', p)
        parts = []
        heading = None
        for m in re.finditer(r'<font ([^>]*)>(.*?)</font>|<item type = "picture">(.*?)</item>', p, re.S):
            if m.group(3) is not None:
                pic = m.group(3)
                add = re.search(r'<add>(\d)</add>', pic).group(1)
                bits = re.search(r'<screen_bits><!\[CDATA\[(.*?)\]\]>', pic, re.S).group(1)
                w = int(re.search(r'<width>(\d+)</width>', pic).group(1))
                ow = int(re.search(r'<original_width>(\d+)</original_width>', pic).group(1))
                k += 1; fn = '%s_%02d.png' % (prefix, k)
                (img_dir / fn).write_bytes(base64.b64decode(bits))
                rel = (img_dir.name + '/' + fn)
                if add == '0':
                    parts.append(('IMG', rel, w, ow))
                else:
                    parts.append(('ICON', rel))
                continue
            attrs, inner = m.group(1), m.group(2)
            for t in re.findall(r'<item type = "normal"><!\[CDATA\[(.*?)\]\]>', inner, re.S):
                t = unesc(t)
                dd = re.search(r'd="(\w+)"', attrs).group(1); h = re.search(r'h="(\d+)"', attrs).group(1)
                bold = dd[0] == 'h'; under = len(dd) > 2 and dd[2] == 'b'
                parts.append(('T', t, bold, under, int(h)))
        # build line
        texts = [x for x in parts if x[0] == 'T']
        imgs = [x for x in parts if x[0] == 'IMG']
        if imgs and not texts and len(imgs) == 1 and not any(x[0] == 'ICON' for x in parts):
            _, rel, w, ow = imgs[0]
            lines.append('![](%s)' % rel if w == min(ow, MAXW) else '![w=%d](%s)' % (w, rel)); continue
        if texts and all(x[2] and x[3] for x in texts) and all(x[4] == 14 for x in texts) and not imgs:
            lines.append('## ' + ''.join(x[1] for x in texts).strip()); continue
        s = ''
        for x in parts:
            if x[0] == 'T':
                t = x[1]
                if x[2] and t.strip():
                    lead = t[:len(t) - len(t.lstrip())]; trail = t[len(t.rstrip()):]
                    s += lead + '**' + t.strip() + '**' + trail
                else: s += t
            elif x[0] == 'ICON': s += '{img:%s}' % x[1]
            else: s += '![](%s)' % x[1]
        sizes = {x[4] for x in texts}
        if sizes == {11}: s = '@11 ' + s
        if num: s = ('    ' * (int(num.group(1)) - 1)) + '1. ' + s
        if align and align.group(1) == '3' and s.strip(): s = '>> ' + s
        lines.append(s.rstrip())
    if lines and not lines[0]: lines.pop(0)   # the blank line under the title is added by build
    while lines and not lines[-1]: lines.pop()
    return '\n'.join(lines) + '\n'


def export_page(path, title, out_dir, root=None):
    root = root or load_tree(path)
    hits = find_node(root, title)
    if not hits: raise SystemExit('No page titled %r' % title)
    n = hits[0]; out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')[:60] or 'page'
    md = desc_to_markup(n.findtext('m_description'), out / 'img', slug)
    st = n.findtext('page_state_flags/page_state_status') or 'Not Started'
    (out / (slug + '.md')).write_text('---\ntitle: %s\nstatus: %s\n---\n%s' % (n.findtext('m_title'), st, md), encoding='utf-8')
    return out / (slug + '.md'), len(hits)


def export_all(path, out_dir):
    """Whole .gui -> project folder (outline.txt + pages/*.md + pages/img). Untouched pages are rebuilt
    byte-for-byte from the saved original (pages/raw)."""
    root = load_tree(path); out = Path(out_dir)
    (out / 'pages' / 'raw').mkdir(parents=True, exist_ok=True)
    outline = []; used = set()
    for n, dep in _nodes(root):
        if n.tag == 'index': continue
        title = n.findtext('m_title') or 'page'
        slug = re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')[:50] or 'page'; base = slug; i = 2
        while slug in used: slug = '%s_%d' % (base, i); i += 1
        used.add(slug)
        desc = n.findtext('m_description') or ''
        md = desc_to_markup(desc, out / 'pages' / 'img', slug)
        st = n.findtext('page_state_flags/page_state_status') or 'Not Started'
        text = '---\ntitle: %s\nstatus: %s\n---\n%s' % (title, st, md)
        (out / 'pages' / (slug + '.md')).write_text(text, encoding='utf-8')
        (out / 'pages' / 'raw' / (slug + '.txt')).write_text(desc, encoding='utf-8')
        (out / 'pages' / 'raw' / (slug + '.sha')).write_text(hashlib.sha1(text.encode('utf-8')).hexdigest())
        outline.append('  ' * (dep - 1 if dep else 0) + 'pages/%s.md' % slug)
    cover = root.find('pages/index')
    m = re.search(r'ILISCyber - ([^\]]*?) - ([^\]]*?)\]\]', unesc(cover.findtext('m_description') or '')) if cover is not None else None
    proj = {'main': m.group(1) if m else 'Main Module', 'sub': m.group(2) if m else 'Sub Module', 'template': str(Path(path).resolve()),
            'note': 'template = the original .gui, so its cover and settings are kept'}
    (out / 'project.json').write_text(json.dumps(proj, indent=1), encoding='utf-8')
    (out / 'outline.txt').write_text('\n'.join(outline) + '\n', encoding='utf-8')
    return len(outline)


# ------------------------------------------------------------------ building
def FONT(h=12, d='eaaaaa', sm=0, fc='Calibri', cl=0, si=0, ss='normal'):
    return '<font v="2" h="%d" w="0" chs="1" d="%s" fc="%s" cl="%d" si="%d" sm="%d" ss="%s">' % (h, d, fc, cl, si, sm, ss)


def _empty(font): return '<field id = "0" data = "NO_DATA">' + font + '</font></field>'


def _run(font, text): return '<field id = "0" data = "NO_DATA">' + font + '<item type = "normal"><![CDATA[' + esc(text) + ']]></item></font></field>'


def _para(inner, first_font, align=None, numbering=None):
    s = '<p>\n'
    if align: s += '<para_align>%d</para_align>' % align
    if numbering:
        s += ('<para_numbering_level>%d</para_numbering_level><para_numbering_type>1</para_numbering_type>'
              '<para_numbering_keep>1</para_numbering_keep><para_first_indent>%d</para_first_indent>'
              '<para_full_indent>%d</para_full_indent>') % (numbering, 50 * numbering, 50 * numbering)
    return s + _empty(first_font) + '<item type = "para_start"/>' + inner + '</p>\n'


def _png(path):
    p = Path(path)
    im = Image.open(p)
    if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGB')
    if p.suffix.lower() == '.png' and im.mode == 'RGB':
        data = p.read_bytes()
    else:
        im2 = im.convert('RGBA') if im.mode == 'RGBA' else im
        if im2.mode == 'RGBA':
            bg = Image.new('RGB', im2.size, 'white'); bg.paste(im2, mask=im2.split()[3]); im2 = bg
        b = io.BytesIO(); im2.save(b, 'PNG'); data = b.getvalue()
    return base64.b64encode(data).decode('ascii'), im.size


def _picture(path, inline, width=None):
    bits, (ow, oh) = _png(path)
    if inline:
        return ('<item type = "picture"><sealed>1</sealed><normal>1</normal><add>1</add><useprop>0</useprop><borderwidth>0</borderwidth>'
                '<margin_left>0</margin_left><margin_right>0</margin_right><margin_top>0</margin_top><margin_bottom>0</margin_bottom>'
                '<scalex>0.0100000000</scalex><scaley>0.0100000000</scaley><width>%d</width><height>%d</height>'
                '<screen_bits><![CDATA[%s]]></screen_bits>\r\n<original_width>%d</original_width><original_height>%d</original_height></item>') % (ow, oh, bits, ow, oh)
    w = width or min(ow, MAXW)
    h = round(oh * w / ow) if w != ow else oh
    sx, sy = (w / ow, h / oh) if w != ow else (1.0, 1.0)
    return ('<item type = "picture"><sealed>1</sealed><normal>1</normal><add>0</add><useprop>0</useprop><borderwidth>0</borderwidth>'
            '<margin_left>0</margin_left><margin_right>0</margin_right><margin_top>0</margin_top><margin_bottom>0</margin_bottom>'
            '<scalex>%.10f</scalex><scaley>%.10f</scaley><width>%d</width><height>%d</height>'
            '<screen_bits><![CDATA[%s]]></screen_bits>\r\n<original_width>%d</original_width><original_height>%d</original_height></item>') % (sx, sy, w, h, bits, ow, oh)


def _icon_path(name, base):
    p = ICONS / (name + '.png')
    if p.exists(): return p
    q = (base / name)
    if q.exists(): return q
    q = Path(name)
    if q.exists(): return q
    raise SystemExit('icon/image not found: %s (house icons: %s)' % (name, ', '.join(x.stem for x in ICONS.glob('*.png'))))


TOKEN = re.compile(r'(\*\*.+?\*\*|\{icon:[^}]+\}|\{img:[^}]+\}|!\[[^\]]*\]\([^)]+\))')


def _inline_runs(text, base, size=12):
    out = ''
    normal = FONT(size); bold = FONT(size, 'haaaaa')
    for tok in TOKEN.split(text):
        if not tok: continue
        if tok.startswith('**') and tok.endswith('**'): out += _run(bold, tok[2:-2])
        elif tok.startswith('{icon:'): out += _picture(_icon_path(tok[6:-1], base), True)
        elif tok.startswith('{img:'): out += _picture(_icon_path(tok[5:-1], base), True)
        elif tok.startswith('!['): out += _picture(_icon_path(re.search(r'\((.*)\)', tok).group(1), base), True)
        else: out += _run(normal, tok)
    return out


STEP = re.compile(r'^\s*\**\s*Step\s+(\d+)\s*\**\s*:\s*(.*)$')


def markup_to_body(md, base, title):
    """Page markup -> unescaped Dr.Explain body XML (para_group)."""
    base = Path(base)
    t = _run(FONT(16, 'haaaaa', 4250, 'Arial', 11558199, 1, 'h1'), title)
    first = FONT(12, sm=4490)
    title_region = ('<item type="title_region"><main_tag><![CDATA[page_title]]></main_tag>\r\n<para_group><p>\n<para_align>3</para_align>'
                    + _empty(FONT(16, 'haaaaa', 4250, 'Arial', 11558199, 1, 'h1')) + '<item type = "para_start"/>' + t + '</p>\n</para_group></item>')
    s = '<para_group>' + _para(_empty(first) + title_region, first, 3)
    s += _para('', FONT(12), 3)  # blank centred line under the title
    for raw in md.split('\n'):
        line = raw.rstrip('\r')
        if not line.strip():
            s += _para('', FONT(12)); continue
        m = re.match(r'^!\[(?:w=(\d+))?\]\(([^)]+)\)\s*$', line.strip())
        if m:
            s += _para(_empty(FONT(12)) + _picture(base / m.group(2), False, int(m.group(1)) if m.group(1) else None), FONT(12), 3); continue
        if line.startswith('## '):
            f = FONT(14, 'habaaa', 4234); s += _para(_run(f, line[3:]), f); continue
        if line.startswith('### '):
            f = FONT(12, 'haaaaa'); s += _para(_run(f, line[4:]), f); continue
        align = None; size = 12; numbering = None
        if line.startswith('>> '): align = 3; line = line[3:]
        mm = re.match(r'^( *)1\. (.*)$', line)
        if mm: numbering = len(mm.group(1)) // 4 + 1; line = mm.group(2)
        if line.startswith('@11 '): size = 11; line = line[4:]
        st = STEP.match(line)
        if st:
            b = FONT(size, 'haaaaa'); n = FONT(size)
            inner = _run(b, 'Step %s ' % st.group(1)) + _run(n, ': ') + _inline_runs(st.group(2), base, size)
            s += _para(inner, b, align, numbering); continue
        s += _para(_inline_runs(line, base, size), FONT(size, 'haaaaa') if line.startswith('**') else FONT(size), align, numbering)
    s += _para('', FONT(12))
    return s + '</para_group>'


def read_page(path):
    txt = Path(path).read_text(encoding='utf-8')
    meta = {}
    if txt.startswith('---'):
        _, fm, body = txt.split('---', 2)
        for l in fm.strip().splitlines():
            if ':' in l: k, v = l.split(':', 1); meta[k.strip()] = v.strip()
        body = body[1:] if body.startswith('\n') else body
    else: body = txt
    return meta, body


NODE = ('<module><uuid><![CDATA[{uuid}]]></uuid><m_topic><![CDATA[new_topic]]></m_topic><m_topic_auto>1</m_topic_auto><output_html>1</output_html>'
        '<sitemap_fields><priority>50</priority><changefreq><![CDATA[daily]]></changefreq><lastmod>0</lastmod></sitemap_fields>'
        '<output_chm>1</output_chm><output_rtf>1</output_rtf><output_pdf>1</output_pdf><output_epub>1</output_epub>'
        '<page_state_flags><page_state_readonly>0</page_state_readonly><page_state_comment><![CDATA[]]></page_state_comment>'
        '<page_state_status><![CDATA[{status}]]></page_state_status></page_state_flags><node_created>1</node_created>'
        '<has_auto_number>0</has_auto_number><m_show_header_and_footer>0</m_show_header_and_footer><m_has_page_number>1</m_has_page_number>'
        '<m_title><![CDATA[{title}]]></m_title><m_description><![CDATA[{desc}]]></m_description><links/><anchors/>'
        '<m_short_description><![CDATA[]]></m_short_description><alias><![CDATA[]]></alias><help_id>{hid}</help_id><m_alias_auto>1</m_alias_auto>'
        '<window_part><has_window_part>0</has_window_part></window_part><empty>0</empty>{children}</module>')


def _cdata(s): return s.replace(']]>', ']]]]><![CDATA[>')


def build(project_dir, out, skip_titles=('trouble shooting', 'troubleshooting')):
    """project_dir: project.json {main, sub, template?} + outline.txt (indented list of page files)."""
    P = Path(project_dir)
    proj = json.loads((P / 'project.json').read_text(encoding='utf-8')) if (P / 'project.json').exists() else {}
    tpl = Path(proj.get('template') or TEMPLATE)
    if not tpl.is_absolute() and not tpl.exists(): tpl = ROOT / tpl
    src = tpl.read_text(encoding='utf-8')
    i = src.index('<pages>'); j = src.index('</index>', i) + len('</index>'); k = src.rindex('</pages>')
    head, cover, tail = src[:i], src[i + 7:j], src[k:]
    main, sub = proj.get('main', 'Main Module'), proj.get('sub', 'Sub Module')
    if 'Main Module - Sub Module' in cover or 'Main Module - Sub Module' in head:
        cover = cover.replace('Main Module - Sub Module', '%s - %s' % (main, sub))
        head = head.replace('Main Module - Sub Module', '%s - %s' % (main, sub))
    # outline
    items = []
    for l in (P / 'outline.txt').read_text(encoding='utf-8').splitlines():
        if not l.strip() or l.strip().startswith('#'): continue
        items.append((len(l) - len(l.lstrip(' ')), l.strip()))
    levels = sorted({d for d, _ in items}); lv = {d: n for n, d in enumerate(levels)}
    tree = []; stack = [(-1, tree)]
    for d, f in items:
        node = {'file': f, 'children': []}
        while stack[-1][0] >= lv[d]: stack.pop()
        stack[-1][1].append(node); stack.append((lv[d], node['children']))
    hid = [1000]; count = [1]; problems = []

    def render(node):
        f = P / node['file']
        meta, body = read_page(f)
        title = meta.get('title') or f.stem
        if title.strip().lower() in skip_titles: problems.append('skipped Trouble shooting page: ' + node['file']); return ''
        raw = P / 'pages' / 'raw' / (f.stem + '.txt'); sha = P / 'pages' / 'raw' / (f.stem + '.sha')
        if raw.exists() and sha.exists() and hashlib.sha1(f.read_text(encoding='utf-8').encode('utf-8')).hexdigest() == sha.read_text().strip():
            desc = raw.read_text(encoding='utf-8')   # untouched page: original, byte for byte
        else:
            desc = esc(markup_to_body(body, f.parent, title))
        kids = ''.join(render(c) for c in node['children'])
        hid[0] += 1; count[0] += 1
        return NODE.format(uuid=str(uuid.uuid4()), status=meta.get('status', 'Not Started'), title=_cdata(title), desc=desc,
                           hid=hid[0], children='<pages>' + kids + '</pages>' if kids else '<pages/>')
    body = ''.join(render(n) for n in tree)
    cover_uuid = re.search(r'<uuid><!\[CDATA\[(.*?)\]\]>', cover).group(1)
    head = re.sub(r'(<selected_node_guid><!\[CDATA\[).*?(\]\]>)', lambda m: m.group(1) + cover_uuid + m.group(2), head)
    head = re.sub(r'<nodes_count>\d+</nodes_count>', '<nodes_count>%d</nodes_count>' % count[0], head)
    head = re.sub(r'<keywords>.*?</keywords>', '<keywords/>', head, flags=re.S)
    doc = head + '<pages>' + cover + body + tail
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(doc, encoding='utf-8', newline='')
    ET.fromstring(doc.encode('utf-8'))  # must parse
    return count[0], problems


# ------------------------------------------------------------------ 1250 px widths
def widths(src, dst, target=MAXW):
    s = Path(src).read_text(encoding='utf-8')
    T = lambda k: r'&B%s&C(\d+(?:\.\d+)?)&B/%s&C' % (k, k)
    pat = re.compile(r'(&Badd&C0&B/add&C.*?)' + T('scalex') + T('scaley') + T('width') + T('height')
                     + r'(.*?)' + T('original_width') + T('original_height'), re.S)
    stats = {'changed': 0, 'already': 0, 'smaller': 0}

    def rep(m):
        pre, sx, sy, w, h, mid, ow, oh = m.groups(); ow, oh = int(ow), int(oh)
        if ow < target: stats['smaller'] += 1; return m.group(0)
        nh = round(oh * target / ow)
        if int(w) == target and int(h) == nh: stats['already'] += 1; return m.group(0)
        stats['changed'] += 1
        return (pre + '&Bscalex&C%.10f&B/scalex&C&Bscaley&C%.10f&B/scaley&C&Bwidth&C%d&B/width&C&Bheight&C%d&B/height&C'
                % (target / ow, nh / oh, target, nh) + mid
                + '&Boriginal_width&C%d&B/original_width&C&Boriginal_height&C%d&B/original_height&C' % (ow, oh))
    out = pat.sub(rep, s)
    Path(dst).write_text(out, encoding='utf-8', newline='')
    ET.fromstring(out.encode('utf-8'))
    return stats


# ------------------------------------------------------------------ index (keywords)
KW_SEP = '-!$@@$$@~'   # Dr.Explain's separator between levels of a keyword path
KW_SKIP_TREE = re.compile(r'^\s*(How to|Accessing|Invoicing via)\b', re.I)   # manual: page and everything under it
KW_SKIP_PAGE = re.compile(r' - (Tabs|Functionalities)\s*$', re.I)            # both: the page only


def _kw_xml(nodes):
    if not nodes: return '<keywords/>'
    return '<keywords>' + ''.join('<keyword><m_title><![CDATA[%s]]></m_title>%s</keyword>' % (_cdata(n['title']), _kw_xml(n['kids']))
                                  for n in nodes) + '</keywords>'


def add_keywords(src, dst, mapping=False):
    """Index mirroring the topic tree: keyword = topic title, each topic linked to its own keyword (full path).
    Cover gets none; manuals skip How to / Accessing / Invoicing via (and their sub-pages); both skip
    '... - Tabs' / '... - Functionalities'. Existing keywords are replaced; everything else stays byte-for-byte."""
    if Path(src).resolve() == Path(dst).resolve(): raise SystemExit('DST must differ from SRC - the original is never edited.')
    s = Path(src).read_text(encoding='utf-8')
    # drop existing topic links
    s = re.sub(r'<keyword><!\[CDATA\[(?:(?!\]\]>).)*\]\]></keyword>', '', s, flags=re.S)
    # topics in document order with their depth (descriptions are escaped, so these tags are structural only)
    pages_at = s.index('<pages>')
    topics = []; depth = 0
    for m in re.finditer(r'<(module|index)>|</(module|index)>', s[pages_at:]):
        if m.group(1):
            pos = pages_at + m.start()
            t = re.search(r'<m_title><!\[CDATA\[(.*?)\]\]></m_title>', s[pos:pos + 5000], re.S)
            topics.append({'pos': pos, 'depth': depth, 'cover': m.group(1) == 'index',
                           'title': t.group(1).replace(']]]]><![CDATA[>', ']]>') if t else ''})
            depth += 1
        else: depth -= 1
    roots = []; stack = []   # stack of (topic depth, keyword node or None, skip subtree)
    links = {}; skipped = []
    for t in topics:
        while stack and stack[-1][0] >= t['depth']: stack.pop()
        if t['cover']: stack.append((t['depth'], None, False)); continue
        if any(x[2] for x in stack): skipped.append(t['title']); stack.append((t['depth'], None, True)); continue
        if not mapping and KW_SKIP_TREE.search(t['title']):
            skipped.append(t['title']); stack.append((t['depth'], None, True)); continue
        if KW_SKIP_PAGE.search(t['title']):
            skipped.append(t['title']); stack.append((t['depth'], None, False)); continue
        parent = next((x[1] for x in reversed(stack) if x[1] is not None), None)
        sibs = parent['kids'] if parent else roots
        node = next((n for n in sibs if n['title'] == t['title']), None)   # same title under same parent = one keyword
        if node is None:
            node = {'title': t['title'], 'kids': [], 'path': (parent['path'] + KW_SEP if parent else '') + t['title']}
            sibs.append(node)
        links[t['pos']] = node['path']
        stack.append((t['depth'], node, False))
    # insert links (from the end so positions stay valid)
    for pos in sorted(links, reverse=True):
        seg = s[pos:pos + 3000]
        m = re.search(r'<output_epub>\d</output_epub>', seg) or re.search(r'(?=<page_state_flags>)', seg)
        if not m: raise SystemExit('cannot place keyword link in topic at %d' % pos)
        at = pos + m.end()
        s = s[:at] + '<keyword><![CDATA[%s]]></keyword>' % _cdata(links[pos]) + s[at:]
    # replace the project keyword tree (in the header, before <pages>)
    head = s[:s.index('<pages>')]
    m = re.search(r'<keywords/>|<keywords>', head)
    if not m: raise SystemExit('no <keywords> block found in the project header')
    if m.group() == '<keywords/>': end = m.end()
    else:
        d = 0
        for tm in re.finditer(r'<keywords>|</keywords>|<keywords/>', s[m.start():]):
            if tm.group() == '<keywords>': d += 1
            elif tm.group() == '</keywords>': d -= 1
            if d == 0: end = m.start() + tm.end(); break
    s = s[:m.start()] + _kw_xml(roots) + s[end:]
    Path(dst).write_text(s, encoding='utf-8', newline='')
    ET.fromstring(s.encode('utf-8'))   # must parse

    def tree(nodes, lvl=0):
        return ''.join('%s- %s\n%s' % ('  ' * lvl, n['title'], tree(n['kids'], lvl + 1)) for n in nodes)
    return tree(roots).rstrip('\n'), len(links), skipped


def keywords_report(src, dst, mapping=False):
    tree, n, skipped = add_keywords(src, dst, mapping)
    return ('%s -> %s (%s rules)\nKeyword tree:\n%s\n%d topics linked; %d pages without keyword (besides the cover)%s'
            % (src, dst, 'mapping' if mapping else 'user manual', tree, n, len(skipped),
               (': ' + '; '.join(skipped)) if skipped else ''))


def remove_pages(src, dst, pattern):
    """Remove every page whose title matches pattern (regex, case-insensitive), with its children.
    Works on the raw text, so everything else in the file stays byte-for-byte the same."""
    s = Path(src).read_text(encoding='utf-8')
    rx = re.compile(pattern, re.I); removed = []
    while True:
        cut = None
        for m in re.finditer(r'<module>', s):
            t = re.match(r'<module><uuid><!\[CDATA\[[^\]]*\]\]></uuid>.*?<m_title><!\[CDATA\[(.*?)\]\]></m_title>', s[m.start():m.start() + 3000], re.S)
            if t and rx.search(t.group(1)):
                depth = 0
                for tm in re.finditer(r'<module>|</module>', s[m.start():]):
                    depth += 1 if tm.group() == '<module>' else -1
                    if depth == 0: cut = (m.start(), m.start() + tm.end(), t.group(1)); break
                break
        if not cut: break
        s = s[:cut[0]] + s[cut[1]:]; removed.append(cut[2])
    s = re.sub(r'<pages></pages>', '<pages/>', s)
    n = len(re.findall(r'<module>', s)) + 1
    s = re.sub(r'<nodes_count>\d+</nodes_count>', '<nodes_count>%d</nodes_count>' % n, s, count=1)
    Path(dst).write_text(s, encoding='utf-8', newline='')
    ET.fromstring(s.encode('utf-8'))
    return removed
