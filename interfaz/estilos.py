"""Helpers visuales y paleta de colores compartidos para paneles de interfaz.

Sistema de diseño "Escuela Moderna" (Modo Operate):
- Alto contraste accesible (WCAG AA y AAA).
- Paleta intencional con acento azul institucional.
- Jerarquía tipográfica consistente y legible para entornos educativos.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QFrame, QLabel
from PySide6.QtGui import QFont


def _ruta_icono_chevron() -> str:
    """Devuelve la ruta POSIX al icono chevron_down.png (compatible con QSS y PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    ruta = base / "assets" / "login" / "chevron_down.png"
    return ruta.as_posix() if ruta.exists() else ""


# --- Tipografía ---
FUENTE_UI = "Segoe UI"
FUENTE_MONO = "Segoe UI"  # Mantenido para retrocompatibilidad


# --- Paleta de Colores ---
# Canvas y Superficies
COLOR_FONDO = "#131418"               # Canvas oscuro balanceado (menos abrasivo que negro puro)
COLOR_TARJETA = "#1c1e24"             # Superficie elevada para tarjetas y paneles
COLOR_BORDE = "#2c303a"               # Borde nítido para delimitar contenedores
COLOR_BORDE_TENUE = "#22252e"         # Separador suave
COLOR_INPUT = "#16181d"               # Fondo de campos de entrada y tablas

# Tipografía y Contraste
COLOR_TEXTO = "#f8fafc"               # Texto primario: blanco cálido de alto contraste (WCAG AAA)
COLOR_TEXTO_TENUE = "#94a3b8"         # Texto secundario: slate legible (WCAG AA > 5:1)

# Acciones y Estados
COLOR_ACENTO = "#2563eb"              # Azul institucional accesible para acciones principales
COLOR_ACENTO_HOVER = "#1d4ed8"        # Hover azul profundo
COLOR_SECUNDARIO = "#262933"          # Superficie neutra para botones secundarios (Volver, Cancelar)
COLOR_SECUNDARIO_HOVER = "#323642"    # Hover neutro

COLOR_PELIGRO = "#b91c1c"             # Rojo vino oscuro para acciones destructivas
COLOR_PELIGRO_HOVER = "#dc2626"       # Hover peligro activo

# Controles auxiliares
COLOR_SCROLLBAR_HANDLE = "#374151"    # Gris pizarra para barras de desplazamiento
COLOR_SCROLLBAR_HOVER = "#4b5563"

# Semántica institucional
COLOR_EXITO = "#22c55e"               # Verde (Presente / Activo)
COLOR_ADVERTENCIA = "#eab308"         # Amarillo (Tarde / Advertencia)
COLOR_RETIRO = "#f97316"              # Naranja (Retiro anticipado)
COLOR_INFO = "#38bdf8"                # Celeste (Información)


def _estilo_input():
    chevron = _ruta_icono_chevron()
    flecha_css = (
        f"image: url({chevron}); width: 11px; height: 11px;"
        if chevron
        else "width: 0px; height: 0px;"
    )
    return f"""
        QLineEdit, QComboBox, QDateEdit, QSpinBox {{
            background-color: {COLOR_INPUT};
            border: 1px solid {COLOR_BORDE};
            border-radius: 8px;
            color: {COLOR_TEXTO};
            padding: 7px 12px;
            font-family: '{FUENTE_UI}';
            font-size: 12px;
        }}
        QComboBox {{
            padding: 6px 32px 6px 12px;
            min-height: 20px;
        }}
        QComboBox:hover {{
            border-color: #3f4654;
            background-color: #191c24;
        }}
        QComboBox:on {{
            border-color: {COLOR_ACENTO};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border: none;
            border-left: 1px solid rgba(255, 255, 255, 0.06);
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            {flecha_css}
        }}
        QDateEdit {{
            padding: 5px 8px;
            font-weight: bold;
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {{
            border: 1px solid {COLOR_ACENTO};
        }}
        QComboBox QAbstractItemView {{
            background-color: #1a1d24;
            color: {COLOR_TEXTO};
            selection-background-color: {COLOR_ACENTO};
            selection-color: #ffffff;
            border: 1px solid {COLOR_BORDE};
            border-radius: 8px;
            padding: 4px;
            outline: 0;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 28px;
            padding: 4px 10px;
            border-radius: 4px;
        }}
    """


def _estilo_boton(color=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER, tamano_fuente: int = 12):
    return f"""
        QPushButton {{
            background-color: {color};
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-family: '{FUENTE_UI}';
            font-size: {tamano_fuente}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {color_hover};
        }}
        QPushButton:disabled {{
            background-color: #1a1d24;
            color: #64748b;
        }}
    """


def _estilo_boton_secundario(tamano_fuente: int = 12):
    return f"""
        QPushButton {{
            background-color: {COLOR_SECUNDARIO};
            color: {COLOR_TEXTO};
            border: 1px solid {COLOR_BORDE};
            border-radius: 8px;
            padding: 8px 16px;
            font-family: '{FUENTE_UI}';
            font-size: {tamano_fuente}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {COLOR_SECUNDARIO_HOVER};
            border-color: #475569;
        }}
        QPushButton:disabled {{
            background-color: #1a1d24;
            color: #64748b;
        }}
    """


def _estilo_boton_peligro(tamano_fuente: int = 12):
    return f"""
        QPushButton {{
            background-color: {COLOR_PELIGRO};
            color: #fef2f2;
            border: 1px solid #7f1d1d;
            border-radius: 8px;
            padding: 8px 16px;
            font-family: '{FUENTE_UI}';
            font-size: {tamano_fuente}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PELIGRO_HOVER};
        }}
        QPushButton:disabled {{
            background-color: #1a1d24;
            color: #64748b;
        }}
    """


def _estilo_scrollbar():
    return f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px 2px 0px 2px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_SCROLLBAR_HANDLE};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {COLOR_SCROLLBAR_HOVER};
        }}
        QScrollBar::handle:vertical:pressed {{
            background: #64748b;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: transparent;
            border: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 2px 0px 2px 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLOR_SCROLLBAR_HANDLE};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {COLOR_SCROLLBAR_HOVER};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: transparent;
            border: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
    """


def _estilo_tabla():
    return f"""
        QTableWidget {{
            background-color: {COLOR_INPUT};
            alternate-background-color: #191c23;
            color: {COLOR_TEXTO};
            border: 1px solid {COLOR_BORDE};
            border-radius: 10px;
            gridline-color: #232732;
            font-family: '{FUENTE_UI}';
            font-size: 12px;
        }}
        QHeaderView::section {{
            background-color: #1a1d24;
            color: {COLOR_TEXTO_TENUE};
            padding: 8px 10px;
            border: none;
            border-bottom: 1px solid {COLOR_BORDE};
            font-family: '{FUENTE_UI}';
            font-size: 11px;
            font-weight: bold;
        }}
        QTableWidget::item {{
            padding: 6px 8px;
        }}
        QTableWidget::item:selected {{
            background-color: #1e3a8a;
            color: #ffffff;
        }}
        {_estilo_scrollbar()}
    """


def _tarjeta() -> QFrame:
    tarjeta = QFrame()
    tarjeta.setStyleSheet(f"""
        QFrame {{
            background-color: {COLOR_TARJETA};
            border-radius: 14px;
            border: 1px solid {COLOR_BORDE};
        }}
    """)
    return tarjeta


def _etiqueta(texto: str, tenue: bool = False, tamano: int = 12, negrita: bool | None = None) -> QLabel:
    label = QLabel(texto)
    es_negrita = (QFont.Bold if not tenue else QFont.Normal) if negrita is None else (QFont.Bold if negrita else QFont.Normal)
    label.setFont(QFont(FUENTE_UI, tamano, es_negrita))
    color = COLOR_TEXTO_TENUE if tenue else COLOR_TEXTO
    label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return label


def _titulo(texto: str, tamano: int = 18) -> QLabel:
    label = QLabel(texto)
    label.setFont(QFont(FUENTE_UI, tamano, QFont.Bold))
    label.setStyleSheet(f"color: {COLOR_TEXTO}; background: transparent; border: none;")
    return label


def _subtitulo(texto: str, tamano: int = 12) -> QLabel:
    label = QLabel(texto)
    label.setFont(QFont(FUENTE_UI, tamano, QFont.Normal))
    label.setStyleSheet(f"color: {COLOR_TEXTO_TENUE}; background: transparent; border: none;")
    return label
