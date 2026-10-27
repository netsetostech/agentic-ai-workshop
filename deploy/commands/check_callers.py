#!/usr/bin/env python3
"""make check-callers GRAPH=1: who may invoke whom on the lane, as service edges, and a cycle refused (workshop
lesson 10.7). Offline: no gcloud, no credential, Rs 0.

    python commands/check_callers.py --graph [--kit DIR]       # from deploy/; --kit reads another copy of the kit

Who may invoke a Cloud Run service is the callee's own IAM binding, roles/run.invoker, made by the script that deploys
it. terraform/sa.tf's caller graph names the services on the request path and that script for each (the authoring
repository's gate, tools/check_authz.py, holds the graph and the scripts equal). This reads each of those scripts as it
stands: the account its `gcloud run deploy` runs the service as (--service-account) and the accounts its invoker
bindings name, a `for` loop expanded. A service whose account may invoke another is an edge between the two. It
prints the services, the edges and then either `acyclic` with an order in which every service may call only services
after it, or the first cycle a walk in the graph's order meets, `cycle: a -> b -> a`, and exits 1. A caller that runs
no service (a person's account, the eval fixtures, Google's service agents) has no edge into it, so it closes no
cycle.

Why a cycle matters here: every service holds a request while it waits on the one it calls, and each has a fixed
number of slots (documind-chat --concurrency=20 on at most 10 instances, documind-agent 20 on at most 5). With an edge
back from documind-agent to documind-chat, a hand-off could come back to a chat that is waiting on it; under load each
side fills its slots with requests waiting on the other, a deadlock across services that only timeouts end. An
acyclic graph rules that out by construction for the lane's own services. It cannot see an agent the lane does not
run: services/agent/chain.py refuses a loop through one at run time (PEER_CHAIN=on).

GRAPH=1 is the only mode so far: comparing these bindings with each service's live IAM policy is not built yet.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
# sa.tf's caller graph: `#   documind-api    <- a, b, c  (lesson-12.2.sh)` - the service, its callers, its script
GRAPH_LINE = re.compile(r"^#\s+(documind-[a-z]+)\s+<-\s+(.+?)\s+\(((?:lesson-[\d.]+|gchat)\.sh)\)\s*$", re.M)


def account(member: str) -> str:
    """An account as the graph names it: documind-x-sa, or a Google service agent as gcp-sa-x."""
    m = re.search(r"documind-[a-z]+-sa\b", member)
    if m:
        return m.group(0)
    m = re.search(r"@(gcp-sa-[a-z]+)\.", member)
    return m.group(1) if m else member


def deployed_as(script: str, service: str) -> str | None:
    """The account a script's `gcloud run deploy <service>` runs the service as."""
    text = script.replace("\\\n", " ")
    m = re.search(rf"gcloud run deploy {re.escape(service)}(?=\s)([^\n]*)", text)
    flag = re.search(r"--service-account[= ](\S+)", m.group(1)) if m else None
    return account(flag.group(1)) if flag else None


def invokers(script: str, service: str) -> set[str]:
    """The accounts a script binds roles/run.invoker on `service`, a `for VAR in a b c; do` loop expanded."""
    text = script.replace("\\\n", " ")
    found: set[str] = set()
    for m in re.finditer(rf"gcloud run services add-iam-policy-binding\s+{re.escape(service)}(?=\s)([^\n]*)", text):
        rest = m.group(1)
        member = re.search(r'--member[= ]"?serviceAccount:([^"\s]+)', rest)
        if "roles/run.invoker" not in rest or not member:
            continue
        var = re.match(r"\$\{?(\w+)\}?@", member.group(1))
        if var:
            loops = [lm for lm in re.finditer(r"for\s+(\w+)\s+in\s+([^;\n]+);\s*do", text[:m.start()])
                     if lm.group(1) == var.group(1)]
            found.update(account(word) for word in (loops[-1].group(2).split() if loops else []))
        else:
            found.add(account(member.group(1)))
    return found


@dataclass
class Graph:
    services: list[str]                                            # in sa.tf's order
    script: dict[str, str] = field(default_factory=dict)          # service -> the script that deploys it
    runs_as: dict[str, str | None] = field(default_factory=dict)  # service -> its account
    callers: dict[str, set[str]] = field(default_factory=dict)    # service -> the accounts that may invoke it
    edges: dict[str, list[str]] = field(default_factory=dict)     # service -> the services its account may invoke


def read_graph(kit: Path = KIT) -> Graph:
    """The graph as the deploy scripts make it, for the services sa.tf's caller graph names."""
    lines = [(m.group(1), m.group(3)) for m in GRAPH_LINE.finditer((kit / "terraform" / "sa.tf").read_text(encoding="utf-8"))]
    if not lines:
        raise SystemExit("terraform/sa.tf has no caller graph (lines like `#   documind-api  <- ...  (lesson-12.2.sh)`)")
    g = Graph(services=[s for s, _ in lines])
    for service, script in lines:
        text = (kit / "commands" / script).read_text(encoding="utf-8")
        g.script[service], g.runs_as[service], g.callers[service] = script, deployed_as(text, service), invokers(text, service)
    for s in g.services:
        g.edges[s] = [t for t in g.services if g.runs_as[s] and g.runs_as[s] in g.callers[t]]
    return g


def cycle(g: Graph) -> list[str] | None:
    """The first cycle a depth-first walk meets, services and edges taken in sa.tf's order, as [a, b, ..., a]."""
    state: dict[str, int] = {}                     # 1: on the walk's path; 2: done, no cycle through it
    path: list[str] = []

    def walk(s: str) -> list[str] | None:
        state[s] = 1
        path.append(s)
        for t in g.edges[s]:
            if state.get(t) == 1:
                return path[path.index(t):] + [t]
            if t not in state and (found := walk(t)):
                return found
        path.pop()
        state[s] = 2
        return None

    for s in g.services:
        if s not in state and (found := walk(s)):
            return found
    return None


def order(g: Graph) -> list[str]:
    """An order in which every service may call only services after it (the graph must be acyclic)."""
    into = {s: sum(s in g.edges[t] for t in g.services) for s in g.services}
    out: list[str] = []
    while len(out) < len(g.services):
        s = next(s for s in g.services if s not in out and into[s] == 0)
        out.append(s)
        for t in g.edges[s]:
            into[t] -= 1
    return out


def report(g: Graph) -> int:
    width = max(len(s) for s in g.services) + 2
    print("each service, the account it runs as, and the script that deploys it and binds its invokers:")
    for s in g.services:
        print(f"  {s:<{width}}{g.runs_as[s] or '(no --service-account)':<22}{g.script[s]}")
    print("\nservice -> service: the caller's account holds roles/run.invoker on the callee")
    for s in g.services:
        for t in g.edges[s]:
            print(f"  {s} -> {t}")
    accounts = set(filter(None, g.runs_as.values()))
    others = sorted(set().union(*g.callers.values()) - accounts)
    print(f"\ncallers that run no service, so nothing calls them and they close no cycle: {', '.join(others) or 'none'}")
    found = cycle(g)
    if found:
        back, to = found[-2], found[-1]
        print(f"\ncycle: {' -> '.join(found)}")
        print(f"  ({g.runs_as[back]} may invoke {to}: a request can come back to a service that is waiting on it)")
        return 1
    print(f"\nacyclic: {', '.join(order(g))}")
    print("  (each service may call only services after it, so no request can wait on itself)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--graph", action="store_true", help="read the graph from the deploy scripts (offline)")
    ap.add_argument("--kit", type=Path, default=KIT, help="the kit to read (default: this one)")
    args = ap.parse_args(argv)
    if not args.graph:
        print("check_callers.py: --graph (make check-callers GRAPH=1) is the only mode; the comparison with each "
              "service's live IAM policy is not built yet.", file=sys.stderr)
        return 2
    return report(read_graph(args.kit))


if __name__ == "__main__":
    sys.exit(main())
