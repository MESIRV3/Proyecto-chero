"""Test de los servicios de alumno y asistencia."""
from servicios.alumno import listar_alumnos_de_curso, listar_cursos, obtener_alumno
from servicios.asistencia import (
    registrar_asistencia,
    calcular_porcentaje_asistencia,
    listar_asistencias_de_alumno
)


def probar_servicios():
    print("=" * 50)
    print("PROBANDO SERVICIOS")
    print("=" * 50)

    # 1. Listar cursos
    print("\n1. Cursos disponibles:")
    for curso in listar_cursos():
        print(f"   {curso['anio']}°{curso['division']} - {curso['turno']}")

    # 2. Listar alumnos de 5°A
    print("\n2. Alumnos de 5°A:")
    alumnos = listar_alumnos_de_curso(3)  # 5°A es el id 3
    for a in alumnos[:3]:
        print(f"   Legajo {a['numero']}: {a['apellido']}, {a['nombre']}")
    print(f"   ... y {len(alumnos) - 3} mas")

    # 3. Obtener un alumno especifico
    juan = obtener_alumno(10000002)  # Juan Lopez
    print(f"\n3. Buscar alumno legajo 10000002:")
    print(f"   {juan['apellido']}, {juan['nombre']} - curso {juan['curso_id']}")

    # 4. Registrar asistencia de Juan en 3 fechas distintas
    print("\n4. Registrando asistencia de Juan (legajo 10000002) en Matematicas:")
    registros = [
        ("2026-03-09", "presente", None),
        ("2026-03-10", "presente", None),
        ("2026-03-11", "ausente", "Enfermo"),
        ("2026-03-12", "presente", None),
        ("2026-03-13", "presente", None),
    ]
    for fecha, estado, obs in registros:
        resultado = registrar_asistencia(
            alumno_numero=10000002,
            materia_id=2,  # Matematicas
            fecha=fecha,
            estado=estado,
            profesor_id=2,  # Carlos Perez
            observaciones=obs
        )
        print(f"   {fecha} - {estado:10s} -> {'OK' if resultado.ok else 'ERROR: ' + resultado.mensaje}")

    # 5. Calcular el porcentaje
    porcentaje = calcular_porcentaje_asistencia(
        alumno_numero=10000002,
        materia_id=2,
        fecha_desde="2026-03-01",
        fecha_hasta="2026-03-31"
    )
    print(f"\n5. Porcentaje de Juan en Matematicas (marzo): {porcentaje}%")

    # 6. Probar validacion: estado invalido
    print("\n6. Probando validacion de estado invalido:")
    resultado = registrar_asistencia(
        alumno_numero=10000002,
        materia_id=2,
        fecha="2026-03-09",
        estado="medio_presente",
        profesor_id=2
    )
    print(f"   {resultado}")

    # 7. Listar todas las asistencias de Juan
    print("\n7. Todas las asistencias de Juan (marzo):")
    for a in listar_asistencias_de_alumno(10000002, "2026-03-01", "2026-03-31"):
        obs = f" ({a['observaciones']})" if a['observaciones'] else ""
        print(f"   {a['fecha']} | {a['materia']:12s} | {a['estado']}{obs}")


    print("\nServicios funcionando correctamente.")


if __name__ == "__main__":
    probar_servicios()
