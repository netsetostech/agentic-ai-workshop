# Lesson 10.3: Check, retry or choose: the critic and refiner pattern

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 4 | [demo_04_the_figure_check_on_its_own_at_rs_0.py](demo_04_the_figure_check_on_its_own_at_rs_0.py) | The figure check on its own, at Rs 0 |
| 5 | [demo_05_verify_the_loop_the_check_and_one_reflect_call_offline.py](demo_05_verify_the_loop_the_check_and_one_reflect_call_offline.py) | verify: the loop, the check and one reflect call, offline |
| 6 | [demo_06_change_it_put_the_notes_into_the_question.py](demo_06_change_it_put_the_notes_into_the_question.py) | Change it: put the notes into the question |
| 7 | [demo_07_the_12_calculator_rows_offline_re_roll_choose_retry.py](demo_07_the_12_calculator_rows_offline_re_roll_choose_retry.py) | The 12 calculator rows offline: re-roll, choose, retry |
| 8 | [demo_08_your_lane_one_verify_turn.py](demo_08_your_lane_one_verify_turn.py) | Your lane: one verify turn |
| 9 | [demo_09_the_12_rows_on_your_lane_with_the_calculator_rule_taken_out.py](demo_09_the_12_rows_on_your_lane_with_the_calculator_rule_taken_out.py) | The 12 rows on your lane, with the calculator rule taken out |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project. Their Python cells need only the shell's own Python; the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4, 10.1 and 10.2 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global, and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's and zeta's stored rows their classes. If you have not run it, run this now: the 12 rows are acme's but one, zeta's carry-forward. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project. Their Python cells need only the shell's own Python; the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4, 10.1 and 10.2 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global, and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's and zeta's stored rows their classes. If you have not run it, run this now: the 12 rows are acme's but one, zeta's carry-forward. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

Operation: bash — run in the operator shell, in the kit (once, if lesson 10.1's setup line has not run: acme's and zeta's stored rows get their classes).

### demo_04_the_figure_check_on_its_own_at_rs_0.py

agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs the check. The cell works the gratuity row's figure out with desk_calc.calculate(), uses the Code's own words as quoted in desk_calc.RULES as the passage, and puts eight answers through figure_check(). Then it asks check_args about a wage the question does not state, once on the person's question and once with a note's words put into it. After a failed check, ask_reflect() writes the reflect call's user turn: the question, the answer, what the attempt did (did_lines()) and the verdict. cut_note() turns its reply into the note, and noted() puts every note into the next attempt's system prompt. The cell gives ask_reflect() an attempt whose calculator returned Rs 2,40,000 and whose answer wrote Rs 2,50,000, then cuts a long reply the way verify cuts every note.

**`step_01_the_check_on_eight_answers_and_check_args(session)` — The figure check on its own, at Rs 0 / Do it: the check on eight answers, and check_args on a note**

agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs the check. The cell works the gratuity row's figure out with desk_calc.calculate(), uses the Code's own words as quoted in desk_calc.RULES as the passage, and puts eight answers through figure_check(). Then it asks check_args about a wage the question does not state, once on the person's question and once with a note's words put into it.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the figure check and check_args, no model).

Expected shape, not a promised result:

```text
the calculator returned Rs 2,40,000
its figure, from the calculator          passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
the same figure, no calculator           failed: no calculator, question or passage of the turn wrote 2,40,000
a figure of its own                      failed: no calculator, question or passage of the turn wrote 2,50,000
a passage it never read                  failed: it cites [3], which no passage the turn read carries
a turn its limits stopped                failed: the turn stopped at its model_calls limit
a yes in words, no calculator            passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
LV-07's 45 copied, no calculator         passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
no calculator, the note in the question  passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
check_args on the person's question: monthly_wage = 60000 is a fact about the person that their message does not state: ask them for it
check_args on a note put into it: monthly_wage = 60000 taken
```

**`step_02_what_a_reflect_call_reads_and_what_code_ke(session)` — The figure check on its own, at Rs 0 / Do it: what a reflect call reads, and what code keeps of its reply**

After a failed check, ask_reflect() writes the reflect call's user turn: the question, the answer, what the attempt did (did_lines()) and the verdict. cut_note() turns its reply into the note, and noted() puts every note into the next attempt's system prompt. The cell gives ask_reflect() an attempt whose calculator returned Rs 2,40,000 and whose answer wrote Rs 2,50,000, then cuts a long reply the way verify cuts every note.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: what a reflect call reads, and the note code keeps).

Expected shape, not a promised result:

```text
Question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

Your answer: Gratuity, an estimate: Rs 2,50,000 [1].

What you did:
   call: retrieve {"query": "gratuity fifteen days wages"}
   returned: [1] code_on_social_security_2020.pdf
   call: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
   returned: a figure

The figure check failed: no calculator, question or passage of the turn wrote 2,50,000
the calculator's figure in what the reflect call reads: False

the reply, 386 characters; the note code keeps, 299:
I wrote Rs 2,50,000 although 'gratuity_estimate' returned another figure. Next time: call gratuity_estimate with the wage and the service the question states, state exactly the figure it returns, cite the passage, and give its formula. I will not round, estimate or work out any figure myself, and I
figures the note writes: 2,50,000
```

### demo_05_verify_the_loop_the_check_and_one_reflect_call_offline.py

Do it: as the prompt stands Do it: a figure of its own, corrected in one round Do it: notes that carry a figure

**`step_01_as_the_prompt_stands(session)` — verify: the loop, the check and one reflect call, offline / Do it: as the prompt stands**

Do it: as the prompt stands

Operation: bash — run in the operator shell, in the kit (Rs 0: verify on the gratuity row as the prompt stands; the first run builds ~/graph-venv).

Expected shape, not a promised result:

```text
agent turn: pattern verify, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes ships
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  the figure check: code, no model (figure_check(): desk_calc.unsupported() over the attempt's calculations, question and passages, every [n] a passage read, no stop); at most 3 attempts, each a turn of its own, a note of at most 300 characters before each retry
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

attempt 1: the loop, a turn of its own
model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 2 (thinking low): in 2,329, thinking 64, visible 17 tokens, Rs 0.3486
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 3 (thinking low): in 2,840, thinking 64, visible 10 tokens, Rs 0.4093
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
the answer that ships: attempt 1's, the first the figure check passed

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].


3 model calls in 1 attempt and 0 reflect calls (12 at most an attempt); the answer that ships: 1 search, 1 calculation, 0 refused or failed tool calls; stopped by nothing
tokens: in 5,436, thinking 192, visible 48; Rs 0.8461 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: answer 3 calls, Rs 0.8461 (gemini-3.6-flash)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_a_figure_of_its_own_corrected_in_one_round(session)` — verify: the loop, the check and one reflect call, offline / Do it: a figure of its own, corrected in one round**

Do it: a figure of its own, corrected in one round

Operation: bash — run in the operator shell, in the kit (Rs 0: a first attempt that writes a figure of its own).

Expected shape, not a promised result:

```text
agent turn: pattern verify, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes ships
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  --invent: the scripted model's first attempt writes Rs 2,50,000 in place of its calculator's figure
  the figure check: code, no model (figure_check(): desk_calc.unsupported() over the attempt's calculations, question and passages, every [n] a passage read, no stop); at most 3 attempts, each a turn of its own, a note of at most 300 characters before each retry
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

attempt 1: the loop, a turn of its own
model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 2 (thinking low): in 2,329, thinking 64, visible 10 tokens, Rs 0.3441
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,50,000 [2].
  the figure check, code and no model: failed: no calculator, question or passage of the turn wrote 2,50,000
attempt 2: the loop, a turn of its own, after a note
model call 3 (reflect, gemini-3.6-flash, thinking low): in 546, thinking 64, visible 58 tokens, Rs 0.1474
  the note, cut to 300 characters by code, into this attempt's system prompt, never its question: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages.
model call 4 (thinking low): in 383, thinking 64, visible 21 tokens, Rs 0.1030
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 5 (thinking low): in 2,445, thinking 64, visible 17 tokens, Rs 0.3634
  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)
       = Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000
model call 6 (thinking low): in 2,957, thinking 64, visible 10 tokens, Rs 0.4242
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
the answer that ships: attempt 2's, the first the figure check passed

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].


6 model calls in 2 attempts and 1 reflect call (12 at most an attempt); the answer that ships: 1 search, 1 calculation, 0 refused or failed tool calls; stopped by nothing
tokens: in 8,927, thinking 384, visible 137; Rs 1.4703 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: answer 5 calls, Rs 1.3229 (gemini-3.6-flash); reflect 1 call, Rs 0.1474 (gemini-3.6-flash)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_03_notes_that_carry_a_figure(session)` — verify: the loop, the check and one reflect call, offline / Do it: notes that carry a figure**

Do it: notes that carry a figure

Operation: bash — run in the operator shell, in the kit (Rs 0: notes that carry a figure).

Expected shape, not a promised result:

```text
agent turn: pattern verify, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes ships
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  --launder: each note the scripted model writes carries Rs 2,40,000, and each later attempt writes it as its own figure, with no calculator; its first attempt writes the row's figure itself
  the figure check: code, no model (figure_check(): desk_calc.unsupported() over the attempt's calculations, question and passages, every [n] a passage read, no stop); at most 3 attempts, each a turn of its own, a note of at most 300 characters before each retry
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

attempt 1: the loop, a turn of its own
model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 2 (thinking low): in 2,329, thinking 64, visible 10 tokens, Rs 0.3441
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: failed: no calculator, question or passage of the turn wrote 2,40,000
attempt 2: the loop, a turn of its own, after a note
model call 3 (reflect, gemini-3.6-flash, thinking low): in 546, thinking 64, visible 65 tokens, Rs 0.1519
  the note, cut to 300 characters by code, into this attempt's system prompt, never its question: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages. The figure is Rs 2,40,000.
  the note writes 2,40,000: a note is never a source, so check_args refuses it as an argument and the figure check flags it in an answer
model call 4 (thinking low): in 390, thinking 64, visible 21 tokens, Rs 0.1039
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 5 (thinking low): in 2,452, thinking 64, visible 10 tokens, Rs 0.3598
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: failed: no calculator, question or passage of the turn wrote 2,40,000
attempt 3: the loop, a turn of its own, after a note
model call 6 (reflect, gemini-3.6-flash, thinking low): in 546, thinking 64, visible 65 tokens, Rs 0.1519
  the note, cut to 300 characters by code, into this attempt's system prompt, never its question: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages. The figure is Rs 2,40,000.
  the note writes 2,40,000: a note is never a source, so check_args refuses it as an argument and the figure check flags it in an answer
model call 7 (thinking low): in 456, thinking 64, visible 21 tokens, Rs 0.1123
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 8 (thinking low): in 2,517, thinking 64, visible 10 tokens, Rs 0.3681
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: failed: no calculator, question or passage of the turn wrote 2,40,000
the answer that ships: attempt 3's, the last of 3: the figure check passed none

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

8 model calls in 3 attempts and 2 reflect calls (12 at most an attempt); the answer that ships: 1 search, 0 calculations, 0 refused or failed tool calls; stopped by nothing
tokens: in 9,503, thinking 512, visible 223; Rs 1.6802 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: answer 6 calls, Rs 1.3765 (gemini-3.6-flash); reflect 2 calls, Rs 0.3037 (gemini-3.6-flash)
figure check: no calculator, question or passage wrote 2,40,000 (desk_calc.unsupported)
```

### demo_06_change_it_put_the_notes_into_the_question.py

Do it: the notes in the question Put it back

**`step_01_the_notes_in_the_question(session)` — Change it: put the notes into the question / Do it: the notes in the question**

Do it: the notes in the question

Operation: bash — run in the operator shell, in the kit (the Change-it: the notes put into the question, then the same run).

Expected shape, not a promised result:

```text
commands/agent_patterns.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
agent turn: pattern verify, desk astar, tenant acme
  the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
  thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
  verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes ships
  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
  --launder: each note the scripted model writes carries Rs 2,40,000, and each later attempt writes it as its own figure, with no calculator; its first attempt writes the row's figure itself
  the figure check: code, no model (figure_check(): desk_calc.unsupported() over the attempt's calculations, question and passages, every [n] a passage read, no stop); at most 3 attempts, each a turn of its own, a note of at most 300 characters before each retry
question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due? My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages. The figure is Rs 2,40,000.

attempt 1: the loop, a turn of its own
model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 2 (thinking low): in 2,329, thinking 64, visible 10 tokens, Rs 0.3441
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: failed: no calculator, question or passage of the turn wrote 2,40,000
attempt 2: the loop, a turn of its own, after a note
model call 3 (reflect, gemini-3.6-flash, thinking low): in 546, thinking 64, visible 65 tokens, Rs 0.1519
  the note, cut to 300 characters by code, into this attempt's system prompt, never its question: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages. The figure is Rs 2,40,000.
  the note writes 2,40,000: a note is never a source, so check_args refuses it as an argument and the figure check flags it in an answer
model call 4 (thinking low): in 455, thinking 64, visible 21 tokens, Rs 0.1122
  -> retrieve(query="gratuity fifteen days wages for every completed year of service")
       5 passages
model call 5 (thinking low): in 2,517, thinking 64, visible 10 tokens, Rs 0.3681
  -> no tool: the answer
  the attempt's answer: Gratuity, an estimate: Rs 2,40,000 [2].
  the figure check, code and no model: passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
the answer that ships: attempt 2's, the first the figure check passed

answer, as the Desk shows it (the model's text, then what code writes):
  Gratuity, an estimate: Rs 2,40,000 [2].

5 model calls in 2 attempts and 1 reflect call (12 at most an attempt); the answer that ships: 1 search, 0 calculations, 0 refused or failed tool calls; stopped by nothing
tokens: in 6,114, thinking 320, visible 127; Rs 1.0645 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
by role: answer 4 calls, Rs 0.9126 (gemini-3.6-flash); reflect 1 call, Rs 0.1519 (gemini-3.6-flash)
figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
```

**`step_02_put_it_back(session)` — Change it: put the notes into the question / Put it back**

Put it back

Operation: bash — run in the operator shell, in the kit (put the line back).

Expected shape, not a promised result:

```text
1
```

### demo_07_the_12_calculator_rows_offline_re_roll_choose_retry.py

Do it: check the rows, then run them Do it: side by side, at Rs 0 Each saved run is one JSON line, the turn's record. A verify run's record carries every attempt, with the note it started from and the figures that note writes. The cell rescores every run with the eval's own functions and prints, row by row, the check's verdict on each of the loop's runs, the run best-of-3 ships, verify's attempts, and each note.

**`step_01_check_the_rows_then_run_them(session)` — The 12 calculator rows offline: re-roll, choose, retry / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the 12 rows recomputed).

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
ok    trap-encash-cap: encashable_days(balance=50, cap=45) = 45 days (LV-07); LV-07 writes 45 days itself: the trap
12 rows (11 calc, 0 lookup, 1 trap, 0 refuse, 0 chained): every figure recomputed by shared/desk_calc.py, every clause in the corpus, every question let through by the hard gate
```

**`step_02_check_the_rows_then_run_them(session)` — The 12 calculator rows offline: re-roll, choose, retry / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0: the loop, three scripted runs a row, saved).

Expected shape, not a promised result:

```text
OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 3 runs each, in this process (--inproc)
saved 36 runs to /home/you/plain-offline.jsonl: --replay rescores them at Rs 0
== loop, thinking default (low), desk astar: 12 rows x 3 runs
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  calc-gratuity-7y8m           calc        3/3        2/3   2.7      171      42   0.7082  no gratuity_estimate call returned it; unsupported: 2,40,000
  calc-gratuity-7y6m           calc        3/3        2/3   2.7      171      42   0.7116  
  calc-gratuity-fixed-term     calc        3/3        3/3   3.0      192      54   0.8982  
  calc-carry-forward           calc        3/3        3/3   3.0      192      37   0.7989  
  calc-carry-forward-zeta      calc        3/3        3/3   3.0      192      37   0.7806  
  calc-encash-invented-cap     calc        3/3        3/3   3.0      192      35   0.6446  
  calc-accrued                 calc        3/3        3/3   3.0      192      37   0.5672  
  calc-notice-e3               calc        3/3        2/3   2.7      171      38   0.6843  
  calc-notice-probation        calc        3/3        3/3   3.0      192      35   0.6811  
  calc-wages-due               calc        3/3        2/3   2.7      171      40   0.6987  
  calc-grc-threshold           calc        3/3        2/3   2.7      171      50   0.7251  no threshold_check call returned it
  trap-encash-cap              trap        3/3        2/3   2.7      171      31   0.5441  no encashable_days call returned it
  first runs: correct    12/12 = 100.0% [75.7%, 100.0%]
              provenance 9/12 = 75.0% [46.8%, 91.1%]
              verified   9/12 = 75.0% [46.8%, 91.1%]
  correct pass@1 1.000, pass^1 1.000; verified pass@1 0.833, pass^1 0.833   (over each row's runs, averaged over rows)
  correct pass@3 1.000, pass^3 1.000; verified pass@3 1.000, pass^3 0.500
  a run: 2.8 model calls, 1.0 searches, thinking 181 and visible 40 tokens, Rs 0.7036 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 102 model calls, Rs 25.3280 for the model and Rs 0.0000 for rag-api
```

**`step_03_check_the_rows_then_run_them(session)` — The 12 calculator rows offline: re-roll, choose, retry / Do it: check the rows, then run them**

Do it: check the rows, then run them

Operation: bash — run in the operator shell, in the kit (Rs 0: verify, one scripted run a row, saved).

Expected shape, not a promised result:

```text
OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 1 run each, in this process (--inproc)
saved 12 runs to /home/you/verify-offline.jsonl: --replay rescores them at Rs 0
== verify, thinking default (low), desk astar: 12 rows x 1 run
  row                          kind    correct provenance calls thinking visible       Rs  why, first run
  calc-gratuity-7y8m           calc        yes        yes   6.0      384     137   1.4703  
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
  trap-encash-cap              trap        yes         no   2.0      128      24   0.3537  no encashable_days call returned it
  first runs: correct    12/12 = 100.0% [75.7%, 100.0%]
              provenance 10/12 = 83.3% [55.2%, 95.3%]
              verified   10/12 = 83.3% [55.2%, 95.3%]
  with notes: the figure check passed on attempt 1 in 11, on attempt 2 in 1, on attempt 3 in 0 and on none in 0 of 12 runs (at most 3 attempts a run); 1.1 attempts, 0.1 reflect calls and 0.1 notes a run; 0 of 1 notes write a figure, which no check takes from a note
  any attempt (the ceiling, each row's first run): correct 12/12 = 100.0% [75.7%, 100.0%], verified 10/12 = 83.3% [55.2%, 95.3%]
  a run: 3.1 model calls, 1.0 searches, thinking 197 and visible 48 tokens, Rs 0.7620 for the model and Rs 0.0000 for rag-api (the script's tokens at list price: nothing is billed)
  in all: 37 model calls, Rs 9.1440 for the model and Rs 0.0000 for rag-api
  by role, a run: answer 3.0 calls, Rs 0.7497 (gemini-3.6-flash); reflect 0.1 calls, Rs 0.0123 (gemini-3.6-flash)
```

**`step_04_side_by_side_at_rs_0(session)` — The 12 calculator rows offline: re-roll, choose, retry / Do it: side by side, at Rs 0**

Do it: side by side, at Rs 0

Operation: bash — run in the operator shell, in the kit (Rs 0: the two saves side by side; the first line, then what the two reports above do not print).

Expected shape, not a promised result:

```text
replayed 48 saved runs of /home/you/plain-offline.jsonl, /home/you/verify-offline.jsonl: rescored at Rs 0, no model call (they cost Rs 34.4720 when they ran; offline, the script)
  paired (correct), 12 rows: both 12, loop only 0, verify only 0, neither 0
  verify - loop = +0.0 points, 95% [-24.3, +24.3] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
  paired (verified), 12 rows: both 9, loop only 0, verify only 1, neither 2
  verify - loop = +8.3 points, 95% [-10.3, +28.7] (Newcombe), exact McNemar p = 1.000
  no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
== check, retry or choose (lesson 10.3): loop against verify, on the 12 rows both ran
  pass@1, loop's first run: correct 12/12 = 100.0% [75.7%, 100.0%], verified 9/12 = 75.0% [46.8%, 91.1%]; 2.8 calls and Rs 0.6755 a row
  pass@3 re-rolls, any of its first 3 runs (the ceiling a perfect chooser reaches): correct 12/12 = 100.0% [75.7%, 100.0%], verified 12/12 = 100.0% [75.7%, 100.0%]; 8.5 calls and Rs 2.1107 a row
  best-of-3, the run the figure check chooses (code, no model): correct 12/12 = 100.0% [75.7%, 100.0%], verified 12/12 = 100.0% [75.7%, 100.0%]; 8.5 calls and Rs 2.1107 a row
  pass@3 with notes, verify's answer that ships (up to 3 attempts, a note before each retry): correct 12/12 = 100.0% [75.7%, 100.0%], verified 10/12 = 83.3% [55.2%, 95.3%]; 3.1 calls and Rs 0.7620 a row
  the figure check's precision: of the 32 of loop's 36 runs it passes, 32 correct (100%) and 30 verified; of the 12 of verify's 13 attempts it passes, 12 correct (100%) and 10 verified
```

**`step_05_the_saved_runs_read_back(session)` — The 12 calculator rows offline: re-roll, choose, retry / Do it: the saved runs, read back**

Each saved run is one JSON line, the turn's record. A verify run's record carries every attempt, with the note it started from and the figures that note writes. The cell rescores every run with the eval's own functions and prints, row by row, the check's verdict on each of the loop's runs, the run best-of-3 ships, verify's attempts, and each note.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back, row by row).

Expected shape, not a promised result:

```text
calc-gratuity-7y8m
  loop runs: check fail/pass/pass, verified no/yes/yes; best-of-3 ships run 2
  verify: check fail -> pass; ships attempt 2, verified yes
    the note before attempt 2: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages.
    figures it writes: none
calc-gratuity-7y6m
  loop runs: check pass/pass/fail, verified yes/yes/no; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-gratuity-fixed-term
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-carry-forward
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-carry-forward-zeta
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-encash-invented-cap
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-accrued
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-notice-e3
  loop runs: check pass/pass/fail, verified yes/yes/no; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-notice-probation
  loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-wages-due
  loop runs: check pass/fail/pass, verified yes/no/yes; best-of-3 ships run 1
  verify: check pass; ships attempt 1, verified yes
calc-grc-threshold
  loop runs: check pass/pass/pass, verified no/yes/yes; best-of-3 ships run 2
  verify: check pass; ships attempt 1, verified no
trap-encash-cap
  loop runs: check pass/pass/pass, verified no/yes/yes; best-of-3 ships run 2
  verify: check pass; ships attempt 1, verified no
```

### demo_08_your_lane_one_verify_turn.py

Without OFFLINE=1, make agent-turn needs PROJECT, and commands/agent-turn.sh exports what a live turn needs: the project for Gemini, rag-api's address, built from REGION (pass yours: the Makefile's default is us-central1), and documind-ui-sa as the account rag-api's ID token is minted as. gemini() builds the model as the chat service builds the Desk agent's, gemini-3.6-flash on location global at thinking low, and the reflect call runs on the same model at the same level. Every search is one POST to /v1/passages, the call lesson 10.1 showed, which rag-api books with no tokens and no cost. Each attempt runs under the chat service's limits, 12 calls and Rs 5, with its reflect call counted on it, so a verify turn can spend up to Rs 15.00 in all. By the kit's own count the turn costs about Rs 1.16 before thinking when its first attempt passes, and each retry adds about Rs 1.31; step 10 shows how that count is made.

**`step_01_definition(session)` — Your lane: one verify turn / Definition**

Without OFFLINE=1, make agent-turn needs PROJECT, and commands/agent-turn.sh exports what a live turn needs: the project for Gemini, rag-api's address, built from REGION (pass yours: the Makefile's default is us-central1), and documind-ui-sa as the account rag-api's ID token is minted as. gemini() builds the model as the chat service builds the Desk agent's, gemini-3.6-flash on location global at thinking low, and the reflect call runs on the same model at the same level. Every search is one POST to /v1/passages, the call lesson 10.1 showed, which rag-api books with no tokens and no cost. Each attempt runs under the chat service's limits, 12 calls and Rs 5, with its reflect call counted on it, so a verify turn can spend up to Rs 15.00 in all. By the kit's own count the turn costs about Rs 1.16 before thinking when its first attempt passes, and each retry adds about Rs 1.31; step 10 shows how that count is made.

Operation: bash — run in the operator shell, in the kit (one live verify turn, about Rs 1.16 before thinking if its first attempt passes).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/turn_verify.txt]
```

### demo_09_the_12_rows_on_your_lane_with_the_calculator_rule_taken_out.py

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in. Do it: side by side, at Rs 0 The same cell as step 7, on your lane's saves.

**`step_01_definition(session)` — The 12 rows on your lane, with the calculator rule taken out / Definition**

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (delete the prompt's calculator rule, for the next two runs only).

Expected shape, not a promised result:

```text
services/chat/desk_agent.py | 3 ---
 1 file changed, 3 deletions(-)
```

**`step_02_definition(session)` — The 12 rows on your lane, with the calculator rule taken out / Definition**

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (36 live turns, about Rs 35.88 before thinking).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_plain.txt]
```

**`step_03_definition(session)` — The 12 rows on your lane, with the calculator rule taken out / Definition**

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (12 live verify runs, about Rs 12.83 before thinking, more for each retry).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_verify.txt]
```

**`step_04_definition(session)` — The 12 rows on your lane, with the calculator rule taken out / Definition**

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in services/chat/desk_agent.py, in your clone only. The bench imports desk_agent from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token. The runs are step 7's without OFFLINE=1: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

Operation: bash — run in the operator shell, in the kit (put the rule back, at once).

Expected shape, not a promised result:

```text
1
```

**`step_05_side_by_side_at_rs_0(session)` — The 12 rows on your lane, with the calculator rule taken out / Do it: side by side, at Rs 0**

Do it: side by side, at Rs 0

Operation: bash — run in the operator shell, in the kit (Rs 0: your two saves side by side).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_side.txt]
```

**`step_06_read_the_records_back_at_rs_0(session)` — The 12 rows on your lane, with the calculator rule taken out / Do it: read the records back, at Rs 0**

The same cell as step 7, on your lane's saves.

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/records_read.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.3_Critic_Refiner_WIX.html`. All 57 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `7dea9d7ffd5ff9269e2969481d0cd7d3175ff4e8`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
