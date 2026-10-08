# Lesson 0.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_0.2_Local_Environment_WIX.html`, reviewed at blob `8085442943c65c12c22f9b8bcad6a06e9f4e71bc`. Learners read that page on the course site; this guide keeps its prose.

Every later lesson starts from the same place: a terminal on your machine, the kit cloned into ~/deploy_module_rag, and its Python in ~/rag-shell-venv. This lesson builds that place and then uses it. You will read the master diagram of DocuMind's two workflows, run the chat service on your laptop with a local model and no cloud at all, and ask it the notice-period question: the answer comes back with citations, for Rs 0. Then you will run the kit's offline gate, watch it pass, loosen one row of the golden set the way a hurried engineer would, read the failure it prints, and repair it.

- What DocuMind is: two workflows on one map

- The words: clone, venv, lane, profile, golden row

- Before you run anything: install the tools, clone the kit, make the venv

- What the clone holds: the kit, the corpus and the golden set

- The Rs 0 lane: the notice-period question, with citations

- Prove a first success: make dryrun

- Diagnose a first failure: one loosened row

- The same gate in CI, and the shell every later lesson opens

- Verify it yourself: the checklist

You will set up the operator shell every later lesson starts from and read DocuMind's two workflows on the master diagram. Then you will prove two things on your own machine for Rs 0: the local lane answers the notice-period question with citations, and `make dryrun` goes green, goes red on one loosened golden row with its reason, and goes green again.

### What DocuMind is: two workflows on one map

The system this course builds, the two journeys through it, and the box each module opens.

DocuMind is a document-question service for companies, and it is the system every lesson of this course builds, runs and changes. A company, a tenant, uploads its documents: an HR handbook, contracts, an invoice, and the Acts of Parliament it has to comply with. The kit ships 3 tenants, `acme`, `zeta` and `globex`. Their employees ask questions in plain words, such as "What is the notice period for a confirmed E3?", and the answer quotes the clause that decides it and names the document and the page it came from. Two promises hold the design together: every answer cites its evidence, and no tenant ever sees another tenant's documents.

Everything DocuMind does is one of two journeys. An upload becomes searchable rows: the file lands in a bucket, an event wakes a worker, and the worker reads the file, cuts it into pieces and writes the pieces to the stores. A question becomes an answer: the UI sends it to the API, the API decides who is asking and for which tenant, the retriever finds the pieces that match, and the generator writes the answer from those pieces alone, citing them. The stores are where the two journeys meet: the worker writes there, the retriever reads there.

A restaurant kitchen with two doors. Deliveries come in at the back: each crate is checked for whose order it is, cut, labelled with the shelf it goes on, and put away in the cold rooms. That is the upload journey: bucket, worker, stores. Orders come in at the front: the host checks the booking, the cook takes only from that customer's shelves, plates the dish, and the bill names the shelf every item came from. That is the question journey, and the bill is the citation.

Two more rooms belong to this lesson. The test kitchen at home uses the same recipes on a small stove and a home fridge stocked with the same labelled cuts: worse food, no rent. That is the Rs 0 lane, the same chat service on your laptop with a small local model. The inspection before opening checks the kitchen without cooking a meal, and it also checks the inspector's own sheet: a line that says "fridge: cold" with no temperature written down can never fail, so it is refused. That is `make dryrun`, and the refused line is the failure you will cause in step 6.

#### The master diagram

The two journeys, drawn with the kit's own names. Every later module opens one or more of the boxes: pick a module to light them and to list its lessons. Pick Your laptop today to see what this lesson runs: `make chat-local` starts the same chat service on your machine with a local model and a local store, so a few boxes run, or are stood in for, at no cost. Everything else waits for the lane that lesson 0.3 deploys on your Google Cloud project.

Every name is read from the kit when this page is built: the 7 Cloud Run services `make up` deploys (the Makefile's `SERVICES`), the bucket and the topic (`terraform/storage.tf`, `terraform/eventarc.tf`), and the 4 stores the API can answer from (`RETRIEVAL_BACKENDS` in `services/rag-api/config.py`). M1 on a box means Module 1 lights it; pick a module to see its lessons.

Arrows are the order a request travels. The tags under a box (M1, M8) are the modules that change or measure it, and the lessons that do it are listed when you pick a module. The diagram is not the resource map: it leaves out the service accounts, the secrets, the network and the budget, which the resource map of lesson 0.3 shows.

### The words: clone, venv, lane, profile, golden row

The words this lesson uses, each with the value it has on your machine by the end of it.

Two of these words carry the rest of the course. The clone is why a kit update is one `git pull` and a mistake is one `git checkout`. The profile is why the chat service you run for Rs 0 today is the same code lesson 0.3 deploys and Module 5 takes apart: one switch changes the model and the store, and nothing else.

### Before you run anything: install the tools, clone the kit, make the venv

From Module 1 on, every lesson opens with a setup block that assumes the shell this lesson makes, so this lesson has no setup to borrow: you build it here, once. Everything on this page runs in a terminal on your own machine: Linux or macOS, or Windows through WSL 2 with Ubuntu, because the kit's Makefile and shell scripts run on Linux. The blocks are bash; macOS opens zsh, so type `bash` first. Nothing on this page signs in to Google Cloud, creates a resource or costs anything.

#### The tools, and why the kit needs each

Install what is missing, open a new terminal so its PATH is fresh, and check. Each tool should print a path; the versions below the paths are the second check, against the table.

#### The clone, the venv and the install

Then make the operator shell. The block below clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag` the first time and pulls the latest kit every time after. It makes `~/rag-shell-venv` with Python 3.12 once, and activates it. Then it sources the kit's restart helper, `commands/session-restart.sh`, which only defines functions, and calls two of them: the first installs the operator packages and checks them, the second checks Terraform. Paste it whole.

Every line of the block is safe to run again, and that is how you restore the shell in a new terminal: run it again, and it pulls, activates and re-checks instead of installing from scratch.

What the install is, in the kit's own code: the 4 requirement files the operator commands use, plus numpy and rank-bm25, installed into the venv's own Python. Then `rag_check_python_dependencies` holds every installed version to its pin (31 packages), imports 28 modules the operator's commands and cells use, and runs `pip check`. It signs in to nothing; its last line says cloud access is checked separately, and lesson 0.3 is where.

Before installing anything, it checks the interpreter: Python 3.12, inside `~/rag-shell-venv`, first on the PATH. A venv made by another Python stops here, with the reason.

`MISSING` in the tool check: install that tool, open a new terminal, and run the check again; only `docker` may stay missing. `python3.12: command not found`: Python 3.12 is not installed, or not on the PATH; older Ubuntu releases do not carry it, and python.org has installers. `ensurepip is not available` on Ubuntu or Debian: run `sudo apt install python3.12-venv`, move the half-made venv aside with `mv ~/rag-shell-venv ~/rag-shell-venv.old`, and run the block again. `type: bad option: -P` or `[[: not found`: the shell is not bash; run `bash`, then the block again. `STOP: the required Python 3.12 virtual environment is not selected`: the venv was made by another Python; move it aside the same way and run the block again with `python3.12` installed. `STOP: operator Python dependencies are incomplete or inconsistent`: the lines under it name each package, and the cause is usually a pip error further up, most often a lost connection; fix that and run `rag_install_python_dependencies` again. `STOP: Terraform is not installed or is outside PATH`, or a version check failure: install Terraform 1.9.0 or newer and run `rag_require_terraform` again. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited here: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into your terminal, whole, and run; the Python cells are wrapped in `python - expected, is text to read: the kit's own code, or the output you should see. Those carry the read-only badge and no copy button. An expected window says where its output came from: the build of this page, which ran the command on the kit itself, or the author's laptop, for the outputs only a machine with Ollama can print.

#### make, or the commands it runs

This lesson uses two make targets, and each is a few lines you can read in the `Makefile` and run without make: `make chat-local` is two commands (step 4), and `make dryrun` is three (step 5).

### What the clone holds: the kit, the corpus and the golden set

Where things are, the documents both lanes answer from, and the rows that judge the answers.

The clone's root is the kit. These places matter from the first day:

#### The corpus: 3 tenants, 13 real documents, invented identifiers

`evals/corpus/` has one folder per tenant. Each tenant's synthetic documents are its own, and their figures differ on purpose: acme's handbook gives a confirmed employee 60 days' notice, zeta's gives 30, and globex has no handbook at all, so an answer borrowed from the wrong tenant is visibly wrong. The real documents are 13 texts of Indian law, 12 Acts and Codes of Parliament and 1 ministry handbook, downloaded from their publishers' own sites and checked by hash (`evals/real_sources.json`). They are held unequally too, so that a leak from one tenant to another would show.

The chunks column is what the Rs 0 lane would hold for each tenant, 2,757 in all, counted by the build of this page with the kit's own loader. Step 4 seeds acme's. The real documents, and what a laptop can read of each:

The invoice's identifiers are invented. It carries a PAN, `AAAPZ1234C`, a GSTIN, `27AAAPZ1234C1ZV`, and a mobile number, `+919876543210`: format-valid, so the personal-data scans that Module 4 exercises fire on them, and invented, as the invoice's own first line says, so nothing real reaches a shared screen.

#### The golden set: the rows that judge every answer

`evals/golden.jsonl` holds 65 questions, one JSON object per line, each saying what a right answer must contain, which clause it must retrieve, and whether the corpus can answer it at all: 34 lookups, 11 joins across two clauses, 8 refusals, 11 isolation rows that ask one tenant about another's documents, and 1 version row. One of them is this lesson's question:

`must_contain` is the figure a right answer must hold, 60. `must_retrieve` names the clause, NP-03, and its document. Step 4 asks this question of the Rs 0 lane; step 6 loosens this row and watches the gate refuse the change.

### The Rs 0 lane: the notice-period question, with citations

The same chat service with a local model and a local store: the make target, the kit's code, the REST call, and a direct read of the store.

DocuMind's chat service reads one switch, `DOCUMIND_PROFILE`. Set to `gcp`, the default, it calls Gemini on Vertex AI and retrieves through the deployed API. Set to `local`, it calls a model on your laptop through Ollama and reads a Chroma directory on your disk. Nothing else changes: the same agent code, the same `retrieve()`, the same answer shape. That is the Rs 0 lane. It is not as good as the lane, since a 4B model, as `profile.py` calls it, is not Gemini, and that is not its job. Its job is to show you a broken prompt, tool or schema on your laptop, with no project, no IAP and no bill.

The local half of each builder: `ChatOllama` with `gemma3:4b` at temperature 0, and a Chroma collection, `documind_dev`, at `./documind_chroma`, whose embedding is a deterministic fake. The comment says what that costs: a fake embedding ranks arbitrarily, so the local `retrieve()` does not rank by it at all, as you will see below.

#### What make chat-local runs

Two commands. The first seeds the store: `python -m shared.local_corpus acme` writes every chunk of acme's corpus into the Chroma directory, and Chroma replaces a chunk that has the same id, so running it again is harmless. The second starts the chat service under uvicorn on `127.0.0.1:8081`, from `services/chat`, with the kit's root on `PYTHONPATH` so that `shared/` imports.

The seed uses the notebooks' loader, `shared/documind_corpus.py`. It reads each document's text (a Markdown file as it is, a PDF through the text mirror `evals/fetch_real.py` extracted beside it), cuts it by the kit's two rules, one chunk per `##` section or 2,000-character windows within a page, and names each piece the way the notebooks' Firestore seed names it: `acme:hr_policy_2026#NP-03`. The deployed worker, which Module 1 opens, cuts by the same rules but names a piece by its version, `acme:#`, and reads a PDF with Document AI instead of the mirror, so its pieces of a PDF can differ; lesson 1.2 compares the two. For acme the seed writes 1,628 chunks from 17 documents: the 12 real documents with a text layer, and 5 synthetic ones. The scanned POSH Act has no text a laptop can read; only the lane's OCR reads it.

#### Install the lane, once

The lane gets a venv of its own, `~/rag-local-venv`. Its packages are the chat service's, LangChain, LangGraph, Chroma and the Ollama client among them, installed on top of the service's image pins as `services/chat/requirements-local.txt` asks. Keeping them out of `~/rag-shell-venv` leaves the operator pins exactly where `rag_check_python_dependencies` expects them, and every later session runs that check; the kit's CI keeps the chat service's pins in a venv of their own for the same reason. Then Ollama pulls the model, once.

#### Start the lane

Start it in the second terminal, so the first stays free for questions. One line in this block matters more than it looks. The recipe seeds from the kit's root and serves from `services/chat`, and the store's default path, `./documind_chroma`, is relative, so the two commands would open two different directories: the service would find an empty store and answer `local corpus is empty`. Exporting one absolute path as `DOCUMIND_CHROMA_DIR` gives both commands the same directory.

The first line is the seed's: `seeded 1628 chunks for tenant 'acme' into the local store`. The build of this page ran the same module on the kit, with Chroma stood in, and it printed the same line. uvicorn's lines follow it: the service is up, listening on your machine only.

#### Ask it

From the first terminal. The health check first: it names the profile, and the brains this service can run.

The service has 4 brains (`langchain`, `langgraph`, `adk` and `direct`), and `langchain` is the default: a tool loop in which the model decides when to search. This lesson asks the `direct` brain, which has no loop at all: one `retrieve()` for the top 5, then one call to the model with those quotes as its only context. It does not depend on a small model choosing the right tool, which the comment in `profile.py` warns it sometimes will not. Module 5 compares the brains.

Three things to read. The answer is `gemma3:4b`'s own words, so yours may be phrased differently, but it should say 60 days, the figure `lk-06` demands. The citations are not the model's: they are what `retrieve()` found, the same 5 on every machine, with `acme:hr_policy_2026#NP-03` first. And the turn cost Rs 0.0: `shared/prices.py` prices every call on the local profile at zero.

#### Under the call: the kit's code

Three pieces of the kit answered that call. The chat endpoint decides the tenant first. On the local profile there is no IAP and no roster, so `LOCAL_TENANT`, acme unless you set it, stands in:

The direct brain makes one `retrieve()` and, because the local lane has no generator behind it, one grounded call to the profile's model, with each quote numbered as a source:

And the local half of `retrieve()` reads every chunk of the tenant from the store, by a filter on `tenant_id` and with no embedding involved. It ranks them with BM25 over the question's content words, keeps the top 5, and applies a gate: if those do not cover at least half of the question's information, the honest answer is nothing, as production's would be.

For this question the content words are `confirmed`, `notice`, `period`, and 556 of acme's 1,628 chunks share at least one of them. NP-03 holds all 3 in 42 words and scores 1.000. The other 4 are long statute windows, 242 to 358 words each, and 3 of them match `confirmed` only through the lane's five-letter prefix rule, on words such as `confiscation` and `confinement`. That is lexical ranking: the clause comes first, and the rest share letters rather than meaning. The model is told to answer only from the quotes, and the quote it needs is the first.

#### Stop the lane, then read the store directly

Press Ctrl+C in the second terminal. The directory stays on disk, and a Python cell can open it the way the service does, with the same `build_store()` and the same `retrieve()`:

The count is acme's corpus, the metadata is what the citation was built from, and the 5 citations are the ones the answer carried, with NP-03's text below them: 60 days for a confirmed employee at grade E3 or above.

It has no UI, no upload path, no API and no worker: the client is curl, and the corpus arrives by seed. It has no identity: `LOCAL_USER` and `LOCAL_TENANT` stand in for IAP and the roster, which is why it listens on `127.0.0.1` and nowhere else. It has no embeddings: BM25 ranks, so a question that shares no word with its clause misses it. And its model is small: it reads the quotes it is given and can still misread them. That is the lane's design, not a fault. The lane lesson 0.3 deploys has every missing piece.

### Prove a first success: make dryrun

Three commands, no credentials, no cost: the kit checks itself, then checks the rows that check the model.

`make dryrun` is three targets, and a bare `make` runs it too, since it is the Makefile's default goal. `check` asks whether the kit still matches the notebooks it was first extracted from; a clone carries none, so it says so and passes. `validate` runs `validate.py`. `eval` runs the offline half of the eval gate. Make runs the three in order and stops at the first that fails.

#### validate.py: 11 checks

The list numbers 10 and a 3b, so there are 11, and the run prints them in this order. Three need a tool: `terraform` and `tflint` validate and lint `terraform/`, and `docker` builds the images. Without its tool a check prints SKIP, never FAIL, and CI, which installs all three, runs them on every push.

#### Run it

Read each block from its last line. `validate.py`: 6 PASS, 1 WARN, 4 SKIP and no FAIL, so it exits 0 and make goes on. The WARN is honest: the `slm` image copies a folder that `make deploy-slm` writes in lesson 9.2, and a fresh clone does not have it yet. The kit's message names that lesson by its notebook-era number, 11.4, as the code's comments do throughout. A WARN never fails the run; `validate.py --strict` would make it. The eval gate: 3 PASS lines and its closing sentence. That is 9 PASS lines in all, and no FAIL: your first success.

#### With Terraform and Docker installed

Install both and run `make dryrun` again. `terraform` then runs `fmt`, `init` without a backend and `validate` over `terraform/` (the first `init` downloads the providers), and `docker` builds every Python image from its own context, which takes a while the first time. The same run on the author's laptop, with both:

#### The eval gate's offline half

It never calls a model; it judges the golden set itself. falsifiable: every `must_contain` is in the tenant's own corpus, and every `must_not_contain` is in another tenant's corpus and not its own, so every row can pass and can fail. anchors: every `must_retrieve` anchor can be found. coverage: no shape has shrunk below its floor, and every id that `evals/required.json` lists, the 15 version, isolation and media rows, still exists. The live half, which sends every row to a deployed API, arrives in Module 4.

### Diagnose a first failure: one loosened row

The most common way an eval suite rots, made on purpose, caught, read and repaired.

Picture a red live run on `lk-06` the night before a release. The fastest way to green is to loosen the row: empty its `must_contain`, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone:

Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled.

One line changed: the row's `must_contain` went from `["60"]` to `[]`. Now run the gate.

#### Read the failure

Read the red run from the top. `validate.py` has not changed its mind: the kit's code did not move, only a data file did. The eval gate's first verdict is `[FAIL] falsifiable`, and the indented line under it is the reason, with the row's id: `lk-06: an answerable row with no must_contain accepts any answer at all`. That is 8 PASS lines and one FAIL. `run_eval.py` prints its closing sentence and exits 1, and make stops there with an error line of its own that names the `eval` target.

The rule is two lines of `check_falsifiable()`, and the comment above them says why it checks the committed file again: `build_golden.py` already refuses such a row when it writes the file, but a hand edit goes around the writer. Notice what did not catch it. coverage counts rows, and `lk-06` is still there; anchors still resolve. A row that cannot fail looks exactly like a test until something asks whether it can.

#### Repair it

`git checkout` puts the committed line back, `git diff --stat` prints nothing, and the run is green again, with 9 PASS lines. Had the change been real, say a re-issued handbook with a new notice period, the repair would be the new figure, not an empty list: the version row `vr-01` asks the same question, and the kit moves both rows with the document in one commit, as `evals/README.md` describes.

### The same gate in CI, and the shell every later lesson opens

What runs these checks on every push, and how the shell you made becomes every lesson's first block.

The kit's CI runs the same three commands on every push and pull request, after its offline unit tests, on a runner that has Terraform and Docker installed, so the checks your laptop skipped run there. The last three steps of its workflow:

A red step there is the red you just read here, with the same reason on the same line. Module 11 builds the pipeline that deploys from the repository without a key.

#### The setup block every later lesson opens with

From Module 1 on, every lesson starts with the same block, lesson 1.1's, and it assumes the shell you just made. Read it now; lesson 1.1 is where you first paste it.

The restart helper you sourced has a second half: `rag_save_session` records a lane's session, and `rag_resume` restores it in a new terminal. Both need a lane; lesson 0.4 saves one and restores it.

### Verify it yourself: the checklist

Each claim of this lesson, the block above that checks it, and what a pass looks like on your machine.

Your machine now has the tools; the kit at `~/deploy_module_rag`, a clone of the learner repository at the commit you pulled, with `evals/golden.jsonl` exactly as committed; `~/rag-shell-venv` with the operator pins; `~/rag-local-venv` with the chat service's; and Ollama with `gemma3:4b`. Inside the clone, the Rs 0 lane left two things that `git status` lists as untracked, harmlessly: `documind_chroma/`, acme's 1,628 chunks, and `services/chat/documind_threads.db`, the lane's conversation file. Nothing exists on Google Cloud yet, and nothing was spent. Lesson 0.3 signs gcloud in, reads the project's resource map and deploys the lane whose boxes the master diagram drew.

Netsetos GenAI on GCP · Module 0 Setup · Lesson 0.2 Reproduce the local environment, read the master diagram and prove a first success · v5.0

Next: Lesson 0.3 Understand the project, identities and resource map, and deploy the lane.
