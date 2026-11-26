"""Panel de gestion de personal: asignacion de cursos a preceptores y horarios a profesores.

Disponible exclusivamente para los roles Administrador ('admin') y Directivo ('directivo').
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from interfaz.estilos import (
    COLOR_ACENTO,
    COLOR_ACENTO_HOVER,
    COLOR_BORDE,
    COLOR_EXITO,
    COLOR_INPUT,
    COLOR_PELIGRO_HOVER,
    COLOR_TARJETA,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_boton_peligro,
    _estilo_boton_secundario,
    _estilo_input,
    _estilo_scrollbar,
    _estilo_tabla,
    _etiqueta,
    _subtitulo,
    _tarjeta,
    _titulo,
)
from servicios import curso as servicio_curso
from servicios import horario as servicio_horario
from servicios import preceptor as servicio_preceptor


def _estilo_tabs_personal() -> str:
    return f"""
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDE};
            border-radius: 12px;
            background-color: transparent;
            top: -1px;
        }}
        QTabBar::tab {{
            background: #18191d;
            color: {COLOR_TEXTO_TENUE};
            padding: 9px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
            font-family: '{FUENTE_MONO}';
            font-weight: bold;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{
            background: {COLOR_ACENTO};
            color: #ffffff;
        }}
        QTabBar::tab:hover:!selected {{
            background: #23252e;
            color: #ffffff;
        }}
    """


def _estilo_lista_personal() -> str:
    return f"""
        QListWidget {{
            background-color: {COLOR_INPUT};
            border: 1px solid {COLOR_BORDE};
            border-radius: 10px;
            color: {COLOR_TEXTO};
            padding: 6px;
            outline: none;
            font-family: '{FUENTE_MONO}';
            font-size: 12px;
        }}
        QListWidget::item {{
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 4px;
            color: {COLOR_TEXTO};
        }}
        QListWidget::item:hover:!selected {{
            background-color: #232732;
        }}
        QListWidget::item:selected {{
            background-color: {COLOR_ACENTO};
            color: #ffffff;
            font-weight: bold;
        }}
        {_estilo_scrollbar()}
    """


class PanelPersonal(QWidget):
    """Gestion de asignaciones de cursos a preceptores y horarios a profesores."""

    asignaciones_actualizadas = Signal()

    def __init__(self, ciclo_id: int | None, rol_actual: str = "admin"):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.rol_actual = rol_actual

        self.cursos_ciclo: list[dict] = []
        self.preceptores: list[dict] = []
        self.preceptor_seleccionado: dict | None = None
        self.checks_cursos: dict[int, QCheckBox] = {}
        self.filas_curso_prec: list[tuple[str, QFrame]] = []

        self.profesores: list[dict] = []
        self.profesor_seleccionado: dict | None = None

        self._armar_ui()
        self.recargar()

    def cambiar_rol(self, nuevo_rol: str, usuario_id: int | None = None):
        """Actualiza el rol activo para validacion de permisos en acciones."""
        self.rol_actual = nuevo_rol

    def showEvent(self, event):
        super().showEvent(event)
        self.recargar()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Encabezado
        header = QVBoxLayout()
        header.setSpacing(4)
        header.addWidget(_titulo("Gestión de Personal y Asignaciones", 18))
        header.addWidget(
            _subtitulo("Asigná los cursos a cargo de cada preceptor y la grilla horaria de cada profesor.", 12)
        )
        layout.addLayout(header)

        # Tabs principales
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_estilo_tabs_personal())

        self.tab_preceptores = QWidget()
        self._armar_tab_preceptores()
        self.tabs.addTab(self.tab_preceptores, "📋 Preceptores — Cursos a Cargo")

        self.tab_profesores = QWidget()
        self._armar_tab_profesores()
        self.tabs.addTab(self.tab_profesores, "👨‍🏫 Profesores — Horarios de Clase")

        layout.addWidget(self.tabs, stretch=1)

    # =====================================================================
    # TAB 1: PRECEPTORES -> CURSOS
    # =====================================================================
    def _armar_tab_preceptores(self):
        layout = QHBoxLayout(self.tab_preceptores)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Columna izquierda: listado de preceptores
        tarjeta_izq = _tarjeta()
        tarjeta_izq.setFixedWidth(280)
        lay_izq = QVBoxLayout(tarjeta_izq)
        lay_izq.setContentsMargins(14, 14, 14, 14)
        lay_izq.setSpacing(10)

        lay_izq.addWidget(_etiqueta("Preceptores activos", tenue=False, tamano=12, negrita=True))
        self.lista_preceptores = QListWidget()
        self.lista_preceptores.setStyleSheet(_estilo_lista_personal())
        self.lista_preceptores.currentItemChanged.connect(self._al_seleccionar_preceptor)
        lay_izq.addWidget(self.lista_preceptores, stretch=1)
        layout.addWidget(tarjeta_izq)

        # Columna derecha: cursos asignables
        tarjeta_der = _tarjeta()
        lay_der = QVBoxLayout(tarjeta_der)
        lay_der.setContentsMargins(18, 16, 18, 16)
        lay_der.setSpacing(12)

        # Encabezado preceptor seleccionado + filtro de turno
        fila_top = QHBoxLayout()
        col_tit = QVBoxLayout()
        col_tit.setSpacing(2)
        self.lbl_prec_nombre = _etiqueta("Seleccioná un preceptor", tenue=False, tamano=15, negrita=True)
        self.lbl_prec_sub = _etiqueta("Elegí un preceptor de la lista para gestionar sus cursos.", tenue=True, tamano=11)
        col_tit.addWidget(self.lbl_prec_nombre)
        col_tit.addWidget(self.lbl_prec_sub)
        fila_top.addLayout(col_tit)
        fila_top.addStretch()

        fila_top.addWidget(_etiqueta("Turno:", tenue=True, tamano=11))
        self.combo_filtro_turno = QComboBox()
        self.combo_filtro_turno.addItem("Todos", None)
        self.combo_filtro_turno.addItem("Mañana", "Mañana")
        self.combo_filtro_turno.addItem("Tarde", "Tarde")
        self.combo_filtro_turno.setStyleSheet(_estilo_input())
        self.combo_filtro_turno.currentIndexChanged.connect(self._filtrar_cursos_preceptor)
        fila_top.addWidget(self.combo_filtro_turno)
        lay_der.addLayout(fila_top)

        # Barra de resumen y acciones rapidas
        fila_meta = QHBoxLayout()
        self.lbl_prec_resumen = _etiqueta("0 cursos seleccionados", tenue=True, tamano=11)
        fila_meta.addWidget(self.lbl_prec_resumen)
        fila_meta.addStretch()

        self.btn_marcar_visibles = QPushButton("Marcar visibles")
        self.btn_marcar_visibles.setCursor(Qt.PointingHandCursor)
        self.btn_marcar_visibles.setStyleSheet(_estilo_boton_secundario(11))
        self.btn_marcar_visibles.clicked.connect(lambda: self._marcar_cursos_visibles(True))
        fila_meta.addWidget(self.btn_marcar_visibles)

        self.btn_desmarcar_visibles = QPushButton("Limpiar selección")
        self.btn_desmarcar_visibles.setCursor(Qt.PointingHandCursor)
        self.btn_desmarcar_visibles.setStyleSheet(_estilo_boton_secundario(11))
        self.btn_desmarcar_visibles.clicked.connect(lambda: self._marcar_cursos_visibles(False))
        fila_meta.addWidget(self.btn_desmarcar_visibles)
        lay_der.addLayout(fila_meta)

        # Area scrolleable de cursos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}\n{_estilo_scrollbar()}")

        self.contenedor_cursos_prec = QWidget()
        self.contenedor_cursos_prec.setStyleSheet("background: transparent;")
        self.layout_cursos_prec = QVBoxLayout(self.contenedor_cursos_prec)
        self.layout_cursos_prec.setContentsMargins(0, 4, 4, 4)
        self.layout_cursos_prec.setSpacing(8)
        scroll.setWidget(self.contenedor_cursos_prec)
        lay_der.addWidget(scroll, stretch=1)

        # Pie con feedback y boton guardar
        fila_pie = QHBoxLayout()
        self.lbl_feedback_prec = QLabel()
        self.lbl_feedback_prec.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_feedback_prec.setStyleSheet("background: transparent; border: none;")
        self.lbl_feedback_prec.hide()
        fila_pie.addWidget(self.lbl_feedback_prec)
        fila_pie.addStretch()

        self.btn_guardar_preceptor = QPushButton("✔ Guardar Cursos Asignados")
        self.btn_guardar_preceptor.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_preceptor.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_guardar_preceptor.clicked.connect(self._guardar_asignaciones_preceptor)
        fila_pie.addWidget(self.btn_guardar_preceptor)
        lay_der.addLayout(fila_pie)

        layout.addWidget(tarjeta_der, stretch=1)

    # =====================================================================
    # TAB 2: PROFESORES -> HORARIOS
    # =====================================================================
    def _armar_tab_profesores(self):
        layout = QHBoxLayout(self.tab_profesores)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Columna izquierda: listado de profesores
        tarjeta_izq = _tarjeta()
        tarjeta_izq.setFixedWidth(280)
        lay_izq = QVBoxLayout(tarjeta_izq)
        lay_izq.setContentsMargins(14, 14, 14, 14)
        lay_izq.setSpacing(10)

        lay_izq.addWidget(_etiqueta("Profesores activos", tenue=False, tamano=12, negrita=True))
        self.lista_profesores = QListWidget()
        self.lista_profesores.setStyleSheet(_estilo_lista_personal())
        self.lista_profesores.currentItemChanged.connect(self._al_seleccionar_profesor)
        lay_izq.addWidget(self.lista_profesores, stretch=1)
        layout.addWidget(tarjeta_izq)

        # Columna derecha: grilla de horarios + formulario de asignacion
        col_der = QVBoxLayout()
        col_der.setSpacing(12)

        # Encabezado del docente seleccionado
        tarjeta_head = _tarjeta()
        lay_head = QHBoxLayout(tarjeta_head)
        lay_head.setContentsMargins(18, 12, 18, 12)
        col_ht = QVBoxLayout()
        col_ht.setSpacing(2)
        self.lbl_prof_nombre = _etiqueta("Seleccioná un profesor", tenue=False, tamano=15, negrita=True)
        self.lbl_prof_sub = _etiqueta("Elegí un docente de la lista para consultar y asignar sus horarios.", tenue=True, tamano=11)
        col_ht.addWidget(self.lbl_prof_nombre)
        col_ht.addWidget(self.lbl_prof_sub)
        lay_head.addLayout(col_ht)
        lay_head.addStretch()

        self.lbl_feedback_prof = QLabel()
        self.lbl_feedback_prof.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.lbl_feedback_prof.setStyleSheet("background: transparent; border: none;")
        self.lbl_feedback_prof.hide()
        lay_head.addWidget(self.lbl_feedback_prof)
        col_der.addWidget(tarjeta_head)

        # Tabla de horarios del profesor
        self.tabla_horarios_prof = QTableWidget(0, 5)
        self.tabla_horarios_prof.setHorizontalHeaderLabels(
            ["Día", "Horario", "Curso", "Materia", "Acción"]
        )
        header_h = self.tabla_horarios_prof.horizontalHeader()
        header_h.setSectionResizeMode(QHeaderView.Stretch)
        header_h.setSectionResizeMode(0, QHeaderView.Fixed)
        header_h.setSectionResizeMode(1, QHeaderView.Fixed)
        header_h.setSectionResizeMode(4, QHeaderView.Fixed)
        self.tabla_horarios_prof.setColumnWidth(0, 96)
        self.tabla_horarios_prof.setColumnWidth(1, 118)
        self.tabla_horarios_prof.setColumnWidth(4, 112)
        self.tabla_horarios_prof.verticalHeader().setVisible(False)
        self.tabla_horarios_prof.verticalHeader().setDefaultSectionSize(44)
        self.tabla_horarios_prof.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_horarios_prof.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_horarios_prof.setAlternatingRowColors(True)
        self.tabla_horarios_prof.setStyleSheet(_estilo_tabla())
        col_der.addWidget(self.tabla_horarios_prof, stretch=1)

        # Formulario de asignacion de horario al profesor
        self.tarjeta_form_prof = _tarjeta()
        form_lay = QVBoxLayout(self.tarjeta_form_prof)
        form_lay.setContentsMargins(18, 16, 18, 16)
        form_lay.setSpacing(14)

        form_lay.addWidget(_etiqueta("➕ Asignar horario de clase al docente", tenue=False, tamano=12, negrita=True))

        fila_datos = QHBoxLayout()
        fila_datos.setSpacing(14)

        # 1. Curso
        col_curso = QVBoxLayout()
        col_curso.setSpacing(5)
        col_curso.addWidget(_etiqueta("Curso:", tenue=True, tamano=11))
        self.combo_curso_prof = QComboBox()
        self.combo_curso_prof.setFixedHeight(36)
        self.combo_curso_prof.setStyleSheet(_estilo_input())
        self.combo_curso_prof.currentIndexChanged.connect(self._cargar_materias_de_curso_seleccionado)
        col_curso.addWidget(self.combo_curso_prof)
        fila_datos.addLayout(col_curso, stretch=3)

        # 2. Dia
        col_dia = QVBoxLayout()
        col_dia.setSpacing(5)
        col_dia.addWidget(_etiqueta("Día:", tenue=True, tamano=11))
        self.combo_dia_prof = QComboBox()
        self.combo_dia_prof.setFixedSize(136, 36)
        self.combo_dia_prof.setStyleSheet(_estilo_input())
        for dia_num, dia_nom in servicio_horario.DIAS_SEMANA.items():
            self.combo_dia_prof.addItem(dia_nom, dia_num)
        col_dia.addWidget(self.combo_dia_prof)
        fila_datos.addLayout(col_dia, stretch=0)

        # 3. Materia
        col_mat = QVBoxLayout()
        col_mat.setSpacing(5)
        col_mat.addWidget(_etiqueta("Materia:", tenue=True, tamano=11))
        self.combo_materia_prof = QComboBox()
        self.combo_materia_prof.setFixedHeight(36)
        self.combo_materia_prof.setStyleSheet(_estilo_input())
        self.combo_materia_prof.currentIndexChanged.connect(self._al_cambiar_materia_prof)
        col_mat.addWidget(self.combo_materia_prof)

        self.input_nueva_materia_prof = QLineEdit()
        self.input_nueva_materia_prof.setFixedHeight(34)
        self.input_nueva_materia_prof.setPlaceholderText("Nombre de la nueva materia...")
        self.input_nueva_materia_prof.setStyleSheet(_estilo_input())
        self.input_nueva_materia_prof.hide()
        col_mat.addWidget(self.input_nueva_materia_prof)
        fila_datos.addLayout(col_mat, stretch=3)

        form_lay.addLayout(fila_datos)

        # Marco visual dedicado para hora inicio y fin
        marco_hora = QFrame()
        marco_hora.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_BORDE};
                border-radius: 10px;
            }}
        """)
        lay_marco = QVBoxLayout(marco_hora)
        lay_marco.setContentsMargins(16, 12, 16, 12)
        lay_marco.setSpacing(10)

        fila_hora = QHBoxLayout()
        fila_hora.setSpacing(10)

        lbl_ico = QLabel("🕒")
        lbl_ico.setFont(QFont(FUENTE_MONO, 13))
        lbl_ico.setStyleSheet("background: transparent; border: none;")
        fila_hora.addWidget(lbl_ico)

        fila_hora.addWidget(_etiqueta("Hora Inicio:", tenue=False, tamano=11))
        self.input_hora_inicio_prof = QLineEdit("07:30")
        self.input_hora_inicio_prof.setPlaceholderText("07:30")
        self.input_hora_inicio_prof.setAlignment(Qt.AlignCenter)
        self.input_hora_inicio_prof.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.input_hora_inicio_prof.setFixedSize(88, 34)
        self.input_hora_inicio_prof.setStyleSheet(_estilo_input())
        fila_hora.addWidget(self.input_hora_inicio_prof)

        lbl_flecha = QLabel("➔")
        lbl_flecha.setFont(QFont(FUENTE_MONO, 11))
        lbl_flecha.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        fila_hora.addWidget(lbl_flecha)

        fila_hora.addWidget(_etiqueta("Hora Fin:", tenue=False, tamano=11))
        self.input_hora_fin_prof = QLineEdit("08:50")
        self.input_hora_fin_prof.setPlaceholderText("08:50")
        self.input_hora_fin_prof.setAlignment(Qt.AlignCenter)
        self.input_hora_fin_prof.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        self.input_hora_fin_prof.setFixedSize(88, 34)
        self.input_hora_fin_prof.setStyleSheet(_estilo_input())
        fila_hora.addWidget(self.input_hora_fin_prof)

        fila_hora.addStretch()

        self.btn_asignar_horario_prof = QPushButton("✔ Asignar Horario")
        self.btn_asignar_horario_prof.setCursor(Qt.PointingHandCursor)
        self.btn_asignar_horario_prof.setFixedHeight(34)
        self.btn_asignar_horario_prof.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_asignar_horario_prof.clicked.connect(self._asignar_horario_profesor)
        fila_hora.addWidget(self.btn_asignar_horario_prof)
        lay_marco.addLayout(fila_hora)

        # Atajos habituales
        fila_atajos = QHBoxLayout()
        fila_atajos.setSpacing(8)
        lbl_at = QLabel("Atajos habituales:")
        lbl_at.setFont(QFont(FUENTE_MONO, 9))
        lbl_at.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
        fila_atajos.addWidget(lbl_at)

        for etiqueta_btn, h_ini, h_fin in [
            ("07:30 - 08:50", "07:30", "08:50"),
            ("09:00 - 10:20", "09:00", "10:20"),
            ("10:30 - 11:50", "10:30", "11:50"),
            ("12:00 - 13:20", "12:00", "13:20"),
            ("13:30 - 14:50", "13:30", "14:50"),
            ("15:00 - 16:20", "15:00", "16:20"),
        ]:
            btn_p = QPushButton(etiqueta_btn)
            btn_p.setCursor(Qt.PointingHandCursor)
            btn_p.setFont(QFont(FUENTE_MONO, 9))
            btn_p.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_TARJETA};
                    color: {COLOR_TEXTO_TENUE};
                    border: 1px solid {COLOR_BORDE};
                    border-radius: 6px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACENTO_HOVER};
                    border-color: {COLOR_ACENTO};
                    color: #ffffff;
                }}
            """)
            btn_p.clicked.connect(lambda _, ini=h_ini, fin=h_fin: self._set_horario_prof(ini, fin))
            fila_atajos.addWidget(btn_p)

        fila_atajos.addStretch()
        lay_marco.addLayout(fila_atajos)

        form_lay.addWidget(marco_hora)
        col_der.addWidget(self.tarjeta_form_prof)
        layout.addLayout(col_der, stretch=1)

    # =====================================================================
    # CARGA DE DATOS
    # =====================================================================
    def recargar(self):
        """Recarga cursos del ciclo, preceptores y profesores."""
        res_cursos = servicio_curso.listar_cursos(self.ciclo_id)
        self.cursos_ciclo = res_cursos.datos if res_cursos.ok else []

        self._recargar_lista_preceptores()
        self._recargar_cursos_combo_prof()
        self._recargar_lista_profesores()

    def _recargar_lista_preceptores(self):
        id_previo = self.preceptor_seleccionado["id"] if self.preceptor_seleccionado else None
        res = servicio_preceptor.listar_preceptores_con_conteo(self.ciclo_id)
        self.preceptores = res.datos if res.ok else []

        self.lista_preceptores.blockSignals(True)
        self.lista_preceptores.clear()
        fila_a_seleccionar = 0
        for idx, p in enumerate(self.preceptores):
            cant = p.get("cantidad_cursos", 0)
            sufijo = "curso" if cant == 1 else "cursos"
            texto = f"{p['apellido']}, {p['nombre']}\n@{p['username']}  ·  {cant} {sufijo}"
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, p["id"])
            self.lista_preceptores.addItem(item)
            if id_previo is not None and p["id"] == id_previo:
                fila_a_seleccionar = idx
        self.lista_preceptores.blockSignals(False)

        if self.preceptores:
            self.lista_preceptores.setCurrentRow(fila_a_seleccionar)
            self._al_seleccionar_preceptor(self.lista_preceptores.currentItem(), None)
        else:
            self.preceptor_seleccionado = None
            self.lbl_prec_nombre.setText("Sin preceptores activos")
            self.lbl_prec_sub.setText("No hay usuarios con rol preceptor cargados en el sistema.")
            self._poblar_cursos_de_preceptor(set())
            self.btn_guardar_preceptor.setEnabled(False)

    def _al_seleccionar_preceptor(self, current: QListWidgetItem | None, _previous):
        self.lbl_feedback_prec.hide()
        if not current:
            self.preceptor_seleccionado = None
            self.btn_guardar_preceptor.setEnabled(False)
            return

        pid = current.data(Qt.UserRole)
        self.preceptor_seleccionado = next((p for p in self.preceptores if p["id"] == pid), None)
        if not self.preceptor_seleccionado:
            return

        p = self.preceptor_seleccionado
        self.lbl_prec_nombre.setText(f"{p['apellido']}, {p['nombre']}")
        self.lbl_prec_sub.setText(f"Preceptor  ·  @{p['username']}")
        self.btn_guardar_preceptor.setEnabled(True)

        res = servicio_preceptor.listar_cursos_de_preceptor(pid, self.ciclo_id)
        asignados = {c["id"] for c in res.datos} if res.ok else set()
        self._poblar_cursos_de_preceptor(asignados)

    def _poblar_cursos_de_preceptor(self, cursos_asignados_ids: set[int]):
        self.checks_cursos.clear()
        self.filas_curso_prec.clear()

        while self.layout_cursos_prec.count() > 0:
            item = self.layout_cursos_prec.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.cursos_ciclo:
            lbl = _etiqueta("No hay cursos registrados en este ciclo lectivo.", tenue=True, tamano=11)
            lbl.setAlignment(Qt.AlignCenter)
            self.layout_cursos_prec.addWidget(lbl)
            self._actualizar_resumen_preceptor()
            return

        for curso in self.cursos_ciclo:
            cid = curso["id"]
            fila = QFrame()
            fila.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLOR_INPUT};
                    border: 1px solid {COLOR_BORDE};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    border-color: #475569;
                }}
            """)
            lay_f = QHBoxLayout(fila)
            lay_f.setContentsMargins(14, 10, 14, 10)
            lay_f.setSpacing(10)

            nombre = servicio_curso.obtener_nombre_curso(curso)
            chk = QCheckBox(nombre)
            chk.setCursor(Qt.PointingHandCursor)
            chk.setChecked(cid in cursos_asignados_ids)
            chk.setFont(QFont(FUENTE_MONO, 12, QFont.Bold))
            chk.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
            chk.stateChanged.connect(self._actualizar_resumen_preceptor)
            lay_f.addWidget(chk, stretch=1)

            lbl_al = _etiqueta(f"👥 {curso.get('cantidad_alumnos', 0)} alumnos", tenue=True, tamano=11)
            lay_f.addWidget(lbl_al)

            # Mostrar si otros preceptores tienen este curso asignado
            res_p = servicio_preceptor.listar_preceptores_de_curso(cid)
            if res_p.ok and res_p.datos:
                nombres_p = ", ".join(f"{x['apellido']} {x['nombre']}" for x in res_p.datos)
                lbl_asig = QLabel(f"📋 {nombres_p}")
                lbl_asig.setFont(QFont(FUENTE_MONO, 10))
                lbl_asig.setStyleSheet(f"""
                    color: {COLOR_TEXTO_TENUE};
                    background-color: {COLOR_TARJETA};
                    border: 1px solid {COLOR_BORDE};
                    border-radius: 6px;
                    padding: 3px 8px;
                """)
                lay_f.addWidget(lbl_asig)

            self.layout_cursos_prec.addWidget(fila)
            self.checks_cursos[cid] = chk
            self.filas_curso_prec.append((curso.get("turno", ""), fila))

        self.layout_cursos_prec.addStretch()
        self._filtrar_cursos_preceptor()
        self._actualizar_resumen_preceptor()

    def _filtrar_cursos_preceptor(self):
        turno_filtro = self.combo_filtro_turno.currentData()
        for turno_curso, fila in self.filas_curso_prec:
            fila.setVisible(turno_filtro is None or turno_curso == turno_filtro)

    def _marcar_cursos_visibles(self, estado: bool):
        turno_filtro = self.combo_filtro_turno.currentData()
        for curso in self.cursos_ciclo:
            if turno_filtro is None or curso.get("turno") == turno_filtro:
                chk = self.checks_cursos.get(curso["id"])
                if chk:
                    chk.setChecked(estado)

    def _actualizar_resumen_preceptor(self):
        seleccionados = sum(1 for chk in self.checks_cursos.values() if chk.isChecked())
        total = len(self.checks_cursos)
        self.lbl_prec_resumen.setText(f"{seleccionados} de {total} cursos seleccionados")

    def _guardar_asignaciones_preceptor(self):
        if self.rol_actual not in ("admin", "directivo"):
            self._mostrar_feedback_prec("No tenés permisos para asignar cursos.", error=True)
            return
        if not self.preceptor_seleccionado:
            self._mostrar_feedback_prec("Seleccioná un preceptor primero.", error=True)
            return

        pid = self.preceptor_seleccionado["id"]
        curso_ids = [cid for cid, chk in self.checks_cursos.items() if chk.isChecked()]
        res = servicio_preceptor.guardar_cursos_de_preceptor(pid, curso_ids, self.ciclo_id)
        if not res.ok:
            self._mostrar_feedback_prec(res.mensaje, error=True)
            return

        self._recargar_lista_preceptores()
        self._mostrar_feedback_prec(
            f"✔ Asignaciones guardadas ({len(curso_ids)} curso(s))",
            error=False,
        )
        self.asignaciones_actualizadas.emit()

    def _mostrar_feedback_prec(self, mensaje: str, error: bool = False):
        color = "#f87171" if error else COLOR_EXITO
        self.lbl_feedback_prec.setText(mensaje)
        self.lbl_feedback_prec.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self.lbl_feedback_prec.show()

    # =====================================================================
    # LOGICA DE PROFESORES -> HORARIOS
    # =====================================================================
    def _recargar_cursos_combo_prof(self):
        curso_previo = self.combo_curso_prof.currentData()
        self.combo_curso_prof.blockSignals(True)
        self.combo_curso_prof.clear()
        idx_previo = 0
        for idx, c in enumerate(self.cursos_ciclo):
            self.combo_curso_prof.addItem(servicio_curso.obtener_nombre_curso(c), c["id"])
            if curso_previo is not None and c["id"] == curso_previo:
                idx_previo = idx
        self.combo_curso_prof.blockSignals(False)
        if self.cursos_ciclo:
            self.combo_curso_prof.setCurrentIndex(idx_previo)
        self._cargar_materias_de_curso_seleccionado()

    def _cargar_materias_de_curso_seleccionado(self):
        self.combo_materia_prof.blockSignals(True)
        self.combo_materia_prof.clear()
        curso_id = self.combo_curso_prof.currentData()
        if curso_id is not None:
            res = servicio_horario.listar_materias_de_curso(curso_id)
            if res.ok:
                for m in res.datos:
                    self.combo_materia_prof.addItem(m["nombre"], m["id"])
        self.combo_materia_prof.addItem("➕ Nueva materia...", "__nueva__")
        self.combo_materia_prof.blockSignals(False)
        self._al_cambiar_materia_prof()

    def _al_cambiar_materia_prof(self):
        if self.combo_materia_prof.currentData() == "__nueva__":
            self.input_nueva_materia_prof.show()
        else:
            self.input_nueva_materia_prof.hide()

    def _set_horario_prof(self, inicio: str, fin: str):
        self.input_hora_inicio_prof.setText(inicio)
        self.input_hora_fin_prof.setText(fin)

    def _recargar_lista_profesores(self):
        id_previo = self.profesor_seleccionado["id"] if self.profesor_seleccionado else None
        res = servicio_horario.listar_profesores_con_conteo(self.ciclo_id)
        self.profesores = res.datos if res.ok else []

        self.lista_profesores.blockSignals(True)
        self.lista_profesores.clear()
        fila_a_seleccionar = 0
        for idx, p in enumerate(self.profesores):
            cant = p.get("cantidad_horarios", 0)
            sufijo = "clase" if cant == 1 else "clases"
            texto = f"{p['apellido']}, {p['nombre']}\n@{p['username']}  ·  {cant} {sufijo}"
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, p["id"])
            self.lista_profesores.addItem(item)
            if id_previo is not None and p["id"] == id_previo:
                fila_a_seleccionar = idx
        self.lista_profesores.blockSignals(False)

        if self.profesores:
            self.lista_profesores.setCurrentRow(fila_a_seleccionar)
            self._al_seleccionar_profesor(self.lista_profesores.currentItem(), None)
        else:
            self.profesor_seleccionado = None
            self.lbl_prof_nombre.setText("Sin profesores activos")
            self.lbl_prof_sub.setText("No hay usuarios con rol profesor cargados en el sistema.")
            self.tabla_horarios_prof.setRowCount(0)
            self.btn_asignar_horario_prof.setEnabled(False)

    def _al_seleccionar_profesor(self, current: QListWidgetItem | None, _previous):
        self.lbl_feedback_prof.hide()
        if not current:
            self.profesor_seleccionado = None
            self.btn_asignar_horario_prof.setEnabled(False)
            return

        pid = current.data(Qt.UserRole)
        self.profesor_seleccionado = next((p for p in self.profesores if p["id"] == pid), None)
        if not self.profesor_seleccionado:
            return

        p = self.profesor_seleccionado
        self.lbl_prof_nombre.setText(f"{p['apellido']}, {p['nombre']}")
        self.lbl_prof_sub.setText(f"Profesor  ·  @{p['username']}")
        self.btn_asignar_horario_prof.setEnabled(True)
        self._recargar_tabla_horarios_prof()

    def _recargar_tabla_horarios_prof(self):
        if not self.profesor_seleccionado:
            self.tabla_horarios_prof.setRowCount(0)
            return

        pid = self.profesor_seleccionado["id"]
        res = servicio_horario.listar_horarios_de_profesor(pid, self.ciclo_id)
        if not res.ok:
            self._mostrar_feedback_prof(res.mensaje, error=True)
            self.tabla_horarios_prof.setRowCount(0)
            return

        horarios = res.datos
        self.tabla_horarios_prof.clearSpans()
        self.tabla_horarios_prof.clearContents()
        self.tabla_horarios_prof.setRowCount(0)
        if not horarios:
            self.tabla_horarios_prof.setRowCount(1)
            item_vacio = QTableWidgetItem("Este docente todavía no tiene horarios asignados.")
            item_vacio.setTextAlignment(Qt.AlignCenter)
            self.tabla_horarios_prof.setItem(0, 0, item_vacio)
            self.tabla_horarios_prof.setSpan(0, 0, 1, 5)
            return

        self.tabla_horarios_prof.setRowCount(len(horarios))
        for fila, h in enumerate(horarios):
            self.tabla_horarios_prof.setRowHeight(fila, 44)
            dia_txt = servicio_horario.DIAS_SEMANA.get(h["dia_semana"], f"Día {h['dia_semana']}")
            rango_txt = f"{h['hora_inicio']} - {h['hora_fin']}"
            curso_txt = servicio_curso.obtener_nombre_curso(h)
            mat_txt = h.get("materia_nombre") or "—"

            self.tabla_horarios_prof.setItem(fila, 0, QTableWidgetItem(dia_txt))
            self.tabla_horarios_prof.setItem(fila, 1, QTableWidgetItem(rango_txt))
            self.tabla_horarios_prof.setItem(fila, 2, QTableWidgetItem(curso_txt))
            self.tabla_horarios_prof.setItem(fila, 3, QTableWidgetItem(mat_txt))

            contenedor_accion = QWidget()
            contenedor_accion.setStyleSheet("background: transparent; border: none;")
            lay_accion = QHBoxLayout(contenedor_accion)
            lay_accion.setContentsMargins(8, 4, 8, 4)
            lay_accion.setAlignment(Qt.AlignCenter)

            btn_quitar = QPushButton("✕ Quitar")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.setFixedSize(88, 28)
            btn_quitar.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(220, 38, 38, 0.14);
                    color: #fca5a5;
                    border: 1px solid rgba(239, 68, 68, 0.45);
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-family: '{FUENTE_MONO}';
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_PELIGRO_HOVER};
                    border-color: {COLOR_PELIGRO_HOVER};
                    color: #ffffff;
                }}
            """)
            hid = h["id"]
            btn_quitar.clicked.connect(lambda _, horario_id=hid: self._eliminar_horario_profesor(horario_id))
            lay_accion.addWidget(btn_quitar)
            self.tabla_horarios_prof.setCellWidget(fila, 4, contenedor_accion)

    def _asignar_horario_profesor(self):
        if self.rol_actual not in ("admin", "directivo"):
            self._mostrar_feedback_prof("No tenés permisos para asignar horarios.", error=True)
            return
        if not self.profesor_seleccionado:
            self._mostrar_feedback_prof("Seleccioná un profesor primero.", error=True)
            return

        curso_id = self.combo_curso_prof.currentData()
        if curso_id is None:
            self._mostrar_feedback_prof("No hay cursos disponibles en el ciclo.", error=True)
            return

        dia_semana = self.combo_dia_prof.currentData()
        hora_inicio = self.input_hora_inicio_prof.text().strip()
        hora_fin = self.input_hora_fin_prof.text().strip()
        materia_data = self.combo_materia_prof.currentData()
        profesor_id = self.profesor_seleccionado["id"]

        if not hora_inicio or not hora_fin:
            self._mostrar_feedback_prof("Ingresá hora de inicio y fin.", error=True)
            return
        if hora_inicio >= hora_fin:
            self._mostrar_feedback_prof("La hora de inicio debe ser anterior a la de fin.", error=True)
            return

        if materia_data == "__nueva__":
            nombre_mat = self.input_nueva_materia_prof.text().strip()
            if not nombre_mat:
                self._mostrar_feedback_prof("Escribí el nombre de la nueva materia.", error=True)
                return
            res_mat = servicio_horario.crear_materia_si_no_existe(curso_id, nombre_mat)
            if not res_mat.ok:
                self._mostrar_feedback_prof(res_mat.mensaje, error=True)
                return
            materia_id = res_mat.datos["id"]
            self._cargar_materias_de_curso_seleccionado()
        else:
            materia_id = materia_data

        res = servicio_horario.agregar_horario(
            curso_id=curso_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            materia_id=materia_id,
            usuario_id=profesor_id,
        )
        if not res.ok:
            self._mostrar_feedback_prof(res.mensaje, error=True)
            return

        self.input_nueva_materia_prof.clear()
        self.input_nueva_materia_prof.hide()
        self._recargar_lista_profesores()
        self._mostrar_feedback_prof("✔ Horario asignado correctamente", error=False)
        self.asignaciones_actualizadas.emit()

    def _eliminar_horario_profesor(self, horario_id: int):
        if self.rol_actual not in ("admin", "directivo"):
            self._mostrar_feedback_prof("No tenés permisos para eliminar horarios.", error=True)
            return

        confirm = QMessageBox.question(
            self,
            "Eliminar Horario",
            "¿Seguro que querés quitar este horario de clase al docente?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        res = servicio_horario.eliminar_horario(horario_id)
        if not res.ok:
            self._mostrar_feedback_prof(res.mensaje, error=True)
            return

        self._recargar_lista_profesores()
        self._mostrar_feedback_prof("Horario eliminado.", error=False)
        self.asignaciones_actualizadas.emit()

    def _mostrar_feedback_prof(self, mensaje: str, error: bool = False):
        color = "#f87171" if error else COLOR_EXITO
        self.lbl_feedback_prof.setText(mensaje)
        self.lbl_feedback_prof.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self.lbl_feedback_prof.show()
