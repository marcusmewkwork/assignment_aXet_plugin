# Prompt Log: Assignment P1 (aXet Plugin)

Each entry records the exact prompt I typed, what aXet said, and whether it was right.

## Entry 1
- **Step:** Explain the code
- **Context given:** None attached by me. aXet asked to read `loan_calc/calculator.py` and read it itself.
- **Prompt (exact):**
  > Explain what each function in calculator.py does, what its inputs and outputs are, and how the functions depend on each other.
- **aXet's answer (short summary):** Described all 13 functions (purpose, inputs, outputs) and drew a call graph. Flagged two suspicious spots: the loop in `amortisation_schedule` is `range(1, tenure_months)`, so the last month is never produced; and `remaining_tenure` uses `annual_rate / 100` instead of a monthly rate.
- **Was it right?** Partly. The function descriptions and call graph match the code. But it said "downstream functions account for this by using len(sched)". That's wrong: only `outstanding_after` uses `len(sched)`, and that doesn't fix the missing month, it just hides it. `prepayment_savings` indexes the schedule directly. It also called these "inconsistencies worth noting" rather than likely bugs.
- **What I did about it:** Didn't accept the "downstream accounts for it" claim. Noted the two suspicious spots as bug candidates, to confirm with tests before fixing anything.
- **Follow-up prompt (exact):**
  > continue
- **Follow-up result:** aXet finished its 4-step plan and gave a cleaner final summary. The final version no longer contains the wrong "len(sched)" claim, but the intermediate answer did. So it's worth reading the in-progress output too, not just the final summary.

## Entry 2
- **Step:** Docstrings and type hints
- **Context given:** `@loan_calc/calculator.py`
- **Prompt (exact):**
  > Add Google-style docstrings and type hints to every public function in calculator.py. Do NOT change any logic, formulas, rounding or loop ranges. Only add docstrings and type annotations. If you think something is a bug, tell me in chat instead of changing it.
- **aXet's answer (short summary):** Added docstrings and type hints to all functions. Flagged one suspected bug: `amortisation_schedule` loops `range(1, tenure_months)`, so the final month is missing.
- **Was it right?** Mostly. I checked `git diff`, and no logic was changed. But it didn't mention the `remaining_tenure` `annual_rate / 100` issue it had flagged in Entry 1, so its bug-spotting isn't consistent. The `total_payment` docstring said "sum of all EMIs", but the code does EMI × months.
- **What I did about it:** Accepted the changes after reviewing the diff. Fixed the `total_payment` docstring wording by hand. Still treating both suspected bugs as unconfirmed until tests show them.