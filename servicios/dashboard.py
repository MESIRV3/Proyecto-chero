"""Metricas para el HUB del panel de administracion."""
from datetime import date
from database.conexion import conexion
from database.resultado import Resultado


def obtener_metricas_hub(ciclo_id):
    hoy = date.today().isoformat()
    hace_7_dias = date.fromordinal(date.today().toordinal() - 7).isoformat()
    try:
        with conexion() as conn:
            c = conn.cursor()
            c.execute('SELECT anio FROM ciclo_lectivo WHERE id = ?', (ciclo_id,))
            f = c.fetchone()
            ciclo_anio = f['anio'] if f else date.today().year
            c.execute('SELECT COUNT(*) AS t FROM alumno a JOIN curso cu ON a.curso_id=cu.id WHERE cu.ciclo_id=? AND a.activo=1', (ciclo_id,))
            alumnos_activos = c.fetchone()['t'] or 0
            c.execute('SELECT COUNT(*) AS t FROM alumno a JOIN curso cu ON a.curso_id=cu.id WHERE cu.ciclo_id=? AND a.activo=0', (ciclo_id,))
            alumnos_baja = c.fetchone()['t'] or 0
            c.execute('SELECT COUNT(*) AS t FROM curso WHERE ciclo_id=?', (ciclo_id,))
            total_cursos = c.fetchone()['t'] or 0
            c.execute(
                'SELECT COUNT(*) AS t FROM asistencia a '
                'JOIN materia m ON m.id = a.materia_id '
                'JOIN curso cu ON cu.id = m.curso_id '
                'WHERE cu.ciclo_id = ? AND a.fecha = ?',
                (ciclo_id, hoy),
            )
            asistencias_hoy = c.fetchone()['t'] or 0
            c.execute(
                'SELECT COUNT(*) AS t FROM asistencia a '
                'JOIN materia m ON m.id = a.materia_id '
                'JOIN curso cu ON cu.id = m.curso_id '
                'WHERE cu.ciclo_id = ? AND a.fecha >= ?',
                (ciclo_id, hace_7_dias),
            )
            asistencias_semana = c.fetchone()['t'] or 0
        return Resultado.exito('Metricas obtenidas', datos={
            'alumnos_activos': alumnos_activos,
            'alumnos_baja': alumnos_baja,
            'total_cursos': total_cursos,
            'asistencias_hoy': asistencias_hoy,
            'asistencias_semana': asistencias_semana,
            'ciclo_anio': ciclo_anio,
        })
    except Exception as e:
        return Resultado.error(f'Error al obtener metricas: {e}')
