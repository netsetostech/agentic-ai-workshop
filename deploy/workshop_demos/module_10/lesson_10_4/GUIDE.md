# Lesson 10.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.4_Desk_Router_WIX.html`, reviewed at blob `03242e524bd39dd3ceff5c2e0518c22d2e49a24c`. Learners read that page on the course site; this guide keeps its prose.

In lesson 5.6 the Desk learned which questions belong to a person. This lesson routes everything else. The routed Desk has one front door, `POST /v1/desk`. It gives each question to one specialist: the company handbook, the law, a person, a question back, or a polite "not ours". Code decides first: who is asking, the hard gate, the masking, and any identifier the question names. Only then do two signals run: a flash-lite classifier that can answer only from a fixed list, and a vote over the route set's labelled examples. When they disagree, one arbiter call picks from the two routes they named, or a question back. Before any of that, every document the kit's manifest names gets a class, because a desk searches only its own classes. On your lane you register the classes and relabel the stored rows, build the example index, and switch the router on for acme. You ask the Desk page four questions and press one button, then call the router and the Desk over REST, watch a figure worked out in code, run the router in shadow on zeta, and read the rows it logs. The same Desk also gets a second front door: the "HR Desk" app in Google Chat, reached through a bridge service that the Desk lets name the person it asks for. With a Business or Enterprise Google Workspace account you ask it the same questions; on every lane you prove what it refuses. Last, you run the router's own eval.

- One door, five routes, and the rules first

- The words: route, desk, class, pin, anchor, L1, the vote, accept, arbiter, clarify, chip, shadow, delegate

- Before you run anything: set up the shell

- Your lane: the classes, the example index and the switches

- The Desk page, and the HR Desk app in Google Chat

- Classes, desks, the rules first and the Google Chat door, in the code

- Two signals and one arbiter, in the code

- /v1/route and /v1/desk, over REST

- The shadow, the rows and the log

- Why it is shaped this way, what it costs, and what the kit does not do yet

- Verify it yourself: the eval and the checklist

You will learn how the kit gives each question one desk: code first, at no cost, then two cheap signals, then one arbiter only when they disagree, and how every document gets the class a desk searches. Then you will prove it on your lane: a handbook answer and a statute answer with its in-force lines on the Desk page, decisions over REST, the router in shadow beside ordinary chat turns, and the router's eval on the dev split. You will also deploy a second door onto the same Desk, the HR Desk app in Google Chat, and prove what it refuses on any lane, and what it answers if you have Google Workspace.

### One door, five routes, and the rules first

What a route is, why a desk needs classes, and the order in which the router decides.

One door, five routes. Until now, DocuMind answered every question the same way: retrieval over the company's documents, then a model. The routed Desk gives each question one route first. `handbook` answers from the company's own policies. `statute` answers from the law the corpus holds. Under the answer is a line for each Act it cites, which repeats what the corpus's own text says about when the Act comes into force, what repeals or amends it, or how current the text is. No line gives a date, because no date has been checked against the Gazette yet. The closing line is "Legal information, not advice.". `case` hands the question to a person, as in lesson 5.6. `clarify` asks one question back, with a button for each of the two likeliest desks. `out_of_scope` answers with a fixed sentence and searches nothing. Each route is a desk, and the code fixes what each answer desk may search. The handbook desk searches the class `policy`. The statute desk searches `statute` and `guidance`. No model and no tool can widen that filter.

A desk searches a class, so every document needs one. Until this lesson, the ingest worker wrote `unknown` on every text chunk and `figure` on every image. A desk's filter would find nothing. So the operator keeps a registry, `tenants/{tenant}/doc_types`, of each object's class and the version a person reviewed (the pin). `make doc-types` writes it from `evals/manifest.json`, and the relabel then moves the stored rows to their class: in Firestore, in Vector Search, in Vertex AI Search and in BigQuery. The worker gives a new version its class only when it is the pinned version. A new version of the handbook stays `unknown`, and off every desk, until a person reads it and re-pins it.

The rules first. `decide()` works in stages, and the cheap, certain ones come first. A person with no role is denied. 5.6's gate sends a disclosure it recognises to a person, with no model call and no text kept. Roles that open no desk are denied. An Aadhaar or card number whose check digit is valid is masked. Then come three things already settled. A turn sent while the person's own case draft is open goes to the case desk. A button the person pressed, a chip, names the desk: the case button in every mode, a desk's button when the company is routed. A company in single mode has one answer desk, so every other question goes there, and the anchors are never checked. (The eval accounts can also send an eval arm, C or A*, which skips the classifier and takes the fallback.) Then come the identifiers, which the kit calls anchors. They are identifiers only, never topic words: a handbook clause code whose prefix the company maps, such as `NP-03`; a named Act or Code; an invoice number; a checked GSTIN; "annual report". One anchor decides at Rs 0 when nothing in the question is near a case. "I", "my", a request for a person, exit dues or a case topic, anywhere in the question, makes it only a hint, because "my bonus under the Bonus Act" may be a person's own dispute.

Two signals, then one arbiter. A question the rules cannot settle goes to two signals at once. L1 is `gemini-3.1-flash-lite` on location `global`, with a schema whose every field is an enum or a boolean, so an injected instruction has nowhere to write. Its thinking budget is 0, it gets one attempt, and it has 4 seconds. The vote embeds the question with `text-embedding-005` and counts the routes of the 7 nearest of the route set's labelled examples, which step 3 copies into each routed company's index. Then `accept()` applies four rules, in order. D: any sign of a case from either signal makes it a case. A: L1 and the vote agree, at 5 of 7 or more. B: L1 names a desk an anchor pointed to. C: L1 says out of scope, and no example is close (cosine under 0.70). Anything else is rule F: one call to `gemini-3.6-flash`, whose schema allows only L1's route, the vote's route and `clarify`. Last come the checks: a question L1 marks as a follow-up, when the result is unsure, keeps the previous desk; a second clarify in a row commits to the best desk; and roles, coverage and the number of parts are applied.

Every number is a starting value. 7 neighbours, 5 votes, 3 case votes, a cosine of 0.70, the timeouts and the 30 minutes of a follow-up are where the kit starts. The kit's own comment says so. The route set's rows are model drafts. `evals/route_threshold.py` sweeps two of the numbers, `TAU_OOS` and `ACCEPT_VOTES`, and is meant to run only once people have written and reviewed rows; nothing in the kit tunes the others yet. This page shows the numbers as the kit holds them, and step 9 lists what is still to do.

The registration counter of a hospital's outpatient department. Each patient is sent to one OPD. A referral slip that names a department, "Cardiology, Dr Rao", goes there without anyone's opinion: that is an anchor. Chest pain goes to the emergency bay before anything else, as 5.6's gate does. For everyone else, a triage nurse asks a few fixed questions and ticks one box on a form, and the clerk looks up where patients with similar complaints went last month. When the nurse's box and the register agree, the token is printed. When they disagree, the duty doctor looks at the two departments they named and chooses one, or says "ask the patient whether they mean the eye or the ear". The nurse's form has no space to write in, so nobody can talk the nurse into printing something else. Each department sees only its own files.

#### A. The rules first

Choose a question and a caller. The twelve questions are the kit's own: rows of `evals/routes.jsonl`, the smoke's POSH disclosure, examples from the gate's tests, and a few written for this page to show an anchor. The three callers hold the roles 5.6 described. The stages are `decide()` itself, run on each question for each caller when this page was built, with the models recorded so that the build could check that none was called before the stage that calls it. For an employee, six of the twelve are settled by code at Rs 0. The other six go to the two signals, and panel B shows what happens there.

Each verdict is `decide()` from your kit's `services/chat/desk_router.py`, with acme's clause prefixes from `evals/desk/queues.acme.json`. The build also ran each question with the classifier answering every route in turn, to check what the roles allow: for a leaver, every route but `case` ends denied.

#### B. Two signals and one arbiter

Set what L1 answered, what the vote found and what an anchor pointed to. The panel applies the acceptance rules and shows which one fired, or the arbiter's choices. Its script mirrors `accept()` and `candidates()`, and the build ran both, the kit's Python and this script, over all 3,161,088 combinations the panel offers and checked that they agree on every one.

The kit's constants, read when this page was built. They are starting values, not yet calibrated:

Rule D is checked first and needs only one signal: a case from L1, as route, second route or a `posh` case type, or 3 case neighbours in the vote. Over-escalating costs a queue a minute; a missed disclosure is a legal failure. With no L1 answer and no case signal, the turn takes the fallback: a direct answer over every class the person may read.

They are not a measurement of how well the router routes. Panel A runs the rules, which are code. Panel B runs the arithmetic of the acceptance rules on inputs you choose. On your lane, flash-lite and the embeddings choose the inputs, and step 10's eval measures the result. The route set it measures with was written by a model, and no person has written or reviewed its rows yet.

### The words: route, desk, class, pin, anchor, L1, the vote, accept, arbiter, clarify, chip, shadow, delegate

Twenty-four rows, each with the value it takes on your lane.

One distinction to hold: the router chooses a desk, and the desk's class filter decides what it may read. The router can be wrong, and the eval measures how often. The filter cannot be argued with: a handbook answer reads only `policy`, whatever the question says.

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

You need the shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `ME`, and your lane as lesson 5.6 left it: acme's queues loaded, your roles set, `desk_gate` unwritten, so acme has the gate's rules, and you allowed to mint tokens as the five eval accounts. If your lane ran an earlier version of lesson 5.6 (or of this lesson, for zeta), `desk_gate` may say `on`, which, once step 3 has pulled this kit and redeployed, adds the paid model check to the rules. After step 3, `make desk` prints a `model_check` note beside it, and `make desk PROJECT="$PROJECT" TENANT=acme DESK_GATE=rules` (and `TENANT=zeta`) keeps the rules without it; the kit you have before step 3 knows only `on` and `off`. Step 3 changes your lane. Every stored row of an object `evals/manifest.json` names, on acme, zeta and globex, gets its class, acme and zeta get an example index, acme's Desk is routed, and globex gets a single desk. From then on, an acme employee who opens the Desk page gets Ask the Desk in every lesson. Run steps 3 to 8 in the same shell, in order: step 3 defines `CHAT`, `UI`, `SINCE106`, `sa` and `etok`, and the later steps use them. The Google Chat door is optional, and off on a lane until you ask for it. Step 3 ends with the optional part that turns it on, with `GCHAT_DOOR=true` on its plan, and deploys its bridge; step 4's part in Google Chat, step 7's smoke of the door and step 8's read of its rows need it. Only step 4's part needs a Business or Enterprise Google Workspace account with Google Chat, and a Chat app you configure in the Google Cloud console. The door's smoke in step 7 needs no Workspace.

### Your lane: the classes, the example index and the switches

The kit you have now; optionally, the Google Chat door; two more eval accounts; each company's registry, applied; the index; the router on for acme and a single desk for globex.

#### Do it: the kit you have now, on your lane

The routed Desk's code was already in the images lesson 5.6 deployed, switched off by `desk_route`. This cell makes sure your lane runs the code this page quotes: it pulls the kit, builds and redeploys rag-api, the UI and the chat service, then plans and applies the kit's Terraform. Terraform comes last because of `DESK_JOB=true`, which you keep as 5.6 said: it points the hourly overdue job at the chat image of the commit you pulled, `chat:COMMIT`, and `commands/lesson-12.8.sh` in the deploy is what builds that image. Without the flag the plan would remove the job, and `make plan`'s guard would refuse it. The Google Chat door stays off: without `GCHAT_DOOR=true` the plan declares nothing of `terraform/gchat.tf`, nor the bridge's account in `terraform/desk.tf`, and the chat deploy says that `documind-gchat-sa` does not exist yet. The whole cell takes many minutes.

#### Optional: the Google Chat door and its bridge

The Google Chat door is a second front door onto the same `POST /v1/desk`. When a person messages the "HR Desk" app, Google Chat calls an HTTPS endpoint, and here that endpoint is `documind-gchat`, a Cloud Run service of its own: the bridge, `services/gchat/`. It asks the Desk on the person's behalf and posts the Desk's reply into the chat as a card. It makes no model call and calls no service but the chat service. Run this part if you will try step 4's part in Google Chat or step 7's smoke of the door; otherwise skip it, with those parts and step 8's read of the door's rows. The plan, with `GCHAT_DOOR=true`, adds the door's 11 resources: what `terraform/gchat.tf` declares, the `documind-gchat` Firestore database, the `documind-gchat-work` topic and its `documind-gchat-push` subscription, the `documind-gchatpush-sa` account and the Chat API, with their IAM bindings; and `documind-gchat-sa`, the account in `terraform/desk.tf` that the bridge runs as. Keep `GCHAT_DOOR=true`, beside `DESK_JOB=true`, on every later `make plan` and `make up`: without it the plan would delete the door, and `make plan`'s guard would refuse it. The plan and apply are the Terraform part of `make plan up GCHAT_DOOR=true`, which the kit names as the step before `make deploy-gchat` (`make up` would also rebuild and redeploy every service). The chat deploy is the part of `make up` the door needs: it allows `documind-gchat-sa`, which exists now, to call `documind-chat`. `make deploy-gchat` refuses on a lane whose last apply had the door off; here it builds the bridge's image and deploys it with `commands/gchat.sh`. Two accounts may call the bridge: `documind-gchatpush-sa`, Pub/Sub's push identity, and `documind-outsider-sa`, which step 7's smoke sends to it. The script's last line allows a third, the Chat app's add-on agent, `service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com`. The kit assumes, without confirmation, that the agent does not exist until a Chat app is configured; while it does not, the binding fails and the line says so. That is expected: only step 4's optional part needs the agent. The service scales to zero instances, and in the words of `terraform/gchat.tf`, "Nothing here bills while idle except what the claims database stores, and its claims expire within a day."

#### Do it: two more eval accounts

The router is measured as the people it serves, so the kit has an eval account for each kind of caller. `evalleaver` is an acme leaver: its roles open the case desk and nothing else. `evalglobex` is a globex employee. Both go on their rosters. Then three accounts get `desk_eval`, the role that lets them call `POST /v1/route`. `evalglobex` also gets `ic_member:head_office`, because globex's queues, loaded below, name it as the Internal Committee, and a single desk, like any routed Desk, is refused while an office's POSH cases have no reader. The cell also sets `CHAT` and `UI`, notes the time in `SINCE106` for step 8, and defines 5.6's two helpers again: `sa` names an account, and `etok` mints a token as one, for the chat service.

#### Do it: the classes

`make doc-types SEED=manifest` writes acme's registry from `evals/manifest.json`. Each text object gets its class, pinned to the `doc_key` the manifest records for its bytes, and the kit cross-checks that against what your lane ingested. A figure takes its parent's class, pinned to the version on your lane, because `make media` drew it there. The town hall video is `not_ingested` unless you made it. Then the view: each object's current label, its class, its pin, its chunks and what the relabel would do. Last comes the relabel's plan. The registry is written now; the stored rows are not, until `APPLY=1`. An object an earlier lesson uploaded that the manifest does not name, such as 1.4's and 3.4's smoke notes or 3.8's visitor rules, shows `unregistered` and keeps `unknown`; which ones you have depends on the lessons you ran.

#### Do it: apply, for all three companies

`APPLY=1` runs the plan on every store that filters by class: the Firestore rows, the Vector Search restricts, the Vertex AI Search documents and BigQuery's `chunk_source`. Then it expires the company's answer cache, so no cached answer from before survives. zeta and globex are seeded and applied in one run each. A run exits 3 when BigQuery deferred a statement because rows were still in its streaming buffer; run the same line again later.

#### Do it: nothing left to change

The same view again, for acme, without `SEED`.

#### Do it: the example index

`make route-index` takes the route set's dev rows on the routes a company's registry covers, embeds each question once with `text-embedding-005` on `us-central1`, and writes them to `tenants/{tenant}/desk_exemplars`. The version is a hash of the rows and the model, so the same rows give the same version on every lane. globex gets no index: a single desk asks no classifier and takes no vote.

#### Do it: the switches

acme goes from off to `on`. globex gets its queues, with its eval account as the Internal Committee, then `single` mode with the statute desk: every globex question goes to the law, with no classifier.

The two new accounts are on their rosters, and `make roles` wrote three role documents; each grant and each revoke is an audit event. The leaver lost `employee`, so its roles open only the case desk. Every current row of a registered object now carries its class, and the second view of acme says `pinned` with nothing to change. The objects earlier lessons uploaded that the manifest does not name stay `unknown`, and so on no desk: on a lane that ran every lesson, 1.4's and 3.4's smoke notes and 3.8's visitor rules on acme, and 1.2's copy of the maternity amendment on globex. The manifest gives them no class, and the kit has no command that classes such an object: `FOLLOW=` refuses a name the manifest does not class. Each routed company has 198 examples: 51 handbook, 129 statute and 18 out of scope, and none for `case` or `clarify`, because the route set has no such rows yet. acme's `desk_route` is `on`, and `make desk` reminded you that the router's alert policies wait until it has taken some turns. globex answers from the law alone. Its `not_readers` lists the four queues nobody on globex reads yet; only POSH must have a reader before a desk goes on. `documind-gchat` is deployed and answers nobody yet: no company has `desk_gchat` on, and no Chat app calls it. The chat service reads the switches within 60 seconds and an index within 5 minutes: wait five minutes before step 4.

### The Desk page, and the HR Desk app in Google Chat

A question back, a handbook answer, a statute answer with its in-force lines and an invoice turned away, signed in as yourself; then, with Google Workspace, a handbook answer and a disclosure in Google Chat.

The Desk page draws a routed half while a company's `desk_route` is on or single. Its file's docstring says what that half does:

#### Do it: the questions, and the page

- A question with no desk in it. Open the address in a new tab, or reload the page, so that the Desk starts a new conversation. Sign in as yourself and choose Desk. You hold `employee` and acme's `desk_route` is on, so the page shows Ask the Desk where 5.6 showed Tell the Desk, with the caption "DocuMind sends your question to the desk that answers it: your company's handbook, the law, or a person." Type "What is the notice period?" into "Your question" and press Ask. It names no grade, no clause and no Act, and both desks hold notice periods. When the two signals disagree and the arbiter chooses `clarify`, the reply asks which desk you mean, the likelier first: "Should I answer this from the company handbook or from the law?", with two buttons, Ask what the company handbook says and Ask what the law says. Press the handbook's. The page asks the same question of the handbook desk, and no model chooses the desk this time. If your two signals agree on handbook instead, you get the handbook answer at once and no buttons. That is the router working too, and step 7 shows the same question on the eval account. Ask it first: after an answer from one desk, the router may take a short question like this as a follow-up and keep that desk, with no question back (the method `sticky` on its row in step 8).

- A handbook question. Paste the lk-06 question and press Ask. The reply is one answer with its citations, all from `acme/hr_policy_2026.md`, saying 60 days. Below it is the caption "DocuMind's answer from your company's documents and the law it holds. If you need a person, raise a case."

- A statute question. Paste the lk-17 question. The statute desk answers from the Acts and the ministry's guidance only. Below the answer's text, in the same reply, is one line for each Act it cites, repeating what the corpus's own text says about when that Act comes into force or what repeals it. Which Acts it cites is your retriever's choice. If it cites the Code on Social Security, that line says the Code comes into force on the date the Central Government appoints by notification, and that the date is not shown until a person has checked it against the Gazette. The last line is "Legal information, not advice."

- An invoice. Paste the lk-10 question. Its invoice number is an anchor, so the reply comes at once and costs nothing: "This is outside what DocuMind's desks answer: it is not in the company handbook or in the law DocuMind holds." Nothing was searched. Under it is one button, Raise a case.

Each question went to the chat service's `POST /v1/desk`, as you, with the page's Desk session, and the page drew the reply only after checking that it named your email and acme. It never shows your question back, and when a call is refused it shows a plain sentence of its own, such as "That choice is no longer on offer. Please ask your question again." for a chip no longer on offer. The handbook and statute answers each ran one rag-api answer over their desk's classes. The question back and the invoice ran no search. The handbook button ran the handbook desk on the thread's last question, which the service read back from its own checkpoint, never from the page. Step 8 reads the `desk` rows your turns wrote, five if you pressed the handbook's button, with no question in any of them.

#### Optional, with Google Workspace: the HR Desk app in Google Chat

This part needs a Business or Enterprise Google Workspace account with Google Chat, in a Workspace whose Chat settings let people use Chat apps. Sign in to the Google Cloud console as a Workspace account that holds a role on your lane's project; whether a project outside the Workspace's organisation can host the app is unconfirmed. It also needs the door on your lane, step 3's optional part. Without such an account, read the expected conversation below as what the door does, leave `desk_gchat` off, and go on to step 5. With the door on, step 7's smoke proves its refusals with no Workspace at all.

Configure the app. In the console, on your lane's project, open the Google Chat API's Configuration page. The kit expects:

- the name HR Desk;

- the add-on model. How the page selects it is unconfirmed. The sign the kit relies on is a service account email shown with the endpoint, equal to `service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com`: on `/` the bridge admits that address and no other. If the page shows no such email, the bridge will refuse every request the app sends, and this part stops here;

- the HTTP endpoint URL `https://documind-gchat-NUMBER.REGION.run.app`, with your project number and region and no trailing slash, because it is the only audience the bridge checks a token for;

- the app available to your Workspace address.

Then run the cell as the operator. It deploys the bridge again, so that its last line now allows the add-on agent. It puts your Workspace address on acme's roster, where with no roles document it holds `employee`. Then it turns the door on for acme. `make desk` refuses `DESK_GCHAT=on` while the company's gate is off, and unless its routed Desk is on or single. For a company whose `data_region` is `in`, it also needs `CONFIRM_RESIDENCY=1`, because the Desk's answers and their quotes then sit in the company's Google Chat. acme's gate has run its rules since lesson 5.6 and its router is on since step 3, and its `data_region` is `any`. The chat service reads the switch within 60 seconds.

- A handbook question. In Google Chat, as your Workspace address, open a direct message with HR Desk, paste the lk-06 question and send it. The reply comes at once: "Thanks. I am reading your question now: the answer follows here in a moment." By then the bridge has checked who you are with the Desk (`GET /v1/desk/check`, at most 5 s), masked the question as the Desk masks, and queued it on `documind-gchat-work`. Its worker asks `POST /v1/desk` for you, giving it up to 180 s, and posts the reply into the same chat as a card headed "From your company handbook", with the sources and their quotes. Answering later is the kit's way around Chat's wait for a reply, which it takes to be 30 seconds. Whether that limit applies to an add-on app, and whether such an app may post through the Chat API at all, are unconfirmed. If it may not, the kit's fallback, `GCHAT_ASYNC = False` in `services/gchat/main.py`, answers inside the request instead.

- A disclosure. Paste the POSH line and send it. The card comes at once, with no acknowledgement. The bridge runs the Desk's gate before every other check, and a hit is answered there and then, never queued and never claimed. The card is the Desk's own: its fixed template, each office's Internal Committee and Local Committee, and a Create a confidential record button for each office, with this line directly above it: "This button sends your case to every Internal Committee member listed above. To leave someone out, use the Desk page instead." This page does not press the button.

What you type in Google Chat stays in that chat, under your company's Workspace retention settings. DocuMind stores none of the disclosure: nothing was queued or claimed, and the Desk's row for it names nobody, as step 8 shows; nor does the bridge's own `gchat` row. A disclosure the gate misses is queued like a question, so it waits in the work queue until the worker answers it, an hour at most, as the card's privacy paragraph says, and no bridge row of that turn names you either. If no acknowledgement comes, read the bridge's `gchat_verify_failed` rows, which step 7's smoke prints: each gives the reason a call was refused, with booleans and never the token. No row at all means the call never reached the bridge's code, as when the add-on agent is not yet allowed to call it. Someone on no DocuMind roster is told "Your account is not on a DocuMind roster, so the HR Desk cannot answer you here."

### Classes, desks, the rules first and the Google Chat door, in the code

How a version gets its class, what each desk may read, the stages of `decide()` that need no model, and how the Desk lets the Google Chat bridge ask for someone.

#### Definition

The worker's hook. `shared/doc_types.assign()` runs before the worker indexes a document. The version gets the registered class only when its `doc_key` is the pin. A registered name arriving with another `doc_key` is logged as a pin miss and stays `unknown`, and a failed read is `unknown` too: a class is never worth a lost document.

The relabel's plan. `relabel.plan()` is pure: rows and registry in, one action per current version out, with why (`pinned`, `pin_miss`, `unregistered`, `reset`), the label each row should carry and the rows that change. An unregistered object is left as it is.

A desk's row. `desk_routes.DESKS` holds each desk's description (L1's prompt describes desks by the documents they own), its classes, the roles it opens to and its chip. `doc_types()` is the only way a desk's filter is read.

The cascade. The router's docstring lists its stages. Stages 0 to 4 are code. Arms C and A* are the eval's, open to a `desk_eval` caller only.

Who, the gate, the masking. `decide()` starts with no text on the decision. A gate hit returns with no text at all. Only after the masking does the decision hold the question, masked. An exception in the roles lookup, the gate or the masking sends the turn to a person; any later one gives the fallback. The router never fails the turn.

Anchors. A clause code counts only when its prefix is in the company's own clause-prefix map, so `NP-03` is a handbook anchor on acme and nothing on a company without `NP`. An Act counts by its title or a short name such as `DPDP Act`. A GSTIN counts only when its check character is right.

#### Do it: the rules on your machine

No lane and no cost: the cell imports the router and runs `decide()` with no models, as an acme employee, on the smoke's disclosure, four questions with identifiers, and one with none.

The disclosure is a case by rule. The invoice, the clause code and the named Act each decide alone. "what bonus do I get" holds the same Act, but "I" is near a case, so the anchor is only a hint and the models are needed. With no models, `decide()` raises inside, and the router's failure path gives the fallback with the reason. The question with no identifier goes the same way. On your lane those two go to the signals.

#### The Google Chat door, in the code

A service of its own, with no IAP. IAP admits a person who signs in, and nobody signs in to the bridge. Its callers are Google's add-on agent for the app and Pub/Sub's push account, so `commands/gchat.sh` deploys it with no IAP and with `--no-allow-unauthenticated`: Cloud Run admits only its invokers, and the code then checks each caller by name. It is a service of its own because of the one thing it can do, which nothing else should: ask the Desk on someone's behalf. Its account holds two project roles, the log writer and a Firestore role limited to its own claims database. It makes no model call and calls no service but the chat service.

One caller for each path. Every request is checked before its body is read: a Google ID token for `SELF_URL`, from the add-on agent on `/` and from the push account on `/work`. Anything else is a 401, "this endpoint answers Google Chat and its own push only", and a `gchat_verify_failed` row. That Chat calls as the add-on agent, at that address, is the kit's assumption until the probe confirms it.

The Desk decides whom the bridge may speak for. A service account cannot mint a token in a person's name, so the bridge names the person in a header, and the Desk, not the bridge, decides whether to believe it. `principal()` is what every Desk and case route asks for its person. With no header it returns the caller unchanged, so the Desk page, the eval accounts and every smoke are served as before. With the header it applies seven rules, in order, each numbered in the code. Rules 1 to 5 judge the caller: it is the one delegate, in this project; the route is one of the six delegable ones, never `/v1/route`, the inbox or a status change; the header names one person's address, once, never a service account; the body has no `arm` and no `prev_*` field; and the profile is not local. Their refusal is a 403 with a fixed reason and a `desk_delegation_refused` row, which the alert "Desk: a delegation was refused" counts. Rules 6 and 7 are about the person: on a roster, in a company whose `desk_gchat` is on. Their 403 is an ordinary answer, with a `desk_delegation_denied` row and no alert. Because rules 1 to 5 come first, a refused caller learns nothing about rosters or switches.

rag-api never sees the header. A delegated turn carries no IAP assertion, so its retrieval reaches rag-api as `documind-chat-sa`, which `make roster` puts on the golden companies' rosters. Whoever could mint a token as `documind-gchat-sa` could speak for every rostered person of every company with the door on, so `tools/check_authz.py` holds the kit to three things: nobody may mint as it, nobody else may publish to its topic, and Pub/Sub's push identity is a separate account that is no delegate.

One card for one reply. `render()` turns what `POST /v1/desk` returned into one Google Chat message in the Cards v2 shape: the POSH card, a case draft to confirm, an answer with its sources and chips, or the Desk's text. Every legal text on a card is the Desk's: the bridge adds only its headers, labels and fixed lines, and escapes every string. A card never shows the person's question, and `sanitise()` removes any `gs://` address or signed URL, because Chat keeps history and a signed URL there works for whoever holds it. `fit()` steps down, to fewer sources and shorter quotes, then the text alone, until the message is under 30,000 bytes. A button calls the bridge back with parameters, never text; that its `action.function` is the endpoint URL is the kit's assumption until the probe confirms it (`cards.action()`).

What is not confirmed. The kit keeps each of its assumptions about Google in one named constant or function, so that the lane probe, the bridge's `gchat_probe` rows, can confirm or correct it in one place. They are: the event's field names and whether an event carries the sender's email (`services/gchat/events.py`); the caller's address (`GCHAT_CALLER`); how the app posts its answers (`post.auth_order()`) and the status a repeated post gets (`post.DUPLICATE_STATUS`); a button's action (`cards.action()`); and several fields in `terraform/gchat.tf`, marked "from memory" there. `make desk-check`, in step 6, runs `commands/tests/test_gchat.py` on the kit's placeholder events, with no call to Google.

### Two signals and one arbiter, in the code

The numbers, L1's schema, the two signals in parallel, the acceptance rules, the arbiter, the graph that runs the chosen desks, and the Desk's offline check.

#### Definition

The numbers. Every threshold sits in one block at the top of the router, under a comment that says what it is.

L1's request. The schema has five fields, each an enum or a boolean, and all five are required. An answer outside the schema is a parse failure, treated like a timeout. The prompt describes each desk by the documents it owns, holds the eight examples of `desk_routes.PROMPT_EXEMPLARS` and the labelling rules, and fences as data the question (up to 1,000 characters), the previous question (up to 300) and the previous route. It carries no company id, name or number. Its version, `2026-10-01.1`, goes on every row.

The two signals. Inside `_route()`, L1 and the vote start together on a thread pool. L1 is counted on the turn's Meter before it is sent, so a turn at its model-call cap sends none. Both are waited for until 4 seconds after they start, and never past the router's 8-second budget. Then `accept()` runs on what came back. With no verdict and no L1 answer, the turn takes the fallback. With no verdict but an L1 answer, rule F.

The acceptance rules. Rule D asks only for a sign of a case, from either signal. Rule A needs the two to agree at 5 of 7. The share is votes over 7, not over the index, so a small index is never confident. Rule F's enum is L1's route, the vote's route and `clarify`, each once.

The arbiter. One call, given whatever is left of the budget, at most 6 seconds. A choice outside the candidates is a parse failure. On any failure L1's route stands with confidence low, and the checks add the desk chips so the person can choose.

The graph. `services/chat/desk_graph.py` runs only answer, clarify and fallback turns; a case, out-of-scope, denied or not-covered turn is answered by code and never enters it. `dispatch()` calls no model and goes to the first desk the decision names. The parts are a list the router fixed, and `next_part()` only pops it: a second desk starts only while the turn has 30 seconds left, and otherwise becomes a chip. No tool can name a desk, and no desk can hand the turn to another.

The in-force lines. For each Act an answer cites, `in_force_line()` says what the corpus's own text says: when the Act comes into force, what repeals or amends it, or how current the text is. No date is shown while `IN_FORCE` holds none, and in your kit it holds none, so the Codes' lines say the date is not shown until a person has checked it against the Gazette.

Agent mode. When L1 says the answer needs arithmetic on figures in the question (`needs_calculation`), the handbook or statute desk runs as a small agent with the desk's calculators from `shared/desk_calc.py`, under the same turn limits. The model reads the passages and chooses the call; code does the arithmetic and names the clause or section it rests on. A gratuity figure is always labelled an estimate.

#### Do it: the router on every dev row, on your machine

No lane and no cost: `evals/route_eval.py --local` runs `decide()` in process on every scored dev row, with a scripted classifier and offline embeddings. For each row, it takes the row's own group out of the vote first, so a question never finds itself.

The first line says what this measures: the cascade, not a model. The scripted classifier answers each row's own label, and is wrong on purpose on about one row in eight; its arbiter picks the label whenever the label is among the candidates. So the accuracy says that the anchors, the vote, the acceptance rules, the arbiter's enum and the checks carry a question to the right desk when the signals are this good. The methods show how much code settles: the anchors, and the nine globex rows in single mode. Rule F took 48 rows, where the offline vote did not back L1 at 5 of 7. The cost line counts the scripted calls at four characters a token. Step 10 runs the same rows through your lane's real models.

#### Do it: the Desk's offline check

`make desk-check` is the proof that the Desk's code holds, with no lane and no cost. It checks that the route set is the one `evals/build_routes.py` builds and that every row is sound, runs the self-tests and unit tests of the eval and the probe, runs the router on the dev rows as the cell above did, checks that the threshold sweep counts right, and checks that every calculator rule says what its line of the corpus says. Then it runs the chat service's tests for the case queue, the router and the desk graph, which need the chat image's libraries: the first run makes `~/graph-venv` and installs `services/chat/requirements.txt` into it, which takes a few minutes. Every line must pass; a failing one stops the run.

### /v1/route and /v1/desk, over REST

Decisions alone as an eval account, answers, the three callers a router must not get wrong, a figure worked out in code, then the smokes: the routed Desk's and, with the door on, the Google Chat door's refusals.

#### Definition

The chat service's docstring lists the routed Desk's three routes, and the shadow. The third, `GET /v1/desk/check`, is for the Google Chat bridge, which asks it on a person's behalf before it queues a question; the cells below do not call it.

The tenant, the person and the previous turn are never fields of `/v1/desk`'s body: the service reads the first two from your identity and the third from the thread, and an unknown field is a 422. `/v1/route` answers a `desk_eval` caller only, at most 120 calls a minute per account in each worker. It has no thread, so its body may carry `prev_question` and `prev_route`, which stand in for the earlier turn a follow-up row of the route set needs. Its reply is the decision: the route, the method, the rule that accepted it, the signals, the calls and the rupees.

#### Do it: decisions

Five questions to `/v1/route` as `evalacme`: the smoke's disclosure, an invoice, a clause code, a named Act, and lk-06 with no identifier. Then lk-06 again, as `documind-ui-sa`.

Four decisions cost nothing: the gate took the disclosure, and the invoice number, `NP-03` and the Bonus Act each decided alone. lk-06 needed the models. On your lane its line shows how many of the 7 neighbours voted handbook and how close the nearest was. lk-06 is itself a dev row in the index, so its nearest neighbour is its own text. `ui-sa`, the UI's own account, which `make smoke` calls as, holds no `desk_eval` role and is refused.

#### Do it: answers

lk-06 and lk-17 to `/v1/desk`, each in its own session. For each section, the cell prints the title, the objects cited, whether the answer holds the route set's expected words, and the in-force lines.

The handbook section cites only `hr_policy_2026.md`, the one `policy` object acme holds. The statute section cites only Acts and the ministry's guidance. Its in-force lines follow the order of the citations, each Act once, and end with the same line every time.

#### Do it: the leaver, the single desk, and a question back

lk-06 as the leaver; globex's DPDP question as `evalglobex`; "What is the notice period?" as `evalacme`.

The leaver's roles open only the case desk. The words do not show that, so the router ran its signals, chose handbook, and the roles check then denied it, with no search, and offered a case. globex is in single mode: statute, method `single`, no classifier and no model call for the routing. The last question names nothing, and on the stand-in that built this page the two signals disagreed, so the arbiter chose `clarify`. On your lane the models decide; if they agree on handbook, this line is a handbook answer instead.

#### Do it: a figure, worked out in code

jn-03 asks for a figure: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" When L1 marks a question `needs_calculation`, the handbook desk runs in agent mode. A small agent searches the handbook's passages, and a calculator from `shared/desk_calc.py` does the arithmetic. The calculator takes the balance only from the person's message and the cap only from clause LV-07 of a passage this turn read; any other number is refused, and the agent is told why.

The route is handbook, chosen like any other; the section's `mode` is `agent`, and its calls are in `tool_calls`. The block after the answer is written by code, not by the model: the formula, where each number came from, and the condition LV-07 sets. The 60 days need no arithmetic: NP-03 states them, and the agent read and cited it. On the stand-in that built this page a scripted model played the agent. On your lane `gemini-3.6-flash` chooses the searches and the calls, so its words, its number of searches and its `model_calls` are its own, and the block appears only when it called a calculator.

#### Do it: the live smoke

`smoke/smoke_desk.py` checks the routed Desk in one run, as the eval accounts, then runs 5.6's case-queue smoke. Its questions are the route set's own rows, read by id, and each run uses fresh sessions.

The routed Desk's 8 checks passed. The handbook answer cited acme's own objects and held the row's expected words. The statute answer carried its in-force lines. The disclosure was a case by rule, with no model call, no case written and the POSH card naming each office's Local Committee. The invoice was out of scope by its anchor, with nothing searched. The leaver was denied with no retrieval. globex answered from its single desk. `/v1/route` answered `evalacme` and refused `ui-sa`. Then the case queue's 11 checks passed as in 5.6: acme's gate is still in front of everything.

#### Optional: the Google Chat door's refusals

This needs the door on your lane, step 3's optional part, and no Google Workspace. On a lane whose last apply had the door off, `make smoke-gchat` refuses and says so. `smoke/smoke_gchat.py` sends four requests that must be refused. Steps 1 and 2 go to the bridge as `documind-outsider-sa`: a Chat-shaped event to `/` and a push envelope to `/work`. The outsider is one of the bridge's invokers, so Cloud Run lets it in, and the 401, "this endpoint answers Google Chat and its own push only", comes from the bridge's own code. Steps 3 and 4 go to the chat service's `POST /v1/desk` as `documind-evalacme-sa` and as `ui-sa`, each naming a person in `X-DocuMind-Principal`, and the Desk's rule 1 refuses both: "not an allowed delegate". Then the smoke prints the latest rows of each kind from the last hour. The kit's comments call steps 3 and 4 the alert's own test: each writes a `desk_delegation_refused` row, which "Desk: a delegation was refused" counts, so expect it to fire and notify whatever channels your lane's alerts use. That is on purpose. No step shows the door accepting a call, because nobody may mint a token as `documind-gchat-sa`, by design. A person in Google Chat, as in step 4, is that proof.

Two `gchat_verify_failed` rows give the reason `wrong_caller`, with booleans about the refused token and never the token itself. Two `desk_delegation_refused` rows name the caller, the reason and the path, and no person. The `gchat`, `gchat_answer` and `via` "gchat" rows show `(none)` unless someone messaged the app in the last hour.

### The shadow, the rows and the log

zeta's router in shadow beside ordinary chat turns; a chunk, its registry entry and an exemplar in Firestore; every row the router logged; the Google Chat door's rows and claims; the Desk's day in BigQuery; then zeta on.

Shadow first. A company that is not ready to route can let the router watch. With `desk_route` at `shadow`, every `/v1/chat` turn for that company is answered by its brain as before, and the router decides the same question beside it, with its own Meter, and logs a `desk_shadow` row. It answers nothing and keeps nothing. Shadow needs `desk_gate` not off, so the door answers every disclosure before the router could see it; zeta already has the gate's rules, because nothing has switched them off. zeta goes on to `desk_route` on later in this step, and the routed Desk waits for a complete POSH queue. So zeta gets its queues, with `evalzeta` as head office's committee, then the role, then the shadow.

#### Do it: three ordinary chat turns

Three of zeta's route-set questions to `/v1/chat` as `evalzeta`, with the direct brain: a travel cap from zeta's handbook, the Code on Wages, and zeta's own contract.

#### Do it: the rows in Firestore

acme's chunk for `NP-03`, the handbook's registry entry, the exemplar for lk-06, and the three companies' switches, read with the Firestore client.

#### Do it: the log

Every `desk` and `desk_shadow` row the chat service logged since step 3.

#### Optional: the Google Chat door's rows

This needs the door on your lane, step 3's optional part: without it there is no `documind-gchat` database to read. Two direct reads of what step 4's conversation left, if you had it. The `desk` rows with `via` "gchat" are the Desk's own rows for the turns the bridge asked for. The handbook turn names you and the delegate; the disclosure's names nobody, as on the Desk page. The bridge's claims are in its own Firestore database, `documind-gchat`, never the default one where the rosters and roles live. A claim stops a message that Chat delivers twice, or that Pub/Sub pushes twice, from being answered twice. Its id is a hash of the message's name, it holds no text and no email, and it expires 24 hours after it was made. A TTL policy then deletes it; how soon after is not confirmed.

The disclosure has no claim, because a gate hit is never claimed. If you did not configure the app, both counts are 0.

#### Do it: the Desk's day in BigQuery

Since step 3's apply, the log sink copies the chat service's `desk` rows into BigQuery. `make desk-views` checks `terraform/sql/desk_daily.sql` with a dry run, then creates the view `documind_observability.desk_daily`: one row per India day, company, desk and kind of caller, with the turns, their outcomes, the escalations, how each turn was decided, the arbiter's share, the chip turns, the rupees and the latencies. No column names a person, a session or a question. The `bq` query then reads today's rows. Run it a few minutes after step 7, since the sink takes a little while to deliver rows and BigQuery types the table's columns from the rows it has seen. This is a preview; lesson 11.5 explains the sink and the views.

#### Do it: zeta on

The shadow rows are what a company reads before it switches. On the stand-in they agree with the route set's labels. Read yours first, and switch zeta on when they do.

The three chat turns were answered by the direct brain as before, each holding its expected words where the row has some. Beside each, the router wrote one `desk_shadow` row. On the stand-in that built this page, for example, the models chose handbook and out of scope, and the Code on Wages went by its anchor; on your lane the model rows are your models' choice. The chunk's class is `policy`, and its `doc_key` is the registry's pin, so the next ingest of the same bytes keeps the class. The exemplar holds a 7-neighbour vote's raw material: a route, a group, a 768-dimension vector and the index version. The log has one row for every turn the routed Desk decided: your turns from the Desk page, the cells' and the smoke's, with surface `route` for the decisions alone. The refused `ui-sa` call was turned away before any decision, so it has none. The disclosure's rows name no person. No row holds a question. The routes on the model rows are your models' choices, and step 10 counts how often they match the labels. `desk_daily` counts the same `desk` turns by company, desk and caller, with no person in any column. If you had step 4's conversation in Google Chat, its two turns are `desk` rows like any other, with `via` "gchat", and its one claim holds six fields and no words.

### Why it is shaped this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Code before models. Who is asking, the gate, the masking and the anchors cost nothing, cannot be talked round, and can be read and tested. A disclosure the gate recognises never reaches a model, and an Aadhaar or card number with a valid check digit is masked before anything reads the words. The gate is pattern rules, so rule D is there for the disclosures they miss.

- Identifiers, not topic words. An anchor is something a question can only mean one way: a clause code the company itself uses, the title of an Act, an invoice number, a checked GSTIN. Topic words such as "leave" or "bonus" are what the signals are for. A question near a case keeps its anchor only as a hint.

- A classifier with nowhere to write. L1's schema has no free-text field, so a question that says "ignore your instructions" can at most choose a wrong desk, and the desk's filter still holds. Its output is a few tokens, and an answer outside the schema is caught as a parse failure.

- Two signals that fail differently. L1 reads the desks' descriptions and the rules. The vote reads the route set's labelled examples, the same rows for acme and zeta. When they agree at 5 of 7, the turn costs one cheap call. When they disagree, one stronger call settles it.

- Asymmetric on purpose. Rule D escalates on any sign of a case, from either signal, before anything else: a wrong escalation costs a queue a minute, a missed disclosure is a legal failure.

- The arbiter chooses, it does not invent. L2's enum is what the two signals proposed, and `clarify`. It cannot name a desk neither proposed.

- The filter is code. A router error sends a question to the wrong desk; it never widens what a desk reads. The handbook desk reads `policy` and nothing else.

- No hand-offs. The parts are a list the router fixed and the graph pops. No tool names a desk, no agent hands the turn to another, and a desk that cannot answer offers a chip, which is a new turn the person chooses.

- Never a 500. An exception in the roles lookup, the gate or the masking sends the turn to a person, with no text kept. Any later exception, or more than 8 seconds, gives the fallback: one answer over every class the person may read, with the desk chips.

- Shadow before on. A company can watch the router decide its real traffic, with every answer unchanged, before it switches.

- Unreviewed text is on no desk. A class is pinned to the bytes a person reviewed. A new version stays `unknown` until someone reads it and re-pins it with `make doc-types FOLLOW= APPLY=1`.

#### What it costs

From the kit's prompts and `shared/prices.py`, at Rs 85 to the dollar. Token counts are estimates at four characters a token, for lk-06's question; a longer question costs a little more. `make route-probe` measures the real output tokens on your lane.

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The thresholds are not calibrated. 7, 5, 3, 0.70, the 4, 6 and 8 seconds, the 30 minutes and the 30 seconds of a second part are starting values. `evals/route_threshold.py` sweeps `TAU_OOS` and `ACCEPT_VOTES`, and is meant to run once people have written and reviewed rows.

- No person has written a route row. All 207 rows of `evals/routes.jsonl` are model drafts, and the test split is empty. So `make route-eval SPLIT=test` fails its gate on every lane until people write the test rows.

- No case, clarify or escalation rows. Recall for `case` and `clarify` is 0 of 0, escalation recall is not measured, and the index holds no case example, so the vote's half of rule D cannot fire yet. Only L1 and 5.6's gate escalate.

- English only. Every route row is in English. 5.6's gate has Hindi and Hinglish examples; the router's routing of Hindi and Hinglish questions is not measured.

- The dev figures are optimistic. The deployed index holds the dev rows themselves, so in a live dev run the vote finds each question's own row. `--local` holds each row's group out; a live run cannot.

- Rule E is not built. Accepting L1 on its own confidence needs flash-lite on `global` to return its top two logprobs, and the probe has not shown that.

- L2 thinks at LOW. MINIMAL waits until the probe shows `gemini-3.6-flash` takes it.

- The router's alerts are off. Its three alert policies (the fallback share, the L2 share, and clarify and out-of-scope week on week) exist only on a lane planned with `DESK_ROUTER_ALERTS=true`, and the default is false.

- No in-force dates. `IN_FORCE` holds no date until a person enters the Labour Codes' and the DPDP Act's dates from the Gazette.

### Verify it yourself: the eval and the checklist

The router's eval on the dev split, the test split's gate, nineteen checks, and Module 5's gate.

#### Do it: the router's eval, dev split

`make route-eval` posts every scored dev row to `/v1/route` as the row's own eval account: 187 rows, with the 20 rows of the prompt's example groups left out, since the prompt has seen them. Each handbook, statute and denial row, 173 of them, goes to `/v1/desk` too, for its answer and citations. The report gives each rate with its interval, the confusion matrix, whether answers cite only the desk's classes and the caller's company, the router's cost, and the p50 and p95 of the routing and of the answers. The dev gates are a route accuracy of 95% or more, each desk's recall at 90% or more, and every escalation row escalated; a `FAIL` line names a gate missed. If the Desk answers 429, more than 120 routes a minute from one account, the eval waits the minute out and tries again, up to three times.

Read the figures as an upper bound: the vote finds each question's own row in the index. The denominators are the route set's, the same on every lane. The rates, the rupees and the times are yours. `case` and `clarify` recall are 0 of 0 on every lane, because the route set has no such rows.

#### Do it: the test split

This is the gate this lesson's proof names, and it fails on every lane: the test split has no rows, so `route_eval.py` returns 1 and make stops with `Error 1`. It waits for people to write the test rows, escalation rows among them, and for the thresholds to be calibrated on the dev rows first. Until then, the dev run above is the measurement, and an optimistic one.

#### Do it: Module 5's gate

The chat service keeps the gate lesson 5.7 set: `make smoke-chat PROJECT=documind-ai-YOUR-ID`, the four brains and the outsider. The routed Desk sits beside `/v1/chat`, not in front of it, so every brain answers as before.

Your lane runs the kit you pulled, with `DESK_JOB=true` kept. `evalleaver` is on acme's roster as a leaver and `evalglobex` on globex's; `evalacme`, `evalleaver`, `evalglobex` and `evalzeta` hold `desk_eval`, and `evalglobex` and `evalzeta` hold `ic_member:head_office` in their companies. acme, zeta and globex each have a doc_type registry set by you, and every current row of a registered object carries its class in Firestore, Vector Search, Vertex AI Search and BigQuery; their answer caches were expired. The objects earlier lessons uploaded that the manifest does not name, such as the smoke notes, stay `unknown` and on no desk. acme and zeta each hold 198 exemplars. In `tenant_settings`, acme's `desk_route` is on; zeta has its queues, the gate's rules and `desk_route` on; globex has its queues and a single statute desk. Your home folder has `~/queues.globex.json`, `~/queues.zeta.json` and `~/graph-venv`. BigQuery has the `desk_daily` view. If you ran step 3's optional part, your lane also has the Google Chat door, and `GCHAT_DOOR=true` goes on every later plan beside `DESK_JOB=true`: the `documind-gchat` service, running as `documind-gchat-sa`, with `documind-gchatpush-sa` as Pub/Sub's push identity; the `documind-gchat` Firestore database for its claims; the `documind-gchat-work` topic and its push subscription, `documind-gchat-push`; and the Chat API. `desk_gchat` is on for acme only if you configured the app in step 4, and then your Workspace address is on acme's roster too; it is off for every other company. The log holds `make smoke-gchat`'s two refused delegations, if you ran it, which the alert "Desk: a delegation was refused" counted. From now on, an acme or zeta employee who opens the Desk page gets Ask the Desk, and every globex question on the Desk goes to the law. A new version of a registered file stays `unknown`, and off every desk, until someone re-pins it. The router's alert policies are still off: once it has taken some turns, `make plan up DESK_ROUTER_ALERTS=true`, as `make desk` printed, and keep the flag on every later plan, beside `DESK_JOB=true` and, with the door on, `GCHAT_DOOR=true`. A Desk turn that code answers writes no checkpoint, though a case turn may open a case draft, which for most case types starts with the person's masked question. An answer, clarify or fallback turn keeps its thread in the chat service's checkpointer, under a session of its own. Lesson 10.5 runs one desk as an agent whose every calculator argument is checked, and measures routed desks against one agent and no agent.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.4 Route each question to one specialist agent · v5.0

Next: Lesson 10.5 Run a desk as an agent with checked calculator arguments.
