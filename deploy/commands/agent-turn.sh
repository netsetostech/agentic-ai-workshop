#!/usr/bin/env bash
# make agent-turn (mk/agents.mk): one turn of an agent pattern, printed whole (commands/agent_turn.py, workshop lessons
# 10.1-10.3 and 10.5). OFFLINE=1: a scripted model and the kit's own corpus - no credential, no cost. Otherwise one real
# turn on your lane: gemini-3.6-flash on location global, built as the Desk's agent builds it, and rag-api's
# /v1/passages with an ID token minted as documind-ui-sa (DOCUMIND_IMPERSONATE_SA, shared/documind_tools.py), which
# every tenant's roster holds. PROJECT and REGION name the lane; PATTERN, THINKING, DESK, TENANT and Q the turn, ROW
# a row of evals/agent_tasks.jsonl in Q's place, and EXEC_MODEL the executor's model of plan_execute and rewoo
# (lesson 10.2). INVENT and LAUNDER, offline, are agent_turn.py's --invent and --launder (lessons 10.1 and 10.3): 1
# passes the flag with its own figure, anything else is the figure (13 October 2026).
# With arguments it runs those instead, in the same venv and the same environment: make agent-eval passes
# evals/agent_eval.py and its flags, make agent-tests the bench's chat-pins tests, and make agent-shapes (lesson
# 10.7) commands/agent_shapes.py.
# It runs in ~/graph-venv (workshop lesson 5.4's), made here if it is missing, with the chat image's pins installed
# into it, as commands/limits-check.sh does.
# The same without make:  OFFLINE=1 bash commands/agent-turn.sh        (from deploy/)
set -euo pipefail
VENV="${GRAPH_VENV:-$HOME/graph-venv}"
[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"
"$VENV/bin/pip" install -q -r services/chat/requirements.txt
if [ "${OFFLINE:-}" = 1 ]; then
  MODE=--offline
else
  : "${PROJECT:?set PROJECT=<project id> for a turn on your lane, or OFFLINE=1 for the scripted one}"
  REGION="${REGION:-us-central1}"
  NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
  case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; nothing sent.' >&2; exit 1;; esac
  export GOOGLE_CLOUD_PROJECT="$PROJECT" RAG_API_URL="https://documind-api-$NUMBER.$REGION.run.app"
  export DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
  MODE=--live
fi
if [ "$#" -gt 0 ]; then
  exec "$VENV/bin/python" "$@"
fi
ARGS=(--pattern "${PATTERN:-loop}" --desk "${DESK:-astar}" --tenant "${TENANT:-acme}")
if [ -n "${THINKING:-}" ]; then ARGS+=(--thinking "$THINKING"); fi
if [ -n "${Q:-}" ]; then ARGS+=(--question "$Q"); fi
if [ -n "${ROW:-}" ]; then ARGS+=(--row "$ROW"); fi
if [ -n "${EXEC_MODEL:-}" ]; then ARGS+=(--exec-model "$EXEC_MODEL"); fi
if [ -n "${INVENT:-}" ]; then ARGS+=(--invent); [ "$INVENT" = 1 ] || ARGS+=("$INVENT"); fi
if [ -n "${LAUNDER:-}" ]; then ARGS+=(--launder); [ "$LAUNDER" = 1 ] || ARGS+=("$LAUNDER"); fi
exec "$VENV/bin/python" commands/agent_turn.py "$MODE" "${ARGS[@]}"
