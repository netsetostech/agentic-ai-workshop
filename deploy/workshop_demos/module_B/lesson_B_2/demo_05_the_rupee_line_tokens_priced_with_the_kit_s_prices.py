"""Lesson B.2: The rupee line: tokens priced with the kit's prices

Do it: the golden question's rupee line, Rs 0

Run order inside this file:
1. Do it: the golden question's rupee line, Rs 0 (source window 13)

Prerequisites: demo_04_the_kit_s_two_estimates_against_plain_character_counts.
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


def step_01_the_golden_question_s_rupee_line_rs_0(session):
    """Run Do it: the golden question's rupee line, Rs 0 at this checkpoint.

    Do it: the golden question's rupee line, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, arithmetic only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 'What is the notice period for a confirmed E3?': 45 characters, about 11 tokens by the estimate
    as input to gemini-3.6-flash: 11 x $1.50 per 1M = $0.000017 = Rs 0.0014 at 85, 0.14 paise
    the same 11 tokens as output: $0.000082 = Rs 0.0070, at 5 times the input rate
    a lakh such questions as input: Rs 140.25
    """
    MODEL = "gemini-3.6-flash"
    PRICES = {MODEL: (1.50, 7.50)}     # USD per 1M tokens, input and output: shared/prices.py, the standard price
    USD_INR = 85                       # shared/prices.py: the course-wide rate
    def price(tokens_in, tokens_out=0):
        """Dollars, then rupees: the arithmetic of the kit's usd() and cost.price(), without the cache.
        
        Example: price(n)
        """
        usd_in, usd_out = PRICES[MODEL]
        usd = (tokens_in * usd_in + tokens_out * usd_out) / 1_000_000
        return usd, usd * USD_INR
    Q = "What is the notice period for a confirmed E3?"
    n = max(1, len(Q) // 4)            # the API's estimate: no call made yet
    usd, inr = price(n)
    print(f"{Q!r}: {len(Q)} characters, about {n} tokens by the estimate")
    print(f"as input to {MODEL}: {n} x ${PRICES[MODEL][0]:.2f} per 1M = ${usd:.6f} = Rs {inr:.4f} at {USD_INR}, {inr * 100:.2f} paise")
    usd_o, inr_o = price(0, n)
    print(f"the same {n} tokens as output: ${usd_o:.6f} = Rs {inr_o:.4f}, at {PRICES[MODEL][1] / PRICES[MODEL][0]:.0f} times the input rate")
    print(f"a lakh such questions as input: Rs {inr * 100_000:.2f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_golden_question_s_rupee_line_rs_0),
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
