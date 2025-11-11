# app/api/models.py
from typing import List, Optional
from pydantic import BaseModel


class SendRequest(BaseModel):
    recipients: List[str]
    messages: List[str]
    attachments: Optional[List[str]] = None


class SendResponse(BaseModel):
    success: bool
    detail: str
