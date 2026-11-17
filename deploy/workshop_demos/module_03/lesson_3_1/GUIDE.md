# Lesson 3.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.1_Stochastic_WIX.html`, reviewed at blob `a05b177935767e6d4412a41782001c53c305ff58`. Learners read that page on the course site; this guide keeps its prose.

Ask DocuMind the same question twice and the answer can come back in other words. Lesson B.5 showed where that comes from, and why the kit sends its model no temperature. This lesson measures it on the kit itself. The prompt bench, `evals/prompt_bench.py`, reads one golden row's passages from your lane once, asks the kit's own `generate()` the row's question five times at thinking level LOW and five at HIGH, and judges every answer by the eval gate's own rule. It counts the distinct answers, the distinct sets of citations and the passes, keeps the thought tokens apart from the visible ones, and prices every answer in rupees. Then it sends a temperature of 2.0, keeps proof that the value went out, and lets you read what changed. You will see the variance in the UI, read the code that holds everything else fixed, run the bench for Rs 0 and then on your lane, and read what your lane logged.

- Why one prompt answers in different words, and what thinking buys

- The words: run, pool, thinking level, thought tokens, arm, recorder, distinct answers, pass k/N

- Before you run anything: set up the shell

- One question, five times, in the Chat page

- The kit's code: what every answer is sent, and how the bench turns one knob

- The bench for Rs 0: its tests, and a scripted model

- Five calls to /v1/query, judged by the gate's rule

- make bench: five runs at LOW and five at HIGH

- Change it: send a temperature of 2.0, and read what went out

- What your lane logged, and what the bench did not

- Verify it yourself: the checklist

You will learn what can change between two runs of one prompt (the words, the citations, the verdict), which of those the eval gate fails, and what a higher thinking level buys and costs. Then you will prove it on your lane: golden row jn-03 asked five times at LOW and five at HIGH with the kit's own generator, and five times more with a temperature of 2.0 that the model is documented to ignore.

### Why one prompt answers in different words, and what thinking buys

What can differ between two runs of one prompt, which difference the gate fails, what the bench holds fixed so that the model is all that is left, and what a thinking level and a temperature change.

Lesson B.5 explained the mechanism; this page measures it on the kit. A decoder writes one token at a time, each drawn from a probability distribution, so two runs of one prompt can draw differently and write different answers. B.5 built that loop in numpy, showed the knobs that reshape the distribution (temperature, top-k and top-p), quoted Google's model page saying that gemini-3.6-flash ignores all three, and sent a bare prompt five times. This page does not repeat any of it. It asks the kit's own generator, on your lane's own passages, and judges every answer the way the eval gate judges `/v1/query`.

Three things can differ between two runs, and only one of them is a failure. The wording: "45 days are encashed" and "encashment is capped at 45 days" are one answer to a reader. The citations: which of the passages the answer cites. The verdict: whether the answer carries what the golden row requires. Row jn-03 asks: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? The gate requires 45, the cap on encashed leave in clause LV-07, and 60, the E3 notice period in clause NP-03, each as a figure on its own boundary, and citations that name acme's own, current documents. An answer that has all 50 days encashed has varied in the way that matters. The bench counts all three, per thinking level: distinct answers, distinct cite sets, and pass k of N.

What the bench holds fixed, so that the model is all that is left. A difference between two answers could come from retrieval (a different pool), from the prompt (a different text), or from the model. The bench removes the first two. It reads the row's pool once from `/v1/passages`, which runs the same door, retrieval and reranker as `/v1/query` and stops before the model, and every run answers from that one pool. The prompt is `generate()`'s own, built from that pool, and the bench prints the sha256 of its head, the rules every prompt starts with, so that you can see it is the text `documind-rag@v3` names. What is left is the model: what it draws, and how long it thinks before it answers.

A thinking level is how long the model thinks before it answers, and you pay for it. A Gemini 3 model writes thought tokens before its answer. Nobody reads them, and they are billed at the output rate: Rs 0.64 per 1,000 on gemini-3.6-flash, 5 times the price of a prompt token. `thinking_level` sets how much it thinks: MINIMAL, LOW, MEDIUM, HIGH. The kit sends LOW on every answer. jn-03 joins two clauses and needs one small calculation (50 days earned, at most 45 encashed), which is the kind of question where more thinking could change the verdict. The bench asks it five times at LOW and five at HIGH, and prints per level the passes, the thought tokens an answer and the rupees an answer, so that whether HIGH is worth it is read off one table. Five runs are a small sample: five passes out of five still has a Wilson lower bound of 56.6%, so every rate on this page is read with its interval.

A temperature the model ignores, sent on purpose. `generator.py` sends no temperature: its comment says gemini-3.6-flash ignores one, and lesson B.5 quotes the model page that says so. The bench can send one anyway. Its edit arm sends 2.0, the hottest value B.5's toy tried, beside the kit's own arm, and its recorder keeps the config each call went out with. So the run answers two questions apart: was 2.0 sent (the recorder's log), and did anything change (the table).

One recipe card, five cooks, one inspector at the pass. A restaurant kitchen hands five cooks the same recipe card and the same tray of ingredients, and asks each of them for the same thali. The five plates come back different: one cook puts the dal on the left, another adds coriander, a third folds the roti in half. None of that is a mistake. The inspector at the pass does not compare the plates with one another. She checks each plate against the order: the two items it names, in the quantities it names, made from this kitchen's tray. A plate with three rotis where the order said two goes back, however well it is laid out. Give the cooks ten minutes to plan before they start and the plates may come out more alike, or more often right; the planning is paid by the minute either way, and nobody eats it. And the stove has a knob marked "flame" that, on this model of stove, is not connected to anything. Turn it to full and the cooking does not change, though the order slip still records that you turned it.

The recipe card is the prompt: `generate()`'s rules, the packed passages and the question. The tray is the row's pool, read once from `/v1/passages`. The five cooks are five calls at one thinking level. The plating is the wording, and the items named are the citations. The inspector is `run_eval.row_verdict()`, and the order's two quantities are 45 and 60. The planning time is the thinking level, paid in thought tokens. The knob is the temperature on gemini-3.6-flash, and the order slip is the bench's recorder.

#### One row through the bench: what is held fixed, and where the answers can differ

The names are the kit's own: `evals/prompt_bench.py` and what it imports, in the order `make bench` runs them. Step 4 reads each piece in the code.

#### The gate's rule, answer by answer

Before the bench runs, see what its judge does with wording. The widget below is `run_eval`'s own reading of a figure, `normalise()` and `contains()`, and the text half of `row_verdict()`, ported to the browser and checked against the kit on 51 cases when this page was built. Try an answer in the first box: a chip fills it with one, and the lines under it say what the gate makes of it. Then edit the answers below it and watch three things move: each verdict, the count of distinct answers, and pass k/5 with its interval.

A verdict here is the gate's for a reply whose citations are valid. A figure must stand on its own boundary once number words have become digits on both sides, so "sixty" is 60, "160" is not, and neither is "60.5". Distinct answers counts the texts that still differ once their spaces are collapsed, as the bench counts them, and pass k/5 carries its Wilson interval, as the bench prints it.

It is the text half of the rule, not all of it. On your lane `row_verdict()` also checks every citation: that its chunk id and its object belong to acme, and that its version is one the ledger lists as current (`judge_citations()`, step 4). The widget takes the citations as valid, so an answer it passes could still fail on the lane for a citation; a recorded answer that did keeps the bench's own verdict until you edit it. It calls no model. And the "45 rupees, 60 hours" chip is there to show the rule's blind spot: it checks figures, not meaning. That is why the gate checks citations as well, and why lesson 4.2 adds a judge.

### The words: run, pool, thinking level, thought tokens, arm, recorder, distinct answers, pass k/N

Fifteen rows, each with what it means and what it is on your lane.

Two of these words carry the lesson: distinct answers, the variance a reader may not mind, and pass k/N, the variance the gate fails. The rest say how each is held still, counted and priced.

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

Steps 4 and 5 cost nothing: step 4 is reading, and step 5 runs the bench in your shell with a scripted model and no network. Steps 3, 6, 7 and 8 ask Gemini on your lane, thirty answers in all, and each says what it costs: the input by the kit's own count of jn-03's prompt on the Rs 0 lane's pool (about 1,584 tokens with 6 passages), and a ceiling with every answer at the 2,048-token cap. The thinking comes out of that cap, so a typical answer costs a fraction of the ceiling, and every run prints what it spent. Step 9 reads logs, for Rs 0.

### One question, five times, in the Chat page

Golden row jn-03 asked five times as yourself: what moves between the answers, what stays, and what the page sends.

Start in the product, where a user meets variance. The Chat page streams each answer from `/v1/stream` and sends only the question: rag-api keeps no history, so five turns are five independent answers to one prompt. Before you ask, note the time in the operator shell. Step 9 reads the usage rows written since then.

#### Do it: ask it five times

- Open the Chat page. Open `https://documind-ui-NUMBER.asia-south1.run.app` and sign in as yourself; the roster maps you to acme. If the sidebar offers a Brain, choose `direct`.

- Ask five times. Paste the question below and send it. When the answer has finished, paste it again, until you have five answers: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?

- Read the five answers. Compare their words, and the teal pills, which are the `[N]` numbers each answer cites. Look for 45 and 60 in each.

- Read what stays. Open Sources under each answer: the passages the stream sent before its first token. Then the sidebar: Tokens grows by each turn's input and output, the thinking included, and Cost this session by its price.

Five streamed answers: about Rs 0.78 of input by the kit's count, at most Rs 7.30 with each at the cap.

#### What the Chat page sends

Each answer came from `generate_stream()`: the same rules and the same thinking level, LOW, as `/v1/query`, and no temperature. It differs from the gate's request in two ways you will meet again. The stream has no response schema, so it writes free text rather than the JSON the gate reads, and the page asks for 5 passages where the gate asks for 6. The Sources list should hold the same passages all five times, because retrieval and the reranker saw the same question; the stream cites what it packed before the model writes a word, so that list is retrieval's, not the model's. If it changed between asks, something moved the pool: a reindex, or acme's store pin. What moved is the model's: the words, sometimes the pills, and the tokens on the sidebar. The sidebar's comment says why there is no slider for any of it.

The Chat page shows variance as a user meets it, but it cannot count it or judge it. The rest of this page does both.

### The kit's code: what every answer is sent, and how the bench turns one knob

generator.py's one request and its bill, the bench's make target, its recorder and its loop, and the gate's rule that judges every answer.

#### Definition

Every `/v1/query` answer is one call of `_call()` in `services/rag-api/generator.py`. Its config has four settings and a comment about the ones it leaves out: JSON back, the `ModelDraft` schema, a cap of 2,048 output tokens that the thinking is drawn from, and `thinking_level` LOW. No temperature, top-p or top-k is sent, because gemini-3.6-flash ignores all three. `_usage()` bills what came back, and it adds the thought tokens to the visible ones in a single `tokens_out`: right for the bill, and the reason the API's envelope cannot tell you how much of an answer was thinking. When a reply is cut off at the cap, `generate()` asks once more with three times the room, 6,144, and bills both attempts. A higher level thinks more out of the same cap, so a cut-off is likelier at HIGH, and the bench prints a retried line when one happens.

#### The code: what every answer is sent

The bench changes one thing at a time and keeps everything else as the kit has it. `make bench` mints the identity token `make eval-live` uses, as `documind-ui-sa`, sets `GOOGLE_CLOUD_PROJECT`, and runs `evals/prompt_bench.py` in your shell. The bench reads each row's pool once from `/v1/passages`, the route that stops before the model. Then it imports `generator.py` as the service imports it and answers with its `generate()`: the same packing, prompt, schema, cap and retry. The one thing it replaces is `generator._client`. The `Recorder` takes its place, so every call passes through it: it sets `thinking_config` to the level being benched and, in the edit arm only, a temperature; it passes the rest of the config on as `_call()` built it; and it keeps what was sent, the usage with the thought tokens apart from the visible ones, and the time. `bench()` runs every row, arm, level and run, interleaved run by run, and puts `generator.SYSTEM` and `_client` back however it ends. `call_inr()` prices each call at list price, the thought tokens at the output rate.

#### The code: the bench

Every answer is judged by `row_verdict()`, the eval gate's judgment of one reply, lifted out of `live()` so that the bench and the gate share one rule; a test in the kit holds the two equal. A reply that is not a well-formed 200 is an error. A forbidden figure in the answer fails it. An answerable row must be answered, with citations that name the tenant's own, current documents, and with every `must_contain` figure, which `contains()` looks for on its own boundary once `normalise()` has turned number words into digits on both sides. `summarise()` then turns the answers into the table's columns: distinct answers and distinct cite sets, counted within each row across its runs, the quote checks, the tokens and the rupees.

#### The code: the judge and the count

Take three things into the runs. The bench's arms differ only in what the recorder sets, `thinking_config` and `temperature`: the schema, the cap, the prompt and the pool are the kit's in every arm. The thought tokens are a column of their own in the bench's table, and in the API's `tokens_out` only a part of a sum. And a pass is the gate's pass, not the bench's opinion: the same function decides it for `make eval-live`.

### The bench for Rs 0: its tests, and a scripted model

The kit's own tests of the bench, then the bench itself, as make bench runs it, over a stand-in lane and a model that follows a script.

#### Definition

Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in `evals/tests/test_prompt_bench.py`. They answer with the kit's own `generate()` over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, `generator.py` is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv.

Then the bench itself. The cell below runs `prompt_bench.main()`, the function `make bench` runs, over `generator.py` imported in your shell, with two things stood in. `/v1/passages` returns the handbook's first six clauses, cut by the kit's own chunker as the kit's tests cut them, so NP-03 is `[Source 1]` and LV-07 is `[Source 4]`. The model is a script behind `generator._client`. It writes five wordings of an answer to jn-03 in turn, the same five at every level and temperature, and "thinks" 120 tokens at LOW and 900 at HIGH, the numbers the kit's tests script. Its fifth wording has all 50 days encashed, so that you can see a failure printed. It also counts the thinking level and the temperature each call was sent with. The cell runs the bench twice: the two levels with `--show`, then a temperature of 2.0.

Read the first table as you will read your lane's. The pool line says the row's 6 passages were read once, before any answer. The kit arm's prompt sha256 is `543ed8060f1b...`, the sha256 that `services/rag-api/prompt_versions.json` registers for `documind-rag@v3`: the bench asks the prompt your lane answers under. Each answer line is one `generate()`: its verdict, its thought and visible tokens, and its rupees.

The script writes the same five wordings at both levels, so the table's two rows agree on everything the words decide: 4 of 5 distinct answers, 1 of 5 cite sets, and 4/5 = 80.0% [37.6%, 96.4%] passed. Run 5 failed with the gate's own line, answered without ['45', '60']: it states one of the two figures, and the rule wants both. The rows differ only in what the level decides: 120 thought tokens an answer against 900, so Rs 0.1859 an answer against Rs 0.6831. Those 780 extra thought tokens, at Rs 0.64 per 1,000, are Rs 0.4972 more an answer, and they bought nothing, because the words did not change.

The temperature run printed two arms with one sha256: the same prompt. The script's own count shows that the edit arm's five calls carried a temperature of 2.0 and the kit arm's five carried none. The script ignores the value, because a script draws nothing. Whether Gemini does is step 8's question.

### Five calls to /v1/query, judged by the gate's rule

The request the eval gate sends, five times, each reply judged as the gate judges it, with its citations, its tokens, its time and its price.

#### Definition

Now the real model, through the API. `/v1/query` is the request `make eval-live` sends for every golden row, and the bench's kit arm at LOW reproduces it, so these five answers are five more draws from what step 7 measures. The cell asks the way the gate asks, `run_eval.ask()` with top_k 6 as `documind-ui-sa`, and judges each reply with `row_verdict()` after reading the ledger's current versions from `GET /v1/sources`, as the gate does. It starts with `/version`, which names the model, the prompt version and the answer cache. The cache is `off` unless a deploy turned it on (`SEMANTIC_CACHE`, lesson 6.2); with it on, a repeated question can come back from the cache with no model call, and the five would not be five draws.

Read the five answers side by side first, then the last line: distinct answers counts the wordings, cite sets counts which passages were cited, and pass is the gate's verdict with its interval. The tokens move from run to run even where the words barely do. `tokens_out` is the bill, the visible answer and the thinking together, and this envelope cannot say how much of it was thinking; step 7's recorder can. A failed answer carries the gate's own line, the one `make eval-live`'s report would give it.

[awaiting the author's run: data/rest_five.txt]

### make bench: five runs at LOW and five at HIGH

One pool from your lane, ten answers from the kit's generate(), the thought tokens apart from the visible ones, and the table that says what HIGH bought.

#### Definition

The bench on your lane: jn-03's pool read once from your `/v1/passages`, then `generate()` five times at LOW and five at HIGH, interleaved, each answer judged and priced. `--show` adds the pool and each level's distinct answers, the most frequent first. `--report` keeps every answer, the config it was sent with, its usage and its verdict in `evals/reports/bench-levels.json`, which the kit's `.gitignore` keeps out of git. The bench imports `generator.py` in your shell: Module 0 installed rag-api's pins in your venv, and if this shell lacks one the bench names it and stops before any call.

Read the table a column at a time. pass is what the gate would make of these answers, with its interval: a difference between the two levels means something only where their intervals do not overlap, and with five runs a level that is rare. 5/5 = 100.0% [56.6%, 100.0%] and 3/5 = 60.0% [23.1%, 88.2%] overlap. distinct and cite sets are the variance a reader meets, and more wordings at one level is no worse if every one of them passes. thought and visible are output tokens an answer, both billed at the output rate: HIGH's extra thinking shows in the first, and the second is the answer's own length. Rs/answer prices the difference. Under the table, `--show` prints each level's answers: read the ones that differ, and ask whether the difference is wording or a figure.

[awaiting the author's run: data/bench_levels.json] The figures for each level are computed here from the recorded file.

Whether HIGH is worth its price is a question about rows like this one, not about one row. A level that adds rupees to every answer has to move verdicts somewhere to earn them. Lesson 3.2 asks it of all 11 join rows at LOW, MEDIUM and HIGH; here the answer is one row's, five runs a level, with the intervals beside it.

### Change it: send a temperature of 2.0, and read what went out

The edit arm with a temperature the model is documented to ignore, the kit arm beside it, and the recorder's log of every call's config.

#### Definition

`generator.py` sends no temperature; the bench can. `--temperature 2.0` adds a second arm, edit: the kit's prompt, the kit's level and a temperature of 2.0 on every call. The kit arm runs beside it, interleaved, so the two share the lane's conditions, and both print one prompt sha256, because the text is the same: the only difference the run can show is the knob. Without `--levels` the bench runs at LOW, so this run's kit arm is a third sample of the request steps 6 and 7 already asked.

#### Read what went out

The table cannot prove that 2.0 was sent: it prints each arm's settings, not its requests. The recorder's log can. Every call in the report carries its config as sent (the thinking level, the temperature, None when none was sent, and the cap) and what came back.

Two questions, two places. Was 2.0 sent? The log says so call by call: each edit call went out with a temperature of 2.0 and each kit call with none, all at thinking level LOW with a cap of 2,048. A level or a temperature the model does not take comes back as the API's error, on that answer's row, as the bench's docstring says; an edit arm whose five answers came back took the value without an error. That is what "ignored" means here: neither refused nor, if Google's page is right, applied.

Did anything change? Compare the two arms' rows in the table. Two samples of the same thing differ by chance, and the kit arm at LOW has now been sampled three times on this page, in steps 6, 7 and 8, which shows how far it moves on its own. If the edit arm sits inside that spread, five runs cannot tell the temperature from chance, which is what Google's page for gemini-3.6-flash leads you to expect. If it sits far outside it, run after run, the comment in `_call()` no longer holds for your model: keep the reports, and raise it.

[awaiting the author's run: data/bench_temperature.json] The two arms' figures are computed here from the recorded file.

### What your lane logged, and what the bench did not

The usage rows written since you started: the Chat page's five, the REST loop's five, the bench's two pool reads, and no row for the bench's twenty answers.

#### Definition

rag-api writes one usage row for every `/v1/query`, `/v1/stream` and `/v1/passages` request, in the one shape `main.py`'s `usage_row()` builds, to Cloud Logging. `make usage` and the BigQuery view `tenant_daily` read those rows, and as each one is written its cost is added to the month's spend counter, which the router's breaker reads before it picks a model. The cell reads the rows written since `T0`, the time you noted in step 3, oldest first, with each row's tokens and the price `cost.py` gave it. Wait a minute after step 8, because a row can take a little while to reach the log, and if this is a new shell, set `T0` again to a time before step 3.

Count the rows by kind. The `stream` rows are your five questions in the Chat page. The `query` rows are step 6's five calls, each with the tokens that cell printed: the row is the API's own record of what it billed. The `passages` rows are the bench's two pool reads, with no tokens and no cost.

The bench's twenty answers left no row at all. `generate()` ran in your shell, not in rag-api, so nothing wrote one. They were billed to your project all the same: you will find them in the bench's own rupee lines and on your Cloud Billing report, and not in the usage rows, `tenant_daily` or the month's counter. Run the bench on a busy lane and the warehouse under-counts by exactly what the bench spent.

[awaiting the author's run: data/usage_rows.txt]

### Verify it yourself: the checklist

Ten checks, each one block above, each with what proves it.

Nothing deployed, and no setting changed. Your lane logged five `stream` rows from the Chat page, five `query` rows from step 6 and two `passages` rows from the bench, and billed thirty answers in all, twenty of them in no usage row. The bench wrote two reports under `evals/reports/`, which git ignores: keep them to compare a later run against, or delete them. `generator.py` is as it was, as each bench run's last lines said. acme's pin goes back with the setup section's window, when you finish. Lesson 3.2 takes the thinking level from one row to all 11 join rows, and asks the same question of few-shot exemplars.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.1 See run-to-run variance and thinking levels in the same prompt · v5.0

Next: Lesson 3.2 Prompt with chain of thought and few-shot exemplars.
