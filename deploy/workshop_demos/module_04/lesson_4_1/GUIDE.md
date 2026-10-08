# Lesson 4.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.1_Eval_Dataset_WIX.html`, reviewed at blob `1842ef7a3c0ff2277b8154be660b88709080a151`. Learners read that page on the course site; this guide keeps its prose.

Module 4 measures the answer, and the measure is a set of questions with answer keys: the kit's golden set, 65 rows over 3 tenants. You find the one clause of ACME's handbook that no row asks about and write a row for it, which the offline gate accepts. Then you write the hardest shape, an isolation row for Zeta. The gate refuses it twice, each time with a sentence that says why, and accepts it on the third try. You ask both rows once against the API, label two paraphrases, and see why a question generated from a chunk is a candidate and not a row. Only step 6 and the last cell of step 7 call the cloud.

- What a golden row promises, and what makes it useful

- The words: row, shape, must_contain, must_not_contain, anchor, answerable, source, required, gate, pair, candidate

- Before you run anything: set up the shell

- The set as it stands: the gate, the rows that cite the handbook, and the clause no row asks about

- A lookup row: written into build_golden.py, built, and judged

- An isolation row: the marker that cannot work, the list it must join, and the gate green again

- Ask the two rows once: the live half's own functions, and the outsider's 403

- Paraphrase pairs and generated candidates: two kinds of row that are not golden

- What rows cost, how a golden set rots, and handing the kit back

- Verify it yourself: the checklist

You will learn what makes a golden row useful. It can fail, its evidence can be found, and the rows that would go red cannot be deleted without a reviewed change. You will learn how the offline gate checks each of these, and the one thing no gate can check for you. Then you will prove it on your lane: add a lookup row and an isolation row to the kit's golden set, watch the gate refuse the isolation row twice and accept it on the third try, and ask both rows once against the API.

### What a golden row promises, and what makes it useful

A question with an answer key, and four things the key must be. The gate can check three of them.

A golden row is a question with an answer key. Each row names a tenant and a question. It says which figures a right answer contains, where the evidence lives, and whether the tenant's documents can answer at all. The kit keeps 65 of them in `evals/golden.jsonl`. The eval gate judges the model with these rows, so the rows have to be judged first. A row that can never fail lets a broken system through. A row that can never pass blocks a good one. Both look like tests.

There are five shapes, and each catches a different way to be wrong. A lookup asks for one fact from one clause. A join needs two clauses, so the packing order and the budget of lesson 3.4 matter. A refusal asks for something the tenant's documents do not hold, and the right answer says so. An isolation row asks one tenant for a fact that only another tenant holds, or holds differently. An answer that carries the other tenant's figure is a leak. A version row asks about a document that has been re-issued, and forbids the figure only the retired version carries.

Useful means four things, and the gate can check three of them. The row is falsifiable: every figure it demands is in its own tenant's files, and every figure it forbids is in another tenant's files and not its own. It is anchored: every `must_retrieve` anchor, a clause code or a document's slug, can be found. It is covered: every isolation, version and media row is listed in `required.json`, so deleting one is a change somebody reviews. The fourth is that the key is right: that 45 days really answers the question you asked. No gate checks that, because a wrong figure from the right tenant's files passes every rule. You check it by reading the clause.

An anchor is a figure, a date or a code, never a sentence. The live half matches figures, not wording. It lower-cases both sides, drops the commas, turns number words into digits and "per cent" into %, and then requires the figure to stand on its own. So "twelve weeks" matches "12 weeks", and "60" does not match "160 days". The words around the figure still have to match exactly. The kit learned this from its own rows. Three overtime rows anchored on "twice the rate of wages", and a model that wrote "twice the normal rate of wages" was scored wrong. A refusal row asked for a GST rate, and the invoice says "GST @ 18%", so the model was right and the row was wrong. Each fix is a line in `build_golden.py`, with a note that says why.

A question paper and its moderator. A teacher sets a paper and writes the answer key. Before the exam, a moderator checks the paper. Every answer in the key must be printed in the textbook, every page reference must exist, and the questions the board requires must all still be there. The moderator cannot tell whether the key's answer to question 7 is the right answer to question 7. Only someone who has read the chapter can. The offline gate is the moderator. You are the teacher. The live run of lesson 4.2 is the exam.

#### The row scorer: a row, the evidence the offline gate finds, and an answer scored the way the live half scores it

Pick a row. The first box shows it as `golden.jsonl` holds it, without its note, and what the offline gate finds for each assertion. The second box scores an answer by the live half's rules: try the presets, then type your own. The 13 rows are kit rows that each carry a lesson, two rows as they were first written, and the rows you will add.

The evidence is the gate's own matching rule, run over `evals/corpus` when this page was built. The scorer is `normalise()`, `contains()` and the per-row judgment of `live()`, ported from `run_eval.py`. For every preset, the build checked the scorer's verdict against the kit's own `live()`.

It has no model and no retriever, so the answer is whatever you type. It assumes a valid citation of the right kind; the live half also checks that every citation names the row's tenant, its own document and a current version. It cannot tell you whether a refusal row is right, and neither can the offline gate. Only a live run can, which is how rf-07 was found.

### The words: row, shape, must_contain, must_not_contain, anchor, answerable, source, required, gate, pair, candidate

Twelve rows, each with the value it takes in the kit you cloned.

One distinction to hold: sound and right are two different claims. The gate proves a row is sound: it can fail, it can pass, and it cannot vanish unnoticed. Only the author can say the row is right, that the figure it demands answers the question it asks. Step 4 shows the gate accepting a row whose key is wrong.

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

Only the shell. Every cell runs in the kit's folder, where the setup block leaves you, and the venv's `python` runs the kit's own scripts. The UI is not used. Step 6 needs the two token functions the block defines, and step 7 needs `bq`, which comes with the Cloud SDK. Steps 4 and 5 change three files of your clone, and step 7 changes a fourth. Step 8 keeps your changes as a patch and gives the kit its files back.

### The set as it stands: the gate, the rows that cite the handbook, and the clause no row asks about

The target, the rows, the checks the gate runs over them, and the gap you will fill.

#### Definition

The offline gate is `run_eval.py` with no arguments. It loads the text files under `evals/corpus` and the committed `golden.jsonl`, then runs three checks. Falsifiable: every answerable row has a figure, every figure is in its tenant's files, and every marker is where its shape says it must be. Anchors: every anchor is found in the tenant's file names and text joined together, so a slug such as `hr_policy_2026` and a clause code such as `NP-03` can both be found. Coverage: no shape falls below its minimum, and `required.json` and the file agree. The matching is plain: the row's text, lower-cased, must appear in the file's text, lower-cased. Nothing is normalised offline. A row is a call to `R()` in `build_golden.py`. The builder applies the same rules when it writes the file, and the gate applies them again to the committed file, because that is the file CI runs.

#### The code

#### Do it: the gate, the rows that cite the handbook, and the handbook's clauses

The second line lists the rows that cite `hr_policy_2026.md`. They are the set a reindex of that one document is judged on, in lesson 4.4.

Ten rows cite the handbook, by `--source`. Now count by clause. The cell reads the handbook's sections and lists, for each clause that is not filler, the ACME rows that anchor on it.

The gate judged the set, not the model: no request left your machine. It found every figure in its tenant's files, every anchor findable and every required row present, so it exited 0. The handbook has 282 sections, and 272 of them are GEN- filler that makes it long enough to test retrieval. Of the 10 real clauses, nine are asked about and one is not: SEC-09, the access review. The clause table also shows what the listing hides. The join rows jn-01, jn-02, jn-03 and jn-07 depend on the handbook, but they anchor on clause codes only, and `sources_of()` counts only anchors that are document slugs. A reindex of the handbook judged with `--source` would not ask them. That is why the rows you write carry the slug as well as the code.

### A lookup row: written into build_golden.py, built, and judged

One line of Python, the builder's check, the gate's verdict, and six versions of the row that show what the gate can and cannot see.

#### Definition

SEC-09 says production access is reviewed quarterly, and any account unused for 45 days is disabled automatically. The row asks the second fact. Its `must_contain` is the figure, `45 days`. Its anchors are the clause code, which finds the clause, and the slug, which ties the row to the handbook for `--source`. It is a lookup and not an isolation row, because Zeta's handbook has the same SEC-09, word for word. A leaked answer would also be the correct one, which is why the kit's README makes the tenants' figures differ on purpose. The row goes into `build_golden.py`, not into `golden.jsonl`. The builder checks every row against its tenant's files before it writes anything, then rewrites the whole file from its list. A line added to `golden.jsonl` by hand would pass the gate, and vanish the next time anybody runs the builder.

#### The code

#### Do it: add the row, build, gate

The cell removes any earlier lk-32 line and inserts the row before the bracket that closes `GOLDEN`, so running it twice is harmless. The builder prints its first five lines and its last. `make eval` runs exactly the gate's line; calling it directly puts the exit code on a line of its own.

#### What the gate catches, and the one mistake it cannot see

The next cell judges six versions of the row in memory, with the gate's own two functions. It writes nothing.

The builder found `45 days` and both anchors in ACME's files and wrote 66 rows. The gate checked the committed file again and exited 0. Four of the six versions were refused, each with the gate's own sentence. Two of those refusals are worth a second look. The words `disabled automatically` are in the clause, but the file breaks that line after `disabled`. The offline check reads the file's characters as they are, line break included, so a two-word phrase can fail where a figure would not. The last version, `60 days`, was accepted. It is NP-03's notice period, from ACME's own handbook, so every rule holds, and the row is wrong: a model that answered SEC-09 correctly would fail it. No gate can catch that. You catch it by reading the clause before you write the key.

### An isolation row: the marker that cannot work, the list it must join, and the gate green again

The same question asked of Zeta, three tries, and the rule each refusal quotes.

#### Definition

LV-07 is a clause where the two handbooks disagree: ACME caps leave encashment on exit at 45 days, and Zeta at 20. So "How many days of earned leave are encashed on exit?" has a right answer for Zeta, `20 days`, and a leaked answer, ACME's. This is the sharpest isolation shape, the one iso-01 uses for the travel cap: answerable, with a marker that must never appear. The marker has two rules. It must be in another tenant's files, or there is nothing to leak and the row is decoration. It must not be in the row's own tenant's files, or a correct answer could fail it. The obvious marker is `45 days`, and it breaks the second rule, because Zeta's SEC-09, the clause of step 4, says 45 days too. An isolation row must also be listed in `required.json`. The builder does not check that; the gate does.

#### The code

#### The first try: the obvious marker

The builder refused and wrote nothing: `golden.jsonl` still has 66 lines. Its sentence names the rule. The next try uses a phrase only ACME's clause holds, `capped at 45 days`.

#### The second try: ACME's phrase

The builder wrote the row, and the gate refused the file. Its coverage rule found an isolation row that `required.json` does not list. The rule works both ways: a listed id missing from the file fails too. So a row can neither vanish nor arrive unlisted.

#### The third try: listed, and the gate green

Each refusal came from a different check, and each quoted its rule. The builder refused a marker that was in Zeta's own handbook. The gate refused an isolation row that the required list did not name. With the marker moved to ACME's phrase and the id listed, both passed, and `make eval` exited 0 over 67 rows and 16 required ids. That is this lesson's proof. The marker is now a phrase, and a phrase has a weakness: a leak in other words, "up to 45 days", does not contain it. Try that answer on iso-11 in the scorer. The row still fails it, because the leaked answer lacks `20 days`. Step 6 shows why the live gate does not lean on the marker at all.

### Ask the two rows once: the live half's own functions, and the outsider's 403

Three requests to `/v1/query`, scored with `run_eval.py`'s own code, before lesson 4.2 runs the whole set.

#### Definition

The live half, `make eval-live`, belongs to lesson 4.2. It sends every row to `/v1/query` with `top_k` 6, as the UI's service account, which `make roster` put on all three tenants. It looks for every marker in every reply and scores each answerable row by `contains()` and by its citations. Isolation is judged a second way. The retriever filters by tenant before anything reaches the model, so a marker can only fire if the model invents another tenant's exact figure, which the kit calls a lottery. The leg that can really leak is identity to tenant. So the gate also asks every isolation row as `documind-outsider-sa`, an account that may call the service and is on no roster, and requires 403 every time. The cell asks your two rows as a member, then asks iso-11 as the outsider, with the same `ask()` and `contains()` the gate uses.

#### The code

#### Do it

Both rows passed on your lane. Each answer held its figure, iso-11's held no marker, and each citation named the tenant's own handbook. The outsider got 403 from the roster check, which is what makes iso-11 a release blocker in lesson 4.2. If lk-32 comes back refused, the row has done its job early: it found a question your lane cannot answer yet. Look at what retrieval returned for it before you change the row.

### Paraphrase pairs and generated candidates: two kinds of row that are not golden

Labelled pairs that measure the answer cache, and questions Gemini writes from chunks, which a person has to turn into rows.

#### Paraphrase pairs

The answer cache of Module 6 serves an earlier answer when a new question's embedding has a cosine similarity of at least 0.95 with an earlier one. That number was chosen, not measured. `paraphrases.jsonl` is what measures it. Each pair rewords a golden question. A pair marked `same` asks the same fact in other words, so a cache hit would be right. A pair marked different is a few words away with a different answer: E3 against E2, minimum against maximum, probation against confirmed. A cache hit there is a wrong answer served fast. `cache_threshold.py` embeds both sides and prints, for each candidate threshold, the hit rate on the same pairs and the false-hit rate on the different ones. The cache stays off until a threshold has no false hit on this set. The labels are yours to get right: the self-test checks that each pair names a real golden row and differs from its question, not that its label is true.

Add two pairs against lk-32. One asks the same fact in other words. The other asks the clause's other fact, the kind of near miss a loose threshold would answer with 45 days.

The self-test is offline. The curve itself, `python evals/cache_threshold.py --project "$PROJECT"`, embeds 68 short questions with `text-embedding-005` in `us-central1`. Lesson 6.4 reads it before the cache is switched on.

#### Generated candidates

`make make-evalset` asks Gemini for one question and answer per chunk of the quality-gated feed. The feed is `rag_data.index_feed`, joined to the chunks the worker mirrors into BigQuery, so a chunk the quality scan held back never becomes a question. Each pair is scanned by the one PII list, `shared/pii.py`, and dropped on any finding, never rewritten. What comes out is a candidate: a question with no figure it must contain, and the chunk's id as its only anchor. A golden row is a contract a person writes, and a generated question inherits the blind spots of the model that wrote it. So the file is `golden_generated.jsonl`, and the gate never reads it.

What would the gate say if a candidate were merged as it is? The cell builds one for SEC-09 the way `make_evalset.py` writes it. Its chunk id is the worker's own: the tenant, the hash of the handbook's bytes, and `#8`, SEC-09's position after the preamble and seven clauses. Then the cell judges the reviewed version.

The candidate fails twice. It has no figure, so it would accept any answer. Its anchor names a version by its hash, which no file contains, and which would point at a retired version the day the handbook is re-issued. The reviewed row, with a figure, a code and a slug, is lk-32. That rewrite is what review means: a figure a person checked in the clause, and anchors that survive a new version.

Last, the generator itself, if your feed has rows. The chunk feature job and the Dataplex quality scan fill the feed, and lesson 11.5 runs them (`make features`). Before that, the count is zero and the cell stops there.

### What rows cost, how a golden set rots, and handing the kit back

The rupees, the ways the kit's own history says a set decays, and your rows kept as a patch.

#### What it costs

#### How a golden set rots

The kit's docstrings name five ways, and each has a guard.

- A red build made green by hand. Somebody edits `golden.jsonl` to loosen a figure. The gate checks the committed file for exactly this reason, and the builder is deterministic, so a loosened figure is a diff with an author and a date.

- The failing rows deleted. A green build with fewer tests looks like a fix. `MIN_ROWS` guards each shape, and `required.json` guards each row that would block a release.

- A document re-issued without its rows. vr-01 and lk-06 move to the new figure in the same commit as the handbook, or the gate is red before anything deploys.

- Anchors that are sentences. The overtime rows: the right figure, scored wrong, because the model added one word.

- A bare numeral that a larger number satisfies. Until 12 September, "60" passed on "160 days". The live check now wants the figure on its own boundaries.

Blind spots remain, and you have now seen each one. The offline gate cannot tell a right key from a wrong one (step 4). It has nothing to check on a refusal row, so only a live run found rf-07. `--source` misses a row anchored on clause codes alone (step 3). And a bare figure passes almost for free: `60` is in 13 of ACME's 17 text files, the CGST Act's table of contents among them, while `45 days` is in 1. The check proves the figure can be said, not that the right clause says it, so give a figure its unit.

#### Keep your rows, and give the kit its files back

Your clone now differs from the kit in four files. Lesson 4.2 runs the kit's own set, 65 rows and 15 required ids. The setup block's `git pull --ff-only` also refuses to run over local edits to a file the kit has changed. So keep your rows as a patch and restore the four files. `git -C "$DEMO_ROOT" apply "$HOME/lesson71_rows.patch"` brings them back whenever you want them.

### Verify it yourself: the checklist

Eleven checks, each one block above, each with the value that proves it on your lane.

In the cloud, only the usage rows of step 6's two answers. In your clone, steps 4, 5 and 7 changed `build_golden.py`, `golden.jsonl`, `required.json` and `paraphrases.jsonl`, and step 8 put all four back; your seven lines are in `~/lesson71_rows.patch`. Two untracked things may remain: `evals/__pycache__`, from the cells that import `run_eval.py`, and `evals/golden_generated.jsonl` if your feed had rows. Both are safe to delete. Lesson 4.2 runs the set you just studied: the offline half as CI runs it, the live half against a candidate with 9 thresholds and 15 required rows, and a judge that scores but never gates.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.1 Build a useful evaluation dataset · v5.0

Next: Lesson 4.2 Separate offline checks, live scoring and LLM judgment.
