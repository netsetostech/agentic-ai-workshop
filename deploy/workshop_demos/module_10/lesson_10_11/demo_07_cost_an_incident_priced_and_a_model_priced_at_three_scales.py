"""Lesson 10.11: Cost: an incident priced, and a model priced at three scales

Component 6's COST-MODEL.md starts from this. The cell reads the rates and the rupee rate from the kit, builds a model's prompt from the kit's own catalog and docstring, prints the plan remediate gives the drill's recording as the model's answer, and fills an hour's window with the recording's own lines at each scale.

Run order inside this file:
1. Do it: the cost model as a script (source window 57)

Prerequisites: demo_06_failure_modes_four_the_kit_reproduces_and_what_pages_for_them.
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


def step_01_the_cost_model_as_a_script(session):
    """Run Do it: the cost model as a script at this checkpoint.

    Component 6's COST-MODEL.md starts from this. The cell reads the rates and the rupee rate from the kit, builds a model's prompt from the kit's own catalog and docstring, prints the plan remediate gives the drill's recording as the model's answer, and fills an hour's window with the recording's own lines at each scale.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the rules: 3 reads at Rs 0 and 0 model calls, at every scale
    a model: 3,241 tokens of rules and runbooks, then the lines; 614 tokens of plan out
        1,000 turns a month:     3 lines an hour,     3 read |  4,016 tokens in | flash Rs  0.90 ($0.0106), flash-lite Rs 0.16 ($0.0019) an incident
       10,000 turns a month:    28 lines an hour,    28 read |  4,564 tokens in | flash Rs  0.97 ($0.0115), flash-lite Rs 0.18 ($0.0021) an incident
      100,000 turns a month:   274 lines an hour,   274 read |  9,945 tokens in | flash Rs  1.66 ($0.0195), flash-lite Rs 0.29 ($0.0034) an incident
    1,000,000 turns a month: 2,740 lines an hour, 2,000 read | 47,701 tokens in | flash Rs  6.47 ($0.0762), flash-lite Rs 1.
    """
    import importlib.util, json, math, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/rag-api"]
    from shared.prices import PRICES, USD_INR                     # the kit's rates and its rupee rate
    from context_budget import estimate_tokens                    # the kit's estimate: four characters a token
    spec = importlib.util.spec_from_file_location("remediate", "commands/remediate.py")
    rm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm)
    catalog = rm.load_catalog()
    rows = rm.runbooks(rm.TF_DIR, catalog)
    state = rm.load_state(rm.KIT / "ops" / "incidents" / "held_model.json")
    state.pop("fixture")
    book = open("ops/runbooks.json", encoding="utf-8").read() + rm.__doc__        # what the rules know, as a prompt
    plan = "\n".join(rm.render(state, rm.diagnose(dict(state), rows, catalog), rows, catalog))   # what it must write
    request, turn = state["lines"][2], state["lines"][5]          # one request line and one chat row, as remediate keeps them
    print(f"the rules: {len(rm.READS)} reads at Rs 0 and 0 model calls, at every scale")
    print(f"a model: {estimate_tokens(book):,} tokens of rules and runbooks, then the lines; {estimate_tokens(plan):,} tokens of plan out")
    for turns in (1_000, 10_000, 100_000, 1_000_000):
        lines = math.ceil(turns / 730 * 2)                        # an hour's window: a request line and a chat row a turn
        read = min(lines, rm.LIMIT)
        s = dict(state, lines=[request, turn] * (read // 2) + [request] * (read % 2))
        tin, tout = estimate_tokens(book) + estimate_tokens(json.dumps(s)), estimate_tokens(plan)
        usd = {m: (tin * PRICES[m][0] + tout * PRICES[m][1]) / 1e6 for m in ("gemini-3.6-flash", "gemini-3.1-flash-lite")}
        print(f"{turns:>9,} turns a month: {lines:>5,} lines an hour, {read:>5,} read | {tin:>6,} tokens in | flash "
              f"Rs {usd['gemini-3.6-flash'] * USD_INR:5.2f} (${usd['gemini-3.6-flash']:.4f}), flash-lite Rs "
              f"{usd['gemini-3.1-flash-lite'] * USD_INR:4.2f} (${usd['gemini-3.1-flash-lite']:.4f}) an incident")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_57', step_01_the_cost_model_as_a_script),
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
