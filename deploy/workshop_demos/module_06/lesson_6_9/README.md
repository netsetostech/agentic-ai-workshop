# Lesson 6.9: Budget working memory: windowing, compaction and write rules

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_on_your_lane_today_every_turn_sends_more.py](demo_03_on_your_lane_today_every_turn_sends_more.py) | On your lane today: every turn sends more |
| 4 | [demo_04_the_window_in_the_kit_and_one_call_opened_up.py](demo_04_the_window_in_the_kit_and_one_call_opened_up.py) | The window in the kit, and one call opened up |
| 5 | [demo_05_twenty_turns_with_the_window_and_without_it.py](demo_05_twenty_turns_with_the_window_and_without_it.py) | Twenty turns, with the window and without it |
| 6 | [demo_06_full_against_windowed_with_gemini.py](demo_06_full_against_windowed_with_gemini.py) | Full against windowed, with Gemini |
| 7 | [demo_07_what_the_checkpoint_keeps.py](demo_07_what_the_checkpoint_keeps.py) | What the checkpoint keeps |

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

### demo_03_on_your_lane_today_every_turn_sends_more.py

Do it

**`step_01_on_your_lane_today_every_turn_sends_more(session)` — On your lane today: every turn sends more / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the six chat rows step 3's turns wrote, from Cloud Logging).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ui_turns.txt]
```

### demo_04_the_window_in_the_kit_and_one_call_opened_up.py

Do it: the venv Do it: one call, opened up

**`step_01_the_venv(session)` — The window in the kit, and one call opened up / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (lesson 5.4's ~/graph-venv with the chat image's pins, made if it is missing).

Expected shape, not a promised result:

```text
graph-venv ok: langchain 1.4.0
```

**`step_02_one_call_opened_up(session)` — The window in the kit, and one call opened up / Do it: one call, opened up**

Do it: one call, opened up

Operation: bash — run in the operator shell, in the kit (ten turns of the kit's brain behind the window; a stand-in search, no network, Rs 0).

Expected shape, not a promised result:

```text
10 turns, 20 model calls, the window's budget for earlier turns 600 tokens
the checkpoint: 40 messages, 5,654 tokens; question 6 kept as typed: True
the card number in what the model was sent, all 20 calls: 0 times
turn 10's answering call, as the model received it: 12 messages, 1,179 tokens, its ceiling 1,201 (the floor 601 + 600)
   1  system  111  You are DocuMind AI, a document intelligence assistant. Use the tools for docu...
   2  human   150  [Earlier in this conversation, not shown here: turns 1 to 7. The person asked,...
   3  ai       43  asks retrieve
   4  tool     33  {"cleared": true, "reason": "evidence from an earlier turn: search again if yo...
   5  ai       56  (offline, scripted) The first passage says: "Stand-in passage 1. The policy te...
   6  human    79  I am drafting a note for the finance team about purchase approvals. A vendor h...
   7  ai      128  asks retrieve
   8  tool     33  {"cleared": true, "reason": "evidence from an earlier turn: search again if yo...
   9  ai       56  (offline, scripted) The first passage says: "Stand-in passage 1. The policy te...
  10  human    17  How many days a month may an employee work remotely?
  11  ai       42  asks retrieve
  12  tool    431  {"citations": [{"chunk_id": "acme:stand_in#1", "source_uri": "gs://bucket/acme...
the line: [Earlier in this conversation, not shown here: turns 1 to 7. The person asked, in turns 2 to 7: (2) "And during probation?" (3) "How many days of earned leave can be carried forward into the next year?" (4) "Is earned leave encashed when someone leaves the company?" (5) "What is the cap on domestic travel reimbursement per trip?" (6) "My corporate card [card no.] was charged twice for one flight. Who has to approve a travel claim above the cap?" (7) "When is Form 16 issued?" Search again for anything you need from them.]
turn 9's question, as this call carries it: 300 characters of 395
```

### demo_05_twenty_turns_with_the_window_and_without_it.py

Do it: with the window Do it: without the window Give earlier turns a quarter of the room, 500 tokens, and run the same twenty turns. CHAT_HISTORY_TOKENS=500 in the environment does the same as HISTORY=500.

**`step_01_with_the_window(session)` — Twenty turns, with the window and without it / Do it: with the window**

Do it: with the window

Operation: bash — run in the operator shell, in the kit.

Expected shape, not a promised result:

```text
make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0
  the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
  the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
  every call is sent the window: the system prompt and the turn it answers, whole, and at most 2,000 tokens
  of earlier turns (CHAT_HISTORY_TOKENS)
  tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

          thread           the turn's largest call     earlier turns              write rules
  turn    msgs   tokens     context   ceiling     kept whole  brought forward  cleared  masked  cut
     1       4      659         714     2,714              0                0        0       0    0
     2       8    1,309         854     2,705              1                0        1       0    0
     3      12    2,088       1,116     2,834              2                0        2       0    0
     4      16    2,792       1,199     2,759              3                0        3       0    0
     5      20    3,301       1,155     2,564              4                0        4       0    0
     6      24    4,245       1,739     2,997              5                0        5       1    0
     7      28    5,020       1,751     2,831              6                0        6       1    0
     8      32    5,682       1,770     2,717              7                0        7       1    0
     9      36    6,584       2,160     2,957              8                0        8       1    0
    10      40    7,481       2,451     2,952              9                0        9       1    1
    11      44    8,372       2,593     2,946             10                0       10       1    1
    12      48    9,196       2,680     2,879             11                0       11       1    1
    13      52   10,173       2,978     3,033             12                0       12       1    1
    14      56   11,073       2,837     2,955             11                2       11       1    1
    15      60   11,706       2,585     2,688             11                3       11       1    1
    16      64   12,563       2,817     2,912             11                4       11       1    1
    17      68   13,198       2,614     2,691             11                5       11       1    1
    18      72   14,163       2,949     3,021             11                6       11       1    1
    19      76   14,832       2,696     2,724             11                7       11       1    1
    20      80   15,657       2,862     2,880             11                8       11       1    1

20 turns, 40 model calls, Rs 0 (a script, not a model). The thread holds 80 messages, 15,657 tokens: the checkpoint keeps every one.
Every call's context was within its ceiling: yes. The last call sent 2,862 tokens, its ceiling 2,880:
  the system prompt (111) and turn 20 whole (769); 11 earlier turns kept whole, 11 results cleared; 8 brought forward in one line, 7 of their questions listed
  the whole thread would have been 15,712 tokens
  the line: [Earlier in this conversation, not shown here: turns 1 to 8. The person asked, in turns 2 to 8: (2) "And during probation?" (3) "How many days of earned leave can be carried forward into the next year?" (4) "Is earned leave enc...
```

**`step_02_without_the_window(session)` — Twenty turns, with the window and without it / Do it: without the window**

Do it: without the window

Operation: bash — run in the operator shell, in the kit.

Expected shape, not a promised result:

```text
make window-check MODE=full: 20 turns of one conversation, offline, Rs 0
  the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
  the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
  every call is sent the whole thread, as the brains do today; the ceiling is the window's (the floor plus 2,000
  tokens of earlier turns), shown for comparison
  tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

          thread           the turn's largest call
  turn    msgs   tokens     context   ceiling     over the ceiling
     1       4      659         714     2,714            -
     2       8    1,309       1,364     2,705            -
     3      12    2,088       2,143     2,834            -
     4      16    2,792       2,847     2,759          +88
     5      20    3,301       3,356     2,564         +792
     6      24    3,446       3,530     2,229       +1,301
     7      28    4,221       4,277     2,831       +1,446
     8      32    4,883       4,938     2,717       +2,221
     9      36    5,785       5,840     2,957       +2,883
    10      40    6,682       6,737     2,952       +3,785
    11      44    7,573       7,628     2,946       +4,682
    12      48    8,397       8,452     2,879       +5,573
    13      52    9,374       9,430     3,033       +6,397
    14      56   10,274      10,329     2,955       +7,374
    15      60   10,907      10,962     2,688       +8,274
    16      64   11,764      11,819     2,912       +8,907
    17      68   12,399      12,455     2,691       +9,764
    18      72   13,364      13,420     3,021      +10,399
    19      76   14,033      14,088     2,724      +11,364
    20      80   14,858      14,913     2,880      +12,033

20 turns, 40 model calls, Rs 0 (a script, not a model). The thread holds 80 messages, 14,858 tokens: the checkpoint keeps every one.
Every call sent the whole thread. From turn 4 on, the largest call was over the ceiling the window would hold it to; the last call sent 14,913 tokens, 5.2 times its ceiling of 2,880.
```

**`step_03_change_it_a_smaller_budget(session)` — Twenty turns, with the window and without it / Change it: a smaller budget**

Give earlier turns a quarter of the room, 500 tokens, and run the same twenty turns. CHAT_HISTORY_TOKENS=500 in the environment does the same as HISTORY=500.

Operation: bash — run in the operator shell, in the kit (the Change-it).

Expected shape, not a promised result:

```text
make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0
  the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
  the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
  every call is sent the window: the system prompt and the turn it answers, whole, and at most 500 tokens
  of earlier turns (CHAT_HISTORY_TOKENS)
  tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

          thread           the turn's largest call     earlier turns              write rules
  turn    msgs   tokens     context   ceiling     kept whole  brought forward  cleared  masked  cut
     1       4      659         714     1,214              0                0        0       0    0
     2       8    1,309         854     1,205              1                0        1       0    0
     3      12    2,088       1,116     1,334              2                0        2       0    0
     4      16    2,792       1,199     1,259              3                0        3       0    0
     5      20    3,301       1,051     1,064              3                1        3       0    0
     6      24    4,245       1,485     1,497              3                2        3       1    0
     7      28    5,020       1,250     1,331              2                4        2       1    0
     8      32    5,682       1,134     1,217              2                5        2       1    0
     9      36    6,584       1,376     1,457              2                6        2       1    0
    10      40    7,481       1,440     1,452              2                7        2       0    1
    11      44    8,372       1,418     1,446              2                8        2       0    1
    12      48    9,196       1,363     1,379              2                9        2       1    1
    13      52   10,173       1,507     1,533              3                9        3       0    0
    14      56   11,073       1,433     1,455              2               11        2       0    1
    15      60   11,706       1,181     1,188              2               12        2       0    1
    16      64   12,563       1,406     1,412              2               13        2       0    1
    17      68   13,198       1,168     1,191              3               13        3       0    0
    18      72   14,163       1,497     1,521              3               14        3       0    0
    19      76   14,832       1,201     1,224              2               16        2       0    0
    20      80   15,657       1,361     1,380              2               17        2       0    0

20 turns, 40 model calls, Rs 0 (a script, not a model). The thread holds 80 messages, 15,657 tokens: the checkpoint keeps every one.
Every call's context was within its ceiling: yes. The last call sent 1,361 tokens, its ceiling 1,380:
  the system prompt (111) and turn 20 whole (769); 2 earlier turns kept whole, 2 results cleared; 17 brought forward in one line, 7 of their questions listed
  the whole thread would have been 15,712 tokens
  the line: [Earlier in this conversation, not shown here: turns 1 to 17. The person asked, in turns 11 to 17: (11) "After how many years of continuous service is gratuity payable?" (12) "Is gratuity payable to a contract employee?" (13) "...
```

### demo_06_full_against_windowed_with_gemini.py

Do it

**`step_01_full_against_windowed_with_gemini(session)` — Full against windowed, with Gemini / Do it**

Do it

Operation: bash — run on your own machine or the operator shell, in the kit (Gemini, billed to your project).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/full_vs_window.txt]
```

### demo_07_what_the_checkpoint_keeps.py

Do it

**`step_01_what_the_checkpoint_keeps(session)` — What the checkpoint keeps / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/thread.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.9_Working_Memory_WIX.html`. All 33 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `56fa31879a33efc1fa05ce81582f42396eff58e2`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
