# app/api/routes.py
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.models import (
    SendRequest,
    SendResponse,
    ThreadOut,
    ThreadsResponse,
    StatsResponse,
)
from app.core.instagram_bot import (
    crear_driver,
    login_ig,
    enviar_mensajes,
    InstagramBotError,
)
from app.db import SessionLocal
from app.models import Thread


router = APIRouter(prefix="/api", tags=["instagram-bot"])


# ------------------- Dependencia DB -------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------- POST /api/send -------------------
@router.post("/send", response_model=SendResponse)
def send_messages(payload: SendRequest, db: Session = Depends(get_db)) -> SendResponse:
    try:
        driver = crear_driver()
        try:
            login_ig(driver)
            enviar_mensajes(
                db=db,
                driver=driver,
                cuentas_destinatarias=payload.recipients,
                mensajes=payload.messages,
                archivos=payload.attachments or [],
            )
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        return SendResponse(success=True, detail="Mensajes enviados correctamente.")
    except InstagramBotError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# ------------------- GET /api/threads -------------------
@router.get("/threads", response_model=ThreadsResponse)
def list_threads(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Filtro por username (substring, sin @)"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Orden por messages_sent"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ThreadsResponse:
    query = db.query(Thread)

    if q:
        q_norm = q.strip().lstrip("@").lower()
        query = query.filter(Thread.username.ilike(f"%{q_norm}%"))

    order_by = Thread.messages_sent.desc() if order == "desc" else Thread.messages_sent.asc()

    items = (
        query.order_by(order_by, Thread.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # La respuesta ahora NO incluye total/limit/offset; solo items con fechas ya formateadas
    return ThreadsResponse(items=items)


# ------------------- GET /api/stats -------------------
@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)) -> StatsResponse:
    total_threads = db.query(func.count(Thread.id)).scalar() or 0
    total_messages = db.query(func.coalesce(func.sum(Thread.messages_sent), 0)).scalar() or 0
    return StatsResponse(
        total_threads=int(total_threads),
        total_messages_sent=int(total_messages),
    )
