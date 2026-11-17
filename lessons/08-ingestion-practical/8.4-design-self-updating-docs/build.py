"""Build lesson 8.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

A design page: a documentation platform that keeps its answers current as its documents change, built only from the
kit's ingestion and freshness parts - the bucket's notification and the push subscription, the generation guard and
the claim, the section chunker and the carry-over, the staged swap, the three copies (Vector Search, the managed
stores, BigQuery), the ledger and its fingerprint, the two caches that follow it, and the nightly walk. Written in the
shape of the capstone rubric (plan/capstone-rubric.md, which lesson 11.8 publishes), as lesson 3.9 is: its sections
follow the five dimensions. The proof: three rejected options the kit itself records, each dated in a kit comment, and
the cost at three scales, which is lessons/08-ingestion-practical/rag_scale.py's (lesson 8.3), imported and never
re-derived.

What the page computes at build time:
  - the ripple panel: nine changes run through the kit's own functions on a stand-in Firestore - idempotency.py
    (the guard, the claim, the swap, the undo, retire_previous, the ledger row, the fingerprint) loaded with its
    cloud client stubbed, the worker's chunker and the indexer's carry-over lifted from main.py and indexer.py with
    `ast` (both build cloud clients at import), the managed mirror's own Mirror class over two stores that record
    instead of calling, shared/doc_types.assign(), shared/tenancy.policy_for(), reconcile.py's planner, and the two
    caches' own freshness rules (cache_manager.stale_against, semantic_cache._alive). The order of the calls is
    held against main.py's and reconcile.py's source; every count the panel prints is the simulation's;
  - the three rejected options' numbers: the handbook re-issued by section and by whole-document windows (the
    kit's own record, 281 of 283 against none of 92, reproduced), the retention window's floor and its storage
    (rag_scale's Firestore floor), and the push lane's dead-letter bound (rag_scale's);
  - the alert policies the kit declares at its defaults and with the nightly walk on, parsed from terraform/;
  - the cost at 1k, 100k and 10M documents (rag_scale.scale) beside the cost of one edit, whose Firestore writes and
    reads are the simulation's own count;
  - the evals: run_eval's offline gate, the version rows, the scope of the anchors check;
  - six offline cells, executed here in deploy/, whose output is the page's expected output.

No live run: a design page. The lane reads on the page show their format with the course's placeholders; their
values are the learner's own.
"""
import ast
import html
import importlib.util
import io
import json
import logging
import math
import os
import re
import subprocess
import sys
import textwrap
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules imported below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, PLAN, block, filler, finish, setup_section, window  # noqa: E402

sys.path.insert(0, str(HERE.parent))
import rag_scale as rs  # noqa: E402  lesson 8.3's module: the prices, the limits and scale()

LESSON = "8.4"
NAME = pb.lesson_meta(LESSON)[1]["name"]
title = (f"<title>Lesson {LESSON} {NAME} - one change and everything it ripples into, the copies that do not follow, "
         "and the bill at three scales | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
NEXT = MANIFEST["modules"]["09"]["lessons"]["9.1"]["name"]

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the ripple panel: a change, four switches, fifteen stations */
.rp-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:8px 14px;margin:0 0 10px;align-items:end;}
.rp-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.rp-in label.rp-wide{grid-column:1 / -1;}
.rp-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rp-path{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:8px;font-size:12.5px;}
.rp-st{margin:0;background:var(--card);border:1px solid var(--border);border-left:4px solid var(--teal);border-radius:10px;padding:8px 12px;line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.rp-st b{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;}
.rp-st .rp-f{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--cyan);margin-bottom:2px;}
.rp-st .rp-c{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin-top:4px;}
.rp-st.skip{border-left-style:dashed;border-left-color:#cbd5e1;background:var(--bg);color:#64748b;}
.rp-st.held{border-left-color:#f59e0b;background:#fffbeb;}
.rp-st.stop{border-left-color:#0891b2;background:#ecfeff;}
.rp-st.gap{border-left-color:#be123c;background:#fff1f2;}
.rp-key{display:flex;flex-wrap:wrap;gap:6px 14px;margin:10px 0 0;font-size:var(--kicker-size);font-family:var(--mono);color:var(--slate);}
.rp-key span{display:inline-flex;align-items:center;gap:6px;}
.rp-key i{display:inline-block;width:14px;height:10px;border-radius:3px;border:1px solid var(--border);border-left-width:4px;}
.rp-key .k-run{border-left-color:var(--teal);}.rp-key .k-held{border-left-color:#f59e0b;background:#fffbeb;}
.rp-key .k-stop{border-left-color:#0891b2;background:#ecfeff;}.rp-key .k-gap{border-left-color:#be123c;background:#fff1f2;}
.rp-key .k-skip{border-left-style:dashed;border-left-color:#cbd5e1;}
.rp-out{font-size:var(--small-size);color:var(--navy);font-weight:700;margin:10px 0 0;}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's pin words
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no "
         "read on this page depends on which store answers. The two windows below are on every page; you can skip both "
         "here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index "
         "while you read."),
        ("Leave it until the lesson's last step is done.", "If you ran it, leave it until the lesson's last step is done.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)
assert "step 3 makes the difference visible." in setup          # this page's step 3: the UI as you, the shell as the UI's account

src = lambda rel: (KIT / rel).read_text(encoding="utf-8")  # noqa: E731
flat = lambda s: re.sub(r"\s+", " ", s)                     # noqa: E731


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


def word(n: int) -> str:
    """A small count as the prose says it."""
    return "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split()[n]


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def short(fp: str) -> str:
    """A hash as the page writes it: its first eight characters and three dots."""
    return fp[:8] + "..."


# ================================================================== the rubric (plan/capstone-rubric.md)
RUBRIC = (PLAN / "capstone-rubric.md").read_text(encoding="utf-8")
COMPONENTS = re.findall(r"^\| (\d) \| (.+?) \| (.+?) \| (.+?) \|$", RUBRIC, re.M)
assert [int(r[0]) for r in COMPONENTS] == list(range(1, 9)), COMPONENTS
assert "ARCHITECTURE.md" in COMPONENTS[4][1] and COMPONENTS[4][3] == "It names at least three rejected options and why."
assert "COST-MODEL.md" in COMPONENTS[5][1] and COMPONENTS[5][3] == "Dual-priced INR, dated, at `USD_INR = 85`."
assert "FAILURE-MODES.md" in COMPONENTS[6][1] and "four entries, each proved by a script" in COMPONENTS[6][1]
RUBRIC_DIMS = re.findall(r"^### (\d)\. (.+?) \(0–3\)$", RUBRIC, re.M)
assert [d for _, d in RUBRIC_DIMS] == ["Architecture", "Failure modes", "Cost at 10×", "Evals", "What you would do next month"], RUBRIC_DIMS
SCORE = one(r"\*\*(\w+) dimensions, scored 0–3 each\. (\d+) points available\. (\d+) to pass, with no dimension at 0\.\*\*", RUBRIC)
POINTS, PASS = int(SCORE[1]), int(SCORE[2])
assert (SCORE[0], POINTS, PASS) == ("Five", 15, 9)
# lesson 11.8 publishes it and checks the components; the defence scores the dimensions (13 October 2026)
assert "lesson 11.8's page shows this document to learners" in RUBRIC and "`make capstone-check FORK=<the fork>`" in RUBRIC

# ================================================================== the kit's settings the design rests on
MK = src("Makefile") + "".join("\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
mk_default = lambda name: one(rf"^{name}\s+\?= (\S+)", src("Makefile"), re.M)  # noqa: E731
DEFAULTS = {k: mk_default(k) for k in ("RECONCILE_JOB", "BATCH_JOB", "SEMANTIC_CACHE", "MANAGED_MIRROR", "RETENTION_DAYS",
                                       "EMBEDDING_MODEL", "EMBEDDING_VERSION", "RETRIEVAL_CURRENT_ONLY")}
assert DEFAULTS == {"RECONCILE_JOB": "false", "BATCH_JOB": "false", "SEMANTIC_CACHE": "off", "MANAGED_MIRROR": "both",
                    "RETENTION_DAYS": "30", "EMBEDDING_MODEL": "text-embedding-005", "EMBEDDING_VERSION": "1",
                    "RETRIEVAL_CURRENT_ONLY": "off"}, DEFAULTS
RETENTION = int(DEFAULTS["RETENTION_DAYS"])
assert "MANAGED_MIRROR=$(MANAGED_MIRROR) RAG_LOCATION=$(RAG_LOCATION)" in MK            # deploy-services hands it to the worker
assert "BQ_CHUNK_TABLE=$(PROJECT).rag_data.chunk_source;" in MK                            # and BigQuery's table, always
assert "reconcile-job: RECONCILE_JOB = true" in MK and "batch-job: BATCH_JOB = true" in MK
VARS = src("terraform/variables.tf")
RET_BLOCK = VARS.split('variable "retention_days" {', 1)[1].split("\n}\n", 1)[0]
assert int(one(r"default = (\d+)", RET_BLOCK)) == RETENTION
RET_MIN, RET_MAX = map(int, one(r"condition\s+= var\.retention_days >= (\d+) && var\.retention_days <= (\d+)", RET_BLOCK))
assert (RET_MIN, RET_MAX) == (1, 3650)
WORKER = src("services/ingest/main.py")
assert 'RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))' in WORKER
STAGE_HOURS = int(one(r"^STAGE_HOURS = (\d+)", WORKER, re.M))
RECON = src("services/ingest/reconcile.py")
assert "a day of\n    the stamp" in RECON or "within about a day of the stamp" in flat(RECON)    # the TTL's own lag, as the kit states it

EV = src("terraform/eventarc.tf")
NOTIF = EV.split('resource "google_storage_notification" "uploads" {', 1)[1].split("\n}\n", 1)[0]
EVENT_TYPES = ast.literal_eval(one(r"event_types\s+= (\[.*?\])", NOTIF))
assert EVENT_TYPES == ["OBJECT_FINALIZE"], EVENT_TYPES                                   # a delete publishes nothing
_UPLOADS = src("terraform/storage.tf").split('resource "google_storage_bucket" "uploads" {', 1)[1].split("\n}\n", 1)[0]
assert "versioning { enabled = true }" in _UPLOADS                                      # a delete archives the live generation
SUB_NAME = one(r'resource "google_pubsub_subscription" "ingest_push" \{\s*name\s+= "([\w-]+)"', EV)
DLQ_SUB = one(r'resource "google_pubsub_subscription" "ingest_dlq_sub" \{\s*name\s+= "([\w-]+)"', EV)
TOPIC = one(r'resource "google_pubsub_topic" "ingest" \{ name = "([\w-]+)" \}', EV)
DLQ_TOPIC = one(r'resource "google_pubsub_topic" "ingest_dlq" \{ name = "([\w-]+)" \}', EV)
assert (SUB_NAME, DLQ_SUB, TOPIC, DLQ_TOPIC) == ("documind-ingest-push", "ingest-dlq-sub", "documind-ingest", "documind-ingest-dlq")
RT = src("terraform/reconcile.tf")
WALK_CRON, WALK_TZ = one(r'schedule\s+= "([\d *]+)"', RT), one(r'time_zone\s+= "([\w/]+)"', RT)
assert (WALK_CRON, WALK_TZ) == ("30 23 * * *", "Asia/Kolkata") and rs.WALK_SECONDS == 1200 and rs.WALK_TASKS == 1
WALK_AT = "23:30 IST"
BT = src("terraform/batch.tf")
BATCH_CRON, BATCH_TIMEOUT = one(r'schedule\s+= "([\d *]+)"', BT), int(one(r'timeout\s+= "(\d+)s"', BT))
assert (BATCH_CRON, BATCH_TIMEOUT) == ("15 * * * *", 7200)
POISON_SH = src("commands/poison.sh")
assert ': > "/tmp/$NAME"' in POISON_SH and "twelve attempts" in POISON_SH                 # a zero-byte object, retried to the DLQ
assert "make dlq about an hour after this line" in POISON_SH                                # the kit's own estimate of the wait
assert "A poison upload (make poison) reaches it about an hour later." in src("terraform/alerts.tf")
assert "size: int = Field(ge=1)" in src("services/ingest/contracts.py")
assert 'raise HTTPException(400, "unparseable message")' in WORKER
GEN_MODEL = one(r'generator_model: str = "([^"]+)"', src("services/rag-api/config.py"))
PROMPT_V = one(r'prompt_version: str = "(v\d+)"', src("services/rag-api/config.py"))
TOP_K = int(one(r"top_k: int = Field\(default=(\d+), ge=1, le=20\)", src("services/rag-api/schemas.py")))
POLICIES = ast.literal_eval(one(r"    policies = (\[.*?\])\n", src("commands/lane.py")))
assert POLICIES == [("acme", "any"), ("zeta", "any"), ("globex", "in")], POLICIES
assert 'MAX_INLINE_PAGES = 250' in WORKER and rs.MAX_INLINE_PAGES == 250

# the worker's order, held against its source: what the simulation below calls, in this order
PUSH = WORKER.split("async def push(request: Request):", 1)[1].split("\ndef index_document(", 1)[0]
INDEX_DOC = WORKER.split("def index_document(", 1)[1]
ORDER_PUSH = ["IngestMessage.model_validate_json(raw)", "stale_generation(_db, msg.tenant_id, msg.name, msg.generation)",
              "blob = _gcs.bucket(msg.bucket).blob(msg.name, generation=int(msg.generation))",
              "if not claim(_db, doc.doc_key, doc.gcs_uri, doc.tenant_id):", 'status_of(_db, doc.doc_key) == "superseded"',
              "withdrawn(_db, doc.tenant_id, doc.gcs_uri)", "back = reactivate(_db, doc.tenant_id, doc.gcs_uri, doc.doc_key)",
              "reupsert(INDEX_NAME, _db, doc.tenant_id, doc.gcs_uri, doc.doc_key)", "gone = retire_previous(",
              "_mirror.after_undo(", 'refresh_fingerprint(_db, doc.tenant_id, "ingest_reactivated")',
              "claim(_db, doc.doc_key, doc.gcs_uri, doc.tenant_id, retake=True)", 'status_of(_db, doc.doc_key) == "processing"',
              "lease = retake_expired(_db, doc.doc_key, doc.gcs_uri, doc.tenant_id)", 'status_of(_db, doc.doc_key) == "queued"',
              "already = current_chunks(", "return index_document(doc, msg, content)"]
ORDER_INDEX = ["doc = doc_types.assign(_db, doc, msg.name)", "pages = _pdf_pages(content)", "_enqueue_batch(doc, msg)",
               "text, pages = _parse(content, msg.content_type)", "chunks = _chunk(text)",
               "pii_inspect_many([c[\"text\"] for c in chunks])", "vectors, counts = embed_with_carry_over(_db, doc, chunks)",
               "mirror_to_firestore(_db, doc, chunks, vectors, staged=True", "gone = swap_versions(",
               "upsert(INDEX_NAME, to_datapoints(doc, chunks, vectors))", 'remove_datapoints(INDEX_NAME, gone["retired_ids"])',
               "_mirror.after_swap(doc, text, gone,", "mirror_to_bigquery(", "finish(_db, doc.doc_key, len(chunks), counts, msg.generation)",
               "record_source(_db, doc.tenant_id, msg.name", 'fingerprint = refresh_fingerprint(_db, doc.tenant_id, "ingest_ok")']
for body, order in ((PUSH, ORDER_PUSH), (INDEX_DOC, ORDER_INDEX)):
    at = [body.index(s) for s in order]
    assert at == sorted(at), [(s, a) for s, a in zip(order, at)]
# the walk's apply branch and make retire's, in reconcile.py's order; since 13 October 2026 both take the retired ids out
# of the index, after the ledger row, with the worker's own remove_datapoints()
WALK_APPLY = RECON.split('if act["action"] == "retire":', 1)[1].split("THE DRIFT LINE", 1)[0]
for a, b in (("retire_previous(db,", "mirror.retired("), ("mirror.retired(", '{"status": "retired"'),
             ('{"status": "retired"', "remove_vectors(index_name, gone)"), ("blob.rewrite(blob)", "refresh_fingerprint(db, tenant")):
    assert WALK_APPLY.index(a) < WALK_APPLY.index(b), (a, b)
RETIRE_BRANCH = RECON.split("WITHDRAWAL IS A TOMBSTONE", 1)[1].split("if a.restore:", 1)[0]
for a, b in (("gone = retire_previous(db, tenant, uri, None, expire_at=expire_at)", 'mirror.retired(tenant, gone.get("retired_doc_keys", []), "withdrawn")'),
             ('mirror.retired(', '{"status": "withdrawn"'), ('{"status": "withdrawn"', "remove_vectors(index_name, gone)"),
             ("remove_vectors(index_name, gone)", 'refresh_fingerprint(db, tenant, "reconcile_withdrawn")')):
    assert RETIRE_BRANCH.index(a) < RETIRE_BRANCH.index(b), (a, b)
assert RECON.count("remove_vectors(index_name, gone)") == 2 and "from indexer import remove_datapoints as remove" in RECON
assert "upsert" not in RECON.split("def main()", 1)[1].split("if a.backfill_vectors:", 1)[0]
assert {p.name for p in (KIT / "services/ingest").glob("*.py") if "remove_datapoints" in p.read_text(encoding="utf-8")} == \
    {"indexer.py", "main.py", "relabel.py", "reconcile.py"}     # the def, the worker's two calls, the relabel's, the walk's
# the claim's lease (13 October 2026): the push subscription's ack deadline and a minute; the batch job's timeout and a minute
IDEM_SRC = src("services/ingest/idempotency.py")
LEASE_S = sum(map(int, one(r"^LEASE_SECONDS = (\d+) \+ (\d+)$", IDEM_SRC, re.M)))
BATCH_LEASE_S = sum(map(int, one(r"^BATCH_LEASE_SECONDS = (\d+) \+ (\d+)$", IDEM_SRC, re.M)))
assert (LEASE_S, BATCH_LEASE_S) == (rs.ACK_DEADLINE + 60, BATCH_TIMEOUT + 60) == (660, 7260), (LEASE_S, BATCH_LEASE_S)

# ================================================================== the stand-in Firestore, and the kit's modules on it
NOW = datetime.now(timezone.utc).replace(microsecond=0)        # only ages are taken from it; no time reaches the page
TS, DEL = object(), object()
STUB = types.SimpleNamespace(SERVER_TIMESTAMP=TS, DELETE_FIELD=DEL, Client=object, Transaction=object, transactional=lambda f: f)
try:
    from google.cloud import firestore as _real_fs           # managed.Mirror.stamp() imports the real one for its timestamp
    REAL_TS = _real_fs.SERVER_TIMESTAMP
except Exception:  # noqa: BLE001
    REAL_TS = TS


class Store:
    """The documents a Firestore holds, by path, with every billed read and write counted."""

    def __init__(self):
        self.docs, self.reads, self.writes, self.tick = {}, 0, 0, 0

    def stamp(self):
        """The next server timestamp: strictly later than the last, so the newest-per-source guard can order rows."""
        self.tick += 1
        return NOW + timedelta(seconds=self.tick)

    def apply(self, path, data, merge):
        """One document write: merge or replace, the two sentinels honoured."""
        cur = dict(self.docs.get(path) or {}) if merge else {}
        for k, v in data.items():
            if v is DEL:
                cur.pop(k, None)
            elif v is TS or v is REAL_TS:
                cur[k] = self.stamp()
            else:
                cur[k] = v
        self.docs[path] = cur
        self.writes += 1

    def collection(self, name):
        return Coll(self, (name,))

    def batch(self):
        return Batch(self)

    def transaction(self):
        return types.SimpleNamespace(set=lambda ref, data: ref.set(data))


class Snap:
    def __init__(self, ref, d):
        self.reference, self.id, self._d, self.exists = ref, ref.path[-1], d, d is not None

    def to_dict(self):
        return dict(self._d) if self._d is not None else None

    def get(self, field):
        return (self._d or {}).get(field)


class Ref:
    def __init__(self, st, path):
        self.st, self.path = st, path

    @property
    def id(self):
        return self.path[-1]

    def get(self, transaction=None):
        self.st.reads += 1
        return Snap(self, self.st.docs.get(self.path))

    def set(self, data, merge=False):
        self.st.apply(self.path, data, merge)

    def update(self, data):
        self.st.apply(self.path, data, True)

    def collection(self, name):
        return Coll(self.st, self.path + (name,))


class Coll:
    def __init__(self, st, path, filters=()):
        self.st, self.path, self.filters = st, path, tuple(filters)

    def document(self, key):
        return Ref(self.st, self.path + (key,))

    def where(self, field, op, value):
        assert op == "==", op
        return Coll(self.st, self.path, self.filters + ((field, value),))

    def stream(self):
        hits = [Snap(Ref(self.st, p), d) for p, d in list(self.st.docs.items())
                if len(p) == len(self.path) + 1 and p[:-1] == self.path and all(d.get(f) == v for f, v in self.filters)]
        self.st.reads += max(1, len(hits))                      # a query bills a read per document, and one for none
        return iter(hits)


class Batch:
    def __init__(self, st):
        self.st, self.ops = st, []

    def set(self, ref, data, merge=False):
        self.ops.append((ref, data, merge))

    def update(self, ref, data, option=None):
        self.ops.append((ref, data, True))

    def commit(self):
        for ref, data, merge in self.ops:
            ref.set(data, merge=merge)
        self.ops = []


def load(rel: str, name: str, fakes: dict | None = None):
    """A kit module, executed from its file; `fakes` stand in for the cloud packages it imports."""
    saved = {k: sys.modules.get(k) for k in (fakes or {})}
    sys.modules.update(fakes or {})
    try:
        spec = importlib.util.spec_from_file_location(name, KIT / rel)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)


def lift(rel: str, names: list, ns: dict) -> dict:
    """The named top-level definitions and assignments of a kit file, executed alone: main.py and indexer.py build
    cloud clients when imported, so their functions are taken out whole and run against the namespace given."""
    text = src(rel)
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            exec(ast.get_source_segment(text, node), ns)
        elif isinstance(node, ast.Assign):
            got = []
            for t in node.targets:
                got += [e.id for e in t.elts] if isinstance(t, ast.Tuple) else [getattr(t, "id", None)]
            if set(got) & set(names):
                exec(ast.get_source_segment(text, node), ns)
    missing = [n for n in names if n not in ns]
    assert not missing, (rel, missing)
    return ns


sys.path[:0] = [str(KIT), str(KIT / "services" / "ingest")]
import contracts  # noqa: E402  pydantic only
import managed  # noqa: E402  standard library at import
import reconcile  # noqa: E402  the planner is pure
from shared import doc_types, tenancy  # noqa: E402  no cloud import at module level
from pypdf import PdfReader, PdfWriter  # noqa: E402

idem = load("services/ingest/idempotency.py", "idempotency_84")
idem.firestore = STUB                                       # the real package would want a real transaction
LOG = []


class _Grab(logging.Handler):
    def emit(self, record):
        LOG.append(record.getMessage())


for _name in ("documind.ingest", "documind.doc_types"):
    logging.getLogger(_name).addHandler(_Grab())
    logging.getLogger(_name).setLevel(logging.INFO)
    logging.getLogger(_name).propagate = False

W = lift("services/ingest/main.py", ["CHUNK_CHARS", "CHUNK_OVERLAP", "_SECTION", "_CODE", "_windows", "_chunk",
                                     "MAX_INLINE_PAGES", "_pdf_pages"],
         {"re": re, "io": io, "chunk_hash": contracts.chunk_hash, "PdfReader": PdfReader})
IX = lift("services/ingest/indexer.py", ["EMBEDDING_MODEL", "EMBEDDING_VERSION", "EMBEDDING_TASK_TYPE", "EMBEDDING_DIMENSIONS",
                                         "valid_vector", "document_embedding_matches", "held_vectors", "plan_carry_over",
                                         "mirror_to_firestore"],
          {"os": types.SimpleNamespace(environ={}), "math": math, "firestore": STUB, "Vector": list,
           "SCHEMA_VERSION": contracts.SCHEMA_VERSION,
           "SPARSE_ENCODER_VERSION": one(r'^SPARSE_ENCODER_VERSION = "([\w-]+)"$', src("shared/sparse_encoder.py"), re.M)})
assert (W["CHUNK_CHARS"], W["CHUNK_OVERLAP"]) == (rs.CHUNK_CHARS, rs.CHUNK_OVERLAP) == (2000, 200)
assert (IX["EMBEDDING_MODEL"], IX["EMBEDDING_VERSION"]) == (DEFAULTS["EMBEDDING_MODEL"], DEFAULTS["EMBEDDING_VERSION"])
DIMS = IX["EMBEDDING_DIMENSIONS"]

# the two caches' own freshness rules: semantic_cache's module with its client stubbed, cache_manager's methods lifted
_fs = types.ModuleType("google.cloud.firestore")
_fs.Client, _fs.SERVER_TIMESTAMP = object, object()
_bvq = types.ModuleType("google.cloud.firestore_v1.base_vector_query")
_bvq.DistanceMeasure = types.SimpleNamespace(COSINE="COSINE")
_vec = types.ModuleType("google.cloud.firestore_v1.vector")
_vec.Vector = list
_gc = types.ModuleType("google.cloud")
_gc.firestore = _fs
SC = load("services/rag-api/semantic_cache.py", "semantic_cache_84",
          {"google.cloud": _gc, "google.cloud.firestore": _fs, "google.cloud.firestore_v1": types.ModuleType("google.cloud.firestore_v1"),
           "google.cloud.firestore_v1.base_vector_query": _bvq, "google.cloud.firestore_v1.vector": _vec})
CM_SRC = src("services/rag-api/cache_manager.py")
_cls = next(n for n in ast.parse(CM_SRC).body if isinstance(n, ast.ClassDef) and n.name == "TenantCacheManager")
_meth = {n.name: textwrap.dedent(ast.get_source_segment(CM_SRC, n)) for n in _cls.body if isinstance(n, ast.FunctionDef)}
_ns = {}
for _m in ("ledger_fingerprint", "stale_against"):
    exec(_meth[_m], _ns)
TTL_H = SC.TTL_HOURS
SCOPE = SC.scope_of(None, TOP_K, PROMPT_V)
assert TTL_H == 24 and "prompt" in src("services/rag-api/semantic_cache.py").split("def scope_of", 1)[1].split("def _alive", 1)[0]


def ctx_stale(db, fp_packed: str) -> str | None:
    """cache_manager's stale_against() for a record packed under fp_packed, against the stand-in ledger."""
    mgr = types.SimpleNamespace(db=db)
    mgr.ledger_fingerprint = types.MethodType(_ns["ledger_fingerprint"], mgr)
    return _ns["stale_against"](mgr, {"corpus_fingerprint": fp_packed}, "acme")


def ans_alive(db, fp_stored: str) -> bool:
    """semantic_cache._alive() for an entry stored under fp_stored, inside its day, read against the stand-in ledger."""
    now_fp = ((db.docs.get(("ledger", "acme")) or {}).get("fingerprint") or "")
    return SC._alive({"fingerprint": fp_stored, "scope": SCOPE, "expire_at": NOW + timedelta(hours=TTL_H)}, now_fp, SCOPE, NOW)


# ================================================================== the corpus: acme's objects as evals/upload.sh sends them
UPLOAD = src("evals/upload.sh")
assert 'if [[ "${f}" == *.md && ( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" ) ]]; then' in UPLOAD
assert 'if [[ "${f}" == *.segments.json ]]; then' in UPLOAD
ACME_DIR = KIT / "evals" / "corpus" / "acme"
ACME_OBJECTS = sorted(p.name for p in ACME_DIR.iterdir() if p.is_file()
                      and not (p.suffix == ".md" and (p.with_suffix(".pdf").exists() or p.with_suffix(".mp4").exists()))
                      and not p.name.endswith(".segments.json"))
N_ACME = len(ACME_OBJECTS)
assert N_ACME == 21 and "hr_policy_2026.md" in ACME_OBJECTS, ACME_OBJECTS
CTYPE = {".md": "text/markdown", ".pdf": "application/pdf", ".png": "image/png"}
BUCKET = f"{PROJ}-uploads"
HB = "acme/hr_policy_2026.md"
V1 = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_bytes()
V2 = (KIT / "evals/demo/hr_policy_2026_v2.md").read_bytes()
D1 = int(one(r"serves a notice period of (\d+) days", V1.decode("utf-8")))
D2 = int(one(r"serves a notice period of (\d+) days", V2.decode("utf-8")))
assert (D1, D2) == (60, 90)
GOLDEN = [json.loads(l) for l in src("evals/golden.jsonl").splitlines() if l.strip()]
LK06, VR01 = (next(r for r in GOLDEN if r["id"] == i) for i in ("lk-06", "vr-01"))
assert LK06["question"] == VR01["question"] == "What is the notice period for a confirmed E3?" and VR01["source"] == "hr_policy_2026.md"
assert "vr-01" in json.loads(src("evals/required.json"))["ids"]


def golden_pass(row: dict, figure: int | None) -> bool:
    """A golden row's own two lists against an answer that states this figure, or against no answer at all."""
    ans = f"The notice period is {figure} days." if figure else ""
    return (all(re.search(rf"(?<!\d){re.escape(w)}(?!\d)", ans) for w in row.get("must_contain", []))
            and not any(w in ans for w in row.get("must_not_contain", [])))


# a PDF of three hundred pages, built here, so the worker's own page count reads it
_pw = PdfWriter()
for _ in range(300):
    _pw.add_blank_page(width=72, height=72)
_buf = io.BytesIO()
_pw.write(_buf)
BIG = _buf.getvalue()
BIG_NAME = "acme/report_300_pages.pdf"


class Lane:
    """One lane's state on the stand-in store: the bucket's objects, the index's ids, BigQuery's rows, the managed
    stores' calls, the log events, and the kit's own functions doing every change, in the worker's order."""

    def __init__(self, region: str = "any"):
        self.db = Store()
        self.bucket, self.gen, self.index, self.bq, self.ops, self.events = {}, 1_000_000, set(), [], [], []
        rag, search = managed.RagEngineStore(PROJ), managed.VertexSearchStore(PROJ)
        for s in (rag, search):                                  # the stores record instead of calling
            s.upsert = (lambda s: lambda t, k, u, text, meta: self.ops.append(("upsert", s.name, k)) or "ok")(s)
            s.delete = (lambda s: lambda t, k: self.ops.append(("delete", s.name, k)) or 1)(s)
        self.regions = {s.name: s.region for s in (rag, search)}
        self.mirror = managed.Mirror(self.db, [rag, search], DEFAULTS["MANAGED_MIRROR"],
                                     policy_for=lambda t: tenancy.policy_for(t, self.db), audit=lambda *a, **k: None)
        self.db.collection("tenant_settings").document("acme").set({"data_region": region})
        for name in ACME_OBJECTS:                                # the rest of acme's corpus, as the ledger holds it
            if name == "hr_policy_2026.md":
                continue
            data = (ACME_DIR / name).read_bytes()
            g, key = self.upload(f"acme/{name}", data, CTYPE[Path(name).suffix]), f"acme_{contracts.sha256_of(data)}"
            self.db.collection("documents").document(key).set({"status": "indexed", "tenant_id": "acme", "generation": g,
                                                               "gcs_uri": f"gs://{BUCKET}/acme/{name}"})
            self.db.collection("sources").document(idem.source_id_for("acme", f"acme/{name}")).set(
                {"tenant_id": "acme", "name": f"acme/{name}", "gcs_uri": f"gs://{BUCKET}/acme/{name}", "doc_key": key,
                 "generation": g, "sha256": key.split("_", 1)[1], "status": "indexed"})
        self.deliver(HB, self.upload(HB, V1), V1, "text/markdown")

    def upload(self, name, data, ctype="text/markdown") -> str:
        self.gen += 1
        self.bucket[name] = (str(self.gen), data, ctype)
        return str(self.gen)

    def fp(self) -> str:
        return (self.db.docs.get(("ledger", "acme")) or {}).get("fingerprint", "")

    def versions(self) -> int:
        return (self.db.docs.get(("ledger", "acme")) or {}).get("versions", 0)

    def current_figure(self) -> int | None:
        """What NP-03 says among the handbook's current rows: the figure /v1/query would answer from, or None."""
        for p, d in self.db.docs.items():
            if p[0] == "chunks" and d.get("source_uri") == f"gs://{BUCKET}/{HB}" and d.get("current") is True and d.get("locator") == "NP-03":
                return int(one(r"notice period of (\d+) days", d["text"]))
        return None

    def deliver(self, name, generation, data, ctype):
        """push() and then index_document(): each step the kit's own function, in main.py's order (held above)."""
        tenant, uri = name.split("/", 1)[0], f"gs://{BUCKET}/{name}"
        try:
            contracts.IngestMessage.model_validate_json(json.dumps(
                {"bucket": BUCKET, "name": name, "size": len(data), "contentType": ctype, "generation": generation}))
        except Exception:  # noqa: BLE001 - pydantic's ValidationError: the worker's 400
            self.events.append("ingest_poison")
            return {"status": 400}
        older = idem.stale_generation(self.db, tenant, name, generation)
        if older:
            self.events.append("ingest_stale_event")
            return {"status": "stale", "ledger": older}
        doc = contracts.DocumentContract(tenant_id=tenant, sha256=contracts.sha256_of(data), gcs_uri=uri, pages=0)
        if not idem.claim(self.db, doc.doc_key, uri, tenant):
            st = idem.status_of(self.db, doc.doc_key)
            if st == "superseded":
                if idem.withdrawn(self.db, tenant, uri):
                    self.events.append("ingest_withdrawn")
                    return {"status": "withdrawn"}
                back = idem.reactivate(self.db, tenant, uri, doc.doc_key)
                if back is not None:
                    up = [s.id for s in self.db.collection("chunks").where("tenant_id", "==", tenant).where("source_uri", "==", uri)
                          .where("current", "==", True).stream() if (s.to_dict() or {}).get("doc_key") == doc.doc_key]
                    self.index.update(up)                                         # reupsert(): the same query, the same ids
                    gone = idem.retire_previous(self.db, tenant, uri, doc.doc_key, expire_at=NOW + timedelta(days=RETENTION))
                    self.index.difference_update(gone["retired_ids"])
                    self.mirror.after_undo(tenant, uri, doc.doc_key, gone, {"generation": generation, "name": name})
                    idem.record_source(self.db, tenant, name, uri, doc.doc_key, generation, doc.sha256, back,
                                       contracts.effective_from_of(name, None), reused=back, embedded=0,
                                       retired=gone["retired_chunks"], embedding_model=IX["EMBEDDING_MODEL"],
                                       embedding_version=IX["EMBEDDING_VERSION"])
                    idem.refresh_fingerprint(self.db, tenant, "ingest_reactivated")
                    self.events.append("ingest_reactivated")
                    return {"status": "reactivated", "chunks": back, "retired": gone["retired_chunks"], "upserted": len(up)}
                if not idem.claim(self.db, doc.doc_key, uri, tenant, retake=True):
                    return {"status": "duplicate"}
            elif st == "processing":                                  # the lease: held is a 409, run out is taken back
                lease = idem.retake_expired(self.db, doc.doc_key, uri, tenant)
                self.events.append("ingest_claim_" + lease["verdict"])
                if lease["verdict"] == "held" and lease["lane"] == "batch":
                    return {"status": "batch_processing"}
                if lease["verdict"] != "retaken":
                    return {"status": 409}
            elif st == "queued":
                return {"status": "queued_batch"}
            else:
                return {"status": "duplicate"}
        if idem.current_chunks(self.db, tenant, uri, doc.doc_key, IX["EMBEDDING_MODEL"], IX["EMBEDDING_VERSION"]):
            return {"status": "already_current"}
        return self.index_document(doc, name, generation, data, ctype)

    def index_document(self, doc, name, generation, data, ctype):
        doc = doc_types.assign(self.db, doc, name)
        pages = W["_pdf_pages"](data) if ctype == "application/pdf" else None
        if pages is not None and pages > W["MAX_INLINE_PAGES"]:                # _enqueue_batch()'s two writes
            self.db.collection("ingest_batch").document(doc.doc_key).set({"tenant_id": doc.tenant_id, "status": "queued",
                                                                          "pages": pages, "generation": generation})
            self.db.collection("documents").document(doc.doc_key).set({"status": "queued", "pages": pages,
                                                                        "generation": generation}, merge=True)
            self.events.append("ingest_queued_batch")
            return {"status": "queued_batch", "pages": pages}
        text = data.decode("utf-8", "replace")
        chunks = W["_chunk"](text)
        held = IX["held_vectors"](self.db, doc)
        vectors, misses = IX["plan_carry_over"](chunks, held)
        for i in misses:
            vectors[i] = [0.5] * DIMS                                          # a stand-in for embed_all()'s answer
        counts = {"reused": len(chunks) - len(misses), "embedded": len(misses)}
        IX["mirror_to_firestore"](self.db, doc, chunks, vectors, staged=True, stage_expire_at=NOW + timedelta(hours=STAGE_HOURS))
        gone = idem.swap_versions(self.db, doc.tenant_id, doc.gcs_uri, doc.doc_key, expire_at=NOW + timedelta(days=RETENTION),
                                  effective_to=doc.effective_from)
        self.index.update(doc.chunk_id(i) for i in range(len(chunks)))
        self.index.difference_update(gone["retired_ids"])
        self.mirror.after_swap(doc, text, gone, {"generation": generation, "name": name})
        self.bq.extend(doc.chunk_id(i) for i in range(len(chunks)))
        idem.finish(self.db, doc.doc_key, len(chunks), counts, generation)
        idem.record_source(self.db, doc.tenant_id, name, doc.gcs_uri, doc.doc_key, generation, doc.sha256, len(chunks),
                           doc.effective_from, reused=counts["reused"], embedded=counts["embedded"],
                           retired=gone["retired_chunks"], embedding_model=IX["EMBEDDING_MODEL"],
                           embedding_version=IX["EMBEDDING_VERSION"])
        idem.refresh_fingerprint(self.db, doc.tenant_id, "ingest_ok")
        if gone["retired_chunks"]:
            self.events.append("ingest_superseded")
        self.events.append("ingest_ok")
        return {"status": "indexed", "chunks": len(chunks), **counts, "retired": gone["retired_chunks"],
                "activated": gone["activated"], "misses": [chunks[i]["locator"] for i in misses],
                "chars": sum(len(chunks[i]["text"]) for i in misses), "doc_type": doc.doc_type}

    def retire_by_hand(self, name):
        """make retire SOURCE=: reconcile.py --retire's branch, in its order (held above)."""
        uri = f"gs://{BUCKET}/{name}"
        gone = idem.retire_previous(self.db, "acme", uri, None, expire_at=NOW + timedelta(days=RETENTION))
        self.mirror.retired("acme", gone.get("retired_doc_keys", []), "withdrawn")
        self.db.collection("sources").document(idem.source_id_for("acme", name)).set({"status": "withdrawn", "withdrawn_at": TS}, merge=True)
        self.unindex(gone)
        idem.refresh_fingerprint(self.db, "acme", "reconcile_withdrawn")
        return gone

    def unindex(self, gone: dict) -> int:
        """reconcile.remove_vectors() over the lane's index: the retired ids out, as VECTOR_INDEX_NAME names it on a lane."""
        return reconcile.remove_vectors("projects/NUMBER/locations/REGION/indexes/ID", gone,
                                        remove=lambda name, ids: self.index.difference_update(ids))

    def night(self):
        """The nightly walk: reconcile.plan() over the bucket, the ledger and the claims, decide_bytes() for each byte
        check, then main()'s apply branch, each action by the kit's functions. Returns the summary and the drift."""
        objects = [{"name": n, "generation": g, "tenant_id": n.split("/", 1)[0]} for n, (g, _, _) in self.bucket.items()]
        ledger = {p[1]: dict(d) for p, d in self.db.docs.items() if p[0] == "sources" and len(p) == 2}
        documents = {p[1]: dict(d) for p, d in self.db.docs.items() if p[0] == "documents" and len(p) == 2}
        summary = {"retire": 0, "reingest": 0, "backfill": 0, "touch": 0, "ok": 0, "withdrawn": 0, "queued": 0}
        touched, acts = set(), reconcile.plan(objects, ledger, documents)
        for act in acts:
            if act["action"] == "check_bytes":
                act["action"] = reconcile.decide_bytes(contracts.sha256_of(self.bucket[act["name"]][1]), act["tenant_id"],
                                                       ledger.get(reconcile.source_id_for(act["tenant_id"], act["name"])), documents)
            summary[act["action"]] += 1
            if act["action"] == "retire":
                gone = idem.retire_previous(self.db, act["tenant_id"], act["gcs_uri"], None, expire_at=NOW + timedelta(days=RETENTION))
                self.mirror.retired(act["tenant_id"], gone.get("retired_doc_keys", []), "retired")
                self.db.collection("sources").document(reconcile.source_id_for(act["tenant_id"], act["name"])).set(
                    {"status": "retired", "retired_at": TS}, merge=True)
                self.unindex(gone)
                touched.add(act["tenant_id"])
                act["retired"] = gone["retired_chunks"]
            elif act["action"] == "touch":
                self.db.collection("sources").document(reconcile.source_id_for(act["tenant_id"], act["name"])).set(
                    {"generation": act["generation"]}, merge=True)
            elif act["action"] == "reingest":                                  # a rewrite onto itself: a new generation
                g, data, ctype = self.bucket[act["name"]]
                act["result"] = self.deliver(act["name"], self.upload(act["name"], data, ctype), data, ctype)
        for t in sorted(touched):
            idem.refresh_fingerprint(self.db, t, "reconcile")
        return {"summary": summary, "drift": reconcile.drift_of(summary), "acts": acts}


def pick(lane: Lane, name: str) -> list:
    """The index's ids of one object's versions: what Vector Search still holds for it."""
    keys = {d.get("doc_key") for p, d in lane.db.docs.items() if p[0] == "chunks" and d.get("source_uri") == f"gs://{BUCKET}/{name}"}
    return [i for i in lane.index if i.split("#")[0].replace(":", "_", 1) in keys]


# ================================================================== the nine changes, each run on a fresh lane
ALERTS = src("terraform/alerts.tf")
COUNTED = one(r'jsonPayload\.event=~"\^ingest_\(([a-z_|]+)\)\$"', ALERTS).split("|")
assert COUNTED == ["ok", "superseded", "reactivated", "stale_event", "failed", "queued_batch", "poison", "withdrawn",
                   "already_current", "claim_retaken"], COUNTED                   # every verdict but a refused delivery, 13 October 2026
counted = lambda ev: ev.startswith("ingest_") and ev[len("ingest_"):] in COUNTED  # noqa: E731
policy_field = lambda name, field: int(one(rf'resource "google_monitoring_alert_policy" "{name}" \{{.*?{field}\s+=\s+"(\d+)s"',  # noqa: E731
                                           ALERTS, re.S))
policy_name = lambda name: one(rf'resource "google_monitoring_alert_policy" "{name}" \{{\s*(?:count\s+= [^\n]+\s*)?display_name = "([^"]+)"', ALERTS)  # noqa: E731
DISPLAY_FAILED, DISPLAY_DLQ, DISPLAY_DRIFT, DISPLAY_BACKLOG = (policy_name(n) for n in ("ingest_failed", "dlq_depth", "reconcile_drift",
                                                                                         "ingest_backlog"))
assert (DISPLAY_FAILED, DISPLAY_DLQ, DISPLAY_DRIFT) == ("Ingest failed", "Ingest dead-letter queue holds messages",
                                                        "Ledger drift above zero for two nights")
assert DISPLAY_BACKLOG == "Ingest subscription backlog: oldest message over 30 minutes", DISPLAY_BACKLOG
BACKLOG_S = int(one(r'resource "google_monitoring_alert_policy" "ingest_backlog" \{.*?threshold_value = (\d+)', ALERTS, re.S))
BACKLOG_FOR_S = policy_field("ingest_backlog", "duration")
assert (BACKLOG_S, BACKLOG_FOR_S) == (1800, 300) and BACKLOG_S + BACKLOG_FOR_S > LEASE_S + rs.MAX_BACKOFF + rs.ACK_DEADLINE
DESK_ALERTS = src("terraform/desk_alerts.tf")
DISPLAY_PIN = one(r'resource "google_monitoring_alert_policy" "doc_type_pin_miss" \{\s*display_name = "([^"]+)"', DESK_ALERTS)
PIN_MIN = int(one(r'resource "google_monitoring_alert_policy" "doc_type_pin_miss" \{.*?alignment_period\s+=\s+"(\d+)s"',
                  DESK_ALERTS, re.S)) // 60
assert (DISPLAY_PIN, PIN_MIN) == ("A registered document arrived at a version nobody reviewed", 10)
DLQ_FOR_S = policy_field("dlq_depth", "duration")
DRIFT_FOR_H = policy_field("reconcile_drift", "duration") // 3600
FAIL_WINDOW_MIN = policy_field("ingest_failed", "alignment_period") // 60
assert (DLQ_FOR_S, DRIFT_FOR_H, FAIL_WINDOW_MIN) == (60, 24, 10)
WALK_DOC = RECON.split('"""', 2)[1]
assert "a new generation fires the same finalize\nevent the worker already handles, so there is one ingestion path, not two" in WALK_DOC

BASE = Lane()                                                           # the lane before any change: the kit's acme corpus
FP0, VERSIONS = BASE.fp(), BASE.versions()
assert VERSIONS == N_ACME and len(BASE.index) == 283 and BASE.current_figure() == D1
N_HB = len(BASE.index)
DK1, DK2 = (f"acme_{contracts.sha256_of(b)}" for b in (V1, V2))


def run(scn: str, walk: bool, batch: bool, cache: bool, region: str) -> dict:
    """One change on a fresh lane; everything the panel prints about it. The batch job and the answer cache change
    only the words: the job's Document AI pass is not run here, and both caches' tests are run whatever the switch."""
    lane = Lane(region)
    g1 = lane.bucket[HB][0]                                             # version 1's generation, as the bucket numbered it
    pre = {"fp": lane.fp(), "fig": lane.current_figure(), "gen": g1}
    if scn in ("undo", "late"):                                         # these start from revision 2, live
        lane.deliver(HB, lane.upload(HB, V2), V2, "text/markdown")
        pre = {"fp": lane.fp(), "fig": lane.current_figure(), "gen": lane.bucket[HB][0], "g1": g1}
    lane.events, lane.ops = [], []
    w0, rd0, bq0, idx0 = lane.db.writes, lane.db.reads, len(lane.bq), set(lane.index)
    res = {}
    if scn == "edit":
        res = lane.deliver(HB, lane.upload(HB, V2), V2, "text/markdown")
    elif scn == "undo":
        res = lane.deliver(HB, lane.upload(HB, V1), V1, "text/markdown")
    elif scn == "same":
        res = lane.deliver(HB, lane.upload(HB, V1), V1, "text/markdown")
    elif scn == "late":
        res = lane.deliver(HB, pre["g1"], V1, "text/markdown")
    elif scn == "deleted":
        del lane.bucket[HB]
        res = {"status": "no event"}
    elif scn == "withdrawn":
        res = lane.retire_by_hand(HB)
    elif scn == "big":
        res = lane.deliver(BIG_NAME, lane.upload(BIG_NAME, BIG, "application/pdf"), BIG, "application/pdf")
    elif scn == "poison":
        res = lane.deliver("acme/poison.pdf", lane.upload("acme/poison.pdf", b"", "application/pdf"), b"", "application/pdf")
    elif scn == "chunker":
        res = {"status": "no event"}
    out = {"res": res, "pre": pre, "events": list(lane.events), "ops": list(lane.ops), "writes": lane.db.writes - w0,
           "reads": lane.db.reads - rd0, "bq_new": len(lane.bq) - bq0, "bq_total": len(lane.bq), "up": len(lane.index - idx0),
           "out": len(idx0 - lane.index), "fp": lane.fp(), "fig": lane.current_figure(), "kept": len(pick(lane, HB)),
           "ledger": (lane.db.docs.get(("sources", idem.source_id_for("acme", HB))) or {}).get("status"),
           "ctx_stale": ctx_stale(lane.db, pre["fp"]), "ans_alive": ans_alive(lane.db, pre["fp"]), "walk": None}
    if walk:
        n_ops, idx_w = len(lane.ops), set(lane.index)
        n1 = lane.night()
        out["walk"] = {"n1": n1, "fp": lane.fp(), "fig": lane.current_figure(), "kept": len(pick(lane, HB)), "ops": lane.ops[n_ops:],
                       "out": len(idx_w - lane.index),
                       "ledger": (lane.db.docs.get(("sources", idem.source_id_for("acme", HB))) or {}).get("status"),
                       "ctx_stale": ctx_stale(lane.db, pre["fp"]), "ans_alive": ans_alive(lane.db, pre["fp"]),
                       "events": list(lane.events)}
        out["walk"]["n2"] = lane.night()
    return out


SWITCHES = [("walk", (False, True)), ("batch", (False, True)), ("cache", (False, True)), ("region", ("any", "in"))]
COMBOS = [dict(zip([k for k, _ in SWITCHES], vals)) for vals in
          [(w, b, c, r) for w in (False, True) for b in (False, True) for c in (False, True) for r in ("any", "in")]]
SCENARIOS = [
    ("edit", "A clause edited: revision 2 of the handbook, under the same name"),
    ("undo", "The edit undone: version 1's bytes again, inside the window"),
    ("same", "The same bytes uploaded again"),
    ("late", "A late event: version 1's delivery arrives after revision 2"),
    ("deleted", "The handbook deleted from the bucket"),
    ("withdrawn", "The handbook withdrawn by a person: make retire"),
    ("big", "A new PDF of 300 pages"),
    ("poison", "A zero-byte object: make poison"),
    ("chunker", "The chunker changed to 400 characters; no document changed"),
]
RUNS = {(s, i): run(s, **c) for s, _ in SCENARIOS for i, c in enumerate(COMBOS)}
DEF = 0                                                                 # COMBOS[0]: the kit's defaults, acme's policy
assert COMBOS[DEF] == {"walk": False, "batch": False, "cache": False, "region": "any"}

# ------------------------------------------------------------------ the facts the panel and the prose rest on, held
E = RUNS[("edit", DEF)]
ER = E["res"]
assert ER["status"] == "indexed" and (ER["chunks"], ER["reused"], ER["embedded"], ER["retired"], ER["activated"]) == (283, 281, 2, 283, 283)
assert ER["misses"] == ["preamble", "NP-03"] and E["up"] == 283 and E["out"] == 283 and E["bq_new"] == 283 and E["bq_total"] == 566
assert E["events"] == ["ingest_superseded", "ingest_ok"], E["events"]
assert sorted(E["ops"]) == sorted([("upsert", "rag_engine", DK2), ("upsert", "vertex_search", DK2),
                                   ("delete", "rag_engine", DK1), ("delete", "vertex_search", DK1)]), E["ops"]
EDIT_IN = RUNS[("edit", COMBOS.index({"walk": False, "batch": False, "cache": False, "region": "in"}))]
assert sorted(EDIT_IN["ops"]) == sorted([("delete", "rag_engine", DK1), ("delete", "vertex_search", DK1)]), EDIT_IN["ops"]
assert ER["doc_type"] == "unknown" and E["fig"] == D2 and E["pre"]["fig"] == D1
FP2, CHARS = E["fp"], ER["chars"]
assert FP2 != FP0 and E["ctx_stale"] == FP2 and E["ans_alive"] is False
assert golden_pass(LK06, D1) and golden_pass(VR01, D1) and not golden_pass(LK06, D2) and not golden_pass(VR01, D2)
assert not golden_pass(LK06, None) and not golden_pass(VR01, None)
EDIT_WRITES, EDIT_READS = E["writes"], E["reads"]
U = RUNS[("undo", DEF)]
assert U["res"]["status"] == "reactivated" and (U["res"]["chunks"], U["res"]["retired"], U["res"]["upserted"]) == (283, 283, 283)
assert U["fp"] == FP0 and U["pre"]["fp"] == FP2 and U["fig"] == D1 and U["events"] == ["ingest_reactivated"]
assert ctx_stale(Lane().db, FP0) is None                               # a pack made under version 1, before the edit
S = RUNS[("same", DEF)]
assert S["res"]["status"] == "duplicate" and S["fp"] == FP0 and S["events"] == [] and S["writes"] == 0
assert any('"event":"ingest_duplicate"' in l for l in LOG)
L = RUNS[("late", DEF)]
assert L["res"]["status"] == "stale" and L["events"] == ["ingest_stale_event"] and L["fp"] == FP2 and L["writes"] == 0
DL = RUNS[("deleted", DEF)]
assert DL["fp"] == FP0 and DL["fig"] == D1 and DL["ledger"] == "indexed" and DL["kept"] == 283
DLW = RUNS[("deleted", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert DLW["n1"]["summary"]["retire"] == 1 and DLW["n1"]["drift"] == 1 and DLW["n2"]["drift"] == 0
assert DLW["ledger"] == "retired" and DLW["fig"] is None and DLW["kept"] == 0 and DLW["out"] == 283 and DLW["fp"] not in (FP0, FP2)
WD = RUNS[("withdrawn", DEF)]
assert WD["res"]["retired_chunks"] == 283 and WD["ledger"] == "withdrawn" and WD["fig"] is None and WD["kept"] == 0 and WD["out"] == 283
assert WD["res"]["datapoints_removed"] == 283 and RUNS[("deleted", DEF)]["kept"] == 283     # no walk: the deleted one's stay
assert WD["fp"] == DLW["fp"]                                            # the same current set, by either road
WDW = RUNS[("withdrawn", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert WDW["n1"]["summary"]["withdrawn"] == 1 and WDW["n1"]["drift"] == 0
B = RUNS[("big", DEF)]
assert B["res"] == {"status": "queued_batch", "pages": 300} and B["events"] == ["ingest_queued_batch"] and B["fp"] == FP0
BW = RUNS[("big", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert BW["n1"]["summary"]["queued"] == 1 and BW["n1"]["drift"] == 0 and BW["n2"]["drift"] == 0
P = RUNS[("poison", DEF)]
assert P["res"] == {"status": 400} and P["events"] == ["ingest_poison"] and counted("ingest_poison")
PW = RUNS[("poison", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert PW["n1"]["summary"]["reingest"] == 1 and PW["n1"]["drift"] == 1 and PW["n2"]["drift"] == 1
assert PW["events"].count("ingest_poison") == 2                         # the upload, and the walk's rewrite of it
SW = RUNS[("same", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert SW["n1"]["summary"]["touch"] == 1 and SW["n1"]["drift"] == 0
EW = RUNS[("edit", COMBOS.index({"walk": True, "batch": False, "cache": False, "region": "any"}))]["walk"]
assert EW["n1"]["drift"] == 0 and EW["n1"]["summary"]["ok"] == N_ACME
CH = RUNS[("chunker", DEF)]
assert CH["events"] == [] and CH["fp"] == FP0 and CH["writes"] == 0
assert counted("ingest_queued_batch") and not counted("ingest_duplicate") and counted("ingest_stale_event")
assert counted("ingest_claim_retaken") and not counted("ingest_claim_held") and not counted("ingest_claim_moved")

# a worker cut off between claim and finish: a delivery inside the lease is a 409, one after it takes the claim back
_cut = Lane()
_cut.db.collection("documents").document(DK2).set({"status": "processing", "tenant_id": "acme", "gcs_uri": f"gs://{BUCKET}/{HB}",
                                                    "claimed_at": datetime.now(timezone.utc) - timedelta(seconds=LEASE_S // 2)})
_g2, _cut.events = _cut.upload(HB, V2), []
CUT_HELD = _cut.deliver(HB, _g2, V2, "text/markdown")
_cut.db.docs[("documents", DK2)]["claimed_at"] = datetime.now(timezone.utc) - timedelta(seconds=LEASE_S + 1)
CUT_TAKEN = _cut.deliver(HB, _g2, V2, "text/markdown")
assert CUT_HELD == {"status": 409} and CUT_TAKEN["status"] == "indexed" and _cut.current_figure() == D2, (CUT_HELD, CUT_TAKEN)
assert _cut.events == ["ingest_claim_held", "ingest_claim_retaken", "ingest_superseded", "ingest_ok"], _cut.events
assert DEFAULTS["MANAGED_MIRROR"] == "both" and {k: v for k, v in BASE.regions.items()} == {"rag_engine": "us-central1", "vertex_search": "global"}

# the undo after the window: the same upload, its claim retired one day past RETENTION_DAYS
_late = Lane()
_late.deliver(HB, _late.upload(HB, V2), V2, "text/markdown")
_late.db.collection("documents").document(DK1).set({"retired_at": NOW - timedelta(days=RETENTION + 1)}, merge=True)
LOG.clear()
LATE_UNDO = _late.deliver(HB, _late.upload(HB, V1), V1, "text/markdown")
assert LATE_UNDO["status"] == "indexed" and LATE_UNDO["embedded"] == 2 and LATE_UNDO["reused"] == 281, LATE_UNDO
_inc = [json.loads(l) for l in LOG if "reactivate_incomplete" in l]
assert _inc and _inc[0]["age_days"] == RETENTION + 1 and _inc[0]["retention_days"] == RETENTION, _inc

# a name make doc-types registered and pinned to version 1: the hook's verdict on revision 2
_reg = Lane()
doc_types.set_class(_reg.db, "acme", HB, "policy", DK1, "operator", "operator")
LOG.clear()
_rr = _reg.deliver(HB, _reg.upload(HB, V2), V2, "text/markdown")
assert _rr["doc_type"] == "unknown" and any('"doc_type_pin_miss"' in l for l in LOG)

# the chunker at 400 / 50: revision 2 cut by the new rule, against version 1's rows
W400 = dict(W)
exec("CHUNK_CHARS, CHUNK_OVERLAP = 400, 50", W400)
for _n in ast.parse(WORKER).body:
    if isinstance(_n, ast.FunctionDef) and _n.name in ("_windows", "_chunk"):
        exec(ast.get_source_segment(WORKER, _n), W400)
_c400 = W400["_chunk"](V2.decode("utf-8"))
_h1 = {c["chunk_hash"] for c in W["_chunk"](V1.decode("utf-8"))}
N400, R400 = len(_c400), sum(c["chunk_hash"] in _h1 for c in _c400)
assert (N400, R400) == (555, 9), (N400, R400)

# whole-document windows, the kit's own record: the same two texts, cut without sections
_w1, _w2 = ([p for _, p in W["_windows"](b.decode("utf-8"))] for b in (V1, V2))
_wh = {contracts.chunk_hash(p) for p in _w1}
WIN_N, WIN_REUSED, WIN_CHARS = len(_w2), sum(contracts.chunk_hash(p) in _wh for p in _w2), sum(len(p) for p in _w2)
assert (len(_w1), WIN_N, WIN_REUSED) == (92, 92, 0) and CHARS == 453, (len(_w1), WIN_N, WIN_REUSED, CHARS)
assert "reused none of its 92 windows. By section it reuses 281 of 283." in flat(WORKER.split("# A handbook's sections", 1)[1][:600].replace("# ", ""))

# ================================================================== the panel's text, from the runs
ST = [("event", "1 &middot; The event", "terraform/eventarc.tf"),
      ("guard", "2 &middot; Guard and claim", "idempotency.py: stale_generation, claim"),
      ("parse", "3 &middot; Parse and chunk", "main.py: _parse, _chunk"),
      ("carry", "4 &middot; The carry-over", "indexer.py: embed_with_carry_over"),
      ("swap", "5 &middot; Stage and swap", "idempotency.py: swap_versions"),
      ("ann", "6 &middot; Vector Search", "indexer.py: upsert, remove_datapoints"),
      ("mirror", "7 &middot; The managed stores", "managed.py: Mirror"),
      ("bq", "8 &middot; BigQuery", "indexer.py: mirror_to_bigquery"),
      ("ledger", "9 &middot; The ledger", "idempotency.py: finish, record_source"),
      ("fp", "10 &middot; The fingerprint", "idempotency.py: refresh_fingerprint"),
      ("ctx", "11 &middot; The context cache", "cache_manager.py: stale_against"),
      ("ans", "12 &middot; The answer cache", "semantic_cache.py: _alive"),
      ("answer", "13 &middot; The answer", "retriever.py, golden.jsonl"),
      ("pager", "14 &middot; Trail and pager", "terraform/alerts.tf"),
      ("walk", "15 &middot; The nightly walk", "reconcile.py, reconcile.tf")]
N_ST = len(ST)
WIN = f"{RETENTION} days"
CNT = "documind/ingest_events"
RS_EMBED = rs.inr(CHARS / 1000 * rs.EMBED_USD_1K["online"])


def mirror_line(ops: list, region: str, fn: str, new: str | None, old: str) -> tuple:
    """The managed stores' station, from the calls the kit's Mirror actually made on the two recording stores."""
    ups = sum(1 for o in ops if o[0] == "upsert")
    dels = sum(1 for o in ops if o[0] == "delete")
    where = (f"the RAG Engine corpus ({BASE.regions['rag_engine']}) and the Vertex AI Search data store "
             f"({BASE.regions['vertex_search']})")
    if ups:
        return ("run", f"data_region {region}, so {fn} copies {new} into {where}" + (f", and deletes {old} from both." if dels else "."),
                f"{ups} upserts, {dels} deletes")
    if dels and new and region == "in":
        return ("stop", f"data_region in: mirror_policy_skipped, so {new} stays on the kit's rows. {fn} still sends {old}'s delete to "
                        "both stores: a delete is never refused.", f"0 upserts, {dels} deletes")
    if dels:
        return ("run", f"{fn} deletes {old} from {where}" + ("." if region == "any" else
                                                             ", which never held it: a delete is never refused."),
                f"0 upserts, {dels} deletes")
    return ("skip", "No call.", "")


def stations(scn: str, combo: dict) -> tuple:
    """The fifteen stations and the one-line outcome for one change under one set of switches."""
    r = RUNS[(scn, COMBOS.index(combo))]
    walk, batch, cache, region = combo["walk"], combo["batch"], combo["cache"], combo["region"]
    res, pre, wk = r["res"], r["pre"], r["walk"]
    s = {}
    skip = lambda t="Not reached.": ("skip", t, "")  # noqa: E731
    walk_off = ("skip", f"RECONCILE_JOB ?= {DEFAULTS['RECONCILE_JOB']}: no job is declared, so nothing runs at {WALK_AT}. make reconcile "
                        "from a shell is the walk.", "off by default")
    ans_off = ("skip", f"SEMANTIC_CACHE ?= {DEFAULTS['SEMANTIC_CACHE']}: no answer is stored and none is served.", "off by default")
    if scn == "edit":
        s["event"] = ("run", f"OBJECT_FINALIZE for the object's new generation: {TOPIC}, then {SUB_NAME}, which delivers it to the "
                             f"worker with an OIDC token. One document per instance, {rs.IN_FLIGHT} at most, {rs.ACK_DEADLINE} s to answer.",
                      f"{rs.MAX_ATTEMPTS} deliveries, then the DLQ")
        s["guard"] = ("run", "The new generation is newer than the ledger's, so its bytes are fetched by generation. New bytes, a new "
                             "sha256, a new doc_key: the claim is won in a transaction.", "claim: processing")
        s["parse"] = ("run", f"Text, so no Document AI. Cut by section: {res['chunks']} chunks, the preamble and one per ## heading. One DLP "
                             "scan of all of them before anything is written. Class: unknown, as no registry names the file.",
                      f"{res['chunks']} chunks")
        s["carry"] = ("run", f"{res['reused']} vectors reused by chunk_hash; {res['embedded']} embedded, the {' and the '.join(res['misses'])} "
                             f"chunks: {CHARS:,} characters sent to {IX['EMBEDDING_MODEL']}.", f"Rs {RS_EMBED:.4f}")
        s["swap"] = ("run", f"{res['chunks']} rows written staged and invisible, then one pass: {res['activated']} flipped current, version 1's "
                            f"{res['retired']} retired (current false, expire_at in {WIN}). Nothing deleted.", f"{r['writes']} writes in all")
        s["ann"] = ("run", f"{r['up']} datapoints upserted under revision 2's ids and version 1's {r['out']} removed. The {res['reused']} reused "
                           "vectors go up again too: a chunk's id names its version.", f"{r['up']} up, {r['out']} out")
        s["mirror"] = mirror_line(r["ops"], region, "after_swap()", "revision 2's text", "version 1")
        s["bq"] = ("gap", f"{r['bq_new']} rows streamed into rag_data.chunk_source for revision 2. Version 1's {N_HB} stay: the table has no "
                          "current column, and nothing retires them.", f"{r['bq_total']} rows for one document")
        s["ledger"] = ("run", f"documents/: revision 2 indexed with chunks {res['chunks']}, reused {res['reused']}, embedded {res['embedded']}; "
                              "version 1 superseded, its retired_at stamped. sources/: revision 2's doc_key and generation.",
                       f"the {RETENTION}-day undo window opens")
        s["fp"] = ("run", f"ledger/acme re-hashed from its {VERSIONS} indexed sources: {short(pre['fp'])} becomes {short(r['fp'])}, "
                          "the value both caches now compare with.", f"{VERSIONS} rows read")
        s["ctx"] = ("held", f"A pack made under {short(pre['fp'])} is stale against the ledger: cache_stale, and answers run uncached until "
                            "make cache packs again.", "nothing alerts on cache_stale")
        s["ans"] = (("run", f"Every entry stored under {short(pre['fp'])} fails _alive(): answered under an older corpus. New answers are "
                            f"stored under the new one.", "misses, by design") if cache else ans_off)
        s["answer"] = ("run", f"NP-03 now says {r['fig']} days, and prefer_current() drops version 1's rows. lk-06 and vr-01 fail live until "
                              "they move with the document.", f"{pre['fig']} days becomes {r['fig']}")
        s["pager"] = ("run", f"ingest_superseded and ingest_ok, counted by {CNT}; embedded and reused land in their two distributions. "
                             "Nothing pages on a default lane. Where make doc-types pinned the handbook to version 1 (lesson 10.4), "
                             f"revision 2 is unreviewed: its class is unknown, and \"{DISPLAY_PIN}\" pages within {PIN_MIN} minutes.",
                      "0 pages, or 1 with a registry")
        s["walk"] = (("run", f"{WALK_AT}: the object's generation equals the ledger's for all {wk['n1']['summary']['ok']} of acme's objects: "
                             f"drift {wk['n1']['drift']}.", "nothing to repair") if walk else walk_off)
        out = (f"Revision 2 is live after one swap: {res['embedded']} of {res['chunks']} chunks embedded and {res['retired']} retired for {WIN}. "
               "The fingerprint moved, so neither cache serves version 1, and nothing paged. BigQuery now holds both versions.")
    elif scn == "undo":
        s["event"] = ("run", "OBJECT_FINALIZE for a new generation carrying version 1's bytes, delivered like any upload.", "")
        s["guard"] = ("run", "Newer than the ledger's generation; version 1's doc_key, whose claim says superseded: the undo. Not "
                             f"withdrawn; reactivate() counts {res['chunks']} rows against the claim's {res['chunks']} and the retire "
                             f"stamp against {WIN}, then flips.", "verified before it flips")
        s["parse"] = skip("Nothing parsed: the rows are still here.")
        s["carry"] = ("skip", f"Nothing embedded: {res['chunks']} rows come back as they were. Past the window the same upload is "
                              f"reactivate_incomplete and a fresh version, and the carry-over embeds {LATE_UNDO['embedded']}.", "0 embedded")
        s["swap"] = ("run", f"Version 1's {res['chunks']} rows flipped current, their stamps cleared; then revision 2's {res['retired']} "
                            f"retired, expire_at in {WIN}.", f"{r['writes']} writes")
        s["ann"] = ("run", f"reupsert(): version 1's {res['upserted']} ids go back up from the rows' own vectors before revision 2's "
                           f"{r['out']} come out, so the tier is never empty.", f"{r['up']} up, {r['out']} out")
        s["mirror"] = mirror_line(r["ops"], region, "after_undo()", "version 1's text", "revision 2")
        s["bq"] = ("skip", f"Nothing streamed: BigQuery has held both versions' rows since the edit, {r['bq_total']} of them.", "")
        s["ledger"] = ("run", f"documents/: version 1 indexed again, revision 2 superseded. sources/: version 1's doc_key, reused "
                              f"{res['chunks']}, embedded 0.", "")
        s["fp"] = ("run", f"{short(pre['fp'])} becomes {short(r['fp'])} again: the hash of the current doc_keys, so the old corpus brings back "
                          "its old fingerprint.", "the fingerprint names a corpus")
        s["ctx"] = ("run", f"A pack made under {short(r['fp'])} before the edit is current again; one made under {short(pre['fp'])} goes stale.", "")
        s["ans"] = (("run", f"Entries stored under {short(r['fp'])} that are still inside their {TTL_H} hours are alive again: the old answer "
                            f"comes back. Entries under {short(pre['fp'])} miss.", "lesson 6.3") if cache else ans_off)
        s["answer"] = ("run", f"NP-03 says {r['fig']} days again; lk-06 and vr-01 pass.", f"{pre['fig']} days becomes {r['fig']}")
        s["pager"] = ("run", f"ingest_reactivated, counted by {CNT}. Nothing pages.", "0 pages")
        s["walk"] = (("run", f"{WALK_AT}: every generation matches the ledger's. Drift {wk['n1']['drift']}.", "") if walk else walk_off)
        out = (f"Version 1 is back for nothing: {res['chunks']} rows flipped, none embedded. The old fingerprint returned, so a cached "
               "answer from before the edit is right again.")
    elif scn == "same":
        s["event"] = ("run", "OBJECT_FINALIZE for a new generation whose bytes are version 1's, the version already current.", "")
        s["guard"] = ("stop", "Newer than the ledger's generation, so the bytes are fetched. Same sha256, same doc_key, and its claim "
                              "says indexed: claim() refuses, push() answers duplicate, and the 200 acks it.", "ingest_duplicate")
        for k in ("parse", "carry", "swap", "ann", "mirror", "bq"):
            s[k] = skip()
        s["ledger"] = ("held", "Nothing written: the ledger keeps the old generation, which only a walk records.", "")
        s["fp"] = ("skip", f"Unchanged at {short(r['fp'])}: nothing current changed.", "")
        s["ctx"] = ("skip", "Attached as before.", "")
        s["ans"] = (("skip", "Entries alive as before.", "") if cache else ans_off)
        s["answer"] = ("skip", f"Unchanged: {r['fig']} days.", "")
        s["pager"] = ("stop", f"ingest_duplicate is a delivery the claim turned away, and {CNT} does not count it. Nothing pages.", "0 pages")
        s["walk"] = (("run", f"{WALK_AT}: the object's generation is newer than the ledger's, so its bytes are hashed: the same sha256, a "
                             f"touch. The generation is recorded; drift {wk['n1']['drift']}.", "a touch is not drift") if walk else
                     ("skip", f"RECONCILE_JOB ?= {DEFAULTS['RECONCILE_JOB']}: the ledger keeps the old generation until a walk records it.", "off by default"))
        out = "Acked as a duplicate. Nothing changed but the generation, and only a walk records that."
    elif scn == "late":
        s["event"] = ("run", "A redelivery of version 1's generation arrives after revision 2 is live: push delivery is at-least-once "
                             "and not in order.", "")
        s["guard"] = ("stop", "stale_generation(): the event's generation is older than the ledger's. Acked as ingest_stale_event, "
                              "with nothing downloaded.", "the generation guard")
        for k in ("parse", "carry", "swap", "ann", "mirror", "bq", "ledger"):
            s[k] = skip()
        s["fp"] = ("skip", f"Unchanged at {short(r['fp'])}: nothing current changed.", "")
        s["ctx"] = ("skip", "As before.", "")
        s["ans"] = (("skip", "As before.", "") if cache else ans_off)
        s["answer"] = ("skip", f"Unchanged: {r['fig']} days. Acting on the event would have published the past.", "")
        s["pager"] = ("run", f"ingest_stale_event, counted by {CNT}. Nothing pages.", "0 pages")
        s["walk"] = (("run", f"{WALK_AT}: every generation matches. Drift {wk['n1']['drift']}.", "") if walk else walk_off)
        out = "Refused before a byte was read: the ledger's generation is newer, and an old event must not undo a new version."
    elif scn in ("deleted", "withdrawn"):
        hand = scn == "withdrawn"
        if hand:
            s["event"] = ("skip", "No upload: make retire runs reconcile.py --retire from the operator's shell.", "")
            s["guard"] = skip("Not involved: the claim is untouched.")
        else:
            s["event"] = ("gap", f"Nothing. The notification declares {EVENT_TYPES[0]} only, so a delete publishes no event and the worker "
                                 "never hears of it.", "no event on delete")
            s["guard"] = skip()
        s["parse"], s["carry"] = skip(), skip("Nothing embedded.")
        acted = hand or walk
        when = "" if hand else f"At {WALK_AT} the walk: "
        if acted:
            gone = res["retired_chunks"] if hand else next(a for a in wk["n1"]["acts"] if a["action"] == "retire")["retired"]
            assert gone == N_HB, (scn, gone)
            s["swap"] = ("run", f"{when}retire_previous() flags version 1's {gone} rows: current false, expire_at in {WIN}. Nothing is "
                                "deleted.", f"{gone} rows retired")
            n_out = r["out"] if hand else wk["out"]
            s["ann"] = ("run", f"{when}remove_vectors() takes the {n_out} retired ids out of the index with the worker's own "
                               "remove_datapoints(), so no neighbour slot goes to a row the retriever would drop.", f"{n_out} out")
            ops = r["ops"] if hand else wk["ops"]
            s["mirror"] = mirror_line(ops, region, f"{when}retired()" if not hand else "retired()", None, "version 1")
            s["bq"] = ("gap", "Version 1's rows stay, as after every change.", "")
            if hand:
                s["ledger"] = ("run", "sources/: withdrawn, a tombstone and not retired; documents/: superseded. The object stays in the "
                                      "bucket.", "make restore is the way back")
            else:
                s["ledger"] = ("run", f"{when}sources/ says retired; documents/ says superseded.", "")
            fp_now = r["fp"] if hand else wk["fp"]
            s["fp"] = ("run", f"{short(pre['fp'])} becomes {short(fp_now)}, without the handbook's doc_key.", "")
            s["ctx"] = ("held", "Stale from then: cache_stale until make cache packs again.", "")
            s["ans"] = (("run", f"Entries stored under {short(pre['fp'])} miss from then.", "") if cache else ans_off)
            s["answer"] = ("run", (f"{when}the handbook's" if when else "The handbook's") + " rows leave the pool. lk-06 and vr-01 lose "
                                  "their source and fail live.", "")
        else:
            s["swap"] = ("gap", f"Nothing: version 1's {N_HB} rows stay current.", "")
            s["ann"] = ("gap", f"Nothing: {r['kept']} datapoints stay.", "")
            s["mirror"] = ("gap", "The stores keep version 1." if region == "any" else "Nothing: the stores never held it.", "")
            s["bq"] = ("gap", "Version 1's rows stay.", "")
            s["ledger"] = ("gap", "sources/ still says indexed: the ledger and the bucket disagree, and nothing measures it.", "")
            s["fp"] = ("gap", f"Unchanged at {short(r['fp'])}: the deleted document is still part of the corpus the caches follow.", "")
            s["ctx"] = ("gap", "Attached as before.", "")
            s["ans"] = (("gap", "Entries alive as before: the fingerprint did not move, so the deleted document's answers go on being "
                                "served and stored.", "") if cache else ans_off)
            s["answer"] = ("gap", f"Still {r['fig']} days, from a document the bucket no longer holds.", "")
        if hand:
            s["pager"] = ("stop", "reconcile_withdrawn is printed in the operator's shell, not logged by a service: no metric, no page.", "0 pages")
            s["walk"] = (("run", f"{WALK_AT}: withdrawn, object kept. Nothing done, and not drift ({wk['n1']['drift']}).", "the tombstone holds")
                         if walk else walk_off)
            out = (f"Withdrawn at once: {res['retired_chunks']} rows retired, the tombstone set, the ids out of the index, the fingerprint "
                   "moved. Nothing paged.")
        elif walk:
            s["pager"] = ("run", f"reconcile_done carries drift {wk['n1']['drift']}: one point on documind/reconcile_drift. The policy pages "
                                 f"only when drift stays above zero for {DRIFT_FOR_H} hours; the next night reads {wk['n2']['drift']}.", "0 pages")
            s["walk"] = ("run", f"plan(): retire, gone from the bucket. Drift {wk['n1']['drift']}, then {wk['n2']['drift']} the next night.", "")
            out = (f"Repaired at {WALK_AT}: retired, its ids out of the index, drift {wk['n1']['drift']}, the fingerprint moved. Nothing "
                   "paged.")
        else:
            s["pager"] = ("gap", "Nothing: no event, no metric, no page.", "")
            s["walk"] = ("gap", f"RECONCILE_JOB ?= {DEFAULTS['RECONCILE_JOB']}: no walk, so the gap stays until someone runs make reconcile "
                                "APPLY=1.", "off by default")
            out = "Nothing happened, and nothing will: the deleted handbook keeps answering until someone runs make reconcile APPLY=1."
    elif scn == "big":
        s["event"] = ("run", "OBJECT_FINALIZE for a new object.", "")
        s["guard"] = ("run", "No ledger row, so nothing is stale; a new doc_key, claimed.", "")
        if batch:
            s["parse"] = ("held", f"_pdf_pages() reads {res['pages']} off the page tree before Document AI is paid; over MAX_INLINE_PAGES "
                                  f"({rs.MAX_INLINE_PAGES}), so the claim says queued. documind-ingest-batch is started at once, and hourly at "
                                  f":{BATCH_CRON.split()[0]}: the same index_document(), in a job of up to {BATCH_TIMEOUT:,} s instead of a "
                                  f"{rs.WORKER_TIMEOUT} s request.", "queued, then taken")
            rest = ("held", "In the batch job, by the same functions, minutes later.", "")
            s["answer"] = ("held", "Answers nothing until the job has indexed it.", "")
            out = "Queued and taken at once by the batch job: the same pipeline, without the push lane's deadline."
        else:
            s["parse"] = ("gap", f"_pdf_pages() reads {res['pages']} off the page tree before Document AI is paid; over MAX_INLINE_PAGES "
                                 f"({rs.MAX_INLINE_PAGES}), so the claim says queued. BATCH_JOB ?= {DEFAULTS['BATCH_JOB']}: no job is declared, "
                                 "and nothing takes it.", "make batch-job declares it")
            rest = ("held", "Waiting for a batch job.", "")
            s["answer"] = ("gap", "Answers nothing, for as long as it waits.", "")
            out = "Queued and left: no batch job is declared, so nothing indexes it, and nothing pages."
        for k in ("carry", "swap", "ann", "mirror", "bq", "ledger", "fp"):
            s[k] = rest
        s["ctx"] = ("skip", "Untouched until it is indexed.", "")
        s["ans"] = (("skip", "Untouched until it is indexed.", "") if cache else ans_off)
        s["pager"] = ("gap", f"ingest_queued_batch is counted by {CNT}, but no policy reads it, and nothing reads the queue.", "0 pages")
        s["walk"] = (("run", f"plan(): queued, the batch lane holds it. Not drift, every night ({wk['n1']['drift']}, {wk['n2']['drift']}).", "")
                     if walk else walk_off)
    elif scn == "poison":
        s["event"] = ("run", "OBJECT_FINALIZE for a zero-byte object.", "")
        s["guard"] = ("stop", f"IngestMessage refuses size 0 before anything else: the worker answers 400 and logs ingest_poison. A 400 is not "
                              f"an ack: Pub/Sub retries with backoff from {rs.MIN_BACKOFF} s to {rs.MAX_BACKOFF} s, {rs.MAX_ATTEMPTS} deliveries "
                              f"in all, then {DLQ_TOPIC}.", "about an hour")
        for k in ("parse", "carry", "swap", "ann", "mirror", "bq", "ledger", "fp"):
            s[k] = skip()
        s["ctx"] = ("skip", "As before.", "")
        s["ans"] = (("skip", "As before.", "") if cache else ans_off)
        s["answer"] = ("skip", f"Unchanged: {r['fig']} days.", "")
        s["pager"] = ("run", f"ingest_poison is counted by {CNT}, but \"{DISPLAY_FAILED}\" reads ingest_failed only. The message ages on "
                             f"{SUB_NAME}: \"{DISPLAY_BACKLOG}\" pages once it has waited {BACKLOG_S // 60} minutes, and \"{DISPLAY_DLQ}\" "
                             f"within {DLQ_FOR_S} s of it landing in {DLQ_SUB}.", "2 pages")
        if walk:
            s["walk"] = ("gap", "plan(): not in the ledger, so its bytes are hashed; no claim holds them: reingest. The object is rewritten "
                                f"onto itself and refused again. Drift {wk['n1']['drift']} every night, and two nights page \"{DISPLAY_DRIFT}\".",
                         "until someone deletes it")
            out = (f"Refused {word(rs.MAX_ATTEMPTS)} times, then parked: the backlog alert pages about half an hour in, the dead-letter "
                   "alert about an hour. Every night the walk rewrites the object, and the refusals start again.")
        else:
            s["walk"] = walk_off
            out = (f"Refused {word(rs.MAX_ATTEMPTS)} times, then parked: the backlog alert pages about half an hour in, the dead-letter "
                   "alert about an hour. Nothing else changed.")
    elif scn == "chunker":
        s["event"] = ("gap", "Nothing: a deploy publishes no object.finalized.", "a rule is not an event")
        s["guard"] = skip()
        s["parse"] = ("held", f"Nothing re-chunked: version 1 keeps its {N_HB} chunks. When the handbook's next version lands, it is cut "
                              f"into {N400} chunks, {R400} of them matching a chunk version 1 holds: {N400 - R400} embedded.", "")
        s["carry"] = ("held", "Only at a document's next version. The same bytes again are a duplicate, so an unchanged document never "
                              "meets the new chunker.", "")
        for k in ("swap", "ann", "mirror", "bq", "ledger"):
            s[k] = skip()
        s["fp"] = ("skip", f"Unchanged at {short(r['fp'])}: a doc_key hashes bytes, not chunks.", "")
        s["ctx"] = ("skip", "Untouched.", "")
        s["ans"] = (("skip", "Untouched: the fingerprint did not move.", "") if cache else ans_off)
        s["answer"] = ("skip", "Unchanged.", "")
        s["pager"] = ("gap", "Nothing. As documents change, the index fills with two chunkers' rows, and nothing says which is which.", "")
        s["walk"] = (("run", f"{WALK_AT}: the bucket and the ledger agree, so drift {wk['n1']['drift']}: a chunker change is not drift.", "")
                     if walk else walk_off)
        out = "Nothing at all until each document next changes: a chunker is a rule, and a rule publishes no event."
    assert set(s) == {k for k, _, _ in ST}, (scn, sorted(set(k for k, _, _ in ST) - set(s)))
    return [s[k] for k, _, _ in ST], out


TEXTS, PANEL = [], {}


def tid(t: str) -> int:
    """A string's place in the panel's one table of texts: each text is stored once."""
    if t not in TEXTS:
        TEXTS.append(t)
    return TEXTS.index(t)


for key, _ in SCENARIOS:
    rows = []
    for c in COMBOS:
        sts, out = stations(key, c)
        rows.append([[{"run": 0, "skip": 1, "held": 2, "stop": 3, "gap": 4}[st], tid(t), tid(n)] for st, t, n in sts] + [tid(out)])
    PANEL[key] = rows
DATA = {"st": [k for k, _, _ in ST], "states": ["run", "skip", "held", "stop", "gap"], "sw": [k for k, _ in SWITCHES],
        "vals": {k: [str(v).lower() for v in vs] for k, vs in SWITCHES}, "t": TEXTS, "p": PANEL}
DEF_ST, DEF_OUT = stations("edit", COMBOS[DEF])
STATE_CSS = {"run": "", "skip": " skip", "held": " held", "stop": " stop", "gap": " gap"}
PANEL_STATIONS = "".join(f'<li class="rp-st{STATE_CSS[st]}" data-st="{k}"><b>{lab}</b><span class="rp-f">{esc(f)}</span>'
                         f'<span class="rp-t">{esc(t)}</span><span class="rp-c">{esc(n)}</span></li>'
                         for (k, lab, f), (st, t, n) in zip(ST, DEF_ST))
PANEL_OPTIONS = "".join(f'<option value="{k}"{" selected" if k == "edit" else ""}>{esc(lab)}</option>' for k, lab in SCENARIOS)
SW_LABELS = {"walk": ("The nightly walk", {"false": f"off: RECONCILE_JOB ?= {DEFAULTS['RECONCILE_JOB']}", "true": "on: make reconcile-job"}),
             "batch": ("The batch job", {"false": f"off: BATCH_JOB ?= {DEFAULTS['BATCH_JOB']}", "true": "on: make batch-job"}),
             "cache": ("The answer cache", {"false": f"off: SEMANTIC_CACHE ?= {DEFAULTS['SEMANTIC_CACHE']}", "true": "on: SEMANTIC_CACHE=on"}),
             "region": ("acme's data_region", {"any": "any, as make roster sets it", "in": "in, as globex has"})}
SW_SELECTS = "".join(f'<label>{esc(SW_LABELS[k][0])}<select id="rp-{k}">' + "".join(
    f'<option value="{str(v).lower()}"{" selected" if i == 0 else ""}>{esc(SW_LABELS[k][1][str(v).lower()])}</option>' for i, v in enumerate(vs))
    + "</select></label>" for k, vs in SWITCHES)
N_DISTINCT = len({json.dumps(PANEL[k][i]) for k, _ in SCENARIOS for i in range(len(COMBOS))})

# ================================================================== the three rejected options' numbers
HBD = next(d for d in rs.DOCS if d["slug"] == "hr_policy_2026")
assert HBD["chunks"] == N_HB
HB_BYTES = HBD["fs_row"] + HBD["fs_index"]                                # rag_scale's Firestore floor for the handbook's rows
KEEP_RS = rs.inr(HB_BYTES / rs.GIB * rs.FS_USD["gib_month"] * RETENTION / 30)
WIN_RS = rs.inr(WIN_CHARS / 1000 * rs.EMBED_USD_1K["online"])
SEC_RS = rs.inr(CHARS / 1000 * rs.EMBED_USD_1K["online"])
assert WIN_CHARS > 100 * CHARS
T_DOC = (1, 10)                                                          # seconds a document takes in the worker: 8.3's unit, and ten of it
REWRITE_MAX = {t: rs.IN_FLIGHT * rs.DLQ_BOUND_S // t for t in T_DOC}
assert rs.DLQ_BOUND_S == (rs.MAX_ATTEMPTS - 1) * rs.MAX_BACKOFF == 6600 and REWRITE_MAX == {1: 198_000, 10: 19_800}
UNDATED_EV = "An earlier draft declared an Eventarc trigger here instead"
UNDATED_VS = "STREAM_UPDATE, not BATCH_UPDATE. With BATCH_UPDATE the worker's"
assert UNDATED_EV in EV and UNDATED_VS in src("terraform/vector.tf")

# ================================================================== the alert policies, at the defaults and with the walk
TF = {p.name: p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf"))}
SUBS = dict(re.findall(r'resource "google_pubsub_subscription" "(\w+)" \{\s*name\s+= "([\w-]+)"', "".join(TF.values())))
resolve = lambda t: re.sub(r"\$\{google_pubsub_subscription\.(\w+)\.name\}", lambda m: SUBS[m.group(1)], t)  # noqa: E731
POL = []
for f, text in TF.items():
    for m in re.finditer(r'resource "google_monitoring_alert_policy" "(\w+)" \{(.*?)\n\}\n', text, re.S):
        name, body = m.group(1), m.group(2)
        gate = re.search(r"^\s+count\s+= var\.(\w+) \? 1 : 0", body, re.M)
        each = re.search(r"^\s+for_each\s+= toset\((\[.*?\])\)", body, re.M)
        disp = one(r'display_name = "([^"]+)"', body.split("conditions", 1)[0])
        targets = [resolve(t) for t in re.findall(r'(?:service_name|subscription_id|job_name)=\\"([^"\\]+)\\"', body)]
        metrics = re.findall(r'metric\.type=\\"([^"\\]+)\\"', body)
        POL.append({"file": f, "name": name, "gate": gate.group(1) if gate else None,
                    "n": len(ast.literal_eval(each.group(1))) if each else 1, "display": disp, "targets": targets, "metrics": metrics})
assert {p["file"] for p in POL} == {"alerts.tf", "desk_alerts.tf"}
GATE_DEFAULT = {"reconcile_job": False, "desk_router_alerts": False, "desk_gate_alerts": False}
for g in GATE_DEFAULT:
    assert one(rf'variable "{g}" \{{\s*type\s+= bool\s*default\s+= (\w+)', "".join(TF.values()), re.S) == "false", g
AT_DEFAULTS = sum(p["n"] for p in POL if not p["gate"])
WITH_WALK = AT_DEFAULTS + sum(p["n"] for p in POL if p["gate"] == "reconcile_job")
assert (SUBS["ingest_push"], SUBS["ingest_dlq_sub"]) == (SUB_NAME, DLQ_SUB), SUBS
INGEST_POL = [p for p in POL if any("documind-ingest" in t or "ingest-dlq" in t or "reconcile" in t for t in p["targets"])
              or any("ingest" in m or "reconcile" in m or "doc_type" in m for m in p["metrics"])]
assert sorted(p["name"] for p in INGEST_POL) == ["dlq_depth", "doc_type_pin_miss", "ingest_backlog", "ingest_failed", "reconcile_drift",
                                                 "reconcile_failed"], [p["name"] for p in INGEST_POL]
# the main subscription: one policy, on its oldest unacknowledged message (13 October 2026)
assert [p["name"] for p in POL if SUB_NAME in json.dumps(p) or "oldest_unacked" in json.dumps(p)] == ["ingest_backlog"]
POL_BODIES = [m.group(1) for t in TF.values() for m in re.finditer(r'resource "google_monitoring_alert_policy" "\w+" \{(.*?)\n\}\n', t, re.S)]
assert all("cache_stale" not in t for t in TF.values()) and not any("ingest_queued_batch" in b for b in POL_BODIES)
assert (AT_DEFAULTS, WITH_WALK) == (11, 13), (AT_DEFAULTS, WITH_WALK)
DISPLAY = {p["name"]: p["display"] for p in POL}
DEFAULT_NAMES = sorted(n for p in POL if not p["gate"] for n in
                       ([p["display"].replace("${each.key}", k) for k in ("documind-slm", "documind-vllm")] if p["n"] > 1 else [p["display"]]))
WALK_NAMES = sorted(DEFAULT_NAMES + [p["display"] for p in POL if p["gate"] == "reconcile_job"])
assert len(DEFAULT_NAMES) == AT_DEFAULTS and len(WALK_NAMES) == WITH_WALK

# ================================================================== the cost at three scales (rag_scale) and of one edit
C = rs.SHAPES["corpus"]
SCALES = (1_000, 100_000, 10_000_000)
SCALE_WORD = {1_000: "1k", 100_000: "100k", 10_000_000: "10M"}
AT = {d: rs.scale(d, C) for d in SCALES}
CHEAP = {d: min(rs.SHARD_GIB, key=lambda z: AT[d]["serve_usd_month"][z]) for d in SCALES}
assert [CHEAP[d] for d in SCALES] == ["SHARD_SIZE_SMALL", "SHARD_SIZE_LARGE", "SHARD_SIZE_LARGE"], CHEAP
assert rs.MONTH_H == 730 and rs.COMPACTIONS_30D == 6 and rs.REPLICAS == 1 and DIMS == rs.DIMS == 768
EDIT_EMBED_USD = CHARS / 1000 * rs.EMBED_USD_1K["online"]
EDIT_STREAM_USD = N_HB * 768 * 4 / 2**30 * rs.VS_STREAM_USD_GIB
EDIT_FS_USD = EDIT_WRITES * rs.FS_USD["write"] + (EDIT_READS - VERSIONS) * rs.FS_USD["read"]
# what an edit costs apart from the fingerprint, summed in the order the cost cell sums it
EDIT_BASE_USD = (EDIT_EMBED_USD + EDIT_STREAM_USD + EDIT_WRITES * rs.FS_USD["write"] + (EDIT_READS - VERSIONS) * rs.FS_USD["read"])
FP_USD = {d: d * rs.FS_USD["read"] for d in SCALES}
FP_CROSS = math.ceil(EDIT_BASE_USD / rs.FS_USD["read"])                  # the tenant size past which the fingerprint costs more
COST = {}
for d in SCALES:
    o = AT[d]
    serve, compact, store = o["serve_usd_month"][CHEAP[d]], o["compact_usd"] * rs.COMPACTIONS_30D, o["fs_usd_month"]
    edit = EDIT_BASE_USD + FP_USD[d]
    COST[d] = {"serve": rs.inr(serve), "shards": o["shards"][CHEAP[d]], "compact": rs.inr(compact), "fs": rs.inr(store),
               "embed": rs.inr(o["embed_usd"]["online"]), "edit": rs.inr(edit), "fp": rs.inr(FP_USD[d]),
               "standing": rs.inr(serve + compact + store), "breakeven": (serve + compact + store) / edit,
               "walk": rs.inr(o["walk_usd"]), "walk_rate": o["walk_rate"], "fp_rate": o["fp_last_rate"]}
assert all(COST[d]["fp_rate"] == d / rs.WORKER_TIMEOUT for d in SCALES)
assert COST[10_000_000]["fp"] > 100 * rs.inr(EDIT_BASE_USD) and 1_000 < FP_CROSS < 10_000, (FP_CROSS, COST)
r0, group, rupees = rs.r0, rs.group, rs.rupees


def money(x: float) -> str:
    """Rupees for a table cell, and the dollars beside: four places under a paisa, two under a thousand rupees, then
    whole rupees, lakh and crore; dollars to six places under a tenth of a cent, four under a dollar, two under a
    thousand, then whole."""
    usd = x / rs.USD_INR
    rs_txt = f"Rs {x:.4f}" if x < 0.01 else f"Rs {x:,.2f}" if x < 1000 else rupees(x)
    usd_txt = f"${usd:.6f}" if usd < 0.001 else f"${usd:.4f}" if usd < 1 else f"${usd:,.2f}" if usd < 1000 else f"${usd:,.0f}"
    return f"{rs_txt} ({usd_txt})"


COST_ROWS = [
    ("Vector Search serving, a month", lambda d: f"{money(COST[d]['serve'])}<br>{COST[d]['shards']} {rs.SHORT[CHEAP[d]]} shard{'s' if COST[d]['shards'] > 1 else ''}"),
    (f"Compaction while changes arrive, {word(rs.COMPACTIONS_30D)} a month", lambda d: money(COST[d]["compact"])),
    ("Firestore storage, a month", lambda d: money(COST[d]["fs"])),
    ("<strong>Standing still and staying fresh, a month</strong>", lambda d: f"<strong>{money(COST[d]['standing'])}</strong>"),
    ("Embedding the corpus once", lambda d: money(COST[d]["embed"])),
    ("One edit like the handbook's, without the fingerprint", lambda d: money(rs.inr(EDIT_BASE_USD))),
    ("The fingerprint's reads, on every change", lambda d: f"{money(COST[d]['fp'])}<br>{d:,} rows"),
    ("<strong>One edit, in all</strong>", lambda d: f"<strong>{money(COST[d]['edit'])}</strong>"),
    ("Edits a month that cost as much as standing still", lambda d: f"{COST[d]['breakeven']:,.0f}"),
    (f"The nightly walk's reads, when it runs", lambda d: money(COST[d]["walk"])),
]


def tw(head: list, rows: list) -> str:
    """A comparison table: the first cell bare, every other cell labelled for the phone layout."""
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">',
           "<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>", "<tbody>"]
    for cells in rows:
        out.append("<tr><td>" + cells[0] + "</td>" + "".join(f'<td data-label="{html.escape(re.sub("<[^>]+>", "", h))}">{c}</td>'
                                                            for h, c in zip(head[1:], cells[1:])) + "</tr>")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')
    return "\n".join(out)


COST_TABLE = tw(["Line"] + [f"{SCALE_WORD[d]} documents" for d in SCALES], [[a] + [f(d) for d in SCALES] for a, f in COST_ROWS])
EDIT_TABLE = tw(["Part of one edit", "Counted how", "Rupees"], [
    ["Embedding", f"{CHARS:,} characters at ${rs.EMBED_USD_1K['online']:.6f} per 1,000", money(rs.inr(EDIT_EMBED_USD))],
    ["Vector Search, streamed in", f"{N_HB} datapoints of {DIMS} numbers at 4 bytes, at ${rs.VS_STREAM_USD_GIB:.2f} a GiB", money(rs.inr(EDIT_STREAM_USD))],
    ["Firestore, the document", f"{EDIT_WRITES:,} writes and {EDIT_READS - VERSIONS:,} reads, counted as the kit's functions made them",
     money(rs.inr(EDIT_FS_USD))],
    ["Firestore, the fingerprint", f"one read per indexed source of the tenant: {VERSIONS} on the kit's acme corpus",
     money(rs.inr(VERSIONS * rs.FS_USD["read"]))],
])

LIMITS_TABLE = tw(["Limit", "Where the kit sets it"] + [f"At {SCALE_WORD[d]} documents" for d in SCALES], [
    ["<strong>The fingerprint</strong>, on every change", "<code>idempotency.py</code>: every indexed source of the tenant, read inside the "
     f"worker's {rs.WORKER_TIMEOUT}-second request"] + [f"{d:,} rows, {r0(COST[d]['fp_rate']):,} a second" for d in SCALES],
    ["<strong>The nightly walk</strong>", f"<code>reconcile.tf</code>: one task, {rs.WALK_SECONDS:,} seconds, no retry"]
    + [f"{AT[d]['walk_items']:,} objects and rows, {r0(COST[d]['walk_rate']):,} a second" for d in SCALES],
    [f"<strong>{rs.IN_FLIGHT} in flight</strong>, {rs.MAX_ATTEMPTS} deliveries", "<code>lesson-12.5.sh</code>, <code>eventarc.tf</code>: "
     "the whole corpus re-issued at once, at 1 s a document"]
    + [("clears inside the dead-letter bound" if d <= REWRITE_MAX[1] else
        f"past {REWRITE_MAX[1]:,}, the tail reaches the DLQ") for d in SCALES],
])
assert [d <= REWRITE_MAX[1] for d in SCALES] == [True, True, False]

# ================================================================== the evals
sys.path.insert(0, str(KIT / "evals"))
import run_eval  # noqa: E402
CORPUS = run_eval.load_corpus()
IN_SCOPE = [r["id"] for r in GOLDEN if run_eval.in_scope(r, "hr_policy_2026.md", CORPUS)]
VERSION_ROWS = [r["id"] for r in GOLDEN if r["shape"] == "version"]
assert VERSION_ROWS == ["vr-01"] and {"lk-06", "vr-01"} <= set(IN_SCOPE)
N_THRESH, N_REQUIRED = len(run_eval.THRESHOLDS), len(run_eval.load_required())
assert not run_eval.check_anchors(GOLDEN, CORPUS)
assert "matches each anchor against filename + text joined together" in src("evals/run_eval.py")
assert "must_retrieve_recall\n                  beside quote_passage_rate - both [info], neither a threshold" in src("evals/run_eval.py")
REINDEX_SH = src("commands/reindex.sh")
assert '"$PY" evals/run_eval.py --source "$OBJ" >/dev/null' in REINDEX_SH

# ================================================================== the cells: written here, run here, their output the page's
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}               # no gcloud on PATH, no Google credentials in the environment
CELLS = {
    "reissue": '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["."]
from shared import documind_corpus as dc     # the notebooks' twin of the worker's chunker: the same texts, hashes and locators
v1, v2 = (open(p, encoding="utf-8").read() for p in ("evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md"))
doc = lambda text: {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://%%BUCKET%%/acme/hr_policy_2026.md", "text": text}
old, new = dc.chunk_document(doc(v1), "acme"), dc.chunk_document(doc(v2), "acme")
held = {c["chunk_hash"] for c in old}                       # the carry-over's rule: a vector is reused when its chunk_hash is held
fresh = [c for c in new if c["chunk_hash"] not in held]
print(f"by section: {len(new)} chunks, {len(new) - len(fresh)} reused, {len(fresh)} embedded "
      f"({', '.join(c['locator'] for c in fresh)}), {sum(len(c['text']) for c in fresh):,} characters sent")
w_old, w_new = dc.windows(v1), dc.windows(v2)              # the same two texts, cut as whole-document windows
w_held = {dc.chunk_hash(t) for t in w_old}
w_fresh = [t for t in w_new if dc.chunk_hash(t) not in w_held]
print(f"by whole-document windows: {len(w_new)} chunks, {len(w_new) - len(w_fresh)} reused, {len(w_fresh)} embedded, "
      f"{sum(map(len, w_fresh)):,} characters sent")
print(f"revision 2's first lines: {v2.splitlines()[0]!r}, then {v2.splitlines()[2][:60]!r}")''',
    "thresholds": '''import re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["."]
from shared import documind_corpus as dc
from shared.prices import USD_INR
src = lambda p: open(p, encoding="utf-8").read()
EMBED_1K = %%EMBED_PY%%                      # text-embedding-005 input, online, per 1,000 characters: lesson 8.3's price, read on %%PRICE_DATE%%
v1, v2 = src("evals/corpus/acme/hr_policy_2026.md"), src("evals/demo/hr_policy_2026_v2.md")
doc = lambda text: {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://b/acme/hr_policy_2026.md", "text": text}
held = {c["chunk_hash"] for c in dc.chunk_document(doc(v1), "acme")}
by_section = sum(len(c["text"]) for c in dc.chunk_document(doc(v2), "acme") if c["chunk_hash"] not in held)
w_held = {dc.chunk_hash(t) for t in dc.windows(v1)}
by_window = sum(len(t) for t in dc.windows(v2) if dc.chunk_hash(t) not in w_held)
print(f"1. one clause edited: Rs {by_section / 1000 * EMBED_1K * USD_INR:.4f} to embed by section, "
      f"Rs {by_window / 1000 * EMBED_1K * USD_INR:.2f} by whole-document windows ({by_window / by_section:,.0f} times as much)")
tf = src("terraform/variables.tf").split('variable "retention_days" {', 1)[1]
low, high = re.search(r"retention_days >= (\\d+) && var.retention_days <= (\\d+)", tf).groups()
days = re.search(r'^RETENTION_DAYS\\s+\\?= (\\d+)', src("Makefile"), re.M).group(1)
print(f"2. retired rows live {days} days (RETENTION_DAYS); the window can be set from {low} to {high} days, never to zero")
ev, run = src("terraform/eventarc.tf"), src("commands/lesson-12.5.sh")
attempts = int(re.search(r"max_delivery_attempts = (\\d+)", ev).group(1))
longest = int(re.search(r'maximum_backoff = "(\\d+)s"', ev).group(1))
flight = int(re.search(r"--max-instances=(\\d+)", run).group(1)) * int(re.search(r"--concurrency=(\\d+)", run).group(1))
bound = (attempts - 1) * longest            # the waits between twelve deliveries, none longer than the longest backoff
for t in (1, 10):
    print(f"3. rewrites at once that the push lane clears inside {bound:,} s of backoff, at {t} s a document: {flight * bound // t:,}")''',
    "alerts": '''import re, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
tf = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("terraform").glob("*.tf"))}
subs = dict(re.findall(r'resource "google_pubsub_subscription" "(\\w+)" \\{\\s*name\\s+= "([\\w-]+)"', "".join(tf.values())))
pols = []
for f, text in tf.items():
    for m in re.finditer(r'resource "google_monitoring_alert_policy" "(\\w+)" \\{(.*?)\\n\\}\\n', text, re.S):
        body = re.sub(r"\\$\\{google_pubsub_subscription\\.(\\w+)\\.name\\}", lambda s: subs[s.group(1)], m.group(2))
        gate = re.search(r"count\\s+= var\\.(\\w+) \\? 1 : 0", body)
        metric = {t.rsplit("/", 1)[-1] for t in re.findall(r'metric\\.type=\\\\"([^"\\\\]+)\\\\"', body)}
        on = set(re.findall(r'(?:subscription_id|job_name)=\\\\"([^"\\\\]+)\\\\"', body))
        pols.append((m.group(1), gate.group(1) if gate else "", metric, on, body))
for name, gate, metric, on, body in pols:
    if any(w in body for w in ("ingest", "reconcile", "doc_type_pin_miss")):
        print(f"{name:18} reads {', '.join(sorted(metric))}" + (f" on {', '.join(sorted(on))}" if on else "")
              + (f" - declared only when {gate} is true" if gate else ""))
sub = subs["ingest_push"]
print(f"policies that read {sub}: {sum(sub in p[4] for p in pols)}; that read oldest_unacked_message_age: "
      f"{sum('oldest_unacked' in t for t in tf.values())}; that count cache_stale: {sum('cache_stale' in t for t in tf.values())}")
mk = open("Makefile", encoding="utf-8").read()
print("the walk:", re.search(r"^RECONCILE_JOB\\s+\\?= \\w+", mk, re.M).group(0), "| the batch job:", re.search(r"^BATCH_JOB\\s+\\?= \\w+", mk, re.M).group(0))''',
    "stuck": '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["services/ingest"]
from reconcile import decide_bytes, drift_of, plan     # the walk's planner: pure, no cloud client
from idempotency import lease_of                       # the claim's lease (13 October 2026)
docs = {"acme_aaa": {"status": "processing", "gcs_uri": "gs://b/acme/cut_off.md"},     # a worker cut off between claim and finish
        "acme_qqq": {"status": "queued", "gcs_uri": "gs://b/acme/big.pdf", "generation": "7"}}
objects = [{"name": "acme/cut_off.md", "generation": "5", "tenant_id": "acme"},
           {"name": "acme/poison.pdf", "generation": "6", "tenant_id": "acme"},
           {"name": "acme/big.pdf", "generation": "7", "tenant_id": "acme"}]
sha = {"acme/cut_off.md": "aaa", "acme/poison.pdf": "e3b0c442", "acme/big.pdf": "qqq"}
summary = {}
for act in plan(objects, {}, docs):
    if act["action"] == "check_bytes":
        act["action"] = decide_bytes(sha[act["name"]], "acme", None, docs)
    summary[act["action"]] = summary.get(act["action"], 0) + 1
    print(f"{act['name']:18} {act['action']:9} ({act.get('why', '')})")
print(f"drift {drift_of(summary)} of {len(objects)} objects")
age = 6 * 3600 + 25 * 60                                # claimed at 17:05 and cut off; the walk runs at 23:30
verdict = "is nacked: the lease is live" if age < lease_of(docs["acme_aaa"]) else "takes the claim back and indexes the bytes"
print(f"acme/cut_off.md's claim at the walk: {age:,} s old, its lease {lease_of(docs['acme_aaa']):,} s, so the rewrite's delivery {verdict}")''',
}
PRICE_DATE = "12 October 2026"                                            # rag_scale.py's date for every price it holds
SUBST_CELLS = {"BUCKET": BUCKET, "EMBED_PY": f"{rs.EMBED_USD_1K['online']:.6f}", "PRICE_DATE": PRICE_DATE}
assert f"read on {PRICE_DATE} from Google's pages" in Path(rs.__file__).read_text(encoding="utf-8")
CELLS["cost"] = '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["."]
from shared import documind_corpus as dc
from shared.prices import USD_INR
# Google's prices the kit does not hold: lesson 8.3's, read on %%PRICE_DATE%% (Mumbai for Vector Search and Firestore) - verify them
EMBED_1K, STREAM_GIB, BUILD_GIB = %%EMBED_PY%%, %%STREAM_PY%%, %%BUILD_PY%%                 # per 1,000 characters; per GiB in; per GiB rebuilt
READ, WRITE, STORE = %%READ_PY%%, %%WRITE_PY%%, %%STORE_PY%%                  # Firestore: per read, per write, per GiB a month
NODE = %%NODE_PY%%                                    # a serving node an hour, by shard size (GiB a shard, USD)
CHUNK_BYTES = %%CHUNK_BYTES%%                    # Firestore bytes a chunk with its eight vector-index entries (8.3's floor)
docs = chunks = 0
chars = 0
for t in ("acme", "globex", "zeta"):
    for d in dc.load_documents(t, "evals", "%%PROJ%%"):
        cs = dc.chunk_document(d, t)
        docs, chunks, chars = docs + 1, chunks + len(cs), chars + sum(len(c["text"]) for c in cs)
per_doc, chars_doc = chunks / docs, chars / docs
EDIT = {"chars": %%CHARS%%, "datapoints": %%N_HB%%, "writes": %%EDIT_WRITES%%, "reads": %%EDIT_READS_DOC%%}   # the handbook's edit, counted on this page
edit = (EDIT["chars"] / 1000 * EMBED_1K + EDIT["datapoints"] * 768 * 4 / 2**30 * STREAM_GIB
        + EDIT["writes"] * WRITE + EDIT["reads"] * READ)
print(f"the kit's corpus: {docs} documents, {per_doc:.2f} chunks and {chars_doc:,.0f} characters each; one edit like the handbook's "
      f"Rs {edit * USD_INR:.2f} before the fingerprint")


def month(n):
    """Standing still and staying fresh for n documents: serving on the cheapest shard size, six compactions, storage."""
    rows = n * per_doc
    gib = rows * 768 * 4 / 2**30
    serve = min(1 * max(1, -(-gib // size)) * usd * 730 for size, usd in NODE.values())
    return serve + gib * BUILD_GIB * 6 + rows * CHUNK_BYTES / 2**30 * STORE, n * chars_doc / 1000 * EMBED_1K


def rupees(x):
    """Rupees as the page's tables write them: crore and lakh above a lakh, whole rupees grouped the Indian way below."""
    if x >= 1e7:
        return f"Rs {x / 1e7:,.2f} crore"
    if x >= 1e5:
        return f"Rs {x / 1e5:,.2f} lakh"
    s = str(int(x + 0.5))
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        head, tail = head[:-2], head[-2:] + "," + tail
    return f"Rs {head},{tail}" if head else f"Rs {tail}"


for n in (1_000, 100_000, 10_000_000):
    standing, embed = month(n)
    each = edit + n * READ                          # every change re-reads the tenant's n ledger rows (the fingerprint)
    print(f"{n:>10,} documents: {rupees(standing * USD_INR)} a month standing, {rupees(embed * USD_INR)} to embed once, "
          f"Rs {each * USD_INR:,.2f} an edit; {standing / each:,.0f} edits a month cost as much as standing still")'''
SUBST_CELLS.update({
    "STREAM_PY": f"{rs.VS_STREAM_USD_GIB:.2f}", "BUILD_PY": f"{rs.VS_BUILD_USD_GIB:.2f}",
    "READ_PY": repr(rs.FS_USD["read"]), "WRITE_PY": repr(rs.FS_USD["write"]), "STORE_PY": repr(rs.FS_USD["gib_month"]),
    "NODE_PY": "{" + ", ".join(f'"{rs.SHORT[z]}": ({rs.SHARD_GIB[z]}, {rs.VS_NODE_USD[z]!r})' for z in rs.SHARD_GIB) + "}",
    "CHUNK_BYTES": repr(C["fs_chunk"]), "PROJ": PROJ, "CHARS": str(CHARS), "N_HB": str(N_HB),
    "EDIT_WRITES": str(EDIT_WRITES), "EDIT_READS_DOC": str(EDIT_READS - VERSIONS)})
CELLS["evals"] = '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals"]
from run_eval import check_anchors, in_scope, load_corpus, load_golden, load_required, THRESHOLDS
golden, corpus, required = load_golden(), load_corpus(), set(load_required())
scope = [r["id"] for r in golden if in_scope(r, "hr_policy_2026.md", corpus)]
print(f"make eval-live SOURCE=hr_policy_2026.md sends {len(scope)} of {len(golden)} rows: {', '.join(scope)}")
for r in golden:
    if r["shape"] == "version":
        demo = open("evals/demo/hr_policy_2026_v2.md", encoding="utf-8").read()
        print(f"{r['id']} ({'required' if r['id'] in required else 'optional'}): must not say {r['must_not_contain']}, which only "
              f"revision 2 holds ({r['must_not_contain'][0] in demo}); re-issue the handbook and this row moves with it, in one commit")
print(f"anchors over whole documents: {len(check_anchors(golden, corpus))} problems - it reads files and never a chunk, "
      f"so no chunker change and no carry-over bug can turn it red")
print(f"what blocks live: {len(THRESHOLDS)} thresholds and {len(required)} required rows; must_retrieve recall is printed as [info]")'''
for k, v in list(CELLS.items()):
    for name, val in SUBST_CELLS.items():
        v = v.replace(f"%%{name}%%", val)
    assert "%%" not in v and "'''" not in v and "\nPY" not in v, (k, re.findall(r"%%\w+%%", v))
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in v, k
    for fn in re.findall(r"^def (\w+)\(", v, re.M):            # every function a cell defines carries a one-line docstring
        assert re.search(rf'^def {fn}\(.*\):\n    """[^\n]+"""', v, re.M), (k, fn)
    CELLS[k] = v


def run_python(code: str) -> str:
    """One cell, run in deploy/ as the learner runs it in $DEMO_ROOT: python - <<'PY' ... PY."""
    r = subprocess.run([sys.executable, "-"], input=code, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-600:], r.stderr[-1500:])
    return r.stdout.rstrip("\n")


OUT = {k: run_python(v) for k, v in CELLS.items()}
gate = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
assert gate.returncode == 0, gate.stdout[-800:] + gate.stderr[-800:]
OUT["evals"] = gate.stdout.rstrip("\n") + "\n" + OUT["evals"]

# every cell's output, held against the numbers the page states
assert (f"by section: {N_HB} chunks, {ER['reused']} reused, {ER['embedded']} embedded (preamble, NP-03), {CHARS:,} characters sent"
        in OUT["reissue"]), OUT["reissue"]
assert f"by whole-document windows: {WIN_N} chunks, {WIN_REUSED} reused, {WIN_N - WIN_REUSED} embedded, {WIN_CHARS:,} characters sent" in OUT["reissue"]
assert f"Rs {SEC_RS:.4f} to embed by section, Rs {WIN_RS:.2f} by whole-document windows" in OUT["thresholds"], OUT["thresholds"]
assert f"retired rows live {RETENTION} days (RETENTION_DAYS); the window can be set from {RET_MIN} to {RET_MAX} days" in OUT["thresholds"]
for t in T_DOC:
    assert f"at {t} s a document: {REWRITE_MAX[t]:,}" in OUT["thresholds"]
assert f"policies that read {SUB_NAME}: 1; that read oldest_unacked_message_age: 1; that count cache_stale: 0" in OUT["alerts"], OUT["alerts"]
assert f"ingest_backlog     reads oldest_unacked_message_age on {SUB_NAME}" in OUT["alerts"], OUT["alerts"]
assert "reconcile_drift    reads reconcile_drift - declared only when reconcile_job is true" in OUT["alerts"], OUT["alerts"]
assert "dlq_depth          reads num_undelivered_messages on ingest-dlq-sub" in OUT["alerts"], OUT["alerts"]
assert "the walk: RECONCILE_JOB   ?= false | the batch job: BATCH_JOB       ?= false" in OUT["alerts"], OUT["alerts"]
assert "acme/cut_off.md    reingest" in OUT["stuck"] and "acme/poison.pdf    reingest" in OUT["stuck"] and "acme/big.pdf       queued" in OUT["stuck"]
assert "drift 2 of 3 objects" in OUT["stuck"], OUT["stuck"]
assert f"23,100 s old, its lease {LEASE_S} s, so the rewrite's delivery takes the claim back and indexes the bytes" in OUT["stuck"], OUT["stuck"]
assert f"one edit like the handbook's Rs {rs.inr(EDIT_BASE_USD):.2f} before the fingerprint" in OUT["cost"], OUT["cost"]
for d in SCALES:
    line = next(l for l in OUT["cost"].splitlines() if l.lstrip().startswith(f"{d:,} documents"))
    assert f"{rupees(COST[d]['standing'])} a month standing, {rupees(COST[d]['embed'])} to embed once" in line, (line, COST[d])
    assert f"Rs {COST[d]['edit']:,.2f} an edit; {COST[d]['breakeven']:,.0f} edits a month" in line, (line, COST[d])
    assert f"{group(r0(COST[d]['breakeven']))}" == f"{COST[d]['breakeven']:,.0f}"          # under a lakh: both groupings agree
assert f"sends {len(IN_SCOPE)} of {len(GOLDEN)} rows" in OUT["evals"] and "The golden set is sound." in OUT["evals"]
assert f"anchors over whole documents: 0 problems" in OUT["evals"] and f"{N_THRESH} thresholds and {N_REQUIRED} required rows" in OUT["evals"]

# ================================================================== the lane reads: what each shows, in the course's placeholders
DOCS_UI = src("services/frontend/documents.py")              # what the Documents page shows: the ledger, as GET /v1/sources serves it
for needle in ('st.subheader("Versions")', '"reused": r_["reused"]', '"embedded": r_["embedded"]', '"retired": r_["retired"]',
               '"embedding": r_["embedding"]', '"held in": _held_in(r_)', "current versions - corpus fingerprint", "(last change:",
               "- data_region {region}: "):
    assert needle in DOCS_UI, needle
assert '"generation"' not in DOCS_UI.split("def versions_section", 1)[1].split("def ", 1)[0]       # the table has no generation column
TOK = '-H "Authorization: Bearer $(tok "$API")"'
LANE_SOURCES = ('curl -s "$API/v1/sources?tenant_id=acme" ' + TOK + " \\\n  | python -c '"
                "import json, sys; d = json.load(sys.stdin); print(\"acme:\", d[\"data_region\"], \"|\", d[\"versions\"], \"current versions | fingerprint\", "
                "d[\"fingerprint\"], \"| last\", d[\"last_event\"]); [print(\" \", s[\"name\"], s[\"status\"], s[\"chunks\"], \"chunks, reused\", s[\"reused\"], "
                "\"embedded\", s[\"embedded\"], \"retired\", s[\"retired\"], s[\"embedding\"]) for s in d[\"sources\"] if s[\"name\"].endswith(\"hr_policy_2026.md\")]'")
LANE_FS = '''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
led = (db.document("ledger/acme").get().to_dict() or {})
print(f"ledger/acme: fingerprint {led.get('fingerprint')}, {led.get('versions')} versions, last event {led.get('last_event')}")
cache = db.document("tenant_caches/acme").get()
packed = (cache.to_dict() or {}).get("corpus_fingerprint") if cache.exists else None
print("tenant_caches/acme: " + ("none" if not cache.exists else f"packed under {packed}: "
                                + ("current" if packed == led.get("fingerprint") else "STALE")))
fps = [s.to_dict().get("fingerprint") for s in db.collection("answer_cache").where("tenant_id", "==", "acme").select(["fingerprint"]).stream()]
print(f"answer_cache, acme: {len(fps)} entries, {sum(f == led.get('fingerprint') for f in fps)} under the current fingerprint")'''
LANE_ALERTS = '''import json, os, re, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies?pageSize=200", headers={"Authorization": "Bearer " + tok})
policies = json.load(urllib.request.urlopen(req, timeout=60)).get("alertPolicies", [])
print(f"{len(policies)} alert policies on the lane")
for p in sorted(policies, key=lambda p: p["displayName"]):
    print(" ", p["displayName"])
filters = " ".join(c.get("conditionThreshold", {}).get("filter", "") for p in policies for c in p.get("conditions", []))
print("reads documind-ingest-push:", "documind-ingest-push" in filters, "| reads the dead-letter subscription:", "ingest-dlq-sub" in filters)'''
for body in (LANE_FS, LANE_ALERTS):
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in body and "'''" not in body
SRC_FMT = (f"acme: {dict(POLICIES)['acme']} | NUMBER current versions | fingerprint ... | last ingest_...\n"
           f"  acme/hr_policy_2026.md indexed {N_HB} chunks, reused N embedded N retired N {DEFAULTS['EMBEDDING_MODEL']}@{DEFAULTS['EMBEDDING_VERSION']}")
FS_FMT = ("ledger/acme: fingerprint ..., NUMBER versions, last event ...\n"
          "tenant_caches/acme: none  (or: packed under ...: current | STALE)\n"
          "answer_cache, acme: N entries, N under the current fingerprint")
ALERTS_FMT = (f"{AT_DEFAULTS} alert policies on the lane\n" + "\n".join("  " + n for n in DEFAULT_NAMES)
              + "\nreads documind-ingest-push: True | reads the dead-letter subscription: True\n\n"
              + f"{WITH_WALK} alert policies on the lane\n" + "\n".join("  " + n for n in WALK_NAMES)
              + "\nreads documind-ingest-push: True | reads the dead-letter subscription: True")


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + esc(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + esc(code) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + esc(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + esc(text.rstrip("\n")) + "</pre></div>\n")


heredoc = lambda code: "python - <<'PY'\n" + code + "\nPY"  # noqa: E731
OFFLINE = "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing)"
BUILT = "(the kit's own output, produced when this page was built; yours matches it line for line)"
WIN_ = {
    "CELL_UI": bash_window("run in the operator shell (prints your UI's address)", 'echo "https://documind-ui-$NUMBER.$REGION.run.app"'),
    "OUT_UI": out_window("(the format: NUMBER is your project number)", "https://documind-ui-NUMBER.asia-south1.run.app"),
    "CELL_SOURCES": bash_window("run in the operator shell (one GET as the UI's account; reads the ledger, writes nothing)", LANE_SOURCES),
    "OUT_SOURCES": out_window("(the format: your counts and fingerprint are yours)", SRC_FMT),
    "CELL_FS": bash_window("run in the operator shell (three Firestore reads; writes nothing)", heredoc(LANE_FS)),
    "OUT_FS": out_window("(the format: your fingerprints and counts are yours)", FS_FMT),
    "CELL_REISSUE": bash_window(OFFLINE, heredoc(CELLS["reissue"])), "OUT_REISSUE": out_window(BUILT, OUT["reissue"]),
    "CELL_THRESH": bash_window(OFFLINE, heredoc(CELLS["thresholds"])), "OUT_THRESH": out_window(BUILT, OUT["thresholds"]),
    "CELL_ALERTS": bash_window(OFFLINE, heredoc(CELLS["alerts"])), "OUT_ALERTS": out_window(BUILT, OUT["alerts"]),
    "CELL_STUCK": bash_window(OFFLINE, heredoc(CELLS["stuck"])), "OUT_STUCK": out_window(BUILT, OUT["stuck"]),
    "CELL_COST": bash_window(OFFLINE, heredoc(CELLS["cost"])), "OUT_COST": out_window(BUILT, OUT["cost"]),
    "CELL_EVALS": bash_window("run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call)",
                              "python evals/run_eval.py\n" + heredoc(CELLS["evals"])),
    "OUT_EVALS": out_window(BUILT, OUT["evals"]),
    "CELL_LANE_ALERTS": bash_window("run in the operator shell (one GET on the Monitoring API; changes nothing)", heredoc(LANE_ALERTS)),
    "OUT_LANE_ALERTS": out_window("on a lane deployed with the defaults, then on one where make reconcile-job has run (your lane shows one of the two)",
                                  ALERTS_FMT),
}

# ================================================================== excerpts, verbatim
EXCERPTS = {
    "notification": ("terraform/eventarc.tf - the bucket's notification: one event type, and the push subscription's ceiling",
                     block("terraform/eventarc.tf", 'resource "google_storage_notification" "uploads" {', n=7) + "\n...\n"
                     + block("terraform/eventarc.tf", "  # At-least-once, with a ceiling:", end="  depends_on")),
    "guard": ("services/ingest/main.py - push(): the generation guard, before a byte is downloaded",
              block("services/ingest/main.py", "    # THE GENERATION GUARD (12 September 2026).", n=11)),
    "claim": ("services/ingest/idempotency.py - claim(): exactly one worker per version, and what it refuses",
              block("services/ingest/idempotency.py", '    ref = db.collection("documents").document(doc_key)', n=17)),
    "chunker": ("services/ingest/main.py - the chunk, and why a handbook is cut by section",
                block("services/ingest/main.py", "# 4.1's chunker, the shape every lesson's corpus has", n=7)),
    "carry": ("services/ingest/indexer.py - the carry-over: a vector is reused when its chunk_hash is held",
              block("services/ingest/indexer.py", "def plan_carry_over(", end="def _restricts(")),
    "swap": ("services/ingest/main.py - index_document(): staged, swapped, and the index follows",
             block("services/ingest/main.py", "        # THE SWAP. The new version is written STAGED", n=11)),
    "fingerprint": ("services/ingest/idempotency.py - the fingerprint: the hash of the tenant's current doc_keys, re-computed on every change",
                    block("services/ingest/idempotency.py", "def corpus_fingerprint(", end="def refresh_fingerprint(")
                    + "\n\n" + block("services/ingest/idempotency.py", "def refresh_fingerprint(", n=11)),
    "caches": ("services/rag-api/cache_manager.py - stale_against(); services/rag-api/semantic_cache.py - _alive(): the two caches' tests",
               block("services/rag-api/cache_manager.py", "    def stale_against(self, rec: dict, tenant_id: str) -> str | None:", n=9)
               + "\n...\n" + block("services/rag-api/semantic_cache.py", "def _alive(", end="def lookup(")),
    "walk_tf": ("terraform/reconcile.tf - the nightly walk: declared only with the switch, one task, no retry, 23:30 IST",
                block("terraform/reconcile.tf", 'variable "reconcile_job" {', n=5) + "\n...\n"
                + block("terraform/reconcile.tf", "  template {", n=6) + "\n...\n"
                + block("terraform/reconcile.tf", "# 23:30 IST, after documind-off has floored the lane", n=7)),
    "rej_windows": ("services/ingest/main.py - the kit's record, 12 September 2026: whole-document windows, tried and measured",
                    block("services/ingest/main.py", "# A handbook's sections (12 September 2026):", n=4)),
    "rej_delete": ("services/ingest/idempotency.py - the kit's record, 11 September 2026: a re-issue retires, it never deletes",
                   block("services/ingest/idempotency.py", "# ------------------------------------------------------------------------------ the ledger", n=7)),
    "rej_retention": ("services/ingest/main.py - 12 September 2026: one deleter, on a schedule; terraform/variables.tf - its floor",
                      block("services/ingest/main.py", "# Retention (12 September 2026):", n=4) + "\n...\n"
                      + block("terraform/variables.tf", "# How long a retired chunk row stays before the TTL policy", n=11)),
    "rej_path": ("services/ingest/reconcile.py - the kit's record, 11 September 2026: one ingestion path, not two",
                 block("services/ingest/reconcile.py", '"""The ledger\'s full reconciliation (12.5, 11 September 2026)', n=1) + "\n...\n"
                 + block("services/ingest/reconcile.py", "The worker handles the incremental case on every object.finalized.", n=7)),
    "undated": ("terraform/eventarc.tf, terraform/vector.tf - two more the kit records, without a date",
                block("terraform/eventarc.tf", "# record, field for field. An earlier draft declared an Eventarc trigger", n=3) + "\n...\n"
                + block("terraform/vector.tf", "  # STREAM_UPDATE, not BATCH_UPDATE.", n=4)),
    "poison": ("services/ingest/main.py - a message the worker can never parse: a 400",
               block("services/ingest/main.py", "    except (KeyError, ValueError, ValidationError) as e:", n=7)),   # the comment grew a line (13 October 2026)
    "dlq_alert": ("terraform/alerts.tf - the one policy on the ingest bus reads the dead-letter subscription",
                  block("terraform/alerts.tf", "# The dead-letter queue, watched (24 September 2026, lesson 11.5).", n=15)),
    "walk_alerts": ("Makefile - the walk's switch; terraform/alerts.tf - the two policies that exist only with it",
                    block("Makefile", "# 12.5's ledger (11 September 2026): the API retrieves only chunks the ledger marks current", n=4)
                    + "\n...\n" + block("terraform/alerts.tf", 'resource "google_monitoring_alert_policy" "reconcile_drift" {', n=3)
                    + "\n...\n" + block("terraform/alerts.tf", 'resource "google_monitoring_alert_policy" "reconcile_failed" {', n=3)),
    "backlog_alert": ("terraform/alerts.tf - the main subscription's backlog, watched since 13 October 2026",
                      block("terraform/alerts.tf", "# The main subscription's backlog, watched (13 October 2026", end="  notification_channels")),
    "lease": ("services/ingest/idempotency.py - the claim's lease: the deadline and a minute (13 October 2026)",
              block("services/ingest/idempotency.py", "# The claim's lease (13 October 2026", n=11)),
    "ingest_metric": ("terraform/alerts.tf - the verdicts the lifecycle metric counts, and not a refused delivery",
                      block("terraform/alerts.tf", 'resource "google_logging_metric" "ingest_events" {', n=8)),
    "release": ("services/ingest/idempotency.py - release(): the claim given back, on an exception",
                block("services/ingest/idempotency.py", "def release(db: firestore.Client, doc_key: str, error: str) -> None:", n=11)),
    "decide": ("services/ingest/reconcile.py - decide_bytes(): what the walk does with an object's bytes",
               block("services/ingest/reconcile.py", "def decide_bytes(", end="def drift_of(")),
    "cache_stale": ("services/rag-api/cache_manager.py - generate_config_kwargs(): a stale pack is a log line",
                    block("services/rag-api/cache_manager.py", "        moved = self.stale_against(rec, tenant_id)", n=5)),
    "ids": ("services/ingest/contracts.py - chunk_id(): the id names the version, so every row and datapoint is new",
            block("services/ingest/contracts.py", "        # The id names the VERSION and the position;", n=4)),
    "version_check": ("evals/run_eval.py - the version row's offline check: the rows move with the document",
                      block("evals/run_eval.py", '        if row["shape"] == "version":', n=18)),
    "anchors": ("evals/run_eval.py - check_anchors(): files and whole texts, never a chunk",
                block("evals/run_eval.py", "def check_anchors(golden: list[dict], corpus: dict) -> list[str]:", n=10)),
    "reindex_gate": ("commands/reindex.sh - a reindex is a release: the gate first",
                     block("commands/reindex.sh", '"$PY" evals/run_eval.py --source "$OBJ" >/dev/null', n=1)),
    "first_undo": ("services/ingest/idempotency.py - reactivate(): what the first undo did, 12 September 2026",
                   block("services/ingest/idempotency.py", "    Verified before anything is flipped (12 September 2026).", n=7)),
    "first_planner": ("services/ingest/reconcile.py - what the first planner did, 12 September 2026",
                      block("services/ingest/reconcile.py", "Two states the walk leaves alone (12 September 2026).", n=7)),
}
E_ = {k: v[1] for k, v in EXCERPTS.items()}
assert E_["notification"].count('event_types    = ["OBJECT_FINALIZE"]') == 1 and "max_delivery_attempts = 12" in E_["notification"]
assert E_["guard"].rstrip().endswith('return {"status": "stale", "generation": msg.generation, "ledger_generation": older}')
assert E_["claim"].rstrip().endswith("return True") and 'retakes = ("failed", "superseded") if retake else ("failed",)' in E_["claim"]
assert E_["chunker"].rstrip().endswith("By section it reuses 281 of 283.")
assert E_["carry"].rstrip().endswith('return vectors, {"reused": len(chunks) - len(misses), "embedded": len(misses)}')
assert E_["swap"].rstrip().endswith('remove_datapoints(INDEX_NAME, gone["retired_ids"])')
assert E_["fingerprint"].rstrip().endswith("return fp")
assert E_["caches"].rstrip().endswith("return exp is None or exp > now                  # expired entries wait for the TTL policy; they are not served")
assert '  schedule    = "30 23 * * *"' in E_["walk_tf"] and "      timeout         = \"1200s\"" in E_["walk_tf"] and "max_retries     = 0" in E_["walk_tf"]
assert E_["rej_windows"].rstrip().endswith("By section it reuses 281 of 283.")
assert "Retiring is a flag, never a delete" in E_["rej_delete"] and E_["rej_delete"].rstrip().endswith("nothing is re-embedded.")
assert "condition     = var.retention_days >= 1 && var.retention_days <= 3650" in E_["rej_retention"]
assert "so there is one ingestion path, not two" in flat(E_["rej_path"])
assert UNDATED_EV in E_["undated"] and "absent for hours and nothing reports an error." in E_["undated"]
assert E_["poison"].rstrip().endswith('raise HTTPException(400, "unparseable message")')
assert "${google_pubsub_subscription.ingest_dlq_sub.name}" in E_["dlq_alert"] and "num_undelivered_messages" in E_["dlq_alert"]
assert "RECONCILE_JOB   ?= false" in E_["walk_alerts"] and E_["walk_alerts"].count("count        = var.reconcile_job ? 1 : 0") == 2
assert 'jsonPayload.event=~"^ingest_(' + "|".join(COUNTED) + ')$"' in E_["ingest_metric"]
assert "oldest_unacked_message_age" in E_["backlog_alert"] and E_["backlog_alert"].rstrip().endswith("}")
assert E_["lease"].rstrip().endswith("BATCH_LEASE_SECONDS = 7200 + 60")
assert E_["release"].rstrip().endswith('"failed_at": firestore.SERVER_TIMESTAMP}, merge=True)')
assert E_["decide"].rstrip().endswith('return "reingest"')
assert E_["cache_stale"].rstrip().endswith("return {}")
assert E_["version_check"].rstrip().endswith("continue")
assert E_["anchors"].rstrip().endswith("return bad")
assert "the source was left with no current version at all" in flat(E_["first_undo"])
assert "Neither counts as drift." in E_["first_planner"]
fill = filler(EXCERPTS, window)

# ================================================================== the numbers the parts state
NEXT_TITLE = esc(NEXT)
STATS = {
    "N_COMPONENTS": word(len(COMPONENTS)), "N_DIMS": word(len(RUBRIC_DIMS)), "POINTS": str(POINTS), "PASS": str(PASS),
    "N_ST_W": word(N_ST), "N_SCN": word(len(SCENARIOS)), "N_COMBOS": str(len(COMBOS)),
    "RETENTION": str(RETENTION), "RET_MIN": str(RET_MIN), "RET_MAX": f"{RET_MAX:,}",
    "TOPIC": TOPIC, "SUB": SUB_NAME, "DLQ_TOPIC": DLQ_TOPIC, "EVENT_TYPE": EVENT_TYPES[0],
    "IN_FLIGHT": str(rs.IN_FLIGHT), "ACK": str(rs.ACK_DEADLINE), "ATTEMPTS": str(rs.MAX_ATTEMPTS),
    "ATTEMPTS_W_CAP": word(rs.MAX_ATTEMPTS).capitalize(), "MIN_BACKOFF": str(rs.MIN_BACKOFF), "MAX_BACKOFF": str(rs.MAX_BACKOFF),
    "DLQ_BOUND": f"{rs.DLQ_BOUND_S:,}", "DLQ_FOR": str(DLQ_FOR_S), "DRIFT_FOR": str(DRIFT_FOR_H),
    "WALK_AT": WALK_AT, "WALK_S": f"{rs.WALK_SECONDS:,}", "TIMEOUT": str(rs.WORKER_TIMEOUT),
    "N_HB": str(N_HB), "REUSED": str(ER["reused"]), "EMBEDDED": str(ER["embedded"]), "EMBEDDED_W": word(ER["embedded"]),
    "CHARS": f"{CHARS:,}", "WIN_N": str(WIN_N), "WIN_REUSED_W": word(WIN_REUSED), "WIN_CHARS": f"{WIN_CHARS:,}",
    "WIN_TIMES": f"{WIN_CHARS / CHARS:,.0f}", "SEC_RS": f"{SEC_RS:.4f}", "WIN_RS": f"{WIN_RS:.2f}", "EDIT_WRITES": f"{EDIT_WRITES:,}",
    "N_ACME": str(N_ACME), "FP0": short(FP0), "DK1": DK1[:13] + "...", "DK2": DK2[:13] + "...", "TTL_H": str(TTL_H),
    "POLICY_ANY": " and ".join(t for t, p in POLICIES if p == "any"), "POLICY_IN": " and ".join(t for t, p in POLICIES if p == "in"),
    "AT_DEFAULTS": str(AT_DEFAULTS), "WITH_WALK": str(WITH_WALK),
    "N_INGEST_DEFAULT_CAP": word(sum(1 for p in INGEST_POL if not p["gate"])).capitalize(),
    "N_INGEST_POL_W": word(len(INGEST_POL)), "N_INGEST_DEFAULT_W": word(sum(1 for p in INGEST_POL if not p["gate"])),
    "D_BACKLOG": DISPLAY["ingest_backlog"], "BACKLOG_MIN": str(BACKLOG_S // 60),
    "BACKLOG_FOR_MIN": word(BACKLOG_FOR_S // 60), "LEASE": str(LEASE_S), "BATCH_LEASE": f"{BATCH_LEASE_S:,}",
    "D_DLQ": DISPLAY["dlq_depth"], "D_FAILED": DISPLAY["ingest_failed"], "D_DRIFT": DISPLAY["reconcile_drift"],
    "D_RFAILED": DISPLAY["reconcile_failed"], "D_PIN": DISPLAY["doc_type_pin_miss"],
    "KEEP_RS": f"{KEEP_RS:.2f}", "HB_MB": f"{HB_BYTES / 1e6:.1f}", "REWRITE_1": f"{REWRITE_MAX[1]:,}", "REWRITE_10": f"{REWRITE_MAX[10]:,}",
    "PRICE_DATE": PRICE_DATE, "USD_INR": str(rs.USD_INR), "COMPACT_DAYS": word(rs.COMPACT_DAYS), "COMPACTIONS": word(rs.COMPACTIONS_30D),
    "FP_CROSS": f"{FP_CROSS:,}", "FP_10M_RS": f"{COST[10_000_000]['fp']:.2f}", "FP_10M_RATE": f"{r0(COST[10_000_000]['fp_rate']):,}",
    "FP_1M_RATE": f"{r0(1_000_000 / rs.WORKER_TIMEOUT):,}", "FP_1M_RS": f"{rs.inr(1_000_000 * rs.FS_USD['read']):.2f}",
    "WALK_1M_RATE": f"{r0(3_000_000 / rs.WALK_SECONDS):,}",
    "STAND_1K": rupees(COST[1_000]["standing"]), "EDIT_1K": f"{COST[1_000]['edit']:.2f}", "BREAK_1K": f"{COST[1_000]['breakeven']:,.0f}",
    "COMPACT_10M": rupees(COST[10_000_000]["compact"]), "SERVE_10M": rupees(COST[10_000_000]["serve"]),
    "EDIT_10M": f"{COST[10_000_000]['edit']:.2f}",
    "N_THRESH": str(N_THRESH), "N_REQUIRED": str(N_REQUIRED), "N_SCOPE": str(len(IN_SCOPE)), "N_GOLDEN": str(len(GOLDEN)),
    "COST_TABLE": COST_TABLE, "EDIT_TABLE": EDIT_TABLE, "LIMITS_TABLE": LIMITS_TABLE,
    "PANEL_OPTIONS": PANEL_OPTIONS, "PANEL_SWITCHES": SW_SELECTS, "PANEL_STATIONS": PANEL_STATIONS, "PANEL_OUT": esc(DEF_OUT),
    "NEXT_TITLE": NEXT_TITLE, **WIN_,
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ================================================================== the panel's script: it shows what the build computed, nothing more
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  function $(id){ return document.getElementById(id); }
  var sel = $('rp-change'), path = $('rp-path'), out = $('rp-out');
  if (!sel || !path || !out) return;
  var sw = D.sw.map(function(k){ return $('rp-' + k); });
  function draw(){
    var rows = D.p[sel.value]; if (!rows) return;
    var i = 0;
    sw.forEach(function(el, k){ var vals = D.vals[D.sw[k]]; i = i * vals.length + Math.max(0, vals.indexOf(el ? el.value : vals[0])); });
    var row = rows[i];
    D.st.forEach(function(key, n){
      var li = path.querySelector('[data-st="' + key + '"]'); if (!li) return;
      var c = row[n];
      li.className = 'rp-st' + (c[0] ? ' ' + D.states[c[0]] : '');
      li.querySelector('.rp-t').textContent = D.t[c[1]];
      li.querySelector('.rp-c').textContent = D.t[c[2]];
    });
    out.textContent = D.t[row[row.length - 1]];
  }
  [sel].concat(sw).forEach(function(el){ if (el) el.addEventListener('change', draw); });
  draw();
})();
</script>
""".replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
# the script's index is the COMBOS order: walk, batch, cache, region, each in its listed order
assert [list(c.values()) for c in COMBOS] == [[w, b, c, r] for w in (False, True) for b in (False, True) for c in (False, True) for r in ("any", "in")]

# node runs the page's own script against a stand-in DOM, for every change under every setting of the switches: each
# station's class, text and note, and the outcome line, must be what stations() computed, character for character
NODE = r"""
var els = {}, st = {}, listeners = [];
function sel(v){ return {value: v, addEventListener: function(t, f){ if (t === 'change') listeners.push(f); }}; }
els['rp-change'] = sel('edit');
__SW__.forEach(function(k){ els['rp-' + k] = sel(__VALS__[k][0]); });
els['rp-path'] = {querySelector: function(q){ var k = /data-st="(\w+)"/.exec(q)[1];
  if (!st[k]) st[k] = {className: '', t: {textContent: ''}, c: {textContent: ''},
                      querySelector: function(s){ return s === '.rp-t' ? this.t : this.c; }};
  return st[k]; }};
els['rp-out'] = {textContent: ''};
var document = {getElementById: function(id){ return els[id] || null; }};
__SCRIPT__
var res = [];
__SCN__.forEach(function(scn){
  __COMBOS__.forEach(function(c){
    els['rp-change'].value = scn;
    __SW__.forEach(function(k, n){ els['rp-' + k].value = c[n]; });
    listeners[0]();
    res.push([__ST__.map(function(k){ return [st[k].className, st[k].t.textContent, st[k].c.textContent]; }), els['rp-out'].textContent]);
  });
});
process.stdout.write(JSON.stringify(res));
"""
_script = JS.split("<script>", 1)[1].rsplit("</script>", 1)[0].replace("<\\/", "</")
_node_src = (NODE.replace("__SCRIPT__", _script).replace("__SW__", json.dumps([k for k, _ in SWITCHES]))
             .replace("__VALS__", json.dumps(DATA["vals"])).replace("__SCN__", json.dumps([k for k, _ in SCENARIOS]))
             .replace("__COMBOS__", json.dumps([[str(v).lower() for v in c.values()] for c in COMBOS]))
             .replace("__ST__", json.dumps([k for k, _, _ in ST])))
_node = subprocess.run(["node", "-"], input=_node_src, capture_output=True, text=True, encoding="utf-8")
assert _node.returncode == 0, _node.stderr[-1500:]
_got = json.loads(_node.stdout)
_want = [stations(k, c) for k, _ in SCENARIOS for c in COMBOS]
assert len(_got) == len(_want) == len(SCENARIOS) * len(COMBOS)
for (sts, out_line), (g_sts, g_out) in zip(_want, _got):
    assert g_out == out_line, (g_out, out_line)
    for (state, t, n), (g_cls, g_t, g_n) in zip(sts, g_sts):
        assert (g_cls, g_t, g_n) == ("rp-st" + STATE_CSS[state], t, n), ((g_cls, g_t, g_n), (state, t, n))
N_NODE = len(_got)
STATS["N_NODE"] = str(N_NODE)

body = "".join([fill(subst(pb.part(LESSON, "a"))), setup, fill(subst(pb.part(LESSON, "b"))), fill(subst(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the edit {ER['reused']} reused, {ER['embedded']} embedded, {ER['retired']} retired, {EDIT_WRITES} writes, {EDIT_READS} reads | "
      f"fingerprint {short(FP0)} -> {short(FP2)} -> {short(U['fp'])} | {len(SCENARIOS)} changes x {len(COMBOS)} switch settings, "
      f"{N_DISTINCT} distinct panels, {len(TEXTS)} texts | policies {AT_DEFAULTS} at the defaults, {WITH_WALK} with the walk | "
      f"one edit Rs {COST[1_000]['edit']:.2f} at 1k, Rs {COST[10_000_000]['edit']:.2f} at 10M | "
      f"the panel's script agrees with the build on {N_NODE} settings (node)")
