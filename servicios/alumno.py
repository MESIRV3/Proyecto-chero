"""Servicios de alumnos: busqueda y consultas."""
from database.conexion import conexion


def listar_alumnos_de_curso(curso_id: int) -> list[dict]:
    """Devuelve la lista de alumnos activos de un curso, ordenados por apellido."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero, nombre, apellido, dni
            FROM alumno
            WHERE curso_id = ? AND activo = 1
            ORDER BY apellido, nombre
        """, (curso_id,))
        return [dict(fila) for fila in cursor.fetchall()]


def obtener_alumno(numero: int) -> dict | None:
    """Devuelve un alumno por su numero de legajo, o None si no existe."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero, nombre, apellido, dni, curso_id, activo
            FROM alumno
            WHERE numero = ?
        """, (numero,))
        fila = cursor.fetchone()
        return dict(fila) if fila else None


def listar_cursos() -> list[dict]:
    """Devuelve todos los cursos del ciclo lectivo actual."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.turno, cl.anio as ciclo
            FROM curso c
            JOIN ciclo_lectivo cl ON c.ciclo_id = cl.id
            ORDER BY c.anio, c.division
        """)
        return [dict(fila) for fila in cursor.fetchall()]
