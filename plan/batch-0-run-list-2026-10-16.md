# Batch 0 run list: Mon 19 to Wed 21 October 2026

*For the author. Batch 0 of `plan/cohort-2-lesson-plan-2026-10-07.md` (section 6): Module 0 from a blank project, the
three Basics pages that call Google, and lesson 10.9's Agent Engine probe. Written on 12 October 2026 against `main`
at `a808716`, which holds the deploy fixes (#103), the local-lane fixes (#100) and the probe (#93). Each run's full
command block and its expected output are in the lesson's own `RUN_LIST.md`, named in every table below; this list
gives the order, the data file each run fills, and what it costs.*

## 1. What the batch records

| Page | Outputs | Where | Run list |
|---|---|---|---|
| 0.1 Billing account, budget and project | 7 | Cloud Shell | `lessons/00-setup/0.1-billing-project/RUN_LIST.md` |
| 0.2 The local environment | 6 | your laptop, no Google Cloud | `lessons/00-setup/0.2-local-environment/RUN_LIST.md` |
| 0.3 Deploy the lane | 9 | Cloud Shell | `lessons/00-setup/0.3-deploy-lane/RUN_LIST.md` |
| 0.4 Prove the lane, break it, switch it off | 12 | Cloud Shell | `lessons/00-setup/0.4-prove-switch-off/RUN_LIST.md` |
| B.2 Tokens and embeddings | 2 | your laptop | `lessons/B-basics/B.2-tokens-embeddings/RUN_LIST.md` |
| B.4 Encoder models | 3 | your laptop | `lessons/B-basics/B.4-encoder-models/RUN_LIST.md` |
| B.5 Decoder models | 2 | your laptop, in this repository | `lessons/B-basics/B.5-decoder-models/RUN_LIST.md` |
| 10.9's Agent Engine probe | 12 facts, one file | your laptop, in this repository | `python tools/probe_agent_stack.py --project "$PROJECT" --run-note` |

That is 41 outputs on seven pages, plus the probe. Everything else on those pages is computed when they build.

## 2. Before Monday (by Fri 16 Oct)

1. **Done on 12 October: the fixes and the probe are in `main`.** With #103 and #100, `make up` gets past the admin
   console, `make down` destroys, every lane has its own state bucket and `make chat-local` serves the store it seeds
   (the plan's section 3). #93 put the probe in `tools/`, which is never published to learners.
2. **Done on 14 October: the kit is published.** The pages clone the public learner kit into `~/deploy_module_rag`,
   and it was published on 14 October from `5acffe6`, with the kit for every lesson merged that day, so every run
   follows the pages exactly as a learner will, on the laptop and in Cloud Shell. Until the next publish, 0.2's run 2
   prints `kit 7c71d48, 2026-10-14`. The published kit is `deploy/` at that commit, byte for byte, so the seven pages,
   built from `main`, count the same files your runs will (0.2's dry run included), and no publish is needed before
   Monday.
3. **Decision 7 (keep the lane up between batches, or tear it down after each), due the same Friday.** 0.4's last run
   tears this lane down whatever you decide, because the page records it. If the lane is torn down after each batch,
   every later `make up` is followed by `make ingest-corpus` again, about Rs 912 each time (section 5).
4. **The laptop:** git, curl, Python 3.12, Terraform 1.9.0 or newer, gcloud, Docker (running), Ollama and make, as
   0.2's tool table says. Pull the local model the day before, since it is a large download: `ollama pull gemma3:4b`.
5. **The leak scan:** your own project id, project number and email in `.publish-deny` at this repository's root
   (never committed), so `check_lesson.py` refuses a recording that still carries one.

## 3. The order

| When | Where | What | Lane billing |
|---|---|---|---|
| Mon 19, morning | laptop | 0.2, runs 1 to 6 | no lane |
| Mon 19, late morning | Cloud Shell | 0.1, runs 1 to 7, and the budget in the console. Run 3 creates the blank project, named `documind-ai-...` (for example `documind-ai-live-NNNN`) so the builds' redaction catches it | no lane |
| Mon 19, midday | laptop | B.2, B.4 and B.5 on that project | no lane |
| Mon 19, afternoon | Cloud Shell | 0.3's step 3 (section 5), then runs 1 to 9. Run 3 is `make up`, one to two hours | starts at `make up`'s apply |
| Mon 19, evening | Cloud Shell | `make ingest-corpus`, then `make wait-vectors` (section 5) | yes |
| Tue 20, morning | laptop, this repository | the Agent Engine probe, 20 to 30 minutes | yes |
| Tue 20, midday | Cloud Shell | 0.4, runs 1 to 11. Run 9 waits about 16 minutes with no request to the lane | yes |
| Tue 20, afternoon | Cloud Shell | 0.4, run 12: `make down`, half an hour or more | stops |
| Wed 21 | - | a spare day for any retake, then send the files back (section 7) | no lane |

Run the probe before 0.4, not between 0.4's runs 8 and 9: its calls would wake services that run 9 is waiting to see
idle.

## 4. Every run

The "Rs" column is the cost of the run itself. The lane's hourly cost while it exists is in section 6.

### 0.2 on the laptop (Rs 0)

| # | Data file | The run | Time |
|---|---|---|---|
| 1 | `data/tool_checks.txt` | the tool check | seconds |
| 2 | `data/install_check.txt` | the clone, venv and install block; move `~/rag-shell-venv` aside first, so it is a first install | a few minutes |
| 3 | `data/chat_local.txt` | terminal 2: the lane's venv, then `make chat-local` (leave it running) | a few minutes |
| 4 | `data/chat_health.txt` | `curl -s localhost:8081/health` | seconds |
| 5 | `data/chat_answer.txt` | the notice-period question through the direct brain | seconds |
| 6 | `data/dryrun_tools.txt` | Ctrl+C in terminal 2, then `make dryrun` with Docker running | a while: it builds every Python image |

Watch for run 3 echoing `DOCUMIND_CHROMA_DIR` and run 5 citing `acme:hr_policy_2026#NP-03`. If run 5 says the local
corpus is empty, the kit you cloned predates fix (d): see section 2, step 2.

### 0.1 in Cloud Shell (Rs 0)

| # | Data file | The run |
|---|---|---|
| 1 | `setup_check.txt` | gcloud's version, account and default project |
| 2 | `billing_accounts.txt` | `gcloud billing accounts list` |
| 3 | `project_link.txt` | create the project, set it as the default, link billing |
| 4 | `apis_enable.txt` | the kit's ENABLE_APIS block, 40 APIs |
| 5 | `apis_check.txt` | count them |
| - | (no file) | the budget, in the console: *Billing account guard*, 5000, rules at 50, 80 and 100 percent actual and 120 percent forecasted |
| 6 | `budgets_list.txt` | read the budget back |
| 7 | `verify.txt` | the project's billing info and gcloud's default project |

All seven go in `lessons/00-setup/0.1-billing-project/data/`. If run 2 shows a personal name on the billing account,
change it to `My Billing Account` in the file.

### B.2, B.4 and B.5 on the laptop (at most about Rs 15)

First each page's setup section in one shell: the Basics venv, then `gcloud auth application-default login`,
`export PROJECT=` the project 0.1 created, and Vertex AI enabled (0.1's run 4 did that).

| Page | # | Data file | The run | Rs |
|---|---|---|---|---|
| B.2 | 1 | `data/count_tokens.txt` | step 6: the model's own token count and the rupee line | 0 (counting is free) |
| B.2 | 2 | `data/embeddings.txt` | step 8: real embeddings and their cosines | at most 0.0011 |
| B.4 | 1 | `data/bi_encoder.txt` | step 7: the bi-encoder side, `text-embedding-005` on `us-central1` | about 0.0016 |
| B.4 | 2 | `data/cross_encoder.txt` | step 7: the cross-encoder side, one Ranking API request (enable `discoveryengine.googleapis.com` first, as the run list says) | about 0.085 |
| B.4 | 3 | `data/compare.txt` | step 7: side by side, from the two files above | 0 |
| B.5 | 1 | `data/five_runs.txt` | step 7: the same prompt five times, from this repository's root | at most 6.53, plus paise of input |
| B.5 | 2 | `data/thinking_levels.txt` | step 8: one prompt at LOW and at HIGH | at most 7.83, plus paise of input |

### 0.3 in Cloud Shell (Rs 0 per run; the lane bills from run 3)

In `~/deploy_module_rag`, after the page's setup block, with the run list's `scrub` function defined. Step 3 comes
first (section 5).

| # | Data file | The run | Time |
|---|---|---|---|
| 1 | `make_plan_summary.txt` | `make plan`, then its PASS and Plan lines | a few minutes |
| 2 | `plan_by_type.txt` | the step 6 block between `make plan` and `make up` | under a minute |
| 3 | `make_up_tail.txt` | `make up` inside `tmux`, timed; the last 30 lines | one to two hours (an estimate) |
| 4 | `run_services.txt` | the two `gcloud run services list` lines of step 8 | seconds |
| 5 | `vector_shard.txt` | the shard size of your index (step 8): expect `SHARD_SIZE_SMALL` | seconds |
| 6 | `ui_unauthenticated.txt` | the UI with no sign-in: a 302 to Google (step 9) | seconds |
| 7 | `iap_policy.txt` | `gcloud iap web get-iam-policy` (step 9) | seconds |
| 8 | `ui_signed_in.txt` | by hand in a browser: signed in, refused in a private window, and whether your project had an organization | a few minutes |
| 9 | `make_roster.txt` | `make roster` | seconds |

The run list's last section names three things to watch: the rewritten admin console deploy (its first run on a
lane), `bq-views` on a blank project, and a 403 on `storage.objects.get` during a build.

### The Agent Engine probe on the laptop (a few rupees, plus Cloud Build and Agent Engine time)

From this repository's root, with Application Default Credentials as you and the lane as the quota project. The run
note prints every prerequisite: the APIs (`telemetry.googleapis.com` is the likeliest to be missing), your actAs on
`documind-agent-sa`, and a venv of its own, `~/probe-venv`, whose install is fact 11.

| Step | Command | Time |
|---|---|---|
| the prerequisites | `python tools/probe_agent_stack.py --project "$PROJECT" --run-note`, then its steps 1 and 2 | ten minutes or so |
| the dry run | `~/probe-venv/bin/python tools/probe_agent_stack.py --project "$PROJECT"` | seconds: no call is made |
| the run | the same with `--yes` | 20 to 30 minutes |
| if anything is left | the same with `--cleanup --yes` (exit code 3 says so) | minutes |

It writes `plan/agent-engine-probe-<date>.md` itself, only after the leak scan passes. Then fill its two AUTHOR lines
(facts 4 and 12, the prices) from Google's pricing page with the date you read it, and commit it on a branch.

### 0.4 in Cloud Shell (under Rs 1 in calls; the lane bills until run 12 ends)

First, not recorded: `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`.

| # | Data file | The run | Time |
|---|---|---|---|
| 1 | `data/preflight.txt` | `make preflight` | under a minute |
| 2 | `data/smoke_green.txt` | `make smoke` with the tenant: one Gemini answer | about a minute |
| 3 | `data/smoke_broken.txt` | `make smoke` without the tenant: a 403, then make's error | about a minute |
| 4 | `data/roster_read.txt` | the two rosters from Firestore | seconds |
| 5 | `data/rest_reads.txt` | `/health`, `/ready`, `/version`, and `/health` with no token | seconds |
| 6 | `data/state_inputs.txt` | the state object and the inputs' names, on the machine that ran `make plan` | seconds |
| 7 | `data/save_session.txt` | `rag_save_session` | seconds |
| 8 | `data/off.txt` | pin acme back to `rag_engine` (not recorded), then `make off` | one to two minutes |
| 9 | `data/zero_instances.txt` | the step 9 cell: `sleep 900`, then the Monitoring read; nothing may call the lane meanwhile | about 16 minutes |
| 10 | `data/standing_resources.txt` | the step 10 cell: seven read-only listings | seconds |
| 11 | `data/resume.txt` | `rag_resume` in a new shell | about a minute |
| 12 | `data/down.txt` | `make down`: destructive, always last | half an hour or more (an estimate) |

## 5. The steps that record nothing

| When | Commands | Why | Rs |
|---|---|---|---|
| before 0.3's run 1 | 0.3's step 3: `make apis`; the state bucket `$PROJECT-tfstate` and `terraform init`; `python commands/infrastructure.py prepare` with your CI repository; the OAuth branding, and the OAuth client if your project has no organization; `make preflight` | the page's own setup, as written | 0 |
| after 0.3's run 9 | `make ingest-corpus PROJECT="$PROJECT"`, then `make wait-vectors PROJECT="$PROJECT" REGION="$REGION"` | 0.4 needs the corpus indexed, and its smoke asserts the vector tier holds vectors | about 912 |
| before 0.4's run 1 | `make tenant-backend ... RETRIEVAL_BACKEND=vector` | 0.4's smoke checks the vector tier only on `vector` | 0 |

`make ingest-corpus` uploads 31 objects across the three tenants: 20 PDFs with 1,065 pages, 3 PNG figures and the
Markdown documents. Every PDF goes through Document AI, and with the Makefile's `RESIDENCY ?= us` that is the Layout
Parser. Lesson 1.2's own cell prints "one full parse: OCR Rs 136   Layout Parser Rs 905" for these pages, at USD 10 per
1,000 pages (re-verify the rate before quoting it). Embedding about 3.26 million characters adds about Rs 7 at USD
0.000025 per 1,000. DLP's one scan per document, Firestore's writes and the managed mirrors' imports add a few rupees
more, not priced here.

## 6. What it costs

| Item | Estimate | From |
|---|---|---|
| The lane, about 30 hours (Mon afternoon to Tue afternoon) | about Rs 1,322 | Rs 44.05 an hour with the SMALL shard a new index gets (`lessons/00-setup/standing_cost.py`, Mumbai list prices read on 7 Oct); Rs 111.10 an hour if the index came up MEDIUM |
| `make ingest-corpus` | about Rs 912 | section 5 |
| B.2, B.4 and B.5 | at most about Rs 15 | the caps in section 4; the real answers are shorter |
| 0.4's calls | under Rs 1 | one Gemini answer in run 2 |
| The probe | a few rupees | the plan's estimate; Agent Engine's own price is fact 12, which you fill in |
| **Total** | **about Rs 2,250** | plus Cloud Build minutes for `make up`'s builds and the probe's image, which no page prices |

Every extra hour the lane stays up adds Rs 44.05: a day's slip between 0.3 and 0.4 adds about Rs 1,057.

## 7. After the runs

1. **Placeholders first.** Each run list says what to replace: the project id with `documind-ai-YOUR-ID`, the project
   number with `NUMBER`, your email with `you@example.com` or `you@your-company.com` as that list says, your home
   directory with `/home/you`, a commit with `COMMIT`. 0.1's build redacts most of this itself; for the others, do it
   before saving the file (0.3's run list gives a `scrub` function for it).
2. **Where the files go:** each lesson's `data/` folder, under the names in section 4. Then, if you like,
   `python pagekit/build.py N.M && python pagekit/check_lesson.py N.M && python pagekit/audit_pages.py N.M` for each
   page: the check fails on any real identifier left behind.
3. **Send them back by Wednesday:** push a branch with the `data/` files (and the probe's facts file), or attach the
   files in the project's chat with Claude. On Thursday 22 Oct the seven pages are rebuilt from them, each in its own
   pull request, with anything a recording contradicts corrected in the prose: where a recording disagrees with a page,
   the recording is right.
