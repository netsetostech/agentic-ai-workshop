# Lesson 11.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.7_Production_Gotchas_WIX.html`, reviewed at blob `3b7c21fe9698327c5c705df17b12bee0ccfc497a`. Learners read that page on the course site; this guide keeps its prose.

An eval row asks one question of whichever revision answers, and judges the answer. It cannot see the lane around the answer: which revision is answering, which settings it was made with, what the next routine deploy will put back, what the month's reports leave out, and what no alert reads. The kit keeps 13 such failures in one registry, `ops/gotchas.json`. Each comes with its symptom, why no eval row catches it, a drill that reproduces it, a detector that finds it on a lane, and the lever that fixes it.

In this lesson you read the registry and run every offline drill, at Rs 0. Then you run the two drills that have a lane form on your own documind-chat: traffic held on an old revision, and a setting made by hand that a routine deploy drops. Each one puts the chat back as it was, and the detectors then read your lane.

- What production shows and no eval row does

- The words: gotcha, registry, signal, drill, stand-in, detector, lever, evidence, held traffic, template, hand-set setting, routine deploy

- Before you run anything: set up the shell

- The registry, read at Rs 0

- The lines the two drills rest on

- Every offline drill, on a stand-in of Cloud Run

- Your two services, as Cloud Run's API returns them

- The two drills on your lane

- The detectors: what your lane shows now

- The release no gate judged, loud against silent, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn why a passing eval says nothing about which revision answers or which settings it carries, and how the kit's registry reproduces, finds and fixes 13 such failures. Then you will prove it on your lane: two live drills reproduce their gotchas and leave documind-chat as it was.

### What production shows and no eval row does

An eval row judges an answer. The registry names what goes wrong around the answer, and how to reproduce, find and fix each one.

An eval row judges an answer, not the lane. The gate (lessons 4.3 and 11.2) sends the golden rows to a candidate revision and reads every reply. That is the right test for a model, a prompt or a retriever. It is blind to three kinds of failure:

- Which revision answers. Change a setting on a service whose traffic is held on a named revision, and you get a new revision that takes none of the traffic. The rows still pass, on the old revision.

- What the next deploy puts back. Every deploy script sets its service's whole environment with `--set-env-vars`. A variable set by hand holds until the next routine `make deploy-services`, and then it is gone. The rows still pass, on the default.

- What nobody reads. A turn stopped at its call cap answers HTTP 200. A search the turn gave up on still bills. The agents' own model calls are in no report of the month. No alert policy reads any of it.

The registry names 13 of them, in `ops/gotchas.json`. Every entry carries the same five things:

- the symptom;

- why no eval row catches it;

- a drill that reproduces it;

- a detector that finds it on a lane and changes nothing;

- the lever that fixes it.

Each entry also names the kit lines it rests on, word for word: 39 lines in 16 files. If the kit changes so that a drill no longer reproduces its gotcha, the kit's tests fail until the entry is marked fixed, with the test that proves it.

Loud or silent. Of the 13, 2 are loud: something pages or goes red on its own. A poison upload pages through the dead-letter policy, about an hour after the upload. A token minted for a candidate's tag URL makes the gate itself go red. The other 11 are silent: nothing in the kit pages on them, and the detector is the only watch.

Drills at Rs 0. An offline drill runs on a stand-in of Cloud Run, or on the kit's own code, with no lane and no credential; 9 entries have one. The stand-in is the JSON that `gcloud run services describe` prints, changed only by the gcloud and make lines a lane would run. A lane form exists for 7 entries. Two of those are the kit's own live drills, on documind-chat, and neither makes a model call: pinned traffic, and a routine deploy that drops a hotfix. The other 5 are commands other lessons teach, such as `make limits-drill` and `make poison`.

A carmaker's service bulletins. Every car leaves the plant after the end-of-line test: brakes, lights, emissions, a run on the rollers. Some faults never show on the rollers: a seal that whistles only above 100 km/h, a sensor that trips only after a week of monsoon rain. When the field reports enough of one fault, the carmaker sends every dealer workshop a bulletin. It gives the symptom the owner describes, why the end-of-line test passes the car, how to reproduce the fault in the workshop, the check that finds it on any car that comes in, and the fix. The workshop runs the check on every car it services, without waiting for the owner to complain.

The registry is the bulletins. An eval row is the end-of-line test. A drill reproduces the fault in the workshop or on the car itself, the detector is the check, and the lever is the fix.

#### The registry as a board

Filter by signal, by drill and by lesson. Then open a gotcha to read its symptom, why no eval row catches it, its drill, its detector, its lever and the kit lines it rests on.

Generated from the kit's `ops/gotchas.json` when this page was built. First the build ran the registry's own rules, `gotchas.problems()`: every field present, and every drill and check it names is one that `commands/gotchas.py` runs. Then it ran `gotchas.kit_problems()` on the kit behind each entry: every evidence line still in its file, the one alert policy it names declared in terraform, and every log event a detector reads written by a service. Every lesson the registry names is in the course's manifest. A check in Node compares the board's filter with the registry on every choice.

`make deploy-services` with its default `SCRIPTS` redeploys documind-api from your checkout. So does `make up`, which runs it. Then it moves 100% of the API's traffic to the revision it just made, by name, with no gate. After a gated promote (lessons 11.2 and 11.3), `GET /version` then names a commit no gate judged.

To deploy the other services, leave the API's script out: `make deploy-services SCRIPTS=commands/lesson-12.8.sh` deploys the chat alone. Step 9 drills this at Rs 0.

It is the registry as the kit holds it, not your lane. Your lane's state is what the detectors read, in step 8.

### The words: gotcha, registry, signal, drill, stand-in, detector, lever, evidence, held traffic, template, hand-set setting, routine deploy

Fourteen rows, each with the value it takes on your lane.

One distinction to hold: `--update-env-vars` merges, and `--set-env-vars` replaces. A hand update merges, and so does `make candidate`; a routine deploy replaces. The board's first five entries follow from that one difference, and from where the traffic is held.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head: make smoke-chat and the drills' /health reads call as documind-ui-sa, and every gcloud line runs as you.

You need the shell in the kit's folder, with `PROJECT`, `REGION` and `ME` set.

- Steps 3 to 5 are offline: nothing leaves your machine.

- Step 7 changes documind-chat for a few minutes, twice, and puts it back each time. Its second drill runs a routine deploy of the chat alone, which builds the chat's image from your checkout.

- Step 9's Change-it edits `ops/gotchas.json` in your clone, and git puts it back.

### The registry, read at Rs 0

One file of 13 entries, the three make targets that run them, and one entry read in full.

#### Definition

`make gotchas` prints the registry, one line per gotcha: its id, its signal, which drills it has, its status, the lessons it touches and its title. `ID=` prints every field of one entry. Each target is one line in `mk/operations.mk` that runs `commands/gotchas.py`, so the same command runs without make: `python commands/gotchas.py list`.

#### Do it: the registry

#### Do it: one entry, every field

Here is the same entry as the file holds it. A new entry takes this shape, and step 9 adds one.

- One id per gotcha, each a few words joined by hyphens, in the order the board shows them. Of the 13, 9 have an offline drill and 7 a lane form; 3 have both.

- The entry rests on 5 kit lines, marked `kit` in the output: the chat's deploy, its hook for more variables, the Makefile's empty `CHAT_EXTRA_ENV`, the API's deploy, and the cap's default in `limits.py`. Step 4 shows the chat's lines and the cap's in their files, and its cell reads the API's deploy with the rest.

- Nothing was called. The registry is a file, and these targets only read it.

### The lines the two drills rest on

Where documind-chat's traffic is held, what its deploy writes, where its cap comes from, and the check both live drills make first.

#### Where the traffic is held

A Cloud Run service's traffic either follows its latest revision or names one. `make candidate`'s `--no-traffic` pins the service to a named revision. The Makefile's comment says what happened when nobody noticed: a routing change ran on the old revision for an hour (F44). So after the API's deploy, `make deploy-services` moves documind-api's traffic by name, to the revision it just made. `make promote` and `make rollback` move it by name too. documind-api is held by name on purpose. documind-chat follows its latest revision, until something holds it.

#### What a deploy writes

The chat's deploy script sets the service's whole environment with `--set-env-vars`: 10 variables, then `${CHAT_EXTRA_ENV-}` at the end, the script's hook for more. `make deploy-services` sets that hook to the empty string for every deploy. A variable the list does not name is gone after the deploy.

#### Where the cap comes from

`limits.py` reads `CHAT_MAX_MODEL_CALLS` once, when the module loads, which is when an instance of a revision starts. `/health` publishes it. So `/health` reports the cap of whichever revision answers.

#### The check before a drill

`limits-drill.sh` (lesson 5.5) refuses to change the chat when its latest revision does not take all the traffic: the change would make a revision that serves nobody. `gotchas.py` makes the same check on the same JSON, and both live drills run it before they change anything.

#### Do it: what each routine deploy writes

The cell loads the kit's own reader of the deploy scripts, the one the drills and the detectors use, and prints what each deploy writes. It reads the scripts and the Makefile, and calls nothing.

- Every one of the 7 deploys sets its service's whole environment with `--set-env-vars`. Every hand-set variable on every service is one routine deploy away from gone.

- documind-chat's list has 10 names, and `CHAT_MAX_MODEL_CALLS` is not one of them. A cap set by hand is dropped, and the default, 12, comes back.

- The switches the recipe passes go back to the Makefile's defaults unless you pass them again, `ADMIN_EMAILS` among them. Step 8's detector finds that one on every lane deployed with your own address.

### Every offline drill, on a stand-in of Cloud Run

The two Rs 0 drills in full, with their levers clearing them; then all 9 at once.

#### Definition

An offline drill runs on a stand-in of Cloud Run: the JSON that `gcloud run services describe` and `gcloud run revisions describe` print. Only two things change it: the gcloud lines a lane would run, and make's targets, played from the kit's own recipes. The stand-in plays four of Cloud Run's rules:

- `--update-env-vars` merges into the variables already there;

- `--set-env-vars` replaces every literal variable;

- a new revision takes traffic only when a traffic entry follows the latest revision;

- `--no-traffic` first binds what followed the latest to the revision that was latest.

Its `/health` reports the answering revision's own cap. The live drill in step 7 is the same function, on your lane.

#### Do it: pinned traffic

The stand-in started where `make deploy-services` leaves documind-chat: `documind-chat-00001-mup` takes 100% of the traffic, following the latest revision, and `/health` says 12, the default in `limits.py`.

- The traffic held on that revision by name is what a rollback by traffic leaves behind.

- The hand update made `documind-chat-00002-zeq` with a cap of 3. It takes 0% of the traffic. The template says 3, and `/health` still says 12: every request is answered by the old revision. Nothing failed.

- The detector named both halves: the traffic is held away from the latest revision, and the newest revision takes nothing and carries no tag.

- The lever moved the traffic to the latest revision, and `/health` said 3. The last line put the setting back as it was, unset, and the chat follows its latest revision again.

#### Do it: a routine deploy drops a hotfix

- The hand-set cap of 8 served: `/health` said 8.

- Before the deploy, the detector named the drop. The variable is not in `lesson-12.8.sh`'s `--set-env-vars`, and `make deploy-services` empties `CHAT_EXTRA_ENV`.

- The routine deploy, played from the script's own list, made a revision without the variable, and `/health` said 12 again. Nothing failed here either.

- The lever is a change to your fork: a deploy that carries the setting keeps it. With `CHAT_EXTRA_ENV='|CHAT_MAX_MODEL_CALLS=8'` in the recipe, the cap survived the deploy, and the detector found nothing to drop. Then the stand-in deployed as the kit does, and the chat was back where it started.

#### Do it: every offline drill

The command runs all 9 drills, and `grep` keeps each drill's verdict lines: its name, `REPRODUCED`, `CLEARED` where it shows its lever, and the count at the end. Run `make gotcha-drill ID=` to read any one of them in full.

All 9 offline drills reproduced their gotcha, and the 6 that show a lever cleared it. Besides the two above, here is what the other drills show.

### Your two services, as Cloud Run's API returns them

Where each service's traffic is held, its newest revision, and its template against the revision that answers: the state the live drills start from.

#### Definition

`gcloud run services describe --format=json` prints what Cloud Run's Admin API v1 returns for a service, and step 5's stand-in is shaped like it. The cell asks the API directly, as you, with your gcloud access token: first documind-chat, then documind-api. For each service it prints three things:

- the newest revision;

- every traffic entry, and whether it follows the latest revision or names one;

- the variables on the template that the serving revision does not have.

In the console, Cloud Run lists each service's revisions with the share of the traffic each one takes.

#### Do it: the two services, before the drills

Read the two services against what the drills need.

- Expect documind-chat to follow its latest revision, so that a change to it serves at once, with its template matching the revision that answers. Its cap should read unset, so the default of 12 in `limits.py` applies. That is the state both live drills require, and the state they must leave.

- Expect documind-api to be held by name, on the revision that `make deploy-services`, `make promote` or `make rollback` put there. A candidate waiting for the gate shows as a tagged entry at 0%, its template ahead of the serving revision.

If documind-chat reads `held by name`, both live drills refuse to start. Read the template line first: moving the traffic with `gcloud run services update-traffic documind-chat --to-latest`, the lever of pinned traffic, serves whatever the newest revision carries.

### The two drills on your lane

Pinned traffic, then a routine deploy that drops a hotfix, each on documind-chat and each putting it back; then the chat's smoke.

#### Definition

The live drills are step 5's two functions with a lane under them: gcloud and make found on your PATH, and `/health` read as `make limits` reads it, as documind-ui-sa. Each one refuses before it changes anything when documind-chat's traffic does not follow its latest revision. Each one puts every setting back from a `finally` block, so a failure halfway restores the chat too. If the restore itself fails, it prints the two gcloud lines that finish the job.

#### Do it: pinned traffic, on your lane

documind-chat changes for a few minutes: two new revisions, four `/health` reads, and no model call.

The recording shows the lines step 5 printed, on your lane:

- the serving revision, and `/health` at 12;

- the traffic held by name, and the cap of 3 by hand;

- the new revision at 0%, with `/health` still at 12, the detector's two lines, and `REPRODUCED`;

- the lever, `/health` at 3, and `CLEARED`;

- the restore: the variable removed (it was unset before), the chat on its latest revision, and `/health` at 12.

That is the first half of the proof: a live drill reproduced its gotcha and left the chat as it was.

#### Before the second drill: four refusals

The second drill runs a routine deploy, so it checks more before it changes anything.

- The traffic must follow the latest revision, as for the first drill.

- Nothing else may be on the chat that the deploy would change. The drill's routine deploy would drop that too, and the lane would not be as it was. If you ran lesson 6.7, its `LESSON113_RESTART` is still on documind-chat: the drill stops and prints the gcloud line that removes it.

- Your checkout must be at the commit the chat's image was built from, because the routine deploy rebuilds the image from your checkout. If it is not, the drill stops and names two ways out: check out that commit, or redeploy the chat from your checkout first. Redeploying is the safer of the two, because an older commit may predate `commands/gotchas.py` itself: `make deploy-services SCRIPTS=commands/lesson-12.8.sh PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"`, about four minutes.

- `ADMIN_EMAILS` must be yours. `make deploy-services` ends with `make operators`, which grants token minting to each address in it.

#### Do it: a routine deploy drops a hotfix, on your lane

Most of its time is the chat's image build, about four minutes. No model call.

- It opened as step 5's drill did: the image's tag, nothing the next deploy would change, and `/health` at 12.

- The cap of 8 by hand served (`/health` at 8), and the detector named the drop before the deploy.

- The routine deploy ran, with make's own output: the chat's image built from your checkout, and the service deployed from its script's list. After it the variable was gone and `/health` said 12: `REPRODUCED`.

- The lever is a change to your fork, so on a lane the drill names it instead of running it. The restore found nothing left to remove.

That is the second half of the proof.

#### Do it: the chat, on every brain

`[PASS] health` shows the limits documind-chat publishes now: `limits=12 calls` again. Each brain answered the same question with citations, within its limits, and each brain's line prints what its turn cost. The outsider got 403 from the roster. `6 passed, 0 failed` closes the proof: the chat answers as it did before the drills.

### The detectors: what your lane shows now

Every detector on your lane, reading only, and how to read what they find.

#### Definition

`make gotcha-detect` runs every detector, or one with `ID=`. It only reads:

- Cloud Run: `gcloud run services describe` and `gcloud run revisions describe`.

- Cloud Logging: `gcloud logging read`, over the last 24 hours. `HOURS=` changes the window.

- Your checkout: `deploy/.candidate-revision` and `deploy/.previous-revision`.

- GitHub: for the production environment, one GET through gh, as `make ci-vars` makes it.

Each detector ends with `FOUND`, `nothing found`, or `nothing this checkout can tell`. A read that fails prints `STOPPED`, and the others still run. The command exits 1 when anything was found, and 2 when a read failed and nothing was found.

#### Do it: every detector

Read it in three groups.

- The lane as the drills left it. pinned-traffic lists documind-chat as following its latest revision. deploy-drops-hotfix finds nothing the next deploy would change on documind-chat: no cap left behind.

- What every lane shows. deploy-drops-hotfix is `FOUND` on documind-admin and documind-ui: both carry your `ADMIN_EMAILS`, and a `make deploy-services` without it would write the placeholder back. The admin console would then answer you `403 - Admins only`, and the UI would stop treating you as an admin, so pass `ADMIN_EMAILS` on every deploy. agent-spend-outside-the-month counts rupees on the chat rows, from the smoke's own turns, that no report of the month includes.

- What depends on your history. The release detectors read the revision files in your checkout. A checkout that never recorded a candidate cannot tell how the API's revision reached the traffic, and says so. With no `deploy/.previous-revision`, ci-promote-loses-previous is `FOUND`, because `make rollback` would refuse in this checkout. The log reads count only what happened in the window.

### The release no gate judged, loud against silent, and what the kit does not do yet

The hazard a routine deploy carries, the registry sorted the way the capstone asks, a gotcha with no detector, and the gaps.

#### The release no gate judged

This is the hazard in step 1's red box. `make up` runs `make deploy-services`, whose default `SCRIPTS` include `lesson-12.2.sh`, the API's deploy. After it the recipe moves documind-api's traffic to the revision it just made, by name (step 4). Lesson 11.2's gate runs on a candidate, and `make deploy-services` makes none.

- After a gated release and `make promote`, a routine deploy from a newer checkout moved documind-api to a revision no gate judged, carrying the new checkout's `GIT_SHA`.

- The detector named it: a serving revision that this checkout neither recorded as a candidate nor rolled back to.

- The same deploy without the API's script left documind-api on the gated revision.

The kit does not gate `make deploy-services` itself. To change the API, go through `make release-candidate`, `make eval-live API=` with the candidate's tag URL, and `make promote`. To deploy anything else, leave `lesson-12.2.sh` out of `SCRIPTS`.

#### Loud against silent: what pages, and what you watch instead

The capstone's failure-modes question, in lesson 11.8, asks for more than reproduced failures. It asks which of them your monitoring would catch, which it would not, and what you did about the second group. Here is that answer for the kit's own 13, read from the registry.

One gotcha has an alert policy, and it pages only once 12 deliveries have failed, about an hour after the upload. Its detector finds the same poison upload as soon as the worker refuses it.

#### Change it: a gotcha with no detector

Add an entry whose drill and check `commands/gotchas.py` does not run, and the registry refuses to load: `make gotchas`, every drill and every detector stop with exit 2 and name the problems. `commands/tests/test_gotchas.py` holds the same rule, in `test_a_detector_that_does_not_exist_is_refused`, one of its 50 tests. The kit's dry-run workflow runs that file on every push, so a pull request that adds such an entry goes red. The cell copies pinned-traffic as made-up-gotcha, runs the registry, and puts the file back.

The two problems are the two halves of an entry the code does not back: an offline drill nobody wrote, and a check nobody wrote. A detector that names an alert policy terraform does not declare, or a log event no service writes, fails the same way in the kit's tests (`kit_problems()`). `git checkout` put the file back, and the registry lists 13 again.

#### Why the registry looks like this

- Evidence, word for word. Each drill checks the kit lines it rests on before it runs. If the kit changes so that the drill stops reproducing its gotcha, the drill exits 1, and the tests stay red until the entry moves to fixed and names the test that proves the fix. The registry cannot go stale quietly.

- Offline first. The 9 offline drills cost nothing and need no lane, so the kit's tests run every one of them on every push. A lane is for the two drills only a lane can prove.

- A live drill puts the lane back. It refuses a chat whose traffic is held, refuses a deploy that would change anything else, and restores from a `finally` block. If even the restore fails, it prints the lines that finish it.

- Detectors only read. A check you run before every deploy has to be safe to run at any time.

#### What it costs

Each point is read from the kit, and the build asserts each one it can, so this box changes when the kit does.

- It does not gate `make deploy-services` or `make up`. The lever is how you deploy: `SCRIPTS` without `lesson-12.2.sh`. The cohort plan fixes the hazard after 6 December.

- No alert policy reads the chat rows. A turn stopped at a limit, a search the turn gave up on, and the agents' own spend show only to the detectors. No policy reads `vector_search_fallback` either.

- A routine deploy keeps no setting made by hand. A fork that needs one carries it in its deploy, reviewed like any change.

- Not yet run against a real lane, by the kit's own account: the live drills, the detectors' reads, and the field names in tag-audience-401's log filter. That GitHub creates an unprotected production environment the first time a job names it is unverified too. The author's run settles the first three.

- Not registered yet: gotchas that need kit work first. The plan lists them for after 6 December, among them ADK sessions held in one worker's memory, an interrupt dropped on a paused thread, a trace id Cloud Run may rewrite, A2A tasks held in one instance's memory, breakers and rate windows counted per worker, and a resumed node that reruns from its first line.

### Verify it yourself: the checklist

Ten checks, each in a step above, each with the value that proves it on your lane.

Here is what this lesson left on your lane:

- documind-chat has new revisions, the drills' and their restores'. It serves from the last one with the settings it had before: no `CHAT_MAX_MODEL_CALLS`, and its traffic on its latest revision.

- The chat's image was rebuilt from the same commit, and the routine deploy ran the rest of its script again: the invoker bindings, the checkpoint migration job, IAP on the service, and `make operators`' token grants for your address. Every routine deploy of the chat runs the same steps.

- `make smoke-chat` asked 4 questions in a session of its own: chat rows, rag-api's rows, the month's counter, and checkpoints.

- Nothing else moved. The drills deployed the chat alone, so documind-api never left its revision, and your clone's `ops/gotchas.json` is as it was.

Lesson 11.8 completes the independent capstone and hands the lane over, and its failure-modes question is the one this lesson's table answers.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.7 Reproduce the agent failures production shows and no eval row does · v5.0

Next: Lesson 11.8 Complete the independent capstone and operational handover.
