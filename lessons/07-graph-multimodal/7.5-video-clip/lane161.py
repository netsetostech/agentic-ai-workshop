"""The stand-in lane for lesson 7.5's build. Under it the kit's own code runs unchanged: evals/build_media.py for
make media, reconcile.py for make retire, the ingest worker's push handler (services/ingest/main.py) for every
upload, rag-api (its query, stream and media routes) for the questions, the MCP server for list_documents, and
smoke/smoke_media.py for make smoke-media.

What is stood in, and how:
  Firestore      a JSON file of what the kit writes, over a read-only base of the corpus's chunk rows (the three
                 tenants' files as evals/upload.sh sends them, cut by the kit's chunker) and the worker's claims;
                 subcollections (the roster), batches, transactions, Increment, DELETE_FIELD and SERVER_TIMESTAMP
                 behave as Firestore's do.
  Cloud Storage  a JSON file of objects with generations: the uploads, media and audit buckets. A signed URL is a
                 URL of the same shape; a signed PUT goes to a local server that stores the object and hands its
                 finalize event to the worker, as the uploads bucket's notification does.
  RAG Engine,    acme's and zeta's managed stores, holding a copy of each text version (lesson 7.3), so make
  Vertex AI      retire's store deletes have something to delete.
  Search
  Gemini         the worker's description of a video is its segments, one per speaker turn of the town hall, timed
                 from the ground truth build_media.py wrote and summarised by hand the way the worker's prompt asks
                 (every number quoted); a figure is a caption; the Studio's image is a fixed PNG; the answer is a
                 reader of the packed sources. Embeddings are constant vectors: the stand-in ranks by text.
  Text-to-Speech two Chirp 3 HD voices that speak at a fixed rate; ffmpeg writes a file of the size an encode of
  and ffmpeg     that length would have.
  gcloud         the identity token: MEMBER for documind-ui-sa, OUTSIDER for documind-outsider-sa.
"""
import asyncio
import base64
import collections
import contextlib
import datetime as dt
import io
import json
import logging
import math
import os
import random
import re
import runpy
import struct
import subprocess
import sys
import types
import wave
import zlib
from types import SimpleNamespace

KIT = os.environ["LANE161_KIT"]
PROJ = os.environ["GOOGLE_CLOUD_PROJECT"]
with open(os.environ["LANE161_BASE"], encoding="utf-8") as _f:
    BASE = json.load(_f)                   # {"rows": {chunk_id: row}, "texts": {tenant: {doc_key: {"text", "source_uri", "pdf"}}}}
PATHS = {k: os.environ[f"LANE161_{k.upper()}"] for k in ("fs", "gcs", "stores", "logs")}
_STATE, _KEY = {}, {}


def _get(name: str) -> dict:
    """A state file, read again only when another process has written it."""
    path = PATHS[name]
    try:
        st = os.stat(path)
        key = (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        key = None
    if _KEY.get(name) != key or name not in _STATE:
        _STATE[name] = {}
        if key:
            with open(path, encoding="utf-8") as f:
                _STATE[name] = json.load(f)
        _KEY[name] = key
    return _STATE[name]


def _put(name: str) -> None:
    text = json.dumps(_STATE[name], default=repr)          # serialised whole first: a bad value never leaves half a file
    tmp = PATHS[name] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, PATHS[name])
    st = os.stat(PATHS[name])
    _KEY[name] = (st.st_mtime_ns, st.st_size)


# ---- the clock: each process starts at LANE161_NOW and moves 50 ms a call (a worker run is a few hundred calls)
_DATETIME = dt.datetime                                    # the real class: freeze() swaps the module's name for a subclass
_T0 = _DATETIME.fromisoformat(os.environ.get("LANE161_NOW", "2026-09-24T08:00:00+00:00"))
_TICK = [0]


def now() -> dt.datetime:
    _TICK[0] += 1
    return _T0 + dt.timedelta(milliseconds=50 * _TICK[0])


def freeze() -> None:
    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            t = now()
            return t.astimezone(tz) if tz else t.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return now().replace(tzinfo=None)
    dt.datetime = _Frozen


_MONO = [0.0]


def fake_time() -> None:
    """time.sleep moves a virtual clock that time.monotonic reads; nothing waits."""
    import time as _t
    _t.sleep = lambda s: _MONO.__setitem__(0, _MONO[0] + s)
    _t.monotonic = lambda: _MONO[0]


# ---- word overlap, TF-IDF weighted: the dense path, the Ranking API, BM25's stand-in and both stores' ranking
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


_DENSE = []


def sim(a: str, b: str) -> float:
    if not _DENSE:
        _DENSE.append(Tfidf(sorted({r["text"] for r in BASE["rows"].values()})))
    return _DENSE[0].sim(a, b)


LAST = {"q": ""}


# ---- Firestore
def _row(coll: str, id_: str):
    over = _get("fs").get(coll, {})
    if id_ in over:
        return over[id_]
    return BASE["rows"].get(id_) if coll == "chunks" else None


def rows(coll: str) -> dict:
    over = _get("fs").get(coll, {})
    out = dict(BASE["rows"]) if coll == "chunks" else {}
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
    return out


def _clean(v):
    if type(v).__name__ == "Vector":
        return [float(x) for x in v]
    if isinstance(v, _DATETIME):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def _apply(old: dict, data: dict, merge: bool) -> dict:
    new = dict(old or {}) if merge else {}
    for k, v in data.items():
        name = type(v).__name__
        if name == "Sentinel":
            if "delete" in repr(v).lower():
                new.pop(k, None)
            else:
                new[k] = now().isoformat()                 # SERVER_TIMESTAMP: the writer's clock
        elif name == "Increment":
            new[k] = (new.get(k) or 0) + v.value
        else:
            new[k] = _clean(v)
    return new


def _write(coll: str, id_: str, value, save: bool = True) -> None:
    _get("fs").setdefault(coll, {})[id_] = value
    if save:
        _put("fs")


class _CollRef:
    """A collection's reference: .parent is the document it hangs under (tenants/acme for tenants/acme/members)."""

    def __init__(self, path: str):
        parts = path.split("/")
        self.id = parts[-1]
        self.parent = Doc("/".join(parts[:-2]), parts[-2]) if len(parts) >= 3 else None


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

    def get(self, transaction=None, **kw):
        return Snap(self.coll, self.id, _row(self.coll, self.id))

    def set(self, data, merge=False, save=True):
        _write(self.coll, self.id, _apply(_row(self.coll, self.id), data, merge), save)

    def update(self, data, save=True):
        _write(self.coll, self.id, _apply(_row(self.coll, self.id), data, True), save)

    def delete(self, save=True):
        _write(self.coll, self.id, None, save)

    def collection(self, name):
        return Query(f"{self.coll}/{self.id}/{name}")

    @property
    def parent(self):
        return _CollRef(self.coll)


class Batch:
    def __init__(self):
        self.ops = []

    def set(self, ref, data, merge=False):
        self.ops.append(("set", ref, data, merge))

    def update(self, ref, data):
        self.ops.append(("update", ref, data, True))

    def delete(self, ref):
        self.ops.append(("delete", ref, None, False))

    def commit(self):
        for op, ref, data, merge in self.ops:
            if op == "delete":
                ref.delete(save=False)
            elif op == "update":
                ref.update(data, save=False)
            else:
                ref.set(data, merge, save=False)
        self.ops = []
        _put("fs")


class Tx:
    def set(self, ref, data, merge=False):
        ref.set(data, merge)

    def update(self, ref, data):
        ref.update(data)


def _holds(id_, d, field, op, value) -> bool:
    x = id_ if field == "__name__" else d.get(field)
    if op == "==":
        return x == value
    if op == "in":
        return x in value
    raise NotImplementedError(op)


class Query:
    def __init__(self, coll: str, preds=(), lim=None, group=False):
        self.coll, self.preds, self.lim, self.group = coll, tuple(preds), lim, group

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.coll, self.preds + ((field, op, value),), self.lim, self.group)

    def select(self, fields):
        return self

    def order_by(self, *a, **kw):
        return self

    def limit(self, n):
        return Query(self.coll, self.preds, n, self.group)

    def _colls(self) -> list:
        """The collection, or for a collection group every collection of that name at any depth."""
        if not self.group:
            return [self.coll]
        names = set(_get("fs")) | ({"chunks"} if self.coll == "chunks" else set())
        return sorted(c for c in names if c == self.coll or c.endswith("/" + self.coll))

    def found(self) -> list:
        return [(c, i, d) for c in self._colls() for i, d in sorted(rows(c).items()) if all(_holds(i, d, *p) for p in self.preds)]

    def document(self, id_=None):
        if id_ is None:
            id_ = f"auto-{sum(1 for _ in rows(self.coll)) + 1}"
        return Doc(self.coll, id_)

    def add(self, data):
        ref = self.document()
        ref.set(data)
        return None, ref

    def matched(self) -> list:
        return [(i, d) for _, i, d in self.found()]

    def stream(self):
        return [Snap(c, i, d) for c, i, d in self.found()[:self.lim]]

    get = stream

    def find_nearest(self, vector_field=None, query_vector=None, distance_measure=None, limit=10, distance_result_field=None, **kw):
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
        return Query(name, group=True)

    def batch(self):
        return Batch()

    def transaction(self, **kw):
        return Tx()


DB = DBClass()


# ---- Cloud Storage: objects with generations
def _objects(bucket: str) -> dict:
    return _get("gcs").setdefault(bucket, {})


def _next_gen() -> str:
    st = _get("gcs")
    st["_gen"] = st.get("_gen", 1758000000000000) + 1000
    return str(st["_gen"])


class Blob:
    def __init__(self, bucket: str, name: str, generation=None):
        self.bucket_name, self.name, self._want = bucket, name, None if generation is None else str(generation)

    def _version(self):
        vs = _objects(self.bucket_name).get(self.name) or []
        if self._want is None:
            return vs[-1] if vs else None
        return next((v for v in vs if v["gen"] == self._want), None)

    @property
    def generation(self):
        v = self._version()
        return int(v["gen"]) if v else None

    @property
    def time_created(self):
        v = self._version()
        return _DATETIME.fromisoformat(v["created"]) if v else None

    @property
    def size(self):
        v = self._version()
        return len(base64.b64decode(v["b64"])) if v else None

    def download_as_bytes(self, **kw):
        v = self._version()
        if v is None:
            from google.api_core.exceptions import NotFound
            raise NotFound(f"gs://{self.bucket_name}/{self.name}#{self._want}")
        return base64.b64decode(v["b64"])

    def download_as_text(self, encoding="utf-8", **kw):
        return self.download_as_bytes().decode(encoding)

    def upload_from_string(self, data, content_type=None, **kw):
        raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        gen = _next_gen()
        _objects(self.bucket_name).setdefault(self.name, []).append(
            {"gen": gen, "b64": base64.b64encode(raw).decode(), "ct": content_type or "", "created": now().isoformat()})
        self._want = None
        _put("gcs")

    def rewrite(self, source, **kw):
        v = source._version()
        gen = _next_gen()
        _objects(self.bucket_name).setdefault(self.name, []).append({**v, "gen": gen, "created": now().isoformat()})
        self._want = None
        _put("gcs")
        return None, len(base64.b64decode(v["b64"])), len(base64.b64decode(v["b64"]))

    def delete(self, **kw):
        _objects(self.bucket_name).pop(self.name, None)
        _put("gcs")

    def exists(self, **kw):
        return self._version() is not None

    def generate_signed_url(self, version="v4", expiration=None, method="GET", content_type=None, credentials=None, **kw):
        """A V4 signed URL's shape, signature cut. A PUT goes to the local door of the bucket (LANE161_GCSURL), which
        stores the object and hands its finalize event to the worker; a GET is only printed."""
        base = os.environ.get("LANE161_GCSURL", "") if method == "PUT" else ""
        who = getattr(credentials, "signer_email", None) or f"documind-api-sa@{PROJ}.iam.gserviceaccount.com"
        heads = "content-type%3Bhost" if content_type else "host"
        return (f"{base or 'https://storage.googleapis.com'}/{self.bucket_name}/{self.name}?X-Goog-Algorithm=GOOG4-RSA-SHA256"
                f"&X-Goog-Credential={who.replace('@', '%40')}%2F20260924%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260924T083000Z"
                f"&X-Goog-Expires=900&X-Goog-SignedHeaders={heads}&X-Goog-Signature=...")


class Bucket:
    def __init__(self, name: str):
        self.name = name

    def blob(self, name, generation=None, **kw):
        return Blob(self.name, name, generation)

    def get_blob(self, name, **kw):
        b = Blob(self.name, name)
        return b if b._version() else None

    def list_blobs(self, prefix=None, **kw):
        return [Blob(self.name, n) for n in sorted(_objects(self.name)) if not n.startswith("_") and (not prefix or n.startswith(prefix))]


class GCSClient:
    def __init__(self, *a, **kw):
        pass

    def bucket(self, name):
        return Bucket(name)


def upload(name: str, data: bytes, content_type: str = "text/markdown") -> str:
    """What gcloud storage cp does to the uploads bucket: a new generation of the object."""
    b = Bucket(f"{PROJ}-uploads").blob(name)
    b.upload_from_string(data, content_type)
    return str(b.generation)


# ---- RAG Engine (vertexai.rag) and Vertex AI Search (discoveryengine_v1), holding what the mirror writes
def _stores() -> dict:
    return _get("stores")


def _text_of(tenant: str, e: dict, dk: str) -> str:
    return e.get("text") if "text" in e else BASE["texts"].get(tenant, {}).get(dk, {}).get("text", "")


def corpus_name(tenant: str) -> str:
    return f"projects/NUMBER/locations/us-central1/ragCorpora/{tenant}-corpus"


SIZE, STEP = 384, 309                               # 512 tokens with 100 overlapping, in words (a word is about 1.33 tokens)
_WIN = {}


def windows(tenant: str):
    files = _stores()["rag"].get(tenant, {})
    key = (tenant, tuple(sorted(files)))
    if key not in _WIN:
        out = []
        for dk in sorted(files):
            words = _text_of(tenant, files[dk], dk).split()
            for i in range(0, len(words), STEP):
                out.append((dk, " ".join(words[i:i + SIZE])))
                if i + SIZE >= len(words):
                    break
        _WIN.clear()
        _WIN[key] = (out, Tfidf([w for _, w in out]), Tfidf([w for _, w in out], pairs=True))
    return _WIN[key]


class _Kw:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Rag(types.ModuleType):
    RagResource = RagRetrievalConfig = Filter = TransformationConfig = ChunkingConfig = _Kw
    RagEmbeddingModelConfig = VertexPredictionEndpoint = RagVectorDbConfig = _Kw

    def list_corpora(self):
        return [SimpleNamespace(name=corpus_name(t), display_name=f"documind-{t}") for t in _stores()["corpora"]]

    def _tenant(self, corpus: str) -> str:
        return corpus.rsplit("/", 1)[1].removesuffix("-corpus")

    def list_files(self, corpus_name_):
        t = self._tenant(corpus_name_)
        return [SimpleNamespace(name=e["name"], display_name=dk, description=e["source_uri"])
                for dk, e in sorted(_stores()["rag"].get(t, {}).items())]

    def upload_file(self, corpus_name, path, display_name, description="", transformation_config=None, **kw):
        st = _stores()
        t = self._tenant(corpus_name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        st["n"] = st.get("n", 0) + 1
        name = f"{corpus_name}/ragFiles/{st['n']}"
        st["rag"].setdefault(t, {})[display_name] = {"name": name, "source_uri": description, "text": text}
        _put("stores")
        return SimpleNamespace(name=name, display_name=display_name)

    def delete_file(self, name, corpus_name=None, **kw):
        st = _stores()
        t = self._tenant(corpus_name or name.split("/ragFiles/")[0])
        files = st["rag"].get(t, {})
        for dk in [dk for dk, e in files.items() if e["name"] == name]:
            del files[dk]
        _put("stores")

    def retrieval_query(self, rag_resources, text, rag_retrieval_config):
        t = self._tenant(rag_resources[0].rag_corpus)
        win, uni, bi = windows(t)
        cfg = rag_retrieval_config
        scored = sorted(((round(max(0.05, 0.62 - 1.2 * (uni.sim(text, w) + bi.sim(text, w))), 4), dk, w) for dk, w in win),
                        key=lambda x: (x[0], x[1], x[2]))
        files = _stores()["rag"].get(t, {})
        ctxs = [SimpleNamespace(source_display_name=dk, source_uri=files[dk]["source_uri"], text=w, score=d, chunk=SimpleNamespace(page_span=None))
                for d, dk, w in scored if d < cfg.filter.vector_distance_threshold][:cfg.top_k]
        return SimpleNamespace(contexts=SimpleNamespace(contexts=ctxs))


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


def _store_of(path: str) -> str:
    return path.split("/dataStores/", 1)[1].split("/", 1)[0].removeprefix("documind-")


def _not_found(what: str):
    from google.api_core.exceptions import NotFound
    return NotFound(what)


def _visible(tenant: str) -> dict:
    return {dk: e for dk, e in _stores()["vs"].get(tenant, {}).items() if e.get("left", 0) == 0}


def _segments(query: str, text: str, pdf: bool, t: Tfidf, k: int) -> list:
    out, page = [], 1
    for block_ in re.split(r"\n\s*\n", text):
        para = " ".join(block_.replace("\f", " ").split())
        if para:
            out.append((para, page))
        page += block_.count("\f")
    scored = sorted(((t.sim(query, p), -i, p, pg) for i, (p, pg) in enumerate(out)), reverse=True)
    segs = []
    for s, _, p, pg in scored[:k]:
        if s <= 0:
            break
        segs.append({"content": p, **({"pageNumber": str(pg)} if pdf else {})})
    return segs


class _SearchClient:
    def search(self, request):
        t = _store_of(request.serving_config)
        if t not in _stores()["data_stores"]:
            raise _not_found(f"DataStore documind-{t} not found")
        docs = _visible(t)
        texts = {dk: _text_of(t, e, dk) for dk, e in docs.items()}
        tf = Tfidf([p for x in texts.values() for p in re.split(r"\n\s*\n", x)])
        ranked = sorted(((tf.sim(request.query, x), dk) for dk, x in texts.items()), key=lambda x: (-x[0], x[1]))
        k = request.content_search_spec.extractive_content_spec.max_extractive_segment_count
        out = []
        for s, dk in ranked[:request.page_size]:
            if s < 0.03:
                break
            pdf = BASE["texts"].get(t, {}).get(dk, {}).get("pdf", False)
            out.append(SimpleNamespace(document=_Document(id=dk, name=f"{request.serving_config}/documents/{dk}",
                                                          struct_data={"source_uri": docs[dk]["source_uri"]},
                                                          derived_struct_data={"extractive_segments": _segments(request.query, texts[dk], pdf, tf, k)})))
        return out


class _DataStoreClient:
    def get_data_store(self, name):
        if _store_of(name) not in _stores()["data_stores"]:
            raise _not_found(f"DataStore {name.rsplit('/', 1)[-1]} not found")
        return SimpleNamespace(name=name)


class _DocumentClient:
    def list_documents(self, parent):
        """A listing is also time passing: an import in flight gets a step nearer done."""
        st = _stores()
        t = _store_of(parent)
        docs = st["vs"].get(t, {})
        moved = False
        for e in docs.values():
            if e.get("left", 0) > 0:
                e["left"] -= 1
                moved = True
        if moved:
            _put("stores")
        return [_Document(id=dk, name=f"{parent}/documents/{dk}", struct_data={"source_uri": e["source_uri"], "doc_key": dk})
                for dk, e in sorted(_visible(t).items())]

    def import_documents(self, request):
        st = _stores()
        t = _store_of(request.parent)
        if st.get("fail_next_vs"):
            st["fail_next_vs"] = False
            _put("stores")
            raise RuntimeError("503 The service is currently unavailable.")
        for doc in request.inline_source.documents:
            uri = doc.content.uri
            bucket, obj = uri[len("gs://"):].split("/", 1)
            text = Bucket(bucket).blob(obj).download_as_text()
            st["vs"].setdefault(t, {})[doc.id] = {"source_uri": doc.struct_data["source_uri"], "text": text, "left": 2}
        st["n"] = st.get("n", 0) + 1
        _put("stores")
        return SimpleNamespace(operation=SimpleNamespace(name=f"{request.parent}/operations/import-documents-{st['n']}"))

    def delete_document(self, name):
        st = _stores()
        t = _store_of(name)
        dk = name.rsplit("/", 1)[1]
        if dk not in st["vs"].get(t, {}):
            raise _not_found(f"Document {dk} not found")
        del st["vs"][t][dk]
        _put("stores")


class _RankClient:
    def __init__(self, *a, **kw):
        pass

    def ranking_config_path(self, project, location, ranking_config):
        return f"projects/{project}/locations/{location}/rankingConfigs/{ranking_config}"

    def rank(self, request, timeout=None):
        order = sorted(((sim(request.query, r.content), int(r.id)) for r in request.records), key=lambda x: (-x[0], x[1]))
        return SimpleNamespace(records=[SimpleNamespace(id=str(i), score=round(s, 4)) for s, i in order[:request.top_n]])


class BM25Okapi:
    """rank_bm25 0.2.2's BM25Okapi (k1 1.5, b 0.75, epsilon 0.25 for a negative idf), stood in."""

    def __init__(self, corpus, k1=1.5, b=0.75, epsilon=0.25):
        self.k1, self.b = k1, b
        self.doc_len = [len(d) for d in corpus]
        self.avgdl = sum(self.doc_len) / max(1, len(corpus))
        self.doc_freqs = [collections.Counter(d) for d in corpus]
        nd = collections.Counter(w for d in corpus for w in set(d))
        self.idf, negative, total = {}, [], 0.0
        for w, freq in nd.items():
            idf = math.log(len(corpus) - freq + 0.5) - math.log(freq + 0.5)
            self.idf[w] = idf
            total += idf
            if idf < 0:
                negative.append(w)
        eps = epsilon * total / max(1, len(self.idf))
        for w in negative:
            self.idf[w] = eps

    def get_scores(self, query):
        score = [0.0] * len(self.doc_len)
        for q in query:
            idf = self.idf.get(q) or 0.0
            score = [s + idf * (f.get(q, 0) * (self.k1 + 1) / (f.get(q, 0) + self.k1 * (1 - self.b + self.b * dl / self.avgdl)))
                     for s, f, dl in zip(score, self.doc_freqs, self.doc_len)]
        return score


# ---- Gemini
# The worker's description of the town hall: one segment per speaker turn, summarised as its prompt asks (two
# sentences of what is said and shown, every number quoted as spoken). The times come from the ground truth
# build_media.py wrote beside the video (LANE161_TRUTH): each segment runs from its turn's start to the next turn's.
SUMMARIES = [
    "Meera, the CEO, opens the FY2026 town hall over a first slide saying the video is synthetic, welcoming staff joining from "
    "Hyderabad, Pune and the regional offices. Meera says ACME closed the year at one thousand and five crore rupees of revenue, "
    "up 19.8 per cent on FY2025, and hands over to Arjun for the regions.",
    "Arjun, the CFO, walks through the revenue table on slide two: India grew from 412 to 508 crore, up 23.3 per cent; APAC "
    "excluding India from 188 to 236 crore, up 25.5 per cent; the Americas from 143 to 170 crore, up 18.9 per cent. EMEA is the "
    "one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped "
    "into the first quarter of FY2027.",
    "Meera says headcount closed at 4,180, up from 3,742, and attrition came down to 11.4 per cent from 14.9 per cent, over the "
    "slide on people and capital. Meera calls the attrition improvement the one to be proudest of.",
    "Arjun says capital expenditure was 78 crore for the year: 31 crore went into the Hyderabad plant expansion and 12 crore into "
    "cloud and the data platform, where DocuMind runs. Arjun points to the annual report for every figure: AR-02 for revenue, "
    "AR-05 for headcount and AR-09 for capex.",
    "Meera thanks Arjun and says questions are open on the portal until Friday, over a closing slide. The recording and the "
    "transcript will be in DocuMind by the afternoon.",
]
CAPTIONS = {"smoke_media_probe.png": "A blank white image one pixel square, with no text, chart or table on it.\n\n"
                                     "Key facts: none; the image carries no information."}


def _png(w: int = 8, h: int = 8, rgb: tuple = (13, 148, 136)) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _usage(prompt: str, out: str):
    return SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(out) // 4 + 24,
                           thoughts_token_count=0, cached_content_token_count=0)


def _describe(uri: str, mime: str):
    """_describe_media's call: segments for a video, a caption for an image."""
    if mime.startswith("video/"):
        with open(os.environ["LANE161_TRUTH"], encoding="utf-8") as f:
            turns = json.load(f)["segments"]
        segs = []
        for i, t in enumerate(turns):
            end = math.floor(turns[i + 1]["start"]) if i + 1 < len(turns) else math.ceil(t["end"])
            segs.append(SimpleNamespace(start=float(math.floor(t["start"])), end=float(end), summary=SUMMARIES[i]))
        text = json.dumps([vars(s) for s in segs])
        return SimpleNamespace(parsed=segs, text=text, usage_metadata=_usage(uri, text))
    text = CAPTIONS.get(uri.rsplit("/", 1)[-1], "An image with no text on it.")
    return SimpleNamespace(parsed=None, text=text, usage_metadata=_usage(uri, text))


def _image():
    """media.py's generate: the image part of the Studio's answer."""
    parts = [SimpleNamespace(text="Here is the chart.", inline_data=None), SimpleNamespace(text=None, inline_data=SimpleNamespace(data=_png(), mime_type="image/png"))]
    return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))], usage_metadata=_usage("", ""))


def _sources(prompt: str) -> tuple:
    question = prompt.rsplit("\n\nQuestion:", 1)[1].strip()
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    return question, [(int(parts[k]), parts[k + 1], " ".join(parts[k + 2].split())) for k in range(1, len(parts) - 2, 3)]


def _draft(prompt: str) -> dict:
    """The reader: the clause a question asks for, from the first packed source that carries it, cited by its number."""
    question, srcs = _sources(prompt)
    q = question.lower()
    for n, head, body in srcs:
        if "town hall" in q and ".mp4" in head and "5.2 per cent" in body:
            quote = re.search(r"EMEA is the one region that shrank: revenue fell 5\.2 per cent, from 96 crore to 91 crore", body).group(0)
            return {"answer": "The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, "
                              f"because two large renewals in Germany slipped into the first quarter of FY2027 [{n}].",
                    "citations": [{"source": n, "quote": quote}], "confidence": "high", "answerable": True}
        if "figure 3" in q and ".png" in head and "EMEA" in body:
            quote = re.search(r"EMEA fell from 96 to 91 \(-5\.2%\)", body).group(0)
            return {"answer": f"EMEA's revenue declined, from Rs 96 crore in FY2025 to Rs 91 crore in FY2026, down 5.2 per cent [{n}].",
                    "citations": [{"source": n, "quote": quote}], "confidence": "high", "answerable": True}
    return {"answer": "The context does not say.", "citations": [], "confidence": "low", "answerable": False}


def _reply(prompt: str):
    draft = _draft(prompt)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=_usage(prompt, draft["answer"]),
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


def _stream(prompt: str):
    """/v1/stream's call: no schema, the answer's text in pieces, the totals on the last."""
    text = _draft(prompt)["answer"]
    words = text.split(" ")
    cut = [0, len(words) // 3, 2 * len(words) // 3, len(words)]
    for k in range(3):
        piece = " ".join(words[cut[k]:cut[k + 1]]) + (" " if k < 2 else "")
        yield SimpleNamespace(text=piece, usage_metadata=_usage(prompt, text) if k == 2 else None)


def _prompt_of(items: list):
    return next((p for p in items if isinstance(p, str) and "\nContext:\n" in p), None)


class Models:
    def generate_content(self, model, contents, config=None):
        items = contents if isinstance(contents, list) else [contents]
        if model == "gemini-3.1-flash-image":
            return _image()
        prompt = _prompt_of(items)
        media = next((p for p in items if getattr(getattr(p, "file_data", None), "mime_type", None)), None)
        if prompt is None and media is not None:
            return _describe(media.file_data.file_uri, media.file_data.mime_type)
        return _reply(prompt if prompt is not None else items[0])

    def generate_content_stream(self, model, contents, config=None):
        items = contents if isinstance(contents, list) else [contents]
        return _stream(_prompt_of(items))

    def embed_content(self, model, contents, config=None):
        texts = [contents] if isinstance(contents, str) else list(contents)
        task = config.get("task_type") if isinstance(config, dict) else getattr(config, "task_type", None)
        if task != "RETRIEVAL_DOCUMENT":
            LAST["q"] = texts[0]                           # a question: the stand-in's nearest neighbours read its text
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.0] * 768) for _ in texts])


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
    """Gemini, Firestore, Cloud Storage, RAG Engine, Vertex AI Search, the Ranking API and BM25, for every process."""
    if "vertexai.rag" in sys.modules:
        return
    rag = _Rag("vertexai.rag")
    sys.modules["vertexai.rag"] = rag
    _mod("vertexai", init=lambda **kw: None, rag=rag)
    _mod("google.cloud.discoveryengine_v1", SearchServiceClient=_SearchClient, DataStoreServiceClient=_DataStoreClient,
         DocumentServiceClient=_DocumentClient, SearchRequest=_SearchRequest, Document=_Document, ImportDocumentsRequest=_Import,
         RankServiceClient=_RankClient, RankingRecord=_Kw, RankRequest=_Kw)
    _mod("google.cloud.storage", Client=GCSClient)
    _mod("rank_bm25", BM25Okapi=BM25Okapi)
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB
    google.cloud.firestore.transactional = lambda fn: (lambda tx, *a, **kw: fn(tx, *a, **kw))


# ---- make media MEDIA_ARGS=--video: Text-to-Speech's two voices and ffmpeg
VOICES = ["en-IN-Chirp3-HD-Achernar", "en-IN-Chirp3-HD-Aoede", "en-IN-Chirp3-HD-Charon", "en-IN-Chirp3-HD-Fenrir", "en-IN-Chirp3-HD-Kore",
          "en-IN-Chirp3-HD-Leda", "en-IN-Chirp3-HD-Orus", "en-IN-Chirp3-HD-Puck", "en-IN-Neural2-A", "en-IN-Standard-A"]
RATE = {"Aoede": 14.2, "Charon": 13.4}                    # characters a second: the stand-in's voices, one a little slower


def tts() -> None:
    class TextToSpeechClient:
        def __init__(self, *a, **kw):
            pass

        def list_voices(self, language_code=None, **kw):
            return SimpleNamespace(voices=[SimpleNamespace(name=n) for n in VOICES if n.startswith(language_code or "")])

        def synthesize_speech(self, input=None, voice=None, audio_config=None, **kw):
            frames = int(len(input.text) / RATE.get(voice.name.rsplit("-", 1)[1], 14.0) * audio_config.sample_rate_hertz)
            return SimpleNamespace(audio_content=b"RIFF" + bytes(40) + bytes(2 * frames))     # a WAV header, then PCM16 mono
    _mod("google.cloud.texttospeech", TextToSpeechClient=TextToSpeechClient, SynthesisInput=_Kw, VoiceSelectionParams=_Kw,
         AudioConfig=_Kw, AudioEncoding=SimpleNamespace(LINEAR16="LINEAR16"))


def ffmpeg() -> None:
    """ffmpeg on PATH; its encode writes a file of the size AAC at 96 kb/s and a still-image H.264 track would have."""
    import shutil
    real_which, real_run = shutil.which, subprocess.run
    shutil.which = lambda name, *a, **kw: "/usr/bin/ffmpeg" if name == "ffmpeg" else real_which(name, *a, **kw)

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "/usr/bin/ffmpeg":
            wav = cmd[cmd.index("-i", cmd.index("-i") + 1) + 1]        # the second input: the narration
            with wave.open(wav) as w:
                seconds = w.getnframes() / w.getframerate()
            size = int(seconds * 13_900)
            with open(cmd[-1], "wb") as f:
                f.write(b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + random.Random(int(seconds * 1000)).randbytes(size - 32))
            return subprocess.CompletedProcess(list(cmd), 0, "", "")
        return real_run(cmd, *a, **kw)
    subprocess.run = run


def worker_stubs() -> None:
    """What the ingest worker imports that this machine does not have: Document AI, DLP, Vertex AI's index types."""
    install()
    _mod("google.cloud.documentai", DocumentProcessorServiceClient=Anything)
    _mod("google.cloud.dlp_v2", DlpServiceClient=Anything)
    sys.path[:0] = [os.path.join(KIT, "services", "ingest"), KIT]
    import shared
    pii = _mod("shared.pii", inspect_image=lambda content, content_type=None: [], inspect_many=lambda texts: [[] for _ in texts])
    shared.pii = pii
    class IndexDatapoint(_Kw):                             # indexer.py names its nested types in annotations
        class SparseEmbedding(_Kw):
            pass

        class Restriction(_Kw):
            pass
    types_ = _mod("google.cloud.aiplatform_v1.types", IndexDatapoint=IndexDatapoint)
    _mod("google.cloud.aiplatform_v1", types=types_)
    _mod("google.cloud.aiplatform", MatchingEngineIndex=Anything, MatchingEngineIndexEndpoint=Anything, init=lambda **kw: None)
    _mod("google.cloud.bigquery", Client=Anything)


# ---- the worker, for one finalize event of the uploads bucket
_LOGS = []


class _Keep(logging.Handler):
    def emit(self, r):
        try:
            j = json.loads(r.getMessage())
        except ValueError:
            return
        _LOGS.append({"timestamp": now().isoformat().replace("+00:00", "Z"),
                      "resource": {"type": "cloud_run_revision", "labels": {"service_name": _SERVICE[0]}}, "jsonPayload": j})


_SERVICE = ["documind-ingest"]


def capture(service: str) -> None:
    _SERVICE[0] = service
    root = logging.getLogger()
    root.addHandler(_Keep())
    root.setLevel(logging.INFO)


def flush_logs() -> None:
    if _LOGS:
        st = _get("logs")
        st.setdefault("entries", []).extend(_LOGS)
        del _LOGS[:]
        _put("logs")


_W = []


def worker(name: str, generation: str, content_type: str = "text/markdown") -> dict:
    """services/ingest/main.py's push handler, given the event Eventarc would deliver for this generation."""
    if not _W:
        worker_stubs()
        capture("documind-ingest")
        import main as W                                   # the ingest worker, unchanged
        _W.append(W)
    data = Bucket(f"{PROJ}-uploads").blob(name, generation).download_as_bytes()
    msg = {"bucket": f"{PROJ}-uploads", "name": name, "size": len(data), "contentType": content_type, "generation": str(generation)}
    envelope = {"message": {"data": base64.b64encode(json.dumps(msg).encode()).decode()}}

    class Req:
        async def json(self):
            return envelope
    before = len(_LOGS)
    result = asyncio.run(_W[0].push(Req()))
    lines = [e["jsonPayload"] for e in _LOGS[before:]]
    flush_logs()
    return {"result": result, "lines": lines}


def reconcile(argv: list) -> tuple:
    """services/ingest/reconcile.py, as make retire / make restore / make reconcile run it; its stdout and exit code."""
    install()
    sys.path[:0] = [os.path.join(KIT, "services", "ingest"), KIT]
    old = sys.argv
    sys.argv = ["reconcile.py"] + list(argv)
    buf, code = io.StringIO(), 0
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(os.path.join(KIT, "services", "ingest", "reconcile.py"), run_name="__main__")
    except SystemExit as e:
        code = e.code or 0
    finally:
        sys.argv = old
    return buf.getvalue(), code


def managed_status(argv: list) -> str:
    """services/ingest/managed.py --status, as make managed-status runs it."""
    install()
    sys.path[:0] = [os.path.join(KIT, "services", "ingest"), KIT]
    old, cwd = sys.argv, os.getcwd()
    sys.argv = ["managed.py"] + list(argv)
    buf = io.StringIO()
    try:
        os.chdir(os.path.join(KIT, "services", "ingest"))
        with contextlib.redirect_stdout(buf):
            runpy.run_path("managed.py", run_name="__main__")
    except SystemExit as e:
        assert not e.code, e.code
    finally:
        sys.argv = old
        os.chdir(cwd)
    return buf.getvalue()


def fake_cli() -> None:
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and list(cmd[:3]) == ["gcloud", "auth", "print-identity-token"]:
            who = "OUTSIDER" if any("outsider" in str(c) for c in cmd) else "MEMBER"
            return subprocess.CompletedProcess(list(cmd), 0, who + "\n", "")
        if isinstance(cmd, (list, tuple)) and list(cmd[:3]) == ["make", "-s", "managed-status"]:
            args = dict(a_.split("=", 1) for a_ in cmd[3:])
            out = managed_status(["--project", args["PROJECT"], "--status", "--mode", "both"]
                                 + (["--tenant", args["TENANT_ONLY"]] if args.get("TENANT_ONLY") else []))
            return subprocess.CompletedProcess(list(cmd), 0, out, "")
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] in ("gcloud", "make"):
            raise SystemExit(f"the stand-in has no answer for {cmd[:4]}")
        return real_run(cmd, *a, **kw)
    subprocess.run = run


# ---- rag-api, for the questions
def stubs() -> None:
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


def serve(port: int, who: dict) -> None:
    stubs()
    sys.path[:0] = [KIT, os.path.join(KIT, "services", "rag-api")]
    import main
    import retriever
    import generator
    import cache_manager
    import shared.iap as iap
    import media
    main._fs = retriever._fs = lambda: DB
    retriever._ranker = lambda: _RankClient()
    media._signing_kwargs = lambda: {}                     # the roster check (auth.enforce_membership) is the kit's, on the roster rows

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity
    import uvicorn
    uvicorn.run(main.app, host="127.0.0.1", port=port, log_level="warning")


def _identity_for(who: dict):
    import shared.iap as iap

    def identity(headers, bearer_audience=None):           # Google's signature check stood in; who is on which roster is the kit's
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity


def mcp_serve(port: int, who: dict) -> None:
    """services/mcp/server.py, unchanged, over the stand-in Firestore: list_documents reads the worker's claims."""
    install()
    sys.path[:0] = [KIT]
    _identity_for(who)
    import services.mcp.server as server
    server._db = lambda: DB
    import uvicorn
    uvicorn.run(server.app, host="127.0.0.1", port=port, log_level="warning")


def gcs_serve(port: int) -> None:
    """The uploads bucket's door for a signed PUT: the object stored as a new generation, then the finalize event the
    bucket's notification would send, handed to the worker - before the PUT is answered."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Door(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_PUT(self):
            bucket, name = self.path.split("?", 1)[0].lstrip("/").split("/", 1)
            data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            ct = self.headers.get("Content-Type", "")
            blob = Bucket(bucket).blob(name)
            blob.upload_from_string(data, ct)
            if bucket == f"{PROJ}-uploads":
                worker(name, str(blob.generation), ct)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
    HTTPServer(("127.0.0.1", port), Door).serve_forever()
