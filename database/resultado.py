"""Clase para devolver resultados de operaciones de forma uniforme."""
class Resultado:
    """
    Representa el resultado de una operacion.
    Puede ser exitosa (ok=True) o fallida (ok=False).
    """

    def __init__(self, ok: bool, mensaje: str, datos=None):
        self.ok = ok
        self.mensaje = mensaje
        self.datos = datos

    @classmethod
    def exito(cls, mensaje: str = "Operacion exitosa", datos=None):
        return cls(ok=True, mensaje=mensaje, datos=datos)

    @classmethod
    def error(cls, mensaje: str, datos=None):
        return cls(ok=False, mensaje=mensaje, datos=datos)

    def __repr__(self):
        estado = "OK" if self.ok else "ERROR"
        return f"Resultado({estado}: {self.mensaje})"
