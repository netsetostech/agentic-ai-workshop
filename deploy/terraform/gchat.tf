# The Google Chat door onto the DocuMind Desk (workshop lesson 10.4): what documind-gchat, the bridge, runs on.
# services/gchat/ is the bridge, commands/gchat.sh deploys it, and the Desk decides whom it may speak for
# (services/chat/delegation.py). The bridge's own account, documind-gchat-sa, is declared in terraform/desk.tf.
#
# Whoever can mint a token as documind-gchat-sa, act as it, or publish to documind-gchat-work can speak for every
# rostered person of every tenant that switched the door on. So, and tools/check_authz.py holds the kit to it:
#   - nobody may mint as it: no person, no Google agent, not cicd_actas; its two project roles below are the only
#     ones it holds, and datastore.user is conditioned on the bridge's own database;
#   - only it may publish to the work topic, and no account holds a Pub/Sub publisher, editor or admin role at
#     project scope;
#   - Pub/Sub mints the push token as a second account, documind-gchatpush-sa, which holds no project role, is not a
#     delegate, and can reach the bridge's /work and nothing else.
# Nothing here bills while idle except what the claims database stores, and its claims expire within a day.
#
# Field names marked "from memory" below are checked by terraform validate and terraform plan; the lane proof
# (make plan up GCHAT_DOOR=true, then make down and make up) checks what they do.
#
# Off by default: GCHAT_DOOR=true on make plan / make up declares everything here and documind-gchat-sa (desk.tf);
# without it none of it exists and the Chat API stays off, as a lane without Google Workspace wants. Once on, keep
# GCHAT_DOOR=true on every later plan, or the plan would delete the door and make plan's guard refuses it. A lane
# applied before this switch already has the door: GCHAT_DOOR=true keeps it, each resource moving to its [0] with no
# change. make deploy-gchat and make smoke-gchat read the output below and refuse while it is false.
variable "gchat_door" {
  type        = bool
  default     = false
  description = "declare the Google Chat door's accounts, claims database, Chat API, work topic and push subscription (lesson 10.4)"
}

output "gchat_door" {
  description = "GCHAT_DOOR as last applied: make deploy-gchat and make smoke-gchat refuse while it is false"
  value       = var.gchat_door
}

resource "google_service_account" "gchatpush" {
  count        = var.gchat_door ? 1 : 0
  account_id   = "documind-gchatpush-sa"
  display_name = "DocuMind Google Chat bridge: Pub/Sub's push identity (no project role; not a delegate)"
}

resource "google_project_iam_member" "gchat_logs" {
  count   = var.gchat_door ? 1 : 0
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gchat[0].email}"
}

# The duplicate claims (services/gchat/claims.py): a database of the bridge's own, so the bridge holds no role on the
# default database, where the rosters and the roles live. Delete protection is off and deletion_policy (from memory,
# with its default ABANDON) is DELETE, because it holds only 24-hour claims and make down should remove it.
resource "google_firestore_database" "gchat" {
  count                   = var.gchat_door ? 1 : 0
  project                 = var.project_id
  name                    = "documind-gchat"
  location_id             = var.india_region
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
}

resource "google_firestore_field" "gchat_events_expire_at" {
  count      = var.gchat_door ? 1 : 0
  project    = var.project_id
  database   = google_firestore_database.gchat[0].name
  collection = "gchat_events"
  field      = "expire_at"

  ttl_config {}
}

# roles/datastore.user on the claims database only. That an IAM condition on a Firestore database's resource name
# validates is from memory and unconfirmed: terraform plan and the lane proof check it. If it does not, the fallback
# is to keep no claims at all (the client- message id alone keeps one post per question), never a project-wide
# roles/datastore.user, which would let the bridge write rosters and roles.
resource "google_project_iam_member" "gchat_claims" {
  count   = var.gchat_door ? 1 : 0
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.gchat[0].email}"

  condition {
    title       = "documind-gchat-claims-only"
    description = "The Google Chat bridge's duplicate claims, and no other database"
    expression  = "resource.name == \"projects/${var.project_id}/databases/documind-gchat\""
  }
}

resource "google_project_service" "chat" {
  count              = var.gchat_door ? 1 : 0
  service            = "chat.googleapis.com"
  disable_on_destroy = false
}

# The work queue: one message per question the bridge acknowledged, {key, kind, email, session_id, space, thread,
# masked question or chip}. Its messages are stored in India (message_storage_policy, from memory), kept one hour,
# and never dead-lettered: the bridge's fifth attempt tells the person instead, so no topic holds question text.
resource "google_pubsub_topic" "gchat_work" {
  count = var.gchat_door ? 1 : 0
  name  = "documind-gchat-work"

  message_storage_policy {
    allowed_persistence_regions = [var.india_region]
  }
}

resource "google_pubsub_topic_iam_member" "gchat_publishes" {
  count  = var.gchat_door ? 1 : 0
  topic  = google_pubsub_topic.gchat_work[0].id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.gchat[0].email}"
}

locals {
  # Cloud Run's deterministic URL, as local.ingest_url (eventarc.tf). The push token's audience is the service URL,
  # not /work, so / and /work verify one audience: the bridge's SELF_URL (commands/gchat.sh).
  gchat_url = "https://documind-gchat-${data.google_project.current.number}.${var.region}.run.app"
}

# Pub/Sub mints the push token as documind-gchatpush-sa, which takes this grant to Pub/Sub's own service agent, on this
# account and no other (eventarc.tf's pattern).
resource "google_service_account_iam_member" "pubsub_mints_gchatpush_token" {
  count              = var.gchat_door ? 1 : 0
  service_account_id = google_service_account.gchatpush[0].name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "gchat_push" {
  count = var.gchat_door ? 1 : 0
  name  = "documind-gchat-push"
  topic = google_pubsub_topic.gchat_work[0].name

  push_config {
    push_endpoint = "${local.gchat_url}/work"
    oidc_token {
      service_account_email = google_service_account.gchatpush[0].email
      audience              = local.gchat_url # from memory
    }
  }

  # Ten seconds, doubling to a minute: the fifth attempt, counted in the claim, is a few minutes after the first.
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "60s"
  }
  # By default a subscription with no activity for 31 days expires, and a quiet lane would lose the door. An empty ttl
  # means it never expires (both from memory: terraform validate checks the block, terraform plan shows the value).
  expiration_policy {
    ttl = ""
  }
  ack_deadline_seconds       = 300
  message_retention_duration = "3600s" # one hour; the minimum allowed is from memory
  depends_on                 = [google_service_account_iam_member.pubsub_mints_gchatpush_token]
}
