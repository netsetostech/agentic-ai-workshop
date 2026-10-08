"""Lesson 5.1: The one retrieve(), from your shell

Do it

Run order inside this file:
1. Do it (source window 15)

Prerequisites: demo_04_the_contract_what_the_model_reads_of_each_tool.
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


# Original CLI workflow for step_01_the_one_retrieve_from_your_shell.
COMMANDS_01 = """export SINCE101="$(date -u +%FT%TZ)"
DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" RAG_API_URL="$API" python - <<'PY'
import time
from shared.documind_tools import retrieve
t = time.time()
r = retrieve("After how many years of continuous service does gratuity become payable?", tenant_id="acme", top_k=5)
print(f"  {len(r['citations'])} citations | answerable {r['answerable']} | confidence {r['confidence']} | {time.time() - t:.1f} s")
if r["citations"]:
    print("  first:", {k: r["citations"][0].get(k) for k in ("chunk_id", "page", "score")})
print("  rag-api's own answer:", (r.get("answer") or r.get("error") or "")[:90])
PY

"""

def step_01_the_one_retrieve_from_your_shell(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the one retrieve(), called from your shell as a roster member).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 5 citations | answerable True | confidence high | 2.7 s
      first: {'chunk_id': 'acme:aaaaaaaa#0', 'page': 3, 'score': 0.94}
      rag-api's own answer: Gratuity is payable on termination after not less than five years of continuous service [1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_the_one_retrieve_from_your_shell),
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
