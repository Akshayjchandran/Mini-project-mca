"""
ITR Learn & Simulate
Centralized Tax Rule Configuration

Educational simulation only.
Tax rules must be verified against the latest official sources.
"""


# ============================================================
# FINANCIAL YEAR / TAX YEAR CONFIGURATION
# ============================================================

TAX_RULES = {

    # --------------------------------------------------------
    # FY 2025-26 / AY 2026-27
    # Governed by Income-tax Act, 1961
    # --------------------------------------------------------

    "FY2025-26": {

        "financial_year": "FY 2025-26",
        "assessment_year": "AY 2026-27",
        "law": "Income-tax Act, 1961",
        "regime_default": "new",

        "new_regime": {

            "slabs": [
                {
                    "from": 0,
                    "to": 400000,
                    "rate": 0.00
                },
                {
                    "from": 400000,
                    "to": 800000,
                    "rate": 0.05
                },
                {
                    "from": 800000,
                    "to": 1200000,
                    "rate": 0.10
                },
                {
                    "from": 1200000,
                    "to": 1600000,
                    "rate": 0.15
                },
                {
                    "from": 1600000,
                    "to": 2000000,
                    "rate": 0.20
                },
                {
                    "from": 2000000,
                    "to": 2400000,
                    "rate": 0.25
                },
                {
                    "from": 2400000,
                    "to": None,
                    "rate": 0.30
                }
            ],

            "rebate_87a": {
                "maximum": 60000,
                "income_limit": 1200000,
                "resident_only": True
            },

            "standard_deduction": 75000
        },


        "old_regime": {

            "general": [
                {
                    "from": 0,
                    "to": 250000,
                    "rate": 0.00
                },
                {
                    "from": 250000,
                    "to": 500000,
                    "rate": 0.05
                },
                {
                    "from": 500000,
                    "to": 1000000,
                    "rate": 0.20
                },
                {
                    "from": 1000000,
                    "to": None,
                    "rate": 0.30
                }
            ],

            "senior_citizen": [
                {
                    "from": 0,
                    "to": 300000,
                    "rate": 0.00
                },
                {
                    "from": 300000,
                    "to": 500000,
                    "rate": 0.05
                },
                {
                    "from": 500000,
                    "to": 1000000,
                    "rate": 0.20
                },
                {
                    "from": 1000000,
                    "to": None,
                    "rate": 0.30
                }
            ],

            "super_senior_citizen": [
                {
                    "from": 0,
                    "to": 500000,
                    "rate": 0.00
                },
                {
                    "from": 500000,
                    "to": 1000000,
                    "rate": 0.20
                },
                {
                    "from": 1000000,
                    "to": None,
                    "rate": 0.30
                }
            ],

            "rebate_87a": {
                "maximum": 12500,
                "income_limit": 500000,
                "resident_only": True
            },

            "standard_deduction": 50000
        },

        "cess": 0.04,

        "surcharge": {
            "5000000": 0.10,
            "10000000": 0.15,
            "20000000": 0.25,
            "50000000": 0.37
        }

    },


    # --------------------------------------------------------
    # FY 2026-27 / Tax Year 2026-27
    # Governed by Income Tax Act, 2025
    # --------------------------------------------------------

    "FY2026-27": {

        "financial_year": "FY 2026-27",
        "tax_year": "Tax Year 2026-27",
        "law": "Income Tax Act, 2025",

        "regime_default": "new",

        "note": (
            "From 1 April 2026, the Income Tax Act, 2025 "
            "applies to tax years beginning on or after "
            "1 April 2026."
        ),

        "new_regime": {

            "slabs": [
                {
                    "from": 0,
                    "to": 400000,
                    "rate": 0.00
                },
                {
                    "from": 400000,
                    "to": 800000,
                    "rate": 0.05
                },
                {
                    "from": 800000,
                    "to": 1200000,
                    "rate": 0.10
                },
                {
                    "from": 1200000,
                    "to": 1600000,
                    "rate": 0.15
                },
                {
                    "from": 1600000,
                    "to": 2000000,
                    "rate": 0.20
                },
                {
                    "from": 2000000,
                    "to": 2400000,
                    "rate": 0.25
                },
                {
                    "from": 2400000,
                    "to": None,
                    "rate": 0.30
                }
            ],

            "rebate": {
                "section": "87A equivalent under new framework",
                "maximum": 60000,
                "income_limit": 1200000,
                "resident_only": True
            }
        },

        "old_regime": {

            "note": (
                "For FY 2026-27, the old/concessional choice "
                "must be implemented according to the "
                "Income Tax Act, 2025 and applicable rules."
            )
        },

        "cess": 0.04
    }
}


# Add convenient aliases for financial and assessment years
TAX_RULES["2025-26"] = TAX_RULES["FY2025-26"]
TAX_RULES["FY 2025-26"] = TAX_RULES["FY2025-26"]
TAX_RULES["AY 2026-27"] = TAX_RULES["FY2025-26"]
TAX_RULES["AY2026-27"] = TAX_RULES["FY2025-26"]

if "FY2026-27" in TAX_RULES:
    TAX_RULES["2026-27"] = TAX_RULES["FY2026-27"]
    TAX_RULES["FY 2026-27"] = TAX_RULES["FY2026-27"]
    TAX_RULES["AY 2027-28"] = TAX_RULES["FY2026-27"]
    TAX_RULES["AY2027-28"] = TAX_RULES["FY2026-27"]


# ============================================================
# AVAILABLE FINANCIAL YEARS
# ============================================================

def get_available_years():
    """
    Return all financial years supported by the application.
    """

    return ["FY 2025-26", "FY 2026-27"]


# ============================================================
# GET RULES
# ============================================================

def get_tax_rules(financial_year):
    """
    Return the tax-rule configuration for a financial year.
    """
    if not financial_year:
        return TAX_RULES["FY2025-26"]

    if financial_year in TAX_RULES:
        return TAX_RULES[financial_year]

    clean_yr = str(financial_year).strip().replace(" ", "").upper()
    if clean_yr in TAX_RULES:
        return TAX_RULES[clean_yr]

    if "2025-26" in str(financial_year) or ("2026-27" in str(financial_year) and "AY" in str(financial_year).upper()):
        return TAX_RULES["FY2025-26"]

    if "2026-27" in str(financial_year):
        return TAX_RULES.get("FY2026-27", TAX_RULES["FY2025-26"])

    return TAX_RULES["FY2025-26"]

# ============================================================
# BASIC TAX CALCULATION
# ============================================================

def calculate_tax_from_slabs(taxable_income, slabs):
    """
    Calculate tax using progressive tax slabs.
    """

    if taxable_income <= 0:
        return 0

    total_tax = 0

    for slab in slabs:

        slab_from = slab["from"]
        slab_to = slab["to"]
        rate = slab["rate"]

        if taxable_income <= slab_from:
            continue

        if slab_to is None:
            taxable_amount = taxable_income - slab_from
        else:
            taxable_amount = min(
                taxable_income,
                slab_to
            ) - slab_from

        if taxable_amount > 0:
            total_tax += taxable_amount * rate

    return round(total_tax)


# ============================================================
# SELECT SLABS
# ============================================================

def get_slabs(financial_year, regime="new", age=0):
    """
    Select the appropriate tax slabs.
    """

    rules = get_tax_rules(financial_year)

    if regime == "new":
        return rules["new_regime"]["slabs"]

    if regime == "old":

        old_rules = rules["old_regime"]

        if age >= 80 and "super_senior_citizen" in old_rules:
            return old_rules["super_senior_citizen"]

        if age >= 60 and "senior_citizen" in old_rules:
            return old_rules["senior_citizen"]

        return old_rules["general"]

    raise ValueError("Invalid tax regime.")


# ============================================================
# CALCULATE BASIC TAX
# ============================================================

def calculate_surcharge(taxable_income, tax_after_rebate, regime="new"):
    """
    Calculate surcharge and statutory marginal relief on surcharge.
    Rates for Individuals / HUF:
    - Income > 50L and <= 1 Cr: 10%
    - Income > 1 Cr and <= 2 Cr: 15%
    - Income > 2 Cr and <= 5 Cr: 25%
    - Income > 5 Cr: 25% (New Regime) / 37% (Old Regime)
    """
    if taxable_income <= 5000000 or tax_after_rebate <= 0:
        return 0, 0

    if taxable_income <= 10000000:
        rate = 0.10
        threshold = 5000000
    elif taxable_income <= 20000000:
        rate = 0.15
        threshold = 10000000
    elif taxable_income <= 50000000:
        rate = 0.25
        threshold = 20000000
    else:
        rate = 0.25 if regime == "new" else 0.37
        threshold = 50000000

    raw_surcharge = round(tax_after_rebate * rate)

    # Marginal Relief on Surcharge:
    # Total tax + surcharge on (threshold + excess) should not exceed:
    # (Tax on threshold + surcharge on threshold) + excess income
    excess_income = taxable_income - threshold
    marginal_relief = 0
    if excess_income > 0:
        # Approximate tax at threshold
        if threshold == 5000000:
            tax_at_threshold = 1312500 if regime == "old" else 1080000
            surcharge_at_threshold = 0
        elif threshold == 10000000:
            tax_at_threshold = 2812500 if regime == "old" else 2580000
            surcharge_at_threshold = round(tax_at_threshold * 0.10)
        elif threshold == 20000000:
            tax_at_threshold = 5812500 if regime == "old" else 5580000
            surcharge_at_threshold = round(tax_at_threshold * 0.15)
        else:
            tax_at_threshold = 14812500 if regime == "old" else 14580000
            surcharge_at_threshold = round(tax_at_threshold * 0.25)

        max_allowable_tax_and_surcharge = tax_at_threshold + surcharge_at_threshold + excess_income
        current_tax_and_surcharge = tax_after_rebate + raw_surcharge

        if current_tax_and_surcharge > max_allowable_tax_and_surcharge:
            marginal_relief = current_tax_and_surcharge - max_allowable_tax_and_surcharge
            raw_surcharge = max(0, raw_surcharge - marginal_relief)

    return raw_surcharge, marginal_relief


def calculate_basic_tax(
    taxable_income,
    financial_year,
    regime="new",
    age=30,
    is_resident=True
):
    """
    Calculate income tax including slabs, Section 87A rebate with
    marginal relief, surcharge, cess, and Section 288B rounding.
    """

    rules = get_tax_rules(financial_year)

    slabs = get_slabs(
        financial_year,
        regime,
        age
    )

    tax_before_rebate = calculate_tax_from_slabs(
        taxable_income,
        slabs
    )

    # --------------------------------------------------------
    # Rebate under Section 87A & Marginal Relief
    # (Available only to Resident Individuals)
    # --------------------------------------------------------

    rebate = 0

    if is_resident:
        if regime == "new":
            rebate_rules = rules["new_regime"].get(
                "rebate_87a",
                rules["new_regime"].get("rebate", {})
            )
            income_limit = rebate_rules.get("income_limit", 1200000)
            maximum_rebate = rebate_rules.get("maximum", 60000)

            if taxable_income <= income_limit:
                rebate = min(tax_before_rebate, maximum_rebate)
            elif taxable_income > income_limit:
                # Statutory Marginal Relief under proviso to Section 87A:
                # Tax payable after rebate cannot exceed (taxable_income - income_limit)
                excess_income = taxable_income - income_limit
                if tax_before_rebate > excess_income:
                    rebate = tax_before_rebate - excess_income
                else:
                    rebate = 0

        elif regime == "old":
            rebate_rules = rules["old_regime"].get("rebate_87a", {})
            income_limit = rebate_rules.get("income_limit", 500000)
            maximum_rebate = rebate_rules.get("maximum", 12500)

            if taxable_income <= income_limit:
                rebate = min(tax_before_rebate, maximum_rebate)

    tax_after_rebate = max(
        0,
        tax_before_rebate - rebate
    )

    # --------------------------------------------------------
    # Surcharge & Marginal Relief
    # --------------------------------------------------------

    surcharge, surcharge_marginal_relief = calculate_surcharge(
        taxable_income=taxable_income,
        tax_after_rebate=tax_after_rebate,
        regime=regime
    )

    # --------------------------------------------------------
    # Health & Education Cess @ 4%
    # --------------------------------------------------------

    cess_rate = rules.get("cess", 0.04)

    cess = round(
        (tax_after_rebate + surcharge) * cess_rate
    )

    # Section 288B Rounding off to nearest ₹10
    total_tax = int(round((tax_after_rebate + surcharge + cess) / 10.0) * 10)

    return {
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge": surcharge,
        "surcharge_marginal_relief": surcharge_marginal_relief,
        "cess": cess,
        "total_tax": total_tax
    }
# ============================================================
# INCOME CALCULATION
# ============================================================

def calculate_income(
    salary=0,
    pension=0,
    house_property=0,
    other_sources=0,
    capital_gains=0,
    agricultural_income=0
):
    """
    Calculate gross income from different income sources.
    """

    salary = max(0, float(salary))
    pension = max(0, float(pension))
    house_property = float(house_property)
    other_sources = max(0, float(other_sources))
    capital_gains = max(0, float(capital_gains))
    agricultural_income = max(0, float(agricultural_income))

    gross_income = (
        salary
        + pension
        + house_property
        + other_sources
        + capital_gains
        + agricultural_income
    )

    return {
        "salary": salary,
        "pension": pension,
        "house_property": house_property,
        "other_sources": other_sources,
        "capital_gains": capital_gains,
        "agricultural_income": agricultural_income,
        "gross_income": gross_income
    }


# ============================================================
# STANDARD DEDUCTION
# ============================================================

def get_standard_deduction(financial_year, regime="new"):
    """
    Return the standard deduction applicable to salary/pension
    for the selected financial year and regime.

    This is currently configured for the salary/pension
    calculator path. Other income heads require separate rules.
    """

    rules = get_tax_rules(financial_year)

    if regime == "new":
        return rules["new_regime"].get(
            "standard_deduction",
            0
        )

    if regime == "old":
        return rules["old_regime"].get(
            "standard_deduction",
            0
        )

    raise ValueError("Invalid tax regime.")


# ============================================================
# CHAPTER VI-A DEDUCTIONS
# ============================================================

def calculate_deductions(
    financial_year,
    regime="new",
    deduction_80c=0,
    deduction_80ccd=0,
    deduction_80d=0,
    deduction_80e=0,
    deduction_80g=0,
    deduction_80tta=0
):
    """
    Calculate eligible deductions.

    For the academic calculator, deductions are capped and
    regime eligibility is handled centrally.

    More specialized deductions will be added as separate
    rule modules.
    """

    # New regime generally does not permit the normal
    # Chapter VI-A deductions used under the old regime.
    if regime == "new":

        eligible_80c = 0
        eligible_80ccd = 0
        eligible_80d = 0
        eligible_80e = 0
        eligible_80g = 0
        eligible_80tta = 0

    else:

        # 80C combined limit
        eligible_80c = min(
            max(0, float(deduction_80c)),
            150000
        )

        eligible_80ccd = max(
            0,
            float(deduction_80ccd)
        )

        eligible_80d = max(
            0,
            float(deduction_80d)
        )

        eligible_80e = max(
            0,
            float(deduction_80e)
        )

        eligible_80g = max(
            0,
            float(deduction_80g)
        )

        eligible_80tta = min(
            max(0, float(deduction_80tta)),
            10000
        )

    total_deductions = (
        eligible_80c
        + eligible_80ccd
        + eligible_80d
        + eligible_80e
        + eligible_80g
        + eligible_80tta
    )

    return {
        "80C": eligible_80c,
        "80CCD": eligible_80ccd,
        "80D": eligible_80d,
        "80E": eligible_80e,
        "80G": eligible_80g,
        "80TTA": eligible_80tta,
        "total": total_deductions
    }


# ============================================================
# COMPLETE BASIC CALCULATION
# ============================================================

def calculate_income_tax(
    financial_year,
    regime="new",
    age=30,
    is_resident=True,
    salary=0,
    pension=0,
    house_property=0,
    other_sources=0,
    capital_gains=0,
    agricultural_income=0,
    deduction_80c=0,
    deduction_80ccd=0,
    deduction_80d=0,
    deduction_80e=0,
    deduction_80g=0,
    deduction_80tta=0,
    tds=0,
    tcs=0,
    advance_tax=0,
    self_assessment_tax=0
):
    """
    Complete statutory income-tax calculation pipeline.

    Calculates:
    1. Five heads of income + Gross Total Income (GTI)
    2. Standard Deduction u/s 16(ia)
    3. Chapter VI-A deductions (under applicable regime)
    4. Total Taxable Income rounded u/s 288A to nearest ₹10
    5. Slab Tax computation
    6. Section 87A rebate & statutory marginal relief
    7. Surcharge & statutory surcharge marginal relief
    8. Health & Education Cess @ 4%
    9. Total Tax Liability rounded u/s 288B to nearest ₹10
    10. Prepaid tax credits (TDS, TCS, Advance Tax, Self-Assessment Tax)
    11. Net Tax Payable or Refund Determined u/s 288B
    """

    # --------------------------------------------------------
    # 1. Calculate income
    # --------------------------------------------------------

    income = calculate_income(
        salary=salary,
        pension=pension,
        house_property=house_property,
        other_sources=other_sources,
        capital_gains=capital_gains,
        agricultural_income=agricultural_income
    )

    gross_income = income["gross_income"]

    # --------------------------------------------------------
    # 2. Standard deduction u/s 16(ia)
    # --------------------------------------------------------

    standard_deduction = 0

    if salary > 0 or pension > 0:

        standard_deduction = get_standard_deduction(
            financial_year,
            regime
        )

        standard_deduction = min(
            standard_deduction,
            salary + pension
        )

    # --------------------------------------------------------
    # 3. Income after standard deduction
    # --------------------------------------------------------

    income_after_standard_deduction = max(
        0,
        gross_income - standard_deduction
    )

    # --------------------------------------------------------
    # 4. Chapter VI-A deductions
    # --------------------------------------------------------

    deductions = calculate_deductions(
        financial_year=financial_year,
        regime=regime,
        deduction_80c=deduction_80c,
        deduction_80ccd=deduction_80ccd,
        deduction_80d=deduction_80d,
        deduction_80e=deduction_80e,
        deduction_80g=deduction_80g,
        deduction_80tta=deduction_80tta
    )

    # --------------------------------------------------------
    # 5. Taxable income (Section 288A: rounded to nearest ₹10)
    # --------------------------------------------------------

    total_deductions = deductions["total"]

    taxable_income = max(
        0,
        income_after_standard_deduction - total_deductions
    )

    taxable_income = int(round(taxable_income / 10.0) * 10)

    # --------------------------------------------------------
    # 6. Calculate tax with slabs, 87A, surcharge & cess
    # --------------------------------------------------------

    tax_result = calculate_basic_tax(
        taxable_income=taxable_income,
        financial_year=financial_year,
        regime=regime,
        age=age,
        is_resident=is_resident
    )

    # --------------------------------------------------------
    # 7. Tax payments
    # --------------------------------------------------------

    tds = max(0, float(tds))
    tcs = max(0, float(tcs))
    advance_tax = max(0, float(advance_tax))
    self_assessment_tax = max(0, float(self_assessment_tax))

    total_tax_paid = (
        tds
        + tcs
        + advance_tax
        + self_assessment_tax
    )

    # --------------------------------------------------------
    # 8. Final amount (Section 288B: rounded to nearest ₹10)
    # --------------------------------------------------------

    balance = tax_result["total_tax"] - total_tax_paid

    if balance > 0:
        refund = 0
        tax_payable = int(round(balance / 10.0) * 10)
    else:
        refund = int(round(abs(balance) / 10.0) * 10)
        tax_payable = 0

    # --------------------------------------------------------
    # 9. Final result
    # --------------------------------------------------------

    return {
        "financial_year": financial_year,
        "regime": regime,
        "age": age,
        "is_resident": is_resident,
        "income": income,
        "gross_income": gross_income,
        "standard_deduction": standard_deduction,
        "income_after_standard_deduction": income_after_standard_deduction,
        "deductions": deductions,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_result["tax_before_rebate"],
        "rebate": tax_result["rebate"],
        "tax_after_rebate": tax_result["tax_after_rebate"],
        "surcharge": tax_result.get("surcharge", 0),
        "surcharge_marginal_relief": tax_result.get("surcharge_marginal_relief", 0),
        "cess": tax_result["cess"],
        "total_tax": tax_result["total_tax"],
        "tds": tds,
        "tcs": tcs,
        "advance_tax": advance_tax,
        "self_assessment_tax": self_assessment_tax,
        "total_tax_paid": total_tax_paid,
        "refund": refund,
        "tax_payable": tax_payable
    }