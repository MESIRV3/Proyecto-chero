# Que es un "schema" (esquema)

## En criollo

Un schema es el **plano de la base de datos**. La lista completa de que tablas existen, que columnas tiene cada una, que tipo de dato guarda cada columna, y que reglas debe cumplir.

Es a la base de datos lo que un plano es a una casa: te dice como esta armada ANTES de construir nada.

## La analogia

Imaginate que una BD es un edificio:
- El schema (schema.sql) = el plano del arquitecto
- La base de datos (asistencia.db) = el edificio ya construido
- Los CREATE TABLE = las instrucciones para levantar cada pared

Si querés saber "como esta armada esta casa?", miras el plano, no las paredes.

## Que contiene un schema

En este proyecto, `database/schema.sql` tiene:

```sql
CREATE TABLE alumno (
    numero   INTEGER PRIMARY KEY,        -- que columnas tiene
    nombre   TEXT    NOT NULL,
    apellido TEXT    NOT NULL,
    ...
);

CREATE TABLE asistencia (
    ...
    UNIQUE(alumno_numero, materia_id, fecha)  -- que reglas tiene
);
```

O sea, todo esto:

1. **Que tablas existen** (alumno, curso, asistencia, etc)
2. **Que columnas tiene cada tabla** (numero, nombre, apellido)
3. **Que tipo de dato** va en cada columna (INTEGER, TEXT, DATE)
4. **Que restricciones** tiene (PRIMARY KEY, NOT NULL, UNIQUE, CHECK)
5. **Como se relacionan las tablas** (FOREIGN KEY)

## Por que va en un archivo separado y no metido en el codigo Python

El schema esta en `database/schema.sql` por tres razones:

### 1. Es documentacion viva
Cualquiera que abre el archivo ve EXACTAMENTE como es la BD.
No hace falta correr nada para entender la estructura.

### 2. Es reusable
Con un solo `crear_bd.py` que ejecute ese schema, podes:
- Crear la BD en tu PC
- Crear la misma BD en la PC de la escuela
- Crear la misma BD en un servidor
- Resetear si algo se rompe (borrar todo y arrancar limpio)

### 3. Es independiente del lenguaje
El schema es SQL puro. Python lo lee, pero tambien lo podria leer Java, PHP,
o cualquier otro lenguaje. Si migras la app, el schema queda igual.

## Diferencia entre "schema" y "base de datos"

| Schema (schema.sql) | Base de datos (asistencia.db) |
|---------------------|-------------------------------|
| El plano | El edificio construido |
| Es un archivo de texto | Es un archivo binario |
| Lo lee cualquiera | Lo lee sqlite3 |
| Contiene SOLO estructura | Contiene estructura + datos |
| Pesa pocos KB | Crece con cada registro |

## Como se usa en este proyecto

```bash
# 1. Tenes el plano (schema.sql)
cat database/schema.sql

# 2. Lo ejecutas para construir el edificio
python database/crear_bd.py

# 3. Ahora tenes edificio (asistencia.db) con todas las tablas vacias

# 4. Despues cargas datos de prueba
python database/cargar_datos_prueba.py
```

## Que pasa si cambio el schema

Si modificas `schema.sql` (agregas una columna, una tabla, etc), los cambios NO se aplican solos a `asistencia.db`. Tenes que:

1. Cambiar `schema.sql`
2. Borrar `asistencia.db` (o usar un script de migracion)
3. Volver a correr `crear_bd.py`

Para un proyecto chico como este esta bien. Para un proyecto grande se usan
"migraciones" (herramientas que actualizan la BD sin borrarla), pero eso es
para mas adelante.

## Lo importante

- Schema = el plano de la BD
- Esta en `database/schema.sql`
- Contiene tablas, columnas, tipos, restricciones y relaciones
- Es texto plano, lo lee cualquiera
- Es independiente del lenguaje de programacion
- Si lo cambias, tenes que regenerar la BD

## Donde se ve en este proyecto

- `database/schema.sql` - el schema completo (10 tablas)
- `database/crear_bd.py` - lee el schema y crea la BD
