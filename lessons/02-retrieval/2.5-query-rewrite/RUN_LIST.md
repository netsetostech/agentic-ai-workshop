# Lesson 2.5 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/02-retrieval/2.5-query-rewrite/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 2.5 && python pagekit/check_lesson.py 2.5 && python pagekit/audit_pages.py 2.5

The build reads more than it shows. `rewrites.txt` replaces the bench's illustrations with the model's own rewrites;
the three ablation files and `changeit.txt` fill the "author's lane" paragraphs under steps 7 and 8; `candidate.txt` is
split into its three windows. The build refuses a file whose shape it cannot read and says which; re-record that one.

## Before the first run

- **The lane:** deployed by lesson 0.3's `make plan` / `make up` with this branch's kit (the rag-api image must carry
  `services/rag-api/rewrite.py`), `make ingest-corpus` done. `QUERY_REWRITE` is absent from the live service.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `NUMBER`, `API` and
  defines `tok`; then the page's names box, which defines `svc_env` and installs the Ranking API's client.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Pin it back to `rag_engine` after run 9,
  with the setup's pin-back window (not recorded).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (it is in every candidate URL gcloud
  prints); your email `you@your-company.com`. Revision names, times and milliseconds may stay. `check_lesson.py`
  refuses a real project id, a project number in a URL, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

Rupees are the page's own estimates (step 7's cost table): the Ranking API at the rate lesson 2.3 states, one US dollar
per thousand requests; each rewrite call from the prompt's length through `shared/prices.py`; an answer at most what
config.py's budgets allow one attempt (8,000 tokens in, 2,048 out at gemini-3.6-flash's list price, Rs 2.33).

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/ui.txt` | 3, a paraphrase in the Chat page, then the log | a minute | one answer, at most Rs 2.33 |
| 2 | `data/rewrites.txt` | 5, rewrite() on the bench's nine questions | under a minute | nine flash-lite calls, about Rs 0.08 |
| 3 | `data/candidate.txt`, section `### on` | 6, the stage on a no-traffic candidate, one question | two minutes | one answer and one call, at most Rs 2.34 |
| 4 | `data/candidate.txt`, section `### fallback` | 6, a model that does not exist, the same question | two minutes | one answer, at most Rs 2.33 (the failed call bills nothing) |
| 5 | `data/rewrite_rows.txt` | 6, the two `query_rewrite` lines | seconds | none |
| 6 | `data/candidate.txt`, section `### undo` | 6, the undo | a minute | none |
| 7 | `data/ablate_wiring.txt` | 7, the wiring check | about a minute | 10 Ranking API requests and 5 calls, about Rs 0.89 |
| 8 | `data/ablate_golden.txt` | 7, the golden rows | a few minutes | 94 requests and 45 calls, about Rs 8.38 |
| 9 | `data/ablate_paraphrases.txt` | 7, the golden rows and the paraphrases | a few minutes | 142 requests and 69 calls, about Rs 12.66 |
| 10 | `data/changeit.txt` | 8, the edited prompt on the 13 rows with a literal | about a minute | 26 requests and 12 calls, about Rs 2.31 |

In all, about Rs 24 for the Ranking API requests and the rewrite calls, plus three answers that print their own cost.
The cohort plan budgeted about Rs 20; the difference is run 9, which scores the 47 golden rows again beside the 24
paraphrases (71 rows, not 24), and run 10, the Change-it's own small run.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui.txt` (step 3)

In the DocuMind UI's Chat page, signed in as yourself (the direct brain), ask exactly:
`How much can I claim per trip for domestic travel?` Then, within ten minutes:

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="stream" OR jsonPayload.event="query_rewrite")' \
  --project "$PROJECT" --freshness 10m --limit 5 --format=json | python -c "
import sys, json
rows = [e['jsonPayload'] for e in json.load(sys.stdin)]
for r in rows:
    if r['event'] == 'stream':
        print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| pool', r.get('pool'), '| retrieve_ms', r.get('retrieve_ms'),
              '| answerable', r.get('answerable'), '| Rs %.2f' % (85 * (r.get('cost_usd') or 0)))
print('query_rewrite lines in the last 10 minutes:', sum(1 for r in rows if r['event'] == 'query_rewrite'))"
```

Expect one `stream | brain ui | tenant acme | pool 20 | ...` line per question asked in the window and
`query_rewrite lines in the last 10 minutes: 0`. Note in the review whether the answer cited EXP-12 and said 40,000.

### 2. `data/rewrites.txt` (step 5)

Run the page's step 5 cell as written (a Python heredoc; it builds a google-genai client on `global` from your ADC).
Expect nine lines in the shape `pp-01  rewritten   812 ms  <the rewrite>`, one per bench row in the cell's order,
each outcome one of `rewritten`, `same`, `rejected` (with `dropped ... - the question is searched`) or `fallback`
(with the error's class), then `9 calls to gemini-3.1-flash-lite, prompt 2026-10-08.1: N tokens in, N out, Rs 0.0N at
list price`. The build reads every line: a row whose outcome is `rewritten` must pass the kit's guard, and every row
id must be there. Record the run as it comes; do not re-run for a nicer outcome.

### 3, 4 and 6. `data/candidate.txt` (step 6), one file in three sections

Paste each cell's output under its own header line, exactly `### on`, `### fallback` and `### undo`, in that order.

`### on` is the step's first cell as written: `gcloud run services update ... --no-traffic --tag candidate
--update-env-vars QUERY_REWRITE=on --quiet`, the `CAND` export, the `ask()` definition and
`ask "$CAND" "How much can I claim per trip for domestic travel?"`. Expect gcloud's deploy lines (the candidate URL
with `NUMBER` replaced), then `rewrite rewritten | rewrite_ms ... | retrieve_ms ... | pool 20 | answerable True | Rs ...`,
a `searched:` line that is not the question, and the citations. If the outcome is `same`, the page tells learners to
ask pp-10's question instead (`How many remote-work days am I allowed per month?`); do the same, record both, and say
so in the review.

`### fallback` is the second cell: `--update-env-vars QUERY_REWRITE_MODEL=no-such-model`, then the same `ask`. Expect
`rewrite fallback | ...`, an answer (`answerable True`), and `searched: How much can I claim per trip for domestic
travel?`. The build asserts the section contains `rewrite fallback`.

`### undo` is the fourth cell (run 6, after run 5's log read): `--remove-env-vars QUERY_REWRITE,QUERY_REWRITE_MODEL`,
`update-traffic --remove-tags candidate`, the `template now:` echo and the traffic describe. Expect
`template now: QUERY_REWRITE= QUERY_REWRITE_MODEL=` and `100;documind-api-...` naming the revision that served before
run 3.

### 5. `data/rewrite_rows.txt` (step 6)

Straight after run 4 (give the log half a minute):

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query_rewrite"' \
  --project "$PROJECT" --freshness 15m --limit 2 --format=json | python -c "import sys, json; [print(json.dumps(e['jsonPayload'])) for e in json.load(sys.stdin)]"
```

Expect two JSON lines, newest first: `"outcome": "fallback"` with `"error"` naming google-genai's exception class (the
page does not say which; the recording does), `"model": "no-such-model"`, zero tokens and cost; then
`"outcome": "rewritten"` with tokens, a cost in fractions of a cent and `"prompt_version": "2026-10-08.1"`. Neither
line may carry the question's words.

### 7. `data/ablate_wiring.txt` (step 7)

```bash
make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --limit 5"
```

Expect make's echo of `python evals/ablate.py ...`, `5 rows with anchors`, the header, the lane's row and the rewrite
row, the `rewrite: 5 questions - ...` tally under the second, any `lost:` lines, and the reading-order lines including
the rewrite row's two. Replace the project id in the header line.

### 8. `data/ablate_golden.txt` (step 7)

```bash
make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite"
```

Expect `47 rows with anchors`, the two arm lines, `rewrite: 45 questions - ...` (lk-06 and vr-01, lk-24 and lk-29 ask
in the same words, so 45 calls), the miss lists, the reading lines. The build writes the golden paragraph from the two
arm lines and the tally.

### 9. `data/ablate_paraphrases.txt` (step 7)

```bash
make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --paraphrases evals/paraphrases.jsonl"
```

Expect `71 rows with anchors`, `24 of them paraphrases (evals/paraphrases.jsonl): ...`, and under each arm line the
split `golden 47 rows, recall@5 ..., mrr ..., N at 1.0 | paraphrases 24 rows, ...`, then `rewrite: 69 questions - ...`
under the rewrite row. The build reads both split lines.

### 10. `data/changeit.txt` (step 8)

Run step 8's first two cells unrecorded (the literal rows to `/tmp/literal_rows.jsonl`; the edit, which prints
`5 rules left; ...`), then record:

```bash
make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --golden /tmp/literal_rows.jsonl"
```

Expect `13 rows with anchors`, the two arm lines and `rewrite: 12 questions - N rewritten, N given back as asked, N
refused by the literal guard, N fell back; ...`. The page sets its refused count beside run 8's. Then run step 8's
restore cell (unrecorded) and check it prints `the rule is back: True`: the clone must not keep the edited prompt.
