from pathlib import Path
from datetime import datetime, timezone

import pandas as pd


VALID_DECISIONS = {
    "CERTIFY",
    "REVOKE",
    "MODIFY",
    "ESCALATE"
}


def record_decision(
    campaign_path,
    audit_path,
    remediation_path,
    item_id,
    reviewer,
    decision,
    justification,
    enforce_assigned_reviewer=True
):
    """
    Records a review decision for an access review item.

    The function:
    1. Validates the requested decision.
    2. Makes sure a justification was provided.
    3. Finds the requested item in the review campaign.
    4. Makes sure the item has not already been reviewed.
    5. Verifies that the person completing the review is the assigned reviewer.
    6. Records the decision in the campaign.
    7. Adds the decision to the audit log.
    8. Creates a remediation item when additional action is required.
    """

    # Clean up values provided from the command line.
    decision = decision.strip().upper()
    reviewer = reviewer.strip()
    justification = justification.strip()

    # ---------------------------------------------------------
    # Validate the review decision
    # ---------------------------------------------------------

    if decision not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision '{decision}'. "
            f"Valid decisions are: {', '.join(sorted(VALID_DECISIONS))}"
        )

    if not justification:
        raise ValueError(
            "A reviewer justification is required."
        )

    if not reviewer:
        raise ValueError(
            "A reviewer name is required."
        )

    # ---------------------------------------------------------
    # Load the current review campaign
    # ---------------------------------------------------------

    campaign_path = Path(campaign_path)

    if not campaign_path.exists():
        raise ValueError(
            f"Review campaign could not be found: {campaign_path}"
        )

    campaign = pd.read_csv(campaign_path).fillna("")

    matches = campaign.index[
        campaign["item_id"] == item_id
    ].tolist()

    if not matches:
        raise ValueError(
            f"Unknown review item: {item_id}"
        )

    index = matches[0]
    item = campaign.loc[index].copy()

    # ---------------------------------------------------------
    # Prevent an item from being reviewed more than once
    # ---------------------------------------------------------

    existing_decision = str(item.get("decision", "")).strip()

    if existing_decision:
        raise ValueError(
            f"{item_id} has already been reviewed with the decision "
            f"'{existing_decision}'."
        )

    # ---------------------------------------------------------
    # Verify the assigned reviewer
    # ---------------------------------------------------------

    assigned_reviewer = str(
        item.get("reviewer", "")
    ).strip()

    if enforce_assigned_reviewer:
        if reviewer.casefold() != assigned_reviewer.casefold():
            raise ValueError(
                f"{reviewer} is not authorized to review {item_id}. "
                f"This item is assigned to {assigned_reviewer}."
            )

    # ---------------------------------------------------------
    # Record the decision in the review campaign
    # ---------------------------------------------------------

    campaign.at[index, "decision"] = decision
    campaign.at[index, "justification"] = justification

    campaign.to_csv(
        campaign_path,
        index=False
    )

    # ---------------------------------------------------------
    # Create the audit record
    # ---------------------------------------------------------

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "item_id": item_id,
        "identity_type": item["identity_type"],
        "identity_id": item["identity_id"],
        "identity_name": item["identity_name"],
        "application": item["application"],
        "access": item["access"],

        # Keep these separate so the audit trail shows both
        # who was assigned the review and who completed it.
        "assigned_reviewer": assigned_reviewer,
        "reviewed_by": reviewer,

        "decision": decision,
        "justification": justification,
        "risk_score": item["risk_score"],
        "risk_level": item["risk_level"],
        "risk_reasons": item["risk_reasons"]
    }

    # ---------------------------------------------------------
    # Add the decision to the audit log
    # ---------------------------------------------------------

    audit_path = Path(audit_path)

    pd.DataFrame([event]).to_csv(
        audit_path,
        mode="a",
        header=not audit_path.exists(),
        index=False
    )

    # ---------------------------------------------------------
    # Create remediation work when necessary
    # ---------------------------------------------------------

    if decision in {
        "REVOKE",
        "MODIFY",
        "ESCALATE"
    }:
        remediation_path = Path(remediation_path)

        remediation_event = {
            **event,
            "status": "PENDING",
            "dry_run": True
        }

        pd.DataFrame([remediation_event]).to_csv(
            remediation_path,
            mode="a",
            header=not remediation_path.exists(),
            index=False
        )

    return event