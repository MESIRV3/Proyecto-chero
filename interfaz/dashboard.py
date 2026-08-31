"""Ventana principal: elegir curso, materia y fecha para trabajar."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from servicios.alumno import listar_cursos
from servicios.materia import listar_materias_de_curso

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
    QPushButton:pressed { background-color: #1a1a1e; }
"""


class VentanaPrincipal(QMainWindow):
    def __init__(self, usuario: dict):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("Sistema de Asistencia - Panel principal")
        self.resize(760, 480)
        self.setStyleSheet(ESTILO_VENTANA)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # --- Encabezado ---
        bienvenida = QLabel(
            f"Hola, {usuario['nombre']} {usuario['apellido']}  ·  rol: {usuario['rol']}"
        )
        bienvenida.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        layout.addWidget(bienvenida)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet("color: #2a2a2a;")
        layout.addWidget(linea)

        # --- Selectores ---
        fila_selectores = QHBoxLayout()
        fila_selectores.setSpacing(15)

        bloque_curso = QVBoxLayout()
        bloque_curso.addWidget(QLabel("Curso"))
        self.combo_curso = QComboBox()
        bloque_curso.addWidget(self.combo_curso)
        fila_selectores.addLayout(bloque_curso)

        bloque_materia = QVBoxLayout()
        bloque_materia.addWidget(QLabel("Materia"))
        self.combo_materia = QComboBox()
        bloque_materia.addWidget(self.combo_materia)
        fila_selectores.addLayout(bloque_materia)

        bloque_fecha = QVBoxLayout()
        bloque_fecha.addWidget(QLabel("Fecha"))
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDate(QDate.currentDate())
        bloque_fecha.addWidget(self.fecha)
        fila_selectores.addLayout(bloque_fecha)

        layout.addLayout(fila_selectores)

        self.combo_curso.currentIndexChanged.connect(self._cargar_materias)

        # --- Acciones ---
        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(15)

        btn_tomar = QPushButton("Tomar asistencia")
        btn_tomar.setCursor(Qt.PointingHandCursor)
        btn_tomar.clicked.connect(self._abrir_tomar_asistencia)
        fila_acciones.addWidget(btn_tomar)

        btn_historial = QPushButton("Ver historial")
        btn_historial.setCursor(Qt.PointingHandCursor)
        btn_historial.clicked.connect(self._abrir_historial)
        fila_acciones.addWidget(btn_historial)

        layout.addLayout(fila_acciones)
        layout.addStretch()

        # Se guardan referencias a las ventanas hijas para que Python
        # no las destruya por falta de referencias (garbage collection)
        self.ventana_asistencia = None
        self.ventana_historial = None

        self._cargar_cursos()

    def _cargar_cursos(self):
        self.cursos = listar_cursos()
        self.combo_curso.clear()
        for curso in self.cursos:
            etiqueta = f"{curso['anio']}\u00b0 \"{curso['division']}\" - {curso['turno']}"
            self.combo_curso.addItem(etiqueta, curso["id"])
        self._cargar_materias()

    def _cargar_materias(self):
        curso_id = self.combo_curso.currentData()
        self.combo_materia.clear()
        if curso_id is None:
            return
        materias = listar_materias_de_curso(curso_id)
        for materia in materias:
            self.combo_materia.addItem(materia["nombre"], materia["id"])

    def _abrir_tomar_asistencia(self):
        curso_id = self.combo_curso.currentData()
        materia_id = self.combo_materia.currentData()
        if curso_id is None or materia_id is None:
            QMessageBox.warning(self, "Faltan datos", "Elegi un curso y una materia")
            return
        fecha_str = self.fecha.date().toString("yyyy-MM-dd")

        from interfaz.tomar_asistencia import VentanaTomarAsistencia
        self.ventana_asistencia = VentanaTomarAsistencia(
            usuario=self.usuario,
            curso_id=curso_id,
            materia_id=materia_id,
            fecha=fecha_str,
            nombre_curso=self.combo_curso.currentText(),
            nombre_materia=self.combo_materia.currentText(),
        )
        self.ventana_asistencia.show()

    def _abrir_historial(self):
        curso_id = self.combo_curso.currentData()
        if curso_id is None:
            QMessageBox.warning(self, "Faltan datos", "Elegi un curso")
            return

        from interfaz.historial import VentanaHistorial
        self.ventana_historial = VentanaHistorial(curso_id=curso_id)
        self.ventana_historial.show()