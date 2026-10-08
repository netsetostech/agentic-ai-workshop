"""Lesson 9.4: The table's maths, read

Do it

Run order inside this file:
1. Do it (source window 9)
2. Do it (source window 11)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_table_s_maths_read.
COMMANDS_01 = """python services/slm/compare_backends.py --selftest

"""

def step_01_the_table_s_maths_read(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the script's own check of its maths; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend            rows  groundedness  cite-precision   p95 ms  Rs/1k queries
    ------------------------------------------------------------------------------
    documind-general      3         0.500           0.667     1200          42.00
    documind-slm          3         1.000           0.500     3100        1951.33

    selftest OK - groundedness excludes refusal rows, precision is per cited chunk, p95 is the 95th latency, Rs/1k is mean cost x 1000
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_table_s_maths_read(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the script, the tools module and config.yaml; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a row asks the gateway for a route by name: documind-general, documind-slm (make compare's default)
      its context: the citations' quotes of the API's own answer - retrieve() posts to /v1/query
      if that answer takes more than 20 s, the row's context is empty, and only the log says so
    from the gateway's reply a row keeps the answer and the token counts, and reads neither the model that answered nor x-litellm-response-cost
    its price is the script's own, by the route asked (USD a million tokens, in / out):
      documind-general    table  1.50 /  7.50   config.yaml  1.50 /  7.50
      documind-reasoning  table  1.50 /  7.50   config.yaml  2.00 / 12.00  <- no entry: documind-general's
      documind-slm    
    """
    import re
    rd = lambda p: open(p, encoding="utf-8").read()
    cb, dt, cfg, mk = rd("services/slm/compare_backends.py"), rd("shared/documind_tools.py"), rd("services/litellm/config.yaml"), rd("Makefile")
    ask = cb.split("def ask(", 1)[1].split("\ndef ", 1)[0]
    backends = re.search(r"BACKENDS:-([\w,-]+)\}", mk).group(1)
    print(f"a row asks the gateway for a route by name: {backends.replace(',', ', ')} (make compare's default)")
    print("  its context: the citations' quotes of the API's own answer - retrieve() posts to "
          + re.search(r'requests\.post\(f"\{RAG_API_URL\}(/v1/\w+)"', dt).group(1))
    wait = re.search(r'"RAG_TIMEOUT_S", "(\d+)"', dt).group(1)
    print(f"  if that answer takes more than {wait} s, the row's context is empty, and only the log says so")
    reads = [k for k in ("model", "x-litellm-response-cost") if f'"{k}")' in ask or f'["{k}"]' in ask]
    print("from the gateway's reply a row keeps the answer and the token counts, and reads "
          + (", ".join(reads) if reads else "neither the model that answered nor x-litellm-response-cost"))
    prices = {k: (float(a), float(b)) for k, a, b in re.findall(r'"(documind-[a-z]+)": \(([\d.]+), ([\d.]+)\)', cb)}
    rates, group = {}, None
    for line in cfg.splitlines():
        m = re.match(r"  - model_name: (\S+)", line)
        group = m.group(1) if m else group
        m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
        if m:
            rates.setdefault(group, {})[m.group(1)] = float(m.group(2)) * 1e6
    print("its price is the script's own, by the route asked (USD a million tokens, in / out):")
    for route, r in rates.items():
        pin, pout = prices.get(route, prices["documind-general"])
        note = "" if route in prices else "  <- no entry: documind-general's"
        print(f"  {route:19} table {pin:5.2f} / {pout:5.2f}   config.yaml {r['input']:5.2f} / {r['output']:5.2f}{note}")
    n = 20
    print(f"p95 on {n} rows is sorted row {max(0, int(round(0.95 * n)) - 1) + 1} of {n}: the slowest row never shows")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_table_s_maths_read),
        ('source_11', step_02_the_table_s_maths_read),
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
