"""Build lesson B.4 from its three parts, the shared template, the Basics laptop setup and verbatim kit excerpts.

Encode with BERT-style models: embeddings and rankers. A Basics page: every cell runs on the learner's laptop before
the kit is cloned (lesson 0.2), so each cell carries its own text and the kit's code is shown as read-only excerpts.

Where the page's numbers come from:
  - the kit: the embedding model, its two task types, its 768 numbers and its region (indexer.py, retriever.py,
    config.py); the ranker's model, location and ranking config (config.py, retriever.py); the pool and the request's
    top_k (config.py, schemas.py); the index's distance (vector.tf); the four handbook clauses every cell scores
    (evals/corpus/acme/hr_policy_2026.md, checked against the kit's chunker); acme's chunk count (the kit's chunker
    over evals/corpus/acme, counted as lesson 2.3 counts it).
  - the offline cells, run here at build time with the Basics interpreter: the masked-word fill, the toy bi-encoder
    and the toy cross-encoder. What they print is the page's expected output, and the asserts pin every claim the
    prose makes about it. The widget's JavaScript port of the two toys is checked against the Python with node, on
    every preset and on more questions.
  - the live cells, the author's runs (RUN_LIST.md): text-embedding-005's cosines, the Ranking API's scores and the
    two side by side, read with pagebuild.recorded(). Until then the page shows marked stand-ins. Here the live cells
    run against stand-ins that check each request (the model, the location, the task types, the REST path, the
    headers, the body); what the stand-ins print is thrown away, never shown.
  - prices and API facts, verified on Google's and the papers' pages on 7 October 2026 (the URLs beside them).
"""
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules imported below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

try:
    import numpy
except ImportError:
    raise SystemExit("build B.4 with the Basics interpreter (Python 3.12, numpy 2.5.3): its offline cells run at build time")
assert numpy.__version__.startswith("2."), numpy.__version__

LESSON = "B.4"
title = ("<title>Lesson B.4 Encode with BERT-style models: embeddings and rankers - two texts read apart, or one pair read "
         "together | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pe-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:10px 16px;margin-bottom:8px;}
.pe-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pe-l select,.pe-l input{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pe-own{display:none;}
.pe-own.on{display:flex;}
.pe-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 8px;overflow-wrap:anywhere;}
.pe-out{display:grid;gap:8px;}
.pe-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;display:grid;gap:4px;min-width:0;}
.pe-id{font-size:var(--small-size);color:var(--navy);}
.pe-bar{display:grid;grid-template-columns:104px minmax(0,1fr) 46px;align-items:center;gap:8px;font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);}
.pe-track{height:12px;background:#e2e8f0;border-radius:6px;overflow:hidden;}
.pe-fill{height:100%;width:0;background:var(--cyan);transition:width .25s;}
.pe-fill.x{background:var(--teal);}
.pe-why{font-size:12.5px;line-height:1.45;color:var(--slate);overflow-wrap:anywhere;}
@media (prefers-reduced-motion: reduce){.pe-fill{transition:none;}}
"""

setup = pb.basics_setup_section()

# ------------------------------------------------------------------ the kit's facts the page states
IDX, RET, CFG, API, SCH, VTF = ("services/ingest/indexer.py", "services/rag-api/retriever.py", "services/rag-api/config.py",
                                "services/rag-api/main.py", "services/rag-api/schemas.py", "terraform/vector.tf")
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (IDX, RET, CFG, API, SCH, VTF)}


def grab(pattern: str, text: str, n: int = 1) -> str:
    m = re.search(pattern, text, re.S)
    assert m, pattern
    return m.group(n)


EMBED_MODEL = grab(r'EMBEDDING_MODEL = os\.environ\.get\("EMBEDDING_MODEL", "([^"]+)"\)', src[IDX])
assert EMBED_MODEL == grab(r'embed_model: str = Field\("([^"]+)", alias="EMBEDDING_MODEL"\)', src[CFG]) == "text-embedding-005"
DOC_TASK = grab(r'EMBEDDING_TASK_TYPE = "([A-Z_]+)"', src[IDX])
DIMS = int(grab(r"EMBEDDING_DIMENSIONS = (\d+)", src[IDX]))
EMBED_LOC = grab(r'_embed = genai\.Client\(\s*enterprise=True,\s*project=os\.environ\["GOOGLE_CLOUD_PROJECT"\],\s*location="([^"]+)"', src[IDX])
QUERY_FN = block(RET, "def embed_query(", end="def _firestore_fallback(")
QUERY_TASK = grab(r'task_type="([A-Z_]+)", output_dimensionality=(\d+)', QUERY_FN)
assert int(grab(r'task_type="[A-Z_]+", output_dimensionality=(\d+)', QUERY_FN)) == DIMS == 768
assert "_genai_client().models.embed_content(" in QUERY_FN and "model=settings.embed_model" in QUERY_FN
assert (DOC_TASK, QUERY_TASK) == ("RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY")
assert EMBED_LOC == grab(r'region: str = "([^"]+)"', src[CFG]) == "us-central1"         # the API's client is regional too
assert "return genai.Client(enterprise=True, project=settings.project_id, location=settings.region)" in src[RET]
RANK_MODEL = grab(r'rerank_model: str = "([^"]+)"', src[CFG])
RANK_LOC, RANK_CFG = re.search(r'ranking_config_path\(\s*project=settings\.project_id, location="([^"]+)",\s*ranking_config="([^"]+)"\)',
                               src[RET]).groups()
assert (RANK_MODEL, RANK_LOC, RANK_CFG) == ("semantic-ranker-fast-004", "global", "default_ranking_config")
POOL = int(grab(r"top_k_retrieve: int = Field\((\d+),", src[CFG]))
TOPK, TOPK_MAX = (int(x) for x in re.search(r"top_k: int = Field\(default=(\d+), ge=1, le=(\d+)\)", src[SCH]).groups())
RECORDS_CUT = int(grab(r"chunks = chunks\[:(\d+)\]", src[RET]))
DISTANCE = grab(r'distance_measure_type\s*=\s*"([A-Z_]+)"', src[VTF])
assert (POOL, TOPK, TOPK_MAX, RECORDS_CUT, DISTANCE) == (20, 5, 20, 200, "DOT_PRODUCT_DISTANCE")
assert "distance_measure=DistanceMeasure.COSINE," in src[RET] and 'd["score"] = 1.0 - d.pop("d", 1.0)' in src[RET]
assert 'records = [discoveryengine.RankingRecord(id=str(i), content=c["text"])' in src[RET]   # the ranker gets text, not vectors
assert 'chunks[int(r.id)]["rerank_score"] = r.score' in src[RET] and "return _by_retrieval_score(chunks, k)" in src[RET]
assert "chunks = rerank(req.query, chunks, req.top_k, tenant_id=req.tenant_id)" in src[API]
assert '"roles/discoveryengine.viewer",' in (KIT / "terraform/sa.tf").read_text(encoding="utf-8")
assert "discoveryengine.googleapis.com" in (KIT / "commands/lesson-12.1.sh").read_text(encoding="utf-8")

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "handler": ("services/rag-api/main.py - /v1/query: the question embedded once and the pool retrieved, then the pool reranked",
                block(API, '    with stage(stages, "retrieve"):', n=4) + "\n...\n" + block(API, '        with stage(stages, "rerank"):', n=2)),
    "idx_consts": ("services/ingest/indexer.py - the document side: one model, the document task type, 768 numbers, a regional client",
                   block(IDX, 'EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL"', n=10)),
    "idx_embed_all": ("services/ingest/indexer.py - embed_all(): every chunk of a document, once, at ingest",
                      block(IDX, "def embed_all(", end="def valid_vector(")),
    "embed_query": ("services/rag-api/retriever.py - embed_query(): the question side, at query time", QUERY_FN),
    "vector_tf": ("terraform/vector.tf - the index compares the two by dot product", block(VTF, "    config {", n=4)),
    "fs_cosine": ("services/rag-api/retriever.py - _firestore_fallback(): the same comparison as a cosine distance, flipped into a score",
                  block(RET, "    hits = (query", n=13)),
    "rerank_fn": ("services/rag-api/retriever.py - rerank(): the question and each candidate's text, not its vector, to the Ranking API",
                  block(RET, "def rerank(query: str")),
    "rerank_cfg": ("services/rag-api/config.py - the ranker's model and the pool's width",
                   block(CFG, '    rerank_model: str = "semantic-ranker-fast-004"', n=1) + "\n...\n"
                   + block(CFG, "    top_k_retrieve: int = Field(20", n=1)),
}
assert EXCERPTS["handler"][1].rstrip().endswith("chunks = rerank(req.query, chunks, req.top_k, tenant_id=req.tenant_id)")
assert "qvec = embed_query(req.query)" in EXCERPTS["handler"][1]
assert EXCERPTS["idx_consts"][1].rstrip().endswith(")") and 'location="us-central1",' in EXCERPTS["idx_consts"][1]
assert EXCERPTS["idx_embed_all"][1].rstrip().endswith("return out") and '"task_type": EMBEDDING_TASK_TYPE' in EXCERPTS["idx_embed_all"][1]
assert EXCERPTS["vector_tf"][1].rstrip().endswith('distance_measure_type       = "DOT_PRODUCT_DISTANCE"')
assert EXCERPTS["fs_cosine"][1].rstrip().endswith('d.pop("embedding", None)          # never ship 768 floats to the model')
assert 'd["score"] = 1.0 - d.pop("d", 1.0)' in EXCERPTS["fs_cosine"][1]
assert EXCERPTS["rerank_fn"][1].rstrip().endswith("return out") and "model=settings.rerank_model," in EXCERPTS["rerank_fn"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the four clauses every cell scores, from the kit's handbook
HANDBOOK = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
CODES = ("NP-03", "PB-02", "LV-01", "LV-07")
HEAD, CLAUSES = {}, {}
for code in CODES:
    m = re.search(r"^## " + re.escape(code) + r" \u2014 (.+?)\n\n(.+?)(?:\n\n|\Z)", HANDBOOK, re.M | re.S)
    HEAD[code], CLAUSES[code] = m.group(1).strip(), " ".join(m.group(2).split())
    assert CLAUSES[code].isascii() and '"' not in CLAUSES[code] and "\\" not in CLAUSES[code], code
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402

CUT = {c["locator"]: c["text"] for c in dc.chunk_document(
    {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x/acme/hr_policy_2026.md", "text": HANDBOOK}, "acme")}
for code in CODES:                                  # the clause is the chunk the kit embeds, less its heading line
    first, rest = CUT[code].split("\n", 1)
    assert first == f"{code} \u2014 {HEAD[code]}" and " ".join(rest.split()) == CLAUSES[code], code
N_CHUNKS = N_CHARS = 0                              # acme's chunks, counted as lesson 2.3 counts them
for p in sorted((KIT / "evals/corpus/acme").glob("*.md")):
    for c in dc.chunk_document({"slug": p.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{p.name}",
                                "text": p.read_text(encoding="utf-8")}, "acme"):
        N_CHUNKS, N_CHARS = N_CHUNKS + 1, N_CHARS + len(c["text"])
assert N_CHUNKS > POOL, N_CHUNKS

QUESTION = "Can I use my unused leave to shorten my notice period?"
REORDERED = "Can my notice period be used to shorten my unused leave?"      # the same words, the other way round
PAID = "Is earned leave paid out when I resign?"
OTHER = "Will my holidays cut my notice short?"
SAME, SWAPPED = "Leave cannot be used to shorten notice.", "Notice cannot be used to shorten leave."
assert "Leave cannot be" in CLAUSES["LV-07"] and CLAUSES["LV-07"].endswith("cannot be used to shorten notice.")


def py_str(text: str, indent: int, width: int = 86) -> str:
    """A long string as adjacent literals split at spaces, each at most about `width` characters."""
    parts, cur = [], ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > width:
            parts.append(cur + " ")
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    parts.append(cur)
    assert "".join(parts) == text
    lits = ['"' + p + '"' for p in parts]
    return lits[0] if len(lits) == 1 else "(" + ("\n" + " " * (indent + 1)).join(lits) + ")"


CLAUSES_PY = "\n".join(["CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md"]
                       + [f'    "{c}": ' + py_str(CLAUSES[c], len(f'    "{c}": ')) + "," for c in CODES] + ["}"])
_ns = {}
exec(CLAUSES_PY, _ns)
assert _ns["CLAUSES"] == CLAUSES

# ------------------------------------------------------------------ the cells: offline ones run here, live ones wait for the author
WARN = 'warnings.filterwarnings("ignore", category=UserWarning)\n'

MLM_PY = r'''import re, warnings
''' + WARN + r'''from collections import Counter
__CLAUSES__
def sentences(text):
    return [s for s in re.sub(r"([.;?!])\s+", r"\1\n", text).split("\n") if s]
def words(sentence):
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", sentence.lower())
def fill(clause, n, hidden):
    text = {(c, k): words(s) for c, t in CLAUSES.items() for k, s in enumerate(sentences(t), 1)}
    toks = text[(clause, n)]
    j = toks.index(hidden)
    toks[j] = "[mask]"                     # the training text has a blank here, so the hidden word itself is never counted
    left, right = toks[j - 1], toks[j + 1]
    after_left = Counter(t[k + 1] for t in text.values() for k in range(len(t) - 1) if t[k] == left and t[k + 1] != "[mask]")
    before_right = Counter(t[k] for t in text.values() for k in range(len(t) - 1) if t[k + 1] == right and t[k] != "[mask]")
    return " ".join(toks).replace("[mask]", "[MASK]"), left, right, after_left, after_left + before_right
def verdict(counts, hidden):
    if not counts:
        return "nothing in the text fits"
    top = [w for w, n in counts.items() if n == max(counts.values())]
    if len(top) > 1:
        return "a tie: " + ", ".join(top) + ("" if hidden in top else "; the hidden word is not among them")
    return top[0] + (", the hidden word" if top[0] == hidden else ", not the hidden word")
n_sentences = sum(len(sentences(t)) for t in CLAUSES.values())
n_words = sum(len(words(s)) for t in CLAUSES.values() for s in sentences(t))
print(f"the text: {len(CLAUSES)} clauses, {n_sentences} sentences, {n_words} words")
for clause, n, hidden in (("NP-03", 1, "notice"), ("PB-02", 2, "15"), ("NP-03", 3, "leave")):
    shown, left, right, one, both = fill(clause, n, hidden)
    print(f"\n{clause}, sentence {n}: {shown}")
    print(f"  left only   ({left} _): " + ", ".join(f"{w} {c}" for w, c in one.most_common()) + f"  -> {verdict(one, hidden)}")
    print(f"  both sides  ({left} _ {right}): " + ", ".join(f"{w} {c}" for w, c in both.most_common()) + f"  -> {verdict(both, hidden)}")'''

DEFS_BI = r'''VOCAB = {   # every word the toy knows points along one named axis, with a weight; all other words are ignored
    "leave": {"leave": 1.0, "earned": 0.8, "unused": 0.6, "accrues": 0.6, "lapses": 0.5, "holidays": 0.9},
    "exit": {"notice": 1.0, "resignation": 0.9, "resign": 0.9, "exit": 0.9, "quit": 0.9, "period": 0.6},
    "pay": {"pay": 1.0, "paid": 1.0, "encashed": 1.0, "basic": 0.5},
    "probation": {"probation": 1.0, "joiners": 0.8, "extended": 0.4},
    "reduce": {"shorten": 1.0, "cut": 1.0, "set": 0.8, "off": 0.4},
}
AXES = list(VOCAB)
WORDS = {w: (AXES.index(axis), weight) for axis, ws in VOCAB.items() for w, weight in ws.items()}
def known(text):
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w in WORDS]
def encode(text):                          # the bi-encoder: one text in, one vector out, no other text seen
    v = np.zeros(len(AXES))
    for w in known(text):
        axis, weight = WORDS[w]
        v[axis] += weight                  # pooling: add up the words' vectors...
    return v / np.linalg.norm(v)           # ...and scale the sum to length 1'''

DEFS_CROSS = r'''def sentences(text):
    return [s for s in re.sub(r"([.;?!])\s+", r"\1\n", text).split("\n") if s]
def ideas(text):                           # the axes of the words it knows, in order, repeats merged
    out = []
    for w in known(text):
        axis = AXES[WORDS[w][0]]
        if not out or out[-1] != axis:
            out.append(axis)
    return out
def aligned(q, s):                         # how many of q's ideas s holds in the same order, gaps allowed
    m = [[0] * (len(s) + 1) for _ in range(len(q) + 1)]
    for i in range(len(q)):
        for j in range(len(s)):
            m[i + 1][j + 1] = m[i][j] + 1 if q[i] == s[j] else max(m[i][j + 1], m[i + 1][j])
    return m[-1][-1]
def cross(question, passage):              # the cross-encoder: the pair in, one score out
    q = ideas(question)
    best = max(sentences(passage), key=lambda s: aligned(q, ideas(s)))
    return aligned(q, ideas(best)) / len(q), best'''

TOY_HEAD = "import re, warnings\n" + WARN + "import numpy as np\n__CLAUSES__\n"

BI_PY = TOY_HEAD + DEFS_BI + "\n" + r'''D = np.array([encode(text) for text in CLAUSES.values()])     # at ingest: once per clause, then stored
QUESTION = "__QUESTION__"
q = encode(QUESTION)                                          # at query time: once per question
show = lambda v: "[" + ", ".join(f"{a} {x:.3f}" for a, x in zip(AXES, v)) + "]"
print(f"the toy: {len(WORDS)} words on {len(AXES)} axes; the store: {D.shape[0]} clause vectors of {D.shape[1]} numbers")
for name, v in zip(CLAUSES, D):
    print(f"  {name}  {show(v)}")
print(f"the question: {QUESTION}")
print(f"  words it knows: {', '.join(known(QUESTION))}")
print(f"  its vector: {show(q)}")
print("the cosine with each stored vector, highest first (for vectors of length 1 the dot product is the cosine):")
for name, score in sorted(zip(CLAUSES, D @ q), key=lambda p: -p[1]):
    print(f"  {name}  {score:.3f}")
OTHER = "__OTHER__"
print(f"the same question in other words: {OTHER}")
print("  " + "   ".join(f"{name} {score:.3f}" for name, score in sorted(zip(CLAUSES, D @ encode(OTHER)), key=lambda p: -p[1])))'''

CROSS_PY = TOY_HEAD + DEFS_BI + "\n" + DEFS_CROSS + "\n" + r'''QUESTION = "__QUESTION__"
q = encode(QUESTION)
print(f"the question's ideas, in order: {' > '.join(ideas(QUESTION))}")
print(f"{'clause':8}{'bi-encoder':>12}{'cross-encoder':>15}")
for name, text in sorted(CLAUSES.items(), key=lambda p: -(encode(p[1]) @ q)):
    score, best = cross(QUESTION, text)
    print(f"{name:8}{encode(text) @ q:12.3f}{score:15.2f}")
    print(f"{'':8}lined up best: {best}")
SAME, SWAPPED = "__SAME__", "__SWAPPED__"
print("the same words, swapped:")
for text in (SAME, SWAPPED):
    print(f"  {text:41}{encode(text) @ q:7.3f}{cross(QUESTION, text)[0]:15.2f}")
print("the two vectors are identical:", bool(np.array_equal(encode(SAME), encode(SWAPPED))))'''

BI_LIVE = r'''import os, json, warnings
''' + WARN + r'''import numpy as np
from google import genai
PROJECT = os.environ["PROJECT"]
QUESTION = "__QUESTION__"
__CLAUSES__
client = genai.Client(enterprise=True, project=PROJECT, location="__ELOC__")   # embeddings are regional, as in the kit
def embed(texts, task):
    r = client.models.embed_content(model="__EMODEL__", contents=texts,
                                    config={"output_dimensionality": __DIMS__, "task_type": task})
    return np.array([e.values for e in r.embeddings])
D = embed(list(CLAUSES.values()), "__DOC__")      # the worker's side: every chunk, once, at ingest
q = embed([QUESTION], "__QRY__")[0]                  # the API's side: once per question
D = D / np.linalg.norm(D, axis=1, keepdims=True)             # length 1, so the dot product below is the cosine
q = q / np.linalg.norm(q)
scores = D @ q
print(f"__EMODEL__ on __ELOC__: {len(D)} clause vectors (__DOC__) and 1 question vector (__QRY__), {D.shape[1]} numbers each")
print("the cosine of the question with each clause, highest first:")
for name, s in sorted(zip(CLAUSES, scores), key=lambda p: -p[1]):
    print(f"  {name}  cosine {s:.4f}")
json.dump({name: float(s) for name, s in zip(CLAUSES, scores)}, open(os.path.expanduser("~/b4_bi.json"), "w"))
print("saved ~/b4_bi.json for the comparison")'''

CROSS_LIVE = r'''import os, json, warnings
''' + WARN + r'''import google.auth, httpx
from google.auth.transport.requests import Request
PROJECT = os.environ["PROJECT"]
QUESTION = "__QUESTION__"
__CLAUSES__
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(Request())                                   # an access token from your Application Default Credentials
url = (f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT}/locations/__RLOC__/"
       "rankingConfigs/__RCFG__:rank")       # the kit's ranking_config_path(), as a REST path
body = {"model": "__RMODEL__", "query": QUESTION,
        "records": [{"id": name, "content": text} for name, text in CLAUSES.items()],
        "topN": len(CLAUSES), "ignoreRecordDetailsInResponse": True}
r = httpx.post(url, json=body, timeout=30,
               headers={"Authorization": f"Bearer {creds.token}", "X-Goog-User-Project": PROJECT})
if r.status_code != 200:
    raise SystemExit(f"HTTP {r.status_code}: {r.text[:500]}")
records = r.json()["records"]                              # highest score first
print(f"__RMODEL__ on __RLOC__: {len(records)} records scored, highest first")
for rec in records:
    print(f"  {rec['id']}  score {rec.get('score', 0.0):.4f}")
json.dump({rec["id"]: rec.get("score", 0.0) for rec in records}, open(os.path.expanduser("~/b4_cross.json"), "w"))
print("saved ~/b4_cross.json for the comparison")'''

COMPARE_PY = r'''import json, os, warnings
''' + WARN + r'''from itertools import combinations
bi = json.load(open(os.path.expanduser("~/b4_bi.json")))           # the first cell: the cosines
cross = json.load(open(os.path.expanduser("~/b4_cross.json")))     # the second: the ranker's scores
by_bi = sorted(bi, key=lambda n: -bi[n])
by_cross = sorted(cross, key=lambda n: -cross[n])
print(f"{'clause':8}{'bi-encoder cosine':>19}{'rank':>6}{'cross-encoder score':>21}{'rank':>6}")
for n in by_bi:
    print(f"{n:8}{bi[n]:19.4f}{by_bi.index(n) + 1:6}{cross[n]:21.4f}{by_cross.index(n) + 1:6}")
pairs = list(combinations(by_bi, 2))
same = sum((bi[a] - bi[b]) * (cross[a] - cross[b]) > 0 for a, b in pairs)
print(f"first choice: bi-encoder {by_bi[0]}, cross-encoder {by_cross[0]}")
print(f"pairs of clauses the two put in the same order: {same} of {len(pairs)}")
print(f"spread, highest minus lowest: bi-encoder {bi[by_bi[0]] - bi[by_bi[-1]]:.4f}, "
      f"cross-encoder {cross[by_cross[0]] - cross[by_cross[-1]]:.4f}")'''

SUBS = {"__CLAUSES__": CLAUSES_PY, "__QUESTION__": QUESTION, "__OTHER__": OTHER, "__SAME__": SAME, "__SWAPPED__": SWAPPED,
        "__ELOC__": EMBED_LOC, "__EMODEL__": EMBED_MODEL, "__DIMS__": str(DIMS), "__DOC__": DOC_TASK, "__QRY__": QUERY_TASK,
        "__RLOC__": RANK_LOC, "__RCFG__": RANK_CFG, "__RMODEL__": RANK_MODEL}


def cell(body: str) -> str:
    for k, v in SUBS.items():
        body = body.replace(k, v)
    assert not re.findall(r"__[A-Z]+__", body), re.findall(r"__[A-Z]+__", body)
    assert body.isascii()
    compile(body, "cell", "exec")
    return body


CELLS = {"mlm": cell(MLM_PY), "bi": cell(BI_PY), "cross": cell(CROSS_PY),
         "bi_live": cell(BI_LIVE), "cross_live": cell(CROSS_LIVE), "compare": cell(COMPARE_PY)}

T = Path(tempfile.mkdtemp(prefix="lessonB4-"))     # every cell's home: the live cells' files land here, never in yours
ENV = {k: v for k, v in os.environ.items() if not k.startswith(("GOOGLE_", "CLOUDSDK_"))}
ENV.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(T), "USERPROFILE": str(T),
            "APPDATA": str(T), "LOCALAPPDATA": str(T), "CLOUDSDK_CONFIG": str(T / "gcloud"), "PROJECT": "documind-ai-YOUR-ID"})


def run_cell(body: str, prelude: str = "") -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(T), capture_output=True, text=True,
                       encoding="utf-8", env=ENV)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


OUT = {k: run_cell(CELLS[k]) for k in ("mlm", "bi", "cross")}

# the toys again, in this process, for the numbers in the prose and for the widget's check
TOY = {}
exec("import re\nimport numpy as np\n" + CLAUSES_PY + "\n" + DEFS_BI + "\n" + DEFS_CROSS, TOY)
encode, cross, ideas, known = TOY["encode"], TOY["cross"], TOY["ideas"], TOY["known"]
q_vec = encode(QUESTION)
BI = {c: float(encode(CLAUSES[c]) @ q_vec) for c in CODES}
XS = {c: cross(QUESTION, CLAUSES[c])[0] for c in CODES}

# ---- step 3: the masked words
MLM = OUT["mlm"]
N_SENT = sum(len(TOY["sentences"](t)) for t in CLAUSES.values())
N_MLM_WORDS = sum(len(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", s.lower())) for t in CLAUSES.values() for s in TOY["sentences"](t))
assert MLM.startswith(f"the text: 4 clauses, {N_SENT} sentences, {N_MLM_WORDS} words\n"), MLM
assert "NP-03, sentence 1: a confirmed employee at grade e3 or above serves a [MASK] period of 60 days\n" in MLM, MLM
assert "  left only   (a _): confirmed 1, maximum 1  -> a tie: confirmed, maximum; the hidden word is not among them\n" in MLM, MLM
assert "  both sides  (a _ period): notice 2, confirmed 1, maximum 1  -> notice, the hidden word\n" in MLM, MLM
assert "PB-02, sentence 2: during probation the notice period is [MASK] days for either side\n" in MLM, MLM
assert ("  both sides  (is _ days): acknowledged 1, encashed 1, 60 1, 1.75 1, 30 1, 45 1  -> a tie: acknowledged, encashed, "
        "60, 1.75, 30, 45; the hidden word is not among them\n") in MLM, MLM
assert "  left only   (earned _): leave 2  -> leave, the hidden word\n" in MLM, MLM
assert "  both sides  (earned _ may): leave 2, probation 1, days 1  -> leave, the hidden word" in MLM, MLM

# ---- step 4: the toy bi-encoder
BO = OUT["bi"]
ORDER = sorted(CODES, key=lambda c: -BI[c])
assert ORDER == ["NP-03", "LV-07", "LV-01", "PB-02"], BI
assert f"the toy: {len(TOY['WORDS'])} words on 5 axes; the store: 4 clause vectors of 5 numbers\n" in BO and len(TOY["WORDS"]) == 23, BO
assert "  words it knows: unused, leave, shorten, notice, period\n" in BO, BO
assert "  its vector: [leave 0.647, exit 0.647, pay 0.000, probation 0.000, reduce 0.404]\n" in BO, BO
assert "  LV-01  [leave 1.000, exit 0.000, pay 0.000, probation 0.000, reduce 0.000]\n" in BO, BO
for c in CODES:
    assert f"  {c}  {BI[c]:.3f}\n" in BO, (c, BO)
OTHER_ORDER = sorted(CODES, key=lambda c: -float(encode(CLAUSES[c]) @ encode(OTHER)))
assert OTHER_ORDER == ORDER and known(OTHER) == ["holidays", "cut", "notice"], (OTHER_ORDER, known(OTHER))
CLAUSE_WORDS = set(re.findall(r"[a-z]+", " ".join(CLAUSES.values()).lower()))
assert set(re.findall(r"[a-z]+", OTHER.lower())) & CLAUSE_WORDS == {"notice"}       # the paraphrase shares one word
VEC = {c: encode(CLAUSES[c]) for c in CODES}
AX = TOY["AXES"]
assert AX[int(VEC["NP-03"].argmax())] == "exit" and AX[int(VEC["PB-02"].argmax())] == "probation" and all(VEC["LV-07"] > 0), VEC
BI_GAP = round(BI["LV-07"], 3) - round(BI["LV-01"], 3)
assert 0 < BI_GAP < 0.05 and BI["NP-03"] - BI["LV-07"] > 0.2, BI           # an answer barely above a topic, as the prose says

# ---- step 5: the toy cross-encoder
CO = OUT["cross"]
assert XS == {"NP-03": 1.0, "LV-07": 1.0, "LV-01": 1 / 3, "PB-02": 1 / 3}, XS
assert ideas(QUESTION) == ["leave", "reduce", "exit"] and "the question's ideas, in order: leave > reduce > exit\n" in CO, CO
for c in CODES:
    assert f"{c:8}{BI[c]:12.3f}{XS[c]:15.2f}\n" in CO, (c, CO)
assert f"{'':8}lined up best: Unused earned leave may not be set off against the notice period.\n" in CO, CO
assert f"{'':8}lined up best: Leave cannot be encashed during probation and cannot be used to shorten notice.\n" in CO, CO
B_SAME, B_SWAP = float(encode(SAME) @ q_vec), float(encode(SWAPPED) @ q_vec)
assert B_SAME == B_SWAP and cross(QUESTION, SAME)[0] == 1.0 and cross(QUESTION, SWAPPED)[0] == 1 / 3
assert f"  {SAME:41}{B_SAME:7.3f}{1.0:15.2f}\n" in CO and f"  {SWAPPED:41}{B_SWAP:7.3f}{1 / 3:15.2f}\n" in CO, CO
assert CO.rstrip().endswith("the two vectors are identical: True"), CO
assert numpy.array_equal(encode(REORDERED), q_vec) and ideas(REORDERED) == ["exit", "reduce", "leave"]   # the widget's second preset
assert cross(REORDERED, SWAPPED)[0] == 1.0 and cross(REORDERED, SAME)[0] == 1 / 3

# ---- step 7: the live cells, against stand-ins that check every request (their output is discarded)
STUB_GENAI = r'''import sys, types, hashlib, atexit
import google
_calls = []
def _vector(text):
    out, i = [], 0
    while len(out) < __DIMS__:
        out += [b / 255 - 0.5 for b in hashlib.sha256(f"{i}|{text}".encode()).digest()]
        i += 1
    return out[:__DIMS__]
class _Models:
    def embed_content(self, model, contents, config):
        assert model == "__EMODEL__" and set(config) == {"output_dimensionality", "task_type"}, (model, config)
        assert config["output_dimensionality"] == __DIMS__ and config["task_type"] in ("__DOC__", "__QRY__"), config
        _calls.append((config["task_type"], len(contents)))
        return types.SimpleNamespace(embeddings=[types.SimpleNamespace(values=_vector(config["task_type"] + t)) for t in contents])
class _Client:
    def __init__(self, **kw):
        assert kw == {"enterprise": True, "project": "documind-ai-YOUR-ID", "location": "__ELOC__"}, kw
        self.models = _Models()
_genai = types.ModuleType("google.genai")
_genai.Client = _Client
sys.modules["google.genai"] = _genai
google.genai = _genai
atexit.register(lambda: print("STUB", sorted(_calls)))
'''
STUB_RANK = r'''import sys, types, hashlib, atexit, json as _json
import google
class _Request:
    pass
class _Creds:
    token = None
    def refresh(self, request):
        assert isinstance(request, _Request)
        self.token = "stub-token"
def _default(scopes=None):
    assert scopes == ["https://www.googleapis.com/auth/cloud-platform"], scopes
    return _Creds(), "documind-ai-YOUR-ID"
_auth, _tr, _req = (types.ModuleType(n) for n in ("google.auth", "google.auth.transport", "google.auth.transport.requests"))
_auth.default, _req.Request, _auth.transport, _tr.requests = _default, _Request, _tr, _req
sys.modules.update({"google.auth": _auth, "google.auth.transport": _tr, "google.auth.transport.requests": _req})
google.auth = _auth
_sent = []
class _Response:
    def __init__(self, body):
        self.status_code, self._body, self.text = 200, body, _json.dumps(body)
    def json(self):
        return self._body
def _post(url, json=None, headers=None, timeout=None):
    assert url == "https://discoveryengine.googleapis.com/v1/projects/documind-ai-YOUR-ID/locations/__RLOC__/rankingConfigs/__RCFG__:rank", url
    assert headers == {"Authorization": "Bearer stub-token", "X-Goog-User-Project": "documind-ai-YOUR-ID"}, headers
    assert set(json) == {"model", "query", "records", "topN", "ignoreRecordDetailsInResponse"}, json
    assert json["model"] == "__RMODEL__" and json["ignoreRecordDetailsInResponse"] is True and json["topN"] == len(json["records"]), json
    assert all(set(r) == {"id", "content"} for r in json["records"]) and timeout, json
    _sent.append(json)
    scored = [{"id": r["id"], "score": int(hashlib.sha256(r["content"].encode()).hexdigest()[:6], 16) / 16 ** 6} for r in json["records"]]
    return _Response({"records": sorted(scored, key=lambda r: -r["score"])})
_httpx = types.ModuleType("httpx")
_httpx.post = _post
sys.modules["httpx"] = _httpx
atexit.register(lambda: print("STUB", len(_sent), [r["id"] for r in _sent[0]["records"]] if _sent else None, _sent[0]["query"] if _sent else None))
'''


def parse_scores(text: str, word: str) -> dict:
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^  (" + "|".join(CODES) + r")  " + word + r" (-?\d+\.\d{4})$", text, re.M)}


def parse_compare(text: str) -> dict:
    rows = re.findall(r"^(" + "|".join(CODES) + r") +(-?\d+\.\d{4}) +(\d) +(-?\d+\.\d{4}) +(\d)$", text, re.M)
    return {r[0]: (float(r[1]), int(r[2]), float(r[3]), int(r[4])) for r in rows}


stub_bi = run_cell(CELLS["bi_live"], cell(STUB_GENAI))
assert stub_bi.rstrip().endswith(f"STUB [('{DOC_TASK}', 4), ('{QUERY_TASK}', 1)]"), stub_bi
assert stub_bi.startswith(f"{EMBED_MODEL} on {EMBED_LOC}: 4 clause vectors ({DOC_TASK}) and 1 question vector ({QUERY_TASK}), {DIMS} numbers each\n")
stub_x = run_cell(CELLS["cross_live"], cell(STUB_RANK))
assert stub_x.rstrip().endswith(f"STUB 1 {list(CODES)} {QUESTION}"), stub_x
assert stub_x.startswith(f"{RANK_MODEL} on {RANK_LOC}: 4 records scored, highest first\n"), stub_x
stub_c = run_cell(CELLS["compare"])
sb, sx, sc = parse_scores(stub_bi, "cosine"), parse_scores(stub_x, "score"), parse_compare(stub_c)
assert set(sb) == set(sx) == set(sc) == set(CODES), (sb, sx, sc)
assert all(abs(sc[c][0] - sb[c]) < 6e-5 and abs(sc[c][2] - sx[c]) < 6e-5 for c in CODES), (sb, sx, sc)
assert re.search(r"^pairs of clauses the two put in the same order: \d of 6$", stub_c, re.M), stub_c
del stub_bi, stub_x, stub_c, sb, sx, sc                    # stand-ins' numbers: checked, never shown
shutil.rmtree(T, ignore_errors=True)

# the author's runs, once recorded: the three files must agree with one another
LIVE = {name: pb.recorded(LESSON, name) for name in ("bi_encoder.txt", "cross_encoder.txt", "compare.txt")}
got = {name: text for name, text in LIVE.items() if pb.data(LESSON, name).exists()}
if "bi_encoder.txt" in got:
    assert set(parse_scores(got["bi_encoder.txt"], "cosine")) == set(CODES), "data/bi_encoder.txt: not the first cell's output"
if "cross_encoder.txt" in got:
    assert set(parse_scores(got["cross_encoder.txt"], "score")) == set(CODES), "data/cross_encoder.txt: not the second cell's output"
if len(got) == 3:
    rb, rx, rc = (parse_scores(got["bi_encoder.txt"], "cosine"), parse_scores(got["cross_encoder.txt"], "score"),
                  parse_compare(got["compare.txt"]))
    assert set(rc) == set(CODES) and all(rc[c][0] == rb[c] and rc[c][2] == rx[c] for c in CODES), \
        "data/compare.txt does not match the other two files: record all three from one run"

# ------------------------------------------------------------------ prices, from Google's pages (checked 7 October 2026)
# https://cloud.google.com/vertex-ai/generative-ai/pricing - "Embeddings for Text (Excluding Gemini Embedding)", input,
#   online requests: $0.000025 per 1,000 (characters, as lesson 1.3 reads it); output: no charge.
# https://cloud.google.com/generative-ai-app-builder/pricing - "Ranking API pricing": Ranking $1.00 / 1,000 count; "A query is
#   defined as having up to 100 documents" (132 documents to rank = 2 queries, 401 = 5).
# https://docs.cloud.google.com/generative-ai-app-builder/docs/ranking (last updated 2026-10-05) - the rank method's REST path
#   and body (model, query, records with id and content, topN, ignoreRecordDetailsInResponse), the X-Goog-User-Project header
#   in Google's own example, scores from 0 to 1 highest first, up to 1000 records per request, 1024 tokens a record for 004,
#   semantic-ranker-default-004 the default and fast-004 the fast one, 005 versions released 1 September 2026.
# https://docs.cloud.google.com/docs/quotas/set-quota-project - user credentials name a quota project; the
#   x-goog-user-project header sets it per request.
# https://cloud.google.com/blog/products/ai-machine-learning/launching-our-new-state-of-the-art-vertex-ai-ranking-api (31 May
#   2025) - default-004 "our most accurate model", fast-004 "our fastest model for latency-critical use cases"; no price.
EMBED_USD_1K_CHARS, RANK_USD_1K_QUERIES, RECORDS_PER_QUERY, RECORDS_PER_REQUEST, USD_INR = 0.000025, 1.00, 100, 1000, 85
LIVE_CHARS = len(QUESTION) + sum(len(t) for t in CLAUSES.values())
EMBED_INR = LIVE_CHARS / 1000 * EMBED_USD_1K_CHARS * USD_INR
RANK_INR = math.ceil(len(CODES) / RECORDS_PER_QUERY) * RANK_USD_1K_QUERIES / 1000 * USD_INR
Q_EMBED_INR = len(QUESTION) / 1000 * EMBED_USD_1K_CHARS * USD_INR
CORPUS_EMBED_INR = N_CHARS / 1000 * EMBED_USD_1K_CHARS * USD_INR
CORPUS_QUERIES = math.ceil(N_CHUNKS / RECORDS_PER_QUERY)
CORPUS_REQUESTS = math.ceil(N_CHUNKS / RECORDS_PER_REQUEST)
CORPUS_RANK_INR = CORPUS_QUERIES * RANK_USD_1K_QUERIES / 1000 * USD_INR
POOL_RANK_INR = math.ceil(POOL / RECORDS_PER_QUERY) * RANK_USD_1K_QUERIES / 1000 * USD_INR
assert (math.ceil(132 / 100), math.ceil(401 / 100)) == (2, 5)            # the pricing page's own examples
assert POOL_RANK_INR == RANK_INR and EMBED_INR < 0.01 < RANK_INR       # "one query" for the pool and for the four clauses, as the page says
# Sentence-BERT (Reimers and Gurevych, 2019), https://arxiv.org/abs/1908.10084: the most similar pair in 10,000 sentences
# is about 50 million inference computations (~65 hours) with BERT, about 5 seconds with SBERT.
SBERT_PAIRS = 10_000 * 9_999 // 2
# BERT (Devlin et al., NAACL 2019), https://aclanthology.org/N19-1423.pdf: 15% of WordPiece tokens masked (80% [MASK], 10% a
# random token, 10% unchanged), a 30,000-token vocabulary, BERT-base L=12, H=768, A=12, 110M parameters; BooksCorpus
# (800M words) and English Wikipedia (2,500M words); bidirectional self-attention, where GPT's attends only to the left.

# ------------------------------------------------------------------ the widget: the two toys in JavaScript, checked against the Python
PASSAGES = [[c, HEAD[c], CLAUSES[c]] for c in CODES] + [["LV-07, cut", "its last clause alone", SAME],
                                                        ["swapped", "the same words, the other way round", SWAPPED]]
PRESETS = [QUESTION, REORDERED, PAID]
DATA = {"axes": TOY["AXES"], "words": {w: [a, wt] for w, (a, wt) in TOY["WORDS"].items()}, "passages": PASSAGES, "presets": PRESETS}
CORE_JS = r"""function known(t){ var m = String(t).toLowerCase().match(/[a-z]+/g) || []; return m.filter(function(w){ return Object.prototype.hasOwnProperty.call(D.words, w); }); }
function encode(t){ var v = D.axes.map(function(){ return 0; }), n = 0, i;
  known(t).forEach(function(w){ v[D.words[w][0]] += D.words[w][1]; });
  for (i = 0; i < v.length; i++) { n += v[i] * v[i]; }
  n = Math.sqrt(n); return n ? v.map(function(x){ return x / n; }) : null; }
function dot(a, b){ var s = 0, i; for (i = 0; i < a.length; i++) { s += a[i] * b[i]; } return s; }
function sentences(t){ return String(t).replace(/([.;?!])\s+/g, '$1\n').split('\n').filter(function(s){ return s; }); }
function ideas(t){ var out = []; known(t).forEach(function(w){ var a = D.axes[D.words[w][0]]; if (!out.length || out[out.length - 1] !== a) { out.push(a); } }); return out; }
function aligned(q, s){ var m = [], i, j;
  for (i = 0; i <= q.length; i++) { m.push([]); for (j = 0; j <= s.length; j++) { m[i].push(0); } }
  for (i = 0; i < q.length; i++) { for (j = 0; j < s.length; j++) { m[i + 1][j + 1] = q[i] === s[j] ? m[i][j] + 1 : Math.max(m[i][j + 1], m[i + 1][j]); } }
  return m[q.length][s.length]; }
function cross(question, passage){ var q = ideas(question), best = null, bestN = -1;
  sentences(passage).forEach(function(s){ var n = aligned(q, ideas(s)); if (n > bestN) { bestN = n; best = s; } });
  return q.length ? [bestN / q.length, best] : [null, null]; }
"""
UI_JS = r"""var root = document.getElementById('pairs'); if (!root) { return; }
var sel = document.getElementById('pe-q'), own = document.getElementById('pe-own'), ownL = document.getElementById('pe-own-l'),
    sum = document.getElementById('pe-sum'), out = document.getElementById('pe-out');
var STORE = D.passages.map(function(p){ return encode(p[2]); });   /* every passage encoded once, before any question */
function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
function bar(kind, value, digits, cls){ var row = el('div', 'pe-bar'), track = el('div', 'pe-track'), fillEl = el('div', 'pe-fill' + (cls ? ' ' + cls : ''));
  fillEl.style.width = (value === null ? 0 : Math.max(0, Math.min(1, value)) * 100).toFixed(1) + '%';
  track.appendChild(fillEl); row.appendChild(el('span', '', kind)); row.appendChild(track); row.appendChild(el('span', '', value === null ? '-' : value.toFixed(digits))); return row; }
function render(){
  var useOwn = sel.value === 'own', q = useOwn ? own.value : D.presets[Number(sel.value)], v = encode(q);
  ownL.className = 'pe-l pe-own' + (useOwn ? ' on' : '');
  out.textContent = '';
  if (!v) { sum.textContent = String(q).trim() ? 'none of these words is among the toy\'s ' + Object.keys(D.words).length + ': try leave, notice, shorten, paid, probation or quit'
                                           : 'type a question: the toy knows ' + Object.keys(D.words).length + ' words, among them leave, notice, shorten, paid, probation and quit'; return; }
  sum.textContent = 'words it knows: ' + known(q).join(', ') + ' | vector: ' + D.axes.map(function(a, i){ return a + ' ' + v[i].toFixed(3); }).join(', ') + ' | ideas in order: ' + ideas(q).join(' > ');
  D.passages.forEach(function(p, k){
    var c = cross(q, p[2]), row = el('div', 'pe-row'), head = el('div', 'pe-id');
    head.appendChild(el('b', '', p[0])); head.appendChild(document.createTextNode(' ' + p[1])); row.appendChild(head);
    row.appendChild(bar('bi-encoder', dot(STORE[k], v), 3, ''));
    row.appendChild(bar('cross-encoder', c[0], 2, 'x'));
    row.appendChild(el('div', 'pe-why', c[0] ? 'lined up best: ' + c[1] : 'none of the question\'s ideas is in any sentence'));
    out.appendChild(row);
  });
}
sel.addEventListener('change', render); own.addEventListener('input', render); render();"""
DATA_JS = json.dumps(DATA, separators=(",", ":")).replace("</", "<\\/")
JS = "<script>\n(function(){\n'use strict';\nvar D = " + DATA_JS + ";\n" + CORE_JS + UI_JS + "\n})();\n</script>\n"
assert "</" not in JS.replace("</script>", "") and "<div" not in JS

CHECK_QS = PRESETS + [OTHER, "How long is the probation notice period?", "Can I quit while on probation?", "leave leave leave",
                      "Is unused leave encashed or does it lapse?", "Shorten notice? Leave! Earned; paid."]
NODE = ("var D = " + DATA_JS + ";\n" + CORE_JS + "var Q = " + json.dumps(CHECK_QS) + ";\n"
        "process.stdout.write(JSON.stringify(Q.map(function(q){ var v = encode(q); return {known: known(q), ideas: ideas(q),"
        " rows: D.passages.map(function(p){ var c = cross(q, p[2]); return [dot(encode(p[2]), v), c[0], c[1]]; })}; })));\n")
try:
    node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
except FileNotFoundError:
    raise SystemExit("B.4's build checks the widget against the Python with node: install Node.js, then build again")
assert node.returncode == 0, node.stderr[-800:]
for q, js in zip(CHECK_QS, json.loads(node.stdout)):
    assert js["known"] == known(q) and js["ideas"] == ideas(q), (q, js)
    for (pid, _label, text), (b, x, best) in zip(PASSAGES, js["rows"]):
        py_x, py_best = cross(q, text)
        assert abs(b - float(encode(text) @ encode(q))) < 1e-12 and x == py_x and best == py_best, (q, pid, b, x, best)
N_CHECKED = len(CHECK_QS) * len(PASSAGES)

# ------------------------------------------------------------------ the windows and the numbers the parts name


def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label, quote=False) + '</span>'
            '<button class="cp" type="button">copy</button></div><pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    head = "expected" + (" " + html.escape(label, quote=False) if label else "")
    return ('<div class="cw"><div class="ch-bar"><span>' + head + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


ENABLE = ('gcloud services enable discoveryengine.googleapis.com --project "$PROJECT" \\\n'
          '  && echo "discoveryengine.googleapis.com is on for $PROJECT"   # the Ranking API: free to enable, billed per request')
WIN = {
    "CELL_MLM": bash_window("run in your venv (a Python cell; no network, Rs 0)", heredoc(CELLS["mlm"])),
    "OUT_MLM": out_window("(this cell, run when the page was built)", OUT["mlm"]),
    "CELL_BI": bash_window("run in your venv (a Python cell; no network, Rs 0)", heredoc(CELLS["bi"])),
    "OUT_BI": out_window("(this cell, run when the page was built)", OUT["bi"]),
    "CELL_CROSS": bash_window("run in your venv (a Python cell; no network, Rs 0)", heredoc(CELLS["cross"])),
    "OUT_CROSS": out_window("(this cell, run when the page was built)", OUT["cross"]),
    "CELL_ENABLE": bash_window("run once, in the shell where PROJECT is set (after lesson 0.1)", ENABLE),
    "OUT_ENABLE": out_window("", "discoveryengine.googleapis.com is on for documind-ai-YOUR-ID"),
    "CELL_BI_LIVE": bash_window("run in your venv, PROJECT set (a Python cell; two paid embedding requests)", heredoc(CELLS["bi_live"])),
    "OUT_BI_LIVE": out_window("(recorded from the author's run of this cell)", LIVE["bi_encoder.txt"]),
    "CELL_CROSS_LIVE": bash_window("run in your venv, PROJECT set (a Python cell; one paid rank request)", heredoc(CELLS["cross_live"])),
    "OUT_CROSS_LIVE": out_window("(recorded from the author's run of this cell)", LIVE["cross_encoder.txt"]),
    "CELL_COMPARE": bash_window("run in your venv after the two cells above (a Python cell; no network, Rs 0)", heredoc(CELLS["compare"])),
    "OUT_COMPARE": out_window("(recorded from the author's run of this cell)", LIVE["compare.txt"]),
}


def inr(x: float, digits: int = 3) -> str:
    return f"Rs {x:.{digits}f}"


STATS = {
    "EMBED_MODEL": EMBED_MODEL, "DIMS": str(DIMS), "DOC_TASK": DOC_TASK, "QUERY_TASK": QUERY_TASK, "EMBED_LOC": EMBED_LOC,
    "RANK_MODEL": RANK_MODEL, "RANK_LOC": RANK_LOC, "RANK_CFG": RANK_CFG, "POOL": str(POOL), "TOPK": str(TOPK),
    "TOPK_MAX": str(TOPK_MAX), "RECORDS_CUT": str(RECORDS_CUT), "DISTANCE": DISTANCE, "N_CHUNKS": f"{N_CHUNKS:,}",
    "N_SENT": str(N_SENT), "N_MLM_WORDS": str(N_MLM_WORDS), "N_WORDS": str(len(TOY["WORDS"])), "QUESTION": QUESTION,
    "BI_NP03": f"{BI['NP-03']:.3f}", "BI_LV07": f"{BI['LV-07']:.3f}", "BI_LV01": f"{BI['LV-01']:.3f}", "BI_PB02": f"{BI['PB-02']:.3f}",
    "BI_GAP": f"{BI_GAP:.3f}", "BI_SAME": f"{B_SAME:.3f}", "N_CHECKED": str(N_CHECKED), "SBERT_PAIRS": f"{SBERT_PAIRS:,}",
    "LIVE_CHARS": f"{LIVE_CHARS:,}", "EMBED_PAISE": f"{EMBED_INR * 100:.2f}", "RANK_INR": inr(RANK_INR), "RANK_PAISE": f"{RANK_INR * 100:.1f}",
    "LIVE_INR": inr(EMBED_INR + RANK_INR), "Q_CHARS": str(len(QUESTION)), "Q_EMBED_PAISE": f"{Q_EMBED_INR * 100:.3f}",
    "CORPUS_CHARS": f"{N_CHARS:,}", "CORPUS_EMBED_INR": inr(CORPUS_EMBED_INR, 2), "CORPUS_QUERIES": str(CORPUS_QUERIES),
    "CORPUS_REQUESTS": {1: "one request", 2: "two requests", 3: "three requests"}.get(CORPUS_REQUESTS, f"{CORPUS_REQUESTS} requests"),
    "CORPUS_RANK_INR": inr(CORPUS_RANK_INR), "POOL_RANK_INR": inr(POOL_RANK_INR), "RANK_RATIO": str(round(RANK_INR / Q_EMBED_INR)),
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(STATS, indent=1))
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for name in LIVE:
    assert f"data/{name}" in RUN_LIST, f"RUN_LIST.md does not name data/{name}"
for k in ("bi_live", "cross_live", "compare"):
    assert heredoc(CELLS[k]) in RUN_LIST, f"RUN_LIST.md does not carry the {k} cell exactly as the page shows it"
print(f"kit: {EMBED_MODEL} ({DOC_TASK} / {QUERY_TASK}, {DIMS}, {EMBED_LOC}) | {RANK_MODEL} on {RANK_LOC} | pool {POOL}, top_k {TOPK}"
      f" | acme {N_CHUNKS} chunks | toys: bi {', '.join(f'{c} {BI[c]:.3f}' for c in ORDER)}; cross 1.00 1.00 0.33 0.33"
      f" | widget checked on {N_CHECKED} pairs | live: {LIVE_CHARS} characters {inr(EMBED_INR, 4)} + rank {inr(RANK_INR)}")
