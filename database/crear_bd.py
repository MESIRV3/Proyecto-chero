"""Script para crear la base de datos desde el schema."""
import sqlite3
from pathlib import Path


def crear_base_datos():
    # Construye la ruta al schema.sql
    schema_path = Path(__file__).parent / "schema.sql"

    # Lee el contenido del schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Conecta (esto crea el archivo si no existe)
    db_path = Path(__file__).parent / "asistencia.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ejecuta el schema
    cursor.executescript(schema_sql)

    # Confirma los cambios
    conn.commit()
    conn.close()

    print(f"Base de datos creada en: {db_path}")


if __name__ == "__main__":
    crear_base_datos()
