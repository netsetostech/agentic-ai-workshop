# Lesson 7.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.2_Graph_Paths_WIX.html`, reviewed at blob `1a20d1bb8fa54cb05200972a3aeeeb45d4c3e58d`. Learners read that page on the course site; this guide keeps its prose.

Lesson 7.1 built the handbook's graph. A walk through it has to start somewhere: a seed, the node the question is about. The kit can keep the same graph in two stores, and they find the seed in different ways. Firestore looks for a stored name inside the question, so "Who signs off on a big purchase?" finds nothing: the handbook says Purchase approval and names the CFO, and the question says neither. Spanner compares the question's meaning with every node's name, so it can start from Purchase approval, and one hop along an edge reaches the CFO.

In this lesson you walk both graphs with that question, build the Spanner copy, and put the walk in front of the dense pool on a candidate, once from each store.

- Two ways into one graph

- The words: seed, containment, candidate name, meaning, cosine distance, threshold, hop, property graph, interleaving, graph_chunks

- Before you run anything: set up the shell

- The seeders, run

- The Firestore path: a name the question contains

- The Spanner path: build it, read it, walk it by meaning

- The walk in front of the dense pool, on a candidate

- Why two paths, what each costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how a walk starts, and the two ways the kit finds its seed: containment on Firestore, cosine distance on Spanner. You will see what the walk hands the retriever, and when `auto` lets it run. Then you will prove it on your lane: the CFO question, which never says CFO, answered with the walk in front of the pool, and `/version` naming the store that walked.

### Two ways into one graph

A seed, a walk, and what the walk hands the pool.

A walk needs a seed. The graph from lesson 7.1 is nodes and edges, and each carries the chunk ids that state it. `retriever.graph_candidates()` uses it in three moves:

- Seed. Find the nodes the question is about: at most five.

- Walk. Follow edges from them in either direction, `GRAPH_HOPS` hops (one by default), keeping at most `GRAPH_CAP` nodes (20).

- Hand over. Fetch the chunks those nodes cite, by id, and put them in the pool ahead of the dense candidates.

The graph can help only a question it can seed.

Firestore seeds by name. `FirestoreGraph.seed()` reads every node of the tenant. It keeps a node when the node's name is inside the lower-cased question, or when the name contains a capitalised run of the question of five letters or more (question words such as Who and Which are left out). There is no model call. A stored name has to appear in the question, even if only as part of a word.

Spanner seeds by meaning. `make graph GRAPH_BACKEND=spanner` stores each node's name with its text-embedding-005 vector, in a column called `embedding`. At question time `SpannerGraph.seed_by_vector()` embeds the question once and asks Spanner for the five names nearest to it by cosine distance. A name farther than `GRAPH_SEED_DISTANCE` (0.4) does not seed, so a question about nothing in the graph seeds nothing.

The walk itself. On Firestore, each hop is two `in` queries per 30 node ids: edges out, then edges in. On Spanner, the whole walk is one GQL statement over the `DocuMindGraph` property graph. The seeds, their neighbours and the neighbours' chunk ids are all read in one consistent snapshot.

When the walk runs. `RETRIEVAL_GRAPH` is off on the lane:

- `on` walks every question that finds a seed.

- `auto` also needs a relational word, such as who, which, whose, depend or supersede. `choose_mode()` checks for one with a regular expression, not a model.

Either way, the walk's chunks join the pool first, at score 1.0, and the reranker then orders the whole pool.

The directory board and the enquiry counter at a government hospital. At the gate, a board lists the departments by name: Cardiology, Orthopaedics, Nephrology. A visitor who knows the word walks straight there. A visitor who says "my father has chest pain" gets nothing from the board.

The clerk at the enquiry counter understands what the visitor means and sends them to Cardiology. From Cardiology, a sign in the corridor points on to the ECG room.

The board is containment: free and instant, but useless without the department's name. The clerk is meaning, and costs a salary whether or not anyone asks, as Spanner bills by the hour. A good clerk who is unsure says "go to the general OPD" rather than guess: that is the threshold, past which the dense pool answers alone. The corridor signs are the edges.

#### One question, two ways in

Pick one of the seven questions, or type your own. The panel runs both seeders over the handbook's graph from lesson 7.1:

- the Firestore column runs the kit's containment rule exactly, on any question you type;

- the Spanner column ranks the names by distance, and the slider sets `GRAPH_SEED_DISTANCE`;

- both show whether `RETRIEVAL_GRAPH` lets the walk run, the nodes it reaches, and the clauses it puts first in the pool.

The graph is lesson 7.1's: 25 nodes and 15 edges from the stand-in's extractions. The Firestore column is the kit's own `_candidate_names()`, `_seed_match()`, `choose_mode()` and walk, ported and checked against the kit's code on 1,926 cases. The Spanner column's distances come from this page's stand-in for text-embedding-005; step 5 prints yours.

The distances come from a stand-in: a vector per phrase built from a small table of concepts, plus noise, so that related phrases land near each other. Your lane's numbers will differ, and so may the names that fall inside 0.4. The rules both columns apply are the kit's own.

### The words: seed, containment, candidate name, meaning, cosine distance, threshold, hop, property graph, interleaving, graph_chunks

Ten rows, each with the value it takes on your lane.

One distinction to hold: the seed decides where a walk starts, and the edges decide where it goes. Spanner changes the first and not the second. Both stores hold the same nodes and edges, so from the same seeds they reach the same nodes; only which of them survive the 20-node cap can differ.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION` and `NUMBER` set by the setup above. Module 0 installed `google-cloud-spanner` with the ingest requirements. You also need:

- Lesson 7.1's graph in Firestore, with its cached extractions. If you skipped 7.1, run its build first: `make graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS="--source hr_policy_2026.md --rebuild"`.

- The Spanner instance `documind-graph`. `make up` created it with the rest of the lane, and it has billed by the hour ever since, whether or not anything reads it.

The two candidates in step 6 take no traffic. The live revision serves throughout, and step 6 ends by putting the template back.

### The seeders, run

The containment rule and the relational gate on six questions, then the kit's own tests of the Spanner walk.

#### Definition

The cell imports the kit's seeding functions and runs them against eight names from the handbook's graph:

- `_candidate_names()` and `_seed_match()`, with the seeds sorted longest first, as `FirestoreGraph.seed()` sorts them;

- `choose_mode()`, which decides whether `auto` walks.

The six questions ask about purchases and approvals in different words. Then `unittest` runs `commands/tests/test_spanner_graph.py`: the kit's 8 checks of `SpannerGraph.expand()`, against a strict fake that refuses what live Spanner refuses.

#### The code

#### Do it

- The CFO question seeds nothing. Neither "purchase approval" nor "cfo" is inside "who signs off on a big purchase?", and the question has no capitalised run of five letters. The Firestore path cannot start a walk from a description.

- Naming the role works. "cfo" is inside "which purchases need the cfo?", so the CFO seeds, and "which" is a relational word, so `auto` walks.

- "What does the CFO approve?" seeds the CFO but stays dense. Neither "what" nor "approve" is in `choose_mode()`'s list, so `auto` never walks it; `on` would.

- A capital letter changes the seeds. "Purchase" with a capital is a candidate name of eight letters, and it is inside "purchase approval". With a small p, the same question seeds nothing.

- Part of a word is enough. "india" is inside "indian", so India seeds a question about travel claims, and the walk would lead to WFH-01, the remote-work clause.

- The Spanner walk passes its own tests: one snapshot for the whole walk, edges followed both ways, the cap counted on distinct nodes, no chunk from another tenant, and one or two hops only. The learner repository's dry run runs them on every push.

### The Firestore path: a name the question contains

The kit's question without the word CFO, then with it.

#### Definition

`make graph` with `--ask` walks the graph for one question and prints what the API would fetch: the seeds, the nodes and the chunk ids. On Firestore it seeds by containment, as `graph_candidates()` does when `GRAPH_BACKEND` is firestore. It only reads; no model is called.

#### Do it

The kit's question found no seed, so the walk had nowhere to start. The API would get an empty list, and the dense pool would answer alone.

With the word CFO, the CFO seeded, and the walk went one hop to Purchase approval and handed over one chunk id: FIN-02's. To seed, each walk read every node of acme's graph, 25 documents each time. That is what containment costs without an index.

### The Spanner path: build it, read it, walk it by meaning

The same graph written to Spanner with a vector per name, read back as tables and as a graph, then walked for the kit's question.

#### Definition

- `make graph GRAPH_BACKEND=spanner` runs lesson 7.1's four passes and writes the result to Spanner. The extractions come from the cache in Firestore, so nothing is sent to flash-lite. Two embedding calls remain: one to resolve names, and one for the node vectors.

- `SpannerGraph.load()` writes every node, with its vector, and every edge in one commit. It prints nothing, so the `graph_built` line is the record.

- The cell then reads both tables in one snapshot. It prints the counts, how many nodes carry a vector, and the CFO's edge with the names at both ends joined from `GraphNode`. Last, it walks one hop from the CFO with the kit's own GQL.

#### Do it

Spanner now holds the same 25 nodes and 15 edges as Firestore, and every node carries a 768-number vector. The line shows `fresh 0`: lesson 7.1 cached the extractions, and the cache does not care which store the graph goes to. The load was one commit of 265 mutations, because Spanner counts one mutation per column written: seven for each node row and six for each edge row.

Your terminal also shows lines this block leaves out: one `HTTP Request: POST ...` for each model call, printed by the SDK's own logging, here and in the walk below. The JSON lines are `graph.py`'s.

The CFO's edge came back two ways. As tables, `GraphEdge` is joined to `GraphNode` twice, for the names at both ends. As a graph, the kit's GQL walk goes from the CFO. Both reach Purchase approval and FIN-02.

Now the kit's question, seeded by meaning. On Spanner, `--ask` prints the five nearest names, each with its distance and whether it passed 0.4. Then it walks from the names that passed.

Purchase approval is 0.183 from the question: the only seed. The CFO is 0.415, just outside 0.4, so it did not seed. The walk reached it anyway, one hop from Purchase approval along the approval edge. The function head came the same way and brought EXP-12, the clause on travel above the cap. So the walk hands over two chunk ids: FIN-02's, which answers the question, and EXP-12's.

These distances are the stand-in's. Read your own before step 6. If no purchase or approval name on your lane is within 0.4, the walk seeds nothing, and step 6 shows how to set the threshold on the candidate from your numbers.

### The walk in front of the dense pool, on a candidate

One question, one candidate, each store in turn; `/version` and the pool say which walked.

#### Definition

`make candidate RETRIEVAL_GRAPH=auto GRAPH_BACKEND=...` makes a revision of the API that takes no traffic, tagged `candidate`, while the live revision keeps serving. `ask152` asks the candidate's `/version` what is serving. Then it asks the kit's question as `documind-ui-sa` and prints the answer, `stages.pool` and `stages.graph_chunks`, and each clause cited.

#### Do it

First with the walk from Firestore:

Then the same candidate, walking from Spanner:

- `/version` named the store each time: firestore, then spanner, with `RETRIEVAL_GRAPH` auto.

- From Firestore, the walk put nothing in the pool: 0 of 20, because there was no seed, as in step 4.

- From Spanner, it put 2 chunks first: FIN-02 and EXP-12, found by meaning and fetched by id ahead of the dense candidates.

- Both answers name the CFO, and the question never did. That is the proof: the CFO question answered without the word CFO, with the walk's share in `graph_chunks` and the store in `/version`.

Notice what the first answer says, too. Dense retrieval found FIN-02 without any graph, because the handbook is small and the clause says "purchase". The Spanner walk made sure FIN-02 was in the pool whatever the dense ranking did. On a corpus where the answer's words are far from the question's, that is the difference.

Set the threshold on the candidate alone, from your own numbers, and ask again. `make candidate` cannot pass it (step 7 says why), so this is a gcloud line:

Choose a value just past the purchase or approval name, and below the first name that has nothing to do with purchases. The undo below removes it.

Last, put the template back. Environment variables carry over from one revision to the next, so the candidate's settings would ride into the next `gcloud run services update` of the API. The undo writes `RETRIEVAL_GRAPH=off` and `GRAPH_BACKEND=firestore`, removes any `GRAPH_SEED_DISTANCE`, drops the tag, and deletes `.candidate-revision`.

The live revision still takes 100 percent. It never changed, and its `RETRIEVAL_GRAPH` is still off.

### Why two paths, what each costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Firestore first, because it is already there. The graph sits beside the chunks, in a database billed per operation. There is nothing to provision, nothing billed by the hour, and the tenant's predicate is on every read.

- Spanner for the shape of the data. The walk is one GQL statement in one snapshot, however many hops. Edges are interleaved in their source node, and `tenant_id` comes first in every key. So a tenant's subgraph is stored together, and deleting a tenant cascades to its edges: DPDP erasure as a property of the schema, not a batch job.

- Seeding by meaning, for the words people use. A question rarely contains the handbook's own name for a thing. A vector per name, and one embedding call per question, close that gap.

- A threshold, because nearest is not the same as near. The five nearest names always exist. 0.4 decides which are close enough, so a question about nothing in the graph seeds nothing and `auto` stays dense.

- Exact distance, no vector index. `spanner.tf` gives the reason: `COSINE_DISTANCE` over a few thousand nodes is enough, and an approximate index needs tuning that a lab cannot judge.

- The walk goes first; the reranker decides. The walk's chunks join the pool at score 1.0. A wrong seed spends pool places, and the reranker still orders the whole pool.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- `make candidate` cannot set the threshold. It writes `RETRIEVAL_GRAPH` and `GRAPH_BACKEND`, but no make target and no deploy script passes `GRAPH_SEED_DISTANCE`, `GRAPH_SEED_K`, `GRAPH_HOPS` or `GRAPH_CAP`. `graph.py`'s comment says the threshold is set from `--ask`'s numbers; today that takes a gcloud line, as in step 6.

- On Spanner, a name in the question does not count by itself. The API seeds by distance only. `SpannerGraph.seed()`, which runs the containment query in SQL, is reached by nothing on the lane. A question that names a node exactly still seeds nothing if its embedding is farther than 0.4 from that name.

- The usage row does not say which store walked. It carries `retrieval_graph` and `graph_chunks`, not `graph_backend`. Rows from a Spanner candidate and a Firestore revision look the same in BigQuery; only `/version`, one revision at a time, tells them apart.

- `SpannerGraph.load()` writes the whole graph in one commit. Spanner refuses more than 80,000 mutations in a commit, counted per column written: 7 for a node row and 6 for an edge row. The handbook's graph is 265. A tenant's graph past about 6,153 nodes, with as many edges, needs batching that the kit does not do. `FirestoreGraph.load()` commits every 400 writes.

- Firestore's seed reads every node, for every question. Its docstring says production would keep a name-token index. There is none, so the reads grow with the graph: 25 on the handbook's, thousands on a whole corpus.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

acme's graph now lives in Spanner as well: 25 nodes, each with a vector, and 15 edges, in the instance that was already billing. The API's template is back to `RETRIEVAL_GRAPH` off and `GRAPH_BACKEND` firestore, the candidate tag is gone, and the live revision never changed. Lesson 7.3 turns from the graph to the managed stores: RAG Engine and Vertex AI Search as mirrors of the kit's index, and the data-region policy that decides which tenants they may serve.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.2 Compare Firestore and Spanner graph paths · v5.0

Next: Lesson 7.3 Configure and query managed retrieval mirrors.
