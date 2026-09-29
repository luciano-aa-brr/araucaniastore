"""
ui/views/history_view.py
Vista de historial completo con filtros por estado, fechas y exportación a PDF y Excel.
"""

from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.theme import Theme
from ui.components.paginator import Paginator
from database.connection import get_connection
from services.report_service import ReportService

class HistoryView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self._construir_filtros()
        self._construir_tabla_contenedor()

        self.paginator = Paginator(self, on_page_change_callback=self.cargar_historial, items_per_page=12)
        self.paginator.pack(side="bottom", fill="x", pady=10)

        self.cargar_historial(1)

    def _construir_filtros(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", pady=(0, 12))

        # Buscador por texto
        self.entry_busqueda = ctk.CTkEntry(
            barra,
            placeholder_text="🔍 Buscar profesor, curso o motivo...",
            width=260,
            height=34
        )
        self.entry_busqueda.pack(side="left", padx=(0, 8))
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.cargar_historial(1))

        # Filtro de Estado
        self.combo_estado = ctk.CTkComboBox(
            barra,
            values=["Todos los Estados", "Activo", "Devuelto"],
            height=34,
            width=150,
            dropdown_fg_color=Theme.BG_CARD,
            command=lambda val: self.cargar_historial(1)
        )
        self.combo_estado.set("Todos los Estados")
        self.combo_estado.pack(side="left", padx=5)

        # Botones de exportación
        self.btn_export_pdf = ctk.CTkButton(
            barra,
            text="📄 Exportar PDF",
            height=34,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self._exportar_pdf
        )
        self.btn_export_pdf.pack(side="right", padx=(5, 0))

        self.btn_export_excel = ctk.CTkButton(
            barra,
            text="📊 Exportar Excel",
            height=34,
            fg_color=Theme.ACCENT_YELLOW,
            hover_color=Theme.ACCENT_YELLOW_HOVER,
            text_color="#1E1E24",
            font=("Segoe UI", 12, "bold"),
            command=self._exportar_excel
        )
        self.btn_export_excel.pack(side="right", padx=5)

    def _construir_tabla_contenedor(self):
        cols_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=36, corner_radius=6)
        cols_frame.pack(fill="x", pady=(0, 6))

        headers = [("Fecha", 90), ("Horario", 110), ("Solicitante", 170), ("Curso", 80), ("Recursos Prestados", 220), ("Estado", 100)]
        for text, width in headers:
            lbl = ctk.CTkLabel(cols_frame, text=text, font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED, anchor="w", width=width)
            lbl.pack(side="left", padx=10, fill="x", expand=(text == "Recursos Prestados"))

        self.filas_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.filas_frame.pack(fill="both", expand=True)

    def cargar_historial(self, page=1):
        for child in self.filas_frame.winfo_children():
            child.destroy()

        filtro = f"%{self.entry_busqueda.get().strip()}%"
        estado_sel = self.combo_estado.get().lower()

        limit = self.paginator.items_per_page
        offset = (page - 1) * limit

        conn = get_connection()
        cur = conn.cursor()

        query_count = """
            SELECT COUNT(*) as total
            FROM prestamos p
            JOIN funcionarios f ON p.funcionario_id = f.id
            LEFT JOIN cursos c ON p.curso_id = c.id
            WHERE (f.nombre LIKE ? OR c.nombre LIKE ? OR p.observaciones LIKE ?)
        """
        params_count = [filtro, filtro, filtro]

        if estado_sel in ["activo", "devuelto"]:
            query_count += " AND p.estado = ?"
            params_count.append(estado_sel)

        cur.execute(query_count, params_count)
        total_items = cur.fetchone()["total"]

        query_data = """
            SELECT p.id, p.fecha, p.hora_inicio, p.hora_fin, p.estado,
                   f.nombre as profesor, c.nombre as curso
            FROM prestamos p
            JOIN funcionarios f ON p.funcionario_id = f.id
            LEFT JOIN cursos c ON p.curso_id = c.id
            WHERE (f.nombre LIKE ? OR c.nombre LIKE ? OR p.observaciones LIKE ?)
        """
        params_data = [filtro, filtro, filtro]

        if estado_sel in ["activo", "devuelto"]:
            query_data += " AND p.estado = ?"
            params_data.append(estado_sel)

        query_data += " ORDER BY p.fecha DESC, p.hora_inicio DESC LIMIT ? OFFSET ?;"
        params_data.extend([limit, offset])

        cur.execute(query_data, params_data)
        prestamos = cur.fetchall()

        if not prestamos:
            lbl_vacio = ctk.CTkLabel(self.filas_frame, text="No hay registros en el historial.", font=("Segoe UI", 13), text_color=Theme.TEXT_MUTED)
            lbl_vacio.pack(pady=40)
        else:
            for p in prestamos:
                cur.execute("""
                    SELECT r.nombre, pd.cantidad
                    FROM prestamo_detalles pd
                    JOIN recursos r ON pd.recurso_id = r.id
                    WHERE pd.prestamo_id = ?;
                """, (p["id"],))
                detalles = cur.fetchall()
                txt_rec = ", ".join([f"{d['cantidad']} {d['nombre']}" if d["cantidad"] > 1 else d["nombre"] for d in detalles])
                self._crear_fila(p, txt_rec)

        conn.close()
        self.paginator.current_page = page
        self.paginator.update_totals(total_items)

    def _crear_fila(self, p, txt_rec):
        fila = ctk.CTkFrame(self.filas_frame, fg_color=Theme.BG_CARD, height=38, corner_radius=6)
        fila.pack(fill="x", pady=2)

        ctk.CTkLabel(fila, text=p["fecha"], width=90, anchor="w", font=("Segoe UI", 11)).pack(side="left", padx=10)
        ctk.CTkLabel(fila, text=f"{p['hora_inicio']} - {p['hora_fin']}", width=110, anchor="w", font=("Segoe UI", 11)).pack(side="left", padx=10)
        ctk.CTkLabel(fila, text=p["profesor"], width=170, anchor="w", font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(fila, text=p["curso"] or "--", width=80, anchor="w", font=("Segoe UI", 11)).pack(side="left", padx=10)
        ctk.CTkLabel(fila, text=txt_rec, anchor="w", font=("Segoe UI", 11), text_color=Theme.ACCENT_YELLOW).pack(side="left", padx=10, fill="x", expand=True)

        # Badge de estado
        es_activo = p["estado"] == "activo"
        lbl_est = ctk.CTkLabel(
            fila,
            text="En Uso" if es_activo else "Devuelto",
            width=90,
            font=("Segoe UI", 10, "bold"),
            text_color="#1E1E24" if not es_activo else "#FFFFFF",
            fg_color=Theme.COLOR_WARNING if es_activo else Theme.COLOR_SUCCESS,
            corner_radius=4
        )
        lbl_est.pack(side="right", padx=10)

    def _exportar_excel(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")], title="Guardar Reporte Excel")
        if ruta:
            estado = self.combo_estado.get().lower()
            ReportService.exportar_excel(ruta, estado="activo" if estado == "activo" else ("devuelto" if estado == "devuelto" else None))
            messagebox.showinfo("Éxito", "Reporte Excel generado correctamente.")

    def _exportar_pdf(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")], title="Guardar Reporte PDF")
        if ruta:
            estado = self.combo_estado.get().lower()
            ReportService.exportar_pdf(ruta, estado="activo" if estado == "activo" else ("devuelto" if estado == "devuelto" else None))
            messagebox.showinfo("Éxito", "Reporte PDF institucional generado correctamente.")