"""Build lesson 2.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The numbers on the page come from the kit at build time: the reranker's settings from config.py, the record cap from
retriever.py, the chunk budget from generator.py's fixed prompt through context_budget.py, the average acme chunk from
the kit's chunker, and the usage selftest's rows and output from evals/usage_rows.py (the reader starts on those rows).
"""
import ast
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "2.3"
title = "<title>Lesson 2.3 Rerank and inspect retrieved candidates - one model reads the pool against the question, a clock on every stage, and a fallback that says so on the row | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.fn-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;}
.fn-row{width:var(--w);max-width:100%;min-width:min(100%,320px);margin:0 auto;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;gap:2px;}
.fn-stage{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.fn-what{font-size:12.5px;line-height:1.5;color:var(--slate);}
.fn-field{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);overflow-wrap:anywhere;}
.ur-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.ur-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.ur-wide{grid-column:1/-1;}
.ur-l select,.ur-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.ur-l textarea{font-family:var(--mono);font-size:16px;line-height:1.35;min-height:120px;resize:vertical;}
.ur-btn{font:inherit;font-size:var(--small-size);min-height:44px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;}
.ur-btn:active{background:var(--teal-light);}
@media (hover:hover) and (pointer:fine){.ur-btn:hover{border-color:var(--teal);color:var(--teal);}}
.ur-meta{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 0;}
.ur-table{overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;margin:8px 0;}
.ur-table table{width:100%;border-collapse:collapse;font-size:12.5px;}
.ur-table th,.ur-table td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--border);vertical-align:top;white-space:nowrap;}
.ur-table td.num{font-family:var(--mono);}
.ur-read{display:grid;gap:10px;margin-top:8px;}
.ur-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;min-width:0;}
.ur-row h5{margin:0 0 4px;font-size:var(--small-size);color:var(--navy);}
.ur-row ul{margin:0;padding-left:20px;font-size:12.5px;line-height:1.5;color:var(--slate);}
.ur-row li.flag{color:#92400e;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RET = "services/rag-api/retriever.py"
CFG = "services/rag-api/config.py"
API = "services/rag-api/main.py"
GEN = "services/rag-api/generator.py"
CB = "services/rag-api/context_budget.py"
SCH = "shared/documind_schemas.py"
ABL = "evals/ablate.py"
USG = "evals/usage_rows.py"
SQL = "terraform/sql/tenant_daily.sql"

EXCERPTS = {
    "stage_clock": ("services/rag-api/main.py - _ms() and stage(): one clock and one span per stage",
                    block(API, "def _ms(since: float)", end="app = FastAPI(")),
    "handler_funnel": ("services/rag-api/main.py - /v1/query, after retrieval: the pool counted, then a cache hit, an empty pool, or the rerank stage and its flag",
                       block(API, '    stages["pool"] = len(chunks)', end='        with stage(stages, "generate"):')),
    "rerank_fn": ("services/rag-api/retriever.py - rerank(): the request, the deadline, the fallback, the scores written back",
                  block(RET, "def rerank(query: str")),
    "by_score": ("services/rag-api/retriever.py - _by_retrieval_score() and rerank_fell_back(): the stand-in and the mark",
                 block(RET, "def _by_retrieval_score(", end="def rerank(query")),
    "rerank_settings": ("services/rag-api/config.py - the reranker's settings: the model, the deadline, the pool's width, and one that nothing reads",
                        block(CFG, '    rerank_model: str = "semantic-ranker-fast-004"', n=10)),
    "usage_target": ("Makefile - the usage target", block("Makefile", "# 12.3: tenant_daily's GROUP BY", n=4)),
    "usage_row_fields": ("services/rag-api/main.py - usage_row(): the three clocks, the pool and the fallback flag on every row",
                         block(API, '            "retrieve_ms": stages.get("retrieve_ms", 0)', n=5)),
    "usage_p95": ("evals/usage_rows.py - p95(): the 95th position of the sorted list", block(USG, "def p95(", end="def group(")),
    "view_cols": ("terraform/sql/tenant_daily.sql - the stage columns and the fallback count in the warehouse view",
                  block(SQL, "  APPROX_QUANTILES(CAST(jsonPayload.retrieve_ms", n=4) + "\n...\n" + block(SQL, "  SUM(CAST(jsonPayload.rerank_fallback", n=1)),
    "stamps": ("services/rag-api/retriever.py - the three stamps: firestore on the fallback rung, vector on the index's ids, graph on a walk",
               block(RET, '        d["found_by"] = "firestore"', n=1) + "\n...\n"
               + block(RET, "    pool = _hydrate(ids[:settings.top_k_retrieve], scores)", n=4) + "\n...\n"
               + block(RET, '        d["found_by"] = "graph"', n=1)),
    "citation_class": ("shared/documind_schemas.py - Citation: the fields a caller receives", block(SCH, "class Citation(BaseModel):", end="class RAGAnswer(")),
    "smoke_tier": ("smoke/smoke.py - check 3a: the index's share of the pool, asserted only when this request ran on vector",
                   block("smoke/smoke.py", '    if j and ver.get("retrieval_backend") == "vector"', n=8)),
    "pack": ("services/rag-api/generator.py - _pack(): the packed set, and a drop is a log line", block(GEN, "def _pack(")),
    "resolve_packed": ("services/rag-api/generator.py - generate(): resolve against the packed list, never the pool",
                       block(GEN, "    # Resolve against PACKED, not `chunks`.", n=4)),
}
assert EXCERPTS["rerank_fn"][1].rstrip().endswith("return out"), EXCERPTS["rerank_fn"][1][-60:]
assert "rerank_fallback" in EXCERPTS["by_score"][1] and "def rerank_fell_back" in EXCERPTS["by_score"][1]
assert EXCERPTS["rerank_settings"][1].rstrip().endswith("top_k_rerank: int = 5")
assert EXCERPTS["handler_funnel"][1].rstrip().endswith('stages["rerank_fallback"] = 1                 # the pool by retrieval score stood in for the Ranking API'), EXCERPTS["handler_funnel"][1][-120:]
assert EXCERPTS["smoke_tier"][1].rstrip().endswith("skipped\")"), EXCERPTS["smoke_tier"][1][-80:]
assert EXCERPTS["view_cols"][1].rstrip().endswith("AS rerank_fallbacks,")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ numbers read off the kit
cfg = (KIT / CFG).read_text(encoding="utf-8")
ret = (KIT / RET).read_text(encoding="utf-8")
grab = lambda pat, text: re.search(pat, text).group(1)
MODEL = grab(r'rerank_model: str = "([^"]+)"', cfg)
TIMEOUT = grab(r'rerank_timeout_s: float = Field\(([\d.]+),', cfg)
TOPK = int(grab(r"top_k_retrieve: int = Field\((\d+),", cfg))
TOTAL = int(grab(r"max_context_tokens: int = (\d+)", cfg))
ANSWER = int(grab(r"max_answer_tokens: int = (\d+)", cfg))
RECORDS = int(grab(r"chunks = chunks\[:(\d+)\]", ret))
QUESTION = "What is the notice period for a confirmed E3?"

sys.path[:0] = [str(KIT), str(KIT / "services" / "rag-api")]
from context_budget import TokenBudget, estimate_tokens  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402

gen_tree = ast.parse((KIT / GEN).read_text(encoding="utf-8"))
consts = {n.targets[0].id: ast.literal_eval(n.value) for n in gen_tree.body
          if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
fixed = f"{consts['SYSTEM']}{consts['DATED_RULE']}\n\nContext:\n\n\nQuestion: {QUESTION}"      # generator._budget(), line for line
budget = TokenBudget.fit(TOTAL, fixed, estimate_tokens, answer=ANSWER)

CORPUS = KIT / "evals" / "corpus" / "acme"
chunk_tokens, handbook, act_pages = [], [], []
for p in sorted(CORPUS.glob("*.md")):
    for c in dc.chunk_document({"slug": p.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{p.name}",
                                "text": p.read_text(encoding="utf-8")}, "acme"):
        chunk_tokens.append(estimate_tokens(c["text"]))
        if p.name == "hr_policy_2026.md":
            handbook.append(estimate_tokens(c["text"]))
        elif p.name == "cgst_act_2017.md":
            act_pages.append(c)
N = len(chunk_tokens)
HB_MEAN = round(sum(handbook) / len(handbook))
WIN = max(chunk_tokens)                                                          # the chunker's page window, 2,000 characters
# the API's packer over twenty full pages of the CGST Act's mirror: what step 8's offline cell prints
from context_budget import pack_chunks  # noqa: E402
full = sorted(act_pages, key=lambda c: -len(c["text"]))[:TOPK]
ctx, packed, dropped = pack_chunks(full, budget.chunks, estimate_tokens)
FIT_WIN, DROP_WIN, WIN_CONTEXT = len(packed), len(dropped), estimate_tokens(ctx)
assert FIT_WIN + DROP_WIN == TOPK and DROP_WIN > 0 and TOPK * HB_MEAN < budget.chunks, (FIT_WIN, DROP_WIN, HB_MEAN, budget.chunks)

# the usage selftest: its rows (the reader's starting data) and its output (the expected block), from the kit itself
usg_tree = ast.parse((KIT / USG).read_text(encoding="utf-8"))
selftest_fn = next(n for n in usg_tree.body if isinstance(n, ast.FunctionDef) and n.name == "selftest")
ROWS = next(ast.literal_eval(s.value) for s in selftest_fn.body
            if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "rows")
SELFTEST = subprocess.run([sys.executable, "evals/usage_rows.py", "--selftest"], cwd=str(KIT),
                          capture_output=True, text=True, check=True).stdout.strip("\n")
assert "selftest OK" in SELFTEST and len(ROWS) == 3 and ROWS[0]["tenant"] == "acme", (SELFTEST[-80:], ROWS)

STATS = {
    "CHUNKS": f"{N:,}", "TOPK": str(TOPK), "MODEL": MODEL, "TIMEOUT": TIMEOUT, "RECORDS": str(RECORDS),
    "BUDGET_TOTAL": f"{TOTAL:,}", "FIXED_TOKENS": str(budget.system), "CHUNK_BUDGET": f"{budget.chunks:,}", "ANSWER_TOKENS": f"{ANSWER:,}",
    "HB_MEAN": str(HB_MEAN), "WIN_TOKENS": str(WIN), "FIT_WIN": str(FIT_WIN), "DROP_WIN": str(DROP_WIN), "WIN_CONTEXT": str(WIN_CONTEXT),
    "RS_REQ": f"{85 / 1000:.3f}", "SELFTEST": html.escape(SELFTEST),
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the reader's script: usage_rows.py's arithmetic and main.py's rules in JavaScript
JS = """<script>
(function(){
  'use strict';
  var SELFTEST = __ROWS__;
  var root = document.getElementById('reader'); if (!root) return;
  var ta = document.getElementById('ur-rows'), caseSel = document.getElementById('ur-case'), reset = document.getElementById('ur-reset'),
      meta = document.getElementById('ur-meta'), table = document.getElementById('ur-table'), read = document.getElementById('ur-read');
  var STAGES = ['retrieve_ms', 'rerank_ms', 'generate_ms'], USD_INR = 85;
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function has(r, k){ return r[k] !== undefined && r[k] !== null; }
  function num(v){ var n = Number(v); return isFinite(n) ? n : 0; }
  /* Python's round() on the 95th position: half to even, as usage_rows.p95() computes it */
  function roundHalfEven(x){ var f = Math.floor(x), d = x - f; if (d < 0.5) return f; if (d > 0.5) return f + 1; return f % 2 === 0 ? f : f + 1; }
  function p95(values){ if (!values.length) return 0; var s = values.slice().sort(function(a, b){ return a - b; }); return s[Math.max(0, roundHalfEven(0.95 * s.length) - 1)]; }
  function lines(rows){ return rows.map(function(r){ return JSON.stringify(r); }).join('\\n'); }
  function parse(text){
    var rows = [], t = text.trim();
    function take(o){ if (!o || typeof o !== 'object') return; if (Array.isArray(o)) { o.forEach(take); return; } if (o.jsonPayload) o = o.jsonPayload;
      if (has(o, 'pool') || has(o, 'latency_ms') || has(o, 'retrieve_ms') || has(o, 'tenant')) rows.push(o); }
    if (!t) return rows;
    try { take(JSON.parse(t)); return rows; } catch (e) {}
    t.split('\\n').forEach(function(line){ line = line.trim(); if (!line) return; try { take(JSON.parse(line)); } catch (e) { rows.push({_bad: line.slice(0, 60)}); } });
    return rows;
  }
  function flat(r){ var f = {}; Object.keys(r).forEach(function(k){ f[k] = r[k]; }); if (r.stages && typeof r.stages === 'object') Object.keys(r.stages).forEach(function(k){ f[k] = r.stages[k]; }); return f; }
  function group(rows){
    var acc = {}, order = [];
    rows.forEach(function(raw){ if (raw._bad) return; var r = flat(raw), k = has(r, 'tenant') ? String(r.tenant) : 'an answer';
      if (!acc[k]) { acc[k] = {key: k, answers: 0, usd: 0, lat: [], unans: 0, st: {retrieve_ms: [], rerank_ms: [], generate_ms: []}, pool: []}; order.push(k); }
      var a = acc[k]; a.answers += 1; a.usd += num(r.cost_usd); a.lat.push(num(r.latency_ms)); a.unans += num(r.unanswerable_flag);
      STAGES.forEach(function(s){ if (has(r, s)) a.st[s].push(num(r[s])); }); if (has(r, 'pool')) a.pool.push(num(r.pool)); });
    return order.map(function(k){ return acc[k]; }).sort(function(x, y){ return y.usd - x.usd; });
  }
  function renderTable(groups){
    var h = '<table><thead><tr><th>tenant</th><th>answers</th><th>INR</th><th>p95 ms</th><th>retrieve</th><th>rerank</th><th>generate</th><th>pool</th><th>unans</th></tr></thead><tbody>';
    groups.forEach(function(a){ var avg = a.pool.length ? a.pool.reduce(function(s, v){ return s + v; }, 0) / a.pool.length : 0;
      h += '<tr><td>' + esc(a.key) + '</td><td class="num" data-label="answers">' + a.answers + '</td><td class="num" data-label="INR">' + (a.usd * USD_INR).toFixed(2) + '</td><td class="num" data-label="p95 ms">' + p95(a.lat) + '</td>' +
           STAGES.map(function(s){ return '<td class="num" data-label="' + s.replace('_ms', '') + '">' + p95(a.st[s]) + '</td>'; }).join('') +
           '<td class="num" data-label="pool">' + (Math.round(avg * 10) / 10).toFixed(1) + '</td><td class="num" data-label="unans">' + (a.answers ? (a.unans / a.answers).toFixed(2) : '0.00') + '</td></tr>'; });
    table.innerHTML = h + '</tbody></table>';
  }
  function reading(raw, i){
    if (raw._bad) return '<div class="ur-row"><h5>line ' + (i + 1) + '</h5><ul><li class="flag">not JSON: ' + esc(raw._bad) + '</li></ul></div>';
    var r = flat(raw), L = [], flag = function(t){ L.push('<li class="flag">' + t + '</li>'); }, say = function(t){ L.push('<li>' + t + '</li>'); };
    var pool = num(r.pool), backend = r.model_backend || r.backend || '', cache = r.cache_hit === 'semantic' || backend === 'cache', none = backend === 'none';
    var head = (has(r, 'tenant') ? esc(r.tenant) : 'an answer') + (r.event ? ' &middot; ' + esc(r.event) : '') + (r.brain ? ' &middot; ' + esc(r.brain) : '');
    if (!has(r, 'pool') && !has(r, 'retrieve_ms')) say('a row from before the stage clocks: counted in answers and in nothing else');
    else if (pool === 0 && cache) say('pool 0 with backend cache: served from the answer cache, so no pool, no reranker, no model; rerank and generate read 0, cost 0');
    else if (pool === 0 && (none || r.answerable === false)) say('pool 0: nothing retrieved, so the empty-pool refusal in the contract\\'s shape; no reranker, no model, cost 0; unanswerable_flag 1 is what the alert counts');
    else if (pool === 0) say('pool 0 with no backend named: an answer-cache hit or an empty pool; the row\\'s model_backend tells them apart');
    else {
      var v = has(r, 'vector_chunks') ? num(r.vector_chunks) : null, g = num(r.graph_chunks), m = num(r.managed_chunks);
      say('the reranker saw ' + pool + ' candidates' + (v !== null ? ': ' + v + ' from the index' + (g ? ', ' + g + ' from the graph' : '') + (m ? ', ' + m + ' from a managed store' : '') : ''));
      if (r.retrieval_backend === 'vector' && v === 0) flag('vector_chunks 0 under a vector backend: the Firestore rung answered (vector_search_fallback in the log), the case make smoke refuses');
      if (num(r.rerank_fallback) === 1) flag('rerank_fallback 1: the Ranking API did not answer inside RERANK_TIMEOUT_S; the pool by retrieval score stood in, a degraded order that is counted, and the log\\'s rerank_fallback line names the error');
      else if (has(r, 'rerank_ms')) say('the Ranking API ordered the pool in ' + num(r.rerank_ms) + ' ms');
      if (r.answerable === false) say('answerable false with a pool: the model found nothing usable in the packed set; unanswerable_flag 1');
    }
    if (has(r, 'retrieve_ms') && has(r, 'rerank_ms') && has(r, 'generate_ms')) {
      var sum = num(r.retrieve_ms) + num(r.rerank_ms) + num(r.generate_ms), clocks = 'retrieve ' + num(r.retrieve_ms) + ' + rerank ' + num(r.rerank_ms) + ' + generate ' + num(r.generate_ms) + ' = ' + sum;
      if (has(r, 'latency_ms')) { var rest = num(r.latency_ms) - sum;
        if (rest >= 0) say(clocks + ' of ' + num(r.latency_ms) + ' ms; the other ' + rest + ' ms is the guard, the cache lookup, packing and the response screen');
        else flag(clocks + ' ms on the clocks exceeds the whole, ' + num(r.latency_ms) + ' ms: not one answer\\'s row'); }
      else say(clocks + ' ms on the three clocks');
    }
    if (num(r.policy_fallback) === 1) say('policy_fallback 1: the tenant\\'s data_region sent this request to the kit\\'s index instead of its managed store; a policy working, not a fault');
    if (has(r, 'cost_usd')) say('cost $' + num(r.cost_usd).toFixed(4) + ' = Rs ' + (num(r.cost_usd) * USD_INR).toFixed(2) + (r.model ? ' at ' + esc(r.model) : '') + (backend ? ' through ' + esc(backend) : ''));
    return '<div class="ur-row"><h5>' + head + '</h5><ul>' + L.join('') + '</ul></div>';
  }
  function withCase(name){
    var base = SELFTEST[0], row;
    if (name === 'fallback') row = Object.assign({}, base, {rerank_fallback: 1});
    else if (name === 'empty') row = {tenant: base.tenant, event: 'query', brain: base.brain, model: base.model, model_backend: 'none', tokens_in: 0, tokens_out: 0, cost_usd: 0, latency_ms: base.retrieve_ms, answerable: false, unanswerable_flag: 1, retrieve_ms: base.retrieve_ms, rerank_ms: 0, generate_ms: 0, pool: 0, rerank_fallback: 0};
    else if (name === 'cache') row = {tenant: base.tenant, event: 'query', brain: base.brain, model: base.model, model_backend: 'cache', tokens_in: 0, tokens_out: 0, cost_usd: 0, latency_ms: base.retrieve_ms, answerable: true, unanswerable_flag: 0, retrieve_ms: base.retrieve_ms, rerank_ms: 0, generate_ms: 0, pool: 0, rerank_fallback: 0};
    else if (name === 'firestore') row = Object.assign({}, base, {retrieval_backend: 'vector', vector_chunks: 0});
    else return;
    ta.value = (ta.value.trim() ? ta.value.replace(/\\s+$/, '') + '\\n' : '') + JSON.stringify(row);
    render();
  }
  function render(){
    var rows = parse(ta.value), good = rows.filter(function(r){ return !r._bad; }), bad = rows.length - good.length;
    meta.textContent = rows.length ? good.length + ' row' + (good.length === 1 ? '' : 's') + ' read' + (bad ? ', ' + bad + ' not JSON' : '') + '; USD_INR=' + USD_INR + '; p95 is the 95th position of the sorted list, as usage_rows.p95() takes it'
                                   : 'no rows: paste some, or press the button';
    renderTable(group(rows));
    read.innerHTML = rows.map(reading).join('');
  }
  ta.addEventListener('input', render);
  caseSel.addEventListener('change', function(){ withCase(caseSel.value); caseSel.value = ''; });
  reset.addEventListener('click', function(){ ta.value = lines(SELFTEST); render(); });
  ta.value = lines(SELFTEST);
  render();
})();
</script>
""".replace("__ROWS__", json.dumps(ROWS, ensure_ascii=False, separators=(",", ":")))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: model {MODEL} | timeout {TIMEOUT} s | pool {TOPK} | records {RECORDS} | budget {TOTAL} - {budget.system} fixed = {budget.chunks} for chunks"
      f" | acme mirrors {N} chunks, handbook section {HB_MEAN} tokens, page window {WIN}: {FIT_WIN} of {TOPK} full pages fit | selftest rows {len(ROWS)}")
