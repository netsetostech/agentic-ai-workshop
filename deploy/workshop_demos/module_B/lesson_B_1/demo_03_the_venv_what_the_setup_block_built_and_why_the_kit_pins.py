"""Lesson B.1: The venv: what the setup block built, and why the kit pins

Inside a venv, sys.prefix is the venv's folder and sys.base_prefix is the Python it was made from; outside one, both name the same folder. Python's documentation says that comparing the two is enough to know whether you are in a venv. The cell below asks that, then asks where python and the two libraries come from, and what google-genai brought with it. The cell below makes a second venv in a temporary folder, without even pip in it, and asks that venv's Python the same questions from the inside. Then it deletes the folder. Neither your system's Python nor ~/basics-venv changes, because a venv is only a folder that points at a base Python; Python's documentation calls venvs disposable, meant to be deleted and made again rather than moved or copied.

Run order inside this file:
1. Where am I? The venv, asked from inside (source window 5)
2. A venv is a folder: make one, ask it, delete it (source window 7)

Prerequisites: workshop setup; see this lesson README.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_where_am_i_the_venv_asked_from_inside(session):
    """Run Where am I? The venv, asked from inside at this checkpoint.

    Inside a venv, sys.prefix is the venv's folder and sys.base_prefix is the Python it was made from; outside one, both name the same folder. Python's documentation says that comparing the two is enough to know whether you are in a venv. The cell below asks that, then asks where python and the two libraries come from, and what google-genai brought with it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in the shell where the setup block activated ~/basics-venv.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python 3.12, running from a venv: True
    `python` on PATH is the venv's: True
    site-packages is inside the venv: True
    numpy 2.5.3, installed in that site-packages: True
    google-genai 2.22.0, installed in that site-packages: True
    google-genai brought 10 more: anyio, distro, google-auth, httpx, pydantic, requests, sniffio, tenacity, typing-extensions, websockets
    its rule for google-auth is google-auth[requests]<3.0.0,>=2.56.0; pip chose 2.60.0
    """
    import re, shutil, sys, sysconfig, warnings
    from importlib import metadata
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    
    venv, base = Path(sys.prefix), Path(sys.base_prefix)     # the venv's folder, and the Python it was made from
    print(f"python {sys.version_info.major}.{sys.version_info.minor}, running from a venv: {venv != base}")
    print("`python` on PATH is the venv's:", Path(shutil.which("python")).parent.parent == venv)
    site = Path(sysconfig.get_paths()["purelib"])            # where pip puts libraries for this Python
    print("site-packages is inside the venv:", site.is_relative_to(venv))
    for name in ("numpy", "google-genai"):
        home = Path(metadata.distribution(name).locate_file("")).resolve()
        print(f"{name} {metadata.version(name)}, installed in that site-packages: {home == site.resolve()}")
    needs = sorted({re.match(r"[\w.-]+", r).group() for r in metadata.requires("google-genai") if "extra ==" not in r})
    print(f"google-genai brought {len(needs)} more:", ", ".join(needs))
    rule = next(r for r in metadata.requires("google-genai") if r.startswith("google-auth"))
    print(f"its rule for google-auth is {rule}; pip chose {metadata.version('google-auth')}")

def step_02_a_venv_is_a_folder_make_one_ask_it_delete(session):
    """Run A venv is a folder: make one, ask it, delete it at this checkpoint.

    The cell below makes a second venv in a temporary folder, without even pip in it, and asks that venv's Python the same questions from the inside. Then it deletes the folder. Neither your system's Python nor ~/basics-venv changes, because a venv is only a folder that points at a base Python; Python's documentation calls venvs disposable, meant to be deleted and made again rather than moved or copied.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop: a second venv in a temporary folder, deleted at the end.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: made throwaway-venv: pyvenv.cfg says include-system-site-packages = false
    its python: running from a venv True, numpy importable False, packages installed 0
    made from the same base Python as this venv: True
    deleted: throwaway-venv exists False; numpy still imports here: True
    """
    import importlib.util, os, shutil, subprocess, sys, tempfile, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    
    root = Path(tempfile.mkdtemp()) / "throwaway-venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(root)], check=True)   # a venv with nothing in it
    cfg = dict(line.split(" = ", 1) for line in (root / "pyvenv.cfg").read_text(encoding="utf-8").splitlines() if " = " in line)
    print(f"made {root.name}: pyvenv.cfg says include-system-site-packages = {cfg['include-system-site-packages']}")
    exe = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")                 # Windows, else macOS and Linux
    probe = ("import sys, importlib.util, importlib.metadata as m; print(sys.prefix != sys.base_prefix, "
             "importlib.util.find_spec('numpy') is not None, len(list(m.distributions())), sys.base_prefix)")
    in_venv, has_numpy, n_packages, its_base = subprocess.run(
        [str(exe), "-c", probe], capture_output=True, text=True, check=True).stdout.split(maxsplit=3)
    print(f"its python: running from a venv {in_venv}, numpy importable {has_numpy}, packages installed {n_packages}")
    print("made from the same base Python as this venv:", Path(its_base.strip()) == Path(sys.base_prefix))
    shutil.rmtree(root.parent)                                # deleting the folder is uninstalling the venv
    print(f"deleted: {root.name} exists {root.exists()}; numpy still imports here: {importlib.util.find_spec('numpy') is not None}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_where_am_i_the_venv_asked_from_inside),
        ('source_7', step_02_a_venv_is_a_folder_make_one_ask_it_delete),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
