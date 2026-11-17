# Lesson 10.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.2_Plan_Execute_WIX.html`, reviewed at blob `b3a4b9903a0ae5b157cb81ed938589e65ff1cfda`. Learners read that page on the course site; this guide keeps its prose.

An exit's full and final settlement asks three figures at once: when the notice ends, how many leave days are encashed, and the gratuity. Each is a search for its clause, then a calculator. Lesson 10.1's loop decides each call after reading the last result. Plan-and-execute writes the whole plan first, lets code carry it out a step at a time, and replans once when a step is refused. ReWOO writes every step at once, with placeholders for results not yet known, and code runs them in waves with no model call between the tools. You run all three on the agent bench's 3 chained rows, offline and on your lane, with correctness, calls and rupees by role for each. You watch a manager's cap that is not the handbook's force a replan, you put the executor on a model a sixth of the input price, and you switch the replan off to see what it was worth.

- Three figures, three ways to order the work

- The words: planner, executor, step, replan, solver, placeholder, wave, extract, role

- Before you run anything: set up the shell

- The Chat page: three figures from a loop

- Plan-and-execute: a plan, an executor, one replan, offline

- ReWOO: one plan with placeholders, checked and run in waves, offline

- Change it: switch the replan off

- The 3 chained rows offline, and a cheaper executor

- Your lane: plan-and-execute, ReWOO and a flash-lite executor

- The 3 rows on your lane, and the plans they saved

- When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn when an agent should write its plan first and let code carry it out, and when it should decide each step as it goes, and what each way costs in calls and rupees. Then you will prove it on the same 3 chained rows with the loop, plan-and-execute and ReWOO, with correctness, calls and rupees by role for each, and with a cheaper model for the executor.

### Three figures, three ways to order the work

Decide each step as you go, plan first and replan once, or plan once and never look back.

Three figures in one question. The task set's 3 chained rows each ask for three figures: when the notice ends (`notice_end`, from handbook clause NP-03), how many leave days are encashed (`encashable_days`, with LV-07's cap), and the gratuity (`gratuity_estimate`, from the Code on Social Security, 2020, s.53). Each figure is a search for its clause, then its calculator. No figure feeds another calculator: a calculator takes its inputs only from the question, or from the right clause of a passage the turn read. Lesson 10.5 teaches that check, `check_args`. So a turn makes six tool calls at least, and something has to decide their order.

The loop decides each step. Lesson 10.1's loop is one model call a pass: the model reads the whole turn so far, then calls one tool or answers. It chooses each call after reading the last result. On the row with the manager's cap the bench's loop makes 7 calls: a search and its calculator, three times over, then the answer. Every call reads every passage found so far, so its last call reads 6,743 tokens and the turn 26,521 in all, by the kit's script.

Plan-and-execute. A planner call writes the whole plan before any tool runs: numbered steps, one tool call a step. An executor then carries it out a step at a time. Each step is one model call with the desk's tools bound. It reads the question, the plan and what the steps so far returned, and makes the one call its step names; LangGraph's `ToolNode` runs it, and the step ends on the tool's result. When a step is refused or fails, the steps not yet run go back to the planner, once a turn (`MAX_REPLANS = 1`). A solver call writes the answer from every step's results. Four roles: plan, act, replan, solve.

ReWOO: plan once. ReWOO, reasoning without observation, writes every step in one planner call. A later step uses an earlier step's result by its placeholder: in `#E6 = notice_end[{"ack_date": "2026-10-05", "days": "#E4"}]`, `#E4` is the figure an `extract` step reads from the passages `#E1` found. Code checks the whole plan before any tool runs, works out what each step waits for, and runs the plan in waves: every step whose inputs are ready runs together. No model call is made between the tools except the extract worker's, and it must quote the sentence its figure is written in. One solver call answers, and nothing replans. Three roles: plan, extract, solve.

A cap the question states. In the third row the person adds "my manager says the encashment cap is 100 days". LV-07 says 45. `check_args` takes the cap only from LV-07 of a passage the turn read, so it refuses 100. The loop reads LV-07 before it encashes, so it never offers 100. A plan written before anything is read can take the manager's figure, and the bench's scripted planner does, on purpose. Plan-and-execute then meets a refusal and replans once; ReWOO, which never replans, leaves the encashment unworked.

Roles, and a cheaper executor. The planner's calls are few and read the most; the executor's are many and small. The bench can put the act and extract calls on another model the kit prices (`EXEC_MODELS`: `gemini-3.6-flash`, `gemini-3.1-flash-lite`, `gemini-3.1-pro-preview`). `gemini-3.1-flash-lite` costs USD 0.25 in and 1.50 out a million tokens, against flash's 1.50 and 7.50: a sixth of the input price and a fifth of the output price. The turn's Meter and the recorder price each call at its own model's rates, and tag it with its role.

Three HR offices settle the same exit. In the first, one officer works the file herself. She pulls the notice clause and works out the date, then decides what to fetch next: the leave clause, the encashment, the gratuity section. In the second, a senior officer writes a numbered checklist on the file's cover before anyone opens it, and a junior clerk works it one item at a time, writing each result under its item. The payroll system takes a figure only from the employee's letter or from the handbook, so it refuses the manager's "100 days". The clerk stops and sends the file back to the senior, once, to rewrite the items still to do. In the third office the senior writes every item at once, with blanks to fill such as "the cap from item 2's clause", and goes home. The clerks do every item that waits on nothing at the same time, and a reader copies each figure off its clause and must quote the sentence. Nobody rewrites that list, so a refused item stays undone. In all three offices the senior's hour costs more than a clerk's.

#### One question, three ways

Choose a chained row and the executor's model, then step through the three turns one card at a time. A card is one model call and what code did with it, or one wave of tools that code runs with no model call at all. The strip under each name is the turn's model calls, one letter a role: L the loop, P plan, A act, E extract, R replan, S solve. The row with the manager's cap comes first.

Every card is the kit's own turn, run when this page was built: each row's scripted models, the ones `make agent-turn OFFLINE=1` uses, over the kit's own corpus. The token counts are the script's: four characters a token, and 64 thinking tokens a call at `low`. The flash-lite executor changes no step and no token, only what the act and extract calls cost. Steps 8 and 9 show your lane's own counts.

The scripted planner writes the same plan every time, and takes the manager's cap on purpose. On your lane Gemini writes its own. It may search LV-07 first, so that no step is refused and no replan shows; it may write a plan code cannot read, which plan-and-execute counts as a failed step and ReWOO refuses; its extract worker may paraphrase where it must quote. What does not change is who does what: the planner writes the steps, code runs and checks them, a calculator works out every figure, and the turn's one Meter counts every role's calls against 12 calls and Rs 5.

### The words: planner, executor, step, replan, solver, placeholder, wave, extract, role

Eighteen rows, each with the value it takes on your lane.

One distinction to hold: in the loop the model decides every call, and in the two planning patterns the model writes the plan while code decides what runs, when, and whether a plan is fit to run at all.

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

The shell, in the kit, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok` from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first `make agent-turn` or `make agent-eval` builds `~/graph-venv` with the chat image's pins (lessons 5.4 and 10.1 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call `gemini-3.6-flash` and `gemini-3.1-flash-lite` on location `global`, and rag-api's `/v1/passages` as `documind-ui-sa`. Step 10's ADK planner runs offline in the same venv, and once, optionally, on the chat service after a redeploy.

The bench's desk searches by class and drops every passage that has none (`services/chat/desk_agent.py`, `_search()`). Lesson 10.1's setup line gave acme's stored rows their classes. If you have not run it, run this now: every chained row is acme's. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

### The Chat page: three figures from a loop

The row with the manager's cap, asked of the deployed langchain brain.

#### Definition

Open the DocuMind UI and its Chat page, choose `langchain` in the sidebar's Brain list, and ask the question below, the third chained row's. Under the answer, the caption names the brain, each tool call the turn made in order, the time it took and the turn's rupees.

I am a confirmed E3 employee at ACME on Rs 52,000 a month with 7 years 8 months of continuous service. My resignation was acknowledged in writing on 5 October 2026. I have 80 days of earned leave, and my manager says the encashment cap is 100 days. When does my notice end, how many leave days are encashed, and roughly what gratuity will I get?

The `langchain` brain is lesson 5.1's loop, on the same model as the bench. It decided each call after reading the last, and the caption's tool list is those calls in order. Its tools are `retrieve` and `calculate_processing_cost` (`services/chat/tools.py`): no calculator, and so no `check_args`. Every figure in its answer is the model's own, and nothing in the chat brain checks which cap it used, LV-07's 45 or the manager's 100.

The calculators' figures for this row are 4 December 2026, 45 days and Rs 2,40,000 (step 7's check prints them). Hold the brain's answer against them. The rest of the lesson runs the same question through agents whose figures come from those calculators, and changes only who decides the order of the work.

### Plan-and-execute: a plan, an executor, one replan, offline

The loop and plan_execute on the row with the manager's cap, at Rs 0.

#### Definition

`plan_execute` is a LangGraph `StateGraph` on the turn's context with six nodes: plan, act, tools, step, replan and solve. `plan` sends the question under the desk's own prompt, `PLANNER` and the tools' declarations written as text, and binds no tool; `read_plan()` keeps each numbered line of the reply as a step. Gemini 3 sometimes tries to call one of those declared tools anyway, and with none bound the reply comes back holding nothing (the call's record says `finish` `UNEXPECTED_TOOL_CALL`), its tokens billed: `_ask()` then asks once more, adding that no tool can run in this call, so the empty reply costs one call, not the plan. `act` sends the executor the question, the plan, each step done with what it returned, and the step to carry out (`EXECUTOR`), with the desk's 8 tools bound. `tools` is the `ToolNode` with the brains' timed wrapper that lesson 10.1's `react_text` uses, so `check_args`, the ledger and the tools' budgets are the Desk's own. `step` reads what came back in `said_of()`'s three words. A refused or failed step sends the turn to `replan`, at most `MAX_REPLANS` times a turn; its numbered reply replaces the steps not yet run, and a later refusal is kept. `solve` answers from every step's results, binding no tool.

What each call reads is chosen in code. The executor and the replanner read a search's handbook passages whole and its statute and guidance passages by name only (`by_name()`): no calculator takes a figure from a Code's text, so that text would only be read again at every step. The solver reads every passage whole, once.

#### The code

#### Do it: the loop on the same row, first

For comparison, the loop on the row with the manager's cap. The filter keeps each model call, the tool it asked for, each calculator's result or refusal, and the totals.

#### Do it: plan-and-execute on the same row

The loop searched NP-03 and worked the date, then searched LV-07, and only then encashed, with `cap=45`, LV-07's own. It never offered the manager's 100, because it chose that call after reading the clause.

The planner wrote five steps before anything was read, and step 3 took the cap the question states, `cap=100`. `check_args` refused it: "cap = 100 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". The replan read that sentence and wrote the work still to do: search LV-07, then encash with "the cap LV-07 states", which the executor filled with 45 once the passage was in. The gratuity's search and calculator then ran as first planned. 10 calls by role: plan 1, act 7, replan 1, solve 1.

That is 10 calls against the loop's 7, and Rs 3.0377 against Rs 3.7474: more calls, fewer tokens, 18,800 read against 26,521. Each act call read between 579 and 1,674 tokens, the plan and the steps done with the Codes' passages by name. Each of the loop's calls read every passage found so far, whole, and its last read 6,743. The solver is plan-and-execute's one big call: 7,091 tokens, Rs 0.9653. These are the script's counts. On your lane every loop call and every act call also carries the 8 tools' declarations, about 1,131 tokens a call, which the script does not count.

### ReWOO: one plan with placeholders, checked and run in waves, offline

The plan's readers on their own, then rewoo on a chained row, at Rs 0.

#### Definition

`rewoo` is a `StateGraph` of plan, wave, tools, collect and solve. `plan` sends the question under the desk's prompt, `REWOO_PLANNER` and the tools' declarations with `extract`'s. `read_rewoo()` reads each line written `#E = []` as a step. `check_rewoo()` refuses the plan before any tool runs when it has no step; more steps than the turn's 12 calls, since its tools run with no call between them and the Meter would not bound them; a tool the desk does not hold; arguments that are not one JSON object; a placeholder naming a step not written above it; an extract that reads no search; or a search's placeholder where a figure goes. A refused plan goes straight to the solver, which says why.

`needs()` gives what each step waits for: the steps its placeholders name, and, for a calculator, every search written above it, because a calculator reads the turn's passages. `next_wave()` picks every step that is ready. A wave's tool calls go on one `AIMessage` that code builds and never sends to a model, so `ToolNode` runs them side by side, as it runs one model message's calls. Its extract steps are executor calls, one after another, each sent the passages its search found (`EXTRACTOR`). `resolve()` fills each placeholder with its step's value, and `check_args` still checks every calculator's arguments, so a figure only the plan wrote is refused. A step whose placeholder's step was refused, failed or never ran never runs.

#### The code

The kit's own test proves the side by side without a clock: each search waits at a barrier the three must reach together, so searches run one after another would break it. `make agent-tests` runs it with the rest of the bench's tests.

#### Do it: the plan's readers, at Rs 0

These functions need no framework and no model: `agent_patterns.py` imports only the standard library and the kit's `shared/` at the top, so the shell's own Python runs them. The cell reads the plan the scripted planner writes for `chained-exit-e3` and prints what each step waits for and the waves. Then it prints what a refused value stops, four plans `check_rewoo()` refuses, one placeholder filled, and an extract worker's figure held to its quote twice.

The plan passed the check. The three searches wait on nothing, so they run first. Each extract waits for its own search only. Each calculator also waits for every search above it, so the gratuity (`#E8`), which takes no placeholder, runs in wave 2 beside the extracts, and the date and the encashment run in wave 3 once their figures are read. Had the cap's extract (`#E5`) been refused, `#E6` would still run, and `#E7`, which needs `#E5`, never would.

Each bad plan is refused before a tool runs, in words the solver can pass on. The thirteen-step plan is refused for its length alone: a plan written once runs its tools with no model call between them, so the Meter's 12-call cap could not stop it once it started. The worker's second reply has the right figure and is refused all the same, because its quote is not in the passage: code checks the quote, not the worker's word.

#### Do it: ReWOO on a chained row

Offline, the corpus is ranked in Python, and a wave's searches share one interpreter: three cold searches side by side can outlast a search's budget, 25 seconds by default, and come back failed, as a slow rag-api's would. The kit's own docstring warns of it. `RAG_TIMEOUT_S=90`, the value the chat service is deployed with, gives them room.

The turn made 4 calls, the plan, two extracts and the answer, against the loop's 7. Wave 1 ran the three searches together; wave 2 the two extracts and the gratuity; wave 3 the date and the encashment, their placeholders filled: `run as notice_end(ack_date="2026-10-05", days=60)`. Each extract quoted its clause's sentence, and code found the quote in the passages. Rs 1.9182, of which the extracts were Rs 0.5628.

Your passage numbers may differ from the page's. A wave's searches finish in any order, and the first one back takes passages [1] to [5]. When this page was built every search had been ranked already, and they came back in the order written. On your first run each search ranks the corpus, and which finishes first is up to your machine. The steps, the waves, the figures and the calls do not change: the build runs the same turn cold, as yours does, and checks them. A passage numbered [10] where the page has [5] is one more character in an extract's input, so ReWOO's rupees can differ from the page's in the fourth decimal, here and in step 7's eval.

The panel in step 1 shows the row with the manager's cap. There the plan writes `encashable_days[{"balance": 80, "cap": 100}]` and no search for LV-07. `check_args` refuses it in wave 2, nothing replans, and the answer says the encashment was not worked out: 3 calls, Rs 1.4606, not correct.

### Change it: switch the replan off

MAX_REPLANS from 1 to 0, the same turn, then the line put back.

#### Definition

The replan hangs on one line: `onward()` sends a failed step to `replan` only while `state["replans"] < MAX_REPLANS`. Set the constant to 0 and a refusal is kept: the next step runs, and the solver answers from what was done. The kit has no switch for it (step 10 lists what it lacks), so you edit the line, run the same turn, and put the file back. The filter drops the passage lists and code's "Worked out in code" lines.

#### Do it: no replan

#### Put it back

With no replan, step 3's refusal stood. The executor went on with the steps as first planned, the gratuity's search and calculator, and the solver wrote the encashment as not worked out, citing [1], since no passage of LV-07 was ever read. The turn made 7 calls for Rs 1.9394, against 10 calls and Rs 3.0377 with the replan: the replan, the LV-07 search and the encashment again cost three calls, and turned a refusal into LV-07's 45. Without it, plan-and-execute ends on this row where ReWOO does. `git checkout` put the line back, and `grep -c` finds it once.

### The 3 chained rows offline, and a cheaper executor

The chained slice through the three patterns at Rs 0, the two planning patterns on flash-lite, and the saved runs read back.

#### Definition

The chained slice is the three rows below. `CHECK=1` recomputes every part's figure with `desk_calc`, checks that the hard gate lets each question through, and that `check_args` refuses the stated cap. `score()` scores each part as a calculator row: a run is correct when every part's figure is stated and no part's wrong figure is, and has its provenance when every part's calculator returned its figure and the figure check finds nothing unsupported. A chained row never slips: the script's one-run-in-five slip is for calculator rows only. `EXEC_MODEL=` runs plan_execute and rewoo once for each executor it names, and each of their arms adds a line of calls and rupees a run by role, and one of how its plans went.

#### The code

#### Do it: check the rows, then run them

#### Do it: a flash-lite executor

#### Do it: the saved runs, read back

Each saved run is one JSON line: `make agent-turn`'s record of the turn, with its plan and its roles. The cell prints each run's calls and rupees by role, and what its plan did: a replan and why, or the waves.

On the three rows, offline: the loop was correct on all three, at 7.0 calls and Rs 3.7404 a run. Plan-and-execute was correct on all three, at 8.7 calls and Rs 2.6420, with one replan, for the stated cap. ReWOO was correct on two, at 3.7 calls and Rs 1.7657, the stated cap left unworked. These are the script's plans and the script's tokens. They show what each pattern does with the same plan, not which one a real model plans better.

The flash-lite executor changed no step and no answer. It cut plan-and-execute's act calls from Rs 1.2172 a run to Rs 0.2136, and ReWOO's extracts from Rs 0.4820 to Rs 0.0835, so a run cost Rs 1.6383 and Rs 1.3673. The plan and the answer stay on flash, and they are most of what is left: the solver's one call reads every passage.

Two arms in one run print a paired comparison, and the kit's verdict on three rows is the honest one: no conclusion. One row split the two patterns, and the interval runs from -79.2 to +29.1 points, across the 3-point margin on both sides. No pattern wins here: the rows show what each costs, and where each breaks.

### Your lane: plan-and-execute, ReWOO and a flash-lite executor

Three live turns of the bench on Gemini and your lane's rag-api.

#### Definition

Without `OFFLINE=1`, `make agent-turn` needs `PROJECT`, and `commands/agent-turn.sh` exports what a live turn needs: the project for Gemini, rag-api's address, built from `REGION` (pass yours: the Makefile's default is `us-central1`), and `documind-ui-sa` as the account rag-api's ID token is minted as. `gemini()` builds the planner as the chat service builds the Desk agent's model, `gemini-3.6-flash` on location `global` at thinking `low`. With `EXEC_MODEL`, the executor is the same client on another model of `EXEC_MODELS`, at the same thinking level, timeout and attempts. Every search is one POST to `/v1/passages`, the call lesson 10.1 showed: no model call, and rag-api books it with no tokens and no cost. Each turn runs under the chat service's limits, 12 calls and Rs 5 for every role together. By the kit's own count the three turns below cost about Rs 3.64, Rs 1.76 and Rs 1.51 before thinking; step 10 shows how that count is made.

#### Do it: plan-and-execute on the manager's cap

The plan is Gemini's own, so read it first. If a step took the manager's 100, that step is refused, and the replan follows with `after: Step N was refused: ...`. If the planner put LV-07's search first, no step is refused and the totals say `plans: 1 written, 0 replans`: the plan was right the first time, and the turn proves nothing about replanning. A planner reply that came back empty is asked once more, and the totals count that call; a plan the reader still cannot parse shows `the plan: no numbered step`, counts as a failed step, and is replanned. And a turn the limits stopped ends `stopped by turn_budget` or `model_calls`, with the Meter's answer in place of one.

#### Do it: ReWOO on a chained row

Read the plan and its check first: `#E` lines the reader took, and either the waves or `refused before any tool ran: ...` with the reason. Then each extract: `= 60, quoting "..."` means code found the worker's quote in the passages, and `refused: its quote is not written in the passages it was given` means the worker paraphrased, and the step it fed never ran. A search cut at its budget prints `failed:`, and the steps that take its passages never run.

#### Do it: a flash-lite executor

The act calls name `gemini-3.1-flash-lite`, and the by-role line prices them at its rates. Whether `gemini-3.1-flash-lite` takes thinking `low` on location `global` is your lane's fact: if it does not, the turn prints `the turn failed: ...` and make's error line in place of the steps.

Three real turns, each priced call by call at its own model's rates, each call tagged with its role. Everything the scripted planner did on purpose, Gemini did or did not do on its own: which cap its plan took, whether its plan parsed, whether its worker quoted exactly. The kit's side held either way: `check_args` took no figure the question or a clause did not write, the plan check ran before any tool, and the Meter counted every role's calls in one turn.

### The 3 rows on your lane, and the plans they saved

15 live turns, then two reads at Rs 0: the saved runs rescored, and their plans read back.

#### Definition

The same two commands as step 7 without `OFFLINE=1`: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

This is the lesson's proof: the loop, plan-and-execute and ReWOO on the same 3 chained rows, each with correct, provenance and verified, its calls, tokens and rupees a run and, for the two planning patterns, its calls and rupees by role; then the same two with a flash-lite executor. For any row a pattern got wrong, the why column says how. Three model-written rows, one run each, cannot rank three patterns, and the kit says so: every comparison is indicative, and none of the three is named the winner.

#### Do it: rescore the saved runs, at Rs 0

#### Do it: read the plans back, at Rs 0

The same cell as step 7, on your lane's saved runs.

A `replanned after:` line names the step Gemini's plan got wrong and why. Waves other than the script's mean the planner ordered its steps another way; a `refused before any tool ran:` line means its plan never ran at all.

### When a plan pays, what each costs, the libraries' forms, and what the kit does not do yet

Choosing between the three, the bill for each run, LangChain's to-do list, ADK's planner on the ADK brain, and the gaps.

#### When a plan pays

- Decide each step when the next call depends on what the last one read. The loop read LV-07 before it encashed, so the manager's figure never reached a calculator. It pays by rereading the whole turn on every call: its last call read 6,743 tokens offline.

- Plan first when the steps are known before anything is read. The executor's calls are many and small, which makes them the place for a cheaper model, and each reads only the plan and the steps done. One replan buys back one wrong step; without it, the refusal stands (step 6).

- Plan once when the steps and what each needs are fixed, and the tools are slow. ReWOO makes the fewest model calls and runs a wave's searches side by side, and code checks the whole plan before anything runs. It cannot recover: whatever its plan got wrong stays wrong.

- No plan brings a number of its own. In every pattern a figure is a calculator's, and `check_args` reads the person's question, never the plan's step: the manager's 100 was refused in a plan exactly as it would be in a loop that offered it.

- What can steer the tools. In ReWOO every tool call is chosen before any passage is read, and the one call that reads passages before the answer, the extract worker, can return only a figure written in its quote. In plan-and-execute the executor and the replanner read handbook passages before they choose a call's arguments. Lesson 10.8 takes injected documents up.

- The far end of planning first. Lesson 10.4's routed Desk chooses the desk for a question with rules and a classifier before any agent runs, and lesson 10.1's `plan_first` is the near end: a plan the model writes and nothing runs.

#### What it costs

"Before thinking" is the input and visible tokens the kit's script counts for these very turns, plus the tool declarations Gemini receives with every loop and act call, about 1,131 tokens, each call priced at its own model's rates (USD 1.50 and 7.50 a million on flash, 0.25 and 1.50 on flash-lite) at Rs 85 to the dollar. Thinking is billed as output, Rs 0.6375 for every 1,000 tokens on flash and Rs 0.1275 on flash-lite, and only your lane knows how much a call spends. One more limit to know: a plan-and-execute turn on a chained row reaches Rs 5 before its last call when its calls think about 398 tokens each, and a loop turn at about 406; the Meter then stops it, and the turn prints `stopped by turn_budget`. Lesson 10.1's four thinking levels tell you your model's figure first.

#### LangChain's form

LangChain, at the chat image's pin (langchain 1.4.0), ships `TodoListMiddleware`. It gives an agent a `write_todos` tool and a `todos` list in its state, each item `pending`, `in_progress` or `completed`; the model writes the whole list and rewrites it as it works, and the middleware refuses two `write_todos` calls in one reply. It is a plan the model keeps, between lesson 10.1's `plan_first` and this lesson's patterns: kept in state rather than in the prompt, and still never run by code, since the loop decides every call. The kit uses it nowhere. Both of this lesson's patterns are built from LangGraph's own parts, `StateGraph` and `ToolNode` (langgraph 1.2.12).

#### ADK's form, on the ADK brain behind a switch

ADK, at the chat image's pin (google-adk 2.8.0), has a plan-first form of its own, `PlanReActPlanner`. Set on an agent, it adds an instruction to every model request, about 768 tokens (Rs 0.10 a call at flash's input rate): write a numbered plan under `/*PLANNING*/`, reason between tool calls under `/*REASONING*/`, revise the plan under `/*REPLANNING*/`, and answer under `/*FINAL_ANSWER*/`. The model's tool calls stay function calls, everything before the final answer comes back marked as thought, and ADK sends the plan back as plain text with every later call of the turn. It sits beside this lesson's patterns, not among them: the plan is written down and kept, but no code runs it, and the model still decides each call, as the loop does. The kit's ADK brain takes it behind one switch, `ADK_PLANNER`, off unless it says `plan_react`:

The planner is set on the agent after it is built, so the constructor lessons 5.7 and 6.1 show is unchanged: ADK's flow reads `root.planner` on every model request, and `LlmAgent`'s pydantic config lets the field be assigned (`commands/tests/test_adk_planner.py` checks both on the pinned ADK). The other half is the answer, which is the text not marked thought: a plan or a line of reasoning never reaches it, and a reply that was all plan says so instead of answering nothing.

Offline, at Rs 0: the kit's own ADK brain with the switch on, on a scripted model, with the search stood in. The plan is stored marked as thought, goes back to the model as plain text with the next call, and stays out of the answer.

On your lane the switch needs the chat service's image to carry this kit, so the run starts with a redeploy (Cloud Build, no model call). It then asks the ADK brain the same question with the switch off and on, and takes the switch off again whatever happens. It is optional for you, at most Rs 10 (two turns, each stopped at the chat service's Rs 5); the author's run is below. It shows what the script cannot: whether Gemini still calls `retrieve` as a function when the instruction asks for tool code under `/*ACTION*/`, and what a written plan adds to a turn's calls and rupees.

Each point is checked in the kit's code or the pinned library, and the build asserts it, so this box changes when they do.

- The comparison is indicative. The 3 chained rows were written with a model's help, and run once each. `evals/paired.py` prints "indicative" on every comparison, and on three rows "no conclusion".

- One replan, fixed. `MAX_REPLANS = 1` is a constant: no make variable and no flag changes it, and nothing replans after every step. ReWOO has no replan node at all.

- One thinking level for every role. `THINKING=` goes with every call of the turn; the planner and the executor cannot think at different levels.

- No plan read back from a checkpoint. Both graphs compile with no checkpointer; the plan lives in the turn's record, which `SAVE=` keeps.

- The offline plans are the script's. The scripted planner takes the manager's cap on purpose, and its tokens are four characters each with 64 thinking tokens a call.

- Offline, a cold wave shares one interpreter. Its searches rank the corpus in Python, so three side by side can outlast the 25 s budget; `RAG_TIMEOUT_S=90` gives them room, and passage numbers can differ from run to run.

- No to-do pattern. `TodoListMiddleware` is not wired into the bench.

- One of ADK's two planners, on one brain. `ADK_PLANNER` sets `PlanReActPlanner` on the chat's ADK brain alone; the bench's patterns and the other brains have no planner, and `BuiltInPlanner` has no switch. The next deploy of the chat service clears it, since `lesson-12.8.sh` sets the service's variables whole.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it.

Nothing was deployed. acme's stored rows carry their classes, if this lesson's setup line ran them. `~/graph-venv` holds the chat image's pins. Your home directory holds the saved runs, `plans-offline.jsonl`, `plans-lite-offline.jsonl`, `plans.jsonl` and `plans_lite.jsonl`, and `commands/agent_patterns.py` is the kit's again. If you ran step 10's lane cell, `documind-chat` runs this kit's image and `ADK_PLANNER` is off again. Lesson 10.3 takes the next question: once an agent has an answer, check it, retry it, or choose the best of several.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.2 Plan first or decide each step: plan-and-execute · v5.0

Next: Lesson 10.3 Check, retry or choose: the critic and refiner pattern.
