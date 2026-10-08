"""Build lesson 3.8 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The numbers and samples on the page come from the kit at build time: the link lifetime, the pill pattern and the
hover length from services/frontend/citations.py, the upload types and size cap from documents.py, the UI's top_k
and its own price table from chat.py, and the lesson's note, read out of step 4's cell and cut by the kit's chunker,
for the chunk count, the byte size, the first citation event and the renderer's sample.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "3.8"
title = "<title>Lesson 3.8 Complete the Streamlit upload-to-answer journey - one person, four identities, a page that holds no model, and a cited answer you can open | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.jn-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;counter-reset:jn;}
.jn-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;gap:2px;min-width:0;}
.jn-who{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.jn-what{font-size:12.5px;line-height:1.5;color:var(--slate);}
.jn-proof{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);overflow-wrap:anywhere;}
.cr-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.cr-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.cr-wide{grid-column:1/-1;}
.cr-l select,.cr-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.cr-l textarea{font-family:var(--mono);font-size:16px;line-height:1.35;min-height:140px;resize:vertical;}
.cr-answer{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-size:var(--small-size);line-height:1.7;color:var(--slate);overflow-wrap:anywhere;min-height:44px;}
.cr-pill{background:#ccfbf1;color:#065f46;border-radius:6px;padding:1px 7px;margin:0 2px;font-size:12px;font-weight:600;cursor:help;white-space:nowrap;}
.cr-sources{margin-top:8px;display:grid;gap:6px;}
.cr-src{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.cr-src b{color:var(--navy);}
.cr-src .cr-cap{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);display:block;margin-top:2px;}
.cr-note{font-family:var(--mono);font-size:var(--kicker-size);color:#92400e;margin:6px 0 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
FE = "services/frontend"
AUTH, DOCS, CHAT, CITE = f"{FE}/auth.py", f"{FE}/documents.py", f"{FE}/chat.py", f"{FE}/citations.py"
API = "services/rag-api/main.py"
IAP = "shared/iap.py"
DEPLOY = "commands/lesson-12.4.sh"

EXCERPTS = {
    "deploy_iap": ("commands/lesson-12.4.sh - IAP on the service itself, its agent the only invoker, and who may sign in",
                   block(DEPLOY, "gcloud run deploy documind-ui \\", n=4) + "\n...\n" + block(DEPLOY, "gcloud run services add-iam-policy-binding documind-ui \\", n=4)
                   + "\n...\n" + block(DEPLOY, 'for who in $(echo "$ADMIN_EMAILS"', n=5)),
    "auth_iap": ("services/frontend/auth.py - current_user(): the assertion, verified for this service's audience",
                 block(AUTH, "def _verify_iap_jwt(", end="def login_gate(")),
    "tenant_for": ("services/frontend/auth.py - tenant_for(): the roster, one query, never cached",
                   block(AUTH, "def tenant_for(email: str)", n=2) + "\n    ...\n" + block(AUTH, '    hits = (_roster_db().collection_group("members")', n=5)),
    "upload_document": ("services/frontend/documents.py - upload_document(): the checks, then one object under the tenant's folder",
                        block(DOCS, "def upload_document(", end="def _held_in(")),
    "upload_loop": ("services/frontend/documents.py - documents_page(): the upload is not the indexing, and the page says so",
                    block(DOCS, '    if files and st.button("Index documents"):', n=4) + "\n...\n" + block(DOCS, '        st.info("documind-ingest performs parsing', n=3)),
    "versions_call": ("services/frontend/documents.py - versions_section(): the ledger, read through the API with the page's two credentials",
                      block(DOCS, '        r = requests.get(f"{RAG_API_URL}/v1/sources"', n=1)),
    "headers": ("services/frontend/chat.py - _headers(): the UI's own token, and the person's assertion forwarded",
                block(CHAT, "def _headers(audience: str = RAG_API_URL)", n=1) + "\n    ...\n" + block(CHAT, '    h = {"Authorization": f"Bearer {_id_token(audience)}"}', n=5)),
    "stream_answer": ("services/frontend/chat.py - stream_answer(): the question, labelled ui, and the events as they come",
                      block(CHAT, "def stream_answer(", end="def chat_page(")),
    "identity": ("shared/iap.py - identity(): the assertion first, the bearer token second, never a header",
                 block(IAP, "    assertion = headers.get(ASSERTION_HEADER)", n=8)),
    "row_user": ("services/rag-api/main.py - usage_row(): who asked, and a brain that defaults to ui",
                 block(API, '    return {"event": surface, "tenant": req.tenant_id, "user": user["email"],', n=1) + "\n...\n"
                 + block(API, '            "brain": getattr(req, "brain", None) or "ui"}', n=1)),
    "label": ("services/frontend/citations.py - the pattern and the labels: [3], [Fig 3, p.12], [Clip 3, 03:20]",
              block(CITE, "_CITE = re.compile(", n=1) + "\n...\n" + block(CITE, "def _label(n: int, src: dict | None)", end="def render_with_citations(")),
    "pill": ("services/frontend/citations.py - render_with_citations(): the pills, drawn as HTML",
             block(CITE, "    def _pill(match):", n=14)),
    "signing": ("services/frontend/citations.py - signing on Cloud Run: the account's email and token, and IAM signs",
                block(CITE, "def _signing_kwargs() -> dict:", end="def _mmss(")),
    "ui_roles": ("terraform/sa.tf - the UI's project roles, and the two it pointedly lacks",
                 block("terraform/sa.tf", "  ui_roles = [", end="  api_roles = [")),
    "bucket_grant": ("terraform/storage.tf - object admin on the uploads bucket", block("terraform/storage.tf", 'resource "google_storage_bucket_iam_member" "ui_uploads" {', n=4)),
    "self_sign": ("commands/lesson-12.4.sh - the account may sign as itself", block(DEPLOY, "# Grant self-impersonation for V4 signed URLs", n=5)),
    "ui_prices": ("services/frontend/chat.py - the page's own rates, and the arithmetic the sidebar shows",
                  block(CHAT, "USD_INR = 85", n=4) + "\n...\n" + block(CHAT, '    cost = (done.get("tokens_in", 0) * PRICE_IN', n=2)),
}
assert EXCERPTS["upload_document"][1].rstrip().endswith('"generation": str(blob.generation or ""), "content_type": mime}')
assert EXCERPTS["pill"][1].rstrip().endswith("st.markdown(html, unsafe_allow_html=True)"), EXCERPTS["pill"][1][-80:]
assert EXCERPTS["signing"][1].rstrip().endswith("return f\"{url}#page={page}\" if page else url"), EXCERPTS["signing"][1][-80:]
assert "yield event, json.loads(line[6:])" in EXCERPTS["stream_answer"][1] and "roles/speech.editor" in EXCERPTS["ui_roles"][1]
assert EXCERPTS["identity"][1].rstrip().endswith("refusing\")"), EXCERPTS["identity"][1][-60:]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ numbers read off the kit
grab = lambda pat, text: re.search(pat, text).group(1)
cite_txt, docs_txt, chat_txt = ((KIT / p).read_text(encoding="utf-8") for p in (CITE, DOCS, CHAT))
EXPIRY = int(grab(r"SIGNED_URL_EXPIRY = datetime\.timedelta\(minutes=(\d+)\)", cite_txt))
TIP_CHARS = int(grab(r'tip = \(src\["text"\]\[:(\d+)\]', cite_txt))
CITE_RE = grab(r'_CITE = re\.compile\(r"([^"]+)"\)', cite_txt)
TYPES = re.findall(r'"(\w+)": "[a-z]+/', grab(r"MIME_TYPES = \{(.*?)\}", docs_txt.replace("\n", " ")))
MAX_MB = int(grab(r"max_upload_size=(\d+)", docs_txt))
UI_TOPK = int(grab(r'"top_k": (\d+), "brain": "ui"', chat_txt))
UI_IN, UI_OUT = grab(r"PRICE_IN, PRICE_OUT = ([\d.]+), [\d.]+", chat_txt), grab(r"PRICE_IN, PRICE_OUT = [\d.]+, ([\d.]+)", chat_txt)
UI_INR = re.search(r"(?m)^USD_INR = (\d+)", chat_txt).group(1)
assert EXPIRY == 15 and TIP_CHARS == 120 and MAX_MB == 200 and UI_TOPK == 5 and len(TYPES) == 9, (EXPIRY, TIP_CHARS, MAX_MB, UI_TOPK, TYPES)

# the note, exactly as step 4's cell writes it, with a sample account and date
part_b = pb.part(LESSON, "b")
cell = html.unescape(part_b.split('cat &gt; "$HOME/pune_visitor_rules.md" &lt;&lt;EOF\n', 1)[1].split("\nEOF\n", 1)[0])
NOTE = cell.replace("$ME", "you@example.com").replace("$(date -u +%F)", "2026-09-23") + "\n"
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402

note_chunks = dc.chunk_document({"slug": "pune_visitor_rules", "doc_type": "policy", "source_uri": "gs://uploads/acme/pune_visitor_rules.md", "text": NOTE}, "acme")
assert len(note_chunks) == 3 and note_chunks[1]["locator"] == "VR-01", [c.get("locator") for c in note_chunks]
size = len(NOTE.encode("utf-8"))
NOTE_SIZE = str(size)[:-2] + "xx"
QUOTE_CUT = int(grab(r"'quote': c\['text'\]\[:(\d+)\]", (KIT / API).read_text(encoding="utf-8")))
FIRST_EVENT = f"first citation: pune_visitor_rules.md | kind text | page None | quote {note_chunks[1]['text'][:QUOTE_CUT][:48]!r}"

# the renderer's sample: the note's chunks and two handbook sections as five citation events, and an answer citing [1]
handbook = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
                              "text": (KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_text(encoding="utf-8")}, "acme")
hb = [next(c for c in handbook if c["locator"] == L) for L in ("NP-03", "PB-02")]
bucket = "gs://documind-ai-YOUR-ID-uploads/acme/"


def event(n: int, chunk: dict, name: str, **extra) -> dict:
    e = {"n": n, "chunk_id": chunk.get("chunk_id"), "source": bucket + name, "page": chunk.get("page_start") if not name.endswith(".md") else None,
         "quote": chunk["text"][:QUOTE_CUT], "kind": "text", "media_url": None, "start": None, "end": None, "effective_from": None}
    e.update(extra)
    return e


def transcript(events: list, answer_parts: list) -> str:
    out = "".join(f"event: citation\ndata: {json.dumps(e, ensure_ascii=False)}\n\n" for e in events)
    out += "".join(f"event: token\ndata: {json.dumps({'t': t}, ensure_ascii=False)}\n\n" for t in answer_parts)
    out += "event: done\ndata: " + json.dumps({"tokens_in": 1480, "tokens_out": 212, "cached_tokens": 0, "model": "gemini-3.6-flash", "backend": "vertex"}) + "\n\n"
    return out


note_events = [event(1, note_chunks[1], "pune_visitor_rules.md"), event(2, note_chunks[2], "pune_visitor_rules.md"),
               event(3, note_chunks[0], "pune_visitor_rules.md"), event(4, hb[0], "hr_policy_2026.md"), event(5, hb[1], "hr_policy_2026.md")]
media_events = [event(1, {"chunk_id": "acme:annual_report_2026_fig3#fig-0", "text": "Figure 3: revenue by region, FY2025 and FY2026."}, "annual_report_2026_fig3.png",
                      kind="figure", media_url=bucket + "annual_report_2026_fig3.png"),
                event(2, {"chunk_id": "acme:payment_of_bonus_act_1965#p30-t0", "text": "The Fourth Schedule: a worked illustration of set on and set off, year by year.",
                          "page_start": 30}, "payment_of_bonus_act_1965_p30.png", kind="table", media_url=bucket + "payment_of_bonus_act_1965_p30.png", page=30)]
clip_events = [event(1, {"chunk_id": "acme:segment_example#seg-4", "text": "The CFO walks through the regional numbers."}, "segment_example.mp4",
                     kind="segment", media_url=bucket + "segment_example.mp4", start=200, end=245)]
SAMPLES = {
    "note": transcript(note_events, ["Every visitor to the Pune warehouse wears an ", "amber badge, issued at gate 2 against a photo ",
                                     "identity card and returned at the same gate [1]."]),
    "media": transcript(media_events, ["The figure shows revenue by region [1], and the schedule works an example year by year [2]."]),
    "clip": transcript(clip_events, ["The CFO covers the regional numbers in the town hall [1]."]),
    "range": transcript(note_events, ["Visitors wear an amber badge [1]; the loading dock is off limits [7]."]),
    "source": transcript(note_events, ["Visitors wear an amber badge [Source 1]."]),
    "pair": transcript(note_events, ["Visitors wear amber badges and are escorted at all times [1, 2]."]),
}

STATS = {"EXPIRY": str(EXPIRY), "TIP_CHARS": str(TIP_CHARS), "N_TYPES": str(len(TYPES)), "MAX_MB": str(MAX_MB), "UI_TOPK": str(UI_TOPK),
         "UI_IN": UI_IN, "UI_OUT": UI_OUT, "UI_INR": UI_INR, "NOTE_CHUNKS": str(len(note_chunks)), "NOTE_SIZE": NOTE_SIZE,
         "FIRST_EVENT": html.escape(FIRST_EVENT)}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the renderer's script: citations.py in JavaScript
JS = """<script>
(function(){
  'use strict';
  var SAMPLES = __SAMPLES__, CITE = new RegExp(__CITE__, 'g'), TIP = __TIP__, EXPIRY = __EXPIRY__;
  var root = document.getElementById('renderer'); if (!root) return;
  var ta = document.getElementById('cr-text'), caseSel = document.getElementById('cr-case'), ans = document.getElementById('cr-answer'), srcs = document.getElementById('cr-sources');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function mmss(s){ var n = parseInt(parseFloat(s), 10); if (isNaN(n)) return '?'; var m = Math.floor(n / 60), r = n % 60; return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r; }
  function label(n, src){                                                         /* _label(): [3], [Fig 3, p.12], [Table 3, p.30], [Clip 3, 03:20] */
    if (!src) return '[' + n + ']';
    var kind = src.kind || 'text';
    if (kind === 'figure' || kind === 'table') return '[' + (kind === 'figure' ? 'Fig' : 'Table') + ' ' + n + (src.page_start ? ', p.' + src.page_start : '') + ']';
    if (kind === 'segment') return '[Clip ' + n + ', ' + mmss(src.start) + ']';
    return '[' + n + ']';
  }
  function parse(text){                                                           /* the UI's stream reader: citation events become sources, tokens the answer */
    var ev = null, sources = [], answer = '', done = false;
    text.split(/\\r?\\n/).forEach(function(line){ line = line.trim(); if (!line) return;
      if (line.indexOf('event: ') === 0) { ev = line.slice(7).trim(); return; }
      if (line.indexOf('data: ') !== 0) return;
      var d; try { d = JSON.parse(line.slice(6)); } catch (e) { return; }
      if (ev === 'citation') sources.push({text: d.quote || '', source_uri: d.source || '', page_start: d.page, kind: d.kind || 'text', media_url: d.media_url, start: d.start, end: d['end'], effective_from: d.effective_from});
      else if (ev === 'token') answer += (d.t || '');
      else if (ev === 'done') done = true; });
    return {sources: sources, answer: answer, done: done};
  }
  function render(){
    var r = parse(ta.value);
    if (!r.sources.length && !r.answer) { ans.innerHTML = '<p class="cr-note">paste the transcript curl -N prints for /v1/stream, or pick a case</p>'; srcs.innerHTML = ''; return; }
    var pills = 0, html = esc(r.answer).replace(CITE, function(m, g){                /* render_with_citations(): each number becomes a pill */
      return g.replace(/ /g, '').split(',').map(function(x){ var n = parseInt(x, 10), src = (n > 0 && n <= r.sources.length) ? r.sources[n - 1] : null; pills++;
        var tip = src ? (src.text.slice(0, TIP) + '...') : 'unknown source';
        return '<span class="cr-pill" title="' + esc(tip) + '">' + esc(label(n, src)) + '</span>'; }).join(''); });
    var notes = [];
    if (/\\[Source \\d+\\]/.test(r.answer)) notes.push('the answer says [Source N]; the pattern accepts digits only, so the UI draws no pill for it');
    if (!r.done) notes.push('no done event: the UI would show "The stream ended without a completed answer", not this answer');
    ans.innerHTML = (html || '<em>no tokens</em>') + (notes.length ? '<p class="cr-note">' + notes.map(esc).join('<br>') + '</p>' : '') + '<p class="cr-note" style="color:var(--teal)">' + pills + ' pill' + (pills === 1 ? '' : 's') + ' drawn</p>';
    srcs.innerHTML = '<b style="font-size:var(--small-size);color:var(--navy)">Sources (' + r.sources.length + ')</b>' + r.sources.map(function(s, i){
      var n = i + 1, name = String(s.source_uri).split('/').pop(), link;
      if ((s.kind === 'figure' || s.kind === 'table') && s.media_url) link = 'the image inline, from ' + esc(String(s.media_url).split('/').pop()) + ', signed for ' + EXPIRY + ' minutes';
      else if (s.kind === 'segment' && s.media_url) link = 'the video from ' + mmss(s.start) + ' to ' + mmss(s['end']) + ' of ' + esc(name) + ', signed for ' + EXPIRY + ' minutes';
      else link = (s.page_start ? 'Jump to page ' + s.page_start : 'Open source') + ': a link to ' + esc(name) + ', signed for ' + EXPIRY + ' minutes';
      return '<div class="cr-src"><b>' + esc(label(n, s)) + '</b> ' + esc(String(s.text).slice(0, 200)) + '...' + (s.effective_from ? '<span class="cr-cap">effective from ' + esc(s.effective_from) + '</span>' : '') + '<span class="cr-cap">' + link + '</span></div>';
    }).join('');
  }
  ta.addEventListener('input', render);
  caseSel.addEventListener('change', function(){ if (SAMPLES[caseSel.value]) { ta.value = SAMPLES[caseSel.value]; render(); } caseSel.value = ''; });
  ta.value = SAMPLES.note;
  render();
})();
</script>
""".replace("__SAMPLES__", json.dumps(SAMPLES, ensure_ascii=False)).replace("__CITE__", json.dumps(CITE_RE)).replace("__TIP__", str(TIP_CHARS)).replace("__EXPIRY__", str(EXPIRY))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(part_b)),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: link {EXPIRY} min | tip {TIP_CHARS} chars | types {len(TYPES)} ({', '.join(TYPES)}) | max {MAX_MB} MB | UI top_k {UI_TOPK} | UI rates ${UI_IN}/{UI_OUT} at {UI_INR}"
      f" | note {size} bytes, {len(note_chunks)} chunks {[c['locator'] for c in note_chunks]}")
