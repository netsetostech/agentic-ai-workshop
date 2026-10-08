"""Build lesson 7.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Compare quality and test update/withdrawal freshness. Two questions about a managed copy. Is it as good? evals/ablate.py
--arms all scores the golden rows' anchors through the kit's four retrieval arms and the two stores (recall at the
arm's depth, recall@5 after the reranker, MRR, and a miss list that says where each lost anchor went). Is it current?
The mirror follows the ledger through four events, each by the kit's own path: a new version (the worker's swap,
after_swap: the text in, the replaced version out), the undo (the worker's reactivation, after_undo: the text re-sent
from the rows), a withdrawal (make retire, reconcile.py: every store's copy deleted) and a restore (make restore: the
object rewritten, the worker's reactivation again); make managed-status holds the stores against the ledger after
each. The drills run on zeta, whose corpus has no pictures, so make managed-status can say `in sync` (lesson 7.3:
it counts media versions the mirror never copies, so acme never can).

Build-time proof: every live cell ran the kit's own code over a stand-in lane (lane154.py, beside this file): the
ingest worker's push handler for every upload, reconcile.py for make retire and make restore, managed.py for make
managed-status, evals/ablate.py for make ablate, rag-api for the questions. Firestore and Cloud Storage are JSON files,
RAG Engine and Vertex AI Search are stateful stand-ins (an import is long-running: a document is visible after two
listings), Gemini, the Ranking API and BM25 rank by word overlap, so the ablation's numbers are the stand-in's and the
page says so. The panel's lifecycle is the kit's: every event sequence it can play was replayed through the real
worker and reconcile.py and compared step by step.
"""
import html
import json
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "7.4"
title = "<title>Lesson 7.4 Compare quality and test update/withdrawal freshness - as good, and as current | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8154
API = "https://documind-api-NUMBER.asia-south1.run.app"
NAME = "zeta/hr_policy_zeta_2026.md"
Q = "How long is the notice period for a confirmed employee?"
MANAGED, WORKER, REC, ABL, IDEM = ("services/ingest/managed.py", "services/ingest/main.py", "services/ingest/reconcile.py",
                                   "evals/ablate.py", "services/ingest/idempotency.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.lf-btns{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:8px;margin:6px 0;}
.lf-btns button{font:inherit;font-size:14px;min-height:44px;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;text-align:left;}
.lf-btns button:active{transform:translateY(1px);}
@media (hover:hover) and (pointer:fine){.lf-btns button:hover{border-color:var(--teal-dark);}}
.lf-ck{display:flex;align-items:center;gap:10px;min-height:44px;font-size:var(--small-size);color:var(--navy);}
.lf-ck input{width:22px;height:22px;margin:0;accent-color:var(--teal-dark);flex:none;}
.lf-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:0 10px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
.lf-steps{margin:0;padding-left:1.4em;font-size:12.5px;}
.lf-steps li{margin:3px 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "arms": ("evals/ablate.py - the six arms: one knob each, the two stores last",
             block(ABL, "def arms(lane: Lane, keys=DEFAULT_ARMS) -> list:", n=10)),
    "source_of": ("evals/ablate.py - a store's context scored against its source, through the kit's rows",
                  block(ABL, "    def source_of(self, tenant: str, doc_key: str) -> str:", n=8)),
    "undo": ("services/ingest/main.py - the undo: the rows flipped back, the newer version retired, the stores told",
             block(WORKER, "            back = reactivate(_db, doc.tenant_id, doc.gcs_uri, doc.doc_key)", n=12)),
    "after_undo": ("services/ingest/managed.py - after_undo(): the text comes off the version's own rows",
                   block(MANAGED, "    def after_undo(self, tenant_id: str, gcs_uri: str, doc_key: str, gone: dict, meta: dict | None = None) -> None:", n=9)),
    "retire": ("services/ingest/reconcile.py - make retire: the rows retired, every store's copy deleted, the ledger row a tombstone",
               block(REC, "        gone = retire_previous(db, tenant, uri, None, expire_at=expire_at)", n=4)),
    "restore": ("services/ingest/reconcile.py - make restore: the tombstone lifted to retired, the object rewritten onto itself",
                block(REC, '        ref.set({"status": "retired", "restored_at": firestore.SERVER_TIMESTAMP,', n=3)),
}
assert EXCERPTS["arms"][1].rstrip().endswith("return [every[k] for k in keys]") and '"vertex_search": (' in EXCERPTS["arms"][1]
assert EXCERPTS["source_of"][1].rstrip().endswith("return self._sources[doc_key]") and "current" not in EXCERPTS["source_of"][1]
assert EXCERPTS["undo"][1].rstrip().endswith('{"generation": str(msg.generation), "name": msg.name})') and "_mirror.after_undo(" in EXCERPTS["undo"][1]
assert EXCERPTS["after_undo"][1].rstrip().endswith('self.stamp(tenant_id, meta.get("name"), doc_key, held)') and "version_rows(self.db, tenant_id, doc_key)" in EXCERPTS["after_undo"][1]
assert 'mirror.retired(tenant, gone.get("retired_doc_keys", []), "withdrawn")' in EXCERPTS["retire"][1]
assert EXCERPTS["restore"][1].rstrip().endswith("blob.rewrite(blob)")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MANAGED, WORKER, REC, ABL, IDEM, "Makefile", "terraform/reconcile.tf", "shared/audit_log.py")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
RETIRE_RECIPE = MK[MK.index("\nretire: guard-project"):MK.index("\nrestore: guard-project")]
assert "MANAGED_MIRROR=$(MANAGED_MIRROR) RAG_LOCATION=$(RAG_LOCATION) AUDIT_BUCKET=$(PROJECT)-audit" in RETIRE_RECIPE
assert '"MANAGED_MIRROR" # the managed mirror' in src["terraform/reconcile.tf"] and '"${var.project_id}-audit"' in src["terraform/reconcile.tf"]
assert 'RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))' in src[REC] and "the next night's walk resurrected what a person had taken down" in src[REC]
assert 'log.warning(json.dumps({"event": "mirror_failed"' in src[MANAGED] and "version answers NotFound (0) rather than refusing." in src[MANAGED]
assert "            from rank_bm25 import BM25Okapi" in src[ABL]          # imported per tenant, inside the arm: a missing package fails the arm's rows
# 1. make retire's store deletes leave no line: reconcile.py never configures logging, and the mirror's mirror_ok is INFO
assert "basicConfig" not in src[REC] and "import logging" not in src[REC] and 'log.info(json.dumps({"event": "mirror_ok"' in src[MANAGED]
assert '_b().blob(f"{d.year}/{d.month:02d}/{d.day:02d}/"' in src["shared/audit_log.py"] and "{action}-{event['id']}.json" in src["shared/audit_log.py"]
# 2. the ablation's hybrid arm needs rank-bm25, which no requirements file carries
REQS = [p for p in pb.kit_runtime_files("requirements*.txt") if "rank-bm25" in p.read_text(encoding="utf-8") or "rank_bm25" in p.read_text(encoding="utf-8")]
assert not REQS and "from rank_bm25 import BM25Okapi" in src[ABL] and "rank-bm25==0.2.2" in src["Makefile"]
# 3. the managed arms score what a store returns, a version the ledger retired included; the dense arms ask the ledger
assert "self._current(" in src[ABL].split("def dense(", 1)[1].split("def hybrid(", 1)[0]
assert "vector_distance_threshold=0.5" in src[ABL].split("def rag_engine(", 1)[1].split("def vertex_search(", 1)[0]
# 4. nothing waits for a Vertex AI Search import; the ledger is stamped on the request (7.3), and no make target polls
assert 'or "import requested"   # an LRO: minutes; the walk verifies' in src[MANAGED]
assert re.findall(r"mirror\.(\w+)\(", src[REC]) == ["retired", "retired"]
# 5. the recorded measurement the page quotes, from ablate.py's own docstring
MEASURED = "dense 5 alone 0.91 recall@5 / 0.81 MRR; the\nlane's dense 20 -> rerank 5 0.96 / 0.91; dense 50 -> rerank 5 0.99 / 0.94"
assert MEASURED in src[ABL] and "Measured on 8 Sept 2026 from Cloud Shell, 43 rows" in src[ABL]
assert "print(json.dumps({\"event\": \"reconcile_withdrawn\", \"gcs_uri\": uri, \"fingerprint\": fp, **gone," in src[REC]   # the line carries every retired id
# 6. ablate.py's docstring is behind its golden set and its arms: 43 rows and one managed arm (the build counts 47, and there are two)
assert "# the 43 anchored rows, four arms (~3 min)" in src[ABL] and "--arms all   # the four and the managed arm (P9.6: needs the mirror)" in src[ABL]
assert 'ARM_KEYS = ("dense5", "dense20", "dense50", "hybrid", "rag_engine", "vertex_search")' in src[ABL]
# what the page says of the scoring: the anchor is matched on the source's path and the text, the reranker is the fast one
assert 'return (chunk.get("source_uri", "") + " " + chunk.get("text", "")).lower()' in src[ABL] and 'model="semantic-ranker-fast-004"' in src[ABL]
assert "CHUNK_SIZE, CHUNK_OVERLAP = 512, 100" in src[MANAGED]
GOLD = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
assert sorted(__import__("collections").Counter(r["tenant"] for r in GOLD if r.get("must_retrieve")).items()) == [("acme", 40), ("globex", 2), ("zeta", 5)]
assert ["NP-03", "hr_policy_2026"] in [r["must_retrieve"] for r in GOLD]
ABLATE_RECIPE = MK[MK.index("ablate: guard-project\n"):].split("\n\n", 1)[0]
ABLATE_ECHO = ABLATE_RECIPE.split("\n", 1)[1].replace("\t", "").replace("$(PY)", "python").replace("$(PROJECT)", PROJ).replace("$(REGION)", "asia-south1").replace("$(ABLATE_ARGS)", "--arms all") + "\n"
assert ABLATE_ECHO == f"python evals/ablate.py --project {PROJ} --region asia-south1 --arms all\n", ABLATE_ECHO
REINDEX = (KIT / "commands/reindex.sh").read_text(encoding="utf-8")
for piece in ('echo ">> gs://$PROJECT-uploads/$TENANT/$OBJ - waiting for the worker (up to 5 min)"', 'echo ">> event doc_key chunks reused embedded retired effective_from"',
              "sed 's/^/>> retired (doc_keys, chunks, expire days): /'",
              'echo ">> the gate, scoped to this document, on a candidate: make eval-live PROJECT=$PROJECT SOURCE=$OBJ API=<candidate url>"'):
    assert piece in REINDEX, piece

# ------------------------------------------------------------------ the corpus, as evals/upload.sh sends it
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
CAPTIONS = {"annual_report_2026_fig3.png": "Figure 3 of the ACME annual report 2026: a bar chart of revenue by business segment, FY2025 against FY2026.",
            "inv_2026_0412.png": "A tax invoice, INV-2026-0412, raised on ACME: line items, GST and the payment terms.",
            "payment_of_bonus_act_1965_p30.png": "Page 30 of the Payment of Bonus Act, 1965: a printed page of sections on the allocable surplus."}
ROWS, TEXTS, LEDGER, RAG, VS = {}, {}, {}, {"acme": {}, "zeta": {}}, {"acme": {}, "zeta": {}}
N = 0
for tdir in sorted((KIT / "evals/corpus").iterdir()):
    tenant = tdir.name
    TEXTS[tenant] = {}
    for f in sorted(tdir.iterdir()):
        if f.suffix == ".md" and (f.with_suffix(".pdf").exists() or f.with_suffix(".mp4").exists()) or f.name.endswith(".segments.json"):
            continue                                                     # upload.sh's rule: an offline mirror stays home
        if f"{tenant}/{f.name}" == NAME:
            continue                                                     # zeta's handbook: the worker ingests it, below
        data = f.read_bytes()
        sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/{tenant}/{f.name}"
        dk = f"{tenant}_{sha}"
        if f.suffix == ".png":
            ROWS[f"{tenant}:{sha}#0"] = {"tenant_id": tenant, "text": CAPTIONS[f.name], "source_uri": uri, "doc_type": "figure", "kind": "figure",
                                         "doc_key": dk, "locator": "", "current": True}
            LEDGER[f"{tenant}~{f.name}"] = {"tenant_id": tenant, "name": f"{tenant}/{f.name}", "gcs_uri": uri, "doc_key": dk, "status": "indexed",
                                            "generation": "1", "sha256": sha, "chunks": 1}
            continue
        md = f.with_suffix(".md")
        if md.exists():
            text = md.read_text(encoding="utf-8")
        else:                                                            # a PDF with no mirror (the POSH Act): its own text
            import pypdf
            text = "\f".join(p.extract_text() or "" for p in pypdf.PdfReader(str(f)).pages)
        text = re.sub(r"\A<!--.*?-->\s*", "", text, flags=re.S)
        cut = chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown", "slug": f.stem}, tenant)
        for i, c in enumerate(cut):
            ROWS[f"{tenant}:{sha}#{i}"] = {"tenant_id": tenant, "text": c["text"], "source_uri": uri, "doc_type": "unknown", "kind": "text",
                                           "doc_key": dk, "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True,
                                           **({"section": c["section"]} if c.get("section") else {})}
        TEXTS[tenant][dk] = {"text": text, "source_uri": uri, "pdf": f.suffix == ".pdf"}
        held = {"rag_engine": "us-central1", "vertex_search": "global"} if tenant in RAG else {}
        LEDGER[f"{tenant}~{f.name}"] = {"tenant_id": tenant, "name": f"{tenant}/{f.name}", "gcs_uri": uri, "doc_key": dk, "status": "indexed",
                                        "generation": "1", "sha256": sha, "chunks": len(cut), "mirrored": held, "data_region": "in" if tenant == "globex" else "any"}
        if tenant in RAG:
            N += 1
            RAG[tenant][dk] = {"name": f"projects/NUMBER/locations/us-central1/ragCorpora/{tenant}-corpus/ragFiles/{N}", "source_uri": uri}
            VS[tenant][dk] = {"source_uri": uri, "left": 0}
V1 = (KIT / "evals/corpus" / NAME).read_bytes()
assert V1.decode("utf-8").count("serves a notice period of 30 days") == 1
V2 = V1.decode("utf-8").replace("serves a notice period of 30 days", "serves a notice period of 45 days").encode("utf-8")   # what the page's sed writes
K1, K2 = f"zeta_{sha256(V1).hexdigest()}", f"zeta_{sha256(V2).hexdigest()}"

T = Path(tempfile.mkdtemp(prefix="lesson154-"))
shutil.copy(HERE / "lane154.py", T / "lane154.py")
(T / "base.json").write_text(json.dumps({"rows": ROWS, "texts": TEXTS}), encoding="utf-8")
STATE = {k: T / f"{k}.json" for k in ("fs", "gcs", "stores", "logs")}
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T), "LANE154_KIT": str(KIT), "LANE154_BASE": str(T / "base.json"),
       **{f"LANE154_{k.upper()}": str(p) for k, p in STATE.items()}, "PYTHONPATH": str(T), "API": API,
       "AUDIT_BUCKET": f"{PROJ}-audit", "MANAGED_MIRROR": "both", "RAG_LOCATION": "us-central1", "EMBEDDING_MODEL": "text-embedding-005",
       "EMBEDDING_VERSION": "1", "RETENTION_DAYS": "30", "SEARCH_LOCATION": "global"}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "GRAPH_", "SPANNER_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR",
                                           "ROUTING", "SPEND_", "BUDGET_", "EMBED_", "BQ_", "DOCAI_", "BATCH_"))]:
    ENV.pop(k)


def reset(paths: dict, fs: dict, stores: dict, gcs: dict) -> None:
    for k, v in (("fs", fs), ("stores", stores), ("gcs", gcs), ("logs", {"entries": []})):
        paths[k].write_text(json.dumps(v), encoding="utf-8")


reset(STATE, {"tenant_settings": {"acme": {"data_region": "any", "retrieval_backend": "vector"},     # make roster, make up, the setup's pin window
                                  "zeta": {"data_region": "any", "retrieval_backend": "vertex_search"}, "globex": {"data_region": "in"}},
              "sources": LEDGER},
      {"corpora": ["acme", "zeta"], "data_stores": ["acme", "zeta"], "rag": RAG, "vs": VS, "n": N}, {})


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T, argv: tuple = ()) -> str:
    r = subprocess.run([sys.executable, "-", *argv], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


def result_of(out: str):
    return json.loads(out.rsplit("RESULT ", 1)[1])


LANE = "import lane154\nlane154.freeze()\n"


def worker(gen: str, at: str) -> dict:
    return result_of(run_cell(f"import json\nr = lane154.worker({NAME!r}, {gen!r})\nprint('RESULT ' + json.dumps(r))\n", LANE, {"LANE154_NOW": at}))


def upload(data: bytes, at: str) -> str:
    return result_of(run_cell(f"import json\nprint('RESULT ' + json.dumps(lane154.upload({NAME!r}, {data!r})))\n", LANE, {"LANE154_NOW": at}))


def settle(paths: dict = STATE) -> None:
    """The long-running imports finished: every document the data stores hold is visible."""
    st = json.loads(paths["stores"].read_text(encoding="utf-8"))
    for docs in st["vs"].values():
        for e in docs.values():
            e["left"] = 0
    paths["stores"].write_text(json.dumps(st), encoding="utf-8")


# lesson 7.3's lane, at the start of this lesson: zeta's handbook v1 ingested by the worker four days ago, its copies settled
g1 = upload(V1, "2026-09-20T10:00:00+00:00")
setup_run = worker(g1, "2026-09-20T10:00:05+00:00")
assert setup_run["result"]["status"] == "indexed" and setup_run["result"]["chunks"] == 283, setup_run["result"]
settle()


def heredoc(body: str, prefix: str = "", args: str = "") -> str:
    return f"{prefix}python - {args}<<'PY'\n{body}\nPY"


# ------------------------------------------------------------------ the cells
FRESH_PY = """import datetime as dt, json, os, re, subprocess, sys, time, urllib.request
from google.cloud import firestore, storage
P, API, SINCE, WANT = os.environ["PROJECT"], os.environ["API"], os.environ["SINCE"], sys.argv[1]
NAME, Q = "zeta/hr_policy_zeta_2026.md", "How long is the notice period for a confirmed employee?"
short = lambda s: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\\1...", s)
since = dt.datetime.fromisoformat(SINCE.replace("Z", "+00:00"))
audit, events = storage.Client(project=P).bucket(f"{P}-audit"), []
for day in sorted({since.date(), dt.datetime.now(dt.timezone.utc).date()}):
    for b in audit.list_blobs(prefix=f"{day:%Y/%m/%d}/zeta/doc.mirror-"):
        if b.time_created >= since:
            events.append(json.loads(b.download_as_text()))
print(f"the mirror's doc.mirror events for zeta since {SINCE} (the audit bucket):")
for e in sorted(events, key=lambda e: e["ts"]):
    m = e["meta"]
    print(f"  {e['ts'][11:19]}  {m['op']:17} {m['store']:13} {m['region']:11} {short(e['target']['id'])}")
if not events:
    print("  none")
print(f"make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook {WANT}):")
db, start, last = firestore.Client(project=P), time.monotonic(), None
while True:
    out = subprocess.run(["make", "-s", "managed-status", f"PROJECT={P}", "TENANT_ONLY=zeta"], capture_output=True, text=True, check=True).stdout
    lines = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    status = (db.collection("sources").document(NAME.replace("/", "~")).get().to_dict() or {}).get("status")
    state = f"handbook {status}; " + "; ".join(s["store"] + " " + s["status"] + "".join(
        f", {k} {' '.join(short(x) for x in s[k + '_doc_keys'])}" for k in ("missing", "orphan") if s.get(k + "_doc_keys")) for s in lines)
    t = int(time.monotonic() - start)
    if state != last:
        print(f"  {t // 60}:{t % 60:02d}  {state}")
        last = state
    if status == WANT and lines and all(s["status"] == "in sync" for s in lines):
        break
    if t > 900:
        raise SystemExit("still apart after 15 minutes: make managed-status TENANT_ONLY=zeta")
    time.sleep(20)
for s in lines:
    print(json.dumps(s))
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "zeta"}).encode(),
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
a = json.load(urllib.request.urlopen(req, timeout=180))
print(f"zeta, answered from {a['stages']['retrieval_backend']}: {a['answer']}")
for c in a["citations"]:
    print(f"  cites {short(c['chunk_id'])}")"""
FRESH_FN = ("fresh154() {   # fresh154 STATUS: the mirror's audit trail since $SINCE, make managed-status until the stores match, zeta asked\n"
            + heredoc(FRESH_PY, args='"$@" ') + "\n}")
SED = "sed 's/serves a notice period of 30 days/serves a notice period of 45 days/' evals/corpus/zeta/hr_policy_zeta_2026.md > \"$HOME/hr_policy_zeta_2026_v2.md\""
SINCE_LINE = "export SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CELLS = {
    "ablate": ('python -m pip install -q rank-bm25==0.2.2      # the hybrid arm\'s BM25 (lesson 2.2 installed it; safe to repeat)\n'
               'make ablate PROJECT="$PROJECT" ABLATE_ARGS="--arms all"'),
    "update": (SED + "\n" + SINCE_LINE + "\n"
               'make reindex PROJECT="$PROJECT" TENANT=zeta FILE="$HOME/hr_policy_zeta_2026_v2.md" NAME=hr_policy_zeta_2026.md\n'
               + FRESH_FN + "\nfresh154 indexed"),
    "undo": (SINCE_LINE + "\n" 'make reindex PROJECT="$PROJECT" TENANT=zeta FILE=evals/corpus/zeta/hr_policy_zeta_2026.md NAME=hr_policy_zeta_2026.md\n'
             "fresh154 indexed"),
    "retire": SINCE_LINE + "\n" 'make retire PROJECT="$PROJECT" SOURCE=zeta/hr_policy_zeta_2026.md\nfresh154 withdrawn',
    "restore": SINCE_LINE + "\n" 'make restore PROJECT="$PROJECT" SOURCE=zeta/hr_policy_zeta_2026.md\nfresh154 indexed',
}

# ---- step 3: the four events through the kit's own Mirror and status(), with two stand-in stores and a stand-in ledger
RULES_PY = """import json, logging, sys
from types import SimpleNamespace
sys.path[:0] = ["services/ingest", "."]
import managed                                        # the kit's mirror and make managed-status's check; the stores and the ledger are stand-ins


class Brief(logging.Handler):                         # the mirror's JSON lines, one short line each
    def emit(self, r):
        j = json.loads(r.getMessage())
        print(f"     {j['event']:13} {j.get('store', ''):13} {j.get('op', ''):17} {j.get('result', j.get('error', ''))}")
logging.getLogger("documind.ingest").addHandler(Brief())
logging.getLogger("documind.ingest").setLevel(logging.INFO)


class Store:                                          # a store: upsert, delete, and the listing make managed-status reads
    def __init__(self, name, region):
        self.name, self.region, self.docs, self.fail_next = name, region, {}, False

    def upsert(self, tenant, doc_key, source_uri, text, meta):
        if self.fail_next:
            self.fail_next = False
            raise TimeoutError("the import did not finish")
        self.docs[doc_key] = text
        return f"{doc_key} uploaded, {len(text)} characters"

    def delete(self, tenant, doc_key):
        return int(self.docs.pop(doc_key, None) is not None)

    def listing(self, tenant):
        return dict.fromkeys(self.docs)


class Table:                                          # the two collections the mirror and status() read: chunks and sources
    def __init__(self, rows, filters=()):
        self.rows, self.filters = rows, filters

    def where(self, field, op, value):
        return Table(self.rows, self.filters + ((field, value),))

    def stream(self):
        return [SimpleNamespace(id=k, to_dict=lambda d=d: dict(d)) for k, d in self.rows.items()
                if all(d.get(f) == v for f, v in self.filters)]


db = SimpleNamespace(chunks={}, sources={})
db.collection = lambda name: Table(getattr(db, name))
stores = [Store("rag_engine", "us-central1"), Store("vertex_search", "global")]
m = managed.Mirror(db, stores, "both", policy_for=lambda tenant: "any", audit=lambda *a, **kw: None)
URI = "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md"
V = {"v1": ["# Zeta HR policy", "A confirmed employee serves a notice period of 30 days."]}
V["v2"] = [V["v1"][0], V["v1"][1].replace("30 days", "45 days")]


def current(key, status="indexed"):                   # the rows after the worker's swap (or make retire), and the ledger row
    for k in V:
        for i, text in enumerate(V[k]):
            db.chunks[f"zeta:{k}#{i}"] = {"tenant_id": "zeta", "doc_key": k, "text": text, "kind": "text", "current": k == key and status == "indexed"}
    db.sources["zeta~hr_policy_zeta_2026.md"] = {"tenant_id": "zeta", "doc_key": key, "status": status}


def doc(key):
    return SimpleNamespace(tenant_id="zeta", doc_key=key, gcs_uri=URI, doc_type="policy", effective_from=None)


def check():
    for s in managed.status(db, stores, "zeta"):
        print(f"   make managed-status: {s['store']:13} {s['status']}" + "".join(f", {k} {s[k + '_doc_keys']}" for k in ("missing", "orphan") if s[k + "_doc_keys"]))


print("1. v1 is ingested: the worker's swap, then after_swap()")
current("v1"); m.after_swap(doc("v1"), "\\n\\n".join(V["v1"]), {})
check()
print("2. v2 replaces it: after_swap(), with v1 in the swap's retired_doc_keys")
current("v2"); m.after_swap(doc("v2"), "\\n\\n".join(V["v2"]), {"retired_doc_keys": ["v1"]})
check()
print("3. the undo, v1's bytes again: the worker flips the rows back, then after_undo(), which is given no text")
current("v1"); m.after_undo("zeta", URI, "v1", {"retired_doc_keys": ["v2"]})
print("   the stores now hold for v1:", {s.name: "..." + s.docs["v1"].split("serves ")[1] for s in stores})
check()
print("4. make retire: the rows retired, the ledger row withdrawn, then retired(..., 'withdrawn')")
current("v1", "withdrawn"); m.retired("zeta", ["v1"], "withdrawn")
check()
print("5. make restore, while Vertex AI Search refuses one import: the worker's reactivation, then after_undo()")
stores[1].fail_next = True
current("v1"); m.after_undo("zeta", URI, "v1", {"retired_doc_keys": []})
check()"""
CELLS["rules"] = heredoc(RULES_PY)
OUT_RULES = run_cell(RULES_PY, cwd=KIT)
assert "   make managed-status: vertex_search drift, missing ['v1']" in OUT_RULES and "mirror_failed vertex_search upsert            TimeoutError" in OUT_RULES, OUT_RULES
assert OUT_RULES.count("delete:superseded 1") == 4 and OUT_RULES.count("delete:withdrawn  1") == 2 and OUT_RULES.count(" in sync") == 9, OUT_RULES
assert "{'rag_engine': '...a notice period of 30 days.', 'vertex_search': '...a notice period of 30 days.'}" in OUT_RULES, OUT_RULES

# ---- step 4: the ablation, the kit's ablate.py on the lane (its latency column is the stand-in's clock, so shown as ...)
ABL_PY = ("import runpy, sys, time\nlane154.install()\n_t = [1758700000.0]\ntime.time = lambda: (_t.__setitem__(0, _t[0] + 0.137), _t[0])[1]\n"
          "time.sleep = lambda s: None\nsys.argv = ['ablate.py', '--project', %r, '--region', 'asia-south1', '--arms', 'all']\n"
          "try:\n    runpy.run_path('evals/ablate.py', run_name='__main__')\nexcept SystemExit as e:\n    print('EXIT', e.code)\n") % PROJ
abl = run_cell(ABL_PY, LANE, cwd=KIT)
assert abl.rstrip().endswith("EXIT 0"), abl[-600:]
abl = abl.rsplit("EXIT 0", 1)[0]
ARM_LINE = re.compile(r"^(?P<arm>\S.*?) +(?P<depth>\d\.\d\d) +(?P<r5>\d\.\d\d) +(?P<mrr>\d\.\d\d) +(?P<rows>\d+) +(?P<p95>\d+)(?P<tail>(?:   \(\d+ rows failed\))?)$", re.M)
ARMS = {m.group("arm").strip(): m for m in ARM_LINE.finditer(abl)}
assert len(ARMS) == 6 and all(m.group("p95") == "137" for m in ARMS.values()), list(ARMS)
OUT = {"ablate": ABLATE_ECHO + ARM_LINE.sub(lambda m: m.group(0)[:m.start("p95") - m.start(0)] + "..." + m.group("tail"), abl)}
A4 = OUT["ablate"]
OUT["rules"] = OUT_RULES
assert A4.splitlines()[1].startswith("47 rows with anchors,"), A4[:300]
for arm in ("rag_engine 20 -> rerank 5  (4.3's corpus, P9.4)", "vertex_search 20 -> rerank 5  (4.4's data store, R4)"):   # the ablation's own labels (notebook-era numbers)
    assert ARMS[arm].group("tail").strip() == "(2 rows failed)" and int(ARMS[arm].group("rows")) <= 45, (arm, ARMS[arm].group(0))
assert "no RAG Engine corpus 'documind-globex'" in A4 and "DataStore documind-globex not found" in A4, A4
N_ROWS = 47
# what step 4's box reads off the stand-in's table: depth is not the knob for the kit's reranked arms, and their misses are the reranker's
for arm in ("dense 20 -> rerank 5   (the lane)", "dense 50 -> rerank 5", "hybrid 20 -> rerank 5  (4.5, not wired)"):
    assert (ARMS[arm].group("depth"), ARMS[arm].group("r5")) == ("1.00", "0.94"), ARMS[arm].group(0)
    tail_ = abl.split(ARMS[arm].group(0), 1)[1].splitlines()[1:5]
    assert [l.endswith("ranked out (in the candidates, not the five)") for l in tail_] == [True, True, True, False], (arm, tail_)
assert ARMS["dense 5, no reranker"].group("r5") == "0.94" and "not retrieved at depth 0" in A4
assert "vector_distance_threshold=0.5" in src[ABL] and "max_extractive_segment_count=3" in src[ABL]

# ---- steps 5 and 6: the four events on zeta's handbook, each by the kit's own path, then fresh154
with socket.socket() as s_:
    assert s_.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
URL = f"http://127.0.0.1:{PORT}"
SERVE = f"import lane154; lane154.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"
LIVE_ENV = {"RETRIEVAL_BACKEND": "vector", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT"}
FRESH_PRELUDE = LANE + "lane154.fake_time()\nlane154.install()\nlane154.fake_cli()\n"


def fresh(since: str, want: str, at: str) -> str:
    """fresh154, against the kit's rag-api on localhost; the server reads the lane's files as they stand."""
    log = T / f"api154-{len(list(T.glob('api154-*')))}.log"
    with open(log, "w", encoding="utf-8") as logf:
        srv = subprocess.Popen([sys.executable, "-c", SERVE], cwd=str(T), env={**ENV, **LIVE_ENV}, stdout=logf, stderr=subprocess.STDOUT)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
                break
            except Exception:                      # noqa: BLE001 - not up yet
                time.sleep(0.2)
        else:
            raise SystemExit("the API did not start: " + log.read_text(encoding="utf-8")[-1500:])
        return run_cell(FRESH_PY, FRESH_PRELUDE, env={"API": URL, "SINCE": since, "LANE154_NOW": at, **LIVE_ENV}, cwd=KIT, argv=(want,))
    finally:
        srv.terminate()
        srv.wait(timeout=20)


def reindex_lines(run: dict, obj: str) -> str:
    """What commands/reindex.sh prints around the worker's line (gcloud's own copy lines are the '...')."""
    line = next(j for j in run["lines"] if j.get("event") in ("ingest_ok", "ingest_reactivated"))
    val = lambda v: "" if v is None else ";".join(map(str, v)) if isinstance(v, list) else str(v)  # noqa: E731 - gcloud's value() format
    out = ("...\n" f">> gs://{PROJ}-uploads/zeta/{obj} - waiting for the worker (up to 5 min)\n"
           ">> event doc_key chunks reused embedded retired effective_from\n"
           ">> " + "\t".join(val(line.get(k)) for k in ("event", "doc_key", "chunks", "reused", "embedded", "retired", "effective_from")) + "\n")
    sup = next((j for j in run["lines"] if j.get("event") == "ingest_superseded"), None)
    if sup:
        out += ">> retired (doc_keys, chunks, expire days): " + "\t".join(val(sup.get(k)) for k in ("retired_doc_keys", "retired_chunks", "expire_days")) + "\n"
    return out + f">> the gate, scoped to this document, on a candidate: make eval-live PROJECT={PROJ} SOURCE={obj} API=<candidate url>\n"


OBJ = NAME.split("/", 1)[1]
# a new version
g2 = upload(V2, "2026-09-24T08:00:10+00:00")
upd = worker(g2, "2026-09-24T08:00:20+00:00")
OUT["update"] = reindex_lines(upd, OBJ) + fresh("2026-09-24T08:00:00Z", "indexed", "2026-09-24T08:01:30+00:00")
UP = OUT["update"]
assert upd["result"] == {"status": "indexed", "chunks": 283, "reused": 282, "embedded": 1}, upd["result"]
assert f">> ingest_ok\t{K2}\t283\t282\t1\t283\t\n" in UP and f">> retired (doc_keys, chunks, expire days): {K1}\t283\t30\n" in UP, UP
# the undo
g3 = upload(V1, "2026-09-24T08:10:10+00:00")
und = worker(g3, "2026-09-24T08:10:20+00:00")
OUT["undo"] = reindex_lines(und, OBJ) + fresh("2026-09-24T08:10:00Z", "indexed", "2026-09-24T08:11:30+00:00")
UN = OUT["undo"]
assert und["result"] == {"status": "reactivated", "doc_key": K1, "chunks": 283}, und["result"]
assert f">> ingest_reactivated\t{K1}\t283\t283\t0\t283\t\n" in UN and "retired (doc_keys" not in UN, UN
# a withdrawal
ret = result_of(run_cell("import json\nout, code = lane154.reconcile(['--project', %r, '--retire', %r, '--apply'])\nprint('RESULT ' + json.dumps([out, code]))\n"
                         % (PROJ, NAME), LANE, {"LANE154_NOW": "2026-09-24T08:20:10+00:00"}))
assert ret[1] == 0, ret
W = json.loads(ret[0].strip().splitlines()[-1])
assert W["event"] == "reconcile_withdrawn" and W["retired_doc_keys"] == [K1] and W["retired_chunks"] == 283 and len(W["retired_ids"]) == 283, W
cut = json.dumps({**W, "retired_ids": [W["retired_ids"][0], "...", W["retired_ids"][-1]]})
OUT["retire"] = cut + "\n" + fresh("2026-09-24T08:20:00Z", "withdrawn", "2026-09-24T08:21:00+00:00")
RE_ = OUT["retire"]
# a restore: make restore rewrites the object; its finalize event reaches the worker
rst = result_of(run_cell("import json\nout, code = lane154.reconcile(['--project', %r, '--restore', %r, '--apply'])\nprint('RESULT ' + json.dumps([out, code]))\n"
                         % (PROJ, NAME), LANE, {"LANE154_NOW": "2026-09-24T08:30:10+00:00"}))
assert rst[1] == 0, rst
R = json.loads(rst[0].strip().splitlines()[-1])
assert R["event"] == "reconcile_restored", R
back = worker(R["generation"], "2026-09-24T08:30:25+00:00")
assert any(j.get("event") == "ingest_reactivated" and j.get("embedded") == 0 for j in back["lines"]), back["lines"]
assert back["result"] == {"status": "reactivated", "doc_key": K1, "chunks": 283}, back["result"]
OUT["restore"] = rst[0] + fresh("2026-09-24T08:30:00Z", "indexed", "2026-09-24T08:31:30+00:00")
RS = OUT["restore"]
short = lambda s: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\1...", s)  # noqa: E731
for text_, notice in ((UP, "45"), (UN, "30"), (RS, "30")):
    assert "  0:00  handbook indexed; rag_engine in sync; vertex_search drift, missing " in text_ and "  0:20  handbook indexed; rag_engine in sync; vertex_search in sync\n" in text_, text_
    assert f"zeta, answered from vertex_search: A confirmed employee at grade L4 or above serves a notice period of {notice} days [" in text_, text_
    assert text_.count('"status": "in sync"') == 2, text_
    assert text_.count('"ledger_current": 7, "held": 7') == 2, text_
for text_, ops in ((UP, ["upsert", "upsert", "delete:superseded", "delete:superseded"]), (UN, ["upsert", "upsert", "delete:superseded", "delete:superseded"]),
                   (RE_, ["delete:withdrawn", "delete:withdrawn"]), (RS, ["upsert", "upsert"])):
    got = re.findall(r"^  \d\d:\d\d:\d\d  (\S+) ", text_, re.M)
    assert got == ops, (got, ops, text_)
assert "  0:00  handbook withdrawn; rag_engine in sync; vertex_search in sync\n" in RE_ and '"ledger_current": 6, "held": 6' in RE_, RE_
assert "zeta, answered from vertex_search: The context does not say.\n" in RE_, RE_
assert f"{short(K2)}" in UP.split("make managed-status", 1)[0] and f"upsert            rag_engine    us-central1 {short(K2)}" in UP, UP

# ------------------------------------------------------------------ the panel: one document's lifecycle, the kit's own paths
V1D = b"# Demo rules\n\n## R-01 \xe2\x80\x94 Visitors\n\nVisitors sign the register at reception.\n\n## R-02 \xe2\x80\x94 Badges\n\nBadges are worn at all times.\n"
V2D = V1D.replace(b"Badges are worn at all times.", b"Badges are worn at all times and returned at the gate.")
PIC = b"\x89PNG demo chart"
EVENTS = ["up1", "up2", "retire", "restore", "walk", "policy", "fail"]
rng = random.Random(154)
SEQS = [[rng.choice(EVENTS) for _ in range(7)] for _ in range(36)] + [["up2", "up1", "retire", "restore"], ["retire", "up1", "up2", "restore", "walk"],
                                                                      ["policy", "up2", "policy", "up1", "retire", "restore"], ["fail", "up2", "walk", "up2", "up1", "up2"],
                                                                      ["up1", "retire", "retire", "restore", "restore", "walk"]]
PICS = [i % 2 == 1 for i in range(len(SEQS))]
P2 = {k: T / f"demo-{k}.json" for k in STATE}
CHECK_PY = """import json, lane154, sys
lane154.worker_stubs()
lane154.capture("documind-ingest")
import main as W                                        # one worker instance for a whole sequence, as one Cloud Run instance
lane154._W.append(W)
import managed
from shared import tenancy
P, NAME = %r, "demo/rules.md"
V1, V2, PIC = %r, %r, %r
KEYS = {}
from hashlib import sha256
for label, data in (("v1", V1), ("v2", V2), ("picture", PIC)):
    KEYS["demo_" + sha256(data).hexdigest()] = label
SEQS, PICS = %r, %r
out = []
for seq, pic in zip(SEQS, PICS):
    for k, v in (("fs", {"tenant_settings": {"demo": {"data_region": "any"}}}), ("stores", {"corpora": ["demo"], "data_stores": ["demo"], "rag": {}, "vs": {}, "n": 0}),
                 ("gcs", {}), ("logs", {"entries": []})):
        open(lane154.PATHS[k], "w", encoding="utf-8").write(json.dumps(v))
    lane154._STATE.clear(); lane154._KEY.clear()
    W._mirror._said.clear(); W._POLICY.clear()
    if pic:
        g = lane154.upload("demo/chart.png", PIC, "image/png")
        lane154.Doc("sources", "demo~chart.png").set({"tenant_id": "demo", "name": "demo/chart.png", "gcs_uri": "gs://%%s-uploads/demo/chart.png" %% P,
                                                          "doc_key": "demo_" + sha256(PIC).hexdigest(), "status": "indexed", "generation": g,
                                                          "sha256": sha256(PIC).hexdigest(), "chunks": 1})
    steps = []
    for ev in ["up1"] + seq:
        lane154.flush_logs()
        mark = len(lane154._get("logs").get("entries", []))
        if ev in ("up1", "up2"):
            g = lane154.upload(NAME, V1 if ev == "up1" else V2)
            outcome = lane154.worker(NAME, g)["result"]["status"]
        elif ev == "retire":
            text, code = lane154.reconcile(["--project", P, "--retire", NAME, "--apply"])
            outcome = "withdrawn"
        elif ev == "restore":
            text, code = lane154.reconcile(["--project", P, "--restore", NAME, "--apply"])
            if code:
                outcome = "refused"
            else:
                outcome = "restored, then " + lane154.worker(NAME, json.loads(text.strip().splitlines()[-1])["generation"])["result"]["status"]
        elif ev == "walk":
            text, code = lane154.reconcile(["--project", P, "--tenant", "demo", "--apply"])
            outcome = "walk: " + ",".join(sorted(json.loads(l)["reconcile"] for l in text.splitlines() if l.startswith('{"reconcile"')) or ["nothing"])
        elif ev == "policy":
            now = tenancy.policy_for("demo", lane154.DB)
            tenancy._db = lambda: lane154.DB
            tenancy.set_policy("demo", "in" if now == "any" else "any")
            W._POLICY.clear()
            outcome = "policy " + tenancy.policy_for("demo", lane154.DB)
        else:
            st = lane154._get("stores"); st["fail_next_vs"] = True; lane154._put("stores")
            outcome = "armed"
        lane154.flush_logs()
        lines = [[e["jsonPayload"]["store"], e["jsonPayload"]["op"], e["jsonPayload"]["event"]] for e in lane154._get("logs")["entries"][mark:]
                 if str(e["jsonPayload"].get("event", "")).startswith("mirror_") and e["jsonPayload"].get("tenant") == "demo"]
        st = lane154._get("stores")
        for e in st["vs"].get("demo", {}).values():
            e["left"] = 0
        lane154._put("stores")
        stores = managed.Mirror.from_env(lane154.DB, "both").stores
        status = [[s["store"], s["status"], sorted(KEYS[k] for k in s.get("missing_doc_keys", [])), sorted(KEYS[k] for k in s.get("orphan_doc_keys", []))]
                  for s in managed.status(lane154.DB, stores, "demo")]
        row = lane154._row("sources", "demo~rules.md") or {}
        steps.append([ev, outcome, lines, [row.get("status"), KEYS.get(row.get("doc_key"))],
                      sorted(KEYS[k] for k in st["rag"].get("demo", {})), sorted(KEYS[k] for k in st["vs"].get("demo", {})), status])
    out.append(steps)
print("RESULT " + json.dumps(out))""" % (PROJ, V1D, V2D, PIC, SEQS, PICS)
CHECK_ENV = {f"LANE154_{k.upper()}": str(p) for k, p in P2.items()}
reset(P2, {}, {"corpora": ["demo"], "data_stores": ["demo"], "rag": {}, "vs": {}}, {})
PY_SIDE = result_of(run_cell(CHECK_PY, LANE, CHECK_ENV))
ALL_STEPS = [s for seq in PY_SIDE for s in seq]
OUTCOMES = {s[1] for s in ALL_STEPS}
assert {"indexed", "reactivated", "duplicate", "withdrawn", "refused", "restored, then reactivated", "armed", "policy in", "policy any"} <= OUTCOMES, OUTCOMES
assert any(l[2] == "mirror_failed" for s in ALL_STEPS for l in s[2]) and any(l[2] == "mirror_policy_skipped" for s in ALL_STEPS for l in s[2])
assert {o for o in OUTCOMES if o.startswith("walk")} <= {"walk: nothing", "walk: touch", "walk: withdrawn"}, sorted(OUTCOMES)
assert "walk: touch" in OUTCOMES and "walk: withdrawn" in OUTCOMES and "walk: nothing" in OUTCOMES, sorted(OUTCOMES)
# 7. a missing copy stays missing: the walk plans nothing for it, and the same bytes again are a duplicate the mirror never sees;
#    only another version's swap, or the undo, sends the text again
FIX = PY_SIDE[SEQS.index(["fail", "up2", "walk", "up2", "up1", "up2"])]
assert [s[1] for s in FIX] == ["indexed", "armed", "indexed", "walk: nothing", "duplicate", "reactivated", "reactivated"], [s[1] for s in FIX]
assert all("v2" in FIX[k][6][1][2] for k in (2, 3, 4)) and FIX[4][2] == [] and "v2" in FIX[6][5] and ["vertex_search", "upsert", "mirror_failed"] in FIX[2][2], FIX
shutil.rmtree(T, ignore_errors=True)

UI_JS = r"""var root = document.getElementById('lf'); if (!root) return;
  var STORES = ['rag_engine', 'vertex_search'];
  function fresh(picture){ return {policy: 'any', rows: {}, claims: {}, ledger: [null, null], object: null, objGen: 0, ledgerGen: 0, held: {rag_engine: {}, vertex_search: {}}, said: {}, failNext: false, picture: picture}; }
  function retireOthers(w, keep){ var gone = []; Object.keys(w.rows).sort().forEach(function(v){ if (v !== keep && w.rows[v] === 'current') { w.rows[v] = 'retired'; w.claims[v] = 'superseded'; gone.push(v); } }); return gone; }
  function upsert(w, v, lines){ if (w.policy !== 'any') { STORES.forEach(function(s){ if (!w.said[s]) { lines.push([s, 'upsert', 'mirror_policy_skipped']); w.said[s] = 1; } }); return; }
    STORES.forEach(function(s){ if (s === 'vertex_search' && w.failNext) { w.failNext = false; lines.push([s, 'upsert', 'mirror_failed']); return; }
      w.held[s][v] = 1; lines.push([s, 'upsert', 'mirror_ok']); }); }
  function drop(w, gone, why, lines){ gone.forEach(function(v){ STORES.forEach(function(s){ delete w.held[s][v]; lines.push([s, 'delete:' + why, 'mirror_ok']); }); }); }
  function arrive(w, v, lines){ var claim = w.claims[v];
    if (claim === 'indexed') { return 'duplicate'; }
    if (claim === 'superseded') { if (w.ledger[0] === 'withdrawn') { return 'withdrawn'; }
      w.rows[v] = 'current'; w.claims[v] = 'indexed'; var back = retireOthers(w, v); upsert(w, v, lines); drop(w, back, 'superseded', lines); w.ledger = ['indexed', v]; w.ledgerGen = w.objGen; return 'reactivated'; }
    w.claims[v] = 'indexed'; w.rows[v] = 'current'; var gone = retireOthers(w, v); upsert(w, v, lines); drop(w, gone, 'superseded', lines); w.ledger = ['indexed', v]; w.ledgerGen = w.objGen; return 'indexed'; }
  function step(w, ev){ var lines = [], out;
    if (ev === 'up1' || ev === 'up2') { w.object = ev === 'up1' ? 'v1' : 'v2'; w.objGen++; out = arrive(w, w.object, lines); }
    else if (ev === 'retire') { drop(w, retireOthers(w, null), 'withdrawn', lines); w.ledger = ['withdrawn', w.ledger[1]]; out = 'withdrawn'; }
    else if (ev === 'restore') { if (w.ledger[0] !== 'withdrawn') { out = 'refused'; } else { w.ledger = ['retired', w.ledger[1]]; w.objGen++; out = 'restored, then ' + arrive(w, w.object, lines); } }
    else if (ev === 'walk') { var acts = []; if (w.ledger[0] === 'withdrawn') { acts.push('withdrawn'); } else if (w.ledger[0] === 'indexed' && w.objGen !== w.ledgerGen) { acts.push('touch'); w.ledgerGen = w.objGen; }
      out = 'walk: ' + (acts.length ? acts.join(',') : 'nothing'); }
    else if (ev === 'policy') { w.policy = w.policy === 'any' ? 'in' : 'any'; out = 'policy ' + w.policy; }
    else { w.failNext = true; out = 'armed'; }
    var current = {}; if (w.ledger[0] === 'indexed') { current[w.ledger[1]] = 1; } if (w.picture) { current.picture = 1; }
    var status = STORES.map(function(s){ var held = w.held[s], missing = Object.keys(current).filter(function(k){ return !held[k]; }).sort(), orphans = Object.keys(held).filter(function(k){ return !current[k]; }).sort();
      return [s, missing.length || orphans.length ? 'drift' : 'in sync', missing, orphans]; });
    return [ev, out, lines, w.ledger.slice(), Object.keys(w.held.rag_engine).sort(), Object.keys(w.held.vertex_search).sort(), status]; }
  window.__lf = {fresh: fresh, step: step};
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  var $ = function(id){ return document.getElementById(id); };
  var NAMES = {up1: 'version 1 uploaded', up2: 'version 2 uploaded', retire: 'make retire', restore: 'make restore', walk: 'the nightly walk', policy: 'the policy turned', fail: 'a Vertex AI Search copy set to fail'};
  var world, log;
  function row(out, k, v, cls){ out.appendChild(el('b', '', k)); out.appendChild(el('span', cls || '', v)); }
  var WALK = {'walk: nothing': 'nothing to do (it never looks inside a store)', 'walk: touch': 'touch, the new generation recorded and nothing indexed', 'walk: withdrawn': 'withdrawn, the tombstone left alone'};
  function show(r){ var li = el('li', '', NAMES[r[0]] + ': ' + (WALK[r[1]] || r[1])); if (r[2].length) { li.appendChild(el('br')); li.appendChild(document.createTextNode(r[2].map(function(l){ return l[0] + ' ' + l[1] + ' ' + l[2].replace('mirror_', ''); }).join('; '))); } $('lf-steps').appendChild(li);
    var st = $('lf-state'); st.textContent = '';
    row(st, 'The ledger', (r[3][0] || 'no row') + (r[3][1] ? ', version ' + r[3][1].replace('v', '') : ''));
    row(st, 'RAG Engine', r[4].length ? r[4].join(', ') : 'nothing'); row(st, 'Vertex AI Search', r[5].length ? r[5].join(', ') : 'nothing');
    r[6].forEach(function(s){ row(st, 'Status: ' + s[0].replace('_engine', '').replace('vertex_search', 'search'), s[1] + (s[2].length ? ', missing ' + s[2].join(', ') : '') + (s[3].length ? ', orphans ' + s[3].join(', ') : ''), s[1] === 'in sync' ? 'pass' : 'stop'); });
    $('lf-policy').textContent = 'Turn the tenant to ' + (world.policy === 'any' ? 'in' : 'any'); }
  function start(){ world = fresh($('lf-pic').checked); $('lf-steps').textContent = ''; show(step(world, 'up1')); }
  ['up1', 'up2', 'retire', 'restore', 'walk', 'policy', 'fail'].forEach(function(ev){ $('lf-' + ev).addEventListener('click', function(){ show(step(world, ev)); }); });
  $('lf-reset').addEventListener('click', start); $('lf-pic').addEventListener('change', start); start();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

PORT_JS = UI_JS.split("function el(")[0].replace("var root = document.getElementById('lf'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var G = window.__lf, SEQS = " + json.dumps(SEQS) + ", PICS = " + json.dumps(PICS) + ";\n"
        "var out = SEQS.map(function(seq, i){ var w = G.fresh(PICS[i]); return ['up1'].concat(seq).map(function(ev){ return G.step(w, ev); }); });\n"
        "process.stdout.write(JSON.stringify(out));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
for i, (a_, b_) in enumerate(zip(JS_SIDE, PY_SIDE)):
    for j, (x, y) in enumerate(zip(a_, b_)):
        assert x == y, (i, SEQS[i], PICS[i], j, x, y)
N_STEPS = len(ALL_STEPS)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the kit's mirror through the four events; no store, no network)",
    "ablate": "run in the operator shell, in the kit (retrieval only, no model: a few minutes)",
    "update": "run in the operator shell, in the kit (a second version of zeta's handbook, then the check)",
    "undo": "run in the operator shell, in the kit (the first version's bytes again, then the check)",
    "retire": "run in the operator shell, in the kit (the handbook withdrawn by hand, then the check)",
    "restore": "run in the operator shell, in the kit (the handbook brought back, then the check)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own managed.py)",
    "ablate": "(the kit's ablate.py on a stand-in lane whose retrieval is word overlap: the shape is real, the numbers are not; the latency column is left out)",
    "update": "(gcloud's copy lines as '...'; the kit's worker, managed.py and rag-api on a stand-in lane; your times differ)",
    "undo": "(the same stand-ins)",
    "retire": "(the kit's reconcile.py on the stand-in lane; its 283 retired_ids cut to the first and the last)",
    "restore": "(the same stand-ins; the worker took the rewrite's event)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

STATS = {"N_ROWS": str(N_ROWS), "N_SEQS": str(len(SEQS)), "N_STEPS": str(N_STEPS), "K2": short(K2), "K1": short(K1)}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the worker, reconcile.py, managed.py, ablate.py and rag-api on a stand-in lane | update, undo, withdrawal, restore: in sync each time"
      f" | panel checked against the kit on {len(SEQS)} sequences, {N_STEPS} steps")
