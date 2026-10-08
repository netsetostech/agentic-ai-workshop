"""Restore lesson 1.1's settings after success OR failure.

Run this before changing lessons or deleting local results. Both restoration
operations are attempted even if one fails. Fixture uploads and roster entries
remain as the HTML intends; this file deletes no documents, chunks or evidence.
It can also restore a backend saved by the old 13-file lesson 1.1 sequence.
"""
from workshop_helpers.lesson31 import restore_cache
from workshop_helpers.session import DemoSession

REPEAT = True  # Cleanup is safe to retry after an interrupted deployment.


def demonstrate(session):
    """Attempt each pending restore independently, retaining flags for any failure.
    
    Example: demonstrate(session)
    """
    errors = []
    operations = [lambda: restore_cache(session)]
    if session.state.get("backend_restore_required"):
        operations.append(session.restore_backend)
    for restore in operations:
        try:
            restore()
        except Exception as error:
            errors.append(str(error))
    if errors:
        raise RuntimeError("Cleanup incomplete; rerun this file after inspecting:\n" + "\n".join(errors))
    session.state["lesson31_closed"] = True
    session.save()
    print("Saved settings restored. Fixtures and local evidence retained.")


def main():
    """Cleanup bypasses demo prerequisites and can run after a failed preparation.
    
    Example: main()
    """
    with DemoSession(__file__, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
