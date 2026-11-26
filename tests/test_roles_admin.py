"""Pruebas unitarias para el selector de roles e intercalado de vistas en VentanaAdmin."""
import sys
import unittest
from PySide6.QtWidgets import QApplication

from interfaz.admin import VentanaAdmin


class TestRolesAdmin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_admin_puede_cambiar_entre_roles(self):
        v = VentanaAdmin({"id": 1, "nombre": "Admin Test", "rol": "admin"})

        self.assertFalse(v.combo_rol_vista.isHidden())
        self.assertEqual(v.combo_rol_vista.currentData(), "admin")
        self.assertEqual(v.panel_hub.rol_actual, "admin")
        self.assertIn("Panel de Administrador", v.label_titulo_barra.text())

        # 1. Cambiar a Directivo
        idx_dir = v.combo_rol_vista.findData("directivo")
        v.combo_rol_vista.setCurrentIndex(idx_dir)
        self.assertEqual(v.panel_hub.rol_actual, "directivo")
        self.assertIn("Panel Directivo", v.label_titulo_barra.text())
        self.assertIn("Directivo", v.label_usuario.text())
        self.assertTrue(v.panel_hub.btn_accion_1.isHidden())
        # En PanelAlumnos, el directivo no tiene acciones destructivas
        self.assertTrue(v.panel_alumnos.btn_baja.isHidden())
        self.assertTrue(v.panel_alumnos.btn_reactivar.isHidden())
        self.assertTrue(v.panel_alumnos.btn_toggle_alta.isHidden())
        self.assertTrue(v.panel_alumnos.btn_mover.isHidden())
        # En PanelCursos, el directivo gestiona horarios pero no agrega cursos ni toma lista
        self.assertEqual(v.panel_cursos.btn_horarios.text(), "⏰ Gestionar Horarios")
        self.assertTrue(v.panel_cursos.btn_tomar_lista.isHidden())
        # En rol directivo, la seccion Personal esta visible
        self.assertFalse(v.botones_nav[4].isHidden())
        self.assertFalse(v.panel_hub.btn_accion_4.isHidden())

        # 2. Cambiar a Preceptor
        idx_prec = v.combo_rol_vista.findData("preceptor")
        v.combo_rol_vista.setCurrentIndex(idx_prec)
        self.assertEqual(v.panel_hub.rol_actual, "preceptor")
        self.assertIn("Preceptoría", v.label_titulo_barra.text())
        self.assertFalse(v.panel_hub.btn_accion_1.isHidden())
        self.assertTrue(v.botones_nav[4].isHidden())
        self.assertTrue(v.panel_hub.btn_accion_4.isHidden())
        # En PanelAlumnos, el preceptor puede agregar/mover pero no dar de baja/reactivar
        self.assertFalse(v.panel_alumnos.btn_toggle_alta.isHidden())
        self.assertFalse(v.panel_alumnos.btn_mover.isHidden())
        self.assertTrue(v.panel_alumnos.btn_baja.isHidden())
        self.assertTrue(v.panel_alumnos.btn_reactivar.isHidden())
        # En PanelCursos, el preceptor ve horarios y toma lista diaria
        self.assertEqual(v.panel_cursos.btn_horarios.text(), "⏰ Ver Horarios")
        self.assertEqual(v.panel_cursos.btn_tomar_lista.text(), "📋 Tomar Lista")

        # 3. Cambiar a Profesor
        idx_prof = v.combo_rol_vista.findData("profesor")
        v.combo_rol_vista.setCurrentIndex(idx_prof)
        self.assertEqual(v.panel_hub.rol_actual, "profesor")
        self.assertIn("Panel Docente", v.label_titulo_barra.text())
        # En rol profesor, la pestaña de alumnos y personal se ocultan
        self.assertTrue(v.botones_nav[2].isHidden())
        self.assertTrue(v.botones_nav[4].isHidden())
        self.assertTrue(v.panel_hub.btn_accion_4.isHidden())
        # En PanelCursos, toma asistencia de clase
        self.assertEqual(v.panel_cursos.btn_tomar_lista.text(), "📝 Asistencia de Clase")
        # En el HUB del profesor, la grilla de KPIs debe ser perfectamente simetrica (3 + 3 = 6)
        self.assertEqual(v.panel_hub.fila_kpi_1.count(), 3)
        self.assertEqual(v.panel_hub.fila_kpi_2.count(), 3)

        # 4. Volver a Admin
        idx_adm = v.combo_rol_vista.findData("admin")
        v.combo_rol_vista.setCurrentIndex(idx_adm)
        self.assertFalse(v.panel_alumnos.btn_baja.isHidden())
        self.assertFalse(v.panel_alumnos.btn_reactivar.isHidden())
        self.assertFalse(v.panel_alumnos.btn_toggle_alta.isHidden())
        self.assertFalse(v.botones_nav[4].isHidden())
        self.assertFalse(v.panel_hub.btn_accion_4.isHidden())
        self.assertEqual(v.panel_hub.fila_kpi_1.count(), 3)
        self.assertEqual(v.panel_hub.fila_kpi_2.count(), 3)

        # Controles de ventana integrados
        self.assertEqual(v.btn_minimizar.toolTip(), "Minimizar")
        self.assertEqual(v.btn_maximizar.toolTip(), "Maximizar")
        self.assertEqual(v.btn_cerrar.toolTip(), "Cerrar")
        self.assertEqual(v.btn_minimizar.width(), 30)

        v.close()

    def test_usuario_no_admin_no_ve_selector_de_roles(self):
        v = VentanaAdmin({"id": 2, "nombre": "Docente Test", "rol": "profesor"})
        self.assertTrue(v.combo_rol_vista.isHidden())
        self.assertTrue(v.lbl_vista.isHidden())
        v.close()


if __name__ == "__main__":
    unittest.main()
