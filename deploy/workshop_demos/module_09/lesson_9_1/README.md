# Lesson 9.1: Trace and authorize gateway routes

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_hook_s_decisions_traced.py](demo_03_the_hook_s_decisions_traced.py) | The hook's decisions, traced |
| 4 | [demo_04_the_token_the_proxy_sends.py](demo_04_the_token_the_proxy_sends.py) | The token the proxy sends |
| 5 | [demo_05_the_gateway_deployed_and_smoke_tested.py](demo_05_the_gateway_deployed_and_smoke_tested.py) | The gateway, deployed and smoke-tested |
| 6 | [demo_06_a_pan_re_routed_and_the_cost_header.py](demo_06_a_pan_re_routed_and_the_cost_header.py) | A PAN re-routed, and the cost header |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The intended gateway backend services and IAM configuration.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_hook_s_decisions_traced.py

Do it

**`step_01_the_hook_s_decisions_traced(session)` — The hook's decisions, traced / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (once: a venv with the gateway image's Presidio and spaCy model).

Expected shape, not a promised result:

```text
en_core_web_lg installed: the image's model, 400 MB
```

**`step_02_the_hook_s_decisions_traced(session)` — The hook's decisions, traced / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the gateway's own classifier and hook; no network).

Expected shape, not a promised result:

```text
Presidio's recognizers: CreditCard, Crypto, Date, Email, Iban, Ip, MacAddress, MedicalLicense, Nhs, Phone, Spacy, Url, UsBank, UsItin, UsLicense, UsPassport, UsSsn
the classifier's own test cases, which nothing runs:
  'What is GDPR?'                  expected PUBLIC       got PUBLIC
  'Email me at user@acme.com'      expected CONFIDENTIAL got CONFIDENTIAL
  'My Aadhaar is 2345-6789-0123'   expected RESTRICTED   got PUBLIC
  'SSN 123-45-6789'                expected RESTRICTED   got PUBLIC
  'PAN ABCDE1234F'                 expected RESTRICTED   got PUBLIC
the hook, on four requests for documind-general:
  PUBLIC       -> documind-general   'What is the notice period for a confirmed E3?'
  PUBLIC       -> documind-general   'My PAN is ABCDE1234F. What is the notice period for a confirmed E3?'
  RESTRICTED   -> documind-sensitive 'My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?'
  CONFIDENTIAL -> documind-general   'Context:'
and what the last one sends to Gemini:
  Context:
  [Source 1] hr_policy_<URL>
  NP-03. A confirmed <US_DRIVER_LICENSE> serves a notice period of <DATE_TIME>. Queries go to <EMAIL_ADDRESS>.
  
  Question: What is the notice period for a confirmed <US_DRIVER_LICENSE>?
```

### demo_04_the_token_the_proxy_sends.py

Do it

**`step_01_the_token_the_proxy_sends(session)` — The token the proxy sends / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the token proxy's token, with the metadata server stood in; no network).

Expected shape, not a promised result:

```text
the SLM, first call       <token 1>   minted so far: 1
the SLM, a minute later   <token 1>   minted so far: 1
the SLM, 55 minutes in    <token 2>   minted so far: 2
the vLLM engine           <token 3>   minted so far: 3
the proxy drops these request headers, then adds its own Authorization: authorization, connection, content-length, host, transfer-encoding
```

### demo_05_the_gateway_deployed_and_smoke_tested.py

Do it

**`step_01_the_gateway_deployed_and_smoke_tested(session)` — The gateway, deployed and smoke-tested / Do it**

Do it

Operation: bash — run in the operator shell, in the kit where make up ran (it reads the database URL from Terraform's state).

Expected shape, not a promised result:

```text
...
>> gateway: https://documind-gateway-NUMBER.asia-south1.run.app (the API and the UI's account may call it)
```

**`step_02_the_gateway_deployed_and_smoke_tested(session)` — The gateway, deployed and smoke-tested / Do it**

Do it

Operation: bash — run in the operator shell, in the kit.

Expected shape, not a promised result:

```text
DocuMind gateway - live smoke test
  target: https://documind-gateway-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] no token is refused at the door  HTTP 403
  [PASS] liveliness as the member's account  HTTP 200 in ...s
  [PASS] documind-general answers JSON  '{"ok": true}' in ...s, model gemini-3.6-flash
  [PASS] the cost header rag-api prices from  x-litellm-response-cost=3.45e-05
  [PASS] a PAN is routed by the guardrail  served by 'gemini-3.6-flash' in ...s (the sensitive route is the self-hosted model, no fallback)
  [PASS] documind-slm answers, or its fallback does  model 'gemini-3.6-flash' in ...s, cost 1.8e-05
  --------------------------------------------------------
  6 passed, 0 failed
```

### demo_06_a_pan_re_routed_and_the_cost_header.py

Do it

**`step_01_a_pan_re_routed_and_the_cost_header(session)` — A PAN re-routed, and the cost header / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (three short answers through the gateway).

Expected shape, not a promised result:

```text
documind-general is priced at 1.50 and 7.50 USD a million tokens, in and out (config.yaml)
  no personal data  HTTP 200  answered by gemini-3.6-flash; 11 tokens in, 20 out; x-litellm-response-cost 0.0001665
  a bare PAN        HTTP 200  answered by gemini-3.6-flash; 16 tokens in, 20 out; x-litellm-response-cost 0.000174
  a PAN and a date  HTTP 500  no answer: the route the hook chose has no backend yet, and no fallback
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_9.1_Gateway_Routes_WIX.html`. All 24 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `30740fa186a22ed90c835763dc109fdeb2bf0409`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
