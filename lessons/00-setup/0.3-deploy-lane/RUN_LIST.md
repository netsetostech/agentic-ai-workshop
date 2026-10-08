# Lesson 0.3: the live runs the page still needs

The page's nine `output` windows are marked stand-ins until these runs are recorded. Each window reads one file from
this folder's `data/` through `pb.recorded()`; `python pagekit/build.py 0.3` then fills it, and `finish()` names any file
still missing. Everything else on the page (the counts, the tables, the explorer, the `expected` windows, the prices) is
computed from the kit at build time and needs no run.

**One run, from a blank project** (planned for about 23 October 2026): a project with billing linked and the budget of
lesson 0.1, and nothing of the kit's yet: no state, no accounts, no services.

**Where:** the operator shell of lesson 0.2 (Cloud Shell or a workstation), in the kit clone at `~/deploy_module_rag`,
after the page's setup block ("Before you run anything: open the operator shell"), which exports `PROJECT`, `REGION`
(asia-south1), `ME`, `ADMIN_EMAILS`, `TENANT`, `TFSTATE_BUCKET`, `TFSTATE_PREFIX` and `NUMBER`.

**Placeholders:** every file must carry the page's placeholders, never the lane's real values. Define this once in the
same shell and pipe every recording through it:

```bash
mkdir -p ~/lesson-0.3
scrub() { sed -e "s/$PROJECT/documind-ai-YOUR-ID/g" -e "s/$NUMBER/NUMBER/g" -e "s/$ME/you@example.com/g" -e "s#$HOME#/home/you#g"; }
```

Read each file before copying it into `lessons/00-setup/0.3-deploy-lane/data/` in the authoring repository:
`python pagekit/check_lesson.py 0.3` fails on a real project id, project number or personal mailbox (tools/leakscan.py).
The `CI trust:` line names your own CI repository and its numeric id; replace them with `YOUR-GITHUB-USER/YOUR-REPO` and
`NUMBER` if they should not appear on the page.

**Cost:** nothing bills by the hour until `make up`'s apply. From then on the lane costs what step 10 of the page computes:
Rs 44.05 an hour if the service picks a SMALL shard for the vector index, Rs 111.10 an hour if it picks MEDIUM, at the
Mumbai (asia-south1) list prices of `lessons/00-setup/standing_cost.py`, read on 7 October 2026 and shared with 0.1 and
0.4. The builds add Cloud Build minutes, not priced on the page. `make down` (lesson 0.4) ends it; keep the lane up if
lesson 0.4's run list follows.

**Times** below are estimates for planning, not measurements; `make up`'s real duration is one of the recordings.

## Before the recordings: the page's step 3, as written

1. `make apis PROJECT="$PROJECT"` (a minute or two; Rs 0).
2. The state bucket and `terraform -chdir=terraform init` with `TFSTATE_BUCKET` and `TFSTATE_PREFIX` (a minute; Rs 0).
3. `python commands/infrastructure.py prepare ...` with your own CI repository, its numeric id and `refs/heads/main`
   (seconds; Rs 0).
4. Google Auth Platform > Branding. Then `gcloud projects describe "$PROJECT" --format='value(parent.type,parent.id)'`:
   if it prints nothing (no organization), create the Web OAuth client and run the `gcloud iap settings set` block of
   step 3. Note which case your project was, for `ui_signed_in.txt` below: the page tells learners without an
   organization that this step is required, and the author's run is its only live check.
5. `make preflight PROJECT="$PROJECT" TFSTATE_BUCKET="$TFSTATE_BUCKET" REGION="$REGION"`: every line `ok`. If a line
   differs from the page's computed `expected` window, say so: that window is built from `smoke/preflight.sh`'s own lines.

## The recordings

| # | data file | Run (in the operator shell, in `~/deploy_module_rag`) | Expect | Time | Cost |
|---|---|---|---|---|---|
| 1 | `make_plan_summary.txt` | `make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ADMIN_EMAILS" 2>&1 \| tee ~/plan.log` then `grep -E '^(PASS\|CI trust\|STOP\|Plan:)\|Reviewed plan\|Review the' ~/plan.log \| scrub > ~/lesson-0.3/make_plan_summary.txt` | two `PASS` lines around `Plan: 234 to add, 0 to change, 0 to destroy.` (the files' count, with one address in `ADMIN_EMAILS`; the build prints a NOTE if the recorded number differs) | a few minutes | Rs 0 |
| 2 | `plan_by_type.txt` | the step 6 block "after make plan and before make up" (the `PLAN=...` line, `terraform show -json`, the Python cell), piped: append `\| scrub > ~/lesson-0.3/plan_by_type.txt` to a `{ ...; }` group around the three commands | `actions: {'create': 234}`, then 55 type lines equal to the page's computed window, then `234  in all` | under a minute | Rs 0 |
| 3 | `make_up_tail.txt` | `tmux new -s up`, then `{ time make up PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ADMIN_EMAILS" 2>&1 ; } 2>&1 \| tee ~/up.log` (the braces put `time`'s report in the log), then `tail -n 30 ~/up.log \| scrub > ~/lesson-0.3/make_up_tail.txt` | the `>> no drift` line, the roster lines, the managed stores, the `vector-status` YAML (0 datapoints), then `real`/`user`/`sys` | one to two hours (estimate) | the hourly rows start here (above) |
| 4 | `run_services.txt` | the two `gcloud run services list` lines of step 8, `\| scrub` | 7 rows, each `RUNS_AS documind-<service>-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`, then `7` | seconds | Rs 0 |
| 5 | `vector_shard.txt` | the three lines of step 8 "The shard size the service chose", `\| scrub` | `SHARD_SIZE_SMALL` or `SHARD_SIZE_MEDIUM`, then the machine and `1`; this decides which Vector Search line of step 10 applies | seconds | Rs 0 |
| 6 | `ui_unauthenticated.txt` | the `curl ... \| cut -d'?' -f1` line of step 9 | `302 https://accounts.google.com/...` (cut at the query string, which carries the OAuth client id) | seconds | Rs 0 |
| 7 | `iap_policy.txt` | the `gcloud iap web get-iam-policy` line of step 9, `\| scrub` | a binding of `roles/iap.httpsResourceAccessor` with `user:you@example.com` | seconds | Rs 0 |
| 8 | `ui_signed_in.txt` | by hand, in a browser: open `https://documind-ui-NUMBER.asia-south1.run.app`; (a) signed in as yourself: write down the sidebar (your address as `you@example.com`, `Tenant: acme`); (b) in a private window, a Google account not in `ADMIN_EMAILS`: write down the heading and first line of IAP's refusal page; (c) one line: whether the project had an organization and whether the custom OAuth client of step 3 was needed | three short notes, in plain words | a few minutes | Rs 0 |
| 9 | `make_roster.txt` | `make roster PROJECT="$PROJECT" 2>&1 \| scrub > ~/lesson-0.3/make_roster.txt` | 11 lines `... is on acme/zeta/globex` and three `data_region` lines, matching the page's computed dry run | seconds | Rs 0 |

Then copy `~/lesson-0.3/*.txt` into `lessons/00-setup/0.3-deploy-lane/data/`, run `python pagekit/build.py 0.3`,
`python pagekit/check_lesson.py 0.3` and `python pagekit/audit_pages.py 0.3`, and read the nine windows on the page.

## If the run does not go as the page says

The page's prose around each window describes the kit as it reads today. If a recording differs, keep the recording
as it is and tell the coordinator; do not edit a recording to match the page. Three things worth watching on this run
(details in the coordinator's report for lesson 0.3):

- `make up`'s deploy step runs `commands/lesson-12.3.sh` third. Its DEPLOY block calls `gcloud builds submit` with a
  `--file` flag gcloud does not have, names `us-central1` where the others use `REGION`, and binds a placeholder group.
  If it stops there, `documind-ui`, `documind-chat`, `documind-mcp` and `documind-agent` are not deployed.
- `make up`'s `bq-views` step creates a view over the log sink's table, which exists only after the API has answered
  once; on a blank project it may stop `make up` before `vector-status`.
- A build that stops at `storage.objects.get` with a 403: the page's step 7 has the three grants. Record whether it
  happened (one line in `make_up_tail.txt` is enough).
