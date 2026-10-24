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

## Entry 3
- **Step:** Propose test cases
- **Context given:** `@loan_calc/calculator.py`
- **Prompt (exact):**
  > @loan_calc/calculator.py Propose pytest test cases for every public function in calculator.py. Include these edge cases: 0% interest, 1-month tenure, very large principal, and a prepayment larger than the outstanding balance. Also include: EMI for 1,000,000 at 9% over 240 months should be 8997.26 (±1). For each test, give the expected value and explain how you worked it out independently of the current code. Don't just copy what the code returns. List the test cases first; don't write the test file yet.
- **aXet's answer (short summary):** Proposed about 35 test cases across all 12 public functions, including the 4 required edge cases and the 9% benchmark, each with a worked explanation.
- **Was it right?** Partly. Three problems:
  1. **Wrong expected value (TC-SUM-01):** for ₹1,00,000 at 0% over 3 months it expected total payment ₹1,00,000.00 and interest ₹0.00. But the EMI is rounded to ₹33,333.33, and 33,333.33 × 3 = ₹99,999.99 (so interest = −₹0.01).
  2. **No concrete numbers** for TC-RT-04, TC-PS-03 and TC-EA-03 ("≈", or "compute in the test"). A test that recomputes the formula can copy the bug.
  3. **Weak rate choice:** every EMI test used 0%, 9% or 12%. No "messy" real-world rate.
- **What I did about it:** Changed TC-SUM-01 to ₹90,000 (divides evenly). Required fixed expected numbers (TC-RT-04 = 11 months). Added a 10% EMI test with an expected ₹9,650.22, from an independent calculation using the standard EMI formula (as Excel's PMT does).

## Entry 4
- **Step:** Write the test file
- **Context given:** `@loan_calc/calculator.py`
- **Prompt (exact):**
  > @loan_calc/calculator.py Write the test cases you proposed into tests/test_calculator.py using pytest, with these changes:
  
  TC-SUM-01: use principal 90,000 (not 100,000), so the expected EMI is ₹30,000.00, the total payment ₹90,000.00 and the total interest ₹0.00. Your original expected values were wrong, because 33,333.33 × 3 = 99,999.99.
  
  Give every test a fixed expected number. No “≈” without a value, and don’t recompute the formula inside the test. TC-RT-04 should expect 11.
  
  Add a test: emi(1_000_000, 10, 240) should be 9650.22 (±1). I got this from an independent calculation.
  
  Use pytest.approx for float comparisons, and tmp_path for the CSV test.
  
  Do NOT change calculator.py.
- **aXet's answer (short summary):** Wrote 17 tests, ran them by itself, and got 1 failure: the 10% EMI was 9623.73 instead of 9650.22, which it traced to `_monthly_rate` rounding to 4 dp. It then marked that test `xfail` so the suite showed "16 passed".
- **Was it right?** No. The diagnosis was right, but:
  - marking the failing test xfail hid a real bug
  - some tests locked in buggy behaviour (a 12-month schedule expecting 11 rows; a test asserting the 4 dp rounding)
  - it swapped TC-RT-04 to 0%, which avoids the path being tested
  - it left out the required 9% benchmark, 1-month, huge-principal and prepayment-over-balance tests
- **What I did about it:** Rejected the file as it was. Sent a correction prompt (Entry 5) telling it to test correct behaviour, with no xfail and no changes to calculator.py.