"""
ITR Learn & Simulate
logic/tax_rules.py

Rule-Based Logic module.

This module exposes clean rule-based helper functions
for tax slabs, deduction rules, regime rules, and
tax-related reference data.

It imports configuration from tax_engine/calculator.py
so that all tax data is in ONE place.

DO NOT modify tax_engine/calculator.py.
DO NOT duplicate tax calculation logic here.
This module only exposes structured rule data and
helper queries for the UI and simulation.

Educational simulation only.
"""

from tax_engine.calculator import TAX_RULES, get_tax_rules


# ============================================================
# AVAILABLE FINANCIAL YEARS
# ============================================================

def get_supported_years():
    """Return list of supported financial years."""
    return list(TAX_RULES.keys())


# ============================================================
# TAX SLAB DATA FOR DISPLAY
# ============================================================

def get_slab_display_data(financial_year="FY2025-26"):
    """
    Return structured slab data for displaying in the Tax Slabs page.

    Returns:
        dict with new_regime and old_regime slab info
    """

    rules = get_tax_rules(financial_year)

    result = {
        "financial_year": rules.get("financial_year", financial_year),
        "assessment_year": rules.get(
            "assessment_year",
            rules.get("tax_year", "")
        ),
        "law": rules.get("law", "Income-tax Act, 1961"),
        "new_regime": None,
        "old_regime": None,
        "cess": rules.get("cess", 0.04)
    }

    # New regime slabs
    new = rules.get("new_regime", {})
    if new:
        result["new_regime"] = {
            "slabs": new.get("slabs", []),
            "standard_deduction": new.get("standard_deduction", 0),
            "rebate_87a": new.get(
                "rebate_87a",
                new.get("rebate", {})
            ),
            "note": new.get("note", "")
        }

    # Old regime slabs
    old = rules.get("old_regime", {})
    if old:
        result["old_regime"] = {
            "general": old.get("general", []),
            "senior_citizen": old.get("senior_citizen", []),
            "super_senior_citizen": old.get("super_senior_citizen", []),
            "standard_deduction": old.get("standard_deduction", 0),
            "rebate_87a": old.get("rebate_87a", {}),
            "note": old.get("note", "")
        }

    return result


# ============================================================
# DEDUCTION RULES REFERENCE DATA
# ============================================================

DEDUCTION_RULES = [
    {
        "section": "80C",
        "name": "Investments & Payments",
        "description": (
            "Life insurance premium (LIC), PPF, EPF employee contribution, "
            "ELSS mutual funds, NSC, home loan principal repayment, "
            "children's school tuition fees, tax-saver FD (5 years)."
        ),
        "limit": 150000,
        "regime": "old",
        "notes": "Combined limit for 80C + 80CCC + 80CCD(1) is ₹1.5 lakh."
    },
    {
        "section": "80CCD(1B)",
        "name": "Additional NPS Contribution",
        "description": (
            "Self-contribution to National Pension System (NPS) "
            "over and above the 80C limit."
        ),
        "limit": 50000,
        "regime": "old",
        "notes": "This is in addition to the ₹1.5 lakh 80C limit."
    },
    {
        "section": "80CCD(2)",
        "name": "Employer NPS Contribution",
        "description": (
            "Employer contribution to NPS account of the employee. "
            "Available under both regimes."
        ),
        "limit": None,
        "limit_note": "Up to 10% of salary (14% for govt employees)",
        "regime": "both",
        "notes": "Available under New Tax Regime too."
    },
    {
        "section": "80D",
        "name": "Health Insurance Premium",
        "description": (
            "Premium paid for medical insurance for self, "
            "spouse, dependent children, and parents."
        ),
        "limit": 25000,
        "limit_note": "₹25,000 (self/family) + ₹25,000 (parents) = ₹50,000",
        "regime": "old",
        "notes": "For senior citizens, the limit is ₹50,000 each."
    },
    {
        "section": "80E",
        "name": "Education Loan Interest",
        "description": (
            "Interest paid on loan taken for higher education "
            "of self, spouse, or children."
        ),
        "limit": None,
        "limit_note": "No maximum limit",
        "regime": "old",
        "notes": "Available for 8 assessment years from repayment start."
    },
    {
        "section": "80G",
        "name": "Donations",
        "description": (
            "Donations to approved funds, charitable institutions, "
            "and government relief funds."
        ),
        "limit": None,
        "limit_note": "50% or 100% of donation amount depending on recipient",
        "regime": "old",
        "notes": "Cash donations above ₹2,000 are not eligible."
    },
    {
        "section": "80TTA",
        "name": "Savings Account Interest",
        "description": (
            "Interest earned on savings bank account "
            "(for individuals below 60 years)."
        ),
        "limit": 10000,
        "regime": "old",
        "notes": "Not available for senior citizens — 80TTB applies instead."
    },
    {
        "section": "80TTB",
        "name": "Senior Citizen Interest Deduction",
        "description": (
            "Interest on deposits (savings, FD, recurring) "
            "for senior citizens (60 years and above)."
        ),
        "limit": 50000,
        "regime": "old",
        "notes": "Available only for senior citizens. 80TTA does not apply."
    },
    {
        "section": "24(b)",
        "name": "Home Loan Interest",
        "description": (
            "Interest on home loan for self-occupied or let-out property."
        ),
        "limit": 200000,
        "limit_note": "₹2 lakh for self-occupied; no limit for let-out property",
        "regime": "old",
        "notes": (
            "For let-out property, set-off of loss may be restricted to "
            "₹2 lakh per year under current rules."
        )
    }
]


def get_deduction_rules(regime=None):
    """
    Return deduction rules, optionally filtered by regime.

    Args:
        regime: 'old', 'new', or None (return all)
    """

    if regime is None:
        return DEDUCTION_RULES

    return [
        d for d in DEDUCTION_RULES
        if d.get("regime") in (regime, "both")
    ]


# ============================================================
# REGIME COMPARISON RULES
# ============================================================

REGIME_COMPARISON = {
    "new_regime": {
        "name": "New Tax Regime",
        "default": True,
        "standard_deduction": {
            "FY2025-26": 75000
        },
        "key_features": [
            "Lower tax slab rates",
            "Standard deduction of ₹75,000 on salary/pension",
            "Rebate u/s 87A up to ₹60,000 (income ≤ ₹12 lakh)",
            "Employer NPS contribution (80CCD(2)) allowed",
            "Most Chapter VI-A deductions not available",
            "No HRA, LTA exemptions",
            "No home loan interest deduction (Section 24b)",
        ],
        "best_for": (
            "Individuals with few investments/deductions, "
            "or those who prefer simplicity."
        )
    },
    "old_regime": {
        "name": "Old Tax Regime",
        "default": False,
        "standard_deduction": {
            "FY2025-26": 50000
        },
        "key_features": [
            "Higher basic exemption for senior/super-senior citizens",
            "Section 80C deductions up to ₹1.5 lakh",
            "Section 80D health insurance deductions",
            "HRA exemption available",
            "Home loan interest deduction (Section 24b)",
            "Rebate u/s 87A up to ₹12,500 (income ≤ ₹5 lakh)",
            "Education loan interest (80E) deductible",
        ],
        "best_for": (
            "Individuals with significant investments, "
            "home loans, or dependents with medical needs."
        )
    }
}


def get_regime_comparison():
    """Return regime comparison data."""
    return REGIME_COMPARISON


# ============================================================
# ITR FORM REFERENCE DATA
# ============================================================

ITR_FORMS = [
    {
        "form": "ITR-1",
        "name": "Sahaj",
        "applicability": "Resident individuals only",
        "income_sources": [
            "Salary / Pension",
            "One house property",
            "Other sources (interest, dividends)",
            "Agricultural income up to ₹5,000"
        ],
        "not_applicable": [
            "Non-Residents",
            "Capital gains income",
            "Business/professional income",
            "More than one house property",
            "Total income above ₹50 lakh",
            "Foreign income/assets",
            "Director in a company",
            "Unlisted equity shares"
        ],
        "color": "green"
    },
    {
        "form": "ITR-2",
        "name": "For Individuals & HUF",
        "applicability": "Individuals and HUF without business income",
        "income_sources": [
            "Salary / Pension",
            "Multiple house properties",
            "Capital gains",
            "Foreign income / assets",
            "Other sources",
            "Agricultural income above ₹5,000"
        ],
        "not_applicable": [
            "Business or professional income (use ITR-3)"
        ],
        "color": "blue"
    },
    {
        "form": "ITR-3",
        "name": "For Business/Profession (Regular Accounts)",
        "applicability": "Individuals/HUF having income from business or profession",
        "income_sources": [
            "Business income (regular accounts)",
            "Professional income",
            "Partnership firm income",
            "All ITR-2 income types"
        ],
        "not_applicable": [],
        "color": "orange"
    },
    {
        "form": "ITR-4",
        "name": "Sugam (Presumptive Taxation)",
        "applicability": "Individuals/HUF/Firms opting for presumptive taxation",
        "income_sources": [
            "Business income under Sec 44AD",
            "Professional income under Sec 44ADA",
            "Transport business under Sec 44AE",
            "Salary/pension",
            "One house property"
        ],
        "not_applicable": [
            "Capital gains",
            "Foreign income/assets",
            "More than one house property",
            "Income above ₹50 lakh"
        ],
        "color": "purple"
    }
]


def get_itr_forms():
    """Return all ITR form reference data."""
    return ITR_FORMS


# ============================================================
# IMPORTANT DATES REFERENCE
# ============================================================

IMPORTANT_DATES = {
    "FY2025-26": {
        "due_date_non_audit": "July 31, 2026",
        "due_date_audit": "October 31, 2026",
        "advance_tax_q1": "June 15, 2025",
        "advance_tax_q2": "September 15, 2025",
        "advance_tax_q3": "December 15, 2025",
        "advance_tax_q4": "March 15, 2026",
        "note": (
            "Dates are for reference/educational purposes only. "
            "Always verify with official Income Tax Department sources."
        )
    }
}


def get_important_dates(financial_year="FY2025-26"):
    """Return important tax dates for the given financial year."""
    return IMPORTANT_DATES.get(financial_year, {})
