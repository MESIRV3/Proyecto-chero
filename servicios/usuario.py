"""Servicios de usuarios: autenticacion y gestion."""
import sqlite3
from database.conexion import conexion
from database.resultado import Resultado


def autenticar(username: str, password: str) -> Resultado:
    """
    Valida usuario y contraseña.
    Por ahora compara password en texto plano (datos de prueba).
    En produccion se usara bcrypt.
    """
    if not username or not password:
        return Resultado.error("Usuario y contrasena son obligatorios")

    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido, username, rol, activo
            FROM usuario
            WHERE username = ? AND password = ?
        """, (username, password))

        fila = cursor.fetchone()
        if not fila:
            return Resultado.error("Usuario o contrasena incorrectos")

        if not fila["activo"]:
            return Resultado.error("Usuario desactivado")

        return Resultado.exito(
            "Login exitoso",
            datos=dict(fila)
        )
