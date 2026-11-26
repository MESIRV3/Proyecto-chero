"""Servicio de exportación de asistencias y partes diarios a formatos estructurados (CSV/Excel)."""
import csv
from pathlib import Path
from database.resultado import Resultado


def exportar_partes_diarios_a_csv(registros: list[dict], ruta_archivo: str) -> Resultado:
    """
    Exporta una lista de partes diarios a un archivo CSV codificado con UTF-8 con BOM
    para compatibilidad inmediata con Microsoft Excel y LibreOffice.
    """
    if not registros:
        return Resultado.error("No hay registros para exportar")

    try:
        path = Path(ruta_archivo)
        path.parent.mkdir(parents=True, exist_ok=True)

        campos = [
            "Fecha",
            "Curso",
            "Alumno",
            "DNI",
            "Estado",
            "Horario",
            "Motivo Retiro",
            "Registrado por",
        ]

        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(campos)

            for reg in registros:
                estado = (reg.get("estado") or "-").capitalize()
                horario = "-"
                if estado.lower() == "tarde" and reg.get("hora_llegada"):
                    horario = f"Llegada: {reg['hora_llegada']}"
                elif estado.lower() == "retirado" and reg.get("hora_retiro"):
                    horario = f"Retiro: {reg['hora_retiro']}"

                fila = [
                    reg.get("fecha", "-"),
                    reg.get("curso_nombre", "-"),
                    reg.get("alumno_completo", "-"),
                    reg.get("dni") or "-",
                    estado,
                    horario,
                    reg.get("motivo_retiro") or "-",
                    reg.get("registrado_por") or "-",
                ]
                writer.writerow(fila)

        return Resultado.exito(f"Exportación exitosa a {path.name}", datos=str(path))
    except Exception as e:
        return Resultado.error(f"Error al exportar partes diarios: {e}")


def exportar_asistencias_catedra_a_csv(registros: list[dict], ruta_archivo: str) -> Resultado:
    """
    Exporta una lista de asistencias de cátedra a un archivo CSV codificado con UTF-8 con BOM.
    """
    if not registros:
        return Resultado.error("No hay registros para exportar")

    try:
        path = Path(ruta_archivo)
        path.parent.mkdir(parents=True, exist_ok=True)

        campos = [
            "Fecha",
            "Curso",
            "Materia",
            "Alumno",
            "DNI",
            "Estado",
            "Observaciones",
            "Docente",
        ]

        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(campos)

            for reg in registros:
                estado = (reg.get("estado") or "-").capitalize()
                fila = [
                    reg.get("fecha", "-"),
                    reg.get("curso_nombre", "-"),
                    reg.get("materia_nombre", "-"),
                    reg.get("alumno_completo", "-"),
                    reg.get("dni") or "-",
                    estado,
                    reg.get("observaciones") or "-",
                    reg.get("profesor_completo") or "-",
                ]
                writer.writerow(fila)

        return Resultado.exito(f"Exportación exitosa a {path.name}", datos=str(path))
    except Exception as e:
        return Resultado.error(f"Error al exportar asistencias de cátedra: {e}")


def exportar_resumen_global_a_csv(registros: list[dict], ruta_archivo: str) -> Resultado:
    """
    Exporta el resumen global diario (agrupado por fecha y curso) a CSV UTF-8 con BOM.
    """
    if not registros:
        return Resultado.error("No hay registros para exportar")

    try:
        path = Path(ruta_archivo)
        path.parent.mkdir(parents=True, exist_ok=True)

        campos = [
            "Fecha",
            "Curso",
            "Estado Carga",
            "Total",
            "Presentes",
            "Ausentes",
            "Tardes",
            "Retirados",
            "% Presentismo",
            "Registrado por",
        ]

        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(campos)

            for reg in registros:
                pct = reg.get("porcentaje_presentismo")
                pct_str = f"{pct}%" if pct is not None else "-"
                fila = [
                    reg.get("fecha", "-"),
                    reg.get("curso_nombre", "-"),
                    reg.get("estado_carga", "-"),
                    reg.get("total_registrados", 0),
                    reg.get("presentes", 0),
                    reg.get("ausentes", 0),
                    reg.get("tardes", 0),
                    reg.get("retirados", 0),
                    pct_str,
                    reg.get("registrado_por") or "-",
                ]
                writer.writerow(fila)

        return Resultado.exito(f"Exportación exitosa a {path.name}", datos=str(path))
    except Exception as e:
        return Resultado.error(f"Error al exportar resumen global: {e}")
