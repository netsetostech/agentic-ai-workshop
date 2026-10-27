# Lesson 6.8: Resume a paused or cut-off turn: checkpoint and resume

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_your_conversation_read_back_step_by_step.py](demo_03_your_conversation_read_back_step_by_step.py) | Your conversation, read back step by step |
| 4 | [demo_04_a_turn_cut_off_mid_flight_resumed_from_its_checkpoint.py](demo_04_a_turn_cut_off_mid_flight_resumed_from_its_checkpoint.py) | A turn cut off mid-flight, resumed from its checkpoint |
| 5 | [demo_05_what_the_chat_service_does_instead_a_new_question_and_the_repair.py](demo_05_what_the_chat_service_does_instead_a_new_question_and_the_repair.py) | What the chat service does instead: a new question, and the repair |
| 6 | [demo_06_one_step_read_back_and_the_thread_exported.py](demo_06_one_step_read_back_and_the_thread_exported.py) | One step read back, and the thread exported |
| 7 | [demo_07_your_thread_replayed_and_forked_on_your_machine.py](demo_07_your_thread_replayed_and_forked_on_your_machine.py) | Your thread replayed and forked on your machine |
| 8 | [demo_08_the_table_read_directly.py](demo_08_the_table_read_directly.py) | The table, read directly |

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

### demo_03_your_conversation_read_back_step_by_step.py

Do it: two questions in the UI Do it: your thread

**`step_01_two_questions_in_the_ui(session)` — Your conversation, read back step by step / Do it: two questions in the UI**

Do it: two questions in the UI

Operation: bash — run in the operator shell (the address of your UI).

Expected shape, not a promised result:

```text
open https://documind-ui-NUMBER.asia-south1.run.app and sign in as you@your-company.com
```

**`step_02_your_thread(session)` — Your conversation, read back step by step / Do it: your thread**

Do it: your thread

Operation: bash — run in the operator shell, in the kit (your threads, then the newest decoded; reads only).

Manual action: In the deployed UI's Chat page, signed in as yourself, set Brain to langgraph and ask: After how many years of continuous service is gratuity payable? When the answer is in, ask: Is it payable to a contract employee? Type done to read your thread back from the checkpointer: without the two questions there is no thread, and every later step of this lesson has nothing to read.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ui_thread.txt]
```

### demo_04_a_turn_cut_off_mid_flight_resumed_from_its_checkpoint.py

Do it: the cut-off turn, resumed At step 0 the first turn had not yet called the model, and the file recorded everything after it, so there is something to compare. The replay re-runs the turn from there and compares what it produced with what the file recorded: each message's kind and the tools it asked for, the sources each search returned, and the answer. A recording that stops mid-turn, like this thread's second turn, is compared as far as it goes, and the rest is what the replay added.

**`step_01_the_cut_off_turn_resumed(session)` — A turn cut off mid-flight, resumed from its checkpoint / Do it: the cut-off turn, resumed**

Do it: the cut-off turn, resumed

Operation: bash — run in the operator shell, in the kit (the kit's cut-off thread, resumed on your machine; no network, Rs 0).

Expected shape, not a promised result:

```text
thread acme:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:lesson68
  from evals/threads/cut_off_turn.json: 8 checkpoints, steps -1 to 6, 2 turns
offline: the model is a script (the thread's own model messages played back, then a rule), a search the thread
  recorded is answered as recorded and any other by the kit's Rs 0 lane over evals/corpus; no network, Rs 0

1. the copy: 8 checkpoints in a local InMemorySaver, one update_state() each; every step's number, next and messages are the file's

2. replay from step 6 (next tools): graph.invoke(None, the config at step 6), through the kit's LangGraph brain
   the turn's question: 'Is gratuity payable to a contract employee?'
   step 6 is where the recorded turn stopped: the model had asked retrieve(query='Is gratuity payable to a contract employee?') and the tool never ran
     + tool   retrieve: 5 citations [1]-[5]
     + ai     (offline, scripted) The first passage says: "(2) As soon as gratuity becomes payable, the emp...
   nothing was recorded after step 6: the replay finished the turn: 2 messages, 1 model call

3. fork from step 4, the turn's input: graph.update_state(the config at step 4, a new question), then graph.invoke(None, the fork)
   the fork's question: 'Is gratuity payable to a contract employee? Answer in one sentence.'
     + human  Is gratuity payable to a contract employee? Answer in one sentence.
     + ai     asks retrieve(query='Is gratuity payable to a contract employee? Answer in one sentenc...
     + tool   retrieve: 5 citations [1]-[5]
     + ai     (offline, scripted) The first passage says: "(2) As soon as gratuity becomes payable, the emp...

4. graph.get_state_history(thread): 14 checkpoints, in 2 branches
     branch     step  source  next        msgs  from  the newest message
     copy         -1  input   __start__      0     -  -
     copy          0  update  agent          1    -1  human  After how many years of continuous service is gratuit...
     copy          1  update  tools          2     0  ai     asks retrieve(query='After how many years of c...
     copy          2  update  agent          3     1  tool   retrieve: 5 citations [1]-[5]
     copy          3  update  -              4     2  ai     (offline, scripted) The first passage says: "Payment...
     copy          4  input   __start__      4     3  ai     (offline, scripted) The first passage says: "Payment...
     copy          5  update  agent          5     4  human  Is gratuity payable to a contract employee?
     copy          6  update  tools          6     5  ai     asks retrieve(query='Is gratuity payable to a...
     replay        7  loop    agent          7     6  tool   retrieve: 5 citations [1]-[5]
     replay        8  loop    -              8     7  ai     (offline, scripted) The first passage says: "(2) As s...
     fork          5  update  agent          5     4  human  Is gratuity payable to a contract employee? Answer in...
     fork          6  loop    tools          6     5  ai     asks retrieve(query='Is gratuity payable to a...
     fork          7  loop    agent          7     6  tool   retrieve: 5 citations [1]-[5]
     fork          8  loop    -              8     7  ai     (offline, scripted) The first passage says: "(2) As s...

only the local copy was written; the lane never is. Model calls: the replay 1, the fork 2; Rs 0 (a script, not a model)
```

**`step_02_a_finished_turn_replayed(session)` — A turn cut off mid-flight, resumed from its checkpoint / Do it: a finished turn, replayed**

At step 0 the first turn had not yet called the model, and the file recorded everything after it, so there is something to compare. The replay re-runs the turn from there and compares what it produced with what the file recorded: each message's kind and the tools it asked for, the sources each search returned, and the answer. A recording that stops mid-turn, like this thread's second turn, is compared as far as it goes, and the rest is what the replay added.

Operation: bash — run in the operator shell, in the kit (a finished turn replayed from step 0; no network, Rs 0).

Expected shape, not a promised result:

```text
thread acme:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:lesson68
  from evals/threads/cut_off_turn.json: 8 checkpoints, steps -1 to 6, 2 turns
offline: the model is a script (the thread's own model messages played back, then a rule), a search the thread
  recorded is answered as recorded and any other by the kit's Rs 0 lane over evals/corpus; no network, Rs 0

1. the copy: 8 checkpoints in a local InMemorySaver, one update_state() each; every step's number, next and messages are the file's

2. replay from step 0 (next agent): graph.invoke(None, the config at step 0), through the kit's LangGraph brain
   the turn's question: 'After how many years of continuous service is gratuity payable?'
     + ai     asks retrieve(query='After how many years of continuous service is gratuity payable?')
     + tool   retrieve: 5 citations [1]-[5]
     + ai     (offline, scripted) The first passage says: "Payment of Gratuity.- (1) Gratuity shall be paya...
   the replay matches the recorded turn: the same steps (ai asks retrieve, tool, ai), the same sources (5 citations), the same answer

3. fork from step -1, the turn's input: graph.update_state(the config at step -1, a new question), then graph.invoke(None, the fork)
   the fork's question: 'After how many years of continuous service is gratuity payable? Answer in one sentence.'
     + human  After how many years of continuous service is gratuity payable? Answer in one sentence.
     + ai     asks retrieve(query='After how many years of continuous service is gratuity payable? A...
     + tool   retrieve: 5 citations [1]-[5]
     + ai     (offline, scripted) The first passage says: "Payment of Gratuity.- (1) Gratuity shall be paya...

4. graph.get_state_history(thread): 15 checkpoints, in 3 branches
     branch     step  source  next        msgs  from  the newest message
     copy         -1  input   __start__      0     -  -
     copy          0  update  agent          1    -1  human  After how many years of continuous service is gratuit...
     copy          1  update  tools          2     0  ai     asks retrieve(query='After how many years of c...
     copy          2  update  agent          3     1  tool   retrieve: 5 citations [1]-[5]
     copy          3  update  -              4     2  ai     (offline, scripted) The first passage says: "Payment...
     copy          4  input   __start__      4     3  ai     (offline, scripted) The first passage says: "Payment...
     copy          5  update  agent          5     4  human  Is gratuity payable to a contract employee?
     copy          6  update  tools          6     5  ai     asks retrieve(query='Is gratuity payable to a...
     replay        1  loop    tools          2     0  ai     asks retrieve(query='After how many years of c...
     replay        2  loop    agent          3     1  tool   retrieve: 5 citations [1]-[5]
     replay        3  loop    -              4     2  ai     (offline, scripted) The first passage says: "Payment...
     fork          0  update  agent          1    -1  human  After how many years of continuous service is gratuit...
     fork          1  loop    tools          2     0  ai     asks retrieve(query='After how many years of c...
     fork          2  loop    agent          3     1  tool   retrieve: 5 citations [1]-[5]
     fork          3  loop    -              4     2  ai     (offline, scripted) The first passage says: "Payment...

only the local copy was written; the lane never is. Model calls: the replay 2, the fork 2; Rs 0 (a script, not a model)
```

### demo_05_what_the_chat_service_does_instead_a_new_question_and_the_repair.py

Do it: the next question, offline The script above accepts any history. Gemini is the model your lane runs, so this cell asks it the same question on a copy of the cut-off thread, through the kit's LangGraph brain, with your lane's rag-api as documind-ui-sa: what /v1/chat would do. It prints the answer, or the error that would have been the request's 500, then the messages from the open call on, the calls left open and what the turn cost.

**`step_01_the_next_question_offline(session)` — What the chat service does instead: a new question, and the repair / Do it: the next question, offline**

Do it: the next question, offline

Operation: bash — run in the operator shell, in the kit (the next question on the cut-off thread, as it is and repaired; no network, Rs 0).

Expected shape, not a promised result:

```text
as it was cut off, then the question 'Is gratuity payable to an apprentice?':
    6. ai     asks retrieve(query='Is gratuity payable to a contract employee?')
    7. human  Is gratuity payable to an apprentice?
    8. ai     asks retrieve(query='Is gratuity payable to an apprentice?')
    9. tool   retrieve: 5 citations [1]-[5]
   10. ai     (offline, scripted) The first passage says: "the amount of gratuity so determined. (3) The em...
  now at step 11; tool calls no tool message answers: retrieve call_21c9aa740d14
repaired by limits.repair_thread, then the question 'Is gratuity payable to an apprentice?':
    6. ai     asks retrieve(query='Is gratuity payable to a contract employee?')
    7. tool   retrieve: {"error": "the turn stopped before this call ran"}
    8. ai     I stopped this turn at one of its limits before I could finish, so this answer is incomplete....
    9. human  Is gratuity payable to an apprentice?
   10. ai     asks retrieve(query='Is gratuity payable to an apprentice?')
   11. tool   retrieve: 5 citations [1]-[5]
   12. ai     (offline, scripted) The first passage says: "the amount of gratuity so determined. (3) The em...
  now at step 12; tool calls no tool message answers: none
```

**`step_02_the_next_question_with_gemini(session)` — What the chat service does instead: a new question, and the repair / Do it: the next question, with Gemini**

The script above accepts any history. Gemini is the model your lane runs, so this cell asks it the same question on a copy of the cut-off thread, through the kit's LangGraph brain, with your lane's rag-api as documind-ui-sa: what /v1/chat would do. It prints the answer, or the error that would have been the request's 500, then the messages from the open call on, the calls left open and what the turn cost.

Operation: bash — run in the operator shell, in the kit (the same question with Gemini and your rag-api; one turn at most).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/next_turn.txt]
```

### demo_06_one_step_read_back_and_the_thread_exported.py

Do it

**`step_01_one_step_read_back_and_the_thread_exported(session)` — One step read back, and the thread exported / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one step read back, and the thread written to a file; reads only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/thread_at.txt]
```

### demo_07_your_thread_replayed_and_forked_on_your_machine.py

Do it The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

**`step_01_your_thread_replayed_and_forked_on_your_ma(session)` — Your thread replayed and forked on your machine / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (your thread replayed and forked on your machine; a few model calls).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/replay_fork.txt]
```

**`step_02_change_it_the_prompt_s_rule_for_follow_ups(session)` — Your thread replayed and forked on your machine / Change it: the prompt's rule for follow-ups**

The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

Operation: bash — run in the operator shell, in the kit (edits one line of your clone's brains.py).

IDE adaptation: Read grep's count, not its status: once the sed has taken the clause out, grep -c prints the 0 the page reads and exits 1, which stopped the demo with brains.py still edited and its restore not run (22 October 2026). The sed still fails the step if it fails.

Expected shape, not a promised result:

```text
0
```

**`step_03_change_it_the_prompt_s_rule_for_follow_ups(session)` — Your thread replayed and forked on your machine / Change it: the prompt's rule for follow-ups**

The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

Operation: bash — run in the operator shell, in the kit (the same replay, with the edited prompt).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/changeit.txt]
```

**`step_04_change_it_the_prompt_s_rule_for_follow_ups(session)` — Your thread replayed and forked on your machine / Change it: the prompt's rule for follow-ups**

The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

Operation: bash — run in the operator shell, in the kit (the kit's prompt back).

Expected shape, not a promised result:

```text
1
```

### demo_08_the_table_read_directly.py

Do it

**`step_01_the_table_read_directly(session)` — The table, read directly / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (your thread's rows, read directly; reads only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/table_read.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.8_Checkpoint_Resume_WIX.html`. All 44 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `348f42b5d8a0f3bd6fa7cd9413e7e42fd83d5a0f`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
