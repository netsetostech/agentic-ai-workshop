# Lesson 3.3 - From bytes to rows

Module 3 - Ingest. The first How beat: the code, file by file, from the Pub/Sub record to the staged rows.

**What the learner does.** Reads six files in the order a document meets them - the message contract, Document AI chosen by residency and the free page count, the shared PII scan, the chunker the worker and the notebooks share, the embedding call with its carry-over, the datapoint and the three mirrors - and follows one clause of the ACME handbook (NP-03) through every function with the values the kit produces: 283 chunks in both revisions, 281 reused, 2 embedded. The ledger functions that decide which version is current are lesson 3.4's.

**Code it opens.**
- `services/ingest/contracts.py`
- `services/ingest/parser.py`
- `shared/pii.py`
- `shared/documind_corpus.py (windows, chunk_hash, chunk_document)`
- `services/ingest/main.py (_pdf_pages, _parse, _windows, _chunk, the DLP block)`
- `services/ingest/indexer.py`
- `shared/sparse_encoder.py`
- `terraform/docai.tf`

**Files in this folder (the lesson package).**

```
Netsetos_GCP_Capstone_3.3_Bytes_To_Rows_WIX.html   main lesson page (Wix-ready)
GCP_Capstone_3.3_Practice_Lab_WIX.html             hands-on lab (five Rs 0 exercises, one live)
GCP_Capstone_3.3_Live_Session_WIX.html             90-min live session plan
GCP_Capstone_3.3_Interview_QA_WIX.html             10 Q&A
GCP_Capstone_3.3_Bytes_To_Rows.ipynb               Colab notebook (Rs 0 until the last cell)
```

`Netsetos_GCP_Capstone_3.3_Ingesting_WIX.html` is the v3 page this lesson replaces; it stays in the folder until the v4 set is on Wix.
