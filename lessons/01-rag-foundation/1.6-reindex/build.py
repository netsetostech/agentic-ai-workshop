"""Build lesson 1.6 from its three parts, the shared template, the 1.1 setup section, verbatim kit excerpts, and
numbers computed with the kit's own chunker and planner at build time."""
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.6"


title = "<title>Lesson 1.6 Reindex a changed section and measure embedding reuse - a release with a gate, and the count that says what it cost | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rm-buttons{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;}
.rm-btn{font:inherit;font-size:var(--small-size);font-weight:500;min-height:44px;padding:8px 12px;border:1px solid var(--teal);border-radius:8px;background:var(--card);color:var(--teal);cursor:pointer;flex:1 1 150px;}
.rm-text{width:100%;box-sizing:border-box;font-family:var(--mono);font-size:16px;line-height:1.45;padding:10px;border:1px solid var(--border);border-radius:10px;background:var(--card);color:var(--navy);resize:vertical;min-height:180px;}
.rm-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:8px 0;overflow-wrap:anywhere;}
.rm-out{display:flex;flex-wrap:wrap;gap:8px;}
.rm-card{flex:1 1 150px;border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.4;min-width:0;border:2px solid var(--teal);background:var(--teal-light);color:var(--navy);}
.rm-card.hot{border-color:#d97706;background:#fffbeb;}
.rm-card b{display:block;font-family:var(--mono);font-size:var(--kicker-size);margin-bottom:3px;}
@media (hover:hover) and (pointer:fine){.rm-btn:hover{background:var(--teal-light);}}
"""

setup = setup_section()



EV = "evals/run_eval.py"
IDM = "services/ingest/idempotency.py"
EXCERPTS = {
    "reindex_sh": ("commands/reindex.sh - what make reindex runs: the gate, the upload, the wait, the counts", block("commands/reindex.sh", "#!/usr/bin/env bash", n=200)),
    "run_eval_main": ("evals/run_eval.py - main(): the offline half, and what --source adds to it", block(EV, "def main() -> int:", n=200)),
    "run_eval_scope": ("evals/run_eval.py - which rows cite a document", block(EV, "def sources_of(", n=14)),
    "chunk_hash": ("shared/documind_corpus.py - chunk_hash(): the identity the carry-over matches on", block("shared/documind_corpus.py", "def chunk_hash(", end="def chunk_document(")),
    "carry_over": ("services/ingest/indexer.py - embed_with_carry_over(): lent by hash, embedded on a miss", block("services/ingest/indexer.py", "def embed_with_carry_over(", end="def _restricts(")),
    "required": ("evals/run_eval.py - the rows that must pass on their own", block(EV, "def load_required(", n=9)),
    "eval_live_make": ("Makefile - eval-live: the live half, scoped with SOURCE=", block("Makefile", "eval-live: guard-project", n=10)),
    "claim_tx": ("services/ingest/idempotency.py - claim(): the transaction and the states it may take back", block(IDM, '    ref = db.collection("documents").document(doc_key)', end="def finish(")),
    "release": ("services/ingest/idempotency.py - release(): a failed claim is a record of one", block(IDM, "def release(", n=11)),
}


fill = filler(EXCERPTS, window)


# ---- numbers from the kit itself: the three version keys, the seven plans, the offline gate's output ----
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402

V1_TEXT = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
V1_BYTES = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_bytes()
V2_BYTES = (KIT / "evals/demo/hr_policy_2026_v2.md").read_bytes()
R3 = V1_TEXT.replace("# ACME Employee Handbook 2026\n", "# ACME Employee Handbook 2026 (revision 3)\n\nEffective from: 2026-11-01. Revision 3 changes NP-03: the notice period for a confirmed E3 becomes 90 days.\n", 1)
R3 = R3.replace("serves a notice period of 60 days", "serves a notice period of 90 days", 1)
SHA1, SHA2, SHA3 = (hashlib.sha256(x).hexdigest() for x in (V1_BYTES, V2_BYTES, R3.encode("utf-8")))


def cut(text, slug="hr_policy_2026"):
    return dc.chunk_document({"slug": slug, "doc_type": "policy", "source_uri": "gs://x", "text": text}, "acme")


def measure(name, old, new, slug="hr_policy_2026"):
    a_, b_ = cut(old, slug), cut(new, slug)
    held = {c["chunk_hash"] for c in a_}
    misses = [i for i, c in enumerate(b_) if c["chunk_hash"] not in held]
    chars = sum(len(b_[i]["text"]) for i in misses)
    line = f"{name:36} chunks {len(a_):>3} -> {len(b_):>3}  reused {len(b_) - len(misses):>3}  embedded {len(misses):>2}  {chars:>5} chars  {[b_[i]['locator'] for i in misses]}"
    return line, (len(a_), len(b_), len(b_) - len(misses), len(misses), [b_[i]["locator"] for i in misses])


v1 = V1_TEXT
m = re.search(r"(## NP-03 — Notice period\n.*?\n\n)(## PB-02 — Probation\n.*?\n\n)", v1, re.S)
wg = (KIT / "evals/corpus/acme/code_on_wages_2019.md").read_text(encoding="utf-8")
pages = wg.split("\f")
pages[1] = "A new opening sentence was inserted at the top of this page. " + pages[1]
EDITS = [
    ("a figure in NP-03 (60 to 90)", v1, v1.replace("serves a notice period of 60 days", "serves a notice period of 90 days", 1), "hr_policy_2026", "one clause's text changed: one hash"),
    ("a figure in PB-02 (15 to 20)", v1, v1.replace("period is 15 days for either side", "period is 20 days for either side", 1), "hr_policy_2026", "the same, in the clause lesson 1.1 asked about"),
    ("NP-03 re-wrapped (whitespace only)", v1, v1.replace("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs", "A confirmed employee at grade E3 or above\nserves a notice period of 60 days. Notice runs", 1), "hr_policy_2026", "whitespace is collapsed before hashing"),
    ("NP-03's heading renamed", v1, v1.replace("## NP-03 — Notice period", "## NP-03 — Notice period and pay in lieu", 1), "hr_policy_2026", "the heading is the first line of the clause's text"),
    ("a clause inserted before PB-02", v1, v1.replace("## PB-02 — Probation", "## NP-04 — Garden leave\n\nGarden leave may be directed for the notice period at full pay.\n\n## PB-02 — Probation", 1), "hr_policy_2026", "positions move, hashes do not"),
    ("NP-03 and PB-02 swapped", v1, v1.replace(m.group(0), m.group(2) + m.group(1), 1), "hr_policy_2026", "order is not part of a hash"),
    ("wages: a sentence added on page 2", wg, "\f".join(pages), "code_on_wages_2019", "windows are cut per page and re-align on the next sentence end"),
]
lines, rows = [], []
for name, old, new, slug, why in EDITS:
    line, (na, nb, reused, embedded, locs) = measure(name, old, new, slug)
    lines.append(line)
    rows.append(f"<tr><td>{html.escape(name)}</td><td data-label=\"Chunks\">{na}{' to ' + str(nb) if nb != na else ''}</td>"
                f"<td data-label=\"Reused\">{reused}</td><td data-label=\"Embedded\">{embedded}{' (' + ', '.join(locs) + ')' if locs else ''}</td>"
                f"<td data-label=\"Why\">{html.escape(why)}</td></tr>")
MEASURE = "\n".join(lines)
MEASURE_ROWS = "\n".join(rows)
assert rows[0].count("<td data-label=\"Embedded\">1 (NP-03)") == 1, rows[0]

gate = subprocess.run([sys.executable, "evals/run_eval.py", "--source", "hr_policy_2026.md"], cwd=str(KIT), capture_output=True, text=True)
GATE = gate.stdout.strip()
assert "rows citing hr_policy_2026.md: 10" in GATE, GATE[-400:]


def subst(text: str) -> str:
    return (text.replace("%%GATE%%", html.escape(GATE)).replace("%%MEASURE%%", html.escape(MEASURE)).replace("%%MEASURE_ROWS%%", MEASURE_ROWS)
            .replace("%%SHA3_12%%", SHA3[:12]).replace("%%SHA3_16%%", SHA3[:16]).replace("%%SHA3_8%%", SHA3[:8])
            .replace("%%SHA1_16%%", SHA1[:16]).replace("%%SHA1_8%%", SHA1[:8]).replace("%%SHA2_8%%", SHA2[:8]))


# ---- the reuse meter: the excerpt lesson 1.2's explorer used, the kit's section rule, the carry-over's hash rule ----
heads = [mm.start() for mm in re.finditer(r"^## ", V1_TEXT, re.M)]
sample = V1_TEXT[:heads[5]].strip()
JS = """<script>
(function(){
  'use strict';
  var ORIGINAL = %s, RATE_PAISE_PER_CHAR = 0.000025 / 1000 * 85 * 100;   /* text-embedding-005, USD per 1,000 characters, at Rs 85 */
  var root = document.getElementById('meter'); if (!root) return;
  var ta = document.getElementById('rm-text'), out = document.getElementById('rm-out'), sum = document.getElementById('rm-sum');
  var CODE = /^([A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,6}){1,2})\\b/;
  function windows(text, n, o){ text = text.trim(); var res = [], start = 0;
    while (start < text.length){ var end = Math.min(text.length, start + n);
      if (end < text.length){ var cut = text.lastIndexOf('. ', end); if (cut >= start + Math.floor(n / 2)) end = cut + 1; }
      var piece = text.slice(start, end).trim(); if (piece) res.push(piece); if (end >= text.length) break; start = Math.max(end - o, start + 1); }
    return res; }
  function chunk(text){ var lines = text.split('\\n'), hs = []; lines.forEach(function(l, i){ if (/^## +/.test(l)) hs.push(i); });
    var outc = [];
    if (hs.length){ var pre = lines.slice(0, hs[0]).join('\\n').trim(); windows(pre, 2000, 200).forEach(function(w, k){ outc.push({loc: 'preamble' + (k ? '-' + k : ''), text: w}); });
      hs.forEach(function(h, j){ var title = lines[h].replace(/^## +/, '').trim(); var body = lines.slice(h + 1, j + 1 < hs.length ? hs[j + 1] : lines.length).join('\\n').trim();
        var mm = CODE.exec(title), key = mm ? mm[1] : 's' + (j + 1); windows(title + '\\n' + body, 2000, 200).forEach(function(w, k){ outc.push({loc: key + (k ? '-' + k : ''), text: w}); }); });
    } else { windows(text, 2000, 200).forEach(function(w, k){ outc.push({loc: 'w' + k, text: w}); }); }
    return outc; }
  function key(t){ return t.replace(/\\s+/g, ' ').trim(); }   /* chunk_hash(): the hash of the whitespace-collapsed text; equal text, equal hash */
  var held = {}; chunk(ORIGINAL).forEach(function(c){ held[key(c.text)] = true; });
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function render(){
    var cs = chunk(ta.value), reused = 0, chars = 0;
    out.innerHTML = cs.map(function(c){ var ok = !!held[key(c.text)]; if (ok) reused++; else chars += c.text.length;
      return '<div class="rm-card' + (ok ? '' : ' hot') + '"><b>' + esc(c.loc) + ' &middot; ' + (ok ? 'reused' : 'embed again') + '</b>' + esc(c.text.slice(0, 90)) + (c.text.length > 90 ? '&hellip;' : '') + '</div>'; }).join('');
    var embedded = cs.length - reused;
    sum.textContent = cs.length + ' chunks: ' + reused + ' reused, ' + embedded + ' embedded' + (embedded ? ' (' + chars + ' characters, about ' + (chars * RATE_PAISE_PER_CHAR).toFixed(2) + ' paise)' : ' (nothing to pay)');
  }
  var EDITS = {
    figure: function(t){ return t.replace('serves a notice period of 60 days', 'serves a notice period of 90 days'); },
    rewrap: function(t){ return t.replace('A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs', 'A confirmed employee at grade E3 or above\\nserves a notice period of 60 days. Notice runs'); },
    heading: function(t){ return t.replace(/^(## NP-03 [^\\n]*)$/m, '$1 and pay in lieu'); },
    insert: function(t){ return t.replace(/^(## PB-02 )/m, '## NP-04 \\u2014 Garden leave\\n\\nGarden leave may be directed for the notice period at full pay.\\n\\n$1'); },
    swap: function(t){ var mm = /(## NP-03 [^\\n]*\\n\\n[\\s\\S]*?\\n\\n)(## PB-02 [^\\n]*\\n\\n[\\s\\S]*?\\n\\n)/.exec(t); return mm ? t.replace(mm[0], mm[2] + mm[1]) : t; },   /* the heading line, its blank line, the body: a clause is heading plus body */
    reset: function(){ return ORIGINAL; }
  };
  root.querySelectorAll('.rm-btn').forEach(function(btn){ btn.addEventListener('click', function(){ ta.value = EDITS[btn.getAttribute('data-edit')](ORIGINAL); render(); }); });
  ta.addEventListener('input', render);
  ta.value = ORIGINAL; render();
})();
</script>
""" % json.dumps(sample)

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
