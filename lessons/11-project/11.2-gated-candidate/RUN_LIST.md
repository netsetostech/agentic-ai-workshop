# Lesson 11.2 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/11-project/11.2-gated-candidate/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 11.2 && python pagekit/check_lesson.py 11.2 && python pagekit/audit_pages.py 11.2

Everything else on the page is computed when it builds, from the kit: `release.py gate` and `gate-check` run against
the kit test's own stand-in lane (a green gate and its record, a red gate, every refusal of `make gate` and of
`gate-check`), the step-1 panel (held equal to `gate-check` on hundreds of states), the Change-it (a copy of the
record naming another revision, refused before `make promote`), the shape of the kit's tests, and the four Python
cells, each run against stand-ins.

## Before the first run

- **Batch 3 (Mon 16 - Wed 18 Nov 2026), straight after lesson 11.1's runs.** These runs judge the candidate that
  11.1's run 4 (`data/run_main.txt`, its main dispatch) left on the lane: a revision of `documind-api` with no
  traffic and the tag `candidate`, made by `sa-documind-cicd`, with promote rejected. 11.1's run list ends "Keep the
  candidate revision": do not remove its tag, and make no other revision of `documind-api` in between (no
  `make candidate`, `make release-candidate`, `make up` or `make deploy-services`). If one was made, see run 2.
- **Where:** the operator shell (Cloud Shell), in the kit (`~/deploy_module_rag`), after the page's shared setup block,
  which exports `PROJECT`, `REGION=asia-south1`, `NUMBER` and `API` and defines `tok`. `gh` signed in as the fork's
  owner, as for 11.1 (run 1 only).
- **First:** pin acme to the kit's index, as the setup section says, so the gate runs as 11.1's dispatch ran its own:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Put the pin back
  (`RETRIEVAL_BACKEND=rag_engine`) after run 6, unless lesson 11.3's runs follow at once.
- **Tokens:** `unset DOCUMIND_ID_TOKEN DOCUMIND_OUTSIDER_TOKEN` if an earlier lesson exported them. `make gate` uses a
  token from the environment as it is, and an old one is refused.
- **Order, in one sitting:** runs 1 to 6 in the page's order. Lesson 11.3's gated promote reads run 4's record: a
  record holds for 24 hours, so run 11.3's promote within 24 hours of run 4, or run `make gate` again first (another
  gate, at the same price).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, in URLs too
  (`https://candidate---documind-api-NUMBER.asia-south1.run.app`); the repository `YOUR-GITHUB-USER/YOUR-REPO`; run
  and job ids `RUN_ID` and `JOB_ID`; commit shas `COMMIT` (the dispatch built the full 40-character commit: it is the
  image's tag and the revision's `GIT_SHA`); your home directory `/home/you`; emails `you@your-company.com`. Revision
  names, digests, sha256 values and times may stay. `check_lesson.py` refuses a real project id, a project number in a
  URL or resource path, a personal mailbox, and every string in `.publish-deny`.
- **The cells were written without a lane or a GitHub run to test them.** The Python cells ran against stand-ins when
  the page was built; the `gh` cell did not. If one fails, record what it printed and tell the page's editor: the cell
  is fixed in `build.py` (`CELLS`) and recorded again.

## The runs

| # | Batch | Data file | Page step | Time | Cost |
|---|---|---|---|---|---|
| 1 | 3 (Mon 16 - Wed 18 Nov 2026) | `data/ci_gate.txt` | 3, the dispatch's own lines | seconds | Rs 0: GitHub reads of 11.1's run 4, no new dispatch |
| 2 | 3 | `data/record_candidate.txt` | 5, the candidate named | seconds | Rs 0: one describe |
| 3 | 3 | `data/audience.txt` | 5, the tag URL and the audience | seconds | Rs 0: two token mints and four GETs, no model call |
| 4 | 3 | `data/gate.txt` | 5, `make gate` | about ten minutes | about Rs 29 |
| 5 | 3 | `data/record_vs_lane.txt` | 6, the record against Cloud Run | seconds | Rs 0: two Cloud Run Admin API reads |
| 6 | 3 | `data/gate_check.txt` | 6, `gate-check` alone | seconds | Rs 0: two describes |

**Total: about Rs 29.**

**Where the rupees come from.** `make gate` asks the 65 golden rows as the roster member, and the 11 isolation rows
again as the outsider; the outsider's 11 requests are refused at the roster before any model call, so at most 65
answers are paid for. `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs 85 to the
dollar, at the course's typical answer of 2,000 tokens in and 300 out (the figure lessons 4.3, 4.4, 11.1 and 11.6
use): Rs 0.45 an answer, so about Rs 29 for the gate. `build.py` checks these figures against the kit on every build.
The review of 7 October estimated Rs 60-110 for a gate, and the plan Rs 60-115 for this lesson's runs.
`make usage PROJECT="$PROJECT" HOURS=1` straight after run 4 prints the real figure; please note it when you hand the
files back.

**This is a second gate on the same candidate, not the one 11.1 paid for.** 11.1's run list says its run 4's gate "is
paid once" and that 11.2 reads the same run. With the kit's `make gate` (R2) that holds only for run 1 here, which
reads the CI gate's log at Rs 0. The CI gate keeps no record: `documind-cd.yml` runs `make eval-live` with no
`REPORT=` and passes only the revision's name to `promote`. `make gate` asks the rows again from the operator shell
because the record it writes (the digest, the report's sha256, the time) is the lesson. So the two lessons together
pay for two gates on one candidate, about Rs 58 in all.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it. The bash blocks below
are the page's cells, character for character (`build.py` refuses to build if they drift apart); the Python cells are
long, so their runs say "as written on the page".

### 1. `data/ci_gate.txt` (step 3)

Reads 11.1's run 4; no new dispatch.

```bash
GH_REPO="$(python -c 'import json; print(json.load(open("terraform/runbook-project.auto.tfvars.json"))["github_repository"])')"
RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
JOB="$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '.jobs[] | select(.name == "release-candidate") | .databaseId')"
echo "run $RUN, job release-candidate $JOB"
gh run view --job "$JOB" --repo "$GH_REPO" --log \
  | grep -E '>> candidate revision: |candidate /version git_sha=[^$]|== eval gate: LIVE ==| rows \(|\[(PASS|FAIL)\]|All thresholds met|Blocked:' \
  | sed -E 's/^[^\t]*\t([^\t]*)\t[^ ]* /\1: /'
```

Expect `run RUN_ID, job release-candidate JOB_ID`, then each kept line after its step's name:
`A candidate revision, no traffic: >> candidate revision: documind-api-... (deploy/.candidate-revision - make promote moves traffic to it by name)`,
`The candidate answers as the tag: candidate /version git_sha=COMMIT, releasing TAG=COMMIT`, and
`The live gate, on the candidate:` before `== eval gate: LIVE ==`, `65 rows (47 answerable, 18 not) against https://candidate---...`,
nine `[PASS]` lines and `All thresholds met.` If the run was not 11.1's run 4 (a later dispatch on `main`), set
`RUN` by hand to run 4's id and run the last three lines again. If `gh` prints `UNKNOWN STEP` in place of the step
names, or prints the lines with no step name at all, record them as they are and say so. If the cell prints only its
first line, record `gh run view --job "$JOB" --repo "$GH_REPO" --log | tail -n 60` instead and tell the editor.

### 2. `data/record_candidate.txt` (step 5)

The page's cell *name the candidate*, as written on the page (`make record-candidate`, then a Python heredoc that
starts `import json, os, subprocess, warnings`). Expect make's line
`>> candidate revision: documind-api-... (deploy/.candidate-revision - make promote moves traffic to it by name)`, the
traffic lines (the serving revision at `100%` with `tag -`, the candidate at `0%` with `tag candidate`), and
`.candidate-revision names documind-api-...; the candidate tag is on documind-api-...: the same revision`, naming the
revision run 1's `>> candidate revision` line named. If it says `NOT the same`, a revision was made after the dispatch:
tell the editor,
then make one candidate from the dispatch's commit, as the page's step-5 box says
(`make release-candidate PROJECT="$PROJECT" REGION="$REGION" GIT_SHA=` and the full commit run 1 printed), and record
this cell again.

### 3. `data/audience.txt` (step 5)

The page's cell *the tag URL and the audience*, as written on the page (a Python heredoc that starts
`import json, os, re, subprocess, urllib.error, urllib.request, warnings`). Expect, for the canonical URL's token,
`GET /version ... HTTP 200  git_sha COMMIT, gemini-3.6-flash, documind-rag@v3` and
`GET /v1/sources?tenant_id=acme ... HTTP 200  N sources of acme`; for the tag URL's token, a refusal on
`/v1/sources`. **Tell the editor what the tag URL's token got on `/version`.** The API's `version()` checks no token
itself, so that line is Cloud Run's front door alone: a `200` means Cloud Run accepts a tag URL as an audience and only
the API's own check (F42) refuses it; a `401` or `403` means the front door refuses it first. Note also the refusal on
`/v1/sources`: a `401` saying `invalid bearer token: ...` is the API's own check; an HTML page's text is Cloud Run's.
The page's step-5 prose is written for either and names the one your run shows.

### 4. `data/gate.txt` (step 5)

```bash
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
```

Expect `>> gate: documind-api-..., the revision .candidate-revision names and the candidate tag routes to`, the
`image` (`.../documind/api:COMMIT`), the `digest` (`.../documind/api@sha256:...`), `GET /version on https://candidate---documind-api-NUMBER.asia-south1.run.app: git_sha COMMIT, gemini-3.6-flash, documind-rag@v3`,
`>> every golden row, asked of that URL by evals/run_eval.py; the report: evals/reports/gate-documind-api-....json`,
then `run_eval.py`'s own lines as in lesson 4.3 (`== eval gate: LIVE ==`, `65 rows (47 answerable, 18 not)`, nine
`[PASS]` lines, the shape table, the latency lines, any rows that cost a point,
`report: /home/you/deploy_module_rag/evals/reports/gate-documind-api-....json`, `All thresholds met.`), then
`>> gate record: evals/reports/gate.json`, `documind-api-...  PASS  65 rows, eval exit 0, report sha256 ...`, the line
about 24 hours, and `exit 0`. If the gate is red, record it anyway (`FAIL` and what blocked it, make's
`Error 1` line and `exit 2`): the prose then needs the reason, and lesson 11.3's promote needs a green gate first. If it
stops before the rows (`STOP: ...`), record it and tell the editor which check stopped it. The `image` line is read
from the service's `spec.template`, because a revision holds only the digest: a stop saying
`documind-api's spec.template has made a later revision` means a revision was made after the dispatch's, as in run 2.
Two stops would be kit findings rather than lane faults, because R2's pull request lists both fields as not yet seen on
a lane:
`cannot be gated: it belongs to no service, not documind-api` (the revision's `serving.knative.dev/service` label) and
`Cloud Run reports no image digest for it (status.imageDigest)`. Either one blocks every gate until the kit reads the
field another way.

### 5. `data/record_vs_lane.txt` (step 6)

The page's cell *the record against the lane*, as written on the page (a Python heredoc that starts
`import hashlib, json, os, warnings`). Expect the record's line (`documind-api-...: pass, eval exit 0, 65 rows,
finished ...`), then 10 lines, each starting `same`: the file, the tag, the image digest, `GIT_SHA`, Ready, the report's
sha256 and the four rule files. **A `DIFFERS` line is a finding: tell the editor.** The cell reads the revision
through the Cloud Run Admin API's v1 REST resource, where `release.py` used `gcloud`: the same fields should agree. If
the cell stops on an HTTP error from `run.googleapis.com`, record that.

### 6. `data/gate_check.txt` (step 6)

```bash
python commands/release.py gate-check --project "$PROJECT" --region "$REGION"; echo "exit $?"
```

Expect `gate record evals/reports/gate.json: documind-api-... passed at ..., N.N hours ago`, the `digest` and `GIT_SHA`
line, the `report` and `sha256` line,
`.candidate-revision names it and the candidate tag is not on another revision; judged by this checkout's evals/run_eval.py, evals/golden.jsonl, evals/required.json, evals/manifest.json`,
and `exit 0`. Nothing moves: this is the first line of `make promote-gated` without the second.

The page's Change-it (step 7) is computed when it builds and is not recorded: it moves no traffic on any lane, but there
is no need to run it here. Last, put acme's pin back:
`make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=rag_engine`, unless lesson 11.3's runs follow at once.
Keep the candidate, its tag and the record: lesson 11.3 promotes exactly this revision with `make promote-gated`.
