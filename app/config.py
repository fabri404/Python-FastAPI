import os
from pathlib import Path
from dotenv import load_dotenv

# === CONFIGURACIÓN BASE ===
BASE_DIR = Path(__file__).resolve().parent.parent  # app/.. = raíz del proyecto
ENV_PATH = BASE_DIR / ".env"

# Cargar variables desde .env
load_dotenv(ENV_PATH)

# === VARIABLES DE ENTORNO ===
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    raise ValueError("IG_USERNAME e IG_PASSWORD deben estar definidos en .env")

# Navegador: por defecto Chrome estable
DEFAULT_CHROME_BINARY = "/usr/bin/google-chrome-stable"
CHROME_BINARY = os.getenv("CHROME_BINARY", DEFAULT_CHROME_BINARY)

# Base de datos: obligatorio Postgres (o MySQL, pero sin fallback a SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL debe estar definido en .env (Postgres recomendado)")

print("DEBUG CONFIG:")
print(f"  IG_USERNAME={IG_USERNAME}")
print(f"  CHROME_BINARY={CHROME_BINARY}")
print(f"  DATABASE_URL={DATABASE_URL}")
