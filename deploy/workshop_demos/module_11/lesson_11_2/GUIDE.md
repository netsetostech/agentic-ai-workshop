# Lesson 11.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.2_Gated_Candidate_WIX.html`, reviewed at blob `213f9987f72054b35fe7a03511bfcd6540d6f02b`. Learners read that page on the course site; this guide keeps its prose.

Lesson 11.1's dispatch left a revision of `documind-api` that takes no traffic, and its live gate said green inside one GitHub run. Your lane does not remember that verdict, and `make promote` moves traffic to whichever revision a file names. This lesson ties the verdict to the revision. `make gate` judges exactly the revision `.candidate-revision` names, once the candidate tag routes to it and its tag URL answers as its own build, and writes a record: the revision, its image digest and `GIT_SHA`, the report's sha256, the verdict and the time. `make promote-gated` reads that record and stops any other revision, a red verdict, an edited report or an old record before `make promote` runs. You will name the candidate, see which token audience the API accepts, gate the candidate, read the record back against Cloud Run, and offer a record that names another revision.

- A verdict that names what it judged

- The words: candidate, tag URL, audience, digest, GIT_SHA, the gate, the report, the record, verdict, rules, stale, gate-check, promote-gated, GATE_FILE

- Before you run anything: set up the shell

- The candidate, as the console and lesson 11.1's run show it

- make gate and make promote-gated, line by line

- On your lane: the candidate named, the token's audience, and the gate

- The record read back against Cloud Run, and gate-check alone

- Change it: a record that names another revision

- What the record does not hold, and what it costs

- Verify it yourself: the checklist

You will learn how a gate's verdict is bound to the one revision it judged, and how `gate-check` stops every other revision before traffic moves. Then you will prove it on your lane: the candidate lesson 11.1 made, judged by `make gate`, its record checked against Cloud Run's own API, and a record that names another revision refused before `make promote` runs.

### A verdict that names what it judged

Why a green gate and a traffic flip need a record between them, what the record holds, and the order gate-check reads it in.

The gate judges a URL; the flip moves a name. The live gate asks the API every golden row and holds the answers to 9 thresholds and the required rows (lesson 4.2), on a candidate that takes no traffic (lesson 4.3 placed it there). What it sees is one URL. `make promote` then moves traffic to the revision `.candidate-revision` names. Before this lesson's two targets, nothing joined the two: `make eval-live` wrote no revision into its report, and `make promote` read no verdict. A red gate, a gate on another candidate and last week's gate all promoted the same way.

What can come between them. A second candidate made after the gate moves the `candidate` tag, and the tag URL then answers from a revision the gate never asked. An image-only update changes the image and leaves the old `GIT_SHA` on the revision, because settings carry over from one revision to the next, so `/version` names a build that is not running (the Makefile's comments call this F43). The lane's documents, rosters and model move over days, so an old green says little about today. The golden rows and the thresholds change, so a verdict can have been judged by rules this checkout no longer holds. And any file can be edited by hand.

The record is the join. `make gate` asks no row until the candidate tag routes to the revision the file names, the revision is Ready with an image digest and a `GIT_SHA` its image tag agrees with, and `/version` on the tag URL answers as that `GIT_SHA`. Then it asks every row and writes `evals/reports/gate.json`: the revision, its image and digest, its `GIT_SHA`, the report's path and sha256, the eval's exit code, the verdict and the scores, the sha256 of the four files the verdict was judged by, and the start and finish times. A red gate writes its record too, so a refusal can say why. `make promote-gated` runs `gate-check` on that record before `make promote`: the files first, and only when every file agrees, the lane.

A batch release certificate. In a pharmaceutical plant, quality assurance never approves "the tablets". It signs a release certificate for batch B-2311, with the laboratory's analysis of that batch attached and the edition of the pharmacopoeia its tests followed. The dispatch clerk loads a carton only when its batch number matches a signed certificate. A certificate for B-2310 releases nothing in B-2311. A failed assay releases nothing. An attached analysis that has been altered voids the certificate. A certificate signed under last year's pharmacopoeia, or long before dispatch, sends the batch back for retest. And the clerk reads the label on the carton itself, not only the paperwork. `make gate` is the signature on one revision, `gate.json` is the certificate, the report is the analysis, the rule files are the pharmacopoeia, and `gate-check` is the clerk at the loading bay.

#### Try it: would make promote-gated let this through?

The panel holds one gate record, the files of a checkout and the lane, as `gate-check` reads them. It starts on a green record of `documind-api-00042-xyz`, two hours old. Pick a case, or change any field: the panel prints what `gate-check` would print, marks each of its checks, and says whether `make promote` would run after it. The names, digests and hashes are the stand-in lane's from step 4.

changed since the gate:

Built when this page was built, from the kit you clone. The rules are `gate-check`'s own, `offline_reasons()` and then `live_reasons()` in `commands/release.py`, written again in JavaScript. Before this page was written, node ran the panel on the 12 cases above and on 355 states in all, and release.py's own `gate-check` ran on the same files against the kit test's stand-in lane: every exit code, every printed line, and whether the lane was read, agreed. The records, the report hashes and the digests are the ones the stand-in gate wrote.

Three things to try. Rename the record's revision to the serving one: it is refused from the files alone, and the lane is never read. Rename the record and `.candidate-revision` both: now the files agree, so `gate-check` reads the lane, and Cloud Run's own digest and `GIT_SHA` for that revision give the copy away. Then set the age to 23.9 hours, and to 24.1: the line at 24 hours is a bound the kit draws, not a promise that 23 hours is fresh.

It runs no gcloud and asks no row. Every case starts from a record the stand-in gate wrote, so it cannot show a record that is not JSON, one with a missing field, or one from another lane's checkout, which `gate-check` also refuses (step 4's table has them). A real revision never changes its image: "another image" stands for a record that was not written about this revision by this lane's `make gate`.

### The words: candidate, tag URL, audience, digest, GIT_SHA, the gate, the report, the record, verdict, rules, stale, gate-check, promote-gated, GATE_FILE

Fourteen rows, each with the value it takes on your lane.

One distinction to hold: `make gate` judges and records, and `gate-check` only reads. A green record moves nothing on its own. `make promote-gated` moves traffic, and lesson 11.3 runs it.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head. `make gate` mints a token as each, both for the API's canonical URL, and step 5 shows why the audience matters even when the tag URL is the one called.

The shell, in the kit's folder, with `NUMBER`, `REGION`, `API` and `tok` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line. On the lane: the candidate lesson 11.1's dispatch left, tagged `candidate` and taking no traffic. If you removed its tag, or never dispatched, the box in step 5 makes one from your shell. Step 3 reads lesson 11.1's run with `gh`. Step 5's gate asks the candidate every golden row: about ten minutes and about Rs 29. Nothing on this page moves traffic.

### The candidate, as the console and lesson 11.1's run show it

The revision with no traffic, its tag, its image and its GIT_SHA; then the lines of the dispatch that named it, checked it and gated it.

#### Definition

A revision is Cloud Run's unit of release. `documind-api` keeps every revision it has made, and its traffic table says which of them take requests: the serving one at 100%, and the candidate at 0% with the tag `candidate`, which gives it a URL of its own. Lesson 11.1's dispatch made the candidate as `sa-documind-cicd`. `make release-candidate` put the image `api:` and the commit on a new revision and set its `GIT_SHA` to the same commit, then `make record-candidate` wrote the revision's name to `.candidate-revision`, on GitHub's runner. The job checked that the tag URL answered as that commit and ran the live gate on it. When the gate was green, `promote` waited for its reviewer, and you said no.

#### Do it: the candidate in the console

Open Cloud Run in the console, then `documind-api`, then its Revisions tab. Two revisions matter here: the one serving 100% of traffic, and the newest, at 0% with the tag `candidate`. Select the candidate. Its container shows the image, `asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:` followed by a commit, and its variables include `GIT_SHA` with the same commit. The console shows what Cloud Run holds now. It cannot show that a gate ever judged this revision, because nothing on Cloud Run records that.

#### Do it: the dispatch's own lines

If your candidate came from lesson 11.1's dispatch, read what its `release-candidate` job printed. The cell finds the run and the job, then keeps the lines that name the revision, compare its `/version` with the commit, and give the live gate's verdict, each after the name of the step that printed it.

Three steps of one job held the whole binding. A candidate revision, no traffic recorded the revision's name, and the job handed that name to `promote` as an output. The candidate answers as the tag compared `/version`'s `git_sha` with the commit being released, before ten minutes of rows were spent. The live gate, on the candidate ran `make eval-live` on the tag URL, and only its green let `promote` start: CI gates by job dependency. None of it outlived the run. The name stayed in a job output and the verdict in a log, and no file anywhere holds the digest the gate judged or a hash of its answers. Your checkout knows none of it. Step 5 judges the same revision from your shell and keeps the record.

### make gate and make promote-gated, line by line

The two targets, the checks before any row is asked, the record, and gate-check's files-then-lane order; then the kit's own tests, and every refusal as release.py prints it.

#### Definition

Both targets are in `mk/release.mk`, and each is a subcommand of `commands/release.py`, standard library only, which runs the same without make. `gate` writes nothing to Google Cloud. It reads the service and the revision, mints two tokens, calls `/version` once, and hands the rows to `evals/run_eval.py`, as `make eval-live` does, with a report path that names the revision. `promote-gated` is two recipe lines: `gate-check`, then the same `make promote` as before. make runs a target's lines in order and stops at the first that fails, so a refusal means `make promote` never starts. Plain `make promote` is unchanged and reads no record, so the candidates of Modules 4 to 12 can still be promoted by hand.

#### The code

The constants say what the gate binds: the service, the two accounts whose tokens it mints, the record's format, the rule files, 24 hours, five minutes of clock skew, and what a revision's name and a digest look like.

#### Before any row: the revision, its facts, its build

`revision_facts()` reads one revision with `gcloud run revisions describe`: the service it belongs to, the digest Cloud Run resolved its image to when it made the revision, its `GIT_SHA`, and whether it is Ready. The revision names its image by that digest only. The tag the deploy gave, `api:COMMIT`, stays in the service's `spec.template`, and the template made one revision: the newest, `status.latestCreatedRevisionName`. So `deployed_image()` reads the tag from the template while the candidate is that revision, and reads nothing once a later update has made another. `unjudgeable()` turns those facts into refusals. The last two are about F43. When the tag and `GIT_SHA` disagree, the revision is not the build its `/version` claims to be. When the tag cannot be read, the gate cannot tell, so it refuses as well.

`cmd_gate()`'s first half is all refusals. One describe of the service gives it the traffic table and the template. It stops if the candidate tag routes to any revision but the one the file names, because the tag URL would then answer from a revision `make promote` would not move traffic to. It mints the member's token for the service's canonical URL, the one audience the API accepts (step 5), and stops if the tag URL answers as another `GIT_SHA`. Every check runs before the first of 65 answers is paid for.

#### The rows, then the record

From here an earlier verdict must not stand for this gate's, so the old record and this revision's old report are deleted before the first row is asked. `live_gate()` runs `run_eval.py` against the tag URL with both tokens, its output streaming to your terminal. Afterwards the gate reads the tag again: if it moved while the rows were asked, the answers may have come from two revisions, and no record is written. Otherwise the verdict is `pass` only if `run_eval.py` exited 0 and nothing in its report blocks, which `report_blocked()` reads by `run_eval.py`'s own rules. The record is written beside itself and renamed into place, so it is whole or absent.

#### gate-check: the files first, then the lane

`offline_reasons()` reads only files: the record, `.candidate-revision`, the report and the four rule files. It collects every reason it finds instead of stopping at the first, so one refusal can name three problems. Only when the files agree does `live_reasons()` read the lane, with the same two describe calls the gate made: the tag, then the revision's digest, `GIT_SHA` and readiness against the record's.

#### Do it: the kit's own tests

`commands/tests/test_release_gate.py` plays every case on this page against a stand-in `gcloud` that keeps one lane's traffic table and revisions in a file. Where a POSIX `sh` is installed, as in Cloud Shell, it also runs the recipes of `record-candidate`, `promote-gated`, `promote` and `rollback` as make hands them to the shell, and shows that only the gated revision is promoted. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a minute or two.

#### Read it: a gate on the stand-in lane

The same stand-in, driven from this page's build: `release.py gate` on `documind-api-00042-xyz`, with a stand-in for `run_eval.py` that writes the report a green run writes. The candidate's `GIT_SHA` is `COMMIT`, the serving revision's `PREVIOUS`, a newer candidate's `NEWER`.

The record it wrote, whole:

A red gate writes a record too, and says what blocked it:

And `gate-check` on the green record, two hours after the gate:

#### Every refusal, as release.py prints it

`make gate` stops with exit 2. Before any row is asked, the stop leaves an earlier record as it was. Once the rows have started, the earlier record is already gone, and the stopped gate writes none. The two `ERROR` lines inside the messages are the stand-in gcloud's words; your gcloud's may read differently.

`gate-check` exits 1 on any reason, and prints every one under the same first line, `REFUSED: the gate record evals/reports/gate.json does not let make promote move traffic:`.

Every line in both tables came from `commands/release.py` itself, run on this page's build against the kit test's stand-in lane: nothing is paraphrased. Two things to notice. The gate refuses before it spends anything: the tag, the revision's facts, its build and both tokens are checked before the first answer is paid for. And `gate-check` never reads the lane while a file disagrees, so a stale, red or renamed record is refused even with no network at all. Only the refusals marked as reading the lane needed Cloud Run, and each of them is something no file in your checkout could show.

### On your lane: the candidate named, the token's audience, and the gate

The candidate's name brought into this checkout, two tokens against the tag URL, then make gate on the candidate lesson 11.1 made.

#### Definition

Three facts about your lane decide whether the gate can run. First, `.candidate-revision` must name the candidate. On the dispatch path the name stayed in a job output, so `make record-candidate` reads the revision Cloud Run made last and writes it here, and the gate's first check refuses if the tag routes anywhere else. Second, the tag URL must answer as the candidate's build. Third, every token must be minted for the service's canonical URL, `https://documind-api-NUMBER.asia-south1.run.app`, whichever URL is called. The API compares a bearer token's audience with its own `SELF_URL` on every route that answers a question, through `verify_iap`, and a token minted for the tag URL fails that check: the first gates on candidates met it as 401 on every row (F42). `/version` runs no check of its own, so whatever it answers to such a token is Cloud Run's front door alone, and the cell below shows what yours does.

#### The code

The gate's `/version` call asks twice, because a revision with no traffic has scaled to zero and its first request waits for an instance. A 401 there names F42, and a token taken from the environment is used as it is.

#### Do it: name the candidate

`make record-candidate` is the line `make release-candidate` ends with, run on its own. The cell then prints the traffic table and whether the file and the tag name one revision.

#### Do it: the tag URL and the audience

The cell mints two tokens as `documind-ui-sa`, one for the canonical URL and one for the tag URL, and calls the tag URL twice with each: `/version`, which checks no token itself, and `/v1/sources` for acme, which goes through `verify_iap` and acme's roster but calls no model.

The canonical URL's token works on both routes: `/version` answers as the candidate's commit, with the model and prompt version it runs, and acme's sources come back because `documind-ui-sa` is on acme's roster. The tag URL's token is refused on `/v1/sources`. A 401 whose body says `invalid bearer token` is the API's own check against `SELF_URL`; an HTML page instead would be Cloud Run's front door refusing first. The same token's line on `/version` is the front door's answer and nothing else. That is why the gate mints both of its tokens for the canonical URL, and why a `/version` check alone could not prove a token is right.

#### Do it: the gate

About ten minutes: every golden row as the member, then the isolation rows again as the outsider. `run_eval.py`'s own lines stream between the gate's two blocks; lesson 4.3 reads them.

`the candidate tag is on ..., but .candidate-revision names ...`: a revision was made after the dispatch's, so the file and the tag disagree. Make one candidate from the commit you mean to release: `make release-candidate PROJECT="$PROJECT" REGION="$REGION" GIT_SHA=COMMIT`, with the full commit step 3's lines show, puts the image the dispatch built on a new revision, moves the tag to it and records it; then run the gate again. `the candidate tag is on no revision`: the tag was removed, and the same line puts it back on a new revision. If you never dispatched, lesson 11.1's local path builds the image first. `could not mint a token`: your account lacks the token-creator role on the two accounts, which `make operators` grants. `answered HTTP 401`: a `DOCUMIND_ID_TOKEN` exported by an earlier lesson is being used as it is; `unset DOCUMIND_ID_TOKEN DOCUMIND_OUTSIDER_TOKEN` and run the gate again. `Cannot find service [documind-api] in region [us-central1]`: `REGION` is not set in this shell, so the Makefile's default stood; run the setup block.

The gate judged one revision by name, and the record now says which: the revision, the digest Cloud Run resolved its image to, the `GIT_SHA` its `/version` answered with, the sha256 of the report its rows went into, the verdict and the time. The CI gate in step 3 asked the same rows of the same revision; this one keeps what it found. If your gate was red, the record says so and what blocked it, and `make promote-gated` will refuse it until a candidate is gated green.

### The record read back against Cloud Run, and gate-check alone

Cloud Run's own API for the revision and the service, the report's sha256 computed again, then gate-check with nothing after it.

#### Definition

`gate-check` trusts nothing it can read again, and neither should you. The record says what the gate saw. The first cell reads the same facts again without `release.py`: the revision and the service from the Cloud Run Admin API's v1 resources, the same JSON `gcloud run ... describe --format=json` prints, and the sha256 of the report and of each rule file from your disk. Then `gate-check` runs alone: the first recipe line of `make promote-gated` without the second, so nothing moves.

#### Do it: the record against the lane

#### Do it: gate-check, and nothing after it

Every value the record holds is still true of the lane: the file and the tag name the revision, Cloud Run reports the digest and `GIT_SHA` the gate recorded, the report hashes to the record's sha256, and the rule files are the ones the verdict was judged by. `gate-check` exited 0, so `make promote-gated` would move traffic now. It goes on saying so for 24 hours from the gate's finish, while no rule file changes and no newer candidate takes the tag. Lesson 11.3 runs it.

### Change it: a record that names another revision

A copy of your record with one field changed, offered to make promote-gated through GATE_FILE.

The cell copies your record to `evals/reports/scratch-gate.json` with one field changed: the revision, set to the one serving now. It offers the copy to `make promote-gated` through `GATE_FILE`, deletes it, and runs `gate-check` on your own record, which it never touched. The copy is green, fresh, judged by today's rules, and its report still hashes to its sha256: everything in it is true except the name.

`gate-check` refused the copy from the files alone: it names the serving revision, and `make promote` would move traffic to the candidate. make stopped at that recipe line, line 46 of `mk/release.mk`, printed its own error line and exited 2, so `make promote` never ran and no traffic moved. Your own record still passes. The panel in step 1 shows the next forgery: rename `.candidate-revision` as well, the files agree, and the lane gives it away.

### What the record does not hold, and what it costs

CI's gate, the two targets that release with no gate at all, the path never to dispatch, and the rupees.

#### CI gates by job dependency, and writes no record

In `documind-cd.yml` the live gate is a step of `release-candidate`, and `promote` needs that job, so a red gate means `promote` never starts. The revision's name travels as a job output; `promote` writes it to `.candidate-revision` on its own runner, waits for the `production` environment's reviewer, and runs plain `make promote`. That binds the name for the length of one run, with a person in between. It keeps no digest, no report and no time, and the runners' files are gone when the run ends. A record from `make gate` stays in your checkout, and CI never reads it.

#### make up and make deploy-services release the API with no gate

`make deploy-services` ends by moving all of `documind-api`'s traffic to the revision its own deploy just made: no candidate, no tag, no gate. `make up` runs `deploy-services` among its steps. Both build and repair a lane, and neither is a release. After either one, the API serves a revision no gate judged, and nothing in either target reads your gate record or removes it: it still names the candidate.

`documind-cd.yml`'s other path rolls a Cloud Deploy release of `run-service.yaml` out over `documind-api`, with settings that are not your lane's (lesson 11.1 reads them). It would break the API, and no gate record would mean anything afterwards. Dispatch with `-f path=candidate` only; the comment above `make gate` in `mk/release.mk`, quoted in step 4, says the same.

#### What else a green record cannot promise

- A make target is not a lock. `make promote-gated` is a rule your checkout keeps. Plain `make promote`, a `gcloud run services update-traffic` typed by hand, or anyone holding `roles/run.developer` on the project moves traffic without reading any record.

- The window is a bound. 24 hours is how long the kit lets a verdict stand. Documents can be reindexed and rosters changed inside it, and the record sees neither.

- It holds what the rows asked. 65 questions through `/v1/query`, as two identities. The gaps lesson 4.3 found, the stream's refusals among them, are still gaps.

- One record at a time. The next `make gate` replaces `gate.json`, whichever revision it judges; only the reports keep their revisions' names.

#### What it costs

Lesson 11.1's dispatch already paid for one gate on this candidate, in CI. `make gate` asks the same rows again because the CI gate kept nothing your checkout can read: judging one revision twice costs twice.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

In this checkout: `.candidate-revision` names the candidate; `evals/reports/gate-documind-api-....json` holds its rows' verdicts and `evals/reports/gate.json` the record, both ignored by git; the copy from step 7 is gone. In the cloud nothing moved: the candidate still takes 0% under its tag, and the serving revision 100%. The gate's answers left their usage rows under the candidate's revision, as lesson 4.3 showed, and the outsider's requests were refused at the roster. The record holds for 24 hours from the gate's finish. Lesson 11.3's gated promote reads it, so take that step within the window, or run `make gate` again first. Put acme's pin back now, with the setup section's pin-back window.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.2 Evaluate and gate the exact candidate revision · v5.0

Next: Lesson 11.3 Promote, roll back and repair a controlled failure.
