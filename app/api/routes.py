# app/api/routes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.instagram_bot import (
    crear_driver,
    login_ig,
    enviar_mensajes,
    InstagramBotError,
)

# El prefijo "/api" hace que el endpoint sea /api/send
router = APIRouter(prefix="/api", tags=["instagram"])


class SendRequest(BaseModel):
    recipients: List[str]
    messages: List[str]
    attachments: List[str] = []


class SendResponse(BaseModel):
    success: bool
    detail: str


@router.post("/send", response_model=SendResponse)
def send(payload: SendRequest, db: Session = Depends(get_db)) -> SendResponse:
    """
    Endpoint principal: recibe destinatarios, mensajes y adjuntos,
    y delega en el bot de Instagram.
    """
    driver = crear_driver()  # 👈 acá creamos el driver

    try:
        # Login en Instagram
        login_ig(driver)

        # Llamamos a enviar_mensajes con TODOS los parámetros nombrados
        enviar_mensajes(
            db=db,
            driver=driver,                          # 👈 ESTE era el que faltaba
            cuentas_destinatarias=payload.recipients,
            mensajes=payload.messages,
            archivos=payload.attachments,
        )

        return SendResponse(success=True, detail="Mensajes enviados correctamente.")
    except InstagramBotError as e:
        # Errores “esperados” del bot (por ej. ig.me no devuelve thread_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Errores inesperados
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
    finally:
        driver.quit()
