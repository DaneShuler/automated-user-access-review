# Automated User Access Review (UAR) Proof of Concept

> **Important:** Every identity, application, access assignment, policy, and record in this repository is made up. 

## Workflow

HR + Human IGA + NHI + Application Context -> Normalization -> Risk Engine -> UAR Campaign -> Human Decision -> Remediation Queue -> Audit Evidence

## Included

- 50 synthetic employees
- 200 synthetic human access assignments
- 40 synthetic non-human identities
- Deliberately planted terminated-user and orphaned-service-account exceptions
- Transparent configurable risk scoring
- Reviewer assignment
- CERTIFY / REVOKE / MODIFY / ESCALATE decisions
- Separate remediation queue
- Audit logging
- Mock connector classes
- Dry-run remediation design
- Unit tests

## Run

```bash
pip install -r requirements.txt
python main.py generate
python main.py campaign
```

Record a review decision:

```bash
python main.py decide --item-id H-A0001 --reviewer "Manager User" --decision REVOKE --justification "User is terminated."
```

Run tests:

```bash
pytest -q
```

## Files

- `data/employees.csv`: workforce source
- `data/applications.csv`: application ownership and review context
- `data/saviynt_access.csv`: human accounts and entitlements
- `data/oasis_nhi.csv`: service accounts, service principals, API keys, ownership, privilege, usage, and credential posture
- `src/connectors.py`: mock integration adapters
- `src/risk_engine.py`: explainable risk rules
- `src/campaign.py`: normalization, reviewer assignment, and campaign generation
- `src/review.py`: decisions, remediation queue, and audit evidence
- `src/generate_data.py`: reproducible dataset generator
- `config.json`: demonstration risk policy
- `main.py`: command-line entry point

## Security design choices

Risk scores prioritize review but never certify access automatically. Certification is intentionally separated from remediation. REVOKE/MODIFY/ESCALATE decisions enter a queue instead of making destructive changes. Real API connectors could replace the CSV adapters later.

The scoring values are demonstration policies, not claimed industry-standard thresholds.
