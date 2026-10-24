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

