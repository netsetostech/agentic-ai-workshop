"""Offline checks for make chat-local, the Rs 0 lane of workshop lesson 0.2: the seed and the service open one store.

The recipe's two commands start in two directories: the seed in the kit's root, the service in services/chat.
shared/profile.py's default store, ./documind_chroma, is relative to the directory a process starts in, so until
8 October 2026 the seed filled deploy/documind_chroma and the service opened services/chat/documind_chroma, which
was empty, and answered "local corpus is empty". Both lines now set one absolute DOCUMIND_CHROMA_DIR.

The recipe is read out of the Makefile. For each command, a probe starts where the command starts, with the
variables the command sets, imports shared.profile as the seed and the service import it, and prints the directory
build_store() would open: Chroma's persist_directory, resolved against the directory the process started in. No
Chroma, no Ollama, no make. $(CURDIR) is the kit's root, where the README runs the target, and $(PY) is this python.

Run: python -m unittest discover -s commands/tests -p test_local_lane.py
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
VARIABLE = "DOCUMIND_CHROMA_DIR"                     # what shared/profile.py reads, else its relative default
PROBE = "import os, shared.profile as p; print(os.path.abspath(p.CHROMA_DIR))"


def recipe(target: str) -> list[str]:
    """The target's commands as the shell receives them: one per recipe line, a backslash-newline joined."""
    text = (KIT / "Makefile").read_text(encoding="utf-8")
    body = text.split(f"\n{target}:", 1)[1].split("\n", 1)[1]
    commands, line = [], ""
    for raw in body.split("\n"):
        if not raw.startswith("\t"):
            break
        line += raw[1:]
        if line.endswith("\\"):
            line = line[:-1]
            continue
        commands.append(line)
        line = ""
    return commands


def start(command: str) -> tuple[Path, dict, list[str]]:
    """Where a recipe command starts, the variables it sets and the program it runs: each `cd DIR &&` moves it, and
    the NAME=value words before the program are its environment. $(CURDIR) and $(PY) are expanded as make would."""
    *moves, run = [part.strip() for part in command.split("&&")]
    cwd = KIT
    for move in moves:
        word, where = shlex.split(move)
        assert word == "cd", move
        cwd = cwd / where
    words = [w.replace("$(CURDIR)", str(KIT)).replace("$(PY)", sys.executable) for w in shlex.split(run)]
    assert not any("$(" in w for w in words), f"a make variable this test does not expand: {run}"
    env = {}
    while words and re.fullmatch(r"[A-Z_][A-Z0-9_]*=.*", words[0]):
        name, value = words.pop(0).split("=", 1)
        env[name] = value
    return cwd, env, words


def opened(cwd: Path, env: dict) -> Path:
    """The directory build_store() opens in a process started in `cwd` with `env` set, in a shell with no DOCUMIND_
    variable and no PYTHONPATH of its own."""
    clean = {k: v for k, v in os.environ.items()
             if not k.startswith("DOCUMIND_") and k not in ("PYTHONPATH", "PYTHONSAFEPATH")}
    r = subprocess.run([sys.executable, "-c", PROBE], cwd=str(cwd), env={**clean, **env},
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return Path(r.stdout.strip()).resolve()


class ChatLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        commands = recipe("chat-local")
        assert len(commands) == 2, commands                  # the seed, then the service
        cls.seed, cls.service = (start(c) for c in commands)

    def test_the_recipe_seeds_from_the_root_then_serves_from_services_chat(self):
        cwd, env, run = self.seed
        self.assertEqual((cwd, env.get("DOCUMIND_PROFILE"), run[1:]),
                         (KIT, "local", ["-m", "shared.local_corpus", "acme"]))
        cwd, env, run = self.service
        self.assertEqual(cwd.resolve(), (KIT / "services" / "chat").resolve())
        self.assertEqual((env.get("DOCUMIND_PROFILE"), env.get("PYTHONPATH"), run[1:4]),
                         ("local", "../..", ["-m", "uvicorn", "agent:app"]))
        for _, env, _ in (self.seed, self.service):
            self.assertTrue(os.path.isabs(env.get(VARIABLE, "")), f"{VARIABLE} is not an absolute path: {env}")

    def test_the_seed_and_the_service_open_one_directory(self):
        seed, service = (opened(cwd, env) for cwd, env, _ in (self.seed, self.service))
        self.assertEqual(seed, service, "the service would open an empty store: local corpus is empty")
        self.assertEqual(seed, (KIT / "documind_chroma").resolve())

    def test_the_relative_default_alone_would_open_two(self):
        """Why the recipe names the directory, and proof that the probe tells the two apart."""
        seed, service = (opened(cwd, {k: v for k, v in env.items() if k != VARIABLE})
                         for cwd, env, _ in (self.seed, self.service))
        self.assertEqual(seed, (KIT / "documind_chroma").resolve())
        self.assertEqual(service, (KIT / "services" / "chat" / "documind_chroma").resolve())


if __name__ == "__main__":
    unittest.main()
