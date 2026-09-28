"""Helpers visuales y paleta de colores compartidos para paneles de interfaz.

Conjunto de constantes y funciones de estilo reutilizables por los distintos
paneles (admin, hub, asistencia_preview) para mantener una UI coherente.
"""
from PySide6.QtWidgets import QFrame, QLabel
from PySide6.QtGui import QFont


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
