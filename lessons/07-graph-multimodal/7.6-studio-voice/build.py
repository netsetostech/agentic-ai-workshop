"""Build lesson 7.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Exercise implemented Studio and voice features. The Studio is the UI's tab over the API's /v1/media routes: a prompt
becomes an image through /v1/media/generate - the roster checked, the audit bucket required before anything is spent,
a prompt drawn before served from the media bucket under DEMO_MODE (on by default on the lane), otherwise
gemini-3.1-flash-image, the PNG kept 30 days, one media.generate audit event (the prompt hashed) and one usage row
(event=media, cost_usd 0.039, or 0 on a cache hit). The upload door (/v1/media/upload-url) signs a 15-minute PUT into
the uploads bucket, so the bytes go straight to the bucket and the worker takes the event. The voice is the UI's
voice.py: cached_tts reads an answer with Chirp 3 HD and caches it by the SHA-256 of voice, rate and text; transcribe
turns the microphone's audio into a question, in SPEECH_REGION (asia-south1), trying chirp_3, chirp_2 and long.
Offline: the usage rows media.py writes, which usage events reach tenant_daily (the sink vs the view), and cached_tts
run with its clients stood in. Live: the Studio's own prompt generated twice (a generation, then a DEMO_MODE hit), the
two usage rows from Cloud Logging, the one audit event and a signed link to the image; the door's guards and a signed
PUT of 7.5's video (the worker acks the known bytes); an answer read aloud (a miss, then a hit, saved as ~/answer.ogg);
the answer's audio transcribed where the UI transcribes (empty) and in eu (the words).

Build-time proof: every live cell ran the kit's own code over a stand-in lane (lane162.py, beside this file): rag-api
under uvicorn (its query and media routes, with the kit's roster check), the ingest worker behind a signed-PUT door, and
the UI's voice.py itself, with Text-to-Speech and Speech-to-Text stood in (the recogniser answers only where Google's
pages list a model for hi-IN and en-IN, checked 24 September 2026). The panel is the kit's rules - media.generate's
branches, cached_tts's cache and transcribe's fallback - ported and compared with the kit's own functions on every
combination it offers.
"""
import ast
import hashlib
import html
import itertools
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
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "7.6"
title = "<title>Lesson 7.6 Exercise implemented Studio and voice features - an image, its row, an answer aloud | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
OUT_SA = f"documind-outsider-sa@{PROJ}.iam.gserviceaccount.com"
MCP_SA = f"documind-mcp-sa@{PROJ}.iam.gserviceaccount.com"
PORT, GCS_PORT = 8162, 8362
API = "https://documind-api-NUMBER.asia-south1.run.app"
VIDEO = "acme/townhall_2026_q1.mp4"
Q = "In the FY2026 town hall, what did the CFO say happened to EMEA revenue?"
MEDIA, VOICE, STUDIO, CHAT, SINK, VIEW, AUDIT, STORAGE, CONFIG, DOCS, DEPLOY_API, DEPLOY_UI = (
    "services/rag-api/media.py", "services/frontend/voice.py", "services/frontend/studio.py", "services/frontend/chat.py", "terraform/sink.tf",
    "terraform/sql/tenant_daily.sql", "shared/audit_log.py", "terraform/storage.tf", "services/frontend/.streamlit/config.toml",
    "services/frontend/documents.py", "commands/lesson-12.2.sh", "commands/lesson-12.4.sh")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.sv-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:0 10px;}
.sv-out{margin:6px 0 0;font-size:12.5px;line-height:1.55;}
.sv-out .pass{color:var(--teal-dark);font-weight:600;}
.sv-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "guards": ("services/rag-api/media.py - /v1/media/generate, before anything is spent: the roster, the audit bucket, DEMO_MODE's cache",
               block(MEDIA, '@router.post("/generate")', n=16)),
    "spend": ("services/rag-api/media.py - the spend: the image, stored; the audit event; the usage row",
              block(MEDIA, "    resp = _client.models.generate_content(", n=20)),
    "usage": ("services/rag-api/media.py - the media usage row, in the shape tenant_daily reads",
              block(MEDIA, "def _usage(tenant_id: str, email: str, cost_usd: float, cached: bool, latency_ms: int) -> dict:", n=14)),
    "upload_url": ("services/rag-api/media.py - the upload door: a signed PUT into the uploads bucket, under the tenant's prefix",
                   block(MEDIA, '@router.post("/upload-url")', n=16)),
    "cached_tts": ("services/frontend/voice.py - an answer read aloud: Chirp 3 HD, cached by the SHA-256 of voice, rate and text",
                   block(VOICE, "def cached_tts(", n=17)),
    "transcribe": ("services/frontend/voice.py - the microphone's audio made a question: three models, then an empty string",
                   block(VOICE, "def transcribe(", n=21)),
    "sink": ("terraform/sink.tf - the sink that copies usage rows into BigQuery, and the events it copies",
             block(SINK, 'resource "google_logging_project_sink" "api_to_bq" {', n=14)),
}
assert EXCERPTS["guards"][1].rstrip().endswith('return {"blob": blob.name, "bucket": BUCKET, "cached": True}') and "enforce_membership(" in EXCERPTS["guards"][1]
assert EXCERPTS["spend"][1].rstrip().endswith('return {"blob": blob.name, "bucket": BUCKET, "cached": False}') and '"prompt_sha": key' in EXCERPTS["spend"][1]
assert EXCERPTS["usage"][1].rstrip().endswith('"policy_fallback": 0, "brain": "ui"}') and '"event": "media"' in EXCERPTS["usage"][1]
assert EXCERPTS["upload_url"][1].rstrip().endswith('"hands it to documind-ingest, and list_documents (MCP) shows it indexed."}')
assert EXCERPTS["cached_tts"][1].rstrip().endswith("return audio") and 'f"{voice}|{rate}|ogg|{text}"' in EXCERPTS["cached_tts"][1]
assert EXCERPTS["transcribe"][1].rstrip().endswith("if r.alternatives).strip()") and 'for m in ("chirp_2", "long"):' in EXCERPTS["transcribe"][1]
assert EXCERPTS["sink"][1].rstrip().endswith("}") and '(jsonPayload.event = "query" OR jsonPayload.event = "stream" OR jsonPayload.event = "chat" OR\n' in EXCERPTS["sink"][1]
assert '     jsonPayload.event = "desk" OR jsonPayload.event = "passages" OR\n' in EXCERPTS["sink"][1] and '"media"' not in EXCERPTS["sink"][1]
assert '     (jsonPayload.event = "desk_gate" AND resource.labels.service_name = "documind-chat"))\n' in EXCERPTS["sink"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MEDIA, VOICE, STUDIO, CHAT, SINK, VIEW, AUDIT, STORAGE, CONFIG, DOCS, DEPLOY_API, DEPLOY_UI,
                                                          "services/frontend/requirements.txt", "services/frontend/app.py")}
assert 'IMAGE_MODEL = "gemini-3.1-flash-image"' in src[MEDIA] and "IMAGE_USD = 0.039" in src[MEDIA] and "IMAGE_USD, USD_INR = 0.039, 85" in src[STUDIO]
assert "DEMO_MODE=${DEMO_MODE-1}" in src[DEPLOY_API] and "DEMO_MODE" not in (KIT / "Makefile").read_text(encoding="utf-8")        # on unless turned off
assert "SPEECH_REGION=asia-south1" in src[DEPLOY_UI] and "TTS_CACHE_BUCKET=$PROJECT-tts-cache" in src[DEPLOY_UI]
assert 'REGION = os.environ.get("SPEECH_REGION", "asia-south1")' in src[VOICE] and 'model="chirp_3"' in src[VOICE] and 'language_codes=("hi-IN", "en-IN")' in src[VOICE]
assert "google-cloud-speech==2.40.0" in src["services/frontend/requirements.txt"] and "google-cloud-texttospeech==2.37.0" in src["services/frontend/requirements.txt"]
assert "st.audio(cached_tts(answer[:1500]), format=\"audio/ogg\")" in src[CHAT] and 'st.toggle("Read answers aloud"' in src[CHAT]
assert "return transcribe(audio[\"bytes\"])" in src[CHAT] and 'pages = ["Chat", "Documents", "Studio", "Admin"]' in src["services/frontend/app.py"]
assert "raised AFTER storing the image: a\n# spend with no record" in src[MEDIA] and "the audit bucket is retention-LOCKED for five years" in src[MEDIA]
assert "eight bills and eight\n    # chances for the network to embarrass you" in src[MEDIA] and "This page never\nholds a model client of its own" in src[STUDIO]
assert len(ast.literal_eval(src[MEDIA].split("UPLOAD_TYPES = ", 1)[1].split("\n", 1)[0])) == 7
assert "{'cache hit (DEMO_MODE)' if body.get('cached') else 'generated'} - " in src[STUDIO] and "Rs {cost * USD_INR:.2f}" in src[STUDIO]
assert f"{0.039 * 85:.2f}" == "3.31"                                     # what the Studio's caption shows, and the page quotes
DEFAULT_PROMPT = next(ast.literal_eval(n.value) for n in ast.parse(src[STUDIO]).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DEFAULT_PROMPT")
for bucket in ("tts_cache", "media"):                                    # both are caches: a 30-day delete rule
    body_ = src[STORAGE].split(f'resource "google_storage_bucket" "{bucket}" {{', 1)[1].split("\n}\n", 1)[0]
    assert "condition { age = 30 }" in body_ and 'action { type = "Delete" }' in body_, bucket
assert 'resource "google_storage_bucket_iam_member" "ui_media"' in src[STORAGE] and 'role   = "roles/storage.objectViewer"' in src[STORAGE].split('"ui_media"', 1)[1][:200]
assert '"media.generate", "media.transcribe",' in src[AUDIT] and "{action}-{event['id']}.json" in src[AUDIT]
# 1. the microphone: the UI transcribes in asia-south1, and every failure is swallowed (the region facts are Google's, on the page)
TR = EXCERPTS["transcribe"][1]
assert TR.count("except Exception") == 2 and "log" not in TR and 'return ""   # all STT attempts failed; degrade gracefully' in TR
# 2. media usage rows never reach BigQuery: the sink copies query/stream/chat, tenant_daily reads query/stream/media
assert 'WHERE jsonPayload.event IN ("query", "stream", "media")' in src[VIEW]
# 3. speech is metered and audited nowhere: voice.py logs nothing, and media.transcribe is registered and never emitted
assert "log" not in src[VOICE] and "audit" not in src[VOICE] and "usage" not in src[VOICE]
EMITTERS = sorted(str(p.relative_to(KIT)).replace("\\", "/") for p in pb.kit_runtime_files("*.py") if "media.transcribe" in p.read_text(encoding="utf-8", errors="ignore"))
assert EMITTERS == ["shared/audit_log.py"], EMITTERS
# 4. DEMO_MODE's cache is the prompt alone under the tenant: not the model; and a hit writes no audit row
assert 'key = hashlib.sha256(body.prompt.encode()).hexdigest()[:32]' in src[MEDIA] and 'blob(f"{body.tenant_id}/gen/{key}.png")' in src[MEDIA]
assert "audit_log.emit" not in EXCERPTS["guards"][1]
# 5. the upload door is called by nothing but the smoke; the UI uploads through Streamlit; both buckets' CORS name a placeholder
assert "maxUploadSize = 200" in src[CONFIG] and "blob.upload_from_file(uploaded_file" in src[DOCS] and "Past 32 MB the browser must PUT straight to GCS" in src[MEDIA]
CALLERS = sorted(str(p.relative_to(KIT)).replace("\\", "/") for p in pb.kit_runtime_files("*.py") if "/v1/media/upload-url" in p.read_text(encoding="utf-8", errors="ignore")
                 and "services/rag-api" not in str(p).replace("\\", "/"))                # outside the API that serves it (main.py names it in a comment)
assert CALLERS == ["smoke/smoke_media.py"], CALLERS
for bucket in ("uploads", "media"):
    assert 'origin          = ["https://documind.example.com"]' in src[STORAGE].split(f'resource "google_storage_bucket" "{bucket}" {{', 1)[1].split("\n}\n", 1)[0], bucket

# ------------------------------------------------------------------ the lane as lesson 7.5 left it
sys.path.insert(0, str(KIT))
from shared.documind_corpus import chunk_document  # noqa: E402
LANE162 = (HERE / "lane162.py").read_text(encoding="utf-8")
SUMMARIES = ast.literal_eval(re.search(r"^SUMMARIES = (\[.*?\n\])", LANE162, re.S | re.M).group(1))
SERVED = ast.literal_eval(re.search(r"^SERVED = (\{[^\n]*\})", LANE162, re.M).group(1))
TURNS = [(0.0, 22.0), (22.0, 58.0), (58.0, 70.0), (70.0, 93.0), (93.0, 105.0)]           # 7.5's stand-in segments
MP4 = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + random.Random(1610).randbytes(1_474_000)
KV = "acme_" + hashlib.sha256(MP4).hexdigest()
ROWS, CLAIMS, LEDGER = {}, {}, {}
AT = "2026-09-20T10:00:00+00:00"
for tdir in sorted((KIT / "evals/corpus").iterdir()):
    tenant = tdir.name
    for f in sorted(tdir.iterdir()):
        if f.suffix == ".md" and f.with_suffix(".pdf").exists() or f.name.endswith(".segments.json") or f.suffix in (".mp4", ".png"):
            continue
        data = f.read_bytes()
        sha, uri = hashlib.sha256(data).hexdigest(), f"gs://{PROJ}-uploads/{tenant}/{f.name}"
        dk = f"{tenant}_{sha}"
        md = f.with_suffix(".md")
        if md.exists():
            text = md.read_text(encoding="utf-8")
        else:                                                            # a PDF with no mirror (the POSH Act): its own text
            import pypdf
            text = "\f".join(p.extract_text() or "" for p in pypdf.PdfReader(str(f)).pages)
        text = re.sub(r"\A<!--.*?-->\s*", "", text, flags=re.S)
        cut = chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown", "slug": f.stem}, tenant)
        withdrawn = f"{tenant}/{f.name}" == "acme/townhall_2026_q1.md"   # 16.1 withdrew the transcript
        for i, c in enumerate(cut):
            ROWS[f"{tenant}:{sha}#{i}"] = {"tenant_id": tenant, "text": c["text"], "source_uri": uri, "doc_type": "unknown", "kind": "text",
                                           "doc_key": dk, "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": not withdrawn}
        LEDGER[f"{tenant}~{f.name}"] = {"tenant_id": tenant, "name": f"{tenant}/{f.name}", "gcs_uri": uri, "doc_key": dk, "sha256": sha,
                                        "status": "withdrawn" if withdrawn else "indexed", "generation": "1", "chunks": len(cut)}
        CLAIMS[dk] = {"gcs_uri": uri, "tenant_id": tenant, "status": "superseded" if withdrawn else "indexed", "chunks": len(cut), "generation": "1",
                      "claimed_at": AT, "indexed_at": AT}
URI_V = f"gs://{PROJ}-uploads/{VIDEO}"
for i, ((s, e), summary) in enumerate(zip(TURNS, SUMMARIES)):
    ROWS[f"acme:{KV[5:]}#{i}"] = {"tenant_id": "acme", "text": summary, "source_uri": URI_V, "doc_type": "segment", "kind": "segment", "doc_key": KV,
                                  "locator": f"t{int(s)}-{int(e)}", "media_url": URI_V, "start": s, "end": e, "current": True, "page_start": 1,
                                  "embedding_model": "text-embedding-005", "embedding_version": "1"}
LEDGER["acme~townhall_2026_q1.mp4"] = {"tenant_id": "acme", "name": VIDEO, "gcs_uri": URI_V, "doc_key": KV, "sha256": KV[5:], "status": "indexed",
                                       "generation": "1758000000017000", "chunks": 5}
CLAIMS[KV] = {"gcs_uri": URI_V, "tenant_id": "acme", "status": "indexed", "chunks": 5, "generation": "1758000000017000", "claimed_at": AT, "indexed_at": AT}
ROSTER = {f"tenants/{t}/members": {sa.lower(): {"email": sa.lower()} for sa in (UI_SA, MCP_SA)} for t in ("acme", "zeta", "globex")}

T = Path(tempfile.mkdtemp(prefix="lesson162-"))
shutil.copy(HERE / "lane162.py", T / "lane162.py")
(T / "base.json").write_text(json.dumps({"rows": ROWS, "texts": {}}), encoding="utf-8")
K2 = T / "kit"                                                           # the learner's kit clone, as 16.1 left it: the video in evals/corpus/acme/
for rel in (STUDIO, VOICE):
    (K2 / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(KIT / rel, K2 / rel)
(K2 / "evals/corpus/acme").mkdir(parents=True, exist_ok=True)
(K2 / "evals/corpus/acme/townhall_2026_q1.mp4").write_bytes(MP4)
STATE = {k: T / f"{k}.json" for k in ("fs", "gcs", "stores", "logs")}
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T), "LANE162_KIT": str(KIT), "LANE162_BASE": str(T / "base.json"),
       **{f"LANE162_{k.upper()}": str(p) for k, p in STATE.items()}, "LANE162_TRUTH": str(T / "none.json"), "LANE162_GCSURL": f"http://127.0.0.1:{GCS_PORT}",
       "PYTHONPATH": str(T), "API": API, "AUDIT_BUCKET": f"{PROJ}-audit", "MANAGED_MIRROR": "both", "RAG_LOCATION": "us-central1",
       "EMBEDDING_MODEL": "text-embedding-005", "EMBEDDING_VERSION": "1", "RETENTION_DAYS": "30", "SEARCH_LOCATION": "global"}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "GRAPH_", "SPANNER_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR",
                                           "ROUTING", "SPEND_", "BUDGET_", "EMBED_", "BQ_", "DOCAI_", "BATCH_", "DEMO_MODE", "DOCUMIND_", "SELF_URL",
                                           "TTS_", "SPEECH_"))]:
    ENV.pop(k)
fs0 = {"tenant_settings": {"acme": {"data_region": "any"}, "zeta": {"data_region": "any", "retrieval_backend": "vertex_search"},
                           "globex": {"data_region": "in"}}, "sources": LEDGER, "documents": CLAIMS, **ROSTER}
gcs0 = {"_gen": 1758000000017000, f"{PROJ}-uploads": {VIDEO: [{"gen": "1758000000017000", "b64": "", "ct": "video/mp4", "created": AT}]}}   # the next generation is newer than the ledger's
for k, v in (("fs", fs0), ("stores", {"corpora": ["acme", "zeta"], "data_stores": ["acme", "zeta"], "rag": {}, "vs": {}, "n": 0}), ("gcs", gcs0),
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


LANE = "import lane162\nlane162.freeze()\n"

# ------------------------------------------------------------------ step 3: the Studio's and the voice's rules, run (offline, on the kit)
RULES_PY = """import ast, hashlib, os, re, sys, types
# 1. the Studio's usage row, as media.py writes it (media.py builds its clients at import, so _usage() is lifted out)
src = open("services/rag-api/media.py", encoding="utf-8").read()
ns = {"IMAGE_MODEL": re.search(r'IMAGE_MODEL = "([^"]+)"', src).group(1)}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name == "_usage":
        exec(compile(ast.Module([node], []), "media.py", "exec"), ns)
USD = float(re.search(r"IMAGE_USD = ([0-9.]+)", src).group(1))
for cached in (False, True):
    row = ns["_usage"]("acme", "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", USD, cached, 180 if cached else 7400)
    print(f"1. {'a DEMO_MODE hit' if cached else 'a generation'}:", {k: row[k] for k in ("event", "modality", "model", "tokens_in", "cost_usd", "cached")})
# 2. which usage events reach tenant_daily: the sink copies some into BigQuery, the view reads others
sink = open("terraform/sink.tf", encoding="utf-8").read()
view = open("terraform/sql/tenant_daily.sql", encoding="utf-8").read()
copied = set(re.findall(r'jsonPayload\\.event = "(\\w+)"', sink))
read = set(re.findall(r'"(\\w+)"', view.split("WHERE jsonPayload.event IN (", 1)[1].split(")", 1)[0]))
for event in sorted(copied | read):
    print(f"2. event={event:11} {'copied' if event in copied else 'never copied':12} by the sink, {'read' if event in read else 'never read'} by tenant_daily")
# 3. the UI's cached_tts, run with its clients stood in: a bucket in memory, a voice that counts its calls
store, said = {}, []
class Blob:
    def __init__(self, name): self.name = name
    def exists(self): return self.name in store
    def download_as_bytes(self): return store[self.name]
    def upload_from_string(self, data, content_type=None): store[self.name] = data
class Voice:
    def streaming_synthesize(self, requests):
        reqs = list(requests)
        said.append(reqs[0].streaming_config.voice.name)
        yield types.SimpleNamespace(audio_content=b"OggS" + reqs[1].input.text.encode())
Kw = lambda **kw: types.SimpleNamespace(**kw)
for name, attrs in (("streamlit", {}), ("google.cloud.speech_v2", {"SpeechClient": lambda **kw: None}),
                    ("google.cloud.speech_v2.types", {}), ("google.cloud.speech_v2.types.cloud_speech", {}),
                    ("google.cloud.storage", {"Client": lambda: types.SimpleNamespace(bucket=lambda n: types.SimpleNamespace(blob=Blob))}),
                    ("google.cloud.texttospeech", {"TextToSpeechClient": Voice, "StreamingSynthesizeConfig": Kw, "VoiceSelectionParams": Kw,
                                                   "StreamingAudioConfig": Kw, "AudioEncoding": Kw(OGG_OPUS="OGG_OPUS"),
                                                   "StreamingSynthesizeRequest": Kw, "StreamingSynthesisInput": Kw})):
    sys.modules[name] = types.ModuleType(name)
    sys.modules[name].__dict__.update(attrs)
sys.modules["google.cloud.speech_v2.types"].cloud_speech = sys.modules["google.cloud.speech_v2.types.cloud_speech"]
os.environ.update(GOOGLE_CLOUD_PROJECT="documind-ai-YOUR-ID", TTS_CACHE_BUCKET="documind-ai-YOUR-ID-tts-cache")
sys.path.insert(0, "services/frontend")
import voice                                                  # the UI's module, unchanged
text = "EMEA revenue fell 5.2 per cent, from 96 crore to 91 crore."      # the Studio's own text to speak
for n, v in ((1, "en-IN-Chirp3-HD-Kore"), (2, "en-IN-Chirp3-HD-Kore"), (3, "hi-IN-Chirp3-HD-Kore")):
    before = len(said)
    voice.cached_tts(text, voice=v, lang=v[:5])
    print(f"3. read aloud {n}, {v}: {'synthesised, then cached' if len(said) > before else 'read back from the cache'} "
          f"({len(store)} object{'s' if len(store) > 1 else ''} in the bucket)")
key = hashlib.sha256(f"en-IN-Chirp3-HD-Kore|1.0|ogg|{text}".encode()).hexdigest()
print(f"   the first object: tts/{key[:16]}....ogg, the SHA-256 of 'en-IN-Chirp3-HD-Kore|1.0|ogg|' and the text")"""
CELLS = {"rules": heredoc(RULES_PY)}
OUT = {"rules": run_cell(RULES_PY, cwd=KIT)}
RU = OUT["rules"]
assert "1. a generation: {'event': 'media', 'modality': 'image', 'model': 'gemini-3.1-flash-image', 'tokens_in': 0, 'cost_usd': 0.039, 'cached': False}" in RU, RU
assert "'cost_usd': 0.0, 'cached': True}" in RU and "2. event=media       never copied by the sink, read by tenant_daily" in RU, RU
assert "2. event=chat        copied       by the sink, never read by tenant_daily" in RU, RU
assert all(f"2. event={ev:11} copied       by the sink, never read by tenant_daily" in RU for ev in ("desk", "passages", "desk_shadow", "desk_gate")), RU
assert "read aloud 1, en-IN-Chirp3-HD-Kore: synthesised, then cached (1 object in the bucket)" in RU and "read aloud 2, en-IN-Chirp3-HD-Kore: read back from the cache" in RU, RU
assert "read aloud 3, hi-IN-Chirp3-HD-Kore: synthesised, then cached (2 objects in the bucket)" in RU, RU

# ------------------------------------------------------------------ steps 4 to 6: the Studio, the door, the voice
STUDIO_PY = """import ast, datetime as dt, json, os, subprocess, time, urllib.request
import google.auth
from google.auth import impersonated_credentials
from google.cloud import storage
P, API = os.environ["PROJECT"], os.environ["API"]
UI = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
PROMPT = next(ast.literal_eval(n.value) for n in ast.parse(open("services/frontend/studio.py", encoding="utf-8").read()).body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DEFAULT_PROMPT")     # the Studio tab's own prompt
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                     capture_output=True, text=True, check=True).stdout.strip()
since = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for n in (1, 2):                                              # the second is DEMO_MODE's to serve
    req = urllib.request.Request(API + "/v1/media/generate", data=json.dumps({"prompt": PROMPT, "tenant_id": "acme"}).encode(),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    body = json.load(urllib.request.urlopen(req, timeout=180))
    print(f"generate {n}: {body}")
time.sleep(15)                                                # a moment for Cloud Logging to hold the rows
rows = json.loads(subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                                  f'AND jsonPayload.event="media" AND timestamp>="{since}"', f"--project={P}", "--format=json", "--limit=10"],
                                 capture_output=True, text=True, check=True).stdout)
print(f"the usage rows since {since} (Cloud Logging, oldest first):")
for e in reversed(rows):
    j = e["jsonPayload"]
    print(f"  tenant {j['tenant']}, modality {j['modality']}, model {j['model']}, cost_usd {j['cost_usd']}, cached {j['cached']}, user {j['user']}")
start = dt.datetime.fromisoformat(since.replace("Z", "+00:00"))
events = [json.loads(b.download_as_text()) for b in storage.Client(project=P).bucket(f"{P}-audit").list_blobs(
    prefix=f"{start:%Y/%m/%d}/acme/media.generate-") if b.time_created >= start]
print(f"the audit events since then, in {P}-audit (kept five years): {len(events)}")
for ev in events:
    print(f"  {ev['action']} by {ev['actor']['user_email']}: {ev['target']['blob']}, meta {ev['meta']}")
signer = impersonated_credentials.Credentials(source_credentials=google.auth.default()[0], target_principal=UI, lifetime=900,
                                              target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
url = storage.Client(project=P, credentials=signer).bucket(body["bucket"]).blob(body["blob"]).generate_signed_url(
    version="v4", expiration=dt.timedelta(minutes=15), method="GET", credentials=signer)
print(f"the image, for 15 minutes, as documind-ui-sa (the Studio's own signer):\\n  {url}")"""
CELLS["studio"] = heredoc(STUDIO_PY)

DOOR_PY = """import datetime as dt, hashlib, json, os, subprocess, time, urllib.error, urllib.parse, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
UI = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                     capture_output=True, text=True, check=True).stdout.strip()


def door(filename, content_type):                             # POST /v1/media/upload-url, as a roster member
    q = urllib.parse.urlencode({"filename": filename, "content_type": content_type, "tenant_id": "acme"})
    req = urllib.request.Request(f"{API}/v1/media/upload-url?{q}", data=b"", method="POST", headers={"Authorization": "Bearer " + tok})
    try:
        return 200, json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()).get("detail")


for fn, ct in (("townhall.zip", "application/zip"), ("../globex/townhall_2026_q1.mp4", "video/mp4")):
    print(f"upload-url {fn} as {ct}: {door(fn, ct)}")
code, body = door("townhall_2026_q1.mp4", "video/mp4")
print(f"upload-url townhall_2026_q1.mp4 as video/mp4: {code}, a PUT into gs://{body['bucket']}/{body['blob']}, signed for 15 minutes")
data = open("evals/corpus/acme/townhall_2026_q1.mp4", "rb").read()        # lesson 7.5's video
since = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
put = urllib.request.Request(body["url"], data=data, method="PUT", headers={"Content-Type": "video/mp4"})
print(f"PUT {len(data):,} bytes straight to the bucket: HTTP {urllib.request.urlopen(put, timeout=300).status}")
key = "acme_" + hashlib.sha256(data).hexdigest()              # the worker's claim key: the bytes' own hash
for _ in range(30):
    time.sleep(10)
    rows = json.loads(subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
                                      f'AND jsonPayload.doc_key="{key}" AND timestamp>="{since}"', f"--project={P}", "--format=json", "--limit=5"],
                                     capture_output=True, text=True, check=True).stdout)
    if rows:
        break
for e in reversed(rows):
    print("the worker:", json.dumps(e["jsonPayload"]))"""
CELLS["door"] = heredoc(DOOR_PY)

VOICE_SETUP = """P = os.environ["PROJECT"]
os.environ.update(GOOGLE_CLOUD_PROJECT=P, TTS_CACHE_BUCKET=f"{P}-tts-cache", SPEECH_REGION="asia-south1")     # the UI's own settings
sys.modules["streamlit"] = types.ModuleType("streamlit")    # voice.py imports streamlit and never calls it
sys.path.insert(0, "services/frontend")
import voice                                                  # the UI's module, unchanged"""
SPEAK_PY = """import hashlib, json, os, subprocess, sys, types, urllib.request
""" + VOICE_SETUP + """
API, UI = os.environ["API"], f"documind-ui-sa@{P}.iam.gserviceaccount.com"
Q = "In the FY2026 town hall, what did the CFO say happened to EMEA revenue?"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                     capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(),
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
answer = json.load(urllib.request.urlopen(req, timeout=180))["answer"]
print("the answer:", answer)
text = answer[:1500]                                          # what chat.py reads aloud: the first 1,500 characters
key = hashlib.sha256(f"en-IN-Chirp3-HD-Kore|1.0|ogg|{text}".encode()).hexdigest()
blob = voice.TTS_CACHE_BUCKET.blob(f"tts/{key}.ogg")
for n in (1, 2):
    hit = blob.exists()
    audio = voice.cached_tts(text)
    print(f"read aloud {n}: {'a hit, read back from' if hit else 'a miss, synthesised by Chirp 3 HD and written to'} "
          f"gs://{P}-tts-cache/tts/{key[:12]}....ogg ({len(audio):,} bytes of Ogg Opus)")
path = os.path.expanduser("~/answer.ogg")
open(path, "wb").write(audio)
print("saved ~/answer.ogg: in Cloud Shell, cloudshell download ~/answer.ogg hands it to your browser to play")"""
CELLS["speak"] = ("python -m pip install -q google-cloud-speech==2.40.0 google-cloud-texttospeech==2.37.0   # the UI image's two speech clients\n"
                  + heredoc(SPEAK_PY))
LISTEN_PY = """import importlib, os, sys, types
""" + VOICE_SETUP + """
audio = open(os.path.expanduser("~/answer.ogg"), "rb").read()
print(f"transcribe() where the UI runs it, asia-south1: {voice.transcribe(audio)!r}")
os.environ["SPEECH_REGION"] = "eu"                          # the same function, pointed at a location Google lists chirp_3 in
voice = importlib.reload(voice)
print(f"transcribe() in eu: {voice.transcribe(audio)!r}")"""
CELLS["listen"] = heredoc(LISTEN_PY)

API_ENV = {"RETRIEVAL_BACKEND": "firestore", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT", "DEMO_MODE": "1", "LANE162_NOW": "2026-09-24T08:10:05+00:00"}
CELL_PRE = LANE + "lane162.install()\nlane162.fake_cli()\nlane162.fake_time()\n"
SIGNER_PRE = ("import google.auth, google.auth.impersonated_credentials as _ic\ngoogle.auth.default = lambda *a, **kw: (object(), lane162.PROJ)\n"
              "class _Signer:\n    def __init__(self, source_credentials=None, target_principal=None, **kw):\n        self.signer_email = target_principal\n"
              "_ic.Credentials = _Signer\n")
URL = f"http://127.0.0.1:{PORT}"
for p_ in (PORT, GCS_PORT):
    with socket.socket() as s_:
        assert s_.connect_ex(("127.0.0.1", p_)) != 0, f"port {p_} is taken on this machine"
servers = []
try:
    for tag, code, extra in (("api", f"import lane162; lane162.freeze(); lane162.serve({PORT}, {{'MEMBER': {UI_SA!r}, 'OUTSIDER': {OUT_SA!r}}})", API_ENV),
                             ("gcs", f"import lane162; lane162.freeze(); lane162.gcs_serve({GCS_PORT})", {"LANE162_NOW": "2026-09-24T08:14:00+00:00"})):
        log = open(T / f"{tag}.log", "w", encoding="utf-8")
        servers.append((tag, subprocess.Popen([sys.executable, "-c", code], cwd=str(T), env={**ENV, **extra}, stdout=log, stderr=subprocess.STDOUT), log))
    for tag, port in (("api", PORT), ("gcs", GCS_PORT)):
        for _ in range(200):
            with socket.socket() as s_:
                if s_.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.2)
        else:
            raise SystemExit(f"the {tag} stand-in did not start: " + (T / f"{tag}.log").read_text(encoding="utf-8")[-1500:])
    OUT["studio"] = run_cell(STUDIO_PY, CELL_PRE + SIGNER_PRE, {"API": URL, "LANE162_NOW": "2026-09-24T08:10:00+00:00"}, cwd=K2)
    OUT["door"] = run_cell(DOOR_PY, CELL_PRE, {"API": URL, "LANE162_NOW": "2026-09-24T08:13:00+00:00"}, cwd=K2)
    OUT["speak"] = run_cell(SPEAK_PY, CELL_PRE + "lane162.voice_stubs()\n", {"API": URL, "LANE162_NOW": "2026-09-24T08:15:00+00:00"}, cwd=K2)
    OUT["listen"] = run_cell(LISTEN_PY, LANE + "lane162.install()\nlane162.voice_stubs()\n", {"LANE162_NOW": "2026-09-24T08:16:00+00:00"}, cwd=K2)
finally:
    for tag, proc, log in servers:
        proc.terminate()
        proc.wait(timeout=20)
        log.close()
KEY = hashlib.sha256(DEFAULT_PROMPT.encode()).hexdigest()[:32]
ST = OUT["studio"]
assert f"generate 1: {{'blob': 'acme/gen/{KEY}.png', 'bucket': '{PROJ}-media', 'cached': False}}" in ST, ST
assert f"generate 2: {{'blob': 'acme/gen/{KEY}.png', 'bucket': '{PROJ}-media', 'cached': True}}" in ST, ST
assert ST.count("  tenant acme, modality image, model gemini-3.1-flash-image, ") == 2 and "cost_usd 0.039, cached False" in ST and "cost_usd 0.0, cached True" in ST, ST
assert "(kept five years): 1\n" in ST and f"'prompt_sha': '{KEY}'" in ST and "'synthid': True" in ST, ST
assert f"https://storage.googleapis.com/{PROJ}-media/acme/gen/{KEY}.png?X-Goog-Algorithm=GOOG4-RSA-SHA256" in ST, ST
DR = OUT["door"]
assert "upload-url townhall.zip as application/zip: (400, \"content_type must be one of [" in DR, DR
assert "upload-url ../globex/townhall_2026_q1.mp4 as video/mp4: (400, 'filename must be a bare name')" in DR, DR
assert f"a PUT into gs://{PROJ}-uploads/{VIDEO}, signed for 15 minutes" in DR and f"PUT {len(MP4):,} bytes straight to the bucket: HTTP 200" in DR, DR
assert f'the worker: {{"event": "ingest_duplicate", "doc_key": "{KV}"}}' in DR, DR
SP = OUT["speak"]
assert "the answer: The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent" in SP, SP
assert "read aloud 1: a miss, synthesised by Chirp 3 HD and written to" in SP and "read aloud 2: a hit, read back from" in SP, SP
LI = OUT["listen"]
assert "transcribe() where the UI runs it, asia-south1: ''" in LI and "transcribe() in eu: 'The CFO said EMEA was the one region that shrank" in LI, LI

# ------------------------------------------------------------------ the panel: one Studio request, one answer aloud, one question spoken
STUDIO_COMBOS = list(itertools.product([True, False], repeat=5))          # member, audit bucket, DEMO_MODE, drawn before, an image back
VOICES = ["en-IN-Chirp3-HD-Kore", "en-IN-Chirp3-HD-Charon", "hi-IN-Chirp3-HD-Kore"]
SPEAK_COMBOS = list(itertools.product(VOICES, [True, False]))
REGIONS = ["asia-south1", "asia-southeast1", "eu", "us"]
CHECK_PY = """import hashlib, importlib, itertools, json, logging, os, sys, types
import lane162
lane162.install(); lane162.stubs(); lane162.voice_stubs()
sys.modules["streamlit"] = types.ModuleType("streamlit")
sys.path[:0] = [lane162.KIT, os.path.join(lane162.KIT, "services", "rag-api"), os.path.join(lane162.KIT, "services", "frontend")]
rows = []
class Rows(logging.Handler):
    def emit(self, r):
        try:
            j = json.loads(r.getMessage())
        except ValueError:
            return
        if j.get("event") == "media":
            rows.append([j["cached"], j["cost_usd"]])
logging.getLogger("documind-api").addHandler(Rows())
logging.getLogger("documind-api").setLevel(logging.INFO)
import media                                                    # the API's media routes, unchanged
from fastapi import HTTPException
P = lane162.PROJ
MEMBER, OUTSIDER = "documind-ui-sa@" + P + ".iam.gserviceaccount.com", "documind-outsider-sa@" + P + ".iam.gserviceaccount.com"
PROMPT = "a chart"
out = {"studio": [], "speak": [], "listen": []}
for member, audit, demo, before, image in %r:
    st = lane162._get("gcs"); st.pop(P + "-media", None); st.pop(P + "-audit", None); lane162._put("gcs")
    if before:
        lane162.Bucket(P + "-media").blob("acme/gen/%%s.png" %% hashlib.sha256(PROMPT.encode()).hexdigest()[:32]).upload_from_string(b"png", "image/png")
    media.AUDIT_BUCKET, media.DEMO_MODE, lane162.IMAGE_OK[0] = (P + "-audit") if audit else "", demo, image
    del rows[:]
    calls = lane162.IMAGE_CALLS[0]
    try:
        body = media.generate(media.GenerateIn(prompt=PROMPT, tenant_id="acme"), user={"email": MEMBER if member else OUTSIDER})
        status = 200
    except HTTPException as e:
        status, body = e.status_code, None
    audits = sum(1 for n in lane162._objects(P + "-audit") if "media.generate-" in n)
    out["studio"].append([status, lane162.IMAGE_CALLS[0] - calls, list(rows), audits, bool(body and body.get("cached"))])
os.environ["TTS_CACHE_BUCKET"] = P + "-tts-cache"
import voice                                                    # the UI's voice, unchanged
text = "EMEA revenue fell 5.2 per cent, from 96 crore to 91 crore."
for v, before in %r:
    st = lane162._get("gcs"); st.pop(P + "-tts-cache", None); lane162._put("gcs")
    name = "tts/%%s.ogg" %% hashlib.sha256(("%%s|1.0|ogg|%%s" %% (v, text)).encode()).hexdigest()
    if before:
        lane162.Bucket(P + "-tts-cache").blob(name).upload_from_string(b"OggS", "audio/ogg")
    calls = lane162.TTS_CALLS[0]
    voice.cached_tts(text, voice=v, lang=v[:5])
    out["speak"].append([lane162.TTS_CALLS[0] - calls, lane162.Bucket(P + "-tts-cache").blob(name).exists()])
audio = voice.cached_tts("How long is the notice period for a confirmed employee?")
for region in %r:
    os.environ["SPEECH_REGION"] = region
    voice = importlib.reload(voice)
    del lane162.TRIED[:]
    said = voice.transcribe(audio)
    out["listen"].append([said != "", [m for _, m in lane162.TRIED]])
print("RESULT " + json.dumps(out))""" % (STUDIO_COMBOS, SPEAK_COMBOS, REGIONS)
PY_SIDE = result_of(run_cell(CHECK_PY, LANE, {"DEMO_MODE": "1"}, cwd=T))
assert {r[0] for r in PY_SIDE["studio"]} == {200, 403, 502, 503}, PY_SIDE["studio"]
assert PY_SIDE["listen"] == [[False, ["chirp_3", "chirp_2", "long"]], [True, ["chirp_3", "chirp_2"]], [True, ["chirp_3"]], [True, ["chirp_3"]]], PY_SIDE["listen"]
shutil.rmtree(T, ignore_errors=True)

UI_JS = r"""var root = document.getElementById('sv'); if (!root) return;
  var SERVED = __SERVED__, ORDER = ['chirp_3', 'chirp_2', 'long'], USD = __USD__;
  function studio(o){ if (!o.member) { return [403, 0, [], 0, false]; } if (!o.audit) { return [503, 0, [], 0, false]; }
    if (o.demo && o.before) { return [200, 0, [[true, 0]], 0, true]; } if (!o.image) { return [502, 1, [], 0, false]; }
    return [200, 1, [[false, USD]], 1, false]; }
  function speak(before){ return [before ? 0 : 1, true]; }
  function listen(region){ var tried = [], served = SERVED[region] || []; for (var i = 0; i < ORDER.length; i++) { tried.push(ORDER[i]); if (served.indexOf(ORDER[i]) >= 0) { return [true, tried]; } } return [false, tried]; }
  window.__sv = {studio: studio, speak: speak, listen: listen};
  var $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function line(box, text, cls){ box.appendChild(el('div', cls || '', text)); }
  var WHY = {403: '403: not a member of this tenant. Refused before anything is spent.', 503: '503: AUDIT_BUCKET is not set on this service. Refused before the model is called.',
    502: '502: the model returned no image part. It was called, and Google bills that call; no usage row, no audit row, no image kept.'};
  function show(){ var s = studio({member: $('sv-who').value === 'member', audit: $('sv-audit').value === 'set', demo: $('sv-demo').value === '1', before: $('sv-before').value === 'yes', image: $('sv-image').value === 'yes'});
    var b = $('sv-studio'); b.textContent = '';
    if (s[0] !== 200) { line(b, WHY[s[0]], 'stop'); }
    else if (s[4]) { line(b, '200: served from the media bucket (DEMO_MODE). No model call.', 'pass'); line(b, 'Usage row: cost_usd 0, cached true. No audit row.'); }
    else { line(b, '200: drawn by gemini-3.1-flash-image and kept in the media bucket for 30 days.', 'pass'); line(b, 'Usage row: cost_usd ' + USD + ' (Rs ' + (USD * 85).toFixed(2) + '), cached false. One media.generate audit row, kept five years.'); }
    var p = speak($('sv-played').value === 'yes'), v = $('sv-voice').value, q = $('sv-speak'); q.textContent = '';
    line(q, p[0] ? 'A miss: ' + v + ' synthesises the text (Chirp 3 HD, streamed as Ogg Opus), and the audio is written to the TTS bucket.' : 'A hit: the same bytes, read back from the TTS bucket. Nothing is synthesised.', p[0] ? '' : 'pass');
    line(q, 'Either way the object stays until the bucket’s 30-day rule deletes it; then the next play is a miss again.');
    var r = listen($('sv-region').value), m = $('sv-mic'); m.textContent = '';
    line(m, 'transcribe() tries ' + r[1].join(', then ') + '.');
    line(m, r[0] ? r[1][r[1].length - 1] + ' answers: the words become the question.' : 'None answers: every error is swallowed, and the question is an empty string, so nothing is asked and nothing says why.', r[0] ? 'pass' : 'stop'); }
  ['sv-who', 'sv-audit', 'sv-demo', 'sv-before', 'sv-image', 'sv-voice', 'sv-played', 'sv-region'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = UI_JS.replace("__SERVED__", json.dumps(SERVED)).replace("__USD__", "0.039")
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('sv'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var S = " + json.dumps(STUDIO_COMBOS) + ", V = " + json.dumps(SPEAK_COMBOS) + ", R = " + json.dumps(REGIONS) + ";\n"
        "var G = window.__sv;\n"
        "process.stdout.write(JSON.stringify({studio: S.map(function(c){ return G.studio({member: c[0], audit: c[1], demo: c[2], before: c[3], image: c[4]}); }),\n"
        "  speak: V.map(function(c){ return G.speak(c[1]); }), listen: R.map(function(r){ return G.listen(r); })}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
for part in ("studio", "speak", "listen"):
    for i, (a_, b_) in enumerate(zip(JS_SIDE[part], PY_SIDE[part])):
        assert a_ == b_, (part, i, a_, b_)
N_CHECKED = len(STUDIO_COMBOS) + len(SPEAK_COMBOS) + len(REGIONS)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the rules, run; no network)",
    "studio": "run in the operator shell, in the kit (one image, then a DEMO_MODE hit)",
    "door": "run in the operator shell, in the kit (two refusals, then lesson 7.5's video through the door)",
    "speak": "run in the operator shell, in the kit (one answer, read aloud twice)",
    "listen": "run in the operator shell, in the kit (the answer's audio, transcribed twice)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own media.py, sink.tf, tenant_daily.sql and voice.py)",
    "studio": "(the kit's rag-api on a stand-in lane with DEMO_MODE=1, as make up deploys it; your blob is the same, your times and signature are yours)",
    "door": "(the kit's rag-api and ingest worker on the stand-in lane; your doc_key is your video's)",
    "speak": "(the kit's rag-api and voice.py on the stand-in lane, Text-to-Speech stood in: your byte counts are Chirp 3 HD's)",
    "listen": "(voice.py on the stand-in lane: its recogniser answers only where Google's pages list a model for hi-IN and en-IN; yours is Google's)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
STATS = {"N_CHECKED": str(N_CHECKED), "KEY": KEY, "KEY8": KEY[:8]}

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
print(f"kit: rag-api (generate, upload-url, query), the worker and voice.py on a stand-in lane | an image, a DEMO_MODE hit, two usage rows,"
      f" one audit event; an answer aloud; transcription empty in asia-south1 | panel checked against the kit on {N_CHECKED} cases")
