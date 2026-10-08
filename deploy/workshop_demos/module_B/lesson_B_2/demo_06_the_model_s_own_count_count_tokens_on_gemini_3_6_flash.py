"""Lesson B.2: The model's own count: count_tokens on gemini-3.6-flash

Do it: three texts, the model's count, and the rupee line

Run order inside this file:
1. Do it: three texts, the model's count, and the rupee line (source window 17)

Prerequisites: demo_05_the_rupee_line_tokens_priced_with_the_kit_s_prices.
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


def step_01_three_texts_the_model_s_count_and_the_rupe(session):
    """Run Do it: three texts, the model's count, and the rupee line at this checkpoint.

    Do it: three texts, the model's count, and the rupee line

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv, after the setup's Gemini block (a Python cell; three count_tokens calls, no charge).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/count_tokens.txt]
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google import genai
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")   # Gemini 3 is served from global, as in the kit
    MODEL = "gemini-3.6-flash"
    PRICES = {MODEL: (1.50, 7.50)}     # shared/prices.py, as in step 5
    USD_INR = 85
    def price(tokens_in, tokens_out=0):
        """Dollars, then rupees, as in step 5.
        
        Example: price(n)
        """
        usd_in, usd_out = PRICES[MODEL]
        usd = (tokens_in * usd_in + tokens_out * usd_out) / 1_000_000
        return usd, usd * USD_INR
    TEXTS = {
        "the question": "What is the notice period for a confirmed E3?",
        "the same in Hindi": "पुष्टि किए गए E3 कर्मचारी की सूचना अवधि क्या है?",
        "an Indian amount": "Purchases up to Rs 2,00,000 are approved by the function head.",
    }
    for name, text in TEXTS.items():
        n = client.models.count_tokens(model=MODEL, contents=text).total_tokens   # the model's own count: no charge
        usd, inr = price(n)
        print(f"{name:17} {len(text):2} characters  estimate {max(1, len(text) // 4):2}  counted {n:2}  "
              f"as input ${usd:.6f} = Rs {inr:.4f} at {USD_INR}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_three_texts_the_model_s_count_and_the_rupe),
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
