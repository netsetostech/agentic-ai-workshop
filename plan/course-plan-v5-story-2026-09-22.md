# Course plan v5 - DocuMind as a story told in 62 scenes (22 September 2026)

Merges the 18-module draft from user feedback (Table 2) with the v4 plan of 21 September. The 18 modules and
62 lessons of Table 2 are the spine; on 22 September 2026 two scenes were removed, 1.1 and 16.1, leaving 60; on 1 October 2026 two were added, 10.5 and 10.6, making 62. Every lesson below was checked against `code/` on 22 September
2026: the files, the make targets and the log lines named are the ones the kit has. Where a title in Table 2
promised something the code does not do, the scene is re-scoped and section 5 says why.

## 1. The story rule

DocuMind is built once, in order, and every lesson is a **scene** that adds one working piece and ends with a
proof the learner can see on screen. A module is a **chapter**; it opens with what DocuMind can do at its end,
and closes on a gate. Modules 1-14 are the whole working system (Core). Modules 15-18 extend it (Advanced) and
can be taken in any order after Core.

Every scene page has the same five parts, in this order - the four beats of v4 folded inside one lesson:

| Part | What it holds | v4 beat |
|---|---|---|
| Where we are | The master diagram with this scene's box lit; what DocuMind could do before this scene | Where |
| What we add, and why | The decision, the alternative rejected, the database or contract change, what it bills | Why |
| The code | The files, verbatim excerpts, the load-bearing lines | How |
| Prove it | One command or notebook cell, the exact line or number to see, the rupees | Do |
| What changed | DocuMind's new state in one paragraph, and the first line of the next scene | - |

A Core lesson is 90 minutes: about 25 for the first two parts, 35 for the code, 30 to prove it. Chapters 2, 4,
13, 14 and 18 are make-driven (Cloud Shell); the rest run from Colab against the learner's lane, with the Rs 0
lane as the fallback for chapters 1, 3, 10 and 12.

## 2. The seven acts

| Act | Chapters | What the learner can say at the end |
|---|---|---|
| I. Run it | 1, 2 | "It answers on my laptop for Rs 0, and my own lane is up, smoked and switched off." |
| II. Make it know things | 3, 4 | "A document becomes rows I can name; an update costs what changed and can be undone." |
| III. Make it answer | 5, 6, 7 | "The right chunks, a cited answer, an interface, and a gate that goes red." |
| IV. Make it safe and cheap | 8, 9 | "The tenant is who you are; a repeated question costs nothing and never goes stale." |
| V. Make it act | 10, 11, 12 | "Four brains over one tool, memory that survives a restart, and agents outside the kit." |
| VI. Run it for real | 13, 14 | "I can find why an answer was wrong, what it cost, ship without a key and roll back." |
| VII. Extend it (Advanced) | 15, 16, 17, 18 | "A graph, managed stores, media, a tuned model and my own GPU, each behind the same API." |

## 3. DocuMind at the end of each chapter

| Chapter | DocuMind can now... | Gate |
|---|---|---|
| 1 Setup - Run and understand DocuMind | answer "What is the notice period?" on the laptop, and the learner can draw both workflows on the master diagram | `make dryrun` green |
| 2 Deployment - Use the cloud lab safely | run as seven Cloud Run services on the learner's project, behind IAP, and switch off | `make smoke` green; `make off` floors to zero |
| 3 Ingestion - Turn documents into searchable evidence | turn one document into stamped rows in Firestore and datapoints in Vector Search | a row with every stamp; `vectorsCount` moved |
| 4 Lifecycle - Deliver, update and recover documents | take a re-issue for the price of the changed chunks, undo it free, and reconcile nightly | `make smoke-reindex` green |
| 5 Retrieval - Retrieve the right evidence | find the right chunks for the right tenant on four backends and say which rung found them | `make ablate` recorded; `make smoke` refuses a fallback answer |
| 6 Generation - Produce grounded answers and a usable interface | stream a cited, structured answer into the UI from an upload the learner made | upload to answer in the UI |
| 7 Evaluation - Measure quality and reject regressions | block a candidate that answers worse than the live revision | `make eval-live` green on a candidate |
| 8 Security - Verify identity, tenant isolation and safety | refuse the outsider, keep tenants apart, find a PAN, block an injection | isolation 1.00; a blocked prompt |
| 9 Caching - Cache without serving stale answers | answer a repeated question for Rs 0 and forget it when the corpus changes | the second ask costs Rs 0; a miss after reindex |
| 10 Agents - Build a tool-using agent | answer through four brains over one tool, refuse a blocked tool, route an employee's question to one desk and hand the law's cases to a person | `make smoke-chat`, `make smoke-cases`, `make smoke-desk` |
| 11 Memory - Persist and isolate conversation state | continue a conversation after a restart, never across a user or tenant | the restart check |
| 12 Protocols - Connect external agents through MCP and A2A | serve an agent it did not build, by one URL, and refuse the wrong tenant | `make smoke-mcp`, `make smoke-agent` |
| 13 Operations - Diagnose failures and control spending | explain a wrong answer, report rupees per tenant, degrade at 80 percent, sleep at 23:00 | `tenant_daily` in INR; zero instances after `make off` |
| 14 Release - Release, recover and demonstrate the project | ship from GitHub with no key, gate the exact candidate, roll back in two minutes, be defended | rollback timed; the rubric scored |
| 15 Graph - Graph and managed retrieval | walk a knowledge graph on Spanner and answer from RAG Engine or Vertex AI Search | `found_by: rag_engine`; status matches the ledger |
| 16 Multimodal - Multimodal evidence and media | cite the second of a clip; generate an image and read an answer aloud | `make smoke-media` |
| 17 Tuning - Managed fine-tuning | serve a model tuned on its own documents, judged against the live one | the tuned candidate passes `make eval-live` |
| 18 Serving - Model gateway and self-hosted inference | answer from Gemini, from a small model on an L4 or from vLLM, and be off by night | `make smoke-gateway`, `make smoke-slm`; zero GPU instances |

## 4. Table 2 against v4

| | Table 2 (yours) | v4 (mine) | v5 (this plan) |
|---|---|---|---|
| Modules / lessons | 18 / 62, Core 14 + Advanced 4 | 15 / 64, flat | 18 / 60, yours without 1.1 and 16.1 |
| Lesson identity | a verb-led task | a beat (Why / Where / How / Do) | your task titles; the four beats become the five parts inside every page |
| Ingest | two chapters (3 evidence, 4 lifecycle) | one five-lesson module | yours: two chapters of four |
| UI | inside generation (6.4) | inside identity (8.4) | yours: 6.4, the upload-to-answer journey |
| Guardrails | inside identity (8.3) | inside generation (5.x) | yours: 8.3 with DLP and audit |
| Agents | 10 brains + 11 state | one five-lesson module | yours: two chapters |
| Debugging a wrong answer | 13.1, new | absent | kept: the trail exists in the code (section 5) |
| Capstone | 14.4 | absent (deferred) | kept: `course-bibles/capstone-rubric.md` exists |
| Closing a session | 2.3 | inside 2.4 | kept: `session-restart.sh` + the saved plan + `make off` |
| Graph, managed stores | Advanced 15 | inside Retrieval 4.3-4.4 | yours |
| Small-model training | absent | 12.3 (flagged: no notebook in the kit) | yours: 18.2 serves a supplied or stock model; no training lesson |
| Batch lane (files over 250 pages) | absent | 3.2 / 3.5 | added to 4.1 |
| BigQuery chunk mirror, feature job, Dataplex scan | absent | 14.3 | added to 3.4 (the mirror) and 13.2 (the job and the scan) |
| Chapter end state and gate | absent | per module | kept, section 3 |
| Rupee line per scene | absent | per module | kept, in Prove it |

The count is 62: 49 Core at 90 minutes is 73.5 hours; the 13 Advanced scenes add 19.5. Module 3 as authored on 21 September
(five lessons: idempotent by design, bucket to row, bytes to rows, the ledger, the drills) maps onto chapters 3
and 4 here - 3.1 and 3.3 into chapter 3, 3.2 and 3.4 into chapter 4, the drills of 3.5 spread across 4.1-4.4 -
and is re-cut, not rewritten.

## 5. The scenes - Core

Each row: what the learner does · the code and targets it opens · the proof on screen. A scene marked **re-scoped**
differs from Table 2's title because the code says so; the reason is in section 6.

### Chapter 1 - Setup - Run and understand DocuMind

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 1.1 | Reproduce the local environment and read the master diagram | Clone the learner repo; Python, Terraform, gcloud, Docker; the tool checks; the corpus (thirteen real Acts, three tenants, invented PANs). The master diagram: upload to index (bucket, worker, four stores) and question to answer (UI, API, retriever, generator), and which box each later chapter lights up. Then the Rs 0 lane: Ollama `gemma3:4b` and a Chroma directory seeded with the same chunk ids Firestore gets. | `commands/session-restart.sh`, `evals/README.md`, `shared/profile.py`, `shared/local_corpus.py`, `make chat-local` | `curl localhost:8081/v1/chat` answers the notice-period question with citations, Rs 0 |
| 1.2 | Prove a first success and diagnose a first failure | `make dryrun`: the ten offline checks and the offline half of the eval gate. Then break one on purpose (loosen a `must_contain`, remove a pinned requirement), read the failure, repair it. | `validate.py`, `evals/run_eval.py` (offline), `.github/workflows/documind-dryrun.yml`, `golden.jsonl` | Ten PASS lines, one FAIL with its reason, green again |

### Chapter 2 - Deployment - Use the cloud lab safely

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 2.1 | Understand the project, identities and resource map | A throwaway project, billing, the APIs, ADC. The resource map: fourteen service accounts and per-account actAs, five buckets, Firestore with five indexes and three TTL fields, Vector Search, two Cloud SQL instances, Spanner, BigQuery, registry, VPC connector; what bills by the hour. | `make apis`, `commands/infrastructure.py prepare`, `terraform/sa.tf`, `variables.tf`, `storage.tf`, `firestore_indexes.tf`, `vector.tf`, `cloudsql.tf`, `spanner.tf`, `INFRASTRUCTURE.md` | `make plan` lists every resource; the learner names the account each of the seven services runs as |
| 2.2 | Review and start the prepared deployment | `make plan` (saved, reviewed, refuses deletes and replacements), then `make up`: images through Cloud Build, seven services, IAP on the UI, the roster, `wait-vectors`. | `commands/infrastructure.py plan / check / apply`, `Makefile up`, `cloudbuild.yaml`, `commands/lesson-12.*.sh` | Seven services listed; the UI opens behind IAP; the hourly items named with their rupees |
| 2.3 | Check readiness, save progress and close the session | `make preflight`, `make smoke`, `/ready` and `/version`. Save: the state bucket, the saved plan and inputs, the session keys `session-restart.sh` restores next weekend. Close: `make off` (floors to zero), `make down` (destroy) and what only project deletion removes. | `smoke/preflight.sh`, `smoke/smoke.py`, `commands/infrastructure.py` (saved inputs), `commands/session-restart.sh`, `make off`, `make down` | Smoke green; zero instances after `make off`; a restored session finds the same PROJECT and REGION |

### Chapter 3 - Ingestion - Turn documents into searchable evidence

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 3.1 | Understand source, tenant, page and chunk contracts | The three identities: the object path, the version hash (`doc_key = tenant_sha256`), the chunk (`tenant:sha256#i` for citations; `chunk_hash` and `locator` across versions). `IngestMessage` (tenant from the path, traversal refused), `DocumentContract`, the tenant-scoped id and the collision it fixed, `effective_from`. | `services/ingest/contracts.py`; notebook, Rs 0 | `chunk_hash` of a re-wrapped paragraph unchanged; a message at the bucket root refused with the field named |
| 3.2 | Parse documents and compare chunk boundaries | Document AI chosen by residency (OCR in asia-south1, Layout Parser in us), 15-page slices, pypdf's count first, `MAX_INLINE_PAGES` 250. Chunk by `## ` section against 2,000-character windows with 200 overlap cut at the form feed; the loader and the worker give the same chunks. | `parser.py`, `main.py` (`_pdf_pages`, `_parse`, `_chunk`), `shared/documind_corpus.py` | The notebook prints locators and hashes from both chunkers, identical (65 of 65 on a 29-page mirror) |
| 3.3 | Create and validate compatible embeddings | The regional client, `text-embedding-005`, `RETRIEVAL_DOCUMENT`, 768 dimensions, batches of 250 texts or 15,000 tokens; the stamp on every row and why an unstamped or differently-tasked vector is rejected; the sparse encoder shared with the query side; generation on `global`, embeddings regional. | `indexer.py` (`batches`, `embed_all`, `valid_vector`, `document_embedding_matches`), `shared/sparse_encoder.py`, `commands/tests/test_document_embeddings.py` | Three chunks embedded: 768 numbers each, the cost in paise; a legacy row fails the match |
| 3.4 | Write, inspect and verify indexed records | The Firestore row (`mirror_to_firestore`: text, vector, stamps, `staged`), the Vector Search datapoint (dense + sparse, restricts on tenant, kind, doc_type, current), the BigQuery `chunk_source` mirror when `BQ_CHUNK_TABLE` is set. Inspect a row; verify the index; repair the tier. | `indexer.py` (`mirror_to_firestore`, `to_datapoints`, `mirror_to_bigquery`, `backfill`), `make vector-status`, `commands/verify-vector-index.py`, `commands/check-firestore-fallback.py`, `make backfill-vectors` | A `chunks` row with every stamp; `vectorsCount` moves after `make ingest-one` |

### Chapter 4 - Lifecycle - Deliver, update and recover documents

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 4.1 | Follow upload events, retries, dead-letter handling and the batch lane **(re-scoped: the batch lane added)** | Bucket notification, topic, push subscription (OIDC as the worker, 600 s ack, backoff 10 s to 600 s, twelve attempts), the dead-letter topic; the HTTP-code rule (2xx acks, anything else retries); `make poison` and `make dlq`. Files over 250 pages: the queued claim and the batch job on the same image. | `terraform/eventarc.tf`, `batch.tf`, `main.py push()`, `batch.py`, `make poison / dlq / queued / batch / batch-job` | The `ingest_poison` line, then the message in `ingest-dlq-sub`; a queued claim drained by `make batch` |
| 4.2 | Reindex a changed section and measure embedding reuse | The claim in a transaction, then the carry-over by `chunk_hash`: `make reindex` of the handbook with one clause changed. | `idempotency.py` (`claim`, `finish`, `release`), `indexer.py` (`held_vectors`, `plan_carry_over`, `embed_with_carry_over`), `make reindex`, `evals/demo/` | `reused=281 embedded=2 retired=283` on the `ingest_ok` line; the notice-period answer moves from 60 to 90 days |
| 4.3 | Publish versions, retire documents and reject stale events | Staged rows flipped current in one pass, the old rows retired with `expire_at` (the TTL policy is the only deleter), the reader's newest-per-source guard; the generation guard; `make retire` and the three states `superseded` / `retired` / `withdrawn`. | `idempotency.py` (`swap_versions`, `retire_previous`, `stale_generation`, `withdrawn`), `contracts.is_stale`, `terraform/firestore_indexes.tf` (TTL), `make retire`, `make sources` | `ingest_stale_event` on a replayed older generation; `sources.status = withdrawn` after `make retire` |
| 4.4 | Restore documents and reconcile index differences | The verified undo (rows counted against the claim, age against the 30-day window), `make restore`, the reconcile plan and apply, the 23:30 job and its `drift`, `make backfill-current` for an older lane, the chapter gate. | `idempotency.reactivate`, `reconcile.py`, `reconcile.tf`, `make restore / reconcile / reconcile-job / backfill-current`, `smoke/smoke_reindex.py` | `ingest_reactivated ... embedded=0`, the answer back; `make smoke-reindex` green |

### Chapter 5 - Retrieval - Retrieve the right evidence

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 5.1 | Apply query embeddings and authorized filters | `embed_query` with the same declared model (`RETRIEVAL_QUERY`); the tenant from identity, never the request; `check_filters` (allowed keys, 400 otherwise); restricts on Vector Search; `RETRIEVAL_CURRENT_ONLY`, `prefer_current`, `newest_per_source`. | `retriever.py`, `rag-api/main.py` (`check_filters`, `retrieval_backend_for`), `config.py` | An unknown filter key answered 400; `stages.retrieval_backend` on the answer |
| 5.2 | Compare dense and hybrid retrieval | Sparse plus dense with reciprocal rank fusion: in-process for the Firestore rung, server-side on Vector Search; the ablation's arms, one knob each, no model in the loop. | `hybrid.py`, `shared/sparse_encoder.py`, `evals/ablate.py`, `make ablate` | recall@k, MRR and p95 per arm on the golden set |
| 5.3 | Rerank and inspect retrieved candidates | The reranker and its fallback (`rerank_fell_back`, the `rerank_fallback` event), the pool size on the usage row, `found_by` on every chunk; read a `stages` block end to end. | `retriever.rerank`, `main.py` (`usage_row`, `stage`) | p95 rerank milliseconds in `make usage`; a citation's `found_by` |
| 5.4 | Test fallback without losing tenant or metadata filters | Blank or undeploy the index: the Firestore rung answers with the same tenant predicate and the caller's equality filters (`vector_search_fallback`); the read-only probe; the smoke that refuses a vector deployment answering from Firestore; moving one tenant by hand. | `retriever._firestore_fallback`, `commands/check-firestore-fallback.py`, `Makefile smoke`, `make tenant-backend`, `make backfill-vectors` | `found_by: firestore` with the `doc_type` filter still applied; `make smoke` red until the tier is back |

### Chapter 6 - Generation - Produce grounded answers and a usable interface

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 6.1 | Pack evidence within the context budget | `TokenBudget`, most-relevant-first packing, the `[Source N]` header with the effective-from date, a token counter injected so tests need no cloud. | `context_budget.py` | The packed set for one question and the tokens it costs |
| 6.2 | Generate structured answers, citations and refusals | The one contract (`ModelDraft` resolved to `RAGAnswer` with real chunk ids), JSON out of the model, the refusal on an empty pool, generation on `global` and a tuned endpoint as a setting, INR at 85 on every answer. | `shared/documind_schemas.py`, `generator.py` (`generate`, `_client_for`), `cost.py`, `main.py empty_pool_answer` | `/v1/query` JSON with resolved citations; a refusal on an unanswerable question |
| 6.3 | Stream answers and handle failures | The SSE citation event; the guard holding tokens until the buffered answer is screened (`blocked_response`, 502); what each failure degrades to: `routing_fallback`, `rerank_fallback`, `semantic_cache_failed`, `budget_record_failed`, `telemetry_not_instrumented`. | `main.py /v1/stream`, `generator.generate_stream`, `telemetry.py` | A stream in curl; one forced fallback line in the log with the answer still served |
| 6.4 | Complete the Streamlit upload-to-answer journey | The Documents page writes the object as the UI's account, the worker ingests, the versions list reads `/v1/sources`, the chat page streams and renders citations; the UI never holds a model. | `services/frontend/documents.py`, `chat.py`, `citations.py`, `auth.py`, `app.py` | Upload in the UI, the version appears, a cited answer streams |

### Chapter 7 - Evaluation - Measure quality and reject regressions

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 7.1 | Build a useful evaluation dataset | The five shapes (lookup, join, refusal, isolation, version), `must_contain` and `must_retrieve`, the required rows, labelled paraphrase pairs, candidate rows generated from the quality-gated feed. | `evals/build_golden.py`, `golden.jsonl`, `required.json`, `paraphrases.jsonl`, `make_evalset.py`, `make make-evalset` | A new row written and accepted by the offline gate |
| 7.2 | Separate offline checks, live scoring and LLM judgment | The offline half in CI on every push; the live half against a no-traffic candidate with nine thresholds, fifteen required rows and two identities; the judge that scores groundedness, compares pairwise and reads trajectories but never gates. | `run_eval.py`, `judge.py`, `make eval / eval-live / judge`, `.github/workflows/documind-dryrun.yml` | `make eval` green; `make eval-live API=` numbers; `make judge` scores |
| 7.3 | Compare one controlled change against a baseline | A candidate revision with one setting changed, the scoped live gate, the pairwise judge against the live revision, the ablation for retrieval-only changes, the price of the difference. | `make candidate`, `make eval-live SOURCE=`, `make judge API_B=`, `make ablate`, `make usage` | A pairwise verdict and the rupee delta |

### Chapter 8 - Security - Verify identity, tenant isolation and safety

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 8.1 | Trace authenticated identity into tenant membership | IAP's signed assertion into one verifier with two legs (the forwarded assertion, or the caller's own ID token), the roster at `tenants/{id}/members/{email}`, the three `auth.py` files that share it, seven accounts on three rosters. | `shared/iap.py`, `shared/tenancy.py`, `rag-api/auth.py`, `admin/auth.py`, `frontend/auth.py`, `terraform/sa.tf`, `make roster` | The identity and tenant on a usage row; `tools/check_auth_wiring.py` green |
| 8.2 | Test valid access, denied access and cross-tenant requests | A member answered; no token refused (the smoke's fourth check); the outsider account admitted by IAM and refused by the roster (403, not 401); acme against zeta on the isolation rows; the tenant's data-residency policy. | `smoke/smoke.py`, `smoke/smoke_chat.py` (check 4), `run_eval.py` (isolation rows), `shared/tenancy.py` (`policy_for`), `make tenant-policy` | 401 and 403 lines side by side; isolation 1.00 in `make eval-live` |
| 8.3 | Exercise DLP, guardrails and audit behavior | One PII list for the worker and the admin console, findings without values in `dlp_findings`; Model Armor on both sides on a candidate, an injection in English and Hinglish; the audit event shape into the retention-locked bucket and the admin's audit tab. | `shared/pii.py`, `services/admin/dlp.py`, `rag-api/guard.py`, `terraform/model_armor.tf`, `make candidate ARMOR=on`, `shared/audit_log.py`, `services/admin/audit.py` | The invoice's PAN in the DLP tab; a 400 `prompt_blocked`; the upload in the audit tab |

### Chapter 9 - Caching - Cache without serving stale answers

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 9.1 | Compare context caching and answer caching | The explicit Gemini cache (4,096-token floor, 60-minute default, no maximum, storage by the hour, on `global`) against the semantic answer cache (a hit with its original citations at cost 0). | `cache_manager.py`, `cache_admin.py`, `semantic_cache.py`, `make cache`, `make candidate SEMANTIC_CACHE=on` | `cached_tokens` on the next usage row; `model_backend=cache` on the second ask |
| 9.2 | Test cache scope, configuration changes and freshness | What must match for a hit: tenant, the corpus fingerprint, the scope (filters, top_k, prompt version), the TTL; a reindex makes every earlier answer a miss (`cache_stale`); a changed filter or prompt version misses too. | `semantic_cache.scope_of`, `cache_manager.generate_config_kwargs`, `idempotency.refresh_fingerprint`, `make reindex` | The miss after `make reindex`; a hit again after `make cache` |
| 9.3 | Measure latency, avoided calls and false cache hits | The threshold measured on labelled paraphrase pairs (same fact, other words: a hit is right; a few words away with a different answer: a hit is wrong), p95 and cost with and without the caches. | `evals/cache_threshold.py`, `evals/paraphrases.jsonl`, `make usage` | The curve, the chosen threshold, the avoided calls in rupees |

### Chapter 10 - Agents - Build a tool-using agent

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 10.1 | Understand tool contracts and the direct agent loop | One `retrieve()` for every brain (the gate that forbids a second), the cost tool, the chat adapter that binds the tenant and ends in `search()`, where every brain's retrieve ends; the model-facing contract (two tools); the direct brain as the floor to compare against; two questions on one session, each turn with its own `tool_calls` and citations numbered from 1. | `shared/documind_tools.py`, `tools/check_one_retrieval.py`, `services/chat/tools.py` (`search`, `TOOLS`, `for_adk`), `brains.py` (`_summary`, `_turn`, `DirectBrain`) | A direct-brain answer with `retrieve` in `tool_calls`; a langchain reply with citations `n` = 1..k |
| 10.2 | Implement the main LangGraph workflow | The hand-built StateGraph: agent, tools, refuse; the checkpointer hook; the same four keys from every brain, for this turn only: `_turn()` gives the question an id that marks the turn's start, and a thread without it is an error. | `brains.py` (`LangGraphBrain`, `_turn`, `_summary`), `chat/agent.py` (`brain_for`), `commands/tests/test_chat_brains.py` | The refuse node fires on a blocked tool and the answer says so; the third turn's `tool_calls` hold only that turn's calls |
| 10.3 | Diagnose tool arguments, access failures and timeouts | Names refused before dispatch (`delete_document`, `send_email`, `modify_access`), a timeout per tool (two budgets), the tenant injected by the runtime and never filled by the model, refusals surfaced as error tool messages; an unknown tier an error result (`ToolException`), a timeout data and not a refusal, a failed token mint failing the turn. Enforced timeouts: a slow tool is abandoned at the smaller of its budget and the turn's time left, and the model reads a payload error. The turn's call cap, rupee cap and deadline stop a looping scripted model with a sentence, and the next turn answers; the rupee cap is named here and taught in 13.3. | `services/chat/tools.py` (`BLOCKED`, `TIMEOUTS`, the cost tool), `services/chat/limits.py` (`Meter`, `timed_tool_call`, `TurnLimitsMiddleware`), `chat/agent.py` (the tenant rule, the Meter), `brains.py` (`GuardMiddleware`), `make limits-check`, `make limits`, `make limits-drill STOP=model_calls` | `refusals` non-empty for the blocked, bad-argument and unknown-name calls; `refusals []` on the timed-out retrieve, with it in `limits.tool_timeouts`; the drill's HTTP 200 with `stopped_by` model_calls |
| 10.4 | Compare the LangChain and ADK adapters | `create_agent` with the guard as middleware; `LlmAgent` and `Runner` with one tool list adapted per framework (`for_adk`), the request through `REQUEST` and no identity in any schema the model reads; one error contract (`tool_failed`, `mark_error`), so equal refusals; the same thread; a new smoke session per run; the turn's limits wired three ways (one `wrap_model_call`, the hand-built agent node, ADK's model callbacks beside `RunConfig.max_llm_calls`), with `ModelCallLimitMiddleware` named as the off-the-shelf cap that adds two nodes; the four cost lines from the chat and rag-api rows, and the judge's trajectories. | `brains.py` (`LangChainBrain`, `AdkBrain`: `for_adk`, `REQUEST`, `tool_failed`, `mark_error`), `services/chat/limits.py`, `smoke/smoke_chat.py`, `services/frontend/chat.py`, `commands/tests/test_chat_brains.py`, `make smoke-chat`, `make judge CHAT_URL=` | Four brains and one `limits` block on `/health`; `make smoke-chat` 6 passed with citations from every brain; four cost lines from the rows |
| 10.5 | Hand a question to the person the law names | The hard gate (`desk_rules.gate()`): five classes found by rule, a first-person marker with a DISCLOSE pattern or an unframed PROCESS pattern, in English, Hindi and Hinglish, and never the words; one fixed reply per class (`desk_law.py`) at rag-api's door and the chat door, with model `none`, cost 0 and a `desk_gate` row that names the class only; checked Aadhaar and card numbers masked; `desk_gate` per tenant, refused until every office's Internal Committee has a member who can read its cases; roles (`roles_for`), queues and cases: a draft that expires in 30 minutes, one client token one case, a POSH case with no text for the chosen members, 404 for everyone else, a case reference as the audit actor; the hourly overdue scan. | `shared/desk_rules.py`, `shared/desk_law.py`, `services/rag-api/desk_door.py`, `services/chat/desk.py`, `shared/roles.py`, `shared/cases.py`, `services/frontend/desk.py`, `services/chat/desk_overdue.py`, `terraform/desk.tf`, `make desk`, `make desk-queues`, `make roles`, `make desk-operators`, `make desk-job`, `make cases`, `make cases-overdue`, `make smoke-cases` | A POSH disclosure through `/v1/stream` returns the fixed template with model `none` and cost 0; a confirmed grievance case in the committee's inbox |
| 10.6 | Route each question to one specialist agent | The doc_type registry: each stored version's class, pinned to its `doc_key` (`doc_types.assign()`, the worker's hook), and the relabel that applies it to Firestore, Vector Search, Vertex AI Search, BigQuery and the answer cache; the route table (`DESKS`), each desk's classes, roles and chip; `decide()`'s cascade: who, the gate, the masking, a draft, single mode, a chip, the anchors at Rs 0, then flash-lite on `global` with an enum-only schema beside a k=7 vote over the tenant's exemplar index, accepted by rules D, A, B and C or settled by flash at thinking LOW, with clarify and the fallback, never an error; the desk graph (`dispatch`, `Command(goto=)`, `next_part`) and the statute desk's in-force lines; `POST /v1/desk` and the eval's `POST /v1/route`; shadow mode; the route eval's dev split, whose figures are an upper bound, and its thresholds, starting values until people write the dev and test rows. | `shared/doc_types.py`, `services/ingest/relabel.py`, `services/chat/desk_routes.py`, `services/chat/desk_router.py`, `services/chat/desk_graph.py`, `shared/desk_law.py` (`in_force_lines`), `services/chat/desk.py`, `services/frontend/desk.py`, `evals/route_eval.py`, `make doc-types`, `make route-index`, `make desk DESK_ROUTE=`, `make roles`, `make smoke-desk`, `make route-eval SPLIT=dev` | `make route-eval SPLIT=test` passes every escalation row (waits for the people-written test split); a cited handbook answer and a statute answer with its in-force line on the Desk page |

### Chapter 11 - Memory - Persist and isolate conversation state

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 11.1 | Distinguish agent state, conversation history and knowledge | The checkpointer's state (LangGraph), ADK's session, the corpus; `CHECKPOINT_DSN=memory` and the log line that says conversations die with the instance. | `chat/agent.py` (docstring, `build_checkpointer`, `lifespan`), `brains.py` | The warning line on a memory checkpointer |
| 11.2 | Configure and inspect durable conversation storage | Cloud SQL (a small zonal instance, a password that lives only in state and Secret Manager, the DSN secret), the migration as a one-off job, the checkpoint tables, ADK's session service on the same instance. | `terraform/cloudsql.tf`, `services/chat/migrate.py`, `commands/lesson-12.8.sh` | The checkpoint tables exist; one row per thread |
| 11.3 | Verify restart recovery and session isolation | The thread id is `tenant:user:session`, prefixed by the server; the same session continues on whichever instance answers; another user's session id finds nothing; the outsider is 403 from the roster. | `chat/agent.py` (`thread_config`, `caller`), `smoke/smoke.py` (the restart check with `DOCUMIND_CHAT_URL`), `smoke/smoke_chat.py` | The conversation continues after a redeploy; a second user cannot read it |

### Chapter 12 - Protocols - Connect external agents through MCP and A2A

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 12.1 | Expose, discover and invoke MCP tools | FastMCP, four tools, stateless streamable HTTP, the tenant from identity and roster never from an argument, the profile switch that runs it on the Rs 0 lane. | `services/mcp/server.py`, `make chat-local` | `tools/list` names four tools; `retrieve` answers from a local client |
| 12.2 | Deploy MCP and verify authorized access | The service with its own account on the rosters, an ID token minted for its URL, the four smoke checks including the refusal; Claude Desktop or an ADK client connected. | `commands/lesson-7.2.sh`, `services/mcp/Dockerfile`, `smoke/smoke_mcp.py`, `make smoke-mcp` | `make smoke-mcp` green; another tenant refused by the server |
| 12.3 | Trace the implemented A2A peer and its permissions | An agent outside the kit: `LlmAgent` over `McpToolset`, a fresh token on every tool call, an agent card and JSON-RPC, no `shared/` imports; who may invoke it. | `services/agent/agent.py`, `agent/Dockerfile`, `terraform/sa.tf` (`run.invoker`), `commands/lesson-8.4.sh`, `smoke/smoke_agent.py` | The card refused without a token; `message/send` completes; `make smoke-agent` green |

### Chapter 13 - Operations - Diagnose failures and control spending

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 13.1 | Debug a wrong answer through the complete pipeline | The trail an answer leaves: `stages` (backend, vector chunks, pool), `found_by` per citation, the fallback events, which version answered (`make sources`), `cache_stale`, the judge's groundedness, the ablation's miss list, the two read-only probes. | `main.py usage_row`, `make sources`, `make judge`, `make ablate`, `commands/check-firestore-fallback.py`, `commands/verify-vector-index.py` | A wrong answer traced to a stale version, a fallback rung or a pool too small |
| 13.2 | Reconcile usage events, reports and alerts | The usage row into Cloud Logging, the sink into BigQuery, the daily view, the usage tool's grouping (tenant, model, backend, brain, surface; p95 per stage), the admin console's five tabs, the log metrics and alert policies; the chunk feature job and the Dataplex scan. | `evals/usage_rows.py`, `terraform/sink.tf`, `sql/tenant_daily.sql`, `make bq-views`, `services/admin/admin_dashboard.py`, `terraform/alerts.tf`, `dataplex.tf`, `sql/chunk_metadata.sql`, `make features` | `tenant_daily` rows in INR equal `make usage`'s totals; an alert tripped by the DLQ |
| 13.3 | Exercise model routing, budgets and shutdown controls | Routing by complexity, the breaker at 80 and 100 percent with the month's counter in Firestore and the `SPEND_PCT` replay, the billing budget, the GPU quota cap, the 23:00 job, `make off` and `make down`. | `rag-api/router.py`, `breakers.py`, `budget.py`, `terraform/budget.tf`, `quota.tf`, `services/slm/gpu_quota.py`, `terraform/off.tf`, `make candidate ROUTING=on`, `make gpu-cap`, `make off / off-now / down` | The model tier changes at 85 percent; zero instances after `make off` |

### Chapter 14 - Release - Release, recover and demonstrate the project

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 14.1 | Build and deploy using keyless identity | Workload Identity Federation pinned to the repository id and branch, the org policy that forbids keys, Cloud Build from the `code/` context, the CD workflow. | `terraform/wif.tf`, `org_policy.tf`, `cloudbuild.yaml`, `.github/workflows/documind-cd.yml`, `make build` | A build and a deploy with no service-account key anywhere |
| 14.2 | Evaluate and gate the exact candidate revision | A no-traffic revision by name, the live gate against its URL, the workflow's eval-gate job; promotion by revision name, never "latest". | `make release-candidate GIT_SHA=`, `make eval-live API=`, `.candidate-revision`, `documind-cd.yml` (`eval-gate`) | The candidate URL judged; the recorded revision name |
| 14.3 | Promote, roll back and repair a controlled failure | Promote; ship a candidate with a wrong setting and watch the gate refuse it; promote a bad one on purpose and roll back to the recorded previous revision; seven smokes as one; Cloud Deploy's canary as the other path. | `make promote`, `make rollback`, `.previous-revision`, `make smoke-all`, `terraform/clouddeploy.tf`, `run-service.yaml` | Rollback timed under two minutes; `make smoke-all` green after |
| 14.4 | Complete the independent capstone and operational handover | The eight components and the published rubric; one lane extended on the learner's fork; the runbook (what pages, what the night job floors, what `make down` removes); the 90-minute defence. | `course-bibles/capstone-rubric.md`, the learner's fork, `README.md` (Tier B checklist) | The five rubric criteria scored; the runbook handed over |

## 6. The scenes - Advanced

### Chapter 15 - Graph - Graph and managed retrieval

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 15.1 | Build graph evidence from source documents | Entities and relations stated in the passage, never inferred; surface forms resolved by embedding at 0.92; nodes and edges from the tenant's current chunks. | `services/ingest/graph.py`, `make graph TENANT=acme` | Node and edge counts; one edge read back with its source chunk |
| 15.2 | Compare Firestore and Spanner graph paths | The Firestore graph seeded by a name the question contains; the Spanner graph (interleaved edges, an `embedding` column) seeded by meaning with cosine distance; the walk in front of the dense pool on a candidate. | `shared/documind_graph.py`, `terraform/spanner.tf`, `make graph GRAPH_BACKEND=spanner`, `make candidate RETRIEVAL_GRAPH=auto GRAPH_BACKEND=spanner` | The CFO question answered without the word CFO; `/version` reports the graph backend |
| 15.3 | Configure and query managed retrieval mirrors | RAG Engine and Vertex AI Search as mirrors of the ledger's current versions, for tenants whose policy allows a copy outside India; one tenant pinned to each backend. | `services/ingest/managed.py`, `terraform/managed.tf`, `make rag-engine-enable`, `make rag-corpus`, `make tenant-backend RETRIEVAL_BACKEND=rag_engine`, `make tenant-policy DATA_REGION=any` | `found_by: rag_engine` on a citation; `mirror_policy_skipped` for an `in` tenant |
| 15.4 | Compare quality and test update/withdrawal freshness | The ablation with the managed arm; a reindex followed by `mirror_ok`; a retirement followed by the store's delete; the undo re-mirrored from the rows; the stores held against the ledger. | `make ablate ABLATE_ARGS="--arms all"`, `managed.py` (`after_swap`, `after_undo`, `retired`), `make managed-status`, `make retire / restore` | `make managed-status` matches the ledger after a reindex, an undo and a withdrawal |

### Chapter 16 - Multimodal - Multimodal evidence and media

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 16.1 | Query a video clip and validate media citations | The media set built and ingested (`make media MEDIA_ARGS=--video` draws the figures and synthesises the town-hall clip; `make ingest-corpus` sends them through the worker's media path, where Gemini describes them and the pixels are DLP-scanned first). Segments of at most 60 seconds with `start` and `end`, the citation that opens the clip at its second, the `mm-` golden rows and the media-kind rate. | `make media MEDIA_ARGS=--video`, `frontend/citations.py`, `shared/documind_schemas.py`, `run_eval.py` (`media_kind_rate`), `make smoke-media` | `[Clip 2, 03:20]` in the answer and the video at that second; `make smoke-media` green |
| 16.2 | Exercise implemented Studio and voice features | Image generation checked against the roster and metered as `event=media`, a signed upload URL so a 40 MB video is an ingest, speech cached by the hash of voice and text, transcription from the microphone. | `rag-api/media.py`, `frontend/studio.py`, `frontend/voice.py`, `terraform/storage.tf` (`media`, `tts_cache`) | A generated image and its usage row; an answer read aloud |

### Chapter 17 - Tuning - Managed fine-tuning

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 17.1 | Decide whether tuning is justified and prepare data **(re-scoped: the decision is a rubric on chapter 7's numbers)** | What must already be true (a gate and a judge that agree the answers are wrong for a reason a prompt or a cache cannot fix), then one question and answer per real chunk in the citation grammar, frozen with a manifest in the datasets bucket. | `evals/make_trainset.py`, `make trainset`, `evals/sft/*.manifest.json` | The frozen manifest and its row count |
| 17.2 | Validate sanitized datasets and run managed tuning | The self-test on fixtures, PII redacted, every golden question excluded, the Vertex and chat formats; the managed job, regional, billed per training token; the endpoint served from the location its path names. | `make_trainset.py --selftest`, `evals/tune.py`, `make tune`, `generator.py` (`_endpoint_location`) | The tuning job id; the endpoint path with its location |
| 17.3 | Compare the tuned candidate with an uncontaminated baseline | The endpoint as a setting on a candidate, the scoped live gate, the pairwise judge against the live revision, the price of the difference; why the golden set never entered the training data. | `make candidate GENERATOR_MODEL=<endpoint path>`, `make eval-live API=`, `make judge API_B=`, `make usage` | The pairwise verdict and the rupee delta |

### Chapter 18 - Serving - Model gateway and self-hosted inference

| # | Scene | What the learner does | Code and targets | Proof |
|---|---|---|---|---|
| 18.1 | Trace and authorize gateway routes | One door for every model with the caller's ID token as the key and no master key; the routes; the sensitivity classifier sending restricted text to the self-hosted route with no fallback; the token proxy that mints a token per call. | `services/litellm/config.yaml`, `documind_router.py`, `documind_classifier.py`, `token_proxy.py`, `gcp_id_token.py`, `terraform/gateway.tf`, `make deploy-gateway`, `make smoke-gateway` | A PAN re-routed; the cost header on a completion |
| 18.2 | Serve a supplied or stock model using Ollama | The image built from a supplied GGUF with a Modelfile generated from its tokenizer, or from a stock model; an L4 at min 0 / max 1 with a startup probe; the API behind the gateway pointed at it on a candidate. | `services/slm/Dockerfile`, `make_modelfile.py`, `make deploy-slm` (`SLM_STOCK=gemma3:4b`), `make smoke-slm`, `make candidate MODEL_BACKEND=gateway GENERATOR_MODEL=documind-slm` | The cold start timed; a gated answer from the small model |
| 18.3 | Inspect the vLLM service and the GKE alternative **(re-scoped: optional, not "verified")** | The FastAPI over `AsyncLLMEngine` (tiered keys, rate limits, `/classify`, `/extract`, SSE); the 13 GB image and the Hugging Face token; the cluster Terraform provisions by default (a Standard CPU node) and the GPU pool that needs `gke_autopilot=true`, quota and a cluster replacement. | `services/gemma-vllm/*`, `terraform/gke.tf`, `gke/vllm-deployment.yaml`, `gke/README.md`, `make build-vllm deploy-vllm`, `make gke-up / gke-down` | The manifest read and the duty-cycle sum done; the route answering only where GPU quota exists |
| 18.4 | Compare actual backends and verify shutdown behavior | The same golden questions on every backend and the four numbers; the quota cap under every `--max-instances`; the alarm for a GPU left warm; the night job; the switches. | `services/slm/compare_backends.py`, `make compare`, `make gpu-cap`, `terraform/alerts.tf` (`gpu_left_warm`), `terraform/off.tf`, `make slm-off / vllm-off` | The comparison table; zero GPU instances at the end |

## 7. Where the code changed a title

Checked on 22 September 2026. Nothing below is an assumption; each row names the file. Decided the same day: 1.1 and 16.1 removed; 4.1, 3.4, 17.1 and 18.3 accepted as re-scoped; the rest are clarifications that change no title.

| Scene | Table 2 said | What the code does | What v5 does | Status (22 Sept) |
|---|---|---|---|---|
| 1.1 | Explore the finished application and its two main workflows | Locally there is no UI and no upload path: `make chat-local` serves only the chat API on port 8081 over a pre-seeded Chroma directory; the upload workflow needs the bucket, Pub/Sub and the worker (`Makefile chat-local`, `frontend/documents.py`). | 1.1 runs on the instructor's demo lane with the learner on a roster (`make roster`), or as a recorded tour; the learner's own lane arrives in chapter 2. Decision needed: which. | Removed |
| 2.3 | Save progress | "Progress" in the kit is three things: the Terraform state bucket, the saved plan and inputs `infrastructure.py` keeps, and the session keys `commands/session-restart.sh` restores (it never resumes or deploys by itself). | The scene names all three and ends on `make off` / `make down`. | Clarified |
| 4.1 | Upload events, retries and dead-letter handling | `eventarc.tf` allows twelve delivery attempts, not five; files over 250 pages leave the push path for a Cloud Run job (`batch.py`, `batch.tf`). | Twelve attempts stated; the batch lane added to the scene. | Accepted |
| 3.4 | Write, inspect and verify indexed records | The worker also mirrors rows into BigQuery `chunk_source` when `BQ_CHUNK_TABLE` is set (`indexer.mirror_to_bigquery`, `dataplex.tf`). | The mirror added; the feature job and scan go to 13.2. | Accepted |
| 11.3 | Verify restart recovery and session isolation | The thread id is `tenant:user:session`, server-prefixed (`chat/agent.py thread_config`); the restart check lives in `smoke/smoke.py` (with `DOCUMIND_CHAT_URL`), and `smoke_chat.py`'s fourth check is the outsider's 403. | Both named as the proof. | Clarified |
| 16.1 | Ingest a figure or scanned page | Two different paths: an image goes to Gemini for a caption (`_describe_media`); a scanned PDF goes to Document AI, and `RESIDENCY` decides between Enterprise OCR in asia-south1 and Layout Parser in us (`parser.py`). | Both paths named; the scanned Gazette (`evals/corpus/acme/posh_act_2013.pdf`, no text layer) is the fixture. | Removed |
| 17.1 | Decide whether tuning is justified | No decision tool exists in the kit; the evidence is chapter 7's gate and judge numbers and `make usage`. | The decision is a rubric on those numbers, then `make trainset`. | Accepted |
| 18.2 | Serve a supplied or stock model | The kit holds the Ollama image, the Modelfile generator and the `SLM_STOCK` stand-in; it holds no training notebook for the GGUF. | Kept as written; no training scene anywhere in v5 (v4's 12.3 is dropped). | Clarified |
| 18.3 | Inspect and run the verified vLLM/GKE alternative | vLLM is optional (a 13 GB image, a Hugging Face token); `gke.tf` defaults `gke_autopilot=false`, a Standard CPU node that cannot schedule the L4 manifest; the GPU pool needs Autopilot, quota and a cluster replacement; `README.md` says the one-shape `make up` has not run live end to end. | "Verified" dropped; the scene inspects both and runs them only where GPU quota exists. | Accepted |

## 8. Decisions this plan needs

1. **Module 3 as authored on 21 September**: re-cut its five lessons into chapters 3 and 4 of v5 (the content
   maps one to one), or keep v4's Module 3 as the reference implementation of the scene format.
2. **The manifest**: `course-manifest.json` carries v3 numbering with a v4 Module 3; v5 renumbers everything.
3. **Time per Core lesson**: 90 minutes as here, or the 60 / 60 / 90 / 120 mix v4 proposed per beat.
4. **React**: unchanged from v4 - the UI is Streamlit; 6.4 teaches it as is.
