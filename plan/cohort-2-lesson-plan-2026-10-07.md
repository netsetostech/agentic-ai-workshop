# Cohort 2 lesson plan: the 33 lessons still to write (7 October 2026)

*Status: approved by the author on 7 October 2026, with four decisions: start every track now; keep `gemini-3.6-flash`;
make all four kit fixes; the author merges every pull request (section 8). A companion to `plan/cohort-2-build-plan-2026-10-07.md`, whose structure
and waves it keeps. It says how the 33 unwritten lessons, the four carried additions and the kit under them get built
by Fri 4 Dec, in what order, and what each needs from the author. Sources: seven read-only reviews made on 7 October
2026, one per wave group, each reading the build plan, the uplift and gap plans and the kit at `main` `4dc45fd`. The kit
files, functions and lines named here were read; anything not verified says so.*

## 1. Where things stand

- **Written:** 62 of 95 lessons, on `main` at `4dc45fd`; the learner kit at `1fc81a5`. Waves 0 and 1a, due Fri 16 and
  Fri 30 Oct, are done.
- **To write:** 33 lessons, four carried additions (2.3, 5.1, 5.2, 12.3), and one port: PR #70, the author's help-desk
  and RRF work on old lesson 5.2, onto 2.2's renumbered page.
- **Waiting on the author's runs:** 41 placeholders on seven pages (B.2 2, B.4 3, B.5 2, 0.1 7, 0.2 6, 0.3 9, 0.4 12).
- **The uplift and gap plans:** none of their tasks is built. Each lesson below takes the smallest slice of them that
  teaches its slot with real kit behaviour, its *cohort scope*; section 10 lists what follows after 6 December.
- **Working days left, counting today:** 22 to wave 1b (Fri 6 Nov), 27 to wave 2, 32 to wave 3, 37 to wave 4, 42 to
  wave 5 (Fri 4 Dec).

## 2. What it takes

| Wave, ready by | Lessons | Kit PRs | Kit, engineer-days | The author's batches |
|---|---|---|---|---|
| Fixes, Fri 16 Oct | the kit bugs (section 3) | 3 | about 3 | before batch 0 |
| 1b, Fri 6 Nov | 2.5, 2.6; 2.3's addition; #70's port | 3 | 7.5 | 1 |
| 2, Fri 13 Nov | 3.1, 3.2, 3.3, 3.6, 3.9, 4.3, 4.5, 4.9 | 5 | 14 | 1, 2 |
| 3, Fri 20 Nov | 5.8, 6.1, 6.8, 6.9; 5.1's and 5.2's additions | 4, plus 1 stretch | 13.5, plus 8-11 | 1, 2 |
| 4, Fri 27 Nov | 8.1, 8.2, 8.3, 8.4 | 1 | 1 | 3 |
| 5, Fri 4 Dec | Module 10: 10.1-10.3, 10.5, 10.7-10.11 | 15, plus 2 optional | 60.5 | 0 (a probe), 1, 3, 4 |
| 5, Fri 4 Dec | Modules 11-12: 11.1-11.3, 11.7, 11.8, 12.4; 12.3's addition | 6 | 21 | 1 (a probe), 3, 4 |
| **Total** | 33 lessons, 4 additions, 1 port | **37** | **about 120** | **6 batches** |

Engineer-days measure size: what one engineer would need for the kit alone, with the pages on top. The pages are
written by parallel writers, as wave 1a's were, so writing does not set the calendar. Three things do: the order the
kit PRs must land in (4.2), the author's six live-run batches (section 6), and how fast about 75 pull requests (37 kit,
33 pages, 4 additions, the port), some 10 a week, are reviewed and merged by the author.

Module 10 is half the kit work and all of it is due on Fri 4 Dec, so its long-lead pieces start now: the agent bench
(KB) and Agent Engine's probe (10.9-A), both merged by Fri 16 Oct.

## 3. First: the kit fixes, landed by Fri 16 Oct

Batch 0 records Module 0 from a blank project on Mon 19 Oct, the build plan's "by about 23 October". Three bugs stop
that run or its teardown, so these land first.

### 3.1 Fixes

The fixes land as three PRs:
1. the deploy fixes (a, b, c, e);
2. the local-lane and text fixes (d, f);
3. Model Armor (g), once verified.

| | Bug | Where | Smallest fix, and its test | Pages rebuilt |
|---|---|---|---|---|
| a | `make up` stops after ingest and the API. The admin script runs `gcloud builds submit --file=`, which is not a flag, under `sh -ec`, so the admin service, `wait-index`, `roster`, `managed-stores` and `operators` never run | `commands/lesson-12.3.sh:13-15`; hard-coded `us-central1` on lines 18, 19, 27, 29; a `group:` binding on 28-31 | Delete 13-15: `make build` already pushes the admin image. Use `${REGION:-us-central1}`, and the ADMIN_EMAILS loop from `lesson-12.4.sh:41-47`. New `commands/tests/test_deploy_scripts.py` over every DEPLOY block | 0.3, 0.4 |
| b | `make down` destroys nothing. `prevent_destroy`, with `MANAGED_SEARCH=true` by default, makes Terraform refuse after the services and corpora are already gone, so six hourly lines keep billing | `terraform/managed.tf:97-102`; `Makefile:126`; the stale comment at `Makefile:863-864`; `README.md:364` | Delete the block: the plan guard in `commands/infrastructure.py` already refuses deletes on plan and up (`test_infrastructure.py:158`). Add a static test that no resource carries `prevent_destroy` | 0.4, 7.3, and 0.1 (its `c.html:119` becomes true) |
| c | Every learner is told to create the same state bucket: `documind-tfstate` is one global name | `Makefile:150`; `smoke/preflight.sh:7, 40` | Default to `$(PROJECT)-tfstate` | 0.3, 0.4 (their workarounds go) |
| d | `make chat-local` serves an empty store: it seeds `./documind_chroma` from `deploy/`, then starts from `services/chat` | `Makefile:569-570`; `shared/profile.py:22` | `DOCUMIND_CHROMA_DIR=$(CURDIR)/documind_chroma` on both recipe lines; `commands/tests/test_local_lane.py` | 0.2 (its workaround cell goes) |
| e | The index's shard size is the API's choice: Rs 44.05 an hour on SMALL, Rs 111.10 on MEDIUM | `terraform/vector.tf:19-29` | An explicit SMALL shard, by the author's decision. It helps only new lanes, which every learner's lane in the pre-work week is; the plan guard refuses to replace an existing index | 0.1, 0.3, 0.4 (`standing_cost.py:69` asserts the absence today) |
| f | A false claim. The chat history budget is labelled a "rolling summary", but no chat code trims or summarises history: every model call resends the whole thread | `services/rag-api/context_budget.py:20`; 3.4's `c.html:104` | Correct the comment and the page before 3.4 is taught on Sat 14 Nov | 3.4 |
| g | Model Armor's verdict. `guard.py:18` reads `match_state`, which uplift task F1 says google-cloud-modelarmor 0.7.1 does not have, so `ARMOR=on` would answer 500. **Not verified** | `services/rag-api/guard.py` | Verify against the pinned library and fix if true, before batch 2 | 4.8; unblocks the candidate halves of 4.9 and 10.8 |
| h | Stale text | See below | Each lesson PR fixes the lines it owns | 2.3, 5.2, 11.1, 11.8 |

The stale text in row h:
- 2.3 `c.html:186`: "lesson 13's view" is 11.5's.
- 5.2 `a.html`: "in lesson 5.7", and "lesson 10.4's relabel" in `a.html:49` and `c.html:28`.
- `plan/capstone-rubric.md`: old lesson numbers, and a source that does not exist.
- The 11.1 demo recipe in `tools/workshop_demo_additions.py` reads `terraform/ci.tf`, which does not exist.
- `INDEXING.md:179` cites an absent `tools/check_auth_wiring.py`.

### 3.2 The model: staying on `gemini-3.6-flash`

The author decided on 7 October 2026 to keep the kit on `gemini-3.6-flash` for the cohort. It is deprecated on Thu 19
Nov 2026, between the third and fourth cohort weekends, and Google's Vertex AI model page recommends Gemini 3.8 Flash at
the same price. If Google's notice changes, or calls to 3.6 Flash start failing, this is the size of a switch, measured
at `4dc45fd`:

- **`deploy/`: 31 files, 68 occurrences.**
  - Defaults: `Makefile:82-83`, `services/rag-api/config.py:84`, and `commands/lesson-12.2.sh:52`,
    `lesson-12.4.sh:24` and `lesson-8.4.sh:21`.
  - Prices: `shared/prices.py:18-27`, `services/rag-api/cost.py`, `config.py:153-156`,
    `services/frontend/chat.py:31-33`, `services/litellm/config.yaml`, `services/slm/compare_backends.py` and
    `evals/route_probe.py`.
  - Service, eval and test lines.
  - `evals/sft/documind_sft_v1.manifest.json:37` is frozen provenance and stays.
- **Generated and shared files:** 101 IDE demo files, regenerated from the pages; 2 files in `tools/`; `CLAUDE.md`.
- **36 lessons.**
  - 10 fail check_lesson until rebuilt: 3.4, 3.8, 4.4, 6.2, 10.4, 11.6, 12.2, 12.3, B.2, B.5.
  - 21 name the model in prose or outputs.
  - 5 name it only in build.py.
- **Lines to review, not just rename:**
  - B.5's claims about the knobs (temperature ignored, the thinking levels), which describe 3.6 Flash and which 3.1
    builds on;
  - two comments on 3.6 Flash's introductory price;
  - `evals/tune.py:23`'s tunable set, which 12.1-12.3 assert.

A switch would start with one call on the author's lane, confirming that Gemini 3.8 Flash answers on `global`.

### 3.3 Hazards a learner can trigger, named on the pages and fixed after 6 December

- **`path=clouddeploy`** in `documind-cd.yml` rolls out `run-service.yaml`, which sets three environment variables and
  a literal `PROJECT_NUMBER` on us-central1. It would break `documind-api`, so 11.1-11.3 say not to use it.
- **`make deploy-services` and `make up`** release the API without the gate. 11.2 and 11.7 say so.
- **`make smoke-all`** runs eight smokes, including the gateway's and the SLM's (`Makefile:816-822`), so it is red
  without Module 9's services. 11.3's proof uses a smoke of the deployed services instead.

## 4. How the work runs

### 4.1 Two tracks, from tomorrow

- **Kit track.**
  - One PR per change, with tests.
  - New behaviour sits behind a switch that defaults off.
  - No line is inserted inside a span a page quotes.
  - Every kit PR also rebuilds every page under Python 3.12 and shows the diff. check_lesson sees quoted lines, but not
    the facts builds assert: 4.8's emitter list, 5.4's `SYSTEM`, 6.6's +3/+5 checkpoints, the chat row that 5.1, 5.5,
    5.7 and 11.5 parse, 10.4's line-number read of `mk/agents.mk`, 12.3's eleven candidate pairs, 7.4's ablate lines.
- **Page track.**
  - Writers work in isolated worktrees from a named base branch, as in wave 1a.
  - Integration is central: the manifest entry (slug, topic, status), the IDE demos and their reviewed digest, cell
    summaries, `deploy/INDEX.md`, check_lesson, audit_pages and CI.
  - A page starts when its kit merges, or earlier against the kit's OFFLINE output, with placeholders for lane values.
  - Where a cohort scope proves less than the manifest's proof, the page PR rewords the proof and says so: 5.8, 6.9,
    10.1-10.3, 10.10 and 11.3 at least.
- **Concurrency:** four to six writers at a time, on disjoint files.

### 4.2 Files with one owner and a fixed order

| File | Order |
|---|---|
| `commands/agent_patterns.py` (new) | KB, then K-10.1, K-10.2, K-10.3 |
| `services/agent/agent.py` | 10.7-A, then 10.7-C, then 10.8-B |
| `services/chat/brains.py`, `tools.py` | 10.7-B adds three lines outside quoted spans; 10.8-A changes the quoted `search()` lines, so 5.1 is rebuilt |
| `evals/run_eval.py` | W2-A only; later PRs import it |
| `commands/release.py`, `mk/release.mk` (new) | R1, then R2, R3, R5 |
| `mk/memory.mk` (new) | 6.8-A creates it; 6.1-A and 6.9-A add to it |
| `mk/evaluation.mk` (new) | W2-E creates it; W2-F+G add to it; 10.8-C extends the attack runner |
| `mk/agents.mk` | append only: 10.4's build finds the route-eval recipe by its position |
| the `.PHONY` line; the chat-pins steps of `checks.yml` and `documind-dryrun.yml` | every PR adds lines; merged in order, rebased at merge |

### 4.3 The author's live runs

- **Six batches, Monday to Wednesday** (section 6).
- **A run list the Friday before each batch:** one consolidated list with every command, the data file it fills and
  its rupee estimate.
- **The round trip:** outputs come back by Wednesday with identifiers replaced, and pages are rebuilt on Thursday.
- **Probes first:** facts no lane has shown go into batches 0 and 1, before any page claims them:
  - Agent Engine's runtime;
  - thinking at HIGH, and stop sequences;
  - `count_tokens` with tools on `global`;
  - Gemini CLI headless;
  - the first keyless dispatch.
- **The last batch** is kept for retakes.

### 4.4 Learner kit releases, each with the author's go-ahead

| Release | Date | Carries |
|---|---|---|
| L1 | Thu 29 Oct | The fixes, 2.5's rewrite stage, 2.6's offline eval, and Module 0's recorded pages. The rewrite stage is in the rag-api image that learners build with `make up` in the pre-work week (31 Oct - 6 Nov) |
| L2 | Thu 12 Nov | Wave 2's eval kit (no image changes) |
| L3 | Thu 19 Nov | Wave 3's commands, plus two changes Module 5's pages show: the A2A peer's cap of 12 (5.5) and the chat fence, which defaults off (5.1) |
| L4 | Thu 26 Nov | Wave 4, and the Module 10-11 commands merged by then |
| L5 | Thu 3 Dec | Wave 5's image changes: chat (10.7-B), agent (10.7-C, 10.8-B) and rag-api (12.4). Those pages carry a pull-and-redeploy step for the one service |

## 5. Calendar

| Week | Kit track | Page track | The author |
|---|---|---|---|
| Thu 8 - Fri 9 Oct | Fixes (a)-(f), and (g) verified; 2.5-A; 2.6-B; KB; 10.9-A; W2-A | #70's port; 2.3's addition; 3.9; 4.3; 8.3 | Decisions 1-8; ask TypeSafe for docs, a key and terms |
| Mon 12 - Fri 16 Oct | Merge those (2.5-A by Wed 14); build W2-B+C, W2-D, W2-E, 6.8-A, 5.8-A, R1 | Drafts of 2.5, 2.6 and 8.4 | Review the fixes first; batch 0's run list on Fri 16 |
| 19-23 Oct | W2-F+G, K-10.1, 6.1-A, 6.9-A, 10.7-A, R4; 2.6-C when TypeSafe answers | 3.1, 3.2, 3.3, 3.6, 4.5 (after the bench, W2-D and W2-E); 6.8; 5.8 | **Batch 0**; batch 1's run list and the Jev stand-in decision on Fri 23 |
| 26-30 Oct | K-10.2, K-10.3, K-10.5, 10.8-A, 10.11, R2, R3 | 4.9, 6.1, 6.9; 5.1's and 5.2's additions; wave 1b and wave 2 from batch 1 | **Batch 1**; L1's go-ahead on Thu 29; 5.8's stretch go/no-go on Fri 30 |
| 2-6 Nov | 10.7-B, 10.9-B, 10.10, R5, R6 | Wave 1b merged Thu 5; drafts of 8.1, 8.2 and 11.1-11.3 | **Batch 2**; sessions Sat 7 and Sun 8 |
| 9-13 Nov (Diwali week) | 10.7-C, 10.8-B, 10.8-C | Wave 2 merged Thu 12; drafts of 10.1-10.3, 11.7, 11.8 and 12.4; 12.3's addition | No batch; L2 on Thu 12 |
| 16-20 Nov | Fixes the probes and batch 3 call for | Wave 3 merged Thu 19; drafts of 10.5 and 10.7-10.11 | **Batch 3**; L3 on Thu 19 |
| 23-27 Nov | (none) | Wave 4 merged Thu 26; wave 5 rebuilt from batches 3 and 4 | **Batch 4**; L4 on Thu 26 |
| 30 Nov - 4 Dec | (none) | Wave 5 merged Thu 3 | **Batch 5** (retakes); L5 on Thu 3 |

If reviews run slower than this, waves 2 and 3 can slip a week without missing their batches. The fixes, the model
switch, 2.5-A, KB and 10.9-A cannot: L1, batch 0 and Module 10's critical path depend on them.

## 6. The author's live-run batches

| Batch | Dates | Runs | Model calls, about |
|---|---|---|---|
| 0 | Mon 19 - Wed 21 Oct | Module 0 from a blank project (0.1-0.4's 34 placeholders); B.2, B.4, B.5 (7); 10.9's Agent Engine probe, which deletes what it creates | small; the probe "a few rupees" |
| 1 | Mon 26 - Wed 28 Oct | 2.5; 2.6 (Jev live if ready, else recorded); 3.1, 3.2, 3.3, 3.6, 4.3; 4.5's judge capture. Probes: 11.1's first keyless dispatch, 10.1's thinking levels on the bench, 6.1's `count_tokens` with tools, 10.10's Gemini CLI headless and Docker in Cloud Shell | Rs 270-350, plus Jev, a Cloud Build and Evaluation |
| 2 | Mon 2 - Wed 4 Nov | 4.5's 20 rows labelled by the author and one peer; 4.9; 5.8, 6.1, 6.8, 6.9; 5.1's optional call and 5.2's doc-types box; retakes for waves 1b and 2 | Rs 140-210, plus Model Armor |
| 3 | Mon 16 - Wed 18 Nov | 8.1 and 8.2 (one lane session of about 3.5 hours); 8.3's calibration; 11.1, 11.2, 11.3; 11.7's two drills; 10.9's managed peer; 10.11's held fault; 12.3's base comparison. Probes: 10.1-10.3's patterns (stop sequences, plan-and-execute's call count). Wave 3 retakes | Rs 175-340, plus Agent Engine |
| 4 | Mon 23 - Wed 25 Nov | 10.1, 10.2, 10.3, 10.5, 10.7, 10.8, 10.10, 11.8, 12.4; wave 4 retakes | Rs 275-470, plus the Ralph loop's cap |
| 5 | Mon 30 Nov - Wed 2 Dec | Wave 5 retakes only | - |

- **Model calls:** about Rs 850-1,400 in all, from the reviews' estimates.
- **Retakes:** each wave's captures fall at least one batch before its deadline, so a failed run can be retaken in
  time. The Diwali week (9-13 Nov) has no batch.
- **Prices no plan states:** Jev, Agent Engine, Model Armor, Cloud Build, Evaluation, and the cap set for the Ralph
  loop. These come on top.
- **The lane costs more than the calls.** At Mumbai list prices it bills Rs 1,057 a day on a SMALL index shard
  (Rs 2,666 on MEDIUM) just by existing:
  - kept up from now to 6 Dec: about Rs 63,000 (Rs 160,000);
  - up only for the six batches, about 18 days: about Rs 19,000 (Rs 48,000), plus whatever the sessions need.

  Tearing down cleanly needs fix (b) and a `make up` per batch (decision 7).

## 7. Lesson by lesson

Kit sizes are engineer-days. "Runs" gives the batch and the rupee estimate for model calls. "If the kit slips" is the
cut line that still lets the session run.

### Wave 1b (Fri 6 Nov)

| Lesson | Cohort scope: what the page proves | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 2.5 Rewrite the query before retrieval, and measure it | A rewrite stage on `/v1/query` behind `QUERY_REWRITE` (off). Rerank and generate keep the original question, and a literal guard keeps codes and figures. Ablate arms on the 47 golden rows and 24 paraphrases give recall@k and MRR. The page must read right if there is no lift: dense20 then rerank5 already measured 0.96 recall and 0.91 MRR on 8 Sept | 2.5-A (3.5): `shared/query_rewrite.py` (standard library only), `services/rag-api/rewrite.py`, two config switches, one call line in `main.py` (`/version` untouched), `ablate.py --rewrite --paraphrases`, `tools/check_retrieval.py`'s namespace, tests. Rebuilds 2.1 and B.4 (fix B.4's `n=4` excerpt). Merge by Wed 14 Oct to reach L1 | 1, about Rs 20 | The module, the ablate arm and the tests (1.5 days, no image change); Level 4 reads the planned stage |
| 2.6 Decide answer-or-refuse with a System One model (Jev) | An offline decision eval through `/v1/passages`: the empty-pool rule, the generator and Jev on the 65 golden rows (47 answerable, 18 not). It reports refusal recall and answer rate with Wilson intervals, calibration, latency and rupees. Jev sits between rerank and generate in the diagram, but not on the request path in the cohort. Only tenants whose policy is `any` are sent (57 rows) | 2.6-B (2.5): `shared/system_one.py` (`JEV_MODE=off\|recorded\|live`), `evals/decide.py`, `mk/retrieval.mk`, tests. 2.6-C (1.5), once TypeSafe's docs and key arrive: the adapter | 1, Rs 60-100 plus Jev | The rule and generator arms, printing "Jev not available". From Fri 23 Oct, last resort: a flash-lite stand-in, labelled as one |
| 2.3 (addition) | A theory level: the bi-encoder built the pool and the cross-encoder orders it. It points to B.4 rather than repeating it | none (0.5) | none | - |
| 2.2 (#70's port) | The author's help desk, two vectors on acme and the RRF panel, moved from old 5.2's paths onto 2.2's page | none | as #70 | - |

### Wave 2 (Fri 13 Nov)

Shared kit, cheaper than one PR per lesson:

| PR | What it adds |
|---|---|
| W2-A eval rows (2) | `run_eval.py` keeps each row's answer and citations, and gains `quote_check()`, `anchors_found()` and `row_verdict()`. `DOCUMIND_EVAL_PASSAGES=1` prints passage-level quote support and must_retrieve recall. It is an environment switch rather than a flag because 1.6 and 4.2 quote `main()` and the `eval-live` recipe. With it off, the output is byte-identical |
| W2-B+C prompt bench and exemplars (3.5) | `evals/prompt_bench.py` and `mk/generation.mk`. Retrieval is fixed per row and the kit's own `generate()` answers. A recorder sets the thinking level or a temperature. `--add-rule` and `--drop-rule` act in memory only, so `generator.py` is untouched. Also `route_eval.py --exemplars kit\|none\|FILE` |
| W2-D prompt versions (1) | `prompt_versions.json` maps `documind-rag@v3` to the hash of `SYSTEM` and `DATED_RULE`. `make prompt-version`, and a test that fails when `SYSTEM` changes without a new version |
| W2-E judge agreement (3) | `evals/agreement.py` (Cohen's kappa), `judge_agree.py` and `build_judge_set.py`; `judge.py --save-rows`; 20 frozen rows. 4.2 changes by one sentence |
| W2-F+G triage and attack runner (4.5) | `evals/triage.py`, plus `evals/adversarial/attacks.jsonl` and `run_attacks.py` under uplift F10's names, so 10.8 extends this runner rather than building another |

| Lesson | Cohort scope | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 3.1 See run-to-run variance and thinking levels | Five runs of one row at LOW and HIGH: distinct wordings, pass k/5, thought tokens, rupees. A temperature of 2.0 is sent and shown not to change the distribution. Links to B.5 | W2-A, B | 1, about Rs 14 | A REST loop and usage rows at LOW, plus an in-page cell |
| 3.2 Chain of thought and few-shot | Thinking level as chain of thought, measured on the 11 join rows at LOW, MEDIUM and HIGH. One prompted-reasoning rule against native thinking. Few-shot: the router's 8 exemplars on and off, with intervals | W2-B, C | 1, Rs 45-65 | In-page cells |
| 3.3 Prompt failure modes | A live eval's failing rows, read with their passages. Three one-rule fixes in the bench, each re-run with the 8 refusal rows as a guard. Nothing is committed: `SYSTEM` must equal `make_trainset.py`'s copy, which 12.1 asserts | W2-A, B | 1, about Rs 50 | `eval-live REPORT=` and one cell per fix |
| 3.6 Check quotes and version prompts | Quote support at passage level across a source. The prompt's text bound to its version. A v4 candidate built on a branch, its quotes checked, then removed | W2-A, D | 1, about Rs 16 plus a Cloud Build | The version check and a scoped run |
| 3.9 System design: fact-checking (design page) | The capstone rubric's five dimensions: three rejected options with the thresholds that would change them, cost at 1k, 10k and 100k, what breaks at 10×, and four failure modes from existing kit paths | none | none | - |
| 4.3 Place evals in the pipeline | Where each eval runs, and what it can and cannot catch. CI never calls the model; the candidate gate applies 9 thresholds; live traffic has usage rows and two alert policies. The stream's row says "answerable" unless the pool was empty (`main.py:516-518`) | none | 1, Rs 11-36 | The matrix and 4.2's artefacts |
| 4.5 Check the LLM judge against people | The learner labels 20 rows. Kappa against a second reader and against the judge, with a CUT slider | W2-E | 1: the judge capture (about Rs 41); 2: the author's labels and one peer's | The data files and a standard-library kappa cell |
| 4.9 Read the failures, then attack your pipeline | Ten failing rows noted before the 8 causes are shown. Then an attack set on rag-api's doors, built on 4.8's probes, with the attack success rate with the guard off and on | W2-A, F+G; fix (g) for the candidate half | 2, about Rs 51 plus Model Armor | Triage by hand and one attack cell; the candidate half only with (g) |

### Wave 3 (Fri 20 Nov)

| Lesson | Cohort scope | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 5.8 Human in the loop | Escalation and clarification on the case desk's existing hand-off, on the lane. Approval (pause, a second person, resume; the requester's own approval refused) runs offline, on a new `services/chat/approval.py` that the service does not import. `BLOCKED` and the refuse node stay, because 5.4, 5.5 and 5.7 quote them. The uplift's D1-D3 are about 20-25 days and would break those three pages | 5.8-A (3.5). Stretch 5.8-B (8-11, plus lane days): an approval wired into the service behind `agent_actions=approval`, which rebuilds 5.6 and 4.8. Go or no-go on Fri 30 Oct | 2, Rs 2-8 | The approval node written in a page cell from brains.py's quoted pieces |
| 6.1 Assemble the context | One turn's context by source, per brain, with tokens and rupees: system prompt, tool declarations, thread, question, tool results. A `top_k` Change-it | 6.1-A (2.5): `commands/context_sources.py` with `OFFLINE=1`; `make context-sources` | probe in 1; 2, Rs 11-19 | A page cell |
| 6.8 Checkpoint and resume | The checkpoint history read back (`make thread`). A cut-off turn resumed offline. A lane thread replayed and forked locally (`make replay`) | 6.8-A (3.5): `thread_read.py`, `thread_replay.py`, `mk/memory.mk`; one lane run before merge | 2, Rs 7-10 | 6.6's thread cell, extended |
| 6.9 Budget working memory | The thread grows while each call's context stays under a ceiling. A new `context_window.py`, not wired into the service; `make window-check` over 20 scripted turns; full against windowed with Gemini, locally; the write rules (masking, the Desk's 300 characters). The build plan's "existing trim" does not exist: every call resends the thread | fix (f), then 6.9-A (4) | 2, Rs 70-115 | langchain's context-editing middleware in a page cell |
| 5.1 (addition) | Parallel tool calls: two `retrieve` calls in one message run at once, and a shared chunk is numbered once (offline, scripted model) | none | optional, under Rs 1 | The definitions row |
| 5.2 (addition) | Two sentences back to 5.1. A `make doc-types` setup box, applied and then reset for 5.5's unknown state. The stale references fixed | none | 2, under Rs 1 | The sentences and a note |

### Wave 4 (Fri 27 Nov)

| Lesson | Cohort scope | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 8.1 Pub/Sub, mapped to Kafka | One upload traced from object to push, ack, records and answer. The subscription's settings. A burst squeezed to five instances. A 13-row Pub/Sub-to-Kafka table | none | 3, under Rs 5 and about 1.5 lane hours | The table and the trace |
| 8.2 Change a chunker, re-embed and reconcile | Both chunker twins edited to 400/50: `services/ingest/main.py:105` and `shared/documind_corpus.py:38`, not `parser.py` as the build plan says. The handbook re-issued as new bytes; reindex, reconcile to drift 0, eval-live by source; revert by redeploying the original tag. Sizes of 600 or more change nothing on the handbook | a twin-chunker test (0.5-1) | 3, under Rs 20 and about 2 lane hours | Drop eval-live and the token call |
| 8.3 Size RAG for ten million documents | A build-time calculator over kit constants, with a dated lesson-side module for the facts the kit lacks (prices, quotas, shard capacity). It ends with what breaks first at 10M (the fingerprint's quadratic reads, the 1,200 s nightly walk, 30 in flight, one replica) and what the kit would change | none | optional calibration, Rs 0 | The calculator and the top three limits |
| 8.4 System design: self-updating docs (design page) | A change-ripple panel. Three rejected options the kit itself records. Failure modes, with what alerts and what does not (no lag alert on the main subscription; no nightly walk by default). Cost at three scales from 8.3 | none | none | Static tables |

### Wave 5, Module 10 (Fri 4 Dec)

The shared bench comes first. **KB (6):**
- `commands/agent_patterns.py`: the loop on the Desk agent's toolset;
- `agent_turn.py`: `make agent-turn PATTERN= THINKING= DESK= OFFLINE=1`;
- `evals/agent_tasks.jsonl` and `agent_eval.py`: runs, pass@k, save, replay, best-of, compare;
- `evals/paired.py`;
- `desk_calc.unsupported()`.

It changes nothing in `services/chat`, so it waits on none of the uplift's chat-service PRs. The uplift's own order would put about 80 task-days of prerequisites before 10.1.

| Lesson | Cohort scope | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 10.1 Observe-think-act and ReAct | Native thinking against a prompted ReAct loop and a plan-first prompt, on the same calculator rows: correct answers, thinking and visible tokens, rupees. A Change-it on the parser's "Observation:" cut | KB, K-10.1 (3) | probes in 1 and 3; 4, Rs 40-60 | The loop at minimal against high; ReAct as a scripted cell |
| 10.2 Plan-and-execute | The loop against plan-and-execute and ReWOO (placeholders, waves, a replan after a refusal) on chained rows: calls, rupees, correctness. A cheaper model for the executor | K-10.2 (4) | 4, Rs 60-90 | The loop on multi-step rows; plan-and-execute as a scripted cell |
| 10.3 Critic and refiner | pass@1; pass@3 with reflection notes; best-of-3 chosen by the deterministic figure check. A note cannot launder a number | K-10.3 (2.5) | 4, Rs 60-90 | KB alone: pass@k and best-of from one saved run |
| 10.5 Run a desk as an agent | `check_args` refuses an invented cap. Arms B, C and A* on the same 12 rows, with a paired difference labelled indicative (dev rows only). The mixture-of-agents vote as Level 5 | K-10.5 (5), all client side | 4, Rs 40-60 | Three existing arm reports side by side |
| 10.7 A2A hand-off; loops and deadlocks | The ADK brain hands one question to the A2A peer, off unless `PEER_URL` is set. The peer is capped at 12 model calls. A caller cycle is refused by construction (`check_callers --graph`) and at run time (`PEER_CHAIN`, off) | 10.7-A (1.5; rebuilds 5.5), 10.7-B (5.5), 10.7-C (3.5; rebuilds 10.6); 10.7-D optional (2) | 4, Rs 10-20 | The hand-off offline, served as 10.6 serves the peer; the cycle refused by construction |
| 10.8 Defend agents against injection | An injected vendor note and a poisoned MCP server, run against three things: the controls that exist; a fence and an exit scrub (`AGENT_FENCE`, `AGENT_SCRUB`, off); and tool pins (`TOOL_PINS`, off). `make attack-eval` shows 0 enforced failures and an attack success table | 10.8-A (3; rebuilds 5.1), 10.8-B (3.5), 10.8-C (about 3, on W2-G's runner) | 4, under Rs 30 | The set against today's controls, with the chat brains' rate shown as the gap |
| 10.9 The peer on Google's managed agent platform | 10.6's peer on Vertex AI Agent Engine: deploy, ask (the roster refuses zeta), trace, smoke, sessions, tear down. A Cloud Run against Agent Engine table, filled from the learner's own runs | 10.9-A (2.5): a probe in the authoring repo only, which the author runs in batch 0. 10.9-B (5.5): no change to `services/agent`, no Terraform | probe in 0; 3. Agent Engine price unknown; torn down by default | The page names a failed probe fact and reads the author's dated capture |
| 10.10 Coding agents | A Ralph loop under a strong and a weak oracle: the oracle has no network, there is a rupee cap, and it never applies or pushes. An AI code reviewer scored on six seeded defects. Paper-to-code through `desk_calc`'s rules and selftest | one PR (6.5, plus 1 for an egress proxy) | probe in 1; 4, capped by `RALPH_BUDGET_INR` | Levels 0-2 offline and the reviewer live; the loop as the author's dated capture |
| 10.11 System design: incident auto-remediation (design page) | A held fault diagnosed by rules with 0 model calls (`make remediate`). The person runs the printed rollback, then verify and restore. The runbooks are drawn from the kit's alert policies | one PR (4.5): kit work, not large | 3, about Rs 10-20 | The drill, with the plan read by hand |

### Wave 5, Modules 11-12 (Fri 4 Dec)

| Lesson | Cohort scope | Kit | Runs | If the kit slips |
|---|---|---|---|---|
| 11.1 Keyless build and deploy | A build and a deploy from GitHub Actions with no key, through workload identity federation (`wif.tf`, `sa.tf` and `documind-cd.yml` exist). A branch dispatch is refused by the ref clause. Zero user-managed keys | R1 (2.5, plus 1 reserved for the first dispatch): `commands/release.py` (`ci-vars`, `keys`), `mk/release.mk` | the first dispatch as a probe in 1; 3, a few rupees | The author's recording, plus the local operator path |
| 11.2 Gate the exact candidate | The gate bound to the exact revision: `make gate` records the revision, sha, digest and report hash, and `promote-gated` refuses any other revision | R2 (3) | 3, Rs 60-115 | `release-candidate`, then `eval-live REPORT=`, with no code |
| 11.3 Promote, roll back, repair | A gated promote. A mistyped model gated red. A forced promote, a red smoke, a timed rollback and a repair. The proof uses a smoke of the deployed services, not `smoke-all` | R3 (2) | 3, Rs 75-145 | `time make rollback` and `make smoke` |
| 11.7 Production gotchas | A registry of about 12 gotchas, each with a drill, a detector and a lever. Two drills at Rs 0: pinned traffic, and a routine deploy that drops a hotfix | R4 (4): `ops/gotchas.json`, `commands/gotchas.py` | 3, about Rs 5 | A build.py table and page cells |
| 11.8 Capstone and handover | `make capstone-check` (pass or fail per rubric component) and `make handover`. The rubric renumbered and shown to learners before 6 Dec | R5 (4, plus a day of the author's for a reference fork) | 4, Rs 0 | The rubric and a checklist |
| 12.4 Eval-gated self-improvement | A production row becomes a proposed rule; a person accepts it; it becomes a golden row, then a v4 candidate; the gate runs; the candidate is promoted or rolled back. A "never refuse" proposal is stopped | R6 (5): `prompt_rules.json`, `evals/improve.py`. `PROMPT_VERSION` defaults to v3, which changes nothing | 4, Rs 65-115 | The proposer as a page cell; the rule added by hand |
| 12.3 (addition) | "Compare the models": the untuned base on a no-traffic tag, eval-live against it, and three reports compared with their generation times | none (1) | 3, about Rs 15 | Generation times added to step 5's cell |

## 8. Decisions for the author

| # | Decision | Recommendation | Needed by |
|---|---|---|---|
| 1 | Go ahead with this plan and its cohort scopes | **decided 7 Oct: yes, every track now** | - |
| 2 | Switch the kit to Gemini 3.8 Flash | **decided 7 Oct: no, the kit stays on `gemini-3.6-flash`** (3.2) | - |
| 3 | Kit fixes (a)-(d) and (f); verify (g), and fix it if true | **decided 7 Oct: yes** | - |
| 4 | An explicit SMALL index shard for new lanes (fix e) | **decided 7 Oct: yes** | - |
| 5 | Jev: TypeSafe's docs, a key, and the terms (may the course publish the API's shape, recorded outputs and metrics; where data is processed and kept) | **13 Oct: the request to TypeSafe is drafted; the author sends it.** With no answer by Fri 23 Oct, 2.6 runs with the rule and generator arms and `JEV_MODE=off`; 2.6-C records Jev's arm when a key arrives | Fri 23 Oct |
| 6 | How about 75 PRs are merged | **decided 7 Oct: the author merges every PR**; revised 13 Oct on the author's instruction: Claude squash-merges each once `checks` passes, through a merge train that replays each PR on the merged stack and rebuilds the pages it touches | - |
| 7 | The lane between batches: kept up, or torn down after each | the author's call: about Rs 63,000 up to 6 Dec on SMALL, against about Rs 19,000 for the batches alone. Recommendation (13 Oct): tear down after each batch; a redeploy costs one `make ingest-corpus`, about Rs 912, four times; 0.4's last run tears it down either way | Fri 16 Oct |
| 8 | PR #70 | port it onto 2.2 | now |
| 9 | 5.8's scope: escalation live, approval offline, the wired approval as a stretch | **decided 13 Oct: both built.** Approval offline (5.8-A, #108) and wired into the chat service (5.8-B, #184) behind `tenant_settings.agent_actions = approval`, off until an operator writes it; the live smoke is batch 3's. The 30 Oct go/no-go is moot | - |
| 10 | 10.1-10.3 come before the Desk lessons that teach the calculators | **decided 13 Oct: kept**; the pages were built in that order with the `make doc-types` setup line | - |
| 11 | 11.1: do learners use their own GitHub fork with Actions? Required reviewers need a public repo or a paid plan | **decided 13 Oct: yes**, with the author's recording as the fallback (`INFRASTRUCTURE.md` section 3, #172) | - |
| 12 | 10.10's sandbox, identity, caps and budget (gap plan G-decisions 6 and 8) | **decided 13 Oct: as built** (#152): an oracle with no network, a model-only credential the author creates and deletes, `RALPH_BUDGET_INR` required; the egress proxy (#177) behind `RALPH_EGRESS=proxy`, off by default, lets the agent's container reach `aiplatform.googleapis.com:443` and nothing else; batch 1's probe proves it on Docker | - |
| 13 | 10.9: reuse `documind-agent-sa` for the cohort, and tear down by default (uplift decisions 23 and 26) | **decided 13 Oct: yes**, as built (#148): `make managed-peer-down` ends every drill | - |
| 14 | Switch defaults (uplift decision 9) | **decided 13 Oct: every new switch off** (`QUERY_REWRITE`, `JEV_MODE`, `PEER_URL`, `PEER_CHAIN`, `TOOL_PINS`, `AGENT_FENCE`, `AGENT_SCRUB`, `ADK_PLANNER`, `RALPH_EGRESS`, `GATE_PROMPT`, `agent_actions`), except the peer's cap of 12 model calls a task | - |
| 15 | 4.5's second reader | the author's call: one peer labels the 20 rows once (`make label-sheet READER=L2`) | Fri 30 Oct |
| 16 | The capstone rubric, renumbered and shown to learners before 6 Dec | **decided 13 Oct: done** (#179): the rubric's 17 lesson numbers are the manifest's and it cites only files that exist; lesson 11.8's page shows it with its notes; the four document templates ship in `deploy/capstone/templates/` and fail `make capstone-check` until filled; "your own corpus" is a tenant other than acme, globex and zeta | - |
| 17 | The first weekend falls on Choti Diwali (Sat 7 Nov) and Diwali (Sun 8 Nov) | the author's call; no batch is planned for 6-10 Nov | before the cohort's calendar goes out |
| 18 | Sat 5 Dec carries 11 lessons and Sun 6 Dec carries 12 | **proposed 14 Oct: the split below** (six live lessons a session, the rest read ahead); the author confirms | Fri 27 Nov |

### 8.1 Decision 18: what is taught live on 5 and 6 December, and what is read ahead

The rule: a lesson is taught live when its proof is a thing the learners watch being decided in minutes on the kit (a
drill, a gate, a refusal); it is read ahead when its proof is a figure the page already carries, a recording the
author made (a long job, a managed platform, a loop), or a design page. Six live lessons in a two-hour session is about
twenty minutes each, demo-led. The read-ahead lessons are announced the Monday before, each with the one question a
learner answers from the page.

**Saturday 5 December, Module 10 (11 lessons).**
- Live (6): 10.1 observe-think-act and ReAct (the `THE CUT` line removed, one invented observation caught); 10.3 the
  critic and refiner (one retry; pass@1 against best-of-3); 10.4 route to a specialist (the router's decision on one
  question); 10.5 a desk as an agent (an invented cap refused by `check_args`); 10.7 the hand-off and a refused cycle;
  10.8 the injected note against the fence and the scrub, and the poisoned tool refused by the pins.
- Read ahead (5): 10.2 plan-and-execute (its figures are on the page); 10.6 the A2A peer's trace; 10.9 the managed
  platform (the author's Agent Engine recording); 10.10 coding agents (the Ralph loop is a recording); 10.11 the
  incident design page.

**Sunday 6 December, Modules 11 and 12 (12 lessons).**
- Live (6): 11.1 a keyless build and deploy; 11.2 the gate on the exact candidate (a red gate refusing a promote);
  11.3 promote, break, roll back; 11.7 one gotcha drill (`latest_takes_all`); 11.8 `make capstone-check` on the canned
  fork, one component deleted, the check failing; 12.4 one production row turned into a gated prompt candidate.
- Read ahead (6): 11.4 debugging a wrong answer; 11.5 usage reconciliation; 11.6 routing, budgets and shutdown
  controls; 12.1 to 12.3 tuning (long managed jobs; the author's recordings).

## 9. Risks, and what is cut first

1. **The author's time.** Six batches, about 75 reviews and merges, and decisions by their dates; batch 4 alone carries nine
   lessons. Mitigation: run lists ready the Friday before, probes early, and a retake batch at the end.
2. **Behaviour no lane has shown.** Each item is checked by a probe in batch 0 or 1 before any page claims it, and the
   proofs report comparisons, not winners:
   - Agent Engine's runtime identity, region and scale to zero;
   - thinking at HIGH, and stop sequences;
   - `count_tokens` with tools on `global`;
   - Gemini CLI headless;
   - Model Armor's verdict;
   - the first keyless dispatch. STS is not among the kit's 40 APIs, and the CI account may lack the storage and
     logging roles that `gcloud builds submit` needs.
3. **A healthy lane may not show what a lesson needs.** Mitigation: flash-lite arms, planted cases built at build time,
   and "no difference" printed with its interval. The cases at risk:
   - identical answers (3.1);
   - no exemplar effect (3.2);
   - too few failures (3.3, 4.9);
   - no flagged quote (3.6);
   - no lift (2.5);
   - a tie between patterns (10.1-10.3) or between arms (10.5).
4. **Coupled pages.** A kit line that a build asserts, rather than quotes, breaks silently. Mitigation: every kit PR
   rebuilds every page (4.1).
5. **Jev's access and terms.** Mitigation: the rule and generator arms ship regardless.
6. **Learners on old images.** A kit change to a deployed service after L1 needs a redeploy. Mitigation: the release
   train (4.4), and a redeploy step on each page that needs one.
7. **A deprecated model.** The kit stays on `gemini-3.6-flash`, deprecated on Thu 19 Nov, so the sessions of 21-22
   Nov, 28-29 Nov and 5-6 Dec run on it. Mitigation: 3.2 sizes the switch, should it become necessary.

**What is cut first, if time runs short:**
1. The stretch work: 5.8-B, K-P10 (ADK's planner switch), 10.7-D, and 10.10's egress proxy.
2. The extra patterns: plan-first in 10.1, ReWOO in 10.2.
3. Live captures, replaced by the author's dated recordings.
4. Last, a lesson ships at its cut line (section 7).

The fixes and 2.5's stage in L1 are not cut.

## 10. After 6 December

The full designs the cohort scopes leave out, by lesson:
- **2.5:** the stream and passages routes, `QUERY_REWRITE` in `make candidate`, HyDE and multi-query arms.
- **2.6:** Jev on the request path as `DECISION=off|shadow|enforce`, coordinated with uplift F5's context screen.
- **Module 3 prompt work:** a runtime prompt pin.
- **4.3:** the stream's answerable verdict.
- **4.5:** commissioned labels (gap S1).
- **4.9 and 10.8:** Hinglish and Devanagari attack rows (gap S8).
- **5.8:** the uplift's D1-D8 approval flow.
- **6.8:** heal at the next turn, and one turn per thread (K4, H6); the fork route (K9).
- **6.9:** wiring the window into the service (H3), long-term memory (H4), retention and erasure (H5).
- **8.2:** `make reembed`.
- **8.3 and 8.4:** an incremental fingerprint, a sharded walk, an explicit shard size with autoscaled replicas, and
  batch embeddings.
- **10.1-10.3:** P10's planner switch, N1, N3 and I2; P2's search, the to-do pattern and LLMCompiler; P9's beam
  search and LATS.
- **10.5:** a people-written test split (E4, E7), arm S, and the formal ship decision (C9).
- **10.7:** the hand-off eval and judge, the chat-row key, C7's shapes, a propagated deadline (R2), a breaker drill
  (R3), the peer's card (J6) and one trace across the hops (G3).
- **10.8:** F5 to F8 (or ADK's Model Armor plugin), and the refused-call log.
- **10.9:** the managed peer's own service account (I7), `adk web` (I3), managed sessions and Memory Bank (I5, I6),
  N4, N5 and S9.
- **10.11:** an agent alert policy (S4), a model for ambiguous incidents, and approve-and-execute.
- **11.1-11.3:** the Cloud Deploy path, and a gate on `deploy-services`.
- **11.7:** the registry entries that need G1, G2, H2, D1, N2, R4, K2, K3, S6 or D3.
- **11.8:** defences, assessors and retries.
- **12.4:** the chat brains' prompt.
