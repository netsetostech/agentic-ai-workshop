# Lesson 10.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.3_Critic_Refiner_WIX.html`, reviewed at blob `7dea9d7ffd5ff9269e2969481d0cd7d3175ff4e8`. Learners read that page on the course site; this guide keeps its prose.

An agent's answer can be wrong in a way code can see: a figure no calculator returned, a passage the turn never read. A critic judges the answer and a refiner improves it, and there are three ways to put them to work. Re-roll: run the agent several times and count a question right when any run is, the ceiling a perfect chooser could reach. Choose: run it several times and ship the run the critic picks. Retry: run it once, and only when the critic fails the answer, let one reflect call write a note and run it again, at most 3 times. On the agent bench the critic is code, not a model: `figure_check()` reads every figure and every [n], so one answer always gets one verdict. You run the three ways on the task set's 12 calculator rows, offline and on your lane, with correct, verified, calls and rupees for each, and the critic's own precision beside them. You watch a note try to carry a figure into the next attempt and fail, then change one line so that it gets through.

- One critic, three ways to use it

- The words: critic, figure check, attempt, reflect call, note, re-roll, best-of, precision

- Before you run anything: set up the shell

- The Chat page: one question, asked twice

- The figure check on its own, at Rs 0

- verify: the loop, the check and one reflect call, offline

- Change it: put the notes into the question

- The 12 calculator rows offline: re-roll, choose, retry

- Your lane: one verify turn

- The 12 rows on your lane, with the calculator rule taken out

- Why the critic is code, what each way costs, the library's form, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn three ways to use a check on an agent's answer, re-roll, choose and retry, why the check here is code and not a model, and what each way costs in calls and rupees. Then you will prove it on the same 12 calculator rows with pass@1, pass@3 re-rolls, best-of-3 chosen by the check and verify's pass@3 with notes, each with its calls and rupees, and with the check's precision beside them.

### One critic, three ways to use it

Run it many times and count, run it many times and choose, or run it once and retry only when the check fails.

One critic. Lesson 10.1's figure check, `desk_calc.unsupported()`, finds every figure in an answer, a number in digits or a whole date, that no calculator of the turn returned and that neither the person's question nor a passage the turn read writes. This lesson's critic, `figure_check()` in `commands/agent_patterns.py`, runs it and adds two rules: every [n] the answer cites must be a passage the turn read, and the turn must not have stopped at one of its limits. It is code, so the same answer, calculations, question and passages always get the same verdict, and a verdict costs no token. Lessons 10.1 and 10.2 changed how the agent works a question out; this lesson keeps lesson 10.1's loop as it is and changes what happens after it answers.

Re-roll. Run the loop k times on the same question. The share of questions where at least one of the k answers is right is pass@k. It is a ceiling, the rate a chooser that always picked the right answer would reach, and it costs k turns a question. On its own it ships nothing: something still has to choose.

Choose: best-of-k. Run the loop k times and ship one answer, chosen in code: a run the figure check passes, then a run whose answer states a calculator's own figure, then the earliest (`best_of()` in `evals/agent_eval.py`). It never reads the expected figure, so it works on a question that has no answer key. It costs k turns a question too.

Retry: verify. Run the loop once. When the check passes the answer, it ships, and the turn cost what the loop costs. When it fails, one reflect call reads the question, the answer, what the attempt did and the check's verdict, and writes a note, which code cuts to 300 characters on one line. The loop answers again as a turn of its own, with every note so far in its system prompt. At most 3 attempts: the first answer the check passes ships, or else the last one does.

A note is memory, not evidence. The notes go into the next attempt's system prompt, never into its question. `check_args`, the check lesson 10.5 teaches, takes a calculator's numbers only from the question or from the right clause of a passage the turn read, and the figure check reads the question and the passages; neither reads a note. So a figure a note writes is refused as a calculator's argument and flagged in an answer: a note cannot launder a number. The reflect call itself is shown each calculator's result only as "a figure", so code never hands it the right number to copy.

What the check cannot see. It reads digits and dates. "Yes, it must have one" holds no figure, so a yes the model decided by itself passes. A figure copied from a passage passes too, because the passage writes it: the trap row's 45 days is LV-07's own cap, right whether or not a calculator worked it out. So an answer the check passes is not yet a verified answer, and the check's precision, the share of the answers it passes that are right and verified, is a number to measure, not to assume.

A tablet plant's quality-control lab. The line makes a batch, and the lab's assay checks every figure on its label against what the instruments measured for that batch: a fixed procedure, not anyone's opinion. A plant can use the lab three ways. It can make three batches of an order to learn how often at least one comes out right, which tells it the best it could do. It can make three batches and release the one the assay passes. Or it can make one, and only when the assay fails it, send it back with a note on the batch record, saying what went wrong and never the right value, and make it again, at most three times. The assay has blind spots: a label that says "within limits" in words carries no figure to check, and a figure copied from the specification sheet matches the sheet whether or not anyone measured it. And a note pinned to the record is not a measurement: the lab never reads a figure off a note.

#### One verify turn

Each attempt's reflect call is counted on that attempt's own Meter, so a verify turn can spend up to 3 times one turn's limits. Step 5 shows the code.

#### Re-roll, choose, retry

Choose a row and k, the number of runs a re-roll or a best-of may use. The first column is the loop's first k runs, each a whole turn: its tools, its answer, the figure check's verdict and the eval's. The second is how best-of-k picks one of them. The third is verify's attempts on the same row, with the note before each retry. Under them is what each way gave on this row and what it cost, then the same over all 12 rows. The three rows where something happens come first.

Every card is a run the kit made when this page was built, step 7's two saves: the loop three times a row and verify once, on the scripted model over the kit's own corpus. The verdicts are the kit's own functions, `figure_check()`, `best_of()` and the eval's `score()`. The tokens and rupees are the script's: four characters a token, and 64 thinking tokens a call at `low`. Step 9 shows your lane's own.

The scripted model slips on a schedule, on purpose. On about one run in five of a calculator row it skips the calculator and writes the figure itself, from code, so the figure is right with no calculator behind it, and on the trap row it does so on its first run. verify's first attempt slips on the same schedule, an attempt that reads notes never slips, and its notes are the script's: what failed, read from the verdict, and which calculator to call, with no figure. So offline, one retry always mends what the check can see. On your lane Gemini decides all of it. With the desk's prompt as it stands it may never skip a calculator, so that verify never retries and every way ties; step 9 takes the prompt's calculator rule out to make failures happen. Gemini's notes are its own and may write a figure, and its retries may fail again. What does not change is who decides: code passes or fails every answer, a calculator works out every figure `check_args` lets through, and no note reaches the question.

### The words: critic, figure check, attempt, reflect call, note, re-roll, best-of, precision

Twenty-one rows, each with the value it takes on your lane.

One distinction to hold: the eval's verified reads the row, its expected figure and its calculator, which no deployed agent has; the figure check reads only the turn, which every deployed agent has. This lesson's critic is the second kind, and the first is how you measure it.

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

The shell, in the kit, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok` from the block above. Steps 4 to 7 run offline at Rs 0 and need no project. Their Python cells need only the shell's own Python; the first `make agent-turn` or `make agent-eval` builds `~/graph-venv` with the chat image's pins (lessons 5.4, 10.1 and 10.2 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call `gemini-3.6-flash` on location `global`, and rag-api's `/v1/passages` as `documind-ui-sa`.

The bench's desk searches by class and drops every passage that has none (`services/chat/desk_agent.py`, `_search()`). Lesson 10.1's setup line gave acme's and zeta's stored rows their classes. If you have not run it, run this now: the 12 rows are acme's but one, zeta's carry-forward. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

### The Chat page: one question, asked twice

The gratuity question, asked of the deployed langchain brain, then asked again in a fresh session.

#### Definition

Open the DocuMind UI and its Chat page, choose `langchain` in the sidebar's Brain list, and ask the question below. Then reload the page and ask it again. The page keeps one conversation per browser session (`services/frontend/chat.py` gives each session its own `session_id`), and a reload starts a new session, so the second turn does not read the first. Under each answer, the caption names the brain, each tool call the turn made, the time it took and the turn's rupees.

I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

Two turns of the same brain on the same question: two answers and two bills. The `langchain` brain is lesson 5.1's loop, on the same model as the bench, and its tools are `retrieve` and `calculate_processing_cost` (`services/chat/tools.py`): no calculator. Every figure in either answer is the model's own arithmetic, and nothing in the chat service checks it, since no code under `services/` runs the figure check. If the two answers differ, you have a re-roll and no way to choose between them. If they agree, agreement is still not a check.

The calculator's figure for this question is Rs 2,40,000; step 7's check prints it. Hold both answers against it. The rest of the lesson puts a critic in code behind the bench's agent and uses it three ways.

### The figure check on its own, at Rs 0

figure_check() and check_args on answers you can read, then what a reflect call is shown.

#### Definition

`figure_check(answer, calculations, question, passages, stopped_by)` passes an answer when `desk_calc.unsupported()` finds no figure that the turn's calculations, its question or its passages' text does not write, every [n] it cites is a passage the turn read, and the turn did not stop at a limit. `said_check()` puts the verdict in words: what failed, each failed figure as the answer wrote it and never another. Nothing else goes in. There is no argument for a note, a plan or a remark, so none of them can supply a figure.

`unsupported()` reads all that `calculate()` returned this turn, the value, the arguments, the formula, the sections and the notes, and the source texts as they stand. A number in words is prose to it, and a date with no year, a clause code, a citation mark and a provision's number are no figures.

#### The code

#### Do it: the check on eight answers, and check_args on a note

`agent_patterns.py` imports only the standard library and the kit's `shared/` at the top, so the shell's own Python runs the check. The cell works the gratuity row's figure out with `desk_calc.calculate()`, uses the Code's own words as quoted in `desk_calc.RULES` as the passage, and puts eight answers through `figure_check()`. Then it asks `check_args` about a wage the question does not state, once on the person's question and once with a note's words put into it.

The same Rs 2,40,000 passed with the calculator's result behind it and failed without it: the check reads where a figure came from, not whether it is right. A figure of its own, a passage never read and a stopped turn each failed, in words a reflect call can read. Then the two blind spots: the yes in words and LV-07's 45, both written with no calculator, both passed.

The last answer passed only because the note was put into the question, which then wrote the figure. `check_args` works the same way: "monthly_wage = 60000 is a fact about the person that their message does not state: ask them for it" on the person's question, and the wage taken once the note's words are in it. That is why verify never puts a note there.

#### Do it: what a reflect call reads, and what code keeps of its reply

After a failed check, `ask_reflect()` writes the reflect call's user turn: the question, the answer, what the attempt did (`did_lines()`) and the verdict. `cut_note()` turns its reply into the note, and `noted()` puts every note into the next attempt's system prompt. The cell gives `ask_reflect()` an attempt whose calculator returned Rs 2,40,000 and whose answer wrote Rs 2,50,000, then cuts a long reply the way verify cuts every note.

The reflect call is told that `gratuity_estimate` was called, with its arguments, and that it "returned: a figure". The right figure is nowhere in what it reads, so its note cannot hand the next attempt a corrected number: the next attempt has to call the calculator again. The verdict names only the figure that failed, 2,50,000.

The reply was 386 characters, and code kept 299 on one line, its backticks made quotes so that the notes' fence stays whole. Code does not take the figure out: this note still writes 2,50,000, and a run's record counts such notes (`note_figures`). It need not take it out, because no check takes a figure from a note.

### verify: the loop, the check and one reflect call, offline

verify on the gratuity row three ways, at Rs 0: as the prompt stands, with a figure of its own, and with notes that carry a figure.

#### Definition

`verify` is a pattern of the bench, beside lesson 10.1's loop and lesson 10.2's planners, on the same tools and limits. Each attempt is the loop, a turn of its own (`retry_context()`: a fresh Meter at 12 calls, Rs 5 and 100 s, and no passage or calculation of an earlier attempt). `figure_check()` reads its answer. Passed, the answer ships. Failed, the next attempt starts with one reflect call, counted on that attempt's Meter: the desk's prompt and `REFLECTOR`, the user turn `ask_reflect()` writes, and no tool bound. Code cuts the reply to a note, and the loop runs again under the desk's prompt with `NOTES` and every note so far in a fenced block. Its question, the text `check_args` and the figure check read, is the person's own: the line marked THE QUESTION. The record is the shipped attempt's, with every call tagged by its attempt and role (answer or reflect), and it adds each attempt, the notes, which attempt shipped, its verdict and the calls and rupees by role.

#### The code

The cells run the scripted model, which plays the loop on each attempt and writes a note on the reflect call, telling the two apart by `REFLECTOR` in its system prompt. A single turn never slips. `--invent` makes its first attempt write a figure of its own; `--launder` makes every note carry a figure, which each later attempt writes as its own, with no calculator, and makes its first attempt write the row's figure itself so that a note is written at all. `make agent-turn` takes them as `INVENT=1` and `LAUNDER=1`; a figure in place of the 1 writes that figure instead. The filter drops the passage lists and code's "Worked out in code" lines.

#### Do it: as the prompt stands

Attempt 1 searched, called `gratuity_estimate` and wrote its figure; the check passed it, and it shipped: 3 calls, Rs 0.8461 by the script's count. When the first answer passes, verify costs exactly what the loop costs, because nothing else runs.

#### Do it: a figure of its own, corrected in one round

Attempt 1 wrote Rs 2,50,000 with no calculator, and the check failed it, naming that figure. The reflect call, Rs 0.1474, wrote the note shown: what went wrong and which calculator to call, with no figure. Attempt 2 started afresh, with the note in its system prompt and the person's question as it was, called `gratuity_estimate` and wrote its Rs 2,40,000. The check passed it, and it shipped. The turn made 6 calls for Rs 1.4703: a retry costs one reflect call and one more attempt.

#### Do it: notes that carry a figure

Every note ended "The figure is Rs 2,40,000.", the right figure, and each later attempt wrote it with no calculator. The check failed every attempt: the figure was only in a note, and a note is not among the things it reads. After 3 attempts the last answer shipped, and the record says the check passed none: 8 calls, Rs 1.6802. The answer is right and still not verified, which is the point. No number reaches an answer through a note, not even the right one.

The kit's own test holds the other half. A note supplies a wage, "The wage is Rs 60,000", attempt 2 gives it to the calculator, and `check_args` refuses it, because the question it reads is the person's own. Its answer then states no figure, so the check passes it, and only the eval says it is not correct; step 10 comes back to that. `make agent-tests` runs this test with the rest of the bench's tests, offline.

### Change it: put the notes into the question

The line marked THE QUESTION, edited so that each attempt asks the question with every note after it, then put back.

#### Definition

Each attempt asks `asked = question`, and that one line decides what `check_args` and the figure check read, because the next line makes it the turn's `desk_message`. Change it so that an attempt asks the question with every note after it, and run the laundering cell again. The kit has no switch for this, on purpose: you edit the line, run the turn, and put the file back.

#### Do it: the notes in the question

#### Put it back

The header's question now ends with the note, and attempt 2's Rs 2,40,000 passed: the note had become part of the question, and the question is a source. It shipped with 0 calculations, after 5 calls for Rs 1.0645. The printout still says "check_args refuses it as an argument and the figure check flags it in an answer": that sentence was true because of the line you changed, and with the change it is not. The eval would still mark this answer unverified, since no `gratuity_estimate` call returned the figure, but the eval reads the row's expected figure and calculator, which a deployed agent never has.

`git checkout` put the line back, and `grep -c` finds it once.

### The 12 calculator rows offline: re-roll, choose, retry

The loop three times a row and verify once, saved, then side by side at Rs 0, and the saved runs read back.

#### Definition

`SLICE=calc,trap` takes the task set's 11 calculator rows and its trap, 12 of its 21 rows. `CHECK=1` recomputes each row's figure with `desk_calc` and checks that the hard gate lets each question through. The eval scores each run as lessons 10.1 and 10.2 do: correct, provenance, and verified for both. Offline, the script skips the calculator on about one run in five of a calculator row, by a checksum of the row's id and the run, and on the trap row's first run: 6 of the loop's 36 runs, on 6 rows, the same rows and runs whatever the pattern.

Two saves and a replay, the way your lane runs them in step 9: the loop with `RUNS=3`, and verify once a row, since its retries are its second and third tries. `REPLAY` with `BEST_OF=3` rescores both at Rs 0 and, with a verify arm and another in the same records, prints the four ways side by side, each with its calls and rupees a row, then the check's precision: the runs and attempts it passes, and how many of those are correct and verified. `critic()` computes all of it from the saved records.

#### The code

#### Do it: check the rows, then run them

#### Do it: side by side, at Rs 0

Every way was correct on every row: the script's slip writes the right figure, so correctness cannot tell the four apart. Verified can. The loop's first runs were verified on 9/12 rows, at 2.8 calls and Rs 0.6755 a row: on 3 rows the first run slipped and wrote its figure with no calculator. Three runs a row reached 12/12, the ceiling, and best-of-3 reached it too, both at 8.5 calls and Rs 2.1107 a row, since a re-roll and a best-of pay for every run. verify reached 10/12 at 3.1 calls and Rs 0.7620 a row. It retried the gratuity row once, whose 2,40,000 the check could see, and shipped the threshold's yes and the trap's 45 on their first attempts, because the check passed them.

The precision line says why. Of the 32 of the loop's 36 runs the check passed, 32 were correct and 30 verified: 2 passes had no calculator behind them, the yes and the 45. Best-of-3 got past those two because each row had other runs, and its second rule prefers a run that states a calculator's figure. verify has no other run to prefer: it pays for a retry only when the check fails, and a pass with no calculator behind it ships.

No way wins here. The paired comparison, verify against the loop's first runs, prints no conclusion at this many rows, and the four ways differ in what they buy: the ceiling, at three times the calls; the ceiling reached by a chooser, at the same price; or a retry paid only on a failure, as good as the check is. These are the script's runs and the script's tokens: they show what each way does with the same slips, not how often Gemini slips.

#### Do it: the saved runs, read back

Each saved run is one JSON line, the turn's record. A verify run's record carries every attempt, with the note it started from and the figures that note writes. The cell rescores every run with the eval's own functions and prints, row by row, the check's verdict on each of the loop's runs, the run best-of-3 ships, verify's attempts, and each note.

6 rows show a slip. On 4 the check failed the slipped run, and on 2, the threshold and the trap, it passed it. Best-of-3 shipped a run with a calculator behind it on every row. verify retried only the gratuity row, the one row whose first run slipped in a way the check could see. The only note offline writes no figure, because the script's notes never do. On your lane the notes are Gemini's, and this cell is how you read them.

### Your lane: one verify turn

verify on the gratuity row, live, with the desk's prompt as it stands.

#### Definition

Without `OFFLINE=1`, `make agent-turn` needs `PROJECT`, and `commands/agent-turn.sh` exports what a live turn needs: the project for Gemini, rag-api's address, built from `REGION` (pass yours: the Makefile's default is `us-central1`), and `documind-ui-sa` as the account rag-api's ID token is minted as. `gemini()` builds the model as the chat service builds the Desk agent's, `gemini-3.6-flash` on location `global` at thinking `low`, and the reflect call runs on the same model at the same level. Every search is one POST to `/v1/passages`, the call lesson 10.1 showed, which rag-api books with no tokens and no cost. Each attempt runs under the chat service's limits, 12 calls and Rs 5, with its reflect call counted on it, so a verify turn can spend up to Rs 15.00 in all. By the kit's own count the turn costs about Rs 1.16 before thinking when its first attempt passes, and each retry adds about Rs 1.31; step 10 shows how that count is made.

Read it attempt by attempt. If attempt 1 called `gratuity_estimate` and the check passed it, the turn is the loop's own and nothing was retried. If the check failed it, the printout says why, then shows the reflect call with its tokens and rupees and the note it wrote; a line `the note writes ...` means Gemini put a figure in its note, which no later attempt can use. A retry that passed ships, and after 3 failures the last attempt ships and the totals say the check passed none. An attempt its limits stopped ends `stopped by turn_budget` or `model_calls`, and the check fails it for that alone.

### The 12 rows on your lane, with the calculator rule taken out

The rule out, 48 live runs, the rule back, then two reads at Rs 0: the side by side, and the records.

#### Definition

A model that follows the desk's prompt calls a calculator for every figure, so the check rarely fails, verify rarely retries, and the four ways tie. That would be true and would prove nothing about checking. To see the critic at work, these two runs take out the prompt's calculator rule, the three lines from "Work every figure out with a calculator" to "say which one is missing" in `services/chat/desk_agent.py`, in your clone only. The bench imports `desk_agent` from your clone in its own process, so the deployed chat service is not touched. Put the rule back as soon as the second run ends. Without it each call reads about 66 tokens fewer, by the script's count of four characters a token.

The runs are step 7's without `OFFLINE=1`: 36 loop turns, then 12 verify runs, each run saved as one JSON line, both with the rule out so that the two arms face the same prompt. A progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

#### Do it: side by side, at Rs 0

This is the lesson's proof: on the same 12 rows, the loop's pass@1, its pass@3 re-rolls, best-of-3 chosen by the figure check and verify's pass@3 with notes, each with correct, verified, calls and rupees a row, then the check's precision. Read the `with notes:` line of verify's report first. If the check passed every first attempt, verify never retried and ties pass@1: the weakened prompt did not make Gemini fail. If it retried, that line says on which attempt each run passed and how many notes wrote a figure. The precision line says how far the check can be trusted on your lane: a pass that is correct but not verified is a figure with no calculator behind it, which the check could not see. The 12 model-written rows cannot rank four ways, and the kit says so: every comparison is indicative, and no way is named the winner. These runs measure the four ways on a weakened prompt; they say nothing about the Desk's own error rate.

#### Do it: read the records back, at Rs 0

The same cell as step 7, on your lane's saves.

Each `the note before attempt` line is a note Gemini wrote, and the line under it says whether the note writes a figure. A note that writes one is what the weakened prompt invites and what the kit expects: the figure check and `check_args` never read it, so the attempt after it had to work its figure out again or fail.

### Why the critic is code, what each way costs, the library's form, and what the kit does not do yet

Choosing between the three ways, the bill for each run, Google ADK's reflect-and-retry plugin, and the gaps.

#### Why the critic is code

- One answer, one verdict. A model asked to judge an answer reads the same passages, can agree with its own mistake, may judge the same answer two ways on two calls, and bills each call. `figure_check()` gives one verdict for one answer and costs nothing, and nothing a note or a remark says can argue with it, because it reads neither.

- It knows only the turn. The eval's verified reads the row: its expected figure and its calculator. A deployed agent has neither, so the critic a deployed agent can run is the turn's own, and that is the one this lesson uses. Nothing from the task row ever reaches the model.

- Its blind spots are the price. It reads digits and dates; a yes in words, a figure in words and a figure copied from a passage pass. Measure its precision before you trust a pass: offline, 2 of the 32 runs it passed had no calculator behind them.

- Re-roll to measure, not to ship. pass@k shows what a perfect chooser could reach, at k turns a question.

- Choose when k turns a question are affordable. Best-of-3 reached the ceiling offline because each row had another run and its second rule prefers a run that states a calculator's figure: 8.5 calls and Rs 2.1107 a row, against pass@1's 2.8 calls and Rs 0.6755.

- Retry when most first answers pass. verify pays for a reflect call and one more attempt only when the check fails: 3.1 calls and Rs 0.7620 a row offline. It ships whatever the check passes, so it is as good as the check.

- A choice made by a model. Lesson 10.4's router chooses too: when its two cheap signals disagree about a question's desk, one arbiter call, a model, picks between the routes they named. This lesson's chooser is code, and it reads the answer, not the question.

#### What it costs

"Before thinking" is the input and visible tokens the kit's script counts for these very runs, plus the tool declarations Gemini receives with every call that binds the desk's 8 tools, about 1,131 tokens, priced at USD 1.50 in and 7.50 out a million and Rs 85 to the dollar. The loop's calls and verify's answer calls bind them; the reflect call binds none. Thinking is billed as output, Rs 0.6375 for every 1,000 tokens, and only your lane knows how much a call spends. Two limits to know. A loop turn on these rows reaches Rs 5 before its last call only when its calls think about 3,400 tokens each, and a verify attempt at about 2,206; the Meter then stops it, and the turn prints `stopped by turn_budget`. And because each attempt has its own Meter, the ceiling for a verify run is Rs 15.00, not Rs 5: Rs 375.00 for steps 8 and 9 together, against about Rs 49.86 before thinking.

#### The library's form

Google's Agent Development Kit, at the chat image's pin (google-adk 2.8.0), ships `ReflectAndRetryToolPlugin`. It catches a tool call that raises an exception, or, in a subclass that overrides `extract_error_from_result()`, one whose result holds an error (the method finds none by default). It gives the model structured guidance to reflect on the error and on the arguments it sent, and lets it try again, up to `max_retries` consecutive failures of a tool (3 by default), counted per invocation unless told otherwise. It retries a tool call, not an answer, and its guidance is the model's to follow. verify checks the whole answer in code and starts a fresh attempt. The kit uses the plugin nowhere. Tree of Thoughts and LATS go further, searching over many candidate steps with a model as the judge. The kit has neither, and the lesson plan defers plan search and LATS past this cohort.

Each point is checked in the kit's code or the pinned library, and the build asserts it, so this box changes when they do.

- The check reads digits and whole dates only. A yes or no in words, a figure in words and a figure copied from a passage pass it: `unsupported()`'s own docstring says a number in words is prose.

- An answer with no figure passes. "I could not work the gratuity out" states nothing to check, so it ships as passed, and only the eval, which reads the row, says it is not correct (the kit's test in step 5).

- No note outlives its turn. Each turn starts with no notes. Moving a note that keeps coming back into the desk's prompt is a hand edit, and nothing measures it.

- No reflect call reads the grader. The reflect call reads only the turn's own verdict, never the eval's: there is no switch for a grader's critique.

- Fixed limits. `MAX_ATTEMPTS = 3` and `NOTE_CHARS = 300` are constants: no make variable and no flag changes them. One thinking level goes with every call, the reflect call's too.

- The Desk does not run verify. Nothing under `services/` imports the bench, and no code there runs the figure check.

- The comparison is indicative. 12 model-written rows; `evals/paired.py` prints "indicative" on every comparison, and on these rows "no conclusion".

- The offline slips and notes are the script's. Its slips write the right figure, and its notes never write one.

### Verify it yourself: the checklist

Thirteen checks, each one block above, each with the value that proves it.

Nothing was deployed. acme's and zeta's stored rows carry their classes, if this lesson's setup line ran. `~/graph-venv` holds the chat image's pins. Your home directory holds the saved runs, `plain-offline.jsonl`, `verify-offline.jsonl`, `plain.jsonl` and `verify.jsonl`, and `commands/agent_patterns.py` and `services/chat/desk_agent.py` are the kit's again. Lesson 10.4 takes the next question: before any agent answers, route each question to one specialist agent.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.3 Check, retry or choose: the critic and refiner pattern · v5.0

Next: Lesson 10.4 Route each question to one specialist agent.
