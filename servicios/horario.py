"""Servicio para gestion de materias y horarios (grilla semanal)."""
from datetime import date
from database.conexion import conexion
from database.resultado import Resultado

DIAS_SEMANA = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
}

BLOQUES_DEFAULT = {
    1: ("07:30", "08:10"),
    2: ("08:10", "08:50"),
    3: ("09:00", "09:40"),
    4: ("09:40", "10:20"),
    5: ("10:30", "11:10"),
    6: ("11:10", "11:50"),
    7: ("12:00", "12:40"),
    8: ("12:40", "13:20"),
}


def listar_materias_de_curso(curso_id: int) -> Resultado:
    """Devuelve las materias asociadas a un curso."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nombre, curso_id FROM materia WHERE curso_id = ? ORDER BY nombre ASC",
                (curso_id,),
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Materias obtenidas", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar materias: {e}")


def crear_materia_si_no_existe(curso_id: int, nombre: str) -> Resultado:
    """Crea una materia para un curso si no existe, o devuelve la existente."""
    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        return Resultado.error("El nombre de la materia no puede estar vacio")

    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nombre, curso_id FROM materia WHERE curso_id = ? AND LOWER(nombre) = LOWER(?)",
                (curso_id, nombre_limpio),
            )
            existente = cursor.fetchone()
            if existente:
                return Resultado.exito("Materia ya existente", datos=dict(existente))

            cursor.execute(
                "INSERT INTO materia (nombre, curso_id) VALUES (?, ?)",
                (nombre_limpio, curso_id),
            )
            nuevo_id = cursor.lastrowid
            return Resultado.exito("Materia creada", datos={"id": nuevo_id, "nombre": nombre_limpio, "curso_id": curso_id})
    except Exception as e:
        return Resultado.error(f"Error al crear materia: {e}")


def listar_horarios_de_curso(curso_id: int, usuario_id: int | None = None) -> Resultado:
    """Lista todos los bloques horarios de un curso, opcionalmente filtrados por profesor."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    h.id, h.curso_id, h.dia_semana, h.numero_bloque,
                    h.hora_inicio, h.hora_fin, h.es_recreo,
                    h.materia_id, m.nombre AS materia_nombre,
                    h.usuario_id, (u.nombre || ' ' || u.apellido) AS profesor_nombre
                FROM horario h
                LEFT JOIN materia m ON m.id = h.materia_id
                LEFT JOIN usuario u ON u.id = h.usuario_id
                WHERE h.curso_id = ?
            """
            params = [curso_id]
            if usuario_id is not None:
                query += " AND h.usuario_id = ?"
                params.append(usuario_id)

            query += " ORDER BY h.dia_semana ASC, h.numero_bloque ASC, h.hora_inicio ASC"
            cursor.execute(query, tuple(params))
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Horarios obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar horarios: {e}")


def agregar_horario(
    curso_id: int,
    dia_semana: int,
    *args,
    hora_inicio: str | None = None,
    hora_fin: str | None = None,
    materia_id: int | None = None,
    usuario_id: int | None = None,
    numero_bloque: int | None = None,
) -> Resultado:
    """Registra una clase en un horario determinado (hora inicio y hora fin).
    
    Soporta la firma simple:
        agregar_horario(curso_id, dia_semana, hora_inicio, hora_fin, materia_id, usuario_id)
    la firma con kwargs:
        agregar_horario(curso_id=..., dia_semana=..., hora_inicio=..., hora_fin=..., materia_id=..., usuario_id=...)
    y la firma tradicional con bloque explicito:
        agregar_horario(curso_id, dia_semana, numero_bloque, hora_inicio, hora_fin, materia_id, usuario_id)
    """
    if dia_semana not in DIAS_SEMANA:
        return Resultado.error("El dia de la semana debe ser entre Lunes (1) y Viernes (5)")

    bloque = numero_bloque
    if len(args) == 5:
        # (bloque, hora_inicio, hora_fin, materia_id, usuario_id)
        bloque, hora_inicio, hora_fin, materia_id, usuario_id = args
    elif len(args) == 4:
        # (hora_inicio, hora_fin, materia_id, usuario_id)
        hora_inicio, hora_fin, materia_id, usuario_id = args
    elif len(args) == 1:
        # (numero_bloque,) con el resto por kwargs
        bloque = args[0]

    hora_inicio = (hora_inicio or "").strip()
    hora_fin = (hora_fin or "").strip()

    if not hora_inicio or not hora_fin:
        return Resultado.error("Las horas de inicio y fin son obligatorias")

    if hora_inicio >= hora_fin:
        return Resultado.error("La hora de inicio debe ser anterior a la hora de fin")

    try:
        with conexion() as conn:
            cursor = conn.cursor()

            # 1. Verificar existencia de curso, materia y usuario
            cursor.execute("SELECT id FROM curso WHERE id = ?", (curso_id,))
            if not cursor.fetchone():
                return Resultado.error("El curso especificado no existe")

            cursor.execute("SELECT id, curso_id FROM materia WHERE id = ?", (materia_id,))
            mat = cursor.fetchone()
            if not mat:
                return Resultado.error("La materia especificada no existe")
            if mat["curso_id"] != curso_id:
                return Resultado.error("La materia no pertenece al curso seleccionado")

            cursor.execute("SELECT id, rol FROM usuario WHERE id = ?", (usuario_id,))
            usr = cursor.fetchone()
            if not usr:
                return Resultado.error("El docente especificado no existe")

            # 2. Verificar superposicion horaria en el mismo curso para el mismo dia
            cursor.execute("""
                SELECT h.id, m.nombre AS materia_nombre, h.hora_inicio, h.hora_fin
                FROM horario h
                LEFT JOIN materia m ON m.id = h.materia_id
                WHERE h.curso_id = ?
                  AND h.dia_semana = ?
                  AND (h.hora_inicio < ? AND h.hora_fin > ?)
            """, (curso_id, dia_semana, hora_fin, hora_inicio))
            conflicto_curso = cursor.fetchone()
            if conflicto_curso:
                return Resultado.error(
                    f"El curso ya tiene ocupado ese horario con la clase de '{conflicto_curso['materia_nombre']}' "
                    f"({conflicto_curso['hora_inicio']} a {conflicto_curso['hora_fin']})"
                )

            # 3. Verificar superposicion horaria del mismo profesor en otro curso
            cursor.execute("""
                SELECT h.id, c.anio, c.division, h.hora_inicio, h.hora_fin
                FROM horario h
                JOIN curso c ON c.id = h.curso_id
                WHERE h.usuario_id = ?
                  AND h.dia_semana = ?
                  AND (h.hora_inicio < ? AND h.hora_fin > ?)
            """, (usuario_id, dia_semana, hora_fin, hora_inicio))
            conflicto_docente = cursor.fetchone()
            if conflicto_docente:
                return Resultado.error(
                    f"El docente ya tiene asignada clase en {conflicto_docente['anio']}°{conflicto_docente['division']} "
                    f"en ese horario ({conflicto_docente['hora_inicio']} a {conflicto_docente['hora_fin']})"
                )

            # 4. Calcular numero_bloque si no fue provisto
            if bloque is None or bloque <= 0:
                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM horario
                    WHERE curso_id = ? AND dia_semana = ? AND hora_inicio <= ?
                """, (curso_id, dia_semana, hora_inicio))
                bloque = (cursor.fetchone()["total"] or 0) + 1

            # 5. Insertar horario
            cursor.execute("""
                INSERT INTO horario (
                    curso_id, dia_semana, numero_bloque,
                    hora_inicio, hora_fin, es_recreo,
                    materia_id, usuario_id
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (curso_id, dia_semana, bloque, hora_inicio, hora_fin, materia_id, usuario_id))
            nuevo_id = cursor.lastrowid

        return Resultado.exito("Horario registrado exitosamente", datos={"id": nuevo_id})
    except Exception as e:
        return Resultado.error(f"Error al registrar horario: {e}")


def eliminar_horario(horario_id: int) -> Resultado:
    """Elimina un bloque horario registrado."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM horario WHERE id = ?", (horario_id,))
            if cursor.rowcount == 0:
                return Resultado.error("No se encontro el horario a eliminar")
        return Resultado.exito("Horario eliminado correctamente")
    except Exception as e:
        return Resultado.error(f"Error al eliminar horario: {e}")


def obtener_cursos_del_dia_por_profesor(
    ciclo_id: int, usuario_id: int, dia_semana: int | None = None
) -> Resultado:
    """Devuelve los cursos que tiene a cargo un profesor en un dia determinado (hoy por defecto)."""
    if dia_semana is None:
        dia_semana = date.today().isoweekday()

    try:
        with conexion() as conn:
            cursor = conn.cursor()

            # Obtener cursos distintos donde el profesor da clases en ese dia
            cursor.execute("""
                SELECT 
                    c.id AS curso_id,
                    c.anio,
                    c.division,
                    c.especialidad,
                    c.turno,
                    (
                        SELECT COUNT(*) 
                        FROM alumno a 
                        WHERE a.curso_id = c.id AND a.activo = 1
                    ) AS cantidad_alumnos
                FROM curso c
                WHERE c.ciclo_id = ?
                  AND c.id IN (
                      SELECT DISTINCT h.curso_id 
                      FROM horario h 
                      WHERE h.usuario_id = ? AND h.dia_semana = ? AND h.es_recreo = 0
                  )
                ORDER BY c.anio ASC, c.division ASC
            """, (ciclo_id, usuario_id, dia_semana))
            cursos = [dict(c) for c in cursor.fetchall()]

            # Enriquecer cada curso con las materias y bloques del dia
            for curso in cursos:
                cursor.execute("""
                    SELECT 
                        h.id, h.numero_bloque, h.hora_inicio, h.hora_fin,
                        h.materia_id, m.nombre AS materia_nombre
                    FROM horario h
                    LEFT JOIN materia m ON m.id = h.materia_id
                    WHERE h.curso_id = ?
                      AND h.usuario_id = ?
                      AND h.dia_semana = ?
                      AND h.es_recreo = 0
                    ORDER BY h.hora_inicio ASC
                """, (curso["curso_id"], usuario_id, dia_semana))
                horarios = [dict(h) for h in cursor.fetchall()]

                # Materias unicas
                materias_unicas = []
                materias_ids = []
                for h in horarios:
                    m = h.get("materia_nombre")
                    mid = h.get("materia_id")
                    if m and m not in materias_unicas:
                        materias_unicas.append(m)
                        if mid:
                            materias_ids.append({"id": mid, "nombre": m})

                # Resumen de horas y franja horaria
                if horarios:
                    min_hora = horarios[0]["hora_inicio"]
                    max_hora = horarios[-1]["hora_fin"]
                    horas_str = ", ".join(f"{h['numero_bloque']}°" for h in horarios)
                    plural = "horas" if len(horarios) > 1 else "hora"
                    horarios_resumen = f"{min_hora} - {max_hora} ({horas_str} {plural})"
                else:
                    horarios_resumen = "—"

                curso["materias"] = materias_unicas
                curso["materias_detalle"] = materias_ids
                curso["primer_materia_id"] = materias_ids[0]["id"] if materias_ids else None
                curso["materias_texto"] = ", ".join(materias_unicas) if materias_unicas else "—"
                curso["horarios_texto"] = horarios_resumen
                curso["bloques"] = horarios

        return Resultado.exito(
            "Cursos del dia obtenidos",
            datos={
                "dia_semana": dia_semana,
                "dia_nombre": DIAS_SEMANA.get(dia_semana, "Día"),
                "cursos": cursos,
            },
        )
    except Exception as e:
        return Resultado.error(f"Error al obtener cursos del dia: {e}")


def listar_materias_de_profesor_en_curso(curso_id: int, usuario_id: int | None = None) -> Resultado:
    """Devuelve las materias que dicta un profesor especifico en un curso dado.
    Si usuario_id es None o no tiene materias con horario, devuelve todas las materias del curso.
    """
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            if usuario_id is not None:
                cursor.execute("""
                    SELECT DISTINCT m.id, m.nombre, m.curso_id
                    FROM materia m
                    JOIN horario h ON h.materia_id = m.id
                    WHERE m.curso_id = ? AND h.usuario_id = ?
                    ORDER BY m.nombre ASC
                """, (curso_id, usuario_id))
                filas = [dict(f) for f in cursor.fetchall()]
                if filas:
                    return Resultado.exito("Materias del profesor obtenidas", datos=filas)

            # Si no hay materias asignadas en horarios o es admin, listar todas las materias del curso
            cursor.execute(
                "SELECT id, nombre, curso_id FROM materia WHERE curso_id = ? ORDER BY nombre ASC",
                (curso_id,)
            )
            todas = [dict(f) for f in cursor.fetchall()]
            return Resultado.exito("Materias del curso obtenidas", datos=todas)
    except Exception as e:
        return Resultado.error(f"Error al obtener materias del profesor: {e}")


def listar_horarios_de_profesor(usuario_id: int, ciclo_id: int | None = None) -> Resultado:
    """Devuelve todos los horarios asignados a un profesor en todos sus cursos."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            condicion_ciclo = "AND c.ciclo_id = ?" if ciclo_id is not None else ""
            params = (usuario_id, ciclo_id) if ciclo_id is not None else (usuario_id,)
            cursor.execute(
                f"""
                SELECT
                    h.id, h.curso_id, h.dia_semana, h.numero_bloque,
                    h.hora_inicio, h.hora_fin, h.materia_id, h.usuario_id,
                    m.nombre AS materia_nombre,
                    c.anio, c.division, c.especialidad, c.turno
                FROM horario h
                JOIN curso c ON c.id = h.curso_id
                LEFT JOIN materia m ON m.id = h.materia_id
                WHERE h.usuario_id = ?
                  AND h.es_recreo = 0
                  {condicion_ciclo}
                ORDER BY h.dia_semana ASC, h.hora_inicio ASC
                """,
                params,
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Horarios del profesor obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar horarios del profesor: {e}")


def listar_profesores_con_conteo(ciclo_id: int | None = None) -> Resultado:
    """Lista todos los profesores activos junto con la cantidad de horarios semanales asignados."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            if ciclo_id is not None:
                cursor.execute(
                    """
                    SELECT u.id, u.nombre, u.apellido, u.username,
                           COUNT(c.id) AS cantidad_horarios
                    FROM usuario u
                    LEFT JOIN horario h ON h.usuario_id = u.id AND h.es_recreo = 0
                    LEFT JOIN curso c ON c.id = h.curso_id AND c.ciclo_id = ?
                    WHERE u.rol = 'profesor' AND u.activo = 1
                    GROUP BY u.id, u.nombre, u.apellido, u.username
                    ORDER BY u.apellido ASC, u.nombre ASC
                    """,
                    (ciclo_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT u.id, u.nombre, u.apellido, u.username,
                           COUNT(h.id) AS cantidad_horarios
                    FROM usuario u
                    LEFT JOIN horario h ON h.usuario_id = u.id AND h.es_recreo = 0
                    WHERE u.rol = 'profesor' AND u.activo = 1
                    GROUP BY u.id, u.nombre, u.apellido, u.username
                    ORDER BY u.apellido ASC, u.nombre ASC
                    """
                )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Profesores obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar profesores: {e}")

