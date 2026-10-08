# Lesson 7.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.1_Graph_Evidence_WIX.html`, reviewed at blob `ce68fb1aaf2d3f04172a25e69ed3b5880f13a267`. Learners read that page on the course site; this guide keeps its prose.

Dense retrieval finds passages that sound like the question. A question about a relation, such as who approves a purchase above two lakh rupees, is better answered by following a named link from one thing to another. The kit builds those links from the tenant's own documents. It asks flash-lite for the entities and relations each passage states, and folds the different ways a name is written into one node. Every node and every edge keeps the chunk it came from, so a hop through the graph can be cited like a passage.

In this lesson you build the handbook's graph with `make graph`, read it back, and audit one extraction against the passage it came from.

- A graph built from what the text says

- The words: entity, relation, extraction, surface form, canonical name, node, edge, evidence

- Before you run anything: set up the shell

- The rules, run

- Build the handbook's graph

- Read it back: the counts, and one edge with its source

- Audit an extraction, and build again

- Why the graph is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn the four passes that turn passages into a graph, and the two rules that keep it honest: stated, never inferred; and a wrong merge is worse than a duplicate. You will also see why every node and edge carries a chunk id. Then you will prove it on your lane: node and edge counts from your own build, and one edge read back with the passage that states it.

### A graph built from what the text says

Four passes, two rules, and a chunk id on everything.

Why a graph at all. Dense retrieval ranks passages by how much they resemble the question. "Who approves a purchase of Rs 3,00,000?" needs the clause that names the approver, and that clause may not resemble the question at all. A graph reaches it from the names: from Purchase approval, along an edge, to the person who approves. The graph hands the retriever chunk ids by relation; lesson 7.2 walks it.

`services/ingest/graph.py` builds it in four passes:

- Extract. For each current text chunk of the tenant (the handbook's GEN- boilerplate is skipped), flash-lite returns a `GraphExtraction`. Its entities are a name exactly as written, with one of seven types. Its relations each have a source, a target, an UPPER_SNAKE verb and a confidence. One rule governs both: only what the passage states.

- Resolve. The same thing written differently becomes one node. First `normalise()` removes case, punctuation and company suffixes such as Pvt and Ltd. Then text-embedding-005 compares what is left, and merges two names only at cosine 0.92 or above. A wrong merge is worse than a duplicate node.

- Build. Each canonical name becomes a node, carrying every chunk id that mentions it. Each source, target and relation becomes an edge, carrying the chunk that states it and the best confidence seen. A relation whose end is not an entity, or that points at its own source, is dropped.

- Load. The nodes and edges go to `graph_nodes` and `graph_edges`, in the same Firestore database as the chunks, every document keyed by tenant. Each extraction is cached in `graph_extractions` under its chunk's hash.

A node is its chunk ids. The graph is evidence, not knowledge. Every node lists the chunks that name it, and every edge names the chunk that states it. So an answer that reached a clause through the graph can still cite the clause, and anyone can check an edge by reading one passage.

A lawyer's index to a case file. She lists every party and every relation the documents state, such as "the tenant paid rent to the landlord (page 12)". She records only what the file says, and every line carries its page.

The same man appears as R. Sharma, Rajesh Sharma and the appellant. She merges those only when she is sure: merging two different Sharmas would wreck the brief, while a duplicate entry costs one extra look.

Because every line points to a page, anyone can check the index. The parties are the entities, the page references are the chunk ids, and her care over merges is the 0.92.

#### Every edge, with the passage that states it

Pick an edge the build kept, or a relation it dropped. The panel shows:

- the edge, the clause that states it, and its confidence;

- the two nodes, the clauses that cite them, and the spellings folded into them;

- the passage, with the names marked.

The graph is the build's: the kit's `resolve_entities()` and `build_graph()` over the stand-in's extractions of the handbook's 11 clauses. On your lane flash-lite writes the extractions, so your names and counts will differ.

The extractions behind it were written for this page, following the prompt's rule. Flash-lite may name more things or fewer. The rules the build applies to them are the kit's own.

### The words: entity, relation, extraction, surface form, canonical name, node, edge, evidence

Ten rows, each with the value it takes on your lane.

One distinction to hold: resolution decides which names are the same thing, and the build decides which relations survive. A mistake in the first joins things that should stay apart; a mistake in the second loses a link. The kit errs towards duplicates and drops.

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

You need the shell in the kit's folder, with `PROJECT` set, and the Python packages `make graph` names: `google-genai`, `google-cloud-firestore` and `numpy`.

- The build calls flash-lite once per clause (eleven for the handbook) and text-embedding-005 once. That is a few paise.

- `--rebuild` erases acme's graph first. Nothing reads the graph unless `RETRIEVAL_GRAPH` is on, and it is off on the lane.

### The rules, run

The extraction's schema, the resolution and the build, on a small example, with no model called.

#### Definition

The cell imports the kit's `graph.py` and runs its pure parts:

- `normalise()` on seven names;

- `resolve_entities()` with an embedding that tells every name apart, so only `normalise()` can merge anything;

- `build_graph()` on two short passages that include a relation to a non-entity and a relation to itself.

#### The code

#### Do it

- `normalise()` alone folds the three ACMEs into one name, and the two function heads into another.

- CFO and Chief Financial Officer stay two nodes. No normalisation turns one into the other; on your lane only text-embedding-005 at 0.92 could merge them.

- The node id is the SHA-1 of the canonical name, so a rebuild writes the same documents.

- `build_graph()` dropped two relations: the one to "board", which is not an entity, and the one from Function Head to itself.

- function head is cited by both passages: one node, two chunk ids.

### Build the handbook's graph

A dry run that counts the clauses, then the build over them.

#### Definition

`make graph` runs `graph.py` for the tenant. `--source hr_policy_2026.md` keeps one document's chunks; otherwise reading order puts the Acts first and the handbook's clauses would come last. The two runs:

- `--dry-run` counts the chunks the build would send, and sends nothing: the bill, before any call.

- `--rebuild` erases the tenant's graph, then extracts, resolves, builds and loads.

#### Do it

Eleven clauses, eleven extractions, all fresh. Then 28 surface forms resolved to 25 nodes, and 15 edges were written. This first rebuild deleted nothing because there was no graph yet; on a lane that had one, it prints the counts it removed.

Your counts are your flash-lite's. The `graph_built` line is the one to keep.

Your terminal also shows lines this block leaves out: one `HTTP Request: POST ...` for each model call, twelve here, printed by the SDK's own logging. The JSON lines are `graph.py`'s.

### Read it back: the counts, and one edge with its source

From Firestore, not from the build's own printing.

#### Definition

The cell reads acme's graph from Firestore. It counts the tenant's nodes and edges, and lists the nodes the most chunks cite. Then it picks one edge (the one that names the CFO, if there is one; otherwise the most confident), reads that edge's chunk from the `chunks` collection, and prints the passage. Last, it checks that both names appear in it as written.

#### Do it

The counts match the build's line. Earned leave is the node the most clauses cite: three mention it, written two ways.

The CFO edge came back with its chunk id, and that chunk is FIN-02, the sentence in which the CFO approves anything above Rs 2,00,000. Both names are in the passage as written.

That is the proof: node and edge counts, and one edge read back with its source chunk.

### Audit an extraction, and build again

The rule checked on one passage, then a build the cache answers.

#### Definition

The cell reads the cached extraction for FIN-02 from `graph_extractions` and prints it beside its passage. It checks each entity name against the passage, and each relation's two ends against the entities. Then `make graph` runs again without `--rebuild`: every cached extraction whose hash still matches its chunk's is used as it is.

#### Do it

The audit makes the rule checkable. Every entity name is in its passage as written, and every relation joins two of them. A name the passage does not contain would be an inference, and the audit would print `NOT IN THE PASSAGE`.

The rerun sent nothing to flash-lite (`fresh 0`), because each cached extraction still matches its chunk's hash. It wrote the same 25 nodes and 15 edges over themselves: stable ids, no duplicates.

### Why the graph is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Stated, never inferred. The graph says only what the documents say, so every edge can be checked against one passage. A model's world knowledge would be unfalsifiable here.

- A wrong merge is worse than a duplicate. Two nodes for one thing cost a second hop. One node for two things sends the walk to the wrong clause. That is why the threshold is 0.92.

- The chunk id on every node and edge. The graph points at evidence; it is not a store of facts. An answer reached through it cites the same passages as any other.

- Stable ids from the name. The id is the SHA-1 of the canonical name, so a rebuild writes over the same documents instead of adding new ones.

- The cache under the chunk's hash. A rerun pays only for chunks whose text has changed since their extraction.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- Nothing rebuilds the graph when a document changes. The ingest worker never writes `graph_nodes` or `graph_edges`. After a reindex, nodes point at the retired version's chunk ids until `make graph` runs again. At query time `prefer_current()` drops those chunks, so the graph silently stops contributing.

- The cache is keyed by chunk id, and a chunk id names the version. A re-issued document is extracted again in full, even though every unchanged chunk has the same hash. `graph.py`'s promise to pay only for new or changed chunks holds within a version, not across one.

- `load()` never removes anything. A build without `--rebuild` leaves every node and edge an earlier build wrote, including entities the documents no longer state. A withdrawn document's names stay in the graph.

- An edge's confidence is stored and never read. The walk and the retriever treat an edge at 0.3 exactly like one at 0.95.

- Nothing checks an extraction against its passage. `build_graph()` drops only dangling and self relations, so a name the passage does not contain becomes a node. Step 6's audit is the only check, and it is this page's, not the kit's.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme's graph now holds the handbook's clauses: its nodes and edges in `graph_nodes` and `graph_edges`, and eleven cached extractions in `graph_extractions`. Nothing serves from it yet, because `RETRIEVAL_GRAPH` is off on the lane. Lesson 7.2 compares the Firestore and Spanner paths through it, and puts the walk in front of the dense pool on a candidate.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.1 Build graph evidence from source documents · v5.0

Next: Lesson 7.2 Compare Firestore and Spanner graph paths.
