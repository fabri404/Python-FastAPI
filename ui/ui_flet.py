import flet as ft
import requests
import os


API_URL = "http://127.0.0.1:8000/api/send"


def main(page: ft.Page):
    page.title = "Envíos automáticos Instagram"
    page.window_width = 800
    page.window_height = 600


    # Campos de entrada
    destinatarios_field = ft.TextField(
        label="Destinatarios (uno por línea)",
        multiline=True,
        min_lines=3,
        max_lines=5,
        hint_text="@usuario1\n@usuario2\n1234567890 (ID de chat)",
        expand=True,
    )

    mensajes_field = ft.TextField(
        label="Mensaje (uno o varios, uno por línea)",
        multiline=True,
        min_lines=3,
        max_lines=5,
        hint_text="Hola, esto es un mensaje automático...",
        expand=True,
    )

    # FilePicker para adjuntos
    archivos_seleccionados = ft.Text(value="Sin archivos adjuntos", selectable=True)
    file_picker = ft.FilePicker()

    def on_files_selected(e: ft.FilePickerResultEvent):
        if e.files:
            rutas = [f.path for f in e.files]
            archivos_seleccionados.value = "\n".join(rutas)
            archivos_seleccionados.update()
        else:
            archivos_seleccionados.value = "Sin archivos adjuntos"
            archivos_seleccionados.update()

    file_picker.on_result = on_files_selected
    page.overlay.append(file_picker)

    estado_texto = ft.Text(value="Listo.", selectable=True)

    def limpiar_campos(e):
        destinatarios_field.value = ""
        mensajes_field.value = ""
        archivos_seleccionados.value = "Sin archivos adjuntos"
        destinatarios_field.update()
        mensajes_field.update()
        archivos_seleccionados.update()
        estado_texto.value = "Campos limpiados."
        estado_texto.update()

    def enviar_automatizacion(e):
        # Tomar destinatarios
        destinatarios = [
            linea.strip()
            for linea in destinatarios_field.value.splitlines()
            if linea.strip()
        ]

        # Tomar mensajes
        mensajes = [
            linea.strip()
            for linea in mensajes_field.value.splitlines()
            if linea.strip()
        ]

        # Tomar adjuntos (si hay)
        adjuntos = []
        if archivos_seleccionados.value != "Sin archivos adjuntos":
            adjuntos = [
                linea.strip()
                for linea in archivos_seleccionados.value.splitlines()
                if linea.strip()
            ]

        if not destinatarios:
            estado_texto.value = "⚠️ Ingresá al menos un destinatario."
            estado_texto.update()
            return

        if not mensajes:
            estado_texto.value = "⚠️ Ingresá al menos un mensaje."
            estado_texto.update()
            return

        payload = {
            "recipients": destinatarios,
            "messages": mensajes,
            "attachments": adjuntos,
        }

        estado_texto.value = "Enviando solicitud al backend..."
        estado_texto.update()

        try:
            resp = requests.post(API_URL, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    estado_texto.value = f"✅ OK: {data.get('detail')}"
                else:
                    estado_texto.value = f"⚠️ Respuesta del servidor: {data}"
            else:
                estado_texto.value = f"❌ Error {resp.status_code}: {resp.text}"
        except Exception as ex:
            estado_texto.value = f"❌ Error al llamar a la API: {ex}"

        estado_texto.update()

    # Layout
    page.add(
        ft.Column(
            [
                ft.Text("Envíos automatizados a Instagram", size=24, weight=ft.FontWeight.BOLD),
                destinarios_row := ft.Row([destinatarios_field], expand=True),
                mensajes_row := ft.Row([mensajes_field], expand=True),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Seleccionar archivos",
                            on_click=lambda e: file_picker.pick_files(allow_multiple=True),
                        ),
                    ]
                ),
                ft.Text("Archivos seleccionados:"),
                archivos_seleccionados,
                ft.Row(
                    [
                        ft.ElevatedButton("Iniciar Automatización", on_click=enviar_automatizacion),
                        ft.ElevatedButton("Limpiar", on_click=limpiar_campos),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(),
                estado_texto,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
    )

if __name__ == "__main__":
    # Abrir la UI en el navegador web en lugar de ventana nativa
    ft.app(target=main, view=ft.WEB_BROWSER)

