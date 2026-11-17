# Lesson 10.9: Run the peer on Google's managed agent platform

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_what_up_stages_and_what_the_runtime_will_import.py](demo_03_what_up_stages_and_what_the_runtime_will_import.py) | What up stages, and what the runtime will import |
| 4 | [demo_04_every_call_through_one_seam_the_dry_run.py](demo_04_every_call_through_one_seam_the_dry_run.py) | Every call through one seam: the dry run |
| 6 | [demo_06_deploy_and_ask_through_the_query_api.py](demo_06_deploy_and_ask_through_the_query_api.py) | Deploy, and ask through the query API |
| 7 | [demo_07_what_the_asks_left_spans_log_rows_and_sessions.py](demo_07_what_the_asks_left_spans_log_rows_and_sessions.py) | What the asks left: spans, log rows and sessions |
| 8 | [demo_08_the_proof_make_managed_peer_smoke_and_the_comparison.py](demo_08_the_proof_make_managed_peer_smoke_and_the_comparison.py) | The proof: make managed-peer-smoke, and the comparison |
| 10 | [demo_10_tear_it_down_and_verify_it_yourself.py](demo_10_tear_it_down_and_verify_it_yourself.py) | Tear it down, and verify it yourself |

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

### demo_03_what_up_stages_and_what_the_runtime_will_import.py

Do it: stage The image runs adk api_server, which imports the package and serves the root_agent it finds there. The cell makes the same import with ADK's own loader, in a venv holding the peer image's pins. It sets the location ADK's Dockerfile sets and the content setting ADK's deploy adds, and reads no .env, since the image ships none. It makes no call: the model and the tools are reached only when a question arrives.

**`step_01_stage(session)` — What up stages, and what the runtime will import / Do it: stage**

Do it: stage

Operation: bash — run in the operator shell, in the kit (what up deploys, written out; no call).

Expected shape, not a promised result:

```text
== stage: what make managed-peer-up deploys, written to /tmp/mp109 ==
  documind_peer/__init__.py       byte for byte commands/managed_peer_agent.py
  documind_peer/agent.py          byte for byte services/agent/agent.py
  documind_peer/chain.py          byte for byte services/agent/chain.py
  documind_peer/pins.py           byte for byte services/agent/pins.py
  documind_peer/requirements.txt  byte for byte services/agent/requirements.txt
  documind_peer/tool_pins.json    byte for byte services/agent/tool_pins.json
  deploy_config/.agent_engine_config.json  {"service_account": "documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "min_instances": 0, "max_instances": 1}
  deploy_config/.env                       {"MCP_URL": "https://documind-mcp-NUMBER.asia-south1.run.app", "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12"}
  the image: google-adk[a2a]==2.8.0 (the peer's pin); the deploy appends google-cloud-aiplatform[adk,agent_engines], unpinned (fact 11)
```

**`step_02_import_the_package_as_the_runtime_will(session)` — What up stages, and what the runtime will import / Do it: import the package as the runtime will**

The image runs adk api_server, which imports the package and serves the root_agent it finds there. The cell makes the same import with ADK's own loader, in a venv holding the peer image's pins. It sets the location ADK's Dockerfile sets and the content setting ADK's deploy adds, and reads no .env, since the image ships none. It makes no call: the model and the tools are reached only when a question arrives.

Operation: bash — run in the operator shell, in the kit (the staged package, imported as the runtime imports it; no Google call).

Expected shape, not a promised result:

```text
{"ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false", "ADK_MAX_LLM_CALLS": "12", "GOOGLE_CLOUD_LOCATION": "asia-south1", "agent": "documind_peer", "event": "managed_peer_up", "model": "gemini-3.6-flash", "model_location": "global", "versions": {"a2a-sdk": "1.1.2", "google-adk": "2.8.0", "google-auth": "2.57.1", "google-cloud-aiplatform": null, "google-genai": "2.22.0"}}
root_agent is agent.py's own agent: True | name: documind_peer
its model: GlobalGemini gemini-3.6-flash | its tools: ['McpToolset']
model calls a turn, at most: 12
```

### demo_04_every_call_through_one_seam_the_dry_run.py

Do it: up, printed Do it: one question, as each host is asked

**`step_01_up_printed(session)` — Every call through one seam: the dry run / Do it: up, printed**

Do it: up, printed

Operation: bash — run in the operator shell, in the kit (up, every call printed and none made).

Expected shape, not a promised result:

```text
DRY RUN: every call printed, none made (up, project documind-ai-YOUR-ID)
== up: the A2A peer on Agent Engine in asia-south1, as documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ==
  would call: GET https://asia-south1-aiplatform.googleapis.com/v1/projects/documind-ai-YOUR-ID/locations/asia-south1/reasoningEngines  # any documind-managed-peer*
  would call: vertexai.Client(project='documind-ai-YOUR-ID', location='asia-south1').agent_engines.create(config={'display_name': 'documind-managed-peer'})
  would call: GET https://cloudresourcemanager.googleapis.com/v1/projects/documind-ai-YOUR-ID  # its number
  would call: POST https://iam.googleapis.com/v1/projects/documind-ai-YOUR-ID/serviceAccounts/documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:getIamPolicy
  would call: POST https://iam.googleapis.com/v1/projects/documind-ai-YOUR-ID/serviceAccounts/documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:setIamPolicy  # adds roles/iam.serviceAccountTokenCreator for serviceAccount:service-NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com
  grant: roles/iam.serviceAccountTokenCreator on documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com for Agent Engine's service agent (down takes it back)
  stage: documind_peer/agent.py and requirements.txt (services/agent/, byte for byte) and documind_peer/__init__.py (commands/managed_peer_agent.py); beside them .agent_engine_config.json {"service_account": "documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "min_instances": 0, "max_instances": 1} and .env {"MCP_URL": "https://documind-mcp-NUMBER.asia-south1.run.app", "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12"}
  would call: google.adk.cli.cli_deploy.to_agent_engine(agent_folder='<staged>/documind_peer', project='documind-ai-YOUR-ID', region='asia-south1', agent_engine_id='projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID', display_name='documind-managed-peer', otel_to_cloud=True, env_file='<staged>/.env', agent_engine_config_file='<staged>/.agent_engine_config.json', adk_version='2.8.0')  # = adk deploy agent_engine, which ends in agent_engines.update(name=..., config=...)
  would call: GET https://asia-south1-aiplatform.googleapis.com/v1/projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID  # what the platform kept
  would call: POST https://cloudresourcemanager.googleapis.com/v1/projects/documind-ai-YOUR-ID:getIamPolicy  # who holds roles/aiplatform.user, roles/aiplatform.admin, roles/editor, roles/owner
  dry run: nothing deployed, nothing read back

STANDING COST: this instance exists until make managed-peer-down. Agent Engine's price is not stated here (fact 12, the author's dated read of the pricing page); min_instances 0 is asked for (fact 3), and whether an idle instance bills is fact 4. Torn down by default: make managed-peer-down when you are done.
WHO MAY CALL IT: every account holding roles/aiplatform.user (or owner, or editor) on the project, unless the instance has an IAM policy of its own (fact 8) - the policy was not read - and it answers each of them as documind-agent-sa, on acme's roster. The Cloud Run peer admits documind-ui-sa, documind-chat-sa (commands/lesson-8.4.sh).
Dry run: nothing was created or changed; 8 call(s) printed above.
```

**`step_02_one_question_as_each_host_is_asked(session)` — Every call through one seam: the dry run / Do it: one question, as each host is asked**

Do it: one question, as each host is asked

Operation: bash — run in the operator shell, in the kit (one question, as each host is asked; nothing sent).

Expected shape, not a promised result:

```text
DRY RUN: every call printed, none made (ask, project documind-ai-YOUR-ID)
== ask: the managed peer, as tenant acme's question ==
  would call: GET https://asia-south1-aiplatform.googleapis.com/v1/projects/documind-ai-YOUR-ID/locations/asia-south1/reasoningEngines  # any documind-managed-peer*
  would call: POST https://asia-south1-aiplatform.googleapis.com/v1/projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID:streamQuery?alt=sse {"class_method": "async_stream_query", "input": {"user_id": "documind-ui-sa", "message": "After how many years of continuous service does gratuity become payable?"}}  # as documind-ui-sa
  question: After how many years of continuous service does gratuity become payable?
  dry run: nothing was asked
Dry run: nothing was created or changed; 2 call(s) printed above.
DRY RUN: every call printed, none made (ask, project documind-ai-YOUR-ID)
== ask: the Cloud Run peer, as tenant acme's question ==
  would call: GET https://cloudresourcemanager.googleapis.com/v1/projects/documind-ai-YOUR-ID  # its number
  would call: POST https://documind-agent-NUMBER.asia-south1.run.app/ message/send {"parts": [{"kind": "text", "text": "After how many years of continuous service does gratuity become payable?"}]}  # make smoke-agent's request, with an ID token minted as documind-ui-sa
  question: After how many years of continuous service does gratuity become payable?
  dry run: nothing was asked
Dry run: nothing was created or changed; 2 call(s) printed above.
```

### demo_06_deploy_and_ask_through_the_query_api.py

Do it: deploy Do it: ask, three ways

**`step_01_deploy(session)` — Deploy, and ask through the query API / Do it: deploy**

Do it: deploy

Operation: bash — run in the operator shell, in the kit (the managed peer deployed: it bills until step 10).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/up.txt]
```

**`step_02_ask_three_ways(session)` — Deploy, and ask through the query API / Do it: ask, three ways**

Do it: ask, three ways

Operation: bash — run in the operator shell, in the kit (acme's question, through the query API).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ask_acme.txt]
```

**`step_03_ask_three_ways(session)` — Deploy, and ask through the query API / Do it: ask, three ways**

Do it: ask, three ways

Operation: bash — run in the operator shell, in the kit (the same question, naming zeta).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ask_zeta.txt]
```

**`step_04_ask_three_ways(session)` — Deploy, and ask through the query API / Do it: ask, three ways**

Do it: ask, three ways

Operation: bash — run in the operator shell, in the kit (the same question to the Cloud Run peer, over A2A).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ask_cloudrun.txt]
```

### demo_07_what_the_asks_left_spans_log_rows_and_sessions.py

Do it: trace Do it: sessions

**`step_01_trace(session)` — What the asks left: spans, log rows and sessions / Do it: trace**

Do it: trace

Operation: bash — run in the operator shell, in the kit (what the asks left: spans, rows, the runtime's line).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace.txt]
```

**`step_02_sessions(session)` — What the asks left: spans, log rows and sessions / Do it: sessions**

Do it: sessions

Operation: bash — run in the operator shell, in the kit (the managed sessions, and who may read one).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/sessions.txt]
```

### demo_08_the_proof_make_managed_peer_smoke_and_the_comparison.py

Do it: the smoke Do it: the table, from your records

**`step_01_the_smoke(session)` — The proof: make managed-peer-smoke, and the comparison / Do it: the smoke**

Do it: the smoke

Operation: bash — run in the operator shell, in the kit (the lesson's proof).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke.txt]
```

**`step_02_the_table_from_your_records(session)` — The proof: make managed-peer-smoke, and the comparison / Do it: the table, from your records**

Do it: the table, from your records

Operation: bash — run in the operator shell, in the kit (Cloud Run against Agent Engine, from your records).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/compare.txt]
```

### demo_10_tear_it_down_and_verify_it_yourself.py

Do it

**`step_01_tear_it_down_and_verify_it_yourself(session)` — Tear it down, and verify it yourself / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (torn down, then checked).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/down.txt]

[awaiting the author's run: data/down_again.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.9_Managed_Agents_WIX.html`. All 48 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b1e042febecc4ac43357ffb2c6605c2c20722e94`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
