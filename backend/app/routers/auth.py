from fastapi import APIRouter, Depends
from typing import Optional, List, Dict, Any
from app.core.rbac import ROLES_CONFIG, get_current_user, ROLE_CAPABILITIES, USER_OF_ROLE, CurrentUser

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

@router.get("/roles")
async def get_roles():
    return {
        "roles": ROLES_CONFIG,
        "capabilities": ROLE_CAPABILITIES,
        "role_users": USER_OF_ROLE,
    }

@router.get("/me")
async def get_current_user_profile(
    user: CurrentUser = Depends(get_current_user)
):
    return {
        "user_id": user.user_id,
        "role": user.role,
        "name": user.name,
        "login_name": user.login_name,
    }
