# Lesson 10.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.1_ReAct_WIX.html`, reviewed at blob `222da83d6de50d7502063423e3eae648e7011723`. Learners read that page on the course site; this guide keeps its prose.

Every agent runs one loop. It observes the question, its tools and every result so far; it thinks; it acts, by calling a tool or answering. Where the thinking happens is a choice, and the choice has a bill. Gemini thinks natively, in thinking tokens you pay for at the output price and never see, then calls a tool by function calling. Prompted ReAct, made for models with no function calling, has the model write its reasoning as text, `Thought:` and `Action:`, stops it at `Observation:`, and lets code read the Action, run it and write the result. A plan-first prompt asks for a numbered plan before the first call. You run all three on the agent bench, with the Desk agent's tools and its 7 calculators: one turn offline and on your lane, then the 11 calculator rows, with correct answers, thinking and visible tokens, and rupees for each. Then you delete the one line of code that keeps a model's own Observation out, and watch an invented figure become the answer.

- One loop, three places to reason

- The words: the loop, thinking, function calling, ReAct, the stop and the cut, the figure check

- Before you run anything: set up the shell

- The Chat page: an agent whose reasoning you see only on the bill

- The loop, its recorder and the figure check, offline

- Prompted ReAct, parsed by code; and a plan first, offline

- Change it: delete the parser's cut

- The 11 calculator rows, scored offline and paired

- Your lane: four thinking levels, ReAct, a plan, and what a search returns

- The 11 rows on your lane, paired, and the rows they leave

- Why each pattern, what it costs, the library's forms, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn where an agent's reasoning can live: in the model's hidden thinking, in text that a parser reads, or in a plan written up front, and what each costs in tokens and rupees. Then you will prove it on the same 11 calculator rows, with correct, verified, thinking and visible tokens and rupees for each pattern, and you will watch one line of code keep a model's invented Observation out of the answer.

### One loop, three places to reason

Observe, think, act; and where the thinking goes.

One loop. Every agent in the kit runs the same loop. The model observes: the question, the tools it may use and every result so far. It thinks. Then it acts: it calls a tool, or it answers. The tool's result is the next observation, and the loop goes round again. Lesson 5.1 built this loop on the chat brains, and lesson 5.4 drew it as a graph. Each pass is one model call, and each call reads the whole turn again, so a long turn pays for its early text many times over. The turn's limits from lesson 5.5 stop it at 12 calls, Rs 5 or 100 seconds.

Native thinking. Gemini 3 models think before they write. The thinking is spent in thinking tokens: you never see them, and you pay for them at the output price, USD 7.50 a million on `gemini-3.6-flash`, which is Rs 0.64 for every 1,000. A request's `thinking_level` says how much to spend. The bench sends `minimal`, `low`, `medium` or `high`, and step 8 shows which of them your model takes on location `global`. Then the model acts by function calling: the request declares the tools, and the reply is a structured call, a name and JSON arguments, which the framework runs. The Desk agent sends `low`. This is the bench's `loop` pattern.

Prompted ReAct. ReAct, reason and act, came first, for models with no function calling. No tool is declared. The tools are written into the prompt as text, with a protocol, and the model writes one step a reply: `Thought:`, what it needs and why, then `Action: tool[{"argument": value}]`. It stops at `Observation:`, a stop sequence the request sends. Code reads the Action, runs the tool and writes the `Observation:` line itself, and the next call sends the whole transcript again. The reasoning is now visible text, billed as output too, and a thinking model still thinks natively before it writes. This is `react_text`.

A plan first. The third pattern keeps the loop and puts one instruction at the top of its prompt: write a numbered plan before the first tool call. The plan is visible text, written once and read back on every later call. Nothing runs it: the loop still decides every call, and the model may leave its plan. Lesson 10.2's patterns execute their plans in code. This is `plan_first`.

The arithmetic is never the model's. All three run on the agent bench, `commands/agent_patterns.py`. It builds the Desk agent of lesson 10.4 beside the Desk's own, with a recorder added: one `retrieve` over the classes policy, statute and guidance, and the 7 calculators of `shared/desk_calc.py`. The prompt tells every pattern to work each figure out with a calculator, and a calculator takes only numbers written in the question or in the right clause of a passage the turn read. Lesson 10.5 teaches that check. Here it means one thing: a right figure that no calculator returned is a figure the model worked out itself, and the eval says so.

What only code may write. In prompted ReAct the Observation belongs to code. A model that runs on past its Action and writes `Observation: Rs 2,50,000` has invented a tool's result, and if anything reads it, the invention becomes the answer. Two things stop that. The stop sequence asks Gemini to end its reply before it writes `Observation:`. The parser's cut, the first line of `read_step()`, reads nothing from the first `Observation:` on, whatever the model wrote. Step 6 deletes the cut.

Three chartered accountants work out the same client's gratuity. The first works it out in her head. You pay for her minutes, but all you see are her instructions to the article assistant, "fetch the Code, section 53", and the figure she signs. The second writes every step in the working papers: "Thought: I need section 53. Action: fetch section 53." The assistant fetches it and writes what he found underneath, "Observation: ...", and the file goes back to her desk, to be read from the top before the next step. Her firm has one rule for that file: only the assistant writes an Observation. If she writes "Observation: Rs 2,50,000" herself, the assistant tears off everything after her last Action before he files it. The third CA writes a plan on the file's cover first, "1. fetch section 53, 2. run the gratuity sheet, 3. sign", then works like the first, and nobody checks her against her plan. In all three offices the arithmetic is done on the firm's gratuity sheet, which accepts only numbers from the client's letter or from the Code.

#### One question, three places to reason

Choose a calculator row, then step through the turn one model call at a time, with the three patterns side by side. Each call shows what it read, what it thought, what it wrote, and what code did with it. For the gratuity row you can also choose what the stop sequence does: hold, as Gemini's should; fail to hold, with the parser's cut in place; or fail to hold with the cut deleted, which is step 6.

Every call here is the kit's own turn, run when this page was built: each row's scripted model, the one `make agent-turn OFFLINE=1` uses, over the kit's own corpus, so the three patterns search with the same words, call the same calculator with the same arguments and give the same answer. The token counts are the script's: four characters a token, and 0 thinking tokens a call at minimal, 64 at low, 256 at medium and 1,024 at high. The loop's script counts no tool declarations, which Gemini does count on your lane, about 1,131 tokens a call; `react_text` carries its tools as text in its prompt, and the script counts them. Step 8 shows your lane's own counts.

A scripted model never wavers. On your lane, Gemini chooses its searches and its calls, may write a different plan or none, and spends the thinking it chooses at each level. What does not change is who writes what: the thinking is the model's, an Observation is code's, and every figure is a calculator's.

### The words: the loop, thinking, function calling, ReAct, the stop and the cut, the figure check

Seventeen rows, each with the value it takes on your lane.

One distinction to hold: the thinking is the model's and hidden, an Observation is code's, and a figure is a calculator's. The three patterns differ in where the first of these happens, and in what it costs.

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

The shell, in the kit, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok` from the block above. Steps 4 to 7 run offline at Rs 0 and need no project: the first `make agent-turn` or `make agent-eval` builds `~/graph-venv` with the chat image's pins (lesson 5.4 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call `gemini-3.6-flash` on location `global` and rag-api's `/v1/passages` as `documind-ui-sa`.

The bench's desk searches by class, and drops every passage that has none (`services/chat/desk_agent.py`, `_search()`). Lesson 10.4 gives each document its class, and this lesson comes first, so run its one line now: it writes acme's and zeta's registries from `evals/manifest.json` and relabels their stored rows, as lesson 10.4 explains. A second run finds nothing to change. It ends with a `relabel_applied` line for each company; an exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later. A `pin_miss` in its plan means the object on your lane is not the version the manifest records, and lesson 10.4 shows how a person re-pins it.

### The Chat page: an agent whose reasoning you see only on the bill

Two agent brains, one figure question, and a caption with no thinking in it.

#### Definition

Open the DocuMind UI and its Chat page. Choose `langchain` in the sidebar's Brain list and ask the question below. Then choose `adk` and ask it again. Under each answer, the caption names the brain, the tools its turn called, the time it took and the turn's rupees.

I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

Both brains are agent loops, lesson 5.1's and lesson 5.7's, on the same model as the bench. `langchain` sends thinking `low` (`shared/profile.py`). `adk` sends no level, so Gemini thinks at its own default for the model: `services/chat/brains.py` builds its `LlmAgent` with no planner and no thinking setting. Their tools are `retrieve` and `calculate_processing_cost` (`services/chat/tools.py`), and neither works out a gratuity. So whatever figure each brain wrote, the model did the arithmetic itself, and nothing on the page says how. The caption's rupees include every thinking token the turn spent, and the page shows none of them.

The figure the calculator returns in step 4 is Rs 2,40,000: 7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000. Hold your brains' figures against it.

### The loop, its recorder and the figure check, offline

The Desk agent's loop with a recorder inside its limits, at Rs 0.

#### Definition

`_loop()` builds the agent the Desk builds: LangChain's `create_agent` over the desk's tools and prompt, with the Desk's own middleware, the turn's limits (`DeskTurnLimits`) and the guard. The bench adds one middleware between the two, the recorder. It wraps each model call: it sends `THINKING` with the call when you set one, and keeps the call's tokens as `call_record()` splits them. langchain-google-genai 4.4.0 counts Gemini's thinking inside `output_tokens` and reports it again as `output_token_details["reasoning"]`. So the visible tokens are the output less the thinking, and the rupees bill both at the output price. The figure check reads the model's answer the other way round: every figure written in it must be in a calculator's result, in the question or in a passage the turn read.

#### The code

#### Do it: one turn

With `OFFLINE=1`, `make agent-turn` runs the bench on a scripted model and the kit's own corpus: no project, no credential, no network. The question is the gratuity row of the task set.

#### Do it: the same turn at four thinking levels

Three model calls: a search, the calculator, the answer. The model's text says Rs 2,40,000 and so does the calculator. The lines under "Worked out in code" are code's, written from the calculator's result, and the figure check finds nothing unsupported.

Every count is the script's: four characters a token, and 0 thinking tokens a call at minimal, 64 at low, 256 at medium and 1,024 at high. So the four levels move only the thinking column and the rupees, from Rs 0.7237 at minimal to Rs 2.6821 at high, while the input stays at 5,436 tokens: thinking is output. On your lane, the model decides how much it thinks at each level, and step 8 measures it.

### Prompted ReAct, parsed by code; and a plan first, offline

The same question through react_text and plan_first, at Rs 0.

#### Definition

`react_text` is a two-node LangGraph graph, `think` then `act`. `think` sends one call with no tool bound. Its system prompt holds the desk's own prompt, `REACT_PROTOCOL`, and each tool's declaration as a line of JSON. Its user turn holds the transcript: the question, then every step as code read it, each followed by the Observation code wrote. The call carries the stop sequence, and it goes through the loop's own two wrappers, the turn's limits around the recorder, so the Meter counts and prices each call as it does the loop's. `read_step()` reads the reply. First comes the cut. Then a Final Answer ends the turn; exactly one Action becomes a tool call, which `act` runs through LangGraph's `ToolNode` with the brains' timed wrapper; anything else is a format error, written back as the next Observation for the model to correct.

`plan_first` is the loop with `PLAN_FIRST` ahead of the desk's prompt, and nothing else.

#### The code

#### Do it: prompted ReAct

#### Do it: a plan first

The same search, the same calculator, the same answer, by three routes. `react_text`'s model wrote each step as text, and code ran each Action and wrote each Observation: 107 visible tokens against the loop's 48.

It also read 9,377 tokens against the loop's 5,436, but most of that gap is the script's doing. `react_text` carries its 8 tools as text, which the script counts. The loop's script counts no declarations, and Gemini does: with them, the loop's three calls read about 8,829. What is left on a lane is the protocol, about 155 tokens a call, and the transcript's labels. The difference that stays is in the output: the Thought lines, and on a thinking model, the thinking as well.

`plan_first`'s prompt is 57 tokens longer on every call, for the instruction. It wrote its plan once, 47 more visible tokens in call 1, and read it back on every later call: call 2 read 103 tokens more than the loop's. Then it did exactly what the loop did. Nothing ran the plan, and nothing had to.

### Change it: delete the parser's cut

A model that writes its own Observation, once with the cut and once without.

#### Definition

A stop sequence is a request to the endpoint, and an endpoint that does not honour it lets the model run on. The kit's scripted text model can play one. With `--invent`, it writes past its calculator's Action: `Observation: Rs 2,50,000`, then a Thought and a Final Answer built on its own observation. `make agent-turn` takes it as `INVENT=1`; `INVENT=` with a figure of your own writes that figure instead.

#### Do it: first, with the cut

The parser read up to the Action and cut the rest: the three lines under "cut by the parser" were never read. Code ran the calculator, wrote the real Observation, and the model answered Rs 2,40,000.

#### Do it: delete the cut, and run it again

#### Put it back

With the line gone, `read_step()` read the whole reply, found a Final Answer after the invented Observation, and ended the turn there: two calls, no calculation, and the answer Rs 2,50,000, a figure no tool produced. The Desk would have shown it with nothing under "Worked out in code". The figure check caught it, because no calculator, question or passage wrote 2,50,000.

That is why the cut is a line of code and not a sentence in a prompt. `REACT_PROTOCOL` already tells the model never to write an Observation, and a model that runs past its stop sequence can run past that sentence too. `git checkout` put the line back, and `grep -c` counts it once again. The kit's own test makes the same deletion in memory (`commands/tests/test_agent_patterns.py`).

### The 11 calculator rows, scored offline and paired

The task set's calculator slice through the three patterns at Rs 0, then the paired difference.

#### Definition

`evals/agent_tasks.jsonl` holds 21 rows: 11 calculator rows, 5 lookups, 3 chained rows (lesson 10.2's), a trap and a refusal. `SLICE=calc` takes the 11 calculator rows: a gratuity three ways, carry-forward for acme and for zeta, encashment with a cap the question invents, accrual, two notice periods, a wage deadline and a committee threshold. `CHECK=1` recomputes each row's figure with `desk_calc` and checks that the hard gate lets each question through. Then every row goes through every pattern. `score()` marks a run correct when its answer states the row's figure and no wrong one, and gives it provenance when a calculator of the row returned that figure and the figure check finds nothing unsupported.

Offline, the scripted model slips on about one run in five, on purpose: it writes the figure itself, right, with no calculator behind it. A single turn never slips; an eval run does.

#### The code

#### Do it: check the rows, then run them

#### Do it: the paired difference, at Rs 0

One cell splits the saved runs by pattern and prints what a call of each pattern read, thought and wrote; for `react_text`, it also counts the replies that ran past the stop and the Actions code could not read, with the bench's own parser. Then `COMPARE=` pairs each pattern with the loop, row by row.

Every pattern is correct on all 11 rows and verified on 9. The script slipped on `calc-gratuity-7y8m` and `calc-grc-threshold` in all three patterns: the same rows, because its slips depend on the row and the run, not on the pattern. The gratuity answer was right, and the figure check flagged its 2,40,000, which no calculator returned. The threshold's answer is a yes, which the figure check cannot flag; only "no threshold_check call returned it" catches that one. That is what provenance is for.

The paired lines say what 11 tied rows prove about which pattern is better: nothing. With no row where two patterns disagree, the difference is 0 and its interval runs from -25.9 to +25.9 points, wider than the 3-point margin on both sides. The rupees are the script's: Rs 0.7048, 1.2100 and 0.7650 a run for the loop, ReAct and the plan.

### Your lane: four thinking levels, ReAct, a plan, and what a search returns

Live turns of the bench on gemini-3.6-flash, then the /v1/passages call every pattern makes.

#### Definition

Without `OFFLINE=1`, `make agent-turn` needs `PROJECT`, and `commands/agent-turn.sh` exports what a live turn needs: the project for Gemini, rag-api's address, and `documind-ui-sa` as the account rag-api's ID token is minted as, which every tenant's roster holds. It builds the address from `REGION`, so pass yours: the Makefile's default is `us-central1`. Each turn is a few calls of `gemini-3.6-flash` on location `global`, under the chat service's limits of 12 calls, Rs 5 and 100 seconds. By the kit's own count each turn below costs Rs 1.16 to 1.26 before thinking; step 10 shows how that count is made.

#### Do it: native thinking, at four levels

The loop, on the gratuity question, once at each level. The filter keeps the level line, the three call lines, the totals and the figure check of each turn.

The thinking column is now the model's own count, reported by Gemini and read by the recorder, and billed at the output price. Read each turn's rupees against its visible tokens: the difference is what its thinking cost. A level your model does not take on location `global` shows as `the turn failed` and make's error line instead of three calls.

#### Do it: prompted ReAct

Read three things. The Thought and Action lines are Gemini's own. A "cut by the parser" block would mean the endpoint did not honour the stop sequence and the cut did its job, as in step 6. The totals line counts the format errors: each is an Action code could not read and answered with an Observation, and each cost a call.

#### Do it: a plan first

The plan is on call 1, after "the model wrote:", when the model wrote it beside its first call. A model may also write the plan and no call at all: `create_agent` then ends the turn, and the plan is the answer. Either way, hold the calls it made against the plan it wrote: nothing kept it to the plan.

#### Do it: what a search returns

Every pattern's `retrieve` is one POST to rag-api's `/v1/passages`: the same door, roster and filters as `/v1/query`, then the reranked passages with their full text, and no model. The cell sends the search the bench's script makes for this question, as the bench sends it: tenant acme, the three classes, the top 5, labelled brain `desk`.

Model `none`, cost 0: at rag-api, a search costs the turn nothing. Its cost comes later. The passages' text is in the input of every later call of the turn, in every pattern: the loop reads it as tool messages, `react_text` as Observation lines. On the Rs 0 lane the same search returns 7,438 characters of passages, which is most of what call 2 and call 3 read in step 4. An empty list here means acme's stored rows carry no class: run the setup line.

### The 11 rows on your lane, paired, and the rows they leave

33 live turns, then three reads at Rs 0: the paired difference, each pattern's calls, and rag-api's rows.

#### Definition

The same command as step 7 without `OFFLINE=1`: every calculator row through every pattern once, at the Desk agent's own thinking level, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes; the report comes when all 33 have run.

This is the lesson's proof: the same 11 rows through native thinking, prompted ReAct and a plan first, each with correct, provenance and verified, the thinking and visible tokens of a run, and its rupees. For any row a pattern got wrong, the why column says how. A tie on correct answers is the likeliest result on rows a calculator settles; what separates the patterns is what each paid for the same answers.

#### Do it: the paired difference and each pattern's calls, at Rs 0

The same cell as step 7, on your lane's saved runs.

The split lines are the per-call view: what one call of each pattern reads, thinks and writes on your lane, and for `react_text` whether any reply ran past its stop and how many Actions code could not read. The paired lines count only the rows where two patterns disagree. Unless several rows split one way, the interval crosses the 3-point margin and the verdict is "no conclusion": the honest answer on 11 model-written rows.

#### Do it: rag-api's rows for those searches

Every search the bench made is a `passages` row in rag-api's log, labelled brain `desk` and asked as `documind-ui-sa`, with model `none` and cost 0. The routed Desk of lesson 10.4 sends its agent mode's searches the same way, so on a lane where it works figures out, those rows are counted here too.

### Why each pattern, what it costs, the library's forms, and what the kit does not do yet

When to reason where, the bill for each, ADK's two planners, and the gaps.

#### When to reason where

- Native thinking with function calling, when the model has both. Gemini 3 does. The reasoning is hidden, so you judge it by its effects: the calls it makes and the figures it gets right. The level is the dial, and every 1,000 thinking tokens cost Rs 0.64, on every call of the turn.

- Prompted ReAct, when the model has no function calling. An older model, or a small one served without tool support. Its reasoning is on the page, line by line. It writes more output, resends its protocol and its transcript as text, and on a thinking model it pays for both kinds of reasoning. It needs two things only code can give it: a stop sequence, and a parser that cuts.

- A plan first, when you want the reasoning up front. It costs one instruction: the plan is written once and read back on every call, and nothing holds the model to it. When a plan must be kept, code has to run it: lesson 10.2.

- In every pattern, a figure is a calculator's. The patterns change where the model reasons, never who does the arithmetic. The figure check and the eval's provenance hold all three to that.

#### The library's forms

ADK, at the chat image's pin (google-adk 2.8.0), offers two of the three as planners. `BuiltInPlanner` sets the model's own `thinking_config` on each request: native thinking. `PlanReActPlanner` tells the model to write a plan under `/*PLANNING*/`, its reasoning under `/*REASONING*/`, its tool code under `/*ACTION*/` and its answer under `/*FINAL_ANSWER*/`, and to revise the plan under `/*REPLANNING*/`. It keeps the model's tool calls as native function calls and marks the written reasoning as thought: a plan first, with ReAct's written reasoning, on a model that still calls functions. The kit's ADK brain uses neither unless it is switched: lesson 10.2's `ADK_PLANNER=plan_react` gives it the second. Text ReAct, an Action that code parses, is not among ADK's planners; `react_text` is the kit's own.

#### What it costs

"Before thinking" is the input and visible tokens the kit's script counts for these very turns, plus the tool declarations Gemini receives with each loop and plan-first call, about 1,131 tokens, priced at USD 1.50 and 7.50 a million at Rs 85 to the dollar. Thinking is the one number only your lane knows. Step 8's four turns tell you yours before you spend on step 9, and the Meter stops any turn that reaches Rs 5.

Each point is checked in the kit's code, or in the pinned ADK, and the build asserts it, so this box changes when they do.

- The comparison is indicative. 11 rows, written with a model's help, one run each. `evals/paired.py` prints "indicative" on every comparison until people write a held-out split.

- Thinking is a count. The recorder reads how many thinking tokens a call spent, never what was thought: the Desk agent's model asks Gemini for no thoughts, only for its answer.

- The offline numbers are the script's. Its thinking is fixed, 0 thinking tokens a call at minimal, 64 at low, 256 at medium and 1,024 at high, and its loop counts no tool declarations.

- Nothing in this lesson runs a plan. `plan_first`'s plan is advice. The patterns that run theirs, `plan_execute` and `rewoo`, are lesson 10.2's.

- The stop sequence is your lane's fact. The scripted model honours it unless told not to; whether Gemini does on location `global` is what step 8's ReAct turn shows. The cut is there either way.

- No planner in the kit's ADK brain by default, and never `BuiltInPlanner`. It builds its `LlmAgent` with neither of ADK's planners; `ADK_PLANNER=plan_react`, off unless set, gives it `PlanReActPlanner` afterwards (lesson 10.2), and nothing in the kit sets `BuiltInPlanner`.

### Verify it yourself: the checklist

Eleven checks, each one block above, each with the value that proves it on your lane.

acme's and zeta's stored rows carry their classes, which lesson 10.4 relies on. `~/graph-venv` holds the chat image's pins. Your home directory holds the saved runs, `bench-101-offline.jsonl` and `bench-101-lane.jsonl`, and their splits by pattern. Nothing was deployed, and `commands/agent_patterns.py` is the kit's again. Lesson 10.2 takes the next question: write a plan first and let code run it, or let the loop decide each step.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.1 Choose where the agent reasons: observe-think-act and ReAct · v5.0

Next: Lesson 10.2 Plan first or decide each step: plan-and-execute.
