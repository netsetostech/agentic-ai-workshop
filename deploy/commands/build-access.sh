#!/usr/bin/env bash
# make build-access (mk/lane.mk; make up runs it before make build): give the account Cloud Build runs as exactly
# what a build needs.
#
# The kit names no account for Cloud Build, so a build runs as the project's default compute account. In an
# organization created on or after 3 May 2024 (iam.automaticIamGrantsForDefaultServiceAccounts) that account is
# created without the Editor role older projects gave it, and on 20 October 2026 the first build of a new lane stopped
# at a 403 on storage.objects.get after a 75-minute apply. These are lesson 0.3's recovery grants, made before the
# build: read the build sources, push the images, write the build logs. Each is skipped when the account already has
# it, so on an older project nothing changes; IAM is given two minutes only when a grant is new.
# Usage: PROJECT=<id> REGION=<region> [SLM_REGION=<region>] bash commands/build-access.sh
set -euo pipefail
: "${PROJECT:?set PROJECT}" "${REGION:?set REGION}"
SLM_REGION="${SLM_REGION:-us-central1}"
NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
BUILDER="serviceAccount:$NUMBER-compute@developer.gserviceaccount.com"
BUCKET="gs://${PROJECT}_cloudbuild"                  # the bucket gcloud builds submit uploads the source to
NEW=

# gcloud builds submit makes this bucket on a project's first build; make it first so it can carry the grant.
gcloud storage buckets describe "$BUCKET" --format=none >/dev/null 2>&1 ||
  gcloud storage buckets create "$BUCKET" --project="$PROJECT" --location=US --uniform-bucket-level-access --quiet

if ! gcloud storage buckets get-iam-policy "$BUCKET" --format=json | grep -q "$BUILDER"; then
  gcloud storage buckets add-iam-policy-binding "$BUCKET" --member="$BUILDER" --role=roles/storage.objectViewer --format=none
  NEW=1
fi
if ! gcloud artifacts repositories get-iam-policy documind --location="$REGION" --project="$PROJECT" --format=json | grep -q "$BUILDER"; then
  gcloud artifacts repositories add-iam-policy-binding documind --location="$REGION" --project="$PROJECT" \
    --member="$BUILDER" --role=roles/artifactregistry.writer --format=none
  NEW=1
fi
if ! gcloud projects get-iam-policy "$PROJECT" --flatten=bindings --filter="bindings.role=roles/logging.logWriter" \
    --format="value(bindings.members)" | grep -q "$BUILDER"; then
  gcloud projects add-iam-policy-binding "$PROJECT" --member="$BUILDER" --role=roles/logging.logWriter --condition=None --format=none
  NEW=1
fi

# gcloud run deploy --source (make deploy-gateway in REGION, make deploy-slm in SLM_REGION) builds through a bucket and
# a repository of its own in the service's region, which gcloud makes on first use with no grant for this account: on
# 22 October 2026 lesson 9.1's first gateway build stopped at the same 403. Make them first, so they carry the grants.
for region in $(printf '%s\n' "$REGION" "$SLM_REGION" | sort -u); do
  SOURCES="gs://run-sources-$PROJECT-$region"
  gcloud storage buckets describe "$SOURCES" --format=none >/dev/null 2>&1 ||
    gcloud storage buckets create "$SOURCES" --project="$PROJECT" --location="$region" --uniform-bucket-level-access --quiet
  if ! gcloud storage buckets get-iam-policy "$SOURCES" --format=json | grep -q "$BUILDER"; then
    gcloud storage buckets add-iam-policy-binding "$SOURCES" --member="$BUILDER" --role=roles/storage.objectViewer --format=none
    NEW=1
  fi
  gcloud artifacts repositories describe cloud-run-source-deploy --location="$region" --project="$PROJECT" --format=none >/dev/null 2>&1 ||
    gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location="$region" \
      --project="$PROJECT" --description="Cloud Run Source Deployments" --quiet
  if ! gcloud artifacts repositories get-iam-policy cloud-run-source-deploy --location="$region" --project="$PROJECT" \
      --format=json | grep -q "$BUILDER"; then
    gcloud artifacts repositories add-iam-policy-binding cloud-run-source-deploy --location="$region" --project="$PROJECT" \
      --member="$BUILDER" --role=roles/artifactregistry.writer --format=none
    NEW=1
  fi
done

# The keyless pipeline (lesson 11.1, .github/workflows/documind-cd.yml) submits its build as sa-documind-cicd, which
# terraform/sa.tf gives no storage role and no actAs beyond the services it deploys. A submit asks two things more of it:
# - the source bucket: gcloud builds submit reads the bucket and writes the source object into it. The workflow names
#   this bucket itself (--gcs-source-staging-dir), so gcloud skips its project-wide bucket listing, and the account
#   gets the bucket's legacy writer role on this one bucket: storage.buckets.get and the object writes, nothing more.
# - the build's own account: with the organization policy's defaults, "the user submitting the build must have the
#   iam.serviceAccounts.actAs permission on the service account" the build runs as (Cloud Build's service account
#   change). That account is $BUILDER. On a project old enough to have given it Editor, actAs on it would hand the
#   pipeline Editor too: the grant is refused there, and the pipeline's builds stop until the build runs as an account
#   of its own. Both are made only once sa-documind-cicd exists (make up's apply makes it before this runs).
CICD_SA="sa-documind-cicd@$PROJECT.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$CICD_SA" --project="$PROJECT" --format=none >/dev/null 2>&1; then
  CICD="serviceAccount:$CICD_SA"
  if ! gcloud storage buckets get-iam-policy "$BUCKET" --format=json | grep -q "$CICD"; then
    gcloud storage buckets add-iam-policy-binding "$BUCKET" --member="$CICD" --role=roles/storage.legacyBucketWriter --format=none
    NEW=1
  fi
  BROAD=
  for role in roles/editor roles/owner; do
    gcloud projects get-iam-policy "$PROJECT" --flatten=bindings --filter="bindings.role=$role" \
      --format="value(bindings.members)" | grep -q "$BUILDER" && BROAD="$role"
  done
  if [ -n "$BROAD" ]; then
    echo ">> build-access: $BUILDER holds $BROAD on $PROJECT: no actAs on it for sa-documind-cicd (it would be $BROAD too)"
  elif ! gcloud iam service-accounts get-iam-policy "${BUILDER#serviceAccount:}" --project="$PROJECT" --format=json | grep -q "$CICD"; then
    gcloud iam service-accounts add-iam-policy-binding "${BUILDER#serviceAccount:}" --project="$PROJECT" \
      --member="$CICD" --role=roles/iam.serviceAccountUser --format=none
    NEW=1
  fi
fi

if [ -n "$NEW" ]; then
  echo ">> build-access: granted $BUILDER its build roles; waiting 120s for IAM to apply them"
  sleep 120
else
  echo ">> build-access: $BUILDER already reads build sources, pushes images and writes build logs"
fi
