# Lesson 10.7 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.7-a2a-handoff/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check. Build with the 3.12 chat venv, credentials isolated
(APPDATA, CLOUDSDK_CONFIG and USERPROFILE in a fresh temp dir; no GOOGLE_APPLICATION_CREDENTIALS). The build serves the
kit's peer offline in the venv lesson 10.6's build keeps (`%TEMP%/agents_workshop/venv-a2a`, made if missing), and lays
that venv's a2a-sdk 1.1.2 and protobuf 6.33 over the chat venv for the chat side:

    <venvs312\chat python> pagekit/build.py 10.7 && python pagekit/check_lesson.py 10.7 && python pagekit/audit_pages.py 10.7

Everything else on the page is computed at build time, offline and at Rs 0: `make handoff` on and off (the kit's
`handoff.sh` against a stub gcloud), the gate cell, the peer's `/health`, the hand-off end to end (the kit's chat app
and ADK brain to the kit's peer, Gemini scripted on both sides), the scripted loop stopped at 12, the drill's two
verdict lines, `make check-callers GRAPH=1` and its Change-it, and the five chains with `PEER_CHAIN` off and on.

The page's prose states what each recording should show, read from the kit's code. If a recording disagrees, the
recording is right: say so, and the prose changes with it.

## Before the runs

- **The lane:** deployed by lesson 0.3's `make up`, with lesson 10.6's peer and `documind-mcp` up and `make operators`
  done, so you may mint tokens as `documind-ui-sa`. The UI runs need your own account on acme's roster (Module 0).
- **Where:** Cloud Shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's), which
  exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme` and `NUMBER` and defines `tok`. Step 3's cell exports
  `SINCE107`, `CHAT` and `AGENT`; run it first in each batch's shell.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, nothing trimmed but secrets.
  For the UI, copy the caption line under each answer (`brain: adk · tools: ... · N ms · Rs ...`), one per question.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`.
  Hand-off ids, task ids, times, seconds, latencies and rupees stay. `check_lesson.py` refuses a real project id, a
  project number in a URL or resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

Rupees are the kit pull requests' estimates, made before any run (10.7-A: `make smoke-agent` about Rs 3 and
`make agent-drill` about Rs 2.2; 10.7-B: `make smoke-handoff` about Rs 3.6, `make smoke-chat` about Rs 4.7 and the
deputy cell about Rs 1.2), at `deploy/shared/prices.py`'s list price for gemini-3.6-flash: USD 1.50 per million input
tokens and 7.50 per million output tokens, Rs 85 to the dollar, so Rs = 85 × (T_in × 1.50 + T_out × 7.50) / 10^6 for
the tokens a chat turn and a peer task are assumed to use. The UI's two turns, which no pull request priced, are put
at the smoke's two. The recordings carry the real rupees, and these estimates change with them.

| # | Data file | Page step | Batch | Command | Cost |
|---|---|---|---|---|---|
| 1 | none | setup box | before Wed 11 Nov 2026 (10.7-A; with lesson 5.5's run list) | `make build deploy-services SERVICES=agent SCRIPTS=commands/lesson-8.4.sh PROJECT=$PROJECT REGION=$REGION` | Cloud Build only; no model call |
| 2 | none (the line is lesson 5.5's) | 5 | before Wed 11 Nov 2026 | `make limits PROJECT=$PROJECT REGION=$REGION`: the peer's `model calls a task` line reads 12 | Rs 0 |
| 3 | none | 5 | before Wed 11 Nov 2026 | `make smoke-agent PROJECT=$PROJECT REGION=$REGION`: still `5 passed, 0 failed` with the cap | about Rs 3 |
| 4 | `data/agent_drill.txt` | 5, trip the cap | before Wed 11 Nov 2026 | step 5's drill cell, `make agent-drill` | about Rs 2.2 (two tasks, three model calls) |
| 5 | none | setup box | 4 (Mon 23 - Wed 25 Nov 2026) | `make build deploy-services SERVICES=chat SCRIPTS=commands/lesson-12.8.sh PROJECT=$PROJECT REGION=$REGION` | Cloud Build only |
| 6 | none (the page computes it) | 3, `make handoff` | 4 | step 3's cell | Rs 0 |
| 7 | `data/ui_captions.txt` | 3, the UI | 4 | the two questions in the UI, brain `adk` | about Rs 4 (two turns, as the smoke's two) |
| 8 | `data/smoke_handoff.txt` | 6, the smoke | 4 | `make smoke-handoff` | about Rs 3.6 |
| 9 | none | not shown | 4 | `make smoke-chat PROJECT=$PROJECT REGION=$REGION` with the hand-off on: the chat's own smoke still passes | about Rs 4.7 |
| 10 | `data/deputy.txt` | 6, the confused deputy | 4 | step 6's deputy cell (it ends with `make handoff`, which puts `PEER_ACCOUNT` back) | about Rs 1.2 (the chat's own calls; the gate sends nothing) |
| 11 | `data/logs.txt` | 7 | 4 | step 7's cell (`sleep 20`, then two log reads) | Rs 0 |
| 12 | none (the page computes it) | 7, switch off | 4 | `make handoff OFF=1` | Rs 0 |
| 13 | none (the page computes both) | 8 | 4 | `make check-callers GRAPH=1`, then the Change-it cell, to confirm on Cloud Shell | Rs 0 |
| 14 | none | 9 | 4 | step 9's first cell: `make deploy-services SCRIPTS=commands/lesson-8.4.sh PEER_CHAIN=on ...` | Cloud Build only; no model call |
| 15 | `data/chain_reject.txt` | 9, two chained tasks | 4 | step 9's second cell | Rs 0: both refused before any model call |

**Total:** about Rs 19 of model calls, inside the plan's Rs 10-20 for lesson 10.7. Runs 1-4 are 10.7-A's (about Rs 5);
runs 5-12 10.7-B's (about Rs 10, and about Rs 4 for the UI's two turns, which the page adds); runs 13-15 10.7-C's
(Rs 0 of model spend).

## What each recording should show

- **`agent_drill.txt`:** `>> documind-agent: /health names max_llm_calls 12`, `ADK_MAX_LLM_CALLS=1`,
  `/health: max_llm_calls 1`, then `[PASS] task failed  status=200 state=failed` with the limit of 1 in its words,
  `>> restored ADK_MAX_LLM_CALLS=12`, and `[PASS] task completed` with the five-year answer. An image from
  before the cap stops at the first line and changes nothing: run 1 first.
- **`ui_captions.txt`:** two caption lines: `tools: documind_peer` for the first question, and `documind_peer, retrieve`
  (in either order) for the second. Unverified until this run: whether Gemini picks `documind_peer` from its
  description. If it does not, record what it did; the page's step 3 prose changes with it.
- **`smoke_handoff.txt`:** `[PASS] adk hands off  tools=[...'documind_peer'...] handoffs=[('answered', 'completed', S)]`
  with S inside 75, `[PASS] langchain answers alone`, `2 passed, 0 failed`. This is the proof's first half on a lane:
  A2A through Cloud Run's IAM with chat-sa's token, and `tenants_of` on Firestore, both unverified until now.
- **`deputy.txt`:** the `>> documind-chat: PEER_ACCOUNT=documind-ui-sa ...` line; `tool_calls: ['documind_peer']`,
  `refusals: ['documind_peer']`; `hand-off 1: refused, budget None, the peer's task None` and the gate's
  `(a confused deputy)` reason; an answer that says the peer was not asked; then `make handoff`'s three lines.
- **`logs.txt`:** one hand-off line for each hand-off since step 3 (the two UI turns, the smoke's ADK turn, and the
  deputy's refusal, the only one with `rosters 3`); the ADK chat rows with `documind_peer` among their tools and
  `handoffs key: False`. If a line is missing, wait and run the cell again: Cloud Logging can lag.
- **`chain_reject.txt`:** `the peer's /health: peer_chain on, max_llm_calls 12`, then both chains `rejected, history
  ['user']` with the two refusal sentences the build shows. Unverified until this run: the metadata reaching the
  executor on a Cloud Run peer, not only on the kit's `to_a2a` offline.
