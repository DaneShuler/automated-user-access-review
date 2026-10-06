import json
from datetime import date

from src.risk_engine import score_human, score_nhi


# ---------------------------------------------------------
# Test Configuration
# ---------------------------------------------------------

# Load the same risk rules used by the main program.
with open("config.json", "r", encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)


# Use a fixed date so test results stay consistent
# regardless of when the tests are run.
TEST_DATE = date(2026, 10, 6)


# ---------------------------------------------------------
# Employee Access Tests
# ---------------------------------------------------------

def test_terminated_employee_with_active_access_is_critical():
    """
    Verify that a terminated employee who still has active,
    high-risk, SOX-controlled access is classified as Critical.
    """

    employee_access = {
        "employee_status": "Terminated",
        "account_status": "Active",
        "risk_level": "High",
        "sox": "Yes",
        "last_login": "2026-09-01"
    }

    score, risk_level, reasons = score_human(
        employee_access,
        CONFIG,
        TEST_DATE
    )

    assert risk_level == "CRITICAL"

    assert (
        "terminated employee retains active access"
        in reasons
    )


# ---------------------------------------------------------
# Service Account / Non-Human Account Tests
# ---------------------------------------------------------

def test_service_account_with_terminated_owner_is_critical():
    """
    Verify that a privileged production service account
    with a terminated owner and poor credential hygiene
    is classified as Critical.
    """

    service_account = {
        "owner_status": "Terminated",
        "privilege_level": "High",
        "environment": "Production",
        "credential_age_days": 380,
        "rotation_required": "Yes",
        "last_used": "2026-06-01"
    }

    score, risk_level, reasons = score_nhi(
        service_account,
        CONFIG,
        TEST_DATE
    )

    assert risk_level == "CRITICAL"

    assert (
        "terminated or missing owner"
        in reasons
    )

# ---------------------------------------------------------
# Additional Risk Scoring Tests
# ---------------------------------------------------------

def test_normal_employee_access_stays_normal():
    """
    Verify that normal employee access without any major
    warning signs is not incorrectly classified as risky.
    """

    employee_access = {
        "employee_status": "Active",
        "account_status": "Active",
        "risk_level": "Low",
        "sox": "No",
        "last_login": "2026-10-01"
    }

    score, risk_level, reasons = score_human(
        employee_access,
        CONFIG,
        TEST_DATE
    )

    assert score == 0
    assert risk_level == "NORMAL"
    assert reasons == []


def test_stale_employee_access_is_identified():
    """
    Verify that an account that has not been used recently
    receives the configured stale-login risk.
    """

    employee_access = {
        "employee_status": "Active",
        "account_status": "Active",
        "risk_level": "Low",
        "sox": "No",
        "last_login": "2026-06-01"
    }

    score, risk_level, reasons = score_human(
        employee_access,
        CONFIG,
        TEST_DATE
    )

    assert score > 0

    assert any(
        "stale login" in reason
        for reason in reasons
    )


def test_old_service_account_credentials_are_identified():
    """
    Verify that old service account credentials are
    recognized as a risk.
    """

    service_account = {
        "owner_status": "Active",
        "privilege_level": "Low",
        "environment": "Development",
        "credential_age_days": 400,
        "rotation_required": "No",
        "last_used": "2026-10-01"
    }

    score, risk_level, reasons = score_nhi(
        service_account,
        CONFIG,
        TEST_DATE
    )

    assert score > 0

    assert any(
        "credential age" in reason
        for reason in reasons
    )