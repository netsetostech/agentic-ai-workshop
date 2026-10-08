# Lesson 3.4 - The ledger

Module 3 - Ingest. The second How beat: claim, swap, retire, undo.

**What the learner does.** Reads the ledger's code file by file, every window quoted verbatim from the kit: `claim()` as a transaction and the retake rule; `finish()`, `release()`, `take_batch()`; the generation guard (`stale_generation()`, `contracts.is_stale()`) and the download by generation; `current_chunks()` and the other lane's version; `swap_versions()`, `_retire()` and `retire_previous()`; `withdrawn()` and the verified undo in `reactivate()`; `record_source()` and the corpus fingerprint; `push()` with its HTTP codes and the batch hand-off; `index_document()` from the carry-over to the `ingest_ok` line; `batch.py` and `reconcile.py`. Ends on a worked trace of the smoke fixture - version 1, version 2, version 1 again - one table per collection.

**Code it opens.**
- `services/ingest/idempotency.py` (all 375 lines)
- `services/ingest/main.py` (`push()`, `index_document()`, `_enqueue_batch()`, `_run_batch_job()`)
- `services/ingest/contracts.py` (`is_stale()`)
- `services/ingest/batch.py`
- `services/ingest/reconcile.py`
- `terraform/firestore_indexes.tf` (the TTL policy), `batch.tf`, `reconcile.tf`
- `make sources / reindex / retire / restore / reconcile / batch / queued / purge / backfill-current / smoke-reindex`

**Page shape.** Hero, nine steps (reading order; the claim; the guard; current_chunks; the swap; the undo and the ledger row; push() and the HTTP codes; index_document(), batch.py and reconcile.py; the worked trace), five knowledge checks, three exercises.

**Files in this folder (the lesson package).**

```
Netsetos_GCP_Capstone_3.4_Ledger_WIX.html   main lesson page (Wix-ready)
GCP_Capstone_3.4_Practice_Lab_WIX.html      hands-on lab (six exercises; four are Rs 0)
GCP_Capstone_3.4_Live_Session_WIX.html      90-min live session plan
GCP_Capstone_3.4_Interview_QA_WIX.html      10 Q&A
GCP_Capstone_3.4_Ledger.ipynb               Colab notebook (source annotated, the claim race, reactivate's verdict, the live ledger)
```
