# Lesson 0.4 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/00-setup/0.4-prove-switch-off/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 0.4 && python pagekit/check_lesson.py 0.4 && python pagekit/audit_pages.py 0.4

## Before the first run

- **The lane:** deployed by lesson 0.3's `make plan` / `make up` in the one shape (`MANAGED_SEARCH=true`,
  `MIN_INSTANCES=0`, nothing from Module 9 deployed), with `make ingest-corpus` done. On the lane, runs 1 to 11
  change nothing but documind-ui's floor (already 0) and acme's pin (put back in run 8); run 7 writes files in your
  home directory. Run 12 is destructive: record it last.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER`,
  `API` and defines `tok`.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector` (the smoke's vector-tier line asserts
  only on `vector`).
- **What to record:** what the terminal shows for the cell, stdout and stderr together (make's `***` and `(ignored)`
  lines are part of the lesson), with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`;
  home directory `/home/you`; commit shas `COMMIT`; the state bucket `documind-ai-YOUR-ID-tfstate`. Revision names
  and times may stay. `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a
  personal mailbox, and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/preflight.txt` | 4, make preflight | under a minute | none: reads only |
| 2 | `data/smoke_green.txt` | 5, make smoke with the tenant | about a minute | one Gemini answer |
| 3 | `data/smoke_broken.txt` | 6, make smoke without the tenant | about a minute | none beyond the calls (the question is refused before retrieval) |
| 4 | `data/roster_read.txt` | 6, the two rosters from Firestore | seconds | two Firestore reads |
| 5 | `data/rest_reads.txt` | 7, /health, /ready, /version, and /health with no token | seconds | none |
| 6 | `data/state_inputs.txt` | 8, the state object and the inputs' names | seconds | none |
| 7 | `data/save_session.txt` | 8, rag_save_session | seconds | none: local files |
| 8 | `data/off.txt` | 9, make off | one to two minutes | none |
| 9 | `data/zero_instances.txt` | 9, instance_count after the idle window | about 16 minutes (15 of them waiting) | none: one Monitoring read |
| 10 | `data/standing_resources.txt` | 10, the listings of what bills by the hour | seconds | none |
| 11 | `data/resume.txt` | 11, rag_resume in a new shell | about a minute | none (the API wakes for three GETs) |
| 12 | `data/down.txt` | 12, make down | about five minutes | destructive (see the run) |

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/preflight.txt` (step 4)

```bash
export TFSTATE_BUCKET="${TFSTATE_BUCKET:-$PROJECT-tfstate}"
make preflight PROJECT="$PROJECT" TFSTATE_BUCKET="$TFSTATE_BUCKET" REGION="$REGION"
```

Expect eleven `ok` lines, `preflight clean - next: make plan, then make up` and the consent-screen line. If your state
bucket has another name, export it first; the page tells learners the same.

### 2. `data/smoke_green.txt` (step 5)

```bash
make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT" DOCUMIND_TENANT="$TENANT"
```

Expect make's echo `python smoke/smoke.py`, then `[PASS]` for health, ready, query, vector tier and no token refused,
`[ -- ] semantic cache ... skipped`, the two `[info]` BigQuery lines, and `5 pass · 0 fail`.

### 3. `data/smoke_broken.txt` (step 6)

```bash
env -u DOCUMIND_TENANT make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT"; echo "exit status: $?"
```

Expect `[PASS] health`, `[PASS] ready`, `[FAIL] query  status=403 body={"detail":"not a member of this tenant"}`, no
vector-tier line, `[PASS] no token refused`, the semantic-cache skip, the `[info]` lines, `3 pass · 1 fail`,
`make: *** [Makefile:523: smoke] Error 1` and `exit status: 2`.

### 4. `data/roster_read.txt` (step 6)

```bash
for t in tenant-smoke acme; do echo "== $t"; GOOGLE_CLOUD_PROJECT="$PROJECT" python -m shared.tenancy list "$t"; done
```

Expect nothing under `== tenant-smoke`; under `== acme`, the agent, chat, mcp and ui service accounts and your email.
Replace the email and the project id.

### 5. `data/rest_reads.txt` (step 7)

```bash
for p in health ready version; do echo "GET /$p"; curl -s -w '\nHTTP %{http_code}\n' "$API/$p" -H "Authorization: Bearer $(tok "$API")"; done
curl -s -o /dev/null -w 'GET /health with no token: HTTP %{http_code}\n' "$API/health"
```

Expect three `HTTP 200`, `/version` with `retrieval_backend` `vector` and your `git_sha` (replace it with `COMMIT`), and
`HTTP 403` with no token (Cloud Run's documented status for an unauthenticated request).

### 6. `data/state_inputs.txt` (step 8)

```bash
gcloud storage ls -l "gs://$TFSTATE_BUCKET/**/default.tfstate"
python -c 'import json; print(sorted(json.load(open("terraform/runbook-project.auto.tfvars.json"))))'
```

Run it on the machine that ran `make plan`. Expect one `default.tfstate` line and the TOTAL line, then the six names
`['billing_account_id', 'deploy_ref', 'github_repository', 'github_repository_id', 'project_id', 'region']`.

### 7. `data/save_session.txt` (step 8)

If `rag_save_session` stops with `Missing rag-source-session.env`, run the page's first-time block (step 8) once,
then this:

```bash
source commands/session-restart.sh
export PROJECT_NUMBER="$NUMBER" OPERATOR_EMAIL="$ME"
rag_save_session
sed 's/=.*//' ~/rag-resume.env; stat -c '%a %n' ~/rag-resume.env
```

Expect `PASS: saved nonsecret restart settings to /home/you/rag-resume.env`, the `export NAME` lines (an offline run of
the same cell in a sandbox printed eleven: PROJECT, REGION, OPERATOR_EMAIL, PROJECT_NUMBER, DEMO_ROOT, SOURCE_BRANCH,
SOURCE_COMMIT, GIT_SHA, RAG_SOURCE_REPO, RAG_SOURCE_BACKUP, TFSTATE_BUCKET) and `600 /home/you/rag-resume.env`. Tell
the page's editor whether the first-time block was needed on your machine.

### 8. `data/off.txt` (step 9)

```bash
make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=rag_engine   # the setup's pin back: not recorded
make off PROJECT="$PROJECT" REGION="$REGION"
```

Record `make off` only. Expect slm-off, vllm-off and gateway-off to fail on absent services with make's `(ignored)`
notes, documind-ui's update, gke-down's `vLLM workload removed; ...` line, then `documind-slm: min-instances absent`,
`documind-vllm: min-instances absent`, `documind-gateway: min-instances absent`, `documind-ui: min-instances 0`.

### 9. `data/zero_instances.txt` (step 9)

Run the page's step 9 cell as written (`sleep 900`, then the Python heredoc), straight after run 8, with no request to
the lane in between: no UI tab, no curl, no smoke. Expect every service `no instance in the window` or a last instance
more than three minutes old, and `services with an instance in the last 3 minutes: none - zero instances`.

### 10. `data/standing_resources.txt` (step 10)

Run the page's step 10 cell as written (seven read-only gcloud listings). Expect the deployed index on `e2-standard-16`
with one replica and `SHARD_SIZE_MEDIUM` (or `e2-standard-2` and `SHARD_SIZE_SMALL`: the page covers both), Spanner
`regional-asia-south1`, `ENTERPRISE`, `100`, two `db-f1-micro` instances, the cluster in `asia-south1` (regional) with one
`e2-standard-2` node on `pd-standard` 30, the connector on `e2-micro` with min 2. These field paths were written without
a gcloud to test them: if a column comes back empty, fix the projection in `build.py` (`CELLS["standing"]`) and record
again.

### 11. `data/resume.txt` (step 11)

In a new shell, without the setup block:

```bash
cd ~/deploy_module_rag && source commands/session-restart.sh && rag_resume
echo "PROJECT=$PROJECT REGION=$REGION API_URL=$API_URL"
```

Expect the dependency PASS lines, the Terraform PASS (or its warning), `PASS: Python ADC refreshed for quota project
documind-ai-YOUR-ID`, `PASS: restored project documind-ai-YOUR-ID and original source snapshot COMMIT`, `Serving
revision: ...`, `API_URL=https://documind-api-NUMBER.asia-south1.run.app`, `PASS: both identity tokens refreshed.`, the
three GETs with `HTTP 200`, `PASS: API health, readiness and version requests succeeded.`, the closing hint, and the
echo with your saved project and `asia-south1`. A dependency STOP is fixed by `rag_install_python_dependencies` (it adds
numpy and rank-bm25, which the setup section's pip line does not install); record after the fix.

### 12. `data/down.txt` (step 12): destructive, last

Only on a lane you are finished with: it deletes every Cloud Run service and the two RAG Engine corpora.

```bash
make down PROJECT="$PROJECT" REGION="$REGION"
```

Expect the cache lines, `candidate tag: none to remove`, `deleted documind-...` for the seven services and `absent`
for documind-gchat, documind-gateway, documind-slm and documind-vllm, the corpora deleted and both pins set to
`default`, terraform init, then `Error: Instance cannot be destroyed` for `google_discovery_engine_data_store.tenant`
(acme and zeta), the list's eight `>>` lines, and make's non-zero exit. The Terraform resources then still exist and
still bill; `gcloud projects delete` (or `make plan` and `make up` again, lesson 0.3) is yours to choose.
