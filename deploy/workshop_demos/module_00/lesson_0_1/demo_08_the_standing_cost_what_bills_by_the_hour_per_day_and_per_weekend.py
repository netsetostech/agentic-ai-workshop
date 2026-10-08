"""Lesson 0.1: The standing cost: what bills by the hour, per day and per weekend

The same table as a Python cell: the hourly prices, the kit's rate and the kit's budget, then the sums. It touches no account and no network, so it runs anywhere a python does, Cloud Shell included.

Run order inside this file:
1. Run the arithmetic yourself, Rs 0 (source window 27)

Prerequisites: demo_06_the_budget_an_alert_on_the_billing_account.
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


def step_01_run_the_arithmetic_yourself_rs_0(session):
    """Run Run the arithmetic yourself, Rs 0 at this checkpoint.

    The same table as a Python cell: the hourly prices, the kit's rate and the kit's budget, then the sums. It touches no account and no network, so it runs anywhere a python does, Cloud Shell included.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell (a Python cell, arithmetic only: no network, no credentials, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: small  shard: USD 0.5182 an hour = Rs 1,057 a day, Rs 2,114 a weekend, Rs 32,157 a month
                  the budget's 50% (Rs 2,500) after 57 hours of this alone
    medium shard: USD 1.3070 an hour = Rs 2,666 a day, Rs 5,333 a weekend, Rs 81,100 a month
                  the budget's 50% (Rs 2,500) after 23 hours of this alone
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    # USD an hour, Mumbai list prices; sizes from the kit's Terraform (see the table above)
    INDEX = {"small": 0.1126804, "medium": 0.9014432}   # one replica, e2-standard-2 or e2-standard-16
    REST = {
        'Spanner graph instance': 0.1722,
        'Cloud SQL, two instances': 0.030789,
        'GKE cluster fee': 0.1,
        'GKE lab node': 0.082457,
        'Serverless VPC Access connector': 0.020121,
    }
    USD_INR, BUDGET = 85, 5000   # the kit's rate (shared/prices.py) and BUDGET_AMOUNT (Makefile)
    for shard, index in INDEX.items():
        hourly = index + sum(REST.values())
        rs = lambda hours: round(hourly * hours * USD_INR)
        print(f"{shard:6} shard: USD {hourly:.4f} an hour = Rs {rs(24):,} a day, Rs {rs(48):,} a weekend, Rs {rs(730):,} a month")
        print(f"              the budget's 50% (Rs {BUDGET * 50 // 100:,}) after {BUDGET * 50 / 100 / (hourly * USD_INR):.0f} hours of this alone")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_run_the_arithmetic_yourself_rs_0),
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
