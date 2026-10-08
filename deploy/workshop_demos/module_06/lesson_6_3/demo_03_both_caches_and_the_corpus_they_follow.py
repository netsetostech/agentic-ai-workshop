"""Lesson 6.3: Both caches, and the corpus they follow

Do it: the two caches Do it: the state, and three asks

Run order inside this file:
1. Do it: the two caches (source window 8)
2. Do it: the state, and three asks (source window 10)

Prerequisites: setup_prepare.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_the_two_caches.
COMMANDS_01 = """make cache PROJECT="$PROJECT" TENANT=acme
make candidate PROJECT="$PROJECT" SEMANTIC_CACHE=on
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_01_the_two_caches(session):
    """Run Do it: the two caches at this checkpoint.

    Do it: the two caches

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's context cache, and a candidate with the answer cache on).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \\
      python cache_admin.py ${CACHE_OP:-create} --project documind-ai-YOUR-ID --tenant acme
      cache projects/NUMBER/locations/global/cachedContents/CACHE_ID
      location global (global or regional: the answer to CLAUDE.md's question)
      model gemini-3.6-flash | tokens 41259 | expires YYYY-MM-DD HH:MM:SS.ssssss+00:00 | corpus 75b21a03f12f | ledger fingerprint 1ef46119bd89b143
      the next /v1/query for acme carries cached_content; read cached_tokens in its usage row
    gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-var
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_state_and_three_asks.
COMMANDS_02 = """ask92() {   # one /v1/query about acme to $1, as documind-ui-sa; $2 = top_k (6), $3 = filters as JSON (none)
TOKEN="$(tok "$API")" URL="$1" K="${2:-6}" F="${3:-null}" Q="$Q92" python - <<'PY'
import json, os, urllib.error, urllib.request
body = json.dumps({"query": os.environ["Q"], "tenant_id": "acme", "top_k": int(os.environ["K"]), "filters": json.loads(os.environ["F"])}).encode()
req = urllib.request.Request(os.environ["URL"] + "/v1/query", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  {a['backend']:6} {a['cache_hit']:8} in {a['tokens_in']:>6} cached {a['cached_tokens']:>6} {a['latency_ms']:>5} ms | {a['answer'][:50]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:90]}")
PY
}
state92() {   # the ledger's fingerprint beside the one the context cache was packed from
python - <<'PY'
import os
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
l, c = (db.document(p).get().to_dict() or {} for p in ("ledger/acme", "tenant_caches/acme"))
state = "none" if not c else "current" if c.get("corpus_fingerprint") == l.get("fingerprint") else "STALE"
print(f"  ledger {l.get('fingerprint')} ({l.get('versions')} versions, last {l.get('last_event')}) | context cache packed from {c.get('corpus_fingerprint')}: {state}")
PY
}
export SINCE92="$(date -u +%FT%TZ)" Q92="What is the notice period for a confirmed E3?"
state92
ask92 "$API"            # the live revision: the context cache, no answer cache
ask92 "$CAND"           # the candidate: a miss, stored
ask92 "$CAND"           # the same words: the exact rung

"""

def step_02_the_state_and_three_asks(session):
    """Run Do it: the state, and three asks at this checkpoint.

    Do it: the state, and three asks

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two small functions, a start time, the state, and three asks).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ledger 1ef46119bd89b143 (17 versions, last ingest_ok) | context cache packed from 1ef46119bd89b143: current
      vertex none     in  43109 cached  41259  2480 ms | A confirmed employee at grade E3 or above serves a
      vertex none     in  43109 cached  41259  2530 ms | A confirmed employee at grade E3 or above serves a
      cache  semantic in      0 cached      0   170 ms | A confirmed employee at grade E3 or above serves a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_two_caches),
        ('source_10', step_02_the_state_and_three_asks),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
