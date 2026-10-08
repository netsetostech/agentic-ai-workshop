# DocuMind course roadmap - 18 chapters, 62 scenes, in the order to build them (22 September 2026)

The working plan for authoring and running the course from v5 (`course-plan-v5-story-2026-09-22.md`, which holds
the files, make targets and proofs per scene). Follow it top to bottom. A scene is done when its six files exist,
pass the checker and its proof has been rehearsed once on a live lane. A chapter is done when its gate is green.

## How to follow it

- **Order.** Phase 0 first. Then chapters 1 to 14 in order (Core, one working system). Then 15 to 18 in any order (Advanced).
- **A scene page has five parts:** Where we are, What we add and why, The code, Prove it, What changed.
- **Six files per scene:** `README.md`, the main page, the practice lab, the live session, the interview Q&A, and a fifth
  file - a Colab notebook in the Colab chapters, a Cloud Shell runbook in the make-driven chapters (2, 4, 13, 14, 18).
- **The authoring loop, per chapter:** one brief (template, voice, sources, a per-scene outline); one writer per scene, in
  parallel; the checker (structure, verbatim code, real make targets, clean notebooks); a human read of every main page;
  one pull request per chapter; the proofs rehearsed on a live lane before the chapter is marked Done.
- **Status:** Not started, Drafted, In review, Done. Chapters 3 and 4 start as Drafted: the five lessons authored on
  21 September under v4 numbering (`Module 3/`) hold their content and are re-cut, not rewritten.

## Phase 0 - before any authoring

- [ ] Rehearse `make up` end to end on a throwaway project and record what breaks. The kit's README says the one-shape apply has not run live; every chapter from 2 on is written against its outputs.
- [ ] Renumber `course-manifest.json` to v5 (18 modules, 60 lessons) and create the folder skeleton, one `README.md` per scene.
- [ ] Re-cut the authored Module 3 into chapters 3 and 4 (v4 3.1 and 3.3 into chapter 3; v4 3.2, 3.4 and 3.5 into chapter 4).
- [ ] Rename `deploy/` to `code/` in the tools (`build_learners.py`, `check_contract.py`, `check_auth_wiring.py`, `deploy_index.py`) and re-mirror the kit to the learner repo, so the notebooks' clone matches the code.
- [ ] Land the four kit fixes found while authoring Module 3: the reindex smoke's tenant filter, the seeder's embedding stamp, the stale comments (attempts, poison ack, page count, cache record), the learner mirror.
- [ ] Generalise the Module 3 checker to every chapter and run it in the dryrun workflow.
- [ ] Confirm the two standing choices: 90 minutes per Core scene; Streamlit stays the UI.

## Act I - Run it

### Chapter 1 - Setup - Run and understand DocuMind (Colab · gate: `make dryrun` green)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 1.1 | Reproduce the local environment and read the master diagram | the Rs 0 lane answers the notice-period question with citations | notebook | Not started |
| 1.2 | Prove a first success and diagnose a first failure | ten PASS lines, one FAIL with its reason, green again | notebook | Not started |

### Chapter 2 - Deployment - Use the cloud lab safely (Cloud Shell · gate: `make smoke` green, `make off` floors to zero)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 2.1 | Understand the project, identities and resource map | `make plan` lists every resource; each service's account named | runbook | Not started |
| 2.2 | Review and start the prepared deployment | seven services up; the UI behind IAP | runbook | Not started |
| 2.3 | Check readiness, save progress and close the session | smoke green; zero instances after `make off`; a restored session | runbook | Not started |

## Act II - Make it know things

### Chapter 3 - Ingestion - Turn documents into searchable evidence (Colab · gate: a row with every stamp; `vectorsCount` moved)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 3.1 | Understand source, tenant, page and chunk contracts | a re-wrapped paragraph keeps its hash; a root-level object refused | notebook | In review |
| 3.2 | Parse documents and compare chunk boundaries | 65 identical chunks from both chunkers | notebook | In review |
| 3.3 | Create and validate compatible embeddings | three 768-number vectors and the cost in paise; a legacy row rejected | notebook | In review |
| 3.4 | Write, inspect and verify indexed records | a `chunks` row with every stamp; `vectorsCount` moves | notebook | In review |

### Chapter 4 - Lifecycle - Deliver, update and recover documents (Cloud Shell · gate: `make smoke-reindex`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 4.1 | Follow upload events, retries, dead-letter handling and the batch lane | `ingest_poison`, then the message in the DLQ; a queued claim drained | runbook | Drafted |
| 4.2 | Reindex a changed section and measure embedding reuse | `reused=281 embedded=2 retired=283`; the answer moves | runbook | Drafted |
| 4.3 | Publish versions, retire documents and reject stale events | `ingest_stale_event`; `withdrawn` after `make retire` | runbook | Drafted |
| 4.4 | Restore documents and reconcile index differences | `ingest_reactivated ... embedded=0`; `make smoke-reindex` green | runbook | Drafted |

## Act III - Make it answer

### Chapter 5 - Retrieval - Retrieve the right evidence (Colab · gate: ablation recorded; `make smoke` refuses a fallback answer)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 5.1 | Apply query embeddings and authorized filters | an unknown filter key answered 400; `stages.retrieval_backend` on the answer | notebook | Not started |
| 5.2 | Compare dense and hybrid retrieval | recall@k and MRR per arm on the golden set | notebook | Drafted |
| 5.3 | Rerank and inspect retrieved candidates | p95 rerank in `make usage`; `found_by` on a citation | notebook | Drafted |
| 5.4 | Test fallback without losing tenant or metadata filters | `found_by: firestore` with the filter still applied | notebook | Drafted |

### Chapter 6 - Generation - Produce grounded answers and a usable interface (Colab · gate: upload to answer in the UI)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 6.1 | Pack evidence within the context budget | the packed set for one question and its tokens | notebook | Drafted |
| 6.2 | Generate structured answers, citations and refusals | resolved citations; a refusal on an unanswerable question | notebook | Drafted |
| 6.3 | Stream answers and handle failures | a stream; one forced fallback line with the answer still served | notebook | Drafted |
| 6.4 | Complete the Streamlit upload-to-answer journey | upload, the version listed, a cited answer streams | notebook | Drafted |

### Chapter 7 - Evaluation - Measure quality and reject regressions (Colab · gate: `make eval-live` green on a candidate)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 7.1 | Build a useful evaluation dataset | a new row accepted by the offline gate | notebook | Drafted |
| 7.2 | Separate offline checks, live scoring and LLM judgment | `make eval` green; live numbers; judge scores | notebook | Drafted |
| 7.3 | Compare one controlled change against a baseline | a pairwise verdict and the rupee delta | notebook | Drafted |

## Act IV - Make it safe and cheap

### Chapter 8 - Security - Verify identity, tenant isolation and safety (Colab · gate: isolation 1.00; a blocked prompt)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 8.1 | Trace authenticated identity into tenant membership | the identity and tenant on a usage row | notebook | Drafted |
| 8.2 | Test valid access, denied access and cross-tenant requests | 401 and 403 side by side; isolation 1.00 | notebook | Drafted |
| 8.3 | Exercise DLP, guardrails and audit behavior | the PAN in the DLP tab; `prompt_blocked`; the upload in the audit tab | notebook | Drafted |

### Chapter 9 - Caching - Cache without serving stale answers (Colab · gate: the second ask costs Rs 0; a miss after reindex)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 9.1 | Compare context caching and answer caching | `cached_tokens` on a row; `model_backend=cache` on the second ask | notebook | Drafted |
| 9.2 | Test cache scope, configuration changes and freshness | the miss after `make reindex`; a hit again after `make cache` | notebook | Drafted |
| 9.3 | Measure latency, avoided calls and false cache hits | the threshold curve and the avoided calls in rupees | notebook | Drafted |

## Act V - Make it act

### Chapter 10 - Agents - Build a tool-using agent (Colab · gate: `make smoke-chat`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 10.1 | Understand tool contracts and the direct agent loop | `retrieve` in `tool_calls` | notebook | Drafted |
| 10.2 | Implement the main LangGraph workflow | the refuse node fires on a blocked tool | notebook | Drafted |
| 10.3 | Diagnose tool arguments, access failures and timeouts | `refusals` non-empty; a timed-out tool reported | notebook | Drafted |
| 10.4 | Compare the LangChain and ADK adapters | four brains on `/health`; four cost lines | notebook | Drafted |
| 10.5 | Hand a question to the person the law names | a POSH disclosure through `/v1/stream` returns the fixed template with model `none` and cost 0; a confirmed grievance case in the committee's inbox | notebook | Drafted |
| 10.6 | Route each question to one specialist agent | `make route-eval SPLIT=test` passes every escalation row; a cited handbook answer and a statute answer with its in-force line on the Desk page | notebook | Drafted |

### Chapter 11 - Memory - Persist and isolate conversation state (Colab · gate: the restart check)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 11.1 | Distinguish agent state, conversation history and knowledge | the memory-checkpointer warning line | notebook | Drafted |
| 11.2 | Configure and inspect durable conversation storage | the checkpoint tables; one row per thread | notebook | Drafted |
| 11.3 | Verify restart recovery and session isolation | the conversation continues after a redeploy; another user finds nothing | notebook | Drafted |

### Chapter 12 - Protocols - Connect external agents through MCP and A2A (Colab · gate: `make smoke-mcp`, `make smoke-agent`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 12.1 | Expose, discover and invoke MCP tools | `tools/list` names four; `retrieve` from a local client | notebook | Drafted |
| 12.2 | Deploy MCP and verify authorized access | `make smoke-mcp` green; another tenant refused | notebook | Drafted |
| 12.3 | Trace the implemented A2A peer and its permissions | the card refused without a token; `message/send` completes | notebook | Drafted |

## Act VI - Run it for real

### Chapter 13 - Operations - Diagnose failures and control spending (Cloud Shell · gate: `tenant_daily` in INR; zero instances after `make off`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 13.1 | Debug a wrong answer through the complete pipeline | a wrong answer traced to its cause | runbook | Drafted |
| 13.2 | Reconcile usage events, reports and alerts | `tenant_daily` equals `make usage`; an alert tripped | runbook | Drafted |
| 13.3 | Exercise model routing, budgets and shutdown controls | the tier changes at 85 percent; zero instances after `make off` | runbook | Drafted |

### Chapter 14 - Release - Release, recover and demonstrate the project (Cloud Shell · gate: rollback timed; the rubric scored)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 14.1 | Build and deploy using keyless identity | a build and a deploy with no key | runbook | Not started |
| 14.2 | Evaluate and gate the exact candidate revision | the candidate judged; its name recorded | runbook | Not started |
| 14.3 | Promote, roll back and repair a controlled failure | rollback under two minutes; `make smoke-all` green | runbook | Not started |
| 14.4 | Complete the independent capstone and operational handover | the five rubric criteria scored | runbook | Not started |

## Act VII - Extend it (Advanced)

### Chapter 15 - Graph - Graph and managed retrieval (Colab · gate: `found_by: rag_engine`; status matches the ledger)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 15.1 | Build graph evidence from source documents | node and edge counts | notebook | Drafted |
| 15.2 | Compare Firestore and Spanner graph paths | the CFO question answered without the word CFO | notebook | Drafted |
| 15.3 | Configure and query managed retrieval mirrors | `found_by: rag_engine`; a policy skip for an `in` tenant | notebook | Drafted |
| 15.4 | Compare quality and test update/withdrawal freshness | `make managed-status` matches after a reindex, an undo, a withdrawal | notebook | Drafted |

### Chapter 16 - Multimodal - Multimodal evidence and media (Colab · gate: `make smoke-media`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 16.1 | Query a video clip and validate media citations | the clip at its second; `make smoke-media` green | notebook | Drafted |
| 16.2 | Exercise implemented Studio and voice features | a generated image and its usage row; an answer read aloud | notebook | Drafted |

### Chapter 17 - Tuning - Managed fine-tuning (Colab · gate: the tuned candidate passes `make eval-live`)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 17.1 | Decide whether tuning is justified and prepare data | the frozen manifest and its row count | notebook | Drafted |
| 17.2 | Validate sanitized datasets and run managed tuning | the job id; the endpoint path with its location | notebook | Drafted |
| 17.3 | Compare the tuned candidate with an uncontaminated baseline | the pairwise verdict and the rupee delta | notebook | Drafted |

### Chapter 18 - Serving - Model gateway and self-hosted inference (Cloud Shell · gate: `make smoke-gateway`, `make smoke-slm`; zero GPU instances)

| # | Scene | Proof | Fifth file | Status |
|---|---|---|---|---|
| 18.1 | Trace and authorize gateway routes | a PAN re-routed; the cost header | runbook | Drafted |
| 18.2 | Serve a supplied or stock model using Ollama | the cold start timed; a gated answer from the small model | runbook | Drafted |
| 18.3 | Inspect the vLLM service and the GKE alternative | the manifest read; the duty-cycle sum | runbook | Drafted |
| 18.4 | Compare actual backends and verify shutdown behavior | the comparison table; zero GPU instances | runbook | Drafted |

## Authoring batches - the order of work

| Batch | Chapters | Scenes | Needs first | Ends with |
|---|---|---|---|---|
| A | 1, 2 | 5 | the Phase 0 rehearsal | pull requests for chapters 1 and 2 |
| B | 3, 4 | 8 | the Module 3 re-cut | pull requests for 3 and 4 |
| C | 5, 6, 7 | 11 | a live lane with the corpus loaded | pull requests for 5, 6 and 7 |
| D | 8, 9 | 6 | chapter 7's gate in use | pull requests for 8 and 9 |
| E | 10, 11, 12 | 12 | the chat service and MCP deployed | pull requests for 10, 11 and 12 |
| F | 13, 14 | 7 | the CD workflow installed | pull requests for 13 and 14 |
| G | 15, 16, 17, 18 | 13 | managed stores enabled (15); GPU quota (18) | pull requests for 15 to 18 |

Sixty-two scenes. At one writer per scene and one batch a week, seven weeks of authoring, plus review and rehearsal.

## What done means

- **Scene:** six files; the checker green (5 quizzes, 3 exercise cards, the titles and the template, every code
  excerpt verbatim, every make target real, the notebook clean); every proof rehearsed once on a live lane; read by a
  second person.
- **Chapter:** the gate green on the live lane; one pull request merged; the learner repo re-mirrored when a notebook changed.
