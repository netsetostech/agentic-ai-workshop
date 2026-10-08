"""Build lesson 7.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Build graph evidence from source documents. services/ingest/graph.py turns a tenant's current text chunks into a
knowledge graph in four passes: an extraction per chunk (gemini-3.1-flash-lite, the GraphExtraction schema, entities
and relations STATED in the passage, never inferred), cached under the chunk's hash; resolution of surface forms to one
canonical name (normalise(), then text-embedding-005 cosine at 0.92 - a wrong merge is worse than a duplicate node);
the build (a node per canonical name with the chunk ids that mention it, an edge per source/target/relation with the
chunk that states it and the best confidence, dangling and self edges dropped); the load into graph_nodes and
graph_edges beside the chunks. Offline: the rules, run - normalise(), resolve_entities(), node_id() and build_graph()
on a small example, no model called. Live: make graph over the handbook, a dry run then the build; the graph read back
- node and edge counts, and one edge with its source chunk; one extraction audited against its passage, and a rerun
that extracts nothing.

Build-time proof: the offline cell runs on the kit. The live cells ran the kit's own graph.py (its main(), through
runpy, as make graph runs it) over a stand-in lane: acme's current chunks as the kit's chunker cuts them, Firestore
in JSON files, flash-lite stood in by a fixed extraction per passage (written to the prompt's rule, and checked here:
every entity name is in its passage as written), text-embedding-005 by a vector per name that tells every name apart.
The counts, the edge and the audit are what the kit wrote. The panel is that graph: the kit's build_graph() and
resolve_entities() over the stand-in's extractions.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "7.1"
title = "<title>Lesson 7.1 Build graph evidence from source documents - stated, resolved, cited | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
GRAPH = "services/ingest/graph.py"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,9em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
.gx-pass{white-space:pre-wrap;font-family:var(--mono);font-size:11.5px;line-height:1.5;background:var(--bg-soft,#f8fafc);border:1px solid var(--border);border-radius:8px;padding:8px 10px;margin:6px 0 0;}
.gx-pass mark{background:#ccfbf1;color:inherit;padding:0 2px;border-radius:3px;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "prompt": ("services/ingest/graph.py - the schema and the rule: typed entities, relations between them, stated and never inferred",
               block(GRAPH, "class Entity(BaseModel):", n=21)),
    "resolve": ("services/ingest/graph.py - resolve_entities(): normalise, then cosine at 0.92 for what survives",
                block(GRAPH, "    for i in range(len(reps)):", n=9)),
    "build": ("services/ingest/graph.py - build_graph(): chunk ids on every node, the best confidence per edge, dangling and self edges dropped",
              block(GRAPH, "def build_graph(extractions: list, canon_of: dict) -> tuple:", n=19)),
    "cache": ("services/ingest/graph.py - extract_all(): a chunk whose hash matches its cached extraction is not sent again",
              block(GRAPH, '        ref = db.collection("graph_extractions")', n=6)),
}
assert EXCERPTS["prompt"][1].rstrip().endswith('If the passage states no relation, return an empty relations list."""')   # the prompt whole, its closing line included
assert "Never infer, never add" in EXCERPTS["prompt"][1] and 'Literal["person", "org", "product", "policy", "system", "location", "date"]' in EXCERPTS["prompt"][1]
assert "if float(vecs[i] @ vecs[j]) >= RESOLVE_THRESHOLD:" in EXCERPTS["resolve"][1]
assert "# drop dangling and self edges" in EXCERPTS["build"][1] and 'r.confidence > prev["confidence"]' in EXCERPTS["build"][1]
assert 'if cached.get("chunk_hash") == c["chunk_hash"]:' in EXCERPTS["cache"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (GRAPH, "shared/documind_graph.py", "services/rag-api/retriever.py", "Makefile")}
assert "RESOLVE_THRESHOLD = 0.92" in src[GRAPH] and 'EXTRACT_MODEL = "gemini-3.1-flash-lite"' in src[GRAPH]
assert '(x.get("section") or "").startswith("GEN-")' in src[GRAPH]                               # the boilerplate is skipped
INGEST = "".join((KIT / "services/ingest" / f).read_text(encoding="utf-8") for f in ("main.py", "idempotency.py", "reconcile.py", "indexer.py", "managed.py"))
assert "graph_nodes" not in INGEST and "graph_edges" not in INGEST and "graph.py" not in INGEST   # nothing rebuilds the graph when a document changes
assert '.document(f"{tenant}:{c[\'chunk_id\']}".replace("/", "~"))' in src[GRAPH]                   # the cache is keyed by chunk id, a version's
assert "confidence" not in src["shared/documind_graph.py"].split("def expand(", 1)[1].split("def delete_tenant", 1)[0]
assert "confidence" not in src["services/rag-api/retriever.py"]                                   # nothing reads an edge's confidence
LOAD = src["shared/documind_graph.py"].split("    def load(self, nodes: dict, edges: dict, tenant_id: str = TENANT) -> None:", 1)[1].split("    def seed(", 1)[0]
assert "delete" not in LOAD                                                                       # load() overwrites; it removes nothing
assert "RETRIEVAL_GRAPH=${RETRIEVAL_GRAPH-off}" in (KIT / "commands/lesson-12.2.sh").read_text(encoding="utf-8")   # nothing serves from the graph on the lane
assert src[GRAPH].count("c['text']") == 1                                                         # the passage goes into the prompt, and into no check
assert "reading order sorts the Acts before the handbook" in src["Makefile"]
RECIPE = src["Makefile"][src["Makefile"].index("graph: guard-project\n"):].split("\n\n", 1)[0].rstrip("\n")
assert RECIPE.endswith("$(PY) graph.py --project $(PROJECT) --tenant $(TENANT) --backend $(GRAPH_BACKEND) $(GRAPH_ARGS)")


def make_echo(args: str) -> str:
    """What make prints before it runs the graph recipe: the recipe's lines, variables expanded."""
    body = RECIPE.split("\n", 1)[1]
    for k, v in {"$(PROJECT)": PROJ, "$(SPANNER_INSTANCE)": "documind-graph", "$(SPANNER_DATABASE)": "documind", "$(PY)": "python",
                 "$(TENANT)": "acme", "$(GRAPH_BACKEND)": "firestore", "$(GRAPH_ARGS)": args}.items():
        body = body.replace(k, v)
    return "\n".join(line.replace("\t", "", 1) for line in body.splitlines()) + "\n"


# ------------------------------------------------------------------ the stand-in extraction: flash-lite's answer per clause, to the rule
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

# ---- the stand-in lane, a module every process below imports as lane151
LANE_LIB = r'''"""The stand-in lane for lesson 7.1's build. services/ingest/graph.py runs unchanged on top of it: Firestore held in
JSON files (acme's current chunks - the handbook and one Act, cut by the kit's chunker - and whatever the build
writes: graph_extractions, graph_nodes, graph_edges), and Gemini stood in twice - the extraction by a fixed
GraphExtraction per passage, written to the prompt's own rule (stated in the passage, never inferred), and
text-embedding-005 by one pseudo-random vector per name, which tells every normalised name apart."""
import collections
import json
import os
import random
import sys
import types
from types import SimpleNamespace

with open(os.environ["LANE151_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)                          # {"rows": {chunk_id: row}, "extractions": {locator: {...}}}
STORE_PATH = os.environ["LANE151_STORE"]            # what the build writes, kept between processes
CALLS = collections.Counter()                       # model calls this process made: extract, embed


def _load() -> dict:
    try:
        with open(STORE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save(store: dict) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f)


def rows(coll: str) -> dict:
    if coll == "chunks":
        return {k: dict(v) for k, v in CORPUS["rows"].items()}
    return {k: dict(v) for k, v in _load().get(coll, {}).items()}


class Snap:
    def __init__(self, coll, id_, data):
        self.id, self._d, self.exists, self.reference = id_, data, data is not None, Doc(coll, id_)

    def to_dict(self):
        return None if self._d is None else dict(self._d)

    def get(self, field):
        return (self._d or {}).get(field)


class Doc:
    def __init__(self, coll: str, id_: str):
        self.coll, self.id = coll, id_

    def get(self):
        return Snap(self.coll, self.id, rows(self.coll).get(self.id))

    def set(self, data, merge=False):
        store = _load()
        c = store.setdefault(self.coll, {})
        c[self.id] = {**(c.get(self.id, {}) if merge else {}), **data}
        _save(store)

    def delete(self):
        store = _load()
        store.get(self.coll, {}).pop(self.id, None)
        _save(store)


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
    def __init__(self, coll: str, preds=()):
        self.coll, self.preds = coll, tuple(preds)

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.coll, self.preds + ((field, op, value),))

    def select(self, fields):
        return self

    def document(self, id_):
        return Doc(self.coll, id_)

    def stream(self):
        return [Snap(self.coll, i, d) for i, d in rows(self.coll).items() if all(_holds(i, d, *p) for p in self.preds)]

    get = stream


class DBClass:
    def collection(self, name):
        return Query(name)

    def batch(self):
        return Batch()


DB = DBClass()


# ---- Gemini: the extraction and the embeddings
_BY_TEXT = {r["text"]: r["locator"] for r in CORPUS["rows"].values()}


class Models:
    def generate_content(self, model, contents, config=None):
        """flash-lite's GraphExtraction, stood in: the fixture written for the passage's clause."""
        CALLS["extract"] += 1
        passage = contents.split("Passage:\n", 1)[1]
        x = CORPUS["extractions"].get(_BY_TEXT.get(passage, ""), {"entities": [], "relations": []})
        return SimpleNamespace(parsed=None, text=json.dumps(x))

    def embed_content(self, model, contents, config=None):
        """text-embedding-005, stood in: one pseudo-random unit-ish vector per name - no two names alike."""
        CALLS["embed"] += 1
        out = []
        for name in contents:
            r = random.Random("name:" + name)
            out.append(SimpleNamespace(values=[r.gauss(0, 1) for _ in range(768)]))
        return SimpleNamespace(embeddings=out)


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models = Models()


def install() -> None:
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB
'''

sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
ROWS, TEXTS = {}, {}
for rel in ("evals/corpus/acme/hr_policy_2026.md", "evals/corpus/acme/dpdp_act_2023.md"):
    data = (KIT / rel).read_bytes()
    sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/acme/{Path(rel).name}"
    for i, c in enumerate(chunk_document({"text": data.decode("utf-8"), "source_uri": uri, "doc_type": "unknown", "slug": Path(rel).stem}, "acme")):
        ROWS[f"acme:{sha}#{i}"] = {"tenant_id": "acme", "text": c["text"], "source_uri": uri, "kind": "text", "doc_key": f"acme_{sha}",
                                   "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True, **({"section": c["section"]} if c.get("section") else {})}
HANDBOOK = {r["locator"]: (cid, r) for cid, r in ROWS.items() if "hr_policy_2026" in r["source_uri"] and not (r.get("section") or "").startswith("GEN-")}
assert sorted(HANDBOOK) == sorted(EXTRACTIONS), sorted(HANDBOOK)
for loc, (ents, rels) in EXTRACTIONS.items():                        # the stand-in keeps the schema's own promise: names as written
    text = " ".join(HANDBOOK[loc][1]["text"].split()).lower()      # a name may wrap across a line
    assert all(e["name"].lower() in text for e in ents), (loc, [e["name"] for e in ents if e["name"].lower() not in text])
T = Path(tempfile.mkdtemp(prefix="lesson151-"))
(T / "corpus151.json").write_text(json.dumps({"rows": ROWS, "extractions": {k: {"entities": e, "relations": r} for k, (e, r) in EXTRACTIONS.items()}}), encoding="utf-8")
(T / "lane151.py").write_text(LANE_LIB, encoding="utf-8")
STORE = T / "store151.json"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "GOOGLE_CLOUD_PROJECT": PROJ, "LANE151_CORPUS": str(T / "corpus151.json"), "LANE151_STORE": str(STORE), "PYTHONPATH": str(T)}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


# ------------------------------------------------------------------ the cells
RULES_PY = """import sys
sys.path[:0] = ["services/ingest", "."]
import graph                                                   # the kit's own pipeline; nothing below calls a model
X = graph.GraphExtraction
print(f"extraction: {graph.EXTRACT_MODEL}, entity types {', '.join(graph.Entity.model_fields['type'].annotation.__args__)}")
print(f"resolution: normalise(), then {graph.EMBED_MODEL} cosine >= {graph.RESOLVE_THRESHOLD}")
forms = ["ACME Pvt. Ltd.", "Acme Private Limited", "ACME Inc", "function head", "Function Head", "CFO", "Chief Financial Officer"]
for f in forms:
    print(f"  normalise({f!r:24}) = {graph.normalise(f)!r}")
apart = lambda names: [[1.0 if i == j else 0.0 for j in range(len(names))] for i in range(len(names))]
canon = graph.resolve_entities(forms, apart)                   # an embedding that tells every name apart: only normalise() merges
print("resolve_entities(), with an embedding that tells every name apart:")
for f in forms:
    print(f"  {f!r:24} -> {canon[f]!r}")
ex = [{"chunk_id": "c1", "graph": X.model_validate({"entities": [{"name": "function head", "type": "person"}, {"name": "CFO", "type": "person"},
                                                                 {"name": "Purchase approval", "type": "policy"}],
                                                    "relations": [{"source": "CFO", "target": "Purchase approval", "rel": "APPROVES", "confidence": 0.9},
                                                                  {"source": "CFO", "target": "board", "rel": "REPORTS_TO", "confidence": 0.8}]})},
      {"chunk_id": "c2", "graph": X.model_validate({"entities": [{"name": "Function Head", "type": "person"}, {"name": "Travel reimbursement", "type": "policy"}],
                                                    "relations": [{"source": "Function Head", "target": "Travel reimbursement", "rel": "APPROVES", "confidence": 0.9},
                                                                  {"source": "Function Head", "target": "Function Head", "rel": "IS", "confidence": 0.5}]})}]
names = [e.name for x in ex for e in x["graph"].entities]
canon = graph.resolve_entities(names, apart)
nodes, edges = graph.build_graph(ex, canon)
print("build_graph() on two passages:")
for nid, n in sorted(nodes.items(), key=lambda kv: kv[1]["name"]):
    print(f"  node {n['name']!r:24} {n['kind']:7} id {nid[:12]}...  cited by {sorted(n['chunks'])}")
for (s, d, rel), v in edges.items():
    print(f"  edge {nodes[s]['name']} -[{rel}]-> {nodes[d]['name']}  from {v['chunk_id']}, confidence {v['confidence']}")
print(f"  {sum(len(x['graph'].relations) for x in ex) - len(edges)} relations dropped: 'board' is no entity (dangling), and Function Head -[IS]-> itself")"""

READ_PY = """import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, TENANT = os.environ["PROJECT"], "acme"
db = firestore.Client(project=P)
q = lambda coll: db.collection(coll).where(filter=FieldFilter("tenant_id", "==", TENANT))
nodes = {d.get("node_id"): d.to_dict() for d in q("graph_nodes").stream()}
edges = [d.to_dict() for d in q("graph_edges").stream()]
print(f"tenant {TENANT}: {len(nodes)} nodes, {len(edges)} edges in Firestore")
print("the nodes the most chunks cite:")
for n in sorted(nodes.values(), key=lambda n: (-len(n["chunk_ids"]), n["name"]))[:4]:
    print(f"  {n['name'][:32]:32} {n['kind']:7} {len(n['chunk_ids'])} chunk(s)")
pick = [e for e in edges if "cfo" in (nodes[e["node_id"]]["name"] + nodes[e["dst_id"]]["name"]).lower()] or sorted(edges, key=lambda e: -e["confidence"])
e = pick[0]
src_name, dst_name = nodes[e["node_id"]]["name"], nodes[e["dst_id"]]["name"]
chunk = db.collection("chunks").document(e["chunk_id"]).get().to_dict() or {}
print("one edge, read back with its source chunk:")
print(f"  {src_name} -[{e['rel']}]-> {dst_name}   confidence {e['confidence']}")
version, n = e["chunk_id"].split("#")
print(f"  stated in {version[:17]}...#{n} ({chunk.get('locator')}, {chunk.get('source_uri', '').rsplit('/', 1)[-1]}):")
for line in chunk.get("text", "").splitlines():
    print("    " + line)
text = " ".join(chunk.get("text", "").split()).lower()          # a name may wrap across a line
print(f"  both names in the passage as written: {src_name} {'yes' if src_name.lower() in text else 'NO'}, {dst_name} {'yes' if dst_name.lower() in text else 'NO'}")"""

AUDIT_PY = """import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, TENANT = os.environ["PROJECT"], "acme"
db = firestore.Client(project=P)
rows = [d for d in db.collection("graph_extractions").where(filter=FieldFilter("tenant_id", "==", TENANT)).stream()]
chunks = {d.get("chunk_id"): (db.collection("chunks").document(d.get("chunk_id")).get().to_dict() or {}) for d in rows}
x = next(d.to_dict() for d in rows if chunks[d.get("chunk_id")].get("locator") == "FIN-02")
raw = chunks[x["chunk_id"]]["text"]
text = " ".join(raw.split())                                   # a name may wrap across a line
print(f"the extraction cached for {chunks[x['chunk_id']]['locator']} ({x['model']}), beside its passage:")
for line in raw.splitlines():
    print("  | " + line)
names = [e["name"] for e in x["graph"]["entities"]]
for e in x["graph"]["entities"]:
    print(f"  entity   {e['name']!r:22} {e['type']:7} {'in the passage as written' if e['name'].lower() in text.lower() else 'NOT IN THE PASSAGE'}")
for r in x["graph"]["relations"]:
    ok = r["source"] in names and r["target"] in names
    print(f"  relation {r['source']} -[{r['rel']}]-> {r['target']}  {r['confidence']}  {'both ends are entities' if ok else 'DANGLING: build_graph drops it'}")
stated = sum(e["name"].lower() in text.lower() for e in x["graph"]["entities"])
print(f"{stated} of {len(names)} entity names are in the passage as written; {len(rows)} extractions cached for {TENANT}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


ARGS_DRY, ARGS_BUILD, ARGS_RERUN = "--source hr_policy_2026.md --dry-run", "--source hr_policy_2026.md --rebuild", "--source hr_policy_2026.md"
CELLS = {
    "rules": heredoc(RULES_PY),
    "build": (f'make graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS="{ARGS_DRY}"      # the bill, before any call\n'
              f'make graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS="{ARGS_BUILD}"'),
    "read": heredoc(READ_PY),
    "audit": heredoc(AUDIT_PY) + f'\nmake graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS="{ARGS_RERUN}"      # again: the cache answers',
}

# ---- step 3: the rules, run on the kit
OUT = {"rules": run_cell(RULES_PY, cwd=KIT)}
R3 = OUT["rules"]
assert re.search(r"normalise\('ACME Pvt\. Ltd\.'\s*\) = 'acme'", R3) and re.search(r"normalise\('Acme Private Limited'\s*\) = 'acme'", R3), R3
assert re.search(r"'Chief Financial Officer'\s+-> 'Chief Financial Officer'", R3) and re.search(r"'Function Head'\s+-> 'function head'", R3), R3
assert re.search(r"'Acme Private Limited'\s+-> 'ACME Pvt\. Ltd\.'", R3) and re.search(r"'CFO'\s+-> 'CFO'", R3), R3
assert "2 relations dropped" in R3 and "cited by ['c1', 'c2']" in R3, R3

# ---- steps 4 to 6: the kit's graph.py main(), as make graph runs it, on the stand-in lane
PRELUDE = "import lane151\nlane151.install()\n"


def graph_py(args: str) -> str:
    body = ("import runpy, sys\nsys.path[:0] = ['.', '../..']\n"
            f"sys.argv = ['graph.py', '--project', {PROJ!r}, '--tenant', 'acme', '--backend', 'firestore'] + {args.split()!r}\n"
            "try:\n    runpy.run_path('graph.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n"
            "print('CALLS', dict(lane151.CALLS))\n")
    out = run_cell(body, PRELUDE, cwd=KIT / "services/ingest")
    text, calls = out.rsplit("CALLS ", 1)
    return text, eval(calls)                                                    # noqa: S307 - our own dict repr


dry, dry_calls = graph_py(ARGS_DRY)
built, built_calls = graph_py(ARGS_BUILD)
OUT["build"] = make_echo(ARGS_DRY) + dry + make_echo(ARGS_BUILD) + built
OUT["read"] = run_cell(READ_PY, PRELUDE)
audit = run_cell(AUDIT_PY, PRELUDE)
rerun, rerun_calls = graph_py(ARGS_RERUN)
OUT["audit"] = audit + make_echo(ARGS_RERUN) + rerun
B, RD, AU = OUT["build"], OUT["read"], OUT["audit"]
assert dry == "11 current text chunks for tenant 'acme' from 'hr_policy_2026.md'\n" and not dry_calls, (dry, dry_calls)
assert built_calls == {"extract": 11, "embed": 1} and rerun_calls == {"embed": 1}, (built_calls, rerun_calls)   # the rerun extracts nothing
EXTRACTED = json.loads(next(line for line in built.splitlines() if '"graph_extracted"' in line))
BUILT = json.loads(next(line for line in built.splitlines() if '"graph_built"' in line))
REBUILT = json.loads(next(line for line in rerun.splitlines() if '"graph_built"' in line))
assert (EXTRACTED["chunks"], EXTRACTED["extracted"], EXTRACTED["fresh"]) == (11, 11, 11)
assert json.loads(next(line for line in rerun.splitlines() if '"graph_extracted"' in line))["fresh"] == 0
N_NODES, N_EDGES, N_FORMS = BUILT["nodes"], BUILT["edges"], BUILT["surface_forms"]
assert (N_NODES, N_EDGES) == (25, 15) and (REBUILT["nodes"], REBUILT["edges"]) == (25, 15), (BUILT, REBUILT)
assert f"{N_NODES} nodes, {N_EDGES} edges written for tenant acme (Firestore)" in built and "tenant acme: 0 graph_nodes deleted" in built, built
assert RD.startswith(f"tenant acme: {N_NODES} nodes, {N_EDGES} edges in Firestore\n"), RD
assert "  CFO -[APPROVES_ABOVE_RS_2_00_000]-> Purchase approval   confidence 0.9\n" in RD and "(FIN-02, hr_policy_2026.md):" in RD, RD
assert "both names in the passage as written: CFO yes, Purchase approval yes" in RD, RD
assert "3 of 3 entity names are in the passage as written; 11 extractions cached for acme" in AU, AU

# ---- the panel: the same graph, from the kit's build_graph() over the stand-in's extractions
sys.path[:0] = [str(KIT / "services/ingest")]
import graph as G  # noqa: E402 - the kit's pure passes, for the panel's data
import random  # noqa: E402
order = sorted(HANDBOOK, key=lambda loc: (HANDBOOK[loc][1]["source_uri"], loc, HANDBOOK[loc][0]))   # load_chunks' reading order
EX = [{"chunk_id": HANDBOOK[loc][0], "graph": G.GraphExtraction.model_validate({"entities": EXTRACTIONS[loc][0], "relations": EXTRACTIONS[loc][1]})} for loc in order]
apart = lambda names: [(lambda r: [r.gauss(0, 1) for _ in range(768)])(random.Random("name:" + n)) for n in names]  # noqa: E731 - the stand-in's own vectors
CANON = G.resolve_entities([e.name for x in EX for e in x["graph"].entities], apart)
NODES, EDGES = G.build_graph(EX, CANON)
assert (len(NODES), len(EDGES), len(CANON)) == (N_NODES, N_EDGES, N_FORMS), ((len(NODES), len(EDGES), len(CANON)), (N_NODES, N_EDGES, N_FORMS), BUILT)
LOC = {cid: loc for loc, (cid, _) in HANDBOOK.items()}


def flow(text: str) -> str:
    """The title line, then the clause as one paragraph: a name that wraps a line in the chunk reads, and highlights, whole."""
    head, _, rest = text.partition("\n")
    return head + "\n" + " ".join(rest.split())


FORMS = {}
for form, canonical in CANON.items():
    FORMS.setdefault(canonical, []).append(form)
DROPPED = []
for x in EX:
    for r in x["graph"].relations:
        s, d = CANON.get(r.source), CANON.get(r.target)
        if not s or not d:
            DROPPED.append({"text": f"{r.source} -[{r.rel}]-> {r.target}", "loc": LOC[x["chunk_id"]], "why": f"'{r.target if not d else r.source}' is not an entity in that passage: a dangling edge"})
        elif s == d:
            DROPPED.append({"text": f"{r.source} -[{r.rel}]-> {r.target}", "loc": LOC[x["chunk_id"]], "why": "a node to itself: a self edge"})
assert len(DROPPED) == 2
PANEL = {"edges": [{"src": NODES[s]["name"], "rel": rel, "dst": NODES[d]["name"], "loc": LOC[v["chunk_id"]], "conf": v["confidence"]}
                   for (s, d, rel), v in sorted(EDGES.items(), key=lambda kv: (NODES[kv[0][0]]["name"].lower(), kv[0][2]))],
         "nodes": [{"name": n["name"], "kind": n["kind"], "locs": sorted(LOC[c] for c in n["chunks"]), "forms": sorted(FORMS[n["name"]])}
                   for n in sorted(NODES.values(), key=lambda n: n["name"].lower())],
         "passages": {loc: flow(HANDBOOK[loc][1]["text"]) for loc in HANDBOOK}, "dropped": DROPPED}
assert all(PANEL['passages'][e['loc']].lower().count(e['src'].lower()) or e['src'] in FORMS for e in PANEL['edges'])
MERGED = [n for n in PANEL["nodes"] if len(n["forms"]) > 1]
assert [(n["name"], n["forms"]) for n in MERGED] == [("Earned leave", ["Earned leave", "earned leave"]), ("Notice period", ["Notice period", "notice period"]),
                                                    ("probation", ["Probation", "probation"])], MERGED
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "rules": "run in the operator shell, in the kit (the rules, run; no model, no network)",
    "build": "run in the operator shell, in the kit (the handbook's clauses: a count, then the build)",
    "read": "run in the operator shell, in the kit (reads only)",
    "audit": "run in the operator shell, in the kit (one extraction against its passage; then the build again)",
}
OUT_LABELS = {
    "rules": "(this cell run on the kit's own graph.py)",
    "build": "(the kit's graph.py on a stand-in lane: flash-lite and text-embedding-005 stood in; your counts are your model's)",
    "read": "(the stand-in lane's Firestore, as the kit's build left it)",
    "audit": "(the same stand-ins; the rerun sends nothing to flash-lite)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: every edge with the passage that states it
UI_JS = r"""var root = document.getElementById('gx'); if (!root) return;
  var D = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function marked(text, names){ var box = el('div', 'gx-pass'), low = text.toLowerCase(), i = 0;
    var hits = []; names.forEach(function(n){ var j = low.indexOf(n.toLowerCase()); if (j >= 0) { hits.push([j, j + n.length]); } });
    hits.sort(function(a, b){ return a[0] - b[0]; });
    hits.forEach(function(h){ if (h[0] < i) { return; } box.appendChild(document.createTextNode(text.slice(i, h[0]))); box.appendChild(el('mark', '', text.slice(h[0], h[1]))); i = h[1]; });
    box.appendChild(document.createTextNode(text.slice(i))); return box; }
  function row(out, k, v, cls){ out.appendChild(el('b', '', k)); out.appendChild(el('span', cls || '', v)); }
  function node(name){ return D.nodes.filter(function(n){ return n.name === name; })[0]; }
  function render(){ var v = $('gx-pick').value, out = $('gx-out'), pass = $('gx-text'); out.textContent = ''; pass.textContent = '';
    if (v.charAt(0) === 'e') { var e = D.edges[Number(v.slice(1))], a = node(e.src), b = node(e.dst);
      row(out, 'The edge', e.src + ' -[' + e.rel + ']-> ' + e.dst, 'pass'); row(out, 'Stated in', e.loc + ', confidence ' + e.conf);
      row(out, 'Source node', a.name + ' (' + a.kind + '), cited by ' + a.locs.join(', ') + (a.forms.length > 1 ? '; written as ' + a.forms.join(' / ') : ''));
      row(out, 'Target node', b.name + ' (' + b.kind + '), cited by ' + b.locs.join(', ') + (b.forms.length > 1 ? '; written as ' + b.forms.join(' / ') : ''));
      pass.appendChild(marked(D.passages[e.loc], a.forms.concat(b.forms))); }
    else { var d = D.dropped[Number(v.slice(1))]; row(out, 'Dropped', d.text, 'stop'); row(out, 'Stated in', d.loc); row(out, 'Why', d.why, 'stop');
      pass.appendChild(marked(D.passages[d.loc], [])); } }
  var g1 = el('optgroup', ''); g1.label = 'Edges the build kept'; D.edges.forEach(function(e, i){ var o = el('option', '', e.src + ' -[' + e.rel + ']-> ' + e.dst); o.value = 'e' + i; g1.appendChild(o); });
  var g2 = el('optgroup', ''); g2.label = 'Relations build_graph dropped'; D.dropped.forEach(function(d, i){ var o = el('option', '', d.text); o.value = 'd' + i; g2.appendChild(o); });
  $('gx-pick').appendChild(g1); $('gx-pick').appendChild(g2); $('gx-pick').addEventListener('change', render);
  D.edges.forEach(function(e, i){ if (e.src === 'CFO') { $('gx-pick').value = 'e' + i; } }); render();""" % json.dumps(PANEL)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_NODES": str(N_NODES), "N_EDGES": str(N_EDGES), "N_FORMS": str(N_FORMS), "N_CHUNKS": "11", "N_DROPPED": str(len(DROPPED))}

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
print(f"kit: the rules run from graph.py; the build is the kit's graph.py main() on a stand-in lane | {N_NODES} nodes, {N_EDGES} edges,"
      f" {len(DROPPED)} relations dropped, the CFO edge read back with FIN-02")
