"""Lesson 11.4: A right answer, and its trail

Do it

Run order inside this file:
1. Do it (source window 11)

Prerequisites: demo_03_the_trail_as_the_kit_writes_it_down.
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


# Original CLI workflow for step_01_a_right_answer_and_its_trail.
COMMANDS_01 = """ask131() {   # ask131 LABEL: acme's E3 notice-period question as documind-ui-sa - the answer and its trail, kept in ~/ask131-LABEL.json
LABEL="$1" python - <<'PY'
import json, os, subprocess, urllib.request
label, P, API = os.environ["LABEL"], os.environ["PROJECT"], os.environ["API"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
body = json.dumps({"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme"}).encode()
req = urllib.request.Request(API + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
ans = json.load(urllib.request.urlopen(req, timeout=120))
json.dump(ans, open(os.path.expanduser(f"~/ask131-{label}.json"), "w"), indent=1)
s = ans["stages"]
print(ans["answer"])
for n, c in enumerate(ans["citations"], 1):
    version, chunk = c["chunk_id"].split(":", 1)[1].split("#")
    print(f"  [{n}] {c['source_uri'].rsplit('/', 1)[-1]}  version {version[:12]}  chunk {chunk}  {c['quote']!r}")
print(f"  cache_hit {ans['cache_hit']} | backend {ans['backend']} | answerable {ans['answerable']}")
print(f"  store {s.get('retrieval_backend')} | vector_chunks {s.get('vector_chunks')} | pool {s.get('pool')} | "
      f"rerank_fallback {s.get('rerank_fallback', 0)} | policy_fallback {s.get('policy_fallback')}")
print(f"  kept in ~/ask131-{label}.json")
PY
}
ask131 before

"""

def step_01_a_right_answer_and_its_trail(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the question, the answer and its trail).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
      [1] hr_policy_2026.md  version 497809ffbaa6  chunk 1  'serves a notice period of 60 days'
      cache_hit none | backend vertex | answerable True
      store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
      kept in ~/ask131-before.json
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_a_right_answer_and_its_trail),
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
