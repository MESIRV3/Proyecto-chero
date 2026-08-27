"""Muestra los datos cargados para verificar."""
import sqlite3
from pathlib import Path


def mostrar_resumen():
    db_path = Path(__file__).parent / "asistencia.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tablas = [
        "ciclo_lectivo", "curso", "usuario", "materia",
        "horario", "alumno", "dia_habil", "asistencia",
        "lista_diaria", "justificacion"
    ]

    print("=" * 50)
    print("RESUMEN DE DATOS EN LA BASE")
    print("=" * 50)

    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        cantidad = cursor.fetchone()[0]
        print(f"  {tabla:20s} -> {cantidad:3d} registros")

    print("\n" + "=" * 50)
    print("EJEMPLO: CURSOS CARGADOS")
    print("=" * 50)
    cursor.execute("""
        SELECT c.id, c.anio, c.division, c.turno, cl.anio as ciclo
        FROM curso c
        JOIN ciclo_lectivo cl ON c.ciclo_id = cl.id
        ORDER BY c.anio, c.division
    """)
    for fila in cursor.fetchall():
        print(f"  {fila[1]}°{fila[2]} - turno {fila[3]} (ciclo {fila[4]})")

    print("\n" + "=" * 50)
    print("EJEMPLO: HORARIO DEL LUNES EN 5°A")
    print("=" * 50)
    cursor.execute("""
        SELECT h.numero_bloque, h.hora_inicio, h.hora_fin,
               h.es_recreo, COALESCE(m.nombre, 'RECREO') as materia
        FROM horario h
        LEFT JOIN materia m ON h.materia_id = m.id
        WHERE h.curso_id = 3 AND h.dia_semana = 1
        ORDER BY h.hora_inicio
    """)
    for fila in cursor.fetchall():
        tipo = "RECREO  " if fila[3] else f"{fila[4]:12s}"
        print(f"  {fila[1]} - {fila[2]}  | bloque {fila[0]} | {tipo}")

    print("\n" + "=" * 50)
    print("EJEMPLO: ALUMNOS DE 5°A")
    print("=" * 50)
    cursor.execute("""
        SELECT numero, apellido, nombre
        FROM alumno
        WHERE curso_id = 3
        ORDER BY apellido, nombre
    """)
    for fila in cursor.fetchall():
        print(f"  Legajo {fila[0]} | {fila[1]}, {fila[2]}")

    conn.close()


if __name__ == "__main__":
    mostrar_resumen()
