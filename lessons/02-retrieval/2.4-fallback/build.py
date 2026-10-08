"""Build lesson 2.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The numbers and lists on the page come from the kit at build time: the composite vector indexes from
terraform/firestore_indexes.tf (the rung finder's table), the backend names and filter keys from the API's
config and schemas, the index and endpoint names from vector.tf, the settings cache window from main.py, the
smoke's two sentences from smoke/smoke.py, and the reads estimate from the size of acme's mirror.
"""
import html
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "2.4"
title = "<title>Lesson 2.4 Test fallback without losing tenant or metadata filters - the rung beneath the index, the three predicates that hold on the way down, and the smoke that refuses a quiet substitution | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rl-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;}
.rl-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;gap:2px;min-width:0;}
.rl-main{border-color:var(--teal);background:var(--teal-light);}
.rl-stage{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.rl-what{font-size:12.5px;line-height:1.5;color:var(--slate);}
.rl-field{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);overflow-wrap:anywhere;}
.rf-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.rf-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.rf-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rf-boxes{display:flex;gap:16px;flex-wrap:wrap;}
.rf-boxes label{display:inline-flex;align-items:center;gap:6px;min-height:44px;font-size:var(--small-size);color:var(--slate);}
.rf-boxes input{width:22px;height:22px;margin:0;}
.rf-out{display:grid;gap:8px;}
.rf-step{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;}
.rf-step b{color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;display:block;margin-bottom:2px;}
.rf-step code{overflow-wrap:anywhere;}
.rf-step.flag{border-color:#f59e0b;background:#fffbeb;}
.rf-step.stop{border-color:#dc2626;background:#fef2f2;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RET = "services/rag-api/retriever.py"
CFG = "services/rag-api/config.py"
API = "services/rag-api/main.py"
SCH = "services/rag-api/schemas.py"
TEN = "shared/tenancy.py"
MK = "mk/ingestion.mk"
PROBE = "commands/check-firestore-fallback.py"
IDX = "terraform/firestore_indexes.tf"
SQL = "terraform/sql/tenant_daily.sql"
SMOKE = "smoke/smoke.py"
RECON = "services/ingest/reconcile.py"
USG = "evals/usage_rows.py"


def nth_after(rel: str, start: str, after: str) -> int:
    """Which occurrence of `start` is the first one after the line containing `after`."""
    lines = (KIT / rel).read_text(encoding="utf-8").splitlines()
    h = next(i for i, line in enumerate(lines) if after in line)
    return sum(1 for line in lines[:h] if start in line) + 1


EXCERPTS = {
    "fallback_fn": ("services/rag-api/retriever.py - _firestore_fallback(): the rung, with the three predicates as pre-filters",
                    block(RET, "def _firestore_fallback(", end="def newest_per_source(")),
    "filter_keys": ("services/rag-api/schemas.py - FILTER_KEYS: the two keys a caller may send, on every path alike",
                    block(SCH, "# The filter keys a caller may send", n=5)),
    "indexes_tf": ("terraform/firestore_indexes.tf - the filter combinations, each a composite vector index of its own",
                   block(IDX, "# Filter combinations used by the Firestore vector fallback.", end='resource "google_firestore_index" "chunks_filter_vector"')),
    "choose_for": ("services/rag-api/main.py - choose_for(): the deployment's backend against the tenant's pin",
                   block(API, "def choose_for(")),
    "dense_branch": ("services/rag-api/retriever.py - _dense_retrieve(): the chosen road onto the rung",
                     block(RET, '    if backend == "firestore":', n=5)),
    "mk_pin": ("mk/ingestion.mk - the tenant-backend target", block(MK, "# Which store answers ONE tenant's questions", end="# `make up` returns")),
    "chaos_except": ("services/rag-api/retriever.py - the chaos rung: the index raised, Firestore answers, the log says so",
                     block(RET, "    except Exception as e:", n=8, nth=nth_after(RET, "    except Exception as e:", 'if settings.retrieval_mode == "hybrid":'))),
    "counts": ("services/rag-api/main.py - the count the smoke reads", block(API, '    stages["vector_chunks"] = sum(', n=1)),
    "smoke_tier": ("smoke/smoke.py - check 3a: the pair, and the sentence it prints for each case",
                   block(SMOKE, '    if j and ver.get("retrieval_backend") == "vector"', n=8)),
    "probe_verify": ("commands/check-firestore-fallback.py - verify_hits(): what every returned row must satisfy",
                     block(PROBE, "def verify_hits(", end="def main(")),
    "probe_modes": ("commands/check-firestore-fallback.py - both current modes through the kit's own function",
                    block(PROBE, "    previous = settings.retrieval_current_only", n=10)),
    "mk_status": ("mk/ingestion.mk - vector-status: the index's own count", block(MK, "# `make up` returns with the index created and EMPTY", end="# Block until the tier holds vectors")),
    "mk_backfill": ("mk/ingestion.mk - backfill-vectors: the tier from the rows", block(MK, "# The ANN tier from the rows.", end="# 12.5's live cells")),
    "backfill_plan": ("services/ingest/reconcile.py - the plan's line", block(RECON, '            print(json.dumps({"event": "backfill_vectors_plan"', n=7)),
    "usage_backend": ("evals/usage_rows.py - the table by rung", block(USG, '    show("by retrieval backend', n=1)),
    "policy_of": ("shared/tenancy.py - policy_of() and permits(): the two pure rules",
                  block(TEN, "def policy_of(", end="def policy_for(") + "\n...\n" + block(TEN, "def permits(", end="def backend_for(")),
    "backend_for": ("services/rag-api/main.py - retrieval_backend_for(): a managed pin held against the policy",
                    block(API, "def retrieval_backend_for(")),
    "view_policy": ("terraform/sql/tenant_daily.sql - the managed share and the policy fallbacks, summed",
                    block(SQL, "  -- The managed stores' share of the pools", n=4)),
}
assert EXCERPTS["chaos_except"][1].startswith("    except Exception as e:") and "vector_search_fallback" in EXCERPTS["chaos_except"][1]
assert EXCERPTS["fallback_fn"][1].rstrip().endswith("return out")
assert EXCERPTS["smoke_tier"][1].rstrip().endswith('skipped")'), EXCERPTS["smoke_tier"][1][-80:]
assert EXCERPTS["probe_modes"][1].rstrip().endswith("settings.retrieval_current_only = previous")
assert EXCERPTS["view_policy"][1].rstrip().endswith("AS policy_fallbacks,")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ what the page and the finder read off the kit
grab = lambda pat, text: re.search(pat, text).group(1)
cfg = (KIT / CFG).read_text(encoding="utf-8")
BACKENDS = tuple(re.findall(r'"(\w+)"', grab(r"(?m)^RETRIEVAL_BACKENDS = \(([^)]*)\)", cfg)))
MANAGED = tuple(re.findall(r'"(\w+)"', grab(r"(?m)^MANAGED_BACKENDS = \(([^)]*)\)", cfg)))
TOPK = int(grab(r"top_k_retrieve: int = Field\((\d+),", cfg))
FILTER_KEYS = tuple(re.findall(r'"(\w+)"', grab(r"(?m)^FILTER_KEYS = \(([^)]*)\)", (KIT / SCH).read_text(encoding="utf-8"))))
CACHE_S = int(grab(r"now - hit\[0\] < (\d+)", (KIT / API).read_text(encoding="utf-8")))
assert BACKENDS == ("vector", "firestore", "rag_engine", "vertex_search") and MANAGED == ("rag_engine", "vertex_search") and FILTER_KEYS == ("doc_type", "kind")

idx_txt = (KIT / IDX).read_text(encoding="utf-8")
combos = re.findall(r"^\s+(\w+)\s*=\s*\[([^\]]+)\]", grab(r"(?s)chunks_filter_indexes = \{(.*?)\}", re.search(r"locals \{(.*?)\n\}", idx_txt, re.S).group(1)), re.M)
INDEXES = [{"name": "chunks_vector", "fields": ["tenant_id"]}, {"name": "chunks_current_vector", "fields": ["tenant_id", "current"]}]
INDEXES += [{"name": f"chunks_filter_vector[{name}]", "fields": re.findall(r'"(\w+)"', fields)} for name, fields in combos]
assert len(INDEXES) == 8 and all(re.search(rf'resource "google_firestore_index" "{n}"', idx_txt) for n in ("chunks_vector", "chunks_current_vector", "chunks_filter_vector"))

vec_txt = (KIT / "terraform" / "vector.tf").read_text(encoding="utf-8")
INDEX_NAME = grab(r'resource "google_vertex_ai_index" .*?display_name\s*=\s*"([^"]+)"', vec_txt.replace("\n", " "))
ENDPOINT_NAME = grab(r'resource "google_vertex_ai_index_endpoint" .*?display_name\s*=\s*"([^"]+)"', vec_txt.replace("\n", " "))

smoke_txt = (KIT / SMOKE).read_text(encoding="utf-8")
SMOKE_FAIL = "RETRIEVAL_BACKEND=vector and no chunk came from the index - the Firestore rung answered. make vector-status; make backfill-vectors APPLY=1"
assert SMOKE_FAIL[:60] in smoke_txt and "chunks came from the index" in smoke_txt and "— skipped" in smoke_txt

# the reads estimate: acme's mirror through the kit's chunker, one read per hundred index entries plus the pool
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402
N = sum(len(dc.chunk_document({"slug": p.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{p.name}", "text": p.read_text(encoding="utf-8")}, "acme"))
        for p in sorted((KIT / "evals" / "corpus" / "acme").glob("*.md")))
READS_EST = math.ceil(N / 100) + TOPK

STATS = {
    "N_INDEXES": str(len(INDEXES)), "BACKENDS": ", ".join(BACKENDS), "FILTER_KEYS": " and ".join(f"<code>{k}</code>" for k in FILTER_KEYS),
    "TOPK": str(TOPK), "CACHE_S": str(CACHE_S), "READS_EST": str(READS_EST),
    "INDEX_NAME": html.escape(INDEX_NAME), "ENDPOINT_NAME": html.escape(ENDPOINT_NAME),
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the finder: the kit's rules in JavaScript
JS = """<script>
(function(){
  'use strict';
  var INDEXES = __INDEXES__, MANAGED = __MANAGED__, TOPK = __TOPK__, CACHE_S = __CACHE__;
  var root = document.getElementById('finder'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var out = $('rf-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function step(title, body, cls){ return '<div class="rf-step' + (cls ? ' ' + cls : '') + '"><b>' + esc(title) + '</b>' + body + '</div>'; }
  function isManaged(b){ return MANAGED.indexOf(b) >= 0; }
  function render(){
    var backend = $('rf-backend').value, mode = $('rf-mode').value, pin = $('rf-pin').value, policyDoc = $('rf-policy').value,
        indexUp = $('rf-index').value === 'up', current = $('rf-current').value === 'on', fDoc = $('rf-doc').checked, fKind = $('rf-kind').checked;
    var steps = [], logs = [];
    /* 1. config.check_retrieval_modes(): hybrid needs the vector backend */
    if (mode === 'hybrid' && backend !== 'vector') {
      steps.push(step('1 · startup', 'refused: <code>RETRIEVAL_MODE=hybrid needs RETRIEVAL_BACKEND=vector</code> - the service does not start, so nothing below applies', 'stop'));
      out.innerHTML = steps.join(''); return;
    }
    steps.push(step('1 · startup', '<code>check_retrieval_modes(' + esc(backend) + ', ' + esc(mode) + ')</code> passes; <code>/version</code> reports <code>retrieval_backend ' + esc(backend) + '</code>'));
    /* 2. main.choose_for(): the pin, unless it is one the deployment cannot serve */
    var served = backend, s2;
    if (pin && pin !== backend) {
      if (isManaged(pin) && mode === 'hybrid') { logs.push('retrieval_pin_ignored'); s2 = 'the pin to <code>' + esc(pin) + '</code> is ignored: a managed store cannot fuse hybrid; served from <code>' + esc(backend) + '</code>, with a <code>retrieval_pin_ignored</code> line'; }
      else { served = pin; s2 = 'the pin wins: this tenant is served from <code>' + esc(pin) + '</code> (read once every ' + CACHE_S + ' s)'; }
    } else s2 = pin ? 'the pin names the deployment\\'s own backend: nothing changes' : 'no pin: the deployment\\'s <code>' + esc(backend) + '</code>';
    steps.push(step('2 · the pin', s2));
    /* 3. main.retrieval_backend_for(): a managed store against the tenant's data_region */
    var policy = policyDoc === 'any' ? 'any' : 'in', policyFallback = 0, s3;
    if (isManaged(served) && policy !== 'any') {
      var own = isManaged(backend) ? 'firestore' : backend; policyFallback = 1;
      s3 = 'policy <code>' + policy + '</code>' + (policyDoc === '' ? ' (a missing policy is <code>in</code>)' : '') + ' keeps this tenant\\'s text home: <code>' + esc(served) + '</code> is not asked; served from <code>' + esc(own) + '</code> with <code>policy_fallback 1</code> on the row';
      served = own;
    } else s3 = isManaged(served) ? 'policy <code>any</code>: the managed store may hold this tenant\\'s text, so it serves' : 'the kit\\'s own tier: the policy has nothing to say';
    steps.push(step('3 · the policy', s3, policyFallback ? 'flag' : ''));
    /* 4. retriever._dense_retrieve(): the rung */
    var foundBy, vectorChunks = 0, managedChunks = 0, s4, cls4 = '';
    if (isManaged(served)) { foundBy = served; managedChunks = TOPK; s4 = 'the managed store ranks its copy; the pool is stamped <code>found_by ' + esc(served) + '</code>, <code>managed_chunks ' + TOPK + '</code>'; }
    else if (served === 'firestore') { foundBy = 'firestore'; s4 = 'the chosen road: no endpoint is asked; Firestore\\'s vector index answers behind the pre-filters; <code>found_by firestore</code>'; }
    else if (indexUp) { foundBy = 'vector'; vectorChunks = TOPK; s4 = 'Vector Search answers (' + esc(mode) + ') under the restricts; <code>found_by vector</code>, <code>vector_chunks ' + TOPK + '</code>'; }
    else { foundBy = 'firestore'; logs.push('vector_search_fallback'); cls4 = 'flag'; s4 = 'the chaos rung: the index raised, one <code>vector_search_fallback</code> line, and Firestore answers dense with the same predicates; <code>found_by firestore</code>, <code>vector_chunks 0</code>' + (mode === 'hybrid' ? ' (hybrid degrades to dense here)' : ''); }
    steps.push(step('4 · the rung', s4, cls4));
    /* 5. the answer and the row */
    steps.push(step('5 · what the answer says', '<code>stages.retrieval_backend ' + esc(served) + '</code> · <code>vector_chunks ' + vectorChunks + '</code> · <code>managed_chunks ' + managedChunks + '</code> · <code>policy_fallback ' + policyFallback + '</code> · chunks stamped <code>found_by ' + esc(foundBy) + '</code>' + (logs.length ? ' · log: <code>' + logs.map(esc).join('</code>, <code>') + '</code>' : ' · no fallback line')));
    /* 6. the Firestore index the predicates need, when Firestore answers */
    if (foundBy === 'firestore') {
      var want = ['tenant_id'].concat(current ? ['current'] : []).concat(fDoc ? ['doc_type'] : []).concat(fKind ? ['kind'] : []);
      var hit = INDEXES.filter(function(ix){ return ix.fields.join(',') === want.join(','); })[0];
      steps.push(step('6 · the composite index', 'pre-filters <code>(' + want.join(', ') + ')</code> need the vector index <code>(' + want.join(', ') + ', __name__, embedding)</code>: ' + (hit ? 'declared as <code>' + esc(hit.name) + '</code> in firestore_indexes.tf' : 'not declared - Firestore refuses the query (a failed precondition naming the index)'), hit ? '' : 'stop'));
    } else steps.push(step('6 · the composite index', 'not needed: ' + (isManaged(served) ? 'the store applies the tenant and the doc_type on its own terms' : 'the restricts travel with the index query')));
    /* 7. smoke.py check 3a */
    var s7;
    if (backend === 'vector' && served === 'vector') s7 = vectorChunks > 0 ? '<code>[PASS] vector tier  ' + TOPK + ' of ' + TOPK + ' chunks came from the index</code>' : '<code>[FAIL] vector tier  ' + esc(__SMOKE_FAIL__) + '</code>';
    else s7 = '<code>[ -- ] vector tier  this request ran on ' + esc(served) + ' — skipped</code>';
    steps.push(step('7 · make smoke', s7, s7.indexOf('[FAIL]') >= 0 ? 'stop' : ''));
    out.innerHTML = steps.join('');
  }
  ['rf-backend', 'rf-mode', 'rf-pin', 'rf-policy', 'rf-index', 'rf-current', 'rf-doc', 'rf-kind'].forEach(function(id){ $(id).addEventListener('change', render); });
  render();
})();
</script>
""".replace("__INDEXES__", json.dumps(INDEXES, separators=(",", ":"))).replace("__MANAGED__", json.dumps(list(MANAGED))) \
   .replace("__TOPK__", str(TOPK)).replace("__CACHE__", str(CACHE_S)).replace("__SMOKE_FAIL__", json.dumps(SMOKE_FAIL))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: backends {BACKENDS} | managed {MANAGED} | filter keys {FILTER_KEYS} | pool {TOPK} | pin cache {CACHE_S} s | indexes {len(INDEXES)}"
      f" | index {INDEX_NAME!r} endpoint {ENDPOINT_NAME!r} | acme mirror {N} chunks -> about {READS_EST} reads a question")
