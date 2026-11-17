# Lesson 10.3 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.3-critic-refiner/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild with the chat venv and check:

    <chat venv python> pagekit/build.py 10.3 && python pagekit/check_lesson.py 10.3 && python pagekit/audit_pages.py 10.3

Runs 2 to 5 are the commands of the kit's pull request (K-10.3, #146), written with the shell's variables; run 1 is the
page's Chat page step and run 6 the page's Rs 0 read of the saved runs. All are batch 4 (Mon 23 - Wed 25 Nov) in the
lesson plan's section 6, on the lane after lesson 10.2's runs.

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and the chat service of Module 5
  deployed (step 3 uses its `langchain` brain).
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API` and defines `tok`. Pass
  `REGION` to every `make agent-*` line: `commands/agent-turn.sh` builds rag-api's address from it, and the Makefile's
  default is `us-central1`.
- **The classes, once:** the bench's desk drops every passage with no class (`services/chat/desk_agent.py`,
  `_search()`). Lesson 10.1's setup line classes acme's and zeta's stored rows; if it has not run on this lane, run the
  page's line first. It costs no model call. The twelve rows are acme's but one, `calc-carry-forward-zeta`.

      for t in acme zeta; do make doc-types PROJECT="$PROJECT" TENANT=$t SEED=manifest APPLY=1; done

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
| 1 | `data/ui_twice.txt` | 3, the Chat page | 4 | two minutes | 2 chat turns: their captions show their rupees; the chat service stops a turn at Rs 5 |
| 2 | `data/turn_verify.txt` | 8, one verify turn | 4 | about a minute | 1 attempt, 3 calls offline: Rs 1.16 before thinking, plus Rs 1.91 for each 1,000 thinking tokens a call; each retry about Rs 1.31 more, plus Rs 2.55 for each 1,000 |
| 3 | `data/eval_plain.txt` | 9, the loop with the rule out | 4 | several minutes | 36 turns, 102 calls: Rs 35.88 before thinking, plus Rs 65.02 for each 1,000 thinking tokens a call |
| 4 | `data/eval_verify.txt` | 9, verify with the rule out | 4 | a few minutes | 12 runs, 37 calls with one retry: Rs 12.83 before thinking, plus Rs 23.59 for each 1,000 thinking tokens a call; each further retry about Rs 1.31 |
| 5 | `data/eval_side.txt` | 9, the side by side | 4 | seconds | Rs 0: the two saved files |
| 6 | `data/records_read.txt` | 9, the records read back | 4 | seconds | Rs 0: the two saved files |

**In all:** the 49 bench runs (runs 2 to 4) come to Rs 49.86 before thinking over 142 calls, and their thinking adds
Rs 90.52 for every 1,000 thinking tokens a call. The two chat turns of run 1 come on top, at the rupees their captions
show. The Meter's ceiling for the 49 runs is Rs 375.00: Rs 5 a loop turn, and Rs 15.00 a verify run, since each of its
three attempts has a Meter of its own. The kit PR's estimate is Rs 60-90 (Rs 2-5 for the turn, Rs 35-55 for the 36 loop
turns, Rs 15-30 for verify's 12 runs), and the lesson plan's for the lesson is Rs 60-90. The runs stay within Rs 60 while
their calls spend about 112 thinking tokens a call or fewer, and within Rs 90 at about 443 thinking tokens a call. Every
retry on the lane, which the deleted rule invites, adds about Rs 1.31 before thinking.

**The Rs 5 limit:** the Meter refuses every call once an attempt has spent Rs 5, so an attempt whose calls think
enough never makes its last call. A loop turn on these rows reaches Rs 5 before its last call only when its calls think
about 3,400 thinking tokens each, and a verify attempt (a reflect call and the loop's calls)
at about 2,206 thinking tokens a call. Lesson 10.1's run 1 (batch 1) measures the loop's thinking at `low` on this model: read its `thinking` figures
before batch 4. A stopped attempt prints `stopped by turn_budget`; it is a finding, not a failed run, so record it and
say so in the PR.

How the costs were computed (`build.py`, which prints them and names any figure this file no longer states): the
page's own offline runs, the twelve rows through the loop three times and through verify once on the kit's scripted
model (the slips write the right figure on six rows, and verify retries the one whose slip the check can see), and the
single verify turn of run 2; each call's input and visible tokens as the script counts them (four characters a token
over what the call is sent and what it writes); plus, for every call that binds the desk's tools (the loop's calls and
verify's answer calls, not its reflect calls), the tool declarations Gemini receives with it, which the script does not
count: the desk's eight tools as `ChatGoogleGenerativeAI.bind_tools` converts them, about 1,131 tokens; each call priced
at `gemini-3.6-flash`'s USD 1.50 in and 7.50 out per million from `shared/prices.py`, at Rs 85 to the dollar. Thinking is
billed as output, Rs 0.6375 for every 1,000 tokens, and the script's own thinking counts are left out: only the lane
knows the model's. The counts keep the prompt's calculator rule, which runs 3 and 4 delete, so they run about 66 tokens
a call high. The searches cost nothing at rag-api (`/v1/passages` books no tokens and no cost).

The page's prose says what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui_twice.txt` (step 3; batch 4)

In the browser, not a terminal: open `https://documind-ui-NUMBER.asia-south1.run.app`, the Chat page. Choose Brain
`langchain` and ask the gratuity row's question; then reload the page (a new browser session, with a new `session_id`,
so the second turn does not read the first), choose `langchain` again and ask the same question:

    I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

Record, for each of the two turns, the brain's name on a line of its own, the answer as the page shows it, and the
caption line under it, for example:

```text
langchain
<the first answer as shown>
brain: langchain · tools: <each tool call, in order> · <milliseconds> ms · Rs <rupees>

langchain
<the second answer as shown>
brain: langchain · tools: <each tool call, in order> · <milliseconds> ms · Rs <rupees>
```

Expect `tools:` to name `retrieve` and no calculator, since the chat brains hold none. The figures are the model's own:
record them as they are, right or wrong, and whether the two agree. The page holds them against the calculator's
Rs 2,40,000 and claims neither way.

### 2. `data/turn_verify.txt` (step 8; batch 4)

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=verify 2>&1 | tee turn_verify.txt
```

Expect the header with `verify (lesson 10.3): check, retry or choose: ...` and `the figure check: code, no model
(...); at most 3 attempts, each a turn of its own, a note of at most 300 characters before each retry`, then `attempt 1:
the loop, a turn of its own`, its calls and tools, `the attempt's answer: ...` and `the figure check, code and no model:
passed: ...` or `failed: ...`; then `the answer that ships: attempt N's, ...`, the answer as the Desk shows it, the
totals with `by role: answer K calls, Rs ...` and the figure check. With the prompt as it stands the first attempt may
pass, and then nothing is retried. Outcomes the page covers but cannot predict, any of which is a finding: a failed
first attempt, followed by `attempt 2: ..., after a note`, the reflect call's line `model call N (reflect,
gemini-3.6-flash, thinking low): ...` and the note; `the note writes ...`, a note with a figure in it; three failures
and `the last of 3: the figure check passed none`; an attempt `stopped by turn_budget` or `model_calls`. Record whichever
happened, and say which in the PR.

### 3. `data/eval_plain.txt` (step 9; batch 4): stdout only

First take the prompt's calculator rule out of your clone, for runs 3 and 4 only (git prints
` services/chat/desk_agent.py | 3 ---` and ` 1 file changed, 3 deletions(-)`):

```bash
sed -i '/Work every figure out with a calculator/,/say which one is missing/d' services/chat/desk_agent.py && git diff --stat
```

Then:

```bash
make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop SLICE=calc,trap RUNS=3 SAVE="$HOME/plain.jsonl" > eval_plain.txt
```

The progress lines (`  [i/12] <row> run r: N model calls, Rs ...`) go to stderr and stay on the terminal. Expect `LIVE:
gemini-3.6-flash on location global, and your lane's rag-api | 12 rows, 1 arm, 3 runs each, in this process
(--inproc)`, `saved 36 runs to /home/you/plain.jsonl: --replay rescores them at Rs 0` (replace your home directory),
then `== loop, thinking default (low), desk astar: 12 rows x 3 runs` with its 12 rows, the `first runs:` rates with
their intervals, the `pass@1` and `pass@3` lines, `a run:` and `in all:`. Keep `~/plain.jsonl` for runs 5 and 6.

### 4. `data/eval_verify.txt` (step 9; batch 4): stdout only

With the rule still out:

```bash
make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=verify SLICE=calc,trap SAVE="$HOME/verify.jsonl" > eval_verify.txt
```

Then put the rule back at once (git's stat prints nothing, and `grep -c` prints `1`):

```bash
git checkout -q -- services/chat/desk_agent.py && git diff --stat && grep -c 'Work every figure out with a calculator' services/chat/desk_agent.py
```

Expect `... | 12 rows, 1 arm, 1 run each, ...`, `saved 12 runs to /home/you/verify.jsonl: ...`, then `== verify,
thinking default (low), desk astar: 12 rows x 1 run` with its rows and rates, `with notes: the figure check passed on
attempt 1 in N, on attempt 2 in N, on attempt 3 in N and on none in N of 12 runs ...; N of M notes write a figure, which
no check takes from a note`, `any attempt (the ceiling, each row's first run): ...`, `a run:`, `in all:` and `by role,
a run: answer ...` (with `reflect ...` when a retry happened). If the `with notes` line says the check passed on attempt
1 in all 12 runs, the deleted rule did not make Gemini fail: record it, and say so in the PR, since verify then ties
pass@1. Keep `~/verify.jsonl` for runs 5 and 6.

### 5. `data/eval_side.txt` (step 9; batch 4)

```bash
make agent-eval REPLAY="$HOME/plain.jsonl $HOME/verify.jsonl" BEST_OF=3 | sed -n '1p;/^  paired (correct)/,$p' | tee eval_side.txt
```

Expect `replayed 48 saved runs of /home/you/plain.jsonl, /home/you/verify.jsonl: rescored at Rs 0, no model call (they
cost Rs ... when they ran)`, the two paired blocks (`paired (correct), 12 rows: ...` and `paired (verified), ...`, each
ending `indicative: the task set's model-written rows, one run each`), then `== check, retry or choose (lesson 10.3):
loop against verify, on the 12 rows both ran` with its four lines (`pass@1, loop's first run`, `pass@3 re-rolls, ...`,
`best-of-3, the run the figure check chooses (code, no model)`, `pass@3 with notes, verify's answer that ships ...`), each
with correct, verified, calls and rupees a row, and `the figure check's precision: ...`.

### 6. `data/records_read.txt` (step 9; batch 4)

Run step 9's last Python cell exactly as the page prints it (it starts `import json, os, sys, warnings` and reads
`~/plain.jsonl` and `~/verify.jsonl`) and record everything it prints. Expect one block a row: the row's id, `loop runs:
check .../.../..., verified .../.../...; best-of-3 ships run N`, and `verify: check ...; ships attempt N, verified ...`,
with `the note before attempt N: ...` and `figures it writes: ...` under a row whose verify run retried. Gemini's notes
are its own: record them as they are, figures and all.

When all six are in, rebuild the page, and reword nothing the recordings confirm.
