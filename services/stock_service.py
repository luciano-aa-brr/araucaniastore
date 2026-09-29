"""
services/stock_service.py
Lógica de cálculo de disponibilidad de stock, validaciones horarias e indefinidas/recurrentes.
"""

from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from database.connection import get_connection, get_db_cursor

class StockService:

    @staticmethod
    def _horarios_se_solapan(inicio_a: str, fin_a: Optional[str], inicio_b: str, fin_b: Optional[str]) -> bool:
        """
        Determina si dos rangos horarios se solapan.
        Si fin_a o fin_b es None o vacío, se considera ocupación de jornada completa.
        """
        if not fin_a or fin_a.strip() == "" or not fin_b or fin_b.strip() == "":
            return True
        return not (fin_a <= inicio_b or fin_b <= inicio_a)

    @staticmethod
    def get_stock_disponible(recurso_id: int, fecha: str, hora_inicio: str, hora_fin: Optional[str] = None, exclude_prestamo_id: Optional[int] = None) -> int:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Obtener stock total
        cur.execute("SELECT stock_total FROM recursos WHERE id = ? AND activo = 1;", (recurso_id,))
        rec = cur.fetchone()
        if not rec:
            conn.close()
            return 0
        stock_total = rec["stock_total"]

        # 2. Obtener préstamos activos en esa fecha
        query = """
            SELECT p.id, p.hora_inicio, p.hora_fin, pd.cantidad
            FROM prestamos p
            JOIN prestamo_detalles pd ON p.id = pd.prestamo_id
            WHERE pd.recurso_id = ?
              AND p.fecha = ?
              AND p.estado = 'activo'
        """
        params = [recurso_id, fecha]

        if exclude_prestamo_id:
            query += " AND p.id != ?"
            params.append(exclude_prestamo_id)

        cur.execute(query, params)
        prestamos_activos = cur.fetchall()
        conn.close()

        # 3. Sumar cantidades que se solapan
        prestados = 0
        for p in prestamos_activos:
            if StockService._horarios_se_solapan(hora_inicio, hora_fin, p["hora_inicio"], p["hora_fin"]):
                prestados += p["cantidad"]

        return max(0, stock_total - prestados)

    @staticmethod
    def verificar_disponibilidad_sala(fecha: str, hora_inicio: str, hora_fin: Optional[str] = None, exclude_prestamo_id: Optional[int] = None) -> Tuple[bool, str]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM recursos WHERE tipo = 'espacio' AND nombre LIKE '%Sala%' LIMIT 1;")
        sala = cur.fetchone()
        if not sala:
            conn.close()
            return True, "No se encontró registro de Sala Multiuso."

        sala_id = sala["id"]
        query = """
            SELECT p.id, p.hora_inicio, p.hora_fin, f.nombre as profesor
            FROM prestamos p
            JOIN prestamo_detalles pd ON p.id = pd.prestamo_id
            JOIN funcionarios f ON p.funcionario_id = f.id
            WHERE pd.recurso_id = ?
              AND p.fecha = ?
              AND p.estado = 'activo'
        """
        params = [sala_id, fecha]

        if exclude_prestamo_id:
            query += " AND p.id != ?"
            params.append(exclude_prestamo_id)

        cur.execute(query, params)
        ocupaciones = cur.fetchall()
        conn.close()

        for o in ocupaciones:
            if StockService._horarios_se_solapan(hora_inicio, hora_fin, o["hora_inicio"], o["hora_fin"]):
                fin_txt = o["hora_fin"] if o["hora_fin"] else "Uso continuo"
                return False, f"La Sala Multiuso ya está reservada por {o['profesor']} ({o['hora_inicio']} - {fin_txt})."

        return True, "Sala disponible"

    @staticmethod
    def crear_prestamo(fecha: str, hora_inicio: str, hora_fin: Optional[str], funcionario_id: int, curso_id: Optional[int], observaciones: str, items: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if hora_fin and hora_fin.strip() != "":
            if hora_fin <= hora_inicio:
                return False, "La hora de término debe ser posterior a la de inicio."
        else:
            hora_fin = None

        # Validaciones de disponibilidad
        for item in items:
            rec_id = item["recurso_id"]
            cant_pedida = item["cantidad"]

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre, tipo FROM recursos WHERE id = ?;", (rec_id,))
            rec = cur.fetchone()
            conn.close()

            if not rec:
                return False, f"El recurso ID {rec_id} no existe."

            if rec["tipo"] == "espacio":
                libre, motivo = StockService.verificar_disponibilidad_sala(fecha, hora_inicio, hora_fin)
                if not libre:
                    return False, motivo
            else:
                disponibles = StockService.get_stock_disponible(rec_id, fecha, hora_inicio, hora_fin)
                if cant_pedida > disponibles:
                    return False, f"Stock insuficiente para '{rec['nombre']}'. Disponibles: {disponibles}, Solicitados: {cant_pedida}."

        # Insertar préstamo
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO prestamos (fecha, hora_inicio, hora_fin, funcionario_id, curso_id, observaciones, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'activo');
            """, (fecha, hora_inicio, hora_fin, funcionario_id, curso_id, observaciones))

            prestamo_id = cur.lastrowid

            for item in items:
                cur.execute("""
                    INSERT INTO prestamo_detalles (prestamo_id, recurso_id, cantidad)
                    VALUES (?, ?, ?);
                """, (prestamo_id, item["recurso_id"], item["cantidad"]))

        return True, "Préstamo registrado exitosamente"

    @staticmethod
    def crear_prestamo_recurrente(fecha_inicio: str, fecha_fin_repeticion: str, hora_inicio: str, hora_fin: Optional[str], funcionario_id: int, curso_id: Optional[int], observaciones: str, items: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Crea préstamos semanales repetidos en el mismo día de la semana hasta la fecha de término."""
        try:
            d_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            d_fin = datetime.strptime(fecha_fin_repeticion, "%Y-%m-%d")
        except ValueError:
            return False, "Formato de fecha inválido. Use YYYY-MM-DD."

        if d_fin < d_ini:
            return False, "La fecha de repetición final debe ser posterior a la fecha inicial."

        fechas_programadas = []
        actual = d_ini
        while actual <= d_fin:
            fechas_programadas.append(actual.strftime("%Y-%m-%d"))
            actual += timedelta(days=7)

        # Crear préstamo para cada una de las fechas
        exitosos = 0
        for f in fechas_programadas:
            exito, _ = StockService.crear_prestamo(f, hora_inicio, hora_fin, funcionario_id, curso_id, f"{observaciones} (Recurrente)", items)
            if exitosos == 0 and not exito:
                return False, f"Conflicto de disponibilidad en la fecha {f}."
            if exito:
                exitosos += 1

        return True, f"Se crearon {exitosos} préstamos semanales recurrentes con éxito."

    @staticmethod
    def marcar_como_devuelto(prestamo_id: int) -> bool:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE prestamos
                SET estado = 'devuelto', fecha_devolucion = ?
                WHERE id = ?;
            """, (ahora, prestamo_id))
        return True

    @staticmethod
    def get_resumen_disponibilidad_actual() -> Dict[str, Any]:
        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.strftime("%H:%M")

        conn = get_connection()
        cur = conn.cursor()

        # Tablets
        cur.execute("SELECT id, stock_total FROM recursos WHERE nombre LIKE '%Tablet%' LIMIT 1;")
        tab = cur.fetchone()
        tablets_libres = 0
        tablets_totales = 0
        if tab:
            tablets_totales = tab["stock_total"]
            tablets_libres = StockService.get_stock_disponible(tab["id"], fecha_hoy, hora_actual)

        # Sala
        cur.execute("SELECT id FROM recursos WHERE tipo = 'espacio' LIMIT 1;")
        sala = cur.fetchone()
        sala_libre = True
        if sala:
            libre, _ = StockService.verificar_disponibilidad_sala(fecha_hoy, hora_actual)
            sala_libre = libre

        conn.close()
        return {
            "sala_libre": sala_libre,
            "tablets_libres": tablets_libres,
            "tablets_totales": tablets_totales
        }