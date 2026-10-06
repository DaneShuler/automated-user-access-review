from pathlib import Path
from datetime import date, timedelta
import csv
import random


# ---------------------------------------------------------
# Sample Data Used for Generation
# ---------------------------------------------------------

FIRST_NAMES = [
    "Alex",
    "Sarah",
    "James",
    "Michael",
    "Jessica",
    "Emily",
    "David",
    "Maria",
    "Jordan",
    "Taylor",
    "Morgan",
    "Chris",
    "Jamie",
    "Avery",
    "Casey"
]

LAST_NAMES = [
    "Carter",
    "Kim",
    "Wilson",
    "Brown",
    "Davis",
    "Parker",
    "Reed",
    "Lopez",
    "Martin",
    "Clark",
    "Young",
    "Hall",
    "Allen",
    "King",
    "Wright"
]


# Departments and example job titles that belong to them.
DEPARTMENTS = {
    "Finance": [
        "Financial Analyst",
        "Accountant",
        "AP Analyst"
    ],
    "IT": [
        "System Administrator",
        "Cloud Engineer",
        "Help Desk Analyst"
    ],
    "Security": [
        "Security Analyst",
        "IAM Analyst",
        "Security Engineer"
    ],
    "Lending": [
        "Loan Officer",
        "Credit Analyst",
        "Underwriter"
    ],
    "Operations": [
        "Operations Analyst",
        "Operations Specialist",
        "Manager"
    ]
}


# Possible application access assignments.
#
# Each entry contains:
# Application, Entitlement, Risk Level, SOX Access
ACCESS_OPTIONS = [
    ("SAP", "Finance_Read", "Medium", "Yes"),
    ("SAP", "Vendor_Create", "High", "Yes"),
    ("Active Directory", "Domain Admin", "Critical", "No"),
    ("Active Directory", "Standard User", "Low", "No"),
    ("Salesforce", "Loan_Read", "Low", "No"),
    ("Salesforce", "Loan_Admin", "High", "No"),
    ("FinanceDB", "Finance_Admin", "High", "Yes"),
    ("LoanAPI", "Loan_Operator", "High", "No")
]


# Applications that exist in the fake company.
APPLICATIONS = [
    {
        "application": "SAP",
        "owner": "Maria Lopez",
        "criticality": "Critical",
        "sox": "Yes",
        "review_frequency_days": 90
    },
    {
        "application": "Active Directory",
        "owner": "David Reed",
        "criticality": "Critical",
        "sox": "No",
        "review_frequency_days": 90
    },
    {
        "application": "Salesforce",
        "owner": "Emily Parker",
        "criticality": "High",
        "sox": "No",
        "review_frequency_days": 180
    },
    {
        "application": "FinanceDB",
        "owner": "Maria Lopez",
        "criticality": "Critical",
        "sox": "Yes",
        "review_frequency_days": 90
    },
    {
        "application": "LoanAPI",
        "owner": "David Reed",
        "criticality": "Critical",
        "sox": "No",
        "review_frequency_days": 90
    }
]


# ---------------------------------------------------------
# CSV Helper
# ---------------------------------------------------------

def write_csv(path, rows):
    """
    Writes a list of dictionaries to a CSV file.
    """

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------
# Employee Generation
# ---------------------------------------------------------

def generate_employees(employee_count, today):
    """
    Creates fake employee records.

    The final two employees are intentionally marked as
    terminated so the access review has terminated users
    to evaluate.
    """

    employees = []

    for i in range(employee_count):
        department = random.choice(
            list(DEPARTMENTS.keys())
        )

        title = random.choice(
            DEPARTMENTS[department]
        )

        name = (
            f"{random.choice(FIRST_NAMES)} "
            f"{random.choice(LAST_NAMES)}"
        )

        manager = (
            f"{random.choice(FIRST_NAMES)} "
            f"{random.choice(LAST_NAMES)}"
        )

        # Keep most employees active, but intentionally create
        # two terminated employees for testing.
        if i in {employee_count - 1, employee_count - 2}:
            status = "Terminated"
        else:
            status = "Active"

        hire_date = today - timedelta(
            days=random.randint(100, 1600)
        )

        if status == "Terminated":
            termination_date = today - timedelta(
                days=random.randint(5, 60)
            )
        else:
            termination_date = ""

        employees.append({
            "employee_id": f"E{1001 + i}",
            "name": name,
            "title": title,
            "department": department,
            "manager": manager,
            "status": status,
            "hire_date": hire_date.isoformat(),
            "termination_date": (
                termination_date.isoformat()
                if termination_date
                else ""
            )
        })

    return employees


# ---------------------------------------------------------
# Employee Access Generation
# ---------------------------------------------------------

def generate_access_assignments(
    employees,
    access_count,
    today
):
    """
    Creates fake employee application access.

    This represents the type of access information that
    could come from an identity management platform such
    as Saviynt.
    """

    access_records = []

    for i in range(access_count):
        employee = random.choice(employees)

        application, entitlement, risk, sox = random.choice(
            ACCESS_OPTIONS
        )

        last_login = today - timedelta(
            days=random.randint(0, 150)
        )

        access_granted_date = today - timedelta(
            days=random.randint(30, 900)
        )

        # Create a simple username from the employee's name.
        account_name = (
            employee["name"][0]
            + employee["name"].split()[-1]
        ).lower()

        access_records.append({
            "account_id": f"A{i + 1:04d}",
            "employee_id": employee["employee_id"],
            "application": application,
            "account_name": account_name,
            "entitlement": entitlement,
            "role": employee["title"],
            "risk_level": risk,
            "sox": sox,
            "last_login": last_login.isoformat(),
            "account_status": "Active",
            "access_granted_date": access_granted_date.isoformat()
        })

    # -----------------------------------------------------
    # Plant a Known Security Problem
    # -----------------------------------------------------
    #
    # Give a terminated employee active, high-risk,
    # SOX-related access.
    #
    # The risk engine should detect this and recommend
    # that the access be revoked.

    terminated_employee = employees[-1]

    access_records[0].update({
        "employee_id": terminated_employee["employee_id"],
        "application": "SAP",
        "entitlement": "Vendor_Create",
        "risk_level": "High",
        "sox": "Yes",
        "account_status": "Active"
    })

    return access_records


# ---------------------------------------------------------
# Service Account / Non-Human Account Generation
# ---------------------------------------------------------

def generate_non_human_accounts(
    employees,
    account_count,
    today
):
    """
    Creates fake service accounts, service principals,
    and API keys.

    This represents the type of information that could
    come from a platform such as Oasis.
    """

    accounts = []

    account_types = [
        "Service Account",
        "Service Principal",
        "API Key"
    ]

    platforms = [
        "Active Directory",
        "Azure",
        "AWS"
    ]

    resources = [
        "FinanceDB",
        "LoanAPI",
        "SAP",
        "Salesforce"
    ]

    environments = [
        "Production",
        "Development",
        "Test"
    ]

    privilege_levels = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    for i in range(account_count):
        owner = random.choice(employees)
        resource = random.choice(resources)

        last_used = today - timedelta(
            days=random.randint(0, 180)
        )

        accounts.append({
            "nhi_id": f"NHI{i + 1:03d}",
            "name": f"svc_{resource.lower()}_{i + 1:02d}",
            "type": random.choice(account_types),
            "platform": random.choice(platforms),

            "owner": owner["employee_id"],
            "owner_name": owner["name"],
            "owner_status": owner["status"],

            "application": resource,
            "environment": random.choice(environments),
            "privilege_level": random.choice(privilege_levels),

            "last_used": last_used.isoformat(),

            "credential_age_days": random.randint(
                5,
                500
            ),

            "rotation_required": random.choice([
                "Yes",
                "No"
            ]),

            "resource": resource
        })

    # -----------------------------------------------------
    # Plant a Known Service Account Problem
    # -----------------------------------------------------
    #
    # This account intentionally has several warning signs:
    #
    # - Its owner has been terminated
    # - It is used in production
    # - It has high privileges
    # - Its credentials are old
    # - Credential rotation is required
    # - It has not been used recently
    #
    # The program should classify this account as Critical
    # and recommend that it be escalated for investigation.

    terminated_employee = employees[-1]

    accounts[0].update({
        "name": "svc_legacy_reporting",
        "owner": terminated_employee["employee_id"],
        "owner_name": terminated_employee["name"],
        "owner_status": "Terminated",
        "application": "FinanceDB",
        "environment": "Production",
        "privilege_level": "High",
        "last_used": (
            today - timedelta(days=120)
        ).isoformat(),
        "credential_age_days": 380,
        "rotation_required": "Yes",
        "resource": "FinanceDB"
    })

    return accounts


# ---------------------------------------------------------
# Main Data Generation Function
# ---------------------------------------------------------

def generate(
    base="data",
    seed=42,
    employee_count=50,
    access_count=200,
    nhi_count=40
):
    """
    Generates all fake data needed for the project.
    """

    # Using the same seed makes the generated data
    # repeatable between test runs.
    random.seed(seed)

    base = Path(base)

    # Create the data directory if it does not exist.
    base.mkdir(
        parents=True,
        exist_ok=True
    )

    today = date.today()

    # Generate employees.
    employees = generate_employees(
        employee_count,
        today
    )

    # Generate employee application access.
    access_records = generate_access_assignments(
        employees,
        access_count,
        today
    )

    # Generate service accounts and other
    # non-human accounts.
    non_human_accounts = generate_non_human_accounts(
        employees,
        nhi_count,
        today
    )

    # -----------------------------------------------------
    # Write Everything to CSV
    # -----------------------------------------------------

    write_csv(
        base / "employees.csv",
        employees
    )

    write_csv(
        base / "applications.csv",
        APPLICATIONS
    )

    write_csv(
        base / "saviynt_access.csv",
        access_records
    )

    write_csv(
        base / "oasis_nhi.csv",
        non_human_accounts
    )