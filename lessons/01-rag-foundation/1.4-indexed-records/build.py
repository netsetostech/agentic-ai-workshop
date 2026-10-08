"""Build lesson 1.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.4"


title = "<title>Lesson 1.4 Write, inspect and verify indexed records - the row, the datapoint, the mirror and the ledger, read side by side | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.wp-controls{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin-bottom:10px;}
.wp-controls select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;flex:1 1 260px;min-width:0;}
.wp-btn{font:inherit;font-size:var(--small-size);font-weight:500;min-height:44px;min-width:44px;padding:8px 14px;border:1px solid var(--teal);border-radius:8px;background:var(--card);color:var(--teal);cursor:pointer;}
.wp-btn:disabled{opacity:.45;cursor:default;}
.wp-step{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:4px 0 8px;overflow-wrap:anywhere;}
.wp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;}
.wp-cell{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;color:var(--slate);min-width:0;transition:border-color .2s,background .2s;}
.wp-cell b{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);margin-bottom:4px;}
.wp-cell.on{border-color:var(--teal);background:var(--teal-light);}
.wp-cell.hot{border:2px solid #d97706;background:#fffbeb;}
.wp-reader{margin-top:10px;padding:8px 12px;border-left:4px solid #d97706;background:#fffbeb;border-radius:0 8px 8px 0;font-size:var(--small-size);color:var(--navy);}
@media (hover:hover) and (pointer:fine){.wp-btn:hover:not(:disabled){background:var(--teal-light);}}
@media (prefers-reduced-motion: reduce){.wp-cell{transition:none;}}
"""

setup = setup_section()



ING = "services/ingest/main.py"
IDX = "services/ingest/indexer.py"
IDM = "services/ingest/idempotency.py"
RET = "services/rag-api/retriever.py"
EXCERPTS = {
    "claim": ("services/ingest/idempotency.py - claim(): the first record, written in a transaction",
              block(IDM, '    ref = db.collection("documents").document(doc_key)', end="def finish(")),
    "finish": ("services/ingest/idempotency.py - finish(): the claim becomes a record", block(IDM, "def finish(", end="def release(")),
    "main_swap": ("services/ingest/main.py - the order: staged rows, the swap, the tier", block(ING, "# THE SWAP. The new version is written STAGED", end="# THE MANAGED MIRROR (P9.2)")),
    "main_tail": ("services/ingest/main.py - then the mirror, the claim, the ledger row and the fingerprint", block(ING, "mirror_to_bigquery(_bigquery() if BQ_CHUNK_TABLE else None", end='if gone["retired_chunks"]:')),
    "main_audit": ("services/ingest/main.py - the audit event, the last record before the log line", block(ING, 'audit_emit("doc.upload",', n=9)),
    "mirror_tail": ("services/ingest/indexer.py - mirror_to_firestore(): the stage marks, and the commit", block(IDX, "        if staged:", end="def mirror_to_bigquery(")),
    "to_datapoints": ("services/ingest/indexer.py - to_datapoints() and upsert()", block(IDX, "def to_datapoints(", end="def remove_datapoints(")),
    "remove": ("services/ingest/indexer.py - remove_datapoints(): a retired id leaves the tier", block(IDX, "def remove_datapoints(", end="def reupsert(")),
    "bq": ("services/ingest/indexer.py - mirror_to_bigquery()", block(IDX, "def mirror_to_bigquery(", n=200)),
    "bq_schema": ("terraform/dataplex.tf - the chunk_source table", block("terraform/dataplex.tf", 'resource "google_bigquery_table" "chunk_source"', n=26)),
    "record_source": ("services/ingest/idempotency.py - record_source(): the ledger row", block(IDM, "def record_source(", end="def corpus_fingerprint(")),
    "fingerprint": ("services/ingest/idempotency.py - corpus_fingerprint() and refresh_fingerprint()", block(IDM, "def corpus_fingerprint(", n=200)),
    "audit_emit": ("shared/audit_log.py - emit(): one JSON object per event, in a retention-locked bucket", block("shared/audit_log.py", "def emit(", n=200)),
    "dense_restricts": ("services/rag-api/retriever.py - _dense_retrieve(): the same predicates as the worker's restricts", block(RET, '    restricts = [Namespace(name="tenant_id", allow_tokens=[tenant_id])]', n=6)),
    "dense_find": ("services/rag-api/retriever.py - _dense_retrieve(): the ANN call, and the rung's name on every chunk", block(RET, "            resp = _index_endpoint().find_neighbors(", n=5) + "\n" + block(RET, "    pool = _hydrate(ids[:settings.top_k_retrieve], scores)", n=4)),
    "fallback": ("services/rag-api/retriever.py - _firestore_fallback(): the same predicates, Firestore's own vector index", block(RET, '    query = _fs().collection(settings.chunks_collection).where("tenant_id", "==", tenant_id)', end="    out = []")),
    "backfill": ("services/ingest/indexer.py - backfill(): the tier rebuilt from the rows", block(IDX, "def backfill(", end="def mirror_to_firestore(")),
    "repair_doc": ("services/ingest/indexer.py - _repair_snapshots(): the rule for a repair", block(IDX, "def _repair_snapshots(", n=7)),
    "ttl": ("terraform/firestore_indexes.tf - the TTL policy: the only thing that ever deletes a chunk row", block("terraform/firestore_indexes.tf", '# TTL for superseded/staged chunk rows.', n=9)),
    "vec_index": ("terraform/firestore_indexes.tf - the vector index the fallback rung needs", block("terraform/firestore_indexes.tf", '# CURRENT chunks only, for the ledger-aware fallback path.', n=27)),
    "vector_status": ("commands/vector-status.sh - what make vector-status runs: the index and the deployment, as gcloud sees them", block("commands/vector-status.sh", "#!/usr/bin/env bash", n=200)),
    "stage_consts": ("services/ingest/main.py - the two clocks on a row", block(ING, 'RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))', n=2)),
}


fill = filler(EXCERPTS, window)


# ---- the write-order player: the worker's order, with the numbers of two real ingests on this lane ----
STORES = ["documents (the claim)", "chunks (the rows)", "Vector Search (datapoints)", "chunk_source (BigQuery)", "sources (the ledger row)", "ledger (the tenant)", "audit bucket + log"]
MODES = {
    "first": {
        "label": "First version: smoke_note_v1.md under acme (3 chunks)",
        "steps": [
            ["claim() in a transaction", ["processing", "", "", "", "", "", ""], "nothing yet: no row of this document is current", 0],
            ["parse and chunk: 1 page, 3 chunks (preamble, SM-01, SM-02)", ["processing", "", "", "", "", "", ""], "nothing yet", -1],
            ["DLP scan: 0 findings, so no dlp_findings row", ["processing", "", "", "", "", "", ""], "nothing yet", -1],
            ["embed_with_carry_over(): nothing held, 3 embedded in one request", ["processing", "", "", "", "", "", ""], "nothing yet", -1],
            ["mirror_to_firestore(staged=True): 3 rows, current=false, staged, expire_at in 24 h", ["processing", "3 rows staged", "", "", "", "", ""], "nothing yet: a staged row fails the current filter", 1],
            ["swap_versions(): the 3 rows flip current; nothing to retire", ["processing", "3 rows current", "", "", "", "", ""], "the Firestore rung finds 3 rows; the ANN tier still knows nothing", 1],
            ["upsert(): 3 datapoints (dense + sparse + 4 restricts)", ["processing", "3 rows current", "3 datapoints", "", "", "", ""], "both rungs answer once the stream update lands", 2],
            ["mirror_to_bigquery(): 3 rows streamed", ["processing", "3 rows current", "3 datapoints", "3 rows", "", "", ""], "the SQL lane sees them too", 3],
            ["finish(): the claim is indexed, chunks 3, reused 0, embedded 3, generation", ["indexed: 3 chunks, 0 reused, 3 embedded", "3 rows current", "3 datapoints", "3 rows", "", "", ""], "same as before", 0],
            ["record_source(): sources/acme~smoke_note_v1.md", ["indexed", "3 rows current", "3 datapoints", "3 rows", "indexed, doc_key, generation, sha256, chunks 3", "", ""], "the Versions table shows the document", 4],
            ["refresh_fingerprint(): ledger/acme changes, versions +1", ["indexed", "3 rows current", "3 datapoints", "3 rows", "indexed", "new fingerprint, last_event ingest_ok", ""], "the answer cache is stale for acme until repacked", 5],
            ["audit doc.upload, then the ingest_ok log line", ["indexed", "3 rows current", "3 datapoints", "3 rows", "indexed", "new fingerprint", "doc.upload event; ingest_ok"], "everything; the operator can prove it", 6],
        ],
    },
    "reissue": {
        "label": "Re-issue: hr_policy_2026.md revision 2 (283 chunks, lesson 1.3)",
        "steps": [
            ["claim() for the new doc_key; version 1's claim stays indexed", ["v2 processing; v1 indexed", "283 v1 rows current", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 1, as before", 0],
            ["parse and chunk: 283 chunks", ["v2 processing", "283 v1 rows current", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 1", -1],
            ["DLP scan: 0 findings", ["v2 processing", "283 v1 rows current", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 1", -1],
            ["embed_with_carry_over(): 281 held by hash, 2 embedded", ["v2 processing", "283 v1 rows current", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 1", -1],
            ["mirror_to_firestore(staged=True): 283 v2 rows staged beside the 283 current v1 rows", ["v2 processing", "283 v1 current + 283 v2 staged", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 1 only: staged rows are invisible", 1],
            ["swap_versions(): v2 rows flip current, then v1 rows are retired (expire_at in 30 days); v1's claim becomes superseded", ["v2 processing; v1 superseded", "283 v2 current + 283 v1 retired", "283 v1 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 2 only, even between the two commits (the newest-per-source guard)", 1],
            ["upsert() 283 v2 datapoints, then remove_datapoints() the 283 retired ids", ["v2 processing; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "283 v1 rows", "v1 indexed", "fingerprint of v1", ""], "version 2 on both rungs", 2],
            ["mirror_to_bigquery(): 283 v2 rows appended; the v1 rows stay (append-only)", ["v2 processing; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "283 v1 + 283 v2 rows", "v1 indexed", "fingerprint of v1", ""], "version 2", 3],
            ["finish(): v2's claim is indexed, chunks 283, reused 281, embedded 2", ["v2 indexed: 281 reused, 2 embedded; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "566 rows", "v1 indexed", "fingerprint of v1", ""], "version 2", 0],
            ["record_source(): the ledger row now names v2, reused 281, embedded 2, retired 283, effective 2026-10-01", ["v2 indexed; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "566 rows", "v2: reused 281, embedded 2, retired 283", "fingerprint of v1", ""], "the Versions table shows revision 2", 4],
            ["refresh_fingerprint(): a new fingerprint; ingest_superseded is logged with the retired keys", ["v2 indexed; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "566 rows", "v2", "new fingerprint, versions unchanged", "ingest_superseded"], "the cache record is stale: the next answer is computed fresh", 5],
            ["audit doc.upload (reused 281, embedded 2, retired 283), then ingest_ok", ["v2 indexed; v1 superseded", "283 v2 current + 283 v1 retired", "283 v2 datapoints", "566 rows", "v2", "new fingerprint", "doc.upload; ingest_ok"], "revision 2, with the undo one upload away", 6],
        ],
    },
}

JS = """<script>
(function(){
  'use strict';
  var STORES = %s, MODES = %s;
  var root = document.getElementById('writer'); if (!root) return;
  var mode = document.getElementById('wp-mode'), prev = document.getElementById('wp-prev'), next = document.getElementById('wp-next'),
      stepEl = document.getElementById('wp-step'), grid = document.getElementById('wp-grid'), reader = document.getElementById('wp-reader');
  var i = 0;
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function render(){
    var steps = MODES[mode.value].steps, s = steps[i];
    stepEl.textContent = 'step ' + (i + 1) + ' of ' + steps.length + ': ' + s[0];
    grid.innerHTML = STORES.map(function(name, k){
      var v = s[1][k], cls = 'wp-cell' + (v ? ' on' : '') + (k === s[3] ? ' hot' : '');
      return '<div class="' + cls + '"><b>' + esc(name) + '</b>' + (v ? esc(v) : '<span style="color:#94a3b8">nothing</span>') + '</div>';
    }).join('');
    reader.textContent = 'A reader asking a question now sees: ' + s[2] + '.';
    prev.disabled = i === 0; next.disabled = i === steps.length - 1;
  }
  prev.addEventListener('click', function(){ if (i > 0){ i--; render(); } });
  next.addEventListener('click', function(){ if (i < MODES[mode.value].steps.length - 1){ i++; render(); } });
  mode.addEventListener('change', function(){ i = 0; render(); });
  render();
})();
</script>
""" % (json.dumps(STORES), json.dumps(MODES))

body = "".join([
    fill(pb.part(LESSON, "a")),
    setup,
    fill(pb.part(LESSON, "b")),
    fill(pb.part(LESSON, "c")),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
