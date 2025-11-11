# app/core/instagram_bot.py

import os
import time
from typing import List, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sqlalchemy.orm import Session

from app.config import IG_USERNAME, IG_PASSWORD, CHROME_BINARY
from app.models import Thread


class InstagramBotError(Exception):
    """Error específico para el bot de Instagram."""


# ===============================
# Helpers de URL / usernames
# ===============================

def extraer_thread_id_desde_url(url: str) -> str:
    """
    De una URL del estilo:
        https://www.instagram.com/direct/t/101396794596347/
    retorna:
        "101396794596347"
    """
    path = urlparse(url).path  # "/direct/t/101396794596347/"
    partes = [p for p in path.split("/") if p]
    if len(partes) >= 3 and partes[0] == "direct" and partes[1] == "t":
        return partes[2]
    raise ValueError(f"URL de thread no reconocida: {url}")


def limpiar_username(username: str) -> str:
    """Normaliza el username (sin @, lower-case)."""
    return username.strip().lstrip("@").lower()


# ===============================
# Selenium: creación de driver
# ===============================

def crear_driver() -> webdriver.Remote:
    """
    Crea y devuelve una instancia de Chrome conectándose a un ChromeDriver
    que ya está corriendo en http://127.0.0.1:9515

    => ANTES de usar el bot, hay que ejecutar:
       /usr/local/bin/chromedriver --port=9515
    """
    try:
        options = Options()
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if CHROME_BINARY:
            options.binary_location = CHROME_BINARY

        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:9515",
            options=options,
        )
        driver.maximize_window()
        return driver

    except WebDriverException as e:
        raise InstagramBotError(
            f"No se pudo inicializar Chrome/ChromeDriver (RemoteWebDriver): {e}"
        ) from e


# ===============================
# Login IG (optimizado)
# ===============================

def login_ig(
    driver: webdriver.Remote,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """
    Inicia sesión en Instagram con las credenciales indicadas
    o usa IG_USERNAME / IG_PASSWORD desde config.

    IMPORTANTE:
    - No busca botones "Ahora no", ni diálogos extra.
    - Solo espera a que desaparezca la pantalla de login.
    - El resto del flujo (ir al chat) se hace por URL directa.
    """
    username = username or IG_USERNAME
    password = password or IG_PASSWORD

    if not username or not password:
        raise InstagramBotError("Faltan credenciales IG_USERNAME o IG_PASSWORD")

    print("[BOT] Abriendo página de login de Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    wait = WebDriverWait(driver, 25)

    # Campos de login
    entrada_usuario = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    entrada_contra = wait.until(EC.presence_of_element_located((By.NAME, "password")))

    print("[BOT] Escribiendo credenciales...")
    entrada_usuario.clear()
    entrada_usuario.send_keys(username)
    entrada_contra.clear()
    entrada_contra.send_keys(password)
    entrada_contra.send_keys(Keys.ENTER)

    # Esperar a que la URL ya no sea /accounts/login
    print("[BOT] Esperando a que termine el login...")
    try:
        WebDriverWait(driver, 25).until(
            lambda d: "accounts/login" not in d.current_url
        )
    except TimeoutException:
        raise InstagramBotError("Timeout esperando que termine el login de Instagram")

    # Pequeña pausa para que se estabilice la página
    time.sleep(2)
    print(f"[BOT] Login completado. URL actual: {driver.current_url}")


# ===============================
# Popup "Turn on Notifications"
# ===============================

def cerrar_popup_notificaciones(driver, timeout: int = 15) -> None:
    """
    Cierra el popup "Turn on Notifications" haciendo clic en el botón "Not Now".
    Si no aparece, simplemente no hace nada.
    """
    wait = WebDriverWait(driver, timeout)

    xpaths = [
        # Por texto, forma más robusta
        "//button[normalize-space()='Not Now']",
        "//div[@role='button' and normalize-space()='Not Now']",
        # XPath absoluto que viste en DevTools
        "/html/body/div[4]/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]",
    ]

    for xp in xpaths:
        try:
            boton = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            boton.click()
            time.sleep(1)
            print(f"[BOT] Popup 'Turn on Notifications' cerrado con XPath: {xp}")
            return
        except TimeoutException:
            # No apareció con este xpath, probamos el siguiente
            continue
        except Exception as e:
            print(f"[BOT] Error al cerrar popup con xpath {xp}: {e}")
            return

    print("[BOT] Popup 'Turn on Notifications' no apareció o ya estaba cerrado.")


# ===============================
# Resolución de thread_id (ig.me)
# ===============================

def obtener_o_crear_thread_id(
    db: Session,
    driver: webdriver.Remote,
    destinatario: str,
    timeout: int = 15,
) -> str:
    """
    Dado un destinatario:
    - si es solo dígitos => se asume que ya es un thread_id y se devuelve directo.
    - si es username => se busca en BD; si no existe:
        * se abre https://ig.me/m/<username> para que IG cree/abra el hilo
        * se extrae el thread_id desde driver.current_url
        * se guarda en BD para usos futuros
    """
    destinatario = destinatario.strip()
    if not destinatario:
        raise InstagramBotError("Destinatario vacío")

    # Caso 1: ya es un thread_id numérico
    if destinatario.isdigit():
        print(f"[BOT] Destinatario '{destinatario}' tratado como thread_id directo.")
        return destinatario

    username_norm = limpiar_username(destinatario)
    print(f"[BOT] Resolviendo username '{username_norm}' -> thread_id")

    # Caso 2: username -> thread_id en BD
    thread = (
        db.query(Thread)
        .filter(Thread.username == username_norm)
        .first()
    )
    if thread:
        print(f"[BOT] Encontrado en BD: {username_norm} -> {thread.thread_id}")
        return thread.thread_id

    # Caso 3: primera vez -> usamos ig.me para crear/abrir el hilo
    ig_me_url = f"https://ig.me/m/{username_norm}"
    print(f"[BOT] No hay thread en BD, abriendo ig.me: {ig_me_url}")
    driver.get(ig_me_url)

    # Esperar a que IG redirija a /direct/t/<thread_id>/
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "/direct/t/" in d.current_url
        )
    except TimeoutException as e:
        raise InstagramBotError(
            f"No se pudo obtener thread_id para {destinatario} vía ig.me "
            f"(timeout). URL actual: {driver.current_url}"
        ) from e

    current_url = driver.current_url
    print(f"[BOT] URL final tras ig.me: {current_url}")
    thread_id = extraer_thread_id_desde_url(current_url)
    print(f"[BOT] thread_id obtenido: {thread_id}")

    # Guardar en BD
    if thread:
        thread.thread_id = thread_id
    else:
        thread = Thread(username=username_norm, thread_id=thread_id)
        db.add(thread)
    db.commit()
    db.refresh(thread)

    print(f"[BOT] Guardado en BD: {username_norm} -> {thread.thread_id}")
    return thread_id


# ===============================
# Envío de mensajes
# ===============================

def enviar_mensajes(
    db: Session,
    driver: webdriver.Remote,
    cuentas_destinatarias: List[str],
    mensajes: List[str],
    archivos: Optional[List[str]] = None,
) -> None:
    """
    Envía mensajes (y opcionalmente archivos) a una lista de cuentas de Instagram.

    - cuentas_destinatarias: lista de @usuarios o IDs numéricos de chat (thread_id)
    - mensajes: lista de textos a enviar
    - archivos: lista de rutas absolutas a archivos a adjuntar (opcional)
    """
    if not cuentas_destinatarias:
        raise InstagramBotError("No se recibieron destinatarios")
    if not mensajes:
        raise InstagramBotError("No se recibieron mensajes")

    archivos = archivos or []
    wait = WebDriverWait(driver, 20)

    for cuenta in cuentas_destinatarias:
        cuenta = cuenta.strip()
        if not cuenta:
            continue

        print(f"[BOT] ---- Procesando destinatario: {cuenta} ----")

        # 1) Resolver thread_id (BD + ig.me)
        thread_id = obtener_o_crear_thread_id(db, driver, cuenta)

        # 2) Ir directo al hilo por URL
        chat_url = f"https://www.instagram.com/direct/t/{thread_id}/"
        print(f"[BOT] Navegando al chat: {chat_url}")
        driver.get(chat_url)

        # 2.1) Cerrar popup "Turn on Notifications" si aparece
        cerrar_popup_notificaciones(driver, timeout=15)
        time.sleep(1)  # pequeña pausa para que se estabilice la vista

        # 3) Esperar a que aparezca el área de texto del mensaje
        try:
            entrada = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='textbox']")
                )
            )
        except TimeoutException:
            raise InstagramBotError(
                f"No se encontró el área de texto del chat para thread_id {thread_id}"
            )

        # 4) Enviar textos
        for texto in mensajes:
            texto = (texto or "").strip()
            if not texto:
                continue

            try:
                entrada.click()
            except ElementClickInterceptedException:
                # Algo tapó el textbox: intentamos cerrar el popup y reintentar
                print("[BOT] Click interceptado, reintentando tras cerrar popup...")
                cerrar_popup_notificaciones(driver, timeout=10)
                entrada = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@role='textbox']")
                    )
                )
                driver.execute_script("arguments[0].click();", entrada)

            entrada.send_keys(texto)
            entrada.send_keys(Keys.ENTER)
            time.sleep(0.5)  # pequeña pausa entre mensajes

        # 5) Enviar archivos adjuntos (si hay)
        for path in archivos:
            path = path.strip()
            if not path or not os.path.exists(path):
                continue
            try:
                input_archivo = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@type='file']")
                    )
                )
                input_archivo.send_keys(path)
                time.sleep(3)

                boton_enviar_archivo = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//div[@role='button' and text()='Enviar']")
                    )
                )
                driver.execute_script(
                    "arguments[0].click();", boton_enviar_archivo
                )
                time.sleep(2)
            except Exception as e:
                print(f"[BOT] No se pudo enviar archivo {path}: {e}")

        # 6) Actualizar contador de mensajes enviados en BD (solo si era username)
        username_norm = limpiar_username(cuenta) if not cuenta.isdigit() else None
        if username_norm:
            thread = (
                db.query(Thread)
                .filter(Thread.username == username_norm)
                .first()
            )
            if thread:
                thread.messages_sent = (thread.messages_sent or 0) + len(mensajes)
                db.commit()

        print(f"[BOT] ---- Fin destinatario: {cuenta} ----")
