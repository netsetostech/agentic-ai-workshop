# Lesson 12.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_12.4_Self_Improving_WIX.html`, reviewed at blob `fcf9af549fca3593ee52b0f3b67f4f8ab8e6c593`. Learners read that page on the course site; this guide keeps its prose.

Lessons 12.1 to 12.3 changed the model behind DocuMind's answers. This lesson changes the words in front of it, starting from one answer that went wrong on your lane. A model may propose the change: one rule for the generator's prompt. A person accepts it, and the golden set gains the row that would have caught the answer. Then the gate judges the new prompt version on a revision that takes no traffic. Only then does traffic move. If the gate says no, the change goes back with git.

In this lesson you turn one production answer into a proposed rule and check it with the kit's own validator. You accept it as prompt version v4 and paste its golden row. Then lesson 11.2's `make gate` judges it, and either `make promote-gated` moves traffic to it or you roll it back.

- What makes self-improvement safe

- The words: production row, proposer, prompt rule, the check, prompt version, PROMPT_VERSION, reviewer, golden row, the evaluator, candidate, the gate, promote or roll back

- Before you run anything: set up the shell

- The answer that went wrong, and the row you write from it

- What the kit does with a prompt rule

- make improve: one rule from the row

- A person accepts it: v4, and its golden row

- v4 on a candidate, and the gate

- Before and after: the live URL and the tag URL

- Promote, or roll back

- The version on every usage row

- Optional: a rule worded past the phrases, gated

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn which steps of a self-improving loop a model may take and which belong to a person and to the gate, and how the kit stops a proposed rule from ever touching the rows that judge it. Then you will prove it on your lane: a production answer becomes prompt version v4, gated before it is promoted or rolled back.

### What makes self-improvement safe

A loop that learns from its own failures, with a person, the golden set and the gate around the one step a model takes.

Self-improvement, in production. An agent improves itself when its own failures feed a change to how it answers. Done carelessly, that loop is dangerous in three ways. A model that rewrites its own instructions can talk itself out of a rule. A loop that writes its own tests can always pass them. And a change that ships because it reads well has not been measured at all. The kit keeps the useful part, a model reading a failure and proposing a fix. It puts a person, the golden set and the gate around that step.

What may change, and how. Only rag-api's prompt, and only by adding to it. `generator.py`'s `SYSTEM` holds 5 numbered rules. A prompt version may add rules after them, numbered from 6, and v3, the default, adds none. The versions live in `services/rag-api/prompt_rules.json`, and the file is append-only: each version's rules begin with the rules of the version before it, unchanged. Which version a revision answers under is a setting, `PROMPT_VERSION`. So one image carries every accepted version, and each revision picks one. `/version` and every usage row name the version that answered.

Who does what.

- The model proposes one rule, on one line, and says why. It is sent the rules as they are served, the answer, and what a right answer holds. It writes nothing.

- You write the question in your own words, and say what a right answer holds: the golden row's shape, its figure and its anchor. You read the proposal and decide whether to accept it. You paste the golden row.

- The kit checks the row against the documents and the rule against `SYSTEM`'s rules before anything is written. It refuses to write the evaluator at all.

- The gate judges the new version on a revision with no traffic, with every golden row, the new one among them.

- Traffic moves only through `make promote-gated`, and only on a green record.

What a rule may never do. It may never undo one of `SYSTEM`'s rules. That means answering from outside the numbered context (rule 1), dropping the citations (rule 2), refusing less when the context does not hold the answer (rule 3), quoting a whole section (rule 5), or setting the rules aside. The kit refuses 58 phrases that say so, at Rs 0, matched as whole words. A rule worded past those phrases reaches the gate, and the gate measures what it does. `refusal_rate` must stay at or above 90% of the 18 rows the documents cannot answer, so if 2 of them are answered the gate is red. And each of `required.json`'s 15 rows must pass on its own.

A hospital's morbidity and mortality meeting. Once a month a hospital's doctors meet about the cases that went wrong. The team that treated the patient presents the case in its own words, with the patient's name left out. Anyone in the room may propose a change to the ward's protocol. The head of the department decides whether it is adopted. An adopted change is added to the protocol as a new numbered item, signed and dated, and nobody rewrites the old items in place. The audit standards the hospital is judged by are not written by whoever proposed the change. A new item is tried on one ward before the hospital takes it up, and it is dropped if that ward's audit gets worse.

The case is the production row, and leaving out the patient's name is writing the question in your own words, never a user's. The proposal is `make improve`'s rule, from a model or from you. The head of department is the reviewer. The new numbered item is v4's rule 6: append-only, with the reviewer and the date on it. The audit standards are the evaluator, which `improve.py` never writes. The trial ward is the candidate revision, the ward's audit is the gate, and taking the item up is `make promote-gated`. Dropping it is a `git revert`.

#### The loop, and what can stop it at each stage

Seven stages, each with the thing that can stop it beside it. Every value here is read from the kit when the page is built.

The values are the kit's: `prompt_rules.py`'s limits, `improve.py`'s list of the evaluator, `run_eval.py`'s thresholds over `golden.jsonl`'s 65 rows and the one you add, `required.json`, and the gate's rupees at lesson 11.2's typical answer of 2,000 tokens in and 300 out (Rs 0.45 each).

#### Write a rule, and see where it stops

Pick a rule or write your own. The first box says what `make improve`'s check says about it, and where it goes next. The second shows the prompt as the next version would serve it: `SYSTEM`, the rules added so far, and yours.

The check is `prompt_rules.py`'s `problems()`, ported to this page and compared with the kit's own on 122 rules when the page was built, every one of the 58 phrases among them. As `make improve` does, the page trims the rule before checking it. The prompt is `generator.py`'s `SYSTEM` and `DATED_RULE`, read from the kit and numbered the way `numbered()` numbers them.

It checks the words, as the kit does, and cannot see what a rule means. The rule "worded past the phrases" passes here and in `make improve` alike, though it asks for fewer refusals. Only the gate measures what a rule does to the answers. Tick the dated source on v3 with a rule that passes, and you see something the kit does on purpose: two rules numbered 6. Step 12 says why.

### The words: production row, proposer, prompt rule, the check, prompt version, PROMPT_VERSION, reviewer, golden row, the evaluator, candidate, the gate, promote or roll back

Twelve rows, each with the value it takes on your lane.

One distinction to hold: the check reads the words and the gate measures the answers. A rule the check refuses never costs a rupee. A rule the check passes has proved nothing yet, until the gate has asked every golden row of a revision that serves it.

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

### The answer that went wrong, and the row you write from it

A question your users' revision answers wrongly, the version that answered it, and the row that says what a right answer holds.

Find the answer. Ask DocuMind a question on the UI, as acme, whose answer is in acme's documents and comes back wrong. It might give the wrong figure, cite the wrong clause, or refuse where the handbook does answer. The UI asks the live revision, the one serving all the traffic, so this is the answer your users get. Each try is one answer, about Rs 0.45.

Your words, never a user's. The question goes into `build_golden.py` and your fork's history, so write it yourself. A usage row never carries the question. It names the tenant, the user, the tokens, the model and the prompt version, and the cell below shows that. If a user reports a failure, the row is your own question about the same fact.

Then ask the same question once more from the shell. The cell keeps the answer and `/version` in your home folder for the next cell, and reads the usage row the answer left in Cloud Logging.

What a right answer holds. This is lesson 4.1's golden row. A lookup or join row has a `must_contain` figure and a `must_retrieve` anchor, both in the tenant's documents. A refusal row has both lists empty, because the documents cannot answer it. Version, isolation and media rows belong to `required.json`, which lesson 4.1 writes by hand, and `improve.py` refuses those shapes. Set your values in the first two lines and run the cell. It writes `~/row124.json`, the file `make improve` reads.

The example question asks about notice during probation. PB-02 sets 15 days during probation, and NP-03 sets 60 days for a confirmed employee at grade E3 or above. The stand-in answer gives NP-03's sentence, word for word. The golden set already asks this fact in other words, as `lk-04`, and a set that holds one wording does not hold the others. Whether your lane gets this question wrong is for your lane to say. The answer above was written for the page, and the author's run uses a question that really failed on the lane.

### What the kit does with a prompt rule

The prompt and its one precedent, the two lines that add a version's rules, the check, the setting, and the one place `improve.py` writes.

The prompt, and its one precedent. `SYSTEM` is the literal below: 5 numbered rules. `DATED_RULE` is the precedent for a rule added after them. It is a sixth line, sent only when a packed source carries an effective date, so that `SYSTEM` itself stays the text `make_trainset.py` copies for the tuned models of lessons 12.1 to 12.3.

The two lines that add a version's rules. At the end of `generator.py`, `SYSTEM` is bound again, to `SYSTEM` with the version's rules appended. The binding goes through `globals()` so that the literal stays `SYSTEM`'s only assignment. `make prompt-version` (lesson 3.6) and the builds of the pages that quote `SYSTEM` read that assignment by AST, and a second `SYSTEM = ...` would break them. `generate()`, `generate_stream()`, `_budget()` and the gateway's two turns read `SYSTEM` when they run, so each one carries the version's rules.

What a rule may not say. Each entry of `FORBIDDEN` names one of `SYSTEM`'s rules, what it holds, and the phrases that would undo it. A phrase is matched as whole words, with case, spacing and curly apostrophes set aside. A match refuses the rule however reasonable the rest of it reads.

Numbered on, and refused when unknown. `numbered()` appends the rules after `SYSTEM`'s last, one a line, from 6, the way the prompt bench of lessons 3.1 to 3.3 numbers a rule it adds. Under v3 `with_rules()` returns the literal itself. `rules_for()` refuses any version the image does not carry, at import, so the revision never starts. Otherwise a typo, or an image built before the rule was accepted, would answer with `SYSTEM` alone while `/version` and every usage row named the version.

The file, and the setting. As the kit ships it, `prompt_rules.json` lists v3 with no rules. `config.py`'s two fields make the label; pydantic-settings reads `PROMPT_VERSION` from the revision's environment over the default. `/version` reports the label, and every usage row carries the version.

What `improve.py` may write. Exactly two things: `prompt_rules.json`, and a proposal, which is JSON and lives outside `services/`. The evaluator is everything a candidate is judged by. A step that could edit the rows that judge its own rule would be judged by nothing, so `write()` refuses the evaluator whatever path is asked for. The golden row is printed for a person to paste.

#### Check it yourself, offline

The kit's check on five rules: the page's example, the kit test's "never refuse", a rule worded past the phrases, a numbered one, and one that names rule 3.

Then the default prompt. `make prompt-version` is lesson 3.6's check: the sha256 of `SYSTEM` followed by `DATED_RULE`, against the registry. The cell shows that v3 serves `SYSTEM` itself, byte for byte the tuning set's copy, so a lane that never sets `PROMPT_VERSION` serves exactly what it served before.

### make improve: one rule from the row

What the proposer is sent, a row that could never pass, the proposal, and a rule that refuses less.

The target. `make improve` runs one script two ways. Without `REVIEWER=` it proposes a rule from `ROW=`. With `REVIEWER=` it accepts the proposal. `IMPROVE_ARGS` passes `--prompt-only` or `--rule`. The target has no `guard-project`, because accepting is offline and a model's proposal stops without `PROJECT`.

First, what the proposer would be sent. `--prompt-only` prints the request and stops, at Rs 0. It contains the rules as they are served today, the dated line, your row, and the phrases a rule may not contain. Before any of that, the row's figures and anchors are checked against the tenant's documents.

A row whose golden row could never pass stops at that check, and costs nothing:

Then the proposal. One call to `gemini-3.1-pro-preview` on the global endpoint, at its default thinking, under a JSON schema that asks for `rule` and `why`. Timeouts, 429s and server errors are retried with backoff, up to 4 attempts. The reply goes through the same check before anything is written. A rule that passes goes to `evals/reports/proposal.json`, which is gitignored, with the row, the version it builds on, and the call's tokens and rupees at list price.

Here is the shape of that output, from the kit's own code with a scripted proposer standing in for the model. That is how the kit's test runs it. The request is the one `--prompt-only` printed above, and the reply is the page's example rule. The token counts are the kit test's: 1,800 in and 1,360 out, 1,200 of them thinking, which is billed as output.

Propose the kit test's own bad rule as yours, with `--rule`. No model is called. The check finds "never refuse", which undoes rule 3, refuses the rule and writes nothing, and make reports the failure.

A rule that asks for the same thing in other words passes this check, as the panel in step 1 shows. Step 11 sends one to the gate.

### A person accepts it: v4, and its golden row

The next version, written with who and when, the golden row pasted by lesson 4.1's method, and the files `improve.py` refuses to write.

Read the proposal, then accept it. `REVIEWER=` is you: a name or an email, on one line. It is written into `prompt_rules.json` and your fork's history, so use the name you sign your commits with. Accept checks everything again: the proposal must be one `make improve` wrote, built on the latest version, with a row whose facts are in the documents and a rule that passes the check. Then it writes the next version, prints the golden row, and lists the way on.

Accept added one version to the file and changed nothing else in it. The version's rules begin with v3's (none) and add yours. Its id, `lk-32`, is the next free id of the row's shape, in `build_golden.py`, in `golden.jsonl`, and in any version that printed a row not yet pasted.

Accept's last lines say the gate wants `refusal_rate` at 90% "over the 18 rows the documents cannot answer": the denominator `run_eval.py` divides by, the 8 refusal rows and the 10 isolation rows whose `answerable` is false, 18 in all (until 13 October 2026 the line counted the 8 refusal rows alone, and the two disagreed). It takes 2 of the 18 answered to turn it red, where over the 8 refusal rows alone it would take 1.

Paste the golden row. This is lesson 4.1's method: the row goes into `build_golden.py`, never into `golden.jsonl`, before the `]` that closes `GOLDEN`. Paste it by hand in the editor, or with this cell, which does exactly that and nothing else. Then the builder checks the row against the documents and writes `golden.jsonl`, and `make eval` runs the offline gate over the set.

The writes `improve.py` refuses. Ask its `write()` for each file of the evaluator, a document under `corpus/` and `demo/`, and `generator.py`. Each one is refused before anything is opened.

### v4 on a candidate, and the gate

One commit, the image that carries it, a revision with no traffic that answers as v4, and every golden row asked of it.

The target. `make prompt-candidate` is `make release-candidate`'s update with one more variable: `PROMPT_VERSION` beside `GIT_SHA`. Before any gcloud call it runs `improve.py version`, which stops on a version `prompt_rules.json` does not list. Then `make record-candidate` writes the new revision's name to `.candidate-revision`, the name `make gate` and `make promote` read. `config.py`'s default stays v3, so v4 answers only where the variable is set.

The check runs offline, and you can run it yourself. The cell reads the version accept wrote as `PV`, and every cell after it uses `$PV`. This page's run wrote v4. On a lane where lesson 3.6 committed its v4, accept writes v5, because it takes the version after the highest that any commit in your history has registered, so a label is never given a second meaning. The commits pass your name as `$ME`, as 3.6's did, so they work on a shell with no git identity of its own.

A revision whose image does not carry its version does not start. If `PROMPT_VERSION` names a version that the image's `prompt_rules.json` does not list and lesson 3.6's registry does not hold, `generator.py`'s last line raises at import, and Cloud Run keeps the traffic where it was:

Commit, build, and make the candidate. The commit holds the new version and its golden row together, because the gate judges them together. `make build` pushes the API image tagged with that commit, so the image carries v4. The last line reads the variable back from the revision itself.

The gate. `make gate` is lesson 11.2's, unchanged. It judges the revision `.candidate-revision` names, once the candidate tag routes to it and its `/version` answers as its `GIT_SHA`. Its first lines print the prompt label the tag URL answers as, which should be v4's. Then `run_eval.py` asks every golden row of the tag URL, the one you pasted among them, and the record binds the verdict to that revision and to the files it was judged by (lesson 11.2). A rule that slips past the phrases and refuses less meets `refusal_rate` here.

### Before and after: the live URL and the tag URL

The same question to the revision your users reach and to the candidate, with the label each one answers under.

Two addresses, one service. The UI reaches only the live URL, so it cannot show you the candidate before it is promoted. The tag URL reaches the candidate directly. The token is minted for the service's canonical URL and works on both, as lesson 11.2's gate uses it. `GET /version` names the label each one answers under, and the same question goes to both.

What to look for: `documind-rag@v3` on the live URL and `documind-rag@v4` on the tag URL, each with its own `git_sha`. Then two answers to one question, the live one as wrong as it was in step 3, and the candidate's as your rule should make it. If the candidate's answer is still wrong, the rule did not fix the case it came from, whatever the gate said about the other rows. Do not promote it.

### Promote, or roll back

A green record moves the traffic to the candidate. A red one moves nothing, and the version goes back with git.

Green. `make promote-gated` runs lesson 11.2's `gate-check` on the record, then the unchanged `make promote`. That writes the revision serving now to `.previous-revision`, moves all the traffic to the candidate by name, and prints `/version` from the live URL. Ask the question on the UI again afterwards: the UI now reaches v4. The cell asks it once more from the shell. If anything looks wrong later, `make rollback` returns the traffic to the revision in `.previous-revision`, which never went away.

Red. No promote. No traffic reached v4, so you can drop it without changing any version that has served. Revert the commit that holds v4 and its golden row; the next rule you accept builds on v3 again. `PROMPT_VERSION=v4` is still in `documind-api`'s template, because an update with `--no-traffic` still writes it. Any later candidate made from an image without v4 would carry the variable and refuse to start. So build the reverted commit and put v3 back with `make prompt-candidate`, which makes a new candidate with no traffic.

The author's run took one of these two paths, and the recording above shows which.

### The version on every usage row

Cloud Logging's rows, grouped by the version that answered, and what the new line costs on every answer.

The rows, by version. Every answer leaves a usage row, and each row carries `prompt_version`, the excerpt in step 4. `make usage` groups the rows by tenant, model, brain, surface and retrieval backend, but not by version, so this cell reads the same rows with `make usage`'s own `read_rows()` and groups them with its own `group()`, keyed by `prompt_version`. The gate's answers on the candidate are v4's, and the live answers before the promote are v3's.

What the line costs. Your rule rides on every answer as input tokens. The page's example line is 37 tokens by the kit's own estimate (`len // 4`), about Rs 4.7 per 1,000 answers at gemini-3.6-flash's input price. If nothing else asked in between, the newest v3 row and the newest v4 row answer the same question: step 8's live answer, and the candidate's (or step 9's, after a promote). The question and the sources are the same and only the rules differ, so their `tokens_in` should differ by about the real count of your line.

### Optional: a rule worded past the phrases, gated

A rule that asks for fewer refusals in words the check does not know, accepted, built, and sent to the gate.

What the check cannot see. The rule below asks the assistant to give "the closest answer it supports" instead of saying the context does not cover the question. None of the 58 phrases is in it, so `make improve` accepts it, as the panel in step 1 does. Its meaning reaches only the gate. There, `refusal_rate` counts the 18 rows the documents cannot answer, and 2 of them answered turn it red. Do not paste the golden row accept prints this time: the question is in the set already. The commit holds the version alone, and the next cell takes it back off.

The recording is the author's. If the gate passes this rule anyway, that is the result, and it says something too: neither the check nor these rows caught it. The way out is more rows the documents cannot answer, written by lesson 4.1's method.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own code and comments, then the bill and the gaps.

Versions only grow. An accepted version is never edited, so a usage row's `prompt_version` names one text forever. A version the gate turns down goes with a `git revert`, because no traffic reached it. Accept refuses a proposal made on an older version, so two people cannot both write a v4.

The version is a setting, not the code's default. `config.py` stays at v3. `make prompt-version` hashes `SYSTEM` and `DATED_RULE` and nothing else, so on a kit with v4 accepted it gives the same verdict as before. A rules version made the code's default would be checked against the wrong text. The tuned models of lessons 12.1 to 12.3 also keep the prompt they were trained behind wherever v3 serves.

Two rules numbered 6. `DATED_RULE` is written with its own number, 6. Under v4, a context with a dated source carries your rule 6 and then the dated rule 6. The kit's author kept it that way on purpose: the prompt bench's edit arm already produces the same, and its parser needs consecutive numbers, so starting the version's rules at 7 would break the bench.

A cached answer belongs to its version. The answer cache's scope includes the prompt version. So a v3 answer stored before the change is never served as v4's, and the gate cannot be handed v3's answers. The cache is off on the lane until its threshold is measured; when it is on, the scope keeps the versions apart.

The proposer is told the rules it must keep. The request lists every forbidden phrase, and the check runs on the reply anyway. The proposer also sees the rules as they are served, with the dated line beside them, so it can see what the prompt already says.

#### What it costs

A pass through this lesson on the author's lane is about Rs 34: 5 answers outside the gate, one proposal and one gate. Step 11's optional gate brings it to about Rs 63. Each wrong answer you try in step 3 adds about Rs 0.45.

- The change lasts only while the variable does. `make deploy-services` sets `documind-api`'s environment whole, from a list that has no `PROMPT_VERSION`. The next routine deploy therefore serves v3 again, with no error: lesson 11.7's gotcha of a setting made by hand that a routine deploy drops. Run `make prompt-candidate PROMPT_VERSION=v4` again afterwards, then gate it and promote it.

- The template keeps the variable. After a candidate that is never promoted, `PROMPT_VERSION` stays in the template, and `make release-candidate` and `make candidate` carry it to their revisions. `make prompt-candidate PROMPT_VERSION=v3` puts the default back.

- Only rag-api's prompt. The chat service's brains keep a prompt of their own (`services/chat/brains.py`), which this loop does not version.

- Accept counts the wrong rows. Its last lines name the 8 refusal rows, but `refusal_rate` is judged over 18 rows (step 6).

- No table by version. `make usage` does not group by `prompt_version`; step 10's cell does.

- Unverified until the author's run: the google-genai call itself (`response_json_schema`, the retry options and the default thinking's cost), a v4 revision starting with `/version` showing `documind-rag@v4`, and lesson 11.2's gate accepting the candidate.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it on your lane. The last is for step 11, if you ran it.

In your fork, one commit holds v4 in `prompt_rules.json`, with your name, the date, the proposer and the golden row's id, and that row in `build_golden.py` and `golden.jsonl`, 66 rows now. A revert commit follows it if the gate was red. `evals/reports/` holds the proposal, the gate's record and its report, all gitignored. `documind-api` has a revision built from that commit with `PROMPT_VERSION=v4`. It serves all the traffic if you promoted it, with `.previous-revision` naming the one before. If you did not, a v3 candidate followed it with no traffic. Cloud Logging holds the usage rows of about 66 gate answers and your own. The next `make deploy-services` drops the variable, and the service answers as v3 again until you put v4 back the same way.

Netsetos GenAI on GCP · Module 12 Tuning · Lesson 12.4 Improve the agent safely: eval-gated self-improvement · v5.0

This is the last lesson of the course. Lesson 11.8, Complete the independent capstone and operational handover, is where your lane is checked and handed on.
