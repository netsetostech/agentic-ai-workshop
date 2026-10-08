# Lesson 5.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.6_Case_Desk_WIX.html`, reviewed at blob `ffa6d70e006958e3f835fa26f78e425518dd3f27`. Learners read that page on the course site; this guide keeps its prose.

Some questions are not DocuMind's to answer. A disclosure of sexual harassment at work, a complaint about how a person is treated, a request about one's own personal data, wages still unpaid after leaving, and "let me talk to a person" belong to the people the law or the company names. In this lesson the kit finds those questions by rule, before any search or model runs, and answers each one with a fixed text. The text is the same at rag-api's door and at the chat service's door. The person can then raise a case that only the right people can read. On your lane you load acme's queues, see that its gate already has its rules with nothing switched on, and give its Internal Committee the roles that read POSH cases. Then you send a disclosure through every door, and raise, confirm and close a case as the eval accounts. Last, you read the records, the audit events and the log rows the Desk leaves behind.

- Five kinds of question that go to a person

- The words: gate, class, DISCLOSE, PROCESS, information frame, fixed reply, desk_gate, door, mask, role, queue, case

- Before you run anything: set up the shell

- Your lane: the Desk's resources, accounts, queues and roles

- The Desk page: tell, raise, read

- One fixed reply at every door

- Roles and cases, in the code

- The case routes, over REST

- The records, the audit events and the log rows

- Why it is shaped this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how the kit finds, by rule and before any model, the questions the law hands to a person, how it answers each with one fixed text at both doors, and how a case reaches only the people who may read it. Then you will prove it on your lane: the gate already answering with nothing switched on, a disclosure answered with model none at every door, and a grievance raised once, read by the committee and closed.

### Five kinds of question that go to a person

What the gate looks for, what it answers, and where the case goes.

Some answers belong to a person. DocuMind answers from documents. "My manager keeps making sexual comments about my body. What can I do?" is not a question about a document. The POSH Act gives it to the employer's Internal Committee. The person decides what to tell them, and the committee can explain the time limits the Act sets. A model that answered it would put the person's words in a prompt, a cache and a log, and would answer what the committee is there to hear. So the kit's `shared/desk_rules.py` names five classes, most protective first: `posh`, `grievance`, `privacy_request`, `exit_dues` and `human_requested`. Its `gate()` returns the class and nothing else. It never returns the words that matched, so no caller can log them or echo them back.

A rule, not a model. `gate()` is a set of regular expressions, in English, in Devanagari Hindi and in Hinglish (Hindi typed in Latin letters). A class fires only when the question holds two things: a first-person marker or a plain request for a person ("Talk to a person.", "HR se baat karni hai"), and one of the class's topic patterns. Each class has two kinds of topic pattern. A DISCLOSE pattern says it happened to the person, or names who did it, and it fires whatever else the question says. A PROCESS pattern names a step, such as filing a complaint or raising a grievance. It fires only when the question has no information frame ("under the Act", "how do I", "can I"), or when the person plainly asks for the step itself ("I want a copy of my data"). `exit_dues` has a test of its own: money a leaver is owed, words saying it has not been paid, and no sign that the leaving is still to come. A rule can be read, tested and versioned: `RULES_VERSION`, 2026-10-01.4 in your kit, goes on every row the gate writes.

One fixed reply, at every door. When a class fires, code writes the reply, unless the company has switched the gate off. `shared/desk_law.py` holds one text per class, and the reply carries model `none` and a cost of 0. Nothing is searched, generated or cached. Two doors give it. rag-api's door sits in front of `POST /v1/query`, `/v1/stream` and `/v1/passages`. The chat service's door sits in front of `POST /v1/chat`, before any brain runs. The second door is needed because an agent brain sends the person's words to its own model before it calls rag-api, so rag-api's door would see only the search words that model wrote. Each answered hit logs one row with the class and the rules version. For `posh`, `grievance` and `privacy_request`, the row logs the class as "sensitive" and the person as null.

A switch per company. Each door reads `tenant_settings/{tenant}.desk_gate`, which has three values. `rules` is what every company has until an operator writes something else: a missing field and a value the doors do not know count as `rules`, and a read that fails is never off (rag-api's door reads it as `rules`; the chat door keeps the last value it read, `rules` if it has none), so the gate never goes off by accident. `off`, written on purpose with `make desk`, lets every question through as before. `on` adds a model check behind the rules (`shared/desk_recall.py`): one `gemini-3.1-flash-lite` call with an enum-only answer, on each question a person sends through `/v1/chat` or the Chat page that the rules let through, for the disclosures no pattern catches. A company whose employees use the Desk would switch it on. Your lane leaves acme on `rules`, so no later lesson pays for that call. None of the three needs a case queue: the fixed replies name the committees and contacts the law names. The services read the switch within 60 seconds. Unless the switch is off, a door also masks Aadhaar numbers (Verhoeff-checked) and card numbers (Luhn-checked) in a question that does not hit the gate, before any handler reads it.

A case for the right people. After a fixed reply, the person can raise a case. The chat door's reply names the kind of case it offers (`case_offer`): a class, never the words that matched. rag-api's door gives the reply alone. The Desk page opens the POSH card at once. For any other class it shows a button that starts that kind of case with an empty form. Nothing typed in the box goes into a case. The company's roles decide who reads it. An `employee` raises cases. A `grc_member` reads grievances and moves them along. An `ic_member:` reads the POSH cases of that office, and only those that name them. A POSH case opens at once, with the office and the members the person chose, and holds no text. Every other case starts as a draft. The person reads it and sends it within 30 minutes. Sending carries a token, so pressing twice opens one case. Each change to a case is an audit event, and the event's actor is a case reference, never an email.

A hospital reception that sends chest pain straight to the emergency bay. The receptionist does not diagnose. Most people get a token and a seat, and wait for the clinic they asked for. A few words change that. Someone who says "I have chest pain" is not handed a token. They are walked to the emergency bay at once, however long the queue. The receptionist says the same thing to each of them, read from a card the hospital wrote, and does not ask how it feels. The register notes that a chest-pain case came in at 10:40, not who it was. Some sentences only look alike: "My father had chest pain last year. Is cardiology open on Sunday?" gets a token like any other question. The emergency bay is the Internal Committee. The card is `desk_law.py`. The register is the log row that says "sensitive". The sentence about the father is a near miss.

#### Ask the gate

Choose a question. 14 of the 16 questions are the kit's own: the disclosure `make smoke-cases` sends, and examples and near misses from the gate's tests. The other two, with numbers in them, are this page's. The verdict is `gate()` itself, run on each question when this page was built. The ticks are the checks it made, read from the same patterns. For a class, the panel shows what acme's Desk does with it: the reply, the case the reply offers, the queue, the due date, the clock and the law, with the corpus line each passage rests on.

Each verdict is `gate()` from your kit's `shared/desk_rules.py` (rules 2026-10-01.4), and the build checks that each tick list reaches the same verdict. The replies come from `desk_law.template()`, the buttons from the Desk page's own `START` labels, the queues and readers from `desk_law.QUEUES`, and the due dates from `cases._due()` with `evals/desk/queues.acme.json`. The clocks come from `cases.clock()`, the law from `desk_law.basis_for()`, and each quoted line is read from `evals/corpus/acme` at the lines the kit names.

It is not a reading of what the person meant. `gate()` reads words. "Someone touched my laptop" names no person it happened to, and "Can I file a POSH complaint after three months?" asks how the process works, so both go to the documents. A model wrote the examples and near misses, 111 and 122 of them, to test the lexicon before people-written rows exist. A fluent Hindi and Hinglish speaker has not reviewed them yet. The law shown is the kit's own table, with the corpus line each passage rests on. It is not legal advice.

### The words: gate, class, DISCLOSE, PROCESS, information frame, fixed reply, desk_gate, door, mask, role, queue, case

Eighteen rows, each with the value it takes on your lane.

One distinction to hold: the gate decides that a person should answer, and the queue decides which person. The gate needs no database and no identity, so it runs first. The queue needs both, so a case goes through the roster, the roles and the company's own queues file.

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

You need the shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `ME`, `API` and `tok`. Step 3 changes your lane. It applies the Desk's Terraform, deploys rag-api, the UI and the chat service with the Desk's code, declares the hourly overdue job, and gives acme its queues and roles. Once the services carry the Desk's code, every question that hits the gate gets the fixed reply, in every lesson and for every company, with no switch to turn on. Run steps 3 to 8 in the same shell, in order: step 3 defines `CHAT`, `UI`, `SINCE105`, `sa` and `etok`, and the later steps use them.

### Your lane: the Desk's resources, accounts, queues and roles

The Terraform, three services and the hourly job; the eval accounts; acme's queues and its switch as it stands; then the roles.

#### Do it: the Desk on your lane

On a lane whose last plan predates the Desk, the plan adds 23 resources. `terraform/desk.tf` has 12 of them: two TTL fields (a draft's `expire_at` and a client token's), five indexes (one for each query the case queue makes) and five eval accounts. `terraform/desk_alerts.tf` has six log-based metrics and four alert policies, and `terraform/storage.tf` lets the chat service write the audit bucket. The one change is the log sink's filter, widened to copy the Desk's rows to BigQuery. Three switches would add more, and this lesson needs none of them: `GCHAT_DOOR=true` adds 11 for lesson 10.4's Google Chat door, `DESK_ROUTER_ALERTS=true` the router's three alert policies, and `DESK_GATE_ALERTS=true` the policy that pages when a company's model checks keep failing, for a lane where some company has the check on. Then come the images with the Desk's code, deployed by their own scripts. `lesson-12.8.sh` builds the chat image itself and lets the eval accounts invoke `documind-chat`. Last, `make desk-job` declares the hourly overdue scan on that chat image: a plan with `DESK_JOB=true`, which adds the job's three, then its apply. The whole cell takes many minutes. The flags are the ones you gave `make up`.

The job is declared by Terraform only while `DESK_JOB=true`. From now on, pass it to every `make plan` and `make up`, and to `make reconcile-job` and `make batch-job`. Each of them is a plan through `make plan`'s guard: without the flag the plan would delete the job, and the guard refuses it before anything changes, naming the switches a lane has to keep passing. The second line `make desk-job` printed says the same.

#### Do it: the eval accounts

A script cannot call the chat service as a person, so the kit has eval accounts. Each is a service account on one tenant's roster, with no project role, and `make smoke-cases` and this lesson's cells call as them. `evalacme` is an acme employee, `evalgrc` an acme Grievance Redressal Committee member, and `evalzeta` a zeta employee. `make desk-operators` lets you mint tokens as all five. The cell also sets `CHAT` and `UI`, notes the time in `SINCE105` for step 8's log read, and defines two helpers: `sa` names an account, and `etok` mints a token as one, for the chat service.

#### Do it: acme's queues, and its switch as it stands

`evals/desk/queues.acme.json` names acme's queues: who receives each kind of case, and the company's target in days. For POSH it lists each office's Internal Committee and its district's Local Committee. The file puts `you@example.com` on both offices' committees, and the `sed` puts your own email there instead. Then `make desk`, with no `DESK_GATE`, prints acme's switches and writes nothing.

The queues were written. `desk_gate` reads `rules`, though nobody has written it: the gate has answered acme's disclosures since the deploy, and the queues were never its condition, because its replies are fixed. `not_readers` lists every committee contact who holds no role that reads the queue, and every queue nobody reads; at this point that is all of them. That matters for the case, not the reply. A POSH case can be read only by a chosen member who holds the office's `ic_member` role, so without one, a disclosure gets its fixed reply and the record the person raises reaches nobody. `make desk DESK_GATE=on` would add the model check; this lane does not switch it on, so acme stays on `rules`, as the switch's paragraph in step 1 explains.

#### Do it: the roles

`evalgrc` gets `grc_member` alone, so it can read and move grievances but cannot raise a case: the note says so. You get `employee`, so the Desk page shows you Tell the Desk and lets you raise cases. You also get the three roles that read: grievances, and the POSH cases of both offices.

Before each change, both accounts read as `["employee"]`, because a member with no role document is an employee. `make roles` wrote a document for each, with you as `set_by`. It also wrote three audit events: a grant and a revoke for `evalgrc`, whose employee role went, and a grant for you. With you holding `ic_member:hyderabad` and `ic_member:pune`, each office has a member who can read its POSH cases, so the record you raise in step 4 reaches someone. Roles are read on every request, so step 4 needs no wait.

A person on a real lane would not hold all four roles. The one who raises a POSH case and the member who reads it are different people. Here you are both, so one sign-in shows both sides.

### The Desk page: tell, raise, read

The disclosure in the Desk's own box, a POSH record and a grievance raised, and both in your inbox, signed in as yourself.

The UI now has a Desk page beside Chat. Its file's docstring names what it reads and its four parts:

#### Do it: the words, and the page

- Tell the Desk. Open the address, sign in as yourself and choose Desk. Before it draws anything of yours, the page reads `GET /v1/cases/offer` and `GET /v1/cases`, and each read that answers must name your email and acme. If one names someone else, such as the UI's own account when IAP is not in front of it, the page shows one warning under its title and nothing else: "The case desk needs your company's sign-in (IAP), and it could not confirm that you are the person signed in here, so nothing is shown. Please ask your administrator to check the sign-in." The Tell the Desk box is there because you hold `employee` and acme's `desk_gate` is not off. Paste the sentence into "What do you need help with?" and press Send. The reply is the `posh` text the widget in step 1 shows, word for word. Below it is the caption "This is a fixed reply. No AI model was used. To reach a person, raise the case below. A case does not include what you typed here."

- A POSH record. The reply offered `posh`, so under Raise a case the page has already chosen "Sexual harassment at work (POSH)" and opened its card. The card shows the office you choose, its Internal Committee and its district's Local Committee, from the queues you loaded. Choose Hyderabad. Under "Internal Committee members to contact", choose yourself: the file you loaded lists your email as Hyderabad's Presiding Officer. Then press Create a confidential record. The card says "Recorded. Your case reference is" and eight characters: the first eight of the case id, in capitals. Below that are who has the case, its "Target date:", the clock lines and the law. Nothing you typed is in it. Record another would start a new record with a new token. You do not need it here.

- A grievance. Under "What is it about?", choose "A complaint about how I am treated at work". Write a sentence of your own and press Next: check it before sending. Read the draft: who it goes to, the clock line and the law it rests on. A draft has no date yet. Then press Send. The page says "Sent. Your case reference is" and eight characters, and that you can follow it under Your cases. There, the grievance shows its "Target date:", set when you sent it, with the clock lines below it.

- Your inbox. Your cases lists both, as "POSH complaint. Status: Sent" and "Grievance. Status: Sent". Your inbox lists both too, because you hold `grc_member`, and `ic_member:hyderabad` with yourself as the chosen member. Under the grievance, choose "Acknowledged (we have seen it)" in "Change the status to" and press Update. The page says "Updated: Acknowledged (we have seen it)." Your cases now shows the grievance as "Seen by the team".

The page asked the chat service who you are before it drew anything. Both reads named your email and acme, so it showed your cases. It sent your words to the chat service's `POST /v1/chat`, and the chat door answered before any brain ran. The reply carried `case_offer` naming `posh`, and the page opened the POSH card from that, never from your words. The page shows the reply as it came. The target dates, the clocks and the law come from the service too: the page holds none of that wording itself.

The two cases went through the chat service's case routes, as you, with your IAP assertion forwarded by the UI. When a call is refused, the page says so in a plain sentence of its own, chosen by the status. It never shows the service's words, which can repeat what was sent. The exceptions are the POSH card's 409 and 503: those words are written for the person, so the card shows them under the contacts. Step 7 calls the same routes directly, and `make cases` there shows these two cases still open.

### One fixed reply at every door

The gate, the mask and the reply in the kit's code, then the same words through rag-api and through the chat service.

#### Definition

`gate()` normalises the question (format characters dropped, lower case, one kind of apostrophe, one space). It returns `None` unless there is a first-person marker or a request for a person. Then it tries each class in order and returns the first that fires. One exception sits in front of the classes: a committee or HR member speaking about a complaint they received ("I am on the ICC...") skips `posh` and `grievance`, unless something says it happened to them. `_fires()` is the test for each class. `mask()` finds numbers with `shared/identifiers.py`, which keeps only those that pass Verhoeff (Aadhaar) or Luhn (cards). It replaces each with a token no longer than the number, so a masked question is never longer than one the handler accepted. `desk_law.py` holds the replies, and `template()` is the only way to one.

#### The code

#### Do it: the gate on your machine

No lane and no cost: the cell imports the kit's rules and runs them on the smoke's disclosure, a near miss, a plain question and two numbers.

Only the disclosure hits. The card number passes the Luhn check and is replaced. The Aadhaar-shaped number fails the Verhoeff check, so it is not an Aadhaar number, and it stays.

#### The doors

Both doors run in the same order. They read the question off the event loop. With no hit, nothing to mask and no model check to run, the body goes on untouched and nobody is verified. Otherwise the door verifies the caller and checks the roster with the service's own functions, then reads the switch. `off` sends the body on as it came. Otherwise a hit is answered. With `on`, a question the rules let through goes to the model check first, which can answer it the same way; rag-api's door runs that check only on `/v1/query` and `/v1/stream`, for a question a person sent (no `brain` label, or the Chat page's `ui`). Then any number is masked. rag-api's `main.py` hands its door the check and the list of companies it runs for, read once a minute, in the same install. rag-api's door answers each surface in its own shape: a `RAGResponse` on `/v1/query`, a token event and a done event on `/v1/stream`. The chat door answers in the shape of a chat turn. Each door caps the body at 64 KiB (65,536 bytes) before it parses anything. A question over 4,000 characters is left to the handler's own 422.

#### Do it: rag-api's door

The disclosure to `/v1/stream` and `/v1/query` as acme, with `tok`'s token for `documind-ui-sa`, the account `make smoke` calls as. The cell takes the words from the smoke's own file.

#### Do it: the chat door

The same words to the chat service as `evalacme`, asking for the `langchain` brain, which would send them to Gemini first. The cell also prints `case_offer`, the field the Desk page reads.

The stream sent one token event holding the whole reply, then a done event: model `none`, backend `desk_gate`, cost 0, no tokens, and `cache_hit` none. `/v1/query` returned the same reply with no citations, `answerable` false and confidence low. The chat door answered for the `langchain` brain without running it: brain `desk_gate`, model `none`, no tool call, no model call and Rs 0. Its `case_offer` names the class, `posh`, and holds none of the words. All three replies are the `posh` text. Each answered call logged one row, two from rag-api and one from the chat door, with the class "sensitive" and no user; step 8 reads them.

### Roles and cases, in the code

Who may raise a case, who may read it, and how one press becomes one case.

#### Definition

Roles. `shared/roles.py` keeps a person's roles in a document of their own, `tenants/{tenant}/roles/{email}`, beside the member document, so the next `make roster` cannot erase them. `roles_for()` is the one reader. A person on no roster has no role. A member with no document is `["employee"]`. A read that fails gives `"unread"`, which opens the case desk and nothing else, so a person can still reach a human while Firestore is unwell. `DESKS` says which desks each role opens. The queue roles open none, which is why `evalgrc` cannot raise a case.

Raising. Every case route starts the same way. `_who()` asks `agent.py`'s `caller()` who is asking, and the roster which tenant they belong to. The tenant and the person are never fields of the body. `create_case` then checks the case desk and reads the company's queues. Then it either opens a POSH case or writes a draft.

Offering. `GET /v1/cases/offer` starts with the same `_who()` and `_raiser()`, so only a person who may raise a case gets an answer. It reads the company's settings through `settings()`, the cache the doors read once a minute, and it reads no case. It returns the email and the tenant the service saw, the person's roles, both switches, the kinds of case whose queue is set up, and the POSH card once the POSH section is complete. The Desk page draws its sections from this answer.

The numbers. A draft can be sent for 30 minutes. A POSH press's token is claimed in `case_tokens` for 24 hours; a send's token stays on the case as its hash. A case due within 24 hours and still unacknowledged is "due". A queue's inbox lists up to 500 active cases and the latest 50 finished ones, and a person's own list holds their latest 50. An audit write claimed more than 2 minutes ago is taken over by the next call.

A new record. The id is `secrets.token_hex(16)`: 32 hex characters that say nothing about the person or the case, and cannot be guessed. A record can carry a SHA-256 of a question, never the question itself. A case raised from the button carries neither, and its summary holds only what the person writes.

Sending. One transaction reads the draft and opens it. The same token again returns the case as it is, and another token on an opened case is 409. A send after `expire_at` is 410. The code checks this itself; the TTL in `desk.tf` only deletes the draft some time later, and after that a send is 404. The due date and its basis come from `_due()`. For a grievance, the date follows section 4(6), under which the committee may complete its proceedings within thirty days, only when the company has said its committee takes a case raised here as the application. acme's queues file says it does not (`accepts_desk_case` false), so acme's grievances get a date 15 days on: the company's own target. The `case.open` event goes into `audit_pending` in the same transaction as the change, and `_flush()` writes it to the bucket after.

POSH. No text is accepted. At least one chosen member must hold the office's `ic_member` role, or nobody could read the case. Then it is 409, and the card's contacts are the way to reach them. Each press is claimed in `case_tokens`, under a hash of the tenant, the person and the token, inside the transaction that writes the case. A doubled press therefore returns the first case.

Reading. The person who raised a case reads it, and a draft is theirs alone. A POSH case is read only by a chosen member who holds the office's role. Any other queue is read by its roles from `desk_law.QUEUES`, and `people_ops` reads a grievance only when the person chose to share it. Anyone else gets 404, the same answer as for a case that does not exist.

The audit event. A sensitive case's target gives its type as "sensitive" and leaves out its queue. Every case event's actor is a case reference.

What Terraform adds. The TTL on a draft's `expire_at`, and one index for each query the queue makes. The overdue job reads the cases and writes only log lines, each with an id, a queue ("sensitive" for a sensitive case), a date and a state.

#### Do it: five of the queue's tests

No lane and no cost: five of `commands/tests/test_cases.py`'s tests, run against its fake Firestore and fake audit bucket. Who holds what; an expired draft is 410; nobody else can tell a case exists; a POSH case holds no text, and one press opens one; and the audit actor is a case reference.

Each test drives the kit's own `roles.py` and `cases.py`. A member with no document was an employee, a leaver reached the case desk only, and a failed read gave the case desk alone. A send 31 minutes after the draft was refused, and the draft stayed a draft with no event written. A grievance was read by its requester and by the committee, and by nobody else in either tenant. Two presses with one token made one POSH case, with no summary, no question hash and no route trace. Every event's actor was a case reference, and no event held an "@" or the office's name.

### The case routes, over REST

What an employee may raise; a grievance raised, confirmed twice, read by the committee, refused to everyone else and closed; then the smoke, and the operator's view.

#### Definition

The chat service serves seven case routes, and its docstring lists them:

`{id}` matches 32 hex characters only: an id of any other shape matches no route, and `/v1/cases/offer` is never taken for a case id. A route that returns a case does so through `cases.view()`. That leaves out the token's hash and the question's hash, and adds who has the case, the clock and the law. `GET /v1/cases` and the offer also name the email and the tenant the service saw: the Desk page checks those before it draws anything.

#### Do it: a case, end to end

The cell first asks what `evalacme` may raise. It raises a grievance as `evalacme` and sends it twice with one token. Then it tries a second token. `evalgrc` reads its inbox, then asks for the offer. `evalzeta` and the outsider ask for the case. The raiser tries to close it, and the committee acknowledges and closes it. It keeps the id in `~/lesson105_case.txt` for step 8.

The offer named acme, `desk_gate` rules, both POSH offices and all six kinds of case, because acme's queues file sets up every one. The draft went to `grc`, the Grievance Redressal Committee, with its basis and an expiry 30 minutes out. Both sends returned the same open case, opened once. It is due 15 days after it opened, and the reply says the date is the company's own target. A second token on the open case was 409. The committee's account found the case in its inbox, and the inbox named the account the service saw. Its offer was 403: `grc_member` alone raises no case, so it is offered none. zeta's account got 404: it cannot tell the case exists. The outsider, who is on no roster, got the roster's 403. The person who raised it may read it but not move it, so closing it was 403. The committee then acknowledged and closed it.

#### Do it: the live smoke

`smoke/smoke_cases.py` checks the whole queue in one run, as the eval accounts, with your email as the Internal Committee member its POSH press names. It closes and withdraws what it opens.

#### Do it: the operator's view

`make cases` lists a tenant's open cases, soonest due first, for you to chase. A sensitive case's type and queue both show as "sensitive", since a queue such as `ic:hyderabad` would give the type away, and no person is named. `make cases-overdue` runs the hourly job's scan once, as you.

The smoke's 11 checks passed: both doors, the draft, one case from two sends, the inbox, the two moves, another tenant's 404, the POSH press made once with no text, its withdrawal, and the outsider's 403. Its own cases are closed or withdrawn, so `make cases` shows only the two you raised on the Desk page: the POSH record, open, and the grievance you acknowledged. Neither is due within 24 hours, so the scan logged no case, only its count line.

### The records, the audit events and the log rows

The case in Firestore, today's events in the audit bucket, and the rows both doors wrote, read without any service.

#### Do it: the records

The case from step 7, the smoke's POSH record, and two role documents, read with the Firestore client.

#### Do it: the audit events

Today's case and role events in the audit bucket, the newest six, then the latest `case.open` and `role.grant` in full.

#### Do it: the log rows

Every `desk_gate` row since step 3, from both services.

The step 7 case holds the words the cell sent, and no `expire_at`: the send deleted it. Its `audit_pending` is empty, because each event was written and cleared, and the token is kept only as a hash. The smoke's POSH record has a unit and a chosen member, and its summary and question hash are both None. The role documents name who set them.

In the bucket, each case event is named by its action and an id. The `case.open` event's actor is a case reference, and its target gives the type as "sensitive". Role events are the operator's acts, so their actor is your email and their target the person's. The log has six rows: the Desk page's turn, the two from step 5's rag-api cell, the chat door's, and the smoke's two. Each says "sensitive" with no user, and none holds the words.

### Why it is shaped this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The class, never the words. `gate()` returns a class name, so no caller can log or echo what matched. The log row holds the class and the rules version. For the three sensitive classes, the row says "sensitive" and leaves out the person.

- Rules before identity. The gate needs no database and no identity, so a question that does not hit and holds no checked number costs one pass of the patterns, plus, at most once a minute in each server process, one read of the list of companies whose `desk_gate` is on (one attempt, at most 2 s); unless the model check may apply to it, the door verifies nobody: the handler does that, as before. A question with a checked number is verified first, so that only a member's question is masked. So is a question that may need the model check: rag-api's door verifies it when its body's company is on, and the chat door, which learns the company only by verifying, verifies every question with words and no hit while any company on the lane is on. A hit is answered only after the caller is verified and the roster checked. The doors render their own errors as FastAPI renders JSON, so a refused caller cannot tell from the reply whether the question hit.

- Two doors, one rule. rag-api's door covers every caller of its three question routes, including the MCP server and the A2A peer. The chat door exists because an agent brain shows the person's words to its own model before it searches.

- Rules unless an operator says off. A missing switch and a value the doors do not know are `rules`, and a failed read is never off (rag-api's door reads it as `rules`; the chat door keeps the last value it read), so the gate is never off by accident: only `make desk DESK_GATE=off` turns it off. The gate needs no queue, because its replies are fixed. The routed Desk does: lesson 10.4 cannot switch it on until every office has a member who can read its POSH cases, and while it is on, `make desk-queues` refuses a POSH section that would leave an office unreadable, and `make roles` warns when a revoke leaves one.

- A POSH record holds no words. It keeps who raised it, the office and the members chosen. What happened is for the person to tell them, and the committee can explain the time limits the Act sets.

- The page draws only what the service says is yours. Both of the Desk page's reads name the email and the company the service saw. A UI with no IAP in front of it calls as its own account, so the page shows one warning about the sign-in rather than that account's cases.

- 404 for everyone else. A case another tenant asks for, or one the reader may not read, is answered as if it did not exist.

- The event with the change. An audit event is written into the case record in the same transaction as the change it records, then flushed to the bucket. A failed write is retried by the next call that touches the case.

- The company's date is labelled as the company's. A queue's target date is shown with a line saying it is the company's own target, not a date set by law, beside what the law says, so nobody reads it as a legal deadline. No date an Act came into force is shown until a person has checked it against the Gazette.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The lexicon has not met people's words. Its examples and near misses were written by a model, and a fluent Hindi and Hinglish speaker has not reviewed them. `evals/routes.jsonl` holds no escalation rows yet, so recall on real disclosures is not measured.

- It reads words, not meaning. With `desk_gate` on `rules`, as on your lane, a disclosure in words the patterns lack goes to the documents and the model. `on` adds the model check for those, and its recall is not measured either. A sentence that only looks like one gets the fixed reply.

- The POSH Act is a scan. The corpus copy has no text layer, so the reply and the case name the Act and its committees, with no section and no line.

- No in-force dates. `IN_FORCE` holds no date until a person enters the Labour Codes' and the DPDP Act's dates from the Gazette, so no case says a law applies from a date.

- No holiday calendar. The exit-dues reading of "two working days" counts Monday to Friday.

- No delivery. A case is a record and an audit event. Nobody is emailed or paged when one opens: the people in its queue see it when they open their Desk inbox.

- The overdue alert reaches the lane, not the queue. An alert policy on the job's lines (`terraform/desk_alerts.tf`) tells your admins, by email or PagerDuty, which queue has a case due or breached, with a count. The line names no company and no person, so `make cases` finds the case, and nobody in the queue is told by the kit.

- An outside agent has already read the words. An agent that calls rag-api through the MCP server has shown the person's words to its own model first. rag-api's door sees only its search words.

- The routed Desk stays off. The kit also holds a router that picks one desk for each question; lesson 10.4 switches it on. With `desk_route` off, as on every tenant after this lesson, the chat door's shadow hook routes nothing and the Desk page shows its case half alone.

### Verify it yourself: the checklist

Fifteen checks, each one block above, each with the value that proves it on your lane.

Terraform added the Desk's TTL fields, indexes and accounts, and the hourly job with its schedule. rag-api, the UI and the chat service run the Desk's code, and the eval accounts may invoke the chat service. You may mint tokens as them, and three of them are on rosters. acme's `tenant_settings` holds its case queues, set by you, and no `desk_gate`: acme has the gate's rules, and no model check. Two role documents exist, yours and `evalgrc`'s. Your two cases from the Desk page are still open. The cell's grievance and the smoke's are closed, and the smoke's POSH record is withdrawn. Every one left events in the audit bucket. Your home folder has `~/queues.acme.json` and `~/lesson105_case.txt`. From now on, a question that hits the gate gets its fixed reply in every lesson, for acme, zeta and globex alike: no company has written `desk_gate`, so each has the rules. An Aadhaar or card number in their questions is masked before rag-api's handlers or a brain see it. Only acme has queues and roles, so only acme's people can raise a case that reaches someone. A turn the chat door answers runs no brain and keeps no conversation. Lesson 5.7 puts one question through all four brains and compares their costs and traces. Lesson 10.4 later sends each of acme's and zeta's other questions to one specialist desk, and every globex question to the law, and Module 6 picks up the conversations the brains and the Desk keep.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.6 Hand a question to the person the law names · v5.0

Next: Lesson 5.7 Compare the LangChain and ADK adapters.
