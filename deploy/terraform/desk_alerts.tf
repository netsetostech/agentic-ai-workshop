# The DocuMind Desk, watched (workshop lessons 5.6 and 10.4): log-based metrics on the lines the Desk already writes,
# and the alert policies that read them. Kept out of alerts.tf, whose policy list lessons quote and count (13.2 asserts
# it, and prints this file's list beside it), as quota.tf keeps a resource of its own; every policy here notifies
# local.alert_channel_ids (alerts.tf).
#
# What a metric may carry: a tenant, a queue, a state, an event, a route, a method, an acceptance rule, a check's
# outcome. Never a person, a session, a case id or any text: no label below extracts one, so no incident can name who
# asked or who is waiting. The overdue job already logs a posh, grievance or privacy_request case's queue as
# "sensitive" (shared/cases.py).
#
# The router's metric counts people's turns only. A person is never a service account, and the eval accounts (make
# smoke-desk; make route-eval, whose arm C is the fallback by design) would otherwise page on a lane where nobody has
# asked anything. A posh, grievance or privacy_request turn names nobody, so it is counted whoever sent it. The gate
# check's row names nobody at all, so its metric counts every check, whoever asked.
#
# Every threshold is a starting value, not yet calibrated on any lane's traffic: the 1% fallback share, the 5-point
# rise and the 100-turn floors, and the gate check's 20% error share and 20-check floor, are this file's own; the 15%
# L2 cap is evals/route_threshold.py's ("cap 15% to start").

# The router's three policies and the gate check's error share are PromQL, and Cloud Monitoring may refuse a PromQL
# condition on a metric that has no data yet, which on a fresh lane would fail make up. So each switch is off until the
# author turns it on, once its metric has data: DESK_ROUTER_ALERTS=true once the router has run (make desk
# DESK_ROUTE=shadow or on, and some turns), DESK_GATE_ALERTS=true once the gate check has (make desk DESK_GATE=on for a
# tenant, and some questions). Each goes on make plan and make up (mk/agents.mk), then on every later plan, or the next
# one would remove its policies and make plan's guard refuses it.
variable "desk_router_alerts" {
  type        = bool
  default     = false
  description = "create the Desk router's three alert policies (DESK_ROUTER_ALERTS=true), once the router has run on the lane"
}

variable "desk_gate_alerts" {
  type        = bool
  default     = false
  description = "create the Desk gate check's error-share alert policy (DESK_GATE_ALERTS=true), once the check has run on the lane"
}

# ---------------------------------------------------------------------------------------------
# The router: one count per routed turn, from the desk rows of POST /v1/desk (surface "desk", arm B: the eval's
# POST /v1/route rows are surface "route") and the desk_shadow rows of /v1/chat turns decided in shadow. Declared on
# every lane, so its series exist before the policies that read it.
resource "google_logging_metric" "desk_router" {
  name    = "documind/desk_router"
  project = var.project_id
  filter  = <<EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="documind-chat"
    ((jsonPayload.event="desk" AND jsonPayload.surface="desk" AND jsonPayload.arm="B") OR jsonPayload.event="desk_shadow")
    NOT jsonPayload.user=~"[.]iam[.]gserviceaccount[.]com$"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "tenant"
      value_type  = "STRING"
      description = "Tenant the question belonged to"
    }
    labels {
      key         = "event"
      value_type  = "STRING"
      description = "desk (a POST /v1/desk turn) | desk_shadow (a /v1/chat turn the router decided in shadow)"
    }
    labels {
      key         = "route"
      value_type  = "STRING"
      description = "handbook | statute | case | clarify | out_of_scope | denied | not_covered | fallback"
    }
    labels {
      key         = "method"
      value_type  = "STRING"
      description = "rule | draft | single | user | anchor | model | arbiter | sticky | fallback"
    }
    labels {
      key         = "accepted_by"
      value_type  = "STRING"
      description = "The acceptance rule: A, B, C or D; F when the turn went to the arbiter (L2); empty when no rule ran"
    }
  }
  label_extractors = {
    tenant      = "EXTRACT(jsonPayload.tenant)"
    event       = "EXTRACT(jsonPayload.event)"
    route       = "EXTRACT(jsonPayload.route)"
    method      = "EXTRACT(jsonPayload.method)"
    accepted_by = "EXTRACT(jsonPayload.accepted_by)"
  }
}

# The queries, per tenant and event (desk and desk_shadow are separate series, so a tenant that changes mode is two).
# Each share is a ratio over the last hour, and it pages only in an hour of 100 routed turns or more, so one fallback
# among a handful of turns on a quiet lane is not a page. The week-on-week query compares the last seven days with the
# seven before, per route, a route last week never took counting 0 there, and needs 100 routed turns in each week. A
# threshold condition cannot look back a week (an alerting window stops at 25 hours), and all three are PromQL so that
# each can carry its floor; the metric is desk_router above, as PromQL names it.
locals {
  desk_router_promql   = "logging_googleapis_com:user_documind_desk_router{monitored_resource=\"cloud_run_revision\"}"
  desk_fallback_promql = "logging_googleapis_com:user_documind_desk_router{monitored_resource=\"cloud_run_revision\",method=\"fallback\"}"
  desk_l2_promql       = "logging_googleapis_com:user_documind_desk_router{monitored_resource=\"cloud_run_revision\",accepted_by=\"F\"}"
  desk_routed_promql   = "logging_googleapis_com:user_documind_desk_router{monitored_resource=\"cloud_run_revision\",route=~\"clarify|out_of_scope\"}"
  desk_hour_floor      = "and on (tenant, event) sum by (tenant, event) (increase(${local.desk_router_promql}[1h])) >= 100"
  desk_fallback_query = join("\n", [
    "sum by (tenant, event) (increase(${local.desk_fallback_promql}[1h]))",
    "  / on (tenant, event)",
    "sum by (tenant, event) (increase(${local.desk_router_promql}[1h]))",
    "> 0.01",
    local.desk_hour_floor,
  ])
  desk_l2_query = join("\n", [
    "sum by (tenant, event) (increase(${local.desk_l2_promql}[1h]))",
    "  / on (tenant, event)",
    "sum by (tenant, event) (increase(${local.desk_router_promql}[1h]))",
    "> 0.15",
    local.desk_hour_floor,
  ])
  desk_trend_query = join("\n", [
    "(",
    "  sum by (tenant, event, route) (increase(${local.desk_routed_promql}[7d]))",
    "    / on (tenant, event) group_left",
    "  sum by (tenant, event) (increase(${local.desk_router_promql}[7d]))",
    ")",
    "- on (tenant, event, route)",
    "(",
    "  (",
    "    sum by (tenant, event, route) (increase(${local.desk_routed_promql}[7d] offset 7d))",
    "      / on (tenant, event) group_left",
    "    sum by (tenant, event) (increase(${local.desk_router_promql}[7d] offset 7d))",
    "  )",
    "  or on (tenant, event, route)",
    "  0 * sum by (tenant, event, route) (increase(${local.desk_routed_promql}[7d]))",
    ")",
    "> 0.05",
    "and on (tenant, event) sum by (tenant, event) (increase(${local.desk_router_promql}[7d])) >= 100",
    "and on (tenant, event) sum by (tenant, event) (increase(${local.desk_router_promql}[7d] offset 7d)) >= 100",
  ])
}

# The fallback is the router failing: L1 timed out, errored or could not be parsed, or the turn ran past the router's
# budget, and the person got a direct answer over every desk they may use (services/chat/desk_router.py _fallback).
resource "google_monitoring_alert_policy" "desk_fallback_share" {
  count        = var.desk_router_alerts ? 1 : 0
  display_name = "Desk router: fallback share above 1% for a tenant"
  combiner     = "OR"
  conditions {
    display_name = "fallback turns / routed turns > 0.01 over the last hour, in an hour of 100 turns or more, for 30 minutes"
    condition_prometheus_query_language {
      query               = local.desk_fallback_query
      duration            = "1800s"
      evaluation_interval = "300s"
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "7200s" }
  documentation {
    content   = "The Desk's router is failing for this tenant: its turns are getting the fallback's direct answer instead of a desk. Read why: gcloud logging read 'jsonPayload.event=\"desk_router_failed\" OR jsonPayload.event=\"desk_router_signal_failed\"' --limit 20. A timeout on every turn is location=global or the model; an error is the code. The desk rows' fallback_reason says which (gcloud logging read 'jsonPayload.event=\"desk\" AND jsonPayload.method=\"fallback\"' --format='value(jsonPayload.tenant,jsonPayload.fallback_reason)'). Lesson 10.4."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_router]
}

# The arbiter's share: L2 is a flash call on top of flash-lite, so a share above its cap is the router's cost and
# latency drifting, or the dev set's thresholds not fitting this tenant's questions.
resource "google_monitoring_alert_policy" "desk_l2_share" {
  count        = var.desk_router_alerts ? 1 : 0
  display_name = "Desk router: L2 share above its 15% cap for a tenant"
  combiner     = "OR"
  conditions {
    display_name = "turns sent to the arbiter / routed turns > 0.15 over the last hour, in an hour of 100 turns or more, for an hour"
    condition_prometheus_query_language {
      query               = local.desk_l2_query
      duration            = "3600s"
      evaluation_interval = "300s"
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "7200s" }
  documentation {
    content   = "More than 15% of this tenant's routed turns went to the arbiter (L2). desk_daily shows the share by desk and day (make desk-views, then bq query on documind_observability.desk_daily). The thresholds that decide it, TAU_OOS and ACCEPT_VOTES, are swept by make route-calibrate; a change to them is a reviewed commit to services/chat/desk_router.py. Lesson 10.4."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_router]
}

resource "google_monitoring_alert_policy" "desk_clarify_oos_trend" {
  count        = var.desk_router_alerts ? 1 : 0
  display_name = "Desk router: clarify or out_of_scope up more than 5 points week on week"
  combiner     = "OR"
  conditions {
    display_name = "a route's share of the last 7 days minus its share of the 7 before > 0.05"
    condition_prometheus_query_language {
      query               = local.desk_trend_query
      duration            = "0s"
      evaluation_interval = "3600s"
    }
  }
  notification_channels = local.alert_channel_ids
  documentation {
    content   = "A larger share of this tenant's questions is being asked back (clarify) or turned away (out_of_scope) than a week ago. desk_daily shows which desk and which day (make desk-views, then bq query on documind_observability.desk_daily): a new kind of question the exemplars do not cover is make route-index after people add dev rows; a desk switched off or not covered is make desk TENANT= and make doc-types TENANT=. Lesson 10.4."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_router]
}

# ---------------------------------------------------------------------------------------------
# The case queue's clock: the hourly overdue job (desk.tf, services/chat/desk_overdue.py) logs one case_overdue line
# per case due within 24 hours and still unacknowledged, and per breached case: the id, the queue and due_at, nothing
# else. The job writes to Cloud Logging; make cases-overdue runs the same scan from your shell and prints to it, so
# only the job's run (hourly, or gcloud run jobs execute documind-cases-overdue) can fire this alert. The line carries
# no tenant, so the incident names a queue, a state and a count.
resource "google_logging_metric" "case_overdue" {
  name    = "documind/case_overdue"
  project = var.project_id
  filter  = <<EOT
    resource.type="cloud_run_job"
    resource.labels.job_name="documind-cases-overdue"
    jsonPayload.event="case_overdue"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "queue"
      value_type  = "STRING"
      description = "The case's queue (payroll, people, a clause prefix's queue); sensitive for posh, grievance and privacy_request"
    }
    labels {
      key         = "state"
      value_type  = "STRING"
      description = "due (within 24 hours of due_at, unacknowledged) | breached (past due_at, not resolved)"
    }
  }
  label_extractors = {
    queue = "EXTRACT(jsonPayload.queue)"
    state = "EXTRACT(jsonPayload.state)"
  }
}

resource "google_monitoring_alert_policy" "case_overdue" {
  display_name = "Desk case queue: a case due within 24 hours and unacknowledged, or breached"
  combiner     = "OR"
  conditions {
    display_name = "case_overdue lines from the last hourly scan, per queue and state"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_job\" AND metric.type=\"logging.googleapis.com/user/documind/case_overdue\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "3600s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["metric.label.queue", "metric.label.state"]
      }
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "7200s" }
  documentation {
    content   = "A case in this queue is due within 24 hours and nobody has acknowledged it, or it is past its due date. The alert names the queue and a count only (an hour can hold two scans, so one case may count twice); make cases TENANT=<tenant> lists each tenant's open cases with their ids, queues and due dates, and the queue's own members see the case in their Desk inbox. A sensitive queue is a POSH, grievance or privacy case: tell its committee or contact, never the wider team. The incident closes on its own once the hourly scans stop logging this queue and state. Lesson 5.6."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.case_overdue]
}

# ---------------------------------------------------------------------------------------------
# A registered document arrived at a version nobody reviewed (shared/doc_types.py assign(), workshop lesson 10.4): it
# is indexed as "unknown", and the desks that filter on a class do not see it until an operator re-pins it. The hook
# runs on both lanes, the push worker and the batch job, so a PDF the push lane hands to the batch lane logs twice;
# any line is worth a look, so the count's doubling does not matter here.
resource "google_logging_metric" "doc_type_pin_miss" {
  name    = "documind/doc_type_pin_miss"
  project = var.project_id
  filter  = <<EOT
    ((resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest") OR
     (resource.type="cloud_run_job" AND resource.labels.job_name="documind-ingest-batch"))
    jsonPayload.event="doc_type_pin_miss"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "tenant"
      value_type  = "STRING"
      description = "Tenant the object belonged to"
    }
  }
  label_extractors = {
    tenant = "EXTRACT(jsonPayload.tenant)"
  }
}

resource "google_monitoring_alert_policy" "doc_type_pin_miss" {
  display_name = "A registered document arrived at a version nobody reviewed"
  combiner     = "OR"
  conditions {
    display_name = "a doc_type_pin_miss line from the ingest worker in the last ten minutes"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/user/documind/doc_type_pin_miss\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "600s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["metric.label.tenant"]
      }
    }
  }
  conditions {
    display_name = "a doc_type_pin_miss line from the batch job in the last ten minutes"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_job\" AND metric.type=\"logging.googleapis.com/user/documind/doc_type_pin_miss\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "600s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["metric.label.tenant"]
      }
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "1800s" }
  documentation {
    content   = "A new version of a document the registry names arrived, and its pin is still the old version, so it is indexed as unknown and the handbook and statute desks refuse rather than quote it. Read which: gcloud logging read 'jsonPayload.event=\"doc_type_pin_miss\"' --limit 5. Read the new version; if it is right, make doc-types TENANT=<tenant> FOLLOW=<name> APPLY=1. Lesson 10.4."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.doc_type_pin_miss]
}

# ---------------------------------------------------------------------------------------------
# A caller that tried to speak for someone else on the Desk and was refused. The Google Chat door's delegate checks
# (services/chat/delegation.py, which desk.py's _principal() calls) write desk_delegation_refused with the caller and
# no principal; make smoke-gchat refuses two such calls on purpose, and nothing else should. Every
# such line is worth a page: only the bridge's account may delegate, and nobody may mint as it. The metric counts lines
# and carries no label, so the incident names the service and a count, never the caller.
resource "google_logging_metric" "desk_delegation_refused" {
  name    = "documind/desk_delegation_refused"
  project = var.project_id
  filter  = <<EOT
    resource.type="cloud_run_revision"
    jsonPayload.event="desk_delegation_refused"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "desk_delegation_refused" {
  display_name = "Desk: a delegation was refused"
  combiner     = "OR"
  conditions {
    display_name = "a desk_delegation_refused line in the last five minutes"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/user/documind/desk_delegation_refused\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.service_name"]
      }
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "1800s" }
  documentation {
    content   = "Something asked the Desk to act for a person and was refused: a caller that is not the Google Chat bridge, a header where none belongs, or a route that cannot be delegated. Read the lines: gcloud logging read 'jsonPayload.event=\"desk_delegation_refused\"' --limit 20 (caller, reason, path). The Google Chat door's smoke refuses two such calls on purpose; anything else is worth asking: who can mint tokens as that caller (tools/check_authz.py), and whether the bridge's account was granted to anyone."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_delegation_refused]
}

# ---------------------------------------------------------------------------------------------
# The hard gate's model check (shared/desk_recall.py, workshop lesson 5.6), for a tenant whose desk_gate is on. Both
# doors log one desk_gate_check line per check - the chat service's POST /v1/chat (surface chat), rag-api's /v1/query
# and /v1/stream (query, stream) - with its outcome: case, none or error. An error (a timeout, an exception, an answer
# outside the schema, a door with no model client) is no class: the turn goes on with the rules alone, the person is
# told nothing, and the line, at WARNING, is the only trace. The line carries no question and no person.
resource "google_logging_metric" "desk_gate_check" {
  name    = "documind/desk_gate_check"
  project = var.project_id
  filter  = <<EOT
    resource.type="cloud_run_revision"
    (resource.labels.service_name="documind-chat" OR resource.labels.service_name="documind-api")
    jsonPayload.event="desk_gate_check"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "tenant"
      value_type  = "STRING"
      description = "Tenant the question belonged to"
    }
    labels {
      key         = "outcome"
      value_type  = "STRING"
      description = "case (the check found a gate class) | none | error (no class: the rules alone decided)"
    }
  }
  label_extractors = {
    tenant  = "EXTRACT(jsonPayload.tenant)"
    outcome = "EXTRACT(jsonPayload.outcome)"
  }
}

# The failed share, per tenant: failed checks over all checks in the last 30 minutes, paging only in 30 minutes of 20
# checks or more, so a timeout or two among a handful of questions on a quiet lane is not a page. PromQL, as the
# router's shares are, so that it can carry its floor; the metric is desk_gate_check above, as PromQL names it.
locals {
  desk_gate_check_promql = "logging_googleapis_com:user_documind_desk_gate_check{monitored_resource=\"cloud_run_revision\"}"
  desk_gate_error_promql = "logging_googleapis_com:user_documind_desk_gate_check{monitored_resource=\"cloud_run_revision\",outcome=\"error\"}"
  desk_gate_error_query = join("\n", [
    "sum by (tenant) (increase(${local.desk_gate_error_promql}[30m]))",
    "  / on (tenant)",
    "sum by (tenant) (increase(${local.desk_gate_check_promql}[30m]))",
    "> 0.2",
    "and on (tenant) sum by (tenant) (increase(${local.desk_gate_check_promql}[30m])) >= 20",
  ])
}

resource "google_monitoring_alert_policy" "desk_gate_error_share" {
  count        = var.desk_gate_alerts ? 1 : 0
  display_name = "Desk gate check: failed share above 20% for a tenant"
  combiner     = "OR"
  conditions {
    display_name = "failed checks / checks > 0.2 over the last 30 minutes, in 30 minutes of 20 checks or more"
    condition_prometheus_query_language {
      query               = local.desk_gate_error_query
      duration            = "0s"
      evaluation_interval = "300s"
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "7200s" }
  documentation {
    content   = "The Desk's model check is failing for this tenant: more than a fifth of its checks in the last 30 minutes ended in error, and each of those questions was gated by the rules alone, with nothing said to the person. Read why: gcloud logging read 'jsonPayload.event=\"desk_gate_check\" AND jsonPayload.outcome=\"error\"' --limit 20 --format='value(jsonPayload.tenant,jsonPayload.surface,jsonPayload.error,jsonPayload.ms)'. error is the exception's class; parse is an answer outside the schema; unavailable is a door with no model client; ms near 3000 is the check's own timeout (CHECK_TIMEOUT_S in shared/desk_recall.py), which each such question waited out. While it cannot work, make desk TENANT=<tenant> DESK_GATE=rules stops the calls; the rules run either way. Lesson 5.6."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_gate_check]
}

# The read behind the check: each door learns which tenants are on from one bounded query of tenant_settings, at most
# once a minute (desk_recall.OnTenants). A failed read keeps the last set, and a process that has never read one checks
# no tenant, so its questions get the rules alone and it logs no desk_gate_check line: the share above cannot see this.
# The door logs desk_check_tenants_unread once per failure streak instead, so one line may stand for many turns, and
# every line is worth a look. No label: the incident names the service and a count.
resource "google_logging_metric" "desk_check_tenants_unread" {
  name    = "documind/desk_check_tenants_unread"
  project = var.project_id
  filter  = <<EOT
    resource.type="cloud_run_revision"
    (resource.labels.service_name="documind-chat" OR resource.labels.service_name="documind-api")
    jsonPayload.event="desk_check_tenants_unread"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "desk_check_tenants_unread" {
  display_name = "Desk gate check: a door could not read which tenants are on"
  combiner     = "OR"
  conditions {
    display_name = "a desk_check_tenants_unread line in the last ten minutes"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/user/documind/desk_check_tenants_unread\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "600s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.service_name"]
      }
    }
  }
  notification_channels = local.alert_channel_ids
  alert_strategy { auto_close = "1800s" }
  documentation {
    content   = "A door of the Desk could not read which tenants have desk_gate on (one query of tenant_settings, one attempt of 2 s). Until a read works, that process keeps the last set it read, and one that never read a set runs the model check for nobody: a tenant that is on may be getting the rules alone. The line is logged once per failure streak, not per turn. Read it: gcloud logging read 'jsonPayload.event=\"desk_check_tenants_unread\"' --limit 20 (surface, error). Then see whether desk_gate_check lines are back for the tenants that are on: gcloud logging read 'jsonPayload.event=\"desk_gate_check\"' --limit 5. A read that keeps failing is Firestore or the service account's access to it. Lesson 5.6."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.desk_check_tenants_unread]
}
