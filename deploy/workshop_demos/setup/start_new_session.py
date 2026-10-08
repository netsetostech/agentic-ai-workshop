"""Start a fresh lesson run only after the previous run's cleanup was recorded.

Edit LESSON and Run in the same interpreter as the demos. This preserves all
evidence and removes only the active pointer; the next demo creates a new run.
It does not delete fixtures or perform cloud cleanup on your behalf.
"""
import json
from workshop_helpers.config import lesson_folder, load_config

LESSON = "1.8"


def main():
    """Archive the active pointer after checking known cleanup requirements.
    
    Example: main()
    """
    config = load_config()
    base = config.results_dir / lesson_folder(LESSON)
    if (base / "session.lock").exists():
        raise RuntimeError("A demo is running or its lock needs recovery. Do not start another session yet.")
    pointer = base / "active.json"
    if not pointer.exists():
        print("No active run; the next demo will create one.")
        return
    run = json.loads(pointer.read_text(encoding="utf-8"))["run_id"]
    state = json.loads((base / run / "session.json").read_text(encoding="utf-8"))
    if state.get("backend_restore_required"):
        raise RuntimeError("Run this lesson's finish file to restore its saved backend before starting again.")
    mapping_path = config.kit_root / "workshop_demos" / lesson_folder(LESSON) / "lesson_map.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    cleanup = [step["id"] for step in mapping["demos"] if step["category"] == "cleanup"]
    if state["attempts"] and any(step not in state["completed"] for step in cleanup):
        raise RuntimeError("Finish files are still outstanding. Review the lesson README and finish or recover this run.")
    pointer.rename(base / f"archived_{run}.json")
    print("Preserved run:", base / run)
    print("The next demo creates a fresh session.")


if __name__ == "__main__":
    main()
