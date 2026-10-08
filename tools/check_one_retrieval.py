#!/usr/bin/env python3
"""Fail if DocuMind's agent tool layer grows a second retrieval implementation.

This is the check lesson 8.7 describes. Run it on the deployed tree:

    python tools/check_one_retrieval.py deploy/

Exit 0 when exactly one function implements retrieval, 1 otherwise.

WHY IT PARSES INSTEAD OF GREPPING
    Grep finds the spelling you thought of. Nobody duplicates `retrieve` and keeps the name -
    the second copy is called `quick_lookup` or `fetch_context`, written under deadline by
    someone who needed a different top_k. So the rule is about SHAPE: a function that takes a
    query and reaches the corpus itself.

WHY IT HAS A SCOPE
    `deploy/services/rag-api/` IS the retrieval service. It embeds, searches and reranks, and
    that is its job - it is the thing being called, not a duplicate of the thing calling it.
    Pointing this check at the whole tree flags the service too, and a check that cries wolf
    gets disabled in week two, after which it checks nothing at all.

    The scope is therefore the AGENT TOOL LAYER: deploy/shared/ plus each service's tools.py.

WHY IT SKIPS DELEGATORS
    Adapters are the point. Every brain needs one - to bind a tenant, rename a filter, reshape a
    response. An adapter whose body calls documind_tools.retrieve is not an implementation.

WHY IT ALLOWS LANES
    The one implementation has two backends since gap G3 - rag-api over the network, or a
    Chroma directory when DOCUMIND_PROFILE=local - and the local one is a private helper in
    the SAME module as the public `retrieve`. A helper that only `retrieve` calls is what the
    implementation does, not a second one. So a `_`-prefixed function counts only when it
    lives in a module that has no public `retrieve` of its own.

WHY IT READS THE IMPORTS (13 September 2026)
    shared/ is where the tool layer lives, but not only: a module the RETRIEVAL SERVICE
    imports - shared/documind_graph.py, 4.6's graph store, which rag-api's retriever walks
    and the ingest builder writes - is a stage of the one thing being called, exactly like
    the service's own retriever.py. It is exempt when services/rag-api/ imports it and no
    tool-layer file does; the exemption is printed, so it is read, not trusted. A brain or
    a tools.py that starts importing it would put it back in scope.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

QUERYISH = {"query", "q", "question", "search_query"}
CORPUS = ("/v1/query", "find_neighbors", "vector", "embed", "corpus", "chunk")


def in_scope(path: Path, root: Path) -> bool:
    """The agent tool layer: shared/, and any service's tools.py."""
    rel = path.relative_to(root).as_posix()
    return rel.startswith("shared/") or rel.endswith("/tools.py") or rel == "tools.py"


def imports_of(path: Path) -> set[str]:
    """The `shared.<module>` names a file imports, from `import shared.x` or `from shared.x import y`."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("shared."):
            out.add(n.module.split(".")[1])
        elif isinstance(n, ast.Import):
            out |= {a.name.split(".")[1] for a in n.names if a.name.startswith("shared.")}
    return out


def service_owned(root: Path) -> dict[str, str]:
    """shared/ modules that are the retrieval service's own stages: imported under services/rag-api/ and by no
    file of the tool layer (another shared/ module, a tools.py). Module stem -> the service file that imports it."""
    by_service: dict[str, str] = {}
    for path in sorted((root / "services" / "rag-api").rglob("*.py")):
        for stem in imports_of(path):
            by_service.setdefault(stem, path.relative_to(root).as_posix())
    for path in sorted(root.rglob("*.py")):
        if in_scope(path, root):
            for stem in imports_of(path):
                by_service.pop(stem, None)          # the tool layer reaches it: in scope after all
    return by_service


def delegates(node: ast.AST) -> bool:
    """True when the body hands off to something's .retrieve() - i.e. it is an adapter."""
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "retrieve"
        for n in ast.walk(node)
    )


def implementations(root: Path, exempt: list[str] | None = None) -> list[str]:
    found: list[str] = []
    owned = service_owned(root)
    for path in sorted(root.rglob("*.py")):
        if not in_scope(path, root):
            continue
        service_stage = path.parent == root / "shared" and path.stem in owned
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        owns_retrieve = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and n.name == "retrieve" for n in tree.body)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not ({a.arg for a in node.args.args} & QUERYISH):
                continue
            if delegates(node):
                continue
            if owns_retrieve and node.name.startswith("_"):
                continue      # a lane of this module's own retrieve, not a second implementation
            # Compare code, not prose: a docstring that mentions "corpus" is not an
            # implementation, and counting it is how a check earns its reputation for lying.
            stmts = node.body
            if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant):
                stmts = stmts[1:]
            body = "\n".join(ast.get_source_segment(src, s) or "" for s in stmts)
            if any(marker in body for marker in CORPUS):
                hit = f"{path.relative_to(root).as_posix()}:{node.lineno} {node.name}()"
                if service_stage:
                    if exempt is not None:
                        exempt.append(f"{hit} - the retrieval service's own stage: imported by {owned[path.stem]}, by no tool-layer file")
                else:
                    found.append(hit)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default="deploy", type=Path)
    args = ap.parse_args()
    if not args.root.is_dir():
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2

    exempt: list[str] = []
    found = implementations(args.root, exempt)
    for e in exempt:
        print(f"  skip {e}")
    for f in found:
        print(f"  {f}")
    if len(found) == 1:
        print(f"OK - one retrieval implementation under {args.root}/")
        return 0
    print(f"FAIL - expected exactly 1 retrieval implementation, found {len(found)}", file=sys.stderr)
    print("Make the extra one an adapter that calls documind_tools.retrieve.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
