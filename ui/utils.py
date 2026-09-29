"""
ui/utils.py
Funciones utilitarias para la interfaz gráfica.
"""

def centrar_ventana(ventana, ancho: int, alto: int):
    """
    Centra una ventana o modal CTkToplevel en la pantalla del usuario.
    """
    ventana.update_idletasks()
    
    # Dimensiones de la pantalla
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    # Cálculo del punto de origen (esquina superior izquierda)
    pos_x = int((pantalla_ancho - ancho) / 2)
    pos_y = int((pantalla_alto - alto) / 2)

    ventana.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")