"""
ui/components/paginator.py
Barra de navegación y controles de paginación para tablas en CustomTkinter.
"""

import customtkinter as ctk
from ui.theme import Theme

class Paginator(ctk.CTkFrame):
    def __init__(self, parent, on_page_change_callback, items_per_page=10):
        super().__init__(parent, fg_color="transparent")
        
        self.on_page_change = on_page_change_callback
        self.items_per_page = items_per_page
        self.current_page = 1
        self.total_items = 0
        self.total_pages = 1

        # Controles visuales
        self.btn_prev = ctk.CTkButton(
            self, 
            text="◀ Anterior", 
            width=90, 
            height=30,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self.prev_page
        )
        self.btn_prev.pack(side="left", padx=5)

        self.lbl_info = ctk.CTkLabel(
            self, 
            text="Página 1 de 1 (0 registros)", 
            font=("Segoe UI", 12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_info.pack(side="left", padx=15)

        self.btn_next = ctk.CTkButton(
            self, 
            text="Siguiente ▶", 
            width=90, 
            height=30,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            command=self.next_page
        )
        self.btn_next.pack(side="left", padx=5)

    def update_totals(self, total_items: int):
        """Actualiza el total de elementos y recalcula páginas."""
        self.total_items = total_items
        self.total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        self.lbl_info.configure(
            text=f"Página {self.current_page} de {self.total_pages} ({self.total_items} registros)"
        )
        
        # Desactivar botones en límites
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < self.total_pages else "disabled")

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.on_page_change(self.current_page)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.on_page_change(self.current_page)

    def reset(self):
        self.current_page = 1