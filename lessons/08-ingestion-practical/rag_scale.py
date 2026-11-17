"""RAG at ten million documents: the kit's own constants, its own corpus measured by its own code, and the prices and
limits the kit does not hold. One source for lesson 8.3's calculator, its Python cell and its widget, and for the
costs at three scales that lesson 8.4 states, so the pages cannot disagree.

What comes from the kit, parsed or run at build time (the build stops if a fact moves):
  - the chunker's window and overlap, in both twins (services/ingest/main.py, shared/documind_corpus.py);
  - the embedding request's two ceilings and the vector's length (services/ingest/indexer.py, and the loader's copy);
  - the index: its dimensions, STREAM_UPDATE, one replica, the machine each shard size names (terraform/vector.tf);
  - the worker: one document per instance, thirty instances, a 600-second request (commands/lesson-12.5.sh), and the
    subscription's 600-second ack deadline (terraform/eventarc.tf);
  - the nightly walk: one task, no retry, 1,200 seconds (terraform/reconcile.tf), off unless RECONCILE_JOB=true;
  - the fingerprint: every ingest streams the tenant's indexed sources (services/ingest/idempotency.py);
  - the Firestore row the worker writes per chunk (indexer.mirror_to_firestore) and the vector indexes over it
    (terraform/firestore_indexes.tf), sized by Firestore's documented rules;
  - the corpus: every text document the kit ships (evals/manifest.json), loaded with load_documents(), chunked with
    chunk_document() and batched with embed_batches(), the code a notebook and the worker share.

Facts the kit does not hold, read on 12 October 2026 from Google's pages; verify before a cohort:
  - https://cloud.google.com/vertex-ai/generative-ai/pricing (redirects to cloud.google.com/gemini-enterprise-agent-
    platform/generative-ai/pricing; no date on the page): "Embeddings for Text (Excluding Gemini Embedding)", input,
    $0.000025 per 1,000 count for online requests and $0.00002 for batch requests; output, no charge. A count is a
    character, as lessons 1.3, 1.6, B.2 and B.4 read it.
  - https://cloud.google.com/vertex-ai/pricing (redirects to cloud.google.com/products/gemini-enterprise-agent-
    platform/pricing), "Vector Search": "$3.00 per gibibyte (GiB) of data processed in all regions" for building and
    updating indexes; "$0.45/GiB ingested for Streaming Update inserts"; "If the oldest uncompacted data is five days
    old, compaction is always triggered", billed "at the same rate of a batch update"; data size is "the number of your
    embeddings/vectors * the number of dimensions you have * 4 bytes per dimension"; serving is "# replicas/shard *
    # shards (~data size/shard size) * hourly cost * 730 hours"; "Dataset size and restricts (filtering) affect shard
    count"; index serving per node hour in Mumbai (asia-south1): e2-standard-2 $0.1126804, e2-standard-16 $0.9014432,
    e2-highmem-16 $1.2160288 (the first two are lessons/00-setup/standing_cost.py's, imported and held equal); and the
    sizing example "20 million | 256 | 1,000 | e2-standard-16 | 1" against "3,000 | e2-standard-16 | 3" (us-central1).
  - https://docs.cloud.google.com/vertex-ai/docs/vector-search/create-manage-index: "SHARD_SIZE_SMALL: 2 GiB per
    shard", "SHARD_SIZE_MEDIUM: 20 GiB per shard", "SHARD_SIZE_LARGE: 50 GiB per shard"; e2-standard-2,
    e2-standard-16 and e2-highmem-16 the default machine of each; "For sparse embeddings, the supported sizes are 20%
    of the shard byte size."
  - https://cloud.google.com/firestore/pricing (Standard edition), Mumbai (asia-south1): document reads $0.035, writes
    $0.104 and deletes $0.012 per 100,000 documents; stored data $0.104 per GiB a month; the free quota 50,000 reads and
    20,000 writes a day and 1 GiB stored.
  - https://firebase.google.com/docs/firestore/storage-size: a document is its name (16 bytes plus each collection and
    document ID) plus its field names plus its field values plus 32 bytes; a string is its UTF-8 bytes plus 1, an
    integer, a float and a date 8 bytes, a boolean 1, null 1, a vector 8 bytes per dimension; a composite index entry
    is the document's name, its parent's name, the indexed values and 32 bytes.

A build imports this as `import rag_scale as rs` after putting this folder on sys.path.
"""
import json
import math
import re
import sys

from pagekit.pagebuild import KIT, ROOT

sys.path[:0] = [str(KIT), str(ROOT / "lessons" / "00-setup")]
from shared import documind_corpus as dc  # noqa: E402  the loader, the chunker and the batcher every lesson shares
import standing_cost as sc  # noqa: E402  the lane's Mumbai prices and USD_INR, imported, never re-derived

_FILES = ("services/ingest/main.py", "shared/documind_corpus.py", "services/ingest/indexer.py",
          "services/ingest/contracts.py", "services/ingest/idempotency.py", "shared/sparse_encoder.py",
          "terraform/vector.tf", "terraform/eventarc.tf", "terraform/reconcile.tf", "terraform/firestore.tf",
          "terraform/firestore_indexes.tf", "terraform/variables.tf", "commands/lesson-12.5.sh", "Makefile")
src = {p: (KIT / p).read_text(encoding="utf-8") for p in _FILES}


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


# ------------------------------------------------------------------ the kit's constants
CHUNK_CHARS, CHUNK_OVERLAP = map(int, one(r"^CHUNK_CHARS, CHUNK_OVERLAP = (\d+), (\d+)$", src["services/ingest/main.py"], re.M))
assert (dc.CHUNK_CHARS, dc.CHUNK_OVERLAP) == (CHUNK_CHARS, CHUNK_OVERLAP)            # the twins agree
IX = src["services/ingest/indexer.py"]
EMBED_BATCH = int(one(r"^EMBED_BATCH = (\d+)$", IX, re.M))
EMBED_TOKENS = int(one(r"^EMBED_TOKENS = ([\d_]+)$", IX, re.M).replace("_", ""))
CHARS_PER_TOKEN = int(one(r"^CHARS_PER_TOKEN = (\d+)$", IX, re.M))
DIMS = int(one(r"^EMBEDDING_DIMENSIONS = (\d+)$", IX, re.M))
assert (dc.EMBED_BATCH, dc.EMBED_TOKENS, dc.CHARS_PER_TOKEN) == (EMBED_BATCH, EMBED_TOKENS, CHARS_PER_TOKEN)
EMBED_MODEL = one(r'^EMBEDDING_MODEL = os\.environ\.get\("EMBEDDING_MODEL", "([\w.-]+)"\)$', IX, re.M)
EMBED_TASK = one(r'^EMBEDDING_TASK_TYPE = "(\w+)"$', IX, re.M)
EMBED_LOCATION = one(r'_embed = genai\.Client\(\s*enterprise=True,\s*project=os\.environ\["GOOGLE_CLOUD_PROJECT"\],\s*location="([\w-]+)"', IX, re.S)
# the model's own ceilings, which the kit's two stay under (indexer.py's comment in the loader's copy)
assert "250 texts per request and 20,000 tokens across them" in src["shared/documind_corpus.py"]
MODEL_TEXTS, MODEL_TOKENS = 250, 20_000

V = src["terraform/vector.tf"]
assert int(one(r"dimensions\s+= (\d+)", V)) == DIMS
assert one(r'index_update_method = "(\w+)"', V) == "STREAM_UPDATE"
REPLICAS = int(one(r"min_replica_count = (\d+)", V))
assert int(one(r"max_replica_count = (\d+)", V)) == REPLICAS == sc.VS_REPLICAS == 1
MACHINE = dict(re.findall(r"(SHARD_SIZE_[A-Z]+)\s+= \"([a-z0-9-]+)\"", V))
assert MACHINE == sc.SHARD_MACHINE
_declared = re.search(r'shard_size\s*=\s*"(SHARD_SIZE_[A-Z]+)"', V.split('resource "google_vertex_ai_index" "documind" {', 1)[1].split("index_update_method", 1)[0])
DECLARED_SHARD = _declared.group(1) if _declared else None       # main at 4dc45fd declares none: the API chooses

DEPLOY = src["commands/lesson-12.5.sh"].split("gcloud run deploy documind-ingest", 1)[1].split("gcloud run services", 1)[0]
WORKER_CONCURRENCY = int(one(r"--concurrency=(\d+)", DEPLOY))
WORKER_INSTANCES = int(one(r"--max-instances=(\d+)", DEPLOY))
WORKER_TIMEOUT = int(one(r"--timeout=(\d+)", DEPLOY))
IN_FLIGHT = WORKER_CONCURRENCY * WORKER_INSTANCES
assert (WORKER_CONCURRENCY, WORKER_INSTANCES, WORKER_TIMEOUT) == (1, 30, 600)
SUB = src["terraform/eventarc.tf"].split('resource "google_pubsub_subscription" "ingest_push"', 1)[1].split("\n}\n", 1)[0]
ACK_DEADLINE = int(one(r"ack_deadline_seconds = (\d+)", SUB))
MAX_ATTEMPTS = int(one(r"max_delivery_attempts = (\d+)", SUB))
MIN_BACKOFF, MAX_BACKOFF = (int(one(rf'{w}_backoff = "(\d+)s"', SUB)) for w in ("minimum", "maximum"))
assert (ACK_DEADLINE, MAX_ATTEMPTS, MIN_BACKOFF, MAX_BACKOFF) == (WORKER_TIMEOUT, 12, 10, 600)
# the kit's own record that a refusal counts towards the twelve (eventarc.tf's comment, read whole)
assert "the first live load sent a document to the DLQ on five refusals that were never the document's fault." in " ".join(
    line.strip().lstrip("# ") for line in SUB.splitlines())
DLQ_BOUND_S = (MAX_ATTEMPTS - 1) * MAX_BACKOFF      # eleven waits between twelve attempts, none longer than the maximum
# Document AI's pace, as the worker's own comment states it; a text upload is not parsed at all (_parse)
MAIN = src["services/ingest/main.py"]
assert "# parser.py sends a PDF to Document AI in 15-page slices at roughly a second a page, and the" in MAIN
assert 'if content_type.startswith("text/"):' in MAIN
DOCAI_S_PER_PAGE = 1
MAX_INLINE_PAGES = int(one(r"^MAX_INLINE_PAGES = (\d+)$", MAIN, re.M))

R = src["terraform/reconcile.tf"]
WALK_TASKS = int(one(r"task_count = (\d+)", R))
WALK_SECONDS = int(one(r'timeout\s+= "(\d+)s"', R))
WALK_RETRIES = int(one(r"max_retries\s+= (\d+)", R))
assert (WALK_TASKS, WALK_SECONDS, WALK_RETRIES) == (1, 1200, 0)
assert one(r'variable "reconcile_job" \{\s*type\s+= bool\s*default\s+= (\w+)', R, re.S) == "false"
assert one(r"^RECONCILE_JOB\s+\?= (\w+)$", src["Makefile"], re.M) == "false"
# what the walk loads before it plans: every object, every sources/ row, every documents/ row
WALK_SRC = (KIT / "services/ingest/reconcile.py").read_text(encoding="utf-8")
for line in ('for b in bucket.list_blobs(prefix=prefix) if "/" in b.name]',
             'ledger = {s.id: (s.to_dict() or {}) for s in db.collection("sources").stream()',
             'documents = {s.id: (s.to_dict() or {}) for s in db.collection("documents").stream()}'):
    assert line in WALK_SRC, line
WALK_LISTS = 3

FP = src["services/ingest/idempotency.py"]
assert 'db.collection("sources").where("tenant_id", "==", tenant_id).where("status", "==", "indexed").stream())' in FP
assert src["services/ingest/main.py"].count("refresh_fingerprint(_db, doc.tenant_id,") == 3   # ok, already current, reactivated
# the ledger row is written before the fingerprint is read, so the k-th document's refresh streams k rows
_OK = MAIN.split("finish(_db, doc.doc_key, len(chunks), counts, msg.generation)", 1)[1]
assert _OK.index("record_source(_db, doc.tenant_id,") < _OK.index('fingerprint = refresh_fingerprint(_db, doc.tenant_id, "ingest_ok")')
# a new version's rows are written staged, then the swap streams the source's rows and flips each new one current
assert "mirror_to_firestore(_db, doc, chunks, vectors, staged=True, stage_expire_at=_expire_at(STAGE_HOURS / 24))" in MAIN
_SWAP = FP.split("def swap_versions(", 1)[1].split("\ndef ", 1)[0]
assert "rows = list(query.stream())" in _SWAP and 'state[0].update(snap.reference, {"current": True, "staged": firestore.DELETE_FIELD,' in _SWAP
WRITES_PER_CHUNK, READS_PER_CHUNK = 2, 1

FS = src["terraform/firestore.tf"]
assert one(r"location_id = var\.(\w+)", FS) == "india_region"
FS_REGION = one(r'variable "india_region" \{\s*type\s+= string\s*default = "([\w-]+)"', src["terraform/variables.tf"], re.S)
assert FS_REGION == sc.LANE_REGION == "asia-south1"
FSI = src["terraform/firestore_indexes.tf"]


def _index(name: str) -> str:
    """One google_firestore_index resource of firestore_indexes.tf, its body."""
    return FSI.split(f'resource "google_firestore_index" "{name}" {{', 1)[1].split("\n}\n", 1)[0]


_filters = one(r"chunks_filter_indexes = \{(.*?)\n  \}", FSI, re.S)
FILTER_INDEXES = re.findall(r"^\s+(\w+)\s+= \[([^\]]*)\]", _filters, re.M)
_each = _index("chunks_filter_vector")
assert "for_each    = local.chunks_filter_indexes" in _each and 'collection  = "chunks"' in _each
assert re.findall(r'field_path = "(\w+)"', _each) == ["__name__", "embedding"]       # after each.value's fields
# every composite index on chunks ends in the document's name and the 768-number vector: two declared one by one, six
# by for_each, so a chunk row carries eight index entries that each hold its whole vector
CHUNK_VECTOR_INDEXES = [(n, re.findall(r'field_path = "(\w+)"', _index(n))) for n in ("chunks_vector", "chunks_current_vector")] + \
    [(name, [f.strip().strip('"') for f in fields.split(",")] + ["__name__", "embedding"]) for name, fields in FILTER_INDEXES]
assert len(CHUNK_VECTOR_INDEXES) == 8 and all(fs[-2:] == ["__name__", "embedding"] for _, fs in CHUNK_VECTOR_INDEXES)
assert FSI.count('collection  = "chunks"') == 3 and FSI.count("dimension = 768") == 4      # chunks x3, answer_cache x1

# ------------------------------------------------------------------ prices and limits the kit does not hold
USD_INR = sc.USD_INR
MONTH_H = sc.MONTH_H
EMBED_USD_1K = {"online": 0.000025, "batch": 0.00002}       # per 1,000 characters, input; output no charge
VS_NODE_USD = {"SHARD_SIZE_SMALL": sc.PRICES["vs:e2-standard-2"], "SHARD_SIZE_MEDIUM": sc.PRICES["vs:e2-standard-16"],
               "SHARD_SIZE_LARGE": 1.2160288}                # Mumbai, per node hour, by the machine each size names
SHARD_GIB = {"SHARD_SIZE_SMALL": 2, "SHARD_SIZE_MEDIUM": 20, "SHARD_SIZE_LARGE": 50}
SPARSE_SHARE = 0.20                                          # the sparse half's share of a shard's bytes (quoted only)
VS_BUILD_USD_GIB, VS_STREAM_USD_GIB, COMPACT_DAYS = 3.00, 0.45, 5
COMPACTIONS_30D = 30 // COMPACT_DAYS                         # a lane that streams every day: one rebuild every five days
FS_USD = {"read": 0.035 / 100_000, "write": 0.104 / 100_000, "delete": 0.012 / 100_000, "gib_month": 0.104}
FS_FREE = {"reads_day": 50_000, "writes_day": 20_000, "gib": 1}
SIZING = {"vectors": 20_000_000, "dims": 256, "qps_one": 1_000, "qps_three": 3_000, "machine": "e2-standard-16"}
GIB = 1 << 30
SHORT = {"SHARD_SIZE_SMALL": "SMALL", "SHARD_SIZE_MEDIUM": "MEDIUM", "SHARD_SIZE_LARGE": "LARGE"}


# ------------------------------------------------------------------ Firestore's size rules, on the worker's own row
def str_bytes(s: str) -> int:
    return len(s.encode("utf-8")) + 1


_ROW = one(r"        row = \{\n(.*?)\n        \}", IX.split("def mirror_to_firestore(", 1)[1], re.S)
ROW_FIELDS = re.findall(r'^\s+"(\w+)":', _ROW, re.M)
assert ROW_FIELDS == ["tenant_id", "text", "source_uri", "page_start", "doc_type", "kind", "doc_key", "current",
                      "indexed_at", "chunk_hash", "locator", "embedding_model", "embedding_version",
                      "embedding_task_type", "sparse_encoder_version", "schema_version", "embedding"], ROW_FIELDS
assert 'return f"{self.tenant_id}:{self.sha256}#{i}"' in src["services/ingest/contracts.py"]
assert 'return f"{self.tenant_id}_{self.sha256}"' in src["services/ingest/contracts.py"]
SPARSE_VERSION = one(r'^SPARSE_ENCODER_VERSION = "([\w-]+)"$', src["shared/sparse_encoder.py"], re.M)
SCHEMA_VERSION = int(one(r"^SCHEMA_VERSION = (\d+)$", src["services/ingest/contracts.py"], re.M))
PLACEHOLDER = "documind-ai-YOUR-ID"


def row_bytes(chunk: dict, tenant: str, slug: str, i: int) -> tuple[int, int]:
    """(the row, its eight vector index entries) in bytes, by Firestore's documented rules: a floor, because the
    automatic single-field indexes and a composite entry's parent name are not counted."""
    name = 16 + str_bytes("chunks") + str_bytes(f"{tenant}:{'0' * 64}#{i}")
    values = {
        "tenant_id": str_bytes(tenant), "text": str_bytes(chunk["text"]),
        "source_uri": str_bytes(f"gs://{PLACEHOLDER}-uploads/{tenant}/{slug}.md"),
        "page_start": 8 if chunk.get("page_start") is not None else 1, "doc_type": str_bytes(chunk["doc_type"]),
        "kind": str_bytes(chunk.get("kind", "text")), "doc_key": str_bytes(f"{tenant}_{'0' * 64}"), "current": 1,
        "indexed_at": 8, "chunk_hash": str_bytes(chunk["chunk_hash"]), "locator": str_bytes(chunk["locator"]),
        "embedding_model": str_bytes(EMBED_MODEL), "embedding_version": str_bytes("1"),
        "embedding_task_type": str_bytes(EMBED_TASK), "sparse_encoder_version": str_bytes(SPARSE_VERSION),
        "schema_version": 8, "embedding": 8 * DIMS}
    if chunk.get("section"):
        values["section"] = str_bytes(chunk["section"])
    row = name + sum(str_bytes(k) for k in values) + sum(values.values()) + 32
    indexed = {**values, "__name__": name}               # a reference is the size of the name it holds
    entries = sum(name + sum(indexed[f] for f in fields) + 32 for _, fields in CHUNK_VECTOR_INDEXES)
    return row, entries


# ------------------------------------------------------------------ the corpus, measured by the kit's own code
_MANIFEST = json.loads((KIT / "evals/manifest.json").read_text(encoding="utf-8"))
MANIFEST_TEXT = {(m["tenant_id"], m["slug"]): m for m in _MANIFEST if m.get("chars")}
SCANNED = [m["slug"] for m in _MANIFEST if m["file"].endswith(".pdf") and not m.get("chars")]
DOCS = []
for tenant in ("acme", "globex", "zeta"):
    for d in dc.load_documents(tenant, str(KIT / "evals"), PLACEHOLDER):
        chunks = dc.chunk_document(d, tenant)
        sizes = [row_bytes(c, tenant, d["slug"], i) for i, c in enumerate(chunks)]
        m = MANIFEST_TEXT[(tenant, d["slug"])]
        DOCS.append({"tenant": tenant, "slug": d["slug"], "doc_type": d["doc_type"], "chars": len(d["text"]),
                     "pdf_pages": m["pages"] if m["file"].endswith(".pdf") else 0,     # Document AI's pages; a .md has none
                     "chunks": len(chunks), "sent": sum(len(c["text"]) for c in chunks),
                     "requests": len(dc.embed_batches([c["text"] for c in chunks])),
                     "fs_row": sum(r for r, _ in sizes), "fs_index": sum(e for _, e in sizes)})
assert set(MANIFEST_TEXT) == {(d["tenant"], d["slug"]) for d in DOCS}
assert len(DOCS) == 27 and SCANNED == ["posh_act_2013"]     # every document with text; the one scan needs Document AI

_KINDS = (("corpus", "the kit's corpus as it is", None),
          ("statute", "statute-like (an Act or a Code)", ("statute",)),
          ("handbook", "handbook-like (a policy or guidance)", ("policy", "guidance")),
          ("short", "short-document-like (a contract, an invoice, a report, a transcript)", ("contract", "invoice", "report", "transcript")))


def _shape(key: str, label: str, types) -> dict:
    ds = [d for d in DOCS if types is None or d["doc_type"] in types]
    n = len(ds)
    tot = {k: sum(d[k] for d in ds) for k in ("chars", "chunks", "sent", "requests", "fs_row", "fs_index", "pdf_pages")}
    return {"key": key, "label": label, "docs": n, "types": sorted({d["doc_type"] for d in ds}),
            "chars": tot["chars"] / n, "chunks": tot["chunks"] / n, "sent": tot["sent"] / n, "requests": tot["requests"] / n,
            "pdf_pages": tot["pdf_pages"] / n,
            "fs_chunk": (tot["fs_row"] + tot["fs_index"]) / tot["chunks"], "fs_row_chunk": tot["fs_row"] / tot["chunks"],
            "total_chunks": tot["chunks"], "total_chars": tot["chars"], "total_sent": tot["sent"], "total_requests": tot["requests"]}


SHAPES = {k: _shape(k, label, types) for k, label, types in _KINDS}
assert sum(SHAPES[k]["docs"] for k in ("statute", "handbook", "short")) == SHAPES["corpus"]["docs"]


# ------------------------------------------------------------------ the calculator (the widget's JavaScript is its twin)
def scale(docs: int, shape: dict, tenants: int = 1) -> dict:
    """Everything the page states for `docs` documents of one shape, spread evenly over `tenants`."""
    chunks = docs * shape["chunks"]
    sent = docs * shape["sent"]
    dense_gib = chunks * DIMS * 4 / GIB
    per_tenant = docs / tenants
    fp_reads = tenants * per_tenant * (per_tenant + 1) / 2
    out = {"docs": docs, "tenants": tenants, "chunks": chunks, "sent": sent, "requests": docs * shape["requests"],
           "embed_usd": {m: sent / 1000 * p for m, p in EMBED_USD_1K.items()},
           "dense_gib": dense_gib, "build_usd": dense_gib * VS_BUILD_USD_GIB, "stream_usd": dense_gib * VS_STREAM_USD_GIB,
           "shards": {}, "serve_usd_month": {},
           "compact_usd": dense_gib * VS_BUILD_USD_GIB,
           "fs_gib": chunks * shape["fs_chunk"] / GIB,
           "fs_ingest_usd": chunks * (WRITES_PER_CHUNK * FS_USD["write"] + READS_PER_CHUNK * FS_USD["read"]),
           "fp_reads": fp_reads, "fp_usd": fp_reads * FS_USD["read"], "fp_last": per_tenant,
           "fp_last_rate": per_tenant / WORKER_TIMEOUT,
           "walk_items": WALK_LISTS * docs, "walk_rate": WALK_LISTS * docs / WALK_SECONDS,
           "walk_usd": 2 * docs * FS_USD["read"],
           "ingest_days_per_s": docs / IN_FLIGHT / 86_400,
           "docai_days": docs * shape["pdf_pages"] * DOCAI_S_PER_PAGE / IN_FLIGHT / 86_400}
    out["fs_usd_month"] = out["fs_gib"] * FS_USD["gib_month"]
    for size, gib in SHARD_GIB.items():
        shards = max(1, math.ceil(dense_gib / gib))
        out["shards"][size] = shards
        out["serve_usd_month"][size] = REPLICAS * shards * VS_NODE_USD[size] * MONTH_H
    return out


def crossover(shape: dict) -> int:
    """The tenant size at which one more document's fingerprint costs more to read than the document costs to embed."""
    return math.ceil(shape["sent"] / 1000 * EMBED_USD_1K["online"] / FS_USD["read"])


def shard_docs(shape: dict, size: str) -> int:
    """How many documents of a shape one shard of a size holds by dense bytes alone (a ceiling: restricts and the
    sparse half take more)."""
    return math.floor(SHARD_GIB[size] * GIB / (DIMS * 4) / shape["chunks"])


def inr(usd: float) -> float:
    return usd * USD_INR


def r0(x: float) -> int:
    return sc.r0(x)


def group(n: float) -> str:
    """An integer grouped the Indian way: 1,02,08,000."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def rupees(x: float) -> str:
    """Rupees for prose: lakh and crore above a lakh, grouped rupees below."""
    if x >= 1e7:
        return f"Rs {x / 1e7:,.2f} crore"
    if x >= 1e5:
        return f"Rs {x / 1e5:,.2f} lakh"
    return f"Rs {group(r0(x))}"
