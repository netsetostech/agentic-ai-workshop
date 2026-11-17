# Lesson 10.11 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.11-incident-remediation/data/`. Every other output on the page
is the kit's own, produced at build time by the page's offline cells (`make remediate OFFLINE=1`, every recording,
`RUNBOOKS=1`, the kit's tests). Record each file once from your lane, then rebuild and check:

    python pagekit/build.py 10.11 && python pagekit/check_lesson.py 10.11 && python pagekit/audit_pages.py 10.11

The batch is **3** (Mon 16 - Wed 18 Nov, the plan's section 6: "10.11's held fault"). The commands are the kit PR's
(#141, `claude/kit-remediate`), in its order, with this page's variables.

## Before the run

- **The lane:** deployed by lesson 0.3, with documind-chat serving its latest revision and its traffic following the
  latest (`HOLD=1` refuses a pinned service), and no fault held: no `deploy/.fault-hold` in the kit.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT` and `REGION`. `make` takes `REGION` from that export.
- **One folder first:** `mkdir -p evals/reports`. `SAVE=` writes there, and a fresh clone has no such folder (git
  ignores it, and only the eval tools make it): without it remediate stops after its three reads, before it prints the
  plan, with `STOP: cannot write evals/reports/...`. The page's cells make the folder too; it is a kit gap, reported.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed. A
  `2>&1 | tee` line is given for each run; copy the file into `data/` under the name in the table.
- **Placeholders:** project id `documind-ai-YOUR-ID`, project number `NUMBER`, your email `you@your-company.com`.
  Revision names and times may stay. The three `SAVE=` recordings already carry the placeholders (`save_state()`
  replaces the project id and number, and refuses a state that still holds either): copy them into `data/` as they are.
  `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a personal mailbox, and every
  string in `.publish-deny`.
- **Restore in the same sitting:** from run 1 to run 6 every agent turn on the lane fails (or stops).

## The runs, in order

| # | Data file | Page step | Time | Cost (rupees, from the kit's ceilings; the kit PR's estimate beside it) |
|---|---|---|---|---|
| 1 | `data/hold.txt` | 3, hold the fault | a minute or two | the hold's smoke: the direct answer, about Rs 2.33 at rag-api's ceiling (8,000 in and 2,048 out at `gemini-3.6-flash`'s $1.50 / $7.50, `shared/prices.py`); the agent turns fail at their first model call. PR: about Rs 0.5 |
| 2 | `data/plan_held.txt`, `data/remediate_held.json` | 3, read the plan | seconds | Rs 0: three reads |
| 3 | `data/rollback.txt` | 3, the rollback | seconds | Rs 0 |
| 4 | `data/smoke_rolled_back.txt` | 3, verify | about a minute | about Rs 17.33 at the ceilings: three agent turns at `CHAT_TURN_BUDGET_INR` Rs 5 each (checked before each model call, so a turn can end one call past it), and the direct answer. PR: Rs 3-6 |
| 5 | `data/plan_rolled_back.txt`, `data/remediate_rolled_back.json` | 3, read the lane again | seconds | Rs 0 |
| 6 | `data/restore.txt` | 3, restore | a minute or two | Rs 0: two service updates, no model call |
| 7 | `data/smoke_restored.txt` | 3, verify again | about a minute | about Rs 17.33 at the ceilings. PR: Rs 3-6 |
| 8 | `data/plan_restored.txt`, `data/remediate_restored.json` | 3, verify again | seconds | Rs 0 |
| 9 | `data/lane_policies.txt` | 4, the lane's policies | seconds | Rs 0: one Monitoring API GET (added to the PR's list: the page's direct read) |

**Total:** about **Rs 36.98** at the kit's own ceilings (the build computes it: Rs 2.33 + 2 x Rs 17.33; a turn's budget
is checked before each model call, and a truncated answer's retry bills both attempts, so this is a ceiling in the kit's
terms, not a hard cap); the kit PR estimates **about Rs 7-13**, inside the plan's budget of Rs 10-20 for this lesson. The model calls are the three smokes'
only; every remediate run is three reads at Rs 0, and the offline first command is free.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: the build stops with the reason, and the prose changes with it.

### 0. Offline first (Rs 0, not recorded: the page computes it)

```bash
make remediate OFFLINE=1
```

### 1. `data/hold.txt` (step 3)

```bash
mkdir -p evals/reports ~/p1011
make incident-drill PROJECT=$PROJECT HOLD=1 2>&1 | tee ~/p1011/hold.txt
```

Expect `>> documind-chat: CHAT_MODEL=gemini-3.6-flsh (FAULT=model), held until make incident-drill RESTORE=1`, the
smoke's own lines (`[PASS] health`, `[PASS] brain direct`, three `[FAIL] brain ...  status=500`, `2 passed, 3 failed`),
then `>> held: documind-chat-... carries CHAT_MODEL=gemini-3.6-flsh; documind-chat-... served before it`.
**If the smoke passes instead** (`WARNING: the smoke passed on the fault`), the mistyped model does not fail the agent
turns on a lane: the kit's `UNOWNED.md` calls this unverified until this run. Then run
`make incident-drill PROJECT=$PROJECT RESTORE=1`, hold `FAULT=model_calls` instead
(`make incident-drill PROJECT=$PROJECT FAULT=model_calls HOLD=1`), record that, and tell whoever owns the page: step 3's
prose, step 10's first row and the fixture-based expectations name `FAULT=model`.

### 2. `data/plan_held.txt` and `data/remediate_held.json` (step 3)

```bash
make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_held.json 2>&1 | tee ~/p1011/plan_held.txt
cp evals/reports/remediate_held.json ~/p1011/
```

Expect `Diagnosis - rule bad_revision`, `the change  CHAT_MODEL: unset -> "gemini-3.6-flsh"` (or the value it had
before, if your lane set one), step 1 rolling back by name to the revision run 1 named as serving before, the restore's
two commands with the note that `make incident-drill RESTORE=1` runs both, `0 model calls. remediate ran 3 reads and
changed nothing on the lane.` and `saved: evals/reports/remediate_held.json`. A line reaches Cloud Logging a few seconds
after it is written: if this reads `no_failure` with "It answered nothing in the window", wait a few seconds and run it
again. The build checks the text for `Diagnosis - rule bad_revision`, and replays the saved state through the page's
desk, which must read `bad_revision` too.

### 3. `data/rollback.txt` (step 3)

```bash
PREV=REVISION   # the revision step 1 of run 2's plan names
gcloud run services update-traffic documind-chat --region "$REGION" --project "$PROJECT" --to-revisions "$PREV=100" 2>&1 | tee ~/p1011/rollback.txt
```

Paste the command exactly as run 2 printed it if you prefer; record what gcloud prints (replace the project number in
any URL with `NUMBER`). Expect the traffic at 100% on `$PREV`.

### 4. `data/smoke_rolled_back.txt` (step 3)

```bash
make smoke-chat PROJECT=$PROJECT 2>&1 | tee ~/p1011/smoke_rolled_back.txt
```

Expect every brain to pass and the outsider refused (`6 passed, 0 failed`): the traffic is on the revision before the
fault. Replace the project number in the `target:` line with `NUMBER`. The build sums the `Rs` each `[PASS] brain`
line reports and states it beside the ceiling.

### 5. `data/plan_rolled_back.txt` and `data/remediate_rolled_back.json` (step 3)

```bash
make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_rolled_back.json 2>&1 | tee ~/p1011/plan_rolled_back.txt
cp evals/reports/remediate_rolled_back.json ~/p1011/
```

Expect `Diagnosis - rule rolled_back`, `1. Roll back: done. ... takes the traffic by name.`, the verify with "So far in
the window", the restore and the verify again; no `--to-revisions` line. Run it within the hour of run 1: once the fault's
lines are older than the window (`SINCE=`, default 1h), a pinned lane reads `pinned_new` instead.

### 6. `data/restore.txt` (step 3)

```bash
make incident-drill PROJECT=$PROJECT RESTORE=1 2>&1 | tee ~/p1011/restore.txt
```

Expect `>> documind-chat: CHAT_MODEL unset again, so the default applies (a new revision)` (or `CHAT_MODEL=<before>
again`), `>> restored: documind-chat-... takes all the traffic, following the latest revision; deploy/.fault-hold
removed`, and the verify line.

### 7 and 8. `data/smoke_restored.txt`, `data/plan_restored.txt` and `data/remediate_restored.json` (step 3)

```bash
make smoke-chat PROJECT=$PROJECT 2>&1 | tee ~/p1011/smoke_restored.txt
make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_restored.json 2>&1 | tee ~/p1011/plan_restored.txt
cp evals/reports/remediate_restored.json ~/p1011/
```

Expect `6 passed, 0 failed`, then `Diagnosis - rule no_failure` with the restore's revision serving, following the
latest revision, and the fault's revision listed with its 5xx answers. The page shows the two outputs in one window, the
smoke's first.

### 9. `data/lane_policies.txt` (step 4)

Paste the page's step 4 cell ("Read it on your lane: the policies your lane holds") as it stands, and record its output.

Expect `10 alert policies on the lane` on a lane deployed with the defaults: 3 `rollback` and 7 `person`, and
`declared by the kit and not on this lane: 6, behind desk_gate_alerts, desk_router_alerts, reconcile_job`. A lane with
a Desk switch or the nightly walk on shows more. A `no row` line is a finding: a policy on the lane that
`ops/runbooks.json` has no row for.

## After the run

Copy the twelve files into `lessons/10-agent-patterns/10.11-incident-remediation/data/` (nine `.txt`, three `.json`),
rebuild and check as above. The three recordings join the Level 0 desk as "the author's lane", replayed by the same
rules; the build checks each one's rule (`bad_revision`, `rolled_back`, `no_failure`) and that its project id is the
placeholder.
