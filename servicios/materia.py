"""Servicios de materias."""
from database.conexion import conexion


def listar_materias_de_curso(curso_id: int) -> list[dict]:
    """Devuelve las materias de un curso, ordenadas por nombre."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, curso_id
            FROM materia
            WHERE curso_id = ?
            ORDER BY nombre
        """, (curso_id,))
        return [dict(fila) for fila in cursor.fetchall()]