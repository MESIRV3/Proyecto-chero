"""Servicios de asistencia: registrar y calcular."""
from datetime import date
from database.conexion import conexion
from database.resultado import Resultado


def registrar_asistencia(
    alumno_numero: int,
    materia_id: int,
    fecha: str,
    estado: str,
    profesor_id: int,
    observaciones: str = None
) -> Resultado:
    """
    Registra la asistencia de un alumno en una materia, en una fecha.
    fecha en formato 'YYYY-MM-DD'.
    estado: 'presente' o 'ausente'.
    """
    # Validaciones de negocio
    if estado not in ("presente", "ausente"):
        return Resultado.error(f"Estado invalido: {estado}")

    try:
        with conexion() as conn:
            cursor = conn.cursor()

            # Verificar que el alumno existe
            cursor.execute(
                "SELECT numero FROM alumno WHERE numero = ? AND activo = 1",
                (alumno_numero,)
            )
            if not cursor.fetchone():
                return Resultado.error(f"El alumno {alumno_numero} no existe")

            # Verificar que la materia existe
            cursor.execute(
                "SELECT id FROM materia WHERE id = ?",
                (materia_id,)
            )
            if not cursor.fetchone():
                return Resultado.error(f"La materia {materia_id} no existe")

            # Insertar o reemplazar (por si se carga dos veces el mismo dia)
            cursor.execute("""
                INSERT INTO asistencia
                    (alumno_numero, materia_id, fecha, estado,
                     observaciones, registrado_por)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(alumno_numero, materia_id, fecha)
                DO UPDATE SET
                    estado = excluded.estado,
                    observaciones = excluded.observaciones,
                    registrado_por = excluded.registrado_por
            """, (alumno_numero, materia_id, fecha, estado,
                  observaciones, profesor_id))

        return Resultado.exito("Asistencia registrada")
    except Exception as e:
        return Resultado.error(f"Error al registrar: {str(e)}")


def calcular_porcentaje_asistencia(
    alumno_numero: int,
    materia_id: int,
    fecha_desde: str,
    fecha_hasta: str
) -> float:
    """
    Calcula el porcentaje de asistencia de un alumno en una materia,
    en un rango de fechas. Solo cuenta dias habiles.
    Devuelve un valor entre 0 y 100.
    """
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                ROUND(
                    (SUM(CASE WHEN a.estado='presente' THEN 1 ELSE 0 END) * 100.0)
                    / NULLIF(COUNT(*), 0),
                    2
                ) AS porcentaje
            FROM asistencia a
            WHERE a.alumno_numero = ?
              AND a.materia_id = ?
              AND a.fecha BETWEEN ? AND ?
              AND a.fecha IN (SELECT fecha FROM dia_habil WHERE es_habil = 1)
        """, (alumno_numero, materia_id, fecha_desde, fecha_hasta))

        fila = cursor.fetchone()
        return fila["porcentaje"] if fila and fila["porcentaje"] else 0.0


def listar_asistencias_de_alumno(
    alumno_numero: int,
    fecha_desde: str,
    fecha_hasta: str
) -> list[dict]:
    """Devuelve todas las asistencias de un alumno en un rango de fechas."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.fecha, a.estado, a.observaciones,
                   m.nombre as materia
            FROM asistencia a
            JOIN materia m ON a.materia_id = m.id
            WHERE a.alumno_numero = ?
              AND a.fecha BETWEEN ? AND ?
            ORDER BY a.fecha DESC, m.nombre
        """, (alumno_numero, fecha_desde, fecha_hasta))
        return [dict(fila) for fila in cursor.fetchall()]
