"""One-off: renumber the course to the Cohort 2 structure in plan/cohort-2-structure-2026-10-07.json.

    python tools/renumber_course.py --dry-run   # report only: what would move and every rewrite
    python tools/renumber_course.py             # apply, then write the review log

In order:
  1. course-manifest.json becomes Basics and Modules 0-12 with every lesson of the structure. Lessons not written yet
     are 'Not started' with no slug, as today's unwritten lessons are.
  2. Each built lesson's directory and page move to their new number and module (git mv).
  3. Each moved lesson's own sources are rewritten:
     - build.py's LESSON and <title>;
     - the hero crumb and the footer, regenerated from the new order, so 'Next' names the next lesson of the new course;
     - 'Lesson N.M' and 'Lessons N.M and N.M' sequences, bare N.M before "'s", and parenthesised lists of lesson ids;
     - 'Module N' where the old module maps whole to one new module.
     Code, pre, svg, script and style regions are left alone. Every other token that is an old lesson id, every
     'Modules ...' plural and every reference to old Module 10 or 12 (now split) goes to the review log.
  4. The demo tooling: the lesson keys in tools/ and deploy/workshop_demos/ (quoted ids, lesson_N_M folders,
     module_NN/lesson_N_M paths), and each built lesson's demo folder moved (git mv). The not-started lessons that
     merge (1.1+1.2 to 0.2, 2.1+2.2 to 0.3, 2.3 to 0.4) keep only their hand-written files; their demos regenerate.
Then: python pagekit/build.py --all; python tools/build_workshop_demos.py; python tools/kit_index.py; the checks.
Kept until the structure settles, then deleted.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY = "--dry-run" in sys.argv
S = json.loads((ROOT / "plan/cohort-2-structure-2026-10-07.json").read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
OLDM = json.loads((ROOT / "course-manifest.json").read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
OLD_LES = OrderedDict((lid, (mk, l)) for mk, m in OLDM["modules"].items() for lid, l in m["lessons"].items())
NEW = S["lessons"]
ORDER = list(NEW)
MAP = dict(S["old_to_new"])                                       # every old id -> its new id (moves and merges)
MOVED = OrderedDict((r["src"][0], nid) for nid, r in NEW.items() if r["kind"].startswith("move"))
# old module -> new module where the whole old module lands in one new module; 10 and 12 split, so they are reviewed
WHOLE = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 3, 7: 4, 8: 4, 9: 6, 11: 6, 13: 11, 14: 11, 15: 7, 16: 7, 17: 12, 18: 9}
ID = r"\d{1,2}\.\d{1,2}"
A, Z = "\x01", "\x02"                                               # wrap rewritten ids until every pass is done
review, changes = [], []


def mkey(lid: str) -> str:
    return "B" if lid.startswith("B") else lid.split(".")[0].zfill(2)


def mword(mk: str) -> str:
    return S["modules"][mk]["name"].split(" - ")[0].strip()


def git(*args):
    if DRY:
        return
    subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)


# ---------------------------------------------------------------- 1. the manifest
def new_manifest() -> OrderedDict:
    out = OrderedDict((k, v) for k, v in OLDM.items() if k != "modules")
    mods = OrderedDict()
    for mk, m in S["modules"].items():
        rec = OrderedDict((k, m[k]) for k in ("name", "slug", "act", "track", "where", "gate"))
        rec["lessons"] = OrderedDict()
        mods[mk] = rec
    for nid, r in NEW.items():
        mods[mkey(nid)]["lessons"][nid] = OrderedDict(
            name=r["name"], slug=r.get("slug") if r["kind"].startswith("move") else None,
            topic_filename=r.get("topic_filename") if r["kind"].startswith("move") else None,
            proof=r["proof"], status=r["status"])
    out["total_modules"] = len(mods)
    out["total_lessons"] = len(NEW)
    out["modules"] = mods
    return out


NEWM = new_manifest()


def lesson_dir(manifest, lid: str) -> Path:
    mk = mkey(lid)
    mod = manifest["modules"][mk]
    les = mod["lessons"][lid]
    return ROOT / "lessons" / f"{mk}-{mod['slug']}" / f"{lid}-{les['slug']}"


def old_dir(old: str) -> Path:
    mk, les = OLD_LES[old]
    return ROOT / "lessons" / f"{mk}-{OLDM['modules'][mk]['slug']}" / f"{old}-{les['slug']}"


# ---------------------------------------------------------------- 3. rewriting one source file
MASK = re.compile(r"<pre\b.*?</pre>|<code\b.*?</code>|<svg\b.*?</svg>|<script\b.*?</script>|<style\b.*?</style>"
                  r'|<div class="hero-crumb">.*?</div>|<div class="footer">.*?</div>', re.S | re.I)   # the last two regenerate
LSEQ = re.compile(r"\b([Ll]essons?)(\s+)(" + ID + r"(?:(?:\s*(?:,|and|or|to|&ndash;|–|-|&amp;)\s*)" + ID + r")*)")
POSS = re.compile(r"(?<![\w.])(" + ID + r")(?=(?:'|&#39;|&rsquo;|’)s\b)")
PAREN = re.compile(r"\((" + ID + r"(?:\s*(?:,|and|or)\s*" + ID + r")*)\)")
MODULE = re.compile(r"\b(Module)(\s+)(\d{1,2})\b(?!\.\d)")
KITLINE = re.compile(r"block\(|\bassert\b|\bin src\b|src\[|flatc\(|read_text\(|re\.(?:search|findall|match|sub|split|finditer)\("
                     r"|\.index\(|\.count\(|startswith\(|endswith\(|\.find\(")
MODULES = re.compile(r"\bModules\s+\d{1,2}\b[^.<]{0,60}")
BARE = re.compile(r"(?<![\w./\x01-])(" + ID + r")(?![\w\x02]|\.\d)")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def map_ids(seq: str, where: str, text: str, pos: int) -> str:
    def one(t):
        old = t.group(0)
        if old in MAP:
            return A + MAP[old] + Z
        review.append(f"{where}:{line_of(text, pos)}: a lesson reference names {old}, which is no lesson")
        return old
    return re.sub(ID, one, seq)


def rewrite_text(text: str, where: str, html_part: bool) -> str:
    """The lesson references in one file, with code regions masked in HTML parts."""
    masked = {}

    def hide(m):
        key = f"\x00{len(masked)}\x00"
        masked[key] = m.group(0)
        return key
    body = MASK.sub(hide, text) if html_part else text

    def lseq(m):
        seq = m.group(3)
        if re.search(r"\bto\b|&ndash;|–|-", seq):
            review.append(f"{where}:{line_of(body, m.start())}: a range of lessons, check it in the new order: "
                          f"{m.group(0)[:80]!r} -> {m.group(1)}{m.group(2)}{map_ids(seq, where, body, m.start())}")
        new = m.group(1) + m.group(2) + map_ids(seq, where, body, m.start())
        if new != m.group(0):
            changes.append((where, m.group(0), new))
        return new
    body = LSEQ.sub(lseq, body)

    def poss(m):
        old = m.group(1)
        if old in MAP:
            changes.append((where, old + "'s", MAP[old] + "'s"))
            return A + MAP[old] + Z
        return old
    body = POSS.sub(poss, body)

    def paren(m):
        ids = re.findall(ID, m.group(1))
        if ids and all(i in MAP for i in ids):
            new = "(" + re.sub(ID, lambda t: A + MAP[t.group(0)] + Z, m.group(1)) + ")"
            changes.append((where, m.group(0), new))
            return new
        return m.group(0)
    body = PAREN.sub(paren, body)

    if html_part:
        def module(m):
            n = int(m.group(3))
            if n in WHOLE:
                new = f"{m.group(1)}{m.group(2)}{WHOLE[n]}"
                changes.append((where, m.group(0), new))
                return new
            review.append(f"{where}:{line_of(body, m.start())}: Module {n} is split in the new course (10 to 5 and "
                          f"10, 12 to 5 and 10): {body[max(0, m.start() - 60):m.end() + 40]!r}")
            return m.group(0)
        for m in MODULES.finditer(body):
            review.append(f"{where}:{line_of(body, m.start())}: a plural module reference: {m.group(0)!r}")
        body = re.sub(r"\bModules\s+\d{1,2}\b", lambda m: m.group(0), body)        # plurals: reviewed by hand
        body = MODULE.sub(module, body)
        for m in BARE.finditer(body):
            tok = m.group(1)
            if tok in MAP:
                ctx = body[max(0, m.start() - 50):m.end() + 30].replace("\n", " ")
                if re.search(r"\bLessons?\s+" + re.escape(MAP.get(tok, tok)), ctx):
                    continue
                review.append(f"{where}:{line_of(body, m.start())}: bare {tok} (old lesson {tok} is now {MAP[tok]}): "
                              f"{ctx!r}")
    for key, val in masked.items():
        body = body.replace(key, val)
    return body.replace(A, "").replace(Z, "")


# Hand-written rewrites, reviewed one by one: (old lesson, its text, the new text). They run before the automatic passes,
# and every number in the new text is protected, so nothing maps it again. Closing paragraphs name the next lesson of the
# new order; stale references from an earlier numbering (the kit's comments still use the notebook course's) say what
# they mean; a few texts are kept as they are because they quote the kit or the notebook course.
OVERRIDES = [
    ("3.2", "handed to the batch lane (Module 4)", "handed to the batch lane (lesson 1.5)"),
    ("3.1", "the agents (Module 10)", "the agents (Modules 5 and 10)"),
    ("3.1", "stage 5 is 3.3, and the writing in stage 6 is 3.4.", "stage 5 is 1.3, and the writing in stage 6 is 1.4."),
    ("3.3", "half of hybrid search (lesson 4.5)", "half of hybrid search (lesson 2.2)"),
    ("3.3", "Hybrid retrieval (lesson 4.5) fuses", "Hybrid retrieval (lesson 2.2) fuses"),
    ("3.3", "the Module 4 notebooks", "the Module 4 notebooks"),
    ("3.4", "is Module 4's whole story", "is the story of lessons 1.5 to 1.8"),
    ("3.4", "Module 3 ends here:", "Ingestion ends here:"),
    ("3.4", "Module 4 takes the same records through their lifetime", "Lessons 1.5 to 1.8 take the same records through their lifetime"),
    ("3.4", "the stamps from 3.3, the locator and hash from 3.1", "the stamps from 1.3, the locator and hash from 1.1"),
    ("3.4", "283 retired ones from 3.3", "283 retired ones from 1.3"),
    ("3.4", "It changed in 3.3 twice", "It changed in 1.3 twice"),
    ("3.4", "the count you saw in 3.3", "the count you saw in 1.3"),
    ("4.1", "Module 3 followed a document from bytes to records", "Lessons 1.1 to 1.4 followed a document from bytes to records"),
    ("4.1", "and Module 3's records are the defence", "and the records of lessons 1.1 to 1.4 are the defence"),
    ("4.1", "Two of these are Module 3's records seen from the queue's side",
     "Two of these are lesson 1.4's records seen from the queue's side"),
    ("4.1", "your 3.4 upload left", "your 1.4 upload left"),
    ("4.1", "widen the window if 3.4 was longer ago", "widen the window if 1.4 was longer ago"),
    ("4.1", "your 3.4 upload's request log", "your 1.4 upload's request log"),
    ("4.3", "566 retired rows after 3.3 and 4.2;", "566 retired rows after 1.3 and 1.6;"),
    ("4.3", "the note the way 3.4 wrote it", "the note the way 1.4 wrote it"),
    ("5.1", "Modules 3 and 4 put the records in place", "Module 1 put the records in place"),
    ("5.2", "NP-03 is the clause 5.1 cited", "NP-03 is the clause 2.1 cited"),
    ("5.4", "Module 6 takes the pool from here into the prompt, starting with the budget the packer keeps.",
     "Lesson 2.5 rewrites the question before it reaches this pool and measures whether that helps; Module 3 then takes "
     "the pool into the prompt."),
    ("6.1", "a tenant pack that Module 10 fills as a cached prefix", "a tenant pack that Module 6 fills as a cached prefix"),
    ("6.1", "The teaching split from lesson 4.5 is", "The kit's teaching split is"),
    ("6.1", '<td data-label="On your lane">Module 10; ', '<td data-label="On your lane">Module 6; '),
    ("6.1", "and Module 10 fills it:", "and Module 6 fills it:"),
    ("6.1", "and Module 8 keeps it outside this API", "and Module 6 keeps it outside this API"),
    ("6.2", "a tuned endpoint from Module 10 or a self-hosted route from Module 11",
     "a tuned endpoint from Module 12 or a self-hosted route from Module 9"),
    ("6.2", "which lesson 13's alert will count", "which lesson 11.5's alert will count"),
    ("6.2", "Lesson 6.3 sends the same contract as a stream:",
     "Lesson 3.6 checks each quote against the passage it cites and versions the prompt, and lesson 3.7 sends the same "
     "contract as a stream:"),
    ("6.3", "the role on the service account, which Module 12 does;", "the role on the service account, which Module 4 does;"),
    ("6.3", "That trade is Module 12's to make.", "That trade is Module 4's to make."),
    ("6.3", '<td data-label="On your lane">Module 12</td>', '<td data-label="On your lane">Module 4</td>'),
    ("6.4", "a figure and a table, shaped as Module 9 writes them", "a figure and a table, shaped as Module 7 writes them"),
    ("6.4", "Once Module 10 turns a context cache on", "Once Module 6 turns a context cache on"),
    ("6.4", "Module 6 ends here: the journey from an upload to a cited answer works end to end on your lane. Module 7 measures "
            "how good those answers are, starting with the questions it measures them on.",
     "The journey from an upload to a cited answer now works end to end on your lane. Lesson 3.9 designs a fact-checking "
     "system from these parts, and Module 4 then measures how good the answers are, starting with the questions it "
     "measures them on."),
    ("7.2", "Lesson 7.3 makes a candidate with one setting changed",
     "Lesson 4.3 places these instruments in the pipeline, and lesson 4.4 makes a candidate with one setting changed"),
    ("7.3", "Module 7 ends here: the golden set is sound", "The golden set is sound"),
    ("7.3", "Module 8 turns to security, starting with how an authenticated identity becomes a tenant.",
     "Lesson 4.5 checks the judge against people, and lesson 4.6 turns to security, starting with how an authenticated "
     "identity becomes a tenant."),
    ("8.3", "Module 9 turns from safety to cost, and Lesson 9.1 compares context caching and answer caching on the same "
            "questions.",
     "Lesson 4.9 reads the failures first, then attacks your own pipeline with a held-out set built on this lesson's four "
     "probes."),
    ("9.1", "until 9.3 measures the line", "until 6.4 measures the line"),
    ("9.3", "Module 10 turns from answering to acting: lesson 10.1 reads a tool's contract and runs the direct agent loop.",
     "Lesson 6.5 turns from caches to memory: agent state, conversation history and knowledge, and where each one lives."),
    ("10.1", "Lesson 10.2 opens the LangGraph brain:",
     "Lesson 5.2 exposes the same tools to any MCP client, and lesson 5.4 opens the LangGraph brain:"),
    ("10.3", "Lesson 10.4 puts the same question through all four brains and compares their costs and traces.",
     "Lesson 5.6 puts a door in front of every brain, for the questions the law hands to a person, and lesson 5.7 puts the "
     "same question through all four brains and compares their costs and traces."),
    ("10.4", "is Module 10's gate.", "is Module 5's gate."),
    ("10.4", "Lesson 10.5 puts a door in front of every brain, for the questions the law hands to a person. Lesson 10.6 sends "
             "the other questions to one desk each, and its last box says where Module 11 picks up these conversations.",
     "Lesson 5.8 pauses a turn for a person: approval, clarification and escalation. Module 6 picks up these "
     "conversations, and lesson 10.4 later sends the other questions to one desk each."),
    ("10.5", "Lesson 10.6 sends each of acme's and zeta's other questions to one specialist desk, and every globex question "
             "to the law, and its last box says where Module 11 picks up the conversations the brains and the Desk keep.",
     "Lesson 5.7 puts one question through all four brains and compares their costs and traces. Lesson 10.4 later sends "
     "each of acme's and zeta's other questions to one specialist desk, and every globex question to the law, and Module 6 "
     "picks up the conversations the brains and the Desk keep."),
    ("10.6", "nineteen checks, and Module 10's gate.", "nineteen checks, and Module 5's gate."),
    ("10.6", "Module 10's gate still passes", "Module 5's gate still passes"),
    ("10.6", "Do it: Module 10's gate", "Do it: Module 5's gate"),
    ("10.6", "The module ends where lesson 10.4 set its gate:", "The chat service keeps the gate lesson 5.7 set:"),
    ("10.6", "the roles 10.5 described", "the roles 5.6 described"),
    ("10.6", "which you keep as 10.5 said", "which you keep as 5.6 said"),
    ("10.6", "where 10.5 showed Tell the Desk", "where 5.6 showed Tell the Desk"),
    ("10.6", "passed as in 10.5", "passed as in 5.6"),
    ("10.6", "Module 11 starts from the conversations the brains and the Desk keep: where each one lives, and what else an "
             "agent remembers.",
     "Lesson 10.5 runs one desk as an agent whose every calculator argument is checked, and measures routed desks against "
     "one agent and no agent."),
    ("11.3", "Module 12 opens the service to agents outside the kit, through MCP and A2A.",
     "Lesson 6.8 resumes a turn that was paused or cut off, from its checkpoint."),
    ("12.2", "Lesson 12.3 follows the A2A peer, <code>documind-agent-sa</code>, through this server to rag-api.",
     "Lesson 5.4 opens the LangGraph brain, and lesson 10.6 later follows the A2A peer, <code>documind-agent-sa</code>, "
     "through this server to rag-api."),
    ("12.3", "Module 13 turns to operations: debugging a wrong answer through the whole pipeline, and controlling what the "
             "lane spends.",
     "Lesson 10.7 hands one question from the ADK brain to this peer as a bounded tool, and stops loops and deadlocks "
     "between agents."),
    ("13.1", "the operator venv from Modules 3 to 5", "the operator venv from Modules 1 and 2"),
    ("13.3", "Module 14 releases the lane: lesson 14.1 builds and deploys it with keyless identity.",
     "Lesson 11.7 reproduces the agent failures production shows and no eval row does, each with a drill that restores "
     "itself."),
    ("15.2", "If you skipped 15.1, run its build first", "If you skipped 7.1, run its build first"),
    ("16.2", "Module 17 starts with lesson 17.1: decide whether tuning is justified, and prepare the data.",
     "Module 8 changes the pipeline and measures it, starting with lesson 8.1: the ingest events through Pub/Sub, mapped "
     "to Kafka."),
    ("16.2", "that 16.1 answered from it", "that 7.5 answered from it"),
    ("16.2", "the way 16.1 showed", "the way 7.5 showed"),
    ("17.1", "and 17.3 holds the tuned model", "and 12.3 holds the tuned model"),
    ("17.3", "(lesson 11.4), but nothing writes it", "(the kit's 'pin one tenant' setting), but nothing writes it"),
    ("17.3", "Module 18 turns to where the model runs: lesson 18.1 traces and authorizes the gateway's routes.",
     "Lesson 12.4 closes the loop: a production row becomes a candidate change, gated by eval-live before it is promoted "
     "or rolled back."),
    ("18.4", "and the lane can prove it is off.",
     "and the lane can prove it is off. Module 10 turns to agent patterns, starting with where an agent reasons."),
]
used_overrides = set()


def apply_overrides(old: str, text: str, where: str) -> str:
    for o_old, o_text, n_text in OVERRIDES:
        if o_old != old or o_text not in text:
            continue
        protected = re.sub(r"\d{1,2}(?:\.\d{1,2})?", lambda m: A + m.group(0) + Z, n_text)
        text = text.replace(o_text, protected)
        used_overrides.add((o_old, o_text))
        changes.append((where, o_text, n_text))
    return text


def rewrite_lesson(old: str, nid: str, d: Path):
    """A moved lesson's build.py, lane scripts and parts. A lesson with no build.py (3.1, whose page is written by hand
    and lends every page its setup section) has its page rewritten instead."""
    rec = NEW[nid]
    has_build = (d / "build.py").exists()
    for p in sorted(d.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or p.suffix not in (".py", ".html"):
            continue
        if p.name.endswith("_WIX.html") and has_build:
            continue                                                      # the built page: rebuilt afterwards
        where = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8")
        new = apply_overrides(old, text, where)
        if p.suffix == ".py":
            # A line that looks kit text up (block(), an assert, `in src`, a regex) quotes the kit, whose comments keep the
            # notebook course's numbers ("A tuned model (10.1)"): it stays as it is, or the build stops finding its line.
            new = "\n".join(ln if KITLINE.search(ln) else rewrite_text(ln, where, html_part=False) for ln in new.split("\n"))
            new = new.replace(A, "").replace(Z, "")
        else:
            new = rewrite_text(new, where, html_part=True)                # the title's 'Lesson N.M' is mapped here
        if p.name == "build.py":
            new = re.sub(r'^LESSON = "' + re.escape(old) + '"', f'LESSON = "{nid}"', new, flags=re.M)
            if "<title>" in new and f"<title>Lesson {nid} " not in new:
                review.append(f"{where}: the <title> does not read 'Lesson {nid} ...'")
        if p.suffix == ".html":
            new = re.sub(r'<div class="hero-crumb">.*?</div>', lambda m: f'<div class="hero-crumb">{crumb(nid)}</div>', new,
                         count=1, flags=re.S)
            new = re.sub(r'<div class="footer">.*?</div>', lambda m: footer(nid), new, count=1, flags=re.S)
        if new != text:
            changes.append((where, "(file)", f"rewritten for {old} -> {nid}"))
            if not DRY:
                p.write_text(new, encoding="utf-8", newline="\n")
        if p.name == "build.py" and f'LESSON = "{nid}"' not in new and re.search(r'^LESSON = ', text, re.M):
            review.append(f"{where}: LESSON constant not rewritten")


def crumb(lid: str) -> str:
    mk = mkey(lid)
    return f"Basics &middot; Lesson {lid}" if mk == "B" else f"Module {int(mk)} &middot; {mword(mk)} &middot; Lesson {lid}"


def footer(lid: str) -> str:
    mk = mkey(lid)
    i = ORDER.index(lid)
    nxt = ORDER[i + 1] if i + 1 < len(ORDER) else None
    where = "Basics" if mk == "B" else f"Module {int(mk)} {mword(mk)}"
    tail = f"Next: Lesson {nxt} {NEW[nxt]['name']}." if nxt else "This is the course's last lesson."
    return (f'<div class="footer"><p><strong>Netsetos GenAI on GCP</strong> &middot; {where} &middot; Lesson {lid} '
            f'{NEW[lid]["name"]} &middot; v{OLDM["version"]}</p><p>{tail}</p></div>')


# ---------------------------------------------------------------- 4. the demo tooling
DEMO_FILES = ["tools/workshop_demo_groups.py", "tools/workshop_demo_reviewed.json", "tools/workshop_demo_runtime_adaptations.py",
              "tools/build_workshop_demos.py", "tools/group_workshop_demos.py",
              "tools/workshop_lesson31.py", "tools/workshop_docstrings.py", "pagekit/demo_links.py", "pagekit/pagebuild.py",
              "pagekit/audit_responsive.py", "deploy/workshop_demos/tests/test_lesson31.py", "deploy/workshop_demos/REVIEW.md"]
PAIR = re.compile(r"module_(\d{2})/lesson_(\d{1,2})_(\d{1,2})\b")
LFOLDER = re.compile(r"(?<![/\x01])\blesson_(\d{1,2})_(\d{1,2})\b")
QUOTED = re.compile(r"""(["'])(""" + ID + r""")\1""")


def demo_folder(lid: str) -> str:
    return f"module_{mkey(lid)}/lesson_{lid.replace('.', '_')}"


def rewrite_tooling(text: str, where: str) -> str:
    def pair(m):
        old = f"{int(m.group(2))}.{int(m.group(3))}"
        if old not in MAP:
            return m.group(0)
        return A + demo_folder(MAP[old]) + Z
    text = PAIR.sub(pair, text)

    def lfolder(m):
        old = f"{int(m.group(1))}.{int(m.group(2))}"
        return A + f"lesson_{MAP[old].replace('.', '_')}" + Z if old in MAP else m.group(0)
    text = LFOLDER.sub(lfolder, text)

    def quoted(m):
        old = m.group(2)
        if old in MAP:
            return m.group(1) + A + MAP[old] + Z + m.group(1)
        return m.group(0)
    text = QUOTED.sub(quoted, text)
    text = LSEQ.sub(lambda m: m.group(1) + m.group(2) + map_ids(m.group(3), where, text, m.start()), text)
    for m in re.finditer(r"(?<!\x01)\bmodule_(\d{2})\b(?!/lesson_)", text):
        review.append(f"{where}:{line_of(text, m.start())}: a bare module folder, check it: "
                      f"{text[max(0, m.start() - 40):m.end() + 40]!r}")
    return text.replace(A, "").replace(Z, "")


def main():
    # 1. the manifest
    if not DRY:
        (ROOT / "course-manifest.json").write_text(json.dumps(NEWM, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                                    newline="\n")
    print(f"manifest: {NEWM['total_modules']} modules, {NEWM['total_lessons']} lessons "
          f"({sum(1 for r in NEW.values() if r['kind'].startswith('move'))} built pages moved)")
    # 2. move the built lessons (into a staging name first, since old and new numbers overlap)
    staged = []
    for old, nid in MOVED.items():
        src = old_dir(old)
        if not src.exists():
            review.append(f"{old}: no lesson directory {src.relative_to(ROOT)}")
            continue
        tmp = ROOT / "lessons" / f"_renumber_{nid}"
        git("mv", str(src.relative_to(ROOT)), str(tmp.relative_to(ROOT)))
        staged.append((old, nid, tmp))
    for old, nid, tmp in staged:
        dst = lesson_dir(NEWM, nid)
        if not DRY:
            dst.parent.mkdir(parents=True, exist_ok=True)
        git("mv", str(tmp.relative_to(ROOT)), str(dst.relative_to(ROOT)))
        oldpage = f"Netsetos_GCP_Capstone_{old}_{NEW[nid]['topic_filename']}_WIX.html"
        newpage = f"Netsetos_GCP_Capstone_{nid}_{NEW[nid]['topic_filename']}_WIX.html"
        if oldpage != newpage:
            git("mv", str((dst / oldpage).relative_to(ROOT)), str((dst / newpage).relative_to(ROOT)))
        changes.append((dst.relative_to(ROOT).as_posix(), old, nid))
        rewrite_lesson(old, nid, dst if not DRY else old_dir(old))
    # 4a. the demo folders: built lessons move; merged not-started lessons keep their hand-written files
    W = ROOT / "deploy/workshop_demos"
    stage = []
    for old, nid in list(MOVED.items()) + [(o, n) for o, n in MAP.items() if o not in MOVED]:
        src = W / f"module_{int(old.split('.')[0]):02}" / f"lesson_{old.replace('.', '_')}"
        if not src.exists():
            review.append(f"{old}: no demo folder {src.relative_to(ROOT)}")
            continue
        tmp = W / f"_renumber_{old.replace('.', '_')}"
        git("mv", str(src.relative_to(ROOT)), str(tmp.relative_to(ROOT)))
        stage.append((old, nid, tmp))
    for old, nid, tmp in stage:
        dst = W / demo_folder(nid)
        if old in MOVED or nid in ("11.1", "11.2", "11.3", "11.8"):
            if not DRY:
                dst.parent.mkdir(parents=True, exist_ok=True)
            git("mv", str(tmp.relative_to(ROOT)), str(dst.relative_to(ROOT)))
            continue
        # a merge: keep the hand-written setup/ and recovery/ files, drop the generated ones (they regenerate)
        tracked = subprocess.run(["git", "ls-files", str(tmp.relative_to(ROOT))], cwd=ROOT, capture_output=True,
                                 text=True).stdout.split() if not DRY else []
        for f in tracked:
            rel = Path(f).relative_to(tmp.relative_to(ROOT))
            if rel.parts[0] in ("setup", "recovery"):
                target = dst / rel
                if target.exists():
                    review.append(f"{old}: {rel} would overwrite {target.relative_to(ROOT)}: kept the first")
                    git("rm", "-q", "-f", f)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                git("mv", f, str(target.relative_to(ROOT)))
            else:
                git("rm", "-q", "-f", f)
        changes.append((demo_folder(nid), old, "merged; generated files regenerate"))
    for readme in sorted(W.glob("module_*/README.md")):
        git("rm", "-q", "-f", str(readme.relative_to(ROOT)))                 # module READMEs regenerate for the new modules
    # 4b. the tooling's lesson keys, and the hand-written files inside demo folders
    files = [ROOT / f for f in DEMO_FILES] + sorted(W.glob("module_*/lesson_*/setup/*.py")) + sorted(
        W.glob("module_*/lesson_*/recovery/*.py"))
    for p in files:
        if not p.exists():
            continue
        where = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8")
        new = rewrite_tooling(text, where)
        if new != text:
            changes.append((where, "(file)", "lesson keys rewritten"))
            if not DRY:
                p.write_text(new, encoding="utf-8", newline="\n")
    # report
    if not DRY:
        import shutil
        for leftover in list((ROOT / "lessons").glob("_renumber_*")) + list(W.glob("_renumber_*")):
            shutil.rmtree(leftover)                                       # untracked caches left behind by git mv
        for base in (ROOT / "lessons", W):
            for d in sorted(base.rglob("*"), key=lambda x: -len(x.parts)):
                if d.is_dir() and (not any(d.iterdir()) or all(c.name == "__pycache__" for c in d.iterdir())):
                    shutil.rmtree(d)
    for o_old, o_text, _ in OVERRIDES:
        if (o_old, o_text) not in used_overrides:
            review.append(f"override for {o_old} found no text: {o_text[:80]!r}")
    log = ROOT.parent / "renumber_review.txt"
    log.write_text("\n".join(review) + "\n", encoding="utf-8", newline="\n")
    (ROOT.parent / "renumber_changes.txt").write_text("\n".join(f"{w}: {a!r} -> {b!r}" for w, a, b in changes) + "\n",
                                                      encoding="utf-8", newline="\n")
    print(f"changes: {len(changes)} | for review: {len(review)} (written to {log.resolve()})")


if __name__ == "__main__":
    main()
