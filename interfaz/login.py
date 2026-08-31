"""Pantalla de login con PySide6 y QSS.

No depende de archivos de imagen externos: el fondo es un degradado
armado con QSS y los iconos de usuario/candado se dibujan por codigo
con QPainter. Asi la interfaz nunca queda "rota" por assets faltantes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMainWindow,
    QGraphicsDropShadowEffect, QMessageBox
)
from PySide6.QtCore import Qt, QPoint, QSize, QPointF, QRectF
from PySide6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QPainter, QPainterPath, QPen
)

FUENTE_MONO = "Courier New"


# =============================================
# ICONOS DIBUJADOS POR CODIGO (sin archivos externos)
# =============================================
def _icono_usuario(size: int = 20, color: str = "#777777") -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))

    # Cabeza
    radio = size * 0.16
    painter.drawEllipse(QPointF(size / 2, size * 0.32), radio, radio)

    # Cuerpo (curva tipo "hombros")
    ruta = QPainterPath()
    ruta.moveTo(size * 0.18, size * 0.88)
    ruta.cubicTo(size * 0.18, size * 0.55, size * 0.82, size * 0.55, size * 0.82, size * 0.88)
    ruta.closeSubpath()
    painter.drawPath(ruta)

    painter.end()
    return QIcon(pixmap)


def _icono_candado(size: int = 20, color: str = "#777777") -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Arco (grillete) sin relleno
    pluma = QPen(QColor(color))
    pluma.setWidth(2)
    painter.setPen(pluma)
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(QRectF(size * 0.27, size * 0.10, size * 0.46, size * 0.5), 0, 180 * 16)

    # Cuerpo del candado
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(QRectF(size * 0.18, size * 0.45, size * 0.64, size * 0.42), 3, 3)

    painter.end()
    return QIcon(pixmap)


def _icono_texto(caracter: str, size: int = 24, color: str = "#333333") -> QIcon:
    """Genera un icono simple con un caracter (para minimizar/maximizar/cerrar)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor(color))
    fuente = QFont(FUENTE_MONO, int(size * 0.6), QFont.Bold)
    painter.setFont(fuente)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, caracter)
    painter.end()
    return QIcon(pixmap)


class VentanaLogin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Asistencia - Login")
        self.setFixedSize(1280, 720)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Para arrastrar la ventana
        self.dragging = False
        self.drag_offset = QPoint()

        # Referencia al dashboard, para que no lo recolecte el garbage collector
        self.ventana_principal = None

        # Widget central con el fondo en degradado (reemplaza a fondo.jpg)
        self.central = QWidget(self)
        self.central.setGeometry(0, 0, 1280, 720)
        self.central.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1b1b2f,
                    stop:0.5 #16213e,
                    stop:1 #0f3057
                );
            }
        """)
        self.setCentralWidget(self.central)

        # Layout para centrar la tarjeta automaticamente
        self.layout_centro = QGridLayout(self.central)
        self.layout_centro.setContentsMargins(0, 0, 0, 0)
        self.layout_centro.setSpacing(0)

        # Tarjeta (se centra sola con el grid layout)
        self.tarjeta = QFrame(self.central)
        self.tarjeta.setFixedSize(440, 540)
        self.tarjeta.setStyleSheet("""
            background-color: rgba(20, 20, 20, 0.65);
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(40)
        sombra.setColor(QColor(0, 0, 0, 100))
        sombra.setOffset(0, 8)
        self.tarjeta.setGraphicsEffect(sombra)

        self.layout_centro.addWidget(self.tarjeta, 0, 0, Qt.AlignmentFlag.AlignCenter)

        # Barra de titulo con botones (arriba a la derecha)
        self.barra_titulo = QWidget(self.central)
        self.barra_titulo.setFixedHeight(40)
        self.barra_titulo.setStyleSheet("background: transparent;")

        layout_barra = QHBoxLayout(self.barra_titulo)
        layout_barra.setContentsMargins(0, 5, 10, 0)
        layout_barra.setSpacing(8)
        layout_barra.addStretch()

        estilo_boton_ventana = """
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #e5e5e5; }
        """

        # Boton minimizar
        self.btn_minimizar = QPushButton(self.barra_titulo)
        self.btn_minimizar.setFixedSize(24, 24)
        self.btn_minimizar.setCursor(Qt.PointingHandCursor)
        self.btn_minimizar.setIcon(_icono_texto("\u2013"))  # –
        self.btn_minimizar.setIconSize(QSize(14, 14))
        self.btn_minimizar.setStyleSheet(estilo_boton_ventana)
        self.btn_minimizar.clicked.connect(self.showMinimized)

        # Boton maximizar
        self.btn_maximizar = QPushButton(self.barra_titulo)
        self.btn_maximizar.setFixedSize(24, 24)
        self.btn_maximizar.setCursor(Qt.PointingHandCursor)
        self.btn_maximizar.setIcon(_icono_texto("\u25a1"))  # □
        self.btn_maximizar.setIconSize(QSize(14, 14))
        self.btn_maximizar.setStyleSheet(estilo_boton_ventana)
        self.btn_maximizar.clicked.connect(self._alternar_maximizar)

        # Boton cerrar
        self.btn_cerrar = QPushButton(self.barra_titulo)
        self.btn_cerrar.setFixedSize(24, 24)
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.setIcon(_icono_texto("\u00d7", color="#cc3333"))  # ×
        self.btn_cerrar.setIconSize(QSize(14, 14))
        self.btn_cerrar.setStyleSheet(estilo_boton_ventana)
        self.btn_cerrar.clicked.connect(self.close)

        layout_barra.addWidget(self.btn_minimizar)
        layout_barra.addWidget(self.btn_maximizar)
        layout_barra.addWidget(self.btn_cerrar)

        # La barra va arriba a la derecha, encimada sobre el fondo
        self.layout_centro.addWidget(
            self.barra_titulo, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )

        self._armar_contenido()
        self.input_usuario.setFocus()

    def resizeEvent(self, event):
        """Ajusta el fondo al tamano de la ventana en cada cambio de tamano."""
        self.central.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def _alternar_maximizar(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        """Inicia el arrastre si se hace clic en la barra de titulo."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Mueve la ventana mientras se arrastra."""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Detiene el arrastre."""
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def _armar_contenido(self):
        # Layout principal de la tarjeta
        layout_principal = QVBoxLayout(self.tarjeta)
        layout_principal.setContentsMargins(50, 45, 50, 45)
        layout_principal.setSpacing(25)

        # --- TITULO ---
        titulo = QLabel("Inicia Sesion", self.tarjeta)
        titulo.setFont(QFont(FUENTE_MONO, 26, QFont.Bold))
        titulo.setStyleSheet("color: white; background: transparent; border: none;")
        titulo.setAlignment(Qt.AlignHCenter)
        layout_principal.addWidget(titulo)

        # --- BLOQUE USUARIO ---
        bloque_usuario = QVBoxLayout()
        bloque_usuario.setSpacing(2)

        label_usuario = QLabel("Nombre de Usuario", self.tarjeta)
        label_usuario.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        label_usuario.setStyleSheet("color: #888888; background: transparent; border: none; margin: 0px; padding: 0px;")

        self.input_usuario = QLineEdit(self.tarjeta)
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setFont(QFont(FUENTE_MONO, 14))
        self.input_usuario.setFixedHeight(50)
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                background-color: #0f0f0f;
                border: 1px solid #1f1f1f;
                border-radius: 12px;
                color: white;
                padding-left: 45px;
                padding-right: 15px;
            }
            QLineEdit:focus { border: 1px solid #3a3a5a; }
            QLineEdit::placeholder { color: #444444; }
        """)
        self.input_usuario.addAction(_icono_usuario(), QLineEdit.ActionPosition.LeadingPosition)

        bloque_usuario.addWidget(label_usuario)
        bloque_usuario.addWidget(self.input_usuario)
        layout_principal.addLayout(bloque_usuario)

        # --- BLOQUE CONTRASENA ---
        bloque_clave = QVBoxLayout()
        bloque_clave.setSpacing(2)

        label_clave = QLabel("Contrasena", self.tarjeta)
        label_clave.setFont(QFont(FUENTE_MONO, 11, QFont.Bold))
        label_clave.setStyleSheet("color: #888888; background: transparent; border: none; margin: 0px; padding: 0px;")

        self.input_clave = QLineEdit(self.tarjeta)
        self.input_clave.setPlaceholderText("Contrasena")
        self.input_clave.setFont(QFont(FUENTE_MONO, 14))
        self.input_clave.setFixedHeight(50)
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.input_clave.setStyleSheet("""
            QLineEdit {
                background-color: #0f0f0f;
                border: 1px solid #1f1f1f;
                border-radius: 12px;
                color: white;
                padding-left: 45px;
                padding-right: 15px;
            }
            QLineEdit:focus { border: 1px solid #3a3a5a; }
            QLineEdit::placeholder { color: #444444; }
        """)
        self.input_clave.addAction(_icono_candado(), QLineEdit.ActionPosition.LeadingPosition)

        bloque_clave.addWidget(label_clave)
        bloque_clave.addWidget(self.input_clave)
        layout_principal.addLayout(bloque_clave)

        # --- BOTON ---
        self.btn_ingresar = QPushButton("Inicia Sesion", self.tarjeta)
        self.btn_ingresar.setFont(QFont(FUENTE_MONO, 14, QFont.Bold))
        self.btn_ingresar.setFixedHeight(52)
        self.btn_ingresar.setCursor(Qt.PointingHandCursor)
        self.btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #242429;
                color: white;
                border: none;
                border-radius: 26px;
            }
            QPushButton:hover { background-color: #2e2e33; }
            QPushButton:pressed { background-color: #1a1a1e; }
        """)
        self.btn_ingresar.clicked.connect(self._intentar_login)
        self.input_clave.returnPressed.connect(self._intentar_login)
        layout_principal.addWidget(self.btn_ingresar)

    def _intentar_login(self):
        from servicios.usuario import autenticar

        username = self.input_usuario.text().strip()
        password = self.input_clave.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Faltan datos", "Ingresa usuario y contrasena")
            return

        resultado = autenticar(username, password)

        if resultado.ok:
            usuario = resultado.datos

            # Abrimos el dashboard ANTES de cerrar el login, para que
            # la app no se cierre sola al quedarse sin ventanas visibles.
            from interfaz.dashboard import VentanaPrincipal
            self.ventana_principal = VentanaPrincipal(usuario)
            self.ventana_principal.show()

            self.close()
        else:
            QMessageBox.critical(self, "Error de login", resultado.mensaje)
            self.input_clave.clear()
            self.input_clave.setFocus()

    def mostrar(self):
        self.show()