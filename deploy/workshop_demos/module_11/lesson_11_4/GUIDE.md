# Lesson 11.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.4_Debug_Wrong_Answer_WIX.html`, reviewed at blob `7449ad397b6297eacbbdc4e2f9efd8e24b0f6a5d`. Learners read that page on the course site; this guide keeps its prose.

An acme employee asks for the E3 notice period and DocuMind says 90 days, where the golden set says 60. Something between the question and the answer made that happen, and guessing where is slow. Every DocuMind answer carries a trail. It says whether the answer cache served it, which store retrieved it and whether a fallback rung stood in, how many chunks the reranker saw and who ordered them, and which version of which document each citation came from. The log's fallback events and the ledger's versions sit beside it. In this lesson you break one answer on purpose, then trace it using only the marks the answer and the lane recorded. You rule out each stage in the order the answer was made, name the cause, and put the lane back.

- An answer leaves a trail

- The words: trail, stages, rung, pool, version, ledger, probe

- Before you run anything: set up the shell

- The trail, as the kit writes it down

- A right answer, and its trail

- Break it: a version reaches the lane

- Trace it, name the cause, put it back

- Why the trail looks like this, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn to read an answer's trail in the order the answer was made. From the marks alone, you will tell a wrong version, a fallback rung and a pool too small apart. Then you will prove it: you make a wrong answer on your own lane, and a cell traces it to its cause without being told what you changed.

### An answer leaves a trail

Five stages make an answer, and each leaves a mark you can read afterwards.

An answer is made in five stages, in order.

- The answer cache. With `SEMANTIC_CACHE=on`, a question asked before, under the same corpus, is answered from the stored reply, and nothing else runs.

- The store. The tenant's pin, or else the deployment's default, names one. When it fails, a fallback rung stands in: for the index, Firestore's own vector search;

- for a managed store, the kit's index, when the tenant's data may not leave India.

- The pool. These are the candidates retrieval hands on. There are `TOP_K_RETRIEVE` of them: 20, unless a revision sets another number.

- The reranker. The Ranking API puts the pool in order. When it does not answer in time, retrieval's own score orders it.

- The model. It writes from the chunks that fit the prompt, and cites them.

Underneath all five is the version: the bytes of the document the chunks were cut from.

Each stage leaves a mark.

- The cache writes `cache_hit` on the answer.

- The store and its rungs write three fields in `stages`. `retrieval_backend` says which store was chosen. `vector_chunks` says how many chunks the index itself returned. `policy_fallback` is 1 when the tenant's data region overruled the choice. When the index fails, the log records `vector_search_fallback` with the error.

- The pool is `stages.pool`.

- The reranker writes `stages.rerank_fallback`, and the log records `rerank_fallback`.

- The version is inside every citation's `chunk_id`, `acme:#`. The ledger says which version is current.

- The model leaves `answerable` and the citations. Whether the answer follows them is `make judge`'s question.

Read the marks in the order the answer was made, and stop at the first one that is off. A mark after a broken one proves little. If the Firestore rung returned a pool of ten, that explains a missing clause better than anything the reranker did.

Three causes this course has built each leave their own marks:

- A version. The answer cites the version the ledger holds, but the ledger holds something other than what you meant.

- A fallback rung. `vector_chunks` is 0 under `vector`, `rerank_fallback` or `policy_fallback` is 1, or there is an event in the log.

- A pool too small. The pool holds fewer than the 20 the ablation decided.

A degraded pipeline often answers right. That is what the rungs are for. In the panel below, 5 of the 7 cases still answer right, and all but the first still move a mark. So read the marks, not only the answer: they show a degraded lane before its answers go wrong.

A path lab's report. A doctor does not believe a haemoglobin value on a report. The lab does not repeat the test blind. The report already says:

- which analyser ran the sample, the main one or the backup;

- how much sample there was;

- the reagent lot and its date;

- whether the value was copied from last week's report;

- who signed it.

The lab reads these in the order the sample moved, and stops at the first one that is wrong. The backup analyser often gives the right value, which is exactly why the report says it was used. Those are DocuMind's fallback rung, pool, version, answer cache and judge.

#### Break one thing, read the trail

Choose a break. The panel shows:

- the answer, and whether golden row lk-06 would pass it;

- the trail on the answer, and the log's events;

- the six links, read in order;

- what the trace names as the cause.

The 7 answers come from the kit's own `query()` in `rag-api/main.py`, run at build time on a stand-in lane. The lane holds the handbook's two versions, cut by the kit's chunker and labelled as lesson 10.4's relabel leaves them: version 1 `policy`, revision 2 `unknown`. The filter case asks for `form`, which rag-api accepts and no row holds on any tenant. It is not one of the registry's seven classes, because each of those is held on acme. The index, Firestore, the Ranking API and Gemini are stood in; the model is a reader that answers from the packed clause. The six links are step 6's trace cell, run on each answer.

It shows the kit's rules on a stand-in lane that holds one document. On your lane the index, the reranker and the model are real, acme holds many documents, and the numbers differ. For example, the Firestore rung's pool here is 10 of 20, because the handbook's retired version sits beside its current one. On your lane it depends on how many retired rows lie near the question.

### The words: trail, stages, rung, pool, version, ledger, probe

Ten rows, each with the value it takes on your lane.

One distinction to hold: a clean trail with a wrong answer points at the corpus, and a degraded trail with a right answer is luck the next question may not have.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `ME` set, and the operator venv from Modules 1 and 2.

- `check-firestore-fallback.py` imports the API's own modules, so it needs that venv.

- `verify-vector-index.py` reads Terraform's state. Run it in the checkout where `make up` ran; anywhere else it stops at `terraform output`.

Step 5 changes acme's handbook for everyone on your lane. It stays changed for the few minutes until step 6 restores it.

### The trail, as the kit writes it down

What the answer carries, what the log records, and which line writes each.

#### Definition

The cell reads rag-api's source and prints the map you will trace with:

- the fields every answer carries beyond the contract;

- the keys of `stages`;

- the values of `found_by`;

- the fields of `GET /version`;

- every event a degraded answer leaves in the log, with its file and line.

Nothing is called. The map is read from the kit, so it changes when the kit does.

#### The code

#### Do it

The map has 10 keys in `stages`, 5 values of `found_by`, and 9 kinds of event on 11 lines.

- Three keys name the store. `retrieval_backend` is the store chosen. `vector_chunks` is how many chunks the index itself returned. `policy_fallback` says whether the tenant's data region overruled the choice.

- Two keys cover the rest of retrieval. `pool` is what the reranker saw. `rerank_fallback` appears only when the Ranking API did not answer.

- The version is not in `stages`. It is in every citation's `chunk_id`, and `prefer_current()` guarantees it is a version the ledger calls current.

### A right answer, and its trail

The question the golden set asks twice, answered by the live revision, and every mark on the answer.

#### Definition

`ask131` asks acme's E3 notice-period question as `documind-ui-sa`. It is the question golden rows lk-06 and vr-01 ask. The whole answer is kept in `~/ask131-LABEL.json`, and the cell prints:

- the answer;

- each citation, with the version its chunk id carries;

- the trail: `cache_hit`, the backend that answered, and the five `stages` fields that cover the store, the pool and the reranker.

#### Do it

Sixty days, as the golden set says, and a clean trail:

- the answer cache did not serve it;

- the index returned all 20 of the pool. acme is pinned to `vector`, so `vector_chunks` equal to `pool` means the index answered, not the Firestore rung;

- the Ranking API put the pool in order.

The citation's version, `497809ffbaa6`, is the first twelve characters of the SHA-256 of `evals/corpus/acme/hr_policy_2026.md` in your checkout. Keep `~/ask131-before.json`: it is the trail to compare against.

### Break it: a version reaches the lane

The kit's own re-issue of the handbook, then the same question.

#### Definition

`make reindex` re-issues one document under an object name. Here it uploads the kit's `evals/demo/hr_policy_2026_v2.md` as `acme/hr_policy_2026.md`. That is revision 2: it declares `Effective from: 2026-10-01` and changes clause NP-03 to 90 days. This is the kit's own demo re-issue, which lesson 1.3 also ran. The script first checks that the golden set is sound, then waits for the worker's line.

- If your lane re-issued revision 2 in the last 30 days, its rows are still kept. The worker reactivates them without embedding anything: `ingest_reactivated`, embedded 0.

- Otherwise it ingests revision 2 afresh: `ingest_ok`, with 281 vectors reused by hash and 2 embedded.

Either way, the ledger's current version of the handbook becomes revision 2. The cell's first line notes the time, which the trace needs.

#### Do it

This is the symptom: 90 days, from 1 October 2026. Compare it with `~/ask131-before.json` and almost nothing moved: the same store, all 20 from the index, the same reranker, the same clause (`chunk 1`, NP-03). Only the version in the chunk id changed, to `5560308823a6`.

From here, pretend you did not make this change. A user has reported 90 days, and step 6 finds out why from the marks alone.

### Trace it, name the cause, put it back

Six links in order, the ledger and the two probes, then version 1 again.

#### Definition

The trace cell knows only the reported answer, `~/ask131-after.json`, and what the lane records. It reads:

- `/version`;

- the revision's `TOP_K_RETRIEVE`, from Cloud Run;

- documind-api's fallback events since the break.

For the first citation it reads four more things:

- the chunk's own row in Firestore;

- the ledger's row for its source, from `GET /v1/sources` (the rows `make sources` prints);

- the bucket's generation of the object;

- the SHA-256 of the same file in your checkout's `evals/corpus/`: the bytes the golden set was written against.

Then `read_trail()` reads the six links in order, and `cause()` names the first one that is off.

#### Do it: the trace

The four pipeline links are clean, and the fifth is off:

- the answer cache did not serve the answer;

- the index answered, with no fallback event since the break;

- the pool is the 20 the ablation decided;

- the Ranking API put it in order.

So the lane served what it holds, faithfully, and what it holds is the problem. Since the break, the ledger's current version of the handbook has been `5560308823a6`, not the golden set's `497809ffbaa6`, and that version declares it applies from 1 October 2026. The model link says only that the answer came from one citation. Whether the words follow the clause is `make judge`'s question; here they plainly do.

That is the proof: a wrong answer, traced to its cause (a version) by a cell nobody told what changed.

If `events since the break` shows `cache_stale`, your acme has a context cache packed before the break. The kit refused the stale pack and answered uncached: one more mark that the corpus moved.

#### Do it: the versions view and the two probes

Three instruments, one story:

- `make sources` shows the handbook indexed at the time of the break: reused 283, embedded 0, which is a reactivation. After a fresh ingest you would see 281 and 2. Its effective column says `-`, although the chunks declare 2026-10-01: a reactivation records the date only from the object's name, never from its text (step 7).

- The vector probe passes. The index Terraform declared is attached and deployed once, so the store link's verdict holds for the infrastructure too.

- The Firestore probe stops. It holds the ledger to the handbook in your checkout, and the ledger now names another version. A probe written for the rung has become a version check.

#### Do it: put version 1 back

These are version 1's bytes again. The worker finds a version it retired minutes ago and reactivates it, embedding nothing. The answer is 60 days again, citing version `497809ffbaa6`, and the Firestore probe passes both current modes. Revision 2's rows are retired again, and kept for 30 days.

### Why the trail looks like this, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The marks ride on the answer. `stages` goes back with every answer, and the usage row carries the same fields, all but one (see below). The caller, `make eval-live`'s report and `tenant_daily` therefore read one set of facts. A trace that needs log access is a trace fewer people can run.

- A version is named by its bytes. The chunk id carries the upload's SHA-256, so a citation says exactly which bytes answered, and the ledger says which bytes are current. Two uploads of the same bytes are one version, which is why the undo embeds nothing.

- Retired versions are kept, not deleted. The rows stay for 30 days, so an undo only flips a flag. `prefer_current()` keeps them out of every answer meanwhile.

- Read in order, and stop at the first mark that is off. A mark after a broken one tells you about the broken one, not about itself.

- The probes read and never write. That makes them safe to run on the live lane during an incident.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- A reactivated version forgets the date it declares. On the undo path, the worker records the source with `effective_from_of(msg.name, None)`: the date comes from the object's name, never from its text. So `make sources` showed `-` for revision 2 while its chunks carry 2026-10-01. A fresh ingest of the same bytes records the date.

- Nothing holds back a version dated in the future. `effective_from` reaches the prompt, in each source's header and in the dated rule. The dated rule only settles which source to follow when sources disagree. Nothing compares the date with today, so revision 2 answered from the moment it landed, whatever date it declares.

- The Firestore rung's pool is shared with retired rows. `RETRIEVAL_CURRENT_ONLY` is off by default on the lane (in `lesson-12.2.sh`), so `find_nearest` spends its 20 slots on current and retired rows alike, and `prefer_current()` drops the retired ones afterwards. A retired row carries the same vector as the current row it was copied from, so each sits beside its twin. In the panel the rung's pool is 10 of 20. The index is not affected, because the worker removes a retired version's datapoints.

- The usage row does not carry `vector_chunks`. The answer does, but `usage_row()` leaves it out. `tenant_daily` cannot count the answers the Firestore rung served for a `vector` tenant; only the log's `vector_search_fallback` events do.

- `/version` does not say how deep the pool is. `TOP_K_RETRIEVE` exists only in the revision's environment, which is why the trace reads it from Cloud Run.

- The Firestore probe is pinned to the frozen handbook. It refuses any other version of acme's handbook, a legitimate re-issue included. After a real release it keeps stopping until the checkout's `evals/corpus/` moves with the release.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme's handbook was re-issued as revision 2, then restored to version 1: two worker lines, and no embeddings if revision 2 was inside its 30 days. Revision 2's rows are retired again and kept for 30 days. Three questions were asked as `documind-ui-sa`, and their usage rows are in documind-api's log. `~/ask131-*.json` holds the three answers, and `operator-evidence/` holds the probes' evidence. Lesson 11.5 reconciles those usage rows with the reports and alerts built on them.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.4 Debug a wrong answer through the complete pipeline · v5.0

Next: Lesson 11.5 Reconcile usage events, reports and alerts.
