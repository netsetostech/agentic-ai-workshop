# Lesson 11.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.8_Capstone_Handover_WIX.html`, reviewed at blob `755bf433e9168d8a73ccf0f5d43bcd6c529eb3a6`. Learners read that page on the course site; this guide keeps its prose.

The capstone is not a feature. It is a fork of this kit that a stranger can verify in under ten minutes: a live URL behind IAP, your own corpus, an eval suite that can go red, one lane on top of the core, and four documents that say what you rejected, what it costs, how it fails and how it rolls back. The rubric names those 8 components, and the kit's `make capstone-check` says PASS or FAIL for each one, offline and at Rs 0, and never a score. The score is the defence's: 5 dimensions, 0 to 3 each, 9 of 15 to pass and no dimension at 0.

In this lesson you read the rubric as the kit reads it, run the check on a canned capstone that passes, on the same with its four documents swapped for the kit's templates, and on a copy with one command deleted, read your own lane with the same two tokens the check mints, and write the operational handover, `HANDOVER.md`, from your checkout and your lane. Nothing on the lane changes.

- What a stranger can check, and what only a defence can score

- The words: component, dimension, the pass rule, incomplete, the fork, the records, the canned fork, the templates, the lane reads, the handover

- Before you run anything: set up the shell

- The live URL behind IAP, and the Documents page

- The lines the check rests on

- The check, offline: the kit as it ships, a canned capstone, your fork

- Change it: one command deleted, one component fails

- Your lane, read with the two tokens

- The handover: HANDOVER.md from the checkout and the lane

- The defence, what the author still decides, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what the capstone rubric asks for, why its 8 components are checked and never scored, and how `make capstone-check` reads a fork and a lane without changing either. Then you will prove it: a canned capstone passes every component, the kit's templates in its place fail until they are filled, a copy with one command deleted fails exactly one, and `make handover` writes the operational handover of your lane.

### What a stranger can check, and what only a defence can score

The rubric has two halves. The components exist or they do not; the dimensions are how well you can speak to what you built.

Eight components, each a thing in your fork. The capstone rubric, published on this page (the interactive below, and step 9), says every component must exist in the learner's fork and be checkable by a stranger in under ten minutes, because a component nobody can verify is a claim. A live URL behind IAP, your own corpus of 30 pages or more, in a tenant other than acme, globex and zeta, an eval suite of 30 golden rows or more with tenant isolation, one lane on top of the core, and four documents: `ARCHITECTURE.md` with the alternatives you rejected, `COST-MODEL.md` at 1k, 10k and 100k queries a month, `FAILURE-MODES.md` with four entries each proved by a script, and `RUNBOOK.md` with one recorded rollback. Each document starts from the kit's template in `capstone/templates/`. A component is PASS or FAIL. One FAIL is an incomplete submission, and the defence does not run.

Five dimensions, scored only in the room. Architecture, failure modes, cost at 10×, evals, and what you would do next month: 0 to 3 each, 15 points, 9 to pass, and no dimension at 0. The no-zero rule matters more than the total: a learner who cannot speak to failure modes at all has not built a production system, however good the architecture is. Two assessors score independently, and a split of more than 3 points goes to a third. Nothing in the kit scores a dimension. It cannot: a dimension is what you say when asked why.

The kit checks the first half. `make capstone-check` runs `commands/capstone_check.py` on a fork: by default the checkout you are in (`FORK=.`), or any directory you name. Offline it reads the fork's files at Rs 0 with no credential: the four documents, the corpus and the golden rows, the records `make smoke-deployed` and `make gate` leave in `evals/reports/` (lessons 11.2 and 11.3), and it runs the fork's own `evals/run_eval.py` offline, as `make eval` runs it. With `PROJECT=` on make's command line (the `PROJECT` your shell exports does not count) it also reads the lane and changes nothing: `gcloud` describe and list calls from an allow-list of 11, two ID tokens minted as `make eval-live` mints them, and GETs on documind-api. It prints PASS or FAIL for each component with the evidence, or with what is missing and which lesson's command supplies it (for a missing document, its template), and exits 1 when any component fails.

An occupancy inspection, then a handover pack. Before a new office building opens, an inspector walks it with a checklist: the fire exits open, the sprinklers hold pressure, the lift has its certificate, the earthing reads under the limit. Each item is there or it is not. The inspector does not grade the architecture; a building with a locked fire exit does not open, however elegant its atrium. Only once every item passes does the owner sit down with the architect and the contractor and ask the hard questions: why this structure, what would fail first, what does it cost to run, what would you do differently. And on the day the building changes hands, the contractor leaves a pack: where the mains are, what the alarms watch, when the night systems switch off, who to call.

The eight components are the inspection. The five dimensions are the questions in the room. `HANDOVER.md` is the pack.

#### The rubric, as the kit reads it

Untick a component to see what one FAIL does. Then score the five dimensions by picking, for each, the row that describes your defence: the verdict applies the pass rule.

1. The components: each exists in the fork, or the submission is incomplete

2. The dimensions: 0 to 3 each, as the assessors would score your defence

Generated from the rubric itself when this page was built: the eight rows of its component table, the five dimensions with the 0 to 3 rows of each, and the pass line. The line under each component says what `make capstone-check` reads for it, taken from the check's own rules in `commands/capstone_check.py`. The verdict's rule was run in Node on all 1024 score combinations, with and without a failed component, and compared with the same rule in Python: 192 of the 1024 pass.

It is your reading of the rubric against your own defence, before the day. The assessors' reading is the one that counts, and the rubric is the only thing they score against. The defence is 90 minutes, two assessors, the live system on screen; the 60-minute peer mock the week before is practice, unscored, and the two are different events.

`make capstone-check` says that a component exists and a stranger could verify it. It does not say the component is good. Three rejected options with six words of reason each pass component 5; whether those reasons are specific to your workload is dimension 1, and only the room scores it. Read a PASS as "the defence can run", not as "this is done".

### The words: component, dimension, the pass rule, incomplete, the fork, the records, the canned fork, the templates, the lane reads, the handover

Fourteen rows, each with the value it takes in your fork or on your lane.

One distinction to hold through the lesson: the check reads records, not the lane's history. A rollback counts when two successive `make smoke-deployed` runs in your log show the traffic leaving the revision the candidate tag names, with `/version` answered before and after. If you rolled back and never ran the smoke, the rollback happened and the check cannot see it.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head: make capstone-check mints the same two tokens tok and otok mint, and every gcloud line it runs is a describe or a list, as you.

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `TENANT` and `API` set and the two token functions, `tok` and `otok`, defined.

- Steps 4 to 6 are offline: nothing leaves your machine, and the only thing written is a copy of the kit under `/tmp/sahyadri`.

- Step 7 reads your lane and changes nothing on it. The two tokens need the token-creator grant `make operators` gives your address; lesson 11.3's runs needed the same.

- Step 8 writes one file, `HANDOVER.md`, into the fork you run it in.

- Your records. Components 1, 4 and 8 read `evals/reports/` in the checkout you run the check in. If lessons 11.2 and 11.3 ran from another checkout, run the check there, or copy that folder over.

### The live URL behind IAP, and the Documents page

Component 1 and component 2 as a reviewer sees them in a browser, and the two lines in the kit that make them so.

#### Definition

The live URL is documind-ui's. `make deploy-services` deploys it from `commands/lesson-12.4.sh` with two flags: `--no-allow-unauthenticated`, so Cloud Run accepts no anonymous request, and `--iap`, so Identity-Aware Proxy stands in front of the service and asks for a Google sign-in. A member of the IAP policy signs in and sees the app; a non-member is refused by IAP with a 403 before any request reaches the service. That is the rubric's first component, as a reviewer checks it: open it, sign in, ask a question, and watch a non-member get 403.

Behind the UI, documind-ui calls documind-api with its own identity token, as documind-ui-sa. The API checks the tenant's roster. documind-outsider-sa is on no roster, so a token minted for it gets 403 from the API too: that is the 403 the kit's isolation rows prove (lessons 4.1 and 4.7), and the one the check reads from your newest live eval report.

#### The Documents page

The UI's Documents page has a Versions view. It makes one call, GET `/v1/sources` for the tenant, and renders what the API serves: each document's name, its status, how many chunks were embedded, reused or retired, the date it declares, when it was indexed, and where its copies are held. It is the same read as `make sources TENANT=`.

Two things about it matter for component 2. First, `status` is what the check reads on the lane: every document of your own tenant must be listed `indexed`. Second, the view carries no page count, and neither does the API: `/v1/sources` returns none. So the check counts your pages offline, from the files in `evals/corpus//`, by the rules the ingest worker counts them with.

- A text file (`.md`, `.txt`) counts its form feeds plus one, the worker's own line in `services/ingest/main.py`. A manual written as one long file is one page unless you separate its pages with form feeds, which is what the canned fork's 32 pages are.

- A PDF counts the pages of its page tree, read with the standard library as the worker reads it with pypdf; a mirror `.md` beside it with a `pages:` line in its header is believed first. The kit's 13 real PDFs agree with the record of them in `evals/real_sources.json`, and the build of this page checked it.

- A picture or a recording is one page. A `.docx` is Document AI's to count, and the check says so: `pages not counted offline`.

- A `.md` beside its `.pdf` or `.mp4` twin stays home when `make ingest-corpus` uploads (`evals/upload.sh`), so it is not a document and not counted twice.

Your own corpus is a tenant other than acme, globex and zeta, the kit's own three. The check takes the tenant folder under `evals/corpus/` with the most pages among the others. Adding your documents to acme's folder adds nothing to the capstone: component 2 reads `evals/corpus/ holds no tenant of your own`. Make a folder of your own, `make ingest-corpus` uploads it under that tenant, `make roster TENANT=... MEMBERS=...` puts documind-ui-sa on its roster so the Documents page and the check can read it, and lesson 4.1's golden rows ask it questions.

### The lines the check rests on

The eight rules as the module states them, the numbers it holds, the loop that prints PASS or FAIL, the two rules that need the most reading, and the allow-list of reads.

#### Definition

`commands/capstone_check.py` is standard library only and has two subcommands, `check` and `handover`, plus `--selftest`. It loads two siblings by path, `release.py` and `remediate.py`, because those own the lane's names and the records `make` leaves: the gate's two accounts, the smoke log's format, how a `/version` answer reads, and the alert policies as Terraform declares them. The check reads the same records by the same rules rather than keeping a second copy of them.

#### The numbers

Every threshold the rubric states is one constant, next to the component it serves. `GOLDEN_MIN`, `ISOLATION_MIN` and `PAGES_MIN` are the rubric's 30, 5 and 30. `REJECTED_MIN` is the three options component 5 asks for, `ENTRIES_MIN` the four entries of component 7, `USD_INR` the 85 of component 6. `REASON_WORDS` is the check's own line: a rejected option argued in fewer than 6 words is named, not argued.

#### The loop

`cmd_check()` runs the eight functions in the rubric's order. Each returns two lists: what it held and what is missing. A component with nothing missing is PASS; its evidence prints under it, indented. A component with anything missing is FAIL, and each missing line says what is absent and which lesson's command supplies it. The exit is 0 when every component passes and 1 otherwise, so a script can gate on it; a precondition that fails, such as a fork that is not a directory, exits 2 with a `STOP:` line instead.

#### The two rules that need the most reading

Component 7 is the one the Change-it in step 6 breaks. An entry is a headed section of `FAILURE-MODES.md` with a `Symptom:` line and a command in backticks that the fork can run. "Can run" is resolved, never run: a `make` target the fork's Makefile or `mk/*.mk` defines, or a script the fork holds, started with `python`, `bash`, `sh` or `./`. Of lesson 11.7's registry, `make gotcha-drill ID=...` with an id that has an offline drill reproduces a gotcha; `make gotchas` and `make gotcha-detect` show and detect one and prove nothing, and the check says so by name.

Component 8 needs a rollback nobody wrote down as such. `make incident` writes no record, so the evidence is the smoke log: two successive `make smoke-deployed` runs of one lane where the revision serving changed from the one the candidate tag still names after it, which is what `make rollback` leaves, or back to an older revision, and both runs recorded a `/version` answer. A run whose traffic moved during its smokes is evidence of neither end.

#### What it may run on your lane

With `PROJECT=`, every gcloud command goes through `gcloud_json()`, which refuses anything not on `READS` before it runs. The list is 11 long: describe and list, plus `auth print-access-token` for the one read gcloud has no GA command for, the Monitoring API's alert policies. The two ID tokens are minted by `release.identity_token()`, as `make eval-live` mints them. Neither `check` nor `handover` can change the lane: there is no command on the list that would.

#### The two targets

`mk/capstone.mk` is the module's own file, not `release.mk`, where the plan first put it: lessons 11.1 to 11.3 quote `release.mk` from their sections to its last line, and a target appended there would land in their pages. Neither target has `guard-project`, because neither needs a project: offline is the default. `FORK` is given on the command line and declared nowhere, since `make replay` (lesson 6.8) reads a `FORK` of its own.

#### Do it: the rules on hand-made input

The selftest runs every rule on documents, records and PDFs it makes up, with no fork and no lane: the rejected options as a list, a table and sub-sections, the cost model's volumes and date, every way a FAILURE-MODES command resolves or does not, pages from text and from a PDF's page tree, plain and packed, a rollback told from a promote, and the outsider's 403. `commands/tests/test_capstone_check.py` holds 31 more tests, on the canned fork and on a stand-in lane, and `commands/tests/test_capstone_templates.py` 13 on the templates of step 5.

### The check, offline: the kit as it ships, a canned capstone, your fork

The to-do list a bare kit prints, eight PASSes on Sahyadri Freight, the records read with the kit's own rules, and the four templates your documents start from, which fail until you fill them.

#### Definition

`make capstone-check` with no `FORK=` checks the checkout you are in. It reads files and records and runs `evals/run_eval.py` offline, as `make eval` does: a few seconds, no credential, no network. Every FAIL line is a to-do item with the lesson that supplies it.

#### Do it: the kit as it ships

Run it in your kit checkout. If your checkout holds lesson 11.3's records, components 1, 4 and 8 read them and your output differs from the one below, which was run on a copy of the kit with no records at all.

The kit as it ships is no capstone, by design, and the check says exactly what is missing.

- One PASS: component 3. The kit's own suite is 65 golden rows, 11 of them isolation rows, and `make eval` exits 0. That is the one component you inherit.

- Component 1 holds half. The fork deploys documind-ui behind IAP: the flags are in the script. What is missing is evidence a member was answered and a non-member refused, which only records can give: `make smoke-deployed` (lesson 11.3) and `make gate` (lesson 11.2).

- Components 2, 5, 6, 7 and 8 each name the file or folder that does not exist: a tenant of your own, the four documents, each with its template in `capstone/templates/`, and a rollback in the smoke log.

- The last line names the failing components and says what a FAIL is: an incomplete submission, for which the defence does not run.

#### Do it: a canned capstone that passes

`commands/tests/capstone_fork/` is Sahyadri Freight, a made-up logistics company whose corpus is a fleet safety manual and a driver handbook, 32 pages between them, with the four documents and the records lesson 11.3's controlled failure leaves: a mistyped model promoted by force, rolled back and repaired, with a smoke run around each step and the repair's gate report. The kit's tests lay it over a copy of the kit, so you do the same: a local clone of your checkout, the canned files over it, its two golden rows appended, then the check. The clone holds none of your records, so the output is the canned fork's alone.

Eight PASSes, each with its evidence. Read them against the rubric's "how a reviewer checks it" column.

- 1, the live URL. Three things held: the deploy's two flags, a member answered (the last smoke run's `/version`, with its `git_sha`, model and prompt), and a non-member refused (every one of the 11 isolation rows answered 403 in the newest report that asked them, the repair's gate report).

- 2, your own corpus. `sahyadri` is the tenant that is not the kit's: 2 documents, 32 pages by the worker's count. And a query cites one: row `sh-01` passed citing the safety manual, in the same report.

- 3, the suite. 67 rows now, 11 isolation; `make eval` exits 0 in the fork.

- 4, one lane. The last smoke run passed `smoke-chat` and `smoke-media`: two lanes on top of the core, when one is enough.

- 5, 6 and 7, the documents. Three rejected options named with a reason; dual-priced amounts, a date and the rate on one line; four entries, each with the command that proves it, the poison upload's among them.

- 8, the rollback. Told from the log: the traffic left `documind-api-00042-typ`, the revision the candidate tag still named, back to `documind-api-00041-kel`, between two smoke runs that both recorded `/version`. The `/version` before says `gemini-3.6-flsh`: the mistyped model, caught.

The last line says it is complete and that nothing here is scored.

#### Do it: the records, with the kit's own rules

The check's rules are functions you can call. The cell loads the module, points a `Fork` at the canned fork and prints what the rules see: the smoke runs in order, the rollback they show, each report with its isolation rows, the tenant's pages, and how each FAILURE-MODES command resolves.

- Four smoke runs, as lesson 11.3 leaves them: the gated promote serving `00041-kel`; the forced promote of `00042-typ`, red, with the mistyped model in `/version`; the rollback to `00041-kel` with the tag still on `00042-typ`; the repair, `00043-fix`. The rollback is the third run against the second.

- One report is a live eval report (the gate's); `gate.json` is the gate's record, not a report, so it is not listed here. It asked all 11 isolation rows and every one was refused.

- Every command resolves. Two `make gotcha-drill` ids with offline drills, `make poison`, a target the Makefile defines, and `commands/incident-drill.sh`, a script the fork holds.

#### Do it: your four documents, from the templates

Your four documents start from the kit's templates in `capstone/templates/`. Each is the canned fork's document emptied: the same headings, a `{{...}}` placeholder in every slot, 66 across the four, and a comment at the top saying what the check reads in it and what the defence reads. In your fork you copy them to its root, `cp capstone/templates/*.md .`, and replace every placeholder, braces included. Here the cell lays them as they ship over the canned fork's four, runs the check, counts the lines that still hold a placeholder, and puts the canned four back.

A template copied as it ships is not yet a document. Each of the four components it stands in for FAILs, on the slots the check reads that still hold a placeholder.

- 1 to 4 still PASS. The canned fork's records, corpus and golden rows were not touched.

- 5: three rejected options named and none argued. `{{OPTION 1}}: {{WHY NOT}}` is 4 words, and the check counts an option as argued at 6 or more.

- 6: the three volumes and the rate are the template's own, so they hold. The amounts are `Rs {{AMOUNT}}` and `USD {{AMOUNT}}`, which carry no figure, and the date is `{{YYYY-MM-DD}}`.

- 7: four entries, each with a `Symptom:` line and a command in one of the four shapes that resolve: a gotcha drill offline, a drill live, a make target and a script. None resolves until its placeholder is a real id, target or script, and the check says why for each.

- 8: the recorded rollback still holds, from the canned smoke log. The runbook does not say how to roll back until its command slot holds `make rollback` with your project and region, as lesson 11.3 ran it.

- The grep counts the lines that still hold a placeholder, 38 across the four. The check reads only some of them and the defence reads all of them, so run the grep in your fork before the check, and expect 0 for each file.

- The canned four back, exit 0. `commands/tests/capstone_fork/` holds the four filled in, for a made-up company: read each beside its template.

The kit's own test, `commands/tests/test_capstone_templates.py`, holds the same line from both sides: as they ship, components 5 to 8 FAIL on their documents; with every placeholder filled, the four PASS.

#### Do it: your fork

In the fork you will defend, offline. The recording is the author's reference fork, built the way yours will be: a tenant of its own, `make ingest-corpus`, `make roster`, golden rows, `make gate`, lesson 11.3's rollback with a smoke run before and after, and the four documents, written from the templates.

Expect the same shape as the canned fork's output with your tenant, your documents, your revision names and your dates. A FAIL here is work, not a verdict: its line names the lesson. The reference fork took the author about a day to make from a working lane; budget the same.

### Change it: one command deleted, one component fails

Delete the command from one FAILURE-MODES entry, and exactly component 7 FAILs; put the file back, and every component passes again.

#### Definition

An entry of `FAILURE-MODES.md` without a command is a symptom nobody can reproduce. The canned fork's first entry, "Pinned traffic hides a change", is proved by `make gotcha-drill ID=pinned-traffic`, lesson 11.7's offline drill. The cell deletes that one line with `sed`, runs the check, then copies the kit's canned file back and runs it once more, printing only the exit code.

- Component 7 FAILs alone. Three entries proved, four or more needed; the first entry's missing piece named: `no command in backticks`. The other seven components are untouched, and they say PASS.

- The verdict is incomplete, not a lower score: `incomplete: component 7 FAILs`, exit 1. The rubric's words are the check's: a missing component is an incomplete submission, and the defence does not run.

- The file back, exit 0. The second check, with its output dropped, says every component passes again.

The kit's own test holds this exact case, `test_change_it_one_failure_modes_command_deleted_fails_that_component_only`, and one more test breaks each component alone and shows that only it fails. If a kit change ever made one FAIL spill into another, that test goes red.

Change the command instead of deleting it and the check says why it would not run. `make gotcha-detect ID=pinned-traffic`: `detects a gotcha, it does not reproduce one`. A script the fork does not hold: `the fork holds no commands/hold-fault.sh`. A `make` target no makefile in the fork defines: `the fork's Makefile and mk/*.mk define no target`. Each is a line under the FAIL, so the fix is never a guess.

### Your lane, read with the two tokens

The three GETs and the one describe by hand, then `make capstone-check PROJECT=`, which makes the same reads and adds them under each component.

#### Definition

With `PROJECT=` the check first reads the project's number (`gcloud projects describe`), builds documind-api's canonical URL from it, and lists the services in `REGION` and in `SLM_REGION`, where the GPU services live. If documind-api is not deployed in `REGION` it stops with exit 2 and says so: the Makefile's default `REGION` is us-central1, and your lane runs in asia-south1, so pass `REGION`. Then, per component:

- 1. GET `/version` as documind-ui-sa must answer 200; GET `/v1/sources` for your tenant as documind-outsider-sa, who is on no roster, must answer 403; and documind-ui, described, must have IAP on.

- 2. GET `/v1/sources` for your tenant as documind-ui-sa must list every document of your corpus folder as `indexed`. A 403 here means documind-ui-sa is on no roster of your tenant's, and the line prints the `make roster` that fixes it.

- 4. The lane's services that the passed smoke needs must be deployed now; for the graph lane, `/version` must say `retrieval_graph` on or auto.

- 8. Both revisions of the recorded rollback must be documind-api's on this lane, from `gcloud run revisions list`.

With a lane, the records narrow too: only smoke runs of this project and region count, and only reports whose `api_url` is this documind-api's. A record another lane left in your checkout proves nothing about this one.

The two tokens are the setup's `tok` and `otok`: ID tokens minted by impersonation, for the API's URL as audience, as `make eval-live` mints them. `make operators` gave your address the token-creator role on both accounts; without it the mint fails and the check stops with the `make operators` line to run.

#### Do it: the reads by hand

Three GETs and one describe, as you. The last line greps documind-ui's description for its IAP annotation; step 9 says why it is greped rather than named.

- 200, then the answer: `/version` as documind-ui-sa names the serving revision's `git_sha`, model and prompt. That is the "member answered" of component 1.

- 403: the outsider's token is valid, and the roster refuses it. The same refusal is every isolation row's, and the lane line under component 1.

- IAP: the annotation `--iap` sets on the service, which the check reads as `iap_on()`.

#### Do it: the check with your lane

Every offline line again, and a `lane:` line under components 1, 2, 4 and 8. Reads only; Rs 0.

- The first line names the lane, `read only`, and the records it reads are now this lane's alone.

- Component 1 gains three lane lines: `/version` as documind-ui-sa 200 with its answer; `/v1/sources` as documind-outsider-sa 403; documind-ui has IAP on.

- Component 2's lane line says the Documents page's read lists all your documents indexed. If it names an absent one, `make ingest-corpus` is the fix and the line says so.

- Component 4 names the lane's services deployed; component 8 says both revisions of the rollback are documind-api's on this project.

Nothing on the lane changed: describe and list calls from the allow-list of 11, two tokens, three GETs. `gcloud run services update`, `update-traffic` and `deploy` are not on the list, and the check's own test proves a write is refused before it runs.

### The handover: HANDOVER.md from the checkout and the lane

The pack the next operator reads: 7 sections, each the checkout's statement and then the lane's, written whole by one command that only reads.

#### Definition

`make handover` writes `HANDOVER.md` into the fork (`--out` puts it elsewhere). Each section gives what the checkout states, from the Makefile, `terraform/*.tf`, `ops/runbooks.json` and the revision files, then what the lane shows, from the same allow-list of reads plus the Monitoring API's alert policies; where the two differ, the lane is what runs. A lane read that fails is listed under `Not read`, the rest is still written, and the exit is 1. The file is written whole each time, so notes of your own belong in `RUNBOOK.md`, and its head says so, naming the runbook's template.

#### The seven sections, and where each comes from

#### The policies, as the checkout declares them

This is the first section's table without the lane column, generated from the same join the handover makes: `remediate.runbooks()`, which stops if `ops/runbooks.json` and `terraform/*.tf` disagree. Of the 17, 9 are in `alerts.tf`, from 8 resource blocks, one of them a `for_each` over the two GPU services.

#### The two lines behind the night job and the budget

#### Do it: the handover, offline, on the canned fork

Without `PROJECT=` every section gives the checkout's half and says the lane was not given. The canned fork is a copy of the kit, so its checkout half is the kit's: the policies, the night job, the floors, the budget and the state bucket as the Makefile and Terraform declare them, plus the canned records under Revisions.

- 58 lines, 7 sections and the tail. The head says who wrote it and when, that it read and changed nothing, and that the lane is what runs where the two halves differ.

- Alert policies: 17 rows, each with its file, when it applies and what to do, and `-` in the lane column, since no lane was given.

- Revisions is the canned fork's: no revision files (a clone has none), the gate record of the repair `documind-api-00043-fix`, PASS, and the last smoke run serving it.

- CI trust has nothing to state: the inputs file `make plan` saves is gitignored, so a clone holds none. State bucket fills the project in as `` for the same reason.

- Not read: `the lane: no PROJECT was given`.

#### Do it: the handover of your lane

In your fork, with `PROJECT` and `REGION`. Reads only. The file lands in the fork's root; the recording is the author's lane.

- Each section gained its lane half. Expect the policies on the lane with their channels, the night job's state and last attempt, a floors table with every service at `0` after `make off` or `1` for the UI on a session day, documind-api's traffic table and revision count, the provider's condition the same as the checkout's, the budget's amount and thresholds, and the state bucket's location and object.

- Not read lists any read that failed, with gcloud's or the API's reason, and the exit is then 1. Step 9 names the reads no lane has answered yet.

- Nothing changed. One file was written, in the fork. The lane was read 7 ways and not touched.

The pack describes a lane that still runs. When it stops, `make down` removes what Terraform and the deploy scripts made, and prints what it cannot remove: only deleting the project does. The next owner should read this list beside the handover.

- Firestore (default): delete_protection_state = DELETE_PROTECTION_ENABLED (firestore.tf) - chunks, ledger, rosters stay

- buckets that hold objects: uploads, datasets, audit (force_destroy = false, storage.tf) - and with AUDIT_LOCK=true the audit bucket's LOCKED retention policy blocks even the project's deletion for five years, by design

- a tuned endpoint from make tune (evals/tune.py: Vertex AI, not Terraform)

- a RAG Engine corpus outside MANAGED_TENANTS (make rag-corpus TENANT= by hand; managed.py: Vertex AI, not Terraform) - it bills storage until deleted: managed-stores-down just removed MANAGED_TENANTS' corpora; gcloud ai rag-corpora ... or 4.3's cleanup cell for the rest

- the BigQuery views make bq-views applied (terraform/sql/*.sql, through bq, not Terraform) - and so the documind_observability dataset that holds them and the log sink's tables (destroy reports it still in use)

- the Vertex AI Search data stores documind-<tenant> once they hold documents (destroy reports Active documents exists): they bill storage until the project goes

- Cloud Run jobs a deploy script made outside Terraform (documind-checkpoint-setup): gcloud run jobs list --region $(REGION)

- the billing account's DocuMind monthly budget for this project (budget.tf): make down leaves it when destroy stops early - remove it under Billing > Budgets & alerts

### The defence, what the author still decides, and what the kit does not do yet

The 90 minutes, the five dimensions row by row with the rubric's notes, the decisions made and those still open, and the lane reads no lane has answered yet.

#### The defence

The rubric's notes for the assessor are worth reading as a learner. Score the system in front of you, not the story: every dimension can be checked live. "I don't know" scores better than a confident wrong answer, because the dimensions reward calibration. A missing component is not a zero on a dimension: it is an incomplete submission, checked before the day with `make capstone-check FORK=`, and the defence does not run. One retry within 30 days, scored by at least one assessor who was not in the first defence.

#### The five dimensions, row by row

Three of the 3s are where the kit's own lessons point. Dimension 1's threshold has the shape of the canned fork's `ARCHITECTURE.md` (a duty cycle above which GKE wins), and the template's last section asks for yours. Dimension 2's 3 is lesson 11.7's table: which failures the monitoring catches, which it does not, and what you did about the second group, which the template's `Caught by:` lines hold. Dimension 4's 3 is lessons 4.1 and 4.7's: the isolation rows that pass by construction, and the outsider's 403 the gate asks beside them.

The components come from lessons 0.3, 1.5, 3.8, 4.1, 4.2, 4.7, 5.4, 7.1, 7.2, 7.5, 8.3, 9.2, 11.3, 11.5, 11.6, 11.7, and this one. The rubric's "where it comes from" column gives 11.8 three shares: the decision record (component 5), the choice of lane (component 4), and the corpus of your own (component 2, with lessons 1.5 and 3.8).

#### The rubric's notes, in its own words

- Component 5 is the one people under-build and the one the defence leans on hardest. An architecture document that lists what you built is a description. One that lists what you did not build, and why, is a decision record — and the interview is sixty minutes of asking why.

- Dimension 1, Architecture. The 3 is not eloquence. It is a falsifiable statement: "we chose Cloud Run because our duty cycle is 4%; above roughly 74% GKE is cheaper and we would move."

- Dimension 3, Cost at 10×. The commonest 2-instead-of-3: the learner scales the bill by ten and stops. At 10× something stops being linear — a quota, a Vector Search replica, a cold-start rate, a per-tenant cache that no longer fits. Naming it is the difference.

- Dimension 4, Evals. Dimension 4's 3 is the hardest point in the rubric and it is deliberately the lesson of 4.1 and 4.7: DocuMind's own `must_not_contain` isolation rows pass by construction, because the retriever filters by tenant before generation. A learner who finds that in their own suite has understood something most teams never do.

- Not on the list: a novel feature. The lane is one of four, chosen not invented. This credential is about shipping and defending, not about ideas.

- Not on the list: test coverage percentage. Component 3 asks for evals of the thing the product does. A coverage number for a RAG service measures the wrong layer.

- Not on the list: uptime. You will have run it for days, not months. Claiming an SLO you have not observed is exactly the kind of answer the rubric penalises under Evals.

#### What the author decided, and what is still open

Four points this page left open were decided on 13 October 2026, and the kit and the page changed with them.

- Templates for the four documents: `capstone/templates/`, step 5. The check's line for a missing document names its template, and `HANDOVER.md`'s head names the runbook's.

- "Your own corpus" is a tenant other than acme, globex and zeta, as the check reads it, and the rubric says so in those words.

- The rubric's lesson numbers and files. Its 17 lesson numbers are all this course's, and the 9 files it cites are all in the kit or the course. This page's build checks both, so a stale number or a missing file stops it.

- Publishing the rubric before 6 December: this page is where learners read it. Step 1 shows its components and dimensions, and this step its defence, its dimensions row by row and its notes, all generated from the rubric itself.

Still open, by the kit's own account, and the page changes when each is decided:

- Three readings the check makes because the kit gives it nothing better: pages counted offline by the worker's rules, since `/v1/sources` returns no page counts; a rollback read from the smoke log, since `make incident` writes no record; and the alert policies and the night job in the handover only, since no rubric check names them.

- Four commercial decisions the rubric leaves to the course owner: the capstone tier's price, the track ID, the length of the upgrade window, and whether the capstone is purchasable without the course. None changes the rubric; all change this lesson's copy.

#### What it costs

Each point is read from the kit or its pull request, and the build asserts each one it can, so this box changes when the kit does.

- It scores nothing, by design. The five dimensions are the defence's. There is no `make` target that grades a document, and there will not be one.

- It reads only the slots it checks. A template's placeholders outside them, the request path, the cost of one answer, the symptoms, survive the check; the grep in step 5 finds them, and the defence reads them.

- Five lane reads no lane has answered yet, by the kit's own account: the IAP annotation's key on a described service (`run.googleapis.com/iap-enabled`, or an `iapEnabled` field, both of which `iap_on()` accepts, which is why step 7 greps for it); the Monitoring API's `alertPolicies` GET with gcloud's access token; `gcloud billing budgets list`, which may need a quota project; the JSON keys `gcloud storage buckets describe` prints; and the scheduler describe's fields. A read that fails lands under `Not read` and nothing else is lost. The author's run settles them.

- The records are the checkout's. `evals/reports/` is gitignored, so a fork cloned fresh has no smoke log and no gate report: the checkout that ran lessons 11.2 and 11.3 is the one to check, or copy the folder.

- The agent lane's extras for the capstone come later than this kit.

### Verify it yourself: the checklist

Eleven checks, each in a step above, each with the value that proves it in your fork or on your lane.

Nothing. Here is what this lesson left, and where:

- On the lane, nothing. Every command only read: describe and list calls, two token mints, GETs on documind-api, the Monitoring API's alert-policy list. No revision was made, no traffic moved, no setting changed.

- In your fork, one file: `HANDOVER.md` in its root, written whole by `make handover`. Commit it with the four documents you wrote from the templates; it is part of the pack.

- On your machine, a copy of the kit under `/tmp/sahyadri`, with Sahyadri Freight's files over it; step 5 put the canned four back after the templates. Delete it when you are done; your checkout is as it was.

- In `evals/reports/`, nothing new. The check reads the records; only `make smoke-deployed`, `make gate` and `make eval-live REPORT=` write them.

Module 12 moves to inference and tuning: lesson 12.1 decides whether tuning is justified at all, from the eval evidence this module taught you to keep.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.8 Complete the independent capstone and operational handover · v5.0

Next: Lesson 12.1 Decide whether tuning is justified and prepare data.
