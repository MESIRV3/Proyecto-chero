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
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QCheckBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont

from servicios import curso as servicio_curso
from servicios import alumno as servicio_alumno
from servicios import ciclo_lectivo as servicio_ciclo

FUENTE_MONO = "Courier New"

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
        self.input_division.setPlaceholderText("A, B, C...")
        self.input_division.setMaxLength(5)
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
        self.combo_turno.addItems(["Manana", "Tarde"])
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

        # --- Formulario de alta ---
        tarjeta_form = _tarjeta()
        form = QVBoxLayout(tarjeta_form)
        form.setContentsMargins(20, 16, 20, 16)
        form.setSpacing(10)

        fila1 = QHBoxLayout()
        fila1.setSpacing(12)

        col_numero = QVBoxLayout()
        col_numero.addWidget(_etiqueta("Numero de legajo", tenue=True))
        self.input_numero = QLineEdit()
        self.input_numero.setPlaceholderText("Ej: 1024")
        self.input_numero.setStyleSheet(_estilo_input())
        col_numero.addWidget(self.input_numero)
        fila1.addLayout(col_numero)

        col_dni = QVBoxLayout()
        col_dni.addWidget(_etiqueta("DNI (opcional)", tenue=True))
        self.input_dni = QLineEdit()
        self.input_dni.setPlaceholderText("Ej: 40123456")
        self.input_dni.setStyleSheet(_estilo_input())
        col_dni.addWidget(self.input_dni)
        fila1.addLayout(col_dni)
        form.addLayout(fila1)

        fila2 = QHBoxLayout()
        fila2.setSpacing(12)

        col_nombre = QVBoxLayout()
        col_nombre.addWidget(_etiqueta("Nombre", tenue=True))
        self.input_nombre = QLineEdit()
        self.input_nombre.setStyleSheet(_estilo_input())
        col_nombre.addWidget(self.input_nombre)
        fila2.addLayout(col_nombre)

        col_apellido = QVBoxLayout()
        col_apellido.addWidget(_etiqueta("Apellido", tenue=True))
        self.input_apellido = QLineEdit()
        self.input_apellido.setStyleSheet(_estilo_input())
        col_apellido.addWidget(self.input_apellido)
        fila2.addLayout(col_apellido)

        col_curso = QVBoxLayout()
        col_curso.addWidget(_etiqueta("Curso", tenue=True))
        self.combo_curso_alta = QComboBox()
        self.combo_curso_alta.setStyleSheet(_estilo_input())
        col_curso.addWidget(self.combo_curso_alta)
        fila2.addLayout(col_curso)
        form.addLayout(fila2)

        self.btn_agregar = QPushButton("+ Agregar alumno")
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.setStyleSheet(_estilo_boton())
        self.btn_agregar.clicked.connect(self._agregar_alumno)
        form.addWidget(self.btn_agregar, alignment=Qt.AlignRight)

        layout.addWidget(tarjeta_form)

        # --- Filtro ---
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

        # --- Tabla de alumnos ---
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Numero", "Apellido", "Nombre", "DNI", "Estado", "Curso ID"]
        )
        self.tabla.setColumnHidden(5, True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla)

        # --- Acciones sobre el seleccionado ---
        fila_acciones = QHBoxLayout()
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
        )
        if resultado.ok:
            self.input_numero.clear()
            self.input_dni.clear()
            self.input_nombre.clear()
            self.input_apellido.clear()
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
                a["dni"] or "-", estado, str(a["curso_id"]),
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
        self.setWindowFlags(Qt.FramelessWindowHint)

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
            }
            QPushButton:hover { background-color: #e5e5e5; }
        """

        btn_minimizar = QPushButton("_")
        btn_minimizar.setFixedSize(24, 24)
        btn_minimizar.setCursor(Qt.PointingHandCursor)
        btn_minimizar.setStyleSheet(estilo_btn_ventana)
        btn_minimizar.clicked.connect(self.showMinimized)

        btn_maximizar = QPushButton("[ ]")
        btn_maximizar.setFixedSize(24, 24)
        btn_maximizar.setCursor(Qt.PointingHandCursor)
        btn_maximizar.setStyleSheet(estilo_btn_ventana)
        btn_maximizar.clicked.connect(self._alternar_maximizar)

        btn_cerrar = QPushButton("X")
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(estilo_btn_ventana)
        btn_cerrar.clicked.connect(self.close)

        layout.addWidget(btn_minimizar)
        layout.addWidget(btn_maximizar)
        layout.addWidget(btn_cerrar)

        barra.mousePressEvent = self._barra_mouse_press
        barra.mouseMoveEvent = self._barra_mouse_move
        barra.mouseReleaseEvent = self._barra_mouse_release

        return barra

    def _alternar_maximizar(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _barra_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
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


if __name__ == "__main__":
    # Permite probar esta ventana de forma independiente:
    #   python -m interfaz.admin   (parado en la carpeta raiz del proyecto)
    app = QApplication(sys.argv)
    ventana = VentanaAdmin()
    ventana.show()
    sys.exit(app.exec())
