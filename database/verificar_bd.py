"""Verifica que la base de datos se creo correctamente."""
import sqlite3
from pathlib import Path


def verificar():
    db_path = Path(__file__).parent / "asistencia.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pide a SQLite la lista de tablas
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tablas = cursor.fetchall()

    print("Tablas creadas en la base de datos:")
    print("-" * 40)
    for tabla in tablas:
        print(f"  - {tabla[0]}")

    print(f"\nTotal: {len(tablas)} tablas")

    conn.close()


if __name__ == "__main__":
    verificar()
