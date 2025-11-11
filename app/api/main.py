# app/api/main.py

from fastapi import FastAPI

from app.db import Base, engine
from app import models             
from app.api.routes import router as api_router

# Crear tablas en BD al arrancar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Instagram Automation API",
    version="1.0.0",
)

app.include_router(api_router)      
