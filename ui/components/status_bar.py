"""
ui/components/status_bar.py
Barra superior de estado en tiempo real (Sala, Tablets) con paleta pastel y créditos KoaLink.
"""

import customtkinter as ctk
from ui.theme import Theme
from services.stock_service import StockService

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=Theme.BG_SIDEBAR, height=50, corner_radius=0)
        self.pack_propagate(False)

        # 1. Contenedor Izquierdo: Estado Sala Multiuso
        self.frame_sala = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_sala.pack(side="left", padx=15)

        self.lbl_sala_title = ctk.CTkLabel(
            self.frame_sala, 
            text="Sala Multiuso:", 
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_sala_title.pack(side="left", padx=(0, 6))

        self.badge_sala = ctk.CTkLabel(
            self.frame_sala,
            text="Consultando...",
            font=("Segoe UI", 11, "bold"),
            text_color="#1E1E24",
            fg_color=Theme.COLOR_WARNING,
            corner_radius=6,
            padx=10,
            pady=2
        )
        self.badge_sala.pack(side="left")

        # 2. Contenedor Centro: Disponibilidad de Tablets
        self.frame_tablets = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tablets.pack(side="left", padx=25)

        self.lbl_tab_title = ctk.CTkLabel(
            self.frame_tablets, 
            text="Tablets Libres:", 
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_tab_title.pack(side="left", padx=(0, 6))

        self.badge_tablets = ctk.CTkLabel(
            self.frame_tablets,
            text="-- / --",
            font=("Segoe UI", 11, "bold"),
            text_color="#1E1E24",
            fg_color=Theme.ACCENT_YELLOW,
            corner_radius=6,
            padx=10,
            pady=2
        )
        self.badge_tablets.pack(side="left")

        # 3. Contenedor Derecho: Botón de refresco manual + Tag KoaLink
        self.lbl_brand = ctk.CTkLabel(
            self,
            text=f"⚡ {Theme.BRAND_TAG}",
            font=("Segoe UI", 11, "italic"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_brand.pack(side="right", padx=15)

        self.btn_refresh = ctk.CTkButton(
            self,
            text="🔄 Actualizar",
            width=90,
            height=28,
            font=("Segoe UI", 11),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self.refresh_status
        )
        self.btn_refresh.pack(side="right", padx=10)

        # Cargar estado inicial
        self.refresh_status()

    def refresh_status(self):
        """Consulta el stock y actualiza los badges visuales."""
        data = StockService.get_resumen_disponibilidad_actual()

        # Actualizar badge de Sala
        if data["sala_libre"]:
            self.badge_sala.configure(
                text="LIBRE",
                fg_color=Theme.COLOR_SUCCESS,
                text_color="#1E1E24"
            )
        else:
            self.badge_sala.configure(
                text="OCUPADA",
                fg_color=Theme.COLOR_DANGER,
                text_color="#FFFFFF"
            )

        # Actualizar badge de Tablets
        libres = data["tablets_libres"]
        totales = data["tablets_totales"]
        self.badge_tablets.configure(text=f"{libres} / {totales}")

        if libres == 0:
            self.badge_tablets.configure(fg_color=Theme.COLOR_DANGER, text_color="#FFFFFF")
        elif libres < 10:
            self.badge_tablets.configure(fg_color=Theme.COLOR_WARNING, text_color="#1E1E24")
        else:
            self.badge_tablets.configure(fg_color=Theme.ACCENT_YELLOW, text_color="#1E1E24")