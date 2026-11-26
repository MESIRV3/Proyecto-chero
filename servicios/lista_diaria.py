"""Servicio de lista diaria (asistencia general por curso y fecha)."""
from datetime import datetime
from database.conexion import conexion
from database.resultado import Resultado


def obtener_lista_diaria(curso_id: int, fecha: str) -> Resultado:
    """
    Obtiene los alumnos activos de un curso y su estado en lista_diaria para la fecha indicada (YYYY-MM-DD).
    Si un alumno todavia no fue registrado para esa fecha, su estado por defecto sera 'presente'.
    """
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.numero, a.nombre, a.apellido, a.dni, a.nacionalidad,
                    ld.estado, ld.hora_llegada, ld.hora_retiro, ld.motivo_retiro,
                    ld.id as lista_diaria_id
                FROM alumno a
                LEFT JOIN lista_diaria ld 
                    ON ld.alumno_numero = a.numero AND ld.fecha = ?
                WHERE a.curso_id = ? AND a.activo = 1
                ORDER BY a.apellido, a.nombre
            """, (fecha, curso_id))

            filas = cursor.fetchall()
            alumnos = []
            ya_registrado = False
            for f in filas:
                d = dict(f)
                if d["estado"] is not None:
                    ya_registrado = True
                else:
                    d["estado"] = "presente"
                alumnos.append(d)

            return Resultado.exito(datos={"alumnos": alumnos, "ya_registrado": ya_registrado})
    except Exception as e:
        return Resultado.error(f"Error al obtener lista diaria: {e}")


def guardar_lista_diaria(fecha: str, registros: list[dict], usuario_id: int) -> Resultado:
    """
    Guarda la lista diaria de asistencia para una fecha dada (YYYY-MM-DD).
    registros: lista de dicts con:
      - alumno_numero: int
      - estado: str ('presente', 'ausente', 'tarde', 'retirado')
      - hora_llegada: str | None
      - hora_retiro: str | None
      - motivo_retiro: str | None
    """
    estados_validos = ("presente", "ausente", "tarde", "retirado")
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            for r in registros:
                num = r["alumno_numero"]
                est = r["estado"]
                if est not in estados_validos:
                    return Resultado.error(f"Estado invalido '{est}' para alumno {num}")

                hora_llegada = r.get("hora_llegada")
                hora_retiro = r.get("hora_retiro")
                motivo_retiro = r.get("motivo_retiro")

                # Si el estado no es tarde, limpiamos hora_llegada
                if est != "tarde":
                    hora_llegada = None
                # Si el estado no es retirado, limpiamos retiro
                if est != "retirado":
                    hora_retiro = None
                    motivo_retiro = None

                cursor.execute("""
                    INSERT INTO lista_diaria 
                        (alumno_numero, fecha, estado, hora_llegada, hora_retiro, motivo_retiro, registrado_por)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alumno_numero, fecha) DO UPDATE SET
                        estado = excluded.estado,
                        hora_llegada = excluded.hora_llegada,
                        hora_retiro = excluded.hora_retiro,
                        motivo_retiro = excluded.motivo_retiro,
                        registrado_por = excluded.registrado_por
                """, (num, fecha, est, hora_llegada, hora_retiro, motivo_retiro, usuario_id))

        return Resultado.exito("Lista diaria guardada correctamente")
    except Exception as e:
        return Resultado.error(f"Error al guardar lista diaria: {e}")


def _formatear_nombre_curso(anio: int, division: str, especialidad: str | None, turno: str) -> str:
    esp = f" - {especialidad}" if especialidad else ""
    return f"{anio}° {division}{esp} ({turno})"


def listar_historial_lista_diaria(
    curso_id: int | None = None,
    alumno_numero: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    ciclo_id: int | None = None,
    turno: str | None = None,
) -> list[dict]:
    """
    Devuelve los registros historicos de lista_diaria (parte de preceptoria)
    con datos del alumno, curso y usuario que registro.
    Permite filtrar por turno, curso, alumno y rango de fechas.
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
            if fecha_desde:
                condiciones.append("ld.fecha >= ?")
                parametros.append(fecha_desde)
            if fecha_hasta:
                condiciones.append("ld.fecha <= ?")
                parametros.append(fecha_hasta)
            if ciclo_id:
                condiciones.append("c.ciclo_id = ?")
                parametros.append(ciclo_id)

            where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

            query = f"""
                SELECT 
                    ld.id, ld.fecha, ld.estado, ld.hora_llegada, ld.hora_retiro, ld.motivo_retiro,
                    a.numero AS alumno_numero, a.nombre AS alumno_nombre, a.apellido AS alumno_apellido, a.dni,
                    c.id AS curso_id, c.anio, c.division, c.especialidad, c.turno,
                    u.nombre AS registrado_por_nombre, u.apellido AS registrado_por_apellido
                FROM lista_diaria ld
                JOIN alumno a ON ld.alumno_numero = a.numero
                JOIN curso c ON a.curso_id = c.id
                LEFT JOIN usuario u ON ld.registrado_por = u.id
                {where}
                ORDER BY ld.fecha DESC, c.anio ASC, c.division ASC, a.apellido ASC, a.nombre ASC
            """
            cursor.execute(query, parametros)
            filas = cursor.fetchall()
            resultado = []
            for f in filas:
                d = dict(f)
                d["curso_nombre"] = _formatear_nombre_curso(
                    d["anio"], d["division"], d.get("especialidad"), d["turno"]
                )
                d["alumno_completo"] = f"{d['alumno_apellido']}, {d['alumno_nombre']}"
                if d.get("registrado_por_nombre"):
                    d["registrado_por"] = f"{d['registrado_por_nombre']} {d.get('registrado_por_apellido', '')}".strip()
                else:
                    d["registrado_por"] = "N/A"
                resultado.append(d)
            return resultado
    except Exception as e:
        print(f"Error al listar historial de lista diaria: {e}")
        return []


def listar_resumen_global_diario(
    turno: str | None = None,
    curso_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    ciclo_id: int | None = None,
) -> list[dict]:
    """
    Devuelve un resumen global de partes diarios agrupado por fecha y curso.
    Si fecha_desde == fecha_hasta (consulta de un solo dia), incluye tambien
    los cursos sin parte cargado ese dia para facilitar la auditoria diaria.
    """
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            es_dia_unico = bool(fecha_desde and fecha_hasta and fecha_desde == fecha_hasta)

            if es_dia_unico:
                condiciones = []
                parametros: list = [fecha_desde]

                if ciclo_id:
                    condiciones.append("c.ciclo_id = ?")
                    parametros.append(ciclo_id)
                if turno:
                    condiciones.append("c.turno = ?")
                    parametros.append(turno)
                if curso_id:
                    condiciones.append("c.id = ?")
                    parametros.append(curso_id)

                where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

                query = f"""
                    SELECT
                        c.id AS curso_id,
                        c.anio,
                        c.division,
                        c.especialidad,
                        c.turno,
                        COUNT(DISTINCT CASE WHEN a.activo = 1 THEN a.numero END) AS matricula_activa,
                        COUNT(ld.id) AS total_registrados,
                        SUM(CASE WHEN ld.estado = 'presente' THEN 1 ELSE 0 END) AS presentes,
                        SUM(CASE WHEN ld.estado = 'ausente' THEN 1 ELSE 0 END) AS ausentes,
                        SUM(CASE WHEN ld.estado = 'tarde' THEN 1 ELSE 0 END) AS tardes,
                        SUM(CASE WHEN ld.estado = 'retirado' THEN 1 ELSE 0 END) AS retirados,
                        GROUP_CONCAT(
                            DISTINCT CASE
                                WHEN u.id IS NOT NULL THEN TRIM(u.nombre || ' ' || u.apellido)
                            END
                        ) AS registrados_por
                    FROM curso c
                    LEFT JOIN alumno a ON a.curso_id = c.id
                    LEFT JOIN lista_diaria ld ON ld.alumno_numero = a.numero AND ld.fecha = ?
                    LEFT JOIN usuario u ON ld.registrado_por = u.id
                    {where}
                    GROUP BY c.id
                    ORDER BY c.anio ASC, c.division ASC, c.turno ASC
                """
                cursor.execute(query, parametros)
                filas = cursor.fetchall()
                resultado = []
                for f in filas:
                    d = dict(f)
                    total = d["total_registrados"] or 0
                    presentes = d["presentes"] or 0
                    ausentes = d["ausentes"] or 0
                    tardes = d["tardes"] or 0
                    retirados = d["retirados"] or 0
                    registrado = total > 0
                    pct = round(((presentes + tardes) / total * 100.0), 1) if registrado else None
                    resultado.append({
                        "fecha": fecha_desde,
                        "curso_id": d["curso_id"],
                        "curso_nombre": _formatear_nombre_curso(
                            d["anio"], d["division"], d.get("especialidad"), d["turno"]
                        ),
                        "turno": d["turno"],
                        "estado_carga": "Registrado" if registrado else "Sin registrar",
                        "matricula_activa": d["matricula_activa"] or 0,
                        "total_registrados": total,
                        "presentes": presentes,
                        "ausentes": ausentes,
                        "tardes": tardes,
                        "retirados": retirados,
                        "porcentaje_presentismo": pct,
                        "registrado_por": (d.get("registrados_por") or "—").replace(",", ", "),
                    })
                return resultado

            # Rango multi-dia: agrupar todos los partes existentes por fecha y curso
            condiciones = []
            parametros = []

            if ciclo_id:
                condiciones.append("c.ciclo_id = ?")
                parametros.append(ciclo_id)
            if turno:
                condiciones.append("c.turno = ?")
                parametros.append(turno)
            if curso_id:
                condiciones.append("c.id = ?")
                parametros.append(curso_id)
            if fecha_desde:
                condiciones.append("ld.fecha >= ?")
                parametros.append(fecha_desde)
            if fecha_hasta:
                condiciones.append("ld.fecha <= ?")
                parametros.append(fecha_hasta)

            where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

            query = f"""
                SELECT
                    ld.fecha,
                    c.id AS curso_id,
                    c.anio,
                    c.division,
                    c.especialidad,
                    c.turno,
                    COUNT(ld.id) AS total_registrados,
                    SUM(CASE WHEN ld.estado = 'presente' THEN 1 ELSE 0 END) AS presentes,
                    SUM(CASE WHEN ld.estado = 'ausente' THEN 1 ELSE 0 END) AS ausentes,
                    SUM(CASE WHEN ld.estado = 'tarde' THEN 1 ELSE 0 END) AS tardes,
                    SUM(CASE WHEN ld.estado = 'retirado' THEN 1 ELSE 0 END) AS retirados,
                    GROUP_CONCAT(
                        DISTINCT CASE
                            WHEN u.id IS NOT NULL THEN TRIM(u.nombre || ' ' || u.apellido)
                        END
                    ) AS registrados_por
                FROM lista_diaria ld
                JOIN alumno a ON ld.alumno_numero = a.numero
                JOIN curso c ON a.curso_id = c.id
                LEFT JOIN usuario u ON ld.registrado_por = u.id
                {where}
                GROUP BY ld.fecha, c.id
                ORDER BY ld.fecha DESC, c.anio ASC, c.division ASC
            """
            cursor.execute(query, parametros)
            filas = cursor.fetchall()
            resultado = []
            for f in filas:
                d = dict(f)
                total = d["total_registrados"] or 0
                presentes = d["presentes"] or 0
                ausentes = d["ausentes"] or 0
                tardes = d["tardes"] or 0
                retirados = d["retirados"] or 0
                pct = round(((presentes + tardes) / total * 100.0), 1) if total > 0 else 0.0
                resultado.append({
                    "fecha": d["fecha"],
                    "curso_id": d["curso_id"],
                    "curso_nombre": _formatear_nombre_curso(
                        d["anio"], d["division"], d.get("especialidad"), d["turno"]
                    ),
                    "turno": d["turno"],
                    "estado_carga": "Registrado",
                    "matricula_activa": total,
                    "total_registrados": total,
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "tardes": tardes,
                    "retirados": retirados,
                    "porcentaje_presentismo": pct,
                    "registrado_por": (d.get("registrados_por") or "N/A").replace(",", ", "),
                })
            return resultado
    except Exception as e:
        print(f"Error al listar resumen global diario: {e}")
        return []

