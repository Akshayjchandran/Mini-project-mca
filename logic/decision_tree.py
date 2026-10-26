"""
ITR Learn & Simulate
logic/decision_tree.py

Decision Tree algorithm module.

This module implements decision-tree-style classification logic for:
  A. ITR Form Selection
  B. Residential Status Classification
  C. Income Classification
  D. Deduction Eligibility
  E. Simulation Validation
  F. Practice Scenario Classification

All logic is deterministic and rule-based.
No AI is used here — AI (Gemini) is used only for explanations.

Educational simulation only.
"""


# ============================================================
# A. ITR FORM SELECTION DECISION TREE & ELIGIBILITY ENGINE
# ============================================================

def select_itr_form(
    salary_income=False,
    pension_income=False,
    one_house_property=False,
    multiple_house_property=False,
    business_income=False,
    professional_income=False,
    presumptive_taxation=False,
    capital_gains=False,
    foreign_income=False,
    foreign_assets=False,
    agriculture_income=0,
    director_in_company=False,
    unlisted_shares=False,
    lottery_income=False,
    total_income=0,
    income_above_50l=None,
    is_resident=True,
    residential_status="Resident and Ordinarily Resident (ROR)",
    status_code="ROR",
    **kwargs
):
    """
    Deterministic Eligibility & Selection Engine for ITR-1, ITR-2, ITR-3, and ITR-4.
    Governed by Rule 12 of the Income-tax Rules, 1962.

    Decision Priority:
      1. Evaluate residential status.
      2. Evaluate business/professional income.
      3. Evaluate presumptive taxation eligibility.
      4. Evaluate capital gains.
      5. Evaluate house-property conditions.
      6. Evaluate foreign assets/income.
      7. Evaluate gross total income (> ₹50 Lakh).
      8. Evaluate remaining statutory exclusions (directorship, unlisted shares, agri > ₹5k).
      9. Return eligible form or explain disqualifications.
    """

    path = []
    disqualifications = []
    eligible_forms = []
    ineligible_forms = []

    # Normalize residential flags
    is_nr = (
        not is_resident
        or status_code == "NR"
        or "Non-Resident" in str(residential_status)
    )
    is_rnor = (
        status_code == "RNOR"
        or "Not Ordinarily Resident" in str(residential_status)
    )
    has_business_or_prof = bool(business_income or professional_income)
    has_capital_gains = bool(capital_gains)
    has_multiple_hp = bool(multiple_house_property)
    has_foreign = bool(foreign_income or foreign_assets)
    has_director_unlisted = bool(director_in_company or unlisted_shares)
    has_high_agri = float(agriculture_income or 0) > 5000
    has_high_income = float(total_income or 0) > 5000000 or bool(income_above_50l)  # ₹50 Lakh

    # --------------------------------------------------------
    # STEP 1: EVALUATE RESIDENTIAL STATUS
    # --------------------------------------------------------
    path.append(f"1. Residential Status Check: {residential_status} (Code: {status_code})")

    if is_nr:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Taxpayer is a Non-Resident (NR) under Section 6. Under Rule 12, ITR-1 is restricted to Resident individuals only.")
        disqualifications.append("ITR-4 (Sugam) disqualified: Taxpayer is a Non-Resident (NR). Presumptive ITR-4 is available only to Resident individuals/HUFs/Firms.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])
    elif is_rnor:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Resident but Not Ordinarily Resident (RNOR) individuals are not permitted to file ITR-1 Sahaj.")
        ineligible_forms.append("ITR-1")

    # --------------------------------------------------------
    # STEP 2 & 3: EVALUATE BUSINESS / PROFESSIONAL INCOME & PRESUMPTIVE TAXATION
    # --------------------------------------------------------
    path.append(f"2. Business / Profession Check: Business={business_income}, Profession={professional_income}")

    if has_business_or_prof:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Taxpayer has income under the head 'Profits and Gains of Business or Profession' (PGBP).")
        disqualifications.append("ITR-2 disqualified: Taxpayer has business or professional income. ITR-2 cannot be used by taxpayers having income under PGBP.")
        ineligible_forms.extend(["ITR-1", "ITR-2"])

        # Check Presumptive Scheme (ITR-4 Sugam)
        can_opt_itr4 = (
            presumptive_taxation
            and not is_nr
            and not is_rnor
            and not has_capital_gains
            and not has_multiple_hp
            and not has_foreign
            and not has_director_unlisted
            and not has_high_agri
            and not has_high_income
        )

        if can_opt_itr4:
            path.append("Presumptive Taxation scheme u/s 44AD/44ADA/44AE eligible & opted -> ITR-4")
            return {
                "form": "ITR-4 (Sugam)",
                "form_code": "ITR-4",
                "recommended_form": "ITR-4 (Sugam)",
                "eligible": True,
                "eligibility_status": "Eligible for ITR-4 Sugam under Presumptive Scheme",
                "reason": (
                    "You have business or professional income and are eligible for presumptive taxation "
                    "under Section 44AD / 44ADA / 44AE with total income up to ₹50 Lakh. "
                    "All statutory conditions for ITR-4 are satisfied."
                ),
                "disqualifications": disqualifications,
                "eligible_forms": ["ITR-4", "ITR-3"],
                "ineligible_forms": list(set(ineligible_forms)),
                "path": path,
                "simulation_note": "Educational simulation only. Verify presumptive limits before actual filing."
            }
        else:
            if presumptive_taxation:
                if has_capital_gains:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Taxpayers with Capital Gains cannot file ITR-4.")
                if has_multiple_hp:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Taxpayers owning more than one house property cannot file ITR-4.")
                if has_high_income:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Total income exceeds ₹50 Lakh statutory limit.")
                if has_foreign:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Holding foreign assets or foreign income bars ITR-4.")
                if has_director_unlisted:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Being a director or holding unlisted equity shares bars ITR-4.")
                if is_nr:
                    disqualifications.append("ITR-4 (Sugam) disqualified: Non-Residents cannot file ITR-4.")

            path.append("Business income present and not eligible/opted for ITR-4 -> ITR-3 mandatory")
            return {
                "form": "ITR-3",
                "form_code": "ITR-3",
                "recommended_form": "ITR-3",
                "eligible": True,
                "eligibility_status": "Eligible for ITR-3 (PGBP with Regular Books or Complex Sources)",
                "reason": (
                    "You have income from business or profession that requires ITR-3. "
                    "ITR-1 and ITR-2 are strictly prohibited for business/professional income. "
                    "ITR-4 is not available because of statutory exclusions (or regular books maintained)."
                ),
                "disqualifications": disqualifications,
                "eligible_forms": ["ITR-3"],
                "ineligible_forms": list(set(ineligible_forms + ["ITR-1", "ITR-2", "ITR-4"])),
                "path": path,
                "simulation_note": "Educational simulation only. ITR-3 is the standard return for business and professional income."
            }

    # --------------------------------------------------------
    # STEP 4: EVALUATE CAPITAL GAINS
    # --------------------------------------------------------
    path.append(f"4. Capital Gains Check: {has_capital_gains}")
    if has_capital_gains:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Capital gains income from shares, mutual funds, or immovable property cannot be reported in ITR-1.")
        disqualifications.append("ITR-4 (Sugam) disqualified: Capital gains cannot be reported in ITR-4.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    # --------------------------------------------------------
    # STEP 5: EVALUATE HOUSE PROPERTY CONDITIONS
    # --------------------------------------------------------
    path.append(f"5. House Property Check: Multiple={has_multiple_hp}")
    if has_multiple_hp:
        disqualifications.append("ITR-1 (Sahaj) disqualified: ITR-1 permits income from only one single house property. Multiple properties require ITR-2.")
        disqualifications.append("ITR-4 (Sugam) disqualified: ITR-4 permits income from only one single house property.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    # --------------------------------------------------------
    # STEP 6: EVALUATE FOREIGN ASSETS / FOREIGN INCOME
    # --------------------------------------------------------
    path.append(f"6. Foreign Income / Assets Check: {has_foreign}")
    if has_foreign:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Taxpayer holds foreign assets or has foreign-sourced income, requiring Schedule FA in ITR-2.")
        disqualifications.append("ITR-4 (Sugam) disqualified: Foreign assets/income bar ITR-4.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    # --------------------------------------------------------
    # STEP 7: EVALUATE TOTAL GROSS INCOME LIMIT
    # --------------------------------------------------------
    path.append(f"7. Income Ceiling Check: Total Income={total_income}")
    if has_high_income:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Total gross income exceeds statutory ceiling of ₹50,00,000 (₹50 Lakh).")
        disqualifications.append("ITR-4 (Sugam) disqualified: Total gross income exceeds statutory ceiling of ₹50,00,000 (₹50 Lakh).")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    # --------------------------------------------------------
    # STEP 8: EVALUATE REMAINING STATUTORY EXCLUSIONS
    # --------------------------------------------------------
    path.append(f"8. Special Conditions: Director/Unlisted={has_director_unlisted}, Agri>5k={has_high_agri}")
    if has_director_unlisted:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Taxpayer is a company director or holds unlisted equity shares.")
        disqualifications.append("ITR-4 (Sugam) disqualified: Taxpayer is a company director or holds unlisted equity shares.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    if has_high_agri:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Agricultural income exceeds statutory ceiling of ₹5,000.")
        disqualifications.append("ITR-4 (Sugam) disqualified: Agricultural income exceeds statutory ceiling of ₹5,000.")
        ineligible_forms.extend(["ITR-1", "ITR-4"])

    if lottery_income:
        disqualifications.append("ITR-1 (Sahaj) disqualified: Income from lottery, puzzles, or race horses cannot be filed in ITR-1.")
        ineligible_forms.append("ITR-1")

    # --------------------------------------------------------
    # FINAL RECOMMENDATION LOGIC
    # --------------------------------------------------------
    # If any ITR-1 disqualification exists, ITR-1 is rejected
    has_itr1_disqualification = bool(
        is_nr or is_rnor or has_capital_gains or has_multiple_hp or
        has_foreign or has_high_income or has_director_unlisted or
        has_high_agri or lottery_income or has_business_or_prof
    )

    if has_itr1_disqualification:
        # User has non-business income but failed ITR-1 criteria -> ITR-2
        path.append("ITR-1 disqualified -> Recommend ITR-2")
        return {
            "form": "ITR-2",
            "form_code": "ITR-2",
            "recommended_form": "ITR-2",
            "eligible": True,
            "eligibility_status": "Eligible for ITR-2 (Ineligible for ITR-1 Sahaj)",
            "reason": (
                "You are not eligible for ITR-1 (Sahaj) due to one or more statutory disqualifications "
                "under Rule 12. Since you have no business or professional income, ITR-2 is the applicable form."
            ),
            "disqualifications": disqualifications,
            "eligible_forms": ["ITR-2"],
            "ineligible_forms": list(set(ineligible_forms + ["ITR-1"])),
            "path": path,
            "simulation_note": "Educational simulation only. ITR-2 is required for capital gains, multiple properties, foreign assets, or income > ₹50 Lakh."
        }

    # If no disqualifications, verify basic permitted income sources for ITR-1
    has_permitted_income = bool(
        salary_income
        or pension_income
        or one_house_property
        or float(total_income or 0) > 0
    )

    if has_permitted_income:
        path.append("All ITR-1 criteria satisfied -> Recommend ITR-1 (Sahaj)")
        return {
            "form": "ITR-1 (Sahaj)",
            "form_code": "ITR-1",
            "recommended_form": "ITR-1 (Sahaj)",
            "eligible": True,
            "eligibility_status": "Fully Eligible for ITR-1 Sahaj",
            "reason": (
                "You are an eligible Resident and Ordinarily Resident (ROR) individual with total income "
                "up to ₹50 Lakh derived from permitted sources (Salary, one house property, and other sources). "
                "No disqualifying capital gains, business income, or foreign assets were reported."
            ),
            "disqualifications": [],
            "eligible_forms": ["ITR-1", "ITR-2"],
            "ineligible_forms": ["ITR-3", "ITR-4"],
            "path": path,
            "simulation_note": "Educational simulation only. Verify that all income sources fall strictly under Section 17, 22, and 56."
        }

    path.append("Insufficient data to recommend a specific form")
    return {
        "form": "ITR-1 (Sahaj)",
        "form_code": "ITR-1",
        "recommended_form": "ITR-1 (Sahaj)",
        "eligible": True,
        "eligibility_status": "Default Resident Evaluation",
        "reason": "Default form evaluation based on standard individual taxpayer profile.",
        "disqualifications": [],
        "eligible_forms": ["ITR-1", "ITR-2"],
        "ineligible_forms": [],
        "path": path,
        "simulation_note": "Educational simulation only."
    }


# ============================================================
# B. RESIDENTIAL STATUS DECISION TREE — SECTION 6
# ============================================================

def determine_residential_status(
    days_in_india_current_year=0,
    days_in_india_last_4_years=0,
    days_in_india_last_7_years=0,
    resident_in_at_least_2_of_10_years=False,
    resident_in_9_of_10_years=None,  # backward compatibility alias
    is_indian_citizen_leaving_for_employment=False,
    is_visiting_india=False,
    indian_source_income=0
):
    """
    Statutory Residential Status Determination Engine under Section 6 of
    the Income-tax Act, 1961.

    A. Basic Conditions (Section 6(1)):
       1. Stay in India during previous year >= 182 days; OR
       2. Stay in India during previous year >= 60 days AND
          stay in India in preceding 4 previous years >= 365 days.

       Statutory Exceptions modifying the 60-day condition:
       - Indian citizen leaving India for employment outside India or as crew member:
         60 days replaced by 182 days (i.e. only 182-day rule applies).
       - Indian citizen / Person of Indian Origin (PIO) visiting India:
         - If Indian-sourced income > ₹15 Lakh: 60 days replaced by 120 days.
         - If Indian-sourced income <= ₹15 Lakh: 60 days replaced by 182 days.

    B. Additional Conditions for Ordinarily Resident (Section 6(6)):
       1. Resident in India in at least 2 out of the 10 previous years preceding
          the relevant financial year.
       2. Stay in India for 730 days or more in the 7 previous years preceding
          the relevant financial year.

    Classification:
       - Satisfies both additional conditions: Resident and Ordinarily Resident (ROR).
       - Fails either additional condition: Resident but Not Ordinarily Resident (RNOR).
       - Fails all basic conditions: Non-Resident (NR).
    """

    path = []

    # Safe numeric casts
    try:
        days_curr = int(days_in_india_current_year or 0)
    except (ValueError, TypeError):
        days_curr = 0

    try:
        days_4yr = int(days_in_india_last_4_years or 0)
    except (ValueError, TypeError):
        days_4yr = 0

    try:
        days_7yr = int(days_in_india_last_7_years or 0)
    except (ValueError, TypeError):
        days_7yr = 0

    try:
        ind_inc = float(indian_source_income or 0)
    except (ValueError, TypeError):
        ind_inc = 0

    # Support legacy argument alias
    if resident_in_9_of_10_years is not None and not resident_in_at_least_2_of_10_years:
        res_2_10 = bool(resident_in_9_of_10_years)
    else:
        res_2_10 = bool(resident_in_at_least_2_of_10_years)

    # --------------------------------------------------------
    # STEP 1: EVALUATE BASIC CONDITIONS (SECTION 6(1))
    # --------------------------------------------------------
    path.append(f"Basic Test 1: Stay in current FY ({days_curr} days) >= 182 days")
    cond_1_satisfied = (days_curr >= 182)

    # Determine applicable threshold for second basic condition
    secondary_threshold = 60
    exception_note = ""

    if is_indian_citizen_leaving_for_employment:
        secondary_threshold = 182
        exception_note = "Exception u/s 6(1) Expl. 1(a): Indian citizen leaving India for employment requires 182 days."
    elif is_visiting_india:
        if ind_inc > 1500000:
            secondary_threshold = 120
            exception_note = "Exception u/s 6(1) Expl. 1(b): Visiting Indian citizen/PIO with Indian income > ₹15L has modified 120-day threshold."
        else:
            secondary_threshold = 182
            exception_note = "Exception u/s 6(1) Expl. 1(b): Visiting Indian citizen/PIO with Indian income <= ₹15L requires 182 days."

    if exception_note:
        path.append(exception_note)

    path.append(
        f"Basic Test 2: Stay in current FY ({days_curr} days) >= {secondary_threshold} days "
        f"AND stay in 4 preceding years ({days_4yr} days) >= 365 days"
    )
    cond_2_satisfied = (days_curr >= secondary_threshold and days_4yr >= 365)

    is_basic_resident = cond_1_satisfied or cond_2_satisfied

    # --------------------------------------------------------
    # NON-RESIDENT (NR) DETERMINATION
    # --------------------------------------------------------
    if not is_basic_resident:
        path.append("RESULT: Fails both basic conditions of Section 6(1) -> Non-Resident (NR)")
        return {
            "status": "Non-Resident (NR)",
            "status_code": "NR",
            "is_resident": False,
            "is_ror": False,
            "is_rnor": False,
            "itr_1_eligible": False,
            "reason": (
                f"You stayed in India for {days_curr} days during the current financial year (< 182 days) "
                f"and {days_4yr} days in the preceding 4 years (< 365 days or < {secondary_threshold} days in current year). "
                "You do not satisfy either basic condition of Section 6(1) of the Income-tax Act, 1961. "
                "Therefore, your residential status is determined as Non-Resident (NR)."
            ),
            "scope_of_income": (
                "Under Section 5(2), only income received, accrued, or deemed to be received or accrued in India "
                "is taxable in India. Foreign-sourced income is completely exempt."
            ),
            "form_restriction": (
                "Non-Residents are NOT eligible to file ITR-1 (Sahaj) or ITR-4 (Sugam). "
                "You must file ITR-2 (or ITR-3 if you have business/professional income in India)."
            ),
            "path": path
        }

    # --------------------------------------------------------
    # STEP 2: EVALUATE ADDITIONAL CONDITIONS (SECTION 6(6))
    # --------------------------------------------------------
    path.append("Basic condition satisfied. Evaluating Section 6(6) Ordinarily Resident conditions:")

    # Condition 1: Resident in India in at least 2 out of 10 preceding previous years
    add_cond_1 = bool(res_2_10)
    path.append(f"Additional Condition 1: Resident in >= 2 of 10 preceding FYs? {add_cond_1}")

    # Condition 2: Stayed in India for >= 730 days in preceding 7 previous years
    add_cond_2 = (days_7yr >= 730)
    path.append(f"Additional Condition 2: Stay in preceding 7 FYs ({days_7yr} days) >= 730 days? {add_cond_2}")

    # Special RNOR case: Visiting citizen/PIO with Indian income > 15L staying between 120 and 181 days
    deemed_rnor_120_days = is_visiting_india and ind_inc > 1500000 and (120 <= days_curr < 182)

    if add_cond_1 and add_cond_2 and not deemed_rnor_120_days:
        path.append("RESULT: Both Section 6(6) additional conditions satisfied -> Resident and Ordinarily Resident (ROR)")
        return {
            "status": "Resident and Ordinarily Resident (ROR)",
            "status_code": "ROR",
            "is_resident": True,
            "is_ror": True,
            "is_rnor": False,
            "itr_1_eligible": True,
            "reason": (
                f"You satisfied a basic condition of Section 6(1) (stay of {days_curr} days in India) "
                f"AND both additional conditions under Section 6(6): you were a resident in at least 2 of the 10 preceding years "
                f"and stayed {days_7yr} days in India during the preceding 7 years (>= 730 days)."
            ),
            "scope_of_income": (
                "Under Section 5(1), your worldwide/global income (both inside and outside India) is taxable in India."
            ),
            "form_restriction": (
                "You are eligible to file ITR-1 (Sahaj), subject to income sources and statutory limits (income <= ₹50 Lakh)."
            ),
            "path": path
        }
    else:
        fail_reasons = []
        if not add_cond_1:
            fail_reasons.append("Not resident in at least 2 out of 10 preceding previous years")
        if not add_cond_2:
            fail_reasons.append(f"Stay in preceding 7 years was {days_7yr} days (< 730 days)")
        if deemed_rnor_120_days:
            fail_reasons.append("Statutory RNOR u/s 6(6)(c) for visiting citizen/PIO with Indian income > ₹15L staying 120-181 days")

        path.append(f"RESULT: Fails one or more Section 6(6) conditions ({', '.join(fail_reasons)}) -> RNOR")
        return {
            "status": "Resident but Not Ordinarily Resident (RNOR)",
            "status_code": "RNOR",
            "is_resident": True,
            "is_ror": False,
            "is_rnor": True,
            "itr_1_eligible": False,
            "reason": (
                f"You satisfy the basic residency test under Section 6(1), but fail the additional tests under Section 6(6) "
                f"({'; '.join(fail_reasons)}). Therefore, your residential status is Resident but Not Ordinarily Resident (RNOR)."
            ),
            "scope_of_income": (
                "Under Section 5(1) proviso, income accrued or received outside India is not taxable unless it is derived "
                "from a business controlled in or profession set up in India."
            ),
            "form_restriction": (
                "Under Rule 12, RNOR taxpayers cannot file ITR-1 (Sahaj). You must file ITR-2 or ITR-3."
            ),
            "path": path
        }


# ============================================================
# C. INCOME CLASSIFICATION DECISION TREE
# ============================================================

def classify_income_source(source_name):
    """
    Classify a user-described income source into the
    correct Income Tax head.

    Returns:
        dict with head, description, and notes
    """

    source = source_name.lower().strip()

    # --------------------------------------------------------
    # Salary / Employment
    # --------------------------------------------------------

    SALARY_KEYWORDS = [
        "salary", "wages", "basic pay", "allowance", "hra",
        "perquisite", "bonus", "incentive", "form 16",
        "employment", "employer", "payslip"
    ]

    for kw in SALARY_KEYWORDS:
        if kw in source:
            return {
                "head": "Salaries",
                "section": "Section 17",
                "description": (
                    "Income from employer including basic salary, "
                    "allowances, perquisites, and bonuses."
                ),
                "notes": "Standard deduction of ₹50,000 (old) / ₹75,000 (new) applies."
            }

    # --------------------------------------------------------
    # House Property
    # --------------------------------------------------------

    HOUSE_KEYWORDS = [
        "rent", "house", "property", "flat", "building",
        "tenancy", "landlord", "houserent"
    ]

    for kw in HOUSE_KEYWORDS:
        if kw in source:
            return {
                "head": "Income from House Property",
                "section": "Sections 22–27",
                "description": (
                    "Income from letting out property or deemed rent "
                    "from self-occupied property."
                ),
                "notes": (
                    "30% standard deduction on net annual value allowed "
                    "under old regime."
                )
            }

    # --------------------------------------------------------
    # Business / Profession
    # --------------------------------------------------------

    BUSINESS_KEYWORDS = [
        "business", "profession", "freelance", "consulting",
        "trade", "manufacturing", "contractor", "self-employed",
        "firm", "partnership", "proprietor"
    ]

    for kw in BUSINESS_KEYWORDS:
        if kw in source:
            return {
                "head": "Profits and Gains from Business or Profession",
                "section": "Sections 28–44",
                "description": (
                    "Income from running a business, trade, profession, "
                    "or freelance work."
                ),
                "notes": (
                    "Various deductions for business expenses allowed. "
                    "Presumptive taxation available under Sec 44AD/44ADA."
                )
            }

    # --------------------------------------------------------
    # Capital Gains
    # --------------------------------------------------------

    CAPITAL_KEYWORDS = [
        "capital gain", "shares", "mutual fund", "stock",
        "equity", "property sale", "land sale", "debenture",
        "bond", "stcg", "ltcg"
    ]

    for kw in CAPITAL_KEYWORDS:
        if kw in source:
            return {
                "head": "Capital Gains",
                "section": "Sections 45–55A",
                "description": (
                    "Income from sale of capital assets such as property, "
                    "shares, mutual funds, or bonds."
                ),
                "notes": (
                    "Short-term gains (held < 12/24/36 months) and "
                    "long-term gains (held longer) are taxed at "
                    "different rates."
                )
            }

    # --------------------------------------------------------
    # Other Sources (default)
    # --------------------------------------------------------

    return {
        "head": "Income from Other Sources",
        "section": "Sections 56–59",
        "description": (
            "Residual head for income not covered by other heads. "
            "Includes interest income, dividends, lottery winnings, etc."
        ),
        "notes": (
            "Savings account interest (up to ₹10,000) may be deductible "
            "under Section 80TTA under old regime."
        )
    }


# ============================================================
# D. DEDUCTION ELIGIBILITY DECISION TREE
# ============================================================

def check_deduction_eligibility(
    regime,
    section,
    amount,
    age=30,
    has_salary=False,
    has_nps=False,
    has_health_insurance=False,
    has_education_loan=False,
    has_home_loan=False,
    has_savings_account=False,
    is_resident=True
):
    """
    Decision Tree for Deduction Eligibility.

    Returns:
        dict with eligible (True/False/Partial), allowed_amount,
        reason, and section info
    """

    section_upper = section.upper().strip()

    # --------------------------------------------------------
    # New Regime — most deductions not available
    # --------------------------------------------------------

    NEW_REGIME_ALLOWED = {
        "80CCD(2)": "Employer NPS contribution (no upper limit as % of salary).",
        "80CCH": "Agnipath Scheme contribution."
    }

    if regime == "new":

        if section_upper in NEW_REGIME_ALLOWED:
            return {
                "eligible": True,
                "allowed_amount": amount,
                "reason": (
                    f"{section_upper} is available under the New Tax Regime. "
                    + NEW_REGIME_ALLOWED[section_upper]
                ),
                "section": section_upper
            }

        return {
            "eligible": False,
            "allowed_amount": 0,
            "reason": (
                f"{section_upper} deduction is generally NOT available "
                "under the New Tax Regime (2025-26). "
                "Switch to the Old Tax Regime to claim this deduction."
            ),
            "section": section_upper
        }

    # --------------------------------------------------------
    # Old Regime — individual section checks
    # --------------------------------------------------------

    # 80C — LIC, PPF, ELSS, home loan principal, school fee, etc.
    if section_upper == "80C":
        cap = 150000
        allowed = min(amount, cap)
        return {
            "eligible": True,
            "allowed_amount": allowed,
            "reason": (
                "Section 80C deduction is available under the Old Regime. "
                "Eligible investments: LIC, PPF, EPF, ELSS, NSC, "
                "home loan principal, children's tuition fee, etc. "
                f"Maximum limit: ₹{cap:,}."
            ),
            "section": "80C"
        }

    # 80D — Health insurance premiums
    if section_upper == "80D":
        if not has_health_insurance:
            return {
                "eligible": False,
                "allowed_amount": 0,
                "reason": (
                    "Section 80D is for medical insurance premiums. "
                    "You indicated you do not have health insurance."
                ),
                "section": "80D"
            }
        if age >= 60:
            cap = 50000
        else:
            cap = 25000
        allowed = min(amount, cap)
        return {
            "eligible": True,
            "allowed_amount": allowed,
            "reason": (
                f"Section 80D: Health insurance premium deduction. "
                f"Limit for your age group: ₹{cap:,}. "
                "Additional deduction for parents' insurance may apply."
            ),
            "section": "80D"
        }

    # 80E — Education loan interest (no cap)
    if section_upper == "80E":
        if not has_education_loan:
            return {
                "eligible": False,
                "allowed_amount": 0,
                "reason": (
                    "Section 80E is for interest on education loans. "
                    "You indicated you do not have an education loan."
                ),
                "section": "80E"
            }
        return {
            "eligible": True,
            "allowed_amount": amount,
            "reason": (
                "Section 80E: Interest on education loan for higher studies. "
                "No maximum limit on the deduction amount. "
                "Available for 8 years from the year of repayment start."
            ),
            "section": "80E"
        }

    # 80G — Donations
    if section_upper == "80G":
        return {
            "eligible": "Partial",
            "allowed_amount": amount,
            "reason": (
                "Section 80G: Donations to approved funds/charities. "
                "The eligible percentage (50% or 100%) and whether a "
                "qualifying limit applies depends on the recipient organisation. "
                "Please verify the fund/institution's 80G registration."
            ),
            "section": "80G"
        }

    # 80TTA — Savings account interest (< 60 years)
    if section_upper == "80TTA":
        if age >= 60:
            return {
                "eligible": False,
                "allowed_amount": 0,
                "reason": (
                    "Section 80TTA (savings account interest up to ₹10,000) "
                    "is NOT applicable for senior citizens (age 60+). "
                    "Instead, Section 80TTB applies — up to ₹50,000 on "
                    "interest from deposits."
                ),
                "section": "80TTA"
            }
        cap = 10000
        allowed = min(amount, cap)
        return {
            "eligible": True,
            "allowed_amount": allowed,
            "reason": (
                "Section 80TTA: Interest on savings bank account "
                f"up to ₹{cap:,} is deductible."
            ),
            "section": "80TTA"
        }

    # 80TTB — Senior citizen deposit interest
    if section_upper == "80TTB":
        if age < 60:
            return {
                "eligible": False,
                "allowed_amount": 0,
                "reason": (
                    "Section 80TTB is available only for senior citizens "
                    "(age 60 and above)."
                ),
                "section": "80TTB"
            }
        cap = 50000
        allowed = min(amount, cap)
        return {
            "eligible": True,
            "allowed_amount": allowed,
            "reason": (
                "Section 80TTB: Interest income from deposits for "
                f"senior citizens — up to ₹{cap:,}."
            ),
            "section": "80TTB"
        }

    # 80CCD(1B) — NPS self-contribution (additional ₹50,000)
    if section_upper in ("80CCD", "80CCD(1B)"):
        if not has_nps:
            return {
                "eligible": False,
                "allowed_amount": 0,
                "reason": (
                    "Section 80CCD(1B) is for additional self-contribution "
                    "to National Pension System (NPS). "
                    "You indicated you do not have an NPS account."
                ),
                "section": "80CCD(1B)"
            }
        cap = 50000
        allowed = min(amount, cap)
        return {
            "eligible": True,
            "allowed_amount": allowed,
            "reason": (
                "Section 80CCD(1B): Additional NPS self-contribution "
                f"deduction up to ₹{cap:,} over and above Section 80C."
            ),
            "section": "80CCD(1B)"
        }

    # Unknown section
    return {
        "eligible": "Unknown",
        "allowed_amount": 0,
        "reason": (
            f"Section {section_upper} could not be evaluated automatically. "
            "Please consult the applicable provisions of the Income-tax Act "
            "or use the AI Assistant for more information."
        ),
        "section": section_upper
    }


# ============================================================
# E. SIMULATION VALIDATION DECISION TREE
# ============================================================

def validate_simulation_step(step_number, step_data):
    """
    Decision Tree for validating each step of the ITR simulation.

    Returns:
        dict with valid (True/False), errors (list), warnings (list)
    """

    errors = []
    warnings = []

    # --------------------------------------------------------
    # Step 1 — Personal Information
    # --------------------------------------------------------

    if step_number == 1:

        name = step_data.get("name", "").strip()
        pan = step_data.get("pan", "").strip().upper()
        dob = step_data.get("dob", "").strip()
        gender = step_data.get("gender", "").strip()
        mobile = step_data.get("mobile", "").strip()
        email = step_data.get("email", "").strip()

        if not name:
            errors.append("Full name is required.")

        if not dob:
            errors.append("Date of birth is required.")

        if not gender:
            errors.append("Gender is required.")

        if pan and (len(pan) != 10 or not _is_valid_pan_format(pan)):
            warnings.append(
                "PAN format appears incorrect. "
                "PAN should be 10 characters (e.g. ABCDE1234F). "
                "This is a simulation so PAN is not verified officially."
            )

        if mobile and not mobile.isdigit():
            errors.append("Mobile number should contain digits only.")

        if email and "@" not in email:
            errors.append("Email address appears invalid.")

    # --------------------------------------------------------
    # Step 2 — Residential Status
    # --------------------------------------------------------

    elif step_number == 2:

        days = step_data.get("days_in_india", 0)

        try:
            days = int(days)
        except (ValueError, TypeError):
            errors.append("Days in India must be a valid number.")
            days = 0

        if days < 0 or days > 366:
            errors.append("Days in India must be between 0 and 366.")

        if days == 0:
            warnings.append(
                "You entered 0 days in India. "
                "This will likely result in Non-Resident status."
            )

    # --------------------------------------------------------
    # Step 3 — Income Details
    # --------------------------------------------------------

    elif step_number == 3:

        income_sources = step_data.get("income_sources", [])

        if not income_sources:
            errors.append(
                "Please select at least one income source."
            )

        # Salary selected → Form 16 data expected
        if "salary" in income_sources:
            salary = step_data.get("salary_amount", 0)
            try:
                salary = float(salary)
            except (ValueError, TypeError):
                salary = 0

            if salary <= 0:
                warnings.append(
                    "You selected salary income but entered ₹0. "
                    "Please enter your salary amount."
                )

        # House property selected → property data expected
        if "house_property" in income_sources:
            hp_data = step_data.get("house_property_income", None)
            if hp_data is None:
                warnings.append(
                    "You selected house property income. "
                    "Please provide property-related details."
                )

        # Capital gains selected → gains data expected
        if "capital_gains" in income_sources:
            cg_data = step_data.get("capital_gains_amount", 0)
            if not cg_data:
                warnings.append(
                    "You selected capital gains. "
                    "Please provide asset sale details."
                )

    # --------------------------------------------------------
    # Step 4 — Deductions
    # --------------------------------------------------------

    elif step_number == 4:

        regime = step_data.get("regime", "new")
        deductions = step_data.get("deductions", {})

        if regime == "new" and deductions:
            warnings.append(
                "Under the New Tax Regime, most Chapter VI-A "
                "deductions (80C, 80D, etc.) are not available. "
                "Only certain deductions like 80CCD(2) are permitted."
            )

        total_deductions = sum(
            float(v) for v in deductions.values()
            if isinstance(v, (int, float, str))
            and str(v).replace(".", "").isdigit()
        )

        if total_deductions < 0:
            errors.append("Deduction amounts cannot be negative.")

    # --------------------------------------------------------
    # Unknown step
    # --------------------------------------------------------

    else:

        warnings.append(
            f"Validation for step {step_number} is not yet configured."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _is_valid_pan_format(pan):
    """
    Basic PAN format check.
    Format: AAAAA9999A (5 letters, 4 digits, 1 letter)
    """

    if len(pan) != 10:
        return False

    return (
        pan[:5].isalpha()
        and pan[5:9].isdigit()
        and pan[9].isalpha()
    )


# ============================================================
# F. PRACTICE SCENARIO CLASSIFICATION
# ============================================================

def classify_practice_scenario(
    income_sources,
    total_income,
    has_deductions,
    has_capital_gains,
    has_house_property,
    has_foreign_income
):
    """
    Decision Tree to classify a practice scenario as:
    - Beginner
    - Intermediate
    - Advanced

    Returns:
        dict with level, label, description, and recommended_form
    """

    complexity_score = 0

    # More income sources = more complexity
    complexity_score += len(income_sources) * 10

    # Capital gains add complexity
    if has_capital_gains:
        complexity_score += 30

    # Multiple sources of house property add complexity
    if has_house_property:
        complexity_score += 15

    # Foreign income is advanced
    if has_foreign_income:
        complexity_score += 50

    # High income adds complexity
    if total_income > 1000000:
        complexity_score += 10
    if total_income > 5000000:
        complexity_score += 20

    # Deductions add some complexity
    if has_deductions:
        complexity_score += 10

    # --------------------------------------------------------
    # Classify
    # --------------------------------------------------------

    if complexity_score <= 20:
        return {
            "level": "beginner",
            "label": "Beginner",
            "description": (
                "Simple salary-only or single-source income. "
                "Suitable for first-time learners."
            ),
            "icon": "🟢",
            "recommended_form": "ITR-1 (Sahaj)"
        }

    elif complexity_score <= 60:
        return {
            "level": "intermediate",
            "label": "Intermediate",
            "description": (
                "Multiple income sources with deductions. "
                "Suitable for learners with some ITR knowledge."
            ),
            "icon": "🟡",
            "recommended_form": "ITR-2"
        }

    else:
        return {
            "level": "advanced",
            "label": "Advanced",
            "description": (
                "Complex scenario with capital gains, foreign income, "
                "or business income. Suitable for advanced learners."
            ),
            "icon": "🔴",
            "recommended_form": "ITR-2 or ITR-3"
        }
