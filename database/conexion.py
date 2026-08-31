"""Modulo de conexion a la base de datos."""
import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager


def _calcular_db_path() -> Path:
    """
    Devuelve la ruta donde vive asistencia.db.

    - En desarrollo (corriendo con 'python main.py'): al lado de este
      archivo, dentro de database/.
    - Empaquetado con PyInstaller: sys.executable apunta al .exe real.
      OJO ACA: no se puede usar Path(__file__) para esto, porque en un
      build --onefile ese archivo vive dentro de la carpeta temporal
      (_MEIPASS) que PyInstaller crea y BORRA en cada ejecucion. Si la
      base quedara ahi, se perderian todos los datos cada vez que se
      cierra el programa (y la primera vez ni siquiera existiria, porque
      nunca se agrego a 'datas' en el .spec).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "asistencia.db"
    return Path(__file__).parent / "asistencia.db"


# Ruta a la base de datos, calculada una sola vez
DB_PATH = _calcular_db_path()


@contextmanager
def conexion():
    """
    Context manager para abrir y cerrar conexiones de forma segura.

    Uso:
        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alumno")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
