"""Schemas for admin login and analytics."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminUserOut(BaseModel):
    id: int = 1
    email: str
    name: str = "Admin"
    last_name: str = "TECBA"
    role_id: int = 99
    position: str = "Administrador"


class AdminLoginResponse(BaseModel):
    token: str
    user: AdminUserOut


class CountBucket(BaseModel):
    key: str
    label: Optional[str] = None
    count: int


class AdminStatsSummary(BaseModel):
    total: int
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    by_activity: list[CountBucket] = Field(default_factory=list)
    by_commune: list[CountBucket] = Field(default_factory=list)
    by_neighborhood: list[CountBucket] = Field(default_factory=list)
    by_status: list[CountBucket] = Field(default_factory=list)
    by_day: list[CountBucket] = Field(default_factory=list)
    by_zoning_mixtura: list[CountBucket] = Field(default_factory=list)
    by_rubro_allowed: list[CountBucket] = Field(default_factory=list)


class AdminConsultationItem(BaseModel):
    id: str
    created_at: datetime
    status: str
    data_status_overall: Optional[str] = None
    activity_code: Optional[str] = None
    activity_name: Optional[str] = None
    original_query: Optional[str] = None
    commune: Optional[str] = None
    neighborhood: Optional[str] = None
    normalized_address: Optional[str] = None
    zoning_mixtura: Optional[str] = None
    zoning_rubro_allowed: Optional[bool] = None
    message: Optional[str] = None


class AdminConsultationList(BaseModel):
    total: int
    items: list[AdminConsultationItem]
