# Automated User Access Review

This is a proof-of-concept I built to explore how parts of the User Access Review process could be automated.

The goal of the project is to take access information from multiple sources, organize it into a single review, identify access that may need extra attention, assign the appropriate reviewer, and keep track of the final decision.

The project uses example data similar to what could come from platforms such as Saviynt for employee access and Oasis for service accounts and other non-human accounts.

> **Important:** Every employee, account, application, access assignment, and policy in this repository is made up. No real company or user data is used.

## How It Works

The program starts with four sets of information:

- Employee information, including department, manager, and employment status
- Employee application access, similar to information that could come from Saviynt
- Service accounts and other non-human accounts, similar to information that could come from Oasis
- Application information, including application owners and whether an application has additional review requirements

The program combines this information and looks for situations that may deserve additional attention.

For example, it can identify:

- A terminated employee who still has active access
- High-risk or critical access
- Access to applications covered by SOX controls
- Accounts that have not been used recently
- Service accounts owned by terminated employees
- Highly privileged service accounts
- Old credentials that may need to be rotated
- Production service accounts that deserve additional review

Each access item receives a risk score and explanation showing why it was flagged. The program then determines who should review the access and creates a User Access Review campaign.

A reviewer can make one of four decisions:

- **CERTIFY**: The access is still appropriate
- **REVOKE**: The access should be removed
- **MODIFY**: The access needs to be changed
- **ESCALATE**: Someone else needs to investigate or make the decision

The reviewer is also required to provide a reason for the decision.

## Review Process

The overall process looks like this:

```text
Employee and Account Information
            ↓
     Access Information
            ↓
   Combine the Information
            ↓
   Check for Risk Factors
            ↓
 Create User Access Review
            ↓
      Reviewer Decision
            ↓
  Remediation if Required
            ↓
       Audit History
```

One of the main design choices I made was keeping the review decision separate from the actual access change.

For example, choosing **REVOKE** does not immediately remove someone's access. Instead, it creates a remediation item that can be reviewed and processed separately. This helps prevent an automated process from making a destructive access change without the proper checks in place.

## Example Data

The project currently generates:

- 50 employees
- 200 employee access assignments
- 40 service accounts and other non-human identities
- Several applications with different owners and security requirements

I intentionally included some access problems in the test data so the program has realistic situations to find.

Examples include a terminated employee who still has active application access and a highly privileged service account that is still owned by a terminated employee.

## Running the Project

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Generate a new set of example data:

```bash
python main.py generate
```

Create the User Access Review:

```bash
python main.py campaign
```

The program will evaluate the access records, calculate their risk, assign reviewers, and create the review campaign.

## Recording a Review Decision

A review decision can be recorded from the command line.

For example:

```bash
python main.py decide --item-id H-A0001 --reviewer "Dane Shuler" --decision REVOKE --justification "User is terminated."
```

This records who made the decision, what they decided, why they made the decision, and the risk information associated with the access.

If the decision requires additional action, it is also added to the remediation queue.

## Project Files

### `data/employees.csv`

Contains the employee information used by the program, including names, job titles, departments, managers, employment status, and employment dates.

### `data/applications.csv`

Contains information about the applications being reviewed, including the application owner, importance of the application, and review requirements.

### `data/saviynt_access.csv`

Represents employee access information that could come from an identity management platform such as Saviynt.

It includes accounts, applications, roles, permissions, risk levels, SOX-related access, and recent login information.

### `data/oasis_nhi.csv`

Represents service accounts and other non-human accounts that could be managed through a platform such as Oasis.

It includes account ownership, environment, privilege level, recent usage, credential age, and whether credentials need to be rotated.

### `src/generate_data.py`

Creates all of the example employees, access assignments, applications, and service accounts used to test the project.

### `src/risk_engine.py`

Checks each access record for potential concerns and assigns a risk score.

It also records the reasons behind the score so reviewers can understand why something was flagged instead of only seeing a number.

### `src/campaign.py`

Combines the different sources of information and creates the actual User Access Review.

It also determines who should review each access item and provides a recommended action when an obvious issue is found.

### `src/review.py`

Handles reviewer decisions.

It records the decision and justification, maintains the audit history, and sends items requiring additional action to the remediation queue.

### `src/connectors.py`

Represents how the program communicates with its different data sources.

The current project reads from CSV files, but these connectors could eventually be replaced with integrations that retrieve information directly from platforms such as Saviynt, Oasis, an HR system, or other identity sources.

### `config.json`

Contains the risk rules and scoring values.

Keeping these settings separate from the main program makes it easier to adjust how different situations are prioritized without rewriting the rest of the program.

### `main.py`

The main entry point for running the project.

It can generate example data, create a User Access Review campaign, and record review decisions.

## Risk Scoring

The risk scoring is meant to help reviewers prioritize what deserves attention first.

For example, a normal active employee with standard access may receive little or no additional risk, while a terminated employee who still has active high-risk access would be pushed to the top of the review.

The score does not automatically decide whether access should remain or be removed. The final decision is still made by a reviewer.

The scoring values used in this project are examples that I created for the proof of concept. 

## Audit and Remediation

Every completed review keeps track of information such as:

- Who reviewed the access
- What decision they made
- Why they made the decision
- The risk level at the time of review
- The reasons the access was flagged
- When the decision was made

Items marked for removal, modification, or escalation are placed into a separate remediation queue.

The current version does not make changes to real systems. Any future integration with an identity platform would include additional validation and safeguards before making access changes.

## Testing

The included tests can be run with:

```bash
pytest -q
```

The tests currently verify important scenarios such as detecting active access belonging to a terminated employee and identifying a high-risk service account with a terminated owner.

## Future Improvements

This is currently a proof of concept, but some of the next improvements I would like to explore include:

- A web interface where managers can complete their access reviews
- Email notifications when a review is assigned
- Reminders for overdue reviews
- Additional approval requirements for high-risk or SOX access
- Separation of Duties checks
- Direct integrations with identity platforms instead of CSV files
- Verification that requested access removals were actually completed
- Reporting for review completion, outstanding risks, and remediation status