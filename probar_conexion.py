"""Prueba que el modulo de conexion funcione bien."""
from database.conexion import conexion


def probar_conexion():
    print("Probando modulo de conexion...\n")

    # 1. Probar que se puede abrir y leer
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM alumno")
        fila = cursor.fetchone()
        print(f"  [OK] Conexion abierta. Hay {fila['total']} alumnos.")

    # 2. Probar que se puede consultar con WHERE
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, apellido
            FROM alumno
            WHERE curso_id = 3
            ORDER BY apellido
            LIMIT 3
        """)
        print("  [OK] Primeros 3 alumnos de 5°A ordenados por apellido:")
        for fila in cursor.fetchall():
            print(f"       - {fila['apellido']}, {fila['nombre']}")

    # 3. Probar un JOIN
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.anio, c.division, COUNT(a.numero) as cant_alumnos
            FROM curso c
            LEFT JOIN alumno a ON a.curso_id = c.id
            GROUP BY c.id
            ORDER BY c.anio, c.division
        """)
        print("\n  [OK] Alumnos por curso:")
        for fila in cursor.fetchall():
            print(f"       - {fila['anio']}°{fila['division']}: {fila['cant_alumnos']} alumnos")

    print("\nTodo funciona. La capa de conexion esta lista.")


if __name__ == "__main__":
    probar_conexion()
