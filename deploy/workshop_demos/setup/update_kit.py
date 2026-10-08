"""Optional explicit update. Never reset, force checkout, or discard local files."""
import shutil
import subprocess
from workshop_helpers.config import load_config


def main():
    """Fast-forward the current tracked learner branch without discarding edits.
    
    Example: main()
    """
    root = load_config().kit_root
    executable = shutil.which("git")
    if not executable:
        raise RuntimeError("git is not on PATH.")

    def git(*args):
        """Run a checked Git read/update command inside the configured learner checkout.
        
        Example: git('remote', 'get-url', 'origin')
        """
        return subprocess.run([executable, "-C", str(root), *args], check=True,
                              text=True, capture_output=True, timeout=120).stdout.strip()

    origin = git("remote", "get-url", "origin")
    if origin.rstrip("/").removesuffix(".git") not in {
        "https://github.com/netsetos/agents_workshop_learner",
        "git@github.com:netsetos/agents_workshop_learner",
    }:
        raise RuntimeError("This updater expects the existing agents_workshop_learner clone. Inspect origin manually.")
    branch = git("branch", "--show-current")
    if not branch:
        raise RuntimeError("Detached HEAD: switch to your intended tracked branch first.")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if not upstream.startswith("origin/"):
        raise RuntimeError("This updater expects the current branch to track origin.")
    # Published demos are tracked kit files too; refuse their local edits as well. Untracked files (the IDE's
    # .idea/, a learner's notes) cannot be lost: git pull refuses before it would overwrite one.
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", ".")
    if dirty:
        raise RuntimeError("The kit has local changes. Commit or preserve them yourself before updating.\n" + dirty)
    print("Updating", branch, "from", upstream)
    print(git("pull", "--ff-only"))
    print(git("log", "-1", "--format=kit %h, %cd", "--date=short"))


if __name__ == "__main__":
    main()
