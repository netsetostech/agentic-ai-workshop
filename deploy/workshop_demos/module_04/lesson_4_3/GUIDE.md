# Lesson 4.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.3_Placing_Evals_WIX.html`, reviewed at blob `67bf859b284dfdb4ca8a5cfa8db03e338447995e`. Learners read that page on the course site; this guide keeps its prose.

Lesson 4.2 ran three instruments, one at a time. This lesson puts each where it runs. The offline gate runs in CI on every push, and both release paths of the delivery workflow need it to pass first. The live gate runs on a candidate, a revision of the API that takes no traffic, and holds the release on 9 thresholds and 15 required rows. After the release nothing gates: each answer leaves a usage row, and two alert policies read rates from the rows. You will break a golden row and watch the offline check refuse it, gate a candidate and remove it, find the gate's own rows in the live log, and read one refusal the alert can never count.

- Three places to run an eval, and what each one can see

- The words: placement, dry run, offline gate, eval-gate, needs, candidate, candidate gate, required row, usage row, revision_name, eval identity, metric, policy

- Before you run anything: set up the shell

- CI: the offline gate on every push, and the job every release needs first

- The candidate gate: a revision with no traffic, judged before any user meets it

- Live traffic: the usage rows, and the gate's rows among them

- The stream's row: answerable, unless the pool was empty

- The alert's own inputs: two log metrics, two policies, and the windows they saw

- The judge's place, the gaps the placements leave, and what each costs

- Verify it yourself: the checklist

You will learn where each eval runs, what it can see from there, and what it cannot: CI judges the golden set, the candidate gate judges answers before anyone gets them, and live traffic leaves rates without text. Then you will prove it on your lane: a row broken and refused offline, a candidate gated and untagged, the gate's own rows found among the live rows, and a refusal whose row says answerable.

### Three places to run an eval, and what each one can see

The same golden set in CI, on a candidate and among live traffic, and the failures each place catches first.

Where an eval runs decides what it can catch. The kit runs one golden set in three places, and they are not interchangeable. In CI, on every push, the offline gate reads the 65 rows and the corpus beside them. It needs no credential and never calls the model, so all it can judge is the set itself. Before a release, the candidate gate sends every row to a revision of the API that takes no traffic, reads every reply, and holds the release on 9 thresholds and 15 required rows. After the release, nothing gates. Every answer leaves one usage row, and two alert policies read rates from the rows. They can open an incident, but they cannot stop anything.

Each place sees more traffic and less of each answer. CI reads no answer at all. The candidate gate reads 65 answers word for word, but only answers to the set's own questions, and only through `/v1/query`. Live traffic is every question anyone asks, but its row keeps counts, clocks and flags, never the question or the answer. So the later a failure is first caught, the more people met it first. Some failures are caught nowhere, and the matrix below names them.

The judge sits beside the pipeline, not in it. Lesson 4.2's judge can read any deployment's answers, a candidate's included. No step of either workflow runs it, and its exit code does not depend on its scores. It explains what the gate found, and it never decides.

A factory that makes pressure cookers. Incoming-material inspection checks the steel and the test gauges before a single cooker is made: is each gauge calibrated, can each specification be met at all? It never tests a cooker. Before a batch ships, the pre-shipment test takes the batch off the line and pressure-tests every unit against the specification, and one failure holds the whole batch. After the cookers are sold, the warranty desk hears from every city, but only as counts: so many returns from Pune this week. It never sees the cooker that leaked quietly and was never returned. CI is the incoming inspection, the candidate gate is the pre-shipment test, and the usage rows and alerts are the warranty desk.

#### The placement matrix: 11 failures, four placements, and where each is caught first

Each row is a failure, and each column is a place an eval runs. Pick a row to read what each placement would do, in the kit's own words: the offline gate's FAIL line, the live gate's exit code and closing sentence, the row an answer leaves and the policy that reads it, and what the judge reads.

Computed when this page was built, from the kit you clone. The CI column ran `run_eval.py`'s offline half on the golden set with the failure planted, with every function that sends a request replaced by one that fails if called, so an offline check that reached for the model would have broken the build. The candidate column ran `live()` against a stub API that fails the way the row says. The live column evaluated `main.py`'s own two expressions, the stream's verdict and the row's flag, against the two policies' numbers, parsed from `alerts.tf`. The judge column is what `judge.py` asks for and what it returns.

Of the 11 failures, CI stops 2 and the candidate gate stops 5. Live traffic is the first to see 2. The judge alone can point at 1, and 1 is caught by nothing in the kit: refusals in the stream, which is what the UI uses. Steps 3 to 7 run one placement each on your lane.

It calls no API and runs no model. The stub's replies fail one way each, and a real failure is rarely that clean. The live column says whether a policy can see the failure at all, not how much traffic it takes to stay above 0.20 for 30 minutes: that depends on how many good answers the same tenant gets in the same windows.

### The words: placement, dry run, offline gate, eval-gate, needs, candidate, candidate gate, required row, usage row, revision_name, eval identity, metric, policy

Thirteen rows, each with the value it takes on your lane.

One distinction to hold: a gate blocks and an alert notifies. A gate runs before anyone is affected, and its exit code can stop the change. An alert runs on traffic people are already sending, and all it can do is tell someone.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 5 makes the difference visible in the usage rows.

The shell, in the kit's folder, with `NUMBER`, `REGION`, `API` and the token function `tok` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line: step 6 needs a pool that is not empty. Step 5 asks one question in the UI, signed in as yourself. Step 4's gate asks the candidate every golden row, which takes about ten minutes; everything else reads files or logs, apart from one streamed answer in step 6.

### CI: the offline gate on every push, and the job every release needs first

Two workflows, the same line of Python in each, the order their jobs run in, and a row broken on purpose.

#### Definition

The learner kit carries two workflows. `documind-dryrun.yml` runs on every push and pull request, with no Google credential: every Python file compiles, the offline suites run, Terraform validates, the images build, and the last step is the offline gate. Lesson 4.2 read its verdict on your commit. `documind-cd.yml` is the delivery, started by hand in the learner repository. Its first job, `eval-gate`, runs the same line, and both release paths name `eval-gate` in `needs`. A red offline gate therefore means no candidate is built, no live gate runs and no person is asked. The offline half is three checks over files, falsifiable, anchors and coverage, which lesson 4.1 wrote rows against. Nothing in it sends a request. That is its strength and its limit: it catches a golden set that has rotted, in seconds and for free, before anything is deployed, and it can say nothing about an answer.

#### The code

#### Do it: the pipeline, read from its two files

The cell reads both workflow files with the standard library and prints each job: what it needs, whether it signs in to Google, who approves it, and every line that runs an eval.

#### Do it: break a row the way a hand edit would

A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs.

Give the kit its file back:

The check refused the edit at once, on your machine, with no credential and no model: exactly where CI runs it. In CI the same exit 1 fails the dry run on the push, and in `documind-cd.yml` it fails `eval-gate`, so `release-candidate`, `promote` and `release-clouddeploy` never start. The matrix's first row shows what would happen without this placement. The candidate gate would ask lk-06, score a correct answer of 60 days as a miss, and still pass, at a must_contain_rate of 97.9% and a correct_rate of 97.9%: one row of 47 is inside every threshold's slack. A wrong answer key is a fault in the set, and only the set's own check is built to see it.

### The candidate gate: a revision with no traffic, judged before any user meets it

The release path's own checks, a candidate made with no change, the gate on its tag URL, its required rows, and the tag removed.

#### Definition

In `documind-cd.yml` the release path runs in a fixed order. `make build` makes the API's image, tagged with the commit. `make release-candidate` puts that image on a revision with no traffic and the tag `candidate`, and records the revision's name. A step then checks that the candidate answers as the tag: its `/version` must name the sha being released, or the gate would judge some other revision. `make eval-live` judges the candidate's tag URL with tokens minted for the service's canonical URL, because the API checks every token against that URL and refuses one minted for the tag. Only a green gate lets `promote` start, and `promote` waits for the reviewers of the `production` environment before it moves traffic to the recorded revision, by name.

On your lane, `make candidate` makes the same kind of revision without a build: a new revision from the service's latest one, the image unchanged, with 11 settings written over it. With no override it writes the Makefile's defaults, which are the values `make up` deployed the API with, unless your shell exports one of them (lesson 4.4 diffs the two revisions to prove it). So this candidate runs what the live revision runs, and the gate's verdict on it is the release decision for "no change". The verdict has three parts: the 9 rates against their thresholds, each of the 15 rows in `required.json` passing on its own, and no leak. Exit 0 lets the release go to a person. Exit 1 or 2 fails the job, and `promote` never starts.

#### The code

#### Do it: the candidate

#### Do it: does the candidate answer as the same build?

This is the workflow's check, by hand: `/version` on the live URL and on the tag URL, both with a token minted for the live one.

#### Do it: the gate on the candidate

Now read the report as a release decision: how many thresholds were judged, what the outsider got, and each required row.

#### Do it: remove the candidate

The candidate has done its job. Removing its tag ends its URL. Deleting `.candidate-revision` means a stray `make promote` stops with an error instead of moving traffic to it; lesson 4.4 explains why both are needed.

The candidate answered every golden row while users stayed on the live revision, and the gate read each answer in full. This is the only placement that sees answers before people do, and the only one that can stop a release: in the workflow, exit 1 or 2 here is a failed job, so `promote`, the person and the traffic flip never happen. It is also the placement that costs, because every row is a model call. And it sees only what it asks: 65 questions, through `/v1/query`, as the eval identity. A failure in other questions, in the stream, or in traffic it never sends is out of its reach. Step 5 turns to that traffic.

### Live traffic: the usage rows, and the gate's rows among them

One question in the UI, the row every answer leaves, the log split by revision and by caller, and make usage.

#### Definition

After the flip there is no gate. What live traffic leaves is one usage row per answer, logged by rag-api as structured JSON, which Cloud Logging stores with the revision that wrote it. The row carries the tenant, the caller, the tokens and rupees, the three stage clocks, the pool, the confidence and an unanswerable flag: 29 fields, and none of them is the question or the answer. Nothing that reads the rows can tell a right answer from a wrong one; what it can count are rates. The gate's rows land in the same log. They carry the eval identity, `documind-ui-sa`, where a person in the UI carries their own email, and the candidate's rows carry the candidate's revision name. `make usage` reads the same rows but keeps only the payload, so its tables group by tenant, model, brain, surface and backend, never by revision or caller.

#### The code

#### Do it: one question in the UI

Open the UI at `https://documind-ui-NUMBER.asia-south1.run.app`, signed in as yourself; Module 0 put your account on acme's roster. Ask What is ACME's sabbatical policy? It is golden row rf-01, a question no acme document answers. The answer streams in and declines in words. Step 6 reads what that answer's row said, so ask it now and run step 6 within half an hour.

#### Do it: the rows, split by revision and by caller

The cell reads the last day's query and stream rows with the label `make usage` drops, the revision, and marks the revision that serves traffic now. Then it counts the rows by caller, and checks the eval identity's rows on a revision with no traffic against `golden.jsonl`.

#### Do it: the same rows, as make usage groups them

The candidate's revision holds the gate's answers and nothing else: 65 rows, every one from the eval identity, split acme 47, zeta 10 and globex 8, exactly as `golden.jsonl` splits them. The outsider's isolation requests left no row, because the roster refuses them before any answer is made. That is this lesson's proof: the same rows ran offline in CI and against a candidate, and they sit among the live rows, where only the revision and the caller tell them apart. `make usage` can tell neither, because no table it prints has a revision or a caller column. On a day the gate ran, its answers are in every total `make usage` prints.

### The stream's row: answerable, unless the pool was empty

Why the UI's refusals never reach the alert, read in main.py and proved on one streamed answer.

#### Definition

The two routes record their verdicts differently. `/v1/query` asks the model for a structured answer, and the row takes the model's own `answerable`. `/v1/stream` cannot: it sends tokens as the model writes them, with no response schema, so the model never returns a verdict. One line decides the stream's row instead. An empty pool, where retrieval found nothing, is a refusal the API writes itself, and its row says false. Every other stream's row says answerable true, confidence medium, whatever the model wrote. So when the model reads passages and declines, which is the right answer for rf-01, the row of that refusal says answerable and its flag is 0. The UI streams, and the alert counts flags: the UI's refusals are invisible to it unless the pool was empty. The gate and the judge cannot fill the gap, because both ask `/v1/query`. The kit's own comment names the missing piece: a real verdict for the stream.

The pool matters, which is why the setup pins acme to the kit's own index. That index comes back empty only when it holds nothing for the tenant, so any question gets its nearest passages and a refusal in words. RAG Engine, where `make up` pins acme, drops every passage farther than a distance of 0.5, so an off-topic question there can come back with an empty pool, and that row would say false.

#### The code

#### Do it: one refusal through the stream, and its row

The cell streams rf-01's question for acme as the eval identity, prints what the stream said, then waits for the row in Cloud Logging and prints its verdict. If you asked the same question in the UI in step 5, it prints your row too, without your email.

The stream declined in words, over a pool of passages that did not hold the answer, and its row said answerable true with the flag at 0. If you asked in the UI, your row said the same. The row has 29 fields and none holds the question or the answer, so nothing downstream can find the refusal later either. The same question through `/v1/query`, the way the gate asks it, writes the model's own verdict: false for a refusal, flag 1. So the gate's refusals count toward the alert and yours do not. A model that began declining questions it could answer would show in the gate, which asks `/v1/query`, and not in the alert, which sees the UI only through its stream rows.

### The alert's own inputs: two log metrics, two policies, and the windows they saw

The filters, the deployed policies, and the five-minute windows the gate's rows fell into.

#### Definition

The unanswerable alert is two counters and a ratio. `documind/queries` counts every query and stream row of `documind-api`, and `documind/unanswerable` counts those whose flag is 1. Both take the tenant from the row as a label. The policy sums each counter per tenant in five-minute windows and opens an incident when unanswerable over queries stays above 0.20 for 30 minutes. The latency policy reads Cloud Run's own request latencies for `documind-api`: the 95th percentile of each series every minute, averaged, above 3 s for 5 minutes. Neither filter names a revision or a caller, so the candidate's answers and the eval identity's are traffic to both. If the candidate refused every row it should, its rows alone put globex at 6 unanswerable of 8 (0.75), zeta at 5 of 10 (0.50) and acme at 7 of 47 (0.15): over the gate's own rows, two tenants are above the line. A full run takes about ten minutes, and the policy waits for 30.

#### The code

#### Do it: the metrics, the policies, and the windows

The cell reads each metric's filter from Cloud Logging, both policies from Cloud Monitoring, and each metric's counts per tenant over the last six hours, aligned the way the policy aligns them. Then it divides, window by window.

The deployed filters and numbers are the file's: 0.20 for 1800 s, and 3000 ms for 300 s. The windows of step 4's run show the gate's own refusals as live traffic, tenant by tenant, and step 6's refusal counted in `documind/queries` and not in `documind/unanswerable`. The notification channels are the incident's audience. `alerts.tf` sends every policy to a PagerDuty key when one is set and to the admins' addresses when `ADMIN_EMAILS` is not the placeholder. With neither, the count is 0, and an incident opens and tells nobody.

### The judge's place, the gaps the placements leave, and what each costs

Where the judge sits, five gaps read from the kit, and the rupees of each placement.

#### The judge: beside the pipeline, never in it

No step of either workflow runs `judge.py`. Its `main()` prints the scores and returns 0 whatever they are; it returns non-zero only when it had nothing to judge or was called wrongly. It collects its answers with `run_eval`'s own `ask()`, so it reads `/v1/query` as the eval identity: the gate's route and the gate's caller. Point it at a candidate with `API_B`, as lesson 4.4 does, and it explains a release decision. It does not make one.

#### Five gaps the placements leave

- Refusals in the UI. The stream's row says answerable unless the pool was empty (step 6), and the gate and the judge ask `/v1/query`. A model that declines good questions in the UI is caught by no instrument in the kit.

- A failed request. A request that fails before its answer writes no usage row, and no policy in `terraform/` reads Cloud Run's request count or a response code. The gate counts every failure, because `request_success_rate` must be 1.00; live traffic counts none.

- The eval's rows are traffic. `documind/unanswerable` and `documind/queries` count the gate's rows and the candidate's like anyone's. The Desk's own router metric made the other choice: it drops every service account, so that the eval accounts cannot page a lane where nobody has asked anything.

- A mean of percentiles. The latency policy averages the p95 of each series it matches and reads every request to the service, the setup block's `/health` among them. An average of percentiles is not the percentile of all requests: a quiet revision with fast answers pulls it down. Its comment says as much: every request, for 5 minutes.

- A tenant the gate barely asks. Globex has 2 answerable rows of 47. With globex's index empty, the matrix's stub run lost those two rows and still exited 0, at an answerable_rate of 95.7%. Only the unanswerable alert would see it, once people asked.

#### What it costs

The usage rows price generation only. The query embedding and the Ranking API bill on their own lines, which no row records.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

In the cloud: one more `documind-api` revision in the service's history, with no traffic and no tag, which step 4 made and judged. The usage rows of its 65 answers, of the stream refusal and of your UI question, each under the revision that served it, and the two log metrics' counts with them. On your machine: `evals/reports/cand43.json`, which git ignores. `.candidate-revision` is gone, and `evals/golden.jsonl` is the kit's own again, so the setup block's `git pull` keeps working. Put acme's pin back now, with the setup section's pin-back window. Lesson 4.4 makes the same kind of candidate with one setting changed, and measures the difference against the live revision.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.3 Place evals in the pipeline: CI, the candidate gate and live traffic · v5.0

Next: Lesson 4.4 Compare one controlled change against a baseline.
