#!/usr/bin/env bash
# make attack-agents [SURFACES=chat,desk,peer] [REPORT=...] [LABEL=...] [CHAT=...] (mk/agents.mk): lesson 10.8's rows of
# the attack set (evals/adversarial/attacks.jsonl) on the agents' doors, as make attack-eval runs lesson 4.9's rows on
# rag-api's (workshop lesson 10.8). Every one of those rows asks as the member, so one token is minted: as
# documind-ui-sa, the UI's account, for documind-chat's canonical URL, the way make attack-eval and make eval-live mint
# rag-api's (DOCUMIND_ID_TOKEN, when set, is used instead). CHAT= picks the URL to call; the token's audience stays the
# canonical one. The chat rows ask the brain DOCUMIND_ATTACK_BRAIN names (langchain unless set), the Desk rows the Desk
# on the same service. The peer row goes to the A2A peer you run on your own machine (services/agent/agent.py with
# MCP_URL at make mcp-local's server and MCP_AUTH=none) at DOCUMIND_PEER_URL, default http://127.0.0.1:8080. Beside the
# lane's rows it carries the headers they carry, which that peer does not read; alone (SURFACES=peer) it carries no
# token, and the run mints nothing and needs no PROJECT. SURFACES= the surfaces whose rows run, comma-separated
# (default chat,desk); REPORT= writes every row's request, outcome and verdict, never a token; LABEL= names the run;
# make attack-offline COMPARE="A B" sets two reports side by side. The exit status is the runner's: 1 when a structural
# row opens or a reply holds another tenant's text, 2 when it cannot start. A chat or Desk row is one turn on your lane.
# The same without make, from the kit:  PROJECT=<id> REGION=<region> [SURFACES=...] bash commands/attack-agents.sh
set -euo pipefail
REGION="${REGION:-us-central1}"; PY="${PY:-python3}"; SURFACES="${SURFACES:-chat,desk}"
lane=; peer=
IFS=, read -r -a wanted <<< "$SURFACES"
for s in "${wanted[@]}"; do
  case "$s" in
    chat|desk) lane=1;;
    peer) peer=1;;
    '') ;;
    *) echo "ERROR: SURFACES names chat, desk and peer, not $s (rag-api's rows are make attack-eval's); no attack sent." >&2
       exit 2;;
  esac
done
args=(--surfaces "$SURFACES")
if [ -n "$lane" ]; then
  : "${PROJECT:?set PROJECT=<project id>}"
  NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
  case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no attack sent.' >&2; exit 1;; esac
  AUD="https://documind-chat-$NUMBER.$REGION.run.app"
  DOCUMIND_ID_TOKEN="${DOCUMIND_ID_TOKEN:-$(gcloud auth print-identity-token --include-email \
    --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" --audiences="$AUD")}"
  [ -n "$DOCUMIND_ID_TOKEN" ] || { echo 'ERROR: no token was minted for documind-chat; no attack sent.' >&2; exit 1; }
  export DOCUMIND_ID_TOKEN
  CHAT="${CHAT:-$AUD}"
  echo ">> $CHAT"
  args+=(--chat-url "$CHAT" --desk)
else
  unset DOCUMIND_ID_TOKEN DOCUMIND_OUTSIDER_TOKEN          # the peer alone: nothing minted, no token to a local peer
fi
if [ -n "$peer" ]; then
  echo ">> ${DOCUMIND_PEER_URL:-http://127.0.0.1:8080} (the A2A peer on this machine)"
  args+=(--peer-local)
fi
if [ -n "${REPORT:-}" ]; then args+=(--report "$REPORT"); fi
if [ -n "${LABEL:-}" ]; then args+=(--label "$LABEL"); fi
exec "$PY" evals/run_attacks.py "${args[@]}"
