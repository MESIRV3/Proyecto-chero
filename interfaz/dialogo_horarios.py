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
    _estilo_boton_secundario,
    _estilo_boton_peligro,
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
        lbl_sub.setFont(QFont(FUENTE_MONO, 11))
        lbl_sub.setStyleSheet(f"color: {COLOR_TEXTO_TENUE};")
        col_tit.addWidget(lbl_sub)
        header.addLayout(col_tit)
        header.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(_estilo_boton_secundario())
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

        self.tabla_horarios = QTableWidget(0, 5)
        self.tabla_horarios.setHorizontalHeaderLabels(
            ["Día", "Horario", "Materia", "Profesor", "Acción"]
        )
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla_horarios.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_horarios.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_horarios.setAlternatingRowColors(True)
        self.tabla_horarios.setStyleSheet(_estilo_tabla())
        layout.addWidget(self.tabla_horarios, stretch=1)

        # --- Formulario para agregar horario ---
        self.tarjeta_form = _tarjeta()
        form_layout = QVBoxLayout(self.tarjeta_form)
        form_layout.setContentsMargins(18, 14, 18, 14)
        form_layout.setSpacing(12)

        lbl_tit_form = QLabel("➕ Asignar horario de clase")
        lbl_tit_form.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_tit_form.setStyleSheet(f"color: {COLOR_TEXTO};")
        form_layout.addWidget(lbl_tit_form)

        # Fila superior: Día, Materia y Docente
        fila_datos = QHBoxLayout()
        fila_datos.setSpacing(12)

        # 1. Día de la semana
        col_dia = QVBoxLayout()
        col_dia.setSpacing(4)
        col_dia.addWidget(_etiqueta("Día de la semana:", tenue=True))
        self.combo_dia = QComboBox()
        self.combo_dia.setStyleSheet(_estilo_input())
        for dia_num, dia_nom in servicio_horario.DIAS_SEMANA.items():
            self.combo_dia.addItem(dia_nom, dia_num)
        col_dia.addWidget(self.combo_dia)
        fila_datos.addLayout(col_dia, stretch=1)

        # 2. Materia
        col_mat = QVBoxLayout()
        col_mat.setSpacing(4)
        col_mat.addWidget(_etiqueta("Materia:", tenue=True))
        self.combo_materia = QComboBox()
        self.combo_materia.setStyleSheet(_estilo_input())
        self.combo_materia.currentIndexChanged.connect(self._al_cambiar_combo_materia)
        col_mat.addWidget(self.combo_materia)

        self.input_nueva_materia = QLineEdit()
        self.input_nueva_materia.setPlaceholderText("Nombre de la nueva materia...")
        self.input_nueva_materia.setStyleSheet(_estilo_input())
        self.input_nueva_materia.hide()
        col_mat.addWidget(self.input_nueva_materia)
        fila_datos.addLayout(col_mat, stretch=2)

        # 3. Docente
        col_doc = QVBoxLayout()
        col_doc.setSpacing(4)
        col_doc.addWidget(_etiqueta("Docente a cargo:", tenue=True))
        self.combo_docente = QComboBox()
        self.combo_docente.setStyleSheet(_estilo_input())
        self._cargar_combo_docentes()
        col_doc.addWidget(self.combo_docente)
        fila_datos.addLayout(col_doc, stretch=2)

        form_layout.addLayout(fila_datos)

        # Marco visual dedicado para ingresar el inicio y fin de la hora
        marco_horario = QFrame()
        marco_horario.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_BORDE};
                border-radius: 12px;
            }}
        """)
        layout_marco = QVBoxLayout(marco_horario)
        layout_marco.setContentsMargins(14, 10, 14, 10)
        layout_marco.setSpacing(8)

        # Fila de inputs de hora inicio y fin
        fila_inputs_hora = QHBoxLayout()
        fila_inputs_hora.setSpacing(10)

        lbl_icono_hora = QLabel("🕒")
        lbl_icono_hora.setFont(QFont(FUENTE_MONO, 13))
        lbl_icono_hora.setStyleSheet("background: transparent; border: none;")
        fila_inputs_hora.addWidget(lbl_icono_hora)

        lbl_inicio = _etiqueta("Hora Inicio:")
        fila_inputs_hora.addWidget(lbl_inicio)

        self.input_hora_inicio = QLineEdit("07:30")
        self.input_hora_inicio.setPlaceholderText("07:30")
        self.input_hora_inicio.setAlignment(Qt.AlignCenter)
        self.input_hora_inicio.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.input_hora_inicio.setFixedWidth(85)
        self.input_hora_inicio.setStyleSheet(_estilo_input())
        fila_inputs_hora.addWidget(self.input_hora_inicio)

        lbl_flecha = QLabel("➔")
        lbl_flecha.setFont(QFont(FUENTE_MONO, 11))
        lbl_flecha.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        fila_inputs_hora.addWidget(lbl_flecha)

        lbl_fin = _etiqueta("Hora Fin:")
        fila_inputs_hora.addWidget(lbl_fin)

        self.input_hora_fin = QLineEdit("08:50")
        self.input_hora_fin.setPlaceholderText("08:50")
        self.input_hora_fin.setAlignment(Qt.AlignCenter)
        self.input_hora_fin.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.input_hora_fin.setFixedWidth(85)
        self.input_hora_fin.setStyleSheet(_estilo_input())
        fila_inputs_hora.addWidget(self.input_hora_fin)

        fila_inputs_hora.addSpacing(16)

        self.btn_guardar_horario = QPushButton("✔ Guardar Horario")
        self.btn_guardar_horario.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_horario.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_guardar_horario.clicked.connect(self._guardar_horario)
        fila_inputs_hora.addWidget(self.btn_guardar_horario)

        fila_inputs_hora.addStretch()
        layout_marco.addLayout(fila_inputs_hora)

        # Fila de sugerencias / atajos rápidos
        fila_atajos = QHBoxLayout()
        fila_atajos.setSpacing(6)
        lbl_atajos = QLabel("Atajos habituales:")
        lbl_atajos.setFont(QFont(FUENTE_MONO, 9))
        lbl_atajos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        fila_atajos.addWidget(lbl_atajos)

        turnos_sugeridos = [
            ("07:30 - 08:50", "07:30", "08:50"),
            ("09:00 - 10:20", "09:00", "10:20"),
            ("10:30 - 11:50", "10:30", "11:50"),
            ("12:00 - 13:20", "12:00", "13:20"),
            ("13:30 - 14:50", "13:30", "14:50"),
            ("15:00 - 16:20", "15:00", "16:20"),
        ]
        for etiqueta_btn, h_ini, h_fin in turnos_sugeridos:
            btn_preset = QPushButton(etiqueta_btn)
            btn_preset.setCursor(Qt.PointingHandCursor)
            btn_preset.setFont(QFont(FUENTE_MONO, 8))
            btn_preset.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_TARJETA};
                    color: {COLOR_TEXTO_TENUE};
                    border: 1px solid {COLOR_BORDE};
                    border-radius: 6px;
                    padding: 3px 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACENTO_HOVER};
                    color: #ffffff;
                }}
            """)
            btn_preset.clicked.connect(lambda _, ini=h_ini, fin=h_fin: self._set_horario(ini, fin))
            fila_atajos.addWidget(btn_preset)

        fila_atajos.addStretch()
        layout_marco.addLayout(fila_atajos)

        form_layout.addWidget(marco_horario)
        layout.addWidget(self.tarjeta_form)

        # Si el rol es preceptor, el formulario de carga permanece oculto (solo lectura)
        if self.usuario_actual.get("rol") == "preceptor":
            self.tarjeta_form.hide()

    def _set_horario(self, inicio: str, fin: str):
        self.input_hora_inicio.setText(inicio)
        self.input_hora_fin.setText(fin)

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
            rango_txt = f"{h['hora_inicio']} - {h['hora_fin']}"
            mat_txt = h.get("materia_nombre") or "—"
            prof_txt = h.get("profesor_nombre") or "—"

            self.tabla_horarios.setItem(fila, 0, QTableWidgetItem(dia_txt))
            self.tabla_horarios.setItem(fila, 1, QTableWidgetItem(rango_txt))
            self.tabla_horarios.setItem(fila, 2, QTableWidgetItem(mat_txt))
            self.tabla_horarios.setItem(fila, 3, QTableWidgetItem(prof_txt))

            # Botón de eliminar horario con RBAC
            rol = self.usuario_actual.get("rol", "admin")
            usr_id = self.usuario_actual.get("id")
            horario_uid = h.get("usuario_id")

            puede_eliminar = False
            if rol in ("admin", "directivo"):
                puede_eliminar = True
            elif rol == "profesor" and usr_id and horario_uid and usr_id == horario_uid:
                puede_eliminar = True

            if puede_eliminar:
                btn_eliminar = QPushButton("✕ Quitar")
                btn_eliminar.setCursor(Qt.PointingHandCursor)
                btn_eliminar.setStyleSheet(_estilo_boton_peligro(11))
                btn_eliminar.setFixedHeight(28)
                horario_id = h["id"]
                btn_eliminar.clicked.connect(lambda _, hid=horario_id: self._eliminar_horario(hid))
                self.tabla_horarios.setCellWidget(fila, 4, btn_eliminar)
            else:
                lbl_bloqueado = QLabel("Asignado" if rol == "profesor" else "—")
                lbl_bloqueado.setFont(QFont(FUENTE_MONO, 11))
                lbl_bloqueado.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
                lbl_bloqueado.setAlignment(Qt.AlignCenter)
                self.tabla_horarios.setCellWidget(fila, 4, lbl_bloqueado)

    def _guardar_horario(self):
        dia_semana = self.combo_dia.currentData()
        hora_inicio = self.input_hora_inicio.text().strip()
        hora_fin = self.input_hora_fin.text().strip()
        materia_data = self.combo_materia.currentData()
        usuario_id = self.combo_docente.currentData()

        if not hora_inicio or not hora_fin:
            self._mostrar_feedback("Debes ingresar la hora de inicio y fin", error=True)
            return

        if hora_inicio >= hora_fin:
            self._mostrar_feedback("La hora de inicio debe ser anterior a la de fin", error=True)
            return

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
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            materia_id=materia_id,
            usuario_id=usuario_id,
        )

        if not res.ok:
            self._mostrar_feedback(res.mensaje, error=True)
            return

        self._mostrar_feedback("✔ Horario registrado con éxito", error=False)
        self.input_nueva_materia.clear()
        self.input_nueva_materia.hide()
        self.recargar_horarios()
        self.horarios_actualizados.emit()

    def _eliminar_horario(self, horario_id: int):
        rol = self.usuario_actual.get("rol", "admin")
        usr_id = self.usuario_actual.get("id")

        if rol not in ("admin", "directivo", "profesor"):
            self._mostrar_feedback("No tienes permisos para eliminar horarios.", error=True)
            return

        if rol == "profesor":
            res_lista = servicio_horario.listar_horarios_de_curso(self.curso_id)
            if res_lista.ok:
                horario_target = next((h for h in res_lista.datos if h["id"] == horario_id), None)
                if horario_target and horario_target.get("usuario_id") != usr_id:
                    self._mostrar_feedback("Solo puedes eliminar tus propios horarios de clase.", error=True)
                    return

        confirm = QMessageBox.question(
            self,
            "Eliminar Horario",
            "¿Estás seguro de eliminar este horario de clase?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        res = servicio_horario.eliminar_horario(horario_id)
        if not res.ok:
            self._mostrar_feedback(res.mensaje, error=True)
            return

        self._mostrar_feedback("Horario eliminado correctamente.", error=False)
        self.recargar_horarios()
        self.horarios_actualizados.emit()

    def _mostrar_feedback(self, mensaje: str, error: bool = False):
        color = "#ff5c5c" if error else "#4ade80"
        self.lbl_feedback.setText(mensaje)
        self.lbl_feedback.setStyleSheet(f"color: {color}; font-weight: bold; padding: 4px;")
        self.lbl_feedback.show()
