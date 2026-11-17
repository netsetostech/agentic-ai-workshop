#!/usr/bin/env bash
# Run one of the kit's Python commands in ~/graph-venv with the chat image's pins (mk/memory.mk's make thread and make
# replay, workshop lesson 6.8). ~/graph-venv is workshop lesson 5.4's venv, made here if it is missing, as
# commands/limits-check.sh makes it; services/chat/requirements.txt is installed into it, so the kit's brains, LangGraph
# and its checkpointer are the versions the chat service runs. --connector adds the Cloud SQL Python Connector and pg8000
# at lesson 6.6's pins, which reading the lane's checkpoint database needs. pip changes nothing when the pins are there.
# The same without make:  bash commands/graph-venv.sh [--connector] commands/thread_read.py --project ... (from deploy/)
set -euo pipefail
extra=()
if [ "${1:-}" = "--connector" ]; then
  extra=("cloud-sql-python-connector[pg8000]==1.22.0" "pg8000==1.31.5")
  shift
fi
VENV="${GRAPH_VENV:-$HOME/graph-venv}"
[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"
"$VENV/bin/pip" install -q -r services/chat/requirements.txt ${extra[@]+"${extra[@]}"}
exec "$VENV/bin/python" "$@"
