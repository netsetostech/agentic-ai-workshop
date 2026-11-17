# Lesson 10.9 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.9-managed-agents/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check. Build with the chat venv: the build reads the pinned
google-adk, and imports the staged package in the venv lesson 10.6's build keeps (it makes it if missing):

    <venvs312\chat python> pagekit/build.py 10.9 && python pagekit/check_lesson.py 10.9 && python pagekit/audit_pages.py 10.9

The build reads more than it shows: `probe_facts.md`'s status column fills the fact cells of the Level 0 table and
panel, so keep the probe's table rows as it writes them (`| # | Fact | Status | Finding |`). The build refuses a file
that lacks one of facts 1-9, 11 and 12.

The page's prose states what each recording should show, read from the kit's code (`deploy/commands/managed_peer.py`).
If a recording disagrees, the recording is right: say so, and the prose changes with it. A command that stops on a
probe fact (exit 3) is recorded as it stopped; the page keeps it, and the pull request names the fact.

## Before the runs

- **Batch 0 (Mon 19 - Wed 21 Oct 2026):** run 0, the probe, from the authoring repository (`tools/` is never
  published). Its table decides `MANAGED_PEER_REGION` (fact 1), `MANAGED_PEER_GRANT_ROLE` (fact 2) and `AIPLATFORM_PIN`
  (fact 11) in `deploy/mk/managed.mk`: set them in a kit pull request before batch 3, not in this page's.
- **Batch 3 (Mon 16 - Wed 18 Nov 2026), runs 1 to 11, in one sitting:** the instance run 2 creates bills until run 10
  deletes it. The lane deployed by lesson 0.3's `make up` with this branch's kit, the Cloud Run peer and `documind-mcp`
  up, and `make operators` done, so you may mint tokens as `documind-ui-sa` and `documind-outsider-sa`.
- **Where:** Cloud Shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's), which
  exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme` and `NUMBER`. Run 2 makes `~/managed-peer-venv` the first time
  (google-adk at the peer's pin and google-cloud-aiplatform).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, nothing trimmed but secrets.
  Run 2's lines include ADK's own deploy progress; keep them.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (it is in every instance name,
  `projects/NUMBER/locations/...`, in the URLs, in the service agent `service-NUMBER@gcp-sa-aiplatform-re...`, and in
  any Google-managed account run 2's WHO MAY CALL IT lists, such as `NUMBER-compute`); the instance id `ENGINE_ID`;
  session ids `SESSION_ID`; your email `you@your-company.com`. The kit counts people and never names them. Times,
  latencies, token counts and rupees stay. `check_lesson.py` refuses a real project id, a project number in a resource
  path or a Cloud Run URL, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

Rupees are priced from `deploy/shared/prices.py`, as the page's step 9 prices them. rag-api's answer inside `retrieve`
costs at most what `services/rag-api/config.py`'s budget allows one answer: 8,000 tokens in and 2,048 out at
gemini-3.6-flash's list price (USD 1.50 / 7.50 per million, Rs 85 to the dollar), Rs 2.33. The peer's own calls, about
two a question (`mk/managed.mk`'s count), are printed by each question in tokens and rupees. Agent Engine's own charges
(the image's build, the instance while it exists, its sessions) are not stated anywhere in the kit: fact 12.

| # | Data file | Page step | Batch | Time | Cost |
|---|---|---|---|---|---|
| 0 | `data/probe_facts.md` | 5, the facts table; the fact cells of step 1 | 0 | about 20 to 30 minutes (the probe's own estimate) | the probe's cost note: about four Gemini Flash calls of a few tokens; the plan's estimate for batch 0, a few rupees; Agent Engine's charges, fact 12 |
| 1 | none | 4, the dry run of up | 3 | seconds | Rs 0: the page's build prints it; yours differs only in the project id |
| 2 | `data/up.txt` | 6, deploy | 3 | 10 to 20 minutes (the kit's estimate) | Agent Engine's charges from now until run 10 (fact 12) |
| 3 | `data/ask_acme.txt` | 6, acme's question | 3 | the first question after the deploy may wait for a cold start (fact 4) | at most Rs 2.33 for rag-api's answer, plus the peer's calls |
| 4 | `data/ask_zeta.txt` | 6, naming zeta | 3 | seconds | the peer's calls only: the roster refuses before rag-api |
| 5 | `data/ask_cloudrun.txt` | 6, the Cloud Run peer | 3 | seconds, or a Cloud Run cold start | at most Rs 2.33, plus the peer's calls |
| 6 | `data/trace.txt` | 7, trace | 3 | up to 150 s (120 for spans, then 30 for rows) | Rs 0: reads |
| 7 | `data/sessions.txt` | 7, sessions | 3 | seconds | Rs 0: reads |
| 8 | `data/smoke.txt` | 8, the proof | 3 | a few minutes, with waits of up to 120 s for rows and for spans | at most Rs 9.32 for four rag-api answers, plus the peer's calls on six questions |
| 9 | `data/compare.txt` | 8, the table | 3 | instant | Rs 0 |
| 10 | `data/down.txt` | 10, down | 3 | up to a minute per instance (read back every 10 s) | Rs 0 |
| 11 | `data/down_again.txt` | 10, down again | 3 | seconds | Rs 0 |

**Total, batch 3:** at most Rs 13.98 for rag-api's six answers (runs 3, 5 and the smoke's four), plus the peer's own
calls on nine questions (about eighteen flash calls; each run prints its share), plus Agent Engine's charges for the
sitting, which no page states until fact 12 is read. Batch 0's probe: a few rupees, by the plan's estimate.

### 0. `data/probe_facts.md` (step 5; batch 0)

```bash
python tools/probe_agent_stack.py --project "$PROJECT" --run-note                         # the prerequisites and commands
~/probe-venv/bin/python tools/probe_agent_stack.py --project "$PROJECT"                   # a dry run: every call printed
~/probe-venv/bin/python tools/probe_agent_stack.py --project "$PROJECT" --yes             # the run
~/probe-venv/bin/python tools/probe_agent_stack.py --project "$PROJECT" --cleanup --yes   # only if anything was left
```

Fill its AUTHOR lines (rows 4 and 12) from the pricing page, as its run note says. Then copy the title line of
`plan/agent-engine-probe-<date>.md` (it carries the date in brackets) and its first table into `data/probe_facts.md`.
Every identifier is already replaced by the probe's scrubber; check anyway.

### 1. The dry run (step 4; nothing recorded)

```bash
make managed-peer-up DRY_RUN=1 PROJECT="$PROJECT" REGION="$REGION"
```

Expect the page's eight `would call:` lines with your project id. Nothing is created or written.

### 2. `data/up.txt` (step 6)

```bash
make managed-peer-up PROJECT="$PROJECT" REGION="$REGION"
```

Expect the dry run's eight calls as `call:`, `created projects/NUMBER/...`, the grant line, the stage line, ADK's own
progress, `deployed in N s`, the read back (`serviceAccount documind-agent-sa@...`; `minInstances` absent or 0;
`maxInstances 1`; the env names), then STANDING COST and WHO MAY CALL IT, naming at least `documind-agent-sa`,
`documind-api-sa`, `documind-chat-sa`, `documind-ingest-sa` and `documind-ui-sa`, and counting the people.

### 3 to 5. `data/ask_acme.txt`, `data/ask_zeta.txt`, `data/ask_cloudrun.txt` (step 6)

```bash
make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION"
make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION" TENANT=zeta
make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION" HOST=cloudrun
```

One file each. acme: a `tool call: retrieve(...)`, its `result:`, an `answer:` with five years, then
`agent_engine in asia-south1: the expected answer; first event after X s, done in Y s; N model call(s), ... tokens, Rs R`
and `first call after the deploy: True`. zeta: the result carries `... is not on tenant 'zeta''s roster`, and the
verdict is `refused by the roster`. Cloud Run: `cloud_run in asia-south1: the expected answer; done in Y s; ...`.

### 6. `data/trace.txt` (step 7)

```bash
make managed-peer-trace PROJECT="$PROJECT" REGION="$REGION" SINCE=15
```

Run it within fifteen minutes of run 3. Without `SINCE`, trace reads the window of the last managed question, which is
zeta's, and documind-mcp writes no row for a question its roster refuses; with it, the rows cover both hosts' acme
questions. Expect the span names and label keys, two `documind-mcp row: tool retrieve, tenant acme, caller
documind-agent-sa@...` lines, the runtime's own line, and `message content in the spans: not checked` (the smoke checks
it). If no span shows yet, run it again: spans can take minutes.

### 7. `data/sessions.txt` (step 7)

```bash
make managed-peer-sessions PROJECT="$PROJECT" REGION="$REGION"
```

Expect two sessions for `documind-ui-sa` (runs 3 and 4), the newest event by event, `as another-user: refused by ADK's
session service - ... - a check in this client, made after the read (fact 9)`, and the API's own read returning it.

### 8. `data/smoke.txt` (step 8)

```bash
make managed-peer-smoke PROJECT="$PROJECT" REGION="$REGION"
```

The instance from run 2 exists, so the smoke uses it and does not delete it. Expect eight `[PASS]` lines, or a `[SKIP]`
with its reason where rows or spans were slow or the runtime's line was not found (its log's resource type is
unverified); the Cloud Run peer's three lines; the table; and `8 passed, 0 failed, 0 skipped`.

### 9. `data/compare.txt` (step 8)

```bash
python commands/managed_peer.py compare
```

The table over runs 3 to 5 and the smoke's records.

### 10 and 11. `data/down.txt`, `data/down_again.txt` (step 10)

```bash
make managed-peer-down PROJECT="$PROJECT" REGION="$REGION"
make managed-peer-down PROJECT="$PROJECT" REGION="$REGION"
```

One file each. The first: `deleted, and read back gone: projects/NUMBER/...` and `grant taken back: ...`. The second:
`nothing to delete: no documind-managed-peer* instance in asia-south1` and `grant: none recorded as added by make
managed-peer-up; nothing to take back`. If the first exits 4, run the delete command it prints, then record both
downs again.
