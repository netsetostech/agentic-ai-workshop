"""Lesson 0.5: Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer

The worker Pub/Sub pushes to, and the API every surface calls. The worker Pub/Sub pushes to, and the API every surface calls. Promote the ready API revision. Keep other service updates idle while this runs. The operator console, behind Google sign-in. This deployment creates documind-admin; Terraform and the image build do not. Confirm the project (yours, documind-ai-YOUR-ID) and region (asia-south1), and complete F2 first. The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup. The job execution succeeds. Chat is deployed as the kit's own script deploys it (commands/lesson-12.8.sh): a private service the UI reaches with the person's forwarded IAP assertion (services/frontend/chat.py, shared/iap.py), its callers bound one by one, and then IAP in front of it as well, the same door the UI and the admin console have. The Desk's five eval accounts are bound as soon as Terraform has made them, so make smoke-cases works later. The page people open, behind IAP. The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

Run order inside this file:
1. F4. Deploy the ingest worker and RAG API (source window 38)
2. F4. Deploy the ingest worker and RAG API (source window 39)
3. F4. Deploy the ingest worker and RAG API (source window 40)
4. F5. Deploy the admin console with IAP (source window 41)
5. F6. Initialize the checkpoint schema, then deploy chat (source window 42)
6. F6. Initialize the checkpoint schema, then deploy chat (source window 43)
7. F6. Initialize the checkpoint schema, then deploy chat (source window 44)
8. F7. Deploy the UI (source window 45)
9. F8. Deploy MCP, then the A2A agent (source window 46)
10. F8. Deploy MCP, then the A2A agent (source window 47)

Prerequisites: demo_08_gate_the_build_then_build_all_seven_images.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_f4_deploy_the_ingest_worker_and_rag_api.
COMMANDS_01 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}"
: "${DOCAI_PROCESSOR_ID:?Run F1}" "${VECTOR_INDEX_NAME:?Run F1}" "${BQ_CHUNK_TABLE:?Run F1}" "${RESIDENCY:?Restore ~/rag-env.sh}"
gcloud artifacts docker images describe "$IMAGE_REPO/ingest:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-ingest --project="$PROJECT" \\
  --image="$IMAGE_REPO/ingest:$GIT_SHA" \\
  --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated \\
  --ingress=internal \\
  --memory=2Gi --cpu=2 --concurrency=1 --timeout=600 \\
  --min-instances=0 --max-instances=30 \\
  --execution-environment=gen2 \\
  --service-account="documind-ingest-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|RESIDENCY=$RESIDENCY|DOCAI_PROCESSOR_ID=$DOCAI_PROCESSOR_ID|AUDIT_BUCKET=$PROJECT-audit|VECTOR_INDEX_NAME=$VECTOR_INDEX_NAME|BQ_CHUNK_TABLE=$BQ_CHUNK_TABLE|RETENTION_DAYS=${RETENTION_DAYS-30}|EMBEDDING_MODEL=${EMBEDDING_MODEL-text-embedding-005}|EMBEDDING_VERSION=${EMBEDDING_VERSION-1}|REGION=$REGION|BATCH_JOB=${BATCH_JOB_NAME-}|MANAGED_MIRROR=${MANAGED_MIRROR-off}|RAG_LOCATION=${RAG_LOCATION-us-central1}"

# Pub/Sub calls the worker as the ingest service account.
gcloud run services add-iam-policy-binding documind-ingest \\
  --region="$REGION" --project="$PROJECT" \\
  --member="serviceAccount:documind-ingest-sa@$PROJECT.iam.gserviceaccount.com" \\
  --role=roles/run.invoker >/dev/null
echo 'PASS: documind-ingest deployed.'
)

"""

def step_01_f4_deploy_the_ingest_worker_and_rag_api(session):
    """Run F4. Deploy the ingest worker and RAG API at this checkpoint.

    The worker Pub/Sub pushes to, and the API every surface calls.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Ingest.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_f4_deploy_the_ingest_worker_and_rag_api.
COMMANDS_02 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${PROJECT_NUMBER:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}"
: "${VECTOR_INDEX_ENDPOINT:?Run F1}" "${VECTOR_DEPLOYED_INDEX_ID:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/api:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-api --project="$PROJECT" \\
  --image="$IMAGE_REPO/api:$GIT_SHA" \\
  --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated \\
  --ingress=all \\
  --memory=1Gi --cpu=2 --concurrency=40 --timeout=120 \\
  --min-instances=0 --max-instances=20 \\
  --cpu-boost --execution-environment=gen2 \\
  --service-account="documind-api-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|RETRIEVAL_BACKEND=${RETRIEVAL_BACKEND:-firestore}|VECTOR_INDEX_ENDPOINT=$VECTOR_INDEX_ENDPOINT|VECTOR_DEPLOYED_INDEX_ID=$VECTOR_DEPLOYED_INDEX_ID|SELF_URL=https://documind-api-$PROJECT_NUMBER.$REGION.run.app|IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-ui,/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-chat|DEMO_MODE=${DEMO_MODE-1}|UPLOAD_BUCKET=$PROJECT-uploads|MEDIA_BUCKET=$PROJECT-media|AUDIT_BUCKET=$PROJECT-audit|GENERATOR_MODEL=${GENERATOR_MODEL-gemini-3.6-flash}|RAG_MODEL_BASE=${RAG_MODEL_BASE-gemini-3.6-flash}|ROUTING=${ROUTING-off}|BUDGET_USD=${BUDGET_USD-100}${SPEND_PCT:+|SPEND_PCT=$SPEND_PCT}|MODEL_BACKEND=${MODEL_BACKEND-vertex}|LITELLM_URL=https://documind-gateway-$PROJECT_NUMBER.$REGION.run.app|ARMOR=${ARMOR-off}|ARMOR_LOCATION=${ARMOR_LOCATION-asia-south1}|ARMOR_TEMPLATE=${ARMOR_TEMPLATE-documind-guard}|SEMANTIC_CACHE=${SEMANTIC_CACHE-off}|RETRIEVAL_CURRENT_ONLY=${RETRIEVAL_CURRENT_ONLY-off}|RETRIEVAL_GRAPH=${RETRIEVAL_GRAPH-off}|GRAPH_BACKEND=${GRAPH_BACKEND-firestore}|SPANNER_INSTANCE=${SPANNER_INSTANCE-documind-graph}|SPANNER_DATABASE=${SPANNER_DATABASE-documind}|RAG_LOCATION=${RAG_LOCATION-us-central1}|EMBEDDING_MODEL=${EMBEDDING_MODEL-text-embedding-005}|EMBEDDING_VERSION=${EMBEDDING_VERSION-1}|GIT_SHA=$GIT_SHA" \\
  --vpc-connector="projects/$PROJECT/locations/$REGION/connectors/documind-vpc" \\
  --vpc-egress=private-ranges-only

# Invoker on THIS service only, for the four identities that reach it (matches sa.tf and check_authz.py).
for who in documind-ui-sa documind-chat-sa documind-mcp-sa documind-outsider-sa; do
  gcloud run services add-iam-policy-binding documind-api \\
    --region="$REGION" --project="$PROJECT" \\
    --member="serviceAccount:$who@$PROJECT.iam.gserviceaccount.com" --role=roles/run.invoker --quiet >/dev/null
  echo "  invoker on documind-api: $who"
done
echo 'PASS: documind-api deployed.'
)

"""

def step_02_f4_deploy_the_ingest_worker_and_rag_api(session):
    """Run F4. Deploy the ingest worker and RAG API at this checkpoint.

    The worker Pub/Sub pushes to, and the API every surface calls.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - RAG API.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_f4_deploy_the_ingest_worker_and_rag_api.
COMMANDS_03 = """source "$DEMO_ROOT/commands/session-restart.sh" &&
rag_promote_ready_api

"""

def step_03_f4_deploy_the_ingest_worker_and_rag_api(session):
    """Run F4. Deploy the ingest worker and RAG API at this checkpoint.

    The worker Pub/Sub pushes to, and the API every surface calls. Promote the ready API revision. Keep other service updates idle while this runs.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Promote API.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_f5_deploy_the_admin_console_with_iap.
COMMANDS_04 = """(
set -euo pipefail
: "${PROJECT:?Run F1}"
: "${REGION:?Run F1}"
: "${PROJECT_NUMBER:?Run F1}"
: "${IMAGE_REPO:?Run F1}"
: "${GIT_SHA:?Use the source tag of the successfully built images}"
: "${ADMIN_EMAILS:?Restore the approved administrator email list}"
: "${AUDIT_BUCKET:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/admin:$GIT_SHA" \\
  --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-admin --project="$PROJECT" \\
  --image="$IMAGE_REPO/admin:$GIT_SHA" --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated --iap --ingress=all \\
  --service-account="documind-admin-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|ADMIN_EMAILS=$ADMIN_EMAILS|AUDIT_BUCKET=$AUDIT_BUCKET|IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-admin" \\
  --set-secrets='COOKIE_SECRET=cookie-secret:latest' \\
  --session-affinity --cpu-boost

gcloud run services add-iam-policy-binding documind-admin --project="$PROJECT" --region="$REGION" \\
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \\
  --role='roles/run.invoker' >/dev/null

for who in $(printf '%s' "$ADMIN_EMAILS" | tr ',' ' '); do
  gcloud iap web add-iam-policy-binding --project="$PROJECT" \\
    --resource-type=cloud-run --service=documind-admin --region="$REGION" \\
    --member="user:$who" --role='roles/iap.httpsResourceAccessor' >/dev/null
  echo "  IAP access on documind-admin: $who"
done
echo 'PASS: documind-admin deployed.'
)

"""

def step_04_f5_deploy_the_admin_console_with_iap(session):
    """Run F5. Deploy the admin console with IAP at this checkpoint.

    The operator console, behind Google sign-in. This deployment creates documind-admin; Terraform and the image build do not. Confirm the project (yours, documind-ai-YOUR-ID) and region (asia-south1), and complete F2 first.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Admin.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_f6_initialize_the_checkpoint_schema_then_d.
COMMANDS_05 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}" "${CHECKPOINT_INSTANCE:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/chat:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
if gcloud run jobs describe documind-checkpoint-setup --project="$PROJECT" --region="$REGION" >/dev/null 2>&1; then
  gcloud run jobs describe documind-checkpoint-setup --project="$PROJECT" --region="$REGION" --format=yaml
  echo 'STOP: the job already exists. Review its image, service account, Cloud SQL attachment and secret above. If they are correct, run the "Rerun existing job" block instead.' >&2
  exit 1
fi
gcloud run jobs create documind-checkpoint-setup --project="$PROJECT" --region="$REGION" \\
  --image="$IMAGE_REPO/chat:$GIT_SHA" \\
  --service-account="documind-chat-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-cloudsql-instances="$CHECKPOINT_INSTANCE" \\
  --set-secrets='CHECKPOINT_DSN=documind-checkpoint-dsn:latest' \\
  --command=python --args=migrate.py
gcloud run jobs execute documind-checkpoint-setup --project="$PROJECT" --region="$REGION" --wait
echo 'PASS: checkpoint schema initialized.'
)

"""

def step_05_f6_initialize_the_checkpoint_schema_then_d(session):
    """Run F6. Initialize the checkpoint schema, then deploy chat at this checkpoint.

    The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Checkpoint job.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_f6_initialize_the_checkpoint_schema_then_d.
COMMANDS_06 = """gcloud run jobs execute documind-checkpoint-setup --project="$PROJECT" --region="$REGION" --wait

"""

def step_06_f6_initialize_the_checkpoint_schema_then_d(session):
    """Run F6. Initialize the checkpoint schema, then deploy chat at this checkpoint.

    The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Rerun existing job (only after review).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

# Original CLI workflow for step_07_f6_initialize_the_checkpoint_schema_then_d.
COMMANDS_07 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${PROJECT_NUMBER:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}"
: "${CHECKPOINT_INSTANCE:?Run F1}" "${API_URL:?Run F1}" "${CHAT_URL:?Run F1}" "${AUDIT_BUCKET:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/chat:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-chat --project="$PROJECT" \\
  --image="$IMAGE_REPO/chat:$GIT_SHA" --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated --ingress=all \\
  --memory=1Gi --cpu=1 --concurrency=20 --timeout=300 \\
  --min-instances=0 --max-instances=10 \\
  --service-account="documind-chat-sa@$PROJECT.iam.gserviceaccount.com" \\
  --add-cloudsql-instances="$CHECKPOINT_INSTANCE" \\
  --set-secrets='CHECKPOINT_DSN=documind-checkpoint-dsn:latest' \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|DOCUMIND_PROFILE=gcp|RAG_API_URL=$API_URL|SELF_URL=$CHAT_URL|RAG_TIMEOUT_S=90|DOCUMIND_BRAIN=langchain|GOOGLE_GENAI_USE_VERTEXAI=1|GOOGLE_CLOUD_LOCATION=global|AUDIT_BUCKET=$AUDIT_BUCKET|IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-chat,/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-ui"

# Who may call it: the UI's account and the eval gate's outsider, then the Desk's five eval accounts and the Google
# Chat bridge's, each bound only once Terraform has created it (desk.tf; the bridge's only with gchat_door=true).
for who in documind-ui-sa documind-outsider-sa \\
           documind-evalacme-sa documind-evalzeta-sa documind-evalglobex-sa documind-evalleaver-sa documind-evalgrc-sa \\
           documind-gchat-sa; do
  gcloud iam service-accounts describe "$who@$PROJECT.iam.gserviceaccount.com" --project="$PROJECT" >/dev/null 2>&1 \\
    || { echo "  $who does not exist yet - not bound"; continue; }
  gcloud run services add-iam-policy-binding documind-chat --project="$PROJECT" --region="$REGION" \\
    --member="serviceAccount:$who@$PROJECT.iam.gserviceaccount.com" --role='roles/run.invoker' --quiet >/dev/null
  echo "  invoker on documind-chat: $who"
done

# No IAP in front of the chat service, as the kit's own deploy (commands/lesson-12.8.sh): every caller is a service
# account, and IAP there refused the UI before the Desk could say who you are. --no-iap also turns off an IAP an
# earlier version of this block switched on. The service stays private: the invoker list above and the roster.
gcloud beta run services update documind-chat --project="$PROJECT" --region="$REGION" --no-iap
echo 'PASS: documind-chat deployed.'
)

"""

def step_07_f6_initialize_the_checkpoint_schema_then_d(session):
    """Run F6. Initialize the checkpoint schema, then deploy chat at this checkpoint.

    The job execution succeeds. Chat is deployed as the kit's own script deploys it (commands/lesson-12.8.sh): a private service the UI reaches with the person's forwarded IAP assertion (services/frontend/chat.py, shared/iap.py), its callers bound one by one, and then IAP in front of it as well, the same door the UI and the admin console have. The Desk's five eval accounts are bound as soon as Terraform has made them, so make smoke-cases works later.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Chat.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_07)

# Original CLI workflow for step_08_f7_deploy_the_ui.
COMMANDS_08 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${PROJECT_NUMBER:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}"
: "${API_URL:?Run F1}" "${CHAT_URL:?Run F1}" "${ADMIN_URL:?Run F1}" "${ADMIN_EMAILS:?Run F1}"
: "${DOCAI_LOCATION:?Run F1}" "${DOCAI_PROCESSOR_ID:?Run F1}" "${VECTOR_INDEX_ENDPOINT:?Run F1}" "${VECTOR_DEPLOYED_INDEX_ID:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/ui:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-ui --project="$PROJECT" \\
  --image="$IMAGE_REPO/ui:$GIT_SHA" --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated --iap --ingress=all \\
  --memory=2Gi --cpu=2 --concurrency=80 --timeout=3600 \\
  --min-instances="${MIN_INSTANCES:-0}" --max-instances=10 \\
  --cpu-boost --session-affinity --execution-environment=gen2 \\
  --service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^AUTH_MODE=iap|RAG_API_URL=$API_URL|CHAT_URL=$CHAT_URL|ADMIN_URL=$ADMIN_URL|SPEECH_REGION=asia-south1|GOOGLE_CLOUD_PROJECT=$PROJECT|GOOGLE_CLOUD_LOCATION=$REGION|UPLOAD_BUCKET=$PROJECT-uploads|LAYOUT_PROCESSOR=projects/$PROJECT/locations/$DOCAI_LOCATION/processors/$DOCAI_PROCESSOR_ID|TTS_CACHE_BUCKET=$PROJECT-tts-cache|VECTOR_INDEX_ENDPOINT=$VECTOR_INDEX_ENDPOINT|DEPLOYED_INDEX_ID=$VECTOR_DEPLOYED_INDEX_ID|CHUNKS_COLLECTION=chunks|AUDIT_COLLECTION=audit_events|OBSERVABILITY_DATASET=documind_observability|RAG_MODEL=gemini-3.6-flash|ADMIN_EMAILS=$ADMIN_EMAILS|ADMIN_DOMAINS=${ADMIN_DOMAINS:-}|IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/$REGION/services/documind-ui" \\
  --set-secrets='COOKIE_SECRET=cookie-secret:latest' \\
  --vpc-connector="projects/$PROJECT/locations/$REGION/connectors/documind-vpc" \\
  --vpc-egress=private-ranges-only

gcloud iam service-accounts add-iam-policy-binding "documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\
  --project="$PROJECT" --member="serviceAccount:documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\
  --role='roles/iam.serviceAccountTokenCreator' --condition=None >/dev/null

gcloud run services add-iam-policy-binding documind-ui --project="$PROJECT" --region="$REGION" \\
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \\
  --role='roles/run.invoker' >/dev/null

for who in $(printf '%s' "$ADMIN_EMAILS" | tr ',' ' '); do
  gcloud iap web add-iam-policy-binding --project="$PROJECT" \\
    --resource-type=cloud-run --service=documind-ui --region="$REGION" \\
    --member="user:$who" --role='roles/iap.httpsResourceAccessor' >/dev/null
  echo "  IAP access on documind-ui: $who"
done
echo 'PASS: documind-ui deployed.'
)

"""

def step_08_f7_deploy_the_ui(session):
    """Run F7. Deploy the UI at this checkpoint.

    The page people open, behind IAP.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - UI.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_08)

# Original CLI workflow for step_09_f8_deploy_mcp_then_the_a2a_agent.
COMMANDS_09 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}" "${API_URL:?Run F1}" "${MCP_URL:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/mcp:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-mcp --project="$PROJECT" \\
  --image="$IMAGE_REPO/mcp:$GIT_SHA" --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated --ingress=all \\
  --memory=1Gi --cpu=1 --concurrency=40 --timeout=120 \\
  --min-instances="${MIN_INSTANCES:-0}" --max-instances=10 \\
  --cpu-boost --execution-environment=gen2 \\
  --service-account="documind-mcp-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|DOCUMIND_PROFILE=gcp|RAG_API_URL=$API_URL|SELF_URL=$MCP_URL|FASTMCP_STATELESS_HTTP=true|RAG_TIMEOUT_S=90"

for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do
  gcloud run services add-iam-policy-binding documind-mcp --project="$PROJECT" --region="$REGION" \\
    --member="serviceAccount:$who@$PROJECT.iam.gserviceaccount.com" --role='roles/run.invoker' >/dev/null
  echo "  invoker on documind-mcp: $who"
done
echo 'PASS: documind-mcp deployed.'
)

"""

def step_09_f8_deploy_mcp_then_the_a2a_agent(session):
    """Run F8. Deploy MCP, then the A2A agent at this checkpoint.

    The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - MCP.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_09)

# Original CLI workflow for step_10_f8_deploy_mcp_then_the_a2a_agent.
COMMANDS_10 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${IMAGE_REPO:?Run F1}" "${GIT_SHA:?Restore the session}" "${MCP_URL:?Run F1}" "${AGENT_URL:?Run F1}"
gcloud artifacts docker images describe "$IMAGE_REPO/agent:$GIT_SHA" --project="$PROJECT" --format='value(image_summary.digest)'
gcloud run deploy documind-agent --project="$PROJECT" \\
  --image="$IMAGE_REPO/agent:$GIT_SHA" --region="$REGION" --platform=managed \\
  --no-allow-unauthenticated --ingress=all \\
  --memory=1Gi --cpu=1 --concurrency=20 --timeout=300 \\
  --min-instances="${MIN_INSTANCES:-0}" --max-instances=5 --cpu-boost \\
  --execution-environment=gen2 \\
  --service-account="documind-agent-sa@$PROJECT.iam.gserviceaccount.com" \\
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|GOOGLE_GENAI_USE_VERTEXAI=1|GOOGLE_CLOUD_LOCATION=global|MCP_URL=$MCP_URL|SELF_URL=$AGENT_URL|AGENT_MODEL=gemini-3.6-flash|PEER_CHAIN=off|ADK_MAX_LLM_CALLS=12"

for who in documind-ui-sa documind-chat-sa; do
  gcloud run services add-iam-policy-binding documind-agent --project="$PROJECT" --region="$REGION" \\
    --member="serviceAccount:$who@$PROJECT.iam.gserviceaccount.com" --role='roles/run.invoker' >/dev/null
  echo "  invoker on documind-agent: $who"
done
echo 'PASS: documind-agent deployed.'
)

"""

def step_10_f8_deploy_mcp_then_the_a2a_agent(session):
    """Run F8. Deploy MCP, then the A2A agent at this checkpoint.

    The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - A2A agent.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_10)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_38', step_01_f4_deploy_the_ingest_worker_and_rag_api),
        ('source_39', step_02_f4_deploy_the_ingest_worker_and_rag_api),
        ('source_40', step_03_f4_deploy_the_ingest_worker_and_rag_api),
        ('source_41', step_04_f5_deploy_the_admin_console_with_iap),
        ('source_42', step_05_f6_initialize_the_checkpoint_schema_then_d),
        ('source_43', step_06_f6_initialize_the_checkpoint_schema_then_d),
        ('source_44', step_07_f6_initialize_the_checkpoint_schema_then_d),
        ('source_45', step_08_f7_deploy_the_ui),
        ('source_46', step_09_f8_deploy_mcp_then_the_a2a_agent),
        ('source_47', step_10_f8_deploy_mcp_then_the_a2a_agent),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
