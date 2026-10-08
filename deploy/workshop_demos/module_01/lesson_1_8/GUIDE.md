# Lesson 1.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.8_Restore_Reconcile_WIX.html`, reviewed at blob `8889e75f35fcc52db957363e2e142eb5b523f6d8`. Learners read that page on the course site; this guide keeps its prose.

Start with a document that answers a question. Delete its cloud file and show why the index can still answer. Preview the reconciliation plan, apply retirement, and prove that storage and the index agree again. Then upload the exact original bytes and watch the worker reuse the existing embeddings. A fresh fixture, exact source checks and a clean baseline make each change visible.

- The demonstration: create a gap, repair it, restore the document

- How reconciliation decides: flow diagrams and the queued claim

- Set up the operator shell

- Prepare: credentials, backend and a clean baseline

- Create this chapter's note and the checks

- Prove the document works

- Delete the cloud file and show the stale index

- Plan retirement, apply it, then prove zero drift

- Restore the exact bytes and prove reuse

- Optional: watch an incomplete undo refuse

- The nightly job and older records

- The separate module smoke test

- Verify the story and restore the original backend

Prove one document's deletion, retirement and restoration before studying the exceptions. Then trace each reconciliation action to its real bucket, ledger and claim evidence.

### Create a gap, repair it, restore the document

Storage, the source ledger and a cited answer are three observations. Watch them agree, disagree, and agree again.

The ingestion worker handles upload events. Deleting an object sends no deletion event this worker acts on, so a file can disappear while its indexed rows remain current. Reconciliation compares live bucket objects with the source ledger and the per-version claims, names the differences, and repairs them only when the operator applies the plan. It never parses or embeds content itself: a reingest rewrites the object onto itself, creating a new finalize event for the existing worker.

The warehouse stock-take. A delivery is booked when it arrives. If an item leaves through a side door, the ledger still lists it. A stock-take spots the difference and corrects the record. If the same item comes back, its earlier record can be reactivated after checking that the retained pieces are complete.

N is the chunk count observed on your fixture, not a hardcoded three. Reuse depends on the retained rows still being complete and inside the undo window.

Zero drift does not mean every document is present. A deleted file and a retired source agree with one another. Reconciliation can already be clean before restoration. The apply's summary describes the differences it found at the start; a new plan proves what remains afterward.

### How reconciliation decides

First compare the live object and ledger. Only then, if required, inspect the bytes.

An object generation identifies an upload; uploading the same bytes creates a new generation. A hash identifies those bytes. A claim is the worker's per-version record in `documents/{tenant}_{sha256}`, with a status such as indexed, superseded or queued. The source ledger is a separate record in `sources/`, keyed by object name.

Amber actions contribute to drift. Green outcomes do not. These flows cover document objects; the planner skips its configured sidecar suffixes. A queued match uses the same object name and generation, with a compatibility path for legacy claims that have no generation.

`drift = retire + reingest + backfill`. These are counts of planned differences. A `touch` updates bookkeeping, and `queued` is work already assigned elsewhere.

#### How do we know a PDF is queued?

The worker writes `status: queued`, the object's `gcs_uri` and its `generation` into the version claim when handing the document to the batch lane. Reconciliation first matches the live file's name and generation to a queued claim. Legacy claims without a generation are also accepted. If the byte-check path is reached, a queued claim for the same tenant and hash produces the same decision. The filename, PDF size and an absent ledger row are not proof of queued status.

In that example the first PDF contributes one unit of drift. The bundle contributes none. Queued means handed to batch processing; it can remain queued if no batch job has run. Use `make queued PROJECT=$PROJECT` to inspect the pending work before deciding how to operate the batch lane.

#### The planner's rules, verbatim

#### Explore a different bucket and ledger

This simulator follows plan() and decide_bytes(). It changes no cloud resources. A queue selection represents a matching claim; an unrelated upload generation must be assessed separately.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Keep the backend change with the demo

Step 3 saves the existing tenant pin before selecting vector. Step 12 restores that saved value. Run them at their own checkpoints; copying a setup and restoration command together immediately undoes the lesson setting.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; the exact-source checks below use the operator token's tenant access.

### Credentials, backend and a clean baseline

Do this before presenting. Stop at an error; do not paste the next stage until its checkpoint passes.

Use the same operator shell and virtual environment throughout. Create a chapter directory before changing the backend, save its original pin, and run the offline planner check. These files are local demo state; keep them out of commits.

The baseline must have no pending retire, reingest, backfill or touch actions. Queued and withdrawn entries may remain; neither is drift. If an unrelated PDF is missing from the ledger, handle it in preparation: inspect the plan, apply only a plan you intend to execute, wait for ingestion and plan again. `APPLY=1` operates across acme, not only this chapter's note. Do not hide a failed managed-mirror operation by disabling the mirror midway through the demonstration.

A Firestore `ACCESS_TOKEN_SCOPE_INSUFFICIENT` means the token used by Python lacks the required scope. Renew the intended Application Default Credentials in this workstation, and check whether `GOOGLE_APPLICATION_CREDENTIALS` is selecting a different credential file. A successful gcloud command alone does not prove Python's ADC works.

### Create this chapter's note and the checks

A fresh name, a new fact and an unchanged local copy remove the dependencies on earlier lessons.

This chapter does not use `~/lesson34_note.md` or the smoke-lantern question. Another smoke note may still answer that question even after one copy is retired. Our primary checks are the exact source name, its object generation and its citation; a bare `answerable True` is insufficient.

#### Load the checks once

The helper block is preparation, not a slide to type live. It stops on failed uploads, polls the exact source and generation, checks citations, and refuses to apply an unexplained tenant-wide plan. The log filter includes both the version key and generation, so another acme upload cannot satisfy the wait. To resume after reopening a shell, first run the shared shell setup, then source this directory's `session.env` and `helpers.sh`; do not create a new note midway through a restore.

The generated local directory contains the query, checksum, original pin and latest responses. If a command fails, inspect its message and the saved response. An upload failure must end that stage; there is no ingestion event to wait for.

### Prove the document works

Show the source ledger in the UI and the same source's evidence from the API.

On the Documents page, use Refresh indexing status and find the exact `lesson44_.md` row. The first upload may need time for the worker and retrieval tier to catch up. The pin is cached for about a minute; the answer's stages prove which backend actually served it.

Checkpoint: source indexed at this upload's generation, a cited answer naming locker Q7 in Jaipur, and no pending repair. If the source is indexed but the query has not caught up, repeat `ch44_ask present` and inspect its evidence; do not upload again merely to wait.

Storage, the source ledger and this cited answer agree. N is the count this worker produced; later we will prove that the same N chunks return without new embeddings.

### Delete the cloud file and show the stale index

The local original stays safe. Delete only this demonstration's live object.

Checkpoint: before a reconciliation run, the ledger can still say indexed and the answer can still cite the fixture. If a scheduled reconciliation already retired it, say that automation closed the gap first; inspect the source and plan rather than claiming the stale state was observed. The bucket's retained version is not a live object in the walk's listing.

The cloud file is gone, but this worker has not processed a deletion. Its current rows are still searchable. This is the difference the reconciliation plan will name.

### Plan retirement, apply it, then prove zero drift

Keep preview, mutation and verification as three visible operations.

The action must be `retire` for `$SOURCE`, with reason gone from the bucket, `applied: false` and drift 1. A plan is evidence, not a repair. Pause other uploads during the demonstration; the kit's apply does not execute a saved, source-scoped plan.

#### The code that applies the plan

Checkpoint: the exact source is retired, the answer no longer cites it once retrieval reflects the change, and a new plan is clean. A refusal is the intended result for the unique question. If another source answers, inspect the citation; do not call that a failed retirement. The displayed reused and embedded counts on a retired ledger row describe its last ingestion, not a new restore.

The apply reported the difference it found, so its own drift may still be 1. The following plan is 0: storage and the index now agree that this document is absent. Restoration is a separate action.

### Restore the exact bytes and prove reuse

A new upload generation, the same content hash, and the worker's verified reactivation.

The checksum must still match. Changing the memo, adding today's date, or replacing it with a base smoke fixture creates different bytes and does not demonstrate the same-version undo. Keep the same object name too.

Checkpoint: the worker reports `ingest_reactivated` for this version and upload generation, the source reads indexed with reused N and embedded 0, the answer again cites the exact fixture, and the plan is clean. If logs arrive later than the ledger, repeat the log read. A fresh `ingest_ok` may restore the document successfully but does not prove reuse; inspect whether retained rows were missing or the undo window closed.

#### Why the undo counts first

The original bytes returned under the original name. The worker checked that all retained chunks were still available and eligible, then reactivated them. We proved the new generation, the reuse counts and the cited source together.

You have shown a working document, a stale index, a planned repair, consistent absence, and a verified return. Steps 9 to 11 are separate extensions. Finish with step 12 even if you skip them: it restores the backend pin saved before the demonstration.

Load this run's saved session variables first. Recover the exact generation named in its source ledger, then verify the content hash before writing the local file. Do not invent replacement text and expect a same-version reactivation. If the recorded generation is no longer retained, stop and inspect version recovery options; this path cannot reconstruct deleted bytes.

After recovery, run `ch44_upload` and the checks from step 8. If the checksum file or the rest of the saved session is missing too, reconstruct and review that state before continuing.

### Watch an incomplete undo refuse

Run this only after the successful round trip. It deliberately removes one retired row from this chapter's fixture.

The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits `reactivate_incomplete`, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents.

Checkpoint: a `reactivate_incomplete` event explains the shortfall, followed by fresh `ingest_ok`; the restored source and answer are valid again. The reused-N/embedded-0 checkpoint belongs to the successful undo in step 8, not this fault. The strict generation filter may exclude `reactivate_incomplete` because that event is emitted by the lower-level undo function; use the read below to see it for this version and time window.

### The nightly job, the number it ends on, and the lane older than the ledger

The job that runs the walk at 23:30, the metric and the pager that read its last line, and the one-time repair for a lane that predates the ledger.

#### Definition

The walk is a Cloud Run job on the ingest image, `documind-reconcile`, declared when `RECONCILE_JOB=true` is on the Terraform apply and scheduled at 23:30 IST, after the night switch has floored the lane, with the worker's own environment and no platform retries. Its last line, `reconcile_done`, carries the drift; a log-based metric extracts that field, and an alert policy pages when the metric stays above zero for twenty-four hours, which is two nightly runs: one night of drift is a lost event the walk repaired, two is a lane nobody is reconciling. `make backfill-current` is the other one-time tool: on a lane whose rows were written before the ledger existed, it gives every row a `current` flag and a version key and every indexed claim a ledger row; inspect its plan before deciding whether an older lane needs repair.

#### The code

#### Read the deployed job and backfill plan

On a lane deployed with the defaults the job is not declared, so the walk is something you run; the page you are on has been that operator. Declaring it is one Terraform plan with the switch on, through `make plan`'s guard, and its apply; keep `RECONCILE_JOB=true` on every later plan, or the guard refuses the plan that would delete the job. From then the same script runs every night as the worker's account and the pager reads its last line. Read the actual backfill counts rather than assuming zero: `chunks 0` means no chunk flag needs that repair; the sources count describes the indexed claims the operation would record.

### Run the broader module validation separately

The reindex smoke tests a different fixture and a wider lifecycle; it is not the proof of this chapter's deletion repair.

`make smoke-reindex` uploads the kit's version 1 and version 2 under its own name, checks carry-over and reactivation, and asks the smoke-lantern question. Existing copies of that fact can affect the answer checks. Rehearse this separately, inspect its citations and fixture state, and report its actual pass/fail result. Do not replace the exact source and generation checks above with a green answer from this other note.

The smoke leaves its own fixture indexed. That does not demonstrate that `$SOURCE` was retired or restored. Count embedding work from the worker's actual events; a refused undo can require fresh embeddings, while a successful reactivation reuses retained vectors.

Two causes, told apart by one log read. A kit older than 23 September 2026 waits for a worker line carrying `jsonPayload.tenant`, and the line the worker writes for the unchanged fixture bytes, `ingest_duplicate`, carries only the document key, so the smoke waits its five minutes for a match that cannot come. The setup block pulls the latest kit every session; on a clone, one pull is the fix, after putting back any copy of the smoke file made by hand, and the count on the second line must be at least 1 afterwards. If the read shows nothing at all, the event never reached the worker, and the push subscription's endpoint is the place to look: it must be the worker's URL.

The check wants the answer to say bay 7 and not bay 4. Lesson 1.4's note, `acme/smoke_note_v1.md`, which step 5 restored, carries the same clause with bay 4 and no date, so with it current the model reads two sources that disagree; rule six tells it to follow the dated one and say from when it applies, and an answer that mentions the old bay fails the check although it is right. Withdraw the note for the smoke and restore it after: both are the kit's own targets from lesson 1.7, and the restore embeds nothing.

### Verify the story and restore the original backend

Use the state transition and the exact evidence, then return the tenant to its saved configuration.

Before reporting the chapter complete, check the final source and plan. If the optional incomplete-undo variation was run, record its fresh ingestion separately from the successful reuse in step 8. Leave the verified fixture and local original available for the audience to inspect.

One fresh chapter fixture was indexed, deleted, retired by reconciliation and restored from verified original bytes. Its new generation and exact citation proved the return. The original tenant backend was restored from the saved value, and unrelated batch work stayed separate. Module 2, Retrieval, starts with lesson 2.1: Apply query embeddings and authorized filters.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.8 Restore documents and reconcile index differences · v5.0

Next: Lesson 2.1 Apply query embeddings and authorized filters.
