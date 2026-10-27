"""Build lesson 8.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Change a chunker, re-embed and reconcile. The chunk size and overlap are edited in both of the kit's chunkers, the
ingest worker's services/ingest/main.py and its twin shared/documind_corpus.py, to 400/50, and
commands/tests/test_twin_chunker.py holds the two equal; a worker built under an image tag of its own is deployed; the
handbook is re-issued as new bytes and its counts read; the ledger is walked against the bucket and the index counted
against the rows; the handbook's golden rows are judged live; the original tag is deployed again, version 1 reactivated
and the checkout put back.

Computed here, offline, from the kit (Rs 0):
  - the handbook through the kit's chunker at the kit's pair, at 400/50 and at every pair of step 1's explorer, by
    shared/documind_corpus.py and by the worker's own _windows() and _chunk() lifted out of main.py with ast (the two
    held equal at every pair): chunks, the sections cut, the chunks whose text (so whose chunk_hash) the lane already
    holds, the characters embedded, the embedding requests (embed_batches) and the rupees, at rag_scale's dated
    embedding price; and why 599 is the line;
  - step 1's explorer: the kit's chunker ported to JavaScript; node runs the script as shipped over the whole handbook
    at every pair and over the explorer's four sections, and its chunks must be the Python's;
  - the twin test, run on the kit and on copies of its files edited by the page's own sed lines;
  - the measuring cell (step 4) and the planner cell (step 8), run here as the page prints them: services/ingest/
    reconcile.py's plan(), decide_bytes() and drift_of() over a stand-in lane;
  - the run list's rupees, from shared/prices.py, rag-api's config.py, rag_scale and lessons/00-setup/standing_cost.py.
Recorded from the author's lane with pb.recorded(): every cell that reads or changes the lane (RUN_LIST.md says how; the
build holds that file to the page, command for command).

    python pagekit/build.py 8.2
"""
import ast
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules imported below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

sys.path.insert(0, str(HERE.parent))               # lessons/08-ingestion-practical: lesson 8.3's dated module
import rag_scale as rs  # noqa: E402  the embedding price (dated), Indian grouping, and the loader every lesson shares
sc, dc = rs.sc, rs.dc                              # lessons/00-setup/standing_cost.py; shared/documind_corpus.py

LESSON = "8.2"
title = ("<title>Lesson 8.2 Change a chunker, re-embed and reconcile - two lines in two files, one handbook re-issued, "
         "the ledger walked, the old image put back | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
NEW = (400, 50)                                    # the cohort plan's pair, in both twins (plan section 7, wave 4)
LANE_H = 2                                         # the plan's lane hours for this lesson, in batch 3 beside 8.1

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the explorer: a size, an overlap, a section; the handbook's totals and the section's cards */
.ck-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.ck-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.ck-in select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.ck-in input[type=range]{width:100%;min-height:44px;font-size:16px;accent-color:var(--teal);}
.ck-btns{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;}
.ck-btn{font:inherit;font-size:var(--small-size);font-weight:500;min-height:44px;padding:8px 12px;border:1px solid var(--teal);border-radius:8px;background:var(--card);color:var(--teal);cursor:pointer;flex:1 1 160px;-webkit-tap-highlight-color:transparent;}
.ck-btn[aria-pressed="true"]{background:var(--teal);color:#fff;}
.ck-btn:active{transform:scale(.98);}
.ck-sum{font-size:var(--small-size);line-height:1.6;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin:0 0 10px;overflow-wrap:anywhere;}
.ck-out{display:flex;flex-wrap:wrap;gap:8px;}
.ck-card{flex:1 1 220px;min-width:0;border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;border:2px solid var(--teal);background:var(--teal-light);color:var(--navy);overflow-wrap:anywhere;white-space:pre-wrap;}
.ck-card.new{border-color:#d97706;background:#fffbeb;}
.ck-card b{display:block;font-family:var(--mono);font-size:var(--kicker-size);margin-bottom:4px;white-space:normal;}
.ck-ov{background:#bae6fd;border-radius:2px;}
@media (hover:hover) and (pointer:fine){.ck-btn:hover{background:var(--teal-light);}.ck-btn[aria-pressed="true"]:hover{background:var(--teal-dark);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their "
         "own, so point acme at the kit's rows for the duration and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head; step 6 uses both: the shell re-issues the handbook, and your browser reads what "
         "the worker made of it.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)


# ------------------------------------------------------------------ the kit's facts
def read(rel: str) -> str:
    """One kit file's text."""
    return (KIT / rel).read_text(encoding="utf-8")


def isolated_env() -> dict:
    """This process's environment without a Google credential or project: nothing run below may reach a cloud."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT")}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    return env


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


ING, COR, TEST_REL, REC = ("services/ingest/main.py", "shared/documind_corpus.py", "commands/tests/test_twin_chunker.py",
                           "services/ingest/reconcile.py")
MAIN, CORPUS, TEST, RECONCILE = read(ING), read(COR), read(TEST_REL), read(REC)
PAIR_RE = r"^CHUNK_CHARS, CHUNK_OVERLAP = (\d+), (\d+)\b"
KIT_PAIR = tuple(map(int, one(PAIR_RE, MAIN, re.M)))
assert tuple(map(int, one(PAIR_RE, CORPUS, re.M))) == KIT_PAIR == (dc.CHUNK_CHARS, dc.CHUNK_OVERLAP) == (2000, 200)


def line_of(text: str, pattern: str) -> int:
    """The 1-based line a pattern's one match starts on."""
    m = list(re.finditer(pattern, text, re.M))
    assert len(m) == 1, pattern
    return 1 + text[:m[0].start()].count("\n")


MAIN_LINE, CORPUS_LINE = line_of(MAIN, PAIR_RE), line_of(CORPUS, PAIR_RE)
HEADER_RE = 're.sub(r"\\A\\s*<!--.*?-->\\s*", "", '                # both twins drop a leading HTML comment
assert MAIN.count(HEADER_RE) == 1 and CORPUS.count(HEADER_RE) == 1
# the third chunker: what the managed mirror asks of RAG Engine, in tokens (services/ingest/managed.py)
MANAGED_SIZE, MANAGED_OV = map(int, one(r"^CHUNK_SIZE, CHUNK_OVERLAP = (\d+), (\d+)\b", read("services/ingest/managed.py"), re.M))
MAKE = read("Makefile") + "".join("\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert re.search(r"^GIT_SHA\s+\?= \$\(shell git rev-parse --short HEAD", MAKE, re.M)      # a build's tag, by default HEAD's
assert "--substitutions=_IMAGE=$(IMAGE_REPO)/$$svc:$(GIT_SHA)" in MAKE and "IMAGE_REPO = $(REGION)-docker.pkg.dev/$(PROJECT)/documind" in MAKE
L125 = read("commands/lesson-12.5.sh")
assert "--image=${REGION:-us-central1}-docker.pkg.dev/$PROJECT/documind/ingest:$GIT_SHA" in L125
IMAGE = f"asia-south1-docker.pkg.dev/{PROJ}/documind/ingest"
RETENTION = int(one(r"^RETENTION_DAYS\s+\?= (\d+)$", MAKE, re.M))
assert "SERVICES   = ingest api admin ui chat mcp agent" in MAKE and "SCRIPTS    = commands/lesson-12.5.sh" in MAKE
# a full re-embed is not in the kit: INDEXING.md lists it as not yet done, and no make target re-cuts a corpus
assert "- Not yet (the strategy's P2): `make reembed EMBEDDING_VERSION=`" in read("INDEXING.md")
assert not re.search(r"^reembed:", MAKE, re.M)
# the walk's inputs: object names and generations, the ledger's rows, the claims; never the chunker
assert not re.search(r"CHUNK_CHARS|CHUNK_OVERLAP|\b_chunk\(|chunk_document|\b_?windows\(", RECONCILE)
# a hand withdrawal and the walk's retirement remove the retired ids too (13 October 2026), through the worker's own call
assert RECONCILE.count("remove_vectors(index_name, gone)") == 2 and "from indexer import remove_datapoints as remove" in RECONCILE
assert MAIN.count("remove_datapoints(INDEX_NAME, gone[\"retired_ids\"])") == 2
TEST_N = len(re.findall(r"^    def test_\w+\(self\):$", TEST, re.M))
assert TEST_N == 11, TEST_N          # the indented first heading joined the twins' cases on 13 October 2026

# the worker's chunker, lifted out of main.py with ast and run here (importing the worker needs FastAPI and a project)
NS = {"re": re, "hashlib": hashlib}


def lift(rel: str, wanted: set) -> None:
    """Module-level assignments and functions of one kit file, exec'd into NS: the kit's own code, run here."""
    found = set()
    for node in ast.parse(read(rel)).body:
        names = {e.id for t in getattr(node, "targets", []) for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                 if isinstance(e, ast.Name)}
        if isinstance(node, ast.Assign) and names & wanted:
            found |= names & wanted
        elif isinstance(node, ast.FunctionDef) and node.name in wanted:
            found.add(node.name)
        else:
            continue
        exec(compile(ast.Module([node], []), rel, "exec"), NS)
    assert found == wanted, wanted - found


lift("services/ingest/contracts.py", {"_WS", "chunk_hash"})
lift(ING, {"CHUNK_CHARS", "CHUNK_OVERLAP", "_SECTION", "_CODE", "_windows", "_chunk"})

# ------------------------------------------------------------------ the handbook, cut by both twins at every pair
HB_REL = "evals/corpus/acme/hr_policy_2026.md"
HB_BYTES = (KIT / HB_REL).read_bytes()
HB = HB_BYTES.decode("utf-8")
DOC = {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x/acme/hr_policy_2026.md"}


def cut(size: int, overlap: int, text: str = HB) -> list:
    """A text through both twins at one pair, set in memory: the corpus twin's chunks, held equal to the worker's."""
    saved = (dc.CHUNK_CHARS, dc.CHUNK_OVERLAP, NS["CHUNK_CHARS"], NS["CHUNK_OVERLAP"])
    dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = NS["CHUNK_CHARS"], NS["CHUNK_OVERLAP"] = size, overlap
    try:
        ours, worker = dc.chunk_document({**DOC, "text": text}, "acme"), NS["_chunk"](text)
    finally:
        dc.CHUNK_CHARS, dc.CHUNK_OVERLAP, NS["CHUNK_CHARS"], NS["CHUNK_OVERLAP"] = saved
    # the same chunks; a text with neither headings nor form feeds is w<k> to the worker and p1-<k> to the twin, the
    # one locator difference the kit keeps (the twin test pins it)
    assert [(c["locator"], c["text"], c["chunk_hash"]) for c in ours] == \
        [(re.sub(r"\Aw(\d+)\Z", r"p1-\1", c["locator"]), c["text"], c["chunk_hash"]) for c in worker], (size, overlap)
    return ours


BASE = cut(*KIT_PAIR)                              # what the lane holds: version 1 at the kit's pair
HELD = {c["chunk_hash"] for c in BASE}
LENS = {c["locator"]: len(c["text"]) for c in BASE}
GEN = sorted(k for k in LENS if k.startswith("GEN-"))
REAL = [k for k in LENS if k != "preamble" and not k.startswith("GEN-")]
N_HEADINGS = len(dc._SECTION.findall(HB))
assert (len(BASE), N_HEADINGS, len(GEN), len(REAL)) == (283, 282, 272, 10) and (GEN[0], GEN[-1]) == ("GEN-000", "GEN-271")
LONGEST = max(LENS.values())
AT_LONGEST = [k for k, v in LENS.items() if v == LONGEST]
GEN_MIN = min(LENS[k] for k in GEN)
SHORT_MAX = max(LENS[k] for k in LENS if not k.startswith("GEN-"))
assert LONGEST == 599 and len(AT_LONGEST) == 15 and SHORT_MAX < NEW[0] < GEN_MIN       # 400 splits GEN only


def stats(size: int, overlap: int) -> dict:
    """The handbook at one pair: chunks, sections cut, reused against the lane's rows, what is embedded and its price."""
    ch = cut(size, overlap)
    locs = {c["locator"] for c in ch}
    new = [c["text"] for c in ch if c["chunk_hash"] not in HELD]
    sent = sum(map(len, new))
    return {"chunks": len(ch), "cut": sum(1 for k in LENS if f"{k}-1" in locs), "reused": len(ch) - len(new),
            "embedded": len(new), "chars": sent, "requests": len(dc.embed_batches(new)) if new else 0,
            "rupees": round(sent / 1000 * rs.EMBED_USD_1K["online"] * sc.USD_INR, 2),
            "largest": max(len(c["text"]) for c in ch),
            "digest": hashlib.sha256("".join(f"{c['locator']}\x00{c['text']}\x01" for c in ch).encode("utf-8")).hexdigest()}


SIZES = (250, 300, 400, 500, 598, 599, 600, 800, 1000, 1500, 2000)
OVERLAPS = (0, 50, 100, 200)
GRID = [(s, o) for s in SIZES for o in OVERLAPS if o < s // 2]   # an overlap of half a window or more crawls
assert KIT_PAIR in GRID and NEW in GRID
STATS = {f"{s}/{o}": stats(s, o) for s, o in GRID}
S_NEW, S_KIT, S_598 = STATS["400/50"], STATS["2000/200"], STATS["598/50"]
assert (S_NEW["chunks"], S_NEW["reused"], S_NEW["embedded"], S_NEW["cut"]) == (555, 11, 544, 272)
assert all(STATS[k]["embedded"] == 0 and STATS[k]["chunks"] == 283 for k in STATS if int(k.split("/")[0]) >= LONGEST)
assert all(STATS[k]["embedded"] > 0 for k in STATS if int(k.split("/")[0]) < LONGEST)
assert S_598["cut"] == len(AT_LONGEST) and S_598["embedded"] == 2 * len(AT_LONGEST)
C400 = cut(*NEW)
KEPT = [c["locator"] for c in C400 if c["chunk_hash"] in HELD]
assert KEPT == ["preamble"] + REAL and all(len([c for c in C400 if c["locator"].startswith(k + "-")]) == 1 for k in GEN)
BIG = max(C400, key=lambda c: len(c["text"]))
assert BIG["locator"] == AT_LONGEST[0] == "GEN-003" and len(BIG["text"]) == S_NEW["largest"]

# the other Markdown documents: cut at the kit's pair when make ingest-corpus ran, and left so by this lesson
OTHERS = []
for name in ("msa_acme_2026", "inv_2026_0412", "annual_report_2026", "townhall_2026_q1"):
    text = (KIT / f"evals/corpus/acme/{name}.md").read_bytes().decode("utf-8")
    OTHERS.append((name, len(cut(*KIT_PAIR, text)), len(cut(*NEW, text))))
assert [o[1] for o in OTHERS] == [6, 1, 4, 1], OTHERS

# the re-issue: version 1's bytes behind a comment both twins drop, so the counts measure the chunker and nothing else
R4_PREFIX = b"<!-- r4 -->\n"
R4 = R4_PREFIX + HB_BYTES
assert [c["text"] for c in cut(*NEW, R4.decode("utf-8"))] == [c["text"] for c in C400]
V1_KEY, R4_KEY = hashlib.sha256(HB_BYTES).hexdigest(), hashlib.sha256(R4).hexdigest()
assert not re.search(r"effective[ _-]?(?:from|date)?\s*[:=]", R4.decode("utf-8")[:3000], re.I)   # no date: effective_from empty

# the rupees: an embedding at rag_scale's dated price; an answer as lessons 4.3, 4.4 and 11.6 price one (shared/prices.py)
PRICES = read("shared/prices.py")
USD_INR = int(one(r"^USD_INR = (\d+)\b", PRICES, re.M))
FLASH_IN, FLASH_OUT = map(float, one(r'"gemini-3\.6-flash": \(([\d.]+), ([\d.]+)\)', PRICES))
CFG = read("services/rag-api/config.py")
CTX, ANS = int(one(r"max_context_tokens: int = (\d+)", CFG)), int(one(r"max_answer_tokens: int = (\d+)", CFG))
TYPICAL = (2000 * FLASH_IN + 300 * FLASH_OUT) / 1e6 * USD_INR
CAP = (CTX * FLASH_IN + ANS * FLASH_OUT) / 1e6 * USD_INR
assert sc.USD_INR == USD_INR == 85 and rs.EMBED_USD_1K["online"] == 0.000025
GATE = subprocess.run([sys.executable, "evals/run_eval.py", "--source", "hr_policy_2026.md"], cwd=str(KIT),
                      capture_output=True, text=True, encoding="utf-8", env=isolated_env())
EVAL_ROWS = int(one(r"rows citing hr_policy_2026\.md: (\d+) ", GATE.stdout))
assert GATE.returncode == 0 and EVAL_ROWS == 10
TOKEN_RS = len(BIG["text"]) / 1000 * rs.EMBED_USD_1K["online"] * USD_INR
LANE_RS = {k: v * LANE_H * USD_INR for k, v in sc.HOURLY.items()}
CALLS_RS = S_NEW["rupees"] + EVAL_ROWS * TYPICAL + TOKEN_RS
FS_WRITES = 2 * S_NEW["chunks"] + len(BASE)       # the new rows staged, then swapped current; version 1's retired
FS_RS = FS_WRITES * rs.FS_USD["write"] * USD_INR     # Mumbai's price per write, lesson 8.3's table
_IDEM = read("services/ingest/idempotency.py")     # swap_versions(): one update per row flipped, one per row retired
assert 'state[0].update(snap.reference, {"current": True, "staged": firestore.DELETE_FIELD,' in _IDEM
assert "_retire(state, snap, new_doc_key, expire_at, effective_to)" in _IDEM

# ------------------------------------------------------------------ the cells
SED = "sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/CHUNK_CHARS, CHUNK_OVERLAP = 400, 50/'"
SED_RE = (r"^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200", "CHUNK_CHARS, CHUNK_OVERLAP = 400, 50")
GREP_PAIR = f"grep -n \"^CHUNK_CHARS\" {ING} {COR}"
RUN_TEST = f"python -m unittest {TEST_REL} 2>&1 | grep -E \"^(FAIL:|AssertionError|Ran |OK|FAILED)\""
TEST_GREP = re.compile(r"^(FAIL:|AssertionError|Ran |OK|FAILED)")
DESCRIBE = ("gcloud run services describe documind-ingest --region \"$REGION\" --project \"$PROJECT\" "
            "--format='value(spec.template.spec.containers[0].image,status.latestReadyRevisionName)'")
LOG_GREP = "grep -E '^>> |has been deployed|^ERROR'"
CELLS = {
    "test_kit": RUN_TEST,
    "edit_one": f"{SED} {ING}\n{GREP_PAIR}\n{RUN_TEST}",
    "edit_two": f"{SED} {COR}\n{GREP_PAIR}\n{RUN_TEST}\ngit status --short",
    "build": ("[ -s ~/lesson82-orig-sha ] || gcloud run services describe documind-ingest --region \"$REGION\" --project \"$PROJECT\" \\\n"
              "  --format='value(spec.template.spec.containers[0].image)' | sed 's/.*://' > ~/lesson82-orig-sha\n"
              "export ORIG_SHA=\"$(cat ~/lesson82-orig-sha)\"; echo \"the worker runs ingest:$ORIG_SHA; building ingest:$ORIG_SHA-c400\"\n"
              "make build deploy-services PROJECT=$PROJECT SERVICES=ingest SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA-c400 \\\n"
              "  > ~/lesson82-build.log 2>&1\n"
              f"{LOG_GREP} ~/lesson82-build.log\n{DESCRIBE}"),
    "reissue": ("python - <<'PY'\nimport hashlib, os\n"
                f"v1 = open(\"{HB_REL}\", \"rb\").read()\n"
                "r4 = b\"<!-- r4 -->\\n\" + v1                     # version 1's text behind a comment both chunkers drop: new bytes\n"
                "path = os.path.expanduser(\"~/hr_policy_2026_r4.md\")\n"
                "open(path, \"wb\").write(r4)\n"
                "print(path, \"| version key acme_\" + hashlib.sha256(r4).hexdigest()[:12] + \"... | version 1's acme_\" + hashlib.sha256(v1).hexdigest()[:12] + \"...\")\n"
                "PY\n"
                "make reindex PROJECT=$PROJECT TENANT=acme FILE=$HOME/hr_policy_2026_r4.md NAME=hr_policy_2026.md"),
    "back": (f"git checkout -- {ING} {COR}\n{GREP_PAIR}\n{RUN_TEST}\n"
             "git diff --quiet && echo \"the checkout matches the kit again\""),
    "revert": ("export ORIG_SHA=\"$(cat ~/lesson82-orig-sha)\"; echo \"back to ingest:$ORIG_SHA\"\n"
               "make deploy-services PROJECT=$PROJECT SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA > ~/lesson82-revert.log 2>&1\n"
               f"{LOG_GREP} ~/lesson82-revert.log\n{DESCRIBE}\n"
               f"make reindex PROJECT=$PROJECT TENANT=acme FILE={HB_REL}"),
    "reconcile": "make reconcile PROJECT=$PROJECT TENANT_ONLY=acme\nmake sources PROJECT=$PROJECT TENANT_ONLY=acme",
    "eval": "make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md",
}
PY_MEASURE = '''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import documind_corpus as dc
hb = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
doc = {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x/acme/hr_policy_2026.md", "text": hb}
def cut(size, overlap):
    """The handbook through the kit's chunker at one pair, set in memory: the files on disk stay as they are."""
    dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = size, overlap
    return dc.chunk_document(doc, "acme")
now = cut(2000, 200)                                  # what the lane holds: version 1, cut at the kit's pair
held, whole = {c["chunk_hash"] for c in now}, {c["locator"]: len(c["text"]) for c in now}
print("pair      chunks reused embedded characters requests  rupees largest")
for size, overlap in [(2000, 200), (1000, 100), (600, 100), (599, 50), (598, 50), (500, 50), (400, 50), (300, 50)]:
    ch = cut(size, overlap)
    new = [c["text"] for c in ch if c["chunk_hash"] not in held]
    sent = sum(map(len, new))
    print(f"{size:>4}/{overlap:<4} {len(ch):>6} {len(ch) - len(new):>6} {len(new):>8} {sent:>10} {len(dc.embed_batches(new)):>8} "
          f"{sent / 1000 * 0.000025 * 85:>7.2f} {max(len(c['text']) for c in ch):>7}")
c400 = cut(400, 50)
kept = [c["locator"] for c in c400 if c["chunk_hash"] in held]
longest = max(whole.values())
print("left whole at 400/50, so reused:", ", ".join(kept))
print(f"cut at 400/50: {len(whole) - len(kept)} sections of {min(v for k, v in whole.items() if k not in kept)} to {longest} "
      f"characters, into {len(c400) - len(kept)} windows")
print(f"the longest section: {longest} characters ({sum(v == longest for v in whole.values())} of them), so no size from "
      f"{longest} up cuts anything")'''
PY_PLAN = '''import hashlib, sys
sys.path.insert(0, "services/ingest")
from reconcile import plan, decide_bytes, drift_of
v1 = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
sha = {"v1": hashlib.sha256(v1).hexdigest(), "r4": hashlib.sha256(b"<!-- r4 -->\\n" + v1).hexdigest()}
NAME, SID = "acme/hr_policy_2026.md", "acme~hr_policy_2026.md"
def night(what, bucket_gen, bucket_bytes, ledger_gen, ledger_bytes, claimed):
    """One walk over a stand-in lane: the handbook's object against its ledger row, decided by the kit's own planner."""
    row = {"gcs_uri": "gs://uploads/" + NAME, "generation": ledger_gen, "sha256": sha[ledger_bytes],
           "doc_key": "acme_" + sha[ledger_bytes], "status": "indexed"}
    claims = {"acme_" + sha[v]: {"status": "indexed"} for v in claimed}
    act = plan([{"name": NAME, "generation": bucket_gen, "tenant_id": "acme"}], {SID: row}, claims)[0]["action"]
    if act == "check_bytes":                          # the walk hashes the object only when the generations differ
        act = decide_bytes(sha[bucket_bytes], "acme", row, claims)
    print(f"{what:56} {act:9} drift {drift_of({act: 1})}")
night("the re-issue landed: bucket and ledger at generation 3", "3", "r4", "3", "r4", ["v1", "r4"])
night("its push was lost: the ledger still names generation 2", "3", "r4", "2", "v1", ["v1"])
night("the same bytes written again (generation 4)", "4", "r4", "3", "r4", ["v1", "r4"])
night("after the revert: version 1 again, at generation 5", "5", "v1", "5", "v1", ["v1", "r4"])'''
CELLS["measure"] = "python - <<'PY'\n" + PY_MEASURE + "\nPY"
CELLS["plan"] = "python - <<'PY'\n" + PY_PLAN + "\nPY"
PY_REST = '''import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
base = f"https://run.googleapis.com/v2/projects/{P}/locations/{R}/services/documind-ingest"
def get(url):
    """One GET on the Cloud Run Admin API, as JSON."""
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60))
svc = get(base)
print("the template's image:", svc["template"]["containers"][0]["image"].rsplit("/", 1)[-1])
print("latest ready revision:", svc["latestReadyRevision"].rsplit("/", 1)[-1])
for t in svc.get("trafficStatuses", []):
    print(f"traffic: {t.get('percent', 0)}% to {t.get('revision') or 'the latest ready revision'} ({t.get('type', '').rsplit('_', 1)[-1].lower()})")
revisions = sorted(get(base + "/revisions").get("revisions", []), key=lambda r: r["createTime"], reverse=True)
for r in revisions[:3]:
    print(f"  {r['name'].rsplit('/', 1)[-1]:30} {r['createTime'][:19]}  {r['containers'][0]['image'].rsplit('/', 1)[-1]}")'''
PY_TOKENS = '''import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import documind_corpus as dc
dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = 400, 50              # the pair the worker runs now, set in memory
hb = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
chunks = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x", "text": hb}, "acme")
big = max(chunks, key=lambda c: len(c["text"]))
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
url = (f"https://us-central1-aiplatform.googleapis.com/v1/projects/{P}/locations/us-central1"
       "/publishers/google/models/text-embedding-005:predict")
body = {"instances": [{"content": big["text"], "task_type": "RETRIEVAL_DOCUMENT"}], "parameters": {"outputDimensionality": 768}}
req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                             headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req, timeout=60))
e = r["predictions"][0]["embeddings"]
print(f"{big['locator']}: {len(big['text'])} characters; the kit's estimate {len(big['text']) // dc.CHARS_PER_TOKEN} tokens (characters // {dc.CHARS_PER_TOKEN})")
print(f"the model read {e['statistics']['token_count']} tokens, truncated {e['statistics']['truncated']}, "
      f"{len(e['values'])} numbers back; billable characters {r.get('metadata', {}).get('billableCharacterCount')}")'''
PY_ROWS = '''import collections, hashlib, json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, R = os.environ["PROJECT"], os.environ["REGION"]
db = firestore.Client(project=P)
eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
uri = f"gs://{P}-uploads/acme/hr_policy_2026.md"
v1 = "acme_" + hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
rows = [s.to_dict() for s in eq(eq(db.collection("chunks"), "tenant_id", "acme"), "source_uri", uri).stream()]
for (key, current), n in sorted(collections.Counter((r.get("doc_key", "?"), bool(r.get("current"))) for r in rows).items()):
    print(f"  {key[:13]}...  {'current' if current else 'retired':8} {n:>4} rows{'  (version 1)' if key == v1 else ''}")
now = {r["locator"]: r for r in rows if r.get("current")}
old = {r["locator"]: r for r in rows if r.get("doc_key") == v1}
print(f"current: {len(now)} rows, the longest {max(len(r['text']) for r in now.values())} characters")
for loc in ("NP-03", "GEN-003"):
    print(f"  {loc:8} current hash {now[loc]['chunk_hash'][:12]}  version 1's {old[loc]['chunk_hash'][:12]}  "
          f"same vector: {list(now[loc]['embedding']) == list(old[loc]['embedding'])}")
current = int(eq(db.collection("chunks"), "current", True).count().get()[0][0].value)
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
url = f"https://{R}-aiplatform.googleapis.com/v1/projects/{P}/locations/{R}/indexes"
for ix in json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60)).get("indexes", []):
    print(f"index {ix['displayName']}: {int(ix.get('indexStats', {}).get('vectorsCount', 0)):,} vectors; Firestore: {current:,} current rows, all tenants")'''
CELLS["rest"] = "python - <<'PY'\n" + PY_REST + "\nPY"
CELLS["tokens"] = "python - <<'PY'\n" + PY_TOKENS + "\nPY"
CELLS["rows"] = "python - <<'PY'\n" + PY_ROWS + "\nPY"
for name, cell in CELLS.items():
    for t in re.findall(r"\bmake[ \t]+([a-z][a-z0-9_-]*)", cell):
        assert re.search(rf"^{re.escape(t)}:", MAKE, re.M), (name, t)
    for fn in re.findall(r"^def (\w+)\(.*\):\n(?!    \"\"\")", cell, re.M):
        raise AssertionError(f"{name}: {fn}() has no one-line docstring")
assert (f"{SED} {ING}").count("2000, 200") == 1


# ------------------------------------------------------------------ the offline cells, run here as the page prints them
def run_cell(body: str, cwd: Path) -> str:
    """One Python cell's body, run with this interpreter in `cwd`: its stdout and stderr, as the shell shows them."""
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=isolated_env())
    assert r.returncode == 0, r.stderr[-1500:]
    return (r.stdout + r.stderr).rstrip("\n")


MEASURE_OUT = run_cell(PY_MEASURE, KIT)
PLAN_OUT = run_cell(PY_PLAN, KIT)
MEASURED = [tuple(map(int, p)) for p in re.findall(r"\((\d+), (\d+)\)", PY_MEASURE.split("for size, overlap in [", 1)[1].split("]:", 1)[0])]
assert len(MEASURED) == 8 and all(p in GRID for p in MEASURED)          # step 4's table is the cell's eight pairs
for (s, o) in MEASURED:
    v = STATS[f"{s}/{o}"]
    assert f"{s:>4}/{o:<4} {v['chunks']:>6} {v['reused']:>6} {v['embedded']:>8} {v['chars']:>10} {v['requests']:>8} {v['rupees']:>7.2f} {v['largest']:>7}" in MEASURE_OUT, (s, o)

# The three cells that read the lane, run here against stand-in Google APIs (gcloud's token, the REST endpoints,
# Firestore), so their code is tested before a lane runs them. Their stand-in output is asserted, never shown.
STAND_IN = '''import json, os, subprocess, sys, types, urllib.request
FIX = json.load(open(os.environ["LESSON82_FIX"], encoding="utf-8"))
def _run(cmd, *args, **kwargs):
    """gcloud, stood in: an access token and nothing else."""
    assert cmd[:3] == ["gcloud", "auth", "print-access-token"], cmd
    return types.SimpleNamespace(stdout="stand-in-token\\n", stderr="", returncode=0)
subprocess.run = _run
class _Response:
    """A urlopen response holding a JSON body."""
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")
    def read(self, *args):
        """The body."""
        return self.body
def _urlopen(req, timeout=None):
    """Google's REST endpoints, stood in: the fixture's answer per URL; a POST's body must be the fixture's."""
    assert req.get_header("Authorization") == "Bearer stand-in-token" and timeout
    if req.data is not None:
        assert json.loads(req.data) == FIX["bodies"][req.full_url], json.loads(req.data)
    return _Response(FIX["urls"][req.full_url])
urllib.request.urlopen = _urlopen
class _Snap:
    """A Firestore snapshot."""
    def __init__(self, row):
        self.row = row
    def to_dict(self):
        """The row."""
        return dict(self.row)
class _Query:
    """A collection, narrowed by equality filters, as the cells use one."""
    def __init__(self, rows, filters=()):
        self.rows, self.filters = rows, filters
    def where(self, filter=None):
        """One more equality filter."""
        assert filter.op_string == "=="
        return _Query(self.rows, self.filters + (filter,))
    def stream(self):
        """The rows every filter admits."""
        return [_Snap(r) for r in self.rows if all(r.get(f.field_path) == f.value for f in self.filters)]
    def count(self):
        """An aggregation query: get() answers [[result]], the result's value the count."""
        n = len(self.stream())
        return types.SimpleNamespace(get=lambda: [[types.SimpleNamespace(value=n)]])
class _Client:
    """firestore.Client, stood in, over the fixture's rows."""
    def __init__(self, project=None):
        assert project == os.environ["PROJECT"]
    def collection(self, name):
        """One collection's rows."""
        return _Query(FIX["rows"][name])
class _FieldFilter:
    """base_query.FieldFilter: a field, an operator, a value."""
    def __init__(self, field_path, op_string, value):
        self.field_path, self.op_string, self.value = field_path, op_string, value
for name in ("google", "google.cloud", "google.cloud.firestore", "google.cloud.firestore_v1", "google.cloud.firestore_v1.base_query"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["google"].cloud = sys.modules["google.cloud"]
sys.modules["google.cloud"].firestore = sys.modules["google.cloud.firestore"]
sys.modules["google.cloud.firestore"].Client = _Client
sys.modules["google.cloud.firestore_v1.base_query"].FieldFilter = _FieldFilter
'''
RUN_V2 = f"https://run.googleapis.com/v2/projects/{PROJ}/locations/asia-south1/services/documind-ingest"
PREDICT = (f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJ}/locations/us-central1"
           "/publishers/google/models/text-embedding-005:predict")
INDEXES = f"https://asia-south1-aiplatform.googleapis.com/v1/projects/{PROJ}/locations/asia-south1/indexes"
URI = f"gs://{PROJ}-uploads/acme/hr_policy_2026.md"


def vec(h: str) -> list:
    """A stand-in vector: the same chunk_hash, the same numbers, as a carried-over vector is."""
    return [int(h[i:i + 4], 16) for i in range(0, 12, 4)]


def rows_of(chunks: list, key: str, current: bool) -> list:
    """Stand-in chunk rows of one version, as the worker writes them (the fields the cell reads)."""
    return [{"tenant_id": "acme", "source_uri": URI, "doc_key": f"acme_{key}", "current": current, "locator": c["locator"],
             "text": c["text"], "chunk_hash": c["chunk_hash"], "embedding": vec(c["chunk_hash"])} for c in chunks]


OTHER_CURRENT = 7                                  # a stand-in tenant's current rows, so the count is not the handbook's
FIX = {"urls": {
    RUN_V2: {"template": {"containers": [{"image": f"{IMAGE}:COMMIT-c400"}]},
             "latestReadyRevision": f"projects/{PROJ}/locations/asia-south1/services/documind-ingest/revisions/documind-ingest-00012-cat",
             "trafficStatuses": [{"type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST", "percent": 100}]},
    RUN_V2 + "/revisions": {"revisions": [
        {"name": f"projects/{PROJ}/locations/asia-south1/services/documind-ingest/revisions/documind-ingest-0001{i}-x",
         "createTime": f"2026-11-1{i}T10:00:00.000000Z", "containers": [{"image": f"{IMAGE}:{tag}"}]}
        for i, tag in ((0, "COMMIT"), (2, "COMMIT-c400"), (1, "COMMIT"))]},
    PREDICT: {"predictions": [{"embeddings": {"statistics": {"truncated": False, "token_count": 77}, "values": [0.0] * 768}}],
              "metadata": {"billableCharacterCount": 300}},
    INDEXES: {"indexes": [{"displayName": "documind-chunks", "indexStats": {"vectorsCount": str(S_NEW["chunks"] + OTHER_CURRENT)}}]}},
    "bodies": {PREDICT: {"instances": [{"content": BIG["text"], "task_type": "RETRIEVAL_DOCUMENT"}],
                         "parameters": {"outputDimensionality": 768}}},
    "rows": {"chunks": rows_of(C400, R4_KEY, True) + rows_of(BASE, V1_KEY, False)
             + [{"tenant_id": "zeta", "current": True, "text": "x"} for _ in range(OTHER_CURRENT)]}}


def stand_in(body: str) -> str:
    """One lane cell's body after the stand-ins, run with this interpreter in the kit: what it would print."""
    tmp = Path(tempfile.mkdtemp(prefix="lesson82_fix_"))
    try:
        (tmp / "fix.json").write_text(json.dumps(FIX), encoding="utf-8")
        env = {**isolated_env(), "LESSON82_FIX": str(tmp / "fix.json"), "PROJECT": PROJ, "REGION": "asia-south1"}
        r = subprocess.run([sys.executable, "-"], input=STAND_IN + body, cwd=str(KIT), capture_output=True, text=True,
                           encoding="utf-8", env=env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-1500:]
    return r.stdout


SI_REST, SI_TOKENS, SI_ROWS = stand_in(PY_REST), stand_in(PY_TOKENS), stand_in(PY_ROWS)
assert SI_REST.splitlines()[:3] == ["the template's image: ingest:COMMIT-c400", "latest ready revision: documind-ingest-00012-cat",
                                    "traffic: 100% to the latest ready revision (latest)"], SI_REST
assert [ln.split()[-1] for ln in SI_REST.splitlines()[3:]] == ["ingest:COMMIT-c400", "ingest:COMMIT", "ingest:COMMIT"], SI_REST
assert SI_TOKENS.splitlines() == [
    f"{BIG['locator']}: {len(BIG['text'])} characters; the kit's estimate {len(BIG['text']) // dc.CHARS_PER_TOKEN} tokens (characters // {dc.CHARS_PER_TOKEN})",
    "the model read 77 tokens, truncated False, 768 numbers back; billable characters 300"], SI_TOKENS
assert SI_ROWS.splitlines() == [
    f"  acme_{R4_KEY[:8]}...  current   {S_NEW['chunks']} rows", f"  acme_{V1_KEY[:8]}...  retired   {len(BASE)} rows  (version 1)",
    f"current: {S_NEW['chunks']} rows, the longest {S_NEW['largest']} characters",
    f"  NP-03    current hash {LENS and [c for c in C400 if c['locator'] == 'NP-03'][0]['chunk_hash'][:12]}  version 1's "
    f"{[c for c in BASE if c['locator'] == 'NP-03'][0]['chunk_hash'][:12]}  same vector: True",
    f"  {BIG['locator']:8} current hash {BIG['chunk_hash'][:12]}  version 1's "
    f"{[c for c in BASE if c['locator'] == BIG['locator']][0]['chunk_hash'][:12]}  same vector: False",
    f"index documind-chunks: {S_NEW['chunks'] + OTHER_CURRENT:,} vectors; Firestore: {S_NEW['chunks'] + OTHER_CURRENT:,} current rows, all tenants"], SI_ROWS
assert f"{NEW[0]}/{NEW[1]:<4} {S_NEW['chunks']:>6} {S_NEW['reused']:>6} {S_NEW['embedded']:>8} {S_NEW['chars']:>10}" in MEASURE_OUT
assert "left whole at 400/50, so reused: " + ", ".join(KEPT) in MEASURE_OUT
assert [ln.split()[-3] for ln in PLAN_OUT.splitlines()] == ["ok", "reingest", "touch", "ok"], PLAN_OUT
assert [int(ln.split()[-1]) for ln in PLAN_OUT.splitlines()] == [0, 1, 0, 0], PLAN_OUT

TWIN_FILES = [TEST_REL, ING, "services/ingest/contracts.py", COR] + \
    [p.relative_to(KIT).as_posix() for p in sorted((KIT / "evals" / "corpus").glob("*/*.md"))]


def twin_test(edited: list) -> tuple:
    """The twin test on a copy of the files it reads, with `edited` given the page's sed line: (exit code, grep's lines,
    grep -n's lines for the two pairs)."""
    tmp = Path(tempfile.mkdtemp(prefix="lesson82_"))
    try:
        for rel in TWIN_FILES:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(KIT / rel, tmp / rel)
        for rel in edited:
            text = (tmp / rel).read_bytes().decode("utf-8")
            new, n = re.subn(SED_RE[0], SED_RE[1], text, flags=re.M)        # sed's s///, line by line: one line matches
            assert n == 1, rel
            (tmp / rel).write_bytes(new.encode("utf-8"))
        grep_n = [f"{rel}:{i}:{ln}" for rel in (ING, COR)
                  for i, ln in enumerate((tmp / rel).read_bytes().decode("utf-8").splitlines(), 1) if ln.startswith("CHUNK_CHARS")]
        r = subprocess.run([sys.executable, "-m", "unittest", TEST_REL], cwd=str(tmp), capture_output=True, text=True,
                           encoding="utf-8", env=isolated_env())
        lines = [re.sub(r"^Ran (\d+) tests in [\d.]+s$", r"Ran \1 tests in ...s", ln)
                 for ln in (r.stdout + r.stderr).splitlines() if TEST_GREP.search(ln)]
        return r.returncode, lines, grep_n
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


T_KIT, T_ONE, T_TWO = twin_test([]), twin_test([ING]), twin_test([ING, COR])
assert T_KIT[0] == 0 and T_KIT[1] == [f"Ran {TEST_N} tests in ...s", "OK"], T_KIT
assert T_TWO[0] == 0 and T_TWO[1] == T_KIT[1], T_TWO
assert T_ONE[0] == 1 and T_ONE[1][-1] == "FAILED (failures=3)" and any("a chunker change edits both lines" in ln for ln in T_ONE[1])
assert T_ONE[2] == [f"{ING}:{MAIN_LINE}:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50",
                    f"{COR}:{CORPUS_LINE}:" + CORPUS.splitlines()[CORPUS_LINE - 1]]
_first = [re.match(r"AssertionError: (\S+): (\d+) chunks from services/ingest/main\.py, (\d+) from shared/documind_corpus\.py$", ln)
          for ln in T_ONE[1]]
_first = [m for m in _first if m][0]                # the first text the corpus test found cut two ways
FIRST_DOC, FIRST_ONE, FIRST_KIT = _first.group(1), int(_first.group(2)), int(_first.group(3))
assert FIRST_ONE > FIRST_KIT
OUT = {"test_kit": "\n".join(T_KIT[1]),
       "edit_one": "\n".join(T_ONE[2] + T_ONE[1]),
       "edit_two": "\n".join(T_TWO[2] + T_TWO[1] + [f" M {ING}", f" M {COR}"]),          # git's short form for two edits
       "back": "\n".join(T_KIT[2] + T_KIT[1] + ["the checkout matches the kit again"]),
       "measure": MEASURE_OUT, "plan": PLAN_OUT}

# ------------------------------------------------------------------ step 1's explorer: the kit's chunker, ported
SAMPLES = ["NP-03", "LV-07", "GEN-007", BIG["locator"]]
_heads = list(dc._SECTION.finditer(HB))


def section_text(loc: str) -> tuple:
    """One section of the handbook as the file holds it, from its heading line to the next heading, and its title."""
    for n, h in enumerate(_heads):
        title = h.group(1).strip()
        code = dc._CODE.match(title)
        if (code.group(1) if code else f"s{n + 1}") == loc:
            return HB[h.start(): _heads[n + 1].start() if n + 1 < len(_heads) else len(HB)].strip(), title
    raise KeyError(loc)


DATA = {"sizes": SIZES, "overlaps": OVERLAPS, "kit": KIT_PAIR, "lesson": NEW, "sections_total": len(BASE),
        "stats": {k: {f: v[f] for f in ("chunks", "cut", "reused", "embedded", "chars", "requests", "rupees", "largest")}
                  for k, v in STATS.items()},
        "sections": {loc: section_text(loc)[0] for loc in SAMPLES}}
CK_JS = r"""var D = __DATA__;
/* the kit's chunker, ported: shared/documind_corpus.py's windows() and chunk_document() (the worker's _windows() and
   _chunk() cut the same texts), with Python's whitespace (str.strip, re's \s) and str.rfind's bounds */
var WS = '[\\t\\n\\x0b\\x0c\\r \\x1c-\\x1f\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
var LEAD = new RegExp('^' + WS + '+'), TRAIL = new RegExp(WS + '+$'), RUNS = new RegExp(WS + '+', 'g');
var HEADER = new RegExp('^' + WS + '*<!--[\\s\\S]*?-->' + WS + '*');
var HEAD = /^## +([\s\S]+?) *$/, CODE = /^([A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,6}){1,2})\b/;
function strip(s){ return s.replace(LEAD, '').replace(TRAIL, ''); }
function key(t){ return strip(t.replace(RUNS, ' ')); }          /* chunk_hash()'s input: equal keys, equal hashes */
function windows(text, n, o){
  text = strip(text);
  var out = [], start = 0;
  while (start < text.length){
    var end = Math.min(text.length, start + n), lo = start + Math.floor(n / 2);
    if (end < text.length && end - 2 >= lo){
      var cut = text.lastIndexOf('. ', end - 2);                 /* text.rfind(". ", lo, end) */
      if (cut >= lo) { end = cut + 1; }
    }
    var raw = text.slice(start, end), piece = strip(raw);
    if (piece) { out.push({text: piece, start: start + raw.length - raw.replace(LEAD, '').length}); }
    if (end >= text.length) { break; }
    start = Math.max(end - o, start + 1);
  }
  return out;
}
function chunk(text, n, o){
  text = text.replace(HEADER, '');
  var heads = [], p = 0, out = [];
  text.split('\n').forEach(function(line){ var m = HEAD.exec(line); if (m) { heads.push({start: p, end: p + line.length, title: strip(m[1])}); } p += line.length + 1; });
  function add(prefix, ws){ ws.forEach(function(w, k){ out.push({loc: prefix + (k ? '-' + k : ''), text: w.text, start: w.start}); }); }
  if (heads.length){
    add('preamble', windows(text.slice(0, heads[0].start), n, o));
    heads.forEach(function(h, j){
      var body = strip(text.slice(h.end, j + 1 < heads.length ? heads[j + 1].start : text.length)), c = CODE.exec(h.title);
      add(c ? c[1] : 's' + (j + 1), windows(h.title + '\n' + body, n, o));
    });
  } else {
    text.split('\f').forEach(function(page, i){ windows(page, n, o).forEach(function(w, k){ out.push({loc: 'p' + (i + 1) + '-' + k, text: w.text, start: w.start}); }); });
  }
  return out;
}
/* what the explorer shows: the whole handbook's totals (computed with the kit when the page was built, and checked
   against this script) and one section's chunks, each kept (the text the lane holds, so its vector) or new */
function fmt(n){ return Number(n).toLocaleString('en-IN'); }
function summary(size, ov){
  var s = D.stats[size + '/' + ov], k = D.stats[D.kit[0] + '/' + D.kit[1]];
  if (!s.embedded) {
    return 'At ' + size + '/' + ov + ' every section of the handbook stays whole: the same ' + s.chunks + ' chunks the lane holds, ' +
      'every one reused, nothing embedded. A re-issue at this size would change the version key and nothing else.';
  }
  return 'At ' + size + '/' + ov + ' the handbook makes ' + fmt(s.chunks) + ' chunks (' + k.chunks + ' at the kit\'s ' + D.kit[0] + '/' +
    D.kit[1] + '). ' + s.reused + ' keep their vectors and ' + fmt(s.embedded) + ' are embedded again: ' + fmt(s.chars) +
    ' characters in ' + s.requests + ' request' + (s.requests === 1 ? '' : 's') + ', about Rs ' + s.rupees.toFixed(2) + '. ' +
    s.cut + ' of the ' + D.sections_total + ' sections are cut, and the largest chunk is ' + s.largest + ' characters.';
}
function cards(loc, size, ov){
  var held = {}, prev = null;
  chunk(D.sections[loc], D.kit[0], D.kit[1]).forEach(function(c){ held[key(c.text)] = true; });
  return chunk(D.sections[loc], size, ov).map(function(c){
    var overlap = prev ? Math.max(0, Math.min(c.text.length, prev.start + prev.text.length - c.start)) : 0;
    prev = c;
    return {loc: c.loc, len: c.text.length, reused: !!held[key(c.text)], overlap: overlap, text: c.text};
  });
}
window.__ck = {chunk: chunk, key: key, summary: summary, cards: cards};
var root = document.getElementById('ck'); if (!root) { return; }
var size = document.getElementById('ck-size'), sizeV = document.getElementById('ck-size-v'), ovSel = document.getElementById('ck-ov'),
    sec = document.getElementById('ck-sec'), sum = document.getElementById('ck-sum'), out = document.getElementById('ck-out'),
    kitB = document.getElementById('ck-kit'), lesB = document.getElementById('ck-lesson');
function valid(s, o){ return o < Math.floor(s / 2); }
function render(){
  var s = D.sizes[parseInt(size.value, 10)], o = parseInt(ovSel.value, 10);
  Array.prototype.forEach.call(ovSel.options, function(opt){ opt.disabled = !valid(s, parseInt(opt.value, 10)); });
  if (!valid(s, o)) {
    for (var i = D.overlaps.length - 1; i >= 0; i--) { if (valid(s, D.overlaps[i])) { o = D.overlaps[i]; ovSel.value = String(o); break; } }
  }
  sizeV.textContent = s;
  kitB.setAttribute('aria-pressed', String(s === D.kit[0] && o === D.kit[1]));
  lesB.setAttribute('aria-pressed', String(s === D.lesson[0] && o === D.lesson[1]));
  sum.textContent = summary(s, o);
  out.textContent = '';
  cards(sec.value, s, o).forEach(function(c){
    var card = document.createElement('div'), b = document.createElement('b');
    card.className = 'ck-card' + (c.reused ? '' : ' new');
    b.textContent = c.loc + ' · ' + c.len + ' characters · ' + (c.reused ? 'keeps its vector' : 'embedded again');
    card.appendChild(b);
    if (c.overlap) { var m = document.createElement('span'); m.className = 'ck-ov'; m.textContent = c.text.slice(0, c.overlap); card.appendChild(m); }
    card.appendChild(document.createTextNode(c.text.slice(c.overlap)));
    out.appendChild(card);
  });
}
function choose(s, o){ size.value = String(D.sizes.indexOf(s)); ovSel.value = String(o); render(); }
size.addEventListener('input', render);
ovSel.addEventListener('change', render);
sec.addEventListener('change', render);
kitB.addEventListener('click', function(){ choose(D.kit[0], D.kit[1]); });
lesB.addEventListener('click', function(){ choose(D.lesson[0], D.lesson[1]); });
choose(D.lesson[0], D.lesson[1]);"""
SHIPPED = CK_JS.replace("__DATA__", json.dumps(DATA, separators=(",", ":"))).replace("</", "<\\/")   # nothing closes the script early
JS = "<script>\n(function(){\n'use strict';\n" + SHIPPED + "\n})();\n</script>\n"
assert "<div" not in JS and "</div" not in JS                 # the page's div balance is counted over the whole file
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"     # node runs the script as shipped
        "(new Function('window', 'document', " + json.dumps("'use strict';\n" + SHIPPED) + "))(window, document);\n"
        "var crypto = require('crypto'), input = JSON.parse(require('fs').readFileSync(0, 'utf8')), ck = window.__ck;\n"
        "var held = {}, stats = {}, sections = {}, cards = {}, sums = {};\n"
        "ck.chunk(input.hb, input.kit[0], input.kit[1]).forEach(function(c){ held[ck.key(c.text)] = true; });\n"
        "input.pairs.forEach(function(p){ var k = p[0] + '/' + p[1], cs = ck.chunk(input.hb, p[0], p[1]), h = crypto.createHash('sha256'), reused = 0, sent = 0;\n"
        "  cs.forEach(function(c){ h.update(c.loc + '\\u0000' + c.text + '\\u0001', 'utf8'); if (held[ck.key(c.text)]) { reused++; } else { sent += c.text.length; } });\n"
        "  stats[k] = [cs.length, h.digest('hex'), reused, sent]; sums[k] = ck.summary(p[0], p[1]);\n"
        "  input.order.forEach(function(loc){ sections[loc + ' ' + k] = ck.chunk(input.sections[loc], p[0], p[1]).map(function(c){ return [c.loc, c.text]; });\n"
        "    cards[loc + ' ' + k] = ck.cards(loc, p[0], p[1]).map(function(c){ return [c.loc, c.reused, c.overlap]; }); }); });\n"
        "process.stdout.write(JSON.stringify({stats: stats, sections: sections, cards: cards, sums: sums}));\n")
_nd = Path(tempfile.mkdtemp(prefix="lesson82_node_"))
try:
    (_nd / "check.js").write_text(NODE, encoding="utf-8")
    node = subprocess.run(["node", str(_nd / "check.js")], capture_output=True, text=True, encoding="utf-8",
                          input=json.dumps({"hb": HB, "kit": KIT_PAIR, "pairs": GRID, "order": SAMPLES, "sections": DATA["sections"]}))
finally:
    shutil.rmtree(_nd, ignore_errors=True)
assert node.returncode == 0, node.stderr[-1200:]
NODE_OUT = json.loads(node.stdout)


def py_summary(size: int, overlap: int) -> str:
    """The explorer's line for one pair, written here from the same totals: the page's text before the script runs."""
    s, k = STATS[f"{size}/{overlap}"], S_KIT
    if not s["embedded"]:
        return (f"At {size}/{overlap} every section of the handbook stays whole: the same {s['chunks']} chunks the lane holds, "
                "every one reused, nothing embedded. A re-issue at this size would change the version key and nothing else.")
    return (f"At {size}/{overlap} the handbook makes {rs.group(s['chunks'])} chunks ({k['chunks']} at the kit's {KIT_PAIR[0]}/"
            f"{KIT_PAIR[1]}). {s['reused']} keep their vectors and {rs.group(s['embedded'])} are embedded again: "
            f"{rs.group(s['chars'])} characters in {s['requests']} request{'' if s['requests'] == 1 else 's'}, about Rs "
            f"{s['rupees']:.2f}. {s['cut']} of the {len(BASE)} sections are cut, and the largest chunk is {s['largest']} characters.")


for (s, o) in GRID:
    k, v = f"{s}/{o}", STATS[f"{s}/{o}"]
    assert NODE_OUT["stats"][k] == [v["chunks"], v["digest"], v["reused"], v["chars"]], k
    assert NODE_OUT["sums"][k] == py_summary(s, o), (k, NODE_OUT["sums"][k])
    whole = cut(s, o)
    for loc in SAMPLES:
        mine = [[c["locator"], c["text"]] for c in whole if c["locator"] == loc or c["locator"].startswith(loc + "-")]
        assert NODE_OUT["sections"][f"{loc} {k}"] == mine, (loc, k)
        kept = [[c["locator"], c["chunk_hash"] in HELD] for c in whole if c["locator"] == loc or c["locator"].startswith(loc + "-")]
        assert [c[:2] for c in NODE_OUT["cards"][f"{loc} {k}"]] == kept, (loc, k)
big_cards = NODE_OUT["cards"][f"{BIG['locator']} {NEW[0]}/{NEW[1]}"]
assert [c[1] for c in big_cards] == [False, False] and big_cards[0][2] == 0 and 0 < big_cards[1][2] <= NEW[1]
assert NODE_OUT["cards"][f"NP-03 {NEW[0]}/{NEW[1]}"] == [["NP-03", True, 0]]
SIZE_IDX = SIZES.index(NEW[0])
OPT_OV = "".join(f'<option value="{o}"{" selected" if o == NEW[1] else ""}{" disabled" if o >= NEW[0] // 2 else ""}>{o}</option>'
                 for o in OVERLAPS)
OPT_SEC = "".join(f'<option value="{loc}"{" selected" if loc == BIG["locator"] else ""}>{loc}, '
                  f'{html.escape(section_text(loc)[1].split(" ", 2)[-1])} ({LENS[loc]} characters)</option>' for loc in SAMPLES)
assert "—" not in OPT_SEC                                  # the titles' dash stays out of the page's own text

# ------------------------------------------------------------------ the kit's code, verbatim
EXCERPTS = {
    "pair_main": ("services/ingest/main.py - the worker's pair, and the comment above it",
                  block(ING, "# 4.1's chunker, the shape every lesson's corpus has", n=3)),
    "pair_corpus": ("shared/documind_corpus.py - the twin's pair, inside the block the notebooks paste",
                    block(COR, "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200", n=1)),
    "windows": ("services/ingest/main.py - _windows(): where the two numbers are used", block(ING, "def _windows(", end="def _chunk(")),
    "header_main": ("services/ingest/main.py - the first line of _chunk(): a leading comment is not content",
                    block(ING, HEADER_RE, n=1)),
    "header_corpus": ("shared/documind_corpus.py - the same line in chunk_document()", block(COR, HEADER_RE, n=1)),
    "test_pair": ("commands/tests/test_twin_chunker.py - the two numbers, read from each file's own line",
                  block(TEST_REL, "    def test_one_size_and_one_overlap(self):", n=6)),
    "test_diff": ("commands/tests/test_twin_chunker.py - differences(): the same chunks, beside the two differences the kit keeps",
                  block(TEST_REL, "def differences(", end="def read(")),
    "carry": ("services/ingest/indexer.py - the carry-over's test: a vector is lent only to the same text, made the same way",
              block("services/ingest/indexer.py", "def document_embedding_matches(", end="def plan_carry_over(")),
    "deploy_image": ("commands/lesson-12.5.sh - the deploy names the image by its tag",
                     block("commands/lesson-12.5.sh", "gcloud run deploy documind-ingest", n=2)),
    "build_tag": ("Makefile - the tag a build pushes: GIT_SHA, by default the checkout's HEAD",
                  block("Makefile", "GIT_SHA       ?=", n=1)),
    "walk_plan": ("services/ingest/reconcile.py - plan(): a generation the ledger holds is ok, any other is hashed",
                  block(REC, "        elif str(row.get(\"generation\")) != str(o[\"generation\"]):", n=5)),
    "decide": ("services/ingest/reconcile.py - decide_bytes() and drift_of()", block(REC, "def decide_bytes(", end="def expired(")),
    "retire_branch": ("services/ingest/reconcile.py - a hand withdrawal: rows retired, the mirror told, the tombstone, the ids out of the index",
                      block(REC, "        gone = retire_previous(db, tenant, uri, None, expire_at=expire_at)", n=5)),
}
for name, (label, code) in EXCERPTS.items():
    assert code.strip(), name
assert "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200" in EXCERPTS["pair_main"][1] and "start = max(end - CHUNK_OVERLAP" in EXCERPTS["windows"][1]
assert "a chunker change edits both lines" in EXCERPTS["test_pair"][1] and "w\\1" in EXCERPTS["test_diff"][1]
assert "document_embedding_matches(row)" in EXCERPTS["carry"][1] and "$GIT_SHA" in EXCERPTS["deploy_image"][1]
assert EXCERPTS["walk_plan"][1].count("check_bytes") == 1 and "drift" in EXCERPTS["decide"][1]
assert "mirror.retired(" in EXCERPTS["retire_branch"][1] and EXCERPTS["retire_branch"][1].rstrip().endswith("remove_vectors(index_name, gone)")
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ windows of commands and of output
def code_win(label: str, code: str) -> str:
    """A bash window: the label says where it runs, the copy button copies the block whole."""
    return ('<div class="cw"><div class="ch-bar"><span>' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_win(label: str, text: str) -> str:
    """An output window: read only, no copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text, quote=False) + "</pre></div>\n")


RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("build_deploy", "reindex", "rest_revisions", "token_check", "reconcile", "index_vs_ledger", "eval_live", "revert")}
WIN = {
    "W_TEST_KIT": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (no credentials, no cost)", CELLS["test_kit"])
    + out_win("expected", OUT["test_kit"]),
    "W_MEASURE": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's own chunker, Rs 0)", CELLS["measure"])
    + out_win("expected", OUT["measure"]),
    "W_EDIT_ONE": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (one twin only, on purpose)", CELLS["edit_one"])
    + out_win("expected (the time differs)", OUT["edit_one"]),
    "W_EDIT_TWO": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (the other twin)", CELLS["edit_two"])
    + out_win("expected (the time differs)", OUT["edit_two"]),
    "W_BUILD": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (a Cloud Build, then one deploy: about ten minutes)", CELLS["build"])
    + out_win("expected (recorded on the author's lane)", RECORDED["build_deploy"]),
    "W_REISSUE": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (writes the new bytes to your home directory, then one re-issue)", CELLS["reissue"])
    + out_win("expected (recorded on the author's lane)", RECORDED["reindex"]),
    "W_REST": code_win("bash &mdash; run in the operator shell (a Python cell: two GETs on the Cloud Run Admin API)", CELLS["rest"])
    + out_win("expected (recorded on the author's lane)", RECORDED["rest_revisions"]),
    "W_TOKENS": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (a Python cell: one embedding, a fraction of a paisa)", CELLS["tokens"])
    + out_win("expected (recorded on the author's lane)", RECORDED["token_check"]),
    "W_PLAN": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's planner on a stand-in, Rs 0)", CELLS["plan"])
    + out_win("expected", OUT["plan"]),
    "W_RECONCILE": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (the plan only: nothing is applied)", CELLS["reconcile"])
    + out_win("expected (recorded on the author's lane)", RECORDED["reconcile"]),
    "W_ROWS": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (a Python cell: Firestore reads, one count, one GET)", CELLS["rows"])
    + out_win("expected (recorded on the author's lane)", RECORDED["index_vs_ledger"]),
    "W_EVAL": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (ten questions; a few rupees)", CELLS["eval"])
    + out_win("expected (recorded on the author's lane)", RECORDED["eval_live"]),
    "W_REVERT": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (one deploy, no build; then version 1 again)", CELLS["revert"])
    + out_win("expected (recorded on the author's lane)", RECORDED["revert"]),
    "W_BACK": code_win("bash &mdash; run in the operator shell, in $DEMO_ROOT (the checkout put back)", CELLS["back"])
    + out_win("expected (the time differs)", OUT["back"]),
}

# ------------------------------------------------------------------ the run list holds the page's commands
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for k in ("build", "reissue", "rest", "tokens", "reconcile", "rows", "eval", "revert", "edit_one", "edit_two", "back"):
    assert CELLS[k] in RUN_LIST, f"RUN_LIST.md's copy of the {k} cell is not the page's"
for k in RECORDED:
    assert f"`data/{k}.txt`" in RUN_LIST, k
for figure in (f"Rs {S_NEW['rupees']:.2f}", f"Rs {TYPICAL:.2f}", f"Rs {CAP:.2f}", f"Rs {EVAL_ROWS * TYPICAL:.2f}",
               f"Rs {EVAL_ROWS * CAP:.2f}", f"Rs {LANE_RS['small']:.2f}", f"Rs {LANE_RS['medium']:.2f}",
               f"Rs {sc.HOURLY['small'] * USD_INR:.2f}", f"Rs {sc.HOURLY['medium'] * USD_INR:.2f}", f"Rs {CALLS_RS:.2f}",
               f"acme_{R4_KEY[:12]}", f"acme_{V1_KEY[:12]}", f"{S_NEW['chunks']} chunks", f"Rs {FS_RS:.2f}",
               f"{rs.group(S_NEW['chars'])} characters", f"{S_NEW['embedded']} chunks embedded", f"{len(BIG['text'])} characters"):
    assert figure in RUN_LIST, figure


# ------------------------------------------------------------------ the numbers the prose states
def g(n: int) -> str:
    """An integer grouped the Indian way, as lesson 8.3 groups them."""
    return rs.group(n)


def row(*cells: str, labels=()) -> str:
    """One table row; every cell after the first carries its data-label for the phone layout."""
    return "<tr><td>" + cells[0] + "</td>" + "".join(f'<td data-label="{l}">{c}</td>' for l, c in zip(labels, cells[1:])) + "</tr>"


PAIR_ROWS = "\n".join(
    row(f"{s}/{o}", str(v["chunks"]), str(v["cut"]), str(v["reused"]), str(v["embedded"]), g(v["chars"]),
        f"Rs {v['rupees']:.2f}", labels=("Chunks", "Sections cut", "Reused", "Embedded", "Characters", "Rupees"))
    for (s, o), v in ((p, STATS[f"{p[0]}/{p[1]}"]) for p in MEASURED))
OTHER_ROWS = "\n".join(row(f"<code>acme/{n}.md</code>", str(a), str(b), labels=("At 2000/200, on your lane", "At 400/50, if re-issued"))
                       for n, a, b in OTHERS)
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 10: "ten", 11: "eleven", 15: "fifteen"}
VALUES = {
    "KIT_PAIR": f"{KIT_PAIR[0]}/{KIT_PAIR[1]}", "KIT_CHARS": g(KIT_PAIR[0]), "KIT_OV": str(KIT_PAIR[1]),
    "NEW_PAIR": f"{NEW[0]}/{NEW[1]}", "NEW_CHARS": str(NEW[0]), "NEW_OV": str(NEW[1]),
    "MAIN_LINE": str(MAIN_LINE), "CORPUS_LINE": str(CORPUS_LINE), "N_SECTIONS": str(len(BASE)), "N_HEADINGS": str(N_HEADINGS),
    "N_REAL": str(len(REAL)), "N_REAL_W": WORDS[len(REAL)], "N_GEN": str(len(GEN)), "GEN_FIRST": GEN[0], "GEN_LAST": GEN[-1],
    "GEN_MIN": str(GEN_MIN), "SHORT_MAX": str(SHORT_MAX), "LONGEST": str(LONGEST), "N_LONGEST": str(len(AT_LONGEST)),
    "N_LONGEST_W": WORDS[len(AT_LONGEST)], "LONGEST_EX": AT_LONGEST[0], "LONGEST_LIST": ", ".join(AT_LONGEST[:3]) + " and twelve more",
    "N400": str(S_NEW["chunks"]), "R400": str(S_NEW["reused"]), "R400_W": WORDS[S_NEW["reused"]], "E400": str(S_NEW["embedded"]),
    "CH400": g(S_NEW["chars"]), "Q400": str(S_NEW["requests"]), "Q400_W": WORDS[S_NEW["requests"]], "RS400": f"{S_NEW['rupees']:.2f}",
    "BIG400": str(S_NEW["largest"]), "BIG_LOC": BIG["locator"], "BIG_EST": str(len(BIG["text"]) // dc.CHARS_PER_TOKEN),
    "CPT": str(dc.CHARS_PER_TOKEN), "CUT400": str(S_NEW["cut"]), "WIN400": str(S_NEW["embedded"]),
    "N598": str(S_598["chunks"]), "R598": str(S_598["reused"]), "E598": str(S_598["embedded"]),
    "KEPT": ", ".join(f"<code>{k}</code>" for k in KEPT), "REAL_LIST": ", ".join(f"<code>{k}</code>" for k in REAL),
    "R4_KEY": R4_KEY[:12], "V1_KEY": V1_KEY[:12], "RETENTION": str(RETENTION), "EVAL_ROWS": str(EVAL_ROWS),
    "EVAL_ROWS_W": WORDS[EVAL_ROWS], "TYPICAL": f"{TYPICAL:.2f}", "EVAL_RS": f"{EVAL_ROWS * TYPICAL:.2f}",
    "TOKEN_PAISE": f"{TOKEN_RS * 100:.2f}", "MANAGED_SIZE": str(MANAGED_SIZE), "MANAGED_OV": str(MANAGED_OV),
    "IMAGE": IMAGE, "TEST_N": str(TEST_N), "TEST_N_W": WORDS.get(TEST_N, str(TEST_N)), "LANE_SMALL": f"{LANE_RS['small']:.2f}",
    "PAIR_ROWS": PAIR_ROWS, "OTHER_ROWS": OTHER_ROWS, "N_GRID": str(len(GRID)),
    "MSA_400": str(OTHERS[0][2]), "INV_400": str(OTHERS[1][2]),
    "NEXT_TITLE": html.escape(MANIFEST["modules"]["08"]["lessons"]["8.3"]["name"]),
    "PREV_TITLE": html.escape(MANIFEST["modules"]["08"]["lessons"]["8.1"]["name"]),
    "SIZE_MAX": str(len(SIZES) - 1), "SIZE_IDX": str(SIZE_IDX), "OPT_OV": OPT_OV, "OPT_SEC": OPT_SEC,
    "CK_SUM": html.escape(py_summary(*NEW), quote=False), "SIZE_LIST": ", ".join(map(str, SIZES[:-1])) + f" and {SIZES[-1]}",
    "NP03_LEN": str(LENS["NP-03"]), "LONGEST_MINUS": str(LONGEST - 1), "TEST_N_WC": WORDS.get(TEST_N, str(TEST_N)).capitalize(),
    "FIRST_DOC": FIRST_DOC, "FIRST_ONE": g(FIRST_ONE), "FIRST_KIT": g(FIRST_KIT), "FS_WRITES": g(FS_WRITES), "FS_RS": f"{FS_RS:.2f}",
    "LANE_H_SMALL": f"{sc.HOURLY['small'] * USD_INR:.2f}", "LANE_H_MEDIUM": f"{sc.HOURLY['medium'] * USD_INR:.2f}",
}


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a window of commands and output, or a number computed above."""
    for k, v in {**WIN, **VALUES}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {KIT_PAIR} in both twins (lines {MAIN_LINE}, {CORPUS_LINE}); the handbook {len(BASE)} chunks, at {NEW}: "
      f"{S_NEW['chunks']} ({S_NEW['reused']} reused, {S_NEW['embedded']} embedded, Rs {S_NEW['rupees']:.2f}); 599 the line | "
      f"the twin test: kit {T_KIT[0]}, one twin {T_ONE[0]}, both {T_TWO[0]} | the explorer's script agrees with both twins at "
      f"{len(GRID)} pairs (node) | run list Rs {CALLS_RS:.2f} in calls, lane Rs {LANE_RS['small']:.2f} for {LANE_H} hours")
