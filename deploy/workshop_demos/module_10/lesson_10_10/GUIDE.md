# Lesson 10.10: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.10_Coding_Agents_WIX.html`, reviewed at blob `a2ff7a373b29baf3d62e995523935a1c8d9326ff`. Learners read that page on the course site; this guide keeps its prose.

A coding agent is a model that reads files, edits them and runs commands. Left to itself, it stops when it believes the work is done. A Ralph loop does not take its word for it. The loop starts the agent fresh on the same prompt for each iteration, and an oracle the agent cannot see or edit decides when the work is done. The kit's task is one function, `statutory_deadline`, cut out of a copy of `shared/desk_calc.py`, and the answer key is the kit's own function. You play one iteration by hand. Then you run the loop offline at Rs 0 under a strong oracle and a weak one, and watch the weak one let a wrong function through. You read what the loop undoes, what it only flags and what it never does. Then you score an AI code reviewer on six planted defects and run the same loop from the statute's text alone. Last, you read the author's live run: Gemini CLI headless in a container, on a key that can call the model and nothing else.

- A loop that forgets, and an oracle it cannot see

- The words: Ralph loop, iteration, oracle, fix plan, context file, seeded defect, rubric, catch count, paper-to-code

- Before you run anything: set up the shell

- One iteration by hand

- The oracle, weak and strong

- The loop offline: three runs, two caps and the guards

- Paper-to-code: the same function from the statute alone

- The reviewer: a linter first, then Gemini on your lane

- The live loop: Gemini CLI in a container, on a model-only key

- Direct reads, and the human step

- Why it is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how a coding agent is held by code it cannot see: a loop that starts it fresh, an oracle that decides when it is done, guards that undo what it may not touch, and a reviewer measured on defects planted on purpose. Then you will prove it offline at Rs 0: the loop stops on the oracle and on a cap, the weak oracle passes a hard-coded date that the strong one fails, and the reviewer gets a catch count on six seeded defects.

### A loop that forgets, and an oracle it cannot see

The task, one iteration, the code that inspects it, the oracle that judges it, and the reviewer.

The task. The DocuMind Desk answers "when are my final wages due?" with `statutory_deadline`. It applies the Code on Wages, 2019, s.17(2): two working days, counted from the last working day, Monday to Friday. Lessons 10.4 and 10.5 teach the desk's calculators; here the function is only the subject. The loop gives a coding agent a copy of `shared/desk_calc.py` in which this one function has lost its body and raises `NotImplementedError`, and a spec saying what it must do. The agent works in a run directory under your temp directory, never in the kit. The answer key is the kit's own function, read when the loop runs, so no second copy of the right answer can drift out of date.

One iteration, fresh. Each iteration starts the agent with nothing in its head. It reads the same `PROMPT.md`, then `spec.md`, `fix_plan.md` (the plan, one item an iteration), `GEMINI.md` (the workspace's standing notes) and `oracle.md` (the last verdict). It changes the function, runs the fast test, ticks one item and exits. What an iteration learned reaches the next one only through those files. Each iteration is one commit, in a git repository kept beside the workspace, where the agent cannot see it.

Code before the oracle. Before any verdict, the loop's own code inspects the iteration. Some changes undo it, and the oracle never sees it: a change outside the function, a deleted file, a symlink, more than 80 changed lines, or, live, output that names the kit's public copy. Two things are flagged and kept: two plan items ticked at once, and a `RALPH_DONE` the oracle does not back. And some things the loop never does: it never writes in the kit, never applies a patch to your clone and never runs `git push`.

The oracle decides. The oracle sees only the agent's function, spliced into the kit's own file, so nothing else the agent changed reaches the verdict. The weak oracle is `desk_calc`'s own selftest, which checks the function on one date: resignation, last working day Friday 2 October 2026, wages due Tuesday 6 October. The strong oracle runs that selftest and 10 acceptance checks, one of them every day of 2026 for each of the four events. The agent learns only `oracle.md`: each failed check's words and the oracle's own counts, never an acceptance check's expected value. The loop stops when the oracle passes, after `RALPH_MAX_ITERS` iterations (8), or at a rupee cap, `RALPH_BUDGET_INR`.

The honest result. A function that returns 6 October for every question passes the weak oracle. It is right on 12 of the 1,460 questions the strong oracle asks: the three last working days whose due date is 6 October (Fri 2 Oct, Sat 3 Oct, Sun 4 Oct), for each of the four events. A loop judged by the weak oracle stops there, satisfied. The strong one does not.

The reviewer. An AI code reviewer reads a diff and names defects, each by one rule of a fixed rubric. The kit scores it on seven diffs: the kit's own function, and that function with one of six defects planted on purpose. A finding of the planted defect's rule is a catch, and any other finding is a false alarm. The reviewer reads code; the oracle runs it.

An apprentice who forgets every night. Each morning the apprentice remembers nothing of yesterday. On the bench lie the job card, the snag list and the inspector's slip from last evening: "3 of 11 checks failed; 628 of 1,460 parts out." The apprentice works one snag, ticks it and goes home. The inspector's gauge stays in the inspector's drawer. The apprentice never sees it, only the slip, and the slip says what failed, never the measurement it wanted. The foreman puts back anything touched outside the one part. A gauge that measures one dimension passes a part machined to that dimension and wrong everywhere else: that is the weak oracle.

#### Run the oracle on a diff

Choose a version of the function and an oracle. The panel shows the change, the oracle's verdict with each failed check, what a loop judged by that oracle does next, and what the reviewer found in that diff.

Each verdict is the kit's oracle.py, run on that version when this page was built, as make ralph-check runs it. The linter is commands/review_diff.py's offline stand-in, run on the same diffs. Gemini's findings come from the author's saved run of make review-eval, dated, and they differ from run to run.

- A fresh agent. Offline, a scripted agent; live, Gemini CLI headless in the ralph image, a new container each iteration. It reads PROMPT.md, spec.md, fix_plan.md, GEMINI.md and oracle.md.

- One item. It changes statutory_deadline, runs the fast test, ticks the first open item of fix_plan.md, and may add a line under "Learned" in GEMINI.md.

- Code inspects it. A change outside the function, a deleted file, a symlink, over 80 changed lines, or the public copy named: undone. Two items ticked, or an unbacked RALPH_DONE: flagged.

- The oracle judges. The function alone, spliced into the kit's own file, in a separate process with the network and new processes refused; live, in a container with no network at all.

- The record. oracle.md gets each failed check's words and counts, and the iteration becomes one commit beside the workspace.

- Stop, or go on. The oracle passed, 8 iterations ran, or one more would pass the rupee cap: the loop stops. Otherwise the next iteration starts fresh.

The order is run_loop()'s in commands/ralph.py; step 5 quotes its caps and its inspection.

These are the kit's own eight versions: the start, the answer key and the six seeds. A live agent writes versions of its own, and the oracle judges each the same way. The panel's verdicts never change from run to run; a model reviewer's findings do, which is why the kit reviews each diff more than once.

### The words: Ralph loop, iteration, oracle, fix plan, context file, seeded defect, rubric, catch count, paper-to-code

Fifteen rows, each with what it is in the kit.

One distinction to hold. The weak oracle and the strong one run the same code on the same function. They differ only in how much of the spec they check. A loop is only as good as the check it stops on.

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

The shell, in the kit's folder. Steps 3 to 6 need only git and Python: they run offline, cost nothing and write only under `/tmp`. Step 7's last cell calls Gemini on your lane, with `PROJECT` from the setup block. Step 8's live loop is the author's. It needs Docker, the ralph image and a model-only key that only the author creates (the cohort plan's decision 12), so on your lane it refuses to start, and you read the author's run instead. Nothing on your lane changes.

### One iteration by hand

The workspace a loop starts from, iteration 1 done in a hurry, then done properly.

#### Definition

`make ralph-workspace` builds what a loop starts from, and stops there. The workspace holds the cut `shared/desk_calc.py`, the `shared/` files it imports and the corpus files its selftest reads, all copied from the kit. At its root are the prompt, the spec, the plan, `GEMINI.md` and `oracle.md`. Its git repository sits beside it, with no remote. The first cell makes one and reads what iteration 1 would read: the plan's one item, the strong oracle's verdict on the start, and the function as the task leaves it.

#### The code

#### Do it: the workspace

The workspace holds the task and nothing that judges it: no oracle checks and no seeds. The strong oracle failed 10 of its 11 checks on the start. The one it passed, the weekend check, passed because every call raised: a value that is no date is the sweep's to count, as `oracle.py` says. Each line of `oracle.md` is a check's words and the oracle's own feedback: a count such as "1,460 of 1,460 wrong", or what the function raised. None of them says which date the oracle wanted.

#### Do it: iteration 1, in a hurry

The second cell plays iteration 1 the way a hurried agent might. It writes the kit's function with one line hard-coded, as `seeds.json`'s placeholder has it. Then it runs the fast test that the prompt names, and asks both oracles about the workspace.

The fast test passed: "every rule says what its corpus line says, and the figures hold". The weak oracle is that same selftest, so it passed too. The strong oracle failed the function on the sweep, 1,448 of 1,460 wrong, from 1 January on. An agent that trusts its own fast test would call this done. The exit status 1, and make's Error line with it, is the strong oracle's FAIL. The check also wrote the workspace's change beside it as `by-hand.patch`, which step 7's reviewer reads.

#### Do it: iteration 1, done properly

Now write the body that spec.md describes, in `$WS/shared/desk_calc.py`, by hand or with a coding agent under your eye. Gemini CLI started in the workspace with no flags runs in its default approval mode: it asks before every edit and every command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. It loads the workspace's `GEMINI.md`, the loop's notes, which carry that name only inside a workspace: a Gemini CLI session opened in the kit itself never loads them. How Gemini CLI signs in on your machine is your own setup, and nothing else on this page uses it. Then run the fast test and check again.

Two PASS lines, once the body meets spec.md. Whatever you wrote, the oracle judged the function alone. A change elsewhere in the file would have been named in a NOTE line, and the loop would have undone that iteration. `by-hand.patch` now holds your function's diff from the task's start.

### The oracle, weak and strong

The one date the selftest checks, the ten checks the strong oracle adds, and what the agent is told.

#### Definition

The weak oracle is `desk_calc`'s selftest: 79 checks, two of which call `statutory_deadline`, both on one date. The strong oracle runs the selftest first, then 10 acceptance checks, each about one thing. The sweep compares every day of 2026, for each of the four events, with `due()`, the oracle's own count, written apart from the code it judges. The kit's tests hold `due()` equal to the kit's own function on all 1,460.

#### The code

#### What the agent is told

A failed check carries two texts: a detail for people, which may quote the candidate's own error, and a feedback line for the agent, which holds only the oracle's own words and counts. `oracle.md` carries the feedback alone. The selftest's feedback includes its own FAIL lines, which the agent's copy of `desk_calc.py` prints anyway; an acceptance check's expected value never reaches the agent.

#### Where it runs

The oracle runs the candidate's code, so it runs it in a separate Python process with no credential in its environment. Before the candidate is imported, `no_network()` makes every connection, datagram and name lookup fail, loopback included, and refuses to start any other process. Guards inside one Python process are not a sandbox, as the kit's own docstring says; so the live loop runs the oracle in a container with no network at all (step 8).

#### Do it

With no arguments, `make ralph-check` judges all 8 versions under both oracles, and holds each verdict to the label `seeds.json` gives it. `SHOW=` adds one version's diff and its failed checks.

Every verdict is the one its label says. The weak oracle passes two seeds. One is the placeholder. The other, date_contract, reads the date with `date.fromisoformat` by hand, so a date not written YYYY-MM-DD raises Python's ValueError instead of `CalcError`. The Desk's tool turns only a `CalcError` into an error result the model reads (`desk_agent._calc`), so on the Desk that person's turn would fail. The selftest never sends a bad date, so it cannot see this; the strong oracle's dates check does. The other four seeds fail the selftest itself.

#### Change it: delete the sweep

The oracle's docstring names the change to try: delete the strong oracle's sweep over 2026. The cell copies `oracle.py` to a scratch directory without the sweep's two lines, then runs that copy on three versions, each spliced into the kit's own file as the loop does it.

Without the sweep, the placeholder passes all ten checks that are left. The formula check reads the result's own date and the shape check sees that it is a date, but only the sweep asks whether it is the right date. calendar_days still fails, on the selftest and on the weekend check. A check that a hard-coded answer can satisfy is no judge of done. The cell changed a copy: the kit's `oracle.py` is untouched.

### The loop offline: three runs, two caps and the guards

The scripted agent under each oracle and under a rupee cap, then what the loop undoes, flags and never does.

#### Definition

`make ralph OFFLINE=1` runs the loop with a scripted agent in the model's place: no model, no network, nothing billed. The script is the kit's own. On the engineer's spec it writes the placeholder, then calendar_days, then the kit's own function; on paper-to-code, closure_counted, then the kit's own. From the second iteration on, each step first adds a plan item for the failure it answers, then ticks the first open item. Its tokens are counted as the agent bench counts its scripted model's, four characters a token over what it reads and writes plus 64 thinking tokens, and priced at list price. So the rupee cap works offline exactly as it does live.

#### The code

#### Do it: the strong oracle, then the weak one

Under the strong oracle the script took 3 iterations. The placeholder failed the sweep. Calendar days failed the selftest, the sweep (628 of 1,460 wrong) and the weekend check (105 last working days gave a Saturday or a Sunday). The kit's own function passed, and kit.patch is empty: identical to the kit's own. Under the weak oracle the same script stopped after one iteration, on the placeholder. The loop's own record says what that means: "for the record, not used by the loop: the strong oracle on the same code: FAIL". That run's kit.patch differs from the kit's own by two lines: the count taken out, the hard-coded date put in. Each iteration's rupees are the script's tokens at list price, as live ones would be counted, and nothing was billed.

#### Do it: a rupee cap

After two iterations at Rs 2.10 to Rs 2.11 each, Rs 4.2113 was spent. A third at the dearest so far would have passed Rs 5, so the loop stopped before starting it. The cap is checked before each iteration but the first, so an iteration under way always finishes, as the chat Meter's rule has it. The iteration cap stops the loop the same way: with `RALPH_MAX_ITERS=2` the script ends "2 iterations, and the strong oracle never passed". A loop that stops on a cap exits 1, and make reports an Error, because the oracle never passed.

#### The guards: undone, flagged, never

`inspect()` runs after the agent and before the oracle. It reads git's view of the workspace and the module's syntax tree with the function left out, so comments and blank lines outside the function do not count, and a change of behaviour does. A weakened selftest is such a change.

The scripted agent can also misbehave on purpose: the kit's tests use that, and so does this page. Each row below is one iteration it played under the strong oracle when this page was built, and what `summary.json` recorded for it.

Two rules cannot show in that table here. A symlink is undone: it is the first rule of `inspect()`, and the kit's tests make one where the system allows it. And only live, an agent's output that names github.com, githubusercontent.com or agents_workshop_learner undoes its iteration, because the oracle is public there and work that may have been copied is not kept. Then what the loop never does. It never writes inside the kit:

It never applies a patch to your clone: kit.patch is written beside the run, for you to apply or not. And it never runs push, pull, fetch, clone or remote: `Run.git()` refuses them, ignores your git config, and works on a repository with no remote to push to.

An undone iteration never reached the oracle. The workspace went back to the last commit, the iteration was committed as "undone" with its reason, and `oracle.md` told the next iteration why its work was thrown away. A new file is kept and listed, but never enters ralph.patch, which carries `shared/desk_calc.py` alone. A flag changes nothing: it is a note for the person who reads the run. An over-cap diff (112 lines against a cap of 80) is undone even when the function inside it is right.

### Paper-to-code: the same function from the statute alone

The same loop and the same oracle, with the statute's lines for a spec.

#### Definition

`TASK=statute` gives the agent no engineer's spec. Its spec.md is `statute.md`, the interface, followed by the law: the lines of the Code on Wages, 2019 that `desk_calc.RULES` cites for this function (`wages_s17_2` and `wages_s17_3`), read from the kit's corpus when the loop runs. The function's docstring, which states the desk's reading, is replaced by a line that points at the law. Where the law leaves a choice open, the agent must make one, and the oracle judges it.

#### The code

#### The kit's own paper-to-code check

`desk_calc.RULES` quotes the statute's words each calculator's rule comes from, with the corpus file and lines. The selftest's first check fails when a quote is not in the lines it cites. So every time the fast test runs, the kit holds its code to the paper, line by line.

#### Do it

Section 17(2) names the closure of the establishment, yet it counts the two working days from four events only: removal, dismissal, retrenchment and resignation. The desk reads it that way and refuses closure. The script's first try accepted closure, and the selftest and the strong oracle's events check both refused it; the second try passed, in 2 iterations. The statute leaves other choices open too. It says "working days", and `statute.md` never says Monday to Friday (the kit's tests hold that), while the oracle counts Monday to Friday with no holiday calendar. So an agent that counted Saturdays, or skipped holidays it knew of, would fail the sweep. In paper-to-code the oracle, not the spec, decides what done means, and writing that oracle is the hard part.

### The reviewer: a linter first, then Gemini on your lane

The rubric, the request and the score; a linter in the reviewer's seat at Rs 0; then the model, three times over.

#### Definition

`commands/review_diff.py` makes one model call a diff. The request holds the diff, the spec it was written to and the definitions the code uses, as the kit holds them, each fenced as data rather than instructions, because a coding agent's patch is text a model wrote. The answer is held to a schema: a list of findings, each one rule of a 10-rule rubric, a line in the new file and one sentence saying why. A rule outside the rubric cannot be given. `make review-eval` runs the reviewer on seven diffs, each from the task's start: the kit's own function, where every finding is a false alarm, and the six seeds. The reviewer never sees a seed's name, label or why, only its diff.

A finding is scored by its rule alone. Per diff, the score counts the runs that found the seeded rule, how many of those pointed within 2 lines of the seeded line, and the false alarms. Then it counts the catch: the seeded defects found in each run. There is one seeded instance of each rule, so each figure is a rate per rule, not a recall.

#### The code

#### Do it: the linter, offline

Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names `NO_HOLIDAYS`. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3.

The linter found 5 of the 6. It has no pattern for a count that starts a day early, so it missed start_day_counted. It raised 7 false alarms a run, one on every diff, the kit's own function included: it reads the citation of s.17(3) as the wrong section. A reviewer who does not know the kit's convention makes the same mistake. The desk cites s.17(3) on purpose, because the appropriate Government may set another time limit. Your hand iteration's diff drew the same false alarm.

#### Do it: Gemini, on your lane

With `PROJECT`, `make review-eval` reviews the seven diffs with gemini-3.6-flash on location `global`, thinking low. It runs as you: a review reads a diff and calls no tool, so it uses your own sign-in, unlike the loop's agent. `REPEAT=3` reviews each diff three times, because a model's review differs from run to run. That is 21 calls, about Rs 5.48 of input (each request is 2,042 to 2,054 tokens by the kit's four-characters-a-token count), plus output and thinking, which the kit does not cap. `REPEAT=1` costs a third. `SAVE` keeps every finding with the model and the date, and `make review-eval FROM=` with that file rescores it at Rs 0.

Read the table one row at a time. The found column counts, out of the reviews of that diff, those that named the seeded rule: a rate on one planted instance. The false alarms column counts what it flagged that is not the planted defect, and on the kit's own function every finding is one. The panel at Level 0 shows the author's run beside the linter's, diff by diff. Neither is the oracle: the oracle runs the code, and a reviewer reads it. The page reports each one's numbers and names no winner. Your own diff can be reviewed the same way: `make review-diff PROJECT="$PROJECT" DIFF="$(dirname "$WS")/by-hand.patch"` is one call, about Rs 0.26 of input.

### The live loop: Gemini CLI in a container, on a model-only key

The image, the two containers, the refusals, the author's run, and how the key stays out of make and out of every log.

#### Definition

Live, each iteration is one `docker run` of the ralph image: Gemini CLI at the kit's pin (`GEMINI_CLI_VERSION` in `mk/coding.mk`), Python 3.12, a user of its own, and no gcloud, credential or kit file. The workspace is mounted at `/work`. The prompt and Gemini CLI's system settings are mounted read-only from the kit, outside the workspace, so an iteration cannot rewrite the next one's prompt. The command is `iteration.sh`: Gemini CLI headless with `--yolo`, which approves every tool call without asking. That is safe only because the container, not a person, is the boundary: no capabilities, a read-only root, memory and process limits, and no credential in its environment but the model key. The oracle runs from the same image in a second container, with no network at all and everything mounted read-only. Gemini CLI's flags, its settings keys and its stats' field names are the kit's reading for the pinned version, and the batch-1 probe confirms them before the live run.

#### The code

#### Do it: the two containers, printed

`DRY_RUN=1` prints the two `docker run` lines an iteration would run, and starts nothing: no Docker, image or key is needed.

#### Do it: the egress proxy, printed

By default the agent's container can reach whatever the machine it runs on can reach. `RALPH_EGRESS=proxy` holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: `commands/ralph/egress.py`, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with `HTTPS_PROXY` naming the proxy. The proxy opens a tunnel to `aiplatform.googleapis.com:443` and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's `iterations/`. The agent's line is the one above with two flags added, `--network` and `HTTPS_PROXY`.

The kit's tests run the proxy on your machine's loopback, with a stand-in in place of the model endpoint, and the loop against a stub Docker. A live Docker is the author's check. `make ralph-probe RALPH_EGRESS=proxy` needs no key and makes no model call. From inside the agent's container it tries example.com and 169.254.169.254, the metadata server's address, directly, then example.com and the model endpoint through the proxy. It also prints whether example.com's name resolved there: whether a name lookup leaves the internal network is Docker's to decide, not the proxy's.

#### Do it: the live loop on your lane

Without the author's cap and key, the live loop does not start. It has no default spend, and it runs only on a model-only key, never on your gcloud login or Application Default Credentials.

- Typed, not written. `read -rs` reads the key from the keyboard without echoing it, and because it is never part of a command line, it never enters your shell's history.

- Exported, never a make variable. `make ralph RALPH_API_KEY=...` would put the key on a command line, where `ps` shows it and history keeps it. `mk/coding.mk` never names it, and the kit's tests hold that.

- One file, for one iteration. `commands/ralph.py` reads the key from its environment and writes it, as `GOOGLE_API_KEY`, into one file created fresh with mode 0600 beside the workspace. Docker reads that file with `--env-file`, never `-e` on a command line. The file is deleted when the iteration ends, however it ends, and once more when the loop stops.

- Names, never values. The loop prints the env file's names, as the dry run shows ("values never printed"), and the kit's tests assert that the key appears in no line the loop prints and no file it writes.

- Model-only, and deleted. Inside the container the agent holds the key. That is why it can call the model and nothing else, and why the author deletes it after the run.

#### The author's run

The author ran the loop in Cloud Shell, which has Docker, with the image built in the same session (Cloud Shell's Docker storage does not outlive it). The cap came from a one-iteration dry run in batch 1. If the probe finds the key needs a project, `RALPH_PROJECT` adds `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION=global` to the agent's environment.

Then the reviewer, on the loop's own work:

Read the live run as you read the offline ones: for each iteration the item, the verdict, the lines, the tokens and the rupees; then the stop and its reason, what it spent at list price, and, after a pass, the other oracle's verdict on the same code. A live model writes versions of its own, so its iterations are not the script's. The reviewer read ralph.patch, the loop's work from the task's start. Its findings are a reading of that diff; the oracle's verdict in the loop is the test of it.

### Direct reads, and the human step

The run's record, read straight from its files, then a patch applied, tested and taken back out by you.

#### Definition

Everything the loop knew is in files: the commits, `fix_plan.md`, `GEMINI.md`, `summary.json` and ralph.patch. The first cell reads the strong offline run from step 5. The second prints `summary.json`'s rows. The author's capture is the same two cells, with `RUN` set to the live run.

#### Do it: the record

The state lives in files, not in a context window: three commits after the task's own, three plan items ticked, one line learned, and the loop's work as one diff of the function. `summary.json` is the loop's own record: for each iteration the verdict, the lines, the tokens and the rupees, and at the end the other oracle's verdict on the final code.

#### Do it: the human step

The loop's last word is kit.patch: its function against the kit's own. Applying it is yours to decide. You apply it in your clone, run the fast test, put the file back, and ask the strong oracle about the same patch. The cell does this with the weak run's kit.patch from step 5.

The fast test passed the hard-coded date, because in your clone `python shared/desk_calc.py --selftest` is the weak oracle. `make ralph-check PATCH=` ran the strong oracle on the same patch and failed it. So the human step is the fast test and the strong oracle together. The kit's docstring pairs the fast test with the kit's own tests instead, and they would catch it too: `commands/tests/test_ralph.py` holds the kit's function to the oracle's count on every day of 2026. Either way the decision stays with you: the loop never applies anything. `git apply -R` took the patch back out, and `git status --short` printed nothing. If a run's kit.patch is empty, the loop wrote the kit's own function byte for byte, and `git apply` refuses an empty patch, because there is nothing to apply.

### Why it is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own code and comments, then the bill and the gaps.

- A fresh agent, every iteration. Each iteration's state is in files and commits, which a person can read, not in a context window that grows until the model loses track of it.

- An oracle outside the agent's reach. The checks never enter the workspace. The oracle splices the agent's function into the kit's own file, so a weakened selftest or a test of the agent's own never reaches the verdict, and the loop undoes the first anyway.

- Counts, never answers. `oracle.md` carries the feedback line, never the detail: no acceptance check's expected value, and nothing of the candidate's own text. The selftest's FAIL lines are there too, because the agent's copy of the file prints them anyway.

- One answer key. The seeds are one-line substitutions on the kit's own function, and a seed whose line has changed stops the run with its name, so the key cannot drift from the code.

- A repository beside the workspace. The agent can neither see nor write `git/`, so a hook it writes never runs when the loop commits. The repository has no remote, and your global and system git config are ignored.

- Two credentials for two jobs. The reviewer reads a diff and calls no tool, so it runs as you. The loop's agent runs tools unattended, so it gets a key that can call the model and nothing else, which the author creates for a run and deletes after it.

- The same questions, wherever an agent acts. What may it change, what check decides it worked, who approves it, and how is it undone? Here the answers are one function, the oracle, you, and `git apply -R`. Lesson 10.11 designs an agent that acts on the running lane rather than on code, where the same four questions need answers of their own.

#### What it costs

Each point is read from the kit's code, and this page's build runs the offline ones, so this box changes when they do.

- The egress proxy is a switch, off unless you set it. Off, the agent's container can reach the network. Gemini CLI's web tools are excluded in its read-only system settings, and an iteration whose output names the kit's public copy is undone, but a fetch that the agent never prints is not caught. On (`RALPH_EGRESS=proxy`, step 8), the container reaches `aiplatform.googleapis.com:443` alone. The proxy holds the host, not the requests: what goes through a tunnel is TLS, and the key inside the container could call the model outside Gemini CLI's stats, which the rupee cap reads.

- The rupee cap is a soft cap. The first iteration always runs, and an iteration under way always finishes. One that costs more than the dearest so far can take the total past the cap. A live iteration cut at 900 seconds, or one whose agent printed no stats, stops the loop with its cost uncounted: read it in your lane's billing.

- A new file is kept. An agent's new file is listed in the run, not undone. It never enters ralph.patch, which carries `shared/desk_calc.py` alone.

- Offline, the oracle's guards are Python's. `make ralph-check` runs a change's code on your machine with the network and new processes refused inside Python. That is not a sandbox, as the kit itself prints, so judge only a change you have read.

- The live facts wait for the probe. Gemini CLI's flags, its settings keys, its stats' field names, its sign-in and whether it sends its calls through the egress proxy, the image build, and the commands that create the key are confirmed by the author's batch-1 probe, not by the kit's tests.

- A rate, not a recall. Each defect class has one planted instance, so the reviewer's numbers are rates per rule over its runs, and the linter flags s.17(3) on every diff.

### Verify it yourself: the checklist

Fifteen checks, each one step above, each with the value that proves it.

Nothing on your lane is configured. The offline runs wrote run directories under `/tmp`, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.10 Coding agents: a Ralph loop, an AI code reviewer and paper-to-code · v5.0

Next: Lesson 10.11 System design: incident auto-remediation.
