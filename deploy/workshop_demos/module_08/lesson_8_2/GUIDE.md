# Lesson 8.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_8.2_Rechunk_Reembed_WIX.html`, reviewed at blob `5111868eecf916b3400fd9d5899661c81313622a`. Learners read that page on the course site; this guide keeps its prose.

The kit cuts every text document into chunks of up to 2,000 characters, and it says so in two places: once in the ingest worker, which cuts what the lane indexes, and once in the module the notebooks, the Rs 0 lane and the offline checks share. This lesson changes the chunk size and its overlap to 400/50 in both places, with a test that fails if only one is changed, and follows the change through a real deploy: a worker built under its own image tag, the handbook re-issued so the new rule cuts it, the counts of what was reused and what was embedded, the ledger walked against the bucket, the handbook's golden questions asked again, and the original image put back.

Two findings shape the practical. A chunk size of 599 characters or more changes nothing at all on the handbook, because no section in it is longer than that. And changing the rule re-cuts nothing that is already indexed: only a document the worker ingests after the deploy is cut by the new rule, which is why the handbook goes up again as new bytes.

- What changing a chunker changes, and what it does not

- The words: twins, pair, window, re-issue, tag, revision, drift

- Before you run anything: set up the shell

- The kit's code: two lines, one rule, and the test that holds them

- Measure before you deploy: the handbook at eight sizes, Rs 0

- Do it: edit both twins, then build and deploy a tagged worker

- Re-issue the handbook as new bytes, and read the counts

- REST: which image serves, and how many tokens a new chunk is

- Reconcile: the ledger against the bucket, the index against the rows, the golden rows

- Put it back: the original tag, version 1, the checkout

- Verify it yourself: the checklist

You will learn where the kit sets its chunk size (twice), why 400/50 re-cuts 272 of the handbook's 283 sections while any size from 599 up re-cuts none, and why a new rule reaches only the documents ingested after it. Then you will make the change on your lane under the twin test, re-issue the handbook, read 555 chunks, 11 reused and 544 embedded off the worker's line, reconcile the ledger to drift 0, ask the handbook's golden questions again, and put the original worker back.

### What changing a chunker changes, and what it does not

A rule set in two files, a section rule ahead of the size, and an index that only learns the rule one document at a time.

A chunker is the code that cuts a document into the pieces that are embedded, stored and retrieved. Lesson 1.2 read the kit's: a handbook is cut at its `##` headings, one chunk per section, and only a section longer than the chunk size is cut again, into overlapping windows that end on a sentence when there is one in the window's second half. Anything without headings is windows, page by page. Two numbers set the windows: `CHUNK_CHARS`, the most characters a window holds (2,000 today), and `CHUNK_OVERLAP`, how far back the next window starts (200). Changing a chunker, in this kit, means changing that pair.

The pair is written down twice. `services/ingest/main.py`, the worker, cuts every document the lane indexes. `shared/documind_corpus.py` cuts the same documents for everything that runs outside the worker's image: the notebooks that seed a Colab lane, the Rs 0 lane on a laptop, the offline checks, and every lesson page that counts chunks when it is built. The image cannot import a notebook and a notebook cannot import the image, so each carries its own copy, the twins, and each says it follows the other. If only one is edited, the lane serves chunks that no offline count, check or estimate has ever seen, and nothing fails. The kit's twin test, `commands/tests/test_twin_chunker.py`, is what fails: it holds the two pairs equal and the two chunkers to the same chunks over the whole corpus.

The size is the second rule, not the first. Sections come first, so a size only matters for sections longer than it. The handbook has 283 chunks today: a short preamble and 282 sections. Of the sections, ten are the clauses the course keeps asking about (`NP-03`, `PB-02`, `LV-01`, `LV-07`, `EXP-12`, `PR-05`, `IT-SEC-04`, `SEC-09`, `FIN-02`, `WFH-01`), none longer than 234 characters. The other 272, `GEN-000` to `GEN-271`, are the handbook's generated filler, 563 to 599 characters each. The longest section of all is 599 characters, so any size of 599 or more leaves every section whole: the same chunks, the same hashes, the same vectors, nothing to embed. The cohort plan's "600 or more changes nothing" is true, and the exact line is 599. At 400/50, every generated section is cut in two and every real clause stays whole: 555 chunks, of which 11 are the very texts the lane holds now.

Last, and easiest to miss: a new rule re-cuts nothing that is already indexed. The rows in Firestore and the vectors in the index were cut when each document was ingested, and the worker cuts again only when a document arrives. So the practical is a deploy (the rule), a re-issue (the one document you want re-cut, as bytes the lane has never seen), a reconcile (the ledger still names what the bucket holds), a gate (the golden questions about that document), and a way back. The kit has no command that re-cuts a whole corpus; `INDEXING.md` lists a full re-embed under "Not yet".

A coaching centre in Kota re-cuts its revision cards. Every chapter of every textbook is printed onto revision cards, each card filed in a catalogue students search. The press has two rules: a topic becomes one card, and a topic too long for a card is cut onto overlapping cards. Head office decides cards should be smaller. Three things follow. The short topics already fit, so their cards come out word for word the same and keep their place in the catalogue; only the long topics are re-cut, and the indexer bills only for those. Nothing already in the drawers changes: only a chapter sent to the press after the decision comes out on new cards, so the centre sends again the one chapter it wants re-cut. And the centre has two presses, one at head office and one at the branch that prints the practice sets: if only one press gets the new card size, the practice sets point at cards head office never printed. Every night a clerk checks the register of chapters against the shelves.

The two presses are the twins and the card size is the pair. The short topics are the handbook's ten real clauses and its preamble, kept with their vectors; the long ones are the 272 generated sections, embedded again. Sending a chapter again is the re-issue. The night clerk is the reconcile: she counts chapters and their editions, not card sizes, so she finds nothing wrong either way, which step 8 shows.

#### The explorer: the handbook at another size

The explorer runs the kit's chunker in your browser, ported line for line from `shared/documind_corpus.py`; when this page was built, the same script cut the whole handbook at every size and overlap below and matched both twins' chunks exactly. Move the size and the overlap. The line under the controls is the whole handbook against what your lane holds today (version 1, cut at 2000/200): how many chunks, how many keep their vectors, how many are embedded again, and what that costs at the embedding price lesson 8.3 dates. The cards are one section's chunks at the chosen size: teal kept its vector, amber is new text, and blue is the overlap a window repeats from the one before it.

At 400/50 the handbook makes 555 chunks (283 at the kit's 2000/200). 11 keep their vectors and 544 are embedded again: 1,70,348 characters in 4 requests, about Rs 0.36. 272 of the 283 sections are cut, and the largest chunk is 368 characters.

The sizes stop at 250, 300, 400, 500, 598, 599, 600, 800, 1000, 1500 and 2000 characters; an overlap of half the size or more is not offered, because the window would creep forward a character at a time. Rupees are for the characters sent to `text-embedding-005` and nothing else; step 8's table has the re-issue's other costs. 41 size and overlap pairs were checked against the kit when this page was built.

The explorer opens at 400/50 on `GEN-003`, the longest section: two windows, the second starting a few words before the first ends, both amber. Choose `NP-03`: one teal card, the same 234 characters the lane holds, so the worker will lend it the vector it already has. Now drag the size up. At 500 the count is still 555, because every generated section is still longer than the size. At 598 only the fifteen sections of exactly 599 characters are cut, 30 chunks to embed, the cheapest real change there is; at 599 every section is whole again and the line says every chunk is reused. And try the overlap at 400/50: it changes what the windows repeat and how many characters you pay for, not how many windows there are.

### The words: twins, pair, window, re-issue, tag, revision, drift

Twelve terms, each with the value it takes on your lane in this lesson.

Two pairs of words are easy to confuse. A re-issue is new bytes under an old name, which the worker always processes, while the undo of lessons 1.6 and 1.7 is old bytes again, which the worker answers by flipping retired rows back with nothing cut and nothing embedded. And an image tag is a name that can be moved, while a revision is fixed: step 5 gives the edited worker a tag nobody else uses, so that step 9 can trust the original tag to mean the original image.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 6 uses both: the shell re-issues the handbook, and your browser reads what the worker made of it.

### The kit's code: two lines, one rule, and the test that holds them

Where each twin sets the pair, the one function that uses it, and the test that fails when the twins disagree.

#### Definition

The change this lesson makes is two lines long. The worker sets its pair at the top of `main.py`, beside a comment that still numbers the lesson the way the notebook course did; its twin sets the same pair inside the block the notebooks paste verbatim, with a comment pointing back at the worker. Nothing else in either file holds a size: every other number in the chunker is derived from these two.

Both numbers are used in one function, `_windows()` in the worker and `windows()` in the twin, line for line the same. A window runs from `start` for `CHUNK_CHARS` characters; if text remains after it, the window is pulled back to the last sentence end in its second half, if there is one; the next window starts `CHUNK_OVERLAP` characters before this one ended. A text no longer than `CHUNK_CHARS` is one window, whatever the overlap, which is the whole reason the handbook stops changing at 599.

The twin test reads each file's pair line with `ast`, so it reads what the file says, not what an earlier import left in memory, and it fails with both lines named. Its other half runs both chunkers on the same texts, every Markdown text under `evals/corpus/` at the kit's pair and at 400/50, and holds them to the same chunks. Two differences are the kit's own, written into the worker on 12 September 2026, and the test pins them rather than ignoring them: the worker leaves `page_start` empty where a text names no page, and it calls the windows of a text with neither headings nor form feeds `w0`, `w1`, where the twin says `p1-0`, `p1-1`.

#### Do it: the twin test on the kit as it is, Rs 0

From the kit, with nothing changed. The `grep` keeps the lines that matter: each failure's name and message, the count and the verdict.

Eleven tests ran in seconds with nothing installed but Python: the two pair lines agree, the section and clause-code patterns and `chunk_hash()` agree, both twins cut the whole corpus into the same chunks at 2000/200 and at 400/50, they agree on thirteen awkward texts at six pairs, and the test's own edit of either file in memory is caught. The same test runs in the kit's CI on every pull request, and in the learner repository's after every publish. Step 5 runs it after each edit you make.

### Measure before you deploy: the handbook at eight sizes, Rs 0

What a re-issue at each pair would cut, reuse, embed and cost, computed with the kit's own chunker before anything is built.

#### Definition

What a re-issue will embed is decided by text alone, so it can be measured before any deploy. The worker reuses a vector when a new chunk's `chunk_hash` matches a current row of the same document (lesson 1.3), and the current rows of the handbook are version 1 cut at 2000/200. So: cut version 1 at the kit's pair, cut it again at a new pair, and every new chunk whose hash is not among the first set is one the worker will embed. The cell below does exactly that with `shared/documind_corpus.py`, setting the pair in memory so the files on disk stay as they are, and it batches the misses with the kit's own `embed_batches()` to count the requests. The price is `text-embedding-005`'s online rate, USD 0.000025 per 1,000 characters, at Rs 85 to the dollar, as lesson 8.3 dates it.

#### Do it: the handbook through the kit's chunker

Read the table from the top. At 2000/200, 599/50 and every size between, the handbook is the same 283 chunks: a re-issue would embed nothing, which is the cohort plan's "600 or more changes nothing", with the line at 599. One character less and the fifteen sections of exactly 599 characters are each cut in two: 30 chunks to embed. At 400/50 the cut runs through all 272 generated sections and stops short of every real clause, because the longest real clause is 234 characters: 555 chunks, 11 reused, 544 embedded, 1,70,348 characters in four requests, Rs 0.36. Only a size under 234 would cut a real clause, which is why 300/50 still reuses the same 11.

The Acts are not in the table on purpose. They went up as PDFs, and the worker cut Document AI's text of them, not the pypdf text on your disk: lesson 1.2 found the Code on Wages at 67 windows on the lane and 65 offline. A re-issued Act's counts can only be read off the lane. The handbook is Markdown, read as it is, so its counts are exact before the deploy.

### Do it: edit both twins, then build and deploy a tagged worker

One twin first, to see the test fail; the other; then a Cloud Build under a tag nobody else uses, and one deploy.

#### Definition

The edit is one `sed` line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again.

Three tests fail, and the first message names both files and both pairs. The second says what the mistake would do to the lane: `acme/cgst_act_2017.md`, cut into 1,536 chunks by the worker and 390 by everything offline. The third is the pinned difference, now three windows against one. Now the twin:

Green again, and `git status` lists the two files you changed: your checkout now differs from the kit in exactly those two lines. Step 9 puts them back. The next session's setup block would refuse to pull over them, as its notes say, so do not leave them.

#### The tag, and the build

The worker on your lane runs the image a build pushed under a tag, and the tag is `GIT_SHA`: by default the checkout's commit, read with `git rev-parse`.

Your edit did not make a commit, so a build with the default tag would push the edited worker under the commit's own tag, as if it were the kit at that commit. When that commit is the one the running worker was built from, the edit replaces the original image under its own name, and a later "redeploy the original tag" deploys the edit. The cell below therefore reads the tag the worker runs now, keeps it in `~/lesson82-orig-sha` (written once, so running the cell again cannot overwrite it), and builds under that tag plus `-c400`. It names the service and the deploy script on purpose: without `SERVICES=ingest` the build is every one of the seven images, and without `SCRIPTS=commands/lesson-12.5.sh` the deploy is every service, all under a tag only the worker has. The build's own lines go to a log; the `grep` shows make's `>>` lines, the deploy's result and any error.

Cloud Build built the worker from your checkout, the two edited lines included, and pushed it as `ingest:COMMIT-c400`; `deploy-services` ran the worker's deploy block from `commands/lesson-12.5.sh` with that tag, and Cloud Run made a new revision and sent it all the traffic. The last line is the service's own record of both. Every document the worker ingests from now on is cut at 400/50. Nothing already indexed has changed: the handbook in Firestore and in the index is still version 1, cut at 2000/200.

### Re-issue the handbook as new bytes, and read the counts

Version 1's text behind one comment line: a new version for the ledger, the same text for the chunker.

#### Definition

The new rule needs the handbook to arrive again, and how it arrives decides what happens. The same bytes as version 1 would be a duplicate: the worker finds the claim it already holds and acks the event, cutting nothing. The bytes of any version retired in the last 30 days, revision 3 from lesson 1.6 or revision 2 from lessons 1.3, 6.3 and 11.4, would be the undo: the worker flips the retired rows back, still cut the old way, and embeds nothing. So the re-issue is version 1's text with one line in front of it, an HTML comment. The bytes are new, so the version key is new and the claim is won. And both twins drop a leading comment before they cut, the way they drop a mirror's provenance header, so the chunks are exactly version 1's text at 400/50: the counts measure the chunker and nothing else.

The worker then lends vectors. A new chunk borrows a current row's vector only when its hash matches and the row's embedding was made the way the worker makes one now: the same model, version and task type.

#### Do it: write the new bytes, then re-issue

`make reindex` is lesson 1.6's release command: the offline gate scoped to the handbook, the upload under the handbook's name, whose event reaches the worker by the push lesson 8.1 traced, and the wait for the worker's line.

Expect the version keys `acme_48f9a1d2929b...` and `acme_497809ffbaa6...`, the upload, and then the worker's line: `ingest_ok`, the new key, 555 chunks, 11 reused, 544 embedded, 283 retired, and no effective date, since version 1 declares none. Then the retired line names version 1's key, its 283 chunks and 30 days to expiry. Step 4 predicted every one of those numbers.

#### See it in the UI

Open the DocuMind UI signed in as yourself and choose Documents. Under Versions, the handbook's row reads `chunks` 555, `reused` 11, `embedded` 544, `retired` 283, with the time it was indexed and the managed stores that hold its text in `held in`. Every other row is as it was: those documents were not re-issued, so they are still cut at 2000/200. The shell put the bytes in the bucket as the operator; your browser read the ledger through the API as a member of acme's roster.

The worker claimed a version it had never seen, cut it at 400/50, found 11 chunks whose text version 1 already holds (the preamble and the ten real clauses), copied their vectors, and sent the 544 windows of the generated sections to the embedding model in four requests, about Rs 0.36. It wrote the new version staged, swapped it current, retired version 1's 283 rows with 30 days to live, upserted the new datapoints and removed the retired ones, and the managed mirror sent the text to acme's stores, which cut it by their own rules. Nothing was deleted: version 1 is one upload away, which step 9 uses.

### REST: which image serves, and how many tokens a new chunk is

Two GETs on the Cloud Run Admin API, then one embedding request read for what the model counted.

#### Definition

`gcloud run services describe` printed one line in step 5. Underneath it is the Cloud Run Admin API, and its service resource says more: the image in the service's template, the newest revision that is ready, where the traffic goes, and, one call further, every revision the service has kept with the image each one runs. Step 9's revert deploys one of those images again, so read them now, while the edited worker serves.

Expect the template's image to be `ingest:COMMIT-c400`, the latest ready revision to be the one step 5's deploy made, and all the traffic on it (Cloud Run reports the share that follows the newest revision as `latest`). Below, the newest three revisions with their creation times: the `-c400` one on top and the original image under it. The original revision is still there, but traffic follows the newest ready one, and step 9 makes a newer one rather than routing back to an old one by name: a route to a named revision would pin the service there, and every later deploy would land with no traffic.

#### The tokens in the largest new chunk

The kit counts characters: the window is 400 characters, and the batcher estimates tokens as characters divided by 3. The embedding model counts tokens, and reads at most 2,048 of one text, cutting the rest unless told not to (lesson B.2 read that on Google's page on 7 October 2026). The largest chunk at 400/50 is `GEN-003`'s first window, 368 characters. The cell cuts the handbook at 400/50 in memory, finds that window, and sends it to `text-embedding-005`'s REST endpoint in `us-central1`, as the worker's client would, under the worker's task type. The response carries the model's own count beside the vector.

Expect `GEN-003: 368 characters; the kit's estimate 122 tokens`, then the model's count, `truncated False`, 768 numbers, and the characters it billed. The model's count is the true one; the kit's estimate counts cautiously, three characters a token, so a batch stays under the request's token ceiling. At 2000/200 a window could hold five times as much, still far under 2,048 tokens. The smaller pair does not change what the model can read; it changes how much of a section each vector has to stand for. One request, 368 characters: 0.08 of a paisa.

### Reconcile: the ledger against the bucket, the index against the rows, the golden rows

The walk that finds a lost event and cannot see a chunker, the rows read directly, and the handbook's ten questions asked again.

#### Definition

Lesson 1.8 ran the nightly walk: every object in the bucket against its ledger row in `sources/`. For each object, a generation the ledger already holds is `ok`; any other generation has its bytes hashed, and the hash decides. The bytes the ledger already names are a `touch` (record the generation, index nothing); bytes a claim indexed that the ledger never recorded are a `backfill`; bytes no claim holds are a `reingest`, which rewrites the object onto itself so the worker's own path runs again. Drift counts the sources the ledger had wrong.

Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life:

The second night is the case the walk exists for: had the re-issue's push been lost, the ledger would still name version 1 at generation 2, the walk would hash generation 3, find bytes no claim holds, and rewrite the object so the worker indexes it, cut by whatever pair the worker runs that night. The same bytes can be cut two ways depending on when they arrive. Now the real walk, the plan only, and the versions view after it:

Expect one `{"reconcile": ...}` line for each object that is not `ok`: the note lesson 8.1 withdrew, if you ran its last step, as `withdrawn` with the reason "withdrawn, object kept", which is a decision, not drift. Then `reconcile_done` with `"applied": false`, the counts, and `"drift": 0`. In the versions view, the handbook's row reads 555 chunks, 11 reused, 544 embedded, 283 retired. The other Markdown rows have not moved, and they show the limit of everything above: they are still cut at 2000/200, and no walk will ever say so.

The lane's rows carry the embedding model and its version, but no field names the chunker. After a change, the way to find a document cut by the old rule is its `chunks` beside an offline count at each pair, which works for Markdown and not for a PDF.

#### The rows and the index, read directly

The ledger row is a summary. The rows are the evidence: the cell counts the handbook's rows by version and state, finds the longest current row, and checks whether two current rows hold version 1's vectors: `NP-03`, which the new rule left whole, and `GEN-003`, which it cut. Then it counts every tenant's current rows in Firestore and reads the Vector Search index's own count.

Expect the new version current with 555 rows and version 1 retired with 283, beside any older version whose 30 days have not run out; the longest current row at 368 characters; `NP-03`'s current hash equal to version 1's and `same vector: True`, because the worker copied it; `GEN-003`'s different, `same vector: False`. The index's count should equal Firestore's current rows once the stream has caught up, which takes a few minutes after an ingest. A source withdrawn by hand, or retired by the walk when its object left the bucket, leaves the index too since 13 October 2026: the rows are retired, the managed stores told, and the retired ids removed with the worker's own `remove_datapoints()`, as the kit's code shows. Before that date only the worker's swap and undo removed them, so on a lane that withdrew or retired a source on an older kit, lesson 8.1's note among them, the count can still be higher by that source's chunks.

The retriever drops such a leftover datapoint after the search, because its row is no longer current, so answers stay right; but the count is not the ledger's, and the walk does not compare the two.

#### The gate: the handbook's golden rows, asked again

The re-cut changed 544 vectors in the same index the questions search, so lesson 1.6's live gate, scoped to the handbook, is the check that matters. Every one of the ten rows asks about a real clause, and every real clause kept its text and its vector: what moved is the 544 windows of generated text beside them, now shorter and more numerous. The gate says whether the clauses still win.

Expect the scope line, `10 row(s) cite it`, the thresholds, the shape table and the latency line, then either `All thresholds met.` or the rows that cost a point. Set the run beside lesson 1.6's green run on version 1: the same 10 questions, the same clauses, a different neighbourhood. A row that now misses names the clause a window of filler displaced, which is the real cost of a smaller chunk on this handbook. With acme pinned to the kit's index, as the setup section asked, these answers come from the rows you just made; on RAG Engine they would come from text the store cut at 512 tokens with 100 of overlap, by its own rule, and this lesson's change would not reach them.

### Put it back: the original tag, version 1, the checkout

One deploy with no build, one upload the worker answers with an undo, and two files checked out again.

#### Definition

The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle.

Expect `back to ingest:COMMIT`, the deploy's lines, the service's image back at `ingest:COMMIT` on a newer revision, and then `make reindex`'s line: `ingest_reactivated`, version 1's key `acme_497809ffbaa6...`, 283 chunks, 283 reused, 0 embedded, 555 retired. Last, the checkout. The test runs once more so the kit you leave is the kit the course ships, and passes:

The worker is the original image again, on a new revision, and the handbook is version 1 again, reactivated: its rows were never deleted, so nothing was embedded, and the new version's 555 rows are retired with 30 days to live. Your checkout matches the kit, line for line, and the twin test says the twins agree. The change, the re-embed, the reconcile and the revert each left a record: the revisions, the ledger's rows and claims, and the worker's lines.

### Verify it yourself: the checklist

Ten checks, each one step above, each with what a pass looks like on your lane.

`documind-ingest` runs its original image again, on a revision two newer than the one you started with; the `-c400` image stays in Artifact Registry, under its own tag, until you delete it. The handbook is version 1 again, reactivated once more; the re-issued version's 555 rows are retired, with their 544 fresh vectors, and the retention policy removes them 30 days from now. The BigQuery mirror gained 555 rows and the managed stores followed both swaps. Your checkout is the kit again. Your home directory holds `hr_policy_2026_r4.md`, `lesson82-orig-sha`, `lesson82-build.log` and `lesson82-revert.log`; delete them when you are done. Put acme's pin back with the setup section's second window.

Netsetos GenAI on GCP · Module 8 Ingestion practical · Lesson 8.2 Change a chunker, re-embed and reconcile · v5.0

Next: Lesson 8.3 Size RAG for ten million documents.
