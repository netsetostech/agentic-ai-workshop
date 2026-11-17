# The task: statutory_deadline, written to its spec

shared/desk_calc.py holds the DocuMind Desk's calculators. In this workspace one of them, `statutory_deadline`, has
lost its body: it raises NotImplementedError. Write the body. Change nothing outside that function.

## What it works out

The Code on Wages, 2019, section 17(2): when an employee is removed, dismissed or retrenched, or resigns, the wages
due are paid within two working days. The desk reads it this way:

- The two working days are counted from the person's last working day: the first of them is the next working day
  after it, and the date returned is the second.
- A working day is a Monday to Friday. No holiday calendar is loaded, so the count skips Saturdays and Sundays only;
  `cases.working_days_after()` counts that way, as the case queue's exit clock does.
- The events the two days count from are `EXIT_EVENTS`: removal, dismissal, retrenchment and resignation. Section
  17(2) also names the closure of the establishment, but it counts the two days from those four events alone: any
  other event, closure included, is refused.

## Its arguments, and what it refuses

`statutory_deadline(event, last_working_day) -> dict`

- `event`: one of `EXIT_EVENTS`, in any case and with spaces around it (" Resignation " is resignation). Anything
  else is refused with `CalcError`, whose message names the four events.
- `last_working_day`: a date, or its ISO text YYYY-MM-DD; `day_of()` reads both, and refuses anything else with
  `CalcError`.
- Never let Python's own ValueError or TypeError out: the Desk's tool turns a `CalcError` into an error result the
  model reads (services/chat/desk_agent.py, `_calc()`), and anything else fails the person's turn.

## What it returns

`_result(...)`, as the other calculators in the file build it:

- calculator `statutory_deadline`; value the due date as YYYY-MM-DD text; unit `date`; not an estimate;
- rules `wages_s17_2` and `wages_s17_3`, so the result cites s.17(2) and s.17(3) of the Code on Wages, 2019;
- formula: the last working day with its weekday, the event, plus `WAGE_DAYS` working days, and the due date with
  its weekday;
- notes, three of them: `NO_HOLIDAYS`; that the days are counted from the last working day, the desk's reading of
  s.17(2), as its case queue counts them; and that the appropriate Government may set another time limit (s.17(3)).

## When it is done

When the loop's oracle passes. Its verdict after each iteration is in oracle.md.
