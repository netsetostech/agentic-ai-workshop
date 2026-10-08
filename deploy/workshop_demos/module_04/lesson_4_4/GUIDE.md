# Lesson 4.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.4_Controlled_Change_WIX.html`, reviewed at blob `97d97638098f6e3f140aba7bc44e9edda7bc2aa0`. Learners read that page on the course site; this guide keeps its prose.

Lesson 4.2 measured the revision that serves today. This lesson changes one thing and measures the difference. You make a candidate revision of the API with a cheaper model behind it and no traffic, and prove from both revisions' settings that the model is the only difference. You run the live gate on the rows that cite the handbook against both, ask the pairwise judge which answers are better, and read the price of the difference off the usage rows. Then you remove the candidate's tag, because an experiment is not a release.

- One change, one baseline, the same questions

- The words: baseline, candidate, tag, template, controlled change, scoped gate, pairwise, win rate, rupee delta, ablation

- Before you run anything: set up the shell

- The candidate: a new revision with no traffic, and the proof that one setting differs

- The scoped gate on both revisions, and the rows that moved

- The pairwise judge: which answer is better, row by row

- The rupee delta, from the usage rows

- Retrieval-only changes: measure retrieval first, with no model

- Deciding, the confounds that fake a result, and removing the candidate

- Verify it yourself: the checklist

You will learn what makes a comparison controlled: one setting changed, a baseline that stays put, the same questions for both, and a check that nothing else moved. You will learn which instrument answers which question about the change, and how to read a pairwise verdict. Then you will prove it on your lane: a candidate with a cheaper model, a diff of the two revisions' settings, the scoped gate on both, the pairwise win rates, and the rupees each answer saves.

### One change, one baseline, the same questions

A comparison names a cause only when one thing differs, and only a diff of the settings proves that.

A comparison can name a cause only when one thing differs. The baseline is the revision serving today. The candidate is the same image and the same settings with one value changed, taking no traffic, reachable at its own tagged URL. Everything else is held still: the golden rows, the corpus, the retrieval and the hour. Then any difference in the gate's rates, the judge's verdict or the price belongs to that one value. Change two values and the numbers still move, but nobody can say which change moved them.

A candidate costs nothing to try and nothing to abandon. Users keep the live revision the whole time. The candidate answers only requests sent to its own URL. The kit's config says every switch is judged this way first: the ledger's current-only retrieval, the knowledge graph, Model Armor, the answer cache. Shipping would be lesson 4.2's release path: the full gate on the candidate, a person, then a traffic flip by name. This lesson stops before that and removes the tag.

Three measurements answer three questions about the change. The scoped live gate asks whether the candidate still clears the thresholds on the rows the change can reach, in minutes rather than the full set's ten. The pairwise judge reads both answers to each question and says which is better, so its verdict is about the difference itself. The usage rows price every answer by the model that gave it, so the rupee delta is measured, not estimated. For a change that touches only retrieval, generation is noise and money: `make ablate` measures retrieval arms with no model at all.

"One change" is a claim you have to check. `make candidate` writes eleven settings onto the service's latest template, taking each from the Makefile's defaults or from your shell, where an exported variable wins. Settings merge across revisions, so a value an earlier experiment left on the latest template rides along into the new revision. The only proof is a diff of the candidate's settings against the revision that serves traffic.

A chai stall trying a cheaper tea powder. The owner makes two cups with the same water, milk, sugar and boiling time; only the powder changes. The regulars taste both cups side by side and say which is better, or that they cannot tell. The owner prices both powders per hundred cups. If the milk changed too, nobody could say which change the regulars tasted. The live revision is today's cup, the candidate is the new powder, the pairwise judge is the regulars, and the usage rows are the owner's price list.

#### The comparison planner: is it one change, what measures it, and what the model change costs

The left column is what the live API runs by default, which is what `make candidate` writes too. Set the candidate's values, then the token counts from your own usage rows. The planner counts the changes, names the instrument for each, and prices the model change with the kit's own rates.

The defaults are the Makefile's, and the build checked that the API is deployed with the same ones (`commands/lesson-12.2.sh`). The price is `cost.price()` from the API, ported and checked against it: its three Gemini rates, cached input at a tenth, 85 rupees to the dollar.

It cannot see your lane. If your live revision was deployed with other values, the left column is wrong for you; step 3's cell diffs the real revisions. The price uses the rates in `cost.py`; the API reads a price table in BigQuery first when one exists, so the usage rows are the bill.

### The words: baseline, candidate, tag, template, controlled change, scoped gate, pairwise, win rate, rupee delta, ablation

Ten rows, each with the value it takes on your lane.

One distinction to hold: a candidate is not a release. The candidate exists to be measured, and removing its tag ends the experiment without touching users. A release is the traffic flip that follows a green gate and a person's approval.

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

The shell, in the kit's folder, with `NUMBER`, `REGION` and the token functions from the setup block, and the judge's venv from lesson 4.2, step 5. If that venv is gone, its three lines make it again. Steps 3 to 6 run back to back in about twenty minutes, so both revisions are measured in the same hour.

### The candidate: a new revision with no traffic, and the proof that one setting differs

The target that makes it, the kit's rule that every switch is judged this way, and a diff of the two revisions.

#### Definition

`make candidate` runs one `gcloud run services update` with `--no-traffic` and `--tag candidate`. It writes eleven settings, and removes `GENERATOR_LOCATION` unless you give one. Here the only override is `GENERATOR_MODEL=gemini-3.1-flash-lite`, the kit's cheap-bulk model, served like the default on the global endpoint and priced from the same table. A model name needs no `RAG_MODEL_BASE` change; that setting only prices a tuned endpoint. The target then records the new revision's name and prints its URL. The candidate's token is the same one the gate uses, because the API checks every token against its canonical URL, whichever URL was called.

#### The code

#### Do it: the candidate

#### Do it: prove it is one change

The cell finds the revision serving traffic and the one tagged `candidate`, reads both revisions' settings, and prints every setting that differs.

Cloud Run made a revision from the service's latest template with eleven settings written over it, and gave it no traffic and its own URL. Users are still on the live revision. The diff compared the candidate with the revision that serves traffic, not with the template, because the template is where a forgotten setting would hide. One line means one change. If you see more, the extra lines name the settings to put back: pass the live value on the `make candidate` line, or unset the shell variable that carried it in, and make the candidate again.

### The scoped gate on both revisions, and the rows that moved

The same 10 rows on each side, the thresholds that have rows behind them, and a row-by-row comparison.

#### Definition

`SOURCE=hr_policy_2026.md` scopes the live gate to the rows that cite the handbook: a slug in `must_retrieve`, or the row's own `source`. A model change can reach any answer, so the handbook's rows are a sample, chosen because they run in a few minutes. A reindex of one document is judged the same way. Refusal, media and isolation rows do not cite the handbook, so those three thresholds have no rows behind them and are printed without a verdict. The baseline runs first with `tail`, so you see its verdict. The candidate runs in full, pointed at `$CAND` with the same token.

#### The code

#### Do it: the gate on the live revision, then on the candidate

Now set the two reports side by side: each judged threshold on both revisions, every row whose verdict changed, and the median round trip of each.

Both revisions answered the same 10 questions within minutes of each other. The gate judged six thresholds and left three without a verdict, because a scoped run holds no refusal, media or isolation row. In the stub's run, the candidate missed one figure and still cleared every threshold. That is the point of reading the rows and not only the verdict: a green gate says the candidate may ship, and the moved row says what it would cost. The latency line is the third measurement you get for free, since a smaller model usually answers faster.

### The pairwise judge: which answer is better, row by row

Both revisions answer the same twenty questions, the candidate is rated, and the judge picks a side or calls a tie.

#### Definition

With `API_B`, the judge collects answers from the live revision and then from the candidate, for the same rows. It rates the candidate's answers for groundedness and instruction following, as in lesson 4.2. It also adds one pairwise metric, question-answering quality, where the judge model reads both answers to each question and chooses the candidate, the baseline, or neither. The SDK turns those choices into two win rates, and a tie counts for neither side. `--rows 20` keeps the run to the first twenty golden rows, thirteen lookups and seven joins, which is enough to see a direction for a fraction of the full run's cost. The run's name ends in `-vs-candidate` and the template hash.

#### The code

#### Do it

Forty answers came back, twenty from each revision, and the Evaluation service made 60 ratings: two pointwise and one pairwise for every row. Read the two win rates together. A candidate win rate near the baseline's, with many ties, says the cheaper model answers these questions about as well. A baseline win rate well above the candidate's says you would be buying the saving with quality. The pointwise lines describe the candidate alone, so compare them with lesson 4.2's run of the live revision. None of these numbers gates anything: step 4's gate decides whether the candidate may ship.

### The rupee delta, from the usage rows

Every answer of the last hour, grouped by the model that gave it, and the difference per answer.

The API priced every answer on its usage row with `cost.price()`, at the rates of the model that answered. The gate's runs and the judge's collections asked both revisions the same questions, so the two groups are like for like. The cell groups the last hour's rows by model and divides.

The usage rows priced about 60 answers, half on each model. The delta is measured, not estimated: the same questions, the same context, only the model's rates and the model's own token counts differ. For a sense of scale, an answer of 2,000 tokens in and 300 out costs Rs 0.4463 on flash and Rs 0.0808 on flash-lite, at the kit's rates: Rs 366 saved per thousand answers. Multiply your delta by your monthly volume, and set it beside step 5's win rates. That pair, the verdict and the rupees, is this lesson's proof.

### Retrieval-only changes: measure retrieval first, with no model

Which instrument fits which kind of change, and why a retrieval change starts with the ablation.

A model change needs the gate and the judge, because only answers show it. A change that touches only retrieval is different: the current-only filter, the knowledge graph, another store as `RETRIEVAL_BACKEND`. Its effect is on which chunks reach the model, and the golden anchors measure that directly. `make ablate`, lesson 2.2's harness, runs retrieval arms against the anchors with no model in the loop, so it is cheap and repeatable. The Makefile's own advice for a new retrieval backend is to run the ablation first and then judge a candidate. Only an arm that retrieves better earns a candidate, the scoped gate and a judge.

### Deciding, the confounds that fake a result, and removing the candidate

What the three measurements decide together, five ways a comparison lies, and the end of the experiment.

#### Deciding

The gate decides whether the candidate may ship. The scoped gate is a first look. Before any release, lesson 4.2's path runs the full gate on the candidate, then a person approves, then `make promote` moves traffic by name. The judge's win rates say what you trade, and the usage rows say what you save. A cheaper model that clears the full gate, and loses no more rows than it wins, is a saving you can defend with numbers.

#### Confounds: five ways a comparison fakes a result

- A second setting on the template. A value an earlier experiment left on the latest template rides into the candidate. Step 3's diff against the serving revision catches it.

- A variable in your shell. Make prefers an exported variable to its own default, and earlier lessons exported the API's settings. They usually match the live values; the diff proves it.

- The answer cache. With `SEMANTIC_CACHE=on` on either side, a repeated question replays an earlier answer at no cost, and both the judge and the price compare replays.

- Time. A reindex between the two runs changes the corpus under one side. Run both in the same sitting.

- Different questions. A delta per answer over different question sets compares the questions, not the models. Every step here asks both sides the same rows.

#### Do it: remove the candidate's tag

This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: `make promote` refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in `.candidate-revision`. Deleting that file makes `make promote` stop with an error instead.

#### What it costs

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

One more `documind-api` revision in the service's history, with no traffic and no tag; step 8 deleted the file that named it. Two reports, `evals/reports/base73.json` and `cand73.json`, also ignored. The usage rows of about 60 answers, and one Experiments run in `documind-eval` whose name ends in `-vs-candidate` and the template hash. The golden set is sound, the gate judges a deployment, the judge explains, and a change is measured against its baseline. Lesson 4.5 checks the judge against people, and lesson 4.6 turns to security, starting with how an authenticated identity becomes a tenant.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.4 Compare one controlled change against a baseline · v5.0

Next: Lesson 4.5 Check the LLM judge against people.
