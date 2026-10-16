"""Dialogo modal para consultar, agregar y eliminar horarios de un curso."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.conexion import conexion
from interfaz.estilos import (
    COLOR_ACENTO,
    COLOR_ACENTO_HOVER,
    COLOR_BORDE,
    COLOR_FONDO,
    COLOR_INPUT,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_TARJETA,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_input,
    _estilo_tabla,
    _estilo_scrollbar,
    _etiqueta,
    _tarjeta,
)
from servicios import curso as servicio_curso
from servicios import horario as servicio_horario


class DialogoHorarios(QDialog):
    """Ventana modal para gestionar la grilla de horarios de un curso."""

    horarios_actualizados = Signal()

    def __init__(
        self,
        curso: dict,
        usuario_actual: dict | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.curso = curso
        self.usuario_actual = usuario_actual or {"id": 1, "nombre": "Admin", "rol": "admin"}
        self.curso_id = curso["id"]

        nombre_curso = servicio_curso.obtener_nombre_curso(curso)
        self.setWindowTitle(f"Horarios de Clase — {nombre_curso}")
        self.setMinimumSize(700, 560)
        self.resize(760, 620)
        self.setStyleSheet(f"background-color: {COLOR_FONDO}; color: {COLOR_TEXTO};\n{_estilo_scrollbar()}")

        self._armar_ui(nombre_curso)
        self.recargar_materias()
        self.recargar_horarios()

    def _armar_ui(self, nombre_curso: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # --- Encabezado ---
        header = QHBoxLayout()
        col_tit = QVBoxLayout()
        lbl_titulo = QLabel(f"⏰ Horarios de {nombre_curso}")
        lbl_titulo.setFont(QFont(FUENTE_MONO, 16, QFont.Bold))
        lbl_titulo.setStyleSheet(f"color: {COLOR_TEXTO};")
        col_tit.addWidget(lbl_titulo)

        sub_info = (
            f"Turno: {self.curso.get('turno', '—')}  ·  "
            f"Especialidad: {self.curso.get('especialidad') or 'Ciclo Básico'}  ·  "
            f"Alumnos: {self.curso.get('cantidad_alumnos', 0)}"
        )
        lbl_sub = QLabel(sub_info)
        lbl_sub.setFont(QFont(FUENTE_MONO, 10))
        lbl_sub.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        col_tit.addWidget(lbl_sub)
        header.addLayout(col_tit)
        header.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(_estilo_boton(COLOR_TARJETA, COLOR_ACENTO_HOVER))
        btn_cerrar.clicked.connect(self.accept)
        header.addWidget(btn_cerrar)
        layout.addLayout(header)

        # --- Mensaje de estado/error inline ---
        self.lbl_feedback = QLabel()
        self.lbl_feedback.setStyleSheet("padding: 4px; font-weight: bold;")
        self.lbl_feedback.hide()
        layout.addWidget(self.lbl_feedback)

        # --- Tabla de horarios registrados ---
        lbl_seccion_tabla = QLabel("Grilla horaria del curso")
        lbl_seccion_tabla.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_seccion_tabla.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        layout.addWidget(lbl_seccion_tabla)

        self.tabla_horarios = QTableWidget(0, 6)
        self.tabla_horarios.setHorizontalHeaderLabels(
            ["Día", "Hora", "Horario", "Materia", "Profesor", "Acción"]
        )
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla_horarios.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_horarios.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_horarios.setAlternatingRowColors(True)
        self.tabla_horarios.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla_horarios, stretch=1)

        # --- Formulario para agregar horario ---
        self.tarjeta_form = _tarjeta()
        form_layout = QVBoxLayout(self.tarjeta_form)
        form_layout.setContentsMargins(18, 14, 18, 14)
        form_layout.setSpacing(10)

        lbl_tit_form = QLabel("➕ Agregar nuevo horario de clase")
        lbl_tit_form.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_tit_form.setStyleSheet(f"color: {COLOR_TEXTO};")
        form_layout.addWidget(lbl_tit_form)

        grid = QGridLayout()
        grid.setSpacing(10)

        # 1. Día de la semana
        grid.addWidget(_etiqueta("Día:", tenue=True), 0, 0)
        self.combo_dia = QComboBox()
        self.combo_dia.setStyleSheet(_estilo_input())
        for dia_num, dia_nom in servicio_horario.DIAS_SEMANA.items():
            self.combo_dia.addItem(dia_nom, dia_num)
        grid.addWidget(self.combo_dia, 0, 1)

        # 2. Hora de clase
        grid.addWidget(_etiqueta("Hora:", tenue=True), 0, 2)
        self.combo_bloque = QComboBox()
        self.combo_bloque.setStyleSheet(_estilo_input())
        for b in range(1, 9):
            sug_ini, _ = servicio_horario.BLOQUES_DEFAULT.get(b, ("", ""))
            self.combo_bloque.addItem(f"{b}° Hora ({sug_ini})", b)
        self.combo_bloque.currentIndexChanged.connect(self._al_cambiar_bloque)
        grid.addWidget(self.combo_bloque, 0, 3)

        # 3. Horas inicio y fin
        grid.addWidget(_etiqueta("Desde:", tenue=True), 0, 4)
        self.input_hora_inicio = QLineEdit("07:30")
        self.input_hora_inicio.setFixedWidth(70)
        self.input_hora_inicio.setStyleSheet(_estilo_input())
        grid.addWidget(self.input_hora_inicio, 0, 5)

        grid.addWidget(_etiqueta("Hasta:", tenue=True), 0, 6)
        self.input_hora_fin = QLineEdit("08:10")
        self.input_hora_fin.setFixedWidth(70)
        self.input_hora_fin.setStyleSheet(_estilo_input())
        grid.addWidget(self.input_hora_fin, 0, 7)

        # Fila 2: Materia y Docente
        grid.addWidget(_etiqueta("Materia:", tenue=True), 1, 0)
        self.combo_materia = QComboBox()
        self.combo_materia.setStyleSheet(_estilo_input())
        self.combo_materia.currentIndexChanged.connect(self._al_cambiar_combo_materia)
        grid.addWidget(self.combo_materia, 1, 1, 1, 3)

        self.input_nueva_materia = QLineEdit()
        self.input_nueva_materia.setPlaceholderText("Nombre de la nueva materia...")
        self.input_nueva_materia.setStyleSheet(_estilo_input())
        self.input_nueva_materia.hide()
        grid.addWidget(self.input_nueva_materia, 1, 4, 1, 4)

        # Docente
        grid.addWidget(_etiqueta("Docente:", tenue=True), 2, 0)
        self.combo_docente = QComboBox()
        self.combo_docente.setStyleSheet(_estilo_input())
        self._cargar_combo_docentes()
        grid.addWidget(self.combo_docente, 2, 1, 1, 3)

        # Botón agregar
        self.btn_guardar_horario = QPushButton("✔ Guardar Horario")
        self.btn_guardar_horario.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_horario.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_guardar_horario.clicked.connect(self._guardar_horario)
        grid.addWidget(self.btn_guardar_horario, 2, 4, 1, 4)

        form_layout.addLayout(grid)
        layout.addWidget(self.tarjeta_form)

    def _cargar_combo_docentes(self):
        """Llena el combo de docentes y preselecciona al usuario actual si es profesor."""
        self.combo_docente.clear()
        try:
            with conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, nombre, apellido FROM usuario WHERE rol = 'profesor' AND activo = 1 ORDER BY apellido, nombre"
                )
                profesores = cursor.fetchall()
                for p in profesores:
                    nombre_completo = f"{p['apellido']}, {p['nombre']}"
                    self.combo_docente.addItem(nombre_completo, p["id"])
        except Exception:
            pass

        # Si el usuario actual es un profesor, preseleccionarlo y fijarlo
        if self.usuario_actual.get("rol") == "profesor":
            idx = self.combo_docente.findData(self.usuario_actual.get("id"))
            if idx >= 0:
                self.combo_docente.setCurrentIndex(idx)
                self.combo_docente.setEnabled(False)

    def _al_cambiar_bloque(self, index: int):
        bloque = self.combo_bloque.currentData()
        if bloque in servicio_horario.BLOQUES_DEFAULT:
            inicio, fin = servicio_horario.BLOQUES_DEFAULT[bloque]
            self.input_hora_inicio.setText(inicio)
            self.input_hora_fin.setText(fin)

    def _al_cambiar_combo_materia(self, index: int):
        data = self.combo_materia.currentData()
        if data == "__nueva__":
            self.input_nueva_materia.show()
            self.input_nueva_materia.setFocus()
        else:
            self.input_nueva_materia.hide()

    def recargar_materias(self):
        self.combo_materia.clear()
        res = servicio_horario.listar_materias_de_curso(self.curso_id)
        if res.ok:
            for m in res.datos:
                self.combo_materia.addItem(m["nombre"], m["id"])
        self.combo_materia.addItem("➕ Nueva materia...", "__nueva__")

    def recargar_horarios(self):
        res = servicio_horario.listar_horarios_de_curso(self.curso_id)
        if not res.ok:
            self._mostrar_feedback(res.mensaje, error=True)
            return

        horarios = res.datos
        self.tabla_horarios.setRowCount(len(horarios))
        for fila, h in enumerate(horarios):
            dia_txt = servicio_horario.DIAS_SEMANA.get(h["dia_semana"], f"Día {h['dia_semana']}")
            bloque_txt = f"{h['numero_bloque']}° Hora"
            rango_txt = f"{h['hora_inicio']} - {h['hora_fin']}"
            mat_txt = h.get("materia_nombre") or "—"
            prof_txt = h.get("profesor_nombre") or "—"

            self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(dia_txt))
            self.tabla_horarios.setItem(fila, 1, QTableWidgetItem(bloque_txt))
            self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(rango_txt))
            self.tabla_horarios.setItem(fila, 3, QTableWidgetItem(mat_txt))
            self.tabla_horarios.setItem(fila, 4, QTableWidgetItem(prof_txt))

            # Botón de eliminar horario
            btn_eliminar = QPushButton("✕ Quitar")
            btn_eliminar.setCursor(Qt.PointingHandCursor)
            btn_eliminar.setStyleSheet(_estilo_boton(COLOR_PELIGRO, COLOR_PELIGRO_HOVER))
            btn_eliminar.setFixedHeight(26)
            horario_id = h["id"]
            btn_eliminar.clicked.connect(lambda _, hid=horario_id: self._eliminar_horario(hid))
            self.tabla_horarios.setCellWidget(fila, 5, btn_eliminar)

    def _guardar_horario(self):
        dia_semana = self.combo_dia.currentData()
        bloque = self.combo_bloque.currentData()
        hora_inicio = self.input_hora_inicio.text().strip()
        hora_fin = self.input_hora_fin.text().strip()
        materia_data = self.combo_materia.currentData()
        usuario_id = self.combo_docente.currentData()

        if not usuario_id:
            self._mostrar_feedback("Debes seleccionar un docente para el horario", error=True)
            return

        # Resolver o crear materia
        if materia_data == "__nueva__":
            nombre_mat = self.input_nueva_materia.text().strip()
            if not nombre_mat:
                self._mostrar_feedback("Escribe el nombre de la nueva materia", error=True)
                return
            res_mat = servicio_horario.crear_materia_si_no_existe(self.curso_id, nombre_mat)
            if not res_mat.ok:
                self._mostrar_feedback(res_mat.mensaje, error=True)
                return
            materia_id = res_mat.datos["id"]
            self.recargar_materias()
        else:
            materia_id = materia_data

        # Guardar horario
        res = servicio_horario.agregar_horario(
            curso_id=self.curso_id,
            dia_semana=dia_semana,
            numero_bloque=bloque,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            materia_id=materia_id,
            usuario_id=usuario_id,
        )

        if not res.ok:
            self._mostrar_feedback(res.mensaje, error=True)
            return

        self._mostrar_feedback("✔ Horario agregado con éxito", error=False)
        self.input_nueva_materia.clear()
        self.input_nueva_materia.hide()
        self.recargar_horarios()
        self.horarios_actualizados.emit()

    def _eliminar_horario(self, horario_id: int):
        confirm = QMessageBox.question(
            self,
            "Eliminar Horario",
            "¿Estás seguro de eliminar este bloque horario?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        res = servicio_horario.eliminar_horario(horario_id)
        if not res.ok:
            self._mostrar_feedback(res.mensaje, error=True)
            return

        self._mostrar_feedback("Horario eliminado", error=False)
        self.recargar_horarios()
        self.horarios_actualizados.emit()

    def _mostrar_feedback(self, mensaje: str, error: bool = False):
        color = "#ff5c5c" if error else "#4ade80"
        self.lbl_feedback.setText(mensaje)
        self.lbl_feedback.setStyleSheet(f"color: {color}; font-weight: bold; padding: 4px;")
        self.lbl_feedback.show()
