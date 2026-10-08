# The DocuMind Desk (workshop lesson 5.6): the case queue's Firestore pieces, its hourly overdue job, and the
# identities its live checks call the chat service as. Kept apart from firestore_indexes.tf, whose index table
# workshop lesson 2.4 computes from that file.

# ---------------------------------------------------------------------------------------------
# The case queue (shared/cases.py). cases/{case_id} carries its tenant; a draft carries expire_at, 30 minutes out,
# which the code checks (a confirm after it is 410) and this TTL only cleans up. A confirmed case has no expire_at:
# it is a record, and how long it is kept is the tenant's decision. case_tokens/{sha256} holds a client token's first
# case for a day, so a doubled press opens one case.
resource "google_firestore_field" "cases_expire_at" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "cases"
  field      = "expire_at"

  ttl_config {}
}

resource "google_firestore_field" "case_tokens_expire_at" {
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = "case_tokens"
  field      = "expire_at"

  ttl_config {}
}

# The queries the case queue makes, each an index of its own:
#   inbox    tenant == t AND queue == q AND status IN (...) ORDER BY created_at DESC   (cases.list_for, per queue)
#   inbox_ic the same, AND chosen_contacts CONTAINS me                                 (cases.list_for, a POSH queue)
#   mine     tenant == t AND requester == me ORDER BY created_at DESC                  (cases.list_for)
#   overdue  status IN (open, acknowledged, in_progress) AND due_at <= now + 24 h      (cases.overdue, the job)
#   tenant   tenant == t AND status IN (...) ORDER BY due_at                           (cases.tenant_cases, make cases)
locals {
  case_indexes = {
    inbox    = [["tenant", "ASCENDING"], ["queue", "ASCENDING"], ["status", "ASCENDING"], ["created_at", "DESCENDING"]]
    inbox_ic = [["tenant", "ASCENDING"], ["queue", "ASCENDING"], ["chosen_contacts", "CONTAINS"], ["status", "ASCENDING"], ["created_at", "DESCENDING"]]
    mine     = [["tenant", "ASCENDING"], ["requester", "ASCENDING"], ["created_at", "DESCENDING"]]
    overdue  = [["status", "ASCENDING"], ["due_at", "ASCENDING"]]
    tenant   = [["tenant", "ASCENDING"], ["status", "ASCENDING"], ["due_at", "ASCENDING"]]
  }
}

resource "google_firestore_index" "cases" {
  for_each    = local.case_indexes
  project     = var.project_id
  database    = google_firestore_database.main.name
  collection  = "cases"
  query_scope = "COLLECTION"

  dynamic "fields" {
    for_each = each.value
    content {
      field_path   = fields.value[0]
      order        = fields.value[1] == "CONTAINS" ? null : fields.value[1]
      array_config = fields.value[1] == "CONTAINS" ? "CONTAINS" : null
    }
  }
  fields {
    field_path = "__name__"
    order      = each.value[length(each.value) - 1][1]
  }
}

# ---------------------------------------------------------------------------------------------
# The hourly overdue scan (services/chat/desk_overdue.py): a Cloud Run job on the chat image the lane already runs
# (var.chat_image: make plan passes REGION-docker.pkg.dev/PROJECT/documind/chat:SHA), as chat-sa, which reads the
# cases already. It logs the id, the queue and due_at of each case due within 24 hours and unacknowledged, and of each
# breached case; it writes nothing. Like batch.tf, one apply: DESK_JOB=true on make plan / make up once a chat image
# exists (the job cannot be created before its image is pushed).
variable "desk_job" {
  type        = bool
  default     = false
  description = "declare and schedule documind-cases-overdue, the case queue's hourly scan (needs a chat image: make build first)"
}

variable "chat_image" {
  type        = string
  default     = ""
  description = "the chat image the overdue job runs (REGION-docker.pkg.dev/PROJECT/documind/chat:SHA)"
}

locals {
  desk_job = var.desk_job && var.chat_image != ""
}

resource "google_cloud_run_v2_job" "cases_overdue" {
  count    = local.desk_job ? 1 : 0
  name     = "documind-cases-overdue"
  location = var.region
  template {
    task_count = 1
    template {
      service_account = google_service_account.chat.email
      max_retries     = 0 # the next hour is the retry
      timeout         = "300s"
      containers {
        image   = var.chat_image
        command = ["python"]
        args    = ["desk_overdue.py", "--project", var.project_id]
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
          name  = "DOCUMIND_PROFILE"
          value = "gcp"
        }
      }
    }
  }
  lifecycle {
    ignore_changes = [client, client_version]
  }
}

resource "google_cloud_run_v2_job_iam_member" "cases_overdue_invoker" {
  count    = local.desk_job ? 1 : 0
  name     = google_cloud_run_v2_job.cases_overdue[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.chat.email}"
}

# Hourly, on the hour: the schedule's OAuth token is chat-sa's, the account that runs the job.
resource "google_cloud_scheduler_job" "cases_overdue" {
  count       = local.desk_job ? 1 : 0
  name        = "documind-cases-overdue-hourly"
  description = "DocuMind: log the case queue's due and breached cases (id, queue and due_at only)"
  schedule    = "0 * * * *"
  time_zone   = "Asia/Kolkata"
  region      = var.region
  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.cases_overdue[0].name}:run"
    oauth_token {
      service_account_email = google_service_account.chat.email
    }
  }
  depends_on = [google_cloud_run_v2_job_iam_member.cases_overdue_invoker]
}

# ---------------------------------------------------------------------------------------------
# The eval identities. The Desk's live checks (make smoke-cases, and the routed Desk's eval) must call the chat
# service as a person of each kind: an acme employee, a zeta employee, a globex employee, an acme leaver and an acme
# Grievance Redressal Committee member. A script cannot call it as a person - the bearer leg needs an ID token minted
# for SELF_URL, which only a service account can mint for another audience - so each is a service account on one
# tenant's roster (make roster), with its roles set by make roles. None holds a project role; each is bound
# roles/run.invoker on documind-chat alone (commands/lesson-12.8.sh, sa.tf's caller graph), and make desk-operators
# lets the operators mint as them. The names match documind-[a-z]+-sa, the pattern tools/check_authz.py reads a
# caller by: a hyphenated name (documind-desk-eval-acme) would match nothing, and the gate's two sides would disagree.
locals {
  desk_eval_accounts = {
    evalacme   = "DocuMind Desk eval: an acme employee"
    evalzeta   = "DocuMind Desk eval: a zeta employee"
    evalglobex = "DocuMind Desk eval: a globex employee"
    evalleaver = "DocuMind Desk eval: an acme leaver"
    evalgrc    = "DocuMind Desk eval: an acme Grievance Redressal Committee member"
  }
}

resource "google_service_account" "desk_eval" {
  for_each     = local.desk_eval_accounts
  account_id   = "documind-${each.key}-sa"
  display_name = each.value
}

# The Google Chat door's account, declared only on a lane planned with GCHAT_DOOR=true (terraform/gchat.tf). The chat
# service's invoker list and its caller graph name it either way, so they change once: lesson-12.8.sh binds it once it
# exists, so deploy chat again after turning the door on (make up does). Without it, the Desk's one delegate
# (services/chat/delegation.py) is an account nobody can be, and every delegation is refused. It sits on no roster, and
# holds only terraform/gchat.tf's two project roles, so the roster refuses it, as it refuses the outsider. Whoever can
# mint a token as this account could one day speak for every rostered person of a tenant that turns the Google Chat
# door on, so nobody is given that power: no person or agent gets roles/iam.serviceAccountTokenCreator or
# roles/iam.serviceAccountUser on it, it is not in sa.tf's cicd_actas, and tools/check_authz.py fails any line in the
# kit that would mint as it or grant either role on it.
resource "google_service_account" "gchat" {
  count        = var.gchat_door ? 1 : 0
  account_id   = "documind-gchat-sa"
  display_name = "DocuMind Google Chat bridge (nobody may mint as it)"
}
