# Lesson 5.8 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/05-mcp-agents/5.8-human-in-loop/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check (the build needs the chat pins and the SQLite
checkpointer, so use the chat venv):

    python pagekit/build.py 5.8 && python pagekit/check_lesson.py 5.8 && python pagekit/audit_pages.py 5.8

Everything else on the page is computed when it builds, from the kit: every transition the panel shows, through
`services/chat/approval.py`, `make approval-check`'s output (the kit's test file on the chat pins), and the offline
cells of step 5 (the pause, the second process, `ask_user`, the Change-it). The build also runs every lane cell below
against the kit's own chat service on stand-ins (agent.py's `chat()` with the LangGraph brain on a scripted model,
desk.py's door and case routes, `shared/cases.py`, `commands/desk_ops.py`, a fake Firestore and audit bucket, a fake
gcloud), so a cell that would fail on the lane fails the build first. The five runs below are batch 2's; batch 3's five,
for step 8 (the approval wired in behind acme's switch), follow them at the end of this file.

This is batch 2 of `plan/cohort-2-lesson-plan-2026-10-07.md` (section 6: Mon 2 - Wed 4 Nov); the plan estimates
Rs 2-8 for 5.8.

## Before the first run

- **The lane:** lesson 5.6's state. The Desk is deployed (its Terraform, and rag-api, the UI and the chat service with
  the Desk's code), acme's queues are loaded with your email in them (`make desk-queues`), the eval accounts are on
  their rosters and you may mint tokens as them (`make desk-operators`, `make roster`), and your roles are `employee`,
  `grc_member`, `ic_member:hyderabad` and `ic_member:pune`. acme's `desk_gate` is not `off` (lesson 5.6 leaves it
  unwritten, which is `rules`). The chat service serves the `langgraph` brain (lesson 5.1's deploy).
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `ME` and `NUMBER`. Steps 4 and 5
  (`make approval-check` and the offline cells) are not recorded: the build computes them.
- **Order, in one shell, in one sitting:** run 1 (step 3's first cell, which also sets `CHAT`, `SINCE108`, `sa` and
  `etok`); then the page's step 3 Desk page walk, not recorded but needed, because runs 4 and 5 show its row and its
  case; run 2; run 3; wait a minute for Cloud Logging; run 4; run 5.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`; the
  part of your email before the @ (runs 4 and 5 print it alone) `you`. Case ids, times, tokens and rupees may stay.
  `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a personal mailbox, and every
  string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/roles.txt` | 3, the People team's reader | seconds | Rs 0: one Firestore write and one audit event |
| - | (not recorded) | 3, the Desk page walk | two minutes | Rs 0 in model cost: the door answers, then the case routes |
| 2 | `data/escalate.txt` | 6, escalate | under a minute | one agent turn (the near miss), about Rs 1; the door's turn and the case are Rs 0 |
| 3 | `data/clarify.txt` | 6, clarify | a minute or two | three agent turns, about Rs 3 |
| 4 | `data/rows.txt` | 7, the log rows | seconds | Rs 0: one Cloud Logging read |
| 5 | `data/records.txt` | 7, the case and your role | seconds | Rs 0: a few Firestore reads |

**Where the rupees come from.** An agent turn on the LangGraph brain is usually one search, so one rag-api answer,
plus the loop's own model calls. The answer is Rs 0.45 at the course's typical 2,000 tokens in and 300 out
(`shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million, Rs 85 to the dollar); lesson 5.7's cost
table puts its gate's four answered turns, three of them agent loops, at about three rupees. So the four agent turns
here (one in run 2, three in run 3) come to about Rs 4. Each turn is
bounded by `CHAT_TURN_BUDGET_INR` (Rs 5: no model call starts once a turn has spent it), so the runs cannot pass about
Rs 20. The cells print each turn's rupees (`limits.cost_inr`): please note the total when you hand the files back.

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/roles.txt` (step 3)

```bash
export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" SINCE108="$(date -u +%FT%TZ)"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \
         --impersonate-service-account="$(sa "$1")"; }
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$ME" ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune,people_ops
```

Expect one JSON line: `"tenant": "acme"`, your email, `"before": ["employee", "grc_member", "ic_member:hyderabad",
"ic_member:pune"]`, `"after"` the same with `"people_ops"` added at the end, `"granted": ["people_ops"]` and
`"revoked": []`. If `before` lists other roles, your lane is not in lesson 5.6's state: say so (the page says "the four
roles lesson 5.6 gave you").

Then do the page's step 3 Desk page walk, signed in as yourself: Tell the Desk `Escalate this to a human please`, press
**Ask for a person**, write a sentence, **Next: check it before sending**, **Send**, then in **Your inbox** move it to
"Acknowledged (we have seen it)" with **Update**. Tell me if any label differs from the page's.

### 2. `data/escalate.txt` (step 6)

The page's step 6 "escalate" cell, as written (`TOKEN="$(etok evalacme)" python - <<'PY' ... PY`).

Expect, in this order:
- `  Escalate this to a human please`, then
  `    200  brain desk_gate  tool_calls []  model_calls 0  Rs 0.0  case_offer {'case_type': 'human_requested'}`, then the
  fixed reply wrapped on three lines ("You asked for a person. DocuMind does not answer this itself: ... where your
  company's DocuMind offers it.").
- `  How do I contact HR about payroll?`, then `    200  brain langgraph  tool_calls [...]` with `model_calls` of 1 or
  more, `Rs` above 0 and `case_offer None`, then the model's answer. The page says the brain "searched and answered from
  the documents": if `tool_calls` is empty, say so.
- `  draft    200  draft in people (People team), expires 0:30:00 after it was made`
- `  confirm  200  open, due 5 days, 0:00:00 after it opened: the company's own target: 5 days (case_queues.people.sla_days)`
- `  cancel   200  withdrawn, by the person who raised it`

The cell writes `~/lesson108_case.txt` for run 5.

### 3. `data/clarify.txt` (step 6)

The page's step 6 "clarify" cell, as written. Three blocks, `[lesson108]` twice and `[lesson108-new]` once, each with
`200`, its `tool_calls`, `model_calls`, `Rs` and `citations`, then the answer wrapped at 100 characters.

The handbook gives 60 days to a confirmed employee at grade E3 or above (NP-03) and 15 days during probation (PB-02).
Expect the first answer either to ask which applies or to give both with citations: tell me which (the page allows
both). Expect the second, on the same session, to answer 15 days for probation. The third, on a new session, has only
"I am still on probation." to go on: whatever the model makes of it is fine. If the second answer does not use the
first turn (it answers as if the thread were empty), say so: the page says the thread carries the question.

### 4. `data/rows.txt` (step 7)

The page's step 7 "log rows" cell, as written, a minute or more after run 3. Expect six lines, oldest first:
- `  desk_gate  user you ...  class human_requested  method rule  rules 2026-10-01.4`: the Desk page's turn (replace your
  email's local part with `you`);
- `  desk_gate  user documind-evalacme-sa ...  class human_requested  method rule  rules 2026-10-01.4`: run 2's;
- four `  chat       user documind-evalacme-sa  brain langgraph` lines, sessions `lesson108-esc`, `lesson108`,
  `lesson108`, `lesson108-new`, each with its tool calls, model calls, tokens and `cost_usd`.

More lines mean something else used the chat service since run 1 (another lesson's smoke, a UI tab): record them as
they are and tell me.

### 5. `data/records.txt` (step 7)

The page's step 7 "the case and your role" cell, as written. Expect `make cases`' table: the Desk page walk's case,
`human_requested`, queue `people`, status `acknowledged`, due about five days on; any of lesson 5.6's cases still open,
listed as `sensitive`; then `N open case(s): 0 due, 0 breached`. Run 2's case is not listed (withdrawn). Then:
- `  cases/<id>`
- `    human_requested withdrawn in people, source button, via direct, opened True`
- `    summary 'Lesson 5.8 test: please call me about my notice period.'  audit_pending []  token_sha256 64 hex digits`
- `  tenants/acme/roles/you@...: ['employee', 'grc_member', 'ic_member:hyderabad', 'ic_member:pune', 'people_ops'], set by you@...`
  (replace your email's local part with `you`, twice).

## After the runs

The lane keeps what the page's "What changed on your lane" box lists: `people_ops` in your roles, the acknowledged
case, three new threads in the chat service's checkpointer. Nothing needs undoing for later lessons.

## Batch 3 (Mon 16 - Wed 18 Nov): step 8, the approval wired in

Five more recordings, for the stretch the plan's section 7 names (5.8-B: the approval behind `agent_actions=approval`),
added on 13 October. They need the chat service redeployed with the kit at or after this change (the chat image: lesson
5.1's deploy), and the state above. The plan puts `make smoke-approval` at about Rs 10-15; the other four runs call no
model. Run them in one shell, in this order, in the same sitting, after step 3's first cell (`CHAT`, `sa`, `etok`).

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 6 | `data/switch.txt` | 8, the switch and the second person | seconds | Rs 0: two Firestore writes and one audit event |
| 7 | `data/smoke_approval.txt` | 8, the flow, live | two to four minutes | two turns that pause (one model call each) and two resumes (one each), plus any search the model asks for: about Rs 10-15 at most |
| 8 | `data/withdraw.txt` | 8, run the approved withdrawal | under a minute | Rs 0: the tombstone's Firestore writes, one audit event, one Firestore read for the sources |
| 9 | `data/approvals.txt` | 8, the records and the events | seconds | Rs 0: a few Firestore reads and one bucket listing |
| 10 | `data/restore.txt` | 8, the document back, the switch off | under a minute | Rs 0: the restore's rewrite, one Firestore write |

### 6. `data/switch.txt` (step 8)

The page's step 8 "switch acme on" cell, as written: `make agent-actions ... AGENT_ACTIONS=approval`, then
`make roles ... EMAIL="$(sa evalacme)" ROLES=employee,doc_approver`.

Expect two JSON lines. The first names `"tenant": "acme"`, `"desk_gate"` as your lane has it (`rules` unless an earlier
lesson wrote `on` or `off`), `"desk_max_parts"`, the routed Desk's mode, `"agent_actions": "approval"` and the note that
the services read it within 60 s. The second is `make roles`' line for `documind-evalacme-sa`: `"before": ["employee"]`
(no role document until now), `"after": ["doc_approver", "employee"]`, `"granted": ["doc_approver"]`. If `before` lists
other roles, say so.

### 7. `data/smoke_approval.txt` (step 8)

`make smoke-approval PROJECT="$PROJECT" TENANT=acme`, at least a minute after run 6 (the chat service reads the switch
once a minute). Expect nine `[PASS]` lines in this order: `paused` (with the 32-hex approval id, `waiting
['withdraw_document']` and the expiry 24 hours on), `held`, `self-approval refused`, `stranger 404`, `approver inbox`,
`approved` (by `documind-evalacme-sa@...`, with the resumed turn's model calls and rupees, then the model's answer),
`decided once`, `rejected` (with `refusals ['withdraw_document']` and the model's answer), `my records`; then
`9 passed, 0 failed` and the two commands run 8 and run 10 use. The model's two answers are its own words: whatever they
say is fine, as long as the first does not claim the document is gone and the second says nothing was withdrawn.

If `paused` fails with "the turn did not pause", the model answered in words instead of asking for the tool: run it
again once (a new session each run); if it fails twice, record the output as it is and say so, and the page's prose
changes with it. If it fails saying the switch is off, wait a minute after run 6 and run again.

### 8. `data/withdraw.txt` (step 8)

The page's step 8 "run the approved withdrawal" cell, as written. Expect `approval <32 hex digits>`, then two JSON
lines from `make withdraw-run`: `"event": "reconcile_withdrawn"` with `"gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.md"`,
its retired chunk ids and the fingerprint, and `"event": "reconcile_approved"` with `"status": "withdrawn"`,
`"requested_by"` documind-ui-sa, `"approved_by"` documind-evalacme-sa, `"run_by"` your account and the `make restore`
undo. Then `make sources`' header line and the townhall row with status `withdrawn`. Replace the project id and your
email as above; the chunk ids may stay.

### 9. `data/approvals.txt` (step 8)

The page's step 8 "the records and the events" cell, as written. Expect two records, oldest first: the first
`withdrawn  kind approval  waiting ['withdraw_document']`, `asked by documind-ui-sa@..., decided by documind-evalacme-sa@...,
audit_pending []`, and its `withdrawal acme/townhall_2026_q1.md, approved by documind-evalacme-sa@..., run by you@...,
withdrawn`; the second `rejected   kind approval`, same asker and decider, `audit_pending []`. Then
`today's acme events in the audit bucket: ['approval.approve', 'approval.reject', 'approval.request', 'approval.request', 'doc.withdraw']`
(more `approval.*` entries if run 7 was retried). Replace your email's local part with `you`.

### 10. `data/restore.txt` (step 8)

The page's step 8 "bring the document back" cell, as written. Expect `make restore`'s `"event": "reconcile_restored"`
line with the new generation and `"next": "ingest_reactivated inside the undo window, ...`, then `make agent-actions`'
JSON line with `"agent_actions": "off"`. A minute later, `make sources` (not recorded) should show the townhall row
`indexed` again: say so if it does not.

### After batch 3

The lane keeps `doc_approver` on `documind-evalacme-sa`, two approval records under `approvals/`, their five audit
events, two more threads in the checkpointer, and the townhall document restored. acme's `agent_actions` is `off`:
later lessons see the chat service as before.
