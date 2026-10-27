"""Lesson 8.4: Architecture: three designs the kit rejected, and the number that would change each

The cell prices the same edit cut both ways at lesson 8.3's embedding price, reads the retention window and its floor from the Makefile and variables.tf, and reads the push lane's limits from eventarc.tf and the worker's deploy script to compute the rewrite bound.

Run order inside this file:
1. Do it: the three thresholds, from the kit's files (source window 28)

Prerequisites: demo_04_architecture_the_path_a_change_takes_station_by_station.
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


def step_01_the_three_thresholds_from_the_kit_s_files(session):
    """Run Do it: the three thresholds, from the kit's files at this checkpoint.

    The cell prices the same edit cut both ways at lesson 8.3's embedding price, reads the retention window and its floor from the Makefile and variables.tf, and reads the push lane's limits from eventarc.tf and the worker's deploy script to compute the rewrite bound.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. one clause edited: Rs 0.0010 to embed by section, Rs 0.38 by whole-document windows (394 times as much)
    2. retired rows live 30 days (RETENTION_DAYS); the window can be set from 1 to 3650 days, never to zero
    3. rewrites at once that the push lane clears inside 6,600 s of backoff, at 1 s a document: 198,000
    3. rewrites at once that the push lane clears inside 6,600 s of backoff, at 10 s a document: 19,800
    """
    import re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["."]
    from shared import documind_corpus as dc
    from shared.prices import USD_INR
    src = lambda p: open(p, encoding="utf-8").read()
    EMBED_1K = 0.000025                      # text-embedding-005 input, online, per 1,000 characters: lesson 8.3's price, read on 12 October 2026
    v1, v2 = src("evals/corpus/acme/hr_policy_2026.md"), src("evals/demo/hr_policy_2026_v2.md")
    doc = lambda text: {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://b/acme/hr_policy_2026.md", "text": text}
    held = {c["chunk_hash"] for c in dc.chunk_document(doc(v1), "acme")}
    by_section = sum(len(c["text"]) for c in dc.chunk_document(doc(v2), "acme") if c["chunk_hash"] not in held)
    w_held = {dc.chunk_hash(t) for t in dc.windows(v1)}
    by_window = sum(len(t) for t in dc.windows(v2) if dc.chunk_hash(t) not in w_held)
    print(f"1. one clause edited: Rs {by_section / 1000 * EMBED_1K * USD_INR:.4f} to embed by section, "
          f"Rs {by_window / 1000 * EMBED_1K * USD_INR:.2f} by whole-document windows ({by_window / by_section:,.0f} times as much)")
    tf = src("terraform/variables.tf").split('variable "retention_days" {', 1)[1]
    low, high = re.search(r"retention_days >= (\d+) && var.retention_days <= (\d+)", tf).groups()
    days = re.search(r'^RETENTION_DAYS\s+\?= (\d+)', src("Makefile"), re.M).group(1)
    print(f"2. retired rows live {days} days (RETENTION_DAYS); the window can be set from {low} to {high} days, never to zero")
    ev, run = src("terraform/eventarc.tf"), src("commands/lesson-12.5.sh")
    attempts = int(re.search(r"max_delivery_attempts = (\d+)", ev).group(1))
    longest = int(re.search(r'maximum_backoff = "(\d+)s"', ev).group(1))
    flight = int(re.search(r"--max-instances=(\d+)", run).group(1)) * int(re.search(r"--concurrency=(\d+)", run).group(1))
    bound = (attempts - 1) * longest            # the waits between twelve deliveries, none longer than the longest backoff
    for t in (1, 10):
        print(f"3. rewrites at once that the push lane clears inside {bound:,} s of backoff, at {t} s a document: {flight * bound // t:,}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_the_three_thresholds_from_the_kit_s_files),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
