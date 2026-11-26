"""Vista y auditoría jerárquica de asistencia y partes diarios por curso, alumno y fecha."""
from datetime import date, datetime
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
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
    COLOR_FONDO,
    COLOR_INPUT,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_boton_secundario,
    _estilo_input,
    _estilo_tabla,
    _etiqueta,
    _tarjeta,
)
from servicios import alumno as servicio_alumno
from servicios import curso as servicio_curso
from servicios.asistencia import (
    listar_asistencias_de_alumno,
    listar_historial_asistencia,
)
from servicios.exportacion import (
    exportar_asistencias_catedra_a_csv,
    exportar_partes_diarios_a_csv,
    exportar_resumen_global_a_csv,
)
from servicios.lista_diaria import (
    listar_historial_lista_diaria,
    listar_resumen_global_diario,
)


def _estilo_tabs() -> str:
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
            font-weight: bold;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{
            background: #2563eb;
            color: #ffffff;
        }}
        QTabBar::tab:hover:!selected {{
            background: #23252e;
            color: #ffffff;
        }}
    """


def _estilo_date_edit() -> str:
    return f"""
        QDateEdit {{
            background-color: {COLOR_INPUT};
            border: 1px solid {COLOR_BORDE};
            border-radius: 8px;
            color: {COLOR_TEXTO};
            padding: 5px 8px;
            font-size: 12px;
            font-weight: bold;
            min-width: 135px;
        }}
        QDateEdit:focus {{
            border: 1px solid {COLOR_ACENTO};
        }}
    """


class PanelAsistencia(QWidget):
    """Panel para consultar y auditar asistencias y partes diarios institucionales."""

    def __init__(self, ciclo_id: int | None = None, usuario_actual: dict | None = None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.usuario_actual = usuario_actual
        self.rol = (usuario_actual.get("rol") if usuario_actual else "admin")
        self.usuario_id = (usuario_actual.get("id") if usuario_actual else None)

        self.todos_los_cursos = []
        self.registros_resumen = []
        self.registros_partes = []
        self.registros_materias = []
        self._bloquear_senales_cascada = False

        self._armar_ui()
        self.recargar_filtros()
        self._consultar()

    def showEvent(self, event):
        super().showEvent(event)
        self.recargar_filtros()
        self._consultar()

    def cambiar_rol(self, nuevo_rol: str, usuario_id: int | None = None):
        """Ajusta la interfaz y vistas por rol (admin, directivo, preceptor, profesor)."""
        self.rol = nuevo_rol
        if usuario_id is not None:
            self.usuario_id = usuario_id

        if hasattr(self, "badge_rol"):
            self.badge_rol.setText(f"Vista: {nuevo_rol.capitalize()}")

        # Enrutamiento de pestaña por defecto segun rol
        if nuevo_rol == "profesor":
            self.tabs.setCurrentIndex(2)
        else:
            self.tabs.setCurrentIndex(0)

        self._consultar()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # --- Encabezado ---
        fila_titulo = QHBoxLayout()
        titulo = _etiqueta("Auditoría de Asistencia", tenue=False)
        titulo.setFont(QFont(FUENTE_MONO, 16, QFont.Bold))
        fila_titulo.addWidget(titulo)

        subtitulo = _etiqueta("Partes Diarios & Cátedra", tenue=True)
        subtitulo.setFont(QFont(FUENTE_MONO, 11))
        fila_titulo.addWidget(subtitulo)

        fila_titulo.addStretch()

        self.badge_rol = QLabel(f"Vista: {self.rol.capitalize()}")
        self.badge_rol.setStyleSheet(
            f"color: {COLOR_TEXTO}; background-color: #2563eb; "
            f"border-radius: 8px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )
        fila_titulo.addWidget(self.badge_rol)
        layout.addLayout(fila_titulo)

        # --- Barra de Filtros Jerárquicos en Cascada ---
        tarjeta_filtros = _tarjeta()
        layout_filtros = QVBoxLayout(tarjeta_filtros)
        layout_filtros.setContentsMargins(14, 12, 14, 12)
        layout_filtros.setSpacing(10)

        # Fila 1: Selectores en cascada (Turno -> Curso -> Alumno)
        fila_cascada = QHBoxLayout()
        fila_cascada.setSpacing(10)

        # Turno
        col_turno = QVBoxLayout()
        col_turno.setSpacing(4)
        col_turno.addWidget(_etiqueta("Turno:", tenue=True))
        self.combo_turno = QComboBox()
        self.combo_turno.setStyleSheet(_estilo_input())
        self.combo_turno.addItem("Todos los turnos", None)
        self.combo_turno.addItem("Mañana", "Mañana")
        self.combo_turno.addItem("Tarde", "Tarde")
        self.combo_turno.currentIndexChanged.connect(self._al_cambiar_turno)
        col_turno.addWidget(self.combo_turno)
        fila_cascada.addLayout(col_turno, stretch=1)

        # Curso
        col_curso = QVBoxLayout()
        col_curso.setSpacing(4)
        col_curso.addWidget(_etiqueta("Curso:", tenue=True))
        self.combo_curso = QComboBox()
        self.combo_curso.setStyleSheet(_estilo_input())
        self.combo_curso.currentIndexChanged.connect(self._al_cambiar_curso)
        col_curso.addWidget(self.combo_curso)
        fila_cascada.addLayout(col_curso, stretch=2)

        # Alumno
        col_alumno = QVBoxLayout()
        col_alumno.setSpacing(4)
        col_alumno.addWidget(_etiqueta("Alumno:", tenue=True))
        self.combo_alumno = QComboBox()
        self.combo_alumno.setStyleSheet(_estilo_input())
        self.combo_alumno.currentIndexChanged.connect(self._al_cambiar_alumno)
        col_alumno.addWidget(self.combo_alumno)
        fila_cascada.addLayout(col_alumno, stretch=3)

        layout_filtros.addLayout(fila_cascada)

        # Fila 2: Rango de fechas y acciones
        fila_fechas = QHBoxLayout()
        fila_fechas.setSpacing(10)

        fila_fechas.addWidget(_etiqueta("Desde:", tenue=True))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setFixedWidth(135)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.setStyleSheet(_estilo_date_edit())
        fila_fechas.addWidget(self.date_desde)

        fila_fechas.addWidget(_etiqueta("Hasta:", tenue=True))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setFixedWidth(135)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setStyleSheet(_estilo_date_edit())
        fila_fechas.addWidget(self.date_hasta)

        # Presets rápidos
        btn_preset_hoy = QPushButton("Hoy")
        btn_preset_hoy.setCursor(Qt.PointingHandCursor)
        btn_preset_hoy.setStyleSheet(_estilo_boton_secundario(11))
        btn_preset_hoy.clicked.connect(self._fijar_rango_hoy)
        fila_fechas.addWidget(btn_preset_hoy)

        btn_preset_7dias = QPushButton("7 días")
        btn_preset_7dias.setCursor(Qt.PointingHandCursor)
        btn_preset_7dias.setStyleSheet(_estilo_boton_secundario(11))
        btn_preset_7dias.clicked.connect(self._fijar_rango_7_dias)
        fila_fechas.addWidget(btn_preset_7dias)

        btn_preset_30dias = QPushButton("30 días")
        btn_preset_30dias.setCursor(Qt.PointingHandCursor)
        btn_preset_30dias.setStyleSheet(_estilo_boton_secundario(11))
        btn_preset_30dias.clicked.connect(self._fijar_rango_30_dias)
        fila_fechas.addWidget(btn_preset_30dias)

        btn_preset_ciclo = QPushButton("Todo el ciclo")
        btn_preset_ciclo.setCursor(Qt.PointingHandCursor)
        btn_preset_ciclo.setToolTip("Consultar todos los registros del ciclo lectivo completo")
        btn_preset_ciclo.setStyleSheet(_estilo_boton_secundario(11))
        btn_preset_ciclo.clicked.connect(self._fijar_rango_ciclo)
        fila_fechas.addWidget(btn_preset_ciclo)

        fila_fechas.addStretch()

        self.btn_consultar = QPushButton("🔍 Consultar")
        self.btn_consultar.setCursor(Qt.PointingHandCursor)
        self.btn_consultar.setStyleSheet(_estilo_boton("#2563eb", "#1d4ed8"))
        self.btn_consultar.clicked.connect(self._consultar)
        fila_fechas.addWidget(self.btn_consultar)

        self.btn_exportar = QPushButton("📥 Exportar CSV")
        self.btn_exportar.setCursor(Qt.PointingHandCursor)
        self.btn_exportar.setToolTip("Exportar los registros de la pestaña activa a un archivo CSV")
        self.btn_exportar.setStyleSheet(_estilo_boton_secundario())
        self.btn_exportar.clicked.connect(self._exportar_csv)
        fila_fechas.addWidget(self.btn_exportar)

        layout_filtros.addLayout(fila_fechas)
        layout.addWidget(tarjeta_filtros)

        # --- Tarjetas Métricas de Resumen (KPIs) ---
        fila_kpis = QHBoxLayout()
        fila_kpis.setSpacing(12)

        self.card_presentismo = self._crear_tarjeta_kpi("📊 Presentismo")
        self.card_presentes = self._crear_tarjeta_kpi("✅ Presentes")
        self.card_ausentes = self._crear_tarjeta_kpi("❌ Ausentes")
        self.card_extra = self._crear_tarjeta_kpi("📋 Partes Registrados")

        fila_kpis.addWidget(self.card_presentismo)
        fila_kpis.addWidget(self.card_presentes)
        fila_kpis.addWidget(self.card_ausentes)
        fila_kpis.addWidget(self.card_extra)
        layout.addLayout(fila_kpis)

        # --- Mensaje de estado / error ---
        self.label_mensaje = QLabel()
        self.label_mensaje.setStyleSheet(
            f"color: {COLOR_TEXTO_TENUE}; padding: 10px 4px; font-weight: bold;"
        )
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.hide()
        layout.addWidget(self.label_mensaje)

        # --- Pestañas (Resumen Global, Detalle Partes Diarios, Asistencias de Cátedra) ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_estilo_tabs())
        self.tabs.currentChanged.connect(self._al_cambiar_pestana)

        # Pestaña 0: Resumen Global por Curso y Día
        self.tab_resumen = QWidget()
        layout_resumen = QVBoxLayout(self.tab_resumen)
        layout_resumen.setContentsMargins(4, 8, 4, 4)
        layout_resumen.setSpacing(6)

        lbl_tip_resumen = _etiqueta(
            "Doble clic en un curso/fecha para abrir el detalle alumno por alumno.",
            tenue=True,
        )
        lbl_tip_resumen.setFont(QFont(FUENTE_MONO, 10))
        layout_resumen.addWidget(lbl_tip_resumen)

        self.tabla_resumen = QTableWidget(0, 10)
        self.tabla_resumen.setHorizontalHeaderLabels([
            "Fecha", "Curso", "Estado", "Total", "Presentes", "Ausentes",
            "Tardes", "Retiros", "% Presentismo", "Preceptor/a",
        ])
        self.tabla_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_resumen.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_resumen.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_resumen.setAlternatingRowColors(True)
        self.tabla_resumen.setStyleSheet(_estilo_tabla())
        self.tabla_resumen.cellDoubleClicked.connect(self._abrir_detalle_desde_resumen)
        layout_resumen.addWidget(self.tabla_resumen)

        self.tabs.addTab(self.tab_resumen, "🌐 Resumen Global (Curso / Día)")

        # Pestaña 1: Detalle por Alumno (Partes Diarios Institucionales)
        self.tab_partes = QWidget()
        layout_partes = QVBoxLayout(self.tab_partes)
        layout_partes.setContentsMargins(4, 8, 4, 4)

        self.tabla_partes = QTableWidget(0, 8)
        self.tabla_partes.setHorizontalHeaderLabels([
            "Fecha", "Curso", "Alumno", "DNI", "Estado", "Horario", "Motivo Retiro", "Preceptor/a"
        ])
        self.tabla_partes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_partes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_partes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_partes.setAlternatingRowColors(True)
        self.tabla_partes.setStyleSheet(_estilo_tabla())
        layout_partes.addWidget(self.tabla_partes)

        self.tabs.addTab(self.tab_partes, "📋 Detalle por Alumno")

        # Pestaña 2: Asistencias de Cátedra (Profesores / Directivos)
        self.tab_materias = QWidget()
        layout_materias = QVBoxLayout(self.tab_materias)
        layout_materias.setContentsMargins(4, 8, 4, 4)

        self.tabla_materias = QTableWidget(0, 8)
        self.tabla_materias.setHorizontalHeaderLabels([
            "Fecha", "Curso", "Materia", "Alumno", "DNI", "Estado", "Observaciones", "Docente"
        ])
        self.tabla_materias.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_materias.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_materias.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_materias.setAlternatingRowColors(True)
        self.tabla_materias.setStyleSheet(_estilo_tabla())
        layout_materias.addWidget(self.tabla_materias)

        self.tabs.addTab(self.tab_materias, "📚 Asistencias de Cátedra")

        layout.addWidget(self.tabs, stretch=1)

    def _crear_tarjeta_kpi(self, titulo: str) -> QFrame:
        card = _tarjeta()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        lbl_titulo = _etiqueta(titulo, tenue=True)
        lbl_titulo.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
        layout.addWidget(lbl_titulo)

        lbl_valor = _etiqueta("—", tenue=False)
        lbl_valor.setFont(QFont(FUENTE_MONO, 18, QFont.Bold))
        layout.addWidget(lbl_valor)

        card.titulo_label = lbl_titulo
        card.valor_label = lbl_valor
        return card

    def recargar_filtros(self):
        """Carga cursos del ciclo lectivo y puebla la cascada inicial."""
        res_cursos = servicio_curso.listar_cursos(self.ciclo_id)
        if res_cursos.ok:
            self.todos_los_cursos = res_cursos.datos or []
        else:
            self.todos_los_cursos = []

        self._filtrar_cursos_por_turno()

    def recargar_alumnos(self):
        """Alias para mantener compatibilidad con llamadas externas."""
        self.recargar_filtros()

    def _al_cambiar_turno(self):
        if self._bloquear_senales_cascada:
            return
        self._filtrar_cursos_por_turno()
        self._consultar()

    def _al_cambiar_curso(self):
        if self._bloquear_senales_cascada:
            return
        self._filtrar_alumnos_por_curso()
        self._consultar()

    def _al_cambiar_alumno(self):
        if self._bloquear_senales_cascada:
            return
        self._consultar()

    def _filtrar_cursos_por_turno(self):
        self._bloquear_senales_cascada = True
        try:
            curso_actual = self.combo_curso.currentData()
            self.combo_curso.clear()
            self.combo_curso.addItem("Todos los cursos", None)

            turno_filtro = self.combo_turno.currentData()
            for c in self.todos_los_cursos:
                if turno_filtro is None or c.get("turno") == turno_filtro:
                    nombre = servicio_curso.obtener_nombre_curso(c)
                    self.combo_curso.addItem(nombre, c["id"])

            if curso_actual is not None:
                idx = self.combo_curso.findData(curso_actual)
                if idx >= 0:
                    self.combo_curso.setCurrentIndex(idx)
        finally:
            self._bloquear_senales_cascada = False

        self._filtrar_alumnos_por_curso()

    def _filtrar_alumnos_por_curso(self):
        self._bloquear_senales_cascada = True
        try:
            alumno_actual = self.combo_alumno.currentData()
            self.combo_alumno.clear()

            curso_id = self.combo_curso.currentData()
            if curso_id is None:
                self.combo_alumno.addItem("Todos los alumnos", None)
                resultado = servicio_alumno.listar_alumnos(curso_id=None, solo_activos=True)
            else:
                self.combo_alumno.addItem("Todos los alumnos del curso", None)
                resultado = servicio_alumno.listar_alumnos(curso_id=curso_id, solo_activos=True)

            if resultado.ok and resultado.datos:
                for a in sorted(
                    resultado.datos,
                    key=lambda x: (x.get("apellido", ""), x.get("nombre", "")),
                ):
                    texto = f"{a.get('apellido', '')}, {a.get('nombre', '')} (Legajo {a['numero']})"
                    self.combo_alumno.addItem(texto, a["numero"])

            if alumno_actual is not None:
                idx = self.combo_alumno.findData(alumno_actual)
                if idx >= 0:
                    self.combo_alumno.setCurrentIndex(idx)
        finally:
            self._bloquear_senales_cascada = False

    def _fijar_rango_hoy(self):
        hoy = QDate.currentDate()
        self.date_desde.setDate(hoy)
        self.date_hasta.setDate(hoy)
        self._consultar()

    def _fijar_rango_7_dias(self):
        hoy = QDate.currentDate()
        self.date_desde.setDate(hoy.addDays(-7))
        self.date_hasta.setDate(hoy)
        self._consultar()

    def _fijar_rango_30_dias(self):
        hoy = QDate.currentDate()
        self.date_desde.setDate(hoy.addDays(-30))
        self.date_hasta.setDate(hoy)
        self._consultar()

    def _fijar_rango_ciclo(self):
        anio = QDate.currentDate().year()
        self.date_desde.setDate(QDate(anio, 1, 1))
        self.date_hasta.setDate(QDate(anio, 12, 31))
        self._consultar()

    def _al_cambiar_pestana(self, _indice: int):
        self._actualizar_tarjetas_kpi()
        self._actualizar_mensaje_vacio()

    def _abrir_detalle_desde_resumen(self, fila: int, _columna: int):
        """Al hacer doble clic en un curso/fecha del resumen global, abre el detalle por alumno."""
        if fila < 0 or fila >= len(self.registros_resumen):
            return
        reg = self.registros_resumen[fila]
        curso_id = reg.get("curso_id")
        fecha_str = reg.get("fecha")

        self._bloquear_senales_cascada = True
        try:
            idx_curso = self.combo_curso.findData(curso_id)
            if idx_curso < 0:
                self.combo_turno.setCurrentIndex(0)
                self._filtrar_cursos_por_turno()
                idx_curso = self.combo_curso.findData(curso_id)
            if idx_curso >= 0:
                self.combo_curso.setCurrentIndex(idx_curso)
        finally:
            self._bloquear_senales_cascada = False

        self._filtrar_alumnos_por_curso()

        if fecha_str:
            qfecha = QDate.fromString(fecha_str, "yyyy-MM-dd")
            if qfecha.isValid():
                self.date_desde.setDate(qfecha)
                self.date_hasta.setDate(qfecha)

        self.tabs.setCurrentIndex(1)
        self._consultar()

    def _consultar(self):
        if self.date_desde.date() > self.date_hasta.date():
            self._mostrar_mensaje(
                "La fecha 'Desde' no puede ser posterior a 'Hasta'.", es_error=True
            )
            self.registros_resumen = []
            self.registros_partes = []
            self.registros_materias = []
            self.tabla_resumen.setRowCount(0)
            self.tabla_partes.setRowCount(0)
            self.tabla_materias.setRowCount(0)
            self._limpiar_tarjetas_kpi()
            return

        turno = self.combo_turno.currentData()
        curso_id = self.combo_curso.currentData()
        alumno_numero = self.combo_alumno.currentData()
        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        # 0. Cargar Resumen Global diario por Curso y Fecha
        self.registros_resumen = listar_resumen_global_diario(
            turno=turno,
            curso_id=curso_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ciclo_id=self.ciclo_id,
        )

        # 1. Cargar historial detallado de Partes Diarios Institucionales
        self.registros_partes = listar_historial_lista_diaria(
            curso_id=curso_id,
            alumno_numero=alumno_numero,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ciclo_id=self.ciclo_id,
            turno=turno,
        )

        # 2. Cargar historial de Asistencias de Cátedra
        profesor_id = self.usuario_id if self.rol == "profesor" else None
        self.registros_materias = listar_historial_asistencia(
            curso_id=curso_id,
            alumno_numero=alumno_numero,
            profesor_id=profesor_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ciclo_id=self.ciclo_id,
            turno=turno,
        )

        self._renderizar_tabla_resumen()
        self._renderizar_tabla_partes()
        self._renderizar_tabla_materias()
        self._actualizar_tarjetas_kpi()
        self._actualizar_mensaje_vacio()

    def _actualizar_mensaje_vacio(self):
        if self.date_desde.date() > self.date_hasta.date():
            return
        idx = self.tabs.currentIndex()
        if idx == 0:
            total_activos = len(self.registros_resumen)
        elif idx == 1:
            total_activos = len(self.registros_partes)
        else:
            total_activos = len(self.registros_materias)

        if total_activos == 0:
            self._mostrar_mensaje(
                "No se encontraron registros de asistencia para el período y filtros seleccionados. "
                "Probá con 'Todo el ciclo' o verificá las fechas.",
                es_error=False,
            )
        else:
            self.label_mensaje.hide()

    def _renderizar_tabla_resumen(self):
        self.tabla_resumen.setRowCount(len(self.registros_resumen))
        for fila, reg in enumerate(self.registros_resumen):
            self.tabla_resumen.setItem(fila, 0, QTableWidgetItem(str(reg.get("fecha", "-"))))
            self.tabla_resumen.setItem(fila, 1, QTableWidgetItem(str(reg.get("curso_nombre", "-"))))

            estado_carga = reg.get("estado_carga", "Sin registrar")
            item_estado = QTableWidgetItem(estado_carga)
            item_estado.setTextAlignment(Qt.AlignCenter)
            item_estado.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
            if estado_carga == "Registrado":
                item_estado.setForeground(QColor("#22c55e"))
            else:
                item_estado.setForeground(QColor("#eab308"))
            self.tabla_resumen.setItem(fila, 2, item_estado)

            for col, clave in [
                (3, "total_registrados"),
                (4, "presentes"),
                (5, "ausentes"),
                (6, "tardes"),
                (7, "retirados"),
            ]:
                val = reg.get(clave, 0)
                item = QTableWidgetItem(str(val) if estado_carga == "Registrado" else "—")
                item.setTextAlignment(Qt.AlignCenter)
                if estado_carga == "Registrado":
                    if col == 4 and val > 0:
                        item.setForeground(QColor("#22c55e"))
                    elif col == 5 and val > 0:
                        item.setForeground(QColor("#ef4444"))
                    elif col == 6 and val > 0:
                        item.setForeground(QColor("#eab308"))
                    elif col == 7 and val > 0:
                        item.setForeground(QColor("#f97316"))
                self.tabla_resumen.setItem(fila, col, item)

            pct = reg.get("porcentaje_presentismo")
            item_pct = QTableWidgetItem(f"{pct}%" if pct is not None else "—")
            item_pct.setTextAlignment(Qt.AlignCenter)
            item_pct.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
            if pct is not None:
                color_pct = "#22c55e" if pct >= 80.0 else ("#eab308" if pct >= 70.0 else "#ef4444")
                item_pct.setForeground(QColor(color_pct))
            self.tabla_resumen.setItem(fila, 8, item_pct)

            self.tabla_resumen.setItem(fila, 9, QTableWidgetItem(str(reg.get("registrado_por") or "—")))

    def _renderizar_tabla_partes(self):
        self.tabla_partes.setRowCount(len(self.registros_partes))
        for fila, reg in enumerate(self.registros_partes):
            self.tabla_partes.setItem(fila, 0, QTableWidgetItem(str(reg.get("fecha", "-"))))
            self.tabla_partes.setItem(fila, 1, QTableWidgetItem(str(reg.get("curso_nombre", "-"))))
            self.tabla_partes.setItem(fila, 2, QTableWidgetItem(str(reg.get("alumno_completo", "-"))))
            self.tabla_partes.setItem(fila, 3, QTableWidgetItem(str(reg.get("dni") or "-")))

            estado = (reg.get("estado") or "-").lower()
            item_estado = QTableWidgetItem(estado.capitalize())
            item_estado.setTextAlignment(Qt.AlignCenter)
            item_estado.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
            if estado == "presente":
                item_estado.setForeground(QColor("#22c55e"))
            elif estado == "ausente":
                item_estado.setForeground(QColor("#ef4444"))
            elif estado == "tarde":
                item_estado.setForeground(QColor("#eab308"))
            elif estado == "retirado":
                item_estado.setForeground(QColor("#f97316"))
            self.tabla_partes.setItem(fila, 4, item_estado)

            detalle_horario = "-"
            if estado == "tarde" and reg.get("hora_llegada"):
                detalle_horario = f"Llegada: {reg['hora_llegada']}"
            elif estado == "retirado" and reg.get("hora_retiro"):
                detalle_horario = f"Retiro: {reg['hora_retiro']}"
            self.tabla_partes.setItem(fila, 5, QTableWidgetItem(detalle_horario))

            self.tabla_partes.setItem(fila, 6, QTableWidgetItem(str(reg.get("motivo_retiro") or "-")))
            self.tabla_partes.setItem(fila, 7, QTableWidgetItem(str(reg.get("registrado_por") or "-")))

    def _renderizar_tabla_materias(self):
        self.tabla_materias.setRowCount(len(self.registros_materias))
        for fila, reg in enumerate(self.registros_materias):
            self.tabla_materias.setItem(fila, 0, QTableWidgetItem(str(reg.get("fecha", "-"))))
            self.tabla_materias.setItem(fila, 1, QTableWidgetItem(str(reg.get("curso_nombre", "-"))))
            self.tabla_materias.setItem(fila, 2, QTableWidgetItem(str(reg.get("materia_nombre", "-"))))
            self.tabla_materias.setItem(fila, 3, QTableWidgetItem(str(reg.get("alumno_completo", "-"))))
            self.tabla_materias.setItem(fila, 4, QTableWidgetItem(str(reg.get("dni") or "-")))

            estado = (reg.get("estado") or "-").lower()
            item_estado = QTableWidgetItem(estado.capitalize())
            item_estado.setTextAlignment(Qt.AlignCenter)
            item_estado.setFont(QFont(FUENTE_MONO, 10, QFont.Bold))
            if estado == "presente":
                item_estado.setForeground(QColor("#22c55e"))
            elif estado == "ausente":
                item_estado.setForeground(QColor("#ef4444"))
            self.tabla_materias.setItem(fila, 5, item_estado)

            self.tabla_materias.setItem(fila, 6, QTableWidgetItem(str(reg.get("observaciones") or "-")))
            self.tabla_materias.setItem(fila, 7, QTableWidgetItem(str(reg.get("profesor_completo") or "-")))

    def _actualizar_tarjetas_kpi(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            # Pestaña 0: Resumen Global por Curso / Día
            total = sum(r.get("total_registrados", 0) for r in self.registros_resumen)
            presentes = sum(r.get("presentes", 0) for r in self.registros_resumen)
            ausentes = sum(r.get("ausentes", 0) for r in self.registros_resumen)
            tardes = sum(r.get("tardes", 0) for r in self.registros_resumen)
            registrados = sum(
                1 for r in self.registros_resumen if r.get("estado_carga") == "Registrado"
            )

            pct = round(((presentes + tardes) / total * 100.0), 1) if total > 0 else 0.0

            color_pct = "#22c55e" if pct >= 80.0 else ("#eab308" if pct >= 70.0 else "#ef4444")
            self.card_presentismo.valor_label.setText(f"{pct}%" if total > 0 else "—")
            self.card_presentismo.valor_label.setStyleSheet(
                f"color: {color_pct if total > 0 else COLOR_TEXTO};"
            )

            self.card_presentes.valor_label.setText(str(presentes))
            self.card_ausentes.valor_label.setText(str(ausentes))

            es_dia_unico = self.date_desde.date() == self.date_hasta.date()
            if es_dia_unico:
                self.card_extra.titulo_label.setText("🏫 Cursos Cargados")
                self.card_extra.valor_label.setText(f"{registrados} / {len(self.registros_resumen)}")
            else:
                self.card_extra.titulo_label.setText("📋 Partes Registrados")
                self.card_extra.valor_label.setText(str(registrados))
        elif idx == 1:
            # Pestaña 1: Detalle por Alumno (Partes Diarios Institucionales)
            total = len(self.registros_partes)
            presentes = sum(1 for r in self.registros_partes if r.get("estado") == "presente")
            ausentes = sum(1 for r in self.registros_partes if r.get("estado") == "ausente")
            tardes = sum(1 for r in self.registros_partes if r.get("estado") == "tarde")
            retirados = sum(1 for r in self.registros_partes if r.get("estado") == "retirado")
            tardes_retiros = tardes + retirados

            pct = round(((presentes + tardes) / total * 100.0), 1) if total > 0 else 0.0

            color_pct = "#22c55e" if pct >= 80.0 else ("#eab308" if pct >= 70.0 else "#ef4444")
            self.card_presentismo.valor_label.setText(f"{pct}%" if total > 0 else "—")
            self.card_presentismo.valor_label.setStyleSheet(
                f"color: {color_pct if total > 0 else COLOR_TEXTO};"
            )

            self.card_presentes.valor_label.setText(str(presentes))
            self.card_ausentes.valor_label.setText(str(ausentes))

            self.card_extra.titulo_label.setText("⏰ Tardes / Retiros")
            self.card_extra.valor_label.setText(str(tardes_retiros))
        else:
            # Pestaña 2: Asistencias de Cátedra
            total = len(self.registros_materias)
            presentes = sum(1 for r in self.registros_materias if r.get("estado") == "presente")
            ausentes = sum(1 for r in self.registros_materias if r.get("estado") == "ausente")

            # Alumnos con faltas críticas (> 15 inasistencias en el período)
            faltas_alumno = {}
            for r in self.registros_materias:
                if r.get("estado") == "ausente":
                    num = r.get("alumno_numero")
                    faltas_alumno[num] = faltas_alumno.get(num, 0) + 1
            criticos = sum(1 for cant in faltas_alumno.values() if cant > 15)

            pct = round((presentes / total * 100.0), 1) if total > 0 else 0.0

            color_pct = "#22c55e" if pct >= 80.0 else ("#eab308" if pct >= 70.0 else "#ef4444")
            self.card_presentismo.valor_label.setText(f"{pct}%" if total > 0 else "—")
            self.card_presentismo.valor_label.setStyleSheet(
                f"color: {color_pct if total > 0 else COLOR_TEXTO};"
            )

            self.card_presentes.valor_label.setText(str(presentes))
            self.card_ausentes.valor_label.setText(str(ausentes))

            self.card_extra.titulo_label.setText("⚠️ Faltas Críticas (>15)")
            self.card_extra.valor_label.setText(str(criticos))

    def _limpiar_tarjetas_kpi(self):
        self.card_presentismo.valor_label.setText("—")
        self.card_presentismo.valor_label.setStyleSheet(f"color: {COLOR_TEXTO};")
        self.card_presentes.valor_label.setText("—")
        self.card_ausentes.valor_label.setText("—")
        self.card_extra.valor_label.setText("—")

    def _mostrar_mensaje(self, mensaje: str, es_error: bool = False):
        color = "#ff5c5c" if es_error else COLOR_TEXTO_TENUE
        self.label_mensaje.setStyleSheet(f"color: {color}; padding: 10px 4px; font-weight: bold;")
        self.label_mensaje.setText(mensaje)
        self.label_mensaje.show()

    def _exportar_csv(self):
        """Exporta los datos de la pestaña activa a un archivo CSV compatible con Excel."""
        indice_tab = self.tabs.currentIndex()
        if indice_tab == 0:
            registros = self.registros_resumen
            prefijo = "resumen_global_diario"
        elif indice_tab == 1:
            registros = self.registros_partes
            prefijo = "partes_diarios"
        else:
            registros = self.registros_materias
            prefijo = "asistencia_catedra"

        if not registros:
            QMessageBox.information(
                self,
                "Exportar asistencia",
                "No hay registros cargados para exportar en la pestaña activa.\n"
                "Realizá una consulta primero.",
            )
            return

        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")
        nombre_sugerido = f"{prefijo}_{fecha_desde}_al_{fecha_hasta}.csv"

        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte como CSV",
            nombre_sugerido,
            "Archivos CSV (*.csv);;Todos los archivos (*.*)",
        )
        if not ruta_archivo:
            return

        if indice_tab == 0:
            resultado = exportar_resumen_global_a_csv(registros, ruta_archivo)
        elif indice_tab == 1:
            resultado = exportar_partes_diarios_a_csv(registros, ruta_archivo)
        else:
            resultado = exportar_asistencias_catedra_a_csv(registros, ruta_archivo)

        if resultado.ok:
            QMessageBox.information(
                self,
                "Exportación exitosa",
                f"Se exportaron correctamente {len(registros)} registros a:\n{ruta_archivo}",
            )
        else:
            QMessageBox.warning(
                self,
                "Error al exportar",
                f"No se pudo completar la exportación:\n{resultado.mensaje}",
            )

