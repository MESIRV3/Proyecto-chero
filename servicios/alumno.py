"""
Servicios de alumnos: busqueda/consultas (para tomar lista) + gestion
(alta, baja, reactivar, cambiar de curso) para el panel de administrador.
"""
from database.conexion import conexion
from database.resultado import Resultado


# =====================================================================
# CONSULTAS (usadas por la pantalla de tomar lista / asistencia)
# =====================================================================

def listar_alumnos_de_curso(curso_id: int) -> list[dict]:
    """Devuelve la lista de alumnos activos de un curso, ordenados por apellido."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero, nombre, apellido, dni, nacionalidad
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
            SELECT numero, nombre, apellido, dni, nacionalidad, curso_id, activo
            FROM alumno
            WHERE numero = ?
        """, (numero,))
        fila = cursor.fetchone()
        return dict(fila) if fila else None


def listar_cursos() -> list[dict]:
    """
    Devuelve todos los cursos (con su anio de ciclo lectivo y especialidad).

    NOTA: a pesar del nombre, esta consulta no filtra por el ciclo lectivo
    actual (no tiene WHERE sobre cl.anio) - trae todos los ciclos cargados.
    Si en algun lado de la app esto te esta trayendo cursos de anios
    anteriores mezclados, es por eso. Lo deje igual que lo tenias para no
    romper nada; si algun dia queres que filtre solo el ciclo activo,
    usa servicios/curso.py -> listar_cursos(ciclo_id) en su lugar, que si
    filtra y ademas trae la cantidad de alumnos por curso.
    """
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.anio, c.division, c.especialidad, c.turno, cl.anio as ciclo
            FROM curso c
            JOIN ciclo_lectivo cl ON c.ciclo_id = cl.id
            ORDER BY c.anio, c.division
        """)
        return [dict(fila) for fila in cursor.fetchall()]


# =====================================================================
# GESTION (usadas por el panel de administrador)
# =====================================================================

def agregar_alumno(numero: int, nombre: str, apellido: str, curso_id: int, dni: str = None, nacionalidad: str = None):
    """Da de alta un alumno nuevo. El numero de legajo es la clave primaria (lo define el usuario)."""
    if not numero:
        return Resultado.error("El numero de legajo es obligatorio")
    if not nombre or not nombre.strip():
        return Resultado.error("El nombre es obligatorio")
    if not apellido or not apellido.strip():
        return Resultado.error("El apellido es obligatorio")
    if not curso_id:
        return Resultado.error("Hay que asignar un curso")

    dni = dni.strip() if dni else None
    nacionalidad = nacionalidad.strip() if nacionalidad else None

    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM curso WHERE id = ?", (curso_id,))
            if cursor.fetchone() is None:
                return Resultado.error("El curso seleccionado no existe")

            cursor.execute(
                """
                INSERT INTO alumno (numero, nombre, apellido, dni, nacionalidad, curso_id, activo)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (numero, nombre.strip(), apellido.strip(), dni, nacionalidad, curso_id),
            )
        return Resultado.exito("Alumno agregado correctamente", datos=numero)
    except Exception as e:
        mensaje = str(e)
        if "UNIQUE" in mensaje and "dni" in mensaje.lower():
            return Resultado.error(f"Ya existe un alumno con el DNI {dni}")
        if "UNIQUE" in mensaje or "PRIMARY KEY" in mensaje:
            return Resultado.error(f"Ya existe un alumno con el numero {numero}")
        return Resultado.error(f"Error al agregar el alumno: {e}")


def listar_alumnos(curso_id: int = None, solo_activos: bool = True):
    """Devuelve la lista de alumnos, opcionalmente filtrada por curso y/o solo los activos."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            condiciones = []
            parametros = []
            if curso_id:
                condiciones.append("curso_id = ?")
                parametros.append(curso_id)
            if solo_activos:
                condiciones.append("activo = 1")
            where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
            cursor.execute(
                f"SELECT * FROM alumno {where} ORDER BY apellido, nombre",
                parametros,
            )
            filas = [dict(f) for f in cursor.fetchall()]
        return Resultado.exito(datos=filas)
    except Exception as e:
        return Resultado.error(f"Error al listar alumnos: {e}")


def dar_de_baja_alumno(numero: int):
    """Baja logica: marca al alumno como inactivo sin borrar su historial."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alumno SET activo = 0 WHERE numero = ?", (numero,))
            if cursor.rowcount == 0:
                return Resultado.error("El alumno no existe")
        return Resultado.exito("Alumno dado de baja correctamente")
    except Exception as e:
        return Resultado.error(f"Error al dar de baja al alumno: {e}")


def reactivar_alumno(numero: int):
    """Vuelve a marcar a un alumno como activo."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alumno SET activo = 1 WHERE numero = ?", (numero,))
            if cursor.rowcount == 0:
                return Resultado.error("El alumno no existe")
        return Resultado.exito("Alumno reactivado correctamente")
    except Exception as e:
        return Resultado.error(f"Error al reactivar al alumno: {e}")


def eliminar_alumno_definitivo(numero: int):
    """Borra al alumno de forma permanente. Falla si tiene registros de asistencia (usar baja logica en ese caso)."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM asistencia WHERE alumno_numero = ?", (numero,))
            total_asistencias = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM lista_diaria WHERE alumno_numero = ?", (numero,))
            total_listas = cursor.fetchone()["total"]
            if total_asistencias > 0 or total_listas > 0:
                return Resultado.error(
                    "No se puede eliminar: el alumno tiene registros de asistencia. Usa 'dar de baja' en su lugar."
                )
            cursor.execute("DELETE FROM alumno WHERE numero = ?", (numero,))
            if cursor.rowcount == 0:
                return Resultado.error("El alumno no existe")
        return Resultado.exito("Alumno eliminado definitivamente")
    except Exception as e:
        return Resultado.error(f"Error al eliminar el alumno: {e}")


def cambiar_curso_alumno(numero: int, nuevo_curso_id: int):
    """Cambia a un alumno de curso (por ejemplo si repite, o si cambia de division)."""
    try:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM curso WHERE id = ?", (nuevo_curso_id,))
            if cursor.fetchone() is None:
                return Resultado.error("El curso seleccionado no existe")
            cursor.execute("UPDATE alumno SET curso_id = ? WHERE numero = ?", (nuevo_curso_id, numero))
            if cursor.rowcount == 0:
                return Resultado.error("El alumno no existe")
        return Resultado.exito("Alumno movido de curso correctamente")
    except Exception as e:
        return Resultado.error(f"Error al cambiar de curso al alumno: {e}")
