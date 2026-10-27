#!/usr/bin/env bash
# Run commands/managed_peer.py (workshop lesson 10.9, mk/managed.mk's targets) in ~/managed-peer-venv, made here if it
# is missing: google-adk at the A2A peer's own pin and extras (services/agent/requirements.txt: [mcp] is what lets the
# staged agent import here), whose deploy builds the managed
# runtime, and google-cloud-aiplatform[adk,agent_engines], which that deploy, ADK's session service and the Agent
# Engine client import - the install the author's probe resolves as its fact 11. Not ~/graph-venv: aiplatform is not
# one of the chat image's pins, and lessons 10.4 and 11.1-11.3 assert what that venv holds. AIPLATFORM_PIN=<version>
# pins aiplatform here (managed_peer.py's --aiplatform-pin pins it in the runtime's image too); empty, pip takes the
# latest, as ADK's deploy does for the image. pip changes nothing once the pins are there.
# The same without make:  bash commands/managed-peer.sh up --project <id> --region <region>   (from deploy/)
set -euo pipefail
VENV="${MANAGED_PEER_VENV:-$HOME/managed-peer-venv}"
ADK_PIN=$(sed -n 's/^google-adk\[[^]]*\]==\([0-9.]*\)$/\1/p' services/agent/requirements.txt)
if [ -z "$ADK_PIN" ]; then
  echo "services/agent/requirements.txt pins no google-adk" >&2
  exit 2
fi
[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"
"$VENV/bin/pip" install -q "google-adk[a2a,mcp]==$ADK_PIN" "google-cloud-aiplatform[adk,agent_engines]${AIPLATFORM_PIN:+==$AIPLATFORM_PIN}"
exec "$VENV/bin/python" commands/managed_peer.py "$@"
