# Lesson 3.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.2_CoT_Few_Shot_WIX.html`, reviewed at blob `9d08b333f5364f71179e7d150f0b9463217dd55e`. Learners read that page on the course site; this guide keeps its prose.

Two ways to get a better answer from the same model. Chain of thought gives the model room to work before it answers. A Gemini 3 model does that natively: it writes thought tokens before its reply, which the kit never asks to see and pays for at the output rate, and the generator asks for little of it, thinking level LOW. A prompt can also ask for the working in writing, and under DocuMind's answer schema the working has one place to go: the answer the person reads. Few-shot puts solved examples in the prompt: the router's first classifier, `gemini-3.1-flash-lite` with a thinking budget of 0, reads eight questions, each labelled with its desk. You will take a join apart in the page, see what the Chat page shows of the thinking and what it bills, read where each technique lives in the kit, then measure both on your lane: the 11 join rows at LOW, MEDIUM and HIGH, one prompted-reasoning rule against native thinking, and the router's examples taken out and put back over 187 scored questions, every rate with its interval.

- Two ways to help a model answer: room to think, and solved examples

- The words: chain of thought, thinking level, thought tokens, prompted reasoning, zero-shot, few-shot, join row, arm, interval, L1 alone

- Before you run anything: set up the shell

- The Chat page: the answer to a join, and the thinking it billed

- Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench

- The pool the bench holds fixed: /v1/passages for jn-03

- Chain of thought, measured: the join rows at LOW, MEDIUM and HIGH

- Change it: one prompted-reasoning rule against native thinking

- Few-shot in the kit: the examples, the swap and the offline arms

- Few-shot, measured: the examples taken out and put back on your lane

- Direct reads: the two reports, turn by turn

- Verify it yourself: the bill and the checklist

You will learn the two prompt techniques the kit uses, native chain of thought in the generator and few-shot examples in the router's classifier, where each one's cost shows up, and why 11 rows cannot tell two thinking levels apart unless their pass counts are at least six rows apart. Then you will measure both on your lane with the prompt bench and the router's eval, with nothing deployed.

### Two ways to help a model answer: room to think, and solved examples

Chain of thought, native or prompted; few-shot against zero-shot; and why each is measured on the same rows with its interval.

Chain of thought is work written before the answer. A model writes one token at a time (lesson B.5), so whatever it writes before its answer is something the answer can build on. Golden row jn-03 asks "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" The answer needs two clauses and one step between them: the handbook's cap on leave encashment, the notice period for an E3, and the question's 50 days held against the cap. That is the bet chain of thought makes: a model that works those out first may get them right more often than one that starts writing the answer at once. Step 6 measures whether it does here. A Gemini 3 model does this natively: before its reply it writes thought tokens, billed at the output rate whether or not anyone reads them. `thinking_level` sets how much: MINIMAL, LOW, MEDIUM or HIGH. MEDIUM is `gemini-3.6-flash`'s default (lesson B.5 reads Google's model page), and the kit's generator pins LOW. Its request names the level and nothing else, so the thoughts never come back to the kit: only their count does.

Prompted reasoning writes the working where the person reads it. Before models thought natively, the way to get a chain of thought was to ask for it in the prompt, "work it out step by step", and let the model write its working into the reply. You can still do that, and it is the one change step 7 makes. In DocuMind it has a cost the textbook version does not. The generator asks for a `ModelDraft`, four fields, and google-genai sends them to the model in a fixed order: `answer`, `citations`, `confidence` and `answerable`. None of them is for working. So working that the prompt asks for is written into `answer`, the text the Chat page shows. It is billed as visible output and counts toward rule 4's 300 words. Native thinking happens before the first field; prompted working happens inside it.

Few-shot shows the task instead of only describing it. A zero-shot prompt describes the task and its rules. A few-shot prompt also shows solved examples, each an input with the right output, and the model continues the pattern. The kit uses each where it fits. The generator's `SYSTEM` is zero-shot: five rules and no example, because every answer is different and so is every context. The router's first classifier, L1, is few-shot. It is `gemini-3.1-flash-lite` with a thinking budget of 0, an answer of five enum fields and no room to explain. It reads the desks, the rules and eight example questions, each labelled with its desk (`desk_routes.PROMPT_EXEMPLARS`, at most twelve). Choosing one label out of five suits examples: a small model that does not think can copy the boundary the examples draw, between a handbook question and a statute one, or between the company's own question and another system's. Lesson 10.4 builds the router; this lesson takes its examples out and puts them back.

Measure each on the same rows, with an interval. A technique that helps on the question you tried can hurt on the next one, so the kit measures every change over a set of rows and prints every rate with its Wilson interval. On the 11 join rows, 11 of 11 passing has the interval [74.1%, 100.0%]. Two levels' intervals stop overlapping only when their pass counts are at least six rows apart, and at that gap only at the two ends of the scale: all 11 against 5, or 6 against none. So one run per level settles little about accuracy, while the thought tokens and the rupees per answer show up at once. The router's L1 sees 126 turns a run, so its intervals are narrower. Both arms answer the same turns, so the turns that one arm gets right and the other gets wrong (step 10) say more than the two rates side by side. Lesson 3.1 measures how far one row's answer moves from run to run.

The new clerk at the HR helpdesk. A new clerk gets two kinds of help. For the hard question, "I am leaving with fifty days of leave: what do I get, and how long do I stay?", the supervisor says take a minute. The clerk works it out on a scratch pad, the pad goes in the bin, and the employee gets only the answer slip. The office pays for the clerk's minute whether or not anyone reads the pad, and a longer minute costs more: that is thinking, and its level. Or the supervisor says write your working on the slip. Now the employee reads the working, the slip is longer and costs more to write: that is prompted reasoning. At the sorting tray, where each letter goes to a counter, the supervisor does something else. Eight letters from last month are pinned above the tray, each stamped with the counter it went to, and the clerk sorts the next letter by its likeness to them: that is few-shot. To know whether any of it helps, the office manager does not ask the clerk. She runs the same files both ways and counts, and she knows that eleven files cannot tell a careful clerk from a lucky one.

#### A join, taken apart: what the answer needs from the documents

A join row is a golden question whose answer needs two facts. Thinking does not find a fact the pool lacks; it helps the model put found facts together. Pick one of the 11 rows. The panel shows what the eval gate requires the answer to say (`must_contain`, matched by run_eval's `contains()`: the figure on its own boundary, in any spelling of the number), the anchors the row names (`must_retrieve`), and, for each figure, the anchored passage that holds it, with the sentence that says it.

Of the eleven join rows, the figures of four (jn-01, jn-03, jn-06 and jn-10) sit in two passages and those of the other seven in one. In jn-08 and jn-10 a figure the gate wants is already in the question. jn-02 names NP-03 and LV-07, and only LV-07 says "cannot": NP-03 says the same in other words, "may not be set off". jn-04 is asked as globex, which cannot see ACME's agreement. The passages are cut by `shared/documind_corpus.py`, which chunks by the ingest worker's two rules (2,000 characters with 200 of overlap, and a handbook cut section by section), from the corpus's text mirrors, when this page was built. A PDF's mirror keeps its page headers and broken words, so its passages read raggedly; the panel shows them as cut. Your lane's worker reads a PDF with Document AI, so its passages may break at other places. Step 5 reads the pool your lane really returns for jn-03.

Take jn-03. LV-07 says "Earned leave is encashed on exit at basic pay, capped at 45 days." NP-03 says "A confirmed employee at grade E3 or above serves a notice period of 60 days." The gate wants 45 and 60 in the answer, and neither clause alone gives both. One step joins them: the question's 50 days against LV-07's cap, so the cap is what is encashed. A careful answer also names the condition NP-03 puts on its 60 days, a confirmed employee, which the question does not state. Native thinking and a prompted rule are two ways to give the model room for that step. Steps 6 and 7 measure each.

#### The router's prompt, with and without its examples

The other technique, in the kit's own prompt. `desk_router.prompt()` builds the L1 classifier's prompt: the task, the five desks each described by the documents it owns, six rules, the examples, then the question, fenced as data. Turn the examples off: the swap that `route_eval.py --exemplars none` makes takes out exactly the eight example lines, and nothing else moves. Each question in the list is a scored dev row that reaches L1 in the kit's offline run; none is in an example's group.

20 dev rows sit in the examples' groups: an example's own row, the golden row it rewords, and that row's paraphrases. Every arm's score leaves them out and scores the other 187: statute 129, handbook 44 and out_of_scope 14. Of those, 52 are decided by an anchor and 9 by globex's single desk before any model is asked, so L1 sees 126 (statute 73, handbook 44 and out_of_scope 9). The examples cover handbook (3), statute (3) and out_of_scope (2); case and clarify have none, and the route set's 207 rows, all on the dev split, include no case or clarify row either. The token counts are the scripted classifier's, characters divided by four (`route_eval.py --local`); the real count is the model's.

### The words: chain of thought, thinking level, thought tokens, prompted reasoning, zero-shot, few-shot, join row, arm, interval, L1 alone

Thirteen rows, each with where it shows on your lane.

Two of these words carry the lesson's first half: thought tokens and visible tokens, the two parts of every answer's output bill. Native thinking moves the first, a prompted rule moves the second, and step 7 shows both in one table. The second half rests on held-out groups: an example the prompt has seen cannot also be a question it is scored on.

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

### The Chat page: the answer to a join, and the thinking it billed

jn-03 asked the way a person asks it, and the one usage row that says what the answer cost.

#### Definition

The Chat page's direct brain posts the question to `/v1/stream` with `top_k` 5. The stream retrieves and reranks as `/v1/query` does, then answers through `generate_stream()`: the same model, the same `SYSTEM` and the same thinking level, LOW, but no response schema, so the answer streams as plain text. What the page draws is the answer and its sources. The thinking is not in the stream, because the request names a level and asks for nothing back. It is in the bill. The stream's usage row carries `tokens_out`, which `generator._usage()` makes by adding the thought tokens to the visible ones, and the row's `cost_usd` prices all of it at the output rate.

#### Do it: jn-03 in the Chat page, then its row

In the Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Read the answer: the eval gate would want 45 and 60 in it. Then read the API's log for the last ten minutes.

The page showed an answer and its sources, and nothing of how the model got there. The row says what that cost: `tokens_out` is the answer you read plus the thinking you did not, both at the output rate of USD 7.50 a million tokens on `gemini-3.6-flash`, five times the input rate. The row cannot say which part was which. The bench in step 6 can, because it keeps the two counts apart.

### Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench

Where the generator sets its thinking, why prompted working can only land in the answer, and how the prompt bench changes either without touching generator.py.

#### Definition: the generator's thinking

`_call()` sends one `generate_content` with the structured-answer config. Two of its settings are the cap and the thinking: `max_output_tokens`, 2,048 unless the retry asks for three times that, and `thinking_level` LOW. The comment between them says why there is no temperature, and why the kit names a level rather than a budget of zero. `_usage()` then bills each attempt: the thought tokens join the visible ones in `tokens_out`, the figure every usage row and the month's budget counter read. Lesson 3.5 reads the rest of the call.

#### Definition: the answer's shape has no field for working

`ModelDraft` is what the model is asked to return: an answer, its citations, a confidence, and whether it could answer at all. When google-genai turns the class into the request's schema, it lists the fields in their declared order, as `property_ordering` `answer, citations, confidence, answerable`, so the reply's first field is the answer itself. (Checked when this page was built, with google-genai 2.28.0; rag-api pins 2.22.0.) A model that thinks has done its working by then, in thought tokens. A model asked to show its working has one place to write it: inside `answer`.

#### Definition: the generator's prompt is zero-shot

`SYSTEM` is five numbered rules and no example. `generate()` starts every prompt with it, adds `DATED_RULE` as a sixth rule only when a packed passage carries an effective date, then appends the packed context and the question. Nothing in it shows a solved question, and nothing asks for the working: what the model works out before it answers is left to the thinking level.

#### Definition: the prompt bench

`evals/prompt_bench.py` asks the kit's own `generate()` the same question at each level you name, from one fixed pool. Each row's pool is read once from your lane's `/v1/passages` before any answer is asked; step 5 reads one. Each answer goes through a recorder that stands in for `generator._client`. It sends the request as `_call()` built it, with the level being benched in place of LOW, and keeps the config as sent and the usage, the thought tokens apart from the visible ones. The kit arm at LOW is therefore the API's own request. A rule added with `--add-rule` changes `generator.SYSTEM` in memory for the edit arm's answers only, and the kit's text goes back after, so generator.py is never written. Every answer is judged by the eval gate's own `row_verdict()`, and every quote is checked against the row's pool. `make bench` mints the API's token as `documind-ui-sa` and runs the script; without make, set `DOCUMIND_ID_TOKEN` and `GOOGLE_CLOUD_PROJECT` yourself.

#### Do it, offline: the edit arm's prompt, before you pay for it

Step 7 adds one rule. This cell builds the edit arm's `SYSTEM` with the bench's own `edit_system()`, from generator.py's text read as data, since importing generator.py builds a Gemini client for your lane. Then it hashes both prompts as the bench's header does, `SYSTEM` followed by `DATED_RULE`, the text lesson 3.6 binds to a version, and looks each hash up in the kit's registry of prompt versions. No model is called.

#### Do it, offline: the bench's and the swap's own tests

The two test files run the bench on a scripted model and a stand-in lane, and the router's example swap on its scripted classifier. They check the level and the temperature sent, the rule edited in memory with generator.py untouched, the gate's verdict on every answer, the rupees, and the swap put back whatever happens. The pipe keeps the summary lines.

You read the two places a chain of thought can live in DocuMind. The thinking is one setting in `_call()`, billed through `_usage()` and never returned. The working has no field of its own, so a rule that asks for it puts it in the answer. The edit arm's prompt is the kit's five rules and one more. Its hash, 3f23ad647176d4fe..., is a text no version names yet; the kit's, 543ed8060f1b177c..., is the one `services/rag-api/prompt_versions.json` registers as `documind-rag@v3`.

### The pool the bench holds fixed: /v1/passages for jn-03

The retrieval half of /v1/query and nothing after it: the passages a join's answer is written from, with no model call.

#### Definition

`POST /v1/passages` runs the same door, roster, retrieval and rerank as `/v1/query`, then returns the pool itself, each passage with its full text, and writes a usage row with no tokens and no cost. The bench reads each row's pool here once, with the body `run_eval.ask()` sends, `top_k` 6, and every arm, level and run answers from that pool. A difference between two of its answers is then the prompt's or the model's, never retrieval's. A row whose pool comes back empty is not benched: `/v1/query` would refuse it with no model call.

#### Do it: jn-03's pool, and where its two facts sit

The curl saves the route's reply. The Python cell lists the passages and checks them with run_eval's own rules: which passage holds each figure the gate wants (`contains()`), and whether each anchor the row names is in the pool (`anchors_found()`, the rule `DOCUMIND_EVAL_PASSAGES=1` uses).

You read the evidence before any model saw it. When both clauses are in the pool, as LV-07 and NP-03 should be for jn-03, a wrong answer is a failure to join them, and that is what thinking can help with. When an anchor is missing, no level of thinking can supply its figure, and the fix is retrieval's, lessons 2.1 to 2.5. The bench reads this pool once and holds it fixed for the three levels of step 6 and both arms of step 7.

### Chain of thought, measured: the join rows at LOW, MEDIUM and HIGH

11 rows, three levels, one answer each: what the gate accepts, how much each level thought, and what it cost.

#### Definition

`--shape join` names the 11 join rows, in golden.jsonl's order, and `--levels LOW,MEDIUM,HIGH` asks each of them at each level: 33 answers, one `generate()` each, from 11 pools read first. The answers are interleaved row by row, so a slow minute on the lane falls on every level alike. Nothing else changes between the levels: the same prompt, schema, cap and pool. Read the summary table column by column:

- pass: k of 11 with its Wilson interval. Read it against step 1: unless two levels' counts are six or more apart, their intervals overlap.

- thought and visible: output tokens per answer, every call of it counted. The thought column is what a level buys.

- Rs/answer: at list price from `shared/prices.py`, the thought tokens at the output rate.

- distinct and cite sets: different answers within a row across its runs. With one run per level each row has one answer, so they equal the answers that came back, 11 of 11 when none errored, by construction; lesson 3.1 runs one row five times to fill them.

- retried, a line under the table when it happens: answers cut off at the 2,048-token cap and asked again with 6,144. The thinking and the answer share one cap, so a level that thinks more can run out of room, and the retry bills both calls.

#### Do it: the join rows at three levels

The same eleven questions, from the same eleven pools, at three levels of native thinking. Read the thought column first: it is what each level bought, and the rupees follow it, since thought tokens are output. The visible column should stay close across the levels, because the answer's shape is fixed. The pass column is one sample a level, so read the rows whose verdict changed, not the rate. The bench ended by checking that generator.py was unchanged on disk. The kit stays at LOW unless a measurement like this one, repeated, shows another level answering more rows right for what it costs.

### Change it: one prompted-reasoning rule against native thinking

The kit's prompt, and the same prompt with one rule asking for the working, both at LOW in one run.

#### Definition

The edit arm's sixth rule is the one step 4's offline cell printed: Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them. Both arms answer at LOW, row by row in the same run, so the difference between them is the rule's alone. Set the two arms beside step 6's levels:

- visible: the rule's working is written into the answer, so this is the column the rule moves. Native thinking moved the other one.

- thought: whether the model, asked to write its working, also thinks more or less before it.

- pass: a longer answer is still judged by the gate's rule. Its figures must still stand on their own boundaries, and every citation must still name the company's own current documents.

- quotes: rule 5, a quote of at most twenty-five words, is unchanged, and the quote lines under the table say whether the quotes still sit in the passages they cite.

The kit arm at LOW is step 6's first level asked again. Its verdicts may differ from step 6's on a row or two. That is run-to-run variance, lesson 3.1's subject, and it is why the edit arm is compared with the kit arm of its own run.

#### Do it: both arms, with every answer kept in a report

#### Do it: jn-03's two answers, from the report

The report keeps each answer's first 600 characters, its calls and its quote checks. The cell prints jn-03's answer from each arm, so you can see where the working went.

- Shipped, the rule would not be alone at number 6. The bench never adds `DATED_RULE`, because `/v1/passages` returns no effective date. On the lane, a pool with a dated passage gets `DATED_RULE`, also numbered 6, after the added rule.

- Shipping a rule is a new prompt version. The edit arm's hash is not the one registered as `documind-rag@v3`. Lesson 3.6 registers a new version before a changed prompt ships.

- SYSTEM is held equal to the tuning data's copy. `evals/make_trainset.py` carries the same text, so a tuned model is served behind the prompt it was trained behind (lesson 12.1). That is one more reason the bench edits in memory.

- The stream has no schema. The Chat page's answer is plain text, so a rule's working would stream straight to the person, with nothing to keep it apart from the answer.

One run, two prompts, one level. The rule's working shows where step 4 said it would: in the visible column, and in jn-03's answer text, which a person would read. Whether it passed more rows than step 6's higher levels did, and at what price an answer, is the comparison the two tables make. Lesson 3.3 uses the same `--add-rule` to fix failing rows one rule at a time.

### Few-shot in the kit: the examples, the swap and the offline arms

The eight triples, the prompt that reads them, the classifier that does not think, the swap that takes them out for one run, and both arms run offline.

#### Definition: the examples and the prompt

`PROMPT_EXEMPLARS` is a tuple of (row id, desk, question) triples from the route set's dev rows: tenant-neutral, with no company name and no figure, as its module's docstring requires. `prompt()` puts them after the rules as `>> desk` lines, in the same fence the question itself arrives in, and reads at most twelve. L1's request leaves the model no room to reason: a thinking budget of 0, and an answer of enums and booleans only, which lesson 10.4 reads in full.

#### Definition: the swap, and what it scores

`--exemplars kit|none|FILE` works only on the router in process (`--local` or `--live-l1`), so the deployed chat service is never touched. `exemplars_in_prompt()` swaps `desk_router.PROMPT_EXEMPLARS`, the name `prompt()` reads, for the run, and puts it back in a `finally`. `prompt_groups()` reads `desk_routes`' own tuple, which the swap never touches, so both arms leave the same 20 rows out and score the same 187. After the usual report the run prints "L1 alone": `l1_alone()` counts L1's own route on the turns it was asked, before the vote and the arbiter can repair it, which is where the examples act. Every rate is `rate()`'s: k of n with its Wilson interval.

#### Do it, offline: the swap, and the rows it scores

#### Do it, offline: both arms on the scripted classifier

`LOCAL=1` runs the same eval with `route_eval.py`'s scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

The swap took the eight lines out and put them back, and the scored rows did not move. Offline the arms agree: L1 alone 106/126 = 84.1% [76.8%, 89.5%] in both, top-1 route 186/187 = 99.5% [97.0%, 99.9%]. Only the router's cost moved, from Rs 3.8411 to Rs 3.4761. That Rs 0.3650 a run is what the examples cost in prompt tokens at the scripted count: about 136 tokens on each of 126 calls to `gemini-3.1-flash-lite`. On your lane the classifier is a model, and the examples can change its answers. Step 9 measures whether they do.

### Few-shot, measured: the examples taken out and put back on your lane

The same 187 rows with the real classifier, first with the kit's examples, then with none: L1 alone and the whole cascade, each with its interval.

#### Definition

`--live-l1` runs `decide()` in your shell with the real models on your project: `gemini-3.1-flash-lite` for L1, `gemini-3.6-flash` for the arbiter at thinking level LOW, and `text-embedding-005` for the vote, after embedding the 198-row exemplar index once. It needs google-genai in the shell, which Module 0's venv has, and no deployed Desk: a Module 3 lane is enough. `make exemplars PROJECT=$PROJECT REPORT="$HOME/exemplars_kit.json"` runs exactly the first cell's line. Each arm keeps its report, because step 10 reads every turn's decision from the two. Run the kit arm first, then none: the first run is the prompt as it ships, the second the examples taken out, and the shipped prompt never stopped serving.

- L1 alone: the examples' direct effect, on the 126 turns L1 is asked.

- top-1 route accuracy: the whole cascade's, on all 187 rows. The vote and the arbiter can repair a wrong L1, so this moves less.

- sent to L2: how often the signals disagreed and the arbiter was asked.

- router cost: L1's and L2's calls at list price, thought tokens included; the embeddings are not in it.

The run ends with lesson 10.4's dev gates: 95% route accuracy and 90% on each desk. Below them it prints `FAIL` lines and exits 1. Here that is a reading, not an error: this lesson compares the two arms, and lesson 10.4 decides whether the router ships.

#### Do it: with the kit's examples, then with none

The same rows, the same index and the same models, with and without the eight lines. "L1 alone" is the number the examples move directly; the route accuracy is what a person would feel, after the vote and the arbiter. If the two arms' intervals overlap, the rates alone cannot tell the arms apart, and the route set's rows are still model drafts, so any difference here is indicative. Nothing on the lane changed: the swap lived in your shell's process, and the deployed router still reads its eight examples.

### Direct reads: the two reports, turn by turn

Every decision the two runs logged, paired by row: the turns where the examples changed L1's route, and what those turns alone can say.

#### Definition

Each report holds the run's examples, its tally and one decision a row, as `desk_router.record()` logs it: L1's answer, the vote, the arbiter and the method, with no question text. Two runs on the same rows are not two samples. A turn both arms get right, or both get wrong, says nothing about the examples; only the discordant turns do. `evals/paired.py` gives the difference between the arms with Newcombe's interval for paired rates and an exact McNemar test on the discordant turns. Its non-inferiority margin was registered for Module 10's agent bench, so this cell prints the interval and the test, and no verdict against that margin.

#### Do it: the paired read, and the turns that flipped

The same cell, run when this page was built over the two offline reports of step 8's arms, written with `--report` to a scratch folder:

You read the experiment one turn at a time. Offline, the scripted classifier ignores the examples, so the two reports agree on every turn: no discordant turn, and a McNemar p of 1.000. On your lane, every turn the cell lists is a question whose route the eight lines changed. If a statute question went to the handbook with the examples out, or the other way round, that is the boundary the examples were drawing. The list and the paired interval are this lesson's proof: the router's examples removed and restored, with the route accuracy before and after.

### Verify it yourself: the bill and the checklist

What the measurements cost at list price, then eleven checks, each with the value that proves it on your lane.

#### What the measurements cost

Each run prints its own rupees; these are estimates from `shared/prices.py`: `gemini-3.6-flash` at USD 1.50 in and 7.50 out a million tokens, `gemini-3.1-flash-lite` at 0.25 and 1.50, Rs 85 to the dollar. A LOW answer is priced as the course's typical answer, 2,000 tokens in and 300 out (Rs 0.45). An answer asked to think or write more, at MEDIUM, at HIGH or under the rule, is priced with its whole 2,048-token cap once (Rs 1.56); a retry after a cut-off adds at most Rs 4.17. Each pool read is one Ranking API request at the rate lesson 2.3 states, Rs 0.085.

In all, about Rs 34.38 if every answer is the typical one, and about Rs 71.15 if every answer that thinks or writes more fills its cap once, plus the arbiter's thinking in step 9. The bench's and the router's own last lines print the real figures.

#### The checklist

Nothing that serves traffic, and no kit file. The log holds one `stream` usage row from the Chat page and 23 `passages` rows, from step 5's read and the two bench runs, each with no tokens and no cost. The bench's 55 answers and the router's calls went from your shell straight to Gemini, so they wrote no usage row: they are on your project's bill, and their own output priced them. Your home folder holds `~/cot_rule.json`, `~/exemplars_kit.json` and `~/exemplars_none.json`, and `/tmp` holds `jn03_pool.json`. generator.py is the kit's, as the bench checked on disk after each run, and the deployed router still reads its eight examples. Lesson 3.3 reads the failing rows of a live eval and fixes them one prompt rule at a time, with the same bench.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.2 Prompt with chain of thought and few-shot exemplars · v5.0

Next: Lesson 3.3 Recognise prompt failure modes and fix them in the prompt.
