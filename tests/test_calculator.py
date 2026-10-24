import pytest

from loan_calc.calculator import (
    amortisation_schedule,
    compare_offers,
    eligible_amount,
    emi,
    format_inr,
    outstanding_after,
    prepayment_savings,
    remaining_tenure,
    schedule_to_csv,
    summary,
    total_interest,
    total_payment,
)


# TC-EMI-01
def test_emi_zero_rate_is_simple_division() -> None:
    # 90,000 / 3 = 30,000 exactly
    assert emi(90_000, 0, 3) == pytest.approx(30_000.00, abs=0.0)


# TC-SUM-01
def test_totals_zero_interest_principal_90000_tenure_3() -> None:
    assert emi(90_000, 0, 3) == pytest.approx(30_000.00, abs=0.0)
    assert total_payment(90_000, 0, 3) == pytest.approx(90_000.00, abs=0.0)
    assert total_interest(90_000, 0, 3) == pytest.approx(0.00, abs=0.0)


# TC-EMI-02
def test_emi_raises_for_non_positive_tenure() -> None:
    with pytest.raises(ValueError, match="tenure must be positive"):
        emi(100_000, 10, 0)


# TC-EMI-03
def test_emi_raises_for_non_positive_principal() -> None:
    with pytest.raises(ValueError, match="principal must be positive"):
        emi(0, 10, 12)


# Required: remove xfail, 10%/240 test must assert correct value (expected to fail with current rounding bug)
def test_emi_independent_calc_1m_10pct_240m() -> None:
    assert emi(1_000_000, 10, 240) == pytest.approx(9650.22, abs=1.0)


# Required: 9%/240 test
def test_emi_independent_calc_1m_9pct_240m() -> None:
    assert emi(1_000_000, 9, 240) == pytest.approx(8997.26, abs=1.0)


# Required: huge principal, 0%, 360 months
def test_emi_huge_principal_zero_rate_360m() -> None:
    assert emi(1_000_000_000_000, 0, 360) == pytest.approx(2777777777.78, abs=0.01)


# Required: 1-month tenure EMI and schedule
def test_one_month_tenure_emi_and_schedule_required() -> None:
    assert emi(10_000, 12, 1) == pytest.approx(10100.00, abs=0.0)
    rows = amortisation_schedule(10_000, 12, 1)
    assert len(rows) == 1
    assert rows[0]["month"] == 1
    assert rows[0]["balance"] == pytest.approx(0.0, abs=0.0)


# Required schedule behavior: 12-month loan must have 12 rows and end at 0 balance
def test_amortisation_schedule_length_is_exactly_tenure_and_ends_at_zero_balance() -> None:
    rows = amortisation_schedule(100_000, 10, 12)
    assert len(rows) == 12
    assert rows[-1]["month"] == 12
    assert rows[-1]["balance"] == pytest.approx(0.0, abs=0.0)


# TC-OUT-01
def test_outstanding_after_zero_or_negative_months_returns_principal() -> None:
    assert outstanding_after(100_000, 10, 12, 0) == pytest.approx(100_000.00, abs=0.0)
    assert outstanding_after(100_000, 10, 12, -3) == pytest.approx(100_000.00, abs=0.0)


# TC-OA-03 (also covers TC-OUT-02 intent)
def test_outstanding_after_more_than_tenure_months_is_zero() -> None:
    assert outstanding_after(100_000, 10, 12, 999) == pytest.approx(0.0, abs=0.0)


# Restore TC-RT-04 as proposed (note: this is intentionally likely to fail with current implementation)
def test_remaining_tenure_tc_rt_04() -> None:
    assert remaining_tenure(100_000, 12, 10_000) == 11


# TC-RT-05
def test_remaining_tenure_raises_when_instalment_too_small() -> None:
    with pytest.raises(ValueError, match="instalment too small to repay the loan"):
        remaining_tenure(balance=100_000, annual_rate=12, instalment=900)

# TC-INR-01
def test_format_inr_indian_grouping_and_decimals() -> None:
    assert format_inr(1234567.89) == "₹12,34,567.89"


# TC-INR-02
def test_format_inr_negative_amount() -> None:
    assert format_inr(-1234.5) == "-₹1,234.50"


# TC-AS-02
def test_outstanding_after_one_month_matches_first_row_balance() -> None:
    principal, rate, tenure = 200_000, 12.0, 12
    rows = amortisation_schedule(principal, rate, tenure)
    assert outstanding_after(principal, rate, tenure, 1) == pytest.approx(rows[0]["balance"], abs=0.0)


# TC-AS-03
def test_outstanding_after_exact_schedule_length_equals_last_row_balance() -> None:
    principal, rate, tenure = 200_000, 12.0, 12
    rows = amortisation_schedule(principal, rate, tenure)
    assert outstanding_after(principal, rate, tenure, len(rows)) == pytest.approx(rows[-1]["balance"], abs=0.0)


# Required: prepayment larger than the balance at prepayment month
def test_prepayment_larger_than_balance_at_prepayment_month_required() -> None:
    out = prepayment_savings(120_000, 0, 12, 1, 200_000)
    assert out["months_saved"] == 11
    assert out["new_tenure"] == 1
    assert out["interest_saved"] == pytest.approx(0.0, abs=0.0)


# TC-PS-02
def test_prepayment_savings_zero_rate_months_saved_is_remaining_months() -> None:
    out = prepayment_savings(120_000, 0, 12, 6, 10_000)
    assert out["months_saved"] == 1
    assert out["new_tenure"] == 11
    assert out["interest_saved"] == pytest.approx(0.0, abs=0.0)


# TC-PRE-01
def test_prepayment_savings_returns_expected_keys_and_types() -> None:
    out = prepayment_savings(
        principal=100_000,
        annual_rate=10,
        tenure_months=12,
        prepay_month=3,
        prepay_amount=10_000,
    )
    assert set(out.keys()) == {
        "emi",
        "months_saved",
        "new_tenure",
        "interest_saved",
        "interest_paid_before_prepayment",
    }
    assert isinstance(out["months_saved"], int)
    assert isinstance(out["new_tenure"], int)
    assert isinstance(out["emi"], float)
    assert isinstance(out["interest_saved"], float)


# TC-EA-01 + TC-EA-02 + TC-CO-01 (fees and order with exact values)
# TC-CO-01: no-fee 12% offer is cheaper than 10% + 2% fee over 12 months
def test_compare_offers_exact_fees_and_sorted_order() -> None:
    offers = [
        {"bank": "LowRateHighFee", "rate": 10.0, "tenure": 12, "processing_fee_pct": 2.0},
        {"bank": "HighRateNoFee", "rate": 12.0, "tenure": 12, "processing_fee_pct": 0.0},
    ]
    out = compare_offers(200_000, offers)

    assert [o["bank"] for o in out] == ["HighRateNoFee", "LowRateHighFee"]
    assert out[0]["processing_fee"] == pytest.approx(0.00)
    assert out[1]["processing_fee"] == pytest.approx(4000.00)
    assert out[0]["total_cost"] == pytest.approx(13_237.12, abs=0.01)
    assert out[1]["total_cost"] == pytest.approx(14_998.16, abs=0.01)


# TC-CSV-01
def test_schedule_to_csv_writes_header_and_rows(tmp_path) -> None:
    rows = amortisation_schedule(100_000, 10, 12)
    out_file = tmp_path / "schedule.csv"
    schedule_to_csv(rows, str(out_file))

    content = out_file.read_text()
    lines = content.strip().splitlines()

    assert lines[0] == "month,emi,interest,principal,balance"
    assert len(lines) == 1 + len(rows)


# TC-SUMMARY-01
def test_summary_contains_expected_fields_and_formats() -> None:
    out = summary(90_000, 0, 3, start=None)
    assert out["principal"] == "₹90,000.00"
    assert out["rate"] == "0% p.a."
    assert out["tenure"] == "3 months"
    assert out["emi"] == "₹30,000.00"
    assert out["total_interest"] == "₹0.00"
    assert out["total_payment"] == "₹90,000.00"
    assert out["currency"] == "INR"

# TC-AS-02 (real): 0% interest, 120,000 over 12 months
def test_schedule_zero_rate_pays_equal_principal_each_month() -> None:
    rows = amortisation_schedule(120_000, 0, 12)
    assert len(rows) == 12
    for row in rows:
        assert row["interest"] == pytest.approx(0.0)
        assert row["principal"] == pytest.approx(10_000.00)
    assert rows[-1]["balance"] == pytest.approx(0.0)


# TC-AS-03 (real): first row of 1,200 at 12% over 12 months, worked out by hand
def test_schedule_first_row_1200_at_12pct() -> None:
    first = amortisation_schedule(1_200, 12, 12)[0]
    assert first["emi"] == pytest.approx(106.62)
    assert first["interest"] == pytest.approx(12.00)
    assert first["principal"] == pytest.approx(94.62)
    assert first["balance"] == pytest.approx(1105.38)


# TC-EA-01: no spare income means no loan
def test_eligible_amount_zero_when_no_spare_income() -> None:
    assert eligible_amount(50_000, 30_000, 10, 12) == 0.0


# TC-EA-02: at 0%, eligible = spare EMI x months = 40,000 x 12
def test_eligible_amount_zero_rate() -> None:
    assert eligible_amount(100_000, 10_000, 0, 12) == pytest.approx(480_000.00)


# TC-EA-03: spare EMI 10,000 at 10% over 12 months (independent PV calc)
def test_eligible_amount_10pct() -> None:
    assert eligible_amount(40_000, 10_000, 10, 12) == pytest.approx(113_745.08, abs=1)