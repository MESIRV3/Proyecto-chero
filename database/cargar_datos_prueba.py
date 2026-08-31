"""Carga datos de prueba en la base de datos."""
import sqlite3
from pathlib import Path
from datetime import date, timedelta


def cargar_datos():
    db_path = Path(__file__).parent / "asistencia.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ============================================
    # LIMPIAR DATOS PREVIOS (por si se corre varias veces)
    # ============================================

    tablas = [
        "justificacion", "asistencia", "lista_diaria",
        "horario", "materia", "alumno", "usuario",
        "curso", "ciclo_lectivo", "dia_habil"
    ]
    for tabla in tablas:
        cursor.execute(f"DELETE FROM {tabla}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}'")

    # ============================================
    # 1. CICLO LECTIVO
    # ============================================

    cursor.execute("""
        INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin)
        VALUES (?, ?, ?)
    """, (2026, "2026-03-01", "2026-12-15"))
    ciclo_id = cursor.lastrowid

    # ============================================
    # 2. CURSOS
    # ============================================

    cursos = [
        (1, "1", "manana"),
        (1, "2", "manana"),
        (5, "1", "manana"),
    ]
    cursos_ids = []
    for anio, division, turno in cursos:
        cursor.execute("""
            INSERT INTO curso (ciclo_id, anio, division, turno)
            VALUES (?, ?, ?, ?)
        """, (ciclo_id, anio, division, turno))
        cursos_ids.append(cursor.lastrowid)

    # ============================================
    # 3. USUARIOS
    # ============================================

    # En produccion las contraseñas van hasheadas con bcrypt.
    # Para datos de prueba usamos un placeholder.

    usuarios = [
        ("Maria",   "Gonzalez", "mgonzalez", "hash_pendiente", "preceptor"),
        ("Carlos",  "Perez",    "cperez",    "hash_pendiente", "profesor"),
        ("Laura",   "Diaz",     "ldiaz",     "hash_pendiente", "profesor"),
        ("Roberto", "Sosa",     "rsosa",     "hash_pendiente", "directivo"),
    ]

    usuarios_ids = []
    for nombre, apellido, username, password, rol in usuarios:
        cursor.execute("""
            INSERT INTO usuario (nombre, apellido, username, password, rol)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, apellido, username, password, rol))
        usuarios_ids.append(cursor.lastrowid)

    # ============================================
    # 4. MATERIAS (para todos los cursos)
    # ============================================

    materias = ["Ingles", "Matematicas", "Lengua", "Historia", "Educacion Fisica"]
    materia_ids_por_curso = {}

    for curso_id in cursos_ids:
        ids_materias = []
        for nombre in materias:
            cursor.execute("""
                INSERT INTO materia (nombre, curso_id)
                VALUES (?, ?)
            """, (nombre, curso_id))
            ids_materias.append(cursor.lastrowid)
        materia_ids_por_curso[curso_id] = ids_materias

    # Se sigue usando para armar el horario de ejemplo (5°A)
    materia_ids = materia_ids_por_curso[cursos_ids[2]]

    # ============================================
    # 5. HORARIO (la grilla semanal de 5°A, lunes)
    # ============================================
    # Recreos tienen materia_id NULL, usuario_id NULL, es_recreo=1
    # Clases tienen materia_id y usuario_id, es_recreo=0
    horario_5a_lunes = [
        # (numero_bloque, hora_inicio, hora_fin, es_recreo, materia_idx, usuario_idx)
        (1, "07:30", "08:10", 0, 0, 1),  # Ingles     - Carlos
        (2, "08:10", "08:50", 0, 1, 2),  # Matematicas - Laura
        (0, "08:50", "09:00", 1, None, None),  # Recreo
        (3, "09:00", "09:40", 0, 1, 2),  # Matematicas - Laura
        (4, "09:40", "10:20", 0, 2, 2),  # Lengua      - Laura
        (0, "10:20", "10:30", 1, None, None),  # Recreo
        (5, "10:30", "11:10", 0, 3, 2),  # Historia    - Laura
        (6, "11:10", "11:50", 0, 4, 2),  # Ed. Fisica  - Laura
        (0, "11:50", "12:00", 1, None, None),  # Recreo salida
        (7, "12:00", "12:40", 0, 1, 2),  # Matematicas - Laura
    ]
    for bloque, inicio, fin, recreo, mat_idx, usr_idx in horario_5a_lunes:
        mat_id = materia_ids[mat_idx] if mat_idx is not None else None
        usr_id = usuarios_ids[usr_idx] if usr_idx is not None else None
        cursor.execute("""
            INSERT INTO horario
                (curso_id, dia_semana, numero_bloque, hora_inicio, hora_fin,
                 es_recreo, materia_id, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cursos_ids[2], 1, bloque, inicio, fin, recreo, mat_id, usr_id))

    # ============================================
    # 6. ALUMNOS (10 de 5°A, 10 de 5°B, 10 de 1°A)
    # ============================================
    nombres = ["Juan", "Sofia", "Mateo", "Valentina", "Lucas",
               "Camila", "Tomas", "Isabella", "Diego", "Martina"]
    apellidos = ["Lopez", "Martinez", "Garcia", "Rodriguez", "Fernandez",
                 "Gomez", "Diaz", "Morales", "Romero", "Acosta"]

    alumno_numero = 10000000  # legajo base de 8 digitos
    for i in range(10):
        for curso_id in cursos_ids:
            cursor.execute("""
                INSERT INTO alumno (numero, nombre, apellido, dni, curso_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alumno_numero,
                nombres[i],
                apellidos[i],
                f"{(alumno_numero % 100000000):08d}",
                curso_id
            ))
            alumno_numero += 1

    # ============================================
    # 7. DIAS HABILES (marzo a junio 2026, lunes a viernes)
    # ============================================
    inicio = date(2026, 3, 1)
    fin = date(2026, 6, 30)
    actual = inicio
    while actual <= fin:
        # weekday(): lunes=0, ..., domingo=6
        if actual.weekday() < 5:
            cursor.execute("""
                INSERT INTO dia_habil (fecha, es_habil, motivo)
                VALUES (?, 1, NULL)
            """, (actual.strftime("%Y-%m-%d"),))
        actual += timedelta(days=1)

    conn.commit()
    conn.close()

    print("Datos de prueba cargados:")
    print("  - 1 ciclo lectivo (2026)")
    print("  - 3 cursos (1°A, 1°B, 5°A)")
    print("  - 4 usuarios (1 preceptor, 2 profes, 1 directivo)")
    print("  - 5 materias por cada curso")
    print("  - 10 bloques de horario (lunes de 5°A)")
    print("  - 30 alumnos (10 por curso)")
    print("  - Dias habiles de marzo a junio 2026")


if __name__ == "__main__":
    cargar_datos()