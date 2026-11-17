# Lesson 10.10: Coding agents: a Ralph loop, an AI code reviewer and paper-to-code

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_one_iteration_by_hand.py](demo_03_one_iteration_by_hand.py) | One iteration by hand |
| 4 | [demo_04_the_oracle_weak_and_strong.py](demo_04_the_oracle_weak_and_strong.py) | The oracle, weak and strong |
| 5 | [demo_05_the_loop_offline_three_runs_two_caps_and_the_guards.py](demo_05_the_loop_offline_three_runs_two_caps_and_the_guards.py) | The loop offline: three runs, two caps and the guards |
| 6 | [demo_06_paper_to_code_the_same_function_from_the_statute_alone.py](demo_06_paper_to_code_the_same_function_from_the_statute_alone.py) | Paper-to-code: the same function from the statute alone |
| 7 | [demo_07_the_reviewer_a_linter_first_then_gemini_on_your_lane.py](demo_07_the_reviewer_a_linter_first_then_gemini_on_your_lane.py) | The reviewer: a linter first, then Gemini on your lane |
| 8 | [demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py](demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py) | The live loop: Gemini CLI in a container, on a model-only key |
| 9 | [demo_09_direct_reads_and_the_human_step.py](demo_09_direct_reads_and_the_human_step.py) | Direct reads, and the human step |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py](optional/demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py) — Optional, the author's run: the live loop on a model-only Gemini API key the author creates for the run and deletes after it, typed at the prompt and never echoed, under a rupee cap from the batch-1 dry run; then the reviewer on its patch. It bills that key's project. Without such a key, skip it: the page's recorded run shows what it does, and the required steps before it prove the loop refuses to start without one.
- [optional/demo_11_verify_it_yourself_the_checklist.py](optional/demo_11_verify_it_yourself_the_checklist.py) — Fifteen checks, each one step above, each with the value that proves it. Nothing on your lane is configured. The offline runs wrote run directories under /tmp, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_one_iteration_by_hand.py

Do it: the workspace The second cell plays iteration 1 the way a hurried agent might. It writes the kit's function with one line hard-coded, as seeds.json's placeholder has it. Then it runs the fast test that the prompt names, and asks both oracles about the workspace. Now write the body that spec.md describes, in $WS/shared/desk_calc.py, by hand or with a coding agent under your eye. Gemini CLI started in the workspace with no flags runs in its default approval mode: it asks before every edit and every command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. It loads the workspace's GEMINI.md, the loop's notes, which carry that name only inside a workspace: a Gemini CLI session opened in the kit itself never loads them. How Gemini CLI signs in on your machine is your own setup, and nothing else on this page uses it. Then run the fast test and check again.

**`step_01_the_workspace(session)` — One iteration by hand / Do it: the workspace**

Do it: the workspace

Operation: bash — run in the operator shell, in the kit (the workspace a loop starts from; offline, Rs 0).

Expected shape, not a promised result:

```text
ralph-workspace: task deadline (statutory_deadline written to an engineer's spec), the workspace a loop starts from
  /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace
  PROMPT.md, spec.md, fix_plan.md, GEMINI.md and oracle.md at its root; no oracle checks and no seeds in it; its git repository beside it, with no remote: git --git-dir=/tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log
  one iteration by hand: cd into it, run gemini in its default approval mode and ask it to follow PROMPT.md, approving or declining each edit and command; then make ralph-check WORKSPACE=<that path>
# Fix plan

One item an iteration: take the first unticked item, do it, then tick it ([x]). When oracle.md lists a failed check
that no item covers, add an unticked item for it at the end.

- [ ] Write statutory_deadline's body, as spec.md says
# The oracle's verdict: FAIL

The strong oracle, on the task as it starts, before any iteration. 10 of its 11 checks failed:

- desk_calc's own selftest: it stopped with NotImplementedError
- the four events s.17(2) counts from are taken, in any case and with spaces around them: statutory_deadline raised NotImplementedError on a question it must answer
- every day of 2026, for each event: the second working day after the last working day, Monday to Friday: 1,460 of 1,460 wrong
- a last working day given as a date is read as its ISO text: statutory_deadline raised NotImplementedError on a question it must answer
- an event s.17(2) does not count from is refused with CalcError: an event outside the four raised NotImplementedError, not CalcError
- a last working day not written YYYY-MM-DD is refused with CalcError: a last working day not written YYYY-MM-DD raised NotImplementedError, not CalcError
- the result: calculator statutory_deadline, the due date as YYYY-MM-DD text, unit date, not an estimate: statutory_deadline raised NotImplementedError on a question it must answer
- the result cites the Code on Wages, 2019, s.17(2) and s.17(3): statutory_deadline raised NotImplementedError on a question it must answer
- the formula shows the last working day, the event and the date due: statutory_deadline raised NotImplementedError on a question it must answer
- the notes say no holiday calendar is loaded, and that s.17(3) may set another time limit: statutory_deadline raised NotImplementedError on a question it must answer
def statutory_deadline(event: str, last_working_day) -> dict:
    """Code on Wages, 2019, s.17(2): wages are paid within two working days of a removal, dismissal, retrenchment or
    resignation. Counted from the person's last working day, as the case queue's exit clock counts it
    (cases.exit_flags), on working days Monday to Friday until a holiday calendar exists (cases.working_days_after)."""
    raise NotImplementedError("statutory_deadline has no body yet: spec.md says what it does")
```

**`step_02_iteration_1_in_a_hurry(session)` — One iteration by hand / Do it: iteration 1, in a hurry**

The second cell plays iteration 1 the way a hurried agent might. It writes the kit's function with one line hard-coded, as seeds.json's placeholder has it. Then it runs the fast test that the prompt names, and asks both oracles about the workspace.

Operation: bash — run in the operator shell, in the kit (iteration 1 in a hurry, then the oracles; Rs 0).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
wrote the body, with: due = date(2026, 10, 6)
ok    lakh is read, and a figure worked out in the head is not the calculator's
every rule says what its corpus line says, and the figures hold
ralph-check: the oracles on statutory_deadline in a change of shared/desk_calc.py (offline, Rs 0)
  the oracle runs the change's code on this machine, with the network and new processes refused inside Python: that is not a sandbox, so judge only a change you have read
  the workspace's change: /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/by-hand.patch (make review-diff DIFF= reads it)
  weak oracle (desk_calc's own selftest): PASS
  strong oracle: FAIL
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (1,448 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-10-06' given)
make: *** [mk/coding.mk:47: ralph-check] Error 1
```

**`step_03_iteration_1_done_properly(session)` — One iteration by hand / Do it: iteration 1, done properly**

Now write the body that spec.md describes, in $WS/shared/desk_calc.py, by hand or with a coding agent under your eye. Gemini CLI started in the workspace with no flags runs in its default approval mode: it asks before every edit and every command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. It loads the workspace's GEMINI.md, the loop's notes, which carry that name only inside a workspace: a Gemini CLI session opened in the kit itself never loads them. How Gemini CLI signs in on your machine is your own setup, and nothing else on this page uses it. Then run the fast test and check again.

Operation: bash — run in the operator shell, in the kit (after you write the body: the fast test, then the oracles).

Manual action: Write the body spec.md describes in $WS/shared/desk_calc.py (the workspace the first cell printed), replacing the hurried one: by hand, or with Gemini CLI started in the workspace with no flags, which asks before every edit and command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. Type done to run the fast test and both oracles: the strong one passes only for a body that does what spec.md says.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
every rule says what its corpus line says, and the figures hold
ralph-check: the oracles on statutory_deadline in a change of shared/desk_calc.py (offline, Rs 0)
  the oracle runs the change's code on this machine, with the network and new processes refused inside Python: that is not a sandbox, so judge only a change you have read
  the workspace's change: /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/by-hand.patch (make review-diff DIFF= reads it)
  weak oracle (desk_calc's own selftest): PASS
  strong oracle: PASS
```

### demo_04_the_oracle_weak_and_strong.py

With no arguments, make ralph-check judges all 8 versions under both oracles, and holds each verdict to the label seeds.json gives it. SHOW= adds one version's diff and its failed checks. The oracle's docstring names the change to try: delete the strong oracle's sweep over 2026. The cell copies oracle.py to a scratch directory without the sweep's two lines, then runs that copy on three versions, each spliced into the kit's own file as the loop does it.

**`step_01_the_oracle_weak_and_strong(session)` — The oracle, weak and strong / Do it**

With no arguments, make ralph-check judges all 8 versions under both oracles, and holds each verdict to the label seeds.json gives it. SHOW= adds one version's diff and its failed checks.

Operation: bash — run in the operator shell, in the kit (every version under both oracles, and one seed shown; Rs 0).

Expected shape, not a promised result:

```text
ralph-check: the oracles on statutory_deadline in a copy of shared/desk_calc.py, task deadline (offline, Rs 0)
  version               weak   strong  seeded defect
  the task              FAIL   FAIL    
  reference             PASS   PASS    
  placeholder           PASS   FAIL    placeholder
  calendar_days         FAIL   FAIL    calendar_days
  start_day_counted     FAIL   FAIL    off_by_one
  closure_counted       FAIL   FAIL    event_scope
  date_contract         PASS   FAIL    error_contract
  holiday_note_dropped  FAIL   FAIL    hidden_assumption

date_contract: day_of() re-written by hand: a date not written YYYY-MM-DD now raises Python's ValueError, which the Desk's tool does not turn into an error result (desk_agent._calc catches CalcError), so the person's turn fails instead of the model reading the refusal. The selftest never sends a bad date.
--- a/shared/desk_calc.py
+++ b/shared/desk_calc.py
@@ -353,7 +353,17 @@
     """Code on Wages, 2019, s.17(2): wages are paid within two working days of a removal, dismissal, retrenchment or
     resignation. Counted from the person's last working day, as the case queue's exit clock counts it
     (cases.exit_flags), on working days Monday to Friday until a holiday calendar exists (cases.working_days_after)."""
-    raise NotImplementedError("statutory_deadline has no body yet: spec.md says what it does")
+    ev = str(event or "").strip().lower()
+    if ev not in EXIT_EVENTS:
+        raise CalcError(f"event is one of {', '.join(EXIT_EVENTS)}: the events section 17(2) counts from")
+    start = date.fromisoformat(str(last_working_day).strip())
+    due = cases.working_days_after(start, WAGE_DAYS)
+    return _result("statutory_deadline", due.isoformat(), "date",
+                   f"last working day {start.isoformat()} ({start:%A}), after the {ev}, + {WAGE_DAYS} working days = "
+                   f"{due.isoformat()} ({due:%A})", ["wages_s17_2", "wages_s17_3"],
+                   notes=[NO_HOLIDAYS, "Counted from the last working day, the desk's reading of s.17(2), as its case "
+                                       "queue counts it.",
+                          "The appropriate Government may set another time limit (s.17(3))."])
 
 
 def threshold_check(headcount, rule: str = "grc") -> dict:

FAIL  a last working day not written YYYY-MM-DD is refused with CalcError: last_working_day '02/10/2026' raised ValueError
  the strong oracle fails 6 of 6 seeded defects; the weak one passes 2: placeholder, date_contract
  every verdict is the one commands/ralph/seeds.json labels it with
```

**`step_02_change_it_delete_the_sweep(session)` — The oracle, weak and strong / Change it: delete the sweep**

The oracle's docstring names the change to try: delete the strong oracle's sweep over 2026. The cell copies oracle.py to a scratch directory without the sweep's two lines, then runs that copy on three versions, each spliced into the kit's own file as the loop does it.

Operation: bash — run in the operator shell, in the kit (Change it: the strong oracle without its sweep; Rs 0).

Expected shape, not a promised result:

```text
the strong oracle with its sweep over 2026 deleted:
  placeholder    PASS, 10 checks
  reference      PASS, 10 checks
  calendar_days  FAIL, 10 checks: desk_calc's own selftest; the due date is never a Saturday or a Sunday
```

### demo_05_the_loop_offline_three_runs_two_caps_and_the_guards.py

Do it: the strong oracle, then the weak one Do it: a rupee cap The scripted agent can also misbehave on purpose: the kit's tests use that, and so does this page. Each row below is one iteration it played under the strong oracle when this page was built, and what summary.json recorded for it. Two rules cannot show in that table here. A symlink is undone: it is the first rule of inspect(), and the kit's tests make one where the system allows it. And only live, an agent's output that names github.com, githubusercontent.com or agents_workshop_learner undoes its iteration, because the oracle is public there and work that may have been copied is not kept. Then what the loop never does. It never writes inside the kit:

**`step_01_the_strong_oracle_then_the_weak_one(session)` — The loop offline: three runs, two caps and the guards / Do it: the strong oracle, then the weak one**

Do it: the strong oracle, then the weak one

Operation: bash — run in the operator shell, in the kit (the loop, scripted, under the strong oracle; Rs 0).

Expected shape, not a promised result:

```text
ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, strong oracle
  caps: 8 iterations, no rupee cap, 80 changed lines an iteration
  the run: /tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
  OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle FAIL (1 failed) | in 14,737 (cached 0), out 302, thinking 64 tokens, Rs 2.1123; spent Rs 2.1123
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (1,448 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-10-06' given)
iteration 2: item "Count the two working days from any last working day: the sweep over 2026 failed" | 2 lines changed | oracle FAIL (3 failed) | in 14,613 (cached 0), out 306, thinking 64 tokens, Rs 2.0990; spent Rs 4.2113
    FAIL  desk_calc's own selftest (1 of 79 lines failed)
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (628 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-01-03' given)
    FAIL  the due date is never a Saturday or a Sunday (105 last working days of 2026 gave a Saturday or a Sunday)
iteration 3: item "Skip Saturdays and Sundays: the due date fell on a weekend" | 2 lines changed | oracle PASS | in 14,695 (cached 0), out 309, thinking 64 tokens, Rs 2.1114; spent Rs 6.3227
stopped: the strong oracle passed after 3 iterations
  spent: Rs 6.3227 at list price for the script's tokens (nothing is billed)
  for the record, not used by the loop: the weak oracle on the same code: PASS
  /tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/ralph.patch: the loop's work (12 lines)
  /tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/kit.patch: its statutory_deadline against the kit's: identical to the kit's own, byte for byte
  /tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/summary.json; the commits: git --git-dir=/tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log --oneline
  nothing was applied to your clone and nothing was pushed: applying kit.patch is yours to decide
```

**`step_02_the_strong_oracle_then_the_weak_one(session)` — The loop offline: three runs, two caps and the guards / Do it: the strong oracle, then the weak one**

Do it: the strong oracle, then the weak one

Operation: bash — run in the operator shell, in the kit (the same script under the weak oracle; Rs 0).

Expected shape, not a promised result:

```text
ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, weak oracle
  caps: 8 iterations, no rupee cap, 80 changed lines an iteration
  the run: /tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
  OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle PASS | in 14,398 (cached 0), out 302, thinking 64 tokens, Rs 2.0691; spent Rs 2.0691
stopped: the weak oracle passed after 1 iteration
  spent: Rs 2.0691 at list price for the script's tokens (nothing is billed)
  for the record, not used by the loop: the strong oracle on the same code: FAIL
  /tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/ralph.patch: the loop's work (12 lines)
  /tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/kit.patch: its statutory_deadline against the kit's: 2 lines differ from the kit's own
  /tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/summary.json; the commits: git --git-dir=/tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log --oneline
  nothing was applied to your clone and nothing was pushed: applying kit.patch is yours to decide
```

**`step_03_a_rupee_cap(session)` — The loop offline: three runs, two caps and the guards / Do it: a rupee cap**

Do it: a rupee cap

Operation: bash — run in the operator shell, in the kit (the same script under a rupee cap; nothing is billed).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, strong oracle
  caps: 8 iterations, Rs 5, 80 changed lines an iteration
  the run: /tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
  OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle FAIL (1 failed) | in 14,737 (cached 0), out 302, thinking 64 tokens, Rs 2.1123; spent Rs 2.1123
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (1,448 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-10-06' given)
iteration 2: item "Count the two working days from any last working day: the sweep over 2026 failed" | 2 lines changed | oracle FAIL (3 failed) | in 14,613 (cached 0), out 306, thinking 64 tokens, Rs 2.0990; spent Rs 4.2113
    FAIL  desk_calc's own selftest (1 of 79 lines failed)
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (628 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-01-03' given)
    FAIL  the due date is never a Saturday or a Sunday (105 last working days of 2026 gave a Saturday or a Sunday)
stopped: Rs 4.2113 spent; one more iteration at the dearest so far (Rs 2.1123) would pass the cap of Rs 5
  spent: Rs 4.2113 at list price for the script's tokens (nothing is billed)
  /tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/ralph.patch: the loop's work (12 lines)
  /tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/kit.patch: its statutory_deadline against the kit's: 2 lines differ from the kit's own
  /tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/summary.json; the commits: git --git-dir=/tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log --oneline
  nothing was applied to your clone and nothing was pushed: applying kit.patch is yours to decide
make: *** [mk/coding.mk:33: ralph] Error 1
```

**`step_04_the_guards_undone_flagged_never(session)` — The loop offline: three runs, two caps and the guards / The guards: undone, flagged, never**

The scripted agent can also misbehave on purpose: the kit's tests use that, and so does this page. Each row below is one iteration it played under the strong oracle when this page was built, and what summary.json recorded for it. Two rules cannot show in that table here. A symlink is undone: it is the first rule of inspect(), and the kit's tests make one where the system allows it. And only live, an agent's output that names github.com, githubusercontent.com or agents_workshop_learner undoes its iteration, because the oracle is public there and work that may have been copied is not kept. Then what the loop never does. It never writes inside the kit:

Operation: bash — run in the operator shell, in the kit (where the loop will not write).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
ERROR: /home/you/deploy_module_rag is inside the kit: the loop never writes there. Give OUT= a directory outside it
make: *** [mk/coding.mk:33: ralph] Error 2
```

### demo_06_paper_to_code_the_same_function_from_the_statute_alone.py

Do it

**`step_01_paper_to_code_the_same_function_from_the_s(session)` — Paper-to-code: the same function from the statute alone / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (paper-to-code, scripted; Rs 0).

Expected shape, not a promised result:

```text
ralph: task statute (statutory_deadline from the statute alone (paper-to-code)), agent scripted, strong oracle
  caps: 8 iterations, no rupee cap, 80 changed lines an iteration
  the run: /tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX
  OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
iteration 1: item "Write statutory_deadline's body, as spec.md says" | 16 lines changed | oracle FAIL (2 failed) | in 14,496 (cached 0), out 312, thinking 64 tokens, Rs 2.0879; spent Rs 2.0879
    FAIL  desk_calc's own selftest (1 of 79 lines failed)
    FAIL  an event s.17(2) does not count from is refused with CalcError (event 'closure' returned a result)
iteration 2: item "Refuse closure with CalcError: an event outside the four was taken" | 2 lines changed | oracle PASS | in 14,472 (cached 0), out 309, thinking 64 tokens, Rs 2.0830; spent Rs 4.1709
stopped: the strong oracle passed after 2 iterations
  spent: Rs 4.1709 at list price for the script's tokens (nothing is billed)
  for the record, not used by the loop: the weak oracle on the same code: PASS
  /tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX/ralph.patch: the loop's work (16 lines)
  /tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX/kit.patch: its statutory_deadline against the kit's: identical to the kit's own, byte for byte
  /tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX/summary.json; the commits: git --git-dir=/tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log --oneline
  nothing was applied to your clone and nothing was pushed: applying kit.patch is yours to decide
```

### demo_07_the_reviewer_a_linter_first_then_gemini_on_your_lane.py

Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3. With PROJECT, make review-eval reviews the seven diffs with gemini-3.6-flash on location global, thinking low. It runs as you: a review reads a diff and calls no tool, so it uses your own sign-in, unlike the loop's agent. REPEAT=3 reviews each diff three times, because a model's review differs from run to run. That is 21 calls, about Rs 5.48 of input (each request is 2,042 to 2,054 tokens by the kit's four-characters-a-token count), plus output and thinking, which the kit does not cap. REPEAT=1 costs a third. SAVE keeps every finding with the model and the date, and make review-eval FROM= with that file rescores it at Rs 0.

**`step_01_the_linter_offline(session)` — The reviewer: a linter first, then Gemini on your lane / Do it: the linter, offline**

Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3.

Operation: bash — run in the operator shell, in the kit (the linter in the reviewer's seat, on the seven diffs; Rs 0).

Expected shape, not a promised result:

```text
review-eval: a linter (offline: regular expressions, not a model)
  7 diffs from the Ralph task's start: the kit's own statutory_deadline (no defect) and 6 seeded with one defect each; each reviewed 1 time
  diff                  seeded rule         found   near   false alarms
  reference             (none)              -       -      1 (wrong_citation)
  placeholder           placeholder         1/1     1/1    1 (wrong_citation)
  calendar_days         calendar_days       1/1     1/1    1 (wrong_citation)
  start_day_counted     off_by_one          0/1     0/1    1 (wrong_citation)
  closure_counted       event_scope         1/1     1/1    1 (wrong_citation)
  date_contract         error_contract      1/1     1/1    1 (wrong_citation)
  holiday_note_dropped  hidden_assumption   1/1     1/1    1 (wrong_citation)
  catch count: 5.0 of 6 seeded defects a run (each run: 5); false alarms a run: 7
  7 reviews, 0 failed; Rs 0.0000 (no model: nothing is billed)
```

**`step_02_the_linter_offline(session)` — The reviewer: a linter first, then Gemini on your lane / Do it: the linter, offline**

Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3.

Operation: bash — run in the operator shell, in the kit (the linter on your hand iteration's diff; Rs 0).

Expected shape, not a promised result:

```text
review-diff: by-hand.patch, by a linter (offline: regular expressions, not a model)
  line 363: wrong_citation - s.17(3) is cited, but the deadline is s.17(2)'s
  1 finding; Rs 0.0000
```

**`step_03_gemini_on_your_lane(session)` — The reviewer: a linter first, then Gemini on your lane / Do it: Gemini, on your lane**

With PROJECT, make review-eval reviews the seven diffs with gemini-3.6-flash on location global, thinking low. It runs as you: a review reads a diff and calls no tool, so it uses your own sign-in, unlike the loop's agent. REPEAT=3 reviews each diff three times, because a model's review differs from run to run. That is 21 calls, about Rs 5.48 of input (each request is 2,042 to 2,054 tokens by the kit's four-characters-a-token count), plus output and thinking, which the kit does not cap. REPEAT=1 costs a third. SAVE keeps every finding with the model and the date, and make review-eval FROM= with that file rescores it at Rs 0.

Operation: bash — run in the operator shell, in the kit (Gemini on your lane: 21 calls; REPEAT=1 makes it 7).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/review_eval.txt]
```

### demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py

DRY_RUN=1 prints the two docker run lines an iteration would run, and starts nothing: no Docker, image or key is needed. By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. The kit's tests run the proxy on your machine's loopback, with a stand-in in place of the model endpoint, and the loop against a stub Docker. A live Docker is the author's check. make ralph-probe RALPH_EGRESS=proxy needs no key and makes no model call. From inside the agent's container it tries example.com and 169.254.169.254, the metadata server's address, directly, then example.com and the model endpoint through the proxy. It also prints whether example.com's name resolved there: whether a name lookup leaves the internal network is Docker's to decide, not the proxy's. Without the author's cap and key, the live loop does not start. It has no default spend, and it runs only on a model-only key, never on your gcloud login or Application Default Credentials.

**`step_01_the_two_containers_printed(session)` — The live loop: Gemini CLI in a container, on a model-only key / Do it: the two containers, printed**

DRY_RUN=1 prints the two docker run lines an iteration would run, and starts nothing: no Docker, image or key is needed.

Operation: bash — run in the operator shell, in the kit (the live loop's two containers, printed; nothing starts).

Expected shape, not a promised result:

```text
ralph --dry-run: the two containers an iteration runs, and nothing else; nothing is started
  the agent: docker run --rm --init --name ralph-<run>-01 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp --memory 2g --pids-limit 256 --cpus 2 --user UID:GID --env-file <run>/agent.env --env RALPH_MODEL=gemini-3.6-flash --env HOME=/tmp --mount type=bind,source=<run>/workspace,target=/work --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/PROMPT.md,target=/ralph/PROMPT.md,readonly --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/settings.json,target=/etc/gemini-cli/settings.json,readonly --workdir /work documind-ralph ralph-iteration
    its --env-file, 0600, deleted when the iteration ends: GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI (values never printed)
  the oracle: docker run --rm --network none --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m --user UID:GID --mount type=bind,source=<run>/oracle/01,target=/oracle/kit,readonly --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph,target=/oracle/check,readonly documind-ralph python3 -I -B -X utf8 /oracle/check/oracle.py --kit /oracle/kit --mode strong --json
```

**`step_02_the_egress_proxy_printed(session)` — The live loop: Gemini CLI in a container, on a model-only key / Do it: the egress proxy, printed**

By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY.

Operation: bash — run in the operator shell, in the kit (the same, behind the egress proxy; nothing starts).

Expected shape, not a promised result:

```text
ralph --dry-run: an iteration's network and three containers, the proxy, the agent and the oracle, and nothing else; nothing is started
  first, RALPH_EGRESS=proxy: the agent's internal network, and the proxy that opens a tunnel to aiplatform.googleapis.com:443 alone:
    docker network create --internal ralph-<run>-01-net
    docker run -d --name ralph-<run>-01-egress --network bridge --read-only --cap-drop ALL --security-opt no-new-privileges --memory 256m --pids-limit 128 --user UID:GID --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/egress.py,target=/egress/egress.py,readonly documind-ralph python3 -I -B -u /egress/egress.py --listen 0.0.0.0:3128 --allow aiplatform.googleapis.com:443
    docker network connect --alias egress ralph-<run>-01-net ralph-<run>-01-egress
  the agent: docker run --rm --init --name ralph-<run>-01 --network ralph-<run>-01-net --env HTTPS_PROXY=http://egress:3128 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp --memory 2g --pids-limit 256 --cpus 2 --user UID:GID --env-file <run>/agent.env --env RALPH_MODEL=gemini-3.6-flash --env HOME=/tmp --mount type=bind,source=<run>/workspace,target=/work --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/PROMPT.md,target=/ralph/PROMPT.md,readonly --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/settings.json,target=/etc/gemini-cli/settings.json,readonly --workdir /work documind-ralph ralph-iteration
    its --env-file, 0600, deleted when the iteration ends: GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI (values never printed)
  then, whatever happened: the proxy's log, kept as iterations/01-egress.txt, and the proxy and the network removed:
    docker logs ralph-<run>-01-egress
    docker rm -f ralph-<run>-01-egress
    docker network rm ralph-<run>-01-net
  the oracle: docker run --rm --network none --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m --user UID:GID --mount type=bind,source=<run>/oracle/01,target=/oracle/kit,readonly --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph,target=/oracle/check,readonly documind-ralph python3 -I -B -X utf8 /oracle/check/oracle.py --kit /oracle/kit --mode strong --json
```

**`step_03_the_egress_proxy_printed(session)` — The live loop: Gemini CLI in a container, on a model-only key / Do it: the egress proxy, printed**

By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. The kit's tests run the proxy on your machine's loopback, with a stand-in in place of the model endpoint, and the loop against a stub Docker. A live Docker is the author's check. make ralph-probe RALPH_EGRESS=proxy needs no key and makes no model call. From inside the agent's container it tries example.com and 169.254.169.254, the metadata server's address, directly, then example.com and the model endpoint through the proxy. It also prints whether example.com's name resolved there: whether a name lookup leaves the internal network is Docker's to decide, not the proxy's.

Operation: bash — the author's run, in Cloud Shell (batch 4): the egress proxy on a live docker.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/isolation.txt]
```

**`step_04_the_live_loop_on_your_lane(session)` — The live loop: Gemini CLI in a container, on a model-only key / Do it: the live loop on your lane**

Without the author's cap and key, the live loop does not start. It has no default spend, and it runs only on a model-only key, never on your gcloud login or Application Default Credentials.

Operation: bash — run in the operator shell, in the kit (the live loop without the author's cap or key).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
ERROR: the live loop has no default spend: give it RALPH_BUDGET_INR=<cap>, set from a dry run (make ralph RALPH_MAX_ITERS=1 RALPH_BUDGET_INR=<a small cap> reads one iteration's rupees)
make: *** [mk/coding.mk:33: ralph] Error 2
ERROR: RALPH_API_KEY is not set: the live loop runs only on a model-only credential the author creates for the run and deletes after it, never on your gcloud login or ADC
make: *** [mk/coding.mk:33: ralph] Error 2
```

### optional/demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.py

Optional, the author's run: the live loop on a model-only Gemini API key the author creates for the run and deletes after it, typed at the prompt and never echoed, under a rupee cap from the batch-1 dry run; then the reviewer on its patch. It bills that key's project. Without such a key, skip it: the page's recorded run shows what it does, and the required steps before it prove the loop refuses to start without one.

**`step_01_the_author_s_run(session)` — The live loop: Gemini CLI in a container, on a model-only key / The author's run**

The author ran the loop in Cloud Shell, which has Docker, with the image built in the same session (Cloud Shell's Docker storage does not outlive it). The cap came from a one-iteration dry run in batch 1. If the probe finds the key needs a project, RALPH_PROJECT adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's environment.

Operation: bash — the author's run, on the author's lane, in Cloud Shell (batch 4): yours refuses, as above.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ralph_loop.txt]
```

**`step_02_the_author_s_run(session)` — The live loop: Gemini CLI in a container, on a model-only key / The author's run**

The author ran the loop in Cloud Shell, which has Docker, with the image built in the same session (Cloud Shell's Docker storage does not outlive it). The cap came from a one-iteration dry run in batch 1. If the probe finds the key needs a project, RALPH_PROJECT adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's environment. Then the reviewer, on the loop's own work:

Operation: bash — the author's run (batch 4): the reviewer on the live loop's work.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/review_diff.txt]
```

### demo_09_direct_reads_and_the_human_step.py

Do it: the record The loop's last word is kit.patch: its function against the kit's own. Applying it is yours to decide. You apply it in your clone, run the fast test, put the file back, and ask the strong oracle about the same patch. The cell does this with the weak run's kit.patch from step 5.

**`step_01_the_record(session)` — Direct reads, and the human step / Do it: the record**

Do it: the record

Operation: bash — run in the operator shell, in the kit (the strong run's record, read straight from its files).

Expected shape, not a promised result:

```text
the task: statutory_deadline written to an engineer's spec
iteration 1: strong oracle FAIL (1 failed)
iteration 2: strong oracle FAIL (3 failed)
iteration 3: strong oracle PASS
# Fix plan

One item an iteration: take the first unticked item, do it, then tick it ([x]). When oracle.md lists a failed check
that no item covers, add an unticked item for it at the end.

- [x] Write statutory_deadline's body, as spec.md says
- [x] Count the two working days from any last working day: the sweep over 2026 failed
- [x] Skip Saturdays and Sundays: the due date fell on a weekend
## Learned
- python3 shared/desk_calc.py --selftest: the fast test; it stops at statutory_deadline until the body is written
diff --git a/shared/desk_calc.py b/shared/desk_calc.py
index 4eebbfb..2da7e42 100644
--- a/shared/desk_calc.py
+++ b/shared/desk_calc.py
@@ -353,7 +353,17 @@ def statutory_deadline(event: str, last_working_day) -> dict:
     """Code on Wages, 2019, s.17(2): wages are paid within two working days of a removal, dismissal, retrenchment or
     resignation. Counted from the person's last working day, as the case queue's exit clock counts it
     (cases.exit_flags), on working days Monday to Friday until a holiday calendar exists (cases.working_days_after)."""
-    raise NotImplementedError("statutory_deadline has no body yet: spec.md says what it does")
+    ev = str(event or "").strip().lower()
+    if ev not in EXIT_EVENTS:
+        raise CalcError(f"event is one of {', '.join(EXIT_EVENTS)}: the events section 17(2) counts from")
+    start = day_of(last_working_day, "last_working_day")
+    due = cases.working_days_after(start, WAGE_DAYS)
+    return _result("statutory_deadline", due.isoformat(), "date",
+                   f"last working day {start.isoformat()} ({start:%A}), after the {ev}, + {WAGE_DAYS} working days = "
+                   f"{due.isoformat()} ({due:%A})", ["wages_s17_2", "wages_s17_3"],
+                   notes=[NO_HOLIDAYS, "Counted from the last working day, the desk's reading of s.17(2), as its case "
+                                       "queue counts it.",
+                          "The appropriate Government may set another time limit (s.17(3))."])
 
 
 def threshold_check(headcount, rule: str = "grc") -> dict:
```

**`step_02_the_record(session)` — Direct reads, and the human step / Do it: the record**

Do it: the record

Operation: bash — run in the operator shell, in the kit (summary.json, the same run).

Expected shape, not a promised result:

```text
task deadline, agent scripted, strong oracle: stopped by oracle_passed; Rs 6.3227, billed False
  1. FAIL   12 lines, 1 failed | in 14,737, cached 0, out 302, thinking 64 | Write statutory_deadline's body, as spec.md says
  2. FAIL    2 lines, 3 failed | in 14,613, cached 0, out 306, thinking 64 | Count the two working days from any last working day: the sweep over 2026 failed
  3. PASS    2 lines, 0 failed | in 14,695, cached 0, out 309, thinking 64 | Skip Saturdays and Sundays: the due date fell on a weekend
the other oracle on the same code: PASS
kit.patch: identical to the kit's own, byte for byte
```

**`step_03_the_human_step(session)` — Direct reads, and the human step / Do it: the human step**

The loop's last word is kit.patch: its function against the kit's own. Applying it is yours to decide. You apply it in your clone, run the fast test, put the file back, and ask the strong oracle about the same patch. The cell does this with the weak run's kit.patch from step 5.

Operation: bash — run in the operator shell, in the kit (the human step, on the weak run's kit.patch).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
--- a/shared/desk_calc.py
+++ b/shared/desk_calc.py
@@ -357,7 +357,7 @@
     if ev not in EXIT_EVENTS:
         raise CalcError(f"event is one of {', '.join(EXIT_EVENTS)}: the events section 17(2) counts from")
     start = day_of(last_working_day, "last_working_day")
-    due = cases.working_days_after(start, WAGE_DAYS)
+    due = date(2026, 10, 6)
     return _result("statutory_deadline", due.isoformat(), "date",
                    f"last working day {start.isoformat()} ({start:%A}), after the {ev}, + {WAGE_DAYS} working days = "
                    f"{due.isoformat()} ({due:%A})", ["wages_s17_2", "wages_s17_3"],
every rule says what its corpus line says, and the figures hold
ralph-check: the oracles on statutory_deadline in a change of shared/desk_calc.py (offline, Rs 0)
  the oracle runs the change's code on this machine, with the network and new processes refused inside Python: that is not a sandbox, so judge only a change you have read
  kit.patch applies to the kit's own file
  weak oracle (desk_calc's own selftest): PASS
  strong oracle: FAIL
    FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (1,448 of 1,460 wrong; the first: removal on 2026-01-01 (Thursday): 2026-01-05 due, '2026-10-06' given)
make: *** [mk/coding.mk:47: ralph-check] Error 1
```

### optional/demo_11_verify_it_yourself_the_checklist.py

Fifteen checks, each one step above, each with the value that proves it. Nothing on your lane is configured. The offline runs wrote run directories under /tmp, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

**`step_01_verify_it_yourself_the_checklist(session)` — Verify it yourself: the checklist / Verify it yourself: the checklist**

Fifteen checks, each one step above, each with the value that proves it. Nothing on your lane is configured. The offline runs wrote run directories under /tmp, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

Operation: bash — run in the operator shell (optional: the run directories this page made).

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.10_Coding_Agents_WIX.html`. All 82 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `a2ff7a373b29baf3d62e995523935a1c8d9326ff`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
