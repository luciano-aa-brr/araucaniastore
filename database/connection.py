"""
database/connection.py
Conexión SQLite, transacciones seguras y datos semilla para AraucaníaStock.
"""

import sqlite3
import os
import sys
from contextlib import contextmanager

# Detectar ruta real (tanto en script .py como en ejecutable .exe compilado en USB)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DB_NAME = os.path.join(BASE_DIR, "araucaniastore.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_cursor():
    """Manejo de transacciones seguras. Hace rollback automático ante cualquier error."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    with get_db_cursor() as cur:
        # 1. Tabla de Funcionarios / Solicitantes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                activo INTEGER DEFAULT 1
            );
        """)

        # 2. Tabla de Cursos / Destinos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                activo INTEGER DEFAULT 1
            );
        """)

        # 3. Tabla de Recursos (Sala, Lotes de Tablets, Notebooks, Cables)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                tipo TEXT CHECK(tipo IN ('espacio', 'lote', 'individual')) NOT NULL,
                stock_total INTEGER NOT NULL DEFAULT 1 CHECK(stock_total >= 0),
                activo INTEGER DEFAULT 1
            );
        """)

        # 4. Tabla Maestra de Préstamos (hora_fin puede ser NULL para indefinidos)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,          -- Formato YYYY-MM-DD
                hora_inicio TEXT NOT NULL,    -- Formato HH:MM
                hora_fin TEXT,                -- Formato HH:MM (o NULL para uso continuo/indefinido)
                funcionario_id INTEGER NOT NULL,
                curso_id INTEGER,
                observaciones TEXT,
                estado TEXT CHECK(estado IN ('activo', 'devuelto', 'cancelado')) DEFAULT 'activo',
                fecha_devolucion TEXT,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE SET NULL
            );
        """)

        # 5. Detalle de Ítems en cada Préstamo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prestamo_detalles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prestamo_id INTEGER NOT NULL,
                recurso_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1 CHECK(cantidad > 0),
                FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE CASCADE,
                FOREIGN KEY (recurso_id) REFERENCES recursos(id) ON DELETE RESTRICT
            );
        """)

        # 6. Tabla de Préstamos Recurrentes (Semanal: Martes, Viernes, etc.)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prestamos_recurrentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                curso_id INTEGER,
                dia_semana INTEGER NOT NULL, -- 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT,               -- Opcional / Indefinido
                fecha_fin_repeticion TEXT NOT NULL, -- YYYY-MM-DD hasta cuándo dura
                observaciones TEXT,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE SET NULL
            );
        """)

        # 7. Detalle de ítems de préstamos recurrentes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prestamo_recurrente_detalles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurrente_id INTEGER NOT NULL,
                recurso_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1 CHECK(cantidad > 0),
                FOREIGN KEY (recurrente_id) REFERENCES prestamos_recurrentes(id) ON DELETE CASCADE,
                FOREIGN KEY (recurso_id) REFERENCES recursos(id) ON DELETE RESTRICT
            );
        """)

        # 8. Semilla inicial de datos tomados del Excel
        _seed_initial_data(cur)

def _seed_initial_data(cur):
    cur.execute("SELECT COUNT(*) as count FROM funcionarios;")
    if cur.fetchone()["count"] == 0:
        funcionarios = [
            "Miguel Riffo", "Vanesa", "Alumnas en practica", "Maria José",
            "Guacolda", "Laura", "Valeria Riquelme", "Rosa Isla",
            "Mario Novoa", "Daniela Carbajo", "Ana Vasquez", "Osvaldo",
            "Nadia", "Angela Sagredo", "Ceci"
        ]
        for f in funcionarios:
            cur.execute("INSERT OR IGNORE INTO funcionarios (nombre) VALUES (?);", (f,))

    cur.execute("SELECT COUNT(*) as count FROM cursos;")
    if cur.fetchone()["count"] == 0:
        cursos = [
            "1°", "2°", "3°", "4°", "5°", "6°", "7°", "8°",
            "Taller", "Centro de Padres", "Reforzamiento", "Inspectoría"
        ]
        for c in cursos:
            cur.execute("INSERT OR IGNORE INTO cursos (nombre) VALUES (?);", (c,))

    cur.execute("SELECT COUNT(*) as count FROM recursos;")
    if cur.fetchone()["count"] == 0:
        recursos = [
            ("Sala Multiuso", "espacio", 1),
            ("Tablets", "lote", 50),
            ("Notebook HP", "individual", 5),
            ("Cable Micro USB", "individual", 4),
            ("Cable HDMI", "individual", 4),
            ("Audífonos", "lote", 30)
        ]
        for nombre, tipo, stock in recursos:
            cur.execute("""
                INSERT OR IGNORE INTO recursos (nombre, tipo, stock_total)
                VALUES (?, ?, ?);
            """, (nombre, tipo, stock))

if __name__ == "__main__":
    init_database()
    print("Base de datos araucaniastore.db inicializada correctamente.")