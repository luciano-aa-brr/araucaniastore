"""
ui/components/modal_loan.py
Ventana emergente para registrar o editar un préstamo, con soporte para
horarios indefinidos / uso durante la jornada y repetición semanal recurrente.
"""

from datetime import datetime
import customtkinter as ctk
from ui.theme import Theme
from ui.utils import centrar_ventana
from database.connection import get_connection, get_db_cursor
from services.stock_service import StockService

class ModalLoan(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback, prestamo_id=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save_callback
        self.prestamo_id = prestamo_id

        self.title("Editar Préstamo" if prestamo_id else "Nuevo Préstamo")
        centrar_ventana(self, ancho=560, alto=720)
        
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._cargar_datos_catalogos()
        self._construir_ui()

        if self.prestamo_id:
            self._cargar_datos_existentes()

    def _cargar_datos_catalogos(self):
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, nombre FROM funcionarios WHERE activo = 1 ORDER BY nombre ASC;")
        self.lista_funcionarios = cur.fetchall()

        cur.execute("SELECT id, nombre FROM cursos WHERE activo = 1 ORDER BY nombre ASC;")
        self.lista_cursos = cur.fetchall()

        cur.execute("SELECT id, nombre, tipo, stock_total FROM recursos WHERE activo = 1 ORDER BY tipo ASC, nombre ASC;")
        self.lista_recursos = cur.fetchall()
        conn.close()

    def _construir_ui(self):
        # 1. Título Superior
        lbl_titulo = ctk.CTkLabel(
            self,
            text="Editar Préstamo" if self.prestamo_id else "Registrar Nuevo Préstamo",
            font=("Segoe UI", 16, "bold"),
            text_color=Theme.ACCENT_YELLOW
        )
        lbl_titulo.pack(side="top", pady=(15, 10))

        # 2. Contenedor Inferior Fijo (Botones y Errores)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=25, pady=(0, 20))

        self.lbl_error = ctk.CTkLabel(
            footer_frame, text="", 
            font=("Segoe UI", 11), 
            text_color=Theme.COLOR_DANGER,
            wraplength=500
        )
        self.lbl_error.pack(fill="x", pady=(0, 8))

        btns_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btns_frame.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btns_frame, text="Cancelar", height=38,
            fg_color=Theme.BG_CARD, hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_guardar = ctk.CTkButton(
            btns_frame, text="Guardar Préstamo", height=38,
            fg_color=Theme.ACCENT_YELLOW, hover_color=Theme.ACCENT_YELLOW_HOVER,
            text_color="#1E1E24", font=("Segoe UI", 12, "bold"),
            command=self._guardar
        )
        btn_guardar.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # 3. Formulario Central Scrollable
        form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_frame.pack(side="top", fill="both", expand=True, padx=25, pady=(0, 10))

        # Funcionario y Curso
        ctk.CTkLabel(form_frame, text="Funcionario / Solicitante:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        nombres_func = [f["nombre"] for f in self.lista_funcionarios]
        self.combo_funcionario = ctk.CTkComboBox(form_frame, values=nombres_func, height=34, dropdown_fg_color=Theme.BG_CARD)
        self.combo_funcionario.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form_frame, text="Curso o Destino:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        nombres_curso = [c["nombre"] for c in self.lista_cursos]
        self.combo_curso = ctk.CTkComboBox(form_frame, values=nombres_curso, height=34, dropdown_fg_color=Theme.BG_CARD)
        self.combo_curso.pack(fill="x", pady=(2, 10))

        # Fecha y Horarios
        row_tiempo = ctk.CTkFrame(form_frame, fg_color="transparent")
        row_tiempo.pack(fill="x", pady=(2, 6))

        col_fecha = ctk.CTkFrame(row_tiempo, fg_color="transparent")
        col_fecha.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(col_fecha, text="Fecha (YYYY-MM-DD):", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.entry_fecha = ctk.CTkEntry(col_fecha, height=34)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha.pack(fill="x")

        col_inicio = ctk.CTkFrame(row_tiempo, fg_color="transparent")
        col_inicio.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(col_inicio, text="Hora Inicio:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.entry_hora_ini = ctk.CTkEntry(col_inicio, height=34)
        self.entry_hora_ini.insert(0, datetime.now().strftime("%H:%M"))
        self.entry_hora_ini.pack(fill="x")

        col_fin = ctk.CTkFrame(row_tiempo, fg_color="transparent")
        col_fin.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(col_fin, text="Hora Fin:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.entry_hora_fin = ctk.CTkEntry(col_fin, height=34)
        self.entry_hora_fin.insert(0, "13:10")
        self.entry_hora_fin.pack(fill="x")

        # Casilla para Tiempo Indefinido / Por la jornada
        self.var_indefinido = ctk.BooleanVar(value=False)
        self.chk_indefinido = ctk.CTkCheckBox(
            form_frame,
            text="Uso indefinido / durante la jornada escolar (sin hora fin fija)",
            variable=self.var_indefinido,
            font=("Segoe UI", 11),
            command=self._toggle_indefinido
        )
        self.chk_indefinido.pack(anchor="w", pady=(0, 10))

        # Bloque de Préstamo Recurrente (Solo en nuevos préstamos)
        if not self.prestamo_id:
            box_recurrente = ctk.CTkFrame(form_frame, fg_color=Theme.BG_CARD, corner_radius=6)
            box_recurrente.pack(fill="x", pady=(0, 10), padx=2)

            self.var_recurrente = ctk.BooleanVar(value=False)
            self.chk_recurrente = ctk.CTkCheckBox(
                box_recurrente,
                text="Repetir semanalmente (ej. todos los martes / viernes)",
                variable=self.var_recurrente,
                font=("Segoe UI", 11, "bold"),
                command=self._toggle_recurrente
            )
            self.chk_recurrente.pack(anchor="w", padx=10, pady=(8, 4))

            self.frame_rec_hasta = ctk.CTkFrame(box_recurrente, fg_color="transparent")
            ctk.CTkLabel(self.frame_rec_hasta, text="Repetir hasta fecha (YYYY-MM-DD):", font=("Segoe UI", 11), text_color=Theme.TEXT_MUTED).pack(side="left", padx=10)
            self.entry_fecha_fin_rep = ctk.CTkEntry(self.frame_rec_hasta, width=130, height=28)
            self.entry_fecha_fin_rep.insert(0, "2026-11-30")
            self.entry_fecha_fin_rep.pack(side="left", padx=5)

        # Recursos Solicitados
        ctk.CTkLabel(form_frame, text="Recursos a Solicitar:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(5, 2))
        
        self.box_recursos = ctk.CTkFrame(form_frame, fg_color=Theme.BG_CARD, corner_radius=6)
        self.box_recursos.pack(fill="x", pady=(0, 10))

        self.recurso_inputs = {}
        for r in self.lista_recursos:
            item_row = ctk.CTkFrame(self.box_recursos, fg_color="transparent")
            item_row.pack(fill="x", padx=10, pady=4)

            var_check = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(item_row, text=r["nombre"], variable=var_check, font=("Segoe UI", 12))
            chk.pack(side="left", padx=5)

            entry_cant = ctk.CTkEntry(item_row, width=65, height=28)
            entry_cant.insert(0, "1")
            entry_cant.pack(side="right", padx=5)

            ctk.CTkLabel(item_row, text="Cant:", font=("Segoe UI", 11), text_color=Theme.TEXT_MUTED).pack(side="right", padx=(0, 4))

            self.recurso_inputs[r["id"]] = {
                "check_var": var_check,
                "cant_entry": entry_cant,
                "tipo": r["tipo"],
                "nombre": r["nombre"]
            }

        # Observaciones
        ctk.CTkLabel(form_frame, text="Observaciones / Motivo:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.entry_obs = ctk.CTkEntry(form_frame, height=34, placeholder_text="Ej: Reforzamiento, clase continua, toma de pruebas...")
        self.entry_obs.pack(fill="x", pady=(2, 10))

    def _toggle_indefinido(self):
        if self.var_indefinido.get():
            self.entry_hora_fin.delete(0, "end")
            self.entry_hora_fin.insert(0, "--:--")
            self.entry_hora_fin.configure(state="disabled")
        else:
            self.entry_hora_fin.configure(state="normal")
            self.entry_hora_fin.delete(0, "end")
            self.entry_hora_fin.insert(0, "13:10")

    def _toggle_recurrente(self):
        if self.var_recurrente.get():
            self.frame_rec_hasta.pack(fill="x", pady=(0, 8))
        else:
            self.frame_rec_hasta.pack_forget()

    def _cargar_datos_existentes(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.*, f.nombre as func_nom, c.nombre as curso_nom
            FROM prestamos p
            JOIN funcionarios f ON p.funcionario_id = f.id
            LEFT JOIN cursos c ON p.curso_id = c.id
            WHERE p.id = ?;
        """, (self.prestamo_id,))
        p = cur.fetchone()

        if p:
            self.combo_funcionario.set(p["func_nom"])
            if p["curso_nom"]:
                self.combo_curso.set(p["curso_nom"])
            self.entry_fecha.delete(0, "end")
            self.entry_fecha.insert(0, p["fecha"])
            self.entry_hora_ini.delete(0, "end")
            self.entry_hora_ini.insert(0, p["hora_inicio"])

            if not p["hora_fin"] or p["hora_fin"] == "":
                self.var_indefinido.set(True)
                self._toggle_indefinido()
            else:
                self.entry_hora_fin.delete(0, "end")
                self.entry_hora_fin.insert(0, p["hora_fin"])

            if p["observaciones"]:
                self.entry_obs.delete(0, "end")
                self.entry_obs.insert(0, p["observaciones"])

            cur.execute("SELECT recurso_id, cantidad FROM prestamo_detalles WHERE prestamo_id = ?;", (self.prestamo_id,))
            detalles = cur.fetchall()
            for d in detalles:
                rec_id = d["recurso_id"]
                if rec_id in self.recurso_inputs:
                    self.recurso_inputs[rec_id]["check_var"].set(True)
                    self.recurso_inputs[rec_id]["cant_entry"].delete(0, "end")
                    self.recurso_inputs[rec_id]["cant_entry"].insert(0, str(d["cantidad"]))
        conn.close()

    def _guardar(self):
        func_nombre = self.combo_funcionario.get()
        curso_nombre = self.combo_curso.get()
        fecha = self.entry_fecha.get().strip()
        h_ini = self.entry_hora_ini.get().strip()
        h_fin = None if self.var_indefinido.get() else self.entry_hora_fin.get().strip()
        obs = self.entry_obs.get().strip()

        func_id = next((f["id"] for f in self.lista_funcionarios if f["nombre"] == func_nombre), None)
        curso_id = next((c["id"] for c in self.lista_cursos if c["nombre"] == curso_nombre), None)

        if not func_id:
            self.lbl_error.configure(text="Seleccione un funcionario válido.")
            return

        items = []
        for rec_id, data in self.recurso_inputs.items():
            if data["check_var"].get():
                try:
                    cant = int(data["cant_entry"].get().strip())
                    if cant <= 0:
                        self.lbl_error.configure(text=f"La cantidad para {data['nombre']} debe ser mayor a 0.")
                        return
                except ValueError:
                    self.lbl_error.configure(text=f"Cantidad inválida para {data['nombre']}.")
                    return
                items.append({"recurso_id": rec_id, "cantidad": cant})

        if not items:
            self.lbl_error.configure(text="Debe seleccionar al menos un recurso o la Sala.")
            return

        try:
            if not self.prestamo_id:
                if hasattr(self, "var_recurrente") and self.var_recurrente.get():
                    f_rep = self.entry_fecha_fin_rep.get().strip()
                    exito, mensaje = StockService.crear_prestamo_recurrente(
                        fecha, f_rep, h_ini, h_fin, func_id, curso_id, obs, items
                    )
                else:
                    exito, mensaje = StockService.crear_prestamo(
                        fecha, h_ini, h_fin, func_id, curso_id, obs, items
                    )
            else:
                exito, mensaje = self._actualizar_prestamo(func_id, curso_id, fecha, h_ini, h_fin, obs, items)

            if not exito:
                self.lbl_error.configure(text=mensaje)
            else:
                self.on_save()
                self.destroy()
        except Exception as e:
            self.lbl_error.configure(text=f"Error inesperado: {str(e)}")

    def _actualizar_prestamo(self, func_id, curso_id, fecha, h_ini, h_fin, obs, items):
        if h_fin and h_fin <= h_ini:
            return False, "La hora de término debe ser posterior a la de inicio."

        for item in items:
            rec_id = item["recurso_id"]
            cant_pedida = item["cantidad"]
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre, tipo FROM recursos WHERE id = ?;", (rec_id,))
            rec = cur.fetchone()
            conn.close()

            if rec["tipo"] == "espacio":
                libre, motivo = StockService.verificar_disponibilidad_sala(fecha, h_ini, h_fin, exclude_prestamo_id=self.prestamo_id)
                if not libre:
                    return False, motivo
            else:
                disponibles = StockService.get_stock_disponible(rec_id, fecha, h_ini, h_fin, exclude_prestamo_id=self.prestamo_id)
                if cant_pedida > disponibles:
                    return False, f"Stock insuficiente para {rec['nombre']}. Libres: {disponibles}."

        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE prestamos
                SET funcionario_id = ?, curso_id = ?, fecha = ?, hora_inicio = ?, hora_fin = ?, observaciones = ?
                WHERE id = ?;
            """, (func_id, curso_id, fecha, h_ini, h_fin, obs, self.prestamo_id))

            cur.execute("DELETE FROM prestamo_detalles WHERE prestamo_id = ?;", (self.prestamo_id,))
            for item in items:
                cur.execute("""
                    INSERT INTO prestamo_detalles (prestamo_id, recurso_id, cantidad)
                    VALUES (?, ?, ?);
                """, (self.prestamo_id, item["recurso_id"], item["cantidad"]))

        return True, "Actualizado exitosamente"