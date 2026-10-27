"""Offline check of the gateway's guardrail block (services/litellm/config.yaml), as the image's LiteLLM reads it.

LiteLLM v1.80.5 (the Dockerfile's base) loads a custom guardrail from `guardrail: <file>.<Class>`, the file beside the
config, and refuses any other name it has not registered at start-up (litellm/proxy/guardrails/guardrail_registry.py).
It runs the guardrail on every request only when `default_on` is true; otherwise only on a request that names it. On
22 October 2026 the block said `guardrail: custom` with a `callback_class`, and lesson 9.1's first deployed gateway
exited at start-up: ValueError: Unsupported guardrail: custom. Stdlib only: the block is read as text.
"""
from pathlib import Path
import re
import unittest

LITELLM = Path(__file__).resolve().parents[2] / "services" / "litellm"


def guardrail_block() -> str:
    """The lines under the top-level `guardrails:` key, up to the next top-level key."""
    lines = (LITELLM / "config.yaml").read_text(encoding="utf-8").splitlines()
    start = lines.index("guardrails:") + 1
    end = next((i for i in range(start, len(lines)) if lines[i] and not lines[i][0].isspace() and not lines[i].startswith("#")),
               len(lines))
    return "\n".join(lines[start:end])


class TheRouterGuardrail(unittest.TestCase):
    def setUp(self):
        self.block = guardrail_block()

    def test_it_is_loaded_by_file_and_class_from_beside_the_config(self):
        name = re.search(r"^\s+guardrail:\s*(\S+)\s*$", self.block, re.M).group(1)
        self.assertRegex(name, r"^\w+\.\w+$", "an unregistered name without a dot stops the gateway at start-up")
        file, cls = name.split(".")
        self.assertRegex((LITELLM / f"{file}.py").read_text(encoding="utf-8"), rf"(?m)^class {cls}\(CustomGuardrail\):")
        docker = (LITELLM / "Dockerfile").read_text(encoding="utf-8")
        copies = [line.split()[1:-1] for line in docker.splitlines() if line.startswith("COPY ") and line.rstrip().endswith("./")]
        self.assertIn(f"{file}.py", sum(copies, []), "the image copies the guardrail's file into /app")
        self.assertIn(["config.yaml"], copies, "and the config beside it")
        self.assertNotIn("callback_class", self.block)

    def test_it_runs_before_every_call(self):
        self.assertRegex(self.block, r'(?m)^\s+mode:\s*"?pre_call"?\s*$')
        self.assertRegex(self.block, r"(?m)^\s+default_on:\s*true\s*$", "without it a request that names no guardrail is never routed")


if __name__ == "__main__":
    unittest.main()
