# Agents and MCP: plan for the production gaps (29 September 2026)

A review of the agent layer (Modules 7, 8, 10, 11, 12, 13 and 18) against the kit at commit `ee81900` found nine
gaps, G1 to G9. This plan says what each gap changes in `deploy/`, which lessons it extends or adds, in what order the
work lands, and how each change is proved offline and on a lane. Kit paths are relative to `deploy/` unless they start
with `lessons/`, `tools/`, `plan/`, `pagekit/` or `.github/`. Every statement about the kit carries a file and line as
of `ee81900`; each pull request re-derives the page lines it touches with `pagekit/check_lesson.py`, because earlier
pull requests shift them. Every statement about a library is listed in section 5 as confirmed in the pinned source,
confirmed by a run, or unverified. Lane values are placeholders: `documind-ai-YOUR-ID`, `NUMBER`, `REGION`, "yours".
Each design was drafted, prototyped on a scratch copy of the kit and reviewed; where the review found a fault, this
plan uses the corrected design.

## 1. Why this plan

The agent layer runs, but several of its numbers and guarantees are not what the pages say. `_summary` counts tool
calls over the whole checkpointed thread and the judge reuses one session per brain, so LangChain and LangGraph
trajectory scores are wrong from the second question. The blocked list names tools that do not exist, tool timeouts
only log, the LangChain and LangGraph loops run to the framework's limit of about 10,000 steps, and the A2A peer is
uncapped. The three agent brains bind different tools, only the direct brain returns citations, and every turn resends
the whole thread. IAM lets the chat service invoke the peer, but no code does. Only rag-api is traced. The MCP server
checks identity inside each tool, with no spec-shaped door, and no lesson covers injection through retrieved documents
or poisoned tools. The chat brains bypass the model gateway, and the gateway as written cannot start.

Production practice, and Google and Kaggle's 5-day agents intensive built on ADK, teach what the kit leaves out:
multi-agent delegation from day 1, human-in-the-loop approval before a tool acts, context engineering for long
conversations, trajectory evaluation read beside a trace, and A2A with a managed deployment. Production practice adds
per-turn limits on calls, time and money, an MCP server that is an OAuth resource server with least-privilege tools,
and treating retrieved text and third-party tool metadata as untrusted input. The Hugging Face Agents Course and
Microsoft's AI Agents for Beginners cover the same ground, notably observability, evaluation and secure agents; their
lesson lists were not re-read for this plan, and no decision here rests on them. The kit already teaches trajectory
scoring (`evals/judge.py`) and an A2A peer (12.3); it teaches none of the rest.

## 2. The gaps at a glance

| Gap | What the kit does today | What it will do | Lessons | Effort | Depends on |
|---|---|---|---|---|---|
| G8 Correctness fixes | Tool calls counted over the thread (`services/chat/brains.py:63-64`); one judge session per brain (`evals/judge.py:126`); only the direct brain cites; three tool lists; `get_usage_stats` a stub (`services/chat/tools.py:143-156`); ADK shows the model `tenant_id` and `assertion` | Per-turn keys; a session per judge question and per smoke run; numbered citations from every brain; one tool list; one error contract; a three-parameter ADK declaration | Extends 10.1, 10.2, 10.3, 10.4, 7.2; rebuilds 11.2 | L (3 PRs) | None |
| G6 Limits | No loop cap on LangChain or LangGraph; `TIMEOUTS` only logs (`brains.py:84-91`); the ADK cap ends in a 500 (`brains.py:202`, `:217-224`); the peer uncapped (`commands/lesson-8.4.sh:21`) | One per-turn Meter (calls, rupees, deadline) in each brain's own seam; enforced tool budgets; a stop is HTTP 200 with `stopped_by`; the peer capped at 12 | Extends 10.3, 10.4, 12.3, 13.3; rebuilds 10.1, 10.2, 11.1, 11.2, 11.3, 13.2 | L (3 PRs) | G8 (hard) |
| G2 Approval | `BLOCKED` names undeclared tools (`tools.py:56`); nothing pauses; the roster has no roles | `withdraw_document` pauses for a second person in the tenant; an approvals record; a job that re-checks and withdraws; audit events | Extends 10.2, 10.3, 10.4, 8.3, 8.1; rebuilds 10.1, 4.3, 15.4 | L (5 PRs) | G8 (hard); G6 (seams) |
| G1 Handoff | No code calls the peer, though chat-sa may invoke it (`commands/lesson-8.4.sh:26-30`) | The ADK brain hands one question to the peer as a tool: roster-gated, bounded in time and count, logged, evaluated, priced | New 12.4 (decision 1); 12.3 footer | L (1 PR) | G8, G6 peer cap (hard); G3, G4 and G7 land later and keep its contracts |
| G3 Tracing | Only rag-api exports spans (`services/rag-api/main.py:26-29`) | One W3C trace from chat, peer and MCP through rag-api to Cloud Trace; log rows joined by a formatter | Extends 13.1, 12.3; rebuilds 10.2 | L (1 PR) | None hard; G8 soft; G6, G2, G1 seams |
| G4 MCP hardening | No door, Origin guard, policy, annotations or budget (`services/mcp/server.py:72-80`, `:270`) | 401 with RFC 9728 metadata before JSON-RPC; Origin and Host guard; default-deny policy; a per-caller tool-call budget; hints and output schemas; a tenant-pinned stdio bridge | Extends 12.1, 12.2; rebuilds 12.3, 16.1 | L (2 PRs) | None hard; G1 (shared budget) |
| G5 Injection | Retrieved text never screened; the Model Armor verdict parse raises (`services/rag-api/guard.py:15-19`); no tool pins | Verdict fix; one fence rule and one scrub; sticky per-thread taint; `mcp_refused`; hash-pinned peer tools; an attack set scored as enforced rows plus ASR | New 12.5 (decision 1); extends 8.3, 6.4, 10.2, 10.3, 12.2, 12.3, 13.2 | L (3 PRs) | G5-a none; G5-b and G5-c: G8 (hard), then G2, G1 and G4 |
| G7 Context | Every model call resends the whole thread (`brains.py:123-126`, `:102-103`, `:201`) | A window with a one-turn floor for LangChain and LangGraph; ADK event compaction; context fields on the chat row; `make smoke-context` | New 11.4 (decision 1); extends 11.1, 11.3; 6.1 prose | L (1 PR) | G8, G6 meter (hard) |
| G9 Gateway | Chat calls Gemini directly (`shared/profile.py:34-40`); the gateway's guardrail entry cannot load (`services/litellm/config.yaml:100-105`); a bare PAN is PUBLIC | PR A: the gateway starts and classifies. PR B: the chat through the gateway per tenant pin or setting, a tool-aware sensitive route, the cost on the chat row | Extends 18.1; re-runs 18.2, 18.4 | L (2 PRs) | PR A none; PR B G5, G1, G3, G6 |

## 3. Order of work

Five phases. Each gap's pull requests land in the order below; a later phase starts when the earlier one's kit
changes are merged.

| Phase | Pull requests, in order | Why here |
|---|---|---|
| 1. Fixes | 1.1 G5-a: the Model Armor verdict fix and 8.3. 1.2 G8-a: kit, tests, CI, 10.1-10.4 and the module_10 demos. 1.3 G8-b: 7.2. 1.4 G8-c: 11.2 and its demo. 1.5 G9-A: the gateway starts and classifies; 18.1's findings become fixes; 18.2 and 18.4 re-run | Nothing here depends on another gap. G8 sets the contracts G1, G2, G5, G6 and G7 build on: the per-turn `_summary`, the request context `tools.REQUEST`, one tool list, and `status: "error"` as the one refusal marker. G5-a makes `ARMOR=on` stop answering 500. G9-A repairs Module 18, whose live cells only ever ran against a stand-in. |
| 2. Limits and approval | 2.1 G6-a: kit, 10.3, 10.4 and the mechanical rebuilds. 2.2 G6-b: the peer cap and 12.3. 2.3 G6-c: 13.3. 2.4 G2-a: kit, Terraform, 10.2's scene and the mechanical rebuilds. 2.5 G2-b: 10.3. 2.6 G2-c: 10.4. 2.7 G2-d: 8.3 and 8.1. 2.8 G2-e: 4.3, 15.4 and the demos | G6 needs G8's per-turn keys and fresh smoke and judge sessions, or a per-turn rupee cap over a thread that never resets turns the Module 10 gate red. G6 lays the one tool wrapper and middleware list that G2 and G3 extend. G2 comes after G6 so its approval sits inside the limits. G6-b must land before G1 switches on. |
| 3. Multi-agent | 3.1 G1: kit, the 12.4 page and its manifest entry (decision 1), 12.3's footer, the module_12 demos | G1 rebases on G8's request getter and refusal rule and needs the peer capped (G6-b). It lands before G3, so the tracing instruments its per-call client once, before G5, so `documind_peer` is a taint source from the start, and before G9-B, so the peer's door is decided with the handoff in place. |
| 4. Tracing | 4.1 G3: kit, 13.1's new step, 12.3's third cell, the 10.2 rebuild | No hard dependency, but it wraps seams phases 2 and 3 create (the composed tool wrapper, the middleware list, `peer.py`'s client). Landing after them means one pass; landing before G4 means the MCP flush middleware is placed outermost once. |
| 5. MCP hardening, injection, context, gateway | 5.1 G4-A: door, guard, policy, hints and schemas; 12.1; rebuilds of 12.2, 12.3, 16.1. 5.2 G4-B: budget, bridge, gate; 12.2. 5.3 G5-b: kit with its rebuilds. 5.4 G5-c: the 12.5 page and its manifest entry (decision 1). 5.5 G7: kit, the 11.4 page and its manifest entry (decision 1), 11.1, 11.3, 6.1. 5.6 G9-B: the chat through the gateway; 18.1's new level | G5's pins hash the annotations and output schemas G4 adds, and its `RefusalLog` joins G4's middleware list. G7 needs G6's meter and must leave G2's paused turns and G5's taint flag intact. G9-B needs G5's fence for the flattened sensitive turn, G1's peer as the third door, and G3's and G6's row keys. |

Rules that hold across phases:

- **A kit pull request carries every rebuild whose quoted lines or build asserts it changes**, because
  `pagekit/check_lesson.py` fails otherwise; new scene content follows in one pull request per lesson. This is the one
  departure from `CLAUDE.md`'s one-lesson default (decision 16).
- **After every kit pull request**: `python pagekit/check_lesson.py N.M` and `python pagekit/audit_pages.py N.M` for
  each rebuilt lesson (R39 is the known exception); `python tools/kit_index.py`, then `--check`;
  `python tools/build_workshop_demos.py`, then `--check`, `python tools/check_workshop_demos.py` and
  `python deploy/workshop_demos/tests/run_tests.py`, with each changed lesson's digest reviewed in
  `tools/workshop_demo_reviewed.json` (`tools/group_workshop_demos.py:127-129` refuses an unreviewed change);
  `python tools/publish_learner.py --check`.
- **A new lesson lands in one pull request with its manifest entry, roadmap and plan rows, page and demo map**,
  because `tools/check_workshop_demos.py:54` and `:158` require a map for every manifest lesson. The same pull request
  moves every stated lesson count: `course-manifest.json` (`total_lessons`), `tools/build_workshop_demos.py:357`,
  `CLAUDE.md`, `README.md:4` and `:19`, `plan/README.md:5`, `tools/README.md:19`, `deploy/README.md:23`,
  `deploy/workshop_demos/README.md:3` and `deploy/workshop_demos/REVIEW.md:7` (the last three are published to
  learners), the course plan's count and hours (`plan/course-plan-v5-story-2026-09-22.md:84`: each new Core lesson adds
  one to 47 and 1.5 hours to 70.5), and the roadmap's title line (`plan/course-roadmap-v5-2026-09-22.md:1`) with its
  `.html` and `.pdf`.
- **One LangChain middleware order.** Trace (G3) first, HumanInTheLoop (G2) second, the context window (G7) last;
  the guard with G6's `timed_tool_call` last around the handler, G5's taint and G6's limits between, in landing order.
  The first entry is outermost for wrap hooks (`langchain/agents/factory.py:661`), and `after_model` runs from the
  last middleware that has one to the first (`factory.py:1787-1800`), so HITL's runs last. LangGraph's `ToolNode`
  takes one wrapper (`langgraph/prebuilt/tool_node.py:755`): one composed wrapper, trace outermost, then timeouts,
  then approval.
- **One FastMCP middleware list in `services/mcp/server.py`, declared in one place**: `_Flush` (G3), `RefusalLog`
  (G5), `CallBudget` (G4), `AuthMiddleware` (G4). The first listed runs first (confirmed by a run, section 5).
  `RefusalLog` gives G4's `rate_limited` error its own `kind` instead of logging it a second time.
- **One per-turn meter and one owner per row key.** G6's `Meter`, created in `agent.chat()` after `brain_for()`, owns
  `model_calls`, `tokens_in`, `tokens_out`, `cached_tokens`, `cost_usd`, `rag_cost_usd` and `stopped_by`. G7 extends
  the Meter with per-call records for `context_tokens` instead of adding a callback. G9's gateway ledger reports into
  it, and a gateway cost header wins over list price. Other keys: G2 `status`, `approval_id`; G1 `handoffs`; G5
  `scrubbed`; G7 `context_*`, `thread_*`, `compactions`, `summary_tokens_*`; G9 `gateway_*`. G3 adds none: its
  formatter adds the `logging.googleapis.com` keys. Fields are named in the row literal: the page guards read the row
  with the regex `\{"event": "chat",(.*?)\}\)\)`, and a spread hides fields from it.
- **One chat requirements set.** G1 adds `a2a-sdk[http-server]==1.1.2`; G2 `google-cloud-storage==3.13.1` and
  `langgraph==1.2.12`; G3 `opentelemetry-exporter-gcp-trace==1.15.0` and, by decision 10, the genai instrumentor;
  G9 `langchain-openai==1.6.2`, `openai==2.54.0`, `litellm==1.99.0`. Re-resolve after each. Line 29,
  `google-adk==2.8.0`, stays byte for byte (10.4, 11.1, 11.2 and 11.3 match it), and SQLAlchemy stays out
  (11.2 and 11.3 assert it) unless decision 4 takes durable ADK sessions.
- **One CI job with the chat pins**, created by G8 as an isolated venv step, runs every framework test:
  `test_chat_brains.py` (G8), `test_chat_limits.py` (G6), `tools/check_approvals.py` (G2), `test_handoff.py` (G1),
  `test_attacks.py`'s framework classes (G5), `test_chat_context.py` (G7) and `check_gateway_chat.py`'s framework tier
  (G9). The shared interpreter gains only `fastmcp==3.4.7` (G4) and `opentelemetry-api` and `-sdk` `1.42.1` (G3).
- **One `.mk` file per module**: `mk/agents.mk` (G6, G2), `mk/memory.mk` (G7), `mk/protocols.mk` (G1, G4, G5),
  `mk/operations.mk` (G3), `mk/serving.mk` (G9). The first pull request to create a file adds its `mk/README.md` row.
  A smoke that `smoke-all` runs stays in the `Makefile` core beside `smoke-all` (`smoke-handoff`); a module drill goes
  in its module's file, as `smoke-reindex` does in `mk/lifecycle.mk`.
- **Kit comments say "workshop lesson N.M".** The kit's comments use the earlier notebook numbering, and 11.4 and 12.4
  already name other lessons there (`smoke/smoke_slm.py:3`, `mk/ingestion.mk:20`; `commands/lesson-12.4.sh` deploys
  the UI).
- **Publishing.** A kit change reaches `netsetos/agents_workshop_learner` only with the author's explicit go-ahead, each
  time: `python tools/publish_learner.py --dest <learner checkout> --commit`, then push.

## 4. The gaps

### 4.1 G8 - Correctness fixes in the agent layer and its evals

**Current state**

- `_summary` builds `tool_calls` and `refusals` from every checkpointed message (`services/chat/brains.py:54-65`);
  LangChain and LangGraph pass the whole thread (`brains.py:105-108`, `:153-156`), while ADK reads only this run's
  events (`brains.py:226-243`). Three turns report 1, 2 and 3 calls.
- The judge sends `f"judge-{brain}"` for every question (`evals/judge.py:126`), so a brain that retrieves once per
  question scores exact 1/6. The smoke reuses `f"smoke-{brain}"` (`smoke/smoke_chat.py:98`).
- Only `DirectBrain` returns citations (`brains.py:256-272`). The UI's agent path renders `st.markdown(answer)`
  (`services/frontend/chat.py:147`), and `SYSTEM` never asks for a citation (`brains.py:46-51`).
- LangChain and LangGraph bind three tools (`tools.py:159`); ADK binds two shared functions (`brains.py:196-199`).
  `get_usage_stats` returns `value None` and cites a table that never existed (`tools.py:143-156`); chat-sa has no
  BigQuery role (`terraform/sa.tf:210-219`). The chat's cost tool is a copy that prices an unknown tier at standard
  (`tools.py:50-51`, `:121-140`); the shared one raises (`shared/documind_tools.py:316-332`).
- ADK's `retrieve` declaration shows `tenant_id*`, `assertion` and `brain` (2,572 characters).
  `guard_tool` overwrites `assertion` only when the request carried one (`brains.py:181-184`), so a model-written
  value reaches rag-api as the IAP header and the retrieval fails. With no `on_tool_error_callback`, an unknown name or
  tier ends the ADK turn with a 500; LangChain returns error results for the same calls.
- `brains.py:24` cites `tools/check_auth_wiring.py`, which does not exist; no kit test covers a brain.

**Target state.** Each turn reports its own trajectory and its own numbered citations in all three agent brains. Each
judge question and each smoke run opens its own conversation. One tool list is adapted per framework, and identity
never appears in a schema the model reads. One error contract holds everywhere: an unknown or blocked name, a refused,
wrongly typed or missing argument, or an unknown tier is an error result with `status: "error"` and counts as a
refusal; a payload error such as a retrieval timeout is data with `refusals []`; any other exception, such as the
token mint (`shared/documind_tools.py:138`), fails the turn.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 10.1 | Understand tool contracts and the direct agent loop | Reads the adapter split: the `@tool` wrapper that takes the tenant from `ToolRuntime`, and `search()`, where every brain's retrieve ends. Prints the model-facing contract: two tools, `get_usage_stats` gone, 'express' refused as the shared tool refuses it. Sends two questions to langchain on one session and sees each turn's own `tool_calls` and citations numbered from 1. | `shared/documind_tools.py`, `services/chat/tools.py` (`search`, `TOOLS`, `for_adk`), `brains.py` (`_summary`, `_turn`, `DirectBrain`), `tools/check_one_retrieval.py` | A direct-brain answer with `retrieve` in `tool_calls`; a langchain reply with citations `n` = 1..k |
| 10.2 | Implement the main LangGraph workflow | Runs three turns on one thread offline: `tool_calls` per turn 1, 1, 1 (the old code gave 1, 2, 3). Reads `_turn()`, where the question's id marks the turn's start, and the rule that a missing id is an error. Runs the new test. | `brains.py` (`LangGraphBrain.answer`, `_turn`, `_summary`), `commands/tests/test_chat_brains.py` | The refuse node fires on a blocked tool; the third turn's `tool_calls` hold only that turn's calls |
| 10.3 | Diagnose tool arguments, access failures and timeouts | The five failures through the LangChain brain, unchanged. Reads the two-entry `TIMEOUTS`, the unknown tier now an error result (`ToolException`), a timeout still not a refusal, the mint still raising. ADK parity is left to 10.4. | `tools.py` (`BLOCKED`, `TIMEOUTS`, the cost tool), `brains.py` (`GuardMiddleware`) | `refusals` non-empty for the blocked, bad-argument and unknown-name calls; `refusals []` on the timed-out retrieve |
| 10.4 | Compare the LangChain and ADK adapters | Prints both `retrieve` declarations (query, doc_type, top_k; 561 characters for `for_adk` beside the raw `FunctionTool` at 2,572). Makes the ADK model write `tenant_id` 'globex' and `assertion` 'anything' and sees rag-api receive acme and no header. Sends a blocked name, a bad argument, 'express' and a call with no arguments: equal refusals. Runs `make smoke-chat` and `make judge CHAT_URL=`. | `brains.py` (`AdkBrain`: `for_adk`, `REQUEST`, `tool_failed`, `mark_error`), `smoke/smoke_chat.py`, `services/frontend/chat.py`, `make smoke-chat`, `make judge CHAT_URL=` | Four brains on `/health`; `make smoke-chat` 6 passed with citations from every brain; four cost lines |
| 7.2 | Separate offline checks, live scoring and LLM judgment | After the lesson's judge cell writes `evals/reports/judge72.json`, runs the trajectory judge and reads nine per-question session ids. A new bullet under "How each instrument lied": one session per brain scored a correct brain 1/6. | `evals/judge.py`, `evals/tests/test_judge_sessions.py`, `make judge CHAT_URL=` | Three trajectory lines with exact, in-order, any-order, mean calls and `cited`; the self-test ends "every question gets a session of its own" |

**Kit changes**

| File | Change |
|---|---|
| `services/chat/brains.py` | `_summary(messages, turn=None, citations=None)` slices from the turn's message id (raises when it is missing) and adds `citations` sorted by `n`; line 64 stays byte for byte. `_turn()` sends `HumanMessage(id=str(uuid4()))`, the 36-character form `add_messages` assigns today, so 11.2's 215-byte question holds. `SYSTEM` keeps 46-50 and gains one sentence: search for every document question, a follow-up too, and cite `[n]` with this turn's numbers. ADK: `_adk_ctx` (160-163) gives way to `tools.REQUEST`; tools become `for_adk()`; `tool_failed` (on_tool_error_callback) handles `ValueError` and `TypeError` and returns None for anything else; `mark_error` (after_tool_callback) adds `status: "error"` to ADK's bare missing-argument dict; `_run` counts refusals from error responses. `guard_tool` keeps its `BLOCKED` branch, commented as unreachable until G2. Docstring 23-24 cites the new test. |
| `services/chat/tools.py` | Delete the rate copies (50-51) and `get_usage_stats` (143-156). `TIMEOUTS = {"retrieve": 30, "calculate_processing_cost": 10}`. Add `REQUEST` and a locked `_number()` (ToolNode runs parallel calls, `langgraph/prebuilt/tool_node.py:821-823`). `search()` holds 86-118 verbatim and numbers the citations. The cost tool delegates to the shared one and re-raises `ValueError` as `ToolException`. `TOOLS = [retrieve, calculate_processing_cost]`; `for_adk()` returns plain `retrieve(query, doc_type, top_k)` and the cost function. |
| `services/frontend/chat.py` | `import html`; `_as_source(c)`; the agent path renders `render_with_citations(html.escape(answer, quote=False), cited)`, because that function draws with `unsafe_allow_html=True` (`services/frontend/citations.py:83-84`); lines 148-149 stay (16.2). |
| `smoke/smoke_chat.py` | `session_id` becomes `f"smoke-{brain}-{RUN}"`, new each run. Citations required from every brain, agent `n` = 1..k, every `[n]` marker in range. Docstring edits at 9-10 only (8.2 quotes 11-13). |
| `evals/judge.py` | Session `judge-{run8}-{brain}-{row id}`; the self-test checks distinct ids; each row records `cited`; the trajectory line prints `cited k/n`. 7.2's and 7.3's excerpts are unchanged. |
| `commands/tests/test_chat_brains.py`, `evals/tests/test_judge_sessions.py` (new) | Thirteen brain tests: per-turn keys, numbered citations, one declaration, equal refusals including a missing argument, a mint failure raising in all three, turn 2's citations numbered from 1, `_as_source` and the escape. Judge tests: per-question sessions; a marker beyond the citations is not cited. |
| `.github/workflows/checks.yml`, `deploy/.github/workflows/documind-dryrun.yml` | One isolated venv step each: install `services/chat/requirements.txt`, run `test_chat_brains.py`. The shared interpreter is unchanged. |
| `UNOWNED.md:38`; `plan/course-plan-v5-story-2026-09-22.md` rows 150 and 173-176 | Cite the new test; the rows name `search`, `for_adk`, the tests, per-run sessions and four keys. |

**Make targets.** None new: `make smoke-chat`, `make judge CHAT_URL=`, `make build deploy-services`.

**Infra and IAM.** Nothing changes in IAM. Redeploy two images:
`make build deploy-services PROJECT=documind-ai-YOUR-ID REGION="$REGION" SERVICES="chat ui" SCRIPTS="commands/lesson-12.4.sh commands/lesson-12.8.sh" ADMIN_EMAILS="$ME"`.
`ADMIN_EMAILS` is required, or `commands/lesson-12.4.sh:24` resets the UI's admins to the `Makefile` default
(`Makefile:68`) and the learner loses the admin page 8.3 needs.

**Pages to rebuild**

- G8-a: 10.1 (`build.py:73` marker becomes `def _summary(messages`; :97-98; :126-132; :268 becomes
  `count("hidden: runtime") == 1`; the stub at :303-306; parts a:66, b:36, c:71-72). 10.2 (:72 becomes the `_turn`
  excerpt labelled "the same four keys"; :81; :90; c:48). 10.3 (:70 only; prose on the tier and the mint). 10.4
  (excerpts :65-70 and :77; expected output :87-90 and :305-313; stand-in :350; the comment at :445; :448 compares
  against the printed line, since the cell printed Rs 0.5933 and the build computed 0.5932; widget :488 and :503-509;
  prose a:31, b:11, b:33, b:39, c:26-28 and c:41). The module_10 demos.
- G8-b: 7.2 (`build.py:305-307`, :329-330; c:47 and :68-70).
- G8-c: 11.2 regenerated (the passages grow with `n`, so "bytes kept" and the widget's INC change) and
  `deploy/workshop_demos/module_11/lesson_11_2/demo_03_what_a_turn_writes.py`, which embeds 2,981 and 8,072.
- Checked unaffected on a scratch copy: 11.3 byte-identical, 11.1's TURN cell identical, `check_lesson` green on 6.3,
  6.4, 7.3, 8.1, 8.2, 13.2, 16.1, 16.2 and 17.3.

**Verification**

- Offline: (1) in a venv from the chat pins, `python -m unittest commands/tests/test_chat_brains.py -v` passes (on
  today's kit the nine designed tests give 3 failures and 6 errors); (2) `python -m unittest
  evals/tests/test_judge_sessions.py -v` and `python evals/judge.py --selftest`; (3) `python tools/check_one_retrieval.py
  deploy`; (4) the rebuilds and the common checks of section 3.
- On a lane: (1) redeploy as above; (2) `make smoke-chat PROJECT=documind-ai-YOUR-ID REGION="$REGION"` twice, 6 passed
  each time, every brain `tools=['retrieve']` with citations 1..k and new sessions on the second run; (3) 10.1's two
  questions give `['retrieve']`, then `['retrieve', 'calculate_processing_cost']`; (4) after 7.2's judge cell,
  `make judge PROJECT=documind-ai-YOUR-ID CHAT_URL=https://documind-chat-NUMBER.REGION.run.app JUDGE_ARGS="--reuse
  evals/reports/judge72.json --no-vertex --trajectory-rows 3"` prints `cited k/3`, and the chat rows show nine distinct
  session ids; (5) in the UI, a langchain answer draws pills, and a `<` in it shows as text.

**Cost.** There is no standing cost. Verification makes two smoke runs (eight turns) and one trajectory-only judge run
(nine turns); read their cost with `make usage HOURS=1`. Without `judge72.json` the judge first collects every golden
answer, which is billed. ADK's own input falls by about 475 tokens per call on the 10.4 stand-in, about Rs 0.06 per call
at flash (an estimate). Each judge run leaves 2 x rows threads in Cloud SQL and `rows` ADK sessions in instance memory.

**Risks**

- The model may omit markers or cite an earlier turn's number, and a within-range collision misattributes a source
  (decision 11).
- `_summary` raises when the turn's message is gone, so any trimming must keep it; `SummarizationMiddleware` would drop
  it (`langchain/agents/middleware/summarization.py:430-435`). G7 does not use it.
- `status: "error"` is the one refusal marker. G2's ADK confirmation returns a bare `{'error': ...}` that `mark_error`
  would count, so G2 gives it a distinct status.
- The gate gets stricter: a lane whose rag-api returns no citations for the gratuity question now fails
  `make smoke-chat`, which is the intent.
- The chat pins in CI (google-adk, `psycopg[binary]`) on Python 3.12 are untested; they are isolated in their own step.

### 4.2 G6 - Loop, time and cost limits per turn

**Current state**

- LangChain's `create_agent` gets no limit (`brains.py:102-108`) and binds `recursion_limit` 9,999
  (`langchain/agents/factory.py:1829-1831`); LangGraph compiles with none (`brains.py:143-151`), so langgraph's 10,007
  applies. A scripted looping model runs about 5,000 calls before `GraphRecursionError`.
- ADK caps at `ADK_MAX_LLM_CALLS` or 12 (`brains.py:202`), but `LlmCallsLimitExceededError` escapes `asyncio.run`
  (`brains.py:217-224`) and `services/chat/agent.py:198-203`: a 500.
- The peer builds `LlmAgent` with no `RunConfig` (`services/agent/agent.py:109-116`) and `commands/lesson-8.4.sh:21`
  sets no cap, so ADK's default of 500 applies.
- `TIMEOUTS` (`tools.py:57`) picks a log level after the call returns (`brains.py:84-91`); LangGraph's `ToolNode` has
  no wrapper (`brains.py:145`); ADK's guard ignores it. The real bound is `RAG_TIMEOUT_S`
  (`shared/documind_tools.py:42`, `:144-145`), 90 s on the lane (`commands/lesson-12.8.sh:32`). The chat model has no
  timeout and 6 retries (`shared/profile.py:38-40`).
- The chat row records no tokens or cost (`services/chat/agent.py:207-211`; asserted by 10.4 `build.py:99` and 13.2
  `build.py:151`), and `documind_tools.retrieve` drops rag-api's usage (`:154-163`).
- The walls: Cloud Run `--timeout=300` (`lesson-12.8.sh:28`) and the UI's 120 s (`services/frontend/chat.py:137-140`).
- 10.3 teaches "The budgets are logged, never enforced" (`lessons/10-agents/10.3-tool-failures/parts/c.html:41`).

**Target state.** Every turn has a model-call cap, a rupee cap and a deadline, checked before each model call. Each
tool call is cut at the smaller of its own budget and the time the turn has left. A tripped limit ends the turn with
HTTP 200, a fixed stop sentence and `limits.stopped_by`, and the next turn on the thread answers. Framework limits stay
as backstops. The peer runs with `ADK_MAX_LLM_CALLS=12`. Defaults: `CHAT_MAX_MODEL_CALLS` 12, `CHAT_TURN_BUDGET_INR` 5,
`CHAT_TURN_DEADLINE_S` 100, `CHAT_MODEL_TIMEOUT_S` 30, `CHAT_MODEL_ATTEMPTS` 2, `CHAT_MIN_MODEL_S` 5. The bound is the
deadline plus about 2 s of retry backoff plus the 1 s tool floor, about 103 s, under the UI's 120 s and Cloud Run's
300 s; a test checks the arithmetic.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 10.3 | Diagnose tool arguments, access failures and timeouts | As before, plus enforced timeouts: a slow tool is abandoned at the smaller of its budget and the turn's time left, and the model reads a payload error, not a refusal. The deadline and call cap stop a looping scripted model with a sentence; the next turn answers. The rupee cap is named here and taught in 13.3. | `services/chat/limits.py` (`Meter`, `timed_tool_call`, `TurnLimitsMiddleware`), `tools.py`, `brains.py`, `chat/agent.py`, `make limits-check`, `make limits`, `make limits-drill STOP=model_calls` | A timed-out tool in `limits.tool_timeouts` with `refusals []`; the drill returns HTTP 200 with `stopped_by` model_calls, and the next turn answers |
| 10.4 | Compare the LangChain and ADK adapters | The same three limits wired three ways: one `wrap_model_call` in `create_agent`; before-model, after-model and model-error callbacks beside `RunConfig.max_llm_calls`; the hand-built agent node. `ModelCallLimitMiddleware` named as the off-the-shelf cap that adds two nodes per call. The four cost lines read from the chat and rag-api rows. | `brains.py`, `limits.py`, `make smoke-chat`, `make judge CHAT_URL=` | Four brains on `/health` with one `limits` block; four cost lines from rows |
| 12.3 | Trace the implemented A2A peer and its permissions | As before, plus the peer's own cap (12; ADK's default is 500), read by the `RunConfig` `to_a2a` builds per request. Over the cap a task ends `failed`, shown offline on the build's local peer at a cap of 1. | `services/agent/agent.py`, `commands/lesson-8.4.sh`, `smoke/smoke_agent.py`, `make smoke-agent`, `make limits` | `/health` shows `max_llm_calls` 12; offline, a capped task ends failed |
| 13.3 | Exercise model routing, budgets and shutdown controls | As before, plus a per-turn clock beside the month's: `CHAT_TURN_BUDGET_INR`, the row's `cost_usd` and `stopped_by`. The page says what the month counter still does not see: the loop's own spend. | `limits.py`, `make limits-drill STOP=turn_budget`, `make candidate ROUTING=on`, `make off` | A chat turn stopped with `stopped_by` turn_budget and HTTP 200 |

**Kit changes**

| File | Change |
|---|---|
| `services/chat/limits.py` (new) | `Meter` (a dataclass with a lock): `allow_model_call()` counts a call when it allows it; `charge_model`, `charge_rag`; `model_timeout_s()` = min(30, left / attempts); `tool_budget_s(name)` = max(1, min(`TIMEOUTS[name]`, left)); `summary()`, `row()`. `TOOL_POOL` (16 threads). `timed_tool_call` submits under `copy_context()`, returns a success-status payload error on timeout, and always logs `'%s took %.2fs (budget %ss)'`, the line 10.3 teaches. `TurnLimitsMiddleware` uses `wrap_model_call` only, so checkpoints stay +3 per turn and +5 with a tool (11.2 `build.py:240` asserts them); on the gcp profile it sets the per-call timeout and attempts and turns a model timeout into the `turn_deadline` stop. ADK callbacks: before-model (sets `http_options.timeout` in milliseconds), after-model, model-error (timeouts only), after-tool. `timed_async` awaits `run_in_executor(TOOL_POOL, ...)`, never `asyncio.to_thread`, which `asyncio.run` would wait for. `repair_thread`; a recursion backstop of 4n + 10. |
| `shared/prices.py` (new) | Mirrors the whole `FALLBACK` of `services/rag-api/cost.py:10-20` (eight keys, gateway routes included), `USD_INR = 85`; the local profile prices at 0. |
| `services/chat/brains.py` | The guard's try/finally becomes `return limits.timed_tool_call(request, handler)`; LangChain adds `TurnLimitsMiddleware`, the backstop and a repair on `GraphRecursionError`; the LangGraph node checks, stops and catches timeouts, and `ToolNode(TOOLS, wrap_tool_call=...)`; ADK gets the callbacks, `RunConfig(max_llm_calls=limits.MAX_MODEL_CALLS)` and a caught `LlmCallsLimitExceededError`; `DirectBrain` charges its retrieve. `_summary` is G8's and is not touched. |
| `services/chat/tools.py`, `shared/documind_tools.py`, `services/mcp/server.py` | `TIMEOUTS["retrieve"]` = `RAG_TIMEOUT_S` + 5; the adapter charges rag-api's usage. `retrieve` returns `out["usage"]` from rag-api's five fields (`services/rag-api/schemas.py:32-45`). The MCP `retrieve` pops it before `return out` (`server.py:164`), so the MCP contract is unchanged. |
| `services/chat/agent.py` | The Meter after `brain_for()`, into the context; the response's `limits`; the row fields `model`, `model_calls`, `tokens_in`, `tokens_out`, `cached_tokens`, `cost_usd`, `rag_cost_usd`, `stopped_by`, `tool_timeouts`, `max_model_calls`, `budget_inr`; `/health` publishes the limits. |
| `shared/profile.py:38-40` | `timeout` and `max_retries` on the gcp branch only; whether `ChatOllama` accepts them is unverified. |
| `services/agent/agent.py`, `commands/lesson-8.4.sh:21` | `setdefault("ADK_MAX_LLM_CALLS", "12")` after line 50 and `max_llm_calls` on `/health`, with no new import or log call (12.3 `build.py:89`, :92); the deploy line appends `\|ADK_MAX_LLM_CALLS=12`. |
| `smoke/smoke_chat.py`, `smoke/smoke_agent.py` | Require `body.limits` (`stopped_by` null, calls within the cap, `cost_inr` > 0 for agent brains); a `DOCUMIND_EXPECT_STOP` mode for the drill. The peer's health must show 12. |
| `commands/tests/test_chat_limits.py` (new); `commands/tests/test_lane.py:25-26` | Stdlib half (Meter arithmetic, prices equal to `cost.py` read with `ast`, the time bound, the row keys) and a library half on the kit's brains that `DOCUMIND_REQUIRE_LIBS=1` turns from skips into failures. `limits` joins the pinned subcommand set. |
| `mk/agents.mk` (new), `commands/limits-check.sh`, `commands/limits-drill.sh`, `commands/lane.py limits`, `Makefile` `.PHONY`, `mk/README.md` | `limits`, `limits-check` (builds `~/graph-venv` from the chat pins, adding google-adk, which 10.3's venv lacks), `limits-drill` (updates the env, asserts the latest revision takes 100 percent of traffic, runs the smoke, restores from a trap). |
| `services/frontend/chat.py` | The agent caption (150-152) adds the stop reason and rupees; a comment at 140 ties the 120 s to the deadline. |

**Make targets.** `make limits`, `make limits-check`, `make limits-drill STOP=model_calls` or `STOP=turn_budget` (new,
`mk/agents.mk`); `make smoke-chat`, `make smoke-agent`, `make judge` (existing).

**Infra and IAM.** There is no Terraform change. The peer's env changes through `lesson-8.4.sh`, the chat gets a new
image, and the ui is redeployed for its caption. The log sink types the new fields on first arrival;
`terraform/sql/tenant_daily.sql:51` and `evals/usage_rows.py:31-32` still exclude event `chat`, so nothing is counted
twice.

**Pages to rebuild.** G6-a: 10.3 rewritten (`build.py:70-71`, `:80`, `:83`, `:204`; `c.html:41`); 10.4 (`build.py:67`,
`:70`, `:72`, `:77`, `:93`, `:99`, the stand-in at `:360`, the table at `:512`); 10.1 (`DirectBrain` n=17 at
`build.py:75`, `out = brain.answer(` at `:79`); 10.2 (`build.py:66`, `:68`, `:70`, `:72`; `:92`, whose
`br_src.count("TIMEOUTS") == 2` and "the graph reads no budget" stop holding once the guard calls `timed_tool_call` and
`ToolNode` takes the wrapper; and `:93`'s `"ToolNode(TOOLS)" in lg` loosened to `"ToolNode(TOOLS" in lg`); 11.1
(`build.py:63`); 11.2 (confirm `:240` still reads +3/+5); 11.3 (`build.py:66`); 13.2 (`build.py:151`, `CHAT_ROW` at
`:887`). Then rebuild whatever `check_lesson` names among 8.2, 6.3, 6.4, 8.1 and 16.2. G6-b: 12.3 (`/health`, the
env line, the offline capped-peer cell). G6-c: 13.3.

**Verification**

- Offline: `make limits-check` shows all three agent brains stopping a looping scripted model at the cap, the budget
  and the deadline with the next turn answering; a 3 s rag stub giving payload errors with `refusals []`;
  `AdkBrain.answer` returning within budget plus 0.3 s while the stub still sleeps; a hung model call giving the stop,
  not an exception; checkpoints +3/+5; a repaired thread after a forced recursion limit; no
  `LlmCallsLimitExceededError` escaping. CI parity: `python -m unittest discover -s deploy/commands/tests`,
  `check_one_retrieval.py`, `check_authz.py`, `check_local_lane.py`, `validate.py`.
- On a lane: (1) `make smoke-chat PROJECT=documind-ai-YOUR-ID` with `stopped_by` null and `cost_inr` > 0; (2)
  `make limits` shows 12 calls, Rs 5, 100 s and retrieve 95 s, and the peer's 12; (3) `make limits-drill
  STOP=model_calls` returns HTTP 200 with the stop sentence, chat rows show `stopped_by` and `model_calls` 1, and the
  restored smoke passes; (4) `STOP=turn_budget` the same; (5) `make smoke-agent` green; (6) `make usage HOURS=1`
  still totals rag-api's rows only.

**Cost.** There is no standing cost. Today a looping LangChain turn can make about 5,000 calls until Cloud Run's 300 s;
after the change a turn stops at Rs 5 plus at most one call's overshoot. Offline, one 200,000-token call spent Rs 25.53
against a Rs 2 cap: (200,000 x 1.50 + 50 x 7.50) / 1M x 85. For scale, twelve flash calls of 8,000 input tokens cost Rs
12.24, so the Rs 5 cap stops such a loop first. The drill is two runs of about eight turns; read the rupees from
`make usage`.

**Risks**

- A turn can overshoot by one call; the first call is always allowed.
- Abandoned tool threads run to `RAG_TIMEOUT_S`, and rag-api still bills them.
- A cold rag-api takes about 90 s, so turns that answer between about 95 and 120 s today stop with `turn_deadline`
  (decision 9).
- Two attempts instead of six mean less tolerance of 429 bursts on the global endpoint.
- The drill caps the real `documind-chat` for a minute or two; the trap restore and the traffic check must run.
- Three price tables now exist (`prices.py`, `cost.py`, and `PRICE_IN`/`PRICE_OUT` at `services/frontend/chat.py:32`);
  the test pins the first two only.
- The month counter and the 80 percent breaker still do not see the loop's spend (decision 9).

### 4.3 G2 - Human approval for a risky action

**Current state**

- `BLOCKED` names three undeclared tools (`tools.py:56`, against `TOOLS` at `:159`). Three guards check it
  (`brains.py:78-83`, `:128-141`, `:176-179` and `:237-240`), and LangGraph's refuse node refuses the whole turn, so an
  allowed retrieve beside it is told it needs approval (`brains.py:134-141`).
- Nothing pauses: `POST /v1/chat` always answers (`services/chat/agent.py:177-212`); the UI shows refusals as a caption
  (`services/frontend/chat.py:150-152`).
- A member document is `{email, added_at}`, written without merge (`shared/tenancy.py:77-82`); there are no roles.
- A reversible withdrawal exists only in the shell: `reconcile.py --retire ... --apply` (`services/ingest/reconcile.py:323-343`;
  `mk/lifecycle.mk:17-20`) and `--restore` (`:345-375`); `prefer_current()` drops withdrawn rows on every retrieval path
  (`services/rag-api/retriever.py:113-118`).
- `AUDIT_ACTIONS` has no approval events (`shared/audit_log.py:15-28`; `emit()` asserts registration at `:45`); the chat
  service has no `AUDIT_BUCKET` (`lesson-12.8.sh:32`) and no bucket grant (`terraform/storage.tf:96-105`).
- ADK sessions live in process memory: the image has no `[db]` extra, so `brains.py:212-215` logs a warning and uses
  `InMemorySessionService`, and the service runs two gunicorn workers (`services/chat/Dockerfile:17`) at min instances
  0 (`lesson-12.8.sh:29`). An ADK approval decided on the other worker would find no paused turn.

**Target state.** `withdraw_document(name, reason)` withdraws a document in the caller's tenant, and
`NEEDS_APPROVAL = {"withdraw_document"}` replaces `BLOCKED`. LangChain pauses with `HumanInTheLoopMiddleware` (first
in the list, with a `when` predicate that skips a call already answered); LangGraph's approve node calls `interrupt()`
before any side effect. A second person, an approver in the same tenant, decides; they see `asked` (the person's own
question, up to 500 characters), the model's reason labelled as the model's, and the turn's sources. The record moves
through pending, approved, rejected, cancelled, expired, lost, queued, executing, executed and failed, and expires. The
approve endpoint authorizes, checks the paused turn (none: status `lost`, no audit event, 409), decides in a
transaction, emits, then resumes with the recorded brain. A fixed-argument job re-checks the record and the four-eyes
rule, runs the same tombstone as `make retire`, and writes `doc.withdraw` only on success; `make restore` is the undo.
ADK offers the tool only when its sessions are durable (decision 4); until then its confirmation is proven offline.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 10.2 | Implement the main LangGraph workflow | Reads the graph: agent, tools, approve, with `interrupt()` before any side effect because a resumed node reruns from its first line. Offline: the pause and resume path, and a reject beside a retrieve that still runs. On the lane: asks for acme's `smoke_note.md` to be withdrawn, gets `pending_approval`, a second question gets 409, `documind-approver-sa` approves, the thread resumes from Postgres. | `brains.py` (`LangGraphBrain`: route, approve, resume, paused), `chat/agent.py` (`/v1/approvals`), `shared/approvals.py`, `make approver`, `make smoke-approval BRAINS=langgraph` | `status: pending_approval` with an id; GET shows `paused` true; then queued, executed, `tool_result.status` withdrawal_started; the smoke-lantern question unanswerable until `make restore` |
| 10.3 | Diagnose tool arguments, access failures and timeouts | Where each failure of a gated call surfaces: a reject (an error tool message and a refusal), a self-approval and a non-approver (403), another tenant's approver (404), a decided approval (409), an expired one (410), a lost turn (409, `lost`), the tool's last lock and a name outside the tenant (refused offline). The budget line as G6 leaves it. | `tools.py` (`NEEDS_APPROVAL`, the adapter), `shared/documind_actions.py`, `shared/approvals.decide`, `shared/tenancy.is_approver`, `make approvals` | `refusals ['withdraw_document']` after a reject; 403 for a self-approval; 404 across tenants |
| 10.4 | Compare the LangChain and ADK adapters | Offline, `HumanInTheLoopMiddleware`'s interrupt beside ADK's `FunctionTool(require_confirmation=True)`, both mapped to one record shape. On the lane the ADK brain does not offer the tool while its sessions are in memory, which points to 11.1. | `brains.py` (`LangChainBrain`, `AdkBrain`: the durable-session check, resume), `make smoke-chat` | `__interrupt__` and `adk_request_confirmation` side by side, each turned into the same record shape |
| 8.3 | Exercise DLP, guardrails and audit behavior | Follows the trail: the chat service writes `approval.request` and `approval.grant` or `approval.deny`; the job writes `doc.withdraw` only after the tombstone succeeds; `make retire` from the shell writes none (decision 5). | `shared/audit_log.py`, `services/ingest/reconcile.py` (`--approved`), `terraform/storage.tf` (`chat_audit`), `commands/lesson-12.8.sh` | `gcloud storage ls gs://documind-ai-YOUR-ID-audit/YYYY/MM/DD/acme/` lists the three events for the smoke's approval |
| 8.1 | Trace authenticated identity into tenant membership | Approving is a second list beside membership, written only by the operator and valid only for a member; `make roster` never touches it. | `shared/tenancy.py` (`is_approver`, `set_approver`), `commands/lane.py approver`, `make approver` | `make approver TENANT=acme EMAIL=you@example.com` prints the grant; after `make roster` it still holds |

**Kit changes**

| File | Change |
|---|---|
| `shared/approvals.py` (new) | Lazy Firestore client. `approval_id` (a sha256 of thread and call ids, 32 characters); `open_request` with `create()`, refusing past `APPROVAL_MAX_OPEN` (3) pending per requester; `held()` as two equality queries; `list_for()` ordered by `requested_at`; `decide()` in a transaction raising 403, 404, 409 or 410; `mark_lost`, `queue`, `note` (no answer text); `expired` (`APPROVAL_TTL_H`, 24); `start_job` with the empty-body Jobs API `:run` of `services/ingest/main.py:266-276`. Records carry `expire_at`. The local profile keeps them in a JSON file beside `DOCUMIND_THREADS_DB`. |
| `shared/documind_actions.py` (new) | `normalize_name` (a bare name, `tenant/name` or the upload URI; refuses `/`, `..` and over 200 characters); `withdraw_document` with the last lock (the record approved, tenant and name matching), then `queue` and `start_job`; returns the undo command. No audit event; kept apart from `documind_tools.py` so the MCP server's imports do not change. |
| `services/chat/tools.py`, `brains.py` | After G8: `NEEDS_APPROVAL`, a 30 s timeout and the `@tool` adapter (tenant from the runtime, the id from the thread and call ids); `TOOLS` is G8's list plus the tool, `retrieve` still first (10.4 quotes it). `SYSTEM` gets one sentence merged with G8's. LangChain: HITL first, `answer()` returns `pending`, new `resume()` and `paused()`. LangGraph: `route` sends to `approve`, which replaces the refuse node. ADK: `_adk_withdraw` under `require_confirmation=True`, added only when the session service is not in memory; a rejection counted under G8's rule with its own status. |
| `services/chat/agent.py` | A `Decision` model after `caller()` (11.3 slices from `ChatRequest` to `caller()`). `chat()` checks `held()` and `paused()`; the five `out = brain.answer(` lines stay (11.3). On `pending`: one call only and a current source, else reject in place; then `open_request` with `asked`, the turn id and the sources, and `approval.request`. The `/v1/approvals` endpoints: ids match `^[0-9a-f]{32}$`, point reads on the record's tenant, the order given above. `/health` unchanged (10.4). |
| `services/frontend/chat.py` | Only the agent branch (131-154) and the sidebar: a waiting card with the question, the model's reason, the document and the sources; an approvals inbox with a reason field. `_headers`, `stream_answer` and the cost lines unchanged (6.3, 6.4). |
| `shared/tenancy.py`, `shared/audit_log.py` | `is_approver`, `set_approver` (refuses a non-member), `list_approvers` and an `approver` CLI after the data-region section; `add_member`, `tenant_for`, `list_members` unchanged (3.1, 8.1). Four events on a new line after `"doc.mirror"` (16.2 asserts the media line). |
| `services/ingest/reconcile.py` | Extract the `--retire` body (336-342) into `withdraw_source()` unchanged; add `--approved`: queued to executing in a transaction, re-check the approver and four eyes, build the URI from the record only, withdraw, write executed with `doc.withdraw` or failed; `--selftest` covers `take()`. |
| `smoke/smoke_approval.py` (new) | Unique sessions per run. Per brain in `BRAINS` (default langchain, langgraph): pause, 409, 403 self-approval, reject with the source still indexed (read from rag-api's `/v1/sources`). Then approve, executed, the smoke-lantern question unanswerable, restore with `make restore`'s local dependencies, the outsider's 403. |
| `mk/agents.mk`, `commands/lane.py`, `commands/tests/test_lane.py`, `Makefile`, `mk/README.md` | `approver`, `approvals`, `withdraw-run`, `smoke-approval`; `lane.py approver` and `approvals` (roster_plan unchanged, 8.1 and 12.2 quote it), added to `test_lane.py`'s set; `.PHONY`; the operators loop (386) adds approver-sa; deploy-services (368) passes `WITHDRAW_JOB_NAME`. |
| `commands/lesson-12.8.sh` | Line 32 adds `AUDIT_BUCKET`, `REGION`, `WITHDRAW_JOB` and `APPROVAL_TTL_H`; the invoker loop (39) adds approver-sa. |
| `terraform/sa.tf`, `reconcile.tf`, `storage.tf`, `firestore_indexes.tf` | `documind-approver-sa` with no project roles, outside the outsider block 8.2 quotes; caller graph line 103 adds it. After `reconcile.tf:98`: job `documind-withdraw` (ingest image and account, `--approved --apply`, no retries) and `run.invoker` on it for chat-sa only. `objectCreator` on the audit bucket for chat-sa. A TTL on `approvals.expire_at` and a composite index for `list_for`. |
| `services/chat/requirements.txt`; `tools/check_approvals.py` (new); `tools/check_authz.py`; 8.3's `build.py` | Add `google-cloud-storage==3.13.1` and `langgraph==1.2.12`. The offline gate: HITL pause, approve, reject and the `when` predicate; the approve path; a resume from a second graph; ADK confirmation with a scripted model and the in-memory exclusion; the `decide()` codes; lost; the last lock; names; the open cap; `take()`. The approver fixture bound only on documind-chat. 8.3's emitters (91-93) and line 94 narrowed to the `--retire` branch. |

**Make targets.** `make approver`, `make approvals`, `make withdraw-run`, `make smoke-approval` (new, `mk/agents.mk`; not
in `smoke-all`, decision 2); `make reconcile-job`, `make deploy-services RECONCILE_JOB=true`, `make operators`,
`make restore`, `make sources` (existing).

**Infra and IAM.** Terraform adds `documind-approver-sa` (no project roles); job `documind-withdraw` under
`local.reconcile`; `run.invoker` on that job for chat-sa only; `storage.objectCreator` on the audit bucket for chat-sa;
a Firestore TTL and one index; `run.invoker` on documind-chat for approver-sa; `serviceAccountTokenCreator` on
approver-sa for `ADMIN_EMAILS` through `make operators`. Firestore gains `approvals` and
`tenants/{t}/approvers/{email}`.

**Pages to rebuild.** 10.1 (`build.py:119` and :468 tool count; :354 row keys; :107's count of `${REGION:-us-central1}`
from 14 to 15 and the sentence "all fourteen places" at `parts/b.html:8`; :383's deploy output), 10.2 (title :35,
excerpts :66-70, asserts :79-80 and :93, the scripted runs :125-147), 10.3 (:58, :60, :70, :83, :201-203), 10.4
(:66-70, :87, :184, :194, :308-310, :488, :530-531), 8.3 (:91-94, :98), 4.3 (the `--retire` block), 15.4
(`retire_previous`, 4 lines); 8.1 only with its scene. `check_lesson` confirms 3.1, 12.2, 11.1-11.3, 13.2, 6.3, 6.4,
4.4, 5.4, 12.3 and 16.2 keep their lines. Demos for modules 4, 8, 10 and 15. The course plan rows
(`plan/course-plan-v5-story-2026-09-22.md:174-175`) and roadmap rows (`plan/course-roadmap-v5-2026-09-22.md:119-120`)
for 10.2 and 10.3 change too, with their manifest proofs (decision 15).

**Verification**

- Offline, in the chat pins: `python tools/check_approvals.py`; `python services/ingest/reconcile.py --selftest`;
  `validate.py`; `check_authz.py`; `check_one_retrieval.py deploy/`; `terraform -chdir=deploy/terraform validate`.
- On a lane: (1) `make plan up RECONCILE_JOB=true`, `make deploy-services RECONCILE_JOB=true`, `make roster TENANT=acme
  MEMBERS=you@example.com`, `make operators`; (2) `make approver` for approver-sa and for you; (3) `make smoke-reindex`
  leaves `acme/smoke_note.md`; (4) `make smoke-approval` PASS for pause, hold, self-approval and reject on both
  brains, then approve, executed, unanswerable, `ingest_reactivated`, the outsider's 403; (5) `make sources
  TENANT_ONLY=acme` shows withdrawn, then indexed; (6) the audit listing above; (7) with `HOLD=1`, the request in your
  UI inbox; (8) brain adk declines and the chat log shows the session warning; (9) `make smoke-chat` green.

**Cost.** Each decision resumes the turn: one extra model call. An assumed 3,000 tokens in and 150 out at flash is
about Rs 0.48; the resumed call resends the thread, so a long conversation costs more. One short job run per
withdrawal; the restore is a reactivation with nothing embedded; a handful of Firestore operations per approval.
`make smoke-approval` over two brains is about ten chat turns, one job and one reactivation; read the figure from
`make usage`.

**Risks**

- A paused thread that gets a new message loses its interrupt (reproduced offline); the hold, the `lost` release and
  the expiry are load-bearing.
- LangChain and LangGraph share one checkpointer and thread id, so the recorded brain resumes, never the radio's
  current choice.
- ADK's `ToolConfirmation` is experimental in 2.8.0, and ADK has no approval path on the lane until decision 4.
- chat-sa's project-wide `datastore.user` (`terraform/sa.tf:212`) can write the roster, the approvers and the records;
  the job's re-check catches bugs, not a compromised chat service.
- The withdrawal is asynchronous: the answer says "started", and the record's status is the truth.
- The approver's assertion goes out on the resumed turn's retrieves, so usage rows name the approver.
- Whether the model calls the tool with the right name is not fully predictable; normalization and a smoke question
  that names the file keep the smoke reliable.

### 4.4 G1 - Multi-agent handoff from the ADK brain to the A2A peer

**Current state**

- The peer is an `LlmAgent` over `McpToolset` (`services/agent/agent.py:95-116`), served by `to_a2a` (`:137-140`). It
  reaches the lane as documind-agent-sa, never as its caller (`:19-24`); that account is on acme's roster only
  (`commands/lane.py:147`), while ui, mcp and chat are on all three golden tenants (`lane.py:145-146`). It logs only at
  start-up (`:141`; 12.3 `build.py:92` asserts it).
- IAM already allows the hop: `run.invoker` on documind-agent for ui-sa and chat-sa (`commands/lesson-8.4.sh:26-30`;
  `terraform/sa.tf:105`), and `sa.tf:110-113` calls chat-sa's binding "8.4's". `tools/check_authz.py:156` asserts no
  `AGENT_URL` in the chat source. Only `smoke/smoke_agent.py` and 12.3's cells call the peer.
- The chat image cannot import the A2A client: `services/chat/requirements.txt:29` is `google-adk==2.8.0` without
  `[a2a]`.
- The chat row says nothing about a remote agent (`services/chat/agent.py:207-211`); the MCP row carries event, tool,
  tenant, caller and via, and no task id (`services/mcp/server.py:121-124`); `list_documents` and `corpus_stats` read
  Firestore only (`server.py:167-224`).
- `validate.py` does not know the import `a2a` (`THIRD_PARTY`, `validate.py:58-67`), and its pin regex skips a
  hyphenated extra (`:298`).
- Timeouts: the UI posts with 120 s (`services/frontend/chat.py:137-140`), chat's Cloud Run timeout is 300 s
  (`lesson-12.8.sh:28`), and the peer's MCP call 120 s (`agent.py:104`).

**Target state.** The ADK brain keeps the turn and calls the peer as a tool, `documind_peer` (agent-as-tool, not a
transfer), and only the request string crosses; a captured `SendMessage` body carried no email, tenant or assertion. A2A
carries no end-user identity, so the delegator authorizes: on the gcp profile `tenancy.tenants_of(PEER_ACCOUNT, 2)`
must equal `[tenant]`, the confused-deputy guard. A token is minted per request as documind-chat-sa for `PEER_URL`.
The hop is bounded by `asyncio.wait_for` at `PEER_TIMEOUT_S` 75 (under the UI's 120 s) and by
`HANDOFF_MAX_PER_TURN` 2, counted before the call so parallel calls count. Refusals, failures and timeouts come back as
`{error, refused or failed: True, status: "error"}`, which G8's rule counts. The chat row logs `handoffs` [{peer,
tenant, task, state, ms}], and the hop is joined to the MCP row by tenant and a time window of `latency_ms` plus 60 s
until G3's trace crosses. `HANDOFF` is off by default. The LangChain, LangGraph and direct brains do not change.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 12.4 (new, decision 1) | Hand a turn from the ADK brain to the A2A peer | Level 0: agent-as-tool against transfer, by what crosses the hop; a diagram of the gate, the token, the deadline and the cap. Level 1: the ADK brain in the UI, an inventory question, the caption "tools: documind_peer". Level 2: `peer.py` verbatim (the roster gate, the per-request token, the deadline, the cap, failures as data) and three lines in `brains.py`. Level 3: `POST /v1/chat` as ui-sa, the `handoffs` field, `make smoke-handoff`. Level 4: the chat row joined to the MCP row by tenant and time; the API row (brain mcp, user documind-mcp-sa) for an explicit "ask the partner agent" retrieve; the hop priced by running the kit's peer locally; `make judge-handoff`. | `services/chat/peer.py`, `brains.py` (`AdkBrain`), `shared/tenancy.py` (`tenants_of`), `chat/agent.py`, `commands/lesson-8.4.sh`, `commands/lesson-12.8.sh`, `make handoff`, `make smoke-handoff`, `make judge-handoff` | `documind_peer` in `tool_calls` with a `TASK_STATE_COMPLETED` task id in `handoffs`; the MCP row as documind-agent-sa for acme in the window; refusals shown offline for zeta, a peer on two rosters and a turn over the cap; `make smoke-handoff` green |
| 12.3 | Trace the implemented A2A peer and its permissions | Unchanged, plus one sentence in "What changed on your lane": chat-sa's invoker binding is the one 12.4 uses. | As today | As today; the footer names 12.4 |

**Kit changes**

| File | Change |
|---|---|
| `services/chat/peer.py` (new, about 140 lines) | `NAME = "documind_peer"`; env `PEER_URL`, `PEER_ACCOUNT`, `PEER_AUTH` (id-token or none), `PEER_TIMEOUT_S` 75, `HANDOFF_MAX_PER_TURN` 2. An explicit `DESCRIPTION` (inventory only; content goes to `retrieve`), required because `AgentTool` declares `agent.description`, empty for a URL card. `HANDOFFS` ContextVar. The gate runs through `asyncio.to_thread` and fails closed. `IdToken(httpx.Auth)` overrides `async_auth_flow` and mints in a thread. An after-request interceptor reads `task.id` and `TaskState.Name(task.status.state)`. `PeerTool(BaseTool)` builds its declaration once; `run_async` reserves the record, checks the cap, then the gate, then builds a per-call `RemoteAgent` through `a2a_client_factory=ClientFactory(config=ClientConfig(httpx_client=..., streaming=False, supported_protocol_bindings=[JSONRPC, HTTP_JSON]))` and awaits `AgentTool(remote).run_async(args={"request": ...})` under `wait_for`; any exception becomes data. `build()` returns None and imports no `a2a` module when `PEER_URL` is unset. |
| `services/chat/brains.py` | Rebased on G8: three lines after the root `LlmAgent` block, outside 10.4's 4-line excerpt (`from peer import build`, build with the request getter, append when set). `_run` sets a new `HANDOFFS` list per turn and returns `handoffs`, merged with G6's and G7's `_run` edits. The added lines avoid 'thinking', 'session.state', '.state[' and 'on_tool_error_callback' (10.4 and 11.1 assert on them). |
| `services/chat/agent.py`, `services/chat/requirements.txt` | The row gains `"handoffs": out.get("handoffs", [])`. Add `a2a-sdk[http-server]==1.1.2` (the peer image's pin); line 29 unchanged. The resolution was checked: protobuf 6.33.6, langgraph 1.2.12, no SQLAlchemy. |
| `shared/tenancy.py` | `tenants_of(email, limit=2)`: `tenant_for`'s query (55-68) with a limit, sorted ids. It goes after `list_members` (85-87) under its own comment, "the peer's question: every roster one account is on", outside 5.1's and 8.1's spans; the docstring (14-18) names this third reader and why. |
| `validate.py` | `"a2a"` in `THIRD_PARTY` with a comment; the pin regex's extras class at 298 widened to `[\w,\-]+`, so `a2a-sdk[http-server]` is compared between the chat and agent images. |
| `Makefile` | `HANDOFF ?= off` beside `ARMOR` and `SEMANTIC_CACHE` (`Makefile:98-101`; the comment there still carries the notebook course's lesson number). Line 353 stays byte for byte (11.1 `build.py:93`) and the quoted line below follows it. `smoke-handoff` goes beside `smoke-agent` and into `.PHONY`; the `smoke-all` loop (`Makefile:818`) runs it with `DOCUMIND_HANDOFF_OPTIONAL=1`. |
| `mk/protocols.mk` (new), `mk/README.md` | `handoff` (a target-specific `HANDOFF = on`, then one `$(MAKE) deploy-services ... SCRIPTS=commands/lesson-12.8.sh` line; `HANDOFF=off` on the command line wins) and `judge-handoff`. |
| `smoke/smoke_handoff.py` (new) | (0) With no `PEER_URL` or `PEER_ACCOUNT` on documind-chat: FAIL and exit 1, or with `DOCUMIND_HANDOFF_OPTIONAL=1` the line "PEER_URL is not set on documind-chat - handoff is off (make handoff)". (1) An explicit partner-agent question as ui-sa: 200, `documind_peer`, a completed task. (2) The MCP row as agent-sa for acme in the window, polled up to 60 s. (3) The chat row with the same task id. |
| `evals/handoff_eval.py`, `evals/handoff.jsonl`, `evals/tests/test_handoff_eval.py` (new) | Uses `judge.trajectory_metrics` (135-145), a session per row and run (at most 64 characters, `chat/agent.py:146`); four rows, two that should go to the peer and two that should not; explains, never gates; an offline self-test that CI runs. |
| `commands/tests/test_handoff.py` (new), the chat-pins CI job | A to_a2a stand-in behind a recording front door, scripted models on both sides: acme completes across two loops; an own-corpus question keeps `retrieve`; zeta, a two-roster peer and a third handoff refused; two threads concurrently; peer down gives failed; a slow peer gives timeout; a gate error refuses; every request carries a token; no body or header holds the email, tenant or assertion. |
| `terraform/sa.tf`, `commands/lesson-8.4.sh`, `tools/check_authz.py` | Comments only at `sa.tf:108-113` and `lesson-8.4.sh:23-25`. `check_authz.py:156` asserts `os.environ.get("PEER_URL"` in the chat source and still no `MCP_URL`; the chat-to-agent edge joins 161-163; new asserts for `tenants_of(`, a `{"request":`-only call and a `wait_for(` deadline. |

The one `Makefile` line, after line 353:

```make
	if [ "$(HANDOFF)" = on ]; then CHAT_EXTRA_ENV="|PEER_URL=https://documind-agent-$$PROJECT_NUMBER.$(REGION).run.app|PEER_ACCOUNT=documind-agent-sa@$(PROJECT).iam.gserviceaccount.com"; fi; \
```

Unquoted, the shell reads each `|` as a pipe and `CHAT_EXTRA_ENV` stays empty; this form was simulated in GNU make.

**Make targets.** `make handoff` and `make handoff HANDOFF=off`, `make judge-handoff` (new, `mk/protocols.mk`);
`make smoke-handoff` (new, `Makefile` core); `make smoke-all` (now runs it).

**Infra and IAM.** No new resource or grant: chat-sa's invoker on documind-agent exists (`lesson-8.4.sh:26-30`), and
chat-sa reads the roster (`terraform/sa.tf:210-219`). With `HANDOFF=on`, documind-chat gets `PEER_URL` and
`PEER_ACCOUNT` through `CHAT_EXTRA_ENV` and `lesson-12.8.sh:32`; `--set-env-vars` replaces the whole set, so off removes
them. The peer's cap from G6-b is a hard prerequisite.

**Pages to rebuild.** 12.4 (new; its `build.py` follows 12.3's pattern with the peer's pins and a venv from the chat
pins). 12.3's footer and lane box change. 10.4 is untouched (G8 already covers errors as refusals), 11.1 holds (line
353 kept), and 8.1 is untouched. `check_lesson` over all lessons should name only these two. The same pull request adds
the manifest entry, the plan row (chapter 12's end state at `plan/course-plan-v5-story-2026-09-22.md:56` gains "and
hand it one question as a tool"), the roadmap row and the counts that section 3 lists (decision 1).

**Verification**

- Offline: `python deploy/validate.py` (imports pass with `a2a` known; the pins compare `a2a-sdk`);
  `check_authz.py`; `check_one_retrieval.py deploy/`; `test_handoff.py` in the chat pins; `python -m unittest discover
  -s deploy/evals/tests`; the 12.4 build and the common checks.
- On a lane, with the peer capped: (1) `make handoff PROJECT=documind-ai-YOUR-ID`, and `gcloud run services describe
  documind-chat` lists both variables; (2) the UI caption; (3) `make smoke-handoff`; (4) "Ask the partner agent: after
  how many years is gratuity payable?" leaves an API row with brain mcp and user documind-mcp-sa; (5)
  `make judge-handoff`; (6) optional live refusal with `gcloud run services update documind-chat --region=REGION
  --update-env-vars=PEER_ACCOUNT=documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`, then `make handoff`
  restores it; (7) the Level-4 price cell; (8) `make smoke-chat` three times and `make smoke-agent`, then
  `make handoff HANDOFF=off`, after which `make smoke-handoff` fails and `make smoke-all` prints the not-set line.

**Cost.** There is no idle cost: documind-agent and documind-mcp scale to zero (`lesson-8.4.sh:18`, `lesson-7.2.sh:18`).
Each `make handoff`, on or off, runs one Cloud Build and one checkpoint-migration job (`lesson-12.8.sh:7-8`, `:46-52`).
Each handoff costs the root's two flash calls, at least two flash calls in the peer, one roster query, requests to
documind-agent and documind-mcp, and a `brain=mcp` API row when a retrieve runs. Rupees per handoff = 85 x (T_in x 1.50
+ T_out x 7.50) / 1e6, where T_out counts candidate plus thought tokens as the kit does
(`services/rag-api/generator.py:214-219`); the figure is the learner's own, measured in Level 4.

**Risks**

- `RemoteA2aAgent` is experimental in google-adk 2.8.0; the pins hold, and `test_handoff.py` fails first on an upgrade.
- Routing is not deterministic: the root may hand off a document question, which can make `make smoke-chat` flaky
  (`smoke/smoke_chat.py:95-111` requires `retrieve`). Live verification runs it three times, and `judge-handoff`
  reports mis-routing before shipping.
- The roster gate is load-bearing and trusts `PEER_ACCOUNT` as operator configuration.
- Attribution moves: the person appears only on the chat row, the MCP row names agent-sa and the API row mcp-sa.
- The peer keeps working after the 75 s deadline, bounded by its own cap and its Cloud Run timeout.
- `make up` or `make deploy-services` without `HANDOFF=on` turns the handoff off, like the other switches.
- The peer's tokens are not in G6's per-turn meter; the row's `handoffs` says a hop happened.

### 4.5 G3 - One trace per answer

**Current state**

- rag-api builds a `TracerProvider` with a batch processor on Cloud Trace (`services/rag-api/main.py:26-29`), opens
  stage spans (`:36-47`, which 5.3 quotes) and instruments FastAPI (`:51`); its rows (`:411`, `:507`) carry no trace
  id. `tools/check_retrieval.py:611-626` lifts `query()`, `stream()` and `usage_row()` into a fixed namespace in CI, so
  those functions cannot gain a new name.
- The chat service has no OpenTelemetry pin, although google-adk 2.8.0 installs api and sdk 1.42.1; `chat()` is sync
  (`services/chat/agent.py:177-178`); the ADK brain's session id is the thread id `tenant:email:session`
  (`brains.py:218`).
- `documind_tools.retrieve` sends no `traceparent` (`shared/documind_tools.py:138-144`). Lane chunk ids are
  `tenant:sha256#i` (`services/ingest/contracts.py:80-97`).
- FastMCP opens a span per `tools/call`, and ADK and a2a-sdk open theirs, but with no SDK installed they go nowhere;
  the MCP `ToolError` texts carry the caller's email (`services/mcp/server.py:113`, `:117`).
- `validate.py`'s pin check (`:289-319`) passes today with rag-api at opentelemetry 1.44.0 (`services/rag-api/requirements.txt:17-22`).
- IAM and the API are in place: `roles/cloudtrace.agent` for the api, ingest, chat, mcp and agent accounts
  (`terraform/sa.tf:148`, `:164`, `:216`, `:226`, `:242`); the API enabled (`commands/lesson-12.1.sh:37`).
- 13.1 asserts no trace target exists (`build.py:100`); 12.3 concludes nothing records who asked the peer
  (`parts/b.html:73`).

**Target state.** One W3C trace across chat, peer, MCP and rag-api, with no prompts, answers, tool arguments or
credentials in spans. `shared/tracing.py` (lazy imports, a no-op unless `K_SERVICE` is set or `TRACING=on`) builds an
explicit provider with a parent-based sampler and a `_Scrub` exporter that drops exception messages and status text. It
forces `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` in code, because the ADK brain's tool arguments carry the IAP
assertion (`brains.py:181-184`), and it turns a2a-sdk telemetry off. A logging formatter adds `logging.googleapis.com`
trace keys to any JSON row written while a span is current, so no row site changes. A pure-ASGI flush middleware runs
before the last byte, bounded by `anyio.move_on_after(TRACE_FLUSH_S)` (2 s), because the SDK's `force_flush` ignores its
timeout. On Cloud Run the front door decides sampling (at most 0.1 unforced requests per second per instance, 10
forced); `TRACE_SAMPLE` (0.1) governs only true roots.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 13.1 | Debug a wrong answer through the complete pipeline | A definitions row, "trace, span, traceparent", set against the lesson's "trail" (eleven rows). A new Level 4 step while revision 2 is current: `make trace-ask PROJECT=documind-ai-YOUR-ID TARGET=chat BRAIN=langchain Q='What is the notice period for a confirmed E3?'`, then `make trace TRACE_ID=...`, reading chat.turn, execute_tool retrieve, documind.retrieve with its versions, and rag-api's POST and stages. Level 5: why the flush is bounded, who decides sampling, the cost, and what the kit does not do yet. A ninth Verify row. | `shared/tracing.py`, `shared/documind_tools.py`, `services/chat/agent.py`, `brains.py`, `services/rag-api/main.py`, `commands/trace.py`, `make trace-ask`, `make trace` | documind-chat and documind-api in one trace; `documind.versions` equals the first 12 characters of the revision-2 SHA in `make sources`; `gcloud logging read 'trace="projects/documind-ai-YOUR-ID/traces/TRACE_ID" AND logName:"run.googleapis.com%2Fstdout"'` includes the chat row and the query row; no word of the question in the tree |
| 12.3 | Trace the implemented A2A peer and its permissions | A third Level 4 cell: `make trace-ask TARGET=agent`, then `make trace`: documind-agent, documind-mcp and documind-api in one trace, with the `mcp_call` line under it. The conclusion at `parts/b.html:73` and the Level 5 entry are rewritten. | `services/agent/agent.py`, `services/mcp/server.py`, `commands/trace.py` | Three service names under the sent trace id; documind-ui-sa in no span and no row |

**Kit changes**

| File | Change |
|---|---|
| `shared/tracing.py` (new, about 230 lines) | `setup(service, genai=False)`, `adopt()` for rag-api's provider, the `server(name)` decorator for a sync endpoint, `label`, `traced`, `inject`, `log_fields`, `wrap_tool_call`, `flush`, `FlushMiddleware` (off with `TRACE_FLUSH=off`), `_Scrub`, `_TraceJson`. |
| `shared/documind_tools.py` | `from shared import tracing`; `_versions()` keeps the text between the first `:` and `#` only when it is 64 hex characters (the lane form; the corpus form yields none); `@tracing.traced("documind.retrieve", kind="client")` over tenant, brain, top_k, doc_type, answerable, citation count and versions; `tracing.inject(headers)` after 140. 10.1's and 10.3's excerpts are unchanged, and ADK's declaration stays identical. |
| `services/chat/agent.py`, `brains.py` | `tracing.setup("documind-chat", genai=True)` and the flush middleware after 134; `@tracing.server("chat.turn")` between 177 and 178; labels after 191 and 204. Lines 198-203 and the row stay byte for byte. `brains.py`: a `TraceMiddleware` first in the list, and `tracing.wrap_tool_call` outermost in G6's composed ToolNode wrapper. |
| `services/agent/agent.py` | Inline tracing (no kit import): env defaults before line 38, `_tracing()`, a pure-ASGI `_TraceIn` that attaches the extracted context and flushes; the status folded into `agent_up`, so the file keeps one `log.` call and no `request.headers` (12.3 `build.py:89`, :92). |
| `services/mcp/server.py` | `tracing.setup("documind-mcp")` and `_Flush`, first in the one middleware list. `_audit` unchanged. |
| `services/rag-api/main.py` | `from shared import tracing` after 16; `OTEL_SERVICE_NAME` and the resource regex before 26; `tracing.adopt()` after 29; the flush middleware after 66. No edit inside `query()`, `stream()` or `usage_row()`. |
| requirements (chat, agent, mcp); `validate.py` | Chat and agent add only `opentelemetry-exporter-gcp-trace==1.15.0`; mcp adds api and sdk 1.44.0 and the exporter, matching rag-api. Decision 10: the chat's `opentelemetry-instrumentation-google-genai==0.7b1` and `opentelemetry-util-genai==0.3b0`, the last versions under google-adk's cap, with a named allowance in `check_pin_consistency` that applies only when every lower-pinned service also pins google-adk. |
| `commands/trace.py` (new), `mk/operations.mk` (new), `Makefile`, `mk/README.md` | `ask` mints for the deterministic run.app URL as ui-sa, sends a forced `traceparent` and a random session, prints `TRACE_ID` and `SESSION`; `show` polls Cloud Trace, prints a tree (orphans as roots, unnamed spans as Cloud Run's front door) and the joined rows; `show --session` finds a rewritten id. Targets pass `--project $(PROJECT) --region $(REGION)` and `trace` errors without `TRACE_ID`. |
| `commands/tests/test_trace.py` (new), `.github/workflows/checks.yml` | The no-op path, `_versions`, the tree renderer, the traceparent format; with the SDK, propagation, the formatter, the scrub and a flush that returns in about 2 s against an exporter that sleeps 5 s. CI installs `opentelemetry-api==1.42.1` and `-sdk==1.42.1`. |

**Make targets.** `make trace-ask`, `make trace` (new, `mk/operations.mk`).

**Infra and IAM.** Writers need nothing new. Readers need `cloudtrace.traces.get` and log read; a lane owner has both,
and a non-owner needs `roles/cloudtrace.user` and `roles/logging.viewer` (decision 10). G3 adds no deploy-script change;
the switches are set with `gcloud run services update --update-env-vars`. Rebuild the chat, mcp, agent and api images.

**Pages to rebuild.** 10.2 (rebuild; its graph excerpt holds the ToolNode line and gains one sentence). 13.1 (parts a
and c, `build.py:100` rewritten to assert the two targets, `MAP_PY`'s event lines regenerated, the lane box, course plan
row 198). 12.3 (the third cell, `b.html:73`, the Level 5 entry, `PERMS_PY`'s import list, the lane box, course plan row
192). A quote scan found 6.4, 12.1, 12.2, 10.3, 10.4, 5.3 and 6.3 unaffected.

**Verification**

- Offline: `python -m unittest discover -s deploy/commands/tests` with the SDK installed; `validate.py` pins pass;
  `check_retrieval.py` unchanged proves no lifted function moved; `check_authz.py`; `check_one_retrieval.py`; the 12.3
  and 13.1 builds byte-identical apart from the intended changes.
- On a lane after `make build deploy-services`: (1) chat and mcp log `tracing_on`, the peer's `agent_up` shows it;
  (2) the chat trace as in the scene, recording whether the sent id was kept; (3) `BRAIN=adk` shows ADK's spans with
  empty `llm_request` and `tool_call_args`; (4) `TARGET=agent` joins three services; (5) one request with no
  `traceparent` and one with flag 00, recording `trace_sampled` and whether spans exist; (6) `make smoke-chat` p50 with
  the flush on and off, the lane's number on 13.1; (7) the outsider's refused MCP call shows `exception.type` ToolError
  and no email.

**Cost.** Cloud Trace is cited at $0.20 per million spans after 2.5 million free per billing account per month (not
re-fetched; the page reads it before stating it); Cloud Run's own spans are free. A lab session of about 200 turns is at
most about 3,400 spans, Rs 0. At 100,000 turns a day with two chat instances, Cloud Run's sampling cap gives at most
about 7.8 million spans a month, about Rs 90 (an upper bound). If every request were forced (Cloud Run caps forced
sampling at 10 per second per instance), about 45 million spans would cost about Rs 723. Log rows gain
about 150 bytes each. The flush adds at most `TRACE_FLUSH_S` per response, only when spans are queued.

**Risks**

- Cloud Run may rewrite the incoming trace id or its flag (not documented); `show --session` and live step 5 cover it.
- rag-api's POST span ends after the flush and can land one request late.
- The ADK brain's spans carry the thread id (`google/adk/telemetry/tracing.py:624-626`), which holds the email; the
  page states it.
- Two genai instrumentor versions run (0.7b1 in chat, 1.1b1 in rag-api).
- Any IAM-admitted caller can force sampling, capped by Cloud Run at 10 per second per instance.
- "Trail" and "trace" must stay distinct words on 13.1.

### 4.6 G4 - MCP auth and hardening to the MCP spec

**Current state**

- No auth provider, middleware or Origin guard: `FastMCP(...)` at `services/mcp/server.py:72-80`, and
  `mcp.http_app(path="/mcp", stateless_http=True)` at `:270` with fastmcp 3.4.7's `host_origin_protection` off by
  default. On 127.0.0.1 a foreign Origin and a foreign Host both got 200 (tested). The local profile trusts
  `LOCAL_USER` with no token (`:86-87`).
- `initialize` and `tools/list` run for anyone Cloud Run admits. Identity is checked inside each tool through
  `_caller()` (`:84-98`, assertion first, then bearer, `shared/iap.py:170-186`); a failure is a `ToolError`, not 401,
  and 12.1 asserts no 401 or `WWW-Authenticate` in the file (`lessons/12-protocols/12.1-mcp-tools/build.py:90`).
- The tenant comes from identity and the roster (`_tenant_for`, `:101-118`). There is no policy table, no annotations
  and no declared output schema on the four decorators (`:141`, `:167`, `:204`, `:227`), and no rate limit beyond
  `--concurrency=40` and `--max-instances=10` (`commands/lesson-7.2.sh:17-18`).
- No token passthrough: `retrieve` calls `documind_tools.retrieve` without an assertion (`:158-159`).
- The plan's 12.2 row promises a desktop client (`plan/course-plan-v5-story-2026-09-22.md:191`), but the kit has no
  credential helper; its 12.1 row names `make chat-local`, which starts the chat service, not MCP (`Makefile:568-571`).
- `make smoke-mcp` has four pass or fail checks and no skip category (`smoke/smoke_mcp.py:37-45`, `:83-128`).

**Target state.** Phases 1 and 2 of the design, with the pinned libraries and no new infrastructure. A
`GoogleIdTokenVerifier` wrapped in `RemoteAuthProvider` answers a missing or email-less token with 401 and
`WWW-Authenticate` naming the RFC 9728 metadata before any JSON-RPC, verifying in a thread and caching until `exp`.
`_caller()` keeps today's assertion leg (fail closed without `IAP_AUDIENCE`) and otherwise reads the verified token.
`host_origin_protection="auto"` answers a foreign Origin with 403 and a foreign Host with 421 on loopback and does
nothing on Cloud Run. A default-deny `TOOL_POLICY` runs through `AuthMiddleware` with an async check whose roster lookup
runs off the event loop. `CallBudget` counts tool calls per verified email per instance (`MCP_RATE_PER_MIN`, 60) and
refuses with a readable `ToolError` naming `retry_after`; it also logs policy denials. Tools declare hints and output
schemas; `retrieve` is open-world because it returns uploaded text. `commands/mcp_bridge.py` is a stdio proxy for
desktop clients that mints a fresh token and pins one tenant against the model. Phase 3 (people as themselves over
OAuth) is decision 6.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 12.1 | Expose, discover and invoke MCP tools | What a client discovers before calling: hints (which a client must not trust from an unknown server) and output schemas it validates `structured_content` against. The door answers before any JSON-RPC: 401 plus the metadata address. A foreign Origin or Host refused on localhost. The policy table decides what `tools/list` shows each caller. The Rs 0 lane with no token behind the Origin guard. | `services/mcp/server.py` (`GoogleIdTokenVerifier`, `RemoteAuthProvider`, `_caller`, `host_origin_protection`), `tool_policy.py`, `tool_schemas.py`, `make mcp-local` | `tools/list` names four tools with hints and schemas; the outsider lists one; an email-less token gets 401 with `resource_metadata`; a foreign Origin gets 403; `retrieve` answers a local client |
| 12.2 | Deploy MCP and verify authorized access | The metadata read behind Cloud Run with an invoker token; the outsider sees one tool and is refused `retrieve` by the roster; the budget refuses with `retry_after`; a desktop client through the bridge, and the `mcp_call` line naming documind-ui-sa; the gate names any door that answered before the app. | `commands/lesson-7.2.sh`, `services/mcp/rate_limit.py`, `commands/mcp_bridge.py`, `commands/lane.py mcp-connect`, `smoke/smoke_mcp.py`, `make smoke-mcp`, `make mcp-connect`, `make mcp-bridge-check` | `make smoke-mcp` 0 failed, any skip naming its door; the bridge refuses a second tenant; the gratuity answer in a desktop client |
| 12.3 | Trace the implemented A2A peer and its permissions | Unchanged, plus one observation: the peer forwards the tools' output schemas to Gemini. | `services/agent/agent.py`, `make smoke-agent` | `make smoke-agent` green after the door change |

**Kit changes**

| File | Change |
|---|---|
| `services/mcp/server.py` | The verifier (via `anyio.to_thread`; `exp` decoded only after `iap.identity` succeeds, 0 not cached; logs `mcp_unauthenticated` with its reason); `auth=RemoteAuthProvider(authorization_servers=["https://accounts.google.com"], base_url=SELF_URL, resource_name="DocuMind MCP")` only on gcp with `SELF_URL` set; `CallBudget` and `AuthMiddleware` in the one list; `READ_ONLY` hints (retrieve open-world) and `output_schema` on the four decorators, bodies unchanged (`tools/check_authz.py:327-396` still lifts `list_documents`); `_caller()` as above; `/health` adds `rate_per_min`; `http_app(..., host_origin_protection="auto")`. `iap.identity(` stays in this file (8.1 `build.py:108-111`). |
| `services/mcp/tool_policy.py`, `rate_limit.py`, `tool_schemas.py` (new) | `TOOL_POLICY` (retrieve, list_documents, corpus_stats: member; calculate_processing_cost: verified) and `async def allowed(ctx)`, memoised per request only. `CallBudget`: a fixed 60 s window, 0 disables, logs `mcp_rate_limited` and `mcp_denied`, pruned past 4,096 keys. Schemas with always-present fields only, pointing at `shared/documind_schemas.py:35-56`. |
| `commands/mcp_bridge.py` (new), `commands/lane.py mcp-connect` | The bridge mints with `gcloud auth print-identity-token --include-email --impersonate-service-account=... --audiences=...`, caches 45 minutes, re-mints once on 401, proxies with `create_proxy`, and pins `DOCUMIND_TENANT` (acme) through a middleware. `mcp-connect` prints each client's block with absolute paths and one line on ui-sa's reach; it writes no files. |
| `mk/protocols.mk`, `Makefile`, `mk/README.md` | `mcp-local` (the local corpus, then uvicorn on 127.0.0.1:8121), `mcp-connect`, `mcp-bridge-check`; `.PHONY`. The `smoke-mcp` recipe stays byte for byte (12.2 `build.py:94`): the smoke reads the budget from `/health`. |
| `commands/lesson-7.2.sh` | Line 21 appends `\|MCP_RATE_PER_MIN=${MCP_RATE_PER_MIN-60}`; a comment on who sees the 401 and the per-instance budget; the smoke block reads the metadata. The invoker loop (28-32) unchanged. |
| `smoke/smoke_mcp.py`, `smoke/smoke_media.py:96`, `commands/tests/test_smoke_mcp_setup.py` | Read `structured_content`. A skipped list; checks 5 (401 with `resource_metadata`, else a skip naming Cloud Run), 6 (the metadata's resource), 7 (hints and schemas), 8 (the outsider lists one tool), 9 (optional burst), 10 (the bridge answers and refuses zeta). |
| `commands/tests/test_mcp_door.py`, `test_mcp_bridge.py` (new); both CI install lines | The door, guard, policy, budget, assertion leg, local profile and schemas tied to `documind_schemas` offline; every registered tool has a policy row and explicit hints. The bridge pin. `fastmcp==3.4.7` in `.github/workflows/checks.yml:34` and `deploy/.github/workflows/documind-dryrun.yml:31` (decision 7). |
| `plan/` rows 190-191, roadmap rows 135-136, manifest proofs of 12.1 and 12.2 | The new proofs; 12.1's targets name `make mcp-local`. Content only; the count is unchanged. |

**Make targets.** `make mcp-local`, `make mcp-connect CLIENT=claude-desktop TENANT=acme` (also cursor, gemini-cli,
claude-code), `make mcp-bridge-check` (new, `mk/protocols.mk`); `make smoke-mcp` extended; `make smoke-agent` and
`make smoke-media` must stay green.

**Infra and IAM.** There is no Terraform change, and documind-mcp gains one env var. The bridge uses the token-creator
grant on ui-sa that `make operators` already gives (`Makefile:384-392`). A dedicated desktop account or phase 3 would
change this (decision 6).

**Pages to rebuild.** G4-A: 12.1 in part rewritten (its TOOLS regex at `build.py:81` and the slice at :88 break on the
new decorators; :90 inverts; three `/health` keys become four; the INVOKE cell's `.data[...]`; the box at
`c.html:25-27`); 12.2 rebuilt (its slice at `build.py:86`; its FrontDoor panel's outcomes); 12.3 and 16.1 rebuilt. G4-B:
12.2 rewritten (budget, bridge, gate output). Demos for 12.1, 12.2, 12.3 and 16.1;
`tools/workshop_demo_runtime_adaptations.py:56-69` starts the 12.1 server and must still pass the door.

**Verification**

- Offline: `python -m unittest discover -s deploy/commands/tests`; `check_authz.py`, `check_one_retrieval.py`,
  `check_local_lane.py`; `python -m compileall -q deploy`; `make mcp-local`, then a client lists four tools with no
  token and `curl -H 'Origin: http://evil.example'` gets 403.
- On a lane: (1) `make build deploy-services PROJECT=documind-ai-YOUR-ID REGION=REGION SERVICES=mcp
  SCRIPTS=commands/lesson-7.2.sh`; (2) `make smoke-mcp` 0 failed; (3) `make smoke-agent` green, which settles whether
  Gemini accepts the forwarded schemas; (4) `make smoke-media`; (5) `make mcp-connect CLIENT=claude-desktop
  TENANT=acme`, a cited gratuity answer, zeta refused by the bridge; (6) the `mcp_call`, `mcp_unauthenticated`,
  `mcp_denied` and `mcp_rate_limited` lines; (7) the API row still names documind-mcp-sa.

**Cost.** There is no infrastructure or monthly cost. The burst check is about 65 requests of
`calculate_processing_cost`, which never reach rag-api or Gemini: well under a rupee. The bridge check adds one
retrieve, under a rupee. Each member `tools/list` or `tools/call` adds one Firestore collection-group read.

**Risks**

- Cloud Run's IAM may answer before the app (unverified), so an anonymous standard client never sees the metadata; check
  5 names the door, and the page must not imply OAuth discovery works on the IAM-gated lane.
- Tokens are minted for `SELF_URL` while the metadata advertises `SELF_URL/mcp`; a strict RFC 8707 client could see a
  mismatch (decision 6).
- Output schemas change client code: `r.data` becomes a generated type, and a too-strict schema turns into failed calls,
  the peer's included. If Gemini rejects the forwarded schema, drop `output_schema` on the server.
- The budget is per instance (up to ten times the limit at ten instances), and agent-sa's budget is shared by every A2A
  user and by G1's handoffs.
- The tenant pin stops the model, not the operator: the server still trusts ui-sa on three rosters.
- `@mcp.tool(timeout=)` does not bound the kit's sync tools (3.0 s measured against 1.0), so no page may call it a
  timeout.

### 4.7 G5 - Indirect prompt injection and MCP tool poisoning

**Current state**

- Model Armor screens only the question and the buffered answer (`services/rag-api/guard.py:22-47`;
  `services/rag-api/main.py:348-366`), and its verdict parse reads a field google-cloud-modelarmor 0.7.1 does not have
  (`guard.py:15-19`), so `ARMOR=on` answers 500; 8.3 tested a stub.
- No spotlighting: `brains.SYSTEM` has no rule on untrusted text (`brains.py:46-51`), the chat's `retrieve` passes
  quotes unmarked (`tools.py:106-118`), the direct brain's local path joins raw quotes (`brains.py:265`).
- A poisoned upload can claim authority: only a leading HTML comment is stripped (`services/ingest/main.py:188`;
  `shared/documind_corpus.py:120`), dates come from the text (`contracts.py:124-137`), and `DATED_RULE` follows the
  latest date (`services/rag-api/generator.py:177-178`).
- The MCP server has no annotations, and a roster refusal raises before `_audit` (`server.py:156-163`), leaving only
  FastMCP's generic log line.
- The peer takes every listed tool, description and output schema verbatim (`services/agent/agent.py:97-108`), and its
  instruction says nothing about untrusted text (`:54-62`).
- The UI renders the answer with `unsafe_allow_html=True` (`services/frontend/citations.py:83-84`) and previews,
  history, agent answers and the stream with `st.markdown` (`citations.py:90`; `services/frontend/chat.py:119`, `:147`,
  `:179`); `/v1/query` returns and caches the answer verbatim (`main.py:401-404`), and documind-mcp relays it
  (`server.py:158-164`).
- Checkpointed brains resend the thread, so an instruction retrieved in turn 1 is still in turn 2's input, and a
  per-turn check misses it (reproduced).

**Target state.** Retrieved passages, peer replies and third-party tool metadata are untrusted. Enforced controls sit in
the runtime: identity and tenant from the verified caller; only declared tools run; once untrusted content enters a
thread, `TAINT_GATED` tools need a person for the rest of the thread (the flag lives in checkpointed state, or ADK
session state); tool metadata is pinned by a hash over name, title, description, input and output schema and hints;
output is scrubbed at every server boundary and at render. Probabilistic controls (the fence, the Model Armor context
screen) are measured as attack success rate (ASR), before and after, and never gate.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 12.5 (new, decision 1) | Defend agents against injected documents and poisoned tools | Loads a vendor note for acme whose hidden comment asks for tool calls and a beacon, whose section overrides the travel cap with a declared date, and which asks for Globex's contract; sees 8.3's prompt guard pass the innocent question. `make attack-offline` shows each attack reaching the quote the model reads. `make attack-eval` against the API, the brains, the deployed peer and the in-process worst case, defences off then on; sorts each outcome into enforced and requested-only. The context screen on the g5-armor tag. The peer locally against the local-profile MCP server and evil-mcp, pins off and on, then `RUG=1`. The deployed server's `mcp_refused` line. `make attack-clean`. | `evals/adversarial/`, `evals/run_attacks.py`, `shared/spotlight.py`, `chat/tools.py` (`TAINT_SOURCES`, `TAINT_GATED`), `brains.py` (`TaintMiddleware`, ADK callbacks), `rag-api/guard.py`, `main.py`, `mcp/server.py` (`RefusalLog`), `agent/pins.py`, `agent/tool_pins.json`, `make attack-offline`, `attack-load`, `attack-tags`, `attack-eval`, `attack-clean`, `pin-tools`, `evil-mcp` | `make attack-eval`: 0 enforced failures on every surface and an ASR table; an `mcp_refused` line naming the tenant and agent-sa; a `tool_unpinned` line for `convert_currency`; `context_dropped` counts as measured; `make sources` shows the note withdrawn and `make eval-live` gives the same per-row verdicts as before |
| 8.3 | Exercise DLP, guardrails and audit behavior | Code only (G5-a): the quoted `_blocked` lines change, plus one sentence that the verdict is `filter_match_state`. The proof becomes reachable. | `rag-api/guard.py` | A 400 `prompt_blocked` on a live `ARMOR=on` candidate |
| 6.4 | Complete the Streamlit upload-to-answer journey | `render_with_citations` sanitises before drawing pills (line 83 only); the JavaScript mirror adds the image and link strip (it already escapes). | `frontend/citations.py` | A markdown image in an answer is not drawn |
| 10.2, 10.3, 10.4, 12.2, 12.3, 13.2 | (manifest titles unchanged) | One sentence each: 10.2's `route()` reads the thread's taint; 10.3 names `TaintMiddleware`, a separate middleware so the quoted `wrap_tool_call` is unchanged; 10.4 names the ADK taint callbacks; 12.2 a refused call now writes `mcp_refused`; 12.3 `tool_filter=_pinned` and the peer's second log line; 13.2's row gains `scrubbed`. | As listed | Unchanged proofs |

**Kit changes**

| File | Change |
|---|---|
| `services/rag-api/guard.py` (G5-a) | `_blocked()` reads `sanitization_result.filter_match_state`. After `check_response`, so 8.3's excerpt changes only inside `_blocked`: `_injected()` reads `filter_results.get("pi_and_jailbreak")` and only that filter decides (so the invoice's PAN never drops a chunk), and `check_context(texts)`. |
| `services/rag-api/main.py`, `config.py` | `screen_context()` outside the 6.3 and 8.3 excerpts, a no-op unless `ARMOR=on` and `ARMOR_CONTEXT=on`, logging chunk ids only; called first inside the generate stage of `/v1/query` (outside 5.3's excerpt) and after rerank in `/v1/stream`. A new line after `ans.stages = dict(stages)` (401) scrubs the answer and quotes before `screen_response` and the semantic cache; 9.1's asserted lines unchanged. `armor_context` beside `armor` (`config.py:125`). |
| `shared/spotlight.py` (new) | Stdlib: `RULE`; `fence(text, source)` escapes `<document` inside the text and wraps it; `scrub(text, allow_hosts)` strips markdown images, raw HTML tags and links or URLs to off-list hosts. |
| `services/chat/tools.py`, `brains.py`, `agent.py` | After G8 and G2: `TAINT_SOURCES = {"retrieve", "documind_peer"}`, `TAINT_GATED` = `BLOCKED` plus G2's approval set; the fence in `search()` on the model-facing copy after `_number()`, so the ledger keeps clean quotes. `SYSTEM` gains `RULE`. `TaintMiddleware` (state `tainted`; set after a source; a gated call becomes an approval request naming the provenance); LangGraph's state and `route()`; ADK `after_tool_callback` sets `tool_context.state["documind_tainted"]` and the guard reads it; the direct local path fences. The chat row adds `scrubbed`. |
| `services/mcp/server.py` | `RefusalLog.on_call_tool` logs `{event: mcp_refused, tool, named_tenant, kind, reason}` on a `ToolError`, never the query, then re-raises; second in the one list. |
| `services/agent/pins.py`, `tool_pins.json` (new), `agent.py`; `commands/pin_tools.py` (new) | The canonical hash; `_pinned` as `McpToolset(tool_filter=...)`, logging `tool_unpinned`; `TOOL_PINS_FILE`; `TOOL_PINS=off` honoured only with `MCP_AUTH=none`; `on_tool_error_callback` refuses only "Tool not found"; one instruction sentence; no `shared/` import. `pin_tools.py` lists `server.py` in process on the local profile and writes or `--check`s the pins, never from a deployed server. Re-run after G4's hints and schemas. |
| `services/frontend/citations.py`, `chat.py`; `validate.py` | `import html as _html`; a module-level `_safe()` (a copy of the scrub patterns); line 83 becomes `html = _CITE.sub(_pill, _safe(answer))`; previews through `_safe()`; `safe_markdown()` for chat lines 119, 147 and 179. `validate.py` holds the copy equal to `shared/spotlight.py`. |
| `evals/adversarial/` (new), `evals/run_attacks.py` (new), `evals/tests/test_attacks.py` (new) | A synthetic fixture with `.invalid` hosts and "Effective from: 2026-07-01"; `attacks.jsonl` with structural enforced rows (no image, tag or off-list URL after scrub; no undeclared call; no gated call without approval; no Globex marker; pins drop unknown and changed tools) and behavioural ASR rows, `atk-05` the control; `evil_mcp.py` clean by default, poisoned with `RUG=1`, plus one never-reviewed tool. The runner's offline mode is CI-safe; live modes `--api-url`, `--chat-url`, `--agent-url`, `--peer-local` (in-process local-profile MCP, so nobody impersonates agent-sa) and `--inproc` (defences toggled in process). |
| `mk/protocols.mk`, `commands/attack-load.sh`, `attack-tags.sh`, `attack-eval.sh`, `attack-clean.sh` (new), `Makefile`, `deploy/.github/workflows/documind-dryrun.yml` | One-line targets. The tag is `gcloud run services update documind-api --no-traffic --tag g5-armor --update-env-vars ARMOR=on,ARMOR_CONTEXT=on,SEMANTIC_CACHE=off`, with no chat tag (the kit re-routes only documind-api after a deploy, `Makefile:374-377`) and not named `candidate`. `attack-eval` ends with a check that no `tool_unpinned` line exists on documind-agent. `attack-clean` retires the fixture and removes only `g5-armor`. `dryrun` runs `attack-offline`, and `pin-tools CHECK=1` when fastmcp imports. |

**Make targets.** `make attack-offline`, `attack-load`, `attack-tags`, `attack-eval`, `attack-clean`, `pin-tools`,
`evil-mcp` (new, `mk/protocols.mk`); `retire`, `restore`, `sources`, `eval-live`, `smoke-chat`, `smoke-mcp`,
`smoke-agent`, `usage` (existing).

**Infra and IAM.** There is no Terraform change: documind-api-sa already holds `roles/modelarmor.user`
(`terraform/sa.tf:144`, `:156`). The eval adds one no-traffic tag on documind-api, removed by `make attack-clean`; the
next `make deploy-services` resets env (`commands/lesson-12.2.sh:52`) and traffic. Rebuild the api, chat, mcp, agent and
frontend images. One fixture object stays behind, its ledger row withdrawn.

**Pages to rebuild.** G5-a: 8.3 (the `_blocked` excerpt). G5-b: 6.4 (line 83 and the mirror); 10.2 (the route excerpt,
`build.py:79`); 10.3 (confirm the `wrap_tool_call` excerpt, one sentence); 10.4 (one sentence); 12.2 (one sentence); 12.3
(the `build_agent` excerpt length at `build.py:71`, the asserts at :79 and :92, the statement); 13.2 (`CHAT_ROW` gains
`scrubbed`). Confirm by rebuild 5.3, 6.3, 8.1, 9.1, 10.1, 11.1-11.3, 12.1, 16.1, 16.2 and 17.1. G5-c: 12.5, with
12.4's footer now naming 12.5 and 12.5's naming 13.1; the same pull request adds the manifest entry, the plan and
roadmap rows and the counts that section 3 lists (decision 1).

**Verification**

- Offline: `python evals/run_attacks.py`; `python -m unittest discover -s evals/tests`, in CI and in the chat pins
  (sticky taint across turns in all three brains, pins over output schemas, the rug pull, the 0.7.1 verdict parse, the
  scrub); `make pin-tools CHECK=1`; `check_one_retrieval.py`; `make dryrun`; `validate.py`.
- On a lane: (1) `make attack-load PROJECT=documind-ai-YOUR-ID`, an `ingest_ok` line and `effective_from` 2026-07-01;
  (2) `make attack-tags`; (3) `make attack-eval`: 0 enforced failures, the ASR table, no `tool_unpinned` on
  documind-agent, `context_dropped` recorded as measured, `atk-05` still 90; (4) `make smoke-agent`, then
  `gcloud logging read` for `jsonPayload.event="mcp_refused"` on documind-mcp naming zeta and agent-sa; (5) the local
  peer with `make evil-mcp`; (6) `make smoke-chat` and `make smoke-mcp` green; (7) `make attack-clean`; (8)
  `make eval-live` gives the same verdicts as before.

**Cost.** There are no always-on resources. The spend is Gemini calls for `attack-eval` (rows x surfaces; `--inproc`
runs every row twice), Model Armor on the tag (one screen per reranked chunk per request, at a price this plan has not
verified) and one embedding per fixture section. The page reads rupees from `make usage` and does not estimate them.

**Risks**

- Behavioural rows flap; only structural rows fail the run.
- Model Armor may flag nothing, or flag statute text; `atk-05` catches false positives.
- On the lane the agent brains read only rag-api's quotes, so live ASR there can be zero by architecture; `--inproc`
  is the worst case, and the page says so.
- `DATED_RULE` with text-declared dates lets any upload claim authority; G5 demonstrates it and does not fix it
  (decision 12).
- Pins go stale when docstrings or schemas change; `pin-tools --check` in dryrun and the log check catch it.
- The public kit ships a poisoned MCP server and an injection fixture; both use `.invalid` hosts, must pass
  `tools/leakscan.py`, and are never deployed.

### 4.8 G7 - Bound what each turn sends the model, keep the full record

**Current state**

- LangGraph prepends the system prompt to `state["messages"]` with no filter (`brains.py:123-126`); LangChain's
  `create_agent` has only the tool guard (`brains.py:102-103`); ADK's `App` has no compaction (`brains.py:201`), and its
  sessions are in memory per gunicorn worker (`brains.py:204-215`; `services/chat/Dockerfile:17`).
- The budget exists only as a comment: `TokenBudget.history=2_000`, "rolling summary (documind-chat, 8.5)"
  (`services/rag-api/context_budget.py:20`); 6.1 says the chat keeps a rolling summary (`parts/a.html:30`, `c.html:104`).
- The pages say the model is sent everything (11.1 `parts/a.html:31`; 11.3 `parts/b.html:41`). 11.3's restart check is a
  fresh two-turn session (`smoke/smoke.py:252`, `:267-268`), so a window with a one-turn floor cannot break it.

**Target state.** The record and the prompt are separate. `window(messages)` keeps this turn whole, always keeps the
previous whole turn (the floor), replaces earlier non-error tool results in a copy with the status `{"cleared": true,
"reason": "evidence from an earlier turn"}`, and trims older turns, whole turns only, to `CHAT_HISTORY_TOKENS` (2,000).
It writes no state, so G2's paused turns and G5's taint flag are untouched, and the checkpoint keeps every message.
`SYSTEM` says earlier evidence is cleared and to search again. ADK turns on `EventsCompactionConfig` (threshold 9,500,
the last `ADK_KEEP_EVENTS` raw events with call and response pairs kept together) with a flash-lite summarizer built by
the same factory as the root model, so it follows G9's gateway. `CHAT_CONTEXT=full` restores today's behaviour. The row
gains the context fields on top of G6's meter.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 11.4 (new, decision 1) | Bound the model's context while keeping the full conversation | The passbook and the statement: the checkpoint keeps every entry, and each call is handed a statement. Offline (Rs 0): twenty scripted turns on the kit's LangChain and LangGraph brains, full then window: the first call's input climbs every turn under full and levels off under window, while the checkpoint keeps turn 2's tool result; one oversized turn shows the floor; the ADK brain's compaction. Live: `make smoke-context`, `make context-report`, the UI caption, the tamarind probe reported, the smoke's thread decoded from Cloud SQL. | `services/chat/context_window.py`, `brains.py`, `chat/agent.py`, `frontend/chat.py`, `smoke/smoke_context.py`, `evals/context_rows.py`, `make smoke-context`, `make context-report SESSION=` | On langchain and langgraph, `context_tokens` stays within its ceiling over the second half while `thread_tokens` rises; turn 2's tool result intact in Cloud SQL; offline, ADK `compactions` of at least 1 with every raw event kept |
| 11.1 | Distinguish agent state, conversation history and knowledge | As today, plus a paragraph on what the thread keeps against what the model is sent, and the kit rule that clears earlier evidence. | The agent-node excerpt now shows the window call | As today |
| 11.3 | Verify restart recovery and session isolation | As today; the model was sent the window, which still held turn 1. | As today | As today; the footer names 11.4 |

**Kit changes**

| File | Change |
|---|---|
| `services/chat/context_window.py` (new) | Named to avoid the brains' `context` parameter. Env with per-call overrides (`CHAT_CONTEXT`, `CHAT_HISTORY_TOKENS`, `ADK_COMPACT_TOKENS`, `ADK_KEEP_EVENTS`, `CHAT_SUMMARY_MODEL`); `turn_start`; `window()` with `trim_messages(strategy="last", start_on="human", allow_partial=False)` on the turns before the floor, copies via `model_copy`, never in place; `middleware()` with both `wrap_model_call` and `awrap_model_call`; the context fields read from G6's per-call records; `adk_compaction()`; `adk_usage()`. The docstring names the rejected `SummarizationMiddleware` (it rewrites the checkpoint). |
| `services/chat/brains.py` | After G8 and G6: one `SYSTEM` sentence; the window last in LangChain's list; `window()` in the LangGraph node, keeping `SystemMessage(content=SYSTEM)` and "never stored"; `App(..., events_compaction_config=...)`; `_run` returns the context fields; the docstring's limits paragraph (17-21). |
| `services/chat/agent.py`, `services/frontend/chat.py` | Named row fields `context_tokens`, `thread_messages`, `thread_tokens`, `context_policy` ('none' for direct), `compactions`, `summary_tokens_in`, `summary_tokens_out`, and the served model; "Six things" becomes "Seven things". The agent caption (150-152) adds context and thread sizes (no page quotes those lines). |
| `smoke/smoke_context.py`, `evals/context_rows.py` (new) | `BRAINS` defaults to langchain and langgraph (adk opt-in, reported, never gated); `TURNS` 12; fresh sessions; a per-turn table with `cached_tokens`; `deploy/` on `sys.path`. `context_rows.py` reads the chat rows from Cloud Logging (retrying for ingestion lag), prints the table and the verdict (INCONCLUSIVE until the thread exceeds twice the budget), with an offline `--selftest`. |
| `mk/memory.mk` (new), `Makefile`, `mk/README.md`, `deploy/README.md` | `smoke-context` (with `$${TURNS:-12}` and `$${BRAINS:-langchain langgraph}`) and `context-report`; `.PHONY`; README mentions beside `smoke-chat` (166) and `make usage` (278). |
| `commands/tests/test_chat_context.py` (new) | The window's invariants including an oversized previous turn, the two-turn recall, the plateau over 20 scripted turns, 80 messages kept, agreement with G8's turn id, ADK compaction at threshold 2,500. |
| `services/rag-api/context_budget.py:20` | The comment names the window and compaction instead of a rolling summary (decision 13). |

**Make targets.** `make smoke-context`, `make context-report` (new, `mk/memory.mk`; not in `smoke-all`, decision 2).

**Infra and IAM.** Nothing new: chat-sa has `roles/aiplatform.user` (`terraform/sa.tf:210-211`). The new env vars are
optional, with code defaults; an override set with `gcloud run services update` is reset by the next
`make deploy-services` (`Makefile:353` empties `CHAT_EXTRA_ENV`, and after G1 only `HANDOFF=on` refills it). Redeploy chat and ui:
`make build deploy-services SERVICES="chat ui" SCRIPTS="commands/lesson-12.8.sh commands/lesson-12.4.sh" PROJECT=documind-ai-YOUR-ID`.

**Pages to rebuild.** 11.4 (new; its Level 0 interactive is a JS port of `window()` checked against the Python with
node, as 11.3 `build.py:445` does). 11.1 (the agent-node excerpt must end at the return line, `build.py:63` and :69;
`a.html:31` and `b.html:24`). 11.3 (`b.html:41`; the footer). 10.2 (the agent-node excerpt at `build.py:68`, and
whatever `check_lesson` names). 6.1 (`a.html:30`, `c.html:104` prose); 16.1 and 17.1 if the `TokenBudget` comment
changes, since they quote it. The tokens-on-the-row guards in 10.1, 10.4 and 13.2 were rebuilt by G6. The same pull
request moves `tools/build_workshop_demos.py:357` and the other lesson counts that section 3 lists.

**Verification**

- Offline: `test_chat_context.py` in the chat pins; `python deploy/evals/context_rows.py --selftest`; `make dryrun`.
- On a lane: (1) redeploy, then `make smoke-chat` and the restart check in `make smoke` with `DOCUMIND_CHAT_URL`; (2)
  `make smoke-context PROJECT=documind-ai-YOUR-ID`, PASS lines on langchain and langgraph; (3) `make context-report
  SESSION=<the smoke's id>`; (4) twelve UI questions on langchain; (5) 11.2's connector cell on the smoke's thread shows
  turn 2's original tool result; (6) the sink table shows the new columns; (7) the author only: one
  `CHAT_CONTEXT=full` run compared on `tokens_in` and `cached_tokens` before the page states any saving.

**Cost.** Estimates only, assuming no implicit caching; the page states only what rows measure. A windowed turn at the
plateau is about Rs 1.40 for the brain's two calls (about 7,500 tokens in, 700 out) plus about Rs 0.70 for rag-api's
answer. `make smoke-context` with defaults is about Rs 45; the optional ADK leg about Rs 35, including flash-lite
summaries at about Rs 0.25 each; the UI walk about Rs 25; the author's full-policy measurement Rs 60 to 125 per brain.

**Risks**

- Implicit caching may shrink the rupee saving far below the token saving (unverified); measured first.
- `count_tokens_approximately` misjudges Gemini 3 content blocks in both directions; the row carries both the estimate
  and the provider's count.
- Clearing earlier evidence forces a new retrieve for follow-ups; check follow-up quality with the judge.
- ADK compaction is experimental and lossy, and the compaction turn's latency includes a summarizer call.
- The window bounds tokens, not storage: the checkpoint still grows with the square of the conversation (11.2
  `parts/c.html:27`).

### 4.9 G9 - The agent brains through the model gateway

**Current state**

- The chat brains call Gemini directly: `build_llm()` returns `ChatGoogleGenerativeAI(vertexai=True, location="global")`
  (`shared/profile.py:34-40`), taken by LangChain and LangGraph (`brains.py:102`, `:121`); ADK passes the bare model name
  (`brains.py:187-194`). Nothing in the chat reads `MODEL_BACKEND` or `LITELLM_URL`, and chat-sa is not a gateway
  invoker (`Makefile:633`, `:636`; `terraform/gateway.tf:3-4`).
- rag-api treats the backend as a setting and a per-tenant pin (`services/rag-api/config.py:119-121`; `main.py:103-127`),
  prices from `x-litellm-response-cost` (`generator.py:122-133`) and caches its ID token (`generator.py:76-84`).
- The gateway cannot start: litellm 1.80.5 rejects `guardrail: custom` (`services/litellm/config.yaml:100-105`) inside
  the lifespan startup with nothing catching it, so the revision never becomes Ready, assuming the image matches PyPI
  1.80.5. 18.1's live cells ran against the `lane181.py` stand-in (`lessons/18-serving/18.1-gateway-routes/build.py:15-16`).
- Under the image's Presidio a bare PAN question is PUBLIC; a PAN is RESTRICTED only when another entity scores 0.7
  (`services/litellm/documind_classifier.py:31-37`; 18.1 `build.py:202-205`). The mask removes answers ("E3" and "60
  days" masked; `documind_router.py:16-26`; 18.1 `build.py:206`). The hook reads string content only (`:20`, `:31-34`)
  and leaves tools in a request it moves to the tool-less self-hosted route (`:44-45`). `smoke/smoke_gateway.py:111-118`
  passes on both branches.

**Target state.** PR A: the gateway starts, classifies each identifier by its own check (PAN by pattern, Aadhaar by
Verhoeff, card by Luhn), masks only email and phone numbers in place, reads list content, fails closed on a body it
cannot read, and its smoke can fail. PR B: the door is chosen per turn, the tenant's pin first and `CHAT_BACKEND`
otherwise (default vertex). `shared/gateway.py` gives LangChain a `ChatOpenAI` with `use_responses_api=False`, a
callable ID-token key and a response hook, and ADK a `LiteLlm` with a client that adds the token. A RESTRICTED request
with tools is flattened into the last user turn as fenced evidence plus a note, never promoted to a user turn of its
own. The cost header is summed onto the row as `gateway_*` fields, and a gateway failure is a 502 with `gateway_route`
parsed from the full error text.

**Scenes**

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 18.1 | Trace and authorize gateway routes | The door, the routes, the classifier (each identifier by its own check; the page keeps the before and after, since it once came back PUBLIC), the mask on email and phone only, the token proxy, and the guardrail entry that lets the gateway start. Then the chat's agent brains through the same door: chat-sa a third caller, the tenant pin or `CHAT_BACKEND` choosing the door, a PAN in a question or passage moving the turn to the tool-less route with fenced evidence, the cost on the chat row. Level 0 gains "tools in the request" and "PAN in a tool result" toggles, built from the real hook. | `services/litellm/config.yaml`, `Dockerfile`, `documind_classifier.py`, `documind_router.py` (`text_of`, the mask, `toolless`), `token_proxy.py`, `terraform/gateway.tf`, `shared/gateway.py`, `brains.py` (`build`), `chat/agent.py`, `smoke/smoke_gateway.py`, `smoke/smoke_chat.py`, `commands/chat-backend.sh`, `make deploy-gateway`, `make smoke-gateway`, `make chat-backend CHAT_BACKEND=gateway`, `make smoke-chat-gateway` | `make smoke-gateway` fails a 200 served by a Vertex api_base; on the chat, `gateway_self_hosted_calls` equals `gateway_calls`, or a 502 with `gateway_route` documind-sensitive, never a 200 from Gemini; `gateway_cost_usd` on the row |

**Kit changes**

| File | Change |
|---|---|
| `services/litellm/config.yaml`, `Dockerfile` (A) | The entry becomes `guardrail: documind_router.DocuMindRouter`, `mode: "pre_call"`, `default_on: true`; `ENV PYTHONPATH=/app`. The `Dockerfile`'s COPY and FROM lines stay (18.1 `build.py:115`, :145). |
| `services/litellm/documind_classifier.py` (A) | Layer 1 authoritative per type, stdlib checks; the any-entity rule at 31-37 goes; Presidio kept for the confidential layer; test values with valid checksums chosen at build time. |
| `services/litellm/documind_router.py` (A, then B) | A: `text_of()` for list content; `mask_pii` with `entities=["EMAIL_ADDRESS", "PHONE_NUMBER"]`, rewriting text parts in place; a body with `input` or `prompt` and no `messages` is RESTRICTED. B: `toolless()` in the RESTRICTED branch pops tool fields and `reasoning_effort`, turns tool calls into text, and puts the question, each tool result in G5's fence and one sentence in the last user turn; requests without tools are untouched. |
| `smoke/smoke_gateway.py` (A) | PASS on a 200 whose `x-litellm-model-api-base` contains `127.0.0.1:8090` or a 5xx naming documind-sensitive; FAIL on a 200 from any other api_base. |
| `shared/gateway.py` (new, B) | The route map (a non-Gemini route raises, since an agent loop needs tools); a cached token; a per-turn ledger that reports into G6's Meter; `backend_for(tenant)` from `tenant_settings` cached 60 s, falling back to `CHAT_BACKEND` with a warning; `chat_model()` with `max_retries=0` and `timeout` 90; `adk_model()`; `route_of(exc)` with `(?:model_group=\|Model Group=)(documind-[a-z-]+)`; framework imports inside functions. |
| `services/chat/brains.py`, `agent.py` (B) | `build(name, checkpointer, llm=None, backend="vertex")` passes the gateway model; `AdkBrain` uses a given model before the local branch; quoted blocks unchanged; `shared/profile.py` untouched (10.4 `build.py:91`). `agent.py`: the backend per turn after the tenant check (10.3 quotes it, n=2), brains cached per (brain, backend), the `gateway_*` fields on the row and response, a 502 handler. |
| requirements (B) | `langchain-openai==1.6.2`, `openai==2.54.0`, and `litellm==1.99.0` moved from `requirements-local.txt:12`; resolution checked clean with no SQLAlchemy. |
| `Makefile`, `commands/lesson-12.8.sh` (B) | `CHAT_BACKEND ?= vertex` after 97; `deploy-services` computes `CHAT_GATEWAY_ENV` in the `Makefile` with `$(REGION)`; line 353 unchanged; the `deploy-gateway` loop (633) adds chat-sa, and the echo and comment name it; `.PHONY`. `lesson-12.8.sh:32` appends only `${CHAT_GATEWAY_ENV-}`, adding no `${REGION:-us-central1}`, so 10.1's count stays where G2 left it. |
| `mk/serving.mk` (new), `commands/chat-backend.sh` (new), `mk/README.md` (B) | `chat-backend` and `smoke-chat-gateway`; `deploy-gateway` and the other Module 18 targets stay in the `Makefile`, because 18.1-18.4 quote them from there. The script stops when the gateway revision is not Ready or chat-sa is not an invoker, notes the second door (rag-api) and, after G1, the third (the peer), then updates the env. |
| `smoke/smoke_chat.py` (B) | A `DOCUMIND_EXPECT_GATEWAY=1` section on fresh `smoke-gw-<brain>-<epoch>` sessions: `model_backend` gateway, two or more calls, a cost; the PAN turn as in the proof. Lines 11-13 untouched (8.2). |
| `terraform/sa.tf`, `gateway.tf`, `tools/check_authz.py`, `tools/check_gateway_chat.py` (new) | A prose sentence under the caller graph, not a graph line; `gateway.tf:3-4` names chat-sa. `check_authz` parses the `deploy-gateway` loop and asserts agent-sa is absent. `check_gateway_chat.py`: a stdlib tier in CI with Presidio stubbed to find nothing, a framework tier, and a proxy tier on litellm[proxy] 1.80.5 that loads the real config and drives the brains. |

**Make targets.** `make deploy-gateway` (binds chat-sa, redeploys the loadable entry), `make smoke-gateway`
(falsifiable), `make chat-backend CHAT_BACKEND=gateway` or `vertex`, `make smoke-chat-gateway` (new, `mk/serving.mk`),
`make deploy-services SCRIPTS=commands/lesson-12.8.sh CHAT_BACKEND=gateway`, `make off`.

**Infra and IAM.** `deploy-gateway` grants chat-sa `run.invoker` on documind-gateway. documind-chat gains
`MODEL_BACKEND` and `LITELLM_URL` only when gateway is chosen. A tenant pin that rag-api already honours now also moves
that tenant's chat turns. The gateway is redeployed with an entry that loads and runs on every request, which also
changes what rag-api's gateway candidates get. There is no new service, account or database.

**Pages to rebuild.** PR A: 18.1 (findings become fixes: `build.py:104`, :152, :201-206, the trace adding agent-shaped
requests under the real Presidio); 18.2 and 18.4 re-run. PR B: 18.1's new level (`build.py:97`, :118; `lane181.py` learns
tools); re-run 10.1-10.4, 11.1-11.3, 12.2 and 13.2 with no text change expected. The module_18 demos and a review entry.

**Verification**

- Offline: `python tools/check_gateway_chat.py` (the stdlib tier; the framework tier in the chat pins; the proxy tier in
  a litellm[proxy] 1.80.5 venv, where `init_guardrails_v2` loads with `PYTHONPATH` and fails without it);
  `PRESIDIO_PY=... python lessons/18-serving/18.1-gateway-routes/build.py`; `check_authz.py`; `validate.py`.
- On a lane: (1) `make deploy-gateway PROJECT=documind-ai-YOUR-ID`, then the documind-gateway revision's Ready
  condition, the first time the real image runs this config; `get-iam-policy` lists chat-sa; `make smoke-gateway`
  passes; (2) `make deploy-services ... CHAT_BACKEND=gateway`; (3) `make smoke-chat-gateway`; (4) chat rows with
  `jsonPayload.model_backend="gateway"`; (5) optional: a tenant pin on acme moves one turn, then removed; (6)
  `make chat-backend CHAT_BACKEND=vertex`, `make off`, `make smoke-chat` green. documind-api is not moved to the
  gateway in this lesson.

**Cost.** There is no new standing cost; the gateway and its db-f1-micro exist (`terraform/gateway.tf:50-69`). Gemini
tokens cost the same through either door (Rs 127.50 and Rs 637.50 per million in and out for documind-general,
`services/litellm/config.yaml:23-24`). The added cost is gateway CPU per model call, two to twelve per turn, with NER
over the resent thread; it is not measured, so no figure goes on the page until the lane gives one. The sensitive route
bills only when 18.2's L4 is up: Rs 86,904 a month if left warm (`Makefile:648`); the proof also works with the GPU off
(the 502 path).

**Risks**

- The first real run of the gateway image may surface more than the loader error; budget a lane session for PR A alone.
- The classifier fix changes routing everywhere, including rag-api's gateway candidates and 18.2 and 18.4's
  comparisons.
- Sensitivity is sticky: one PAN sends the rest of the thread to the tool-less route.
- The SLM's context is `num_ctx 4096` (`services/slm/Modelfile:18`), and flattened evidence can exceed it.
- The perimeter keeps a second door (rag-api's answer for `retrieve()`) and, after G1, a third (the peer); the chat's
  setting covers neither (decision 14).
- The chat image grows by litellm, openai and their dependencies, and the client and server litellm versions differ.
- Never send `x-litellm-tags` from the chat: tag filtering (`services/litellm/config.yaml:82`) rejects unknown tags.

## 5. Library APIs this plan relies on

"Source" means read in the pinned version's installed package in a scratch venv; "run" means exercised by a script
there; "unverified" means neither, and the plan says how it is settled.

| API | Pinned version | Status | Evidence |
|---|---|---|---|
| langchain requires langgraph >=1.2.11,<1.3.0 and resolves 1.2.12, with langgraph-prebuilt 1.1.0 | langchain 1.4.0 | Confirmed, source | `langchain-1.4.0.dist-info` METADATA |
| `create_agent` binds `recursion_limit` 9,999; langgraph's default is 10,007 | langchain 1.4.0, langgraph 1.2.12 | Confirmed, source | `langchain/agents/factory.py:1829-1831`; `langgraph/_internal/_config.py:32` |
| Middleware order: first is outermost for wrap hooks; `after_model` runs last to first | langchain 1.4.0 | Confirmed, source | `factory.py:661`, `:1787-1800` |
| `wrap_model_call` may return an `AIMessage` without calling the handler; `model_settings` reach `bind_tools`; `ModelRequest.override(messages=)` | langchain 1.4.0 | Confirmed, source and run | `langchain/agents/middleware/types.py:98`, `:315`, `:503-526`; `factory.py:1396-1439`; g6review r3 |
| `before_model` and `after_model` hooks add graph nodes (+5/+9 checkpoints); `wrap_model_call` alone keeps +3/+5 | langchain 1.4.0 | Confirmed, run | g6review r1 on the kit's guard |
| A middleware with only sync `wrap_model_call` raises under `ainvoke` | langchain 1.4.0 | Confirmed, source | `types.py:638-648`; `factory.py:1144-1152` |
| `HumanInTheLoopMiddleware(interrupt_on={tool: {allowed_decisions, description, when}})`; a reject adds a status-error ToolMessage; it interrupts on every matching call without checking for a ToolMessage | langchain 1.4.0 | Confirmed, source and run (the last point source only) | `langchain/agents/middleware/human_in_the_loop.py:28-51`, `:195`, `:217-277`, `:337-354`, `:405-492` |
| `interrupt()`, `Command(resume=...)`, `__interrupt__`, `get_state().interrupts` | langgraph 1.2.12 | Confirmed, source and run | `langgraph/types.py:728`, `:827-860`, `:902`; `pregel/main.py:3946-3954` |
| A paused turn resumes from a second process sharing the Postgres checkpointer | langgraph-checkpoint-postgres 3.1.2 | Unverified (shown with a shared `InMemorySaver`) | `langgraph/checkpoint/postgres/__init__.py:598`; settled by G2's live step |
| A new message on an interrupted thread drops the interrupt | langgraph 1.2.12 | Confirmed, run | g2 `hitl_newmsg.py` |
| `ToolNode(wrap_tool_call=)` takes one wrapper; parallel calls run through `executor.map`; only `ToolInvocationError` is turned into a message by default | langgraph-prebuilt 1.1.0 | Confirmed, source | `langgraph/prebuilt/tool_node.py:755-770`, `:821-823`, `:383-391` |
| `ToolRuntime.context` is the dict passed to `invoke(context=...)` | langgraph 1.2.12 | Confirmed, source | `pregel/main.py:4337-4364`; `tool_node.py:806-810`, `:841-845` |
| `add_messages` keeps a caller-set id | langgraph 1.2.12 | Confirmed, source | `langgraph/graph/message.py:204-208` |
| `GraphRecursionError` is a `RecursionError`; `update_state` repairs a thread | langgraph 1.2.12 | Confirmed, source and run | `langgraph/errors.py:67`; g6 `t_repair.py` |
| `ToolException` with `handle_tool_error=True` gives a status-error message | langchain-core 1.6.2 | Confirmed, source | `langchain_core/tools/base.py:1121-1126` |
| `trim_messages(strategy="last", start_on="human", allow_partial=False)` returns [] when the last turn exceeds the budget | langchain-core 1.6.2 | Confirmed, source and run | `langchain_core/messages/utils.py:2086-2130`; g7review `trim_edge.py` |
| A callback's `on_llm_end` sees exactly one request's calls | langchain-core 1.6.2 | Confirmed, run | `langchain_core/callbacks/base.py:90`; g7review `cb_probe.py` |
| `SummarizationMiddleware` rewrites the checkpoint with `RemoveMessage(REMOVE_ALL_MESSAGES)` | langchain 1.4.0 | Confirmed, source | `langchain/agents/middleware/summarization.py:398-437` |
| Sticky taint: middleware `state_schema` plus `Command(update=...)` persists; ADK `tool_context.state` persists to the session | langchain 1.4.0, google-adk 2.8.0 | Confirmed, run | g5review `sticky_taint.py` |
| langchain, langchain-core and langgraph emit no OpenTelemetry; langsmith's bridge is off by default | langsmith 0.14.1 | Confirmed, source | grep of the venv; `langsmith/_internal/otel/` |
| Per-call `timeout` and `max_retries` (as total attempts); httpx timeouts not wrapped; `usage_metadata` counts thoughts as output and `cache_read` | langchain-google-genai 4.4.0 | Confirmed, source | `langchain_google_genai/chat_models.py:362-367`, `:2040-2071`, `:3850-3858`, `:4089-4097` |
| google-genai retries timeouts; `HttpOptions.timeout` is in milliseconds | google-genai 2.22.0 | Confirmed, source | `google/genai/_api_client.py:105-118`, `:248-258`, `:547-593` |
| `RunConfig.max_llm_calls` reads `ADK_MAX_LLM_CALLS` (default 500) and raises `LlmCallsLimitExceededError`; `to_a2a` builds a `RunConfig` per request and turns an exception into a failed task | google-adk 2.8.0 | Confirmed, source (the live over-cap task unverified) | `google/adk/agents/run_config.py:36-50`; `invocation_context.py:86-102`; `a2a/converters/request_converter.py:120`; `a2a/executor/a2a_agent_executor.py:152-172` |
| `before_model_callback` runs before ADK counts the call; `on_model_error_callback` can end a timed-out call; ADK's Gemini does not retry by default | google-adk 2.8.0 | Confirmed, source and run | `flows/llm_flows/base_llm_flow.py:1734-1762`; `agents/llm_agent.py:96-103`, `:478`; `models/google_llm.py:182`; g6review r4, r5 |
| `on_tool_error_callback` covers a missing tool (before `before_tool_callback`) and a raising tool; `after_tool_callback`'s dict replaces the response; the missing-argument check returns `{'error'}` with no status | google-adk 2.8.0 | Confirmed, source and run | `flows/llm_flows/functions.py:589-605`, `:631-646`, `:652-683`; `tools/function_tool.py` `run_async` |
| `FunctionTool` declares every parameter but the context and drops undeclared arguments; a ContextVar set before `asyncio.run` reaches tools | google-adk 2.8.0 | Confirmed, source | `tools/function_tool.py:140-156`, `:266-288`; `functions.py:231-258` |
| `asyncio.wait_for(asyncio.to_thread(...))` inside `asyncio.run` waits for the thread; `run_in_executor` on an own pool returns at the budget | Python 3.12 (`python:3.12-slim`) | Confirmed, source and run | `asyncio/runners.py:73`; g6review r2, r6 |
| `FunctionTool(require_confirmation=True)` and `adk_request_confirmation` (experimental) | google-adk 2.8.0 | Confirmed, source and run | `tools/function_tool.py:106-142`, `:291-352`; `tools/tool_confirmation.py:28-56` |
| `DatabaseSessionService` needs the `[db]` extra and creates its own tables | google-adk 2.8.0 | Confirmed, source and run | METADATA:124; `utils/_dependency.py:28`; `sessions/database_session_service.py:233-236`, `:510` |
| `App.events_compaction_config` (experimental; import from `google.adk.apps.app`); compaction appends an event and keeps raw events; splits keep call and response pairs, not turns | google-adk 2.8.0 | Confirmed, source and run | `apps/app.py:29`, `:84`; `apps/_configs.py:49-106`; `flows/llm_flows/compaction.py:36-57`; `apps/compaction.py:336-449`; `apps/llm_event_summarizer.py:66`, `:146-177` |
| `McpToolset(tool_filter=)` predicate; `header_provider` and sessions keyed by headers; MCP errors returned as data; `outputSchema` sent as `response_json_schema` under an experimental flag on by default; the trace injected into `_meta` | google-adk 2.8.0 | Confirmed, source | `tools/base_toolset.py:41-58`; `tools/mcp_tool/mcp_toolset.py:339-366`, `:482-536`; `mcp_session_manager.py:818-843`; `mcp_tool.py:35`, `:247-268`, `:417-430`, `:487-491`; `features/_feature_registry.py:170-178` |
| ADK spans (`invocation`, `invoke_agent`, `execute_tool`, `call_llm`); content capture defaults on; tool arguments recorded after the guard mutates them; `session_id` on spans ungated | google-adk 2.8.0 | Confirmed, source and run | `telemetry/_instrumentation.py:133`, `:470`, `:507`; `telemetry/context.py:107-110`; `functions.py:709-710`; `telemetry/tracing.py:305-311`, `:624-626` |
| google-adk caps opentelemetry api and sdk at <=1.42.1 | google-adk 2.8.0 | Confirmed, source | METADATA:32-33 |
| `RemoteA2aAgent` (experimental) with `a2a_client_factory`; `httpx_client` deprecated; card RPC URLs must share the origin | google-adk 2.8.0 | Confirmed, source and run | `agents/remote_a2a_agent.py:333-345`, `:562`, `:595-616`, `:624`, `:663`, `:907-950` |
| `AgentTool` sends only `args["request"]`, declares `agent.description`, returns a remote failure as a result string | google-adk 2.8.0 | Confirmed, source and run | `tools/agent_tool.py:160-199`, `:246-257`, `:343-347` |
| `ClientConfig`, `ClientFactory`, `TransportProtocol`, `TaskState.Name`; the `[a2a]` extra is `a2a-sdk[http-server]>=0.3.4,<2` and resolves without SQLAlchemy | a2a-sdk 1.1.2 | Confirmed, source and run | `a2a/client/client.py:40-57`; `a2a/utils/constants.py:15`; importlib metadata |
| a2a-sdk telemetry is on by default and off with `OTEL_INSTRUMENTATION_A2A_SDK_ENABLED=false`, read at import | a2a-sdk 1.1.2 | Confirmed, source and run | `a2a/utils/telemetry.py:23-27`, `:107` |
| An `httpx.Auth.async_auth_flow` override minting in a thread keeps the metadata call off the loop | httpx 0.28.1 | Unverified end to end | `httpx/_auth.py:87`; covered by `test_handoff.py` |
| ADK's `ServiceAccount(use_id_token=True)` scheme as the peer's auth | google-adk 2.8.0 | Unverified; not used | `auth/credential_manager.py:230-260` |
| `RemoteAuthProvider` publishes RFC 9728 metadata; `RequireAuthMiddleware` answers 401 before JSON-RPC; a `TokenVerifier` with `expires_at` 0 skips expiry | fastmcp 3.4.7, mcp 1.30.0 | Confirmed, source and run | `fastmcp/server/auth/auth.py:54-57`, `:366-507`; `fastmcp/server/http.py:589-621`; `mcp/server/auth/middleware/bearer_auth.py:61-85` |
| `host_origin_protection` defaults off; "auto" answers 403 and 421 on loopback | fastmcp 3.4.7 | Confirmed, source and run | `fastmcp/settings.py:343`; `fastmcp/server/http.py:225-296` |
| `AuthMiddleware` filters `tools/list` and checks `tools/call`; sync checks run on the loop while sync tools run in threads | fastmcp 3.4.7 | Confirmed, source | `server/middleware/authorization.py:112-186`; `utilities/authorization.py:76-99`; `utilities/async_utils.py:26-34`; `tools/function_tool.py:457` |
| A `ToolError` from `on_call_tool` reaches the client as `is_error`, through `create_proxy` too; the first listed middleware runs first; a proxy middleware can inject and refuse an argument | fastmcp 3.4.7 | Confirmed, run | `fastmcp/server/server.py:527`, `:2487-2500`; `server/middleware/middleware.py:61-62`, `:168` |
| `@mcp.tool(annotations=, output_schema=)`; with a schema `.data` becomes a generated type; clients validate `structuredContent` | fastmcp 3.4.7, mcp 1.30.0 | Confirmed, source | `fastmcp/server/server.py:1694-1712`; `fastmcp/client/mixins/tools.py:450-463`; `mcp/client/session.py:412-445` |
| FastMCP lists `outputSchema` `{type: object, additionalProperties: true}` and no annotations for the four kit tools | fastmcp 3.4.7 | Confirmed, run | g5review `list_tools.py` |
| The `tools/call` span opens inside the middleware chain and records `str(e)` on failure; a `ToolError` logs only a generic line | fastmcp 3.4.7 | Confirmed, source | `fastmcp/server/server.py:1249-1281`, `:1327-1331`; `fastmcp/server/telemetry.py:103-104` |
| `RateLimitingMiddleware` raises `McpError` -32000, not a tool result | fastmcp 3.4.7 | Confirmed, source | `server/middleware/rate_limiting.py:10-20`, `:93` |
| `GoogleProvider` and `MultiAuth` exist for phase 3 | fastmcp 3.4.7 | Confirmed, source; not exercised | `server/auth/providers/google.py:204-283`; `auth.py:510` |
| `force_flush` ignores its timeout; an empty queue makes no RPC; the Trace RPC defaults to 120 s | opentelemetry-sdk 1.42.1 | Confirmed, source (1.44.0 not checked) | `opentelemetry/sdk/_shared_internal/__init__.py:128-129`, `:240-245`; `google/cloud/trace_v2/services/trace_service/transports/base.py:161` |
| `to_thread.run_sync(abandon_on_cancel=True)` | anyio 4.15.1 | Confirmed, source | `anyio/to_thread.py:27-39` |
| `ReadableSpan` constructor is public; `CloudTraceSpanExporter(resource_regex=)` | opentelemetry-sdk 1.42.1, exporter-gcp-trace 1.15.0 | Confirmed, source | `opentelemetry/sdk/trace/__init__.py:412-426`; `opentelemetry/exporter/cloud_trace/__init__.py:170-189` |
| The genai instrumentor treats `NO_CONTENT` as off and patches the call langchain-google-genai makes | instrumentation-google-genai 0.7b1 | Confirmed, source | `opentelemetry/instrumentation/google_genai/flags.py:24-33`, `generate_content.py:118-120` |
| `FilterResult` has no `match_state`; the verdicts are `filter_match_state` and the pi_and_jailbreak result | google-cloud-modelarmor 0.7.1 | Confirmed, source and run | `google/cloud/modelarmor_v1/types/service.py:1254-1420`, `:1998-2030` |
| `guardrail: custom` is rejected inside the lifespan startup; `file.Class` loads with no `sys.path` change; `default_on`; router errors append the group name last; the cost and api-base headers | litellm 1.80.5 | Confirmed, source (the Docker image matching PyPI unverified) | `proxy/guardrails/guardrail_registry.py:434-510`; `proxy/guardrails/init_guardrails.py:18-34`; `proxy/proxy_server.py:2575-2580`, `:784`; `integrations/custom_guardrail.py:246-306`; `router.py:4178-4222`; `proxy/common_request_processing.py:224-245` |
| `ChatOpenAI` takes a callable key refreshed per request, and switches to the Responses API unless `use_responses_api=False` | langchain-openai 1.6.2, openai 2.54.0 | Confirmed, source | `langchain_openai/chat_models/base.py:742-744`, `:1237-1247`, `:1924-1937`, `:4464-4476`; `openai/_client.py:558-582` |
| `LiteLlm(llm_client=)` as a per-call seam | google-adk 2.8.0 | Confirmed, source | `models/lite_llm.py:865-895`, `:3042`, `:3048-3061` |
| Cloud Run fills `traceparent` and caps sampling at 0.1 unforced and 10 forced requests per second per instance | Cloud Run (service) | Confirmed, docs fetched in review | docs.cloud.google.com/run/docs/trace |
| Cloud Run keeps an incoming trace id; Cloud Logging lifts the trace keys from a stdout JSON line; Cloud Trace's price | Cloud Run, Logging, Trace | Unverified | G3 live steps 2 and 5; the page reads the price before stating it |
| Cloud Run's IAM answers before the app for a tokenless or non-invoker request | Cloud Run | Unverified | G4 check 5 skips naming the door |
| Gemini accepts the nested `response_json_schema` ADK forwards; validates thought signatures only for the current turn; serves long prefixes from an implicit cache | Gemini 3 on global | Unverified | `make smoke-agent` (G4); `make smoke-context` and the author's full run (G7) |
| `run.invoker` on a job allows an empty-body `:run` | Cloud Run jobs | Unverified (the kit's own pattern, `services/ingest/main.py:266-276`) | G2's live approve step |
| Model Armor's pi_and_jailbreak filter flags document-borne instructions; its logging stores no chunk text | Model Armor | Unverified | measured on `g5-armor`; checked in Cloud Logging before `ARMOR_CONTEXT` |
| Streamlit fetches a markdown image and an `<img>` rendered with `unsafe_allow_html` | Streamlit 1.63.0 | Unverified | G5's live cell shows the fetch against a `.invalid` host |
| Ollama's legacy `{{ .Prompt }}` template renders neither the system message nor tool messages | Ollama | Unverified | the flattening into the last user turn works either way |
| `ChatOllama` accepts per-call `timeout` and `max_retries` | langchain-ollama 1.1.0 | Unverified | G6 applies them on the gcp profile only |
| Claude Desktop, Cursor and Gemini CLI read `{command, args, env}` stdio blocks | client apps | Unverified | the bridge proved with fastmcp's stdio client; G4 live step 5 |

## 6. Decisions this plan needs

1. **New lessons and the lesson count.** Recommended: add three Core lessons, 11.4 "Bound the model's context while
   keeping the full conversation" (G7), 12.4 "Hand a turn from the ADK brain to the A2A peer" (G1) and 12.5 "Defend
   agents against injected documents and poisoned tools" (G5): 60 to 63 lessons, Core 47 to 50, 70.5 to 75 hours. Each
   has its own working piece, target and proof, and the fallbacks overload 12.3, which already takes changes from G3,
   G4 and G6. Fallbacks at 60: G1 into 12.3 as two levels with `judge-handoff` as a Verify row; G5 split into 10.3
   (documents) and 12.3 (tools), keeping manifest titles; G7 as a new top level in 11.1. Not now: G4's phase-3 OAuth
   lesson, and a 10.5 split of G2 unless 10.2 runs past 90 minutes.
2. **Module gates.** Recommended: Module 12's gate adds `make smoke-handoff`; `make attack-eval` stays 12.5's proof,
   because it loads a fixture and adds a tag on every run; Module 11 keeps the restart check; `smoke-approval` and
   `smoke-context` stay out of `smoke-all` (one withdraws and restores a document, the other costs about Rs 45).
3. **Which write tool gets approval.** Recommended: `withdraw_document` only, because it is reversible with
   `make restore`, on LangChain and LangGraph on the lane. The MCP server and the peer stay read-only. A handoff is not
   approval-gated: the peer's membership of the tenant's roster counts as the tenant's consent. `TAINT_GATED` is G2's
   approval set; `documind_peer` is a taint source, not gated.
4. **Durable ADK sessions.** Recommended: a separate item outside this plan (`google-adk[db]==2.8.0`, a migration job
   for ADK's own tables against 8.5's migrate rule, and rebuilds of 11.1-11.3). Until then ADK approval and compaction
   are proven offline, and live smokes default to langchain and langgraph.
5. **Approver role and the withdrawal path.** Recommended: approvers in `tenants/{t}/approvers/{email}`, which changes
   no quoted line; the fixed-argument `documind-withdraw` job; a failed job start is recovered by `make withdraw-run` by
   hand; `make retire` from the shell writes no `doc.withdraw`; the pending response is 200 with
   `status: pending_approval`; approvers decide on the tenant chat page. An 11.3 step showing that a paused approval
   survives a redeploy is optional and not planned here.
6. **MCP client auth.** Recommended: Google ID tokens behind `RemoteAuthProvider` with RFC 9728 metadata naming
   `https://accounts.google.com` (stored with fastmcp's trailing slash), honest about the issuer though no standard
   client can finish an OAuth flow against it. Desktop clients use the tenant-pinned stdio bridge as documind-ui-sa
   now. A single-tenant `documind-desktop-sa` (Terraform, roster, invoker, operators; rebuilds 8.1, 12.2, 12.3) and the
   `GoogleProvider` OAuth proxy in `MultiAuth` (a manual OAuth client, two secrets, a separate Firestore database,
   documind-mcp opened at Cloud Run) wait. Pick one client for 12.2's live cell: Claude Desktop, or Gemini CLI or
   Claude Code from a terminal.
7. **MCP budget and CI.** Recommended: tool calls per verified email per instance, 60 a minute, refused with a
   readable `ToolError`, not HTTP 429; the burst stays in `make smoke-mcp` as a check that passes or skips;
   `calculate_processing_cost` open to any verified caller; `fastmcp==3.4.7` in both CI install lines so the new tests
   run.
8. **Handoff defaults.** Recommended: `HANDOFF` off by default with `make handoff` in 12.4; `PEER_TIMEOUT_S` 75 and
   `HANDOFF_MAX_PER_TURN` 2, measured in 12.4; only the ADK brain hands off; the hop priced locally in 12.4, not by a
   peer-side row that would change 12.3's excerpt; the chat row only, no `agent.handoff` audit event.
9. **Chat limits.** Recommended: 12 model calls, Rs 5 per turn (reset after a week of `cost_usd` plus `rag_cost_usd`
   rows), two attempts per call, HTTP 200 with `stopped_by`, a fixed stop sentence, a peer over its cap ending
   `failed`. Deadline: keep 100 s with the UI at 120 s and accept that cold-API turns stop, or 120 s with the UI at
   150 s (worst case about 123 s); recommended 100/120 for the lab. Recording the loop's spend in the month counter
   and `tenant_daily` is a later phase.
10. **Tracing.** Recommended: the genai instrumentor in chat at 0.7b1 with a narrow ADK-cap allowance in `validate.py`;
    the `@tracing.server` decorator (no re-indent of 10.1's and 11.3's lines); scrub exception text at export; the
    flush on with 2 s; `TRACE_SAMPLE` 0.1 for roots; a2a-sdk telemetry off; the peer's tracing inline; the reader
    roles stated on the page, not granted in Terraform.
11. **G8's contract.** Recommended: remove `get_usage_stats` (wiring it would give chat-sa `dataViewer` on every
    tenant's rows); number citations per turn with the instruction to search again, since per-thread numbering changes
    `citations.py` lines 6.4 quotes; narrow ADK's error handling to `ValueError` and `TypeError` plus `mark_error`;
    per-run smoke sessions; no `n` on the direct brain's citations and no citation count on the row.
12. **Injection defences.** Recommended: the context screen per query on the `g5-armor` tag, failing closed on the tag;
    teach `DATED_RULE` with text-declared dates as a known risk in 12.5 and fix it later; strip every HTML comment in
    text uploads at ingest in a later pull request (no corpus file has a non-leading comment, so no chunk changes);
    the frontend keeps a local copy of the scrub checked by `validate.py`; no `malicious_uri_filter_settings` until
    provider support is checked.
13. **Context window.** Recommended: on by default on the deployed service; `CHAT_HISTORY_TOKENS` 2,000,
    `ADK_COMPACT_TOKENS` 9,500 and `ADK_KEEP_EVENTS` 4 or 6, retuned after the first lane run; earlier tool results
    cleared; no rolling summary for LangChain and LangGraph; stepped cut points only if measured caching shows a loss;
    correct the `TokenBudget` comment in G7's pull request and rebuild 6.1, 16.1 and 17.1.
14. **Gateway.** Recommended: the chat's default door stays vertex; a sensitive agent turn is a tool-less small-model
    answer over fenced evidence; `reasoning_effort` low on documind-general; a failed tenant-pin read falls back to the
    service default; the mask covers email and phone only; the peer stays on Gemini, stated as the third door, until
    a later item routes it through the gateway (agent-sa as an invoker, `check_authz.py:160`, a 12.3 rebuild); a
    retry-free `retrieve`-only flag on `/v1/query` as its own gap; dropping `roles/aiplatform.user` from chat-sa only
    once a lane commits to the gateway (`tools/check_authz.py:125` asserts the role today); no tags from the chat, and
    tenant and brain attribution in the gateway's spend logs deferred. A 10.4 sentence pointing to 18.1 is its own
    one-lesson pull request, or none.
15. **Manifest proof text of extended lessons.** Recommended: rewrite, in each lesson's own pull request, the proofs of
    10.2 ("a withdrawal pauses for an approver and resumes"), 10.3 (an enforced timeout and a refused self-approval),
    12.1 and 12.2 (G4's proofs) and 13.3 (a turn stopped by its budget), with the plan and roadmap rows; the demo
    summaries regenerate. The count does not change for these.
16. **Pull request slicing and publishing.** Recommended: a kit pull request carries the rebuilds its quoted lines force
    (so G8-a spans 10.1-10.4 and G6-a spans eight lessons), and new scene content follows one lesson per pull request;
    publish the learner kit at the end of each phase, each time with the author's explicit go-ahead.
