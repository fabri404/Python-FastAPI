# app/api/models.py
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_serializer


# ---------- Requests / Responses existentes ----------
class SendRequest(BaseModel):
    recipients: List[str]
    messages: List[str]
    attachments: Optional[List[str]] = None


class SendResponse(BaseModel):
    success: bool
    detail: str


# ---------- Modelo de salida con fechas formateadas ----------
_TZ = ZoneInfo("America/Argentina/Cordoba")
_FMT = "%d/%m/%Y %H:%M"  # dd/mm/yyyy HH:MM (24h)

class ThreadOut(BaseModel):
    id: int
    username: str
    thread_id: str
    messages_sent: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None
        # Si viene naive, se asume horario local; si viene con tz, se normaliza a Córdoba
        dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
        return dt.strftime(_FMT)


class ThreadsResponse(BaseModel):
    items: List[ThreadOut]


class StatsResponse(BaseModel):
    total_threads: int
    total_messages_sent: int
