# Lesson 11.8 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/11-project/11.8-capstone-handover/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 11.8 && python pagekit/check_lesson.py 11.8 && python pagekit/audit_pages.py 11.8

Everything else on the page is computed when it is built, offline: the rubric's interactive, the selftest, the check
on a copy of the kit as it ships, on the canned fork and on the Change-it's copy, the records cell, and the handover
of the canned fork.

## Before the first run

- **Batch:** 4 (Mon 23 - Wed 25 Nov), as the plan's batch table lists 11.8, after batch 3's runs of lessons 11.1 to
  11.3, which leave the records the check reads (the smoke log and the gate's reports in `evals/reports/`).
- **The reference fork,** about one author day from a working lane, before the batch: a tenant other than acme, globex
  and zeta with 30 or more pages under `evals/corpus/<tenant>/` (form feeds separate a text file's pages; a PDF's page
  tree counts), then `make ingest-corpus`,
  `make roster TENANT=<tenant> MEMBERS=documind-ui-sa@$PROJECT.iam.gserviceaccount.com`, golden rows for the tenant
  (lesson 4.1), `make gate`, lesson 11.3's forced promote, rollback and repair with `make smoke-deployed` before and
  after each (the rollback is read from that log), and the four documents, copied from `capstone/templates/` to the
  fork's root and filled in until `grep -c '{{'` counts 0 in each (the canned fork's four are the worked example).
  Run `make capstone-check` offline until every component passes, then record.
- **The kit:** a checkout with `commands/capstone_check.py`, `mk/capstone.mk` (kit R5) and `capstone/templates/`
  (13 October 2026). Run from the checkout that ran lessons 11.2 and 11.3: `evals/reports/` is gitignored, and the
  check reads the records in the checkout it runs in. The handover's CI trust section reads `terraform/runbook-project.auto.tfvars.json`, which `make plan` saved in
  the checkout that planned the lane; without it the section says so, and nothing fails.
- **Where:** the operator shell (Cloud Shell or the workstation), in the fork, after the page's shared setup block
  (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT`, `ME`, `NUMBER` and `API` and defines
  `tok` and `otok`. For run 2 set `TENANT` to your own tenant. `make`, `gcloud` and `git` on PATH; `make operators`
  done for your address (the two token mints need it).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. Run 4 is the command's one line and then `HANDOVER.md` whole.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (it is in every `run.app` URL the
  check prints, and in the state bucket's object path if the project number appears there); your email
  `you@your-company.com`; the fork's directory `/home/you/<your-fork>`; your fork's repository, where the handover's
  CI trust section prints it, `your-github-user/your-fork`, and its repository ID `REPO-ID`; commit shas `COMMIT`.
  Revision names, times, counts, rupees, policy names and channel counts may stay. `check_lesson.py` refuses a real
  project id, a project number in a URL or resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

Rupees from `shared/prices.py`: none of the four runs makes a model call. Every read is a `gcloud` describe or list,
a token mint, a GET on documind-api or one GET on the Monitoring API, and nothing on the lane changes.

| # | Data file | Page step | Command | Time | Cost |
|---|---|---|---|---|---|
| 1 | `data/capstone_check.txt` | 5, your fork, offline | `make capstone-check` in the reference fork | a few seconds (`make eval` runs offline) | Rs 0 |
| 2 | `data/rest_reads.txt` | 7, the reads by hand | the step's bash cell, as written | seconds | Rs 0: two token mints, three GETs, one describe |
| 3 | `data/capstone_live.txt` | 7, the check with your lane | `make capstone-check PROJECT="$PROJECT" REGION="$REGION"` | under a minute | Rs 0: gcloud describe and list reads, two tokens, three GETs |
| 4 | `data/handover.txt` | 8, the handover of your lane | `make handover PROJECT="$PROJECT" REGION="$REGION" && cat HANDOVER.md` | under a minute | Rs 0: describe and list reads, the Monitoring API's alert-policy list |

In all, Rs 0. The cohort plan budgeted Rs 0 for this lesson's runs.

The page's prose states what each recording should show, read from the kit's code. If a recording disagrees, the
recording is right: say so in the review, and the prose changes with it.

### 1. `data/capstone_check.txt` (step 5)

In the reference fork, offline. Expect the shape the canned fork prints on the page: the `>> capstone-check: the fork
at /home/you/<your-fork>, offline: ...` paragraph, eight `PASS` lines with their evidence indented under each, and
`>> complete: every one of the eight components PASSes. Nothing here is scored: the defence scores the five dimensions`.
Component 1's evidence names your last smoke run's `/version` answer and the report that asked the isolation rows;
component 2 your tenant, its documents and pages, and the row that cited one; component 4 the lane whose smoke
passed; component 8 the rollback's two revisions and the two `/version` answers. A `FAIL` is work on the fork, not a
recording: its line names the lesson. Record only a run with eight PASSes.

### 2. `data/rest_reads.txt` (step 7)

Run the cell as written, with `TENANT` set to your own tenant. Expect four lines and a JSON body:
`GET /version as documind-ui-sa: 200`, then `/version`'s JSON (`git_sha`, `generator_model`, `prompt`,
`retrieval_graph`, `model_backend`), then `GET /v1/sources?tenant_id=<tenant> as documind-outsider-sa: 403`, then
the grep of documind-ui's description for its IAP annotation (`"run.googleapis.com/iap-enabled": "true"`, or the
`iapEnabled` field; the kit has not seen either on a lane yet, so if the grep prints nothing and the line says
`no iap annotation: see step 9`, record that as it is and say so in the review: component 1's lane line in run 3
tells the same story). Replace the project number in nothing here: the URLs are in `$API`, not in the output.

### 3. `data/capstone_live.txt` (step 7)

Right after run 2, in the same fork. Expect run 1's lines again, the first paragraph now ending `, and the lane
documind-ai-YOUR-ID in asia-south1, read only`, and a `lane:` line under components 1 (three of them: `/version` as
documind-ui-sa 200 with its answer; `/v1/sources?tenant_id=<tenant>` as documind-outsider-sa, on no roster, 403;
documind-ui has IAP on), 2 (`GET /v1/sources?tenant_id=<tenant>, the Documents page's read, lists all N documents
indexed`), 4 (`<lane>'s services are deployed: ...`) and 8 (`both are documind-api revisions on documind-ai-YOUR-ID`).
The project id prints in several lines: replace it everywhere. If the IAP line reads `documind-ui does not have IAP
on` while the console shows IAP on, the annotation's key is the one the kit has not verified: record the run as it
is and report it; the fix is the kit's.

### 4. `data/handover.txt` (step 8)

In the same fork. Expect `>> handover: /home/you/<your-fork>/HANDOVER.md, from this checkout and the lane
documind-ai-YOUR-ID`, then the file: `# Handover: DocuMind on documind-ai-YOUR-ID`, the head paragraph, and seven
sections, each with the checkout's statement and then the lane's. The policies table's last column should read
`enabled, N channels` for each policy on the lane; the night job `ENABLED` with its schedule and last attempt; the
floors table every service in both regions; documind-api's traffic table and revision count; the provider's condition
`the same as the checkout's`; the budget's amount and thresholds; the state bucket's location and the object's size
and update time. `## Not read` should end with `- nothing`; if it lists a read, record the run as it is and name the
read in the review. Five reads have not run on a lane before this one: the IAP annotation, the Monitoring API's
alertPolicies GET, `gcloud billing budgets list` (it may need a quota project), gcloud storage's describe keys, and
the scheduler describe's fields. The exit is 1 when any read failed; record it anyway.

Replace in the file: the project id (title, head, state bucket path, the budget's billing line if it names one), the
project number if a URL or path carries it, your repository name and ID in CI trust, and commit shas (`GIT_SHA`
under Revisions) with `COMMIT`.
