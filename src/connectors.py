from pathlib import Path

import pandas as pd


class CSVConnector:
    """
    Base connector used by the proof of concept.

    The project uses CSV files as stand-ins for data that could come
    from real identity, HR, or application systems through APIs or
    other integrations.
    """

    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        """Read the connector's synthetic source data."""
        return pd.read_csv(self.path)


class HRConnector(CSVConnector):
    """
    Provides employee information used during access reviews.

    In a production environment, this could be replaced with an
    integration to the organization's HR or workforce system.
    """

    def get_employees(self):
        return self.read()


class SaviyntConnector(CSVConnector):
    """
    Provides human identity and access information.

    The CSV used in this proof of concept represents access data that
    could be retrieved from Saviynt. This connector is intentionally
    simple and does not attempt to recreate Saviynt's native access
    review or certification functionality.
    """

    def get_access(self):
        return self.read()

    def create_remediation(
        self,
        identity,
        entitlement,
        dry_run=True
    ):
        """
        Demonstrate where a remediation request could be sent to an
        identity platform after an access review decision.

        No real access changes are performed by this project.
        """

        action = f"revoke {entitlement} from {identity}"

        if dry_run:
            return f"[DRY RUN] Would {action}"

        return f"[SIMULATED] {action}"


class OasisConnector(CSVConnector):
    """
    Provides synthetic service account and other non-human identity
    information.

    The CSV represents the type of ownership and account information
    that could come from a non-human identity management platform.
    """

    def get_non_human_identities(self):
        return self.read()

    def create_remediation(
        self,
        identity,
        action,
        dry_run=True
    ):
        """
        Demonstrate where remediation for a service account or other
        non-human identity could be requested.

        No real identity changes are performed by this project.
        """

        remediation = f"{action} for {identity}"

        if dry_run:
            return f"[DRY RUN] Would {remediation}"

        return f"[SIMULATED] {remediation}"


class ApplicationConnector(CSVConnector):
    """
    Provides application ownership and review information.

    Application metadata is used to help determine review context
    and assign the appropriate reviewer.
    """

    def get_applications(self):
        return self.read()
