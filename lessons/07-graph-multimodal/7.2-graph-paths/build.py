"""Build lesson 7.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Compare Firestore and Spanner graph paths. shared/documind_graph.py holds one tenant graph two ways. FirestoreGraph
(graph_nodes and graph_edges beside the chunks) seeds a walk by CONTAINMENT - a node's name inside the question, or a
capitalised run of the question inside a node's name - and expands with `in` queries, one round per hop. SpannerGraph
(spanner.tf's DocuMindGraph: GraphEdge interleaved in GraphNode ON DELETE CASCADE, and an `embedding` column) seeds BY
MEANING - COSINE_DISTANCE between the question's embedding and every node name's, the GRAPH_SEED_K nearest within
GRAPH_SEED_DISTANCE - and expands with one GQL statement in one snapshot. retriever.graph_candidates() puts the chunks
the walk reaches in front of the dense pool when RETRIEVAL_GRAPH says so (auto: a relational question with a seed).
Offline: the containment rule and choose_mode() on six questions, then the kit's own Spanner tests. Live: the Firestore
walk for the CFO question, without the word and with it; the graph built in Spanner, read back, and walked by meaning;
a candidate on each backend asked the question, with /version; the template put back.

Build-time proof: the offline cell runs on the kit. The live cells ran the kit's own graph.py (its main(), through
runpy, as make graph runs it) and the kit's own rag-api (under uvicorn, as the candidate) over a stand-in lane: acme's
chunks as the kit's chunker cuts them, lesson 7.1's graph, Firestore in JSON files, Spanner as a small interpreter of
the kit's own statements (the nearest names, the rows, the GQL walk - the walk read the way commands/tests/
test_spanner_graph.py reads it), and Gemini stood in: the extraction by 7.1's fixture, text-embedding-005 by a vector
per phrase from a small table of concepts plus noise, the answer by a reader of the packed clause. The panel's name
column is the kit's containment rule, ported and checked against the kit's code; its meaning column is the stand-in's
distances, labelled as such.
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

LESSON = "7.2"
title = "<title>Lesson 7.2 Compare Firestore and Spanner graph paths - seeded by a name, or by meaning | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8152
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
Q = "Who signs off on a big purchase?"                  # the kit's own acceptance question (INDEXING.md, README)
Q_NAMED = "Which purchases need the CFO?"
GRAPH, DG, RET, CFG, MAIN = ("services/ingest/graph.py", "shared/documind_graph.py", "services/rag-api/retriever.py",
                             "services/rag-api/config.py", "services/rag-api/main.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in label[hidden]{display:none;}
.pc-in select,.pc-in input[type=text]{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-in input[type=range]{min-height:44px;width:100%;margin:0;accent-color:var(--teal-dark);}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.gp-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:0 10px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,7.5em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "containment": ("shared/documind_graph.py - Firestore's seed: a stored name inside the question, or a capitalised run of the question inside a name",
                    block(DG, "def _candidate_names(question: str) -> list:", n=12)),
    "fs_seed": ("shared/documind_graph.py - FirestoreGraph.seed(): every node of the tenant, matched in Python, the longest names first",
                block(DG, "    def seed(self, question: str, tenant_id: str = TENANT, limit: int = 5) -> list:", n=11)),
    "ddl": ("terraform/spanner.tf - the tables and the property graph: tenant first in every key, edges interleaved in their source node",
            block("terraform/spanner.tf", "      CREATE TABLE IF NOT EXISTS GraphNode (", n=31)),
    "sp_sql": ("shared/documind_graph.py - SpannerGraph: the nearest names by cosine distance, and the walk as one GQL statement",
               block(DG, '    KNN_SQL = """SELECT node_id, name, kind, COSINE_DISTANCE(embedding, @q) AS d FROM GraphNode', n=13)),
    "route": ("services/rag-api/retriever.py - graph_candidates(): which seeder, then the relational gate, then the walk",
              block(RET, "    mode = settings.retrieval_graph", n=13)),
    "choose": ("shared/documind_graph.py - choose_mode(): auto walks only a relational question that found a seed",
               block(DG, "def choose_mode(question: str, seeds: list) -> str:", n=9)),
    "pool": ("services/rag-api/retriever.py - retrieve(): the walk's chunks first, then the dense candidates not already there",
             block(RET, "    graph = graph_candidates(query, tenant_id, filters)", n=6)),
}
assert EXCERPTS["containment"][1].rstrip().endswith("(name_lower in question_lower or any(c in name_lower for c in candidates))")   # each excerpt whole,
assert EXCERPTS["ddl"][1].rstrip().endswith("LABEL RELATES_TO") and EXCERPTS["sp_sql"][1].rstrip().endswith('LIMIT @cap"""')         # its last line included
assert "every backend's seed() matches by" in EXCERPTS["containment"][1] and 'if r.lower() not in _STOP and len(r) >= 5' in EXCERPTS["containment"][1]
assert 'select(["node_id", "name", "kind", "name_lower"]).stream()' in EXCERPTS["fs_seed"][1] and "return hits[:limit]" in EXCERPTS["fs_seed"][1]
assert "INTERLEAVE IN PARENT GraphNode ON DELETE CASCADE" in EXCERPTS["ddl"][1] and "embedding  ARRAY<FLOAT32>(vector_length=>768)," in EXCERPTS["ddl"][1]
assert "-[e:RELATES_TO]-{1,%d}" in EXCERPTS["sp_sql"][1] and "ORDER BY d" in EXCERPTS["sp_sql"][1] and "ROWS_SQL" in EXCERPTS["sp_sql"][1]
assert "seeds = g.seed_by_vector(embed_for_graph(query)" in EXCERPTS["route"][1] and EXCERPTS["route"][1].rstrip().endswith("cap=settings.graph_cap)")
assert 'return "graph" if (relational and seeds) else "vector"' in EXCERPTS["choose"][1]
assert "return prefer_current(graph + [c for c in dense if c[\"id\"] not in seen])[:settings.top_k_retrieve]" in EXCERPTS["pool"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (GRAPH, DG, RET, CFG, MAIN, "Makefile", "terraform/spanner.tf", "commands/lesson-12.2.sh")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert 'graph_seed_distance: float = Field(0.4, alias="GRAPH_SEED_DISTANCE")   # unverified on the real corpus: judge it on a candidate' in src[CFG]
assert 'graph_seed_k: int = Field(5, alias="GRAPH_SEED_K")' in src[CFG] and 'graph_hops: int = Field(1, alias="GRAPH_HOPS")' in src[CFG]
assert 'graph_cap: int = Field(20, alias="GRAPH_CAP")' in src[CFG] and 'retrieval_graph: str = Field("off", alias="RETRIEVAL_GRAPH")' in src[CFG]
# make candidate writes the backend and the switch, never the seed's threshold, k, hops or cap - and nothing in the kit's make files does
_c = MK.index("\ncandidate: guard-project")
CAND_RECIPE = MK[_c:MK.index("record-candidate PROJECT=$(PROJECT) REGION=$(REGION)", _c)]
assert "RETRIEVAL_GRAPH=$(RETRIEVAL_GRAPH)|GRAPH_BACKEND=$(GRAPH_BACKEND)|SPANNER_INSTANCE=$(SPANNER_INSTANCE)|SPANNER_DATABASE=$(SPANNER_DATABASE)" in CAND_RECIPE
assert not any(v in MK for v in ("GRAPH_SEED_DISTANCE", "GRAPH_SEED_K", "GRAPH_HOPS", "GRAPH_CAP"))
assert "GRAPH_SEED" not in src["commands/lesson-12.2.sh"] and "RETRIEVAL_GRAPH=${RETRIEVAL_GRAPH-off}|GRAPH_BACKEND=${GRAPH_BACKEND-firestore}" in src["commands/lesson-12.2.sh"]
# on Spanner the API seeds by distance only: SpannerGraph.seed(), the containment query, is reached by nothing that runs on the lane
ROUTE = src[RET].split("def graph_candidates(", 1)[1].split("def retrieve(", 1)[0]
SP_BRANCH, FS_BRANCH = ROUTE.split('if settings.graph_backend == "spanner":', 1)[1].split("    else:", 1)
assert "seed_by_vector" in SP_BRANCH and ".seed(" not in SP_BRANCH and "seeds = g.seed(query, tenant_id)" in FS_BRANCH
ASK_SPANNER = src[GRAPH].split('if args.backend == "spanner":', 1)[1].split("r = graph_chunk_ids(", 1)[0]
assert "vec=vec" in ASK_SPANNER and ".seed(" not in ASK_SPANNER
assert src[DG].count(".seed(question, tenant_id)") == 2 and "g = FirestoreGraph(db)\n    seeds = g.seed(question, tenant_id)" in src[DG]   # walk() without a vector, and graph_chunk_ids()
# the usage row carries the switch and the count, not the backend; /version carries the backend
USAGE_ROW = src[MAIN].split("def usage_row(", 1)[1].split("@app.get", 1)[0]
VERSION = src[MAIN].split('@app.get("/version")', 1)[1].split("@app.get", 1)[0]
assert '"retrieval_graph": settings.retrieval_graph, "graph_chunks": stages.get("graph_chunks", 0),' in USAGE_ROW and "graph_backend" not in USAGE_ROW
assert '"graph_backend": settings.graph_backend,' in VERSION
# SpannerGraph.load() writes the whole graph in one commit; FirestoreGraph.load() commits every 400 writes
SP_LOAD = src[DG].split("    def load(self, nodes: dict, edges: dict, tenant_id: str = TENANT, embeddings: dict | None = None) -> None:", 1)[1].split("    def seed(", 1)[0]
FS_LOAD = src[DG].split("    def load(self, nodes: dict, edges: dict, tenant_id: str = TENANT) -> None:", 1)[1].split("    def seed(", 1)[0]
assert SP_LOAD.count("with self.database.batch() as batch:") == 1 and "commit" not in SP_LOAD and "print(" not in SP_LOAD
assert FS_LOAD.count("if n % 400 == 0:") == 2 and "print(" in FS_LOAD
NODE_COLS = re.search(r'columns=\(("tenant_id", "node_id", "kind", "name", "chunk_ids", "embedding", "updated_at")\)', SP_LOAD).group(1).count('"') // 2
EDGE_COLS = re.search(r'columns=\(("tenant_id", "node_id", "dst_id", "rel", "chunk_id", "confidence")\)', SP_LOAD).group(1).count('"') // 2
assert (NODE_COLS, EDGE_COLS) == (7, 6)
MUTATION_LIMIT = 80_000                                                  # Spanner's quotas page, "Mutations per commit", checked 24 September 2026
FIT = MUTATION_LIMIT // (NODE_COLS + EDGE_COLS)                           # nodes that fit with as many edges
assert FIT == 6153
# FirestoreGraph.seed() streams every node of the tenant for each question; the docstring's name-token index is not built
assert "Production would keep a name-token index." in src[DG]
assert 'edition          = "ENTERPRISE"' in src["terraform/spanner.tf"] and "processing_units = 100" in src["terraform/spanner.tf"]
assert "--instance-type free-instance" in src["terraform/spanner.tf"]
RECIPE = src["Makefile"][src["Makefile"].index("graph: guard-project\n"):].split("\n\n", 1)[0].rstrip("\n")
assert RECIPE.endswith("$(PY) graph.py --project $(PROJECT) --tenant $(TENANT) --backend $(GRAPH_BACKEND) $(GRAPH_ARGS)")
assert "(no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)" in MK
assert "(deploy/.candidate-revision - make promote moves traffic to it by name)" in MK
assert re.search(r"^RETRIEVAL_GRAPH \?= off$", src["Makefile"], re.M) and re.search(r"^GRAPH_BACKEND    \?= firestore$", src["Makefile"], re.M)


def make_echo(args: str, backend: str = "firestore") -> str:
    """What make prints before it runs the graph recipe: the recipe's lines, variables expanded."""
    body = RECIPE.split("\n", 1)[1]
    for k, v in {"$(PROJECT)": PROJ, "$(SPANNER_INSTANCE)": "documind-graph", "$(SPANNER_DATABASE)": "documind", "$(PY)": "python",
                 "$(TENANT)": "acme", "$(GRAPH_BACKEND)": backend, "$(GRAPH_ARGS)": args}.items():
        body = body.replace(k, v)
    return "\n".join(line.replace("\t", "", 1) for line in body.splitlines()) + "\n"


def candidate_echo(backend: str) -> str:
    """make candidate's lines, as 7.3 shows them: the command (its long settings list cut), then make's two >> lines."""
    return ("gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\\n"
            f'  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|...|RETRIEVAL_GRAPH=auto|GRAPH_BACKEND={backend}|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION\n'
            "...\n"
            ">> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
            f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\n")


# ------------------------------------------------------------------ lesson 7.1's graph: the stand-in extraction per clause, to the rule
E = lambda *pairs: [{"name": n, "type": t} for n, t in pairs]  # noqa: E731
R = lambda *rels: [{"source": s, "target": t, "rel": r, "confidence": c} for s, t, r, c in rels]  # noqa: E731
EXTRACTIONS = {
    "preamble": (E(("ACME Employee Handbook 2026", "policy")), R()),
    "NP-03": (E(("Notice period", "policy"), ("confirmed employee", "person"), ("earned leave", "policy")),
              R(("confirmed employee", "Notice period", "SERVES", 0.95), ("earned leave", "Notice period", "MAY_NOT_BE_SET_OFF_AGAINST", 0.9))),
    "PB-02": (E(("Probation", "policy"), ("New joiners", "person"), ("notice period", "policy")),
              R(("New joiners", "Probation", "SERVE", 0.95), ("Probation", "notice period", "SETS", 0.7), ("Probation", "Probation", "MAY_BE_EXTENDED", 0.6))),
    "LV-01": (E(("Earned leave", "policy"), ("31 December", "date")), R(("Earned leave", "31 December", "LAPSES_ABOVE_30_DAYS_ON", 0.85))),
    "LV-07": (E(("Leave on exit", "policy"), ("Earned leave", "policy"), ("basic pay", "policy"), ("probation", "policy")),
              R(("Earned leave", "basic pay", "ENCASHED_AT", 0.9), ("Leave on exit", "Earned leave", "GOVERNS", 0.8), ("Earned leave", "notice", "CANNOT_SHORTEN", 0.8))),
    "EXP-12": (E(("Travel reimbursement", "policy"), ("function head", "person")), R(("function head", "Travel reimbursement", "APPROVES_ABOVE_CAP", 0.9))),
    "PR-05": (E(("Form 16", "policy"), ("15 June", "date")), R(("Form 16", "15 June", "ISSUED_BY", 0.95))),
    "IT-SEC-04": (E(("USB mass-storage devices", "product"), ("company laptops", "product"), ("contractors", "person"), ("approved cloud bucket", "system")),
                  R(("USB mass-storage devices", "company laptops", "BLOCKED_ON", 0.95))),
    "SEC-09": (E(("Access review", "policy"), ("Production access", "system")), R(("Access review", "Production access", "REVIEWS_QUARTERLY", 0.85))),
    "FIN-02": (E(("Purchase approval", "policy"), ("function head", "person"), ("CFO", "person")),
               R(("function head", "Purchase approval", "APPROVES_UP_TO_RS_2_00_000", 0.9), ("CFO", "Purchase approval", "APPROVES_ABOVE_RS_2_00_000", 0.9))),
    "WFH-01": (E(("Remote work", "policy"), ("manager", "person"), ("India", "location"), ("tax clearance", "policy")),
               R(("manager", "Remote work", "CONSENTS_TO", 0.85), ("Remote work", "tax clearance", "REQUIRES_FROM_OUTSIDE_INDIA", 0.8))),
}

# the read cell's three statements - the stand-in answers exactly these, and the cell sends exactly these
NODES_SQL = "SELECT COUNT(*), COUNTIF(embedding IS NOT NULL), MAX(ARRAY_LENGTH(embedding)) FROM GraphNode WHERE tenant_id = @t"
EDGES_SQL = "SELECT COUNT(*) FROM GraphEdge WHERE tenant_id = @t"
NAMED_PARTS = ("SELECT n.node_id, n.name, e.rel, d.name, e.chunk_id FROM GraphEdge e ",
               "JOIN GraphNode n ON n.tenant_id = e.tenant_id AND n.node_id = e.node_id ",
               "JOIN GraphNode d ON d.tenant_id = e.tenant_id AND d.node_id = e.dst_id ",
               "WHERE e.tenant_id = @t ORDER BY n.name, e.rel")
NAMED_SQL = "".join(NAMED_PARTS)

# ---- the stand-in lane, a module every process below imports as lane152
LANE_LIB = r'''"""The stand-in lane for lesson 7.2's build. services/ingest/graph.py and the rag-api run unchanged on top of it.

Firestore is held in JSON files: acme's chunks (the handbook and one Act, cut by the kit's chunker) and whatever the
build and the API write. Spanner is held the same way, as the two tables spanner.tf declares, and answers the
statements the kit sends - the nearest names by cosine distance, the rows by id, the GQL walk in either direction
(a walk may come back through its seed, as the kit's own test reads it) - plus the read cell's three. Gemini is stood
in three times: the extraction by lesson 7.1's fixture; text-embedding-005 by a vector per phrase - a shared part,
a small table of concepts read off the words, and noise from the phrase itself; and the answer by a reader of the
packed clause. The dense path and the Ranking API are word overlap, TF-IDF weighted, as in lessons 11.4-11.6."""
import collections
import json
import math
import os
import random
import re
import struct
import subprocess
import sys
import types
from types import SimpleNamespace

KIT = os.environ["LANE152_KIT"]
with open(os.environ["LANE152_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)                          # {"rows": {chunk_id: row}, "extractions": {locator: {...}}}
STORE_PATH = os.environ["LANE152_STORE"]            # Firestore: what the build and the API write, kept between processes
SPANNER_PATH = os.environ["LANE152_SPANNER"]        # Spanner: GraphNode and GraphEdge, kept between processes
CALLS = collections.Counter()                       # model calls this process made
READS = collections.Counter()                       # Firestore documents this process read, per collection
COMMITS = []                                        # Spanner commits this process made: mutations in each
LAST = {"q": ""}                                    # the question embed_query was last given
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


# ---- the dense path and the Ranking API: word overlap, TF-IDF weighted
STOP = set("a an the of for to in on at by is are be what which who how when does do i my can during with and or from as per this that it its".split())


def _toks(text: str, pairs: bool) -> list:
    w = [x for x in re.findall(r"[a-z0-9]+", text.lower()) if x not in STOP]
    return w + ([a + "_" + b for a, b in zip(w, w[1:])] if pairs else [])


_TEXTS = sorted({r["text"] for r in CORPUS["rows"].values()})
_DF = collections.Counter(t for text in _TEXTS for t in set(_toks(text, True)))
_VEC: dict = {}


def _tfidf(text: str, pairs: bool) -> dict:
    key = (text, pairs)
    if key not in _VEC:
        c = collections.Counter(_toks(text, pairs))
        v = {t: (1 + math.log(n)) * (math.log((len(_TEXTS) + 1) / (_DF.get(t, 0) + 1)) + 1) for t, n in c.items()}
        s = math.sqrt(sum(x * x for x in v.values())) or 1.0
        _VEC[key] = {t: x / s for t, x in v.items()}
    return _VEC[key]


def sim(a: str, b: str, pairs: bool = False) -> float:
    va, vb = _tfidf(a, pairs), _tfidf(b, pairs)
    return round(sum(x * vb.get(t, 0.0) for t, x in va.items()), 6)


# ---- text-embedding-005 for the graph (SEMANTIC_SIMILARITY), stood in
CONCEPTS = [  # a word that starts with the stem carries the concepts
    ("approv", ("approve",)), ("sign", ("approve",)), ("sanction", ("approve",)), ("consent", ("approve",)), ("clearance", ("approve",)),
    ("purchas", ("purchase", "finance")), ("buy", ("purchase",)), ("procur", ("purchase",)), ("spend", ("purchase",)),
    ("big", ("amount",)), ("large", ("amount",)), ("above", ("amount",)), ("lakh", ("amount",)), ("crore", ("amount",)),
    ("threshold", ("amount",)), ("cap", ("amount",)),
    ("cfo", ("finance", "senior")), ("financ", ("finance",)), ("reimburs", ("finance",)), ("claim", ("finance",)), ("budget", ("finance",)),
    ("pay", ("pay",)), ("encash", ("pay",)), ("salary", ("pay",)), ("tax", ("tax",)),
    ("leave", ("leave",)), ("holiday", ("leave",)), ("vacation", ("leave",)),
    ("notice", ("exit",)), ("exit", ("exit",)), ("resign", ("exit",)), ("quit", ("exit",)),
    ("probation", ("joining",)), ("joiner", ("joining",)), ("confirm", ("joining",)),
    ("head", ("senior",)), ("officer", ("senior",)), ("manager", ("role",)), ("employee", ("role",)), ("contractor", ("role",)), ("staff", ("role",)),
    ("laptop", ("device",)), ("usb", ("device",)), ("device", ("device",)), ("storage", ("device",)),
    ("cloud", ("system",)), ("bucket", ("system",)), ("production", ("system",)), ("access", ("security",)), ("review", ("security",)),
    ("travel", ("travel",)), ("trip", ("travel",)), ("remote", ("remote",)), ("home", ("remote",)),
    ("india", ("place",)), ("outside", ("place",)), ("abroad", ("place",)),
    ("december", ("date",)), ("june", ("date",)), ("month", ("date",)),
    ("handbook", ("document",)), ("policy", ("document",)), ("form", ("document",)),
]
WEIGHT = {"approve": 0.8, "amount": 0.6, "role": 0.7, "senior": 0.7, "finance": 0.7, "document": 0.6, "date": 0.7}
AXES = sorted({c for _, cs in CONCEPTS for c in cs})
COMMON, NOISE = 1.5, 0.9


def embed_text(text: str) -> list:
    """768 numbers, unit length: what every phrase shares, the concepts its words carry, and the phrase's own noise."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    hit = {c for w in words for stem, cs in CONCEPTS if w.startswith(stem) for c in cs}
    r = random.Random("vec:" + text)
    noise = [r.gauss(0, 1) for _ in range(768 - 1 - len(AXES))]
    nn = math.sqrt(sum(x * x for x in noise))
    v = [COMMON] + [WEIGHT.get(a, 1.0) if a in hit else 0.0 for a in AXES] + [NOISE * x / nn for x in noise]
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]


# ---- Firestore
def rows(coll: str) -> dict:
    return CORPUS["rows"] if coll == "chunks" else _load(STORE_PATH).get(coll, {})


class Snap:
    def __init__(self, coll, id_, data):
        self.id, self._d, self.exists, self.reference = id_, data, data is not None, Doc(coll, id_)

    def to_dict(self):
        return None if self._d is None else json.loads(json.dumps(self._d))

    def get(self, field):
        return (self._d or {}).get(field)


class Doc:
    def __init__(self, coll: str, id_: str):
        self.coll, self.id = coll, id_

    def get(self):
        READS[self.coll] += 1
        return Snap(self.coll, self.id, rows(self.coll).get(self.id))

    def set(self, data, merge=False):
        """A write, with firestore.Increment applied the way Firestore applies it: added to what is there."""
        store = json.loads(json.dumps(_load(STORE_PATH)))
        c = store.setdefault(self.coll, {})
        old = c.get(self.id, {}) if merge else {}
        new = dict(old)
        for k, v in data.items():
            new[k] = (old.get(k) or 0) + v.value if type(v).__name__ == "Increment" else v
        c[self.id] = new
        _save(STORE_PATH, store)

    def delete(self):
        store = json.loads(json.dumps(_load(STORE_PATH)))
        store.get(self.coll, {}).pop(self.id, None)
        _save(STORE_PATH, store)


class Batch:
    def __init__(self):
        self.ops = []

    def set(self, ref, data, merge=False):
        self.ops.append(("set", ref, data, merge))

    def delete(self, ref):
        self.ops.append(("delete", ref, None, False))

    def commit(self):
        for op, ref, data, merge in self.ops:
            ref.set(data, merge) if op == "set" else ref.delete()
        self.ops = []


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
        out = [Snap(self.coll, i, d) for i, d in self.matched()[:self.lim]]
        READS[self.coll] += len(out)
        return out

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

    def batch(self):
        return Batch()


DB = DBClass()


# ---- Spanner
COMMIT_TIMESTAMP = "spanner.commit_timestamp()"
NODES_SQL, EDGES_SQL, NAMED_SQL = @@READ_SQL@@


def _f32(xs) -> list:
    return list(struct.unpack(f"{len(xs)}f", struct.pack(f"{len(xs)}f", *xs)))


def _norm(sql: str) -> str:
    return " ".join(sql.split())


def _tables() -> tuple:
    t = _load(SPANNER_PATH)
    return t.get("GraphNode", {}), t.get("GraphEdge", {})


def _execute(sql: str, p: dict) -> list:
    nodes, edges = _tables()
    s, t = _norm(sql), p.get("tenant", p.get("t"))
    mine = {k: v for k, v in sorted(nodes.items()) if v["tenant_id"] == t}          # primary-key order
    if "COSINE_DISTANCE(embedding, @q) AS d FROM GraphNode" in s:
        assert "WHERE tenant_id = @tenant AND embedding IS NOT NULL ORDER BY d LIMIT @k" in s, s
        q = _f32(p["q"])
        qn = math.sqrt(sum(x * x for x in q))
        out = []
        for v in mine.values():
            e = v.get("embedding")
            if e is None:
                continue
            en = math.sqrt(sum(x * x for x in e))
            out.append((1.0 - sum(a * b for a, b in zip(q, e)) / (qn * en), v["node_id"], v))
        out.sort(key=lambda x: (x[0], x[1]))
        return [[v["node_id"], v["name"], v["kind"], d] for d, _, v in out[:p["k"]]]
    if s.startswith("GRAPH DocuMindGraph"):
        assert "a.tenant_id = @tenant AND a.node_id IN UNNEST(@seeds)" in s and "(b:GraphNode WHERE b.tenant_id = @tenant)" in s, s
        assert "RETURN DISTINCT b.node_id AS node_id ORDER BY node_id LIMIT @cap" in s, s
        hops = int(re.search(r"-\[e:RELATES_TO\]-\{1,(\d)\}", s).group(1))
        adj = collections.defaultdict(set)
        for e in edges.values():
            if e["tenant_id"] == t:
                adj[e["node_id"]].add(e["dst_id"])
                adj[e["dst_id"]].add(e["node_id"])                               # -[e]- : either direction
        ids = {v["node_id"] for v in mine.values()}
        frontier, reached = {n for n in p["seeds"] if n in ids}, set()
        for _ in range(hops):
            frontier = set().union(*(adj[n] for n in frontier)) if frontier else set()
            reached |= frontier
        return [[n] for n in sorted(reached)[:p["cap"]]]
    if s == "SELECT node_id, name, kind, chunk_ids FROM GraphNode WHERE tenant_id = @tenant AND node_id IN UNNEST(@ids)":
        return [[v["node_id"], v["name"], v["kind"], list(v.get("chunk_ids") or [])] for v in mine.values() if v["node_id"] in p["ids"]]
    if s == _norm(NODES_SQL):
        vecs = [v["embedding"] for v in mine.values() if v.get("embedding") is not None]
        return [[len(mine), len(vecs), max((len(x) for x in vecs), default=None)]]
    if s == _norm(EDGES_SQL):
        return [[sum(1 for e in edges.values() if e["tenant_id"] == t)]]
    if s == _norm(NAMED_SQL):
        name = {v["node_id"]: v["name"] for v in mine.values()}
        out = [[e["node_id"], name[e["node_id"]], e["rel"], name[e["dst_id"]], e["chunk_id"]] for e in edges.values()
               if e["tenant_id"] == t and e["node_id"] in name and e["dst_id"] in name]
        return sorted(out, key=lambda r: (r[1], r[2]))
    raise SystemExit(f"the stand-in Spanner has no answer for: {s[:160]}")


class _Snapshot:
    def __init__(self, multi_use: bool):
        self.multi_use, self.used, self.active = multi_use, 0, False

    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, *a):
        self.active = False

    def execute_sql(self, sql, params=None, param_types=None):
        assert self.active, "a snapshot reads inside its with block"
        assert set(params or {}) == set(param_types or {}), "every parameter must be typed"
        self.used += 1
        if not self.multi_use and self.used > 1:
            raise ValueError("Cannot re-use single-use snapshot.")
        return _execute(sql, params or {})


class _Batch:
    def __init__(self):
        self.ops, self.mutations = [], 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *a):
        if exc_type is None:
            self.commit()

    def insert_or_update(self, table, columns, values):
        for row in values:
            self.ops.append(("put", table, dict(zip(columns, row))))
            self.mutations += len(columns)                      # Spanner counts one mutation per column written, the key's included

    def delete(self, table, keyset):
        self.ops.append(("delete", table, keyset))
        self.mutations += 1

    def commit(self):
        if self.mutations > 80_000:
            raise ValueError(f"The transaction contains too many mutations: {self.mutations} (the limit is 80,000)")
        data = json.loads(json.dumps(_load(SPANNER_PATH)))
        nodes, edges = data.setdefault("GraphNode", {}), data.setdefault("GraphEdge", {})
        for op, table, x in self.ops:
            if op == "put":
                x = dict(x)
                if x.get("embedding") is not None:
                    x["embedding"] = _f32(x["embedding"])
                if x.get("updated_at") == COMMIT_TIMESTAMP:
                    x["updated_at"] = "2026-09-24T07:10:00Z"
                if table == "GraphNode":
                    nodes[x["tenant_id"] + "|" + x["node_id"]] = x
                else:
                    edges["|".join((x["tenant_id"], x["node_id"], x["dst_id"], x["rel"]))] = x
            else:
                assert table == "GraphNode", table
                for rng in x.ranges:
                    assert rng.start_closed == rng.end_closed and len(rng.start_closed) == 1, "a tenant's key range"
                    tenant = rng.start_closed[0]
                    for k in [k for k, v in nodes.items() if v["tenant_id"] == tenant]:
                        del nodes[k]
                    for k in [k for k, v in edges.items() if v["tenant_id"] == tenant]:   # INTERLEAVE ... ON DELETE CASCADE
                        del edges[k]
        for k, e in edges.items():                                                     # an interleaved row needs its parent
            if e["tenant_id"] + "|" + e["node_id"] not in nodes:
                raise ValueError(f"Parent row for row {k} in table GraphEdge is missing.")
        COMMITS.append(self.mutations)
        _save(SPANNER_PATH, data)


class _Database:
    def snapshot(self, multi_use=False, **kw):
        return _Snapshot(multi_use)

    def batch(self, **kw):
        return _Batch()


class _Instance:
    def database(self, name):
        assert name == "documind", name
        return _Database()


class _Client:
    def __init__(self, project=None, **kw):
        self.project = project

    def instance(self, name):
        assert name == "documind-graph", name
        return _Instance()


class _KeyRange:
    def __init__(self, start_closed=None, end_closed=None, start_open=None, end_open=None):
        self.start_closed, self.end_closed = start_closed, end_closed


class _KeySet:
    def __init__(self, keys=None, ranges=None, all_=False):
        self.keys, self.ranges = keys or [], ranges or []


def spanner_database():
    return _Database()


# ---- Gemini: the extraction, the embeddings, the answer
_BY_TEXT = {r["text"]: r["locator"] for r in CORPUS["rows"].values()}


def _reply(prompt: str):
    """Gemini, stood in by a reader: the answer from the packed clause that states it, cited, or a refusal."""
    question = prompt.rsplit("\n\nQuestion:", 1)[1].strip()
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    draft = {"answer": "The context does not say.", "citations": [], "confidence": "low", "answerable": False}
    for k in range(1, len(parts) - 2, 3):
        n, body = int(parts[k]), " ".join(parts[k + 2].split())
        m = re.search(r"Purchases up to Rs ([\d,]+) are approved by the function head\. Above that, the CFO approves\.", body)
        if m and "purchase" in question.lower():
            draft = {"answer": f"Purchases up to Rs {m.group(1)} are approved by the function head; above that, the CFO approves [{n}].",
                     "citations": [{"source": n, "quote": f"Purchases up to Rs {m.group(1)} are approved by the function head."}],
                     "confidence": "high", "answerable": True}
            break
    usage = SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(draft["answer"]) // 4 + 24,
                            thoughts_token_count=0, cached_content_token_count=0)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=usage,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


class Models:
    def generate_content(self, model, contents, config=None):
        text = contents[0] if isinstance(contents, list) else contents
        if isinstance(text, str) and text.startswith("Passage:\n"):
            CALLS["extract"] += 1
            x = CORPUS["extractions"].get(_BY_TEXT.get(text.split("Passage:\n", 1)[1], ""), {"entities": [], "relations": []})
            return SimpleNamespace(parsed=None, text=json.dumps(x))
        CALLS["answer"] += 1
        return _reply(text)

    def embed_content(self, model, contents, config=None):
        task = getattr(config, "task_type", None)
        assert task == "SEMANTIC_SIMILARITY" and model == "text-embedding-005", (model, task)   # the graph's vectors, and only those
        texts = [contents] if isinstance(contents, str) else list(contents)
        CALLS["embed"] += 1
        return SimpleNamespace(embeddings=[SimpleNamespace(values=embed_text(t)) for t in texts])


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models, self.caches = Models(), None
        self._api_client = SimpleNamespace(location=kw.get("location"))


def _mod(name: str, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


def install() -> None:
    """Gemini, Firestore and Spanner, for graph.py, the cells and the API."""
    if "google.cloud.spanner" in sys.modules:
        return
    param_types = SimpleNamespace(STRING="STRING", INT64="INT64", FLOAT32="FLOAT32", FLOAT64="FLOAT64", BOOL="BOOL", Array=lambda t: ("ARRAY", t))
    _mod("google.cloud.spanner", Client=_Client, KeyRange=_KeyRange)
    _mod("google.cloud.spanner_v1", param_types=param_types, COMMIT_TIMESTAMP=COMMIT_TIMESTAMP, KeySet=_KeySet)
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB


def stubs() -> None:
    """The modules rag-api imports that this machine does not have; nothing below reaches them."""
    install()
    if "google.cloud.discoveryengine_v1" in sys.modules:
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

    class Rec:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class Anything:
        def __init__(self, *a, **kw):
            pass

        def __getattr__(self, name):
            return lambda *a, **kw: None

    _mod("opentelemetry.exporter.cloud_trace", CloudTraceSpanExporter=CloudTraceSpanExporter)
    _mod("opentelemetry.instrumentation.fastapi", FastAPIInstrumentor=FastAPIInstrumentor)
    _mod("opentelemetry.instrumentation.google_genai", GoogleGenAiSdkInstrumentor=GoogleGenAiSdkInstrumentor)
    _mod("google.cloud.aiplatform", MatchingEngineIndexEndpoint=Anything, MatchingEngineIndex=Anything, init=lambda **kw: None)
    _mod("google.cloud.aiplatform.matching_engine")
    _mod("google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint", Namespace=Namespace)
    _mod("google.cloud.discoveryengine_v1", RankServiceClient=Anything, RankingRecord=Rec, RankRequest=Rec)
    for name in ("bigquery", "storage", "logging"):
        _mod(f"google.cloud.{name}", Client=Anything)


# ---- the index and the Ranking API
class Index:
    def find_neighbors(self, deployed_index_id, queries, num_neighbors, filter=None):
        allow = {ns.name: set(ns.allow_tokens) for ns in (filter or [])}
        keep = lambda d: all({"tenant_id": d["tenant_id"], "doc_type": d["doc_type"], "kind": d["kind"],  # noqa: E731
                              "current": "true"}.get(k) in toks for k, toks in allow.items())
        found = sorted(((sim(LAST["q"], d["text"]), i) for i, d in CORPUS["rows"].items() if keep(d)), key=lambda x: (-x[0], x[1]))
        return [[SimpleNamespace(id=i, distance=s) for s, i in found[:num_neighbors]]] if found else []


class Ranker:
    def ranking_config_path(self, project, location, ranking_config):
        return f"projects/{project}/locations/{location}/rankingConfigs/{ranking_config}"

    def rank(self, request, timeout=None):
        order = sorted(((sim(request.query, r.content, pairs=True), int(r.id)) for r in request.records), key=lambda x: (-x[0], x[1]))
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

    def embed(q):
        LAST["q"] = q
        return [0.001] * 768
    main.embed_query = retriever.embed_query = embed
    main.enforce_membership = lambda email, tenant_id: None     # the roster is lesson 8's; every ask here is a member's

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches
    return main


def serve(port: int, who: dict) -> None:
    """The kit's app on localhost, behind a stand-in of Cloud Run's IAM check; /_standin/calls reports the model calls."""
    main = rag()
    import shared.iap as iap

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity

    @main.app.get("/_standin/calls")
    def calls():
        return {"calls": dict(CALLS), "reads": dict(READS)}

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


def fake_cli() -> None:
    """gcloud's identity token, for the cells; the rest of subprocess stays."""
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd[:3] == ["gcloud", "auth", "print-identity-token"]:
            return subprocess.CompletedProcess(list(cmd), 0, "MEMBER\n", "")
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gcloud":
            raise SystemExit(f"the stand-in gcloud has no answer for {cmd[:4]}")
        return real_run(cmd, *a, **kw)
    subprocess.run = run
'''.replace("@@READ_SQL@@", repr((NODES_SQL, EDGES_SQL, NAMED_SQL)))

# ---- acme's chunks, as the kit's chunker cuts them, with the worker's chunk ids
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
ROWS = {}
for rel in ("evals/corpus/acme/hr_policy_2026.md", "evals/corpus/acme/dpdp_act_2023.md"):
    data = (KIT / rel).read_bytes()
    sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/acme/{Path(rel).name}"
    for i, c in enumerate(chunk_document({"text": data.decode("utf-8"), "source_uri": uri, "doc_type": "unknown", "slug": Path(rel).stem}, "acme")):
        ROWS[f"acme:{sha}#{i}"] = {"tenant_id": "acme", "text": c["text"], "source_uri": uri, "page_start": None, "doc_type": "unknown", "kind": "text",
                                   "doc_key": f"acme_{sha}", "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True,
                                   **({"section": c["section"]} if c.get("section") else {})}
HANDBOOK = {r["locator"]: (cid, r) for cid, r in ROWS.items() if "hr_policy_2026" in r["source_uri"] and not (r.get("section") or "").startswith("GEN-")}
assert sorted(HANDBOOK) == sorted(EXTRACTIONS), sorted(HANDBOOK)
for loc, (ents, rels) in EXTRACTIONS.items():                        # the stand-in keeps the schema's own promise: names as written
    text = " ".join(HANDBOOK[loc][1]["text"].split()).lower()
    assert all(e["name"].lower() in text for e in ents), (loc, [e["name"] for e in ents if e["name"].lower() not in text])
LOC = {cid: loc for loc, (cid, _) in HANDBOOK.items()}
FIN02, EXP12 = HANDBOOK["FIN-02"][0], HANDBOOK["EXP-12"][0]
TITLES = {loc: r["text"].split("\n", 1)[0].split(" \u2014 ", 1)[-1].strip() for loc, (_, r) in HANDBOOK.items()}
assert TITLES["FIN-02"] == "Purchase approval" and TITLES["EXP-12"] == "Travel reimbursement", TITLES

T = Path(tempfile.mkdtemp(prefix="lesson152-"))
(T / "corpus152.json").write_text(json.dumps({"rows": ROWS, "extractions": {k: {"entities": e, "relations": r} for k, (e, r) in EXTRACTIONS.items()}}), encoding="utf-8")
(T / "lane152.py").write_text(LANE_LIB, encoding="utf-8")
STORE, SPANNER = T / "store152.json", T / "spanner152.json"
STORE.write_text(json.dumps({"tenant_settings": {"acme": {"retrieval_backend": "vector"}}}), encoding="utf-8")   # 1.1's pin
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T), "LANE152_KIT": str(KIT), "LANE152_CORPUS": str(T / "corpus152.json"),
       "LANE152_STORE": str(STORE), "LANE152_SPANNER": str(SPANNER), "PYTHONPATH": str(T)}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "GRAPH_", "SPANNER_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR",
                                           "ROUTING", "SPEND_", "BUDGET_", "EMBEDDING_", "EMBED_"))]:
    ENV.pop(k)


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


# ------------------------------------------------------------------ the cells
RULES_PY = """import sys
sys.path.insert(0, ".")
from shared.documind_graph import _candidate_names, _seed_match, choose_mode   # the kit's seeding rules; no model, no network
NAMES = ["Purchase approval", "function head", "CFO", "Travel reimbursement", "Notice period", "probation", "India", "Remote work"]
QUESTIONS = ["Who signs off on a big purchase?", "Which purchases need the CFO?", "What does the CFO approve?",
             "Who approves a purchase above two lakh?", "Who approves a Purchase above two lakh?", "Who handles Indian travel claims?"]
print("eight names from the handbook's graph:", ", ".join(NAMES))
for q in QUESTIONS:
    cands, ql = _candidate_names(q), q.lower()
    seeds = sorted((n for n in NAMES if _seed_match(n.lower(), ql, cands)), key=len, reverse=True)[:5]
    print(q)
    print(f"  candidate names {cands}")
    print(f"  seeds by containment: {', '.join(seeds) or 'none'}   auto: {choose_mode(q, seeds)}")"""
TEST_CMD = "python -m unittest discover -s commands/tests -p test_spanner_graph.py"

READ_PY = ("""import os, sys
sys.path.insert(0, ".")
from google.cloud import firestore, spanner
from google.cloud.spanner_v1 import param_types as T
from shared.documind_graph import SpannerGraph
P, TENANT = os.environ["PROJECT"], "acme"
db = spanner.Client(project=P).instance("documind-graph").database("documind")
fs = firestore.Client(project=P)
loc = lambda cid: (fs.collection("chunks").document(cid).get().to_dict() or {}).get("locator")
p, t = {"t": TENANT}, {"t": T.STRING}
with db.snapshot(multi_use=True) as s:                         # one consistent read of both tables
    nodes, vectors, dims = list(s.execute_sql(%r,
                                              params=p, param_types=t))[0]
    edges = list(s.execute_sql(%r, params=p, param_types=t))[0][0]
    named = list(s.execute_sql(%r
                               %r
                               %r
                               %r, params=p, param_types=t))
print(f"tenant {TENANT}: {nodes} nodes ({vectors} with a {dims}-number vector), {edges} edges in Spanner")
cfo = [r for r in named if "cfo" in (r[1] + " " + r[3]).lower()] or named[:1]
print("the edges that name the CFO, as tables (the names joined from GraphNode):")
for nid, a, rel, b, cid in cfo:
    print(f"  {a} -[{rel}]-> {b}   stated in {loc(cid)}")
walked = SpannerGraph(db).expand([cfo[0][0]], TENANT, hops=1)       # the same rows as a graph: the kit's GQL walk
print(f"one hop from {cfo[0][1]}, by the kit's GQL walk: {', '.join(n['name'] for n in walked)}")
print(f"  the chunks they cite: {', '.join(sorted({loc(c) for n in walked for c in n['chunk_ids']}))}")"""
           % ((NODES_SQL, EDGES_SQL) + NAMED_PARTS))
assert "".join(re.findall(r"'([^']*)'", READ_PY.split("named = list(s.execute_sql(", 1)[1].split(", params=p", 1)[0])) == NAMED_SQL

ASK_PY = """import json, os, subprocess, urllib.request
from google.cloud import firestore
P, API, URL = os.environ["PROJECT"], os.environ["API"], os.environ["URL"]
Q = "Who signs off on a big purchase?"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
h = {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}
v = json.load(urllib.request.urlopen(urllib.request.Request(URL + "/version", headers=h), timeout=60))
print(f"/version: retrieval_graph={v['retrieval_graph']} graph_backend={v['graph_backend']} embedding={v['embedding']}")
req = urllib.request.Request(URL + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(), headers=h)
a, db = json.load(urllib.request.urlopen(req, timeout=180)), firestore.Client(project=P)
s = a["stages"]
print(f"Q: {Q}")
print(f"A: {a['answer']}")
print(f"pool {s['pool']}: the walk put {s['graph_chunks']} chunk(s) first; retrieval_backend {s['retrieval_backend']}")
for c in a["citations"]:
    row = db.collection("chunks").document(c["chunk_id"]).get().to_dict() or {}
    print(f"cites {row.get('locator')} ({c['source_uri'].rsplit('/', 1)[-1]}): {c['quote'][:96]}")
print(f"the word CFO: {'in' if 'cfo' in Q.lower() else 'not in'} the question, {'in' if 'CFO' in a['answer'] else 'not in'} the answer")"""

ASK_FN = ("ask152() {   # ask152 URL: the CFO question, without the word CFO, as documind-ui-sa - /version, the answer, the walk's share\n"
          + heredoc(ASK_PY, 'URL="$1" ') + "\n}")
ARGS_ASK = f"--ask \"{Q}\""
ARGS_ASK_NAMED = f"--ask \"{Q_NAMED}\""
ARGS_BUILD = "--source hr_policy_2026.md --rebuild"
CELLS = {
    "rules": heredoc(RULES_PY) + "\n" + TEST_CMD + "      # the kit's own tests of the Spanner walk, against a strict fake",
    "fs_ask": (f"make graph PROJECT=\"$PROJECT\" TENANT=acme GRAPH_ARGS='{ARGS_ASK}'\n"
               f"make graph PROJECT=\"$PROJECT\" TENANT=acme GRAPH_ARGS='{ARGS_ASK_NAMED}'"),
    "sp_build": (f'make graph PROJECT="$PROJECT" TENANT=acme GRAPH_BACKEND=spanner GRAPH_ARGS="{ARGS_BUILD}"\n' + heredoc(READ_PY)),
    "sp_ask": f"make graph PROJECT=\"$PROJECT\" TENANT=acme GRAPH_BACKEND=spanner GRAPH_ARGS='{ARGS_ASK}'",
    "cand_fs": ('make candidate PROJECT="$PROJECT" RETRIEVAL_GRAPH=auto GRAPH_BACKEND=firestore\n'
                'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"\n' + ASK_FN + '\nask152 "$CAND"'),
    "cand_sp": 'make candidate PROJECT="$PROJECT" RETRIEVAL_GRAPH=auto GRAPH_BACKEND=spanner\nask152 "$CAND"',
    "undo": ('gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\\n'
             "  --update-env-vars RETRIEVAL_GRAPH=off,GRAPH_BACKEND=firestore --remove-env-vars GRAPH_SEED_DISTANCE --quiet     # env vars merge: put the template back\n"
             'gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet\n'
             "rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag\n"
             'gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format=\'value(status.traffic[].percent,status.traffic[].revisionName)\''),
}
SEED_FIX = ('gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\\n'
            "  --update-env-vars GRAPH_SEED_DISTANCE=0.45 --quiet     # your number from step 5, not this one\n"
            'ask152 "$CAND"')

# ---- step 3: the rules, run on the kit; then the kit's own Spanner tests
OUT = {"rules": run_cell(RULES_PY, cwd=KIT)}
test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "commands/tests", "-p", "test_spanner_graph.py"],
                      cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=ENV)
assert test.returncode == 0 and test.stdout == "", (test.returncode, test.stdout, test.stderr)
N_TESTS = int(re.search(r"^Ran (\d+) tests? in [\d.]+s$", test.stderr, re.M).group(1))
assert N_TESTS == 8 and test.stderr.rstrip().endswith("\nOK"), test.stderr
OUT["rules"] += re.sub(r"in [\d.]+s", "in 0.004s", test.stderr)
R3 = OUT["rules"]
for q, seeds, mode in ((Q, "none", "vector"), (Q_NAMED, "CFO", "graph"), ("What does the CFO approve?", "CFO", "vector"),
                       ("Who approves a purchase above two lakh?", "none", "vector"), ("Who approves a Purchase above two lakh?", "Purchase approval", "graph"),
                       ("Who handles Indian travel claims?", "India", "graph")):
    assert f"{q}\n" in R3 and f"  seeds by containment: {seeds}   auto: {mode}\n" in R3.split(f"{q}\n", 1)[1].split("\n", 2)[1] + "\n", (q, R3)
assert "  candidate names ['purchase']\n" in R3 and "  candidate names ['indian']\n" in R3 and "  candidate names ['who signs off on a big purchase?']\n" in R3, R3

# ---- steps 4 and 5: the kit's graph.py main(), as make graph runs it, on the stand-in lane
PRELUDE = "import lane152\nlane152.install()\n"


def graph_py(args: list, backend: str = "firestore") -> tuple:
    body = ("import json, runpy, sys\nsys.path[:0] = ['.', '../..']\n"
            f"sys.argv = ['graph.py', '--project', {PROJ!r}, '--tenant', 'acme', '--backend', {backend!r}] + {args!r}\n"
            "try:\n    runpy.run_path('graph.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n"
            "print('STANDIN ' + json.dumps({'calls': dict(lane152.CALLS), 'reads': dict(lane152.READS), 'commits': lane152.COMMITS}))\n")
    out = run_cell(body, PRELUDE, cwd=KIT / "services/ingest")
    text, meta = out.rsplit("STANDIN ", 1)
    return text, json.loads(meta)


# lesson 7.1's state: the handbook's graph in Firestore, and its eleven extractions cached
built151, m151 = graph_py(["--source", "hr_policy_2026.md", "--rebuild"])
assert m151["calls"] == {"extract": 11, "embed": 1}, m151
assert '"nodes": 25, "edges": 15' in built151 and "25 nodes, 15 edges written for tenant acme (Firestore)" in built151, built151

ask_fs, m_fs = graph_py(["--ask", Q])
ask_named, m_named = graph_py(["--ask", Q_NAMED])
OUT["fs_ask"] = make_echo(ARGS_ASK) + ask_fs + make_echo(ARGS_ASK_NAMED) + ask_named
A_FS, A_NAMED = json.loads(ask_fs), json.loads(ask_named)
assert A_FS == {"question": Q, "backend": "firestore", "seeded_by": "containment", "seeds": [], "nodes": [], "chunk_ids": []}, A_FS
assert A_NAMED["seeds"] == ["CFO"] and A_NAMED["nodes"] == ["CFO", "Purchase approval"] and A_NAMED["chunk_ids"] == [FIN02], A_NAMED
assert not m_fs["calls"] and not m_named["calls"] and m_fs["reads"]["graph_nodes"] == 25, (m_fs, m_named)   # containment: no model; every node read
N_NODES = 25

built_sp, m_sp = graph_py(ARGS_BUILD.split(), "spanner")
OUT["sp_build"] = make_echo(ARGS_BUILD, "spanner") + built_sp
BUILT = json.loads(next(line for line in built_sp.splitlines() if '"graph_built"' in line))
EXTRACTED = json.loads(next(line for line in built_sp.splitlines() if '"graph_extracted"' in line))
assert BUILT == {"event": "graph_built", "tenant": "acme", "backend": "spanner", "chunks": 11, "surface_forms": 28, "nodes": 25, "edges": 15}, BUILT
assert (EXTRACTED["extracted"], EXTRACTED["fresh"]) == (11, 0) and m_sp["calls"] == {"embed": 2}, (EXTRACTED, m_sp)   # the cache answers; two embedding calls
assert built_sp.startswith("11 current text chunks for tenant 'acme' from 'hr_policy_2026.md'\n") and "written for tenant" not in built_sp, built_sp
MUTATIONS = m_sp["commits"][-1]
assert m_sp["commits"] == [1, 25 * NODE_COLS + 15 * EDGE_COLS] and MUTATIONS == 265, m_sp          # the delete, then the whole graph in one commit
read = run_cell(READ_PY, PRELUDE, cwd=KIT)
OUT["sp_build"] += read
assert read.startswith("tenant acme: 25 nodes (25 with a 768-number vector), 15 edges in Spanner\n"), read
assert "  CFO -[APPROVES_ABOVE_RS_2_00_000]-> Purchase approval   stated in FIN-02\n" in read, read
assert "one hop from CFO, by the kit's GQL walk: CFO, Purchase approval\n" in read and "  the chunks they cite: FIN-02\n" in read, read

ask_sp, m_ask = graph_py(["--ask", Q], "spanner")
OUT["sp_ask"] = make_echo(ARGS_ASK, "spanner") + ask_sp
A_SP = json.loads(ask_sp)
NEAR = {x["name"]: x for x in A_SP["nearest"]}
assert A_SP["seeded_by"] == "meaning" and A_SP["seed_distance"] == 0.4 and A_SP["seeds"] == ["Purchase approval"], A_SP
assert A_SP["nearest"][0]["name"] == "Purchase approval" and A_SP["nearest"][0]["seeded"] and len(A_SP["nearest"]) == 5, A_SP
assert "CFO" in NEAR and not NEAR["CFO"]["seeded"] and NEAR["CFO"]["distance"] > 0.4 and "CFO" in A_SP["nodes"], A_SP        # reached by the walk, not seeded
assert sorted(A_SP["nodes"]) == ["CFO", "Purchase approval", "function head"] and A_SP["chunk_ids"] == sorted([FIN02, EXP12]), A_SP
assert m_ask["calls"] == {"embed": 1}, m_ask
D_SEED, D_CFO, D_NEXT = NEAR["Purchase approval"]["distance"], NEAR["CFO"]["distance"], A_SP["nearest"][2]["distance"]

# ---- step 6: the kit's app on localhost as the candidate, on each backend
with socket.socket() as s_:
    assert s_.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
URL = f"http://127.0.0.1:{PORT}"
SERVE = f"import lane152; lane152.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"
LIVE_ENV = {"RETRIEVAL_BACKEND": "firestore", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT", "EMBEDDING_MODEL": "text-embedding-005",
            "EMBEDDING_VERSION": "1", "SPANNER_INSTANCE": "documind-graph", "SPANNER_DATABASE": "documind"}


def candidate(backend: str) -> tuple:
    log = T / f"api152-{backend}.log"
    with open(log, "w", encoding="utf-8") as logf:
        srv = subprocess.Popen([sys.executable, "-c", SERVE], cwd=str(T), env={**ENV, **LIVE_ENV, "RETRIEVAL_GRAPH": "auto", "GRAPH_BACKEND": backend},
                               stdout=logf, stderr=subprocess.STDOUT)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
                break
            except Exception:                      # noqa: BLE001 - not up yet
                time.sleep(0.2)
        else:
            raise SystemExit("the API did not start: " + log.read_text(encoding="utf-8")[-1500:])
        out = run_cell(ASK_PY, PRELUDE + "lane152.fake_cli()\n", env={"API": "https://documind-api-NUMBER.asia-south1.run.app", "URL": URL})
        calls = json.load(urllib.request.urlopen(urllib.request.Request(URL + "/_standin/calls", headers={"Authorization": "Bearer MEMBER"}), timeout=5))
    finally:
        srv.terminate()
        srv.wait(timeout=20)
    rows_ = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.startswith('{"event": "query"')]
    return out, {"calls": calls, "rows": rows_}


ans_fs, S_FS = candidate("firestore")
ans_sp, S_SP = candidate("spanner")
OUT["cand_fs"] = candidate_echo("firestore") + ans_fs
OUT["cand_sp"] = candidate_echo("spanner") + ans_sp
assert ans_fs.startswith("/version: retrieval_graph=auto graph_backend=firestore embedding=text-embedding-005@1\n"), ans_fs
assert ans_sp.startswith("/version: retrieval_graph=auto graph_backend=spanner embedding=text-embedding-005@1\n"), ans_sp
for a_ in (ans_fs, ans_sp):
    assert "the word CFO: not in the question, in the answer\n" in a_ and "cites FIN-02 (hr_policy_2026.md): " in a_, a_
assert "pool 20: the walk put 0 chunk(s) first; retrieval_backend vector\n" in ans_fs, ans_fs
assert "pool 20: the walk put 2 chunk(s) first; retrieval_backend vector\n" in ans_sp, ans_sp
assert S_FS["calls"]["calls"].get("embed", 0) == 0 and S_SP["calls"]["calls"]["embed"] == 1, (S_FS["calls"], S_SP["calls"])   # one embedding a question, Spanner only
for side, n in ((S_FS, 0), (S_SP, 2)):
    (row,) = side["rows"]
    assert row["retrieval_graph"] == "auto" and row["graph_chunks"] == n and "graph_backend" not in row, row   # the row cannot tell the backends apart
COST_RS = max(side["rows"][0]["cost_usd"] for side in (S_FS, S_SP)) * 85
OUT["undo"] = "100\tdocumind-api-000NN-xxx\n"

# ---- the panel: the handbook's graph, both seeders, and the stand-in's distances for seven questions
PRESETS = [Q, Q_NAMED, "What does the CFO approve?", "Who approves a purchase above two lakh?", "Who approves a Purchase above two lakh?",
           "Who handles Indian travel claims?", "Who approves travel above the cap?"]
names_ = sorted({n for x in EXTRACTIONS.values() for n in (e["name"] for e in x[0])})
BATTERY = PRESETS + [f"{w} {f(n)}?" for w in ("Who approves the", "What is the", "Which rule covers", "Tell me about") for n in names_
                     for f in (str, str.lower, str.upper, str.title)] + ["Who manages Indian contractors?", "Does a New Joiner serve Probation?",
                                                                         "Which Code on Wages clause?", "Who owns the approved cloud bucket?"]
THRS = [i / 100 for i in range(20, 61, 2)] + [0.41, 0.415, 0.42]
CHECK_PY = ("import json, sys\nsys.path[:0] = [%r]\n"
            "from shared.documind_graph import FirestoreGraph, SpannerGraph, choose_mode, walk, graph_chunk_ids\n"
            "db, sp = lane152.DB, SpannerGraph(lane152.spanner_database())\n"
            "BATTERY, PRESETS, THRS = %r, %r, %r\n"
            "lane152.READS.clear(); FirestoreGraph(db).seed(BATTERY[0], 'acme'); seed_reads = lane152.READS['graph_nodes']\n"
            "nodes = [{'id': d.get('node_id'), 'name': d.get('name'), 'kind': d.get('kind'), 'cids': d.get('chunk_ids')} for d in db.collection('graph_nodes').stream()]\n"
            "edges = [[e.get('node_id'), e.get('dst_id')] for e in db.collection('graph_edges').stream()]\n"
            "fs = []\n"
            "for q in BATTERY:\n"
            "    for h in (1, 2):\n"
            "        r = graph_chunk_ids(db, q, 'acme', hops=h)\n"
            "        fs.append([q, h, [s['name'] for s in r['seeds']], choose_mode(q, r['seeds']), [n['name'] for n in r['nodes']], r['chunk_ids']])\n"
            "dist, spr = [], []\n"
            "for i, q in enumerate(PRESETS):\n"
            "    vec = lane152.embed_text(q)\n"
            "    dist.append({x['node_id']: x['distance'] for x in sp.seed_by_vector(vec, 'acme', k=99, max_distance=None)})\n"
            "    for k in (3, 5, 7):\n"
            "        for thr in THRS:\n"
            "            for h in (1, 2):\n"
            "                r = walk(sp, q, 'acme', hops=h, vec=vec, k=k, max_distance=thr)\n"
            "                spr.append([i, k, thr, h, [s['name'] for s in r['seeds']], choose_mode(q, r['seeds']), [n['name'] for n in r['nodes']], r['chunk_ids']])\n"
            "same = 0\n"                                                   # from the same seeds, both stores reach the same nodes (cap aside)
            "for q in BATTERY:\n"
            "    ids = [s['node_id'] for s in FirestoreGraph(db).seed(q, 'acme')]\n"
            "    for h in ((1, 2) if ids else ()):\n"
            "        a = sorted(n['name'] for n in FirestoreGraph(db).expand(ids, 'acme', hops=h, cap=99))\n"
            "        b = sorted(n['name'] for n in sp.expand(ids, 'acme', hops=h, cap=99))\n"
            "        assert a == b, (q, h, a, b)\n"
            "        same += 1\n"
            "print(json.dumps({'nodes': nodes, 'edges': edges, 'fs': fs, 'dist': dist, 'sp': spr, 'seed_reads': seed_reads, 'same': same}))\n") % (str(KIT), BATTERY, PRESETS, THRS)
PY_SIDE = json.loads(run_cell(CHECK_PY, PRELUDE))
assert PY_SIDE["seed_reads"] == N_NODES and PY_SIDE["same"] > 300, (PY_SIDE["seed_reads"], PY_SIDE["same"])
NODES = sorted(PY_SIDE["nodes"], key=lambda n: n["name"].lower())
IDX = {n["id"]: i for i, n in enumerate(NODES)}
CIDS = sorted({c for n in NODES for c in n["cids"]})
PANEL = {"nodes": [{"id": n["id"], "name": n["name"], "c": [CIDS.index(c) for c in n["cids"]]} for n in NODES],
         "edges": [[IDX[a], IDX[b]] for a, b in PY_SIDE["edges"]],
         "cids": [LOC[c] for c in CIDS], "titles": TITLES,
         "stop": sorted(__import__("ast").literal_eval(re.search(r"_STOP = (\{.*?\})\n", src[DG], re.S).group(1))),
         "presets": [{"q": q, "dist": [round(PY_SIDE["dist"][i][n["id"]], 6) for n in NODES]} for i, q in enumerate(PRESETS)]}
assert len(PANEL["nodes"]) == 25 and len(PANEL["edges"]) == 15 and len(PY_SIDE["fs"]) == 2 * len(BATTERY)
FIRST_SEEDS = {tuple(r[2]) for r in PY_SIDE["fs"]}
assert len(FIRST_SEEDS) > 12, FIRST_SEEDS                                  # the battery reaches many different seed sets

# ------------------------------------------------------------------ the widget: one question, two ways in
UI_JS = r"""var root = document.getElementById('gp'); if (!root) return;
  var D = @@DATA@@, STOP = D.stop, CAP = 20;
  var RUN = /\b[A-Z][\w&-]*(?:\s+(?:[A-Z][\w&-]*|of|on|and|for))*/g;
  var REL = /\b(who|which|whose|related|relationship|connect|between|depend|owns?|reports? to|supersed|replac|affect|impact|downstream|upstream)\b/i;
  function byId(a, b){ return D.nodes[a].id < D.nodes[b].id ? -1 : D.nodes[a].id > D.nodes[b].id ? 1 : 0; }
  function byName(a, b){ var x = D.nodes[a].name, y = D.nodes[b].name; return x < y ? -1 : x > y ? 1 : 0; }
  var ALL = D.nodes.map(function(n, i){ return i; }), DOCS = ALL.slice().sort(byId);
  function cands(q){ var out = []; (q.match(RUN) || []).forEach(function(r){ var l = r.toLowerCase(); if (STOP.indexOf(l) < 0 && r.length >= 5) { out.push(l); } }); return out.length ? out : [q.toLowerCase()]; }
  function chooseMode(q, seeds){ return REL.test(q) && seeds.length ? 'graph' : 'vector'; }
  function fsSeeds(q){ var cs = cands(q), ql = q.toLowerCase(), hits = [];
    DOCS.forEach(function(i){ var nl = D.nodes[i].name.toLowerCase(); if (nl && (ql.indexOf(nl) >= 0 || cs.some(function(c){ return nl.indexOf(c) >= 0; }))) { hits.push(i); } });
    return hits.sort(function(a, b){ return D.nodes[b].name.length - D.nodes[a].name.length; }).slice(0, 5); }
  function nbrs(set){ var nxt = {}; D.edges.forEach(function(e){ if (set[e[0]]) { nxt[e[1]] = 1; } if (set[e[1]]) { nxt[e[0]] = 1; } }); return nxt; }
  function fsWalk(seeds, hops){ var seen = {}, front = {}; seeds.forEach(function(i){ seen[i] = 1; front[i] = 1; });
    for (var h = 0; h < hops; h++) { var nxt = nbrs(front), f = {}; Object.keys(nxt).forEach(function(k){ if (!seen[k]) { f[k] = 1; } seen[k] = 1; }); front = f; }
    return Object.keys(seen).map(Number).sort(byName).slice(0, CAP); }
  function spNearest(dist, k){ return ALL.slice().sort(function(a, b){ return dist[a] - dist[b] || byId(a, b); }).slice(0, k); }
  function spWalk(seeds, hops){ var first = seeds.slice().sort(byId), seen = {}, front = {}, reached = {};
    first.forEach(function(i){ seen[i] = 1; front[i] = 1; });
    for (var h = 0; h < hops; h++) { front = nbrs(front); Object.keys(front).forEach(function(k){ reached[k] = 1; }); }
    var gql = Object.keys(reached).map(Number).sort(byId).slice(0, CAP);
    return first.concat(gql.filter(function(i){ return !seen[i]; })).slice(0, CAP); }
  function chunks(nodes){ var s = {}; nodes.forEach(function(i){ D.nodes[i].c.forEach(function(c){ s[c] = 1; }); }); return Object.keys(s).map(Number).sort(function(a, b){ return a - b; }); }
  window.__gp = {fsSeeds: fsSeeds, fsWalk: fsWalk, spNearest: spNearest, spWalk: spWalk, chunks: chunks, chooseMode: chooseMode, names: function(l){ return l.map(function(i){ return D.nodes[i].name; }); }};
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  var $ = function(id){ return document.getElementById(id); };
  function names(l){ return l.map(function(i){ return D.nodes[i].name; }).join(', '); }
  function clauses(l){ return l.map(function(c){ return D.cids[c] + ' ' + (D.titles[D.cids[c]] || ''); }).join('; '); }
  function row(out, k, v, cls){ out.appendChild(el('b', '', k)); out.appendChild(el('span', cls || '', v)); }
  function walkRows(out, q, seeds, mode, walk){
    if (!seeds.length) { row(out, 'The walk', 'none: no seed, so the dense pool answers alone', 'stop'); return; }
    if (mode === 'auto' && chooseMode(q, seeds) !== 'graph') { row(out, 'The walk', 'none: auto walks only a relational question (who, which, whose, depend...), so the dense pool answers alone', 'stop'); return; }
    var w = walk(seeds); row(out, 'The walk', names(w)); row(out, 'Pool, first', clauses(chunks(w)), 'pass'); }
  function render(){ var pick = $('gp-q').value, own = pick === 'own', q = own ? $('gp-own').value.trim() : D.presets[Number(pick)].q;
    var mode = $('gp-mode').value, hops = Number($('gp-hops').value), k = Number($('gp-k').value), thr = Number($('gp-d').value);
    $('gp-own-l').hidden = !own; $('gp-dv').textContent = thr.toFixed(2);
    var fs = $('gp-fs'), sp = $('gp-sp'); fs.textContent = ''; sp.textContent = '';
    if (!q) { row(fs, 'Question', 'type one above'); row(sp, 'Question', 'type one above'); return; }
    var cs = cands(q), s1 = fsSeeds(q);
    row(fs, 'Candidates', cs.length === 1 && cs[0] === q.toLowerCase() ? 'no capitalised run of five letters: the whole question stands in' : cs.join(', '));
    row(fs, 'Seeds', s1.length ? names(s1) : 'none: no stored name is in the question', s1.length ? 'pass' : 'stop');
    row(fs, 'It cost', D.nodes.length + ' document reads: every node of the tenant, every question');
    walkRows(fs, q, s1, mode, function(s){ return fsWalk(s, hops); });
    if (own) { row(sp, 'Seeds', 'these need the question\'s embedding, so this column works only for the questions in the list', 'stop'); return; }
    var dist = D.presets[Number(pick)].dist, near = spNearest(dist, k), s2 = near.filter(function(i){ return dist[i] <= thr; });
    row(sp, 'Nearest ' + k, near.map(function(i){ return D.nodes[i].name + ' ' + dist[i].toFixed(3) + (dist[i] <= thr ? ' \u2713' : ''); }).join(', '));
    row(sp, 'Seeds', s2.length ? names(s2) : 'none within ' + thr.toFixed(2), s2.length ? 'pass' : 'stop');
    row(sp, 'It cost', 'one embedding call, then a scan inside an instance billed by the hour');
    walkRows(sp, q, s2, mode, function(s){ return spWalk(s, hops); }); }
  D.presets.forEach(function(p, i){ var o = el('option', '', p.q); o.value = String(i); $('gp-q').appendChild(o); });
  var own = el('option', '', 'Type your own question...'); own.value = 'own'; $('gp-q').appendChild(own);
  ['gp-q', 'gp-own', 'gp-mode', 'gp-hops', 'gp-k', 'gp-d'].forEach(function(id){ $(id).addEventListener('input', render); $(id).addEventListener('change', render); });
  render();""".replace("@@DATA@@", json.dumps(PANEL))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# the port against the kit: the name column on every question of the battery, the meaning column on every preset, k and threshold
PORT_JS = UI_JS.split("function el(")[0].replace("var root = document.getElementById('gp'); if (!root) return;", "")
TESTS = {"fs": [[r[0], r[1]] for r in PY_SIDE["fs"]], "sp": [r[:4] for r in PY_SIDE["sp"]]}
NODE = ("var window = {}, document = {};\n"
        "var src = " + json.dumps(PORT_JS) + ";\n"
        "(new Function('window', 'document', src))(window, document);\n"
        "var G = window.__gp, D = " + json.dumps(PANEL) + ", T = " + json.dumps(TESTS) + ";\n"
        "var ids = function(l){ return G.chunks(l).map(function(c){ return " + json.dumps(CIDS) + "[c]; }); };\n"
        "var fs = T.fs.map(function(t){ var s = G.fsSeeds(t[0]), w = s.length ? G.fsWalk(s, t[1]) : [];\n"
        "  return [t[0], t[1], G.names(s), G.chooseMode(t[0], s), G.names(w), ids(w)]; });\n"
        "var sp = T.sp.map(function(t){ var dist = D.presets[t[0]].dist, s = G.spNearest(dist, t[1]).filter(function(i){ return dist[i] <= t[2]; }),\n"
        "  w = s.length ? G.spWalk(s, t[3]) : []; return [t[0], t[1], t[2], t[3], G.names(s), G.chooseMode(D.presets[t[0]].q, s), G.names(w), ids(w)]; });\n"
        "process.stdout.write(JSON.stringify({fs: fs, sp: sp}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
assert JS_SIDE["fs"] == PY_SIDE["fs"], next(((a, b) for a, b in zip(JS_SIDE["fs"], PY_SIDE["fs"]) if a != b), None)
assert JS_SIDE["sp"] == PY_SIDE["sp"], next(((a, b) for a, b in zip(JS_SIDE["sp"], PY_SIDE["sp"]) if a != b), None)
N_CHECKED = len(PY_SIDE["fs"]) + len(PY_SIDE["sp"])
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the seeding rules, run; then the kit's tests; no model, no network)",
    "fs_ask": "run in the operator shell, in the kit (two walks of the Firestore graph; reads only)",
    "sp_build": "run in the operator shell, in the kit (the same graph written to Spanner, then read back)",
    "sp_ask": "run in the operator shell, in the kit (one walk of the Spanner graph, seeded by meaning; one embedding call)",
    "cand_fs": "run in the operator shell, in the kit (a candidate with no traffic: the walk on, from Firestore; one question)",
    "cand_sp": "run in the operator shell, in the kit (the same candidate, the walk from Spanner; the same question)",
    "undo": "run in the operator shell, in the kit (the template put back, the tag dropped; the live revision was never touched)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own documind_graph.py and its test)",
    "fs_ask": "(the kit's graph.py on a stand-in lane holding lesson 7.1's graph; your names are your flash-lite's)",
    "sp_build": "(the kit's graph.py and SpannerGraph on a stand-in lane; your counts are your build's)",
    "sp_ask": "(the stand-in's distances, from a small table of concepts, not text-embedding-005: your numbers will differ)",
    "cand_fs": "(make's lines as a shape; then the kit's rag-api on a stand-in lane, Gemini stood in)",
    "cand_sp": "(the same stand-ins, the walk from Spanner)",
    "undo": "shape (your revision's name)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["CELL_SEED_FIX"] = bash_window("run only if step 5 seeded nothing (the threshold, on the candidate alone)", SEED_FIX)

STATS = {"N_NODES": str(N_NODES), "N_EDGES": "15", "N_TESTS": str(N_TESTS), "N_CHECKED": f"{N_CHECKED:,}", "N_PRESETS": str(len(PRESETS)),
         "D_SEED": f"{D_SEED:.3f}", "D_CFO": f"{D_CFO:.3f}", "D_NEXT": f"{D_NEXT:.3f}", "MUTATIONS": str(MUTATIONS), "FIT": f"{FIT:,}",
         "COST_RS": f"{COST_RS:.2f}"}

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
print(f"kit: graph.py and rag-api on a stand-in lane (Firestore, Spanner, Gemini stood in) | the CFO question: Firestore seeds nothing,"
      f" Spanner seeds Purchase approval at {D_SEED:.3f} and walks to the CFO | panel port checked on {N_CHECKED:,} cases")
