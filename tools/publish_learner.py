"""Publish the kit: deploy/ at HEAD becomes the whole of the public learner repository.

    python tools/publish_learner.py --check                           # scan what would be published, publish nothing
    python tools/publish_learner.py --dest ../agents_workshop_learner           # replace that checkout's files, staged
    python tools/publish_learner.py --dest ../agents_workshop_learner --commit  # and commit, naming this repo's commit

The learner repository is generated. Every file in it comes from deploy/ as committed here, byte for byte,
with its executable bit; a file there that deploy/ does not have is deleted by the next publish. Only what git
tracks under deploy/ travels, so ignored state, caches and tfvars never do. Nothing is copied if
tools/leakscan.py finds anything: key material, a real project id or number, a personal mailbox, a page or a
notebook, or a string you deny (PUBLISH_DENY, .publish-deny).

Pushing stays a separate, deliberate step:  git -C ../agents_workshop_learner push origin main
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.leakscan import deny_strings, refused_name, scan_text  # noqa: E402

LEARNER_REPO = "netsetos/agents_workshop_learner"
PREFIX = "deploy/"


def git(*args, cwd: Path = ROOT, data: bytes | None = None, check: bool = True) -> bytes:
    r = subprocess.run(["git", *args], cwd=str(cwd), input=data, capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}:\n{r.stderr.decode(errors='replace')}")
    return r.stdout


def kit_tree(ref: str = "HEAD") -> list[tuple[str, str, str]]:
    """(mode, blob sha, path relative to deploy/) for every file committed under deploy/ at ref."""
    out = []
    for entry in git("ls-tree", "-r", "-z", ref, "--", PREFIX).split(b"\0"):
        if not entry:
            continue
        meta, path = entry.decode("utf-8").split("\t", 1)
        mode, kind, sha = meta.split()
        if kind != "blob" or not path.startswith(PREFIX):
            continue
        out.append((mode, sha, path[len(PREFIX):]))
    return out


def blobs(shas: list[str]) -> dict[str, bytes]:
    """The contents of many blobs in one git cat-file --batch."""
    raw = git("cat-file", "--batch", data=("\n".join(shas) + "\n").encode())
    out, pos = {}, 0
    for sha in shas:
        nl = raw.index(b"\n", pos)
        header = raw[pos:nl].decode().split()
        size = int(header[2])
        out[sha] = raw[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
    return out


def scan(tree: list[tuple[str, str, str]], content: dict[str, bytes]) -> list[str]:
    deny = deny_strings()
    problems = []
    for mode, sha, rel in tree:
        if mode == "120000":
            problems.append(f"{rel}: a symbolic link (publish copies files only)")
            continue
        if refused_name(rel):
            problems.append(f"{rel}: a file kind that stays in the authoring repo")
            continue
        data = content[sha]
        if b"\0" in data[:8192]:
            continue                                   # binary: images, PDFs
        for what, text in scan_text(data.decode("utf-8", errors="replace"), deny):
            problems.append(f"{rel}: {what}: {text}")
    return problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="scan only; publish nothing")
    ap.add_argument("--dest", help="a checkout of netsetos/agents_workshop_learner")
    ap.add_argument("--commit", action="store_true", help="commit in the destination after staging")
    ap.add_argument("--message", action="append", default=[], help="an extra paragraph for the commit message")
    ap.add_argument("--trailer", action="append", default=[], help="a trailer line for the commit message")
    a = ap.parse_args(argv)
    if not a.check and not a.dest:
        ap.error("--check, or --dest DIR")

    head = git("rev-parse", "HEAD").decode().strip()
    tree = kit_tree()
    if not tree:
        print("nothing committed under deploy/: commit it first", file=sys.stderr)
        return 1
    content = blobs(sorted({sha for _, sha, _ in tree}))
    problems = scan(tree, content)
    if problems:
        print(f"refused: {len(problems)} finding(s), nothing published")
        for p in problems:
            print("  " + p)
        return 1
    print(f"{len(tree)} files under deploy/ at {head[:12]}, nothing private in them")
    if git("status", "--porcelain", "--", PREFIX).strip():
        print("note: deploy/ has uncommitted changes; the publish uses the committed tree at HEAD")
    if a.check:
        return 0

    dest = Path(a.dest).resolve()
    if dest == ROOT or ROOT in dest.parents:
        print("refused: the destination is inside this repository", file=sys.stderr)
        return 1
    remote = git("remote", "get-url", "origin", cwd=dest, check=False).decode().strip()
    if LEARNER_REPO not in remote.removesuffix(".git"):
        print(f"refused: {dest} is not a checkout of {LEARNER_REPO} (origin: {remote or 'none'})", file=sys.stderr)
        return 1

    git("config", "core.autocrlf", "false", cwd=dest)      # the blobs go in byte for byte, whatever the machine
    for p in dest.iterdir():
        if p.name != ".git":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    for mode, sha, rel in tree:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content[sha])
    git("add", "-A", cwd=dest)
    for mode, sha, rel in tree:
        if mode == "100755":
            git("update-index", "--chmod=+x", "--", rel, cwd=dest)

    staged = {}
    for entry in git("ls-files", "-s", "-z", cwd=dest).split(b"\0"):
        if entry:
            meta, path = entry.decode("utf-8").split("\t", 1)
            staged[path] = tuple(meta.split()[:2])
    wrong = [rel for mode, sha, rel in tree if staged.get(rel) != (mode, sha)]
    extra = sorted(set(staged) - {rel for _, _, rel in tree})
    if wrong or extra:
        print(f"refused: the staged tree differs from deploy/ ({wrong[:5]} {extra[:5]})", file=sys.stderr)
        return 1
    status = git("status", "--short", cwd=dest).decode()
    if not status.strip():
        print("the learner repo already matches deploy/ at this commit: nothing to publish")
        return 0
    counts = {}
    for line in status.splitlines():
        counts[line[:2].strip()] = counts.get(line[:2].strip(), 0) + 1
    print("staged in " + dest.name + ": " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    if a.commit:
        msg = [f"Kit from agents_workshop@{head[:12]}",
               f"Generated by tools/publish_learner.py from deploy/ at {head} in the private authoring\n"
               "repository. This repository is replaced on every publish: change the kit there."]
        msg += a.message
        if a.trailer:
            msg.append("\n".join(a.trailer))
        git("commit", "-q", "-F", "-", cwd=dest, data=("\n\n".join(msg) + "\n").encode())
        print("committed " + git("rev-parse", "--short", "HEAD", cwd=dest).decode().strip()
              + f"; push with: git -C {dest} push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
