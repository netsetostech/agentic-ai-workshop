# Lesson 4.3 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/04-evals-safety/4.3-placing-evals/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 4.3 && python pagekit/check_lesson.py 4.3 && python pagekit/audit_pages.py 4.3

Everything else on the page is computed when it builds, from the kit: the placement matrix, the pipeline cell's
output, the broken row and its restore (run on a throwaway copy of the kit's evals), the report cell (over a stub's
report), and the shapes of `make candidate`, the `/version` check, the tag's removal and `make usage`.

## Before the first run

- **The lane:** deployed by `make up` (lesson 0.3) with `make ingest-corpus` done, serving the kit the page was built
  against. The runs make one revision of `documind-api` with no traffic, whose tag run 1 removes, and nothing else that
  serves. If an earlier lesson left a `candidate` tag, remove it first (run 1's last block).
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block, which exports `PROJECT`, `REGION=asia-south1`, `ME`, `NUMBER` and `API` and defines `tok`.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Run 3 needs it: on RAG Engine an
  off-topic question can come back with an empty pool, and its row then says `false`, which is not the case the page
  shows. Put the pin back (`RETRIEVAL_BACKEND=rag_engine`) after run 4.
- **Order, in one sitting:** run 1 (step 4); then the UI question (step 5); run 2 (step 5); run 3 (step 6, within 30
  minutes of the UI question); run 4 (step 7, within six hours of run 1, and a few minutes after run 3 so the metrics
  have its point).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, including in URLs
  (`https://candidate---documind-api-NUMBER.asia-south1.run.app`); emails `you@your-company.com`; commit shas `COMMIT`.
  Revision names and times may stay. None of the four cells prints an email; check anyway. `check_lesson.py` refuses a
  real project id, a project number in a URL or resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/candidate_gate.txt` | 4, the gate on a candidate | about ten minutes | about Rs 29 (about Rs 4.5 scoped) |
| 2 | `data/rows_by_revision.txt` | 5, the rows split by revision and caller | seconds | Rs 0: one log read, one describe |
| 3 | `data/stream_refusal.txt` | 6, one refusal through the stream, and its row | under two minutes | about Rs 0.45, and the same for the UI question |
| 4 | `data/alert_series.txt` | 7, the alert's metrics, policies and windows | seconds | Rs 0: two Logging and three Monitoring reads |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs 85
to the dollar, priced at the course's typical answer of 2,000 tokens in and 300 out (the figure lessons 4.4 and 11.6
use): Rs 0.45 an answer. Run 1 is 65 answers, since the outsider's 11 requests are refused at the roster before any
model call: about Rs 29. The scoped fallback (`SOURCE=hr_policy_2026.md`) is 10 answers: about Rs 4.5. Run 3 is one
answer. The usage rows price generation only: the query embedding and the Ranking API bill on their own lines, and are
not estimated here. `make usage PROJECT="$PROJECT" HOURS=1` straight after run 1 prints the real figure; please note it
when you hand the files back. The review of 7 October estimated about Rs 35 for run 1 (about Rs 10 scoped) and about
Rs 1 for run 3.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/candidate_gate.txt` (step 4)

The step's cells in order. Record only the gate (`make eval-live`):

```bash
make candidate PROJECT="$PROJECT"          # no override: the Makefile's settings, the image unchanged
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"
for u in "$API" "$CAND"; do echo "$u/version"
  curl -s "$u/version" -H "Authorization: Bearer $(tok "$API")" \
    | python -c 'import json, sys; v = json.load(sys.stdin); print("  git_sha", v["git_sha"], "| generator", v["generator_model"], "| prompt", v["prompt"])'
done
make eval-live PROJECT="$PROJECT" API="$CAND" REPORT=evals/reports/cand43.json      # record this one
```

Then the page's report cell (step 4, not recorded), and the tag's removal:

```bash
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"
```

Expect `>> https://candidate---documind-api-NUMBER.asia-south1.run.app`, `== eval gate: LIVE ==`,
`65 rows (47 answerable, 18 not)`, nine `[PASS]` lines, the shape table, the latency lines, any rows that cost a
point, `report: evals/reports/cand43.json` and `All thresholds met.` If the gate exits non-zero, record it anyway: the
prose then needs the reason. Also tell the page's editor if any of these differs from the shapes the page shows:
`make candidate`'s two `>>` lines; the two `/version` lines naming the same `git_sha`, `gemini-3.6-flash` and
`documind-rag@v3`; the report cell's `thresholds judged: 9 of 9` and `required rows: 15 of 15 passed`; the untag's
`HTTP 404`.

Fallback, only if the full run cannot be afforded:
`make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE=hr_policy_2026.md REPORT=evals/reports/cand43.json`. Say so when
you hand the file back: the prose, the checklist and runs 2 and 4 assume the full set, and a scoped run judges six
thresholds, asks one required row (vr-01) and leaves 10 rows on the candidate, all acme.

### 2. `data/rows_by_revision.txt` (step 5)

First, in the browser, signed in as yourself (Module 0 put your account on acme's roster), ask the UI:
*What is ACME's sabbatical policy?* Then run the page's step 5 cell as written (the Python heredoc that starts
`import collections, datetime as dt, json, os, subprocess, warnings`), and record it. Then run
`make usage PROJECT="$PROJECT" HOURS=24`: not recorded, because the page shows its shape; tell the editor if its
section titles or columns differ from the page's.

Expect the row count; a revision table with the serving revision (`serving`: your UI stream and any earlier rows) and
the candidate's revision (`none`): 65 rows, 65 query, 0 stream, 65 under `eval id`; the identity table, with
`documind-ui-sa: gates, judge, smoke, tok` and `everyone else: N identities`; then
`golden.jsonl: acme 47, globex 8, zeta 10` and the candidate's line,
`documind-api-...-..., no traffic, the eval identity: acme 47, globex 8, zeta 10`. A no-traffic revision from an
earlier lesson within the last 24 hours shows too; it may stay.

### 3. `data/stream_refusal.txt` (step 6)

Within 30 minutes of the UI question, run the page's step 6 cell as written (it starts `TOKEN="$(tok "$API")" python - <<'PY'`)
and record it.

Expect `the stream:` and the model declining in words; `pool 20, backend vertex, model gemini-3.6-flash, tokens out N`;
`its usage row: answerable True, unanswerable_flag 0, confidence medium, pool 20`;
`29 fields; holding the question or the answer: none`; and
`your stream in the UI (acme): answerable True, unanswerable_flag 0, pool 20`. If the stream answered instead of
declining, record it and say so. `answerable False` means the pool was empty: check the pin, then run again.

### 4. `data/alert_series.txt` (step 7)

Within six hours of run 1, and a few minutes after run 3, run the page's step 7 cell as written and record it.

Expect the two filters as `alerts.tf` declares them, whitespace collapsed; both policies, in the API's order:
`'Unanswerable rate > 20% for a tenant': above 0.2 for 1800s` and `'API p95 latency > 3s': above 3000 for 300s`, each
with `enabled True` and its channel count; then the five-minute windows with questions. In run 1's windows globex and
zeta should be above 0.20 if the candidate refused as it should, and run 3's window should show acme's stream in
queries and not in unanswerable. If no window appears, the metrics have not caught up: wait five minutes and run again.
