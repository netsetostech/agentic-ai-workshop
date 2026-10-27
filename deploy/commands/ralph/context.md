# This workspace

A copy of a few files of the DocuMind kit, for one task: spec.md says which. The kit's rules for a calculator in
shared/desk_calc.py:

- a figure is worked out in code, and the result names the section its rule comes from (`_result`, `basis`, `cites`);
- a result says what it assumes, in its notes;
- an argument a calculator cannot take raises `CalcError`, never Python's own ValueError or TypeError: the Desk's tool
  turns a `CalcError` into an error result the model reads, and anything else fails the person's turn.

The fast test: `python3 shared/desk_calc.py --selftest` prints an ok or FAIL line a check, then a summary line.

## Learned

