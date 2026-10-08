# Lesson 3.2 runbook - From the bucket to the row, inspected live

A Cloud Shell runbook for lesson 3.2 (Module 3, Ingest). It shows every box of the ingest lane from the live project - the bucket, the notification, the topic, the push subscription, the dead-letter subscription, the worker's shape and environment, the two jobs and their schedules - then puts one document through and reads the trail it left, then sends a poison object towards the DLQ. The last section finds the same facts offline in the Terraform, for a machine with no project.

**Needs.** A lane deployed from Module 2 (`make up` done, `make smoke` green), Cloud Shell, and three exports:

```bash
export PROJECT=documind-ai-YOUR-ID
export TENANT=acme
export REGION=us-central1
cd code
```

**Costs.** Every `describe` and `list` is Rs 0. Block 7 embeds one one-chunk document (a fraction of a paisa at standard embedding pricing) and writes a handful of Firestore rows. Block 9's poison object costs nothing - the worker refuses it before it downloads anything. Cloud Run bills only while a request runs; the lane idles at zero instances.

**Takes.** About 30 minutes at the keyboard. The poison message needs closer to an hour to reach the dead-letter subscription (twelve attempts with a 10 s backoff doubling towards 600 s), so start block 9 early and read its last step at the end.

---

## 1. Preflight

```bash
make preflight PROJECT=$PROJECT
gcloud config set project $PROJECT
```

Expect:

```text
  ok    gcloud on PATH
  ok    signed in as you@example.com
  ok    project documind-ai-YOUR-ID exists
  ok    billing linked
```

Every line `ok`. A `MISS` line says what to run. Nothing here creates anything.

## 2. The bucket and its notification

```bash
gcloud storage buckets describe gs://$PROJECT-uploads \
  --format='yaml(location,versioning_enabled,uniform_bucket_level_access,public_access_prevention)'
gcloud storage buckets notifications list gs://$PROJECT-uploads
```

Expect:

```text
location: ASIA-SOUTH1
public_access_prevention: enforced
uniform_bucket_level_access: true
versioning_enabled: true
---
event_types:
- OBJECT_FINALIZE
payload_format: JSON_API_V1
topic: //pubsub.googleapis.com/projects/documind-ai-YOUR-ID/topics/documind-ingest
```

`versioning_enabled: true` is what lets the worker download a specific generation. One notification, one event type, one topic: `storage.tf` and `eventarc.tf`. If the notification list is empty, `terraform apply` never reached `google_storage_notification.uploads` - `make plan` and look for it.

## 3. The two topics

```bash
gcloud pubsub topics list --project $PROJECT --filter='name:documind-ingest' --format='value(name)'
```

Expect:

```text
projects/documind-ai-YOUR-ID/topics/documind-ingest
projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq
```

Two topics: the one the bucket publishes to and the dead-letter topic. If only the first exists, `eventarc.tf` is from before the DLQ; the subscription below will show no `deadLetterPolicy`.

## 4. The push subscription and the dead-letter subscription

```bash
gcloud pubsub subscriptions describe documind-ingest-push --project $PROJECT \
  --format='yaml(ackDeadlineSeconds,deadLetterPolicy,pushConfig.oidcToken.serviceAccountEmail,pushConfig.pushEndpoint,retryPolicy)'
gcloud pubsub subscriptions describe ingest-dlq-sub --project $PROJECT --format='value(topic)'
```

Expect:

```text
ackDeadlineSeconds: 600
deadLetterPolicy:
  deadLetterTopic: projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq
  maxDeliveryAttempts: 12
pushConfig:
  oidcToken:
    serviceAccountEmail: documind-ingest-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
  pushEndpoint: https://documind-ingest-NUMBER.us-central1.run.app
retryPolicy:
  maximumBackoff: 600s
  minimumBackoff: 10s
projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq
```

Four numbers and one account. `maxDeliveryAttempts: 12` is the applied value; `README.md` and the Makefile say five, and the Terraform resource (`eventarc.tf`) is what Terraform applied. The endpoint is Cloud Run's deterministic URL built from the project number. If `pushEndpoint` names a different region or number than your service, the subscription was applied with another `REGION`; the worker never receives a message and nothing logs.

## 5. The worker's shape and environment

```bash
gcloud run services describe documind-ingest --region $REGION --project $PROJECT \
  --format='yaml(metadata.annotations,spec.template.spec.serviceAccountName,spec.template.spec.containerConcurrency,spec.template.spec.timeoutSeconds,spec.template.spec.containers[0].resources.limits,spec.template.spec.containers[0].env)'
gcloud run services get-iam-policy documind-ingest --region $REGION --project $PROJECT --format='value(bindings)'
```

Expect, among the annotations and the spec:

```text
run.googleapis.com/ingress: internal
serviceAccountName: documind-ingest-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
containerConcurrency: 1
timeoutSeconds: 600
limits: {cpu: '2', memory: 2Gi}
env:
- {name: GOOGLE_CLOUD_PROJECT, value: documind-ai-YOUR-ID}
- {name: RESIDENCY, value: us}
- {name: DOCAI_PROCESSOR_ID, value: <hex id>}
- {name: AUDIT_BUCKET, value: documind-ai-YOUR-ID-audit}
- {name: VECTOR_INDEX_NAME, value: projects/NUMBER/locations/us-central1/indexes/<id>}
- {name: BQ_CHUNK_TABLE, value: documind-ai-YOUR-ID.rag_data.chunk_source}
- {name: RETENTION_DAYS, value: '30'}
- {name: EMBEDDING_MODEL, value: text-embedding-005}
- {name: EMBEDDING_VERSION, value: '1'}
- {name: REGION, value: us-central1}
- {name: BATCH_JOB, value: ''}
- {name: MANAGED_MIRROR, value: both}
- {name: RAG_LOCATION, value: us-central1}
{'members': ['serviceAccount:documind-ingest-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com'], 'role': 'roles/run.invoker'}
```

Concurrency 1 and a 600 s timeout, equal to the subscription's ack deadline. The thirteen variables of lesson 3.2 step 3: `DOCAI_PROCESSOR_ID`, `VECTOR_INDEX_NAME`, `RETENTION_DAYS` and the embedding pair were read out of the Terraform state by `make deploy-services`. `BATCH_JOB` is empty until `make deploy-services BATCH_JOB=true`, and an empty value is not a fault - the worker says so on every `ingest_queued_batch` line. The invoker binding is what lets Pub/Sub's token in; without it every push is a 403 and the message walks to the DLQ.

## 6. The jobs and their schedules

```bash
gcloud run jobs list --region $REGION --project $PROJECT
gcloud scheduler jobs list --location $REGION --project $PROJECT
```

Expect:

```text
JOB                     REGION       LAST RUN AT  ...
documind-ingest-batch   us-central1  ...
documind-off            us-central1  ...
documind-reconcile      us-central1  ...
ID                             LOCATION     SCHEDULE (TZ)                 TARGET_TYPE  STATE
documind-ingest-batch-hourly   us-central1  15 * * * * (Asia/Kolkata)     HTTP         ENABLED
documind-off-nightly           us-central1  0 23 * * * (Asia/Kolkata)     HTTP         ENABLED
documind-reconcile-nightly     us-central1  30 23 * * * (Asia/Kolkata)    HTTP         ENABLED
```

Two jobs on the ingest image (`batch.tf`, `reconcile.tf`) and their schedules: hourly at :15 for the batch lane, 23:30 IST for the reconcile, after the 23:00 night switch (`documind-off`, `off.tf`, which is Module 2's and not this lesson's). If the two jobs are missing, nothing is wrong yet: they exist only after `make batch-job` and `make reconcile-job`, which are applies with `BATCH_JOB=true` / `RECONCILE_JOB=true` and need an ingest image in the state (`make build` first). Keep both switches on every later `make plan`, or the next apply removes them.

## 7. One document in, and its line

```bash
SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
make ingest-one FILE=evals/corpus/acme/msa_acme_2026.md TENANT=$TENANT PROJECT=$PROJECT
gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"documind-ingest\" AND jsonPayload.event=~\"^(ingest_ok|ingest_duplicate|ingest_already_current|ledger_fingerprint)$\" AND timestamp>=\"$SINCE\"" \
  --project $PROJECT --limit 4 \
  --format='value(jsonPayload.event,jsonPayload.tenant,jsonPayload.doc_key,jsonPayload.chunks,jsonPayload.pages,jsonPayload.reused,jsonPayload.embedded,jsonPayload.retired,jsonPayload.fingerprint)'
```

Expect from `make`:

```text
>> gs://documind-ai-YOUR-ID-uploads/acme/msa_acme_2026.md - waiting for the worker (up to 5 min)
>> indexed: acme_<sha256> 6 1
```

and from the log read, newest first:

```text
ledger_fingerprint  acme                                  <16 hex>
ingest_ok  acme  acme_<sha256>  6  1  0  6  0  <16 hex>
```

The MSA is six chunks on one page - a `preamble` and the five `MSA-` clauses, chunked by section - so `chunks=6 pages=1 reused=0 embedded=6 retired=0` on a first load, and the `ledger_fingerprint` line beside it carries the same 16-hex fingerprint. If the document was already in from an earlier run, `make` reports "no ingest_ok in 5 min" and the log read shows `ingest_duplicate` (the same bytes, the claim lost) or `ingest_already_current` instead - both are 200s and both are correct; use a file that is not in yet, or `make reindex FILE= NAME=` with a changed copy, to see `ingest_ok` again. No line at all within five minutes: block 4's endpoint or block 5's invoker binding.

## 8. The ledger row, the index, the audit object

```bash
make sources TENANT_ONLY=$TENANT PROJECT=$PROJECT | grep -i 'msa_acme\|"ledger"'
make vector-status PROJECT=$PROJECT
gcloud storage ls gs://$PROJECT-audit/$(date -u +%Y/%m/%d)/$TENANT/ | grep doc.upload | tail -1
```

Expect:

```text
acme/msa_acme_2026.md                        indexed   <generation>      6      0     6       0 -          text-embedding-005@1   2026-09-21T..
{"ledger": "acme", "fingerprint": "<16 hex>", "versions": <n>, "last_event": "ingest_ok"}
displayName: documind-chunks
indexStats:
  vectorsCount: '<n>'
gs://documind-ai-YOUR-ID-audit/2026/09/21/acme/doc.upload-<uuid>.json
```

The ledger row is the `sources/acme~msa_acme_2026.md` document: which version is current, its generation, what it cost, the embedding it was made with. The fingerprint equals the one on the log line. `vectorsCount` is the index's own number and lags a streamed upsert by minutes - re-run in a while and it is six higher. The audit object is the `doc.upload` event under today's date and the tenant, in a bucket the worker may create in and never delete from.

## 9. Poison, twelve visits, the DLQ

```bash
SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
make poison PROJECT=$PROJECT TENANT=$TENANT
```

Expect:

```text
>> zero-byte object in: poison-<epoch>.pdf
>> the worker refused it (400): 1 validation error for IngestMessage
size
  Input should be greater than or equal to 1 ...
>> Pub/Sub retries a non-2xx five times with backoff, then ingest-dlq: make dlq in a few minutes
```

The zero-byte object fails `IngestMessage`'s `size >= 1` at the edge, before any download. The Makefile's last line says five and a few minutes; the subscription says twelve, and with the backoff doubling from 10 s towards 600 s the twelfth attempt is closer to an hour away. Watch the count climb in the meantime, and read the DLQ at the end of the session:

```bash
gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"documind-ingest\" AND jsonPayload.event=\"ingest_poison\" AND timestamp>=\"$SINCE\"" \
  --project $PROJECT --limit 20 --format='value(timestamp)' | wc -l
make dlq PROJECT=$PROJECT
```

Expect, once the attempts are spent:

```text
12
MESSAGE_ID        OBJECT_ID                 EVENT_TIME                DELIVERY_ATTEMPT
1234567890123456  acme/poison-<epoch>.pdf   2026-09-21T10:15:02.1Z   12
```

`make dlq` pulls five messages without acking, so the row shows again next time; `gcloud pubsub subscriptions pull ingest-dlq-sub --auto-ack --limit=5` clears it once a person has read it. An empty table before the hour is up is not a failure.

## 10. Offline: the same facts in the Terraform

For a machine with no project, or to check the page against the clone:

```bash
grep -n 'event_types\|payload_format\|ack_deadline_seconds\|max_delivery_attempts\|minimum_backoff\|maximum_backoff\|service_account_email\|ingest_url' terraform/eventarc.tf
grep -n 'location\|versioning\|age = ' terraform/storage.tf | head -8
grep -n 'name  *= "documind\|schedule\|time_zone\|timeout\|max_retries' terraform/batch.tf terraform/reconcile.tf
grep -n 'concurrency\|timeout\|max-instances\|ingress\|set-env-vars' commands/lesson-12.5.sh
grep -n 'MAX_INLINE_PAGES = \|STAGE_HOURS = \|RETENTION_DAYS = ' services/ingest/main.py
grep -n 'jsonPayload.event' terraform/alerts.tf
```

Expect the values of blocks 2 to 6 - `OBJECT_FINALIZE`, `JSON_API_V1`, `600`, `12`, `10s`, `600s`, the deterministic `ingest_url`; `var.india_region`, `versioning { enabled = true }`, `age = 90` and `age = 365`; `15 * * * *` and `30 23 * * *` in `Asia/Kolkata`, `7200s` and `1200s`, `max_retries = 0`; `--concurrency=1 --timeout=600 --max-instances=30 --ingress=internal`; `250`, `24`, `30` - and, from `alerts.tf`, the one regex that decides which five events become the `ingest_events` metric.

---

## Checklist

- [ ] `make preflight` all `ok`
- [ ] Bucket in `ASIA-SOUTH1`, versioning on, one `OBJECT_FINALIZE` notification into `documind-ingest`
- [ ] Two topics; the push subscription with `600`, `12`, `10s`, `600s` and the worker's account as the token
- [ ] `containerConcurrency: 1`, `timeoutSeconds: 600`, ingress `internal`, thirteen variables, the invoker binding
- [ ] Two jobs and two schedules (or the reason they are absent)
- [ ] One `ingest_ok` line with its fields, the `ledger_fingerprint` beside it, the ledger row, the audit object
- [ ] One `ingest_poison` line, the count climbing, the DLQ row with `deliveryAttempt` 12
- [ ] The offline greps agree with the live describes

## Teardown and cost

Nothing in this runbook needs tearing down. The MSA stays indexed as one more document of the tenant (the nightly walk sees a source that matches its ledger row); the poison object stays in the bucket as a zero-byte file the worker will never index - delete it with `gcloud storage rm gs://$PROJECT-uploads/$TENANT/poison-*.pdf` if you like a clean listing, which the walk then records as a retirement of nothing. The lane costs nothing while idle: Cloud Run at zero instances, Pub/Sub and Firestore by use. The hourly bills of the deployment as a whole - the Vector Search endpoint, the Cloud SQL instances, Spanner - are Module 2's `make off` and `make down`, not this lesson's.
