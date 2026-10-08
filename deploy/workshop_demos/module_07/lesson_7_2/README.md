# Lesson 7.2: Compare Firestore and Spanner graph paths

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_seeders_run.py](demo_03_the_seeders_run.py) | The seeders, run |
| 4 | [demo_04_the_firestore_path_a_name_the_question_contains.py](demo_04_the_firestore_path_a_name_the_question_contains.py) | The Firestore path: a name the question contains |
| 5 | [demo_05_the_spanner_path_build_it_read_it_walk_it_by_meaning.py](demo_05_the_spanner_path_build_it_read_it_walk_it_by_meaning.py) | The Spanner path: build it, read it, walk it by meaning |
| 6 | [demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py](demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py) | The walk in front of the dense pool, on a candidate |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The Firestore graph from 7.1 and an explicitly configured Spanner graph for the alternative path.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py](recovery/demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py) — Notice what the first answer says, too. Dense retrieval found FIN-02 without any graph, because the handbook is small and the clause says "purchase". The Spanner walk made sure FIN-02 was in the pool whatever the dense ranking did. On a corpus where the answer's words are far from the question's, that is the difference. Set the threshold on the candidate alone, from your own numbers, and ask again. make candidate cannot pass it (step 7 says why), so this is a gcloud line:

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

### demo_03_the_seeders_run.py

Do it

**`step_01_the_seeders_run(session)` — The seeders, run / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the seeding rules, run; then the kit's tests; no model, no network).

Expected shape, not a promised result:

```text
eight names from the handbook's graph: Purchase approval, function head, CFO, Travel reimbursement, Notice period, probation, India, Remote work
Who signs off on a big purchase?
  candidate names ['who signs off on a big purchase?']
  seeds by containment: none   auto: vector
Which purchases need the CFO?
  candidate names ['which purchases need the cfo?']
  seeds by containment: CFO   auto: graph
What does the CFO approve?
  candidate names ['what does the cfo approve?']
  seeds by containment: CFO   auto: vector
Who approves a purchase above two lakh?
  candidate names ['who approves a purchase above two lakh?']
  seeds by containment: none   auto: vector
Who approves a Purchase above two lakh?
  candidate names ['purchase']
  seeds by containment: Purchase approval   auto: graph
Who handles Indian travel claims?
  candidate names ['indian']
  seeds by containment: India   auto: graph
........
----------------------------------------------------------------------
Ran 8 tests in 0.004s

OK
```

### demo_04_the_firestore_path_a_name_the_question_contains.py

Do it

**`step_01_the_firestore_path_a_name_the_question_con(session)` — The Firestore path: a name the question contains / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (two walks of the Firestore graph; reads only).

Expected shape, not a promised result:

```text
cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \
  SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \
  python graph.py --project documind-ai-YOUR-ID --tenant acme --backend firestore --ask "Who signs off on a big purchase?"
{
 "question": "Who signs off on a big purchase?",
 "backend": "firestore",
 "seeded_by": "containment",
 "seeds": [],
 "nodes": [],
 "chunk_ids": []
}
cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \
  SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \
  python graph.py --project documind-ai-YOUR-ID --tenant acme --backend firestore --ask "Which purchases need the CFO?"
{
 "question": "Which purchases need the CFO?",
 "backend": "firestore",
 "seeded_by": "containment",
 "seeds": [
  "CFO"
 ],
 "nodes": [
  "CFO",
  "Purchase approval"
 ],
 "chunk_ids": [
  "acme:497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173#9"
 ]
}
```

### demo_05_the_spanner_path_build_it_read_it_walk_it_by_meaning.py

Do it The CFO's edge came back two ways. As tables, GraphEdge is joined to GraphNode twice, for the names at both ends. As a graph, the kit's GQL walk goes from the CFO. Both reach Purchase approval and FIN-02. Now the kit's question, seeded by meaning. On Spanner, --ask prints the five nearest names, each with its distance and whether it passed 0.4. Then it walks from the names that passed.

**`step_01_the_spanner_path_build_it_read_it_walk_it(session)` — The Spanner path: build it, read it, walk it by meaning / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the same graph written to Spanner, then read back).

Expected shape, not a promised result:

```text
cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \
  SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \
  python graph.py --project documind-ai-YOUR-ID --tenant acme --backend spanner --source hr_policy_2026.md --rebuild
11 current text chunks for tenant 'acme' from 'hr_policy_2026.md'
{"event": "graph_extracted", "tenant": "acme", "chunks": 11, "extracted": 11, "fresh": 0}
{"event": "graph_built", "tenant": "acme", "backend": "spanner", "chunks": 11, "surface_forms": 28, "nodes": 25, "edges": 15}
tenant acme: 25 nodes (25 with a 768-number vector), 15 edges in Spanner
the edges that name the CFO, as tables (the names joined from GraphNode):
  CFO -[APPROVES_ABOVE_RS_2_00_000]-> Purchase approval   stated in FIN-02
one hop from CFO, by the kit's GQL walk: CFO, Purchase approval
  the chunks they cite: FIN-02
```

**`step_02_the_spanner_path_build_it_read_it_walk_it(session)` — The Spanner path: build it, read it, walk it by meaning / Do it**

The CFO's edge came back two ways. As tables, GraphEdge is joined to GraphNode twice, for the names at both ends. As a graph, the kit's GQL walk goes from the CFO. Both reach Purchase approval and FIN-02. Now the kit's question, seeded by meaning. On Spanner, --ask prints the five nearest names, each with its distance and whether it passed 0.4. Then it walks from the names that passed.

Operation: bash — run in the operator shell, in the kit (one walk of the Spanner graph, seeded by meaning; one embedding call).

Expected shape, not a promised result:

```text
cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \
  SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \
  python graph.py --project documind-ai-YOUR-ID --tenant acme --backend spanner --ask "Who signs off on a big purchase?"
{
 "question": "Who signs off on a big purchase?",
 "backend": "spanner",
 "seeded_by": "meaning",
 "seed_distance": 0.4,
 "nearest": [
  {
   "name": "Purchase approval",
   "kind": "policy",
   "distance": 0.183,
   "seeded": true
  },
  {
   "name": "CFO",
   "kind": "person",
   "distance": 0.415,
   "seeded": false
  },
  {
   "name": "approved cloud bucket",
   "kind": "system",
   "distance": 0.434,
   "seeded": false
  },
  {
   "name": "tax clearance",
   "kind": "policy",
   "distance": 0.434,
   "seeded": false
  },
  {
   "name": "Travel reimbursement",
   "kind": "policy",
   "distance": 0.459,
   "seeded": false
  }
 ],
 "seeds": [
  "Purchase approval"
 ],
 "nodes": [
  "Purchase approval",
  "function head",
  "CFO"
 ],
 "chunk_ids": [
  "acme:497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173#5",
  "acme:497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173#9"
 ]
}
```

### demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py

First with the walk from Firestore: First with the walk from Firestore: Then the same candidate, walking from Spanner: Choose a value just past the purchase or approval name, and below the first name that has nothing to do with purchases. The undo below removes it. Last, put the template back. Environment variables carry over from one revision to the next, so the candidate's settings would ride into the next gcloud run services update of the API. The undo writes RETRIEVAL_GRAPH=off and GRAPH_BACKEND=firestore, removes any GRAPH_SEED_DISTANCE, drops the tag, and deletes .candidate-revision.

**`step_01_the_walk_in_front_of_the_dense_pool_on_a_c(session)` — The walk in front of the dense pool, on a candidate / Do it**

First with the walk from Firestore:

Operation: bash — run in the operator shell, in the kit (a candidate with no traffic: the walk on, from Firestore; one question).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|...|RETRIEVAL_GRAPH=auto|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
/version: retrieval_graph=auto graph_backend=firestore embedding=text-embedding-005@1
Q: Who signs off on a big purchase?
A: Purchases up to Rs 2,00,000 are approved by the function head; above that, the CFO approves [1].
pool 20: the walk put 0 chunk(s) first; retrieval_backend vector
cites FIN-02 (hr_policy_2026.md): Purchases up to Rs 2,00,000 are approved by the function head.
the word CFO: not in the question, in the answer
```

**`step_02_the_walk_in_front_of_the_dense_pool_on_a_c(session)` — The walk in front of the dense pool, on a candidate / Do it**

First with the walk from Firestore: Then the same candidate, walking from Spanner:

Operation: bash — run in the operator shell, in the kit (the same candidate, the walk from Spanner; the same question).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|...|RETRIEVAL_GRAPH=auto|GRAPH_BACKEND=spanner|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
/version: retrieval_graph=auto graph_backend=spanner embedding=text-embedding-005@1
Q: Who signs off on a big purchase?
A: Purchases up to Rs 2,00,000 are approved by the function head; above that, the CFO approves [1].
pool 20: the walk put 2 chunk(s) first; retrieval_backend vector
cites FIN-02 (hr_policy_2026.md): Purchases up to Rs 2,00,000 are approved by the function head.
the word CFO: not in the question, in the answer
```

**`step_03_the_walk_in_front_of_the_dense_pool_on_a_c(session)` — The walk in front of the dense pool, on a candidate / Do it**

Choose a value just past the purchase or approval name, and below the first name that has nothing to do with purchases. The undo below removes it. Last, put the template back. Environment variables carry over from one revision to the next, so the candidate's settings would ride into the next gcloud run services update of the API. The undo writes RETRIEVAL_GRAPH=off and GRAPH_BACKEND=firestore, removes any GRAPH_SEED_DISTANCE, drops the tag, and deletes .candidate-revision.

Operation: bash — run in the operator shell, in the kit (the template put back, the tag dropped; the live revision was never touched).

Expected shape, not a promised result:

```text
100	documind-api-000NN-xxx
```

### recovery/demo_06_the_walk_in_front_of_the_dense_pool_on_a_candidate.py

Notice what the first answer says, too. Dense retrieval found FIN-02 without any graph, because the handbook is small and the clause says "purchase". The Spanner walk made sure FIN-02 was in the pool whatever the dense ranking did. On a corpus where the answer's words are far from the question's, that is the difference. Set the threshold on the candidate alone, from your own numbers, and ask again. make candidate cannot pass it (step 7 says why), so this is a gcloud line:

**`step_01_the_walk_in_front_of_the_dense_pool_on_a_c(session)` — The walk in front of the dense pool, on a candidate / Do it**

Notice what the first answer says, too. Dense retrieval found FIN-02 without any graph, because the handbook is small and the clause says "purchase". The Spanner walk made sure FIN-02 was in the pool whatever the dense ranking did. On a corpus where the answer's words are far from the question's, that is the difference. Set the threshold on the candidate alone, from your own numbers, and ask again. make candidate cannot pass it (step 7 says why), so this is a gcloud line:

Operation: bash — run only if step 5 seeded nothing (the threshold, on the candidate alone).

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_7.2_Graph_Paths_WIX.html`. All 27 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `1a20d1bb8fa54cb05200972a3aeeeb45d4c3e58d`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
