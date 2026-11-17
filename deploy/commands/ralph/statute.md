# The task: statutory_deadline, from the statute alone

shared/desk_calc.py holds the DocuMind Desk's calculators. In this workspace one of them, `statutory_deadline`, has
lost its body: it raises NotImplementedError. Write the body from the law below, the lines of the Code on Wages,
2019 that `desk_calc.RULES` cites for it (`wages_s17_2` and `wages_s17_3`), as the kit's corpus holds them. The law
is the only spec: where it leaves a choice open, make one, and expect the oracle to judge it. Change nothing outside
that function.

## The interface

- `statutory_deadline(event, last_working_day) -> dict`: `event` names what ended the employment;
  `last_working_day` is the person's last working day, a date or its ISO text YYYY-MM-DD.
- It returns `_result(...)`, as the other calculators in the file build it, with the due date as YYYY-MM-DD text
  and unit `date`, citing the rules `wages_s17_2` and `wages_s17_3`.
- An argument it cannot take is refused with `CalcError`, as the other calculators refuse theirs.

## When it is done

When the loop's oracle passes. Its verdict after each iteration is in oracle.md.

## The law
