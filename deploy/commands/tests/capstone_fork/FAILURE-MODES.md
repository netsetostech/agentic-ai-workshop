# Sahyadri Freight on DocuMind: the failure modes

Four entries, each reproduced by a command this fork holds, and what the monitoring does about it.

## Pinned traffic hides a change

Symptom: a setting changed with gcloud run services update never serves; /health still reports the old value.
Command: `make gotcha-drill ID=pinned-traffic`
Caught by: no policy. The countermeasure is make gotcha-detect after every hand update.

## A rollback keeps the bad template

Symptom: after make rollback, the next make release-candidate carries the rolled-back GENERATOR_MODEL.
Command: `make gotcha-drill ID=rollback-keeps-template`
Caught by: no policy; make incident names the repair.

## A poison upload pages an hour later

Symptom: a zero-byte object fails twelve deliveries, then the dead-letter policy pages.
Command: `make poison TENANT=sahyadri PROJECT=documind-ai-YOUR-ID`
Caught by: Ingest dead-letter queue holds messages.

## A mistyped model answers 500

Symptom: every agent turn on documind-chat fails with a 500, while /health stays green.
Command: `FAULT=model HOLD=1 PROJECT=documind-ai-YOUR-ID bash commands/incident-drill.sh`
Caught by: no policy counts 5xx answers; make remediate diagnoses it from the request log.
