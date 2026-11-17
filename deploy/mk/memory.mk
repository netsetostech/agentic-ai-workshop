# ---------- Memory (the v5 course's Module 6): a conversation's checkpoints read back, and a turn replayed and forked ----------
# Included by the Makefile (`include mk/*.mk`): PROJECT, REGION, TENANT and PY are its variables, and EMAIL, SESSION, AT,
# EXPORT, FILE, OFFLINE, FORK and DB are given on the command line. Both targets run a script under commands/ in
# ~/graph-venv with the chat image's pins (commands/graph-venv.sh), so they run the same way without make.

# A person's chat threads read back from the lane's Cloud SQL, step by step (workshop lesson 6.8), as the operator, the
# way lesson 6.6's cells reach it: the DSN from Secret Manager into memory, the Cloud SQL Python Connector and pg8000,
# and a session made read only before its first query. EMAIL (default documind-ui-sa, the account the lessons' chat
# cells ask as) lists that person's threads, one row per session; SESSION= decodes one, a row per step: when it was
# written, its source, the brain that wrote it, its next and its messages. AT= prints the messages saved at that step;
# EXPORT=<file> writes the thread for make replay; TENANT=, given on the command line, picks the tenant when a session
# is in two. Reads only, no model call. See commands/thread_read.py.
thread: guard-project
	@PY=$(PY) bash commands/graph-venv.sh --connector commands/thread_read.py --project $(PROJECT) \
	  --email "$(or $(EMAIL),documind-ui-sa@$(PROJECT).iam.gserviceaccount.com)" $(if $(SESSION),--session "$(SESSION)",) \
	  $(if $(AT),--at="$(AT)",) $(if $(EXPORT),--export "$(EXPORT)",) $(if $(filter command line,$(origin TENANT)),--tenant "$(TENANT)",)

# One turn of an exported thread replayed, then forked, on your machine and never on the lane (workshop lesson 6.8): the
# thread copied into a local saver step for step with update_state; the turn re-run from AT (by default where it
# stopped, or its last turn's question) through the kit's LangGraph brain with graph.invoke(None, ...); a fork from the
# turn's input with another question (FORK=); and every branch listed by get_state_history. OFFLINE=1: a script for the
# model, the thread's own searches answered as recorded and any other by the Rs 0 lane over evals/corpus; no network, no
# credential, Rs 0; FILE defaults to evals/threads/cut_off_turn.json, a thread cut off mid-turn. Without it: Gemini on
# location global and your lane's rag-api as documind-ui-sa, on FILE= from make thread EXPORT=: a few model calls,
# priced and printed. DB=<a new file> keeps the copy in SQLite (requirements-local.txt's pin). See commands/thread_replay.py.
replay: $(if $(OFFLINE),,guard-project)
	@if [ -z "$(OFFLINE)" ]; then NUMBER=$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)') || exit 1; \
	  export GOOGLE_CLOUD_PROJECT=$(PROJECT) RAG_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app \
	    DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com; fi; \
	  PY=$(PY) bash commands/graph-venv.sh commands/thread_replay.py $(if $(OFFLINE),--offline,) $(if $(FILE),--file "$(FILE)",) \
	  $(if $(AT),--at="$(AT)",) $(if $(FORK),--fork "$(FORK)",) $(if $(DB),--db "$(DB)",)

# One turn's context by source (workshop lesson 6.1): what rides each model call of a turn - the system prompt, the
# tool declarations as the brain's adapter serialises them, the thread so far, the question, the model's own calls and
# the tool results - each source's tokens and its rupees at list price (shared/prices.py), read where every brain's
# call meets google-genai. BRAIN: langchain (the default), langgraph, adk, direct or desk, with DESK= statute (the
# default), handbook or astar; TURNS=2 or 3 asks earlier questions on one local thread first; TOP_K= sends that top_k
# with every search (the Change-it); Q= another question; TENANT the tenant; JSON=1 prints the turn as one JSON record.
# OFFLINE=1: a scripted model and the Rs 0 lane's retrieve over evals/corpus, every count an estimate, no network, no
# credential, Rs 0. Without it, one real turn on your lane: Gemini on global and rag-api as documind-ui-sa under the
# chat service's limits, a few rupees, then each source counted by count_tokens on global (not billed) and the probe
# printed: does it honour the declarations and the system instruction, and how far is its count from the bill.
context-sources: $(if $(OFFLINE),,guard-project)
	@if [ -z "$(OFFLINE)" ]; then NUMBER=$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)') || exit 1; \
	  export GOOGLE_CLOUD_PROJECT=$(PROJECT) RAG_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app \
	    DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com; fi; \
	  Q="$(Q)"; PY=$(PY) bash commands/graph-venv.sh commands/context_sources.py $(if $(OFFLINE),--offline,) \
	  $(if $(BRAIN),--brain "$(BRAIN)",) $(if $(DESK),--desk "$(DESK)",) $(if $(TURNS),--turns "$(TURNS)",) \
	  $(if $(TOP_K),--top-k "$(TOP_K)",) $${Q:+--question "$$Q"} --tenant "$(TENANT)" $(if $(JSON),--json,)

# A conversation's model calls beside its thread (workshop lesson 6.9): twenty scripted questions in one conversation of
# the kit's LangChain brain (BRAIN=langgraph: its LangGraph brain), and after each turn the thread's size, the context
# the turn's largest call was sent and that call's ceiling: the system prompt and the turn whole, plus the window's
# budget for earlier turns. MODE=windowed, the default, puts the window of services/chat/context_window.py in front of
# the model, which the service does not do; MODE=full sends the whole thread, as every brain does today. HISTORY= is the
# budget (2,000 tokens), TURNS= how many questions, SAVE=<file> every turn as JSON. Offline: a scripted model and the
# Rs 0 lane over evals/corpus, no network, no credential, Rs 0. LIVE=1: each question in two fresh conversations, one
# full and one windowed, with Gemini on location global from your machine, the searches still the Rs 0 lane's: model
# calls only, priced and printed. In ~/graph-venv with the chat image's pins. See commands/window_check.py.
window-check: $(if $(LIVE),guard-project,)
	@$(if $(LIVE),GOOGLE_CLOUD_PROJECT=$(PROJECT)) PY=$(PY) bash commands/graph-venv.sh commands/window_check.py \
	  $(if $(MODE),--mode $(MODE),) $(if $(TURNS),--turns $(TURNS),) $(if $(HISTORY),--history $(HISTORY),) \
	  $(if $(BRAIN),--brain $(BRAIN),) $(if $(SAVE),--save "$(SAVE)",) $(if $(LIVE),--live,)
