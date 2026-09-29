"""
ui/views/inventory_view.py
Gestión de Recursos/Stock, Funcionarios y Cursos con paginación y validaciones.
"""

import customtkinter as ctk
from ui.theme import Theme
from ui.components.paginator import Paginator
from database.connection import get_connection, get_db_cursor
from ui.components.modal_item import ModalItem

class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, on_stock_changed_callback):
        super().__init__(parent, fg_color="transparent")
        self.on_stock_changed = on_stock_changed_callback
        self.seccion_actual = "recursos"

        self._construir_pestanas()
        self._construir_cabecera()
        self._construir_tabla_contenedor()

        # Paginador inferior
        self.paginator = Paginator(self, on_page_change_callback=self.cargar_datos, items_per_page=20)
        self.paginator.pack(side="bottom", fill="x", pady=10)

        self.cargar_datos(1)

    def _construir_pestanas(self):
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0, 10))

        self.btn_tab_recursos = ctk.CTkButton(
            tab_frame, text="📦 Recursos y Equipamiento", height=32,
            fg_color=Theme.BG_CARD, hover_color=Theme.BORDER_COLOR,
            command=lambda: self._cambiar_pestana("recursos")
        )
        self.btn_tab_recursos.pack(side="left", padx=(0, 5))

        self.btn_tab_funcionarios = ctk.CTkButton(
            tab_frame, text="👥 Funcionarios / Docentes", height=32,
            fg_color="transparent", hover_color=Theme.BORDER_COLOR,
            command=lambda: self._cambiar_pestana("funcionarios")
        )
        self.btn_tab_funcionarios.pack(side="left", padx=5)

        self.btn_tab_cursos = ctk.CTkButton(
            tab_frame, text="🎓 Cursos y Áreas", height=32,
            fg_color="transparent", hover_color=Theme.BORDER_COLOR,
            command=lambda: self._cambiar_pestana("cursos")
        )
        self.btn_tab_cursos.pack(side="left", padx=5)

    def _cambiar_pestana(self, pestana: str):
        self.seccion_actual = pestana
        self.btn_tab_recursos.configure(fg_color=Theme.BG_CARD if pestana == "recursos" else "transparent")
        self.btn_tab_funcionarios.configure(fg_color=Theme.BG_CARD if pestana == "funcionarios" else "transparent")
        self.btn_tab_cursos.configure(fg_color=Theme.BG_CARD if pestana == "cursos" else "transparent")
        self.entry_busqueda.delete(0, "end")
        self.paginator.reset()
        self.cargar_datos(1)

    def _construir_cabecera(self):
        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.pack(fill="x", pady=(0, 10))

        self.entry_busqueda = ctk.CTkEntry(
            cabecera,
            placeholder_text="🔍 Buscar en este catálogo...",
            width=320,
            height=34
        )
        self.entry_busqueda.pack(side="left")
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.cargar_datos(1))

        self.btn_agregar = ctk.CTkButton(
            cabecera,
            text="+ Agregar Nuevo",
            height=34,
            font=("Segoe UI", 12, "bold"),
            fg_color=Theme.ACCENT_YELLOW,
            hover_color=Theme.ACCENT_YELLOW_HOVER,
            text_color="#1E1E24",
            command=self._modal_agregar
        )
        self.btn_agregar.pack(side="right")

    def _construir_tabla_contenedor(self):
        self.cols_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=36, corner_radius=6)
        self.cols_frame.pack(fill="x", pady=(0, 6))

        self.filas_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.filas_frame.pack(fill="both", expand=True)

    def _actualizar_cabeceras(self):
        for child in self.cols_frame.winfo_children():
            child.destroy()

        if self.seccion_actual == "recursos":
            headers = [("ID", 60), ("Nombre del Recurso", 240), ("Tipo", 140), ("Stock Total", 120), ("Acciones", 120)]
        else:
            headers = [("ID", 60), ("Nombre", 350), ("Estado", 140), ("Acciones", 120)]

        for text, width in headers:
            lbl = ctk.CTkLabel(self.cols_frame, text=text, font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED, anchor="w", width=width)
            lbl.pack(side="left", padx=10, fill="x", expand=(text in ["Nombre del Recurso", "Nombre"]))

    def cargar_datos(self, page=1):
        for child in self.filas_frame.winfo_children():
            child.destroy()

        self._actualizar_cabeceras()

        filtro = f"%{self.entry_busqueda.get().strip()}%"
        limit = self.paginator.items_per_page
        offset = (page - 1) * limit

        conn = get_connection()
        cur = conn.cursor()

        if self.seccion_actual == "recursos":
            cur.execute("SELECT COUNT(*) as t FROM recursos WHERE nombre LIKE ?;", (filtro,))
            total = cur.fetchone()["t"]
            cur.execute("""
                SELECT id, nombre, tipo, stock_total 
                FROM recursos 
                WHERE nombre LIKE ? 
                ORDER BY tipo ASC, nombre ASC 
                LIMIT ? OFFSET ?;
            """, (filtro, limit, offset))
            items = cur.fetchall()
        elif self.seccion_actual == "funcionarios":
            cur.execute("SELECT COUNT(*) as t FROM funcionarios WHERE nombre LIKE ?;", (filtro,))
            total = cur.fetchone()["t"]
            cur.execute("SELECT id, nombre, activo FROM funcionarios WHERE nombre LIKE ? ORDER BY nombre ASC LIMIT ? OFFSET ?;", (filtro, limit, offset))
            items = cur.fetchall()
        else:
            cur.execute("SELECT COUNT(*) as t FROM cursos WHERE nombre LIKE ?;", (filtro,))
            total = cur.fetchone()["t"]
            cur.execute("SELECT id, nombre, activo FROM cursos WHERE nombre LIKE ? ORDER BY nombre ASC LIMIT ? OFFSET ?;", (filtro, limit, offset))
            items = cur.fetchall()

        conn.close()

        if not items:
            lbl_vacio = ctk.CTkLabel(self.filas_frame, text="No se encontraron registros.", font=("Segoe UI", 13), text_color=Theme.TEXT_MUTED)
            lbl_vacio.pack(pady=30)
        else:
            for item in items:
                self._crear_fila(item)

        self.paginator.current_page = page
        self.paginator.update_totals(total)

    def _crear_fila(self, item):
        fila = ctk.CTkFrame(self.filas_frame, fg_color=Theme.BG_CARD, height=40, corner_radius=6)
        fila.pack(fill="x", pady=2)

        lbl_id = ctk.CTkLabel(fila, text=str(item["id"]), width=60, anchor="w", font=("Segoe UI", 11), text_color=Theme.TEXT_MUTED)
        lbl_id.pack(side="left", padx=10)

        lbl_nom = ctk.CTkLabel(fila, text=item["nombre"], font=("Segoe UI", 12, "bold"), anchor="w")
        lbl_nom.pack(side="left", padx=10, fill="x", expand=True)

        if self.seccion_actual == "recursos":
            lbl_tipo = ctk.CTkLabel(fila, text=item["tipo"].capitalize(), width=140, anchor="w", font=("Segoe UI", 11), text_color=Theme.TEXT_MUTED)
            lbl_tipo.pack(side="left", padx=10)

            lbl_stock = ctk.CTkLabel(fila, text=str(item["stock_total"]), width=120, anchor="w", font=("Segoe UI", 12), text_color=Theme.ACCENT_YELLOW)
            lbl_stock.pack(side="left", padx=10)

            btn_edit = ctk.CTkButton(
                fila, text="Ajustar Stock", width=100, height=26,
                fg_color=Theme.BG_DARK, hover_color=Theme.BORDER_COLOR,
                command=lambda r=item: self._modal_ajustar_stock(r)
            )
            btn_edit.pack(side="right", padx=10)
        else:
            estado = "Activo" if item["activo"] == 1 else "Inactivo"
            lbl_estado = ctk.CTkLabel(
                fila, text=estado, width=140, anchor="w",
                font=("Segoe UI", 11), text_color=Theme.COLOR_SUCCESS if item["activo"] == 1 else Theme.COLOR_DANGER
            )
            lbl_estado.pack(side="left", padx=10)

            btn_toggle = ctk.CTkButton(
                fila, text="Desactivar" if item["activo"] == 1 else "Activar",
                width=100, height=26,
                fg_color=Theme.BG_DARK, hover_color=Theme.BORDER_COLOR,
                command=lambda id_item=item["id"], act=item["activo"]: self._toggle_activo(id_item, act)
            )
            btn_toggle.pack(side="right", padx=10)

    def _modal_agregar(self):
        def guardar_callback(nombre, tipo="individual", stock=1):
            try:
                with get_db_cursor() as cur:
                    if self.seccion_actual == "recursos":
                        cur.execute(
                            "INSERT INTO recursos (nombre, tipo, stock_total) VALUES (?, ?, ?);",
                            (nombre, tipo, stock)
                        )
                    elif self.seccion_actual == "funcionarios":
                        cur.execute("INSERT INTO funcionarios (nombre) VALUES (?);", (nombre,))
                    else:
                        cur.execute("INSERT INTO cursos (nombre) VALUES (?);", (nombre,))

                self.cargar_datos(self.paginator.current_page)
                self.on_stock_changed()
            except Exception as e:
                print("Error al guardar en base de datos:", e)

        ModalItem(self, seccion=self.seccion_actual, on_save_callback=guardar_callback)

    def _modal_ajustar_stock(self, recurso):
        dialog = ctk.CTkInputDialog(
            text=f"Nuevo stock total para '{recurso['nombre']}' (Actual: {recurso['stock_total']}):",
            title="Ajustar Stock Total"
        )
        valor = dialog.get_input()
        if valor is None:
            return

        try:
            nuevo_stock = int(valor.strip())
            if nuevo_stock < 0:
                return

            with get_db_cursor() as cur:
                cur.execute("UPDATE recursos SET stock_total = ? WHERE id = ?;", (nuevo_stock, recurso["id"]))

            self.cargar_datos(self.paginator.current_page)
            self.on_stock_changed()
        except ValueError:
            pass

    def _toggle_activo(self, id_item: int, estado_actual: int):
        nuevo_estado = 0 if estado_actual == 1 else 1
        tabla = "funcionarios" if self.seccion_actual == "funcionarios" else "cursos"
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE {tabla} SET activo = ? WHERE id = ?;", (nuevo_estado, id_item))
        self.cargar_datos(self.paginator.current_page)