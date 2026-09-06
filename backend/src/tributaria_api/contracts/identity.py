from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tributaria_api.application.security import Role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)
    organization_slug: str = Field(min_length=1, max_length=100)


class CurrentUserView(BaseModel):
    user_id: str
    email: str
    display_name: str
    organization_id: str
    organization_name: str
    membership_id: str
    role: Role
    permissions: list[str]


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_name: str = Field(min_length=1, max_length=300)
    trade_name: str | None = Field(default=None, max_length=300)
    tax_id: str = Field(pattern=r"^[0-9]{14}$")

    @field_validator("legal_name")
    @classmethod
    def legal_name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("legal_name must not be blank")
        return value.strip()


class CompanyStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ACTIVE", "INACTIVE"]


class CompanyView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    legal_name: str
    trade_name: str | None
    tax_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class EstablishmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tax_id: str = Field(pattern=r"^[0-9]{14}$")
    name: str = Field(min_length=1, max_length=300)
    state: str = Field(pattern=r"^[A-Z]{2}$")
    municipality: str = Field(min_length=1, max_length=200)


class EstablishmentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    tax_id: str
    name: str
    state: str
    municipality: str
    status: str
    created_at: datetime
    updated_at: datetime


class MembershipUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role | None = None
    status: Literal["ACTIVE", "INACTIVE"] | None = None


class MembershipView(BaseModel):
    id: str
    user_id: str
    email: str
    display_name: str
    role: Role
    status: str
    created_at: datetime
    updated_at: datetime
