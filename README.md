# Automated User Access Review

This is a proof of concept I built to explore how parts of the User Access Review process could be automated.

The project brings identity and access information from multiple sources into a review campaign, identifies access that may deserve additional attention, assigns an appropriate reviewer, and tracks decisions through remediation and audit history.

It includes both a command-line workflow and an interactive Streamlit dashboard.

> **Important:** All identities, accounts, applications, access assignments, policies, and review records in this repository are synthetic. No real company or user data is used.

---

## Live Demo

### [Open the Live UAR Demo](https://automated-user-access-review.streamlit.app/)

The hosted Streamlit application runs as an isolated demonstration environment. Each visitor receives their own session, so review decisions can be submitted and the workflow can be tested without modifying the repository or affecting other users.

The demo can be reset to its original state at any time and does not connect to or modify any production identity systems.

---

## Dashboard

### Access Review Campaign

![Access Review Dashboard](screenshots/access-reviews.png)

The campaign dashboard prioritizes access reviews by risk and supports filtering by risk level, application, identity type, assigned reviewer, and review status.

### Individual Access Review

![Individual Access Review](screenshots/review-details.png)

Selecting an item shows the identity, application, entitlement, risk score, assigned reviewer, recommended action, and the individual conditions that contributed to the risk score.

Reviewers can **CERTIFY**, **REVOKE**, **MODIFY**, or **ESCALATE** access and must provide a justification for the decision.

### Remediation Queue

![Remediation Queue](screenshots/remediation-queue.png)

REVOKE, MODIFY, and ESCALATE decisions are placed into a separate remediation queue instead of immediately changing access.

The proof of concept operates in dry-run mode, demonstrating where remediation could continue without making changes to a real identity system.

### Audit History

![Audit History](screenshots/audit-history.png)

Every completed review creates an audit record containing the identity, access, reviewer, decision, justification, risk information, and timestamp.

---

## How It Works

The proof of concept combines four sources of information:

- Employee and workforce information
- Human identity and access information
- Service accounts and other non-human identities
- Application ownership and review information

The program normalizes this information, evaluates access using configurable risk rules, assigns reviewers, and creates a User Access Review campaign.

```text
Employee / HR Information ───────┐
                                 │
Human Access / Saviynt ──────────┤
                                 │
Non-Human Identities / Oasis ────┼──> Normalize Access
                                 │          │
Application Information ─────────┘          ↓
                                       Risk Scoring
                                            │
                                            ↓
                                    Reviewer Assignment
                                            │
                                            ↓
                                    User Access Review
                                            │
                         ┌──────────────────┼──────────────────┐
                         │                  │                  │
                      CERTIFY       REVOKE / MODIFY         ESCALATE
                         │                  │                  │
                         │                  └────────┬─────────┘
                         │                           ↓
                         │                   Remediation Queue
                         │                           │
                         └─────────────┬─────────────┘
                                       ↓
                                   Audit History
```

One of the main design choices was keeping the review decision separate from the access change. A reviewer selecting REVOKE does not immediately remove access. Instead, the decision creates remediation work that can be processed separately.

---

## How This Relates to Existing IAM Platforms

This proof of concept is not intended to replace the access review and certification capabilities already available in identity governance platforms such as Saviynt.

Instead, I built it to explore the complete User Access Review workflow and how information from multiple identity sources could be brought together, prioritized, assigned for review, and tracked through remediation and audit history.

In a production environment, many of these functions could remain within the organization's existing identity governance platform. The automation needed would depend on the existing environment and could focus on areas such as data integration, campaign preparation, reviewer assignment, exception handling, remediation, and reporting.

The connectors in this project are intentionally separated from the review logic so the synthetic CSV sources could be replaced with real integrations without redesigning the entire workflow.

---

## Key Features

### Risk-Based Prioritization

Human access is evaluated using factors such as:

- Employment status
- Active access belonging to terminated employees
- Critical or high-risk entitlements
- SOX-controlled access
- Last login activity

Service accounts and other non-human identities are evaluated using factors such as:

- Missing or terminated ownership
- Privilege level
- Production usage
- Credential age
- Credential rotation requirements
- Last account usage

Each applicable condition contributes to a risk score and is also recorded as a readable reason.

For example:

```text
terminated employee retains active access
high-risk entitlement
SOX-controlled access
stale login (131 days)
```

Risk scores prioritize reviews but never automatically certify or revoke access.

### Reviewer Assignment

Reviews are routed based on the type and risk of the access. Depending on the situation, a review can be assigned to an employee's manager, an application owner, or IAM.

The assigned reviewer is enforced when a decision is submitted. An unauthorized reviewer cannot complete someone else's assigned review.

### Review Decisions

Reviewers can choose:

- **CERTIFY:** Access remains appropriate
- **REVOKE:** Access should be removed
- **MODIFY:** Access should be changed
- **ESCALATE:** Additional investigation or approval is needed

Every decision requires a justification, and completed reviews cannot be submitted a second time.

### Remediation and Audit Evidence

CERTIFY decisions are recorded in the audit history without creating remediation work.

REVOKE, MODIFY, and ESCALATE decisions are recorded in the audit history and added to the remediation queue.

This keeps risk assessment, human approval, and access remediation separate while maintaining evidence of the complete review process.

---

## Example Data

The project generates:

- 50 synthetic employees
- 200 synthetic employee access assignments
- 40 synthetic service accounts and other non-human identities
- Application ownership and review metadata

Several problems are deliberately planted in the generated data so the workflow has realistic scenarios to identify.

Examples include:

- A terminated employee retaining active access
- High-risk and SOX-controlled access
- Stale employee access
- A service account owned by a terminated employee
- Privileged production identities
- Old credentials requiring rotation
- Stale service account usage

The repository also contains example campaign, remediation, and audit output so the results can be reviewed without running the project first.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/DaneShuler/automated-user-access-review.git
cd automated-user-access-review
```

### 2. Create a virtual environment

Windows:

```bash
py -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Generate synthetic data

```bash
python main.py generate
```

### 5. Create the review campaign

```bash
python main.py campaign
```

### 6. Start the dashboard

```bash
python -m streamlit run app.py
```

---

## Command-Line Interface

The same workflow can also be used without the dashboard.

Generate synthetic data:

```bash
python main.py generate
```

Create the campaign:

```bash
python main.py campaign
```

Record a review decision:

```bash
python main.py decide --item-id H-A0001 --reviewer "Dane Shuler" --decision REVOKE --justification "Employee is terminated and should no longer retain active access."
```

The command-line workflow writes persistent results to the `output/` directory. The hosted Streamlit version instead uses isolated session data so visitors can safely interact with the demo.

---

## Project Structure

```text
automated-user-access-review/
│
├── app.py
├── main.py
├── config.json
├── requirements.txt
│
├── data/
│   ├── employees.csv
│   ├── applications.csv
│   ├── saviynt_access.csv
│   └── oasis_nhi.csv
│
├── demo/
│   ├── review_campaign.csv
│   ├── audit_log.csv
│   └── remediation_queue.csv
│
├── output/
│   ├── review_campaign.csv
│   ├── audit_log.csv
│   └── remediation_queue.csv
│
├── screenshots/
│
├── src/
│   ├── campaign.py
│   ├── connectors.py
│   ├── generate_data.py
│   ├── review.py
│   └── risk_engine.py
│
└── tests/
    └── test_risk_engine.py
```

### Main Components

**`app.py`**  
Interactive Streamlit interface for reviewing access, recording decisions, viewing remediation work, and inspecting audit history.

**`main.py`**  
Command-line interface for generating data, creating campaigns, and recording review decisions.

**`src/connectors.py`**  
Defines the boundaries between the review workflow and its data sources. The proof of concept uses CSV files, but these connectors could be replaced with real integrations.

**`src/risk_engine.py`**  
Evaluates human and non-human identity access using configurable risk rules and records the reasons contributing to each score.

**`src/campaign.py`**  
Combines source information, calculates risk, assigns reviewers, provides recommendations, and creates the review campaign.

**`src/review.py`**  
Handles review decisions, reviewer authorization, duplicate-review prevention, remediation queue creation, and audit evidence.

**`config.json`**  
Contains configurable risk rules, thresholds, and review settings.

---

## Testing

Run the automated tests with:

```bash
python -m pytest -q
```

The project tests important behaviors including human and non-human identity risk scoring, reviewer authorization, duplicate decision prevention, audit logging, and remediation queue creation.

A GitHub Actions workflow runs the test suite automatically when changes are pushed.

---

## Design and Safety Choices

A few safeguards were intentional:

- Risk scores prioritize reviews but do not make access decisions automatically.
- Review decisions require human input and written justification.
- The assigned reviewer is enforced.
- Duplicate review decisions are rejected.
- Review approval and remediation are separate steps.
- Remediation remains in dry-run mode.
- The public demo uses isolated sessions and does not modify production systems or repository data.

The goal is to automate the repetitive parts of the review process while keeping consequential access decisions controlled and auditable.

---

## Current Limitations and Future Improvements

This is a proof of concept rather than a production identity governance system.

The current version uses synthetic CSV data, demonstration risk policies, and simulated remediation. It does not authenticate dashboard users, execute real access changes, send review notifications, or connect to production identity systems.

Potential next steps could include:

- Real identity and HR system integrations
- Automated campaign creation and scheduling
- Email or Teams review notifications
- Review deadlines, reminders, and escalations
- Separation of Duties checks
- Additional approval requirements for sensitive access
- Remediation status tracking and verification
- Authentication and role-based dashboard access
- Additional reporting and campaign analytics

---

## Why I Built This

I built this project after discussing User Access Review automation as a real IAM challenge.

Rather than attempting to recreate a full identity governance platform, I wanted to understand the problem from end to end: bringing identity information together, identifying potentially risky access, assigning responsibility, capturing human decisions, separating approval from remediation, and maintaining audit evidence.

The result is a small, vendor-aware proof of concept that demonstrates how I would begin approaching the workflow while leaving the specific integrations, policies, and implementation details dependent on the organization's existing IAM environment.
