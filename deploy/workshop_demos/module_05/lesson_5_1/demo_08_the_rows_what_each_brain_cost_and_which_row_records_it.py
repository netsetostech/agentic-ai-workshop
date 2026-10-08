"""Lesson 5.1: The rows: what each brain cost, and which row records it

rag-api's row for every retrieve(), and the chat service's row for every turn. Each retrieve() posts to rag-api's /v1/query, and rag-api writes its usage row, now labelled with the brain that asked. The chat service writes a row of its own for each turn: the brain, the tenant, the user, the session, the time and the two lists, and the turn's own model calls, their tokens and their cost, beside what its searches billed. Lesson 5.5 shows the limits those numbers are counted against. The cell reads both kinds since step 5, the shell's own retrieval included, labelled ui because it named no brain.

Run order inside this file:
1. The rows: what each brain cost, and which row records it (source window 24)

Prerequisites: demo_07_the_loop_the_model_chooses_its_tools.
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


def step_01_the_rows_what_each_brain_cost_and_which_ro(session):
    """Run The rows: what each brain cost, and which row records it at this checkpoint.

    rag-api's row for every retrieve(), and the chat service's row for every turn. Each retrieve() posts to rag-api's /v1/query, and rag-api writes its usage row, now labelled with the brain that asked. The chat service writes a row of its own for each turn: the brain, the tenant, the user, the session, the time and the two lists, and the turn's own model calls, their tokens and their cost, beside what its searches billed. Lesson 5.5 shows the limits those numbers are counted against. The cell reads both kinds since step 5, the shell's own retrieval included, labelled ui because it named no brain.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the rows both services wrote since the retrieve cell; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: rag-api, one row per retrieve():
        brain ui         in   1790  out   96  Rs 0.2894   2600 ms
        brain direct     in   1790  out   96  Rs 0.2894   2710 ms
        brain langchain  in   1812  out  101  Rs 0.2954   2840 ms
        brain langchain  in   1650  out   88  Rs 0.2665   2390 ms
        brain direct     in   1705  out   92  Rs 0.2760   2620 ms
      the chat service, one row per turn:
        brain direct     tool_calls ['retrieve']    3180 ms  (keys: brain, budget_inr, cached_tokens, cost_usd, event, latency_ms, max_model_calls, model, model_calls, rag_cost_usd, refusals, session_id, stopped_by, surface, tenant, tokens_in, tokens_out, tool_calls, tool_timeouts, user)
        brain langchain  tool_calls ['
    """
    import json, os, subprocess
    def rows(service, event):
        """Read usage log rows for the specified service and event so the brain costs can be compared.
        
        Example: rows('documind-api', 'query')
        """
        f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND jsonPayload.event="{event}" '
             f'AND timestamp>="{os.environ["SINCE101"]}"')
        out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "30",
                              "--format", "json"], capture_output=True, text=True, check=True).stdout
        return [e["jsonPayload"] for e in json.loads(out or "[]")]
    print("  rag-api, one row per retrieve():")
    for j in rows("documind-api", "query"):
        print(f"    brain {j.get('brain', ''):9}  in {j['tokens_in']:>6}  out {j['tokens_out']:>4}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")
    print("  the chat service, one row per turn:")
    for j in rows("documind-chat", "chat"):
        print(f"    brain {j['brain']:9}  tool_calls {j['tool_calls']}  {j['latency_ms']:>6} ms  (keys: {', '.join(sorted(j))})")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_the_rows_what_each_brain_cost_and_which_ro),
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
