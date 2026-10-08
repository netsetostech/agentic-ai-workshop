"""Lesson 6.2: Four asks: a miss, two hits and a paraphrase

One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

Run order inside this file:
1. Four asks: a miss, two hits and a paraphrase (source window 25)
2. Four asks: a miss, two hits and a paraphrase (source window 27)

Prerequisites: demo_05_the_answer_cache_a_candidate_that_remembers_answers.
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


# Original CLI workflow for step_01_four_asks_a_miss_two_hits_and_a_paraphrase.
COMMANDS_01 = """ask91 "$CAND" "$Q91"                                   # 1: a miss - retrieved, generated, stored
ask91 "$CAND" "$Q91"                                   # 2: the same words - the exact rung
ask91 "$CAND" "how many days a month can i work remotely"      # 3: other case, no "?" - the same qhash
ask91 "$CAND" "How many days per month am I allowed to work from home?"   # 4: a paraphrase - the near rung, if it is 0.95 close

"""

def step_01_four_asks_a_miss_two_hits_and_a_paraphrase(session):
    """Run Four asks: a miss, two hits and a paraphrase at this checkpoint.

    One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (four asks to the candidate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend vertex cache_hit none     tokens_in  43071  cached_tokens  41259   2590 ms  | Employees may work remotely up to eight days
      backend cache  cache_hit semantic tokens_in      0  cached_tokens      0    182 ms  | Employees may work remotely up to eight days
      backend cache  cache_hit semantic tokens_in      0  cached_tokens      0    176 ms  | Employees may work remotely up to eight days
      backend vertex cache_hit none     tokens_in  43053  cached_tokens  41259   2720 ms  | Employees may work remotely up to eight days
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_four_asks_a_miss_two_hits_and_a_paraphrase(session):
    """Run Four asks: a miss, two hits and a paraphrase at this checkpoint.

    One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same rows cell, now with the candidate's).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 00041-kqz  vertex  in   1812  cached      0  Rs 0.4937   2410 ms
      00041-kqz  vertex  in  43071  cached  41259  Rs 1.0197   2650 ms
      00044-rtv  vertex  in  43071  cached  41259  Rs 1.0197   2590 ms
      00044-rtv  cache   in      0  cached      0  Rs 0.0000    182 ms
      00044-rtv  cache   in      0  cached      0  Rs 0.0000    176 ms
      00044-rtv  vertex  in  43053  cached  41259  Rs 1.0085   2720 ms
    """
    import json, os, subprocess
    f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
         f'AND jsonPayload.tenant="acme" AND timestamp>="{os.environ["SINCE91"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    for e in json.loads(out or "[]"):
        j, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
        print(f"  {rev[-9:]}  {j['model_backend']:6}  in {j['tokens_in']:>6}  cached {j['cached_tokens']:>6}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_four_asks_a_miss_two_hits_and_a_paraphrase),
        ('source_27', step_02_four_asks_a_miss_two_hits_and_a_paraphrase),
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
