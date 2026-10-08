"""Build lesson 1.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.3"


title = "<title>Lesson 1.3 Create and validate compatible embeddings - one model, one task type, one stamp on every row | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.em-controls,.bp-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;}
.em-l,.bp-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.em-l select,.em-l input[type=text],.bp-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.bp-l input[type=range]{width:100%;min-height:44px;}
.bp-chk{flex-direction:row;align-items:center;gap:8px;min-height:44px;}
.bp-chk input{width:22px;height:22px;}
.em-own{display:none;}
.em-own.on{display:flex;}
.em-bar{height:14px;border-radius:7px;background:#e2e8f0;overflow:hidden;margin:4px 0 6px;}
.em-fill{height:100%;width:0;background:linear-gradient(90deg,#0d9488,#0891b2);transition:width .25s;}
.em-sum,.bp-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 8px;overflow-wrap:anywhere;}
.em-out{display:flex;flex-wrap:wrap;gap:8px;}
.em-chunk{flex:1 1 220px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;color:var(--slate);min-width:0;}
.em-chunk b{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);margin-bottom:4px;}
.em-chunk mark{background:#fde68a;color:#1f2937;padding:0 2px;border-radius:2px;}
.bp-out{display:flex;flex-direction:column;gap:5px;}
.bp-row{display:grid;grid-template-columns:52px 1fr;align-items:center;gap:8px;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);}
.bp-track{height:18px;background:#e2e8f0;border-radius:5px;overflow:hidden;position:relative;}
.bp-fill{height:100%;background:#0d9488;}
.bp-fill.bad{background:#dc2626;}
.bp-lbl{position:absolute;left:8px;top:0;line-height:18px;font-size:11px;color:#fff;white-space:nowrap;}
.bp-note{font-size:var(--small-size);color:var(--slate);margin-top:8px;}
@media (prefers-reduced-motion: reduce){.em-fill{transition:none;}}
"""

# ---- the setup section, shared with 3.1 (from its heading to the tenant step marker) ----
setup = setup_section()

# ---- verbatim kit excerpts ----


EXCERPTS = {
    "tf_vars": ("terraform/variables.tf - the declaration", block("terraform/variables.tf", 'variable "embedding_model"', n=9)),
    "indexer_consts": ("services/ingest/indexer.py - the constants, and the regional client", block("services/ingest/indexer.py", "EMBED_BATCH = 250", n=14)),
    "config_embed": ("services/rag-api/config.py - the API reads the same two names", block("services/rag-api/config.py", "embed_model: str = Field(", n=2)),
    "retriever_embed_query": ("services/rag-api/retriever.py - embed_query(), the question's side", block("services/rag-api/retriever.py", "def embed_query(", end="def _firestore_fallback(")),
    "indexer_embed_all": ("services/ingest/indexer.py - embed_all() and valid_vector()", block("services/ingest/indexer.py", "def embed_all(", end="def document_embedding_matches(")),
    "indexer_batches": ("services/ingest/indexer.py - batches()", block("services/ingest/indexer.py", "def batches(", end="def embed_all(")),
    "corpus_embed_batches": ("shared/documind_corpus.py - embed_batches(), the loader's copy", block("shared/documind_corpus.py", "def embed_batches(", end="def rows_of(")),
    "indexer_mirror_row": ("services/ingest/indexer.py - mirror_to_firestore(), the row and its stamp", block("services/ingest/indexer.py", "def mirror_to_firestore(", end='        if chunk.get("section"):')),
    "indexer_valid": ("services/ingest/indexer.py - valid_vector() and document_embedding_matches()", block("services/ingest/indexer.py", "def valid_vector(", end="def held_vectors(")),
    "idem_current": ("services/ingest/idempotency.py - current_chunks(): a row without the stamp does not count", block("services/ingest/idempotency.py", "def current_chunks(")),
    "makefile_backfill": ("mk/ingestion.mk - the backfill-vectors target (the Makefile includes mk/*.mk)", block("mk/ingestion.mk", "backfill-vectors: guard-project", n=5)),
    "indexer_held": ("services/ingest/indexer.py - held_vectors()", block("services/ingest/indexer.py", "def held_vectors(", end="def plan_carry_over(")),
    "indexer_plan": ("services/ingest/indexer.py - plan_carry_over() and embed_with_carry_over()", block("services/ingest/indexer.py", "def plan_carry_over(", end="def _restricts(")),
    "main_carry": ("services/ingest/main.py - where the worker calls it", block("services/ingest/main.py", "# THE CARRY-OVER (12 September 2026)", n=3)),
    "sparse": ("shared/sparse_encoder.py - the whole encoder", block("shared/sparse_encoder.py", "SPARSE_DIMS = 1 << 20", n=200)),
    "indexer_datapoint": ("services/ingest/indexer.py - _sparse() and _datapoint(): what goes to Vector Search", block("services/ingest/indexer.py", "def _sparse(", end="def to_datapoints(")),
    "hybrid_query": ("services/rag-api/hybrid.py - the question, encoded the same way", block("services/rag-api/hybrid.py", "vals, dims = sparse_encode(query_text)", n=3)),
    "vector_tf": ("terraform/vector.tf - the index the datapoints go to", block("terraform/vector.tf", "    config {", end="  # STREAM_UPDATE, not BATCH_UPDATE") + "\n  index_update_method = \"STREAM_UPDATE\""),
    "corpus_by_hash": ("shared/documind_corpus.py - seed(): the carry-over, the loader's copy", block("shared/documind_corpus.py", 'by_hash = {r["chunk_hash"]: r["embedding"] for r in live', n=8)),
    "corpus_row": ("shared/documind_corpus.py - seed(): the row it writes (model and version, no task type)", block("shared/documind_corpus.py", 'row = {**c, "doc_key": key', n=4)),
}


fill = filler(EXCERPTS, window)


# ---- the interactive pieces: real data from the corpus ----
lens = json.loads(pb.data(LESSON, "lens33.json").read_text(encoding="utf-8"))
samples = json.loads(pb.data(LESSON, "samples33.json").read_text(encoding="utf-8"))
samples["Q1"] = "How many days of notice does a confirmed employee at grade E3 serve?"
samples["Q2"] = "Can I quit while still on probation?"
samples["Q3"] = "What happens to my unused leave when I resign?"

JS = """<script>
(function(){
  'use strict';
  var SAMPLES = %s, LENS = %s;
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  /* ---- the shared-words meter: shared/sparse_encoder.py's tokens and weights, without the hash ---- */
  var meter = document.getElementById('meter');
  if (meter){
    var selA = document.getElementById('em-a'), selB = document.getElementById('em-b'), own = document.getElementById('em-own'),
        ownWrap = own.parentNode, fill = document.getElementById('em-fill'), sum = document.getElementById('em-sum'), out = document.getElementById('em-out');
    function tokens(t){ return (String(t).toLowerCase().match(/[a-z0-9\\-]+/g) || []); }
    function weights(t){ var w = {}; tokens(t).forEach(function(k){ w[k] = (w[k] || 0) + 1; }); Object.keys(w).forEach(function(k){ w[k] = 1 + (w[k] - 1) * 0.5; }); return w; }
    function cosine(a, b){ var dot = 0, na = 0, nb = 0, k; for (k in a){ na += a[k] * a[k]; if (b[k]) dot += a[k] * b[k]; } for (k in b){ nb += b[k] * b[k]; } return (na && nb) ? dot / Math.sqrt(na * nb) : 0; }
    function card(label, text, shared){
      var body = esc(text).replace(/[A-Za-z0-9\\-]+/g, function(w){ return shared[w.toLowerCase()] ? '<mark>' + w + '</mark>' : w; });
      return '<div class="em-chunk"><b>' + esc(label) + ' &middot; ' + tokens(text).length + ' words</b>' + body + '</div>';
    }
    function label(sel){ return sel.options[sel.selectedIndex].text.replace(/ \\(clause\\)$/, ''); }
    function render(){
      var a = SAMPLES[selA.value], useOwn = selB.value === 'own', b = useOwn ? own.value : SAMPLES[selB.value];
      ownWrap.className = 'em-l em-own' + (useOwn ? ' on' : '');
      var wa = weights(a), wb = weights(b), shared = {}, k, n = 0;
      for (k in wa){ if (wb[k]){ shared[k] = true; n++; } }
      var c = cosine(wa, wb);
      fill.style.width = Math.round(c * 100) + '%%';
      sum.textContent = 'shared words: ' + n + ' of ' + Object.keys(wa).length + ' and ' + Object.keys(wb).length + ' distinct  |  sparse cosine ' + c.toFixed(2) + (b.trim() ? '' : '  (type text B)');
      out.innerHTML = card(label(selA), a, shared) + card(useOwn ? 'your text' : label(selB), b, shared);
    }
    [selA, selB].forEach(function(el){ el.addEventListener('change', render); });
    own.addEventListener('input', render);
    render();
  }
  /* ---- the batch planner: services/ingest/indexer.py's batches(), with the two ceilings as parameters ---- */
  var planner = document.getElementById('planner');
  if (planner){
    var doc = document.getElementById('bp-doc'), rn = document.getElementById('bp-n'), rt = document.getElementById('bp-t'), one = document.getElementById('bp-one'),
        nv = document.getElementById('bp-n-v'), tv = document.getElementById('bp-t-v'), psum = document.getElementById('bp-sum'), pout = document.getElementById('bp-out');
    function batches(lens, EMBED_BATCH, EMBED_TOKENS){
      var out = [], cur = [], curTokens = 0;
      lens.forEach(function(L){
        var t = Math.max(1, Math.floor(L / 3));
        if (cur.length && (cur.length >= EMBED_BATCH || curTokens + t > EMBED_TOKENS)){ out.push({n: cur.length, tokens: curTokens}); cur = []; curTokens = 0; }
        cur.push(L); curTokens += t;
      });
      if (cur.length) out.push({n: cur.length, tokens: curTokens});
      return out;
    }
    function plan(){
      var lens = LENS[doc.value], n = parseInt(rn.value, 10), t = parseInt(rt.value, 10);
      nv.textContent = n; tv.textContent = t.toLocaleString('en-IN');
      var bs = one.checked ? batches(lens, 1e9, 1e9) : batches(lens, n, t), bad = 0;
      pout.innerHTML = bs.map(function(b, i){
        var refused = b.n > 250 || b.tokens > 20000; if (refused) bad++;
        var w = Math.min(100, Math.round(b.tokens / 20000 * 100));
        return '<div class="bp-row"><span>req ' + (i + 1) + '</span><div class="bp-track"><div class="bp-fill' + (refused ? ' bad' : '') + '" style="width:' + w + '%%"></div><span class="bp-lbl">' + b.n + ' texts, ~' + b.tokens.toLocaleString('en-IN') + ' tokens' + (refused ? ' - refused whole' : '') + '</span></div></div>';
      }).join('');
      psum.textContent = lens.length + ' chunks -> ' + bs.length + ' request' + (bs.length === 1 ? '' : 's') + (bad ? ', ' + bad + ' over the model\\'s ceiling' : ', all under the ceiling') + (one.checked ? '  (no rule)' : '  (ceilings ' + n + ' texts, ' + t.toLocaleString('en-IN') + ' est. tokens)');
    }
    [doc, rn, rt, one].forEach(function(el){ el.addEventListener('input', plan); el.addEventListener('change', plan); });
    plan();
  }
})();
</script>
""" % (json.dumps(samples), json.dumps(lens))

body = "".join([
    fill(pb.part(LESSON, "a")),
    setup,
    fill(pb.part(LESSON, "b")),
    fill(pb.part(LESSON, "c")),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
