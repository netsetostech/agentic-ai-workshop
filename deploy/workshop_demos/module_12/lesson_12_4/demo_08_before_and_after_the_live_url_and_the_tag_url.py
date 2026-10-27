"""Lesson 12.4: Before and after: the live URL and the tag URL

The same question to the revision your users reach and to the candidate, with the label each one answers under. Two addresses, one service. The UI reaches only the live URL, so it cannot show you the candidate before it is promoted. The tag URL reaches the candidate directly. The token is minted for the service's canonical URL and works on both, as lesson 11.2's gate uses it. GET /version names the label each one answers under, and the same question goes to both.

Run order inside this file:
1. Before and after: the live URL and the tag URL (source window 52)

Prerequisites: demo_07_v4_on_a_candidate_and_the_gate.
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


# Original CLI workflow for step_01_before_and_after_the_live_url_and_the_tag.
COMMANDS_01 = """export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
for url in "$API" "$CAND"; do
  echo "== $url"
  curl -s "$url/version" -H "Authorization: Bearer $(tok "$API")" \\
    | python -c 'import json, sys; v = json.load(sys.stdin); print("prompt:", v["prompt"], "| git_sha", v["git_sha"])'
  curl -s -X POST "$url/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
    -d "$(python -c 'import json, os; print(json.dumps({"query": os.environ["Q"], "tenant_id": os.environ["TENANT"], "stream": False}))')" \\
    | python -c 'import json, sys; a = json.load(sys.stdin); print("answerable:", a["answerable"], "| answer:", a["answer"])'
done

"""

def step_01_before_and_after_the_live_url_and_the_tag(session):
    """Run Before and after: the live URL and the tag URL at this checkpoint.

    The same question to the revision your users reach and to the candidate, with the label each one answers under. Two addresses, one service. The UI reaches only the live URL, so it cannot show you the candidate before it is promoted. The tag URL reaches the candidate directly. The token is minted for the service's canonical URL and works on both, as lesson 11.2's gate uses it. GET /version names the label each one answers under, and the same question goes to both.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one answer from each URL: about Rs 0.9).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/before_after.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_52', step_01_before_and_after_the_live_url_and_the_tag),
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
