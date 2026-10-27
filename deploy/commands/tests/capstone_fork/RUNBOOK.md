# Sahyadri Freight on DocuMind: the runbook

## When a policy pages

- API p95 latency > 3s, or Unanswerable rate > 20% for a tenant: make remediate POLICY='<the policy>' prints the
  plan; for documind-api the plan is a rollback.
- Ingest dead-letter queue holds messages: make dlq shows the message; fix or remove the object, then acknowledge it.

## Roll back the API

`make rollback PROJECT=documind-ai-YOUR-ID REGION=asia-south1` returns the traffic to .previous-revision, the revision
make promote moved it off. Then make smoke-deployed and make incident.

## The recorded rollback

On 17 November 2026 the mistyped model (documind-api-00042-typ) was promoted by force and rolled back to
documind-api-00041-kel. The smoke runs before and after it are in evals/reports/smoke-deployed.jsonl, and make
incident prints them with what /version said.
