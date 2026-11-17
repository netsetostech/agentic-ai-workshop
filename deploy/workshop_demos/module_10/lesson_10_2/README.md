# Lesson 10.2: Plan first or decide each step: plan-and-execute

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 4 | [demo_04_plan_and_execute_a_plan_an_executor_one_replan_offline.py](demo_04_plan_and_execute_a_plan_an_executor_one_replan_offline.py) | Plan-and-execute: a plan, an executor, one replan, offline |
| 5 | [demo_05_rewoo_one_plan_with_placeholders_checked_and_run_in_waves_offline.py](demo_05_rewoo_one_plan_with_placeholders_checked_and_run_in_waves_offline.py) | ReWOO: one plan with placeholders, checked and run in waves, offline |
| 6 | [demo_06_change_it_switch_the_replan_off.py](demo_06_change_it_switch_the_replan_off.py) | Change it: switch the replan off |
| 7 | [demo_07_the_3_chained_rows_offline_and_a_cheaper_executor.py](demo_07_the_3_chained_rows_offline_and_a_cheaper_executor.py) | The 3 chained rows offline, and a cheaper executor |
| 8 | [demo_08_your_lane_plan_and_execute_rewoo_and_a_flash_lite_executor.py](demo_08_your_lane_plan_and_execute_rewoo_and_a_flash_lite_executor.py) | Your lane: plan-and-execute, ReWOO and a flash-lite executor |
| 9 | [demo_09_the_3_rows_on_your_lane_and_the_plans_they_saved.py](demo_09_the_3_rows_on_your_lane_and_the_plans_they_saved.py) | The 3 rows on your lane, and the plans they saved |
| 10 | [demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py](demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py) | When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py](optional/demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py) — Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer. On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls retrieve as a function when the instruction asks for tool code under /*ACTION*/, and what a written plan adds to a turn's calls and rupees.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4 and 10.1 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash and gemini-3.1-flash-lite on location global, and rag-api's /v1/passages as documind-ui-sa. Step 10's ADK planner runs offline in the same venv, and once, optionally, on the chat service after a redeploy. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's stored rows their classes. If you have not run it, run this now: every chained row is acme's. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4 and 10.1 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash and gemini-3.1-flash-lite on location global, and rag-api's /v1/passages as documind-ui-sa. Step 10's ADK planner runs offline in the same venv, and once, optionally, on the chat service after a redeploy. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's stored rows their classes. If you have not run it, run this now: every chained row is acme's. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

Operation: bash — run in the operator shell, in the kit (once, if lesson 10.1's setup line has not run: acme's stored rows get their classes).

### demo_04_plan_and_execute_a_plan_an_executor_one_replan_offline.py

For comparison, the loop on the row with the manager's cap. The filter keeps each model call, the tool it asked for, each calculator's result or refusal, and the totals. Do it: plan-and-execute on the same row

**`step_01_the_loop_on_the_same_row_first(session)` — Plan-and-execute: a plan, an executor, one replan, offline / Do it: the loop on the same row, first**

For comparison, the loop on the row with the manager's cap. The filter keeps each model call, the tool it asked for, each calculator's result or refusal, and the totals.

Operation: bash — run in the operator shell, in the kit (Rs 0: the loop on the stated-cap row, its calls only; the first run builds ~/graph-venv).

Expected shape, not a promised result:

```text
model call 1 (thinking low): in 333, thinking 64, visible 20 tokens, Rs 0.0960
  -> retrieve(query="notice period confirmed employee acknowledged in writing")
model call 2 (thinking low): in 2,426, thinking 64, visible 12 tokens, Rs 0.3578
  -> notice_end(ack_date="2026-10-05", days=60)
       = 2026-12-04: 2026-10-05 + 60 days = 2026-12-04 (Friday)
model call 3 (thinking low): in 2,567, thinking 64, visible 13 tokens, Rs 0.3764
  -> retrieve(query="earned leave encashed on exit")
model call 4 (thinking low): in 4,053, thinking 64, visible 11 tokens, Rs 0.5646
  -> encashable_days(balance=80, cap=45)
       = 45 days: min(80, 45) = 45 days
model call 5 (thinking low): in 4,168, thinking 64, visible 21 tokens, Rs 0.5856
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
model call 6 (thinking low): in 6,231, thinking 64, visible 17 tokens, Rs 0.8461
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 7 (thinking low): in 6,743, thinking 64, visible 32 tokens, Rs 0.9209
  -> no tool: the answer
7 model calls (12 at most), 3 searches, 3 calculations, 0 refused or failed tool calls; stopped by nothing
```

**`step_02_plan_and_execute_on_the_same_row(session)` — Plan-and-execute: a plan, an executor, one replan, offline / Do it: plan-and-execute on the same row**

Do it: plan-and-execute on the same row

Operation: bash — run in the operator shell, in the kit (Rs 0: plan_execute on the same row).

Expected shape, not a promised result:

```text
agent turn: pattern plan_execute, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  plan_execute (lesson 10.2): plan-and-execute: a planner call writes a numbered plan, an executor carries it out a step at a time with the desk's tools through ToolNode, a refused or failed step sends the rest back to the planner once, and a last call writes the answer from the steps' results
  the planner: gemini-3.6-flash (plan, replan and solve); the executor: gemini-3.6-flash (act; EXEC_MODEL= names another)
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I am a confirmed E3 employee at ACME on Rs 52,000 a month with 7 years 8 months of continuous service. My resignation was acknowledged in writing on 5 October 2026. I have 80 days of earned leave, and my manager says the encashment cap is 100 days. When does my notice end, how many leave days are encashed, and roughly what gratuity will I get?

model call 1 (plan, gemini-3.6-flash, thinking low): in 1,643, thinking 64, visible 127 tokens, Rs 0.3312
  the plan:
    1. Search for NP-03: retrieve {"query": "notice period confirmed employee acknowledged in writing"}
    2. Last day of notice: notice_end {"ack_date": "2026-10-05", "days": "<the days NP-03 states>"}
    3. Earned leave encashed on exit: encashable_days {"balance": 80, "cap": 100}
    4. Search for Code on Social Security, 2020, s.53(2): retrieve {"query": "gratuity fifteen days wages for every completed year of service"}
    5. Gratuity, an estimate: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
step 1: Search for NP-03: retrieve {"query": "notice period confirmed employee acknowledged in writing"}
  model call 2 (act, gemini-3.6-flash, thinking low): in 579, thinking 64, visible 20 tokens, Rs 0.1274
  -> retrieve(query="notice period confirmed employee acknowledged in writing")
       5 passages
         [1] hr_policy_2026.md, NP-03 — Notice period
         [2] it_act_2000.pdf (statute)
         [3] osh_code_2020.pdf (statute)
         [4] cgst_act_2017.pdf (statute)
         [5] osh_code_2020.pdf (statute)
step 2: Last day of notice: notice_end {"ack_date": "2026-10-05", "days": "<the days NP-03 states>"}
  model call 3 (act, gemini-3.6-flash, thinking low): in 801, thinking 64, visible 12 tokens, Rs 0.1506
  -> notice_end(ack_date="2026-10-05", days=60)
       = 2026-12-04: 2026-10-05 + 60 days = 2026-12-04 (Friday)
step 3: Earned leave encashed on exit: encashable_days {"balance": 80, "cap": 100}
  model call 4 (act, gemini-3.6-flash, thinking low): in 968, thinking 64, visible 11 tokens, Rs 0.1712
  -> encashable_days(balance=80, cap=100)
       refused: cap = 100 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states
  the step was refused
model call 5 (replan, gemini-3.6-flash, thinking low): in 2,142, thinking 64, visible 101 tokens, Rs 0.3783
  after: Step 3 was refused: cap = 100 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states
  the plan for the work still to do:
    1. Search for LV-07: retrieve {"query": "earned leave encashed on exit"}
    2. Earned leave encashed on exit: encashable_days {"balance": 80, "cap": "<the cap LV-07 states>"}
    3. Search for Code on Social Security, 2020, s.53(2): retrieve {"query": "gratuity fifteen days wages for every completed year of service"}
    4. Gratuity, an estimate: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
step 4: Search for LV-07: retrieve {"query": "earned leave encashed on exit"}
  model call 6 (act, gemini-3.6-flash, thinking low): in 1,076, thinking 64, visible 13 tokens, Rs 0.1863
  -> retrieve(query="earned leave encashed on exit")
       5 passages
         [6] hr_policy_2026.md, LV-07 — Leave on exit
         [7] osh_code_2020.pdf (statute)
         [8] osh_code_2020.pdf (statute)
         [9] hr_policy_2026.md, LV-01 — Earned leave
         [10] osh_code_2020.pdf (statute)
step 5: Earned leave encashed on exit: encashable_days {"balance": 80, "cap": "<the cap LV-07 states>"}
  model call 7 (act, gemini-3.6-flash, thinking low): in 1,335, thinking 64, visible 11 tokens, Rs 0.2180
  -> encashable_days(balance=80, cap=45)
       = 45 days: min(80, 45) = 45 days
step 6: Search for Code on Social Security, 2020, s.53(2): retrieve {"query": "gratuity fifteen days wages for every completed year of service"}
  model call 8 (act, gemini-3.6-flash, thinking low): in 1,491, thinking 64, visible 21 tokens, Rs 0.2443
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
         [11] payment_of_gratuity_act_1972.pdf (statute)
         [12] code_on_social_security_2020.pdf (statute)
         [13] code_on_social_security_2020.pdf (statute)
         [14] labour_codes_compliance_handbook.pdf (guidance)
         [15] labour_codes_compliance_handbook.pdf (guidance)
step 7: Gratuity, an estimate: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
  model call 9 (act, gemini-3.6-flash, thinking low): in 1,674, thinking 64, visible 17 tokens, Rs 0.2651
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 10 (solve, gemini-3.6-flash, thinking low): in 7,091, thinking 64, visible 32 tokens, Rs 0.9653
  -> no tool: the answer, from the steps' results

answer, as the Desk shows it (the model's text, then what code writes):
  Last day of notice: 4 December 2026 [1]. Earned leave encashed on exit: 45 days [6]. Gratuity, an estimate: Rs 2,40,000 [12].

  Worked out in code:
  - Last day of notice (NP-03): 2026-10-05 + 60 days = 2026-12-04 (Friday). The days from NP-03 [1]; the acknowledgement date from your message. The desk's count: calendar days, the first being the day after the written acknowledgement. A handbook that counts the days otherwise moves the date.
  - Earned leave encashed on exit (LV-07): min(80, 45) = 45 days. The balance from your message; the cap from LV-07 [6]. Condition: LV-07 bars encashment during probation: this figure holds only once probation is over.
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.

10 model calls (12 at most), 3 searches, 3 calculations, 1 refused or failed tool call; stopped by nothing
tokens: in 18,800, thinking 640, visible 365; Rs 3.0377 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: plan 1 call, Rs 0.3312 (gemini-3.6-flash); act 7 calls, Rs 1.3628 (gemini-3.6-flash); replan 1 call, Rs 0.3783 (gemini-3.6-flash); solve 1 call, Rs 0.9653 (gemini-3.6-flash)
plans: 2 written, 1 replan (at most 1 a turn)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

### demo_05_rewoo_one_plan_with_placeholders_checked_and_run_in_waves_offline.py

These functions need no framework and no model: agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs them. The cell reads the plan the scripted planner writes for chained-exit-e3 and prints what each step waits for and the waves. Then it prints what a refused value stops, four plans check_rewoo() refuses, one placeholder filled, and an extract worker's figure held to its quote twice. Offline, the corpus is ranked in Python, and a wave's searches share one interpreter: three cold searches side by side can outlast a search's budget, 25 seconds by default, and come back failed, as a slow rag-api's would. The kit's own docstring warns of it. RAG_TIMEOUT_S=90, the value the chat service is deployed with, gives them room.

**`step_01_the_plan_s_readers_at_rs_0(session)` — ReWOO: one plan with placeholders, checked and run in waves, offline / Do it: the plan's readers, at Rs 0**

These functions need no framework and no model: agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs them. The cell reads the plan the scripted planner writes for chained-exit-e3 and prints what each step waits for and the waves. Then it prints what a refused value stops, four plans check_rewoo() refuses, one placeholder filled, and an extract worker's figure held to its quote twice.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the plan's readers, no model).

Expected shape, not a promised result:

```text
8 steps read; check_rewoo refuses: nothing
  #E1 retrieve          takes -    runs after -
  #E2 retrieve          takes -    runs after -
  #E3 retrieve          takes -    runs after -
  #E4 extract           takes #E1  runs after -
  #E5 extract           takes #E2  runs after -
  #E6 notice_end        takes #E4  runs after #E1, #E2, #E3
  #E7 encashable_days   takes #E5  runs after #E1, #E2, #E3
  #E8 gratuity_estimate takes -    runs after #E1, #E2, #E3
wave 1: #E1, #E2, #E3
wave 2: #E4, #E5, #E8
wave 3: #E6, #E7
after #E5 is refused: (['#E6'], {'#E7': '#E5 was refused'})
refused: #E1 uses #E2 before #E2 runs: a step may use only the steps written above it
refused: #E2 gives cap the passages of #E1: a search returns passages, not a figure, so read the figure with extract
refused: #E1 calls payroll_update, which is not one of this desk's tools
refused: it has 13 steps, and a turn runs at most 12: the tools of a plan written once run with no model call between them
{'balance': 50, 'cap': 45}
(45, 'Earned leave is encashed on exit at basic pay, capped at 45 days.', None)
(None, 'Leave is encashed up to 45 days.', 'its quote is not written in the passages it was given')
```

**`step_02_rewoo_on_a_chained_row(session)` — ReWOO: one plan with placeholders, checked and run in waves, offline / Do it: ReWOO on a chained row**

Offline, the corpus is ranked in Python, and a wave's searches share one interpreter: three cold searches side by side can outlast a search's budget, 25 seconds by default, and come back failed, as a slow rag-api's would. The kit's own docstring warns of it. RAG_TIMEOUT_S=90, the value the chat service is deployed with, gives them room.

Operation: bash — run in the operator shell, in the kit (Rs 0: rewoo on the first chained row; RAG_TIMEOUT_S gives a cold wave room).

Expected shape, not a promised result:

```text
agent turn: pattern rewoo, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  rewoo (lesson 10.2): plan once (ReWOO): one planner call writes every step, a later one naming an earlier result by placeholder (#E1); code runs them in waves, the steps that wait on nothing together, an extract worker reading a figure from a search's passages; one solver call writes the answer from the evidence, and nothing replans
  the planner: gemini-3.6-flash (plan and solve); the executor: gemini-3.6-flash (extract; EXEC_MODEL= names another)
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I am a confirmed E3 employee at ACME on Rs 52,000 a month with 7 years 8 months of continuous service. My resignation was acknowledged in writing on 5 October 2026, and I have 50 days of earned leave. When does my notice end, how many leave days are encashed, and roughly what gratuity will I get?

model call 1 (plan, gemini-3.6-flash, thinking low): in 1,769, thinking 64, visible 202 tokens, Rs 0.3951
  the plan, written once:
    #E1 = retrieve[{"query": "notice period confirmed employee acknowledged in writing"}]
    #E2 = retrieve[{"query": "earned leave encashed on exit"}]
    #E3 = retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]
    #E4 = extract[{"what": "the days NP-03 states", "from": "#E1"}]
    #E5 = extract[{"what": "the cap LV-07 states", "from": "#E2"}]
    #E6 = notice_end[{"ack_date": "2026-10-05", "days": "#E4"}]
    #E7 = encashable_days[{"balance": 50, "cap": "#E5"}]
    #E8 = gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]
wave 1: #E1, #E2, #E3, together
  #E1 = retrieve(query="notice period confirmed employee acknowledged in writing")
       5 passages
         [1] hr_policy_2026.md, NP-03 — Notice period
         [2] it_act_2000.pdf (statute)
         [3] osh_code_2020.pdf (statute)
         [4] cgst_act_2017.pdf (statute)
         [5] osh_code_2020.pdf (statute)
  #E2 = retrieve(query="earned leave encashed on exit")
       5 passages
         [6] hr_policy_2026.md, LV-07 — Leave on exit
         [7] osh_code_2020.pdf (statute)
         [8] osh_code_2020.pdf (statute)
         [9] hr_policy_2026.md, LV-01 — Earned leave
         [10] osh_code_2020.pdf (statute)
  #E3 = retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
         [11] payment_of_gratuity_act_1972.pdf (statute)
         [12] code_on_social_security_2020.pdf (statute)
         [13] code_on_social_security_2020.pdf (statute)
         [14] labour_codes_compliance_handbook.pdf (guidance)
         [15] labour_codes_compliance_handbook.pdf (guidance)
wave 2: #E4, #E5, #E8, together
  #E4 = extract(what="the days NP-03 states", from="#E1")
    model call 2 (extract, gemini-3.6-flash, thinking low): in 2,062, thinking 64, visible 26 tokens, Rs 0.3203
       = 60, quoting "A confirmed employee at grade E3 or above serves a notice period of 60 days."
  #E5 = extract(what="the cap LV-07 states", from="#E2")
    model call 3 (extract, gemini-3.6-flash, thinking low): in 1,467, thinking 64, visible 23 tokens, Rs 0.2425
       = 45, quoting "Earned leave is encashed on exit at basic pay, capped at 45 days."
  #E8 = gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
wave 3: #E6, #E7, together
  #E6 = notice_end(ack_date="2026-10-05", days="#E4"), run as notice_end(ack_date="2026-10-05", days=60)
       = 2026-12-04: 2026-10-05 + 60 days = 2026-12-04 (Friday)
  #E7 = encashable_days(balance=50, cap="#E5"), run as encashable_days(balance=50, cap=45)
       = 45 days: min(50, 45) = 45 days
model call 4 (solve, gemini-3.6-flash, thinking low): in 7,052, thinking 64, visible 32 tokens, Rs 0.9603
  -> no tool: the answer, from the steps' results

answer, as the Desk shows it (the model's text, then what code writes):
  Last day of notice: 4 December 2026 [1]. Earned leave encashed on exit: 45 days [6]. Gratuity, an estimate: Rs 2,40,000 [12].

  Worked out in code:
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.
  - Last day of notice (NP-03): 2026-10-05 + 60 days = 2026-12-04 (Friday). The days from NP-03 [1]; the acknowledgement date from your message. The desk's count: calendar days, the first being the day after the written acknowledgement. A handbook that counts the days otherwise moves the date.
  - Earned leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [6]. Condition: LV-07 bars encashment during probation: this figure holds only once probation is over.

4 model calls (12 at most), 3 searches, 3 calculations, 0 refused or failed tool calls; stopped by nothing
tokens: in 12,350, thinking 256, visible 283; Rs 1.9182 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: plan 1 call, Rs 0.3951 (gemini-3.6-flash); extract 2 calls, Rs 0.5628 (gemini-3.6-flash); solve 1 call, Rs 0.9603 (gemini-3.6-flash)
waves: 3 (#E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

### demo_06_change_it_switch_the_replan_off.py

Do it: no replan Put it back

**`step_01_no_replan(session)` — Change it: switch the replan off / Do it: no replan**

Do it: no replan

Operation: bash — run in the operator shell, in the kit (the Change-it: no replan, then the same turn).

Expected shape, not a promised result:

```text
commands/agent_patterns.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
agent turn: pattern plan_execute, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  plan_execute (lesson 10.2): plan-and-execute: a planner call writes a numbered plan, an executor carries it out a step at a time with the desk's tools through ToolNode, a refused or failed step sends the rest back to the planner once, and a last call writes the answer from the steps' results
  the planner: gemini-3.6-flash (plan, replan and solve); the executor: gemini-3.6-flash (act; EXEC_MODEL= names another)
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I am a confirmed E3 employee at ACME on Rs 52,000 a month with 7 years 8 months of continuous service. My resignation was acknowledged in writing on 5 October 2026. I have 80 days of earned leave, and my manager says the encashment cap is 100 days. When does my notice end, how many leave days are encashed, and roughly what gratuity will I get?

model call 1 (plan, gemini-3.6-flash, thinking low): in 1,643, thinking 64, visible 127 tokens, Rs 0.3312
  the plan:
    1. Search for NP-03: retrieve {"query": "notice period confirmed employee acknowledged in writing"}
    2. Last day of notice: notice_end {"ack_date": "2026-10-05", "days": "<the days NP-03 states>"}
    3. Earned leave encashed on exit: encashable_days {"balance": 80, "cap": 100}
    4. Search for Code on Social Security, 2020, s.53(2): retrieve {"query": "gratuity fifteen days wages for every completed year of service"}
    5. Gratuity, an estimate: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
step 1: Search for NP-03: retrieve {"query": "notice period confirmed employee acknowledged in writing"}
  model call 2 (act, gemini-3.6-flash, thinking low): in 579, thinking 64, visible 20 tokens, Rs 0.1274
  -> retrieve(query="notice period confirmed employee acknowledged in writing")
       5 passages
step 2: Last day of notice: notice_end {"ack_date": "2026-10-05", "days": "<the days NP-03 states>"}
  model call 3 (act, gemini-3.6-flash, thinking low): in 801, thinking 64, visible 12 tokens, Rs 0.1506
  -> notice_end(ack_date="2026-10-05", days=60)
       = 2026-12-04: 2026-10-05 + 60 days = 2026-12-04 (Friday)
step 3: Earned leave encashed on exit: encashable_days {"balance": 80, "cap": 100}
  model call 4 (act, gemini-3.6-flash, thinking low): in 968, thinking 64, visible 11 tokens, Rs 0.1712
  -> encashable_days(balance=80, cap=100)
       refused: cap = 100 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states
  the step was refused
step 4: Search for Code on Social Security, 2020, s.53(2): retrieve {"query": "gratuity fifteen days wages for every completed year of service"}
  model call 5 (act, gemini-3.6-flash, thinking low): in 1,050, thinking 64, visible 21 tokens, Rs 0.1881
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
step 5: Gratuity, an estimate: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
  model call 6 (act, gemini-3.6-flash, thinking low): in 1,232, thinking 64, visible 17 tokens, Rs 0.2087
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 7 (solve, gemini-3.6-flash, thinking low): in 5,433, thinking 64, visible 45 tokens, Rs 0.7622
  -> no tool: the answer, from the steps' results

answer, as the Desk shows it (the model's text, then what code writes):
  Last day of notice: 4 December 2026 [1]. Earned leave encashed on exit: not worked out, as encashable_days refused what it was given [1]. Gratuity, an estimate: Rs 2,40,000 [7].


7 model calls (12 at most), 2 searches, 2 calculations, 1 refused or failed tool call; stopped by nothing
tokens: in 11,706, thinking 448, visible 253; Rs 1.9394 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: plan 1 call, Rs 0.3312 (gemini-3.6-flash); act 5 calls, Rs 0.8460 (gemini-3.6-flash); solve 1 call, Rs 0.7622 (gemini-3.6-flash)
plans: 1 written, 0 replans (at most 0 a turn)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_put_it_back(session)` — Change it: switch the replan off / Put it back**

Put it back

Operation: bash — run in the operator shell, in the kit (put the line back).

Expected shape, not a promised result:

```text
1
```

### demo_07_the_3_chained_rows_offline_and_a_cheaper_executor.py

Do it: check the rows, then run them Do it: a flash-lite executor Each saved run is one JSON line: make agent-turn's record of the turn, with its plan and its roles. The cell prints each run's calls and rupees by role, and what its plan did: a replan and why, or the waves.

**`step_01_check_the_rows_then_run_them(session)` — The 3 chained rows offline, and a cheaper executor / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the three rows recomputed).

Expected shape, not a promised result:

```text
ok    chained-exit-e3: notice_end(ack_date=2026-10-05, days=60) = 2026-12-04 (NP-03); encashable_days(balance=50, cap=45) = 45 days (LV-07); gratuity_estimate(monthly_wage=52000, years=7, months=8) = Rs 2,40,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
ok    chained-exit-saturday: notice_end(ack_date=2026-10-06, days=60) = 2026-12-05 (NP-03); encashable_days(balance=80, cap=45) = 45 days (LV-07); gratuity_estimate(monthly_wage=52000, years=7, months=6) = Rs 2,10,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
ok    chained-exit-stated-cap: notice_end(ack_date=2026-10-05, days=60) = 2026-12-04 (NP-03); encashable_days(balance=80, cap=45) = 45 days (LV-07); the stated cap = 100 is refused by check_args; gratuity_estimate(monthly_wage=52000, years=7, months=8) = Rs 2,40,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
3 rows (0 calc, 0 lookup, 0 trap, 0 refuse, 3 chained): every figure recomputed by shared/desk_calc.py, every clause in the corpus, every question let through by the hard gate
```

**`step_02_check_the_rows_then_run_them(session)` — The 3 chained rows offline, and a cheaper executor / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0: 9 scripted turns, about a minute).

Expected shape, not a promised result:

```text
OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 3 rows, 3 arms, 1 run each, in this process (--inproc)
saved 9 runs to /home/you/plans-offline.jsonl: --replay rescores them at Rs 0
== loop, thinking default (low), desk astar: 3 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  chained-exit-e3              chained     yes        yes   7.0      448     126   3.7366  
  chained-exit-saturday        chained     yes        yes   7.0      448     126   3.7373  
  chained-exit-stated-cap      chained     yes        yes   7.0      448     126   3.7474  
  first runs: correct    3/3 = 100.0% [43.8%, 100.0%]
              provenance 3/3 = 100.0% [43.8%, 100.0%]
              verified   3/3 = 100.0% [43.8%, 100.0%]
  a run: 7.0 model calls, 3.0 searches, thinking 448 and visible 126 tokens, Rs 3.7404 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 21 model calls, Rs 11.2213 for the model and Rs 0.0000 for rag-api
== plan_execute, thinking default (low), desk astar: 3 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  chained-exit-e3              chained     yes        yes   8.0      512     276   2.4439  
  chained-exit-saturday        chained     yes        yes   8.0      512     276   2.4443  
  chained-exit-stated-cap      chained     yes        yes  10.0      640     365   3.0377  
  first runs: correct    3/3 = 100.0% [43.8%, 100.0%]
              provenance 3/3 = 100.0% [43.8%, 100.0%]
              verified   3/3 = 100.0% [43.8%, 100.0%]
  a run: 8.7 model calls, 3.0 searches, thinking 555 and visible 306 tokens, Rs 2.6420 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 26 model calls, Rs 7.9259 for the model and Rs 0.0000 for rag-api
  by role, a run: plan 1.0 calls, Rs 0.3400 (gemini-3.6-flash); act 6.3 calls, Rs 1.2172 (gemini-3.6-flash); replan 0.3 calls, Rs 0.1261 (gemini-3.6-flash); solve 1.0 calls, Rs 0.9586 (gemini-3.6-flash)
  the plans: replanned in 1 of 3 runs
== rewoo, thinking default (low), desk astar: 3 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  chained-exit-e3              chained     yes        yes   4.0      256     283   1.9182  
  chained-exit-saturday        chained     yes        yes   4.0      256     283   1.9184  
  chained-exit-stated-cap      chained      no         no   3.0      192     242   1.4606  no encashable_days call returned it; encashable_days: the figure is not stated
  first runs: correct    2/3 = 66.7% [20.8%, 93.9%]
              provenance 2/3 = 66.7% [20.8%, 93.9%]
              verified   2/3 = 66.7% [20.8%, 93.9%]
  a run: 3.7 model calls, 2.7 searches, thinking 235 and visible 269 tokens, Rs 1.7657 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 11 model calls, Rs 5.2972 for the model and Rs 0.0000 for rag-api
  by role, a run: plan 1.0 calls, Rs 0.3890 (gemini-3.6-flash); extract 1.7 calls, Rs 0.4820 (gemini-3.6-flash); solve 1.0 calls, Rs 0.8948 (gemini-3.6-flash)
  the plans: refused before any tool ran in 0 of 3 runs, 3.0 waves a run
```

**`step_03_a_flash_lite_executor(session)` — The 3 chained rows offline, and a cheaper executor / Do it: a flash-lite executor**

Do it: a flash-lite executor

Operation: bash — run in the operator shell, in the kit (Rs 0: the two planning patterns with a flash-lite executor).

Expected shape, not a promised result:

```text
OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's; an executor on gemini-3.1-flash-lite | 3 rows, 2 arms, 1 run each, in this process (--inproc)
saved 6 runs to /home/you/plans-lite-offline.jsonl: --replay rescores them at Rs 0
== plan_execute, thinking default (low), desk astar, executor gemini-3.1-flash-lite: 3 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  chained-exit-e3              chained     yes        yes   8.0      512     276   1.5005  
  chained-exit-saturday        chained     yes        yes   8.0      512     276   1.5007  
  chained-exit-stated-cap      chained     yes        yes  10.0      640     365   1.9137  
  first runs: correct    3/3 = 100.0% [43.8%, 100.0%]
              provenance 3/3 = 100.0% [43.8%, 100.0%]
              verified   3/3 = 100.0% [43.8%, 100.0%]
  a run: 8.7 model calls, 3.0 searches, thinking 555 and visible 306 tokens, Rs 1.6383 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 26 model calls, Rs 4.9149 for the model and Rs 0.0000 for rag-api
  by role, a run: plan 1.0 calls, Rs 0.3400 (gemini-3.6-flash); act 6.3 calls, Rs 0.2136 (gemini-3.1-flash-lite); replan 0.3 calls, Rs 0.1261 (gemini-3.6-flash); solve 1.0 calls, Rs 0.9586 (gemini-3.6-flash)
  the plans: replanned in 1 of 3 runs
== rewoo, thinking default (low), desk astar, executor gemini-3.1-flash-lite: 3 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  chained-exit-e3              chained     yes        yes   4.0      256     283   1.4530  
  chained-exit-saturday        chained     yes        yes   4.0      256     283   1.4531  
  chained-exit-stated-cap      chained      no         no   3.0      192     242   1.1957  no encashable_days call returned it; encashable_days: the figure is not stated
  first runs: correct    2/3 = 66.7% [20.8%, 93.9%]
              provenance 2/3 = 66.7% [20.8%, 93.9%]
              verified   2/3 = 66.7% [20.8%, 93.9%]
  a run: 3.7 model calls, 2.7 searches, thinking 235 and visible 269 tokens, Rs 1.3673 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 11 model calls, Rs 4.1018 for the model and Rs 0.0000 for rag-api
  by role, a run: plan 1.0 calls, Rs 0.3890 (gemini-3.6-flash); extract 1.7 calls, Rs 0.0835 (gemini-3.1-flash-lite); solve 1.0 calls, Rs 0.8948 (gemini-3.6-flash)
  the plans: refused before any tool ran in 0 of 3 runs, 3.0 waves a run
  paired (correct), 3 rows: both 2, plan_execute only 1, rewoo only 0, neither 0
  rewoo - plan_execute = -33.3 points, 95% [-79.2, +29.1] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
  paired (verified), 3 rows: both 2, plan_execute only 1, rewoo only 0, neither 0
  rewoo - plan_execute = -33.3 points, 95% [-79.2, +29.1] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
```

**`step_04_the_saved_runs_read_back(session)` — The 3 chained rows offline, and a cheaper executor / Do it: the saved runs, read back**

Each saved run is one JSON line: make agent-turn's record of the turn, with its plan and its roles. The cell prints each run's calls and rupees by role, and what its plan did: a replan and why, or the waves.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back).

Expected shape, not a promised result:

```text
~/plans-offline.jsonl: 9 runs
  chained-exit-e3          loop                                 7 calls, Rs 3.74
  chained-exit-saturday    loop                                 7 calls, Rs 3.74
  chained-exit-stated-cap  loop                                 7 calls, Rs 3.75
  chained-exit-e3          plan_execute                         8 calls, Rs 2.44 | plan 1, Rs 0.34; act 6, Rs 1.14; solve 1, Rs 0.96
  chained-exit-saturday    plan_execute                         8 calls, Rs 2.44 | plan 1, Rs 0.34; act 6, Rs 1.14; solve 1, Rs 0.96
  chained-exit-stated-cap  plan_execute                        10 calls, Rs 3.04 | plan 1, Rs 0.33; act 7, Rs 1.36; replan 1, Rs 0.38; solve 1, Rs 0.97
      replanned after: Step 3 was refused: cap = 100 is not written in LV-07 of a handbook passage this turn read: search f
  chained-exit-e3          rewoo                                4 calls, Rs 1.92 | plan 1, Rs 0.40; extract 2, Rs 0.56; solve 1, Rs 0.96
      waves: #E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7
  chained-exit-saturday    rewoo                                4 calls, Rs 1.92 | plan 1, Rs 0.40; extract 2, Rs 0.56; solve 1, Rs 0.96
      waves: #E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7
  chained-exit-stated-cap  rewoo                                3 calls, Rs 1.46 | plan 1, Rs 0.38; extract 1, Rs 0.32; solve 1, Rs 0.76
      waves: #E1, #E2 | #E3, #E5, #E6 | #E4
~/plans-lite-offline.jsonl: 6 runs
  chained-exit-e3          plan_execute on gemini-3.1-flash-lite  8 calls, Rs 1.50 | plan 1, Rs 0.34; act 6, Rs 0.20; solve 1, Rs 0.96
  chained-exit-saturday    plan_execute on gemini-3.1-flash-lite  8 calls, Rs 1.50 | plan 1, Rs 0.34; act 6, Rs 0.20; solve 1, Rs 0.96
  chained-exit-stated-cap  plan_execute on gemini-3.1-flash-lite 10 calls, Rs 1.91 | plan 1, Rs 0.33; act 7, Rs 0.24; replan 1, Rs 0.38; solve 1, Rs 0.97
      replanned after: Step 3 was refused: cap = 100 is not written in LV-07 of a handbook passage this turn read: search f
  chained-exit-e3          rewoo on gemini-3.1-flash-lite       4 calls, Rs 1.45 | plan 1, Rs 0.40; extract 2, Rs 0.10; solve 1, Rs 0.96
      waves: #E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7
  chained-exit-saturday    rewoo on gemini-3.1-flash-lite       4 calls, Rs 1.45 | plan 1, Rs 0.40; extract 2, Rs 0.10; solve 1, Rs 0.96
      waves: #E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7
  chained-exit-stated-cap  rewoo on gemini-3.1-flash-lite       3 calls, Rs 1.20 | plan 1, Rs 0.38; extract 1, Rs 0.06; solve 1, Rs 0.76
      waves: #E1, #E2 | #E3, #E5, #E6 | #E4
```

### demo_08_your_lane_plan_and_execute_rewoo_and_a_flash_lite_executor.py

Do it: plan-and-execute on the manager's cap Do it: ReWOO on a chained row Do it: a flash-lite executor

**`step_01_plan_and_execute_on_the_manager_s_cap(session)` — Your lane: plan-and-execute, ReWOO and a flash-lite executor / Do it: plan-and-execute on the manager's cap**

Do it: plan-and-execute on the manager's cap

Operation: bash — run in the operator shell, in the kit (one live turn, about Rs 3.64 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_plan_execute.txt]
```

**`step_02_rewoo_on_a_chained_row(session)` — Your lane: plan-and-execute, ReWOO and a flash-lite executor / Do it: ReWOO on a chained row**

Do it: ReWOO on a chained row

Operation: bash — run in the operator shell, in the kit (one live turn, about Rs 1.76 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_rewoo.txt]
```

**`step_03_a_flash_lite_executor(session)` — Your lane: plan-and-execute, ReWOO and a flash-lite executor / Do it: a flash-lite executor**

Do it: a flash-lite executor

Operation: bash — run in the operator shell, in the kit (one live turn, about Rs 1.51 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_lite.txt]
```

### demo_09_the_3_rows_on_your_lane_and_the_plans_they_saved.py

The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in. Do it: rescore the saved runs, at Rs 0 The same cell as step 7, on your lane's saved runs.

**`step_01_definition(session)` — The 3 rows on your lane, and the plans they saved / Definition**

The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (9 live turns, about Rs 27.85 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_plans.txt]
```

**`step_02_definition(session)` — The 3 rows on your lane, and the plans they saved / Definition**

The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (6 live turns, about Rs 8.75 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_lite.txt]
```

**`step_03_rescore_the_saved_runs_at_rs_0(session)` — The 3 rows on your lane, and the plans they saved / Do it: rescore the saved runs, at Rs 0**

Do it: rescore the saved runs, at Rs 0

Operation: bash — run in the operator shell, in the kit (Rs 0: the saved runs rescored, no model call).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/replay.txt]
```

**`step_04_read_the_plans_back_at_rs_0(session)` — The 3 rows on your lane, and the plans they saved / Do it: read the plans back, at Rs 0**

The same cell as step 7, on your lane's saved runs.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/plans_read.txt]
```

### demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py

The planner is set on the agent after it is built, so the constructor lessons 5.7 and 6.1 show is unchanged: ADK's flow reads root.planner on every model request, and LlmAgent's pydantic config lets the field be assigned (commands/tests/test_adk_planner.py checks both on the pinned ADK). The other half is the answer, which is the text not marked thought: a plan or a line of reasoning never reaches it, and a reply that was all plan says so instead of answering nothing. Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer.

**`step_01_adk_s_form_on_the_adk_brain_behind_a_switc(session)` — When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet / ADK's form, on the ADK brain behind a switch**

The planner is set on the agent after it is built, so the constructor lessons 5.7 and 6.1 show is unchanged: ADK's flow reads root.planner on every model request, and LlmAgent's pydantic config lets the field be assigned (commands/tests/test_adk_planner.py checks both on the pinned ADK). The other half is the answer, which is the text not marked thought: a plan or a line of reasoning never reaches it, and a reply that was all plan says so instead of answering nothing. Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer.

Operation: bash — run in the operator shell, in the kit (a Python cell in ~/graph-venv; Rs 0: the kit's ADK brain with ADK_PLANNER on, on a scripted model).

Expected shape, not a promised result:

```text
ADK_PLANNER: plan_react | the agent's planner: PlanReActPlanner
call 1 is told to plan: True
  stored, thought=True: '1. Search the handbook for the notice period.\n2. Answer with the figure and its source.'
  stored, a tool call: retrieve({'query': 'notice period confirmed employee'})
  stored, thought=True: 'The handbook says 60 days.'
  stored, thought=None: 'Sixty days of notice [1].'
call 2 is sent the plan back, thought = [None]
the answer: 'Sixty days of notice [1].' | tool calls: ['retrieve'] | citations: 1
a reply that is all plan answers:
The model wrote a plan but no final answer. Its plan:
1. Search the handbook for the notice period.
2. Answer with the figure and its source.
```

### optional/demo_10_when_a_plan_pays_what_each_costs_the_libraries_forms_and_what_the_kit_does_not_d.py

Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer. On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls retrieve as a function when the instruction asks for tool code under /*ACTION*/, and what a written plan adds to a turn's calls and rupees.

**`step_01_adk_s_form_on_the_adk_brain_behind_a_switc(session)` — When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet / ADK's form, on the ADK brain behind a switch**

Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer. On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls retrieve as a function when the instruction asks for tool code under /*ACTION*/, and what a written plan adds to a turn's calls and rupees.

Operation: bash — run in the operator shell, in the kit (optional: a chat redeploy, then two ADK turns, the switch off and on; at most Rs 10).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/adk_planner.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.2_Plan_Execute_WIX.html`. All 64 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b3a4b9903a0ae5b157cb81ed938589e65ff1cfda`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
