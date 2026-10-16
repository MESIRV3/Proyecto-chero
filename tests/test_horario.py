"""Pruebas unitarias para el servicio de horarios y la vista del rol profesor."""
import sys
import unittest
from datetime import date
from PySide6.QtWidgets import QApplication

from database.conexion import conexion
from servicios import horario
from interfaz.admin import VentanaAdmin


class TestHorarioServicio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        # Asegurar datos minimos para pruebas de conflicto
        with conexion() as conn:
            c = conn.cursor()
            # Obtenemos un curso y usuario profesor existentes
            c.execute("SELECT id, ciclo_id FROM curso LIMIT 1")
            curso = c.fetchone()
            self.curso_id = curso["id"]
            self.ciclo_id = curso["ciclo_id"]

            c.execute("SELECT id FROM usuario WHERE rol = 'profesor' LIMIT 1")
            self.profesor_id = c.fetchone()["id"]

            c.execute("SELECT id FROM materia WHERE curso_id = ? LIMIT 1", (self.curso_id,))
            mat = c.fetchone()
            if mat:
                self.materia_id = mat["id"]
            else:
                res = horario.crear_materia_si_no_existe(self.curso_id, "Materia Test")
                self.materia_id = res.datos["id"]

    def test_crear_y_listar_materias(self):
        res_crear = horario.crear_materia_si_no_existe(self.curso_id, "Filosofia Test")
        self.assertTrue(res_crear.ok)
        materia_id = res_crear.datos["id"]

        # Evitar duplicados
        res_dup = horario.crear_materia_si_no_existe(self.curso_id, "Filosofia Test")
        self.assertTrue(res_dup.ok)
        self.assertEqual(res_dup.datos["id"], materia_id)

        # Listar materias
        res_lista = horario.listar_materias_de_curso(self.curso_id)
        self.assertTrue(res_lista.ok)
        nombres = [m["nombre"] for m in res_lista.datos]
        self.assertIn("Filosofia Test", nombres)

    def test_agregar_horario_y_validaciones(self):
        # 1. Dia invalido
        res_dia = horario.agregar_horario(
            self.curso_id, 9, 1, "07:30", "08:10", self.materia_id, self.profesor_id
        )
        self.assertFalse(res_dia.ok)

        # 2. Horas invalidas
        res_hora = horario.agregar_horario(
            self.curso_id, 3, 1, "10:00", "09:00", self.materia_id, self.profesor_id
        )
        self.assertFalse(res_hora.ok)

        # 3. Horario exitoso el Miercoles (dia 3, bloque 8)
        res_ok = horario.agregar_horario(
            self.curso_id, 3, 8, "12:40", "13:20", self.materia_id, self.profesor_id
        )
        self.assertTrue(res_ok.ok, res_ok.mensaje)
        horario_id = res_ok.datos["id"]

        # 4. Superposicion en el mismo curso y bloque
        res_conflicto = horario.agregar_horario(
            self.curso_id, 3, 8, "12:40", "13:20", self.materia_id, self.profesor_id
        )
        self.assertFalse(res_conflicto.ok)
        self.assertIn("ya tiene ocupado", res_conflicto.mensaje)

        # 5. Eliminar horario
        res_del = horario.eliminar_horario(horario_id)
        self.assertTrue(res_del.ok)

    def test_obtener_cursos_del_dia_por_profesor(self):
        # Agregar un horario temporal para el viernes (dia 5)
        res_add = horario.agregar_horario(
            self.curso_id, 5, 1, "07:30", "08:10", self.materia_id, self.profesor_id
        )
        self.assertTrue(res_add.ok)
        hid = res_add.datos["id"]

        try:
            # Consultar para el dia 5 (Viernes)
            res = horario.obtener_cursos_del_dia_por_profesor(
                self.ciclo_id, self.profesor_id, dia_semana=5
            )
            self.assertTrue(res.ok)
            cursos = res.datos["cursos"]
            self.assertGreaterEqual(len(cursos), 1)
            curso_ids = [c["curso_id"] for c in cursos]
            self.assertIn(self.curso_id, curso_ids)

            # Para el domingo (dia 7) no debe tener cursos
            res_dom = horario.obtener_cursos_del_dia_por_profesor(
                self.ciclo_id, self.profesor_id, dia_semana=7
            )
            self.assertTrue(res_dom.ok)
            self.assertEqual(len(res_dom.datos["cursos"]), 0)
        finally:
            horario.eliminar_horario(hid)

    def test_interfaz_profesor_boton_horarios_y_hub(self):
        v = VentanaAdmin({"id": self.profesor_id, "nombre": "Docente Test", "rol": "profesor"})

        # En rol profesor, la tabla del Hub debe tener 5 columnas (con Materia y Horario)
        self.assertEqual(v.panel_hub.rol_actual, "profesor")
        self.assertEqual(v.panel_hub.tabla_cursos.columnCount(), 5)
        self.assertIn("Cursos a cargo hoy", v.panel_hub.lbl_titulo_tabla.text())

        # En PanelCursos, el botón de Mis Horarios debe estar visible y Eliminar curso oculto
        v.panel_cursos.cambiar_rol("profesor", usuario_id=self.profesor_id)
        self.assertTrue(v.panel_cursos.btn_horarios.isVisible() or not v.panel_cursos.btn_horarios.isHidden())
        self.assertTrue(v.panel_cursos.btn_eliminar.isHidden())

        # En rol admin, btn_horarios debe decir 'Gestionar Horarios' y btn_eliminar debe estar visible
        v.panel_cursos.cambiar_rol("admin", usuario_id=1)
        self.assertEqual(v.panel_cursos.btn_horarios.text(), "⏰ Gestionar Horarios")
        self.assertFalse(v.panel_cursos.btn_eliminar.isHidden())

        v.close()


if __name__ == "__main__":
    unittest.main()
