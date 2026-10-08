# Course plan v3 - eight modules over the DocuMind kit (21 September 2026)

Replaces the 13-module / 68-lesson v2.0 layout, which was deleted from this checkout on 21 September 2026. The kit under `code/` (formerly `deploy/`) is now the source of truth: lessons clone it, open it and run it; they do not carry copies of it. `course-manifest.json` carries the same numbering.

**Lesson page format, every lesson:** 1 Architecture and the database (Firestore) design, including how an update is handled | 2 Component diagram | 3 Tech stack | 4 Flow diagram - how it connects to the whole system | 5 Code summary | 6 Code explanation.

Deployment and RAG run to six lessons because that is how much code sits under them; the rest are four or five. Modules 2, 3 and 8 are make-driven (Terraform, gcloud, Docker) and run from Cloud Shell or a workstation rather than Colab.


## Module 1 - Set Up

*By the end: A billable project, the code on your machine, and DocuMind answering a question on your laptop for Rs 0.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 1.1 | **Your Google Cloud project** | Create a throwaway project, link billing, turn on the APIs, log in once (ADC). | `make apis`, `commands/infrastructure.py prepare`, `INFRASTRUCTURE.md` |
| 1.2 | **The code on your machine** | Clone the learner repo, install Python, Terraform, gcloud and Docker, and tour the folders: services/, shared/, terraform/, evals/, smoke/. | `README.md`, `INDEX.md`, `commands/session-restart.sh (its tool checks)`, `shared/requirements.txt` |
| 1.3 | **The documents DocuMind reads** | Three companies (acme, zeta, globex), thirteen real Indian Acts, invented PANs, and the 65 test questions. | `evals/README.md`, `evals/fetch_real.py`, `evals/build_corpus.py`, `evals/build_golden.py`, `evals/golden.jsonl`, `evals/required.json` |
| 1.4 | **Run DocuMind for Rs 0** | Ollama + Chroma on the laptop; ask 'What is the notice period?'. | `make chat-local`, `shared/profile.py`, `shared/local_corpus.py`, `services/chat/requirements-local.txt` |
| 1.5 | **The health check before you spend money** | Ten offline checks; break one on purpose and watch it fail. | `make dryrun`, `validate.py`, `evals/run_eval.py (offline)`, `.github/workflows/documind-dryrun.yml` |

## Module 2 - Deployment

*By the end: The whole of DocuMind live on Cloud Run behind a login, with a budget, alarms, a night switch and a rollback.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 2.1 | **Terraform in plain words** | Plan, review, apply; where the state lives. | `terraform/backend.tf`, `terraform/variables.tf`, `commands/infrastructure.py plan / check / apply`, `make plan` |
| 2.2 | **Who may do what: accounts, roles, secrets** | One service account per service, the smallest roles, secrets never in env vars. | `terraform/sa.tf`, `terraform/secrets.tf`, `terraform/org_policy.tf`, `make secrets` |
| 2.3 | **Databases, buckets and indexes** | What Terraform creates and why each one exists. | `terraform/firestore.tf`, `terraform/firestore_indexes.tf`, `terraform/vector.tf`, `terraform/storage.tf`, `terraform/docai.tf`, `terraform/cloudsql.tf`, `terraform/spanner.tf`, `terraform/registry.tf`, `terraform/network.tf` |
| 2.4 | **Seven services on Cloud Run, behind a login** | Build the images, deploy, put IAP in front, add people to a tenant, run the smoke test. | `cloudbuild.yaml`, `make build`, `make deploy-services`, `commands/lesson-12.*.sh`, `shared/iap.py`, `shared/tenancy.py`, `make roster`, `make up`, `make smoke` |
| 2.5 | **Watch it, pay for it, switch it off** | The admin console, usage in rupees, budget and alerts, the 23:00 job, make down. | `services/admin/`, `evals/usage_rows.py (make usage)`, `terraform/budget.tf`, `terraform/alerts.tf`, `terraform/sink.tf`, `terraform/off.tf`, `make off`, `make down` |
| 2.6 | **Ship without keys, roll back in two minutes** | GitHub to Google Cloud with no secret, an eval gate, promote a candidate by name, roll back. | `terraform/wif.tf`, `.github/workflows/documind-cd.yml`, `terraform/clouddeploy.tf`, `make release-candidate`, `make promote`, `make rollback` |

## Module 3 - RAG

*By the end: The learner can follow a document in and a question out, name every table, and change what answers with a setting.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 3.1 | **Flow diagram** | Two journeys drawn end to end: upload to index, question to answer, each box a service. | `README.md`, `services/*`, `shared/documind_tools.py (retrieve())` |
| 3.2 | **Database schema** | Firestore: chunks, documents, sources, ledger, tenants/{id}/members, tenant_settings, tenant_caches, answer_cache, budget, graph_nodes / graph_edges, ingest_batch, dlp_findings, audit_index. BigQuery: documind_observability, rag_data (chunk_source, chunk_metadata, ingest_events, index_feed, tenant_daily). Spanner: GraphNode / GraphEdge. Plus the Vector Search index, Cloud SQL and the five buckets. | `INDEXING.md section 4`, `services/ingest/contracts.py`, `services/ingest/indexer.py`, `terraform/firestore_indexes.tf`, `terraform/dataplex.tf`, `terraform/sink.tf`, `terraform/spanner.tf`, `terraform/sql/*.sql` |
| 3.3 | **Ingesting** | Upload, event, worker, Document AI, DLP scan, chunk, embed, store. New versions, undo, big files, the nightly reconcile. | `terraform/eventarc.tf`, `services/ingest/main.py`, `services/ingest/contracts.py`, `services/ingest/parser.py`, `shared/pii.py`, `services/ingest/idempotency.py`, `services/ingest/indexer.py`, `services/ingest/batch.py`, `services/ingest/reconcile.py`, `make ingest-one / reindex / retire / reconcile / poison / dlq` |
| 3.4 | **Retrieval** | Embed the question; four places to search (Vector Search, Firestore, RAG Engine, Vertex AI Search); hybrid; rerank; the knowledge graph in front; measure with the ablation. | `services/rag-api/retriever.py`, `services/rag-api/hybrid.py`, `shared/sparse_encoder.py`, `shared/documind_graph.py`, `services/ingest/graph.py`, `services/ingest/managed.py`, `services/rag-api/config.py`, `evals/ablate.py`, `make tenant-backend`, `make graph` |
| 3.5 | **Generator** | Pack chunks into a token budget, ask Gemini for JSON, turn [Source N] into citations, stream it, guard both sides with Model Armor, price it in rupees. | `services/rag-api/generator.py`, `services/rag-api/context_budget.py`, `shared/documind_schemas.py`, `services/rag-api/cost.py`, `services/rag-api/guard.py`, `terraform/model_armor.tf`, `services/rag-api/main.py (/v1/query, /v1/stream)`, `services/frontend/chat.py` |
| 3.6 | **Cache and cost control** | The context cache, the semantic answer cache, the router, the budget breaker. | `services/rag-api/cache_manager.py`, `services/rag-api/cache_admin.py`, `services/rag-api/semantic_cache.py`, `evals/cache_threshold.py`, `services/rag-api/router.py`, `services/rag-api/breakers.py`, `services/rag-api/budget.py`, `make cache` |

## Module 4 - MCP

*By the end: DocuMind's retrieve() is a tool any agent can call over the network, and it refuses the wrong tenant.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 4.1 | **What MCP is, and DocuMind's one tool** | Why every surface shares one retrieve(). | `shared/documind_tools.py`, `services/chat/tools.py`, `tools/check_one_retrieval.py` |
| 4.2 | **Build the server with FastMCP** | Run it on the laptop against the Rs 0 lane. | `services/mcp/server.py` |
| 4.3 | **Put it on Cloud Run behind IAM** | Deploy, call it with an ID token, smoke it. | `commands/lesson-7.2.sh`, `services/mcp/Dockerfile`, `make smoke-mcp`, `smoke/smoke_mcp.py` |
| 4.4 | **Connect a client** | An ADK agent (and Claude Desktop) calls the remote tool; see what the server refuses. | `services/agent/agent.py (_mcp_headers)`, `smoke/smoke_mcp.py refusal checks` |

## Module 5 - Multimodal

*By the end: A chart, a scanned page and a video go through the same pipeline, and answers cite the figure or the second of the clip.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 5.1 | **Pictures and videos as documents** | Draw the figure, render the invoice and page 30 of an Act, synthesise the town-hall video. | `evals/build_media.py`, `make media` |
| 5.2 | **Ingest an image or a video** | Gemini describes it, the caption or the segments become chunks, pixels are DLP-scanned first. | `services/ingest/main.py (media path)`, `shared/pii.py (inspect_image)`, `services/ingest/contracts.py` |
| 5.3 | **Answers that cite a figure or a clip** | kind, media_url, start, end; the UI shows the figure inline and the video at its second. | `shared/documind_schemas.py`, `services/frontend/citations.py`, `the mm- rows in evals/golden.jsonl`, `evals/run_eval.py (media_kind_rate)` |
| 5.4 | **Media Studio and voice** | Generate an image, upload a 40 MB video by signed URL, read the answer aloud. | `services/rag-api/media.py`, `services/frontend/studio.py`, `services/frontend/voice.py`, `terraform/storage.tf`, `make smoke-media` |

## Module 6 - Fine-tuning

*By the end: A model tuned on DocuMind's own documents, tested against the golden set and judged against the live one.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 6.1 | **Training data from your own documents** | One question and answer per chunk, PII-scanned, test questions kept out, frozen with a manifest. | `evals/make_trainset.py`, `evals/sft/`, `make trainset` |
| 6.2 | **Tune Gemini on Vertex AI** | Managed SFT; the tuned endpoint becomes a setting on the API. | `evals/tune.py`, `make tune`, `services/rag-api/generator.py (endpoint path, GENERATOR_LOCATION, RAG_MODEL_BASE)` |
| 6.3 | **Tune a small open model into a GGUF** | The chat-format file, a Modelfile from the tokenizer. Feeds Module 8. | `evals/sft/*.chat.jsonl`, `services/slm/make_modelfile.py`, `services/slm/Modelfile` |
| 6.4 | **Test it against the golden set** | A no-traffic candidate revision, the live gate's nine thresholds and fifteen required rows. | `make candidate`, `make eval-live`, `evals/run_eval.py (live)` |
| 6.5 | **Let a judge compare old and new** | Vertex AI Evaluation, pairwise, one run per commit; price the difference. | `evals/judge.py`, `make judge`, `make usage` |

## Module 7 - Agents

*By the end: Four agent brains over the one tool, memory that survives a restart, and an agent that talks to another agent.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 7.1 | **The model calls a tool: the direct loop** | Function calling by hand. | `services/chat/brains.py (DirectBrain)`, `services/chat/tools.py` |
| 7.2 | **LangChain and LangGraph brains** | A graph with a refuse node and a summary step. | `services/chat/brains.py (LangChainBrain, LangGraphBrain)`, `shared/profile.py` |
| 7.3 | **Memory that survives a restart** | A checkpointer in Cloud SQL, set up by a one-off job. | `services/chat/migrate.py`, `terraform/cloudsql.tf`, `make smoke-chat` |
| 7.4 | **The ADK brain and the chat service** | One /v1/chat, pick the brain per request, the UI's brain radio. | `services/chat/brains.py (AdkBrain)`, `services/chat/agent.py`, `commands/lesson-12.8.sh` |
| 7.5 | **Agent to agent: A2A** | A peer agent that knows DocuMind only through MCP. | `services/agent/agent.py`, `commands/lesson-8.4.sh`, `make smoke-agent` |

## Module 8 - vLLM & SLM

*By the end: The same API answers from Gemini, from your own small model on a GPU, or from vLLM - and the GPU is off by 23:00.*

| # | Lesson | What the learner does | Code |
|---|---|---|---|
| 8.1 | **One door for every model: the LiteLLM gateway** | Routes, a PII guardrail, cost on every reply. | `services/litellm/`, `terraform/gateway.tf`, `make deploy-gateway`, `make smoke-gateway` |
| 8.2 | **Your small model on a Cloud Run GPU** | Ollama on an L4, scale to zero, the cold start measured. | `services/slm/`, `make deploy-slm`, `make smoke-slm`, `make slm-off` |
| 8.3 | **vLLM with your own FastAPI** | Chat completions, /classify, /extract, rate limits, a 13 GB image. | `services/gemma-vllm/`, `make build-vllm`, `make deploy-vllm` |
| 8.4 | **Cloud Run or GKE?** | The duty-cycle sum: Rs 65,514 a month always-on vs Rs 0 idle, break-even about 74 percent. | `terraform/gke.tf`, `gke/vllm-deployment.yaml`, `gke/README.md`, `make gke-up / gke-down` |
| 8.5 | **Compare them honestly and cap the bill** | Same questions, every backend; a quota cap, an alarm for a GPU left warm. | `services/slm/compare_backends.py (make compare)`, `services/slm/gpu_quota.py (make gpu-cap)`, `terraform/alerts.tf`, `terraform/off.tf` |

## Still to do before authoring

1. `deploy/` to `code/`: about 1,700 references in 53 files (workflows, tools/, docs) still name the old folder, and the kit's own docs do too.
2. The kit's extractor model (`code/extract_documind.py`, `INDEX.md`, `tools/deploy_index.py`, `tools/check_contract.py`, `tools/check_auth_wiring.py`) assumed the old notebooks owned the code as heredocs. Retire or re-point them.
3. `CLAUDE.md` and `README.md` still describe the v2.0 layout.
4. The one-shape `make up` has not run live end to end (code/README.md). Rehearse Module 2 on a throwaway project before Modules 3-8 are written against its outputs.

