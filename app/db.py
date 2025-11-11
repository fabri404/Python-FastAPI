from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# Para Postgres / MySQL / etc. no necesitamos connect_args especiales
engine = create_engine(
    DATABASE_URL,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia para FastAPI: abre y cierra sesión de BD por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
