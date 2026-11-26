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


def obtener_asistencia_materia(curso_id: int, materia_id: int, fecha: str) -> Resultado:
    """
    Obtiene los alumnos activos de un curso y su estado de asistencia para una materia y fecha dada (YYYY-MM-DD).
    Si un alumno todavia no fue registrado para esa fecha y materia, su estado por defecto sera 'presente'.
    """
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.numero, a.nombre, a.apellido, a.dni, a.nacionalidad,
                    ast.estado, ast.observaciones, ast.id as asistencia_id
                FROM alumno a
                LEFT JOIN asistencia ast 
                    ON ast.alumno_numero = a.numero 
                   AND ast.materia_id = ? 
                   AND ast.fecha = ?
                WHERE a.curso_id = ? AND a.activo = 1
                ORDER BY a.apellido, a.nombre
            """, (materia_id, fecha, curso_id))

            filas = cursor.fetchall()
            alumnos = []
            ya_registrado = False
            for f in filas:
                d = dict(f)
                if d["estado"] is not None:
                    ya_registrado = True
                else:
                    d["estado"] = "presente"
                if d.get("observaciones") is None:
                    d["observaciones"] = ""
                alumnos.append(d)

            return Resultado.exito(datos={"alumnos": alumnos, "ya_registrado": ya_registrado})
    except Exception as e:
        return Resultado.error(f"Error al obtener asistencia de materia: {e}")


def guardar_asistencia_materia(
    materia_id: int, fecha: str, registros: list[dict], profesor_id: int
) -> Resultado:
    """
    Guarda la asistencia de catedra de un grupo de alumnos para una fecha dada (YYYY-MM-DD).
    registros: lista de dicts con:
      - alumno_numero: int
      - estado: str ('presente', 'ausente')
      - observaciones: str | None
    """
    estados_validos = ("presente", "ausente")
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            for r in registros:
                num = r["alumno_numero"]
                est = r["estado"]
                if est not in estados_validos:
                    return Resultado.error(f"Estado invalido '{est}' para alumno {num}")
                obs = r.get("observaciones")
                if obs is not None:
                    obs = obs.strip() or None

                cursor.execute("""
                    INSERT INTO asistencia
                        (alumno_numero, materia_id, fecha, estado, observaciones, registrado_por)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alumno_numero, materia_id, fecha) DO UPDATE SET
                        estado = excluded.estado,
                        observaciones = excluded.observaciones,
                        registrado_por = excluded.registrado_por
                """, (num, materia_id, fecha, est, obs, profesor_id))

        return Resultado.exito("Asistencia de cátedra guardada correctamente")
    except Exception as e:
        return Resultado.error(f"Error al guardar asistencia de materia: {e}")


def listar_historial_asistencia(
    curso_id: int | None = None,
    alumno_numero: int | None = None,
    materia_id: int | None = None,
    profesor_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    ciclo_id: int | None = None,
    turno: str | None = None,
) -> list[dict]:
    """
    Devuelve registros historicos de asistencia de catedra con datos del alumno, materia, curso y docente.
    Permite filtrar por turno, curso, alumno, materia, profesor y rango de fechas.
    """
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            condiciones = []
            parametros = []

            if turno:
                condiciones.append("c.turno = ?")
                parametros.append(turno)
            if curso_id:
                condiciones.append("c.id = ?")
                parametros.append(curso_id)
            if alumno_numero:
                condiciones.append("a.numero = ?")
                parametros.append(alumno_numero)
            if materia_id:
                condiciones.append("m.id = ?")
                parametros.append(materia_id)
            if profesor_id:
                condiciones.append("ast.registrado_por = ?")
                parametros.append(profesor_id)
            if fecha_desde:
                condiciones.append("ast.fecha >= ?")
                parametros.append(fecha_desde)
            if fecha_hasta:
                condiciones.append("ast.fecha <= ?")
                parametros.append(fecha_hasta)
            if ciclo_id:
                condiciones.append("c.ciclo_id = ?")
                parametros.append(ciclo_id)

            where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

            query = f"""
                SELECT 
                    ast.id, ast.fecha, ast.estado, ast.observaciones,
                    a.numero AS alumno_numero, a.nombre AS alumno_nombre, a.apellido AS alumno_apellido, a.dni,
                    m.id AS materia_id, m.nombre AS materia_nombre,
                    c.id AS curso_id, c.anio, c.division, c.especialidad, c.turno,
                    u.nombre AS profesor_nombre, u.apellido AS profesor_apellido
                FROM asistencia ast
                JOIN alumno a ON ast.alumno_numero = a.numero
                JOIN materia m ON ast.materia_id = m.id
                JOIN curso c ON a.curso_id = c.id
                LEFT JOIN usuario u ON ast.registrado_por = u.id
                {where}
                ORDER BY ast.fecha DESC, m.nombre ASC, a.apellido ASC, a.nombre ASC
            """
            cursor.execute(query, parametros)
            filas = cursor.fetchall()
            resultado = []
            for f in filas:
                d = dict(f)
                esp = f" - {d['especialidad']}" if d.get("especialidad") else ""
                d["curso_nombre"] = f"{d['anio']}° {d['division']}{esp} ({d['turno']})"
                d["alumno_completo"] = f"{d['alumno_apellido']}, {d['alumno_nombre']}"
                if d.get("profesor_nombre"):
                    d["profesor_completo"] = f"{d['profesor_nombre']} {d.get('profesor_apellido', '')}".strip()
                else:
                    d["profesor_completo"] = "N/A"
                resultado.append(d)
            return resultado
    except Exception as e:
        print(f"Error al listar historial de asistencia de catedra: {e}")
        return []


