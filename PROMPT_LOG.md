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

## Entry 5
- **Step:** Correct the test file
- **Context given:** `@tests/test_calculator.py`, `@loan_calc/calculator.py`
- **Prompt (exact):**
  > @/tests/test_calculator.py @/loan_calc/calculator.py 
Fix this test file. Tests must check CORRECT loan behaviour, not copy what the current code does. It’s expected that some tests will FAIL; that’s how I find the bugs. Do not use xfail or skip, do not run the tests, and do NOT change calculator.py.

Remove the xfail from the 10% EMI test.
Delete test_monthly_rate_rounding_to_4_decimals.
Schedule length: a 12-month loan must have 12 rows, and the last row’s balance must be 0.
Restore TC-RT-04 as proposed: remaining_tenure(100_000, 12, 10_000) == 11.
Add the required tests: emi(1_000_000, 9, 240) ≈ 8997.26 (±1); 1-month tenure: emi(10_000, 12, 1) == 10100.00, and its schedule has exactly 1 row with balance 0; huge principal: emi(1_000_000_000_000, 0, 360) ≈ 2777777777.78; prepayment larger than the balance: prepayment_savings(120_000, 0, 12, 1, 200_000) gives months_saved 11, new_tenure 1, interest_saved 0.0.
Add your other proposed tests with fixed values: TC-AS-02, TC-AS-03, TC-OA-03, TC-PS-02, TC-EA-01, TC-EA-02, and TC-CO-01 with exact fees and order.
- **aXet's answer (short summary):** Removed the xfail, fixed the schedule-length test (12 rows), restored TC-RT-04, and added the required 9%, 1-month, huge-principal and prepayment-over-balance tests.
- **Was it right?** Partly. Two tests labelled "TC-AS-02" and "TC-AS-03" weren't the proposed tests: they only compared `outstanding_after` against `amortisation_schedule` (code checking code, with no independent numbers). A comment said "TC-EA-01 + TC-EA-02", but `eligible_amount` wasn't tested or even imported.
- **What I did about it:** Wrote 5 tests by hand: the real TC-AS-02 and TC-AS-03, plus 3 `eligible_amount` tests with independently calculated values. Result: 28 tests, 8 failing.

## Entry 6
- **Step:** Diagnose failing tests: bug #1 (monthly rate rounding)
- **Context given:** `@loan_calc/calculator.py`, `@tests/test_calculator.py`
- **Prompt (exact):**
  > @loan_calc/calculator.py @tests/test_calculator.py These two tests fail: test_emi_independent_calc_1m_10pct_240m (gets 9623.73, expected 9650.22) and test_eligible_amount_10pct. Explain the root cause and propose the smallest fix to calculator.py. Show me the change, but don't apply it yet. Don't change the tests.
- **aXet's answer (short summary):** Both failures come from `_monthly_rate()` doing `round(annual_rate / 1200, 4)`. At 10%, 0.008333… becomes 0.0083, and over 240 months that lowers the EMI to 9623.73. `eligible_amount()` uses the same helper, so it's wrong too. Fix: `return annual_rate / 1200` and keep rounding only on final money values.
- **Was it right?** Yes, the diagnosis and fix are correct. One small slip: it called it "truncation", but it's rounding (for example, 8.5% gives 0.0070833…, which rounds *up* to 0.0071). Worth noting why the assignment's 9% benchmark never caught this: 9/1200 = 0.0075 exactly, so rounding to 4 dp changes nothing. The same goes for 12% and 0%.
- **What I did about it:** Applied the fix by hand (one function plus its docstring). Re-ran the tests: the two 10% tests now pass. Committed the fix on its own as bug fix #1.

## Entry 7
- **Step:** Diagnose failing tests: bug #2 (schedule off-by-one)
- **Context given:** `@loan_calc/calculator.py`, `@tests/test_calculator.py`
- **Prompt (exact):**
  > @loan_calc/calculator.py @tests/test_calculator.py These 3 tests fail: test_one_month_tenure_emi_and_schedule_required (0 rows instead of 1), test_amortisation_schedule_length_is_exactly_tenure_and_ends_at_zero_balance (11 rows instead of 12), and test_schedule_zero_rate_pays_equal_principal_each_month. Explain the root cause and propose the smallest fix to calculator.py. Show me the change, but don't apply it yet. Don't change the tests.
- **aXet's answer (short summary):** `range(1, tenure_months)` stops one short, so a 1-month loan gets 0 rows and a 12-month loan gets 11. It also means the "last month" block never runs. Fix: `range(1, tenure_months + 1)`.
- **Was it right?** Yes. A one-line fix that explains all 3 failures. Its Entry 1 explanation had already spotted this loop, but called it an "inconsistency", and the first test file even locked it in (expecting 11 rows).
- **What I did about it:** Applied the one-line fix. 3 schedule tests now pass (3 failed, 25 passed). Committed it on its own as bug fix #2.

## Entry 8
- **Step:** Diagnose failing tests: bug #3 (remaining_tenure rate)
- **Context given:** `@loan_calc/calculator.py`, `@tests/test_calculator.py`
- **Prompt (exact):**
  > @loan_calc/calculator.py @tests/test_calculator.py test_remaining_tenure_tc_rt_04 fails: remaining_tenure(100_000, 12, 10_000) raises "instalment too small to repay the loan", but the monthly interest is only 1,000. Expected 11 months. Explain the root cause and propose the smallest fix to calculator.py. Show me the change, but don't apply it yet. Don't change the tests.
- **aXet's answer (short summary):** `remaining_tenure` uses `r = annual_rate / 100`, so 12% p.a. is treated as 12% per month. The guard then sees ₹12,000 of "monthly interest" and wrongly raises. Fix: `r = _monthly_rate(annual_rate)`.
- **Was it right?** Yes. Reusing `_monthly_rate()` keeps the rate conversion in one place. This only works properly because bug #1 was fixed first; otherwise it would inherit the 4 dp rounding.
- **What I did about it:** Applied the one-line fix. TC-RT-04 now passes. Committed it on its own as bug fix #3.

## Entry 9
- **Step:** A test that was wrong (found after fixing bug #3)
- **Context given:** None (found by reviewing the test after the fix)
- **Prompt (exact):**
  > (none: found by reviewing the test myself)
- **aXet's answer (short summary):** In Entry 5's test file, aXet wrote `remaining_tenure(100_000, 10, 9_000)` and expected "instalment too small".
- **Was it right?** No. At 10% p.a., monthly interest on ₹1,00,000 is ₹833.33, so ₹9,000 is plenty. The test only passed because of bug #3 (10% was read as 10% per month = ₹10,000). Once the bug was fixed, the test failed. This is the case where the test is wrong, not the code. aXet had also changed it from its own original proposal (TC-RT-03: 12%, ₹900).
- **What I did about it:** Changed the test back to 12% with a ₹900 instalment (monthly interest ₹1,000, so ₹900 really is too small). Committed it separately from the code fix.



## Note on commit history
Commit `e334ee1` is labelled "Fix: remaining_tenure used annual rate as monthly rate", but it actually contains **bug fix #2** (amortisation schedule `range(1, tenure_months + 1)`). I used the wrong commit message by mistake. The real remaining_tenure fix (bug #3) is the next commit. Each bug is still in its own commit. I didn't rewrite history because it was already pushed.