"""
ui/app.py
Ventana principal de AraucaníaStock con barra de estado, navegación y respaldo portable.
"""

import os
import shutil
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

from ui.theme import Theme
from ui.components.status_bar import StatusBar
from ui.views.loans_view import LoansView
from ui.views.inventory_view import InventoryView
from ui.views.history_view import HistoryView
from database.connection import DB_NAME, BASE_DIR

class AraucaniaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración básica de ventana
        self.title("AraucaníaStock - Gestión Sala Multiuso")
        self.geometry("1100x680")
        self.minsize(950, 580)
        ctk.set_appearance_mode("dark")

        # Iniciar maximizado automáticamente
        self.after(0, lambda: self.state("zoomed"))

        # Layout general: Grid 2x2
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Barra Superior (Full Width)
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        # 2. Sidebar Izquierdo de Navegación
        self.sidebar = ctk.CTkFrame(self, fg_color=Theme.BG_SIDEBAR, width=220, corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # Título / Identidad en Sidebar
        self.lbl_app_name = ctk.CTkLabel(
            self.sidebar,
            text="Escuela Araucanía 510",
            font=("Segoe UI", 16, "bold"),
            text_color=Theme.ACCENT_YELLOW
        )
        self.lbl_app_name.pack(pady=(20, 5), padx=10)

        self.lbl_subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Control de Recursos y Sala",
            font=("Segoe UI", 11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_subtitle.pack(pady=(0, 25), padx=10)

        # Botones de navegación
        self.nav_buttons = {}

        self.btn_nav_prestamos = ctk.CTkButton(
            self.sidebar,
            text="📋 Préstamos Activos",
            anchor="w",
            height=38,
            font=("Segoe UI", 13),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            command=lambda: self.switch_view("prestamos")
        )
        self.btn_nav_prestamos.pack(fill="x", padx=12, pady=5)
        self.nav_buttons["prestamos"] = self.btn_nav_prestamos

        self.btn_nav_inventario = ctk.CTkButton(
            self.sidebar,
            text="📦 Inventario y Stock",
            anchor="w",
            height=38,
            font=("Segoe UI", 13),
            fg_color="transparent",
            hover_color=Theme.BORDER_COLOR,
            command=lambda: self.switch_view("inventario")
        )
        self.btn_nav_inventario.pack(fill="x", padx=12, pady=5)
        self.nav_buttons["inventario"] = self.btn_nav_inventario

        self.btn_nav_historial = ctk.CTkButton(
            self.sidebar,
            text="📜 Historial Completo",
            anchor="w",
            height=38,
            font=("Segoe UI", 13),
            fg_color="transparent",
            hover_color=Theme.BORDER_COLOR,
            command=lambda: self.switch_view("historial")
        )
        self.btn_nav_historial.pack(fill="x", padx=12, pady=5)
        self.nav_buttons["historial"] = self.btn_nav_historial

        # Pie de Sidebar (Botón Backup y Crédito KoaLink)
        self.frame_side_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_side_footer.pack(side="bottom", pady=15, padx=12, fill="x")

        self.btn_backup = ctk.CTkButton(
            self.frame_side_footer,
            text="💾 Respaldar Base de Datos",
            height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self.hacer_backup_db
        )
        self.btn_backup.pack(fill="x", pady=(0, 12))

        self.lbl_footer_koalink = ctk.CTkLabel(
            self.frame_side_footer,
            text="KoaLink Solutions\nLabranza, Temuco",
            font=("Segoe UI", 10),
            text_color=Theme.TEXT_MUTED,
            justify="center"
        )
        self.lbl_footer_koalink.pack()

        # 3. Contenedor de Vistas Principal
        self.main_content = ctk.CTkFrame(self, fg_color=Theme.BG_DARK, corner_radius=0)
        self.main_content.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)

        # Montar vista inicial
        self.current_view = LoansView(self.main_content, on_data_changed_callback=self.status_bar.refresh_status)
        self.current_view.pack(fill="both", expand=True)

    def switch_view(self, view_name: str):
        """Maneja el cambio visual de vistas y actualiza los botones del sidebar."""
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=Theme.BG_CARD if name == view_name else "transparent")

        if hasattr(self, "current_view") and self.current_view:
            self.current_view.destroy()

        if view_name == "prestamos":
            self.current_view = LoansView(self.main_content, on_data_changed_callback=self.status_bar.refresh_status)
            self.current_view.pack(fill="both", expand=True)
        elif view_name == "inventario":
            self.current_view = InventoryView(self.main_content, on_stock_changed_callback=self.status_bar.refresh_status)
            self.current_view.pack(fill="both", expand=True)
        elif view_name == "historial":
            self.current_view = HistoryView(self.main_content)
            self.current_view.pack(fill="both", expand=True)

    def hacer_backup_db(self):
        """Copia la base de datos araucaniastore.db de forma segura con marca de tiempo."""
        if not os.path.exists(DB_NAME):
            messagebox.showerror("Error", "No se encontró el archivo de base de datos para respaldar.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_defecto = f"respaldo_araucaniastore_{timestamp}.db"

        # Ofrecer al usuario elegir dónde guardar el respaldo
        ruta_destino = filedialog.asksaveasfilename(
            initialfile=nombre_defecto,
            defaultextension=".db",
            filetypes=[("Base de Datos SQLite", "*.db"), ("Todos los archivos", "*.*")],
            title="Guardar copia de seguridad de la base de datos"
        )

        if ruta_destino:
            try:
                shutil.copy2(DB_NAME, ruta_destino)
                messagebox.showinfo("Copia Exitosa", f"Respaldo creado correctamente en:\n{ruta_destino}")
            except Exception as e:
                messagebox.showerror("Error de Respaldo", f"No se pudo completar la copia:\n{str(e)}")