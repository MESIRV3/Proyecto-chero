import pathlib

hub_py = r'''"""Panel HUB (Dashboard) de administracion.

Muestra las metricas clave del ciclo lectivo activo y accesos rapidos
a las secciones principales. No contiene logica de negocio; delega en
servicios/dashboard.py para obtener los datos.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

FUENTE_MONO = "Courier New"

COLOR_FONDO = "#0b0b0d"
COLOR_TARJETA = "rgba(255, 255, 255, 0.04)"
COLOR_BORDE = "rgba(255, 255, 255, 0.08)"
COLOR_TEXTO = "#ffffff"
COLOR_TENUE = "#888888"
COLOR_ACENTO = "#2e2e33"
COLOR_ACENTO_HOVER = "#3a3a40"
COLOR_VERDE = "#1e4d30"
COLOR_VERDE_HOVER = "#265c39"
COLOR_PELIGRO = "#4d1e1e"


def _tarjeta_kpi(emoji: str, titulo: str, valor: str, color_fondo: str = COLOR_TARJETA) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {color_fondo};
            border-radius: 16px;
            border: 1px solid {COLOR_BORDE};
        }}
    """)
    frame.setMinimumHeight(110)
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(6)

    lbl_emoji = QLabel(emoji)
    lbl_emoji.setFont(QFont(FUENTE_MONO, 22))
    lbl_emoji.setStyleSheet("color: white; background: transparent; border: none;")

    lbl_valor = QLabel(valor)
    lbl_valor.setFont(QFont(FUENTE_MONO, 28, QFont.Bold))
    lbl_valor.setStyleSheet("color: white; background: transparent; border: none;")
    lbl_valor.setObjectName("kpi_valor")

    lbl_titulo = QLabel(titulo)
    lbl_titulo.setFont(QFont(FUENTE_MONO, 10))
    lbl_titulo.setStyleSheet(f"color: {COLOR_TENUE}; background: transparent; border: none;")
    lbl_titulo.setWordWrap(True)

    layout.addWidget(lbl_emoji)
    layout.addWidget(lbl_valor)
    layout.addWidget(lbl_titulo)

    return frame


def _boton_acceso(texto: str, color=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER) -> QPushButton:
    btn = QPushButton(texto)
    btn.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
    btn.setMinimumHeight(44)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
        }}
        QPushButton:hover {{ background-color: {color_hover}; }}
        QPushButton:pressed {{ background-color: #1a1a1e; }}
    """)
    return btn


class PanelHub(QWidget):
    """Dashboard principal: metricas, bienvenida y accesos rapidos."""

    def __init__(self, ciclo_id: int, on_ir_alumnos=None, on_ir_cursos=None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.on_ir_alumnos = on_ir_alumnos
        self.on_ir_cursos = on_ir_cursos

        self.setStyleSheet(f"background-color: {COLOR_FONDO};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        self._layout_contenido = QVBoxLayout(contenido)
        self._layout_contenido.setContentsMargins(32, 28, 32, 32)
        self._layout_contenido.setSpacing(24)

        self._armar_bienvenida()
        self._armar_kpis()
        self._armar_accesos_rapidos()

        scroll.setWidget(contenido)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(scroll)

        # Refresco automatico cada 60 segundos
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.actualizar)
        self._timer.start(60_000)

    def _armar_bienvenida(self):
        from datetime import date
        anio = date.today().year

        lbl_titulo = QLabel(f"Panel de Administracion  |  Ciclo Lectivo {anio}")
        lbl_titulo.setFont(QFont(FUENTE_MONO, 18, QFont.Bold))
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")

        lbl_sub = QLabel("Resumen general del sistema de asistencia escolar")
        lbl_sub.setFont(QFont(FUENTE_MONO, 11))
        lbl_sub.setStyleSheet(f"color: {COLOR_TENUE}; background: transparent; border: none;")

        self._layout_contenido.addWidget(lbl_titulo)
        self._layout_contenido.addWidget(lbl_sub)

    def _armar_kpis(self):
        self._kpi_alumnos_activos = _tarjeta_kpi("👥", "Alumnos activos", "...", "rgba(30,80,50,0.35)")
        self._kpi_alumnos_baja = _tarjeta_kpi("⚠️", "Dados de baja", "...", "rgba(80,30,30,0.35)")
        self._kpi_cursos = _tarjeta_kpi("🏫", "Cursos registrados", "...", "rgba(30,50,80,0.35)")
        self._kpi_hoy = _tarjeta_kpi("📝", "Asistencias hoy", "...", COLOR_TARJETA)
        self._kpi_semana = _tarjeta_kpi("📅", "Asistencias (7 dias)", "...", COLOR_TARJETA)

        grilla = QGridLayout()
        grilla.setSpacing(14)
        grilla.addWidget(self._kpi_alumnos_activos, 0, 0)
        grilla.addWidget(self._kpi_alumnos_baja, 0, 1)
        grilla.addWidget(self._kpi_cursos, 0, 2)
        grilla.addWidget(self._kpi_hoy, 1, 0)
        grilla.addWidget(self._kpi_semana, 1, 1)

        self._layout_contenido.addLayout(grilla)
        self.actualizar()

    def _armar_accesos_rapidos(self):
        lbl = QLabel("Accesos rapidos")
        lbl.setFont(QFont(FUENTE_MONO, 13, QFont.Bold))
        lbl.setStyleSheet(f"color: {COLOR_TENUE}; background: transparent; border: none;")
        self._layout_contenido.addWidget(lbl)

        fila = QHBoxLayout()
        fila.setSpacing(12)

        btn_alumno = _boton_acceso("+ Agregar alumno", COLOR_VERDE, COLOR_VERDE_HOVER)
        btn_alumno.clicked.connect(lambda: self.on_ir_alumnos and self.on_ir_alumnos(abrir_alta=True))

        btn_curso = _boton_acceso("+ Crear curso")
        btn_curso.clicked.connect(lambda: self.on_ir_cursos and self.on_ir_cursos(abrir_alta=True))

        btn_alumnos = _boton_acceso("Ver alumnos")
        btn_alumnos.clicked.connect(lambda: self.on_ir_alumnos and self.on_ir_alumnos())

        btn_cursos = _boton_acceso("Ver cursos")
        btn_cursos.clicked.connect(lambda: self.on_ir_cursos and self.on_ir_cursos())

        fila.addWidget(btn_alumno)
        fila.addWidget(btn_curso)
        fila.addWidget(btn_alumnos)
        fila.addWidget(btn_cursos)
        fila.addStretch()

        self._layout_contenido.addLayout(fila)

    def actualizar(self):
        """Recarga las metricas desde la base de datos."""
        from servicios.dashboard import obtener_metricas_hub
        resultado = obtener_metricas_hub(self.ciclo_id)
        if not resultado.ok:
            return
        d = resultado.datos

        def _set_valor(tarjeta: QFrame, valor: str):
            for lbl in tarjeta.findChildren(QLabel):
                if lbl.objectName() == "kpi_valor":
                    lbl.setText(valor)
                    break

        _set_valor(self._kpi_alumnos_activos, str(d["alumnos_activos"]))
        _set_valor(self._kpi_alumnos_baja, str(d["alumnos_baja"]))
        _set_valor(self._kpi_cursos, str(d["total_cursos"]))
        _set_valor(self._kpi_hoy, str(d["asistencias_hoy"]))
        _set_valor(self._kpi_semana, str(d["asistencias_semana"]))
'''

pathlib.Path('interfaz/hub.py').write_text(hub_py, encoding='utf-8')
print('OK - hub.py', len(hub_py))

