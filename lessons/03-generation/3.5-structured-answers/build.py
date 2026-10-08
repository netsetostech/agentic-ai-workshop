"""Build lesson 3.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The numbers and texts on the page come from the kit at build time: the contract's limits from
shared/documind_schemas.py, the generator's settings and rates from config.py and cost.py, the empty pool's constant
from main.py, the resolver bench's two packed chunks from the kit's chunker, and the offline cell of step 3, which is
executed here so its expected output is the kit's own.
"""
import ast
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "3.5"
title = "<title>Lesson 3.5 Generate structured answers, citations and refusals - the three moments of one contract, the numbers a model may cite, and the two shapes of not in my documents | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rv-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.rv-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.rv-wide{grid-column:1/-1;}
.rv-l select,.rv-l textarea,.rv-l input{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rv-l textarea{font-family:var(--mono);font-size:16px;line-height:1.35;min-height:150px;resize:vertical;}
.rv-pair{display:flex;gap:8px;}
.rv-pair input{width:50%;min-width:0;font-family:var(--mono);}
.rv-out{display:grid;gap:8px;}
.rv-step{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;}
.rv-step b{color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;display:block;margin-bottom:2px;}
.rv-step code{overflow-wrap:anywhere;}
.rv-step pre{margin:6px 0 0;padding:8px;background:#1e293b;color:#e2e8f0;border-radius:8px;font-family:var(--mono);font-size:var(--kicker-size);line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere;}
.rv-step ul{margin:4px 0 0;padding-left:20px;}
.rv-step li{overflow-wrap:anywhere;}
.rv-step.flag{border-color:#f59e0b;background:#fffbeb;}
.rv-step.stop{border-color:#dc2626;background:#fef2f2;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
GEN = "services/rag-api/generator.py"
CFG = "services/rag-api/config.py"
API = "services/rag-api/main.py"
SCH = "shared/documind_schemas.py"
RSP = "services/rag-api/schemas.py"
COST = "services/rag-api/cost.py"

EXCERPTS = {
    "draft_class": ("shared/documind_schemas.py - DraftCitation and ModelDraft: what the model is asked for",
                    block(SCH, "class DraftCitation(BaseModel):", end="def resolve(")),
    "citation_class": ("shared/documind_schemas.py - Citation and RAGAnswer: what a caller receives, and the contract",
                       block(SCH, "class Citation(BaseModel):", end="class DraftCitation(")),
    "resolve_fn": ("shared/documind_schemas.py - resolve(): the draft's numbers against the packed list",
                   block(SCH, "    cits: List[Citation] = []", end="    return RAGAnswer(") + "\n" + block(SCH, "    return RAGAnswer(", n=2)),
    "empty_pool": ("services/rag-api/main.py - EMPTY_POOL_ANSWER: the refusal the API writes itself",
                   block(API, "EMPTY_POOL_ANSWER = (", n=3)),
    "generate_fn": ("services/rag-api/generator.py - generate(): the pack, the prompt, the call, the resolution against the packed list, the envelope",
                    block(GEN, "    context, packed = _pack(query, chunks)", n=7) + "\n...\n" + block(GEN, "    ans = resolve(draft, packed)", n=8)),
    "response_class": ("services/rag-api/schemas.py - RAGResponse: the contract plus the transport envelope",
                       block(RSP, "class RAGResponse(RAGAnswer):", end="class StreamEvent(")),
    "rule_three": ("services/rag-api/generator.py - the system prompt's five rules", block(GEN, 'SYSTEM = """You are DocuMind', end="# The ledger's second half")),
    "empty_pool_fn": ("services/rag-api/main.py - empty_pool_answer(): the same shape, no model, the clocks at 0",
                      block(API, "def empty_pool_answer(", n=1) + "\n...\n" + block(API, '    stages["rerank_ms"] = stages["generate_ms"] = 0', n=3)),
    "unanswerable_flag": ("services/rag-api/main.py - usage_row(): the flag the alert counts, beside the backend that tells the refusals apart",
                          block(API, '            "unanswerable_flag": 0 if answerable else 1,', n=2)),
    "call_fn": ("services/rag-api/generator.py - _call(): one generate_content with the structured-answer config",
                block(GEN, "def _call(prompt: str, packed", end="def _exhausted_tier(")),
    "usage_fn": ("services/rag-api/generator.py - _usage(): what one attempt billed, the thoughts counted as output",
                 block(GEN, "def _usage(r)", end="def _add(")),
    "draft_fn": ("services/rag-api/generator.py - _draft(): the parsed class, or the text read and validated, one violation repaired",
                 block(GEN, "    if isinstance(r.parsed, ModelDraft):", end="def _finish_reason(")),
    "client_for": ("services/rag-api/generator.py - _client_for(): a name on global, a tuned endpoint on its own location",
                   block(GEN, "def _client_for(model: str)", end="# ----------------------------------------------------------------------------- the gateway backend")),
    "endpoint_location": ("services/rag-api/generator.py - _endpoint_location(): the setting, else the path, else the region",
                          block(GEN, "def _endpoint_location(model: str)", end="def _client_for(")),
    "choose_model": ("services/rag-api/main.py - choose_model_for(): the router when ROUTING is on, else the generator model",
                     block(API, "def choose_model_for(query: str)", end="def tenant_settings(")),
    "exhausted": ("services/rag-api/generator.py - a 429 from a routed tier is answered by the default model, with a line",
                  block(GEN, "def _call_or_fallback(", end="def _quote_limit(")),
    "retry_guard": ("services/rag-api/generator.py - cut off is not refused: once more with three times the room",
                    block(GEN, '    if draft is None and _finish_reason(r) == "MAX_TOKENS":', n=9)),
    "unparsed": ("services/rag-api/generator.py - no draft after the retry: a 502 that names the finish reason, never a refusal",
                 block(GEN, "    if draft is None:", n=10)),
}
assert "class ModelDraft" in EXCERPTS["draft_class"][1] and "class RAGAnswer" in EXCERPTS["citation_class"][1]
assert EXCERPTS["resolve_fn"][1].rstrip().endswith("confidence=draft.confidence, answerable=draft.answerable)"), EXCERPTS["resolve_fn"][1][-90:]
assert EXCERPTS["empty_pool"][1].rstrip().endswith('"expect is ingested and current, or ask with the words it uses.")')
assert EXCERPTS["unparsed"][1].rstrip().endswith('raise HTTPException(502, f"generation produced no parseable answer ({reason})")'), EXCERPTS["unparsed"][1][-120:]
assert EXCERPTS["retry_guard"][1].rstrip().endswith('"thoughts": getattr(r.usage_metadata, "thoughts_token_count", None)}))')
assert "response_schema=ModelDraft" in EXCERPTS["call_fn"][1] and "tier_exhausted" in EXCERPTS["exhausted"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ numbers and texts read off the kit
grab = lambda pat, text: re.search(pat, text).group(1)
cfg = (KIT / CFG).read_text(encoding="utf-8")
ANSWER = int(grab(r"max_answer_tokens: int = (\d+)", cfg))
TOTAL = int(grab(r"max_context_tokens: int = (\d+)", cfg))
GEN_MODEL = grab(r'generator_model: str = "([^"]+)"', cfg)
PROMPT_VERSION = grab(r'prompt_version: str = "([^"]+)"', cfg)
cost_txt = (KIT / COST).read_text(encoding="utf-8")
RATE_IN, RATE_OUT = (float(x) for x in re.search(r'"' + re.escape(GEN_MODEL) + r'": \(([\d.]+), ([\d.]+)\)', cost_txt).groups())
USD_INR = grab(r'USD_INR = float\(os.environ.get\("USD_INR_RATE", "([\d.]+)"\)\)', cost_txt)
sch = (KIT / SCH).read_text(encoding="utf-8")
QUOTE_CIT = int(grab(r"quote: str = Field\(max_length=(\d+)\)", sch))
QUOTE_DRAFT = int(grab(r"quote: str = Field\(max_length=(\d+), description", sch))
CONFIDENCE = re.findall(r'"(\w+)"', grab(r'confidence: Literal\[([^\]]+)\]', sch))
assert QUOTE_CIT == 500 and QUOTE_DRAFT == 200 and CONFIDENCE == ["high", "medium", "low"]
main_tree = ast.parse((KIT / API).read_text(encoding="utf-8"))
EMPTY_POOL = next(ast.literal_eval(n.value) for n in main_tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "EMPTY_POOL_ANSWER")

sys.path[:0] = [str(KIT), str(KIT / "services" / "rag-api")]
from context_budget import TokenBudget, estimate_tokens  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402

gen_tree = ast.parse((KIT / GEN).read_text(encoding="utf-8"))
K = {n.targets[0].id: ast.literal_eval(n.value) for n in gen_tree.body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
QUESTION = "What is the notice period for a confirmed E3?"
budget = TokenBudget.fit(TOTAL, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {QUESTION}", estimate_tokens, answer=ANSWER)

# the offline cell of step 3, run here: the expected block is its output
part_b = pb.part(LESSON, "b")
cell_src = html.unescape(part_b.split("<!-- cell:offline -->", 1)[1].split("python - &lt;&lt;'PY'\n", 1)[1].split("\nPY</pre>", 1)[0])
run = subprocess.run([sys.executable, "-"], input=cell_src, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8",
                     env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})     # the lane's shell is UTF-8; a Windows console is not
assert run.returncode == 0, run.stderr[-800:]
OFFLINE_OUT = run.stdout.strip("\n")
assert "2 of 3 citations kept" in OFFLINE_OUT and OFFLINE_OUT.count("refused (") == 3 and "the empty pool's" in OFFLINE_OUT, OFFLINE_OUT[-400:]

# the resolver bench's two packed chunks, from the kit's chunker
handbook = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
                              "text": (KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_text(encoding="utf-8")}, "acme")
packed = [next(c for c in handbook if c["locator"] == L) for L in ("NP-03", "PB-02")]
PACKED = [{"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "page": c.get("page_start"), "text": c["text"], "kind": c.get("kind", "text")} for c in packed]
words = lambda t, n: " ".join(t.split()[:n])
GOOD = {"answer": "A confirmed employee in grade E3 serves the notice period in NP-03 [1]; probation is different [2].",
        "citations": [{"source": 1, "quote": words(packed[0]["text"], 12)}, {"source": 2, "quote": words(packed[1]["text"], 10)}],
        "confidence": "high", "answerable": True}

STATS = {
    "GEN_MODEL": GEN_MODEL, "PROMPT_VERSION": PROMPT_VERSION, "ANSWER": f"{ANSWER:,}", "ANSWER_RAW": str(ANSWER),
    "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": USD_INR.rstrip("0").rstrip("."), "RS_1K_IN": f"{RATE_IN * float(USD_INR) / 1000:.3f}",
    "QUOTE_CIT": str(QUOTE_CIT), "QUOTE_DRAFT": str(QUOTE_DRAFT), "CHUNK_BUDGET_RAW": str(budget.chunks),
    "OFFLINE_OUT": html.escape(OFFLINE_OUT),
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the bench's script: the schema's rules, _draft()'s repair, resolve() and price() in JavaScript
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var root = document.getElementById('resolver'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var ta = $('rv-draft'), caseSel = $('rv-case'), tokIn = $('rv-in'), tokOut = $('rv-out'), out = $('rv-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function step(title, body, cls){ return '<div class="rv-step' + (cls ? ' ' + cls : '') + '"><b>' + esc(title) + '</b>' + body + '</div>'; }
  function isInt(v){ return typeof v === 'number' && isFinite(v) && Math.floor(v) === v; }
  function problems(o){                                                                /* pydantic's rules for ModelDraft, ported */
    var p = [];
    if (!o || typeof o !== 'object' || Array.isArray(o)) return ['the reply is not an object'];
    if (typeof o.answer !== 'string') p.push('answer: Input should be a valid string');
    if (!Array.isArray(o.citations)) p.push('citations: Input should be a valid list');
    else o.citations.forEach(function(c, i){
      if (!c || typeof c !== 'object') { p.push('citations.' + i + ': Input should be a valid dictionary'); return; }
      if (!isInt(c.source)) p.push('citations.' + i + '.source: Input should be a valid integer');
      else if (c.source < 1) p.push('citations.' + i + '.source: Input should be greater than or equal to 1');
      if (typeof c.quote !== 'string') p.push('citations.' + i + '.quote: Input should be a valid string');
      else if (c.quote.length > D.quoteDraft) p.push('citations.' + i + '.quote: String should have at most ' + D.quoteDraft + ' characters');
    });
    if (D.confidence.indexOf(o.confidence) < 0) p.push("confidence: Input should be 'high', 'medium' or 'low'");
    if (typeof o.answerable !== 'boolean') p.push('answerable: Input should be a valid boolean');
    return p;
  }
  function repair(o){                                                                  /* _draft(): an over-long quote is trimmed to the contract, once */
    var done = false;
    (o.citations || []).forEach(function(c){ if (c && typeof c.quote === 'string' && c.quote.length > D.quoteDraft) { c.quote = c.quote.slice(0, D.quoteDraft - 3).replace(/\\s+$/, '') + '...'; done = true; } });
    return done;
  }
  function resolve(draft){                                                             /* resolve(): against the packed list, out of range dropped */
    var cits = [];
    draft.citations.forEach(function(d){ if (!(1 <= d.source && d.source <= D.packed.length)) return; var c = D.packed[d.source - 1];
      cits.push({chunk_id: c.chunk_id, source_uri: c.source_uri, page: c.page, quote: (d.quote || c.text).slice(0, D.quoteCit), score: 0.0, kind: c.kind, grounded: norm(c.text).indexOf(norm(d.quote || '')) >= 0}); });
    return {answer: draft.answer, citations: cits, confidence: draft.confidence, answerable: draft.answerable};
  }
  function norm(s){ return String(s).split(/\\s+/).join(' ').toLowerCase(); }
  function price(tin, tout){ var usd = (tin * D.rateIn + tout * D.rateOut) / 1e6; return '$' + usd.toFixed(6) + ' = Rs ' + (usd * D.usdInr).toFixed(4) + ' at ' + D.usdInr; }
  function render(){
    var steps = [], text = ta.value.trim(), obj = null;
    if (text === '') { out.innerHTML = step('the empty pool', 'no draft, because no model was called: the handler writes the refusal itself. <pre>' + esc(JSON.stringify({answer: D.emptyPool, citations: [], confidence: 'low', answerable: false}, null, 1)) + '</pre>envelope: <code>backend none</code>, <code>tokens_in 0</code>, <code>tokens_out 0</code>, <code>cost_usd 0.0</code>, rerank and generate clocks 0; never stored in the answer cache; <code>unanswerable_flag 1</code> on the row', 'flag'); return; }
    try { obj = JSON.parse(text); } catch (e) { out.innerHTML = step('1 · _draft()', 'the reply is not JSON: <code>json.loads</code> fails, the draft is None, and after the retry the handler raises <code>502 generation produced no parseable answer</code>, which is a failure, never a refusal', 'stop'); return; }
    var p = problems(obj), repaired = false;
    if (p.length) {
      var copy = JSON.parse(JSON.stringify(obj)); repaired = repair(copy);
      var p2 = repaired ? problems(copy) : p;
      if (p2.length) { out.innerHTML = step('1 · _draft()', 'pydantic refuses the draft, logged as <code>generation_invalid</code> with the fields that failed, and the answer becomes a 502:<ul>' + p2.map(function(x){ return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>', 'stop'); return; }
      obj = copy;
      steps.push(step('1 · _draft()', 'one violation the generator repairs rather than fails: a quote over ' + D.quoteDraft + ' characters is trimmed to the contract and the draft validated again; logged as <code>generation_repaired</code> with <ul>' + p.map(function(x){ return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>', 'flag'));
    } else steps.push(step('1 · _draft()', 'the draft validates as <code>ModelDraft</code>: ' + obj.citations.length + ' citation' + (obj.citations.length === 1 ? '' : 's') + ', confidence <code>' + esc(obj.confidence) + '</code>, answerable <code>' + obj.answerable + '</code>'));
    var ans = resolve(obj), dropped = obj.citations.length - ans.citations.length;
    steps.push(step('2 · resolve()', (ans.citations.length + ' of ' + obj.citations.length + ' citations resolved against the ' + D.packed.length + ' packed chunks' + (dropped ? '; ' + dropped + ' dropped: a number outside the packed list is not a citation' : '')) + (ans.citations.length ? '<ul>' + ans.citations.map(function(c, i){ return '<li>[' + (i + 1) + '] <code>' + esc(c.chunk_id) + '</code> page ' + c.page + ', score ' + c.score.toFixed(1) + ' (no ranker offline), kind ' + esc(c.kind) + ' · quote in the chunk: <code>' + c.grounded + '</code></li>'; }).join('') + '</ul>' : ''), dropped ? 'flag' : ''));
    var contract = {answer: ans.answer, citations: ans.citations.map(function(c){ var o = {}; ['chunk_id', 'source_uri', 'page', 'quote', 'score', 'kind'].forEach(function(k){ o[k] = c[k]; }); return o; }), confidence: ans.confidence, answerable: ans.answerable};
    steps.push(step('3 · RAGAnswer' + (ans.answerable ? '' : ', a refusal'), (ans.answerable ? 'the contract every module passes along' : 'the model\\'s refusal in the contract\\'s shape: <code>answerable false</code>, no citations, low confidence; a model call was made and billed, and the row carries <code>unanswerable_flag 1</code>') + '<pre>' + esc(JSON.stringify(contract, null, 1)) + '</pre>'));
    var tin = parseInt(tokIn.value, 10) || 0, tout = parseInt(tokOut.value, 10) || 0;
    steps.push(step('4 · the envelope', '<code>model ' + esc(D.model) + '</code> · <code>backend vertex</code> · <code>tokens_in ' + tin + '</code> · <code>tokens_out ' + tout + '</code> (the answer and its thoughts) · <code>cached_tokens 0</code> · <code>cost.price()</code> = ' + price(tin, tout)));
    out.innerHTML = steps.join('');
  }
  function withCase(name){
    var g = JSON.parse(JSON.stringify(D.good));
    if (name === 'good') {}
    else if (name === 'range') g.citations.push({source: 7, quote: 'a source that was never packed'});
    else if (name === 'long') g.citations[0].quote = D.packed[0].text.split(/\\s+/).slice(0, 60).join(' ');
    else if (name === 'invalid') g.confidence = 'certain';
    else if (name === 'refusal') g = {answer: 'The context does not contain the answer.', citations: [], confidence: 'low', answerable: false};
    else if (name === 'empty') { ta.value = ''; render(); return; }
    else return;
    ta.value = JSON.stringify(g, null, 1); render();
  }
  ta.addEventListener('input', render); tokIn.addEventListener('input', render); tokOut.addEventListener('input', render);
  caseSel.addEventListener('change', function(){ withCase(caseSel.value); caseSel.value = ''; });
  withCase('good');
})();
</script>
""".replace("__DATA__", json.dumps({"packed": PACKED, "good": GOOD, "quoteDraft": QUOTE_DRAFT, "quoteCit": QUOTE_CIT, "confidence": CONFIDENCE,
                                     "emptyPool": EMPTY_POOL, "model": GEN_MODEL, "rateIn": RATE_IN, "rateOut": RATE_OUT, "usdInr": float(USD_INR)},
                                    ensure_ascii=False, separators=(",", ":")))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(part_b)),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {GEN_MODEL} ${RATE_IN}/{RATE_OUT} per M at {USD_INR} | answer reserve {ANSWER} | quote limits draft {QUOTE_DRAFT} citation {QUOTE_CIT} | confidence {CONFIDENCE}"
      f" | chunk budget {budget.chunks} | packed ids {[c['chunk_id'] for c in PACKED]}")
