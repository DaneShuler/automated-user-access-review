import pandas as pd
from .risk_engine import score_human, score_nhi


def build_campaign(employees, access, nhi, applications, config):
    # Rename employee fields so they are easier to distinguish
    # after combining the different data sources.
    emp = employees.rename(columns={
        "status": "employee_status",
        "name": "employee_name",
        "manager": "manager_name"
    })

    # Combine employee information, access information,
    # and application information.
    human = access.merge(
        emp[
            [
                "employee_id",
                "employee_name",
                "department",
                "manager_name",
                "employee_status"
            ]
        ],
        on="employee_id",
        how="left"
    ).merge(
        applications[
            [
                "application",
                "owner",
                "criticality",
                "review_frequency_days"
            ]
        ],
        on="application",
        how="left"
    )

    rows = []

    # ---------------------------------------------------------
    # Employee Access Reviews
    # ---------------------------------------------------------

    for _, r in human.iterrows():
        score, level, reasons = score_human(r, config)

        iam_reviewer = config["review_settings"]["iam_reviewer"]

        # Critical findings go to IAM.
        if level == "CRITICAL":
            reviewer = iam_reviewer

        # High-risk or SOX-related access goes to the
        # application owner.
        elif str(r.get("sox", "")).lower() == "yes" or level == "HIGH":
            reviewer = r["owner"]

        # Normal and medium-risk access goes to the
        # employee's manager.
        else:
            reviewer = r["manager_name"]

        # A terminated employee with active access should
        # have that access revoked.
        recommendation = (
            "REVOKE"
            if "terminated employee retains active access" in reasons
            else "REVIEW"
        )

        rows.append({
            "item_id": f"H-{r['account_id']}",
            "identity_type": "HUMAN",
            "identity_id": r["employee_id"],
            "identity_name": r["employee_name"],
            "application": r["application"],
            "access": r["entitlement"],
            "reviewer": reviewer,
            "risk_score": score,
            "risk_level": level,
            "risk_reasons": "; ".join(reasons) if reasons else "none",
            "recommendation": recommendation,
            "decision": "",
            "justification": ""
        })

    # Create a quick lookup for application information.
    lookup = applications.set_index("application").to_dict("index")

    # ---------------------------------------------------------
    # Service Account / Non-Human Account Reviews
    # ---------------------------------------------------------

    for _, r in nhi.iterrows():
        score, level, reasons = score_nhi(r, config)

        app = r.get(
            "application",
            r.get("resource", "Unknown")
        )

        meta = lookup.get(app, {})

        iam_reviewer = config["review_settings"]["iam_reviewer"]

        # Critical service/non-human accounts go to IAM.
        if level == "CRITICAL":
            reviewer = iam_reviewer

        # Otherwise use the application owner.
        # If there isn't one, fall back to the account owner.
        else:
            reviewer = meta.get("owner") or r.get("owner_name")

        # A service account with a terminated or missing owner
        # should be investigated before making a change that
        # could potentially break an application or service.
        recommendation = (
            "ESCALATE"
            if "terminated or missing owner" in reasons
            else "REVIEW"
        )

        rows.append({
            "item_id": f"N-{r['nhi_id']}",
            "identity_type": "NHI",
            "identity_id": r["nhi_id"],
            "identity_name": r["name"],
            "application": app,
            "access": r["privilege_level"],
            "reviewer": reviewer,
            "risk_score": score,
            "risk_level": level,
            "risk_reasons": "; ".join(reasons) if reasons else "none",
            "recommendation": recommendation,
            "decision": "",
            "justification": ""
        })

    # ---------------------------------------------------------
    # Sort the final campaign by risk
    # ---------------------------------------------------------

    result = pd.DataFrame(rows)

    rank = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "NORMAL": 3
    }

    if not result.empty:
        result["_rank"] = result["risk_level"].map(rank)

        result = result.sort_values(
            ["_rank", "risk_score"],
            ascending=[True, False]
        ).drop(columns="_rank")

    return result