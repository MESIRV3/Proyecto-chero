import bcrypt
from database.conexion import conexion
from database.resultado import Resultado


def hashear_password(password: str) -> str:
    """Genera un hash seguro usando bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verificar_password(password_plano: str, password_almacenado: str) -> bool:
    """Verifica si la contrasena ingresada coincide con el hash almacenado."""
    if not password_almacenado or not password_plano:
        return False
    try:
        if password_almacenado.startswith(("$2b$", "$2a$")):
            return bcrypt.checkpw(
                password_plano.encode("utf-8"),
                password_almacenado.encode("utf-8")
            )
        # Compatibilidad defensiva si quedan datos legados en texto plano
        return password_plano == password_almacenado
    except Exception:
        return False


def autenticar(username: str, password: str) -> Resultado:
    """Valida credenciales de usuario contra la base de datos."""
    if not username or not password:
        return Resultado.error("Usuario y contrasena son obligatorios")

    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido, username, password, rol, activo
            FROM usuario
            WHERE username = ?
        """, (username,))

        fila = cursor.fetchone()
        if not fila:
            return Resultado.error("Usuario o contrasena incorrectos")

        if not fila["activo"]:
            return Resultado.error("Usuario desactivado")

        if not verificar_password(password, fila["password"]):
            return Resultado.error("Usuario o contrasena incorrectos")

        datos_usuario = dict(fila)
        del datos_usuario["password"]

        return Resultado.exito(
            "Login exitoso",
            datos=datos_usuario
        )

