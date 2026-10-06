from datetime import datetime

import pandas as pd


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def days_since(date_value, today):
    """
    Calculates how many days have passed since a given date.

    Returns None if no date was provided.
    """

    if pd.isna(date_value) or date_value == "":
        return None

    parsed_date = pd.to_datetime(date_value).date()

    return (today - parsed_date).days


def get_risk_level(score, thresholds):
    """
    Converts a numeric risk score into a readable risk level.

    The thresholds are stored in config.json so they can be
    changed without modifying the risk engine itself.
    """

    if score >= thresholds["critical"]:
        return "CRITICAL"

    if score >= thresholds["high"]:
        return "HIGH"

    if score >= thresholds["medium"]:
        return "MEDIUM"

    return "NORMAL"


# ---------------------------------------------------------
# Employee Access Risk Scoring
# ---------------------------------------------------------

def score_human(row, config, today=None):
    """
    Calculates the risk score for an employee access record.

    The function looks for situations such as:
    - A terminated employee who still has active access
    - Critical or high-risk permissions
    - SOX-controlled access
    - Access that has not been used recently

    It returns:
    - The numeric risk score
    - The risk level
    - A list explaining why points were added
    """

    if today is None:
        today = datetime.now().date()

    rules = config["human_rules"]

    score = 0
    reasons = []

    # -----------------------------------------------------
    # Terminated Employee With Active Access
    # -----------------------------------------------------

    employee_status = str(
        row.get("employee_status", "")
    ).lower()

    account_status = str(
        row.get("account_status", "")
    ).lower()

    if (
        employee_status == "terminated"
        and account_status == "active"
    ):
        score += rules["terminated_active_access"]

        reasons.append(
            "terminated employee retains active access"
        )

    # -----------------------------------------------------
    # Access Risk Level
    # -----------------------------------------------------

    access_risk = str(
        row.get("risk_level", "")
    ).lower()

    if access_risk == "critical":
        score += rules["critical_access"]

        reasons.append(
            "critical entitlement"
        )

    elif access_risk == "high":
        score += rules["high_access"]

        reasons.append(
            "high-risk entitlement"
        )

    # -----------------------------------------------------
    # SOX-Controlled Access
    # -----------------------------------------------------

    sox_access = str(
        row.get("sox", "")
    ).lower()

    if sox_access in {"yes", "true", "1"}:
        score += rules["sox_access"]

        reasons.append(
            "SOX-controlled access"
        )

    # -----------------------------------------------------
    # Stale Access
    # -----------------------------------------------------

    days_since_login = days_since(
        row.get("last_login"),
        today
    )

    if (
        days_since_login is not None
        and days_since_login > rules["stale_login_days"]
    ):
        score += rules["stale_login_score"]

        reasons.append(
            f"stale login ({days_since_login} days)"
        )

    # -----------------------------------------------------
    # Determine Final Risk Level
    # -----------------------------------------------------

    risk_level = get_risk_level(
        score,
        config["risk_thresholds"]
    )

    return score, risk_level, reasons


# ---------------------------------------------------------
# Service Account / Non-Human Account Risk Scoring
# ---------------------------------------------------------

def score_nhi(row, config, today=None):
    """
    Calculates the risk score for a service account or
    other non-human account.

    The function looks for situations such as:
    - A terminated or missing account owner
    - Critical or high privileges
    - Production usage
    - Old credentials
    - Credentials that require rotation
    - Accounts that have not been used recently

    It returns:
    - The numeric risk score
    - The risk level
    - A list explaining why points were added
    """

    if today is None:
        today = datetime.now().date()

    rules = config["nhi_rules"]

    score = 0
    reasons = []

    # -----------------------------------------------------
    # Account Ownership
    # -----------------------------------------------------

    owner_status = str(
        row.get("owner_status", "")
    ).lower()

    if owner_status in {
        "terminated",
        "missing",
        "unknown"
    }:
        score += rules["terminated_owner"]

        reasons.append(
            "terminated or missing owner"
        )

    # -----------------------------------------------------
    # Privilege Level
    # -----------------------------------------------------

    privilege_level = str(
        row.get("privilege_level", "")
    ).lower()

    if privilege_level == "critical":
        score += rules["critical_privilege"]

        reasons.append(
            "critical privilege"
        )

    elif privilege_level == "high":
        score += rules["high_privilege"]

        reasons.append(
            "high privilege"
        )

    # -----------------------------------------------------
    # Production Environment
    # -----------------------------------------------------

    environment = str(
        row.get("environment", "")
    ).lower()

    if environment == "production":
        score += rules["production"]

        reasons.append(
            "production identity"
        )

    # -----------------------------------------------------
    # Credential Age
    # -----------------------------------------------------

    credential_age = int(
        row.get("credential_age_days", 0) or 0
    )

    if credential_age > rules["credential_age_days"]:
        score += rules["old_credential_score"]

        reasons.append(
            f"credential age {credential_age} days"
        )

    # -----------------------------------------------------
    # Credential Rotation
    # -----------------------------------------------------

    rotation_required = str(
        row.get("rotation_required", "")
    ).lower()

    if rotation_required in {
        "yes",
        "true",
        "1"
    }:
        score += rules["rotation_required"]

        reasons.append(
            "credential rotation required"
        )

    # -----------------------------------------------------
    # Stale Usage
    # -----------------------------------------------------

    days_since_use = days_since(
        row.get("last_used"),
        today
    )

    if (
        days_since_use is not None
        and days_since_use > rules["stale_usage_days"]
    ):
        score += rules["stale_usage_score"]

        reasons.append(
            f"stale usage ({days_since_use} days)"
        )

    # -----------------------------------------------------
    # Determine Final Risk Level
    # -----------------------------------------------------

    risk_level = get_risk_level(
        score,
        config["risk_thresholds"]
    )

    return score, risk_level, reasons