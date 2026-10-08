# Lesson B.1 run list

None needed. The page has no `recorded()` output and no `data/` folder: every output on it comes from a cell the build
runs on the Basics interpreter (Python 3.12, numpy 2.5.3, google-genai 2.22.0), on 127.0.0.1 only, with no account, no
network beyond the laptop and no cost. The kit's side is read from `deploy/` at build time.

One value on the page follows the interpreter rather than the kit: the step 3 cell prints the google-auth version pip
chose for the Basics venv (`pip chose ...`), and the page says the learner's may be newer. Rebuilding with a Basics venv
installed on a later day can move that one number; nothing else changes.
