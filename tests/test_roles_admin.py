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

        # 2. Cambiar a Preceptor
        idx_prec = v.combo_rol_vista.findData("preceptor")
        v.combo_rol_vista.setCurrentIndex(idx_prec)
        self.assertEqual(v.panel_hub.rol_actual, "preceptor")
        self.assertIn("Preceptoría", v.label_titulo_barra.text())
        self.assertFalse(v.panel_hub.btn_accion_1.isHidden())

        # 3. Cambiar a Profesor
        idx_prof = v.combo_rol_vista.findData("profesor")
        v.combo_rol_vista.setCurrentIndex(idx_prof)
        self.assertEqual(v.panel_hub.rol_actual, "profesor")
        self.assertIn("Panel Docente", v.label_titulo_barra.text())
        # En rol profesor, la pestaña de alumnos se oculta
        self.assertTrue(v.botones_nav[2].isHidden())

        v.close()

    def test_usuario_no_admin_no_ve_selector_de_roles(self):
        v = VentanaAdmin({"id": 2, "nombre": "Docente Test", "rol": "profesor"})
        self.assertTrue(v.combo_rol_vista.isHidden())
        self.assertTrue(v.lbl_vista.isHidden())
        v.close()


if __name__ == "__main__":
    unittest.main()
