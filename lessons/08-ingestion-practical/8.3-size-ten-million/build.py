"""Build lesson 8.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Size RAG for ten million documents. Every number on the page is one of three kinds, and the build computes each:
the kit's constants (parsed from its code and Terraform), the kit's corpus as the kit's own loader, chunker and
batcher count it (shared/documind_corpus.py, run here), and the prices and limits Google publishes, which the kit does
not hold (lessons/08-ingestion-practical/rag_scale.py keeps them, dated and linked, with the calculator that 8.4 reuses).
Step 5's cell is run here, offline, on the kit, and its output is the page's expected output; the calculator in step 1
is rag_scale.scale() in JavaScript, and node runs it against the Python on a grid of inputs before the page is written.
Live: what the lane prints (make sources, make vector-status, the index's REST read, Firestore's counts, the ingest's
request latencies) is pb.recorded() from the author's run; RUN_LIST.md says which command records which file.

    python pagekit/build.py 8.3
"""
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

sys.path.insert(0, str(HERE.parent))
import rag_scale as rs  # noqa: E402

LESSON = "8.3"
title = ("<title>Lesson 8.3 Size RAG for ten million documents - the kit's constants and its own corpus, scaled until "
         "something breaks | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
N = 10_000_000                                                       # the lesson's target, and the calculator's default

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the calculator: four inputs, one row per line of the bill or the limit it meets */
.sz-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:8px 14px;margin:0 0 6px;}
.sz-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.sz-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.sz-in input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.sz-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin:6px 0 8px;overflow-wrap:anywhere;}
.sz-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;padding:8px 10px;border:1px solid var(--border);border-left-width:4px;border-left-color:#0891b2;border-radius:10px;background:var(--card);margin:0 0 6px;font-size:12.5px;line-height:1.5;color:var(--slate);}
.sz-row b{color:var(--navy);}
.sz-row .v{font-family:var(--mono);color:var(--navy);text-align:right;white-space:nowrap;}
.sz-row .why{grid-column:1 / -1;overflow-wrap:anywhere;}
.sz-row.money{border-left-color:var(--teal);}
.sz-row.limit{border-left-color:#c2410c;background:#fff7ed;}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's pin words
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which "
         "store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back "
         "at the end if you want the UI's answers to come from the kit's index while you read."),
        ("Leave it until the lesson's last step is done.", "If you ran it, leave it until the lesson's last step is done.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)
assert "step 3 makes the difference visible." in setup          # this page's step 3: the UI as you, the shell as the operator

# ------------------------------------------------------------------ verbatim kit excerpts
MAIN, IX, DC, V = "services/ingest/main.py", "services/ingest/indexer.py", "shared/documind_corpus.py", "terraform/vector.tf"
EV, FP, RC, RT = "terraform/eventarc.tf", "services/ingest/idempotency.py", "services/ingest/reconcile.py", "terraform/reconcile.tf"
FSI, L125 = "terraform/firestore_indexes.tf", "commands/lesson-12.5.sh"
EXCERPTS = {
    "chunk_consts": ("services/ingest/main.py - the chunk: 2,000 characters, 200 of overlap",
                     block(MAIN, "# 4.1's chunker, the shape every lesson's corpus has", n=3)),
    "windows": ("services/ingest/main.py - _windows(): cut on a sentence when one is near", block(MAIN, "def _windows(")),
    "embed_consts": ("services/ingest/indexer.py - one request's ceilings, the vector's length, the region",
                     block(IX, "EMBED_BATCH = 250", end="def batches(")),
    "embed_all": ("services/ingest/indexer.py - embed_all(): the requests go one after another", block(IX, "def embed_all(")),
    "embed_doc": ("shared/documind_corpus.py - embed_batches(): why 250 and 15,000", block(DC, "def embed_batches(", n=6)),
    "vector_config": ("terraform/vector.tf - the index: 768 numbers a vector, streamed",
                      block(V, "    config {", end="  # STREAM_UPDATE, not BATCH_UPDATE.") + "\n...\n"
                      + block(V, '  index_update_method = "STREAM_UPDATE"', n=1)),
    "vector_machine": ("terraform/vector.tf - the machine each shard size names", block(V, "  vector_machine_by_shard = {", n=5)),
    "vector_deployed": ("terraform/vector.tf - the deployed index: one replica, never more",
                        block(V, "  # One compatible replica.", end="# These two outputs are the whole contract")),
    "row": ("services/ingest/indexer.py - mirror_to_firestore(): the row every chunk gets", block(IX, "        row = {", n=19)),
    "fs_filters": ("terraform/firestore_indexes.tf - six of the eight vector indexes on chunks",
                   block(FSI, "  chunks_filter_indexes = {", n=8) + "\n...\n"
                   + block(FSI, 'resource "google_firestore_index" "chunks_filter_vector" {', end="# FirestoreGraph.expand()")),
    "deploy_comment": ("commands/lesson-12.5.sh - the worker: one document an instance, thirty instances",
                       block(L125, "# The ingest worker. Reached by nothing but the push subscription", n=6) + "\n...\n"
                       + block(L125, "  --memory=2Gi --cpu=2 --concurrency=1 --timeout=600 \\", n=2)),
    "docai_pace": ("services/ingest/main.py - Document AI's pace, and the largest PDF the push lane takes",
                   block(MAIN, "# parser.py sends a PDF to Document AI in 15-page slices", n=6)),
    "dlq": ("terraform/eventarc.tf - twelve deliveries, then the dead-letter topic",
            block(EV, "  # At-least-once, with a ceiling:", end="  depends_on")),
    "ingest_ok": ("services/ingest/main.py - after every ingest: the ledger row, then the fingerprint",
                  block(MAIN, "        finish(_db, doc.doc_key, len(chunks), counts, msg.generation)", end='        if gone["retired_chunks"]:')),
    "fingerprint": ("services/ingest/idempotency.py - corpus_fingerprint(): every indexed source of the tenant",
                    block(FP, "def corpus_fingerprint(", end="def refresh_fingerprint(")),
    "walk_tf": ("terraform/reconcile.tf - the nightly job: one task, no retry, 1,200 seconds",
                block(RT, 'resource "google_cloud_run_v2_job" "reconcile" {', n=11)),
    "walk_py": ("services/ingest/reconcile.py - the walk loads three lists before it plans",
                block(RC, '    prefix = f"{a.tenant}/" if a.tenant else None', n=7)),
    "walk_switch": ("terraform/reconcile.tf - off unless the lane turns it on", block(RT, 'variable "reconcile_job" {', n=5)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["chunk_consts"].endswith("CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200")
assert E["windows"].rstrip().endswith("return out") and "start = max(end - CHUNK_OVERLAP, start + 1)" in E["windows"]
assert "EMBEDDING_DIMENSIONS = 768" in E["embed_consts"] and E["embed_consts"].rstrip().endswith(")")
assert 'location="us-central1",' in E["embed_consts"]
assert "    for batch in batches(texts):" in E["embed_all"] and E["embed_all"].rstrip().endswith("return out")
assert "250 texts per request and 20,000 tokens across them" in " ".join(E["embed_doc"].split())
assert "dimensions                  = 768" in E["vector_config"] and E["vector_config"].endswith('index_update_method = "STREAM_UPDATE"')
assert E["vector_machine"].count("SHARD_SIZE_") == 3
assert E["vector_deployed"].rstrip().endswith("}") and "    min_replica_count = 1\n    max_replica_count = 1" in E["vector_deployed"]
assert E["row"].startswith("        row = {") and E["row"].endswith("        }") and '"embedding": Vector(vector),' in E["row"]
assert E["fs_filters"].count("field_path") == 3 and 'field_path = "__name__"' in E["fs_filters"]
assert "Thirty instances, so a corpus" in E["deploy_comment"] and "--min-instances=0 --max-instances=30 \\" in E["deploy_comment"]
assert E["docai_pace"].endswith(f"MAX_INLINE_PAGES = {rs.MAX_INLINE_PAGES}")
assert "max_delivery_attempts = 12" in E["dlq"] and E["dlq"].rstrip().endswith("ack_deadline_seconds = 600")
assert E["ingest_ok"].rstrip().endswith('fingerprint = refresh_fingerprint(_db, doc.tenant_id, "ingest_ok")')
assert '.where("status", "==", "indexed").stream())' in E["fingerprint"]
assert '      timeout         = "1200s"' in E["walk_tf"] and "    task_count = 1" in E["walk_tf"]
assert E["walk_py"].rstrip().endswith("actions = plan(objects, ledger, documents)")
assert E["walk_switch"].endswith("}") and "  default     = false\n" in E["walk_switch"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the prose states, beyond rag_scale's
flat = lambda s: re.sub(r"\s+", " ", s)                             # noqa: E731
MK = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert "\nsources: guard-project\n" in MK and "\nvector-status: guard-project\n" in MK
assert "--report $(if $(TENANT_ONLY),--tenant $(TENANT_ONLY),)" in MK
VS_SH = (KIT / "commands/vector-status.sh").read_text(encoding="utf-8")
assert "--format='yaml(displayName,indexStats.vectorsCount,indexStats.shardsCount,indexUpdateMethod)'" in VS_SH
UPLOAD = (KIT / "evals/upload.sh").read_text(encoding="utf-8")
assert "a .md whose .pdf twin exists stays home." in UPLOAD
assert "ingest-corpus: guard-project\n\tPROJECT_ID=$(PROJECT) bash evals/upload.sh" in MK
DOCS_UI = (KIT / "services/frontend/documents.py").read_text(encoding="utf-8")
assert 'st.subheader("Versions")' in DOCS_UI and '"chunks": r_["chunks"]' in DOCS_UI and "corpus fingerprint" in DOCS_UI
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))                # noqa: E731  comments read as one sentence
assert "The DEPLOYED index is the third, and it is the one that costs money per hour" in flatc((KIT / V).read_text(encoding="utf-8"))
RC_SRC = (KIT / RC).read_text(encoding="utf-8")
assert "The walk ends with one number, drift" in flatc(RC_SRC)
# the sparse half and the restricts ride with every datapoint, beside the dense vector Google's data size counts
assert "sparse_embedding=_sparse(text)," in (KIT / IX).read_text(encoding="utf-8") and "restricts=_restricts(tenant_id, kind, doc_type)," in (KIT / IX).read_text(encoding="utf-8")
assert (KIT / "shared/prices.py").read_text(encoding="utf-8").count(f"USD_INR = {rs.USD_INR} ") == 1
FS_TF = (KIT / "terraform/firestore.tf").read_text(encoding="utf-8")
assert "POINT_IN_TIME_RECOVERY_ENABLED" in FS_TF                   # PITR bills its own storage: named, not priced
LANE_SHARD_WORDS = ("vector.tf names no shard size, so the API chose your index's when <code>make up</code> created it"
                    if rs.DECLARED_SHARD is None else
                    f"vector.tf creates a new index {rs.SHORT[rs.DECLARED_SHARD]} and leaves an existing one the size it has")
IN_KIT_WORDS = ("None of the four is in the kit today." if rs.DECLARED_SHARD is None else
                "Three of the four are not in the kit today, and the fourth is there only in part.")

# ------------------------------------------------------------------ step 5: the kit's chunker on the kit's corpus, run here
MEASURE_PY = f'''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import documind_corpus as dc     # the loader, the chunker and the batcher: the worker's rules (step 4)
from shared.prices import USD_INR             # the course's rate, Rs {rs.USD_INR} to the dollar
N, DIMS, GIB = {N:_}, {rs.DIMS}, 1 << 30     # the target; indexer.py's EMBEDDING_DIMENSIONS; a gibibyte
USD_PER_1K = {rs.EMBED_USD_1K["online"]:.6f}                 # text-embedding-005 input, online, per 1,000 characters (step 8)
rows = []
for tenant in ("acme", "globex", "zeta"):
    for d in dc.load_documents(tenant, "evals", "{PROJ}"):
        texts = [c["text"] for c in dc.chunk_document(d, tenant)]
        rows.append((d["doc_type"], len(d["text"]), len(texts), sum(map(len, texts)), len(dc.embed_batches(texts))))


def line(name, group):
    print(f"{{name:10}} {{len(group):>4}} {{sum(r[1] for r in group):>10,}} {{sum(r[2] for r in group):>6,}} "
          f"{{sum(r[3] for r in group):>10,}} {{sum(r[4] for r in group):>8,}}")


print(f"{{'doc_type':10}} {{'docs':>4}} {{'characters':>10}} {{'chunks':>6}} {{'sent':>10}} {{'requests':>8}}")
for t in sorted({{r[0] for r in rows}}):
    line(t, [r for r in rows if r[0] == t])
line("all", rows)
docs, chunks, sent, requests = len(rows), *(sum(r[i] for r in rows) for i in (2, 3, 4))
k = N / docs
print(f"\\nper document: {{chunks / docs:.2f}} chunks, {{sent / docs:,.0f}} characters sent, {{requests / docs:.2f}} requests")
print(f"at {{N:,}} documents of this mix:")
print(f"  vectors              {{chunks * k:,.0f}}")
print(f"  embedding requests   {{requests * k:,.0f}}")
print(f"  dense index          {{chunks * k * DIMS * 4 / GIB:,.1f}} GiB ({{DIMS}} numbers x 4 bytes a vector)")
print(f"  embedding, once      Rs {{sent * k / 1000 * USD_PER_1K * USD_INR / 1e5:,.2f}} lakh")'''
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}        # no gcloud on PATH, no Google credentials in the environment
r = subprocess.run([sys.executable, "-"], input=MEASURE_PY, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-800:], r.stderr[-2000:])
MEASURE_OUT = r.stdout.rstrip("\n")
C = rs.SHAPES["corpus"]
TEN = rs.scale(N, C)
# the cell's numbers are rag_scale's: the same loader, the same chunker, the same batcher, the same arithmetic
_tail = MEASURE_OUT.split("\nall ", 1)[1].split()
assert [int(x.replace(",", "")) for x in _tail[:5]] == [C["docs"], C["total_chars"], C["total_chunks"], C["total_sent"], C["total_requests"]], _tail
assert f"  vectors              {TEN['chunks']:,.0f}" in MEASURE_OUT and f"  dense index          {TEN['dense_gib']:,.1f} GiB" in MEASURE_OUT
assert f"  embedding requests   {TEN['requests']:,.0f}" in MEASURE_OUT
assert f"Rs {rs.inr(TEN['embed_usd']['online']) / 1e5:,.2f} lakh" in MEASURE_OUT
TYPES = {line.split()[0]: [int(x.replace(",", "")) for x in line.split()[1:]] for line in MEASURE_OUT.splitlines()[1:]
         if line and line.split()[0] in {d["doc_type"] for d in rs.DOCS}}
assert sum(v[0] for v in TYPES.values()) == C["docs"] and set(TYPES) == set(C["types"])

# ------------------------------------------------------------------ number words, as the prose and the widget print them
r0, inr, group, rupees = rs.r0, rs.inr, rs.group, rs.rupees


def n0(x: float) -> str:
    """A count, grouped the international way: 1,021,111,111."""
    return f"{r0(x):,}"


def fx(x: float, d: int) -> str:
    """A decimal, rounded half up as the widget's Math.round rounds, then grouped: 2,921.4."""
    return f"{r0(x * 10 ** d) / 10 ** d:,.{d}f}"


def days(x: float) -> str:
    return fx(x, 1) + (" day" if fx(x, 1) == "1.0" else " days")


def usd(x: float) -> str:
    """A small price as written, never in exponent form: 0.000025."""
    return f"{x:.6f}".rstrip("0").rstrip(".")


def dur(sec: float) -> str:
    """A time in the unit that reads best: 19.8 ms, 33.3 s, 21.6 min, 9.3 hours, 150.3 days."""
    if sec < 1:
        return fx(sec * 1_000, 1) + " ms"
    if sec < 60:
        return fx(sec, 1) + " s"
    if sec < 3_600:
        return fx(sec / 60, 1) + " min"
    if sec < 172_800:
        return fx(sec / 3_600, 1) + (" hour" if fx(sec / 3_600, 1) == "1.0" else " hours")
    return days(sec / 86_400)


SHAPE_KEYS = list(rs.SHAPES)
SIZES = list(rs.SHARD_GIB)
STOPS = [27, 100, 300, 1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000, 3_000_000, 10_000_000, 30_000_000, 100_000_000]
TENANTS = [1, 10, 100, 1_000]
assert STOPS[0] == C["docs"] and N in STOPS


def view(docs: int, shape: str, tenants: int, size: str) -> dict:
    """What the calculator prints for one setting: every figure as text. node must print the same."""
    s = rs.SHAPES[shape]
    o = rs.scale(docs, s, tenants)
    per = docs / tenants
    cross = rs.crossover(s)
    backlog_s = docs * s["pdf_pages"] * rs.DOCAI_S_PER_PAGE / rs.IN_FLIGHT
    return {
        "chunks": n0(o["chunks"]), "per_doc": fx(s["chunks"], 2), "requests": n0(o["requests"]), "sent": n0(o["sent"]),
        "embed_online": rupees(inr(o["embed_usd"]["online"])), "embed_batch": rupees(inr(o["embed_usd"]["batch"])),
        "gib": fx(o["dense_gib"], 1), "shards": n0(o["shards"][size]), "serve": rupees(inr(o["serve_usd_month"][size])),
        "stream": rupees(inr(o["stream_usd"])), "compact": rupees(inr(o["compact_usd"])),
        "fs_gib": fx(o["fs_gib"], 1), "fs_month": rupees(inr(o["fs_usd_month"])), "fs_ingest": rupees(inr(o["fs_ingest_usd"])),
        "ingest_time": dur(o["ingest_days_per_s"] * 86_400),
        "docai_time": dur(o["docai_days"] * 86_400) if s["pdf_pages"] else "",
        "budget": dur(rs.DLQ_BOUND_S * rs.IN_FLIGHT / docs),
        "backlog_h": fx(backlog_s / 3600, 1), "dlq": "yes" if backlog_s > rs.DLQ_BOUND_S else "no",
        "fp_reads": n0(o["fp_reads"]), "fp_rs": rupees(inr(o["fp_usd"])), "fp_rate": n0(o["fp_last_rate"]),
        "fp_over": "yes" if per > cross else "no", "per_tenant": n0(per),
        "walk_items": n0(o["walk_items"]), "walk_rate": n0(o["walk_rate"]), "walk_rs": rupees(inr(o["walk_usd"])),
    }


# ------------------------------------------------------------------ the calculator's data and script (step 1)
assert rs.DLQ_BOUND_S % 60 == 0                        # the widget prints the backoff span in whole minutes
W = {"stops": STOPS, "tenants": TENANTS, "start": STOPS.index(N), "dims": rs.DIMS, "gib": rs.GIB, "inr": rs.USD_INR,
     "embed": rs.EMBED_USD_1K, "build": rs.VS_BUILD_USD_GIB, "stream": rs.VS_STREAM_USD_GIB, "monthH": rs.MONTH_H,
     "replicas": rs.REPLICAS, "shardGib": rs.SHARD_GIB, "node": rs.VS_NODE_USD, "short": rs.SHORT, "machine": rs.MACHINE,
     "fs": rs.FS_USD, "writes": rs.WRITES_PER_CHUNK, "reads": rs.READS_PER_CHUNK, "inFlight": rs.IN_FLIGHT,
     "walkLists": rs.WALK_LISTS, "walkS": rs.WALK_SECONDS, "timeout": rs.WORKER_TIMEOUT, "docai": rs.DOCAI_S_PER_PAGE,
     "dlq": rs.DLQ_BOUND_S, "dlqMin": rs.DLQ_BOUND_S // 60, "attempts": rs.MAX_ATTEMPTS,
     "shapes": {k: {key: s[key] for key in ("label", "docs", "chunks", "sent", "requests", "fs_chunk", "pdf_pages")}
                for k, s in rs.SHAPES.items()}}
CALC_JS = r"""var D = __DATA__;
function r0(x){ return Math.floor(x + 0.5); }
function grp(s){ var out = ''; while (s.length > 3){ out = ',' + s.slice(-3) + out; s = s.slice(0, -3); } return s + out; }
function grpIN(s){ if (s.length <= 3) return s; var head = s.slice(0, -3), tail = s.slice(-3), parts = [];
  while (head.length > 2){ parts.unshift(head.slice(-2)); head = head.slice(0, -2); } if (head) parts.unshift(head); return parts.join(',') + ',' + tail; }
function n0(x){ return grp(String(r0(x))); }
function fx(x, d){ var m = Math.pow(10, d), s = (r0(x * m) / m).toFixed(d), i = s.indexOf('.'); return grp(i < 0 ? s : s.slice(0, i)) + (i < 0 ? '' : s.slice(i)); }
function rupees(x){ if (x >= 1e7) return 'Rs ' + fx(r0(x / 1e5) / 100, 2) + ' crore'; if (x >= 1e5) return 'Rs ' + fx(r0(x / 1e3) / 100, 2) + ' lakh';
  return 'Rs ' + grpIN(String(r0(x))); }
function days(x){ var t = fx(x, 1); return t + (t === '1.0' ? ' day' : ' days'); }
function dur(x){ if (x < 1) return fx(x * 1000, 1) + ' ms'; if (x < 60) return fx(x, 1) + ' s'; if (x < 3600) return fx(x / 60, 1) + ' min';
  if (x < 172800){ var t = fx(x / 3600, 1); return t + (t === '1.0' ? ' hour' : ' hours'); } return days(x / 86400); }
function inr(usd){ return usd * D.inr; }
function scale(docs, s, tenants){
  var chunks = docs * s.chunks, sent = docs * s.sent, dense = chunks * D.dims * 4 / D.gib, per = docs / tenants,
      fp = tenants * per * (per + 1) / 2, o = {chunks: chunks, sent: sent, requests: docs * s.requests,
      embed: {online: sent / 1000 * D.embed.online, batch: sent / 1000 * D.embed.batch}, dense: dense,
      stream: dense * D.stream, compact: dense * D.build, shards: {}, serve: {},
      fsGib: chunks * s.fs_chunk / D.gib, fsIngest: chunks * (D.writes * D.fs.write + D.reads * D.fs.read),
      fpReads: fp, fpUsd: fp * D.fs.read, fpRate: per / D.timeout,
      walkItems: D.walkLists * docs, walkRate: D.walkLists * docs / D.walkS, walkUsd: 2 * docs * D.fs.read,
      ingestDays: docs / D.inFlight / 86400, docaiDays: docs * s.pdf_pages * D.docai / D.inFlight / 86400};
  o.fsMonth = o.fsGib * D.fs.gib_month;
  Object.keys(D.shardGib).forEach(function(size){
    var n = Math.max(1, Math.ceil(dense / D.shardGib[size]));
    o.shards[size] = n; o.serve[size] = D.replicas * n * D.node[size] * D.monthH; });
  return o;
}
function crossover(s){ return Math.ceil(s.sent / 1000 * D.embed.online / D.fs.read); }
function view(docs, key, tenants, size){
  var s = D.shapes[key], o = scale(docs, s, tenants), per = docs / tenants, cross = crossover(s),
      backlog = docs * s.pdf_pages * D.docai / D.inFlight;
  return {chunks: n0(o.chunks), per_doc: fx(s.chunks, 2), requests: n0(o.requests), sent: n0(o.sent),
    embed_online: rupees(inr(o.embed.online)), embed_batch: rupees(inr(o.embed.batch)),
    gib: fx(o.dense, 1), shards: n0(o.shards[size]), serve: rupees(inr(o.serve[size])),
    stream: rupees(inr(o.stream)), compact: rupees(inr(o.compact)),
    fs_gib: fx(o.fsGib, 1), fs_month: rupees(inr(o.fsMonth)), fs_ingest: rupees(inr(o.fsIngest)),
    ingest_time: dur(o.ingestDays * 86400), docai_time: s.pdf_pages ? dur(o.docaiDays * 86400) : '',
    budget: dur(D.dlq * D.inFlight / docs),
    backlog_h: fx(backlog / 3600, 1), dlq: backlog > D.dlq ? 'yes' : 'no',
    fp_reads: n0(o.fpReads), fp_rs: rupees(inr(o.fpUsd)), fp_rate: n0(o.fpRate),
    fp_over: per > cross ? 'yes' : 'no', per_tenant: n0(per),
    walk_items: n0(o.walkItems), walk_rate: n0(o.walkRate), walk_rs: rupees(inr(o.walkUsd))};
}
window.__sz = {view: view};
var root = document.getElementById('sz'); if (!root) { return; }
var nIn = document.getElementById('sz-n'), nV = document.getElementById('sz-n-v'), shape = document.getElementById('sz-shape'),
    ten = document.getElementById('sz-tenants'), shard = document.getElementById('sz-shard'), sum = document.getElementById('sz-sum'),
    out = document.getElementById('sz-rows');
function row(cls, name, value, why){
  var d = document.createElement('div'); d.className = 'sz-row ' + cls;
  var b = document.createElement('b'); b.textContent = name; d.appendChild(b);
  var v = document.createElement('span'); v.className = 'v'; v.textContent = value; d.appendChild(v);
  var w = document.createElement('span'); w.className = 'why'; w.textContent = why; d.appendChild(w);
  out.appendChild(d);
}
function render(){
  var docs = D.stops[parseInt(nIn.value, 10)], key = shape.value, tenants = parseInt(ten.value, 10), size = shard.value,
      v = view(docs, key, tenants, size), short = D.short[size];
  nV.textContent = n0(docs);
  out.textContent = '';
  row('', 'Vectors', v.chunks, v.per_doc + ' chunks a document, the average of ' + D.shapes[key].docs + ' kit documents of this kind, by the kit\'s own chunker');
  row('money', 'Embedding, once', v.embed_online, v.requests + ' requests carrying ' + v.sent + ' characters, sent online by the worker; as a batch job at the batch price: ' + v.embed_batch);
  row('money', 'Vector Search, serving', v.serve + ' a month', v.gib + ' GiB of dense vectors in ' + v.shards + ' ' + short + ' shard(s) of ' + D.shardGib[size] + ' GiB, one ' + D.machine[size] + ' node each, ' + D.replicas + ' replica');
  row('money', 'Vector Search, upkeep', v.compact + ' a compaction', 'streaming the vectors in costs ' + v.stream + ' once; each compaction rebuilds the whole index at the batch-update price, at least every five days while updates keep arriving');
  row('money', 'Firestore, stored', v.fs_month + ' a month', 'at least ' + v.fs_gib + ' GiB: every chunk row and its eight vector-index entries; writing them costs ' + v.fs_ingest + ' once');
  row(v.dlq === 'yes' ? 'limit' : '', 'Ingest at 1 s a document', v.ingest_time,
      D.inFlight + ' documents in flight, one per worker instance; scale this by your median from step 7. ' +
      (v.docai_time ? 'Document AI alone, at the kit\'s "roughly a second a page", keeps the last document waiting ' + v.docai_time + '. '
                    : 'These go up as text, so Document AI adds nothing. ') +
      'A document that waits is refused and retried; ' + D.attempts + ' deliveries span at most ' + D.dlqMin +
      ' minutes of backoff, and the queue clears inside that only while a document takes under ' + v.budget);
  row(v.fp_over === 'yes' ? 'limit' : '', 'Fingerprint, during the load', v.fp_reads + ' reads',
      v.fp_rs + ' with ' + v.per_tenant + ' documents a tenant; the last ingest streams ' + v.per_tenant + ' rows inside its ' + D.timeout + '-second request, ' + v.fp_rate + ' a second' +
      (v.fp_over === 'yes' ? '. Past ' + n0(crossover(D.shapes[key])) + ' a tenant, one more document costs more to fingerprint than to embed' : ''));
  row('', 'Nightly walk', v.walk_rate + ' a second', v.walk_items + ' objects and rows to list in one task of ' + n0(D.walkS) + ' seconds; its Firestore reads: ' + v.walk_rs + ' a night');
  sum.textContent = n0(docs) + ' documents, ' + D.shapes[key].label + ': ' + v.chunks + ' vectors, ' + v.gib + ' GiB, ' + v.serve + ' a month on ' + short + ' shards, ' + v.embed_online + ' to embed';
}
[nIn, shape, ten, shard].forEach(function(el){ el.addEventListener('input', render); el.addEventListener('change', render); });
render();"""
CALC_JS = CALC_JS.replace("__DATA__", json.dumps(W, separators=(",", ":")))
JS = "<script>\n(function(){\n'use strict';\n" + CALC_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# node runs the calculator on a grid of settings; every figure must be the Python's, character for character
GRID = [(d, k, t, z) for d in (27, 1_000, 9_999, 100_000, N, 100_000_000) for k in SHAPE_KEYS for t in (1, 1_000) for z in SIZES]
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "(new Function('window', 'document', " + json.dumps(CALC_JS) + "))(window, document);\n"
        "var G = " + json.dumps(GRID) + ";\n"
        "process.stdout.write(JSON.stringify(G.map(function(g){ return window.__sz.view(g[0], g[1], g[2], g[3]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for g, got in zip(GRID, json.loads(node.stdout)):
    assert got == view(*g), (g, got, view(*g))
N_GRID = len(GRID)

# the panel's options: its select values are the module's keys, its defaults the prose's
SHAPE_NAME = {"corpus": "The kit's corpus, as mixed", "statute": "Acts and Codes", "handbook": "Handbooks and policies",
              "short": "Short documents"}
assert set(SHAPE_NAME) == set(rs.SHAPES)
OPT_SHAPE = "".join(f'<option value="{k}"' + (" selected" if k == "corpus" else "") + f'>{html.escape(SHAPE_NAME[k])} ({s["docs"]})</option>'
                    for k, s in rs.SHAPES.items())
OPT_TENANTS = "".join(f'<option value="{t}"' + (" selected" if t == 1 else "") + f">{t:,}</option>" for t in TENANTS)
OPT_SHARD = "".join(f'<option value="{z}"' + (" selected" if z == "SHARD_SIZE_MEDIUM" else "") + f'>{rs.SHORT[z]}: {rs.SHARD_GIB[z]} GiB</option>'
                    for z in SIZES)
V10 = view(N, "corpus", 1, "SHARD_SIZE_MEDIUM")

# ------------------------------------------------------------------ the tables
SMALL, MEDIUM, LARGE = SIZES


def tw(head: list, rows: list) -> str:
    """A comparison table: the first cell bare, every other cell labelled for the phone layout."""
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">',
           "<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>", "<tbody>"]
    for cells in rows:
        out.append("<tr><td>" + cells[0] + "</td>" + "".join(f'<td data-label="{html.escape(re.sub("<[^>]+>", "", h))}">{c}</td>'
                                                            for h, c in zip(head[1:], cells[1:])) + "</tr>")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')
    return "\n".join(out)


# step 3: acme's text documents as the kit's chunker counts them, beside how the lane received each
ACME = [d for d in rs.DOCS if d["tenant"] == "acme"]
ACME_TABLE = tw(["Document", "Type", "Uploaded as", "Characters", "Chunks offline", "Requests"],
                [[f"<code>{d['slug']}</code>", d["doc_type"],
                  f"PDF, {d['pdf_pages']} pages: Document AI's text" if d["pdf_pages"] else ".md: the same text, the same count",
                  f"{d['chars']:,}", f"{d['chunks']:,}", str(d["requests"])] for d in ACME])
N_ACME, N_ACME_MD = len(ACME), sum(1 for d in ACME if not d["pdf_pages"])
# step 4's example of the heading rule: acme's contract, under one window long, one chunk per section and one above them
MSA = next(d for d in ACME if d["slug"] == "msa_acme_2026")
MSA_HEADS = len(re.findall(r"^## ", (KIT / "evals/corpus/acme/msa_acme_2026.md").read_text(encoding="utf-8"), re.M))
assert MSA["chars"] < rs.CHUNK_CHARS and MSA["chunks"] == MSA_HEADS + 1 and not MSA["pdf_pages"]

# step 8: the index at ten million, by shard size
SHARD_TABLE = tw(["Shard size", "A shard holds", "Machine (Mumbai, an hour)", "Shards at ten million", "Serving a month"],
                 [[f"<strong>{rs.SHORT[z]}</strong>", f"{rs.SHARD_GIB[z]} GiB", f"{rs.MACHINE[z]}, ${rs.VS_NODE_USD[z]}",
                   n0(TEN["shards"][z]), rupees(inr(TEN["serve_usd_month"][z]))] for z in SIZES])
SHARD_DOCS = {z: rs.shard_docs(C, z) for z in SIZES}

# step 8: everything else at ten million documents of the corpus's mix
COST_ROWS = [
    ["Embedding, online", f"{n0(TEN['sent'])} characters at ${usd(rs.EMBED_USD_1K['online'])} per 1,000", "once", rupees(inr(TEN["embed_usd"]["online"]))],
    ["Embedding, as a batch job", f"the same characters at ${usd(rs.EMBED_USD_1K['batch'])} per 1,000", "once", rupees(inr(TEN["embed_usd"]["batch"]))],
    ["Streaming the vectors in", f"{fx(TEN['dense_gib'], 1)} GiB at ${rs.VS_STREAM_USD_GIB:.2f} a GiB", "once", rupees(inr(TEN["stream_usd"]))],
    ["A compaction", f"the whole index rebuilt at ${rs.VS_BUILD_USD_GIB:.2f} a GiB", f"at least every {rs.COMPACT_DAYS} days while updates arrive",
     rupees(inr(TEN["compact_usd"]))],
    ["Firestore, stored", f"at least {fx(TEN['fs_gib'], 1)} GiB at ${rs.FS_USD['gib_month']} a GiB", "a month", rupees(inr(TEN["fs_usd_month"]))],
    ["Firestore, written", f"{rs.WRITES_PER_CHUNK} writes and {rs.READS_PER_CHUNK} read a chunk", "once", rupees(inr(TEN["fs_ingest_usd"]))],
    ["The fingerprint, one tenant", f"{n0(TEN['fp_reads'])} reads", "once, during the load", rupees(inr(TEN["fp_usd"]))],
    ["The nightly walk's reads", f"{n0(2 * N)} rows", "a night", rupees(inr(TEN["walk_usd"]))],
]
COST_TABLE = tw(["Line", "How it is counted", "When", "Rupees"], [[f"<strong>{a}</strong>", b, c, d] for a, b, c, d in COST_ROWS])
COMPACT_MONTH = rupees(inr(TEN["compact_usd"] * rs.COMPACTIONS_30D))
CHEAPEST = min(SIZES, key=lambda z: TEN["serve_usd_month"][z])
assert CHEAPEST == LARGE and TEN["serve_usd_month"][SMALL] > TEN["serve_usd_month"][MEDIUM] > TEN["serve_usd_month"][LARGE]

# step 8: what the kit would change
CHANGE_TABLE = tw(["What breaks", "Where the kit sets it", "What would change it", "In the kit"], [
    ["<strong>The fingerprint</strong>", "<code>idempotency.py</code>: <code>corpus_fingerprint()</code> streams every indexed source, on every ingest",
     "An incremental fingerprint: each ingest folds its own doc_key into a running value on the ledger row, in the same write that records it, so an ingest reads one row, not all of them",
     "Not built"],
    ["<strong>The nightly walk</strong>", f"<code>reconcile.tf</code>: one task, {rs.WALK_SECONDS:,} seconds, no retry; <code>reconcile.py</code> loads all three lists first",
     "A sharded walk: many tasks, each taking its own slice of the tenants or the object names, each comparing as it streams rather than after loading everything",
     "Not built"],
    [f"<strong>{rs.IN_FLIGHT} in flight</strong>", f"<code>lesson-12.5.sh</code>: <code>--concurrency={rs.WORKER_CONCURRENCY}</code>, <code>--max-instances={rs.WORKER_INSTANCES}</code>; "
     f"<code>eventarc.tf</code>: {rs.MAX_ATTEMPTS} deliveries",
     "Batch embeddings for a backfill: the load goes to a batch job at the batch price, and the one-document worker keeps the daily trickle it was built for",
     "Not built"],
    ["<strong>One replica</strong>", "<code>vector.tf</code>: <code>min_replica_count = 1</code>, <code>max_replica_count = 1</code>",
     "An explicit shard size chosen from the data size, and replicas that scale with the queries, two at least so one node's restart is not an outage",
     "Not built" if rs.DECLARED_SHARD is None else "The shard size is declared; the replicas are not"],
])

# ------------------------------------------------------------------ the cells: what you run, and what the lane prints
INDEX_PY = f'''import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
base = f"https://{{R}}-aiplatform.googleapis.com/v1/projects/{{P}}/locations/{{R}}"
get = lambda path: json.load(urllib.request.urlopen(urllib.request.Request(f"{{base}}/{{path}}", headers={{"Authorization": f"Bearer {{tok}}"}}), timeout=60))
GIB, SHARD_GIB = 1 << 30, {json.dumps(rs.SHARD_GIB)}   # Google's shard sizes (step 8)
for ix in get("indexes").get("indexes", []):
    cfg, st = ix["metadata"]["config"], ix.get("indexStats", {{}})
    n, dims, shard = int(st.get("vectorsCount", 0)), int(cfg["dimensions"]), cfg.get("shardSize", "not stated")
    print(f"index {{ix['displayName']}}: {{n:,}} vectors of {{dims}}, {{st.get('shardsCount', 0)}} shard(s), {{shard}}, {{ix['indexUpdateMethod']}}")
    if shard in SHARD_GIB:
        used = n * dims * 4 / GIB
        print(f"  dense data {{used * 1024:,.1f}} MiB: {{100 * used / SHARD_GIB[shard]:.3f}}% of one {{SHARD_GIB[shard]}} GiB shard; "
              f"the shard holds {{int(SHARD_GIB[shard] * GIB / (dims * 4)):,}} vectors of this length")
for ep in get("indexEndpoints").get("indexEndpoints", []):
    for d in ep.get("deployedIndexes", []):
        res = d.get("dedicatedResources", {{}})
        print(f"deployed {{d['id']}}: {{res.get('machineSpec', {{}}).get('machineType')}}, replicas {{res.get('minReplicaCount')}} to {{res.get('maxReplicaCount')}}")'''
COUNTS_PY = '''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
db = firestore.Client(project=os.environ["PROJECT"])
count = lambda q: int(q.count().get()[0][0].value)          # one aggregation: billed by the index entries it reads, not by rows
eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
print(f"{'tenant':7} {'chunk rows':>10} {'current':>8} {'indexed sources':>15}")
for t in ("acme", "globex", "zeta"):
    rows = eq(db.collection("chunks"), "tenant_id", t)
    print(f"{t:7} {count(rows):>10,} {count(eq(rows, 'current', True)):>8,} "
          f"{count(eq(eq(db.collection('sources'), 'tenant_id', t), 'status', 'indexed')):>15,}")'''
LATENCY_PY = f'''import json, os, statistics, warnings
warnings.filterwarnings("ignore", category=UserWarning)
by = {{}}
for e in json.load(open(os.path.expanduser("~/ingest-requests.json"))):
    h = e.get("httpRequest", {{}})
    by.setdefault(int(h.get("status", 0)), []).append(float(str(h.get("latency", "0s")).rstrip("s") or 0))
for status, secs in sorted(by.items()):
    secs.sort()
    print(f"HTTP {{status}}: {{len(secs):>4}} deliveries, median {{statistics.median(secs):.1f}} s, slowest {{secs[-1]:.1f}} s")
taken = sorted(s for status, secs in by.items() if 200 <= status < 300 for s in secs)
if taken:
    m = statistics.median(taken)
    print(f"at {N:,} documents, {rs.IN_FLIGHT} at a time, {{m:.1f}} s each: {{{N} * m / {rs.IN_FLIGHT} / 86400:,.1f}} days")'''
for body in (MEASURE_PY, INDEX_PY, COUNTS_PY, LATENCY_PY):
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in body and "'''" not in body and "\nPY" not in body
assert f"{rs.IN_FLIGHT} at a time" in LATENCY_PY and rs.IN_FLIGHT == rs.WORKER_INSTANCES * rs.WORKER_CONCURRENCY

LOG_FILTER = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
              'AND httpRequest.requestMethod="POST"')
CELLS = {
    "ui": 'echo "https://documind-ui-$NUMBER.$REGION.run.app"     # open it signed in as yourself, then Documents',
    "sources": 'make sources PROJECT="$PROJECT" TENANT_ONLY=acme',
    "vector": 'make vector-status PROJECT="$PROJECT" REGION="$REGION"',
    "measure": "python - <<'PY'\n" + MEASURE_PY + "\nPY",
    "index": "python - <<'PY'\n" + INDEX_PY + "\nPY",
    "counts": "python - <<'PY'\n" + COUNTS_PY + "\nPY",
    "latency": (f"gcloud logging read '{LOG_FILTER}' \\\n  --project=\"$PROJECT\" --freshness=30d --limit=1000 --format=json > ~/ingest-requests.json\n"
                "python - <<'PY'\n" + LATENCY_PY + "\nPY"),
}
CELL_LABELS = {
    "ui": "run in the operator shell (prints your UI's address)",
    "sources": "run in the operator shell, in the kit (reads the ledger; writes nothing)",
    "vector": "run in the operator shell, in the kit (two gcloud describes; changes nothing)",
    "measure": "run in the operator shell, in the kit (no network: the kit's own code on the kit's own files)",
    "index": "run in the operator shell (two GETs on the Vertex AI API; changes nothing)",
    "counts": "run in the operator shell (nine Firestore count queries; writes nothing)",
    "latency": "run in the operator shell (one Cloud Logging read; writes one file in your home directory)",
}
RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("sources_acme", "vector_status", "index_rest", "firestore_counts", "ingest_latency")}
LANE_LABEL = "(the author's lane: your ids, counts and times are yours)"
OUTS = {
    "ui": ("(the format: NUMBER is your project number)", "https://documind-ui-NUMBER.asia-south1.run.app"),
    "measure": ("(this cell, run on the kit when this page was built: your output is the same, digit for digit)", MEASURE_OUT),
    "sources": (LANE_LABEL, RECORDED["sources_acme"]), "vector": (LANE_LABEL, RECORDED["vector_status"]),
    "index": (LANE_LABEL, RECORDED["index_rest"]), "counts": (LANE_LABEL, RECORDED["firestore_counts"]),
    "latency": (LANE_LABEL, RECORDED["ingest_latency"]),
}


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

# ------------------------------------------------------------------ the numbers the prose states
PAGES = {
    "embed_price": "https://cloud.google.com/vertex-ai/generative-ai/pricing",
    "vs_price": "https://cloud.google.com/vertex-ai/pricing",
    "shards": "https://docs.cloud.google.com/vertex-ai/docs/vector-search/create-manage-index",
    "fs_price": "https://cloud.google.com/firestore/pricing",
    "fs_size": "https://firebase.google.com/docs/firestore/storage-size",
}
RS_SRC = Path(rs.__file__).read_text(encoding="utf-8")
assert all(u in RS_SRC for u in PAGES.values()) and "read on 12 October 2026" in RS_SRC
PRICE_DATE = "12 October 2026"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
         11: "eleven", 12: "twelve", 17: "seventeen", 27: "twenty-seven", 30: "thirty"}
SH = {k: rs.SHAPES[k] for k in SHAPE_KEYS}
FS_IDX = len(rs.CHUNK_VECTOR_INDEXES)
ROW_B = r0(C["fs_row_chunk"])
CHUNK_B = r0(C["fs_chunk"])
STATS = {
    "N": f"{N:,}", "N_DOCS": str(C["docs"]), "N_DOCS_W": WORDS[C["docs"]], "N_CHUNKS": f"{C['total_chunks']:,}",
    "N_CHARS": f"{C['total_chars']:,}", "N_SENT": f"{C['total_sent']:,}", "N_REQ": str(C["total_requests"]),
    "PER_DOC": fx(C["chunks"], 2), "PER_DOC_R": str(r0(C["chunks"])), "SENT_DOC": n0(C["sent"]), "REQ_DOC": fx(C["requests"], 2),
    "CHUNK_CHARS": f"{rs.CHUNK_CHARS:,}", "OVERLAP": str(rs.CHUNK_OVERLAP), "EMBED_BATCH": str(rs.EMBED_BATCH),
    "EMBED_TOKENS": f"{rs.EMBED_TOKENS:,}", "CPT": str(rs.CHARS_PER_TOKEN), "MODEL_TOKENS": f"{rs.MODEL_TOKENS:,}",
    "MODEL_TEXTS": str(rs.MODEL_TEXTS), "DIMS": str(rs.DIMS), "VEC_BYTES": f"{rs.DIMS * 4:,}", "EMBED_MODEL": rs.EMBED_MODEL,
    "EMBED_LOCATION": rs.EMBED_LOCATION, "REPLICAS": str(rs.REPLICAS), "IN_FLIGHT": str(rs.IN_FLIGHT),
    "IN_FLIGHT_W": WORDS[rs.IN_FLIGHT], "TIMEOUT": str(rs.WORKER_TIMEOUT), "WALK_S": f"{rs.WALK_SECONDS:,}",
    "ATTEMPTS": str(rs.MAX_ATTEMPTS), "ATTEMPTS_W": WORDS[rs.MAX_ATTEMPTS], "WAITS_W": WORDS[rs.MAX_ATTEMPTS - 1],
    "MAX_BACKOFF": str(rs.MAX_BACKOFF), "MIN_BACKOFF": str(rs.MIN_BACKOFF), "DLQ_S": f"{rs.DLQ_BOUND_S:,}",
    "DLQ_MIN": n0(rs.DLQ_BOUND_S / 60), "MAX_PAGES": str(rs.MAX_INLINE_PAGES),
    # ten million, the corpus's mix
    "T_CHUNKS": n0(TEN["chunks"]), "T_CHUNKS_B": fx(TEN["chunks"] / 1e9, 2), "T_REQ": n0(TEN["requests"]),
    "T_SENT": n0(TEN["sent"]), "T_GIB": fx(TEN["dense_gib"], 1), "T_TIB": fx(TEN["dense_gib"] / 1024, 2),
    "T_EMBED": rupees(inr(TEN["embed_usd"]["online"])), "T_EMBED_B": rupees(inr(TEN["embed_usd"]["batch"])),
    "T_SH_S": n0(TEN["shards"][SMALL]), "T_SH_M": n0(TEN["shards"][MEDIUM]), "T_SH_L": n0(TEN["shards"][LARGE]),
    "T_SERVE_S": rupees(inr(TEN["serve_usd_month"][SMALL])), "T_SERVE_M": rupees(inr(TEN["serve_usd_month"][MEDIUM])),
    "T_SERVE_L": rupees(inr(TEN["serve_usd_month"][LARGE])), "T_STREAM": rupees(inr(TEN["stream_usd"])),
    "T_COMPACT": rupees(inr(TEN["compact_usd"])), "T_COMPACT_MONTH": COMPACT_MONTH, "COMPACTIONS": WORDS[rs.COMPACTIONS_30D],
    "T_FS_GIB": fx(TEN["fs_gib"], 1), "T_FS_TIB": fx(TEN["fs_gib"] / 1024, 1), "T_FS_MONTH": rupees(inr(TEN["fs_usd_month"])),
    "T_FS_INGEST": rupees(inr(TEN["fs_ingest_usd"])), "T_FP_READS": n0(TEN["fp_reads"]), "T_FP": rupees(inr(TEN["fp_usd"])),
    "T_FP_RATE": n0(TEN["fp_last_rate"]), "T_WALK_ITEMS": n0(TEN["walk_items"]), "T_WALK_RATE": n0(TEN["walk_rate"]),
    "T_WALK_RS": rupees(inr(TEN["walk_usd"])), "T_INGEST_DAYS": fx(TEN["ingest_days_per_s"], 2),
    "T_DOCAI_DAYS": fx(TEN["docai_days"], 1), "T_BACKLOG_H": V10["backlog_h"],
    "PAGES_DOC": fx(C["pdf_pages"], 1), "PAGES_STATUTE": fx(SH["statute"]["pdf_pages"], 1),
    # the shapes
    "SH_STAT_DOCS": str(SH["statute"]["docs"]), "SH_STAT_CHUNKS": fx(SH["statute"]["chunks"], 1),
    "SH_HAND_DOCS": str(SH["handbook"]["docs"]), "SH_HAND_CHUNKS": fx(SH["handbook"]["chunks"], 1),
    "SH_SHORT_DOCS": str(SH["short"]["docs"]), "SH_SHORT_CHUNKS": fx(SH["short"]["chunks"], 1),
    "CROSS": f"{rs.crossover(C):,}", "CROSS_STAT": f"{rs.crossover(SH['statute']):,}", "CROSS_SHORT": f"{rs.crossover(SH['short']):,}",
    "SHARD_DOCS_S": f"{SHARD_DOCS[SMALL]:,}", "SHARD_DOCS_M": f"{SHARD_DOCS[MEDIUM]:,}", "SHARD_DOCS_L": f"{SHARD_DOCS[LARGE]:,}",
    # Firestore
    "FS_IDX": str(FS_IDX), "FS_IDX_W": WORDS[FS_IDX], "ROW_B": f"{ROW_B:,}", "CHUNK_B": f"{CHUNK_B:,}",
    "IDX_B": f"{CHUNK_B - ROW_B:,}", "FS_TIMES": str(r0(C["fs_chunk"] / (rs.DIMS * 4))),
    "FS_REGION": rs.FS_REGION, "WRITES": WORDS[rs.WRITES_PER_CHUNK],
    # prices and sizes
    "PRICE_DATE": PRICE_DATE, "USD_INR": str(rs.USD_INR), "EMBED_ON": usd(rs.EMBED_USD_1K["online"]),
    "EMBED_BA": usd(rs.EMBED_USD_1K["batch"]), "VS_BUILD": f"{rs.VS_BUILD_USD_GIB:.2f}", "VS_STREAM": f"{rs.VS_STREAM_USD_GIB:.2f}",
    "COMPACT_DAYS": WORDS[rs.COMPACT_DAYS], "GIB_S": str(rs.SHARD_GIB[SMALL]), "GIB_M": str(rs.SHARD_GIB[MEDIUM]),
    "GIB_L": str(rs.SHARD_GIB[LARGE]), "M_S": rs.MACHINE[SMALL], "M_M": rs.MACHINE[MEDIUM], "M_L": rs.MACHINE[LARGE],
    "FS_READ": f"{rs.FS_USD['read'] * 100_000:.3f}", "FS_WRITE": f"{rs.FS_USD['write'] * 100_000:.3f}",
    "FS_GIB_MONTH": str(rs.FS_USD["gib_month"]), "SIZING_Q1": f"{rs.SIZING['qps_one']:,}", "SIZING_Q3": f"{rs.SIZING['qps_three']:,}",
    "SIZING_V": f"{rs.SIZING['vectors'] // 1_000_000}", "SIZING_D": str(rs.SIZING["dims"]), "SIZING_M": rs.SIZING["machine"],
    # the lane's facts
    "MSA_CHARS": f"{MSA['chars']:,}", "MSA_CHUNKS": WORDS[MSA["chunks"]], "MSA_HEADS": WORDS[MSA_HEADS],
    "LANE_SHARD": LANE_SHARD_WORDS, "IN_KIT": IN_KIT_WORDS, "N_ACME": str(N_ACME), "N_ACME_MD": WORDS[N_ACME_MD], "N_GRID": str(N_GRID),
    "ACME_TABLE": ACME_TABLE, "SHARD_TABLE": SHARD_TABLE, "COST_TABLE": COST_TABLE, "CHANGE_TABLE": CHANGE_TABLE,
    "OPT_SHAPE": OPT_SHAPE, "OPT_TENANTS": OPT_TENANTS, "OPT_SHARD": OPT_SHARD, "N_STOPS": str(len(STOPS) - 1),
    "START": str(STOPS.index(N)), "NEXT_TITLE": html.escape(MANIFEST["modules"]["08"]["lessons"]["8.4"]["name"]),
    **{f"URL_{k.upper()}": v for k, v in PAGES.items()},
}
# step 2's lane column, step 4's request arithmetic, step 7's floor: the corpus's own text chunks
LANE = rs.scale(C["docs"], C)
TOK_CHUNK = rs.CHUNK_CHARS // rs.CHARS_PER_TOKEN
PER_REQ_FULL = rs.EMBED_TOKENS // TOK_CHUNK
assert PER_REQ_FULL < rs.EMBED_BATCH and (PER_REQ_FULL + 1) * TOK_CHUNK > rs.EMBED_TOKENS
STATS.update({
    "TOK_CHUNK": str(TOK_CHUNK), "PER_REQ_FULL": str(PER_REQ_FULL), "PER_REQ_AVG": fx(C["total_chunks"] / C["total_requests"], 1),
    "STAT_CHUNKS": f"{TYPES['statute'][2]:,}", "L_MIB": fx(LANE["dense_gib"] * 1024, 1),
    "L_STREAM": fx(inr(LANE["stream_usd"]), 2), "L_COMPACT": fx(inr(LANE["compact_usd"]), 2),
    "L_FS_MIB": fx(C["total_chunks"] * C["fs_chunk"] / (1 << 20), 0), "ATTEMPTS_W_CAP": WORDS[rs.MAX_ATTEMPTS].capitalize(),
    "IN_FLIGHT_CAP": WORDS[rs.IN_FLIGHT].capitalize(),
})
# claims the prose makes in words, held to the numbers
OTHERS = (TEN["serve_usd_month"][MEDIUM] + TEN["embed_usd"]["online"] + TEN["stream_usd"] + TEN["compact_usd"]
          + TEN["fs_usd_month"] + TEN["fs_ingest_usd"] + TEN["walk_usd"])
assert TEN["fp_usd"] > OTHERS                                       # "more than everything else on the page together"
_spread = rs.scale(N, C, 1_000)
assert 990 < TEN["fp_reads"] / _spread["fp_reads"] < 1010            # "about a thousandfold"
assert view(3_000, "corpus", 1, MEDIUM)["fp_over"] == view(3_000, "corpus", 1, MEDIUM)["dlq"] == "no"   # both rows turn blue
assert TYPES["statute"][2] > C["total_chunks"] / 2                   # "the statutes dominate"
ALERTS = (KIT / "terraform/alerts.tf").read_text(encoding="utf-8")
assert 'display_name = "Nightly reconcile failed"' in ALERTS and r'metric.labels.result=\"failed\"' in ALERTS
for quote in ("If the oldest uncompacted data is five days old, compaction is always triggered",
              "Dataset size and restricts (filtering) affect shard count"):
    assert quote in flat(RS_SRC.replace("\n    ", " ")), quote
assert "three" == WORDS[len(re.findall(r"\b(tenant_id|kind|doc_type)\b", "_restricts(tenant_id, kind, doc_type)"))]
assert TEN["fp_last_rate"] > TEN["walk_rate"] / 2 and rs.crossover(C) < N
assert TEN["serve_usd_month"][MEDIUM] > TEN["fs_usd_month"] and TEN["fs_ingest_usd"] < TEN["embed_usd"]["online"]
assert V10["dlq"] == "yes" and V10["fp_over"] == "yes"
assert rs.crossover(SH["short"]) < rs.crossover(C) < rs.crossover(SH["statute"])


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {C['docs']} documents, {C['total_chunks']:,} chunks, {C['total_requests']} requests (step 5's cell, run offline) | "
      f"at {N:,}: {n0(TEN['chunks'])} vectors, {fx(TEN['dense_gib'], 1)} GiB, MEDIUM {n0(TEN['shards'][MEDIUM])} shards "
      f"{rupees(inr(TEN['serve_usd_month'][MEDIUM]))} a month | the calculator agrees with Python on {N_GRID} settings (node)")
