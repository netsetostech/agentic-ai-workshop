# Lesson 7.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.3_Managed_Mirrors_WIX.html`, reviewed at blob `5d2f8eed1c871bf3e8af3c1094e90280a07c7795`. Learners read that page on the course site; this guide keeps its prose.

The kit's own index lives in Mumbai, asia-south1. Two Google-managed stores can hold a copy of a tenant's documents too: a Vertex AI RAG Engine corpus in us-central1 and a Vertex AI Search data store in `global`. The worker copies each version it makes current into them, but only for a tenant whose `data_region` says `any`. The API reads a store only for a tenant pinned to it, and holds that pin against the same policy.

In this lesson you read the policies and the stores, and ask each tenant a question from the store it is pinned to. You trace one citation back to the store that found it. Then you watch the mirror refuse to copy a note for a tenant whose text must stay in India.

- A copy outside India, by the tenant's leave

- The words: mirror, corpus, data store, data_region, permits, the skip, mirrored, pin, policy_fallback, found_by

- Before you run anything: set up the shell

- The mirror's rules, run

- The policies, the pins and the stores

- Ask the stores, and find who found the cited chunk

- globex stays home: the skip, the ledger row, and a pin the policy overrides

- Why the mirror works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn where a tenant's text may be held, and who decides: the tenant's `data_region`, not the deployment. You will see how the mirror copies and skips, how the API turns a store's answer into the kit's chunks, and why a pin cannot move text the policy keeps home. Then you will prove it on your lane: a cited chunk `found_by: rag_engine`, and a `mirror_policy_skipped` line for globex, a tenant whose policy is `in`.

### A copy outside India, by the tenant's leave

Two stores, one policy per tenant, a write side and a read side.

Two stores beside the kit's own. Both are declared per tenant and named `documind-{tenant}`:

- A RAG Engine corpus in us-central1, the only region serverless corpora have. Each version's text goes in as one file named by its doc_key, and RAG Engine cuts it into pieces of 512 tokens with 100 overlapping.

- A Vertex AI Search data store in `global`, declared by `managed.tf`. Each version is one document whose id is its doc_key.

Neither store is in India.

The policy decides, per tenant. `tenant_settings/{tenant}.data_region` says where the tenant's text may be held:

- `any` lets a store outside India keep a copy.

- `in` keeps the text on the kit's own rows. An absent field, an unknown value and a document that cannot be read all mean `in`.

`permits()` is the whole rule: `any` permits every store, and `in` permits only a store whose region starts with asia-south. `make roster` set acme and zeta to `any` and globex to `in`. Only the operator writes the field, with `make tenant-policy`.

The write side: the mirror. When the worker makes a version current, it calls `Mirror.after_swap()` with the text it indexed:

- The text goes into every store the policy permits: one `mirror_ok` line and one `doc.mirror` audit event each.

- A store the policy forbids gets one `mirror_policy_skipped` line per tenant and store, and then silence.

- The version it replaced leaves every store, whatever the policy: a delete is never refused.

- The ledger row gets `mirrored`: the stores that hold the version, and their regions.

A picture or a video has no text and is never copied. `MANAGED_MIRROR=both`, which `make up` set, says which stores exist to copy into. The policy says whether this tenant's text may go there.

The read side: a pin, held against the policy. `tenant_settings/{tenant}.retrieval_backend` pins a tenant to a store (`make tenant-backend`). `make up` pinned acme to `rag_engine` and zeta to `vertex_search`. On every request, `retrieval_backend_for()` checks the policy. A pin to a store for an `in` tenant is served from the kit's own index instead, and the row says `policy_fallback 1`.

The store's answer, a RAG Engine context or a Vertex AI Search segment, becomes a chunk of the kit's contract through the version's own row. It gets the source, the doc_type, a fresh `current`, an id minted from its text (`#rag-...` or `#vs-...`), and `found_by`. The reranker, the packing, the answer and the citations stay the kit's.

A family's property papers and a lawyer in another city. The originals stay in the almirah at home in Mumbai. The lawyer's office may keep certified copies, but only of the files whose owner signed a consent letter. For each copy sent or recalled, the clerk writes a line in the register, and notes in the family's file index which offices hold one.

For the cousin's file, marked "do not send out", the clerk writes "not sent: owner's instruction" once, and sends nothing. When a paper is replaced, the old copy is recalled from every office, consent or no consent. Anyone who asks the lawyer about the cousin's file is sent to the almirah.

The consent letter is `data_region`. The register is the `doc.mirror` audit trail, and the file index is `mirrored`. The clerk's one line is `mirror_policy_skipped`, and being sent to the almirah is `policy_fallback`.

#### Where may this text go, and who answers?

Start from a tenant, then change any setting. The panel follows one version through the worker's mirror and one question through the API:

- the upload: each store's line, the ledger row's `mirrored`, and the audit events;

- the question: whether the pin is honoured, whether the policy sends it back to the kit's index, and what the pool's chunks say they were `found_by`.

The rules are the kit's: `Mirror.after_swap()` behind the worker's guard, `choose_for()`, `retrieval_backend_for()` and the store dispatch in `_dense_retrieve()`, ported and checked against the kit's code on all 352 combinations of these settings. The deployment's own backend is `vector`, as `make deploy-services` sets it.

It follows one upload and one question, not counts: how many chunks a store returns depends on the question and on what the store holds. "No store" is what a tenant without a corpus or a data store gets, which is globex today.

### The words: mirror, corpus, data store, data_region, permits, the skip, mirrored, pin, policy_fallback, found_by

Ten rows, each with the value it takes on your lane.

One distinction to hold: `MANAGED_MIRROR` is the deployment's list of stores it can copy into, and `data_region` is each tenant's permission. The first is the same for every tenant. The second is why acme's text is in RAG Engine and globex's is not.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above. Module 0 installed the API's requirements, including `google-cloud-aiplatform` and `google-cloud-discoveryengine`, which step 5 imports.

- The pin window. The setup moved acme to the kit's own index for the lessons that read it. Step 5 moves it back to RAG Engine, where `make up` put it, so the window's closing line then changes nothing.

- What the lesson changes. It reads the stores, asks a handful of questions, and uploads one short note to globex. It copies nothing into a store.

### The mirror's rules, run

The kit's Mirror with two stand-in stores and a policy, through five moves.

#### Definition

The cell imports the kit's `managed.py` and runs its `Mirror`, the class the worker holds, with two stand-in stores: one in us-central1 and one in `global`, as the real ones declare. The policy is a dict: acme `any`, globex `in`. The five moves:

- acme's version v1 becomes current;

- globex adds a note;

- globex adds a second note;

- acme's policy is turned to `in`, and version v2 becomes current;

- v1 is retired.

#### The code

#### Do it

- `policy_of()` reads `any` only when the field says so. An absent field, `us` or any other value is `in`. `ANY` counts, because the value is trimmed and lower-cased.

- acme's v1 went to both stores: two `mirror_ok` lines and two audit events. `held` names both regions, which is what the ledger row's `mirrored` will say.

- globex's note went nowhere: one `mirror_policy_skipped` line per store. The second note printed nothing, because the skip is said once per tenant and store.

- Turning acme to `in` stopped v2, but v1's copies stayed. The policy is judged when a version is copied, not afterwards.

- Retiring v1 took it out of both stores, although acme is now `in`: a delete is never refused. The audit trail has four events: two copies in, two out.

### The policies, the pins and the stores

What each tenant may do, where it is pinned, and what each store holds against the ledger.

#### Definition

Given no value, `make tenant-policy` and `make tenant-backend` print what `tenant_settings` holds for a tenant. `make managed-status` holds every store against the ledger. For each tenant and store it prints how many versions the ledger calls current, how many the store holds, and the difference.

#### Do it

- The policies are `make roster`'s: acme and zeta `any`, globex `in`. The pins are `make up`'s, except acme's, which the setup's pin window moved to the kit's index.

- zeta's stores are in sync: 7 versions in the ledger, and 7 in each store.

- globex has no store at all, no corpus and no data store. `managed-stores` makes corpora only for acme and zeta, and `managed.tf` declares data stores for the same two.

- acme reads `drift` in both stores: 21 versions current, 18 held, 3 missing. The missing doc_keys are the corpus's three pictures: Figure 3 of the annual report, the invoice image and page 30 of the Bonus Act. The mirror never copies a version without text, but `status()` counts every indexed version.

Your counts include your own uploads. The three pictures are missing on every lane that ran `make ingest-corpus`.

### Ask the stores, and find who found the cited chunk

Each tenant from the store it is pinned to; then the cited chunk, found in the kit's own pool.

#### Definition

acme's pin goes back to `rag_engine`. The API reads a tenant's settings once a minute per instance, so the cell waits a minute. Then `ask153` asks each tenant a question its own documents answer, as `documind-ui-sa`. It prints the store that served, the pool, the answer and the chunk the answer cites.

#### Do it

- acme answered from RAG Engine: 17 chunks in the pool, 14 from the store. The other 3 are the kit's own figure rows: a store holds text only, so the pictures join from the kit's index.

- zeta answered from Vertex AI Search: every chunk in its pool came from the data store, because zeta has no pictures.

- globex answered from the kit's index (`vector`): it has no pin and no store.

- The chunk ids tell the stores apart: `#rag-...` for acme, `#vs-...` for zeta, and the kit's own `tenant:sha256#n` for globex. A store does not keep the kit's chunk ids, so the API mints one from the version's key and a hash of the text.

The answer's citation carries no `found_by`, because the kit's Citation has no such field. The stamp is on the chunk in the pool. This cell asks the API again, then runs the kit's own `retrieve()` in your shell with backend `rag_engine`, the call the API made, and looks for the cited chunk in that pool.

The pool is the same 17 chunks the API saw: 14 found by `rag_engine`, and the 3 figure rows, which carry no `found_by` at all. The chunk the answer cites is in it, `found_by rag_engine`, at 1 minus its RAG Engine distance.

That is the first proof: `found_by: rag_engine` on the cited chunk. The id matches because the store returns the same text for the same question.

### globex stays home: the skip, the ledger row, and a pin the policy overrides

A note to a tenant whose text may not leave India, the worker's two lines about it, and a pin that changes nothing.

#### Definition

The cell writes a short note and uploads it to globex with `make reindex`, which waits for the worker's line. Your email and the time in the note make its bytes new, so the worker ingests it instead of acknowledging a copy it has already seen.

#### Do it

Then read what the worker's mirror said about the note, and the ledger row it stamped:

There are two `mirror_policy_skipped` lines, one per store, each with the region the store holds data in and globex's `data_region: in`. That is the second proof. The ledger row says `mirrored {}`: the kit's rows only. Nothing was copied, so nothing was audited.

If your lines are missing, the worker instance that took the note had already said it: the skip is said once per tenant and store per instance. The cell then prints the last week's lines instead, and the empty `mirrored` on the row is the record for this document.

Last, try to move globex's text with a pin:

The pin was written, and the API served globex from the kit's index anyway: `retrieval_backend vector`, `policy_fallback 1`. A pin chooses among the stores the policy allows; it cannot move text the policy keeps home. The last line clears the pin again.

### Why the mirror works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- A policy per tenant, not per deployment. Residency used to be one variable for the whole deployment. Since 13 September it is one field per tenant, so one deployment serves acme from RAG Engine and globex from Mumbai.

- Fail closed. An absent field, an unknown value and an unreadable document all mean `in`, so nothing leaves by accident.

- The operator writes the policy; no service can. A service that could widen its own tenant's region could export the tenant's documents.

- A store per tenant. RAG Engine has no metadata filter, and Vertex AI Search's needs a schema, so isolation is structural: no store ever holds two tenants' text.

- The mirror never fails an ingest. A missing store, a refused policy or a failed upload is one line. The kit's own rows are the record.

- The store retrieves; the kit does the rest. The reranker, the packing, the answer and the citations are the kit's, so an answer from RAG Engine reads, and is judged, like any other.

- A delete is never refused. Taking text out is the direction the policy wants.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- `make managed-status` never reads `in sync` for acme. It holds each store against every indexed version, and the mirror never copies a picture or a video, so acme's three pictures are missing from both stores for good. A check that meant "in sync" would compare text versions only.

- Turning a tenant to `in` removes nothing already copied. `set_policy()` writes one field. The copies stay in RAG Engine and Vertex AI Search until each version is retired, and `make managed-status` goes on saying `in sync`, because it never reads the policy.

- Nothing repairs or backfills a missing copy. `managed.py` says the nightly walk repairs the mirror, and the Makefile says a version ingested before its corpus existed waits for that repair. But `reconcile.py` only removes versions from the stores. A failed upload (`mirror_failed`), a version older than its store, or a tenant turned to `any` stays uncopied until each version is ingested again.

- A Vertex AI Search copy is recorded before it exists. The import is a long-running operation. `mirror_ok`, the `doc.mirror` event and the ledger's `mirrored` all follow the request, and nothing checks that the import finished.

- `found_by` stops at the pool. The Citation contract has no `found_by`, so an answer shows its store only in the chunk id's `#rag-` or `#vs-`. The figure rows that join a managed pool carry no `found_by` at all.

- `make down` cannot finish while the data stores exist. `managed.tf` marks them `prevent_destroy`, and Terraform rejects any plan that would destroy such a resource, so `make down`'s `terraform destroy` fails before it removes anything. The README says `make down` names the protected stores; its closing list does not. Deleting the throwaway project, which is `make down`'s own last line, is the sure way to stop the bills.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme is pinned to `rag_engine` again, where `make up` put it, and globex's pin is cleared. globex holds one more document, the visitor note, on the kit's own rows only: its ledger row says `mirrored {}`. No store gained or lost anything. Lesson 7.4 compares the stores' answers with the kit's, and tests what a reindex, an undo and a withdrawal do to them.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.3 Configure and query managed retrieval mirrors · v5.0

Next: Lesson 7.4 Compare quality and test update/withdrawal freshness.
