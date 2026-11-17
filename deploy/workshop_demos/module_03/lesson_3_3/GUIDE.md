# Lesson 3.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.3_Prompt_Failures_WIX.html`, reviewed at blob `2234cf3cb8c2625c7b3c783425458e19c04d13ec`. Learners read that page on the course site; this guide keeps its prose.

Lessons 3.1 and 3.2 changed how the model is asked. This lesson starts from what came back wrong. The eval gate judges every golden row by one rule, and a row that fails says why: refused, answered without its figure, answered when it should have refused, or no answer at all. Only some of those are the prompt's to fix. A clause that never reached the model cannot be answered by any instruction, and a reply that never came back was never read. You will run the live eval with each answerable row's passages read again, sort the failing rows by where their fix lives, and try one new rule per row in the kit's prompt bench: SYSTEM edited in memory, the row asked again on the same passages, and the 8 refusal rows asked beside it to show what the rule breaks. Nothing is committed: generator.py's SYSTEM stays byte for byte the tuning set's copy.

- Every failure has an address: the prompt, retrieval or the code

- The words: prompt failure, SYSTEM, dated rule, verdict, why, pool, anchor, quote check, address, bench, arm, guard

- Before you run anything: set up the shell

- One golden question in the Chat page, read the way the gate reads it

- The prompt and the gate's rule in the kit: SYSTEM, the prompt line, row_verdict() and the passage checks

- The live eval, with every answerable row's pool read again

- The failing rows, read with their passages, and where each fix lives

- One rule per row in the bench, with the refusal rows beside it

- Why the fix stays in memory: the served prompt is the trained prompt

- What the fixes cost, which way the guard points, and what the bench cannot see

- Verify it yourself: the checklist

You will learn to tell a prompt failure from a failure that only looks like one: the gate says why a row failed, the row's pool says whether the model had the evidence, and only then is a new rule worth trying. Then you will prove it on your lane: a live eval with its passages, the failing rows read and sorted, three one-rule fixes in the bench, each asked beside the refusal rows, and the kit's prompt unchanged on disk.

### Every failure has an address: the prompt, retrieval or the code

Three parts of one prompt, a verdict that says what went wrong, a pool that says whose fault it is, and a rule that is never tried alone.

The prompt is three things in one string. `generate()` starts every answer from SYSTEM, the kit's 5 numbered rules, then the passages retrieval returned, each under a `[Source N]` header, then the question. The model reads that string and writes a structured reply: an answer, its citations with the words it quoted, a confidence and `answerable`. When a reply is wrong, the fault can lie in any of the three parts, or outside the string altogether.

The gate says what went wrong; the pool says whose fault it is. `run_eval.py` judges every reply by one rule, `row_verdict()`. An answerable row must be answered, cite its own tenant's passages and hold every `must_contain` figure; an unanswerable row must be refused. A row that fails carries a why in the gate's own words: `refused`, `answered without ['60']`, `answered without a citation`, `answered, should refuse`, or an HTTP status when no reply came back. The why alone cannot tell a model that ignored the clause from a model that never saw it. With `DOCUMIND_EVAL_PASSAGES=1` the gate also reads each answerable row's pool again from `/v1/passages` and records whether each `must_retrieve` anchor, a clause code such as NP-03 or a document's name, was in it.

A failure is the prompt's only when the evidence was there. If every anchor reached the pool and the reply still refused, dropped a figure or answered the wrong part, the model mishandled what it was given, and a sentence in SYSTEM can change how it handles it. If an anchor is missing, no sentence can help: the fix is retrieval's, Module 2's. If no reply came back, it is the code's: a 502 means the generator had no answer it could parse, whether the reply was cut off at its token limit twice, the second time with three times the room, or broke the answer's schema. And some failures were never the model's: the third live eval (7 Sept 2026) scored "300 or more" as wrong against a row that says three hundred, and the fix went into the gate's `normalise()`, not into the prompt.

A new rule is a trade, so it is never tried alone. A rule that makes the model answer more readily, or say more, also makes it likelier to answer where it must not. So every fix on this page is asked again on its failing row and, beside it, on the 8 refusal rows the golden set keeps: questions no document answers, such as ACME's sabbatical policy or its revenue in FY2024. A fix that turns its row green and a refusal row red has moved the failure, not fixed it.

A bank's letters desk and its style guide. A customer complains: the bank wrote that it was "unable to advise", though its own policy plainly covered her case. Before anyone touches the style guide, the desk opens the writer's folder. If the policy page was never in it, the filing room is at fault, and no style rule would have helped. If the letter never went out because the printer jammed, the printer is. Only when the page was in the folder does the desk draft one new line for the guide. Then it rewrites the letter that was complained about, and beside it a stack of old letters that rightly said "unable to advise", because a line that makes writers answer more readily will make some of them answer where they must not. SYSTEM is the style guide, the folder is the pool, the filing room is retrieval, the printer is the code, and the stack of rightly declined letters is the refusal rows.

#### The failure desk: 8 golden rows, the gate's verdict and where each fix lives

Each button is a golden row with a pool of the kit's own passages and a reply written for this page to show one kind of failure. Edit the reply, untick its citation, take the clause out of the pool or let the request fail with a 502: the verdict, the quote check, the anchors and the fix's address are worked out again with the kit's rules on every change. Two to try: tick the MSA's clause into lk-12's pool and watch its address move from retrieval to the prompt; type the missing half of jn-03's answer into its reply and watch the row pass.

The rows are golden rows, and the passages are the kit's own chunks as `shared/documind_corpus.py` cuts them, each shown around the words that matter; the replies are this page's illustrations, not answers any model gave. The verdict is `row_verdict()`, the quote check `quote_check()` and the anchor check `anchors_found()`, ported to JavaScript with `normalise()` and `contains()`; the address is step 6's `address()`. When this page was built, node ran the port over every case and every combination of its switches, and over 21 more replies to other golden rows (a leaked figure, a retired version, a missing figure citation, a malformed body, a refusal at the door): 581 replies in all, and every result equalled the kit's. The desk skips the one check it cannot hold, a citation's version against the ledger, as the gate does when `/v1/sources` cannot be read.

It is not your lane. Each reply fails one way, and a real failure is rarely that clean: a reply can refuse with half its anchors in the pool, or answer the wrong part and quote the wrong passage at once. And an anchor is evidence, not proof. A row whose only anchor is a document's name, such as lk-23's `industrial_relations_code_2020`, counts it as found when any passage of that document is in the pool, even one that does not answer. Step 6 prints, for every failing row, the sentence of its pool that holds each expected figure, so you can see the evidence rather than infer it.

### The words: prompt failure, SYSTEM, dated rule, verdict, why, pool, anchor, quote check, address, bench, arm, guard

Twelve rows, each with the value it takes on your lane.

Two of these words carry the lesson: why and anchor. The why is what the gate saw. The anchors say whether the model could have done better with the passages it was given, and that decides whether a line of prompt is the right repair.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head: step 3 asks as you, in the browser, and steps 5 to 7 ask as documind-ui-sa.

The shell, in the kit's folder, with `PROJECT`, `API` and the token function `tok` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line. Step 3 asks one question in the UI, signed in as yourself. Step 5's eval asks every golden row and takes ten minutes or more. Step 7's bench imports `services/rag-api/generator.py` into your shell, so the venv needs rag-api's packages, which Module 0's install put there (if the bench says one is missing: `python -m pip install -r services/rag-api/requirements.txt`), and its model calls go out on your Application Default Credentials, which the setup block's `adc ok` line checks. Steps 4 and 8 read files and call nothing.

### One golden question in the Chat page, read the way the gate reads it

jn-03 asked as yourself: the answer's two figures, the passages the model was given, and what each would mean.

#### Definition

The Chat page sends your question to rag-api's `/v1/stream` as you, through IAP, and asks for 5 passages. Before the first token arrives, the stream sends one citation event per passage the model was given: the packed set, after the budget, which the page lists under Sources, each with its first 200 characters. The answer streams in as plain text, because a stream carries no response schema: no `answerable` flag, no quotes of the model's own. The gate asks `/v1/query` instead, for 6 passages and a structured reply. The model reads the same SYSTEM either way, but from a pool one passage deeper, and the gate can judge its reply field by field. So the Chat page is where a person meets a failure, and the gate is where one can be counted.

#### The code

#### Do it: ask jn-03 and judge the reply by eye

Open the UI at `https://documind-ui-NUMBER.asia-south1.run.app`, signed in as yourself; Module 0 put your account on acme's roster. On the Chat page, with Brain `direct` if the sidebar offers a choice, ask golden row jn-03's question:

I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?

Then check it the way `row_verdict()` and `anchors_found()` would:

- The figures. The row's `must_contain` is 45 and 60: LV-07 caps leave encashed on exit at 45 days, and NP-03 sets an E3's notice period at 60 days. Does the answer hold both?

- The passages. Open Sources. Each line is a passage's opening, and a handbook passage opens with its clause code. The row's anchors are LV-07 and NP-03: are both there?

- The address. Both clauses in Sources and a figure missing: the prompt's failure. A clause missing: retrieval's, whatever the answer says. Both figures there: the row would pass.

You judged one reply by eye, the way the gate judges every row: the figures first, then whether the passages that state them were in front of the model. In the UI the Sources list is the evidence, because it is exactly what the model read. The gate cannot see this page. It asks `/v1/query` for all 65 rows, with 6 passages and a schema, so its reply to jn-03 can differ from yours: lesson 3.1 measures how much one question's answers vary between runs. Step 5 asks every row that way and keeps each reply.

### The prompt and the gate's rule in the kit: SYSTEM, the prompt line, row_verdict() and the passage checks

The 5 rules every answer starts from, the line that joins them to the passages, and the code that decides a row failed and why.

#### Definition

SYSTEM is a string set once in `generator.py`: a line saying who the model is, then 5 numbered rules. Rule 1 confines the answer to the numbered context, rule 2 asks for `[N]` markers, rule 3 is the refusal rule, rule 4 caps the length, and rule 5 says what a quote is: the clause that answers, at most twenty-five words. A sixth, `DATED_RULE`, is added only when a packed passage carries an effective date. None of the corpus's documents declares one, while three rehearsal documents under `evals/demo` do (gratuity_amendment_2026.md, hr_policy_2026_v2.md, smoke_note_v2.md). So on a lane that holds the corpus alone, no golden row's prompt carries rule 6; if an earlier lesson left a dated version current, its rows' prompts on the lane do. `generate()` packs the passages within the budget (lesson 3.4) and builds the prompt in one line: SYSTEM, the dated rule when it applies, the context, the question.

The gate's rule has two layers. `THRESHOLDS` are rates over many rows, so a run can be green with rows failing: `correct_rate` needs 32 of the 47 answerable rows answered right, so up to 15 can fail before that rate turns red, and `refusal_rate` needs 17 of the 18 unanswerable rows refused. Those failing rows are what this lesson works from. `row_verdict()` is the gate's judgment of one row as a function of the reply alone: `live()` keeps an inline copy that lessons quote, and a test holds the two equal. Figures are compared with `normalise()` on both sides, so 300 and three hundred are one figure, and `contains()` makes a figure stand on its own: 60 is not in 160 days. Since 8 October each row's record keeps its answer and its citations, and with the switch on, `quote_check()` and `anchors_found()` run on the pool read back.

#### The code

#### Do it: SYSTEM's rules, as the bench will number them

The cell reads SYSTEM and DATED_RULE from `generator.py` as text, with Python's own parser, and splits SYSTEM into its rules with the bench's own reader, `rules_of()`. It imports no Google library and calls nothing.

You read the instructions every answer on your lane starts from, numbered as step 7's bench numbers them: a rule you add becomes rule 6 there, in memory. The last line is the sha256 of SYSTEM followed by DATED_RULE, the text a prompt version names (lesson 3.6 binds it to `documind-rag@v3`), and step 7's kit arm prints the same value. Nothing in SYSTEM names a document, a figure or a tenant: its rules are general, and a fix written into it has to be general too.

### The live eval, with every answerable row's pool read again

Every golden row asked through `/v1/query`, every answerable row's passages read back through `/v1/passages`, and every record kept in a report.

#### Definition

`make eval-live` asks every golden row through `/v1/query` as `documind-ui-sa`, which `make roster` put on the three golden tenants, and every isolation row again as `documind-outsider-sa`, which must be refused with a 403. `REPORT=` writes each row's record: its outcome, verdict and why, its latency and stages, the first 600 characters of its answer and its citations. `DOCUMIND_EVAL_PASSAGES=1` is an environment switch, not a flag, because lessons quote `main()` and the recipe whole; make passes the environment straight through to the script. With it on, the eval reads each answerable row's pool again from `/v1/passages`: the same door, roster, retrieval and rerank, and no model call. Each citation gets a quote check, each anchor a found or not found, and two [info] lines print the totals. Neither is a threshold.

#### The code

#### Do it: the eval, with the switch on

Read it from the top. The nine rates and their thresholds decide the exit code. The two [info] lines are the switch's: `quote_passage_rate` counts the answered rows' quotes found in the passage they cite, and `must_retrieve_recall` the anchors found in the pools read back. The shape table says where the passes fell. Under rows that cost a point each failing row is printed with its why, and the report's path is the last line before the verdict. A run can exit green and still list failing rows, and that list is what step 6 reads.

The gate asked your lane all 65 rows and judged every reply with the rule you read in step 4. Because of the switch, every answerable row's record also says what the model had in front of it: each anchor found or not, and each quote checked against its own passage. The report is now the eval's answers as data, and step 6 reads it without asking the model anything again.

### The failing rows, read with their passages, and where each fix lives

Every record that did not pass, its answer and quotes, its anchors, the sentence of its pool that holds each figure, and its address.

#### Definition

The cell reads the report and nothing else of the eval's: no row is asked again. For each record that did not pass it prints the why, the question, the reply's answer and each citation with its quote check, and the anchors the switch recorded. Then it asks `/v1/passages` for that row's pool once more, Rs 0 and no model, and prints the sentence that holds each expected figure, matched the way the gate matches figures, with `contains()`. Last comes `address()`, the rule the desk ran in step 1. A failing row's fix is the prompt's when the reply came back well formed and either the corpus answers the row and every anchor was in the pool, or the corpus does not and the reply answered anyway; the cell names the other addresses as it goes. It ends with an export line: one row of each kind the three fixes in step 7 are written for, the first of each in the golden set's order, and a note when it found fewer than three.

#### Do it: the failing rows

How to read a row. `-> the prompt` rows are this lesson's: the model had the clause and still refused, or left a figure out, or answered a question no document answers. `-> retrieval` rows belong to Module 2, and `-> the code` rows to lessons 3.5 and 3.7. A passage line that finds the figure is the strongest evidence a reply could have been right. One that finds it in none of the passages, with every anchor present, needs your eyes: the anchor may be a document's name whose answering passage was not retrieved, which is retrieval's after all, or the figure may be written in a form the gate does not read. The line about passing rows names replies whose quotes the passage check flags: rule 5's silent failures, which the gate passes and lesson 3.6 measures across the set. Paste the export line into your shell: step 7's commands read `FIX1`, `FIX2` and `FIX3`.

You read the eval's failures with their evidence beside them, and every failing row now has an address. Only the prompt's rows go to the bench. A rule written for a retrieval miss would add a sentence to every prompt on the lane and change nothing for that row, because the passage it needs would still not be there.

### One rule per row in the bench, with the refusal rows beside it

SYSTEM edited in memory, the failing row asked again on its own pool, the 8 refusal rows asked beside it, and generator.py's bytes checked before and after.

#### Definition

`make bench` runs `evals/prompt_bench.py` in your shell. It reads each row's pool once from your lane's `/v1/passages` and holds it fixed, so a difference between two answers is the prompt's or the model's, never retrieval's. It imports `generator.py` as the service does and answers with the kit's own `generate()`: the same packing, prompt, schema and retry, with thinking at `LOW` as the API asks for it. `--add-rule` appends one line to SYSTEM as rule 6, in memory, for the second arm only; the kit arm answers with SYSTEM as it is. The two arms answer the same rows from the same pools, one after the other, and every answer is judged by `row_verdict()`. When the run ends, the kit's SYSTEM and client are put back whatever happened, and the file's bytes are compared with the bytes it started with.

Each fix asks one failing row and the 8 refusal rows, in both arms: 18 answers, one run each. The rule is written for a kind of failure, not for the row. It names no figure and no clause, because a rule that said "the CFO approves purchases above Rs 2,00,000" would fix lk-08 by handing it the answer, and teach the model nothing about the next row. And each rule pushes the model toward answering, or toward saying more, which is exactly what the refusal rows are there to catch.

#### The code

#### Do it: the three rules, applied in memory first

Before anything costs money, see what each edit arm will send. The cell applies each rule with the bench's own `edit_system()` and prints the rule count, the prompt's sha256 and the new rule 6, then checks `generator.py`'s bytes.

#### Do it: FIX1, the refused row

#### Do it: FIX2, the half-answered join

#### Do it: FIX3, the answer without its figure

Each run prints its pools, its two arms with their prompts' sha256, one line per answer (the verdict, the thought and visible tokens, the rupees and the why), then a table per arm: passes out of 9 with a Wilson interval, the quote checks, and the cost. The last lines say that `generator.py` is unchanged on disk and SYSTEM is the kit's again. The cell below reads the three reports and puts each fix's row and guard side by side.

Four verdicts are possible. Fixed, and the guard held: the kit arm failed the row, the edit arm passed it, and the edit arm refused at least as many refusal rows as the kit arm. Fixed, and the guard broke: the rule moved the failure onto a refusal row, so it is not a fix; reword it narrower and run it again. Not fixed: the rule did not reach this failure; try another wording, or look again at the row's passages, because the fault may not be the prompt's. The kit arm passed too: on its own pool the row did not fail this time, so this run cannot credit the rule with anything. That is lesson 3.1's variance, and `--runs 3` asks each row three times for three times the price.

Three failing rows, each answered again from the pool the eval drew on, once with the kit's prompt and once with one new line, and each line tried against the 8 questions no document answers. That is the lesson's proof: a failure read, its address found, one rule written for its kind and re-run with a guard. One run each is one draw: the interval on 9 answers an arm is wide, and a row that flips once has shown the rule can work, not that it always will. Nothing was deployed and no file changed. The rule lived in the bench's memory for one arm and was gone when the run ended.

### Why the fix stays in memory: the served prompt is the trained prompt

SYSTEM in two files, a test that holds them equal, and what shipping a rule would take.

#### Definition

SYSTEM lives in two files. `generator.py` serves it with every answer, and `evals/make_trainset.py` builds the tuning set behind it (lesson 12.1), so that a tuned model is served behind the prompt it was trained behind. A test in `commands/tests` holds the two strings byte for byte equal, and the prompt's text is registered under a version, `documind-rag@v3`, which every usage row records. Edit SYSTEM on disk and the test fails, the tuning set no longer matches what is served, and every answer would be labelled with a version whose text it no longer is. There is one more trap: `DATED_RULE` numbers itself 6 in its own text, so a rule shipped as the sixth would meet a second rule 6 in every prompt with a dated passage. Shipping a prompt change is lesson 3.6's: a new version, registered, built into a candidate and gated. This lesson's rules stay where the bench put them, in memory.

#### The code

#### Do it: the two copies, and the kit's own test

The served prompt and the trained prompt are still one text, and the kit's own test says so. The three fixes changed neither: each existed for one arm of one bench run. A rule that earned its place, fixed with the guard held over several runs, is a change to propose, and the proposal is a new prompt version that the gate judges on a candidate, never an edit made on a live lane.

### What the fixes cost, which way the guard points, and what the bench cannot see

The rupees of each run, the guard a refusing rule would need, the cheap model for a lane with too few failures, and five things the bench leaves out.

#### What it costs

Estimated when this page was built: every golden row's prompt on the Rs 0 lane's pools (the kit's lexical rank over its own chunks, the top 6 packed and counted the way `generate()` packs and counts them), priced with `shared/prices.py`. "Of input" is the prompts alone. "Typical" adds 300 output tokens an answer, the course's usual figure; thinking is billed as output too, so yours may be higher. "At most" adds the whole 2,048-token answer reserve to every call. A fix is priced with its row at the largest answerable prompt, 3,017 tokens, of 8,000 allowed. A reply cut off and asked again bills both calls, which no estimate here includes, and the query's embedding and the reranker bill on their own lines.

Each bench run prints its own total from the usage the model returned, thought tokens included. That figure, not this table, is what the run cost.

#### Which way the guard points

The refusal rows catch a rule that makes the model answer where it must not. They cannot catch the opposite. A rule written to stop an answer to a question no document answers, such as rf-06's paternity leave, pushes toward refusing: If no source states what the question asks for, set answerable=false, even when a source covers a nearby subject. A rule like that can only break the rows the corpus does answer, so its guard is the answerable rows: `--shape lookup,join`, 45 rows, 90 answers across both arms, Rs 24.40 of input and at most Rs 141.90. The same holds for a failing row whose why is `answered without a citation`, whose rule would be Every answer with answerable=true cites at least one source, with the words it relied on. To see what rule 3 itself is holding up, take it out and ask the refusal rows alone: `make bench PROJECT="$PROJECT" BENCH_ARGS="--shape refusal --drop-rule 3"`, 16 answers, Rs 3.96 of input and at most Rs 24.85.

#### A lane with too few prompt failures

A healthy lane may fail fewer than three rows the prompt could fix, and step 6's export line then says so. The kit's cheap model is a second source of failures on the same questions. Ask it every lookup and join row on their own pools, with the kit's prompt only: `make bench PROJECT="$PROJECT" BENCH_ARGS="--shape lookup,join --model gemini-3.1-flash-lite --show"`, 45 answers, Rs 2.03 of input and at most Rs 13.78. `--show` prints each row's pool, so pick FAIL rows whose pools hold their clause, export them as `FIX1` to `FIX3` by hand, and add `--model gemini-3.1-flash-lite` to step 7's commands. The fix cell prints each report's model, so a fix measured on the cheap model says so.

#### What the bench cannot see

- The dated rule. `/v1/passages` returns no effective date, so the bench never adds `DATED_RULE`. That matches every golden prompt on a lane that holds the corpus alone, and not a lane where a dated version is current.

- Figures. It returns no media URL either, so a figure or a table is answered from its caption with no image beside the prompt. A row that asks for a figure citation is not a fair bench row.

- The tenant's cache and a tuned model. No tenant goes with the bench's calls, so no explicit cache is attached, and a tuned endpoint is refused: it is served on a regional client, and `make candidate` with `make eval-live` judges one.

- The Chat page. The UI streams with 5 passages and no schema; the bench answers like `/v1/query`, with 6 passages and the schema. A rule that fixes a row in the bench is a rule for `/v1/query`'s replies first.

- Its own rows. The bench's answers go from your shell to Gemini and never pass through rag-api, so they leave no query usage row: each run leaves one `passages` row per row it read, and its own printed total.

#### What comes next

The pool is what retrieval returned; the prompt holds what the budget packed. With the kit's chunks the two are the same: six of the corpus's largest chunks, with SYSTEM, the dated rule and the longest golden question, come to 3,272 tokens of the 8,000 allowed, and the largest golden prompt on the Rs 0 lane to 3,017. Lesson 3.4 shows what happens when they are not. Lesson 3.5 takes the reply apart: the schema the model fills, how its citations are resolved, and how the model's refusals differ from the API's own. Lesson 3.6 checks quotes across the whole set and ships a prompt with its version.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

In the cloud: nothing deployed and no revision made. Step 5's eval left a usage row for each answer that came back, and a `passages` row for each answerable row read again; the outsider's requests were refused at the roster and left none. Step 6 left one `passages` row per failing row it read. The bench left one `passages` row per row it benched and no query row, because its answers went from your shell to Gemini directly, billed to your project at list price, as each run printed. On your machine: `evals/reports/lesson33.json` and `fix33_1.json` to `fix33_3.json`, which git ignores. `generator.py` is byte for byte what you cloned, as each bench run checked, so the setup block's `git pull` keeps working. Put acme's pin back now, with the setup section's pin-back window. Lesson 3.4 opens the prompt's middle: how the passages are packed into the budget.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.3 Recognise prompt failure modes and fix them in the prompt · v5.0

Next: Lesson 3.4 Pack evidence within the context budget.
