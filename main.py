"""
main.py
Punto de entrada de AraucaníaStock
"""

import sys
import os

# Asegurar que la raíz esté en sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database
from ui.app import AraucaniaApp

def main():
    # 1. Asegurar que la base de datos y tablas existan
    init_database()

    # 2. Iniciar la interfaz gráfica
    app = AraucaniaApp()
    app.mainloop()

if __name__ == "__main__":
    main()