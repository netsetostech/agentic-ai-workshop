# Lesson 6.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.4_Cache_Measure_WIX.html`, reviewed at blob `afcbff09c9738c4e6b84e3080c2c49c6941152f9`. Learners read that page on the course site; this guide keeps its prose.

One number decides what the answer cache is worth: how similar a new question must be to an earlier one before it gets the earlier answer. Set it too low and the cache answers the wrong question fast; too high and it never answers at all. You measure that number offline on the kit's 42 labelled pairs. Then you ask the same pairs live on a candidate at the kit's 0.95, and check whether the offline curve predicted the live false hits. Finally you turn the hits into avoided calls in rupees, and set their latency beside a model answer's.

- One number, two rates, and what a hit is worth

- The words: threshold, similarity, pairs, hit rate, false-hit rate, the rule of three, avoided call

- Before you run anything: set up the shell

- The curve: every candidate threshold on the labelled pairs

- The replay: the same pairs, asked live at 0.95

- Avoided calls in rupees, and the latency of a hit

- Choosing the threshold, and the clean-up

- Why the cache is tuned this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn why the questions most likely to be served a wrong answer are the ones one word away, how a labelled set turns a guessed threshold into a measured one, and how much a set this size can promise. Then you will prove it on your lane: the threshold curve from your own embeddings, the live false hits beside it, and the calls the hits avoided, in rupees.

### One number, two rates, and what a hit is worth

The threshold buys savings and wrong answers together; a labelled set says how many of each.

One number decides what the answer cache is worth. On the near rung, a new question gets an earlier answer when the cosine similarity of the two questions' embeddings is at or above the threshold. Every threshold therefore buys two rates. The hit rate is the share of genuine rephrasings that are answered from the cache, which is the saving. The false-hit rate is the share of near-miss questions that are answered from it too, which is a wrong answer. The two move together: lower the threshold and both rise.

The dangerous questions are the ones one word away. "The notice period for a confirmed E3" and "for a confirmed E2" differ by one character. So do Rs 3,00,000 and Rs 30,000, "minimum" and "maximum", and "before" and "after". An embedding summarises what a question is about, and one token barely moves the summary. Such pairs are often the most similar pairs of all, which is why the kit chose 0.95 rather than a looser 0.92, and why the switch stays off until the number is measured.

Measure it on labelled pairs, and read how big the set is. `evals/paraphrases.jsonl` holds 24 pairs that ask a golden row's fact in other words, where a hit is right, and 18 pairs a few words away with a different answer, where a hit is wrong. `cache_threshold.py` embeds both sides the way the API embeds a query and prints both rates for nine candidate thresholds. The kit's rule is to take the lowest candidate with no false hit. But zero false hits on 18 pairs does not prove zero. By the rule of three, the true rate could still be as high as about 17%, with 95% confidence. Only a bigger, harder set narrows that.

Then count what the hits bought, and what they cost. Every hit is a model call not made: its row says `cache` at a cost of 0, and its latency is an embedding and a Firestore read. The rupees avoided are the hits times the average cost of a model answer. A false hit is counted among those hits as well: it saved a call by being wrong. So report both numbers side by side.

A pharmacy counter. An assistant is allowed to hand over what was dispensed a minute ago when the next customer asks for the same thing, so the pharmacist is not called every time. "Paracetamol 500" and "the 500 milligram paracetamol tablet" are the same request, and serving it at once is right. "Paracetamol 650" looks almost identical and is a different dose, and serving that is the mistake that matters. A careful pharmacy tests the assistant on labelled pairs before allowing it, counts how many pharmacist minutes the assistant saves, and knows that twenty clean tests do not prove the assistant never errs.

#### The threshold explorer

Each dot is one pair, placed by its similarity: teal pairs ask the same fact, red pairs ask something else. Move the line and read what the cache would serve. It starts on an invented example; step 3 gives you your own report to paste in.

The counts and the recommendation are `curve()` and `recommend()` from `evals/cache_threshold.py`. The build ran the kit's two functions on the example and on 61 random sets, and the port agreed with each. The day's figures are arithmetic on your inputs; the rupee default is the example rows' average model answer at `cost.py`'s rates.

The starting similarities are invented for this page. There is no recorded measurement, and the example exists to show the shape of the trade. Your own report, from step 3, is the only curve that says anything about your lane. The explorer places each pair against its own golden question, as the tool does; the live cache compares a question with every stored one, and step 4 shows where that differs.

### The words: threshold, similarity, pairs, hit rate, false-hit rate, the rule of three, avoided call

Eleven rows, each with the value it takes on your lane.

One distinction to hold: the curve measures embeddings, and the replay measures the cache. The curve compares each pair with its own golden question only. The live cache compares a question with every question stored for the tenant, and serves the first alive one at the threshold. Step 4 shows both, side by side.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. Step 3 makes 65 embeddings, which cost a fraction of a paisa. Step 4 creates a candidate with `SEMANTIC_CACHE=on` that serves no traffic, and asks it 65 questions. About fifty of them reach the model, so the replay costs roughly as many rupees as it has misses, at half a rupee each. Step 6 removes the candidate's tag.

### The curve: every candidate threshold on the labelled pairs

The pairs, the check that they can judge anything, and both rates for nine thresholds.

#### Definition

A pair names its golden row, its tenant, the question, and whether it asks the same fact. `check_pairs()` refuses a set that cannot judge a threshold. It rejects a pair whose row does not exist, a same-fact pair against an unanswerable row, a pair identical to its golden question (the exact rung would serve that, so it tests nothing), a pair on the wrong tenant, and a set with fewer than 15 same-fact or 10 different pairs. The tool then embeds the 23 golden questions and the 42 pairs with `text-embedding-005`, `RETRIEVAL_QUERY`, 768 numbers, which is how the API embeds a question. For each pair it takes the cosine similarity to its own golden question. `curve()` counts the hits and false hits at each candidate threshold, and `recommend()` picks the lowest one with no false hit. It embeds in us-central1 by default; the model is the same one the API calls in its own region.

#### The code

#### Do it

Read the table from the bottom up. At the top candidates, no different pair hits, but few same-fact pairs do either. Moving down, the same-fact hits climb quickly, and so do the false hits. The line under the table is your lane's lowest safe threshold, and the list after it is the different pairs sorted by how close they came. That table is this lesson's first proof, the threshold curve. The nearest false pairs are usually the one-token ones: a grade, a zero, minimum against maximum. Now run `cat ~/cache93_curve.json`, copy the output into the explorer above, and press Read my report. The dots then become your similarities.

### The replay: the same pairs, asked live at 0.95

A candidate with the answer cache on, the golden questions first, then every pair.

#### Definition

The live cache does more than the curve. For a new question, the near rung asks Firestore for the tenant's five nearest stored questions, walks them nearest first, stops at the first below the threshold, and serves the first one that is still alive. The replay asks the candidate the 23 golden questions first. Those are misses, and each answerable, cited answer is stored. Then it asks every pair. A hit returns a stored answer word for word, so the cell can tell which golden question it came from. Its own golden answer on a same-fact pair is a right hit; its own golden answer on a different pair is a false hit. Another question's answer is a hit from that question, which you judge by reading it. The cell prints only the hits, then a count for each kind of pair, and saves every result to `~/cache93_replay.json`.

#### The code

#### Do it: the candidate

#### Do it: the replay

Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own `run_eval.py` gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it.

The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

If every question failed, the candidate cannot answer at all; if a few did, those questions reach a step the others do not. The traceback's last lines name the step.

Set the replay's count of different pairs served from the cache beside the curve's false hits at 0.95. If the two agree, the offline curve predicted the live cache, which is what makes it worth running before any threshold goes live. A difference has a reason you can find in the hits list. A line reading `hit from` means another stored golden question was nearer than the pair's own. Read its answer: sometimes it is the right answer for the pair, and sometimes it is a second kind of false hit that the curve cannot see. Every `FALSE HIT` line is a customer who would have got a confident, cited, wrong answer at the kit's 0.95.

### Avoided calls in rupees, and the latency of a hit

The candidate's own rows, then the kit's usage table for the same hour.

#### Definition

Every answer on the candidate wrote a usage row, and a hit's row says `model_backend` `cache`, with zero tokens and zero cost. The cell reads the candidate revision's rows since step 4 began and splits them into hits and model answers. It prints the p95 latency of each, the average cost of a model answer, and the calls the hits avoided, priced at that average. It then reads the replay's file and names the hits that served a wrong answer. `make usage` groups the same rows the way the warehouse view does, and its "by model and backend" table shows the cache as a row of its own.

#### The code

#### Do it: the candidate's rows

#### Do it: the kit's table

The avoided calls, in rupees, are this lesson's second proof. Read them together with the line under them. Every hit saved a model call and cost nothing on the row, and a hit's p95 is a fraction of a model answer's. That time is the embedding and a Firestore read, and the embedding is paid on a miss too. But the wrong answers are counted among the savings. On this replay the cache was cheap and fast, and for the different pairs it was also wrong. The warehouse view, `tenant_daily`, groups the same way, so the cache's share of answers and its latency are one query away every day.

### Choosing the threshold, and the clean-up

What the numbers allow, where the threshold lives, and the candidate put away.

The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's `hit from` lines, which the curve cannot see. The threshold is an environment variable, `SEMANTIC_CACHE_THRESHOLD`, read once when a revision starts. No `make` target passes it, so trying 0.97 on a candidate takes `gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97`, with your region and project, and then the replay again.

The answers the replay stored stay in `answer_cache` for their day. The service's configuration says `SEMANTIC_CACHE=on` until the next deploy or candidate sets it back. Your two reports stay in your home folder: `~/cache93_curve.json` and `~/cache93_replay.json`.

### Why the cache is tuned this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Tight first, then measured. 0.95, not 0.92: a cache that answers "what is the notice period" to "what is the probation period" serves a wrong answer fast. The kit starts tight and keeps the switch off until a curve says otherwise.

- A false hit is worse than a miss. A miss costs a model call. A false hit returns a confident answer with real citations to a question it does not fit, and nothing on the page tells the reader. That is why the rule counts false hits, not the balance of the two rates.

- The exact rung needs no threshold. The same words, lower-cased and without punctuation, are found by two equality filters. Whatever the near rung's threshold, repeated questions still hit.

- The pairs are checked before they judge. A pair against a missing row, an unanswerable row or the wrong tenant, or identical to its golden question, would make the curve lie. `check_pairs()` refuses such a set, and so does `--selftest`, offline.

- Per tenant, always. Every lookup is filtered by tenant, so a threshold can only confuse one tenant's questions with each other, never with another tenant's.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The tool embeds with a fixed model. `cache_threshold.py` names `text-embedding-005` in its code, while the API reads `EMBEDDING_MODEL`. On a lane that declares another embedding model, the curve describes a model the cache does not use.

- No `make` target sets the threshold. Neither `make candidate` nor `make up` passes `SEMANTIC_CACHE_THRESHOLD`, so a measured value reaches a revision only by hand.

- The cache-hit alert is not created. `quota.tf` lists `cache_hit_low`, "documind/cache_hit_rate < 0.30 for 1h", in a map nothing reads, and no metric of that name exists. A cache that stopped paying for itself would go unnoticed.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`documind-api` has one more revision, which serves no traffic and has no tag. The service's configuration says `SEMANTIC_CACHE=on` until the next deploy sets it back, and `.candidate-revision` is gone. `answer_cache` holds the replay's answers until their day is up. Your home folder has two reports, and the log has the usage rows of about 65 questions. Lesson 6.5 turns from caches to memory: agent state, conversation history and knowledge, and where each one lives.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.4 Measure latency, avoided calls and false cache hits · v5.0

Next: Lesson 6.5 Distinguish agent state, conversation history and knowledge.
