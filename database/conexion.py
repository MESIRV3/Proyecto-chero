"""Modulo de conexion a la base de datos."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager


# Ruta a la base de datos, calculada una sola vez
DB_PATH = Path(__file__).parent / "asistencia.db"


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
