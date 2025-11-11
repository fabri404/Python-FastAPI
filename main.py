# main.py (en /home/adriel/Documentos/ADRIEL/Python-FastAPI)

from app.api.main import app  # aquí está tu instancia de FastAPI


if __name__ == "__main__":
    import uvicorn

    # "main:app" = módulo main.py (este archivo) y variable app
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
