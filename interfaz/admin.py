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
    QLabel, QLineEdit, QPushButton, QFrame, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QCheckBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QPoint, QSize, QRegularExpression
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator

from servicios import curso as servicio_curso
from servicios import alumno as servicio_alumno
from servicios import ciclo_lectivo as servicio_ciclo


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

FUENTE_MONO = "Courier New"

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

COLOR_FONDO = "#0b0b0d"
COLOR_TARJETA = "rgba(255, 255, 255, 0.04)"
COLOR_BORDE = "rgba(255, 255, 255, 0.08)"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_TENUE = "#888888"
COLOR_INPUT = "#151517"
COLOR_ACENTO = "#2e2e33"
COLOR_ACENTO_HOVER = "#3a3a40"
COLOR_PELIGRO = "#7a2c2c"
COLOR_PELIGRO_HOVER = "#933636"


def _estilo_input():
    return f"""
        QLineEdit, QComboBox {{
            background-color: {COLOR_INPUT};
            border: 1px solid #1f1f1f;
            border-radius: 10px;
            color: {COLOR_TEXTO};
            padding: 8px 12px;
        }}
        QLineEdit:focus, QComboBox:focus {{ border: 1px solid #3a3a5a; }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_INPUT};
            color: {COLOR_TEXTO};
            selection-background-color: {COLOR_ACENTO};
        }}
    """


def _estilo_boton(color=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER):
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {color_hover}; }}
        QPushButton:disabled {{ background-color: #1a1a1c; color: #555555; }}
    """


def _estilo_tabla():
    return f"""
        QTableWidget {{
            background-color: {COLOR_INPUT};
            alternate-background-color: #1a1a1c;
            color: {COLOR_TEXTO};
            border: 1px solid {COLOR_BORDE};
            border-radius: 10px;
            gridline-color: #232326;
        }}
        QHeaderView::section {{
            background-color: #1c1c1f;
            color: {COLOR_TEXTO_TENUE};
            padding: 8px;
            border: none;
            font-weight: bold;
        }}
        QTableWidget::item:selected {{ background-color: #2a2a3a; }}
    """


def _tarjeta() -> QFrame:
    tarjeta = QFrame()
    tarjeta.setStyleSheet(f"""
        background-color: {COLOR_TARJETA};
        border-radius: 16px;
        border: 1px solid {COLOR_BORDE};
    """)
    return tarjeta


def _etiqueta(texto: str, tenue: bool = False) -> QLabel:
    label = QLabel(texto)
    label.setFont(QFont(FUENTE_MONO, 11, QFont.Bold if not tenue else QFont.Normal))
    color = COLOR_TEXTO_TENUE if tenue else COLOR_TEXTO
    label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return label


def _validador_solo_letras() -> QRegularExpressionValidator:
    """Letras (con acentos y ñ) y espacios, para nombre/apellido."""
    return QRegularExpressionValidator(QRegularExpression(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]*$"))


def _validador_solo_numeros() -> QRegularExpressionValidator:
    """Solo digitos, para DNI y numero de legajo."""
    return QRegularExpressionValidator(QRegularExpression(r"^[0-9]*$"))


def _validador_division() -> QRegularExpressionValidator:
    """Un solo digito del 1 al 9 (o vacio mientras se esta escribiendo)."""
    return QRegularExpressionValidator(QRegularExpression(r"^[1-9]?$"))


class PanelCursos(QWidget):
    """Alta, listado y baja de cursos."""

    def __init__(self, ciclo_id: int, on_cambio=None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.on_cambio = on_cambio  # callback para avisar a PanelAlumnos que recargue combos
        self._armar_ui()
        self.recargar()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- Formulario de alta ---
        tarjeta_form = _tarjeta()
        form = QHBoxLayout(tarjeta_form)
        form.setContentsMargins(20, 16, 20, 16)
        form.setSpacing(12)

        col_anio = QVBoxLayout()
        col_anio.addWidget(_etiqueta("Anio", tenue=True))
        self.combo_anio = QComboBox()
        self.combo_anio.addItems(["1", "2", "3", "4", "5", "6"])
        self.combo_anio.setStyleSheet(_estilo_input())
        self.combo_anio.currentIndexChanged.connect(self._actualizar_especialidad_habilitada)
        col_anio.addWidget(self.combo_anio)
        form.addLayout(col_anio)

        col_division = QVBoxLayout()
        col_division.addWidget(_etiqueta("Division", tenue=True))
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

        self.btn_agregar = QPushButton("+ Agregar curso")
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.setStyleSheet(_estilo_boton())
        self.btn_agregar.clicked.connect(self._agregar_curso)
        form.addWidget(self.btn_agregar, alignment=Qt.AlignBottom)

        layout.addWidget(tarjeta_form)
        self._actualizar_especialidad_habilitada()

        # --- Tabla de cursos ---
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Anio", "Division", "Especialidad", "Turno", "Alumnos", "ID"]
        )
        self.tabla.setColumnHidden(5, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla)

        self.btn_eliminar = QPushButton("Eliminar curso seleccionado")
        self.btn_eliminar.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(_estilo_boton(COLOR_PELIGRO, COLOR_PELIGRO_HOVER))
        self.btn_eliminar.clicked.connect(self._eliminar_curso)
        layout.addWidget(self.btn_eliminar, alignment=Qt.AlignLeft)

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
            self.recargar()
            if self.on_cambio:
                self.on_cambio()
        else:
            QMessageBox.warning(self, "No se pudo agregar el curso", resultado.mensaje)

    def _eliminar_curso(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Elegi un curso", "Selecciona primero un curso de la tabla")
            return

        curso_id = int(self.tabla.item(fila, 5).text())
        nombre = self.tabla.item(fila, 0).text() + " " + self.tabla.item(fila, 1).text()
        confirmar = QMessageBox.question(
            self, "Confirmar", f"Seguro que queres eliminar el curso {nombre}?"
        )
        if confirmar != QMessageBox.Yes:
            return

        resultado = servicio_curso.eliminar_curso(curso_id)
        if resultado.ok:
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
        self.tabla.setRowCount(len(cursos))
        ordinales = {1: "1ro", 2: "2do", 3: "3ro", 4: "4to", 5: "5to", 6: "6to"}
        for fila, c in enumerate(cursos):
            especialidad = servicio_curso.NOMBRES_ESPECIALIDAD.get(c["especialidad"], "-")
            valores = [
                ordinales.get(c["anio"], str(c["anio"])),
                c["division"],
                especialidad,
                c["turno"],
                str(c["cantidad_alumnos"]),
                str(c["id"]),
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))


class PanelAlumnos(QWidget):
    """Alta, listado, baja/reactivacion y cambio de curso de alumnos."""

    def __init__(self, ciclo_id: int):
        super().__init__()
        self.ciclo_id = ciclo_id
        self._armar_ui()
        self.recargar_cursos()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- Filtro (arriba de todo, la tabla es lo principal de esta pantalla) ---
        fila_filtro = QHBoxLayout()
        fila_filtro.addWidget(_etiqueta("Ver curso:", tenue=True))
        self.combo_curso_filtro = QComboBox()
        self.combo_curso_filtro.setStyleSheet(_estilo_input())
        self.combo_curso_filtro.currentIndexChanged.connect(self.recargar_tabla)
        fila_filtro.addWidget(self.combo_curso_filtro, stretch=1)

        self.check_inactivos = QCheckBox("Mostrar dados de baja")
        self.check_inactivos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        self.check_inactivos.stateChanged.connect(self.recargar_tabla)
        fila_filtro.addWidget(self.check_inactivos)
        layout.addLayout(fila_filtro)

        # --- Tabla de alumnos (ocupa todo el espacio que el formulario deja libre) ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Numero", "Apellido", "Nombre", "DNI", "Nacionalidad", "Estado", "Curso ID"]
        )
        self.tabla.setColumnHidden(6, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla, stretch=1)

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

        # --- Acciones sobre el seleccionado (aca vive el boton para abrir el alta) ---
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
        else:
            QMessageBox.warning(self, "No se pudo agregar el alumno", resultado.mensaje)

    def recargar_tabla(self):
        curso_id = self.combo_curso_filtro.currentData()
        solo_activos = not self.check_inactivos.isChecked()
        resultado = servicio_alumno.listar_alumnos(curso_id=curso_id, solo_activos=solo_activos)
        if not resultado.ok:
            QMessageBox.warning(self, "Error", resultado.mensaje)
            return

        alumnos = resultado.datos
        self.tabla.setRowCount(len(alumnos))
        for fila, a in enumerate(alumnos):
            estado = "Activo" if a["activo"] else "De baja"
            valores = [
                str(a["numero"]), a["apellido"], a["nombre"],
                a["dni"] or "-", a["nacionalidad"] or "-", estado, str(a["curso_id"]),
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))

    def _numero_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Elegi un alumno", "Selecciona primero un alumno de la tabla")
            return None
        return int(self.tabla.item(fila, 0).text())

    def _dar_de_baja(self):
        numero = self._numero_seleccionado()
        if numero is None:
            return
        resultado = servicio_alumno.dar_de_baja_alumno(numero)
        if resultado.ok:
            self.recargar_tabla()
        else:
            QMessageBox.warning(self, "No se pudo dar de baja", resultado.mensaje)

    def _reactivar(self):
        numero = self._numero_seleccionado()
        if numero is None:
            return
        resultado = servicio_alumno.reactivar_alumno(numero)
        if resultado.ok:
            self.recargar_tabla()
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
        else:
            QMessageBox.warning(self, "No se pudo cambiar de curso", resultado.mensaje)


class VentanaAdmin(QMainWindow):
    """Ventana principal del panel de administrador (super usuario)."""

    def __init__(self):
        super().__init__()
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

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: transparent;
                color: {COLOR_TEXTO_TENUE};
                padding: 12px 24px;
                font-family: '{FUENTE_MONO}';
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                color: {COLOR_TEXTO};
                border-bottom: 2px solid #5a5a8a;
            }}
        """)

        self.panel_alumnos = PanelAlumnos(self.ciclo_id)
        self.panel_cursos = PanelCursos(self.ciclo_id, on_cambio=self.panel_alumnos.recargar_cursos)

        self.tabs.addTab(self.panel_cursos, "Cursos")
        self.tabs.addTab(self.panel_alumnos, "Alumnos")
        layout_raiz.addWidget(self.tabs)

    def _armar_barra_titulo(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(44)
        barra.setStyleSheet(f"background-color: {COLOR_FONDO}; border-bottom: 1px solid {COLOR_BORDE};")

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(20, 0, 12, 0)
        layout.setSpacing(8)

        titulo = QLabel("Panel de Administrador")
        titulo.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        titulo.setStyleSheet(f"color: {COLOR_TEXTO};")
        layout.addWidget(titulo)
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
