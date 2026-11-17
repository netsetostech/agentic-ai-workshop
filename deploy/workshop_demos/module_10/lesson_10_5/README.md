# Lesson 10.5: Run a desk as an agent with checked calculator arguments

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_desk_page_a_figure_worked_out_in_code_and_a_cap_nobody_wrote.py](demo_03_the_desk_page_a_figure_worked_out_in_code_and_a_cap_nobody_wrote.py) | The Desk page: a figure worked out in code, and a cap nobody wrote |
| 4 | [demo_04_the_agent_its_calculators_and_check_args_in_the_code.py](demo_04_the_agent_its_calculators_and_check_args_in_the_code.py) | The agent, its calculators and check_args, in the code |
| 5 | [demo_05_change_it_delete_the_prompt_s_rule.py](demo_05_change_it_delete_the_prompt_s_rule.py) | Change it: delete the prompt's rule |
| 6 | [demo_06_one_question_two_arms_over_rest.py](demo_06_one_question_two_arms_over_rest.py) | One question, two arms, over REST |
| 7 | [demo_07_the_rows_and_the_checkpoint.py](demo_07_the_rows_and_the_checkpoint.py) | The rows and the checkpoint |
| 8 | [demo_08_three_arms_on_the_same_twelve_rows_compared_and_combined.py](demo_08_three_arms_on_the_same_twelve_rows_compared_and_combined.py) | Three arms on the same twelve rows, compared and combined |
| 10 | [demo_10_verify_it_yourself.py](demo_10_verify_it_yourself.py) | Verify it yourself |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_desk_page_a_figure_worked_out_in_code_and_a_cap_nobody_wrote.py

make desk with NOTES= writes tenant_settings/acme.clause_notes from evals/desk/clause_notes.acme.json: a note on LV-01 and LV-07. Each note says what the OSH Code's text says about that leave, and leaves it to the People team whether it covers the person's role. The handbook desk adds a clause's note under an answer that cites the clause, in agent mode as in a direct answer. The command prints one line: acme's switches as they stand, "clause_notes": ["LV-01", "LV-07"], and that rag-api and the chat service read the change within 60 seconds. The cell also notes the time in SINCE105, from which step 7 reads the Desk's rows, and prints the Desk page's address.

**`step_01_acme_s_notes_on_two_clauses(session)` — The Desk page: a figure worked out in code, and a cap nobody wrote / Do it: acme's notes on two clauses**

make desk with NOTES= writes tenant_settings/acme.clause_notes from evals/desk/clause_notes.acme.json: a note on LV-01 and LV-07. Each note says what the OSH Code's text says about that leave, and leaves it to the People team whether it covers the person's role. The handbook desk adds a clause's note under an answer that cites the clause, in agent mode as in a direct answer. The command prints one line: acme's switches as they stand, "clause_notes": ["LV-01", "LV-07"], and that rag-api and the chat service read the change within 60 seconds. The cell also notes the time in SINCE105, from which step 7 reads the Desk's rows, and prints the Desk page's address.

Operation: bash — acme's clause notes, and the time this lesson starts.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/desk_page.txt]
```

### demo_04_the_agent_its_calculators_and_check_args_in_the_code.py

Three of commands/tests/test_desk.py's agent tests. In the first, the agent passes a cap of 40, which neither LV-07 nor the message writes: refused, no calculation, no "Worked out in code". The second sends a gratuity question to the statute desk with the Code on Wages, not the Code on Social Security, among the passages, and has the agent ask for encashable_days, which the statute desk does not hold: two refusals, one by the Code check and one as an unknown tool. In the third the model raises a 429, and the section is the direct answer under the same Meter. A scripted model plays the agent and a table plays rag-api, so no model is called. commands/agent-turn.sh, given arguments, runs them in ~/graph-venv, which it makes with the chat image's pins if it is missing; with OFFLINE=1 it needs no project. The same check, on what your lane's rag-api returns. The cell asks POST /v1/passages, as documind-ui-sa, the account on every company's roster, for acme's handbook passages on "earned leave encashed on exit": the retrieval the agent's search makes, with no model call. Then it runs check_args() on jn-03's question twice, with a cap of 60 and then 45. 60 is NP-03's notice days: when NP-03 is among the passages, 60 is a number the turn has read, but it is not in LV-07's words, so the check refuses it with "refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". 45 is accepted, found in LV-07 at its passage's place in the list.

**`step_01_three_tests_offline(session)` — The agent, its calculators and check_args, in the code / Do it: three tests, offline**

Three of commands/tests/test_desk.py's agent tests. In the first, the agent passes a cap of 40, which neither LV-07 nor the message writes: refused, no calculation, no "Worked out in code". The second sends a gratuity question to the statute desk with the Code on Wages, not the Code on Social Security, among the passages, and has the agent ask for encashable_days, which the statute desk does not hold: two refusals, one by the Code check and one as an unknown tool. In the third the model raises a 429, and the section is the direct answer under the same Meter. A scripted model plays the agent and a table plays rag-api, so no model is called. commands/agent-turn.sh, given arguments, runs them in ~/graph-venv, which it makes with the chat image's pins if it is missing; with OFFLINE=1 it needs no project.

Operation: bash — three agent tests, offline.

Expected shape, not a promised result:

```text
test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk (commands.tests.test_desk.GraphTests.test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk) ... ok
test_a_model_error_is_the_direct_answer_under_the_same_limits (commands.tests.test_desk.GraphTests.test_a_model_error_is_the_direct_answer_under_the_same_limits) ... ok
test_a_number_in_neither_the_passages_nor_the_message_is_refused (commands.tests.test_desk.GraphTests.test_a_number_in_neither_the_passages_nor_the_message_is_refused) ... ok

----------------------------------------------------------------------
Ran 3 tests in N.NNNs

OK
```

**`step_02_the_check_on_your_lane_s_own_passages(session)` — The agent, its calculators and check_args, in the code / Do it: the check on your lane's own passages**

The same check, on what your lane's rag-api returns. The cell asks POST /v1/passages, as documind-ui-sa, the account on every company's roster, for acme's handbook passages on "earned leave encashed on exit": the retrieval the agent's search makes, with no model call. Then it runs check_args() on jn-03's question twice, with a cap of 60 and then 45. 60 is NP-03's notice days: when NP-03 is among the passages, 60 is a number the turn has read, but it is not in LV-07's words, so the check refuses it with "refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". 45 is accepted, found in LV-07 at its passage's place in the list.

Operation: bash — your lane's passages for LV-07, then check_args with cap 60, then 45 (Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/passages_check.txt]
```

### demo_05_change_it_delete_the_prompt_s_rule.py

The rule is advice to the model; the check is code. Delete the rule, run the tests and two turns on your lane, then put it back. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. What to read. Each encashable_days call's arguments, and what came back. Without the rule a model may try a number of its own more often: a balance for the second question, which gives none, or a cap from the wrong clause. Every such call comes back refused, in the check's words; for a balance nobody wrote: "refused: balance = 50 is a fact about the person that their message does not state: ask them for it". The model then asks for the missing number or answers without a calculation, and the figure check at the end says whether any figure in its words has no source. Whether this model tries a wrong number at all on the day you run it is the model's own behaviour; what the run shows is that none gets past the check. The rule makes a refused call less likely, which saves a model call. It was never what made the figure right.

**`step_01_change_it_delete_the_prompt_s_rule(session)` — Change it: delete the prompt's rule / Change it: delete the prompt's rule**

The rule is advice to the model; the check is code. Delete the rule, run the tests and two turns on your lane, then put it back. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service.

Operation: bash — the Change-it: delete the prompt's rule, in your checkout only.

Expected shape, not a promised result:

```text
before:
  "- Work every figure out with a calculator, never yourself. Give a calculator only numbers and dates "
  "written in the person's question or in a passage, as they are written there: it refuses any other. When "
  "a number you need is in neither, say which one is missing.\n"
after:
  "- Work every figure out with a calculator, never yourself.\n"
 M services/chat/desk_agent.py
```

**`step_02_change_it_delete_the_prompt_s_rule(session)` — Change it: delete the prompt's rule / Change it: delete the prompt's rule**

One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt.

Operation: bash — the same three tests, with the rule gone.

Expected shape, not a promised result:

```text
test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk (commands.tests.test_desk.GraphTests.test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk) ... ok
test_a_model_error_is_the_direct_answer_under_the_same_limits (commands.tests.test_desk.GraphTests.test_a_model_error_is_the_direct_answer_under_the_same_limits) ... ok
test_a_number_in_neither_the_passages_nor_the_message_is_refused (commands.tests.test_desk.GraphTests.test_a_number_in_neither_the_passages_nor_the_message_is_refused) ... ok

----------------------------------------------------------------------
Ran 3 tests in N.NNNs

OK
```

**`step_03_change_it_delete_the_prompt_s_rule(session)` — Change it: delete the prompt's rule / Change it: delete the prompt's rule**

Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn.

Operation: bash — two agent turns on your lane, with the rule gone.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_changeit.txt]
```

**`step_04_change_it_delete_the_prompt_s_rule(session)` — Change it: delete the prompt's rule / Change it: delete the prompt's rule**

On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. What to read. Each encashable_days call's arguments, and what came back. Without the rule a model may try a number of its own more often: a balance for the second question, which gives none, or a cap from the wrong clause. Every such call comes back refused, in the check's words; for a balance nobody wrote: "refused: balance = 50 is a fact about the person that their message does not state: ask them for it". The model then asks for the missing number or answers without a calculation, and the figure check at the end says whether any figure in its words has no source. Whether this model tries a wrong number at all on the day you run it is the model's own behaviour; what the run shows is that none gets past the check. The rule makes a refused call less likely, which saves a model call. It was never what made the figure right.

Operation: bash — put the rule back.

Expected shape, not a promised result:

```text
(no output)
```

### demo_06_one_question_two_arms_over_rest.py

jn-03 to POST /v1/desk as evalacme: the routed Desk, then one agent with every tool. An eval account may send arm in the body of POST /v1/desk; from anyone else the field is a 403, "arm is for the Desk's eval accounts (desk_eval)". Arm B is the Desk everyone gets. Arm Astar skips the classifier: the router takes the fallback decision, marked arm Astar, and the desk graph answers it with one agent whose retrieve may search any class the person reads, with all seven calculators. The cell sends jn-03 on each arm, in a session of its own, and prints what the arms differ in: each section's desk and mode, its tool calls and refused calls, each calculation with its arguments and where they were found, and the turn's model calls and limits.cost_inr.

**`step_01_one_question_two_arms_over_rest(session)` — One question, two arms, over REST / One question, two arms, over REST**

jn-03 to POST /v1/desk as evalacme: the routed Desk, then one agent with every tool. An eval account may send arm in the body of POST /v1/desk; from anyone else the field is a 403, "arm is for the Desk's eval accounts (desk_eval)". Arm B is the Desk everyone gets. Arm Astar skips the classifier: the router takes the fallback decision, marked arm Astar, and the desk graph answers it with one agent whose retrieve may search any class the person reads, with all seven calculators. The cell sends jn-03 on each arm, in a session of its own, and prints what the arms differ in: each section's desk and mode, its tool calls and refused calls, each calculation with its arguments and where they were found, and the turn's model calls and limits.cost_inr.

Operation: bash — jn-03 to POST /v1/desk as evalacme, on arm B, then arm Astar.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_arms.txt]
```

### demo_07_the_rows_and_the_checkpoint.py

Every POST /v1/desk turn logs one desk row from the chat service. It names every field it carries, and never the question. Two of its fields are easy to misread. mode is the company's: desk_route as the chat service read it, on for acme, not the section's agent or direct; a row shows agent mode by its tool_calls and refusals. arm is B unless an eval account sent another. The cell reads the rows since SINCE105: your two Desk page turns and evalacme's two. Run it in the shell where step 3 set SINCE105 and step 6 defined sa, a minute after step 6, so that Cloud Logging has the rows. Then make thread, lesson 6.8's reader of the chat service's Cloud SQL checkpoints, lists evalacme's threads, the latest first.

**`step_01_the_rows_and_the_checkpoint(session)` — The rows and the checkpoint / The rows and the checkpoint**

Every POST /v1/desk turn logs one desk row from the chat service. It names every field it carries, and never the question. Two of its fields are easy to misread. mode is the company's: desk_route as the chat service read it, on for acme, not the section's agent or direct; a row shows agent mode by its tool_calls and refusals. arm is B unless an eval account sent another. The cell reads the rows since SINCE105: your two Desk page turns and evalacme's two. Run it in the shell where step 3 set SINCE105 and step 6 defined sa, a minute after step 6, so that Cloud Logging has the rows. Then make thread, lesson 6.8's reader of the chat service's Cloud SQL checkpoints, lists evalacme's threads, the latest first.

Operation: bash — the Desk's rows since step 3, then evalacme's threads.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/desk_rows.txt]
```

### demo_08_three_arms_on_the_same_twelve_rows_compared_and_combined.py

Each row goes to POST /v1/route and to POST /v1/desk as its company's eval account, in a fresh session. On arm B the dev gates apply, as in lesson 10.4: 95% route accuracy and 90% recall for each desk. On 12 rows that means all 12 routed right: 8 of 8 handbook rows and 4 of 4 statute rows. One wrong route prints a FAIL line and make ends with Error 1, and the saved run and the report are written all the same. About Rs 13 to 17. Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm Astar: one agent on every row, lookups included, over every class the person may read, with all seven calculators. The most model calls of the three: about Rs 17 to 24. --compare reads two or three reports of one split, one arm each, on the same rows, and refuses anything else: two reports of one arm, no report of arm B, two splits, or rows that differ. For each arm it prints the correct and authority rates with their Wilson intervals, the desk turns' rupees and model calls, p50 and p95 latency, and the turns in agent mode with their calculator results and refused calls. Then it pairs B against each other arm row by row, through evals/paired.py: Newcombe's interval for the difference, the exact McNemar p, and a verdict read against the margin written there before any run, 3 points, on 8 October 2026. evals/combine.py reads the saved runs as the members of an ensemble, at Rs 0. For each answer row it prints which members were right, by the route eval's own verdict. On a row where any member ran a calculator, the members vote: each proposes the (calculator, value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members made than any other wins. The answer of the first member that made it ships as it stands. A member with no calculation proposes nothing, and a tie abstains: the row goes to a person, since a regulated figure is not settled by a coin. Then come each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the rows it voted on, and the figure check, desk_calc.unsupported(), on every member's answer. Do it: the combiners on scripted members, offline. --selftest runs on scripted members of fig-01, with no model call. Two members' calculators returned Rs 2,40,000; a third writes Rs 2,10,000 itself. With --layers 2 it adds an arbiter, which picks one member's answer from an enum of their names and ships it word for word, and two layers of a mixture-of-agents aggregator, each reading every answer of the layer before and writing a new one. The vote and the arbiter only choose among the members' answers, so neither writes a figure of its own. The aggregator writes new text: this one averages the figures it reads and writes "About Rs 2,25,000", a figure no member computed, and unsupported() flags it at every layer. That is the mixture-of-agents pattern's cost on a regulated figure: every layer is a model writing again, so its figures need the same check as an agent's, while the vote needs no model call at all. --layers goes up to 5. On a lane the arbiter and the aggregator would be model calls of their own; the kit runs them scripted only. Do it: the three saved runs, combined.

**`step_01_arm_b_the_routed_desk(session)` — Three arms on the same twelve rows, compared and combined / Do it: arm B, the routed Desk**

Each row goes to POST /v1/route and to POST /v1/desk as its company's eval account, in a fresh session. On arm B the dev gates apply, as in lesson 10.4: 95% route accuracy and 90% recall for each desk. On 12 rows that means all 12 routed right: 8 of 8 handbook rows and 4 of 4 statute rows. One wrong route prints a FAIL line and make ends with Error 1, and the saved run and the report are written all the same. About Rs 13 to 17.

Operation: bash — arm B, the routed Desk, on the twelve rows.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/arms_B.txt]
```

**`step_02_arm_c_and_arm_astar_on_the_same_rows(session)` — Three arms on the same twelve rows, compared and combined / Do it: arm C and arm Astar, on the same rows**

Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5.

Operation: bash — arm C, code only, on the same rows.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/arms_C.txt]
```

**`step_03_arm_c_and_arm_astar_on_the_same_rows(session)` — Three arms on the same twelve rows, compared and combined / Do it: arm C and arm Astar, on the same rows**

Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm Astar: one agent on every row, lookups included, over every class the person may read, with all seven calculators. The most model calls of the three: about Rs 17 to 24.

Operation: bash — arm Astar, one agent, on the same rows.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/arms_Astar.txt]
```

**`step_04_the_arms_side_by_side(session)` — Three arms on the same twelve rows, compared and combined / The arms side by side**

--compare reads two or three reports of one split, one arm each, on the same rows, and refuses anything else: two reports of one arm, no report of arm B, two splits, or rows that differ. For each arm it prints the correct and authority rates with their Wilson intervals, the desk turns' rupees and model calls, p50 and p95 latency, and the turns in agent mode with their calculator results and refused calls. Then it pairs B against each other arm row by row, through evals/paired.py: Newcombe's interval for the difference, the exact McNemar p, and a verdict read against the margin written there before any run, 3 points, on 8 October 2026.

Operation: bash — the three reports side by side (Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/arms_compare.txt]
```

**`step_05_the_arms_as_an_ensemble(session)` — Three arms on the same twelve rows, compared and combined / The arms as an ensemble**

evals/combine.py reads the saved runs as the members of an ensemble, at Rs 0. For each answer row it prints which members were right, by the route eval's own verdict. On a row where any member ran a calculator, the members vote: each proposes the (calculator, value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members made than any other wins. The answer of the first member that made it ships as it stands. A member with no calculation proposes nothing, and a tie abstains: the row goes to a person, since a regulated figure is not settled by a coin. Then come each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the rows it voted on, and the figure check, desk_calc.unsupported(), on every member's answer. Do it: the combiners on scripted members, offline. --selftest runs on scripted members of fig-01, with no model call. Two members' calculators returned Rs 2,40,000; a third writes Rs 2,10,000 itself. With --layers 2 it adds an arbiter, which picks one member's answer from an enum of their names and ships it word for word, and two layers of a mixture-of-agents aggregator, each reading every answer of the layer before and writing a new one.

Operation: bash — the combiners on scripted members (Rs 0).

Expected shape, not a promised result:

```text
combine.py --selftest: the combiners on scripted members of fig-01, no model call (Rs 0)
  question   I earn Rs 52,000 a month and leave after 7 years 8 months of continuous service. What gratuity is due to me under the Code on Social Security, 2020?
  right      must_contain 2,40,000
  P1         gratuity_estimate = 240000 by code; right; unsupported: none
  P2         gratuity_estimate = 240000 by code; right; unsupported: none
  P3         no calculation, it writes "About Rs 2,10,000 [1]: fifteen days' wages for each of the 7 completed years."; wrong; unsupported: 2,10,000
  vote       gratuity_estimate = 240000 from 2 of 3 members: P1's answer ships as it stands; right; 0 model calls
  split      three other members, a different figure by code each:
             S1 gratuity_estimate = 240000 (monthly_wage=52000, years=7, months=8)
             S2 gratuity_estimate = 210000 (monthly_wage=52000, years=7, months=6)
             S3 gratuity_estimate = 230769 (monthly_wage=50000, years=7, months=8)
             a tie, 3 proposals made by 1 member each: the row goes to a person; 0 model calls
  arbiter    an enum of P1, P2, P3; its scripted pick, P2: that answer ships word for word; right; no figure of its own; 1 model call
  layer 1    the aggregator reads 3 answers and writes "About Rs 2,25,000 [1], between the figures the answers give."; unsupported: 2,25,000; 1 model call
  layer 2    the aggregator reads 1 answer and writes "About Rs 2,25,000 [1], between the figures the answers give."; unsupported: 2,25,000; 1 model call
  calls      the vote 0, the arbiter 1, the aggregator 2 (one a layer)
ok    the vote ships a member's figure, from two members of three, and adds no model call
ok    a three-way split abstains to a person
ok    the arbiter ships one member's answer word for word
ok    the aggregator writes Rs 2,25,000 at each of its 2 layers, which no member computed, and unsupported() flags it
ok    P3's figure, which no calculation returned, is flagged; P1's and P2's are not
the vote and the arbiter wrote no figure of their own; the aggregator wrote one no member computed, flagged at every layer
```

**`step_06_the_arms_as_an_ensemble(session)` — Three arms on the same twelve rows, compared and combined / The arms as an ensemble**

The vote and the arbiter only choose among the members' answers, so neither writes a figure of its own. The aggregator writes new text: this one averages the figures it reads and writes "About Rs 2,25,000", a figure no member computed, and unsupported() flags it at every layer. That is the mixture-of-agents pattern's cost on a regulated figure: every layer is a model writing again, so its figures need the same check as an agent's, while the vote needs no model call at all. --layers goes up to 5. On a lane the arbiter and the aggregator would be model calls of their own; the kit runs them scripted only. Do it: the three saved runs, combined.

Operation: bash — the three saved runs as an ensemble (Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/arms_combine.txt]
```

### demo_10_verify_it_yourself.py

evals/tests/test_route_arms.py recomputes every figure of the arms set, holds the rows to the route set's rules, runs the three arms end to end against a stand-in chat service (save, report, compare, combine) and checks the make targets; evals/tests/test_combine.py checks the vote, the selftest and what combine.py refuses. Standard library only, no lane, Rs 0.

**`step_01_lesson_10_5_s_own_tests(session)` — Verify it yourself / Do it: lesson 10.5's own tests**

evals/tests/test_route_arms.py recomputes every figure of the arms set, holds the rows to the route set's rules, runs the three arms end to end against a stand-in chat service (save, report, compare, combine) and checks the make targets; evals/tests/test_combine.py checks the vote, the selftest and what combine.py refuses. Standard library only, no lane, Rs 0.

Operation: bash — lesson 10.5's own tests, offline.

Expected shape, not a promised result:

```text
----------------------------------------------------------------------
Ran 21 tests in N.NNNs

OK
----------------------------------------------------------------------
Ran 12 tests in N.NNNs

OK
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.5_Agent_Desks_WIX.html`. All 58 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `c28dde874c47f9fe22a3fa07eca871da38a48b53`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
