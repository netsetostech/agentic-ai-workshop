# Lesson 12.4 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/12-tuning/12.4-self-improving/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 12.4 && python pagekit/check_lesson.py 12.4 && python pagekit/audit_pages.py 12.4

Everything else on the page is computed when it builds, offline, from the kit: the row cell over a stand-in answer;
`improve.py`'s own `main()` on a copy of the kit for `--prompt-only`, a row whose figure is not in the documents, a
"never refuse" rule (refused), a scripted proposal (the kit test's way) and accept; the paste cell, `build_golden.py`
and `make eval` over the new row; `improve.py version`; the import-time refusal of an unlisted version; `write()`
refusing the evaluator; `make prompt-version` before and after v4; the validator and byte-identity cells on the kit;
and the step 1 panel, whose check is compared with `prompt_rules.problems()` on every case it was built with.

## Before the first run

- **Batch 4 (Mon 23 - Wed 25 Nov 2026), on a lane that has run lessons 11.2 and 11.3.** The kit needs R6
  (`make improve`, `make prompt-candidate`) and R2 (`make gate`, `make promote-gated`, lesson 11.2) merged, and the
  kit checkout must be a git repository you can commit to (your fork, as in lesson 11.1).
- **A question that really fails on the lane.** The lesson needs a question that the live revision, under v3,
  answers wrongly from acme's documents. Find it before recording anything: ask on the UI, each try one answer at
  about Rs 0.45. Try the page's example first ("I am still on probation. If I resign now, how long is my notice?":
  PB-02 says 15 days during probation, NP-03 says 60 days for a confirmed E3); if the lane answers it right, try
  other questions near the handbook's clauses, in your own words and not word for word a row of `golden.jsonl`. When
  one fails, put it in step 3's `Q=` and set `WRONG`, `SHAPE`, `CONTAIN` and `RETRIEVE` in the row cell with facts
  that are in acme's documents (`make improve` refuses any that are not, before the model call). Tell the page's
  editor which question failed and how: the page's prose about the example stays a stand-in, and the recordings are
  the real case.
- **Where:** the operator shell (Cloud Shell), in the kit (`~/deploy_module_rag`), after the page's shared setup
  block, which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API` and defines `tok`.
  Pin acme to the kit's index first, as the setup section says, so the gate runs as lesson 11.2's did:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Put the pin back
  (`RETRIEVAL_BACKEND=rag_engine`) after run 8.
- **Tokens:** `unset DOCUMIND_ID_TOKEN DOCUMIND_OUTSIDER_TOKEN` if an earlier lesson exported them: `make gate` uses
  a token from the environment as it is.
- **Order, in one sitting:** runs 1 to 8 in the page's order, with no other revision of `documind-api` made in
  between (no `make candidate`, `make release-candidate`, `make up` or `make deploy-services`). Promote straight after
  the gate, while its record holds (lesson 11.2). Run 9 is optional and comes last.
- **What to record:** what the terminal shows for the cell, stdout and stderr together (make's echo lines and its
  `***` lines are part of the lesson), with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, in URLs too
  (`https://candidate---documind-api-NUMBER.asia-south1.run.app`); commit shas `COMMIT` (the image tag, the
  revision's `GIT_SHA` and `git log` lines); your email `you@your-company.com` (`REVIEWER="$ME"` prints it in runs
  3 and 9, and it goes into `prompt_rules.json`); your home directory `/home/you`. Revision names, digests, sha256
  values, dates and times may stay. `check_lesson.py` refuses a real project id, a project number in a URL or
  resource path, a personal mailbox, and every string in `.publish-deny`.
- **The cells were written without a lane to test them.** The Python cells ran when the page was built (the usage
  cell over stand-in rows, with `gcloud` never called); the bash cells did not. If one fails, record what it printed
  and tell the page's editor: the cell is fixed in `build.py` (`CELLS`) and recorded again.

## The runs

| # | Batch | Data file | Page step | Cost |
|---|---|---|---|---|
| 1 | 4 (Mon 23 - Wed 25 Nov 2026) | `data/production_row.txt` | 3, the question, `/version` and the usage row | one answer here and one on the UI: about Rs 0.89 for the two |
| 2 | 4 | `data/proposal.txt` | 5, `make improve ROW=` | about Rs 2 (one gemini-3.1-pro-preview call; it prints its own rupees) |
| 3 | 4 | `data/accept.txt` | 6, accept, the paste, `build_golden.py`, `make eval` | Rs 0 |
| 4 | 4 | `data/prompt_candidate.txt` | 7, commit, `make build`, `make prompt-candidate` | Rs 0 in model tokens, one Cloud Build |
| 5 | 4 | `data/gate_v4.txt` | 7, `make gate` | 66 golden rows on the candidate: about Rs 29 |
| 6 | 4 | `data/before_after.txt` | 8, the live URL and the tag URL | two answers: about Rs 0.89 |
| 7 | 4 | `data/outcome.txt` | 9, `make promote-gated` (or the revert) | one answer after a promote: about Rs 0.45 |
| 8 | 4 | `data/usage_delta.txt` | 10, the usage rows by version | Rs 0 |
| 9 | 4, optional | `data/gate_past.txt` | 11, a rule worded past the phrases, gated | about Rs 29 |

Runs 1 to 8 come to about Rs 34 (five answers outside the gate at Rs 0.45 each, the proposal and the gate, at the
course's typical answer of 2,000 tokens in and 300 out); about Rs 63 with run 9. Each extra try at a failing
question in run 1 adds about Rs 0.45, and a second proposal (if the first is refused) about Rs 2.

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/production_row.txt` (step 3)

Ask the failing question on the UI first (the answer your users get), then run the page's first step-3 cell with
your question in `Q=`. Record the cell only.

Expect `serving: documind-rag@v3 | gemini-3.6-flash | git_sha COMMIT`, `answerable:` and the citation count, the
lane's wrong answer, then `usage row:` with `'event': 'query'`, `'tenant': 'acme'`, `'prompt_version': 'v3'`, the
model and tokens, and `the question in the row: False`. Then run the row cell (not recorded) with your values.

### 2. `data/proposal.txt` (step 5)

```bash
make improve ROW="$HOME/row124.json" PROJECT="$PROJECT"
```

Expect make's echo, then `row:`, `expected:`, `builds on: v3, SYSTEM's 5 rules and 0 added`, `proposer:
gemini-3.1-pro-preview on global: N in, N out (N of them thinking), Rs N at list price (shared/prices.py)`, `rule:
6. ...`, `why: ...`, `checks: ... passed` and `wrote /home/you/deploy_module_rag/evals/reports/proposal.json`. If the
model's rule is refused (`REFUSED:` lines, exit 1), record that run too, as `data/proposal_refused.txt`, tell the
page's editor, and propose again. Unverified until this run: the google-genai call shape (`response_json_schema`, the
retry options) and the default thinking's cost.

### 3. `data/accept.txt` (step 6)

Read `evals/reports/proposal.json` first. Then run the accept cell (`make improve REVIEWER="$ME" | tee
~/accept124.txt`, then `git status --short`), the paste cell and `python evals/build_golden.py && make eval`, and
record all three in one file.

Expect `accepted:  documind-rag@v4, v3's 0 added rules and this one, by you@your-company.com on <date>`, the rule as
`6. ...`, `wrote services/rag-api/prompt_rules.json`, the golden row (the next id of its shape: `lk-32` for a lookup),
the `Then:` lines, and ` M services/rag-api/prompt_rules.json` as the only `git status` line. Then
`evals/build_golden.py: the golden row is line N`, the builder's report with `rows : 66` and every
`must_contain / must_retrieve verified ... OK`, `python evals/run_eval.py`, three `[PASS]` lines and `The golden set
is sound.`

### 4. `data/prompt_candidate.txt` (step 7)

Run the page's step-7 candidate cell as written. Expect the commit's `git log --oneline` line, the last lines of
`make build`'s Cloud Build log, then `make prompt-candidate`'s `documind-rag@v4: SYSTEM's 5 rules and 1 added,
accepted by you@your-company.com on <date>` with the rule, gcloud's update lines, `>> candidate revision:
documind-api-...`, `>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app answers as v4 (make
gate, then make promote-gated)` and `on the revision: PROMPT_VERSION v4 | GIT_SHA COMMIT`. Unverified until this run:
the v4 revision starting (an image without v4 refuses to start, by design).

### 5. `data/gate_v4.txt` (step 7)

```bash
make gate PROJECT="$PROJECT" REGION="$REGION"
```

Expect lesson 11.2's gate: `>> gate:` with the candidate, its image and digest, `GET /version on
https://candidate---documind-api-NUMBER.asia-south1.run.app: git_sha COMMIT, gemini-3.6-flash, documind-rag@v4`, the
`run_eval.py` report over `66 rows (48 answerable, 18 not)` for a lookup or join row (`66 rows (47 answerable, 19 not)`
for a refusal row), the thresholds, `>> gate record:` and the verdict line, `PASS` or `FAIL`. `refusal_rate` is judged
over the 18 rows the documents cannot answer (19 with a refusal row), not the 8 refusal rows accept's line names.
Unverified until this run: lesson 11.2's gate accepting a `make prompt-candidate` revision.

### 6. `data/before_after.txt` (step 8)

Run the page's step-8 cell as written. Expect `== https://documind-api-NUMBER.asia-south1.run.app`, `prompt:
documind-rag@v3`, the live answer (as wrong as in run 1), then `== https://candidate---...`, `prompt:
documind-rag@v4` and the candidate's answer. If the candidate's answer is still wrong, record it, do not promote,
and tell the page's editor.

### 7. `data/outcome.txt` (step 9)

Green gate: run the promote cell. Expect `gate-check`'s lines, `>> serving before the flip: ...`, the traffic update,
`>> live: <the candidate>`, `/version` with `"prompt":"documind-rag@v4"`, then `live now, answerable: True | answer:
...` with the right answer. Ask the question on the UI once more and tell the page's editor what it showed.
Red gate: run the revert cell instead and record it: the revert commit, the build's last lines and the v3 candidate.

### 8. `data/usage_delta.txt` (step 10)

Run the page's step-10 cell within three hours of run 5. Expect the answer count, the `by prompt version` table with
a `v3` line and a `v4` line (the gate's 66 answers among v4's), the newest row of each, `tokens_in, v4 minus v3:`
near the estimate on the last line (if nothing else asked the API between runs 6 and 8), and the estimate line.

### 9. `data/gate_past.txt` (step 11, optional)

Run the page's step-11 cell as written (it reads the version accept wrote as `PAST`), record it, then run the cleanup
cell after it (not recorded; set `PROMPT_VERSION=v3` there if run 7 reverted `$PV`). Expect the check to pass the rule (`checks: ... passed`), accept to write the
next version (do not paste its golden row), the candidate, and a gate. Of the 18 rows the documents cannot answer, if
the model now answers 2 of them or more, `refusal_rate` falls under 90% and the gate is red. If the gate passes it
anyway, record it as it is: the page says what that means.
