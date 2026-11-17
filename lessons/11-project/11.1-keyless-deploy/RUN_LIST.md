# Lesson 11.1 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/11-project/11.1-keyless-deploy/data/`. Record each file once, replace every identifier
with the course's placeholders, then rebuild and check:

    python pagekit/build.py 11.1 && python pagekit/check_lesson.py 11.1 && python pagekit/audit_pages.py 11.1

Everything else on the page is computed when it builds, from the kit: the trust panel (`wif.tf`'s condition and
binding, accepted by `infrastructure.parse_trust()` and run by node against a Python evaluation), the counts of roles,
accounts and APIs, `make ci-vars`' output before the environment exists and its region refusal, `make keys-check` on a
planted key (all three are `commands/release.py` run against stand-in `terraform`, `gh` and `gcloud`, as its own tests
run it), and the make lines of the local operator path.

## Before the first run

- **The lane:** deployed by `make up` (lesson 0.3), with its CI trust on a **public fork the author owns** of
  `netsetos/agents_workshop_learner`, on `refs/heads/main`, as a learner's lane is (decision 11). The trust cannot be
  moved on an existing lane (`infrastructure.py` refuses the plan), so if the author's lane trusts another repository,
  these runs need a lane created with such a fork.
- **The fork:** synced with the upstream's `main` (`gh repo sync YOUR-GITHUB-USER/agents_workshop_learner`), so the run
  builds the kit the lane runs; its workflows enabled once in the fork's Actions tab.
- **Where:** the operator shell (Cloud Shell), in the kit (`~/deploy_module_rag`), on the machine that ran `make plan`,
  after the page's shared setup block, which exports `PROJECT`, `REGION=asia-south1`, `NUMBER` and `API` and defines
  `tok`. Then `gh auth login` as the fork's owner.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`, so the dispatch's live gate runs as
  lesson 4.3's gate ran. Put the pin back (`RETRIEVAL_BACKEND=rag_engine`) after the last run.
- **Order, in one sitting:** runs 2 to 9 in the page's order. Run 4's dispatch takes about fifteen minutes; run 5
  follows step 6's reject cell; run 8 (the audit read) within 24 hours of run 4.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (in the provider's name, the principalSet,
  the subject and any URL); the repository `YOUR-GITHUB-USER/YOUR-REPO`, its id `REPO_ID`, the GitHub user
  `YOUR-GITHUB-USER`; commit shas `COMMIT`; run ids `RUN_ID`; an organization id `ORG_ID`; emails `you@your-company.com`.
  Revision names, job ids and times may stay. `check_lesson.py` refuses a real project id, a project number in a URL or
  resource path, a personal mailbox and every string in `.publish-deny`.
- **The gh and Python cells were written without a GitHub run or a lane to test them.** If one fails, record what it
  printed and tell the page's editor: the cell is fixed in `build.py` (`CELLS`) and recorded again.

## The runs

| # | Batch | Data file | Page step | Time | Cost |
|---|---|---|---|---|---|
| 1 | 1 (Mon 26 - Wed 28 Oct 2026) | `data/probe_dispatch.txt` | 9, the first keyless dispatch | about 15 minutes | up to about Rs 29 and one Cloud Build; no model call if it stops before the gate |
| 2 | 3 (Mon 16 - Wed 18 Nov 2026) | `data/fork_check.txt` | 3, the trust cell | seconds | Rs 0 |
| 3 | 3 | `data/gh_setup.txt` | 5, a reviewer, then the variables | seconds | Rs 0 |
| 4 | 3 | `data/run_main.txt` | 6, dispatch and wait | about 15 minutes | about Rs 29 and one Cloud Build |
| 5 | 3 | `data/candidate.txt` | 6, what the run left | seconds | Rs 0 |
| 6 | 3 | `data/run_branch.txt` | 7, the branch dispatch | a few minutes | Rs 0: refused at the auth step |
| 7 | 3 | `data/iam_rest.txt` | 8, IAM's REST API | seconds | Rs 0 |
| 8 | 3 | `data/audit.txt` | 8, the audit trail | seconds | Rs 0 |
| 9 | 3 | `data/keys.txt` | 8, make keys-check | seconds | Rs 0 |

**Total: about Rs 58 in all, plus two Cloud Builds.**

**Where the rupees come from.** A dispatch that gets past the build runs the live gate on its candidate
(`documind-cd.yml`'s step *The live gate, on the candidate*): the 65 golden rows as the roster member, and the 11
isolation rows again as the outsider, whose requests are refused at the roster before any model call. `shared/prices.py`:
gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs 85 to the dollar, at the course's typical answer of
2,000 tokens in and 300 out (the figure lessons 4.3, 4.4 and 11.6 use): Rs 0.45 an answer, so at most 65 answers cost
about Rs 29. `build.py` checks these figures against the kit on every build. Lesson 11.2 reads run 4's gate log and
judges the candidate it leaves (one dispatch serves 11.1 to 11.3), so record 11.2's files from the same run when its
run list asks. CI keeps no gate record (`documind-cd.yml` runs `make eval-live` with no `REPORT=`), so 11.2's own
`make gate` costs about Rs 29 more, on 11.2's run list. Cloud Build bills build-minutes at its own rate, which
`shared/prices.py` does not hold; the plan estimates a few rupees. The candidate revision takes no traffic and the API's
floor is zero instances, so it costs nothing idle. `make usage PROJECT="$PROJECT" HOURS=1` after run 4 prints the gate's
real figure; please note it when you hand the files back. The review of 7 October estimated Rs 60-110 for a gate.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it. The bash blocks below
are the page's cells, character for character (`build.py` refuses to build if they drift apart); the three Python
cells are long, so their runs say "as written on the page".

### 1. `data/probe_dispatch.txt` (batch 1: the probe)

The first dispatch on the author's lane, before any page claims it works. It proves what the kit grants for the
build beyond `sa.tf` (24 October 2026): the token exchange, with `sts.googleapis.com` among `make apis`' 41 APIs;
the source upload into `gs://PROJECT_cloudbuild`, which the workflow names and `make build-access` lets
`sa-documind-cicd` write (the bucket's legacy writer role, nothing project-wide); and actAs on the account the build
runs as (the Compute Engine default), which `make build-access` grants unless that account holds Editor or Owner.
The build is submitted `--async` and polled, so no log is read. A lane made up before then runs
`make build-access PROJECT="$PROJECT"` first.

First, not recorded in batch 1: the trust cell (run 2's block), the first `make ci-vars`, and the reviewer and the
variables (run 3's block). Then the dispatch (run 4's block), and record its output; if `release-candidate` failed,
append:

```bash
gh run view "$RUN" --repo "$GH_REPO" --log-failed | tail -n 40
```

If the run got as far as promote, reject it (run 4's second block). Then remove the candidate's tag, so batch 3 starts
from a clean service (not recorded):

```bash
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
```

Expect, if all of them hold: `eval-gate` and `release-candidate` green and `promote` waiting. If one does not: the
auth step failing on the exchange, or *Build the API image* failing on the upload, on the log, or on acting as the
build's account. **Tell the page's editor which, and what fixed it.** The fix is a kit PR (a grant in `sa.tf`, or an
API in `commands/lesson-12.1.sh`'s list, both quoted by other pages; R1 kept a day for it), and steps 6 and 9 of this
page change with it before batch 3. If the probe passes, say so too: step 9's "may" becomes "did not".

### 2. `data/fork_check.txt` (step 3)

```bash
read -r GH_REPO TRUST_ID TRUST_REF < <(python -c 'import json; t = json.load(open("terraform/runbook-project.auto.tfvars.json")); print(t["github_repository"], t["github_repository_id"], t["deploy_ref"])')
export GH_REPO; echo "your lane trusts $GH_REPO, id $TRUST_ID, on $TRUST_REF"
gh repo view "$GH_REPO" --json nameWithOwner,visibility,isFork,parent \
  --jq '"GitHub: \(.nameWithOwner), \(.visibility), " + (if .isFork then "a fork of \(.parent.owner.login)/\(.parent.name)" else "not a fork" end)'
gh api "repos/$GH_REPO" --jq '"its GitHub id: \(.id)"'
gh workflow list --repo "$GH_REPO" --all --json name,state --jq '.[] | "workflow \(.name): \(.state)"'
```

Expect:

```
your lane trusts YOUR-GITHUB-USER/YOUR-REPO, id REPO_ID, on refs/heads/main
GitHub: YOUR-GITHUB-USER/YOUR-REPO, PUBLIC, a fork of netsetos/agents_workshop_learner
its GitHub id: REPO_ID
workflow documind-cd: active
workflow DocuMind dry run (Tier A): active
```

A workflow in the state `disabled_fork` has not been enabled in the fork's Actions tab: enable it and run the block
again.

### 3. `data/gh_setup.txt` (step 5)

First the page's first `make ci-vars`, not recorded (the page computes its output):

```bash
make ci-vars PROJECT="$PROJECT" REGION="$REGION"
```

Then record this block. The environment call creates or updates, so an environment left by batch 1 is fine.

```bash
printf '{"reviewers":[{"type":"User","id":%s}]}' "$(gh api user --jq .id)" \
  | gh api -X PUT "repos/$GH_REPO/environments/production" --input - --jq '"environment \(.name): " + ([.protection_rules[].type] | join(", "))'
make ci-vars PROJECT="$PROJECT" REGION="$REGION" | tee "$HOME/ci-vars.txt"
grep '^gh variable set ' "$HOME/ci-vars.txt" | bash
gh variable list --repo "$GH_REPO"
echo "repository secrets: $(gh secret list --repo "$GH_REPO" | wc -l)"
```

Expect `environment production: required_reviewers`, `make ci-vars`' four `gh variable set` lines, its trust and
dispatch lines and `# production: 1 required reviewer, so promote waits for a person`, gh's confirmation of each
variable, the variable list (four names with your values: replace the project id and the number in `WIF_PROVIDER`),
and `repository secrets: 0`.

### 4. `data/run_main.txt` (step 6)

```bash
gh workflow run documind-cd.yml --repo "$GH_REPO" --ref main -f path=candidate && sleep 20
export RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "run $RUN: https://github.com/$GH_REPO/actions/runs/$RUN"
until [ "$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '[.jobs[] | select(.name == "release-candidate") | .status] | first')" = completed ]; do sleep 30; done
gh run view "$RUN" --repo "$GH_REPO"
```

Expect gh's dispatch confirmation, `run RUN_ID: https://github.com/YOUR-GITHUB-USER/YOUR-REPO/actions/runs/RUN_ID`,
and the summary: `eval-gate` and `release-candidate` green, `promote` waiting for its reviewer. Then reject promote,
not recorded (it prints `promote: rejected`):

```bash
ENV_ID="$(gh api "repos/$GH_REPO/environments/production" --jq .id)"
printf '{"environment_ids":[%s],"state":"rejected","comment":"lesson 11.2 judges this candidate first"}' "$ENV_ID" \
  | gh api -X POST "repos/$GH_REPO/actions/runs/$RUN/pending_deployments" --input - --silent && echo "promote: rejected"
```

### 5. `data/candidate.txt` (step 6)

After the reject, the cell *what the run left on Cloud Run*, as written on the page (a Python heredoc that starts
`import json, os, subprocess, warnings`, then two `gh run view` lines). Expect
`documind-api, last changed by sa-documind-cicd@documind-ai-YOUR-ID.iam.gserviceaccount.com`; the traffic lines, the
serving revision at 100% and the candidate at 0% with `tag candidate`; the candidate's `made by` the same account;
`image asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT`, `GIT_SHA COMMIT` and
`the run built: COMMIT` (one full sha three times: replace each with `COMMIT`, and say whether they matched); then
`run: completed, failure` and each job's conclusion. If an annotation prints `(not recorded)`, say so: the page claims
the revision names the account that made it.

### 6. `data/run_branch.txt` (step 7)

```bash
gh api -X POST "repos/$GH_REPO/git/refs" -f ref=refs/heads/try-a-branch \
  -f sha="$(gh api "repos/$GH_REPO/commits/main" --jq .sha)" --jq '"branch \(.ref) at \(.object.sha[0:7])"'
gh workflow run documind-cd.yml --repo "$GH_REPO" --ref try-a-branch -f path=candidate && sleep 20
BR="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch try-a-branch --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$BR" --repo "$GH_REPO" --exit-status > /dev/null; echo "gh run watch $BR: exit $?"
gh run view "$BR" --repo "$GH_REPO"
gh run view "$BR" --repo "$GH_REPO" --log-failed | grep -iE "error|attribute condition" | head -n 5
gh api -X DELETE "repos/$GH_REPO/git/refs/heads/try-a-branch" && echo "branch try-a-branch deleted"
```

Expect `branch refs/heads/try-a-branch at COMMIT`, gh's dispatch confirmation, `gh run watch RUN_ID: exit 1`, the
summary with `eval-gate` green, `release-candidate` failed at its auth step and `promote` skipped, then up to five
error lines from the auth step, Google's refusal among them (it should name the attribute condition), and
`branch try-a-branch deleted`. If the run fails at another step, or the error names something else, record it as it
is and tell the editor. If creating the branch is refused for a missing `workflow` scope on gh's token, run
`gh auth refresh -s workflow` and the block again.

### 7. `data/iam_rest.txt` (step 8)

The IAM cell, as written on the page (a Python heredoc that starts `import os, warnings` and defines `call()`). Expect
`provider documind-github/providers/github-oidc | ACTIVE | issuer https://token.actions.githubusercontent.com`, three
`condition` lines (`assertion.repository_id == 'REPO_ID'`, `assertion.repository == 'YOUR-GITHUB-USER/YOUR-REPO'`,
`assertion.ref == 'refs/heads/main'`), four `mapping` lines, the bindings on `sa-documind-cicd`
(`roles/iam.workloadIdentityUser <- documind-github/attribute.repository_id/REPO_ID`, `roles/iam.serviceAccountUser`
for the account itself, and any others: keep them), then `user-managed keys on sa-documind-cicd: 0`.

### 8. `data/audit.txt` (step 8)

The audit cell, as written on the page (a Python heredoc that starts `import datetime as dt, os, warnings`), within
24 hours of run 4. Expect a count, then a timestamp and a method per entry, Cloud Build's build creation and Cloud
Run's service update at least, each with
`on behalf of principal://iam.googleapis.com/projects/NUMBER/locations/global/workloadIdentityPools/documind-github/subject/repo:YOUR-GITHUB-USER/YOUR-REPO:ref:refs/heads/main`.
**Tell the editor whether the delegation line appears** (the review of 7 October could not verify it). If every entry
says `(no delegation recorded)`, step 8's prose changes.

### 9. `data/keys.txt` (step 8)

```bash
make keys-check PROJECT="$PROJECT"; echo "exit $?"
```

Expect the parent line (with no organization, `documind-ai-YOUR-ID has no parent: ... this check is the control`;
under one, the organization's line, with its id replaced by `ORG_ID`), `N service accounts, and the user-managed keys
of each:`, a `0` line per account (replace the project id in each email), `no user-managed keys: no key file can sign
in as any account of documind-ai-YOUR-ID` and `exit 0`. If any account holds a key, do not record yet: delete the key
the check names, if nothing uses it, and say so.

Last, put acme's pin back: `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=rag_engine`. Keep the
candidate revision: lesson 11.2's runs judge it.
