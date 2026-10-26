"""
ITR Learn & Simulate
logic/validation.py

Simulation and form validation helpers.

Works alongside decision_tree.py for step-by-step
simulation validation and general input checking.

Educational simulation only.
"""

import re


# ============================================================
# GENERAL FIELD VALIDATORS
# ============================================================

def validate_required(value, field_name):
    """Check that a field is not empty."""
    if not value or str(value).strip() == "":
        return f"{field_name} is required."
    return None


def validate_positive_number(value, field_name):
    """Check that a value is a non-negative number."""
    try:
        num = float(value)
        if num < 0:
            return f"{field_name} cannot be negative."
        return None
    except (ValueError, TypeError):
        return f"{field_name} must be a valid number."


def validate_pan(pan):
    """
    Validate PAN format.
    Format: AAAAA9999A
    """
    if not pan:
        return None  # Optional field

    pan = pan.strip().upper()
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"

    if not re.match(pattern, pan):
        return (
            "PAN format is invalid. "
            "Expected format: ABCDE1234F "
            "(5 letters, 4 digits, 1 letter)."
        )
    return None


def validate_email(email):
    """Basic email format check."""
    if not email:
        return None  # Optional

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(pattern, email.strip()):
        return "Email address format is invalid."
    return None


def validate_mobile(mobile):
    """Indian mobile number format check."""
    if not mobile:
        return None  # Optional

    mobile = mobile.strip()
    if not re.match(r"^[6-9]\d{9}$", mobile):
        return (
            "Mobile number should be 10 digits "
            "starting with 6, 7, 8, or 9."
        )
    return None


def validate_date(date_str, field_name="Date"):
    """Check that a date string is in YYYY-MM-DD format."""
    if not date_str:
        return f"{field_name} is required."

    try:
        from datetime import datetime
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return None
    except ValueError:
        return f"{field_name} must be in YYYY-MM-DD format."


# ============================================================
# INCOME VALIDATION
# ============================================================

def validate_income_fields(income_data):
    """
    Validate all income-related fields in a simulation step.

    Args:
        income_data: dict with income field names and values

    Returns:
        dict with errors and warnings lists
    """

    errors = []
    warnings = []

    fields_to_check = [
        "salary", "pension", "house_property",
        "other_sources", "capital_gains", "agricultural_income"
    ]

    for field in fields_to_check:

        value = income_data.get(field, 0)

        if value == "" or value is None:
            income_data[field] = 0
            continue

        err = validate_positive_number(value, field.replace("_", " ").title())
        if err:
            errors.append(err)

    total = sum(
        float(income_data.get(f, 0) or 0)
        for f in fields_to_check
    )

    if total == 0:
        warnings.append(
            "All income amounts are zero. "
            "Please enter at least one income amount."
        )
    elif total > 100000000:  # ₹10 crore
        warnings.append(
            "Total income appears very high (above ₹10 crore). "
            "Please verify the entered values."
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0
    }


# ============================================================
# DEDUCTION VALIDATION
# ============================================================

def validate_deduction_fields(deduction_data, regime):
    """
    Validate deduction fields.

    Args:
        deduction_data: dict with deduction amounts
        regime: 'old' or 'new'

    Returns:
        dict with errors and warnings lists
    """

    errors = []
    warnings = []

    deduction_fields = [
        "deduction_80c",
        "deduction_80ccd",
        "deduction_80d",
        "deduction_80e",
        "deduction_80g",
        "deduction_80tta"
    ]

    for field in deduction_fields:

        value = deduction_data.get(field, 0)

        if value == "" or value is None:
            continue

        err = validate_positive_number(
            value,
            field.replace("deduction_", "Section ").upper()
        )
        if err:
            errors.append(err)

    # New regime warning
    if regime == "new":

        non_zero = any(
            float(deduction_data.get(f, 0) or 0) > 0
            for f in deduction_fields
        )

        if non_zero:
            warnings.append(
                "Under the New Tax Regime, most Chapter VI-A "
                "deductions are not available. "
                "These values will be set to zero in the calculation."
            )

    # 80C limit warning
    dc_80c = float(deduction_data.get("deduction_80c", 0) or 0)
    if dc_80c > 150000:
        warnings.append(
            f"Section 80C amount ₹{dc_80c:,.0f} exceeds "
            "the maximum limit of ₹1,50,000. "
            "Only ₹1,50,000 will be considered."
        )

    # 80TTA limit warning
    dc_tta = float(deduction_data.get("deduction_80tta", 0) or 0)
    if dc_tta > 10000:
        warnings.append(
            f"Section 80TTA amount ₹{dc_tta:,.0f} exceeds "
            "the maximum limit of ₹10,000. "
            "Only ₹10,000 will be considered."
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0
    }


# ============================================================
# SIMULATION COMPLETENESS CHECK
# ============================================================

def check_simulation_completeness(simulation_data):
    """
    Check whether all required simulation steps have been completed.

    Args:
        simulation_data: dict with all steps' data

    Returns:
        dict with complete (True/False), missing_steps list
    """

    required_keys = [
        "personal",
        "residential_status",
        "income",
        "deductions",
        "regime"
    ]

    missing = []

    for key in required_keys:
        if key not in simulation_data or not simulation_data[key]:
            missing.append(key.replace("_", " ").title())

    return {
        "complete": len(missing) == 0,
        "missing_steps": missing
    }
