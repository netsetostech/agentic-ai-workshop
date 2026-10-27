# Lesson 10.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.5_Agent_Desks_WIX.html`, reviewed at blob `c28dde874c47f9fe22a3fa07eca871da38a48b53`. Learners read that page on the course site; this guide keeps its prose.

In lesson 10.4 the routed Desk sent a question that asks for a figure to a desk running as a small agent. This lesson opens that agent. The model reads the passages and chooses each calculator call; code does the arithmetic. A calculator is only as right as what goes into it, so before one runs, `check_args()` takes every argument from its one source: a fact about the person from their own message, a handbook figure from its clause of a passage the turn read. The cap a manager mentioned, the 60 days of the notice clause, the 31 of "31 December", the 07 of "LV-07": each is refused, in words the model reads and acts on. You try the check on the kit's own passages, ask the Desk page for a figure and give it a wrong cap, read the agent's code and three of its tests, delete the prompt's rule and watch the check refuse anyway, send one question to two arms over REST, and read what the Desk logs and keeps. Last, you run the Desk's three eval arms on the same twelve rows: the routed Desk, code alone, and one agent with every tool. You set them side by side with a paired difference that says what twelve rows can and cannot show, then combine them: a vote over what code returned, a tie handed to a person, and a mixture-of-agents aggregator whose invented figure the check catches.

- The teller's rule: every number from the slip or the rate card

- The words: agent mode, source, clause, check_args, refusal, arm, paired, vote, aggregator

- Before you run anything: set up the shell

- The Desk page: a figure worked out in code, and a cap nobody wrote

- The agent, its calculators and check_args, in the code

- Change it: delete the prompt's rule

- One question, two arms, over REST

- The rows and the checkpoint

- Three arms on the same twelve rows, compared and combined

- Why it is shaped this way, what it costs, and what the kit does not do yet

- Verify it yourself

You will learn how the Desk's agent mode keeps every calculator argument to its one source, in code, and what that check can and cannot see. Then you will prove it on your lane: a figure and a wrong cap on the Desk page, the check on your lane's own passages, the prompt's rule deleted with the refusals unchanged, two arms over REST, the Desk's rows, and three arms run on the same twelve rows, compared and combined.

### The teller's rule: every number from the slip or the rate card

Where each argument of a calculator may come from, why that is checked in code, and what the check cannot see.

A desk that runs as an agent. In lesson 10.4, when the router's classifier says a question asks for a figure (`needs_calculation`), the handbook or statute desk does not answer with one rag-api call. It runs as a small agent: `services/chat/desk_agent.py`, a LangChain `create_agent` loop on `gemini-3.6-flash` at thinking level low. The agent searches the desk's own documents and calls the desk's calculators from `shared/desk_calc.py`. The model chooses the searches, the calculator and its arguments. Code does the arithmetic, and code writes the lines under the answer that show the formula and where each number came from.

The arithmetic is not the risk; the arguments are. min(50, 45) is 45 whoever computes it. What can go wrong is what goes in. A person writes "my manager says the encashment cap is 100 days", and a model passes 100. A question asks about encashment and notice at once, the passages hold both clauses, and the model takes NP-03's 60 days as the encashment cap. It reads 31 from "lapses on 31 December", 7 from the clause code "LV-07", 3 from the grade "E3", 5 from the Code's "five years". Or the person gives no balance, and a model fills one in. Every one of those calls would run, and every result would be arithmetic done right on a number nobody wrote where it had to be written.

One source for each argument. `desk_calc.CALCULATORS` names, for every argument, the one place it may come from. A fact about the person (months, days, a balance, a wage, years, a headcount, a date) must be written in the person's own message, as the router masked it. A handbook figure (the accrual rate and the carry-forward cap in LV-01, the encashment cap in LV-07, the notice days in NP-03, or PB-02 on probation) must be written in that clause of a handbook passage this turn read. A flag such as `fixed_term` is true only when the message says it, and not just after a "not". `check_args()` checks each argument against its source before the calculator runs. Anything else is refused, and the refusal is an error result the model reads: "ask them for it", or "search for that clause and use the figure it states". The model can try again with a number that has a source, or say which number is missing.

The clause, not the passage. A passage is a chunk the search returned; a clause is the words from its code, such as LV-07, to the next clause code. A cap must be in LV-07's words, not merely somewhere in what the turn read, so NP-03's 60 never passes for LV-07's cap. `check_args()` reads digits (40,000 and 1,50,000 alike), number words (fifty, twenty-six), lakh, crore and k. The digits of a date are never a number of their own, and a clause code or a grade is a name, not a number.

A Code's calculator needs the Code. The statute desk's three calculators (a gratuity estimate, the date wages are due, the grievance committee threshold) take only facts about the person, because a Code's own figures are the same in every company that holds it, and `desk_calc` fixes them. So a Code's calculator runs only when this turn's passages include that Code's own text, and a company that does not hold the Code gets no figure from it.

Only the last box does arithmetic, and only after the first three have passed. No box asks the model anything. Step 4 shows each one in the code.

Then three ways to build the Desk, on the same rows. Arm B is the routed Desk of lesson 10.4: agent mode only on a figure. Arm C is code alone: the gate, then a direct answer, with no classifier and no calculator. Arm A* is one agent over every class the person may read, with every calculator. Step 8 runs all three on the same 12 dev rows, pairs them row by row, and combines them.

The teller at a bank counter, booking a fixed deposit. The amount and the tenure come from the customer's own slip, in the customer's hand. The interest rate comes from the printed rate card on the counter, and only from the line for that scheme: the senior citizens' line, not the savings line above it. If the customer says "my neighbour got 9 percent", the teller does not key in 9: it is not on the card. If the slip has no amount, the teller asks for one and never guesses. The booking system takes no rate that is not on the card's line, so a quick teller and a careless one book the same deposit. What the system cannot tell is whether the teller read the line for the right scheme: that is what the branch's own checks are for.

#### The argument check

Choose a calculator, a person's question, the passages the turn has read and the value the model gave one argument; the call's other arguments are the ones the question gives. Every verdict was computed when this page was built by `desk_agent._calc()` itself, on a stand-in for the turn's context: the desk's list, `check_args()`, the Code's own text, then `desk_calc`. 385 calls in all: 24 accepted and 361 refused. It opens on jn-03 with NP-03 and LV-07 read and a cap of 60.

The passages are the lane's own chunks of acme's and zeta's handbooks, as `evals/agent_eval.py` mints them, one chunk a clause, and three sentences of s.53 as `desk_calc` quotes them; each comes from the asking person's own company, as a desk's search only ever does. The words are the kit's: a refusal is what the model reads, and an accepted call shows the line code writes under the answer. Only the note under a verdict is the page's: it compares the call with the one the kit's own row expects, from `evals/route_arms.jsonl` (as `evals/tests/test_route_arms.py` recomputes it) or `evals/agent_tasks.jsonl`.

It is not a measure of how often a model brings a wrong number: only a run on a lane can say that, and steps 5 and 8 make one. Nor is the check the whole guard. Of the 24 accepted calls, 11 pass with a figure the kit's row does not expect. In 7 of them the number is written in the right source but stands for something else. LV-01 writes both the accrual rate and the carry-forward cap, and the check reads 1.75 and 30 in its words, so a cap of 1.75 or a rate of 30 passes: 8 completed months x 30 days = 240 days. PB-02 writes six months of probation, three months of extension and 15 days of notice, and the check reads 3, 6 and 15, so notice days of 6 pass: 2026-10-05 + 6 days = 2026-10-11. fig-01's message writes "8 months", so years = 8 passes: 8 years 8 months counts as 9 years (a part of a year over six months counts as a year). In the other 4 the clause is right for someone else: PB-02's 15 days for a confirmed E3, NP-03's 60 for a person on probation. `check_args()` proves where a number is written; it cannot know what the number stands for there, or which of two clauses covers this person. The prompt, the calculators' own range checks, the eval rows of step 8 and, for a regulated figure, a person carry the rest.

### The words: agent mode, source, clause, check_args, refusal, arm, paired, vote, aggregator

Twenty-one rows, each with the value it takes on your lane.

One distinction to hold: the model chooses a call, and code decides whether the call may run. The model can choose badly, and step 8 measures how often it does; the check cannot be argued with, because no argument the model writes is ever a source.

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

The shell from the section above, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `ME`, `API` and `tok`. Your lane as lesson 10.4 left it: the routed Desk on for acme and zeta, `evalacme` and `evalzeta` holding `desk_eval`, and the example index built. This lesson deploys nothing. Its kit is lesson 10.5's eval files (`evals/route_arms.jsonl`, `evals/route_eval.py`'s `--compare`, `evals/combine.py`) and two make targets, which the setup's `git pull` brought; the Desk your lane serves is lesson 10.4's. The offline cells, the tests of steps 4, 5 and 10 and step 8's selftest, need no lane and cost nothing; the first makes `~/graph-venv`, lesson 5.4's venv, with the chat image's pins if it is missing. The cells that call a model cost about Rs 46 to 61 in all, most of it step 8.

### The Desk page: a figure worked out in code, and a cap nobody wrote

acme's clause notes, then two questions on Ask the Desk: jn-03, and one that states a wrong cap.

#### Do it: acme's notes on two clauses

`make desk` with `NOTES=` writes `tenant_settings/acme.clause_notes` from `evals/desk/clause_notes.acme.json`: a note on LV-01 and LV-07. Each note says what the OSH Code's text says about that leave, and leaves it to the People team whether it covers the person's role. The handbook desk adds a clause's note under an answer that cites the clause, in agent mode as in a direct answer. The command prints one line: acme's switches as they stand, `"clause_notes": ["LV-01", "LV-07"]`, and that rag-api and the chat service read the change within 60 seconds. The cell also notes the time in `SINCE105`, from which step 7 reads the Desk's rows, and prints the Desk page's address.

#### Do it: two questions on Ask the Desk

Open the Desk page at that address, signed in as yourself, and under Ask the Desk ask jn-03 from the arms set: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" Then ask: "I am leaving with 80 days of earned leave, and my manager says the encashment cap is 100 days. How many days will be encashed?" Both ask for a figure, so when the router's classifier marks them `needs_calculation`, as it should, the handbook desk answers each in agent mode: a few `gemini-3.6-flash` calls a turn.

What to read. The first answer is the model's sentences, then a block that code wrote: "Worked out in code:", then "Earned leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [n]." and the condition LV-07 sets, that the figure holds only once probation is over. The n is the place of LV-07's passage among those the agent read; its search may read them in another order on your lane. The 60 days of notice need no arithmetic: NP-03 states them, and the agent cites the passage. Under the block, "Note on LV-07:" is acme's note, there because the answer cites LV-07. In the second answer, a calculation can only be "min(80, 45) = 45 days": the balance the person gave and LV-07's cap. The 100 days the manager mentioned are in the person's message, not in LV-07, so the calculator cannot take them. If the model passed 100 first, the check refused it; the page does not show a refused call, and step 6 reads one from the reply. On your lane `gemini-3.6-flash` writes the sentences and chooses the calls, so its words are its own, and the block appears only when a calculator ran.

### The agent, its calculators and check_args, in the code

Where agent mode starts, the desk's tools, one call through `_calc()`, the check, the prompt and the limits, the lines code writes; three tests; then the check on your lane's own passages.

#### Where agent mode starts

`_answer()` runs a handbook or statute desk in agent mode when the decision carries `needs_calculation` and the desk has an agent model, and arm A*'s desk always. `_agent_answer()` refuses anything but an answer turn, so a gate hit or a case never reaches an agent. A model error, a 429 or a 5xx, is not the turn's: the section becomes the direct answer, under the same Meter, and the log names only the error's type.

#### The desk's tools

Each desk's agent holds its own retrieve, whose classes code fixes, and its own calculators: the handbook desk `retrieve`, `accrued_leave`, `carry_forward`, `encashable_days`, `notice_end`; the statute desk `retrieve`, `gratuity_estimate`, `statutory_deadline`, `threshold_check`; arm A*'s agent a retrieve that may choose a class among the person's own, and all seven calculators. `handle_tool_error` turns a refusal into an error result the model reads, not a failed turn. A calculator's docstring is what the model reads about it, and each argument there says where it must come from: "as LV-07 of a handbook passage states it".

#### One call: _calc()

Every calculator tool is a thin wrapper around `_calc()`. It checks the name against the desk's list, then runs `check_args()` on the turn's ledger: the passages in the order the agent read them, so the i-th is passage [i]. Then a Code's calculator needs that Code among the statute passages. Only then does `desk_calc` compute, and the result carries the arguments and, for each, where it was found. A refusal raises `ToolException` with the check's own words.

#### Each argument's source

The handbook figures name their clauses; every fact about the person names `MESSAGE`; the two flags carry the pattern that must be said; each Code's calculator names its Code in `needs`.

#### The check

`check_args()` reads the person's numbers and dates once, then walks the arguments. A handbook figure must be `_in_clause()`'s hit: the first policy passage whose clause writes it. A clause is `clause_text()`: from each place its code is written to the next clause code. `numbers_in()` skips a date's digits and any digits glued to a letter on their left, so "LV-07" and "E3" give no number, and `said()` refuses a flag in a negated phrase.

#### The prompt, the limits and how the agent is built

The system prompt asks for a search first, citations as [n], every figure through a calculator, and only numbers written in the question or a passage: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Step 5 deletes that sentence. `DeskTurnLimits` prices each agent call as `gemini-3.6-flash` on the turn's own Meter, the one the router's calls already counted, so one turn holds to 12 model calls, Rs 5 and 100 seconds, whatever the agent does. `agent()` builds each desk's agent once per process, with no checkpointer of its own: the passages and the arguments stay out of the Desk's thread.

#### The lines code writes

The block under the agent's answer is `compose()`: each calculation's label, its clause or section, the formula, where each number came from, its conditions and its notes. A gratuity figure is labelled an estimate here, whatever the model wrote.

#### Do it: three tests, offline

Three of `commands/tests/test_desk.py`'s agent tests. In the first, the agent passes a cap of 40, which neither LV-07 nor the message writes: refused, no calculation, no "Worked out in code". The second sends a gratuity question to the statute desk with the Code on Wages, not the Code on Social Security, among the passages, and has the agent ask for `encashable_days`, which the statute desk does not hold: two refusals, one by the Code check and one as an unknown tool. In the third the model raises a 429, and the section is the direct answer under the same Meter. A scripted model plays the agent and a table plays rag-api, so no model is called.

`commands/agent-turn.sh`, given arguments, runs them in `~/graph-venv`, which it makes with the chat image's pins if it is missing; with `OFFLINE=1` it needs no project.

#### Do it: the check on your lane's own passages

The same check, on what your lane's rag-api returns. The cell asks `POST /v1/passages`, as `documind-ui-sa`, the account on every company's roster, for acme's handbook passages on "earned leave encashed on exit": the retrieval the agent's search makes, with no model call. Then it runs `check_args()` on jn-03's question twice, with a cap of 60 and then 45. 60 is NP-03's notice days: when NP-03 is among the passages, 60 is a number the turn has read, but it is not in LV-07's words, so the check refuses it with "refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". 45 is accepted, found in LV-07 at its passage's place in the list.

### Change it: delete the prompt's rule

The rule is advice to the model; the check is code. Delete the rule, run the tests and two turns on your lane, then put it back.

One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of `services/chat/desk_agent.py`, which the offline tests and `make agent-turn` import, and nothing here redeploys the chat service.

Offline: the same three tests. They pass unchanged. Each refusal comes from `_calc()` and `check_args()`, and neither reads the prompt.

On your lane: two agent turns with the rule gone. `make agent-turn` runs the handbook desk's agent in your shell, built as the Desk builds it, on `gemini-3.6-flash` and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn.

What to read. Each `encashable_days` call's arguments, and what came back. Without the rule a model may try a number of its own more often: a balance for the second question, which gives none, or a cap from the wrong clause. Every such call comes back refused, in the check's words; for a balance nobody wrote: "refused: balance = 50 is a fact about the person that their message does not state: ask them for it". The model then asks for the missing number or answers without a calculation, and the figure check at the end says whether any figure in its words has no source. Whether this model tries a wrong number at all on the day you run it is the model's own behaviour; what the run shows is that none gets past the check. The rule makes a refused call less likely, which saves a model call. It was never what made the figure right.

### One question, two arms, over REST

jn-03 to `POST /v1/desk` as `evalacme`: the routed Desk, then one agent with every tool.

An eval account may send `arm` in the body of `POST /v1/desk`; from anyone else the field is a 403, "arm is for the Desk's eval accounts (desk_eval)". Arm B is the Desk everyone gets. Arm Astar skips the classifier: the router takes the fallback decision, marked arm Astar, and the desk graph answers it with one agent whose retrieve may search any class the person reads, with all seven calculators. The cell sends jn-03 on each arm, in a session of its own, and prints what the arms differ in: each section's desk and mode, its tool calls and refused calls, each calculation with its arguments and where they were found, and the turn's model calls and `limits.cost_inr`.

What to read. Arm B's route is `handbook`, and its section's desk is `handbook` with mode `agent` when the classifier marked the question `needs_calculation`; its `model_calls` count the classifier's call too. Arm Astar's route is `fallback`, its section's desk `astar`, and no classifier call is in its count; its retrieve may search the statutes as well, so it can read more passages and make more calls. In both, `encashable_days` with `found {'balance': 'your message', 'cap': 'LV-07 [n]'}` is the check's record of where each number came from, and a name in `refusals` is a call the check turned back. `limits.cost_inr` is the turn's own price, the router's call included: step 8 adds it up row by row.

### The rows and the checkpoint

The `desk` rows of steps 3 and 6, from Cloud Logging; evalacme's threads; and what a Desk thread keeps.

Every `POST /v1/desk` turn logs one `desk` row from the chat service. It names every field it carries, and never the question.

Two of its fields are easy to misread. `mode` is the company's: `desk_route` as the chat service read it, `on` for acme, not the section's agent or direct; a row shows agent mode by its `tool_calls` and `refusals`. `arm` is `B` unless an eval account sent another. The cell reads the rows since `SINCE105`: your two Desk page turns and evalacme's two. Run it in the shell where step 3 set `SINCE105` and step 6 defined `sa`, a minute after step 6, so that Cloud Logging has the rows. Then `make thread`, lesson 6.8's reader of the chat service's Cloud SQL checkpoints, lists evalacme's threads, the latest first.

What to read. Your rows say `you` and evalacme's say `evalacme`; each says `mode on`; arm B's and arm Astar's rows differ in `route` (`handbook`, `fallback`) and `method`. A turn that ran a calculator has `encashable_days` in `tool_calls`, and a refused call is in `refusals`. `cost_usd` is the model calls' price in dollars, which the reply showed in rupees with rag-api's part added. In `make thread`'s list, `desk~lesson105-Astar` and `desk~lesson105-B` are step 6's threads: an answer turn runs the desk graph, which writes a checkpoint. The reader marks each "(a Desk thread, desk_graph.py: not decoded here)": it decodes the chat brains' threads, not the Desk's.

#### What a Desk thread keeps

The thread is `tenant:user:desk~session`, and its state is `DeskState`. The messages are the masked question and the reply. The sections are kept whole: each with its mode, its calculations with their arguments and where they were found, its refused calls, and its citations, each quote a passage's text cut to 500 characters by `citation()`.

Since `make thread` does not decode a Desk thread, the page shows one from the kit's own graph: one turn of the wrong-cap question through `desk_graph.build()` and `run_turn()`, with the stand-ins of `commands/tests/test_desk.py`. A scripted model plays the agent: it searches, passes a cap of 100, is refused, passes 45, and answers. A table plays rag-api, holding the lane's chunks of LV-07 and NP-03, and acme's notes are the file step 3 wrote. Then `graph.get_state()` reads the thread back.

The refused call is in the section's `refusals`, the accepted one in its `calculations`, with `found`; the messages hold no passage and no argument. On your lane the section of step 6's threads has the same keys, holding what your model chose.

### Three arms on the same twelve rows, compared and combined

The arms set; one run an arm; the reports side by side, paired; then the saved runs as an ensemble.

#### The rows

`evals/route_arms.jsonl` holds 12 dev rows in the route set's schema: 6 that a calculator decides and 6 that a clause answers as it stands; 8 for the handbook desk and 4 for the statute desk; 10 acme's and two zeta's. five are new, all model drafts; jn-03 and the six lookups are copied unchanged from `evals/routes.jsonl`. `evals/tests/test_route_arms.py` recomputes every figure with `shared/desk_calc.py`, from the row's own question and its company's own clause. fig-04, the notice-to-wages chain across two desks, is not written yet.

Three rows test why the check exists. fig-03 is scored on the date as the calculator writes it, 2026-12-04, which only "Worked out in code" writes in that form; an answer that works the date out in the model's words and writes "4 December 2026" fails. fig-05 is zeta's, whose LV-01 carries 18 days forward where acme's carries 30. fig-06 has no figure at all: 3 years 2 months is under the five years s.53(1) asks for, and 90,000 is the sum that ignores them, so an answer that writes it fails.

#### What a live run keeps

Since lesson 10.5's kit, a `--live` run keeps, from each desk turn's reply, what the arms differ in: each section's desk, mode, refused tool calls and calculations, and the turn's model calls, `limits.cost_inr` and latency as measured here. A measure the reply does not carry is left out, never written as 0. `make route-eval` passes `ROUTES=` as `--routes`, so it scores the arms set in place of the route set.

#### Do it: arm B, the routed Desk

Each row goes to `POST /v1/route` and to `POST /v1/desk` as its company's eval account, in a fresh session. On arm B the dev gates apply, as in lesson 10.4: 95% route accuracy and 90% recall for each desk. On 12 rows that means all 12 routed right: 8 of 8 handbook rows and 4 of 4 statute rows. One wrong route prints a `FAIL` line and make ends with `Error 1`, and the saved run and the report are written all the same. About Rs 13 to 17.

What to read. The route lines first: every row's route right, and no `FAIL`. Then `authority_rate`, every answer citing only its own company's documents of the classes the row expects, and `correct_rate`, each answer saying what its row must say. On arm B the 6 calculator rows should run in agent mode and the lookups directly: the compare below counts them.

#### Do it: arm C and arm Astar, on the same rows

Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5.

Arm Astar: one agent on every row, lookups included, over every class the person may read, with all seven calculators. The most model calls of the three: about Rs 17 to 24.

#### The arms side by side

`--compare` reads two or three reports of one split, one arm each, on the same rows, and refuses anything else: two reports of one arm, no report of arm B, two splits, or rows that differ. For each arm it prints the correct and authority rates with their Wilson intervals, the desk turns' rupees and model calls, p50 and p95 latency, and the turns in agent mode with their calculator results and refused calls. Then it pairs B against each other arm row by row, through `evals/paired.py`: Newcombe's interval for the difference, the exact McNemar p, and a verdict read against the margin written there before any run, 3 points, on 8 October 2026.

Reading it honestly. Twelve rows are few. With all 12 right, a rate prints as "12/12 = 100.0% [75.7%, 100.0%]": its 95% interval reaches down to 75.7%. In the pairing, two arms right on every row give B minus the other +0.0 points, with an interval of [-24.3, +24.3]: "no conclusion at this many rows: the interval crosses the margin". One row that B misses and the other arm gets moves it to [-35.4, +16.9]. Only when B is right on at least four rows the other arm misses, and wrong on none it gets, does the interval clear the margin, and then it says B is better. The last line says why the verdict is indicative, never a ship decision: these are dev rows, not a test split people wrote, and B's exemplar index holds 7 of these 12 rows (jn-03 and the six lookups), so on them B's figures are an upper bound. What the paired lines do give you at twelve rows is the rows the arms disagree on: read those answers.

#### The arms as an ensemble

`evals/combine.py` reads the saved runs as the members of an ensemble, at Rs 0. For each answer row it prints which members were right, by the route eval's own verdict. On a row where any member ran a calculator, the members vote: each proposes the (calculator, value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members made than any other wins. The answer of the first member that made it ships as it stands. A member with no calculation proposes nothing, and a tie abstains: the row goes to a person, since a regulated figure is not settled by a coin. Then come each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the rows it voted on, and the figure check, `desk_calc.unsupported()`, on every member's answer.

Do it: the combiners on scripted members, offline. `--selftest` runs on scripted members of fig-01, with no model call. Two members' calculators returned Rs 2,40,000; a third writes Rs 2,10,000 itself. With `--layers 2` it adds an arbiter, which picks one member's answer from an enum of their names and ships it word for word, and two layers of a mixture-of-agents aggregator, each reading every answer of the layer before and writing a new one.

The vote and the arbiter only choose among the members' answers, so neither writes a figure of its own. The aggregator writes new text: this one averages the figures it reads and writes "About Rs 2,25,000", a figure no member computed, and `unsupported()` flags it at every layer. That is the mixture-of-agents pattern's cost on a regulated figure: every layer is a model writing again, so its figures need the same check as an agent's, while the vote needs no model call at all. `--layers` goes up to 5. On a lane the arbiter and the aggregator would be model calls of their own; the kit runs them scripted only.

Do it: the three saved runs, combined.

What to read. Each answer row's line: which arms were right and, on a calculator row, the vote's proposal, how many members made it and whose answer shipped. Arm C runs no calculator, so it proposes nothing, and on a row where B and Astar agree the vote ships B's answer. Then the members' rates, the vote beside the best single arm on the rows it voted on, and last the figures no calculation returned: a figure arm C's model wrote on a calculator row is what to expect there.

### Why it is shaped this way, what it costs, and what the kit does not do yet

Five decisions, the price of agent mode, and the gaps.

- The check is code; the rule is advice. Step 5 deleted the prompt's rule and the refusals stayed. A prompt makes a wrong call rarer, and a rarer wrong call saves a model call; the check makes one impossible to run.

- Refused in words the model can act on. A refusal names the argument, the value, the source it lacks and what to do next: ask the person, search for the clause, search for the Code's section. The agent can put it right within the same 12 calls and Rs 5.

- The clause is the unit, and it has an edge. A number must be written in its source; nothing checks what it stands for there. Step 1's panel found 11 such calls among its 24 accepted ones. A finer unit, such as each figure of a clause labelled with what it is, would need the handbooks marked up for it.

- A Code's figure needs the Code. A company that does not hold the Code on Social Security gets no gratuity figure: globex holds only the Digital Personal Data Protection Act, 2023 and the Information Technology Act, 2000, so its desk cannot run `gratuity_estimate`.

- Combine by vote, not by a writer. A vote over what code returned adds no model call and no new figure, and a tie goes to a person. An aggregator writes, so it can invent, as the selftest showed.

What agent mode costs. A direct answer is one rag-api answer: about Rs 0.45 at the course's typical 2,000 tokens in and 300 out. A figure in agent mode is the classifier's call, about Rs 0.015 on `gemini-3.1-flash-lite`, then the agent's calls on `gemini-3.6-flash`: a search, a calculator, the answer, and one more after a refused call. At 3,000 tokens in and 300 out, the passages and the tools included, a call is about Rs 0.57, so a figure costs about Rs 1.74 to 2.31, four to five times a direct answer. The search for passages makes no model call; rag-api bills its embedding and ranking on their own lines, not counted here. Your reply's `limits.cost_inr` says what yours cost, and the cap holds every turn to Rs 5. That is the trade the arms measure: arm B pays for agent mode only on a figure, arm Astar on every row, and arm C never; its figure rows show what that saving costs.

- A test split people wrote: the arms set is 12 model-drafted dev rows, so every verdict here is indicative.

- Leaving a row's own group out of B's exemplar index on a lane: the index holds 7 of the rows B is scored on.

- Arm S, and fig-04, the notice-to-wages chain across two desks.

- A smoke check that forces arm A*: `smoke/smoke_desk.py` does not.

- A live arbiter or aggregator: `evals/combine.py` runs them scripted only.

- The formal ship decision between the arms.

- Reading a Desk thread back: `make thread` lists one and does not decode it.

- Telling which of a clause's numbers an argument means, or which of two clauses covers the person: `check_args()` checks where a number is written, not what it stands for.

### Verify it yourself

Each claim of the lesson, where you checked it, and what a pass looks like.

#### Do it: lesson 10.5's own tests

`evals/tests/test_route_arms.py` recomputes every figure of the arms set, holds the rows to the route set's rules, runs the three arms end to end against a stand-in chat service (save, report, compare, combine) and checks the make targets; `evals/tests/test_combine.py` checks the vote, the selftest and what `combine.py` refuses. Standard library only, no lane, Rs 0.

acme's `tenant_settings` holds `clause_notes` on LV-01 and LV-07, set by you. They stay, and the handbook desk shows them, until `make desk PROJECT="$PROJECT" TENANT=acme NOTES=none` clears them. The chat service's Cloud SQL holds new Desk threads: your Desk page conversation, step 6's `desk~lesson105-B` and `desk~lesson105-Astar`, and a fresh session for each row of each arm in step 8; Cloud Logging holds their `desk` rows, the `/v1/route` calls' among them. Your machine holds `~/arms`, the three saved runs and the three reports, and `~/graph-venv` if it was not there before. Your checkout's `services/chat/desk_agent.py` is as the kit has it. Nothing was deployed, and no switch, role or roster changed.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.5 Run a desk as an agent with checked calculator arguments · v5.0

Next: Lesson 10.6 Trace the implemented A2A peer and its permissions.
