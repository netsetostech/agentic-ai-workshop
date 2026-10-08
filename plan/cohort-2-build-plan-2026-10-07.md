# Cohort 2 build plan (7 October 2026)

*Status: in progress. The author's decision on 7 October 2026: build the full course now, for the 7 November cohort, in the author's lesson order with the restructure review's fixes. Companions: `plan/agents-section-uplift-plan-2026-10-05.md` and `plan/agents-coverage-gap-plan-2026-10-07.md`, whose designs the agent lessons follow. The structure as data, with the old-to-new numbers: `plan/cohort-2-structure-2026-10-07.json`.*

## 1. What is being built, and by when

"Agentic AI Cohort 2.0" runs ten live two-hour sessions on weekends, 10 AM to 12 PM IST, from Saturday 7 November to Sunday 6 December 2026. The cohort gets the full course, so each lesson must be ready before the session that first uses it. Lessons ship in that order:

| Wave | Ready by | For |
|---|---|---|
| 0 | Fri 16 Oct | the renumbering PR: every existing page on its new number, before any new lesson lands |
| 1a | Fri 30 Oct | pre-work week (31 Oct - 6 Nov): Basics and Module 0, so learners set up their lane before session 1 |
| 1b | Fri 6 Nov | weekend 1: Sat 7 Nov Module 1, Sun 8 Nov Module 2 |
| 2 | Fri 13 Nov | weekend 2: Sat 14 Nov Module 3, Sun 15 Nov Module 4 |
| 3 | Fri 20 Nov | weekend 3: Sat 21 Nov Module 5, Sun 22 Nov Module 6 |
| 4 | Fri 27 Nov | weekend 4: Sat 28 Nov Modules 7 and 8, Sun 29 Nov Module 9 |
| 5 | Fri 4 Dec | weekend 5: Sat 5 Dec Module 10, Sun 6 Dec Modules 11 and 12 |

**The course:** 95 lessons in Basics and Modules 0 to 12. 53 are today's pages on new numbers (4 of them with a small addition) and 42 are written new (3 of them design pages). The author's list had 104 slots. The review's fixes merge its duplicates, fold Layer Normalization into Transformer, and give the setup and deployment pages a home in Module 0, which gives 95.

**Decisions taken on 7 October 2026:**
- **Order:** the author's, with the restructure review's fixes. Setup and deployment go into Module 0, and 3.3 moves to Module 1. The agent harness (LangGraph, tool failures, the case desk and the adapters) joins MCP in Module 5, so memory (Module 6) and the multi-agent lessons (Module 10) come after what they build on. MCP keeps the author's Module 5 places, with a setup step for the relabel it needs, and the router stays in Module 10 after the case desk. The injection lesson comes after everything it attacks, and 'Integration with other clouds' becomes Google's managed agent platform.
- **One cloud for now:** Module 0 is a Google Cloud billing and project lesson, with no Azure or AWS accounts.
- **Live runs:** the author runs them on their own project. Each lesson's pull request carries a run list, and pages use placeholders until the author's output comes back.
- **Pull requests:** one branch and one pull request per lesson, pushed once check_lesson and audit_pages pass. The author merges.
- **Basics:** runnable pages in the standard format, with numpy and google-genai cells whose outputs are computed at build time.
- **Jev:** TypeSafe AI's System One model, as 2.6. It is the kit's first non-Google model, so it sits behind a default-off switch, with a recorded response for learners without TypeSafe early access.

## 2. The structure

*Kind*: renumber (today's page on its new number), write (a new page, or a manifest lesson not started yet). *Kit*: what the lesson needs from `deploy/`. *Source*: where the content comes from: a lesson number is today's page, and named tasks are the uplift and gap plans' designs.

### Basics: The ideas under the kit, as runnable pages

*Pre-work · gate: every cell runs on the learner's laptop · ready by Fri 30 Oct (wave 1a)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| B.1 | Run Python the way the kit does: venvs, JSON and HTTP calls | write | kit exists | author's Basics: Python Basics |
| B.2 | Turn text into tokens and embeddings | write | kit exists | author's Basics: Tokenization & Embeddings |
| B.3 | Read a transformer block, with layer normalization | write | kit exists | author's Basics: Transformer, author's Basics: Layer Normalization (folded in) |
| B.4 | Encode with BERT-style models: embeddings and rankers | write | kit exists | author's Basics: BERT & Encoder Models |
| B.5 | Generate with GPT-style models: decoding and run-to-run variance | write | kit exists | author's Basics: GPT & Decoder Models |

### Module 0: Deploy, prove and switch off your lane on Google Cloud

*Core · gate: `make dryrun` green; `make smoke` green, `make off` floors to zero · ready by Fri 30 Oct (wave 1a)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 0.1 | Set up the Google Cloud billing account, budget and project | write | kit exists | 2.1 (part), author's M0: GCP / Azure / AWS Free Account (GCP only) |
| 0.2 | Reproduce the local environment, read the master diagram and prove a first success | write | kit exists | 1.1, 1.2, author's M0: Git Setup, Setting Local |
| 0.3 | Understand the project, identities and resource map, and deploy the lane | write | kit exists | 2.1, 2.2 |
| 0.4 | Prove the lane, break it once, and switch it off | write | kit exists | 2.3, 1.2 (the failure half) |

### Module 1: Turn documents into searchable evidence and keep them current

*Core · gate: a row with every stamp; `make smoke-reindex` · ready by Fri 6 Nov (wave 1b)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 1.1 | Understand source, tenant, page and chunk contracts | renumber | kit exists | 3.1 |
| 1.2 | Parse documents and compare chunk boundaries | renumber | kit exists | 3.2 |
| 1.3 | Create and validate compatible embeddings | renumber | kit exists | 3.3 |
| 1.4 | Write, inspect and verify indexed records | renumber | kit exists | 3.4 |
| 1.5 | Follow upload events, retries, dead-letter handling and the batch lane | renumber | kit exists | 4.1 |
| 1.6 | Reindex a changed section and measure embedding reuse | renumber | kit exists | 4.2 |
| 1.7 | Publish versions, retire documents and reject stale events | renumber | kit exists | 4.3 |
| 1.8 | Restore documents and reconcile index differences | renumber | kit exists | 4.4 |

### Module 2: Retrieve the right evidence

*Core · gate: ablation recorded; `make smoke` refuses a fallback answer · ready by Fri 6 Nov (wave 1b)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 2.1 | Apply query embeddings and authorized filters | renumber | kit exists | 5.1 |
| 2.2 | Compare dense and hybrid retrieval | renumber | kit exists | 5.2 |
| 2.3 | Rerank and inspect retrieved candidates *(adds a theory level on bi-encoders against cross-encoders (the author's title))* | renumber + small addition | kit exists | 5.3 |
| 2.4 | Test fallback without losing tenant or metadata filters | renumber | kit exists | 5.4 |
| 2.5 | Rewrite the query before retrieval, and measure it | write | kit work | author's M2: Query rewriting before retrieval |
| 2.6 | Decide answer-or-refuse with a System One model (Jev) | write | kit work | author's M2: Jev: the System One decision model |

### Module 3: Prompt, ground and stream the answer

*Core · gate: upload to answer in the UI · ready by Fri 13 Nov (wave 2)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 3.1 | See run-to-run variance and thinking levels in the same prompt | write | small kit work | author's M3: Stochastic LLMs |
| 3.2 | Prompt with chain of thought and few-shot exemplars | write | small kit work | author's M3: Chain-of-thought and few-shot prompting |
| 3.3 | Recognise prompt failure modes and fix them in the prompt | write | small kit work | author's M3: Prompt failure modes |
| 3.4 | Pack evidence within the context budget | renumber | kit exists | 6.1 |
| 3.5 | Generate structured answers, citations and refusals | renumber | kit exists | 6.2 |
| 3.6 | Check quotes and version prompts | write | small kit work | author's M3: Grounding (quote checks), author's M3: Prompting reliably |
| 3.7 | Stream answers and handle failures | renumber | kit exists | 6.3 |
| 3.8 | Complete the Streamlit upload-to-answer journey | renumber | kit exists | 6.4 |
| 3.9 | System design: a fact-checking system built from DocuMind's parts | write (design page) | kit exists | author's M3: System design: fact-checking agentic system |

### Module 4: Measure quality, isolation and safety, and reject regressions

*Core · gate: `make eval-live` green on a candidate; isolation 1.00; a blocked prompt · ready by Fri 13 Nov (wave 2)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 4.1 | Build a useful evaluation dataset | renumber | kit exists | 7.1 |
| 4.2 | Separate offline checks, live scoring and LLM judgment | renumber | kit exists | 7.2 |
| 4.3 | Place evals in the pipeline: CI, the candidate gate and live traffic | write | kit exists | author's M4: Placing and plugging evals |
| 4.4 | Compare one controlled change against a baseline | renumber | kit exists | 7.3 |
| 4.5 | Check the LLM judge against people | write | small kit work | author's M4: Human evals, gap plan S1-S3 (7.4) |
| 4.6 | Trace authenticated identity into tenant membership | renumber | kit exists | 8.1 |
| 4.7 | Test valid access, denied access and cross-tenant requests | renumber | kit exists | 8.2 |
| 4.8 | Exercise DLP, guardrails and audit behavior | renumber | kit exists | 8.3 |
| 4.9 | Read the failures first, then attack your own pipeline | write | kit work | author's M4: Exploratory and adversarial evals, gap plan S2, S14 |

### Module 5: Tools, MCP and the agent harness

*Core · gate: `make smoke-chat`, `make smoke-mcp` · ready by Fri 20 Nov (wave 3)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 5.1 | Understand tool contracts and the direct agent loop *(takes the author's 'Parallel tool calls' slot as a level)* | renumber + small addition | kit exists | 10.1 |
| 5.2 | Expose, discover and invoke MCP tools *(two sentences point back to 5.1 for tool definitions; a `make doc-types` setup step)* | renumber + small addition | kit exists | 12.1 |
| 5.3 | Deploy MCP and verify authorized access | renumber | kit exists | 12.2 |
| 5.4 | Implement the main LangGraph workflow | renumber | kit exists | 10.2 |
| 5.5 | Diagnose tool arguments, access failures and timeouts | renumber | kit exists | 10.3 |
| 5.6 | Hand a question to the person the law names | renumber | kit exists | 10.5 |
| 5.7 | Compare the LangChain and ADK adapters | renumber | kit exists | 10.4 |
| 5.8 | Pause, approve, clarify and escalate: human in the loop | write | large kit work | author's M5: Human in the loop, uplift D1-D3 |

### Module 6: Context, caching and memory

*Core · gate: the second ask costs Rs 0; the restart check · ready by Fri 20 Nov (wave 3)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 6.1 | Assemble the context: what rides every model call | write | small kit work | author's M6: Context Architecture & Assembly |
| 6.2 | Compare context caching and answer caching | renumber | kit exists | 9.1 |
| 6.3 | Test cache scope, configuration changes and freshness | renumber | kit exists | 9.2 |
| 6.4 | Measure latency, avoided calls and false cache hits | renumber | kit exists | 9.3 |
| 6.5 | Distinguish agent state, conversation history and knowledge | renumber | kit exists | 11.1 |
| 6.6 | Configure and inspect durable conversation storage | renumber | kit exists | 11.2 |
| 6.7 | Verify restart recovery and session isolation | renumber | kit exists | 11.3 |
| 6.8 | Resume a paused or cut-off turn: checkpoint and resume | write | kit work | author's M6: Checkpoint and resume, uplift K8, K13 |
| 6.9 | Budget working memory: windowing, compaction and write rules | write | large kit work | author's M6: Memory summarization and write strategies, author's M6: Working memory management, uplift 11.4 (H3, H4, H11) |

### Module 7: Graph, managed and multimodal retrieval

*Advanced · gate: `found_by: rag_engine`; `make smoke-media` · ready by Fri 27 Nov (wave 4)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 7.1 | Build graph evidence from source documents | renumber | kit exists | 15.1 |
| 7.2 | Compare Firestore and Spanner graph paths | renumber | kit exists | 15.2 |
| 7.3 | Configure and query managed retrieval mirrors | renumber | kit exists | 15.3 |
| 7.4 | Compare quality and test update/withdrawal freshness | renumber | kit exists | 15.4 |
| 7.5 | Query a video clip and validate media citations | renumber | kit exists | 16.1 |
| 7.6 | Exercise implemented Studio and voice features | renumber | kit exists | 16.2 |

### Module 8: Change the pipeline and measure it

*Core · gate: a re-embedded index reconciled to the ledger · ready by Fri 27 Nov (wave 4)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 8.1 | Run the ingest events through Pub/Sub, mapped to Kafka | write | kit exists | author's M8: Pub/Sub, with the Kafka equivalent, author's M8: Ingestion: the pipeline end to end |
| 8.2 | Change a chunker, re-embed and reconcile | write | kit exists | author's M8: Code part: change a chunker, re-embed, reconcile, author's M8: Embedding or Tokenization [Practical] |
| 8.3 | Size RAG for ten million documents | write | kit exists | author's M1: RAG over 10M docs: the scale side, author's M8: RAG over 10M docs: the pipeline side |
| 8.4 | System design: a self-updating documentation platform | write (design page) | kit exists | author's M4: System design: self-updating AI documentation platform |

### Module 9: Model gateway and self-hosted inference

*Advanced · gate: `make smoke-gateway`, `make smoke-slm`; zero GPU instances · ready by Fri 27 Nov (wave 4)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 9.1 | Trace and authorize gateway routes | renumber | kit exists | 18.1 |
| 9.2 | Serve a supplied or stock model using Ollama | renumber | kit exists | 18.2 |
| 9.3 | Inspect the vLLM service and the GKE alternative | renumber | kit exists | 18.3 |
| 9.4 | Compare actual backends and verify shutdown behavior | renumber | kit exists | 18.4 |

### Module 10: Agent loops, patterns and multi-agent systems

*Core · gate: `make smoke-agent`; `make smoke-desk` · ready by Fri 4 Dec (wave 5)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 10.1 | Choose where the agent reasons: observe-think-act and ReAct | write | large kit work | author's M10: Agent loop, author's M10: Observe-think-act and ReAct loops, gap plan P4 (P1, P10) |
| 10.2 | Plan first or decide each step: plan-and-execute | write | large kit work | author's M10: Plan-and-execute loop, gap plan P5 (P2) |
| 10.3 | Check, retry or choose: the critic and refiner pattern | write | large kit work | author's M10: Critic and Refiner pattern, gap plan P6 (P3, P9) |
| 10.4 | Route each question to one specialist agent | renumber | kit exists | 10.6 |
| 10.5 | Run a desk as an agent with checked calculator arguments | write | large kit work | uplift 10.7 (M3, A8, A9, C3, E8), author's M10: Mixture of agents pattern (gap plan Q6) |
| 10.6 | Trace the implemented A2A peer and its permissions | renumber | kit exists | 12.3 |
| 10.7 | Hand one question to the A2A peer, and stop loops and deadlocks | write | large kit work | uplift 12.4 (C2, C4, C7), author's M10: Deadlocks in multi-agent systems (gap plan R2, Q4) |
| 10.8 | Defend agents against injected documents and poisoned tools | write | large kit work | uplift 12.5 (F10), author's M5: Prompt injection through documents and tools (moved after A2A) |
| 10.9 | Run the peer on Google's managed agent platform | write | large kit work | uplift I7 (I1, I5, I6), gap plan N4, N5, S9, author's M10: Integration with other clouds (replaced: one cloud for now) |
| 10.10 | Coding agents: a Ralph loop, an AI code reviewer and paper-to-code | write | large kit work | author's M10: Ralph loop, author's M10: System design: paper-to-code agent, author's M4: System design: AI code reviewer, gap plan P7, P8 |
| 10.11 | System design: incident auto-remediation | write (design page) | large kit work | author's M10: System design: incident auto-remediation, gap plan S10, S11 |

### Module 11: Release, operate and hand over the project

*Core · gate: rollback timed; `tenant_daily` in INR; the rubric scored · ready by Fri 4 Dec (wave 5)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 11.1 | Build and deploy using keyless identity | write | kit work | 14.1 |
| 11.2 | Evaluate and gate the exact candidate revision | write | kit work | 14.2 |
| 11.3 | Promote, roll back and repair a controlled failure | write | kit work | 14.3 |
| 11.4 | Debug a wrong answer through the complete pipeline | renumber | kit exists | 13.1 |
| 11.5 | Reconcile usage events, reports and alerts | renumber | kit exists | 13.2 |
| 11.6 | Exercise model routing, budgets and shutdown controls | renumber | kit exists | 13.3 |
| 11.7 | Reproduce the agent failures production shows and no eval row does | write | kit work | author's M11: Brainstorming production gotchas, gap plan S12 |
| 11.8 | Complete the independent capstone and operational handover | write | kit work | 14.4 |

### Module 12: Inference and tuning

*Advanced · gate: the tuned candidate passes `make eval-live` · ready by Fri 4 Dec (wave 5)*

| Lesson | Title | Kind | Kit | Source |
|---|---|---|---|---|
| 12.1 | Decide whether tuning is justified and prepare data | renumber | kit exists | 17.1 |
| 12.2 | Validate sanitized datasets and run managed tuning | renumber | kit exists | 17.2 |
| 12.3 | Compare the tuned candidate with an uncontaminated baseline *(takes the author's 'Inference: compare the models' slot: tuned against base on one gate)* | renumber + small addition | kit exists | 17.3 |
| 12.4 | Improve the agent safely: eval-gated self-improvement | write | kit work | author's M12: Self-evolving agents |

## 3. Old numbers to new

The renumbering moves every built page in one scripted pull request, before any new lesson lands. Kit comments keep their notebook-era numbers; `deploy/INDEX.md` maps kit files to lessons.

| Today | New | Today | New | Today | New |
|---|---|---|---|---|---|
| 1.1 | 0.2 | 7.1 | 4.1 | 13.1 | 11.4 |
| 1.2 | 0.2 | 7.2 | 4.2 | 13.2 | 11.5 |
| 2.1 | 0.3 | 7.3 | 4.4 | 13.3 | 11.6 |
| 2.2 | 0.3 | 8.1 | 4.6 | 14.1 | 11.1 |
| 2.3 | 0.4 | 8.2 | 4.7 | 14.2 | 11.2 |
| 3.1 | 1.1 | 8.3 | 4.8 | 14.3 | 11.3 |
| 3.2 | 1.2 | 9.1 | 6.2 | 14.4 | 11.8 |
| 3.3 | 1.3 | 9.2 | 6.3 | 15.1 | 7.1 |
| 3.4 | 1.4 | 9.3 | 6.4 | 15.2 | 7.2 |
| 4.1 | 1.5 | 10.1 | 5.1 | 15.3 | 7.3 |
| 4.2 | 1.6 | 10.2 | 5.4 | 15.4 | 7.4 |
| 4.3 | 1.7 | 10.3 | 5.5 | 16.1 | 7.5 |
| 4.4 | 1.8 | 10.4 | 5.7 | 16.2 | 7.6 |
| 5.1 | 2.1 | 10.5 | 5.6 | 17.1 | 12.1 |
| 5.2 | 2.2 | 10.6 | 10.4 | 17.2 | 12.2 |
| 5.3 | 2.3 | 11.1 | 6.5 | 17.3 | 12.3 |
| 5.4 | 2.4 | 11.2 | 6.6 | 18.1 | 9.1 |
| 6.1 | 3.4 | 11.3 | 6.7 | 18.2 | 9.2 |
| 6.2 | 3.5 | 12.1 | 5.2 | 18.3 | 9.3 |
| 6.3 | 3.7 | 12.2 | 5.3 | 18.4 | 9.4 |
| 6.4 | 3.8 | 12.3 | 10.6 |  |  |

Several of today's lessons merge into one new lesson: 1.1 and 1.2 into 0.2, 2.1 and 2.2 into 0.3, and 2.3 with 1.2's failure half into 0.4. All five are not started today, so no page is merged.

## 4. How a lesson is built

- **Renumber.** The renumbering pull request moves the page, its parts, its build.py title and its workshop demo map to the new number, rewrites every 'Lesson N.M' and 'Module N' reference from the table above, and rebuilds the page. It also adds a check to `check_lesson.py` first: every lesson and module a page names must exist in the manifest, so a stale number fails CI.
- **Write.** A new lesson follows CLAUDE.md's page shape: hero with chips, table of contents, 'In this lesson', Level 0 theory with an analogy and a diagram or interactive built on the kit's real rules, definitions, the shared setup, levels from the deployed UI to the kit to REST to direct reads, 'Verify it yourself', 'What changed on your lane', and a footer naming the next lesson. Excerpts come verbatim from `block()`, and numbers are computed at build time.
- **Kit first.** Where a lesson needs kit work, the kit change lands in its own pull request with tests, before or with the page, and the pages that quote changed lines are rebuilt (check_lesson names them).
- **Live runs.** Each pull request carries a run list: the commands the author runs on their lane, and which placeholder each output fills. The author's output goes into the lesson's `data/` files with every identifier replaced by a placeholder, and the page is rebuilt from it.
- **Gates.** `python pagekit/build.py <lesson>`, `python pagekit/check_lesson.py <lesson>`, `python pagekit/audit_pages.py <lesson>`, the kit's tests, then the pull request. The author merges.
- **Publishing.** The learner kit is published only with the author's go-ahead each time, ideally once per wave.

## 5. The first two weeks

1. **The renumbering pull request (wave 0, by Fri 16 Oct).** The manifest moves to Basics and Modules 0 to 12; the 53 built pages, their demo maps and their references move to the new numbers; the reference check goes into `check_lesson.py`; and the counts in CLAUDE.md, the READMEs and the demo builder follow, as the author's edits.
2. **Basics and Module 0 (wave 1a, by Fri 30 Oct).** Nine pages, written in parallel from 8 October. Module 0's run list includes one `make up` from a blank project, recorded on the author's lane by about 23 October so the pages can be finished from real output.
3. **The long-lead agent kit starts at once, in the background.** 11 lessons need large kit work from the uplift and gap plans: 5.8, 6.9, 10.1, 10.2, 10.3, 10.5, 10.7, 10.8, 10.9, 10.10, 10.11. Their kit pull requests start in October, so the pages can be written in November.

## 6. Risks

- **Volume.** 42 new pages and the renumbering in about eight weeks. Lessons are built in parallel, and each week's report says what is ready and what is slipping, early enough to cut scope instead of a session.
- **Large kit work.** The lessons named in section 5 depend on uplift and gap tasks that are not built. Each has a cohort scope, the smallest version that teaches its slot honestly. Where the full design cannot land by its wave, the cohort scope ships, and the rest follows after 6 December.
- **Live runs are a bottleneck.** Every lane run goes through the author. Run lists are batched weekly, and pages are written so that only lane-dependent values wait on them.
- **People's labels.** 4.5's cohort version has learners label about 20 rows themselves. Commissioned labels (gap plan S1) follow after the cohort.
- **Jev's early access.** If the author's TypeSafe account or its terms are not ready, 2.6 runs from a recorded response and says so.
- **Renumbering breaks references.** The reference check lands before the move, so CI catches any number left behind.

## 7. Every new lesson's cohort scope

| Lesson | Cohort scope | Kit |
|---|---|---|
| B.1 | venv, pathlib, json, an HTTP call and an async call, each cell run locally and checked at build time | kit exists |
| B.2 | count tokens through the Gemini API and price them as 3.4 does; embed with text-embedding-005 and compare cosine similarity; ties to 1.3 and 3.4 | kit exists |
| B.3 | numpy self-attention, heads, the residual path and layer normalization on a toy sentence | kit exists |
| B.4 | the masked-language idea, bi-encoders against cross-encoders, tied to 1.3's embeddings and 2.3's ranker | kit exists |
| B.5 | next-token generation, why Gemini 3 ignores temperature, thinking level and run-to-run variance; ties to 3.1 | kit exists |
| 0.1 | trial credit and paid billing, the budget alert terraform/budget.tf declares, the project and its APIs, the standing cost per day and per weekend; one cloud only | kit exists |
| 0.2 | Git and the clone, the venv, the master diagram, the Rs 0 lane, `make dryrun` with one failure diagnosed | kit exists |
| 0.3 | service accounts and the resource map, `make plan` and `make up`, IAP and the roster; the author records one `make up` from a blank project | kit exists |
| 0.4 | `make smoke`, one failure diagnosed, `make off` and `make down`, the daily cost of a lane left up | kit exists |
| 2.5 | a rewrite stage in rag-api behind a default-off switch, one call line in main.py, and an ablate.py arm | kit work (three to five days) |
| 2.6 | a Jev client behind a default-off switch (the kit's first non-Google model, the author's go-ahead), a recorded response for learners without TypeSafe early access, and a decision eval on the golden rows | kit work (three to five days) |
| 3.1 | a repeat script over the generator; temperature shown as ignored by Gemini 3 | small kit work (a day or two) |
| 3.2 | thinking level as chain of thought, measured; few-shot through the router's PROMPT_EXEMPLARS and route-eval | small kit work (a day or two) |
| 3.3 | failures read from the golden set's failing rows, each fixed with one Change-it on the generator prompt | small kit work (a day or two) |
| 3.6 | run_eval's quote-support measure and prompt versioning; citations and refusals stay in 3.5 | small kit work (a day or two) |
| 3.9 | a design page in the capstone rubric's shape, anchored on the generator, the quote check and the judge | kit exists |
| 4.3 | where each eval runs (checks.yml, eval-live, usage rows) and what each can and cannot catch | kit exists |
| 4.5 | the learner labels about 20 rows and the kit computes agreement; people-written labels (gap plan S1) follow after the cohort | small kit work (a day or two) |
| 4.9 | triage by cause on the golden set's failing rows, and an attack set on rag-api's doors built on 4.8's probes | kit work (three to five days) |
| 5.8 | the LangGraph approval flow (uplift D1-D3) is not built yet; until it is, the lesson ships the escalation and clarification levels on the case desk's existing handoff | large kit work (uplift or gap tasks) |
| 6.1 | the chat brains' prompt assembly read and measured per source | small kit work (a day or two) |
| 6.8 | the checkpointer's history read back and one turn replayed | kit work (three to five days) |
| 6.9 | the uplift's 11.4 design; until H11 lands, the windowing level runs on the existing trim | large kit work (uplift or gap tasks) |
| 8.1 | 1.5's pipeline driven end to end, with a Kafka mapping table | kit exists |
| 8.2 | a Change-it practical on parser.py, reindex.sh and reconcile.py | kit exists |
| 8.3 | a build-time calculator over kit constants, ending with what the kit would change at that scale | kit exists |
| 8.4 | a design page anchored on ingestion, versions and the cache freshness rules | kit exists |
| 10.1 | the gap plan's P4 page; P1's parser and P10's planner switch are its kit | large kit work (uplift or gap tasks) |
| 10.2 | the gap plan's P5 page on P2's kit | large kit work (uplift or gap tasks) |
| 10.3 | the gap plan's P6 page on P3's and P9's kit | large kit work (uplift or gap tasks) |
| 10.5 | the uplift's 10.7, with the mixture-of-agents aggregator as its Level 5 step | large kit work (uplift or gap tasks) |
| 10.7 | the uplift's 12.4 with the gap plan's loops-and-deadlocks steps | large kit work (uplift or gap tasks) |
| 10.8 | the uplift's 12.5, after everything it attacks | large kit work (uplift or gap tasks) |
| 10.9 | the uplift's I7 level as its own lesson (gap plan G-decision 2 (b)) | large kit work (uplift or gap tasks) |
| 10.10 | the gap plan's P8 page on P7's kit | large kit work (uplift or gap tasks) |
| 10.11 | the gap plan's S11 page on S10's kit | large kit work (uplift or gap tasks) |
| 11.1 | a build and a deploy with no key | kit work (three to five days) |
| 11.2 | the candidate judged; its name recorded | kit work (three to five days) |
| 11.3 | a controlled failure repaired; the rollback timed | kit work (three to five days) |
| 11.7 | a curated registry of gotchas, each with a drill, a detector and a lever, built from existing drills | kit work (three to five days) |
| 11.8 | the capstone's components checked; the handover walked | kit work (three to five days) |
| 12.4 | the improvement loop with a person and a gate in it, on 11.2's and 11.3's targets | kit work (three to five days) |
