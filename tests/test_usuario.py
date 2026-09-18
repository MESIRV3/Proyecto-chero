import unittest
import sys
from pathlib import Path

# Configurar path raiz
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from servicios.usuario import hashear_password, verificar_password, autenticar


class TestServicioUsuario(unittest.TestCase):
    def test_hashear_y_verificar_password(self):
        password = 'clave_secreta_123'
        hashed = hashear_password(password)
        self.assertTrue(hashed.startswith(('$', '$')))
        self.assertTrue(verificar_password(password, hashed))
        self.assertFalse(verificar_password('clave_incorrecta', hashed))

    def test_autenticacion_admin(self):
        res_ok = autenticar('admin', 'admin123')
        self.assertTrue(res_ok.ok)
        self.assertEqual(res_ok.datos['username'], 'admin')
        self.assertNotIn('password', res_ok.datos)

        res_bad = autenticar('admin', 'password_invalido')
        self.assertFalse(res_bad.ok)

    def test_autenticacion_usuario_inexistente(self):
        res = autenticar('usuario_fantasma', '123456')
        self.assertFalse(res.ok)


if __name__ == '__main__':
    unittest.main()
