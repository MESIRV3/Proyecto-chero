"""Pruebas unitarias y de interfaz para asignacion de cursos a preceptores y horarios a profesores."""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from servicios import horario as servicio_horario
from servicios import preceptor as servicio_preceptor
from servicios import usuario as servicio_usuario
from interfaz.personal import PanelPersonal
from interfaz.admin import VentanaAdmin


class TestAsignacionPersonal(unittest.TestCase):
    """Pruebas hermeticas sobre BD temporal para preceptores, horarios por docente y PanelPersonal."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.addCleanup(self._limpiar_temp)

        schema_path = BASE_DIR / "database" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)

        self.patch_db = mock.patch("database.conexion.DB_PATH", self.db_path)
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)

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
        cur = conn.cursor()
        # Dos ciclos lectivos
        cur.execute(
            "INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
            (2026, "2026-03-01", "2026-12-31"),
        )
        self.ciclo_actual = cur.lastrowid
        cur.execute(
            "INSERT INTO ciclo_lectivo (anio, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
            (2025, "2025-03-01", "2025-12-31"),
        )
        self.ciclo_anterior = cur.lastrowid

        # Cursos en ciclo actual y ciclo anterior
        cur.execute(
            "INSERT INTO curso (ciclo_id, anio, division, especialidad, turno) VALUES (?, ?, ?, ?, ?)",
            (self.ciclo_actual, 1, "1", None, "Mañana"),
        )
        self.curso_1 = cur.lastrowid
        cur.execute(
            "INSERT INTO curso (ciclo_id, anio, division, especialidad, turno) VALUES (?, ?, ?, ?, ?)",
            (self.ciclo_actual, 3, "1", "Computacion", "Tarde"),
        )
        self.curso_2 = cur.lastrowid
        cur.execute(
            "INSERT INTO curso (ciclo_id, anio, division, especialidad, turno) VALUES (?, ?, ?, ?, ?)",
            (self.ciclo_anterior, 1, "1", None, "Mañana"),
        )
        self.curso_viejo = cur.lastrowid

        # Materias
        cur.execute("INSERT INTO materia (nombre, curso_id) VALUES (?, ?)", ("Matematica", self.curso_1))
        self.materia_1 = cur.lastrowid
        cur.execute("INSERT INTO materia (nombre, curso_id) VALUES (?, ?)", ("Programacion", self.curso_2))
        self.materia_2 = cur.lastrowid
        cur.execute("INSERT INTO materia (nombre, curso_id) VALUES (?, ?)", ("Historia", self.curso_viejo))
        self.materia_vieja = cur.lastrowid

        # Usuarios
        cur.execute(
            "INSERT INTO usuario (nombre, apellido, username, password, rol, activo) VALUES (?, ?, ?, ?, ?, 1)",
            ("Maria", "Gonzalez", "mgonzalez", "x", "preceptor"),
        )
        self.preceptor_id = cur.lastrowid
        cur.execute(
            "INSERT INTO usuario (nombre, apellido, username, password, rol, activo) VALUES (?, ?, ?, ?, ?, 1)",
            ("Carlos", "Perez", "cperez", "x", "profesor"),
        )
        self.profesor_id = cur.lastrowid
        cur.execute(
            "INSERT INTO usuario (nombre, apellido, username, password, rol, activo) VALUES (?, ?, ?, ?, ?, 1)",
            ("Roberto", "Sosa", "rsosa", "x", "directivo"),
        )
        self.directivo_id = cur.lastrowid
        cur.execute(
            "INSERT INTO usuario (nombre, apellido, username, password, rol, activo) VALUES (?, ?, ?, ?, ?, 1)",
            ("Super", "Admin", "admin", "x", "admin"),
        )
        self.admin_id = cur.lastrowid
        conn.commit()

    def test_listar_usuarios_por_rol_sin_password(self):
        res_prec = servicio_usuario.listar_usuarios(rol="preceptor")
        self.assertTrue(res_prec.ok)
        self.assertEqual(len(res_prec.datos), 1)
        self.assertEqual(res_prec.datos[0]["username"], "mgonzalez")
        self.assertNotIn("password", res_prec.datos[0])

        res_prof = servicio_usuario.listar_usuarios(rol="profesor")
        self.assertTrue(res_prof.ok)
        self.assertEqual(len(res_prof.datos), 1)
        self.assertEqual(res_prof.datos[0]["username"], "cperez")

    def test_asignar_y_desasignar_cursos_a_preceptor_y_validaciones(self):
        # Rechazar usuario que no es preceptor
        res_rol = servicio_preceptor.asignar_curso_a_preceptor(self.profesor_id, self.curso_1)
        self.assertFalse(res_rol.ok)

        # Rechazar curso inexistente
        res_curso = servicio_preceptor.asignar_curso_a_preceptor(self.preceptor_id, 9999)
        self.assertFalse(res_curso.ok)

        # Asignacion exitosa
        res_ok = servicio_preceptor.asignar_curso_a_preceptor(self.preceptor_id, self.curso_1)
        self.assertTrue(res_ok.ok, res_ok.mensaje)

        # Evitar duplicado
        res_dup = servicio_preceptor.asignar_curso_a_preceptor(self.preceptor_id, self.curso_1)
        self.assertFalse(res_dup.ok)

        # Consultar cursos asignados y preceptores del curso
        res_cursos = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_actual)
        self.assertTrue(res_cursos.ok)
        self.assertEqual([c["id"] for c in res_cursos.datos], [self.curso_1])

        res_precs = servicio_preceptor.listar_preceptores_de_curso(self.curso_1)
        self.assertTrue(res_precs.ok)
        self.assertEqual([p["id"] for p in res_precs.datos], [self.preceptor_id])

        # Desasignar
        res_del = servicio_preceptor.desasignar_curso_de_preceptor(self.preceptor_id, self.curso_1)
        self.assertTrue(res_del.ok)
        res_cursos_post = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_actual)
        self.assertEqual(len(res_cursos_post.datos), 0)

    def test_guardar_cursos_de_preceptor_respeta_ciclo_lectivo(self):
        # Asignar curso de ciclo anterior primero
        self.assertTrue(servicio_preceptor.asignar_curso_a_preceptor(self.preceptor_id, self.curso_viejo).ok)

        # Guardar cursos del ciclo actual
        res = servicio_preceptor.guardar_cursos_de_preceptor(
            self.preceptor_id, [self.curso_1, self.curso_2], ciclo_id=self.ciclo_actual
        )
        self.assertTrue(res.ok, res.mensaje)

        # Ciclo actual tiene ambos cursos y ciclo anterior se preserva intacto
        c_act = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_actual).datos
        c_ant = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_anterior).datos
        self.assertEqual({c["id"] for c in c_act}, {self.curso_1, self.curso_2})
        self.assertEqual([c["id"] for c in c_ant], [self.curso_viejo])

        # Conteo por ciclo actual debe ser 2 (no 3)
        conteos = servicio_preceptor.listar_preceptores_con_conteo(self.ciclo_actual).datos
        self.assertEqual(conteos[0]["cantidad_cursos"], 2)

    def test_listar_horarios_de_profesor_y_conteo_por_ciclo(self):
        # Horario en ciclo actual y en ciclo anterior
        r1 = servicio_horario.agregar_horario(
            self.curso_1, 1, "07:30", "08:50", self.materia_1, self.profesor_id
        )
        self.assertTrue(r1.ok, r1.mensaje)
        r2 = servicio_horario.agregar_horario(
            self.curso_viejo, 2, "09:00", "10:20", self.materia_vieja, self.profesor_id
        )
        self.assertTrue(r2.ok, r2.mensaje)

        res_act = servicio_horario.listar_horarios_de_profesor(self.profesor_id, self.ciclo_actual)
        self.assertTrue(res_act.ok)
        self.assertEqual(len(res_act.datos), 1)
        self.assertEqual(res_act.datos[0]["materia_nombre"], "Matematica")

        conteos = servicio_horario.listar_profesores_con_conteo(self.ciclo_actual).datos
        self.assertEqual(conteos[0]["cantidad_horarios"], 1)

    def test_panel_personal_directivo_y_admin_asignan_cursos_y_horarios(self):
        panel = PanelPersonal(self.ciclo_actual, rol_actual="directivo")

        # 1. Asignar curso_2 al preceptor desde Directivo
        panel.checks_cursos[self.curso_2].setChecked(True)
        panel._guardar_asignaciones_preceptor()
        asignados = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_actual).datos
        self.assertEqual([c["id"] for c in asignados], [self.curso_2])

        # 2. Asignar horario al profesor desde Directivo usando atajo horario
        panel._set_horario_prof("09:00", "10:20")
        idx_c1 = panel.combo_curso_prof.findData(self.curso_1)
        panel.combo_curso_prof.setCurrentIndex(idx_c1)
        panel._asignar_horario_profesor()

        horarios_prof = servicio_horario.listar_horarios_de_profesor(self.profesor_id, self.ciclo_actual).datos
        self.assertEqual(len(horarios_prof), 1)
        self.assertEqual(horarios_prof[0]["hora_inicio"], "09:00")
        self.assertEqual(horarios_prof[0]["hora_fin"], "10:20")
        self.assertEqual(panel.tabla_horarios_prof.rowCount(), 1)

        # 3. Defensa en profundidad: si rol es preceptor, no puede guardar cambios
        panel.cambiar_rol("preceptor")
        panel.checks_cursos[self.curso_2].setChecked(False)
        panel._guardar_asignaciones_preceptor()
        asignados_post = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_actual).datos
        self.assertEqual([c["id"] for c in asignados_post], [self.curso_2])

        panel.close()

    def test_vista_preceptor_muestra_solo_cursos_asignados(self):
        # Asignar solo curso_1 al preceptor
        self.assertTrue(
            servicio_preceptor.guardar_cursos_de_preceptor(
                self.preceptor_id, [self.curso_1], ciclo_id=self.ciclo_actual
            ).ok
        )

        v = VentanaAdmin({"id": self.preceptor_id, "nombre": "Maria", "rol": "preceptor"})
        self.assertTrue(v.botones_nav[4].isHidden())
        self.assertEqual(len(v.panel_cursos.cursos_cargados), 1)
        self.assertEqual(v.panel_cursos.cursos_cargados[0]["id"], self.curso_1)
        self.assertEqual(v.panel_hub.tabla_cursos.rowCount(), 1)
        v.close()

    def test_login_directivo_accede_a_personal_y_gestion_horarios(self):
        v = VentanaAdmin({"id": self.directivo_id, "nombre": "Roberto", "rol": "directivo"})
        self.assertTrue(v.combo_rol_vista.isHidden())
        self.assertFalse(v.botones_nav[4].isHidden())
        self.assertEqual(v.panel_personal.rol_actual, "directivo")
        self.assertEqual(v.panel_cursos.btn_horarios.text(), "⏰ Gestionar Horarios")
        v.close()


if __name__ == "__main__":
    unittest.main()
