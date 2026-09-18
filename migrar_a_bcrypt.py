"""
Script para migrar contrasenas existentes de texto plano a bcrypt.
"""
import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.conexion import DB_PATH
from servicios.usuario import hashear_password


def migrar_contrasenas(verbose: bool = True) -> bool:
    """Migra todas las contrasenas de texto plano o pendientes a hashes bcrypt."""
    if verbose:
        print("Iniciando migracion de contrasenas a bcrypt...")

    if not DB_PATH.exists():
        print(f"Error: Base de datos no encontrada en {DB_PATH}")
        return False

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT id, username, password, rol FROM usuario")
            usuarios = cursor.fetchall()

            if not usuarios:
                print("No se encontraron usuarios en la base de datos")
                return False

            migrados = 0
            ya_hasheados = 0
            errores = 0

            for usuario in usuarios:
                user_id = usuario["id"]
                username = usuario["username"]
                password_actual = usuario["password"]
                rol = usuario["rol"]

                # Si ya esta hasheado con bcrypt ($2b$ o $2a$), se omite
                if password_actual.startswith(("$2b$", "$2a$")):
                    ya_hasheados += 1
                    continue

                if password_actual == "hash_pendiente":
                    password_plano = f"{rol}123"
                    detalle = f"(asignada clave temporal '{password_plano}')"
                else:
                    password_plano = password_actual
                    detalle = ""

                try:
                    password_hashed = hashear_password(password_plano)
                    cursor.execute(
                        "UPDATE usuario SET password = ? WHERE id = ?",
                        (password_hashed, user_id)
                    )

                    if cursor.rowcount > 0:
                        migrados += 1
                        if verbose:
                            print(f"  OK: Usuario '{username}' migrado {detalle}")
                    else:
                        errores += 1
                        if verbose:
                            print(f"  ERROR: No se actualizo usuario '{username}'")

                except Exception as e:
                    errores += 1
                    if verbose:
                        print(f"  ERROR al hashear para '{username}': {e}")

            conn.commit()

            if verbose:
                print("\nResumen de migracion:")
                print(f"  - Total usuarios: {len(usuarios)}")
                print(f"  - Ya estaban hasheados: {ya_hasheados}")
                print(f"  - Migrados exitosamente: {migrados}")
                print(f"  - Errores: {errores}")

            return errores == 0

    except Exception as e:
        print(f"Error critico durante la migracion: {e}")
        return False


if __name__ == "__main__":
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    if not auto_confirm:
        confirmacion = input(
            "Se migraran las contrasenas no hasheadas a bcrypt.\n"
            "Escribi 'SI' para continuar: "
        )
        auto_confirm = confirmacion.strip().upper() == "SI"

    if auto_confirm:
        exito = migrar_contrasenas()
        if exito:
            print("\nMigracion completada con exito.")
        else:
            print("\nLa migracion finalizo con errores.")
    else:
        print("Migracion cancelada.")