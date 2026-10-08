# Lesson 0.2: Reproduce the local environment, read the master diagram and prove a first success

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: install the tools, clone the kit, make the venv |
| 4 | [demo_04_the_rs_0_lane_the_notice_period_question_with_citations.py](demo_04_the_rs_0_lane_the_notice_period_question_with_citations.py) | The Rs 0 lane: the notice-period question, with citations |
| 5 | [demo_05_prove_a_first_success_make_dryrun.py](demo_05_prove_a_first_success_make_dryrun.py) | Prove a first success: make dryrun |
| 6 | [demo_06_diagnose_a_first_failure_one_loosened_row.py](demo_06_diagnose_a_first_failure_one_loosened_row.py) | Diagnose a first failure: one loosened row |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

Install what is missing, open a new terminal so its PATH is fresh, and check. Each tool should print a path; the versions below the paths are the second check, against the table.

**`step_01_the_tools_and_why_the_kit_needs_each(session)` — Before you run anything: install the tools, clone the kit, make the venv / The tools, and why the kit needs each**

Install what is missing, open a new terminal so its PATH is fresh, and check. Each tool should print a path; the versions below the paths are the second check, against the table.

Operation: bash — run in a terminal on your laptop, after installing the tools.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/tool_checks.txt]
```

### demo_04_the_rs_0_lane_the_notice_period_question_with_citations.py

The lane gets a venv of its own, ~/rag-local-venv. Its packages are the chat service's, LangChain, LangGraph, Chroma and the Ollama client among them, installed on top of the service's image pins as services/chat/requirements-local.txt asks. Keeping them out of ~/rag-shell-venv leaves the operator pins exactly where rag_check_python_dependencies expects them, and every later session runs that check; the kit's CI keeps the chat service's pins in a venv of their own for the same reason. Then Ollama pulls the model, once. Start it in the second terminal, so the first stays free for questions. One line in this block matters more than it looks. The recipe seeds from the kit's root and serves from services/chat, and the store's default path, ./documind_chroma, is relative, so the two commands would open two different directories: the service would find an empty store and answer local corpus is empty. Exporting one absolute path as DOCUMIND_CHROMA_DIR gives both commands the same directory. From the first terminal. The health check first: it names the profile, and the brains this service can run. From the first terminal. The health check first: it names the profile, and the brains this service can run. The service has 4 brains (langchain, langgraph, adk and direct), and langchain is the default: a tool loop in which the model decides when to search. This lesson asks the direct brain, which has no loop at all: one retrieve() for the top 5, then one call to the model with those quotes as its only context. It does not depend on a small model choosing the right tool, which the comment in profile.py warns it sometimes will not. Module 5 compares the brains. Press Ctrl+C in the second terminal. The directory stays on disk, and a Python cell can open it the way the service does, with the same build_store() and the same retrieve():

**`step_01_install_the_lane_once(session)` — The Rs 0 lane: the notice-period question, with citations / Install the lane, once**

The lane gets a venv of its own, ~/rag-local-venv. Its packages are the chat service's, LangChain, LangGraph, Chroma and the Ollama client among them, installed on top of the service's image pins as services/chat/requirements-local.txt asks. Keeping them out of ~/rag-shell-venv leaves the operator pins exactly where rag_check_python_dependencies expects them, and every later session runs that check; the kit's CI keeps the chat service's pins in a venv of their own for the same reason. Then Ollama pulls the model, once.

Operation: bash — run once, in a second terminal, which the lane will keep: its own venv and its model.

**`step_02_start_the_lane(session)` — The Rs 0 lane: the notice-period question, with citations / Start the lane**

Start it in the second terminal, so the first stays free for questions. One line in this block matters more than it looks. The recipe seeds from the kit's root and serves from services/chat, and the store's default path, ./documind_chroma, is relative, so the two commands would open two different directories: the service would find an empty store and answer local corpus is empty. Exporting one absolute path as DOCUMIND_CHROMA_DIR gives both commands the same directory.

Operation: bash — run in the second terminal, and leave it running.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/chat_local.txt]
```

**`step_03_ask_it(session)` — The Rs 0 lane: the notice-period question, with citations / Ask it**

From the first terminal. The health check first: it names the profile, and the brains this service can run.

Operation: bash — run in the first terminal, while the lane serves.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/chat_health.txt]
```

**`step_04_ask_it(session)` — The Rs 0 lane: the notice-period question, with citations / Ask it**

From the first terminal. The health check first: it names the profile, and the brains this service can run. The service has 4 brains (langchain, langgraph, adk and direct), and langchain is the default: a tool loop in which the model decides when to search. This lesson asks the direct brain, which has no loop at all: one retrieve() for the top 5, then one call to the model with those quotes as its only context. It does not depend on a small model choosing the right tool, which the comment in profile.py warns it sometimes will not. Module 5 compares the brains.

Operation: bash — run in the first terminal: the notice-period question, through the direct brain.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/chat_answer.txt]
```

**`step_05_stop_the_lane_then_read_the_store_directly(session)` — The Rs 0 lane: the notice-period question, with citations / Stop the lane, then read the store directly**

Press Ctrl+C in the second terminal. The directory stays on disk, and a Python cell can open it the way the service does, with the same build_store() and the same retrieve():

Operation: bash — run in the first terminal after Ctrl+C has stopped the lane: read the store directly.

Expected shape, not a promised result:

```text
1628 chunks in the collection documind_dev
NP-03: gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md | page 1 | NP-03 — Notice period
answerable True | confidence high
1.000  acme:hr_policy_2026#NP-03                 page 1
0.601  acme:osh_code_2020#p36-0                  page 36
0.586  acme:cgst_act_2017#p160-0                 page 160
0.580  acme:maternity_benefit_act_1961#p6-1      page 6
0.579  acme:cgst_act_2017#p159-0                 page 159
NP-03 — Notice period
A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs
from the date the resignation is acknowledged in writing. Unused earned leave may not be
set off against the notice period.
```

### demo_05_prove_a_first_success_make_dryrun.py

Run it

**`step_01_prove_a_first_success_make_dryrun(session)` — Prove a first success: make dryrun / Run it**

Run it

Operation: bash — run in the first terminal, in the operator venv.

Expected shape, not a promised result:

```text
kit-only checkout: no curriculum notebooks under Module */ - nothing to extract or check; deploy/ here IS the extracted tree

  DocuMind AI — Tier-A offline dry run
  ------------------------------------------------------------
  [SKIP] extract       kit-only checkout (the learner repo): deploy/ is the extracted tree, nothing to compare  (Ns)
  [PASS] py_compile    125 python files parse  (Ns)
  [PASS] imports       all local imports resolve  (Ns)
  [PASS] shared-deps   every google.cloud client a shared module opens is pinned by its importers  (Ns)
  [PASS] requirements  11 files, all deps pinned  (Ns)
  [PASS] pins          30 shared packages agree across 12 files  (Ns)
  [PASS] dockerfile    11 services have a Dockerfile  (Ns)
  [WARN] copy-paths    10 of 11 Dockerfiles resolve; needs a later lesson's artefact: slm: build/ (11.4's make deploy-slm writes services/slm/build/ (the GGUF and the Modelfile the image copies); gitignored, so absent in a fresh checkout)  (Ns)
  [SKIP] terraform     terraform not on PATH (CI runs it)  (Ns)
  [SKIP] tflint        tflint not on PATH (optional)  (Ns)
  [SKIP] docker        docker not on PATH (CI builds images)  (Ns)
  ------------------------------------------------------------
  6 pass · 1 warn · 0 fail · 4 skip · Ns

== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [PASS] falsifiable
  [PASS] anchors
  [PASS] coverage

  The golden set is sound. It can go red, and it still contains the rows that would.
```

### demo_06_diagnose_a_first_failure_one_loosened_row.py

The most common way an eval suite rots, made on purpose, caught, read and repaired. Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. One line changed: the row's must_contain went from ["60"] to []. Now run the gate. Repair it

**`step_01_diagnose_a_first_failure_one_loosened_row(session)` — Diagnose a first failure: one loosened row / Diagnose a first failure: one loosened row**

The most common way an eval suite rots, made on purpose, caught, read and repaired. Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone:

Operation: bash — run in the first terminal: loosen lk-06 in your clone (or delete the 60 by hand in an editor).

Expected shape, not a promised result:

```text
lk-06 must_contain before: ['60']
lk-06 must_contain after:  []
```

**`step_02_diagnose_a_first_failure_one_loosened_row(session)` — Diagnose a first failure: one loosened row / Diagnose a first failure: one loosened row**

Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled.

Operation: bash — run in the first terminal.

Expected shape, not a promised result:

```text
diff --git a/evals/golden.jsonl b/evals/golden.jsonl
index 50b46d6..e2d97fb 100644
--- a/evals/golden.jsonl
+++ b/evals/golden.jsonl
@@ -6 +6 @@
-{"id": "lk-06", "shape": "lookup", "question": "What is the notice period for a confirmed E3?", "tenant": "acme", "must_contain": ["60"], "must_retrieve": ["NP-03", "hr_policy_2026"], "answerable": true}
+{"id": "lk-06", "shape": "lookup", "question": "What is the notice period for a confirmed E3?", "tenant": "acme", "must_contain": [], "must_retrieve": ["NP-03", "hr_policy_2026"], "answerable": true}
```

**`step_03_diagnose_a_first_failure_one_loosened_row(session)` — Diagnose a first failure: one loosened row / Diagnose a first failure: one loosened row**

Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. One line changed: the row's must_contain went from ["60"] to []. Now run the gate.

Operation: bash — run in the first terminal.

Expected shape, not a promised result:

```text
kit-only checkout: no curriculum notebooks under Module */ - nothing to extract or check; deploy/ here IS the extracted tree

  DocuMind AI — Tier-A offline dry run
  ------------------------------------------------------------
  [SKIP] extract       kit-only checkout (the learner repo): deploy/ is the extracted tree, nothing to compare  (Ns)
  [PASS] py_compile    125 python files parse  (Ns)
  [PASS] imports       all local imports resolve  (Ns)
  [PASS] shared-deps   every google.cloud client a shared module opens is pinned by its importers  (Ns)
  [PASS] requirements  11 files, all deps pinned  (Ns)
  [PASS] pins          30 shared packages agree across 12 files  (Ns)
  [PASS] dockerfile    11 services have a Dockerfile  (Ns)
  [WARN] copy-paths    10 of 11 Dockerfiles resolve; needs a later lesson's artefact: slm: build/ (11.4's make deploy-slm writes services/slm/build/ (the GGUF and the Modelfile the image copies); gitignored, so absent in a fresh checkout)  (Ns)
  [SKIP] terraform     terraform not on PATH (CI runs it)  (Ns)
  [SKIP] tflint        tflint not on PATH (optional)  (Ns)
  [SKIP] docker        docker not on PATH (CI builds images)  (Ns)
  ------------------------------------------------------------
  6 pass · 1 warn · 0 fail · 4 skip · Ns

== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [FAIL] falsifiable
         lk-06: an answerable row with no must_contain accepts any answer at all
  [PASS] anchors
  [PASS] coverage

  1 problem(s). The golden set cannot judge the model until it judges itself.
```

**`step_04_repair_it(session)` — Diagnose a first failure: one loosened row / Repair it**

Repair it

Operation: bash — run in the first terminal: repair, check, run again.

Expected shape, not a promised result:

```text
== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [PASS] falsifiable
  [PASS] anchors
  [PASS] coverage

  The golden set is sound. It can go red, and it still contains the rows that would.
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_0.2_Local_Environment_WIX.html`. All 39 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `8085442943c65c12c22f9b8bcad6a06e9f4e71bc`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
