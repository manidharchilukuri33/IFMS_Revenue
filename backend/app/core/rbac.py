from typing import Optional, Dict, Any, List
from fastapi import Header, Depends, Request
from app.core.exceptions import WorkflowPermissionException

# Master capabilities definition matching the functional prototype
ROLE_CAPABILITIES: dict[str, list[str]] = {
    'nav.dashboard': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.collection': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.upload': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'BANK_OPS', 'AUDITOR'],
    'nav.recon': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR'],
    'nav.exceptions': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.sla': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.refund': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR', 'CITIZEN'],
    'nav.devolution': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR'],
    'nav.accounting': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'FINANCE', 'AUDITOR'],
    'nav.reports': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.masters': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.audit': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'nav.help': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR', 'CITIZEN'],
    
    # Specific Functional Action Capabilities
    'upload.portal': ['PAO_MAKER', 'DDO', 'TRE_ADMIN', 'SYSADMIN'],
    'upload.bank': ['PAO_MAKER', 'BANK_OPS', 'TRE_ADMIN', 'SYSADMIN'],
    'upload.rbi': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'batch.approve': ['PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    'batch.delete': ['SYSADMIN', 'TRE_ADMIN'],
    
    'collection.create': ['PAO_MAKER', 'DDO', 'TRE_ADMIN', 'SYSADMIN'],
    'collection.edit': ['PAO_MAKER', 'DDO', 'SYSADMIN'],
    'dept.validate': ['DDO', 'PAO_MAKER', 'SYSADMIN'],
    
    'recon.run': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'recon.commit': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'recon.reset': ['TRE_ADMIN', 'SYSADMIN'],
    'override.propose': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'override.approve': ['PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    
    'exception.manage': ['PAO_MAKER', 'PAO_CHECK', 'TRE_ADMIN', 'DDO', 'SYSADMIN'],
    'exception.escalate': ['PAO_MAKER', 'PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    
    'penalty.letter': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'penalty.response': ['BANK_OPS', 'PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'penalty.waive': ['PAO_CHECK', 'TRE_ADMIN', 'FINANCE', 'SYSADMIN'],
    
    'refund.create': ['DDO', 'PAO_MAKER', 'CITIZEN', 'TRE_ADMIN', 'SYSADMIN'],
    'refund.process': ['DDO', 'PAO_MAKER', 'FINANCE', 'TRE_ADMIN', 'SYSADMIN'],
    'refund.approve': ['PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    'refund.pay': ['PAO_MAKER', 'PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    
    'devolution.create': ['DDO', 'PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'devolution.approve': ['PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    'devolution.pay': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    
    'voucher.create': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
    'voucher.approve': ['PAO_CHECK', 'TRE_ADMIN', 'SYSADMIN'],
    
    'masters.edit': ['SYSADMIN', 'TRE_ADMIN'],
    'config.edit': ['SYSADMIN', 'TRE_ADMIN'],
    'bizdate.edit': ['SYSADMIN', 'TRE_ADMIN'],
    'data.reset': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'],
    'export': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
    'testsuite.run': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK']
}

# Standard demo user identities mapped to roles
USER_ROLE_MAPPING: dict[str, dict] = {
    'SYSADMIN': {'user_id': 1, 'name': 'System Administrator', 'login_name': 'admin'},
    'PAO_MAKER': {'user_id': 2, 'name': 'Rajesh Kumar (PAO-21 Maker)', 'login_name': 'budget_maker'},
    'PAO_CHECK': {'user_id': 3, 'name': 'Dr. Meera Sharma (PAO-21 Checker)', 'login_name': 'budget_reviewer'},
    'DDO': {'user_id': 4, 'name': 'S. K. Verma (Trade & Taxes DDO)', 'login_name': 'admin_secretary'},
    'FINANCE': {'user_id': 6, 'name': 'Amit Bansal (Finance Dept Reviewer)', 'login_name': 'finance_reviewer'},
    'TRE_ADMIN': {'user_id': 7, 'name': 'R. K. Singh (Director / Treasury Admin)', 'login_name': 'director_budget'},
    'BANK_OPS': {'user_id': 9, 'name': 'Nisha Arora (SBI Focal Point Ops)', 'login_name': 'budget_controller'},
    'AUDITOR': {'user_id': 11, 'name': 'Internal Auditor (CAG Liaison)', 'login_name': 'auditor'},
    'CITIZEN': {'user_id': 99, 'name': 'Public Citizen User', 'login_name': 'citizen_portal'}
}

ROLES_CONFIG = [
    {"role": k, "user_id": v["user_id"], "name": v["name"], "login_name": v["login_name"]}
    for k, v in USER_ROLE_MAPPING.items()
]
USER_OF_ROLE = {k: v["user_id"] for k, v in USER_ROLE_MAPPING.items()}

class CurrentUser:
    def __init__(self, user_id: int, role: str, name: str, login_name: str):
        self.user_id = user_id
        self.role = role.upper()
        self.name = name
        self.login_name = login_name

    def can(self, capability: str) -> bool:
        allowed_roles = ROLE_CAPABILITIES.get(capability, [])
        return self.role in allowed_roles

def get_current_user(request: Request) -> CurrentUser:
    role_header = request.headers.get("X-User-Role") or request.headers.get("X-IFMS-Role") or "TRE_ADMIN"
    user_id_header = request.headers.get("X-User-Id") or request.headers.get("X-IFMS-User-Id")
    
    role = role_header.upper()
    user_info = USER_ROLE_MAPPING.get(role, USER_ROLE_MAPPING.get('TRE_ADMIN', {'user_id': 1, 'name': 'Admin', 'login_name': 'admin'}))
    
    user_id = int(user_id_header) if user_id_header and user_id_header.isdigit() else user_info['user_id']
    return CurrentUser(
        user_id=user_id,
        role=role,
        name=user_info['name'],
        login_name=user_info['login_name']
    )

def require_capability(capability: str):
    def dependency(user: CurrentUser = Depends(get_current_user)):
        if not user.can(capability):
            allowed = ROLE_CAPABILITIES.get(capability, [])
            raise WorkflowPermissionException(action=capability, current_role=user.role, required_roles=allowed)
        return user
    return dependency
