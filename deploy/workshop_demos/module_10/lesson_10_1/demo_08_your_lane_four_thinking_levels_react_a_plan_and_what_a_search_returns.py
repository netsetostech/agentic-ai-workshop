"""Lesson 10.1: Your lane: four thinking levels, ReAct, a plan, and what a search returns

The loop, on the gratuity question, once at each level. The filter keeps the level line, the three call lines, the totals and the figure check of each turn. Do it: prompted ReAct Do it: a plan first Every pattern's retrieve is one POST to rag-api's /v1/passages: the same door, roster and filters as /v1/query, then the reranked passages with their full text, and no model. The cell sends the search the bench's script makes for this question, as the bench sends it: tenant acme, the three classes, the top 5, labelled brain desk.

Run order inside this file:
1. Do it: native thinking, at four levels (source window 39)
2. Do it: prompted ReAct (source window 41)
3. Do it: a plan first (source window 43)
4. Do it: what a search returns (source window 45)

Prerequisites: demo_07_the_11_calculator_rows_scored_offline_and_paired.
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


# Original CLI workflow for step_01_native_thinking_at_four_levels.
COMMANDS_01 = """for t in minimal low medium high; do make agent-turn PROJECT="$PROJECT" REGION="$REGION" THINKING=$t 2>&1 | grep -E '^(  thinking:|model call|tokens:|figure check|the turn failed|make: )'; done

"""

def step_01_native_thinking_at_four_levels(session):
    """Run Do it: native thinking, at four levels at this checkpoint.

    The loop, on the gratuity question, once at each level. The filter keeps the level line, the three call lines, the totals and the figure check of each turn.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (four live turns of the loop, about Rs 4.63 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_levels.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_prompted_react.
COMMANDS_02 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=react_text

"""

def step_02_prompted_react(session):
    """Run Do it: prompted ReAct at this checkpoint.

    Do it: prompted ReAct

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live turn, about Rs 1.26 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_react.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_plan_first.
COMMANDS_03 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_first

"""

def step_03_a_plan_first(session):
    """Run Do it: a plan first at this checkpoint.

    Do it: a plan first

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live turn, about Rs 1.22 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_plan.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_what_a_search_returns(session):
    """Run Do it: what a search returns at this checkpoint.

    Every pattern's retrieve is one POST to rag-api's /v1/passages: the same door, roster and filters as /v1/query, then the reranked passages with their full text, and no model. The cell sends the search the bench's script makes for this question, as the bench sends it: tenant acme, the three classes, the top 5, labelled brain desk.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: /v1/passages calls no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/passages.txt]
    """
    import json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    PROJECT, API = os.environ["PROJECT"], os.environ["API"]
    token = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                            f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                           capture_output=True, text=True, check=True).stdout.strip()
    body = {"query": "gratuity fifteen days wages for every completed year of service", "tenant_id": "acme", "top_k": 5,
            "stream": False, "filters": {"doc_type": ["guidance", "policy", "statute"]}, "brain": "desk"}
    req = urllib.request.Request(f"{API}/v1/passages", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    got = json.load(urllib.request.urlopen(req, timeout=60))
    u = got["usage"]
    print(f"answerable {got['answerable']} | passages {len(got['passages'])} | model {u['model']} | cost_usd {u['cost_usd']} | "
          f"tokens {u['tokens_in']} in, {u['tokens_out']} out | pool {u['stages']['pool']}")
    for p in got["passages"]:
        print(f"  [{p['n']}] {p['source_uri'].rsplit('/', 1)[-1]:<38} {p['doc_type']:<9} {len(p['text']):>6,} characters")
    print(f"every later call of the turn reads them again: {sum(len(p['text']) for p in got['passages']):,} characters")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_39', step_01_native_thinking_at_four_levels),
        ('source_41', step_02_prompted_react),
        ('source_43', step_03_a_plan_first),
        ('source_45', step_04_what_a_search_returns),
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
