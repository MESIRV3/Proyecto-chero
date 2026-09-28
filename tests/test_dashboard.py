"""Tests unitarios para servicios/dashboard.py — strict TDD, hermeticos."""
import os
import sys
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from servicios.dashboard import obtener_metricas_hub


class TestDashboardMetrics(unittest.TestCase):
    """Métricas del HUB acotadas por ciclo lectivo."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.addCleanup(self._limpiar_temp)

        schema_path = BASE_DIR / "database" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)

        self.patch_db_path = mock.patch("database.conexion.DB_PATH", self.db_path)
        self.patch_db_path.start()
        self.addCleanup(self.patch_db_path.stop)

        with sqlite3.connect(self.db_path) as conn:
            self._sembrar_datos(conn)

    def _limpiar_temp(self):
        try:
            os.close(self.db_fd)
        except OSError:
            pass
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def _sembrar_datos(self, conn):
        hoy = date.today().isoformat()
        hace_7 = (date.today() - timedelta(days=7)).isoformat()
        hace_8 = (date.today() - timedelta(days=8)).isoformat()

        cur = conn.cursor()

        # Dos ciclos lectivos
        cur.execute(
            "INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
            (2030, "2030-03-01", "2030-12-31"),
        )
        ciclo_a = cur.lastrowid
        cur.execute(
            "INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
            (2031, "2031-03-01", "2031-12-31"),
        )
        ciclo_b = cur.lastrowid

        # Un curso por ciclo
        cur.execute(
            "INSERT INTO curso (ciclo_id, anio, division, especialidad, turno) VALUES (?, ?, ?, ?, ?)",
            (ciclo_a, 1, "A", None, "Mañana"),
        )
        curso_a = cur.lastrowid
        cur.execute(
            "INSERT INTO curso (ciclo_id, anio, division, especialidad, turno) VALUES (?, ?, ?, ?, ?)",
            (ciclo_b, 1, "B", None, "Tarde"),
        )
        curso_b = cur.lastrowid

        # Una materia por curso
        cur.execute(
            "INSERT INTO materia (nombre, curso_id) VALUES (?, ?)",
            ("Matemáticas", curso_a),
        )
        materia_a = cur.lastrowid
        cur.execute(
            "INSERT INTO materia (nombre, curso_id) VALUES (?, ?)",
            ("Historia", curso_b),
        )
        materia_b = cur.lastrowid

        # Alumnos en ciclo A: 2 activos, 1 de baja
        cur.execute(
            "INSERT INTO alumno (numero, nombre, apellido, dni, nacionalidad, curso_id, activo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1001, "Ana", "Activa", "11111111", None, curso_a, 1),
        )
        cur.execute(
            "INSERT INTO alumno (numero, nombre, apellido, dni, nacionalidad, curso_id, activo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1002, "Bruno", "Activo", "11111112", None, curso_a, 1),
        )
        cur.execute(
            "INSERT INTO alumno (numero, nombre, apellido, dni, nacionalidad, curso_id, activo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1003, "Carla", "Baja", "11111113", None, curso_a, 0),
        )

        # Cinco alumnos activos en ciclo B (para comprobar scoping con varios registros)
        alumnos_b = []
        for i in range(5):
            numero = 2001 + i
            alumnos_b.append(numero)
            cur.execute(
                "INSERT INTO alumno (numero, nombre, apellido, dni, nacionalidad, curso_id, activo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (numero, f"Alumno{i+1}", "Otro", f"2222222{i}", None, curso_b, 1),
            )

        # Usuario que registra asistencias
        cur.execute(
            "INSERT INTO usuario (nombre, apellido, username, password, rol) VALUES (?, ?, ?, ?, ?)",
            ("Profe", "Uno", "profe1", "x", "profesor"),
        )
        usuario_id = cur.lastrowid

        # Asistencias en ciclo A:
        # - hoy: 2 registros
        # - hace 7 días: 2 registros (dentro de la semana)
        # - hace 8 días: 1 registro (fuera de la semana)
        for alumno in (1001, 1002):
            cur.execute(
                "INSERT INTO asistencia (alumno_numero, materia_id, fecha, estado, registrado_por) "
                "VALUES (?, ?, ?, ?, ?)",
                (alumno, materia_a, hoy, "presente", usuario_id),
            )
            cur.execute(
                "INSERT INTO asistencia (alumno_numero, materia_id, fecha, estado, registrado_por) "
                "VALUES (?, ?, ?, ?, ?)",
                (alumno, materia_a, hace_7, "presente", usuario_id),
            )
        cur.execute(
            "INSERT INTO asistencia (alumno_numero, materia_id, fecha, estado, registrado_por) "
            "VALUES (?, ?, ?, ?, ?)",
            (1001, materia_a, hace_8, "ausente", usuario_id),
        )

        # Asistencias en ciclo B: 5 registros de hoy, uno por alumno
        # (deben ser ignoradas al consultar ciclo A)
        for alumno in alumnos_b:
            cur.execute(
                "INSERT INTO asistencia (alumno_numero, materia_id, fecha, estado, registrado_por) "
                "VALUES (?, ?, ?, ?, ?)",
                (alumno, materia_b, hoy, "presente", usuario_id),
            )

        conn.commit()
        self.ciclo_a = ciclo_a
        self.ciclo_b = ciclo_b

    def test_ciclo_valido_devuelve_seis_claves_con_valores_correctos(self):
        resultado = obtener_metricas_hub(self.ciclo_a)

        self.assertTrue(resultado.ok, resultado.mensaje)
        self.assertIsNotNone(resultado.datos)
        self.assertEqual(
            set(resultado.datos.keys()),
            {
                "alumnos_activos",
                "alumnos_baja",
                "total_cursos",
                "asistencias_hoy",
                "asistencias_semana",
                "ciclo_anio",
            },
        )
        self.assertEqual(resultado.datos["ciclo_anio"], 2030)
        self.assertEqual(resultado.datos["alumnos_activos"], 2)
        self.assertEqual(resultado.datos["alumnos_baja"], 1)
        self.assertEqual(resultado.datos["total_cursos"], 1)
        self.assertEqual(resultado.datos["asistencias_hoy"], 2)
        self.assertEqual(resultado.datos["asistencias_semana"], 4)

    def test_scoping_excluye_asistencias_de_otro_ciclo(self):
        resultado_a = obtener_metricas_hub(self.ciclo_a)
        resultado_b = obtener_metricas_hub(self.ciclo_b)

        self.assertTrue(resultado_a.ok)
        self.assertTrue(resultado_b.ok)
        # Ciclo A no debe contagiar las 5 asistencias de hoy del ciclo B
        self.assertEqual(resultado_a.datos["asistencias_hoy"], 2)
        self.assertEqual(resultado_a.datos["asistencias_semana"], 4)
        # Ciclo B solo ve su propia asistencia
        self.assertEqual(resultado_b.datos["asistencias_hoy"], 5)
        self.assertEqual(resultado_b.datos["asistencias_semana"], 5)

    def test_borde_semanal_incluye_hoy_menos_7_y_excluye_hoy_menos_8(self):
        resultado = obtener_metricas_hub(self.ciclo_a)

        # Sabemos que hay 2 asistencias hoy y 2 de hace 7 días
        self.assertEqual(resultado.datos["asistencias_hoy"], 2)
        self.assertEqual(resultado.datos["asistencias_semana"], 4)
        # La de hace 8 días no debe sumar
        self.assertNotEqual(resultado.datos["asistencias_semana"], 5)

    def test_ciclo_inexistente_devuelve_ceros_y_anio_actual(self):
        resultado = obtener_metricas_hub(9999)

        self.assertTrue(resultado.ok, resultado.mensaje)
        self.assertEqual(resultado.datos["alumnos_activos"], 0)
        self.assertEqual(resultado.datos["alumnos_baja"], 0)
        self.assertEqual(resultado.datos["total_cursos"], 0)
        self.assertEqual(resultado.datos["asistencias_hoy"], 0)
        self.assertEqual(resultado.datos["asistencias_semana"], 0)
        self.assertEqual(resultado.datos["ciclo_anio"], date.today().year)

    def test_ciclo_none_devuelve_ceros_y_anio_actual(self):
        resultado = obtener_metricas_hub(None)

        self.assertTrue(resultado.ok, resultado.mensaje)
        self.assertEqual(resultado.datos["alumnos_activos"], 0)
        self.assertEqual(resultado.datos["alumnos_baja"], 0)
        self.assertEqual(resultado.datos["total_cursos"], 0)
        self.assertEqual(resultado.datos["asistencias_hoy"], 0)
        self.assertEqual(resultado.datos["asistencias_semana"], 0)
        self.assertEqual(resultado.datos["ciclo_anio"], date.today().year)

    def test_falla_de_base_de_datos_devuelve_resultado_error(self):
        with mock.patch("servicios.dashboard.conexion", side_effect=Exception("boom")):
            resultado = obtener_metricas_hub(self.ciclo_a)

        self.assertFalse(resultado.ok)
        self.assertIn("Error al obtener metricas", resultado.mensaje)


if __name__ == "__main__":
    unittest.main()
