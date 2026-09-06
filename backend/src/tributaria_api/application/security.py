from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tributaria_api.application.errors import AuthorizationError


class Role(StrEnum):
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    CURATOR = "CURATOR"
    APPROVER = "APPROVER"
    PUBLISHER = "PUBLISHER"
    ADMIN = "ADMIN"


class Permission(StrEnum):
    READ = "READ"
    RUN_EVALUATION = "RUN_EVALUATION"
    CURATE_RULE = "CURATE_RULE"
    APPROVE_RULE = "APPROVE_RULE"
    PUBLISH_RULE = "PUBLISH_RULE"
    MANAGE_COMPANY = "MANAGE_COMPANY"
    MANAGE_MEMBERSHIP = "MANAGE_MEMBERSHIP"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({Permission.READ}),
    Role.ANALYST: frozenset({Permission.READ, Permission.RUN_EVALUATION}),
    Role.CURATOR: frozenset({Permission.READ, Permission.CURATE_RULE}),
    Role.APPROVER: frozenset({Permission.READ, Permission.APPROVE_RULE}),
    Role.PUBLISHER: frozenset({Permission.READ, Permission.PUBLISH_RULE}),
    Role.ADMIN: frozenset(
        {Permission.READ, Permission.MANAGE_COMPANY, Permission.MANAGE_MEMBERSHIP}
    ),
}


@dataclass(frozen=True, slots=True)
class AuthContext:
    session_id: str
    user_id: str
    email: str
    display_name: str
    organization_id: str
    organization_name: str
    membership_id: str
    role: Role

    @property
    def permissions(self) -> frozenset[Permission]:
        return ROLE_PERMISSIONS[self.role]

    def require(self, permission: Permission) -> None:
        if permission not in self.permissions:
            raise AuthorizationError("Insufficient permission")
