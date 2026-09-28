"""Vista preliminar read-only de asistencia por alumno."""
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from interfaz.estilos import (
    COLOR_ACENTO,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_input,
    _estilo_tabla,
    _etiqueta,
)
from servicios import alumno as servicio_alumno
from servicios.asistencia import listar_asistencias_de_alumno


class PanelAsistencia(QWidget):
    """Panel preliminar para consultar asistencias de un alumno (solo lectura)."""

    def __init__(self, ciclo_id: int | None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self._armar_ui()
        self._recargar_alumnos()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- Encabezado con badge preliminar ---
        fila_titulo = QHBoxLayout()
        titulo = _etiqueta("Consulta de asistencia", tenue=False)
        titulo.setFont(QFont(FUENTE_MONO, 16, QFont.Bold))
        fila_titulo.addWidget(titulo)

        badge = QLabel("Vista preliminar")
        badge.setStyleSheet(
            f"color: {COLOR_TEXTO}; background-color: {COLOR_ACENTO}; "
            f"border-radius: 8px; padding: 4px 10px;"
        )
        fila_titulo.addWidget(badge)
        fila_titulo.addStretch()
        layout.addLayout(fila_titulo)

        # --- Filtros ---
        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(10)

        fila_filtros.addWidget(_etiqueta("Alumno:", tenue=True))
        self.combo_alumnos = QComboBox()
        self.combo_alumnos.setStyleSheet(_estilo_input())
        fila_filtros.addWidget(self.combo_alumnos, stretch=2)

        fila_filtros.addWidget(_etiqueta("Desde:", tenue=True))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.setStyleSheet(_estilo_input())
        fila_filtros.addWidget(self.date_desde)

        fila_filtros.addWidget(_etiqueta("Hasta:", tenue=True))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setStyleSheet(_estilo_input())
        fila_filtros.addWidget(self.date_hasta)

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setCursor(Qt.PointingHandCursor)
        self.btn_consultar.setStyleSheet(_estilo_boton())
        self.btn_consultar.clicked.connect(self._consultar)
        fila_filtros.addWidget(self.btn_consultar)

        layout.addLayout(fila_filtros)

        # --- Estado vacio / error ---
        self.label_mensaje = QLabel()
        self.label_mensaje.setStyleSheet(
            f"color: {COLOR_TEXTO_TENUE}; padding: 20px 4px;"
        )
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.hide()
        layout.addWidget(self.label_mensaje)

        # --- Tabla de asistencias ---
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Materia", "Estado", "Observaciones"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla, stretch=1)

    def _recargar_alumnos(self):
        self.combo_alumnos.clear()
        self.combo_alumnos.addItem("Selecciona un alumno...", None)

        resultado = servicio_alumno.listar_alumnos(curso_id=None, solo_activos=True)
        if not resultado.ok:
            self._mostrar_mensaje(
                f"Error al cargar alumnos: {resultado.mensaje}", es_error=True
            )
            return

        for alumno in sorted(
            resultado.datos, key=lambda a: (a.get("apellido", ""), a.get("nombre", ""))
        ):
            texto = f"{alumno.get('apellido', '')}, {alumno.get('nombre', '')} ({alumno['numero']})"
            self.combo_alumnos.addItem(texto, alumno["numero"])

        self._mostrar_mensaje(
            "Selecciona un alumno y un rango de fechas para consultar.",
            es_error=False,
        )

    def _consultar(self):
        numero = self.combo_alumnos.currentData()
        if numero is None:
            self.tabla.setRowCount(0)
            self._mostrar_mensaje("Selecciona un alumno para consultar.", es_error=False)
            return

        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        try:
            registros = listar_asistencias_de_alumno(numero, fecha_desde, fecha_hasta)
        except Exception as e:
            self.tabla.setRowCount(0)
            self._mostrar_mensaje(
                f"Error al consultar asistencias: {e}", es_error=True
            )
            return

        self.tabla.setRowCount(len(registros))
        if not registros:
            self._mostrar_mensaje(
                "No hay registros de asistencia para el alumno en el rango seleccionado.",
                es_error=False,
            )
            return

        self.label_mensaje.hide()
        for fila, registro in enumerate(registros):
            valores = [
                registro.get("fecha", "-"),
                registro.get("materia", "-"),
                registro.get("estado", "-"),
                registro.get("observaciones") or "-",
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor)))

    def _mostrar_mensaje(self, mensaje: str, es_error: bool = False):
        color = "#ff5c5c" if es_error else COLOR_TEXTO_TENUE
        self.label_mensaje.setStyleSheet(f"color: {color}; padding: 20px 4px;")
        self.label_mensaje.setText(mensaje)
        self.label_mensaje.show()
