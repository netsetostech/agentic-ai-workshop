# Lesson 10.1 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.1-react/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild with the chat venv and check:

    <chat venv python> pagekit/build.py 10.1 && python pagekit/check_lesson.py 10.1 && python pagekit/audit_pages.py 10.1

Two runs are probes the lesson plan puts in earlier batches (section 6), because the page's claims rest on them: run 1
in batch 1 (Mon 26 - Wed 28 Oct, which thinking levels `gemini-3.6-flash` takes on `global`) and run 2 in batch 3
(Mon 16 - Wed 18 Nov, whether the stop sequence holds there with thinking on). The rest are the page's runs, in batch 4
(Mon 23 - Wed 25 Nov).

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and the chat service of Module 5
  deployed (step 3 uses its `langchain` and `adk` brains).
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API` and defines `tok`. Pass
  `REGION` to every `make agent-*` line: `commands/agent-turn.sh` builds rag-api's address from it, and the Makefile's
  default is `us-central1`.
- **The classes, once:** the bench's desk drops every passage with no class (`services/chat/desk_agent.py`, `_search()`),
  so run the page's setup line first. It costs no model call; it writes acme's and zeta's doc_type registries and
  relabels their stored rows (Firestore, the Vector Search restricts, BigQuery's `chunk_source`). zeta is in it because
  the calculator slice holds one zeta row (`calc-carry-forward-zeta`).

      for t in acme zeta; do make doc-types PROJECT="$PROJECT" TENANT=$t SEED=manifest APPLY=1; done

  An exit status of 3 means BigQuery deferred a statement: run it again later, as its last line says. A second run
  plans nothing.
- **The venv:** the first `make agent-turn` builds `~/graph-venv` with `services/chat/requirements.txt` (a few minutes).
  pip's own notices, if any, are not part of a recording.
- **What to record:** what each cell prints, as the run says (stdout and stderr together, unless the run says stdout),
  with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; home directory `/home/you`; your email
  `you@your-company.com`. None of the bench's outputs should carry the first two; `make agent-eval` prints the saved
  file's path, which carries your home directory. `check_lesson.py` refuses a real project id, a project number in a URL
  and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Batch | Time (an estimate) | Cost, from the kit's own counts (see below) |
|---|---|---|---|---|---|
| 1 | `data/turn_levels.txt` | 8, four thinking levels | 1 (probe) | a few minutes | 4 turns, 12 calls: Rs 4.63 before thinking, plus Rs 7.65 for each 1,000 thinking tokens a call |
| 2 | `data/turn_react.txt` | 8, prompted ReAct | 3 (probe) | about a minute | 1 turn: Rs 1.26 before thinking |
| 3 | `data/ui_chat.txt` | 3, the Chat page | 4 | a few minutes | 2 chat turns: each caption shows its rupees; the chat service stops a turn at Rs 5 |
| 4 | `data/turn_plan.txt` | 8, a plan first | 4 | about a minute | 1 turn: Rs 1.22 before thinking |
| 5 | `data/passages.txt` | 8, what a search returns | 4 | seconds | Rs 0: `/v1/passages` calls no model |
| 6 | `data/eval_patterns.txt` | 9, the 11 rows | 4 | several minutes | 33 turns, 99 calls: Rs 37.79 before thinking, plus Rs 63.11 for each 1,000 thinking tokens a call; the Meter's ceiling is Rs 5 a turn, Rs 165.00 for the run |
| 7 | `data/eval_paired.txt` | 9, paired, and each pattern's calls | 4 | seconds | Rs 0: the saved file |
| 8 | `data/passages_rows.txt` | 9, rag-api's rows | 4 | seconds | Rs 0: one Cloud Logging read |

**In all:** the 39 bench turns (runs 1, 2, 4 and 6) come to Rs 44.90 before thinking, and their thinking adds Rs 74.59
for every 1,000 thinking tokens a call, over 117 calls; batch 4's bench turns alone (runs 4 and 6) are Rs 39.01 before
thinking, plus Rs 65.02 for each 1,000 thinking tokens a call. The two chat turns of run 3 come on top, at the rupees
their captions show. The Meter's ceiling for the 39 turns is Rs 195.00 (Rs 5 a turn). The lesson plan's estimate for
batch 4 is Rs 40-60: batch 4's bench turns stay within Rs 60 while their calls spend about 322 thinking tokens a call or
fewer, and run 1 says how many the loop spends at `low`. Read the `thinking` figure on run 1's `low` lines before batch 4,
and price run 6 from it.

How the costs were computed (`build.py`, which prints them and names any figure this file no longer states): every
calculator row through every pattern on the kit's scripted model, offline, with no slip; each call's input and visible
tokens as the script counts them (four characters a token over what the call is sent and what it writes); plus, for
`loop` and `plan_first`, the tool declarations Gemini receives with every call, which the script does not count: the
desk's eight tools as `ChatGoogleGenerativeAI.bind_tools` converts them, about 1,131 tokens; priced at
`gemini-3.6-flash`'s USD 1.50 in and 7.50 out per million, at Rs 85 to the dollar (`shared/prices.py`). Thinking is
billed as output, Rs 0.6375 for every 1,000 tokens, and the script's own thinking counts are left out: only the lane
knows the model's. The searches cost nothing at rag-api.

The page's prose says what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/turn_levels.txt` (step 8; batch 1, the thinking-levels probe)

```bash
for t in minimal low medium high; do make agent-turn PROJECT="$PROJECT" REGION="$REGION" THINKING=$t 2>&1 | grep -E '^(  thinking:|model call|tokens:|figure check|the turn failed|make: )'; done | tee turn_levels.txt
```

Expect, for each level: `  thinking: <level>, sent with every call`; a `model call N (thinking <level>): in ..., thinking
..., visible ... tokens, Rs ...` line for each call (three on the clean path: search, calculator, answer; the model
decides); the `tokens:` totals line, `Rs ... for the model calls at list price, Rs 0.0000 for rag-api`; and `figure
check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)`.
A level the endpoint refuses shows `the turn failed: ...` and make's error line instead: record it, and tell the page's
editor, because steps 4, 8 and 10 name the four levels. The thinking counts are the model's: the page reads them, it
does not predict them.

### 2. `data/turn_react.txt` (step 8; batch 3, the stop-sequence probe)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=react_text 2>&1 | tee turn_react.txt
```

Expect the header with `react_text (lesson 10.1): prompted ReAct: no function declaration sent, ...`, then for each
call the `model call` line and the `Thought:` and `Action:` lines Gemini wrote, `-> code runs retrieve(...)` with the
passages, `-> code runs gratuity_estimate(...)` with `= Rs 2,40,000: ...`, a `Final Answer:` and `-> no tool: the Final
Answer is the answer`; then the answer with `Worked out in code:`, the totals line ending `N format errors; stopped by
nothing`, and the figure check. Two outcomes the page covers but cannot predict: a `cut by the parser` block (the
endpoint did not honour the stop sequence, and the cut kept the rest out) and format errors (Actions the parser could
not read, each answered with an Observation). Record whichever happened, and say so in the PR.

### 3. `data/ui_chat.txt` (step 3; batch 4)

In the browser, not a terminal: open `https://documind-ui-NUMBER.asia-south1.run.app`, the Chat page. Choose Brain
`langchain` and ask `I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?`; then choose
`adk` and ask it again. Record, for each, the brain's name on a line of its own, the answer as the page shows it, and
the caption line under it, for example:

```text
langchain
<the answer as shown>
brain: langchain · tools: retrieve · 5234 ms · Rs 0.85
adk
...
```

Expect `tools:` to name `retrieve` and no calculator, since the chat brains hold none. The figure each wrote is the
model's own: record it as it is, right or wrong; the page compares it with the calculator's Rs 2,40,000 and claims
neither.

### 4. `data/turn_plan.txt` (step 8; batch 4)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_first 2>&1 | tee turn_plan.txt
```

Expect `plan_first (lesson 10.1): the loop, its prompt led by an instruction to write a plan first: ...`, and on call 1,
when the model wrote its plan beside its first call, `the model wrote: Plan: ...` (or the plan's lines under `the model
wrote:`). If the model wrote only the plan and no call, the turn ends there with `-> no tool: the answer`: record it,
because step 8 names that outcome.

### 5. `data/passages.txt` (step 8; batch 4)

Run step 8's Python cell (it starts `import json, os, subprocess, urllib.request, warnings`) exactly as the page prints
it. Expect `answerable True | passages 5 | model none | cost_usd 0.0 | tokens 0 in, 0 out | pool N`, five lines of file
name, class and length, and the total characters. `passages 0` means acme's rows have no class: run the setup line.

### 6. `data/eval_patterns.txt` (step 9; batch 4): stdout only

```bash
make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop,react_text,plan_first SLICE=calc SAVE="$HOME/bench-101-lane.jsonl" > eval_patterns.txt
```

The progress lines (`  [i/11] <row> run 1: N model calls, Rs ...`) go to stderr and stay on the terminal: watch them,
and stop the run if a turn fails on every row. Expect `LIVE: gemini-3.6-flash on location global, and your lane's
rag-api | 11 rows, 3 arms, 1 run each, in this process (--inproc)`, `saved 33 runs to /home/you/bench-101-lane.jsonl:
--replay rescores them at Rs 0` (replace your home directory), then three blocks, `== loop, thinking default (low), desk
astar: 11 rows x 1 run` and the same for `react_text` and `plan_first`, each with its 11 rows, the `first runs:` rates
with their intervals, `a run:` and `in all:`. No paired block: three arms in one run print none, and run 7 pairs them.
Keep `~/bench-101-lane.jsonl` for run 7.

### 7. `data/eval_paired.txt` (step 9; batch 4)

Run step 9's paired cell exactly as the page prints it (`export SAVED="$HOME/bench-101-lane.jsonl"`, the Python
heredoc, then two `make agent-eval COMPARE=...` lines) and record everything it prints. Expect `33 runs in
~/bench-101-lane.jsonl`, one line a pattern (`react_text`'s ends with the replies that ran past the stop and the format
errors), then two blocks, `react_text` against `loop` and `plan_first` against `loop`, each with `paired (correct)` and
`paired (verified)`, Newcombe's interval, McNemar's p and the verdict against the margin registered on 2026-10-08.

### 8. `data/passages_rows.txt` (step 9; batch 4)

Run step 9's last Python cell (it starts `import json, os, subprocess, warnings` and reads Cloud Logging) within a day of
run 6. Expect a count of `passages` rows labelled brain `desk`, split by tenant (acme's and zeta's), `model ['none']`,
`tokens 0`, `cost_usd 0.0`, and `asked as ['documind-ui-sa']`.

When all eight are in, rebuild the page, and reword nothing the recordings confirm.
