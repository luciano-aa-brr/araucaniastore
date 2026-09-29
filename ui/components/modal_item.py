"""
ui/components/modal_item.py
Modal centrado y estilizado para agregar Recursos, Funcionarios o Cursos.
"""

import customtkinter as ctk
from ui.theme import Theme
from ui.utils import centrar_ventana

class ModalItem(ctk.CTkToplevel):
    def __init__(self, parent, seccion: str, on_save_callback):
        super().__init__(parent)
        self.seccion = seccion
        self.on_save = on_save_callback

        titulo = f"Agregar {seccion.capitalize().rstrip('s')}"
        self.title(titulo)
        
        # Ajuste de altura suficiente para que los botones nunca se corten
        alto = 390 if seccion == "recursos" else 260
        centrar_ventana(self, ancho=440, alto=alto)
        
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._construir_ui()

    def _construir_ui(self):
        # Título
        lbl_titulo = ctk.CTkLabel(
            self,
            text=f"Nuevo Registro: {self.seccion.capitalize()}",
            font=("Segoe UI", 15, "bold"),
            text_color=Theme.ACCENT_YELLOW
        )
        lbl_titulo.pack(pady=(15, 10))

        # Contenedor inferior de botones (fijado abajo)
        btns_frame = ctk.CTkFrame(self, fg_color="transparent")
        btns_frame.pack(side="bottom", fill="x", padx=25, pady=(0, 20))

        btn_cancelar = ctk.CTkButton(
            btns_frame, text="Cancelar", height=36,
            fg_color=Theme.BG_CARD, hover_color=Theme.BORDER_COLOR,
            command=self.destroy
        )
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_guardar = ctk.CTkButton(
            btns_frame, text="Guardar", height=36,
            fg_color=Theme.ACCENT_YELLOW, hover_color=Theme.ACCENT_YELLOW_HOVER,
            text_color="#1E1E24", font=("Segoe UI", 12, "bold"),
            command=self._guardar
        )
        btn_guardar.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Mensaje de error/alerta (justo arriba de los botones)
        self.lbl_error = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color=Theme.COLOR_DANGER)
        self.lbl_error.pack(side="bottom", fill="x", padx=25, pady=(0, 6))

        # Formulario principal
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(side="top", fill="both", expand=True, padx=25)

        # Campo: Nombre
        ctk.CTkLabel(form, text="Nombre:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        self.entry_nombre = ctk.CTkEntry(form, height=34, placeholder_text="Ingrese el nombre...")
        self.entry_nombre.pack(fill="x", pady=(3, 10))

        # Campos adicionales solo para recursos
        if self.seccion == "recursos":
            ctk.CTkLabel(form, text="Tipo de Recurso:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
            self.combo_tipo = ctk.CTkComboBox(
                form,
                values=["Lote (Cantidades/Bolsa)", "Individual (Único)", "Espacio (Sala/Lugar)"],
                height=34,
                dropdown_fg_color=Theme.BG_CARD
            )
            self.combo_tipo.set("Lote (Cantidades/Bolsa)")
            self.combo_tipo.pack(fill="x", pady=(3, 10))

            ctk.CTkLabel(form, text="Stock Inicial:", font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
            self.entry_stock = ctk.CTkEntry(form, height=34)
            self.entry_stock.insert(0, "1")
            self.entry_stock.pack(fill="x", pady=(3, 6))

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            self.lbl_error.configure(text="El nombre no puede estar vacío.")
            return

        if self.seccion == "recursos":
            tipo_map = {
                "Lote (Cantidades/Bolsa)": "lote",
                "Individual (Único)": "individual",
                "Espacio (Sala/Lugar)": "espacio"
            }
            tipo_val = tipo_map.get(self.combo_tipo.get(), "lote")
            try:
                stock_val = int(self.entry_stock.get().strip())
                if stock_val < 0:
                    self.lbl_error.configure(text="El stock no puede ser negativo.")
                    return
            except ValueError:
                self.lbl_error.configure(text="El stock debe ser un número entero.")
                return

            self.on_save(nombre, tipo_val, stock_val)
        else:
            self.on_save(nombre)

        self.destroy()