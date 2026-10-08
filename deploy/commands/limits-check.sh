#!/usr/bin/env bash
# make limits-check (mk/agents.mk): a chat turn's limits, offline - no credential, no cost (workshop lesson 5.5).
# The kit's own langchain, langgraph and adk brains against scripted models and a stand-in rag-api: a looping model
# stopped by the call cap, the rupee cap and the deadline with the next turn answering; a slow search abandoned at
# its budget as data; a hung model call ending in the stop; the checkpoints a turn writes unchanged.
# It runs in ~/graph-venv (workshop lesson 5.4's), made here if it is missing, with the chat image's pins installed
# into it: google-adk is among them, and workshop lesson 5.5's venv lacks it. CI's chat-pins step runs the same test
# file.
# The same without make:  bash commands/limits-check.sh        (from deploy/)
set -euo pipefail
VENV="${GRAPH_VENV:-$HOME/graph-venv}"
[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"
"$VENV/bin/pip" install -q -r services/chat/requirements.txt
DOCUMIND_REQUIRE_LIBS=1 "$VENV/bin/python" -m unittest commands/tests/test_chat_limits.py -v
