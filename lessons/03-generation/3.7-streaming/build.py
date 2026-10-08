"""Build lesson 3.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The texts on the page come from the kit at build time: the event names and the citation event's fields from
main.py, the empty pool's constant, the guard and cache defaults from config.py, the usage selftest's clocks
(evals/usage_rows.py) for the reader's sample, and two handbook chunks through the kit's chunker for its citations.
"""
import ast
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "3.7"
title = "<title>Lesson 3.7 Stream answers and handle failures - four events on one connection, the sources before the first token, and the failures that degrade into a line instead of a 500 | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.sr-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.sr-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.sr-wide{grid-column:1/-1;}
.sr-l select,.sr-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.sr-l textarea{font-family:var(--mono);font-size:16px;line-height:1.35;min-height:160px;resize:vertical;}
.sr-meta{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 0;}
.sr-out{display:grid;gap:8px;margin-top:8px;}
.sr-step{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;}
.sr-step b{color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;display:block;margin-bottom:2px;}
.sr-step code{overflow-wrap:anywhere;}
.sr-step ul{margin:4px 0 0;padding-left:20px;}
.sr-step li{overflow-wrap:anywhere;}
.sr-step li.flag{color:#92400e;}
.sr-step.flag{border-color:#f59e0b;background:#fffbeb;}
.sr-step.stop{border-color:#dc2626;background:#fef2f2;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
API = "services/rag-api/main.py"
GEN = "services/rag-api/generator.py"
RET = "services/rag-api/retriever.py"
GUARD = "services/rag-api/guard.py"
TEL = "services/rag-api/telemetry.py"
UI = "services/frontend/chat.py"
USG = "evals/usage_rows.py"

EXCERPTS = {
    "gen_stream_doc": ("services/rag-api/generator.py - generate_stream(): why the citations are the packed set, and why there is no schema",
                       block(GEN, "    No response_schema here on purpose", n=6)),
    "gen_stream": ("services/rag-api/generator.py - generate_stream(): the packed list once, then the tokens, then the usage",
                   block(GEN, '    yield "packed", packed', n=9) + "\n...\n" + block(GEN, "            if part.text:", n=3)),
    "stream_events": ("services/rag-api/main.py - /v1/stream: the citation events from the packed list, then each token as it comes",
                      block(API, '        for kind, payload in ([("token", hit.answer)]', n=17)),
    "stream_done": ("services/rag-api/main.py - /v1/stream: the held tokens screened, the error or the tokens, then done",
                    block(API, '        verdict, reason = screen_response("".join(held), guard)', n=12)),
    "empty_token": ("services/rag-api/main.py - /v1/stream: the empty pool and a cache hit as one token each, with their backends",
                    block(API, "        empty = None if (hit or chunks) else empty_pool_answer(model, stages)", n=1) + "\n...\n"
                    + block(API, "        if hit:                                      # the stored answer as one token", n=4)),
    "stream_row": ("services/rag-api/main.py - /v1/stream: the row, with event stream and the same columns",
                   block(API, '        row = usage_row(req, user, usage.get("tokens_in", 0)', n=5)),
    "screen_prompt": ("services/rag-api/main.py - screen_prompt(): before retrieval, a block is a 400", block(API, "def screen_prompt(", end="def screen_response(")),
    "screen_response": ("services/rag-api/main.py - screen_response(): on the buffered answer, the row's verdict", block(API, "def screen_response(", end='@app.post("/v1/query"')),
    "held": ("services/rag-api/main.py - /v1/stream: with the guard on, the tokens are held", block(API, '            elif kind == "token":', n=5)),
    "guard_client": ("services/rag-api/guard.py - the client and the template, built at import", block(GUARD, "LOCATION = os.environ.get", n=7)),
    "stream_rerank": ("services/rag-api/main.py - /v1/stream: the rerank branch and its flag, on its own clock",
                      block(API, "        if chunks:                                   # a hit brought none", n=5)),
    "rerank_fell_back": ("services/rag-api/retriever.py - rerank_fell_back(): the mark the handler reads", block(RET, "def rerank_fell_back(", end="def rerank(query")),
    "telemetry_guard": ("services/rag-api/telemetry.py and main.py - content capture off by default, and the import that must never take the API down",
                        block(TEL, 'os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"', n=4) + "\n...\n"
                        + block(API, "    import telemetry  # noqa: E402,F401", n=3)),
    "routing_fallback": ("services/rag-api/main.py - choose_model_for(): a classifier failure is never an outage",
                         block(API, '        log.warning(json.dumps({"event": "routing_fallback"', n=2)),
    "tier_stream": ("services/rag-api/generator.py - _vertex_stream(): an exhausted tier before the first token, the default model instead",
                    block(GEN, "    except errors.APIError as e:", n=8, nth=2)),
    "cache_failed": ("services/rag-api/main.py - _semantic_hit(): a cache that fails is a miss and a warning",
                     block(API, '        log.warning(json.dumps({"event": "semantic_cache_failed"', n=2)),
    "record_fn": ("services/rag-api/main.py - _record(): a counter that fails fails quietly", block(API, "def _record(usd: float)", n=6)),
    "ui_iter": ("services/frontend/chat.py - stream_answer(): the UI's reader of the same three events", block(UI, "def stream_answer(", end="def chat_page(")),
    "usage_surface": ("evals/usage_rows.py - the table by surface", block(USG, '    show("by surface"', n=1)),
}
assert EXCERPTS["stream_events"][1].rstrip().endswith("yield f\"event: token\\ndata: {json.dumps({'t': payload})}\\n\\n\""), EXCERPTS["stream_events"][1][-120:]
assert EXCERPTS["stream_done"][1].rstrip().endswith('"prompt": f"{settings.prompt_id}@{settings.prompt_version}"}'), EXCERPTS["stream_done"][1][-100:]
assert "tier_exhausted" in EXCERPTS["tier_stream"][1] and "yield from _vertex_stream" in EXCERPTS["tier_stream"][1]
assert EXCERPTS["stream_row"][1].rstrip().endswith("retrieval_backend=rbackend)"), EXCERPTS["stream_row"][1][-80:]
assert EXCERPTS["record_fn"][1].rstrip().endswith('"error": type(e).__name__}))')
assert EXCERPTS["held"][1].rstrip().endswith("\\n\\n\"") and "held.append(payload)" in EXCERPTS["held"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ texts and numbers read off the kit
grab = lambda pat, text: re.search(pat, text).group(1)
cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
GEN_MODEL = grab(r'generator_model: str = "([^"]+)"', cfg)
PROMPT = grab(r'prompt_id: str = "([^"]+)"', cfg) + "@" + grab(r'prompt_version: str = "([^"]+)"', cfg)
TIMEOUT = grab(r'rerank_timeout_s: float = Field\(([\d.]+),', cfg)
ARMOR_TEMPLATE = grab(r'armor_template: str = Field\("([^"]+)"', cfg)
assert grab(r'armor: str = Field\("([^"]+)"', cfg) == "off" and grab(r'semantic_cache: str = Field\("([^"]+)"', cfg) == "off"
main_txt = (KIT / API).read_text(encoding="utf-8")
QUOTE_CUT = int(grab(r"'quote': c\['text'\]\[:(\d+)\]", main_txt))
EVENTS = ("routing_fallback", "tier_exhausted", "vector_search_fallback", "rerank_fallback", "semantic_cache_failed",
          "semantic_cache_store_failed", "budget_record_failed", "telemetry_not_instrumented")
kit_src = "".join((KIT / p).read_text(encoding="utf-8") for p in (API, GEN, RET))
assert all(f'"event": "{e}"' in kit_src for e in EVENTS), [e for e in EVENTS if f'"event": "{e}"' not in kit_src]
EMPTY_POOL = next(ast.literal_eval(n.value) for n in ast.parse(main_txt).body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "EMPTY_POOL_ANSWER")

# the reader's sample: main.py's event shapes, two handbook chunks through the kit's chunker, the selftest's clocks
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402

handbook = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
                              "text": (KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_text(encoding="utf-8")}, "acme")
packed = [next(c for c in handbook if c["locator"] == L) for L in ("NP-03", "PB-02")]
usg_tree = ast.parse((KIT / USG).read_text(encoding="utf-8"))
selftest_fn = next(n for n in usg_tree.body if isinstance(n, ast.FunctionDef) and n.name == "selftest")
ROW = next(ast.literal_eval(s.value) for s in selftest_fn.body if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "rows")[0]


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def citation_events(chunks: list) -> str:
    return "".join(sse("citation", {"n": i, "chunk_id": c["chunk_id"], "source": c["source_uri"], "page": c.get("page_start"), "quote": c["text"][:QUOTE_CUT],
                                    "kind": c.get("kind", "text"), "media_url": None, "start": None, "end": None, "effective_from": None})
                   for i, c in enumerate(chunks, 1))


def stages(pool: int, rerank_fallback: int = 0, vector: int | None = None) -> dict:
    s = {"policy_fallback": 0, "retrieval_backend": "vector", "retrieve_ms": ROW["retrieve_ms"], "pool": pool, "graph_chunks": 0, "managed_chunks": 0,
         "vector_chunks": pool if vector is None else vector, "rerank_ms": ROW["rerank_ms"] if pool else 0, "generate_ms": ROW["generate_ms"] if pool else 0}
    if rerank_fallback:
        s["rerank_fallback"] = 1
    return s


def done(**kw) -> str:
    d = {"tokens_in": ROW["tokens_in"], "tokens_out": ROW["tokens_out"], "cached_tokens": 0, "latency_ms": ROW["latency_ms"], "stages": stages(20),
         "cache_hit": "none", "model": GEN_MODEL, "backend": "vertex", "prompt": PROMPT}
    d.update(kw)
    return sse("done", d)


answer_words = " ".join(packed[0]["text"].split()) + " [1]."
tokens = [w + " " for w in answer_words.split(" ")[:-1]] + [answer_words.split(" ")[-1]]
normal = citation_events(packed) + "".join(sse("token", {"t": t}) for t in tokens) + done()
SAMPLES = {
    "normal": normal,
    "empty": sse("token", {"t": EMPTY_POOL}) + done(tokens_in=0, tokens_out=0, stages=stages(0), backend="none", latency_ms=ROW["retrieve_ms"]),
    "cache": citation_events(packed) + sse("token", {"t": answer_words}) + done(tokens_in=0, tokens_out=0, stages=stages(0), backend="cache", cache_hit="semantic", latency_ms=ROW["retrieve_ms"]),
    "blocked": citation_events(packed) + sse("error", {"error": "the guard blocked the response"}) + done(),
    "fallback": citation_events(packed) + "".join(sse("token", {"t": t}) for t in tokens) + done(stages=stages(20, rerank_fallback=1)),
}

STATS = {"GEN_MODEL": GEN_MODEL, "PROMPT": PROMPT, "TIMEOUT": TIMEOUT, "ARMOR_TEMPLATE": ARMOR_TEMPLATE, "QUOTE_CUT": str(QUOTE_CUT)}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the reader's script
JS = """<script>
(function(){
  'use strict';
  var SAMPLES = __SAMPLES__, EVENTS = __EVENTS__;
  var root = document.getElementById('reader'); if (!root) return;
  var ta = document.getElementById('sr-text'), caseSel = document.getElementById('sr-case'), meta = document.getElementById('sr-meta'), out = document.getElementById('sr-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function step(title, body, cls){ return '<div class="sr-step' + (cls ? ' ' + cls : '') + '"><b>' + esc(title) + '</b>' + body + '</div>'; }
  function has(o, k){ return o && o[k] !== undefined && o[k] !== null; }
  function parse(text){                                                                  /* the UI's iterator: event line, data line */
    var events = [], ev = null;
    text.split(/\\r?\\n/).forEach(function(line){ line = line.trim(); if (!line) return;
      if (line.indexOf('event: ') === 0) ev = line.slice(7).trim();
      else if (line.indexOf('data: ') === 0) { var d; try { d = JSON.parse(line.slice(6)); } catch (e) { events.push({ev: ev || '?', bad: line.slice(6, 70)}); return; } events.push({ev: ev || '?', d: d}); ev = null; } });
    return events;
  }
  function render(){
    var events = parse(ta.value), cits = [], tokens = [], done = null, err = null, bad = 0, order = [];
    events.forEach(function(e){ if (e.bad) { bad++; return; } order.push(e.ev); if (e.ev === 'citation') cits.push(e.d); else if (e.ev === 'token') tokens.push(String(e.d.t === undefined ? '' : e.d.t)); else if (e.ev === 'done') done = e.d; else if (e.ev === 'error') err = e.d; });
    meta.textContent = events.length ? events.length + ' events: ' + cits.length + ' citation, ' + tokens.length + ' token, ' + (err ? '1 error, ' : '') + (done ? '1 done' : 'no done') + (bad ? ', ' + bad + ' data lines not JSON' : '') : 'no events: paste a transcript, or pick a case';
    if (!events.length) { out.innerHTML = ''; return; }
    var steps = [];
    var firstTok = order.indexOf('token'), lastCit = order.lastIndexOf('citation');
    steps.push(step('1 · the order', (cits.length ? cits.length + ' citation event' + (cits.length === 1 ? '' : 's') + ' ' + (firstTok < 0 || lastCit < firstTok ? 'before the first token, from the packed set' : '<span class="flag">after a token: not a transcript main.py wrote</span>') : 'no citation events: nothing was packed') + (cits.length ? '<ul>' + cits.map(function(c){ return '<li>[' + esc(c.n) + '] <code>' + esc(c.chunk_id) + '</code> ' + esc(String(c.source || '').split('/').pop()) + ' · page ' + esc(c.page) + ' · kind ' + esc(c.kind) + (c.effective_from ? ' · effective from ' + esc(c.effective_from) : '') + (c.media_url ? ' · media' : '') + '</li>'; }).join('') + '</ul>' : '')));
    var text = tokens.join('');
    var body2;
    if (err) body2 = '<span class="flag">event: error</span> instead of the tokens: the guard screened the finished answer and blocked it; the row was logged first with <code>guard: blocked_response</code>, and the caller sees ' + esc(JSON.stringify(err));
    else if (tokens.length === 1 && done && done.backend === 'cache') body2 = 'one token, backend <code>cache</code>: the stored answer of an earlier near-enough question, with the citations it had; cost 0, <code>cache_hit semantic</code>';
    else if (tokens.length === 1 && done && done.backend === 'none') body2 = 'one token, backend <code>none</code>: the empty pool, refused by the API without a model; the row says <code>answerable false</code>';
    else body2 = tokens.length + ' token event' + (tokens.length === 1 ? '' : 's') + ', ' + text.length + ' characters, prose with [N] marks where N is the packed position';
    steps.push(step('2 · the tokens', body2 + (text ? '<ul><li>' + esc(text.slice(0, 220)) + (text.length > 220 ? ' …' : '') + '</li></ul>' : ''), err ? 'stop' : ((tokens.length === 1 && done && (done.backend === 'cache' || done.backend === 'none')) ? 'flag' : '')));
    if (!done) { steps.push(step('3 · done', 'no done event: the stream ended early, or the transcript is cut', 'flag')); out.innerHTML = steps.join(''); return; }
    var s = done.stages || {}, L = [], flag = function(t){ L.push('<li class="flag">' + t + '</li>'); }, say = function(t){ L.push('<li>' + t + '</li>'); };
    say('<code>tokens_in ' + esc(done.tokens_in) + '</code> · <code>tokens_out ' + esc(done.tokens_out) + '</code> (the answer and its thoughts) · <code>cached_tokens ' + esc(done.cached_tokens) + '</code> · <code>model ' + esc(done.model) + '</code> · <code>backend ' + esc(done.backend) + '</code> · <code>cache_hit ' + esc(done.cache_hit) + '</code> · <code>prompt ' + esc(done.prompt) + '</code> · the price is on the row, not here');
    var pool = Number(s.pool) || 0;
    if (pool === 0) say('pool 0: ' + (done.backend === 'cache' ? 'the answer cache served it' : 'nothing retrieved') + '; rerank and generate read 0 because they never ran');
    else { say('the reranker saw ' + pool + ' candidates' + (has(s, 'vector_chunks') ? ', ' + s.vector_chunks + ' from the index' : ''));
      if (s.retrieval_backend === 'vector' && Number(s.vector_chunks) === 0) flag('vector_chunks 0 under a vector backend: the Firestore rung answered, a vector_search_fallback line in the log');
      if (Number(s.rerank_fallback) === 1) flag('rerank_fallback 1: the Ranking API did not answer inside its deadline; the pool by retrieval score stood in, a rerank_fallback line in the log, and the citations are in the retriever\\'s order');
      else if (has(s, 'rerank_ms')) say('the Ranking API ordered the pool in ' + s.rerank_ms + ' ms'); }
    if (has(s, 'retrieve_ms') && has(s, 'rerank_ms') && has(s, 'generate_ms')) { var sum = Number(s.retrieve_ms) + Number(s.rerank_ms) + Number(s.generate_ms); say('retrieve ' + s.retrieve_ms + ' + rerank ' + s.rerank_ms + ' + generate ' + s.generate_ms + ' = ' + sum + ' of ' + esc(done.latency_ms) + ' ms; the first token came somewhere inside generate, which no field records'); }
    if (Number(s.policy_fallback) === 1) say('policy_fallback 1: the tenant\\'s data_region sent this request to the kit\\'s index');
    steps.push(step('3 · done', '<ul>' + L.join('') + '</ul>', L.some(function(x){ return x.indexOf('class="flag"') >= 0; }) ? 'flag' : ''));
    steps.push(step('4 · what did not appear', 'no fallback is named in the events themselves; of the eight the API can log, only <code>rerank_fallback</code> and <code>vector_search_fallback</code> leave a trace in done.stages, the other six are log lines: ' + EVENTS.filter(function(e){ return e !== 'rerank_fallback' && e !== 'vector_search_fallback'; }).map(function(e){ return '<code>' + e + '</code>'; }).join(', ')));
    out.innerHTML = steps.join('');
  }
  ta.addEventListener('input', render);
  caseSel.addEventListener('change', function(){ if (SAMPLES[caseSel.value]) { ta.value = SAMPLES[caseSel.value]; render(); } caseSel.value = ''; });
  ta.value = SAMPLES.normal;
  render();
})();
</script>
""".replace("__SAMPLES__", json.dumps(SAMPLES, ensure_ascii=False)).replace("__EVENTS__", json.dumps(list(EVENTS)))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: model {GEN_MODEL} | prompt {PROMPT} | quote cut {QUOTE_CUT} | rerank timeout {TIMEOUT} | armor template {ARMOR_TEMPLATE} | events {len(EVENTS)}"
      f" | sample citations {[c['chunk_id'] for c in packed]} | sample tokens {len(tokens)}")
