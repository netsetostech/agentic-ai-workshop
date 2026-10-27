#!/usr/bin/env bash
# make handoff [OFF=1] (mk/agents.mk): switch the chat's hand-off to the A2A peer on, or off (workshop lesson 10.7).
# On: PEER_URL, the peer's run.app url, and PEER_ACCOUNT, the account documind-agent runs as - read from Cloud Run, so
# services/chat/peer.py's confused-deputy gate reads the roster of the account that really answers - go onto
# documind-chat in one env update (a new revision; nothing is rebuilt). The ADK brain may then hand a question to the
# peer: two a turn, 75 s each at most, and only for a tenant whose roster is the peer account's one roster. Off: both
# are removed. Either way the latest revision must take all the traffic. The next make deploy-services puts the
# chat's own environment back (commands/lesson-12.8.sh sets every variable), and the hand-off is off again.
# Before switching on it checks that documind-agent is deployed and that documind-chat-sa may invoke it
# (commands/lesson-8.4.sh binds it); either missing, nothing changes. No model call.
# The same without make:  PROJECT=<id> REGION=<region> [OFF=1] bash commands/handoff.sh
set -euo pipefail
: "${PROJECT:?set PROJECT=<project id>}"
REGION="${REGION:-us-central1}"; PY="${PY:-python3}"; CHAT=documind-chat; PEER=documind-agent
NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; nothing changed.' >&2; exit 1;; esac
svc() { local name=$1; shift; gcloud run services "$@" "$name" --project="$PROJECT" --region="$REGION"; }
latest_takes_all() {   # the latest revision serves 100 percent: an env change creates a revision that must serve
  svc "$CHAT" describe --format=json | "$PY" -c 'import json, sys
t = json.load(sys.stdin)["status"].get("traffic", [])
sys.exit(0 if any(x.get("latestRevision") and x.get("percent") == 100 for x in t) else 1)'
}
update() {   # documind-chat's env, quietly: gcloud's deploy progress goes to stderr, and is shown only on a failure
  local log; log=$(mktemp)
  if svc "$CHAT" update "$@" --quiet >/dev/null 2>"$log"; then rm -f "$log"; else cat "$log" >&2; rm -f "$log"; return 1; fi
}
latest_takes_all || { echo "ERROR: $CHAT's traffic is pinned away from its latest revision; the change would not serve." >&2
                      echo "       gcloud run services update-traffic $CHAT --to-latest --region=$REGION   then run it again." >&2; exit 1; }
if [ -n "${OFF:-}" ]; then
  update --remove-env-vars=PEER_URL,PEER_ACCOUNT
  latest_takes_all || { echo "ERROR: the new revision does not take all the traffic." >&2; exit 1; }
  echo ">> $CHAT: the hand-off is off (PEER_URL and PEER_ACCOUNT removed); every brain answers alone"
  exit 0
fi
URL="https://$PEER-$NUMBER.$REGION.run.app"
ACCOUNT=$(svc "$PEER" describe --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)
[ -n "$ACCOUNT" ] || { echo "ERROR: $PEER is not deployed in $REGION; nothing changed." >&2
                       echo "       make build deploy-services SERVICES=agent SCRIPTS=commands/lesson-8.4.sh   then run it again." >&2; exit 1; }
CALLER="serviceAccount:documind-chat-sa@$PROJECT.iam.gserviceaccount.com"
svc "$PEER" get-iam-policy --format=json | "$PY" -c 'import json, sys
b = json.load(sys.stdin).get("bindings", [])
sys.exit(0 if any(x.get("role") == "roles/run.invoker" and sys.argv[1] in x.get("members", []) for x in b) else 1)' "$CALLER" \
  || { echo "ERROR: documind-chat-sa may not invoke $PEER (roles/run.invoker); nothing changed." >&2
       echo "       commands/lesson-8.4.sh's step 3 binds it." >&2; exit 1; }
update --update-env-vars="PEER_URL=$URL,PEER_ACCOUNT=$ACCOUNT"
latest_takes_all || { echo "ERROR: the new revision does not take all the traffic." >&2; exit 1; }
echo ">> $CHAT: PEER_URL=$URL"
echo ">> $CHAT: PEER_ACCOUNT=$ACCOUNT"
echo "   the ADK brain may hand a question to the peer; make smoke-handoff checks it, make handoff OFF=1 ends it"
