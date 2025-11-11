from sqlalchemy import Column, Integer, String, DateTime, func
from app.db import Base


class Thread(Base):
    """
    Mapea un username de Instagram a un thread_id de Direct.
    También guarda algo de metadata básica para estadísticas.
    """
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    thread_id = Column(String(255), unique=True, index=True, nullable=False)

    messages_sent = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
