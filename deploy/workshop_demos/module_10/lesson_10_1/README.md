# Lesson 10.1: Choose where the agent reasons: observe-think-act and ReAct

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 4 | [demo_04_the_loop_its_recorder_and_the_figure_check_offline.py](demo_04_the_loop_its_recorder_and_the_figure_check_offline.py) | The loop, its recorder and the figure check, offline |
| 5 | [demo_05_prompted_react_parsed_by_code_and_a_plan_first_offline.py](demo_05_prompted_react_parsed_by_code_and_a_plan_first_offline.py) | Prompted ReAct, parsed by code; and a plan first, offline |
| 6 | [demo_06_change_it_delete_the_parser_s_cut.py](demo_06_change_it_delete_the_parser_s_cut.py) | Change it: delete the parser's cut |
| 7 | [demo_07_the_11_calculator_rows_scored_offline_and_paired.py](demo_07_the_11_calculator_rows_scored_offline_and_paired.py) | The 11 calculator rows, scored offline and paired |
| 8 | [demo_08_your_lane_four_thinking_levels_react_a_plan_and_what_a_search_returns.py](demo_08_your_lane_four_thinking_levels_react_a_plan_and_what_a_search_returns.py) | Your lane: four thinking levels, ReAct, a plan, and what a search returns |
| 9 | [demo_09_the_11_rows_on_your_lane_paired_and_the_rows_they_leave.py](demo_09_the_11_rows_on_your_lane_paired_and_the_rows_they_leave.py) | The 11 rows on your lane, paired, and the rows they leave |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lesson 5.4 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class, and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.4 gives each document its class, and this lesson comes first, so run its one line now: it writes acme's and zeta's registries from evals/manifest.json and relabels their stored rows, as lesson 10.4 explains. A second run finds nothing to change. It ends with a relabel_applied line for each company; an exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later. A pin_miss in its plan means the object on your lane is not the version the manifest records, and lesson 10.4 shows how a person re-pins it.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lesson 5.4 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class, and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.4 gives each document its class, and this lesson comes first, so run its one line now: it writes acme's and zeta's registries from evals/manifest.json and relabels their stored rows, as lesson 10.4 explains. A second run finds nothing to change. It ends with a relabel_applied line for each company; an exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later. A pin_miss in its plan means the object on your lane is not the version the manifest records, and lesson 10.4 shows how a person re-pins it.

Operation: bash — run in the operator shell, in the kit (once: acme's and zeta's stored rows get the classes the bench searches).

### demo_04_the_loop_its_recorder_and_the_figure_check_offline.py

With OFFLINE=1, make agent-turn runs the bench on a scripted model and the kit's own corpus: no project, no credential, no network. The question is the gratuity row of the task set. Do it: the same turn at four thinking levels

**`step_01_one_turn(session)` — The loop, its recorder and the figure check, offline / Do it: one turn**

With OFFLINE=1, make agent-turn runs the bench on a scripted model and the kit's own corpus: no project, no credential, no network. The question is the gratuity row of the task set.

Operation: bash — run in the operator shell, in the kit (Rs 0: a scripted model and the kit's corpus; the first run builds ~/graph-venv).

Expected shape, not a promised result:

```text
agent turn: pattern loop, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
         [1] payment_of_gratuity_act_1972.pdf (statute)
         [2] code_on_social_security_2020.pdf (statute)
         [3] code_on_social_security_2020.pdf (statute)
         [4] labour_codes_compliance_handbook.pdf (guidance)
         [5] labour_codes_compliance_handbook.pdf (guidance)
model call 2 (thinking low): in 2,329, thinking 64, visible 17 tokens, Rs 0.3486
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 3 (thinking low): in 2,840, thinking 64, visible 10 tokens, Rs 0.4093
  -> no tool: the answer

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

  Worked out in code:
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.

3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls; stopped by nothing
tokens: in 5,436, thinking 192, visible 48; Rs 0.8461 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_the_same_turn_at_four_thinking_levels(session)` — The loop, its recorder and the figure check, offline / Do it: the same turn at four thinking levels**

Do it: the same turn at four thinking levels

Operation: bash — run in the operator shell, in the kit (Rs 0: the same turn at the four levels, the per-call lines only).

Expected shape, not a promised result:

```text
thinking: minimal, sent with every call
model call 1 (thinking minimal): in 267, thinking 0, visible 21 tokens, Rs 0.0474
model call 2 (thinking minimal): in 2,329, thinking 0, visible 17 tokens, Rs 0.3078
model call 3 (thinking minimal): in 2,840, thinking 0, visible 10 tokens, Rs 0.3685
tokens: in 5,436, thinking 0, visible 48; Rs 0.7237 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
  thinking: low, sent with every call
model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
model call 2 (thinking low): in 2,329, thinking 64, visible 17 tokens, Rs 0.3486
model call 3 (thinking low): in 2,840, thinking 64, visible 10 tokens, Rs 0.4093
tokens: in 5,436, thinking 192, visible 48; Rs 0.8461 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
  thinking: medium, sent with every call
model call 1 (thinking medium): in 267, thinking 256, visible 21 tokens, Rs 0.2106
model call 2 (thinking medium): in 2,329, thinking 256, visible 17 tokens, Rs 0.4710
model call 3 (thinking medium): in 2,840, thinking 256, visible 10 tokens, Rs 0.5317
tokens: in 5,436, thinking 768, visible 48; Rs 1.2133 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
  thinking: high, sent with every call
model call 1 (thinking high): in 267, thinking 1,024, visible 21 tokens, Rs 0.7002
model call 2 (thinking high): in 2,329, thinking 1,024, visible 17 tokens, Rs 0.9606
model call 3 (thinking high): in 2,840, thinking 1,024, visible 10 tokens, Rs 1.0213
tokens: in 5,436, thinking 3,072, visible 48; Rs 2.6821 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

### demo_05_prompted_react_parsed_by_code_and_a_plan_first_offline.py

Do it: prompted ReAct Do it: a plan first

**`step_01_prompted_react(session)` — Prompted ReAct, parsed by code; and a plan first, offline / Do it: prompted ReAct**

Do it: prompted ReAct

Operation: bash — run in the operator shell, in the kit (Rs 0: prompted ReAct on the same question).

Expected shape, not a promised result:

```text
agent turn: pattern react_text, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  react_text (lesson 10.1): prompted ReAct: no function declaration sent, the tools written into the prompt, the model writing Thought and Action as text and stopping at "Observation:", code reading the Action, running it through ToolNode and writing each Observation
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

model call 1 (thinking low): in 1,556, thinking 64, visible 40 tokens, Rs 0.2647
  Thought: I need the passage this rests on, so I search for it.
  Action: retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]
  -> code runs retrieve(query="gratuity fifteen days wages for every completed year of service"); the Observation it writes:
       5 passages
         [1] payment_of_gratuity_act_1972.pdf (statute)
         [2] code_on_social_security_2020.pdf (statute)
         [3] code_on_social_security_2020.pdf (statute)
         [4] labour_codes_compliance_handbook.pdf (guidance)
         [5] labour_codes_compliance_handbook.pdf (guidance)
model call 2 (thinking low): in 3,639, thinking 64, visible 44 tokens, Rs 0.5328
  Thought: gratuity_estimate works the figure out from numbers the question and the passages state.
  Action: gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]
  -> code runs gratuity_estimate(monthly_wage=52000, years=7, months=8); the Observation it writes:
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 3 (thinking low): in 4,182, thinking 64, visible 23 tokens, Rs 0.5887
  Thought: I have what the answer needs.
  Final Answer: Gratuity, an estimate: Rs 2,40,000 [2].
  -> no tool: the Final Answer is the answer

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

  Worked out in code:
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.

3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls, 0 format errors; stopped by nothing
tokens: in 9,377, thinking 192, visible 107; Rs 1.3862 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_a_plan_first(session)` — Prompted ReAct, parsed by code; and a plan first, offline / Do it: a plan first**

Do it: a plan first

Operation: bash — run in the operator shell, in the kit (Rs 0: the plan-first prompt on the same question).

Expected shape, not a promised result:

```text
agent turn: pattern plan_first, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  plan_first (lesson 10.1): the loop, its prompt led by an instruction to write a plan first: nothing runs the plan, and the loop still decides every call
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

model call 1 (thinking low): in 324, thinking 64, visible 68 tokens, Rs 0.1255
  the model wrote: Plan: 1. Search for the passage the figure rests on. 2. Call gratuity_estimate with numbers the question and that passage state. 3. Answer with the figure it returns, citing the passage.
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
         [1] payment_of_gratuity_act_1972.pdf (statute)
         [2] code_on_social_security_2020.pdf (statute)
         [3] code_on_social_security_2020.pdf (statute)
         [4] labour_codes_compliance_handbook.pdf (guidance)
         [5] labour_codes_compliance_handbook.pdf (guidance)
model call 2 (thinking low): in 2,432, thinking 64, visible 17 tokens, Rs 0.3617
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 3 (thinking low): in 2,944, thinking 64, visible 10 tokens, Rs 0.4225
  -> no tool: the answer

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

  Worked out in code:
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.

3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls; stopped by nothing
tokens: in 5,700, thinking 192, visible 95; Rs 0.9097 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

### demo_06_change_it_delete_the_parser_s_cut.py

Do it: first, with the cut Do it: delete the cut, and run it again Put it back

**`step_01_first_with_the_cut(session)` — Change it: delete the parser's cut / Do it: first, with the cut**

Do it: first, with the cut

Operation: bash — run in the operator shell, in the kit (Rs 0: a scripted model whose stop sequence does not hold).

Expected shape, not a promised result:

```text
agent turn: pattern react_text, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  react_text (lesson 10.1): prompted ReAct: no function declaration sent, the tools written into the prompt, the model writing Thought and Action as text and stopping at "Observation:", code reading the Action, running it through ToolNode and writing each Observation
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  --invent: past its calculator's Action the scripted model writes "Observation: Rs 2,50,000" and a Final Answer from it, as a model does whose stop sequence does not hold
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

model call 1 (thinking low): in 1,556, thinking 64, visible 40 tokens, Rs 0.2647
  Thought: I need the passage this rests on, so I search for it.
  Action: retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]
  -> code runs retrieve(query="gratuity fifteen days wages for every completed year of service"); the Observation it writes:
       5 passages
         [1] payment_of_gratuity_act_1972.pdf (statute)
         [2] code_on_social_security_2020.pdf (statute)
         [3] code_on_social_security_2020.pdf (statute)
         [4] labour_codes_compliance_handbook.pdf (guidance)
         [5] labour_codes_compliance_handbook.pdf (guidance)
model call 2 (thinking low): in 3,639, thinking 64, visible 75 tokens, Rs 0.5526
  Thought: gratuity_estimate works the figure out from numbers the question and the passages state.
  Action: gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]
  cut by the parser, which reads nothing from the first "Observation:" on:
    | Observation: Rs 2,50,000
    | Thought: The calculator returned the figure.
    | Final Answer: Gratuity, an estimate: Rs 2,50,000 [2].
  -> code runs gratuity_estimate(monthly_wage=52000, years=7, months=8); the Observation it writes:
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 3 (thinking low): in 4,182, thinking 64, visible 23 tokens, Rs 0.5887
  Thought: I have what the answer needs.
  Final Answer: Gratuity, an estimate: Rs 2,40,000 [2].
  -> no tool: the Final Answer is the answer

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

  Worked out in code:
  - Gratuity, an estimate (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3)): 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. The monthly wage from your message; the years from your message; the months from your message. An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted. No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these documents do not hold.

3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls, 0 format errors; stopped by nothing
tokens: in 9,377, thinking 192, visible 138; Rs 1.4059 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_delete_the_cut_and_run_it_again(session)` — Change it: delete the parser's cut / Do it: delete the cut, and run it again**

Do it: delete the cut, and run it again

Operation: bash — run in the operator shell, in the kit (the Change-it: delete the cut, then the same run).

Expected shape, not a promised result:

```text
commands/agent_patterns.py | 1 -
 1 file changed, 1 deletion(-)
agent turn: pattern react_text, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  react_text (lesson 10.1): prompted ReAct: no function declaration sent, the tools written into the prompt, the model writing Thought and Action as text and stopping at "Observation:", code reading the Action, running it through ToolNode and writing each Observation
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  --invent: past its calculator's Action the scripted model writes "Observation: Rs 2,50,000" and a Final Answer from it, as a model does whose stop sequence does not hold
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

model call 1 (thinking low): in 1,556, thinking 64, visible 40 tokens, Rs 0.2647
  Thought: I need the passage this rests on, so I search for it.
  Action: retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]
  -> code runs retrieve(query="gratuity fifteen days wages for every completed year of service"); the Observation it writes:
       5 passages
         [1] payment_of_gratuity_act_1972.pdf (statute)
         [2] code_on_social_security_2020.pdf (statute)
         [3] code_on_social_security_2020.pdf (statute)
         [4] labour_codes_compliance_handbook.pdf (guidance)
         [5] labour_codes_compliance_handbook.pdf (guidance)
model call 2 (thinking low): in 3,639, thinking 64, visible 75 tokens, Rs 0.5526
  Thought: gratuity_estimate works the figure out from numbers the question and the passages state.
  Action: gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]
  Observation: Rs 2,50,000
  Thought: The calculator returned the figure.
  Final Answer: Gratuity, an estimate: Rs 2,50,000 [2].
  -> no tool: the Final Answer is the answer

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,50,000 [2].

2 model calls (12 at most), 1 search, 0 calculations, 0 refused or failed tool calls, 0 format errors; stopped by nothing
tokens: in 5,195, thinking 128, visible 115; Rs 0.8173 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
figure check: no calculator, question or passage wrote 2,50,000 (desk_calc.unsupported)
```

**`step_03_put_it_back(session)` — Change it: delete the parser's cut / Put it back**

Put it back

Operation: bash — run in the operator shell, in the kit (put the line back).

Expected shape, not a promised result:

```text
1
```

### demo_07_the_11_calculator_rows_scored_offline_and_paired.py

Do it: check the rows, then run them One cell splits the saved runs by pattern and prints what a call of each pattern read, thought and wrote; for react_text, it also counts the replies that ran past the stop and the Actions code could not read, with the bench's own parser. Then COMPARE= pairs each pattern with the loop, row by row.

**`step_01_check_the_rows_then_run_them(session)` — The 11 calculator rows, scored offline and paired / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the slice recomputed).

Expected shape, not a promised result:

```text
ok    calc-gratuity-7y8m: gratuity_estimate(monthly_wage=52000, years=7, months=8) = Rs 2,40,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
ok    calc-gratuity-7y6m: gratuity_estimate(monthly_wage=52000, years=7, months=6) = Rs 2,10,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
ok    calc-gratuity-fixed-term: gratuity_estimate(monthly_wage=30000, years=1, months=5, fixed_term=True, term_expired=True) = Rs 24,519 (Code on Social Security, 2020, s.53(2), s.53 Explanation 3, s.53(2) third proviso, s.53(1) second proviso, s.53(3))
ok    calc-carry-forward: carry_forward(days=34, cap=30) = 30 days (LV-01)
ok    calc-carry-forward-zeta: carry_forward(days=25, cap=18) = 18 days (LV-01)
ok    calc-encash-invented-cap: encashable_days(balance=80, cap=45) = 45 days (LV-07)
ok    calc-accrued: accrued_leave(months=8, per_month=1.75) = 14 days (LV-01)
ok    calc-notice-e3: notice_end(ack_date=2026-10-05, days=60) = 2026-12-04 (NP-03)
ok    calc-notice-probation: notice_end(ack_date=2026-10-05, days=15) = 2026-10-20 (PB-02, NP-03)
ok    calc-wages-due: statutory_deadline(event=resignation, last_working_day=2026-10-02) = 2026-10-06 (Code on Wages, 2019, s.17(2), s.17(3))
ok    calc-grc-threshold: threshold_check(headcount=23) = yes (Industrial Relations Code, 2020, s.4(1), s.2(zr))
11 rows (11 calc, 0 lookup, 0 trap, 0 refuse, 0 chained): every figure recomputed by shared/desk_calc.py, every clause in the corpus, every question let through by the hard gate
```

**`step_02_check_the_rows_then_run_them(session)` — The 11 calculator rows, scored offline and paired / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0: 33 scripted turns, a few minutes).

Expected shape, not a promised result:

```text
OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 11 rows, 3 arms, 1 run each, in this process (--inproc)
saved 33 runs to /home/you/bench-101-offline.jsonl: --replay rescores them at Rs 0
== loop, thinking default (low), desk astar: 11 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  calc-gratuity-7y8m           calc        yes         no   2.0      128      31   0.4324  no gratuity_estimate call returned it; unsupported: 2,40,000
  calc-gratuity-7y6m           calc        yes        yes   3.0      192      48   0.8499  
  calc-gratuity-fixed-term     calc        yes        yes   3.0      192      54   0.8982  
  calc-carry-forward           calc        yes        yes   3.0      192      37   0.7989  
  calc-carry-forward-zeta      calc        yes        yes   3.0      192      37   0.7806  
  calc-encash-invented-cap     calc        yes        yes   3.0      192      35   0.6446  
  calc-accrued                 calc        yes        yes   3.0      192      37   0.5672  
  calc-notice-e3               calc        yes        yes   3.0      192      42   0.8072  
  calc-notice-probation        calc        yes        yes   3.0      192      35   0.6811  
  calc-wages-due               calc        yes        yes   3.0      192      46   0.8308  
  calc-grc-threshold           calc        yes         no   2.0      128      45   0.4614  no threshold_check call returned it
  first runs: correct    11/11 = 100.0% [74.1%, 100.0%]
              provenance 9/11 = 81.8% [52.3%, 94.9%]
              verified   9/11 = 81.8% [52.3%, 94.9%]
  a run: 2.8 model calls, 1.0 searches, thinking 180 and visible 41 tokens, Rs 0.7048 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 31 model calls, Rs 7.7524 for the model and Rs 0.0000 for rag-api
== react_text, thinking default (low), desk astar: 11 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  calc-gratuity-7y8m           calc        yes         no   2.0      128      63   0.7841  no gratuity_estimate call returned it; unsupported: 2,40,000
  calc-gratuity-7y6m           calc        yes        yes   3.0      192     107   1.3900  
  calc-gratuity-fixed-term     calc        yes        yes   3.0      192     112   1.4376  
  calc-carry-forward           calc        yes        yes   3.0      192      95   1.3382  
  calc-carry-forward-zeta      calc        yes        yes   3.0      192      95   1.3199  
  calc-encash-invented-cap     calc        yes        yes   3.0      192      92   1.1835  
  calc-accrued                 calc        yes        yes   3.0      192      94   1.1059  
  calc-notice-e3               calc        yes        yes   3.0      192     100   1.3465  
  calc-notice-probation        calc        yes        yes   3.0      192      93   1.2203  
  calc-wages-due               calc        yes        yes   3.0      192     105   1.3708  
  calc-grc-threshold           calc        yes         no   2.0      128      77   0.8132  no threshold_check call returned it
  first runs: correct    11/11 = 100.0% [74.1%, 100.0%]
              provenance 9/11 = 81.8% [52.3%, 94.9%]
              verified   9/11 = 81.8% [52.3%, 94.9%]
  a run: 2.8 model calls, 1.0 searches, thinking 180 and visible 94 tokens, Rs 1.2100 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 31 model calls, Rs 13.3100 for the model and Rs 0.0000 for rag-api
== plan_first, thinking default (low), desk astar: 11 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  calc-gratuity-7y8m           calc        yes         no   2.0      128      78   0.4827  no gratuity_estimate call returned it; unsupported: 2,40,000
  calc-gratuity-7y6m           calc        yes        yes   3.0      192      95   0.9135  
  calc-gratuity-fixed-term     calc        yes        yes   3.0      192     100   0.9611  
  calc-carry-forward           calc        yes        yes   3.0      192      83   0.8616  
  calc-carry-forward-zeta      calc        yes        yes   3.0      192      83   0.8432  
  calc-encash-invented-cap     calc        yes        yes   3.0      192      81   0.7075  
  calc-accrued                 calc        yes        yes   3.0      192      82   0.6292  
  calc-notice-e3               calc        yes        yes   3.0      192      86   0.8684  
  calc-notice-probation        calc        yes        yes   3.0      192      80   0.7428  
  calc-wages-due               calc        yes        yes   3.0      192      93   0.8943  
  calc-grc-threshold           calc        yes         no   2.0      128      91   0.5110  no threshold_check call returned it
  first runs: correct    11/11 = 100.0% [74.1%, 100.0%]
              provenance 9/11 = 81.8% [52.3%, 94.9%]
              verified   9/11 = 81.8% [52.3%, 94.9%]
  a run: 2.8 model calls, 1.0 searches, thinking 180 and visible 87 tokens, Rs 0.7650 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 31 model calls, Rs 8.4154 for the model and Rs 0.0000 for rag-api
```

**`step_03_the_paired_difference_at_rs_0(session)` — The 11 calculator rows, scored offline and paired / Do it: the paired difference, at Rs 0**

One cell splits the saved runs by pattern and prints what a call of each pattern read, thought and wrote; for react_text, it also counts the replies that ran past the stop and the Actions code could not read, with the bench's own parser. Then COMPARE= pairs each pattern with the loop, row by row.

Operation: bash — run in the operator shell, in the kit (Rs 0: the saved runs split by pattern, then paired).

Expected shape, not a promised result:

```text
33 runs in ~/bench-101-offline.jsonl
loop       11 runs, 31 calls; a call reads 1,569, thinks 64, writes 14; Rs 7.75 in all
react_text 11 runs, 31 calls; a call reads 2,881, thinks 64, writes 33; Rs 13.31 in all; 0 replies ran past the stop, 0 format errors
plan_first 11 runs, 31 calls; a call reads 1,656, thinks 64, writes 31; Rs 8.42 in all
== /home/you/bench-101-offline-react_text.jsonl (react_text, thinking default (low), desk astar) against /home/you/bench-101-offline-loop.jsonl (loop, thinking default (low), desk astar), each row's first run, Rs 0
  paired (correct), 11 rows: both 11, loop only 0, react_text only 0, neither 0
  react_text - loop = +0.0 points, 95% [-25.9, +25.9] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
  paired (verified), 11 rows: both 9, loop only 0, react_text only 0, neither 2
  react_text - loop = +0.0 points, 95% [-16.5, +16.5] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
== /home/you/bench-101-offline-plan_first.jsonl (plan_first, thinking default (low), desk astar) against /home/you/bench-101-offline-loop.jsonl (loop, thinking default (low), desk astar), each row's first run, Rs 0
  paired (correct), 11 rows: both 11, loop only 0, plan_first only 0, neither 0
  plan_first - loop = +0.0 points, 95% [-25.9, +25.9] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
  paired (verified), 11 rows: both 9, loop only 0, plan_first only 0, neither 2
  plan_first - loop = +0.0 points, 95% [-16.5, +16.5] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
```

### demo_08_your_lane_four_thinking_levels_react_a_plan_and_what_a_search_returns.py

The loop, on the gratuity question, once at each level. The filter keeps the level line, the three call lines, the totals and the figure check of each turn. Do it: prompted ReAct Do it: a plan first Every pattern's retrieve is one POST to rag-api's /v1/passages: the same door, roster and filters as /v1/query, then the reranked passages with their full text, and no model. The cell sends the search the bench's script makes for this question, as the bench sends it: tenant acme, the three classes, the top 5, labelled brain desk.

**`step_01_native_thinking_at_four_levels(session)` — Your lane: four thinking levels, ReAct, a plan, and what a search returns / Do it: native thinking, at four levels**

The loop, on the gratuity question, once at each level. The filter keeps the level line, the three call lines, the totals and the figure check of each turn.

Operation: bash — run in the operator shell, in the kit (four live turns of the loop, about Rs 4.63 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_levels.txt]
```

**`step_02_prompted_react(session)` — Your lane: four thinking levels, ReAct, a plan, and what a search returns / Do it: prompted ReAct**

Do it: prompted ReAct

Operation: bash — run in the operator shell, in the kit (one live turn, about Rs 1.26 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_react.txt]
```

**`step_03_a_plan_first(session)` — Your lane: four thinking levels, ReAct, a plan, and what a search returns / Do it: a plan first**

Do it: a plan first

Operation: bash — run in the operator shell, in the kit (one live turn, about Rs 1.22 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_plan.txt]
```

**`step_04_what_a_search_returns(session)` — Your lane: four thinking levels, ReAct, a plan, and what a search returns / Do it: what a search returns**

Every pattern's retrieve is one POST to rag-api's /v1/passages: the same door, roster and filters as /v1/query, then the reranked passages with their full text, and no model. The cell sends the search the bench's script makes for this question, as the bench sends it: tenant acme, the three classes, the top 5, labelled brain desk.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: /v1/passages calls no model).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/passages.txt]
```

### demo_09_the_11_rows_on_your_lane_paired_and_the_rows_they_leave.py

The same command as step 7 without OFFLINE=1: every calculator row through every pattern once, at the Desk agent's own thinking level, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes; the report comes when all 33 have run. The same cell as step 7, on your lane's saved runs. Do it: rag-api's rows for those searches

**`step_01_definition(session)` — The 11 rows on your lane, paired, and the rows they leave / Definition**

The same command as step 7 without OFFLINE=1: every calculator row through every pattern once, at the Desk agent's own thinking level, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes; the report comes when all 33 have run.

Operation: bash — run in the operator shell, in the kit (33 live turns, about Rs 37.79 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_patterns.txt]
```

**`step_02_the_paired_difference_and_each_pattern_s_c(session)` — The 11 rows on your lane, paired, and the rows they leave / Do it: the paired difference and each pattern's calls, at Rs 0**

The same cell as step 7, on your lane's saved runs.

Operation: bash — run in the operator shell, in the kit (Rs 0: your lane's saved runs split by pattern, then paired).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_paired.txt]
```

**`step_03_rag_api_s_rows_for_those_searches(session)` — The 11 rows on your lane, paired, and the rows they leave / Do it: rag-api's rows for those searches**

Do it: rag-api's rows for those searches

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: one Cloud Logging read).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/passages_rows.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.1_ReAct_WIX.html`. All 52 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `222da83d6de50d7502063423e3eae648e7011723`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
