resource "google_bigquery_dataset" "observability" {
  dataset_id                  = "documind_observability"
  location                    = var.india_region
  description                 = "API structured logs, DLP findings, tenant rollups"
  default_table_expiration_ms = 7776000000 # 90 days for raw logs
  delete_contents_on_destroy  = false
}

# The DocuMind Desk's rows ride the same sink (workshop lessons 5.6 and 10.4): desk (POST /v1/desk, and the eval's
# POST /v1/route as surface "route"), passages (rag-api's search-only answers), desk_shadow (a /v1/chat turn the
# router decided in shadow) and desk_gate (a question a door answered). None carries question text, and a posh,
# grievance or privacy row carries no person. No sensitive row is copied beside a row of the same turn that names the
# person, so two kinds stay in Cloud Logging only:
# - a sensitive desk_shadow row: the brain answered that turn too, and its chat row carries the user;
# - rag-api's desk_gate rows: that door also answers the search words a brain wrote inside a chat turn.
# The chat door answers a gated turn itself and no brain runs, so its desk_gate rows have no chat row, and are copied.
# The sink copies only entries logged after the apply; terraform/sql/desk_daily.sql (make desk-views) reads the desk
# rows once they have landed.
resource "google_logging_project_sink" "api_to_bq" {
  name                   = "documind-api-to-bq"
  destination            = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.observability.dataset_id}"
  filter                 = <<EOT
    resource.type = "cloud_run_revision"
    (resource.labels.service_name = "documind-api" OR resource.labels.service_name = "documind-chat")
    (jsonPayload.event = "query" OR jsonPayload.event = "stream" OR jsonPayload.event = "chat" OR
     jsonPayload.event = "desk" OR jsonPayload.event = "passages" OR
     (jsonPayload.event = "desk_shadow" AND NOT jsonPayload.case_type = "sensitive") OR
     (jsonPayload.event = "desk_gate" AND resource.labels.service_name = "documind-chat"))
  EOT
  unique_writer_identity = true
  bigquery_options { use_partitioned_tables = true }
}

# Sink identity needs BQ data editor
resource "google_bigquery_dataset_iam_member" "sink_writer" {
  dataset_id = google_bigquery_dataset.observability.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.api_to_bq.writer_identity
}
