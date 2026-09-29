"""
ui/theme.py
Paleta de colores pastel basada en el logo de Escuela Araucanía 510
"""

class Theme:
    # Fondos principales (modo oscuro pastel)
    BG_DARK = "#1E1E24"
    BG_CARD = "#2B2D42"
    BG_SIDEBAR = "#181920"
    
    # Derivados del Amarillo institucional (pasteles, suaves)
    ACCENT_YELLOW = "#F4D06F"       # Amarillo pastel principal
    ACCENT_YELLOW_HOVER = "#E0BC5B" # Hover de botones amarillos
    
    # Tonos de estado (Semáforo visual)
    COLOR_SUCCESS = "#81C784"       # Verde pastel (Disponible / Devuelto)
    COLOR_WARNING = "#FFB74D"       # Naranja pastel (Poco stock / Pendiente)
    COLOR_DANGER = "#E57373"        # Rojo pastel (Ocupado / Sin stock)
    
    # Textos y bordes
    TEXT_MAIN = "#EDF2F4"
    TEXT_MUTED = "#8D99AE"
    BORDER_COLOR = "#3D405B"
    
    # Firma KoaLink
    BRAND_TAG = "Desarrollado por KoaLink"