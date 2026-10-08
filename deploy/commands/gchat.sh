# The Google Chat door onto the DocuMind Desk (workshop lesson 10.4): documind-gchat, the bridge.
# NOT run automatically. make deploy-gchat runs the DEPLOY block below through make deploy-services, which passes
# PROJECT, GIT_SHA, REGION, PROJECT_NUMBER and CHAT_URL. Terraform creates what it runs on first
# (terraform/gchat.tf: make plan up GCHAT_DOOR=true), and the app is configured in the Google Cloud console (Google
# Chat API, Configuration) with its HTTP endpoint URL set to exactly the SELF_URL below, with no trailing slash.

# ---- DEPLOY ----
# 1. The service. No IAP: every caller is a Google service agent or a service account, nobody signs in here, and the
#    code checks each caller by name (services/gchat/main.py): the Workspace add-on agent of this project's Chat app
#    on /, Pub/Sub's push account on /work. SELF_URL is the deterministic run.app URL, the one audience both verify.
#    CHAT_URL is the chat service's, the only service the bridge calls. GCHAT_CALLER is the add-on agent's address,
#    which carries this project's number, so a request from another project's Chat app is refused by name.
gcloud run deploy documind-gchat \
  --image=${REGION:-us-central1}-docker.pkg.dev/$PROJECT/documind/gchat:$GIT_SHA \
  --region=${REGION:-us-central1} --platform=managed \
  --no-allow-unauthenticated --ingress=all \
  --memory=512Mi --cpu=1 --concurrency=20 --timeout=300 \
  --min-instances=0 --max-instances=3 \
  --service-account=documind-gchat-sa@$PROJECT.iam.gserviceaccount.com \
  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|SELF_URL=https://documind-gchat-$PROJECT_NUMBER.${REGION:-us-central1}.run.app|CHAT_URL=$CHAT_URL|GCHAT_CALLER=service-$PROJECT_NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com"

# 2. Who may call it: Pub/Sub's push account, which reaches /work and nothing else, and the eval gate's outsider, which
#    make smoke-gchat sends to / and /work to see the code's 401 and not the network's. sa.tf's caller graph is the
#    list; the gate check_authz.py compares this script with it.
for who in documind-gchatpush-sa documind-outsider-sa; do
  gcloud run services add-iam-policy-binding documind-gchat \
    --region=${REGION:-us-central1} --project=$PROJECT \
    --member="serviceAccount:$who@$PROJECT.iam.gserviceaccount.com" --role=roles/run.invoker --quiet
done

# 3. The Workspace add-on agent, which calls / for the Chat app, as 12.4 binds IAP's agent. It may not exist until the
#    app is configured: then this says so, and make deploy-gchat binds it when run again.
gcloud run services add-iam-policy-binding documind-gchat --region=${REGION:-us-central1} --project=$PROJECT --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com" --role=roles/run.invoker --quiet >/dev/null \
  || echo ">> the Chat app's add-on agent does not exist yet: configure the app (Google Chat API, Configuration), then run make deploy-gchat again"
