"""Servicio para gestion de asignaciones entre preceptores y cursos."""
from database.conexion import conexion
from database.resultado import Resultado


SQL_CREAR_TABLA_PRECEPTOR_CURSO = """
CREATE TABLE IF NOT EXISTS preceptor_curso (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    curso_id    INTEGER NOT NULL,
    UNIQUE(usuario_id, curso_id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (curso_id)   REFERENCES curso(id)
);
"""


def asegurar_tabla_preceptor_curso(conn=None) -> None:
    """Crea la tabla preceptor_curso de forma idempotente si todavia no existe."""
    if conn is not None:
        conn.execute(SQL_CREAR_TABLA_PRECEPTOR_CURSO)
        return
    with conexion() as nueva_conn:
        nueva_conn.execute(SQL_CREAR_TABLA_PRECEPTOR_CURSO)


def asignar_curso_a_preceptor(usuario_id: int, curso_id: int) -> Resultado:
    """Asigna un curso a un preceptor activo."""
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, rol, activo FROM usuario WHERE id = ?",
                (usuario_id,),
            )
            usr = cursor.fetchone()
            if not usr:
                return Resultado.error("El preceptor especificado no existe")
            if usr["rol"] != "preceptor":
                return Resultado.error("El usuario seleccionado no tiene rol de preceptor")
            if not usr["activo"]:
                return Resultado.error("El preceptor seleccionado no esta activo")

            cursor.execute("SELECT id FROM curso WHERE id = ?", (curso_id,))
            if not cursor.fetchone():
                return Resultado.error("El curso especificado no existe")

            cursor.execute(
                "SELECT id FROM preceptor_curso WHERE usuario_id = ? AND curso_id = ?",
                (usuario_id, curso_id),
            )
            if cursor.fetchone():
                return Resultado.error("El preceptor ya tiene asignado ese curso")

            cursor.execute(
                "INSERT INTO preceptor_curso (usuario_id, curso_id) VALUES (?, ?)",
                (usuario_id, curso_id),
            )
            nuevo_id = cursor.lastrowid
        return Resultado.exito("Curso asignado al preceptor correctamente", datos={"id": nuevo_id})
    except Exception as e:
        return Resultado.error(f"Error al asignar curso al preceptor: {e}")


def desasignar_curso_de_preceptor(usuario_id: int, curso_id: int) -> Resultado:
    """Quita la asignacion de un curso a un preceptor."""
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM preceptor_curso WHERE usuario_id = ? AND curso_id = ?",
                (usuario_id, curso_id),
            )
            if cursor.rowcount == 0:
                return Resultado.error("No se encontro la asignacion a eliminar")
        return Resultado.exito("Curso desasignado correctamente")
    except Exception as e:
        return Resultado.error(f"Error al desasignar curso del preceptor: {e}")


def guardar_cursos_de_preceptor(
    usuario_id: int,
    curso_ids: list[int],
    ciclo_id: int | None = None,
) -> Resultado:
    """Reemplaza atomica e idempotentemente los cursos asignados a un preceptor (en un ciclo dado o globalmente)."""
    ids_unicos = list(dict.fromkeys(int(cid) for cid in curso_ids))
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, rol, activo FROM usuario WHERE id = ?",
                (usuario_id,),
            )
            usr = cursor.fetchone()
            if not usr:
                return Resultado.error("El preceptor especificado no existe")
            if usr["rol"] != "preceptor":
                return Resultado.error("El usuario seleccionado no tiene rol de preceptor")
            if not usr["activo"]:
                return Resultado.error("El preceptor seleccionado no esta activo")

            if ids_unicos:
                placeholders = ",".join("?" for _ in ids_unicos)
                cursor.execute(
                    f"SELECT id, ciclo_id FROM curso WHERE id IN ({placeholders})",
                    tuple(ids_unicos),
                )
                encontrados = {r["id"]: r["ciclo_id"] for r in cursor.fetchall()}
                if len(encontrados) != len(ids_unicos):
                    return Resultado.error("Uno o mas cursos seleccionados no existen")
                if ciclo_id is not None:
                    for cid, c_ciclo in encontrados.items():
                        if c_ciclo != ciclo_id:
                            return Resultado.error("Uno o mas cursos no pertenecen al ciclo lectivo indicado")

            if ciclo_id is not None:
                cursor.execute(
                    """
                    DELETE FROM preceptor_curso
                    WHERE usuario_id = ?
                      AND curso_id IN (SELECT id FROM curso WHERE ciclo_id = ?)
                    """,
                    (usuario_id, ciclo_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM preceptor_curso WHERE usuario_id = ?",
                    (usuario_id,),
                )

            for cid in ids_unicos:
                cursor.execute(
                    "INSERT INTO preceptor_curso (usuario_id, curso_id) VALUES (?, ?)",
                    (usuario_id, cid),
                )

        return Resultado.exito(
            "Asignaciones guardadas correctamente",
            datos={"usuario_id": usuario_id, "curso_ids": ids_unicos},
        )
    except Exception as e:
        return Resultado.error(f"Error al guardar asignaciones de cursos: {e}")


def listar_cursos_de_preceptor(usuario_id: int, ciclo_id: int | None = None) -> Resultado:
    """Devuelve los cursos asignados a un preceptor (con cantidad de alumnos activos)."""
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()
            condicion_ciclo = "AND c.ciclo_id = ?" if ciclo_id is not None else ""
            params = (usuario_id, ciclo_id) if ciclo_id is not None else (usuario_id,)
            cursor.execute(
                f"""
                SELECT c.*,
                       (SELECT COUNT(*) FROM alumno a
                        WHERE a.curso_id = c.id AND a.activo = 1) AS cantidad_alumnos
                FROM curso c
                JOIN preceptor_curso pc ON pc.curso_id = c.id
                WHERE pc.usuario_id = ?
                  {condicion_ciclo}
                ORDER BY c.anio ASC, c.division ASC
                """,
                params,
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Cursos del preceptor obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar cursos del preceptor: {e}")


def listar_preceptores_de_curso(curso_id: int) -> Resultado:
    """Devuelve los preceptores activos asignados a un curso."""
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nombre, u.apellido, u.username
                FROM usuario u
                JOIN preceptor_curso pc ON pc.usuario_id = u.id
                WHERE pc.curso_id = ? AND u.rol = 'preceptor' AND u.activo = 1
                ORDER BY u.apellido ASC, u.nombre ASC
                """,
                (curso_id,),
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Preceptores del curso obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar preceptores del curso: {e}")


def listar_preceptores_con_conteo(ciclo_id: int | None = None) -> Resultado:
    """Lista todos los preceptores activos junto con la cantidad de cursos asignados."""
    try:
        with conexion() as conn:
            asegurar_tabla_preceptor_curso(conn)
            cursor = conn.cursor()
            if ciclo_id is not None:
                cursor.execute(
                    """
                    SELECT u.id, u.nombre, u.apellido, u.username,
                           COUNT(c.id) AS cantidad_cursos
                    FROM usuario u
                    LEFT JOIN preceptor_curso pc ON pc.usuario_id = u.id
                    LEFT JOIN curso c ON c.id = pc.curso_id AND c.ciclo_id = ?
                    WHERE u.rol = 'preceptor' AND u.activo = 1
                    GROUP BY u.id, u.nombre, u.apellido, u.username
                    ORDER BY u.apellido ASC, u.nombre ASC
                    """,
                    (ciclo_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT u.id, u.nombre, u.apellido, u.username,
                           COUNT(pc.curso_id) AS cantidad_cursos
                    FROM usuario u
                    LEFT JOIN preceptor_curso pc ON pc.usuario_id = u.id
                    WHERE u.rol = 'preceptor' AND u.activo = 1
                    GROUP BY u.id, u.nombre, u.apellido, u.username
                    ORDER BY u.apellido ASC, u.nombre ASC
                    """
                )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito("Preceptores obtenidos", datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar preceptores: {e}")
