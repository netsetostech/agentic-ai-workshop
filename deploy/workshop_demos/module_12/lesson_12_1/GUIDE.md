# Lesson 12.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_12.1_Tuning_Decision_WIX.html`, reviewed at blob `74d0c88ef6b682c383fddeaf29771c03fe9980f8`. Learners read that page on the course site; this guide keeps its prose.

Tuning teaches a model a habit, not facts. Before you pay for it, your lane's own numbers must show answers that are wrong in a way a habit fixes: a missing citation, a missing refusal, JSON that breaks. The fix must also be one that a prompt, a cache or better retrieval cannot make more cheaply. The kit has no tool that makes this call. This page gives you a rubric that reads numbers the kit already produces.

In this lesson you audit the training file the kit ships. Then you run the live gate with a report, and put that report, a week of the API's logs and the price table through the rubric. Last, you build your own training file as version v2, freeze it with its manifest in the datasets bucket, and read it back.

- What tuning can fix, and the data it needs

- The words: tuning, the habit, the rubric, the report, the grammar events, a training row, the golden set, exclude_golden, the manifest, the datasets bucket

- Before you run anything: set up the shell

- The kit's rules, and the file it ships, audited

- The evidence, and the verdict

- Your training file, as v2

- The frozen file, read back

- Optional: a better file, v3, in the house style and in Hinglish

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what supervised tuning changes in a model and what it cannot. You will learn the four questions that decide whether your lane needs it, and the four rules the kit's training file follows. You will also see where the file falls short of those rules today. Then you will prove it on your lane: a verdict with its evidence, and the frozen manifest with its row count.

### What tuning can fix, and the data it needs

A habit, not facts; four questions before any spend; four rules for the file.

What a tuned model learns. Supervised tuning shows a model a few hundred worked examples: this prompt, this answer. It changes how the model answers, not what it knows. The kit's own words, in `make_trainset.py`: a model tuned on this learns the habit the lane serves, not facts, because facts are retrieval's job. On DocuMind the habit is the answer the generator asks for, in `SYSTEM`'s five rules:

- The shape. ModelDraft's JSON: an answer, citations, `answerable`, `confidence`.

- The citation. A `[N]` mark in the answer for each source it uses, and a citation with the clause that answers, at most twenty-five words.

- The refusal. `answerable=false` when the sources do not answer.

A fact reaches the model through retrieval, on every request, in its current version, with a source to cite. A fact trained into the weights stays as it was on the day of training, and has no source to cite.

Four questions before the spend. The rubric reads four numbers the kit already produces:

- The gate's misses: habit or knowledge? `make eval-live REPORT=` writes each row's outcome and why. A row that answered without a citation, answered when it should have refused, or came back malformed is a habit miss. A row that refused an answerable question, or answered without the figure it needed, is a knowledge miss: retrieval, the corpus, or the row itself. Tuning can only fix the first kind.

- The grammar under traffic. The generator logs `generation_repaired` when it had to fix a draft, `generation_invalid` when the fix failed, and `generation_unparsed` when the reply was not JSON. The rubric counts them against a week of answers. The line is this page's, not the kit's: 1%. Below it, the prompt is holding the grammar.

- The price. `gemini-3.6-flash`, the model your lane serves, cannot be tuned. Managed tuning accepts `gemini-3.5-flash` and `gemini-3.1-flash-lite`, and the kit tunes flash-lite. In `cost.py`'s table flash-lite costs a sixth of flash for input and a fifth for output: USD 0.25 and 1.50 a million tokens, against 1.50 and 7.50. A tuned model costs more than its base, though: Google's pricing page, checked on 24 September 2026, says that from Gemini 3 onward a tuned endpoint's predictions cost 1.5 times the base model's. That makes a tuned flash-lite about a quarter of flash for input and three tenths for output. One that passes the same gate would still cut the bill: a reason to try it, as an experiment that lesson 12.3 decides.

- The data. One row per real chunk needs chunks. `make_trainset.py` takes chunks of 400 characters or more from the tenant's corpus mirrors, and acme has 1,542.

The verdict follows from the four numbers:

- Tune for quality when the misses are habit, or the grammar breaks at 1% or more.

- Tune for price, as an experiment only, when the misses are knowledge but the tunable base is cheaper.

- Do not tune in every other case.

Four rules for the file. `make_trainset.py` samples 300 chunks, sorted by id and evenly strided, so the sample is the same every time the corpus is. For each chunk `gemini-3.6-flash` writes a question, the answer, the clause that answers, and a question the passage does not answer. Every tenth chunk also yields a refusal row. Then four rules apply:

- `exclude_golden`: no row may teach the test. A row is dropped if its chunk is a golden row's evidence: the chunk is in the row's scope and carries one of its must-contain phrases. It is also dropped if its question is a golden question rephrased. For each golden row in turn, the evidence rule is checked before the question rule.

- `redact`: drop, never rewrite. DLP inspects each question and answer, and a row with any finding is dropped. The kit's reason: weights cannot be filtered per tenant afterwards.

- `write`: one list, two formats. The Gemini tuning format that Vertex AI reads, the chat format that open-source trainers read, and a manifest with each file's SHA-256.

- Frozen. The version is in the file name. A changed corpus is a new version, never an edit.

A tuition teacher before the board exams. A good tuition teacher drills how to write an answer: make the point, cite the section, and write "not in the syllabus" when it is not. That habit carries into any paper. The teacher cannot drill next year's syllabus changes: those are in the textbook, and this is an open-book exam. An honest teacher also never drills the board paper itself, or questions rephrased from it. The marks would then say the student is ready when the student has only memorised.

Before paying for a crash course, the parent reads the last test. Marks lost for not citing, or for answering what was not asked, are what drilling fixes. Marks lost because the textbook lacks the chapter are not. And if a younger student, once drilled, could sit the same paper for a quarter of the fees, a trial is worth it, judged by the same paper.

The drilling is tuning, and the way of writing is the habit. The open textbook is retrieval and the board paper is the golden set. The last test is the gate's report, and the crash course's fee is the tuning job.

#### Would this row enter the training file?

Pick a chunk from acme's corpus and a question to write from it, or type your own. The panel runs `exclude_golden` against the gate's 65 golden rows. It tells you whether the row is kept, or which golden row drops it and by which rule.

The rules are the kit's: `exclude_golden` with `run_eval.normalise`, ported and compared with the kit's own function on 737 cases. The cases are every row of the committed v1, plus every question offered here and every golden question, each on every chunk offered here.

It judges one row against the golden set, and nothing else. It does not run DLP, write a question, or check the quote. `make trainset` does all three, and a row the panel keeps can still be dropped by the PII scan.

### The words: tuning, the habit, the rubric, the report, the grammar events, a training row, the golden set, exclude_golden, the manifest, the datasets bucket

Ten rows, each with the value it takes on your lane.

One distinction to hold: the golden set tests the model, and the training rows teach it. A row the golden set could recognise, by its evidence or by its question, would let a tuned model pass the test from memory. That is why `exclude_golden` runs before anything is written, and why lesson 12.3 can trust its comparison.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above, and a lane that answers.

- The gate, as in lesson 4.2. Step 4 runs every golden row against your API and keeps the report in `~/gate171.json`.

- A week of traffic, if you have one. The rubric reads the last seven days of the API's usage rows from Cloud Logging. On a lane with few answers the rate it prints is noisy, but it still runs.

- `make trainset`'s two clients. Step 5's first line installs the ingest image's pins of `google-genai` and `google-cloud-dlp` in the operator venv. The Makefile says the target needs both.

- What the lesson changes. It writes `~/gate171.json`, and three v2 files: in `evals/sft/` in your kit folder, and in the datasets bucket. The kit's own v1 is not touched.

### The kit's rules, and the file it ships, audited

The self-test on fixtures, then the committed v1 held to the rules it states. Offline.

#### Definition

The cell does two things with the kit's own files:

- `make_trainset.py --selftest` runs each rule on fixtures, with no network and no credential.

- It audits `evals/sft/documind_sft_v1`, the file the kit ships, in eight checks: the manifest;

- whether the two formats agree;

- whether every target parses as ModelDraft;

- whether `SYSTEM` is the generator's;

- the quotes, against their chunks and against `SYSTEM`'s twenty-five words;

- the `[N]` marks in the answers;

- the handbook's rows, and today's golden set against v1;

- one chunk as the training prompt shows it, and as the generator serves it.

#### The code

The rules, as the file states them:

The row: the user turn it trains on, and the target it teaches.

What the generator serves instead, for every source it packs:

#### Do it

- The rules hold on fixtures, and v1 agrees with itself. It has 317 rows, 30 of them refusals. The two formats agree, every target parses, `SYSTEM` is the generator's, and today's golden set drops none of v1's rows.

- The quotes do not match their chunks. Of 287 quotes, only 22 appear in their chunk as written, and 282 once line breaks count as spaces. 5 are not in their chunk at all. 17 are longer than the twenty-five words `SYSTEM`'s rule 5 allows, the longest 33 words. Nothing in `make_trainset.py` checks either.

- No answer marks its source. `SYSTEM`'s rule 2 asks for `[N]` in the answer, and the UI turns each `[N]` into a pill. None of v1's 287 answers carries one, because `target()` puts the citation in the JSON only. A model tuned on these rows is taught to leave the mark out. The gate would not notice, because it counts the citations list.

- The handbook's rows are filler. Its ten clauses and its preamble are all shorter than 400 characters, so none of them is ever sampled. All 58 of its rows come from its 272 generated GEN- sections, one paragraph repeated under 18 topic names.

- The training prompt is not the prompt the generator serves. Training shows one source as `[Source 1]` followed at once by the chunk's text. The generator packs several sources, each under a header line that names its file. The training rows also carry `SYSTEM` twice, as the system instruction and in the user turn. The generator sends it once, in the prompt.

### The evidence, and the verdict

The gate with a report, then the rubric over the report, a week of logs and the price table.

#### Definition

The first cell runs the gate as lesson 4.2 did, every golden row against your API, and keeps the report. The second cell is the rubric. It reads four things:

- The report's missed rows. Each is classed as habit or knowledge. A habit miss is in `run_eval.py`'s own words, "answered without a citation" or "answered, should refuse", or a malformed reply.

- A week of Cloud Logging. The API's `query` and `stream` rows, and the generator's grammar events.

- `cost.py`'s price table, at your lane's own average tokens and monthly answers, with a tuned endpoint at 1.5 times its base, as Google prices it.

- The chunks `make_trainset.py` could use.

Managed tuning accepts two bases, and neither is the model you serve:

#### Do it

- Both misses are knowledge. `jn-06` cited a source but left out EMEA and 11.4. `lk-27` refused a question the CGST Act answers. A tuned model would miss both the same way: the figure and the section have to be retrieved, not remembered.

- The grammar holds. One repaired draft in 360 answers is 0.3%, under the 1% line.

- The price case is real. At this lane's tokens a tuned flash-lite costs Rs 0.28 an answer, at 1.5 times its base price, against Rs 1.08 for flash: Rs 1,236 a month less.

- So the verdict is: not for quality, and for price only as an experiment. Lesson 12.2 tunes flash-lite on the rows, and 12.3 holds the tuned model to the same gate.

On your lane the rows, the rate and the rupees are your own. Keep this cell's output with the report: it is the decision's record.

Step 5 builds the file whatever your verdict. It costs about Rs 40 of tokens, and a file decides nothing. The billed act is 12.2's tuning job, and 12.3's gate decides whether the tuned model may serve. If your verdict is "do not tune", the rest of the chapter is practice, and the tuning job is a cost you choose.

### Your training file, as v2

make trainset with a version of your own: sample, write, exclude, scan, freeze, upload.

#### Definition

`make trainset` runs `make_trainset.py` on acme's corpus mirrors, and uploads what it writes to the datasets bucket:

Pass `--version v2`. The default version is v1, and `write()` opens its files for writing without checking whether they exist. A run without a version would overwrite the kit's own v1 in `evals/sft/`, and upload it under the name `make tune` reads from the bucket by default. The rule "frozen" is a comment in the code, not a check.

Before anything is written, `exclude_golden` runs: the rule the panel in step 1 ran.

#### Do it

Standard pay-as-you-go Gemini shares its capacity, and a 429 there is a rate limit from a spike in traffic. Google's answer is to wait and try again, doubling the wait each time. Google's retry page says the SDK does this by default. The ingest image's `google-genai` 2.22.0 does not: without retry options on the client it makes one attempt. So until 24 September 2026 the first 429 ended the run, and lost every pair made before it.

`ask_pairs()` now gives each call 8 attempts on 408, 429 and 5xx, waiting 2 seconds and doubling up to a minute: about 3 minutes before it gives up on a chunk. A chunk that still fails is skipped and named, and the file has fewer rows. Three chunks in a row that fail stop the run with nothing written, because the capacity is gone for now: run the same cell again later. A 400 or a 403 is not retried. That is the request's fault, and waiting will not fix it.

- 300 chunks, the same 300 as v1's. The sample is sorted by id and strided, so while the corpus is unchanged the chunks are too. What differs is the model's questions, and the golden set as it stands today.

- 15 rows dropped for the golden set, and none by the PII scan. The line names the golden rows they overlapped, and the manifest records each rule's count.

- Three files, written and uploaded: the Gemini tuning file, the chat file and the manifest, in `evals/sft/` and in the datasets bucket.

- The last line is the kit's own advice. Review the rows before you commit them: a generated question inherits the generator's blind spots.

### The frozen file, read back

The manifest from the bucket, both files held to its SHA-256, the rows checked again.

#### Definition

The cell reads the manifest from the datasets bucket, not from your disk, and holds each uploaded file to the SHA-256 the manifest records. Then it checks your v2's rows the way step 3 checked v1: today's golden set, the quotes, the `[N]` marks and the handbook's rows. Last, it prints three sample questions. This is the manifest `write()` builds:

#### Do it

- The manifest in the bucket says v2: 315 rows, 30 of them refusals. Both files match the SHA-256 it records. That is this lesson's proof: the frozen manifest and its row count.

- The golden set drops none of the 315 rows. `exclude_golden` ran before the write, and nothing has changed the rows since.

- The stand-in copies its quotes, so every quote here is in its chunk. On your lane, compare with v1's 5 quotes off their chunk and 17 over twenty-five words. The marks and the handbook's rows come out as they did for v1, because the rules that make them have not changed.

- Read the sample questions, then more. `head -n 5 evals/sft/documind_sft_v2.chat.jsonl` shows whole rows. That is the review `make trainset` asks for.

### Optional: a better file, v3, in the house style and in Hinglish

make trainset --style helpdesk: a stronger teacher, the prompt the generator really sends, answers that mark their source, and a Hinglish twin for every second chunk.

Steps 3 and 6 found four faults in the file the kit writes by default. It trains on a prompt the generator never sends. Its answers never mark their source. Nobody checks its quotes. And the handbook's rows are filler. A model tuned on it learns those faults as surely as the habit. Step 4's verdict is still why you might tune: a tuned flash-lite costs about a quarter as much, if it passes the same gate. Version 3 is the file worth that experiment. It fixes the four faults, and it teaches one habit the served model does not have, so that lesson 12.3 can show the difference on a single question.

#### The house style

Every answer in v3 has the same three lines: the verdict first, then the reason with the `[N]` mark of the source it rests on, then the clause and the file its header names. For example:

The format is the habit; the facts in it still come from retrieval. The verdict, the reason and the clause are all in the source the mark names. The same facts in a plain paragraph would be just as correct. The labels make an answer quicker to read, and the clause makes it quicker to check.

#### Hinglish

Many of the people who ask DocuMind questions type in Hinglish: Hindi grammar in Roman script, with English terms. For every second chunk the teacher writes the question, the verdict and the reason again in Hinglish, keeping every number, section and name as the passage writes it, and v3 carries both rows. A model tuned on the pairs learns to answer in the language it is asked in, with the same labels and the same `[N]` mark. Refusals come in both languages too.

#### What else changes

The distractors come from the same corpus: one from the answering chunk's own document where it has another, as a retriever would return it, and the rest from other documents. None is a golden row's evidence and none is filler, so the test set stays out of the prompts as well as the answers. The answering chunk's place among the three is fixed by its id, so the file teaches `[1]`, `[2]` and `[3]`, not always `[1]`. And one more rule joins `exclude_golden`: when its question rule drops an English row, the row's Hinglish twin goes too. A golden question rephrased in Hinglish is still a rephrasing, and a word-overlap rule cannot see it.

#### Do it

Then read the frozen file back from the bucket and check it with the kit's own functions. The last lines print one chunk's two rows, the English and its Hinglish twin:

- 395 training rows and 40 validation rows. 131 of the training rows are in Hinglish and 27 are refusals. v2 is as step 5 left it.

- The checks dropped what they should. 10 pairs had a quote that was not in their chunk, 5 Hinglish twins came back in English, 23 rows touched the golden set, and the scan of every chunk dropped 1 row: the CGST Act's front page prints a public helpdesk address, which lesson 12.2 found the plain scan never reads. The stand-in fails the first two checks on purpose, so that you can see them fire.

- Every prompt is the one the generator sends. Each has three sources under their headers, and every answer marks the source its citation names.

- The two sample rows are one chunk, asked twice. They have the same sources, the same mark and the same clause; only the language changes. The stand-in's wording is mechanical. On your lane, the teacher writes them.

- Nothing is tuned yet. Lesson 12.2's step 7 validates v3 and tunes on it, with its validation file.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Tune the habit, retrieve the facts. A fact in the weights is fixed on the day of training and has no source to cite. A fact that comes through retrieval is current, and the answer can cite it.

- The corpus, never the logs or the answer cache. The log sink keeps questions and answers out of BigQuery on purpose. The answer cache holds the golden questions every eval run asked, and a model trained on its own test set has learned nothing you can measure.

- The test set never enters. `exclude_golden` drops by evidence as well as by question. The first self-test passed a rephrased golden question on a lexical score alone, so one rule was not enough.

- Drop, never rewrite. A row that carries PII is not worth a redacted version, and weights cannot be filtered per tenant afterwards.

- One list, two formats. Vertex AI's tuning and an open-source trainer read the same rows, so a managed model and a small self-hosted one learn the same habit.

- Frozen, with a manifest. The version, the counts, what was dropped and why, and a SHA-256 per file. The file can be named in a tuning job and proven unchanged.

- Tuning is an explicit act. `tune.py` bills per training token, and nothing else on the lane starts it.

#### What it costs

Each point is checked in the kit's code or its committed v1, and the build asserts it, so this box changes when the kit does.

- The rule "frozen" is a comment. The version defaults to v1, and `write()` overwrites without checking. `make trainset`'s recipe passes no version, and `make tune` reads v1 unless told otherwise. A second run without `TRAINSET_ARGS` replaces the file the kit ships, and the manifest that proved it.

- The plain style's training prompt is not the served prompt. Training shows one source, with no header line, and carries `SYSTEM` twice. The generator packs several sources under header lines, and sends `SYSTEM` once. The code names `tools/check_auth_wiring.py` as what holds the two `SYSTEM`s equal, and it does not exist. They are equal today, and nothing keeps them so. Step 7's `--style helpdesk` builds the served prompt with the generator's own packer.

- The plain style's targets never mark a source. `SYSTEM`'s rule 2 asks for `[N]` in the answer, and the UI turns each one into a pill. `target()` never writes one, so the file teaches the model to leave the marks out. The gate, which counts the citations list, would not notice. v3's answers carry the mark.

- The plain style checks no quote. Not against its chunk: 5 of v1's 287 are not in it. Not against `SYSTEM`'s twenty-five words either: 17 are over, the longest 33. `target()` only cuts a quote at 200 characters, ModelDraft's limit. v3 drops a pair whose quote fails either test.

- The plain style's PII scan reads the question and the answer, not the chunk. The chunk is in the user turn, and it enters the weights too. acme's invoice carries a PAN and a GSTIN. The default sample of 300 passes it by, but a sample of 1,000 would train on it, unless the model happened to repeat one in its answer. v3's scan reads every chunk a prompt carries.

- The plain style trains on the handbook's filler. Its ten clauses and its preamble are under 400 characters, so they are never sampled. 58 of v1's 317 rows come from one generated paragraph, repeated under 18 topic names. v3 never samples them.

- The kit prices a tuned endpoint at its base rate. `cost.py` bills an endpoint path at the price of `RAG_MODEL_BASE`. Google's pricing page, checked on 24 September 2026, says a tuned Gemini 3 endpoint's predictions cost 1.5 times the base's. The usage rows, and so `make usage` and `tenant_daily`, would count a tuned model's answers at two thirds of their price. The rubric in step 4 applies the 1.5 itself.

- No decision tool. The rubric is this page's. The kit has the numbers, in the report, the grammar events and `cost.py`'s table, but nothing that reads them together or records the verdict beside the file.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane. The ninth is for step 7, if you ran it.

`~/gate171.json` holds the gate's report, and step 4's output is your verdict. `evals/sft/` in your kit folder holds v2's three files, and the datasets bucket holds the same three under `sft/`, versioned and never expiring. The kit's own v1 is as it shipped. Lesson 12.2 validates this file and tunes flash-lite on it. Pass it `VERSION=v2`, or `make tune` reads v1. If you ran step 7, the same folder and the bucket also hold v3's four files and its manifest, and lesson 12.2's step 7 tunes on them.

Netsetos GenAI on GCP · Module 12 Tuning · Lesson 12.1 Decide whether tuning is justified and prepare data · v5.0

Next: Lesson 12.2 Validate sanitized datasets and run managed tuning.
