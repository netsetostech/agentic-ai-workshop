# Lesson 6.9 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/06-context-memory/6.9-working-memory/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild (with the chat image's pins: the build runs the kit's brains)
and check:

    python pagekit/build.py 6.9 && python pagekit/check_lesson.py 6.9 && python pagekit/audit_pages.py 6.9

Batch 2 of the lesson plan's section 6 (Mon 2 - Wed 4 Nov 2026). The build reads `full_vs_window.txt`'s two totals
lines into step 6's "What just happened"; it refuses a file that has neither the stand-in nor those lines.

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done, acme on the roster and you a
  member of acme. acme's `desk_gate` must not be `off` (the default is the rules): run 1's sixth question carries a
  published test card number, and run 3 expects the chat door to have masked it.
- **Where:** runs 1 and 3 in the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup
  block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `ME`, `NUMBER` and `API`. Run 2 on your own
  machine (or the operator shell), from the kit's root, with Application Default Credentials for your project.
- **What to record:** what the terminal shows for the cell or command, stdout and stderr together, with nothing
  trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`.
  Session ids, times and token counts may stay. `check_lesson.py` refuses a real project id, a project number in a
  URL or resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost (estimated when the page was built) |
|---|---|---|---|---|
| 1 | `data/ui_turns.txt` | 3, six questions in the UI, then the chat rows | five minutes | six turns: the chat calls' input about 24,891 tokens by the window's estimate (Rs 3.2), six rag-api answers at most Rs 2.33 each (Rs 13.95), plus the chat calls' output |
| 2 | `data/full_vs_window.txt` | 6, `make window-check LIVE=1`, twenty turns | twenty to forty minutes | about Rs 80 at list price before implicit caching (the kit builder's estimate: about 80 gemini-3.6-flash calls, roughly 500K tokens in and 25K out); the input alone by the window's estimate, 356,162 tokens, Rs 45 |
| 3 | `data/thread.txt` | 7, `make thread` on run 1's conversation | a minute | none: reads only |

How the estimates were computed (`build.py` computes each and refuses to build if this file no longer states it):
the window's estimate is `count_tokens_approximately` over what each call is sent in the offline runs of
`make window-check`, with the full thread for run 1 (today's behaviour on the lane) and both conversations for run 2,
priced at gemini-3.6-flash's list input price from `shared/prices.py` (USD 1.50 per million, USD_INR 85). It leaves
out the tool declarations, Gemini's own tokenizer, the answers and any caching. A rag-api answer is at most what
`services/rag-api/config.py`'s budgets allow one attempt (8,000 tokens in, 2,048 out). `TURNS=12` would send
128,346 tokens of input by the same estimate (Rs 16; the kit builder put it at about Rs 30-35 in all), and
`TURNS=6` 34,658 (Rs 4.4). The cohort plan budgeted Rs 70-115 for this lesson's runs.

The page's prose says what each recording should show, read from the kit's code; the expectations are under each run.
If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui_turns.txt` (step 3)

First, in the browser (not recorded): open `https://documind-ui-NUMBER.asia-south1.run.app`, sign in as yourself, and
on the Chat page choose Brain `langchain`. Ask these six questions, one at a time, in one conversation (one browser
session, no reload between them):

1. `What is the notice period for an employee at grade E3?`
2. `And during probation?`
3. `How many days of earned leave can be carried forward into the next year?`
4. `Is earned leave encashed when someone leaves the company?`
5. `What is the cap on domestic travel reimbursement per trip?`
6. `My corporate card 4111 1111 1111 1111 was charged twice for one flight. Who has to approve a travel claim above the cap?`

Note each answer's caption (`brain: langchain · tools: retrieve · ... ms · Rs N.NN`) and tell the page's editor if
the rupees did not climb. Then, within the hour, run step 3's cell exactly as the page prints it (the Python cell that
starts `import json, os, subprocess, warnings`) and record its output.

Expect `session <12 hex digits>: 6 turns, brain langchain`, the header line, six rows (`model calls` 2 when Gemini
searched once; more if it searched again), `tokens_in` climbing row by row, `cached` above 0 on the later rows if
Gemini's implicit cache matched a repeated beginning, the two rupee columns, and last `turn 6 sent N.N times turn 1's
input tokens`. The cell writes `~/lesson69-session.txt` for run 3. If the session line names another conversation (a
later chat in the same hour), run the cell again straight after the six questions.

### 2. `data/full_vs_window.txt` (step 6)

From the kit's root, with ADC for your project (your project id in place of the placeholder):

```bash
make window-check LIVE=1 PROJECT=documind-ai-YOUR-ID SAVE=full_vs_window.json | tee full_vs_window.txt
```

Copy `full_vs_window.txt` to `data/`. The page does not read `full_vs_window.json` (every turn's question, answer,
citations, thread size, every call's window report and usage): keep it beside the text as the run's full record, or
leave it out. Neither file carries a project id: the header says `with gemini-3.6-flash (location global), on your
machine`, and the sources are chunk ids on acme.

Expect the header (`full against windowed with gemini-3.6-flash (location global), on your machine`, the 2,000-token
budget, the Rs 0 lane's searches), then for each of the twenty turns `turn N: <the question>` and two rows,
`full` and `windowed`, each with `in`, `estimate`, `cached`, `out`, `calls`, `Rs`, the start of the answer and its
sources (`the same as full` on the windowed row when both cited the same passages); the windowed row adds the largest
call's context, its ceiling and the turns kept and brought forward. Then `totals:` with both conversations, `the
window sent N% fewer input tokens and cost N% fewer rupees than the whole thread` and `the two answers cited the same
sources on N of 20 turns`. What the page says to look for: the full row's `in` climbing every turn and the windowed
row's levelling off once turns start leaving the call (turn 14 in the offline run; Gemini's longer answers may bring it
earlier), `cached_tokens` on both, and turn 20's two answers to `What was the first question I asked you in this
conversation?` (offline, the windowed call's line no longer lists turn 1 by then).

If the run stops with `stopped: turn N, the windowed conversation: ...` (exit 1), Gemini refused the windowed
conversation: record it as it is and tell the page's editor; that is a finding about the folded line or the cleared
results, the first time they reach a real model. The searches run on your machine (BM25 over `evals/corpus`): a
`retrieve took ... (budget 25s)` warning means a search passed its budget and that turn's model read a failed search;
re-run when the machine is quieter. A turn that answers `I stopped this turn at one of its limits` reached the chat
service's per-turn limits (Rs 5, twelve model calls), and its row names the limit (`; stopped by model_calls`): record
it, and say so.

### 3. `data/thread.txt` (step 7)

Straight after run 1, in the same shell:

```bash
make thread PROJECT="$PROJECT" EMAIL="$ME" SESSION="$(cat ~/lesson69-session.txt)"
```

Expect the connection line (`<project>:asia-south1:documind-checkpoint, database documind, as chat (read only)`:
replace the project id), `thread acme:<your email>:<session>: N checkpoints, 6 turns` (replace the email with
`you@your-company.com`), then the step table: one `input` row per turn, `langchain` in the brain column, the message
count climbing to 24 at the last step (four messages a turn when Gemini searched once), and turn 6's input row
reading `input, not in the messages yet: human  My corporate card [card no.] ...`. If the sixth question shows the
number as typed, acme's `desk_gate` is `off`: say so, because step 7's prose then changes.
