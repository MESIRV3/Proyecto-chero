# Que es "conn" y para que sirve

## En criollo

`conn` es la abreviacion de "connection" (conexion en ingles).
Es la puerta de entrada a la base de datos.

Cuando en Python haces `conn = sqlite3.connect("asistencia.db")`, estas diciendo:
"abreme la puerta a la BD, y guardame el picaporte en `conn` para no tener que volver a llamar a la puerta cada vez".

## La analogia

Imaginate que la BD es una bovedilla de banco.
- `sqlite3.connect(...)` es ir al banco y abrir tu caja fuerte
- `conn` es la llave de tu caja fuerte
- `cursor = conn.cursor()` es agarrar una lapicera para anotar cosas
- `cursor.execute("SELECT ...")`: anotar algo (leer, escribir, etc)
- `conn.commit()`: confirmar las anotaciones
- `conn.close()`: cerrar la caja fuerte y devolver la llave

## Por que se llama asi

Es una convencion mundial. Casi todo el codigo Python que toca bases de datos
usa `conn` o `connection`. Si lo abris en StackOverflow, en GitHub, en
documentacion oficial, lo vas a ver igual.

## Como se ve en este proyecto

En `database/conexion.py` definimos un **context manager** que se encarga de
abrir y cerrar solo:

```python
from database.conexion import conexion

# asi se usa en los servicios (servicios/asistencia.py, servicios/alumno.py)
with conexion() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alumno WHERE numero = ?", (12345,))
    alumno = cursor.fetchone()
```

El `with` se encarga de:
1. Abrir la conexion
2. Darte `conn` para que uses
3. Hacer `commit()` si todo salio bien
4. Hacer `rollback()` si hubo error (deshace los cambios)
5. Cerrar la conexion SIEMPRE, incluso si hay error

Por eso no ves `conn.close()` en los servicios. Esta encapsulado.

## Lo importante

- `conn` = la conexion abierta a la BD
- `cursor` = la herramienta para ejecutar queries dentro de esa conexion
- Siempre van juntos: primero `conn`, despues `cursor`
- Sin cerrar `conn`, la BD queda "ocupada" y podes tener bloqueos

## Mal uso tipico

```python
# MAL: abrir y no cerrar
conn = sqlite3.connect("asistencia.db")
cursor = conn.cursor()
cursor.execute("SELECT ...")
# ... te olvidaste de conn.close()
```

```python
# BIEN: usar el context manager
with conexion() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
# aca ya se cerro solo
```

## Donde se usa en este proyecto

- `database/conexion.py` - define la funcion `conexion()`
- `servicios/alumno.py` - 3 funciones usan `with conexion() as conn`
- `servicios/asistencia.py` - 3 funciones usan `with conexion() as conn`
- `servicios/usuario.py` - `autenticar()` usa `with conexion() as conn`
