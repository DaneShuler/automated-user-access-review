from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

ROOT = Path(__file__).parent
DEMO = ROOT / "demo"

CAMPAIGN_FILE = DEMO / "review_campaign.csv"
AUDIT_FILE = DEMO / "audit_log.csv"
REMEDIATION_FILE = DEMO / "remediation_queue.csv"


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="User Access Review",
    layout="wide"
)


# ---------------------------------------------------------
# Data Loading
# ---------------------------------------------------------

def load_csv(path):
    """
    Load one of the synthetic baseline demo files.
    """

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path).fillna("")


def initialize_demo():
    """
    Give each Streamlit session its own working copy of
    the campaign, audit history, and remediation queue.

    Changes made through the dashboard affect only the
    current visitor's session.
    """

    if "campaign" not in st.session_state:
        st.session_state.campaign = load_csv(CAMPAIGN_FILE)

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = load_csv(AUDIT_FILE)

    if "remediation_queue" not in st.session_state:
        st.session_state.remediation_queue = load_csv(
            REMEDIATION_FILE
        )


def reset_demo():
    """
    Restore the current session to the original synthetic
    demonstration data.
    """

    st.session_state.campaign = load_csv(CAMPAIGN_FILE)
    st.session_state.audit_log = load_csv(AUDIT_FILE)
    st.session_state.remediation_queue = load_csv(
        REMEDIATION_FILE
    )


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def risk_icon(risk_level):
    icons = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "NORMAL": "🟢"
    }

    return icons.get(
        str(risk_level).upper(),
        "⚪"
    )


def decision_icon(decision):
    icons = {
        "CERTIFY": "✓",
        "REVOKE": "✕",
        "MODIFY": "✎",
        "ESCALATE": "!"
    }

    return icons.get(
        str(decision).upper(),
        ""
    )


def format_identity_type(identity_type):
    if identity_type == "NHI":
        return "Service / Non-Human Identity"

    if identity_type == "HUMAN":
        return "Employee"

    return identity_type


def parse_risk_reasons(value):
    if not value:
        return []

    if str(value).lower() == "none":
        return []

    return [
        reason.strip()
        for reason in str(value).split(";")
        if reason.strip()
    ]


def record_demo_decision(
    item_id,
    reviewer,
    decision,
    justification
):
    """
    Record a review decision in the current Streamlit
    session only.

    Nothing is written to the repository or to an
    external identity system.
    """

    campaign = st.session_state.campaign.copy()

    matches = campaign.index[
        campaign["item_id"] == item_id
    ].tolist()

    if not matches:
        raise ValueError(
            f"Unknown review item: {item_id}"
        )

    index = matches[0]
    item = campaign.loc[index].copy()

    existing_decision = str(
        item.get("decision", "")
    ).strip()

    if existing_decision:
        raise ValueError(
            f"{item_id} has already been reviewed with "
            f"the decision '{existing_decision}'."
        )

    assigned_reviewer = str(
        item.get("reviewer", "")
    ).strip()

    if reviewer.strip() != assigned_reviewer:
        raise ValueError(
            f"{reviewer} is not authorized to review "
            f"{item_id}. This item is assigned to "
            f"{assigned_reviewer}."
        )

    decision = decision.upper().strip()

    valid_decisions = {
        "CERTIFY",
        "REVOKE",
        "MODIFY",
        "ESCALATE"
    }

    if decision not in valid_decisions:
        raise ValueError(
            "Invalid review decision."
        )

    if not justification.strip():
        raise ValueError(
            "Reviewer justification is required."
        )

    # Update this visitor's campaign.
    campaign.at[index, "decision"] = decision
    campaign.at[index, "justification"] = justification

    st.session_state.campaign = campaign

    # Create the audit event.
    timestamp = pd.Timestamp.now(tz="UTC").isoformat()

    event = {
        "timestamp_utc": timestamp,
        "item_id": item_id,
        "identity_type": item.get(
            "identity_type",
            ""
        ),
        "identity_id": item.get(
            "identity_id",
            ""
        ),
        "identity_name": item.get(
            "identity_name",
            ""
        ),
        "application": item.get(
            "application",
            ""
        ),
        "access": item.get(
            "access",
            ""
        ),
        "assigned_reviewer": assigned_reviewer,
        "reviewed_by": reviewer.strip(),
        "decision": decision,
        "justification": justification.strip(),
        "risk_score": item.get(
            "risk_score",
            ""
        ),
        "risk_level": item.get(
            "risk_level",
            ""
        ),
        "risk_reasons": item.get(
            "risk_reasons",
            ""
        )
    }

    audit = st.session_state.audit_log.copy()

    audit = pd.concat(
        [
            audit,
            pd.DataFrame([event])
        ],
        ignore_index=True
    )

    st.session_state.audit_log = audit

    # Only decisions requiring further action enter
    # the remediation queue.
    if decision in {
        "REVOKE",
        "MODIFY",
        "ESCALATE"
    }:

        remediation_event = {
            **event,
            "status": "PENDING",
            "dry_run": True
        }

        remediation = (
            st.session_state.remediation_queue.copy()
        )

        remediation = pd.concat(
            [
                remediation,
                pd.DataFrame(
                    [remediation_event]
                )
            ],
            ignore_index=True
        )

        st.session_state.remediation_queue = remediation

    return event


# ---------------------------------------------------------
# Initialize Session
# ---------------------------------------------------------

initialize_demo()

campaign = st.session_state.campaign
audit_log = st.session_state.audit_log
remediation_queue = st.session_state.remediation_queue


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Demo Environment")

    st.caption(
        "This dashboard uses synthetic identity and access "
        "data. Changes made here affect only your current "
        "demo session."
    )

    st.divider()

    st.write(
        "Use Reset Demo to restore the campaign, audit "
        "history, and remediation queue to their original "
        "example state."
    )

    confirm_reset = st.checkbox(
        "Confirm reset"
    )

    if st.button(
        "Reset Demo",
        disabled=not confirm_reset,
        use_container_width=True
    ):
        reset_demo()
        st.rerun()


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("User Access Review")

st.caption(
    "Risk-based review of employee and service account access."
)

st.info(
    "**Demo Environment:** All identities, applications, "
    "access records, and review data are synthetic. "
    "This application does not connect to or modify any "
    "production identity systems."
)


# ---------------------------------------------------------
# Campaign Check
# ---------------------------------------------------------

if campaign.empty:

    st.warning(
        "No demonstration campaign was found."
    )

    st.stop()


# ---------------------------------------------------------
# Campaign Statistics
# ---------------------------------------------------------

total_reviews = len(campaign)

critical_reviews = (
    campaign["risk_level"] == "CRITICAL"
).sum()

high_reviews = (
    campaign["risk_level"] == "HIGH"
).sum()

medium_reviews = (
    campaign["risk_level"] == "MEDIUM"
).sum()

completed_reviews = (
    campaign["decision"] != ""
).sum()

pending_reviews = (
    campaign["decision"] == ""
).sum()


st.subheader("Campaign Overview")

metric1, metric2, metric3, metric4, metric5, metric6 = (
    st.columns(6)
)

metric1.metric(
    "Total Reviews",
    total_reviews
)

metric2.metric(
    "Critical",
    critical_reviews
)

metric3.metric(
    "High",
    high_reviews
)

metric4.metric(
    "Medium",
    medium_reviews
)

metric5.metric(
    "Completed",
    completed_reviews
)

metric6.metric(
    "Pending",
    pending_reviews
)


# ---------------------------------------------------------
# Campaign Progress
# ---------------------------------------------------------

if total_reviews > 0:

    completion_percentage = (
        completed_reviews / total_reviews
    )

    st.progress(
        completion_percentage,
        text=(
            f"Campaign Progress: "
            f"{completed_reviews} of {total_reviews} "
            f"reviews completed "
            f"({completion_percentage:.1%})"
        )
    )


st.divider()


# ---------------------------------------------------------
# Main Tabs
# ---------------------------------------------------------

reviews_tab, remediation_tab, audit_tab = st.tabs(
    [
        "Access Reviews",
        "Remediation Queue",
        "Audit History"
    ]
)


# =========================================================
# ACCESS REVIEWS
# =========================================================

with reviews_tab:

    st.subheader("Access Reviews")

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    filter1, filter2, filter3, filter4, filter5 = (
        st.columns(5)
    )

    selected_risk = filter1.selectbox(
        "Risk Level",
        [
            "All",
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "NORMAL"
        ]
    )

    application_options = [
        "All"
    ] + sorted(
        campaign["application"]
        .astype(str)
        .unique()
        .tolist()
    )

    selected_application = filter2.selectbox(
        "Application",
        application_options
    )

    selected_identity = filter3.selectbox(
        "Identity Type",
        [
            "All",
            "HUMAN",
            "NHI"
        ]
    )

    reviewer_options = [
        "All"
    ] + sorted(
        campaign["reviewer"]
        .astype(str)
        .unique()
        .tolist()
    )

    selected_reviewer = filter4.selectbox(
        "Reviewer",
        reviewer_options
    )

    selected_status = filter5.selectbox(
        "Review Status",
        [
            "All",
            "Pending",
            "Completed"
        ]
    )


    # -----------------------------------------------------
    # Apply Filters
    # -----------------------------------------------------

    filtered_campaign = campaign.copy()

    if selected_risk != "All":
        filtered_campaign = filtered_campaign[
            filtered_campaign["risk_level"]
            == selected_risk
        ]

    if selected_application != "All":
        filtered_campaign = filtered_campaign[
            filtered_campaign["application"]
            == selected_application
        ]

    if selected_identity != "All":
        filtered_campaign = filtered_campaign[
            filtered_campaign["identity_type"]
            == selected_identity
        ]

    if selected_reviewer != "All":
        filtered_campaign = filtered_campaign[
            filtered_campaign["reviewer"]
            == selected_reviewer
        ]

    if selected_status == "Pending":
        filtered_campaign = filtered_campaign[
            filtered_campaign["decision"] == ""
        ]

    elif selected_status == "Completed":
        filtered_campaign = filtered_campaign[
            filtered_campaign["decision"] != ""
        ]


    # -----------------------------------------------------
    # Campaign Table
    # -----------------------------------------------------

    st.write(
        f"Showing **{len(filtered_campaign)}** "
        f"of **{len(campaign)}** review items."
    )

    display_campaign = filtered_campaign.copy()

    display_campaign["risk"] = (
        display_campaign["risk_level"].apply(
            risk_icon
        )
        + " "
        + display_campaign[
            "risk_level"
        ].astype(str)
    )

    display_campaign["review_status"] = (
        display_campaign["decision"].apply(
            lambda value:
            (
                f"{decision_icon(value)} {value}"
                if value
                else "Pending"
            )
        )
    )

    display_columns = [
        "item_id",
        "identity_name",
        "identity_type",
        "application",
        "access",
        "reviewer",
        "risk_score",
        "risk",
        "recommendation",
        "review_status"
    ]

    st.dataframe(
        display_campaign[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "item_id": "Item ID",
            "identity_name": "Identity",
            "identity_type": "Type",
            "application": "Application",
            "access": "Access",
            "reviewer": "Reviewer",
            "risk_score": "Risk Score",
            "risk": "Risk Level",
            "recommendation": "Recommended",
            "review_status": "Status"
        }
    )


    # -----------------------------------------------------
    # Individual Review
    # -----------------------------------------------------

    st.divider()

    st.subheader("Review Access")

    if filtered_campaign.empty:

        st.info(
            "No review items match the selected filters."
        )

    else:

        item_options = filtered_campaign[
            "item_id"
        ].tolist()

        selected_item_id = st.selectbox(
            "Select a review item",
            item_options,
            format_func=lambda item_id: (
                f"{item_id} | "
                f"{campaign.loc[
                    campaign['item_id'] == item_id,
                    'identity_name'
                ].iloc[0]} | "
                f"{campaign.loc[
                    campaign['item_id'] == item_id,
                    'application'
                ].iloc[0]}"
            )
        )

        selected_rows = campaign[
            campaign["item_id"] == selected_item_id
        ]

        if not selected_rows.empty:

            item = selected_rows.iloc[0]

            st.markdown(
                f"### {risk_icon(item['risk_level'])} "
                f"{item['identity_name']}"
            )

            st.caption(
                f"{format_identity_type(item['identity_type'])} "
                f"• Review Item {item['item_id']}"
            )

            detail1, detail2, detail3, detail4 = (
                st.columns(4)
            )

            detail1.metric(
                "Application",
                item["application"]
            )

            detail2.metric(
                "Access",
                item["access"]
            )

            detail3.metric(
                "Risk Score",
                item["risk_score"]
            )

            detail4.metric(
                "Risk Level",
                item["risk_level"]
            )


            reviewer_col, recommendation_col = (
                st.columns(2)
            )

            with reviewer_col:

                st.markdown(
                    "**Assigned Reviewer**"
                )

                st.write(
                    item["reviewer"]
                )

            with recommendation_col:

                st.markdown(
                    "**Recommended Action**"
                )

                st.write(
                    item["recommendation"]
                )


            st.markdown(
                "#### Why was this flagged?"
            )

            reasons = parse_risk_reasons(
                item["risk_reasons"]
            )

            if reasons:

                for reason in reasons:
                    st.write(
                        f"• {reason}"
                    )

            else:

                st.write(
                    "No elevated risk conditions "
                    "were identified."
                )


            # -------------------------------------------------
            # Existing Decision
            # -------------------------------------------------

            existing_decision = str(
                item["decision"]
            ).strip()

            if existing_decision:

                st.divider()

                st.success(
                    f"This review has already been "
                    f"completed: {existing_decision}"
                )

                if str(
                    item["justification"]
                ).strip():

                    st.markdown(
                        "**Reviewer Justification**"
                    )

                    st.write(
                        item["justification"]
                    )


            # -------------------------------------------------
            # Review Form
            # -------------------------------------------------

            else:

                st.divider()

                st.markdown(
                    "#### Record Review Decision"
                )

                with st.form(
                    key=(
                        f"review_form_"
                        f"{selected_item_id}"
                    )
                ):

                    reviewer_name = st.text_input(
                        "Reviewer",
                        value=str(
                            item["reviewer"]
                        ),
                        help=(
                            "The reviewer must match "
                            "the person assigned to "
                            "this review."
                        )
                    )

                    decision_options = [
                        "CERTIFY",
                        "REVOKE",
                        "MODIFY",
                        "ESCALATE"
                    ]

                    recommended_action = str(
                        item["recommendation"]
                    ).upper()

                    if (
                        recommended_action
                        in decision_options
                    ):
                        default_index = (
                            decision_options.index(
                                recommended_action
                            )
                        )
                    else:
                        default_index = 0

                    decision = st.selectbox(
                        "Decision",
                        decision_options,
                        index=default_index
                    )

                    justification = st.text_area(
                        "Justification",
                        placeholder=(
                            "Explain why this access "
                            "should be certified, "
                            "revoked, modified, or "
                            "escalated."
                        ),
                        height=120
                    )

                    submit_decision = (
                        st.form_submit_button(
                            "Submit Decision",
                            type="primary",
                            use_container_width=True
                        )
                    )


                if submit_decision:

                    try:

                        event = record_demo_decision(
                            item_id=selected_item_id,
                            reviewer=reviewer_name,
                            decision=decision,
                            justification=justification
                        )

                        st.success(
                            f"{event['decision']} "
                            f"recorded successfully for "
                            f"{event['item_id']}."
                        )

                        if event[
                            "decision"
                        ] in {
                            "REVOKE",
                            "MODIFY",
                            "ESCALATE"
                        }:

                            st.info(
                                "A remediation item was "
                                "also added to the "
                                "remediation queue."
                            )

                        st.rerun()

                    except ValueError as error:

                        st.error(
                            str(error)
                        )


# =========================================================
# REMEDIATION QUEUE
# =========================================================

with remediation_tab:

    st.subheader(
        "Remediation Queue"
    )

    st.caption(
        "Access changes and escalations requiring "
        "additional action."
    )

    if remediation_queue.empty:

        st.info(
            "There are currently no remediation items."
        )

    else:

        total_remediation = len(
            remediation_queue
        )

        pending_remediation = (
            remediation_queue["status"]
            == "PENDING"
        ).sum()

        revoke_count = (
            remediation_queue["decision"]
            == "REVOKE"
        ).sum()

        modify_count = (
            remediation_queue["decision"]
            == "MODIFY"
        ).sum()

        escalate_count = (
            remediation_queue["decision"]
            == "ESCALATE"
        ).sum()

        rem1, rem2, rem3, rem4, rem5 = (
            st.columns(5)
        )

        rem1.metric(
            "Total",
            total_remediation
        )

        rem2.metric(
            "Pending",
            pending_remediation
        )

        rem3.metric(
            "Revoke",
            revoke_count
        )

        rem4.metric(
            "Modify",
            modify_count
        )

        rem5.metric(
            "Escalate",
            escalate_count
        )


        remediation_display = (
            remediation_queue.copy()
        )

        remediation_columns = [
            column
            for column in [
                "item_id",
                "identity_name",
                "identity_type",
                "application",
                "access",
                "decision",
                "risk_level",
                "reviewed_by",
                "status",
                "dry_run"
            ]
            if column
            in remediation_display.columns
        ]

        st.dataframe(
            remediation_display[
                remediation_columns
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "item_id": "Item ID",
                "identity_name": "Identity",
                "identity_type": "Type",
                "application": "Application",
                "access": "Access",
                "decision": "Action",
                "risk_level": "Risk",
                "reviewed_by": "Reviewed By",
                "status": "Status",
                "dry_run": "Dry Run"
            }
        )


        st.divider()

        st.markdown(
            "#### Remediation Details"
        )

        remediation_ids = (
            remediation_queue[
                "item_id"
            ]
            .astype(str)
            .tolist()
        )

        selected_remediation_id = (
            st.selectbox(
                "Select remediation item",
                remediation_ids,
                key="remediation_item"
            )
        )

        selected_remediation = (
            remediation_queue[
                remediation_queue[
                    "item_id"
                ]
                == selected_remediation_id
            ]
        )

        if not selected_remediation.empty:

            remediation_item = (
                selected_remediation.iloc[-1]
            )

            rem_detail1, rem_detail2, rem_detail3 = (
                st.columns(3)
            )

            rem_detail1.metric(
                "Action",
                remediation_item.get(
                    "decision",
                    ""
                )
            )

            rem_detail2.metric(
                "Risk Level",
                remediation_item.get(
                    "risk_level",
                    ""
                )
            )

            rem_detail3.metric(
                "Status",
                remediation_item.get(
                    "status",
                    ""
                )
            )

            st.markdown(
                "**Identity**"
            )

            st.write(
                remediation_item.get(
                    "identity_name",
                    ""
                )
            )

            st.markdown(
                "**Application / Access**"
            )

            st.write(
                f"{remediation_item.get('application', '')} "
                f"• "
                f"{remediation_item.get('access', '')}"
            )

            st.markdown(
                "**Justification**"
            )

            st.write(
                remediation_item.get(
                    "justification",
                    ""
                )
            )

            st.markdown(
                "**Risk Reasons**"
            )

            remediation_reasons = (
                parse_risk_reasons(
                    remediation_item.get(
                        "risk_reasons",
                        ""
                    )
                )
            )

            for reason in remediation_reasons:

                st.write(
                    f"• {reason}"
                )


# =========================================================
# AUDIT HISTORY
# =========================================================

with audit_tab:

    st.subheader(
        "Audit History"
    )

    st.caption(
        "Recorded history of completed access "
        "review decisions."
    )

    if audit_log.empty:

        st.info(
            "No review decisions have been "
            "recorded yet."
        )

    else:

        audit_total = len(
            audit_log
        )

        certify_total = (
            audit_log["decision"]
            == "CERTIFY"
        ).sum()

        revoke_total = (
            audit_log["decision"]
            == "REVOKE"
        ).sum()

        modify_total = (
            audit_log["decision"]
            == "MODIFY"
        ).sum()

        escalate_total = (
            audit_log["decision"]
            == "ESCALATE"
        ).sum()

        aud1, aud2, aud3, aud4, aud5 = (
            st.columns(5)
        )

        aud1.metric(
            "Total Decisions",
            audit_total
        )

        aud2.metric(
            "Certified",
            certify_total
        )

        aud3.metric(
            "Revoked",
            revoke_total
        )

        aud4.metric(
            "Modified",
            modify_total
        )

        aud5.metric(
            "Escalated",
            escalate_total
        )


        audit_display = (
            audit_log.copy()
        )

        if (
            "timestamp_utc"
            in audit_display.columns
        ):

            audit_display = (
                audit_display.sort_values(
                    "timestamp_utc",
                    ascending=False
                )
            )


        audit_columns = [
            column
            for column in [
                "timestamp_utc",
                "item_id",
                "identity_name",
                "application",
                "access",
                "assigned_reviewer",
                "reviewed_by",
                "decision",
                "risk_level",
                "justification"
            ]
            if column
            in audit_display.columns
        ]

        st.dataframe(
            audit_display[
                audit_columns
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp_utc": "Timestamp",
                "item_id": "Item ID",
                "identity_name": "Identity",
                "application": "Application",
                "access": "Access",
                "assigned_reviewer":
                    "Assigned Reviewer",
                "reviewed_by": "Reviewed By",
                "decision": "Decision",
                "risk_level": "Risk",
                "justification":
                    "Justification"
            }
        )


        st.divider()

        st.markdown(
            "#### Audit Event Details"
        )

        audit_options = list(
            audit_display.index
        )

        selected_audit_index = (
            st.selectbox(
                "Select audit event",
                audit_options,
                format_func=lambda index: (
                    f"{audit_display.loc[index, 'item_id']} | "
                    f"{audit_display.loc[index, 'decision']} | "
                    f"{audit_display.loc[index, 'identity_name']}"
                ),
                key="audit_event"
            )
        )

        audit_event = (
            audit_display.loc[
                selected_audit_index
            ]
        )

        audit_detail1, audit_detail2, audit_detail3 = (
            st.columns(3)
        )

        audit_detail1.metric(
            "Decision",
            audit_event.get(
                "decision",
                ""
            )
        )

        audit_detail2.metric(
            "Risk",
            audit_event.get(
                "risk_level",
                ""
            )
        )

        audit_detail3.metric(
            "Reviewed By",
            audit_event.get(
                "reviewed_by",
                ""
            )
        )

        st.markdown(
            "**Identity**"
        )

        st.write(
            audit_event.get(
                "identity_name",
                ""
            )
        )

        st.markdown(
            "**Application / Access**"
        )

        st.write(
            f"{audit_event.get('application', '')} "
            f"• "
            f"{audit_event.get('access', '')}"
        )

        st.markdown(
            "**Justification**"
        )

        st.write(
            audit_event.get(
                "justification",
                ""
            )
        )

        st.markdown(
            "**Risk Reasons**"
        )

        audit_reasons = (
            parse_risk_reasons(
                audit_event.get(
                    "risk_reasons",
                    ""
                )
            )
        )

        if audit_reasons:

            for reason in audit_reasons:

                st.write(
                    f"• {reason}"
                )

        else:

            st.write(
                "No elevated risk conditions "
                "were recorded."
            )