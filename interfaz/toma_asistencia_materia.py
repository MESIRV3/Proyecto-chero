"""Componente para toma de asistencia de cátedra por materia (Rol Profesor)."""
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QDateEdit,
)

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
    _estilo_input,
    _estilo_scrollbar,
    _etiqueta,
    _tarjeta,
)
from servicios import asistencia as servicio_asistencia
from servicios import horario as servicio_horario


class FilaTomaMateria(QFrame):
    """Fila para registrar presentismo de un alumno en una materia con soporte de atajos de teclado."""

    def __init__(self, index: int, alumno: dict, on_cambio=None, on_navegar=None):
        super().__init__()
        self.alumno = alumno
        self.on_cambio = on_cambio
        self.on_navegar = on_navegar
        self.estado = alumno.get("estado") or "presente"

        self.texto_busqueda = (
            f"{alumno['numero']} {alumno['apellido']} {alumno['nombre']} {alumno.get('dni') or ''}".lower()
        )

        self.setFixedHeight(54)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_BORDE};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: #1e222d;
                border: 1px solid #3b4252;
            }}
            QFrame:focus {{
                border: 1px solid {COLOR_ACENTO};
                background-color: rgba(37, 99, 235, 0.08);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # 1. Badge Legajo
        lbl_legajo = QLabel(f"#{alumno['numero']}")
        lbl_legajo.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_legajo.setStyleSheet(f"""
            color: {COLOR_TEXTO_TENUE};
            background-color: {COLOR_INPUT};
            border: 1px solid {COLOR_BORDE};
            border-radius: 6px;
            padding: 4px 8px;
        """)
        layout.addWidget(lbl_legajo)

        # 2. Nombre del Alumno
        nombre_completo = f"{alumno['apellido'].upper()}, {alumno['nombre']}"
        lbl_nombre = QLabel(nombre_completo)
        lbl_nombre.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        lbl_nombre.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout.addWidget(lbl_nombre, stretch=1)

        # 3. DNI
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
        lbl_dni.setFont(QFont(FUENTE_MONO, 11))
        lbl_dni.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        layout.addWidget(lbl_dni)

        # 4. Campo de Observaciones
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Observación opcional...")
        self.input_obs.setText(alumno.get("observaciones") or "")
        self.input_obs.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_BORDE};
                border-radius: 6px;
                color: {COLOR_TEXTO};
                padding: 6px 10px;
                font-size: 12px;
                font-family: '{FUENTE_MONO}';
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
        """)
        self.input_obs.setFixedWidth(200)
        layout.addWidget(self.input_obs)

        # 5. Botones Presente / Ausente
        self.btn_presente = QPushButton("Presente")
        self.btn_presente.setCursor(Qt.PointingHandCursor)
        self.btn_presente.setToolTip("Marcar Presente [1 / P]")
        self.btn_presente.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
        self.btn_presente.setFixedHeight(30)
        self.btn_presente.clicked.connect(lambda: self.set_estado("presente"))
        layout.addWidget(self.btn_presente)

        self.btn_ausente = QPushButton("Ausente")
        self.btn_ausente.setCursor(Qt.PointingHandCursor)
        self.btn_ausente.setToolTip("Marcar Ausente [2 / A]")
        self.btn_ausente.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
        self.btn_ausente.setFixedHeight(30)
        self.btn_ausente.clicked.connect(lambda: self.set_estado("ausente"))
        layout.addWidget(self.btn_ausente)

        self._actualizar_botones()

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key_1, Qt.Key_P):
            self.set_estado("presente")
            if self.on_navegar:
                self.on_navegar(1)
            event.accept()
        elif k in (Qt.Key_2, Qt.Key_A):
            self.set_estado("ausente")
            if self.on_navegar:
                self.on_navegar(1)
            event.accept()
        elif k in (Qt.Key_Down, Qt.Key_J):
            if self.on_navegar:
                self.on_navegar(1)
            event.accept()
        elif k in (Qt.Key_Up, Qt.Key_K):
            if self.on_navegar:
                self.on_navegar(-1)
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_estado(self, nuevo_estado: str):
        self.estado = nuevo_estado
        self._actualizar_botones()
        if self.on_cambio:
            self.on_cambio()

    def _actualizar_botones(self):
        if self.estado == "presente":
            self.btn_presente.setStyleSheet("""
                QPushButton {
                    background-color: rgba(74, 222, 128, 0.15);
                    border: 1px solid #4ade80;
                    color: #4ade80;
                    border-radius: 6px;
                    padding: 4px 14px;
                }
            """)
            self.btn_ausente.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    color: {COLOR_TEXTO_TENUE};
                    border-radius: 6px;
                    padding: 4px 14px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.07);
                    color: {COLOR_TEXTO};
                }}
            """)
        else:
            self.btn_presente.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    color: {COLOR_TEXTO_TENUE};
                    border-radius: 6px;
                    padding: 4px 14px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.07);
                    color: {COLOR_TEXTO};
                }}
            """)
            self.btn_ausente.setStyleSheet("""
                QPushButton {
                    background-color: rgba(248, 113, 113, 0.15);
                    border: 1px solid #f87171;
                    color: #f87171;
                    border-radius: 6px;
                    padding: 4px 14px;
                }
            """)

    def obtener_registro(self) -> dict:
        return {
            "alumno_numero": self.alumno["numero"],
            "estado": self.estado,
            "observaciones": self.input_obs.text().strip(),
        }


class VistaTomaAsistenciaMateria(QWidget):
    """Vista completa para la toma de asistencia de una materia en un curso."""

    asistencia_guardada = Signal()

    def __init__(self, on_volver=None, parent=None):
        super().__init__(parent)
        self.on_volver = on_volver
        self.curso_actual = None
        self.usuario_actual = None
        self.filas_alumnos: list[FilaTomaMateria] = []

        self._armar_ui()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # --- Fila superior: Volver, Título, Materia y Fecha ---
        header = QHBoxLayout()
        header.setSpacing(12)

        self.btn_volver = QPushButton("← Volver al curso")
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.setStyleSheet(_estilo_boton_secundario())
        if self.on_volver:
            self.btn_volver.clicked.connect(self.on_volver)
        header.addWidget(self.btn_volver)

        self.lbl_titulo = QLabel("Asistencia de Cátedra")
        self.lbl_titulo.setFont(QFont(FUENTE_MONO, 16, QFont.Bold))
        self.lbl_titulo.setStyleSheet(f"color: {COLOR_TEXTO};")
        header.addWidget(self.lbl_titulo)

        header.addStretch()

        header.addWidget(_etiqueta("Materia:", tenue=True))
        self.combo_materia = QComboBox()
        self.combo_materia.setStyleSheet(_estilo_input())
        self.combo_materia.setMinimumWidth(200)
        self.combo_materia.currentIndexChanged.connect(self._al_cambiar_materia_o_fecha)
        header.addWidget(self.combo_materia)

        header.addWidget(_etiqueta("Fecha:", tenue=True))
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setFixedWidth(135)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setStyleSheet(_estilo_input())
        self.date_picker.dateChanged.connect(self._al_cambiar_materia_o_fecha)
        header.addWidget(self.date_picker)

        layout.addLayout(header)

        # --- Tarjeta de métricas y acciones rápidas ---
        tarjeta_control = _tarjeta()
        layout_control = QHBoxLayout(tarjeta_control)
        layout_control.setContentsMargins(18, 12, 18, 12)
        layout_control.setSpacing(12)

        self.lbl_metricas = QLabel("👥 0 Alumnos  |  🟢 0 Presentes  ·  🔴 0 Ausentes")
        self.lbl_metricas.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_metricas.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
        layout_control.addWidget(self.lbl_metricas)

        layout_control.addStretch()

        btn_todos_presentes = QPushButton("✔ Marcar todos presentes")
        btn_todos_presentes.setCursor(Qt.PointingHandCursor)
        btn_todos_presentes.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        btn_todos_presentes.clicked.connect(self._marcar_todos_presentes)
        layout_control.addWidget(btn_todos_presentes)

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Filtrar alumnos...")
        self.input_buscar.setStyleSheet(_estilo_input())
        self.input_buscar.setFixedWidth(200)
        self.input_buscar.textChanged.connect(self._filtrar_alumnos)
        layout_control.addWidget(self.input_buscar)

        lbl_atajos = QLabel("💡 1/P: Presente · 2/A: Ausente · ↑/↓: Navegar")
        lbl_atajos.setFont(QFont(FUENTE_MONO, 11))
        lbl_atajos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding-left: 6px;")
        layout_control.addWidget(lbl_atajos)

        layout.addWidget(tarjeta_control)

        # --- ScrollArea con alumnos ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {COLOR_ACENTO}; border-radius: 4px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {COLOR_ACENTO_HOVER}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.contenedor_filas = QWidget()
        self.contenedor_filas.setStyleSheet("background: transparent;")
        self.layout_filas = QVBoxLayout(self.contenedor_filas)
        self.layout_filas.setContentsMargins(0, 4, 0, 4)
        self.layout_filas.setSpacing(8)

        self.lbl_sin_alumnos = QLabel("No hay alumnos para mostrar.")
        self.lbl_sin_alumnos.setFont(QFont(FUENTE_MONO, 11))
        self.lbl_sin_alumnos.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; padding: 30px;")
        self.lbl_sin_alumnos.setAlignment(Qt.AlignCenter)
        self.lbl_sin_alumnos.hide()
        self.layout_filas.addWidget(self.lbl_sin_alumnos)

        self.scroll_area.setWidget(self.contenedor_filas)
        layout.addWidget(self.scroll_area, stretch=1)

        # --- Fila inferior: Feedback y Botón Guardar ---
        fila_footer = QHBoxLayout()
        self.lbl_feedback = QLabel()
        self.lbl_feedback.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_feedback.hide()
        fila_footer.addWidget(self.lbl_feedback)

        fila_footer.addStretch()

        self.btn_guardar = QPushButton("💾 Guardar Asistencia de Cátedra")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
        self.btn_guardar.setStyleSheet(_estilo_boton("#1e3a29", "#284e37"))
        self.btn_guardar.clicked.connect(self._guardar)
        fila_footer.addWidget(self.btn_guardar)

        layout.addLayout(fila_footer)

    def configurar(
        self,
        curso: dict,
        usuario_actual: dict,
        materia_id_inicial: int | None = None,
        fecha_inicial: QDate | None = None,
    ):
        """Inicializa la vista para un curso y profesor específico."""
        self.curso_actual = curso
        self.usuario_actual = usuario_actual

        anio_div = f"{curso['anio']}°{curso['division']}"
        self.lbl_titulo.setText(f"📝 Asistencia de Cátedra · {anio_div}")

        if fecha_inicial:
            self.date_picker.blockSignals(True)
            self.date_picker.setDate(fecha_inicial)
            self.date_picker.blockSignals(False)

        # Cargar materias del profesor para este curso
        self.combo_materia.blockSignals(True)
        self.combo_materia.clear()

        prof_id = usuario_actual.get("id") if usuario_actual.get("rol") == "profesor" else None
        res_mat = servicio_horario.listar_materias_de_profesor_en_curso(curso["id"], prof_id)
        if res_mat.ok and res_mat.datos:
            for m in res_mat.datos:
                self.combo_materia.addItem(m["nombre"], m["id"])
            if materia_id_inicial:
                idx = self.combo_materia.findData(materia_id_inicial)
                if idx >= 0:
                    self.combo_materia.setCurrentIndex(idx)
        else:
            self.combo_materia.addItem("(Sin materias asignadas)", None)

        self.combo_materia.blockSignals(False)
        self._recargar_asistencia()

    def _al_cambiar_materia_o_fecha(self):
        self._recargar_asistencia()

    def _recargar_asistencia(self):
        if not self.curso_actual:
            return

        materia_id = self.combo_materia.currentData()
        fecha_str = self.date_picker.date().toString("yyyy-MM-dd")

        # Limpiar filas previas
        for fila in self.filas_alumnos:
            self.layout_filas.removeWidget(fila)
            fila.deleteLater()
        self.filas_alumnos.clear()

        for i in reversed(range(self.layout_filas.count())):
            item = self.layout_filas.itemAt(i)
            w = item.widget()
            if w and w != self.lbl_sin_alumnos:
                self.layout_filas.removeWidget(w)
                w.deleteLater()
            elif not w:
                self.layout_filas.removeItem(item)

        self.lbl_sin_alumnos.hide()
        self.lbl_feedback.hide()

        if not materia_id:
            self.lbl_sin_alumnos.setText("No hay una materia válida seleccionada.")
            self.lbl_sin_alumnos.show()
            self._actualizar_metricas()
            return

        res = servicio_asistencia.obtener_asistencia_materia(
            self.curso_actual["id"], materia_id, fecha_str
        )
        if not res.ok:
            self.lbl_sin_alumnos.setText(f"Error: {res.mensaje}")
            self.lbl_sin_alumnos.show()
            return

        alumnos = res.datos["alumnos"]
        if not alumnos:
            self.lbl_sin_alumnos.setText("No hay alumnos matriculados en este curso.")
            self.lbl_sin_alumnos.show()
        else:
            for idx, al in enumerate(alumnos, 1):
                fila = FilaTomaMateria(
                    idx,
                    al,
                    on_cambio=self._actualizar_metricas,
                    on_navegar=lambda delta, i=idx - 1: self._navegar_fila(i, delta),
                )
                self.layout_filas.addWidget(fila)
                self.filas_alumnos.append(fila)

        self.layout_filas.addStretch()
        self._actualizar_metricas()

    def _navegar_fila(self, idx: int, delta: int):
        siguiente = idx + delta
        if 0 <= siguiente < len(self.filas_alumnos):
            self.filas_alumnos[siguiente].setFocus()

    def _actualizar_metricas(self):
        total = len(self.filas_alumnos)
        presentes = sum(1 for f in self.filas_alumnos if f.estado == "presente")
        ausentes = sum(1 for f in self.filas_alumnos if f.estado == "ausente")
        self.lbl_metricas.setText(
            f"👥 {total} Alumnos  |  🟢 {presentes} Presentes  ·  🔴 {ausentes} Ausentes"
        )

    def _marcar_todos_presentes(self):
        for f in self.filas_alumnos:
            f.set_estado("presente")
        self._actualizar_metricas()

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
            self.lbl_sin_alumnos.setText("No se encontraron alumnos que coincidan con la búsqueda.")
            self.lbl_sin_alumnos.show()
        else:
            self.lbl_sin_alumnos.hide()

    def _guardar(self):
        if not self.curso_actual or not self.filas_alumnos:
            return

        materia_id = self.combo_materia.currentData()
        if not materia_id:
            QMessageBox.warning(self, "Atención", "Selecciona una materia válida para guardar asistencia.")
            return

        fecha_str = self.date_picker.date().toString("yyyy-MM-dd")
        registros = [f.obtener_registro() for f in self.filas_alumnos]
        profesor_id = self.usuario_actual.get("id", 1) if self.usuario_actual else 1

        res = servicio_asistencia.guardar_asistencia_materia(
            materia_id=materia_id,
            fecha=fecha_str,
            registros=registros,
            profesor_id=profesor_id,
        )

        if res.ok:
            QMessageBox.information(
                self,
                "Asistencia Registrada",
                f"Se guardó la asistencia de cátedra para el día {fecha_str} con éxito.",
            )
            self.lbl_feedback.setText(f"✔ Asistencia guardada ({fecha_str})")
            self.lbl_feedback.setStyleSheet("color: #4ade80;")
            self.lbl_feedback.show()
            self.asistencia_guardada.emit()
        else:
            QMessageBox.critical(self, "Error al guardar", res.mensaje)
