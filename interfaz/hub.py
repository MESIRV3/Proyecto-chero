"""Panel HUB (Inicio) con metricas adaptativas por rol y accesos rapidos."""
from datetime import date, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    COLOR_ACENTO,
    COLOR_ACENTO_HOVER,
    FUENTE_MONO,
    _estilo_boton,
    _estilo_boton_secundario,
    _estilo_tabla,
    _etiqueta,
    _tarjeta,
)
from servicios import curso as servicio_curso
from servicios import horario as servicio_horario
from servicios import preceptor as servicio_preceptor
from servicios.dashboard import obtener_metricas_hub


class PanelHub(QWidget):
    """Vista de inicio adaptativa por rol (Admin, Directivo, Preceptor, Profesor)."""

    navegar_a_alumnos = Signal()
    navegar_a_cursos = Signal()
    navegar_a_asistencia = Signal()
    navegar_a_personal = Signal()
    tomar_asistencia_materia_solicitada = Signal(int, object)

    def __init__(self, ciclo_id: int | None, profesor_id: int | None = None, preceptor_id: int | None = None):
        super().__init__()
        self.ciclo_id = ciclo_id
        self.profesor_id = profesor_id
        self.preceptor_id = preceptor_id
        self.rol_actual = "admin"
        self._anio_ciclo = date.today().year
        self._armar_ui()
        self._actualizar_banner()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Mensaje de error inline
        self.label_error = QLabel()
        self.label_error.setStyleSheet("color: #ff5c5c; padding: 8px 4px;")
        self.label_error.hide()
        layout.addWidget(self.label_error)

        # --- Banner de bienvenida ---
        banner = _tarjeta()
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 18, 24, 18)
        banner_layout.setSpacing(4)

        self.label_saludo = _etiqueta("", tenue=False)
        self.label_saludo.setFont(QFont(FUENTE_MONO, 17, QFont.Bold))
        banner_layout.addWidget(self.label_saludo)

        self.label_ciclo = _etiqueta("", tenue=True)
        self.label_ciclo.setFont(QFont(FUENTE_MONO, 11))
        banner_layout.addWidget(self.label_ciclo)

        layout.addWidget(banner)

        # --- Accesos rapidos ---
        self.fila_acciones = QHBoxLayout()
        self.btn_accion_1 = QPushButton("+ Agregar Alumno")
        self.btn_accion_1.setCursor(Qt.PointingHandCursor)
        self.btn_accion_1.setStyleSheet(_estilo_boton())
        self.btn_accion_1.clicked.connect(self.navegar_a_alumnos.emit)
        self.fila_acciones.addWidget(self.btn_accion_1)

        self.btn_accion_2 = QPushButton("🏫 Ver Cursos")
        self.btn_accion_2.setCursor(Qt.PointingHandCursor)
        self.btn_accion_2.setStyleSheet(_estilo_boton_secundario())
        self.btn_accion_2.clicked.connect(self.navegar_a_cursos.emit)
        self.fila_acciones.addWidget(self.btn_accion_2)

        self.btn_accion_3 = QPushButton("📋 Consulta Asistencia")
        self.btn_accion_3.setCursor(Qt.PointingHandCursor)
        self.btn_accion_3.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
        self.btn_accion_3.clicked.connect(self.navegar_a_asistencia.emit)
        self.fila_acciones.addWidget(self.btn_accion_3)

        self.btn_accion_4 = QPushButton("👥 Asignar Personal")
        self.btn_accion_4.setCursor(Qt.PointingHandCursor)
        self.btn_accion_4.setStyleSheet(_estilo_boton_secundario())
        self.btn_accion_4.clicked.connect(self.navegar_a_personal.emit)
        self.fila_acciones.addWidget(self.btn_accion_4)

        self.fila_acciones.addStretch()
        layout.addLayout(self.fila_acciones)

        # --- Contenedor de KPIs ---
        self.contenedor_kpis = QVBoxLayout()
        self.contenedor_kpis.setSpacing(12)

        self.fila_kpi_1 = QHBoxLayout()
        self.fila_kpi_1.setSpacing(12)
        self.fila_kpi_2 = QHBoxLayout()
        self.fila_kpi_2.setSpacing(12)

        self.contenedor_kpis.addLayout(self.fila_kpi_1)
        self.contenedor_kpis.addLayout(self.fila_kpi_2)
        layout.addLayout(self.contenedor_kpis)

        # --- Tabla resumen de cursos ---
        self.lbl_titulo_tabla = QLabel("Resumen de Cursos del Ciclo")
        self.lbl_titulo_tabla.setFont(QFont(FUENTE_MONO, 13, QFont.Bold))
        self.lbl_titulo_tabla.setStyleSheet(f"color: {COLOR_TEXTO}; margin-top: 6px;")
        layout.addWidget(self.lbl_titulo_tabla)

        self.tabla_cursos = QTableWidget(0, 4)
        self.tabla_cursos.setHorizontalHeaderLabels(
            ["Curso", "Especialidad", "Turno", "Alumnos Activos"]
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
        lbl_titulo.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        lbl_titulo.setWordWrap(True)
        layout.addWidget(lbl_titulo)

        lbl_valor = _etiqueta("—", tenue=False)
        lbl_valor.setFont(QFont(FUENTE_MONO, 24, QFont.Bold))
        lbl_valor.setStyleSheet(f"color: {COLOR_TEXTO};")
        layout.addWidget(lbl_valor)

        card.valor_label = lbl_valor
        return card

    def cambiar_rol(self, nuevo_rol: str, profesor_id: int | None = None, preceptor_id: int | None = None):
        """Cambia el rol activo en el hub y reconfigura las tarjetas e informacion mostrada."""
        self.rol_actual = nuevo_rol
        if profesor_id is not None:
            self.profesor_id = profesor_id
        if preceptor_id is not None:
            self.preceptor_id = preceptor_id
        self._cargar_datos()

    def showEvent(self, event):
        super().showEvent(event)
        self._cargar_datos()

    def _saludo_por_hora(self) -> str:
        hora = datetime.now().hour
        if hora < 12:
            return "Buen día"
        if hora < 20:
            return "Buenas tardes"
        return "Buenas noches"

    def _actualizar_banner(self):
        saludo = self._saludo_por_hora()
        roles_desc = {
            "admin": ("Panel de Administración", "Control global de la institución"),
            "directivo": ("Panel Directivo", "Visión macro de presentismo y alertas institucionales"),
            "preceptor": ("Panel de Preceptoría", "Control operativo diario y toma de lista"),
            "profesor": ("Panel Docente", "Gestión de cátedras y clases asignadas"),
        }
        titulo_rol, sub_rol = roles_desc.get(self.rol_actual, ("Sistema Escolar", "Panel institucional"))
        self.label_saludo.setText(f"{saludo}, {titulo_rol}")
        self.label_ciclo.setText(f"Ciclo lectivo activo: {self._anio_ciclo}  ·  {sub_rol}")

    def _cargar_datos(self):
        self.label_error.hide()
        self._actualizar_banner()
        self._configurar_acciones_por_rol()
        self._cargar_kpis_por_rol()
        self._cargar_tabla_cursos()

    def _configurar_acciones_por_rol(self):
        if self.rol_actual == "admin":
            self.btn_accion_1.setText("+ Agregar Alumno")
            self.btn_accion_1.show()
            self.btn_accion_2.setText("🏫 Gestionar Cursos")
            self.btn_accion_2.show()
            self.btn_accion_3.setText("📊 Consultar Asistencia")
            self.btn_accion_3.show()
            self.btn_accion_4.setText("👥 Asignar Personal")
            self.btn_accion_4.show()
        elif self.rol_actual == "directivo":
            self.btn_accion_1.hide()
            self.btn_accion_2.setText("🏫 Ver Cursos")
            self.btn_accion_2.show()
            self.btn_accion_3.setText("📊 Auditoría de Asistencia")
            self.btn_accion_3.show()
            self.btn_accion_4.setText("👥 Asignar Personal")
            self.btn_accion_4.show()
        elif self.rol_actual == "preceptor":
            self.btn_accion_1.setText("+ Agregar Alumno")
            self.btn_accion_1.show()
            self.btn_accion_2.setText("📋 Cursos y Toma de Lista")
            self.btn_accion_2.show()
            self.btn_accion_3.setText("📊 Consultar Asistencia")
            self.btn_accion_3.show()
            self.btn_accion_4.hide()
        elif self.rol_actual == "profesor":
            self.btn_accion_1.hide()
            self.btn_accion_2.setText("🏫 Ver Cursos")
            self.btn_accion_2.show()
            self.btn_accion_3.setText("📝 Asistencia de Clases")
            self.btn_accion_3.show()
            self.btn_accion_4.hide()

    def _cargar_kpis_por_rol(self):
        resultado = obtener_metricas_hub(self.ciclo_id)
        if not resultado.ok:
            self._mostrar_error(resultado.mensaje)
            return

        datos = resultado.datos
        self._anio_ciclo = datos.get("ciclo_anio", self._anio_ciclo)

        # Limpiar filas previas
        for fila in (self.fila_kpi_1, self.fila_kpi_2):
            while fila.count() > 0:
                item = fila.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        # Armar KPIs específicos según el rol
        total_cursos = datos.get("total_cursos", 6)
        cursos_tomados = datos.get("cursos_con_lista_hoy", 0)

        if self.rol_actual == "directivo":
            defs_1 = [
                ("📊 Presentismo Hoy", datos.get("presentismo_texto", "—")),
                ("👥 Matrícula Activa", str(datos.get("alumnos_activos", 0))),
                ("🏫 Cursos Totales", str(total_cursos)),
            ]
            defs_2 = [
                ("🔴 Ausentes Hoy", str(datos.get("ausentes_hoy", 0))),
                ("🟡 Llegadas Tarde Hoy", str(datos.get("tardes_hoy", 0))),
                ("⚠️ Alumnos de baja", str(datos.get("alumnos_baja", 0))),
            ]
        elif self.rol_actual == "preceptor":
            defs_1 = [
                ("📋 Cursos con Lista Hoy", f"{cursos_tomados} de {total_cursos}"),
                ("🟢 Presentes Hoy", str(datos.get("presentes_hoy", 0))),
                ("🔴 Ausentes Hoy", str(datos.get("ausentes_hoy", 0))),
            ]
            defs_2 = [
                ("🟡 Tardes Hoy (con hora)", str(datos.get("tardes_hoy", 0))),
                ("🔵 Retirados Hoy", str(datos.get("retirados_hoy", 0))),
                ("👥 Alumnos a Cargo", str(datos.get("alumnos_activos", 0))),
            ]
        elif self.rol_actual == "profesor":
            defs_1 = [
                ("📚 Materias del Ciclo", str(datos.get("total_materias", 0))),
                ("🏫 Cursos Asignados", str(total_cursos)),
                ("👥 Matrícula Escolar", str(datos.get("alumnos_activos", 0))),
            ]
            defs_2 = [
                ("📝 Asistencias Materia Hoy", str(datos.get("asistencias_hoy", 0))),
                ("📅 Asistencias Semana", str(datos.get("asistencias_semana", 0))),
                ("📊 Presentismo General", datos.get("presentismo_texto", "—")),
            ]
        else:  # admin
            defs_1 = [
                ("👥 Alumnos Activos", str(datos.get("alumnos_activos", 0))),
                ("🏫 Cursos Registrados", str(total_cursos)),
                ("📊 Presentismo Hoy", datos.get("presentismo_texto", "—")),
            ]
            defs_2 = [
                ("🟢 Presentes Hoy", str(datos.get("presentes_hoy", 0))),
                ("🔴 Ausentes Hoy", str(datos.get("ausentes_hoy", 0))),
                ("⚠️ Alumnos de baja", str(datos.get("alumnos_baja", 0))),
            ]

        for titulo, valor in defs_1:
            c = self._crear_tarjeta_kpi(titulo)
            c.valor_label.setText(valor)
            self.fila_kpi_1.addWidget(c)

        for titulo, valor in defs_2:
            c = self._crear_tarjeta_kpi(titulo)
            c.valor_label.setText(valor)
            self.fila_kpi_2.addWidget(c)

    def _cargar_tabla_cursos(self):
        if self.rol_actual == "profesor":
            dia_hoy = date.today().isoweekday()
            dia_nombre = servicio_horario.DIAS_SEMANA.get(dia_hoy, "Día actual")
            self.lbl_titulo_tabla.setText(f"📅 Cursos a cargo hoy ({dia_nombre})")

            self.tabla_cursos.setColumnCount(6)
            self.tabla_cursos.setHorizontalHeaderLabels(
                ["Curso", "Materia(s)", "Horario", "Turno", "Alumnos", "Acción"]
            )
            self.tabla_cursos.clearSpans()
            self.tabla_cursos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tabla_cursos.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

            profesor_id = self.profesor_id
            if profesor_id is None:
                try:
                    from database.conexion import conexion
                    with conexion() as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT id FROM usuario WHERE rol = 'profesor' AND activo = 1 ORDER BY id LIMIT 1")
                        r = cur.fetchone()
                        profesor_id = r["id"] if r else 1
                except Exception:
                    profesor_id = 1

            resultado = servicio_horario.obtener_cursos_del_dia_por_profesor(
                self.ciclo_id, profesor_id, dia_hoy
            )
            if not resultado.ok:
                self._mostrar_error(resultado.mensaje)
                self.tabla_cursos.setRowCount(0)
                return

            cursos = resultado.datos.get("cursos", [])
            if not cursos:
                self.tabla_cursos.setRowCount(1)
                item_vacio = QTableWidgetItem(f"No tenés cursos asignados para el día de hoy ({dia_nombre}).")
                item_vacio.setTextAlignment(Qt.AlignCenter)
                self.tabla_cursos.setItem(0, 0, item_vacio)
                self.tabla_cursos.setSpan(0, 0, 1, 6)
            else:
                self.tabla_cursos.setRowCount(len(cursos))
                for fila, curso in enumerate(cursos):
                    nombre = servicio_curso.obtener_nombre_curso(curso)
                    valores = [
                        nombre,
                        curso.get("materias_texto", "—"),
                        curso.get("horarios_texto", "—"),
                        curso.get("turno", "—"),
                        str(curso.get("cantidad_alumnos", 0)),
                    ]
                    for col, valor in enumerate(valores):
                        self.tabla_cursos.setItem(fila, col, QTableWidgetItem(str(valor)))

                    # Boton de accion directa
                    btn_pasar_lista = QPushButton("📝 Pasar Lista")
                    btn_pasar_lista.setCursor(Qt.PointingHandCursor)
                    btn_pasar_lista.setStyleSheet(_estilo_boton(COLOR_ACENTO, COLOR_ACENTO_HOVER))
                    btn_pasar_lista.setFixedHeight(28)
                    c_id = curso.get("curso_id")
                    m_id = curso.get("primer_materia_id")
                    btn_pasar_lista.clicked.connect(
                        lambda _, cid=c_id, mid=m_id: self.tomar_asistencia_materia_solicitada.emit(cid, mid)
                    )
                    self.tabla_cursos.setCellWidget(fila, 5, btn_pasar_lista)
        else:
            self.tabla_cursos.setColumnCount(4)
            self.tabla_cursos.setHorizontalHeaderLabels(
                ["Curso", "Especialidad", "Turno", "Alumnos Activos"]
            )
            self.tabla_cursos.clearSpans()
            self.tabla_cursos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            if self.rol_actual == "preceptor" and self.preceptor_id is not None:
                self.lbl_titulo_tabla.setText("📋 Cursos Asignados a mi Cargo")
                resultado = servicio_preceptor.listar_cursos_de_preceptor(self.preceptor_id, self.ciclo_id)
            else:
                self.lbl_titulo_tabla.setText("Resumen de Cursos del Ciclo")
                resultado = servicio_curso.listar_cursos(self.ciclo_id)

            if not resultado.ok:
                self._mostrar_error(resultado.mensaje)
                self.tabla_cursos.setRowCount(0)
                return

            cursos = resultado.datos
            if self.rol_actual == "preceptor" and self.preceptor_id is not None and not cursos:
                self.tabla_cursos.setRowCount(1)
                item_vacio = QTableWidgetItem("No tenés cursos asignados todavía. Solicitá la asignación en Dirección.")
                item_vacio.setTextAlignment(Qt.AlignCenter)
                self.tabla_cursos.setItem(0, 0, item_vacio)
                self.tabla_cursos.setSpan(0, 0, 1, 4)
                return

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
