"""Ventana para consultar historial y porcentaje de asistencia de un alumno."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from servicios.alumno import listar_alumnos_de_curso
from servicios.materia import listar_materias_de_curso
from servicios.asistencia import listar_asistencias_de_alumno, calcular_porcentaje_asistencia

FUENTE_MONO = "Courier New"

ESTILO_VENTANA = """
    QMainWindow { background-color: #141414; }
    QLabel { color: #dddddd; }
    QComboBox, QDateEdit {
        background-color: #0f0f0f;
        border: 1px solid #1f1f1f;
        border-radius: 8px;
        color: white;
        padding: 8px 10px;
        min-height: 28px;
    }
    QComboBox QAbstractItemView {
        background-color: #0f0f0f;
        color: white;
        selection-background-color: #2e2e33;
    }
    QPushButton {
        background-color: #242429;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 16px;
    }
    QPushButton:hover { background-color: #2e2e33; }
    QTableWidget {
        background-color: #0f0f0f;
        color: #dddddd;
        gridline-color: #1f1f1f;
        border: 1px solid #1f1f1f;
    }
    QHeaderView::section {
        background-color: #1a1a1a;
        color: #dddddd;
        padding: 6px;
        border: none;
    }
"""


class VentanaHistorial(QMainWindow):
    def __init__(self, curso_id: int):
        super().__init__()
        self.curso_id = curso_id

        self.setWindowTitle("Historial de asistencia")
        self.resize(700, 560)
        self.setStyleSheet(ESTILO_VENTANA)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        titulo = QLabel("Historial de asistencia")
        titulo.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        layout.addWidget(titulo)

        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(10)

        self.combo_alumno = QComboBox()
        fila_filtros.addWidget(QLabel("Alumno"))
        fila_filtros.addWidget(self.combo_alumno)

        self.combo_materia = QComboBox()
        fila_filtros.addWidget(QLabel("Materia (%)"))
        fila_filtros.addWidget(self.combo_materia)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        fila_filtros.addWidget(QLabel("Desde"))
        fila_filtros.addWidget(self.fecha_desde)

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(QDate.currentDate())
        fila_filtros.addWidget(QLabel("Hasta"))
        fila_filtros.addWidget(self.fecha_hasta)

        layout.addLayout(fila_filtros)

        btn_consultar = QPushButton("Consultar")
        btn_consultar.setCursor(Qt.PointingHandCursor)
        btn_consultar.clicked.connect(self._consultar)
        layout.addWidget(btn_consultar)

        self.label_porcentaje = QLabel("")
        self.label_porcentaje.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        layout.addWidget(self.label_porcentaje)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Materia", "Estado", "Observaciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla)

        self._cargar_alumnos()
        self._cargar_materias()

    def _cargar_alumnos(self):
        alumnos = listar_alumnos_de_curso(self.curso_id)
        self.combo_alumno.clear()
        for alumno in alumnos:
            etiqueta = f"{alumno['apellido']}, {alumno['nombre']} (N\u00b0 {alumno['numero']})"
            self.combo_alumno.addItem(etiqueta, alumno["numero"])

    def _cargar_materias(self):
        materias = listar_materias_de_curso(self.curso_id)
        self.combo_materia.clear()
        for materia in materias:
            self.combo_materia.addItem(materia["nombre"], materia["id"])

    def _consultar(self):
        alumno_numero = self.combo_alumno.currentData()
        materia_id = self.combo_materia.currentData()
        if alumno_numero is None:
            QMessageBox.warning(self, "Faltan datos", "Elegi un alumno")
            return

        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")

        if materia_id is not None:
            porcentaje = calcular_porcentaje_asistencia(alumno_numero, materia_id, desde, hasta)
            self.label_porcentaje.setText(
                f"Asistencia en {self.combo_materia.currentText()}: {porcentaje}%"
            )

        registros = listar_asistencias_de_alumno(alumno_numero, desde, hasta)
        self.tabla.setRowCount(len(registros))
        for fila_idx, registro in enumerate(registros):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(registro["fecha"]))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(registro["materia"]))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(registro["estado"]))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(registro["observaciones"] or ""))