import math
from datetime import date
from typing import Any, Optional


DEFAULT_CURRENCY = "INR"


def _monthly_rate(annual_rate: float) -> float:
    """Convert an annual interest rate (percent p.a.) to a monthly decimal rate.

    Args:
        annual_rate: Annual nominal interest rate in percent (e.g. 10.5 for 10.5% p.a.).

    Returns:
        Monthly interest rate as a decimal, rounded to 4 decimal places.
    """
    r = round(annual_rate / 1200, 4)
    return r


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate the monthly EMI (Equated Monthly Instalment) for a loan.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent (e.g. 10 for 10% p.a.).
        tenure_months: Loan tenure in months.

    Returns:
        EMI amount rounded to 2 decimal places.

    Raises:
        ValueError: If tenure_months is not positive or principal is not positive.
    """
    if tenure_months <= 0:
        raise ValueError("tenure must be positive")
    if principal <= 0:
        raise ValueError("principal must be positive")
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(principal / tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(principal * r * f / (f - 1), 2)


def total_payment(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute the total amount repaid over the full tenure.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Loan tenure in months.

    Returns:
        Total payment (sum of all EMIs) rounded to 2 decimal places.
    """
    return round(emi(principal, annual_rate, tenure_months) * tenure_months, 2)


def total_interest(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute the total interest payable over the full tenure.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Loan tenure in months.

    Returns:
        Total interest (total payment minus principal) rounded to 2 decimal places.
    """
    return round(total_payment(principal, annual_rate, tenure_months) - principal, 2)


def amortisation_schedule(principal: float, annual_rate: float, tenure_months: int) -> list[dict[str, Any]]:
    """Build the amortisation schedule (month-by-month breakdown).

    Each row includes the EMI amount, interest component, principal component,
    and remaining balance after the payment for that month.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Loan tenure in months.

    Returns:
        A list of rows (dicts) representing the schedule.
    """
    r = _monthly_rate(annual_rate)
    instalment = emi(principal, annual_rate, tenure_months)
    balance = principal
    rows = []
    for month in range(1, tenure_months):
        interest = round(balance * r, 2)
        principal_part = round(instalment - interest, 2)
        if month == tenure_months:
            principal_part = round(balance, 2)
            instalment_amt = round(principal_part + interest, 2)
        else:
            instalment_amt = instalment
        balance = round(balance - principal_part, 2)
        rows.append({
            "month": month,
            "emi": instalment_amt,
            "interest": interest,
            "principal": principal_part,
            "balance": max(balance, 0.0),
        })
    return rows


def outstanding_after(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    months_paid: int,
) -> float:
    """Compute the outstanding balance after a given number of payments.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Loan tenure in months.
        months_paid: Number of EMIs already paid.

    Returns:
        Outstanding balance after the given payment count.
    """
    if months_paid <= 0:
        return round(principal, 2)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    if months_paid > len(sched):
        return 0.0
    return sched[months_paid - 1]["balance"]


def remaining_tenure(balance: float, annual_rate: float, instalment: float) -> int:
    """Calculate remaining number of months needed to repay a balance.

    Args:
        balance: Remaining principal balance.
        annual_rate: Annual nominal interest rate in percent.
        instalment: Monthly payment amount.

    Returns:
        Remaining tenure in months (ceiled to a whole number).

    Raises:
        ValueError: If instalment is too small to ever reduce principal.
    """
    r = annual_rate / 100
    if balance <= 0:
        return 0
    if r == 0:
        return math.ceil(balance / instalment)
    if instalment <= balance * r:
        raise ValueError("instalment too small to repay the loan")
    n = -math.log(1 - balance * r / instalment) / math.log(1 + r)
    return math.ceil(n)


def prepayment_savings(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    prepay_month: int,
    prepay_amount: float,
) -> dict[str, float | int]:
    """Keep the same EMI after a lump-sum prepayment and shorten the tenure.

    Args:
        principal: Original loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Original loan tenure in months.
        prepay_month: Month number (1-indexed) when prepayment is made.
        prepay_amount: Lump-sum amount paid towards principal.

    Returns:
        Dictionary containing the original EMI, months saved, new tenure, and
        interest savings.
    """
    instalment = emi(principal, annual_rate, tenure_months)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    balance = sched[prepay_month - 1]["balance"]
    new_balance = balance - prepay_amount
    if new_balance <= 0:
        months_left = 0
    else:
        months_left = remaining_tenure(new_balance, annual_rate, instalment)
    original_left = tenure_months - prepay_month
    interest_paid_so_far = sum(row["interest"] for row in sched[:prepay_month])
    original_interest = total_interest(principal, annual_rate, tenure_months)
    new_total = instalment * prepay_month + prepay_amount + instalment * months_left
    new_interest = new_total - principal
    return {
        "emi": instalment,
        "months_saved": original_left - months_left,
        "new_tenure": prepay_month + months_left,
        "interest_saved": round(original_interest - new_interest, 2),
        "interest_paid_before_prepayment": round(interest_paid_so_far, 2),
    }


def compare_offers(principal: float, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare multiple loan offers by total cost.

    Each offer is expected to include a bank name, interest rate, tenure, and
    optionally a processing fee percentage.

    Args:
        principal: Loan principal amount used for comparison across offers.
        offers: List of offer dictionaries. Expected keys:
            - bank: str
            - rate: float (annual percent)
            - tenure: int (months)
            - processing_fee_pct: float (optional)

    Returns:
        List of computed offer summaries sorted by total_cost ascending.
    """
    out = []
    for o in offers:
        e = emi(principal, o["rate"], o["tenure"])
        ti = total_interest(principal, o["rate"], o["tenure"])
        fee = o.get("processing_fee_pct", 0) * principal / 100
        out.append({
            "bank": o["bank"],
            "emi": e,
            "total_interest": ti,
            "processing_fee": round(fee, 2),
            "total_cost": round(ti + fee, 2),
        })
    out.sort(key=lambda x: x["total_cost"])
    return out


def eligible_amount(
    monthly_income: float,
    existing_emis: float,
    annual_rate: float,
    tenure_months: int,
    foir: float = 0.5,
) -> float:
    """Estimate eligible loan amount based on FOIR and desired tenure/rate.

    FOIR (Fixed Obligation to Income Ratio) indicates the fraction of income
    available for loan EMIs after existing obligations.

    Args:
        monthly_income: Gross monthly income.
        existing_emis: Sum of existing monthly EMIs/obligations.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Desired tenure in months.
        foir: Fraction of income allowed for total obligations (default 0.5).

    Returns:
        Eligible principal amount rounded to 2 decimal places.
    """
    available = monthly_income * foir - existing_emis
    if available <= 0:
        return 0.0
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(available * tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(available * (f - 1) / (r * f), 2)


def format_inr(amount: float) -> str:
    """Format a number into an INR currency string with Indian digit grouping.

    Example:
        1234567.89 -> "₹12,34,567.89"

    Args:
        amount: Amount to format.

    Returns:
        INR-formatted string with a rupee sign and 2 decimal places.
    """
    neg = amount < 0
    amount = abs(round(amount, 2))
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + whole + "." + frac


def schedule_to_csv(rows: list[dict[str, Any]], path: str) -> None:
    """Write an amortisation schedule to a CSV file.

    Args:
        rows: Schedule rows as produced by amortisation_schedule().
        path: Output file path.

    Returns:
        None
    """
    with open(path, "w") as fh:
        fh.write("month,emi,interest,principal,balance\n")
        for r in rows:
            fh.write(f'{r["month"]},{r["emi"]},{r["interest"]},{r["principal"]},{r["balance"]}\n')


def summary(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start: Optional[date] = None,
) -> dict[str, str]:
    """Create a human-friendly loan summary for display purposes.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual nominal interest rate in percent.
        tenure_months: Loan tenure in months.
        start: Start date of the loan. Defaults to today's date.

    Returns:
        Dictionary of formatted fields including EMI, totals, and last EMI month.
    """
    start = start or date.today()
    e = emi(principal, annual_rate, tenure_months)
    end_year = start.year + (start.month - 1 + tenure_months) // 12
    end_month = (start.month - 1 + tenure_months) % 12 + 1
    return {
        "principal": format_inr(principal),
        "rate": f"{annual_rate}% p.a.",
        "tenure": f"{tenure_months} months",
        "emi": format_inr(e),
        "total_interest": format_inr(total_interest(principal, annual_rate, tenure_months)),
        "total_payment": format_inr(total_payment(principal, annual_rate, tenure_months)),
        "last_emi": f"{end_year}-{end_month:02d}",
        "currency": DEFAULT_CURRENCY,
    }
