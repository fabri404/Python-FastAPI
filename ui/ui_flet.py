# ui_flet.py
import os
import json
import flet as ft
import httpx

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
SEND_ENDPOINT = f"{API_BASE}/api/send"
THREADS_ENDPOINT = f"{API_BASE}/api/threads"
STATS_ENDPOINT = f"{API_BASE}/api/stats"


def main(page: ft.Page):
    page.title = "Instagram DM Automation"
    page.window_width = 980
    page.window_height = 720
    page.scroll = "auto"

    # ------------- Estado -------------
    adjuntos: list[str] = []
    seleccion_archivos = ft.Text("Sin archivos adjuntos", selectable=True)

    # ------------- Picker de archivos -------------
    def on_files_selected(e: ft.FilePickerResultEvent):
        adjuntos.clear()
        if e.files:
            for f in e.files:
                if f.path:
                    adjuntos.append(f.path)
        seleccion_archivos.value = (
            "\n".join(adjuntos) if adjuntos else "Sin archivos adjuntos"
        )
        page.update()

    file_picker = ft.FilePicker(on_result=on_files_selected)
    page.overlay.append(file_picker)

    # ------------- Controles pestaña "Enviar" -------------
    tf_recipientes = ft.TextField(
        label="Destinatarios (@usuario o thread_id), uno por línea",
        multiline=True,
        min_lines=4,
        max_lines=6,
        autofocus=True,
    )
    tf_mensajes = ft.TextField(
        label="Mensajes (uno por línea)",
        multiline=True,
        min_lines=4,
        max_lines=8,
    )

    info_send = ft.Text("", selectable=True)

    def limpiar(e=None):
        tf_recipientes.value = ""
        tf_mensajes.value = ""
        adjuntos.clear()
        seleccion_archivos.value = "Sin archivos adjuntos"
        info_send.value = ""
        page.update()

    def iniciar_automatizacion(e):
        rec = [r.strip() for r in (tf_recipientes.value or "").splitlines() if r.strip()]
        msgs = [m.strip() for m in (tf_mensajes.value or "").splitlines() if m.strip()]
        body = {"recipients": rec, "messages": msgs, "attachments": adjuntos}

        if not rec or not msgs:
            page.snack_bar = ft.SnackBar(ft.Text("Faltan destinatarios o mensajes"), open=True)
            page.update()
            return

        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.post(SEND_ENDPOINT, json=body)
            if res.status_code == 200:
                info_send.value = json.dumps(res.json(), ensure_ascii=False, indent=2)
                page.snack_bar = ft.SnackBar(ft.Text("Envío iniciado"), open=True)
                cargar_historial()  # refresca tabla tras enviar
            else:
                info_send.value = f"Error {res.status_code}: {res.text}"
                page.snack_bar = ft.SnackBar(ft.Text("Error al enviar"), open=True)
        except Exception as ex:
            info_send.value = f"Excepción: {ex}"
            page.snack_bar = ft.SnackBar(ft.Text("Excepción en la solicitud"), open=True)
        page.update()

    enviar_layout = ft.Column(
        [
            ft.Text("Enviar mensajes", size=20, weight=ft.FontWeight.BOLD),
            tf_recipientes,
            tf_mensajes,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Adjuntar archivos",
                        icon=ft.Icons.ATTACH_FILE,
                        on_click=lambda e: file_picker.pick_files(
                            allow_multiple=True
                        ),
                    ),
                    ft.TextButton("Limpiar", on_click=limpiar),
                    ft.FilledButton(
                        "Iniciar Automatización",
                        icon=ft.Icons.SEND,
                        on_click=iniciar_automatizacion,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text("Adjuntos:"),
            ft.Container(seleccion_archivos, padding=10, bgcolor=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text("Respuesta:", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(info_send, padding=10, bgcolor=ft.Colors.SURFACE),
        ],
        spacing=12,
        expand=True,
    )

    # ------------- Controles pestaña "Historial" -------------
    tf_buscar = ft.TextField(
        label="Buscar por username (substring, sin @)",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: cargar_historial(),
    )
    dd_orden = ft.Dropdown(
        label="Orden por enviados",
        value="desc",
        options=[ft.dropdown.Option("desc"), ft.dropdown.Option("asc")],
        on_change=lambda e: cargar_historial(),
        width=180,
    )
    btn_refrescar = ft.IconButton(
        icon=ft.Icons.REFRESH, tooltip="Refrescar", on_click=lambda e: cargar_historial()
    )

    txt_stats = ft.Text("—", size=14)
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Thread ID")),
            ft.DataColumn(ft.Text("Enviados")),
            ft.DataColumn(ft.Text("Creado")),
            ft.DataColumn(ft.Text("Actualizado")),
        ],
        rows=[],
        data_row_max_height=56,
        column_spacing=18,
        heading_row_color=ft.Colors.ON_SURFACE_VARIANT,
        divider_thickness=0,
    )

    def set_rows(items):
        tabla.rows = []
        for it in items:
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(it.get("username", ""))),
                        ft.DataCell(
                            ft.Text(
                                it.get("thread_id", ""),
                                selectable=True,
                            )
                        ),
                        ft.DataCell(ft.Text(str(it.get("messages_sent", 0)))),
                        ft.DataCell(ft.Text(it.get("created_at", ""))),
                        ft.DataCell(ft.Text(it.get("updated_at", ""))),
                    ]
                )
            )

    def cargar_historial():
        params = {}
        if tf_buscar.value and tf_buscar.value.strip():
            params["q"] = tf_buscar.value.strip().lstrip("@")
        params["order"] = dd_orden.value or "desc"

        try:
            with httpx.Client(timeout=30.0) as client:
                r_threads = client.get(THREADS_ENDPOINT, params=params)
                r_stats = client.get(STATS_ENDPOINT)

            if r_threads.status_code == 200:
                data = r_threads.json()
                items = data.get("items", [])
                set_rows(items)
            else:
                tabla.rows = []
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Error cargando threads: {r_threads.status_code}"), open=True
                )

            if r_stats.status_code == 200:
                st = r_stats.json()
                txt_stats.value = f"Total cuentas: {st.get('total_threads', 0)} · Total mensajes: {st.get('total_messages_sent', 0)}"
            else:
                txt_stats.value = "—"

        except Exception as ex:
            tabla.rows = []
            txt_stats.value = f"Error: {ex}"

        page.update()

    historial_layout = ft.Column(
        [
            ft.Text("Historial de envíos", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [tf_buscar, dd_orden, btn_refrescar],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(
                content=ft.Column([tabla], expand=True),
                expand=True,
                bgcolor=ft.Colors.SURFACE,
                padding=10,
                border_radius=8,
            ),
            ft.Row([txt_stats]),
        ],
        spacing=12,
        expand=True,
    )

    # ------------- Tabs generales -------------
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Enviar", icon=ft.Icons.SEND, content=enviar_layout),
            ft.Tab(text="Historial", icon=ft.Icons.HISTORY, content=historial_layout),
        ],
        expand=1,
        animation_duration=200,
    )

    page.add(tabs)
    cargar_historial()


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)