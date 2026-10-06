from pathlib import Path
import pandas as pd

class CSVConnector:
    def __init__(self,path): self.path=Path(path)
    def read(self): return pd.read_csv(self.path)

class HRConnector(CSVConnector):
    def get_employees(self): return self.read()

class SaviyntConnector(CSVConnector):
    def get_access(self): return self.read()
    def create_remediation(self,identity,entitlement,dry_run=True):
        msg=f"revoke {entitlement} from {identity}"
        return f"[DRY RUN] Would {msg}" if dry_run else f"SIMULATED: {msg}"

class OasisConnector(CSVConnector):
    def get_non_human_identities(self): return self.read()
    def create_remediation(self,identity,action,dry_run=True):
        msg=f"{action} for {identity}"
        return f"[DRY RUN] Would {msg}" if dry_run else f"SIMULATED: {msg}"

class ApplicationConnector(CSVConnector):
    def get_applications(self): return self.read()
