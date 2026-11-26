"""Pruebas unitarias para el servicio de asistencia de cátedra (profesor)."""
import unittest
from database.conexion import conexion
from servicios import asistencia
from servicios import horario


class TestAsistenciaMateria(unittest.TestCase):
    def setUp(self):
        with conexion() as conn:
            c = conn.cursor()
            # Obtenemos un curso, profesor y alumno existentes
            c.execute("SELECT id FROM curso LIMIT 1")
            self.curso_id = c.fetchone()["id"]

            c.execute("SELECT id FROM usuario WHERE rol = 'profesor' LIMIT 1")
            prof = c.fetchone()
            self.profesor_id = prof["id"] if prof else 1

            c.execute("SELECT id FROM materia WHERE curso_id = ? LIMIT 1", (self.curso_id,))
            mat = c.fetchone()
            if mat:
                self.materia_id = mat["id"]
            else:
                res = horario.crear_materia_si_no_existe(self.curso_id, "Materia Asistencia Test")
                self.materia_id = res.datos["id"]

            c.execute("SELECT numero FROM alumno WHERE curso_id = ? AND activo = 1 LIMIT 1", (self.curso_id,))
            al = c.fetchone()
            self.alumno_numero = al["numero"] if al else 1001

            # Limpiar asistencias de prueba para la fecha 2026-11-20
            c.execute("DELETE FROM asistencia WHERE fecha = '2026-11-20'")

    def test_obtener_asistencia_materia_default(self):
        res = asistencia.obtener_asistencia_materia(self.curso_id, self.materia_id, "2026-11-20")
        self.assertTrue(res.ok)
        self.assertIn("alumnos", res.datos)
        self.assertFalse(res.datos["ya_registrado"])
        if res.datos["alumnos"]:
            primer_alumno = res.datos["alumnos"][0]
            self.assertEqual(primer_alumno["estado"], "presente")

    def test_guardar_y_recuperar_asistencia_materia(self):
        registros = [
            {
                "alumno_numero": self.alumno_numero,
                "estado": "ausente",
                "observaciones": "Fiebre y reposo",
            }
        ]
        res_guardar = asistencia.guardar_asistencia_materia(
            self.materia_id, "2026-11-20", registros, self.profesor_id
        )
        self.assertTrue(res_guardar.ok)

        # Ahora obtenemos y verificamos que ya_registrado sea True y que el estado sea 'ausente'
        res_obtener = asistencia.obtener_asistencia_materia(
            self.curso_id, self.materia_id, "2026-11-20"
        )
        self.assertTrue(res_obtener.ok)
        self.assertTrue(res_obtener.datos["ya_registrado"])

        alumnos = {a["numero"]: a for a in res_obtener.datos["alumnos"]}
        if self.alumno_numero in alumnos:
            al = alumnos[self.alumno_numero]
            self.assertEqual(al["estado"], "ausente")
            self.assertEqual(al["observaciones"], "Fiebre y reposo")

    def test_listar_materias_de_profesor_en_curso(self):
        res = horario.listar_materias_de_profesor_en_curso(self.curso_id, self.profesor_id)
        self.assertTrue(res.ok)
        self.assertIsInstance(res.datos, list)

    def test_interfaz_flujo_dual_toma_asistencia(self):
        import sys
        from PySide6.QtWidgets import QApplication
        from interfaz.admin import VentanaAdmin

        app = QApplication.instance() or QApplication(sys.argv)
        v = VentanaAdmin({"id": self.profesor_id, "nombre": "Docente Test", "rol": "profesor"})

        # 1. En rol profesor, btn_tomar_lista en PanelCursos debe decir '📝 Asistencia de Clase'
        v.panel_cursos.cambiar_rol("profesor", usuario_id=self.profesor_id)
        self.assertEqual(v.panel_cursos.btn_tomar_lista.text(), "📝 Asistencia de Clase")
        self.assertFalse(v.panel_cursos.btn_tomar_lista.isHidden())

        # 2. En rol preceptor y admin, debe decir '📋 Tomar Lista'
        v.panel_cursos.cambiar_rol("preceptor", usuario_id=self.profesor_id)
        self.assertEqual(v.panel_cursos.btn_tomar_lista.text(), "📋 Tomar Lista")

        v.panel_cursos.cambiar_rol("admin", usuario_id=self.profesor_id)
        self.assertEqual(v.panel_cursos.btn_tomar_lista.text(), "📋 Tomar Lista")

        # 3. En rol directivo, el botón de tomar lista debe estar oculto
        v.panel_cursos.cambiar_rol("directivo", usuario_id=self.profesor_id)
        self.assertTrue(v.panel_cursos.btn_tomar_lista.isHidden())

        # 4. Probar flujo dual desde HUB hacia PanelCursos
        v.panel_cursos.cambiar_rol("profesor", usuario_id=self.profesor_id)
        v.panel_hub.tomar_asistencia_materia_solicitada.emit(self.curso_id, self.materia_id)
        self.assertEqual(v.stack.currentIndex(), 1)  # Se cambió a PanelCursos
        self.assertEqual(v.panel_cursos.stack.currentIndex(), 3)  # Se abrió VistaTomaAsistenciaMateria

        v.close()



if __name__ == "__main__":
    unittest.main()
