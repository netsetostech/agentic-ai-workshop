"""Lesson 6.2: The context cache: a pack, a cache, and the next answer

Do it: the question, uncached Do it: the cache Do it: the same question, with the cache

Run order inside this file:
1. Do it: the question, uncached (source window 10)
2. Do it: the cache (source window 12)
3. Do it: the same question, with the cache (source window 14)

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


# Original CLI workflow for step_01_the_question_uncached.
COMMANDS_01 = """ask91() {   # one /v1/query to $1 about acme, as documind-ui-sa; prints the answer's cache fields
TOKEN="$(tok "$API")" URL="$1" Q="$2" python - <<'PY'
import json, os, urllib.error, urllib.request
body = json.dumps({"query": os.environ["Q"], "tenant_id": "acme", "top_k": 6}).encode()
req = urllib.request.Request(os.environ["URL"] + "/v1/query", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  backend {a['backend']:6} cache_hit {a['cache_hit']:8} tokens_in {a['tokens_in']:>6}  cached_tokens {a['cached_tokens']:>6}  {a['latency_ms']:>5} ms  | {a['answer'][:44]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:90]}")
PY
}
export SINCE91="$(date -u +%FT%TZ)" Q91="How many days a month can I work remotely?"
ask91 "$API" "$Q91"

"""

def step_01_the_question_uncached(session):
    """Run Do it: the question, uncached at this checkpoint.

    Do it: the question, uncached

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a small ask function, a start time for the rows, and one question to the live API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend vertex cache_hit none     tokens_in   1812  cached_tokens      0   2410 ms  | Employees may work remotely up to eight days
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_cache.
COMMANDS_02 = """make cache PROJECT="$PROJECT" TENANT=acme

"""

def step_02_the_cache(session):
    """Run Do it: the cache at this checkpoint.

    Do it: the cache

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's context cache: its pack, on Gemini, for an hour).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \\
      python cache_admin.py ${CACHE_OP:-create} --project documind-ai-YOUR-ID --tenant acme
      cache projects/NUMBER/locations/global/cachedContents/CACHE_ID
      location global (global or regional: the answer to CLAUDE.md's question)
      model gemini-3.6-flash | tokens 41259 | expires YYYY-MM-DD HH:MM:SS.ssssss+00:00 | corpus 75b21a03f12f | ledger fingerprint FINGERPRINT
      the next /v1/query for acme carries cached_content; read cached_tokens in its usage row
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_same_question_with_the_cache.
COMMANDS_03 = """ask91 "$API" "$Q91"

"""

def step_03_the_same_question_with_the_cache(session):
    """Run Do it: the same question, with the cache at this checkpoint.

    Do it: the same question, with the cache

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question again, to the live API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend vertex cache_hit none     tokens_in  43071  cached_tokens  41259   2650 ms  | Employees may work remotely up to eight days
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_question_uncached),
        ('source_12', step_02_the_cache),
        ('source_14', step_03_the_same_question_with_the_cache),
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
