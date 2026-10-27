# Lesson 11.7 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/11-project/11.7-production-gotchas/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 11.7 && python pagekit/check_lesson.py 11.7 && python pagekit/audit_pages.py 11.7

Everything else on the page is computed when it is built, offline: the registry, every offline drill, the deploy
reader, the Change-it, and the REST cell's code, which the build runs against the kit's own stand-in of Cloud Run.

## Before the first run

- **Batch:** 3 (Mon 16 - Wed 18 Nov), after lessons 11.1-11.3's runs, so that the release detectors in run 5 read a
  lane and a checkout that have been through a candidate and a promote.
- **The kit:** a checkout with `commands/gotchas.py`, `ops/gotchas.json` and `mk/operations.mk` (PR #139). Run from
  the checkout that planned the lane if you can: the production-environment detector reads
  `terraform/runbook-project.auto.tfvars.json`, which `make plan` saved there, and prints `STOPPED` for itself alone
  without it. `gh`, signed in, lets that detector read the environment; without gh it prints a note.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit, after the page's shared setup block
  (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API`. `make`,
  `gcloud` and `git` on PATH.
- **documind-chat's state:** traffic on its latest revision, and no variable on it that a routine deploy would drop.
  Run 1 shows both. Lesson 6.7 leaves `LESSON113_RESTART` on the chat; run 3 stops on it and prints the
  `gcloud run services update documind-chat --remove-env-vars=...` line that takes it off. Run that line (not
  recorded), then run 3 again.
- **The checkout and the chat's image:** run 3 rebuilds the chat's image from this checkout, so it refuses unless the
  checkout is at the commit the serving image was built from. If it stops on that, redeploy the chat from the
  checkout first (not recorded; about four minutes, no model call):
  `make deploy-services SCRIPTS=commands/lesson-12.8.sh PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"`.
  The page tells learners the same.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets, except in run 3 (below).
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`;
  commit shas, the chat's image tag among them, `COMMIT`; your fork's name, where the environment detector prints it,
  `your-github-user/your-fork`. Revision names, times, counts and rupees may stay. `check_lesson.py` refuses a real
  project id, a project number in a URL, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

Rupees from `shared/prices.py` and the kit's own limits: runs 1, 2, 3 and 5 make no model call. Run 4 asks one
question per brain: each agent turn stops calling the model once it has spent Rs 5 (`CHAT_TURN_BUDGET_INR`, the
default in `services/chat/limits.py`), and the direct brain's one answer is at most Rs 2.33 (`config.py`'s 8,000
tokens in and 2,048 out at gemini-3.6-flash's list price). Its four brain lines print what each turn cost.

| # | Data file | Page step | Command | Time | Cost |
|---|---|---|---|---|---|
| 1 | `data/rest_traffic.txt` | 6, the two services before the drills | the step's Python cell, as written | seconds | Rs 0: two service reads, two revision reads |
| 2 | `data/drill_pinned.txt` | 7, pinned traffic on the lane | `make gotcha-drill ID=pinned-traffic LIVE=1 PROJECT="$PROJECT" REGION="$REGION"` | a few minutes | Rs 0: no model call, four `/health` reads |
| 3 | `data/drill_deploy_drop.txt` | 7, a routine deploy drops a hotfix | `make gotcha-drill ID=deploy-drops-hotfix LIVE=1 PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"` | about five minutes, four of them the chat's image build | Rs 0 in model calls; one Cloud Build of the chat image, whose price `shared/prices.py` does not state |
| 4 | `data/smoke_chat.txt` | 7, the chat on every brain | `make smoke-chat PROJECT="$PROJECT" REGION="$REGION"` | a minute or two | about Rs 5 |
| 5 | `data/detect_all.txt` | 8, every detector | `make gotcha-detect PROJECT="$PROJECT" REGION="$REGION"` | under a minute | Rs 0: reads only |

In all, about Rs 5 in model calls, all of it run 4, plus one Cloud Build of the chat image in run 3. The cohort plan
budgeted about Rs 5 for this lesson's runs.

The page's prose states what each recording should show, read from the kit's code. If a recording disagrees, the
recording is right: say so in the review, and the prose changes with it.

### 1. `data/rest_traffic.txt` (step 6)

Run the step's Python heredoc as written. On the kit's stand-in, a lane as `make deploy-services` leaves it, the cell
printed this (the build checks it):

```
documind-chat: newest revision documind-chat-00001-mup
  100%  documind-chat-00001-mup  follows the latest revision
  the template against documind-chat-00001-mup: the same variables
  CHAT_MAX_MODEL_CALLS on the template: unset (limits.py: 12)
documind-api: newest revision documind-api-00001-mup
  100%  documind-api-00001-mup  held by name
  the template against documind-api-00001-mup: the same variables
```

Expect the same shape with your revision names. documind-api may show a `tag candidate` line at 0% and template
differences, if lesson 11.2's or 11.3's candidate is still tagged; record it as it is. If documind-chat says
`held by name`, or its template line names a variable, fix that first (both drills would refuse) and run the cell
again before recording.

### 2. `data/drill_pinned.txt` (step 7)

Expect the lines step 5's offline drill prints, on your lane: the header `== pinned-traffic, live on ...`, the
serving revision with `/health: max_model_calls 12`, the two gcloud lines, the new revision `takes 0% of the traffic;
/health: max_model_calls 12`, the detector's two lines, `REPRODUCED: ...`, the lever's gcloud line, `/health:
max_model_calls 3`, `CLEARED: ...`, the restore's `--remove-env-vars` line, and last
`restored: CHAT_MAX_MODEL_CALLS unset, traffic on the latest revision; /health: max_model_calls 12`.
The gcloud lines carry your project and region: replace the project id. If the drill prints `RESTORE FAILED`, run the
two gcloud lines it prints at once, record nothing, and report it.

### 3. `data/drill_deploy_drop.txt` (step 7)

See "Before the first run" for its two refusals. Expect: `documind-chat: image tag COMMIT, nothing the next deploy
would change; /health: max_model_calls 12`, the hand update and `/health: max_model_calls 8: the hand-set value
answers`, `detector, before the deploy: CHAT_MAX_MODEL_CALLS=8: dropped, not in commands/lesson-12.8.sh's
--set-env-vars; ...`, then `the routine deploy:` and `$ make deploy-services SCRIPTS=commands/lesson-12.8.sh ...`,
then make's own output, then `documind-chat-...: CHAT_MAX_MODEL_CALLS gone; /health: max_model_calls 12`,
`REPRODUCED: ...`, the line `the lever, carrying the value in the deploy, is a change to your fork: ...`, and
`restored: CHAT_MAX_MODEL_CALLS unset, traffic on the latest revision; /health: max_model_calls 12`.

Make's own output is long (the Cloud Build log, the deploy, the invoker bindings, the checkpoint job, IAP, and
`make operators`). Keep its first line (`>> commands/lesson-12.8.sh (DEPLOY block)`), the deploy's `Service
[documind-chat] revision [...] has been deployed` lines and the last line, and put `...` where you cut. Keep every line
the drill itself prints, unchanged.

### 4. `data/smoke_chat.txt` (step 7)

Right after run 3. Expect `[PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s`, then
`[PASS] brain direct`, `[PASS] brain langchain`, `[PASS] brain langgraph` and `[PASS] brain adk`, each with its
latency, tools, citations, calls and `Rs`, then `[PASS] outsider refused  status=403 ...`, and
`6 passed, 0 failed`. Note in the review the sum of the four brain lines' rupees: it is this run's cost.

### 5. `data/detect_all.txt` (step 8)

After run 4. Expect thirteen blocks, each opening `== <id>: ...` and ending `FOUND: ...`, `nothing found`,
`nothing this checkout can tell` or `STOPPED: ...`, then `13 detectors: N found, M could not read`. The command
exits 1 when anything is found; that is expected. Three things the page counts on:

- pinned-traffic: `documind-chat: follows its latest revision (...)`;
- deploy-drops-hotfix: `documind-chat (commands/lesson-12.8.sh): nothing the next make deploy-services would change`,
  and `ADMIN_EMAILS=...: written back as ADMIN_EMAILS=admin@documind.example.com, the default, unless you pass
  ADMIN_EMAILS=...` under documind-admin and documind-ui (replace your address both times);
- agent-spend-outside-the-month: `FOUND`, with rupees on the chat rows from run 4's turns.

The rest depend on the lane's history and the checkout; record them as they come. If any of the three above differs,
say which in the review: the page's step 8 prose is written to them.
