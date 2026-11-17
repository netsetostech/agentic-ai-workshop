"""Build lesson 3.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Check quotes and version prompts. The first half holds each citation's quote against the passage it cites:
run_eval.quote_check()'s five verdicts against the pool /v1/passages reads back, beside judge_citations()' search of
the tenant's whole corpus. The second binds the prompt's text to its label: config.py's prompt_id@prompt_version, the
sha256 of generator.py's SYSTEM followed by DATED_RULE, services/rag-api/prompt_versions.json and make prompt-version
(commands/prompt_pin.py). The change it ships is rule 5 weakened: in memory on the bench, then as a v4 candidate.

Computed here, offline, from the kit:
  - the quote bench's data and rule: quote_check() ported to JavaScript and checked against the kit's in node on
    every case; the corpus verdict of each case from judge_citations() over acme's corpus;
  - the version strip's: a JavaScript sha256 checked against hashlib, and prompt_pin.check()'s lines checked against
    prompt_pin itself on every case, each case a copy of the three files it reads in a temporary directory;
  - step 3's two cells, run on a copy of the kit's evals and shared/: nine quotes through quote_check() and
    judge_citations(), and run_eval.live() scoped to the handbook with DOCUMIND_EVAL_PASSAGES=1 against a stand-in API;
  - make prompt-version on the kit (step 5), and step 7's branch in a throwaway git repository holding a copy of the
    files it touches: the edit, the refusal, the registration with the check and the unit test, and the commit;
  - the undo's shape, from prompt_pin's own output on the kit.
Recorded from the author's lane with pb.recorded() (RUN_LIST.md says how): the scoped gate on the live revision and its
citations, the bench, the build and the candidate, the version check, the candidate's gate, the comparison and the rows.
The lane cells that read a report, a describe or the log are also run here, against stand-ins, so their code is tested
before a lane runs them. The kit's own files are never written.

    python pagekit/build.py 3.6
"""
import ast
import hashlib
import html
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "3.6"
title = ("<title>Lesson 3.6 Check quotes and version prompts - every quote held against the passage it cites, and the "
         "prompt's text bound to the label every answer carries | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the two benches: controls in a grid, the verdict and its steps as cards */
.qb-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.qb-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.qb-wide{grid-column:1/-1;}
.qb-l select,.qb-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.qb-l textarea{font-family:var(--mono);line-height:1.4;resize:vertical;}
.qb-check{display:flex;gap:8px;align-items:center;font-size:var(--small-size);color:var(--navy);min-height:44px;}
.qb-check input{width:20px;height:20px;flex:0 0 auto;}
.qb-out{display:grid;gap:8px;}
.qb-step{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.qb-step b{color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;display:block;margin-bottom:2px;}
.qb-step pre{margin:6px 0 0;padding:8px;background:#1e293b;color:#e2e8f0;border-radius:8px;font-family:var(--mono);font-size:var(--kicker-size);line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere;}
.qb-step.ok{border-color:#16a34a;background:#f0fdf4;}
.qb-step.flag{border-color:#f59e0b;background:#fffbeb;}
.qb-step.stop{border-color:#dc2626;background:#fef2f2;}
.qb-step.skip{border-style:dashed;}
.qb-v{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px;margin-right:6px;}
.v-own,.v-exit0{background:#d1fae5;color:#065f46;}.v-elsewhere,.v-substituted{background:#fef3c7;color:#92400e;}
.v-absent,.v-exit2{background:#fee2e2;color:#991b1b;}.v-unread{background:#f1f5f9;color:#475569;}
.qb-pool details{background:var(--card);border:1px solid var(--border);border-radius:8px;margin:6px 0 0;}
.qb-pool summary{cursor:pointer;padding:8px 10px;font-family:var(--mono);font-size:12px;color:var(--navy);min-height:max(36px,var(--touch));overflow-wrap:anywhere;}
.qb-pool details p{margin:0;padding:0 10px 8px;white-space:pre-wrap;font-family:var(--mono);font-size:12px;line-height:1.5;overflow-wrap:anywhere;}
.qb-path{display:grid;grid-template-columns:minmax(0,10em) minmax(0,1fr);gap:4px 10px;margin:4px 0 0;}
.qb-path dt{font-family:var(--mono);font-size:11px;color:var(--navy);font-weight:700;}
.qb-path dd{margin:0;}
@media (max-width: 640px){.qb-path{grid-template-columns:minmax(0,1fr);}.qb-path dd{margin:0 0 6px;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at "
         "the kit's own index for the duration and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head; every gate and bench on this page asks as documind-ui-sa.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ verbatim kit excerpts
SCH, GEN, RE_ = "shared/documind_schemas.py", "services/rag-api/generator.py", "evals/run_eval.py"
MAIN, CFG, SC = "services/rag-api/main.py", "services/rag-api/config.py", "services/rag-api/semantic_cache.py"
TD, PIN, REG = "terraform/sql/tenant_daily.sql", "commands/prompt_pin.py", "services/rag-api/prompt_versions.json"
GENMK, BENCH, PV_TEST = "mk/generation.mk", "evals/prompt_bench.py", "commands/tests/test_prompt_versions.py"
UIC, TRAINSET = "services/frontend/citations.py", "evals/make_trainset.py"
EXCERPTS = {
    "resolve_quote": ("shared/documind_schemas.py - resolve(): one citation a chunk, its quote the model's words or the passage's first 500 characters",
                      block(SCH, "    cits: List[Citation] = []", n=14) + "\n...\n" + block(SCH, "    for d in draft.citations:", n=6)
                      + "\n...\n" + block(SCH, "MARKER = re.compile(", n=1)),
    "draft_trim": ("services/rag-api/generator.py - _draft(): an over-long quote cut to the contract, and three dots added",
                   block(GEN, "    limit = _quote_limit()", n=4)),
    "judge_citations": ("evals/run_eval.py - judge_citations(): quote support, the words looked for in the tenant's whole corpus",
                        block(RE_, "def judge_citations(", end="def pct(")),
    "quote_check": ("evals/run_eval.py - quote_check(): one verdict a citation, against the passage it names",
                    block(RE_, "QUOTE_VERDICTS = (", n=1) + "\n...\n" + block(RE_, "def quote_check(", end="def anchors_found(")),
    "stream_cites": ("services/rag-api/main.py - /v1/stream: the citations sent before the first token, each quoting its passage's opening",
                     block(MAIN, "                # Citations first, and from the PACKED set", n=9)),
    "ui_sources": ("services/frontend/citations.py - render_with_citations(): the Sources list shows each one's first 200 characters",
                   block(UIC, "    with st.expander(f", n=5)),
    "switch": ("evals/run_eval.py - live(): the switch, read once every row has been asked",
               block(RE_, "    # DOCUMIND_EVAL_PASSAGES=1: each answerable row's pool read again, its quotes and anchors", n=3)),
    "passage_checks": ("evals/run_eval.py - passage_checks(): each answered row's pool read again, each quote checked, each anchor looked for",
                       block(RE_, "def passage_checks(", end="def passage_info(")),
    "config_label": ("services/rag-api/config.py - the label: two fields, which everything that names a prompt reads",
                     block(CFG, '    prompt_id: str = "documind-rag"', n=2)),
    "main_label": ("services/rag-api/main.py - where the label goes: /version, every usage row, the stream's last event",
                   block(MAIN, '@app.get("/version")', n=8) + "\n...\n" + block(MAIN, '            "model": model,', n=2)
                   + "\n...\n" + block(MAIN, '        done = {**usage, "latency_ms": int((time.time() - t0) * 1000), "stages": stages,', n=4)),
    "scope_of": ("services/rag-api/semantic_cache.py - scope_of(): the answer cache's scope includes the version",
                 block(SC, "def scope_of(", end="def _alive(")),
    "tenant_daily": ("terraform/sql/tenant_daily.sql - the daily view: one row per version, among its other dimensions",
                     block(TD, "  -- The dimensions an answer can be sliced by.", n=7) + "\n...\n" + block(TD, "GROUP BY day, tenant, surface", n=2)),
    "system_text": ("services/rag-api/generator.py - SYSTEM and DATED_RULE: the text the label names",
                    block(GEN, 'SYSTEM = """You are DocuMind', end="def _dated_rule(") + "\n\n" + block(GEN, "def _dated_rule(", n=2)),
    "prompt_join": ("services/rag-api/generator.py - generate(): every prompt starts with that text, and generate_stream()'s the same",
                    block(GEN, '    prompt = f"{SYSTEM}{_dated_rule(packed)}', n=1)),
    "pin_check": ("commands/prompt_pin.py - check(): the label, the text's sha256, and the registry's verdict",
                  block(PIN, "def check(", end="def main(")),
    "registry": ("services/rag-api/prompt_versions.json - the registry: one label, one sha256", block(REG, "{", n=6)),
    "mk_target": ("mk/generation.mk - prompt-version: offline, no project, no guard",
                  block(GENMK, "# The prompt bound to its version (lesson 3.6)", n=7)),
    "edit_system": ("evals/prompt_bench.py - edit_system() and prompt_sha(): SYSTEM edited in memory, and hashed as a version's text is",
                    block(BENCH, "def edit_system(", end="def rule_count(")),
    "trainset_test": ("commands/tests/test_prompt_versions.py - the tuning set's copy of SYSTEM, held equal to the served one",
                      block(PV_TEST, "    def test_make_trainset_keeps_the_generators_system(self):", n=4)),
    "build_recipe": ("Makefile - build: one Cloud Build per service, the image tagged with the commit",
                     block("Makefile", "# Cloud Build every image make up deploys.", end="# A checkout that was never connected")),
    "release_candidate": ("Makefile - release-candidate: that image on a revision with no traffic, recorded by name",
                          block("Makefile", "release-candidate: guard-project", n=5)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
RQ = E["resolve_quote"].split("\n...\n")
assert RQ[0].rstrip().endswith('quote=(quote or c.get("text", ""))[:500],') and "        if chunk_id in seen:\n            return" in RQ[0], RQ[0][-200:]
assert RQ[1] == ("    for d in draft.citations:\n        if 1 <= d.source <= len(packed):\n            cite(d.source, d.quote)\n"
                 "    for n in cited_numbers(draft.answer):\n        if 1 <= n <= len(packed):\n            cite(n, \"\")"), RQ[1]
assert RQ[2].startswith("MARKER = re.compile(") and len(RQ) == 3
assert E["draft_trim"].rstrip().endswith('c["quote"] = c["quote"][: limit - 3].rstrip() + "..."'), E["draft_trim"]
assert E["judge_citations"].rstrip().endswith("return valid, supported, why") and "if quote and quote not in corpus_text:" in E["judge_citations"]
assert E["quote_check"].rstrip().endswith('return "absent"') and E["quote_check"].startswith('QUOTE_VERDICTS = ("own", "elsewhere", "absent", "substituted", "unread")')
assert "'quote': c['text'][:240]" in E["stream_cites"] and "src['text'][:200]" in E["ui_sources"]
assert 'os.environ.get("DOCUMIND_EVAL_PASSAGES") == "1"' in E["switch"]
assert E["passage_checks"].rstrip().endswith('"must_retrieve_recall": found / asked if asked else None}')
assert E["config_label"] == '    prompt_id: str = "documind-rag"\n    prompt_version: str = "v3"', E["config_label"]
assert E["main_label"].count('f"{settings.prompt_id}@{settings.prompt_version}"') == 2 and '"prompt_version": settings.prompt_version,' in E["main_label"]
assert '"prompt": prompt_version' in E["scope_of"] and "prompt_version," in E["tenant_daily"].split("GROUP BY", 1)[1]
assert E["pin_check"].rstrip().endswith("return 1, lines") and E["registry"].rstrip().endswith("}")
assert E["mk_target"].rstrip().endswith("\t$(PY) commands/prompt_pin.py"), E["mk_target"]
assert E["edit_system"].rstrip().endswith("return hashlib.sha256((system + dated_rule).encode(\"utf-8\")).hexdigest()")
assert "--no-traffic --tag candidate" in E["release_candidate"] and "record-candidate" in E["release_candidate"]
assert "gcloud builds submit . --project=$(PROJECT) --quiet --config=cloudbuild.yaml" in E["build_recipe"]
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ the kit's facts
def load(path: Path, name: str):
    """A kit module by path, without putting its folder on sys.path for the rest of the build."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path[:0] = [str(KIT), str(KIT / "evals")]
import run_eval as rv  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402
from shared.documind_schemas import DraftCitation, ModelDraft, resolve  # noqa: E402

pp = load(KIT / PIN, "prompt_pin_lesson36")
bench = load(KIT / BENCH, "prompt_bench_lesson36")
GEN_SRC = (KIT / GEN).read_text(encoding="utf-8")
CFG_SRC = (KIT / CFG).read_text(encoding="utf-8")
REG_SRC = (KIT / REG).read_text(encoding="utf-8")
STRS = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(GEN_SRC).body
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
SYSTEM, DATED = STRS["SYSTEM"], STRS["DATED_RULE"]
PROMPT_ID = re.search(r'^    prompt_id: str = "([\w-]+)"$', CFG_SRC, re.M).group(1)
VERSION = re.search(r'^    prompt_version: str = "(\w+)"$', CFG_SRC, re.M).group(1)
LABEL = f"{PROMPT_ID}@{VERSION}"
TEXT = pp.prompt_text(GEN_SRC)
assert TEXT == SYSTEM + DATED and LABEL == pp.label(CFG_SRC) == "documind-rag@v3"
V3_SHA = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()
REGISTRY = json.loads(REG_SRC)["versions"]
assert REGISTRY == {LABEL: V3_SHA}, REGISTRY
assert json.dumps(json.loads(REG_SRC), indent=2, ensure_ascii=False) + "\n" == REG_SRC   # the register cell's rewrite adds one line
PIN_CODE, PIN_LINES = pp.check(KIT)
assert PIN_CODE == 0 and PIN_LINES[-1].startswith(f"registry: {LABEL} has this sha256"), PIN_LINES

# rule 5, weakened: the change this lesson ships
RULE5_OLD = "5. A quote is the clause that answers - at most twenty-five words, never a whole section."
RULE5_NEW = "5. A quote sums up the clause that answers - at most fifteen words, in plain language."
TRAINSET_SRC = (KIT / TRAINSET).read_text(encoding="utf-8")
assert GEN_SRC.count(RULE5_OLD) == 1 and TRAINSET_SRC.count(RULE5_OLD) == 1 and SYSTEM.count(RULE5_OLD) == 1
SYS_V4 = SYSTEM.replace(RULE5_OLD, RULE5_NEW)
V4_TEXT = SYS_V4 + DATED
V4_SHA = hashlib.sha256(V4_TEXT.encode("utf-8")).hexdigest()
NEW_RULE = RULE5_NEW.split(". ", 1)[1]
assert bench.edit_system(SYSTEM, add=[NEW_RULE], drop=[5]) == SYS_V4                  # the bench's edit is the branch's text
assert bench.prompt_sha(SYS_V4, DATED) == V4_SHA and bench.prompt_sha(SYSTEM, DATED) == V3_SHA
QUOTE_WORDS = re.search(r"at most ([\w-]+) words", RULE5_OLD).group(1)
assert QUOTE_WORDS == "twenty-five"
# the kit's other prompt versions: dated labels with no registry behind them (prompt_pin.py reads generator.py alone)
REWRITE_PV, ROUTER_PV = (re.search(r'^PROMPT_VERSION = "([^"]+)"$', (KIT / rel).read_text(encoding="utf-8"), re.M).group(1)
                         for rel in ("shared/query_rewrite.py", "services/chat/desk_router.py"))
assert "query_rewrite" not in (KIT / PIN).read_text(encoding="utf-8") and "desk_router" not in (KIT / PIN).read_text(encoding="utf-8")

# the contract's limits, the stream's and the UI's quote lengths, the UI's request
SCH_SRC = (KIT / SCH).read_text(encoding="utf-8")
QUOTE_DRAFT = int(re.search(r'quote: str = Field\(max_length=(\d+), description="Exact words from that source"\)', SCH_SRC).group(1))
QUOTE_CIT = int(re.search(r"quote: str = Field\(max_length=(\d+)\)\n", SCH_SRC).group(1))
assert (QUOTE_DRAFT, QUOTE_CIT) == (200, 500)
STREAM_QUOTE = int(re.search(r"'quote': c\['text'\]\[:(\d+)\]", E["stream_cites"]).group(1))
UI_QUOTE = int(re.search(r"src\['text'\]\[:(\d+)\]", E["ui_sources"]).group(1))
UI_TIP = int(re.search(r'tip = \(" "\.join\(src\["text"\]\[:(\d+)\]\.split\(\)\) \+ "\.\.\."\) if src else "unknown source"',
                       (KIT / UIC).read_text(encoding="utf-8")).group(1))
assert UI_TIP == 120
UI_SRC = (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")
UI_TOP_K = int(re.search(r'json=\{"query": query, "tenant_id": tenant_id, "top_k": (\d+), "brain": "ui"\}', UI_SRC).group(1))
assert (STREAM_QUOTE, UI_QUOTE, UI_TOP_K) == (240, 200, 5)
TOP_K = int(re.search(r'json\.dumps\(\{"query": question, "tenant_id": tenant, "top_k": (\d+)\}\)', (KIT / RE_).read_text(encoding="utf-8")).group(1))
assert TOP_K == bench.TOP_K == 6


def scope_of(version: str) -> str:
    """semantic_cache.scope_of() for the UI's request: no filters, the UI's top_k."""
    return hashlib.sha256(json.dumps({"filters": {}, "top_k": UI_TOP_K, "prompt": version}, sort_keys=True).encode("utf-8")).hexdigest()[:16]


assert "json.dumps({\"filters\": filters or {}, \"top_k\": top_k, \"prompt\": prompt_version}," in E["scope_of"]

# make's own lines: the recipe it echoes, and the line its error names
GENMK_LINES = (KIT / GENMK).read_text(encoding="utf-8").splitlines()
MK_LINE = GENMK_LINES.index("\t$(PY) commands/prompt_pin.py") + 1
assert GENMK_LINES[MK_LINE - 2] == "prompt-version:" and re.search(r"^PY +\?= python$", (KIT / "Makefile").read_text(encoding="utf-8"), re.M)
MAKE_ECHO = "python commands/prompt_pin.py"
MAKE_ERR = f"make: *** [{GENMK}:{MK_LINE}: prompt-version] Error 1"

# the handbook as the kit's chunker cuts it, with the ids the ingest worker mints
SOURCE = "hr_policy_2026.md"
RAW = (KIT / "evals" / "corpus" / "acme" / SOURCE).read_bytes()
DOC_SHA = hashlib.sha256(RAW).hexdigest()
URI = f"gs://{PROJ}-uploads/acme/{SOURCE}"
CUT = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": URI, "text": RAW.decode("utf-8")}, "acme")
PASS = {c["locator"]: {"n": i, "chunk_id": f"acme:{DOC_SHA}#{i}", "source_uri": URI, "section": c["section"], "text": c["text"]}
        for i, c in enumerate(CUT)}
assert json.loads((KIT / "evals" / "manifest.json").read_text(encoding="utf-8"))[0]["sha256"] == DOC_SHA
POOL_CODES = ("NP-03", "PB-02", "LV-07", "LV-01", "GEN-000", "GEN-001")
POOL = [PASS[k] for k in POOL_CODES]
CORPUS_TEXT = re.sub(r"\s+", " ", rv.haystack(rv.load_corpus(), "acme"))
CORPUS_CHARS = f"{len(CORPUS_TEXT) / 1e6:.1f} million"
GOLDEN = rv.load_golden()
LK06 = next(r for r in GOLDEN if r["id"] == "lk-06")
SCOPED = [r for r in GOLDEN if rv.in_scope(r, SOURCE, rv.load_corpus())]
assert [r["id"] for r in SCOPED] == [f"lk-0{i}" for i in range(1, 10)] + ["vr-01"] and all(r["tenant"] == "acme" and r["answerable"] for r in SCOPED)

# ------------------------------------------------------------------ the cells
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}       # no gcloud on PATH, no credentials in reach


def run_cell(code: str, cwd: Path, env: dict | None = None, prelude: str = "") -> str:
    """One page cell's Python, run as the page runs it (python -), with nothing on stderr allowed."""
    r = subprocess.run([sys.executable, "-"], input=prelude + code, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=env or ENV)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1500:], r.stdout[-500:])
    return r.stdout


def heredoc(code: str) -> str:
    """The cell as a bash window shows it: python - <<'PY' ... PY."""
    return f"python - <<'PY'\n{code}\nPY"


PY_NINE = '''import hashlib, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "evals"]
import run_eval as rv                                                  # the gate: judge_citations() and quote_check()
from shared import documind_corpus as dc
from shared.documind_schemas import DraftCitation, ModelDraft, resolve
raw = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
sha, uri = hashlib.sha256(raw).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
cut = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": uri, "text": raw.decode("utf-8")}, "acme")
P = {c["locator"]: {"chunk_id": f"acme:{sha}#{i}", "source_uri": uri, "text": c["text"]} for i, c in enumerate(cut)}
pool = [P[k] for k in ("NP-03", "PB-02", "LV-07", "LV-01", "GEN-000", "GEN-001")]   # six passages, ids as the worker mints them
corpus = re.sub(r"\\s+", " ", rv.haystack(rv.load_corpus(), "acme"))  # what judge_citations() searches: every acme mirror
row = next(r for r in rv.load_golden() if r["id"] == "lk-06")
said = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
whole = " ".join(P["GEN-000"]["text"].split("\\n", 1)[1].split())     # a whole section, longer than a draft's 200 characters
empty = resolve(ModelDraft(answer="60 days [1].", confidence="high", answerable=True,
                           citations=[DraftCitation(source=1, quote="")]), pool).citations[0].quote
cases = [("NP-03", said, "the sentence, under its own passage"),
         ("NP-03", "NOTICE RUNS from the date the resignation is acknowledged in writing.", "a line break, in capitals"),
         ("PB-02", said, "the same sentence, under [2]"),
         ("NP-03", "Confirmed E3 staff give 60 days' notice.", "a paraphrase"),
         ("NP-03", said.replace("60 days", "90 days"), "revision 2's figure"),
         ("NP-03", empty, "an empty quote, filled in by resolve()"),
         ("GEN-000", whole[:200 - 3].rstrip() + "...", "_draft()'s cut of a whole section"),
         ("NP-03", "A confirmed employee ... serves a notice period of 60 days.", "an elision, mid-sentence"),
         ("EXP-12", said, "a passage the pool did not hold")]
got = []
print(f"{'case':39} {'chars':>5}  {'quote_check':12} judge_citations")
for code, quote, label in cases:
    c = {"chunk_id": P[code]["chunk_id"], "source_uri": uri, "quote": quote}
    verdict, supported = rv.quote_check(c, pool), rv.judge_citations(row, [c], None, {}, corpus)[1]
    got.append((verdict, supported))
    print(f"{label:39} {len(quote):5}  {verdict:12} {'supported' if supported else 'not supported'}")
print("quote_check: " + ", ".join(f"{v} {sum(g == v for g, _ in got)}" for v in rv.QUOTE_VERDICTS)
      + f" | judge_citations: supported {sum(s for _, s in got)} of {len(got)}")'''

PY_GATE0 = '''import hashlib, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "evals"]
import run_eval as rv
from shared import documind_corpus as dc
from shared.documind_schemas import DraftCitation, ModelDraft, resolve
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN"):
    os.environ.pop(k, None)
os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"                            # the switch: each answered row's pool read again
SOURCE, API = "hr_policy_2026.md", "https://stand-in.invalid"
raw = open("evals/corpus/acme/" + SOURCE, "rb").read()
sha, uri = hashlib.sha256(raw).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/" + SOURCE
cut = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": uri, "text": raw.decode("utf-8")}, "acme")
P = {c["locator"]: {"n": i, "chunk_id": f"acme:{sha}#{i}", "source_uri": uri, "page": 1, "kind": "text", "text": c["text"]}
     for i, c in enumerate(cut)}                                        # ids as the ingest worker mints them
CLAUSES = [k for k in P if k != "preamble" and not k.startswith("GEN")]
rows = [r for r in rv.load_golden() if rv.in_scope(r, SOURCE, rv.load_corpus())]


def sentence(code):
    """The first sentence of a clause's body: what a model that keeps rule 5 would quote."""
    return " ".join(P[code]["text"].split("\\n", 1)[1].split()).split(". ")[0].rstrip(".") + "."


PLANT = {"lk-04": ("NP-03", sentence("PB-02")),                        # the clause's words, under another passage
         "lk-06": ("NP-03", "Confirmed E3 staff give 60 days' notice."),       # words the model wrote
         "lk-08": ("FIN-02", "")}                                        # no quote: resolve() puts the passage's opening in
GONE = {"lk-09": "WFH-01"}                                               # cited, and missing from the pool read back
asked, read = iter(rows), iter(rows)


def ask(api_url, question, tenant, email, token, retries=1):
    """The stand-in /v1/query: the row's figure, and one citation resolved the way rag-api resolves one."""
    row = next(asked)
    code, quote = PLANT.get(row["id"], (row["must_retrieve"][0], sentence(row["must_retrieve"][0])))
    draft = ModelDraft(answer=f"The handbook says {' and '.join(row['must_contain'])} [1].", confidence="high",
                       answerable=True, citations=[DraftCitation(source=1, quote=quote)])
    return 200, {**resolve(draft, [P[code]]).model_dump(), "model": "stand-in", "backend": "vertex", "cache_hit": "none"}, 1500


def passages(api_url, question, tenant, email, token, top_k=6, retries=1):
    """The stand-in /v1/passages: six of the handbook's clauses, the row's own first."""
    row = next(read)
    first = row["must_retrieve"][0]
    return [P[c] for c in [first] + [c for c in CLAUSES if c != first] if c != GONE.get(row["id"])][:top_k]


rv.ask, rv.passages, rv.fetch_current_shas = ask, passages, lambda *a, **k: {sha}
print("exit", rv.live(API, source=SOURCE, report="evals/reports/standin36.json"))'''

PY_CITES = '''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path = "evals/reports/quotes36.json"                                  # the report the scoped gate just wrote
r = json.load(open(path, encoding="utf-8"))
pq = r.get("passage_checks")
if not pq:
    raise SystemExit(f"{path} has no passage_checks: run make eval-live with DOCUMIND_EVAL_PASSAGES=1")


def pct(v):
    """A rate as the gate prints it, or n/a when nothing was counted."""
    return "n/a" if v is None else f"{v:.1%}"


print(f"{r['api_url']}  {r['rows']} rows | quote_support_rate {pct(r.get('quote_support_rate'))} | quote_passage_rate {pct(pq['quote_passage_rate'])}")
for rec in r["records"]:
    for c in rec.get("cites") or []:
        words = " ".join((c.get("quote") or "").split())
        print(f"  {rec['id']:6} {c.get('check', 'not read'):11} #{(c.get('chunk_id') or '').rsplit('#', 1)[-1]:<4} {words[:60]!r}{' ...' if len(words) > 60 else ''}")
    lost = sorted(a for a, hit in (rec.get("anchors") or {}).items() if not hit)
    if "pool" in rec and (rec["pool"] is None or lost):
        print(f"  {rec['id']:6} pool {rec['pool']}{'; anchors not in it: ' + ', '.join(lost) if lost else ''}")
print("verdicts: " + ", ".join(f"{k} {n}" for k, n in pq["quotes"].items()))'''

PY_COMPARE = '''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
V3, V4 = "evals/reports/quotes36.json", "evals/reports/quotes36_v4.json"    # step 4's report, and the candidate's


def load(path):
    """One run_eval.py report, its passage checks, and the gate's exit as the gate decides it."""
    r = json.load(open(path, encoding="utf-8"))
    code = 2 if r["leaks"] else 1 if (r["failed"] or r["stale"] or r["required_failed"]) else 0
    return r, r.get("passage_checks") or {}, code


def pct(v):
    """A rate as the gate prints it, or n/a when nothing was counted."""
    return "n/a" if v is None else f"{v:.1%}"


def verdicts(rec):
    """A row's quote checks in citation order, or why it has none."""
    return " ".join(c.get("check", "-") for c in rec.get("cites") or []) or rec.get("why") or "-"


(a, qa, ea), (b, qb, eb) = load(V3), load(V4)
for name, r, q, e in (("v3", a, qa, ea), ("v4", b, qb, eb)):
    print(f"{name}: gate exit {e} | quote_support_rate {pct(r.get('quote_support_rate'))} | quote_passage_rate "
          f"{pct(q.get('quote_passage_rate'))} | " + ", ".join(f"{k} {n}" for k, n in (q.get("quotes") or {}).items()))
by_id = {x["id"]: x for x in b["records"]}
print(f"\\n  {'row':6} {'v3':22} {'v4':22} v4's first quote")
for x in a["records"]:
    y = by_id.get(x["id"], {})
    first = " ".join(((y.get("cites") or [{}])[0].get("quote") or "").split())
    print(f"  {x['id']:6} {verdicts(x)[:22]:22} {verdicts(y)[:22]:22} {first[:50]!r}")'''

PY_ROWS = '''import collections, datetime as dt, json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, REGION = os.environ["PROJECT"], os.environ["REGION"]


def gcloud_json(*args):
    """Run one gcloud command for the project and return its JSON output, parsed."""
    out = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True, check=True).stdout
    return json.loads(out or "[]")


since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = gcloud_json("logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                   f'AND jsonPayload.prompt_version:* AND timestamp>="{since}"', "--limit", "2000")
serving = {t["revisionName"] for t in gcloud_json("run", "services", "describe", "documind-api", "--region", REGION)["status"]["traffic"]
           if t.get("percent")}
n, out = collections.Counter(), collections.Counter()
for e in rows:
    p = e["jsonPayload"]
    key = (e["resource"]["labels"]["revision_name"], p.get("event"), p.get("prompt_version"))
    n[key] += 1
    out[key] += int(p.get("tokens_out") or 0)
print(f"{len(rows)} usage rows from documind-api in the last 6 h, by revision, event and prompt_version")
print(f"  {'revision':30} {'traffic':8} {'event':9} {'prompt':7} {'rows':>5} {'tokens_out':>10}")
for rev, event, version in sorted(n):
    key = (rev, event, version)
    print(f"  {rev:30} {'serving' if rev in serving else 'none':8} {event:9} {version:7} {n[key]:5} {out[key]:10}")
v4 = sorted({rev for rev, _, version in n if version == "v4"})
print(f"rows that say v4 come from: {', '.join(v4) or 'no revision'}; serving traffic among them: {', '.join(sorted(set(v4) & serving)) or 'none'}")'''

PY_EDIT = f'''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
OLD = "{RULE5_OLD}"
NEW = "{RULE5_NEW}"
for path in ("services/rag-api/generator.py", "evals/make_trainset.py"):  # the served SYSTEM, and the tuning set's copy of it
    text = open(path, encoding="utf-8").read()
    assert text.count(OLD) == 1, f"{{path}}: rule 5 is not the kit's: git checkout {{path}}, then run this again"
    open(path, "w", encoding="utf-8", newline="\\n").write(text.replace(OLD, NEW))
    print(f"{{path}}: rule 5 now reads {{NEW[3:]!r}}")'''

PY_REGISTER = f'''import hashlib, json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "commands")
import prompt_pin                                                     # the check's own reader of SYSTEM + DATED_RULE
CFG, REG = prompt_pin.CONFIG, prompt_pin.REGISTRY
cfg = open(CFG, encoding="utf-8").read()
assert cfg.count('    prompt_version: str = "v3"\\n') == 1, f"{{CFG}}: prompt_version is not v3"
open(CFG, "w", encoding="utf-8", newline="\\n").write(cfg.replace('    prompt_version: str = "v3"\\n', '    prompt_version: str = "v4"\\n'))
digest = hashlib.sha256(prompt_pin.prompt_text(open(prompt_pin.GENERATOR, encoding="utf-8").read()).encode("utf-8")).hexdigest()
reg = json.load(open(REG, encoding="utf-8"))
reg["versions"]["{PROMPT_ID}@v4"] = digest                           # beside v3's line, which stays as it is
open(REG, "w", encoding="utf-8", newline="\\n").write(json.dumps(reg, indent=2, ensure_ascii=False) + "\\n")
print(f"{{CFG}}: prompt_version v4")
print(f'{{REG}}: "{PROMPT_ID}@v4": "{{digest}}"')'''

PY_ENVCHECK = ('import json, sys; env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", []); '
               'print("PROMPT_VERSION on the service:", next((e.get("value") for e in env if e["name"] == "PROMPT_VERSION"), '
               '"not set, so config.py names the version"))')
PY_VERSION = ('import json, sys; v = json.load(sys.stdin); print(sys.argv[1], "| prompt", v["prompt"], "| git_sha", v["git_sha"], '
              '"| this commit:", v["git_sha"] == sys.argv[2])')

GATE_LIVE = f'DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" SOURCE={SOURCE} REPORT=evals/reports/quotes36.json'
GATE_CAND = f'DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE={SOURCE} REPORT=evals/reports/quotes36_v4.json'
BENCH_CMD = ('make bench PROJECT="$PROJECT" BENCH_ARGS="--from-report evals/reports/quotes36.json --no-baseline --drop-rule 5 '
             f"--add-rule '{NEW_RULE}'\"")
COMMIT_MSG = "Prompt v4: rule 5 asks for a summary of the clause"
CELLS = {
    "NINE": heredoc(PY_NINE),
    "GATE0": heredoc(PY_GATE0),
    "LIVE": GATE_LIVE,
    "CITES": heredoc(PY_CITES),
    "PIN": 'make prompt-version; echo "exit $?"',
    "BENCH": BENCH_CMD,
    "BRANCH": "git status --short; git switch -c prompt-v4\n" + heredoc(PY_EDIT) + "\ngit diff --stat",
    "REFUSE": 'make prompt-version; echo "exit $?"',
    "REGISTER": heredoc(PY_REGISTER) + '\nmake prompt-version; echo "exit $?"\npython -m unittest discover -s commands/tests -p test_prompt_versions.py',
    "COMMIT": f'git -c user.name="$ME" -c user.email="$ME" commit -qam "{COMMIT_MSG}"\ngit show --stat --format=\'%h %s\' HEAD',
    "SHIP": ('gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format=json \\\n'
             f"  | python -c '{PY_ENVCHECK}'\n"
             'make build PROJECT="$PROJECT" SERVICES=api\n'
             'make release-candidate PROJECT="$PROJECT"\n'
             'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "VERSION": ('for u in "$API" "$CAND"; do\n'
                '  curl -s "$u/version" -H "Authorization: Bearer $(tok "$API")" \\\n'
                f"    | python -c '{PY_VERSION}' \"$u\" \"$(git rev-parse --short HEAD)\"\n"
                "done"),
    "CAND": GATE_CAND,
    "COMPARE": heredoc(PY_COMPARE),
    "ROWS": heredoc(PY_ROWS),
    "UNDO": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
             "rm -f .candidate-revision      # make promote moves traffic to the revision this file names\n"
             'curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"\n'
             "git switch main\n"
             'make prompt-version; echo "exit $?"\n'
             "git branch --list prompt-v4"),
}
assert "'" not in PY_ENVCHECK and "'" not in PY_VERSION        # each sits inside python -c '...' in bash
CELL_LABELS = {
    "NINE": "run in the operator shell, in the kit (a Python cell; Rs 0: nothing leaves the machine)",
    "GATE0": "run in the operator shell, in the kit (the gate against a stand-in API this cell plays; Rs 0; writes evals/reports/standin36.json)",
    "LIVE": "run in the operator shell, in the kit (ten answers, then ten pool reads: a few rupees)",
    "CITES": "run in the operator shell, in the kit (reads the report; changes nothing)",
    "PIN": "run in the operator shell, in the kit (offline: no project, no credential, Rs 0)",
    "BENCH": "run in the operator shell, in the kit (ten pool reads, then ten answers from the kit's generate() in your shell: a few rupees)",
    "BRANCH": "run in the operator shell, in the kit (a branch of your clone; two files edited)",
    "REFUSE": "run in the operator shell, in the kit (the check, which should fail)",
    "REGISTER": "run in the operator shell, in the kit (two more files edited; then the check and the unit test the dry run runs)",
    "COMMIT": "run in the operator shell, in the kit (one commit on the branch; nothing is pushed)",
    "SHIP": "run in the operator shell, in the kit (one Cloud Build of the API's image, then a revision with no traffic: minutes)",
    "VERSION": "run in the operator shell, in the kit (two GETs: the live revision and the candidate)",
    "CAND": "run in the operator shell, in the kit (the same ten questions to the candidate: a few rupees)",
    "COMPARE": "run in the operator shell, in the kit (reads the two reports; changes nothing)",
    "ROWS": "run in the operator shell (one Cloud Logging read and one describe; changes nothing)",
    "UNDO": "run in the operator shell, in the kit (the tag and its record removed, main checked out; the branch kept)",
}

OUT: dict = {}
TMP = Path(tempfile.mkdtemp(prefix="lesson36-"))
try:
    # ---------------------------------------------------------- step 3, on a copy of the kit's evals and shared/
    KITCOPY = TMP / "kit"
    for rel in ("evals/run_eval.py", "evals/golden.jsonl", "evals/required.json", "evals/manifest.json",
                "shared/documind_corpus.py", "shared/documind_schemas.py"):
        (KITCOPY / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(KIT / rel, KITCOPY / rel)
    for sub in ("corpus", "demo"):             # the text files load_corpus() and load_demo() read; the PDFs stay behind
        for p in (KIT / "evals" / sub).rglob("*"):
            if p.is_file() and p.suffix in (".md", ".txt"):
                dest = KITCOPY / p.relative_to(KIT)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
    nine = run_cell(PY_NINE, KITCOPY)
    NINE_ROWS = nine.splitlines()[1:-1]
    OUT["NINE"] = ("(the cell, run on a copy of the kit's evals when this page was built; yours should match it)", nine)
    want_nine = [("own", True), ("own", True), ("elsewhere", True), ("absent", False), ("absent", False), ("substituted", True),
                 ("own", False), ("absent", False), ("unread", True)]
    got_nine = [(re.search(r"  (own|elsewhere|absent|substituted|unread) +(supported|not supported)$", line).group(1),
                 line.endswith(" supported") and not line.endswith("not supported")) for line in NINE_ROWS]
    assert got_nine == want_nine, got_nine
    assert nine.rstrip().endswith("quote_check: own 3, elsewhere 1, absent 3, substituted 1, unread 1 | judge_citations: supported 5 of 9"), nine[-200:]

    gate0 = run_cell(PY_GATE0, KITCOPY)
    OUT["GATE0"] = ("(the cell, run on a copy of the kit's evals when this page was built; yours should match it)", gate0)
    SI = {k: re.search(rf"\[info\] {k} +([\d.]+%)", gate0).group(1) for k in ("quote_support_rate", "quote_passage_rate", "must_retrieve_recall")}
    assert SI == {"quote_support_rate": "90.0%", "quote_passage_rate": "66.7%", "must_retrieve_recall": "95.0%"}, SI
    assert "(6 of 9 answered rows' quotes in the passage they cite; elsewhere 1, absent 1, substituted 1, unread 1; not a threshold)" in gate0
    assert "(19 of 20 anchors in the pool /v1/passages returned, over 10 answerable rows; not a threshold)" in gate0
    assert gate0.rstrip().endswith("All thresholds met.\nexit 0"), gate0[-200:]
    STANDIN = KITCOPY / "evals" / "reports" / "standin36.json"
    report0 = json.loads(STANDIN.read_text(encoding="utf-8"))
    planted = {x["id"]: [c["check"] for c in x["cites"]] for x in report0["records"]}
    assert planted == {**{r["id"]: ["own"] for r in SCOPED}, "lk-04": ["elsewhere"], "lk-06": ["absent"], "lk-08": ["substituted"],
                       "lk-09": ["unread"]}, planted

    # the reader and the comparison, run here on stand-in reports: lane cells tested before a lane runs them
    assert PY_CITES.count('"evals/reports/quotes36.json"') == 1 and PY_COMPARE.count('"evals/reports/quotes36_v4.json"') == 1
    cites0 = run_cell(PY_CITES.replace("quotes36.json", "standin36.json"), KITCOPY)
    assert cites0.startswith("https://stand-in.invalid  10 rows | quote_support_rate 90.0% | quote_passage_rate 66.7%"), cites0[:200]
    assert "  lk-04  elsewhere   #1" in cites0 and "  lk-09  pool 6; anchors not in it: WFH-01" in cites0, cites0
    assert cites0.rstrip().endswith("verdicts: own 6, elsewhere 1, absent 1, substituted 1, unread 1"), cites0[-120:]
    v4rep = json.loads(json.dumps(report0))                 # a second stand-in: every quote rewritten, every check absent
    for x in v4rep["records"]:
        for c in x["cites"]:
            c["quote"], c["check"] = "A summary in plain language.", "absent"
    v4rep["passage_checks"]["quotes"] = {"own": 0, "elsewhere": 0, "absent": 9, "substituted": 0, "unread": 1}
    v4rep["passage_checks"]["quote_passage_rate"] = 0.0
    (KITCOPY / "evals" / "reports" / "standin36_v4.json").write_text(json.dumps(v4rep), encoding="utf-8")
    cmp0 = run_cell(PY_COMPARE.replace("quotes36", "standin36"), KITCOPY)
    assert cmp0.startswith("v3: gate exit 0 | quote_support_rate 90.0% | quote_passage_rate 66.7% | own 6,"), cmp0[:200]
    assert "v4: gate exit 0 | quote_support_rate 90.0% | quote_passage_rate 0.0% | own 0, elsewhere 0, absent 9" in cmp0
    assert "  lk-04  elsewhere              absent                 'A summary in plain language.'" in cmp0, cmp0

    # ---------------------------------------------------------- step 5: make prompt-version on the kit itself
    pin_run = subprocess.run([sys.executable, "commands/prompt_pin.py"], cwd=str(KIT), capture_output=True, text=True,
                             encoding="utf-8", env=ENV)
    assert pin_run.returncode == 0 and not pin_run.stderr and pin_run.stdout.strip().splitlines() == PIN_LINES, pin_run
    PIN_OUT = MAKE_ECHO + "\n" + pin_run.stdout
    OUT["PIN"] = ("(make prompt-version on the kit when this page was built: make's echo of the recipe, then prompt_pin.py's lines)",
                  PIN_OUT + "exit 0\n")

    # ---------------------------------------------------------- step 7's branch, in a throwaway git repository
    REPO = TMP / "repo"
    for rel in (GEN, CFG, REG, TRAINSET, PIN, PV_TEST, GENMK, "mk/README.md", "Makefile", "UNOWNED.md", "INDEX.md"):
        (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(KIT / rel, REPO / rel)
    GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "init.defaultBranch=main",
           "-c", "user.name=lesson", "-c", "user.email=lesson@localhost"]

    def git(*args: str) -> subprocess.CompletedProcess:
        """One git command in the throwaway repository."""
        r = subprocess.run([*GIT, *args], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, (args, r.stderr)
        return r

    def pin_here() -> tuple:
        """make prompt-version in the throwaway repository: prompt_pin's exit code and what the terminal shows."""
        r = subprocess.run([sys.executable, "commands/prompt_pin.py"], cwd=str(REPO), capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        assert not r.stderr, r.stderr
        tail = f"{MAKE_ERR}\nexit 2\n" if r.returncode else "exit 0\n"
        return r.returncode, MAKE_ECHO + "\n" + r.stdout + tail

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "the kit")
    assert git("status", "--short").stdout == ""
    switched = git("switch", "-c", "prompt-v4")
    edit_out = run_cell(PY_EDIT, REPO)
    stat = git("diff", "--stat").stdout
    OUT["BRANCH"] = ("(the cell, run on a copy of the four files when this page was built; git status prints nothing for a clean clone)",
                     switched.stderr + edit_out + stat)
    assert switched.stderr.strip() == "Switched to a new branch 'prompt-v4'" and "2 files changed, 2 insertions(+), 2 deletions(-)" in stat, stat
    code1, refuse = pin_here()
    assert code1 == 1 and f'Set prompt_version to "v4" in {CFG}, then add' in refuse and f'    "{PROMPT_ID}@v4": "{V4_SHA}"' in refuse, refuse
    OUT["REFUSE"] = ("(the same copy: prompt_pin.py's lines, then make's, as GNU make prints them)", refuse)
    reg_out = run_cell(PY_REGISTER, REPO)
    assert reg_out == f"{CFG}: prompt_version v4\n{REG}: \"{PROMPT_ID}@v4\": \"{V4_SHA}\"\n", reg_out
    code2, passed = pin_here()
    assert code2 == 0 and f"registry: {PROMPT_ID}@v4 has this sha256" in passed, passed
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "commands/tests", "-p", "test_prompt_versions.py"],
                          cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert test.returncode == 0 and test.stdout == "" and test.stderr.rstrip().endswith("OK"), test.stderr[-800:]
    N_TESTS = int(re.search(r"Ran (\d+) tests in [\d.]+s", test.stderr).group(1))
    test_err = re.sub(r"Ran (\d+) tests in [\d.]+s", r"Ran \1 tests in 0.xxxs", test.stderr)
    OUT["REGISTER"] = ("(the same copy; the test's time is yours)", reg_out + passed + test_err)
    reg_diff = git("diff", "--", REG).stdout
    assert reg_diff.count("\n+  ") == 2 and reg_diff.count("\n-  ") == 1, reg_diff      # v3's line gains a comma; v4's is new
    git("commit", "-qam", COMMIT_MSG)
    show = git("show", "--stat", "--format=%h %s", "HEAD").stdout
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    assert show.startswith(f"{head} {COMMIT_MSG}\n") and "4 files changed" in show, show
    OUT["COMMIT"] = ("(the same copy; COMMIT is your commit's short sha, the tag make build gives the image)", show.replace(head, "COMMIT", 1))

    # main again, with v4's line kept or not: what the next change is offered (the version strip's sixth case)
    git("switch", "-q", "main")
    code3, back = pin_here()
    assert code3 == 0 and back == PIN_OUT + "exit 0\n", back
    assert git("branch", "--list", "prompt-v4").stdout == "  prompt-v4\n"
    OUT["UNDO"] = ("shape (gcloud's traffic table first; git's two lines; then prompt_pin.py on main, as this page's build printed it on the kit)",
                   "...\nthe candidate URL now: HTTP 404\nSwitched to branch 'main'\nYour branch is up to date with 'origin/main'.\n"
                   + back + "  prompt-v4\n")

    # ---------------------------------------------------------- the version strip's cases, each through prompt_pin itself
    def with_value(source: str, name: str, value: str) -> str:
        """source with the module-level string assigned to `name` replaced by `value`, written as a JSON literal."""
        stmt = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                    and n.targets[0].id == name)
        old = ast.get_source_segment(source, stmt)
        return source.replace(old, old.replace(ast.get_source_segment(source, stmt.value), json.dumps(value), 1), 1)

    SYS_NEXT = SYSTEM.replace("4. Keep answers under 300 words unless asked for more.", "4. Keep answers under 200 words unless asked for more.")
    SYS_SPACE = SYSTEM.replace("unless asked for more.\n", "unless asked for more. \n")
    assert SYS_NEXT != SYSTEM and SYS_SPACE != SYSTEM
    V_CASES = [
        {"label": "The kit as shipped: v3", "system": SYSTEM, "dated": DATED, "ver": "v3", "reg4": False},
        {"label": "Rule 5 weakened, prompt_version left at v3", "system": SYS_V4, "dated": DATED, "ver": "v3", "reg4": False},
        {"label": "prompt_version set to v4, its line not added", "system": SYS_V4, "dated": DATED, "ver": "v4", "reg4": False},
        {"label": "v4 registered: the branch's commit", "system": SYS_V4, "dated": DATED, "ver": "v4", "reg4": True},
        {"label": "Back on main, v4's line kept", "system": SYSTEM, "dated": DATED, "ver": "v3", "reg4": True},
        {"label": "Back on main, the next change", "system": SYS_NEXT, "dated": DATED, "ver": "v3", "reg4": True},
        {"label": "DATED_RULE changed, SYSTEM not", "system": SYSTEM, "dated": DATED + " Name that date.", "ver": "v3", "reg4": False},
        {"label": "v4's label on v3's text", "system": SYSTEM, "dated": DATED, "ver": "v4", "reg4": True},
        {"label": "One space more, at the end of rule 4", "system": SYS_SPACE, "dated": DATED, "ver": "v3", "reg4": False},
    ]
    for i, case in enumerate(V_CASES):
        kit = TMP / f"vcase{i}"
        (kit / "services" / "rag-api").mkdir(parents=True)
        (kit / GEN).write_text(with_value(with_value(GEN_SRC, "SYSTEM", case["system"]), "DATED_RULE", case["dated"]),
                               encoding="utf-8", newline="\n")
        (kit / CFG).write_text(CFG_SRC.replace(f'    prompt_version: str = "{VERSION}"\n', f'    prompt_version: str = "{case["ver"]}"\n'),
                               encoding="utf-8", newline="\n")
        versions = {LABEL: V3_SHA, **({f"{PROMPT_ID}@v4": V4_SHA} if case["reg4"] else {})}
        (kit / REG).write_text(json.dumps({"versions": versions}, indent=2) + "\n", encoding="utf-8", newline="\n")
        case["code"], case["lines"] = pp.check(kit)
    assert [c["code"] for c in V_CASES] == [0, 1, 1, 0, 0, 1, 1, 1, 1], [c["code"] for c in V_CASES]
    assert 'Set prompt_version to "v5"' in "\n".join(V_CASES[5]["lines"]) and "This text is registered as documind-rag@v3" in "\n".join(V_CASES[7]["lines"])
    assert V_CASES[2]["lines"][3] == f"registry: {PROMPT_ID}@v4 is not registered ({REG})"
    # main of the copy again, the next change, the prompt-v4 branch kept: v4 is spent there, so v5 is offered. The kit
    # reads every version of the registry git keeps (13 October 2026); the strip reads the file alone, as a copy outside
    # git would, and offers v4 when v4's line is not ticked.
    (REPO / GEN).write_text(with_value(GEN_SRC, "SYSTEM", SYS_NEXT), encoding="utf-8", newline="\n")
    code4, spent_out = pin_here()
    assert code4 == 1 and f'Set prompt_version to "v5" in {CFG}, then add' in spent_out, spent_out
    git("checkout", "--", GEN)
    assert git("status", "--short").stdout == "" and git("branch", "--list", "prompt-v4").stdout == "  prompt-v4\n"

    # ---------------------------------------------------------- lane cells against stand-ins
    STAND_IN = r'''import io, json, sys, types, urllib.request
class R:
    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0
ENTRIES, TRAFFIC = json.loads(%r), json.loads(%r)
def run(cmd, **kw):
    if cmd[1:3] == ["logging", "read"]:
        return R(json.dumps(ENTRIES))
    if cmd[1:4] == ["run", "services", "describe"]:
        return R(json.dumps(TRAFFIC))
    raise SystemExit("unexpected command: " + " ".join(cmd))
fake = types.ModuleType("subprocess"); fake.run = run; sys.modules["subprocess"] = fake
'''

    def entry(rev: str, **p) -> dict:
        """One Cloud Logging entry as gcloud logging read returns it."""
        return {"resource": {"labels": {"revision_name": rev}}, "jsonPayload": p}

    LIVE_REV, CAND_REV = "documind-api-00042-liv", "documind-api-00043-v4c"
    entries = ([entry(LIVE_REV, event="query", prompt_version="v3", tokens_out=300) for _ in range(10)]
               + [entry(LIVE_REV, event="passages", prompt_version="v3", tokens_out=0) for _ in range(20)]
               + [entry(CAND_REV, event="query", prompt_version="v4", tokens_out=280) for _ in range(10)]
               + [entry(CAND_REV, event="passages", prompt_version="v4", tokens_out=0) for _ in range(10)])
    traffic = {"status": {"traffic": [{"revisionName": LIVE_REV, "percent": 100}, {"revisionName": CAND_REV, "tag": "candidate"}]}}
    lane_env = {**QUIET, "PROJECT": PROJ, "REGION": "asia-south1"}
    rows_out = run_cell(PY_ROWS, TMP, lane_env, STAND_IN % (json.dumps(entries), json.dumps(traffic)))
    assert rows_out.startswith("50 usage rows from documind-api in the last 6 h") and f"rows that say v4 come from: {CAND_REV}; serving traffic among them: none" in rows_out, rows_out
    assert f"  {CAND_REV:30} none     query     v4         10       2800" in rows_out, rows_out
    for env_list, want in (([], "not set, so config.py names the version"), ([{"name": "PROMPT_VERSION", "value": "v3"}], "v3")):
        desc = {"spec": {"template": {"spec": {"containers": [{"env": [{"name": "GIT_SHA", "value": "abc1234"}, *env_list]}]}}}}
        r = subprocess.run([sys.executable, "-c", PY_ENVCHECK], input=json.dumps(desc), capture_output=True, text=True, encoding="utf-8", env=QUIET)
        assert r.returncode == 0 and r.stdout == f"PROMPT_VERSION on the service: {want}\n", (r.stdout, r.stderr)
    r = subprocess.run([sys.executable, "-c", PY_VERSION, CAND, "abc1234"], capture_output=True, text=True, encoding="utf-8", env=QUIET,
                       input=json.dumps({"prompt": f"{PROMPT_ID}@v4", "git_sha": "abc1234", "generator_model": "x"}))
    assert r.stdout == f"{CAND} | prompt {PROMPT_ID}@v4 | git_sha abc1234 | this commit: True\n", (r.stdout, r.stderr)

    # ---------------------------------------------------------- the two benches' rules, in node, against the kit's
    def icbrt(n: int) -> int:
        """The integer cube root of n."""
        x = int(round(n ** (1 / 3)))
        while x ** 3 > n:
            x -= 1
        while (x + 1) ** 3 <= n:
            x += 1
        return x

    PRIMES = [p for p in range(2, 312) if all(p % d for d in range(2, int(p ** 0.5) + 1))][:64]
    K256 = [icbrt(p << 96) & 0xFFFFFFFF for p in PRIMES]
    H256 = [math.isqrt(p << 64) & 0xFFFFFFFF for p in PRIMES[:8]]
    assert len(PRIMES) == 64 and K256[0] == 0x428A2F98 and K256[-1] == 0xC67178F2 and H256[0] == 0x6A09E667

    QC_CORE = r"""function flat(s){ return String(s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }
function head(s, n){ return Array.from(String(s)).slice(0, n).join(''); }
function quoteCheck(cit, pool){
  pool = (pool || []).filter(function(p){ return p && typeof p === 'object'; });
  var own = null, i;
  for (i = 0; i < pool.length; i++) if (pool[i].chunk_id && pool[i].chunk_id === cit.chunk_id) { own = pool[i]; break; }
  if (!own) return {v: 'unread'};
  var quote = cit.quote || '', text = own.text || '';
  if (flat(quote) === flat(head(text, 500))) return {v: 'substituted', own: own};
  var words = flat(quote), dots = false;
  if (words.slice(-3) === '...') { words = words.slice(0, -3).replace(/\s+$/, ''); dots = true; }
  if (!words) return {v: 'absent', own: own, dots: dots, empty: true};
  if (flat(text).indexOf(words) >= 0) return {v: 'own', own: own, dots: dots};
  var other = pool.filter(function(p){ return p !== own && flat(p.text).indexOf(words) >= 0; });
  if (other.length) return {v: 'elsewhere', own: own, dots: dots, other: other};
  return {v: 'absent', own: own, dots: dots};
}"""
    PP_CORE = (r"""var K256 = __K__, H256 = __H__;
function sha256hex(str){
  var b = new TextEncoder().encode(str), n = b.length, L = Math.ceil((n + 9) / 64) * 64, m = new Uint8Array(L), w = new Array(64), H = H256.slice(), t, o;
  m.set(b); m[n] = 0x80;
  var hi = Math.floor(n / 536870912), lo = (n * 8) >>> 0;
  m[L - 8] = hi >>> 24; m[L - 7] = (hi >>> 16) & 255; m[L - 6] = (hi >>> 8) & 255; m[L - 5] = hi & 255;
  m[L - 4] = lo >>> 24; m[L - 3] = (lo >>> 16) & 255; m[L - 2] = (lo >>> 8) & 255; m[L - 1] = lo & 255;
  for (o = 0; o < L; o += 64) {
    for (t = 0; t < 16; t++) w[t] = (m[o + 4 * t] << 24) | (m[o + 4 * t + 1] << 16) | (m[o + 4 * t + 2] << 8) | m[o + 4 * t + 3];
    for (t = 16; t < 64; t++) {
      var x = w[t - 15], y = w[t - 2];
      var s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3), s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
      w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
    }
    var a = H[0], bb = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
    for (t = 0; t < 64; t++) {
      var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7)), ch = (e & f) ^ (~e & g);
      var t1 = (h + S1 + ch + K256[t] + w[t]) | 0;
      var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10)), mj = (a & bb) ^ (a & c) ^ (bb & c);
      h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = bb; bb = a; a = (t1 + ((S0 + mj) | 0)) | 0;
    }
    H[0] = (H[0] + a) | 0; H[1] = (H[1] + bb) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
    H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
  }
  return H.map(function(v){ return ('00000000' + (v >>> 0).toString(16)).slice(-8); }).join('');
}
function escRe(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function nextVersion(name, versions){
  var at = name.indexOf('@'), pid = at < 0 ? name : name.slice(0, at), re = new RegExp('^' + escRe(pid) + '@v(\\d+)$'), nums = [];
  Object.keys(versions).concat([name]).forEach(function(k){ var m = re.exec(k); if (m) nums.push(parseInt(m[1], 10)); });
  return nums.length ? 'v' + (Math.max.apply(null, nums) + 1) : '<new version>';
}
function pinCheck(system, dated, pid, version, versions, F){
  var text = system + dated, name = pid + '@' + version, digest = sha256hex(text);
  var lines = ['prompt:   ' + name + ' (' + F.cfg + ': prompt_id@prompt_version, as /version reports it)',
               'text:     SYSTEM + DATED_RULE, ' + Array.from(text).length + ' characters, as generate() joins them (' + F.gen + ')',
               'sha256:   ' + digest];
  if (versions[name] === digest) return {code: 0, digest: digest, lines: lines.concat(['registry: ' + name + ' has this sha256 (' + F.reg + '): the text is the one its version names'])};
  var same = Object.keys(versions).filter(function(k){ return versions[k] === digest; }).sort();
  var sw = same.length ? 'set prompt_version to "' + same[0].slice(same[0].indexOf('@') + 1) + '" in ' + F.cfg : '';
  var add = function(l){ return ['    "' + l + '": "' + digest + '"', 'to "versions" in ' + F.reg + ', keeping the lines already there.']; };
  if (!Object.prototype.hasOwnProperty.call(versions, name)) {
    lines.push('registry: ' + name + ' is not registered (' + F.reg + ')', 'Register it: add');
    lines = lines.concat(add(name));
    if (same.length) lines.push('Or, since this text is registered as ' + same[0] + ', ' + sw + '.');
  } else if (same.length) {
    lines.push('registry: ' + name + ' has another sha256, ' + versions[name], 'This text is registered as ' + same[0] + ': ' + sw + ', or restore ' + name + "'s text.");
  } else {
    var nv = nextVersion(name, versions);
    lines.push('registry: ' + name + ' has another sha256, ' + versions[name] + ': SYSTEM or DATED_RULE changed and prompt_version did not',
               'A changed prompt needs a new version. Set prompt_version to "' + nv + '" in ' + F.cfg + ', then add');
    lines = lines.concat(add(pid + '@' + nv));
  }
  return {code: 1, digest: digest, lines: lines};
}
function scopeOf(version, topK){ return sha256hex('{"filters": {}, "prompt": ' + JSON.stringify(version) + ', "top_k": ' + topK + '}').slice(0, 16); }"""
               .replace("__K__", json.dumps(K256)).replace("__H__", json.dumps(H256)))

    # the quote bench's data: the pool, the passage it cannot read, the nine cases with the kit's own verdicts
    EXTRA = PASS["EXP-12"]
    NINE_CASES_SRC = re.search(r"cases = \[(.*?)\]\ngot", PY_NINE, re.S).group(1)
    said = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
    whole = " ".join(PASS["GEN-000"]["text"].split("\n", 1)[1].split())
    empty = resolve(ModelDraft(answer="60 days [1].", confidence="high", answerable=True,
                               citations=[DraftCitation(source=1, quote="")]), POOL).citations[0].quote
    # the prose's claims about resolve(): a source cited only in the answer's prose gets the same opening as an empty
    # quote, and substituted is its verdict; one citation a chunk, the first quote kept
    bare = resolve(ModelDraft(answer="60 days [1].", confidence="high", answerable=True, citations=[]), POOL).citations
    assert [c.quote for c in bare] == [empty] == [POOL[0]["text"][:QUOTE_CIT]]
    assert rv.quote_check({"chunk_id": bare[0].chunk_id, "quote": bare[0].quote}, POOL) == "substituted"
    pair = resolve(ModelDraft(answer="60 days [1, 2].", confidence="high", answerable=True,
                              citations=[DraftCitation(source=1, quote=said)]), POOL).citations
    assert [(c.chunk_id, c.quote) for c in pair] == [(POOL[0]["chunk_id"], said), (POOL[1]["chunk_id"], POOL[1]["text"][:QUOTE_CIT])]
    twice = resolve(ModelDraft(answer="60 days [1].", confidence="high", answerable=True,
                               citations=[DraftCitation(source=1, quote=said), DraftCitation(source=1, quote="60 days")]), POOL).citations
    assert [c.quote for c in twice] == [said]
    QCASES = [("NP-03", said, "the sentence, under its own passage"),
              ("NP-03", "NOTICE RUNS from the date the resignation is acknowledged in writing.", "a line break, in capitals"),
              ("PB-02", said, "the same sentence, under [2]"),
              ("NP-03", "Confirmed E3 staff give 60 days' notice.", "a paraphrase"),
              ("NP-03", said.replace("60 days", "90 days"), "revision 2's figure"),
              ("NP-03", empty, "an empty quote, filled in by resolve()"),
              ("GEN-000", whole[:QUOTE_DRAFT - 3].rstrip() + "...", "_draft()'s cut of a whole section"),
              ("NP-03", "A confirmed employee ... serves a notice period of 60 days.", "an elision, mid-sentence"),
              ("EXP-12", said, "a passage the pool did not hold")]
    for code, _q, label in QCASES:                       # the bench's cases are the cell's, label for label
        assert f'"{label}")' in NINE_CASES_SRC and f'("{code}",' in NINE_CASES_SRC, label
    SOURCES = POOL + [EXTRA]
    qcases = []
    for code, quote, label in QCASES:
        c = {"chunk_id": PASS[code]["chunk_id"], "source_uri": URI, "quote": quote}
        qcases.append({"label": label, "src": [p["chunk_id"] for p in SOURCES].index(c["chunk_id"]), "quote": quote,
                       "v": rv.quote_check(c, POOL), "corpus": rv.judge_citations(LK06, [c], None, {}, CORPUS_TEXT)[1]})
    assert [(q["v"], q["corpus"]) for q in qcases] == want_nine
    # more cases for node, from the kit's own test: own wins over a second passage; an empty quote; dots alone; trailing space
    boiler = "It applies to all employees and to contractors working on ACME premises or systems."
    extra_cases = [(PASS["GEN-001"]["chunk_id"], boiler), (PASS["NP-03"]["chunk_id"], ""), (PASS["NP-03"]["chunk_id"], "..."),
                   (PASS["NP-03"]["chunk_id"], "Notice runs from the date the resignation is acknowledged ..."),
                   (PASS["PB-02"]["chunk_id"], "  probation may be EXTENDED once  "), (PASS["LV-07"]["chunk_id"], PASS["LV-07"]["text"]),
                   (PASS["GEN-000"]["chunk_id"], PASS["GEN-000"]["text"][:500]), ("acme:nowhere#9", "anything")]
    node_qc = [{"c": {"chunk_id": cid, "quote": q}, "py": rv.quote_check({"chunk_id": cid, "quote": q}, POOL)} for cid, q in extra_cases]
    node_qc += [{"c": {"chunk_id": SOURCES[q["src"]]["chunk_id"], "quote": q["quote"]}, "py": q["v"]} for q in qcases]
    assert {x["py"] for x in node_qc} == set(rv.QUOTE_VERDICTS)
    sha_inputs = [TEXT, V4_TEXT, "", "abc", "a" * 55, "a" * 56, "a" * 64, "— " * 300, SYS_SPACE + DATED]
    FILES = {"gen": GEN, "cfg": CFG, "reg": REG}
    node_pp = [{"system": c["system"], "dated": c["dated"], "ver": c["ver"],
                "versions": {LABEL: V3_SHA, **({f"{PROMPT_ID}@v4": V4_SHA} if c["reg4"] else {})}, "code": c["code"], "lines": c["lines"]}
               for c in V_CASES]
    test_js = ("'use strict';\n" + QC_CORE + "\n" + PP_CORE + "\n"
               + "var POOL = " + json.dumps(POOL) + ", QC = " + json.dumps(node_qc) + ", SH = " + json.dumps(sha_inputs)
               + ", PP = " + json.dumps(node_pp) + ", F = " + json.dumps(FILES) + ";\n"
               + "console.log(JSON.stringify({qc: QC.map(function(x){ return quoteCheck(x.c, POOL).v; }), sh: SH.map(sha256hex),"
               + " pp: PP.map(function(x){ var r = pinCheck(x.system, x.dated, " + json.dumps(PROMPT_ID) + ", x.ver, x.versions, F); return [r.code, r.lines]; }),"
               + " scope: ['v3', 'v4', 'v5'].map(function(v){ return scopeOf(v, " + str(UI_TOP_K) + "); })}));\n")
    tjs = TMP / "benches.js"
    tjs.write_text(test_js, encoding="utf-8")
    node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
    assert node.returncode == 0, node.stderr[-1500:]
    js = json.loads(node.stdout)
    assert js["qc"] == [x["py"] for x in node_qc], list(zip(js["qc"], [x["py"] for x in node_qc]))
    assert js["sh"] == [hashlib.sha256(s.encode("utf-8")).hexdigest() for s in sha_inputs]
    assert js["pp"] == [[c["code"], c["lines"]] for c in V_CASES], js["pp"]
    assert js["scope"] == [scope_of(v) for v in ("v3", "v4", "v5")]
finally:
    shutil.rmtree(TMP, ignore_errors=True)

# ------------------------------------------------------------------ the author's lane, recorded once
LANE = "(the author's lane: your answers, quotes, tokens and times are yours)"
OUT["LIVE"] = ("(the author's lane: the scoped gate on the live revision with the switch on; your rates and rows are yours)",
               pb.recorded(LESSON, "quotes_live.txt"))
OUT["CITES"] = (LANE, pb.recorded(LESSON, "quotes_live_cites.txt"))
OUT["BENCH"] = ("(the author's lane: the edit arm's prompt sha256 is the same on every lane; the answers and rupees are yours)",
                pb.recorded(LESSON, "bench_v4.txt"))
OUT["SHIP"] = ("(the author's lane, Cloud Build's own log cut to its first and last lines; your revision names and times are yours)",
               pb.recorded(LESSON, "ship_v4.txt"))
OUT["VERSION"] = ("(the author's lane: COMMIT is each revision's short sha)", pb.recorded(LESSON, "version_v4.txt"))
OUT["CAND"] = ("(the author's lane: the same ten rows on the candidate; your rates and rows are yours)", pb.recorded(LESSON, "quotes_candidate.txt"))
OUT["COMPARE"] = (LANE, pb.recorded(LESSON, "quotes_compare.txt"))
OUT["ROWS"] = ("(the author's lane: your revision names and counts are yours)", pb.recorded(LESSON, "rows_v4.txt"))


# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, and it has a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected-output window: read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k}": out_window(*v) for k, v in OUT.items()})
assert set(CELLS) == set(OUT), set(CELLS) ^ set(OUT)

# ------------------------------------------------------------------ the two benches' script
QDATA = {"pool": [{"chunk_id": p["chunk_id"], "n": p["n"], "section": p["section"], "text": p["text"]} for p in POOL],
         "extra": {"chunk_id": EXTRA["chunk_id"], "n": EXTRA["n"], "section": EXTRA["section"], "text": EXTRA["text"]},
         "cases": [{"label": q["label"], "src": q["src"], "quote": q["quote"], "corpus": q["corpus"]} for q in qcases],
         "corpusChars": CORPUS_CHARS, "cit": QUOTE_CIT}
VDATA = {"pid": PROMPT_ID, "files": FILES, "v3": V3_SHA, "v4": V4_SHA, "label": LABEL, "topK": UI_TOP_K, "echo": MAKE_ECHO, "err": MAKE_ERR,
         "cases": [{"label": c["label"], "system": c["system"], "dated": c["dated"], "ver": c["ver"], "reg4": c["reg4"]} for c in V_CASES]}
UI_JS = r"""function esc(t){ return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function card(title, body, cls){ return '<div class="qb-step' + (cls ? ' ' + cls : '') + '"><b>' + esc(title) + '</b>' + body + '</div>'; }
function chip(v, text){ return '<span class="qb-v v-' + v + '">' + esc(text || v) + '</span>'; }
function short(p){ return '#' + p.n + ' ' + p.section; }
(function(){
  var root = document.getElementById('qcheck'); if (!root) return;
  var sources = Q.pool.concat([Q.extra]), caseSel = document.getElementById('qc-case'), srcSel = document.getElementById('qc-src');
  var ta = document.getElementById('qc-quote'), out = document.getElementById('qc-out'), poolBox = document.getElementById('qc-pool'), current = -1;
  caseSel.innerHTML = '<option value="">choose a case</option>' + Q.cases.map(function(c, i){ return '<option value="' + i + '">' + esc(c.label) + '</option>'; }).join('');
  srcSel.innerHTML = sources.map(function(p, i){ return '<option value="' + i + '">' + (i < Q.pool.length ? '[' + (i + 1) + '] ' : '[not in the pool] ') + esc(short(p)) + '</option>'; }).join('');
  poolBox.innerHTML = '<p class="dg-cap">The pool read back, in [Source N] order:</p>' + Q.pool.map(function(p, i){
    return '<details' + (i ? '' : ' open') + '><summary>[' + (i + 1) + '] ' + esc(short(p)) + ', ' + Array.from(p.text).length + ' characters</summary><p>' + esc(p.text) + '</p></details>'; }).join('');
  function corpusLine(quote, r){
    var c = Q.cases[current];
    if (c && c.quote === quote && String(c.src) === srcSel.value) return (c.corpus ? 'supported' : 'not supported') + ': judge_citations() over acme\'s whole corpus, ' + Q.corpusChars + ' characters, when this page was built';
    var q = flat(quote);
    if (!q) return 'supported: judge_citations() does not look for an empty quote';
    if (sources.some(function(p){ return flat(p.text).indexOf(q) >= 0; })) return 'supported: its words are in a passage cut from an acme document, so they are in the corpus';
    return 'not decided here: its words are in none of the seven passages this page holds, and judge_citations() searches every acme document (step 3\'s cell runs it)';
  }
  function render(){
    var src = sources[+srcSel.value], quote = ta.value, r = quoteCheck({chunk_id: src.chunk_id, quote: quote}, Q.pool), steps = [];
    var said = {own: 'The words of the passage the citation names.', elsewhere: 'Real words, under the wrong [Source N].', absent: 'Words the model wrote, not words it read.',
                substituted: 'Nothing was quoted: resolve() filled in the passage\'s opening, and nothing is supported.', unread: 'Not judged: the passage it names was not read back, so the rate leaves it out.'}[r.v];
    steps.push(card('the verdict', chip(r.v) + esc(said) + '<br>corpus measure: ' + esc(corpusLine(quote, r)), {own: 'ok', elsewhere: 'flag', substituted: 'flag', absent: 'stop', unread: 'skip'}[r.v]));
    var idx = Q.pool.indexOf(r.own);
    if (r.v === 'unread') { steps.push(card('1 · the passage it names', esc(short(src)) + ' is not in the pool read back, so quote_check() returns unread before it reads a word.', 'skip')); out.innerHTML = steps.join(''); return; }
    steps.push(card('1 · the passage it names', '[' + (idx + 1) + '] ' + esc(short(src)) + ' is in the pool read back: the quote can be held against it.'));
    if (r.v === 'substituted') { steps.push(card('2 · substituted?', 'Yes: the quote is this passage\'s first ' + Q.cit + ' characters, whitespace collapsed. resolve() puts them there when the model\'s quote is empty, and when the answer cites this passage only as an [N] in its prose.', 'flag')); out.innerHTML = steps.join(''); return; }
    steps.push(card('2 · substituted?', 'No: the quote is not the passage\'s first ' + Q.cit + ' characters.'));
    steps.push(card('3 · the generator\'s dots', r.dots ? 'A trailing ... is dropped first: _draft() adds it when it cuts an over-long quote, and the document never wrote it.' : 'No trailing ... to drop.'));
    if (r.empty) { steps.push(card('4 · what is left', 'Nothing to look for: absent.', 'stop')); out.innerHTML = steps.join(''); return; }
    if (r.v === 'own') { steps.push(card('4 · its own passage', 'Found in [' + (idx + 1) + '], whitespace collapsed and case folded: own.', 'ok')); out.innerHTML = steps.join(''); return; }
    steps.push(card('4 · its own passage', 'Not in [' + (idx + 1) + '].'));
    if (r.v === 'elsewhere') steps.push(card('5 · the rest of the pool', 'Found in ' + r.other.map(function(p){ return '[' + (Q.pool.indexOf(p) + 1) + '] ' + esc(short(p)); }).join(', ') + ': elsewhere.', 'flag'));
    else steps.push(card('5 · the rest of the pool', 'In no passage of the pool: absent.', 'stop'));
    out.innerHTML = steps.join('');
  }
  function pick(i){ var c = Q.cases[i]; current = i; srcSel.value = String(c.src); ta.value = c.quote; render(); }
  caseSel.addEventListener('change', function(){ if (caseSel.value !== '') pick(+caseSel.value); });
  srcSel.addEventListener('change', render); ta.addEventListener('input', render);
  pick(0); caseSel.value = '0';
})();
(function(){
  var root = document.getElementById('vstrip'); if (!root) return;
  var caseSel = document.getElementById('vs-case'), ver = document.getElementById('vs-ver'), reg = document.getElementById('vs-reg');
  var sys = document.getElementById('vs-system'), dated = document.getElementById('vs-dated'), out = document.getElementById('vs-out');
  caseSel.innerHTML = '<option value="">choose a case</option>' + V.cases.map(function(c, i){ return '<option value="' + i + '">' + esc(c.label) + '</option>'; }).join('');
  function render(){
    var versions = {}; versions[V.label] = V.v3; if (reg.checked) versions[V.pid + '@v4'] = V.v4;
    var r = pinCheck(sys.value, dated.value, V.pid, ver.value, versions, V.files), name = V.pid + '@' + ver.value, steps = [];
    var term = V.echo + '\n' + r.lines.join('\n') + '\n' + (r.code ? V.err + '\nexit 2' : 'exit 0');
    steps.push(card('make prompt-version', chip(r.code ? 'exit2' : 'exit0', r.code ? 'exit 2' : 'exit 0') + (r.code ? 'prompt_pin exits 1, and make 2: this label does not name this text.' : 'The label names exactly this text.') + '<pre>' + esc(term) + '</pre>', r.code ? 'stop' : 'ok'));
    var scope = scopeOf(ver.value, V.topK), v3scope = scopeOf('v3', V.topK);
    steps.push(card('where the label goes', '<dl class="qb-path"><dt>/version</dt><dd><code>"prompt": "' + esc(name) + '"</code></dd>'
      + '<dt>every usage row</dt><dd><code>"prompt_version": "' + esc(ver.value) + '"</code>, on query, stream and passages rows alike</dd>'
      + '<dt>the stream\'s done</dt><dd><code>"prompt": "' + esc(name) + '"</code></dd>'
      + '<dt>the answer cache</dt><dd>scope <code>' + scope + '</code> for the UI\'s request' + (ver.value === 'v3' ? ', the scope v3\'s answers are stored under' : ', so every answer stored under v3 (<code>' + v3scope + '</code>) is a miss') + '</dd>'
      + '<dt>tenant_daily</dt><dd>its own row a day, per tenant and surface, for <code>' + esc(ver.value) + '</code></dd></dl>'
      + (r.code ? 'The service writes this label whatever the registry says: nothing in it reads the registry. The check is what makes a label name one text.' : '')));
    out.innerHTML = steps.join('');
  }
  function pick(i){ var c = V.cases[i]; sys.value = c.system; dated.value = c.dated; ver.value = c.ver; reg.checked = c.reg4; render(); }
  caseSel.addEventListener('change', function(){ if (caseSel.value !== '') pick(+caseSel.value); });
  [sys, dated].forEach(function(el){ el.addEventListener('input', render); });
  [ver, reg].forEach(function(el){ el.addEventListener('change', render); });
  pick(0); caseSel.value = '0';
})();"""
JS = ("<script>\n(function(){\n'use strict';\nvar Q = " + json.dumps(QDATA, separators=(",", ":")).replace("</", "<\\/")
      + ";\nvar V = " + json.dumps(VDATA, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + QC_CORE + "\n" + PP_CORE + "\n" + UI_JS + "\n})();\n</script>\n")
for bad in ("innerHeight", "scrollIntoView", "—", "–"):
    assert bad not in JS, bad

# ------------------------------------------------------------------ numbers for the prose
PRICES: dict = {}
exec(compile((KIT / "shared" / "prices.py").read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
GEN_MODEL = re.search(r'generator_model: str = "([^"]+)"', CFG_SRC).group(1)
TYPICAL = (2000, 300)                    # the course's typical answer (lessons 4.3, 4.4 and 11.6): 2,000 tokens in, 300 out
RATE_IN, RATE_OUT = PRICES["PRICES"][GEN_MODEL]
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * PRICES["USD_INR"]
assert PRICES["USD_INR"] == 85 and (RATE_IN, RATE_OUT) == (1.50, 7.50) and GEN_MODEL == "gemini-3.6-flash"
N_SCOPED = len(SCOPED)
N_RUNS = 3                               # the scoped gate twice (steps 4 and 7) and the bench once (step 6), N_SCOPED answers each
WORD = {5: "five", 9: "nine", 10: "ten"}
STATS = {
    "LABEL": LABEL, "LABEL_V4": f"{PROMPT_ID}@v4", "N_VERDICTS": str(len(rv.QUOTE_VERDICTS)),
    "N_VERDICTS_WORD": WORD[len(rv.QUOTE_VERDICTS)], "N_ANSWERS": str(N_SCOPED * N_RUNS), "UI_TIP": str(UI_TIP),
    "V3_SHA": V3_SHA, "V3_SHORT": V3_SHA[:12], "V4_SHA": V4_SHA, "V4_SHORT": V4_SHA[:12],
    "TEXT_CHARS": str(len(TEXT)), "V4_CHARS": str(len(V4_TEXT)), "QUOTE_DRAFT": str(QUOTE_DRAFT), "QUOTE_CIT": str(QUOTE_CIT),
    "STREAM_QUOTE": str(STREAM_QUOTE), "UI_QUOTE": str(UI_QUOTE), "TOP_K": str(TOP_K), "UI_TOP_K": str(UI_TOP_K),
    "CORPUS_CHARS": CORPUS_CHARS, "N_SCOPED": str(N_SCOPED), "SOURCE": SOURCE,
    "RULE5_OLD": html.escape(RULE5_OLD[3:]), "RULE5_NEW": html.escape(RULE5_NEW[3:]), "QUOTE_WORDS": QUOTE_WORDS,
    "SI_SUPPORT": SI["quote_support_rate"], "SI_PASSAGE": SI["quote_passage_rate"], "SI_RECALL": SI["must_retrieve_recall"],
    "REWRITE_PV": REWRITE_PV, "ROUTER_PV": ROUTER_PV,
    "MK_LINE": str(MK_LINE), "SCOPE_V3": scope_of("v3"), "SCOPE_V4": scope_of("v4"), "N_TESTS": str(N_TESTS),
    "GEN_MODEL": GEN_MODEL, "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": str(PRICES["USD_INR"]),
    "RS_ANSWER": f"{RS_ANSWER:.2f}", "RS_SCOPED": f"{RS_ANSWER * N_SCOPED:.1f}", "RS_ALL": f"{RS_ANSWER * N_SCOPED * N_RUNS:.0f}",
}


def subst(text: str) -> str:
    """Every %%NAME%% of a part: a window or a number."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body_html = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body_html, JS)
print(f"kit: {LABEL} = {V3_SHA[:12]} ({len(TEXT)} characters); v4's rule 5 = {V4_SHA[:12]} ({len(V4_TEXT)}), the bench's edit equal | "
      f"nine quotes: {', '.join(v for v, _ in want_nine)} | stand-in gate: support {SI['quote_support_rate']}, passage "
      f"{SI['quote_passage_rate']}, recall {SI['must_retrieve_recall']}, exit 0 | {len(node_qc)} quote cases, {len(sha_inputs)} sha256s, "
      f"{len(V_CASES)} version cases equal in node | branch: refused, registered, {N_TESTS} tests OK | lane cells passed against stand-ins")
