"""Tests for CSV export service and keyboard shortcuts in attendance views."""
import os
import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from servicios.exportacion import (
    exportar_partes_diarios_a_csv,
    exportar_asistencias_catedra_a_csv,
    exportar_resumen_global_a_csv,
)
from interfaz.admin import FilaTomaLista
from interfaz.toma_asistencia_materia import FilaTomaMateria


class TestExportacionCSV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exportar_partes_diarios_vacio(self):
        """Verifica que una lista vacía retorne un error controlado."""
        ruta = os.path.join(self.temp_dir.name, "vacio.csv")
        res = exportar_partes_diarios_a_csv([], ruta)
        self.assertFalse(res.ok)
        self.assertIn("No hay registros", res.mensaje)

    def test_exportar_partes_diarios_valido(self):
        """Verifica la correcta generación del CSV con encoding utf-8-sig y delimitador ';'."""
        registros = [
            {
                "fecha": "2026-11-12",
                "curso_nombre": "1° 1° - TM",
                "alumno_completo": "Pérez, Juan",
                "dni": "45123456",
                "estado": "tarde",
                "hora_llegada": "08:15",
                "hora_retiro": None,
                "motivo_retiro": None,
                "registrado_por": "Preceptor Guardia",
            },
            {
                "fecha": "2026-11-12",
                "curso_nombre": "1° 1° - TM",
                "alumno_completo": "González, Sofía",
                "dni": "46987654",
                "estado": "retirado",
                "hora_llegada": None,
                "hora_retiro": "11:30",
                "motivo_retiro": "Cita médica",
                "registrado_por": "Preceptor Guardia",
            },
        ]
        ruta = os.path.join(self.temp_dir.name, "partes_test.csv")
        res = exportar_partes_diarios_a_csv(registros, ruta)
        self.assertTrue(res.ok)
        self.assertTrue(os.path.exists(ruta))

        # Verificar contenido y encoding
        with open(ruta, "r", encoding="utf-8-sig") as f:
            contenido = f.read()

        lineas = contenido.strip().splitlines()
        self.assertGreaterEqual(len(lineas), 3)
        self.assertIn("Fecha;Curso;Alumno;DNI;Estado;Horario;Motivo Retiro;Registrado por", lineas[0])
        self.assertIn("Pérez, Juan", lineas[1])
        self.assertIn("Llegada: 08:15", lineas[1])
        self.assertIn("González, Sofía", lineas[2])
        self.assertIn("Retiro: 11:30", lineas[2])
        self.assertIn("Cita médica", lineas[2])

    def test_exportar_asistencias_catedra_valido(self):
        """Verifica la exportación de asistencias de cátedra."""
        registros = [
            {
                "fecha": "2026-11-12",
                "curso_nombre": "2° 2° - TT",
                "materia_nombre": "Matemática",
                "alumno_completo": "López, Martín",
                "dni": "47111222",
                "estado": "presente",
                "observaciones": "Participó en clase",
                "profesor_completo": "Prof. Ana Rossi",
            }
        ]
        ruta = os.path.join(self.temp_dir.name, "catedra_test.csv")
        res = exportar_asistencias_catedra_a_csv(registros, ruta)
        self.assertTrue(res.ok)
        self.assertTrue(os.path.exists(ruta))

        with open(ruta, "r", encoding="utf-8-sig") as f:
            contenido = f.read()

        lineas = contenido.strip().splitlines()
        self.assertEqual(len(lineas), 2)
        self.assertIn("Fecha;Curso;Materia;Alumno;DNI;Estado;Observaciones;Docente", lineas[0])
        self.assertIn("Matemática", lineas[1])
        self.assertIn("Participó en clase", lineas[1])

    def test_exportar_resumen_global_valido(self):
        """Verifica la exportación del resumen global por curso y fecha."""
        registros = [
            {
                "fecha": "2026-11-19",
                "curso_nombre": "1° A (Mañana)",
                "estado_carga": "Registrado",
                "total_registrados": 25,
                "presentes": 22,
                "ausentes": 2,
                "tardes": 1,
                "retirados": 0,
                "porcentaje_presentismo": 92.0,
                "registrado_por": "Maria Gonzalez",
            }
        ]
        ruta = os.path.join(self.temp_dir.name, "resumen_global.csv")
        res = exportar_resumen_global_a_csv(registros, ruta)
        self.assertTrue(res.ok)
        self.assertTrue(os.path.exists(ruta))

        with open(ruta, "r", encoding="utf-8-sig") as f:
            lineas = f.read().strip().splitlines()

        self.assertEqual(len(lineas), 2)
        self.assertIn(
            "Fecha;Curso;Estado Carga;Total;Presentes;Ausentes;Tardes;Retirados;% Presentismo;Registrado por",
            lineas[0],
        )
        self.assertIn("1° A (Mañana)", lineas[1])
        self.assertIn("92.0%", lineas[1])


class TestAtajosTecladoAsistencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_fila_toma_lista_atajos_teclado(self):
        """Verifica que FilaTomaLista responda a las teclas 1, 2, 3, 4 y notifique navegación."""
        alumno = {"numero": 101, "apellido": "Gómez", "nombre": "Lucas", "dni": "44332211"}
        navegacion_invocada = []

        def on_nav(delta):
            navegacion_invocada.append(delta)

        fila = FilaTomaLista(0, alumno, on_navegar=on_nav)

        # Probar tecla 2 (Ausente)
        evento_2 = QKeyEvent(QEvent.KeyPress, Qt.Key_2, Qt.NoModifier)
        fila.keyPressEvent(evento_2)
        self.assertEqual(fila.estado, "ausente")
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar tecla 3 (Tarde)
        evento_3 = QKeyEvent(QEvent.KeyPress, Qt.Key_3, Qt.NoModifier)
        fila.keyPressEvent(evento_3)
        self.assertEqual(fila.estado, "tarde")
        self.assertIsNotNone(fila.hora_llegada)
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar tecla 4 (Retirado)
        evento_4 = QKeyEvent(QEvent.KeyPress, Qt.Key_4, Qt.NoModifier)
        fila.keyPressEvent(evento_4)
        self.assertEqual(fila.estado, "retirado")
        self.assertIsNotNone(fila.hora_retiro)
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar tecla 1 (Presente)
        evento_1 = QKeyEvent(QEvent.KeyPress, Qt.Key_1, Qt.NoModifier)
        fila.keyPressEvent(evento_1)
        self.assertEqual(fila.estado, "presente")
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar navegación hacia arriba (Up)
        evento_up = QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier)
        fila.keyPressEvent(evento_up)
        self.assertEqual(navegacion_invocada[-1], -1)

    def test_fila_toma_materia_atajos_teclado(self):
        """Verifica que FilaTomaMateria responda a las teclas 1, 2, P, A y flechas."""
        alumno = {"numero": 202, "apellido": "Suárez", "nombre": "Carla", "dni": "45667788"}
        navegacion_invocada = []

        def on_nav(delta):
            navegacion_invocada.append(delta)

        fila = FilaTomaMateria(0, alumno, on_navegar=on_nav)

        # Probar tecla A (Ausente)
        evento_a = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier)
        fila.keyPressEvent(evento_a)
        self.assertEqual(fila.estado, "ausente")
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar tecla P (Presente)
        evento_p = QKeyEvent(QEvent.KeyPress, Qt.Key_P, Qt.NoModifier)
        fila.keyPressEvent(evento_p)
        self.assertEqual(fila.estado, "presente")
        self.assertEqual(navegacion_invocada[-1], 1)

        # Probar flecha Down (Navegar siguiente)
        evento_down = QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier)
        fila.keyPressEvent(evento_down)
        self.assertEqual(navegacion_invocada[-1], 1)
