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
