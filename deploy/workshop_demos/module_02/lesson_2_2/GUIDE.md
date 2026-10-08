# Lesson 2.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.2_Hybrid_WIX.html`, reviewed at blob `e328b1eb4da48eab527de6f40bfc73967d53aefb`. Learners read that page on the course site; this guide keeps its prose.

Lesson 2.1 reproduced the API's pool by hand: one vector, one index, the tenant restrict. This lesson adds the second leg. Every datapoint already carries a sparse vector (lesson 1.3); the index can search by it, fuse the two lists by rank rather than by score, and hand back one pool; a deployment setting turns that on; and a harness measures each choice on the golden set with no model in the loop. You will rank acme's own rows with two sparse rulers and see one find the right clause first while the other buries it, fetch the same question three ways from the index, fuse two of the lists yourself with the kit's function and match the server's order, run the ablation and read recall, MRR and p95 per arm, then turn hybrid on for a candidate revision that takes no traffic and compare its answers with the live dense ones.

- What a second leg adds, and how two lists become one

- The words: leg, TF, IDF, BM25, RRF, alpha, k, arm, recall@k, MRR, p95, ceiling

- Before you run anything: set up the shell

- The lane runs dense, and two sparse rulers over its own rows

- Three ways through the index: dense, sparse only, fused

- RRF by hand: the kit's rule reproduces the server's order

- The ablation: one knob per arm, no model in the loop

- The knob: hybrid on a candidate that takes no traffic, compared, then removed

- What hybrid costs, where it cannot go, and what the harness does not measure

- Verify it yourself: the checklist

You will learn what the sparse leg of hybrid retrieval is made of, why two ranked lists are merged by position with Reciprocal Rank Fusion rather than by score, and why a sparse leg is only as good as its weights. Then you will prove it on your lane: rank acme's rows with the index's ruler and the ablation's, ask the index dense, sparse-only and fused, reproduce the fused order with `rrf_fuse()`, run `make ablate`, and judge `RETRIEVAL_MODE=hybrid` on a candidate revision before it serves anyone.

### What a second leg adds, and how two lists become one

Meaning and spellings are found by different rulers, fused by rank, and only as good as their weights.

Retrieval finds evidence two ways, and each is blind where the other sees. The dense leg turns the question and every chunk into 768 numbers from a model that has read a great deal of text, so "quit" lands near "resign" and a question about senior staff finds a clause about grade E3. It is weak exactly where a token means nothing outside this corpus: an invoice number, a clause code, a product name is just a rare string to it. The sparse leg counts the words themselves. "INV-2026-0412" matches "INV-2026-0412" and nothing else, and it will never know that "quit" and "resign" are the same request. Hybrid retrieval runs both legs and merges the two ranked lists into one pool.

The merge goes by rank, not by score. A dense distance and a sparse dot product live on different scales, so adding them would let one leg drown the other. Reciprocal Rank Fusion ignores the scores: each list gives an id 1 / (k + rank) points, the dense list's points are multiplied by alpha and the sparse list's by 1 - alpha, the points are summed and the ids sorted. With k at 60, being first rather than second is worth a little; being on a list rather than absent is worth a lot. The kit's `rrf_fuse()`, the ablation's `rrf()` and the index's `rrf_ranking_alpha` are three spellings of this one rule, and the API sends alpha 0.7.

A sparse leg is only as good as its weights. The index's sparse leg weights a word by how often it appears in the chunk, 1 for the first time and 0.5 for each repeat, and every word counts: "the" as much as "invoice". A long Act page with sixty occurrences of "the" and "of" therefore outscores the one invoice that carries the number you asked for. The ablation's sparse leg is BM25, which does two more things: it weights a word by how rare it is across the corpus, so "inv-2026-0412" counts and "the" barely does, and it discounts long chunks. On acme's corpus that is the difference between finding the invoice first and finding it around rank one thousand. This is the finding steps 3 and 4 confirm on your lane, and it is why the question "is hybrid better?" has to be answered as "which hybrid, and measured how".

Two clerks and a chair. A records room with two clerks. The first has read every file and brings the pages that mean what you asked. The second works from a concordance and brings every page that carries your exact words, and if you let him count every "the", he brings the longest pages first. The chair never compares the clerks' confidence. She takes each clerk's ranked stack, gives a page 1 / (60 + position) points for where it sits in each stack, trusts the first clerk 70 to 30, and reads the totals. A page both clerks brought rises. A page only the second clerk brought, at 30 percent, cannot outscore anything in the first clerk's top twenty, and that arithmetic is in step 5.

#### The fusion bench: two sparse rulers and one rule, on acme's real questions

Pick a golden question. Leg A is what the index's sparse leg computes for it: the kit's encoder on the question and on every chunk of acme's corpus, scored by dot product, as the index scores a sparse vector. Leg B is the ablation's leg, BM25, over the same chunks. The anchor is the golden row's clause or document, and each leg says where it ranked it. The table underneath fuses two lists with the RRF rule at the alpha and k you set: list 2 is leg A, and list 1 is your dense order from step 4 once you paste it, with leg B standing in until then.

Computed when this page was built by the kit's own code: `shared/sparse_encoder.py` for leg A, BM25Okapi with rank_bm25's constants (k1 1.5, b 0.75) for leg B, over the 1,628 chunks the kit's chunker cuts from acme's 17 markdown mirrors. Your lane's Act chunks came through Document AI and differ; the ranks in step 3 are yours. The fusion is the rule in `rrf_fuse()`, character for character, in JavaScript.

It has no dense leg of its own, because that needs the model and your lane; step 4 gives you the list to paste. Until then, list 1 is leg B, which makes the RRF table a demonstration of the rule on two rankers that disagree, not of what the API fuses. Move alpha from 0.7 towards 0 on the invoice question and watch which ruler's first choice wins the fused top: that is the whole meaning of alpha.

### The words: leg, TF, IDF, BM25, RRF, alpha, k, arm, recall@k, MRR, p95, ceiling

Twelve words, each with the value it takes on your lane.

Two of these words carry the lesson's finding: the index's sparse leg and BM25 are both "sparse", and they are not the same ruler. Keep them apart when someone says the ablation proved hybrid does nothing: it proved that about one of them.

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

The index endpoint, the deployed index and the retrieval settings live in the API's environment; steps 3, 4 and 7 use them. An empty value means the setting's default, which the page names where it matters; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and step 8's cell imports the kit. The ablation's sparse leg needs `rank_bm25`, which the kit's images do not carry because no service runs it; the pip line puts it in the venv once.

### The lane runs dense, and two sparse rulers over its own rows

The setting that decides the mode, the vector the second leg is made of, and the bench run on your rows for Rs 0.

#### Definition

The mode is a deployment setting: `retrieval_mode` in config.py is "dense" unless `RETRIEVAL_MODE` says otherwise, a validator refuses a pair the service could not honour, `/version` reports the mode that passed, and every usage row carries it. Nothing in a request can change it. The second leg's material is already on every row and datapoint: the sparse vector lesson 1.3 computed and lesson 1.4 read back off the index. At query time the index scores it by dot product with the question's sparse vector, which is the sum, over the words the two share, of the two term-frequency weights. The ablation's harness never touches that vector: its sparse leg is BM25, built in memory from the rows' text. The cell runs both rulers over acme's current rows for a question you choose and prints where the right chunk lands under each.

#### The code

#### The bench's numbers, offline, for seven golden questions

Where each ruler placed the anchor among the 1,628 chunks of acme's mirrors, computed when this page was built. Yours, in the cell after the table, come from your rows.

#### Do it: both rulers over your rows, Rs 0

The cell reads the text of every current acme row, no vectors, and scores each row twice for the invoice question; then run it again for the notice-period clause. Firestore reads of this size sit inside the free quota.

To run the cell for another question, put the two variables in front of its first line, `Q="What is the notice period for a confirmed E3?" ANCHOR=NP-03 python - <<'PY'`, and paste the rest unchanged. NP-03 is the clause 2.1 cited; the index leg buries it under the same Act pages and BM25 puts it first, because "notice", "period" and "e3" are rare across the corpus and "the" is not.

The same rows were ranked by two rulers and the anchor's rank told the story. The first counted every shared word, so the pages with the most words won; the second weighted rare words and discounted long pages, so the one chunk with the invoice number won. The API's hybrid mode is built on the first ruler, and the ablation's hybrid arm on the second. Neither is wrong about what it measures; they measure different things, which is what step 6 has to be read with.

### Three ways through the index: dense, sparse only, fused

One question, one endpoint, three queries, and the lists saved for step 5.

#### Definition

`hybrid_find_neighbors()` is the whole production path. It encodes the question with the same sparse encoder the worker used, builds a `HybridQuery` from the dense vector, the sparse values and dimensions and `rrf_ranking_alpha`, puts the tenant restrict in the filter exactly once beside whatever the dense path sends, and asks the endpoint for one list. The fusion happens on the index, not in the API. Alpha 1.0 is the dense leg alone, alpha 0.0 the sparse leg alone, and 0.7 is what `_dense_retrieve()` sends under hybrid mode. Alpha 0.0 is the one value the function does not send: 0.0 is the wire format's empty value, so a query carrying it reaches the index with no alpha at all and comes back in the dense order, and the function asks for the sparse leg as a query with no dense vector instead. The cell embeds the question once, where the API embeds it, asks the index the three ways and prints where the anchor landed in each list; it saves the lists so step 5 can fuse them by hand.

#### The code

#### Do it: dense, alpha 0, alpha 0.7

Three queries went to one endpoint with the same tenant restrict. The dense leg found the invoice; the sparse leg alone did not, and its list was the long Act pages step 3 predicted, the same first three as step 3's first ruler; on acme's lane the two legs shared no chunk, so the fused list at alpha 0.7 was the dense list exactly, because a leg weighted 0.3 cannot lift an id the other leg did not hold. On a question where the legs do share a chunk, the fused list is the dense list with a few positions shuffled, and an Act page both legs held can move above the invoice: that is the lift working against you, and the arithmetic of it is next. Paste the dense list's five lines into the bench in step 1 and the RRF table becomes what the API would fuse. For a question whose exact token the corpus repeats rarely, set `Q` and `ANCHOR` and run the cell again; the anchor ranks are the measurement.

### RRF by hand: the kit's rule reproduces the server's order

The function, the bound that decides what a 0.3 leg can do, and the fused list checked against the index's.

#### Definition

`rrf_fuse(dense_ids, sparse_ids, alpha, k=60)` is eleven lines: two passes that add alpha / (k + rank + 1) and (1 - alpha) / (k + rank + 1) into one dictionary, then a sort. The same eleven lines sit in ablate.py as `rrf()`. Three numbers explain everything you saw in step 4. At alpha 0.7 the dense list's first id earns 0.01148, its twentieth 0.00875, and the sparse list's first id earns only 0.00492: a chunk the sparse leg alone found cannot outscore any chunk in the dense top twenty. What the sparse leg can do is lift a chunk both legs hold, for better or worse: with a ruler that likes long pages, the lifted chunk is often an Act page, and it can overtake an anchor the sparse leg never saw. When the legs share nothing, the bound decides the whole list: every dense id outranks every sparse id, and the fused twenty are the dense twenty in their order. The index fuses deeper lists than the twenty you fetched, so the tails of your fusion and the server's can differ; the heads should agree. The comparison proves something only if the two saved legs differ, so the cell prints that first: two copies of one list fuse into that list, and every check below would pass.

#### The code

#### Do it: fuse the saved lists, compare with the index's fused list

Eleven lines on your machine gave the order the index computed on its side, which is the claim in the function's docstring, checked. The two extreme alphas returned the legs unchanged, and the bound showed why a 0.3 leg is a tie-breaker rather than a second opinion: it can move a chunk both legs found, never one the dense leg missed. In the sample the legs shared nothing, so no line has a sparse rank and the fused twenty are the dense twenty, in order: the bound, seen whole. On a question where a line with a sparse rank sits above the anchor, that is the lift, and with this ruler it is usually an Act page: the sparse ruler's taste for long pages, applied at 0.3. If the first line printed says the legs do not differ, the sparse list you saved is the dense list again, and the checks under it prove nothing; update the kit and run step 4 again. Either is the honest result for that question, and the reranker in lesson 2.3 gets the whole pool either way.

### The ablation: one knob per arm, no model in the loop

Four arms, three numbers each, a miss list under every arm, and what the hybrid row does and does not say.

#### Definition

`evals/ablate.py` runs retrieval only, from outside the API, against the golden rows that carry `must_retrieve` anchors: 47 of the 65 rows today, 40 of them acme's, with 66 anchors of which 21 are clause codes. Each arm changes one thing: dense 5 with no reranker, dense 20 then rerank to 5, which is the lane's own recipe, dense 50 then rerank, and hybrid 20 then rerank. The dense leg of every arm is Firestore's `find_nearest` with the tenant filter, not the index; the hybrid arm's sparse leg is BM25 over the tenant's rows, fused with `rrf()` in-process at alpha 0.7. Beside every reranked number stands `recall@depth`, the reranker's ceiling, and under every arm the rows that cost a point say whether the anchor was ranked out or never retrieved. No generation call is made; the exit code is 1 only when an arm could not run a single row.

#### The code

#### Do it: a wiring check, then acme's rows with a ledger

The first run takes five rows and about a minute; the second takes acme's 40 rows and a few minutes, and appends one JSON line per arm to a ledger you keep. `make ablate` passes your exported `REGION` as the embedding region, which is where the API embeds; the direct call is the same line without make.

The kit's author measured this on 8 September 2026, over the 43 anchored rows the golden set had then: dense 5 alone 0.91 recall at 5 and 0.81 MRR; the lane's dense 20 then rerank 0.96 and 0.91; dense 50 then rerank 0.99 and 0.94 at four times the latency; and the hybrid row identical to the lane's row at alpha 0.5 and, on acme's rows, 0.7. Those figures are in the file's docstring, and they are the baseline your ledger line is read against.

Four recipes ran over the same rows and the same question set, and each was scored by whether the anchor came back, not by whether an answer sounded right, so nothing a model said could flatter a recipe. The hybrid row's honest reading is narrow: with BM25 as the sparse leg and Firestore as the dense one, fusing changed nothing at depth 20 on this golden set, because the dense leg already held the anchors and RRF at 0.7 could only reorder. It says nothing about the index's own sparse leg, which step 3 showed is a weaker ruler, and it says nothing about the API's wiring, which is step 7's business. The arm's label, "not wired", is the file telling you the same.

### The knob: hybrid on a candidate that takes no traffic, compared, then removed

A revision that answers on a tag URL and serves nobody, the same questions to both, and the variable taken back out.

#### Definition

`RETRIEVAL_MODE` is read once, at startup, and `check_retrieval_modes()` refuses the pairs the service could not honour before it serves a request: hybrid with a managed backend, hybrid with the Firestore backend. The way to judge a switch is the kit's own: a revision of `documind-api` deployed with `--no-traffic` and a tag, which gets a URL of its own and no traffic, while the live revision keeps serving. With `MIN_INSTANCES` at 0 an idle revision costs nothing. Two rules from the release lessons apply here. The identity token's audience stays the service's canonical URL whichever URL you call, so `tok "$API"` is right for the candidate too. And environment variables merge across revisions, so a variable set for one candidate would ride into the next one unless removed; the last block removes it and drops the tag.

#### The code

#### Do it: hybrid on a candidate, the same two questions to both revisions, then undo

A second revision of the API came up with hybrid on, answered on its own URL, took no traffic, and was asked the same questions as the live one. The citations are the reranker's choice from the pool, so hybrid can only change them by changing which twenty candidates arrive, not their order; where the citations agreed, the pool's membership was the same and hybrid changed nothing for that question, which step 5's bound predicted for a 0.3 leg over a dense pool that already held the anchor; where they differed, the difference is the finding, and the gate that decides whether it is a good one is lesson 7's, `make eval-live` against the candidate URL. Then the variable was removed, so the next candidate does not inherit it, and the tag was dropped. The next `make plan` may show the service template moved; `make up` puts it back.

### What hybrid costs, where it cannot go, and what the harness does not measure

The rupee line, the two places the mode is refused or degrades, and the column that lets a day of hybrid be compared with a day of dense.

#### What it costs

#### Where hybrid cannot go

Two places, one at startup and one at runtime. A managed backend has no sparse leg to fuse and the Firestore rung's vector index takes one dense vector and nothing else, so `check_retrieval_modes()` refuses both pairs before the service serves; a tenant pinned to a managed store under hybrid mode is served from the deployment's backend with a `retrieval_pin_ignored` line instead. At runtime the chaos rung applies to hybrid as to dense: an unreachable index degrades to the Firestore rung, which is dense only, with a `vector_search_fallback` line and never a 500. The cell asks the validator the two questions offline.

#### What the harness does not measure, and what the usage rows can

The ablation's hybrid arm is BM25 plus Firestore's dense rung, fused in-process; the API's hybrid mode is the hashed word-count leg plus the index, fused on the index. The 8 September result, hybrid identical to the lane, is a statement about the first pair. The second pair is judged on a candidate, as in step 7, and over time on the usage rows: every answer's row carries `retrieval_mode`, and the warehouse view groups by it, so a day served under hybrid can be set beside a day served under dense with the same columns lesson 11.5 reads. And when a better sparse ruler is wanted on the index itself, the encoder is the place: `SPARSE_ENCODER_VERSION` is stamped on every row, so a weighting with rarity in it is a reindex away, and lesson 1.6 showed what a reindex costs.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. Step 7 created two revisions of the API that took none and removed the tag and the variable again; the service's live revision never changed. The ablation left `~/ablate.jsonl`, one line per arm, which lesson 7 reads as a baseline. The bench in step 1 keeps whatever you pasted only until you leave the page. Lesson 2.3 takes the pool this lesson measured and studies the reranker that cuts it to the citations you see.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.2 Compare dense and hybrid retrieval · v5.0

Next: Lesson 2.3 Rerank and inspect retrieved candidates.
