"""The rules a prompt version adds to SYSTEM (workshop lesson 12.4): prompt_rules.json, read and checked.

generator.py sets SYSTEM once, to the literal its five rules are written in: the text evals/make_trainset.py copies (a
tuned model is served behind the prompt it was trained behind, lessons 12.1-12.3), the text make prompt-version hashes
(lesson 3.6) and the text the lessons quote. A prompt version may add rules after those five. generator.py's last two
lines rebind SYSTEM to with_rules(SYSTEM, prompt_id, prompt_version): SYSTEM, then the version's rules, numbered on
from 6 the way evals/prompt_bench.py's edit_system() numbers a rule the bench adds (lessons 3.1-3.3), so a rule measured
on the bench is the rule a version serves. v3, config.py's default, adds none, and SYSTEM is the literal, byte for byte.

A version is served when prompt_rules.json lists it, or when prompt_versions.json registers it as prompt_id@version
(lesson 3.6: a version made by editing SYSTEM itself, which adds nothing here). Any other PROMPT_VERSION is refused at
import, as config.py refuses an unknown QUERY_REWRITE: a typo, or an image built before the version was accepted, must
not answer with SYSTEM alone while /version and every usage row name the version.

What a rule may be (problems()):
- one line of at most MAX_WORDS words, without its number: its place gives it one;
- nothing SYSTEM's rules forbid (FORBIDDEN, phrases matched whole words, inflected or quoted, case and spacing aside):
  a rule that refuses less, answers past the numbered context, drops the citations or sets the rules aside is refused
  here, at Rs 0. A rule worded past these phrases is the gate's to stop: every candidate is judged on refusal_rate
  (evals/run_eval.py's THRESHOLDS: 90% of the rows the corpus cannot answer, refused) and on required.json's rows before
  it is promoted;
- new: not already a rule of its version.
The file is append-only (problems_in()): each version's rules begin with the rules of the version before it, unchanged,
so a version can only add. evals/improve.py writes a new version after a person accepts its rule and never edits one;
extends() is the check on that write. A version the gate turns down goes with a git revert of the commit that added
it: no traffic reached it, and the next rule is accepted on the version before.

Standard library only: generator.py imports it at the end, and evals/improve.py and evals/tests/test_prompt_rules.py
load it by path.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE / "prompt_rules.json"
REGISTRY = HERE / "prompt_versions.json"          # lesson 3.6's registry: label -> the sha256 of its text
MAX_WORDS = 40
VERSION = re.compile(r"v([1-9][0-9]*)")           # config.py's form: v3, v4, ...
OWN_RULE = re.compile(r"^([0-9]+)\. \S")          # one of SYSTEM's numbered lines

# What SYSTEM's own rules forbid a later rule to say: (the rule, what it holds, the phrases that undo it). A phrase is
# matched as whole words in the rule lower-cased, its spacing collapsed, its apostrophes made straight and its quote
# marks read as spaces, each word in its plain inflections too ("never refused", "overrides": 13 October 2026), and a
# match refuses the rule however reasonable the rest of it reads: "Do not use outside knowledge" repeats rule 1 anyway.
FORBIDDEN = (
    (3, "say so, answerable=false, when the context does not hold the answer",
     ("never refuse", "do not refuse", "don't refuse", "must not refuse", "never decline", "do not decline",
      "always answer", "always give an answer", "always provide an answer", "answer every question",
      "answer all questions", "answer any question", "answerable=true", "answerable = true", "answerable to true",
      "answerable true", "never say you don't know", "never say you do not know", "never say the context")),
    (1, "answer only from the numbered context, and never invent sources",
     ("your own knowledge", "general knowledge", "prior knowledge", "world knowledge", "background knowledge",
      "outside knowledge", "training data", "from memory", "best guess", "educated guess", "fill in the gaps",
      "fill the gaps", "fill the gap", "make up", "fabricate")),
    (2, "cite with [N]",
     ("without citations", "without citing", "without a citation", "no citations", "skip citations",
      "skip the citations", "omit citations", "omit the citations", "do not cite", "don't cite", "never cite")),
    (5, "a quote is the clause that answers, never a whole section",
     ("whole section", "entire section", "full section", "whole document", "entire document")),
    (None, "the rules above",
     ("ignore the rules", "ignore the above", "ignore previous", "ignore the context", "ignore all", "disregard",
      "override", "overrule")),
)


class RulesError(Exception):
    """prompt_rules.json, or a PROMPT_VERSION, the rag-api must not answer under: refused at import."""


def _plain(text: str) -> str:
    return " ".join(text.replace("’", "'").replace("‘", "'").casefold().split())


def _forms(word: str) -> str:
    """A phrase's word as a pattern: the word, or its plain inflections ("refuse": refuses, refused, refusing;
    "override": overrides, overridden) - "never refused" and "overrides the context" say what the phrase says. A word
    with a sign in it (answerable=true, don't) is itself alone."""
    if not word.isalpha():
        return re.escape(word)
    stem = word[:-1] if word.endswith("e") else word
    return f"(?:{stem}(?:s|es|d|ed|ing|den)|{word})"           # the longer form first: one span in any engine


# One pattern a phrase, whole words: the quote marks around a phrase are spaces by the time it is searched (_bare).
_PHRASE = {phrase: re.compile(r"(?<![\w'])" + " ".join(_forms(w) for w in phrase.split()) + r"(?![\w'])")
           for _, _, phrases in FORBIDDEN for phrase in phrases}


def _bare(plain: str) -> str:
    """_plain's text with every quote mark a space: 'best guess' in quotes is best guess (an apostrophe inside a word,
    don't, stays)."""
    return " ".join(re.sub(r"[\"“”]|(?<!\w)'|'(?!\w)", " ", plain).split())


def problems(rule, before=()) -> list[str]:
    """Why `rule` may not follow `before` (the version's rules ahead of it); empty when it may."""
    if not isinstance(rule, str):
        return ["a rule is a line of text"]
    if not rule.strip():
        return ["a rule is a line of text, and this one is empty"]
    out = []
    if rule != rule.strip():
        out.append("no space before or after it")
    if any(ord(c) < 32 for c in rule):
        out.append("one line, with no tab or control character")
    words = len(rule.split())
    if words > MAX_WORDS:
        out.append(f"{words} words; a rule has at most {MAX_WORDS}")
    if re.match(r"\s*[0-9]+[.)]\s", rule):
        out.append("written without its number: its place gives it one")
    plain, bare = _plain(rule), _bare(_plain(rule))
    for number, holds, phrases in FORBIDDEN:
        spans: set = set()
        for phrase in phrases:
            hit = _PHRASE[phrase].search(bare)
            if hit and hit.span() not in spans:            # "fill the gap", inflected, is "fill the gaps": said once
                spans.add(hit.span())
                undoes = f"SYSTEM's rule {number} ({holds})" if number else holds
                out.append(f'"{phrase}" undoes {undoes}')
    if re.search(r"\b(context|question):", plain):
        out.append("Context: and Question: are the prompt's own labels, where the sources and the question begin")
    if re.search(r"\brules? [0-9]", plain):
        out.append("a rule stands alone and names no other rule by its number")
    if plain in {_plain(r) for r in before if isinstance(r, str)}:
        out.append("already a rule of this version")
    return out


def read(path) -> dict:
    """A JSON file, parsed, with a key written twice refused: a version has one list of rules."""
    path = Path(path)

    def once(pairs):
        keys = [k for k, _ in pairs]
        twice = sorted({k for k in keys if keys.count(k) > 1})
        if twice:
            raise RulesError(f"{path.name}: {', '.join(twice)} written twice")
        return dict(pairs)

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=once)
    except OSError as e:
        raise RulesError(f"{path.name}: cannot read it ({e.strerror or e})") from None
    except ValueError as e:
        raise RulesError(f"{path.name}: not JSON ({e})") from None


def problems_in(doc) -> list[str]:
    """Why this prompt_rules.json may not be served: its shape, each rule (problems()), and append-only, version by
    version in their numbers' order."""
    versions = doc.get("versions") if isinstance(doc, dict) else None
    if not isinstance(versions, dict) or not versions:
        return ['no "versions" object of version -> {"rules": [...]}']
    out = [f"{v!r}: a version is v and a number, as config.py's prompt_version is" for v in versions
           if not VERSION.fullmatch(v)]
    before = None
    for v in sorted((v for v in versions if VERSION.fullmatch(v)), key=lambda v: int(v[1:])):
        rules = versions[v].get("rules") if isinstance(versions[v], dict) else None
        if not isinstance(rules, list) or not all(isinstance(r, str) for r in rules):
            out.append(f'{v}: needs "rules", a list of lines of text')
            continue
        for i, rule in enumerate(rules):
            out += [f"{v}, added rule {i + 1}: {p}" for p in problems(rule, rules[:i])]
        if before and rules[:len(before[1])] != before[1]:
            out.append(f"{v}: its rules must begin with {before[0]}'s {len(before[1])}, unchanged (append-only: a "
                       "version adds rules and never edits or drops one)")
        before = (v, rules)
    return out


def load(path=None) -> dict:
    """prompt_rules.json, refused whole when anything in it is (problems_in())."""
    path = Path(path or RULES)
    doc = read(path)
    bad = problems_in(doc)
    if bad:
        raise RulesError(f"{path.name}: " + "; ".join(bad))
    return doc


def extends(old: dict, new: dict) -> list[str]:
    """Why `new` is not `old` with versions added: every version `old` lists is in `new`, unchanged."""
    was, now = old["versions"], new["versions"]
    return ([f"{v}: dropped; a version stays once it is written" for v in was if v not in now]
            + [f"{v}: changed; a version is never edited, and a new rule is a new version" for v in was
               if v in now and now[v] != was[v]])


def dumps(doc: dict) -> str:
    """The file's own format, which evals/improve.py writes: an accepted version's diff is only the lines it adds."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def registered(path=None) -> set[str]:
    """The labels lesson 3.6's registry holds (prompt_versions.json's "versions")."""
    path = Path(path or REGISTRY)
    versions = read(path).get("versions")
    if not isinstance(versions, dict):
        raise RulesError(f'{path.name}: no "versions" object of label -> sha256')
    return set(versions)


def rules_for(prompt_id: str, version: str, rules_path=None, registry_path=None) -> list[str]:
    """The rules `version` adds to SYSTEM: its own when prompt_rules.json lists it, none when lesson 3.6's registry
    holds prompt_id@version, and a RulesError for any other version."""
    rules_path, registry_path = Path(rules_path or RULES), Path(registry_path or REGISTRY)
    versions = load(rules_path)["versions"]
    if version in versions:
        return list(versions[version]["rules"])
    label = f"{prompt_id}@{version}"
    try:
        if label in registered(registry_path):
            return []
    except RulesError as e:
        raise RulesError(f"PROMPT_VERSION={version!r}: {rules_path.name} does not list it, and {e}") from None
    listed = ", ".join(sorted(versions, key=lambda v: int(v[1:])))
    raise RulesError(f"PROMPT_VERSION={version!r}: {rules_path.name} lists {listed} and {registry_path.name} does not "
                     f"register {label}, so this image does not carry that version (a typo, an image built before its "
                     f"rule was accepted, or a version reverted since) and would answer with SYSTEM alone as {label}. "
                     "Set PROMPT_VERSION to a version the image lists, or take it off the service")


def own_rules(system: str) -> int:
    """How many numbered rules SYSTEM ends with. A version's rules follow them, so SYSTEM must end with its numbered
    lines and a newline, as generator.py's does; any other shape is refused rather than guessed at."""
    lines = system.split("\n")
    if lines[-1] != "":
        raise RulesError("SYSTEM must end with a newline after its last rule for a version's rules to follow it")
    count = 0
    for line in lines[:-1]:
        m = OWN_RULE.match(line)
        if m and int(m.group(1)) == count + 1:
            count += 1
        elif count:
            raise RulesError(f"SYSTEM has a line after its numbered rules: {line[:60]!r}")
    if not count:
        raise RulesError("SYSTEM has no numbered rules for a version's rules to follow")
    return count


def numbered(system: str, rules) -> str:
    """SYSTEM with `rules` appended, one a line, numbered on from its own last rule: "6. ..." after its five."""
    first = own_rules(system) + 1
    return system + "".join(f"{n}. {rule}\n" for n, rule in enumerate(rules, first))


def with_rules(system: str, prompt_id: str, version: str, rules_path=None, registry_path=None) -> str:
    """SYSTEM as `version` serves it: the literal itself when the version adds no rules (v3), else numbered()."""
    rules = rules_for(prompt_id, version, rules_path, registry_path)
    return numbered(system, rules) if rules else system
