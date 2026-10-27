"""Build lesson 11.8 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Complete the independent capstone and operational handover. The kit's commands/capstone_check.py says PASS or FAIL
for each of the capstone rubric's eight components and never a score (make capstone-check), and writes HANDOVER.md
from the checkout and, with PROJECT, from the lane (make handover). Both only read: the fork's files and records, and
on the lane an allow-list of gcloud reads, two ID tokens minted as make eval-live mints them, and GETs on documind-api.

Computed here, offline, from the kit and the rubric:
  - the rubric (Level 0), parsed from plan/capstone-rubric.md when the page is built: the eight components, each with
    what make capstone-check reads for it, the five dimensions with their 0-3 rows, and the pass rule, 9 of 15 with no
    dimension at 0, which the self-score applies (its rule is checked in Node against the same rule in Python); its
    notes (step 9), every lesson number it names checked against the manifest, and every file it cites found;
  - capstone_check.py --selftest; make capstone-check on a copy of the kit as it ships (one PASS, seven FAIL), on the
    canned fork commands/tests/capstone_fork/ laid over a copy of the kit (eight PASS), on the same with the four
    templates of capstone/templates/ over its four documents, as they ship (components 5 to 8 FAIL), and on the
    Change-it's copy with one FAILURE-MODES command deleted (component 7 FAILs alone); make handover on the canned fork,
    HANDOVER.md whole; and the records cell, the kit's own rules reading the canned fork's records. No gcloud on PATH,
    no credential.
Recorded from the author's lane with pb.recorded() (RUN_LIST.md says how): the lane's reads with the two tokens, make
capstone-check on the author's reference fork offline and with PROJECT, and make handover with PROJECT.

    python pagekit/build.py 11.8
"""
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, PLAN, block, filler, finish, module_key, setup_section, window  # noqa: E402

LESSON = "11.8"
title = ("<title>Lesson 11.8 Complete the independent capstone and operational handover - eight components checked "
         "PASS or FAIL in your fork, five dimensions self-scored against the rubric, and HANDOVER.md written from your "
         "lane | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
FORK_PATH, KIT_PATH = "/tmp/sahyadri", "/home/you/deploy_module_rag"     # what the cells print on a learner's machine

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the rubric: eight components to tick, five dimensions to score, one verdict */
.cs-sub{font-size:var(--small-size);color:var(--navy);margin:12px 0 6px;font-weight:600;}
.cs-comp{display:grid;grid-template-columns:auto minmax(0,1fr);gap:2px 10px;align-items:start;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;margin:0 0 6px;min-height:44px;cursor:pointer;-webkit-tap-highlight-color:transparent;}
.cs-comp input{width:22px;height:22px;margin:3px 0 0;accent-color:var(--teal);grid-row:1/4;}
.cs-comp[data-fail="1"]{border:2px solid #dc2626;background:#fef2f2;}
.cs-name{font-weight:600;color:var(--navy);font-size:13.5px;line-height:1.4;overflow-wrap:anywhere;}
.cs-how{font-size:12.5px;line-height:1.5;color:var(--slate);overflow-wrap:anywhere;}
.cs-kit{font-family:var(--mono);font-size:11.5px;line-height:1.5;color:var(--teal-dark);overflow-wrap:anywhere;}
.cs-dim{display:grid;grid-template-columns:minmax(0,190px) minmax(0,1fr);gap:4px 10px;align-items:center;margin:0 0 6px;}
.cs-dname{font-size:13.5px;font-weight:600;color:var(--navy);line-height:1.4;}
.cs-dim select{font:inherit;font-size:16px;min-height:44px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);max-width:100%;min-width:0;width:100%;}
#cs-dims[aria-disabled="true"]{opacity:.45;}
.cs-verdict{border-left:4px solid var(--teal);background:var(--teal-light);border-radius:10px;padding:8px 12px;margin:10px 0 6px;font-size:var(--small-size);line-height:1.55;color:var(--navy);}
.cs-verdict[data-ok="0"]{border-left-color:#dc2626;background:#fef2f2;}
.cs-verdict b{font-family:var(--mono);}
.cs-verdict p{margin:0 0 4px;font-size:var(--small-size);}
@media (hover:hover) and (pointer:fine){.cs-comp:hover{border-color:var(--teal);}}
.cs-comp:active{background:var(--teal-light);}
@media (max-width: 640px){.cs-dim{grid-template-columns:minmax(0,1fr);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme "
         "wherever it is."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head: make capstone-check mints the same two tokens tok and otok mint, and every "
         "gcloud line it runs is a describe or a list, as you.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ the kit's check, loaded as make runs it
CC_PATH = "commands/capstone_check.py"
spec = importlib.util.spec_from_file_location("_capstone118", KIT / CC_PATH)
CC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CC)
REL = CC.release
assert list(CC.COMPONENTS) == list(range(1, 9))
assert (CC.GOLDEN_MIN, CC.ISOLATION_MIN, CC.PAGES_MIN) == (30, 5, 30)
assert (CC.REJECTED_MIN, CC.ENTRIES_MIN, CC.USD_INR, CC.REASON_WORDS, CC.AMOUNTS_MIN) == (3, 4, 85, 6, 3)
assert CC.KIT_TENANTS == ("acme", "globex", "zeta") and CC.UI_SCRIPT == "commands/lesson-12.4.sh"
assert CC.IAP_FLAGS == ("--iap", "--no-allow-unauthenticated")
assert (CC.SMOKE_LOG, CC.REPORTS, CC.REGISTRY) == ("evals/reports/smoke-deployed.jsonl", "evals/reports", "ops/gotchas.json")
assert CC.LANES == (("chat", "smoke-chat"), ("media", "smoke-media"), ("SLM", "smoke-slm")) and CC.GRAPH_ON == ("on", "auto")
assert CC.GOTCHA_TARGETS == ("gotcha-drill", "gotcha-detect", "gotchas") and (CC.INCOMPLETE, CC.STOPPED) == (1, 2)
assert CC.ONE_PAGE == (".png", ".jpg", ".jpeg", ".mp4", ".mp3")
N_READS = len(CC.READS)
assert N_READS == 11 and all(r[0] == "gcloud" for r in CC.READS)
assert CC.is_read(["gcloud", "run", "services", "describe"]) and CC.is_read(["gcloud", "auth", "print-access-token"])
for refused in (["gcloud", "run", "services", "update-traffic"], ["gcloud", "run", "deploy"], ["gcloud", "run", "services", "update"],
                ["terraform", "apply"], ["gcloud", "scheduler", "jobs", "run"]):
    assert not CC.is_read(refused), refused
READ_NAMES = [" ".join(r[1:]) for r in CC.READS]
assert (REL.MEMBER_SA, REL.OUTSIDER_SA, REL.SERVICE) == ("documind-ui-sa", "documind-outsider-sa", "documind-api")
assert REL.MAX_AGE_HOURS == 24.0 and REL.SMOKE_FORMAT == "documind-smoke/1" and REL.GATE_FORMAT == "documind-gate/1"
assert CC.text_pages("a\fb\fc") == 3 and CC.text_pages("") == 1
assert CC.cron_time("0 23 * * *", "Asia/Kolkata") == "23:00 IST"
assert CC.is_command("make gotcha-drill ID=pinned-traffic") and not CC.is_command("gcloud run deploy x")
assert "does not reproduce" in CC.unresolved("make gotcha-detect ID=x", {"gotcha-detect"}, lambda p: False, {})
SRC = (KIT / CC_PATH).read_text(encoding="utf-8")
N_TESTS = len(re.findall(r"^    def test_", (KIT / "commands/tests/test_capstone_check.py").read_text(encoding="utf-8"), re.M))
assert N_TESTS == 31, N_TESTS
HANDOVER_SECTIONS = re.findall(r'out = \["## (.+?)", ""\]', SRC)
assert HANDOVER_SECTIONS == ["Alert policies", "The night job", "Floors", "Revisions", "CI trust", "Budget", "State bucket"], HANDOVER_SECTIONS
N_SECTIONS = len(HANDOVER_SECTIONS)
assert 'tail = ["## Not read", ""]' in SRC

# ------------------------------------------------------------------ the rubric (plan/capstone-rubric.md), parsed when the page is built
RUBRIC = (PLAN / "capstone-rubric.md").read_text(encoding="utf-8")
assert "renumbered 2026-10-13 to the" in RUBRIC and "course-bibles" not in RUBRIC          # the kit PR's renumbering landed
assert "`make capstone-check FORK=<the fork>`" in RUBRIC                                      # the rubric sends assessors here
ROWS = re.findall(r"^\| (\d) \| (.+?) \| (.+?) \| (.+?) \|$", RUBRIC, re.M)                 # number, component, where from, the check
assert [int(r[0]) for r in ROWS] == list(range(1, 9)), ROWS
N_COMPONENTS = len(ROWS)
LESSON_IDS = {lid for m in MANIFEST["modules"].values() for lid in m["lessons"]}
FROM_LESSONS = sorted({lid for _, _, where, _ in ROWS for lid in re.findall(r"\b\d{1,2}\.\d{1,2}\b", where)},
                      key=lambda x: tuple(int(p) for p in x.split(".")))
assert all(lid in LESSON_IDS for lid in FROM_LESSONS), FROM_LESSONS            # every lesson the rubric names is in the manifest
assert "11.7" in ROWS[6][2] and "11.3" in ROWS[7][2] and ROWS[0][2] == "0.3, 3.8, 4.7" and ROWS[2][2] == "4.1, 4.2, 4.7"
assert [int(n) for n, _, where, _ in ROWS if "11.8" in where] == [2, 4, 5] and ROWS[1][2] == "1.5, 3.8, 11.8"   # this lesson's three shares
TESTS = (KIT / "commands/tests/test_capstone_check.py").read_text(encoding="utf-8")
for name in ("test_change_it_one_failure_modes_command_deleted_fails_that_component_only", "test_each_component_broken_alone_fails_alone",
             "test_a_write_is_refused_before_it_runs", "test_the_kit_as_it_ships_is_no_capstone", "test_the_page_trees_of_the_kits_pdfs"):
    assert f"def {name}(self):" in TESTS, name
DIMS = re.findall(r"^### (\d)\. (.+?) \(0–3\)$", RUBRIC, re.M)
assert [d for _, d in DIMS] == ["Architecture", "Failure modes", "Cost at 10×", "Evals", "What you would do next month"], DIMS
N_DIMS = len(DIMS)
SCORE_LINE = re.search(r"\*\*(\w+) dimensions, scored 0–3 each\. (\d+) points available\. (\d+) to pass, with no dimension at 0\.\*\*", RUBRIC)
assert SCORE_LINE and SCORE_LINE.group(1) == "Five"
POINTS, PASS = int(SCORE_LINE.group(2)), int(SCORE_LINE.group(3))
assert (POINTS, PASS) == (15, 9) and POINTS == 3 * N_DIMS
assert "Two assessors score\nindependently; a split of more than 3 points goes to a third." in RUBRIC
SPLIT = 3
assert "**One retry within 30 days.**" in RUBRIC and "**60-minute peer mock interview**" in RUBRIC and "**90-minute defence**" in RUBRIC
assert "A missing component is not a zero on a dimension" in RUBRIC and "the\n  defence does not run" in RUBRIC
DEFENCE = re.findall(r"^\| (\d+–\d+) \| (.+?) \|$", RUBRIC, re.M)
assert [m for m, _ in DEFENCE] == ["0–15", "15–75", "75–90"], DEFENCE
NOT_LISTED = re.findall(r"^- \*\*(.+?)\.\*\*", RUBRIC.split("### What is deliberately NOT on the list", 1)[1].split("---", 1)[0], re.M)
assert NOT_LISTED == ["A novel feature", "Test coverage percentage", "Uptime"], NOT_LISTED
OPEN = re.search(r"Four commercial decisions this document deliberately does not make: (.+?)\. None of them", RUBRIC, re.S)
assert OPEN and "capstone tier's price" in OPEN.group(1)
# the author's decisions of 13 October 2026, as the rubric states them: your own corpus is a tenant other than the kit's
# three, in those words; the four documents start from the kit's templates; lesson 11.8's page is where learners read it
KIT_TENANTS = f"{', '.join(CC.KIT_TENANTS[:-1])} and {CC.KIT_TENANTS[-1]}"
assert KIT_TENANTS == "acme, globex and zeta" and f"**Your own corpus, ≥ 30 pages, ingested** — a tenant other than {KIT_TENANTS}" in RUBRIC
assert f"`{CC.TEMPLATES}/ARCHITECTURE.md`" in RUBRIC and "lesson 11.8's page shows this document to learners" in RUBRIC
# every lesson number the rubric names is this course's, and every file it cites exists: in the kit, among the
# templates (the four documents are the learner's, and their templates are the kit's), or in the course (the manifest)
RUBRIC_LIDS = sorted(set(re.findall(r"(?<![\w.])(\d{1,2}\.\d{1,2})(?![\w.])", RUBRIC)), key=lambda x: tuple(int(p) for p in x.split(".")))
assert all(lid in LESSON_IDS for lid in RUBRIC_LIDS), RUBRIC_LIDS
assert set(FROM_LESSONS) <= set(RUBRIC_LIDS) and "11.8" in RUBRIC_LIDS
CITED = sorted({c for c in re.findall(r"`([^`\s]+)`", RUBRIC) if re.search(r"\.(md|json|jsonl|py|sh|mk)$", c) or "/" in c[1:]})
for cited in CITED:
    assert (KIT / cited).exists() or (KIT / CC.TEMPLATES / cited).exists() or (ROOT / cited).exists(), cited
assert {"evals/golden.jsonl", "ops/gotchas.json", "course-manifest.json", "commands/tests/capstone_fork/"} <= set(CITED), CITED
N_RUBRIC_LIDS, N_CITED = len(RUBRIC_LIDS), len(CITED)


def dim_rows(n: int) -> list:
    """The 0-3 table of dimension n: (score, what it looks like), and the rubric's note under it when there is one."""
    section = RUBRIC.split(f"### {n}. ", 1)[1].split("\n### ", 1)[0].split("\n---", 1)[0]
    rows = re.findall(r"^\| ([0-3]) \| (.+?) \|$", section, re.M)
    assert [int(s) for s, _ in rows] == [0, 1, 2, 3], (n, rows)
    note = " ".join(line[2:].strip() for line in section.splitlines() if line.startswith("> "))
    return rows, note


DIM_TABLES = {int(n): dim_rows(int(n)) for n, _ in DIMS}
assert DIM_TABLES[1][0][3][1].startswith("Also names what they rejected") and "falsifiable" in DIM_TABLES[1][1]
assert "vacuous" in DIM_TABLES[4][0][3][1] and "must_not_contain" in DIM_TABLES[4][1]
assert sum(1 for n in DIM_TABLES if DIM_TABLES[n][1]) == 3                   # notes under Architecture, Cost and Evals


def plain(md: str) -> str:
    """A rubric cell without its Markdown: ** and ` dropped, the arrows and dashes kept."""
    return re.sub(r"\*\*|`", "", md).strip()


def inline(md: str) -> str:
    """A rubric sentence as HTML: its lines joined, escaped, ** as strong, * as em and ` as code."""
    text = html.escape(" ".join(md.split()), quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", text)


# the rubric's notes, in its own words, for step 9: the one under the component table, the three under the dimensions,
# and what is deliberately not on the list, each with its reason
C5_NOTE = re.search(r"^(\*\*Component 5 is the one .+?)\n\n", RUBRIC, re.M | re.S).group(1)
assert C5_NOTE.rstrip().endswith("the interview is sixty minutes of asking why.")
NOT_LISTED_ITEMS = re.findall(r"^- \*\*(.+?)\*\* (.+?)(?=\n- |\n*\Z)", RUBRIC.split("### What is deliberately NOT on the list", 1)[1]
                              .split("---", 1)[0].strip(), re.M | re.S)
assert [name for name, _ in NOT_LISTED_ITEMS] == [f"{x}." for x in NOT_LISTED], NOT_LISTED_ITEMS


# what make capstone-check reads for each component (the check's own rules, lines 20-48 of its docstring), offline and on the lane
OFFLINE_READS = {
    1: f"{CC.UI_SCRIPT}: {' and '.join(CC.IAP_FLAGS)}; the last make smoke-deployed run's /version; the newest eval report that asked the isolation rows: every one 403",
    2: f"evals/corpus/<yours>/: {CC.PAGES_MIN}+ pages as the ingest worker counts them; a passed row citing one of its documents",
    3: f"evals/golden.jsonl: {CC.GOLDEN_MIN}+ rows, {CC.ISOLATION_MIN}+ isolation; evals/run_eval.py offline exits 0 (make eval)",
    4: "the last make smoke-deployed run passed smoke-chat, smoke-media or smoke-slm, or the API's smoke with retrieval_graph on or auto",
    5: f"ARCHITECTURE.md: a Rejected or Alternatives section with {CC.REJECTED_MIN}+ options, each argued in {CC.REASON_WORDS}+ words",
    6: f"COST-MODEL.md: 1k, 10k and 100k; {CC.AMOUNTS_MIN}+ amounts in rupees and {CC.AMOUNTS_MIN}+ in dollars; a date; USD_INR = {CC.USD_INR} on one line",
    7: f"FAILURE-MODES.md: {CC.ENTRIES_MIN}+ entries, each a Symptom: line and a backticked command the fork can run (resolved, never run)",
    8: "RUNBOOK.md names make rollback or update-traffic; two successive smoke-deployed runs show a rollback with /version before and after",
}
LANE_READS = {
    1: f"GET /version as {REL.MEMBER_SA}: 200; GET /v1/sources as {REL.OUTSIDER_SA}: 403; documind-ui has IAP on",
    2: "GET /v1/sources?tenant_id=<yours>: every document listed indexed",
    3: "nothing: the suite is the fork's",
    4: "that lane's services are deployed now",
    5: "nothing: a document", 6: "nothing: a document", 7: "nothing: a document",
    8: f"both revisions are {REL.SERVICE}'s on the lane",
}
for n in range(1, 9):   # each rule above is in the check's own account of itself, so the two cannot drift apart silently
    for word in re.findall(r"\b(smoke-deployed|isolation|golden\.jsonl|run_eval\.py|retrieval_graph|Symptom|rollback|update-traffic|indexed|IAP)\b",
                           OFFLINE_READS[n] + " " + LANE_READS[n]):
        assert word in SRC, (n, word)

# ------------------------------------------------------------------ verbatim kit excerpts
EXCERPTS = {
    "rules": (f"{CC_PATH} - the eight components, each as the check reads it: the module's own account",
              block(CC_PATH, "  1  A live URL behind IAP.", end="handover writes HANDOVER.md into the fork")),
    "consts": (f"{CC_PATH} - the rubric's numbers, as the check holds them", block(CC_PATH, "COMPONENTS = {1:", n=13)),
    "loop": (f"{CC_PATH} - cmd_check(): PASS or FAIL per component, the evidence under each, and the two exits",
             block(CC_PATH, "def cmd_check(a) -> int:", end="---- the handover")),
    "c7": (f"{CC_PATH} - component_7(): FAILURE-MODES.md, four entries each proved by a command the fork can run",
           block(CC_PATH, "def component_7(fork: Fork, lane: Lane | None) -> tuple[list, list]:")),
    "rollback": (f"{CC_PATH} - rollback(): the recorded rollback, told from two make smoke-deployed runs",
                 block(CC_PATH, "def rollback(runs: list) -> tuple[dict, dict] | None:")),
    "reads": (f"{CC_PATH} - READS and gcloud_json(): the only gcloud commands it runs; any other is refused before it runs",
              block(CC_PATH, "# The only gcloud commands this runs.", end="def access_token() -> str:")),
    "pages": (f"{CC_PATH} - pages as the ingest worker counts them: form feeds, a PDF's page tree, a picture or a recording as one",
              block(CC_PATH, "def text_pages(text: str) -> int:", n=3) + "\n...\n" + block(CC_PATH, "def pages_of(path: Path) -> int | None:")),
    "mk": ("mk/capstone.mk - the two targets, neither behind guard-project",
           block("mk/capstone.mk", "capstone-check:", n=2) + "\n...\n" + block("mk/capstone.mk", "handover:", n=2)),
    "ui": ("commands/lesson-12.4.sh - documind-ui's deploy: --no-allow-unauthenticated and --iap (the service account and its environment follow)",
           block("commands/lesson-12.4.sh", "gcloud run deploy documind-ui \\", n=4)),
    "versions": ("services/frontend/documents.py - the Documents page's Versions view: one GET /v1/sources, rendered",
                 block("services/frontend/documents.py", 'r = requests.get(f"{RAG_API_URL}/v1/sources"', n=1) + "\n...\n"
                 + block("services/frontend/documents.py", 'st.dataframe([{"document": r_["name"], "status": r_["status"]', n=4)),
    "night": ("terraform/off.tf - the night job: 23:00 IST, every night",
              block("terraform/off.tf", 'resource "google_cloud_scheduler_job" "off" {', n=5)),
    "down": ("Makefile - make down: what it cannot remove, and only deleting the project does",
             block("Makefile", 'echo ">> make down cannot remove these; only deleting the project does:"', n=11)),
    "budget": ("terraform/budget.tf - the budget's four thresholds", block("terraform/budget.tf", "threshold_rules { threshold_percent = 0.5 }", n=6)),
    "handover_text": (f"{CC_PATH} - Handover.text(): the seven sections, the head, and the Not read tail",
                      block(CC_PATH, "    def text(self, written: str) -> str:", end="def cmd_handover(a) -> int:")),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["rules"].startswith("  1  A live URL behind IAP.") and E["rules"].rstrip().endswith("documind-api's revisions.")
assert E["consts"].startswith("COMPONENTS = {1:") and E["consts"].rstrip().endswith("not yours")
assert E["loop"].rstrip().endswith("return INCOMPLETE") and "print(f\"   {n}  {'FAIL' if missing else 'PASS'}  {COMPONENTS[n]}\")" in E["loop"]
assert E["c7"].rstrip().endswith('"Symptom: line and a command in backticks that the fork can run", *missing]') and "proved >= ENTRIES_MIN" in E["c7"]
assert E["rollback"].rstrip().endswith("return found") and "answered(before.get(\"version\")) and answered(run.get(\"version\"))" in E["rollback"]
assert E["reads"].startswith("# The only gcloud commands this runs.") and E["reads"].rstrip().endswith('raise Stop(f"{what} did not return JSON") from None')
assert '"capstone_check only reads, and' in E["reads"] and E["reads"].count("gcloud") >= N_READS
assert E["pages"].rstrip().endswith("return 1 if suffix in ONE_PAGE else None") and 'return max(1, text.count("\\f") + 1)' in E["pages"]
assert E["mk"].count("@$(PY) commands/capstone_check.py") == 2 and "guard-project" not in E["mk"]
assert E["ui"].rstrip().endswith("--no-allow-unauthenticated --iap \\")
assert 'params={"tenant_id": tenant_id}' in E["versions"] and '"status": r_["status"]' in E["versions"]
assert E["night"].rstrip().endswith('time_zone   = "Asia/Kolkata"') and 'schedule    = "0 23 * * *"' in E["night"]
assert E["down"].rstrip().endswith("gcloud projects delete $(PROJECT)\"; exit $$rc") and E["down"].count('echo ">>   ') == 9
assert E["budget"].count("threshold_percent") == 4 and 'spend_basis       = "FORECASTED_SPEND"' in E["budget"]
assert E["handover_text"].rstrip().endswith('return "\\n".join(head + [line for section in body for line in section] + tail) + "\\n"')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
MK = (KIT / "Makefile").read_text(encoding="utf-8")
DEFAULTS = {k: CC.make_default(MK, k) for k in ("MIN_INSTANCES", "BUDGET_AMOUNT", "TFSTATE_BUCKET", "TFSTATE_PREFIX", "REGION", "SLM_REGION")}
assert DEFAULTS == {"MIN_INSTANCES": "0", "BUDGET_AMOUNT": "5000", "TFSTATE_BUCKET": "$(PROJECT)-tfstate",
                    "TFSTATE_PREFIX": "documind/$(PROJECT)", "REGION": "us-central1", "SLM_REGION": "us-central1"}, DEFAULTS
DOWN_ITEMS = [line for line in E["down"].splitlines() if 'echo ">>   ' in line and "gcloud projects delete" not in line]
assert len(DOWN_ITEMS) == 8 and "Firestore" in DOWN_ITEMS[0] and "buckets" in DOWN_ITEMS[1] and "tuned endpoint" in DOWN_ITEMS[2]
assert "RAG Engine corpus" in DOWN_ITEMS[3] and "BigQuery views" in DOWN_ITEMS[4] and "data stores" in DOWN_ITEMS[5]
OFF = (KIT / "terraform/off.tf").read_text(encoding="utf-8")
JOB = CC.tf_block(OFF, "google_cloud_scheduler_job", "off")
JOB_NAME, SCHEDULE, ZONE = (CC.tf_string(JOB, k) for k in ("name", "schedule", "time_zone"))
assert (JOB_NAME, SCHEDULE, ZONE) == ("documind-off-nightly", "0 23 * * *", "Asia/Kolkata")
NIGHT = CC.cron_time(SCHEDULE, ZONE)
FLOORED = re.findall(r"(documind-[a-z0-9-]+):\$(?:SLM_REGION|REGION)\b", OFF)
assert FLOORED == ["documind-slm", "documind-vllm", "documind-gateway", "documind-ui"], FLOORED
BUDGET_TF = (KIT / "terraform/budget.tf").read_text(encoding="utf-8")
BUDGET_NAME = CC.tf_string(CC.tf_block(BUDGET_TF, "google_billing_budget", "documind"), "display_name")
RULES = re.findall(r'threshold_percent\s*=\s*([0-9.]+)(?:\s*\n\s*spend_basis\s*=\s*"(\w+)")?', BUDGET_TF)
assert BUDGET_NAME == "DocuMind monthly budget" and RULES == [("0.5", ""), ("0.8", ""), ("1.0", ""), ("1.2", "FORECASTED_SPEND")], RULES
THRESHOLDS = ", ".join(f"{float(p):.0%}" + (" forecast" if basis == "FORECASTED_SPEND" else "") for p, basis in RULES)
POLICY_ROWS = CC.remediate.runbooks(KIT / "terraform", CC.remediate.load_catalog(KIT / "ops" / "runbooks.json"))
N_POLICIES = len(POLICY_ROWS)
ALERTS_TF = (KIT / "terraform/alerts.tf").read_text(encoding="utf-8")
N_ALERT_BLOCKS = ALERTS_TF.count('resource "google_monitoring_alert_policy"')
BY_FILE = {}
for row in POLICY_ROWS:
    BY_FILE[row["resource"].split(" ", 1)[0].removeprefix("terraform/")] = BY_FILE.get(row["resource"].split(" ", 1)[0].removeprefix("terraform/"), 0) + 1
assert N_ALERT_BLOCKS == 8 and BY_FILE.get("alerts.tf", 0) >= N_ALERT_BLOCKS and sum(BY_FILE.values()) == N_POLICIES, (BY_FILE, N_POLICIES)
N_ALERTS_TF = BY_FILE["alerts.tf"]
assert re.search(r'resource "google_monitoring_alert_policy" "gpu_left_warm" \{\n  for_each', ALERTS_TF)     # one block, two GPU policies
assert N_ALERTS_TF == N_ALERT_BLOCKS + 1, (N_ALERTS_TF, N_ALERT_BLOCKS)
N_ROLLBACK_POLICIES = sum(1 for r in POLICY_ROWS if r.get("action") == "rollback")
assert N_ROLLBACK_POLICIES >= 1
N_GATED = sum(1 for r in POLICY_ROWS if r.get("gate"))
FILES_DESC = ", ".join(f"{n} in {f}" for f, n in sorted(BY_FILE.items(), key=lambda kv: (-kv[1], kv[0])))
UI_DEPLOY = CC.shell_command((KIT / CC.UI_SCRIPT).read_text(encoding="utf-8"), "gcloud run deploy documind-ui")
assert set(CC.IAP_FLAGS) <= set(UI_DEPLOY.split())
INGEST = (KIT / "services/ingest/main.py").read_text(encoding="utf-8")
assert 'return text, max(1, text.count("\\f") + 1)' in INGEST                                   # text_pages() is the worker's rule
assert '"isolation": 5' in (KIT / "evals/run_eval.py").read_text(encoding="utf-8")                # MIN_ROWS, the rubric's five
assert "evals/reports/" in (KIT / ".gitignore").read_text(encoding="utf-8").splitlines()          # the records are the checkout's only
GOLDEN_ROWS = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
N_KIT_GOLDEN = len(GOLDEN_ROWS)
N_KIT_ISO = sum(1 for r in GOLDEN_ROWS if r.get("shape") == "isolation")
assert (N_KIT_GOLDEN, N_KIT_ISO) == (65, 11), (N_KIT_GOLDEN, N_KIT_ISO)
REAL = json.loads((KIT / "evals/real_sources.json").read_text(encoding="utf-8"))
N_REAL_PDFS = len(REAL)
for s in REAL:   # the check counts a PDF's pages off its page tree; the kit's record of each real PDF agrees
    pdf = KIT / "evals" / "corpus" / s["tenants"][0] / f"{s['slug']}.pdf"
    assert pdf.is_file() and CC.pdf_pages(pdf.read_bytes()) == s["pages"], pdf.name
assert N_REAL_PDFS == 13
PRICES = {}
exec(compile((KIT / "shared" / "prices.py").read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
assert PRICES["USD_INR"] == CC.USD_INR == 85
NEXT = MANIFEST["modules"]["12"]["lessons"]["12.1"]["name"]
assert NEXT == "Decide whether tuning is justified and prepare data"
PROOF = MANIFEST["modules"]["11"]["lessons"][LESSON]["proof"]   # the manifest's proof: what this page and the check prove
for said in ("`make capstone-check`: the eight components PASS", "the templates as they ship fail components 5 to 8",
             "one deleted FAILURE-MODES command fails component 7 alone",
             f"the five dimensions self-scored 0 to 3, {PASS} of {POINTS} with no zero to pass", "`HANDOVER.md` written by `make handover`"):
    assert said in PROOF, (said, PROOF)

# the canned fork: Sahyadri Freight, commands/tests/capstone_fork/
CANNED = KIT / "commands/tests/capstone_fork"
DOCS = ["ARCHITECTURE.md", "COST-MODEL.md", "FAILURE-MODES.md", "RUNBOOK.md"]
assert all((CANNED / d).is_file() for d in DOCS)
TENANT = "sahyadri"
CORPUS = CC.documents(CANNED / "evals" / "corpus" / TENANT)
N_PAGES = sum(n or 0 for _, n in CORPUS)
assert CORPUS == [("driver_handbook_2026.md", 8), ("fleet_safety_manual_2026.md", 24)] and N_PAGES == 32, CORPUS
ADD_ROWS = [json.loads(line) for line in (CANNED / "evals/golden.jsonl.add").read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(ADD_ROWS) == 2 and all(r["tenant"] == TENANT for r in ADD_ROWS)
N_GOLDEN, N_ISO = N_KIT_GOLDEN + len(ADD_ROWS), N_KIT_ISO
SMOKE_RUNS = [json.loads(line) for line in (CANNED / CC.SMOKE_LOG).read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(SMOKE_RUNS) == 4 and [r["serving"] for r in SMOKE_RUNS] == ["documind-api-00041-kel", "documind-api-00042-typ",
                                                                        "documind-api-00041-kel", "documind-api-00043-fix"]
BACK = CC.rollback(SMOKE_RUNS)
assert BACK and (BACK[0]["serving"], BACK[1]["serving"]) == ("documind-api-00042-typ", "documind-api-00041-kel")
GATE = json.loads((CANNED / CC.REPORTS / "gate.json").read_text(encoding="utf-8"))
assert GATE["format"] == REL.GATE_FORMAT and GATE["revision"] == "documind-api-00043-fix" and GATE["verdict"] == "pass"
COST_HELD, COST_MISSING = CC.cost_model((CANNED / "COST-MODEL.md").read_text(encoding="utf-8"))
assert not COST_MISSING and len(COST_HELD) == 4 and COST_HELD[1].startswith("dual-priced: ") and COST_HELD[1].endswith(" in dollars"), COST_HELD
MODES = CC.failure_modes((CANNED / "FAILURE-MODES.md").read_text(encoding="utf-8"))
assert len(MODES) == 4 and all(s and len(c) == 1 for _, s, c in MODES), MODES
FM_COMMANDS = [c[0] for _, _, c in MODES]
assert FM_COMMANDS[0] == "make gotcha-drill ID=pinned-traffic"
DELETED_LINE = "Command: `make gotcha-drill ID=pinned-traffic`"
assert (CANNED / "FAILURE-MODES.md").read_text(encoding="utf-8").count(DELETED_LINE + "\n") == 1

# the templates: capstone/templates/, the canned fork's four documents emptied, a {{...}} placeholder in every slot
assert CC.TEMPLATES == "capstone/templates"
TPL = KIT / CC.TEMPLATES
assert sorted(p.name for p in TPL.iterdir()) == sorted(DOCS)
TPL_TEXT = {d: (TPL / d).read_text(encoding="utf-8") for d in DOCS}
N_PLACEHOLDERS = sum(len(re.findall(r"\{\{.*?\}\}", t)) for t in TPL_TEXT.values())
TPL_LINES = {d: sum("{{" in line for line in t.splitlines()) for d, t in TPL_TEXT.items()}
for d in DOCS:   # the template has the canned document's sections, under the same headings
    canned_heads = [title for _, title, _ in CC.sections((CANNED / d).read_text(encoding="utf-8"))]
    heads = [title.replace("{{YOUR COMPANY}}", "Sahyadri Freight") for _, title, _ in CC.sections(TPL_TEXT[d])]
    assert len(heads) == len(canned_heads) and (d == "FAILURE-MODES.md" or heads == canned_heads), (d, heads)
TPL_OPTIONS = CC.rejected_options(TPL_TEXT["ARCHITECTURE.md"])
assert len(TPL_OPTIONS) == CC.REJECTED_MIN and all(CC.words(o) < CC.REASON_WORDS for o in TPL_OPTIONS)
TPL_OPTION, TPL_WORDS = TPL_OPTIONS[0], CC.words(TPL_OPTIONS[0])
assert TPL_OPTION == "{{OPTION 1}}: {{WHY NOT}}" and TPL_WORDS == 4
assert "Rs {{AMOUNT}}" in TPL_TEXT["COST-MODEL.md"] and "(USD {{AMOUNT}})" in TPL_TEXT["COST-MODEL.md"] and "Dated {{YYYY-MM-DD}}" in TPL_TEXT["COST-MODEL.md"]
N_TPL_LINES = sum(TPL_LINES.values())
TPL_COMMANDS = [c[0] for _, _, c in CC.failure_modes(TPL_TEXT["FAILURE-MODES.md"])]
assert TPL_COMMANDS == ["make gotcha-drill ID={{GOTCHA-ID}}", "make gotcha-drill ID={{GOTCHA-ID}} LIVE=1", "make {{TARGET}}",
                        "bash commands/{{SCRIPT}}.sh"], TPL_COMMANDS
assert f"USD_INR = {CC.USD_INR}" in TPL_TEXT["COST-MODEL.md"] and not re.search(r"\bmake rollback\b|\bupdate-traffic\b", TPL_TEXT["RUNBOOK.md"])
N_TPL_TESTS = len(re.findall(r"^    def test_", (KIT / "commands/tests/test_capstone_templates.py").read_text(encoding="utf-8"), re.M))
assert N_TPL_TESTS == 13, N_TPL_TESTS

# ------------------------------------------------------------------ the forks, in a throwaway directory, and the command line as make runs it
T = Path(tempfile.mkdtemp(prefix="lesson118-")).resolve()
TOOLS = ("gcloud", "gcloud.cmd", "gcloud.ps1", "bq", "bq.cmd", "gsutil", "gsutil.cmd", "terraform", "terraform.exe")


def iso_env(extra: dict | None = None) -> dict:
    """No Google credential, no gcloud, bq, gsutil or terraform on PATH, a throwaway home: nothing here reaches a lane."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GOOGLE_", "CLOUDSDK_", "DOCUMIND_"))
           and k not in ("PROJECT", "REGION", "SLM_REGION", "FORK", "TENANT")}
    keep = [p for p in env.get("PATH", "").split(os.pathsep) if p and not any((Path(p) / t).exists() for t in TOOLS)]
    env.update(PATH=os.pathsep.join(keep), HOME=str(T), USERPROFILE=str(T), APPDATA=str(T), CLOUDSDK_CONFIG=str(T / "gcloud"),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    env.update(extra or {})
    return env


SKIP_DIRS = {"workshop_demos", "__pycache__", ".terraform", ".git", ".idea", ".vscode", "operator-evidence", ".pytest_cache"}
SKIP_FILES = {".candidate-revision", ".previous-revision", ".fault-hold", "compare.csv"}
SKIP_SUFFIX = (".pyc", ".mp4", ".mp3", ".wav", ".segments.json", ".tfstate", ".tfplan", ".tfvars", ".tfvars.json")


def ignore(folder: str, names: list) -> set:
    """What a learner's clone of the kit does not hold (deploy/.gitignore): the records, the state, the revision files."""
    rel = Path(folder).resolve().relative_to(KIT.resolve()).as_posix()
    out = {n for n in names if n in SKIP_DIRS or n in SKIP_FILES or n.endswith(SKIP_SUFFIX) or ".tfstate." in n or n.startswith("tfplan")}
    if rel == "evals":
        out.add("reports")
    if rel == "services/slm":
        out.add("build")
    return out


def kit_copy(dest: Path) -> Path:
    """The kit as a learner's clone holds it: every tracked file, none of the records a lane left in this checkout."""
    shutil.copytree(KIT, dest, ignore=ignore)
    return dest


def assemble(dest: Path) -> Path:
    """The canned fork: a copy of the kit, Sahyadri Freight's files over it, its golden rows appended (the .add file)."""
    kit_copy(dest)
    for path in sorted(CANNED.rglob("*")):
        if not path.is_file():
            continue
        target = dest / path.relative_to(CANNED)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".add":
            with open(target.with_suffix(""), "ab") as f:
                f.write(path.read_bytes())
        else:
            shutil.copyfile(path, target)
    return dest


def cli(*args: str, cwd: Path = KIT, want: int = 0) -> str:
    """python commands/capstone_check.py ARGS, the line each make target runs; stdout then stderr, as a terminal shows them."""
    r = subprocess.run([sys.executable, "commands/capstone_check.py", *args], cwd=str(cwd), env=iso_env(), capture_output=True,
                       text=True, encoding="utf-8", timeout=900)
    assert r.returncode == want, (args, r.returncode, r.stdout[-2000:], r.stderr[-2000:])
    return r.stdout + r.stderr


def run_cell(body: str, cwd: Path = KIT) -> str:
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=iso_env())
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


def verdicts(out: str) -> dict:
    return {int(n): v for n, v in re.findall(r"(?m)^   (\d)  (PASS|FAIL)  ", out)}


def rewrap(out: str, here: Path, shown: str) -> str:
    """The check's first paragraph names the fork's directory: this machine's throwaway path becomes the path a learner's
    cell prints, and the paragraph is wrapped again as say() wraps it (118 columns, the >> prefix)."""
    lines = out.splitlines()
    end = next(i for i, line in enumerate(lines) if re.match(r"^   \d  (PASS|FAIL)  ", line))
    head = " ".join(line.strip() for line in lines[:end]).replace(str(here), shown).replace("\\", "/")
    assert head.startswith(">> capstone-check: the fork at " + shown), head
    wrapped = textwrap.fill(head[3:], width=118, initial_indent=">> ", subsequent_indent="   ", break_long_words=False, break_on_hyphens=False)
    return "\n".join([wrapped, *lines[end:]]) + "\n"


OUT = {}
OUT["selftest"] = cli("--selftest")
assert OUT["selftest"].startswith("capstone_check selftest: ARCHITECTURE.md's rejected options") and OUT["selftest"].count("\n") == 1

BARE = kit_copy(T / "kit")
bare = cli("check", "--fork", str(BARE), want=1)
assert verdicts(bare) == {n: "PASS" if n == 3 else "FAIL" for n in range(1, 9)}, bare
flat = " ".join(bare.split())
assert "evals/corpus/ holds no tenant of your own, only the kit's (acme, globex, zeta)" in flat and "ARCHITECTURE.md is missing from the fork's root" in flat
assert f"no make smoke-deployed run in {CC.SMOKE_LOG}" in flat and f"evals/golden.jsonl: {N_KIT_GOLDEN} golden rows, {N_KIT_ISO} of them isolation rows" in flat
assert "incomplete: components 1, 2, 4, 5, 6, 7 and 8 FAIL" in flat
OUT["kit"] = rewrap(bare, BARE, KIT_PATH)

FORK = assemble(T / "sahyadri")
golden = [json.loads(line) for line in (FORK / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(golden) == N_GOLDEN and sum(1 for r in golden if r["shape"] == "isolation") == N_ISO
good = cli("check", "--fork", str(FORK))
assert verdicts(good) == {n: "PASS" for n in range(1, 9)}, good
flat = " ".join(good.split())
for line in ("the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated",
             "a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3",
             f"every isolation row ({N_ISO}) answered 403 to the outsider (evals/reports/gate-documind-api-00043-fix.json)",
             f"{TENANT}'s corpus: {len(CORPUS)} documents, {N_PAGES} pages as the ingest worker counts them",
             "a query cites one: sh-01 cited fleet_safety_manual_2026.md and passed",
             f"{N_GOLDEN} golden rows, {N_ISO} of them isolation rows", "make eval: evals/run_eval.py offline exits 0",
             "chat: make smoke-chat passed", "media: make smoke-media passed",
             "names 3 rejected options with a reason: GKE Autopilot for the API; A second vector database (Pinecone); Fine-tuning before prompting",
             *COST_HELD, "dated 2026-11-18", "at 85 rupees to the dollar",
             "4 entries proved by a command the fork runs", '"A poison upload pages an hour later": make poison',
             "a recorded rollback, the traffic left the revision the candidate tag names: documind-api-00042-typ -> documind-api-00041-kel",
             "/version before: git_sha abc1234, gemini-3.6-flsh", "complete: every one of the eight components PASSes"):
    assert line in flat, line
OUT["fork"] = rewrap(good, FORK, FORK_PATH)

# the Change-it: one FAILURE-MODES command deleted, exactly that component fails; the file put back, every one passes again
BROKEN = T / "broken"
shutil.copytree(FORK, BROKEN)
modes_path = BROKEN / "FAILURE-MODES.md"
modes_path.write_text(modes_path.read_text(encoding="utf-8").replace(DELETED_LINE + "\n", ""), encoding="utf-8", newline="\n")
assert DELETED_LINE not in modes_path.read_text(encoding="utf-8")
broken = cli("check", "--fork", str(BROKEN), want=1)
assert verdicts(broken) == {n: "FAIL" if n == 7 else "PASS" for n in range(1, 9)}, broken
flat = " ".join(broken.split())
assert "3 entries proved, 4 or more" in flat and '"Pinned traffic hides a change": no command in backticks' in flat and "incomplete: component 7 FAILs" in flat
shutil.copyfile(CANNED / "FAILURE-MODES.md", modes_path)
assert cli("check", "--fork", str(BROKEN)).count("PASS") == 9                  # eight components, and PASSes in the last line
OUT["change"] = rewrap(broken, BROKEN, FORK_PATH) + "exit 1\nexit 0\n"

# the templates, as they ship, over the canned fork's four documents: components 5 to 8 FAIL, each on the slots of its
# document that still hold a placeholder, while 1 to 4 still PASS on the canned records; the canned four back, all PASS
TEMPLATED = T / "templated"
shutil.copytree(FORK, TEMPLATED)
for d in DOCS:
    shutil.copyfile(TPL / d, TEMPLATED / d)
templated = cli("check", "--fork", str(TEMPLATED), want=1)
assert verdicts(templated) == {n: "FAIL" if n >= 5 else "PASS" for n in range(1, 9)}, templated
flat = " ".join(templated.split())
for line in ("names 0 rejected options with a reason (and 3 without one: {{OPTION 1}}; {{OPTION 2}}; {{OPTION 3}})",
             "COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month", "gives 0 amounts in rupees",
             "carries no date", "at 85 rupees to the dollar", "0 entries proved, 4 or more",
             '"{{FAILURE 1}}": `make gotcha-drill ID={{GOTCHA-ID}}`: ID={{GOTCHA-ID}} is not in ops/gotchas.json',
             "the fork's Makefile and mk/*.mk define no {{TARGET}} target", "the fork holds no commands/{{SCRIPT}}.sh",
             "RUNBOOK.md does not say how to roll back", "a recorded rollback, the traffic left the revision the candidate tag names",
             "incomplete: components 5, 6, 7 and 8 FAIL"):
    assert line in flat, line
GREP = "".join(f"{FORK_PATH}/{d}:{TPL_LINES[d]}\n" for d in DOCS)       # grep -c: the lines that still hold a placeholder
for d in DOCS:
    shutil.copyfile(CANNED / d, TEMPLATED / d)
assert cli("check", "--fork", str(TEMPLATED)).count("PASS") == 9
OUT["templates"] = rewrap(templated, TEMPLATED, FORK_PATH) + "exit 1\n" + GREP + "exit 0\n"

# only the slots the check reads filled: components 5 to 8 PASS while the request path, the cost of one answer and the
# symptoms are still placeholders (step 9's "reads only the slots it checks"), the check's own functions on a copy
HALF = T / "half"
shutil.copytree(FORK, HALF)
HALF_FILLS = {"ARCHITECTURE.md": [("{{WHY NOT}}", "it would cost more than it saves at our volume")],
              "COST-MODEL.md": [("Rs {{AMOUNT}}", "Rs 100"), ("USD {{AMOUNT}}", "USD 1.18"), ("{{YYYY-MM-DD}}", "2026-11-18")],
              "FAILURE-MODES.md": [("make gotcha-drill ID={{GOTCHA-ID}}`", "make gotcha-drill ID=rollback-keeps-template`"),
                                   ("ID={{GOTCHA-ID}} LIVE=1", "ID=pinned-traffic LIVE=1"), ("make {{TARGET}}", "make poison"),
                                   ("commands/{{SCRIPT}}.sh", "commands/incident-drill.sh")],
              "RUNBOOK.md": []}
HALF_TEXT = {}
for d in DOCS:
    text = TPL_TEXT[d]
    for old, new in HALF_FILLS[d]:
        assert old in text, (d, old)
        text = text.replace(old, new)
    if d == "RUNBOOK.md":
        text, n = re.subn(r"`\{\{[^`]*\}\}`", "`make rollback PROJECT=documind-ai-YOUR-ID REGION=asia-south1`", text)
        assert n == 1
    HALF_TEXT[d] = text
    (HALF / d).write_text(text, encoding="utf-8", newline="\n")
assert "{{From the browser" in HALF_TEXT["ARCHITECTURE.md"] and "USD {{COST}}, Rs {{COST}}" in HALF_TEXT["COST-MODEL.md"]
assert HALF_TEXT["FAILURE-MODES.md"].count("Symptom: {{") == CC.ENTRIES_MIN and all("{{" in t for t in HALF_TEXT.values())
HALF_FORK = CC.Fork(HALF)
assert {n: fn(HALF_FORK, None)[1] for n, fn in CC.CHECKS if n >= 5} == {5: [], 6: [], 7: [], 8: []}

# the records, read with the kit's own rules (the cell runs here against the canned fork; a learner's runs against /tmp/sahyadri)
RECORDS_PY = r'''import importlib.util, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
spec = importlib.util.spec_from_file_location("capstone_check", "commands/capstone_check.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)                           # the kit's own rules: no lane, no network, nothing changed
fork = cc.Fork(Path("FORK_DIR"))
print(f"{len(fork.runs)} make smoke-deployed runs in {cc.SMOKE_LOG}, oldest first:")
for run in fork.runs:
    print(f"  {run['finished']}  serving {run['serving']}  candidate {run['candidate']}  {run['verdict'].upper():4}  "
          f"/version: {cc.release.answered(run['version'])}")
before, after = cc.rollback(fork.runs)
print(f"the rollback the check finds: {before['serving']} -> {after['serving']}, "
      f"{'the traffic left the revision the candidate tag names' if after['candidate'] == before['serving'] else 'back to an older revision'}")
for rel, report in fork.reports:
    print(f"{rel}: {report['rows']} rows, {cc.isolation_asked(report)} isolation rows asked, every one refused: {cc.outsider_refused(report)}")
print(f"your own tenant: {fork.own_tenant}; " + ", ".join(f"{name} {n} pages" for name, n in fork.corpus[fork.own_tenant])
      + f"; {sum(n or 0 for _, n in fork.corpus[fork.own_tenant])} in all")
for title, symptom, commands in cc.failure_modes((fork.root / "FAILURE-MODES.md").read_text(encoding="utf-8")):
    why = [cc.unresolved(c, fork.targets, fork.has_file, fork.registry) for c in commands]
    print(f"FAILURE-MODES.md: {title!r}: Symptom {'yes' if symptom else 'no'}; " + "; ".join(f"`{c}` {w or 'runs in the fork'}" for c, w in zip(commands, why)))'''
OUT["records"] = run_cell(RECORDS_PY.replace("FORK_DIR", str(FORK).replace("\\", "/")))
R_ = OUT["records"]
assert R_.startswith(f"4 make smoke-deployed runs in {CC.SMOKE_LOG}, oldest first:\n") and "the rollback the check finds: documind-api-00042-typ -> documind-api-00041-kel, the traffic left" in R_
assert f"your own tenant: {TENANT}; driver_handbook_2026.md 8 pages, fleet_safety_manual_2026.md 24 pages; {N_PAGES} in all" in R_
assert R_.count("runs in the fork") == 4 and "gate-documind-api-00043-fix.json: 67 rows, 11 isolation rows asked, every one refused: True" in R_
assert str(T) not in R_ and "netse" not in R_

# the handover, offline, on the canned fork: the stdout line, then HANDOVER.md whole
hand = cli("handover", "--fork", str(FORK))
assert hand.startswith(">> handover: ") and hand.rstrip().endswith("from this checkout only (PROJECT= adds the lane)")
HANDOVER = (FORK / "HANDOVER.md").read_text(encoding="utf-8")
STAMP = re.search(r" at (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ), from this checkout", HANDOVER)
assert STAMP and REL.read_stamp(STAMP.group(1))
HANDOVER_SHOWN = HANDOVER.replace(STAMP.group(1), "YYYY-MM-DDTHH:MM:SSZ")
assert HANDOVER_SHOWN.startswith("# Handover: DocuMind, this checkout\n") and HANDOVER_SHOWN.rstrip().endswith("## Not read\n\n- the lane: no PROJECT was given")
assert HANDOVER_SECTIONS == re.findall(r"^## (?!Not read)(.+)$", HANDOVER_SHOWN, re.M) and HANDOVER_SHOWN.count("\n## ") == N_SECTIONS + 1
POL_LINE = re.search(r"^(\d+) policies declared in terraform/\*\.tf, each with what ops/runbooks\.json says to do when it pages\.$", HANDOVER_SHOWN, re.M)
assert POL_LINE and int(POL_LINE.group(1)) == N_POLICIES, POL_LINE
assert f"the Cloud Scheduler job `{JOB_NAME}`: `{SCHEDULE}` in {ZONE}, {NIGHT}, every night" in HANDOVER_SHOWN and ", ".join(FLOORED) in HANDOVER_SHOWN
assert f"`MIN_INSTANCES ?= {DEFAULTS['MIN_INSTANCES']}` in the Makefile" in HANDOVER_SHOWN
assert "- `.candidate-revision`: none in this checkout\n- `.previous-revision`: none in this checkout" in HANDOVER_SHOWN
assert f"the gate record (`{CC.REPORTS}/gate.json`): documind-api-00043-fix, PASS, finished 2026-11-17T10:12:00Z; make promote-gated holds it for 24 hours" in HANDOVER_SHOWN
assert "the last make smoke-deployed run: 2026-11-17T10:30:00Z, serving documind-api-00043-fix, PASS" in HANDOVER_SHOWN
assert "No confirmed inputs in this checkout" in HANDOVER_SHOWN
assert f"budget.tf's `{BUDGET_NAME}`, `BUDGET_AMOUNT ?= {DEFAULTS['BUDGET_AMOUNT']}` in the Makefile" in HANDOVER_SHOWN and f"alerting at {THRESHOLDS} of it" in HANDOVER_SHOWN
assert "Terraform keeps the lane's state in `gs://<project>-tfstate/documind/<project>/default.tfstate` (the Makefile's TFSTATE_BUCKET and TFSTATE_PREFIX defaults)" in HANDOVER_SHOWN
assert "| Policy | Declared in | Applied | When it pages | On the lane |" in HANDOVER_SHOWN and HANDOVER_SHOWN.count("| - |\n") == N_POLICIES
N_HANDOVER_LINES = HANDOVER_SHOWN.count("\n")
OUT["handover_off"] = hand.replace(str(FORK) + os.sep, FORK_PATH + "/").replace(str(FORK), FORK_PATH).replace("\\", "/") + HANDOVER_SHOWN
assert OUT["handover_off"].startswith(f">> handover: {FORK_PATH}/HANDOVER.md, from this checkout only")
for key in ("kit", "fork", "change", "templates", "handover_off", "selftest"):
    assert str(T) not in OUT[key] and "netse" not in OUT[key] and "Temp" not in OUT[key], key
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the cells
def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


ASSEMBLE_SH = (f"rm -rf {FORK_PATH} && git clone -q --local . {FORK_PATH}      # a copy of the kit, with none of your records\n"
               f"cp -r commands/tests/capstone_fork/. {FORK_PATH}/              # Sahyadri Freight's documents, corpus and records over it\n"
               f"cat {FORK_PATH}/evals/golden.jsonl.add >> {FORK_PATH}/evals/golden.jsonl && rm {FORK_PATH}/evals/golden.jsonl.add\n"
               f"make capstone-check FORK={FORK_PATH}")
CHANGE_SH = (f"sed -i '/^Command: `make gotcha-drill ID=pinned-traffic`$/d' {FORK_PATH}/FAILURE-MODES.md   # one command gone\n"
             f"make capstone-check FORK={FORK_PATH}; echo \"exit $?\"\n"
             f"cp commands/tests/capstone_fork/FAILURE-MODES.md {FORK_PATH}/      # the file back as it was\n"
             f"make capstone-check FORK={FORK_PATH} >/dev/null; echo \"exit $?\"")
TEMPLATES_SH = (f"cp {CC.TEMPLATES}/*.md {FORK_PATH}/                 # the four templates over the canned four, as they ship\n"
                f"make capstone-check FORK={FORK_PATH}; echo \"exit $?\"\n"
                "grep -c '{{' " + FORK_PATH + "/{ARCHITECTURE,COST-MODEL,FAILURE-MODES,RUNBOOK}.md   # lines with a placeholder left\n"
                f"cp commands/tests/capstone_fork/*.md {FORK_PATH}/      # the canned four back\n"
                f"make capstone-check FORK={FORK_PATH} >/dev/null; echo \"exit $?\"")
REST_SH = ('curl -s -o /dev/null -w "GET /version as documind-ui-sa: %{http_code}\\n" "$API/version" -H "Authorization: Bearer $(tok "$API")"\n'
           'curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")"; echo\n'
           'curl -s -o /dev/null -w "GET /v1/sources?tenant_id=$TENANT as documind-outsider-sa: %{http_code}\\n" \\\n'
           '  "$API/v1/sources?tenant_id=$TENANT" -H "Authorization: Bearer $(otok)"\n'
           'gcloud run services describe documind-ui --region "$REGION" --project "$PROJECT" --format=json | grep -i iap || echo "no iap annotation: see step 9"')
CELLS = {
    "selftest": "python commands/capstone_check.py --selftest",
    "kit": "make capstone-check                 # FORK=. : the checkout you are in, offline",
    "fork": ASSEMBLE_SH,
    "records": heredoc(RECORDS_PY.replace("FORK_DIR", FORK_PATH)),
    "templates": TEMPLATES_SH,
    "ref": "make capstone-check                 # in the fork, offline: its files, its records, and make eval",
    "change": CHANGE_SH,
    "rest": REST_SH,
    "live": 'make capstone-check PROJECT="$PROJECT" REGION="$REGION"',
    "handover_off": f"make handover FORK={FORK_PATH} && cat {FORK_PATH}/HANDOVER.md",
    "handover": 'make handover PROJECT="$PROJECT" REGION="$REGION" && cat HANDOVER.md',
}
OFF = "run in the operator shell, in the kit (offline: nothing leaves your machine; Rs 0)"
CELL_LABELS = {
    "selftest": "run in the operator shell, in the kit (the rules on hand-made input; no fork, no lane, Rs 0)",
    "kit": "run in the operator shell, in the kit (reads your checkout and runs make eval, a few seconds; no lane, Rs 0)",
    "fork": "run in the operator shell, in the kit (a copy of the kit with the canned fork over it, then the check; Rs 0)",
    "records": "run in the operator shell, in the kit (the kit's own rules on the canned fork's records; Rs 0)",
    "templates": "run in the operator shell, in the kit (the templates over the canned fork's copy, then its four back; Rs 0)",
    "ref": "run in the operator shell, in your fork (offline; Rs 0)",
    "change": "run in the operator shell, in the kit (edits the canned fork's copy, then puts it back; Rs 0)",
    "rest": "run in the operator shell, in the kit (three GETs with the two tokens, one describe; Rs 0)",
    "live": f"run in the operator shell, in your fork (gcloud reads from an allow-list of {N_READS}, two tokens, three GETs; Rs 0)",
    "handover_off": "run in the operator shell, in the kit (writes HANDOVER.md into the canned fork; Rs 0)",
    "handover": "run in the operator shell, in your fork (reads the lane, writes HANDOVER.md into the fork; Rs 0)",
}
BUILT = "(this command run on the kit when the page was built)"
OUT_LABELS = {
    "selftest": BUILT,
    "kit": "(this command run on a copy of the kit as it ships, with no records, when the page was built: your checkout's records change components 1, 4 and 8)",
    "fork": "(this command run on the canned fork when the page was built)",
    "records": "(this cell run on the canned fork when the page was built)",
    "templates": "(this cell run on a copy of the canned fork when the page was built)",
    "change": "(this cell run on a copy of the canned fork when the page was built)",
    "handover_off": "(this command run on the canned fork when the page was built; the time stamp is yours)",
}
LANE = "(the author's lane, recorded: your project, revisions, dates and times are yours)"
REF = "(the author's reference fork, recorded: your fork's documents, corpus and records are yours)"
REC = {"rest": ("rest_reads.txt", LANE), "ref": ("capstone_check.txt", REF), "live": ("capstone_live.txt", LANE),
       "handover": ("handover.txt", LANE)}
for key, (name, label) in REC.items():
    OUT[key] = pb.recorded(LESSON, name)
    OUT_LABELS[key] = label
assert set(CELLS) == set(OUT) == set(CELL_LABELS) == set(OUT_LABELS), (set(CELLS) ^ set(OUT))


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the rubric as an interactive: generated from the file
def esc(text: str) -> str:
    return html.escape(text, quote=False)


COMP_ITEMS = []
for n, name, where, how in ROWS:
    COMP_ITEMS.append(
        f'<label class="cs-comp" data-fail="0"><input type="checkbox" checked data-n="{n}" aria-label="component {n} passes">'
        f'<span class="cs-name">{n}. {esc(plain(name))} <span class="cs-how">(from {esc(plain(where))})</span></span>'
        f'<span class="cs-how">A reviewer: {esc(plain(how))}</span>'
        f'<span class="cs-kit">make capstone-check reads {esc(OFFLINE_READS[int(n)])}. With PROJECT: {esc(LANE_READS[int(n)])}.</span></label>')
COMP_ITEMS = "\n".join(COMP_ITEMS)
DIM_ITEMS = []
for n, name in DIMS:
    rows, note = DIM_TABLES[int(n)]
    options = "".join(f'<option value="{s}"{" selected" if s == "2" else ""}>{s}: {esc(plain(what))}</option>' for s, what in rows)
    DIM_ITEMS.append(f'<label class="cs-dim"><span class="cs-dname">{n}. {esc(name)}</span><select data-d="{n}" aria-label="dimension {n}">{options}</select></label>')
DIM_ITEMS = "\n".join(DIM_ITEMS)
DIM_NAMES = [name for _, name in DIMS]

RULE_JS = ("function rule(fails, scores){ var total = 0, zeros = []; scores.forEach(function(v, i){ total += v; if (v === 0) zeros.push(i + 1); });"
           " if (fails.length) return {code: 'incomplete', total: total, zeros: zeros};"
           " if (zeros.length) return {code: 'zero', total: total, zeros: zeros};"
           f" return {{code: total >= {PASS} ? 'pass' : 'short', total: total, zeros: zeros}}; }}")
UI_JS = r"""var root = document.getElementById('cs'); if (!root) return;
  var comps = Array.prototype.slice.call(root.querySelectorAll('.cs-comp input')), dims = Array.prototype.slice.call(root.querySelectorAll('.cs-dim select'));
  var dimsBox = document.getElementById('cs-dims'), out = document.getElementById('cs-verdict');
  RULE_JS
  function p(text, mono){ var e = document.createElement('p'); if (mono) { var b = document.createElement('b'); b.textContent = mono; e.appendChild(b); e.appendChild(document.createTextNode(' ' + text)); } else { e.textContent = text; } return e; }
  function names(list){ return list.map(function(i){ return i + '. ' + D[i - 1]; }).join(', '); }
  function apply(){
    var fails = [], scores = [];
    comps.forEach(function(c){ c.parentNode.setAttribute('data-fail', c.checked ? '0' : '1'); if (!c.checked) fails.push(parseInt(c.getAttribute('data-n'), 10)); });
    dims.forEach(function(s){ scores.push(parseInt(s.value, 10)); });
    var r = rule(fails, scores); out.textContent = '';
    dimsBox.setAttribute('aria-disabled', fails.length ? 'true' : 'false');
    dims.forEach(function(s){ s.disabled = fails.length > 0; });
    out.setAttribute('data-ok', r.code === 'pass' ? '1' : '0');
    if (r.code === 'incomplete') { out.appendChild(p('component' + (fails.length > 1 ? 's ' : ' ') + fails.join(', ') + ' FAIL. The defence does not run, and nothing is scored: a missing component is not a zero on a dimension, it is an incomplete submission.', 'INCOMPLETE')); out.appendChild(p('make capstone-check exits 1 and says the same.')); return; }
    if (r.code === 'zero') { out.appendChild(p(r.total + ' of POINTS, with ' + names(r.zeros) + ' at 0: not a pass. The no-zero rule decides before the total does.', 'NO PASS')); return; }
    if (r.code === 'short') { out.appendChild(p(r.total + ' of POINTS, no dimension at 0, but under PASSMARK: not a pass.', 'NO PASS')); return; }
    out.appendChild(p(r.total + ' of POINTS, no dimension at 0: a pass. Two assessors score independently; a split of more than SPLIT points goes to a third.', 'PASS')); }
  comps.concat(dims).forEach(function(x){ x.addEventListener('change', apply); });
  apply();""".replace("RULE_JS", RULE_JS).replace("POINTS", str(POINTS)).replace("PASSMARK", str(PASS)).replace("SPLIT", str(SPLIT))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar D = " + json.dumps(DIM_NAMES, ensure_ascii=True) + ";\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert "<div" not in JS and "<tr" not in JS and "</" not in JS.replace("</script>", "") and "—" not in JS and "–" not in JS

# the pass rule, checked in Node against the same rule in Python: every score combination, with and without a failed component
NODE = (RULE_JS + "\nvar out = [];\nfor (var a = 0; a < 4; a++) for (var b = 0; b < 4; b++) for (var c = 0; c < 4; c++) for (var d = 0; d < 4; d++) for (var e = 0; e < 4; e++) {"
        " out.push(rule([], [a, b, c, d, e]).code); out.push(rule([7], [a, b, c, d, e]).code); }\nprocess.stdout.write(JSON.stringify(out));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
WANT = []
for a in range(4):
    for b in range(4):
        for c in range(4):
            for d in range(4):
                for e in range(4):
                    scores = (a, b, c, d, e)
                    WANT.append("zero" if 0 in scores else "pass" if sum(scores) >= PASS else "short")
                    WANT.append("incomplete")
assert json.loads(node.stdout) == WANT, "the self-score's rule disagrees with the rubric"
N_PASSING = sum(1 for code in WANT[::2] if code == "pass")
N_COMBOS = len(WANT) // 2
assert N_COMBOS == 4 ** N_DIMS == 1024


# ------------------------------------------------------------------ the tables the parts carry
def td(label: str, text: str) -> str:
    return f'<td data-label="{label}">{text}</td>'


def code(text: str) -> str:
    return "<code>" + html.escape(text) + "</code>"


DIM_TABLE = "\n".join(
    f"<tr><td>{n}. {esc(name)}</td>" + "".join(td(f"Score {s}", esc(plain(what))) for s, what in DIM_TABLES[int(n)][0]) + "</tr>"
    for n, name in DIMS)
DEFENCE_ROWS = "\n".join(f"<tr><td>{esc(minutes)}</td>{td('What happens', esc(plain(what)))}</tr>" for minutes, what in DEFENCE)
POLICY_ROWS_HTML = "\n".join(
    f"<tr><td>{esc(r['policy'])}</td>{td('Declared in', esc(r['resource'].split(' ', 1)[0].removeprefix('terraform/')))}"
    f"{td('Applied', 'when ' + esc(r['gate'].upper()) + '=true' if r.get('gate') else 'always')}"
    f"{td('When it pages', 'make remediate proposes a rollback' if r.get('action') == 'rollback' else 'a person: ' + esc(r.get('person') or 'see its documentation'))}</tr>"
    for r in POLICY_ROWS)
READ_ROWS = "\n".join(f"<li>{code('gcloud ' + name)}</li>" for name in READ_NAMES)
DOWN_LIST = "\n".join(f"<li>{esc(re.search(r'echo \">>   (.*?)\"; \\$', line).group(1))}</li>" for line in DOWN_ITEMS)
assert DOWN_LIST.count("<li>") == 8
RUBRIC_NOTES = "\n".join(
    [f"<li>{inline(C5_NOTE)}</li>"]
    + [f"<li><strong>Dimension {n}, {esc(name)}.</strong> {inline(DIM_TABLES[int(n)][1])}</li>" for n, name in DIMS if DIM_TABLES[int(n)][1]]
    + [f"<li><strong>Not on the list: {inline(name[0].lower() + name[1:])}</strong> {inline(why)}</li>" for name, why in NOT_LISTED_ITEMS])
assert RUBRIC_NOTES.count("<li>") == 1 + 3 + len(NOT_LISTED) and "**" not in RUBRIC_NOTES and "`" not in RUBRIC_NOTES

STATS = {
    "N_COMPONENTS": str(N_COMPONENTS), "N_DIMS": str(N_DIMS), "POINTS": str(POINTS), "PASS": str(PASS), "SPLIT": str(SPLIT),
    "GOLDEN_MIN": str(CC.GOLDEN_MIN), "ISOLATION_MIN": str(CC.ISOLATION_MIN), "PAGES_MIN": str(CC.PAGES_MIN),
    "REJECTED_MIN": str(CC.REJECTED_MIN), "REASON_WORDS": str(CC.REASON_WORDS), "ENTRIES_MIN": str(CC.ENTRIES_MIN),
    "AMOUNTS_MIN": str(CC.AMOUNTS_MIN), "USD_INR": str(CC.USD_INR), "N_READS": str(N_READS), "N_TESTS": str(N_TESTS),
    "N_SECTIONS": str(N_SECTIONS), "N_POLICIES": str(N_POLICIES), "N_ALERT_BLOCKS": str(N_ALERT_BLOCKS), "N_ALERTS_TF": str(N_ALERTS_TF),
    "FILES_DESC": FILES_DESC,
    "N_ROLLBACK_POLICIES": str(N_ROLLBACK_POLICIES), "N_GATED": str(N_GATED), "NIGHT": NIGHT, "JOB_NAME": JOB_NAME, "SCHEDULE": SCHEDULE,
    "FLOORED": ", ".join(FLOORED), "MIN_INSTANCES": DEFAULTS["MIN_INSTANCES"], "BUDGET_AMOUNT": DEFAULTS["BUDGET_AMOUNT"],
    "BUDGET_NAME": BUDGET_NAME, "THRESHOLDS": THRESHOLDS, "MAX_AGE_HOURS": f"{REL.MAX_AGE_HOURS:g}",
    "N_PAGES": str(N_PAGES), "N_DOCS": str(len(CORPUS)), "N_GOLDEN": str(N_GOLDEN), "N_ISO": str(N_ISO), "N_KIT_GOLDEN": str(N_KIT_GOLDEN),
    "N_RUNS": str(len(SMOKE_RUNS)), "N_REAL_PDFS": str(N_REAL_PDFS), "N_HANDOVER_LINES": str(N_HANDOVER_LINES),
    "N_COMBOS": str(N_COMBOS), "N_PASSING": str(N_PASSING),
    "COMP_ITEMS": COMP_ITEMS, "DIM_ITEMS": DIM_ITEMS, "DIM_TABLE": DIM_TABLE, "DEFENCE_ROWS": DEFENCE_ROWS,
    "POLICY_ROWS": POLICY_ROWS_HTML, "READ_ROWS": READ_ROWS, "DOWN_LIST": DOWN_LIST, "RUBRIC_NOTES": RUBRIC_NOTES,
    "NEXT_NAME": esc(NEXT), "FORK_PATH": FORK_PATH,
    "KIT_TENANTS": KIT_TENANTS, "TEMPLATES": CC.TEMPLATES, "N_PLACEHOLDERS": str(N_PLACEHOLDERS), "N_TPL_TESTS": str(N_TPL_TESTS),
    "N_RUBRIC_LIDS": str(N_RUBRIC_LIDS), "N_CITED": str(N_CITED), "TPL_OPTION": esc(TPL_OPTION), "TPL_WORDS": str(TPL_WORDS),
    "N_TPL_LINES": str(N_TPL_LINES), "FROM_OTHERS": ", ".join(lid for lid in FROM_LESSONS if lid != LESSON),
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if not k.endswith(("_ITEMS", "_TABLE", "_ROWS", "_LIST"))})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"rubric: {N_COMPONENTS} components, {N_DIMS} dimensions, {PASS} of {POINTS} with no zero; the rule checked in Node on {N_COMBOS} "
      f"score combinations ({N_PASSING} pass); {N_RUBRIC_LIDS} lesson numbers, all the manifest's; {N_CITED} files cited, all there | "
      f"the check: selftest ok; the kit as it ships 1 PASS 7 FAIL; the canned fork 8 PASS ({len(CORPUS)} documents, {N_PAGES} pages, "
      f"{N_GOLDEN} rows); its documents swapped for the templates ({N_PLACEHOLDERS} placeholders), 5 to 8 FAIL; the Change-it fails "
      f"component 7 alone | the handover: {N_SECTIONS} sections, {N_POLICIES} policies, the night job at {NIGHT}")
