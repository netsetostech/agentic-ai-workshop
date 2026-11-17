# Lesson 4.5 run list: the author's runs the page still needs

The page builds without them. Until a file below exists in `lessons/04-evals-safety/4.5-judge-vs-people/data/`, every
output that needs it shows a marked stand-in, `[awaiting the author's run: data/NAME]`, and so does the second
agreement board (step 5). Record each file once, replace every identifier with the course's placeholders, then rebuild
and check:

    python pagekit/build.py 4.5 && python pagekit/check_lesson.py 4.5 && python pagekit/audit_pages.py 4.5

Everything else on the page is computed when it builds, from the kit, at Rs 0: `agreement.py --selftest` and the
kit's `test_agreement.py`; the first agreement board, on the kit's judge fixtures (`evals/tests/judge_fixtures/`),
whose arithmetic node must reproduce; and the two standard-library cells, run on the fixtures. Once the files below
are recorded, the build also runs every learner command the page prints (`make label-sheet`, `--check`, `make
judge-agree` with and without `PEOPLE=1`, `CUT=3 SWEEP=1`) over them, with the kit's own code, so those expected
outputs are exact, not recorded.

## Six files, two homes

Four of the files are the kit's own data as well as the page's. The kit's make targets already name them
(`mk/evaluation.mk`), and `deploy/UNOWNED.md` lists them as absent by design until these runs:

| File | `data/` (the page) | `deploy/evals/` (the kit, through a kit PR) |
|---|---|---|
| `judge_set.json` | yes | yes: `make label-sheet`, `make judge-frozen` and `make judge-agree` read it |
| `judge_set.ratings.jsonl` | yes | yes: `make judge-agree`'s default `RUN=` |
| `judge_labels.L1.csv` | yes | yes: `make judge-agree PEOPLE=1`'s default `AGAINST=` |
| `judge_labels.L2.csv` | yes | yes: the page's step 4 names it with `AGAINST=` |
| `freeze.txt` | yes | no |
| `judge_frozen.txt` | yes | no |

Copy the same bytes to both places. The build refuses a `data/` file that differs from the kit's copy, and says which
kit file is still missing. Commit the four kit files only after reading every frozen row (run 3).

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and `make roster` run. Run 2
  makes one `documind-api` revision with no traffic, and removes its tag at the end. Nothing else serves differently.
- **The judge's venv:** lesson 4.2's `~/judge-venv` (`google-cloud-aiplatform[evaluation]==2.1.0`, pandas,
  google-cloud-firestore), checked with `"$HOME/judge-venv/bin/python" evals/judge.py --selftest`.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson
  1.1's), which exports `PROJECT`, `REGION=asia-south1`, `NUMBER` and `API`. `mkdir -p evals/reports` first.
- **What to record:** for `freeze.txt` and `judge_frozen.txt`, what the terminal shows, stdout and stderr together,
  with nothing trimmed but secrets and the SDK's redrawn progress bars (say so if you trim them). The other four files
  are copied as the kit wrote them.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; home directory `/home/you`. make echoes
  `judge-frozen`'s recipe with the project id and the venv's path, so `judge_frozen.txt` needs both replaced.
  `--freeze` refuses a row that names a lane (a project number or id, a personal mailbox), and every reader id is
  pseudonymous (`L1`, `L2`). Grep anyway before you copy: `grep -n "$NUMBER\|$PROJECT" freeze.txt judge_frozen.txt`.
  `check_lesson.py` refuses a real project id, a project number in a URL and every string in `.publish-deny`.

## The runs

| # | Batch | Data file | Page step | Time | Cost |
|---|---|---|---|---|---|
| 1 | 1 | none: `evals/reports/judge45_rows.jsonl`, for run 3 | 8 | as lesson 4.2's `make judge` (its first live run spent seventeen minutes collecting) | 65 answers on gemini-3.6-flash, at most about Rs 29.01, plus 130 Evaluation requests |
| 2 | 1 | none: `evals/reports/cand45_rows.jsonl`, for run 3 | 8 | the same again | 65 answers on gemini-3.1-flash-lite, at most about Rs 5.25, plus 130 Evaluation requests |
| 3 | 1 | `data/freeze.txt` and `data/judge_set.json` | 3 to 8 | seconds, then reading 20 rows | Rs 0 |
| 4 | 1 | `data/judge_frozen.txt` and `data/judge_set.ratings.jsonl` | 5, 6 | a few minutes | 40 Evaluation requests, no answers |
| 5 | 2 | `data/judge_labels.L1.csv` | 3 to 7 | the author's reading of 20 rows | Rs 0 |
| 6 | 2 | `data/judge_labels.L2.csv` | 4, 5, 7 | one peer's reading of 20 rows | Rs 0 |

**Total: about Rs 34.26 of model answers, plus 300 Vertex AI Evaluation requests**, which the kit does not price: read
them off the bill. The lesson plan's figure for batch 1 was about Rs 41.

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens,
gemini-3.1-flash-lite at $0.25 and $1.50, Rs 85 to the dollar, priced at the course's typical answer of 2,000 tokens
in and 300 out (as lessons 4.3, 4.4 and 11.6 price one): Rs 0.45 an answer on flash and Rs 0.08 on flash-lite, so Rs
29.01 and Rs 5.25 for the 65 golden rows each. "At most": a refusal row whose pool comes back empty is refused by code,
with no model call. `make judge` asks every golden row as `documind-ui-sa`, a member of all three rosters, so no row
is refused at the roster. `build.py` prints these figures and names any this file no longer states.

The page's prose says what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. The live revision's answers, rated (batch 1)

```bash
mkdir -p evals/reports
make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" \
  JUDGE_ARGS="--reuse evals/reports/judge45.json --save-rows evals/reports/judge45_rows.jsonl --label judge45"
```

Not recorded for the page. `--save-rows` is what `--freeze` reads: a `--no-vertex` collection holds the quotes, not
the context the judge read, and `--freeze` refuses it, so the capture has to go through the Evaluation service.
`--label judge45` names the Experiments run `api-judge45-...`, so no commit sha reaches `freeze.txt`. Expect `65/65
answers collected`, `context: N/N cited chunks read in full from the store`, the pointwise line naming
`GROUNDEDNESS + INSTRUCTION_FOLLOWING`, and `per-row ratings: 65 rows written to evals/reports/judge45_rows.jsonl`
(fewer if a row did not come back 200: say so). If the Evaluation step stops, run the same command again: `--reuse`
judges the same answers without asking the lane again.

### 2. A flash-lite candidate's answers, rated (batch 1)

```bash
make candidate PROJECT="$PROJECT" GENERATOR_MODEL=gemini-3.1-flash-lite
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API="$CAND" \
  JUDGE_ARGS="--reuse evals/reports/cand45.json --save-rows evals/reports/cand45_rows.jsonl --label cand45"
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision
```

Not recorded for the page. The candidate is lesson 4.4's: one setting changed, no traffic, its tag removed at the end
(`make promote` follows `.candidate-revision`, so the file goes too). A cheaper model refuses or drops figures more
often, which gives `--freeze` the natural failures a healthy live revision may not: it wants a third of the rows to
fail the gate's own rules. Expect `65/65 answers collected from https://candidate---...` with `model
gemini-3.1-flash-lite`, and `per-row ratings: 65 rows written to evals/reports/cand45_rows.jsonl`.

### 3. `data/freeze.txt` and `data/judge_set.json` (batch 1; steps 3 to 8)

```bash
python evals/build_judge_set.py --freeze evals/reports/judge45_rows.jsonl flash-lite=evals/reports/cand45_rows.jsonl 2>&1 | tee freeze.txt
```

Copy `freeze.txt` and `evals/judge_set.json` into `data/`, and `evals/judge_set.json` into `deploy/evals/` in a kit
PR. Expect the two captures (`(live): 65 rows rated, run api-judge45-...` and `(flash-lite): ...`), `picked 20 of N
answers, one per question, without the judge's ratings:`, the natural failures by kind, the constructed rows (`so
groundedness has N rows expected to fail`), the passing rows by shape, and `wrote evals/judge_set.json: 20 rows, no
judge score.` with each constructed row's added sentence. A line starting `fewer than a third` or `only N of`
means the captures held too few failures: record it, and say so. **Read every frozen row before anything is
labelled or committed**, the constructed ones above all: each must read as an answer with one unsupported sentence,
and no row may carry anything you would not publish. To freeze again, `--force`; every sheet and rating on the old set
goes stale.

### 4. `data/judge_frozen.txt` and `data/judge_set.ratings.jsonl` (batch 1; steps 5 and 6)

```bash
make judge-frozen PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" RUN=evals/judge_set.ratings.jsonl 2>&1 | tee judge_frozen.txt
```

Copy `judge_frozen.txt` and `evals/judge_set.ratings.jsonl` into `data/`, and the ratings into `deploy/evals/` in the
same kit PR. Expect make's echo of the recipe (`/home/you/judge-venv/bin/python evals/judge.py --api-url
frozen:evals/judge_set.json --project documind-ai-YOUR-ID --reuse evals/judge_set.json --no-enrich --label frozen
--save-rows evals/judge_set.ratings.jsonl`), then `20 rows reused from evals/judge_set.json`, `20/20 answers collected
from frozen:evals/judge_set.json`, `context: as each row holds it (--no-enrich: no store read)`, `trajectories: off`,
the pointwise line with the templates' hash (lesson 4.2 recorded `cd7070` for SDK 2.1.0), `pairwise: off`, `judge:
the service default`, `per-row ratings: 20 rows written to evals/judge_set.ratings.jsonl`, the Experiments run
`documind-eval/api-frozen-YYYYMMDD-HHMM-t...` with its means, and the gate's closing line. The build reads the ratings
with `judge_agree.py`'s own reader: it stops on a groundedness score other than 0 or 1, a second metric outside 1 to
5, or a rating whose answer is not the frozen one.

### 5. `data/judge_labels.L1.csv`: the author's labels (batch 2; steps 3 to 7)

```bash
make label-sheet LABELS=evals/judge_labels.L1.csv READER=L1
# label all 20 rows, both columns, with a note wherever you hesitate, before reading the judge's ratings
python evals/build_judge_set.py --check evals/judge_labels.L1.csv
```

Copy the checked sheet into `data/` and into `deploy/evals/`. The author froze the set and read its constructed rows
in run 3, so these labels are not blind on groundedness; the peer's are. The page says the peer labelled blind.
Expect `evals/judge_labels.L1.csv: 20 rows labelled by L1 - groundedness ... yes, ... no; answers_the_question ...
yes, ... no; ... with a note. Ready for judge_agree.py.`

### 6. `data/judge_labels.L2.csv`: one peer's labels (batch 2; steps 4, 5 and 7)

```bash
make label-sheet LABELS=evals/judge_labels.L2.csv READER=L2
python evals/build_judge_set.py --check evals/judge_labels.L2.csv
```

Decision 15 of the lesson plan: one peer labels the 20 rows once. Give the peer the empty sheet and the guide that
`make label-sheet` prints, and nothing else: not `freeze.txt`, not the author's sheet, not the ratings. Copy the
checked sheet into `data/` and into `deploy/evals/`. The reader id stays `L2`: the sheet ships in a public kit.

When all six files are in, rebuild. The build prints `author's files: recorded`, the second board appears in step 5,
and the build's `note:` lines name any kit file still missing.
