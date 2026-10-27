# Lesson 3.6 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/03-generation/3.6-quote-checks/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 3.6 && python pagekit/check_lesson.py 3.6 && python pagekit/audit_pages.py 3.6

Everything else on the page is computed when it builds, from the kit: the two interactives (checked in node against
`quote_check()`, `hashlib` and `prompt_pin.check()`), step 3's nine quotes and its stand-in gate, step 5's
`make prompt-version`, step 7's branch cells (the edit, the refusal, the registration with the check and the unit test,
the commit) on a throwaway copy of the kit, and the shape of step 8's undo. The reader, comparison and rows cells, and
the two one-line Python filters of step 7, are also run at build time against stand-ins.

Batch 1 of the lesson plan's section 6 (Mon 26 - Wed 28 Oct).

## Before the first run

- **The lane:** deployed by `make up` (lesson 0.3) with `make ingest-corpus` done, serving the kit the page was built
  against. Cloud Build must work on the lane, as it did for `make up`. If an earlier lesson left a `candidate` tag,
  remove it first (step 8's undo, its first two lines).
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), inside
  `rag-shell-venv` with rag-api's pins (Module 0's install; the bench in run 3 imports `services/rag-api/generator.py`),
  after the page's shared setup block, which exports `PROJECT`, `REGION=asia-south1`, `ME`, `NUMBER` and `API` and
  defines `tok`.
- **The clone:** on `main`, up to date (the setup block pulls) and clean: `git status --short` prints nothing. Step 7
  makes a branch, `prompt-v4`, and commits on it; nothing is pushed.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. The chunk ids the reader prints are then
  the kit's. Put the pin back (`RETRIEVAL_BACKEND=rag_engine`) after the undo.
- **Order, in one sitting:** step 4's UI question, then runs 1 to 8 in order, all within six hours (run 8 reads the last
  six hours of rows), then step 8's undo.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but secrets
  and, in run 4 only, the middle of Cloud Build's own log (keep its first lines and its closing table).
- **Placeholders:** project id `documind-ai-YOUR-ID` (also inside the image path); project number `NUMBER`, including in
  URLs (`https://candidate---documind-api-NUMBER.asia-south1.run.app`); emails `you@your-company.com`; commit shas
  `COMMIT`. Revision names and times may stay. `check_lesson.py` refuses a real project id, a project number in a URL or
  resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/quotes_live.txt` | 4, the scoped gate on the live revision, the switch on | a few minutes | about Rs 4.5 |
| 2 | `data/quotes_live_cites.txt` | 4, every citation's verdict | seconds | Rs 0: reads the report |
| 3 | `data/bench_v4.txt` | 6, rule 5 weakened on the bench | a few minutes | about Rs 4.5; the bench prints its own figure |
| 4 | `data/ship_v4.txt` | 7, the build and the candidate | about ten minutes, mostly Cloud Build | one Cloud Build: not priced by the kit |
| 5 | `data/version_v4.txt` | 7, the label on both URLs | seconds | Rs 0: two GETs |
| 6 | `data/quotes_candidate.txt` | 7, the scoped gate on the candidate | a few minutes | about Rs 4.5 |
| 7 | `data/quotes_compare.txt` | 7, v3 against v4 | seconds | Rs 0: reads two reports |
| 8 | `data/rows_v4.txt` | 8, the rows by revision, event and version | seconds | Rs 0: one log read, one describe |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs 85
to the dollar, priced at the course's typical answer of 2,000 tokens in and 300 out (the figure lessons 4.3, 4.4 and
11.6 use): Rs 0.45 an answer. Runs 1, 3 and 6 are 10 answers each, about Rs 4.5 each and about Rs 13 in all. Their pool
reads (`/v1/passages`) make no model call. The query embedding and the Ranking API bill on their own lines for every
answer and pool read, and are not estimated here. Run 4's Cloud Build bills build minutes on Cloud Build's own line, and
the image's storage on Artifact Registry's; the kit carries neither price. `make usage PROJECT="$PROJECT" HOURS=6` after
run 6 prints the real figure for runs 1 and 6 (the bench's answers leave no usage row; it prints its own). Please note
both when you hand the files back. The lesson plan estimated about Rs 16 plus a Cloud Build; the review of 7 October
about Rs 8 for each scoped run.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/quotes_live.txt` (step 4)

First, in the browser, signed in as yourself, ask the UI *What is the notice period for a confirmed E3?* and open
Sources (the page describes what you see; nothing is recorded). Then:

```bash
DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" SOURCE=hr_policy_2026.md REPORT=evals/reports/quotes36.json
```

Expect `>> https://documind-api-NUMBER.asia-south1.run.app`, `== eval gate: LIVE ==`,
`scoped to hr_policy_2026.md: 10 row(s) cite it`, `10 rows (10 answerable, 0 not)`, six judged threshold lines and three
`[ -- ]` lines (refusal, media, isolation: no rows in scope), then three `[info]` lines: `quote_support_rate`,
`quote_passage_rate` with its `N of M answered rows' quotes in the passage they cite; elsewhere ..., absent ...,
substituted ..., unread ...` and `must_retrieve_recall`; the shape table (lookup 9, version 1), the latency lines, any
rows that cost a point, `report: evals/reports/quotes36.json`, and `All thresholds met.` If the gate blocks, record it
anyway and say so: the prose then needs the reason.

### 2. `data/quotes_live_cites.txt` (step 4)

Run the page's step 4 reader cell as written (the cell that starts `import json, warnings` and reads
`evals/reports/quotes36.json`) and record it.

Expect a header line with the API URL, `10 rows` and the two rates as run 1 printed them; one line per citation with
its verdict, the cited passage's position (`#1` is NP-03 in the handbook) and the quote's first words; a `pool` line
only for a row whose pool could not be read or lacked an anchor; and `verdicts: own N, elsewhere N, absent N,
substituted N, unread N`. Please tell the editor which verdicts other than `own` appeared, with their rows: the step's
"What just happened" is written for either case and gains a sentence for yours.

### 3. `data/bench_v4.txt` (step 6)

```bash
make bench PROJECT="$PROJECT" BENCH_ARGS="--from-report evals/reports/quotes36.json --no-baseline --drop-rule 5 --add-rule 'A quote sums up the clause that answers - at most fifteen words, in plain language.'"
```

Expect `>> https://documind-api-NUMBER.asia-south1.run.app`, `== prompt bench: gemini-3.6-flash, against ... ==`,
`10 row(s) x 1 arm(s) x 1 level(s) x 1 run(s)`, a pool line per row with its `eval-live:` result from run 1's report,
then the arm: `edit  rule 5 dropped; rule added: A quote sums up the clause that answers - at most fifteen words, in
plain language. - 5 rules; no temperature` and
`prompt sha256 269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8`. **That sha256 must match**: the page
computes it from the kit, and step 7 registers it as v4. If it differs, stop: the clone is not the kit the page was
built from. Then ten answer lines, the summary table with `pass k/10`, the `quotes edit LOW: N of M in the passage they
cite (...)` line, `Rs X in all: 10 answers, ...` and `generator.py unchanged on disk; SYSTEM is the kit's again`.

### Step 7's branch cells (not recorded)

Run, in order and as written: the branch cell (`git status --short; git switch -c prompt-v4` and the Python edit), the
refusal (`make prompt-version; echo "exit $?"`), the registration cell (the Python edit, the check and the unit test)
and the commit. The page shows their output as computed from the kit; tell the editor if yours differs in anything but
the commit sha and the test's time. Expect the refusal to name `"v4"` and the line
`"documind-rag@v4": "269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8"`, `Error 1` and `exit 2`; then
`exit 0`, `Ran 6 tests` and `OK`; then the commit with `4 files changed`.

### 4. `data/ship_v4.txt` (step 7)

Run the page's build cell as written and record all of it:

```bash
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format=json \
  | python -c '...the page's one-line filter...'
make build PROJECT="$PROJECT" SERVICES=api
make release-candidate PROJECT="$PROJECT"
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"
```

Expect `PROMPT_VERSION on the service: not set, so config.py names the version`. **If it names a value, stop**: remove
it (`gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --remove-env-vars PROMPT_VERSION`),
tell the editor, and start the cell again. Then
`>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api`, Cloud Build's
log (cut its middle to `...`, keep its first lines and the closing table with `STATUS SUCCESS`), make's echo of the
`gcloud run services update documind-api ... --image ...api:COMMIT --no-traffic --tag candidate --update-env-vars
GIT_SHA=COMMIT --quiet` line and gcloud's progress lines, then
`>> candidate revision: documind-api-000NN-xxx (deploy/.candidate-revision - make promote moves traffic to it by name)`,
`>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app  (make eval-live API=that, then make promote)`
and `CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app`.

### 5. `data/version_v4.txt` (step 7)

Run the page's version cell (the `for u in "$API" "$CAND"` loop) and record it. Expect two lines:
`https://documind-api-NUMBER.asia-south1.run.app | prompt documind-rag@v3 | git_sha COMMIT | this commit: False` and
`https://candidate---documind-api-NUMBER.asia-south1.run.app | prompt documind-rag@v4 | git_sha COMMIT | this commit: True`.
Both shas become `COMMIT`; the booleans keep the difference.

### 6. `data/quotes_candidate.txt` (step 7)

```bash
DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE=hr_policy_2026.md REPORT=evals/reports/quotes36_v4.json
```

Expect run 1's shape against `https://candidate---documind-api-NUMBER.asia-south1.run.app`, ending
`report: evals/reports/quotes36_v4.json`. Record it whatever the quotes did: if v4's quotes are all still `own`, the page
reads right (the schema's own description of the field held the model to the clause), and the editor adds that
sentence. If the gate blocks, record it and say why.

### 7. `data/quotes_compare.txt` (step 7)

Run the page's comparison cell as written (the cell that reads `evals/reports/quotes36.json` and
`evals/reports/quotes36_v4.json`) and record it. Expect `v3: gate exit ... | quote_support_rate ... | quote_passage_rate ... | own N, ...`, the same line
for `v4:`, then a table of the ten rows: v3's checks, v4's checks and v4's first quote.

### 8. `data/rows_v4.txt` (step 8)

Within six hours of run 1, run the page's rows cell as written (the cell that starts
`import collections, datetime as dt, json, os, subprocess, warnings`) and record it. Expect the row count, then a table
by revision, event and prompt version: the serving revision with `query v3` (run 1's ten), `passages v3` (run 1's ten and
the bench's ten) and a `stream v3` row for your UI question; the candidate's revision, `none` for traffic, with
`query v4` (ten, with tokens) and `passages v4` (ten, `tokens_out` 0); then
`rows that say v4 come from: documind-api-000NN-xxx; serving traffic among them: none`. Rows from earlier work in the
window may appear under the serving revision as v3; they may stay.

### After run 8 (not recorded)

Run step 8's undo cell as written, then put acme's pin back. Tell the editor if its shape differs from the page's: the
traffic table, `the candidate URL now: HTTP 404`, `Switched to branch 'main'`, the check on `main` with `exit 0`, and
`  prompt-v4`. The branch stays in your clone; the image stays in Artifact Registry.
