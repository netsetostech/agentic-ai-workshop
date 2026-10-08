# Lesson 12.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_12.3_Tuned_Candidate_WIX.html`, reviewed at blob `b2fefa0d8707ac518698fb9851e542583dd1762a`. Learners read that page on the course site; this guide keeps its prose.

Lesson 12.2 left a tuned endpoint. This lesson puts it behind the API on a candidate revision that takes no traffic, and compares that revision with the live one on the same questions, in the same hour. The method is lesson 4.4's. What is new is what can contaminate the comparison when the candidate is a tuned model, and how the price of its answers is counted.

In this lesson you prove that the candidate differs from the live revision only by its model and that model's price base. You check that no cache and no training row can hand the candidate an answer it did not earn. Then you run the gate on both revisions, ask the pairwise judge which answers are better, and read the rupee delta off the usage rows, at the price Google bills.

- What makes a tuned comparison uncontaminated

- The words: baseline, candidate, one change, RAG_MODEL_BASE, contamination, the answer cache, the chapter's gate, the pairwise verdict, the rupee delta, the tenant pin

- Before you run anything: set up the shell

- What the kit does with a tuned candidate

- The candidate, audited

- The gate on both revisions

- The verdict and the delta

- Optional: the v3 candidate, and the gate on it

- Optional: one question, two models

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn the four ways a comparison with a tuned model can be contaminated, and how to rule each one out on your lane. You will learn why the model and its price base are one change, and why the usage rows understate what the tuned model costs. Then you will prove it on your lane: the pairwise verdict, and the rupee delta.

### What makes a tuned comparison uncontaminated

Lesson 4.4's method, and the four things a tuned model adds to it.

The comparison, as lesson 4.4 made it. The baseline is the revision serving today. The candidate is the same image with the same settings and one value changed, taking no traffic, reachable at its own tagged URL. Both answer the same golden rows in the same hour. The gate runs on both, the pairwise judge reads both answers to each question, and the usage rows price both. Any difference then belongs to the one value.

What a tuned model adds. Four things can make that comparison lie, and each has a check:

- One change is two settings. The usage rows price a tuned endpoint at `RAG_MODEL_BASE`'s rates, so the model and its price base move together. Leave the base out and it stays at the Makefile's `gemini-3.6-flash`: the tuned endpoint's answers are then logged at flash's rates.

- The test must be unseen. A tuned model has read its training file. If golden rows, or the chunks they are scored against, were in that file, the gate would measure memory. `exclude_golden` dropped 15 rows from v2, touching 9 golden rows. The audit checks the file the endpoint was tuned on against today's golden set.

- No cache may answer for the candidate. The answer cache returns a stored answer for a near-enough earlier question of the same tenant. Its test checks the corpus, the scope and the expiry, and never the model. With the cache on, the candidate could be served `gemini-3.6-flash`'s stored answer to a golden question, which every eval run asks, and be scored as if it were its own. `make candidate` writes `SEMANTIC_CACHE=off` unless you say otherwise.

- The same input price. A context cache belongs to one model. The live revision can read acme's, and the tuned endpoint cannot. Cached tokens cost a tenth, so the baseline would look cheaper than it is next to the candidate.

Then the price itself. From Gemini 3 onward, Google prices a tuned endpoint's predictions at 1.5 times its base's. The usage rows log the base rate (`cost.py`), so the delta must add the 1.5.

The two proofs. The pairwise verdict is two win rates, the candidate's and the baseline's; a tie counts for neither. The rupee delta is the live revision's cost per answer minus the candidate's at Google's price, from the usage rows these runs leave.

Who decides. The gate decides whether the candidate may ship, and this chapter's gate is that the tuned candidate passes `make eval-live`. The judge says which answers are better where the two differ. The delta says what the difference is worth.

A coaching class's claim, checked by the principal. The coaching class says its student will write as well as the school topper, for a quarter of the fees. The principal checks before believing it. Both sit the same paper in the same hour, in the same hall. The student never saw this paper during coaching. Nobody slips the topper's old answer sheet into the student's desk. And the fee compared is what the class actually charges, not the one in its brochure.

Then an examiner marks both scripts against the answer key, and the student must pass. A second examiner reads the two answers to each question side by side, and picks the better one or calls it even. The accountant works out the saving.

The student is the tuned candidate and the topper is the baseline. The paper is the golden set, and seeing it in coaching is contamination through the training file. The old answer sheet is the answer cache, and the brochure fee is the base rate the usage rows log. The first examiner is the gate, the second is the pairwise judge, and the saving is the rupee delta.

#### Make a candidate, and see what the comparison would be worth

Choose how the candidate is made and what the live revision runs. The first box shows the settings that would differ, and whether anything could contaminate the comparison. The second shows the price of an answer on each revision, as the usage rows log it and as Google bills it, and the delta at the volume you pick.

The rules are the kit's: `make candidate`'s eleven settings, parsed from the Makefile, and `cost.price()`, ported and compared with the kit's own on all 24 combinations. The tokens are this page's averages: 7,400 in for both revisions, 210 out on flash and 140 on the tuned endpoint. The 1.5 is Google's, checked on 24 September 2026.

It takes the live revision's settings to be the Makefile's defaults. Step 4's audit reads your live revision's real settings, and any that differ from the defaults show up there as extra lines.

### The words: baseline, candidate, one change, RAG_MODEL_BASE, contamination, the answer cache, the chapter's gate, the pairwise verdict, the rupee delta, the tenant pin

Ten rows, each with the value it takes on your lane.

One distinction to hold: the gate decides and the judge explains, as `judge.py`'s last line says. A candidate that fails the gate does not ship, whatever the judge prefers. A candidate that passes may still give the worse answer where the two differ, and the win rates say how often.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and the `tok` function set by the setup above, and lesson 12.2's endpoint.

- Lesson 12.2's two logs. `~/poll172.log` holds the endpoint, which step 4 reads if `ENDPOINT` is not set. `~/tune172.log` holds the file the endpoint was tuned on, which the audit checks.

- The judge's venv from lesson 4.2. `~/judge-venv`, with the Evaluation SDK and pandas. If it is gone, lesson 4.2's three lines make it again.

- Two hours. Run steps 4 to 6 back to back, so that both revisions are measured in the same window and step 6's two hours of usage rows cover every run.

- What the lesson changes. It makes a candidate revision with no traffic and removes its address at the end. It writes two reports in your home folder and one Experiments run, and leaves the usage rows of the answers. Nothing is promoted.

### What the kit does with a tuned candidate

The answer cache's test, the endpoint's price three ways, and make usage's model column. Offline.

#### Definition

The cell runs three pieces of the kit on made-up inputs:

- It lifts the answer cache's test out of `semantic_cache.py`, and asks whether an answer `gemini-3.6-flash` stored is alive for a lookup made for the tuned endpoint.

- It prices one answer on the tuned endpoint with `cost.price()`, once with the right base and once with the Makefile's default, and then as Google bills it.

- It prints `make usage`'s table for one answer on each model.

#### The code

#### Do it

- The cache's test passed an answer for the wrong model. It compares the corpus fingerprint, the scope and the expiry. Every entry records the model that gave it, and nothing reads that field.

- One answer, three prices. `cost.py` says Rs 0.1764 with the right base, and Rs 1.0391 if the Makefile's default is left in place. Google bills Rs 0.2646. Only the last is the bill.

- `make usage` shows the tuned endpoint as `projects/NUMBER/loca`. The model column is cut at twenty characters, so every endpoint looks alike.

### The candidate, audited

make candidate with the endpoint and its base, then four checks that nothing else can answer for it.

#### Definition

`make candidate` runs one `gcloud run services update` with `--no-traffic` and `--tag candidate`. It writes eleven settings, and removes `GENERATOR_LOCATION` unless you give one, so the endpoint is called where its path says (lesson 12.2):

The cell passes the endpoint and its base. The other nine settings take the Makefile's defaults, which is why lesson 4.4's diff comes next.

#### Do it: the candidate

#### Do it: the audit

The cell makes the four checks from step 1:

- It diffs the settings of the revision serving traffic against the candidate's.

- It reads the answer cache's switch on both revisions.

- It finds the training file in `~/tune172.log`, reads that file from the bucket, and runs today's golden set over its rows.

- It looks for acme's context cache in Firestore.

- Two settings differ: the model and its price base. That is one change. If you see more lines, they name the settings to put back: pass the live value on the `make candidate` line, or unset the shell variable that carried it in, then make the candidate again (lesson 4.4).

- The answer cache is off on both revisions, so every answer in this comparison is generated in this hour.

- The test set never entered the file. Building v2 dropped 15 rows written from the evidence or the questions of 9 golden rows: jn-10, jn-11, lk-14, lk-17, lk-18, lk-23, lk-24, lk-26, lk-28. Today's golden set drops none. The only record of which file the endpoint learned from is `~/tune172.log` (lesson 12.2).

- acme has no context cache, so both revisions pay the full price for their input.

### The gate on both revisions

Every golden row on each side, then the rows that moved. The chapter's gate: the candidate passes.

#### Definition

Lesson 4.4 scoped its gates to the handbook's rows. A tuned model can change any answer, so this gate runs every golden row: first on the live revision, then on the candidate. The comparison cell then reads the two reports, prints each judged rate side by side, and lists every row whose verdict moved.

#### Do it

- Both revisions pass every threshold. That is the chapter's gate: the tuned candidate passes `make eval-live`.

- Three rows moved. On the stand-in, `jn-06` now passes, because the candidate states both figures it needs. `jn-03` and `jn-09` now fail: each answer gives one of the two figures its join needs. That is a habit the training rows could teach: each showed a single source (lesson 12.1), and a join needs two. Read your own moved rows the same way.

- The rates barely move: `must_contain_rate` and `correct_rate` each drop about two points, both far above their lines. The rows say where the difference is.

### The verdict and the delta

The pairwise judge on every row, the usage rows by model, the decision, and the candidate's tag removed.

#### Definition

With `API_B`, the judge collects every golden row's answer from the live revision, then from the candidate. The candidate is judged and the live revision is the baseline:

For each row, the Evaluation service's judge reads both answers and chooses the candidate, the baseline, or neither. The SDK turns those choices into two win rates, and a tie counts for neither side. It also rates the candidate alone for groundedness and instruction following, as in lesson 4.2.

#### Do it: the verdict

The pairwise verdict: the candidate wins 0.015 of the rows, and the baseline 0.031. On the stand-in the judge chose the candidate on 1 row and the baseline on 2, the same joins the gate moved, and called the other 62 even. That is the first proof. The pointwise lines describe the candidate alone.

#### Do it: the delta

The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints `make usage`'s model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

- The rupee delta: each answer on the tuned endpoint costs Rs 0.8079 less, Rs 808 per 1,000 answers, at Google's price. That is the second proof.

- The usage rows alone would claim more. They log the candidate at Rs 0.1761 an answer, where Google bills Rs 0.2641.

- `make usage` names the endpoint `projects/NUMBER/loca`. The cell groups by the full path.

#### The decision, and the candidate's tag

The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:

- Promote it: `make promote` moves all traffic to the recorded candidate by name, and `make rollback` returns it. The tuned model then answers every tenant, and it was trained on acme's corpus.

- Pin it to acme: the API reads `tenant_settings/acme.generator_model` before the service's model. No target writes that field (step 9):

- Keep the live model, and remove the candidate's address. The lane's path is this one:

The revision stays in the service's list, with no traffic and no URL. The tuned endpoint stays too, billed only when it answers.

### Optional: the v3 candidate, and the gate on it

If you tuned v3 in lesson 12.2's step 7: its endpoint behind the candidate address, then every golden row on it.

Steps 4 to 6 compared the v2 model with the live one. Its answers were about the same, some worse on the joins, for a quarter of the price. v3 was built to be worth showing. Its rows are the served prompt, its answers mark their source, and it answers in the house style and in the language it is asked in. This step puts its endpoint behind the candidate address, as step 4 did for v2, and step 8 asks it questions next to the live model.

`make candidate` writes the tag again, so the candidate URL now answers with v3's endpoint. The live revision keeps all the traffic, and so does the UI, which only calls the service's own URL. Step 4's audit holds here too: lesson 12.1's step 7 and lesson 12.2's step 7 checked that the file v3 learned from holds no golden row, and no golden evidence in any prompt.

#### Do it

Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:

- The candidate URL serves v3. `GENERATOR_MODEL` names lesson 12.2's second endpoint, priced at flash-lite. The live revision serves as it did.

- v3 passes every threshold. On the stand-in it keeps the v2 candidate's three misses: two joins with one figure each, and lk-27's refusal. Each of v3's rows still answers from one source, so the stand-in does not credit it with the second figure a join needs. On your lane, the gate decides. Read the rows that cost a point, as step 5 did.

### Optional: one question, two models

The same questions to the live revision, as the UI asks them, and to the v3 candidate: both answers, their marks, their price, and the traffic line.

Every step before this one measured. This one shows. The cell sends each question to both addresses with the gate's own client, `run_eval.ask`, which makes the same call the UI's requests arrive as. It prints both answers, then the service's traffic line, which proves the UI never saw the candidate. Its three questions test three things:

- An answer. Can unused leave shorten my notice period? is golden row jn-02, so no training file ever held it. Both models should say no, from NP-03. v3 says it in the house style, with the clause named.

- The same question in Hinglish. v3 learned to answer in the language it is asked in. Whether the live model answers a Hinglish question in Hinglish is for your lane to show; on the stand-in it answers in English.

- A refusal. The handbook has a section headed Referral bonus that states no amount, so both should refuse. v3 refuses in the house style.

To ask your own questions, write them in `~/demo_questions.txt`, one to a line, and the cell asks those instead. Ask the same question in the UI while it runs: the UI's answer is the live one.

#### Do it

- The same facts, a different habit. Both revisions retrieve the same way, so both answered from the same clause. What changed is how the answer is written: the verdict first, the mark, the clause, and the question's own language.

- The price differs too. On the stand-in, an answer costs Rs 0.25 on the tuned candidate, at Google's 1.5 times flash-lite, against Rs 1.06 on the live model. The candidate also answered in half the time.

- The UI never moved. The traffic line shows the service's own URL sending all its traffic to the live revision. The candidate answers only at its tagged URL.

- This is one question, not the verdict. The verdict is step 7's gate, and step 6's judge if you run it on v3 (`make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND"`). Most answers will match in substance. The differences sit where the habit shows.

- When you are done, remove the candidate's address with step 6's last block, or run the lesson's finish file.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The model is a setting. A tuned endpoint goes behind the same retrieval as a model name: `make candidate GENERATOR_MODEL=`, and every surface above the API changes nothing.

- A candidate takes no traffic. The live revision keeps serving while the tagged URL answers the gate and the judge.

- Promotion is by name. `make candidate` records the revision it made, and `make promote` moves traffic to that revision, never to whatever is newest.

- The golden set never enters the training file, so the gate and the judge score what the tuned model learned, not what it memorised.

- A context cache is one model's, so a tuned endpoint is never handed `gemini-3.6-flash`'s cache.

- The gate still decides; the judge explains. Where the two disagree, read the row.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The answer cache never reads the model. Every entry records the model that answered, and the test ignores it. With the cache on, a candidate is served the live model's stored answers, and the live revision would serve the candidate's to users.

- `RAG_MODEL_BASE` is yours to remember. The Makefile's default is `gemini-3.6-flash`, and `make candidate` does not take the base from the endpoint or the tuning job. `tune.py` prints the right line; nothing checks that you used it.

- The usage rows price a tuned endpoint at its base, where Google bills 1.5 times that. Step 6's cell adds the 1.5 itself.

- `make usage` cuts the model column at twenty characters. Every tuned endpoint prints as `projects/` plus the first eleven characters of your project number, so two endpoints cannot be told apart.

- No target pins a tuned model to its tenant. The API reads `tenant_settings/{tenant}.generator_model` (the kit's 'pin one tenant' setting), but nothing writes it. And `cost.py` prices a pinned endpoint at the service's `RAG_MODEL_BASE`: `gemini-3.6-flash` on the live revision, about four times Google's price for a tuned flash-lite.

- Promotion makes one tenant's model everyone's. The training file was acme's (`TENANT ?= acme`), and `make promote` puts the tuned model behind every tenant's answers. In the kit's own words, weights cannot be filtered per tenant afterwards.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane. The last two are for steps 7 and 8, if you ran them.

`documind-api` has one more revision, with the tuned endpoint as its model, no traffic and no tag, and `.candidate-revision` is gone. Your home folder has `base173.json` and `cand173.json`, and Experiments has the pairwise run. Cloud Logging holds the usage rows of about 260 answers. The live revision still serves `gemini-3.6-flash`, and the tuned endpoint stays, billed only when it answers. If you ran steps 7 and 8, the candidate address pointed at v3's endpoint until you removed it again, and `~/cand173v3.json` holds v3's gate. Lesson 12.4 closes the loop: a production row becomes a candidate change, gated by eval-live before it is promoted or rolled back.

Netsetos GenAI on GCP · Module 12 Tuning · Lesson 12.3 Compare the tuned candidate with an uncontaminated baseline · v5.0

Next: Lesson 12.4 Improve the agent safely: eval-gated self-improvement.
