# loan-calc: Architecture

## What it is

loan-calc is a small Python module for retail loan maths. It calculates:

- the monthly instalment (EMI)
- the month-by-month repayment table (amortisation schedule)
- how much a lump-sum prepayment saves
- which of several bank offers is cheapest
- how much someone can borrow

All amounts are in Indian rupees (INR).

## Files

| File | Role |
|---|---|
| `loan_calc/calculator.py` | All the logic: 13 functions and one constant (`DEFAULT_CURRENCY = "INR"`). |
| `loan_calc/__init__.py` | One line: `from .calculator import *`. It re-exports every public name, so other code can write `from loan_calc import emi`. `_monthly_rate` is not exported, because `import *` skips names that start with `_`. |
| `cli.py` | The command-line entry point. It reads the principal, the annual rate (%) and the tenure (months), then prints `summary()` as JSON. `--schedule` also prints every schedule row. Giving both `--prepay-month` and `--prepay-amount` also prints `prepayment_savings()`. |
| `tests/` | `tests/test_calculator.py` | 29 pytest tests, added during this assignment (the starter had none). |

## Key ideas

- **EMI (Equated Monthly Instalment):** the same payment every month. Each payment has two parts: interest on the money still owed, and the rest, which pays down the balance. Early payments are mostly interest; later ones are mostly principal.
  - Formula: `EMI = P × r × (1+r)^n / ((1+r)^n − 1)`, where P = principal, r = monthly rate and n = number of months.
- **Monthly rate:** banks quote a yearly percentage, but interest is charged monthly. Monthly rate (as a decimal) = annual % ÷ 12 ÷ 100 = annual % ÷ 1200. For example, 9% p.a. gives 0.0075.
- **Amortisation schedule:** the table with one row per month, showing the interest, the principal repaid and the balance left.
- **Rounding:** money values are rounded to 2 decimal places (paise) at each step.

## How the pieces connect

```
cli.py
 ├─ summary ──────────────┬─ emi ── _monthly_rate
 │                        ├─ total_payment ── emi
 │                        ├─ total_interest ── total_payment
 │                        └─ format_inr
 ├─ amortisation_schedule ─┬─ _monthly_rate
 │                         └─ emi
 └─ prepayment_savings ───┬─ emi
                          ├─ amortisation_schedule
                          ├─ remaining_tenure ── _monthly_rate
                          └─ total_interest

Not used by the CLI:
 outstanding_after ── amortisation_schedule
 compare_offers ─────┬─ emi
                     └─ total_interest
 eligible_amount ──── _monthly_rate
 schedule_to_csv      (standalone)
```

`emi()` sits at the centre: almost everything depends on it. So a mistake in `emi()` or `_monthly_rate()` spreads to nearly every result.

## Functions

### Core maths

**`_monthly_rate(annual_rate)`**
Converts an annual % rate into a monthly decimal rate: `annual_rate / 1200`, at full precision. Rounding happens only on final money values, never on the rate. The leading underscore marks it as a private helper: it's used inside the module and isn't part of the public API.

**`emi(principal, annual_rate, tenure_months)`**
Returns the EMI, rounded to 2 dp.
- Raises `ValueError` if the tenure or the principal is 0 or less.
- At 0% interest, the formula would divide by zero, so it returns `principal / tenure_months` instead.
- Negative rates are not checked.

**`total_payment(principal, annual_rate, tenure_months)`**
EMI × number of months, rounded. It uses the rounded EMI, so it can differ by a few paise from adding up the schedule.

**`total_interest(principal, annual_rate, tenure_months)`**
`total_payment − principal`.

### Schedule

**`amortisation_schedule(principal, annual_rate, tenure_months)`**
Returns a list of dicts, one per month, with the keys `month` (starting at 1), `emi`, `interest`, `principal` and `balance`. Each month:
- interest = balance × monthly rate
- principal part = EMI − interest
- the balance goes down by the principal part

The last month pays off exactly what's left, so rounding leftovers are cleared and the final balance is 0.

**`outstanding_after(principal, annual_rate, tenure_months, months_paid)`**
The balance after `months_paid` instalments, read from the schedule.
- 0 or fewer months paid returns the original principal.
- More months than the schedule has returns `0.0`.

### Prepayment

**`remaining_tenure(balance, annual_rate, instalment)`**
How many months a fixed instalment takes to clear a balance, using `n = −log(1 − B·r / E) / log(1 + r)`, rounded up. (B = balance, r = rate, E = instalment.) The monthly rate comes from `_monthly_rate()`, the same as in the rest of the module.
- Returns 0 if there's no balance.
- At 0% interest, returns balance ÷ instalment, rounded up.
- Raises `ValueError` if the instalment doesn't even cover the interest, because then the loan would never shrink.

**`prepayment_savings(principal, annual_rate, tenure_months, prepay_month, prepay_amount)`**
The scenario: pay a lump sum after month `prepay_month`, keep the same EMI, and finish the loan earlier. Steps:
1. Look up the balance after `prepay_month` in the schedule.
2. Subtract the lump sum.
3. If anything is left, ask `remaining_tenure()` how many more months are needed.
4. Compare total interest with and without the prepayment.

It returns `emi`, `months_saved`, `new_tenure`, `interest_saved` and `interest_paid_before_prepayment`. It assumes every remaining month is a full EMI. If the prepayment is larger than the outstanding balance, it is capped at the balance, because you only pay what you owe.

### Other helpers

**`compare_offers(principal, offers)`**
`offers` is a list of dicts, each with `bank`, `rate`, `tenure` and an optional `processing_fee_pct`. For each offer it works out:
- the EMI
- the total interest
- the fee (the fee % of the principal)
- the total cost (interest + fee)

It returns the offers sorted cheapest first. A missing required key raises `KeyError`.

**`eligible_amount(monthly_income, existing_emis, annual_rate, tenure_months, foir=0.5)`**
The largest loan someone qualifies for. FOIR (Fixed Obligation to Income Ratio) is the share of income allowed to go on EMIs; the default is 50%.
- Spare EMI capacity = `income × foir − existing EMIs`. If that's 0 or less, it returns `0.0`.
- Otherwise it runs the EMI formula backwards to find the principal that capacity can support.

**`format_inr(amount)`**
Formats a number as rupees with Indian digit grouping: the last 3 digits, then groups of 2. So 1000000 becomes `₹10,00,000.00`. Negative numbers become `-₹...`.

**`schedule_to_csv(rows, path)`**
Writes schedule rows to a CSV file with the header `month,emi,interest,principal,balance`. It overwrites any existing file at `path`.

**`summary(principal, annual_rate, tenure_months, start=None)`**
Returns a display-ready dict of strings: `principal`, `rate`, `tenure`, `emi`, `total_interest`, `total_payment`, `last_emi` (as `YYYY-MM`) and `currency`. `start` defaults to today, and `last_emi` is `start` plus `tenure_months` months. The CLI prints this.

## Bugs found and fixed

| # | Bug | Effect | Fix | Commit |
|---|---|---|---|---|
| 1 | `_monthly_rate` rounded the rate to 4 dp | Wrong EMI for rates like 10% (₹9,623.73 instead of ₹9,650.22). Hidden at 9%, because 9/1200 = 0.0075 exactly | Return `annual_rate / 1200` | `0708f71` |
| 2 | `amortisation_schedule` looped `range(1, tenure_months)` | Last month missing (11 rows for 12 months; 0 rows for 1 month) | `range(1, tenure_months + 1)` | `e334ee1` (mislabelled, see the prompt log) |
| 3 | `remaining_tenure` used `annual_rate / 100` | Annual rate treated as monthly, so valid instalments were rejected as "too small" | Use `_monthly_rate()` | `cc490a5` |
| 4 (extra) | `prepayment_savings` counted an over-large prepayment in full | Negative "interest saved" | Cap the prepayment at the balance | `12f135a` | 5 (extra) | `cli.py` help text had a bare `%` | Crashes on Python 3.14 (argparse rejects it) | Escape it as `%%` | `xxxxxxx` |

## Tests

Run `python -m pytest --cov=loan_calc --cov-report=term-missing`. 29 tests, 100% line coverage. Expected numbers come from independent calculations (the standard EMI, present-value and remaining-tenure formulas, and hand arithmetic), not from running the code. Two tests (the CSV writer and the summary formatting) check structure and formatting rather than calculated values.

## Where the AI explanation was wrong

- aXet's in-progress answer said downstream functions "account for" the missing schedule month by using `len(sched)`. In fact, only `outstanding_after` uses `len(sched)`, and that only hides the problem. `prepayment_savings` indexes the schedule directly. (aXet's final summary dropped this claim.)
- aXet called issues 1 and 2 "implementation notes" or "inconsistencies" rather than likely bugs.
