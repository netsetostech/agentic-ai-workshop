"""Lesson 11.6: The controls, as the kit writes them down

Do it

Run order inside this file:
1. Do it (source window 9)

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


def step_01_the_controls_as_the_kit_writes_them_down(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the controls as the kit writes them down; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: per answer: ROUTING=off on the lane (lesson-12.2.sh). With it on, gemini-3.1-flash-lite labels each question SIMPLE, MEDIUM, COMPLEX, and breakers.choose_model() picks the model:
      spend   SIMPLE                  MEDIUM                  COMPLEX
      0%      gemini-3.1-flash-lite   gemini-3.6-flash        gemini-3.1-pro-preview
      79.9%   gemini-3.1-flash-lite   gemini-3.6-flash        gemini-3.1-pro-preview
      80%     gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
      85%     gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
      100%    gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
      120%    gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6
    """
    import pathlib, re, sys
    sys.path.insert(0, "services/rag-api")
    import breakers                                                     # the kit's own table, run below
    router, deploy, mk = (open(p, encoding="utf-8").read() for p in ("services/rag-api/router.py", "commands/lesson-12.2.sh", "Makefile"))
    budget_tf, off_tf = (open(f"terraform/{f}", encoding="utf-8").read() for f in ("budget.tf", "off.tf"))
    classes = re.findall(r"^    (SIMPLE|MEDIUM|COMPLEX) = ", router, re.M)
    print("per answer: ROUTING=" + re.search(r"ROUTING=\$\{ROUTING-(\w+)\}", deploy).group(1) + " on the lane (lesson-12.2.sh). With it on, "
          + re.search(r'CLASSIFIER_MODEL = "([^"]+)"', router).group(1) + " labels each question " + ", ".join(classes)
          + ", and breakers.choose_model() picks the model:")
    print((f"  {'spend':8}" + "".join(f"{c:24}" for c in classes)).rstrip())
    for pct in (0, 79.9, 80, 85, 100, 120):
        print((f"  {str(pct) + '%':8}" + "".join(f"{breakers.choose_model(c, pct):24}" for c in classes)).rstrip())
    cap = re.search(r"BUDGET_USD=\$\{BUDGET_USD-(\d+)\}", deploy).group(1)
    print(f"  the spend: Firestore budget/<month, UTC>, USD added by every answer, over BUDGET_USD ({cap} on the lane); SPEND_PCT replaces it")
    readers = [p.as_posix() for p in pathlib.Path("services").rglob("*.py") if "BUDGET_FLOOR_PCT" in p.read_text(encoding="utf-8") and p.name != "breakers.py"]
    print(f"  BUDGET_FLOOR_PCT = {breakers.BUDGET_FLOOR_PCT} (the comment's min-instances 0): read by " + (", ".join(readers) or "nothing"))
    rules = [float(t) for t in re.findall(r"threshold_percent = ([\d.]+)", budget_tf)]
    print("per month: " + re.search(r'display_name    = "([^"]+)"', budget_tf).group(1) + ", BUDGET_AMOUNT " + re.search(r"BUDGET_AMOUNT\s+\?= (\d+)", mk).group(1)
          + " in the billing account's currency; it emails at " + ", ".join(f"{r:.0%}" for r in rules[:-1]) + f" and at a {rules[-1]:.0%} forecast")
    loop = off_tf.split("for pair in", 1)[1].split("; do", 1)[0]
    print("per hour: documind-off runs " + re.search(r'schedule    = "([^"]+)"', off_tf).group(1) + " " + re.search(r'time_zone   = "([^"]+)"', off_tf).group(1)
          + " and floors " + ", ".join(re.findall(r"(documind-[\w-]+):", loop)) + " to min-instances 0; make off does the same by hand")
    print("  make gpu-cap: the GPU quota in " + re.search(r"SLM_REGION \?= ([\w-]+)", mk).group(1) + " capped at " + re.search(r"CAP \?= (\d+)", mk).group(1)
          + "; alerts.tf's gpu_left_warm pages when one stays up two hours")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_controls_as_the_kit_writes_them_down),
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
