# {{YOUR COMPANY}} on DocuMind: the failure modes

<!--
The capstone's component 7 (lesson 11.8). Copy this file to your fork's root as FAILURE-MODES.md, replace every
placeholder in double curly braces, braces included, and delete these comments.

make capstone-check counts an entry as a section under its own second-level heading that holds a Symptom: line and a
command in backticks your fork can run, four entries or more. It resolves each command and never runs it: a make
target your Makefile or mk/*.mk defines, or a script your fork holds, started with python, bash, sh or ./. Of lesson
11.7's registry, ops/gotchas.json, make gotcha-drill with an ID= that has an offline drill reproduces a gotcha, and
with LIVE=1 one that has a live drill; make gotchas and make gotcha-detect show and detect a gotcha, and prove
nothing. The four commands below are the four shapes that resolve: keep the one that fits each failure. The defence
reads the Caught by: lines, on dimension 2: which failures your monitoring would catch, which it would not, and what
you did about the second group. commands/tests/capstone_fork/FAILURE-MODES.md is one filled in, for a made-up company.
-->

{{One line: what the four failures have in common, and how each was reproduced.}}

## {{FAILURE 1}}

Symptom: {{What a user or an alert sees.}}
Command: `make gotcha-drill ID={{GOTCHA-ID}}`
Caught by: {{The policy that pages, or no policy and what you did about it.}}

## {{FAILURE 2}}

Symptom: {{What a user or an alert sees.}}
Command: `make gotcha-drill ID={{GOTCHA-ID}} LIVE=1`
Caught by: {{The policy that pages, or no policy and what you did about it.}}

## {{FAILURE 3}}

Symptom: {{What a user or an alert sees.}}
Command: `make {{TARGET}}`
Caught by: {{The policy that pages, or no policy and what you did about it.}}

## {{FAILURE 4}}

Symptom: {{What a user or an alert sees.}}
Command: `bash commands/{{SCRIPT}}.sh`
Caught by: {{The policy that pages, or no policy and what you did about it.}}
