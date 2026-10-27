"""Lesson 3.9: Architecture: three designs rejected, and the number that would change each

The cell rebuilds a claim's budget with the kit's own function, reads the cache's floor and its read rate from the kit, measures each tenant's corpus with the kit's estimate, reads the policies make roster writes, and prices the judge on every claim. Four prices come from Google's pages, dated in the cell: the cache's storage, the embedding, the ranking query and the judge's default autorater.

Run order inside this file:
1. Do it: the three thresholds, from the kit's files (source window 22)

Prerequisites: demo_03_architecture_the_path_a_claim_takes_station_by_station.
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

    The cell rebuilds a claim's budget with the kit's own function, reads the cache's floor and its read rate from the kit, measures each tenant's corpus with the kit's estimate, reads the policies make roster writes, and prices the judge on every claim. Four prices come from Google's pages, dated in the cell: the cache's storage, the embedding, the ranking query and the judge's default autorater.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a cache would replace $0.01284 a claim: 7,825 chunk tokens at the ceiling, one embedding, one ranking query
      1,000 claims a month: a cached corpus is cheaper below 14,588 tokens; no cache exists below 4,096
     10,000 claims a month: a cached corpus is cheaper below 57,567 tokens; no cache exists below 4,096
    100,000 claims a month: a cached corpus is cheaper below 81,612 tokens; no cache exists below 4,096
    acme    485,430 tokens: Rs 30,121 a month to keep it cached, Rs 6.19 a claim to read it
    globex   43,184 tokens: Rs  2,680 a month to keep it cached, Rs 0.55 a claim to read it
    zeta    287,517 tokens: Rs 17,840 a month to keep it cached, Rs 3.67 a claim to read it
    acme    data_region any: a w
    """
    import ast, re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "evals", "services/rag-api"]
    from shared.prices import PRICES, USD_INR
    from context_budget import TokenBudget, estimate_tokens
    from run_eval import load_corpus
    src = lambda p: open(p, encoding="utf-8").read()
    cfg = src("services/rag-api/config.py")
    K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src("services/rag-api/generator.py")).body
         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
    CLAIM = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
    b = TokenBudget.fit(int(re.search(r"max_context_tokens: int = (\d+)", cfg).group(1)), f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {CLAIM}",
                        estimate_tokens, answer=int(re.search(r"max_answer_tokens: int = (\d+)", cfg).group(1)))
    r_in = PRICES["gemini-3.6-flash"][0] / 1e6
    cached = float(re.search(r"cached_tokens \* usd_in \* ([\d.]+)", src("services/rag-api/cost.py")).group(1))
    floor = int(re.search(r"MIN_CACHE_TOKENS = ([\d_]+)", src("services/rag-api/cache_manager.py")).group(1).replace("_", ""))
    # Google's prices the kit does not hold, read on 8 October 2026 - verify: cache storage, embeddings, ranking, the judge
    STORE, EMBED, RANK, J_IN, J_OUT = 0.000001, 4000 / 1000 * 0.000025, 1.00 / 1000, 0.15, 0.60
    replaced = b.chunks * r_in + EMBED + RANK         # what a cache replaces per claim: the chunks at the ceiling, the embedding, the ranking
    print(f"a cache would replace ${replaced:.5f} a claim: {b.chunks:,} chunk tokens at the ceiling, one embedding, one ranking query")
    for q in (1_000, 10_000, 100_000):
        print(f"{q:>7,} claims a month: a cached corpus is cheaper below {replaced / (cached * r_in + STORE * 730 / q):>6,.0f} tokens;"
              f" no cache exists below {floor:,}")
    for t, docs in load_corpus().items():
        n = sum(estimate_tokens(text) for text in docs.values())
        print(f"{t:7} {n:>7,} tokens: Rs {n * STORE * 730 * USD_INR:>6,.0f} a month to keep it cached, Rs {n * cached * r_in * USD_INR:.2f} a claim to read it")
    for t, region in ast.literal_eval(re.search(r"policies = (\[.*?\])", src("commands/lane.py")).group(1)):
        print(f"{t:7} data_region {region:3}: " + ("its text stays on the kit's own rows: a web search is refused" if region == "in"
                                                   else "a web search only once the tenant has agreed to it"))
    judge = 2 * ((b.input_total + b.answer) * J_IN + b.answer * J_OUT) / 1e6     # two metrics, the default autorater, at the ceiling
    print(f"a judge on every claim: Rs {judge * USD_INR:.2f} a claim, Rs {judge * USD_INR * 100_000:,.0f} a month at 100k; one in twenty, Rs {judge * USD_INR * 5_000:,.0f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_the_three_thresholds_from_the_kit_s_files),
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
