"""Servicios relacionados a cursos (anio + division + especialidad + turno)."""
from database.conexion import conexion
from database.resultado import Resultado


# 1ro y 2do van sin especialidad. De 3ro a 6to se especializan.
ANIOS_SIN_ESPECIALIDAD = (1, 2)
ANIOS_CON_ESPECIALIDAD = (3, 4, 5, 6)
ESPECIALIDADES_VALIDAS = ("Computacion", "GAO")
TURNOS_VALIDOS = ("Mañana", "Tarde")

NOMBRES_ESPECIALIDAD = {
    "Computacion": "Computacion",
    "GAO": "Gestion y Administracion de las Organizaciones",
}


def _validar_especialidad(anio: int, especialidad):
    """Devuelve un mensaje de error si la especialidad no es valida para ese anio, o None si esta OK."""
    if anio in ANIOS_SIN_ESPECIALIDAD:
        if especialidad not in (None, ""):
            return "1er y 2do anio no tienen especialidad"
    elif anio in ANIOS_CON_ESPECIALIDAD:
        if especialidad not in ESPECIALIDADES_VALIDAS:
            return "A partir de 3er anio hay que elegir una especialidad (Computacion o GAO)"
    else:
        return "El anio tiene que estar entre 1 y 6"
    return None


def agregar_curso(ciclo_id: int, anio: int, division: str, turno: str, especialidad: str = None):
    """Crea un curso nuevo. Devuelve Resultado con el id del curso creado en .datos"""
    especialidad = especialidad or None

    error = _validar_especialidad(anio, especialidad)
    if error:
        return Resultado.error(error)

    if not division or not division.strip():
        return Resultado.error("La division no puede estar vacia")

    if turno not in TURNOS_VALIDOS:
        return Resultado.error("El turno debe ser Manana o Tarde")

    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO curso (ciclo_id, anio, division, especialidad, turno)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ciclo_id, anio, division.strip(), especialidad, turno),
            )
            nuevo_id = cursor.lastrowid
        return Resultado.exito("Curso creado correctamente", datos=nuevo_id)
    except Exception as e:
        if "UNIQUE" in str(e):
            return Resultado.error("Ya existe un curso con ese anio, division, especialidad y turno")
        return Resultado.error(f"Error al crear el curso: {e}")


def listar_cursos(ciclo_id: int = None):
    """Devuelve la lista de cursos (con cantidad de alumnos activos), opcionalmente filtrada por ciclo."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            condicion = "WHERE curso.ciclo_id = ?" if ciclo_id else ""
            parametros = (ciclo_id,) if ciclo_id else ()
            cursor.execute(
                f"""
                SELECT curso.*,
                       (SELECT COUNT(*) FROM alumno
                        WHERE alumno.curso_id = curso.id AND alumno.activo = 1) AS cantidad_alumnos
                FROM curso
                {condicion}
                ORDER BY curso.anio, curso.division
                """,
                parametros,
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito(datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar cursos: {e}")


def eliminar_curso(curso_id: int):
    """Elimina un curso. No se puede si todavia tiene alumnos asignados (activos o no)."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM alumno WHERE curso_id = ?", (curso_id,))
            total_alumnos = cursor.fetchone()["total"]
            if total_alumnos > 0:
                return Resultado.error(
                    f"No se puede eliminar: el curso tiene {total_alumnos} alumno(s) asignado(s). "
                    "Primero hay que reasignarlos o darlos de baja."
                )
            cursor.execute("DELETE FROM curso WHERE id = ?", (curso_id,))
            if cursor.rowcount == 0:
                return Resultado.error("El curso no existe")
        return Resultado.exito("Curso eliminado correctamente")
    except Exception as e:
        return Resultado.error(f"Error al eliminar el curso: {e}")


def obtener_nombre_curso(curso: dict) -> str:
    """Arma un nombre legible para mostrar en la interfaz. Ej: '4to A - Computacion (Manana)'"""
    ordinales = {1: "1ro", 2: "2do", 3: "3ro", 4: "4to", 5: "5to", 6: "6to"}
    nombre = f"{ordinales.get(curso['anio'], curso['anio'])} {curso['division']}"
    if curso.get("especialidad"):
        nombre += f" - {curso['especialidad']}"
    nombre += f" ({curso['turno']})"
    return nombre
