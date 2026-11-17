# Lesson 10.2 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.2-plan-execute/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild with the chat venv and check:

    <chat venv python> pagekit/build.py 10.2 && python pagekit/check_lesson.py 10.2 && python pagekit/audit_pages.py 10.2

Runs 2 to 8 are the six commands of the kit's pull request (K-10.2, #132), written with the shell's variables, plus the
page's Rs 0 read of the saved runs; run 1 is the page's Chat page step. All are batch 4 (Mon 23 - Wed 25 Nov) in the
lesson plan's section 6. Run 2 is also the probe the plan puts in batch 3 (Mon 16 - Wed 18 Nov), plan-and-execute's
call count: run it then if you can, and again in batch 4 only if the kit changed. Run 9 is step 10's ADK planner
(`ADK_PLANNER`, the kit's K-P10 pull request), the one run that redeploys the chat service first.

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and the chat service of Module 5
  deployed (step 3 uses its `langchain` brain).
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API` and defines `tok`. Pass
  `REGION` to every `make agent-*` line: `commands/agent-turn.sh` builds rag-api's address from it, and the Makefile's
  default is `us-central1`.
- **The classes, once:** the bench's desk drops every passage with no class (`services/chat/desk_agent.py`,
  `_search()`). Lesson 10.1's setup line classes acme's stored rows; if it has not run on this lane, run the page's line
  first. It costs no model call. Every chained row is acme's.

      make doc-types PROJECT="$PROJECT" TENANT=acme SEED=manifest APPLY=1

  An exit status of 3 means BigQuery deferred a statement: run it again later, as its last line says. A second run
  plans nothing.
- **The venv:** the first `make agent-turn` builds `~/graph-venv` with `services/chat/requirements.txt` (a few minutes).
  pip's own notices, if any, are not part of a recording.
- **What to record:** what each run prints, as the run says (stdout and stderr together, unless the run says stdout),
  with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; home directory `/home/you`; your email
  `you@your-company.com`. None of the bench's outputs should carry the first two; `make agent-eval` prints the saved
  file's path, which carries your home directory. `check_lesson.py` refuses a real project id, a project number in a URL
  and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Batch | Time (an estimate) | Cost, from the kit's own counts (see below) |
|---|---|---|---|---|---|
| 1 | `data/ui_chat.txt` | 3, the Chat page | 4 | a minute | 1 chat turn: its caption shows its rupees; the chat service stops a turn at Rs 5 |
| 2 | `data/turn_plan_execute.txt` | 8, plan-and-execute | 3 (probe) or 4 | about a minute | 1 turn, 10 calls offline: Rs 3.64 before thinking, plus Rs 6.38 for each 1,000 thinking tokens a call |
| 3 | `data/turn_rewoo.txt` | 8, ReWOO | 4 | about a minute | 1 turn, 4 calls: Rs 1.76 before thinking, plus Rs 2.55 for each 1,000 thinking tokens a call |
| 4 | `data/turn_lite.txt` | 8, a flash-lite executor | 4 | about a minute | 1 turn, 8 calls: Rs 1.51 before thinking, plus Rs 2.04 for each 1,000 thinking tokens a call |
| 5 | `data/eval_plans.txt` | 9, the three patterns | 4 | several minutes | 9 turns, 58 calls: Rs 27.85 before thinking, plus Rs 36.98 for each 1,000 thinking tokens a call |
| 6 | `data/eval_lite.txt` | 9, a flash-lite executor | 4 | a few minutes | 6 turns, 37 calls: Rs 8.75 before thinking, plus Rs 11.35 for each 1,000 thinking tokens a call |
| 7 | `data/replay.txt` | 9, the saved runs rescored | 4 | seconds | Rs 0: the saved file |
| 8 | `data/plans_read.txt` | 9, the plans read back | 4 | seconds | Rs 0: the saved files |
| 9 | `data/adk_planner.txt` | 10, ADK's planner on the ADK brain | 4 | about 10 minutes (the redeploy) | Cloud Build for the chat image, then 2 ADK chat turns: at most Rs 10 (Rs 5 a turn) |

**In all:** the 18 bench turns (runs 2 to 6) come to Rs 43.50 before thinking over 117 calls, and their thinking adds
Rs 59.29 for every 1,000 thinking tokens a call. The chat turn of run 1 comes on top, at the rupees its caption shows,
and so do run 9's two ADK turns, at the rupees the cell prints (at most Rs 10).
The Meter's ceiling for the 18 turns is Rs 90.00 (Rs 5 a turn). The kit PR's estimate for these runs is Rs 45-65, with
a ceiling of about Rs 100; the lesson plan's for the lesson is Rs 60-90. They stay within Rs 65 while their calls spend
about 362 thinking tokens a call or fewer, and within Rs 100 at about 952 thinking tokens a call.

**The Rs 5 limit:** the Meter refuses every call once a turn has spent Rs 5, so a turn whose calls think enough never
makes its last call. A loop turn on a chained row reaches Rs 5 before its last call when its calls think
about 406 thinking tokens each, a plan-and-execute turn at about 398 thinking tokens a call, and a ReWOO turn only
at about 2177 thinking tokens a call. Lesson 10.1's run 1 (batch 1) measures the loop's
thinking at `low` on this model: read its `thinking` figures before batch 4. A stopped turn prints `stopped by
turn_budget` and the Meter's answer; it is a finding, not a failed run, so record it and say so in the PR.

How the costs were computed (`build.py`, which prints them and names any figure this file no longer states): every
chained row through every pattern, with both executors, on the kit's scripted models offline (a chained row never
slips, so an eval run is the single turn); each call's input and visible tokens as the script counts them (four
characters a token over what the call is sent and what it writes); plus, for the loop's calls and plan_execute's act
calls, the tool declarations Gemini receives with every call that binds the desk's tools, which the script does not
count: the desk's eight tools as `ChatGoogleGenerativeAI.bind_tools` converts them, about 1,131 tokens; each call priced
at its own model's rates from `shared/prices.py`, `gemini-3.6-flash` at USD 1.50 in and 7.50 out per million and
`gemini-3.1-flash-lite` at 0.25 and 1.50, at Rs 85 to the dollar. Thinking is billed as output, Rs 0.6375 for every
1,000 tokens on flash and Rs 0.1275 on flash-lite, and the script's own thinking counts are left out: only the lane
knows the model's. The searches cost nothing at rag-api (`/v1/passages` books no tokens and no cost).

The scripted planner takes the manager's cap on purpose, so the offline figures include one replan; a Gemini plan that
searches LV-07 first saves those three calls, and a plan that goes wrong elsewhere may cost a replan of its own.

The page's prose says what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui_chat.txt` (step 3; batch 4)

In the browser, not a terminal: open `https://documind-ui-NUMBER.asia-south1.run.app`, the Chat page. Choose Brain
`langchain` and ask the third chained row's question:

    I am a confirmed E3 employee at ACME on Rs 52,000 a month with 7 years 8 months of continuous service. My resignation was acknowledged in writing on 5 October 2026. I have 80 days of earned leave, and my manager says the encashment cap is 100 days. When does my notice end, how many leave days are encashed, and roughly what gratuity will I get?

Record the brain's name on a line of its own, the answer as the page shows it, and the caption line under it, for
example:

```text
langchain
<the answer as shown>
brain: langchain · tools: retrieve, retrieve, retrieve · 8410 ms · Rs 1.20
```

Expect `tools:` to name `retrieve` (each call in order) and no calculator, since the chat brains hold none. The figures
are the model's own, the encashment's cap included: record them as they are, right or wrong. The page holds them against
the calculators' 4 December 2026, 45 days and Rs 2,40,000, and claims neither way.

### 2. `data/turn_plan_execute.txt` (step 8; batch 3's probe, or batch 4)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_execute ROW=chained-exit-stated-cap 2>&1 | tee turn_plan_execute.txt
```

Expect the header with `plan_execute (lesson 10.2): plan-and-execute: ...` and `the planner: gemini-3.6-flash (plan,
replan and solve); the executor: gemini-3.6-flash (act; EXEC_MODEL= names another)`; then `model call 1 (plan,
gemini-3.6-flash, thinking low): ...` and `the plan:` with Gemini's numbered steps; `step N: ...` for each step, with its
act call, the tool and what it returned; `model call M (solve, ...)`; the answer with three figures; the totals with
`by role: ...` and `plans: N written, R replan(s) (at most 1 a turn)`; and the figure check. Outcomes the page covers
but cannot predict, any of which is a finding: a step that took `cap=100`, refused (`refused: refused: cap = 100 is not
written in LV-07 ...` and `the step was refused`) and then replanned (`after: Step N was refused: ...`); no refusal at
all, because the planner searched LV-07 first (`plans: 1 written, 0 replans`); `the plan: no numbered step`, a plan the
reader could not parse; `stopped by turn_budget` or `model_calls`. Record whichever happened, and say which in the PR.

### 3. `data/turn_rewoo.txt` (step 8; batch 4)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=rewoo ROW=chained-exit-e3 2>&1 | tee turn_rewoo.txt
```

Expect `the planner: gemini-3.6-flash (plan and solve); the executor: gemini-3.6-flash (extract; ...)`, `the plan,
written once:` with Gemini's `#E` lines, then either the waves (`wave 1: ...`, each extract's `= 60, quoting "..."` or
`refused: ...`, each filled placeholder's `run as ...`, any `never ran` line), the solve call and `waves: N (...)`, or
`refused before any tool ran: <why>` and the solver's answer. A search cut at its budget prints `failed: retrieve did not
answer within 25s and was abandoned`: a wave sends rag-api its searches at once, so if it happens, run the line once
more; if it happens again, record it and say so in the PR.

### 4. `data/turn_lite.txt` (step 8; batch 4)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_execute ROW=chained-exit-e3 EXEC_MODEL=gemini-3.1-flash-lite 2>&1 | tee turn_lite.txt
```

Expect `the executor: gemini-3.1-flash-lite (act; EXEC_MODEL= names another)`, each act call as `model call N (act,
gemini-3.1-flash-lite, thinking low)`, and `by role: ...; act K calls, Rs ... (gemini-3.1-flash-lite); ...`. Whether
flash-lite takes thinking `low` on location `global` is the run's own question: if it does not, the output is `the turn
failed: ...` and make's error line. Record it, and tell the page's editor, because step 8 names that outcome.

### 5. `data/eval_plans.txt` (step 9; batch 4): stdout only

```bash
make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop,plan_execute,rewoo SLICE=chained SAVE="$HOME/plans.jsonl" > eval_plans.txt
```

The progress lines (`  [i/3] <row> run 1: N model calls, Rs ...`) go to stderr and stay on the terminal. Expect `LIVE:
gemini-3.6-flash on location global, and your lane's rag-api | 3 rows, 3 arms, 1 run each, in this process (--inproc)`,
`saved 9 runs to /home/you/plans.jsonl: --replay rescores them at Rs 0` (replace your home directory), then three blocks,
`== loop, thinking default (low), desk astar: 3 rows x 1 run` and the same for `plan_execute` and `rewoo`, each with its
3 rows, the `first runs:` rates with their intervals, `a run:` and `in all:`; the two planning blocks add `by role, a
run: ...` and `the plans: ...`. No paired block: three arms in one run print none. Keep `~/plans.jsonl` for runs 7 and 8.

### 6. `data/eval_lite.txt` (step 9; batch 4): stdout only

```bash
make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=plan_execute,rewoo SLICE=chained EXEC_MODEL=gemini-3.1-flash-lite SAVE="$HOME/plans_lite.jsonl" > eval_lite.txt
```

Expect `LIVE: gemini-3.6-flash on location global, and your lane's rag-api; an executor on gemini-3.1-flash-lite | 3
rows, 2 arms, 1 run each, ...`, `saved 6 runs to /home/you/plans_lite.jsonl: ...`, two blocks named `..., executor
gemini-3.1-flash-lite: 3 rows x 1 run` with the act and the extract calls priced on flash-lite in `by role`, then the
paired block for the two arms, which ends `indicative: the task set's model-written rows, one run each`. Keep
`~/plans_lite.jsonl` for run 8.

### 7. `data/replay.txt` (step 9; batch 4)

```bash
make agent-eval REPLAY="$HOME/plans.jsonl" 2>&1 | tee replay.txt
```

Expect `replayed 9 saved runs of /home/you/plans.jsonl: rescored at Rs 0, no model call (they cost Rs ... when they
ran)`, then the same three blocks as run 5, scored again from the saved records.

### 8. `data/plans_read.txt` (step 9; batch 4)

Run step 9's last Python cell exactly as the page prints it (it starts `import json, os, warnings` and reads
`~/plans.jsonl` and `~/plans_lite.jsonl`) and record everything it prints. Expect `~/plans.jsonl: 9 runs` and `~/plans_lite.jsonl: 6 runs`, one line
a run with its calls and rupees and, for the two planning patterns, by role; under a run, a `replanned after: ...` line
for each replan, a `refused before any tool ran: ...` line for a plan the check refused, a `stopped by its limits ...`
line for a stopped turn, and ReWOO's `waves: ...`.

### 9. `data/adk_planner.txt` (step 10; batch 4)

The chat service must run an image built from this kit, which has `ADK_PLANNER` in `services/chat/brains.py`; if
documind-chat was deployed before the K-P10 pull request merged, the cell's first line redeploys it (Cloud Build, a few
minutes, no model call). Run step 10's second cell exactly as the page prints it: the `make build deploy-services`
line, the `export CHAT=...` line, then the Python cell, which asks the ADK brain the same question with the switch off,
sets `ADK_PLANNER=plan_react` on documind-chat (one env update, a new revision), asks again, and removes the variable
in a `finally`. Record everything the Python cell prints (the make line's own output is not part of the recording).
Expect two blocks of two lines, `ADK_PLANNER off: tool calls [...], N model calls, Rs ..., stopped by None` and the
answer, then the same for `on`, then `ADK_PLANNER removed from documind-chat again`. What the page waits to learn:
whether the `on` turn's `tool calls` still names `retrieve` (the planner's instruction asks for tool code as text under
`/*ACTION*/`), whether its answer starts `The model wrote a plan but no final answer` (a reply that was all plan), and
how many more model calls and rupees the written plan costs. Record them as they are; if the `on` turn calls no tool,
that is the finding, so say so in the PR.

When all nine are in, rebuild the page, and reword nothing the recordings confirm.
