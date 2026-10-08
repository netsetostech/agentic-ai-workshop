# Lesson 1.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.2_Parse_Chunk_WIX.html`, reviewed at blob `b099dbefa1a1ac6ed8c033e6e86ca49edce9f313`. Learners read that page on the course site; this guide keeps its prose.

Before a document can be searched it has to be read, and before it can be cited it has to be cut into pieces small enough to compare with a question. This lesson opens the two steps that do that in DocuMind: the parser that turns a PDF into pages of text through Document AI, and the chunker that turns text into addressed pieces. You will count pages, cut a handbook into clauses, cut an Act into page windows, and compare the pieces two different parsers make of the same document on your own lane.

- What parsing and chunking are

- The words: page, slice, section, window, locator

- Before you run anything: set up the shell

- Parse: Document AI, chosen by residency

- Count pages first: slices, and the 250-page line

- Chunk by section: the handbook becomes 283 clauses

- Chunk by window: an Act becomes page windows

- Compare the boundaries: two parsers, one document

- One chunker in two places, and what parsing bills

- Verify it yourself: the checklist

You will learn how a file becomes text (parsing, with Document AI for PDFs and no processor at all for Markdown) and how text becomes addressed pieces (chunking, one chunk per clause where a document has headings, page windows where it does not). Then you will prove it on your lane: count the pages, cut the documents yourself, read the worker's pieces back from Firestore, and see why the same Act became 67 pieces on the lane and 65 on your laptop.

### What parsing and chunking are

Two small steps between "a file" and "a piece a question can find", and why the cut decides the answer.

Parsing is reading. A PDF is a drawing of a page: shapes and positions, sometimes with a hidden text layer, sometimes only pixels. Parsing turns it into plain text, page by page, so that "page 7" still means something afterwards. A Markdown file needs no parsing at all; it is already text. DocuMind sends PDFs and images to Document AI, Google's document reader, and reads text files directly.

Chunking is cutting. A question is a sentence or two; a document is thousands of sentences. Retrieval works by comparing the question with pieces of similar size, so the text is cut into chunks of a few hundred words, and every chunk gets an address, its locator, so that a citation can point back to it. The cut matters more than it looks: a clause split across two chunks is a clause the question may never find whole, and a chunk that contains three unrelated clauses is a chunk that answers three questions badly.

A newspaper and a scrapbook. Parsing is the newspaper arriving as pages of print instead of a photograph of the page. Chunking is cutting the articles out for a scrapbook. Cut along the article boundaries and every clipping makes sense on its own; cut every page into equal squares and most clippings start mid-sentence and end mid-sentence. DocuMind cuts along the boundaries when the document has them (headings) and falls back to squares of a fixed size, with an overlap, when it does not (an Act's running text). The locator is the label on the clipping: "Notice period, clause NP-03" or "page 7, second square".

#### Which reader each file gets

Before anything is cut, the worker decides how to read the file, and the file's type decides. Two checks come first and cost nothing: an object outside a tenant folder is refused, and bytes the lane has seen before are not parsed or embedded again. Text is read as it is. A PDF has its pages counted first, for free: over 250 it waits for the batch lane, otherwise it goes to Document AI fifteen pages at a time, and a scan takes the same road because Document AI reads the page images. A picture or a recording cannot be cut like text, so Gemini describes it, and that description is the chunk. Every chunk is scanned for personal data before anything is indexed.

The examples are the kit's own files with their real page counts; the 270-page bundle is the two Acts lesson 1.5 joins, and the video is lesson 7.5's. Step 3 opens the parser; steps 5 and 6 are the two cutting rules.

#### Try the cut yourself

The explorer below runs the kit's own cutting rules on two small samples: a handbook with headings and a page of an Act without. Switch the rule, drag the window size, and watch where the boundaries fall. Then type a word and see which piece would have to be retrieved to answer a question about it. The lane cuts at 2,000 characters with a 200-character overlap; the slider is scaled down so the samples show more than one cut.

Each block is one chunk; its label is the locator the kit would give it. In section mode a clause is one chunk however long or short it is. In window mode the cut prefers a sentence end in the second half of the window, and the next window starts overlap characters earlier, so a sentence on the seam appears in both. The highlighted block is the one that contains your word.

It is the two rules, not the whole worker: no Document AI, no page counting, no hashes. Its window sizes are small so the samples show several cuts. The rules themselves are the ones you will read in step 5 and step 6, character for character.

### The words: page, slice, section, window, locator

Six words, each with the value it takes on your lane.

Two of these words are contracts from lesson 1.1 seen from the other side. The locator is the page-and-section contract; the chunker is what writes it. The page is why a citation can say "p. 7": the parser preserved it. Everything else on this page is mechanism.

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

### Parse: Document AI, chosen by residency

What reads a PDF, why one setting picks the reader, and how to see which reader your lane has.

#### Definition

The worker never reads a PDF itself. It sends the bytes to one Document AI processor and gets back pages of text. Which processor exists is decided once, by `RESIDENCY`: `india` creates an Enterprise OCR processor in Mumbai, `us` creates a Layout Parser in the United States. The Layout Parser understands headings, tables and reading order; the OCR processor returns text with layout boxes and no structure. The comment in the code says why that is not a quality decision: if a customer's contract says its documents stay in India, the processor in `us` is not available, whatever it would have given you. Text files skip all of this - a Markdown handbook is decoded and used as it is.

#### See it in the UI

Look at the document column of the Versions table. Every `.pdf` row went through Document AI; every `.md` row did not. Both kinds end up with a chunk count, and nothing downstream can tell them apart, which is the point of parsing: after it, everything is text. One row to look for is `acme/posh_act_2013.pdf`, a scanned Gazette with no text layer; if it is in your table with a chunk count, your processor can read a scan.

#### The code

Note the default: the code says `india`, but the Makefile deploys with `RESIDENCY ?= us` unless you override it, and the Terraform in `docai.tf` creates whichever processor the same variable names. On a default `make up`, therefore, your lane has a Layout Parser in `us`. The page says both so that what you read off your lane in a moment makes sense.

Read the shape of the return value: one string with a form feed (`\f`) between pages, and the page count. That form feed is the whole reason a citation can name a page: the chunker in step 6 cuts at it and never lets a window cross it.

#### Call it: which reader does your lane have?

Two read-only calls. The first prints the worker's environment, where the residency and the processor id live. The second asks the Document AI API to list the processors in each of the two possible locations; exactly one location will list `documind-parser`.

A lane deployed with `RESIDENCY=india` prints the mirror image: `OCR_PROCESSOR` under `asia-south1` and nothing under `us`. Either way there is exactly one processor, and the worker's environment names it.

You found the one machine that reads every PDF on your lane, and the one setting that chose it. Nothing about the worker's code changes between the two choices; the processor map and the Terraform read the same word. That is what "chosen by residency rather than by preference" means in the parser's first line.

### Count pages first: slices, and the 250-page line

The worker counts a PDF's pages before it pays to read one, and two numbers hang on that count.

#### Definition

Reading a PDF's page count is free: the page tree is in the file, and pypdf reads it without rendering anything. The worker does that first, because two decisions need only the number. A file over 250 pages, `MAX_INLINE_PAGES`, cannot finish inside one push request, so it is handed to the batch lane (lesson 1.5). A file under that line is sent to Document AI in slices of 15 pages, because 15 is the online request limit; a 29-page Act is two requests, a 236-page Act is sixteen. Nothing in the corpus crosses 250: the CGST Act, at 236 pages, is the largest.

#### The code

#### Do it: count the corpus, Rs 0

The same count, on the PDFs in your kit folder, with the same library. The cell prints pages and slices per PDF, then the totals and what one parse of the whole corpus would cost at each processor's list price - the rates as the course reads them on the pricing page, to re-verify before quoting.

#### Prove it on the lane: one small PDF, four pages

The amendment Act is four pages and globex does not hold it, so ingesting it there is a fresh source, one Document AI request, and a few paise. Then read the worker's line for it, which carries the page count as `pages`.

Four pages, five chunks: the count is pypdf's, the chunks are Document AI's text cut per page. Your chunk count may differ by one, because the two readers do not always agree on where a line ends, which is exactly what step 7 is about.

The worker learned the page count for free, decided the file was small enough for the push lane, sent it to Document AI in one slice, and wrote `pages: 4` on its log line. The same field on the CGST Act's line reads 236 and sixteen requests were made for it; over 250 and the line would have been `ingest_queued_batch` instead.

### Chunk by section: the handbook becomes 283 clauses

The first rule of the chunker, and why a clause is the right size for a policy question.

#### Definition

A Markdown document with `##` headings is cut at the headings: one chunk per section, whatever its length, with the heading's clause code as the locator (`NP-03`) or, when a heading carries no code, the section's ordinal (`s1`). Text above the first heading is the `preamble`. A section longer than a window is windowed within itself and its pieces are numbered (`NP-03-1`). A question about the notice period is answered by one chunk that is exactly the notice-period clause, which is why the handbook's answers cite so precisely.

#### The code

The first line drops a mirror's provenance header, the HTML comment `fetch_real.py` writes at the top of every mirrored Act, so a comment about where a file came from is never indexed as content. The rest is the rule: preamble, then one chunk per heading, each chunk beginning with its own title so the clause code is inside the text that gets embedded.

#### Do it: cut the handbook, Rs 0

Every one of the 282 sections fits in a single window, so no locator carries a numeric suffix; the handbook's clauses are short. The hashes are what lesson 1.1 called the chunk's identity across versions.

#### Read it on the lane

The worker cut the same file with the same rule when the corpus was loaded. Its rows for the handbook should be the same 283 locators in the same order.

Two different programs - the worker on Cloud Run and the loader on your machine - cut the same Markdown into the same 283 pieces with the same locators and the same hashes. For a text file there is nothing to disagree about: no parser stands between the bytes and the chunker. Step 7 shows what happens when one does.

### Chunk by window: an Act becomes page windows

The second rule of the chunker: fixed windows with an overlap, cut page by page, ending on a sentence when one is near.

#### Definition

Running text has no headings to cut at, so the chunker cuts windows of 2,000 characters. It prefers to end a window at a sentence boundary in the window's second half, and it starts the next window 200 characters back, so a sentence sitting on the seam is present in both. Windows never cross a page: the text is split at every form feed first, and each page is windowed on its own. The locator is the page and the window's number on it, counted from zero: `p7-0`, `p7-1`. Text with no form feeds at all has no page to name, and its locators are `w0`, `w1`.

#### The code

#### Do it: cut the Code on Wages, Rs 0

Your kit has a text mirror of every Act, made by pypdf when the corpus was fetched, with a form feed between pages. Cut the mirror of the Code on Wages and look at one seam.

Page 1 is a title page and makes one window; page 2 makes two. Look at the seam. The first window is exactly 2,000 characters and ends in the middle of the word "including": the definitions clause on that page runs for hundreds of characters without a full stop, so there was no sentence end in the window's second half to cut at, and the rule fell back to a hard cut. This is what the overlap is for. The second window starts 200 characters earlier, so the broken word, and the sentence around it, are whole in `p2-1`. A question about that sentence still finds it.

#### Read it on the lane, and ask a question that lands on a page

The lane's windows carry pages because the parser kept the page breaks, and the citation shows `page 9` because the chunk's `page_start` is 9: section 17 of the Code, on when wages fall due, sits on page 9 of the Act. But look at the first line: the lane has 67 windows where your mirror has 65. Same Act, same rule, two different counts. That is the next step.

### Compare the boundaries: two parsers, one document

Why the same Act became 67 pieces on the lane and 65 on your laptop, and what that means for anything that compares chunks.

#### Definition

The chunking rule is the same in both places, character for character. What differs is the text it was given. The lane's text came from Document AI; your mirror's text came from pypdf when the corpus was fetched. Two readers of the same PDF do not produce identical characters: line breaks fall differently, hyphenated words are joined or not, headers and footers are kept or dropped, spaces between columns vary. A window is cut by counting characters, so a few characters more or fewer on a page can add or remove a window. For a Markdown file nothing stands between the bytes and the chunker, and the two sides agree exactly, as step 5 showed.

#### The numbers, on a real lane

Even where the counts agree, the hashes do not: a single differently placed line break changes a window's characters and therefore its `chunk_hash`. The two sides only match exactly on files that need no parsing.

#### See it, page by page

#### Why it matters

Three things follow, and the kit is built around all three. First, a chunk id on the lane is not the id a notebook would give the same PDF; only the Markdown-fed rows match. Second, the golden set does not assert on ids at all: its `must_retrieve` anchors are short phrases matched against the retrieved text, so a test written on the mirror still passes against the lane. Third, when you compare two retrievers, two lanes or two versions, compare quotes and locators, never ids. Module 4 builds on exactly this.

You held the two parsers' outputs side by side and found where they parted: a couple of pages where a few extra characters pushed a window over 2,000 and forced one more cut. Same document, same rule, different text. The lesson is not that one parser is wrong; it is that a boundary is a property of the text you cut, so anything that depends on a boundary must be checked on the text the lane actually holds.

### One chunker in two places, and what parsing bills

Why the chunking rule is written twice, how the kit keeps the two copies honest, and where the rupees go.

#### Two copies, one rule

The chunker lives in `services/ingest/main.py` for the worker and again in `shared/documind_corpus.py` for everything that runs outside the worker's image: the notebooks that seed a Colab lane, the Rs 0 lane on a laptop, and the offline evaluation gate that runs on every push. The image cannot import a notebook and a notebook cannot import the image, so the block is pasted into both, with the same constants and the same two rules. The kit's own check holds the two to identical output on the same text - the same 65 windows from the Code on Wages mirror, the same 283 clauses from the handbook. Two small differences are deliberate: the loader gives a Markdown chunk `page_start: 1` where the worker gives `None`, and the loader's chunk ids are the human form `acme:hr_policy_2026#NP-03` while the worker's are the version-and-position form from lesson 1.1.

Compare it with `_windows()` in step 6: the same loop, one difference in what it returns (the worker keeps the start offset too). The comment on the first line points at the worker's file, which is how a reader knows where the twin lives.

#### What parsing bills, and what it does not

The asymmetry is worth remembering when you design an update: parsing is paid per re-issue, embedding is paid per changed chunk. A tenant that re-uploads a 200-page PDF to fix one clause pays for 200 pages of parsing and one chunk of embedding.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

One new source: `globex/maternity_benefit_amendment_act_2017.pdf`, four pages, five chunks, a few paise of Document AI. Everything else was read, not written. Lesson 1.3 takes the chunks you cut today and gives each one its 768 numbers, with the stamp that lets the lane tell its own vectors from anyone else's.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.2 Parse documents and compare chunk boundaries · v5.0

Next: Lesson 1.3 Create and validate compatible embeddings.
