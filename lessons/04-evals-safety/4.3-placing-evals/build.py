"""Build lesson 4.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Place evals in the pipeline: where each instrument of lesson 4.2 runs, and what it can and cannot catch there. CI
(documind-dryrun.yml on every push, and documind-cd.yml's eval-gate job, which every release job needs) runs
run_eval.py's offline checks, which never call the model. The candidate gate runs make eval-live against a revision
that takes no traffic: run_eval's THRESHOLDS and the ids of required.json. Live traffic has no gate: every answer
writes one usage row, which holds no question and no answer, and terraform/alerts.tf reads two rates from the API's
traffic, the unanswerable share per tenant and the p95 latency. The judge advises.

Computed here, offline, from the kit:
  - the placement matrix. For each failure: run_eval.offline() over the golden set with the failure planted, with
    ask() replaced by a function that fails if called, so an offline check that reached for the model would break
    this build; run_eval.live() against a stub API that fails the way the row says (lesson 4.2's stub, extended);
    main.py's own two expressions, the stream's verdict and the row's flag, evaluated against alerts.tf's two
    policies, whose numbers are parsed from the file; and what judge.py asks and returns, read from its source;
  - the pipeline cell, run on the kit's two workflow files;
  - the Change-it: the cell's own edit applied to a copy of the kit's evals in a throwaway git repository, then
    run_eval.py there, then git checkout; the kit's files are never written;
  - the report cell, over a stub's report; make candidate's and make usage's shapes, from the Makefile and from
    usage_rows.py's own tables.
Recorded from the author's lane with pb.recorded(): the gate on a candidate, the usage rows split by revision and
identity, one stream refusal with its row, and the alert's metrics, policies and windows (RUN_LIST.md says how). The
three lane cells behind the last three are also run here against a stand-in gcloud and API, so their code is tested
before a lane runs them.

    python pagekit/build.py 4.3
"""
import ast
import contextlib
import html
import io
import json
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

LESSON = "4.3"
title = ("<title>Lesson 4.3 Place evals in the pipeline: CI, the candidate gate and live traffic - the golden set checked "
         "on every push, a revision with no traffic gated before release, and the rows live traffic leaves | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
API = "https://documind-api-NUMBER.asia-south1.run.app"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the placement matrix: one button per failure, four verdicts, the four placements' own words below */
.pm-head,.pm-row{display:grid;grid-template-columns:minmax(0,1fr) repeat(4,minmax(48px,66px));gap:4px;align-items:center;}
.pm-head{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--slate);padding:0 7px 4px;}
.pm-head span{min-width:0;overflow-wrap:anywhere;}
.pm-head span + span{text-align:center;}
.pm-row{width:100%;font:inherit;font-size:12.5px;line-height:1.35;text-align:left;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:6px;margin:0 0 4px;cursor:pointer;min-height:max(44px,var(--touch));-webkit-tap-highlight-color:transparent;}
.pm-row[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);}
.pm-row:active{transform:scale(.99);}
.pm-name{min-width:0;overflow-wrap:anywhere;}
.pm-v{font-family:var(--mono);font-size:11px;text-align:center;border-radius:6px;padding:5px 2px;min-width:0;overflow-wrap:anywhere;}
.v-blocks{background:#d1fae5;color:#065f46;}
.v-pages{background:#fef3c7;color:#92400e;}
.v-partly{background:#fffbeb;color:#92400e;box-shadow:inset 0 0 0 1px #f59e0b;}
.v-advises{background:#e0f2fe;color:#075985;}
.v-misses{background:#f1f5f9;color:#64748b;}
.pm-detail{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin:10px 0 0;font-size:var(--small-size);line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pm-detail h5{font-size:var(--small-size);color:var(--navy);margin:0 0 4px;}
.pm-detail p{margin:0 0 6px;font-size:var(--small-size);}
.pm-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,165px),1fr));gap:8px;margin:8px 0;}
.pm-card{border:1px solid var(--border);border-radius:10px;padding:8px 10px;background:var(--bg);font-size:12.5px;line-height:1.5;min-width:0;}
.pm-card b{display:block;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);margin-bottom:4px;}
.pm-card .pm-v{display:inline-block;margin:0 0 6px;padding:3px 8px;}
.pm-card p{font-size:12.5px;margin:0;}
.pm-first{font-weight:700;color:var(--teal-dark);}
@media (hover:hover) and (pointer:fine){.pm-row:hover{border-color:var(--teal);}}
/* on a phone the failure's name takes its own line and the four verdicts share the width beneath it */
@media (max-width: 640px){.pm-head,.pm-row{grid-template-columns:repeat(4,minmax(0,1fr));gap:3px 4px;}.pm-head span:first-child,.pm-name{grid-column:1 / -1;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the "
         "duration and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head; step 5 makes the difference visible in the usage rows.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ verbatim kit excerpts
RE_, JG, USG = "evals/run_eval.py", "evals/judge.py", "evals/usage_rows.py"
DRY, CD = ".github/workflows/documind-dryrun.yml", ".github/workflows/documind-cd.yml"
MAIN, GEN, TF, DESK_TF = ("services/rag-api/main.py", "services/rag-api/generator.py", "terraform/alerts.tf",
                          "terraform/desk_alerts.tf")
EXCERPTS = {
    "offline": ("evals/run_eval.py - offline(): three checks over files, and no request to anything",
                block(RE_, "def offline() -> int:", end="# ------------------------------------------------------------- the figure, not the spelling")),
    "cd_gate": (".github/workflows/documind-cd.yml - eval-gate: the first job, the same line, no credential",
                block(CD, "  # ---------------------------------------------------------------- gate 1: mechanical",
                      end="  # ---------------------------------------------------------------- the lane's release (path: candidate)")),
    "cd_needs": (".github/workflows/documind-cd.yml - every release job needs it, and the flip needs a person",
                 block(CD, "  release-candidate:", n=3) + "\n...\n" + block(CD, "  promote:", n=4) + "\n...\n"
                 + block(CD, "  release-clouddeploy:", n=3)),
    "cd_tag": (".github/workflows/documind-cd.yml - the candidate answers as the tag, before the gate spends ten minutes",
               block(CD, "      # Before the gate spends ten minutes: the candidate answers as the tag being released.",
                     end="      - name: The live gate, on the candidate")),
    "release_candidate": ("Makefile - release-candidate: the built image on a revision with no traffic, recorded by name",
                          block("Makefile", "# 12.7's release unit.", end="# Traffic to the recorded candidate, by name.")),
    "required_fn": ("evals/run_eval.py - load_required(): a list in a file, so removing a row is a reviewed diff",
                    block(RE_, "def load_required() -> list[str]:", end="def check_coverage(")),
    "usage_row": ("services/rag-api/main.py - usage_row(): counts, clocks and flags; no question, no answer",
                  block(MAIN, '    return {"event": surface, "tenant": req.tenant_id, "user": user["email"],', end='@app.get("/health")')),
    "read_rows": ("evals/usage_rows.py - read_rows(): the payload only, so make usage never sees a revision",
                  block(USG, "def read_rows(", end="def p95(")),
    "stream_verdict": ("services/rag-api/main.py - /v1/stream: the row says answerable unless the pool was empty",
                       block(MAIN, "        # The row's verdict: a refusal for the empty pool; otherwise the stream still says answerable", n=8)),
    "query_row": ("services/rag-api/main.py - /v1/query: the row takes the model's own answerable",
                  block(MAIN, "    row = usage_row(req, user, ans.tokens_in, ans.tokens_out", n=4)),
    "no_schema": ("services/rag-api/generator.py - generate_stream(): no response schema, so the model returns no verdict",
                  block(GEN, "    No response_schema here on purpose: you cannot usefully stream structured", n=2)),
    "alert_metrics": ("terraform/alerts.tf - the two log metrics: every query and stream row, and the flagged ones, per tenant",
                      block(TF, 'resource "google_logging_metric" "unanswerable" {', n=9) + "\n...\n"
                      + block(TF, 'resource "google_logging_metric" "queries" {', n=8) + "\n...\n"
                      + block(TF, "  label_extractors = {", n=3, nth=2)),
    "alert_policy": ("terraform/alerts.tf - the policy: per tenant, five-minute windows, above 0.20 for 30 minutes",
                     block(TF, 'resource "google_monitoring_alert_policy" "unanswerable_rate" {', end="  notification_channels = local.alert_channel_ids")),
    "latency_policy": ("terraform/alerts.tf - the other policy: p95 of every request to documind-api, above 3 s for 5 minutes",
                       block(TF, "# Latency: documind-api's p95 over 3 s for 5 minutes.", end="  notification_channels = local.alert_channel_ids")),
    "desk_metric": ("terraform/desk_alerts.tf - the Desk's metric made the other choice: no service account counts",
                    block(DESK_TF, "# The router's metric counts people's turns only.", n=4) + "\n...\n"
                    + block(DESK_TF, '    NOT jsonPayload.user=~"[.]iam[.]gserviceaccount[.]com$"', n=1)),
    "judge_end": ("evals/judge.py - main(): the scores are printed, and the exit is 0 whatever they are",
                  block(JG, "    summary = evaluate(df, a.experiment, run_name", end='if __name__ == "__main__":')),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["offline"].rstrip().endswith("    return 0") and "check_coverage(golden)" in E["offline"], E["offline"][-120:]
assert E["cd_gate"].rstrip().endswith("run: python evals/run_eval.py"), E["cd_gate"][-80:]
assert E["cd_needs"].count("needs:") == 3 and "environment: production" in E["cd_needs"]
assert E["cd_tag"].rstrip().endswith("the gate would judge some other revision\" >&2; exit 1; }"), E["cd_tag"][-80:]
assert E["release_candidate"].rstrip().endswith("make promote moves traffic to it by name)\""), E["release_candidate"][-80:]
assert E["required_fn"].rstrip().endswith("return row[\"shape\"] in (\"version\", \"isolation\") or bool(row.get(\"must_cite_kind\"))")
assert E["usage_row"].rstrip().endswith('"brain": getattr(req, "brain", None) or "ui"}'), E["usage_row"][-80:]
assert E["read_rows"].rstrip().endswith('return [e["jsonPayload"] for e in json.loads(r.stdout or "[]") if "jsonPayload" in e]')
assert 'answerable, confidence = (False, "low") if empty else (True, hit.confidence if hit else "medium")' in E["stream_verdict"]
assert E["query_row"].count("ans.answerable") == 1 and '"query"' in E["query_row"]
assert E["alert_policy"].rstrip().endswith("}") and "threshold_value    = 0.20" in E["alert_policy"]
assert E["latency_policy"].rstrip().endswith("}") and "threshold_value = 3000" in E["latency_policy"]
assert E["judge_end"].rstrip().endswith("return 0"), E["judge_end"][-80:]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts
sys.path.insert(0, str(KIT / "evals"))
import run_eval as rv  # noqa: E402

golden = rv.load_golden()
corpus = rv.load_corpus()
required = rv.load_required()
TRUTH = {r["id"]: r for r in golden}
A_ROWS = [r for r in golden if r["answerable"]]
TENANTS = ("acme", "zeta", "globex")
per_tenant = {t: sum(r["tenant"] == t for r in golden) for t in TENANTS}
unans_tenant = {t: sum(r["tenant"] == t and not r["answerable"] for r in golden) for t in TENANTS}
ans_tenant = {t: per_tenant[t] - unans_tenant[t] for t in TENANTS}
REQ_KIND = {"version": [i for i in required if TRUTH[i]["shape"] == "version"],
            "isolation": [i for i in required if TRUTH[i]["shape"] == "isolation"],
            "media": [i for i in required if TRUTH[i]["shape"] not in ("version", "isolation") and TRUTH[i].get("must_cite_kind")]}
assert sum(map(len, REQ_KIND.values())) == len(required) and all(rv.mandatory(TRUTH[i]) for i in required)
OFFLINE_CHECKS = re.findall(r'\("(\w+)", check_\w+\(', E["offline"])
assert OFFLINE_CHECKS == ["falsifiable", "anchors", "coverage"], OFFLINE_CHECKS
N_DOCS = sum(len(v) for v in corpus.values())

# the workflows: read with the pipeline cell's own function (below), and the facts the page states
PY_PIPELINE_DEF = r'''import re, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def jobs_of(path):
    """A workflow's triggers, then each job: what it needs, its condition, who approves it, whether it signs in to Google, its eval lines."""
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    tops = [i for i, l in enumerate(lines) if not l.startswith(" ")] + [len(lines)]

    def section(key):
        i = lines.index(key)
        return lines[i + 1:next(t for t in tops if t > i)]
    triggers = [m.group(1) for l in section("on:") if (m := re.match(r"  ([\w-]+):", l))]
    body = section("jobs:")
    starts = [i for i, l in enumerate(body) if re.fullmatch(r"  [\w-]+:", l)] + [len(body)]
    jobs = []
    for a, b in zip(starts, starts[1:]):
        job = body[a + 1:b]
        key = lambda k: next((l.split(":", 1)[1].split("#")[0].strip() for l in job if l.startswith(f"    {k}:")), "")
        evals = [l.strip().removeprefix("run:").strip() for l in job if "run_eval.py" in l or "make eval-live" in l]
        jobs.append((body[a].strip(" :"), key("needs"), key("if"), key("environment"),
                     any("google-github-actions/auth" in l for l in job), evals))
    return triggers, jobs'''
PY_PIPELINE = PY_PIPELINE_DEF + r'''


for path in (".github/workflows/documind-dryrun.yml", ".github/workflows/documind-cd.yml"):
    triggers, jobs = jobs_of(path)
    print(f"{path.rsplit('/', 1)[1]}: on {', '.join(triggers)}")
    for name, needs, cond, env, google, evals in jobs:
        extra = (f", only if {cond.strip('${} ')}" if cond else "") + (f", then a person ({env} reviewers)" if env else "")
        print(f"  {name:19} needs {needs or '-':18} signs in to Google: {'yes' if google else 'no'}{extra}")
        for e in evals:
            print(f"      runs {e}")'''
ns: dict = {}
exec(compile(PY_PIPELINE_DEF, "pipeline-cell", "exec"), ns)
dry_on, dry_jobs = ns["jobs_of"](str(KIT / DRY))
cd_on, cd_jobs = ns["jobs_of"](str(KIT / CD))
JOB = {j[0]: j for j in cd_jobs}
assert dry_on == ["push", "pull_request", "workflow_dispatch"] and cd_on == ["workflow_dispatch"], (dry_on, cd_on)
assert [(j[0], j[4], j[5]) for j in dry_jobs] == [("tier-a", False, ["python evals/run_eval.py"])], dry_jobs
assert list(JOB) == ["eval-gate", "release-candidate", "promote", "release-clouddeploy"], list(JOB)
assert JOB["eval-gate"][1:] == ("", "", "", False, ["python evals/run_eval.py"]), JOB["eval-gate"]
assert JOB["release-candidate"][1] == "eval-gate" and JOB["release-candidate"][4] and JOB["release-candidate"][5][0].startswith("make eval-live ")
assert JOB["release-clouddeploy"][1] == "eval-gate" and JOB["release-clouddeploy"][5] == ['python evals/run_eval.py --api-url "$URL"']
assert JOB["promote"][1] == "release-candidate" and JOB["promote"][3] == "production" and not JOB["promote"][5]
for wf in (DRY, CD):                                   # no step of either workflow runs the judge
    assert not [line for line in (KIT / wf).read_text(encoding="utf-8").splitlines()
                if "judge.py" in line and not line.lstrip().startswith("#")], wf

# the Makefile: the targets the page runs, and what make candidate writes with no override
MK = (KIT / "Makefile").read_text(encoding="utf-8")
recipe = lambda name: MK[MK.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]      # noqa: E731
CAND_RECIPE = recipe("candidate")
env_part = CAND_RECIPE.split('"^|^', 1)[1].split("$(if", 1)[0]
PAIRS = re.findall(r"([A-Z_]+)=\$\(([A-Z_]+)\)", env_part)
DEFAULTS = {v: re.search(rf"^{v} +\?= *(\S*)$", MK, re.M).group(1) for _, v in PAIRS}
assert len(PAIRS) == 11 and all(k == v for k, v in PAIRS) and all(DEFAULTS.values()), (PAIRS, DEFAULTS)
assert re.search(r"^GENERATOR_LOCATION \?=$", MK, re.M) and not re.search(r"^RETRIEVAL_BACKEND\s*\??=", MK + "".join(
    p.read_text(encoding="utf-8") for p in (KIT / "mk").glob("*.mk")), re.M)
assert "$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)" in CAND_RECIPE
DEPLOY_12_2 = (KIT / "commands" / "lesson-12.2.sh").read_text(encoding="utf-8")
for k, v in DEFAULTS.items():
    assert f"{k}=${{{k}-{v}}}" in DEPLOY_12_2, (k, v)                 # make up deployed the API with the same values
ECHO_REV = re.search(r'echo ">> candidate revision: \$\$REV (\(deploy/\.candidate-revision - [^"]+\))"', recipe("record-candidate")).group(1)
ECHO_CAND = re.search(r'echo ">> candidate: https://candidate---documind-api-\$\$NUMBER\.\$\(REGION\)\.run\.app ([^"]+)"', CAND_RECIPE).group(1)
assert "$${API:-$$AUD}" in recipe("eval-live") and "$(if $(REPORT),--report $(REPORT),)" in recipe("eval-live")
assert "AUD=https://documind-api-$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)').$(REGION).run.app" in recipe("eval-live")
assert "--no-traffic --tag candidate" in recipe("release-candidate") and "record-candidate" in recipe("release-candidate")
USAGE_LINE = recipe("usage").splitlines()[1].strip()
assert USAGE_LINE == "$(PY) evals/usage_rows.py --project $(PROJECT) --hours $${HOURS:-24}", USAGE_LINE
cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
PROMPT = "{}@{}".format(re.search(r'prompt_id: str = "([\w-]+)"', cfg).group(1), re.search(r'prompt_version: str = "(\w+)"', cfg).group(1))
assert re.search(r'generator_model: str = "gemini-3.6-flash"', cfg) and DEFAULTS["GENERATOR_MODEL"] == "gemini-3.6-flash"
assert re.search(r'rag_distance_threshold: float = Field\(0\.5, alias="RAG_DISTANCE_THRESHOLD"\)', cfg)
RETRIEVER = (KIT / "services" / "rag-api" / "retriever.py").read_text(encoding="utf-8")
assert "filter=rag.Filter(vector_distance_threshold=settings.rag_distance_threshold)" in RETRIEVER
assert "an EMPTY outer list when the index" in RETRIEVER and "holds nothing for these restricts" in RETRIEVER

# main.py: the row's fields, the stream's verdict, the flag, the empty pool, the door before any row
MAIN_SRC = (KIT / MAIN).read_text(encoding="utf-8")
TREE = ast.parse(MAIN_SRC)
FN = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
ret = next(n for n in ast.walk(FN["usage_row"]) if isinstance(n, ast.Return))
ROW_KEYS = [k.value for k in ret.value.keys]
assert "user" in ROW_KEYS and not set(ROW_KEYS) & {"query", "question", "answer", "text", "revision", "revision_name"}, ROW_KEYS
N_ROW_FIELDS = len(ROW_KEYS)
FLAG_EXPR = ast.get_source_segment(MAIN_SRC, ret.value.values[ROW_KEYS.index("unanswerable_flag")])
verdict_assign = next(n for n in ast.walk(FN["sse"]) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple)
                      and [getattr(e, "id", None) for e in n.targets[0].elts] == ["answerable", "confidence"])
STREAM_EXPR = ast.get_source_segment(MAIN_SRC, verdict_assign.value)
assert FLAG_EXPR == "0 if answerable else 1" and STREAM_EXPR == '(False, "low") if empty else (True, hit.confidence if hit else "medium")'


def flag(answerable: bool) -> int:
    """usage_row()'s own expression for unanswerable_flag."""
    return eval(FLAG_EXPR, {}, {"answerable": answerable})


def stream_verdict(empty: bool) -> tuple:
    """/v1/stream's own expression for the row's (answerable, confidence), with no answer-cache hit."""
    return eval(STREAM_EXPR, {}, {"empty": empty, "hit": None})


rag_call = next(n for n in ast.walk(FN["empty_pool_answer"]) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "RAGResponse")
EMPTY_QUERY_ANSWERABLE = next(ast.literal_eval(k.value) for k in rag_call.keywords if k.arg == "answerable")
EMPTY_POOL_ANSWER = ast.literal_eval(next(n.value for n in TREE.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EMPTY_POOL_ANSWER"))
query_call = next(n for n in ast.walk(FN["query"]) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "usage_row")
assert ast.unparse(query_call.args[6]) == "ans.answerable" and EMPTY_QUERY_ANSWERABLE is False
for route in ("query", "stream"):                     # the roster's 403 comes before any row is written
    assert ast.unparse(FN[route].body[0]) == "enforce_membership(user['email'], req.tenant_id)", route
assert stream_verdict(False) == (True, "medium") and stream_verdict(True) == (False, "low")
assert flag(True) == 0 and flag(False) == 1
assert "No response_schema here on purpose" in (KIT / GEN).read_text(encoding="utf-8")
assert 'json={"query": query, "tenant_id": tenant_id, "top_k": 5, "brain": "ui"}' in (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")
assert 'f"{settings.prompt_id}@{settings.prompt_version}"' in MAIN_SRC and '"git_sha": os.environ.get("GIT_SHA", "unknown")' in MAIN_SRC

# alerts.tf: the two policies over the API's traffic, their numbers parsed; no policy anywhere counts a failed request
TF_SRC = (KIT / TF).read_text(encoding="utf-8")


def tf_block(src: str, header: str) -> str:
    """One resource block of a .tf file: from its header to the closing brace at column 0."""
    i = src.index(header)
    return src[i:src.index("\n}\n", i) + 2]


def tf_value(blk: str, key: str, nth: int = 0) -> str:
    return re.findall(rf'\b{key}\s*=\s*"?([\w.\[\]"/]+?)"?\s*$', blk, re.M)[nth]


UM, QM = tf_block(TF_SRC, 'resource "google_logging_metric" "unanswerable" {'), tf_block(TF_SRC, 'resource "google_logging_metric" "queries" {')
UP, LP = (tf_block(TF_SRC, 'resource "google_monitoring_alert_policy" "unanswerable_rate" {'),
          tf_block(TF_SRC, 'resource "google_monitoring_alert_policy" "api_latency" {'))
EVENTS = re.findall(r'jsonPayload\.event="(\w+)"', UM)
assert EVENTS == re.findall(r'jsonPayload\.event="(\w+)"', QM) == ["query", "stream"], EVENTS
assert "jsonPayload.unanswerable_flag=1" in UM and "unanswerable_flag" not in QM
assert UM.count('tenant = "EXTRACT(jsonPayload.tenant)"') == QM.count('tenant = "EXTRACT(jsonPayload.tenant)"') == 1
for blk in (UM, QM):                                  # the service and the event: never a revision, never a caller
    assert 'resource.labels.service_name="documind-api"' in blk and "revision_name" not in blk and "jsonPayload.user" not in blk
UNANS_T = float(tf_value(UP, "threshold_value"))
UNANS_DUR = int(tf_value(UP, "duration").rstrip("s"))
UNANS_ALIGN = {tf_value(UP, "alignment_period", i) for i in (0, 1)}
assert (UNANS_T, UNANS_DUR, UNANS_ALIGN) == (0.20, 1800, {"300s"}), (UNANS_T, UNANS_DUR, UNANS_ALIGN)
assert UP.count('per_series_aligner   = "ALIGN_DELTA"') == 2 and UP.count('cross_series_reducer = "REDUCE_SUM"') == 2
assert UP.count('group_by_fields      = ["metric.label.tenant"]') == 2 and 'display_name = "Unanswerable rate > 20% for a tenant"' in UP
assert 'metric.type=\\"logging.googleapis.com/user/documind/unanswerable\\"' in UP and "documind/queries" in UP
LAT_T = int(tf_value(LP, "threshold_value"))
LAT_DUR = int(tf_value(LP, "duration").rstrip("s"))
assert (LAT_T, LAT_DUR) == (3000, 300) and 'display_name = "API p95 latency > 3s"' in LP
assert '"ALIGN_PERCENTILE_95"' in LP and '"REDUCE_MEAN"' in LP and "group_by_fields" not in LP
assert 'resource.labels.service_name=\\"documind-api\\" AND metric.type=\\"run.googleapis.com/request_latencies\\"' in LP
assert "route" not in LP and "/v1/query" not in LP.split("\n", 1)[1]
assert "# Latency: documind-api's p95 over 3 s for 5 minutes. Every request to the service counts" in TF_SRC
ALL_TF = "".join(p.read_text(encoding="utf-8") for p in (KIT / "terraform").glob("*.tf"))
assert "request_count" not in ALL_TF and "response_code" not in ALL_TF
for m in re.finditer(r'resource "google_logging_metric" "(\w+)" \{.*?filter\s*=\s*<<EOT(.*?)EOT', ALL_TF, re.S):
    if re.search(r'jsonPayload\.event="(query|stream)"', m.group(2)):
        assert "jsonPayload.user" not in m.group(2), m.group(1)   # no metric over the API's answers reads the caller
DESK_SRC = (KIT / DESK_TF).read_text(encoding="utf-8")
DESK_FLAT = re.sub(r"\s+", " ", re.sub(r"\n#\s*", " ", DESK_SRC))
assert "the eval accounts (make" in DESK_FLAT and "would otherwise page on a lane where nobody has asked anything" in DESK_FLAT
assert "local.alert_channel_ids" in UP and 'count        = var.pagerduty_key == "unset-in-dryrun" ? 0 : 1' in TF_SRC
assert "ALERT_EMAILS  ?= $(if $(filter admin@documind.example.com,$(ADMIN_EMAILS)),,$(ADMIN_EMAILS))" in MK

# judge.py: what it asks through, and what it returns
JG_SRC = (KIT / JG).read_text(encoding="utf-8")
assert "from run_eval import GOLDEN, ask, load_golden, normalise" in JG_SRC
JTREE = ast.parse(JG_SRC)
jmain = next(n for n in JTREE.body if isinstance(n, ast.FunctionDef) and n.name == "main")
for r_ in (n for n in ast.walk(jmain) if isinstance(n, ast.Return)):   # every exit is a constant or the self-test: no score decides
    assert isinstance(r_.value, ast.Constant) or ast.unparse(r_.value) == "selftest()", ast.unparse(r_)
assert 'f"{api_url.rstrip(\'/\')}/v1/query"' in (KIT / RE_).read_text(encoding="utf-8")

# usage_rows.py: what make usage groups by
USG_SRC = (KIT / USG).read_text(encoding="utf-8")
GROUPS = re.findall(r"group\(rows, \(([^)]*)\)\)", USG_SRC.split("def main", 1)[1])
GROUP_KEYS = sorted({k.strip().strip('"') for g in GROUPS for k in g.split(",") if k.strip()})
assert GROUP_KEYS == ["brain", "event", "model", "model_backend", "retrieval_backend", "tenant"], GROUP_KEYS

# ------------------------------------------------------------------ the placement matrix
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL"):
    os.environ.pop(k, None)
OUTSIDER = "outsider@not-a-tenant.invalid"
rv.fetch_current_shas = lambda *a, **k: set()           # the stub's chunk ids carry no worker sha to check
rv.fetch_media_names = lambda *a, **k: {"figure": {"annual_report_2026_fig3.png", "inv_2026_0412.png", "payment_of_bonus_act_1965_p30.png"}} if a[1] == "acme" else {}   # the lane before 7.5: the pictures, no video
TMP = Path(tempfile.mkdtemp(prefix="lesson43-"))
(TMP / "evals" / "reports").mkdir(parents=True)
for name in ("golden.jsonl", "required.json", "run_eval.py", "usage_rows.py"):
    shutil.copy2(KIT / "evals" / name, TMP / "evals" / name)
PLANT_ROW, PLANT = "lk-06", "120 days"
PLANT_OLD = TRUTH[PLANT_ROW]["must_contain"][0]
assert PLANT.lower() not in rv.haystack(corpus, TRUTH[PLANT_ROW]["tenant"]) and not rv.check_falsifiable(golden, corpus)
EXTRA = "Staff may also take a paid sabbatical."           # a sentence no document of any tenant holds
assert all(EXTRA.lower() not in rv.haystack(corpus, t) for t in corpus) and "sabbatical" not in " ".join(rv.haystack(corpus, t) for t in corpus)
assert not any(rv.contains(EXTRA, w) for r in A_ROWS for w in r.get("must_not_contain", []))


def body(answer: str, cites: list, answerable: bool) -> dict:
    return {"answer": answer, "citations": cites, "answerable": answerable, "confidence": "high" if answerable else "low",
            "model": "stub", "backend": "vertex", "cache_hit": "none",
            "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1500, "pool": 12}}


def reply(row: dict, outcome: str) -> tuple:
    """The stub's /v1/query reply to one row: the right answer from the kit's own row, or the failure planted."""
    truth = TRUTH[row["id"]]
    t, mc, mnc = truth["tenant"], truth.get("must_contain", []), truth.get("must_not_contain", [])
    cite = {"chunk_id": f"{t}:lesson#0", "source_uri": f"gs://lesson/{t}/doc.md", "quote": mc[0] if mc else "lesson",
            "kind": truth.get("must_cite_kind") or "text"}
    fig = " and ".join(mc)
    if outcome == "err":
        return 500, {}
    if outcome == "empty":
        return 200, body(EMPTY_POOL_ANSWER, [], EMPTY_QUERY_ANSWERABLE)
    if truth["answerable"]:
        table = {"ok": (f"{fig} [1].", [cite], True), "refused": ("The documents do not say.", [], False),
                 "extra": (f"{fig} [1]. {EXTRA}", [cite], True)}
        if mnc:
            table["leak"] = (f"{fig}, and {mnc[0]} [1].", [cite], True)
            table["stale"] = (f"{mnc[0]} [1].", [cite], True)
    else:
        table = {"ok": ("The documents do not say.", [], False)}
    answer, cites, answerable = table[outcome]
    return 200, body(answer, cites, answerable)


def stub_ask(rows: list, outcomes: dict, latency: int, let_in: int):
    """run_eval.ask() for a stub API: each member question answered in the order live() sends them."""
    seq, outsider = [0], [0]

    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            outsider[0] += 1
            if let_in and outsider[0] == 1:
                return 200, body("The documents do not say.", [], False), latency
            return 403, {}, 120
        row = rows[seq[0]]
        seq[0] += 1
        assert row["question"] == question and row["tenant"] == tenant, (row["id"], question)
        status, b = reply(row, outcomes.get(row["id"], "ok"))
        return status, b, latency
    return ask


def run_gate(rows: list, outcomes: dict | None = None, latency: int = 1000, let_in: int = 0, name: str = "m") -> tuple:
    """run_eval.live() against the stub: (exit code, what it printed, the report)."""
    rv.ask = stub_ask(rows, outcomes or {}, latency, let_in)
    report = TMP / "evals" / "reports" / f"{name}.json"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = rv.live(CAND, report=str(report), golden=[dict(r) for r in rows])
    return rc, buf.getvalue(), json.loads(report.read_text(encoding="utf-8"))


def no_model(*a, **k):
    raise AssertionError("the offline half reached for the model")


def run_offline(rows: list) -> tuple:
    """run_eval.offline() over these rows, with every function that could send a request made to fail."""
    keep = (rv.load_golden, rv.ask, rv._ask_once, rv.fetch_current_shas)
    rv.load_golden, rv.ask, rv._ask_once, rv.fetch_current_shas = (lambda: [dict(r) for r in rows]), no_model, no_model, no_model
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = rv.offline()
    finally:
        rv.load_golden, rv.ask, rv._ask_once, rv.fetch_current_shas = keep
    return rc, buf.getvalue()


def moved(rows: list) -> list:
    return [dict(r, must_contain=[PLANT]) if r["id"] == PLANT_ROW else r for r in rows]


DELETED = "iso-03"
assert DELETED in required
REFUSED = [r["id"] for r in A_ROWS if r["id"] not in required][::4]
EMPTY_TENANT = "globex"
LEAK_ROW, STALE_ROW, ERR_ROW = "iso-01", "vr-01", "lk-08"
assert TRUTH[LEAK_ROW]["answerable"] and TRUTH[LEAK_ROW]["must_not_contain"] and TRUTH[STALE_ROW]["shape"] == "version"
assert ERR_ROW not in required
SLOW_MS = 4000
assert SLOW_MS > LAT_T

SCEN = [
    {"key": "moved", "name": "A golden row's figure edited",
     "what": f"{PLANT_ROW}'s must_contain is edited from {PLANT_OLD} to {PLANT}, a figure no {TRUTH[PLANT_ROW]['tenant']} document holds: the hand edit that quiets a red row.",
     "rows": moved(golden), "out": {}},
    {"key": "deleted", "name": "An isolation row deleted",
     "what": f"{DELETED} is deleted from golden.jsonl: the other way a red run is made green.",
     "rows": [r for r in golden if r["id"] != DELETED], "out": {}},
    {"key": "refuses", "name": "The model refuses good questions",
     "what": f"The model declines {len(REFUSED)} of the {len(A_ROWS)} answerable rows, every fourth that required.json does not list.",
     "rows": golden, "out": {i: "refused" for i in REFUSED}},
    {"key": "stream", "name": "The stream refuses, the query answers",
     "what": "On /v1/stream the model declines questions it answers on /v1/query. The stream writes tokens with no response schema, so the two routes can behave differently.",
     "rows": golden, "out": {}},
    {"key": "empty", "name": "A tenant's index is empty",
     "what": f"{EMPTY_TENANT.capitalize()}'s documents never reached the lane's index, so every question for {EMPTY_TENANT} comes back with an empty pool.",
     "rows": golden, "out": {r["id"]: "empty" for r in golden if r["tenant"] == EMPTY_TENANT}},
    {"key": "leak", "name": "Another tenant's figure leaks",
     "what": f"{LEAK_ROW}'s answer for {TRUTH[LEAK_ROW]['tenant']} carries {TRUTH[LEAK_ROW]['must_not_contain'][0]}, another tenant's figure, beside its own.",
     "rows": golden, "out": {LEAK_ROW: "leak"}},
    {"key": "outsider", "name": "The roster lets an outsider in",
     "what": "The roster admits documind-outsider-sa once: one isolation question it asks is answered instead of refused.",
     "rows": golden, "out": {}, "let_in": 1},
    {"key": "stale", "name": "A retired version is quoted",
     "what": f"{STALE_ROW} is answered with {TRUTH[STALE_ROW]['must_not_contain'][0]}, the retired handbook's figure.",
     "rows": golden, "out": {STALE_ROW: "stale"}},
    {"key": "slow", "name": "Every answer takes 4 s",
     "what": f"Every answer takes {SLOW_MS:,} ms end to end; nothing else is wrong.",
     "rows": golden, "out": {}, "latency": SLOW_MS},
    {"key": "err", "name": "One request fails with a 500",
     "what": f"{ERR_ROW}'s request fails with a 500 twice, so the gate's one retry fails too.",
     "rows": golden, "out": {ERR_ROW: "err"}},
    {"key": "extra", "name": "A sentence no document says",
     "what": f"Every answer carries its figure and a valid citation, and one more sentence no document holds: \"{EXTRA}\"",
     "rows": golden, "out": {r["id"]: "extra" for r in A_ROWS}},
]
MODEL_FAILURES = {"refuses", "stream", "empty", "leak", "outsider", "stale", "slow", "err", "extra"}
assert {s["key"] for s in SCEN} - MODEL_FAILURES == {"moved", "deleted"}

# the CI column: offline() over each scenario's rows. A failure in answers leaves the rows as they are.
ci_base_rc, ci_base_out = run_offline(golden)
assert ci_base_rc == 0 and "[PASS] coverage" in ci_base_out
for s in SCEN:
    rc, out = run_offline(s["rows"])
    fails = [line.strip() for line in out.splitlines() if line.startswith("         ")]
    s["ci"] = (rc, fails)
assert SCEN[0]["ci"] == (1, [f"{PLANT_ROW}: must_contain {PLANT!r} is not in {TRUTH[PLANT_ROW]['tenant']}'s corpus - the row can only fail"]), SCEN[0]["ci"]
assert SCEN[1]["ci"] == (1, [f"required.json names {DELETED!r} and golden.jsonl no longer has it"]), SCEN[1]["ci"]
assert all(s["ci"] == (0, []) for s in SCEN[2:])

# the candidate column: live() against the stub, per scenario
for s in SCEN:
    rc, out, rep = run_gate(s["rows"], s["out"], s.get("latency", 1000), s.get("let_in", 0), name=s["key"])
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    s["gate"] = {"rc": rc, "verdict": lines[-1], "failed": rep["failed"], "scores": rep["scores"],
                 "missed": [(r["id"], r["why"] or r["outcome"]) for r in rep["records"] if not r["pass"]],
                 "required_failed": rep["required_failed"], "leaks": rep["leaks"], "stale": rep["stale"],
                 "p95": re.search(r"latency ms  p50 +\d+  p95 +(\d+)", out).group(1) if "latency ms" in out else ""}
G = {s["key"]: s["gate"] for s in SCEN}
assert [G[k]["rc"] for k in ("moved", "deleted", "refuses", "stream", "empty", "leak", "outsider", "stale", "slow", "err", "extra")] \
    == [0, 0, 1, 0, 0, 2, 1, 1, 0, 1, 0], {k: v["rc"] for k, v in G.items()}
assert G["moved"]["missed"] == [(PLANT_ROW, f"answered without {[PLANT]}")] and G["refuses"]["failed"] == ["answerable_rate"]
assert G["empty"]["missed"] == [(r["id"], "refused") for r in golden if r["tenant"] == EMPTY_TENANT and r["answerable"]]
assert G["outsider"]["failed"] == ["isolation_403_rate"] and G["err"]["failed"] == ["request_success_rate"]
assert G["slow"]["p95"] == str(SLOW_MS) and G["stale"]["stale"] and G["leak"]["leaks"]
assert not G["extra"]["missed"] and not G["stream"]["missed"]
pct = lambda x: f"{x:.1%}"                               # noqa: E731
MOVED_MC, MOVED_CR = pct(G["moved"]["scores"]["must_contain_rate"]), pct(G["moved"]["scores"]["correct_rate"])
REF_AR = pct(G["refuses"]["scores"]["answerable_rate"])
EMPTY_AR = pct(G["empty"]["scores"]["answerable_rate"])


def gate_why(k: str) -> str:
    g = G[k]
    text = f"exit {g['rc']}. {g['verdict']}"
    if g["leaks"]:
        text += " (" + "; ".join(g["leaks"]) + ")"
    if g["rc"] == 0 and g["missed"]:
        text += f" Rows that cost a point: {len(g['missed'])} (" + ", ".join(f"{i} {w}" for i, w in g["missed"]) + ")."
    extra = {"moved": f" Its must_contain_rate ({MOVED_MC}) and correct_rate ({MOVED_CR}) still clear their lines: a right answer is now scored as a miss, and nothing blocks.",
             "deleted": f" It asked the rows the file holds; {DELETED} was never asked.",
             "stream": " Every row went to /v1/query, which answered right; the gate never opens a stream.",
             "empty": f" {EMPTY_TENANT.capitalize()} has {ans_tenant[EMPTY_TENANT]} answerable rows of {len(A_ROWS)}, and losing both is inside every threshold's slack (answerable_rate {EMPTY_AR}).",
             "slow": f" It printed p95 {G['slow']['p95']} ms; no threshold reads latency.",
             "extra": " The figure and the citation are what it checks, and both are right."}
    return text + extra.get(k, "")


def ci_why(s: dict) -> str:
    rc, fails = s["ci"]
    if rc:
        return f"exit {rc}. [FAIL] " + "; ".join(fails)
    if s["key"] == "empty":
        return "exit 0. It reads the repository's corpus, which still holds every document; the lane's index is out of its reach."
    return "exit 0. offline() read the rows and the corpus and never called the model: nothing about an answer can reach it."


# the live column: main.py's expressions and alerts.tf's numbers, the booleans written as the row's JSON writes them
U_LINE = f"{UNANS_T:.2f} for {UNANS_DUR // 60} minutes"
q_ref, s_ref = flag(False), flag(stream_verdict(False)[0])
assert (q_ref, s_ref, flag(stream_verdict(True)[0]), flag(EMPTY_QUERY_ANSWERABLE)) == (1, 0, 1, 1)
jb = json.dumps                                          # True -> "true", as the logged row spells it


def live_cell(k: str) -> tuple:
    if k == "refuses":
        return "partly", (f"On /v1/query each refusal writes answerable {jb(False)}, unanswerable_flag {q_ref}: documind/unanswerable counts it, "
                          f"and a tenant above {U_LINE} opens an incident. In the UI the same refusal goes through /v1/stream, whose row "
                          f"says answerable {jb(stream_verdict(False)[0])}, flag {s_ref}: not counted.")
    if k == "stream":
        return "misses", (f"The stream's row says answerable {jb(stream_verdict(False)[0])}, flag {s_ref}, for every pool that is not empty: "
                          "documind/unanswerable never counts these refusals.")
    if k == "empty":
        return "pages", (f"An empty pool writes answerable {jb(EMPTY_QUERY_ANSWERABLE)}, flag {flag(stream_verdict(True)[0])}, on both routes: "
                         f"documind/unanswerable counts every {EMPTY_TENANT} question, and above {U_LINE} the policy opens an incident.")
    if k == "slow":
        return "pages", (f"The latency policy reads Cloud Run's own request latencies: a p95 above {LAT_T} ms for {LAT_DUR // 60} minutes "
                         "opens an incident.")
    if k == "outsider":
        return "misses", "The outsider's answer writes an ordinary row with its email in user, and no metric over the API's rows reads user."
    if k == "err":
        return "misses", "A request that fails before its answer writes no row, and no policy in terraform/ reads Cloud Run's request count or a response code."
    if k in ("moved", "deleted"):
        return "misses", "Nothing on a row changes: the row carries neither the question nor the answer key."
    return "misses", f"The answer is not on the row, and it counts as answered: answerable {jb(True)}, flag {flag(True)}. No policy can see it."


JUDGE = {
    "moved": ("misses", "It reads the lane's answers, never the answer key, and the answer it reads is right."),
    "deleted": ("misses", "It judges the rows the file still holds."),
    "refuses": ("misses", "A refusal claims nothing, so it is grounded (lesson 4.2)."),
    "stream": ("misses", "It collects through run_eval's own ask(), which posts to /v1/query."),
    "empty": ("misses", "The empty pool's refusal is grounded too."),
    "leak": ("advises", "The other tenant's figure is in no passage this answer cites, so it can rate the row ungrounded. Its exit code stays 0."),
    "outsider": ("misses", "It asks as the member only."),
    "stale": ("misses", "When the answer cites the retired passage, that passage says the same, so the answer is grounded in what it cites."),
    "slow": ("misses", "It rates text, not time."),
    "err": ("advises", "It prints the rows that did not come back 200 and judges the rest; its exit code stays 0."),
    "extra": ("advises", "The added sentence is in no cited passage, which is what groundedness rates 0. Its exit code stays 0."),
}


def first(cells: list) -> str:
    ci, cand, live, judge = (c["v"] for c in cells)
    if ci == "blocks":
        return "First caught in CI: the push fails before anything is built or deployed."
    if cand == "blocks":
        return "First caught by the candidate gate: the release stops before any user meets it."
    if live == "pages":
        return "Only live traffic catches it: an incident, after people have met it."
    if live == "partly":
        return "Only live traffic, and only from callers of /v1/query: the UI's rows hide it."
    if judge == "advises":
        return "Nothing blocks it. Only the judge can point at it, and the judge never blocks."
    return "Nothing in the kit catches it."


ROWS = []
for s in SCEN:
    k = s["key"]
    cells = [{"v": "blocks" if s["ci"][0] else "misses", "why": ci_why(s)},
             {"v": "blocks" if G[k]["rc"] else "misses", "why": gate_why(k)},
             dict(zip(("v", "why"), live_cell(k))),
             dict(zip(("v", "why"), JUDGE[k]))]
    ROWS.append({"name": s["name"], "what": s["what"], "cells": cells, "first": first(cells)})
FIRSTS = [r["first"].split(":")[0] for r in ROWS]
COUNT = {
    "CI": sum(f.startswith("First caught in CI") for f in FIRSTS),
    "CAND": sum(f.startswith("First caught by the candidate gate") for f in FIRSTS),
    "LIVE": sum(f.startswith("Only live traffic") for f in FIRSTS),
    "JUDGE": sum(f.startswith("Nothing blocks it") for f in FIRSTS),
    "NONE": sum(f.startswith("Nothing in the kit") for f in FIRSTS),
}
assert COUNT == {"CI": 2, "CAND": 5, "LIVE": 2, "JUDGE": 1, "NONE": 1}, COUNT
COLS = [{"name": "CI: the offline gate, every push", "short": "CI"},
        {"name": "The candidate gate, before release", "short": "candidate"},
        {"name": "Live traffic: rows and alerts", "short": "live"},
        {"name": "The judge, when asked", "short": "judge"}]
MATRIX = {"cols": COLS, "rows": ROWS}

# ------------------------------------------------------------------ the cells
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}       # no gcloud on PATH, no credentials in reach


def run_cell(code: str, cwd: Path, env: dict | None = None, prelude: str = "") -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + code, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=env or ENV)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1200:], r.stdout[-400:])
    return r.stdout


def heredoc(code: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{code}\nPY"


PY_PLANT = f'''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path, old, new = "evals/golden.jsonl", '"must_contain": ["{PLANT_OLD}"]', '"must_contain": ["{PLANT}"]'
lines = open(path, encoding="utf-8").read().split("\\n")
i = next(k for k, line in enumerate(lines) if line.startswith('{{"id": "{PLANT_ROW}",'))
assert old in lines[i], "{PLANT_ROW} is not as the kit ships it: git checkout evals/golden.jsonl, then run this again"
lines[i] = lines[i].replace(old, new)
open(path, "w", encoding="utf-8", newline="\\n").write("\\n".join(lines))
print("{PLANT_ROW} now asks for", json.loads(lines[i])["must_contain"])'''

PY_REQUIRED = r'''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
r = json.load(open("evals/reports/cand43.json", encoding="utf-8"))
required = json.load(open("evals/required.json", encoding="utf-8"))["ids"]
rec = {x["id"]: x for x in r["records"]}
print(r["api_url"])
print(f"  thresholds judged: {len(r['judged'])} of {len(r['thresholds'])}; failed: {', '.join(r['failed']) or 'none'}")
print(f"  the outsider: isolation_403_rate {r['scores']['isolation_403_rate']:.0%}; let in on: {', '.join(x.split(':')[0] for x in r['isolation']) or 'no row'}")
print(f"  required rows: {sum(bool(rec.get(i, {}).get('pass')) for i in required)} of {len(required)} passed")
for i in required:
    x = rec.get(i)
    verdict = "not asked" if x is None else "pass" if x["pass"] else "FAIL: " + (x["why"] or x["outcome"])
    print(f"    {i:7} {x['shape'] if x else '':10} {x['tenant'] if x else '':7} {verdict}")
code = 2 if r["leaks"] else 1 if (r["failed"] or r["stale"] or r["required_failed"]) else 0
print(f"  leaks {len(r['leaks'])}, stale {len(r['stale'])}: the gate's exit was {code}")'''

PY_ROWS = r'''import collections, datetime as dt, json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, REGION = os.environ["PROJECT"], os.environ["REGION"]
EVAL = f"documind-ui-sa@{P}.iam.gserviceaccount.com"     # make eval-live, make judge, make smoke and tok() ask as this


def gcloud_json(*args):
    """Run one gcloud command for the project and return its JSON output, parsed."""
    out = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True, check=True).stdout
    return json.loads(out or "[]")


since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = gcloud_json("logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                   f'AND (jsonPayload.event="query" OR jsonPayload.event="stream") AND timestamp>="{since}"', "--limit", "2000")
traffic = gcloud_json("run", "services", "describe", "documind-api", "--region", REGION)["status"]["traffic"]
serving = {t["revisionName"] for t in traffic if t.get("percent")}
by_rev, by_who, asked = (collections.defaultdict(collections.Counter) for _ in range(3))
others = set()
for e in rows:
    p, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
    mine = p.get("user") == EVAL
    if not mine:
        others.add(p.get("user"))
    for c in (by_rev[rev], by_who[mine]):
        c["rows"] += 1
        c[p["event"]] += 1
        c["eval"] += mine
        c["unans"] += int(p.get("unanswerable_flag") or 0)
    if mine and rev not in serving:
        asked[rev][p["tenant"]] += 1
print(f"{len(rows)} usage rows from documind-api in the last 24 h (events query and stream)")
cols = f"{'rows':>5} {'query':>6} {'stream':>7} {'unans':>6}"
print(f"\n  {'revision':30} {'traffic':8} {cols} {'eval id':>8}")
for rev, c in sorted(by_rev.items()):
    print(f"  {rev:30} {'serving' if rev in serving else 'none':8} {c['rows']:5} {c['query']:6} {c['stream']:7} {c['unans']:6} {c['eval']:8}")
print(f"\n  {'identity':39} {cols}")
for mine, label in ((True, "documind-ui-sa: gates, judge, smoke, tok"), (False, f"everyone else: {len(others)} identities")):
    c = by_who[mine]
    print(f"  {label:39} {c['rows']:5} {c['query']:6} {c['stream']:7} {c['unans']:6}")
gold = collections.Counter(json.loads(l)["tenant"] for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip())
print("\n  golden.jsonl: " + ", ".join(f"{t} {n}" for t, n in sorted(gold.items())))
for rev, t in sorted(asked.items()):
    print(f"  {rev}, no traffic, the eval identity: " + ", ".join(f"{k} {n}" for k, n in sorted(t.items())))'''

PY_STREAM = r'''import datetime as dt, json, os, subprocess, time, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, API, ME = os.environ["PROJECT"], os.environ["API"], os.environ.get("ME", "").lower()
EVAL = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
QUESTION = "What is ACME's sabbatical policy?"            # golden row rf-01: no acme document answers it
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
req = urllib.request.Request(f"{API}/v1/stream", method="POST",
                             data=json.dumps({"query": QUESTION, "tenant_id": "acme", "top_k": 5}).encode(),
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
event, text, done = "", [], {}
with urllib.request.urlopen(req, timeout=120) as resp:
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: ") and event == "token":
            text.append(json.loads(line[6:])["t"])
        elif line.startswith("data: ") and event == "done":
            done = json.loads(line[6:])
print("the stream:", " ".join("".join(text).split())[:240])
print(f"  pool {done['stages']['pool']}, backend {done['backend']}, model {done['model']}, tokens out {done.get('tokens_out')}")


def stream_rows(start):
    """The stream usage rows documind-api logged since this time, newest first, from Cloud Logging."""
    flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
           f'AND jsonPayload.event="stream" AND timestamp>="{start}"')
    out = subprocess.run(["gcloud", "logging", "read", flt, "--project", P, "--limit", "20", "--format=json"],
                         capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]


mine = []
for _ in range(18):                        # a row reaches Cloud Logging a few seconds after the stream ends
    mine = [r for r in stream_rows(since) if r.get("user") == EVAL]
    if mine:
        break
    time.sleep(5)
if not mine:
    raise SystemExit("no stream row from the eval identity after 90 s: run the cell again")
row = mine[0]
print(f"its usage row: answerable {row['answerable']}, unanswerable_flag {row['unanswerable_flag']}, "
      f"confidence {row['confidence']}, pool {row['pool']}")
print(f"  {len(row)} fields; holding the question or the answer: {[k for k in row if k in ('query', 'question', 'answer', 'text')] or 'none'}")
recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
for r in stream_rows(recent):
    if ME and r.get("user") == ME:
        print(f"your stream in the UI ({r['tenant']}): answerable {r['answerable']}, unanswerable_flag {r['unanswerable_flag']}, pool {r['pool']}")'''

PY_ALERT = r'''import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P = os.environ["PROJECT"]
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api_json(url):
    """GET one Google API URL with the operator's token and return the parsed JSON."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    return json.load(urllib.request.urlopen(req, timeout=60))


for name in ("documind/unanswerable", "documind/queries"):
    m = api_json(f"https://logging.googleapis.com/v2/projects/{P}/metrics/{urllib.parse.quote(name, safe='')}")
    print(f"{name}: {' '.join(m['filter'].split())}")
for p in api_json(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies?pageSize=200").get("alertPolicies", []):
    if p["displayName"] in ("Unanswerable rate > 20% for a tenant", "API p95 latency > 3s"):
        c = p["conditions"][0]["conditionThreshold"]
        print(f"policy {p['displayName']!r}: above {c['thresholdValue']} for {c['duration']}, "
              f"enabled {p.get('enabled', True)}, notification channels {len(p.get('notificationChannels', []))}")
now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")


def windows(metric):
    """One log metric's count per tenant in five-minute windows over the last six hours, aligned as the policy aligns it."""
    q = urllib.parse.urlencode({
        "filter": f'metric.type="logging.googleapis.com/user/{metric}" AND resource.type="cloud_run_revision"',
        "interval.startTime": iso(now - dt.timedelta(hours=6)), "interval.endTime": iso(now),
        "aggregation.alignmentPeriod": "300s", "aggregation.perSeriesAligner": "ALIGN_DELTA",
        "aggregation.crossSeriesReducer": "REDUCE_SUM", "aggregation.groupByFields": "metric.label.tenant"})
    out = {}
    for s in api_json(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{q}").get("timeSeries", []):
        for pt in s.get("points", []):
            out[(pt["interval"]["endTime"][11:16], s["metric"]["labels"].get("tenant", "?"))] = int(pt["value"].get("int64Value", 0))
    return out


num, den = windows("documind/unanswerable"), windows("documind/queries")
print("\nfive-minute windows with questions, the last six hours (UTC), per tenant:")
for key in sorted(den):
    if den[key]:
        share = num.get(key, 0) / den[key]
        print(f"  {key[0]}  {key[1]:7} {num.get(key, 0):3} of {den[key]:3} unanswerable = {share:.2f}" + ("  above 0.20" if share > 0.20 else ""))'''
# the cell reads the windows exactly as the policy aligns them, and draws the policy's own line
for want in ('"aggregation.alignmentPeriod": "300s"', '"aggregation.perSeriesAligner": "ALIGN_DELTA"',
             '"aggregation.crossSeriesReducer": "REDUCE_SUM"', '"aggregation.groupByFields": "metric.label.tenant"'):
    assert want in PY_ALERT, want
assert f"{UNANS_T:.2f}" in PY_ALERT and "Unanswerable rate > 20% for a tenant" in UP and '"API p95 latency > 3s"' in LP

CELLS = {
    "pipeline": heredoc(PY_PIPELINE),
    "plant": heredoc(PY_PLANT) + "\ngit diff --stat evals/golden.jsonl\npython evals/run_eval.py; echo \"exit $?\"",
    "restore": "git checkout evals/golden.jsonl\npython evals/run_eval.py | tail -1; git status --short evals/golden.jsonl",
    "candidate": ('make candidate PROJECT="$PROJECT"          # no override: the Makefile\'s settings, the image unchanged\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "version": ('for u in "$API" "$CAND"; do echo "$u/version"\n'
                '  curl -s "$u/version" -H "Authorization: Bearer $(tok "$API")" \\\n'
                "    | python -c 'import json, sys; v = json.load(sys.stdin); print(\"  git_sha\", v[\"git_sha\"], \"| generator\", v[\"generator_model\"], \"| prompt\", v[\"prompt\"])'\n"
                "done"),
    "gate": 'make eval-live PROJECT="$PROJECT" API="$CAND" REPORT=evals/reports/cand43.json',
    "required": heredoc(PY_REQUIRED),
    "untag": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
              'rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag (lesson 4.4)\n'
              'curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"'),
    "rows": heredoc(PY_ROWS),
    "usage": 'make usage PROJECT="$PROJECT" HOURS=24',
    "stream": heredoc(PY_STREAM, prefix='TOKEN="$(tok "$API")" '),
    "alert": heredoc(PY_ALERT),
}
CELL_LABELS = {
    "pipeline": "run in the operator shell, in the kit (reads the two workflow files; no network)",
    "plant": "run in the operator shell, in the kit (edits one line of your clone on purpose, then runs what CI runs)",
    "restore": "run in the operator shell, in the kit (the kit's file back)",
    "candidate": "run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users)",
    "version": "run in the operator shell (two GETs: the live revision and the candidate)",
    "gate": "run in the operator shell, in the kit (every row as the member, every isolation row as the outsider: about ten minutes)",
    "required": "run in the operator shell, in the kit (reads the report; changes nothing)",
    "untag": "run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched)",
    "rows": "run in the operator shell, in the kit (one Cloud Logging read and one describe; changes nothing)",
    "usage": "run in the operator shell, in the kit (the same rows, as make usage groups them)",
    "stream": "run in the operator shell, in the kit (one streamed answer, then its row from Cloud Logging)",
    "alert": "run in the operator shell (two Cloud Logging reads and three Cloud Monitoring reads; changes nothing)",
}

OUT: dict = {}
# the pipeline, as the cell prints it over the kit's two files
OUT["pipeline"] = ("(the cell, run on the kit's own workflow files when this page was built)", run_cell(PY_PIPELINE, KIT))
assert "release-candidate   needs eval-gate" in OUT["pipeline"][1] and "signs in to Google: no" in OUT["pipeline"][1]

# the Change-it, on a copy of the kit's evals in a throwaway git repository: the cell's edit, git, then the gate
REPO = TMP / "repo"
for rel in ("evals/golden.jsonl", "evals/required.json", "evals/run_eval.py", "evals/manifest.json"):
    (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(KIT / rel, REPO / rel)
for sub in ("corpus", "demo"):                  # the text files load_corpus() and load_demo() read; the PDFs stay behind
    for p in (KIT / "evals" / sub).rglob("*"):
        if p.is_file() and p.suffix in (".md", ".txt"):
            dest = REPO / p.relative_to(KIT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "user.name=lesson", "-c", "user.email=lesson@localhost"]


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*GIT, *args], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")


assert git("init", "-q").returncode == 0 and git("add", "-A").returncode == 0 and git("commit", "-q", "-m", "kit").returncode == 0
plant_out = run_cell(PY_PLANT, REPO)
stat = git("diff", "--stat", "evals/golden.jsonl")
gate = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", env=ENV)
assert gate.returncode == 1 and f"{PLANT_ROW}: must_contain {PLANT!r} is not in" in gate.stdout, gate.stdout[-600:]
OUT["plant"] = ("(the cell, run on a copy of the kit's evals when this page was built)",
                plant_out + stat.stdout + gate.stdout + f"exit {gate.returncode}\n")
co = git("checkout", "evals/golden.jsonl")
again = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", env=ENV)
status = git("status", "--short", "evals/golden.jsonl")
assert co.returncode == 0 and again.returncode == 0 and status.stdout == "" and (REPO / "evals/golden.jsonl").read_bytes() == (KIT / "evals/golden.jsonl").read_bytes()
OUT["restore"] = ("(the same copy, restored; git status prints nothing for a clean file)",
                  (co.stderr.strip() + "\n" if co.stderr.strip() else "") + again.stdout.rstrip("\n").splitlines()[-1] + "\n")
assert again.stdout.rstrip().endswith("The golden set is sound. It can go red, and it still contains the rows that would.")

# make candidate with no override: make's own echo of the recipe, with the Makefile's defaults
ENV_VALUE = "^|^" + "|".join(f"{k}={DEFAULTS[v]}" for k, v in PAIRS)
OUT["candidate"] = ("shape (make echoes the gcloud line; gcloud's own progress lines are left out; the two >> lines are make's)",
                    f"gcloud run services update documind-api --region asia-south1 --project {PROJ} --no-traffic --tag candidate \\\n"
                    f"  --update-env-vars \"{ENV_VALUE}\" --remove-env-vars GENERATOR_LOCATION\n...\n"
                    f">> candidate revision: documind-api-000NN-yyy {ECHO_REV}\n"
                    f">> candidate: {CAND} {ECHO_CAND}\nCAND={CAND}\n")
OUT["version"] = ("shape (COMMIT is the commit your lane was built from: both lines name the same one)",
                  "".join(f"{u}/version\n  git_sha COMMIT | generator {DEFAULTS['GENERATOR_MODEL']} | prompt {PROMPT}\n" for u in (API, CAND)))
OUT["untag"] = ("shape (gcloud's traffic table first)", "...\nthe candidate URL now: HTTP 404\n")

# the report cell, over a stub's report in which the candidate answered every row right
rc_ok, _, _ = run_gate(golden, name="cand43")
assert rc_ok == 0
OUT["required"] = ("(this cell over a stub's report in which the candidate answered every row right; your report gives your rows)",
                   run_cell(PY_REQUIRED, TMP))
assert f"required rows: {len(required)} of {len(required)} passed" in OUT["required"][1] and "the gate's exit was 0" in OUT["required"][1]

# make usage: usage_rows.py's own tables over one stand-in row, every row of each table left to your lane
USAGE_FAKE = ("import json, sys, types\n"
              "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
              "ROW = {'event': 'query', 'tenant': 'acme', 'model': 'gemini-3.6-flash', 'model_backend': 'vertex', 'brain': 'ui',\n"
              "       'retrieval_backend': 'vector', 'tokens_in': 2000, 'tokens_out': 300, 'cost_usd': 0.00525, 'latency_ms': 3000,\n"
              "       'unanswerable_flag': 0, 'retrieve_ms': 400, 'rerank_ms': 200, 'generate_ms': 2300, 'pool': 20}\n"
              "def run(cmd, **kw):\n"
              "    assert cmd[1:3] == ['logging', 'read'], cmd\n"
              "    return R(json.dumps([{'jsonPayload': ROW}]))\n"
              "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
usage_raw = run_cell("import sys; sys.argv = ['usage_rows.py', '--project', '" + PROJ + "', '--hours', '24']\n"
                     "sys.path.insert(0, 'evals')\nimport usage_rows\nusage_rows.main()\n", TMP, QUIET, USAGE_FAKE)
blocks_ = usage_raw.strip("\n").split("\n\n")
assert blocks_[0] == "1 answers from documind-api in the last 24 h; USD_INR=85", blocks_[0]
shape = ["NN answers from documind-api in the last 24 h; USD_INR=85"]
for blk in blocks_[1:]:
    ls = blk.split("\n")
    assert len(ls) == 4 and set(ls[2]) == {"-"}, ls
    shape.append("\n".join(ls[:3] + ["..."]))
assert not any(w in "\n".join(shape) for w in ("revision", "user"))      # no table of make usage names a revision or a caller
OUT["usage"] = ("shape (usage_rows.py's own section titles and columns; every row of every table is your lane's)",
                USAGE_LINE.replace("$(PY)", "python").replace("$(PROJECT)", PROJ).replace("$$", "$") + "\n" + "\n\n".join(shape) + "\n")

# the recorded outputs: the author's lane
LANE = "(the author's lane: your revision names, times and counts are yours)"
OUT["gate"] = ("(the author's lane: the full gate on a candidate with no change; your rates, rows and times are yours)",
               pb.recorded(LESSON, "candidate_gate.txt"))
OUT["rows"] = (LANE, pb.recorded(LESSON, "rows_by_revision.txt"))
OUT["stream"] = (LANE, pb.recorded(LESSON, "stream_refusal.txt"))
OUT["alert"] = ("(the author's lane: your windows are your lane's hours)", pb.recorded(LESSON, "alert_series.txt"))

# the three lane cells, run here against a stand-in gcloud and API: their code is tested before a lane runs them
EVAL_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
STAND_IN = r'''import io, json, sys, types, urllib.request
class R:
    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0
class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
ENTRIES, TRAFFIC, URLS = json.loads(%r), json.loads(%r), json.loads(%r)
def run(cmd, **kw):
    if cmd[1:3] == ["logging", "read"]:
        return R(json.dumps(ENTRIES))
    if cmd[1:4] == ["run", "services", "describe"]:
        return R(json.dumps(TRAFFIC))
    if cmd[1:3] == ["auth", "print-access-token"]:
        return R("stand-in-token\n")
    raise SystemExit("unexpected command: " + " ".join(cmd))
fake = types.ModuleType("subprocess"); fake.run = run; sys.modules["subprocess"] = fake
def urlopen(req, timeout=None):
    url = req.full_url
    for key, value in URLS.items():
        if key in url:
            return Resp(value.encode() if isinstance(value, str) else json.dumps(value).encode())
    raise SystemExit("unexpected URL: " + url)
urllib.request.urlopen = urlopen
'''


def stand_in(entries: list, traffic: dict, urls: dict) -> str:
    return STAND_IN % (json.dumps(entries), json.dumps(traffic), json.dumps(urls))


def entry(rev: str, **p) -> dict:
    return {"resource": {"labels": {"revision_name": rev}}, "jsonPayload": p}


lane_env = {**QUIET, "PROJECT": PROJ, "REGION": "asia-south1", "API": API, "ME": "you@your-company.com", "TOKEN": "stand-in"}
gate_rows = [entry("rev-cand", event="query", user=EVAL_SA, tenant=r["tenant"], unanswerable_flag=flag(r["answerable"])) for r in golden]
lane_rows = [entry("rev-live", event="stream", user="you@your-company.com", tenant="acme", unanswerable_flag=0),
             entry("rev-live", event="stream", user=EVAL_SA, tenant="acme", unanswerable_flag=0)]
out_rows = run_cell(PY_ROWS, TMP, lane_env, stand_in(gate_rows + lane_rows, {"status": {"traffic": [{"revisionName": "rev-live", "percent": 100}]}}, {}))
want = ", ".join(f"{t} {per_tenant[t]}" for t in sorted(TENANTS))
assert f"golden.jsonl: {want}" in out_rows and f"rev-cand, no traffic, the eval identity: {want}" in out_rows, out_rows
assert f"{len(golden) + 2} usage rows" in out_rows and "everyone else: 1 identities" in out_rows, out_rows
stream_row = {"event": "stream", "tenant": "acme", "user": EVAL_SA, **{k: 0 for k in ROW_KEYS if k not in ("event", "tenant", "user")},
              "answerable": stream_verdict(False)[0], "unanswerable_flag": s_ref, "confidence": stream_verdict(False)[1], "pool": 20}
assert len(stream_row) == N_ROW_FIELDS
sse = ("event: citation\ndata: {\"n\": 1}\n\nevent: token\ndata: {\"t\": \"The documents do not say.\"}\n\n"
       "event: done\ndata: " + json.dumps({"tokens_out": 40, "stages": {"pool": 20}, "backend": "vertex", "model": "gemini-3.6-flash"}) + "\n\n")
out_stream = run_cell(PY_STREAM, TMP, lane_env, stand_in([{"jsonPayload": stream_row}, {"jsonPayload": dict(stream_row, user="you@your-company.com")}],
                                                          {}, {"/v1/stream": sse}))
assert f"its usage row: answerable True, unanswerable_flag 0, confidence medium, pool 20" in out_stream, out_stream
assert f"{N_ROW_FIELDS} fields; holding the question or the answer: none" in out_stream and "your stream in the UI (acme)" in out_stream
series = lambda m: {"timeSeries": [{"metric": {"labels": {"tenant": t}}, "points": [{"interval": {"endTime": "2026-10-08T10:05:00Z"},
                    "value": {"int64Value": str(n)}}]} for t, n in m.items()]}      # noqa: E731
urls = {"metrics/documind%2Funanswerable": {"filter": "x"}, "metrics/documind%2Fqueries": {"filter": "y"},
        "alertPolicies": {"alertPolicies": [{"displayName": "Unanswerable rate > 20% for a tenant", "notificationChannels": [],
                                             "conditions": [{"conditionThreshold": {"thresholdValue": UNANS_T, "duration": f"{UNANS_DUR}s"}}]}]},
        "logging.googleapis.com%2Fuser%2Fdocumind%2Funanswerable": series(unans_tenant),
        "logging.googleapis.com%2Fuser%2Fdocumind%2Fqueries": series(per_tenant)}
out_alert = run_cell(PY_ALERT, TMP, lane_env, stand_in([], {}, urls))
assert (f"{'globex':7} {unans_tenant['globex']:3} of {per_tenant['globex']:3} unanswerable = "
        f"{unans_tenant['globex'] / per_tenant['globex']:.2f}  above 0.20") in out_alert, out_alert
assert f"above {UNANS_T} for {UNANS_DUR}s, enabled True, notification channels 0" in out_alert, out_alert
shutil.rmtree(TMP, ignore_errors=True)


# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the matrix's script
UI_JS = r"""var root = document.getElementById('pm'); if (!root) return;
  var list = document.getElementById('pm-rows'), detail = document.getElementById('pm-detail'), buttons = [];
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function show(i){
    var r = M.rows[i];
    buttons.forEach(function(b, j){ b.setAttribute('aria-pressed', j === i ? 'true' : 'false'); });
    detail.textContent = '';
    detail.appendChild(el('h5', '', r.name));
    detail.appendChild(el('p', '', r.what));
    var cards = el('div', 'pm-cards');
    M.cols.forEach(function(c, j){
      var card = el('div', 'pm-card');
      card.appendChild(el('b', '', c.name));
      card.appendChild(el('span', 'pm-v v-' + r.cells[j].v, r.cells[j].v));
      card.appendChild(el('p', '', r.cells[j].why));
      cards.appendChild(card); });
    detail.appendChild(cards);
    detail.appendChild(el('p', 'pm-first', r.first)); }
  M.rows.forEach(function(r, i){
    var b = el('button', 'pm-row'); b.type = 'button'; b.setAttribute('aria-pressed', 'false');
    b.setAttribute('aria-label', r.name + ': ' + M.cols.map(function(c, j){ return c.short + ' ' + r.cells[j].v; }).join(', '));
    b.appendChild(el('span', 'pm-name', r.name));
    r.cells.forEach(function(c){ b.appendChild(el('span', 'pm-v v-' + c.v, c.v)); });
    b.addEventListener('click', function(){ show(i); });
    list.appendChild(b); buttons.push(b); });
  show(0);"""
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar M = " + json.dumps(MATRIX, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
      + ";\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert "<div" not in JS and "<tr" not in JS and "\u2014" not in JS and "\u2013" not in JS

# ------------------------------------------------------------------ numbers for the prose
PRICES = {}
exec(compile((KIT / "shared" / "prices.py").read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
TYPICAL = (2000, 300)                    # the course's typical answer (lessons 4.4 and 11.6): 2,000 tokens in, 300 out
RATE_IN, RATE_OUT = PRICES["PRICES"][DEFAULTS["GENERATOR_MODEL"]]   # the table itself, whatever DOCUMIND_PROFILE says
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * PRICES["USD_INR"]
assert PRICES["USD_INR"] == 85 and (RATE_IN, RATE_OUT) == (1.50, 7.50)
RAG_DIST = re.search(r'rag_distance_threshold: float = Field\(([\d.]+), alias="RAG_DISTANCE_THRESHOLD"\)', cfg).group(1)
assert "RAG_DISTANCE_THRESHOLD" not in DEPLOY_12_2 and RAG_DIST == "0.5"
STATS = {
    "N_ROWS": str(len(golden)), "N_ANS": str(len(A_ROWS)), "N_UNANS": str(len(golden) - len(A_ROWS)),
    "N_THRESHOLDS": str(len(rv.THRESHOLDS)), "N_REQ": str(len(required)), "N_REQ_ISO": str(len(REQ_KIND["isolation"])),
    "N_REQ_MEDIA": str(len(REQ_KIND["media"])), "N_REQ_VERSION": str(len(REQ_KIND["version"])),
    "N_ISO": str(sum(r["shape"] == "isolation" for r in golden)), "N_DOCS": str(N_DOCS),
    "N_SCEN": str(len(SCEN)), "N_FIRST_CI": str(COUNT["CI"]), "N_FIRST_CAND": str(COUNT["CAND"]), "N_FIRST_LIVE": str(COUNT["LIVE"]),
    "N_FIRST_JUDGE": str(COUNT["JUDGE"]), "N_FIRST_NONE": str(COUNT["NONE"]),
    "UNANS_T": f"{UNANS_T:.2f}", "UNANS_MIN": str(UNANS_DUR // 60), "UNANS_S": str(UNANS_DUR), "LAT_MS": str(LAT_T), "LAT_S": str(LAT_T // 1000),
    "LAT_MIN": str(LAT_DUR // 60), "LAT_DUR_S": str(LAT_DUR),
    "PLANT_ROW": PLANT_ROW, "PLANT": PLANT, "PLANT_OLD": PLANT_OLD, "MOVED_MC": MOVED_MC, "MOVED_CR": MOVED_CR,
    "N_SETTINGS": str(len(PAIRS)), "N_ROW_FIELDS": str(N_ROW_FIELDS),
    "N_ACME": str(per_tenant["acme"]), "N_ZETA": str(per_tenant["zeta"]), "N_GLOBEX": str(per_tenant["globex"]),
    "U_ACME": str(unans_tenant["acme"]), "U_ZETA": str(unans_tenant["zeta"]), "U_GLOBEX": str(unans_tenant["globex"]),
    "R_ACME": f"{unans_tenant['acme'] / per_tenant['acme']:.2f}", "R_ZETA": f"{unans_tenant['zeta'] / per_tenant['zeta']:.2f}",
    "R_GLOBEX": f"{unans_tenant['globex'] / per_tenant['globex']:.2f}",
    "A_GLOBEX": str(ans_tenant["globex"]), "EMPTY_AR": EMPTY_AR, "N_REFUSED": str(len(REFUSED)), "REF_AR": REF_AR,
    "RS_ANSWER": f"{RS_ANSWER:.2f}", "RS_GATE": f"{RS_ANSWER * len(golden):.0f}",
    "PROMPT": PROMPT, "RAG_DIST": RAG_DIST,
}
assert unans_tenant["globex"] / per_tenant["globex"] > UNANS_T and unans_tenant["zeta"] / per_tenant["zeta"] > UNANS_T
assert unans_tenant["acme"] / per_tenant["acme"] < UNANS_T


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body_html = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body_html, JS)
print(f"kit: {len(golden)} rows, {len(rv.THRESHOLDS)} thresholds, {len(required)} required | matrix: {len(SCEN)} failures through offline(), "
      f"live() on a stub, main.py's row rules and alerts.tf ({UNANS_T:.2f} for {UNANS_DUR}s; {LAT_T} ms for {LAT_DUR}s) | "
      f"first caught: CI {COUNT['CI']}, candidate {COUNT['CAND']}, live {COUNT['LIVE']}, judge only {COUNT['JUDGE']}, none {COUNT['NONE']} | "
      f"Change-it on a throwaway repo: exit {gate.returncode}, then 0 | three lane cells passed against a stand-in")
