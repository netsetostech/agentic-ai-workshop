# Kit artifacts with no lesson behind them

Everything here is real, deployable, and **taught nowhere**. `extract_documind.py` reads the
Module 12 notebooks only, so these files are not regenerated from anything and
`extract --check` will never notice if they drift.

This file exists because that had already happened silently three times before anyone wrote it
down. When the owning lesson is authored, it must **adopt** the file — move it into the
notebook's heredoc and let the extractor own it — not write a second copy beside it.

Last reviewed: 2026-09-05 (twice: adoption, then an adversarial audit of the adoption).

## One shape, 2026-09-15 (the lean profile, 2026-09-06, superseded)

The lean | full profile switch is gone: every resource the full profile used to gate behind
`count = local.full ? 1 : 0` is declared unconditionally, and `variables.tf` carries `audit_lock`
and `gemini_quota_override` in its place. `terraform/gke.tf`, `terraform/spanner.tf`,
`terraform/gateway.tf` and `terraform/off.tf` stay unowned (the cluster is Terraform's now; the
night job no longer deletes it). The pieces the lane ran live are all owned: `variables.tf` and
`storage.tf` (12.1), `eventarc.tf`, the worker's `parser.py` / `contracts.py` / `main.py` and the
`documind-ingest` deploy command (12.5), `config.py` / `retriever.py` (12.2), `tenancy.py`'s
write side (12.8), `run_eval.py`'s outsider token (12.7). The `Makefile` is hand-written, as
before; `services/litellm/config.lean.yaml` was folded into the one `config.yaml`.

## Adopted since the last review

| File | Adopted by | What adoption changed |
|---|---|---|
| `terraform/wif.tf` | **12.7** | Now a heredoc in 12.7's notebook. Also repaired: the condition pinned only the MUTABLE `assertion.repository`, so a released repo name could be re-registered to satisfy it, and no branch was pinned at all. Now `repository_id` + `repository` + `refs/heads/main`, with the `principalSet` keyed on the immutable id. |
| `terraform/clouddeploy.tf` | **12.7** | Now a heredoc in 12.7's notebook, unchanged in content. It names `cicd` as the RENDER/DEPLOY/VERIFY execution account, which is what surfaced the missing execution roles in `sa.tf`. |
| `.github/workflows/documind-cd.yml` | **12.7** | Now a heredoc in 12.7's notebook — possible only because `dest_for()` grew a `.github/workflows/` destination; before that the heredoc was found, dropped, and `extract --check` stayed green. Still `workflow_dispatch` only, deliberately, and the header shows the `on:` block the application repo uses instead. Gained an `eval-gate` job, a staging-rollout wait, the live eval, and the promote-to-prod step. |
| `terraform/org_policy.tf` | **12.7** | NEW. `iam.disableServiceAccountKeyCreation`, gated behind `enforce_no_sa_keys` (default **false**, because organization policy needs the project to belong to an organization and a learner's throwaway project does not). `wif.tf` removes the *need* for a key; this removes the *ability* to create one. |
| `run-service.yaml` | **12.7** | NEW. The Cloud Run manifest `gcloud deploy releases create --from-run-manifest` renders. Without it the release is never cut: Cloud Deploy needs a skaffold configuration, this kit has none, and `--from-run-manifest` makes gcloud generate one. Deliberately has **no `traffic:` stanza** — Cloud Deploy owns traffic during a canary. `dest_for()` gained a `DEPLOY_ROOT_FILES` destination for it. |
| `evals/run_eval.py` | **12.7** | NEW, and the one file under `evals/` a lesson owns (`dest_for()` gained an `EVAL_FILES` destination for it). Implements the anchor-matching rule `evals/README.md` left open, and is wired into `make eval`, `make dryrun` and `documind-dryrun.yml`. The rest of `evals/` remains hand-written. |
| `cloudbuild.yaml` | **12.7** | NEW. Builds `rag-api` from the **`deploy/` context** (`docker build -f services/rag-api/Dockerfile .`) so the service can import `shared/`; `documind-cd.yml` runs it with `--config=cloudbuild.yaml` from `deploy/`. Routed by `DEPLOY_ROOT_FILES`. |
| `shared/documind_schemas.py` | **12.2** | NEW. The answer contract — `Citation`, `RAGAnswer`, `DraftCitation`, `ModelDraft`, `resolve()` — as a heredoc in 12.2's notebook, routed by `SHARED_FILES`. `services/rag-api/schemas.py` imports it and adds only the transport envelope `RAGResponse(RAGAnswer)`. 3.2, 4.2, 4.5 and 4.6 paste the class text verbatim; `tools/check_contract.py` proves containment. No `from __future__ import annotations` — the text is exec'd as a notebook cell, where a deferred `List` never resolves. |
| `terraform/cloudsql.tf` | **12.8** | NEW (gap G5). The chat checkpointer's Cloud SQL (`db-f1-micro`, zonal, `deletion_protection = false`), a `random_password` that lives only in state and Secret Manager, the `documind-checkpoint-dsn` secret in 8.5's DSN shape, `secretAccessor` + `cloudsql.client` for `documind-chat-sa` (which `sa.tf`, 12.1, now defines — the service had no account). Needs the `random` provider `backend.tf` now declares. |
| `services/chat/brains.py` | **12.8** | NEW (gap G6). Four brains over the one `tools.py` — langchain, langgraph (with a refuse node), adk, direct — `DOCUMIND_BRAIN` default, `brain` per request; every usage row names the brain. `commands/tests/test_chat_brains.py` proves offline that every agent brain reports its own turn's tool calls, refusals and numbered citations, that the three bind one tool list, and that one error contract holds in all three (workshop lessons 10.1 to 10.4). |
| 12.8 `DEPLOY` (→ `commands/lesson-12.8.sh`) | **12.8** | NEW. The chat service's deploy command, which never existed: build from the shared `cloudbuild.yaml` (`_DOCKERFILE`), `--add-cloudsql-instances`, `--set-secrets=CHECKPOINT_DSN`, both IAP audiences, the one-off `documind-checkpoint-setup` job (`migrate.py`), then `--iap`. In `make deploy-services`. |
| `terraform/dataplex.tf` + `terraform/sql/chunk_metadata.sql` | **12.3** | NEW (gap G9). Module 5's production lane: the `rag_data` dataset (5.5's own name, so its SQL runs unchanged), four declared tables, the three-rule Dataplex scan on `index_feed`; the SQL is the feature job (`make features`). `services/ingest/indexer.py` streams `chunk_source` rows with the worker's own `pii_flag` when `BQ_CHUNK_TABLE` is set. `evals/make_evalset.py` (unowned, live) writes PII-scanned eval *candidates* — `run_eval.py` never reads them. Also found: `sql/tenant_daily.sql` was applied by nothing; `make bq-views` (in `make up`) now applies it. |
| `services/rag-api/media.py` | **12.2** | NEW (gap G8). 9.4's Media Studio router, which 9.4 wrote *"so 12.x can adopt it"* and nothing did — now with the tenant roster check and an `event=media` usage row in `tenant_daily`'s shape; 9.4's cell 25 is the same text. Needs the `-media` bucket `storage.tf` (12.1) now provisions and the `media.*` actions `shared/audit_log.py` now registers. Also fixed on the way: `services/ingest/main.py` called `_parse`, `_chunk` and `_enqueue_batch` and none existed anywhere — every message would have raised `NameError`. |

`sa.tf` was already owned by 12.1 and is not listed above, but 12.7 changed it: `roles/iam.serviceAccountUser` was granted at **project** scope, which is actAs on every service account in the project including future ones — so with `cloudbuild.builds.editor` the deploy identity could submit a build as `documind-api-sa` and read Secret Manager, Firestore and BigQuery. It is now granted per service account, as a **static-keyed map** (`for_each` over computed `google_service_account.*.name` fails `terraform plan` outright: "The keys of the map or all values in a set of strings must be known values"), covering the four runtime identities **and `cicd` itself** — Cloud Deploy requires actAs on its own execution account. Two missing execution roles were added, `clouddeploy.jobRunner` and `run.developer`; the first repair also added `storage.objectAdmin` and `logging.logWriter`, and **both were removed again** — Google's documented set is three roles, jobRunner already carries the bucket access, and objectAdmin at project scope reaches the customer-document and retention-locked audit buckets. Over-granting inside the lesson about blast radius is the defect that reviews it.

---

## Stood up for the masterclass, ahead of their lessons

The Flagship Plan's P1 rows are *"stand-up/verification only — build hours sit in the Phase 1
roadmap"*. The 12–26 September demos need infrastructure that exists; the lessons that teach it
are authored in November and December.
Every Cohort 2 page has landed: `terraform/spanner.tf` is quoted by 0.1, 0.3, 0.4 and 7.2, `terraform/gke.tf` by 0.1,
0.3 and 0.4 and `gke/` by 0.3 and 9.3, and `services/slm/` by 9.2 and 9.4, so their rows moved to INDEX.md (13 October
2026).

## The judge against people (lesson 4.5)

Kit files PR W2-E adds that no page quotes yet, with `evals/judge.py`'s two new flags, `--save-rows` and
`--no-enrich` (the lines after its by-shape block, which no page quotes). Lesson 4.5's page adopts them; the page pull
request removes the rows it adopts. The set's data files arrive with the author's runs: the capture in batch 1, the
labels in batch 2.
Lesson 4.5's page quotes `evals/agreement.py`, `evals/build_judge_set.py`, `evals/judge_agree.py` and
`evals/tests/test_judge_rows.py`, so their rows moved to INDEX.md (12 October 2026).
Lesson 4.5's page quotes `mk/evaluation.mk`, so its row moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/tests/test_agreement.py` | **4.5** | Stdlib: the worked table's 0.40 and a second table by hand, all agree, no variance (undefined), one reader without variance (0), opposite constants, -1, a three-class set, no rows; the 2x2, the two rates and route_eval's Wilson; judge_agree's cut and sweep arithmetic. |
| `evals/tests/judge_fixtures/` (`capture.ndjson`, `judge_set.json`, `ratings.ndjson`, `labels.FX1.csv`, `labels.FX2.csv`) | **4.5** | Synthetic, for the tests only: a made-up twelve-row capture (questions and context marked "fixture"), what `--freeze --rows 9` makes of it, the tests' stand-in judge's ratings of that set through `judge.py`'s own path, and two made-up readers, FX1 and FX2. `test_judge_rows.py` holds each one to the code that makes it. The two JSON Lines files are named `.ndjson`, the format's other name, so lesson B.1's count of the kit's `.jsonl` datasets stays a count of datasets. |
| `evals/judge_set.json`, `evals/judge_set.ratings.jsonl`, `evals/judge_labels.L1.csv`, `evals/judge_labels.L2.csv` | **4.5** | Absent by design: none is invented. The author freezes the set from batch 1's capture (`make judge ... JUDGE_ARGS="--reuse ... --save-rows ..."`, then `build_judge_set.py --freeze`) and rates it once (`make judge-frozen RUN=evals/judge_set.ratings.jsonl`); in batch 2 the author (L1) and one peer (L2) each label the rows once (`make label-sheet READER=L1 LABELS=evals/judge_labels.L1.csv`, then `--check`). Until then `make judge-frozen` refuses and `judge_agree.py` says which file is missing. |

## Read the failures, then attack the pipeline (lesson 4.9)

Kit files PR W2-F+G adds that no page quotes yet, with three targets appended to `mk/evaluation.mk`. Lesson 4.9's page
adopts them; the page pull request removes the rows it adopts. The attack set and its runner carry uplift task F10's
file names, so lesson 10.8 (its PR 10.8-C) adds its rows, doors and controls here instead of building a second runner.
Nothing under `services/` changed.
Lesson 4.9's page quotes `evals/triage.py` and `evals/run_attacks.py`, so their rows moved to INDEX.md (12 October
2026).
Lesson 4.9's page quotes `mk/evaluation.mk`'s `triage`, `attack-offline` and `attack-eval` targets, so their row moved
to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/adversarial/attacks.jsonl` | **4.9** (10.8 adds rows) | Fifteen rows on acme, all on rag-api's surface: lesson 4.8's four probes (the plain question, the English and the Hinglish injections, the synthetic PAN) as rows 1 to 4; an override riding on the plain question (11 days, in no corpus) and a refusal bait on golden rf-01's sabbatical; acme asking for Globex's agreement at `/v1/query`, `/v1/passages` and `/v1/stream` (120 days and 99.0% are Globex's alone); the outsider at all three doors; a body filter naming `tenant_id` at `/v1/query` and `/v1/passages`; the outsider's token with x-user-email naming the member. One plain row, five behavioural (Model Armor and SYSTEM's rules hold them), nine structural, each naming the one control that holds it (roster, iap_identity, filter_check or tenant_filter). No question fires the Desk's gate or is masked (`commands/tests/test_desk_rules.py` reads this file). Lesson B.1 counts it among the kit's JSONL files and their lines, so a row added here moves B.1's line count. Gap task S8's Hinglish and Devanagari rows wait for a fluent writer; the vendor note's indirect injection is lesson 10.8's. |
| `evals/tests/test_triage.py` | **4.9** | Stdlib. Reports written by `run_eval.live()` itself over a stub, as `test_eval_rows.py` runs it, with `DOCUMIND_EVAL_PASSAGES=1` and the kit's chunker's passages, and once without: exactly the failing rows and the outsider's leg; the kit's reading of each (every cause but row, and an isolation hidden behind a later verdict); no reading of retrieval or omission without the pool; the open-coding view naming no cause; the template, and its refusal to overwrite; the eight causes printed; labels counted with their agreement, and each refusal; two reports; the lessons named in `course-manifest.json` (skipped in a learner's clone). |
| `evals/tests/test_attacks.py` | **4.9** | Stdlib. The committed set sound and its shape (every door, attack, control and caller used; 4.8's probes as rows 1 to 4); every way `check_set()` refuses a row; no question firing the Desk gate or masked; the stand-in's functions the kit's own, and `main.py`'s three handlers calling them in the stand-in's order; the rows each control opens alone, and the leak with filter_check and tenant_filter both off; every outcome a reply can be read as, the eight-word prompt run, a leak in the stream's citations before its screen; the live path over a local HTTP server serving the stand-in (the same outcomes, no token in the report, the refusal without the outsider's token, a hole failing the run, `--compare`); one retry for a blip and none for a verdict; the targets, `.PHONY`, the 888 lines and these rows. |

## Prompt versions (lesson 3.6)

Kit files the prompt-versions pull request adds that no page quotes yet. Lesson 3.6's page adopts them; the page pull
request removes the rows it adopts.
Lesson 3.6's page quotes `services/rag-api/prompt_versions.json`, `commands/prompt_pin.py`,
`commands/tests/test_prompt_versions.py` and `mk/generation.mk`, so their rows moved to INDEX.md (12 October 2026).

## DocuMind Desk (lessons 5.6, 10.4)

Kit files the Desk's pull requests add that no page quotes yet. Lesson 5.6's page adopted the gate, the fixed
replies, both doors, the roles, the case queue, the Desk page, the overdue job and `terraform/desk.tf`. Lesson
10.4's page adopted the class registry, the relabel, the route table, the router and the desk graph, and of the
Google Chat door the Desk's delegation rules, the bridge's token check, its cards, its claims and its deploy
block. The page pull requests remove the rows they adopt.
Lesson 5.8's page quotes `mk/agents.mk` (so do 0.3, 3.2, 10.1-10.3, 10.5 and 10.8), so its two rows moved to INDEX.md
(13 October 2026).
Every Cohort 2 page has landed. Lessons 5.6 and 10.4 name these files without quoting them, and other pages quote
them: `commands/desk_ops.py` (3.9), `evals/route_eval.py` (3.2, 10.5), `shared/desk_calc.py` (10.1, 10.3, 10.5, 10.8,
10.10), `services/chat/desk_agent.py` (6.1, 10.1, 10.3, 10.5, 10.8), `commands/tests/test_desk.py` (10.5),
`terraform/desk_alerts.tf` (4.3, 10.11) and `terraform/gchat.tf` (8.1), so their rows moved to INDEX.md (13 October
2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `shared/desk_recall.py` | **5.6** | The model check behind the hard gate's rules, for a tenant whose `desk_gate` is `on`: `gemini-3.1-flash-lite` on `global`, enum-only JSON (`case`: a gate class or `none`), thinking budget 0, one attempt, `CHECK_TIMEOUT_S`; it reads the masked question, prompted to choose a class when the writer may be describing their own situation, and a failure is no class. `row()` is the `desk_gate_check` line (outcome, tokens, cost; no question, no person, no class). `OnTenants` is the doors' tenants-on set, one bounded query (`READ_TIMEOUT_S`, no retry) at most once a minute, one reader at a time, claimed on the event loop by `tenants()`, which both doors await; the chat service's shadow keeps a second one (`SHADOWING`, the tenants in shadow, read with `asyncio.to_thread`; `event=` names its failure line `desk_shadow_tenants_unread`, which nothing pages). Called by both doors (`services/chat/desk.py` `_check`, rag-api's `main.py` install line, which 5.6 quotes); lesson 5.6's prose names it and quotes none of it. Offline tests in `commands/tests/test_desk_rules.py` (`DeskRecallTests`). |
| `commands/tests/test_doc_types.py` | **10.4** | Stdlib, with a fake Firestore: the media parent map, the pin miss, the second plan, the reset round trip, current rows only into `_repair_snapshots`, retired versions by the pin rule, a failed version, a repair that fails after its first group, and a swap during the upsert, the exit on a deferred BigQuery statement, the Vertex AI Search and BigQuery calls against stand-ins, the export `route_eval.py` reads, the hook's place before `index_document`'s `try`. |
| `evals/routes.jsonl` | **10.4** | The route set: 207 dev rows relabelled from golden, the paraphrases and 100 first-person rewrites of SFT user turns, every label and rewrite a model draft until a person reviews it. People write the further dev rows, then the test split. |
| `evals/build_routes.py` | **10.4** | Builds the 207 rows and validates the hand-written ones; `--check` fails on a golden row with no label, a label the handbook/statute labelling rule contradicts, a rewrite outcome not judged on the corpus, a paraphrase guard that is not another tenant's figure, or a stale file. |
| `evals/route_probe.py` | **10.4** | The router's probe: top-two logprobs, thinking budget 0, the schema's output tokens, flash at MINIMAL; `--dry-run` and `--selftest` offline. |
| `evals/tests/test_route_eval.py` | **10.4** | Their offline tests, including lesson 10.4's Wilson figures and a check that the eval's class list and media rule are the registry's. |

| `shared/identifiers.py` | **5.6** | Aadhaar (12 digits, first 2-9, Verhoeff), card numbers (13-19 digits, a payment network's first digit, Luhn), PAN and GSTIN (mod-36 check). A number may be typed with any spaces, dots, slashes or dashes, and in Devanagari or full-width digits. The gateway's classifier keeps its own regexes (its image cannot import `shared/`). |
| `commands/tests/test_desk_rules.py` | **5.6** | Stdlib: 0 fires on the 424 existing questions and the route rows, 0 fires and 0 masks on the smoke and demo questions (but `smoke_cases.py`'s one POSH disclosure, sent on purpose, which must fire posh), the model-written positive and negative examples per class, the Verhoeff, Luhn and GSTIN vectors, the escalation rows of `evals/routes.jsonl` (skipped while there are none), and the door against a fake app in plain asyncio: the three gate states (`gate_state`, `True` and `False` included; a failed read is `rules`), and the model check (on only, `/v1/query` and `/v1/stream` with no brain label or `ui`, a failed check is no class). `DeskRecallTests`: the fenced prompt, the enum-only one-attempt request, the row with no question, person or class, and `OnTenants`' one bounded reader, through the door, released however its turn ends. |
| `evals/desk/queues.acme.json`, `queues.zeta.json`, `queues.globex.json` | **5.6** | The synthetic tenants' case queues for `make desk-queues`: acme's units hyderabad and pune (`acme/townhall_2026_q1.md:7`), zeta's and globex's one placeholder unit; every contact an `example.com` placeholder, every `sla_days` the company's own target, set by the author. |
| `evals/desk/clause_notes.acme.json` | **10.4** | acme's notes on two handbook clauses for `make desk NOTES=`: LV-01 (`acme/hr_policy_2026.md:19-20`) against the OSH Code s.32(1)(vii) to (ix) (`acme/osh_code_2020.md:1550-1562`: carry forward up to 30 days, refused leave without limit, encashment at the year's end and above 30 days) and LV-07 (`:24-25`) against s.32(1)(vi) (`:1537-1548`: wages in lieu of leave on leaving, before the second working day), each ending "The OSH Code gives workers these rights; whether they apply to your role is a question for the People team." (the Code's worker, s.2(1)(zzl), `:663-676`, leaves out managerial roles). `test_desk.py` holds each phrase to the corpus lines. |
| `smoke/smoke_cases.py` | **5.6** | `make smoke-cases`: the POSH disclosure through `/v1/chat` (documind-evalacme-sa) and `/v1/stream` (ui-sa) with model none and cost 0; a grievance drafted, confirmed twice with one token, in documind-evalgrc-sa's inbox, acknowledged and closed; documind-evalzeta-sa's 404; a POSH press twice with one token naming `IC_EMAIL` (one case, no text), then withdrawn; the outsider's 403. |
| `smoke/smoke_desk.py` | **10.4** | `make smoke-desk`: the routed Desk as the eval accounts, its questions read from `evals/routes.jsonl` by id: a handbook answer citing acme's own objects with the row's figure (lk-06), a statute answer with its in-force lines (lk-16), a POSH disclosure answered by rule with the POSH card, no model call and no case written, an invoice question out of scope by its anchor (lk-10), the leaver's denied turn with no retrieval, globex in single mode (lk-28), `/v1/route` as documind-evalacme-sa and its 403 for ui-sa; then `smoke_cases.py`'s `main()`. |
| `commands/tests/test_cases.py` | **5.6** | A stdlib half (roles, cases, the queue files, the case table against the corpus and the manifest, the wiring, `desk_ops.py`, including the gate needing no queue and the POSH rule while the routed Desk is on or single, with a fake Firestore and a fake audit bucket) and a chat-pins half (the door against a fake app - the rules by default, the model check for a tenant whose gate is on, the local profile's rules - the real chat service: identical bytes for a refused caller on a hit and a miss, no model call and no checkpoint on a gated turn; the case routes). CI's chat-pins step and `make desk-check` run it with `DOCUMIND_REQUIRE_LIBS=1`. |
| `evals/route_threshold.py` | **10.4** | The sweep of `TAU_OOS` and `ACCEPT_VOTES` on the dev split, as `cache_threshold.py` sweeps the cache's: accepted accuracy, L1 errors sent to L2 and the L2 share per pair, and the pair that meets 98%, 70% and 15%; it writes nothing. `--selftest`, `--local` (scripted, shows the sweep works), `--project` (about 200 flash-lite calls and embeddings), `--signals`. `make route-calibrate`. |
| `terraform/sql/desk_daily.sql` | **10.4** (11.5 names it) | The Desk's day, `make desk-views`: per India day, tenant, desk (the route, or the routed desk of a denied or not_covered turn) and `callers` (people, or service_accounts: the eval accounts and every arm but B), from surface `desk` rows only. Turns, answered, refused, clarified, denied, not_covered, out_of_scope; escalations by type with posh, grievance and privacy_request as one `escalated_sensitive` count, and draft turns apart; the method mix; `to_l2` and `l2_share`; `chip_turns` and `chip_rate`; `cost_inr` (model plus rag-api at 85, the rag part also on rag-api's own rows) and `model_cost_inr`; p50 and p95 of latency and `router_ms`. No user or session column, no join. desk, case_type, accepted_by and chip are read from the row's JSON, so a lane where nobody has pressed a chip still gets the view; the rest are read directly, so a sink that has seen no desk row refuses it. A sensitive turn names nobody, so an eval account's (the smoke's POSH turn) counts as people. |
| `commands/tests/test_desk_operations.py` | **10.4** | Stdlib: the sink's Desk events against the lines the kit writes, `desk_gate` from `documind-chat` only and no sensitive `desk_shadow` row (each would sit beside its turn's `chat` row), and the chat door's gate hit answering before `chat()` runs; `desk_daily.sql` against the desk row literal, `desk_graph`'s outcomes, `desk_router.METHODS`, the case table and `USD_INR`, with no person column and no join; the metrics' labels (no person, case or text), every policy reading a metric the file declares and paging `local.alert_channel_ids`, the router's three behind `desk_router_alerts` and the gate check's share behind `desk_gate_alerts`, the gate check's two metrics against `desk_recall`'s lines and both doors' log calls, the thresholds and floors (the L2 cap is `route_threshold.py`'s), the PromQL rendered and balanced, the overdue and pin-miss filters against `desk.tf`, `batch.tf` and the log lines; `make desk-views`, `DESK_ROUTER_ALERTS` and `DESK_GATE_ALERTS`. |
| `services/gchat/` (`events.py`, `replies.py`, `post.py`, `requirements.txt`, `Dockerfile`) | **10.4** | The bridge's other files; lesson 10.4 quotes `main.py`'s token check (`expected_caller()`, `verify()`), `cards.render()` and `claims.take()`. `events.py`: both event shapes (`events.normalise`), the session id (`gc-`, 24 hex digits of the space's hash and the India day), the claim keys and the `client-` message id, and `is_person`, the Desk's own pattern, so a sender the Desk would not take as one person's address is "could not read your account" with no Desk call. `replies.py`: the fixed replies, equal to the Desk's denials where they answer one, the welcome card and the add-on reply wrapper (`wrap`). `post.py`: `spaces.messages.create` under a `client-` id and Pub/Sub's publish, over REST through google-auth, so the bridge pins only the chat service's own versions; a post no credential may make is not retried. Every path a read page did not state is one named function or constant marked UNCONFIRMED until the lane probe's `gchat_probe` row (`events.py`'s event paths, `post.auth_order`, `post.DUPLICATE_STATUS`); `main.py`'s `GCHAT_ASYNC = False` is the sync-only fallback if the app cannot post. |
| `smoke/smoke_gchat.py` | **10.4** | `make smoke-gchat`: `POST /` and `POST /work` as the outsider are the code's 401; `POST /v1/desk` with the header as documind-evalacme-sa and as ui-sa is the 403 "not an allowed delegate" (the refused-delegation alert's own test); then the latest rows. No question it sends fires the gate. |
| `commands/tests/test_gchat.py` | **10.4** | A stdlib half (both event shapes from placeholder fixtures, which may hold no email outside `example.com` and no run of ten digits; the session id; the keys and the `client-` id; `render()` for every Desk outcome; the fixed replies equal to the Desk's denials; `post.py` against a stand-in session, a post no credential may make not retried; `claims.py` itself on a transactional stand-in, the stale claim and lease taken back, "busy", attempts counted across release, `expire_at` kept; the wiring and the pins; `make desk DESK_GCHAT`) and a chat-pins half (the bridge's handlers with fakes: the token first, the gate before everything, the queue, the presses, the worker's retries and fifth attempt, the token before the body, sync-only mode, the real claims holding no text and no email; and `delegation.principal()` on `agent.py`'s app, every rule and which row it writes). CI's chat-pins step and `make desk-check` run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Query rewrite (lesson 2.5)

Kit files that the query-rewrite pull request (the cohort plan's 2.5-A) adds and no page quotes yet. Lesson 2.5's page
adopts them, and its pull request removes the rows it adopts. The stage is off on every lane (`QUERY_REWRITE=off`), so
until a revision turns it on, these files change nothing a learner sees.
Lesson 2.5's page (#110) quotes the stage's two files, so their rows moved to INDEX.md (12 October 2026); the
test is quoted by no page yet.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/tests/test_query_rewrite.py` | **2.5** | Stdlib: the guard on the design's examples and the golden rows, the outcomes, the request (and, where google-genai is installed, against its `GenerateContentConfig`), the cost arithmetic, the line with no question text, `search_query()` lifted from `rewrite.py` (off makes no call), and `evals/ablate.py`'s rewrite arm (`--rewrite`), paraphrase rows (`--paraphrases`) and `main()` against a stand-in lane. `tools/check_retrieval.py` runs the stage through `main.py`'s lifted `/v1/query`. |

## Answer or refuse (lesson 2.6)

Kit files PR 2.6-B adds that no page quotes yet. Lesson 2.6's page adopts them; the page pull request removes the rows
it adopts. PR 2.6-C, once TypeSafe's docs, a key and its terms arrive, fills the adapter seam in `shared/system_one.py`.
Lesson 2.6's page (#114) quotes `shared/system_one.py`, `evals/decide.py` and `mk/retrieval.mk`, so their rows
moved to INDEX.md (12 October 2026); the test and the absent recording are quoted by no page.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/system_one/recorded.jsonl` | **2.6** | Absent by design. No recording ships until decisions are recorded against TypeSafe's API, none is ever written by hand, and whether recordings may be published is one of TypeSafe's terms (the lesson plan's decision 5). While it is absent every recorded row is skipped with that reason and `decide.py` prints the file's absence. A line is `recording()`'s shape, held by `recording_errors()`: the row id, tenant, verdict, score, model, the vendor's `request_id`, `recorded_at`, `ms`, `tokens` and the pool's `chunk_ids` (a recording made on another pool says so). |
| `evals/tests/test_decide.py` | **2.6** | Stdlib (a stand-in for `requests` when it is missing): off makes no call and reads no file; recorded opens no socket and reads no policy; an absent file skips every row, a malformed or second line is an error, and an invented recording fails; an `in`, unknown, missing or unreadable policy is never sent; live is "TypeSafe adapter not configured (PR 2.6-C)" until PR 2.6-C; identifiers are masked before the transport, which sees only the question and the passages' text; a failed call is an error, never a refusal; the price is TypeSafe's; the confusion matrix, Wilson, kappa, Brier and the bins on a fixture; the Rs 0 lane on globex end to end and its replay (a local run's pool never meets the lane's generator); the lane client (the API and documind-ui-sa from the project, one token a run, a failed mint stops the run, a reply that is not JSON is an error row); a live run against a stand-in lane sends acme's and zeta's 55 non-empty pools and none of globex's 8; the make target and these rows. |

## The prompt bench and the router's examples (lessons 3.1, 3.2 and 3.3)

Kit files PR W2-B+C adds that no page quotes yet (wave 2 of `plan/cohort-2-lesson-plan-2026-10-07.md`, on W2-A's
`run_eval.py` helpers). Lessons 3.1-3.3 adopt them; the page pull requests remove the rows they adopt.
`services/rag-api/generator.py` is not changed: the bench edits its `SYSTEM` in memory only.
Lesson 3.1's page quotes `evals/prompt_bench.py` and `mk/generation.mk`, so their rows moved to INDEX.md (13 October
2026).
Lesson 3.2's page quotes `evals/route_eval.py`'s `--exemplars` and `mk/agents.mk`'s `exemplars` target, so their row
moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/tests/test_prompt_bench.py` | **3.1, 3.2, 3.3** | Stdlib and pydantic: `generator.py` lifted with ast as `tools/check_retrieval.py` lifts it, over a scripted model and a stand-in lane, on the handbook as the kit's chunker cuts it. One pool read a row before any answer, the same context in every request; the prompt `generate()` builds from a pool; the level and temperature sent and every other config field as `generator._call` builds it (the kit arm at LOW equal to the API's own request), thought tokens apart; the same on google-genai's own types (skipped without the library, a failure with `DOCUMIND_REQUIRE_LIBS=1`); a rule dropped and one added in the edit arm's prompt only, each arm's prompt sha256, `generator.py`'s bytes unchanged and `SYSTEM` and `_client` put back even when the run fails; a report's failing rows with the refusal rows, and the rows, levels, rule numbers, reports and tuned endpoints refused; a row with no pool or an empty one not benched; the gate's verdicts (a wrong figure, an answer that should refuse, a retired version, quotes own, elsewhere and absent); an answer cut off twice is a 502 with both calls billed; a 429 on the model asked falls back to the default and says so; distinct answers and citation sets; the rupees at list price; the make target and these rows. |
| `evals/tests/test_route_exemplars.py` | **3.2** | Stdlib: the counts on the committed set (187 scored, 20 left out); kit, none and a file, and a file's refusals; only `desk_router`'s tuple swapped, the L1 prompt with and without its examples, `prompt_groups()` unchanged, the kit's tuple back after a failure; `l1_alone()` on built decisions; a run on a small route set printing the two lines only with `--exemplars`, and the report's keys only then; the refusals without `--local` or `--live-l1`; the make target in `agents.mk`. Not in `make desk-check`, which runs `test_route_eval.py` alone. |

## The agent bench (lessons 10.1-10.3, 10.5)

The shared kit under the Module 10 pattern lessons: one task set, one recorder and one scorer, so the patterns those
lessons add (`react_text`, `plan_first`, `plan_execute`, `rewoo`, `verify`, each in its lesson's pull request) are
compared on the same rows, tools and limits. Nothing in `services/chat` changes; the pages that adopt these files remove
their rows. Lesson 10.2's pull request adds `plan_execute`, `rewoo`, the chained rows and `commands/tests/test_agent_plans.py`;
lesson 10.3's adds `verify`, the figure check best-of shares, the side-by-side report and `commands/tests/test_agent_verify.py`.
Lesson 10.3's page quotes `commands/tests/test_agent_verify.py`, so its row moved to INDEX.md (13 October 2026).
Lesson 10.2's page quotes `commands/tests/test_agent_plans.py`, so its row moved to INDEX.md (13 October 2026).
Lessons 10.1 to 10.3 quote `commands/agent_patterns.py` and `evals/agent_eval.py`, lessons 10.2 and 10.3
`commands/agent_turn.py`, and lesson 10.5 `evals/paired.py`, so their rows moved to INDEX.md (13 October 2026);
`commands/agent-turn.sh`, which no page quotes, keeps a row of its own.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/agent-turn.sh` | **10.1-10.3, 10.5** | The script `make agent-turn` runs, around `commands/agent_turn.py`: `OFFLINE=1` (scripted, Rs 0) or a lane turn (`--live`: `GOOGLE_CLOUD_PROJECT`, `RAG_API_URL` from the project number, `DOCUMIND_IMPERSONATE_SA=documind-ui-sa`). It makes `~/graph-venv` as `limits-check.sh` does and, given arguments, runs them in that venv and environment (`make agent-eval`, `make agent-tests`). |
| `evals/agent_tasks.jsonl` | **10.1-10.3, 10.5** | 21 model-written rows, acme's and one of zeta's: 11 calculator rows covering all seven calculators (gratuity at 7 years 8 months, Rs 52,000: Rs 2,40,000; at 7 years 6 months; fixed term; acme's and zeta's carry-forward; an invented cap; accrual; two notice dates; wages due; the GRC threshold), 5 single-hop lookups (golden lk-03, lk-04, lk-06, lk-07, lk-16), the provenance trap (50 days encashed: 45, which LV-07 also writes), a refusal (no years of service), and lesson 10.2's 3 chained rows (`kind` chained, desk astar, `parts`): the notice end, the leave encashed and the gratuity in one question (4 December 2026, 45 days, Rs 2,40,000; Saturday 5 December, 45, Rs 2,10,000; and the first with a manager's cap of 100 the question states, `stated`, which check_args refuses). No figure feeds another calculator: check_args takes a calculator's inputs from the question or a clause only. Each row carries its expected figure, its clause, the figures a right answer never states and the scripted model's search words. People write the held-out split. |
| `commands/tests/test_agent_bench.py` | **10.1-10.3, 10.5** | A stdlib half (the wiring: targets, `.PHONY`, `mk/README.md`, the targets after every Desk recipe, the CI lines, these rows; the recorder's arithmetic; the corpus store; the slip schedule) and a chat-pins half (the loop on the scripted model over the corpus, held equal to `desk_agent.run()`; the context's keys; the recorder inside the limits, adding no node; thinking sent per call; the turn's limits; an invented cap refused; the corpus with no network; `agent_turn.py` and `agent_eval.py` offline end to end, with save, replay and best-of). CI's chat-pins steps and `make agent-tests` run it with `DOCUMIND_REQUIRE_LIBS=1`. |
| `commands/tests/test_agent_patterns.py` | **10.1** | A stdlib half (`read_step()` on every form a reply takes, the cut one marked line, the registry, the CI lines, `make agent-tests`, this row) and a chat-pins half: `react_text` on the scripted text model, with the gap plan's P1 cases (an Action run through `ToolNode` and its value the next Observation, an invented wage refused as an Observation, a malformed Action answered with a format Observation and then corrected, an invented `Observation: Rs 2,50,000` cut, a loop stopped at the call cap, no function declaration sent), the timed wrapper, the loop's wrappers at the model call, the stop sequence, the Change-it (the cut deleted in memory, and `unsupported()` flagging Rs 2,50,000) and thinking per call; `plan_first` (the instruction, the loop's own middleware, tools and graph, the plan written and the loop still deciding); `agent_turn.py` and `agent_eval.py` with both. CI's chat-pins steps and `make agent-tests` run it with `DOCUMIND_REQUIRE_LIBS=1`. |
| `evals/tests/test_paired.py`, `evals/tests/test_agent_eval.py` | **10.1-10.3, 10.5** | Stdlib: the interval, the test and the margin; the task set's check and the cases it refuses, the scorer, pass@k and pass^k, best-of, replay and compare on saved records; a chained row's check, its refusals and its score (10.2); best-of by the figure check (a cited passage never read, a stop, a failed run), an arm with too few runs, replay of several saves, and the side-by-side on hand-written verify records (10.3). |

## Run a desk as an agent (lesson 10.5)

Kit files lesson 10.5's kit pull request (K-10.5) adds that no page quotes yet. All of it is client side: nothing in
`services/` changes, so a lane needs no redeploy. Lesson 10.5's page adopts them; the page pull request removes the
rows it adopts.
Lesson 10.5's page quotes `evals/combine.py`, so its row moved to INDEX.md (13 October 2026).
Lesson 10.5's page quotes `evals/route_eval.py`'s `--compare` and the kept turn, and `mk/agents.mk`'s `route-compare`,
`arms-combine` and `ROUTES`, so their row moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/route_arms.jsonl` | **10.5** | The arms set: 12 dev rows in the route set's schema, for `make route-eval ROUTES=evals/route_arms.jsonl`. Five new rows, model drafts (`source` new): fig-01 (gratuity on Rs 52,000 a month after 7 years 8 months: Rs 2,40,000), fig-02 (7 years 6 months: Rs 2,10,000, six months not being over six), fig-03 (notice acknowledged on 5 October 2026, NP-03's 60 days: 2026-12-04, the date as the calculator writes it), fig-05 (zeta, 34 days and LV-01's cap of 18: 18 carried, 16 lapse; acme's 30 would give 30 and 4) and fig-06 (3 years 2 months: no figure, under s.53(1)'s five years; `must_not_contain` 90,000, the sum that ignores them). The statute rows name the Code, so `build_routes.py`'s labelling rule labels them statute, and every fig row is in the first person, so on arm B no anchor decides it at Rs 0: L1 is asked, and its `needs_calculation` is what sends B to agent mode. fig-04, the notice-and-wages chain across two desks (uplift A8), waits for its chain edge (A1). Then seven rows of `evals/routes.jsonl` as they stand: jn-03 (45 and 60; LV-07 writes 45 too, the provenance trap) and the lookups lk-01, lk-04, lk-06, lk-07, lk-17 and iso-01 (zeta's 25,000, with acme's 40,000 refused). No row is in a group of the router's prompt examples, so `--live` scores all 12; the seven are in B's exemplar index (an upper bound for B on them), the five fig rows are not. |
| `evals/tests/test_route_arms.py` | **10.5** | Stdlib. Every figure of the arms set recomputed: each calculator call through `check_args` on the row's question and the tenant's chunk of its clause, then `calculate()`; each lookup figure in its clause or the Code's line; every `must_contain` accounted for; fig-01 to fig-05 each ask for a figure in neither the question nor what the calculation reads; fig-06's missing figure and its guard, fig-05's zeta cap against acme's, jn-03's trap, iso-01's guard. The rows: the route schema, the copies equal to `routes.jsonl`'s and in B's index, the new rows in neither, no prompt-example group, the labelling rule, the gate and the mask, and arm B asking L1 on every figure row (the router in process, scripted). What `--live` keeps and `--report` adds; a live run of B, C and Astar against a stand-in chat service end to end (the saves, the reports, `--compare` against `paired.py`'s own arithmetic, `combine.py`); `--compare`'s refusals; the targets, line 214, the 888 lines, these rows. Not in `--selftest` or `make desk-check`. |
| `evals/tests/test_combine.py` | **10.5** | Stdlib: `vote()` (the most-made proposal, a tie, no proposal, a member with no calculation), proposals read from a run's sections, `invented()` (a model's figure, a cited one, an in-force date), a combine over saved runs with a tie (its agreement buckets, the vote's counts, the abstention, the flagged figures), the selftest at one, two and three layers (Rs 2,25,000 flagged at every layer, the abstaining split, the calls each combiner adds), its refusals and the make target. |

## A person in the loop (lesson 5.8)

Kit files lesson 5.8's kit pull requests add that no page quotes yet. The chat service reaches
`services/chat/approval.py` through one module, `services/chat/approval_routes.py`, behind a company's
`tenant_settings.agent_actions = approval` (13 October 2026, the wired approval); for every company that has not set it,
`tools.BLOCKED` and the LangGraph brain's refuse node stay as lessons 5.4, 5.5 and 5.7 show them, and a lane's chat
service is unchanged. Escalation on the lane is the case desk's existing hand-off (5.6). The page pull request removes
the rows it adopts. Lesson 5.8's page quotes `services/chat/approval.py`, `commands/approval-check.sh`,
`shared/approvals.py` and `services/chat/approval_routes.py`, so their rows are INDEX.md's.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_approvals.py` | **5.8** | A stdlib half (one module in the service imports approval.py, behind the switch; no audit emitter; the versions the module names are the pins; make, the script and both CI chat-pins steps run it) and a chat-pins half on scripted models, a stand-in rag-api and a fake Firestore that records writes: the pause and its path through the checkpoints; a turn with nothing to approve; a second process resuming from the same SQLite file; the requester's own approval refused by `decide()`, by the node's own lock and by `may_approve`; a rejection beside a search, and a cancel; `ask_user` answered by the requester only; `offer_case` for all six types with nothing written, and refused without the case desk or a queue; the Change-it line written twice; the tool's last lock and `normalize_name()`; the middleware form's extra node and checkpoint, and its record shape equal to the graph's. Both CI chat-pins steps install the SQLite pin before it. |
| `commands/tests/test_approval_wired.py` | **5.8** | The approval wired in (13 October 2026). A stdlib half: the switch reaches `agent.py` through one `approval_routes.wired()` call and one install line, defaults off, and `approval_routes.py` is the one importer of `approval.py`; `doc_approver` is a role, the four audit actions are registered, make, `.PHONY`, `mk/README.md` and both CI chat-pins steps carry `agent-actions`, `withdraw-run`, `smoke-approval` and this file; `reconcile.py --approved` re-checks and re-enters `--retire`'s own branch (its two `mirror.` calls unchanged). `shared/approvals.py` on a fake Firestore and audit bucket: one pause is one record with one event; who may read; 410 past `expire_at` and 409 once decided, in code; the status a decision amounts to; the executor records and withdraws nothing; `recheck()`'s refusals; an event the bucket refused waits on the record. A chat-pins half on the real chat service: the switch off is the brain lessons 5.4-5.7 show, with no record; on, the pause and its record, the hold (409), the requester's own approval (403), another company's approver and a colleague without the role (404), the second person's approval and the resumed turn's row, a second decision (409), a rejection beside a search, the requester's cancel, a question (`ask_user`) the requester alone answers, an expired record (410) and the hold ending its pause, a lost pause (409), `offer_case` as `case_offer`, and `--approved` dry and applied on the record. |
| `smoke/smoke_approval.py` | **5.8** | `make smoke-approval` (about Rs 10-15 of model calls; not in `smoke-all`), after `make agent-actions TENANT=acme AGENT_ACTIONS=approval` and `doc_approver` for documind-evalacme-sa: a withdrawal asked for as documind-ui-sa pauses the turn (200, pending), the same session is held (409), the requester's own approval is refused (403), documind-evalzeta-sa cannot see the record (404), the approver's inbox lists it, documind-evalacme-sa approves it (200, approved, the resumed turn's answer), a second decision is 409, a second withdrawal is rejected with a reason (refusals name the tool), and the requester's list shows both. It withdraws nothing: it prints the `make withdraw-run APPROVAL=` for the approval it left, then `make restore SOURCE=` and `make agent-actions ... AGENT_ACTIONS=off`. |

## The release (lessons 11.1-11.3, 11.8)

Kit files the release's pull requests add that no page quotes yet. R1 (lesson 11.1) adds the first three below; R2
(lesson 11.2: `make gate`, `make promote-gated`) extends `commands/release.py` and `mk/release.mk` and adds the fourth;
R3 (lesson 11.3: `make smoke-deployed`, `make incident`) extends the same two and adds the fifth; R5 (lesson 11.8:
`make capstone-check`, `make handover`) adds four: the command, its own `mk/capstone.mk` (not
`mk/release.mk`, which lessons 11.1-11.3 quote to its last line), its test and the canned fork the test runs it on.
The kit pull request that adds `make gate`'s `GATE_PROMPT=1` (13 October 2026) adds the last row. The page pull
requests remove the rows they adopt.
Lesson 11.1's page quotes `commands/release.py` and `mk/release.mk`, so their rows moved to INDEX.md (12 October
2026).
Lesson 11.8's page quotes `commands/capstone_check.py` and `mk/capstone.mk`, so their rows moved to INDEX.md (13
October 2026).
The four documents' templates, `capstone/templates/`, and their test are the last two rows (13 October 2026): the
author decided on templates, and lesson 11.8's page names both and quotes neither.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_release.py` | **11.1** | Stdlib. Stub `gcloud`, `gh` and `terraform`: one script behind a `/bin/sh` wrapper, or a `.cmd` on Windows, on a PATH that holds nothing else, recording every call. The four lines; the reviewer present, missing, no environment, no gh; each refusal (another region, another project, another lane's state, no state, no outputs, no confirmed inputs, a workflow that reads other variables, no terraform); keys none, found then deleted, an account not read, the parent, no gcloud; every call a read; the make targets, and the names `release.py` expects from `wif.tf`, `sa.tf` and `documind-cd.yml`. |
| `commands/tests/test_release_gate.py` | **11.2** | Stdlib. A stand-in gcloud and curl over one lane's `documind-api` in a JSON file (the traffic table with the candidate tag; each revision's image, digest, `GIT_SHA` and `/version`; `update-traffic` keeps the tags, as Cloud Run does), called in-process in place of `release.run`, with `get_version`, `live_gate` (a stand-in gate that writes `run_eval.py`'s report) and the clock replaced: the record's fields and files, red, a leak, a gate that stops (no report, the tag moved mid-run, Ctrl-C) and leaves no record, every refusal before a row is asked, `gate-check`'s pass and every refusal; `get_version` against a local HTTP server. Where a POSIX sh exists (CI's runner; Git Bash), the same stand-in on PATH runs `record-candidate`, `promote-gated`, `promote` and `rollback` as make hands their recipes to the shell (`MiniMake`; no make needed) in a copy of the kit's release files: the gated revision promoted and rolled back; another revision, a red record and a moved tag stopped before `promote`; `promote` and `rollback` as before. The targets, `.PHONY`, `GATE_FILE`, `mk/README.md` and these rows. |
| `commands/tests/test_release_repair.py` | **11.3** | Stdlib. `test_release_gate.py`'s stand-in, lane classes, stand-in gate and `MiniMake`, loaded from that file and extended: `spec.template` and `gcloud run services update` (a revision made from the template with env vars merged and `--remove-env-vars`, the candidate tag moved), `gcloud run services list` per region, `gcloud run revisions list` with creation times, `/version` from a revision's env, and `make` for the smokes (an API smoke fails while the serving revision names a model Vertex AI does not serve). `smoke-deployed`: exactly the deployed services' smokes, in smoke-all's order with its exports (twice through the real `run_smoke` and a stand-in make on disk), Module 9's when deployed and the SLM only in SLM_REGION, a red smoke, a smoke's own exit status, `/version` or what stopped it, the traffic moving mid-run, every refusal, an interrupted run. `incident`: the gated state after a gated promote; after the forced promote and the rollback (the drift, the red candidate, the repair line); the template put back; the repair gated and promoted; a red revision serving; a revision no gate judged; the repair for an image, a setting `make candidate` does not pass, a non-default setting and one set only on the template; the window and the log's other lines; refusals. Where a POSIX sh exists: the controlled failure through `record-candidate`, `promote-gated`, `candidate` (`MiniMake` learns `$(if)`), `promote`, `rollback`, `release-candidate` (which inherits the typo) and `incident`; `make smoke-deployed` itself, its one HTTPS request refused by a local proxy. The targets, `.PHONY`, the recipes, smoke-all's smokes against their recipes' URLs, `make candidate`'s settings and these rows. |
| `commands/tests/test_capstone_check.py` | **11.8** | Stdlib. The canned fork laid over a copy of the kit files the check reads: all eight PASS; the Change-it (one FAILURE-MODES command deleted) fails component 7 alone; each component broken alone fails alone; the kit as it ships passes component 3 alone; the lane as a stand-in at `release.run` and `http_json` (every component's reads and each way they fail, only READS and the two tokens asked, a write refused before it runs, another lane's records ignored); handover offline, with the lane and with a failed read; the selftest; the page trees of the kit's real PDFs against `evals/real_sources.json`; the wiring (targets, `.PHONY`, the Makefile's 888 lines, FORK declared nowhere, `mk/README.md`, these rows). |
| `commands/tests/capstone_fork/` | **11.8** | The canned fork, made up (Sahyadri Freight, tenant `sahyadri`, placeholders only: its records name the lane's URLs `documind-api-NUMBER`, and the test puts the stand-in lane's number in): the four documents, a 32-page corpus in two text files, two golden rows (`golden.jsonl.add`, which the test appends to the kit's), and the records lesson 11.3's controlled failure leaves (four make smoke-deployed runs around a forced promote and its rollback, and the repair's gate report and record). A fixture, not a template: `capstone/templates/` holds the templates, and these four are them filled in for a made-up company. |
| `capstone/templates/` | **11.8** | The four documents' templates, `ARCHITECTURE.md`, `COST-MODEL.md`, `FAILURE-MODES.md` and `RUNBOOK.md`: the canned fork's four emptied, each slot a `{{...}}` placeholder on one line, and a comment at the top of each saying what `make capstone-check` reads in it and what the defence reads. Copied to a fork's root as they ship, each fails its component (5 to 8) until the placeholders the check reads are replaced. The check's line for a missing document names its template, and `HANDOVER.md`'s head names the runbook's. Lesson 11.8's page copies them over the canned fork's four and shows the check fail, then pass with the canned four back. |
| `commands/tests/test_capstone_templates.py` | **11.8** | Stdlib, no make: the check's own component functions on a fork in a temporary directory. The four and nothing else; the canned documents' headings and none of their text; one placeholder per line and none in a comment; what the check reads in each; as they ship, components 5 to 8 FAIL, each on the slots of its document that still hold a placeholder; every placeholder filled, the four PASS; a missing document names its template; `HANDOVER.md` names the runbook's; the rate is `shared/prices.py`'s; these rows. |
| `commands/tests/test_gate_prompt.py` | **11.2** | Stdlib and git. `make gate`'s `GATE_PROMPT=1` (13 October 2026, off by default): `release.prompt_reasons()` on commits of a throwaway repository holding the four files it reads (the kit as it ships; its text changed under v3; lesson 3.6's v4 registered beside v3; v4's line on v3's text; lesson 12.4's rules version, alone, on a changed SYSTEM and with its label registered too; a commit with no rules file or no registry; a sha the checkout does not hold), and `live_gate()` with and without the switch: without it no `/version` is read and the rows run as before; with it a prompt that is not a registered version stops before `evals/run_eval.py` starts. A page that adopts the switch (3.6 or 11.2) quotes it. |

## Older orphans, predating this file

Nothing points at these and no lesson creates them. A learner following the notebooks alone
never provisions the Firestore database that `firestore_indexes.tf` attaches its vector indexes
to — worth closing when Module 12's infra lesson is next opened.
Lessons 0.1, 0.3 and 0.4 quote `terraform/network.tf`, so its row moved to INDEX.md (13 October 2026). Lesson 0.3
names the other two without quoting them.

| File | Should belong to |
|---|---|
| `terraform/firestore.tf` | **12.1** (infra) |
| `terraform/registry.tf` | **12.1** |

## Shared modules — owned, but by more than one lesson

Not orphans; listed so nobody "tidies" them back into a service.

| File | Why it is shared |
|---|---|
| `shared/documind_tools.py` | the single `retrieve()`. `tools/check_one_retrieval.py` enforces it. |
| `shared/pii.py` | one India info-type list, used by the ingest worker **and** the admin dashboard. Two lists that drift is the worst kind of compliance bug: the scan misses a type, the dashboard reports zero findings, and both look correct. |
| `shared/audit_log.py` | one event shape into one retention-locked bucket, written by ingest and admin. |
| `shared/documind_schemas.py` | the one answer contract (owned by 12.2, see the adoption table). Imported by rag-api; pasted verbatim by 3.2, 4.2, 4.5, 4.6. A second copy that drifts is exactly the M03 gate failure it closed. |
| `shared/profile.py` | 6.4's step-7 cell as a module: `DOCUMIND_PROFILE`, `build_llm()`, `build_store()`. Read by `chat/agent.py` (the model) and by `documind_tools.retrieve()` (the store). **Unowned** — 6.4 is outside the extractor; 6.4's notebook and page name it. Gap G3. |
| `shared/local_corpus.py` | DocuMind's corpus — `evals/corpus/` through `shared/documind_corpus.py`, the same chunks and ids 2.3 and 4.2 put in Firestore, thirteen real documents included — seeded per tenant into the local Chroma store (`make chat-local`, `python -m shared.local_corpus [tenant]`). Unowned, same reason. Until 2026-09-05 it typed the six Module 6–8 passages. |
| `shared/documind_corpus.py` | the one loader and chunker: `find_kit()`, `load_documents()`, `chunk_document()`, `seed()`. Pasted verbatim (its kit block) by 2.3, 4.2, 4.5 and the 4.2/4.5 practice labs — `tools/check_contract.py` holds them to it — and imported by `local_corpus.py` and `tools/check_real_corpus.py`. Unowned. Gap G20. |
| `services/chat/requirements-local.txt` | 6.4's pins for the local lane (`langchain-chroma`, `chromadb`, `langchain-ollama`, `langgraph-checkpoint-sqlite`), installed on top of `requirements.txt` and never in the image. Unowned; `services/chat/tools.py`, `requirements.txt` and `Dockerfile` are unowned too — 12.8's notebook holds `agent.py`, `cloudsql.tf` and the chat `DEPLOY` command. |
| `services/chat/migrate.py` | `PostgresSaver.setup()` once, as a Cloud Run job (`commands/lesson-12.8.sh` step 3) — 8.5's rule that migrations taking exclusive locks never run at startup. Unowned. Gap G5. |

Services that can see `shared/` build from the `deploy/` context: **chat, ingest, admin, rag-api**
(rag-api since 2026-09-05, through `cloudbuild.yaml`). `frontend`, `gemma-vllm` and `litellm`
still build from their own directory — move them to the `deploy/` context before importing
anything from `shared/` there.

## Checkpoint and resume (lesson 6.8)

Kit files PR 6.8-A adds that no page quotes yet. Lesson 6.8's page adopts them; the page pull request removes the rows
it adopts. Nothing under `services/` changed: the chat service writes its threads as before, and these only read them.
Lesson 6.8's page quotes `commands/thread_read.py`, `commands/thread_replay.py`, `mk/memory.mk` and
`evals/threads/cut_off_turn.json`, so their rows moved to INDEX.md (12 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/graph-venv.sh` | **6.8** | Runs a kit command in `~/graph-venv` (made if missing, as `limits-check.sh` makes it) after `pip install -r services/chat/requirements.txt`; `--connector` adds `cloud-sql-python-connector[pg8000]==1.22.0` and `pg8000==1.31.5`, lesson 6.6's pins. Later Module 6 targets can run through it too. |
| `commands/tests/test_thread_read.py` | **6.8** | A stdlib half (the targets, the 888 lines, both CI lines and these rows; every statement a SELECT; the listing through a fake gcloud and connector, read only from the first statement, the password used and never printed; EMAIL, SESSION, AT and an ambiguous tenant refused; a thread's latest line) and a chat-pins half: threads the kit's LangChain and LangGraph brains wrote (a langgraph thread, one both brains wrote, a recursion-limit repair, the cut-off fixture) turned into the rows PostgresSaver stores with the pinned library's own `_dump_blobs`/`_dump_writes`, served by a fake pg8000 cursor and decoded back to every step's messages, metadata and next; the strict serializer; the export round trip and a branched thread; the offline replay inside its socket guard with no project set, the copy step for step, a recorded turn matched (from its input and from mid-turn), a cut-off turn finished, the fork's branch, parent and uuid4 question, three branches in the history, a turn's last step refused, the command's refusals and `DB=`; the shipped fixture against `--write-fixture`. CI's chat-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Context sources (lesson 6.1)

Kit files PR 6.1-A adds that no page quotes yet. Lesson 6.1's page adopts them; the page pull request removes the rows
it adopts. Nothing under `services/` changed: the command builds the chat brains and the Desk agent as the service
builds them and reads their model calls where they meet google-genai. A lane run writes no thread and no chat row;
rag-api logs its searches as it logs any.
Lesson 6.1's page quotes `commands/context_sources.py` and `commands/tests/test_context_sources.py`, so their rows
moved to INDEX.md (13 October 2026).
Lesson 6.1's page quotes `mk/memory.mk`'s `context-sources` target, so its row moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|

## Working memory (lesson 6.9)

Kit files PR 6.9-A adds that no page quotes yet. Lesson 6.9's page adopts them; the page pull request removes the rows
it adopts. The chat service does not import `services/chat/context_window.py`: no brain, route or switch reaches it, every
brain still sends its model the whole thread on every call (as lesson 3.4 says), and a lane's chat service is unchanged.
`make window-check`, appended to `mk/memory.mk` after lesson 6.8's targets, runs it.
Lesson 6.9's page quotes `services/chat/context_window.py`, so its row moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/window_check.py` | **6.9** | `make window-check`: twenty scripted questions on acme in one conversation of the kit's LangChain brain (`BRAIN=langgraph` for the other) on an InMemorySaver, its model `context_window.windowed()`; after each turn a row: the thread's messages and tokens, the turn's largest call's context and ceiling, the earlier turns it kept whole and brought forward, and the results cleared, numbers masked and questions cut. `MODE=windowed` (the default) or `full` (today's, with the window's ceiling for comparison); `HISTORY=` the budget; `TURNS=`; `SAVE=` every turn as JSON with every call's report. The questions carry a published test card number (question 6) and one of 395 characters (question 9), and none the Desk's gate takes. Offline: lesson 6.8's harness (`thread_replay.offline()` and `scripted()`: a socket guard, a script that searches for the question and answers from the first passage, the Rs 0 lane over `evals/corpus`), Rs 0. `LIVE=1` (`guard-project`; `GOOGLE_CLOUD_PROJECT` from `PROJECT`): each question in two fresh conversations, full then windowed, with Gemini through `build_llm()` on location global, the searches still the Rs 0 lane's (`rs0_lane()`: the placeholder project in the URIs, no token minted), per turn and conversation Gemini's own input, cached and output tokens, the window's estimate, the rupees from the turn's `limits.Meter`, the answer and its sources; totals and the share saved; a turn that raises stops the run (exit 1) with the turn and conversation named. Runs in `~/graph-venv` through `commands/graph-venv.sh`. Not yet run with Gemini. |
| `commands/tests/test_context_window.py` | **6.9** | A stdlib half (the target, the 888 lines, both CI lines and these rows; nothing under `services/`, `shared/` or `smoke/` imports the module; `plan()` at its edges and on 3,000 random cases; `turns()` and a split pair joined; an earlier question masked then cut to the Desk's 300; the command's refusals and its questions) and a chat-pins half: every promise of `window()` on generated threads (tool rounds of parallel calls, refusals, a turn cut off, answers in content blocks, card and Aadhaar numbers, long questions; budgets 0 to a million), an oversized newest turn sent whole, the line and the kept turns, an earlier refusal kept as it was beside a cleared result, `full()`'s very list, the kit's LangGraph and LangChain brains with `windowed()` sending exactly `window()` of what they hold while the checkpoint keeps every message unmasked, mode full equal to no window at all, the middleware's window and lesson 6.6's +3/+5 checkpoints unchanged, `make window-check` offline in both modes on five of the corpus's documents, and the live path on a scripted model inside the socket guard. CI's chat-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Production gotchas (lesson 11.7)

Kit files the production-gotchas pull request (the cohort plan's R4) adds that no page quotes yet. Lesson 11.7's page
adopts them; the page pull request removes the rows it adopts. Nothing under `services/` or `terraform/` changed and no
target that existed before does anything new: the registry is read, the offline drills run on a stand-in at Rs 0, the
detectors only read, and only a live drill (`LIVE=1`, on the author's lane) changes a lane, and puts it back.
Lesson 11.7's page quotes `ops/gotchas.json`, `commands/gotchas.py` and `mk/operations.mk`, so their rows moved to
INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_gotchas.py` | **11.7** | Stdlib. The registry's schema and each of its rules, unique ids, the lessons in `course-manifest.json` (skipped where there is none: the learner repository), the kit behind each entry, each detector and drill run by `gotchas.py`, a detector that does not exist refused (the page's Change-it); every offline drill's REPRODUCED and CLEARED lines; pinned-traffic and deploy-drops-hotfix in detail on the stand-in (the gcloud lines, the cap `/health` reports, the lever, the chat put back, and put back after a failure mid-drill); `limits-drill.sh`'s own `latest_takes_all` agreeing with `follows_latest()`; a kit that changed (a deploy that merges, no traffic move after lesson-12.2.sh, evidence gone) not reproduced; the deploy reader (`test_deploy_scripts.py`'s cut, the seven services, what deploy-services passes, what the next deploy changes, sh's expansions); the stand-in's Cloud Run rules; each detector on stand-ins and their exit codes; the live path's preconditions, lines and `make deploy-services` argv; `detect` through a stub gcloud, the only tool on PATH; the make wiring. |

## Incident remediation (lesson 10.11)

Kit files lesson 10.11's kit pull request adds that no page quotes yet (wave 5 of `plan/cohort-2-lesson-plan-2026-10-07.md`:
a held fault diagnosed by rules with no model call). Lesson 10.11's page adopts them; the page pull request removes the
rows it adopts. Nothing a lane runs changed: `make remediate` only reads, and `make incident-drill` changes
documind-chat only when asked to hold a fault, until it is asked to restore it.
Lesson 10.11's page quotes `commands/remediate.py`, `commands/incident-drill.sh`, `mk/operations.mk`,
`ops/runbooks.json` and `commands/tests/test_remediate.py`, so their rows moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `ops/incidents/` | **10.11** | Recorded lane states in the shape `SAVE=` writes, written by hand from the kit's own shapes (no lane was read), placeholders only: `held_model.json` (`make remediate OFFLINE=1`'s default: the drill's mistyped model, `bad_revision`), `held_model_calls.json` (the call cap, `bad_revision`), `rolled_back.json` (after the printed rollback and a smoke), `restored.json` (after `RESTORE=1`, `no_failure`), `old_revision.json` (5xx on a revision made before the window, `no_change`), `person_only.json` (the Desk's delegation policy) and `unknown_policy.json` (the agent alert policy designed for after 6 December, which the kit does not declare). The author's batch 3 run can add a recorded one with `SAVE=`. |

## Change a chunker (lesson 8.2)

Kit files the twin-chunker pull request adds that no page quotes yet. Nothing outside the tests changed: the worker and
`shared/documind_corpus.py` chunk as before. Lesson 8.2's page adopts them; the page pull request removes the rows it
adopts.
Lesson 8.2's page quotes `commands/tests/test_twin_chunker.py`, so its row moved to INDEX.md (13 October 2026).

## The managed peer (lesson 10.9)

Kit files PR 10.9-B adds that no page quotes yet. Lesson 10.9's page adopts them; the page pull request removes the
rows it adopts. Nothing under `services/` changed and no Terraform did: the A2A peer's own files are staged as they
are, and it runs as `documind-agent-sa`, the Cloud Run peer's account (the lesson plan's decision 13). What no lane had
shown when these were written is a row of the author's batch-0 probe (`tools/probe_agent_stack.py`, authoring repository
only), named in `managed_peer.py`'s `FACTS`; a refusal that contradicts one stops the command with exit 3 and the row.
Lesson 10.9's page quotes `commands/managed_peer.py`, `commands/managed_peer_agent.py` and `mk/managed.mk`, so their
rows moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/managed-peer.sh` | **10.9** | Runs `managed_peer.py` in `~/managed-peer-venv` (`MANAGED_PEER_VENV`), made if missing, after `pip install "google-adk[a2a]==<the peer's pin>" "google-cloud-aiplatform[adk,agent_engines]"` - the probe's own install, its fact 11 - with `==$AIPLATFORM_PIN` when set. The pin is read from `services/agent/requirements.txt` with sed. Not `~/graph-venv`, whose contents lessons 10.4 and 11.1-11.3 assert. |
| `commands/tests/test_managed_peer.py` | **10.9** | A stdlib half (the targets, the 888 lines, both CI lines, these rows; what `stage()` writes, byte for byte, and the `.env` against lesson-8.4.sh's variables; every command on `FakeGoogle`: up's order (create, grant, deploy) and its second run, the grant left when it was there before, each deploy refusal's fact (1, 2 with the role to grant, 3, 11) with the instance kept for `down`, a read back naming another account; ask's record, its rupees, its cold flags and no identifier in it, zeta's refusal, each failed turn's fact (5, 2, 6), documind-ui-sa refused (8), the Cloud Run peer asked the same way; trace's spans, callers and runtime line, the question in a span (7), another caller (2), the wait; sessions; down by name and by display name, other names and regions untouched, the grant taken back, twice, what is left; the smoke's eight checks, its table, `--keep`, an existing peer kept, a failed check, the SKIPs, a fact during its deploy; every dry run with no backend and no Google import; compare) and a google-adk half: the staged package through ADK's own `AgentLoader` (a2a-sdk and mcp stood in where absent), `root_agent` the peer's own agent on GlobalGemini at global with the peer's credential hook, the import line, the cap stopping a scripted loop at twelve model calls; ADK's own deploy on a stand-in vertexai (the config, the env_vars with telemetry on and content off, the Dockerfile's `GOOGLE_CLOUD_LOCATION`, the requirements with the unpinned line ADK appends, or none with a pin); `LiveGoogle`'s REST, session and A2A calls on stand-ins. CI's chat-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Coding agents (lesson 10.10)

Kit files the coding-agents pull request (the cohort plan's 10.10) adds that no page quotes yet. Lesson 10.10's page
adopts them; the page pull request removes the rows it adopts. Nothing under `services/` changes, and no kit file is
written by them: the loop works on a copy of `shared/desk_calc.py` in a run directory outside the kit, and the answer key
is the kit's own `statutory_deadline`, read at run time. The egress proxy the plan sizes at a day came in a pull request
of its own (13 October 2026): `RALPH_EGRESS=proxy`, off unless given, holds the live agent's container to the model
endpoint; off, the container can reach the network as before; see `commands/ralph.py`.
Lesson 10.10's page quotes `commands/ralph.py`, `commands/ralph/oracle.py` and `commands/review_diff.py`, so their
rows moved to INDEX.md (13 October 2026).
Lesson 10.10's page quotes `commands/ralph/statute.md`, `commands/ralph/PROMPT.md`, `commands/ralph/Dockerfile`,
`commands/ralph/iteration.sh` and `commands/ralph/settings.json`, so they left their rows for INDEX.md (13 October
2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/ralph/seeds.json` | **10.10** | Six one-line substitutions on the kit's `statutory_deadline`, each with its rubric class and its weak and strong verdict: placeholder (`date(2026, 10, 6)`: weak pass, strong fail), calendar_days, start_day_counted (off_by_one), closure_counted (event_scope), date_contract (error_contract: `date.fromisoformat` by hand, ValueError not `CalcError`; weak pass) and holiday_note_dropped (hidden_assumption). Every one fails the strong oracle; the weak one passes two. |
| `commands/ralph/spec.md` | **10.10** | The engineer's spec: the desk's reading of s.17(2) (from the last working day, Monday to Friday, the four events and not closure), `CalcError`, the result's rules, formula and notes. |
| `commands/ralph/fix_plan.md`, `commands/ralph/context.md` | **10.10** | The one-item plan the agent extends, and the context file copied in as `GEMINI.md` (the kit's calculator rules, the fast test, a "Learned" list). |
| `mk/coding.mk` | **10.10** | Module 10's coding-agent file: `ralph-image` (`GEMINI_CLI_VERSION` required), `ralph` (`OFFLINE`, `DRY_RUN`, `TASK`, `ORACLE`, `RALPH_MAX_ITERS`, `RALPH_BUDGET_INR`, `RALPH_MAX_DIFF_LINES`, `RALPH_MODEL`, `RALPH_PROJECT`, `OUT`), `ralph-workspace`, `ralph-check` (`PATCH`, `WORKSPACE`, `SHOW`), `ralph-probe` (`YES`), `review-diff` (`DIFF`, `MODEL`, `THINKING`; `guard-project` unless `OFFLINE`) and `review-eval` (`REPEAT`, `SAVE`, `FROM`), with `RALPH_IMAGE ?= documind-ralph`, its row in `mk/README.md` and the targets appended to the last line of the Makefile's `.PHONY`, so the Makefile keeps its 888 lines. A new file, so `mk/agents.mk`, whose route-eval recipe lesson 10.4 reads by line, is untouched. |
| `commands/tests/test_ralph.py`, `commands/tests/test_review_diff.py` | **10.10** | Stdlib, in CI's offline step. The wiring and these rows; the image's files; the cut, splice and `outside()`; every seed once, a stale one refused; every version's verdict its label, the oracle's count equal to the kit's over 2026, the Change-it, the guard (urllib, a name, a connection, a datagram, a process), no credential in its environment, a forged verdict line; the workspace; the scripted loop strong, weak and on paper-to-code, every cap, undo and flag; the live loop through a stub docker (the run lines, the env file's names and 0600, the key in no output, the oracle with no network, the stats priced, a cut iteration, no stats, the public copy), the live refusals, the dry run and the probe; `check` on patches and a workspace. The reviewer: the rubric and schema, the definitions, the request with no label in it, a review priced, its errors, the client on `global`, the linter, the score and the command. |
| `commands/ralph/egress.py` | **10.10** | The egress proxy (`RALPH_EGRESS=proxy`, off unless given), stdlib: an allowlisting forward proxy that opens an HTTPS tunnel (CONNECT) to an exact `host:port` on its allowlist, `aiplatform.googleapis.com:443` as `commands/ralph.py` starts it, and refuses everything else with 403 - another host, port or IP, any plain request - without dialling it; one log line a request, a plain request logged by its method and host alone. `commands/ralph.py` (`Egress`, `EgressAgent`) runs it for each live iteration in a container of the ralph image, on docker's default bridge and on the iteration's own `--internal` network, where the agent's container finds it as `egress` through `HTTPS_PROXY`; the network and the proxy are removed after the iteration and the log kept as `iterations/NN-egress.txt`. `make ralph-probe RALPH_EGRESS=proxy` checks it on a live docker, free. |
| `commands/tests/test_ralph_egress.py` | **10.10** | Stdlib, in CI's offline step. The proxy on loopback, with a stand-in upstream and a dialler that refuses all else: an allowed tunnel both ways, the exact match (case and a trailing dot folded; another host, port, a suffix, an IP refused), a plain request refused and its URL never logged, a malformed, oversized or slow head, an unreachable endpoint; the proxy's own command line end to end; the standard library alone; the allowlist and its reasons; the switch (off by default, the flag, `RALPH_EGRESS`, a wrong word, offline untouched); through `test_ralph.py`'s stub docker, taught `network`, `run -d` and `logs`: the commands around each iteration and the agent's line with two flags added and nothing else changed, a refused host counted, a proxy that does not start or never listens stopping the loop with nothing left, the default untouched, the dry run, and the probe's three free checks and its calls behind the proxy; the recipes and these rows. |

## Eval-gated self-improvement (lesson 12.4)

Kit files PR R6 adds that no page quotes yet. Lesson 12.4's page adopts them; the page pull request removes the rows it
adopts. Two files change outside every span a page quotes: `services/rag-api/generator.py` gains two lines at its end,
and `mk/generation.mk` (its row is under lesson 3.6) gains `improve` and `prompt-candidate`, both appended to the last
line of the Makefile's `.PHONY`, so the Makefile keeps its 888 lines. `PROMPT_VERSION` defaults to v3, which adds no
rules: a lane that sets nothing serves the prompt it served before.
Lesson 12.4's page quotes `services/rag-api/prompt_rules.json`, `services/rag-api/prompt_rules.py` and
`evals/improve.py`, so their rows moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/tests/test_prompt_rules.py` | **12.4** | Stdlib. The kit's v3 adds nothing and `config.py`'s default is v3, so the served prompt is the literal, equal to `evals/make_trainset.py`'s `SYSTEM`; `generator.py` ends with the two lines, after every function, and `SYSTEM` keeps its one assignment (`prompt_pin.prompt_text()` unchanged); the lines, run as the service runs them, give v3's text, v4's with its rule, and a refusal; every reader of `SYSTEM` reads it inside a function, and `cache_admin.py` imports it when it runs; the numbering equals `prompt_bench.edit_system()`'s; each check and each forbidden phrase; append-only and `extends()`; a registered version adds nothing and any other is refused; the image copies the files, and the module imports the standard library alone. |
| `evals/tests/test_improve.py` | **12.4** | Stdlib, a scripted proposer and a copy of the kit hashed before and after: a proposal accepted end to end (the request's model, schema and prompt, its rupees, v4 written with its reviewer, the `R(...)` row taken by `build_golden.py`'s `R()`, only `prompt_rules.json` and the proposal written, `version v4`); v5 built on v4; a stale proposal and the proposer as reviewer refused; a "never refuse" proposal stopped by the check, from the model and by `--rule`; a reply outside the schema; a row whose facts are not in the documents, refused before any call; rows it cannot use; no project; `write()` refusing each evaluator file; every write through `write()`; the targets, the 888 lines, the README row and these rows. |

## Defend agents against injected documents and poisoned tools (lesson 10.8)

Kit files PRs 10.8-A and 10.8-C add that no page quotes yet. Lesson 10.8's page adopts them; the page pull request
removes the rows it adopts. Two switches, both off unless set to `on` (any case), so a lane that sets neither behaves as before:
`AGENT_FENCE` on documind-chat (`services/chat/tools.py`'s `search()` hands the chat brains' model each quote inside a
`<document>` fence with `RULE` first, after `_number()`, so the ledger and the answer's citations keep the clean quote;
`services/chat/desk_agent.py`'s `_search()` does the same for a Desk agent's passages, after its ledger, which
`desk_calc.check_args` reads) and `AGENT_SCRUB` on documind-chat (`services/chat/agent.py` scrubs each `/v1/chat`
answer after the brain returns it and adds `scrubbed`, the count, to the response; the chat row is unchanged). Lesson
5.1's adapter excerpt now shows the fence line, and its page was rebuilt with it. The UI's direct radio streams
rag-api's `/v1/stream`, which neither switch touches; since 13 October 2026 the Chat page shows the count on a line
under an agent brain's caption when it is above 0 (the section at the end of this file). The A2A
peer's sentence is PR 10.8-B's. PR 10.8-C adds the injected document below and extends lesson 4.9's attack runner
(`evals/run_attacks.py`, `evals/adversarial/attacks.jsonl`, `evals/tests/test_attacks.py`, all owned by 4.9) with the
chat, Desk and peer surfaces: six rows (`atk-16` to `atk-21`), the doors `--chat-url`, `--desk` and `--peer-local`, and
the controls `tenant_pin`, `check_args`, `doc_class`, `agent_fence` and `agent_scrub`. `--surfaces` defaults to `api`,
so lesson 4.9's runs are unchanged; its page rebuilds identical but for the one-line count of `test_attacks.py`'s tests.
Lesson 10.8's page quotes `shared/spotlight.py` and `evals/adversarial/vendor_note_acme.md`, so their rows moved to
INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_spotlight.py` | **10.8** | A stdlib half (the fence on every spelling of its own tag and an escaped source; `fenced()` changing nothing it was given; each marker and count; an allowed host kept and the tricks a URL can play refused; 2,000 generated answers with nothing a renderer fetches left and a second scrub finding nothing; the switches off unless on; the kit's lines where they must sit, outside the spans lessons 5.1, 6.1 and 6.7 quote and off the chat row; both CI lines and these rows) and a chat-pins half: `search()` as it was with the fence off and a fenced copy after `_number()` with it on; ADK's retrieve; the LangChain brain on a scripted model reading the fence while the turn's citations stay clean; the Desk agent's `_search()` with a clean ledger; `POST /v1/chat` with the markers and `scrubbed` in the response and the row's keys unchanged. CI's chat-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## The A2A peer's cap and the chat's hand-off (lesson 10.7)

Kit files PRs 10.7-A and 10.7-B add that no page quotes yet. Lesson 10.7's page adopts them; the page pull request
removes the rows it adopts. The cap itself is in files pages already quote, outside their excerpts:
`services/agent/agent.py` sets `ADK_MAX_LLM_CALLS` to 12 unless the environment holds a value (`os.environ.setdefault`,
before `to_a2a` builds the app; ADK's `RunConfig` reads it as each task starts, and its own default is 500) and names it
on `/health` as `max_llm_calls`, and `commands/lesson-8.4.sh` deploys the same 12. Lesson 5.5's `make limits` line now
prints the 12. The hand-off, too, touches quoted files outside their excerpts only: `services/chat/brains.py` imports
`peer` and, when `PEER_URL` is set, adds its tool to the ADK brain's list and the turn's `handoffs` to its answer (five
lines); `shared/tenancy.py` gains `tenants_of()` after `list_members()`; `services/chat/requirements.txt` pins
`a2a-sdk==1.1.2` with no extra; `validate.py`'s `THIRD_PARTY` names `a2a`. Off by default: a lane without `PEER_URL`
answers exactly as before.
Lesson 10.7's page quotes `commands/agent-drill.sh` and `services/chat/peer.py`, so their rows moved to INDEX.md (13
October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_agent_drill.py` | **10.7** | Stdlib and bash, in CI's shared interpreter: agent.py's `setdefault` before `to_a2a` and `max_llm_calls` on `/health`; the deploy's 12 (and `commands/managed_peer.py`'s, lesson 10.9, where it exists); the smoke's five checks and the helpers the drill borrows; the target, `.PHONY`, `mk/README.md`, the 888 lines and these rows. Then the drill against a stub gcloud that keeps the service's environment and traffic in a file and records every call, and a stand-in peer answering as agent.py over `to_a2a` does: end to end, an unset variable removed again, no cap on `/health` and pinned traffic (both stop before any change), and a revision that does not take the traffic, a peer that ignores the cap and a task that fails for another reason (each fails, and the trap puts the variable back). |
| `commands/handoff.sh` | **10.7** | `make handoff` (`mk/agents.mk`, appended): `PEER_URL` (`https://documind-agent-NUMBER.REGION.run.app`) and `PEER_ACCOUNT` (documind-agent's own account, read from Cloud Run) onto documind-chat in one env update, after checking that documind-agent is deployed and that documind-chat-sa holds `roles/run.invoker` on it (either missing, nothing changes); `OFF=1` removes both. The latest revision must take all the traffic, before and after. No Makefile line beyond `.PHONY`: the chat's deploy (`commands/lesson-12.8.sh`) sets every variable, so the next `make deploy-services` switches the hand-off off. |
| `smoke/smoke_handoff.py` | **10.7** | `make smoke-handoff`: smoke_chat.py's own `token_as()` and `call()`, as documind-ui-sa. The ADK brain, asked what the corpus holds, has `documind_peer` among its tool calls and a hand-off answered, its task completed within its budget (a refusal's reason is printed); the LangChain brain answers the same question with no `handoffs` key. Not in Module 10's gate (`make smoke-agent`, `make smoke-desk`) or `make smoke-all`: the hand-off is off by default. |
| `commands/tests/test_handoff.py` | **10.7** | Stdlib (with requests) and bash, in CI's shared interpreter: the constants (2, 75 s inside the turn's 100 s and the UI's 120 s), `gate()` and `budget_s()`, `tenants_of()` on a fake Firestore, the brains.py lines (off unless `PEER_URL`; the ADK brain alone), the pins and `THIRD_PARTY`, the targets, the 888 lines, both CI lines and these rows, smoke_handoff.py's verdict, and handoff.sh against a stub gcloud (on, off, no peer, no invoker). Then, in the chat image's pins with a2a-sdk, the kit's ADK brain on a scripted model against a stand-in peer that answers a2a-sdk's client as `agent.py` over `to_a2a` does: off unchanged; an inventory question handed over with only the question and the chat's token; the peer and a search together; both confused deputies refused with nothing sent; the third of three refused; a failed task, a slow peer cut at the floor, a shut door, each data; one log line per hand-off. CI's chat-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Cycles: the caller graph and the peer's delegation chain (lesson 10.7)

Kit files PR 10.7-C adds that no page quotes yet. Lesson 10.7's page adopts them; the page pull request removes the
rows it adopts. Files that already exist change too. `services/agent/agent.py` reads `PEER_CHAIN` (default `off`),
names it on `/health` as `peer_chain`, and hands `to_a2a` `agent_executor_factory=_chain_factory()`: `None`, ADK's own
executor as before, unless the switch is `on`, and only then is `chain.py` imported. That `to_a2a` line is inside
lesson 10.6's `serve` excerpt, so 10.6 is rebuilt with it (its build's assert follows the line; the cell that lists
agent.py's imports now names `chain`). `commands/lesson-8.4.sh` deploys `PEER_CHAIN=${PEER_CHAIN:-off}`, before the
cap, which stays last on the line. `services/chat/peer.py` sends the chain, `["documind_adk"]`, and a hand-off id in
the A2A request's metadata, and its record and log line carry the id. `tools/check_authz.py`, in the authoring
repository, holds `check_callers.py`'s reading equal to its own graph. Off by default: a peer without `PEER_CHAIN=on`
runs every task exactly as before.
Lesson 10.7's page quotes `services/agent/chain.py` and `commands/check_callers.py`, so their rows moved to INDEX.md
(13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_check_callers.py` | **10.7** | Stdlib, in CI's shared interpreter: the kit's graph (nine edges, the order, acyclic); the scripts' callers equal to sa.tf's six lines; the Change-it's cycle with exit 1; a service its own account may invoke (a cycle of one); a caller that runs no service (no cycle); no `--graph` (exit 2); a binding's member parsed (a loop variable in braces, a Google service agent, another role, another service); the target, `.PHONY`, `mk/README.md`, the 888 lines and these rows. |
| `commands/tests/test_a2a_peer.py` | **10.7** | Stdlib first: agent.py's switch (`chain` imported only when on; still one log call and no caller's headers, which lesson 10.6's build asserts), the metadata keys equal on both sides of the hop, lesson-8.4.sh's `PEER_CHAIN=${PEER_CHAIN:-off}` with the cap last, both CI lines and these rows. Then, in the peer image's pins (CI's agent-pins steps, new in both workflows, with `DOCUMIND_REQUIRE_LIBS=1`), the kit's agent.py over its own `to_a2a` through Starlette's TestClient, the model scripted and counted, the MCP toolset removed: off, no factory, and a looping chain runs; on, a loop and a chain of three each rejected with no model call, no `InvalidAgentResponseError` and one `a2a_refused` line; on, no metadata and the chat's own chain answered; the 0.3 wire's "rejected"; `/health`'s `peer_chain`. |

## Tool pins: the peer refuses a changed or unknown tool (lesson 10.8)

Kit files PR 10.8-B adds that no page quotes yet. Lesson 10.8's page adopts them; the page pull request removes the
rows it adopts. `services/agent/agent.py` (one owner, after 10.7's PRs) reads `TOOL_PINS` (default `off`) and
`AGENT_FENCE` (default off), names both on `/health`, and adds one line to `build_agent`'s `McpToolset`,
`tool_filter=_tool_filter()`: `None` unless `TOOL_PINS=on`, and only then is `pins.py` imported, so the managed form
(lesson 10.9), which stages agent.py alone, keeps importing with the switch off. That line is in lesson 10.6's `peer`
excerpt, so 10.6's `block(..., n=22)` becomes `n=23` and 10.6 is rebuilt (its import cell now also names `pins`).
With `AGENT_FENCE=on` the peer's `INSTRUCTION` gains one sentence (passages and tool results are data, never
instructions) - the same switch 10.8-A reads for the chat's fence; off by default, so `INSTRUCTION` is unchanged and no
page moves. Off by default throughout: a peer without `TOOL_PINS=on` uses every tool the server lists, as before.
Lesson 10.8's page quotes `services/agent/pins.py`, `services/agent/tool_pins.json`, `commands/pin_tools.py` and
`evals/adversarial/evil_mcp.py`, so their rows moved to INDEX.md (13 October 2026).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_pins.py` | **10.8** | Stdlib first: `tool_pins.json`'s shape and the four names; `pins.py`'s fingerprint and filter (off -> None; on -> keep the pinned and unchanged, drop and log the rest) driven with stand-in tools; agent.py's switches, the `_tool_filter` import-only-when-on, the `/health` keys and the one log call, and the `AGENT_FENCE` sentence off by default; the targets, `.PHONY`, `mk/README.md`, the 888 lines, both CI lines (with `fastmcp==3.4.7`) and these rows. Then, with libraries: the kit's agent over google-adk gets the filter only when on; `evil_mcp.py`'s tools over fastmcp are refused (the extra by name, the rug by fingerprint) while the honest four are kept; and, where the kit's MCP server imports (the local stack), `tool_pins.json` pins exactly its current tools. CI's agent-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## The agents' doors from make, the local MCP server, and the scrub on the Chat page (lesson 10.8)

Kit files the lesson 10.8 gaps PR adds that no page quotes yet. Lesson 10.8's page adopts them; the page pull request
removes the rows it adopts. Three gaps lesson 10.8's page named are closed (13 October 2026). `make attack-agents`
(`mk/agents.mk`, and `commands/attack-agents.sh`, which lesson 10.8's page quotes) runs the attack set's chat and Desk
rows on documind-chat with a token minted as `documind-ui-sa` for the chat service's canonical URL, the way `make
attack-eval` mints rag-api's, and the peer's row (`SURFACES=peer`: no token, no `PROJECT`) at a peer on your own
machine. `make mcp-local` serves the kit's MCP server in the local profile on `127.0.0.1:8000`, over acme's corpus in
the Chroma directory `make chat-local` seeds, so that peer reaches it with `MCP_AUTH=none`; the local profile has no
roster and takes a tenant the model names as given, so another tenant's question finds only what the store holds.
`services/frontend/chat.py`'s `_scrubbed_line()` says, on a line under an agent brain's caption, how many images,
tags or links documind-chat's `AGENT_SCRUB` replaced; with the count 0 or absent it shows nothing, so a lane with the
switch off sees the page it always saw. Both targets run only when called, and `mk/evaluation.mk`, whose attack
recipes lesson 4.9 quotes to its end, is unchanged.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_attack_agents.py` | **10.8** | Stdlib first: the two targets in `mk/agents.mk`, `.PHONY` and `mk/README.md`, the 888 lines, attack-agents's guard and what it hands the script, both CI lines and this row; `commands/attack-agents.sh` in bash against a stub gcloud and `test_attacks.py`'s stand-in chat service and peer on 127.0.0.1 (one mint as documind-ui-sa for the canonical URL, `DOCUMIND_ID_TOKEN` used instead, the peer added, the peer alone with no gcloud call and no token, an api surface refused, no project number, a leak exiting 1); `make mcp-local`'s seed and server opening one Chroma directory; and `_scrubbed_line()` run without Streamlit and placed under the caption. With fastmcp and uvicorn: the recipe's server command, run as written, lists the four pinned tools over the MCP wire with no token, and in process, over acme's chunks held in memory, answers acme's question and finds nothing for a named globex. CI's agent-pins steps run it with `DOCUMIND_REQUIRE_LIBS=1`. |

## Ingest reliability (lesson 8.4)

Kit files the ingest-reliability pull request adds that no page quotes yet (13 October 2026, from lesson 8.4's
review). Lesson 8.4's page adopts them; the page pull request removes the rows it adopts. The fixes themselves sit in
files pages already quote: the claim's lease (`idempotency.py`'s `retake_expired()`, `push()`'s `processing` branch),
the retired ids leaving the index on the walk and on `make retire` (`reconcile.py`'s `remove_vectors()`,
`mk/lifecycle.mk`, `terraform/reconcile.tf`), the backlog policy on `documind-ingest-push` (`terraform/alerts.tf`,
its row in `ops/runbooks.json`) and the lifecycle metric's verdicts. Plain bugs, so no switch: the worker answers as
before unless a claim is `processing`, and the backlog policy is declared on every lane, as `dlq_depth` is.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_ingest_reliability.py` | **8.4** | Stdlib with a stand-in Firestore, and pydantic for `push()`'s contracts (skipped without it; `DOCUMIND_REQUIRE_LIBS=1` fails instead): the lease's length from `eventarc.tf`, `lesson-12.5.sh` and `batch.tf`; held, retaken once, its last second, the batch job's lease, a claim that moved on, no clock; `claim()` unchanged; `push()` lifted out of `main.py` whole: a 409 inside the lease, the cut-off claim taken back and indexed after it, a batch claim acked, finished and queued claims as before; the walk's reingest for a cut-off claim; `remove_vectors()` over a stubbed index, `--retire` and the walk through `reconcile.main()`, nothing touched without an index, the index's name in the job and both make targets; the metric's verdicts against the worker's lines; the queued line naming `make batch-job` first. |

## ADK's planner on the ADK brain (lesson 10.2)

Kit files PR K-P10 adds that no page quotes yet. Lesson 10.2's page adopts them; the page pull request removes the rows
it adopts. One file that already exists changes: `services/chat/brains.py` reads `ADK_PLANNER` once at import (empty by
default) and, set to `plan_react`, gives the ADK brain ADK's `PlanReActPlanner`, assigned to the `LlmAgent` after it is
built and after the hand-off's lines, so every span lessons 5.7, 6.1 and 10.7 quote stays as it is. Its final-answer
join drops parts marked thought (the planner's plan and reasoning come back so marked), and a reply that is all plan
answers with a labelled line and the plan, never an empty answer. Lesson 10.1's page said nothing in the kit sets a
planner; it now names this switch. Off by default: a chat service without `ADK_PLANNER` answers every ADK turn as before.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_adk_planner.py` | **10.2** | Stdlib first: the switch read once at import and `plan_react` its one value; the assignment in the ADK brain alone, after the constructor and the hand-off's lines, with no thinking level named (lessons 5.7 and 6.1 assert it); the join that drops thought parts and its labelled fallback; both CI lines and this row. Then, in the chat image's pins (both chat-pins steps), the kit's ADK brain on a scripted model: LlmAgent's config neither frozen nor validated on assignment, and the planner set afterwards the one the flow reads (its instruction is in the request); a final answer without its plan or reasoning; a plan beside a call stored as thought and resent as plain text; a reply that is all plan labelled, never empty; unset, no planner and a plain reply as before; a thought part never in the answer; an unknown value warned about and ignored. |

## Two agents in a ping-pong, and the cap that ends it (lesson 10.7)

Kit files PR 10.7-D adds that no page quotes yet. Lesson 10.7's page adopts them; the page pull request removes the rows
it adopts. `commands/agent_shapes.py` (`make agent-shapes OFFLINE=1`, appended to `mk/agents.mk`) has no row: lesson
10.7's page quotes its `TransferCap` from the same pull request. `commands/agent-turn.sh`'s header names the new caller.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/tests/test_agent_shapes.py` | **10.7** | Stdlib first: `MAX_TRANSFERS = 3`, the `temp:` count and the plugin on the Runner's App; the target (`OFFLINE=1` the only mode, through `commands/agent-turn.sh`'s venv), the `.PHONY` entry and the 888 lines, the `mk/README.md` row, both CI lines and this row. Then, in the chat image's pins (both chat-pins steps), the shape on its scripted models: the ping-pong between the desks stopped after 3 transfers with the 4th refused, the cap's words as the answer and 4 model calls; with `disallow_transfer_to_peers` each desk offered only the root and the loop through the root, ended by the same cap; nothing of the count stored, and a second turn starting at the desk that spoke last and counting from one again; the printed report and `--offline` as the only mode. |

## The lane's own guards: build access, deferred views, down's region (lessons 0.3 and 0.4)

Kit files the end-to-end run of 20 October 2026 added after a new lane in an organization project stopped twice in
`make up` and a `make down` without `REGION=` deleted none of an asia-south1 lane's services. No page quotes them yet:
lesson 0.3's page adopts the first two (its recovery box for the build's 403 and its note on `bq-views` stay true, now
for a lane made before them), lesson 0.4's the third.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `mk/lane.mk` | **0.3** | Three one-line targets: `build-access` and `bq-views-when-ready` (both in `make up`'s list) and `down-region` (`make down-services` depends on it). |
| `commands/build-access.sh` | **0.3** | The recovery box's three grants to the default compute account, each skipped when present; the `_cloudbuild` bucket made first so it can carry its grant; 120 s for IAM only when a grant is new. |
| `commands/bq-views-when-ready.sh` | **0.3** | `make bq-views` when `documind_observability.run_googleapis_com_stdout` exists, otherwise one line saying to run it after `make smoke`. |
| `commands/down-region.sh` | **0.4** | STOP (exit 2) when the saved inputs name PROJECT in another region than REGION; passes when there are no saved inputs for PROJECT. |

## Citations reconciled with the answer, and the search mirror's own bucket (21 October 2026)

Tests for two kit changes from the end-to-end run: `resolve()` keeps one citation per chunk and adds one for every
source the answer cites only in its prose; the Vertex AI Search mirror stages its text in `<project>-search`
(`terraform/managed.tf`), not the audit bucket, and `stamp()` replaces `mirrored`. Pages 3.5 and 3.6 own the first.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `evals/tests/test_resolve_citations.py` | **3.5** | The two live failure shapes ([1, 2] with one entry; one chunk three times), out-of-range numbers and every marker form. |
| `commands/tests/test_search_mirror.py` | **7.4** | `Mirror.from_env` stages in `<project>-search` or `SEARCH_BUCKET`, never `AUDIT_BUCKET`; `stamp()` writes `mirrored` as field paths. |

## The Case Room, Phase 0: the full and final cases and the statutory floor (after Module 10, 25 October 2026)

Kit files the Case Room report's Phase 0 adds: a case set of thirty full and final settlements and the statutory floor
under them, drafted by a model for the author's review (`drafted_by: model`, `reviewed_by: null` on every case; nothing
in the floor is `checked`). No page quotes them yet: a read-ahead design page after lesson 10.11 adopts them, and Phase 1
(the offline Case Room, `commands/case_room.py`) builds on them. Nothing that exists changes, except one target name on
the Makefile's `.PHONY` line and a row in `mk/README.md`.

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `shared/ff_floor.py` | **after 10.11** | The statutory floor: 26 entries, 20 quoted from the corpus and held to their lines by `--selftest`, 5 resting on secondary sources by URL and 1 contested between them; the handbook bars by tenant; the dates the Codes and their Central Rules are reported to apply from (`desk_law.IN_FORCE` stays `None` until a person checks one); the states with final rules as of 1 October 2026. `--table` prints it for review. |
| `shared/ff_case.py` | **after 10.11** | A case's facts, its fact sheet (the "message" every calculator's `check_args` reads), the binding of each argument to the fact it stands for, the lines a case's facts call for and their statuses, the points a person decides and what is forbidden. |
| `evals/ff_cases.jsonl` | **after 10.11** | Thirty cases: twenty handed over, three that wait for a fact, two gate pauses, two refused openers, one rejection, one withdrawal and one company whose documents cover nothing. Every figure is recomputed by `make case-check`. |
| `evals/case_eval.py` | **after 10.11** | `--check` (Rs 0, standard library) and `--review` (the set and the floor as markdown). |
| `mk/casework.mk` | **after 10.11** | `make case-check`, `REVIEW=1` for the markdown. |
| `evals/tests/test_ff_cases.py` | **after 10.11** | Standard library: the set passes `--check` and counts its reviews; the sheet, the binding, the lines, the statuses and the opener rule; `--check` refusing a doctored figure, a status, a gated note, a point, a proposal, a set-off and an opener's own sign-off; the floor's selftest and table; the target, the `.PHONY` entry and the 888 lines, the `mk/README.md` row and this section. |

## The Case Room, Phase 1: the offline Case Room (after Module 10, 25 October 2026)

Kit files the Case Room report's Phase 1 adds on Phase 0's case set: one full and final case carried by a team of agents
on a typed board, from the facts a payroll person confirms to a signed hand-over to the payroll queue, offline and at
Rs 0, beside the same workflow with one agent (L+) and that agent alone (A*). No page quotes them yet: the design page
after lesson 10.11 adopts them, and Phase 2 runs them live. `evals/case_eval.py` (Phase 0's row) gains `--offline`,
`--replay` and `--compare`; `mk/casework.mk` gains `case-eval` and `case-tests`; `shared/ff_case.py`'s binding compares a
number by its value (a calculator tool's float 50.0 is the fact's 50).

| File | Owning lesson | Notes for whoever adopts it |
|---|---|---|
| `commands/case_room.py` | **after 10.11** | The roster (five model roles, five code agents), the board's zones and their one kind of writer, the registrar's rules, the treasurer's slices of an 80-call, Rs 40, 900 s budget, the lead's plan checked against the template, the scouts side by side and a deferred gather, the reckoner on the calculators alone, the clock keeper, the auditor's statuses, points and findings, the composer's slots, the payroll approver's seat as an interrupt, the hand-over; L+ and A*; the scripted model every role shares and the faults it plays by duty. `--offline --case <id> [--arm]` prints one run. |
| `commands/tests/test_case_room.py` | **after 10.11** | Stdlib first: the roster and its writers, the treasurer, `check_plan()`'s refusals, the registrar's rules on evidence, derivations, the draft and a sign-off, the door, a paused case's clocks, the auditor on every case, the slots and the draft check, the bench's scoring, the targets, the `.PHONY` entries and the 888 lines, both CI lines and these rows. Then, in the chat image's pins (both chat-pins steps), the three arms on the scripted model: the baseline case to a signed hand-over in 13 calls, the scouts side by side (a barrier), each fault in each arm, four eyes, a rejection, a withdrawal, the gate's pause with its clocks, a refused opener, a company with no document, a derived date never fed to a calculator, a budget that stops a case whole, a composer's digit and the lock, and `case_eval.py --offline`, `--replay` and `--compare`. |
