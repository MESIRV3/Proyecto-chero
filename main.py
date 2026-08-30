"""Punto de entrada de la aplicacion."""
import sys
from PySide6.QtWidgets import QApplication
from interfaz.login import VentanaLogin


def main():
    app = QApplication(sys.argv)
    ventana = VentanaLogin()
    ventana.mostrar()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
