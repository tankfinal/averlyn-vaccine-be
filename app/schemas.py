from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class VaccineRead(BaseModel):
    id: str
    name: str
    name_en: str
    subtitle: Optional[str] = None
    type: str
    done: bool
    done_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    price: Optional[int] = None
    description: str
    side_effects: Optional[str] = None
    notes: Optional[str] = None
    display_order: int
    updated_at: datetime
    created_at: datetime


class VaccineUpdate(BaseModel):
    done: bool
    done_date: Optional[date] = None


class BabyRead(BaseModel):
    id: int
    name: str
    birth_date: date
