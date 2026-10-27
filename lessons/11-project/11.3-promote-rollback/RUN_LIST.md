# Lesson 11.3 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/11-project/11.3-promote-rollback/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 11.3 && python pagekit/check_lesson.py 11.3 && python pagekit/audit_pages.py 11.3

Everything else on the page is computed when it builds, from the kit: the fifteen commands run through the Makefile's
own recipes (the kit test's MiniMake, in sh) against the kit test's stand-in gcloud, curl and make, with `release.py`
as make runs it (the step-1 stepper, the step-5 outputs, and what `make release-candidate` would make after the
rollback); `make incident`'s verdict after every command; the smokes table; the shape of the kit's tests; and the two
Python cells, each run against stand-ins. The build needs a POSIX `sh` (Git Bash on Windows), as the kit test's
recipe tests do.

## Before the first run

- **Batch 3 (Mon 16 - Wed 18 Nov 2026), in the same sitting as lesson 11.2's runs, straight after them.** These runs
  start from 11.2's state: its candidate (lesson 11.1's dispatch revision) tagged `candidate` with no traffic,
  `.candidate-revision` naming it, and 11.2's run 4 record (`evals/reports/gate.json`, green) in this checkout. A
  record holds for 24 hours: run 1 here within 24 hours of 11.2's run 4, or `make gate` again first (another gate,
  about Rs 29).
- **Where:** the operator shell (Cloud Shell), in the kit (`~/deploy_module_rag`), after the page's shared setup block,
  which exports `PROJECT`, `REGION=asia-south1`, `NUMBER` and `API` and defines `tok`.
- **acme stays pinned** to the kit's index, as for 11.2 (`make tenant-backend PROJECT=$PROJECT TENANT=acme
  RETRIEVAL_BACKEND=vector`), so both gates here judge with the rows 11.2 judged. Put the pin back
  (`RETRIEVAL_BACKEND=rag_engine`) after run 12.
- **Tokens:** `unset DOCUMIND_ID_TOKEN DOCUMIND_OUTSIDER_TOKEN` if an earlier lesson exported them.
- **Order, in one sitting:** runs 1 to 12 in this order. Run 4 makes the API answer 500 on purpose, until run 6 rolls
  it back: take runs 5 and 6 straight after it. Run 8 reads the template after the rollback and before the repair, so
  it goes between runs 7 and 9, not at the end with the other read.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. For run 6, include bash's `real`, `user` and `sys` lines: the manifest's proof is a rollback under two
  minutes.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, in URLs too
  (`https://documind-api-NUMBER.asia-south1.run.app`); commit shas `COMMIT` (the dispatch built the full 40-character
  commit: it is the image's tag and every revision's `GIT_SHA` here); your home directory `/home/you`; emails
  `you@your-company.com`. Revision names, digests, sha256 values and times may stay. `check_lesson.py` refuses a real
  project id, a project number in a URL or resource path, a personal mailbox, and every string in `.publish-deny`.
- **Optional pre-flight, Rs 0:** the kit's own tests of this lesson, stand-ins only, a few minutes:

```bash
python commands/tests/test_release_repair.py
```

  Expect a line of dots, `Ran 23 tests in ...s` and `OK` (with `skipped=2` only where no `sh` is installed).
- **The two Python cells were written without a lane to test them.** They ran against stand-ins when the page was
  built. If one fails, record what it printed and tell the page's editor: the cell is fixed in `build.py` (`CELLS`)
  and recorded again.

## The runs

| # | Batch | Data file | Page step | Time | Cost |
|---|---|---|---|---|---|
| 1 | 3 (Mon 16 - Wed 18 Nov 2026) | `data/promote_gated.txt` | 6, lesson 11.2's candidate promoted | seconds | Rs 0 |
| 2 | 3 | `data/candidate_typo.txt` | 6, the mistyped model as a candidate | about a minute | Rs 0: a revision with no traffic |
| 3 | 3 | `data/gate_typo.txt` | 6, the gate on it | about ten minutes | Rs 0 in model tokens |
| 4 | 3 | `data/promote_refused_forced.txt` | 6, refused, then forced | seconds | Rs 0 |
| 5 | 3 | `data/smoke_incident_red.txt` | 6, the smokes and the incident on the bad revision | several minutes | Rs 0 for the API's answers; the smokes' other calls |
| 6 | 3 | `data/rollback_timed.txt` | 6, the timed rollback | seconds | Rs 0 |
| 7 | 3 | `data/smoke_incident_after.txt` | 6, the smokes and the incident after the rollback | several minutes | about Rs 4.5; the smokes' other calls |
| 8 | 3 | `data/template_read.txt` | 6, the template read from Cloud Run's API | seconds | Rs 0: two Cloud Run Admin API reads |
| 9 | 3 | `data/candidate_gate_repair.txt` | 7, the repair candidate and its gate | about eleven minutes | about Rs 29 |
| 10 | 3 | `data/promote_repair.txt` | 7, the repair promoted | seconds | Rs 0 |
| 11 | 3 | `data/smoke_incident_proof.txt` | 7, the proof | several minutes | about Rs 4.5; the smokes' other calls |
| 12 | 3 | `data/errors_by_revision.txt` | 8, the request logs by revision | seconds | Rs 0: Cloud Logging reads |

**Total: about Rs 38, plus the smokes' other calls.**

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs
85 to the dollar, at the course's typical answer of 2,000 tokens in and 300 out (the figure lessons 4.3, 4.4, 11.1,
11.2 and 11.6 use): Rs 0.45 an answer.

- Run 9's gate asks the 65 golden rows as the roster member and the isolation rows again as the outsider;
  the outsider's 11 requests are refused at the roster before any model call, so 65 answers: about Rs 29, as in 11.2.
- Run 3's gate asks the same rows of the mistyped model. Every model call is refused by Vertex AI, which serves no
  model by that name and bills no tokens for it, and a row whose retrieval comes back empty never calls the model:
  Rs 0 in model tokens. Each row's query embedding and reranking, before the model call, are outside the price table
  (as they are in 11.2's figure).
- `make smoke-deployed` on a healthy revision asks at least 10 answers of documind-api (one each from smoke,
  smoke-mcp, smoke-agent and smoke-media, four from smoke-chat's brains, two from smoke-reindex; `build.py` checks the
  smoke scripts for these counts): about Rs 4.5 a run, for runs 7 and 11. Run 5's answers fail at the model and bill
  nothing. Every run also makes calls the price table does not hold: the three agent brains' and the A2A peer's own
  model calls, one generated image (smoke-media), and the indexing of smoke-media's and smoke-reindex's uploads. The
  kit's own pull request left the smokes' cost unverified; please note your billing for the smokes when you hand the
  files back, and `make usage PROJECT="$PROJECT" HOURS=2` after run 11 for the API's share.

So about Rs 38 for what the table prices (29 + 4.5 + 4.5). The plan's estimate for this lesson was Rs 75-145, and the
7 October review's Rs 60-110 for a gate; `build.py` checks these figures against the kit on every build.

The page's prose states what each recording should show, read from the kit's code and the stand-in run. If a
recording disagrees, the recording is right: say so, and the prose changes with it. The bash blocks below are the
page's cells, character for character (`build.py` refuses to build if they drift apart); the Python cells are long, so
their runs say "as written on the page".

### 1. `data/promote_gated.txt` (step 6)

```bash
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `gate-check`'s four lines (`gate record evals/reports/gate.json: documind-api-... passed at ..., N.N hours ago`,
the digest and `GIT_SHA`, the report's sha256, `.candidate-revision names it and the candidate tag is not on another
revision; judged by this checkout's ...`), then `make promote`'s
`>> serving before the flip: documind-api-... (deploy/.previous-revision - make rollback returns to it)` naming the
revision `make up` released, gcloud's traffic lines, `>> live: documind-api-...` naming 11.2's candidate, the
`/version` JSON with `"git_sha": "COMMIT"` and `gemini-3.6-flash`, and `exit 0`. If it says `REFUSED` and `stale`,
more than 24 hours have passed since 11.2's run 4: run `make gate` first, record that too, and tell the editor.

### 2. `data/candidate_typo.txt` (step 6)

```bash
make candidate PROJECT="$PROJECT" REGION="$REGION" GENERATOR_MODEL=gemini-3.6-flsh
```

Expect make's echo of the `gcloud run services update documind-api ... --no-traffic --tag candidate
--update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flsh|..."` command, gcloud's deploy lines ending with the revision
serving 0 percent of traffic, then `>> candidate revision: documind-api-... (deploy/.candidate-revision - make promote
moves traffic to it by name)` and `>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no
traffic; ...)`. **If the revision never becomes Ready, record it and tell the editor**: the kit expects it to start,
because nothing in the API checks the model's name at startup, and the whole drill depends on it.

### 3. `data/gate_typo.txt` (step 6)

```bash
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `>> gate: documind-api-..., the revision .candidate-revision names and the candidate tag routes to`, the image
and digest, `GET /version on https://candidate---documind-api-NUMBER.asia-south1.run.app: git_sha COMMIT,
gemini-3.6-flsh, documind-rag@v3`, `>> every golden row, asked of that URL by evals/run_eval.py; ...`, then
`run_eval.py`'s own lines, with requests failing (HTTP 500) and its `Blocked:` line, then `>> gate record:
evals/reports/gate.json`, `documind-api-...  FAIL  ...` naming `request_success_rate` (and, most likely,
`correct_rate`), `make promote-gated refuses it (make promote reads no record)`, make's
`make: *** [mk/release.mk:37: gate] Error 1` and `exit 2`. The stand-in assumes every row fails; on a lane a row whose
retrieval comes back empty answers without a model call, so the rates may be above 0%: record what it says. **If
make's line says `Error 2` (a `STOP:` line: the gate stopped instead of judging), tell the editor**: the kit expects a
red verdict on the rows (release.py exit 1), not a stop.

### 4. `data/promote_refused_forced.txt` (step 6)

```bash
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make promote PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `REFUSED: the gate record evals/reports/gate.json does not let make promote move traffic:` and
`  - red: the gate judged documind-api-... red (...)`, make's `make: *** [mk/release.mk:46: promote-gated] Error 1`,
`exit 2`; then `make promote`'s `>> serving before the flip: documind-api-...` naming 11.2's candidate, gcloud's
traffic lines, `>> live: documind-api-...` naming the mistyped revision, the `/version` JSON with `gemini-3.6-flsh`,
and `exit 0`. **From here the API answers 500: take runs 5 and 6 straight away.**

### 5. `data/smoke_incident_red.txt` (step 6)

```bash
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `>> smoke-deployed: documind-api in documind-ai-YOUR-ID, asia-south1, serving documind-api-...` (the mistyped
revision), `GET /version: git_sha COMMIT, gemini-3.6-flsh, documind-rag@v3`, `deployed: ...` (your services),
`>> N of smoke-all's 8 smokes; skipped, a service not deployed: ...` (6 of 8 on a lane without Module 9's gateway and
SLM, skipping smoke-gateway and smoke-slm), each smoke's `== name` and its PASS and FAIL lines (the API's smoke:
`[PASS] health`, `[FAIL] query  status=500 body=Internal Server Error`), `== name: FAILED (exit 1)` for each that
failed, `>> FAIL: ... failed; N passed, M skipped. Recorded in evals/reports/smoke-deployed.jsonl`, make's
`make: *** [mk/release.mk:60: smoke-deployed] Error 1`, `exit 2`. **Tell the editor which smokes failed and which
passed**: the kit's stand-in assumes every smoke that asks documind-api fails. Then `make incident`: the timeline (11.2's
candidate and the mistyped revision, each with its `GENERATOR_MODEL` and verdict, the red gate, the red smoke run),
`>> now`, `>> not the gated state:`, `- documind-api-... serves, and the gate judged it red (...)`,
`Repair: make rollback, which moves traffic back to documind-api-... (.previous-revision); then make incident again`,
make's `make: *** [mk/release.mk:71: incident] Error 1`, `exit 2`.

### 6. `data/rollback_timed.txt` (step 6)

```bash
time make rollback PROJECT="$PROJECT" REGION="$REGION"
```

Expect gcloud's traffic lines, `>> traffic on documind-api-...` naming 11.2's candidate, then bash's `real`, `user`
and `sys`. The Makefile's comment above `rollback` says fifteen seconds; the manifest's proof wants `real` under two
minutes. **Tell the editor the `real` figure.**

### 7. `data/smoke_incident_after.txt` (step 6)

```bash
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect the smokes on 11.2's candidate, `GET /version: git_sha COMMIT, gemini-3.6-flash, documind-rag@v3`, every smoke
that ran passing, `>> PASS: N passed, M skipped. ...`, `exit 0`. Then `make incident`: the timeline now with
`traffic   documind-api-... -> documind-api-...: seen between the smoke runs of ...` and the PASS smoke run, then
`>> not the gated state:` with two reasons, `spec.template is not what serves: GENERATOR_MODEL gemini-3.6-flsh in the
template, gemini-3.6-flash on ...` and `.candidate-revision names documind-api-..., which the gate judged red ...`,
`Repair: make candidate GENERATOR_MODEL=gemini-3.6-flash; then make gate; then make promote-gated`, make's Error 1
line, `exit 2`. **Copy the Repair line exactly.** If it names more than `GENERATOR_MODEL` (settings your serving
revision runs at other than the Makefile's defaults), run 9 uses that line in place of the page's `make candidate`
line: record it as run, and tell the editor.

### 8. `data/template_read.txt` (step 6)

The page's cell *the template, read from Cloud Run's API*, as written on the page (a Python heredoc that starts
`import os, warnings`), **between runs 7 and 9**. Expect up to four revisions, oldest first, each with its traffic,
tag, image and `GENERATOR_MODEL` (11.2's candidate at `100%`, the mistyped revision at `0%` with `tag candidate` and
`GENERATOR_MODEL=gemini-3.6-flsh`; each revision's image a digest, `api@sha256:` and 12 hex digits, the same on the two
made from `api:COMMIT`), the `spec.template` line with the tag `api:COMMIT` and `GENERATOR_MODEL=gemini-3.6-flsh`, then
`the template is NOT what serves: documind-api-... runs GENERATOR_MODEL=gemini-3.6-flash.` and the line after it. If a
revision's image shows a tag instead of a digest, or the cell stops on an HTTP error from `run.googleapis.com`, record
that and tell the editor.

### 9. `data/candidate_gate_repair.txt` (step 7)

```bash
make candidate PROJECT="$PROJECT" REGION="$REGION" GENERATOR_MODEL=gemini-3.6-flash
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

(Or the Repair line run 7 printed, if it differs.) Expect `make candidate`'s lines as in run 2, with
`GENERATOR_MODEL=gemini-3.6-flash` and a new revision's name, then the gate as in 11.2's run 4: `GET /version ...:
git_sha COMMIT, gemini-3.6-flash, documind-rag@v3`, `run_eval.py`'s lines (`65 rows (47 answerable, 18 not)`, nine
`[PASS]` lines, `All thresholds met.`), `>> gate record: evals/reports/gate.json`, `documind-api-...  PASS  65 rows,
eval exit 0, report sha256 ...`, the line about 24 hours, `exit 0`. If it is red, record it and tell the editor:
run 10 would refuse it.

### 10. `data/promote_repair.txt` (step 7)

```bash
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `gate-check`'s four lines naming the repair revision, `>> serving before the flip: documind-api-...` naming
11.2's candidate, `>> live: documind-api-...` naming the repair, the `/version` JSON with `gemini-3.6-flash`, `exit 0`.

### 11. `data/smoke_incident_proof.txt` (step 7)

```bash
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

The proof. Expect the smokes green on the repair revision, `>> PASS: ...`, `exit 0`; then `make incident`'s whole
timeline (the three revisions with their verdicts, the repair's gate, the three smoke runs and both traffic moves),
`>> now` (serving and the candidate tag on the repair revision, `.previous-revision` naming 11.2's candidate,
`spec.template ... GENERATOR_MODEL=gemini-3.6-flash`), `>> the gated state: documind-api-... serves, judged green
(evals/reports/gate.json); spec.template is what serves; no red candidate is recorded` and `exit 0`.

### 12. `data/errors_by_revision.txt` (step 8)

The page's cell *errors by revision, from the request logs*, as written on the page (a Python heredoc that starts
`import collections, datetime, os, warnings`), right after run 11. Expect one line per revision that answered in the
last three hours: 5xx only on the mistyped revision (from run 3's rows on its tag URL and run 5's smokes), with the
time span and the paths; none on 11.2's candidate or the repair. **A 5xx on any other revision is a finding: tell the
editor.** If the sitting took longer than three hours, run it with `HOURS=5 python - <<'PY' ...` and say so.

Last, put acme's pin back: `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=rag_engine`, and keep
the repair revision serving.
