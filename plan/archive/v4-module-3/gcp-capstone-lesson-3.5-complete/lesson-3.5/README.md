# Lesson 3.5 - Ingest, re-issue, undo, poison

Module 3 - Ingest: chunks, embeddings and the Firestore ledger. The Do beat.

**What the learner does.** Runs the lifecycle on their own lane with the Makefile: one document in (`ingest_ok`), the corpus (31 objects, 1,065 Document AI pages, the ANN tier filling), a re-issue of the handbook (`reused=281 embedded=2 retired=283`, the answer moves, the scoped gate goes red), the undo (`ingest_reactivated`, nothing embedded, the fingerprint back), retire and restore (the tombstone against the same bytes and the nightly walk), poison and the DLQ (twelve attempts, about an hour), the batch lane (why the same bytes never queue, and how to see it), reconcile and drift, and the module's gate: `make smoke-reindex` green, with the rupees of every drill.

**Code it opens.**
- `Makefile` - `preflight`, `ingest-one`, `ingest-corpus`, `wait-vectors`, `vector-status`, `sources`, `reindex`, `retire`, `restore`, `poison`, `dlq`, `queued`, `batch`, `batch-job`, `reconcile`, `reconcile-job`, `drift`, `backfill-current`, `smoke-reindex`, `usage`, `off`, `down`
- `smoke/smoke_reindex.py`
- `evals/demo/README.md`, `evals/demo/*.md`, `evals/upload.sh`
- `INDEXING.md` sections 6 and 7
- `commands/lesson-12.5.sh`, `terraform/eventarc.tf`, `terraform/batch.tf`, `terraform/reconcile.tf`, `terraform/alerts.tf`

**Page format (eight steps).** 1 Before you start | 2 One document in | 3 The corpus | 4 A re-issue | 5 The undo | 6 Retire and restore | 7 Poison, the DLQ and the batch lane | 8 Reconcile and the gate - then five quizzes and three exercises.

**Files in this folder (the lesson package).**

```
Netsetos_GCP_Capstone_3.5_Ingest_Lab_WIX.html   main lesson page (Wix-ready)
GCP_Capstone_3.5_Practice_Lab_WIX.html          hands-on lab (six exercises, two of them Rs 0)
GCP_Capstone_3.5_Live_Session_WIX.html          90-min live session plan
GCP_Capstone_3.5_Interview_QA_WIX.html          10 Q&A
GCP_Capstone_3.5_Ingest_Lab_Runbook.md          Cloud Shell runbook (a make-driven lesson: no notebook)
```
