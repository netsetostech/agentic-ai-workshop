# Lesson 3.2 - From the bucket to the row

Module 3 - Ingest: chunks, embeddings and the Firestore ledger. The Where beat.

**What the learner does.** Draws the ingest lane box by box: the uploads bucket and its notification, the `documind-ingest` topic, the push subscription with its OIDC token and its twelve attempts, the dead-letter topic, the Cloud Run worker with its account and thirteen variables, the eight-step update path with every early exit, the seven writes in the code's order (Firestore staged, the swap, Vector Search, the managed mirror, BigQuery, the ledger, the audit event), the two jobs beside the push lane (batch at :15, reconcile at 23:30 IST), the reader's `current` pre-filter and newest-per-source guard, and the trail - every event name, the `gcloud logging read` filter that finds it, the metrics and policies in `alerts.tf`. Then inspects all of it live from Cloud Shell with the runbook.

**Code it opens.**
- `terraform/eventarc.tf`, `storage.tf`, `batch.tf`, `reconcile.tf`, `alerts.tf`, `firestore_indexes.tf`, `vector.tf`, `dataplex.tf`
- `commands/lesson-12.5.sh`
- `services/ingest/main.py` (the write block), `idempotency.py`, `batch.py`, `reconcile.py`, `managed.py` (the event names)
- `services/rag-api/retriever.py` (`prefer_current`, `newest_per_source`)
- `INDEXING.md` section 2, `evals/upload.sh`
- `make ingest-one / sources / vector-status / poison / dlq / queued / batch / batch-job / reconcile / reconcile-job / preflight`

**Files in this folder (the lesson package).**

```
Netsetos_GCP_Capstone_3.2_Bucket_To_Row_WIX.html   main lesson page (Wix-ready)
GCP_Capstone_3.2_Practice_Lab_WIX.html             hands-on lab, six exercises with solutions
GCP_Capstone_3.2_Live_Session_WIX.html             90-min live session plan
GCP_Capstone_3.2_Interview_QA_WIX.html             10 Q&A
GCP_Capstone_3.2_Bucket_To_Row_Runbook.md          Cloud Shell runbook (make-driven; no notebook for this lesson)
```
