# HTML and IDE demo alignment review

Reviewed against author main `1a2a29c547cc` and learner main `76fe0c8b2b92` on 25 September 2026. Their kit trees matched before editing. The existing manual fixes form the baseline.

The lesson numbers below are the course's numbers on the day of the review. The Cohort 2 renumbering (7 October 2026, `plan/cohort-2-build-plan-2026-10-07.md`) moved the lessons; the links point at the renumbered folders.

## Scope and numbering

All **18 modules and 62 lessons** are included. The **53 authored HTML pages contain 1,646 code windows**. Every window is accounted for as a runnable example, shared setup, or read-only reference. The nine course-plan lessons are listed explicitly below; no HTML correspondence is claimed for them.

One file corresponds to one numbered HTML section. `demo_05_...` means section 5, including inside `optional/`, `recovery/` and `cleanup/`. A section can contain several ordered functions. Unnumbered setup retains descriptive setup filenames. `setup/finish.py` runs the remaining cleanup sections, then restores saved settings, including after a failed example.

The HTML displays public learner-file links under its headings. Source hashes refer to the reviewed teaching HTML with only the generated IDE-navigation blocks removed. Rebuilding links therefore cannot renumber source windows or hide changes to the lesson text/code.

## Preserved manual fixes

| Existing fix | Review evidence |
|---|---|
| 4.1 paid large-PDF exercise remains optional | Window 30 remains in `optional/`, outside the required prerequisites |
| Expected smoke/guard failures remain observable | 5.3, 5.4, 6.4, 8.2 and 18.3 retain their reviewed command/error handling |
| Candidate gates keep fresh reports and the selected API | 7.3 and 17.3 retain `live_gate(api=...)`; gate regressions remain enabled |
| Monitoring waits count elapsed time | 13.3 and 18.4 retain their recorded shutdown timestamp; the helper now resolves it across section files |
| Cloud Build recovery keeps narrow grants | 2.2, 12.2 and 14.1 keep the conditional bucket-reader, artifact-writer and log-writer recovery |
| Training/eval generation retries are retained | Existing retry implementations and their offline tests are preserved; this change does not alter dataset generation |
| Learner links remain public | The file/link checker rejects private-author links and missing learner/relative targets |

## Verification

- Compared **508 teaching functions** with the current-main baseline by executable AST, including their command constants. No original teaching function was omitted or changed. Added docstrings and outer section/session orchestration are excluded from this comparison.
- **1,541 functions/classes** in demos, setup and helpers have summaries and usage examples, including nested cell functions and local stub classes.
- Checked **535 raw HTML Bash windows**, **244 Python heredocs**, **57 inline Python snippets** and **247 generated command workflows**; imported every demo without executing it.
- Verified visible HTML number, filename, heading, source-window order, prerequisite order, complete lesson coverage and public/relative links.
- All **41 offline session regressions pass**, covering ordered runs, failed reads, exact-generation polling, state retention, expected refusals, owned cleanup, cross-section waits and restoration after failure.
- Page excerpt checks still verify the current kit code verbatim. Generated navigation has a separate bounded allowance; the teaching-content size budget is unchanged.
- Rebuilt all **50 buildable HTML lessons**, including the serving lessons with their specified tokenizer/Presidio dependencies; the directly authored 3.1 page passed source and excerpt checks. Reviewed the two derived-output changes described below.
- Four generator/navigation regressions pass. Existing operator, evaluation and offline kit gates pass locally. Linux command regressions and repository publication checks also run in the pull requests' CI; Windows cannot execute all Unix shell fixtures.

**Limits:** these are source, build and offline checks. They do not establish live IAM access, index availability, ingestion completion, model answers, latency or billing in your GCP project. Illustrative output remains illustrative. Run the lesson sequence on the intended workstation to verify those observations.

## Additional review findings

- Some page builders counted teaching copies as production implementations. Their runtime-source scans now exclude `workshop_demos/`; event-writer/backend-reader assertions still inspect the actual deployed kit.
- Lesson 10.3's offline build uses a high-resolution monotonic clock on Windows so a quick tool call is not rounded down to zero in the zero-budget demonstration. The learner's command is unchanged.
- Rebuilding 10.4 with the kit's pinned libraries changed the computed LangChain tool-schema length from 465 to 481 characters and the associated illustrative token/cost figures. Those derived figures were reviewed and refreshed; executable cells are unchanged. They are not live Gemini measurements.
- Lesson 17.3's fixture now initializes pandas before freezing its clock, avoiding a native datetime loader crash on Windows while keeping the same generated teaching content.
- Lesson 18.3's builder reads the current Makefile prerequisites, including `tf-backend`, instead of assuming `guard-project` is the only prerequisite. Its expected guard error now points to the current Makefile line 711 rather than the stale line 695.

## Complete lesson inventory

| Lesson | Source | Required section/plan files | Optional/recovery files | Cleanup files | HTML windows |
|---|---|---:|---:|---:|---:|
| [1.1: Reproduce the local environment and read the master diagram](module_00/lesson_0_2/README.md) | Course plan; no HTML | 3 | 0 | 1 | — |
| [1.2: Prove a first success and diagnose a first failure](module_00/lesson_0_2/README.md) | Course plan; no HTML | 2 | 0 | 0 | — |
| [2.1: Understand the project, identities and resource map](module_00/lesson_0_3/README.md) | Course plan; no HTML | 2 | 0 | 0 | — |
| [2.2: Review and start the prepared deployment](module_00/lesson_0_3/README.md) | Course plan; no HTML | 3 | 1 | 0 | — |
| [2.3: Check readiness, save progress and close the session](module_00/lesson_0_4/README.md) | Course plan; no HTML | 2 | 0 | 1 | — |
| [3.1: Understand source, tenant, page and chunk contracts](module_01/lesson_1_1/README.md) | HTML | 7 | 0 | 1 | 36 |
| [3.2: Parse documents and compare chunk boundaries](module_01/lesson_1_2/README.md) | HTML | 6 | 0 | 2 | 29 |
| [3.3: Create and validate compatible embeddings](module_01/lesson_1_3/README.md) | HTML | 7 | 0 | 2 | 48 |
| [3.4: Write, inspect and verify indexed records](module_01/lesson_1_4/README.md) | HTML | 7 | 0 | 2 | 46 |
| [4.1: Follow upload events, retries, dead-letter handling and the batch lane](module_01/lesson_1_5/README.md) | HTML | 6 | 1 | 3 | 40 |
| [4.2: Reindex a changed section and measure embedding reuse](module_01/lesson_1_6/README.md) | HTML | 6 | 0 | 2 | 26 |
| [4.3: Publish versions, retire documents and reject stale events](module_01/lesson_1_7/README.md) | HTML | 6 | 1 | 2 | 38 |
| [4.4: Restore documents and reconcile index differences](module_01/lesson_1_8/README.md) | HTML | 7 | 5 | 2 | 44 |
| [5.1: Apply query embeddings and authorized filters](module_02/lesson_2_1/README.md) | HTML | 6 | 1 | 2 | 29 |
| [5.2: Compare dense and hybrid retrieval](module_02/lesson_2_2/README.md) | HTML | 7 | 0 | 2 | 40 |
| [5.3: Rerank and inspect retrieved candidates](module_02/lesson_2_3/README.md) | HTML | 7 | 0 | 2 | 46 |
| [5.4: Test fallback without losing tenant or metadata filters](module_02/lesson_2_4/README.md) | HTML | 7 | 0 | 2 | 43 |
| [6.1: Pack evidence within the context budget](module_03/lesson_3_4/README.md) | HTML | 7 | 0 | 2 | 35 |
| [6.2: Generate structured answers, citations and refusals](module_03/lesson_3_5/README.md) | HTML | 7 | 0 | 2 | 37 |
| [6.3: Stream answers and handle failures](module_03/lesson_3_7/README.md) | HTML | 6 | 0 | 2 | 36 |
| [6.4: Complete the Streamlit upload-to-answer journey](module_03/lesson_3_8/README.md) | HTML | 6 | 0 | 2 | 35 |
| [7.1: Build a useful evaluation dataset](module_04/lesson_4_1/README.md) | HTML | 6 | 1 | 3 | 45 |
| [7.2: Separate offline checks, live scoring and LLM judgment](module_04/lesson_4_2/README.md) | HTML | 6 | 0 | 2 | 40 |
| [7.3: Compare one controlled change against a baseline](module_04/lesson_4_4/README.md) | HTML | 5 | 0 | 3 | 27 |
| [8.1: Trace authenticated identity into tenant membership](module_04/lesson_4_6/README.md) | HTML | 6 | 0 | 2 | 30 |
| [8.2: Test valid access, denied access and cross-tenant requests](module_04/lesson_4_7/README.md) | HTML | 6 | 0 | 2 | 24 |
| [8.3: Exercise DLP, guardrails and audit behavior](module_04/lesson_4_8/README.md) | HTML | 7 | 0 | 3 | 32 |
| [9.1: Compare context caching and answer caching](module_06/lesson_6_2/README.md) | HTML | 6 | 0 | 3 | 32 |
| [9.2: Test cache scope, configuration changes and freshness](module_06/lesson_6_3/README.md) | HTML | 6 | 0 | 3 | 31 |
| [9.3: Measure latency, avoided calls and false cache hits](module_06/lesson_6_4/README.md) | HTML | 4 | 1 | 3 | 23 |
| [10.1: Understand tool contracts and the direct agent loop](module_05/lesson_5_1/README.md) | HTML | 7 | 0 | 2 | 25 |
| [10.2: Implement the main LangGraph workflow](module_05/lesson_5_4/README.md) | HTML | 4 | 0 | 2 | 19 |
| [10.3: Diagnose tool arguments, access failures and timeouts](module_05/lesson_5_5/README.md) | HTML | 4 | 0 | 2 | 18 |
| [10.4: Compare the LangChain and ADK adapters](module_05/lesson_5_7/README.md) | HTML | 5 | 0 | 2 | 20 |
| [11.1: Distinguish agent state, conversation history and knowledge](module_06/lesson_6_5/README.md) | HTML | 5 | 0 | 2 | 19 |
| [11.2: Configure and inspect durable conversation storage](module_06/lesson_6_6/README.md) | HTML | 5 | 0 | 2 | 19 |
| [11.3: Verify restart recovery and session isolation](module_06/lesson_6_7/README.md) | HTML | 5 | 0 | 2 | 19 |
| [12.1: Expose, discover and invoke MCP tools](module_05/lesson_5_2/README.md) | HTML | 5 | 0 | 3 | 20 |
| [12.2: Deploy MCP and verify authorized access](module_05/lesson_5_3/README.md) | HTML | 5 | 1 | 2 | 22 |
| [12.3: Trace the implemented A2A peer and its permissions](module_10/lesson_10_6/README.md) | HTML | 5 | 0 | 2 | 19 |
| [13.1: Debug a wrong answer through the complete pipeline](module_11/lesson_11_4/README.md) | HTML | 5 | 0 | 2 | 21 |
| [13.2: Reconcile usage events, reports and alerts](module_11/lesson_11_5/README.md) | HTML | 5 | 0 | 2 | 23 |
| [13.3: Exercise model routing, budgets and shutdown controls](module_11/lesson_11_6/README.md) | HTML | 5 | 0 | 2 | 25 |
| [14.1: Build and deploy using keyless identity](module_11/lesson_11_1/README.md) | Course plan; no HTML | 2 | 1 | 0 | — |
| [14.2: Evaluate and gate the exact candidate revision](module_11/lesson_11_2/README.md) | Course plan; no HTML | 2 | 0 | 0 | — |
| [14.3: Promote, roll back and repair a controlled failure](module_11/lesson_11_3/README.md) | Course plan; no HTML | 2 | 0 | 0 | — |
| [14.4: Complete the independent capstone and operational handover](module_11/lesson_11_8/README.md) | Course plan; no HTML | 2 | 0 | 0 | — |
| [15.1: Build graph evidence from source documents](module_07/lesson_7_1/README.md) | HTML | 5 | 0 | 2 | 17 |
| [15.2: Compare Firestore and Spanner graph paths](module_07/lesson_7_2/README.md) | HTML | 5 | 1 | 2 | 27 |
| [15.3: Configure and query managed retrieval mirrors](module_07/lesson_7_3/README.md) | HTML | 5 | 0 | 2 | 26 |
| [15.4: Compare quality and test update/withdrawal freshness](module_07/lesson_7_4/README.md) | HTML | 5 | 0 | 2 | 23 |
| [16.1: Query a video clip and validate media citations](module_07/lesson_7_5/README.md) | HTML | 5 | 0 | 2 | 26 |
| [16.2: Exercise implemented Studio and voice features](module_07/lesson_7_6/README.md) | HTML | 5 | 0 | 2 | 22 |
| [17.1: Decide whether tuning is justified and prepare data](module_12/lesson_12_1/README.md) | HTML | 5 | 0 | 2 | 22 |
| [17.2: Validate sanitized datasets and run managed tuning](module_12/lesson_12_2/README.md) | HTML | 5 | 0 | 2 | 22 |
| [17.3: Compare the tuned candidate with an uncontaminated baseline](module_12/lesson_12_3/README.md) | HTML | 5 | 0 | 3 | 27 |
| [18.1: Trace and authorize gateway routes](module_09/lesson_9_1/README.md) | HTML | 5 | 0 | 2 | 24 |
| [18.2: Serve a supplied or stock model using Ollama](module_09/lesson_9_2/README.md) | HTML | 6 | 0 | 2 | 36 |
| [18.3: Inspect the vLLM service and the GKE alternative](module_09/lesson_9_3/README.md) | HTML | 5 | 0 | 2 | 23 |
| [18.4: Compare actual backends and verify shutdown behavior](module_09/lesson_9_4/README.md) | HTML | 5 | 0 | 2 | 21 |

Counts include setup and the finish dispatcher where present. The lesson README gives the exact run order, browser prerequisites, examples, effects and expected observations. No module or lesson is left out of this inventory.
