# mk/ - the Makefile, one file per lane

The kit's `Makefile` keeps what every target shares: the variables (`PROJECT`, `REGION`, the Terraform variable
list, the service list), `guard-project`, `.PHONY`, and the core lifecycle of a lane (`plan`, `up`, `build`,
`deploy-services`, `down`, the smokes, the release). Everything a course module teaches as its own operations lives
here, one file per lane, pulled in by `include mk/*.mk`:

| File | Targets | Course module |
|---|---|---|
| `lane.mk` | `build-access`, `bq-views-when-ready`, `down-region` | 0 Setup (the lane's own guards, found on a new organization lane on 20 October 2026: the build account's three grants before `make up` builds, `commands/build-access.sh`, lesson 0.3's recovery made a step; the BigQuery views deferred until the log sink's table exists, `commands/bq-views-when-ready.sh`; and `make down` refused when `REGION` is not the region the clone prepared the lane in, `commands/down-region.sh`, lesson 0.4) |
| `ingestion.mk` | `roster`, `tenant-policy`, `tenant-backend`, `managed-sync`, `vector-status`, `wait-vectors`, `backfill-vectors`, `ingest-one`, `poison`, `dlq` | 3 Ingestion |
| `lifecycle.mk` | `reindex`, `retire`, `restore`, `reconcile`, `backfill-current`, `reconcile-job`, `sources`, `purge`, `smoke-reindex`, `batch-job`, `batch`, `queued` | 4 Lifecycle |
| `retrieval.mk` | `decide` | 2 Retrieval (the answer-or-refuse eval, lesson 2.6: `evals/decide.py`, with Jev behind `JEV_MODE`) |
| `generation.mk` | `bench`, `prompt-version`, `improve`, `prompt-candidate` | 3 Generation (the prompt bench, lessons 3.1-3.3: `evals/prompt_bench.py`, each row's pool held fixed while the kit's own `generate()` answers at each thinking level, temperature or rule edit; the prompt bound to its version, lesson 3.6: `commands/prompt_pin.py` against `services/rag-api/prompt_versions.json`; and Module 12's eval-gated self-improvement, lesson 12.4: `evals/improve.py` turns a production answer into a rule a person accepts as the next version in `services/rag-api/prompt_rules.json`, and `prompt-candidate` puts that version on a candidate revision as `PROMPT_VERSION`) |
| `agents.mk` | `desk-check`, `route-probe`, `route-index`, `route-calibrate`, `doc-types`, `limits`, `limits-check`, `limits-drill`, `desk`, `roles`, `desk-queues`, `cases`, `cases-overdue`, `smoke-cases`, `smoke-desk`, `route-eval`, `desk-views`, `desk-job`, `desk-operators`, `deploy-gchat`, `smoke-gchat`, `agent-turn`, `agent-eval`, `agent-tests`, `route-compare`, `arms-combine`, `approval-check`, `exemplars`, `agent-drill`, `handoff`, `smoke-handoff`, `check-callers`, `pin-tools`, `evil-mcp`, `mcp-local`, `attack-agents`, `agent-shapes`, `agent-actions`, `withdraw-run`, `smoke-approval` | 10 Agents (a chat turn's limits, lesson 5.5; the DocuMind Desk, lessons 5.6 and 10.4, and its Google Chat door; the agent bench, lessons 10.1-10.3 and 10.5, with lesson 10.5's Desk arms side by side and combined, and a person in the loop, offline, lesson 5.8, appended below the Desk's targets; the router's prompt examples on and off, lesson 3.2; A2A peer's cap tripped on the lane, the chat's hand-off to the peer switched on and smoked, and the caller graph checked for a cycle, offline, lesson 10.7; the peer's tools pinned and a poisoned server refused, lesson 10.8, appended after them; the MCP server in the local profile and the attack set on the agents' doors, lesson 10.8, after those; two ADK desks handing a question back and forth until a transfer cap stops them, offline, lesson 10.7, appended after those; the approval wired into the chat service behind a company's `agent_actions` switch, the approved withdrawal the operator runs through `services/ingest/reconcile.py --approved`, and its live smoke, lesson 5.8, appended last) |
| `managed.mk` | `managed-peer-up`, `managed-peer-ask`, `managed-peer-trace`, `managed-peer-smoke`, `managed-peer-sessions`, `managed-peer-down` | 10 Agents (lesson 10.6's A2A peer on Vertex AI Agent Engine, lesson 10.9: `commands/managed_peer.py`, which stages `services/agent/` as it is with `commands/managed_peer_agent.py`, run in `~/managed-peer-venv` by `commands/managed-peer.sh`; torn down by `managed-peer-down`, and by the smoke when it deployed the peer itself) |
| `evaluation.mk` | `label-sheet`, `judge-agree`, `judge-frozen`, `triage`, `attack-offline`, `attack-eval` | 4 Evals and safety (the LLM judge checked against people, lesson 4.5: `evals/build_judge_set.py`, `evals/judge_agree.py`, and `evals/judge.py` on the frozen rows; a live eval's failing rows read before their causes, and the attack set on rag-api's doors offline and on the lane, lesson 4.9: `evals/triage.py`, and `evals/run_attacks.py` over `evals/adversarial/attacks.jsonl`, which lesson 10.8 extends) |
| `memory.mk` | `thread`, `replay`, `context-sources`, `window-check` | 6 Context and memory (a conversation's checkpoints read back from the lane, and one turn replayed and forked locally, lesson 6.8: `commands/thread_read.py` and `commands/thread_replay.py`; one turn's context by source, each source's tokens and rupees, lesson 6.1: `commands/context_sources.py`; what each model call is sent of a conversation, the whole thread or the window of `services/chat/context_window.py`, lesson 6.9: `commands/window_check.py`; all run in `~/graph-venv` by `commands/graph-venv.sh`) |
| `coding.mk` | `ralph-image`, `ralph`, `ralph-workspace`, `ralph-check`, `ralph-probe`, `review-diff`, `review-eval` | 10 Agents (coding agents, lesson 10.10: a Ralph loop on a copy of `shared/desk_calc.py`'s `statutory_deadline` under a strong and a weak oracle, `commands/ralph.py`, with its task, oracle, seeds and image in `commands/ralph/`; an AI code reviewer scored on six seeded defects, `commands/review_diff.py`; paper-to-code as the loop's `TASK=statute`) |
| `release.mk` | `ci-vars`, `keys-check`, `gate`, `promote-gated`, `smoke-deployed`, `incident` | 11 Project (the keyless pipeline's repository variables and the key check, lesson 11.1; the live gate bound to the exact candidate revision, and `make promote` only for the revision a green, fresh gate record names, lesson 11.2; the smokes of the services the lane has deployed, and a release incident's timeline with the gated state checked, lesson 11.3) |
| `capstone.mk` | `capstone-check`, `handover` | 11 Project (the capstone rubric's eight components checked in a fork, PASS or FAIL each and never a score, and the lane's operational handover written into it, lesson 11.8: `commands/capstone_check.py`, which reads and never changes the lane. Its own file, not `release.mk`: lessons 11.1-11.3 quote `release.mk` from their sections to its last line) |
| `operations.mk` | `gotchas`, `gotcha-drill`, `gotcha-detect` | 11 Project (production gotchas, lesson 11.7: the registry `ops/gotchas.json`, read and run by `commands/gotchas.py`; each offline drill on a stand-in of Cloud Run or the kit's own code at Rs 0, the two live drills and the detectors on the lane) |
| `casework.mk` | `case-check`, `case-eval`, `case-tests` | After Module 10 (the Case Room, Phase 0: thirty full and final cases, `evals/ff_cases.jsonl`, and the statutory floor under them, `shared/ff_floor.py`, drafted for the author's review and checked at Rs 0 by `evals/case_eval.py`, `REVIEW=1` printing them as markdown; Phase 1: the offline Case Room, `commands/case_room.py`, its three arms run and paired by `case-eval` in `~/graph-venv` through `commands/agent-turn.sh`, and its tests. Its own file: lessons quote `agents.mk` by line) |
| `operations.mk` | `remediate`, `incident-drill` | 10 Agent patterns (an incident's plan from rules, never a model, lesson 10.11: `commands/remediate.py` over `ops/runbooks.json`, the alert policies' runbook catalog, with recorded lane states in `ops/incidents/`; a fault held on documind-chat for it to diagnose, `commands/incident-drill.sh`). For documind-api it prints the Makefile's own `make rollback`, lesson 11.3's, rather than a second rollback |

The Makefile pins the default goal to `dryrun` (Tier A: offline, free), so a bare `make` never depends on which file
here sorts first. Still, always name the target. Five files add variables of their own: `agents.mk` declares `DESK_JOB`,
`CHAT_IMAGE`, `DESK_EVAL_SAS`, `DESK_ROUTER_ALERTS`, `DESK_GATE_ALERTS` and `GCHAT_DOOR`, and appends all but
`DESK_EVAL_SAS` to the Makefile's Terraform variable list (`TF_EXTRA_VARS +=`, which works because that list is a
recursive variable and the `include` comes after it); `retrieval.mk` declares `JEV_MODE` (`off`, `recorded` or
`live`; `off` by default) and passes it to `evals/decide.py` alone; `release.mk` declares `GATE_FILE`
(`evals/reports/gate.json`), the gate record `make gate` writes and `make promote-gated` reads; `managed.mk` declares `MANAGED_PEER_REGION`
(`REGION` by default), `MANAGED_PEER_GRANT_ROLE` and `AIPLATFORM_PIN` (empty by default: unpinned), which only its own
targets read. `coding.mk` declares `RALPH_IMAGE` (`documind-ralph`), the image `ralph-image` builds and the
live Ralph loop and `ralph-probe` run; `RALPH_EGRESS=proxy` on either (off unless given) holds the agent's container
to the model endpoint through a proxy run from the same image.

Three rules keep the files small:

1. **A target is a one-line entry.** A recipe longer than a few lines is a script under `commands/` (`ingest-one.sh`,
   `poison.sh`, `reindex.sh`, `wait-vectors.sh`, `vector-status.sh`, `limits-check.sh`, `limits-drill.sh`, `agent-drill.sh`, `handoff.sh`, `desk-check.sh`,
   `agent-turn.sh` with `agent_shapes.py`, `approval-check.sh`, `graph-venv.sh` with `thread_read.py`, `thread_replay.py`,
   `context_sources.py` and `window_check.py`, `remediate.py`, `incident-drill.sh`, `capstone_check.py`, `managed-peer.sh` with `managed_peer.py`) or a subcommand of `commands/lane.py` (`sources`, `queued`, `vector-status`, `backfill-vectors`, `roster`,
   `tenant-backend`, `tenant-policy`, `limits`), or of `commands/desk_ops.py` for the DocuMind Desk's targets
   (`doc-types`, `desk`, `roles`, `desk-queues`, `cases`, `route-index`, and `agent-actions`, which is `desk --actions`), or of `commands/release.py` for the release's
   (`ci-vars`, and `keys` for `keys-check`; `gate`, and `gate-check` before `promote-gated`'s `make promote`;
   `smoke-deployed`, which still needs `make` for the smokes it runs, and `incident`), or of `commands/ralph.py` for
   the coding agents' (`loop`, `workspace`, `check`, `probe`, with `commands/review_diff.py` for the reviewer's). The make target and the direct
   call run the same code, so a learner without `make` - Windows, Colab - runs
   `PROJECT=<id> TENANT=acme FILE=... bash commands/ingest-one.sh` or `python commands/lane.py sources`.
2. **The comment travels with the target.** The design notes that explained a target in the Makefile sit above it
   here, unchanged.
3. **A new module is a new file.** Add `mk/<lane>.mk`, list its targets in the Makefile's `.PHONY`, and give any
   long recipe a script, a `lane.py` subcommand or, for the Desk, a `desk_ops.py` subcommand first. Nothing else
   changes: `tools/check_*.py` read the Makefile and `mk/*.mk` as one text, and the publish (`tools/publish_learner.py`
   in the authoring repository) copies every tracked file under the kit.

Moved on 22 September 2026, with every target's name, comment and recipe kept byte for byte except the six that
became scripts and one comment that still said five delivery attempts (eventarc.tf says twelve); the scripts also fix a latent slip in the old recipes, where a `FILE=` or golden-set check that
failed inside `( ...; exit 1 )` did not stop the recipe.
