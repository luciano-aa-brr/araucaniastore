"""
ui/components/status_bar.py
Barra superior de estado con disponibilidad en vivo, reloj digital y botón de recarga.
"""

from datetime import datetime
import customtkinter as ctk
from ui.theme import Theme
from services.stock_service import StockService

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=Theme.BG_SIDEBAR, height=52, corner_radius=0)
        self.pack_propagate(False)

        # 1. Contenedor Izquierdo (Semáforos de Disponibilidad)
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", padx=20, fill="y")

        # Sala Multiuso
        self.lbl_sala_tag = ctk.CTkLabel(
            self.left_frame,
            text="Sala Multiuso:",
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_sala_tag.pack(side="left", padx=(0, 6), pady=12)

        self.badge_sala = ctk.CTkLabel(
            self.left_frame,
            text="LIBRE",
            font=("Segoe UI", 11, "bold"),
            text_color="#1E1E24",
            fg_color=Theme.COLOR_SUCCESS,
            corner_radius=6,
            width=70,
            height=26
        )
        self.badge_sala.pack(side="left", padx=(0, 20), pady=12)

        # Tablets
        self.lbl_tablets_tag = ctk.CTkLabel(
            self.left_frame,
            text="Tablets Libres:",
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_tablets_tag.pack(side="left", padx=(0, 6), pady=12)

        self.badge_tablets = ctk.CTkLabel(
            self.left_frame,
            text="-- / --",
            font=("Segoe UI", 11, "bold"),
            text_color="#1E1E24",
            fg_color=Theme.ACCENT_YELLOW,
            corner_radius=6,
            width=80,
            height=26
        )
        self.badge_tablets.pack(side="left", padx=(0, 10), pady=12)

        # 2. Contenedor Derecho (Botón de refresco y crédito)
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", padx=20, fill="y")

        self.lbl_brand = ctk.CTkLabel(
            self.right_frame,
            text="⚡ Desarrollado por KoaLink",
            font=("Segoe UI", 10, "italic"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_brand.pack(side="right", padx=(12, 0), pady=12)

        self.btn_refresh = ctk.CTkButton(
            self.right_frame,
            text="🔄 Actualizar",
            width=90,
            height=28,
            font=("Segoe UI", 11),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            command=self.refresh_status
        )
        self.btn_refresh.pack(side="right", pady=12)

        # 3. Contenedor Central (Fecha y Reloj en tiempo real)
        self.lbl_clock = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_clock.pack(side="left", expand=True)

        self._actualizar_reloj()
        self.refresh_status()

    def _actualizar_reloj(self):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        ahora = datetime.now()
        dia_nom = dias[ahora.weekday()]
        mes_nom = meses[ahora.month - 1]
        
        texto_tiempo = f"📅 {dia_nom}, {ahora.day} de {mes_nom} de {ahora.year}   •   ⏰ {ahora.strftime('%H:%M:%S')} hrs"
        self.lbl_clock.configure(text=texto_tiempo)
        
        # Reprogramar ejecución cada 1000 ms (1 segundo)
        self.after(1000, self._actualizar_reloj)

    def refresh_status(self):
        try:
            resumen = StockService.get_resumen_disponibilidad_actual()
            
            # Actualizar badge de Sala
            if resumen["sala_libre"]:
                self.badge_sala.configure(text="LIBRE", fg_color=Theme.COLOR_SUCCESS, text_color="#1E1E24")
            else:
                self.badge_sala.configure(text="OCUPADA", fg_color=Theme.COLOR_DANGER, text_color="#FFFFFF")

            # Actualizar badge de Tablets
            libres = resumen["tablets_libres"]
            totales = resumen["tablets_totales"]
            self.badge_tablets.configure(text=f"{libres} / {totales}")
            
            if libres == 0:
                self.badge_tablets.configure(fg_color=Theme.COLOR_DANGER, text_color="#FFFFFF")
            elif libres < 10:
                self.badge_tablets.configure(fg_color=Theme.COLOR_WARNING, text_color="#1E1E24")
            else:
                self.badge_tablets.configure(fg_color=Theme.ACCENT_YELLOW, text_color="#1E1E24")

        except Exception as e:
            print("Error al refrescar barra de estado:", e)