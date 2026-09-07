from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class TerritorialAreaView(BaseModel):
    area_id: str
    area_type: str
    official_name: str
    version: int
    version_id: str
    legal_device: str
    criteria: dict[str, Any]
    valid_from: date
    valid_to: date | None
