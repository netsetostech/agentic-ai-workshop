"""Lesson 3.9: Cost: a claim, a month and a floor, at 1k, 10k and 100k claims

This is the table as a script you can keep: component 6's COST-MODEL.md starts from its output. It reads the rates and the rupee rate from the kit, rebuilds a claim's budget with the kit's own function, and carries the three prices the kit does not hold, the embedding, the ranking query and the judge's autorater, as constants with their date. The ceiling is what no claim may exceed; the average is what claims cost. make usage reads the last day's usage rows, and its table by model and backend carries each model's answers and tokens; the second line divides them. Your average depends on what was asked on your lane, so it is yours, not the author's.

Run order inside this file:
1. Do it: the cost model as a script (source window 34)
2. Do it: your lane's tokens a claim, from the rows (source window 36)

Prerequisites: demo_05_failure_modes_four_the_kit_reproduces_and_which_ones_the_alerts_see.
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

    This is the table as a script you can keep: component 6's COST-MODEL.md starts from its output. It reads the rates and the rupee rate from the kit, rebuilds a claim's budget with the kit's own function, and carries the three prices the kit does not hold, the embedding, the ranking query and the judge's autorater, as constants with their date.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a claim at the ceiling, 8,000 tokens in and 2,048 out: model $0.02736, retrieval $0.00110, judge $0.000274
      1,000 claims, SMALL : model Rs 2,326 + retrieval Rs 94 + judge Rs 23 + floor Rs 32,157 = Rs 34,600 ($407), Rs 34.60 a claim
      1,000 claims, MEDIUM: model Rs 2,326 + retrieval Rs 94 + judge Rs 23 + floor Rs 81,100 = Rs 83,543 ($983), Rs 83.54 a claim
     10,000 claims, SMALL : model Rs 23,256 + retrieval Rs 935 + judge Rs 233 + floor Rs 32,157 = Rs 56,581 ($666), Rs 5.66 a claim
     10,000 claims, MEDIUM: model Rs 23,256 + retrieval Rs 935 + judge Rs 233 + floor Rs 81,100 = Rs 1,05,524 ($1,241), Rs 10.55 a claim
    100,000 claims, SMALL : model Rs 2,32,560 + retrieval Rs 9,350 + judge Rs 2,326 
    """
    import ast, re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/rag-api"]
    from shared.prices import PRICES, USD_INR                      # the kit's rates and its rupee rate
    from context_budget import TokenBudget, estimate_tokens
    src = lambda p: open(p, encoding="utf-8").read()
    cfg = src("services/rag-api/config.py")
    K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src("services/rag-api/generator.py")).body
         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
    CLAIM = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
    b = TokenBudget.fit(int(re.search(r"max_context_tokens: int = (\d+)", cfg).group(1)), f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {CLAIM}",
                        estimate_tokens, answer=int(re.search(r"max_answer_tokens: int = (\d+)", cfg).group(1)))
    r_in, r_out = PRICES["gemini-3.6-flash"]
    # Google's list prices the kit does not hold, read on 8 October 2026 - verify before you rely on them
    EMBED_1K, RANK_1K, J_IN, J_OUT = 0.000025, 1.00, 0.15, 0.60   # per 1,000 characters; per 1,000 queries; Gemini 2.0 Flash per 1M
    FLOOR = {"SMALL": 32157, "MEDIUM": 81100}                # the lane's standing cost a month, Rs (lessons 0.1 and 0.4)
    JUDGED = 0.05                                                     # the design's choice: the judge reads one claim in twenty
    model = (b.input_total * r_in + b.answer * r_out) / 1e6
    retrieval = 4000 / 1000 * EMBED_1K + RANK_1K / 1000                 # the longest claim QueryRequest takes; one ranking query
    judge = JUDGED * 2 * ((b.input_total + b.answer) * J_IN + b.answer * J_OUT) / 1e6
    
    
    def inr(x):                                                          # whole rupees, grouped the Indian way: 2,76,393
        """Format a rupee amount as whole rupees, rounded half up and grouped the Indian way (2,76,393).
        
        Example: inr(parts[0])
        """
        s = str(int(x + 0.5))
        head, tail = s[:-3], s[-3:]
        while len(head) > 2:
            head, tail = head[:-2], head[-2:] + "," + tail
        return f"{head},{tail}" if head else tail
    
    
    print(f"a claim at the ceiling, {b.input_total:,} tokens in and {b.answer:,} out: model ${model:.5f}, retrieval ${retrieval:.5f}, judge ${judge:.6f}")
    for q in (1_000, 10_000, 100_000):
        parts = [int(q * usd * USD_INR + 0.5) for usd in (model, retrieval, judge)]       # whole rupees, half up
        for shard, floor in FLOOR.items():
            total = sum(parts) + floor
            print(f"{q:>7,} claims, {shard:6}: model Rs {inr(parts[0])} + retrieval Rs {inr(parts[1])} + judge Rs {inr(parts[2])}"
                  f" + floor Rs {inr(floor)} = Rs {inr(total)} (${total / USD_INR:,.0f}), Rs {total / q:.2f} a claim")

# Original CLI workflow for step_02_your_lane_s_tokens_a_claim_from_the_rows.
COMMANDS_02 = """make usage PROJECT=$PROJECT HOURS=24 | sed -n '/^by model and backend/,/^$/p' | tee /tmp/usage39.txt
awk '$2 == "vertex" && $3 > 0 {printf "%s: %d answers, %.0f tokens in and %.0f out each, p95 %s ms\\n", $1, $3, $4 / $3, $5 / $3, $8}' /tmp/usage39.txt

"""

def step_02_your_lane_s_tokens_a_claim_from_the_rows(session):
    """Run Do it: your lane's tokens a claim, from the rows at this checkpoint.

    The ceiling is what no claim may exceed; the average is what claims cost. make usage reads the last day's usage rows, and its table by model and backend carries each model's answers and tokens; the second line divides them. Your average depends on what was asked on your lane, so it is yours, not the author's.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: one read of the last day's usage rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/usage_tokens.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_the_cost_model_as_a_script),
        ('source_36', step_02_your_lane_s_tokens_a_claim_from_the_rows),
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
