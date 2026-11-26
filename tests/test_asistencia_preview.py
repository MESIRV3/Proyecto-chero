"""Tests para la vista de consulta jerárquica y servicios de auditoría de asistencia."""
import unittest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from database.conexion import conexion
from servicios.asistencia import (
    guardar_asistencia_materia,
    listar_historial_asistencia,
)
from servicios.lista_diaria import (
    listar_historial_lista_diaria,
    listar_resumen_global_diario,
)
from interfaz.asistencia_preview import PanelAsistencia


class TestAsistenciaPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_listar_historial_lista_diaria(self):
        """Verifica que el servicio devuelva los registros con formato enriquecido."""
        registros = listar_historial_lista_diaria()
        self.assertIsInstance(registros, list)
        if registros:
            r = registros[0]
            self.assertIn("fecha", r)
            self.assertIn("curso_nombre", r)
            self.assertIn("alumno_completo", r)
            self.assertIn("estado", r)
            self.assertIn("registrado_por", r)

    def test_listar_historial_asistencia_con_datos(self):
        """Inserta una asistencia de cátedra y verifica que el historial la devuelva."""
        # Obtener un alumno activo, materia y usuario docente
        with conexion() as conn:
            c = conn.cursor()
            c.execute("SELECT numero, curso_id FROM alumno WHERE activo = 1 LIMIT 1")
            alumno = c.fetchone()
            self.assertIsNotNone(alumno, "Debe existir al menos un alumno activo en la BD de pruebas")
            alumno_num = alumno["numero"]
            curso_id = alumno["curso_id"]

            c.execute("SELECT id FROM materia WHERE curso_id = ? LIMIT 1", (curso_id,))
            materia = c.fetchone()
            if not materia:
                c.execute("SELECT id FROM materia LIMIT 1")
                materia = c.fetchone()
            materia_id = materia["id"]

            c.execute("SELECT id FROM usuario WHERE rol = 'profesor' LIMIT 1")
            prof = c.fetchone()
            prof_id = prof["id"] if prof else 1

        fecha_test = "2026-11-12"
        res = guardar_asistencia_materia(
            materia_id=materia_id,
            fecha=fecha_test,
            registros=[{"alumno_numero": alumno_num, "estado": "presente", "observaciones": "Clase OK"}],
            profesor_id=prof_id,
        )
        self.assertTrue(res.ok)

        # Consultar historial
        historial = listar_historial_asistencia(
            curso_id=curso_id,
            alumno_numero=alumno_num,
            fecha_desde=fecha_test,
            fecha_hasta=fecha_test,
        )
        self.assertGreaterEqual(len(historial), 1)
        r = historial[0]
        self.assertEqual(r["alumno_numero"], alumno_num)
        self.assertEqual(r["estado"], "presente")
        self.assertEqual(r["observaciones"], "Clase OK")
        self.assertIn("materia_nombre", r)
        self.assertIn("profesor_completo", r)

    def test_panel_asistencia_filtros_en_cascada(self):
        """Verifica la cascada Turno -> Curso -> Alumnos en el PanelAsistencia."""
        panel = PanelAsistencia(ciclo_id=1)
        panel.recargar_filtros()

        self.assertGreaterEqual(panel.combo_turno.count(), 3)
        self.assertGreaterEqual(panel.combo_curso.count(), 1)
        self.assertGreaterEqual(panel.combo_alumno.count(), 1)

        # Filtrar por turno 'Mañana'
        idx_manana = panel.combo_turno.findData("Mañana")
        self.assertGreaterEqual(idx_manana, 0)
        panel.combo_turno.setCurrentIndex(idx_manana)

        # Verificar que los cursos listados pertenezcan a turno Mañana
        for i in range(1, panel.combo_curso.count()):
            texto = panel.combo_curso.itemText(i)
            self.assertIn("Mañana", texto)

        # Seleccionar el primer curso real
        if panel.combo_curso.count() > 1:
            panel.combo_curso.setCurrentIndex(1)
            # El combo de alumnos debe tener 'Todos los alumnos del curso' y alumnos específicos
            self.assertEqual(panel.combo_alumno.itemText(0), "Todos los alumnos del curso")

    def test_panel_asistencia_consultar_y_kpis(self):
        """Verifica la consulta y el cálculo de métricas en las tarjetas KPI."""
        panel = PanelAsistencia(ciclo_id=1)
        panel.date_desde.setDate(QDate(2026, 1, 1))
        panel.date_hasta.setDate(QDate(2026, 12, 31))
        panel._consultar()

        # Debe haber poblado las filas de partes diarios si existen registros en la BD
        if panel.registros_partes:
            self.assertEqual(panel.tabla_partes.rowCount(), len(panel.registros_partes))
            self.assertNotEqual(panel.card_presentismo.valor_label.text(), "—")
            self.assertNotEqual(panel.card_presentes.valor_label.text(), "—")

    def test_panel_asistencia_cambio_rol(self):
        """Verifica que el cambio de rol enrute a la pestaña y vista correcta."""
        panel = PanelAsistencia(ciclo_id=1)

        panel.cambiar_rol("profesor", usuario_id=2)
        self.assertEqual(panel.tabs.currentIndex(), 2)
        self.assertIn("Profesor", panel.badge_rol.text())

        panel.cambiar_rol("preceptor", usuario_id=3)
        self.assertEqual(panel.tabs.currentIndex(), 0)
        self.assertIn("Preceptor", panel.badge_rol.text())

        panel.cambiar_rol("directivo", usuario_id=4)
        self.assertEqual(panel.tabs.currentIndex(), 0)
        self.assertIn("Directivo", panel.badge_rol.text())

    def test_listar_resumen_global_diario_rango_y_dia_unico(self):
        """Verifica el resumen global agrupado por curso/fecha en rango y en día único."""
        resumen_rango = listar_resumen_global_diario(
            fecha_desde="2026-01-01",
            fecha_hasta="2026-12-31",
            ciclo_id=1,
        )
        self.assertIsInstance(resumen_rango, list)
        if resumen_rango:
            item = resumen_rango[0]
            self.assertEqual(item["estado_carga"], "Registrado")
            self.assertIn("curso_nombre", item)
            self.assertIn("presentes", item)
            self.assertIn("ausentes", item)
            self.assertIn("porcentaje_presentismo", item)

        # Consulta de un solo día sin carga: debe listar cursos con estado 'Sin registrar'
        resumen_dia = listar_resumen_global_diario(
            fecha_desde="2026-01-02",
            fecha_hasta="2026-01-02",
            ciclo_id=1,
        )
        self.assertGreaterEqual(len(resumen_dia), 1)
        self.assertTrue(all(r["estado_carga"] == "Sin registrar" for r in resumen_dia))

        # Filtro por turno inexistente en ciclo no debe devolver registros de otro turno
        resumen_tarde = listar_resumen_global_diario(
            turno="TurnoInexistente",
            fecha_desde="2026-01-01",
            fecha_hasta="2026-12-31",
            ciclo_id=1,
        )
        self.assertEqual(len(resumen_tarde), 0)

    def test_panel_asistencia_drilldown_resumen_a_detalle(self):
        """Verifica que el doble clic en el resumen global abra el detalle por alumno."""
        panel = PanelAsistencia(ciclo_id=1)
        panel._fijar_rango_ciclo()

        if panel.registros_resumen:
            self.assertEqual(panel.tabla_resumen.rowCount(), len(panel.registros_resumen))
            reg_esperado = panel.registros_resumen[0]
            panel._abrir_detalle_desde_resumen(0, 0)

            self.assertEqual(panel.tabs.currentIndex(), 1)
            self.assertEqual(panel.combo_curso.currentData(), reg_esperado["curso_id"])
            self.assertEqual(
                panel.date_desde.date().toString("yyyy-MM-dd"),
                reg_esperado["fecha"],
            )
            self.assertEqual(
                panel.date_hasta.date().toString("yyyy-MM-dd"),
                reg_esperado["fecha"],
            )

    def test_panel_asistencia_validacion_rango_fechas(self):
        """Verifica que un rango inválido (desde > hasta) muestre error y limpie datos."""
        panel = PanelAsistencia(ciclo_id=1)
        panel.date_desde.setDate(QDate(2026, 12, 31))
        panel.date_hasta.setDate(QDate(2026, 1, 1))
        panel._consultar()

        self.assertFalse(panel.label_mensaje.isHidden())
        self.assertIn("posterior", panel.label_mensaje.text().lower())
        self.assertEqual(panel.tabla_resumen.rowCount(), 0)
        self.assertEqual(panel.tabla_partes.rowCount(), 0)
        self.assertEqual(panel.tabla_materias.rowCount(), 0)
        self.assertEqual(panel.card_presentismo.valor_label.text(), "—")


if __name__ == "__main__":
    unittest.main()
