"""Prepare lesson 1.1 at the unnumbered HTML setup heading.

Use the existing rag-shell-venv interpreter after workshop_demos/setup/bootstrap.py.
Project/region come from setup/config/settings.local.json, not shell exports.
This saves ACME's existing retrieval backend and pins it to Vector Search.
If SEMANTIC_CACHE=on, it temporarily disables that API-wide setting by creating
a Cloud Run revision; setup/finish.py restores it and the backend, even after a
failed demo. No cache entries are deleted. Keep the local results directory.
"""
import time

from workshop_helpers.lesson31 import prepare_cache, require
from workshop_helpers.session import DemoSession

REPEAT = False
DISABLE_ANSWER_CACHE = True  # Explicit API-wide change; False refuses an enabled cache.


def demonstrate(session):
    """Save settings before mutation so a partial preparation remains recoverable.
    
    Example: demonstrate(session)
    """
    require(session.config.tenant_id == "acme", "Use tenant_id=acme for this lesson.")
    require(not session.state.get("lesson31_closed"), "This run was cleaned up. Use setup/start_new_session.py with LESSON='1.1'.")
    env = session.service_environment(session.config.api_service, ["VECTOR_INDEX_ENDPOINT", "VECTOR_DEPLOYED_INDEX_ID"])
    require(all(env.values()) and len(env) == 2, "The serving API has no deployed Vector Search endpoint. Complete the deployment before this lesson.")
    prepare_cache(session, disable=DISABLE_ANSWER_CACHE)
    session.pin_vector()
    # main.py caches tenant settings for 60 seconds in each API process.
    # Save a deadline rather than forcing every later question to sleep again.
    session.state["lesson31_pin_ready_after"] = time.time() + 65
    session.save()
    print("Prepared. Run demo_03_tenant_something_you_are_never_something_you_send.py next.")


def main():
    """Run only preparation; it is separate from the numbered HTML examples.
    
    Example: main()
    """
    with DemoSession(__file__, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
