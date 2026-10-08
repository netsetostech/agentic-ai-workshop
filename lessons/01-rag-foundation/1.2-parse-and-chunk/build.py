import json, re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.2"


title = "<title>Lesson 1.2 Parse documents and compare chunk boundaries - pages, sections, and the cut that decides retrieval | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.bx-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;}
.bx-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;}
.bx-l select,.bx-l input[type=text]{font:inherit;font-size:var(--small-size);padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);}
.bx-l input[type=range]{width:100%;}
.bx-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 8px;}
.bx-out{display:flex;flex-wrap:wrap;gap:8px;}
.bx-chunk{flex:1 1 220px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;color:var(--slate);}
.bx-chunk b{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);margin-bottom:4px;}
.bx-chunk.hit{border:2px solid var(--teal);background:var(--teal-light);}
.bx-chunk mark{background:#fde68a;color:#1f2937;padding:0 2px;border-radius:2px;}
.bx-chunk .ov{background:#e0f2fe;}
/* the road each file takes: landscape above the 640px rung, portrait below it, never a shrunken landscape */
.pr-dg svg text{font-family:inherit;}
.pr-wide{--svg-min:600px;overflow-x:auto;overscroll-behavior-x:contain;min-width:0;}
.pr-wide svg{display:block;width:100%;min-width:var(--svg-min);max-width:760px;height:auto;margin:0 auto;}
.pr-tall{display:none;}
.pr-tall svg{display:block;width:100%;max-width:440px;height:auto;margin:0 auto;}
@media (max-width:640px){.pr-wide{display:none;}.pr-tall{display:block;}}
"""

# the setup section, shared with 3.1 (from its heading to the tenant step marker)
setup = setup_section()
setup = setup.replace("once before step 3 and once after step 9", "once before step 3 and once after step 9")

# the explorer's two samples, taken from the kit's own corpus
hb = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
heads = [m.start() for m in re.finditer(r"^## ", hb, re.M)]
hb_sample = hb[:heads[5]].strip()                     # the preamble and the first five clauses
wg = (KIT / "evals/corpus/acme/code_on_wages_2019.md").read_text(encoding="utf-8")
page9 = wg.split("\f")[8]
page9 = re.sub(r"\A\s*<!--.*?-->\s*", "", page9, flags=re.S).strip()
act_sample = page9[:1500].rsplit(". ", 1)[0] + "."

JS = """<script>
(function(){
  'use strict';
  var SAMPLES = {hb: %s, act: %s};
  var root = document.getElementById('explorer'); if (!root) return;
  var sel = document.getElementById('bx-sample'), rule = document.getElementById('bx-rule'),
      size = document.getElementById('bx-size'), ov = document.getElementById('bx-ov'),
      q = document.getElementById('bx-q'), out = document.getElementById('bx-out'), sum = document.getElementById('bx-sum'),
      sizeV = document.getElementById('bx-size-v'), ovV = document.getElementById('bx-ov-v');
  var CODE = /^([A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,6}){1,2})\\b/;
  function windows(text, n, o){                      /* the kit's _windows(), with the size and overlap as parameters */
    text = text.trim(); var res = [], start = 0;
    while (start < text.length){
      var end = Math.min(text.length, start + n);
      if (end < text.length){ var cut = text.lastIndexOf('. ', end); if (cut >= start + Math.floor(n / 2)) end = cut + 1; }
      var piece = text.slice(start, end).trim();
      if (piece) res.push({text: piece, start: start});
      if (end >= text.length) break;
      start = Math.max(end - o, start + 1);
    }
    return res;
  }
  function chunk(text, mode, n, o){
    var lines = text.split('\\n'), heads = [];
    lines.forEach(function(l, i){ if (/^## +/.test(l)) heads.push(i); });
    var outc = [];
    if (mode !== 'win' && heads.length){
      var pre = lines.slice(0, heads[0]).join('\\n').trim();
      windows(pre, n, o).forEach(function(w, k){ outc.push({loc: 'preamble' + (k ? '-' + k : ''), text: w.text}); });
      heads.forEach(function(h, j){
        var title = lines[h].replace(/^## +/, '').trim();
        var body = lines.slice(h + 1, j + 1 < heads.length ? heads[j + 1] : lines.length).join('\\n').trim();
        var m = CODE.exec(title), key = m ? m[1] : 's' + (j + 1);
        windows(title + '\\n' + body, n, o).forEach(function(w, k){ outc.push({loc: key + (k ? '-' + k : ''), text: w.text}); });
      });
    } else {
      windows(text, n, o).forEach(function(w, k){ outc.push({loc: 'w' + k, text: w.text}); });
    }
    return outc;
  }
  function esc(t){ return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function render(){
    var text = SAMPLES[sel.value], n = parseInt(size.value, 10), o = parseInt(ov.value, 10);
    sizeV.textContent = n; ovV.textContent = o;
    var cs = chunk(text, rule.value, n, o), needle = q.value.trim().toLowerCase(), hits = 0;
    out.innerHTML = cs.map(function(c){
      var body = esc(c.text), hit = needle && c.text.toLowerCase().indexOf(needle) !== -1;
      if (hit){ hits++; var re = new RegExp(needle.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), 'ig'); body = body.replace(re, function(m){ return '<mark>' + m + '</mark>'; }); }
      return '<div class="bx-chunk' + (hit ? ' hit' : '') + '"><b>' + esc(c.loc) + ' · ' + c.text.length + ' chars</b>' + body + '</div>';
    }).join('');
    var mode = (rule.value !== 'win' && /^## +/m.test(text)) ? 'by section' : 'by window';
    sum.textContent = cs.length + ' chunks, cut ' + mode + (needle ? ' · "' + q.value.trim() + '" is in ' + hits + ' chunk' + (hits === 1 ? '' : 's') : '');
  }
  [sel, rule, size, ov].forEach(function(el){ el.addEventListener('input', render); el.addEventListener('change', render); });
  q.addEventListener('input', render);
  render();
})();
</script>
""" % (json.dumps(hb_sample), json.dumps(act_sample))

# ------------------------------------------------------------------ step 1: the road each kind of file takes
# Two drawings of one flow from ROUTES: landscape for the page, portrait under the page's 640px rung (CSS), so a phone
# never shrinks 11-unit labels below the 9px floor. Every fact they show is read off the kit here.
import html as _html  # noqa: E402
from pypdf import PdfReader  # noqa: E402
ING, PAR, CON, IDEM, MK = ((KIT / p).read_text(encoding="utf-8") for p in (
    "services/ingest/main.py", "services/ingest/parser.py", "services/ingest/contracts.py", "services/ingest/idempotency.py", "Makefile"))
assert 'raise ValueError("object is not under a tenant prefix")' in CON                        # refused: no tenant folder
assert '"event":"ingest_duplicate"' in IDEM                                                     # the same bytes: no new work
assert 'if content_type.startswith("text/"):' in ING and "Plain text needs no processor" in ING   # text is read as it is
assert "MAX_INLINE_PAGES = 250" in ING and "ONLINE_PAGE_LIMIT = 15" in PAR and "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200" in ING
assert ('MEDIA_TYPES = {"image/png": "figure", "image/jpeg": "figure",\n'
        '               "video/mp4": "segment", "audio/mpeg": "segment"}') in ING                  # Gemini describes media
IDX = ING[ING.index("def index_document("):]
assert IDX.index("_pdf_pages(content)") < IDX.index("_parse(content") < IDX.index("pii_inspect_many(") < IDX.index("upsert(INDEX_NAME")
assert '"india": {"location": "asia-south1", "type": "OCR_PROCESSOR"}' in PAR and '"LAYOUT_PARSER_PROCESSOR"' in PAR
assert "RESIDENCY     ?= us" in MK                                                               # make up's reader
PAGES = {n: len(PdfReader(str(KIT / f"evals/corpus/acme/{n}.pdf")).pages)
         for n in ("code_on_wages_2019", "posh_act_2013", "cgst_act_2017", "it_act_2000")}
SLICES = lambda p: -(-p // 15)  # noqa: E731
assert PAGES["code_on_wages_2019"] == 29 and PAGES["posh_act_2013"] == 13
assert PAGES["cgst_act_2017"] + PAGES["it_act_2000"] == 270                                      # lesson 4.1's joined PDF
assert len(re.findall(r"^## ", hb, re.M)) + 1 == 283                                            # 282 clauses and the preamble
assert (KIT / "evals/corpus/acme/inv_2026_0412.png").is_file()
V161 = (Path(__file__).resolve().parents[2] / "07-graph-multimodal/7.5-video-clip/parts/a.html").read_text(encoding="utf-8")
assert "townhall_2026_q1.mp4" in V161 and "[Clip N, mm:ss]" in V161

wages, posh = PAGES["code_on_wages_2019"], PAGES["posh_act_2013"]
ROUTES = [  # type, its detail, how it is read, its detail, example file, what it becomes, style (t read, s stops or waits)
    ("Markdown, text", ".md, .txt", "Read directly", "no parser, no cost", "hr_policy_2026.md", "283 clause chunks", "t"),
    ("Normal PDF", "250 pages or fewer", "Document AI", "in 15-page slices", "code_on_wages_2019.pdf",
     f"{wages} pages: {SLICES(wages)} slices", "t"),
    ("Big PDF", "over 250 pages", "Batch lane", "queued, parsed later", "270-page bundle", "lesson 1.5's joined PDF waits", "s"),
    ("Scanned PDF", "no text layer", "Document AI", "reads the page images", "posh_act_2013.pdf",
     f"{posh} pages: {SLICES(posh)} slice", "t"),
    ("Image", ".png, .jpg", "Gemini caption", "the picture becomes text", "inv_2026_0412.png", "1 figure chunk", "t"),
    ("Video, audio", ".mp4, .mp3", "Gemini segments", "timed, start and end", "townhall_2026_q1.mp4", "cited as [Clip N, mm:ss]", "t"),
]
FILLS = {"t": ("#ccfbf1", "#0d9488", ""), "s": ("#fff7ed", "#c2410c", ' stroke-dasharray="4 3"'), "n": ("#ffffff", "#64748b", "")}


def _rect(x, y, w, h, kind):
    f, s, d = FILLS[kind]
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{f}" stroke="{s}" stroke-width="1"{d}/>'


def _text(x, y, s, size=13, weight="", mono=False, fill="#0f1729"):
    extra = (f' font-weight="{weight}"' if weight else "") + (' font-family="JetBrains Mono,monospace"' if mono else "")
    return f'<text x="{x}" y="{y}" font-size="{size}"{extra} fill="{fill}">{_html.escape(s, quote=False)}</text>'


def _node(x, y, w, h, kind, title, sub=None, mono=False):
    if sub is None:
        return _rect(x, y, w, h, kind) + _text(x + 12, y + h // 2 + 5, title, 13, "500")
    return (_rect(x, y, w, h, kind) + _text(x + 12, y + h // 2 - 3, title, 12 if mono else 13, "" if mono else "500", mono)
            + _text(x + 12, y + h // 2 + 13, sub, 11, fill="#475569"))


def _arrow(x1, y1, x2, y2, key):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#475569" stroke-width="1.5" marker-end="url(#{key}A)"/>'


def _svg(w, h, key, body):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{key}T {key}D">'
            f'<title id="{key}T">The road each kind of file takes, from upload to chunks</title>'
            f'<desc id="{key}D">An upload outside a tenant folder is refused and bytes seen before need no new work. Markdown '
            f'and text are read directly. A PDF of 250 pages or fewer goes to Document AI in 15-page slices; a bigger one '
            f'waits for the batch lane; a scanned PDF is read from its page images. An image gets a Gemini caption and a '
            f'video or recording timed Gemini segments. Text is cut by headings or by page windows, every chunk is scanned '
            f'for personal data, then embedded and written.</desc>'
            f'<defs><marker id="{key}A" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0L10 5L0 10z" fill="#475569"/></marker></defs>{"".join(body)}</svg>')


def routes_wide():
    k, b = "prw", []
    b += [_node(180, 40, 320, 44, "n", "Upload lands in the bucket", "uploads bucket, tenant/file"), _arrow(340, 84, 340, 104, k),
          _node(180, 106, 320, 44, "n", "Check the path", "a tenant folder is required"), _arrow(500, 128, 518, 128, k),
          _node(520, 106, 120, 44, "s", "Refused", "no tenant folder"), _arrow(340, 150, 340, 170, k),
          _node(180, 172, 320, 44, "n", "Fingerprint the bytes", "SHA-256 names the version"), _arrow(500, 194, 518, 194, k),
          _node(520, 172, 120, 44, "s", "No new work", "bytes seen before"), _arrow(340, 216, 340, 236, k),
          _node(180, 238, 320, 36, "n", "Route by file type"),
          '<path d="M340 274 V288 H52 V602" fill="none" stroke="#475569" stroke-width="1.5"/>']
    for i, (typ, tdet, how, hdet, ex, res, style) in enumerate(ROUTES):
        y, mid = 300 + 56 * i, 322 + 56 * i
        b += [_arrow(52, mid, 62, mid, k), _node(64, y, 150, 44, "t", typ, tdet), _arrow(214, mid, 232, mid, k),
              _node(234, y, 186, 44, style, how, hdet), _arrow(420, mid, 438, mid, k), _node(440, y, 200, 44, "n", ex, res, mono=True)]
    b += ['<rect x="52" y="644" width="588" height="88" rx="8" fill="none" stroke="#64748b" stroke-width="1" stroke-dasharray="4 4"/>',
          _text(64, 664, "Text from Markdown and PDFs is cut into chunks", 13, "500"),
          _node(64, 676, 276, 44, "t", "Has ## headings", "one chunk per clause: NP-03"),
          _node(356, 676, 272, 44, "t", "No headings", "2,000-char windows per page: p9-0"), _arrow(340, 732, 340, 750, k),
          _node(180, 752, 320, 44, "n", "Personal-data scan (DLP)", "every chunk, before indexing"), _arrow(340, 796, 340, 816, k),
          _node(180, 818, 320, 44, "n", "Embed and write", "Firestore rows + Vector Search"),
          _node(40, 878, 600, 44, "n", "Which Document AI? Set once by RESIDENCY",
                "india: OCR in Mumbai, text only · us: Layout Parser, headings and tables · make up: us"),
          _rect(40, 934, 14, 14, "t"), _text(62, 946, "how the file is read and cut", 11, fill="#475569"),
          _rect(320, 934, 14, 14, "s"), _text(342, 946, "stops or waits here", 11, fill="#475569")]
    return _svg(680, 962, k, b)


def routes_tall():
    k, b = "prt", []
    b += [_node(12, 12, 336, 40, "n", "Upload lands in the bucket", "uploads bucket, tenant/file"), _arrow(118, 52, 118, 68, k),
          _node(12, 70, 212, 40, "n", "Check the path", "a tenant folder is required"), _arrow(224, 90, 234, 90, k),
          _node(236, 70, 112, 40, "s", "Refused", "no tenant folder"), _arrow(118, 110, 118, 126, k),
          _node(12, 128, 212, 40, "n", "Fingerprint the bytes", "SHA-256 names the version"), _arrow(224, 148, 234, 148, k),
          _node(236, 128, 112, 40, "s", "No new work", "bytes seen before"), _arrow(118, 168, 118, 184, k),
          _node(12, 186, 336, 34, "n", "Route by file type"),
          '<path d="M180 220 V228 H12 V595" fill="none" stroke="#475569" stroke-width="1.5"/>']
    for i, (typ, tdet, how, hdet, ex, res, style) in enumerate(ROUTES):
        y = 236 + 66 * i
        b += [_arrow(12, y + 29, 22, y + 29, k), _rect(24, y, 324, 58, style), _text(36, y + 18, f"{typ} ({tdet})", 13, "500"),
              _text(36, y + 34, f"{how}: {hdet}", 11, fill="#475569"), _text(36, y + 50, f"{ex} → {res}", 11, fill="#475569")]
    b += ['<rect x="12" y="644" width="336" height="124" rx="8" fill="none" stroke="#64748b" stroke-width="1" stroke-dasharray="4 4"/>',
          _text(24, 663, "Text from Markdown and PDFs is cut", 13, "500"),
          _node(24, 674, 312, 38, "t", "Has ## headings", "one chunk per clause: NP-03"),
          _node(24, 720, 312, 38, "t", "No headings", "2,000-char windows per page: p9-0"), _arrow(180, 768, 180, 786, k),
          _node(12, 788, 336, 40, "n", "Personal-data scan (DLP)", "every chunk, before indexing"), _arrow(180, 828, 180, 846, k),
          _node(12, 848, 336, 40, "n", "Embed and write", "Firestore rows + Vector Search"),
          _rect(12, 904, 336, 58, "n"), _text(24, 922, "Which Document AI? Set by RESIDENCY", 13, "500"),
          _text(24, 938, "india: OCR in Mumbai, text only", 11, fill="#475569"),
          _text(24, 954, "us: Layout Parser, headings and tables (make up)", 11, fill="#475569"),
          _rect(12, 976, 14, 14, "t"), _text(32, 987, "how the file is read and cut", 11, fill="#475569"),
          _rect(190, 976, 14, 14, "s"), _text(210, 987, "stops or waits here", 11, fill="#475569")]
    return _svg(360, 1004, k, b)


part_a = pb.part(LESSON, "a")
assert part_a.count("%%ROUTES_WIDE%%") == 1 and part_a.count("%%ROUTES_TALL%%") == 1
part_a = part_a.replace("%%ROUTES_WIDE%%", routes_wide()).replace("%%ROUTES_TALL%%", routes_tall())

body = "".join([
    part_a,
    setup,
    pb.part(LESSON, "b"),
    pb.part(LESSON, "c"),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
