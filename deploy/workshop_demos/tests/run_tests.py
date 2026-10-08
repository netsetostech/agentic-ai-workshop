"""Run offline helper regressions; this runner never selects a cloud demo."""
from pathlib import Path
import unittest


def main():
    """Exit nonzero if any session or planner contract fails."""
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
