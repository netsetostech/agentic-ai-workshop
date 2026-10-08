# Lesson 4.6: Trace authenticated identity into tenant membership

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_door_and_the_verifier_who_may_knock_and_what_makes_a_token_count.py](demo_03_the_door_and_the_verifier_who_may_knock_and_what_makes_a_token_count.py) | The door and the verifier: who may knock, and what makes a token count |
| 4 | [demo_04_the_roster_one_document_per_member_two_ways_to_read_it_one_writer.py](demo_04_the_roster_one_document_per_member_two_ways_to_read_it_one_writer.py) | The roster: one document per member, two ways to read it, one writer |
| 5 | [demo_05_the_surfaces_who_calls_the_shared_verifier_and_who_still_keeps_a_copy.py](demo_05_the_surfaces_who_calls_the_shared_verifier_and_who_still_keeps_a_copy.py) | The surfaces: who calls the shared verifier, and who still keeps a copy |
| 6 | [demo_06_one_request_end_to_end_a_forged_header_and_the_row_that_ignores_it.py](demo_06_one_request_end_to_end_a_forged_header_and_the_row_that_ignores_it.py) | One request, end to end: a forged header, and the row that ignores it |
| 7 | [demo_07_the_person_s_leg_how_a_signed_in_person_reaches_the_api_through_the_ui.py](demo_07_the_person_s_leg_how_a_signed_in_person_reaches_the_api_through_the_ui.py) | The person's leg: how a signed-in person reaches the API through the UI |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

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

### demo_03_the_door_and_the_verifier_who_may_knock_and_what_makes_a_token_count.py

Do it: the API's audiences, and who may invoke it The cell mints two tokens for the API as documind-ui-sa: one the way tok does, and one without --include-email. It reads their claims without verifying them; the API does the verifying. Nothing is sent.

**`step_01_the_api_s_audiences_and_who_may_invoke_it(session)` — The door and the verifier: who may knock, and what makes a token count / Do it: the API's audiences, and who may invoke it**

Do it: the API's audiences, and who may invoke it

Operation: bash — run in the operator shell, in the kit (the API's two audiences and who may invoke it; reads only).

Expected shape, not a promised result:

```text
IAP_AUDIENCE  /projects/NUMBER/locations/asia-south1/services/documind-ui
              /projects/NUMBER/locations/asia-south1/services/documind-chat
SELF_URL      https://documind-api-NUMBER.asia-south1.run.app
run.invoker   serviceAccount:documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
              serviceAccount:documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
              serviceAccount:documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
              serviceAccount:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
```

**`step_02_what_your_token_says_about_itself(session)` — The door and the verifier: who may knock, and what makes a token count / Do it: what your token says about itself**

The cell mints two tokens for the API as documind-ui-sa: one the way tok does, and one without --include-email. It reads their claims without verifying them; the API does the verifying. Nothing is sent.

Operation: bash — run in the operator shell, in the kit (two tokens for the API, one with the email and one without; decoded, not sent).

Expected shape, not a promised result:

```text
TOKEN: aud https://documind-api-NUMBER.asia-south1.run.app
       email documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com, email_verified True, iss https://accounts.google.com, 59 minutes left
BARE: aud https://documind-api-NUMBER.asia-south1.run.app
       email (none), email_verified (none), iss https://accounts.google.com, 59 minutes left
```

### demo_04_the_roster_one_document_per_member_two_ways_to_read_it_one_writer.py

Do it: the three rosters, as Firestore holds them make roster runs this command without --dry-run. The dry run prints the memberships and the data-region policies it would set, and writes nothing.

**`step_01_the_three_rosters_as_firestore_holds_them(session)` — The roster: one document per member, two ways to read it, one writer / Do it: the three rosters, as Firestore holds them**

Do it: the three rosters, as Firestore holds them

Operation: bash — run in the operator shell, in the kit (the three rosters in Firestore; reads only).

Expected shape, not a promised result:

```text
acme    5 member(s)
    documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    you@example.com
zeta    3 member(s)
    documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
globex  3 member(s)
    documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
```

**`step_02_the_plan_make_roster_would_write_for_you(session)` — The roster: one document per member, two ways to read it, one writer / Do it: the plan make roster would write for you**

make roster runs this command without --dry-run. The dry run prints the memberships and the data-region policies it would set, and writes nothing.

Operation: bash — run in the operator shell, in the kit (make roster's plan; --dry-run writes nothing).

Expected shape, not a promised result:

```text
would put you@example.com on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would set acme: data_region=any
would set zeta: data_region=any
would set globex: data_region=in
```

### demo_05_the_surfaces_who_calls_the_shared_verifier_and_who_still_keeps_a_copy.py

Do it: which services call the shared verifier

**`step_01_which_services_call_the_shared_verifier(session)` — The surfaces: who calls the shared verifier, and who still keeps a copy / Do it: which services call the shared verifier**

Do it: which services call the shared verifier

Operation: bash — run in the operator shell, in the kit (which services call the shared verifier).

Expected shape, not a promised result:

```text
services/chat/agent.py
services/mcp/server.py
services/rag-api/auth.py
```

### demo_06_one_request_end_to_end_a_forged_header_and_the_row_that_ignores_it.py

Two questions to acme, one claiming to be the CEO, and the two usage rows they leave. The cell asks the same question twice with run_eval.py's own ask(), which sets an x-user-email header on every request. The first names the eval account; the second claims to be ceo@acme.example. Both carry your token and no assertion, so the bearer leg names the caller. After twenty seconds for the logs to land, the cell reads the two newest query rows for acme.

**`step_01_one_request_end_to_end_a_forged_header_and(session)` — One request, end to end: a forged header, and the row that ignores it / One request, end to end: a forged header, and the row that ignores it**

Two questions to acme, one claiming to be the CEO, and the two usage rows they leave. The cell asks the same question twice with run_eval.py's own ask(), which sets an x-user-email header on every request. The first names the eval account; the second claims to be ceo@acme.example. Both carry your token and no assertion, so the bearer leg names the caller. After twenty seconds for the logs to land, the cell reads the two newest query rows for acme.

Operation: bash — run in the operator shell, in the kit (two questions, one with a forged x-user-email; then their usage rows).

Expected shape, not a promised result:

```text
x-user-email eval@documind.in   HTTP 200, answerable True
x-user-email ceo@acme.example   HTTP 200, answerable True
YYYY-MM-DDTHH:MM:SS.ssssssZ	documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com	acme
YYYY-MM-DDTHH:MM:SS.ssssssZ	documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com	acme
```

### demo_07_the_person_s_leg_how_a_signed_in_person_reaches_the_api_through_the_ui.py

IAP in front of the UI, the assertion forwarded beside the UI's token, and every caller the API recorded in a day. A person never calls the API directly. They sign in at IAP in front of the UI, which admits only accounts granted the sign-in role. IAP hands the UI a signed assertion with every request. When the UI calls the API, it sends two credentials, as its _headers() shows in step 5: its own token, which gets past the door, and the person's assertion, forwarded unchanged. The API's verifier sees the assertion first and takes the person's email from it. The roster check and the usage row are then about the person, which is what lesson 3.8 saw in Chat. The cell counts every caller the API recorded in the last day.

**`step_01_the_person_s_leg_how_a_signed_in_person_re(session)` — The person's leg: how a signed-in person reaches the API through the UI / The person's leg: how a signed-in person reaches the API through the UI**

IAP in front of the UI, the assertion forwarded beside the UI's token, and every caller the API recorded in a day. A person never calls the API directly. They sign in at IAP in front of the UI, which admits only accounts granted the sign-in role. IAP hands the UI a signed assertion with every request. When the UI calls the API, it sends two credentials, as its _headers() shows in step 5: its own token, which gets past the door, and the person's assertion, forwarded unchanged. The API's verifier sees the assertion first and takes the person's email from it. The roster check and the usage row are then about the person, which is what lesson 3.8 saw in Chat. The cell counts every caller the API recorded in the last day.

Operation: bash — run in the operator shell, in the kit (every caller the API recorded in the last day).

Manual action: Sign in through the deployed UI as the lesson's rostered person and submit the example question. Type done before inspecting the person's assertion path.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
NN documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
      N you@example.com
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_4.6_Identity_Tenancy_WIX.html`. All 30 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `68df6795d0127a075315d621003ac5db51aa9805`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
