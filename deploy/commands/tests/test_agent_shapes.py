"""Offline checks for commands/agent_shapes.py: two ADK desks in a ping-pong, and the cap that ends it (workshop
lesson 10.7).

    python -m unittest commands/tests/test_agent_shapes.py -v          # from deploy/

No network, no credential. The first class needs only the standard library: the cap's constants as the file holds them,
the make target (OFFLINE=1 the only mode, through commands/agent-turn.sh's venv), the .PHONY entry and the 888 lines,
mk/README.md's row, both CI lines and the UNOWNED.md row.

The second runs the shape itself on its scripted models, and needs the chat image's pins (pip install -r
services/chat/requirements.txt), google-adk 2.8.0 among them: a ping-pong between the two desks stops after 3 transfers,
with the 4th refused before the agent it names runs, the cap's words as the answer and 4 model calls; with
disallow_transfer_to_peers each desk is offered only the root, the loop runs through the root, and the same cap ends it;
the count is a temp: key, so ADK stores nothing of it, and a second turn in the same session starts at the desk that
spoke last and counts again from one; the printed report, and --offline as the only mode. Without the pins this class is
skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error instead.
"""
import asyncio
import contextlib
import importlib.util
import io
import logging
import os
import re
import sys
import unittest
import warnings
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
CI_LINE = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_agent_shapes.py -v"


def _has(module: str) -> bool:
    """find_spec, but False when a parent package is missing (find_spec raises then: CI's shared interpreter)."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


FRAMEWORKS = _has("google.adk")
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


class TheShapeAsWritten(unittest.TestCase):
    """What needs no framework: the constants, the target, the entries and the rows."""

    def test_the_cap_and_its_scope(self):
        src = read("commands", "agent_shapes.py")
        self.assertRegex(src, r"(?m)^MAX_TRANSFERS = 3 ")
        self.assertRegex(src, r'(?m)^STARTS = "temp:')                      # ADK keeps temp: keys one invocation
        self.assertIn("plugins=[transfer_cap()]", src)                      # on the Runner's App, for every agent

    def test_the_target_the_entries_and_the_rows(self):
        mk, agents, readme = read("Makefile"), read("mk", "agents.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertIn("agent-shapes", phony.split())                       # later kits append after it
        recipe = agents.split("\nagent-shapes:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("OFFLINE=1 PY=$(PY) bash commands/agent-turn.sh commands/agent_shapes.py "
                      "$(if $(OFFLINE),--offline,)", recipe)
        row = next(line for line in readme.splitlines() if line.startswith("| `agents.mk` |"))
        self.assertIn("`agent-shapes`", row)
        self.assertIn(CI_LINE, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(CI_LINE, repo_ci.read_text(encoding="utf-8"))
        f = "commands/tests/test_agent_shapes.py"
        index = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
        self.assertTrue(f"| `{f}` | **10.7**" in read("UNOWNED.md") or index.split(" | ")[2:3] not in ([], ["-"]), f)


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class ThePingPong(unittest.TestCase):
    """The shape on its scripted models."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        cls.adk_level = logging.getLogger("google_adk").level
        logging.getLogger("google_adk").setLevel(logging.ERROR)    # ADK's notes on a scripted model's missing usage
        sys.path.insert(0, str(KIT / "commands"))
        import agent_shapes
        cls.shapes = agent_shapes
        cls.stop = agent_shapes.STOP.format(n=agent_shapes.MAX_TRANSFERS)

    @classmethod
    def tearDownClass(cls):
        logging.getLogger("google_adk").setLevel(cls.adk_level)

    def run_shape(self, peers=True, turns=1):
        return asyncio.run(self.shapes.swarm_adk(peers, turns))

    def test_a_ping_pong_stops_after_three_transfers(self):
        run = self.run_shape()
        turn = run["turns"][0]
        self.assertEqual(turn["transfers"], [("desk_root", "handbook_desk"), ("handbook_desk", "statute_desk"),
                                             ("statute_desk", "handbook_desk"), ("handbook_desk", "statute_desk")])
        self.assertEqual(turn["answer"], self.stop)
        self.assertEqual(turn["last"], "statute_desk")                        # refused: answered in its place
        self.assertEqual([c[0] for c in turn["calls"]], ["desk_root", "handbook_desk", "statute_desk", "handbook_desk"])
        offered = {agent: enum for agent, enum, _ in turn["calls"]}
        self.assertEqual(offered, {"desk_root": ["handbook_desk", "statute_desk"],
                                   "handbook_desk": ["desk_root", "statute_desk"],
                                   "statute_desk": ["desk_root", "handbook_desk"]})

    def test_without_peer_edges_the_loop_runs_through_the_root_and_the_cap_still_ends_it(self):
        turn = self.run_shape(peers=False)["turns"][0]
        for agent, enum, _ in turn["calls"]:
            if agent != "desk_root":
                self.assertEqual(enum, ["desk_root"], agent)                     # only the parent is offered
        self.assertEqual(turn["transfers"], [("desk_root", "handbook_desk"), ("handbook_desk", "desk_root"),
                                             ("desk_root", "statute_desk"), ("statute_desk", "desk_root")])
        self.assertEqual((turn["answer"], turn["last"], len(turn["calls"])), (self.stop, "desk_root", 4))

    def test_the_count_is_one_turns_and_never_stored(self):
        run = self.run_shape(turns=2)
        self.assertEqual(run["stored"], {})                                     # a temp: key: nothing of it is stored
        first, second = run["turns"]
        self.assertEqual(second["calls"][0][0], first["last"])                  # ADK resumes the desk that spoke last
        self.assertEqual(len(second["transfers"]), self.shapes.MAX_TRANSFERS + 1)    # and the count starts again
        self.assertEqual(second["answer"], self.stop)

    def test_the_report_and_the_one_mode(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.shapes.main(["--offline"]), 0)
        text = out.getvalue()
        self.assertEqual(text.count("answer, written by TransferCap, in "), 2)
        refused = re.findall(r"^transfer 4: .*refused: TransferCap answered before \w+ ran$", text, re.M)
        self.assertEqual(len(refused), 2)
        self.assertEqual(text.count("model calls: 4 | transfers made: 3 | session state stored after the turn: {}"), 2)
        with contextlib.redirect_stderr(err):
            self.assertEqual(self.shapes.main([]), 2)
        self.assertIn("offline only so far", err.getvalue())


if __name__ == "__main__":
    unittest.main()
