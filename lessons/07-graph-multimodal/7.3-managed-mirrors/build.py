"""Build lesson 7.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Configure and query managed retrieval mirrors. services/ingest/managed.py copies each version the worker makes current
into the tenant's Vertex AI RAG Engine corpus (us-central1) and Vertex AI Search data store (global) - the stores the
rag_engine and vertex_search retrieval backends read - but only where the tenant's data_region lets the text go
(tenant_settings/{tenant}: `any`, or `in`, which an absent or unreadable policy also means; shared/tenancy.permits).
A forbidden store is one mirror_policy_skipped line; every copy is a doc.mirror audit event and a `mirrored` stamp on
the ledger row. The API reads a store for a tenant pinned to it (make tenant-backend), held against the same policy:
an `in` tenant pinned to a store is served from the kit's own index with policy_fallback 1. A store's text comes back
as chunks of the kit's contract, their ids minted from the text (#rag-, #vs-), found_by the store.
Offline: the kit's Mirror with two stand-in stores and a policy - a copy, two skips, a policy turned to `in`, a
retirement. Live: the policies, the pins and make managed-status; acme pinned back to RAG Engine, three tenants asked,
and the cited chunk found in the kit's own retrieve() with found_by rag_engine; a note uploaded to globex (`in`) and the
worker's mirror_policy_skipped lines with the ledger row's empty `mirrored`; globex pinned to a store and served from
the kit's index anyway.

Build-time proof: the offline cell runs on the kit. The live cells ran the kit's own tenancy CLI, managed.py (--status,
and the Mirror the worker holds), rag-api (under uvicorn) and retriever over a stand-in lane: the three tenants' corpus
as evals/upload.sh sends it (the doc_keys are the files' own hashes), Firestore in JSON files, RAG Engine as a corpus
per `any` tenant cut 512/100 and ranked by word overlap, Vertex AI Search as a data store per `any` tenant answering
with extractive segments, Gemini as a reader of the packed clause. The panel is the kit's rules - Mirror.after_swap
with the worker's guard, choose_for, retrieval_backend_for and the store dispatch - ported and checked against the
kit's code on every combination of its settings.
"""
import html
import json
import os
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
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "7.3"
title = "<title>Lesson 7.3 Configure and query managed retrieval mirrors - a copy outside India, by the tenant's leave | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8153
API = "https://documind-api-NUMBER.asia-south1.run.app"
Q_NOTICE = "How long is the notice period for a confirmed employee?"
Q_MSA = "How much notice does either party give to end the Globex agreement for convenience?"
NOTE_NAME = "globex_visitor_note_2026.md"
MANAGED, TENANCY, MAIN, RET, WORKER = ("services/ingest/managed.py", "shared/tenancy.py", "services/rag-api/main.py",
                                       "services/rag-api/retriever.py", "services/ingest/main.py")

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
.mm-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:0 10px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "policy": ("shared/tenancy.py - the policy: `in` unless the tenant's settings say `any`, and the one rule a store's region is held to",
               block(TENANCY, "def policy_of(doc: dict | None) -> str:", n=5) + "\n\n\n"
               + block(TENANCY, "def permits(policy: str, region: str | None) -> bool:", n=6)),
    "permitted": ("services/ingest/managed.py - Mirror.permitted(): the stores a tenant's text may go to; a forbidden one is said once, then silence",
                  block(MANAGED, "    def permitted(self, tenant_id: str, doc_key: str, op: str) -> list:", n=17)),
    "after_swap": ("services/ingest/managed.py - after_swap(): the text into the permitted stores, the replaced version out of every store, the ledger stamped",
                   block(MANAGED, "    def after_swap(self, doc, text: str, gone: dict, meta: dict | None = None) -> None:", n=10)),
    "guard": ("services/ingest/main.py - the worker calls the mirror only for a version with text",
              block(WORKER, "        if _mirror.active and text is not None:", n=2)),
    "stores": ("Makefile - managed-stores, which make up runs: a corpus per `any` tenant, then the demo's pins",
               block("Makefile", "managed-stores: guard-project", n=6)),
    "status": ("services/ingest/managed.py - status(): what the ledger calls current, which every store is held against",
               block(MANAGED, "    current: dict[str, set] = {}", n=9)),
    "fallback": ("services/rag-api/main.py - retrieval_backend_for(): a pin to a store, held against the tenant's policy on every request",
                 block(MAIN, "def retrieval_backend_for(tenant_id: str, backend: str) -> tuple[str, int]:", n=11)),
    "mapping": ("services/rag-api/retriever.py - a RAG Engine context made a chunk of the kit's contract: the version's row, an id from the text, found_by",
                block(RET, "        chunk = {\"id\": f\"{tenant_id}:{doc_key}#rag-", n=6)),
}
assert EXCERPTS["policy"][1].rstrip().endswith('return str(region or "").strip().lower().startswith(INDIA_REGION_PREFIXES)')
assert 'return region if region in DATA_REGIONS else "in"' in EXCERPTS["policy"][1]
assert EXCERPTS["permitted"][1].rstrip().endswith("        return out") and '"event": "mirror_policy_skipped"' in EXCERPTS["permitted"][1]
assert EXCERPTS["after_swap"][1].rstrip().endswith("self.stamp(doc.tenant_id, meta.get(\"name\"), doc.doc_key, held)")
assert EXCERPTS["guard"][1].rstrip().endswith('_mirror.after_swap(doc, text, gone, {"generation": str(msg.generation), "name": msg.name})')
assert "shared.tenancy backend acme rag_engine" in EXCERPTS["stores"][1] and "shared.tenancy backend zeta vertex_search" in EXCERPTS["stores"][1]
assert EXCERPTS["status"][1].rstrip().endswith('current[t].add(row["doc_key"])') and 'row.get("status") == "indexed"' in EXCERPTS["status"][1]
assert EXCERPTS["fallback"][1].rstrip().endswith("    return backend, 0") and 'policy_of(ts) != "any"' in EXCERPTS["fallback"][1]
assert EXCERPTS["mapping"][1].rstrip().endswith('"found_by": "rag_engine"}')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MANAGED, TENANCY, MAIN, RET, WORKER, "Makefile", "terraform/managed.tf",
                                                          "services/ingest/reconcile.py", "shared/documind_schemas.py", "commands/lane.py",
                                                          "evals/upload.sh", "README.md", "services/rag-api/config.py")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert 'policies = [("acme", "any"), ("zeta", "any"), ("globex", "in")]' in src["commands/lane.py"]
assert "$(MAKE) drift secrets build deploy-services wait-index roster managed-stores bq-views vector-status" in MK   # make up
assert re.search(r"^MANAGED_MIRROR  \?= both$", src["Makefile"], re.M) and re.search(r"^MANAGED_TENANTS \?= acme zeta$", src["Makefile"], re.M)
assert "MANAGED_MIRROR=$(MANAGED_MIRROR) RAG_LOCATION=$(RAG_LOCATION)" in MK and "RETRIEVAL_BACKEND=vector; \\" in MK   # the worker mirrors; the API's default
assert 'default     = ["acme", "zeta"]' in src["terraform/managed.tf"] and 'location                     = "global"' in src["terraform/managed.tf"]
assert "CHUNK_SIZE, CHUNK_OVERLAP = 512, 100" in src[MANAGED] and 'rag_distance_threshold: float = Field(0.5, alias="RAG_DISTANCE_THRESHOLD")' in src["services/rag-api/config.py"]
assert 'MEDIA_TYPES = {"image/png": "figure", "image/jpeg": "figure",' in src[WORKER] and "text = None                                          # a media document has none" in src[WORKER]
# 1. managed-status holds the stores against every indexed version, media included, which the mirror never copies
STATUS = src[MANAGED].split("def status(", 1)[1].split("def main(", 1)[0]
assert "kind" not in STATUS and "policy" not in STATUS                                   # no media filter; no policy read
# 2. a policy turned to `in` deletes nothing: set_policy writes one field, and only a retirement takes a copy out
SET_POLICY = src[TENANCY].split("def set_policy(", 1)[1].split('if __name__ == "__main__":', 1)[0]
assert "delete" not in SET_POLICY.lower() and "mirror" not in SET_POLICY.lower()
assert "A delete is never refused: it is the direction the policy wants." in src[MANAGED]
# 3. nothing repairs a missing copy: the walk only removes, despite what managed.py and the Makefile say
REC = src["services/ingest/reconcile.py"]
assert re.findall(r"mirror\.(\w+)\(", REC) == ["retired", "retired"], re.findall(r"mirror\.(\w+)\(", REC)
assert "the walk repairs the mirror (P9.3)" in src[MANAGED] and "waits for the walk's repair" in src["Makefile"]
UPSERT_CALLERS = sorted({p.relative_to(KIT).as_posix() for p in (KIT / "services").rglob("*.py") if re.search(r"_mirror\.after_(swap|undo)\(|mirror\.upsert\(", p.read_text(encoding="utf-8"))})
assert UPSERT_CALLERS == ["services/ingest/main.py"], UPSERT_CALLERS                       # the worker's swap and undo, and nothing else
# 4. a Vertex AI Search copy is recorded as held when its import is only requested
VS_UPSERT = src[MANAGED].split("class VertexSearchStore:", 1)[1].split("    def delete(", 1)[0]
assert 'or "import requested"   # an LRO: minutes; the walk verifies' in VS_UPSERT and ".result(" not in VS_UPSERT
# 5. found_by never reaches the answer: a citation has no such field, and the kit's own media rows in a managed pool carry none
CITATION = src["shared/documind_schemas.py"].split("class Citation(BaseModel):", 1)[1].split("\nclass ", 1)[0]
MEDIA_ROWS = src[RET].split("def _media_rows(", 1)[1].split("def _managed_retrieve(", 1)[0]
assert "found_by" not in CITATION and "found_by" not in MEDIA_ROWS
# make down cannot finish while the data stores exist: Terraform rejects a plan that destroys a prevent_destroy resource
assert "lifecycle {\n    prevent_destroy = true\n  }" in src["terraform/managed.tf"]
DOWN = MK[MK.index("\ndown: guard-project"):MK.index("# ---------- Teardown")]
assert "terraform destroy -input=false -auto-approve $(TF_VARS)" in DOWN and "-target" not in DOWN and "state rm" not in DOWN and "data store" not in DOWN.lower()
assert "-var managed_search=$(MANAGED_SEARCH)" in MK and re.search(r"^MANAGED_SEARCH  \?= true$", src["Makefile"], re.M)
assert "protected managed search stores (`prevent_destroy = true`)" in src["README.md"]
TENANT_SETTINGS = src[MAIN].split("def tenant_settings(", 1)[1].split("def choose_for(", 1)[0]
assert "except Exception:  # noqa: BLE001 - the pin is a convenience; the setting is the default\n        doc = {}" in TENANT_SETTINGS
STATUS_RECIPE = MK[MK.index("managed-status: guard-project\n"):].split("\n\n", 1)[0]


def recipe_echo(recipe: str, subs: dict) -> str:
    """What make prints before it runs a recipe: its lines, variables expanded (the $(if ...) empty), trailing blanks gone."""
    body = recipe.split("\n", 1)[1]
    body = re.sub(r"\$\(if \$\(filter off,\$\(MANAGED_MIRROR\)\),both,\$\(MANAGED_MIRROR\)\)", "both", body)
    body = re.sub(r"\$\(if \$\(TENANT_ONLY\),--tenant \$\(TENANT_ONLY\),\)", "", body)
    for k, v in subs.items():
        body = body.replace(k, v)
    return "\n".join(line.replace("\t", "", 1).rstrip() for line in body.splitlines()) + "\n"


STATUS_ECHO = recipe_echo(STATUS_RECIPE, {"$(PROJECT)": PROJ, "$(RAG_LOCATION)": "us-central1", "$(PY)": "python"})
assert STATUS_ECHO.endswith("python managed.py --project documind-ai-YOUR-ID --status --mode both\n"), STATUS_ECHO

# ---- the stand-in lane, a module every process below imports as lane153
LANE_LIB = r'''"""The stand-in lane for lesson 7.3's build. The kit's tenancy CLI, managed.py, rag-api and retriever run unchanged on
top of it. Firestore is held in a JSON file: the three tenants' chunk rows and ledger (the corpus evals/upload.sh sends,
each version's doc_key its file's own hash), the tenants' settings, and whatever the kit writes. RAG Engine is a corpus
per `any` tenant (acme, zeta: make up's managed-stores), a file per current text version, cut 512 tokens with 100
overlapping (words stand in for tokens) and ranked by word overlap, a distance for each context; Vertex AI Search is a
data store per `any` tenant (managed.tf), a document per current text version, answering with the paragraphs that match
as extractive segments. The worker is stood in by the kit's own Mirror, called the way main.py calls it after a swap.
Gemini reads the packed clause. gcloud answers identity tokens and log reads from what the stand-in worker logged."""
import collections
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
import types
from hashlib import sha256
from types import SimpleNamespace

KIT = os.environ["LANE153_KIT"]
PROJ = os.environ["GOOGLE_CLOUD_PROJECT"]
with open(os.environ["LANE153_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)                          # {"versions": {tenant: {doc_key: {...}}}, "captions": {...}}
STORE_PATH, LOG_PATH = os.environ["LANE153_STORE"], os.environ["LANE153_LOG"]
CALLS = collections.Counter()
LAST = {"q": ""}
OFF = {"corpus": set(), "datastore": set()}         # stores switched off, for the panel's check
_CACHE = {}


def _load(path: str) -> dict:
    try:
        st = os.stat(path)
    except FileNotFoundError:
        return {}
    key = (path, st.st_mtime_ns, st.st_size)
    if key not in _CACHE:
        with open(path, encoding="utf-8") as f:
            _CACHE.clear()
            _CACHE[key] = json.load(f)
    return _CACHE[key]


def _save(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str)
    _CACHE.clear()


# ---- word overlap, TF-IDF weighted: the dense path, the Ranking API, and both stores' ranking
STOP = set("a an the of for to in on at by is are be what which who how when does do i my can during with and or from as per this that it its long much".split())


def _toks(text: str, pairs: bool = False) -> list:
    w = [x for x in re.findall(r"[a-z0-9]+", text.lower()) if x not in STOP]
    return w + ([a + "_" + b for a, b in zip(w, w[1:])] if pairs else [])


class Tfidf:
    def __init__(self, texts, pairs=False):
        self.pairs, self.n = pairs, len(texts)
        self.df = collections.Counter(t for text in texts for t in set(_toks(text, pairs)))
        self.memo = {}

    def vec(self, text: str) -> dict:
        if text not in self.memo:
            c = collections.Counter(_toks(text, self.pairs))
            v = {t: (1 + math.log(k)) * (math.log((self.n + 1) / (self.df.get(t, 0) + 1)) + 1) for t, k in c.items()}
            s = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.memo[text] = {t: x / s for t, x in v.items()}
        return self.memo[text]

    def sim(self, a: str, b: str) -> float:
        va, vb = self.vec(a), self.vec(b)
        return round(sum(x * vb.get(t, 0.0) for t, x in va.items()), 6)


_ROWS = None


def chunk_rows() -> dict:
    global _ROWS
    if _ROWS is None:
        _ROWS = {}
        for tenant, versions in CORPUS["versions"].items():
            for dk, v in versions.items():
                for i, row in enumerate(v["rows"]):
                    _ROWS[f"{tenant}:{dk.split('_', 1)[1]}#{i}"] = row
    return _ROWS


_DENSE = {}


def dense() -> Tfidf:
    if "t" not in _DENSE:
        _DENSE["t"] = Tfidf(sorted({r["text"] for r in chunk_rows().values()}))
    return _DENSE["t"]


def sim(a: str, b: str, pairs: bool = False) -> float:
    return dense().sim(a, b)


# ---- Firestore
def rows(coll: str) -> dict:
    base = chunk_rows() if coll == "chunks" else {}
    extra = _load(STORE_PATH).get(coll, {})
    if coll == "chunks":
        return {**base, **extra}
    return extra


class Snap:
    def __init__(self, coll, id_, data):
        self.id, self._d, self.exists, self.reference = id_, data, data is not None, Doc(coll, id_)

    def to_dict(self):
        return None if self._d is None else json.loads(json.dumps(self._d, default=str))

    def get(self, field):
        return (self._d or {}).get(field)


class Doc:
    def __init__(self, coll: str, id_: str):
        self.coll, self.id = coll, id_

    def get(self):
        return Snap(self.coll, self.id, rows(self.coll).get(self.id))

    def set(self, data, merge=False):
        """A write, with firestore.Increment applied the way Firestore applies it, and DELETE_FIELD removing its field."""
        store = json.loads(json.dumps(_load(STORE_PATH)))
        c = store.setdefault(self.coll, {})
        old = c.get(self.id, {}) if merge else {}
        new = dict(old)
        for k, v in data.items():
            name = type(v).__name__
            if name == "Increment":
                new[k] = (old.get(k) or 0) + v.value
            elif name == "Sentinel" and "delete" in repr(v).lower():
                new.pop(k, None)
            elif name == "Sentinel":
                new[k] = "2026-09-24T07:31:00Z"            # SERVER_TIMESTAMP
            else:
                new[k] = v
        c[self.id] = new
        _save(STORE_PATH, store)


def _holds(id_, d, field, op, value) -> bool:
    x = id_ if field == "__name__" else d.get(field)
    if op == "==":
        return x == value
    if op == "in":
        return x in value
    raise NotImplementedError(op)


class Query:
    def __init__(self, coll: str, preds=(), lim=None):
        self.coll, self.preds, self.lim = coll, tuple(preds), lim

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.coll, self.preds + ((field, op, value),), self.lim)

    def select(self, fields):
        return self

    def limit(self, n):
        return Query(self.coll, self.preds, n)

    def document(self, id_):
        return Doc(self.coll, id_)

    def matched(self) -> list:
        return [(i, d) for i, d in rows(self.coll).items() if all(_holds(i, d, *p) for p in self.preds)]

    def stream(self):
        return [Snap(self.coll, i, d) for i, d in self.matched()[:self.lim]]

    get = stream

    def find_nearest(self, vector_field, query_vector, distance_measure=None, limit=10, distance_result_field=None, **kw):
        return Nearest(self, limit, distance_result_field)


class Nearest:
    def __init__(self, q: Query, limit: int, field):
        self.q, self.limit, self.field = q, limit, field

    def get(self):
        scored = sorted(((sim(LAST["q"], d.get("text") or ""), i, d) for i, d in self.q.matched()), key=lambda x: (-x[0], x[1]))
        out = []
        for s, i, d in scored[:self.limit]:
            d = dict(d)
            if self.field:
                d[self.field] = round(1.0 - s, 6)
            out.append(Snap(self.q.coll, i, d))
        return out


class DBClass:
    def collection(self, name):
        return Query(name)

    def collection_group(self, name):
        return Query(name)

    def batch(self):
        raise NotImplementedError("batch")


DB = DBClass()


# ---- the stores' contents: every current text version of an `any` tenant (the mirror's rule), media never
def versions(tenant: str) -> dict:
    return {dk: v for dk, v in CORPUS["versions"].get(tenant, {}).items() if v["kind"] == "text" and v["text"].strip()}


CORPORA = {"acme": "projects/NUMBER/locations/us-central1/ragCorpora/acme-corpus", "zeta": "projects/NUMBER/locations/us-central1/ragCorpora/zeta-corpus"}
DATA_STORES = ("acme", "zeta")                      # managed.tf's `tenants`
SIZE, STEP = 384, 309                               # 512 tokens with 100 overlapping, in words (a word is about 1.33 tokens)
_WIN, _WT, _WB = {}, {}, {}


def windows(tenant: str) -> list:
    if tenant not in _WIN:
        out = []
        for dk, v in sorted(versions(tenant).items()):
            words = v["text"].split()
            for i in range(0, len(words), STEP):
                out.append((dk, " ".join(words[i:i + SIZE])))
                if i + SIZE >= len(words):
                    break
        _WIN[tenant] = out
        _WT[tenant] = Tfidf([w for _, w in out])
        _WB[tenant] = Tfidf([w for _, w in out], pairs=True)
    return _WIN[tenant]


def distance(tenant: str, query: str, text: str) -> float:
    """The stand-in's cosine distance for a context - the words it shares with the question, and the phrases: the clause
    that answers near 0.3, text on the same subject under RAG_DISTANCE_THRESHOLD (0.5), the rest past it."""
    return round(max(0.05, 0.62 - 1.2 * (_WT[tenant].sim(query, text) + _WB[tenant].sim(query, text))), 4)


class _Rag(types.ModuleType):
    """vertexai.rag, as the kit calls it: list_corpora, list_files, retrieval_query, and the config classes."""

    class _Kw:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    RagResource = RagRetrievalConfig = Filter = TransformationConfig = ChunkingConfig = _Kw
    RagEmbeddingModelConfig = VertexPredictionEndpoint = RagVectorDbConfig = _Kw

    def list_corpora(self):
        return [SimpleNamespace(name=c, display_name=f"documind-{t}") for t, c in CORPORA.items() if t not in OFF["corpus"]]

    def list_files(self, corpus_name):
        tenant = next(t for t, c in CORPORA.items() if c == corpus_name)
        return [SimpleNamespace(name=f"{corpus_name}/ragFiles/{k}", display_name=dk, description=v["source_uri"])
                for k, (dk, v) in enumerate(sorted(versions(tenant).items()))]

    def retrieval_query(self, rag_resources, text, rag_retrieval_config):
        corpus = rag_resources[0].rag_corpus
        tenant = next(t for t, c in CORPORA.items() if c == corpus)
        if tenant in OFF["corpus"]:
            raise RuntimeError(f"404 {corpus} not found")
        CALLS["rag_query"] += 1
        cfg = rag_retrieval_config
        scored = sorted(((distance(tenant, text, w), dk, w) for dk, w in windows(tenant)), key=lambda x: (x[0], x[1], x[2]))
        ctxs = [SimpleNamespace(source_display_name=dk, source_uri=versions(tenant)[dk]["source_uri"], text=w, score=d,
                                chunk=SimpleNamespace(page_span=None))
                for d, dk, w in scored if d < cfg.filter.vector_distance_threshold][:cfg.top_k]
        return SimpleNamespace(contexts=SimpleNamespace(contexts=ctxs))


# ---- Vertex AI Search (discoveryengine_v1), and the Ranking API's names from the same module
class _Kw:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _SearchRequest(_Kw):
    class ContentSearchSpec(_Kw):
        class SnippetSpec(_Kw):
            pass

        class ExtractiveContentSpec(_Kw):
            pass


class _Document(_Kw):
    class Content(_Kw):
        pass

    @staticmethod
    def to_dict(doc):
        return {"struct_data": dict(getattr(doc, "struct_data", None) or {}),
                "derived_struct_data": dict(getattr(doc, "derived_struct_data", None) or {})}


class _Import(_Kw):
    class InlineSource(_Kw):
        pass

    class ReconciliationMode:
        INCREMENTAL = 1


_DT = {}


def _store_of(path: str) -> str:
    return path.split("/dataStores/", 1)[1].split("/", 1)[0].removeprefix("documind-")


def _exists(tenant: str) -> bool:
    return tenant in DATA_STORES and tenant not in OFF["datastore"]


def _not_found(what: str):
    from google.api_core.exceptions import NotFound
    return NotFound(what)


def _segments(tenant: str, query: str, v: dict, k: int) -> list:
    """The paragraphs of a version that match, best first; a PDF's text keeps its pages (a form feed between them)."""
    out, page = [], 1
    for block_ in re.split(r"\n\s*\n", v["text"]):
        para = " ".join(block_.replace("\f", " ").split())
        if para:
            out.append((para, page))
        page += block_.count("\f")
    t = _DT[tenant]
    scored = sorted(((t.sim(query, p), -i, p, pg) for i, (p, pg) in enumerate(out)), reverse=True)
    segs = []
    for s, _, p, pg in scored[:k]:
        if s <= 0:
            break
        segs.append({"content": p, **({"pageNumber": str(pg)} if v["pdf"] else {})})
    return segs


class _SearchClient:
    def search(self, request):
        tenant = _store_of(request.serving_config)
        if not _exists(tenant):
            raise _not_found(f"DataStore documind-{tenant} not found")
        CALLS["search"] += 1
        vs = versions(tenant)
        if tenant not in _DT:
            _DT[tenant] = Tfidf([p for v in vs.values() for p in re.split(r"\n\s*\n", v["text"])])
        t = _DT[tenant]
        ranked = sorted(((t.sim(request.query, v["text"]), dk) for dk, v in vs.items()), key=lambda x: (-x[0], x[1]))
        k = request.content_search_spec.extractive_content_spec.max_extractive_segment_count
        out = []
        for s, dk in ranked[:request.page_size]:
            if s < 0.03:
                break
            out.append(SimpleNamespace(document=_Document(id=dk, name=f"{request.serving_config}/documents/{dk}",
                                                          struct_data={"source_uri": vs[dk]["source_uri"]},
                                                          derived_struct_data={"extractive_segments": _segments(tenant, request.query, vs[dk], k)})))
        return out


class _DataStoreClient:
    def get_data_store(self, name):
        if not _exists(_store_of(name)):
            raise _not_found(f"DataStore {name.rsplit('/', 1)[-1]} not found")
        return SimpleNamespace(name=name)


class _DocumentClient:
    def list_documents(self, parent):
        tenant = _store_of(parent)
        return [_Document(id=dk, name=f"{parent}/documents/{dk}", struct_data={"source_uri": v["source_uri"], "doc_key": dk})
                for dk, v in sorted(versions(tenant).items())]

    def import_documents(self, request):
        raise RuntimeError("the stand-in holds its data stores fixed")

    def delete_document(self, name):
        raise RuntimeError("the stand-in holds its data stores fixed")


# ---- Gemini: the reader, and text-embedding-005 for the dense path's query
def _reply(prompt: str):
    question = prompt.rsplit("\n\nQuestion:", 1)[1].strip()
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    draft = {"answer": "The context does not say.", "citations": [], "confidence": "low", "answerable": False}
    for k in range(1, len(parts) - 2, 3):
        n, body = int(parts[k]), " ".join(parts[k + 2].split())
        q = question.lower()
        m = re.search(r"A confirmed employee at grade (\w+) or above serves a notice period of (\d+) days", body)
        if m and "notice period" in q:
            draft = {"answer": f"A confirmed employee at grade {m.group(1)} or above serves a notice period of {m.group(2)} days [{n}].",
                     "citations": [{"source": n, "quote": m.group(0) + "."}], "confidence": "high", "answerable": True}
            break
        m = re.search(r"Either party may terminate for convenience on (\d+) days written notice", body)
        if m and "convenience" in q:
            draft = {"answer": f"Either party may terminate the agreement for convenience on {m.group(1)} days' written notice [{n}].",
                     "citations": [{"source": n, "quote": m.group(0) + "."}], "confidence": "high", "answerable": True}
            break
    usage = SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(draft["answer"]) // 4 + 24,
                            thoughts_token_count=0, cached_content_token_count=0)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=usage,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


class Models:
    def generate_content(self, model, contents, config=None):
        CALLS["answer"] += 1
        return _reply(contents[0] if isinstance(contents, list) else contents)

    def embed_content(self, model, contents, config=None):
        q = contents if isinstance(contents, str) else contents[0]
        LAST["q"] = q                                        # the stand-in's nearest-neighbour search reads the text
        CALLS["embed"] += 1
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.001] * 768)])


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models, self.caches = Models(), None
        self._api_client = SimpleNamespace(location=kw.get("location"))


def _mod(name: str, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


class Anything:
    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, name):
        return lambda *a, **kw: Anything()


def install() -> None:
    """Gemini, Firestore, RAG Engine, Vertex AI Search and Cloud Storage, for every process below."""
    if "vertexai.rag" in sys.modules:
        return
    rag = _Rag("vertexai.rag")
    sys.modules["vertexai.rag"] = rag
    _mod("vertexai", init=lambda **kw: None, rag=rag)
    _mod("google.cloud.discoveryengine_v1", SearchServiceClient=_SearchClient, DataStoreServiceClient=_DataStoreClient,
         DocumentServiceClient=_DocumentClient, SearchRequest=_SearchRequest, Document=_Document, ImportDocumentsRequest=_Import,
         RankServiceClient=Anything, RankingRecord=_Kw, RankRequest=_Kw)
    _mod("google.cloud.storage", Client=Anything)
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB


def stubs() -> None:
    """The modules rag-api imports that this machine does not have; nothing below reaches them."""
    install()
    if "opentelemetry.exporter.cloud_trace" in sys.modules:
        return
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    class CloudTraceSpanExporter(SpanExporter):
        def __init__(self, **kw):
            pass

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def shutdown(self):
            pass

    class FastAPIInstrumentor:
        @staticmethod
        def instrument_app(app, **kw):
            return None

    class GoogleGenAiSdkInstrumentor:
        def instrument(self, **kw):
            return None

    class Namespace:
        def __init__(self, name, allow_tokens=None, deny_tokens=None):
            self.name, self.allow_tokens, self.deny_tokens = name, list(allow_tokens or []), list(deny_tokens or [])

    _mod("opentelemetry.exporter.cloud_trace", CloudTraceSpanExporter=CloudTraceSpanExporter)
    _mod("opentelemetry.instrumentation.fastapi", FastAPIInstrumentor=FastAPIInstrumentor)
    _mod("opentelemetry.instrumentation.google_genai", GoogleGenAiSdkInstrumentor=GoogleGenAiSdkInstrumentor)
    _mod("google.cloud.aiplatform", MatchingEngineIndexEndpoint=Anything, MatchingEngineIndex=Anything, init=lambda **kw: None)
    _mod("google.cloud.aiplatform.matching_engine")
    _mod("google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint", Namespace=Namespace)
    for name in ("bigquery", "spanner", "logging"):
        _mod(f"google.cloud.{name}", Client=Anything)


class Index:
    def find_neighbors(self, deployed_index_id, queries, num_neighbors, filter=None):
        allow = {ns.name: set(ns.allow_tokens) for ns in (filter or [])}
        keep = lambda d: all({"tenant_id": d["tenant_id"], "doc_type": d.get("doc_type"), "kind": d.get("kind"),  # noqa: E731
                              "current": "true"}.get(k) in toks for k, toks in allow.items())
        found = sorted(((sim(LAST["q"], d["text"]), i) for i, d in chunk_rows().items() if keep(d)), key=lambda x: (-x[0], x[1]))
        return [[SimpleNamespace(id=i, distance=s) for s, i in found[:num_neighbors]]] if found else []


class Ranker:
    def ranking_config_path(self, project, location, ranking_config):
        return f"projects/{project}/locations/{location}/rankingConfigs/{ranking_config}"

    def rank(self, request, timeout=None):
        order = sorted(((sim(request.query, r.content), int(r.id)) for r in request.records), key=lambda x: (-x[0], x[1]))
        return SimpleNamespace(records=[SimpleNamespace(id=str(i), score=round(s, 4)) for s, i in order[:request.top_n]])


def rag():
    """rag-api's modules, imported from the kit and wired to the stand-ins above."""
    stubs()
    sys.path[:0] = [KIT, os.path.join(KIT, "services", "rag-api")]
    import main
    import retriever
    import generator
    import cache_manager
    main._fs = retriever._fs = lambda: DB
    retriever._index_endpoint = lambda: Index()
    retriever._ranker = lambda: Ranker()
    main.enforce_membership = lambda email, tenant_id: None     # the roster is lesson 8's; every ask here is a member's

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches
    return main


def serve(port: int, who: dict) -> None:
    main = rag()
    import shared.iap as iap

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity

    class FrontDoor:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and not dict(scope["headers"]).get(b"authorization"):
                await send({"type": "http.response.start", "status": 403, "headers": [(b"content-type", b"text/html")]})
                await send({"type": "http.response.body", "body": b"<html><title>403 Forbidden</title></html>"})
                return
            await self.app(scope, receive, send)
    import uvicorn
    uvicorn.run(FrontDoor(main.app), host="127.0.0.1", port=port, log_level="warning")


# ---- the worker, stood in by the kit's own Mirror after a swap; its lines go where gcloud logging read finds them
def worker_ingest(tenant: str, name: str, text: str, when: str) -> dict:
    import logging
    install()
    sys.path[:0] = [os.path.join(KIT, "services", "ingest"), KIT]
    import managed
    from contracts import effective_from_of
    from idempotency import record_source
    from shared.documind_corpus import chunk_document
    from shared.tenancy import policy_for
    lines = []

    class Keep(logging.Handler):
        def emit(self, r):
            lines.append(json.loads(r.getMessage()))
    log = logging.getLogger("documind.ingest")
    log.addHandler(Keep())
    log.setLevel(logging.INFO)
    sha = sha256(text.encode("utf-8")).hexdigest()
    doc_key, uri = f"{tenant}_{sha}", f"gs://{PROJ}-uploads/{name}"
    chunks = chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown", "slug": name.rsplit("/", 1)[-1].rsplit(".", 1)[0]}, tenant)
    for i, c in enumerate(chunks):
        Doc("chunks", f"{tenant}:{sha}#{i}").set({"tenant_id": tenant, "text": c["text"], "source_uri": uri, "doc_type": "unknown",
                                                  "kind": "text", "doc_key": doc_key, "chunk_hash": c["chunk_hash"],
                                                  "locator": c["locator"], "current": True})
    effective = effective_from_of(name, text)
    record_source(DB, tenant, name, uri, doc_key, "1727163000000001", sha, len(chunks), effective, reused=0, embedded=len(chunks), retired=0,
                  embedding_model="text-embedding-005", embedding_version="1")
    mirror = managed.Mirror.from_env(DB, mode="both", policy_for=lambda t: policy_for(t, DB), audit=lambda *a, **kw: lines.append({"event": "doc.mirror"}))
    doc = SimpleNamespace(tenant_id=tenant, doc_key=doc_key, gcs_uri=uri, doc_type="unknown", effective_from=effective)
    mirror.after_swap(doc, text, {"retired_doc_keys": []}, {"generation": "1727163000000001", "name": name})
    lines.append({"event": "ingest_ok", "tenant": tenant, "lane": "push", "doc_key": doc_key, "chunks": len(chunks), "pages": 1,
                  "kinds": ["text"], "reused": 0, "embedded": len(chunks), "retired": 0, "generation": "1727163000000001",
                  "effective_from": effective, "fingerprint": "f00d"})
    base = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    entries = [{"timestamp": (base + dt.timedelta(seconds=9 + k)).isoformat().replace("+00:00", "Z"),
                "resource": {"type": "cloud_run_revision", "labels": {"service_name": "documind-ingest"}}, "jsonPayload": j}
               for k, j in enumerate(lines)]
    old = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            old = json.load(f)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(old + entries, f)
    return {"doc_key": doc_key, "chunks": len(chunks), "effective_from": effective, "lines": lines}


def _logging_read(cmd: list) -> str:
    """gcloud logging read FILTER --format=json [--limit=N]: the filter's service, tenant, event and time, newest first."""
    flt = cmd[3]
    limit = next((int(a.split("=", 1)[1]) for a in cmd if a.startswith("--limit=")), 1000)
    with open(LOG_PATH, encoding="utf-8") as f:
        entries = json.load(f)
    svc = re.search(r'resource\.labels\.service_name="([\w-]+)"', flt).group(1)
    tenant = re.search(r'jsonPayload\.tenant="(\w+)"', flt).group(1)
    since = re.search(r'timestamp>="([^"]+)"', flt).group(1)
    exact = re.search(r'jsonPayload\.event="(\w+)"', flt)
    has = re.search(r'jsonPayload\.event:"(\w+)"', flt)
    keep = [e for e in entries if e["resource"]["labels"]["service_name"] == svc and e["jsonPayload"].get("tenant") == tenant
            and e["timestamp"] >= since and (not exact or e["jsonPayload"]["event"] == exact.group(1))
            and (not has or has.group(1) in e["jsonPayload"]["event"])]
    return json.dumps(sorted(keep, key=lambda e: e["timestamp"], reverse=True)[:limit])


def fake_cli() -> None:
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd[:3] == ["gcloud", "auth", "print-identity-token"]:
            return subprocess.CompletedProcess(list(cmd), 0, "MEMBER\n", "")
        if isinstance(cmd, (list, tuple)) and cmd[:3] == ["gcloud", "logging", "read"]:
            return subprocess.CompletedProcess(list(cmd), 0, _logging_read(list(cmd)), "")
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gcloud":
            raise SystemExit(f"the stand-in gcloud has no answer for {cmd[:4]}")
        return real_run(cmd, *a, **kw)
    subprocess.run = run
'''

# ---- the corpus as evals/upload.sh sends it: each file's own hash is its doc_key; a PDF's text is its .md mirror's
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
UP = src["evals/upload.sh"]
assert 'if [[ "${f}" == *.md && ( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" ) ]]; then' in UP and '*.segments.json' in UP
CAPTIONS = {"annual_report_2026_fig3.png": "Figure 3 of the ACME annual report 2026: a bar chart of revenue by business segment, FY2025 against FY2026.",
            "inv_2026_0412.png": "A tax invoice, INV-2026-0412, raised on ACME: line items, GST and the payment terms.",
            "payment_of_bonus_act_1965_p30.png": "Page 30 of the Payment of Bonus Act, 1965: a printed page of sections on the allocable surplus."}
FULL_ROWS = {("acme", "hr_policy_2026.md"), ("zeta", "hr_policy_zeta_2026.md")}          # every chunk row; the rest keep one, for the version's row
VERSIONS, LEDGER = {}, {}
for tdir in sorted((KIT / "evals/corpus").iterdir()):
    tenant = tdir.name
    VERSIONS[tenant] = {}
    for f in sorted(tdir.iterdir()):
        if f.suffix == ".md" and (f.with_suffix(".pdf").exists() or f.with_suffix(".mp4").exists()) or f.name.endswith(".segments.json"):
            continue                                                     # upload.sh's own rule: the offline mirrors stay home
        data = f.read_bytes()
        sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/{tenant}/{f.name}"
        dk = f"{tenant}_{sha}"
        if f.suffix == ".png":
            kind, text = "media", ""
            rows_ = [{"tenant_id": tenant, "text": CAPTIONS[f.name], "source_uri": uri, "doc_type": "figure", "kind": "figure",
                      "doc_key": dk, "locator": "", "current": True}]
        else:
            kind = "text"
            md = f.with_suffix(".md")
            if md.exists():
                text = md.read_text(encoding="utf-8")
            else:                                                        # a PDF with no mirror (the POSH Act): its own text, a form feed between pages
                import pypdf
                text = "\f".join(p.extract_text() or "" for p in pypdf.PdfReader(str(f)).pages)
            text = re.sub(r"\A<!--.*?-->\s*", "", text, flags=re.S)       # the mirror's provenance header is not the PDF's text
            cut = chunk_document({"text": text, "source_uri": uri, "doc_type": "unknown", "slug": f.stem}, tenant) if text else []
            keep = cut if (tenant, f.name) in FULL_ROWS or tenant == "globex" else cut[:1]
            rows_ = [{"tenant_id": tenant, "text": c["text"], "source_uri": uri, "doc_type": "unknown", "kind": "text", "doc_key": dk,
                      "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True, **({"section": c["section"]} if c.get("section") else {})}
                     for c in keep] or [{"tenant_id": tenant, "text": "", "source_uri": uri, "doc_type": "unknown", "kind": "text",
                                          "doc_key": dk, "locator": "", "current": True}]
        VERSIONS[tenant][dk] = {"name": f"{tenant}/{f.name}", "source_uri": uri, "kind": kind, "text": text, "pdf": f.suffix == ".pdf", "rows": rows_}
        held = {"rag_engine": "us-central1", "vertex_search": "global"} if kind == "text" and tenant in ("acme", "zeta") else {}
        LEDGER[f"{tenant}~{f.name}"] = {"tenant_id": tenant, "name": f"{tenant}/{f.name}", "gcs_uri": uri, "doc_key": dk, "status": "indexed",
                                        "generation": "1", "sha256": sha, "chunks": len(rows_),
                                        **({"mirrored": held, "data_region": "any" if tenant != "globex" else "in"} if kind == "text" else {})}
COUNTS = {t: (sum(1 for v in vs.values() if v["kind"] == "text"), sum(1 for v in vs.values() if v["kind"] == "media")) for t, vs in VERSIONS.items()}
assert COUNTS == {"acme": (18, 3), "globex": (3, 0), "zeta": (7, 0)}, COUNTS
MEDIA_KEYS = sorted(dk for dk, v in VERSIONS["acme"].items() if v["kind"] == "media")

T = Path(tempfile.mkdtemp(prefix="lesson153-"))
(T / "corpus153.json").write_text(json.dumps({"versions": VERSIONS}), encoding="utf-8")
(T / "lane153.py").write_text(LANE_LIB, encoding="utf-8")
STORE, LOGS = T / "store153.json", T / "logs153.json"
SETTINGS0 = {"acme": {"data_region": "any", "retrieval_backend": "vector"},   # make roster, make up's pins, then the setup's pin window
             "zeta": {"data_region": "any", "retrieval_backend": "vertex_search"}, "globex": {"data_region": "in"}}
STORE.write_text(json.dumps({"tenant_settings": SETTINGS0, "sources": LEDGER}), encoding="utf-8")
LOGS.write_text("[]", encoding="utf-8")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T), "LANE153_KIT": str(KIT), "LANE153_CORPUS": str(T / "corpus153.json"),
       "LANE153_STORE": str(STORE), "LANE153_LOG": str(LOGS), "PYTHONPATH": str(T), "API": API}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "GRAPH_", "SPANNER_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR",
                                           "ROUTING", "SPEND_", "BUDGET_", "EMBEDDING_", "EMBED_", "MANAGED_", "RAG_", "SEARCH_", "AUDIT_"))]:
    ENV.pop(k)
FREEZE = ("import datetime as _d\n_NOW = _d.datetime.fromisoformat('2026-09-24T07:33:00+00:00')\n"
          "class _Frozen(_d.datetime):\n    @classmethod\n    def now(cls, tz=None):\n        return _NOW.astimezone(tz) if tz else _NOW.replace(tzinfo=None)\n"
          "_d.datetime = _Frozen\n")
PRELUDE = FREEZE + "import lane153\nlane153.install()\nlane153.fake_cli()\n"


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T, argv: tuple = ()) -> str:
    r = subprocess.run([sys.executable, "-", *argv], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


def heredoc(body: str, prefix: str = "", args: str = "") -> str:
    return f"{prefix}python - {args}<<'PY'\n{body}\nPY"


# ------------------------------------------------------------------ the cells
RULES_PY = """import json, logging, sys
sys.path[:0] = ["services/ingest", "."]
import managed                                        # the kit's mirror, as the worker holds it; the two stores below are stand-ins
from shared.tenancy import permits, policy_of


class Brief(logging.Handler):                         # the mirror's JSON lines, one short line each
    def emit(self, r):
        j = json.loads(r.getMessage())
        print(f"     {j['event']:22} {j.get('store', ''):13} {j.get('op', ''):17} {j.get('result', j.get('data_region', ''))}")
logging.getLogger("documind.ingest").addHandler(Brief())
logging.getLogger("documind.ingest").setLevel(logging.INFO)


class Store:                                          # what the Mirror needs of a store: a name, a region, upsert, delete
    def __init__(self, name, region):
        self.name, self.region, self.docs = name, region, set()

    def upsert(self, tenant, doc_key, source_uri, text, meta):
        self.docs.add(doc_key)
        return f"{doc_key} uploaded"

    def delete(self, tenant, doc_key):
        gone = doc_key in self.docs
        self.docs.discard(doc_key)
        return int(gone)


print("policy_of:", {str(d.get("data_region")): policy_of(d) for d in ({}, {"data_region": "any"}, {"data_region": "ANY "}, {"data_region": "us"})})
print("permits:", {f"{p} -> {r}": permits(p, r) for p in ("any", "in") for r in ("us-central1", "global", "asia-south1")})
policy, audit = {"acme": "any", "globex": "in"}, []
stores = [Store("rag_engine", "us-central1"), Store("vertex_search", "global")]
m = managed.Mirror(None, stores, "both", policy_for=policy.get,
                   audit=lambda action, actor, target, meta: audit.append(f"{action} {meta['op']} {meta['store']} {target['id']}"))
print("1. acme (any) makes version v1 current:")
print("   held", m.upsert("acme", "acme_v1", "gs://b/acme/hr.md", "Notice period: 60 days."))
print("2. globex (in) adds a note:")
print("   held", m.upsert("globex", "globex_n1", "gs://b/globex/n1.md", "Visitors sign the register."))
print("3. globex adds a second note:")
print("   held", m.upsert("globex", "globex_n2", "gs://b/globex/n2.md", "Badges at all times."))
policy["acme"] = "in"
print("4. acme's policy is turned to in, and version v2 becomes current:")
print("   held", m.upsert("acme", "acme_v2", "gs://b/acme/hr.md", "Notice period: 90 days."))
print("   the stores still hold", {s.name: sorted(s.docs) for s in stores})
print("5. v1 is retired:")
m.retired("acme", ["acme_v1"], "superseded")
print("   the stores hold", {s.name: sorted(s.docs) for s in stores})
print("the audit trail:", *audit, sep="\\n   ")"""

POLICY_CMD = ('for t in acme zeta globex; do\n'
              '  make tenant-policy PROJECT="$PROJECT" TENANT=$t        # where its text may be held\n'
              '  make tenant-backend PROJECT="$PROJECT" TENANT=$t       # which store answers it\n'
              'done\n'
              'make managed-status PROJECT="$PROJECT"                     # every store, held against the ledger')

ASK_PY = """import json, os, re, subprocess, sys, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
Q = {"acme": "How long is the notice period for a confirmed employee?", "zeta": "How long is the notice period for a confirmed employee?",
     "globex": "How much notice does either party give to end the Globex agreement for convenience?"}
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
short = lambda cid: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\\1...", cid)      # the version's sha256, cut to 8
for t in sys.argv[1:]:
    req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q[t], "tenant_id": t}).encode(),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=180))
    s = a["stages"]
    print(f"{t}: retrieval_backend {s['retrieval_backend']}, policy_fallback {s['policy_fallback']}; pool {s['pool']}, {s['managed_chunks']} from a managed store")
    print(f"  A: {a['answer']}")
    for c in a["citations"]:
        print(f"  cites {short(c['chunk_id'])} ({c['source_uri'].rsplit('/', 1)[-1]})")"""
ASK_FN = ("ask153() {   # ask153 TENANT...: each tenant's question as documind-ui-sa - the store that served, the answer, the cited chunk\n"
          + heredoc(ASK_PY, args='"$@" ') + "\n}")

JOIN_PY = """import json, os, re, subprocess, sys, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
os.environ["GOOGLE_CLOUD_PROJECT"] = P                  # the kit's settings, read as the API reads them
sys.path[:0] = [".", "services/rag-api"]
Q = "How long is the notice period for a confirmed employee?"
short = lambda cid: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\\1...", cid)
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(),
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
a = json.load(urllib.request.urlopen(req, timeout=180))
s = a["stages"]
print(f"the API: retrieval_backend {s['retrieval_backend']}, {s['managed_chunks']} of the pool's {s['pool']} chunks from the store")
import retriever                                        # the kit's retrieval stage, run in this shell with your credentials
pool = retriever.retrieve(Q, "acme", 5, backend="rag_engine")
kinds = {}
for c in pool:
    kinds.setdefault(c.get("found_by"), []).append(c)
print(f"the same question through the kit's retrieve(), backend rag_engine: {len(pool)} chunks")
for k, v in kinds.items():
    print(f"  found_by {k or '(none)':13} {len(v):2}   for example {short(v[0]['id'])}")
by_id = {c["id"]: c for c in pool}
for c in a["citations"]:
    hit = by_id.get(c["chunk_id"])
    print(f"the chunk the answer cites: {short(c['chunk_id'])}")
    if hit:
        print(f"  found_by {hit['found_by']}, score {hit['score']:.3f} (1 minus its distance), from {hit['source_uri'].rsplit('/', 1)[-1]}")
    else:
        print("  not in this pool: ask again (the store answers the same text for the same question)")"""

NOTE_CMD = ('cat > "$HOME/globex_visitor_note.md" <<EOF\n'
            "# Globex visitor note\n\n"
            "Visitors to the Globex office sign the register at reception and wear a visitor badge at all times.\n\n"
            "Written by $ME on $(date -u +%Y-%m-%dT%H:%M:%SZ) for lesson 7.3.\n"
            "EOF\n"
            "export SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)\n"
            f'make reindex PROJECT="$PROJECT" TENANT=globex FILE="$HOME/globex_visitor_note.md" NAME={NOTE_NAME}')

LOGS_PY = f"""import datetime as dt, json, os, subprocess, urllib.request
P, API, SINCE = os.environ["PROJECT"], os.environ["API"], os.environ["SINCE"]
NAME = "globex/{NOTE_NAME}"


def logs(extra, limit=20):
    flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
           'AND jsonPayload.tenant="globex" AND ' + extra)
    out = subprocess.run(["gcloud", "logging", "read", flt, "--project", P, "--format=json", f"--limit={{limit}}"],
                         capture_output=True, text=True, check=True).stdout
    return sorted(json.loads(out or "[]"), key=lambda e: e["timestamp"])


def show(e):
    j = e["jsonPayload"]
    print(f"  {{e['timestamp'][11:19]}} {{j['event']:22}} store {{j.get('store', '-'):13}} region {{j.get('region', '-'):11}} data_region {{j.get('data_region', '-')}}")


lines = logs(f'jsonPayload.event:"mirror_" AND timestamp>="{{SINCE}}"')
print(f"the worker's mirror lines for globex since {{SINCE}}:")
for e in lines:
    show(e)
if not any(e["jsonPayload"]["event"] == "mirror_policy_skipped" for e in lines):
    week = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("  none since the upload: this worker instance had said it already (once per tenant and store per instance); the last 7 days:")
    for e in logs(f'jsonPayload.event="mirror_policy_skipped" AND timestamp>="{{week}}"', 4):
        show(e)
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={{API}}",
                      f"--impersonate-service-account=documind-ui-sa@{{P}}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
src = json.load(urllib.request.urlopen(urllib.request.Request(f"{{API}}/v1/sources?tenant_id=globex", headers={{"Authorization": "Bearer " + tok}}), timeout=60))
row = next(r for r in src["sources"] if r["name"] == NAME)
print(f"the ledger row for {{NAME}}: status {{row['status']}}, mirrored {{row['mirrored']}}")
print(f"globex's data_region, as GET /v1/sources reports it: {{src['data_region']}}")"""

GLOBEX_CMD = ('make tenant-backend PROJECT="$PROJECT" TENANT=globex RETRIEVAL_BACKEND=rag_engine\n'
              "sleep 60      # the API reads a tenant's settings once a minute per instance\n"
              "ask153 globex\n"
              'make tenant-backend PROJECT="$PROJECT" TENANT=globex RETRIEVAL_BACKEND=default')

CELLS = {
    "rules": heredoc(RULES_PY),
    "policies": POLICY_CMD,
    "ask": ('make tenant-backend PROJECT="$PROJECT" TENANT=acme RETRIEVAL_BACKEND=rag_engine     # make up\'s pin, back\n'
            "sleep 60      # the API reads a tenant's settings once a minute per instance\n" + ASK_FN + "\nask153 acme zeta globex"),
    "join": heredoc(JOIN_PY),
    "note": NOTE_CMD,
    "logs": heredoc(LOGS_PY),
    "globex": GLOBEX_CMD,
}

# ---- step 3: the rules, run on the kit
OUT = {"rules": run_cell(RULES_PY, cwd=KIT)}
R3 = OUT["rules"]
assert "policy_of: {'None': 'in', 'any': 'any', 'ANY ': 'any', 'us': 'in'}" in R3, R3
assert "'in -> us-central1': False, 'in -> global': False, 'in -> asia-south1': True}" in R3, R3
assert R3.count("mirror_policy_skipped") == 4 and R3.count("mirror_ok") == 4, R3            # globex twice (once each store), acme twice after the turn
assert "   held {'rag_engine': 'us-central1', 'vertex_search': 'global'}\n" in R3 and R3.count("   held {}\n") == 3, R3
assert "   the stores still hold {'rag_engine': ['acme_v1'], 'vertex_search': ['acme_v1']}" in R3, R3
assert "   the stores hold {'rag_engine': [], 'vertex_search': []}" in R3, R3
assert R3.count("doc.mirror upsert") == 2 and R3.count("doc.mirror delete:superseded") == 2, R3

# ---- step 4: the policies, the pins and the stores (the kit's tenancy CLI and managed.py on the stand-in lane)
TENANCY_PY = ("import runpy, sys\nsys.path.insert(0, '.')\nfor argv in %r:\n    sys.argv = ['tenancy'] + argv\n"
              "    runpy.run_module('shared.tenancy', run_name='__main__', alter_sys=True)\n")


def tenancy(*argvs) -> str:
    return run_cell(TENANCY_PY % [list(a) for a in argvs], PRELUDE, cwd=KIT)


pol = tenancy(*[a for t in ("acme", "zeta", "globex") for a in (["policy", t], ["backend", t])])
STATUS_PY = ("import runpy, sys\nsys.path[:0] = ['.', '../..']\nsys.argv = ['managed.py', '--project', %r, '--status', '--mode', 'both']\n"
             "try:\n    runpy.run_path('managed.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n") % PROJ
status = run_cell(STATUS_PY, PRELUDE, cwd=KIT / "services/ingest", env={"RAG_LOCATION": "us-central1", "AUDIT_BUCKET": f"{PROJ}-audit"})
OUT["policies"] = pol + STATUS_ECHO + status
assert pol == ("acme: data_region=any\nacme: retrieval_backend=vector\nzeta: data_region=any\nzeta: retrieval_backend=vertex_search\n"
               "globex: data_region=in\nglobex: retrieval_backend=default (the deployment RETRIEVAL_BACKEND)\n"), pol
ST = [json.loads(line) for line in status.splitlines()]
ST_BY = {(s["tenant"], s["store"]): s for s in ST}
for store in ("rag_engine", "vertex_search"):
    a_ = ST_BY[("acme", store)]
    assert (a_["ledger_current"], a_["held"], a_["missing"], a_["orphans"], a_["status"]) == (21, 18, 3, 0, "drift") and a_["missing_doc_keys"] == MEDIA_KEYS, a_
    z_ = ST_BY[("zeta", store)]
    assert (z_["ledger_current"], z_["held"], z_["status"]) == (7, 7, "in sync"), z_
    assert ST_BY[("globex", store)]["status"] == "no store", ST_BY[("globex", store)]
assert [(s["tenant"], s["store"]) for s in ST] == [(t, s) for t in ("acme", "globex", "zeta") for s in ("rag_engine", "vertex_search")]

# ---- step 5: acme back on RAG Engine; the three tenants asked; the cited chunk found in the kit's own retrieve()
with socket.socket() as s_:
    assert s_.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
URL = f"http://127.0.0.1:{PORT}"
SERVE = f"import lane153; lane153.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"
LIVE_ENV = {"RETRIEVAL_BACKEND": "vector", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT", "EMBEDDING_MODEL": "text-embedding-005",
            "EMBEDDING_VERSION": "1", "RAG_LOCATION": "us-central1"}


def api(body: str, argv: tuple = (), prelude: str = PRELUDE) -> tuple:
    """The kit's app on localhost for one cell (a fresh process: the tenant settings are read afresh), then its usage rows."""
    log = T / f"api153-{len(list(T.glob('api153-*')))}.log"
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
        out = run_cell(body, prelude, env={"API": URL, "SINCE": "2026-09-24T07:30:00Z", **LIVE_ENV}, cwd=KIT, argv=argv)
    finally:
        srv.terminate()
        srv.wait(timeout=20)
    rows_ = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.startswith('{"event": "query"')]
    return out, rows_


pin = tenancy(["backend", "acme", "rag_engine"])
assert pin == "acme: retrieval_backend=rag_engine\n", pin
asked, ROWS5 = api(ASK_PY, argv=("acme", "zeta", "globex"))
OUT["ask"] = pin + asked
A5 = asked
assert [r["retrieval_backend"] for r in ROWS5] == ["rag_engine", "vertex_search", "vector"] and [r["policy_fallback"] for r in ROWS5] == [0, 0, 0], ROWS5
assert re.search(r"  A: A confirmed employee at grade E3 or above serves a notice period of 60 days \[\d+\]\.\n", A5), A5
assert re.search(r"  A: A confirmed employee at grade L4 or above serves a notice period of 30 days \[\d+\]\.\n", A5), A5
assert re.search(r"  A: Either party may terminate the agreement for convenience on 120 days' written notice \[\d+\]\.\n", A5), A5
CITE = re.findall(r"  cites (\S+) \((\S+)\)", A5)
assert CITE[0][0].startswith("acme:acme_") and "#rag-" in CITE[0][0] and "#vs-" in CITE[1][0] and re.fullmatch(r"globex:[0-9a-f]{8}\.\.\.#\d+", CITE[2][0]), CITE
assert [c[1] for c in CITE] == ["hr_policy_2026.md", "hr_policy_zeta_2026.md", "msa_globex_2026.md"], CITE
P5 = [re.search(r"pool (\d+), (\d+) from a managed store", line).groups() for line in A5.splitlines() if "retrieval_backend" in line]
POOL_ACME, MANAGED_ACME = map(int, P5[0])
assert MANAGED_ACME >= 3 and POOL_ACME > MANAGED_ACME and int(P5[1][1]) == int(P5[1][0]) and P5[2][1] == "0", P5   # acme's pool mixes the store's text and the kit's figures
joined, _ = api(JOIN_PY, prelude=PRELUDE + "lane153.stubs()\n")
OUT["join"] = joined
J = joined
assert f"the API: retrieval_backend rag_engine, {MANAGED_ACME} of the pool's {POOL_ACME} chunks from the store\n" in J, J
assert re.search(r"  found_by rag_engine +%d +for example acme:acme_" % MANAGED_ACME, J) and re.search(r"  found_by \(none\) +%d " % (POOL_ACME - MANAGED_ACME), J), J
assert f"the chunk the answer cites: {CITE[0][0]}\n  found_by rag_engine, score " in J and "from hr_policy_2026.md" in J, J

# ---- step 6: a note to globex (in): the kit's Mirror as the worker calls it; the lines, the ledger row; a pin the policy overrides
NOTE = ("# Globex visitor note\n\nVisitors to the Globex office sign the register at reception and wear a visitor badge at all times.\n\n"
        "Written by you@example.com on 2026-09-24T07:29:58Z for lesson 7.3.\n")
ingest = json.loads(run_cell("import json, lane153\nprint(json.dumps(lane153.worker_ingest('globex', %r, %r, '2026-09-24T07:30:00Z')))\n"
                             % (f"globex/{NOTE_NAME}", NOTE), PRELUDE))
EV = [line["event"] for line in ingest["lines"]]
assert EV == ["mirror_policy_skipped", "mirror_policy_skipped", "ingest_ok"], EV            # both stores skipped; no copy, no audit event
NOTE_KEY = ingest["doc_key"]
OUT["note"] = ("...\n"
               f">> gs://{PROJ}-uploads/globex/{NOTE_NAME} - waiting for the worker (up to 5 min)\n"
               ">> event doc_key chunks reused embedded retired effective_from\n"
               f">> ingest_ok\t{NOTE_KEY}\t{ingest['chunks']}\t0\t{ingest['chunks']}\t0\t\n"
               f">> the gate, scoped to this document, on a candidate: make eval-live PROJECT={PROJ} SOURCE={NOTE_NAME} API=<candidate url>\n")
REINDEX = (KIT / "commands/reindex.sh").read_text(encoding="utf-8")
for piece in ('echo ">> gs://$PROJECT-uploads/$TENANT/$OBJ - waiting for the worker (up to 5 min)"', 'echo ">> event doc_key chunks reused embedded retired effective_from"',
              "--format='value(jsonPayload.event,jsonPayload.doc_key,jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded,jsonPayload.retired,jsonPayload.effective_from)'",
              'echo ">> the gate, scoped to this document, on a candidate: make eval-live PROJECT=$PROJECT SOURCE=$OBJ API=<candidate url>"'):
    assert piece in REINDEX, piece
assert ingest["effective_from"] is None
logs_out, _ = api(LOGS_PY)
OUT["logs"] = logs_out
assert "  07:30:09 mirror_policy_skipped  store rag_engine    region us-central1 data_region in\n" in logs_out, logs_out
assert "  07:30:10 mirror_policy_skipped  store vertex_search region global      data_region in\n" in logs_out, logs_out
assert f"the ledger row for globex/{NOTE_NAME}: status indexed, mirrored {{}}\n" in logs_out and "as GET /v1/sources reports it: in\n" in logs_out, logs_out
g_pin = tenancy(["backend", "globex", "rag_engine"])
g_ask, ROWS6 = api(ASK_PY, argv=("globex",))
g_unpin = tenancy(["backend", "globex", "default"])
OUT["globex"] = g_pin + g_ask + g_unpin
assert g_pin == "globex: retrieval_backend=rag_engine\n" and g_unpin == "globex: retrieval_backend=default\n", (g_pin, g_unpin)
assert g_ask.startswith("globex: retrieval_backend vector, policy_fallback 1; pool "), g_ask
assert [(r["retrieval_backend"], r["policy_fallback"], r["managed_chunks"]) for r in ROWS6] == [("vector", 1, 0)], ROWS6
COST_RS = max(r["cost_usd"] for r in ROWS5 + ROWS6) * 85

# ------------------------------------------------------------------ the panel: the kit's rules on every combination of the settings
POLICIES, MODES, KINDS = ["any", "in", "absent", "unreadable"], ["off", "rag_engine", "vertex_search", "both"], ["text", "new", "media"]
PINS, RMODES = ["default", "vector", "firestore", "rag_engine", "vertex_search"], ["dense", "hybrid"]
CHECK_PY = """import json, logging, sys
from types import SimpleNamespace
import lane153
lane153.stubs()
main = lane153.rag()
import retriever
sys.path[:0] = [lane153.KIT + "/services/ingest"]
import managed
from shared.tenancy import policy_for, policy_of
POLICIES, MODES, KINDS, PINS, RMODES = %r, %r, %r, %r, %r
seen = []


class Keep(logging.Handler):
    def emit(self, r):
        try:
            seen.append(json.loads(r.getMessage()))
        except ValueError:
            pass
logging.getLogger().addHandler(Keep())                  # the root: the worker's and the API's lines both propagate here, once
logging.getLogger().setLevel(logging.INFO)


class Store:
    def __init__(self, name, region, exists):
        self.name, self.region, self.exists = name, region, exists

    def upsert(self, tenant, doc_key, source_uri, text, meta):
        if not self.exists:
            raise managed.NoStore("none")
        return "uploaded"

    def delete(self, tenant, doc_key):
        if not self.exists:
            raise managed.NoStore("none")
        return 0


class PolicyDB:                                         # tenant_settings/{tenant} as the worker's policy_for reads it
    def __init__(self, kind):
        self.kind = kind

    def collection(self, name):
        return self

    def document(self, id_):
        return self

    def get(self):
        if self.kind == "unreadable":
            raise RuntimeError("permission denied")
        doc = {} if self.kind == "absent" else {"data_region": self.kind}
        return SimpleNamespace(exists=True, to_dict=lambda: doc)


class StampDB:                                          # the ledger row stamp() writes
    def __init__(self):
        self.row = None

    def collection(self, name):
        return self

    def document(self, id_):
        return self

    def set(self, data, merge=False):
        self.row = data


write = []
for p in POLICIES:
    for mode in MODES:
        for corpus in (True, False):
            for ds in (True, False):
                for kind in KINDS:
                    stores = []
                    if mode in ("rag_engine", "both"):
                        stores.append(Store("rag_engine", "us-central1", corpus))
                    if mode in ("vertex_search", "both"):
                        stores.append(Store("vertex_search", "global", ds))
                    db, audits = StampDB(), []
                    m = managed.Mirror(db, stores, mode, policy_for=lambda t, p=p: policy_for(t, PolicyDB(p)), audit=lambda *a, **kw: audits.append(1))
                    del seen[:]
                    text = None if kind == "media" else "Visitors sign the register."
                    if m.active and text is not None:        # main.py's guard, as the worker holds it
                        m.after_swap(SimpleNamespace(tenant_id="t", doc_key="t_new", gcs_uri="gs://b/t/x.md", doc_type="unknown", effective_from=None),
                                     text, {"retired_doc_keys": ["t_old"] if kind == "text" else []}, {"name": "t/x.md"})
                    lines = [[j["store"], j["op"], j["event"]] for j in seen if j.get("event", "").startswith("mirror_")]
                    write.append([p, mode, corpus, ds, kind, lines, None if db.row is None else db.row["mirrored"],
                                  None if db.row is None else db.row["data_region"], len(audits)])
read = []
Q = "How long is the notice period for a confirmed employee?"
for p in POLICIES:
    for pin in PINS:
        for rmode in RMODES:
            for corpus in (True, False):
                for ds in (True, False):
                    doc = {} if p == "unreadable" else {**({} if p == "absent" else {"data_region": p}), **({} if pin == "default" else {"retrieval_backend": pin})}
                    main.tenant_settings = lambda t, doc=doc: doc
                    main.settings.retrieval_mode = rmode
                    del seen[:]
                    _, _, chosen = main.choose_for(SimpleNamespace(tenant_id="acme", query=Q))
                    served, fb = main.retrieval_backend_for("acme", chosen)
                    ignored = any(j.get("event") == "retrieval_pin_ignored" for j in seen)
                    found = None
                    if rmode == "dense":
                        lane153.OFF["corpus"] = set() if corpus else {"acme"}
                        lane153.OFF["datastore"] = set() if ds else {"acme"}
                        retriever._corpora.clear()
                        pool = retriever._dense_retrieve(Q, "acme", 5, backend=served)
                        found = sorted({c.get("found_by") for c in pool} - {None})        # the kit's own media rows join when there is room
                    read.append([p, pin, rmode, corpus, ds, served, fb, ignored, found])
print("RESULT " + json.dumps({"write": write, "read": read}))""" % (POLICIES, MODES, KINDS, PINS, RMODES)
PY_SIDE = json.loads(run_cell(CHECK_PY, FREEZE, env=LIVE_ENV).rsplit("RESULT ", 1)[1])
assert len(PY_SIDE["write"]) == 192 and len(PY_SIDE["read"]) == 160
W_EVENTS = {tuple(map(tuple, r[5])) for r in PY_SIDE["write"]}
R_OUT = {(r[5], r[6], r[7], tuple(r[8] or ())) for r in PY_SIDE["read"]}
assert len(W_EVENTS) >= 10 and len(R_OUT) >= 8, (len(W_EVENTS), len(R_OUT))
shutil.rmtree(T, ignore_errors=True)

UI_JS = r"""var root = document.getElementById('mm'); if (!root) return;
  var MODES = {off: [], rag_engine: ['rag_engine'], vertex_search: ['vertex_search'], both: ['rag_engine', 'vertex_search']};
  var REGION = {rag_engine: 'us-central1', vertex_search: 'global'}, RB = ['vector', 'firestore', 'rag_engine', 'vertex_search'];
  var MB = ['rag_engine', 'vertex_search'], DEPLOY = 'vector';
  function policyOf(p){ return p === 'any' ? 'any' : 'in'; }
  function permits(policy, region){ return policy === 'any' || region.indexOf('asia-south') === 0; }
  function writeSide(p, mode, corpus, ds, kind){ var stores = MODES[mode], exists = {rag_engine: corpus, vertex_search: ds};
    var out = {lines: [], mirrored: null, region: null, audits: 0}; if (!stores.length || kind === 'media') { return out; }
    var policy = policyOf(p), said = {}, held = {};
    stores.forEach(function(s){ if (!permits(policy, REGION[s])) { out.lines.push([s, 'upsert', 'mirror_policy_skipped']); return; }
      if (!exists[s]) { out.lines.push([s, 'upsert', 'mirror_no_store']); said[s] = 1; return; }
      out.lines.push([s, 'upsert', 'mirror_ok']); out.audits++; held[s] = REGION[s]; });
    if (kind === 'text') { stores.forEach(function(s){ if (!exists[s]) { if (!said[s]) { out.lines.push([s, 'delete:superseded', 'mirror_no_store']); said[s] = 1; } return; }
      out.lines.push([s, 'delete:superseded', 'mirror_ok']); out.audits++; }); }
    out.mirrored = held; out.region = policy; return out; }
  function readSide(p, pin, rmode, corpus, ds){ var hasPin = p !== 'unreadable' && pin !== 'default', policy = p === 'unreadable' ? 'in' : policyOf(p);
    var chosen = DEPLOY, ignored = false;
    if (hasPin && pin !== chosen) { if (RB.indexOf(pin) >= 0 && !(MB.indexOf(pin) >= 0 && rmode === 'hybrid')) { chosen = pin; } else { ignored = true; } }
    var served = chosen, fb = 0;
    if (MB.indexOf(chosen) >= 0 && policy !== 'any') { served = MB.indexOf(DEPLOY) < 0 ? DEPLOY : 'firestore'; fb = 1; }
    var found = null;
    if (rmode === 'dense') { found = served === 'rag_engine' ? (corpus ? ['rag_engine'] : ['firestore']) : served === 'vertex_search' ? (ds ? ['vertex_search'] : ['firestore']) : [served]; }
    return {served: served, fb: fb, ignored: ignored, found: found}; }
  window.__mm = {writeSide: writeSide, readSide: readSide};
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  var $ = function(id){ return document.getElementById(id); };
  function row(out, k, v, cls){ out.appendChild(el('b', '', k)); out.appendChild(el('span', cls || '', v)); }
  var SAY = {mirror_ok: 'mirror_ok', mirror_policy_skipped: 'mirror_policy_skipped: the policy keeps the text home', mirror_no_store: 'mirror_no_store: no store for the tenant (said once)'};
  var FOUND = {rag_engine: 'found_by rag_engine: RAG Engine\'s text, ids ending #rag-', vertex_search: 'found_by vertex_search: the data store\'s segments, ids ending #vs-',
    media: 'the kit\'s own figure and segment rows, when the tenant has any and the pool has room: no found_by at all',vector: 'found_by vector: the kit\'s Vector Search index, ids tenant:sha256#n',
    firestore: 'found_by firestore: the kit\'s rows in Firestore'};
  var PRESETS = {acme: ['any', 'both', true, true, 'rag_engine', 'text'], zeta: ['any', 'both', true, true, 'vertex_search', 'text'], globex: ['in', 'both', false, false, 'default', 'new']};
  function render(){ var p = $('mm-policy').value, mode = $('mm-mode').value, kind = $('mm-kind').value, pin = $('mm-pin').value, rmode = $('mm-rmode').value;
    var corpus = $('mm-corpus').checked, ds = $('mm-ds').checked, w = writeSide(p, mode, corpus, ds, kind), r = readSide(p, pin, rmode, corpus, ds);
    var up = $('mm-up'), ask = $('mm-ask'); up.textContent = ''; ask.textContent = '';
    if (!MODES[mode].length) { row(up, 'The mirror', 'not called: MANAGED_MIRROR is off, so the worker has no store to copy to', 'stop'); }
    else if (kind === 'media') { row(up, 'The mirror', 'not called: a picture or a video has no text, and stays on the kit\'s own index', 'stop'); }
    else { w.lines.forEach(function(l){ row(up, l[0], (l[1] === 'upsert' ? 'the new version: ' : 'the version it replaced: ') + SAY[l[2]],
        l[2] === 'mirror_ok' ? 'pass' : l[2] === 'mirror_policy_skipped' ? 'stop' : ''); }); }
    var held = w.mirrored ? Object.keys(w.mirrored) : null;
    row(up, 'Ledger row', held === null ? 'no mirrored field: the mirror was not called' : held.length ? 'mirrored {' + held.map(function(s){ return s + ': ' + w.mirrored[s]; }).join(', ') + '}, data_region ' + w.region : 'mirrored {}: the kit\'s rows only, data_region ' + w.region);
    row(up, 'Audit', w.audits + ' doc.mirror event' + (w.audits === 1 ? '' : 's'));
    row(ask, 'The pin', p === 'unreadable' ? 'unread: the settings could not be read, so no pin and the strict policy' : pin === 'default' ? 'none: the deployment\'s ' + DEPLOY : r.ignored ? pin + ' ignored: a managed store cannot fuse hybrid (retrieval_pin_ignored)' : pin, r.ignored ? 'stop' : '');
    row(ask, 'The policy', r.fb ? policyOf(p === 'unreadable' ? 'in' : p) + ': a store may not serve this tenant, so the kit\'s own index does (policy_fallback 1)' : 'no fallback needed (policy_fallback 0)', r.fb ? 'stop' : '');
    row(ask, 'Served by', r.served, 'pass');
    if (r.found) { row(ask, 'The pool', FOUND[r.found[0]]); if (MB.indexOf(r.found[0]) >= 0) { row(ask, 'And', FOUND.media); } if (r.found[0] === 'firestore' && MB.indexOf(r.served) >= 0) { row(ask, 'Why', (r.served === 'rag_engine' ? 'rag_engine_fallback' : 'vertex_search_fallback') + ': no store for the tenant, so the Firestore rung answers', 'stop'); } }
    else { row(ask, 'The pool', 'found_by vector: dense and sparse fused over the kit\'s index'); }
    row(ask, 'On the row', 'retrieval_backend ' + r.served + ', policy_fallback ' + r.fb + ', managed_chunks ' + (r.found && r.found.indexOf(r.served) >= 0 && MB.indexOf(r.served) >= 0 ? 'more than 0' : '0')); }
  function preset(){ var v = PRESETS[$('mm-tenant').value]; $('mm-policy').value = v[0]; $('mm-mode').value = v[1]; $('mm-corpus').checked = v[2]; $('mm-ds').checked = v[3]; $('mm-pin').value = v[4]; $('mm-kind').value = v[5]; $('mm-rmode').value = 'dense'; render(); }
  ['mm-policy', 'mm-mode', 'mm-kind', 'mm-pin', 'mm-rmode', 'mm-corpus', 'mm-ds'].forEach(function(id){ $(id).addEventListener('change', render); });
  $('mm-tenant').addEventListener('change', preset); preset();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# the port against the kit, on every combination
PORT_JS = UI_JS.split("function el(")[0].replace("var root = document.getElementById('mm'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var G = window.__mm, T = " + json.dumps({"write": [r[:5] for r in PY_SIDE["write"]], "read": [r[:5] for r in PY_SIDE["read"]]}) + ";\n"
        "var write = T.write.map(function(t){ var w = G.writeSide(t[0], t[1], t[2], t[3], t[4]); return t.concat([w.lines, w.mirrored, w.region, w.audits]); });\n"
        "var read = T.read.map(function(t){ var r = G.readSide(t[0], t[1], t[2], t[3], t[4]); return t.concat([r.served, r.fb, r.ignored, r.found]); });\n"
        "process.stdout.write(JSON.stringify({write: write, read: read}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
assert JS_SIDE["write"] == PY_SIDE["write"], next(((a, b) for a, b in zip(JS_SIDE["write"], PY_SIDE["write"]) if a != b), None)
assert JS_SIDE["read"] == PY_SIDE["read"], next(((a, b) for a, b in zip(JS_SIDE["read"], PY_SIDE["read"]) if a != b), None)
N_CHECKED = len(PY_SIDE["write"]) + len(PY_SIDE["read"])


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the mirror's rules, run; no store, no network)",
    "policies": "run in the operator shell, in the kit (reads only)",
    "ask": "run in the operator shell, in the kit (acme's pin back to RAG Engine, then one question for each tenant)",
    "join": "run in the operator shell, in the kit (the same question to the API, then through the kit's own retrieve())",
    "note": "run in the operator shell, in the kit (a note to globex, whose text may not leave India)",
    "logs": "run in the operator shell, in the kit (reads only)",
    "globex": "run in the operator shell, in the kit (globex pinned to a store for one question, then unpinned)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own managed.py and tenancy.py)",
    "policies": "(the kit's tenancy CLI and managed.py on a stand-in lane holding the corpus make ingest-corpus sends; your counts include your own uploads)",
    "ask": "(the kit's rag-api on a stand-in lane: RAG Engine, Vertex AI Search and Gemini stood in; your pool sizes and ids are your stores')",
    "join": "(the same stand-ins; the kit's retrieve() run in the cell's own process)",
    "note": "(gcloud's copy lines as a shape; the worker's line from the stand-in: your doc_key differs, the note carries your email and the time)",
    "logs": "(the kit's own Mirror, as the worker calls it after a swap, on the stand-in lane; your times are yours)",
    "globex": "(the kit's rag-api on the stand-in lane)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

STATS = {"N_CHECKED": str(N_CHECKED), "POOL_ACME": str(POOL_ACME), "MANAGED_ACME": str(MANAGED_ACME), "N_MEDIA": str(len(MEDIA_KEYS)),
         "ACME_CURRENT": "21", "ACME_HELD": "18", "ZETA_HELD": "7", "COST_RS": f"{COST_RS:.2f}"}

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
print(f"kit: tenancy, managed.py, the Mirror, rag-api and retrieve() on a stand-in lane | acme cited from RAG Engine (found_by rag_engine),"
      f" globex skipped twice (mirror_policy_skipped) | panel port checked on {N_CHECKED} combinations")
