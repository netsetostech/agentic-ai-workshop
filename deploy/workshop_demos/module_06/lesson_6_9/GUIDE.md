# Lesson 6.9: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.9_Working_Memory_WIX.html`, reviewed at blob `56fa31879a33efc1fa05ce81582f42396eff58e2`. Learners read that page on the course site; this guide keeps its prose.

A conversation's thread grows with every turn, and today every model call the chat brains make sends all of it again: every question, every answer, every search result. The kit's new window decides what one call is sent instead. The system prompt and the newest turn always go whole. Earlier turns go whole too, newest first, while they fit in 2,000 tokens, with their search results cleared. The rest are brought forward in one line that code writes. Every earlier question is masked and cut to the Desk's 300 characters. The chat service does not use the window yet. You watch a thread grow on your lane, run twenty scripted turns with and without the window at Rs 0, open one call message by message, and read the author's run of the same twenty questions against Gemini.

- Every call resends the thread, and the window that caps it

- The words: thread, turn, call, floor, budget, ceiling, compaction, the line, write rules

- Before you run anything: set up the shell

- On your lane today: every turn sends more

- The window in the kit, and one call opened up

- Twenty turns, with the window and without it

- Full against windowed, with Gemini

- What the checkpoint keeps

- Why the window is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn why a conversation's calls grow with its length, the rule that holds each call under a ceiling while the thread keeps growing, and the write rules for what an earlier turn may carry into a call. Then you will prove it: your lane's input tokens climbing turn by turn, every windowed call within its ceiling over twenty turns while the whole thread passes it, one call opened message by message, and Gemini's own counts for both.

### Every call resends the thread, and the window that caps it

The record and the call, the rule at every call, and what a call may carry.

The record and the call. The checkpointer keeps every message of a conversation, its thread, under a key of tenant, person and session (lessons 6.5 to 6.8). A model call is something else: the list of messages a brain sends Gemini for one step. Today the two are the same list. The LangGraph brain sends its system prompt and then the whole thread, and `create_agent` does the same for the LangChain brain. A turn that searches makes at least two calls, one that asks for the search and one that answers from it, and each sends every earlier question, answer and search result again. So each turn sends more than the one before. Over the twenty scripted turns of step 5, the forty calls send 285,188 tokens between them by the kit's estimate; with the window, 70,974.

No trim today. Nothing in the chat service trims, windows or summarises a conversation's thread. The budget lesson 3.4 teaches has a line for history, which rag-api's own `fit()` sets to 0 because rag-api keeps none, and its comment says what the chat service does instead: its agents "resend whole threads, untrimmed". Step 3 measures that on your lane.

The window. `services/chat/context_window.py` is new in the kit. At every model call it takes the messages the brain would send and decides, on a copy, what the call is sent. The floor always goes whole: the system prompt and the newest turn, which is the person's latest message and every call and result since. Earlier turns follow, newest first, each kept whole while the earlier turns fit in `CHAT_HISTORY_TOKENS`, 2,000 tokens by default, the history line of lesson 3.4's budget. A kept turn is compacted: each search result becomes a short "cleared" note and the call that asked for it stays, so no call is sent without a result. A refusal stays as it was, so the model still reads why. The turns that do not fit leave the call, and one line at the top of the first kept message brings them forward: which turns, and as many of their questions as still fit, each with its turn's number. Code writes that line, not a model, so it costs nothing and invents nothing. A call is therefore at most its floor plus the budget, its ceiling, however long the thread grows. And the window writes nothing back: the checkpoint keeps every message.

The write rules. What a call carries from earlier turns follows the Desk's rules for a person's words (lessons 5.6 and 10.4). Every earlier question, kept or listed in the line, is masked, a checked card number becoming `[card no.]` and an Aadhaar number `[Aadhaar]`, and then cut to 300 characters, the previous question the Desk keeps. The model's earlier answers are masked too. The newest question is masked and sent whole.

Not in the service yet. Nothing in the chat service imports the window, so every brain on your lane still sends the whole thread. A later change would put it in front of the brains' model, behind a switch that defaults to the whole thread. This lesson runs it where it is: in `make window-check`, offline at Rs 0, and in the author's run against Gemini.

A bank passbook. The passbook holds every entry since the account was opened: that is the checkpoint. When a page fills, nobody copies the whole book onto the next page. The next page opens with a B/F line, brought forward, printed by the machine, standing for everything before it, and the newest entries follow in full. However old the account, a page has the same number of lines. The window is that page: the newest turns in full, a fixed room, and one line at the top. The machine prints the line, not a clerk, so it never says anything the book does not hold. And the page shows only the last digits of the account number: what is carried forward is masked.

#### What one call is sent, turn by turn

Choose a turn of step 5's twenty-turn conversation and a budget for earlier turns. The top bar is what that turn's answering call sends today: the system prompt, every earlier turn as stored, and the newest turn. The bar below it, on the same scale, is what the window sends, with its ceiling marked in red. The columns show all twenty turns at the chosen budget: grey for the whole thread, teal for the window.

Every size is the kit's own, measured when this page was built on the thread step 5's windowed run wrote: each earlier turn as the window sends it, each question's room in the line, the floor, and the context `window()` returns at each budget. Which turns stay and which questions the line lists is `plan()`, the rule's arithmetic, ported to JavaScript and checked against the Python for all 120 pairs of turn and budget here, the line itself character for character. Tokens are the window's estimate, four characters a token and three a message.

It is the kit's rule over one scripted conversation, not your lane: your lane's brains send the whole thread, and step 3 measures what that costs. The tokens are langchain-core's estimate, which leaves out the tool declarations every call also carries (lesson 6.1 measures those). Step 6 puts Gemini's own count beside it.

### The words: thread, turn, call, floor, budget, ceiling, compaction, the line, write rules

Eleven rows, each with what it is in the kit.

One distinction to hold: the thread is the record, and the window is a view of it for one call. Masking and cutting change what a call reads, never what the record holds.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

The shell, in the kit's folder, with `PROJECT`, `REGION` and `ME`, and the DocuMind UI open and signed in as yourself for step 3. You need `~/graph-venv` from lesson 5.4 with the chat image's pins: step 4's first cell makes it if it is missing, as `make window-check` would, and installs the pins if they are not there. After that, steps 4 and 5 run on your machine, open no connection and need no credential. Step 6 calls Gemini from your machine and bills your project, so the page shows the author's recording and a shorter run you can choose. Step 7 reads your lane's checkpoint database and writes nothing. Your lane gains one conversation, step 3's.

### On your lane today: every turn sends more

Six questions in the UI, then the six chat rows they wrote.

#### Definition

In the DocuMind UI's Chat page, choose the `langchain` brain and ask these six questions, one at a time, in one conversation. They are the first six of `make window-check`'s twenty, so step 5 runs the same conversation offline. Each answer ends with a caption, and its last figure is what the turn cost in rupees.

- What is the notice period for an employee at grade E3?

- And during probation?

- How many days of earned leave can be carried forward into the next year?

- Is earned leave encashed when someone leaves the company?

- What is the cap on domestic travel reimbursement per trip?

- My corporate card 4111 1111 1111 1111 was charged twice for one flight. Who has to approve a travel claim above the cap?

The sixth carries a published test card number. On your lane the Desk's chat door masks it before any brain reads it (lesson 5.6); step 7 shows where it went. Then the cell reads the chat rows the chat service logged, one per turn: the model calls, `tokens_in`, the cached share of it, `tokens_out`, and the turn's two costs, the chat's own model calls and rag-api's answer behind each search. It saves the conversation's session id for step 7.

#### Do it

Every row is one turn of one conversation. The questions are short; what climbs is `tokens_in`, because each of a turn's calls carried every earlier question, answer and search result again, and the caption's rupees climbed with it. That is the kit's code, not a fault: the LangGraph brain sends its system prompt and then `state["messages"]` (step 4 quotes the line). The cached column is Gemini's own cache of a repeated beginning of a request, billed at a tenth of the input price (`shared/prices.py`); a thread resent whole is a long repeated beginning. Nothing on your lane changes this yet.

### The window in the kit, and one call opened up

Today's call, the rule in code, then turn 10's call as the model received it.

#### Definition

The excerpts come first: the line every LangGraph turn runs today, the budget line in rag-api, then the window's constants, `plan()`, the core of `window()`, how an earlier turn is compacted and its question carried, and `windowed()`, which puts the window in front of a brain's model. Then a cell runs the kit's own LangChain brain through ten of `make window-check`'s questions, its model behind the window. The budget is 600 tokens so the line appears early, and the search is a stand-in, so nothing but the window is measured. The model is lesson 6.8's script, which searches for the question and answers from the first passage; the cell keeps every list of messages it was sent. It prints what the checkpoint holds, then turn 10's answering call as the model received it, message by message.

#### The code: today

The system prompt, then every message of the thread, on every call. `create_agent`, the LangChain brain, does the same with its system prompt and the state's messages. rag-api's `TokenBudget` (lesson 3.4) has a line for a conversation's history, 2,000 tokens in its teaching split; the API's own `fit()` sets it to 0, because rag-api keeps no history, and the comment says what the chat service does instead:

#### The code: the window

`CLEARED` replaces an earlier search result: valid JSON, so the call that asked for it still has an answer, and a reason the model can act on. Besides it, the four `LINE_` strings are the only words the window writes into a call.

The whole rule's arithmetic, on whole numbers. If everything earlier fits, nothing is dropped and there is no line. Otherwise room is set aside for the line, earlier turns are kept newest first until one does not fit, and none older is kept after it, so a call never has a hole in its middle. What room is left lists the dropped turns' questions, newest first. A budget too small even for the line drops the turns without one. The widget in step 1 runs this function, ported.

`window()` splits off the system prompt, cuts the thread into turns, compacts every earlier turn, sizes each, and asks `plan()`. The kept turns and the newest go into the call, and the line is folded into the first kept message after the system prompt, a person's message, never the system prompt. The floor is measured before the line is added, so the line always counts against the budget.

An earlier question is masked first and cut second, the Desk's own order (step 7 quotes it), so a number that crosses the cut leaves no digit behind. An earlier search result becomes `CLEARED` unless it is a refusal. The model's earlier words are masked, never cut.

A chat model with the window in front of it. A brain is built with it as its model, so the brain, its graph, its middleware and its checkpointer stay the kit's own, and every call's report is kept.

#### Do it: the venv

#### Do it: one call, opened up

The checkpoint holds all 40 messages, and question 6's card number as it was typed: the cell drove the brain directly, not through the chat door, and the window writes nothing back. Yet not one of the 20 calls carried the number. Turn 10's call is 12 messages. First the system prompt. Then turn 8, its question with the line folded on top: turns 1 to 7 brought forward, their questions listed from turn 2, the sixth masked. Turns 8 and 9 are kept whole, each search result cleared to the short note. Last comes turn 10 whole, its search result in full, because that is what the call answers from.

Turn 9's question went in cut to 300 of its 395 characters, 79 tokens. Its call, 128 tokens, is bigger than the question beside it: the script searched with the whole question, and the window keeps a call as it was, so the pair is never broken. Turn 1's question did not fit in the line; the line's own numbers say so, turns 1 to 7 and questions from 2.

### Twenty turns, with the window and without it

make window-check three ways: the window, the whole thread, and a quarter of the budget.

#### Definition

`make window-check` runs twenty scripted questions in one conversation of the kit's LangChain brain, offline, on lesson 6.8's harness: a socket guard that refuses anything but your own machine, the script as the model, and every search answered by the Rs 0 lane over `evals/corpus`, BM25 on your CPU. After each turn it prints one row: the thread's messages and tokens, which is what the checkpoint holds, and for the turn's largest call the context it was sent and its ceiling. With the window it adds the earlier turns kept whole and brought forward, and the write rules' counts: results cleared, numbers masked, questions cut. `MODE=full` sends every call the whole thread, as the brains do today, and prints the same ceiling for comparison. `BRAIN=langgraph` drives the other brain and prints the same rows: the window sits in front of either brain's model.

#### The code

#### Do it: with the window

The thread grew from 659 tokens to 15,657, 80 messages: the checkpoint keeps every one. Every call stayed within its ceiling, and the last sent 2,862 tokens of 2,880. Up to turn 13 every earlier turn fitted in 2,000 tokens once its results were cleared, so nothing was brought forward. From turn 14 the oldest turns left the call, and the context stopped growing with the thread: by turn 20 it keeps turns 9 to 19 whole and brings turns 1 to 8 forward, listing 7 of their questions, turns 2 to 8. Turn 20 asks "What was the first question I asked you in this conversation?", and that call does not carry turn 1's question; the line's numbers tell the model so. The masked column turns 1 at turn 6, the card number, and the cut column at turn 10, when turn 9's question of 395 characters became an earlier turn.

Each search runs on your machine. The Rs 0 lane counts each chunk's words once and keeps the counts, so a search takes a fraction of a second, turn 9's question of 395 characters included. A search that passed `retrieve`'s budget of 25 seconds (`RAG_TIMEOUT_S` plus 5, lesson 5.5) would be cut: the model would read a failed search, the script would answer that the search found nothing, and that turn's row and every thread size after it would come out smaller, with a `retrieve took ... (budget 25s)` warning naming the search. The window would still hold every call within its ceiling.

#### Do it: without the window

Every call sent the whole thread. The largest call passed the window's ceiling at turn 4, and turn 20's sent 14,913 tokens, 5.2 times its ceiling of 2,880. This is your lane's behaviour, measured the same way as the window.

From turn 6 the thread column is 799 tokens smaller than with the window, for a reason that is the script's: it searches with the newest question word for word. Here that search carried the card number's digits, words no passage holds, so the Rs 0 lane's evidence gate, which wants half of the question's information covered, returned nothing, and the turn stored a search that found nothing. With the window the model read `[card no.]` instead, searched for that, and found `EXP-12`, the travel reimbursement clause. The mask changed what the model searched for. Every other answer is the same in both runs.

#### Change it: a smaller budget

Give earlier turns a quarter of the room, 500 tokens, and run the same twenty turns. `CHAT_HISTORY_TOKENS=500` in the environment does the same as `HISTORY=500`.

Every ceiling fell by 1,500 tokens, and every call stayed within its own. The line appears at turn 5, and from then on only 2 or 3 earlier turns stay whole; by turn 20, 17 are brought forward. Turn 19 asks "Summarise what you told me about the notice period and probation.", about turns 1 and 2. At 500 tokens that call carries neither their answers nor their questions; at 2,000 it carried their questions in the line. The model has to search again, which the kit's system prompt asks for on every follow-up anyway. A smaller budget is cheaper on every call and remembers less.

### Full against windowed, with Gemini

The author's run: the same twenty questions, two conversations each, Gemini's own counts.

#### Definition

`make window-check LIVE=1` asks each question in two fresh conversations of the same brain, one sent the whole thread and one the window, with gemini-3.6-flash on location `global` from your machine. The searches stay on the Rs 0 lane, so both conversations read the same passages and only Gemini is billed, at list price, by each turn's Meter (lesson 5.5). Per turn and conversation it prints Gemini's own input, cached and output tokens, the window's estimate for the same calls, the rupees, the start of the answer and the sources it cites; then the totals. This is the first time the folded line and the cleared results reach a real model: the run shows whether Gemini takes them, and what the window costs in answers.

By the window's estimate of step 5's runs, two calls a turn in each conversation, twenty turns send 356,162 tokens of input, about Rs 45 at list price before the tool declarations, the answers and any caching; the kit's builder put the whole run at about Rs 80 before caching. `TURNS=12` sends 128,346 tokens by the same estimate (Rs 16 of input), and `TURNS=6` sends 34,658 (Rs 4.4), if you want to see it on your own project for less.

#### Do it

#### What to read in it

- `in`, turn by turn. The full conversation's input climbs with every turn; the windowed one's levels off once turns start leaving the call.

- `cached`. Gemini caches a repeated beginning of a request on its own. The whole thread repeats a longer beginning on every call, while the window changes its first kept message each time a turn leaves. Read the rupees as well as the tokens.

- `sources`. "the same as full" when both conversations cited the same passages for a turn.

- turn 20. "What was the first question I asked you in this conversation?" The full conversation has turn 1 in every call. The windowed one has what its line lists, and in step 5 the line no longer listed turn 1 by turn 20.

The recording's totals say how much input and how many rupees the window saved in that run. The ceiling holds the window's estimate, not Gemini's count: the "in" column is Gemini's own, and it also counts the tool declarations the estimate leaves out. A turn that reaches the chat service's limits (lesson 5.5: Rs 5 and twelve model calls a turn) answers with the stop sentence instead; the full conversation is the one whose turns grow towards the rupee limit.

### What the checkpoint keeps

Step 3's conversation, read back from your lane's Cloud SQL.

#### Definition

`make thread`, lesson 6.8's reader, decodes the conversation step 3 wrote from your lane's checkpoint database, a row per checkpoint, in a session that cannot write. Each row shows the step, its source, the brain that wrote it, the node that runs next, how many messages the thread held then, and the newest message.

#### Do it

Six turns, every message kept: at its last step the thread holds every question, call, result and answer step 3 wrote, four messages a turn when Gemini searched once. That whole list is what each call on your lane sends today, and what the window would leave untouched while it sends less. Question 6 is stored as `My corporate card [card no.] was charged twice ...`: the chat door masked the number before the brain read it, so neither the model, the search nor the checkpoint saw it.

The window applies the same rule again at every call, to whatever an earlier turn holds. That matters wherever a number got into a thread: a tenant whose `desk_gate` is off, so that its door passes the question as typed, or a brain driven directly, as `make window-check` and step 4's cell drive it. A Desk thread applies the rule when it writes, as the third excerpt shows.

#### The code: the rule where it is written

### Why the window is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own code and comments, then the bill and the gaps.

- Whole turns, newest first. A turn runs from a person's message to the next, and a call and its result always share one; a result whose call sits in an earlier turn joins the turns between into one. So keeping or dropping whole turns never splits a pair, and no call reaches the model without the result the thread holds for it. Nothing older than a dropped turn is kept, so a call has no hole in its middle.

- The newest turn is never cut. The question being answered is the one thing a call cannot lose, and Gemini 3 needs the thought signatures of the turn in progress, so the newest turn's model messages and results go as they are. A newest turn bigger than the budget still goes whole: the floor is not part of the budget.

- A line written by code, not a summary. The line costs no call and states nothing the thread does not hold: which turns left, and the questions asked in them, each with its number, so the model can tell the first question from the first one listed. It rides in a person's message, never in the system prompt, because the questions are the person's words.

- Clearing alone does not cap a call. langchain's own `ClearToolUsesEdit`, set to work from the first call and keep the newest three results, still sends 4,912 tokens at turn 20 of step 5's thread, against the window's 2,862, and it grows by about 148 tokens a turn from turn 10: it keeps every question, call and answer. Dropping whole turns is what holds a ceiling. (The build ran it on the same calls.)

- A copy, never the record. `windowed()` wraps the model and `middleware()` is `create_agent`'s `wrap_model_call`. Neither adds a graph node, so a turn writes the checkpoints it wrote before (lesson 6.6's three and five) and `make thread` still lists every message. The kit's tests check it for both forms.

- 2,000 tokens. The budget is the history line of rag-api's `TokenBudget` (lesson 3.4), the figure the kit had already named for a conversation's history.

- An estimate, not Gemini's count. The window counts with langchain-core's `count_tokens_approximately`, four characters a token and three a message, the counter `trim_messages` and LangChain's context-editing middleware also default to. Step 6 prints Gemini's own count beside it.

The kit's docstring says what it does not use, and why:

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The window is not in the service. No brain, route or switch reaches `context_window.py`, and on your lane every brain sends the whole thread on every call, as step 3 measured. A later change would put it in front of the model, behind a switch that defaults to the whole thread.

- Nothing bounds the thread itself. The checkpoint keeps every message of every conversation, and every version of the list (lesson 6.6). Retention and erasure, and memory that lasts from one conversation to the next, come later too.

- The ADK brain and the Desk are out of reach. The ADK brain keeps its own sessions, and ADK's own compaction is marked experimental in google-adk 2.8.0. The Desk sends its models the turn's masked question, never the thread.

- The ceiling is the estimate's. Tool declarations and Gemini's own tokenizer are outside the window's count, so a call's real input is above the figure the window holds under its ceiling.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it.

One conversation: step 3's six turns are in the checkpoint tables and the chat service's log, and their rupees on your bill. Nothing else. `make window-check` and step 4's cell ran on your machine, and step 7 read without writing. If you ran step 6, it billed Gemini in your project and touched no lane service. `~/graph-venv` has the chat image's pins, and `~/lesson69-session.txt` holds step 3's session id. Lesson 7.1 starts Module 7: graph evidence built from the source documents.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.9 Budget working memory: windowing, compaction and write rules · v5.0

Next: Lesson 7.1 Build graph evidence from source documents.
