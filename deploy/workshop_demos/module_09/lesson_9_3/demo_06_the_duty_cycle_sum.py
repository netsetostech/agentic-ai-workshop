"""Lesson 9.3: The duty-cycle sum

Do it

Run order inside this file:
1. Do it (source window 22)

Prerequisites: demo_05_the_lane_s_cluster_inspected.
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


# Original CLI workflow for step_01_the_duty_cycle_sum.
COMMANDS_01 = """BURSTS=8 MINUTES=30 DAYS=22 python3 - <<'PY'      # your own pattern: change the three numbers
import os
BURSTS, MINUTES, DAYS = (int(os.environ.get(k, d)) for k, d in (("BURSTS", 8), ("MINUTES", 30), ("DAYS", 22)))
IDLE, HOURS, INR = 10, 730, 85                    # Cloud Run keeps an idle GPU instance up to 10 minutes; a month; rupees a dollar
RUN = (0.0001867 + 8 * 0.000018 + 32 * 0.000002) * 3600     # Cloud Run, us-central1: L4, 8 vCPU, 32 GiB, USD an hour
GKE = {"us-central1": (0.853624312, 0.067, 0.003, 0.00035),   # g2-standard-8, then Autopilot's L4, vCPU and GiB premiums, USD an hour
       "asia-south1": (0.888583031, 0.0804737, 0.0036033, 0.00042)}
gap = 24 * 60 / BURSTS - MINUTES
lives = min(24 * 60, BURSTS * (MINUTES + min(IDLE, max(gap, 0))))    # minutes a day an instance is up, and billed
hours = lives / 60 * DAYS
print(f"your pattern: {BURSTS} bursts a day of {MINUTES} minutes, on {DAYS} days a month")
print(f"Cloud Run, on demand: each burst, then up to {IDLE} idle minutes - an instance lives {lives:.0f} minutes a day")
print(f"  the duty-cycle sum: {lives:.0f} min x {DAYS} days = {hours:.1f} hours of {HOURS} ({hours / HOURS:.1%}) x ${RUN:.4f} = "
      f"${hours * RUN:,.2f}, Rs {hours * RUN * INR:,.0f} a month")
print(f"GKE Autopilot, always on, for all {HOURS} hours:")
least = None
for region, (node, l4, vcpu, gib) in GKE.items():
    hour = node + l4 + 8 * vcpu + 32 * gib
    month, fee_month = hour * HOURS * INR, (hour + 0.10) * HOURS * INR
    least = min(least or month, month)
    print(f"  {region:12} ${hour:.4f} an hour (node {node:.4f} + L4 {l4:.4f} + 8 vCPU {8 * vcpu:.4f} + 32 GiB {32 * gib:.4f}): "
          f"Rs {month:,.0f}; with the $0.10 cluster fee, Rs {fee_month:,.0f}")
    print(f"  {'':12} cheaper than Cloud Run above {hour / RUN:.1%} of the month ({(hour + 0.10) / RUN:.1%} with the fee)")
print(f"at {hours / HOURS:.1%}: " + (f"Cloud Run is cheaper - Rs {hours * RUN * INR:,.0f} against Rs {least:,.0f} for the cheapest GKE line"
      if hours * RUN * INR < least else "GKE is cheaper: an instance that lives this long is a pod that never sleeps"))
PY

"""

def step_01_the_duty_cycle_sum(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (arithmetic only; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: your pattern: 8 bursts a day of 30 minutes, on 22 days a month
    Cloud Run, on demand: each burst, then up to 10 idle minutes - an instance lives 320 minutes a day
      the duty-cycle sum: 320 min x 22 days = 117.3 hours of 730 (16.1%) x $1.4209 = $166.72, Rs 14,171 a month
    GKE Autopilot, always on, for all 730 hours:
      us-central1  $0.9558 an hour (node 0.8536 + L4 0.0670 + 8 vCPU 0.0240 + 32 GiB 0.0112): Rs 59,309; with the $0.10 cluster fee, Rs 65,514
                   cheaper than Cloud Run above 67.3% of the month (74.3% with the fee)
      asia-south1  $1.0113 an hour (node 0.8886 + L4 0.0805 + 8 vCPU 0.0288 + 32 GiB 0.0134): Rs 62,753; with the $0.10 cluster fee, Rs 68,958
                   cheaper 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_the_duty_cycle_sum),
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
