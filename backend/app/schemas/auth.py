from typing import List
from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: int
    login_name: str
    name: str
    role: str
    capabilities: List[str]

class RoleSwitchRequest(BaseModel):
    role: str
