# 📘 Instagram Direct Bot — Documentación Técnica

> Objetivo: Automatizar el envío de mensajes de Instagram Direct a uno o varios usuarios, exponiendo una API REST con FastAPI y una UI de escritorio con Flet, utilizando Selenium + ChromeDriver para controlar el navegador y PostgreSQL para persistir información de los chats.
> 

---

## 0. Inicio rápido — paso a paso (de 0 a bot funcionando)

### 0.1 Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd <carpeta_del_repo>

```

### 0.2 Crear entorno virtual e instalar dependencias de Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

### 0.3 Instalar PostgreSQL (si no lo tienes)

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib

```

### 0.4 Crear base de datos y usuario (ajusta credenciales propias)

```bash
sudo -u postgres psql -c "CREATE USER YOUR_DB_USER WITH PASSWORD 'YOUR_DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE instagram_bot OWNER YOUR_DB_USER;"

```

### 0.5 Crear archivo `.env` a partir del ejemplo

```bash
cp .env.example .env

```

Editar `.env` con tus valores:

```
IG_USERNAME=YOUR_IG_USERNAME
IG_PASSWORD=YOUR_IG_PASSWORD

CHROME_BINARY=/usr/bin/google-chrome-stable

DATABASE_URL=postgresql+psycopg2://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot

```

### 0.6 Instalar Google Chrome (desde `.deb` oficial, si no lo tienes)

```bash
cd ~/Descargas
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt -f install
which google-chrome-stable

```

### 0.7 Instalar ChromeDriver (compatible con tu versión de Chrome)

```bash
chmod +x chromedriver
sudo mv chromedriver /usr/local/bin/chromedriver
chromedriver --version

```

### 0.8 Levantar ChromeDriver (terminal 1)

```bash
chromedriver --port=9515

```

### 0.9 Levantar la API FastAPI (terminal 2)

```bash
cd <carpeta_del_repo>
source .venv/bin/activate
python main.py

```

La API queda disponible en:

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

### 0.10 Levantar la UI Flet (terminal 3, opcional)

```bash
cd <carpeta_del_repo>
source .venv/bin/activate
python ui_flet.py

```

---

## 1. Introducción conceptual

### 1.1 ¿Qué hace esta aplicación?

La aplicación **automatiza el envío de mensajes por Instagram Direct** a uno o varios usuarios.

Proporciona:

- Una **API REST** (FastAPI) para disparar el proceso desde HTTP (Swagger, scripts, etc.).
- Una **interfaz gráfica** con Flet para cargar destinatarios, mensajes y archivos.
- Un motor de automatización basado en **Selenium + ChromeDriver**, que controla el navegador y ejecuta las acciones en Instagram como si fuera un usuario humano.

### 1.2 Componentes principales

- **FastAPI**
    
    Expone el endpoint:
    
    - `POST /api/send` que recibe un payload con:
        - `recipients`: lista de usernames o `thread_id`.
        - `messages`: lista de textos a enviar.
        - `attachments`: rutas de archivos (en desarrollo desde la UI).
- **Selenium + ChromeDriver**
    - Inicia sesión en Instagram usando `IG_USERNAME` / `IG_PASSWORD`.
    - Usa URLs directas hacia los chats (por ejemplo `https://ig.me/m/<username>` y `https://www.instagram.com/direct/t/<thread_id>/`), evitando depender de hacer clic en todos los elementos de la UI.
- **PostgreSQL + SQLAlchemy**
    - Mantiene una tabla `threads` donde se guarda:
        - `username` (ej. `usuario` sin `@`).
        - `thread_id` del chat.
        - contador de mensajes enviados (`messages_sent`).
- **Flet**
    - UI de escritorio para:
        - Cargar destinatarios.
        - Escribir mensajes.
        - Disparar el endpoint del backend desde un formulario.

### 1.3 Flujo general

1. Login en Instagram (una vez al inicio de la ejecución).
2. Para cada destinatario:
    - Si se recibe un **username**:
        - Se busca primero en la tabla `threads`.
        - Si no existe, se abre `https://ig.me/m/<username>` para que Instagram cree/abra el chat.
        - Se extrae el `thread_id` de la URL final y se guarda en la base.
    - Si se recibe directamente un **`thread_id` numérico**, se usa tal cual.
3. Se navega a `https://www.instagram.com/direct/t/<thread_id>/`.
4. Se cierra el popup “Turn on Notifications” haciendo clic en **“Not Now”**.
5. Se localiza el área de texto del chat y se envían los mensajes.
6. Se actualiza el contador `messages_sent` en la tabla `threads`.

---

## 2. Requisitos del sistema

### 2.1 Sistema operativo

- Linux (Ubuntu, Zorin u otra distribución basada en Debian).

### 2.2 Software necesario

- **Python 3.11+**
- **PostgreSQL 14+** (servidor y cliente `psql`)
- **Google Chrome** instalado desde paquete `.deb`.
- **ChromeDriver** compatible con la versión de Chrome instalada.
- **Git** (para clonar el repositorio).

---

## 3. Instalación (paso a paso)

### 3.1 Clonado y entorno Python

```bash
git clone <URL_DEL_REPO>
cd <carpeta_del_repo>

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

### 3.2 PostgreSQL: instalación y creación de base

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
psql --version

```

Crear usuario y base (ajusta nombres propios):

```bash
sudo -u postgres psql -c "CREATE USER YOUR_DB_USER WITH PASSWORD 'YOUR_DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE instagram_bot OWNER YOUR_DB_USER;"

```

Probar conexión:

```bash
psql postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot

```

### 3.3 Archivo `.env`

```bash
cp .env.example .env

```

Editar con tus datos:

```
IG_USERNAME=YOUR_IG_USERNAME
IG_PASSWORD=YOUR_IG_PASSWORD

CHROME_BINARY=/usr/bin/google-chrome-stable

DATABASE_URL=postgresql+psycopg2://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot

```

### 3.4 Chrome y ChromeDriver

Instalar Chrome desde el `.deb` descargado:

```bash
cd ~/Descargas
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt -f install
which google-chrome-stable

```

Instalar ChromeDriver:

```bash
chmod +x chromedriver
sudo mv chromedriver /usr/local/bin/chromedriver
chromedriver --version

```

### 3.5 Arranque

**Terminal 1 (ChromeDriver):**

```bash
chromedriver --port=9515

```

**Terminal 2 (API):**

```bash
cd <carpeta_del_repo>
source .venv/bin/activate
python main.py

```

**Terminal 3 (UI Flet, opcional):**

```bash
cd <carpeta_del_repo>
source .venv/bin/activate
python ui_flet.py

```

---

## 4. Configuración de la aplicación

### 4.1 Variables principales (archivo `.env`)

- `IG_USERNAME`: usuario de Instagram que se usará para iniciar sesión.
- `IG_PASSWORD`: contraseña de Instagram.
- `CHROME_BINARY`: ruta al ejecutable de Chrome en Linux.
- `DATABASE_URL`: cadena de conexión a PostgreSQL, formato:

```
postgresql+psycopg2://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot

```

### 4.2 Carga de configuración

El módulo `app.config`:

- Lee el archivo `.env`.
- Valida la existencia de `IG_USERNAME`, `IG_PASSWORD` y `DATABASE_URL`.
- Configura la ruta de `CHROME_BINARY` para Selenium.

---

## 5. Esquema de base de datos y comandos útiles (psql)

### 5.1 Tabla `threads` (modelo simplificado)

La aplicación crea una tabla equivalente a:

```sql
CREATE TABLE IF NOT EXISTS threads (
  id SERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  thread_id TEXT NOT NULL UNIQUE,
  messages_sent INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

```

Uso de columnas:

- `username`: nombre de usuario de Instagram (normalizado, sin `@`).
- `thread_id`: identificador del chat (parte numérica de la URL `/direct/t/...`).
- `messages_sent`: contador simple de mensajes enviados a ese usuario.

### 5.2 Comandos útiles (psql)

Probar conexión a la base:

```bash
psql postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot -c "SELECT now();"

```

Ver la tabla `threads`:

```bash
psql postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot -c "\d+ threads"

```

Ver últimos registros:

```bash
psql postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/instagram_bot -c "SELECT * FROM threads ORDER BY id DESC LIMIT 10;"

```

---

## 6. Endpoints y ejemplos

### 6.1 Rutas

- `POST /api/send` — envía mensajes a uno o varios destinatarios.

### 6.2 Ejemplo con `curl` (envío simple)

```bash
curl -X POST "http://127.0.0.1:8000/api/send" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["@usuario1", "@usuario2"],
    "messages": ["Hola, este es un mensaje automatizado"],
    "attachments": []
  }'

```

Respuesta esperada (`200 OK`):

```json
{
  "success": true,
  "detail": "Mensajes enviados correctamente."
}

```

### 6.3 Uso desde Swagger

1. Abrir `http://127.0.0.1:8000/docs`.
2. Seleccionar `POST /api/send`.
3. Click en **Try it out**.
4. Completar el JSON con tus destinatarios y mensajes.
5. Ejecutar con **Execute** para disparar la automatización.

---

## 7. Estructura de proyecto — qué hay en cada carpeta y por qué

> Objetivo: alta cohesión y bajo acoplamiento. Cada módulo tiene una responsabilidad clara para facilitar mantenimiento y evolución.
> 

### 7.1 Estructura básica

```
.
├─ main.py                  # Punto de entrada de la API (inicia FastAPI/Uvicorn)
├─ ui_flet.py               # Frontend Flet (formulario gráfico)
├─ app/
│  ├─ __init__.py
│  ├─ api/
│  │  ├─ main.py            # Crea instancia de FastAPI y monta el router
│  │  └─ routes.py          # Define el endpoint /api/send
│  ├─ core/
│  │  └─ instagram_bot.py   # Lógica Selenium: login, ig.me, thread_id, envío
│  ├─ db.py                 # SQLAlchemy: engine, SessionLocal, Base
│  ├─ models.py             # Modelo Thread (username, thread_id, stats)
│  └─ config.py             # Carga de .env y variables de configuración
├─ requirements.txt         # Dependencias de Python del proyecto
├─ .env.example             # Plantilla de configuración de entorno
└─ README.md                # Documentación técnica

```

### 7.2 Responsabilidades por módulo

- `app/api/`
    
    Capa HTTP (FastAPI); solo recibe requests, valida y delega en la lógica del bot.
    
- `app/core/`
    
    Lógica de negocio y automatización con Selenium (login, navegación, envío de mensajes).
    
- `app/db.py` y `app/models.py`
    
    Capa de persistencia con SQLAlchemy + PostgreSQL.
    
- `ui_flet.py`
    
    Interfaz de usuario para no depender únicamente de Swagger o `curl`.
    

---

## 8. Futuras mejoras

Algunas ideas para siguientes iteraciones del proyecto:

### 8.1 Adjuntos completos desde UI

- Terminar y robustecer el flujo de adjuntar imágenes/archivos directamente desde Flet.
- Manejar tamaños máximos, tipos de archivo permitidos y errores de carga.

### 8.2 Manejo de desafíos de seguridad de Instagram

- Soporte para 2FA, códigos de seguridad o flujos de verificación adicionales.
- Detección de bloqueos temporales y reintentos controlados.

### 8.3 Pruebas automatizadas (`pytest`)

- Tests para la lógica de obtención de `thread_id`.
- Tests para normalización de usernames.
- Tests de integración simulando respuestas de la API de FastAPI.

### 8.4 Contenedores Docker

- Dockerizar:
    - API FastAPI.
    - PostgreSQL.
    - Chrome + ChromeDriver (por ejemplo, imagen Selenium standalone).
- Añadir `docker-compose.yml` para levantar todo el entorno con un solo comando.

### 8.5 Panel de estadísticas

- Endpoint o vista para ver:
    - Cuántos mensajes se enviaron por usuario.
    - Qué cuentas ya tienen `thread_id` guardado.
    - Historial básico de envíos.

---

## 9. Consideraciones de uso y seguridad

- **Nunca** incluyas credenciales reales en el repositorio.
    - Usa siempre el archivo `.env` local y no lo subas a Git.
- Las credenciales de Instagram (`IG_USERNAME` y `IG_PASSWORD`) deben ser propias de quien ejecute la herramienta.
- Respetar siempre los **Términos y Condiciones de Instagram**:
    - No hacer spam.
    - No automatizar acciones en cuentas que no te hayan autorizado.
    - No usar el bot con fines maliciosos.
- El proyecto está pensado para:
    - **Aprendizaje**.
    - **Demostración técnica**.
    - **Uso controlado** en contexto de portfolio.
