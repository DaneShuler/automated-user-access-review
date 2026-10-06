import argparse
import json
from pathlib import Path

from src.generate_data import generate
from src.connectors import (
    HRConnector,
    SaviyntConnector,
    OasisConnector,
    ApplicationConnector
)
from src.campaign import build_campaign
from src.review import record_decision


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

# Find the main project directory.
ROOT = Path(__file__).parent

# Source data is stored here.
DATA = ROOT / "data"

# Generated review files are stored here.
OUTPUT = ROOT / "output"

# Configuration file containing risk and review settings.
CONFIG_FILE = ROOT / "config.json"


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

def load_config():
    """
    Loads the project's settings from config.json.
    """

    return json.loads(
        CONFIG_FILE.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------
# Generate Fake Data
# ---------------------------------------------------------

def generate_data(args):
    """
    Generates the fake employee, application, access,
    and service account data used by the project.
    """

    generate(
        base=DATA,
        seed=args.seed,
        employee_count=args.employees,
        access_count=args.access,
        nhi_count=args.nhi
    )

    print("Generated synthetic data.")
    print(f"Employees: {args.employees}")
    print(f"Employee access assignments: {args.access}")
    print(f"Service/non-human accounts: {args.nhi}")


# ---------------------------------------------------------
# Create User Access Review Campaign
# ---------------------------------------------------------

def create_campaign(args):
    """
    Loads information from each source, evaluates risk,
    assigns reviewers, and creates the User Access Review.
    """

    # Make sure the output directory exists.
    OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    # Load the project configuration.
    config = load_config()

    # -----------------------------------------------------
    # Load Information From Each Source
    # -----------------------------------------------------

    employees = HRConnector(
        DATA / "employees.csv"
    ).get_employees()

    employee_access = SaviyntConnector(
        DATA / "saviynt_access.csv"
    ).get_access()

    non_human_accounts = OasisConnector(
        DATA / "oasis_nhi.csv"
    ).get_non_human_identities()

    applications = ApplicationConnector(
        DATA / "applications.csv"
    ).get_applications()

    # -----------------------------------------------------
    # Build the Review Campaign
    # -----------------------------------------------------

    campaign = build_campaign(
        employees=employees,
        access=employee_access,
        nhi=non_human_accounts,
        applications=applications,
        config=config
    )

    campaign_path = OUTPUT / "review_campaign.csv"

    campaign.to_csv(
        campaign_path,
        index=False
    )

    # -----------------------------------------------------
    # Display a Summary
    # -----------------------------------------------------

    print()
    print("User Access Review campaign created.")
    print(f"Total review items: {len(campaign)}")
    print()

    if not campaign.empty:
        print("Risk Summary:")
        print(
            campaign["risk_level"]
            .value_counts()
            .to_string()
        )

    print()
    print(f"Campaign saved to: {campaign_path}")


# ---------------------------------------------------------
# Record a Review Decision
# ---------------------------------------------------------

def record_review_decision(args):
    """
    Records a reviewer's decision for a specific access item.

    Reviewer authorization can be enforced through
    the review_settings section of config.json.
    """

    config = load_config()

    review_settings = config.get(
        "review_settings",
        {}
    )

    enforce_reviewer = review_settings.get(
        "enforce_assigned_reviewer",
        True
    )

    event = record_decision(
        campaign_path=OUTPUT / "review_campaign.csv",
        audit_path=OUTPUT / "audit_log.csv",
        remediation_path=OUTPUT / "remediation_queue.csv",
        item_id=args.item_id,
        reviewer=args.reviewer,
        decision=args.decision,
        justification=args.justification,
        enforce_assigned_reviewer=enforce_reviewer
    )

    print()
    print("Review decision recorded.")
    print(f"Item: {event['item_id']}")
    print(f"Decision: {event['decision']}")
    print(f"Reviewed by: {event['reviewed_by']}")

    if event["decision"] in {
        "REVOKE",
        "MODIFY",
        "ESCALATE"
    }:
        print(
            "A remediation item was added to the "
            "remediation queue."
        )


# ---------------------------------------------------------
# Command-Line Setup
# ---------------------------------------------------------

def create_parser():
    """
    Creates the command-line options used to run the project.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Automated User Access Review proof of concept."
        )
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True
    )

    # -----------------------------------------------------
    # Generate Command
    # -----------------------------------------------------

    generate_parser = commands.add_parser(
        "generate",
        help="Generate fake data for testing."
    )

    generate_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used to create repeatable test data."
    )

    generate_parser.add_argument(
        "--employees",
        type=int,
        default=50,
        help="Number of fake employees to generate."
    )

    generate_parser.add_argument(
        "--access",
        type=int,
        default=200,
        help="Number of employee access assignments to generate."
    )

    generate_parser.add_argument(
        "--nhi",
        type=int,
        default=40,
        help="Number of service/non-human accounts to generate."
    )

    generate_parser.set_defaults(
        func=generate_data
    )

    # -----------------------------------------------------
    # Campaign Command
    # -----------------------------------------------------

    campaign_parser = commands.add_parser(
        "campaign",
        help="Create a User Access Review campaign."
    )

    campaign_parser.set_defaults(
        func=create_campaign
    )

    # -----------------------------------------------------
    # Decision Command
    # -----------------------------------------------------

    decision_parser = commands.add_parser(
        "decide",
        help="Record a decision for a review item."
    )

    decision_parser.add_argument(
        "--item-id",
        required=True,
        help="Review item ID, such as H-A0174."
    )

    decision_parser.add_argument(
        "--reviewer",
        required=True,
        help="Name of the person completing the review."
    )

    decision_parser.add_argument(
        "--decision",
        required=True,
        choices=[
            "CERTIFY",
            "REVOKE",
            "MODIFY",
            "ESCALATE"
        ],
        help="Decision being made for the access."
    )

    decision_parser.add_argument(
        "--justification",
        required=True,
        help="Reason for the review decision."
    )

    decision_parser.set_defaults(
        func=record_review_decision
    )

    return parser


# ---------------------------------------------------------
# Start the Program
# ---------------------------------------------------------

def main():
    """
    Reads the command entered by the user and runs
    the appropriate part of the project.

    Expected user errors are displayed cleanly instead
    of showing a full Python traceback.
    """

    parser = create_parser()
    args = parser.parse_args()

    try:
        args.func(args)

    except ValueError as error:
        print()
        print(f"ERROR: {error}")


if __name__ == "__main__":
    main()