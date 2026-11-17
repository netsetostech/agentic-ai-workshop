"""The kit's two chunkers, held to one rule (workshop lesson 8.2).

    python -m unittest commands/tests/test_twin_chunker.py          (from deploy/)

The kit cuts text into chunks in two places. services/ingest/main.py's _chunk() is the lane's: every upload, re-issue
and reindex goes through it. shared/documind_corpus.py's chunk_document() is everyone else's: the notebooks' seed(),
the Rs 0 lane (shared/local_corpus.py), the offline gates and the lesson pages that count chunks at build time. Each
file says it chunks by the other's rules, and nothing in this repository checked it until 13 October 2026 (INDEXING.md
names a wiring gate for it, tools/check_auth_wiring.py, that this repository does not carry). Lesson 8.2 changes the
chunk size and overlap, CHUNK_CHARS and CHUNK_OVERLAP, which each file sets on a line of its own: an edit to one twin
alone leaves the lane minting chunks that no offline count, gate or carry-over estimate has seen. This file fails
then, and names both lines.

Standard library only. The worker's chunker is lifted from main.py's source with ast, with contracts.py's chunk_hash
(importing the worker needs FastAPI, google-cloud and a project; contracts.py needs pydantic), and the corpus twin is
lifted from its own source the same way, so an edited copy of either file is held to the other in memory. No kit file
is written.

For the same text the twins give the same chunks: the same texts in the same order, with the same chunk_hash, kind,
section and locator. That is checked over every Markdown text under evals/corpus/ (the handbooks, the contracts, the
invoice, the report, the transcript and the real Acts' page-split mirrors) at the kit's pair and at lesson 8.2's
400/50, and over the edge cases below at more pairs. Two differences are the kit's own, written into main.py on
12 September 2026, and are pinned here so that a third cannot hide behind them:
  - page_start: the worker writes None where the text names no page (a handbook's sections, a text with no form
    feed), and the corpus twin writes 1;
  - a text with neither `## ` headings nor form feeds (an invoice, a transcript): the worker's locators are w0, w1, ...
    and the corpus twin reads it as a one-page mirror, p1-0, p1-1, ...
"""
import ast
import hashlib
import re
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]                       # deploy/
WORKER, CONTRACTS, CORPUS = "services/ingest/main.py", "services/ingest/contracts.py", "shared/documind_corpus.py"
PAIR = ("CHUNK_CHARS", "CHUNK_OVERLAP")
LESSON_8_2 = (400, 50)                                          # the pair lesson 8.2 writes into both files
HEADER = re.compile(r"\A\s*<!--.*?-->\s*", re.S)                # a mirror's provenance header, which both twins drop


def source(rel: str) -> str:
    """One kit file's text."""
    return (KIT / rel).read_text(encoding="utf-8")


def lift(ns: dict, src: str, filename: str, names: set) -> dict:
    """The module-level assignments and functions named in `names`, exec'd from `src` into `ns`."""
    found, nodes = set(), []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            targets = {e.id for t in node.targets for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                       if isinstance(e, ast.Name)}
            if targets & names:
                nodes.append(node)
                found |= targets & names
    if names - found:
        raise AssertionError(f"{filename} no longer defines {sorted(names - found)} at module level")
    exec(compile(ast.Module(nodes, []), filename, "exec"), ns)
    return ns


def worker_twin(main_src: str = None) -> dict:
    """main.py's chunker (the pair, _SECTION, _CODE, _windows, _chunk) with contracts.py's chunk_hash."""
    ns = lift({"re": re, "hashlib": hashlib}, source(CONTRACTS), CONTRACTS, {"_WS", "chunk_hash"})
    return lift(ns, source(WORKER) if main_src is None else main_src, WORKER,
                {*PAIR, "_SECTION", "_CODE", "_windows", "_chunk"})


def corpus_twin(corpus_src: str = None) -> dict:
    """shared/documind_corpus.py's chunker (the pair, _SECTION, _CODE, windows, chunk_hash, chunk_document)."""
    return lift({"re": re, "hashlib": hashlib}, source(CORPUS) if corpus_src is None else corpus_src, CORPUS,
                {*PAIR, "_SECTION", "_CODE", "windows", "chunk_hash", "chunk_document"})


def pair_line(src: str) -> ast.Assign:
    """The statement `CHUNK_CHARS, CHUNK_OVERLAP = ...` in a file's source."""
    for node in ast.parse(src).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple)
                and [getattr(e, "id", None) for e in node.targets[0].elts] == list(PAIR)):
            return node
    raise AssertionError("no `CHUNK_CHARS, CHUNK_OVERLAP = ...` line")


def pair_of(src: str) -> tuple:
    """The (size, overlap) a file's source sets."""
    return tuple(ast.literal_eval(pair_line(src).value))


def with_pair(src: str, size: int, overlap: int) -> str:
    """`src` with its pair line set to (size, overlap), the rest of the line (its comment) kept: lesson 8.2's edit."""
    value = pair_line(src).value
    lines = src.splitlines(keepends=True)
    row = lines[value.lineno - 1].encode("utf-8")                     # ast's column offsets count UTF-8 bytes
    lines[value.lineno - 1] = (row[:value.col_offset] + f"{size}, {overlap}".encode("utf-8")
                               + row[value.end_col_offset:]).decode("utf-8")
    return "".join(lines)


def set_pair(ns: dict, size: int, overlap: int) -> dict:
    """A lifted twin with another pair, the way the edited line would set it."""
    ns["CHUNK_CHARS"], ns["CHUNK_OVERLAP"] = size, overlap
    return ns


def both(w: dict, c: dict, text: str) -> tuple:
    """One text through both twins: (the worker's chunks, the corpus twin's chunks)."""
    doc = {"slug": "doc", "doc_type": "policy", "source_uri": "gs://uploads/acme/doc.md", "text": text}
    return w["_chunk"](text), c["chunk_document"](doc, "acme")


def differences(w: dict, c: dict, text: str) -> list:
    """What the twins disagree on for one text, beyond the two differences the kit keeps (the module's docstring)."""
    mine, theirs = both(w, c, text)
    if len(mine) != len(theirs):
        return [f"{len(mine)} chunks from {WORKER}, {len(theirs)} from {CORPUS}"]
    body = HEADER.sub("", text, count=1)
    sections = bool(c["_SECTION"].search(body))
    plain = not sections and "\f" not in body
    out = []
    for i, (x, y) in enumerate(zip(mine, theirs)):
        for field in ("text", "chunk_hash", "kind", "section"):
            if x.get(field) != y.get(field):
                out.append(f"chunk {i} ({y['locator']}): {field} {str(x.get(field))[:60]!r} from {WORKER}, "
                           f"{str(y.get(field))[:60]!r} from {CORPUS}")
        locator = re.sub(r"\Ap1-(\d+)\Z", r"w\1", y["locator"]) if plain else y["locator"]
        if x["locator"] != locator:
            out.append(f"chunk {i}: locator {x['locator']!r} from {WORKER}, {y['locator']!r} from {CORPUS}")
        page = None if (plain or sections) else y["page_start"]
        if x["page_start"] != page:
            out.append(f"chunk {i} ({y['locator']}): page_start {x['page_start']!r} from {WORKER}, {page!r} expected")
    return out


def read(path: Path) -> str:
    """A corpus file as the worker decodes an upload: the bytes, UTF-8, no newline translation."""
    return path.read_bytes().decode("utf-8")


def corpus_texts() -> dict:
    """Every Markdown text under evals/corpus/, once per distinct content (two tenants' copies are chunked once)."""
    out = {}
    for path in sorted((KIT / "evals" / "corpus").glob("*/*.md")):
        out.setdefault(read(path), f"{path.parent.name}/{path.name}")
    return {name: text for text, name in out.items()}


SENTENCE = "An employee on probation serves fifteen days' notice, and the company may waive it in writing. "
NO_STOP = "Rs 52,000 a month for grade E3 under LV-07 with gratuity under s.53 of the Code " * 6
# Lesson 8.2's re-issue (new bytes, the same text) and the rules each twin applies: sections with and without clause
# codes, a preamble and a section longer than a window, cuts with and without a sentence end, pages, Hindi.
EDGES = {
    "a re-issue's provenance header": "<!-- r4 -->\n# Handbook\n\n## NP-03 Notice period\n" + SENTENCE * 3,
    "a long preamble": SENTENCE * 40 + "\n## LV-07 Leave encashment\n" + SENTENCE * 2,
    "a long section": "## NP-03 Notice period\n" + SENTENCE * 45 + "\n## GEN-014 Grievances\n" + SENTENCE,
    "sections without codes": "Intro.\n## Purpose of this policy\n" + SENTENCE * 8 + "\n## Scope  \n" + SENTENCE,
    "no sentence end": "## IT-SEC-04 Passwords\n" + NO_STOP * 12,
    "CRLF line ends": "Intro.\r\n## MSA-04 Payment terms\r\n" + SENTENCE * 9 + "\r\n## s\r\nlast.\r\n",
    "pages": SENTENCE * 25 + "\f" + "\f" + NO_STOP * 5 + "\f" + SENTENCE * 3 + "\f",
    "a mirror with a header": "<!-- source: indiacode.nic.in -->\n" + SENTENCE * 12 + "\f" + SENTENCE * 30,
    "plain text": SENTENCE * 30,
    "Hindi": "## LV-07 अवकाश नकदीकरण\n" + "कर्मचारी को ₹52,000 प्रति माह मिलते हैं। यह नियम 1 अप्रैल से लागू है. " * 40,
    "nothing": "",
    "only whitespace": " \n\t\f \n",
    "only a header": "<!-- r4 -->\n",
    "a first heading indented": "  ## NP-03 Notice period\n" + SENTENCE * 2 + "\n## LV-07 Leave encashment\n" + SENTENCE,
}
PAIRS = [(2000, 200), LESSON_8_2, (600, 100), (1000, 0), (250, 100), (120, 0)]


class TheTwinsAgree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = corpus_texts()

    def agree(self, w: dict, c: dict, name: str, text: str):
        """Fail with the first differences, named, when the twins cut one text two ways."""
        found = differences(w, c, text)
        if found:
            self.fail(f"{name}: " + "; ".join(found[:3]))

    def test_one_size_and_one_overlap(self):
        # The two numbers lesson 8.2 edits, read from each file's own line.
        worker, corpus = pair_of(source(WORKER)), pair_of(source(CORPUS))
        if worker != corpus:
            self.fail(f"{WORKER} sets CHUNK_CHARS, CHUNK_OVERLAP = {worker[0]}, {worker[1]} and {CORPUS} sets "
                      f"{corpus[0]}, {corpus[1]}: a chunker change edits both lines")

    def test_one_section_rule_one_clause_code_one_hash(self):
        w, c = worker_twin(), corpus_twin()
        for name in ("_SECTION", "_CODE"):
            self.assertEqual((w[name].pattern, w[name].flags), (c[name].pattern, c[name].flags), name)
        for text in ["NP-03 Notice\nbody", "a  re-wrapped\n\tparagraph ", " ", "₹52,000 प्रति माह", *EDGES.values()]:
            self.assertEqual(w["chunk_hash"](text), c["chunk_hash"](text), repr(text[:40]))

    def test_the_corpus_at_the_kits_pair(self):
        w, c = worker_twin(), corpus_twin()
        self.assertGreaterEqual(len(self.texts), 15)                     # the handbooks, the rest, the Acts' mirrors
        for name, text in self.texts.items():
            self.agree(w, c, name, text)

    def test_the_corpus_at_lesson_8_2s_pair(self):
        w, c = set_pair(worker_twin(), *LESSON_8_2), set_pair(corpus_twin(), *LESSON_8_2)
        for name, text in self.texts.items():
            self.agree(w, c, name, text)

    def test_the_edge_cases_at_more_pairs(self):
        for size, overlap in PAIRS:
            w, c = set_pair(worker_twin(), size, overlap), set_pair(corpus_twin(), size, overlap)
            for name, text in EDGES.items():
                with self.subTest(pair=(size, overlap), text=name):
                    self.agree(w, c, name, text)
                    self.assertEqual([piece for _, piece in w["_windows"](text)], c["windows"](text))

    def test_the_two_differences_the_kit_keeps(self):
        # Pinned, so a change to either side's rule is a decision someone makes here, not a drift.
        w, c = worker_twin(), corpus_twin()
        mine, theirs = both(w, c, self.texts["acme/inv_2026_0412.md"])        # neither headings nor form feeds
        got = [(x["locator"], x["page_start"]) for x in mine], [(x["locator"], x["page_start"]) for x in theirs]
        want = [(f"w{k}", None) for k in range(len(mine))], [(f"p1-{k}", 1) for k in range(len(mine))]
        if not mine or got != want:
            self.fail(f"the invoice: {WORKER} gives {got[0][:3]}, {CORPUS} {got[1][:3]}; the kit keeps w<k> with no page "
                      f"against p1-<k> on page 1")
        mine, theirs = both(w, c, self.texts["acme/hr_policy_2026.md"])         # a handbook's sections
        self.assertEqual({x["page_start"] for x in mine}, {None})
        self.assertEqual({x["page_start"] for x in theirs}, {1})

    def test_a_first_heading_indented_with_spaces_is_a_heading_for_both(self):
        """13 October 2026: the worker searched the stripped text for headings and the twin the text as it came, so a
        handbook whose first `## ` heading sat behind spaces was two sections on the lane and a preamble plus one in a
        notebook. Both read it stripped now."""
        text = EDGES["a first heading indented"]
        w, c = worker_twin(), corpus_twin()
        self.assertEqual(differences(w, c, text), [])
        mine, theirs = both(w, c, text)
        self.assertEqual([x["locator"] for x in mine], ["NP-03", "LV-07"])
        self.assertEqual([x["section"] for x in theirs], ["NP-03 Notice period", "LV-07 Leave encashment"])


class OneTwinEditedAlone(unittest.TestCase):
    """Lesson 8.2's edit, made in memory: one file alone is caught, both files agree. The edit writes 400/50, or
    another pair once a lane has made lesson 8.2's edit, so this file passes before that edit and after it. Any two of
    the pairs below cut the handbook differently: its longest section is 599 characters (13 October 2026), so a size of
    599 or more leaves every section whole, and 400 or 300 cuts most of them."""

    @classmethod
    def setUpClass(cls):
        cls.handbook = read(KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md")
        cls.main, cls.corpus = source(WORKER), source(CORPUS)
        held = {pair_of(cls.main), pair_of(cls.corpus)}
        cls.other = next(p for p in (LESSON_8_2, (2000, 200), (300, 30)) if p not in held)

    def test_the_edit_changes_only_the_pair(self):
        for src in (self.main, self.corpus):
            edited = with_pair(src, *self.other)
            self.assertEqual(pair_of(edited), self.other)
            changed = [(a, b) for a, b in zip(src.splitlines(), edited.splitlines()) if a != b]
            self.assertEqual(len(changed), 1, changed)
            self.assertEqual(changed[0][0].split("#", 1)[1:], changed[0][1].split("#", 1)[1:])   # the comment kept

    def test_the_worker_edited_alone_is_caught(self):
        edited = with_pair(self.main, *self.other)
        self.assertNotEqual(pair_of(edited), pair_of(self.corpus))
        self.assertTrue(differences(worker_twin(edited), corpus_twin(), self.handbook))

    def test_the_corpus_twin_edited_alone_is_caught(self):
        edited = with_pair(self.corpus, *self.other)
        self.assertNotEqual(pair_of(self.main), pair_of(edited))
        self.assertTrue(differences(worker_twin(), corpus_twin(edited), self.handbook))

    def test_both_edited_agree(self):
        main, corpus = with_pair(self.main, *self.other), with_pair(self.corpus, *self.other)
        self.assertEqual(pair_of(main), pair_of(corpus))
        w, c = worker_twin(main), corpus_twin(corpus)
        self.assertEqual(differences(w, c, self.handbook), [])
        before, _ = both(worker_twin(), corpus_twin(), self.handbook)
        after, _ = both(w, c, self.handbook)
        self.assertNotEqual([x["text"] for x in after], [x["text"] for x in before])   # the edit moved the boundaries


if __name__ == "__main__":
    unittest.main()
