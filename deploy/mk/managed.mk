# ---------- The managed peer (the v5 course's Module 10): the A2A peer on Vertex AI Agent Engine, lesson 10.9 ----------
# Included by the Makefile (`include mk/*.mk`): PROJECT, REGION, TENANT and PY are its variables; Q, HOST, ASKER, JSON,
# WAIT, SINCE, KEEP, DELETE, REDEPLOY and DRY_RUN are given on the command line. Every target runs commands/managed_peer.py
# in ~/managed-peer-venv (commands/managed-peer.sh), so each also runs without make, from deploy/:
#     bash commands/managed-peer.sh up --project <id> --region <region> --services-region <region>
# DRY_RUN=1 runs it with the kit's own python instead: every call printed and none made, no credential, Rs 0. No
# change to services/agent and no Terraform: the peer's own files are staged as they are, and it runs as
# documind-agent-sa, the Cloud Run peer's account (the lesson plan's decision 13).

# Where the managed peer runs: beside its Cloud Run twin, in REGION (asia-south1 on the course's lane). Whether Agent
# Engine takes asia-south1 is fact 1 of the author's dated probe; MANAGED_PEER_REGION=us-central1 deploys it there.
MANAGED_PEER_REGION ?= $(REGION)
# The role Agent Engine's service agent needs on documind-agent-sa to run as it (fact 2); up grants it, down takes it back.
MANAGED_PEER_GRANT_ROLE ?= roles/iam.serviceAccountTokenCreator
# empty: google-cloud-aiplatform unpinned, in the venv and in the runtime's image, as ADK's deploy leaves it (fact 11)
AIPLATFORM_PIN ?=
MANAGED_PEER = $(if $(DRY_RUN),$(PY) commands/managed_peer.py,PY=$(PY) AIPLATFORM_PIN=$(AIPLATFORM_PIN) bash commands/managed-peer.sh)
MANAGED_PEER_FLAGS = --project $(or $(PROJECT),documind-ai-YOUR-ID) --region $(MANAGED_PEER_REGION) \
  --services-region $(REGION) --grant-role $(MANAGED_PEER_GRANT_ROLE) $(if $(AIPLATFORM_PIN),--aiplatform-pin $(AIPLATFORM_PIN),) \
  $(if $(DRY_RUN),--dry-run,) $(if $(JSON),--json,) $(if $(ASKER),--as $(ASKER),) $(if $(WAIT),--wait $(WAIT),)

# The peer deployed to Agent Engine: services/agent/agent.py and its requirements.txt staged byte for byte, with
# commands/managed_peer_agent.py as the package's __init__.py (the peer's own agent, its model on location global),
# through google-adk's own deploy into an instance named documind-managed-peer, as documind-agent-sa, with MCP_URL,
# AGENT_MODEL and the cap of 12 model calls (ADK_MAX_LLM_CALLS), telemetry on and message content off, min_instances 0
# and max_instances 1. The service agent's grant on documind-agent-sa first. 10 to 20 minutes, most of it the image's
# build. It prints what bills while the instance exists - nothing here states Agent Engine's price (fact 12) - and who
# may call it: every roles/aiplatform.user holder on the project, unless the instance has an IAM policy of its own (fact
# 8). Run again, it does nothing unless REDEPLOY=1.
managed-peer-up: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) up $(MANAGED_PEER_FLAGS) $(if $(REDEPLOY),--redeploy,)

# One question through the instance's query API (streamQuery), as documind-ui-sa (ASKER=me asks as your own
# credentials): TENANT=acme (the default) is answered through documind-mcp, any other tenant is refused by the roster,
# asked as make smoke-agent's check 4 asks. Q= asks your own question. HOST=cloudrun asks the Cloud Run peer the same
# way, over A2A. Each run appends its record to evals/reports/managed-peer/runs.ndjson; JSON=1 prints it. About two
# gemini-3.6-flash calls of the peer's, and rag-api's answer inside retrieve.
managed-peer-ask: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) ask $(MANAGED_PEER_FLAGS) --tenant $(TENANT) $(if $(Q),--question "$(Q)",) $(if $(HOST),--host $(HOST),)

# What the last ask left: the spans in Cloud Trace, waited for up to WAIT seconds (120 by default), with none of the
# question's words in them; the rows documind-mcp logged, whose caller is documind-agent-sa; and the runtime's own
# line, with its GOOGLE_CLOUD_LOCATION and the versions its image installed. SINCE=<minutes> reads that window instead.
# Reads only.
managed-peer-trace: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) trace $(MANAGED_PEER_FLAGS) $(if $(SINCE),--since $(SINCE),)

# The lesson's proof: acme answered (twice: the first call and a warm one), zeta refused by the roster, the outsider
# refused by the platform, documind-mcp's rows naming documind-agent-sa, the spans with message content off, the
# managed sessions with another user refused by ADK's session service, and the runtime's own settings line; then the
# Cloud Run peer asked the same three questions, and the comparison table from the records. With no managed peer it
# deploys one first, and deletes it at the end unless KEEP=1. Exit 1 when a check fails.
managed-peer-smoke: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) smoke $(MANAGED_PEER_FLAGS) $(if $(KEEP),--keep,)

# The instance's managed sessions, by user; the newest session, whoever's, read event by event; the same session read
# as another user, which ADK's session service refuses - a check in the client, after the read (fact 9) - and the API's
# own read, which names no user. DELETE=1 deletes them (down's delete takes them anyway).
managed-peer-sessions: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) sessions $(MANAGED_PEER_FLAGS) $(if $(DELETE),--delete,)

# Torn down: every documind-managed-peer* instance in the regions deleted by name, its sessions with it, and read back
# gone; the service agent's grant taken back when up added it. Says what it deleted; run again, it says there is nothing
# to delete. Exit 4, with the delete command, when something could not be deleted.
managed-peer-down: $(if $(DRY_RUN),,guard-project)
	@$(MANAGED_PEER) down $(MANAGED_PEER_FLAGS)
