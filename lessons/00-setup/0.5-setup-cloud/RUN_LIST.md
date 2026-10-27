# Lesson 0.5: the live run the page still needs

The page has no recorded `output` windows: every block ends in a checkpoint the learner reads (a PASS line, a count, a
yaml), and the kit facts it states (the seven services, the roster plan, what `make up` runs after the apply, the
standing cost) are quoted or computed from the kit at build time. What a build cannot prove is that the three phases
run green end to end on the kit of 14 October 2026, so one run is still wanted.

**One run, from a blank project** (before the cohort's first session on 7 November 2026): a project with billing
linked, and nothing of the kit's yet. Cloud Shell, as the page says, in `tmux`.

**What to record** (paste into this folder as `data/run-2026-10.md`, then this file is updated; placeholders as in
lesson 0.3's run list: the project id becomes `documind-ai-YOUR-ID`, the number `NUMBER`, your mailbox `you@example.com`):

1. S6's last three lines: the `PASS: up to date with origin/main` line, the commit, and the file count. The page says
   1,630 files (the kit of 14 October 2026); if the repository the clone block names carries another kit, the page's
   count is wrong and the clone block's repository must be updated first.
2. T6's `Plan: N to add, 0 to change, 0 to destroy.` line, with N.
3. T7's confirm block: `exit code: 0`.
4. T8's index, endpoint and deployed id lines.
5. The build gate's two `OK` lines (12 and 8 tests) and the `PASS: shared sparse encoder available: blake2b-tf-v1` line.
6. F3's image list: seven names, one short tag.
7. The tenants step's roster lines for one tenant, and the read-back.
8. The closing targets' four results: `>> indexes READY`, `>> managed stores ready ...`, the view statements' results,
   the `vectorsCount` yaml.
9. The verify step's seven `OK` lines.
10. One cited answer in the UI (a sentence, not a screenshot), and the refusal of an account that is not on
    `ADMIN_EMAILS`.

**Anything that STOPs** is the finding: the block, the STOP line, and what the console showed. The pin block and the
chat deploy (F6, IAP on after the deploy) are the two blocks that changed most for this kit.
