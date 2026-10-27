"""Lesson 3.1: Five calls to /v1/query, judged by the gate's rule

Now the real model, through the API. /v1/query is the request make eval-live sends for every golden row, and the bench's kit arm at LOW reproduces it, so these five answers are five more draws from what step 7 measures. The cell asks the way the gate asks, run_eval.ask() with top_k 6 as documind-ui-sa, and judges each reply with row_verdict() after reading the ledger's current versions from GET /v1/sources, as the gate does. It starts with /version, which names the model, the prompt version and the answer cache. The cache is off unless a deploy turned it on (SEMANTIC_CACHE, lesson 6.2); with it on, a repeated question can come back from the cache with no model call, and the five would not be five draws.

Run order inside this file:
1. Definition (source window 26)

Prerequisites: demo_05_the_bench_for_rs_0_its_tests_and_a_scripted_model.
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

    Now the real model, through the API. /v1/query is the request make eval-live sends for every golden row, and the bench's kit arm at LOW reproduces it, so these five answers are five more draws from what step 7 measures. The cell asks the way the gate asks, run_eval.ask() with top_k 6 as documind-ui-sa, and judges each reply with row_verdict() after reading the ledger's current versions from GET /v1/sources, as the gate does. It starts with /version, which names the model, the prompt version and the answer cache. The cache is off unless a deploy turned it on (SEMANTIC_CACHE, lesson 6.2); with it on, a repeated question can come back from the cache with no model call, and the five would not be five draws.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (five /v1/query answers at LOW: about Rs 1.01 of input by the kit's count, at most Rs 7.54 with every answer at the 2,048-token cap).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_five.txt]
    """
    import json, os, re, subprocess, sys, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["evals", "."]
    import run_eval
    from route_eval import rate
    from shared.prices import USD_INR, usd
    API, PROJECT = os.environ["API"], os.environ["PROJECT"]
    ROW = next(r for r in run_eval.load_golden() if r["id"] == "jn-03")
    TOKEN = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                            f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                           capture_output=True, text=True, check=True).stdout.strip()
    version = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}/version", headers={"Authorization": f"Bearer {TOKEN}"}),
                                               timeout=30))
    print(f"/version: {version['generator_model']} | prompt {version['prompt']} | semantic_cache {version['semantic_cache']}")
    current = run_eval.fetch_current_shas(API, ROW["tenant"], TOKEN)          # the ledger's current versions, as the gate reads them
    if current is None:
        print("[info] GET /v1/sources was unavailable: the version check is skipped")
    manifest = run_eval.load_manifest_objects()
    corpus = re.sub(r"\s+", " ", run_eval.haystack(run_eval.load_corpus(), ROW["tenant"]))
    said, cited, passed, rupees = [], [], 0, 0.0
    for run in range(1, 6):
        status, body, ms = run_eval.ask(API, ROW["question"], ROW["tenant"], "eval@documind.in", TOKEN)   # the gate's own request
        v = run_eval.row_verdict(ROW, status, body, current, manifest, corpus)                               # and its own rule
        if v["outcome"] != "ok":
            print(f"run {run}: {v['outcome']} | {v['why']}")
            continue
        passed += v["pass"]
        said.append(" ".join(body["answer"].split()))
        cited.append(frozenset(c["chunk_id"] for c in body["citations"]))
        rs = usd(body["model"], body["tokens_in"], body["tokens_out"]) * USD_INR       # tokens_out: the answer and the thinking
        rupees += rs
        print(f"run {run}: {'pass' if v['pass'] else 'FAIL'} | tokens {body['tokens_in']} in + {body['tokens_out']} out | "
              f"generate_ms {body['stages'].get('generate_ms')} | cache {body['cache_hit']} | Rs {rs:.4f}"
              + (f" | {v['why']}" if v["why"] else ""))
        for c in body["citations"]:
            print(f"       cites {c['source_uri'].rsplit('/', 1)[-1]}#{c['chunk_id'].rsplit('#', 1)[-1]}: {c['quote'][:60]!r}")
        print(f"       {said[-1][:240]}")
    print(f"distinct answers {len(set(said))} of {len(said)} | cite sets {len(set(cited))} of {len(said)} | "
          f"pass {rate(passed, 5)} | Rs {rupees:.4f} for the five")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_definition),
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
