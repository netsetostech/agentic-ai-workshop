#!/bin/sh
# One iteration of the Ralph loop (workshop lesson 10.10), run inside the ralph image as ralph-iteration: Gemini CLI
# headless on the loop's prompt, in the workspace commands/ralph.py mounts at /work. A fresh process each iteration, so
# a fresh context: what it knows of earlier iterations is in the workspace's files. The prompt is mounted read-only
# from outside the workspace, so the agent cannot rewrite the next iteration's.
#   --prompt          headless: one prompt, then exit (the flags are the batch-1 probe's for the pinned version)
#   --yolo            every tool call approved without asking: the container, not a person, is the boundary
#   --output-format   json: one object with the response and the token stats the loop prices
set -eu
cd /work
exec gemini --model "${RALPH_MODEL:?the loop sets RALPH_MODEL}" --yolo --output-format json --prompt "$(cat /ralph/PROMPT.md)"
