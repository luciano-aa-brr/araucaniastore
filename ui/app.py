"""
ui/app.py
Ventana principal de AraucaníaStock
"""

import customtkinter as ctk
from ui.theme import Theme
from ui.components.status_bar import StatusBar

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

        # Pie de Sidebar (Crédito KoaLink)
        self.frame_side_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_side_footer.pack(side="bottom", pady=15, padx=10, fill="x")

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

        # Placeholder temporal
        self.lbl_placeholder = ctk.CTkLabel(
            self.main_content,
            text="Panel de Préstamos Activos\n(En construcción para el siguiente paso)",
            font=("Segoe UI", 16),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_placeholder.pack(expand=True)

    def switch_view(self, view_name: str):
        print(f"Cambiando a la vista: {view_name}")