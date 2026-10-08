"""Finish this lesson after success or failure; keep all saved evidence.

Summary: call the cleanup section files in their documented restoration order.
Example: Run this file once at lesson end, including after an earlier failure.
It attempts remaining restorations and closes the session only after success.
"""
from workshop_helpers.cleanup import finish_lesson
from workshop_helpers.session import DemoSession

REPEAT = False


def demonstrate(session):
    """Restore the mapped cleanup sections and the original lesson settings.

    Example: main() opens the saved run and passes its session here.
    """
    finish_lesson(session)


def main():
    """Open this lesson's saved state with the IDE interpreter.

    Example: Run setup/finish.py after the numbered examples, or after failure.
    """
    with DemoSession(__file__, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == '__main__':
    main()
