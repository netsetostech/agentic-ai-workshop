#!/usr/bin/env bash
# make approval-check (mk/agents.mk): workshop lesson 5.8's person in the loop, offline - no credential, no cost.
# services/chat/approval.py, which the chat service does not import, on scripted models: a withdrawal that waits for a
# second person and is resumed by a second process from the same SQLite checkpoint file; the requester's own approval
# refused; a rejection that errors that call alone while a search beside it runs; a question the person who asked
# answers; a case offered with nothing written; the approval line a resume writes twice once it sits above interrupt();
# and the same pause as LangChain's HumanInTheLoopMiddleware.
# It runs in ~/graph-venv (workshop lesson 5.4's), made here if it is missing, with the chat image's pins and the local
# lane's SQLite checkpointer, at the version services/chat/requirements-local.txt pins. CI's chat-pins step runs the
# same test file.
# The same without make:  bash commands/approval-check.sh        (from deploy/)
set -euo pipefail
VENV="${GRAPH_VENV:-$HOME/graph-venv}"
[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"
SQLITE="$(grep -E '^langgraph-checkpoint-sqlite==' services/chat/requirements-local.txt)" \
  || { echo "ERROR: services/chat/requirements-local.txt pins no langgraph-checkpoint-sqlite" >&2; exit 1; }
"$VENV/bin/pip" install -q -r services/chat/requirements.txt "$SQLITE"
DOCUMIND_REQUIRE_LIBS=1 "$VENV/bin/python" -m unittest commands/tests/test_approvals.py -v
