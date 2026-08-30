# Que es "cursor" y para que sirve

## En criollo

`cursor` es la "lapicera" que te dan despues de abrir una conexion a la base de datos.
Con la lapicera escribis queries (SELECT, INSERT, UPDATE) y traes los resultados.

## La analogia completa

Volvamos a la bovedilla del banco:

```
conn = sqlite3.connect("asistencia.db")
# abriste tu caja fuerte, tenes la llave

cursor = conn.cursor()
# agarraste una lapicera de la mesa

cursor.execute("SELECT * FROM alumno WHERE numero = ?", (12345,))
# escribiste "traeme el alumno con legajo 12345" en un papel

fila = cursor.fetchone()
# leiste el papel: una sola fila (el alumno)
# (o .fetchall() para leer todos los papeles)
```

## Por que se llama asi

Viene de SQL. La "cursor" es la posicion actual en el conjunto de resultados.
Despues de un SELECT, el cursor "apunta" a la primera fila.
Cada vez que hace `fetchone()` o `fetchall()`, el cursor avanza.

## Los 4 metodos principales del cursor

```python
cursor.execute("SELECT ...")       # ejecuta una sola query
cursor.executemany("INSERT ...", lista)  # ejecuta la misma query muchas veces
cursor.fetchone()                  # trae UNA fila (o None si no hay mas)
cursor.fetchall()                  # trae TODAS las filas en una lista
```

## Como se ve en este proyecto

En `servicios/asistencia.py`:

```python
def registrar_asistencia(alumno_numero, materia_id, fecha, estado, profesor_id):
    with conexion() as conn:
        cursor = conn.cursor()                              # agarro la lapicera

        cursor.execute("SELECT numero FROM alumno ...")     # escribo query 1
        if not cursor.fetchone():                           # leo resultado 1
            return Resultado.error("No existe el alumno")

        cursor.execute("SELECT id FROM materia ...")       # escribo query 2
        if not cursor.fetchone():                           # leo resultado 2
            return Resultado.error("No existe la materia")

        cursor.execute("INSERT INTO asistencia ...")       # escribo query 3
        # no hay fetch aca, es un INSERT
    # al salir del with, se hace conn.commit() solo
```

## La relacion conn + cursor

Siempre van juntos y en este orden:

```
1. conn  = conexion a la BD
2. cursor = lapicera para hablar con la BD
3. cursor.execute(...)  ->  hablarle a la BD
4. cursor.fetchone()/fetchall()  ->  leer la respuesta
```

## Preguntas frecuentes

### ¿Por que no usar "conn" directamente?
Porque `conn` representa LA CONEXION (el cable, la puerta, la bovedilla).
`cursor` representa LA OPERACION EN CURSO (la lapicera, la pregunta puntual).
Se separan para que puedas tener VARIAS operaciones simultaneas con UNA sola conexion
(abrir varios cursores a la vez). Ademas hace el codigo mas claro.

### ¿Se cierra el cursor?
Con el `with conexion() as conn:` que usamos, no hace falta.
Al cerrar la conexion se cierra el cursor tambien.

### ¿Y si hago "cursor.execute" sin "fetchone"?
Si es un SELECT: el resultado queda en el cursor pero no lo leiste (desperdicio).
Si es un INSERT/UPDATE/DELETE: no hay nada que leer, asi que esta bien.

## Lo importante

- `conn` = la conexion a la base
- `cursor` = la lapicera para ejecutar queries
- `execute(...)` = escribir la query
- `fetchone()` = leer UNA fila
- `fetchall()` = leer TODAS las filas
- Siempre: primero abrir conexion, despues crear cursor, despues ejecutar

## Donde se usa en este proyecto

Todos los servicios lo usan:
- `servicios/alumno.py` - 3 funciones
- `servicios/asistencia.py` - 3 funciones
- `servicios/usuario.py` - autenticar()
