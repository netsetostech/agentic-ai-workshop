"""Build lesson 3.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The numbers on the page come from the kit at build time: the budget class's defaults and the fit for the lesson's
question (context_budget.py with generator.py's own strings), the settings and rates (config.py, cost.py,
cache_manager.py), the packing bench (acme's mirrors through the kit's chunker, ordered by lesson 2.2's BM25 port,
with the dated smoke note read by the worker's own date reader), and the offline cell of step 3, which is executed
here so its expected output is the kit's own.
"""
import ast
import html
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "3.4"
title = "<title>Lesson 3.4 Pack evidence within the context budget - the lines of one prompt, the packer that fills them most relevant first, and the counter that says what the packed set costs | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pb-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.pb-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pb-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pb-l input[type=range]{width:100%;min-height:44px;margin:0;}
.pb-check label{display:inline-flex;align-items:center;gap:8px;min-height:44px;font-size:var(--small-size);color:var(--slate);}
.pb-check input{width:22px;height:22px;margin:0;}
.pb-lines{display:flex;width:100%;height:28px;border-radius:8px;overflow:hidden;border:1px solid var(--border);margin:6px 0 4px;}
.pb-lines span{display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:var(--kicker-size);color:#fff;white-space:nowrap;overflow:hidden;min-width:0;}
.pb-lines .sys{background:#334155;}.pb-lines .chk{background:var(--teal);}.pb-lines .free{background:#cbd5e1;color:var(--navy);}
.pb-legend{font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);margin:0 0 8px;overflow-wrap:anywhere;}
.pb-out{display:grid;gap:8px;}
.pb-step{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;}
.pb-step b{color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;display:block;margin-bottom:2px;}
.pb-step ol{margin:4px 0 0;padding-left:22px;}
.pb-step li{overflow-wrap:anywhere;}
.pb-step li.drop{color:#92400e;}
.pb-step code{overflow-wrap:anywhere;}
.pb-step.flag{border-color:#f59e0b;background:#fffbeb;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CB = "services/rag-api/context_budget.py"
GEN = "services/rag-api/generator.py"
CFG = "services/rag-api/config.py"
API = "services/rag-api/main.py"
COST = "services/rag-api/cost.py"
CONTRACTS = "services/ingest/contracts.py"
INDEXER = "services/ingest/indexer.py"

EXCERPTS = {
    "budget_class": ("services/rag-api/context_budget.py - TokenBudget: the five lines, and 4.5's teaching split",
                     block(CB, "@dataclass(frozen=True)", end="    @classmethod")),
    "fit": ("services/rag-api/context_budget.py - fit(): the API's own budget from the total and the fixed prompt",
            block(CB, "    @classmethod", end="def estimate_tokens(")),
    "header": ("services/rag-api/context_budget.py - estimate_tokens() and the [Source N] header, with the page and the date",
               block(CB, "def estimate_tokens(", n=2) + "\n...\n" + block(CB, '    uri = chunk.get("source_uri")', n=8)),
    "pack_chunks": ("services/rag-api/context_budget.py - pack_chunks(): most relevant first, the drop, and the counter's trim",
                    block(CB, "def pack_chunks(", n=2) + "\n...\n" + block(CB, "    packed, dropped, parts, used = [], [], [], 0")),
    "budget_fn": ("services/rag-api/generator.py - _budget(): the fixed prompt counted, the chunks get what is left",
                  block(GEN, '    fixed = f"{SYSTEM}{DATED_RULE}', n=2)),
    "pack_fn": ("services/rag-api/generator.py - _pack(): the packed set, and a drop is a log line",
                block(GEN, "    context, packed, dropped = pack_chunks(chunks, _budget(query).chunks, estimate_tokens)", n=7)),
    "count_loop": ("services/rag-api/context_budget.py - the counter's loop: the exact size, then the tail comes off",
                   block(CB, "    if count_fn and context:", n=7)),
    "usage_fn": ("services/rag-api/generator.py - _usage(): the prompt, the cached part of it, and the output with the thinking",
                 block(GEN, "def _usage(r)", end="def _add(")),
    "price_fn": ("services/rag-api/cost.py - price(): both currencies, cached input at a tenth",
                 block(COST, '    usd_in, usd_out = _prices().get(model', n=9)),
    "effective_reader": ("services/ingest/contracts.py - effective_from_of(): the date off the name, then off the first lines",
                         block(CONTRACTS, "_EFFECTIVE_TEXT = re.compile(", n=2) + "\n...\n" + block(CONTRACTS, "def effective_from_of(", n=10)),
    "row_stamp": ("services/ingest/indexer.py - the stamp on every row of a dated document",
                  block(INDEXER, '        if getattr(doc, "effective_from", None):', n=2)),
    "dated_rule": ("services/rag-api/generator.py - SYSTEM's five rules, the sixth held for a dated source, and when it is added",
                   block(GEN, 'SYSTEM = """You are DocuMind', end="# The ledger's second half") + "\n...\n" + block(GEN, 'DATED_RULE = ("', end="def _budget(")),
    "citation_event": ("services/rag-api/main.py - the stream's citation event carries the row's date out",
                       block(API, "                    yield f\"event: citation\\ndata: {json.dumps({'n': i, 'chunk_id': c.get('id')", n=1)),
    "reserve_setting": ("services/rag-api/config.py - the answer's reserve, and why it is not 1,024",
                        block(CFG, "    # 2048, not 1024: a statute answer with its quotes", n=4)),
    "retry": ("services/rag-api/generator.py - generate(): cut off is not refused; once more with three times the room, both billed",
              block(GEN, '    if draft is None and _finish_reason(r) == "MAX_TOKENS":', n=17)),
    "usage_fields": ("services/rag-api/main.py - usage_row(): the tokens and the price on every row",
                     block(API, '            "tokens_in": ans_tokens_in, "tokens_out": ans_tokens_out,', n=2)),
}
assert EXCERPTS["fit"][1].rstrip().endswith("history=0, answer=answer)"), EXCERPTS["fit"][1][-80:]
assert EXCERPTS["pack_chunks"][1].rstrip().endswith("return context, packed, dropped")
assert EXCERPTS["retry"][1].rstrip().endswith("draft = _draft(r)"), EXCERPTS["retry"][1][-60:]
assert EXCERPTS["dated_rule"][1].count("6. Some sources carry an effective date") == 1 and "def _dated_rule" in EXCERPTS["dated_rule"][1]
assert EXCERPTS["price_fn"][1].rstrip().endswith('"cached_tokens": cached_tokens}')
assert "'effective_from': c.get('effective_from')" in EXCERPTS["citation_event"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ numbers read off the kit
grab = lambda pat, text: re.search(pat, text).group(1)
cfg = (KIT / CFG).read_text(encoding="utf-8")
TOTAL = int(grab(r"max_context_tokens: int = (\d+)", cfg))
ANSWER = int(grab(r"max_answer_tokens: int = (\d+)", cfg))
GEN_MODEL = grab(r'generator_model: str = "([^"]+)"', cfg)
PROMPT_VERSION = grab(r'prompt_version: str = "([^"]+)"', cfg)
cost_txt = (KIT / COST).read_text(encoding="utf-8")
RATE_IN, RATE_OUT = (float(x) for x in re.search(r'"' + re.escape(GEN_MODEL) + r'": \(([\d.]+), ([\d.]+)\)', cost_txt).groups())
USD_INR = grab(r'USD_INR = float\(os.environ.get\("USD_INR_RATE", "([\d.]+)"\)\)', cost_txt)
MIN_CACHE = int(grab(r"MIN_CACHE_TOKENS = ([\d_]+)", (KIT / "services" / "rag-api" / "cache_manager.py").read_text(encoding="utf-8")).replace("_", ""))

sys.path[:0] = [str(KIT), str(KIT / "services" / "rag-api"), str(KIT / "services" / "ingest")]
from context_budget import TokenBudget, estimate_tokens, source_header, pack_chunks  # noqa: E402
from contracts import effective_from_of  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402

gen_tree = ast.parse((KIT / GEN).read_text(encoding="utf-8"))
K = {n.targets[0].id: ast.literal_eval(n.value) for n in gen_tree.body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
QUESTION = "What is the notice period for a confirmed E3?"
SCAFFOLD_A, SCAFFOLD_B = "\n\nContext:\n\n\nQuestion: ", ""
fixed = f"{K['SYSTEM']}{K['DATED_RULE']}{SCAFFOLD_A}{QUESTION}"
budget = TokenBudget.fit(TOTAL, fixed, estimate_tokens, answer=ANSWER)
TB = TokenBudget()

# the offline cell of step 3, run here: the expected block is its output
part_b = pb.part(LESSON, "b")
cell_src = part_b.split("<!-- cell:offline -->", 1)[1]
cell_src = cell_src.split("python - &lt;&lt;'PY'\n", 1)[1].split("\nPY</pre>", 1)[0]
cell_src = html.unescape(cell_src)
run = subprocess.run([sys.executable, "-"], input=cell_src, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8",
                     env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})     # the lane's shell is UTF-8; a Windows console is not
assert run.returncode == 0, run.stderr[-800:]
OFFLINE_OUT = run.stdout.strip("\n")
assert "full Act pages, top_k 20: packed" in OFFLINE_OUT and "the dated rule is added" in OFFLINE_OUT and "effective from 2026-10-01" in OFFLINE_OUT, OFFLINE_OUT[-400:]


def chunks_of(name: str, path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    out = dc.chunk_document({"slug": name.rsplit(".", 1)[0], "doc_type": "policy", "source_uri": f"gs://uploads/acme/{name}", "text": text}, "acme")
    date = effective_from_of(name, text)
    for c in out:
        if date:
            c["effective_from"] = date
    return out


CORPUS = KIT / "evals" / "corpus" / "acme"
handbook = chunks_of("hr_policy_2026.md", CORPUS / "hr_policy_2026.md")
act = sorted(chunks_of("cgst_act_2017.md", CORPUS / "cgst_act_2017.md"), key=lambda c: (-len(c["text"]), c["locator"]))
note = chunks_of("smoke_note.md", KIT / "evals" / "demo" / "smoke_note_v2.md")
assert note and note[0].get("effective_from") == "2026-10-01"
np03 = next(c for c in handbook if c["locator"] == "NP-03")["text"]
HINDI = "सूचना अवधि: पुष्टि किए गए कर्मचारी के लिए तीस दिन, परिवीक्षा पर सात दिन।"
_, act_packed, act_dropped = pack_chunks(act[:20], budget.chunks, estimate_tokens)
act_context = pack_chunks(act[:20], budget.chunks, estimate_tokens)[0]

# the bench: acme's mirrors ordered by the BM25 port of lesson 2.2 for three golden questions
docs = []
for p in sorted(CORPUS.glob("*.md")):
    docs += chunks_of(p.name, p)
tokens = lambda text: re.findall(r"[a-z0-9\-]+", text.lower())
tok_docs = [tokens(d["text"]) for d in docs]
N = len(docs)
doc_len = [len(t) for t in tok_docs]
avgdl = sum(doc_len) / N
doc_freqs = [Counter(t) for t in tok_docs]
nd = Counter()
for f in doc_freqs:
    nd.update(f.keys())
K1, B, EPS = 1.5, 0.75, 0.25
idf = {w: math.log(N - n + 0.5) - math.log(n + 0.5) for w, n in nd.items()}
avg_idf = sum(idf.values()) / len(idf)
idf = {w: (v if v >= 0 else EPS * avg_idf) for w, v in idf.items()}


def bm25(q: str) -> list:
    out = [0.0] * N
    for w in tokens(q):
        if w not in idf:
            continue
        for i, f in enumerate(doc_freqs):
            qf = f.get(w, 0)
            if qf:
                out[i] += idf[w] * qf * (K1 + 1) / (qf + K1 * (1 - B + B * doc_len[i] / avgdl))
    return out


golden = {r["id"]: r for r in (json.loads(l) for l in (KIT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}


def lite(c: dict) -> dict:
    return {"src": c["source_uri"].rsplit("/", 1)[-1], "loc": c.get("locator") or "", "page": c.get("page_start") or c.get("page") or c.get("pages") or None,
            "sec": c.get("section") or "", "len": len(c["text"]), "eff": c.get("effective_from")}


bench, options = {}, []
for rid in ("lk-06", "lk-16", "lk-27"):
    q = golden[rid]["question"]
    scores = bm25(q)
    order = [i for i in sorted(range(N), key=lambda i: -scores[i]) if scores[i] > 0][:20]
    bench[rid] = {"q": q, "pool": [lite(docs[i]) for i in order]}
    options.append(f'<option value="{rid}">{rid} &middot; {html.escape(q)}</option>')
BENCH = {"questions": bench, "note": lite(note[0]), "system": K["SYSTEM"], "dated": K["DATED_RULE"], "scaffold": SCAFFOLD_A,
         "answer": ANSWER, "rateIn": RATE_IN, "rateOut": RATE_OUT, "usdInr": float(USD_INR), "model": GEN_MODEL}

STATS = {
    "TOTAL": f"{TOTAL:,}", "TOTAL_RAW": str(TOTAL), "ANSWER": f"{ANSWER:,}", "ANSWER_RAW": str(ANSWER), "GEN_MODEL": GEN_MODEL, "PROMPT_VERSION": PROMPT_VERSION,
    "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": USD_INR.rstrip("0").rstrip("."), "MIN_CACHE": f"{MIN_CACHE:,}",
    "RS_1K_IN": f"{RATE_IN * float(USD_INR) / 1000:.3f}",
    "TB_SYSTEM": f"{TB.system:,}", "TB_PACK": f"{TB.tenant_pack:,}", "TB_CHUNKS": f"{TB.chunks:,}", "TB_HISTORY": f"{TB.history:,}", "TB_ANSWER": f"{TB.answer:,}",
    "FIXED_TOKENS": f"{budget.system:,}", "FIXED_TOKENS_RAW": str(budget.system), "CHUNK_BUDGET": f"{budget.chunks:,}", "CHUNK_BUDGET_RAW": str(budget.chunks),
    "NP03_CHARS": str(len(np03)), "NP03_EST": str(estimate_tokens(np03)), "HINDI_CHARS": str(len(HINDI)), "HINDI_EST": str(estimate_tokens(HINDI)),
    "ACT_CHARS": str(len(act[0]["text"])), "ACT_EST": str(estimate_tokens(act[0]["text"])),
    "ACT20_P": str(len(act_packed)), "ACT20_D": str(len(act_dropped)), "ACT20_C": str(estimate_tokens(act_context)),
    "OFFLINE_OUT": html.escape(OFFLINE_OUT), "BENCH_OPTIONS": "".join(options),
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the bench's script: fit(), source_header(), pack_chunks() and price() in JavaScript
JS = """<script>
(function(){
  'use strict';
  var D = __BENCH__;
  var root = document.getElementById('bench'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var qSel = $('pb-q'), total = $('pb-total'), kIn = $('pb-k'), counter = $('pb-counter'), dated = $('pb-dated'), lines = $('pb-lines'), out = $('pb-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function est(len){ return Math.max(1, Math.floor(len / 4)); }                       /* estimate_tokens(): len // 4, never below 1 */
  function header(n, c){ var bits = [c.src]; if (c.page) bits.push('p.' + c.page); if (c.sec) bits.push(c.sec); if (c.eff) bits.push('effective from ' + c.eff); return '[Source ' + n + '] ' + bits.join(', '); }
  function pack(chunks, budget, factor){                                                /* pack_chunks(): the estimate packs, then the counter trims from the tail */
    var packed = [], dropped = [], used = 0, blocks = [];
    chunks.forEach(function(c){ var h = header(packed.length + 1, c), need = est(h.length + 1 + c.len);
      if (used + need > budget) { dropped.push(c); return; } used += need; packed.push({c: c, h: h, t: need}); blocks.push(h.length + 1 + c.len); });
    var ctxLen = blocks.reduce(function(s, v){ return s + v; }, 0) + Math.max(0, blocks.length - 1) * 2, exact = Math.round(est(ctxLen) * factor);
    var trimmed = 0;
    while (exact > budget && packed.length) { dropped.unshift(packed.pop().c); blocks.pop(); trimmed++; ctxLen = blocks.reduce(function(s, v){ return s + v; }, 0) + Math.max(0, blocks.length - 1) * 2; exact = blocks.length ? Math.round(est(ctxLen) * factor) : 0; }
    return {packed: packed, dropped: dropped, ctx: est(ctxLen), exact: exact, trimmed: trimmed};
  }
  function render(){
    var q = D.questions[qSel.value], T = parseInt(total.value, 10), k = parseInt(kIn.value, 10), factor = parseFloat(counter.value);
    $('pb-total-v').textContent = T; $('pb-k-v').textContent = k;
    var fixedLen = D.system.length + D.dated.length + D.scaffold.length + q.q.length, fixed = est(fixedLen), chunkBudget = Math.max(0, T - fixed);
    var pool = (dated.checked ? [D.note] : []).concat(q.pool).slice(0, k), r = pack(pool, chunkBudget, factor);
    var pf = Math.max(2, 100 * fixed / T), pc = Math.max(0, 100 * Math.min(r.ctx, chunkBudget) / T), pfree = Math.max(0, 100 - pf - pc);
    lines.innerHTML = '<span class="sys" style="width:' + pf.toFixed(1) + '%">fixed ' + fixed + '</span><span class="chk" style="width:' + pc.toFixed(1) + '%">chunks ' + r.ctx + '</span><span class="free" style="width:' + pfree.toFixed(1) + '%">' + (chunkBudget - r.ctx > 0 ? 'unused ' + (chunkBudget - r.ctx) : '') + '</span>';
    var steps = [];
    steps.push('<div class="pb-step"><b>1 · fit()</b>the fixed prompt is ' + fixedLen + ' characters, ' + fixed + ' tokens by the estimate; <code>TokenBudget(system=' + fixed + ', tenant_pack=0, chunks=' + chunkBudget + ', history=0, answer=' + D.answer + ')</code>, input_total ' + (fixed + chunkBudget) + ' of ' + T + '</div>');
    var items = r.packed.map(function(p){ return '<li>' + esc(p.h) + ' <code>' + p.t + '</code></li>'; }).join('');
    steps.push('<div class="pb-step"><b>2 · pack_chunks(), ' + k + ' offered</b>packed ' + r.packed.length + ', dropped ' + r.dropped.length + ', context ' + r.ctx + ' tokens by the estimate' + (factor !== 1 ? ', ' + r.exact + ' by the counter, ' + r.trimmed + ' trimmed from the tail' : '') + '<ol>' + items + '</ol>' +
      (r.dropped.length ? '<ol start="' + (r.packed.length + 1) + '">' + r.dropped.map(function(c){ return '<li class="drop">' + esc(header('-', c).replace('[Source -] ', '')) + ' <code>' + est(header('-', c).length + 1 + c.len) + '</code> dropped</li>'; }).join('') + '</ol>' : '') + '</div>');
    var anyDated = r.packed.some(function(p){ return p.c.eff; });
    steps.push('<div class="pb-step' + (r.dropped.length ? ' flag' : '') + '"><b>3 · the log and the prompt</b>' + (r.dropped.length ? '<code>{"event": "context_budget_drop", "packed": ' + r.packed.length + ', "dropped": ' + r.dropped.length + '}</code>' : 'no drop line') + (anyDated ? ' · rule 6 is added: a packed source carries a date' : ' · the five rules only: no packed source carries a date') + '</div>');
    var tokIn = fixed + r.ctx, tokOut = 300, usd = (tokIn * D.rateIn + tokOut * D.rateOut) / 1e6, inr = usd * D.usdInr;
    steps.push('<div class="pb-step"><b>4 · tokens_in and the price</b>about ' + tokIn + ' input tokens by the estimate, and a ' + tokOut + '-token answer: <code>cost.price(' + esc(D.model) + ')</code> = $' + usd.toFixed(6) + ' = Rs ' + inr.toFixed(4) + ' at ' + D.usdInr + ' (in $' + D.rateIn.toFixed(2) + ', out $' + D.rateOut.toFixed(2) + ' per million)</div>');
    out.innerHTML = steps.join('');
  }
  [qSel, total, kIn, counter, dated].forEach(function(el){ el.addEventListener('input', render); el.addEventListener('change', render); });
  render();
})();
</script>
""".replace("__BENCH__", json.dumps(BENCH, ensure_ascii=False, separators=(",", ":")))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(part_b)),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: total {TOTAL} | answer {ANSWER} | fixed {budget.system} -> chunks {budget.chunks} | {GEN_MODEL} ${RATE_IN}/{RATE_OUT} per M at {USD_INR} | cache from {MIN_CACHE}"
      f" | teaching split {TB.system}/{TB.tenant_pack}/{TB.chunks}/{TB.history}/{TB.answer} | Act pages at 20: {len(act_packed)} packed {len(act_dropped)} dropped | bench {N} chunks")
