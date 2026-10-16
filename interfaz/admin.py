"""
Panel de Administrador (super usuario).

Permite gestionar cursos (anio + division + especialidad + turno) y
alumnos (alta, baja, reactivar, cambiar de curso). Pensado para el rol
'admin' o 'directivo' de la tabla usuario.

Como abrirlo desde login.py, despues de un login exitoso:

    resultado = autenticar(username, password)
    if resultado.ok:
        usuario = resultado.datos
        if usuario["rol"] in ("admin", "directivo"):
            from interfaz.admin import VentanaAdmin
            self.ventana_admin = VentanaAdmin()
            self.ventana_admin.show()
        self.close()
"""
import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QStackedWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QCheckBox,
    QAbstractItemView, QButtonGroup, QTabWidget, QGridLayout, QScrollArea, QDateEdit
)
from PySide6.QtCore import Qt, QPoint, QSize, QRegularExpression, QDate, QTime
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator

from servicios import curso as servicio_curso
from servicios import alumno as servicio_alumno
from servicios import ciclo_lectivo as servicio_ciclo
from servicios import lista_diaria as servicio_lista_diaria

from interfaz.estilos import (
    FUENTE_MONO,
    COLOR_FONDO,
    COLOR_BORDE,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_TARJETA,
    COLOR_INPUT,
    COLOR_ACENTO,
    COLOR_ACENTO_HOVER,
    _estilo_input,
    _estilo_boton,
    _estilo_tabla,
    _tarjeta,
    _etiqueta,
)

from interfaz.hub import PanelHub
from interfaz.asistencia_preview import PanelAsistencia


def resource_path(relative_path):
    """Devuelve la ruta de un recurso, tanto en desarrollo como en PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent.parent
    return str(base_path / relative_path)


# RUTAS DE ASSETS (iconos de control de ventana compartidos)
ASSETS_PATH = resource_path(os.path.join("assets", "login"))
ICONO_MINIMIZAR = os.path.join(ASSETS_PATH, "minimize.png")
ICONO_MAXIMIZAR = os.path.join(ASSETS_PATH, "maximize.png")
ICONO_CERRAR = os.path.join(ASSETS_PATH, "close.png")

# Paises de America con la cantidad maxima de digitos de su documento
# de identidad nacional. OJO: son valores aproximados/orientativos (no
# saque esto de una fuente oficial pais por pais) pensados para que el
# campo DNI no te deje escribir de mas segun la nacionalidad elegida.
# Si para algun pais en particular sabes el numero exacto, cambialo aca
# nomas, es el unico lugar donde estan definidos.
NACIONALIDADES = {
    "Antigua y Barbuda": 9,
    "Argentina": 8,
    "Bahamas": 9,
    "Barbados": 9,
    "Belice": 9,
    "Bolivia": 8,
    "Brasil": 11,
    "Canadá": 9,
    "Chile": 9,
    "Colombia": 10,
    "Costa Rica": 9,
    "Cuba": 11,
    "Dominica": 9,
    "Ecuador": 10,
    "El Salvador": 9,
    "Estados Unidos": 9,
    "Granada": 9,
    "Guatemala": 13,
    "Guyana": 9,
    "Haití": 9,
    "Honduras": 13,
    "Jamaica": 9,
    "México": 18,
    "Nicaragua": 14,
    "Panamá": 9,
    "Paraguay": 8,
    "Perú": 8,
    "República Dominicana": 11,
    "San Cristóbal y Nieves": 9,
    "San Vicente y las Granadinas": 9,
    "Santa Lucía": 9,
    "Surinam": 9,
    "Trinidad y Tobago": 9,
    "Uruguay": 8,
    "Venezuela": 8,
}


def _validador_solo_letras() -> QRegularExpressionValidator:
    """Letras (con acentos y ñ) y espacios, para nombre/apellido."""
    return QRegularExpressionValidator(QRegularExpression(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]*$"))


def _validador_solo_numeros() -> QRegularExpressionValidator:
    """Solo digitos, para DNI y numero de legajo."""
    return QRegularExpressionValidator(QRegularExpression(r"^[0-9]*$"))


def _validador_division() -> QRegularExpressionValidator:
    """Un solo digito del 1 al 9 (o vacio mientras se esta escribiendo)."""
    return QRegularExpressionValidator(QRegularExpression(r"^[1-9]?$"))


class FilaAlumnoMinimalista(QFrame):
    """Fila minimalista para la lista de alumnos (usada en detalle de curso y en panel alumnos)."""

    def __init__(self, index: int, alumno: dict, curso_texto: str = "", on_click=None):
        super().__init__()
        self.alumno = alumno
        self.on_click = on_click
        self.seleccionada = False
        self.setCursor(Qt.PointingHandCursor if on_click else Qt.ArrowCursor)

        self.texto_busqueda = f"{alumno['numero']} {alumno['apellido']} {alumno['nombre']} {alumno.get('dni') or ''} {curso_texto}".lower()

        self.setFixedHeight(50)
        self._actualizar_estilo()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        # 1. Badge Legajo
        lbl_legajo = QLabel(f"#{alumno['numero']}")
        lbl_legajo.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
        lbl_legajo.setStyleSheet(f"""
            color: {COLOR_TEXTO_TENUE};
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 4px 8px;
        """)
        layout.addWidget(lbl_legajo)

        # 2. Nombre y Apellido
        nombre_completo = f"{alumno['apellido'].upper()}, {alumno['nombre']}"
        lbl_nombre = QLabel(nombre_completo)
        lbl_nombre.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_nombre.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout.addWidget(lbl_nombre, stretch=1)

        # 3. Badge Curso (opcional, util cuando se listan alumnos de todos los cursos)
        if curso_texto:
            lbl_curso = QLabel(curso_texto)
            lbl_curso.setFont(QFont(FUENTE_MONO, 9, QFont.Bold))
            lbl_curso.setStyleSheet(f"""
                color: {COLOR_TEXTO_TENUE};
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid {COLOR_BORDE};
                border-radius: 6px;
                padding: 3px 8px;
            """)
            layout.addWidget(lbl_curso)

        # 4. DNI
        dni = alumno.get("dni")
        if dni:
            try:
                dni_fmt = f"{int(dni):,}".replace(",", ".")
            except ValueError:
                dni_fmt = str(dni)
            txt_dni = f"DNI {dni_fmt}"
        else:
            txt_dni = "DNI —"
        lbl_dni = QLabel(txt_dni)
        lbl_dni.setFont(QFont(FUENTE_MONO, 10))
        lbl_dni.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        layout.addWidget(lbl_dni)

        # 5. Nacionalidad con bandera
        nac = alumno.get("nacionalidad") or "Argentina"
        banderas = {
            "Argentina": "🇦🇷", "Bolivia": "🇧🇴", "Brasil": "🇧🇷",
            "Chile": "🇨🇱", "Colombia": "🇨🇴", "Paraguay": "🇵🇾",
            "Perú": "🇵🇪", "Uruguay": "🇺🇾", "Venezuela": "🇻🇪",
        }
        bandera = banderas.get(nac, "🌐")
        lbl_nac = QLabel(f"{bandera} {nac}")
        lbl_nac.setFont(QFont(FUENTE_MONO, 10))
        lbl_nac.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        layout.addWidget(lbl_nac)

        # 6. Pill de estado
        activo = bool(alumno.get("activo", 1))
        lbl_estado = QLabel("● Activo" if activo else "● De baja")
        lbl_estado.setFont(QFont(FUENTE_MONO, 9, QFont.Bold))
        if activo:
            lbl_estado.setStyleSheet("""
                color: #4ade80;
                background-color: rgba(74, 222, 128, 0.08);
                border: 1px solid rgba(74, 222, 128, 0.2);
                border-radius: 10px;
                padding: 3px 10px;
            """)
        else:
            lbl_estado.setStyleSheet("""
                color: #f87171;
                background-color: rgba(248, 113, 113, 0.08);
                border: 1px solid rgba(248, 113, 113, 0.2);
                border-radius: 10px;
                padding: 3px 10px;
            """)
        layout.addWidget(lbl_estado)

    def _actualizar_estilo(self):
        if self.seleccionada:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.09);
                    border: 1px solid #7a7a85;
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background-color: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                }}
            """)

    def set_seleccionada(self, valor: bool):
        self.seleccionada = valor
        self._actualizar_estilo()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.on_click:
            self.on_click(self)
        super().mousePressEvent(event)


class FilaTomaLista(QFrame):
    """Fila para registrar asistencia de un alumno en la toma de lista diaria."""

    def __init__(self, index: int, alumno: dict, on_cambio=None):
        super().__init__()
        self.alumno = alumno
        self.on_cambio = on_cambio

        self.estado = alumno.get("estado") or "presente"
        self.hora_llegada = alumno.get("hora_llegada")
        self.hora_retiro = alumno.get("hora_retiro")
        self.motivo_retiro = alumno.get("motivo_retiro")

        self.texto_busqueda = f"{alumno['numero']} {alumno['apellido']} {alumno['nombre']} {alumno.get('dni') or ''}".lower()

        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.10);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        lbl_legajo = QLabel(f"#{alumno['numero']}")
        lbl_legajo.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
        lbl_legajo.setStyleSheet(f"""
            color: {COLOR_TEXTO_TENUE};
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 4px 8px;
        """)
        layout.addWidget(lbl_legajo)

        nombre_completo = f"{alumno['apellido'].upper()}, {alumno['nombre']}"
        lbl_nombre = QLabel(nombre_completo)
        lbl_nombre.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_nombre.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout.addWidget(lbl_nombre, stretch=1)

        dni = alumno.get("dni")
        if dni:
            try:
                dni_fmt = f"{int(dni):,}".replace(",", ".")
            except ValueError:
                dni_fmt = str(dni)
            txt_dni = f"DNI {dni_fmt}"
        else:
            txt_dni = "DNI —"
        lbl_dni = QLabel(txt_dni)
        lbl_dni.setFont(QFont(FUENTE_MONO, 10))
        lbl_dni.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        layout.addWidget(lbl_dni)

        self.lbl_hora_extra = QLabel("")
        self.lbl_hora_extra.setFont(QFont(FUENTE_MONO, 9, QFont.Bold))
        self.lbl_hora_extra.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 3px 8px;
        """)
        self.lbl_hora_extra.hide()
        layout.addWidget(self.lbl_hora_extra)

        self.btns = {}
        for est, label, color_bg, color_border, color_txt in [
            ("presente", "Presente", "rgba(74, 222, 128, 0.15)", "#4ade80", "#4ade80"),
            ("ausente", "Ausente", "rgba(248, 113, 113, 0.15)", "#f87171", "#f87171"),
            ("tarde", "Tarde", "rgba(251, 191, 36, 0.15)", "#fbbf24", "#fbbf24"),
            ("retirado", "Retirado", "rgba(96, 165, 250, 0.15)", "#60a5fa", "#60a5fa"),
        ]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont(FUENTE_MONO, 9, QFont.Bold))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, e=est: self.set_estado(e))
            self.btns[est] = {
                "widget": btn,
                "color_bg": color_bg,
                "color_border": color_border,
                "color_txt": color_txt,
            }
            layout.addWidget(btn)

        self._actualizar_botones()

    def set_estado(self, nuevo_estado: str):
        hora_ahora = QTime.currentTime().toString("HH:mm")
        if nuevo_estado == "tarde" and not self.hora_llegada:
            self.hora_llegada = hora_ahora
        elif nuevo_estado == "retirado" and not self.hora_retiro:
            self.hora_retiro = hora_ahora

        self.estado = nuevo_estado
        self._actualizar_botones()
        if self.on_cambio:
            self.on_cambio()

    def _actualizar_botones(self):
        for est, cfg in self.btns.items():
            btn = cfg["widget"]
            if est == self.estado:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {cfg['color_bg']};
                        border: 1px solid {cfg['color_border']};
                        color: {cfg['color_txt']};
                        border-radius: 6px;
                        padding: 4px 10px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        color: {COLOR_TEXTO_TENUE};
                        border-radius: 6px;
                        padding: 4px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(255, 255, 255, 0.07);
                        color: {COLOR_TEXTO};
                    }}
                """)

        if self.estado == "tarde" and self.hora_llegada:
            self.lbl_hora_extra.setText(f"🕒 {self.hora_llegada}")
            self.lbl_hora_extra.show()
        elif self.estado == "retirado" and self.hora_retiro:
            self.lbl_hora_extra.setText(f"🚪 {self.hora_retiro}")
            self.lbl_hora_extra.show()
        else:
            self.lbl_hora_extra.hide()

    def obtener_registro(self) -> dict:
        return {
            "alumno_numero": self.alumno["numero"],
            "estado": self.estado,
            "hora_llegada": self.hora_llegada if self.estado == "tarde" else None,
            "hora_retiro": self.hora_retiro if self.estado == "retirado" else None,
            "motivo_retiro": self.motivo_retiro if self.estado == "retirado" else None,
        }


class TarjetaCurso(QFrame):
    def __init__(self, curso, ciclo_anio, on_click):
        super().__init__()
        self.curso = curso
        self.on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_TARJETA};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDE};
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        titulo = f"{curso['anio']}°{curso['division']} Ciclo {ciclo_anio}"
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXTO}; border: none; background: transparent;")
        
        lbl_alumnos = QLabel(f"👥 {curso['cantidad_alumnos']} Alumnos Activos")
        lbl_alumnos.setFont(QFont(FUENTE_MONO, 11))
        lbl_alumnos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; border: none; background: transparent;")

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_alumnos)
        
        if curso.get('especialidad'):
            lbl_esp = QLabel(f"📚 {curso['especialidad']}")
            lbl_esp.setFont(QFont(FUENTE_MONO, 10))
            lbl_esp.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; border: none; background: transparent;")
            layout.addWidget(lbl_esp)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click(self.curso)
        super().mousePressEvent(event)


class PanelCursos(QWidget):
    """Alta, listado y detalle de cursos con toma de lista diaria integrada."""

    def __init__(self, ciclo_id: int, usuario_id: int = 1, on_cambio=None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.usuario_id = usuario_id
        self.on_cambio = on_cambio

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        layout_raiz.addWidget(self.stack)

        self.vista_general = QWidget()
        self._armar_vista_general()
        
        self.vista_detalle = QWidget()
        self._armar_vista_detalle()

        self.vista_toma_lista = QWidget()
        self._armar_vista_toma_lista()

        self.stack.addWidget(self.vista_general)     # 0
        self.stack.addWidget(self.vista_detalle)     # 1
        self.stack.addWidget(self.vista_toma_lista)  # 2

        self.recargar()

    def cambiar_rol(self, nuevo_rol: str):
        """Ajusta permisos y vistas en el panel de cursos segun el rol."""
        self.rol_actual = nuevo_rol
        if hasattr(self, "btn_toggle_alta"):
            if nuevo_rol in ("admin", "directivo"):
                self.btn_toggle_alta.show()
            else:
                self.btn_toggle_alta.hide()
                if hasattr(self, "tarjeta_form"):
                    self.tarjeta_form.hide()

    def _armar_vista_general(self):
        layout = QVBoxLayout(self.vista_general)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        fila_acciones = QHBoxLayout()
        self.btn_toggle_alta = QPushButton("+ Agregar curso")
        self.btn_toggle_alta.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_alta.setStyleSheet(_estilo_boton())
        self.btn_toggle_alta.clicked.connect(self._alternar_formulario_alta)
        fila_acciones.addWidget(self.btn_toggle_alta)
        fila_acciones.addStretch()
        layout.addLayout(fila_acciones)

        self.tarjeta_form = _tarjeta()
        form = QHBoxLayout(self.tarjeta_form)
        form.setContentsMargins(20, 16, 20, 16)
        form.setSpacing(12)

        col_anio = QVBoxLayout()
        col_anio.addWidget(_etiqueta("Año", tenue=True))
        self.combo_anio = QComboBox()
        self.combo_anio.addItems(["1", "2", "3", "4", "5", "6"])
        self.combo_anio.setStyleSheet(_estilo_input())
        self.combo_anio.currentIndexChanged.connect(self._actualizar_especialidad_habilitada)
        col_anio.addWidget(self.combo_anio)
        form.addLayout(col_anio)

        col_division = QVBoxLayout()
        col_division.addWidget(_etiqueta("División", tenue=True))
        self.input_division = QLineEdit()
        self.input_division.setPlaceholderText("1-9")
        self.input_division.setMaxLength(1)
        self.input_division.setValidator(_validador_division())
        self.input_division.setStyleSheet(_estilo_input())
        col_division.addWidget(self.input_division)
        form.addLayout(col_division)

        col_especialidad = QVBoxLayout()
        col_especialidad.addWidget(_etiqueta("Especialidad", tenue=True))
        self.combo_especialidad = QComboBox()
        self.combo_especialidad.addItem("(sin especialidad)", None)
        self.combo_especialidad.addItem("Computacion", "Computacion")
        self.combo_especialidad.addItem("Gestion y Adm. de las Organizaciones (GAO)", "GAO")
        self.combo_especialidad.setStyleSheet(_estilo_input())
        col_especialidad.addWidget(self.combo_especialidad)
        form.addLayout(col_especialidad)

        col_turno = QVBoxLayout()
        col_turno.addWidget(_etiqueta("Turno", tenue=True))
        self.combo_turno = QComboBox()
        self.combo_turno.addItems(["Mañana", "Tarde"])
        self.combo_turno.setStyleSheet(_estilo_input())
        col_turno.addWidget(self.combo_turno)
        form.addLayout(col_turno)

        self.btn_agregar = QPushButton("Guardar curso")
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_agregar.clicked.connect(self._agregar_curso)
        form.addWidget(self.btn_agregar, alignment=Qt.AlignBottom)

        self.tarjeta_form.hide()
        layout.addWidget(self.tarjeta_form)
        self._actualizar_especialidad_habilitada()

        self.tabs_cursos = QTabWidget()
        self.tabs_cursos.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background-color: {COLOR_TARJETA};
                color: {COLOR_TEXTO};
                font-family: '{FUENTE_MONO}';
                font-size: 11px;
                padding: 7px 18px;
                border-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_ACENTO};
                font-weight: bold;
                border-bottom: 2px solid {COLOR_TEXTO};
            }}
            QTabBar::tab:hover {{ background-color: {COLOR_ACENTO_HOVER}; }}
        """)
        layout.addWidget(self.tabs_cursos, stretch=1)

    def _armar_vista_detalle(self):
        layout = QVBoxLayout(self.vista_detalle)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        btn_volver = QPushButton("← Volver a cursos")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setStyleSheet(_estilo_boton(COLOR_TARJETA, COLOR_ACENTO_HOVER))
        btn_volver.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        header.addWidget(btn_volver)
        header.addStretch()

        self.btn_tomar_lista = QPushButton("📋 Tomar Lista")
        self.btn_tomar_lista.setCursor(Qt.PointingHandCursor)
        self.btn_tomar_lista.setStyleSheet(_estilo_boton("#1e3a29", "#284e37"))
        self.btn_tomar_lista.clicked.connect(self._iniciar_toma_lista)
        header.addWidget(self.btn_tomar_lista)
        
        self.btn_eliminar = QPushButton("Eliminar curso")
        self.btn_eliminar.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(_estilo_boton(COLOR_PELIGRO, COLOR_PELIGRO_HOVER))
        self.btn_eliminar.clicked.connect(self._eliminar_curso)
        header.addWidget(self.btn_eliminar)
        layout.addLayout(header)

        # Tarjeta encabezado del curso
        tarjeta_resumen = _tarjeta()
        layout_resumen = QVBoxLayout(tarjeta_resumen)
        layout_resumen.setContentsMargins(20, 16, 20, 16)
        layout_resumen.setSpacing(6)

        self.lbl_detalle_titulo = QLabel("...")
        self.lbl_detalle_titulo.setFont(QFont(FUENTE_MONO, 18, QFont.Bold))
        self.lbl_detalle_titulo.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout_resumen.addWidget(self.lbl_detalle_titulo)

        self.lbl_detalle_info = QLabel("...")
        self.lbl_detalle_info.setFont(QFont(FUENTE_MONO, 11))
        self.lbl_detalle_info.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        layout_resumen.addWidget(self.lbl_detalle_info)
        layout.addWidget(tarjeta_resumen)

        # Barra de listado y buscador
        barra_alumnos = QHBoxLayout()
        self.lbl_cant_alumnos_detalle = QLabel("Alumnos Matriculados")
        self.lbl_cant_alumnos_detalle.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        self.lbl_cant_alumnos_detalle.setStyleSheet(f"color: {COLOR_TEXTO};")
        barra_alumnos.addWidget(self.lbl_cant_alumnos_detalle)
        barra_alumnos.addStretch()

        self.input_buscar_alumno = QLineEdit()
        self.input_buscar_alumno.setPlaceholderText("🔍 Buscar por apellido, nombre o DNI...")
        self.input_buscar_alumno.setStyleSheet(_estilo_input())
        self.input_buscar_alumno.setFixedWidth(280)
        self.input_buscar_alumno.textChanged.connect(self._filtrar_alumnos_detalle)
        barra_alumnos.addWidget(self.input_buscar_alumno)
        layout.addLayout(barra_alumnos)

        # ScrollArea con lista minimalista
        self.scroll_alumnos = QScrollArea()
        self.scroll_alumnos.setWidgetResizable(True)
        self.scroll_alumnos.setFrameShape(QFrame.NoFrame)
        self.scroll_alumnos.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {COLOR_ACENTO}; border-radius: 4px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {COLOR_ACENTO_HOVER}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.contenedor_alumnos = QWidget()
        self.contenedor_alumnos.setStyleSheet("background: transparent;")
        self.layout_alumnos = QVBoxLayout(self.contenedor_alumnos)
        self.layout_alumnos.setContentsMargins(0, 4, 0, 4)
        self.layout_alumnos.setSpacing(8)

        self.lbl_sin_resultados = QLabel("No se encontraron alumnos que coincidan con la búsqueda.")
        self.lbl_sin_resultados.setFont(QFont(FUENTE_MONO, 11))
        self.lbl_sin_resultados.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 20px;")
        self.lbl_sin_resultados.setAlignment(Qt.AlignCenter)
        self.lbl_sin_resultados.hide()
        self.layout_alumnos.addWidget(self.lbl_sin_resultados)

        self.scroll_alumnos.setWidget(self.contenedor_alumnos)
        layout.addWidget(self.scroll_alumnos, stretch=1)

        self.filas_alumnos = []
        self.curso_actual = None

    def _armar_vista_toma_lista(self):
        layout = QVBoxLayout(self.vista_toma_lista)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        btn_volver = QPushButton("← Volver al curso")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setStyleSheet(_estilo_boton(COLOR_TARJETA, COLOR_ACENTO_HOVER))
        btn_volver.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        header.addWidget(btn_volver)

        self.lbl_toma_titulo = QLabel("Toma de Lista Diaria")
        self.lbl_toma_titulo.setFont(QFont(FUENTE_MONO, 16, QFont.Bold))
        self.lbl_toma_titulo.setStyleSheet(f"color: {COLOR_TEXTO};")
        header.addWidget(self.lbl_toma_titulo)
        header.addStretch()

        header.addWidget(_etiqueta("Fecha:", tenue=True))
        self.date_toma_lista = QDateEdit()
        self.date_toma_lista.setCalendarPopup(True)
        self.date_toma_lista.setDate(QDate.currentDate())
        self.date_toma_lista.setStyleSheet(_estilo_input())
        self.date_toma_lista.dateChanged.connect(self._recargar_toma_lista)
        header.addWidget(self.date_toma_lista)

        self.lbl_reloj = QLabel(f"🕒 {QTime.currentTime().toString('HH:mm')}")
        self.lbl_reloj.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_reloj.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            background-color: {COLOR_TARJETA};
            border: 1px solid {COLOR_BORDE};
            border-radius: 8px;
            padding: 6px 12px;
        """)
        header.addWidget(self.lbl_reloj)
        layout.addLayout(header)

        # Barra resumen de métricas y acciones rápidas
        barra_metricas = _tarjeta()
        layout_m = QHBoxLayout(barra_metricas)
        layout_m.setContentsMargins(16, 12, 16, 12)
        layout_m.setSpacing(16)

        self.lbl_metricas_toma = QLabel("...")
        self.lbl_metricas_toma.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_metricas_toma.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout_m.addWidget(self.lbl_metricas_toma)
        layout_m.addStretch()

        btn_todos_presentes = QPushButton("✓ Marcar todos presentes")
        btn_todos_presentes.setCursor(Qt.PointingHandCursor)
        btn_todos_presentes.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        btn_todos_presentes.clicked.connect(self._marcar_todos_presentes)
        layout_m.addWidget(btn_todos_presentes)

        layout.addWidget(barra_metricas)

        # Buscador
        fila_busqueda = QHBoxLayout()
        self.input_buscar_toma = QLineEdit()
        self.input_buscar_toma.setPlaceholderText("🔍 Filtrar alumno en la lista...")
        self.input_buscar_toma.setStyleSheet(_estilo_input())
        self.input_buscar_toma.textChanged.connect(self._filtrar_toma_lista)
        fila_busqueda.addWidget(self.input_buscar_toma)
        layout.addLayout(fila_busqueda)

        # ScrollArea con las filas de toma de lista
        self.scroll_toma = QScrollArea()
        self.scroll_toma.setWidgetResizable(True)
        self.scroll_toma.setFrameShape(QFrame.NoFrame)
        self.scroll_toma.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {COLOR_ACENTO}; border-radius: 4px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {COLOR_ACENTO_HOVER}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.contenedor_toma = QWidget()
        self.contenedor_toma.setStyleSheet("background: transparent;")
        self.layout_toma = QVBoxLayout(self.contenedor_toma)
        self.layout_toma.setContentsMargins(0, 4, 0, 4)
        self.layout_toma.setSpacing(8)

        self.lbl_sin_resultados_toma = QLabel("No se encontraron alumnos.")
        self.lbl_sin_resultados_toma.setFont(QFont(FUENTE_MONO, 11))
        self.lbl_sin_resultados_toma.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 20px;")
        self.lbl_sin_resultados_toma.setAlignment(Qt.AlignCenter)
        self.lbl_sin_resultados_toma.hide()
        self.layout_toma.addWidget(self.lbl_sin_resultados_toma)

        self.scroll_toma.setWidget(self.contenedor_toma)
        layout.addWidget(self.scroll_toma, stretch=1)

        # Botón Guardar inferior
        fila_guardar = QHBoxLayout()
        fila_guardar.addStretch()
        self.btn_guardar_toma = QPushButton("💾 Guardar Asistencia Diaria")
        self.btn_guardar_toma.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_toma.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        self.btn_guardar_toma.setStyleSheet(_estilo_boton("#1e3a29", "#284e37"))
        self.btn_guardar_toma.clicked.connect(self._guardar_toma_lista)
        fila_guardar.addWidget(self.btn_guardar_toma)
        layout.addLayout(fila_guardar)

        self.filas_toma = []

    def _iniciar_toma_lista(self):
        if not self.curso_actual:
            return
        self.lbl_toma_titulo.setText(f"Toma de Lista Diaria · {self.curso_actual['anio']}°{self.curso_actual['division']}")
        self.lbl_reloj.setText(f"🕒 {QTime.currentTime().toString('HH:mm')}")
        self.date_toma_lista.blockSignals(True)
        self.date_toma_lista.setDate(QDate.currentDate())
        self.date_toma_lista.blockSignals(False)
        self._recargar_toma_lista()
        self.stack.setCurrentIndex(2)

    def _recargar_toma_lista(self):
        if not self.curso_actual:
            return

        fecha = self.date_toma_lista.date().toString("yyyy-MM-dd")
        resultado = servicio_lista_diaria.obtener_lista_diaria(self.curso_actual["id"], fecha)
        if not resultado.ok:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            return

        for fila in self.filas_toma:
            self.layout_toma.removeWidget(fila)
            fila.deleteLater()
        self.filas_toma.clear()

        for i in reversed(range(self.layout_toma.count())):
            item = self.layout_toma.itemAt(i)
            widget = item.widget()
            if widget and widget != self.lbl_sin_resultados_toma:
                self.layout_toma.removeWidget(widget)
                widget.deleteLater()
            elif not widget:
                self.layout_toma.removeItem(item)

        self.input_buscar_toma.blockSignals(True)
        self.input_buscar_toma.clear()
        self.input_buscar_toma.blockSignals(False)
        self.lbl_sin_resultados_toma.hide()

        alumnos = resultado.datos["alumnos"]
        if not alumnos:
            lbl_vacio = QLabel("No hay alumnos matriculados en este curso.")
            lbl_vacio.setFont(QFont(FUENTE_MONO, 11))
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 30px;")
            lbl_vacio.setAlignment(Qt.AlignCenter)
            self.layout_toma.addWidget(lbl_vacio)
        else:
            for idx, al in enumerate(alumnos, 1):
                fila = FilaTomaLista(idx, al, on_cambio=self._actualizar_metricas_toma)
                self.layout_toma.addWidget(fila)
                self.filas_toma.append(fila)

        self.layout_toma.addStretch()
        self._actualizar_metricas_toma()

    def _actualizar_metricas_toma(self):
        p = sum(1 for f in self.filas_toma if f.estado == "presente")
        a = sum(1 for f in self.filas_toma if f.estado == "ausente")
        t = sum(1 for f in self.filas_toma if f.estado == "tarde")
        r = sum(1 for f in self.filas_toma if f.estado == "retirado")
        total = len(self.filas_toma)
        self.lbl_metricas_toma.setText(
            f"👥 {total} Alumnos  |  🟢 {p} Presentes  ·  🔴 {a} Ausentes  ·  🟡 {t} Tardes  ·  🔵 {r} Retirados"
        )

    def _marcar_todos_presentes(self):
        for f in self.filas_toma:
            f.set_estado("presente")
        self._actualizar_metricas_toma()

    def _filtrar_toma_lista(self, texto: str):
        texto = texto.strip().lower()
        visibles = 0
        for fila in self.filas_toma:
            coincide = not texto or (texto in fila.texto_busqueda)
            fila.setVisible(coincide)
            if coincide:
                visibles += 1

        total = len(self.filas_toma)
        if total > 0 and visibles == 0:
            self.lbl_sin_resultados_toma.show()
        else:
            self.lbl_sin_resultados_toma.hide()

    def _guardar_toma_lista(self):
        if not self.curso_actual or not self.filas_toma:
            return

        fecha = self.date_toma_lista.date().toString("yyyy-MM-dd")
        registros = [f.obtener_registro() for f in self.filas_toma]
        resultado = servicio_lista_diaria.guardar_lista_diaria(fecha, registros, self.usuario_id)

        if resultado.ok:
            QMessageBox.information(
                self, "Asistencia Guardada", f"Se guardó la lista diaria del día {fecha} con éxito."
            )
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo guardar", resultado.mensaje)

    def _alternar_formulario_alta(self):
        if self.tarjeta_form.isHidden():
            self.tarjeta_form.show()
            self.btn_toggle_alta.setText("Ocultar formulario")
        else:
            self.tarjeta_form.hide()
            self.btn_toggle_alta.setText("+ Agregar curso")

    def _actualizar_especialidad_habilitada(self):
        anio = int(self.combo_anio.currentText())
        habilitada = anio in servicio_curso.ANIOS_CON_ESPECIALIDAD
        self.combo_especialidad.setEnabled(habilitada)
        if not habilitada:
            self.combo_especialidad.setCurrentIndex(0)
        elif self.combo_especialidad.currentIndex() == 0:
            self.combo_especialidad.setCurrentIndex(1)

    def _agregar_curso(self):
        anio = int(self.combo_anio.currentText())
        division = self.input_division.text()
        especialidad = self.combo_especialidad.currentData()
        turno = self.combo_turno.currentText()

        resultado = servicio_curso.agregar_curso(self.ciclo_id, anio, division, turno, especialidad)
        if resultado.ok:
            self.input_division.clear()
            self.tarjeta_form.hide()
            self.btn_toggle_alta.setText("+ Agregar curso")
            self.recargar()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo agregar el curso", resultado.mensaje)

    def _abrir_detalle(self, curso):
        self.curso_actual = curso
        
        import datetime
        from database.conexion import conexion
        try:
            with conexion() as conn:
                c = conn.cursor()
                c.execute("SELECT anio FROM ciclo_lectivo WHERE id = ?", (self.ciclo_id,))
                f = c.fetchone()
                ciclo_anio = f["anio"] if f else datetime.date.today().year
        except Exception:
            ciclo_anio = datetime.date.today().year
            
        titulo = f"{curso['anio']}°{curso['division']} Ciclo {ciclo_anio}"
        self.lbl_detalle_titulo.setText(titulo)
        
        esp = f" · {curso['especialidad']}" if curso.get('especialidad') else ""
        info = f"Turno {curso['turno']}{esp} · {curso['cantidad_alumnos']} Alumnos Activos"
        self.lbl_detalle_info.setText(info)
        
        for fila in self.filas_alumnos:
            self.layout_alumnos.removeWidget(fila)
            fila.deleteLater()
        self.filas_alumnos.clear()

        for i in reversed(range(self.layout_alumnos.count())):
            item = self.layout_alumnos.itemAt(i)
            widget = item.widget()
            if widget and widget != self.lbl_sin_resultados:
                self.layout_alumnos.removeWidget(widget)
                widget.deleteLater()
            elif not widget:
                self.layout_alumnos.removeItem(item)

        self.input_buscar_alumno.blockSignals(True)
        self.input_buscar_alumno.clear()
        self.input_buscar_alumno.blockSignals(False)
        self.lbl_sin_resultados.hide()

        alumnos = servicio_alumno.listar_alumnos_de_curso(curso['id'])
        self.lbl_cant_alumnos_detalle.setText(f"Alumnos Matriculados ({len(alumnos)})")

        if not alumnos:
            lbl_vacio = QLabel("No hay alumnos matriculados en este curso.")
            lbl_vacio.setFont(QFont(FUENTE_MONO, 11))
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 30px;")
            lbl_vacio.setAlignment(Qt.AlignCenter)
            self.layout_alumnos.addWidget(lbl_vacio)
        else:
            for idx, al in enumerate(alumnos, 1):
                fila = FilaAlumnoMinimalista(idx, al)
                self.layout_alumnos.addWidget(fila)
                self.filas_alumnos.append(fila)

        self.layout_alumnos.addStretch()
        self.stack.setCurrentIndex(1)

    def _filtrar_alumnos_detalle(self, texto: str):
        texto = texto.strip().lower()
        visibles = 0
        for fila in self.filas_alumnos:
            coincide = not texto or (texto in fila.texto_busqueda)
            fila.setVisible(coincide)
            if coincide:
                visibles += 1
        
        total = len(self.filas_alumnos)
        if total > 0 and visibles == 0:
            self.lbl_sin_resultados.show()
        else:
            self.lbl_sin_resultados.hide()

        if texto:
            self.lbl_cant_alumnos_detalle.setText(f"Alumnos ({visibles} de {total})")
        else:
            self.lbl_cant_alumnos_detalle.setText(f"Alumnos Matriculados ({total})")

    def _eliminar_curso(self):
        if not self.curso_actual:
            return

        curso_id = self.curso_actual["id"]
        nombre = f"{self.curso_actual['anio']}°{self.curso_actual['division']}"
        confirmar = QMessageBox.question(
            self, "Confirmar", f"¿Seguro que querés eliminar el curso {nombre}?"
        )
        if confirmar != QMessageBox.Yes:
            return

        resultado = servicio_curso.eliminar_curso(curso_id)
        if resultado.ok:
            self.stack.setCurrentIndex(0)
            self.curso_actual = None
            self.recargar()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", resultado.mensaje)

    def recargar(self):
        resultado = servicio_curso.listar_cursos(self.ciclo_id)
        if not resultado.ok:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            return

        cursos = resultado.datos
        
        if self.stack.currentIndex() == 1 and self.curso_actual:
            curso_actualizado = next((c for c in cursos if c["id"] == self.curso_actual["id"]), None)
            if curso_actualizado:
                self._abrir_detalle(curso_actualizado)
            else:
                self.stack.setCurrentIndex(0)
                self.curso_actual = None
        elif self.stack.currentIndex() == 2 and self.curso_actual:
            self._recargar_toma_lista()

        ordinales = {1: "1ro", 2: "2do", 3: "3ro", 4: "4to", 5: "5to", 6: "6to"}

        por_anio = {}
        for c in cursos:
            por_anio.setdefault(c["anio"], []).append(c)

        tab_activo_idx = self.tabs_cursos.currentIndex()
        self.tabs_cursos.blockSignals(True)
        self.tabs_cursos.clear()
        
        import datetime
        from database.conexion import conexion
        try:
            with conexion() as conn:
                c = conn.cursor()
                c.execute("SELECT anio FROM ciclo_lectivo WHERE id = ?", (self.ciclo_id,))
                f = c.fetchone()
                ciclo_anio = f["anio"] if f else datetime.date.today().year
        except:
            ciclo_anio = datetime.date.today().year

        for anio in sorted(por_anio.keys()):
            label_tab = ordinales.get(anio, f"{anio}°")
            cantidad = len(por_anio[anio])

            contenedor = QScrollArea()
            contenedor.setWidgetResizable(True)
            contenedor.setFrameShape(QFrame.NoFrame)
            contenedor.setStyleSheet("background: transparent; border: none;")
            
            contenido = QWidget()
            contenido.setStyleSheet("background: transparent;")
            grilla = QGridLayout(contenido)
            grilla.setContentsMargins(16, 16, 16, 16)
            grilla.setSpacing(16)
            
            fila, col = 0, 0
            for curso in por_anio[anio]:
                tarjeta = TarjetaCurso(curso, ciclo_anio, self._abrir_detalle)
                grilla.addWidget(tarjeta, fila, col)
                col += 1
                if col > 2:
                    col = 0
                    fila += 1
                    
            grilla.setRowStretch(fila + 1, 1)
            grilla.setColumnStretch(3, 1)

            contenedor.setWidget(contenido)
            self.tabs_cursos.addTab(contenedor, f"{label_tab}  ({cantidad})")

        if not por_anio:
            vacio = QWidget()
            vacio.setStyleSheet("background: transparent;")
            lbl = QLabel("No hay cursos para este ciclo lectivo.")
            lbl.setFont(QFont(FUENTE_MONO, 11))
            lbl.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            lay = QVBoxLayout(vacio)
            lay.addWidget(lbl)
            self.tabs_cursos.addTab(vacio, "Sin cursos")

        self.tabs_cursos.blockSignals(False)
        if 0 <= tab_activo_idx < self.tabs_cursos.count():
            self.tabs_cursos.setCurrentIndex(tab_activo_idx)


class PanelAlumnos(QWidget):
    """Alta, listado minimalista, baja/reactivacion y cambio de curso de alumnos."""

    def __init__(self, ciclo_id: int, on_cambio=None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.on_cambio = on_cambio
        self.mapa_cursos = {}
        self.filas_alumnos = []
        self.alumno_seleccionado = None
        self.fila_seleccionada = None

        self._armar_ui()
        self.recargar_cursos()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- Filtros y Buscador superior ---
        fila_filtro = QHBoxLayout()
        fila_filtro.setSpacing(12)

        fila_filtro.addWidget(_etiqueta("Ver curso:", tenue=True))
        self.combo_curso_filtro = QComboBox()
        self.combo_curso_filtro.setStyleSheet(_estilo_input())
        self.combo_curso_filtro.currentIndexChanged.connect(self.recargar_tabla)
        fila_filtro.addWidget(self.combo_curso_filtro, stretch=1)

        self.check_inactivos = QCheckBox("Mostrar dados de baja")
        self.check_inactivos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        self.check_inactivos.stateChanged.connect(self.recargar_tabla)
        fila_filtro.addWidget(self.check_inactivos)

        self.input_buscar_alumno = QLineEdit()
        self.input_buscar_alumno.setPlaceholderText("🔍 Buscar por apellido, nombre o DNI...")
        self.input_buscar_alumno.setStyleSheet(_estilo_input())
        self.input_buscar_alumno.setFixedWidth(280)
        self.input_buscar_alumno.textChanged.connect(self._filtrar_alumnos)
        fila_filtro.addWidget(self.input_buscar_alumno)

        layout.addLayout(fila_filtro)

        # --- Formulario de alta (arranca oculto; se muestra con el boton "+ Agregar alumno") ---
        self.tarjeta_form = _tarjeta()
        form = QVBoxLayout(self.tarjeta_form)
        form.setContentsMargins(20, 16, 20, 16)
        form.setSpacing(10)

        fila1 = QHBoxLayout()
        fila1.setSpacing(12)

        col_numero = QVBoxLayout()
        col_numero.addWidget(_etiqueta("Numero de legajo", tenue=True))
        self.input_numero = QLineEdit()
        self.input_numero.setPlaceholderText("Ej: 1024")
        self.input_numero.setValidator(_validador_solo_numeros())
        self.input_numero.setStyleSheet(_estilo_input())
        col_numero.addWidget(self.input_numero)
        fila1.addLayout(col_numero)

        col_dni = QVBoxLayout()
        col_dni.addWidget(_etiqueta("DNI (opcional)", tenue=True))
        self.input_dni = QLineEdit()
        self.input_dni.setPlaceholderText("Ej: 40123456")
        self.input_dni.setValidator(_validador_solo_numeros())
        self.input_dni.setStyleSheet(_estilo_input())
        col_dni.addWidget(self.input_dni)
        fila1.addLayout(col_dni)
        form.addLayout(fila1)

        fila2 = QHBoxLayout()
        fila2.setSpacing(12)

        col_nombre = QVBoxLayout()
        col_nombre.addWidget(_etiqueta("Nombre", tenue=True))
        self.input_nombre = QLineEdit()
        self.input_nombre.setValidator(_validador_solo_letras())
        self.input_nombre.setStyleSheet(_estilo_input())
        col_nombre.addWidget(self.input_nombre)
        fila2.addLayout(col_nombre)

        col_apellido = QVBoxLayout()
        col_apellido.addWidget(_etiqueta("Apellido", tenue=True))
        self.input_apellido = QLineEdit()
        self.input_apellido.setValidator(_validador_solo_letras())
        self.input_apellido.setStyleSheet(_estilo_input())
        col_apellido.addWidget(self.input_apellido)
        fila2.addLayout(col_apellido)
        form.addLayout(fila2)

        fila3 = QHBoxLayout()
        fila3.setSpacing(12)

        col_nacionalidad = QVBoxLayout()
        col_nacionalidad.addWidget(_etiqueta("Nacionalidad", tenue=True))
        self.combo_nacionalidad = QComboBox()
        for pais in sorted(NACIONALIDADES.keys()):
            self.combo_nacionalidad.addItem(pais)
        indice_argentina = self.combo_nacionalidad.findText("Argentina")
        if indice_argentina >= 0:
            self.combo_nacionalidad.setCurrentIndex(indice_argentina)
        self.combo_nacionalidad.currentTextChanged.connect(self._actualizar_maximo_dni)
        self.combo_nacionalidad.setStyleSheet(_estilo_input())
        col_nacionalidad.addWidget(self.combo_nacionalidad)
        fila3.addLayout(col_nacionalidad)

        col_curso = QVBoxLayout()
        col_curso.addWidget(_etiqueta("Curso", tenue=True))
        self.combo_curso_alta = QComboBox()
        self.combo_curso_alta.setStyleSheet(_estilo_input())
        col_curso.addWidget(self.combo_curso_alta)
        fila3.addLayout(col_curso)
        form.addLayout(fila3)

        self.btn_agregar = QPushButton("Guardar alumno")
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.setStyleSheet(_estilo_boton())
        self.btn_agregar.clicked.connect(self._agregar_alumno)
        form.addWidget(self.btn_agregar, alignment=Qt.AlignRight)

        self.tarjeta_form.hide()
        layout.addWidget(self.tarjeta_form)
        self._actualizar_maximo_dni(self.combo_nacionalidad.currentText())

        # --- Lista minimalista de alumnos ---
        self.scroll_alumnos = QScrollArea()
        self.scroll_alumnos.setWidgetResizable(True)
        self.scroll_alumnos.setFrameShape(QFrame.NoFrame)
        self.scroll_alumnos.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_ACENTO};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLOR_ACENTO_HOVER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.contenedor_alumnos = QWidget()
        self.contenedor_alumnos.setStyleSheet("background: transparent;")
        self.layout_alumnos = QVBoxLayout(self.contenedor_alumnos)
        self.layout_alumnos.setContentsMargins(0, 4, 0, 4)
        self.layout_alumnos.setSpacing(8)

        self.lbl_sin_resultados = QLabel("No se encontraron alumnos que coincidan con la búsqueda.")
        self.lbl_sin_resultados.setFont(QFont(FUENTE_MONO, 11))
        self.lbl_sin_resultados.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 20px;")
        self.lbl_sin_resultados.setAlignment(Qt.AlignCenter)
        self.lbl_sin_resultados.hide()
        self.layout_alumnos.addWidget(self.lbl_sin_resultados)

        self.scroll_alumnos.setWidget(self.contenedor_alumnos)
        layout.addWidget(self.scroll_alumnos, stretch=1)

        # --- Acciones sobre el seleccionado ---
        fila_acciones = QHBoxLayout()

        self.btn_toggle_alta = QPushButton("+ Agregar alumno")
        self.btn_toggle_alta.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_alta.setStyleSheet(_estilo_boton())
        self.btn_toggle_alta.clicked.connect(self._alternar_formulario_alta)
        fila_acciones.addWidget(self.btn_toggle_alta)

        self.btn_baja = QPushButton("Dar de baja")
        self.btn_baja.setCursor(Qt.PointingHandCursor)
        self.btn_baja.setStyleSheet(_estilo_boton(COLOR_PELIGRO, COLOR_PELIGRO_HOVER))
        self.btn_baja.clicked.connect(self._dar_de_baja)
        fila_acciones.addWidget(self.btn_baja)

        self.btn_reactivar = QPushButton("Reactivar")
        self.btn_reactivar.setCursor(Qt.PointingHandCursor)
        self.btn_reactivar.setStyleSheet(_estilo_boton())
        self.btn_reactivar.clicked.connect(self._reactivar)
        fila_acciones.addWidget(self.btn_reactivar)

        self.combo_nuevo_curso = QComboBox()
        self.combo_nuevo_curso.setStyleSheet(_estilo_input())
        fila_acciones.addWidget(self.combo_nuevo_curso, stretch=1)

        self.btn_mover = QPushButton("Cambiar de curso")
        self.btn_mover.setCursor(Qt.PointingHandCursor)
        self.btn_mover.setStyleSheet(_estilo_boton())
        self.btn_mover.clicked.connect(self._cambiar_curso)
        fila_acciones.addWidget(self.btn_mover)

        layout.addLayout(fila_acciones)

    def _actualizar_maximo_dni(self, pais: str):
        """Ajusta cuantos digitos se pueden escribir en DNI segun la nacionalidad elegida."""
        maximo = NACIONALIDADES.get(pais, 12)
        self.input_dni.setMaxLength(maximo)
        if len(self.input_dni.text()) > maximo:
            self.input_dni.setText(self.input_dni.text()[:maximo])

    def _alternar_formulario_alta(self):
        """Muestra u oculta el formulario de alta de alumno."""
        mostrar = not self.tarjeta_form.isVisible()
        self.tarjeta_form.setVisible(mostrar)
        self.btn_toggle_alta.setText("Cancelar" if mostrar else "+ Agregar alumno")

    def recargar_cursos(self):
        """Vuelve a cargar los combos de curso (llamar despues de agregar/eliminar un curso)."""
        resultado = servicio_curso.listar_cursos(self.ciclo_id)
        cursos = resultado.datos if resultado.ok else []

        self.mapa_cursos = {c["id"]: servicio_curso.obtener_nombre_curso(c) for c in cursos}

        for combo in (self.combo_curso_alta, self.combo_nuevo_curso):
            combo.clear()
            for c in cursos:
                combo.addItem(servicio_curso.obtener_nombre_curso(c), c["id"])

        self.combo_curso_filtro.blockSignals(True)
        self.combo_curso_filtro.clear()
        self.combo_curso_filtro.addItem("Todos los cursos", None)
        for c in cursos:
            self.combo_curso_filtro.addItem(servicio_curso.obtener_nombre_curso(c), c["id"])
        self.combo_curso_filtro.blockSignals(False)

        self.recargar_tabla()

    def _agregar_alumno(self):
        curso_id = self.combo_curso_alta.currentData()
        if curso_id is None:
            QMessageBox.warning(self, "Sin cursos", "Primero tenes que crear un curso en la pestana Cursos")
            return

        numero_texto = self.input_numero.text().strip()
        if not numero_texto.isdigit():
            QMessageBox.warning(self, "Numero invalido", "El numero de legajo tiene que ser numerico")
            return

        resultado = servicio_alumno.agregar_alumno(
            numero=int(numero_texto),
            nombre=self.input_nombre.text(),
            apellido=self.input_apellido.text(),
            curso_id=curso_id,
            dni=self.input_dni.text(),
            nacionalidad=self.combo_nacionalidad.currentText(),
        )
        if resultado.ok:
            self.input_numero.clear()
            self.input_dni.clear()
            self.input_nombre.clear()
            self.input_apellido.clear()
            self._alternar_formulario_alta()  # lo vuelve a ocultar
            self.recargar_tabla()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo agregar el alumno", resultado.mensaje)

    def _on_fila_alumno_click(self, fila):
        if self.fila_seleccionada == fila:
            fila.set_seleccionada(False)
            self.fila_seleccionada = None
            self.alumno_seleccionado = None
        else:
            if self.fila_seleccionada:
                self.fila_seleccionada.set_seleccionada(False)
            self.fila_seleccionada = fila
            self.alumno_seleccionado = fila.alumno
            fila.set_seleccionada(True)

    def recargar_tabla(self):
        curso_id = self.combo_curso_filtro.currentData()
        solo_activos = not self.check_inactivos.isChecked()
        resultado = servicio_alumno.listar_alumnos(curso_id=curso_id, solo_activos=solo_activos)
        if not resultado.ok:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            return

        self.alumno_seleccionado = None
        self.fila_seleccionada = None

        for fila in self.filas_alumnos:
            self.layout_alumnos.removeWidget(fila)
            fila.deleteLater()
        self.filas_alumnos.clear()

        for i in reversed(range(self.layout_alumnos.count())):
            item = self.layout_alumnos.itemAt(i)
            widget = item.widget()
            if widget and widget != self.lbl_sin_resultados:
                self.layout_alumnos.removeWidget(widget)
                widget.deleteLater()
            elif not widget:
                self.layout_alumnos.removeItem(item)

        alumnos = resultado.datos
        self.lbl_sin_resultados.hide()

        if not alumnos:
            lbl_vacio = QLabel("No hay alumnos cargados para el filtro actual.")
            lbl_vacio.setFont(QFont(FUENTE_MONO, 11))
            lbl_vacio.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 30px;")
            lbl_vacio.setAlignment(Qt.AlignCenter)
            self.layout_alumnos.addWidget(lbl_vacio)
        else:
            for idx, a in enumerate(alumnos, 1):
                curso_texto = self.mapa_cursos.get(a.get("curso_id"), "")
                fila = FilaAlumnoMinimalista(
                    idx,
                    a,
                    curso_texto=curso_texto,
                    on_click=self._on_fila_alumno_click,
                )
                self.layout_alumnos.addWidget(fila)
                self.filas_alumnos.append(fila)

        self.layout_alumnos.addStretch()

        texto_busqueda = self.input_buscar_alumno.text().strip()
        if texto_busqueda:
            self._filtrar_alumnos(texto_busqueda)

    def _filtrar_alumnos(self, texto: str):
        texto = texto.strip().lower()
        visibles = 0
        for fila in self.filas_alumnos:
            coincide = not texto or (texto in fila.texto_busqueda)
            fila.setVisible(coincide)
            if coincide:
                visibles += 1

        total = len(self.filas_alumnos)
        if total > 0 and visibles == 0:
            self.lbl_sin_resultados.show()
        else:
            self.lbl_sin_resultados.hide()

    def _numero_seleccionado(self):
        if not self.alumno_seleccionado:
            QMessageBox.information(
                self, "Elegí un alumno", "Seleccioná primero un alumno de la lista haciendo clic sobre él"
            )
            return None
        return int(self.alumno_seleccionado["numero"])

    def _dar_de_baja(self):
        numero = self._numero_seleccionado()
        if numero is None:
            return
        resultado = servicio_alumno.dar_de_baja_alumno(numero)
        if resultado.ok:
            self.recargar_tabla()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo dar de baja", resultado.mensaje)

    def _reactivar(self):
        numero = self._numero_seleccionado()
        if numero is None:
            return
        resultado = servicio_alumno.reactivar_alumno(numero)
        if resultado.ok:
            self.recargar_tabla()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo reactivar", resultado.mensaje)

    def _cambiar_curso(self):
        numero = self._numero_seleccionado()
        if numero is None:
            return
        nuevo_curso_id = self.combo_nuevo_curso.currentData()
        if nuevo_curso_id is None:
            QMessageBox.warning(self, "Sin cursos", "No hay cursos cargados todavia")
            return
        resultado = servicio_alumno.cambiar_curso_alumno(numero, nuevo_curso_id)
        if resultado.ok:
            self.recargar_tabla()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo cambiar de curso", resultado.mensaje)


class VentanaAdmin(QMainWindow):
    """Ventana principal del panel de administrador (super usuario)."""

    def __init__(self, usuario: dict | None = None):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("Panel de Administrador")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)

        self.dragging = False
        self.drag_offset = QPoint()

        self.central = QWidget(self)
        self.central.setStyleSheet(f"background-color: {COLOR_FONDO};")
        self.setCentralWidget(self.central)

        layout_raiz = QVBoxLayout(self.central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        layout_raiz.addWidget(self._armar_barra_titulo())

        # Obtener/crear el ciclo lectivo actual antes de armar los paneles
        resultado_ciclo = servicio_ciclo.obtener_o_crear_ciclo_actual()
        if not resultado_ciclo.ok:
            QMessageBox.critical(self, "Error critico", resultado_ciclo.mensaje)
            self.ciclo_id = None
        else:
            self.ciclo_id = resultado_ciclo.datos

        self._armar_sidebar_y_stack()
        layout_raiz.addWidget(self.cuerpo)
        self._al_cambiar_rol_vista()

    def _armar_sidebar_y_stack(self):
        """Construye el sidebar de navegacion y el QStackedWidget de paneles."""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_TARJETA};
                border-right: 1px solid {COLOR_BORDE};
            }}
            QLabel {{
                color: {COLOR_TEXTO};
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO_TENUE};
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-family: '{FUENTE_MONO}';
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACENTO};
                color: {COLOR_TEXTO};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_INPUT};
            }}
            QPushButton:checked {{
                background-color: {COLOR_ACENTO};
                color: {COLOR_TEXTO};
                border-left: 3px solid {COLOR_TEXTO};
            }}
            QPushButton:checked:hover {{
                background-color: {COLOR_ACENTO_HOVER};
            }}
        """)

        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(16, 20, 16, 20)
        layout_sidebar.setSpacing(8)

        branding = QLabel("Asistencia\nEscolar")
        branding.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        branding.setStyleSheet(f"color: {COLOR_TEXTO};")
        layout_sidebar.addWidget(branding)
        layout_sidebar.addSpacing(24)

        self.grupo_nav = QButtonGroup(self)
        self.grupo_nav.setExclusive(True)
        self.botones_nav = []
        nombres_nav = ["Inicio", "Cursos", "Alumnos", "Asistencia"]
        for idx, nombre in enumerate(nombres_nav):
            btn = QPushButton(nombre)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.grupo_nav.addButton(btn, idx)
            layout_sidebar.addWidget(btn)
            self.botones_nav.append(btn)

        layout_sidebar.addStretch()

        self.label_usuario = QLabel()
        self.label_usuario.setWordWrap(True)
        self.label_usuario.setStyleSheet(
            f"color: {COLOR_TEXTO_TENUE}; font-size: 11px; background: transparent; border: none;"
        )
        self._actualizar_footer_usuario()
        layout_sidebar.addWidget(self.label_usuario)

        self.btn_logout = QPushButton("Cerrar sesion")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(_estilo_boton(COLOR_PELIGRO, COLOR_PELIGRO_HOVER))
        self.btn_logout.clicked.connect(self._cerrar_sesion)
        layout_sidebar.addWidget(self.btn_logout)

        self.stack = QStackedWidget()

        self.panel_hub = PanelHub(self.ciclo_id)
        self.panel_alumnos = PanelAlumnos(self.ciclo_id)
        usuario_id = self.usuario.get("id", 1) if self.usuario else 1
        self.panel_cursos = PanelCursos(
            self.ciclo_id, usuario_id=usuario_id, on_cambio=self.panel_alumnos.recargar_cursos
        )
        self.panel_alumnos.on_cambio = self.panel_cursos.recargar
        self.panel_asistencia = PanelAsistencia(self.ciclo_id)

        self.stack.addWidget(self.panel_hub)        # 0 - Inicio
        self.stack.addWidget(self.panel_cursos)     # 1 - Cursos
        self.stack.addWidget(self.panel_alumnos)    # 2 - Alumnos
        self.stack.addWidget(self.panel_asistencia) # 3 - Asistencia

        self.grupo_nav.idClicked.connect(self.stack.setCurrentIndex)
        self.stack.currentChanged.connect(lambda i: self.grupo_nav.button(i).setChecked(True))
        self.panel_hub.navegar_a_alumnos.connect(lambda: self.stack.setCurrentIndex(2))
        self.panel_hub.navegar_a_cursos.connect(lambda: self.stack.setCurrentIndex(1))
        self.panel_hub.navegar_a_asistencia.connect(lambda: self.stack.setCurrentIndex(3))

        self.stack.setCurrentIndex(0)
        self.grupo_nav.button(0).setChecked(True)

        self.cuerpo = QWidget()
        layout_cuerpo = QHBoxLayout(self.cuerpo)
        layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        layout_cuerpo.setSpacing(0)
        layout_cuerpo.addWidget(self.sidebar)
        layout_cuerpo.addWidget(self.stack, stretch=1)

    def _actualizar_footer_usuario(self, rol_vista: str | None = None):
        if self.usuario:
            nombre = self.usuario.get("nombre", "Usuario")
            rol_real = self.usuario.get("rol", "admin")
            if rol_vista and rol_vista != rol_real:
                self.label_usuario.setText(f"{nombre} ({rol_real})\nVista: {rol_vista.capitalize()}")
            else:
                self.label_usuario.setText(f"{nombre}\n{rol_real.capitalize()}")
        else:
            rol_txt = rol_vista.capitalize() if rol_vista else "Admin"
            self.label_usuario.setText(f"Sesion local\nVista: {rol_txt}")

    def _al_cambiar_rol_vista(self, index: int = 0):
        if not hasattr(self, "combo_rol_vista"):
            return
        rol = self.combo_rol_vista.currentData()
        if not rol:
            return

        titulos_rol = {
            "admin": "Panel de Administrador",
            "directivo": "Panel Directivo",
            "preceptor": "Panel de Preceptoría",
            "profesor": "Panel Docente",
        }
        if hasattr(self, "label_titulo_barra"):
            self.label_titulo_barra.setText(titulos_rol.get(rol, "Panel de Control"))

        if hasattr(self, "panel_hub"):
            self.panel_hub.cambiar_rol(rol)

        self._actualizar_footer_usuario(rol_vista=rol)
        self._aplicar_permisos_vista_rol(rol)

    def _aplicar_permisos_vista_rol(self, rol: str):
        # 0: Inicio, 1: Cursos, 2: Alumnos, 3: Asistencia
        if hasattr(self, "botones_nav") and len(self.botones_nav) >= 4:
            btn_alumnos = self.botones_nav[2]
            if rol == "profesor":
                btn_alumnos.hide()
                if self.stack.currentIndex() == 2:
                    self.stack.setCurrentIndex(0)
            else:
                btn_alumnos.show()

        if hasattr(self, "panel_cursos") and hasattr(self.panel_cursos, "cambiar_rol"):
            self.panel_cursos.cambiar_rol(rol)

    def _cerrar_sesion(self):
        """Cierra el admin y abre una nueva ventana de login; nunca termina la app."""
        from interfaz.login import VentanaLogin
        self.ventana_login = VentanaLogin()
        self.ventana_login.mostrar()
        self.close()

    def _armar_barra_titulo(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(44)
        barra.setStyleSheet(f"background-color: {COLOR_FONDO}; border-bottom: 1px solid {COLOR_BORDE};")

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(20, 0, 12, 0)
        layout.setSpacing(10)

        self.label_titulo_barra = QLabel("Panel de Administrador")
        self.label_titulo_barra.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.label_titulo_barra.setStyleSheet(f"color: {COLOR_TEXTO};")
        layout.addWidget(self.label_titulo_barra)

        layout.addSpacing(8)

        self.lbl_vista = QLabel("Vista:")
        self.lbl_vista.setFont(QFont(FUENTE_MONO, 10))
        self.lbl_vista.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        layout.addWidget(self.lbl_vista)

        self.combo_rol_vista = QComboBox()
        self.combo_rol_vista.addItem("👑 Administrador", "admin")
        self.combo_rol_vista.addItem("👔 Directivo", "directivo")
        self.combo_rol_vista.addItem("📋 Preceptor", "preceptor")
        self.combo_rol_vista.addItem("👨‍🏫 Profesor", "profesor")
        self.combo_rol_vista.setCursor(Qt.PointingHandCursor)
        self.combo_rol_vista.setFixedHeight(28)
        self.combo_rol_vista.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_BORDE};
                border-radius: 6px;
                color: {COLOR_TEXTO};
                padding: 2px 10px;
                font-family: '{FUENTE_MONO}';
                font-size: 11px;
                font-weight: bold;
            }}
            QComboBox:hover {{
                border: 1px solid #3a3a5a;
                background-color: {COLOR_ACENTO};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left-width: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #141416;
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
                border: 1px solid {COLOR_BORDE};
                padding: 4px;
            }}
        """)
        self.combo_rol_vista.currentIndexChanged.connect(self._al_cambiar_rol_vista)
        layout.addWidget(self.combo_rol_vista)

        # Si el usuario logueado NO es admin, no puede cambiar de rol
        if self.usuario and self.usuario.get("rol") != "admin":
            self.lbl_vista.hide()
            self.combo_rol_vista.hide()

        layout.addStretch()

        estilo_btn_ventana = """
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #e5e5e5; }
            QPushButton:pressed { background-color: #cccccc; }
        """
        estilo_btn_cerrar = """
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #ff5c5c; }
            QPushButton:pressed { background-color: #e04848; }
        """

        self.btn_minimizar = QPushButton(barra)
        self.btn_minimizar.setFixedSize(24, 24)
        self.btn_minimizar.setCursor(Qt.PointingHandCursor)
        self.btn_minimizar.setToolTip("Minimizar")
        self.btn_minimizar.setIcon(QIcon(ICONO_MINIMIZAR))
        self.btn_minimizar.setIconSize(QSize(14, 14))
        self.btn_minimizar.setStyleSheet(estilo_btn_ventana)
        self.btn_minimizar.clicked.connect(self.showMinimized)

        self.btn_maximizar = QPushButton(barra)
        self.btn_maximizar.setFixedSize(24, 24)
        self.btn_maximizar.setCursor(Qt.PointingHandCursor)
        self.btn_maximizar.setToolTip("Maximizar")
        self.btn_maximizar.setIcon(QIcon(ICONO_MAXIMIZAR))
        self.btn_maximizar.setIconSize(QSize(14, 14))
        self.btn_maximizar.setStyleSheet(estilo_btn_ventana)
        self.btn_maximizar.clicked.connect(self._alternar_maximizar)

        self.btn_cerrar = QPushButton(barra)
        self.btn_cerrar.setFixedSize(24, 24)
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.setToolTip("Cerrar")
        self.btn_cerrar.setIcon(QIcon(ICONO_CERRAR))
        self.btn_cerrar.setIconSize(QSize(14, 14))
        self.btn_cerrar.setStyleSheet(estilo_btn_cerrar)
        self.btn_cerrar.clicked.connect(self._cerrar_aplicacion)

        layout.addWidget(self.btn_minimizar)
        layout.addWidget(self.btn_maximizar)
        layout.addWidget(self.btn_cerrar)

        barra.mousePressEvent = self._barra_mouse_press
        barra.mouseMoveEvent = self._barra_mouse_move
        barra.mouseReleaseEvent = self._barra_mouse_release
        barra.mouseDoubleClickEvent = self._barra_mouse_double_click

        return barra

    def _alternar_maximizar(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_maximizar.setToolTip("Maximizar")
        else:
            self.showMaximized()
            self.btn_maximizar.setToolTip("Restaurar")

    def _cerrar_aplicacion(self):
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    def _barra_mouse_press(self, event):
        if event.button() == Qt.LeftButton and not self.isMaximized():
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _barra_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def _barra_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def _barra_mouse_double_click(self, event):
        if event.button() == Qt.LeftButton:
            self._alternar_maximizar()
            event.accept()


if __name__ == "__main__":
    # Permite probar esta ventana de forma independiente:
    #   python -m interfaz.admin   (parado en la carpeta raiz del proyecto)
    app = QApplication(sys.argv)
    ventana = VentanaAdmin()
    ventana.show()
    sys.exit(app.exec())