"""Offline tests of the capstone's four document templates (lesson 11.8): capstone/templates/ holds ARCHITECTURE.md,
COST-MODEL.md, FAILURE-MODES.md and RUNBOOK.md, the empty shape of the canned fork's four
(commands/tests/capstone_fork/), with {{...}} placeholders where the canned ones have a made-up company's text.
Standard library. Nothing reaches Google Cloud, and nothing runs make or a model: the check's own component functions
read a fork in a temporary directory.

Covered: the folder holds the four and nothing else; each has the canned document's headings and none of its text;
each placeholder opens and closes on one line, and the guidance comments hold none, so a grep for {{ finds only what
is left to fill; each holds what commands/capstone_check.py reads for its component (a Rejected section of three
options, the three volumes, the rate on one line, a rupee and a dollar slot for every amount, a date slot, four entries
each with a Symptom: line and one command in backticks, a section on rolling back); copied into a fork as they ship,
components 5, 6, 7 and 8 FAIL, each on the slots of its document that still hold a placeholder; every placeholder
filled, the four PASS; a document missing from the fork names its template; HANDOVER.md names the runbook's template; the rate
is shared/prices.py's; and the rows in UNOWNED.md.
"""
import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]
CANNED = HERE / "capstone_fork"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = load("capstone_check_for_templates", KIT / "commands" / "capstone_check.py")
TEMPLATES = KIT / cc.TEMPLATES
DOCS = ("ARCHITECTURE.md", "COST-MODEL.md", "FAILURE-MODES.md", "RUNBOOK.md")
COMPONENT = dict(zip(DOCS, (5, 6, 7, 8)))
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}")
COMPANY = "Sahyadri Freight"                        # the canned fork's company, in the canned documents' titles
TABLE_HEAD = "| Queries a month | Model | Retrieval and hosting | Total |"
# The kit files components 5 to 8 read in a fork: the makefiles a FAILURE-MODES command resolves against, the registry
# its gotcha drills come from, and the script the filled template's fourth entry names. The canned fork's smoke log
# goes in too, so component 8 turns on RUNBOOK.md alone: its four runs hold lesson 11.3's rollback.
KIT_FILES = ("Makefile", "ops/gotchas.json", "commands/incident-drill.sh")

# A value for each placeholder, by the placeholder's first words; a list is used in the order the placeholders come.
# The values are the canned fork's, or close to them: the filled templates are four documents the check passes.
FILLS = {
    "ARCHITECTURE.md": {
        "YOUR COMPANY": COMPANY,
        "One paragraph": "A made-up logistics company's dispatchers ask its fleet safety manual and driver handbook, "
                         "tenant sahyadri.",
        "YYYY-MM-DD": "2026-11-18",
        "From the browser": "A dispatcher signs in to documind-ui through IAP; documind-api checks the roster, "
                            "retrieves filtered by tenant, reranks and answers with citations.",
        "The lane you chose": "Chat: documind-chat answers follow-up questions, and make smoke-chat proves it.",
        "OPTION 1": "GKE Autopilot for the API",
        "OPTION 2": "A second vector database (Pinecone)",
        "OPTION 3": "Fine-tuning before prompting",
        "WHY NOT": ["our duty cycle is about 4%, so Cloud Run's per-request billing costs less",
                    "it would hold tenant text outside asia-south1, which our contracts forbid",
                    "the golden set showed no gap that the prompt and the reranker could not close"],
        "The threshold": "A p95 above 3 s for a week at ten times today's traffic, or a duty cycle above 74%.",
    },
    "COST-MODEL.md": {
        "YOUR COMPANY": COMPANY,
        "YYYY-MM-DD": "2026-11-18",
        "MODEL": "gemini-3.6-flash",
        "PRICE": ["1.50", "7.50"],
        "TOKENS": ["2,000", "300"],
        "COST": ["0.00525", "0.45"],
        "AMOUNT": ["446", "5.25", "1,700", "20.00", "2,146", "25.25",
                   "4,463", "52.50", "2,550", "30.00", "7,013", "82.50",
                   "44,625", "525.00", "8,500", "100.00", "53,125", "625.00"],
        "The first limit": "The per-minute request quota on the global endpoint, which the morning dispatch peak "
                           "reaches first.",
    },
    "FAILURE-MODES.md": {
        "YOUR COMPANY": COMPANY,
        "One line": "Four failures, each reproduced by a command this fork holds.",
        "FAILURE 1": "A rollback keeps the bad template",
        "FAILURE 2": "Pinned traffic hides a change",
        "FAILURE 3": "A poison upload pages an hour later",
        "FAILURE 4": "A mistyped model answers 500",
        "What a user or an alert sees": ["the next release candidate carries the rolled-back model",
                                         "a setting changed by hand never serves",
                                         "a zero-byte object fails twelve deliveries",
                                         "every agent turn answers 500 while /health stays green"],
        "GOTCHA-ID": ["rollback-keeps-template", "pinned-traffic"],
        "TARGET": "poison TENANT=sahyadri PROJECT=documind-ai-YOUR-ID",
        "SCRIPT": "incident-drill",
        "The policy that pages": ["no policy; make incident names the repair",
                                  "no policy; make gotcha-detect after every hand update",
                                  "Ingest dead-letter queue holds messages",
                                  "no policy counts 5xx answers; make remediate reads the request log"],
    },
    "RUNBOOK.md": {
        "YOUR COMPANY": COMPANY,
        "POLICY": ["API p95 latency > 3s", "Ingest dead-letter queue holds messages"],
        "What to do when it pages": ["make remediate POLICY='API p95 latency > 3s' prints the plan, a rollback",
                                     "make dlq shows the message; fix or remove the object, then acknowledge it"],
        "THE ROLLBACK COMMAND": "make rollback PROJECT=documind-ai-YOUR-ID REGION=asia-south1",
        "What it moves": "returns the traffic to .previous-revision; then make smoke-deployed and make incident.",
        "When,": "On 17 November 2026 the mistyped model, documind-api-00042-typ, went back to documind-api-00041-kel.",
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fill(text: str, values: dict) -> str:
    """The template with each {{...}} replaced by the next value of the longest key it starts with; every value used."""
    pending = {key: list(v) if isinstance(v, list) else [v] for key, v in values.items()}

    def value(m: re.Match) -> str:
        key = next((k for k in sorted(pending, key=len, reverse=True) if m.group(1).startswith(k)), None)
        assert key is not None and pending[key], f"no value left for {m.group(0)}"
        return pending[key].pop(0)
    out = PLACEHOLDER.sub(value, text)
    assert not any(pending.values()), {k: v for k, v in pending.items() if v}
    return out


def headings(text: str) -> list:
    return [(level, title) for level, title, _ in cc.sections(text)]


class ShapeTests(unittest.TestCase):
    def test_the_folder_holds_the_four(self):
        self.assertEqual(sorted(p.name for p in TEMPLATES.iterdir()), sorted(DOCS))

    def test_each_is_the_canned_documents_shape_and_none_of_its_text(self):
        for name in DOCS:
            with self.subTest(name):
                template, canned = read(TEMPLATES / name), read(CANNED / name)
                mine = [(level, title.replace("{{YOUR COMPANY}}", COMPANY)) for level, title in headings(template)]
                if name == "FAILURE-MODES.md":     # the entries are the canned company's: as many, each the same three lines
                    self.assertEqual([level for level, _ in mine], [level for level, _ in headings(canned)])
                    self.assertEqual(mine[0], headings(canned)[0])
                    for doc in (template, canned):
                        self.assertEqual([[line.split(":", 1)[0] for line in body if re.match(r"^[A-Z][a-z ]+: ", line)]
                                          for level, _, body in cc.sections(doc) if level == 2],
                                         [["Symptom", "Command", "Caught by"]] * cc.ENTRIES_MIN)
                else:
                    self.assertEqual(mine, headings(canned))
                shared = {line for line in template.splitlines() if line.strip()} & set(canned.splitlines())
                self.assertEqual({line for line in shared if not line.startswith("#") and line != TABLE_HEAD
                                  and not cc.TABLE_RULE.match(line)}, set())

    def test_each_placeholder_is_on_one_line_and_no_comment_holds_one(self):
        for name in DOCS:
            text = read(TEMPLATES / name)
            with self.subTest(name):
                self.assertTrue(PLACEHOLDER.search(text))
                for line in text.splitlines():
                    self.assertEqual(line.count("{{"), line.count("}}"), line)
                    self.assertEqual(line.count("{{"), len(PLACEHOLDER.findall(line)), line)
                for comment in re.findall(r"<!--.*?-->", text, re.S):
                    self.assertNotIn("{{", comment)
                self.assertLessEqual(max(len(line) for line in text.splitlines()), 118)


class WhatTheCheckReadsTests(unittest.TestCase):
    def test_architecture_names_three_options_and_argues_none(self):
        options = cc.rejected_options(read(TEMPLATES / "ARCHITECTURE.md"))
        self.assertIsNotNone(options)
        self.assertEqual(len(options), cc.REJECTED_MIN)
        for option in options:
            self.assertTrue(PLACEHOLDER.search(option), option)
            self.assertLess(cc.words(option), cc.REASON_WORDS, option)        # a name until filled, not an argument

    def test_cost_model_names_the_volumes_and_the_rate_with_a_slot_for_every_amount(self):
        text = read(TEMPLATES / "COST-MODEL.md")
        held, missing = cc.cost_model(text)
        self.assertIn("COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month", held)
        self.assertIn(f"at {cc.USD_INR} rupees to the dollar", held)
        self.assertIn(f"USD_INR = {cc.USD_INR}", text)
        rows = [line for line in text.splitlines() if line.startswith("|") and line != TABLE_HEAD
                and not cc.TABLE_RULE.match(line)]
        self.assertEqual([row.split("|")[1].strip() for row in rows], ["1k", "10k", "100k"])
        for row in rows:
            self.assertEqual(row.count("Rs {{AMOUNT}}"), row.count("(USD {{AMOUNT}})"))
            self.assertGreaterEqual(row.count("Rs {{AMOUNT}}"), 1)
        self.assertGreaterEqual(text.count("Rs {{"), cc.AMOUNTS_MIN)
        self.assertIn("Dated {{YYYY-MM-DD}}", text)

    def test_failure_modes_holds_four_entries_each_with_a_symptom_and_a_command(self):
        entries = cc.failure_modes(read(TEMPLATES / "FAILURE-MODES.md"))
        self.assertEqual(len(entries), cc.ENTRIES_MIN)
        for title, symptom, commands in entries:
            self.assertTrue(symptom, title)
            self.assertEqual(len(commands), 1, title)
            self.assertTrue(cc.is_command(commands[0]), commands)
        # the four shapes that resolve: a drill offline, a drill live, a make target, a script the fork holds
        self.assertEqual([c[0] for _, _, c in entries], ["make gotcha-drill ID={{GOTCHA-ID}}",
                                                          "make gotcha-drill ID={{GOTCHA-ID}} LIVE=1",
                                                          "make {{TARGET}}", "bash commands/{{SCRIPT}}.sh"])

    def test_runbook_has_its_rollback_section(self):
        self.assertIn((2, "Roll back the API"), headings(read(TEMPLATES / "RUNBOOK.md")))


class ForkTests(unittest.TestCase):
    """A fork in a temporary directory: the kit files components 5 to 8 read, and the canned fork's smoke log."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="capstone_templates_"))
        self.addCleanup(shutil.rmtree, self.root, True)
        for rel in [*KIT_FILES, *(f"mk/{p.name}" for p in sorted((KIT / "mk").glob("*.mk")))]:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(KIT / rel, self.root / rel)
        (self.root / cc.REPORTS).mkdir(parents=True)
        shutil.copyfile(CANNED / cc.SMOKE_LOG, self.root / cc.SMOKE_LOG)

    def components(self) -> dict:
        """{component: (held, missing)} for components 5 to 8, as make capstone-check reads this fork offline."""
        fork = cc.Fork(self.root)
        return {n: check(fork, None) for n, check in cc.CHECKS if n in COMPONENT.values()}

    def test_copied_as_they_ship_each_fails_on_its_document(self):
        for name in DOCS:
            shutil.copyfile(TEMPLATES / name, self.root / name)
        found = self.components()
        self.assertEqual([n for n, (_, missing) in found.items() if missing], [5, 6, 7, 8])
        flat = {n: " ".join(" ".join(held + missing).split()) for n, (held, missing) in found.items()}
        self.assertIn("names 0 rejected options with a reason (and 3 without one: {{OPTION 1}}; {{OPTION 2}}; "
                      "{{OPTION 3}})", flat[5])
        self.assertEqual(len(found[6][1]), 2)                               # the amounts and the date, nothing else
        self.assertIn("gives 0 amounts in rupees", flat[6])
        self.assertIn("carries no date", flat[6])
        self.assertIn("0 entries proved, 4 or more", flat[7])
        for why in ("ID={{GOTCHA-ID}} is not in ops/gotchas.json", "define no {{TARGET}} target",
                    "the fork holds no commands/{{SCRIPT}}.sh"):
            self.assertIn(why, flat[7])
        self.assertEqual(found[8][1], ["RUNBOOK.md does not say how to roll back: make rollback (lesson 11.3), or gcloud "
                                       "run services update-traffic"])           # the recorded rollback still holds
        self.assertIn("a recorded rollback", flat[8])

    def test_every_placeholder_filled_each_passes(self):
        for name in DOCS:
            filled = fill(read(TEMPLATES / name), FILLS[name])
            self.assertNotIn("{{", filled, name)
            (self.root / name).write_text(filled, encoding="utf-8", newline="\n")
        found = self.components()
        self.assertEqual({n: missing for n, (_, missing) in found.items()}, {5: [], 6: [], 7: [], 8: []})
        self.assertTrue(found[5][0][0].startswith("ARCHITECTURE.md names 3 rejected options with a reason: GKE Autopilot"))
        self.assertIn("dated 2026-11-18", found[6][0])
        self.assertEqual(found[7][0][0], "4 entries proved by a command the fork runs:")
        self.assertIn("RUNBOOK.md says how to roll back", found[8][0])

    def test_a_missing_document_names_its_template(self):
        found = self.components()
        for name, n in COMPONENT.items():
            with self.subTest(name):
                self.assertEqual(found[n][1][0], f"{name} is missing from the fork's root: copy {cc.TEMPLATES}/{name} there "
                                                 "from the kit, and replace each {{...}} placeholder in it")
                self.assertTrue((KIT / cc.TEMPLATES / name).is_file())

    def test_handover_names_the_runbooks_template(self):
        text = cc.Handover(cc.Fork(KIT), None).text("2026-10-13T00:00:00Z")
        self.assertIn(f"notes of your own belong in RUNBOOK.md, whose template is {cc.TEMPLATES}/RUNBOOK.md.",
                      " ".join(text.split()))


class WiringTests(unittest.TestCase):
    def test_the_rate_is_the_kits(self):
        rate = re.search(r"(?m)^USD_INR = (\d+)\b", read(KIT / "shared" / "prices.py"))
        self.assertEqual(int(rate.group(1)), cc.USD_INR)

    def test_the_files_are_listed(self):
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read(KIT / "UNOWNED.md"), read(KIT / "INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in (f"{cc.TEMPLATES}/", "commands/tests/test_capstone_templates.py"):
            self.assertTrue(f"`{f}`" in unowned or any(q == f or q.startswith(f) for q in quoted), f)


if __name__ == "__main__":
    unittest.main()
