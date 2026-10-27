# Lesson 2.6 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/02-retrieval/2.6-system-one/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 2.6 && python pagekit/check_lesson.py 2.6 && python pagekit/audit_pages.py 2.6

Every Jev figure on the page reads "Jev not available" until a recording of Jev exists. Nothing here records Jev today:
`JEV_MODE` stays `off`, TypeSafe's adapter is PR 2.6-C, and whether the course may publish TypeSafe's outputs and
metrics is one of the terms asked of TypeSafe (the lesson plan's decision 5). Run 3 says how Jev joins the page later.

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and `make roster` run (acme and
  zeta `any`, globex `in`). Nothing here changes the lane: the runs are reads and model calls only.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API`, and pins acme to the kit's
  index (`make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`). Put the pin back after run 3.
- **Shell variables:** `JEV_MODE` and `JEV_API_KEY` unset (`env | grep JEV_` prints nothing).
- **What to record:** what the terminal shows for the command, stdout and stderr together (the eval's `... 10/65 rows`
  progress lines go to stderr; make's echo of the recipe is part of the output), with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`.
  make's echo carries the project id. A pool or generator error row can carry the API's address, which holds the
  project number: `grep -n "$NUMBER\|$PROJECT" data/*` before you copy, and replace what it finds.
  `check_lesson.py` refuses a real project id, a project number in a URL and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost (estimated when the page was built) |
|---|---|---|---|---|
| 1 | `data/ui_refusal.txt` | 3, rf-01 in the UI and from the shell | two minutes | two generator calls (the UI's and the shell's): Rs 0.46 of input, at most Rs 3.08 in all |
| 2 | `data/decide_learner.txt` | 6, `make decide` on zeta's 10 rows | about two minutes | 10 generator calls: Rs 2.75 of input, at most Rs 15.80 in all |
| 3 | `data/decide_live.txt` and `data/decide_run.json` | 7, all 65 rows, saved | ten to fifteen minutes | 65 generator calls: Rs 17.57 of input, at most Rs 102.43 in all; plus Jev's, later |

How the costs were computed (`build.py`, which prints them and names any figure this file no longer states): every
golden row's pool on the Rs 0 lane, packed the way `generator.generate()` packs it (`_budget()`, `pack_chunks()`, the
prompt line) and counted by the kit's `estimate_tokens()` (four characters a token), priced with `shared/prices.py`
(gemini-3.6-flash, USD 1.50 in and 7.50 out per million, USD_INR 85). "Of input" is that prompt alone; "at most" adds
the whole 2,048-token answer reserve (`max_answer_tokens`, thinking included) to every call. A call cut off at the
reserve is asked once more with three times the room, which no estimate here includes. The lesson plan's figure for the
batch was Rs 60-100 plus Jev. `/v1/passages` calls cost nothing: no model, no tokens.

Jev, when it is recorded: TypeSafe's page prices input at USD 42 per billion tokens and names no output price. The 57
rows Jev may be sent (acme and zeta) come to about 90,914 tokens on the Rs 0 lane's pools by the kit's count: about
Rs 0.32 in all, input only.

The page's prose says what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui_refusal.txt` (step 3)

First, in the browser (not recorded): open `https://documind-ui-NUMBER.asia-south1.run.app`, sign in as yourself, and
on the Chat page (Brain `direct` if the sidebar offers one) ask `What is ACME's sabbatical policy?`. Check what step 3
says you will see: a refusal in the model's words, a Sources list of about five passages, and the sidebar's
"Cost this session" grown by the turn. Tell the page's editor if any of the three differs.

Then run step 3's second cell (the Python cell that starts `import json, os, subprocess, sys, urllib.request,
warnings`) exactly as the page prints it, and record its output.

Expect: `/v1/query     answerable False | confidence low | citations 0 | backend vertex | model gemini-3.6-flash`; a
`pool 20` line where `generate_ms` is the largest of the three stages; `tokens ... in + ... out | cost_usd on the
answer: None | priced by shared/prices.py: Rs 0.xxxx`; the answer's first 100 characters; then `/v1/passages
passages 5 | answerable True | model none | cost_usd 0.0` and five passage lines (file names only, no bucket). If
`answerable` comes back True, the model answered a refusal row: record it anyway, and say so.

### 2. `data/decide_learner.txt` (step 6)

```bash
make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--tenant zeta --save evals/reports/decide-zeta.json" 2>&1 | tee decide_learner.txt
```

Expect make's echo (`JEV_MODE=off python evals/decide.py --project documind-ai-YOUR-ID --region asia-south1 --tenant
zeta --save evals/reports/decide-zeta.json`), then the header: `rows       10 golden rows: 5 answerable, 5 not`, the
pool from `your lane's /v1/passages ... top 5`, the generator through `run_eval.ask() (top_k 6)`, and `jev
JEV_MODE=off: Jev not available, nothing sent`. Then both the rule and the generator decided on 10 rows, kappa against
the generator, the rows where the arms disagree, the generator's right decisions by confidence, latency for both, and
the rupee lines: `rule Rs 0 ...` and, on the default vertex backend, `generator  - (10 decisions unpriced)`, because
`/v1/query` leaves `cost_usd` null for a Gemini answer and `decide.py` prices only what the answer carries. Last line:
`saved: evals/reports/decide-zeta.json`. Exit status 0.

### 3. `data/decide_live.txt` and `data/decide_run.json` (step 7)

```bash
make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--save evals/reports/decide-live.json" 2>&1 | tee decide_live.txt
python - <<'PY'
import json
run = json.load(open("evals/reports/decide-live.json", encoding="utf-8"))
rows = run.pop("rows")
for r in rows:                               # the passages' ids stay, so the file still replays with --from; their text goes
    r["pool"]["passages"] = [{"n": p["n"], "chunk_id": p["chunk_id"]} for p in r["pool"]["passages"]]
with open("decide_run.json", "w", encoding="utf-8", newline="\n") as f:       # the run's own fields, then one line a row
    f.write(json.dumps(run, ensure_ascii=False)[:-1] + ', "rows": [\n'
            + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]}\n")
PY
```

Copy `decide_live.txt` and `decide_run.json` into `data/`. The build reads every Level 5 figure for the rule on your
lane and for the generator from `decide_run.json`, with `decide.py`'s own scoring, and checks that its answer rate and
refusal recall for both arms are the ones `decide_live.txt` prints: the two files must come from the same run.

Expect `rows       65 golden rows: 47 answerable, 18 not`, both arms decided on every row (an empty pool is rare on a
dense lane), the false answers by id with isolation rows starred, kappa, the disagreements, the rule's Brier and bins,
the generator by confidence, latency, `generator  - (65 decisions unpriced)` (or fewer, if a pool was empty), and
`saved: evals/reports/decide-live.json`.

**Jev, later.** Once PR 2.6-C has merged with recordings in `evals/system_one/recorded.jsonl`, made against TypeSafe's
API, and TypeSafe's terms allow the course to publish them, add Jev to the same pools for Rs 0 with no lane:

```bash
JEV_MODE=recorded python evals/decide.py --from evals/reports/decide-live.json --save evals/reports/decide-live-jev.json 2>&1 | tee decide_live.txt
```

then rerun the slimming cell with `decide-live-jev.json` in its first line and copy both files again. A recording made on another pool says
so in its reason. If PR 2.6-C records through a live run instead, record that run's output and saved file here in the
same two names. Until then the page shows Jev not available, and nothing on it is a Jev output.

When all three runs are in, put acme's pin back (the setup section's last window), and rebuild the page.
