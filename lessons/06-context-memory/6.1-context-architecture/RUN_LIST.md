# Lesson 6.1 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/06-context-memory/6.1-context-architecture/data/`. Record each file once from your
lane, replace any identifier with the course's placeholders, then rebuild and check. The build runs the kit's brains
offline, so it needs the chat image's pins (`venvs312/chat`):

    <venvs312/chat python> pagekit/build.py 6.1 && python pagekit/check_lesson.py 6.1 && python pagekit/audit_pages.py 6.1

Every offline output on the page (step 1's widget, steps 5, 8 and 9's offline cells) is computed by the build from
the kit and needs no run.

## Before the first run

- **The lane:** up from lesson 0.3, with rag-api (`documind-api`) serving and acme on its roster. `make
  context-sources` does not use the chat service: it builds the brains on your machine, in `~/graph-venv`, and asks
  Gemini on location global and your rag-api as `documind-ui-sa` (the target sets `RAG_API_URL` and
  `DOCUMIND_IMPERSONATE_SA`). Your account needs Vertex AI on the project and Token Creator on `documind-ui-sa`, as
  Module 0 granted.
- **acme's pin:** on the kit's own index for the runs, as the page's setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Put it back after run 10:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=rag_engine`.
- **The Desk (runs 7 and 9):** the statute desk searches the classes `statute` and `guidance`. A row on the lane is
  `unknown` until lesson 10.4's doc_type registry pins its class, and then the desk's searches find nothing. Run them
  on a lane with acme's registry in place. If yours has none, record anyway and tell the page's editor: step 7 of the
  page describes that case, but the comparison in step 8 needs passages.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's setup block, which exports
  `PROJECT`. The first run makes `~/graph-venv` if it is missing and installs `services/chat/requirements.txt` into it:
  a few minutes, and pip's notices before the output are not part of the recording.
- **What to record:** what the terminal shows for the command, stdout and stderr together, nothing trimmed. Record the
  whole output of runs 1 and 2 too: the page's step 6 shows only their probe blocks, and the build cuts those out
  itself (from the line starting `probe (` to the end).
- **Placeholders:** the output names no project, account or URL; check anyway. A project id becomes
  `documind-ai-YOUR-ID`, a project number `NUMBER`. `check_lesson.py` refuses a real project id, a project number in
  a URL or resource path, a personal mailbox, and every string in `.publish-deny`.
- **What the runs leave:** rag-api logs each search as it logs any: a `query` row per chat-brain or direct search,
  with the brain's name, and a `passages` row, no tokens and no cost, per Desk search. No thread, no chat row, nothing
  configured.

## The runs

The batches are the plan's section 6 (`plan/cohort-2-lesson-plan-2026-10-07.md`): batch 1 is Mon 26 - Wed 28 Oct, batch
2 is Mon 2 - Wed 4 Nov. Batch 1 is the probe: whether `count_tokens` on location global honours `system_instruction`
and `tools` (both declaration forms) and how far its count is from the bill. If it refuses or ignores a field, the
counts are still printed (estimated, marked `~`), but tell the kit's owner before batch 2.

| # | Batch | Data file | Command | Page step | Cost |
|---|---|---|---|---|---|
| 1 | 1 | `data/probe_langgraph.txt` | `make context-sources PROJECT=$PROJECT BRAIN=langgraph` | 6, the probe | about Rs 1.5 |
| 2 | 1 | `data/probe_adk.txt` | `make context-sources PROJECT=$PROJECT BRAIN=adk` | 6, the probe | about Rs 1.5 |
| 3 | 2 | `data/lane_langchain.txt` | `make context-sources PROJECT=$PROJECT BRAIN=langchain` | 7 | about Rs 1.5 |
| 4 | 2 | `data/lane_langgraph.txt` | `make context-sources PROJECT=$PROJECT BRAIN=langgraph` | 7, and step 8's baseline | about Rs 1.5 |
| 5 | 2 | `data/lane_adk.txt` | `make context-sources PROJECT=$PROJECT BRAIN=adk` | 7 | about Rs 1.5 |
| 6 | 2 | `data/lane_direct.txt` | `make context-sources PROJECT=$PROJECT BRAIN=direct` | 7 | about Rs 1 |
| 7 | 2 | `data/lane_desk.txt` | `make context-sources PROJECT=$PROJECT BRAIN=desk` | 7, and step 8's Desk baseline | about Rs 0.5 |
| 8 | 2 | `data/lane_langgraph_topk3.txt` | `make context-sources PROJECT=$PROJECT BRAIN=langgraph TOP_K=3` | 8 | about Rs 1 |
| 9 | 2 | `data/lane_desk_topk3.txt` | `make context-sources PROJECT=$PROJECT BRAIN=desk TOP_K=3` | 8 | about Rs 0.5 |
| 10 | 2 | `data/lane_langchain_turns3.txt` | `make context-sources PROJECT=$PROJECT BRAIN=langchain TURNS=3` | 9 | about Rs 5 |

Batch 1 is about Rs 3 and batch 2 about Rs 13 (Rs 11-14): about Rs 16 in all. The estimates are the kit builder's,
at list price from `shared/prices.py` (gemini-3.6-flash, $1.50 in and $7.50 out per million tokens, Rs 85 to the
dollar). Most of a chat-brain turn is rag-api's answer: at most `max_context_tokens` 8,000 tokens in, Rs 1.02, plus
its output and thinking at the output rate. The chat model's two calls carry a few thousand tokens between them.
`count_tokens` is not billed. Each run prints its own cost in its last lines (`the turn ... at list price`); write
the batch's sum in the commit message.

Record runs 4 and 8, and runs 7 and 9, in the same sitting: the page compares them.

## What each recording should show

Read from the kit's code (`commands/context_sources.py`'s `render()`). If a recording disagrees, the recording is
right: say so, and the prose changes with it.

- **Every run:** the header `context sources: one turn on brain B, tenant acme, ...`, the three `on your lane:` lines,
  the question, then each model call: `model call N of M (gemini-3.6-flash): in X (Y cached), out Z (W thinking): Rs
  R`, one line per source (a `~` before a count is an estimate), the residual with `billed X, counted Y`, and what the
  call asked for. Under a search: `search: top_k 5; N citations back, C characters` and `inside it, rag-api's own call
  (its usage): in X, out Y: Rs R`. Then the turn by source, `the model calls ... the turn's Meter (limits.py) charged
  Rs R for N calls` (the same rupees on both sides), `rag-api, inside`, `the turn`, and the answer, a real one citing
  `[n]`.
- **The probe (every run with a model call):** `probe (workshop lesson 6.1, batch 1): count_tokens on location global,
  gemini-3.6-flash`, then `system_instruction: honoured: +N`, `tools: honoured: +N` and `contents: counted` when the
  endpoint takes them, and `call 1's request: counted X, billed Y (prompt_token_count), residual Z; K count_tokens
  requests, none billed`. Expect call 1's residual to be a few tokens at most. Call 2's residual is in its own lines:
  note it, the page discusses it (a thought signature is one candidate).
- **Runs 1 and 4 (langgraph), 3 (langchain):** `a system prompt of 426 characters, the brain's own` and `2 tool
  declarations (retrieve, calculate_processing_cost), each with its parameters`.
- **Runs 2 and 5 (adk):** `a system prompt of 483 characters, the brain's own and then the framework's 'You are an
  agent. Your internal name is "documind_adk".'` and `each with its parametersJsonSchema`.
- **Run 6 (direct):** `no model call of the chat's own: one retrieve, and rag-api's grounded answer comes back with it
  (brains.DirectBrain).`, the search with rag-api's own call, `the turn: no model call of the chat's own`, and no probe.
- **Runs 7 and 9 (desk):** `brain desk, desk statute`, `4 tool declarations (retrieve, gratuity_estimate,
  statutory_deadline, threshold_check)`, `search: top_k 5; N passages back` (`top_k 3 (TOP_K; 5 asked)` in run 9),
  `/v1/passages: no model call inside the search`, and `rag-api, inside` at Rs 0.0000.
- **Runs 8 and 9 (TOP_K=3):** the header's `every search sends top_k 3 (TOP_K), whatever was asked` and the search's
  `top_k 3 (TOP_K; 5 asked)`. On langgraph, rag-api's `in` should be lower than run 4's by about two chunks, while the
  tool results stay close to run 4's; on the Desk, fewer passages and smaller tool results than run 7's.
- **Run 10 (TURNS=3):** `turn 3 of one thread, after 2 earlier questions`, `the 2 earlier turns, not measured: N model
  calls and M searches, Rs R`, and a `thread so far` line with the same count in each call.
