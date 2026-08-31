"""Ventana para tomar asistencia de un curso/materia/fecha."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from servicios.asistencia import listar_asistencia_de_curso, registrar_asistencia

FUENTE_MONO = "Courier New"

ESTILO_VENTANA = """
    QMainWindow { background-color: #141414; }
    QLabel { color: #dddddd; }
    QScrollArea { border: none; }
    QFrame#fila {
        background-color: #1a1a1a;
        border-radius: 10px;
    }
    QRadioButton { color: #cccccc; padding: 4px 10px; }
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


class VentanaTomarAsistencia(QMainWindow):
    def __init__(self, usuario, curso_id, materia_id, fecha, nombre_curso, nombre_materia):
        super().__init__()
        self.usuario = usuario
        self.curso_id = curso_id
        self.materia_id = materia_id
        self.fecha = fecha
        self.filas = []  # lista de (numero, radio_presente, radio_ausente)

        self.setWindowTitle(f"Asistencia - {nombre_materia} - {fecha}")
        self.resize(600, 620)
        self.setStyleSheet(ESTILO_VENTANA)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        titulo = QLabel(f"{nombre_curso} \u00b7 {nombre_materia} \u00b7 {fecha}")
        titulo.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        layout.addWidget(titulo)

        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        contenedor = QWidget()
        self.layout_lista = QVBoxLayout(contenedor)
        self.layout_lista.setSpacing(8)
        self.area.setWidget(contenedor)
        layout.addWidget(self.area)

        btn_guardar = QPushButton("Guardar asistencia")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.clicked.connect(self._guardar)
        layout.addWidget(btn_guardar)

        self._cargar_alumnos()

    def _cargar_alumnos(self):
        alumnos = listar_asistencia_de_curso(self.curso_id, self.materia_id, self.fecha)

        if not alumnos:
            self.layout_lista.addWidget(QLabel("No hay alumnos activos en este curso."))
            return

        for alumno in alumnos:
            fila = QFrame()
            fila.setObjectName("fila")
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(15, 10, 15, 10)

            nombre = QLabel(f"{alumno['apellido']}, {alumno['nombre']}  (N\u00b0 {alumno['numero']})")
            nombre.setFont(QFont(FUENTE_MONO, 11))
            fila_layout.addWidget(nombre)
            fila_layout.addStretch()

            grupo = QButtonGroup(fila)
            rb_presente = QRadioButton("Presente")
            rb_ausente = QRadioButton("Ausente")
            grupo.addButton(rb_presente)
            grupo.addButton(rb_ausente)

            # Si ya habia asistencia cargada ese dia, respeta ese estado.
            # Si no, arranca en "Presente" por defecto.
            estado_actual = alumno.get("estado")
            if estado_actual == "ausente":
                rb_ausente.setChecked(True)
            else:
                rb_presente.setChecked(True)

            fila_layout.addWidget(rb_presente)
            fila_layout.addWidget(rb_ausente)

            self.layout_lista.addWidget(fila)
            self.filas.append((alumno["numero"], rb_presente, rb_ausente))

        self.layout_lista.addStretch()

    def _guardar(self):
        errores = []
        for numero, rb_presente, _rb_ausente in self.filas:
            estado = "presente" if rb_presente.isChecked() else "ausente"
            resultado = registrar_asistencia(
                alumno_numero=numero,
                materia_id=self.materia_id,
                fecha=self.fecha,
                estado=estado,
                profesor_id=self.usuario["id"],
            )
            if not resultado.ok:
                errores.append(f"N\u00b0 {numero}: {resultado.mensaje}")

        if errores:
            QMessageBox.critical(self, "Errores al guardar", "\n".join(errores))
        else:
            QMessageBox.information(self, "Listo", "Asistencia guardada correctamente")