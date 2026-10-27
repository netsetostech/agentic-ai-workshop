"""Lesson 3.1: What your lane logged, and what the bench did not

rag-api writes one usage row for every /v1/query, /v1/stream and /v1/passages request, in the one shape main.py's usage_row() builds, to Cloud Logging. make usage and the BigQuery view tenant_daily read those rows, and as each one is written its cost is added to the month's spend counter, which the router's breaker reads before it picks a model. The cell reads the rows written since T0, the time you noted in step 3, oldest first, with each row's tokens and the price cost.py gave it. Wait a minute after step 8, because a row can take a little while to reach the log, and if this is a new shell, set T0 again to a time before step 3.

Run order inside this file:
1. Definition (source window 34)

Prerequisites: demo_08_change_it_send_a_temperature_of_2_0_and_read_what_went_out.
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


def step_01_definition(session):
    """Run Definition at this checkpoint.

    rag-api writes one usage row for every /v1/query, /v1/stream and /v1/passages request, in the one shape main.py's usage_row() builds, to Cloud Logging. make usage and the BigQuery view tenant_daily read those rows, and as each one is written its cost is added to the month's spend counter, which the router's breaker reads before it picks a model. The cell reads the rows written since T0, the time you noted in step 3, oldest first, with each row's tokens and the price cost.py gave it. Wait a minute after step 8, because a row can take a little while to reach the log, and if this is a new shell, set T0 again to a time before step 3.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT, a minute after step 8 (a Python cell; Rs 0: one Cloud Logging read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/usage_rows.txt]
    """
    import json, os, subprocess, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared.prices import USD_INR
    EVENTS = ("query", "stream", "passages")
    FILTER = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND ('
              + " OR ".join(f'jsonPayload.event="{e}"' for e in EVENTS) + f') AND timestamp>="{os.environ["T0"]}"')
    got = subprocess.run(["gcloud", "logging", "read", FILTER, "--project", os.environ["PROJECT"], "--limit", "200",
                          "--format=json"], capture_output=True, text=True, check=True).stdout
    rows = [e["jsonPayload"] for e in json.loads(got or "[]")][::-1]          # Cloud Logging lists the newest first
    for r in rows:
        print(f"{r['event']:8} {r['tenant']:5} tokens {r['tokens_in']:>5} in + {r['tokens_out']:>5} out | "
              f"Rs {(r.get('cost_usd') or 0) * USD_INR:.4f} | answerable {r['answerable']} | {r['model']} | "
              f"{r['prompt_version']} | generate_ms {r.get('generate_ms')}")
    print("rows since T0: " + ", ".join(f"{e} {sum(r['event'] == e for r in rows)}" for e in EVENTS)
          + f" | tokens out {sum(r['tokens_out'] for r in rows):,} | Rs {sum(r.get('cost_usd') or 0 for r in rows) * USD_INR:.4f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_definition),
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
