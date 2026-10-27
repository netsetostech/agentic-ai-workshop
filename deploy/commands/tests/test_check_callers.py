"""Offline checks for make check-callers GRAPH=1, the caller graph checked for a cycle (workshop lesson 10.7).

    python -m unittest commands/tests/test_check_callers.py -v          # from deploy/

Standard library only, no network, no credential. commands/check_callers.py reads the deploy scripts terraform/sa.tf's
caller graph names: each service's account and the accounts its invoker bindings name, loops expanded. Covered: the
kit's graph, its nine service edges and its order, acyclic; the scripts' callers equal to the ones sa.tf's six lines
name (the authoring repository's tools/check_authz.py holds the same, through this module); the 10.7 page's Change-it,
documind-agent-sa added to lesson-12.8.sh's invoker loop, named as the cycle documind-chat -> documind-agent ->
documind-chat with exit 1; a service whose own account may invoke it, a cycle of one; no --graph, exit 2; the
parsing of a binding's member (a loop variable, braces, a Google service agent); the target, `.PHONY`,
`mk/README.md`, the 888 lines and the UNOWNED.md rows.
"""
import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "commands"))
import check_callers as cc  # noqa: E402

EDGES = {("documind-chat", "documind-api"), ("documind-chat", "documind-agent"), ("documind-mcp", "documind-api"),
         ("documind-agent", "documind-mcp"), ("documind-ui", "documind-api"), ("documind-ui", "documind-chat"),
         ("documind-ui", "documind-mcp"), ("documind-ui", "documind-agent"), ("documind-gchat", "documind-chat")}


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class ScratchKit:
    """sa.tf and the deploy scripts, copied, so a test can edit a binding."""

    def __enter__(self) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "terraform").mkdir()
        shutil.copy(KIT / "terraform" / "sa.tf", root / "terraform" / "sa.tf")
        (root / "commands").mkdir()
        for script in KIT.joinpath("commands").glob("*.sh"):
            shutil.copy(script, root / "commands" / script.name)
        return root

    def __exit__(self, *exc):
        self.tmp.cleanup()


def edit(root: Path, script: str, old: str, new: str) -> None:
    path = root / "commands" / script
    src = path.read_text(encoding="utf-8")
    assert old in src, (script, old)
    path.write_text(src.replace(old, new, 1), encoding="utf-8", newline="\n")


class TheKitsGraph(unittest.TestCase):

    def test_acyclic_with_nine_edges_and_an_order(self):
        g = cc.read_graph()
        self.assertEqual(g.services, ["documind-api", "documind-chat", "documind-mcp", "documind-agent", "documind-ui",
                                      "documind-gchat"])
        self.assertEqual({s: g.runs_as[s] for s in g.services}, {s: f"{s}-sa" for s in g.services})
        self.assertEqual({(s, t) for s in g.services for t in g.edges[s]}, EDGES)
        self.assertIsNone(cc.cycle(g))
        self.assertEqual(cc.order(g), ["documind-ui", "documind-gchat", "documind-chat", "documind-agent", "documind-mcp",
                                       "documind-api"])
        code, out, _ = run("--graph")
        self.assertEqual(code, 0)
        self.assertIn("\nacyclic: documind-ui, documind-gchat, documind-chat, documind-agent, documind-mcp, documind-api\n", out)
        self.assertIn("  documind-chat -> documind-agent\n", out)
        self.assertIn("documind-outsider-sa", out.split("callers that run no service", 1)[1].split("\n", 1)[0])

    def test_the_scripts_callers_are_the_ones_sa_tf_names(self):
        g = cc.read_graph()
        named = {m.group(1): m.group(2) for m in cc.GRAPH_LINE.finditer(read("terraform", "sa.tf"))}
        for service, callers in named.items():
            want = set(re.findall(r"documind-[a-z]+-sa\b", callers)) | set(re.findall(r"gcp-sa-[a-z]+", callers))
            with self.subTest(service=service):
                self.assertEqual(g.callers[service], want)
                self.assertEqual(g.script[service], re.search(rf"^#\s+{service}\s+<-.*\((\S+\.sh)\)", read("terraform", "sa.tf"),
                                                              re.M).group(1))


class ACycle(unittest.TestCase):

    def test_the_pages_change_it_an_edge_back_from_the_peer_to_the_chat(self):
        with ScratchKit() as root:
            edit(root, "lesson-12.8.sh", "for who in documind-ui-sa documind-outsider-sa \\",
                 "for who in documind-ui-sa documind-agent-sa documind-outsider-sa \\")
            self.assertIn("documind-agent-sa", cc.read_graph(root).callers["documind-chat"])
            code, out, _ = run("--graph", "--kit", str(root))
        self.assertEqual(code, 1)
        self.assertIn("\ncycle: documind-chat -> documind-agent -> documind-chat\n", out)
        self.assertIn("(documind-agent-sa may invoke documind-chat:", out)
        self.assertNotIn("acyclic", out)

    def test_a_service_whose_own_account_may_invoke_it(self):
        with ScratchKit() as root:
            edit(root, "lesson-7.2.sh", "for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do",
                 "for who in documind-ui-sa documind-agent-sa documind-mcp-sa documind-outsider-sa; do")
            code, out, _ = run("--graph", "--kit", str(root))
        self.assertEqual(code, 1)
        self.assertIn("\ncycle: documind-mcp -> documind-mcp\n", out)

    def test_a_caller_that_runs_no_service_closes_no_cycle(self):
        with ScratchKit() as root:                 # the outsider on the peer: wrong (lesson 10.6), but no cycle
            edit(root, "lesson-8.4.sh", "for sa in documind-ui-sa documind-chat-sa; do",
                 "for sa in documind-ui-sa documind-chat-sa documind-outsider-sa; do")
            code, out, _ = run("--graph", "--kit", str(root))
        self.assertEqual(code, 0)
        self.assertIn("\nacyclic: ", out)


class TheReading(unittest.TestCase):

    def test_without_graph_it_says_what_it_does_not_do(self):
        code, out, err = run()
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--graph (make check-callers GRAPH=1) is the only mode", err)

    def test_a_bindings_member(self):
        script = ("gcloud run deploy svc-x \\\n  --region=r --service-account=documind-x-sa@$PROJECT.iam.gserviceaccount.com\n"
                  "for who in documind-a-sa \\\n  documind-b-sa; do\n"
                  '  gcloud run services add-iam-policy-binding svc-x --member="serviceAccount:${who}@$PROJECT.iam" '
                  "--role=roles/run.invoker\ndone\n"
                  "gcloud run services add-iam-policy-binding svc-x \\\n"
                  '  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \\\n'
                  "  --role=roles/run.invoker\n"
                  'gcloud run services add-iam-policy-binding svc-x --member="serviceAccount:documind-c-sa@p" --role=roles/run.admin\n'
                  'gcloud run services add-iam-policy-binding svc-xy --member="serviceAccount:documind-d-sa@p" --role=roles/run.invoker\n')
        self.assertEqual(cc.deployed_as(script, "svc-x"), "documind-x-sa")
        self.assertIsNone(cc.deployed_as(script, "svc"))
        self.assertEqual(cc.invokers(script, "svc-x"), {"documind-a-sa", "documind-b-sa", "gcp-sa-iap"})


class TheEntries(unittest.TestCase):

    def test_the_target_the_phony_line_the_readme_and_the_rows(self):
        mk, agents, readme = read("Makefile"), read("mk", "agents.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertIn("check-callers", phony.split())                         # later kits append after it
        recipe = agents.split("\ncheck-callers:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("$(PY) commands/check_callers.py $(if $(GRAPH),--graph,)", recipe)
        self.assertNotIn("guard-project", agents.split("\ncheck-callers:", 1)[1].split("\n", 1)[0])    # no project, no gcloud
        row = next(line for line in readme.splitlines() if line.startswith("| `agents.mk` |"))
        self.assertIn("`check-callers`", row)
        unowned = read("UNOWNED.md")
        for f in ("commands/check_callers.py", "commands/tests/test_check_callers.py"):
            row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
            self.assertTrue(f"| `{f}` | **10.7**" in unowned or row.split(" | ")[2:3] not in ([], ["-"]), f)


if __name__ == "__main__":
    unittest.main()
