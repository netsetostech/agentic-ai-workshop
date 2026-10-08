"""Restore a lesson through its section files, retaining progress and failures.

Example: setup/finish.py calls finish_lesson(session); each cleanup section is
attempted even if another fails, and already completed sections are skipped.
"""
import importlib.util


def finish_lesson(session):
    """Run all mapped restorations once and close the run only when all succeed.

    Args: session is the active DemoSession opened by setup/finish.py.
    Returns: None. A failed restoration raises after the others are attempted.
    Example: a failed candidate removal still allows the saved backend restore.
    """
    original = session.step
    errors = []
    try:
        for record in session.mapping['demos']:
            if record['category'] != 'cleanup' or record.get('orchestrator'):
                continue
            if record['id'] in session.state['completed'] and not session.repeat:
                print('Already restored:', record['file'])
                continue
            path = session.lesson_dir / record['file']
            spec = importlib.util.spec_from_file_location('_workshop_cleanup_' + record['id'], path)
            module = importlib.util.module_from_spec(spec)
            session.step = record
            try:
                spec.loader.exec_module(module)
                module.demonstrate(session)
            except (Exception, SystemExit) as error:
                errors.append(f"{record['file']}: {error}")
                print('Restoration failed; continuing:', errors[-1])
            else:
                if record['id'] not in session.state['completed']:
                    session.state['completed'].append(record['id'])
            finally:
                session.save()
    finally:
        session.step = original
    if errors:
        raise RuntimeError('Cleanup incomplete:\n' + '\n'.join(errors))
    session.state['lifecycle_complete'] = True
    session.save()
