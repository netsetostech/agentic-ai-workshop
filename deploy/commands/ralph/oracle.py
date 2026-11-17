#!/usr/bin/env python3
"""The Ralph loop's oracle (workshop lesson 10.10): the checks that decide when the loop's work on statutory_deadline
is done. A coding agent never sees this file: it stays in the kit, outside the workspace the agent works in.

    python -I -B -X utf8 commands/ralph/oracle.py --kit DIR [--mode strong|weak] [--json]

DIR is a copy of the kit's shared/ files desk_calc.py imports and the evals/corpus/ files its selftest reads, with the
candidate's statutory_deadline spliced into the kit's own shared/desk_calc.py (commands/ralph.py builds it, oracle_dir()).
Only the function in scope comes from the candidate, so nothing else an agent changed - a weakened selftest, a new
constant, a test of its own - reaches the verdict.

    weak    desk_calc's own selftest, which checks statutory_deadline on one date: resignation, last working day
            Friday 2 October 2026, wages due Tuesday 6 October. A function that returns 6 October for every
            question passes it
    strong  that selftest, then the acceptance checks below: every day of 2026 for each of the four events against
            the oracle's own count, the events and the dates refused, the result's shape, its sections and its notes

The weak oracle is a test a wrong change also passes; the strong one is the loop's spec. Delete the strong oracle's
sweep over 2026 (the check named "every day of 2026") and make ralph-check shows the placeholder passing it too.

THE COUNT. due() is the oracle's own count of two working days, written apart from the code it judges: the second day
after the last working day that is a Monday to Friday, the desk's reading of s.17(2) (desk_calc.NO_HOLIDAYS).
commands/tests/test_ralph.py holds it equal to the kit's own statutory_deadline on every day of 2026.

NO NETWORK, NO PROCESSES. Before the candidate is imported, no_network() makes the socket module refuse every
connection, every datagram and every name, loopback included, and the process refuses to start another (subprocess,
os.system, os.exec*, os.spawn*, os.posix_spawn, os.fork). commands/thread_replay.py's no_network() is the kit's
model for it; the oracle talks to nothing at all, so it lets nothing through. A candidate's attempt is a failed check
whose detail says what was refused. Guards inside one Python process stop code that uses Python's own socket and
process calls; they are not a sandbox, and code in a process can reach anything in it. So the live loop runs this
file in a container with no network at all (commands/ralph.py, Oracle), and the oracle exits with os._exit() as soon
as its verdict is printed, so nothing a candidate registers runs after it.

THE OUTPUT. One line a check, as desk_calc's selftest prints them ("ok    ..." or "FAIL  ..."), then the verdict. With
--json the last line is "ORACLE-VERDICT " and a JSON object: the mode, passed, and every check with its words, whether
the weak oracle holds it, a detail for people (it may quote the candidate's own error) and a feedback line for the
agent. The loop feeds the agent the check's words and that feedback: for an acceptance check, what the oracle counted
and never an expected value; for the selftest, its own FAIL lines, which the agent's copy of desk_calc.py prints too.
Exit 0 when the oracle passes, 1 when it fails, 2 when it could not run.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
from datetime import date, timedelta

YEAR = 2026
SAMPLES = (("resignation", "2026-10-02"), ("dismissal", "2026-12-31"))      # a Friday; a year's last Thursday
REFUSED_EVENTS = ("closure", "lay-off", "retirement", "", None)
REFUSED_DATES = ("02/10/2026", "2 October 2026", "2026-02-30", "2026-13-01", "", None)
MARK = "ORACLE-VERDICT "


# ----------------------------------------------------------------------------- the guard
def no_network() -> None:
    """For the rest of this process: no connection, no datagram and no name resolved, anywhere; no other process."""
    def connect_to(address, *rest, **kw):
        raise OSError(f"offline: the oracle refused a connection to {address!r}")

    def connect(sock, address, *rest):
        connect_to(address)

    def send(sock, *args):
        raise OSError("offline: the oracle refused to send a datagram")

    def resolve(host, *rest, **kw):
        raise OSError(f"offline: the oracle refused to resolve {host!r}")

    def process(*args, **kwargs):
        raise OSError("offline: the oracle refused to start a process")

    socket.socket.connect = socket.socket.connect_ex = connect
    socket.socket.sendto = socket.socket.sendmsg = send
    socket.create_connection = connect_to
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        setattr(socket, name, resolve)
    subprocess.Popen.__init__ = process
    for name in ("system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp", "startfile",
                 "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
                 "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe"):
        if hasattr(os, name):
            setattr(os, name, process)


# ----------------------------------------------------------------------------- the oracle's own count
def due(day: date) -> date:
    """The second working day after `day`, Monday to Friday: the oracle's count, apart from the code it judges."""
    d, left = day, 2
    while left:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def days(year: int = YEAR):
    d = date(year, 1, 1)
    while d.year == year:
        yield d
        d += timedelta(days=1)


# ----------------------------------------------------------------------------- the checks
class Fail(Exception):
    """A check failed: detail for people, feedback for the agent (the oracle's own words and counts only)."""

    def __init__(self, detail: str, feedback: str = ""):
        super().__init__(detail)
        self.detail = detail
        self.feedback = feedback or "the check failed"       # never the detail, which may quote the candidate


def raised(e: BaseException, calc_error) -> str:
    """What a candidate raised, as the agent may read it: CalcError or a built-in's name, never the candidate's text."""
    if isinstance(e, calc_error):
        return "CalcError"
    return type(e).__name__ if type(e).__module__ == "builtins" else "an exception of its own"


def _why(e: BaseException) -> str:
    return f"{type(e).__name__}: {' '.join(str(e).split())[:160]}"


class Oracle:
    def __init__(self, dc):
        self.dc = dc
        # Read before the candidate runs even once, so nothing it does to the module moves the goalposts.
        self.events, self.calc_error = tuple(dc.EXIT_EVENTS), dc.CalcError
        self.no_holidays, self.cites = dc.NO_HOLIDAYS, dc.cites(["wages_s17_2", "wages_s17_3"])

    def call(self, event, day):
        return self.dc.statutory_deadline(event, day)

    def result(self, event, day) -> dict:
        try:
            r = self.call(event, day)
        except Exception as e:  # noqa: BLE001 - the candidate's failure is the check's
            raise Fail(f"statutory_deadline({event!r}, {day!r}) raised {_why(e)}",
                       f"statutory_deadline raised {raised(e, self.calc_error)} on a question it must answer") from None
        if not isinstance(r, dict):
            raise Fail(f"statutory_deadline returned {type(r).__name__}, not the dict _result() builds",
                       "statutory_deadline did not return the dict _result() builds")
        return r

    # weak: the kit's own selftest -------------------------------------------------------------------------------
    def selftest(self):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = self.dc.selftest()
        except Exception as e:  # noqa: BLE001 - a selftest that cannot finish has failed
            failed = [line[6:] for line in out.getvalue().splitlines() if line.startswith("FAIL  ")]
            raise Fail(f"it stopped with {_why(e)}" + (f" after {len(failed)} failed lines" if failed else ""),
                       f"it stopped with {raised(e, self.calc_error)}" +
                       "".join(f"\n  FAIL  {line}" for line in failed)) from None
        lines = out.getvalue().splitlines()
        failed = [line[6:] for line in lines if line.startswith("FAIL  ")]
        if code != 0 or failed:
            words = f"{len(failed)} of {sum(1 for x in lines if x[:6] in ('ok    ', 'FAIL  '))} lines failed"
            raise Fail(words + "".join(f"\n  FAIL  {line}" for line in failed),
                       words + "".join(f"\n  FAIL  {line}" for line in failed))
        return f"{len(lines) - 1} lines ok"

    # strong: the acceptance checks ------------------------------------------------------------------------------
    def events_taken(self):
        """Each event, and the same event in capitals or title case with spaces around it, answered alike. Whether
        the date is right is the sweep's to say."""
        for ev in self.events:
            plain = self.result(ev, "2026-10-02").get("value")
            for written in (ev.upper(), f"  {ev.title()} "):
                r = self.result(written, "2026-10-02")
                if r.get("value") != plain:
                    raise Fail(f"{written!r} on 2026-10-02 gave {r.get('value')!r}, {ev!r} gave {plain!r}",
                               "an event written in another case, or with spaces around it, gave another date")

    def sweep(self):
        total, wrong, first = 0, 0, None
        for day in days():
            want = due(day).isoformat()
            for ev in self.events:
                total += 1
                try:
                    got = self.call(ev, day.isoformat())["value"]
                except Exception as e:  # noqa: BLE001
                    got = f"raised {raised(e, self.calc_error)}"
                if got != want:
                    wrong += 1
                    first = first or f"{ev} on {day.isoformat()} ({day:%A}): {want} due, {got!r} given"
        if wrong:
            raise Fail(f"{wrong:,} of {total:,} wrong; the first: {first}", f"{wrong:,} of {total:,} wrong")
        return f"{total:,} right"

    def never_a_weekend(self):
        bad = 0
        for day in days():
            try:
                value = self.call("resignation", day.isoformat())["value"]
                bad += date.fromisoformat(value).weekday() >= 5
            except Exception:  # noqa: BLE001 - a value that is no date is the sweep's to count
                continue
        if bad:
            raise Fail(f"{bad} last working days of 2026 gave a Saturday or a Sunday",
                       f"{bad} last working days of 2026 gave a Saturday or a Sunday")

    def date_object(self):
        a, b = self.result("resignation", date(2026, 10, 2)), self.result("resignation", "2026-10-02")
        if a.get("value") != b.get("value"):
            raise Fail(f"a date gave {a.get('value')!r}, its ISO text {b.get('value')!r}",
                       "a date object gave another due date than its ISO text")

    def _refused(self, event, day) -> str | None:
        """None when the call raised CalcError; otherwise what it did instead, in the agent's words."""
        try:
            self.call(event, day)
        except Exception as e:  # noqa: BLE001
            return None if isinstance(e, self.calc_error) else f"raised {raised(e, self.calc_error)}"
        return "returned a result"

    def events_refused(self):
        for ev in REFUSED_EVENTS:
            what = self._refused(ev, "2026-10-02")
            if what:
                raise Fail(f"event {ev!r} {what}", f"an event outside the four {what}, not CalcError")

    def dates_refused(self):
        for day in REFUSED_DATES:
            what = self._refused("resignation", day)
            if what:
                raise Fail(f"last_working_day {day!r} {what}",
                           f"a last working day not written YYYY-MM-DD {what}, not CalcError")

    def shape(self):
        for ev, day in SAMPLES:
            r = self.result(ev, day)
            value = r.get("value")
            if not (r.get("calculator") == "statutory_deadline" and r.get("unit") == "date"
                    and r.get("estimate") is False and isinstance(value, str)):
                raise Fail(f"calculator {r.get('calculator')!r}, unit {r.get('unit')!r}, estimate "
                           f"{r.get('estimate')!r}, value {value!r}",
                           "the result's calculator, unit, estimate or value is not as spec.md says")
            try:
                ok = date.fromisoformat(value).isoformat() == value
            except ValueError:
                ok = False
            if not ok:
                raise Fail(f"value {value!r} is not YYYY-MM-DD", "the value is not a date written YYYY-MM-DD")

    def sections(self):
        r = self.result(*SAMPLES[0])
        got = [b.get("section") for b in r.get("basis") or () if isinstance(b, dict)]
        if r.get("cites") != self.cites or got != ["s.17(2)", "s.17(3)"]:
            raise Fail(f"cites {r.get('cites')!r}, sections {got}", "the result does not cite s.17(2) and s.17(3)")

    def formula(self):
        """The formula shows the last working day, the event and the result's own date due. Whether that date is
        right is the sweep's to say, so deleting the sweep leaves no other check that a fixed date fails."""
        for ev, day in SAMPLES:
            r = self.result(ev, day)
            text, value = str(r.get("formula") or ""), str(r.get("value") or "")
            if not (day in text and ev in text and value and value in text and "working day" in text):
                raise Fail(f"{ev} on {day}: formula {text!r}", "one of the three is missing from it")

    def notes(self):
        notes = [str(n) for n in self.result(*SAMPLES[0]).get("notes") or ()]
        if self.no_holidays not in notes or not any("17(3)" in n for n in notes):
            raise Fail(f"notes {notes!r}", "the notes do not say both things spec.md asks for")

    def checks(self):
        """(the check's words, whether the weak oracle holds it, the check) in the order they run."""
        return [
            ("desk_calc's own selftest", True, self.selftest),
            ("the four events s.17(2) counts from are taken, in any case and with spaces around them", False,
             self.events_taken),
            ("every day of 2026, for each event: the second working day after the last working day, Monday to Friday",
             False, self.sweep),
            ("the due date is never a Saturday or a Sunday", False, self.never_a_weekend),
            ("a last working day given as a date is read as its ISO text", False, self.date_object),
            ("an event s.17(2) does not count from is refused with CalcError", False, self.events_refused),
            ("a last working day not written YYYY-MM-DD is refused with CalcError", False, self.dates_refused),
            ("the result: calculator statutory_deadline, the due date as YYYY-MM-DD text, unit date, not an estimate",
             False, self.shape),
            ("the result cites the Code on Wages, 2019, s.17(2) and s.17(3)", False, self.sections),
            ("the formula shows the last working day, the event and the date due", False, self.formula),
            ("the notes say no holiday calendar is loaded, and that s.17(3) may set another time limit", False,
             self.notes),
        ]


def judge(kit: str, mode: str) -> dict:
    """Every check of `mode` on the candidate in `kit`: {mode, passed, checks: [{what, weak, ok, detail, feedback}]}."""
    sys.path.insert(0, kit)
    no_network()
    try:
        import shared.desk_calc as dc                         # the candidate, spliced into the kit's own file
    except BaseException as e:  # noqa: BLE001 - a module that cannot import fails every check
        what = "shared/desk_calc.py imports"
        return {"mode": mode, "passed": False,
                "checks": [{"what": what, "weak": True, "ok": False, "detail": _why(e),
                            "feedback": f"it did not import: {raised(e, ())}"}]}
    oracle = Oracle(dc)
    out = []
    for what, weak, check in oracle.checks():
        if mode == "weak" and not weak:
            continue
        try:
            detail = check() or ""
            out.append({"what": what, "weak": weak, "ok": True, "detail": detail, "feedback": ""})
        except Fail as f:
            out.append({"what": what, "weak": weak, "ok": False, "detail": f.detail, "feedback": f.feedback})
        except BaseException as e:  # noqa: BLE001 - the check itself could not finish: a failure, with its reason
            out.append({"what": what, "weak": weak, "ok": False, "detail": f"the check stopped: {_why(e)}",
                        "feedback": f"the check stopped: {raised(e, oracle.calc_error)}"})
    return {"mode": mode, "passed": all(c["ok"] for c in out), "checks": out}


def render(verdict: dict) -> str:
    lines = []
    for c in verdict["checks"]:
        head, *more = (c["detail"] or "").split("\n")
        lines.append(("ok    " if c["ok"] else "FAIL  ") + c["what"] + (f" ({head})" if head else ""))
        lines += [f"      {line.strip()}" for line in more]
    failed = sum(not c["ok"] for c in verdict["checks"])
    lines.append(f"{verdict['mode']} oracle: " + ("PASS" if verdict["passed"] else
                                                   f"FAIL, {failed} of {len(verdict['checks'])} checks failed"))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The Ralph loop's oracle on statutory_deadline (lesson 10.10).")
    ap.add_argument("--kit", required=True, help="the oracle's copy of the kit, the candidate spliced in")
    ap.add_argument("--mode", choices=("strong", "weak"), default="strong")
    ap.add_argument("--json", action="store_true", help="end with the verdict as one JSON line")
    a = ap.parse_args(argv)
    if not os.path.isfile(os.path.join(a.kit, "shared", "desk_calc.py")):
        print(f"ERROR: {a.kit} holds no shared/desk_calc.py: commands/ralph.py builds the oracle's copy", file=sys.stderr)
        return 2
    verdict = judge(a.kit, a.mode)
    text = render(verdict) + ("\n" + MARK + json.dumps(verdict, ensure_ascii=False) if a.json else "")
    sys.stdout.write(text + "\n")
    sys.stdout.flush()
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    code = main()
    sys.stderr.flush()
    os._exit(code)              # nothing the candidate registered (atexit, a thread) runs after the verdict
