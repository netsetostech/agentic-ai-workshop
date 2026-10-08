"""Lesson 7.5: make smoke-media, green

Do it

Run order inside this file:
1. Do it (source window 25)

Prerequisites: demo_05_the_clip_at_its_second.
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


# Original CLI workflow for step_01_make_smoke_media_green.
COMMANDS_01 = """python -m pip install -q fastmcp==3.4.7      # the gate's MCP legs (lesson 5.2 installed it; safe to repeat)
make smoke-media PROJECT="$PROJECT"

"""

def step_01_make_smoke_media_green(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the gate: a minute or two).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind Module 9 - live smoke test
      api: https://documind-api-NUMBER.asia-south1.run.app
      mcp: https://documind-mcp-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] generate  blob=acme/gen/cd18d3eb6f6dd202ce999de17eb66160.png cached=False
      [PASS] outsider refused  status=403
      [PASS] figure citation  kinds=['figure'] media_url=gs://documind-ai-YOUR-ID-uploads/acme/annual_report_2026_fig  "EMEA's revenue declined, from Rs 96 crore in FY2025 to Rs 91"
      [PASS] media documents  4 of 21 indexed documents are media: ['annual_report_2026_fig3.png', 'inv_2026_0412.png', 'payment_of_bonus_act_1965_p30.png', 'townhall_2026_q1.mp4']
      [PASS] signed PUT
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_make_smoke_media_green),
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
