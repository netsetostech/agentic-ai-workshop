"""Build lesson 7.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Query a video clip and validate media citations. A video is a document the ingest worker DESCRIBES rather than parses:
Gemini splits it into segments of at most 60 seconds, each with start and end in seconds and a two-sentence summary that
quotes every number as it is spoken. The summary is the chunk - embedded, retrieved, quoted - and the video rides beside
it as media_url; a citation of it is kind=segment with start and end. The UI's pill says [Clip N, mm:ss] and its player
starts at that second. Offline: the kit's resolve(), the UI's _label/_mmss and main.py's modality_of over three packed
sources. Live: make media MEDIA_ARGS=--video (the town hall synthesised, its ground truth beside it); make retire of the
transcript Module 3 uploaded (upload.sh keeps a transcript home once its video exists, but removes nothing already sent);
make reindex of the MP4 (the worker's segments); the segments held against the ground truth; golden row mm-03's question
through /v1/stream, the answer drawn with the UI's own pill, the cited window checked against the ground truth, and a
signed link that opens the video at that second; make smoke-media green.

Build-time proof: every live cell ran the kit's own code over a stand-in lane (lane161.py, beside this file):
build_media.py (Text-to-Speech and ffmpeg stood in), reconcile.py, the ingest worker's push handler, rag-api under uvicorn
(its query, stream and media routes, with the kit's roster check), the MCP server under uvicorn, and smoke_media.py itself.
The panel is the kit's rendering - the UI's _label and _mmss and render_with_citations' source branch, main.py's
modality_of and run_eval's kind check - ported and compared with the kit's own functions on every combination it offers.
"""
import ast
import collections
import contextlib
import html
import itertools
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "7.5"
title = "<title>Lesson 7.5 Query a video clip and validate media citations - the clip at its second | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
OUT_SA = f"documind-outsider-sa@{PROJ}.iam.gserviceaccount.com"
MCP_SA = f"documind-mcp-sa@{PROJ}.iam.gserviceaccount.com"
PORT, MCP_PORT, GCS_PORT = 8161, 8261, 8361
API = "https://documind-api-NUMBER.asia-south1.run.app"
MCP_API = "https://documind-mcp-NUMBER.asia-south1.run.app"
VIDEO = "acme/townhall_2026_q1.mp4"
TRANSCRIPT = "acme/townhall_2026_q1.md"
Q = "In the FY2026 town hall, what did the CFO say happened to EMEA revenue?"
WORKER, SCHEMAS, CITES, UPLOAD, RUN_EVAL, BUDGET, SMOKE, MEDIA, GEN, PII, REC, MAIN = (
    "services/ingest/main.py", "shared/documind_schemas.py", "services/frontend/citations.py", "evals/upload.sh", "evals/run_eval.py",
    "services/rag-api/context_budget.py", "smoke/smoke_media.py", "services/rag-api/media.py", "services/rag-api/generator.py",
    "shared/pii.py", "services/ingest/reconcile.py", "services/rag-api/main.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-in label.ck{flex-direction:row;align-items:center;gap:10px;min-height:44px;}
.pc-in label.ck input{width:22px;height:22px;margin:0;accent-color:var(--teal-dark);flex:none;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.cc-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:0 10px;}
.cc-pill{background:#ccfbf1;color:#065f46;border-radius:6px;padding:1px 7px;margin:0 2px;font-size:12px;font-weight:600;white-space:nowrap;}
.fs-grid{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "describe": ("services/ingest/main.py - _describe_media(), its video half: segments of at most 60 seconds, every number quoted",
                 block(WORKER, '    audio = content_type.startswith("audio/")', n=21)),
    "citation": ("shared/documind_schemas.py - the Citation a caller receives: a segment carries its media_url, start and end",
                 block(SCHEMAS, "class Citation(BaseModel):", n=15)),
    "label": ("services/frontend/citations.py - the pill in the answer: [Clip N, mm:ss] for a segment",
              block(CITES, "def _label(n: int, src: dict | None) -> str:", n=11)),
    "player": ("services/frontend/citations.py - under Sources: the video itself, from the second the segment starts",
               block(CITES, '                elif kind == "segment" and src.get("media_url"):', n=5)),
    "upload_rule": ("evals/upload.sh - a transcript stays home when its video exists, as a PDF's mirror does",
                    block(UPLOAD, '  for f in "${dir}"*; do', n=10)),
    "kind_check": ("evals/run_eval.py - a media row asks for the citation's kind, not only the words",
                   block(RUN_EVAL, '                want_kind = row.get("must_cite_kind")', n=12)),
    "header": ("services/rag-api/context_budget.py - the [Source N] header the model reads: the file, a page, a section, a date",
               block(BUDGET, '    uri = chunk.get("source_uri") or chunk.get("source_file") or chunk.get("doc_id") or ""', n=8)),
}
assert EXCERPTS["describe"][1].rstrip().endswith('"chunk_hash": chunk_hash(s.summary)} for s in (r.parsed or [])]')
assert "segments of at most 60 seconds" in EXCERPTS["describe"][1] and "MEDIA_RESOLUTION_LOW" in EXCERPTS["describe"][1] and "quoting every number" in EXCERPTS["describe"][1]
assert EXCERPTS["citation"][1].rstrip().endswith("end: Optional[float] = None") and 'kind: Literal["text", "figure", "table", "segment"] = "text"' in EXCERPTS["citation"][1]
assert EXCERPTS["label"][1].rstrip().endswith('return f"[{n}]"') and "[Clip {n}, {_mmss(src.get('start'))}]" in EXCERPTS["label"][1]
assert EXCERPTS["player"][1].rstrip().endswith("""f"{src['source_uri'].rsplit('/', 1)[-1]}")""") and "start_time=start" in EXCERPTS["player"][1]
assert EXCERPTS["upload_rule"][1].rstrip().endswith("  done") and '( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" )' in EXCERPTS["upload_rule"][1]
assert EXCERPTS["kind_check"][1].rstrip().endswith('rec["why"] = f"cited no {want_kind}"') and "kind_ok = want_kind in kinds" in EXCERPTS["kind_check"][1]
assert EXCERPTS["header"][1].rstrip().endswith('return f"[Source {n}] " + ", ".join(bits)') and 'get("start")' not in EXCERPTS["header"][1] and 'get("end")' not in EXCERPTS["header"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (WORKER, SCHEMAS, CITES, UPLOAD, RUN_EVAL, BUDGET, SMOKE, MEDIA, GEN, PII, REC, MAIN,
                                                          "Makefile", "evals/build_media.py", "evals/required.json", "terraform/storage.tf",
                                                          "commands/lesson-12.1.sh", "services/rag-api/config.py")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert 'GEN_MODEL = os.environ.get("GEN_MODEL", "gemini-3.6-flash")' in src[WORKER]
assert 'MEDIA_TYPES = {"image/png": "figure", "image/jpeg": "figure",\n               "video/mp4": "segment", "audio/mpeg": "segment"}' in src[WORKER]
assert "media:\n\t$(PY) evals/build_media.py $(MEDIA_ARGS)" in MK and "MANAGED_MIRROR  ?= both" in MK
for pin in ("Pillow==12.3.0", "google-cloud-texttospeech==2.37.0", "imageio-ffmpeg==0.6.0"):
    assert pin in src["Makefile"], pin                                   # the pins the page's pip line uses: the Makefile's own
assert "texttospeech.googleapis.com" in src["commands/lesson-12.1.sh"] and "\napis: guard-project" in MK
assert 'resource "google_storage_bucket_iam_member" "ui_uploads"' in src["terraform/storage.tf"]      # documind-ui-sa reads the uploads bucket: its signed link opens
assert '"mm-03"' in src["evals/required.json"] and '"media_kind_rate": 0.80' in src[RUN_EVAL]
assert "SIGNED_URL_EXPIRY = datetime.timedelta(minutes=15)" in src[CITES]
assert 'IMAGE_MODEL = "gemini-3.1-flash-image"' in src[MEDIA] and "IMAGE_USD = 0.039" in src[MEDIA]
assert "DEMO_MODE=${DEMO_MODE-1}" in (KIT / "commands/lesson-12.2.sh").read_text(encoding="utf-8")   # a prompt drawn before costs nothing after the first run
# 1. make smoke-media asks one question, the figure one: no gate asks for a segment
assert src[SMOKE].count('call("POST", f"{API}/v1/query"') == 1 and 'c.get("kind") == "figure" and c.get("media_url")' in src[SMOKE]
assert 'c.get("kind") == "segment"' not in src[SMOKE]
# 2. nothing checks the second: the ground truth build_media.py writes is read by nothing (writer, skip rules and prose only)
MENTIONS = sorted(str(p.relative_to(KIT)).replace("\\", "/") for p in pb.kit_runtime_files("*") if p.is_file() and p.suffix in (".py", ".sh", ".mk", "")
                  and "segments.json" in p.read_text(encoding="utf-8", errors="ignore"))
assert MENTIONS == [".gitignore", "evals/build_media.py", "evals/demo_corpus_gate.py", "evals/upload.sh", "services/ingest/reconcile.py"], MENTIONS
assert 'open(out[:-4] + ".segments.json", "w"' in src["evals/build_media.py"] and "SKIP_SUFFIXES = (\".segments.json\",)" in src[REC]
# 3. the worker keeps Gemini's times as given: no check of order, of the 60 seconds or of the video's length
assert "class Segment(BaseModel):\n    start: float\n    end: float\n    summary: str" in src[WORKER]
assert "validator" not in src[WORKER] and "s.end - s.start" not in src[WORKER] and "s.start < s.end" not in src[WORKER]
# 4. the model is never told when a segment starts: the header has no time, and only figures and tables are shown to it
assert 'if c.get("kind") in ("figure", "table") and c.get("media_url"):' in src[GEN]
# 5. media_url is the object's gs:// path, though the schema calls it a signed URL; only the Streamlit UI signs it
assert "media_url: Optional[str] = None            # a signed URL for figure / table / segment" in src[SCHEMAS]
assert '"kind": "segment", "media_url": gcs_uri,' in src[WORKER]
SIGNERS = sorted(p.name for p in (KIT / "services/rag-api").glob("*.py") if "generate_signed_url" in p.read_text(encoding="utf-8"))
assert SIGNERS == ["media.py"] and 'method="PUT"' in src[MEDIA], SIGNERS          # the API signs only the upload door, never a citation
# 6. a video's frames are not DLP-scanned: inspect_image returns nothing for what is not an image; the summaries are scanned
assert "if content_type not in IMAGE_TYPES:\n        return []" in src[PII] and "video" not in src[PII].split("IMAGE_TYPES = ", 1)[1].split("}", 1)[0]
# 7. a transcript already sent stays: upload.sh only skips, and the walk has no rule for a transcript beside its video
assert "gcloud storage rm" not in src[UPLOAD] and ".mp4" not in src[REC]
assert "def prefer_current(chunks: list[dict]) -> list[dict]:" in (KIT / "services/rag-api/retriever.py").read_text(encoding="utf-8")
GOLD = {r["id"]: r for r in (json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
assert [k for k, r in GOLD.items() if r.get("must_cite_kind") == "segment"] == ["mm-03"] and GOLD["mm-03"]["question"] == Q
assert GOLD["mm-01"]["must_cite_kind"] == GOLD["mm-02"]["must_cite_kind"] == "figure" and all(f'"{k}"' in src["evals/required.json"] for k in ("mm-01", "mm-02", "mm-03"))
assert "media is a document. Five checks." in src[SMOKE] and "fastmcp==3.4.7" in (KIT / "services/mcp/requirements.txt").read_text(encoding="utf-8")
assert "gap_s: float = 0.7" in src["evals/build_media.py"] and "A resolution is a frame-sampling dial" in src[WORKER]
# 8. the worker's Gemini call on a video (or a figure) is metered nowhere: it reads no usage, and no row carries its cost
assert "usage_metadata" not in src[WORKER] and "cost_usd" not in src[WORKER] and "tokens_in" not in src[WORKER]

# ------------------------------------------------------------------ the corpus, as evals/upload.sh sent it before the video existed
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
FIG3 = ("Figure 3 of the ACME Annual Report FY2026: a grouped bar chart titled 'Revenue by region, FY2025 vs FY2026 (Rs crore)', one FY2025 "
        "and one FY2026 bar for each region.\n\nKey facts: India grew from 412 to 508 (+23.3%), APAC ex-India from 188 to 236 (+25.5%) and the "
        "Americas from 143 to 170 (+18.9%); EMEA fell from 96 to 91 (-5.2%), the only region that declined.\n\n| Region | FY2025 | FY2026 | Growth |\n"
        "|---|---|---|---|\n| India | 412 | 508 | 23.3% |\n| APAC ex-India | 188 | 236 | 25.5% |\n| EMEA | 96 | 91 | -5.2% |\n| Americas | 143 | 170 | 18.9% |")
CAPTIONS = {"annual_report_2026_fig3.png": FIG3,
            "inv_2026_0412.png": "A tax invoice rendered as a page image: INV-2026-0412, raised on ACME, with its line items, GST and payment terms.",
            "payment_of_bonus_act_1965_p30.png": "Page 30 of the Payment of Bonus Act, 1965: the Fourth Schedule's table of set on and set off of "
                                                 "the allocable surplus, year by year."}
ROWS, TEXTS, LEDGER, CLAIMS, RAG, VS = {}, {}, {}, {}, {"acme": {}, "zeta": {}}, {"acme": {}, "zeta": {}}
N = 0
AT = "2026-09-20T10:00:00+00:00"
for tdir in sorted((KIT / "evals/corpus").iterdir()):
    tenant = tdir.name
    TEXTS[tenant] = {}
    for f in sorted(tdir.iterdir()):
        if f.suffix == ".md" and (f.with_suffix(".pdf").exists() or f.with_suffix(".mp4").exists()) or f.name.endswith(".segments.json") or f.suffix == ".mp4":
            continue                                                     # upload.sh's rule, on a clone with no video yet
        data = f.read_bytes()
        sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/{tenant}/{f.name}"
        dk = f"{tenant}_{sha}"
        if f.suffix == ".png":
            ROWS[f"{tenant}:{sha}#0"] = {"tenant_id": tenant, "text": CAPTIONS[f.name], "source_uri": uri, "doc_type": "figure", "kind": "figure",
                                         "doc_key": dk, "locator": "figure", "media_url": uri, "current": True, "page_start": 1}
            n_chunks = 1
        else:
            md = f.with_suffix(".md")
            if md.exists():
                text = md.read_text(encoding="utf-8")
            else:                                                        # a PDF with no mirror (the POSH Act): its own text
                import pypdf
                text = "\f".join(p.extract_text() or "" for p in pypdf.PdfReader(str(f)).pages)
            text = re.sub(r"\A<!--.*?-->\s*", "", text, flags=re.S)
            cut = chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown", "slug": f.stem}, tenant)
            for i, c in enumerate(cut):
                ROWS[f"{tenant}:{sha}#{i}"] = {"tenant_id": tenant, "text": c["text"], "source_uri": uri, "doc_type": "unknown", "kind": "text",
                                               "doc_key": dk, "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True,
                                               **({"section": c["section"]} if c.get("section") else {})}
            TEXTS[tenant][dk] = {"text": text, "source_uri": uri, "pdf": f.suffix == ".pdf"}
            n_chunks = len(cut)
            if tenant in RAG:
                N += 1
                RAG[tenant][dk] = {"name": f"projects/NUMBER/locations/us-central1/ragCorpora/{tenant}-corpus/ragFiles/{N}", "source_uri": uri}
                VS[tenant][dk] = {"source_uri": uri, "left": 0}
        held = {"rag_engine": "us-central1", "vertex_search": "global"} if tenant in RAG and f.suffix != ".png" else {}
        LEDGER[f"{tenant}~{f.name}"] = {"tenant_id": tenant, "name": f"{tenant}/{f.name}", "gcs_uri": uri, "doc_key": dk, "status": "indexed",
                                        "generation": "1", "sha256": sha, "chunks": n_chunks, "mirrored": held}
        CLAIMS[dk] = {"gcs_uri": uri, "tenant_id": tenant, "status": "indexed", "chunks": n_chunks, "generation": "1", "claimed_at": AT, "indexed_at": AT}
TRANSCRIPT_KEY = LEDGER["acme~townhall_2026_q1.md"]["doc_key"]
N_TRANSCRIPT = LEDGER["acme~townhall_2026_q1.md"]["chunks"]
ROSTER = {f"tenants/{t}/members": {sa.lower(): {"email": sa.lower()} for sa in (UI_SA, MCP_SA)} for t in ("acme", "zeta", "globex")}   # keyed as make roster keys it: lower case

T = Path(tempfile.mkdtemp(prefix="lesson161-"))
shutil.copy(HERE / "lane161.py", T / "lane161.py")
(T / "base.json").write_text(json.dumps({"rows": ROWS, "texts": TEXTS}), encoding="utf-8")
K2 = T / "kit"                                                           # where make media writes: a copy of the kit's corpus folder, not the kit
for rel in ("evals/build_media.py", "services/frontend/citations.py", "evals/corpus/acme/townhall_2026_q1.md", "evals/corpus/acme/annual_report_2026.md",
            *(f"evals/corpus/acme/{n}" for n in CAPTIONS)):
    (K2 / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(KIT / rel, K2 / rel)
TRUTH = K2 / "evals/corpus/acme/townhall_2026_q1.segments.json"
STATE = {k: T / f"{k}.json" for k in ("fs", "gcs", "stores", "logs")}
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T), "LANE161_KIT": str(KIT), "LANE161_BASE": str(T / "base.json"),
       **{f"LANE161_{k.upper()}": str(p) for k, p in STATE.items()}, "LANE161_TRUTH": str(TRUTH), "LANE161_GCSURL": f"http://127.0.0.1:{GCS_PORT}",
       "PYTHONPATH": str(T), "API": API, "AUDIT_BUCKET": f"{PROJ}-audit", "MANAGED_MIRROR": "both", "RAG_LOCATION": "us-central1",
       "EMBEDDING_MODEL": "text-embedding-005", "EMBEDDING_VERSION": "1", "RETENTION_DAYS": "30", "SEARCH_LOCATION": "global"}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "GRAPH_", "SPANNER_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR",
                                           "ROUTING", "SPEND_", "BUDGET_", "EMBED_", "BQ_", "DOCAI_", "BATCH_", "DEMO_MODE", "DOCUMIND_", "SELF_URL"))]:
    ENV.pop(k)
fs0 = {"tenant_settings": {"acme": {"data_region": "any"}, "zeta": {"data_region": "any", "retrieval_backend": "vertex_search"},
                           "globex": {"data_region": "in"}},
       "sources": LEDGER, "documents": CLAIMS, **ROSTER}
for k, v in (("fs", fs0), ("stores", {"corpora": ["acme", "zeta"], "data_stores": ["acme", "zeta"], "rag": RAG, "vs": VS, "n": N}), ("gcs", {}),
             ("logs", {"entries": []})):
    STATE[k].write_text(json.dumps(v), encoding="utf-8")


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T, argv: tuple = ()) -> str:
    r = subprocess.run([sys.executable, "-", *argv], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-4000:])
    return r.stdout


def result_of(out: str):
    return json.loads(out.rsplit("RESULT ", 1)[1])


def heredoc(body: str, prefix: str = "", args: str = "") -> str:
    return f"{prefix}python - {args}<<'PY'\n{body}\nPY"


LANE = "import lane161\nlane161.freeze()\n"
short = lambda s: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\1...", s)  # noqa: E731

# ------------------------------------------------------------------ step 3: from a segment to a pill, run (offline, on the kit)
RULES_PY = """import ast, re, sys
sys.path.insert(0, ".")
from shared.documind_schemas import ModelDraft, resolve     # the answer contract, resolved the way rag-api resolves it

ns = {}                                                       # the UI's pill and clock, and the usage row's modality, lifted out
for path, names in (("services/frontend/citations.py", ("_mmss", "_label")), ("services/rag-api/main.py", ("modality_of",))):
    for node in ast.parse(open(path, encoding="utf-8").read()).body:          # (citations.py imports streamlit; main.py the cloud clients)
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module([node], []), path, "exec"), ns)

URI = "gs://documind-ai-YOUR-ID-uploads/acme/"
packed = [                                                    # three chunks as the budget packed them: a table row, a figure, a clip
    {"id": "acme:3f2a...#AR-02", "source_uri": URI + "annual_report_2026.md", "kind": "text", "rerank_score": 0.62,
     "text": "| EMEA | 96 | 91 | -5.2% |"},
    {"id": "acme:9c1d...#0", "source_uri": URI + "annual_report_2026_fig3.png", "kind": "figure", "media_url": URI + "annual_report_2026_fig3.png",
     "rerank_score": 0.71, "text": "Figure 3: revenue by region, FY2025 against FY2026. EMEA fell from 96 to 91 (-5.2%)."},
    {"id": "acme:77e0...#1", "source_uri": URI + "townhall_2026_q1.mp4", "kind": "segment", "media_url": URI + "townhall_2026_q1.mp4",
     "start": 200.7, "end": 238.0, "rerank_score": 0.88,
     "text": "Arjun, the CFO: EMEA is the one region that shrank; revenue fell 5.2 per cent, from 96 crore to 91 crore."},
]
draft = ModelDraft(answer="Revenue in EMEA fell 5.2 per cent, from 96 crore to 91 crore [3].", confidence="high", answerable=True,
                   citations=[{"source": 3, "quote": "revenue fell 5.2 per cent, from 96 crore to 91 crore"},
                              {"source": 7, "quote": "a source the model made up"}])
answer = resolve(draft, packed)
c = answer.citations[0]
print(f"1. resolve(): {len(draft.citations)} draft citations in, {len(answer.citations)} out ([Source 7] was not in the context):")
print("  ", c.model_dump(exclude={"quote"}))
pill = lambda m: ns["_label"](int(m.group(1)), packed[int(m.group(1)) - 1])
print("2. the answer as the UI draws it:", re.sub(r"\\[(\\d+)\\]", pill, draft.answer))
print(f"   under Sources: the video from second {int(float(c.start or 0))}, captioned {ns['_mmss'](c.start)} – {ns['_mmss'](c.end)} "
      f"of {c.source_uri.rsplit('/', 1)[-1]}")
print("3. the pills for the three sources:", *[ns["_label"](i, s) for i, s in enumerate(packed, 1)],
      "| a segment with no start:", ns["_label"](3, {"kind": "segment"}))
print("4. the usage row's modality:", ns["modality_of"]([x.kind for x in answer.citations]),
      "| the same answer from the table and the figure:", ns["modality_of"](["text", "figure"]))
for cited in (3, 1):                                          # run_eval's rule for a media row: mm-03 asks for a segment
    one = ModelDraft(answer=draft.answer, confidence="high", answerable=True, citations=[{"source": cited, "quote": "5.2 per cent"}])
    kinds = sorted({x.kind for x in resolve(one, packed).citations})
    print(f"5. mm-03, citing [Source {cited}]: kinds {kinds} -> {'counts' if 'segment' in kinds else 'cited no segment'}")"""
CELLS = {"rules": heredoc(RULES_PY)}
OUT = {"rules": run_cell(RULES_PY, cwd=KIT)}
RU = OUT["rules"]
assert "2 draft citations in, 1 out" in RU and "'kind': 'segment'" in RU and "'start': 200.7, 'end': 238.0" in RU, RU
assert "fell 5.2 per cent, from 96 crore to 91 crore [Clip 3, 03:20]." in RU and "the video from second 200, captioned 03:20 – 03:58" in RU, RU
assert "[1] [Fig 2] [Clip 3, 03:20] | a segment with no start: [Clip 3, ?]" in RU and "modality: video | the same answer from the table and the figure: image" in RU, RU
assert "citing [Source 3]: kinds ['segment'] -> counts" in RU and "citing [Source 1]: kinds ['text'] -> cited no segment" in RU, RU

# ------------------------------------------------------------------ step 4: the clip built, the transcript withdrawn, the video heard
MEDIA_ECHO = MK[MK.index("\nmedia:\n\t") + 9:].split("\n", 1)[0].replace("$(PY)", "python").replace("$(MEDIA_ARGS)", "--video") + "\n"
assert MEDIA_ECHO == "python evals/build_media.py --video\n", MEDIA_ECHO
CELLS["media"] = ("python -m pip install -q Pillow==12.3.0 google-cloud-texttospeech==2.37.0 imageio-ffmpeg==0.6.0   # slides, voices, a static ffmpeg\n"
                  "make media MEDIA_ARGS=--video")
BUILD_PY = ("lane161.tts()\nlane161.ffmpeg()\nimport runpy, sys\nsys.argv = ['build_media.py', '--video']\n"
            "runpy.run_path('evals/build_media.py', run_name='__main__')\n")
built = run_cell(BUILD_PY, LANE, cwd=K2)
OUT["media"] = MEDIA_ECHO + built.replace("corpus\\acme\\", "corpus/acme/")
MD = OUT["media"]
TRUTH_J = json.loads(TRUTH.read_text(encoding="utf-8"))
TURNS = TRUTH_J["segments"]
MP4 = (K2 / "evals/corpus/acme/townhall_2026_q1.mp4").read_bytes()
KV = f"acme_{sha256(MP4).hexdigest()}"
assert len(TURNS) == 5 and [t["speaker"] for t in TURNS] == ["Meera", "Arjun", "Meera", "Arjun", "Meera"], TURNS
assert "voices: {'Meera': 'en-IN-Chirp3-HD-Aoede', 'Arjun': 'en-IN-Chirp3-HD-Charon'}" in MD and MD.count("  keep ") == 3, MD
assert re.search(r"corpus/acme/townhall_2026_q1\.mp4: \d\.\d MB, \d+ s, 5 utterances; ground truth beside it in townhall_2026_q1\.segments\.json", MD), MD
SAID = next(t for t in TURNS if "5.2 per cent" in t["text"])
assert SAID["speaker"] == "Arjun" and max(t["end"] - t["start"] for t in TURNS) < 60

CELLS["retire"] = f'make retire PROJECT="$PROJECT" SOURCE={TRANSCRIPT}'
ret = result_of(run_cell("import json\nout, code = lane161.reconcile(['--project', %r, '--retire', %r, '--apply'])\nprint('RESULT ' + json.dumps([out, code]))\n"
                         % (PROJ, TRANSCRIPT), LANE, {"LANE161_NOW": "2026-09-24T08:05:10+00:00"}))
assert ret[1] == 0, ret
W = json.loads(ret[0].strip().splitlines()[-1])
assert W["event"] == "reconcile_withdrawn" and W["retired_doc_keys"] == [TRANSCRIPT_KEY] and W["retired_chunks"] == N_TRANSCRIPT, W
OUT["retire"] = json.dumps({**W, "retired_ids": W["retired_ids"] if len(W["retired_ids"]) <= 2 else [W["retired_ids"][0], "...", W["retired_ids"][-1]]})


def upload(name: str, data: bytes, ct: str, at: str) -> str:
    return result_of(run_cell(f"import json, base64\nprint('RESULT ' + json.dumps(lane161.upload({name!r}, base64.b64decode({__import__('base64').b64encode(data).decode()!r}), {ct!r})))\n",
                              LANE, {"LANE161_NOW": at}))


def worker(name: str, gen: str, ct: str, at: str) -> dict:
    return result_of(run_cell(f"import json\nr = lane161.worker({name!r}, {gen!r}, {ct!r})\nprint('RESULT ' + json.dumps(r, default=str))\n",
                              LANE, {"LANE161_NOW": at}))


def reindex_lines(run: dict, tenant: str, obj: str) -> str:
    """What commands/reindex.sh prints around the worker's line (gcloud's own copy lines are the '...')."""
    line = next(j for j in run["lines"] if j.get("event") in ("ingest_ok", "ingest_reactivated"))
    val = lambda v: "" if v is None else ";".join(map(str, v)) if isinstance(v, list) else str(v)  # noqa: E731 - gcloud's value() format
    out = ("...\n" f">> gs://{PROJ}-uploads/{tenant}/{obj} - waiting for the worker (up to 5 min)\n"
           ">> event doc_key chunks reused embedded retired effective_from\n"
           ">> " + "\t".join(val(line.get(k)) for k in ("event", "doc_key", "chunks", "reused", "embedded", "retired", "effective_from")) + "\n")
    sup = next((j for j in run["lines"] if j.get("event") == "ingest_superseded"), None)
    if sup:
        out += ">> retired (doc_keys, chunks, expire days): " + "\t".join(val(sup.get(k)) for k in ("retired_doc_keys", "retired_chunks", "expire_days")) + "\n"
    return out + f">> the gate, scoped to this document, on a candidate: make eval-live PROJECT={PROJ} SOURCE={obj} API=<candidate url>\n"


REINDEX = (KIT / "commands/reindex.sh").read_text(encoding="utf-8")
for piece in ('echo ">> gs://$PROJECT-uploads/$TENANT/$OBJ - waiting for the worker (up to 5 min)"', 'echo ">> event doc_key chunks reused embedded retired effective_from"',
              '"$PY" evals/run_eval.py --source "$OBJ" >/dev/null',
              'echo ">> the gate, scoped to this document, on a candidate: make eval-live PROJECT=$PROJECT SOURCE=$OBJ API=<candidate url>"'):
    assert piece in REINDEX, piece
GATE = subprocess.run([sys.executable, "evals/run_eval.py", "--source", "townhall_2026_q1.mp4"], cwd=str(KIT), capture_output=True, text=True,
                      encoding="utf-8", env={**ENV, "PYTHONPATH": ""})
assert GATE.returncode == 0 and "rows citing townhall_2026_q1.mp4: 1" in GATE.stdout and "mm-03" in GATE.stdout, GATE.stdout[-600:]   # reindex.sh's first line passes
CELLS["reindex"] = f'make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/{VIDEO}'
gv = upload(VIDEO, MP4, "video/mp4", "2026-09-24T08:07:00+00:00")
heard = worker(VIDEO, gv, "video/mp4", "2026-09-24T08:07:05+00:00")
assert heard["result"] == {"status": "indexed", "chunks": 5, "reused": 0, "embedded": 5}, heard["result"]
OUT["reindex"] = reindex_lines(heard, "acme", VIDEO.split("/", 1)[1])
assert f">> ingest_ok\t{KV}\t5\t0\t5\t0\t\n" in OUT["reindex"] and "retired (doc_keys" not in OUT["reindex"], OUT["reindex"]

ROWS_PY = """import json, os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P = os.environ["PROJECT"]
URI = f"gs://{P}-uploads/acme/townhall_2026_q1.mp4"
db = firestore.Client(project=P)
rows = [d.to_dict() for d in db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", "acme"))
        .where(filter=FieldFilter("source_uri", "==", URI)).where(filter=FieldFilter("current", "==", True)).stream()]
truth = json.load(open("evals/corpus/acme/townhall_2026_q1.segments.json", encoding="utf-8"))["segments"]
mmss = lambda s: f"{int(s) // 60:02d}:{int(s) % 60:02d}"
print(f"{len(rows)} segments of townhall_2026_q1.mp4 in acme's index, against the ground truth's {len(truth)} turns:")
for r in sorted(rows, key=lambda r: r["start"]):
    heard = [f"{t['speaker']} {mmss(t['start'])}" for t in truth if min(t["end"], r["end"]) - max(t["start"], r["start"]) > 1]   # a second of the turn or more
    print(f"  {r['kind']} {r['locator']:9} {mmss(r['start'])}-{mmss(r['end'])} {r['end'] - r['start']:4.0f} s  over {', '.join(heard) or 'nobody'}")
    print(f"      {r['text'][:104]}...")
longest = max(r["end"] - r["start"] for r in rows)
bad = [r["locator"] for r in rows if not 0 <= r["start"] < r["end"]]
video_end = truth[-1]["end"]
print(f"checks: longest {longest:.0f} s (the prompt asks for at most 60) -> {'PASS' if longest <= 60 else 'FAIL'}; "
      f"start before end in every row -> {'PASS' if not bad else 'FAIL ' + ', '.join(bad)}; "
      f"last end {mmss(max(r['end'] for r in rows))} against the speech's end {mmss(video_end)}")
said = next(t for t in truth if "5.2 per cent" in t["text"])
hit = [r["locator"] for r in rows if r["start"] <= said["end"] and r["end"] >= said["start"] and "5.2 per cent" in r["text"]]
print(f"the EMEA line: {said['speaker']} says '5.2 per cent' in the turn at {mmss(said['start'])}-{mmss(said['end'])}; "
      f"the segment that quotes it: {', '.join(hit) or 'none'}")"""
CELLS["rows"] = heredoc(ROWS_PY)
OUT["rows"] = run_cell(ROWS_PY, LANE + "lane161.install()\n", {"LANE161_NOW": "2026-09-24T08:09:00+00:00"}, cwd=K2)
RW = OUT["rows"]
assert RW.startswith("5 segments of townhall_2026_q1.mp4 in acme's index, against the ground truth's 5 turns:") and RW.count("  segment ") == 5, RW
assert "(the prompt asks for at most 60) -> PASS" in RW and "start before end in every row -> PASS" in RW and "the segment that quotes it: t" in RW, RW

# ------------------------------------------------------------------ step 5: the clip at its second, and step 6: the gate
ASK_PY = """import ast, datetime, json, os, re, subprocess, urllib.request
import google.auth
from google.auth import impersonated_credentials
from google.cloud import storage
P, API = os.environ["PROJECT"], os.environ["API"]
UI = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
Q = "In the FY2026 town hall, what did the CFO say happened to EMEA revenue?"            # golden row mm-03
ns = {}                                                       # the UI's pill and clock, lifted from services/frontend/citations.py
for node in ast.parse(open("services/frontend/citations.py", encoding="utf-8").read()).body:
    if isinstance(node, ast.FunctionDef) and node.name in ("_mmss", "_label"):
        exec(compile(ast.Module([node], []), "citations.py", "exec"), ns)
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                     capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(API + "/v1/stream", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(),
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
sources, answer, event = [], "", None
with urllib.request.urlopen(req, timeout=180) as r:           # the events the UI reads: the packed sources first, then the tokens
    for raw in r:
        line = raw.decode("utf-8").rstrip("\\n")
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: ") and event == "citation":
            c = json.loads(line[6:])
            sources.append({"text": c["quote"], "source_uri": c["source"], "page_start": c.get("page"), "kind": c.get("kind", "text"),
                            "media_url": c.get("media_url"), "start": c.get("start"), "end": c.get("end")})
        elif line.startswith("data: ") and event == "token":
            answer += json.loads(line[6:])["t"]
CITE = re.compile(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]")                   # citations.py's own pattern
cited = [int(n) for g in CITE.findall(answer) for n in g.replace(" ", "").split(",")]
pill = lambda m: "".join(ns["_label"](int(n), sources[int(n) - 1] if 0 < int(n) <= len(sources) else None) for n in m.group(1).replace(" ", "").split(","))
print(f"{len(sources)} sources packed:", " ".join(f"[{i}] {s['kind']}" for i, s in enumerate(sources, 1)))
print("the UI shows:", CITE.sub(pill, answer))
kinds = sorted({sources[n - 1]["kind"] for n in cited if 0 < n <= len(sources)})
print(f"run_eval's rule for mm-03: cited kinds {kinds}, a segment asked for -> {'PASS' if 'segment' in kinds else 'FAIL'}")
truth = json.load(open("evals/corpus/acme/townhall_2026_q1.segments.json", encoding="utf-8"))["segments"]
said = next(t for t in truth if "5.2 per cent" in t["text"])  # the ground truth: the turn in which the CFO says it
print(f"the ground truth: {said['speaker']} says '5.2 per cent' in the turn {ns['_mmss'](said['start'])}-{ns['_mmss'](said['end'])}")
signer = impersonated_credentials.Credentials(source_credentials=google.auth.default()[0], target_principal=UI, lifetime=900,
                                              target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
for n in cited:
    c = sources[n - 1]
    if c["kind"] != "segment":
        continue
    start = int(float(c["start"] or 0))
    holds = c["start"] <= said["end"] and c["end"] >= said["start"]
    print(f"[Clip {n}]: the player opens {c['source_uri'].rsplit('/', 1)[-1]} at {ns['_mmss'](start)}, the clip runs to "
          f"{ns['_mmss'](c['end'])}; it holds the turn -> {'PASS' if holds else 'FAIL'}")
    bucket, name = c["media_url"].removeprefix("gs://").split("/", 1)
    url = storage.Client(project=P, credentials=signer).bucket(bucket).blob(name).generate_signed_url(
        version="v4", expiration=datetime.timedelta(minutes=15), method="GET", credentials=signer)
    print(f"  open it at that second, for 15 minutes, as documind-ui-sa:\\n  {url}#t={start}")"""
CELLS["ask"] = heredoc(ASK_PY)
ASK_PRELUDE = (LANE + "lane161.install()\nlane161.fake_cli()\nimport google.auth, google.auth.impersonated_credentials as _ic\n"
               "google.auth.default = lambda *a, **kw: (object(), lane161.PROJ)\n"
               "class _Signer:\n    def __init__(self, source_credentials=None, target_principal=None, **kw):\n        self.signer_email = target_principal\n"
               "_ic.Credentials = _Signer\n")

CELLS["smoke"] = ("python -m pip install -q fastmcp==3.4.7      # the gate's MCP legs (lesson 5.2 installed it; safe to repeat)\n"
                  'make smoke-media PROJECT="$PROJECT"')
SMOKE_RECIPE = MK[MK.index("\nsmoke-media: guard-project\n"):].split("\n\n", 1)[0]
assert "DOCUMIND_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app" in SMOKE_RECIPE and "DOCUMIND_OUTSIDER_SA=documind-outsider-sa@$(PROJECT)" in SMOKE_RECIPE
assert "\t@NUMBER=" in SMOKE_RECIPE                                       # the recipe is silent: make echoes nothing
URL, MURL = f"http://127.0.0.1:{PORT}", f"http://127.0.0.1:{MCP_PORT}"
SMOKE_PY = ("import runpy, sys\nlane161.install()\nlane161.fake_cli()\nsys.argv = ['smoke_media.py']\n"
            "try:\n    runpy.run_path('smoke/smoke_media.py', run_name='__main__')\nexcept SystemExit as e:\n    print('EXIT', e.code)\n")
WHO = {"MEMBER": UI_SA, "OUTSIDER": OUT_SA}
LIVE_ENV = {"RETRIEVAL_BACKEND": "firestore", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT", "DEMO_MODE": "1"}   # as make up deploys the API
for p_ in (PORT, MCP_PORT, GCS_PORT):
    with socket.socket() as s_:
        assert s_.connect_ex(("127.0.0.1", p_)) != 0, f"port {p_} is taken on this machine"
servers = []
try:
    for tag, code, extra in (("api", f"import lane161; lane161.freeze(); lane161.serve({PORT}, {WHO!r})", LIVE_ENV),
                             ("mcp", f"import lane161; lane161.freeze(); lane161.mcp_serve({MCP_PORT}, {WHO!r})", {"SELF_URL": MURL}),
                             ("gcs", f"import lane161; lane161.freeze(); lane161.gcs_serve({GCS_PORT})", {"LANE161_NOW": "2026-09-24T08:14:00+00:00"})):
        log = open(T / f"{tag}.log", "w", encoding="utf-8")
        servers.append((tag, subprocess.Popen([sys.executable, "-c", code], cwd=str(T if tag != "mcp" else KIT), env={**ENV, **extra},
                                              stdout=log, stderr=subprocess.STDOUT), log))
    for tag, port in (("api", PORT), ("mcp", MCP_PORT), ("gcs", GCS_PORT)):
        for _ in range(200):
            with socket.socket() as s_:
                if s_.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.2)
        else:
            raise SystemExit(f"the {tag} stand-in did not start: " + (T / f"{tag}.log").read_text(encoding="utf-8")[-1500:])
    OUT["ask"] = run_cell(ASK_PY, ASK_PRELUDE, {"API": URL, "LANE161_NOW": "2026-09-24T08:11:00+00:00", **LIVE_ENV}, cwd=K2)
    sm = run_cell(SMOKE_PY, LANE, {"DOCUMIND_API_URL": URL, "DOCUMIND_MCP_URL": MURL, "DOCUMIND_IMPERSONATE_SA": UI_SA, "DOCUMIND_OUTSIDER_SA": OUT_SA,
                                   "LANE161_NOW": "2026-09-24T08:13:00+00:00"}, cwd=KIT)
finally:
    for tag, proc, log in servers:
        proc.terminate()
        proc.wait(timeout=20)
        log.close()
AK = OUT["ask"]
assert AK.rstrip().count("\n") >= 6 and "run_eval's rule for mm-03: cited kinds ['segment'], a segment asked for -> PASS" in AK, AK
assert re.search(r"the UI shows: The CFO said EMEA was the one region that shrank: revenue fell 5\.2 per cent, from 96 crore to 91 crore, "
                 r"because two large renewals in Germany slipped into the first quarter of FY2027 \[Clip \d, \d\d:\d\d\]\.", AK), AK
assert "it holds the turn -> PASS" in AK and f"https://storage.googleapis.com/{PROJ}-uploads/{VIDEO}?X-Goog-Algorithm=GOOG4-RSA-SHA256" in AK, AK
assert "X-Goog-Credential=documind-ui-sa%40" in AK and re.search(r"&X-Goog-Signature=\.\.\.#t=\d+\n", AK), AK
assert sm.rstrip().endswith("EXIT 0"), sm[-1500:]
OUT["smoke"] = sm.rsplit("EXIT 0", 1)[0].rstrip() .replace(URL, API).replace(MURL, MCP_API) + "\n"
SM = OUT["smoke"]
for check in ("generate", "outsider refused", "figure citation", "media documents", "signed PUT", "worker indexed the PUT"):
    assert f"  [PASS] {check}  " in SM, (check, SM)
assert "6 passed, 0 failed" in SM and "[FAIL]" not in SM and "townhall_2026_q1.mp4" in SM and "kinds=['figure']" in SM, SM
assert "127.0.0.1" not in SM and API in SM and MCP_API in SM, SM
N_DOCS = int(re.search(r"media documents  (\d+) of (\d+) indexed documents are media", SM).group(2))
CLIP = re.search(r"\[Clip (\d), (\d\d:\d\d)\]", AK)

# ------------------------------------------------------------------ the panel: what a citation turns into, the kit's rendering
KINDS = ["text", "figure", "table", "segment"]
NS_, PAGES, STARTS, ENDS, MEDIAS, OTHERS, WANTS = [1, 2, 3], [None, 12, 30], [None, 0, 21.6, 59.99, 200.7], [None, 58.0, 230.0], [True, False], \
    ["none", "text", "figure"], ["none", "figure", "segment"]
FILES = {"text": "annual_report_2026.md", "figure": "annual_report_2026_fig3.png", "table": "payment_of_bonus_act_1965_p30.png", "segment": "townhall_2026_q1.mp4"}
QUOTES = {"text": "| EMEA | 96 | 91 | -5.2% |", "figure": "Figure 3: revenue by region, FY2025 against FY2026. EMEA fell from 96 to 91 (-5.2%).",
          "table": "The Fourth Schedule: set on and set off of the allocable surplus, year by year.",
          "segment": "Arjun, the CFO: EMEA is the one region that shrank; revenue fell 5.2 per cent, from 96 crore to 91 crore."}
URI_ = f"gs://{PROJ}-uploads/acme/"
COMBOS = list(itertools.product(KINDS, NS_, PAGES, STARTS, ENDS, MEDIAS, OTHERS, WANTS))


class _St:
    """streamlit, recording what render_with_citations draws."""

    def __init__(self):
        self.calls = []

    def markdown(self, text, unsafe_allow_html=False):
        self.calls.append(["md", text])

    def expander(self, label):
        return contextlib.nullcontext()

    def image(self, url, caption=None):
        self.calls.append(["image", url, caption])

    def video(self, url, start_time=0):
        self.calls.append(["video", url, start_time])

    def caption(self, text):
        self.calls.append(["caption", text])

    def link_button(self, label, url):
        self.calls.append(["link", label, url])


st_ = _St()
sys.modules["streamlit"] = types.SimpleNamespace(markdown=st_.markdown, expander=st_.expander, image=st_.image, video=st_.video,
                                                 caption=st_.caption, link_button=st_.link_button)
_saved_storage = sys.modules.get("google.cloud.storage")
sys.modules["google.cloud.storage"] = types.SimpleNamespace(Client=lambda *a, **kw: None)
cit = types.ModuleType("citations")
exec(compile(src[CITES], str(KIT / CITES), "exec"), cit.__dict__)      # the UI's module, whole
if _saved_storage is not None:
    sys.modules["google.cloud.storage"] = _saved_storage
cit.signed_url = lambda uri, page=None: "SIGNED:" + uri + (f"#page={page}" if page else "")
mod_ns = {}
for node in ast.parse(src[MAIN]).body:
    if isinstance(node, ast.FunctionDef) and node.name == "modality_of":
        exec(compile(ast.Module([node], []), MAIN, "exec"), mod_ns)
PY_SIDE = []
for kind, n, page, start, end, media, other, want in COMBOS:
    chosen = {"text": QUOTES[kind], "source_uri": URI_ + FILES[kind], "page_start": page, "kind": kind,
              "media_url": URI_ + FILES[kind] if media else None, "start": start, "end": end}
    filler = {"text": "a text source", "source_uri": URI_ + "hr_policy_2026.md", "page_start": None, "kind": "text"}
    st_.calls = []
    cit.render_with_citations(f"Revenue in EMEA fell 5.2 per cent [{n}].", [filler] * (n - 1) + [chosen])
    pill = re.findall(r">(\[[^<]*\])</span>", st_.calls[0][1])
    starts = [i for i, c in enumerate(st_.calls) if c[0] == "md" and c[1].startswith("**")]
    entry = st_.calls[starts[-1]:]
    kinds = [kind] + ([] if other == "none" else [other])
    ks = sorted(set(kinds))
    verdict = "not a media row" if want == "none" else "counts" if want in ks else f"cited no {want} (kinds {ks})"
    PY_SIDE.append([pill, entry, mod_ns["modality_of"](kinds), verdict])
assert {r[2] for r in PY_SIDE} == {"text", "image", "video"} and any("[Clip 2, 03:20]" in r[0] for r in PY_SIDE)
assert 'kind_ok = want_kind in kinds' in src[RUN_EVAL] and 'kinds = sorted({c.get("kind", "text") for c in body["citations"]})' in src[RUN_EVAL]

UI_JS = r"""var root = document.getElementById('cc'); if (!root) return;
  var FILES = __FILES__, QUOTES = __QUOTES__, URI = __URI__;
  function pad(x){ return (x < 10 ? '0' : '') + x; }
  function mmss(s){ if (s === null || s === undefined) { return '?'; } var v = Math.trunc(Number(s)); if (isNaN(v)) { return '?'; } return pad(Math.floor(v / 60)) + ':' + pad(v % 60); }
  function label(n, src){ if (!src) { return '[' + n + ']'; } var kind = src.kind || 'text';
    if (kind === 'figure' || kind === 'table') { var page = src.page_start; return '[' + (kind === 'figure' ? 'Fig' : 'Table') + ' ' + n + (page ? ', p.' + page : '') + ']'; }
    if (kind === 'segment') { return '[Clip ' + n + ', ' + mmss(src.start) + ']'; }
    return '[' + n + ']'; }
  function signed(uri, page){ return 'SIGNED:' + uri + (page ? '#page=' + page : ''); }
  function file(uri){ return uri.split('/').pop(); }
  function entry(i, src){ var out = [['md', '**' + label(i, src) + '** ' + src.text.slice(0, 200) + '...']], kind = src.kind || 'text', page = src.page_start;
    if ((kind === 'figure' || kind === 'table') && src.media_url) { out.push(['image', signed(src.media_url), label(i, src) + ' \u00b7 ' + file(src.source_uri)]); }
    else if (kind === 'segment' && src.media_url) { out.push(['video', signed(src.media_url), Math.trunc(Number(src.start || 0))]);
      out.push(['caption', mmss(src.start) + ' \u2013 ' + mmss(src.end) + ' of ' + file(src.source_uri)]); }
    else { out.push(['link', page ? 'Jump to page ' + page : 'Open source', signed(src.source_uri, page)]); }
    return out; }
  function modality(kinds){ if (kinds.indexOf('segment') >= 0) { return 'video'; } if (kinds.indexOf('figure') >= 0 || kinds.indexOf('table') >= 0) { return 'image'; } return 'text'; }
  function verdict(want, kinds){ if (want === 'none') { return 'not a media row'; } var ks = kinds.filter(function(k, i){ return kinds.indexOf(k) === i; }).sort();
    return ks.indexOf(want) >= 0 ? 'counts' : 'cited no ' + want + ' (kinds [' + ks.map(function(k){ return "'" + k + "'"; }).join(', ') + '])'; }
  function world(o){ var src = {text: QUOTES[o.kind], source_uri: URI + FILES[o.kind], page_start: o.page, kind: o.kind, media_url: o.media ? URI + FILES[o.kind] : null, start: o.start, end: o.end};
    var kinds = [o.kind].concat(o.other === 'none' ? [] : [o.other]);
    return [[label(o.n, src)], entry(o.n, src), modality(kinds), verdict(o.want, kinds)]; }
  window.__cc = {world: world};
  var $ = function(id){ return document.getElementById(id); };
  function num(v){ return v === 'none' ? null : Number(v); }
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function row(box, k, v, cls){ box.appendChild(el('b', '', k)); box.appendChild(el('span', cls || '', v)); }
  function show(){ var o = {kind: $('cc-kind').value, n: Number($('cc-n').value), page: num($('cc-page').value), start: num($('cc-start').value), end: num($('cc-end').value),
      media: $('cc-media').checked, other: $('cc-other').value, want: $('cc-want').value};
    var w = world(o), ans = $('cc-answer'), under = $('cc-under'), m;
    ans.textContent = ''; ans.appendChild(document.createTextNode('Revenue in EMEA fell 5.2 per cent ')); ans.appendChild(el('span', 'cc-pill', w[0][0])); ans.appendChild(document.createTextNode('.'));
    under.textContent = ''; row(under, 'The line', w[1][0][1].replace(/^\*\*/, '').replace('**', ''));
    m = w[1][1];
    if (m[0] === 'image') { row(under, 'Then', 'the image itself, inline, captioned \u201c' + m[2] + '\u201d, from a 15-minute signed link'); }
    else if (m[0] === 'video') { row(under, 'Then', 'the video, playing from second ' + m[2] + ' (a 15-minute signed link)'); row(under, 'Caption', w[1][2][1]); }
    else { row(under, 'Then', 'a button, \u201c' + m[1] + '\u201d, to a 15-minute signed link of ' + file(m[2].replace('SIGNED:', '').split('#')[0]) + (m[2].indexOf('#page=') >= 0 ? ' at #page=' + m[2].split('#page=')[1] : '')); }
    row(under, 'Usage row', 'modality ' + w[2]); row(under, 'The eval', w[3], w[3] === 'counts' ? 'pass' : w[3] === 'not a media row' ? '' : 'stop'); }
  ['cc-kind', 'cc-n', 'cc-page', 'cc-start', 'cc-end', 'cc-media', 'cc-other', 'cc-want'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = UI_JS.replace("__FILES__", json.dumps(FILES)).replace("__QUOTES__", json.dumps(QUOTES)).replace("__URI__", json.dumps(URI_))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('cc'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps([list(c) for c in COMBOS]) + ";\n"
        "var out = C.map(function(c){ return window.__cc.world({kind: c[0], n: c[1], page: c[2], start: c[3], end: c[4], media: c[5], other: c[6], want: c[7]}); });\n"
        "process.stdout.write(JSON.stringify(out));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
for i, (a_, b_) in enumerate(zip(JS_SIDE, PY_SIDE)):
    assert a_ == b_, (COMBOS[i], a_, b_)
N_CHECKED = len(COMBOS)
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the contract and the UI's pill, run; no network)",
    "media": "run in the operator shell, in the kit (the town hall synthesised: a minute or two)",
    "retire": "run in the operator shell, in the kit (the transcript withdrawn from acme)",
    "reindex": "run in the operator shell, in the kit (the video uploaded; waits for the worker)",
    "rows": "run in the operator shell, in the kit (reads only)",
    "ask": "run in the operator shell, in the kit (golden row mm-03's question, as the UI asks it)",
    "smoke": "run in the operator shell, in the kit (the gate: a minute or two)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own documind_schemas.py, citations.py and main.py)",
    "media": "(the kit's build_media.py on stand-ins for Text-to-Speech and ffmpeg: your voices, times and file size are the API's and your ffmpeg's)",
    "retire": "(the kit's reconcile.py on a stand-in lane; your doc_key, ids and fingerprint differ)",
    "reindex": "(gcloud's copy lines as '...'; the kit's worker on the stand-in lane, its Gemini call stood in: your doc_key and segment count are yours)",
    "rows": "(the stand-in's segments, one per speaker turn: Gemini cuts your video its own way)",
    "ask": "(the kit's rag-api on the stand-in lane: your pool, clip number and seconds are your lane's; the signature is cut)",
    "smoke": "(the kit's smoke_media.py against the kit's rag-api and MCP server on the stand-in lane; your counts include your own uploads)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
STATS = {"N_CHECKED": str(N_CHECKED), "N_TRANSCRIPT": str(N_TRANSCRIPT), "N_DOCS": str(N_DOCS), "CLIP_N": CLIP.group(1), "CLIP_AT": CLIP.group(2),
         "KV": short(KV)}

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
print(f"kit: build_media.py, reconcile.py, the worker, rag-api, the MCP server and smoke_media.py on a stand-in lane | the clip cited"
      f" [Clip {CLIP.group(1)}, {CLIP.group(2)}] | panel checked against the kit on {N_CHECKED} combinations")
