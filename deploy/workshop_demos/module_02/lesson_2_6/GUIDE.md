# Lesson 2.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.6_System_One_WIX.html`, reviewed at blob `2c5ffaf4fdf36c282a1fd6ba68ee3e9c5728f9c4`. Learners read that page on the course site; this guide keeps its prose.

Lesson 2.5 rewrote the question before retrieval. This lesson decides what happens to the pool that retrieval hands back: answer from it, or refuse. The kit decides twice today. Code refuses an empty pool before any model runs, for nothing. Otherwise the generator reads the passages and may refuse by setting `answerable` to false, a refusal that has already paid for a full generator call. A decision could sit between rerank and generate instead: a System One model, which returns a typed decision with a calibrated probability rather than text. TypeSafe AI describes its Jev as one. It is the kit's first model that is not Google's, so it sits behind `JEV_MODE`, off by default, and in this course it is not on the request path at all. `evals/decide.py` asks three arms to decide every golden row from the same pool: the kit's evidence rule at Rs 0, the generator's own `answerable`, and Jev. It scores each against the golden set's truth, with Wilson intervals, calibration, latency and rupees. You will move the rule's floor across the 65 rows, ask a refusal row in the UI and see what it paid for, read the two refusals and the seam Jev would plug into, run the eval for Rs 0 and on your lane, and hold every arm against the gate's 0.90.

- Why decide before generating, and who may decide

- The words: decision, arm, evidence share, floor, two refusals, rates, Wilson, Brier, kappa, System One, JEV_MODE, skip

- Before you run anything: set up the shell

- A refusal in the UI, and what it paid for

- The kit's code: two refusals in the handler, and the evidence rule

- The decision eval for Rs 0, a higher floor, and Jev's switch

- The rule and the generator on your lane's pools

- Against the gate: refusal recall, false answers, calibration, latency and rupees

- Verify it yourself: the checklist

You will learn what an answer-or-refuse decision is, why the kit refuses twice today and what each refusal costs, how a rule, the generator and a System One model are measured against the same truth, and why Jev is measured offline here rather than put on the request path. Then you will prove it: ask a refusal row in the UI, run the decision eval for Rs 0 and on your lane, and read each arm's refusal recall against the gate's 0.90.

### Why decide before generating, and who may decide

A pool is not an answer, the kit's second refusal is its expensive one, three deciders can be held to one truth, and the third of them is not on the request path in this course.

Retrieval hands over a pool, and something must decide what to do with it. The golden set says what the right decision is for every row. Of its 65 rows, 47 are questions the tenant's documents answer and 18 are not. The 8 refusal rows ask for something no document of the tenant holds: ACME's sabbatical policy, its revenue in FY2024, the name of its CTO. The 10 isolation rows ask one tenant what only another tenant's documents say. A system that answers one of those 18 has written a false answer, and an isolation row answered is the worse kind, because the words came from somewhere the tenant's documents are not. A system that refuses one of the 47 has lost an answer someone needed. That makes the decision a classifier with a confusion matrix, and `evals/decide.py` scores it as one.

The kit decides twice today, and the second decision is the expensive one. When retrieval finds nothing, `empty_pool_answer()` writes the refusal in code: `answerable` false, backend `none`, no reranker, no model, Rs 0. When retrieval finds something, the reranker orders the pool and the generator reads it, and rule 3 of its system prompt lets it set `answerable` to false when the context does not contain the answer. A dense retriever always finds something: it returns the nearest neighbours of the question whether or not they answer it. So on your lane nearly every refusal is the model's, and the model's refusal is billed as a full call. For the sabbatical question, packed from the Rs 0 lane's five passages and counted the way the kit's packer counts, the prompt alone is about 1,822 tokens, before the model has thought about it. Lesson 3.5 compared the two refusals' envelopes. This lesson asks whether a cheaper decision could come first, and what it would cost in lost answers.

Three deciders, one pool. `decide.py` takes each golden row's pool from your lane's `/v1/passages`, which is `/v1/query` up to the reranker and nothing after it: the same door, roster, filters, guard, backend and rerank, then the passages, with no model. Three arms then decide on that pool. The rule is the kit's own code: the share of the question's information the pool carries, each content word weighted by its idf over the tenant's chunks, held against `EVIDENCE_FLOOR`, 0.5. It is the gate the Rs 0 lane has always applied, and it costs nothing and takes microseconds. The generator is `/v1/query` itself, asked as the eval gate asks it (top_k 6), and its decision is the `answerable` it returns. Jev is TypeSafe AI's System One model. By TypeSafe's own page in October 2026, it returns a typed decision (a choice, a score, a value between 0 and 1) with a calibrated probability instead of text. Those are the vendor's claims, not the kit's measurements, and measuring them is what the third arm is for.

What is measured, and why every rate carries an interval. Answer rate is the share of the 47 answerable rows an arm answered; refusal recall is the share of the 18 unanswerable rows it refused; accuracy is the share of all rows it decided right. Each is printed with its Wilson 95% interval, because 18 rows is a small sample: even 18 refusals out of 18 leave a lower bound of 82.4%. The live eval gate wants refusal recall of 0.90. An arm that gives a score is also checked for calibration: does a score of 0.8 mean right four times in five? Every arm is timed and priced per decision. And an error or a skipped row is never a refusal: it is counted on its own line and left out of every rate.

Jev is not on the request path in this course. It is the kit's first model that is not Google's, so it arrives behind three guards. `JEV_MODE` is off by default and makes no call. `recorded` mode reads `evals/system_one/recorded.jsonl`, which does not exist: no recording ships until one is made against TypeSafe's API, and none is written by hand. `live` mode would send only the tenants whose `data_region` is `any`, acme and zeta (57 of the 65 rows), with identifiers masked, and today it answers an error, because TypeSafe's adapter is a later pull request, 2.6-C, waiting on TypeSafe's documentation and terms. So wherever Jev's numbers would go, this page says Jev not available until the author's recording exists. The diagram shows where Jev would sit; in this course only `decide.py` calls it, offline.

The registry's scrutiny. A petition filed in a High Court goes first to the registry, which scrutinises it before any judge sees it: are the annexures there, is the court fee paid, is the affidavit sworn? A filing that lacks the papers to decide it is returned with objections, by a clerk, in minutes. A filing with no papers at all is not taken in at the counter. Everything else is listed, and the judge still rules: a listed matter can be dismissed after a full hearing, which has cost the court a morning. Scrutiny never decides the merits, and it is judged two ways: how many hopeless filings it stopped before they reached a bench, and how many sound ones it returned that deserved a hearing. Too strict, and litigants lose their day in court; too lax, and judges spend their mornings on filings that could never succeed. A court could even hand scrutiny to an agency outside the building, if its rules let the case files leave.

The empty filing is the empty pool, refused in code. The registry is the rule, or Jev, deciding before generation. The judge is the generator, whose rule 3 still refuses what it reads. Stopped hopeless filings are refusal recall; sound filings returned are lost answers. And whether the files may leave the building is a tenant's `data_region`.

#### The answer path: where each refusal is made, and the slot no code fills

The names are the kit's own, in the order `/v1/query` calls them; `generate()` lives in generator.py and the door in desk_door.py. Step 4 reads the two refusals in the code, and step 5 the switch that guards slot 6.

#### The rule's floor, on the 65 golden rows

The rule is the one arm that runs without a lane, so the bench below runs it on the kit's own corpus: each golden row's top 5 passages from the Rs 0 lane, which ranks the tenant's chunks by their words, and the evidence share `decide.py` computes for them, read with `decide.py`'s own `LocalLane` when this page was built. Move `EVIDENCE_FLOOR` and the confusion matrix, the three rates, the false answers and the per-shape table move with it, by the rule's own arithmetic: a pool whose share is under the floor is refused. The plot traces the rule as the floor rises, against the gate's line. The generator and Jev read no floor, so they appear on the plot and in the table as fixed, recorded points once the author's run exists, and are marked absent until then.

answer rate -refusal recall -accuracy -false answers (* an isolation row) -

The 20 rows the floor can move: their top 5 passages carry less than all of the question's information. Teal is a right decision at the current floor and orange a wrong one; the dark line in each bar is the floor.

- rf-05refusal, not answerable0.179

- rf-01refusal, not answerable0.299

- iso-02isolation, not answerable0.349

- rf-04refusal, not answerable0.396

- iso-04isolation, not answerable0.496

- lk-29lookup, answerable0.549

- jn-04join, answerable0.567

- iso-10isolation, not answerable0.608

- jn-07join, answerable0.609

- mm-04isolation, not answerable0.610

- lk-24lookup, answerable0.616

- rf-06refusal, not answerable0.617

- iso-07isolation, not answerable0.688

- jn-08join, answerable0.693

- jn-11join, answerable0.739

- rf-07refusal, not answerable0.793

- mm-01lookup, answerable0.793

- jn-03join, answerable0.793

- lk-30lookup, answerable0.833

- mm-03lookup, answerable0.872

The other 45 rows carry all of it, a share of 1.00: 37 answerable, and 8 that are not (rf-02, rf-03, iso-03*, iso-05*, iso-06*, iso-08*, iso-09*, mm-05; * an isolation row). The rule answers every one of them at every floor below 1, so on this lane no floor takes the rule past 10/18 = 55.6% [33.7%, 75.4%] refusal recall; from 0.80 upwards it holds that figure while answering 39/47 = 83.0% [69.9%, 91.1%] of the answerable rows.

Shares, verdicts and counts are `decide.py`'s, computed when this page was built, and the rates are printed by the kit's own `route_eval.rate()`. At 0.50 and 0.70 they equal the two runs in step 5, which the build checks. On your lane the pool comes from dense retrieval and the reranker, so its shares differ, and step 6 measures them.

It is not your lane and it is not Jev. The Rs 0 lane ranks words, so a row's pool here is not the pool your lane's index and reranker return, and a question can carry every word of its answer without being answered. A recorded point is the author's lane, on that lane's pools, and it does not move with the floor because neither the generator nor Jev reads one. Nothing on this bench calls a model.

### The words: decision, arm, evidence share, floor, two refusals, rates, Wilson, Brier, kappa, System One, JEV_MODE, skip

Thirteen rows, each with the value it takes on your lane.

One pair of words carries the lesson: lost answers and false answers. Every arm trades one for the other, the floor makes the trade visible, and the only fair comparison puts every arm on the same pool and the same truth.

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

### A refusal in the UI, and what it paid for

The golden set's first refusal row asked as yourself in the browser, its truth read from the golden file, and the same question through both routes from the shell.

rf-01 is the golden set's first refusal row: acme, asking for a sabbatical policy that no acme document holds. Its note in the golden file says how such a row is made. It asked about parental leave until the real Maternity Benefit Acts joined acme's corpus and made twenty-six weeks a defensible answer, so a refusal row has to ask for something the corpus really does not hold. On your lane the question still finds a pool, because a dense retriever returns the nearest neighbours of any question: passages near it in meaning that do not answer it. The reranker orders them, the generator reads them, and rule 3 makes it refuse. The refusal is right, and it is the expensive kind. The browser shows what a person sees; the shell shows the envelope behind it.

#### Do it: ask it in the UI

- Ask. Open `https://documind-ui-NUMBER.asia-south1.run.app` and sign in as yourself; the roster maps you to acme. On the Chat page, with the Brain set to `direct` if the sidebar offers a choice, ask: What is ACME's sabbatical policy?

- Read the reply. The words are the model's own, and they say that the documents do not cover a sabbatical. Below the reply, Sources lists the passages the model read, five unless the budget dropped one. The stream sends the packed passages as citations before its first token, so even a refusal arrives with sources it did not use.

- Read the sidebar. Under Cost this session, the USD figure shows the last turn's cost and the INR figure has grown with it. The page computes both from the tokens the stream reported, at flash's rates: the refusal was billed like an answer.

#### Do it: the golden row, and the same question from the shell

First the row's truth, from the file every eval reads:

Then the question as `documind-ui-sa`, through `/v1/query`, which generates, and `/v1/passages`, which stops at the reranker:

The generator refused: `answerable` False and no citations, after retrieve, rerank and a generate stage that took most of the request's time, with a full call's tokens. The answer's own `cost_usd` is null. On the default vertex backend `/v1/query` carries no price in its body; the usage row prices the call with cost.py, the UI priced it from the tokens, and the cell priced it with `shared/prices.py`. `/v1/passages` handed back the passages for the same question with model `none` and cost 0.0, and its `answerable` True means only that passages exist: the route stops at the reranker and decides nothing, which is the slot a decision would fill. The `pool` figure is the candidates the reranker saw; five of them went on.

One more thing is visible in the usage rows. Your browser question's row says `answerable` true: a `/v1/stream` row reads only whether the pool was empty, so the model's refusal on the UI path never reaches the unanswerable alert. The shell's `/v1/query` row says false.

### The kit's code: two refusals in the handler, and the evidence rule

The handler's branch, the empty pool's refusal, the generator's rule 3, the route that stops before the model, and the rule the Rs 0 lane gates on, worked by hand for three rows.

#### Definition

The handler's own branch is where the two refusals sit. After retrieval, `/v1/query` checks three cases in order: an answer-cache hit, which skips the reranker and the model; an empty pool, which `empty_pool_answer()` refuses in the contract's shape with zero tokens; and everything else, which is reranked and then generated. Slot 6 of the diagram is the line between `rerank()` and `generate()`: a decision there would let a refusal be written without the generator, at whatever the decider charges. Rule 3 of `SYSTEM` is the generator's refusal. `/v1/passages` is the handler up to the reranker, which is why `decide.py` takes its pools there: every arm decides on the passages the reranker kept, and no model runs to fetch them.

The rule is older than this lesson. `shared/documind_tools.py`'s Rs 0 lane gates every retrieval with it. `_lexical_rank()` scores the tenant's chunks with BM25 and returns the idf of the question's content words; a word found in more than half of the tenant's chunks is dropped, because a match on it says nothing. The pool must then carry at least `EVIDENCE_FLOOR` of the remaining information, counting the top passages together (the "set" mode), or the lane returns nothing. `decide.py`'s rule arm applies the same arithmetic to any pool, your lane's included: `evidence_share()` over the pool's text, then `rule_arm()` against the floor. The cell works it by hand for three rows and prints each word's weight.

#### The code

#### Do it: the rule's arithmetic on three rows

rf-01's heaviest word, sabbatical, is in no chunk of acme's, so it carries the most weight in the question, and the pool holds only policy: a share of 0.30, under the floor. The rule refuses before any model is asked, as the generator refused after reading. rf-02 is the warning. All three of its content words are in the pool, the share is 1.00, and the rule answers a question the corpus cannot answer: casual is there only as the CGST Act's casual taxable person and leave as the handbook's earned leave, and the handbook grants no casual leave. The rule measures whether the question's words are present, never whether they answer it. lk-01 carries all five of its words and is answered, rightly. A floor can move a row like rf-01 across the line; no floor can move rf-02, which is why a decision model is worth measuring at all.

### The decision eval for Rs 0, a higher floor, and Jev's switch

The whole eval with the lane taken away, the same run at 0.70, and every mode of Jev's switch called by hand, none of it leaving the machine.

#### Definition

`decide.py --local` is the whole eval with the lane taken away. The pool comes from the kit's corpus on the Rs 0 lane, the way `tools/check_local_lane.py` runs it: `documind_tools.retrieve(passages=True)` on the local profile over the chunks the local corpus would seed, top 5. That lane's own gate is the evidence rule at `--floor`, so on it an empty pool is the rule's refusal, and `decide.py` answers what the lane served. The generator needs a lane and says so; Jev is off and says that too. `decide_row()` is where the arms meet: a pool that failed is an error for every arm, an empty pool is refused in code and asks no model, and Jev is always called through `system_one.decide()`, which decides for itself whether to do anything. `summarise()` turns the rows into the confusion matrix and the three rates, with errors and skips counted apart.

#### The code

#### Do it: all 65 rows, Rs 0

At 0.50 the rule answered every answerable row, 47/47 = 100.0% [92.4%, 100.0%], and refused 5 of the 18 it should have: refusal recall 5/18 = 27.8% [12.5%, 50.9%], under the gate's 0.90 with the whole interval. All 5 refusals were empty pools at the lane's gate, which is why the report counts them as decided by code. The 13 false answers (rf-02, rf-03, iso-03*, iso-05*, rf-06, iso-06*, iso-07*, rf-07, iso-08*, iso-09*, iso-10*, mm-04*, mm-05) are rows whose top passages carry at least half of the question's information, 8 of them all of it, rf-02's casual leave among them. The Brier score of 0.182 grades the share as if it were a probability, which it is not; the bins say the same more plainly, with 47 rows in the top bin and 8 of them not answerable. Every rate is the rule's alone: the other two arms said why they did not decide, and decided nothing.

#### Change it: a higher floor

Raise the floor and the rule buys refusals with answers. The same run at 0.70:

Refusal recall rose to 9/18 = 50.0% [29.0%, 71.0%] and the answer rate fell to 42/47 = 89.4% [77.4%, 95.4%]: 5 answerable rows are now refused (jn-04, jn-07, jn-08, lk-24, lk-29), most of them joins, whose answer is spread across passages that each carry only part of the question's words. Accuracy went from 52/65 = 80.0% [68.7%, 87.9%] to 51/65 = 78.5% [67.0%, 86.7%]. The bench in step 1 shows the rest of the trade: from 0.80 upwards nothing more is refused, because the 8 unanswerable rows at a share of 1.00 carry every word they ask with, and the rule's best on this lane is 10/18 = 55.6% [33.7%, 75.4%].

#### Jev's switch, called by hand

`shared/system_one.py` is the only door to Jev, and `decide()` its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's `data_region` first, failing closed to `in`, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: `_headers()`, `_request()` and `_parse()`, which PR 2.6-C fills once TypeSafe documents its API. Until then `_request()` raises before any key is read or any socket opens, and `decide()` turns that into an error row, which no rate counts as a refusal.

Run the Rs 0 eval with `JEV_MODE=recorded` on zeta's 10 rows, then call `decide()` in each mode, with the data regions `make roster` writes standing in for the Firestore read:

Recorded mode named the file it looked for and why it is absent, and skipped every row that had a pool: a skip, never a refusal, so Jev's line reads not available. The bracket on that line counts the one row Jev was never asked about: iso-04, whose pool the Rs 0 lane's gate emptied, refused in code as it is for every arm. The four calls walked the switch. Off sent nothing. Recorded found no file. Live for globex stopped at the policy, because globex's `data_region` is `in` and Jev's region is undocumented. Live for acme passed the policy, masked the invoice's PAN, had the question and one passage ready, and stopped at the seam with `TypeSafe adapter not configured (PR 2.6-C)`: an error, and nothing left the machine.

The last lines show what the mask does not cover. The invoice's GSTIN fails its own check character, so the finder does not take it for a GSTIN, and the contact number and the email address are not among the four identifiers the kit masks. A live call would have carried all three. That is one reason the question of which tenants may be sent to Jev is still open (step 7).

### The rule and the generator on your lane's pools

make decide against your lane: the pools from /v1/passages, the generator's own decisions from /v1/query, Jev off, zeta's ten rows kept for a replay that costs nothing.

#### Definition

`make decide` is one line of `mk/retrieval.mk`, and the same eval as step 5 with the lane put back. With `--project`, `decide.py` asks gcloud for the project number and builds the API's address. The pools come from `/v1/passages` through `documind_tools.retrieve(passages=True)`, minted as `documind-ui-sa`, the identity `make eval-live` uses. The generator's decisions come from `/v1/query` through `run_eval.ask()`, asked as the eval gate asks it, with top_k 6: one passage more than the pool the other two arms read, which the report's header says. `JEV_MODE` stays off unless you set it, and the key, when there is one, will be `JEV_API_KEY` in your shell and never a make variable.

This run takes zeta's rows: 10 of them, 5 answerable and 5 isolation rows that are not, so both rates have rows to count. `--limit 10` would take the golden file's first ten rows, which are all answerable lookups, and print a refusal recall of 0/0. zeta's pool comes from whichever store `make up` pinned it to. `--save` keeps every row's pool and decisions under `evals/reports/`, which the kit's `.gitignore` keeps out of git, and `--from` replays a saved run for Rs 0 with no lane: `python evals/decide.py --from evals/reports/decide-zeta.json --floor 0.7` re-scores the rule on your own lane's pools, with the generator's decisions as they were saved.

#### The code

#### Do it: zeta's rows on your lane

The rule decided each of zeta's rows from your lane's pool, with the corpus's idf, and the generator decided each from its own answer. Three lines are worth reading. The rows where the arms disagree are the ones to open: a row the rule answered and the generator refused is a pool that carries the question's words without its answer, and a row the generator answered and the rule refused is an answer the floor would have cost you. Kappa says how much of the arms' agreement is more than chance. And the generator's rupee line is priced from its tokens: `/v1/query` fills `cost_usd` only when the gateway priced the answer or no model ran, so for a Gemini answer it is null, as step 3 showed, and `decide.py` prices that answer's tokens at `shared/prices.py`'s list price, as `cost.py` prices the usage row.

### Against the gate: refusal recall, false answers, calibration, latency and rupees

All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort.

The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by `decide.py`'s own `summarise()`, `calibration()`, `by_confidence()` and `latency()`. The same command runs on your lane if you want your own.

#### Refusal recall against the gate's 0.90

The live eval gate refuses a release whose refusal rate is under 0.90. Refusal recall is the same quantity measured on the decision alone, so it can be held against the same line:

With 18 unanswerable rows, the gate is a point estimate and nothing more. Even a perfect 18 of 18 has a Wilson lower bound of 82.4%, so no arm can show on this set that its refusal recall is above 0.90 with 95% confidence. A fair comparison reads the intervals side by side and asks whether they overlap before it calls one arm better.

#### The false answers, by id

An isolation row in that list is the one to read first: a tenant was asked about a document it does not hold, and the arm answered anyway.

#### Calibration, latency and rupees

The generator's rupees are its tokens at `shared/prices.py`'s list price, as `decide.py`'s own line prices them (step 6): gemini-3.6-flash at USD 1.50 in and USD 7.50 out per million tokens, and 85 rupees to the dollar. Jev's are priced at TypeSafe's page rate, USD 42 per billion input tokens, and never at `shared/prices.py`'s, which would bill an unknown model at flash's rate; a decision that reports output tokens is left unpriced, because the page names no output price. On the Rs 0 lane's pools, the 57 rows Jev could be sent come to about 90,629 tokens by the kit's own count, about Rs 0.32 at that rate for all of them: the price is not what decides whether Jev belongs on the path.

#### Refusing first: what it would save, and what it would lose

Put a decider in slot 6 and the generator is skipped on every row it refuses. The saved run says what that would have meant on the author's lane, row by row:

- [awaiting the author's run: data/decide_run.json]

- Jev not available: JEV_MODE is off, TypeSafe's adapter is PR 2.6-C, and no recording exists.

Read the lines together. A decider earns its slot only if the generator calls it saves are worth more than the answers it loses, and an isolation row it stops counts for more than either.

#### Where Jev could sit after 6 December

In this course Jev is not on the request path, and nothing on your lane changes when the eval runs. For after the cohort, the lesson plan names one next step: Jev between rerank and generate behind a switch, `off`, `shadow` or `enforce`. Off is today. Shadow would ask Jev on every request beside the generator and log its decision without acting on it, which is this lesson's eval run on live traffic. Enforce would write Jev's refusals in place of a generator call, the way `empty_pool_answer()` writes the empty pool's. The kit has none of it yet, and the step from shadow to enforce is the one this lesson's numbers would have to justify.

#### Whether a tenant's text may go to Jev

The kit's live mode sends a tenant only when its `data_region` is `any`, and that reading is not settled. `any` was written for Google's managed stores: `shared/tenancy.py`'s own comment says it means a managed store may hold a copy. TypeSafe's API runs outside Google Cloud, its retention and its hosting region are undocumented, and where it processes and keeps data is one of the terms asked of it. Masking covers four identifiers, and step 5 showed what it lets through. Until those terms are known, whether `any` covers a vendor outside Google Cloud is an open decision for the course, and the only Jev data this page will show is the author's own recording.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it.

Nothing deployed, and no setting changed. Your browser question, the shell's question and `make decide`'s generator calls are usage rows, `event` stream or query; the `/v1/passages` calls are rows of their own with no tokens and no cost. The saved run is `evals/reports/decide-zeta.json` inside the kit's clone, which git ignores; it is yours to keep or delete. No `JEV_MODE` was set in your shell, so Jev made no call, and the switch cell's recorded line only looked for a file that is not there. acme's pin goes back with the setup section's window, when you finish. Module 3 takes the pool into the prompt, and lesson 3.1 starts with the generator's own run-to-run variance.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.6 Decide answer-or-refuse with a System One model (Jev) · v5.0

Next: Lesson 3.1 See run-to-run variance and thinking levels in the same prompt.
