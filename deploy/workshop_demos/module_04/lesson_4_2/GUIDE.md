# Lesson 4.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.2_Live_Judge_WIX.html`, reviewed at blob `a3b436e773ca4580adf995f55ba1ad0be7561a39`. Learners read that page on the course site; this guide keeps its prose.

Lesson 4.1 made the golden set sound. This lesson runs the three instruments that use it, and keeps them apart on purpose. The offline gate checks the set on every push, with no credentials. The live gate sends every row to the deployed API, as a roster member and again as an outsider, and blocks a release on 9 thresholds and 15 required rows. The judge has Gemini read the lane's answers with the context they cite, and it never blocks anything. You will read CI's verdict on the kit you run, run the live gate and take its report apart, and run the judge beside it.

- Three instruments, three questions, and why only one may block

- The words: offline half, live half, threshold, required row, two identities, exit code, report, candidate, judge, groundedness

- Before you run anything: set up the shell

- The offline half: on every push, and CI's verdict on the commit you run

- The live half: every row, two identities, nine rates, three exit codes

- The judge: the lane's own answers, read with the context they cite

- Where the gate and the judge disagree: read the row

- The judge's other two modes: trajectories now, pairwise in lesson 4.4

- How each instrument lied before it was fixed, and what a run costs

- Verify it yourself: the checklist

You will learn why an evaluation needs three instruments that fail for different reasons, what each one can and cannot see, and why only the deterministic one may block a release. Then you will prove it on your lane: CI's green run on the commit you cloned, a live gate run with its report taken apart, the judge's scores, and the rows where the two disagree.

### Three instruments, three questions, and why only one may block

One judges the golden set, one judges a deployment, and one explains what the deployment said.

Each instrument answers a different question. The offline gate asks whether the golden set is sound. It reads files, needs no credentials and takes seconds, so it runs on every push. It never sees an answer. The live gate asks whether a deployment answers the set well enough to release. It sends every row to `/v1/query`, scores each reply with fixed string rules and exits 0, 1 or 2. It needs a deployment and two identities, takes minutes and costs rupees, so it runs before a release. The judge asks whether each answer is supported by the context it cites, and does what was asked. It is Gemini reading the lane's own answers, through Vertex AI Evaluation.

Only the deterministic instrument may block. The live gate gives the same verdict for the same replies, every time. The judge is a model. Its score depends on its prompt template, the model behind the service and the context it is shown. The kit's first judged runs scored the lane 0.25 grounded, for reasons that were all about the judge's inputs. So the judge's scores go into an Experiments run named for the revision it judged, and the gate still decides. The judge's own last line says it: where they disagree, read the row.

The live gate is strict in specific ways. Every row is sent, answerable or not; the first version scored only answerable rows and silently skipped every refusal. A 5xx or a malformed body is a failed request, never a refusal. Each rate has its own denominator. `must_contain_rate` divides by the rows answered and `correct_rate` by every answerable row, so a model that answers little cannot look accurate. A leak exits 2 whatever the rates say, and a required row that fails blocks on its own. Isolation is judged twice: by markers in every reply, and by an outsider who must be refused on every isolation row.

A Test match. Before play, the match referee inspects the pitch and the balls: is the equipment fit for a fair game? That needs no players. During play, the umpire rules by the laws of the game: out or not out, no opinion, and the decision stands. The commentators say who played well and why, and they notice things the laws never ask about. They are worth hearing, but they never change the scorecard. The offline gate is the referee's inspection, the live gate is the umpire, and the judge is the commentary box.

#### The threshold board: what the live gate would say about a run you design

Each chip is a golden row. Pick one and choose what the API replies to it, or start from a preset. The board scores the run the way `live()` does: 9 rates, each over its own rows, the required rows, and the exit code with the gate's own closing sentence.

The arithmetic is the aggregate half of `live()` in `run_eval.py`, ported. For each of the 11 presets, the build ran the kit's own `live()` against a stub that replies to every row the way the preset says, and the board had to match its scores, failed thresholds, required rows, exit code and closing sentence.

It calls no API. Each choice stands for a reply the live half could get, scored the way `live()` scores it. Latency, cache hits and quote support are printed by the gate but are not thresholds, so the board leaves them out. Try answers everything and refuses everything: two opposite models, both blocked, by different thresholds.

### The words: offline half, live half, threshold, required row, two identities, exit code, report, candidate, judge, groundedness

Twelve rows, each with the value it takes on your lane.

One distinction to hold: the live gate scores and the judge rates. A score comes from a rule you can read, and the same reply always gets it. A rating comes from a model reading the reply, and a new template, a new judge model or a new context changes it. Scores gate a release. Ratings tell you where to look.

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

The shell, in the kit's folder, with the two token functions the block defines. The UI is not used. Step 5 makes a second venv for the judge, and step 7 needs the chat service only if your lane has one. The live gate and the judge each ask the API every golden row, so plan about twenty-five minutes for steps 4 and 5 together.

### The offline half: on every push, and CI's verdict on the commit you run

Two workflows, one that runs by itself and one that waits for a person, and the dry run's result on your clone.

#### Definition

Two workflows carry the kit's gates, and only one runs by itself. `documind-dryrun.yml` runs on every push and pull request of the learner repository, with no Google credential. Every Python file compiles, the offline suites run, Terraform validates, the images build, and the last step is the offline gate. `documind-cd.yml` is the release. In the learner repository it runs only when started by hand, because no project stands behind a public repository. Its first job repeats the offline gate. Its release path makes a candidate revision that takes no traffic and runs the live gate against the candidate's own URL. Then it waits for a person, and only then moves traffic. The previous revision stays, so flipping back is the rollback.

#### The code

#### Do it: the gate as CI runs it, and CI's result on your commit

The next cell asks GitHub's public API which commits the dry run has judged, and marks the one your clone is at.

The offline gate passed in seconds on your machine, as it does on every push. When the marked commit shows `success`, CI ran the same line on the kit you run, alongside the compile, the suites, the Terraform check and the image builds. That is what "the kit is sound" means before any money is spent. None of it talks to Google, so none of it can say anything about answers. That is the live gate's job, and it is why the live gate is a separate step with its own credentials.

### The live half: every row, two identities, nine rates, three exit codes

The target that mints two tokens, the loop that sends every row, the rates, the exit, and what one run costs.

#### Definition

`make eval-live` mints two identity tokens, both for the API's canonical run.app URL, whichever URL is called: the member's and the outsider's. Then `run_eval.py` sends every golden row to `/v1/query` as the member, answerable or not. A non-200 reply, after one retry, or a malformed body is a failed request. Every reply is checked for every marker. An answerable row needs `answerable` true, a citation that names its own tenant and a current version, and every figure on its own boundaries. Then the gate asks every isolation row again as the outsider and requires 403. Nine rates come out, each over its own rows. The exit code is the verdict, and `REPORT` keeps every row's result in a file. The run points at the live revision by default. Lesson 4.4 points the same command at a candidate.

#### The code

#### Do it: the live gate, with a report

Now take the report apart. The cell recounts the four rates whose denominators people misread, from the report's own rows, then prints all nine with their verdicts and the rows that cost a point.

Last, what the run cost. The API priced every answer on its usage row; `make usage` groups the last hour of those rows. Run it straight after the gate, before step 5 asks the lane again.

The gate asked all 65 rows as the member and the 11 isolation rows again as the outsider. Read the table from the top. A single failed request fails the first threshold outright, because a 500 is not a refusal. Each row that cost a point is printed with the API's own words, so a miss is something you can read. The arithmetic shows why two rates can disagree. In the stub's run, 45 of 46 answered rows carried their figure, and 45 of 47 answerable rows were right; your report gives your own pair. A model that refused half the set could not score well by being right about the other half. `make usage` turned the same hour of usage rows into rupees: 47 acme, 10 zeta and 8 globex answers, one full live run.

### The judge: the lane's own answers, read with the context they cite

Its own venv, its offline self-test, and a run that ends in Vertex AI Experiments.

#### Definition

The judge collects its own answers with the same `ask()` and the same member token, so it judges the lane and not a prompt in a notebook. For each answer it reads the cited chunks in full from Firestore. It builds the prompt the judge model will see: the context, then the question. It asks Vertex AI Evaluation, in `us-central1`, for two ratings per row. GROUNDEDNESS is 1 when every part of the answer is attributable to that context and 0 otherwise. The second is the one its SDK names, which for the pinned 2.1.0 is INSTRUCTION_FOLLOWING, from 1 to 5. Each run is an Experiments run in `documind-eval`, named for the API revision's `GIT_SHA`, the time and a hash of the judge's templates, because a different template is a different judge. That SDK is 2.1.0, while the kit's services pin `google-cloud-aiplatform` 1.153.1, which the retriever, the indexer and the ablation harness import in your shell. So the judge gets its own venv, and `make judge` is told to use its python.

#### The code

#### Do it: the judge's venv and its self-test

#### Do it: the judge on your lane

`--reuse` keeps the collected answers in a file. If the Evaluation step stops, the rerun judges the same answers without asking the lane again.

The self-test proved the judge's assembly offline: the full chunk text replaces the quote, the prompt carries the context and then the question, and the trajectory maths is right. The live run asked the lane every row again, read every cited chunk it could find, and sent 130 requests to the Evaluation service, two per answer. `groundedness/mean` is the share of answers judged fully grounded. The by-shape lines are the ones to read, because a refusal claims nothing and so says nothing about grounding. No SDK 2.1.0 setting pins the judge model, so the run says the service's default judged it. The template hash in the run's name is how you tell two judges apart later.

### Where the gate and the judge disagree: read the row

Four ways the two can meet, and the gate's misses read against the judge's answers.

`judge.py` prints its summary and writes no per-row ratings, so "read the row" means reading the answers. The cell takes each row the gate failed and prints what the judge's own collection received for it.

The stub's two misses read differently. jn-06 answered with one of its two figures, and everything it said was in its context, so a groundedness judge can call it grounded. lk-27 refused, and a refusal is always grounded. Neither is the judge failing; both are rows the gate caught and a groundedness rating cannot. The reverse happens too: an answer can carry the gate's figure and a sentence its context never said. That row passes the gate, and only a low by-shape rating, or your reading, finds it. The two collections are separate runs, so a row can differ between them; that difference is itself worth reading.

### The judge's other two modes: trajectories now, pairwise in lesson 4.4

The chat service's tool calls against the one grounded path, and why the pairwise judge needs a candidate.

With `CHAT_URL`, the judge sends a few answerable acme rows to each of the chat service's three brains, langchain, langgraph and adk. It compares the tool calls each brain returns with the reference path: one retrieve, then the answer. The three matches are computed in `judge.py`: exact, in order and any order. A brain that answers without retrieving scores 0 on all three, whatever its answer says. `--no-vertex` skips the Evaluation service, and `--reuse` skips asking the API again, so this costs only the chat turns. `CHAT_URL` is the service's `documind-chat-NUMBER.REGION.run.app` address, not the `status.url` gcloud prints, which is usually its hashed `a.run.app` address: the judge mints its token for `CHAT_URL`, and the chat service accepts only a token minted for its own `SELF_URL`.

Pairwise is the third mode. With `API_B`, the same questions also go to a candidate revision, and the judge says which of the two answers is better, row by row, with the live revision as the baseline. It needs a candidate with one setting changed, which is where lesson 4.4 begins.

### How each instrument lied before it was fixed, and what a run costs

The kit's own history of green runs that meant nothing, and the rupees of this lesson.

#### The live gate, before 12 September

- A 200 whose body was `{}` counted as a refusal. Every 200 is now checked against the response schema, and a malformed body is a failed request.

- A 500 on the version row cost one point and never blocked. `request_success_rate` must now be 1.00, and a required row that errors blocks on its own.

- "60" was satisfied by "160 days". A figure must now stand on its own boundaries.

- A citation was any non-empty list. Each one must now name the row's tenant and a current version.

- 33 correct answers of 47 read as 87%. The rates divided by the rows answered. `correct_rate` now divides answered-and-right by every answerable row.

- A missing outsider token printed a note and ran anyway. The run now refuses to start, because every isolation row would ask as a member and could only fail.

#### The judge, in its first live runs on 10 September

- It read quotes. A citation's quote is at most twenty-five words, so every answer that said more looked unsupported: 0.25 grounded. It now reads the cited chunks in full.

- It read the bare question. The template reads only the prompt and the response, so the chunk text in another column was never seen. It scored 0.25 again, because the sixteen refusals among sixty-four rows were the only answers that looked grounded. The prompt is now the context, then the question.

- It stopped after seventeen minutes. The SDK had renamed FULFILLMENT. The second metric is now resolved by preference and printed.

- Two runs collided on one name, and Experiments refused the second. The name now carries the time.

- A candidate token for the tag URL got 401 on every row, and the judge wrote a run with no rows. Tokens now carry the canonical URL as their audience, and an empty collection stops the run.

#### What it costs

In an application repository, `documind-cd.yml` would run on every pull request and every push to main, as its header says. It is keyless: GitHub's short-lived token is exchanged through Workload Identity Federation for a Google credential that lasts about an hour, pinned to the repository's immutable id and to main. The learner repository has no project behind it, so there the workflow waits for a person to start it.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

In the cloud: the usage rows of the gate's and the judge's answers, the outsider's refused requests in the API's log, and one run in the Experiments experiment `documind-eval`, which stays until you delete it. On your machine: `evals/reports/lesson72.json` and `evals/reports/judge72.json`, which git ignores, and `~/judge-venv`, which you can delete. Nothing in the kit changed, so the setup block's `git pull` keeps working. Lesson 4.3 places these instruments in the pipeline, and lesson 4.4 makes a candidate with one setting changed and turns all three instruments on it: the scoped live gate, the pairwise judge against the live revision, and the price of the difference.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.2 Separate offline checks, live scoring and LLM judgment · v5.0

Next: Lesson 4.3 Place evals in the pipeline: CI, the candidate gate and live traffic.
