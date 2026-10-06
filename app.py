from pathlib import Path
import json

import pandas as pd
import streamlit as st

from src.review import record_decision


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"

CAMPAIGN_FILE = OUTPUT / "review_campaign.csv"
AUDIT_FILE = OUTPUT / "audit_log.csv"
REMEDIATION_FILE = OUTPUT / "remediation_queue.csv"
CONFIG_FILE = ROOT / "config.json"


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
    Loads a CSV file and replaces empty values with
    blank strings.

    If the file does not exist yet, an empty DataFrame
    is returned instead.
    """

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path).fillna("")


def load_config():
    """
    Loads project settings from config.json.
    """

    if not CONFIG_FILE.exists():
        return {}

    return json.loads(
        CONFIG_FILE.read_text(encoding="utf-8")
    )


campaign = load_csv(CAMPAIGN_FILE)
audit_log = load_csv(AUDIT_FILE)
remediation_queue = load_csv(REMEDIATION_FILE)
config = load_config()


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def risk_icon(risk_level):
    """
    Returns a simple visual indicator for each risk level.
    """

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
    """
    Returns a visual indicator for review decisions.
    """

    icons = {
        "CERTIFY": "✅",
        "REVOKE": "❌",
        "MODIFY": "✏️",
        "ESCALATE": "⚠️"
    }

    return icons.get(
        str(decision).upper(),
        ""
    )


def format_identity_type(identity_type):
    """
    Converts internal identity type names into
    easier-to-read labels.
    """

    if identity_type == "NHI":
        return "Service / Non-Human Identity"

    if identity_type == "HUMAN":
        return "Employee"

    return identity_type


def parse_risk_reasons(value):
    """
    Converts the semicolon-separated risk reasons stored
    in the campaign into a list.
    """

    if not value:
        return []

    if str(value).lower() == "none":
        return []

    return [
        reason.strip()
        for reason in str(value).split(";")
        if reason.strip()
    ]


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("User Access Review")

st.caption(
    "Risk-based review of employee and service account access."
)


# ---------------------------------------------------------
# Campaign Check
# ---------------------------------------------------------

if campaign.empty:
    st.warning(
        "No review campaign was found. "
        "Run `python main.py campaign` first."
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

normal_reviews = (
    campaign["risk_level"] == "NORMAL"
).sum()

completed_reviews = (
    campaign["decision"] != ""
).sum()

pending_reviews = (
    campaign["decision"] == ""
).sum()


st.subheader("Campaign Overview")

metric1, metric2, metric3, metric4, metric5, metric6 = st.columns(6)

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
# Progress
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
# Main Navigation
# ---------------------------------------------------------

reviews_tab, remediation_tab, audit_tab = st.tabs(
    [
        "Access Reviews",
        "Remediation Queue",
        "Audit History"
    ]
)


# =========================================================
# ACCESS REVIEWS TAB
# =========================================================

with reviews_tab:

    st.subheader("Access Reviews")

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    filter1, filter2, filter3, filter4, filter5 = st.columns(5)

    risk_options = [
        "All",
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "NORMAL"
    ]

    selected_risk = filter1.selectbox(
        "Risk Level",
        risk_options
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

    identity_options = [
        "All",
        "HUMAN",
        "NHI"
    ]

    selected_identity = filter3.selectbox(
        "Identity Type",
        identity_options
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

    status_options = [
        "All",
        "Pending",
        "Completed"
    ]

    selected_status = filter5.selectbox(
        "Review Status",
        status_options
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
    # Review Table
    # -----------------------------------------------------

    st.write(
        f"Showing **{len(filtered_campaign)}** "
        f"of **{len(campaign)}** review items."
    )

    display_campaign = filtered_campaign.copy()

    display_campaign["risk"] = (
        display_campaign["risk_level"].apply(risk_icon)
        + " "
        + display_campaign["risk_level"].astype(str)
    )

    display_campaign["review_status"] = (
        display_campaign["decision"]
        .apply(
            lambda value:
            f"{decision_icon(value)} {value}"
            if value
            else "Pending"
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
        display_campaign[display_columns],
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
    # Individual Review Workspace
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

            # -------------------------------------------------
            # Identity Summary
            # -------------------------------------------------

            st.markdown(
                f"### {risk_icon(item['risk_level'])} "
                f"{item['identity_name']}"
            )

            st.caption(
                f"{format_identity_type(item['identity_type'])} "
                f"• Review Item {item['item_id']}"
            )

            detail1, detail2, detail3, detail4 = st.columns(4)

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


            # -------------------------------------------------
            # Reviewer and Recommendation
            # -------------------------------------------------

            reviewer_col, recommendation_col = st.columns(2)

            with reviewer_col:

                st.markdown("**Assigned Reviewer**")

                st.write(
                    item["reviewer"]
                )

            with recommendation_col:

                st.markdown("**Recommended Action**")

                st.write(
                    item["recommendation"]
                )


            # -------------------------------------------------
            # Risk Reasons
            # -------------------------------------------------

            st.markdown("#### Why was this flagged?")

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
                    "No elevated risk conditions were identified."
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
                    f"This review has already been completed: "
                    f"{existing_decision}"
                )

                if str(item["justification"]).strip():

                    st.markdown("**Reviewer Justification**")

                    st.write(
                        item["justification"]
                    )


            # -------------------------------------------------
            # Decision Form
            # -------------------------------------------------

            else:

                st.divider()

                st.markdown("#### Record Review Decision")

                with st.form(
                    key=f"review_form_{selected_item_id}"
                ):

                    reviewer_name = st.text_input(
                        "Reviewer",
                        value=str(item["reviewer"]),
                        help=(
                            "The reviewer must match the person "
                            "assigned to this review when reviewer "
                            "enforcement is enabled."
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

                    if recommended_action in decision_options:
                        default_decision_index = (
                            decision_options.index(
                                recommended_action
                            )
                        )
                    else:
                        default_decision_index = 0

                    decision = st.selectbox(
                        "Decision",
                        decision_options,
                        index=default_decision_index
                    )

                    justification = st.text_area(
                        "Justification",
                        placeholder=(
                            "Explain why this access should be "
                            "certified, revoked, modified, or escalated."
                        ),
                        height=120
                    )

                    submit_decision = st.form_submit_button(
                        "Submit Decision",
                        type="primary",
                        use_container_width=True
                    )


                # -------------------------------------------------
                # Submit Review
                # -------------------------------------------------

                if submit_decision:

                    try:

                        review_settings = config.get(
                            "review_settings",
                            {}
                        )

                        enforce_reviewer = (
                            review_settings.get(
                                "enforce_assigned_reviewer",
                                True
                            )
                        )

                        event = record_decision(
                            campaign_path=CAMPAIGN_FILE,
                            audit_path=AUDIT_FILE,
                            remediation_path=REMEDIATION_FILE,
                            item_id=selected_item_id,
                            reviewer=reviewer_name,
                            decision=decision,
                            justification=justification,
                            enforce_assigned_reviewer=(
                                enforce_reviewer
                            )
                        )

                        st.success(
                            f"{event['decision']} recorded "
                            f"successfully for {event['item_id']}."
                        )

                        if event["decision"] in {
                            "REVOKE",
                            "MODIFY",
                            "ESCALATE"
                        }:

                            st.info(
                                "A remediation item was also added "
                                "to the remediation queue."
                            )

                        # Reload the page so the dashboard,
                        # campaign counts, and tables immediately
                        # reflect the new decision.
                        st.rerun()

                    except ValueError as error:

                        st.error(
                            str(error)
                        )

                    except PermissionError:

                        st.error(
                            "The campaign or output file could not "
                            "be updated. Make sure the CSV files "
                            "are not currently open in Excel."
                        )


# =========================================================
# REMEDIATION QUEUE TAB
# =========================================================

with remediation_tab:

    st.subheader("Remediation Queue")

    st.caption(
        "Access changes and escalations requiring additional action."
    )

    if remediation_queue.empty:

        st.info(
            "There are currently no remediation items."
        )

    else:

        # -----------------------------------------------------
        # Remediation Metrics
        # -----------------------------------------------------

        total_remediation = len(
            remediation_queue
        )

        pending_remediation = (
            remediation_queue["status"] == "PENDING"
        ).sum()

        revoke_count = (
            remediation_queue["decision"] == "REVOKE"
        ).sum()

        modify_count = (
            remediation_queue["decision"] == "MODIFY"
        ).sum()

        escalate_count = (
            remediation_queue["decision"] == "ESCALATE"
        ).sum()

        rem1, rem2, rem3, rem4, rem5 = st.columns(5)

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


        # -----------------------------------------------------
        # Remediation Table
        # -----------------------------------------------------

        remediation_display = remediation_queue.copy()

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
            if column in remediation_display.columns
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


        # -----------------------------------------------------
        # Remediation Details
        # -----------------------------------------------------

        st.divider()

        st.markdown("#### Remediation Details")

        remediation_ids = (
            remediation_queue["item_id"]
            .astype(str)
            .tolist()
        )

        selected_remediation_id = st.selectbox(
            "Select remediation item",
            remediation_ids,
            key="remediation_item"
        )

        selected_remediation = remediation_queue[
            remediation_queue["item_id"]
            == selected_remediation_id
        ]

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

            st.markdown("**Identity**")

            st.write(
                remediation_item.get(
                    "identity_name",
                    ""
                )
            )

            st.markdown("**Application / Access**")

            st.write(
                f"{remediation_item.get('application', '')} "
                f"• "
                f"{remediation_item.get('access', '')}"
            )

            st.markdown("**Justification**")

            st.write(
                remediation_item.get(
                    "justification",
                    ""
                )
            )

            st.markdown("**Risk Reasons**")

            remediation_reasons = parse_risk_reasons(
                remediation_item.get(
                    "risk_reasons",
                    ""
                )
            )

            for reason in remediation_reasons:
                st.write(
                    f"• {reason}"
                )


# =========================================================
# AUDIT HISTORY TAB
# =========================================================

with audit_tab:

    st.subheader("Audit History")

    st.caption(
        "Recorded history of completed access review decisions."
    )

    if audit_log.empty:

        st.info(
            "No review decisions have been recorded yet."
        )

    else:

        # -----------------------------------------------------
        # Audit Metrics
        # -----------------------------------------------------

        audit_total = len(audit_log)

        certify_total = (
            audit_log["decision"] == "CERTIFY"
        ).sum()

        revoke_total = (
            audit_log["decision"] == "REVOKE"
        ).sum()

        modify_total = (
            audit_log["decision"] == "MODIFY"
        ).sum()

        escalate_total = (
            audit_log["decision"] == "ESCALATE"
        ).sum()

        aud1, aud2, aud3, aud4, aud5 = st.columns(5)

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


        # -----------------------------------------------------
        # Audit Table
        # -----------------------------------------------------

        audit_display = audit_log.copy()

        # Show newest events first.
        if "timestamp_utc" in audit_display.columns:

            audit_display = audit_display.sort_values(
                "timestamp_utc",
                ascending=False
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
            if column in audit_display.columns
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
                "assigned_reviewer": "Assigned Reviewer",
                "reviewed_by": "Reviewed By",
                "decision": "Decision",
                "risk_level": "Risk",
                "justification": "Justification"
            }
        )


        # -----------------------------------------------------
        # Audit Event Details
        # -----------------------------------------------------

        st.divider()

        st.markdown("#### Audit Event Details")

        audit_options = list(
            audit_display.index
        )

        selected_audit_index = st.selectbox(
            "Select audit event",
            audit_options,
            format_func=lambda index: (
                f"{audit_display.loc[index, 'item_id']} | "
                f"{audit_display.loc[index, 'decision']} | "
                f"{audit_display.loc[index, 'identity_name']}"
            ),
            key="audit_event"
        )

        audit_event = audit_display.loc[
            selected_audit_index
        ]

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

        st.markdown("**Identity**")

        st.write(
            audit_event.get(
                "identity_name",
                ""
            )
        )

        st.markdown("**Application / Access**")

        st.write(
            f"{audit_event.get('application', '')} "
            f"• "
            f"{audit_event.get('access', '')}"
        )

        st.markdown("**Justification**")

        st.write(
            audit_event.get(
                "justification",
                ""
            )
        )

        st.markdown("**Risk Reasons**")

        audit_reasons = parse_risk_reasons(
            audit_event.get(
                "risk_reasons",
                ""
            )
        )

        if audit_reasons:

            for reason in audit_reasons:
                st.write(
                    f"• {reason}"
                )

        else:

            st.write(
                "No elevated risk conditions were recorded."
            )