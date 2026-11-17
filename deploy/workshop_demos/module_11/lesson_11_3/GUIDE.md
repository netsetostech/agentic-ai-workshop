# Lesson 11.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.3_Promote_Rollback_WIX.html`, reviewed at blob `ebc973c7ecc9467df73d5fb1e4b5daf99da5814c`. Learners read that page on the course site; this guide keeps its prose.

Lesson 11.2 left one green verdict, bound to one revision. This lesson moves traffic with it, then breaks the API on purpose and brings it back. `make promote-gated` promotes lesson 11.2's candidate. A candidate with a mistyped model name is judged red by `make gate` and refused, and plain `make promote`, which reads no record, moves traffic to it anyway. `make smoke-deployed` runs the smokes of the services your lane has deployed, and they go red; `make incident` reads the lane and your records, and names the way back. `time make rollback` returns the traffic in seconds, because the old revision never went away. But a rollback moves traffic and nothing else: the service's template still holds the mistyped name, and the next release would start from it. The repair is a new candidate made with what serves, judged by `make gate` and promoted by `make promote-gated`, until `make incident` exits 0.

- Traffic moves by name; the template stays where the last update left it

- The words: promote, .previous-revision, rollback, spec.template, F43, the controlled failure, a forced promote, smoke-deployed, the smoke log, incident, the gated state, the repair

- Before you run anything: set up the shell

- The traffic table, the template and the UI, as the console shows them

- make promote, make rollback and make candidate, and why a mistyped model is a 500

- make smoke-deployed and make incident, line by line

- On your lane: promote, break it, roll back

- On your lane: the repair through the gate, and the proof

- Errors by revision, from the request logs

- What the kit did not build, a promote made by CI, the smokes, and what it costs

- Verify it yourself: the checklist

You will learn why a rollback takes seconds, what it leaves behind, and how `make incident` tells you a release is whole again. Then you will run a controlled failure on your lane: a mistyped model gated red, promoted by force, smoked red, rolled back against the clock, and repaired through the gate until `make incident` exits 0.

### Traffic moves by name; the template stays where the last update left it

What a promote and a rollback change, what they leave alone, and the three checks that say a release is whole again.

A promote moves a name, and a rollback moves it back. `make promote` moves all of `documind-api`'s traffic to the revision `.candidate-revision` names, and first writes the revision serving 100% into `.previous-revision`. `make rollback` moves all of it back to the name in that file. Neither builds nor deploys anything. A revision never changes once it is made, and Cloud Run keeps it when traffic leaves it, so the old revision is still there to take the traffic back: the flip is one call, and the Makefile's comment above `rollback` calls it the fastest rollback there is. Lesson 11.2 put a gate in front of the promote: `make promote-gated` runs `gate-check` on the gate record first. Plain `make promote` still reads no record at all.

The service also holds the settings of its next revision. Besides its traffic table, `documind-api` keeps a template, `spec.template`: the image and the environment variables its next revision will be made from. `make candidate` and `make release-candidate` are both `gcloud run services update` calls. Each makes a revision from the template with its own changes, and leaves the template holding the result. An update keeps every variable it does not name, because environment variables merge across revisions (the Makefile's comments call this F43). A traffic move changes the traffic table and nothing else. So once a bad candidate has been made, the template holds the bad setting, whatever the traffic does afterwards. Promote it and roll it back, and the template still holds it; the next `make release-candidate`, which names only the image and `GIT_SHA`, carries it into the next release.

The controlled failure, and the gated state. This lesson's failure is one letter: `GENERATOR_MODEL=gemini-3.6-flsh`. Nothing in the API checks the model's name when it starts, so the revision starts, `/health` answers and `/version` names the typo. Every answer that reaches the model fails: Vertex AI serves no model by that name, and the API re-raises the error, so `/v1/query` answers 500. The failure is the same on every run, costs nothing in model tokens and needs no code change, which makes it a good drill. It is also all the drill proves: the plumbing of a release, not a model that answers worse, which is never this predictable. `make incident` says when a release is whole again, in what it calls the gated state: the revision serving was judged green by a gate in this checkout; `spec.template` is what serves; and `.candidate-revision` names no revision the gate judged red. A rollback restores the first and leaves the other two broken. Only a new candidate made with what serves restores them, and it reaches traffic through the gate.

A recall, and the master formula. Lesson 11.2's plant releases a batch only against a signed certificate. One morning a batch is made from a master formula with one ingredient code mistyped. Quality assurance fails it, and someone ships it anyway. The complaints start within the hour. The recall is fast, because yesterday's batch never left the warehouse: it goes back on the shelves, and the bad batch comes off. Two things are still wrong. The mistyped code is still in the master formula, and tomorrow's batch will be made from it. And the dispatch board still names the failed batch as the next one to load. The plant is back to normal only when a batch made from the corrected formula has passed its tests and been released against its own certificate. A traffic move is the recall, `spec.template` is the master formula, `.candidate-revision` is the dispatch board, and the repair is a new batch, a new certificate and a release that checks it.

#### Try it: step through the controlled failure

The panel holds the fifteen commands of this lesson as they ran when this page was built: the Makefile's own recipes in `sh`, `commands/release.py` as make runs it, and the kit test's stand-in for `gcloud`, `curl` and `make`, which keeps one lane's revisions, traffic and template in a file. Step 0 is where lesson 11.2 left the lane. Pick a step: the panel shows what the command printed, the lane after it (each revision's traffic, tag, model and verdict, the two files and the template), and `make incident`'s three checks on that state, run after every step.

Built when this page was built, from the kit you clone. Every printed line is the kit's own, from a recipe or from `release.py`, with the stand-in gcloud's progress lines left out; the checks are `make incident`'s verdict on the lane after each command, read from what it printed. The names, the commit and the times are the stand-in's.

Four things to watch. Step 0 is not the gated state either: the revision `make up` released serves, and no gate in this checkout judged it, so it takes step 1's gated promote to get there. From step 5 to step 8 the traffic moves to the mistyped revision and back, and `spec.template` does not move at all. At step 10 the smokes are green and `make incident` still exits 1: two of its three checks fail. And at step 11 the gated state comes back before any gate has run, because the candidate made with what serves puts the template back, and it is not a red revision, only an unjudged one. It still needs step 12's green record before step 13's `make promote-gated` moves traffic to it.

The stand-in's gate decides by one rule: a revision whose `GENERATOR_MODEL` Vertex AI does not serve fails every row, and any other passes them all, which is the rule its smokes follow too. On your lane a row whose retrieval comes back empty is answered without a model call, so the mistyped revision's success rate may not be 0%. Each stand-in smoke prints two checks; yours print their own. And the stand-in cannot time a rollback: `time`'s lines in step 6 are your lane's.

### The words: promote, .previous-revision, rollback, spec.template, F43, the controlled failure, a forced promote, smoke-deployed, the smoke log, incident, the gated state, the repair

Thirteen rows, each with what it is on your lane.

One distinction to hold: neither `make incident` nor `make smoke-deployed` moves traffic or makes a revision. Every traffic move on this page is a make target you run yourself, and `make incident` only says which one comes next.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head. `make smoke-deployed` asks `GET /version` as the first, and step 3 asks the UI as yourself.

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `API` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line. On the lane and in this checkout, lesson 11.2's state: its candidate tagged `candidate` with no traffic, `.candidate-revision` naming it, and its green record in `evals/reports/gate.json`, made within the last 24 hours (if it is older, run `make gate` again first). This lesson moves traffic four times and breaks your API on purpose for a few minutes, between step 6's forced promote and its rollback: run it on your own lane, with nobody else using it. The two gates ask every golden row, about ten minutes each; the repair's costs about Rs 29, the mistyped one's nothing in model tokens.

### The traffic table, the template and the UI, as the console shows them

Where to watch each traffic move, where the template shows itself, and what the UI does on a revision that cannot answer.

#### Definition

The console shows the two halves of a service that this lesson pulls apart. The Revisions tab is the traffic table: every revision `documind-api` has made, each with its share of traffic and any tag. The template has no table of its own. It is what the service would deploy next, and the console's form for a new revision opens filled in with it. The UI is the deployed `documind-ui`, which asks `documind-api` as you, through IAP.

#### Do it: the traffic table

Open Cloud Run in the console, then `documind-api`, then its Revisions tab, and keep it open beside the shell through step 6. Before step 6, the revision lesson 11.2 judged sits at 0% under the tag `candidate`. Reload after each command: `make promote-gated` puts it at 100%; `make candidate` adds a revision at 0% and moves the tag to it; `make promote` moves the 100% to that revision; `make rollback` moves it back. No revision disappears at any point, which is why the rollback can be one call.

#### Do it: the template, after the rollback

After step 6's rollback, open Edit and deploy new revision on `documind-api` and look at the container's variables, changing nothing. `GENERATOR_MODEL` reads `gemini-3.6-flsh`, although the revision serving 100% runs `gemini-3.6-flash`: the form shows the template, not what serves. Then cancel. Deploying from the form as it stands would make one more revision from the template, typo and all, and with the form's defaults send it the traffic.

#### Look: the UI on the mistyped revision

If you want to see what a user would see, ask the UI one question in the minute between step 6's forced promote and its rollback, then go straight on. The UI's chat streams from `/v1/stream`, which sends the sources it retrieved before the model's first word, so the sources may appear before the answer fails. The UI then shows one of its stream errors, The answer stream failed or The stream ended without a completed answer, depending on how the broken stream ends. Nothing on this page records it, and nothing depends on it.

The console can show you both halves, but only one at a time, and nothing on it says that they disagree. The Revisions tab looks healthy after the rollback; the form looks like a routine edit. `make incident` puts the two side by side, and step 6 reads them a third way, from Cloud Run's own API.

### make promote, make rollback and make candidate, and why a mistyped model is a 500

The three recipes that move traffic and make revisions, line by line; then the lines of the API that turn a mistyped name into a 500 and still name it on /version.

#### Definition

None of this lesson's traffic moves needs new code. `make candidate`, `make promote` and `make rollback` are recipes in the kit's Makefile, unchanged by this lesson, and lesson 11.2's `make promote-gated` runs `make promote` as its second line. What makes them a release procedure is the order you run them in, and the two files between them: `.candidate-revision`, which `make candidate` writes and `make promote` reads, and `.previous-revision`, which `make promote` writes and `make rollback` reads.

#### The code: a candidate

`make candidate` is one `gcloud run services update` with `--no-traffic --tag candidate`: a new revision made from the template with the settings it names, taking no traffic and reachable at a URL of its own. Its recipe names 14 settings, and each one it passes takes the Makefile's default unless you set it on the command line (two pass only when `RETRIEVAL_BACKEND` is set, and `GENERATOR_LOCATION` is removed when it is not), so on a lane serving the defaults `GENERATOR_MODEL=gemini-3.6-flsh` changes exactly one thing. Its last two lines record the revision's name for `make promote` and print the tag URL. The comment above it is the F43 warning: variables merge across revisions.

#### The code: a promote and a rollback

`make promote` reads the traffic table once and refuses if the candidate tag has moved to a revision the file does not name. Then it writes the revision serving the most traffic into `.previous-revision`, moves 100% to the candidate by name, and asks `/version` on the service's URL as `documind-ui-sa`, so the last thing it prints is what now answers. `make rollback` is one line: 100% to the name in `.previous-revision`. Neither recipe reads a gate record, and neither touches the template.

#### The code: why the mistyped model is a 500, and why /version still names it

The API sends every answer through `_call_or_fallback()`. It catches one error only: a 429 from a routed tier, the model the `ROUTING` setting picked when that tier's quota runs out, which it answers with the default model instead. Any other error is raised again. With `GENERATOR_MODEL=gemini-3.6-flsh` the model is the default, Vertex AI answers that it has no such model, and the error rises out of `/v1/query` as a 500, with no fallback. That is the behaviour you want: a fallback would hide the typo behind a working answer, and the gate would have passed it.

`/version` answers from the settings, not from the model, so it names the typo and never calls Vertex AI. That is what lets the gate, the smokes and `make incident` say which model each revision was told to use, even when that model does not exist.

#### The code: smoke-all, and why it is red on most lanes

`make smoke-all` runs eight smokes in one loop, each with the API's URL and the lane's identity exported, and decides by each smoke's own exit status, which it writes to a file inside the pipeline because `/bin/sh` has no `pipefail`. The loop runs eight, the gateway's and the SLM's among them (its comment said seven until 13 October 2026). On a lane without Module 9's `documind-gateway` and `documind-slm`, those two fail whatever the API does, so `make smoke-all` cannot be this lesson's proof.

### make smoke-deployed and make incident, line by line

The two targets this lesson adds, the smokes they choose, the three checks and the repair line; then the kit's own tests, and the controlled failure as release.py prints it.

#### Definition

Both targets are in `mk/release.mk`, under lesson 11.2's two, and each is a subcommand of `commands/release.py`, standard library only, which runs the same without make. Neither writes to Google Cloud. `smoke-deployed` reads which Cloud Run services exist, runs `make smoke-all`'s own smokes for the ones that do, and appends a line to the smoke log. `incident` reads the service, its revisions, the gate record, each revision's gate report and the smoke log, prints the timeline, and checks the gated state.

#### The code: the two targets

#### Which smokes run

`SMOKES` is `make smoke-all`'s list in its order, each smoke with the Cloud Run services its recipe calls; `smoke-deployed` stops if the two lists ever differ. `choose_smokes()` keeps a smoke only when every service it needs is deployed, with `documind-slm` looked up in `SLM_REGION` and every other service in `REGION`.

The answers column is read from the smoke scripts, and `build.py` checks them on every build: the member's question in four of them, smoke-chat's four brains, and smoke-reindex's two questions. It is what one run asks of a healthy revision; step 9 prices it.

#### A smoke run, recorded

Before the smokes, `cmd_smoke_deployed()` reads the traffic table and asks `GET /version` on the service's own URL as `documind-ui-sa`. If `/version` cannot be read, the smokes still run, and the log says why. Without `documind-api` in `REGION` there is nothing to smoke, and it stops with exit 2.

Then each chosen smoke runs as `make smoke-all` runs it: through make, with the same exports, its output filtered by the same pattern, and its own exit status recorded. Afterwards it reads the traffic table again: if the traffic moved during the run, the results may come from two revisions, and the log line says so. The line goes to `evals/reports/smoke-deployed.jsonl`, beside the gate's reports and ignored by git.

#### What judged a revision

`judged()` answers from your checkout's records only: the gate record when it names the revision, otherwise the revision's own report beside it, which `make gate` wrote as `gate-` and the revision's name. The record holds one revision at a time, so after the repair's gate it names the repair, and the mistyped revision's red verdict is read from its own report. A revision no gate in this checkout judged, such as one `make up` released, has no verdict at all.

#### What differs from what serves, and the line that repairs it

`drift()` compares the template with the revision serving: the image, then every variable, a secret by the reference it names. `repair_steps()` turns the differences into make lines. The image and `GIT_SHA` go back with `make release-candidate` and the serving tag. A setting `make candidate` passes goes back with `make candidate`, which names every setting the serving revision runs at other than the Makefile's default, because it passes them all and one left out would return to its default. Anything else goes back on the template by hand, with no traffic. Then `make gate` and `make promote-gated`, always.

#### The timeline, and the three checks

`cmd_incident()` reads the service once, for its traffic and its `spec.template`, lists the revisions, and loads the gate record, the smoke log and the two files. The template keeps the tag a deploy gave its image, `api:COMMIT`; a revision holds only the digest Cloud Run resolved that tag to when it made the revision, `api@sha256:` and 64 hex digits. A tag never equals a digest, so `drift()` is handed the template's image as the revision the template made last (`status.latestCreatedRevisionName`) holds it. The timeline is every revision made in the window with its image (its digest, cut to 12 hex digits), `GENERATOR_MODEL` and verdict, the gate record's finish, and every smoke run, with a traffic move inferred wherever two runs in a row saw different revisions serving. The events are sorted by time, not by the order they were read in.

The second half prints the state now and checks the gated state. A red revision serving gets the rollback as its repair: `make rollback` when `.previous-revision` names another revision, or a traffic move by hand to a revision the gate judged green when it does not. Otherwise `repair_steps()` builds the line. When the template holds exactly the recorded candidate, and the gate has not judged that candidate red, it says so first: the candidate may be the change you mean to release, and the line it prints then is the gate and the gated promote.

#### Do it: the kit's own tests

`commands/tests/test_release_repair.py` runs this lesson against lesson 11.2's stand-in `gcloud`, extended with the template, `gcloud run services update`, the service and revision lists, and a stand-in `make` for the smokes. Where a POSIX `sh` is installed, as in Cloud Shell, 2 of its tests run the Makefile's own recipes: the whole controlled failure from `make promote-gated` back to the gated state, including that a `make release-candidate` after the rollback inherits the typo, and `make smoke-deployed` itself, with its one HTTP request caught by a local proxy. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a few minutes.

#### Read it: the controlled failure on the stand-in lane

The same stand-in, driven by this page's build through the recipes, as the stepper in step 1 shows it. The mistyped revision is `documind-api-00042-qqq`, lesson 11.2's candidate `documind-api-00041-kel` and the repair `documind-api-00043-rrr`. All three were made from the image `api:COMMIT`, so all three hold the one digest that tag named; the revision `make up` released, `documind-api-00040-abc`, holds `api:PREVIOUS`'s. First the gate on the mistyped revision, red:

Then `make promote-gated`, refused from the record, and plain `make promote`, which moves the traffic anyway:

The smokes on the mistyped revision, and `make incident`, which names the rollback:

After `make rollback` the smokes are green, and `make incident` names the two checks still failing, and the repair:

And after the repair, gated and promoted, the proof:

Every line above came from the kit, run on this page's build: the recipes' own echo lines and `release.py`'s, nothing paraphrased. Three things to notice. `make promote-gated` refused from the record alone, and `make promote` never looked at it. The rollback fixed the smokes and not the incident: the template kept `gemini-3.6-flsh`, and `.candidate-revision` kept naming the red revision. And the repair line came from `make incident` itself, computed from what serves, so on a lane whose serving revision runs other settings it names those too.

### On your lane: promote, break it, roll back

Lesson 11.2's candidate promoted through the gate; a mistyped model gated red, refused and forced; the smokes and the incident; the rollback, timed; then the template, read from Cloud Run's own API.

#### Definition

Ten of the fifteen commands, in one sitting and in this order. The first promotes the revision lesson 11.2 judged. The next six make the failure and read it: a candidate with the mistyped model, its gate, the refusal, the forced promote, the red smokes, and the incident that reads them. From the forced promote until the rollback your API answers 500 to every question, so run those cells one straight after another. Then the rollback, timed, and the smokes and the incident again.

#### Do it: promote lesson 11.2's candidate

`gate-check` reads lesson 11.2's record, the files first and then the lane; when every check passes, `make promote` moves the traffic and prints what `/version` now says.

`stale: the gate finished ... hours ago`: more than 24 hours have passed since lesson 11.2's gate, so run `make gate` again, then this cell. `another revision`, or `the candidate tag is on ...`: a revision was made after lesson 11.2's gate; make one candidate again, as lesson 11.2's step 5 box says, and run `make gate` on it. `there is no gate record`: lesson 11.2's gate ran in another checkout, or not at all.

#### Do it: the mistyped model, as a candidate

`make candidate` makes a revision from the template, with every setting it passes at the Makefile's default except the one you name. It takes no traffic, gets the `candidate` tag and goes into `.candidate-revision`.

#### Do it: the gate on it

The same gate as lesson 11.2's, on the revision the file now names: about ten minutes of rows, and every row that reaches the model fails. `run_eval.py`'s lines stream between the gate's two blocks. The verdict is recorded, red, and make reports `release.py`'s exit 1 on its last line, `Error 1`, before exiting 2 itself.

#### Do it: refused, then forced

First `make promote-gated`, which the red record stops at its first recipe line, line 46 of `mk/release.mk`, so its `make promote` never starts. Then plain `make promote`, which reads no record and moves all the traffic to the mistyped revision. Go straight on to the next cell.

#### Do it: the smokes, and the incident

`make smoke-deployed` names the smokes it skips and runs the rest; `make incident` reads what the smokes logged, with the gate record and the lane.

The smokes fail wherever their question reaches the model, and `make incident` finds a revision the gate judged red serving: its `Repair:` line is the rollback, to the revision `.previous-revision` holds. Run it now.

#### Do it: the rollback, timed

`time` is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes.

Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of `documind-api`'s traffic and the model that revision runs, and runs `make rollback` only while that model is `gemini-3.6-flsh`. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names `gemini-3.6-flsh` until step 7's repair deploys a good revision.

#### Do it: the smokes and the incident, after the rollback

The smokes pass: the revision lesson 11.2 judged serves again, and `/version` names `gemini-3.6-flash`. `make incident` still exits 1. Its timeline now holds the whole failure, with the traffic move between the two smoke runs, and two checks still fail: `spec.template` holds `gemini-3.6-flsh`, and `.candidate-revision` names the red revision. Note its `Repair:` line; step 7 runs it.

#### Read it: the template, from Cloud Run's API

The cell reads `documind-api` and its revisions from the Cloud Run Admin API's v1 resources, the same JSON `gcloud run services describe --format=json` prints, without `release.py`: each recent revision's traffic, tag, image and model, then the template's, and whether the template is what serves. Each revision's image is a digest and the template's a tag, so the cell compares the template through the revision it made last, as `make incident` does. Run it now, before the repair, while they differ.

#### Read it: what make release-candidate would make now

The rollback left a trap for the next release. `make release-candidate`, the target a real release uses, names only the image and its `GIT_SHA`, so it starts from the template. On the stand-in lane, in its state after the rollback, it made a revision that runs `gemini-3.6-flsh`, and the gate judged that one red as well. There is no need to make it on your lane: the kit's recipe test does the same and checks it.

You made a red revision serve, saw the smokes and the incident name it, and moved the traffic back in one call. The rollback was fast because nothing was built: the revision lesson 11.2 judged had been there all along. But it restored only the first of `make incident`'s three checks. The template still holds the typo, in `make incident`'s reading and in Cloud Run's own API, and the next release would carry it. Step 7 puts the template back the only way it goes back: with a new revision.

### On your lane: the repair through the gate, and the proof

A candidate made with what serves, judged by make gate and promoted by make promote-gated; then the smokes, and make incident exiting 0.

#### Definition

The repair is three targets you already know. `make candidate` makes a new revision with the settings that serve, which puts the template back. `make gate` judges it, because a revision nobody judged is no better evidence than the one that just failed. `make promote-gated` moves the traffic, so the record is checked before it moves. That is why the kit has no repair target of its own: the repair is a new revision, and a new revision goes through the gate.

#### Do it: the repair candidate, and its gate

Run the `Repair:` line your `make incident` printed after the rollback. On a lane whose serving revision runs the Makefile's defaults it is the first line below; if yours names more settings, use yours. Then the gate: about ten minutes and about Rs 29.

#### Do it: promote it through the gate

#### Do it: the proof

The smokes of your deployed services, then `make incident` on the lane as it is now. The proof is both: `make smoke-deployed` exits 0, and `make incident` exits 0 with the gated state.

The repair revision serves, judged green by a gate in this checkout. The template holds what serves, because the repair candidate was made with those settings. `.candidate-revision` names the repair, so no red revision is recorded, and `.previous-revision` names lesson 11.2's revision, so a `make rollback` now would return there. The mistyped revision is still in the list at 0%, and its red verdict is still in its own report: Cloud Run keeps every revision, and your checkout keeps the evidence. `make incident`'s timeline, with `/version` before and after the rollback in the smoke runs, is the record of a rollback that lesson 11.8's capstone asks you to show.

### Errors by revision, from the request logs

Cloud Run's own record of every request documind-api answered, counted by the revision that answered it.

#### Definition

Everything `make incident` reads is either the lane's state now or a record this checkout wrote. Cloud Run keeps a third record that neither can edit: a request log line for every request a revision answers, written to Cloud Logging under `run.googleapis.com/requests`, labelled with the revision and carrying the HTTP status. The cell reads those lines for the last three hours with the Cloud Logging API's `entries:list`, page by page, and counts them by revision and status class, with the paths and the time span of every 5xx.

#### Do it: the requests, by revision

The 5xx lines belong to one revision, the mistyped one: the gate's rows on its tag URL, and the smokes while it served. Lesson 11.2's revision and the repair answered without them. One caveat when you read the counts: a streamed answer sends its status before the model is called, so a broken stream from the UI is most likely logged as a 200, not a 5xx. The smoke log holds the other half of the evidence, each run's `/version` before the rollback and after, and `make incident` prints both side by side.

### What the kit did not build, a promote made by CI, the smokes, and what it costs

The two targets the kit left out on purpose, the rollback a CI promote leaves you without, the smokes this page does not use, the drill's limits and the rupees.

#### No repair target, and no timed-rollback target

The kit adds two targets for this lesson and stops there. The timed rollback is `time make rollback`: the flip is one call, and the before and after are already in the smoke log, which `make incident` reads. There is no repair target, on purpose. A rollback cannot put the template back; only a new revision can, and a new revision is a candidate like any other, which needs `make gate` before `make promote-gated` moves traffic to it. A one-word repair would have to skip the gate or hide it.

#### A promote made by CI

Lesson 11.1's workflow promotes with plain `make promote` on a GitHub runner, after its reviewer approves. That `make promote` writes `.previous-revision` on the runner, and the runner is gone when the job ends. Your checkout's `.previous-revision` is then either missing, and `make rollback` refuses and prints the lines to do it by hand, or left over from your own last promote, and `make rollback` would move traffic to that older revision. `make incident` prints the name it would return to, so read it before you run the rollback. Without the file it names a traffic move by hand instead, to a revision the gate judged green.

#### make smoke-all, and plain make smoke

`make smoke-all` stays as it is, eight smokes, for a lane with Module 9's services. Plain `make smoke`, the API's smoke alone, reads `DOCUMIND_API_URL` from your shell and nothing from `PROJECT`. The setup block exports `API`, not `DOCUMIND_API_URL`, so on its own it prints that the variable is not set and exits 2. `make smoke-deployed` hands every smoke the lane's URL and identity, as `make smoke-all` does. To run the one smoke by hand: `DOCUMIND_API_URL=$API DOCUMIND_PROJECT=$PROJECT DOCUMIND_TENANT=acme make smoke`.

#### What the drill proves, and what it does not

- It proves the plumbing. A red verdict recorded and refused, a forced promote seen by the smokes and the incident, a rollback in one call, a repair through the gate. Every step is the same on every run.

- It does not show that a worse model would be caught. A prompt or a model that answers worse fails no request: `/v1/query` answers 200, the smokes pass, and only the gate's thresholds (lesson 4.2) can see it, in the rows it misses.

- The smokes are not the gate. A green `make smoke-deployed` says each surface answered its question with citations, and nothing about the other rows.

- A make target is not a lock. Plain `make promote` moved traffic to a red revision in step 6 because nothing stops it, and the same is true of a traffic move typed by hand with `gcloud`.

Lessons 11.1 and 11.2 say it, and it matters most here: `documind-cd.yml`'s other path rolls a Cloud Deploy release of `run-service.yaml` out over `documind-api`, with settings that are not your lane's (lesson 11.1 reads them). It would make a revision no gate judged and a template that is not what served before, which is everything this lesson repairs. Dispatch with `-f path=candidate` only.

#### What it costs

The two gates ask the same rows: the repair's pays for 65 answers, and the mistyped one's pays for none, because every model call it makes is refused. The smokes are the part this page cannot price from the kit alone: their answers are counted above, and the agent brains, the image and the uploads come on your bill.

### Verify it yourself: the checklist

Fourteen checks, each one block above, each with the value that proves it on your lane.

In the cloud: the repair revision serves 100% of `documind-api` and carries the `candidate` tag; lesson 11.2's revision and the mistyped one are still in the list at 0%, with no tag; `spec.template` holds the repair's settings. In this checkout: `.candidate-revision` names the repair, `.previous-revision` names lesson 11.2's revision, `evals/reports/gate.json` holds the repair's green record with the mistyped revision's red report beside it, and `evals/reports/smoke-deployed.jsonl` holds three runs, all ignored by git. The repair's gate and the two healthy smoke runs left their usage rows; the mistyped revision's failed requests left none, because a request that fails before its answer writes no row. Keep the repair revision serving, and put acme's pin back now, with the setup section's pin-back window.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.3 Promote, roll back and repair a controlled failure · v5.0

Next: Lesson 11.4 Debug a wrong answer through the complete pipeline.
