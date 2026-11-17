"""Lesson 12.4: The version on every usage row

Cloud Logging's rows, grouped by the version that answered, and what the new line costs on every answer. The rows, by version. Every answer leaves a usage row, and each row carries prompt_version, the excerpt in step 4. make usage groups the rows by tenant, model, brain, surface and retrieval backend, but not by version, so this cell reads the same rows with make usage's own read_rows() and groups them with its own group(), keyed by prompt_version. The gate's answers on the candidate are v4's, and the live answers before the promote are v3's.

Run order inside this file:
1. The version on every usage row (source window 57)

Prerequisites: demo_09_promote_or_roll_back.
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


def step_01_the_version_on_every_usage_row(session):
    """Run The version on every usage row at this checkpoint.

    Cloud Logging's rows, grouped by the version that answered, and what the new line costs on every answer. The rows, by version. Every answer leaves a usage row, and each row carries prompt_version, the excerpt in step 4. make usage groups the rows by tenant, model, brain, surface and retrieval backend, but not by version, so this cell reads the same rows with make usage's own read_rows() and groups them with its own group(), keyed by prompt_version. The gate's answers on the candidate are v4's, and the live answers before the promote are v3's.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads Cloud Logging; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/usage_delta.txt]
    """
    import json, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import usage_rows                     # make usage's own reader and GROUP BY
    rows = usage_rows.read_rows(os.environ["PROJECT"], 3)
    print(f"{len(rows)} answers from documind-api in the last 3 hours; USD_INR={usage_rows.USD_INR}")
    usage_rows.show("by prompt version", usage_rows.group(rows, ("prompt_version",)), ("prompt_version",))
    newest = {}
    for r in rows:                        # gcloud lists the newest entry first
        newest.setdefault(r.get("prompt_version"), r)
    for v in sorted(newest):
        print(f"newest {v} row: tokens_in {newest[v].get('tokens_in')}, tokens_out {newest[v].get('tokens_out')}")
    versions = json.load(open("services/rag-api/prompt_rules.json", encoding="utf-8"))["versions"]
    pv = max(versions, key=lambda v: int(v[1:]))        # the version accept wrote: v4, or v5 where lesson 3.6 spent v4
    if pv != "v3" and {"v3", pv} <= set(newest):
        print(f"tokens_in, {pv} minus v3:", int(newest[pv].get("tokens_in") or 0) - int(newest["v3"].get("tokens_in") or 0))
    added = "".join(f"{6 + k}. {rule}\n" for k, rule in enumerate(versions[pv].get("rules", [])))
    print(f"{pv}'s added lines: {len(added)} characters, about {len(added) // 4} tokens by the kit's estimate (len // 4)")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_57', step_01_the_version_on_every_usage_row),
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
