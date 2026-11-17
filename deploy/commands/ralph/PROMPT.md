You are one iteration of a Ralph loop. You start fresh: what earlier iterations did is in the files here, not in
your memory.

1. Read spec.md (the task), fix_plan.md (the plan) and oracle.md (the oracle's verdict on the code as it stands).
   The oracle's checks are not in this workspace: you cannot read them or run them. Its verdict is all you get.
2. If oracle.md lists a failed check that no item in fix_plan.md covers, add one unticked item for it at the end.
3. Take the first unticked item, and only that one. Do it by changing statutory_deadline in shared/desk_calc.py.
   Change nothing else in that file, and no other file but fix_plan.md and GEMINI.md: the loop undoes any other
   change, and the iteration is spent.
4. Run the fast test, python3 shared/desk_calc.py --selftest, and read what it prints.
5. Tick the item ([x]). If you learned a command or a fact the next iteration needs, add one line under "Learned" in
   GEMINI.md.
6. If you believe the whole spec is met, end your answer with a line that says RALPH_DONE and nothing else. The loop
   believes the oracle, not you.

Use no network: everything you need is in this workspace. Do not use git, and install nothing.
