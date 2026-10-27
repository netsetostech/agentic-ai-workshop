# Reference commands extracted from 12.3 (GCP_Capstone_12.3_AdminObservability.ipynb).
# NOT run automatically. Review, set $PROJECT / $GIT_SHA, then run by hand
# or via the Makefile live-tier targets. See deploy/README.md.

# ---- DEPLOY ----
# documind-admin is its OWN service and its OWN image. It used to deploy ui:$GIT_SHA,
# which is built from services/frontend/ only - so services/admin/*.py was in no
# image at all and this service came up as a second copy of the chat UI. Deployed,
# healthy, reachable, and not the code you wrote.
#
# make build makes that image, as it makes every image make up deploys: cloudbuild.yaml from
# the deploy/ context with services/admin/Dockerfile named, so shared/ (pii.py, audit_log.py)
# ships with it - the same modules the ingest worker scans with. Until 8 October 2026 this
# block built it a second time with `gcloud builds submit --file=`, a flag gcloud does not
# have, and under deploy-services' sh -ec that stopped make up here: no admin, UI, chat, MCP
# or A2A service, and no wait-index, roster, managed-stores or operators after them.
#
# The rest is lesson-12.4.sh's pattern, the other service with IAP on the service itself
# (8 October 2026): REGION for the region and the registry, where us-central1 was written;
# --ingress=all, because internal-and-cloud-load-balancing refuses a browser at the run.app
# URL and the kit has no load balancer; IAP_AUDIENCE as THIS service's audience, which
# admin/auth.py refuses everyone without; ADMIN_EMAILS as make deploy-services passes it,
# where two placeholder addresses were written; IAP's service agent as the invoker; and one
# IAP grant per address, where a placeholder group was bound. No COOKIE_SECRET: nothing in
# services/admin reads it, and documind-admin-sa may not read that secret (secrets.tf grants
# it to the UI's and the API's accounts), so mounting it failed the deploy.
gcloud run deploy documind-admin \
  --image=${REGION:-us-central1}-docker.pkg.dev/$PROJECT/documind/admin:$GIT_SHA \
  --region=${REGION:-us-central1} --no-allow-unauthenticated \
  --ingress=all \
  --service-account=documind-admin-sa@$PROJECT.iam.gserviceaccount.com \
  --set-env-vars=^:^GOOGLE_CLOUD_PROJECT=$PROJECT:ADMIN_EMAILS=$ADMIN_EMAILS:AUDIT_BUCKET=$PROJECT-audit:IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/${REGION:-us-central1}/services/documind-admin \
  --session-affinity --cpu-boost

# IAP on the service, then IAP's service agent as its invoker: once IAP is on, the agent is
# what calls the service, and gcloud does not grant it.
gcloud beta run services update documind-admin --region=${REGION:-us-central1} --iap
gcloud run services add-iam-policy-binding documind-admin \
  --region=${REGION:-us-central1} --project=$PROJECT \
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \
  --role=roles/run.invoker

# Who may sign in: one grant per address in ADMIN_EMAILS (comma-separated), as for the UI.
# admin/auth.py then checks the same list itself, the defence in depth behind IAP.
for who in $(echo "$ADMIN_EMAILS" | tr ',' ' '); do
  gcloud iap web add-iam-policy-binding --project=$PROJECT \
    --resource-type=cloud-run --service=documind-admin --region=${REGION:-us-central1} \
    --member="user:$who" --role=roles/iap.httpsResourceAccessor
done

# admin-sa's project roles (BigQuery, Firestore, logs, the audit bucket) are Terraform's: sa.tf's admin_roles,
# applied before this block runs. Two gcloud grants here repeated them without --condition=None, which stops
# make up's sh -ec on a project whose policy carries a condition (12 October 2026).

# ---- SMOKE ----
# 1. Sink is writing
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM documind_observability.run_googleapis_com_stdout \
   WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)"
# -> positive integer = sink healthy

# 2. DLP finds PII in a test doc
python -c "from dlp import inspect_and_log; print(inspect_and_log(\
  'test_chunk', 'tenant-acme', 'Contact raj@example.in PAN ABCDE1234F'))"
# -> {"has_pii": true, "types": ["EMAIL_ADDRESS","INDIA_PAN_INDIVIDUAL"]}

# 3. Audit emit writes to GCS
python -c "from audit import emit; print(emit(\
  "doc.upload", {"email":"alice@acme.in","tenant_id":"tenant-acme"},\
  {"type":"doc","id":"doc_9f23"}))"
gsutil ls gs://$PROJECT-audit/$(date +%Y)/$(date +%m)/$(date +%d)/tenant-acme/

# 4. Non-admin user cannot see admin tab
# Open documind-admin Cloud Run URL as a non-admin user -> IAP 403.

# 5. Alert fires on synthetic latency spike
hey -n 200 -c 20 -m POST -H "Authorization: Bearer $TOK" \
  https://documind-api-xxx.run.app/v1/query
# Wait 6 min, PagerDuty page arrives if p95 > 3000ms

