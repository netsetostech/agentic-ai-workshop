# The managed stores (P9.1, 13 September 2026): what lessons 4.3 and 4.4 build, declared per tenant for the mirror
# (services/ingest/managed.py, MANAGED_MIRROR) and the rag_engine / vertex_search retrieval backends (P9.4, P9.5).
# One store per tenant - RAG Engine has no metadata filter and Vertex AI Search's needs a schema, so isolation is
# structural (the plan's D2). A Vertex AI Search data store is a Terraform resource and is declared here, in
# `global` (the only home a generic data store has), behind MANAGED_SEARCH=true. A RAG Engine corpus is not a
# Terraform resource: `make rag-corpus TENANT=` creates one idempotently by display name, in us-central1 (the
# only region serverless corpora have), after `make rag-engine-enable` has switched the project to serverless
# mode once (4.3's one-time prep). Neither store is inside India (us-central1, global), so a tenant's text reaches
# them only when its data_region policy says `any` (tenant_settings/{tenant}, make tenant-policy; managed.py asks
# per document and audits every copy) - the `tenants` variable lists the tenants whose policy is `any`.
variable "managed_search" {
  type        = bool
  default     = false
  description = "declare a Vertex AI Search data store per tenant (global) for the vertex_search mirror and backend"
}

variable "managed_mirror" {
  type        = string
  default     = "off"
  description = "MANAGED_MIRROR for the batch and reconcile jobs, the same value make deploy-services hands the worker: off | rag_engine | vertex_search | both"
  validation {
    condition     = contains(["off", "rag_engine", "vertex_search", "both"], var.managed_mirror)
    error_message = "managed_mirror must be off, rag_engine, vertex_search or both."
  }
}

# RAG Engine's serverless corpus is backed by a Vector Search collection. The
# RAG service agent (not the operator, ingest SA, or generic Vertex AI agent)
# needs its Google-defined service-agent role before creating that collection.
# Keep this IAM prerequisite in Terraform so fresh projects do not depend on
# the timing of Google's automatic first-use IAM grants.
# https://docs.cloud.google.com/iam/docs/roles-permissions/vectorsearch
resource "google_project_service" "managed_rag" {
  for_each = contains(["rag_engine", "both"], var.managed_mirror) ? toset([
    "aiplatform.googleapis.com",
    "vectorsearch.googleapis.com",
  ]) : toset([])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Generate Google's service identities; do not create a user-managed account
# with a similar name. The RAG identity uses the project NUMBER in its address.
resource "google_project_service_identity" "managed_rag" {
  count    = contains(["rag_engine", "both"], var.managed_mirror) ? 1 : 0
  provider = google-beta
  project  = var.project_id
  service  = "aiplatform.googleapis.com"

  depends_on = [google_project_service.managed_rag]
}

resource "google_project_iam_member" "managed_rag_service_agent" {
  count   = contains(["rag_engine", "both"], var.managed_mirror) ? 1 : 0
  project = var.project_id
  role    = "roles/aiplatform.ragServiceAgent"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-vertex-rag.iam.gserviceaccount.com"

  depends_on = [google_project_service_identity.managed_rag]
}

variable "tenants" {
  type        = list(string)
  default     = ["acme", "zeta"] # the tenants whose data_region is `any` (make roster): globex's text stays on the kit's rows
  description = "the tenants a managed store is declared for (the `any` tenants; the Makefile's MANAGED_TENANTS names the same); a tenant not listed gets mirror_no_store, never a store created on the fly"
}

locals {
  managed_tenants = var.managed_search ? toset(var.tenants) : toset([])
}

# The data store: unstructured documents with metadata (CONTENT_REQUIRED, GENERIC, search). The worker imports
# each version's text as one Document whose id is the doc_key, so a re-issue replaces and a retirement deletes.
# Declare the API's default digital parser explicitly: refresh returns this immutable configuration even when
# creation omitted it. Leaving it absent would plan replacement of populated stores on the next run.
# P9.5 reads extractive segments, which need no chunk mode. The schema is ours, not the default: the fields the
# mirror writes are indexable so the API's doc_type / kind filters become filter expressions (P9.5).
resource "google_discovery_engine_data_store" "tenant" {
  for_each                     = local.managed_tenants
  location                     = "global"
  data_store_id                = "documind-${each.key}"
  display_name                 = "DocuMind ${each.key}"
  industry_vertical            = "GENERIC"
  content_config               = "CONTENT_REQUIRED"
  solution_types               = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search  = false
  skip_default_schema_creation = true

  document_processing_config {
    default_parsing_config {
      digital_parsing_config {}
    }
  }

  # No prevent_destroy (8 October 2026). A parser or identity change, or managed_search
  # turned off, would plan a delete of the students' indexed documents, and
  # commands/infrastructure.py refuses every delete and replacement on make plan and
  # make up, so none reaches an apply. prevent_destroy refused more than that: Terraform
  # rejected make down's whole destroy over these stores, after the services and the
  # corpora were gone, and every hourly line kept billing. make down is the one target
  # that destroys them. Do not work around the plan check with state rm.
}

# Where the mirror stages each version's text for the import (services/ingest/managed.py, SEARCH_BUCKET), 21 October
# 2026. It was the audit bucket, whose retention policy refuses every delete and overwrite: a retire left the staged
# copy (mirror_failed delete:retired, 403) and a restore could not rewrite it, so the document never came back to the
# data store while the ledger still said it was there. A bucket of its own holds copies only - the record of every
# copy is doc.mirror in the audit bucket - so the worker may replace and delete them, and make down may empty it.
resource "google_storage_bucket" "search" {
  count                       = var.managed_search ? 1 : 0
  name                        = "${var.project_id}-search"
  location                    = var.india_region
  uniform_bucket_level_access = true
  force_destroy               = true
}

# The worker and the batch and reconcile jobs (all documind-ingest-sa) write, replace and delete the staged text.
resource "google_storage_bucket_iam_member" "ingest_search" {
  count  = var.managed_search ? 1 : 0
  bucket = google_storage_bucket.search[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingest.email}"
}

resource "google_discovery_engine_schema" "tenant" {
  for_each      = local.managed_tenants
  location      = google_discovery_engine_data_store.tenant[each.key].location
  data_store_id = google_discovery_engine_data_store.tenant[each.key].data_store_id
  schema_id     = "default_schema"
  json_schema = jsonencode({
    "$schema" = "https://json-schema.org/draft/2020-12/schema"
    type      = "object"
    properties = {
      title          = { type = "string", keyPropertyMapping = "title", retrievable = true }
      tenant_id      = { type = "string", indexable = true, retrievable = true }
      doc_key        = { type = "string", indexable = true, retrievable = true }
      source_uri     = { type = "string", indexable = true, retrievable = true }
      kind           = { type = "string", indexable = true, retrievable = true }
      doc_type       = { type = "string", indexable = true, retrievable = true, dynamicFacetable = true }
      effective_from = { type = "string", indexable = true, retrievable = true }
      generation     = { type = "string", retrievable = true }
      name           = { type = "string", retrievable = true }
    }
  })
}

output "managed_data_stores" {
  value       = { for t, ds in google_discovery_engine_data_store.tenant : t => ds.name }
  description = "the Vertex AI Search data store per tenant, when MANAGED_SEARCH=true"
}
