# Lesson 10.7: Hand one question to the A2A peer, and stop loops and deadlocks

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_switch_the_hand_off_on_and_ask_the_adk_brain.py](demo_03_switch_the_hand_off_on_and_ask_the_adk_brain.py) | Switch the hand-off on, and ask the ADK brain |
| 4 | [demo_04_the_hand_off_in_the_kit_what_crosses_and_the_gate_in_front_of_it.py](demo_04_the_hand_off_in_the_kit_what_crosses_and_the_gate_in_front_of_it.py) | The hand-off in the kit: what crosses, and the gate in front of it |
| 5 | [demo_05_the_far_side_the_peer_stops_a_task_at_12_model_calls.py](demo_05_the_far_side_the_peer_stops_a_task_at_12_model_calls.py) | The far side: the peer stops a task at 12 model calls |
| 6 | [demo_06_the_hand_off_over_rest_the_response_the_smoke_and_the_confused_deputy.py](demo_06_the_hand_off_over_rest_the_response_the_smoke_and_the_confused_deputy.py) | The hand-off over REST: the response, the smoke, and the confused deputy |
| 7 | [demo_07_what_the_lane_logs_the_hand_off_line_beside_the_chat_row.py](demo_07_what_the_lane_logs_the_hand_off_line_beside_the_chat_row.py) | What the lane logs: the hand-off line beside the chat row |
| 8 | [demo_08_a_loop_among_the_lane_s_own_services_refused_by_construction.py](demo_08_a_loop_among_the_lane_s_own_services_refused_by_construction.py) | A loop among the lane's own services: refused by construction |
| 9 | [demo_09_a_loop_through_someone_else_s_agent_refused_at_run_time.py](demo_09_a_loop_through_someone_else_s_agent_refused_at_run_time.py) | A loop through someone else's agent: refused at run time |
| 10 | [demo_10_why_it_is_built_this_way_what_it_costs_and_what_the_kit_does_not_do_yet.py](demo_10_why_it_is_built_this_way_what_it_costs_and_what_the_kit_does_not_do_yet.py) | Why it is built this way, what it costs, and what the kit does not do yet |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/setup_before_you_run_anything_set_up_the_shell.py](recovery/setup_before_you_run_anything_set_up_the_shell.py) — Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The shell, in the kit's folder, with PROJECT, REGION, NUMBER and tok. The peer and the chat must run this lesson's kit: the peer's image with its cap, and the chat's with peer.py and a2a-sdk. If the peer's /health in step 5 names no max_llm_calls, or the chat was deployed before your last git pull, build and deploy them again with this cell. Otherwise skip it.

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

### recovery/setup_before_you_run_anything_set_up_the_shell.py

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The shell, in the kit's folder, with PROJECT, REGION, NUMBER and tok. The peer and the chat must run this lesson's kit: the peer's image with its cap, and the chat's with peer.py and a2a-sdk. If the peer's /health in step 5 names no max_llm_calls, or the chat was deployed before your last git pull, build and deploy them again with this cell. Otherwise skip it.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The shell, in the kit's folder, with PROJECT, REGION, NUMBER and tok. The peer and the chat must run this lesson's kit: the peer's image with its cap, and the chat's with peer.py and a2a-sdk. If the peer's /health in step 5 names no max_llm_calls, or the chat was deployed before your last git pull, build and deploy them again with this cell. Otherwise skip it.

Operation: bash — run in the operator shell, in the kit, only if your peer or chat predate this lesson's kit (each several minutes).

### demo_03_switch_the_hand_off_on_and_ask_the_adk_brain.py

Do it

**`step_01_switch_the_hand_off_on_and_ask_the_adk_bra(session)` — Switch the hand-off on, and ask the ADK brain / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the hand-off on: one env update on documind-chat, no model call).

Expected shape, not a promised result:

```text
>> documind-chat: PEER_URL=https://documind-agent-NUMBER.asia-south1.run.app
>> documind-chat: PEER_ACCOUNT=documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
   the ADK brain may hand a question to the peer; make smoke-handoff checks it, make handoff OFF=1 ends it
```

### demo_04_the_hand_off_in_the_kit_what_crosses_and_the_gate_in_front_of_it.py

No network and no model: the cell imports peer.py, asks its gate about four askers, then asks how long a hand-off may wait with 100 s, 30 s and half a second left in the turn.

**`step_01_the_gate_and_the_wait_on_the_kit_s_own_cod(session)` — The hand-off in the kit: what crosses, and the gate in front of it / Do it: the gate and the wait, on the kit's own code**

No network and no model: the cell imports peer.py, asks its gate about four askers, then asks how long a hand-off may wait with 100 s, 30 s and half a second left in the turn.

Operation: bash — run in the operator shell, in the kit (peer.py's gate and wait, on the kit's own code; no network).

Expected shape, not a promised result:

```text
HANDOFF_MAX_PER_TURN 2, PEER_TIMEOUT_S 75 s, the turn's deadline 100 s
an acme member: sent
an acme member, 2 already sent this turn: refused, this turn has already handed 2 questions to the peer, the most one turn may (HANDOFF_MAX_PER_TURN)
a zeta member: refused, the peer reads the corpus as an account that is not on this tenant's roster alone, so its answer could come from another tenant's documents; it was not asked (a confused deputy)
an acme member, the peer's account on 3 rosters: refused, the peer reads the corpus as an account that is not on this tenant's roster alone, so its answer could come from another tenant's documents; it was not asked (a confused deputy)
100 s left in the turn: the hand-off waits at most 75 s
30 s left in the turn: the hand-off waits at most 30 s
0.5 s left in the turn: the hand-off waits at most 1 s
```

### demo_05_the_far_side_the_peer_stops_a_task_at_12_model_calls.py

Do it: the cap, published Do it: trip the cap on your lane

**`step_01_the_cap_published(session)` — The far side: the peer stops a task at 12 model calls / Do it: the cap, published**

Do it: the cap, published

Operation: bash — run in the operator shell, in the kit (the peer's /health).

Expected shape, not a promised result:

```text
{"status":"ok","mcp_url":"https://documind-mcp-NUMBER.asia-south1.run.app","self_url":"https://documind-agent-NUMBER.asia-south1.run.app","model":"gemini-3.6-flash","max_llm_calls":12,"peer_chain":"off","tool_pins":"off","agent_fence":false,"kit_import":false}
```

**`step_02_trip_the_cap_on_your_lane(session)` — The far side: the peer stops a task at 12 model calls / Do it: trip the cap on your lane**

Do it: trip the cap on your lane

Operation: bash — run in the operator shell, in the kit (the cap tripped, then put back).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/agent_drill.txt]
```

### demo_06_the_hand_off_over_rest_the_response_the_smoke_and_the_confused_deputy.py

Do it: the smoke Do it: a confused deputy

**`step_01_the_smoke(session)` — The hand-off over REST: the response, the smoke, and the confused deputy / Do it: the smoke**

Do it: the smoke

Operation: bash — run in the operator shell, in the kit (the hand-off's smoke: two turns).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_handoff.txt]
```

**`step_02_a_confused_deputy(session)` — The hand-off over REST: the response, the smoke, and the confused deputy / Do it: a confused deputy**

Do it: a confused deputy

Operation: bash — run in the operator shell, in the kit (the confused deputy, refused before anything is sent).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/deputy.txt]
```

### demo_07_what_the_lane_logs_the_hand_off_line_beside_the_chat_row.py

Do it Then switch the hand-off off

**`step_01_what_the_lane_logs_the_hand_off_line_besid(session)` — What the lane logs: the hand-off line beside the chat row / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the hand-off lines and the chat rows since step 3).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/logs.txt]
```

**`step_02_then_switch_the_hand_off_off(session)` — What the lane logs: the hand-off line beside the chat row / Then switch the hand-off off**

Then switch the hand-off off

Operation: bash — run in the operator shell, in the kit (the hand-off off again).

Expected shape, not a promised result:

```text
>> documind-chat: the hand-off is off (PEER_URL and PEER_ACCOUNT removed); every brain answers alone
```

### demo_08_a_loop_among_the_lane_s_own_services_refused_by_construction.py

Do it This loop in lesson-12.8.sh binds who may invoke documind-chat. Add documind-agent-sa to it, as an edit meant to let the peer ask the chat something would, then run the check, then put the file back.

**`step_01_a_loop_among_the_lane_s_own_services_refus(session)` — A loop among the lane's own services: refused by construction / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the caller graph; offline, no gcloud).

Expected shape, not a promised result:

```text
python commands/check_callers.py --graph
each service, the account it runs as, and the script that deploys it and binds its invokers:
  documind-api    documind-api-sa       lesson-12.2.sh
  documind-chat   documind-chat-sa      lesson-12.8.sh
  documind-mcp    documind-mcp-sa       lesson-7.2.sh
  documind-agent  documind-agent-sa     lesson-8.4.sh
  documind-ui     documind-ui-sa        lesson-12.4.sh
  documind-gchat  documind-gchat-sa     gchat.sh

service -> service: the caller's account holds roles/run.invoker on the callee
  documind-chat -> documind-api
  documind-chat -> documind-agent
  documind-mcp -> documind-api
  documind-agent -> documind-mcp
  documind-ui -> documind-api
  documind-ui -> documind-chat
  documind-ui -> documind-mcp
  documind-ui -> documind-agent
  documind-gchat -> documind-chat

callers that run no service, so nothing calls them and they close no cycle: documind-evalacme-sa, documind-evalglobex-sa, documind-evalgrc-sa, documind-evalleaver-sa, documind-evalzeta-sa, documind-gchatpush-sa, documind-outsider-sa, gcp-sa-gsuiteaddons, gcp-sa-iap

acyclic: documind-ui, documind-gchat, documind-chat, documind-agent, documind-mcp, documind-api
  (each service may call only services after it, so no request can wait on itself)
```

**`step_02_change_it_an_edge_back_from_the_peer_to_th(session)` — A loop among the lane's own services: refused by construction / Change it: an edge back from the peer to the chat**

This loop in lesson-12.8.sh binds who may invoke documind-chat. Add documind-agent-sa to it, as an edit meant to let the peer ask the chat something would, then run the check, then put the file back.

Operation: bash — run in the operator shell, in the kit (Change-it: an edge back from the peer to the chat, then the kit put back).

IDE adaptation: Read the check's refusal as the cell's answer: with the peer's account added to lesson-12.8.sh the check names the cycle and exits 1, which stopped the demo before the put-back line and left lesson-12.8.sh edited (22 October 2026). The file is put back first; the step fails only if the check let the edge through.

Expected shape, not a promised result:

```text
-for who in documind-ui-sa documind-outsider-sa \
+for who in documind-ui-sa documind-agent-sa documind-outsider-sa \
each service, the account it runs as, and the script that deploys it and binds its invokers:
  documind-api    documind-api-sa       lesson-12.2.sh
  documind-chat   documind-chat-sa      lesson-12.8.sh
  documind-mcp    documind-mcp-sa       lesson-7.2.sh
  documind-agent  documind-agent-sa     lesson-8.4.sh
  documind-ui     documind-ui-sa        lesson-12.4.sh
  documind-gchat  documind-gchat-sa     gchat.sh

service -> service: the caller's account holds roles/run.invoker on the callee
  documind-chat -> documind-api
  documind-chat -> documind-agent
  documind-mcp -> documind-api
  documind-agent -> documind-chat
  documind-agent -> documind-mcp
  documind-ui -> documind-api
  documind-ui -> documind-chat
  documind-ui -> documind-mcp
  documind-ui -> documind-agent
  documind-gchat -> documind-chat

callers that run no service, so nothing calls them and they close no cycle: documind-evalacme-sa, documind-evalglobex-sa, documind-evalgrc-sa, documind-evalleaver-sa, documind-evalzeta-sa, documind-gchatpush-sa, documind-outsider-sa, gcp-sa-gsuiteaddons, gcp-sa-iap

cycle: documind-chat -> documind-agent -> documind-chat
  (documind-agent-sa may invoke documind-chat: a request can come back to a service that is waiting on it)
exit 1
acyclic: documind-ui, documind-gchat, documind-chat, documind-agent, documind-mcp, documind-api
  (each service may call only services after it, so no request can wait on itself)
```

### demo_09_a_loop_through_someone_else_s_agent_refused_at_run_time.py

The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

**`step_01_switch_it_on_then_send_two_chained_tasks(session)` — A loop through someone else's agent: refused at run time / Do it: switch it on, then send two chained tasks**

The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

Operation: bash — run in the operator shell, in the kit (the peer deployed with PEER_CHAIN=on; no model call).

**`step_02_switch_it_on_then_send_two_chained_tasks(session)` — A loop through someone else's agent: refused at run time / Do it: switch it on, then send two chained tasks**

The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

Operation: bash — run in the operator shell, in the kit (two chained tasks for the peer, each refused before a model call).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/chain_reject.txt]
```

### demo_10_why_it_is_built_this_way_what_it_costs_and_what_the_kit_does_not_do_yet.py

Every guard above sits on the lane. One more loop needs neither a hand-off nor a second service: two agents that may each hand the turn to the other, where neither owns the answer. In ADK it is one setting away. An agent under a parent is offered transfer_to_agent, whose agent_name is an enum of the agents it may reach: its parent, and its peers unless disallow_transfer_to_peers is set. commands/agent_shapes.py builds two such desks under a root, scripts each to want the other desk to answer, and puts one plugin on the run, TransferCap. It counts the agents a turn starts in a temp: key, which ADK keeps for one turn and never stores, and once 3 transfers have been made it answers in place of the next agent, before that agent's model is called. Run it offline, at Rs 0. It runs the same turn twice, with the peer edges and without them:

**`step_01_a_ping_pong_and_the_cap_that_ends_it(session)` — Why it is built this way, what it costs, and what the kit does not do yet / A ping-pong, and the cap that ends it**

Every guard above sits on the lane. One more loop needs neither a hand-off nor a second service: two agents that may each hand the turn to the other, where neither owns the answer. In ADK it is one setting away. An agent under a parent is offered transfer_to_agent, whose agent_name is an enum of the agents it may reach: its parent, and its peers unless disallow_transfer_to_peers is set. commands/agent_shapes.py builds two such desks under a root, scripts each to want the other desk to answer, and puts one plugin on the run, TransferCap. It counts the agents a turn starts in a temp: key, which ADK keeps for one turn and never stores, and once 3 transfers have been made it answers in place of the next agent, before that agent's model is called. Run it offline, at Rs 0. It runs the same turn twice, with the peer edges and without them:

Operation: bash — run in the operator shell, in the kit (two ADK desks in a ping-pong, and the cap that ends it; offline, Rs 0; the first run builds ~/graph-venv).

Expected shape, not a promised result:

```text
swarm_adk, offline: scripted models, no credential, Rs 0. TransferCap ends a turn after 3 transfers.
Q: What notice period does a confirmed E3 employee at ACME serve?

== transfers between the desks allowed (ADK's default)
who each agent may transfer to (transfer_to_agent's enum, as its model was offered it):
  desk_root      handbook_desk, statute_desk
  handbook_desk  desk_root, statute_desk
  statute_desk   desk_root, handbook_desk
transfer 1: desk_root -> handbook_desk
transfer 2: handbook_desk -> statute_desk
transfer 3: statute_desk -> handbook_desk
transfer 4: handbook_desk -> statute_desk   refused: TransferCap answered before statute_desk ran
answer, written by TransferCap, in statute_desk's place: Stopped after 3 transfers in one turn.
model calls: 4 | transfers made: 3 | session state stored after the turn: {}

== disallow_transfer_to_peers=True on both desks
who each agent may transfer to (transfer_to_agent's enum, as its model was offered it):
  desk_root      handbook_desk, statute_desk
  handbook_desk  desk_root
  statute_desk   desk_root
transfer 1: desk_root -> handbook_desk
transfer 2: handbook_desk -> desk_root
transfer 3: desk_root -> statute_desk
transfer 4: statute_desk -> desk_root   refused: TransferCap answered before desk_root ran
answer, written by TransferCap, in desk_root's place: Stopped after 3 transfers in one turn.
model calls: 4 | transfers made: 3 | session state stored after the turn: {}

With the peer edges gone the loop ran through the root; the cap ended it both times.
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.7_A2A_Handoff_WIX.html`. All 53 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `687e6663142d3602ab105d211e0fa11b3981a1f8`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
