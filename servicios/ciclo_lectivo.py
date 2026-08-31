"""Servicios para manejar los ciclos lectivos (anio escolar)."""
from datetime import date

from database.conexion import conexion
from database.resultado import Resultado


def obtener_o_crear_ciclo_actual():
    """
    Devuelve el id del ciclo lectivo correspondiente al anio actual.
    Si no existe todavia, lo crea automaticamente (1 marzo - 15 diciembre).
    """
    anio_actual = date.today().year
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ciclo_lectivo WHERE anio = ?", (anio_actual,))
            fila = cursor.fetchone()
            if fila:
                return Resultado.exito(datos=fila["id"])

            cursor.execute(
                """
                INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin)
                VALUES (?, ?, ?)
                """,
                (anio_actual, f"{anio_actual}-03-01", f"{anio_actual}-12-15"),
            )
            nuevo_id = cursor.lastrowid
        return Resultado.exito("Ciclo lectivo creado automaticamente", datos=nuevo_id)
    except Exception as e:
        return Resultado.error(f"Error al obtener/crear el ciclo lectivo: {e}")


def listar_ciclos():
    """Devuelve todos los ciclos lectivos cargados, el mas nuevo primero."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ciclo_lectivo ORDER BY anio DESC")
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito(datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar ciclos lectivos: {e}")
