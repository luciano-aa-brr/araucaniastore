"""
services/stock_service.py
Gestión de stock, validación de solapamientos horarios y operaciones de préstamos.
"""

from datetime import datetime
from database.connection import get_db_cursor, get_connection

class StockService:

    @staticmethod
    def _horarios_se_solapan(inicio_a: str, fin_a: str, inicio_b: str, fin_b: str) -> bool:
        """
        Determina si dos rangos de horas se cruzan.
        Formato esperado: 'HH:MM'.
        Regla: No hay solapamiento si A termina antes o exactamente cuando inicia B,
        o si B termina antes o exactamente cuando inicia A.
        """
        return not (fin_a <= inicio_b or fin_b <= inicio_a)

    @staticmethod
    def verificar_disponibilidad_sala(fecha: str, hora_inicio: str, hora_fin: str, exclude_prestamo_id: int = None) -> tuple[bool, str]:
        """
        Verifica si la Sala Multiuso está ocupada en esa fecha y rango horario.
        Retorna (True, "") si está libre, o (False, "Motivo") si está ocupada.
        """
        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT p.id, p.hora_inicio, p.hora_fin, f.nombre as profesor
            FROM prestamos p
            JOIN prestamo_detalles pd ON p.id = pd.prestamo_id
            JOIN recursos r ON pd.recurso_id = r.id
            JOIN funcionarios f ON p.funcionario_id = f.id
            WHERE p.fecha = ?
              AND p.estado = 'activo'
              AND r.tipo = 'espacio'
        """
        params = [fecha]

        if exclude_prestamo_id:
            query += " AND p.id != ?"
            params.append(exclude_prestamo_id)

        cur.execute(query, params)
        reservas = cur.fetchall()
        conn.close()

        for res in reservas:
            if StockService._horarios_se_solapan(hora_inicio, hora_fin, res["hora_inicio"], res["hora_fin"]):
                return False, f"La sala ya está reservada por {res['profesor']} ({res['hora_inicio']} - {res['hora_fin']})"

        return True, "Disponible"

    @staticmethod
    def get_stock_disponible(recurso_id: int, fecha: str, hora_inicio: str, hora_fin: str, exclude_prestamo_id: int = None) -> int:
        """
        Calcula el stock libre de un recurso en un bloque horario determinado.
        """
        conn = get_connection()
        cur = conn.cursor()

        # 1. Obtener stock total registrado
        cur.execute("SELECT stock_total FROM recursos WHERE id = ?;", (recurso_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return 0
        stock_total = row["stock_total"]

        # 2. Obtener todos los préstamos activos de ese recurso en esa fecha
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

        # 3. Sumar solo las cantidades de los préstamos que coinciden en el horario
        prestados_en_horario = 0
        for p in prestamos_activos:
            if StockService._horarios_se_solapan(hora_inicio, hora_fin, p["hora_inicio"], p["hora_fin"]):
                prestados_en_horario += p["cantidad"]

        disponible = stock_total - prestados_en_horario
        return max(0, disponible)

    @staticmethod
    def get_resumen_disponibilidad_actual() -> dict:
        """
        Devuelve el estado en tiempo real (ahora mismo) para la barra superior:
        - Estado de la sala (Libre u Ocupada con nombre del docente)
        - Cantidad de tablets disponibles en este instante
        """
        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.strftime("%H:%M")

        # Rango de 1 minuto para chequear el instante actual
        hora_fin = f"{int(hora_actual.split(':')[0]):02d}:{int(hora_actual.split(':')[1])+1:02d}" if int(hora_actual.split(':')[1]) < 59 else "23:59"

        # 1. Estado Sala
        libre_sala, detalle_sala = StockService.verificar_disponibilidad_sala(fecha_hoy, hora_actual, hora_fin)

        # 2. Stock Tablets
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, stock_total FROM recursos WHERE nombre LIKE '%Tablet%' LIMIT 1;")
        tablet = cur.fetchone()
        conn.close()

        tablets_libres = 0
        tablets_totales = 0
        if tablet:
            tablets_totales = tablet["stock_total"]
            tablets_libres = StockService.get_stock_disponible(tablet["id"], fecha_hoy, hora_actual, hora_fin)

        return {
            "sala_libre": libre_sala,
            "sala_detalle": detalle_sala if not libre_sala else "Sala Libre",
            "tablets_libres": tablets_libres,
            "tablets_totales": tablets_totales
        }

    @staticmethod
    def crear_prestamo(fecha: str, hora_inicio: str, hora_fin: str, funcionario_id: int,
                       curso_id: int, observaciones: str, items: list[dict]) -> tuple[bool, str]:
        """
        items: lista de diccionarios [{'recurso_id': int, 'cantidad': int}]
        Valida disponibilidad y realiza inserción atómica.
        """
        # Validación de horarios coherentes
        if hora_fin <= hora_inicio:
            return False, "La hora de término debe ser posterior a la hora de inicio."

        # Validaciones de disponibilidad para cada ítem
        for item in items:
            rec_id = item["recurso_id"]
            cant_pedida = item["cantidad"]

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre, tipo FROM recursos WHERE id = ?;", (rec_id,))
            rec = cur.fetchone()
            conn.close()

            if not rec:
                return False, f"El recurso con ID {rec_id} no existe."

            if rec["tipo"] == "espacio":
                libre, motivo = StockService.verificar_disponibilidad_sala(fecha, hora_inicio, hora_fin)
                if not libre:
                    return False, motivo
            else:
                disponibles = StockService.get_stock_disponible(rec_id, fecha, hora_inicio, hora_fin)
                if cant_pedida > disponibles:
                    return False, f"Stock insuficiente para '{rec['nombre']}'. Solicitados: {cant_pedida}, Disponibles: {disponibles}."

        # Inserción con transacción segura
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

        return True, "Préstamo registrado exitosamente."

    @staticmethod
    def marcar_como_devuelto(prestamo_id: int) -> bool:
        """Marca un préstamo como devuelto y registra fecha/hora de devolución."""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE prestamos 
                SET estado = 'devuelto', fecha_devolucion = ?
                WHERE id = ?;
            """, (ahora, prestamo_id))
        return True

    