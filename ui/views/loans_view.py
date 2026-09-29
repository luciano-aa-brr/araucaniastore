"""
ui/views/loans_view.py
Panel visual para listar, buscar, devolver y editar los préstamos activos.
"""

from datetime import datetime
import customtkinter as ctk
from ui.theme import Theme
from ui.components.paginator import Paginator
from ui.components.modal_loan import ModalLoan
from database.connection import get_connection
from services.stock_service import StockService

class LoansView(ctk.CTkFrame):
    def __init__(self, parent, on_data_changed_callback):
        super().__init__(parent, fg_color="transparent")
        self.on_data_changed = on_data_changed_callback

        self._construir_cabecera()
        self._construir_tabla_contenedor()

        # Paginador inferior
        self.paginator = Paginator(self, on_page_change_callback=self.cargar_prestamos, items_per_page=8)
        self.paginator.pack(side="bottom", fill="x", pady=10)

        self.cargar_prestamos(1)

    def _construir_cabecera(self):
        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.pack(fill="x", pady=(0, 15))

        # Buscador
        self.entry_busqueda = ctk.CTkEntry(
            cabecera,
            placeholder_text="🔍 Buscar por profesor, curso u observación...",
            width=350,
            height=36
        )
        self.entry_busqueda.pack(side="left")
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.cargar_prestamos(1))

        # Botón Nuevo Préstamo
        btn_nuevo = ctk.CTkButton(
            cabecera,
            text="+ Nuevo Préstamo",
            height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color=Theme.ACCENT_YELLOW,
            hover_color=Theme.ACCENT_YELLOW_HOVER,
            text_color="#1E1E24",
            command=self._abrir_modal_nuevo
        )
        btn_nuevo.pack(side="right")

    def _construir_tabla_contenedor(self):
        # Encabezados de tabla
        cols_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=36, corner_radius=6)
        cols_frame.pack(fill="x", pady=(0, 6))

        headers = [("Horario", 120), ("Solicitante", 180), ("Curso", 90), ("Equipos / Espacio", 220), ("Observaciones", 200), ("Acciones", 160)]
        for text, width in headers:
            lbl = ctk.CTkLabel(cols_frame, text=text, font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED, anchor="w")
            lbl.pack(side="left", padx=10, fill="x", expand=(text in ["Equipos / Espacio", "Observaciones"]))

        # Contenedor con scroll para las filas
        self.filas_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.filas_frame.pack(fill="both", expand=True)

    def cargar_prestamos(self, page=1):
        # Limpiar filas existentes
        for child in self.filas_frame.winfo_children():
            child.destroy()

        filtro = f"%{self.entry_busqueda.get().strip()}%"
        limit = self.paginator.items_per_page
        offset = (page - 1) * limit

        conn = get_connection()
        cur = conn.cursor()

        # Conteo total con filtro
        cur.execute("""
            SELECT COUNT(*) as total
            FROM prestamos p
            JOIN funcionarios f ON p.funcionario_id = f.id
            LEFT JOIN cursos c ON p.curso_id = c.id
            WHERE p.estado = 'activo'
              AND (f.nombre LIKE ? OR c.nombre LIKE ? OR p.observaciones LIKE ?);
        """, (filtro, filtro, filtro))
        total_items = cur.fetchone()["total"]

        # Registros paginados
        cur.execute("""
            SELECT p.id, p.fecha, p.hora_inicio, p.hora_fin, p.observaciones,
                   f.nombre as profesor, c.nombre as curso
            FROM prestamos p
            JOIN funcionarios f ON p.funcionario_id = f.id
            LEFT JOIN cursos c ON p.curso_id = c.id
            WHERE p.estado = 'activo'
              AND (f.nombre LIKE ? OR c.nombre LIKE ? OR p.observaciones LIKE ?)
            ORDER BY p.fecha DESC, p.hora_inicio DESC
            LIMIT ? OFFSET ?;
        """, (filtro, filtro, filtro, limit, offset))
        prestamos = cur.fetchall()

        if not prestamos:
            lbl_vacio = ctk.CTkLabel(
                self.filas_frame,
                text="No hay préstamos activos registrados en este momento.",
                font=("Segoe UI", 13),
                text_color=Theme.TEXT_MUTED
            )
            lbl_vacio.pack(pady=40)
        else:
            for p in prestamos:
                # Obtener recursos de este préstamo
                cur.execute("""
                    SELECT r.nombre, pd.cantidad
                    FROM prestamo_detalles pd
                    JOIN recursos r ON pd.recurso_id = r.id
                    WHERE pd.prestamo_id = ?;
                """, (p["id"],))
                detalles = cur.fetchall()
                txt_recursos = ", ".join([f"{d['cantidad']} {d['nombre']}" if d['cantidad'] > 1 else d['nombre'] for d in detalles])

                self._crear_fila(p, txt_recursos)

        conn.close()
        self.paginator.current_page = page
        self.paginator.update_totals(total_items)

    def _crear_fila(self, p, txt_recursos):
        fila = ctk.CTkFrame(self.filas_frame, fg_color=Theme.BG_CARD, height=44, corner_radius=6)
        fila.pack(fill="x", pady=3)

        horario = f"{p['hora_inicio']} - {p['hora_fin']}"
        lbl_hora = ctk.CTkLabel(fila, text=horario, width=120, anchor="w", font=("Segoe UI", 12))
        lbl_hora.pack(side="left", padx=10)

        lbl_prof = ctk.CTkLabel(fila, text=p["profesor"], width=180, anchor="w", font=("Segoe UI", 12, "bold"))
        lbl_prof.pack(side="left", padx=10)

        lbl_curso = ctk.CTkLabel(fila, text=p["curso"] or "--", width=90, anchor="w", font=("Segoe UI", 12))
        lbl_curso.pack(side="left", padx=10)

        lbl_rec = ctk.CTkLabel(fila, text=txt_recursos, anchor="w", font=("Segoe UI", 12), text_color=Theme.ACCENT_YELLOW)
        lbl_rec.pack(side="left", padx=10, fill="x", expand=True)

        lbl_obs = ctk.CTkLabel(fila, text=p["observaciones"] or "", anchor="w", font=("Segoe UI", 11), text_color=Theme.TEXT_MUTED)
        lbl_obs.pack(side="left", padx=10, fill="x", expand=True)

        # Acciones
        acc_frame = ctk.CTkFrame(fila, fg_color="transparent", width=160)
        acc_frame.pack(side="right", padx=10)

        btn_edit = ctk.CTkButton(
            acc_frame, text="✏️", width=36, height=28,
            fg_color=Theme.BG_DARK, hover_color=Theme.BORDER_COLOR,
            command=lambda pid=p["id"]: self._abrir_modal_editar(pid)
        )
        btn_edit.pack(side="left", padx=2)

        btn_dev = ctk.CTkButton(
            acc_frame, text="✓ Devolver", width=85, height=28,
            fg_color=Theme.COLOR_SUCCESS, hover_color="#66BB6A", text_color="#1E1E24",
            font=("Segoe UI", 11, "bold"),
            command=lambda pid=p["id"]: self._devolver(pid)
        )
        btn_dev.pack(side="left", padx=2)

    def _abrir_modal_nuevo(self):
        ModalLoan(self, on_save_callback=self._on_datos_guardados)

    def _abrir_modal_editar(self, prestamo_id):
        ModalLoan(self, on_save_callback=self._on_datos_guardados, prestamo_id=prestamo_id)

    def _devolver(self, prestamo_id):
        StockService.marcar_como_devuelto(prestamo_id)
        self._on_datos_guardados()

    def _on_datos_guardados(self):
        self.cargar_prestamos(self.paginator.current_page)
        self.on_data_changed()