# Lesson 3.5 - Ingest, re-issue, undo, poison: the Cloud Shell runbook

The eight drills of lesson 3.5 as copy-paste blocks, each with the line to expect, what it means, and what to do
when it does not appear. Every target below exists in `code/Makefile` (grep it); hashes and generations in the
expected output are illustrative, the counts are not.

**Needs.** A lane from Module 2 (`make up` done, `make smoke` green); the kit checked out (`code/` - a clone of the
learner repo names the same folder `deploy/`); Cloud Shell or any shell with `gcloud`, `make`, `python`,
`google-cloud-firestore` and `google-cloud-storage` (the shell that ran `make up` has them); these exports:

```bash
export PROJECT=documind-ai-YOUR-ID
export TENANT=acme
export REGION=us-central1
cd code
```

**Costs.** Under Rs 1,200 for the whole runbook on the Makefile's default `RESIDENCY=us` (the Layout Parser at $10
per 1,000 pages), under Rs 200 with `RESIDENCY=india` (Enterprise OCR at $1.50 per 1,000 pages); `USD_INR = 85`.
The corpus load in block 4 is about Rs 915 / Rs 145 of that and the optional batch drill in block 9 about
Rs 200 / Rs 30; everything else is paise. Rates read off the pricing pages on 21 September 2026 - re-verify. The
lane's own hourly floor (the Vector Search endpoint) is Module 2's number and runs regardless.

**Time.** About 90 minutes of attention, plus one hour of waiting for the poison message to reach the DLQ (start
block 8 early, read it at the end).

---

## 1. Preflight

```bash
make preflight PROJECT=$PROJECT TFSTATE_BUCKET=$PROJECT-tfstate
```

```text
  ok    gcloud on PATH
  ...
  ok    google-cloud-firestore for make roster

preflight clean - next: make plan, then make up
```

Read-only (`smoke/preflight.sh`), one line per check. On a lane that is already up it still prints them; the one
that matters now is the last `ok`, because `make sources`, `retire`, `restore`, `reconcile` and `queued` run
`reconcile.py` / `batch.py` in this shell. A `MISS` line carries the command that fixes it.

## 2. The worker's log

```bash
W='resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest"'
gcloud logging read "$W" --project $PROJECT --freshness=1h --limit 20 \
  --format='value(timestamp,jsonPayload.event,jsonPayload.tenant,jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded,jsonPayload.retired)'
```

```text
2026-09-21T09:58:11Z  ingest_ok  acme  6  0  6  0
```

One JSON line per event, `event` first. Keep `W` exported for every block below. If the read is empty, the lane
has not ingested anything in the last hour, which is fine before block 3. A second tab with
`gcloud beta run services logs tail documind-ingest --region $REGION --project $PROJECT` shows lines as they are
written.

## 3. One document in

```bash
make ingest-one FILE=evals/demo/gratuity_amendment_2026.md TENANT=acme PROJECT=$PROJECT
gcloud logging read "$W AND jsonPayload.event=\"ingest_ok\" AND jsonPayload.tenant=\"$TENANT\"" \
  --project $PROJECT --freshness=10m --limit 1 --format='value(jsonPayload)'
make sources TENANT_ONLY=acme PROJECT=$PROJECT
```

```text
>> gs://documind-ai-YOUR-ID-uploads/acme/gratuity_amendment_2026.md - waiting for the worker (up to 5 min)
>> indexed: acme_5b1c9e...   3   1
{'event': 'ingest_ok', 'tenant': 'acme', 'lane': 'push', 'doc_key': 'acme_5b1c9e...', 'chunks': 3, 'pages': 1,
 'kinds': ['text'], 'reused': 0, 'embedded': 3, 'retired': 0, 'generation': '1758450012345678',
 'effective_from': '2026-10-01', 'fingerprint': '9c1e8f2a4b7d3e10'}
source                                       status            gen chunks reused embed retired effective  embedding              indexed_at
acme/gratuity_amendment_2026.md              indexed 1758450012345678      3      0     3       0 2026-10-01 text-embedding-005@1   2026-09-21T10:15:02
{"ledger": "acme", "fingerprint": "9c1e8f2a4b7d3e10", "versions": 1, "last_event": "ingest_ok"}
```

Three chunks (the preamble and two sections), one page, all three embedded because a first version has nothing
to carry over, the date read off the document's own `effective_from:` line. Use the amendment, not
`smoke_note_v1.md`: the smoke fixture must stay un-ingested until block 11, because a version is `tenant_sha256`
whatever the object is called, and `make smoke-reindex`'s first check cannot see a duplicate. Cost: 563
characters embedded, under a paisa.

*If `no ingest_ok in 5 min`:* read `gcloud logging read "$W AND jsonPayload.event=\"ingest_failed\"" --freshness=10m`
(the `error` field), then `make dlq`, then `gcloud pubsub subscriptions describe documind-ingest-push` (the push
endpoint must be the worker's URL, the OIDC account `documind-ingest-sa`).

## 4. The corpus

```bash
make ingest-corpus PROJECT=$PROJECT
# about ten minutes; the CGST Act (236 pages, sixteen Document AI slices) is usually last
gcloud logging read "$W AND jsonPayload.event=\"ingest_ok\"" --project $PROJECT --freshness=30m --limit 50 \
  --format='value(jsonPayload.tenant,jsonPayload.pages,jsonPayload.chunks,jsonPayload.embedded,jsonPayload.kinds)'
gcloud logging read "$W AND jsonPayload.event=\"ingest_ok\"" --project $PROJECT --freshness=30m --limit 50 --format='value(jsonPayload.doc_key)' | wc -l
make wait-vectors WANT=200 PROJECT=$PROJECT
make vector-status PROJECT=$PROJECT
make sources TENANT_ONLY=acme PROJECT=$PROJECT | tail -1
```

```text
==> acme (21 files) -> gs://documind-ai-YOUR-ID-uploads/acme/
==> globex (3 files) -> gs://documind-ai-YOUR-ID-uploads/globex/
==> zeta (7 files) -> gs://documind-ai-YOUR-ID-uploads/zeta/
acme    1     283   283   ['text']        <- hr_policy_2026.md
acme    236   390   390   ['text']        <- cgst_act_2017.pdf (Document AI's count: near 390, not exactly)
acme    1     1     1     ['figure']      <- a PNG: one caption
31
>> waiting for >= 200 datapoints in documind-chunks
>> 2790 datapoints
displayName: documind-chunks
indexStats:
  vectorsCount: '2790'
{"ledger": "acme", "fingerprint": "e07b3c19d2a48f65", "versions": 22, "last_event": "ingest_ok"}
```

31 objects (a `.md` whose `.pdf` twin exists stays home), 31 `ingest_ok` lines, every one `reused=0`. The handbook
is 283 chunks - the module's number. `versions: 22` is acme's 21 objects plus block 3. Cost: 1,065 Document AI
pages (685 acme, 325 zeta, 55 globex) = Rs 905 on the Layout Parser or Rs 136 on OCR; 3.47 million characters of
embeddings = Rs 7.4; DLP inside the free gigabyte.

*If `make wait-vectors` times out:* it prints the three causes - the worker never upserted (check
`VECTOR_INDEX_NAME` on the service and the `ingest_ok` lines), the corpus never landed, or run
`make backfill-vectors APPLY=1` to fill the tier from the rows Firestore holds.

## 5. The re-issue

```bash
make reindex FILE=evals/demo/hr_policy_2026_v2.md NAME=hr_policy_2026.md TENANT=acme PROJECT=$PROJECT
NUMBER=$(gcloud projects describe $PROJECT --format='value(projectNumber)'); API=https://documind-api-$NUMBER.$REGION.run.app
TOKEN=$(gcloud auth print-identity-token --include-email --impersonate-service-account=documind-ui-sa@$PROJECT.iam.gserviceaccount.com --audiences=$API)
ask() { curl -s -X POST $API/v1/query -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"query\":\"$1\",\"tenant_id\":\"acme\",\"user_id\":\"u_lab\",\"top_k\":5,\"stream\":false}" | python -c "import json,sys; print(json.load(sys.stdin).get('answer'))"; }
ask "What is the notice period for a confirmed E3?"
make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md
```

```text
>> event doc_key chunks reused embedded retired effective_from
>> ingest_ok   acme_a1f3c8...   283   281   2   283   2026-10-01
>> retired (doc_keys, chunks, expire days): acme_497809ff...   283   30
A confirmed employee at grade E3 or above serves a notice period of 90 days, effective from 2026-10-01 [Source 1].
== eval gate: LIVE ==
  [FAIL] must_contain_rate ...      <- lk-06 wants 60; vr-01 is in required.json and blocks on its own
```

The offline gate ran first and was green (the corpus and the golden rows still say 60). Two chunks embedded (the
preamble gained two lines, NP-03 moved from 60 to 90), 281 reused by `chunk_hash`, the old 283 rows flagged with a
30-day `expire_at`. The red live gate is the demo: in a real release `lk-06` and `vr-01` move to 90 in the same
commit as the document. The `ledger_fingerprint` line changed, so every cache is stale. Cost: about 370 characters
embedded, under a paisa.

*If it stops at "the golden set is not sound":* someone edited `evals/golden.jsonl` or `evals/corpus/` on this
checkout; `python evals/run_eval.py` names the check. A reindex is a release; do not bypass it.

## 6. The undo

```bash
make reindex FILE=evals/corpus/acme/hr_policy_2026.md TENANT=acme PROJECT=$PROJECT
make sources TENANT_ONLY=acme PROJECT=$PROJECT | tail -1
ask "What is the notice period for a confirmed E3?"
make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md
```

```text
>> ingest_reactivated   acme_497809ff...   283   283   0   283
{"ledger": "acme", "fingerprint": "e07b3c19d2a48f65", "versions": 22, "last_event": "ingest_reactivated"}
A confirmed employee at grade E3 or above serves a notice period of 60 days [Source 1].
  [PASS] must_contain_rate ...
```

`embedded=0`: the rows kept their vectors, `reactivate()` counted them (283 of 283, minutes old) and flipped the
flag; revision 2 is retired in its turn. The fingerprint is block 4's value again, because it hashes the set of
current doc_keys and the same set is current. Cost: nothing. After 30 days the same upload would print
`reactivate_incomplete` (rows, chunks, age_days, retention_days, reason) and go through as a fresh version.

## 7. Retire and restore

```bash
make retire SOURCE=acme/gratuity_amendment_2026.md PROJECT=$PROJECT
gcloud storage cp evals/demo/gratuity_amendment_2026.md gs://$PROJECT-uploads/acme/ --project $PROJECT
sleep 30; gcloud logging read "$W AND jsonPayload.event=\"ingest_withdrawn\"" --project $PROJECT --freshness=5m --limit 1 --format='value(jsonPayload)'
make reconcile TENANT_ONLY=acme PROJECT=$PROJECT
make restore SOURCE=acme/gratuity_amendment_2026.md PROJECT=$PROJECT
sleep 30; gcloud logging read "$W AND jsonPayload.event=\"ingest_reactivated\" AND jsonPayload.tenant=\"acme\"" \
  --project $PROJECT --freshness=5m --limit 1 --format='value(jsonPayload.chunks,jsonPayload.embedded,jsonPayload.retired)'
```

```text
{"event": "reconcile_withdrawn", "gcs_uri": "gs://.../acme/gratuity_amendment_2026.md", "fingerprint": "5d02ab7e...", "retired_chunks": 3, ...}
{'event': 'ingest_withdrawn', 'tenant': 'acme', 'doc_key': 'acme_5b1c9e...', ..., 'hint': 'make restore SOURCE= clears the tombstone'}
{"reconcile": "withdrawn", "name": "acme/gratuity_amendment_2026.md", "why": "withdrawn, object kept (generation ... -> ...: make restore re-ingests what the object holds now)"}
{"event": "reconcile_done", "applied": false, "retire": 0, "reingest": 0, "backfill": 0, "touch": 0, "ok": 21, "withdrawn": 1, "queued": 0, "drift": 0}
{"event": "reconcile_restored", "gcs_uri": "...", "generation": "...", "next": "ingest_reactivated inside the undo window, ingest_ok (a fresh version) after it"}
3   0   0
```

The ledger row says `withdrawn` (not `retired`: that word means the object left the bucket); the same bytes are
acked with a hint and nothing moves; the plan reports it and counts it apart from drift; `make restore` sets the
row to `retired`, rewrites the object onto itself, and the worker's ordinary undo brings the three rows back.
`make ingest-one` is the wrong tool for the re-upload - it waits only for `ingest_ok`. Cost: nothing.

*If `make restore` prints `reconcile_restore_refused`:* the source is not withdrawn (an indexed one is already
live; a retired one comes back when its object does) or the object is gone (upload the bytes again).

## 8. Poison (start this early; read the DLQ an hour later)

```bash
make poison PROJECT=$PROJECT
# ... about an hour later:
make dlq PROJECT=$PROJECT
gcloud pubsub subscriptions pull ingest-dlq-sub --project $PROJECT --auto-ack --limit=10
gcloud storage rm gs://$PROJECT-uploads/acme/poison-*.pdf --project $PROJECT
```

```text
>> zero-byte object in: poison-1758453600.pdf
>> the worker refused it (400): 1 validation error for IngestMessage
size
  Input should be greater than or equal to 1 [type=greater_than_equal, input_value='0', input_type=str]
>> Pub/Sub retries a non-2xx five times with backoff, then ingest-dlq: make dlq in a few minutes
MESSAGE_ID         OBJECT_ID                     EVENT_TIME                EVENT_TYPE  DELIVERY_ATTEMPT
12345678901234567  acme/poison-1758453600.pdf    2026-09-21T11:00:03.412Z              1
```

`IngestMessage` requires `size >= 1`, so the worker fails at the edge, before any download, and answers 400 -
the message would fail identically every time. The target's last line is stale: `eventarc.tf` sets
`max_delivery_attempts = 12` with backoff from 10 s to 600 s, so the DLQ row appears after about an hour, not a
few minutes. `make dlq` peeks without acking; the second command drains. The third removes the object - block 10
shows what it does to the nightly walk if you leave it. Cost: nothing.

*If `make dlq` is still empty after ninety minutes:* `gcloud pubsub subscriptions describe documind-ingest-push`
must show the dead-letter policy, and the Pub/Sub service agent must hold `pubsub.publisher` on the DLQ topic and
`pubsub.subscriber` on the push subscription (both in `eventarc.tf`).

## 9. The batch lane (optional, about Rs 200 on the default lane)

The corpus has no file over `MAX_INLINE_PAGES` (250; the CGST Act is 236), and the Act's own bytes are already an
indexed claim, so the same bytes again are `ingest_duplicate` before the page count is reached. The lane needs a
lower ceiling and a new version of a big document.

```bash
make batch-job PROJECT=$PROJECT
sed -i 's/^MAX_INLINE_PAGES = 250$/MAX_INLINE_PAGES = 100/' services/ingest/main.py
make build SERVICES=ingest PROJECT=$PROJECT
make deploy-services SERVICES=ingest SCRIPTS=commands/lesson-12.5.sh BATCH_JOB=true PROJECT=$PROJECT
cp evals/corpus/acme/cgst_act_2017.pdf /tmp/cgst_v2.pdf
printf '\n%% batch-lane drill: a new version of the same document\n' >> /tmp/cgst_v2.pdf
gcloud storage cp /tmp/cgst_v2.pdf gs://$PROJECT-uploads/acme/cgst_act_2017.pdf --project $PROJECT
sleep 30; gcloud logging read "$W AND jsonPayload.event=\"ingest_queued_batch\"" --project $PROJECT --freshness=5m --limit 1 --format='value(jsonPayload)'
make queued PROJECT=$PROJECT
make reconcile TENANT_ONLY=acme PROJECT=$PROJECT | tail -2
make batch PROJECT=$PROJECT
J='resource.type="cloud_run_job" AND resource.labels.job_name="documind-ingest-batch"'
gcloud logging read "$J AND (jsonPayload.event=\"ingest_ok\" OR jsonPayload.event=\"batch_run\")" --project $PROJECT --freshness=30m --limit 2 --format='value(jsonPayload)'
gcloud storage cp evals/corpus/acme/cgst_act_2017.pdf gs://$PROJECT-uploads/acme/cgst_act_2017.pdf --project $PROJECT
git checkout -- services/ingest/main.py
make build SERVICES=ingest PROJECT=$PROJECT
make deploy-services SERVICES=ingest SCRIPTS=commands/lesson-12.5.sh BATCH_JOB=true PROJECT=$PROJECT
```

```text
{'event': 'ingest_queued_batch', 'tenant': 'acme', 'doc_key': 'acme_1249d8cf...', 'pages': 236, 'generation': '...',
 'consumer': 'documind-ingest-batch started (...); the hourly schedule backstops it'}
1 queued document(s)
  acme_1249d8cf5e7a9b3  gs://documind-ai-YOUR-ID-uploads/acme/cgst_act_2017.pdf  pages=236  generation=...
{"reconcile": "queued", "name": "acme/cgst_act_2017.pdf", "why": "handed to the batch lane; the batch job indexes it, the claim says queued"}
{"event": "reconcile_done", ..., "queued": 1, "drift": 0}
{'event': 'ingest_ok', 'tenant': 'acme', 'lane': 'batch', 'chunks': 390, 'pages': 236, 'reused': 390, 'embedded': 0, 'retired': 390, ...}
{'event': 'batch_run', 'queued': 1, 'indexed': 1, 'skipped': 0, 'gone': 0, 'failed': 0}
```

pypdf counted the pages for nothing, the claim went `queued`, the job (7,200 s, the same `index_document()` with
`lane=batch`) indexed it, and the carry-over reused every vector because Document AI produced the same text - the
bill is 236 pages of parsing, no embeddings. The job's `ingest_ok` is in the job's log, so `make reindex` and
`make ingest-one` would not have seen it. The last four lines undo the version (reactivated before any page is
counted) and put the ceiling back. Keep `BATCH_JOB=true` on every later `make plan` / `make up`.

## 10. Reconcile and drift

```bash
make reconcile PROJECT=$PROJECT | tail -1                     # drift 0 once the poison object is gone
gcloud storage rm gs://$PROJECT-uploads/acme/gratuity_amendment_2026.md --project $PROJECT
make reconcile TENANT_ONLY=acme PROJECT=$PROJECT
make reconcile TENANT_ONLY=acme APPLY=1 PROJECT=$PROJECT
make sources TENANT_ONLY=acme PROJECT=$PROJECT | grep gratuity
make reindex FILE=evals/demo/gratuity_amendment_2026.md TENANT=acme PROJECT=$PROJECT
make reconcile TENANT_ONLY=acme PROJECT=$PROJECT | tail -1
make drift PROJECT=$PROJECT
make backfill-current PROJECT=$PROJECT
make reconcile-job PROJECT=$PROJECT
```

```text
{"event": "reconcile_done", "applied": false, "retire": 0, "reingest": 0, "backfill": 0, "touch": 0, "ok": 32, "withdrawn": 0, "queued": 0, "drift": 0}
{"reconcile": "retire", "name": "acme/gratuity_amendment_2026.md", "why": "gone from the bucket"}
{"event": "reconcile_done", "applied": false, ..., "retire": 1, ..., "drift": 1}
{"event": "reconcile_retired", "gcs_uri": "...", "retired_chunks": 3, ...}
{"event": "reconcile_done", "applied": true, ..., "retire": 1, ..., "drift": 1}
acme/gratuity_amendment_2026.md              retired ...      3      3     0       0 2026-10-01 ...
>> ingest_reactivated   acme_5b1c9e...   3   3   0   0
{"event": "reconcile_done", ..., "ok": 22, ..., "drift": 0}
>> no drift: the plan after apply is empty
{"event": "reconcile_backfill", "chunks": 0, "sources": 0, "applied": true}
>> documind-reconcile declared on ... and scheduled 23:30 IST (reconcile.tf); gcloud run jobs execute documind-reconcile --region us-central1 --project ... runs it now
```

With the poison object still in the bucket the first plan says `reingest ... not in the ledger` and `drift: 1`;
`APPLY=1` would rewrite it every night and re-poison the DLQ - delete it (block 8). A deleted document is
`retire`, drift 1, and `APPLY=1` flags its rows and writes `retired`; the object back through `make reindex` (it
matches `ingest_reactivated`) is drift 0. `make drift` is Terraform's plan-after-apply, not the ledger's drift.
`make backfill-current` prints zeros on a lane born with the ledger. `make reconcile-job` is an apply with
`RECONCILE_JOB=true`: the nightly job, its schedule, and the two alert policies; keep the flag on every later plan.

## 11. The gate

```bash
make smoke-reindex PROJECT=$PROJECT
```

```text
  [PASS] v1 indexed  ingest_ok chunks=3
  [PASS] v2 reindexed  chunks=3 reused=1 embedded=2 retired=3 effective_from=2026-10-01
  [PASS] v2 dated  effective_from=2026-10-01 read off the document
  [PASS] answer moved  ... bay 7 ...
  [PASS] v1 reactivated  chunks=3 embedded=0 retired=3
  [PASS] answer restored  ... bay 4 ...
  [PASS] ledger row  acme/smoke_note.md reused=3 embedded=0 retired=3 fingerprint=...
  7 pass · 0 fail
```

The lifecycle on a three-chunk fixture: SM-02 reused, the preamble and SM-01 embedded, the answer moved and back,
the undo embedded nothing. Run it once per lane.

*If the first check fails with "no worker line in time":* version 1 was already current (a previous run, or
someone ingested the fixture by hand); the worker acked it as `ingest_duplicate`, a line without the `tenant`
field the smoke filters on. `gcloud storage rm gs://$PROJECT-uploads/acme/smoke_note.md`, then
`make reconcile APPLY=1`, then run the smoke again: its first check now reads `ingest_reactivated`.

## 12. The rupees, and the lights

```bash
make usage HOURS=1 PROJECT=$PROJECT
make off PROJECT=$PROJECT
make down PROJECT=$PROJECT        # when the rehearsal is over (Module 14)
```

```text
14 answers from documind-api in the last 1 h; USD_INR=85
tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
acme                        14     61240     3920    0.0754      6.41    4210      0
```

`make usage` prices the answers (the API's usage rows), not the ingest; Document AI, embeddings and DLP appear in
Billing tomorrow under their own SKUs, and the arithmetic is the cost table below. `make off` floors the services
tonight (`documind-off` does the same at 23:00 IST); `make down` removes the services and everything Terraform
owns and prints what only deleting the project removes.

---

## Checklist

- [ ] `make preflight` clean; `W` exported
- [ ] block 3: `ingest_ok chunks=3 reused=0 embedded=3 effective_from=2026-10-01`; the ledger row `indexed`
- [ ] block 4: 31 `ingest_ok` lines, all `reused=0`; the handbook 283; `vectorsCount` above 200; `versions: 22`
- [ ] block 5: `ingest_ok 283 281 2 283 2026-10-01`; the answer says 90; the scoped gate red
- [ ] block 6: `ingest_reactivated 283 283 0 283`; the fingerprint back to block 4's; the answer says 60; the gate green
- [ ] block 7: `reconcile_withdrawn`, `ingest_withdrawn`, the plan's `withdrawn: 1, drift: 0`, `reconcile_restored`, `ingest_reactivated 3 0 0`
- [ ] block 8: `ingest_poison` naming `size`; the DLQ row an hour later; drained; the object removed
- [ ] block 10: drift 1 with the deleted document, drift 0 after `make reindex`; `make drift` empty; the nightly job declared
- [ ] block 11: `7 pass · 0 fail`
- [ ] block 12: `make off` run; `make down` when the rehearsal is over
- [ ] the sentence: the undo embedded nothing because nothing was deleted - the swap flagged the rows, the rows kept their vectors and stamps, and `reactivate()` counted them and flipped a flag

## Cost table

| Block | What bills | Rs, RESIDENCY=us (default) | Rs, RESIDENCY=india |
|---|---|---|---|
| 3 one document in | 563 characters embedded; one DLP scan | under 0.01 | under 0.01 |
| 4 the corpus | Document AI 1,065 pages; 3.47 million characters embedded; three captions | about 915 | about 145 |
| 5 the re-issue | 2 chunks (about 370 characters) embedded; one DLP scan | under 0.01 | under 0.01 |
| 6 the undo | nothing | 0 | 0 |
| 7 retire and restore | nothing | 0 | 0 |
| 8 poison and the DLQ | nothing | 0 | 0 |
| 9 the batch lane (optional) | Document AI 236 pages again; embeddings reused | about 200 | about 30 |
| 10 to 12 reconcile, the smoke, the questions | 5 fixture chunks embedded; about a dozen Gemini answers | under 5 | under 5 |
| Whole runbook | Document AI is the bill | under 1,200 | under 200 |

Rates: Layout Parser $10 per 1,000 pages, Enterprise Document OCR $1.50 per 1,000 pages, `text-embedding-005`
$0.000025 per 1,000 characters, DLP inside the free gigabyte, `USD_INR = 85`; read on 21 September 2026 -
re-verify before quoting.

## Teardown

Before you leave the lane: the poison object removed (block 8), the DLQ drained, the amendment back and the plan
at drift 0 (block 10), `MAX_INLINE_PAGES` back at 250 and redeployed if you ran block 9, and `make off`. When the
rehearsal is over, `make down PROJECT=$PROJECT` (Module 14): the seven services, the corpora, then
`terraform destroy`; the batch and reconcile jobs go with it; Firestore and the buckets that hold objects stay
until the project is deleted, and `make down` says so.
