"""Panel HUB (Inicio) con metricas del ciclo y accesos rapidos."""
from datetime import date, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
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
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_tabla,
    _etiqueta,
    _tarjeta,
)
from servicios import curso as servicio_curso
from servicios.dashboard import obtener_metricas_hub


class PanelHub(QWidget):
    """Vista de inicio: bienvenida, KPIs, accesos rapidos y resumen de cursos."""

    navegar_a_alumnos = Signal()
    navegar_a_cursos = Signal()

    def __init__(self, ciclo_id: int | None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self._anio_ciclo = date.today().year
        self._armar_ui()
        self._actualizar_banner()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Mensaje de error inline (no modal)
        self.label_error = QLabel()
        self.label_error.setStyleSheet(f"color: #ff5c5c; padding: 8px 4px;")
        self.label_error.hide()
        layout.addWidget(self.label_error)

        # --- Banner de bienvenida ---
        banner = _tarjeta()
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(4)

        self.label_saludo = _etiqueta("", tenue=False)
        self.label_saludo.setFont(QFont(FUENTE_MONO, 18, QFont.Bold))
        banner_layout.addWidget(self.label_saludo)

        self.label_ciclo = _etiqueta("", tenue=True)
        banner_layout.addWidget(self.label_ciclo)

        layout.addWidget(banner)

        # --- Accesos rapidos ---
        fila_acciones = QHBoxLayout()
        self.btn_agregar_alumno = QPushButton("+ Agregar Alumno")
        self.btn_agregar_alumno.setCursor(Qt.PointingHandCursor)
        self.btn_agregar_alumno.setStyleSheet(_estilo_boton())
        self.btn_agregar_alumno.clicked.connect(self.navegar_a_alumnos.emit)
        fila_acciones.addWidget(self.btn_agregar_alumno)

        self.btn_crear_curso = QPushButton("+ Crear Curso")
        self.btn_crear_curso.setCursor(Qt.PointingHandCursor)
        self.btn_crear_curso.setStyleSheet(_estilo_boton())
        self.btn_crear_curso.clicked.connect(self.navegar_a_cursos.emit)
        fila_acciones.addWidget(self.btn_crear_curso)
        fila_acciones.addStretch()
        layout.addLayout(fila_acciones)

        # --- KPIs ---
        self.grid_kpi = QGridLayout()
        self.grid_kpi.setSpacing(12)

        self.kpi_cards = {}
        kpi_defs = [
            ("👥 Alumnos Activos", "alumnos_activos"),
            ("🏫 Cursos Registrados", "total_cursos"),
            ("📝 Asistencias hoy", "asistencias_hoy"),
            ("📝 Asistencias semana", "asistencias_semana"),
            ("⚠️ Alumnos de baja", "alumnos_baja"),
        ]
        for idx, (titulo, clave) in enumerate(kpi_defs):
            card = self._crear_tarjeta_kpi(titulo)
            self.kpi_cards[clave] = card
            self.grid_kpi.addWidget(card, idx // 3, idx % 3)
        layout.addLayout(self.grid_kpi)

        # --- Tabla resumen de cursos ---
        self.tabla_cursos = QTableWidget(0, 4)
        self.tabla_cursos.setHorizontalHeaderLabels(
            ["Curso", "Especialidad", "Turno", "Alumnos"]
        )
        self.tabla_cursos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_cursos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_cursos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_cursos.setAlternatingRowColors(True)
        self.tabla_cursos.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla_cursos, stretch=1)

    def _crear_tarjeta_kpi(self, titulo: str):
        card = _tarjeta()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        lbl_titulo = _etiqueta(titulo, tenue=True)
        lbl_titulo.setWordWrap(True)
        layout.addWidget(lbl_titulo)

        lbl_valor = _etiqueta("—", tenue=False)
        lbl_valor.setFont(QFont(FUENTE_MONO, 24, QFont.Bold))
        lbl_valor.setStyleSheet(f"color: {COLOR_TEXTO};")
        layout.addWidget(lbl_valor)

        card.valor_label = lbl_valor
        return card

    def showEvent(self, event):
        super().showEvent(event)
        self._cargar_datos()

    def _cargar_datos(self):
        self.label_error.hide()
        self._cargar_kpi()
        self._cargar_tabla_cursos()

    def _saludo_por_hora(self) -> str:
        hora = datetime.now().hour
        if hora < 12:
            return "Buen día"
        if hora < 20:
            return "Buenas tardes"
        return "Buenas noches"

    def _actualizar_banner(self):
        self.label_saludo.setText(
            f"{self._saludo_por_hora()}, bienvenido al panel de administración"
        )
        self.label_ciclo.setText(f"Ciclo lectivo activo: {self._anio_ciclo}")

    def _cargar_kpi(self):
        resultado = obtener_metricas_hub(self.ciclo_id)
        if not resultado.ok:
            self._mostrar_error(resultado.mensaje)
            for card in self.kpi_cards.values():
                card.valor_label.setText("—")
            return

        datos = resultado.datos
        self._anio_ciclo = datos.get("ciclo_anio", self._anio_ciclo)
        for clave, card in self.kpi_cards.items():
            card.valor_label.setText(str(datos.get(clave, 0)))
        self._actualizar_banner()

    def _cargar_tabla_cursos(self):
        resultado = servicio_curso.listar_cursos(self.ciclo_id)
        if not resultado.ok:
            self._mostrar_error(resultado.mensaje)
            self.tabla_cursos.setRowCount(0)
            return

        cursos = resultado.datos
        self.tabla_cursos.setRowCount(len(cursos))
        for fila, curso in enumerate(cursos):
            nombre = servicio_curso.obtener_nombre_curso(curso)
            especialidad = curso.get("especialidad") or "-"
            valores = [
                nombre,
                especialidad,
                curso.get("turno", "-"),
                str(curso.get("cantidad_alumnos", 0)),
            ]
            for col, valor in enumerate(valores):
                self.tabla_cursos.setItem(fila, col, QTableWidgetItem(str(valor)))

    def _mostrar_error(self, mensaje: str):
        self.label_error.setText(f"Error al cargar datos: {mensaje}")
        self.label_error.show()
