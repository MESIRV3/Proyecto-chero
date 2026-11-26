# Asistencia Escolar — Guía completa del proyecto

> **Qué es esto:** una aplicación de escritorio para gestionar la asistencia de un colegio (ciclo lectivo, cursos, alumnos, usuarios y asistencias), con un panel de métricas (HUB) y navegación por sidebar. Está escrita en Python + PySide6 + SQLite.
>
> **Para quién es esta guía:** para cualquier persona del equipo que necesite entender el proyecto rápido, **sin conocimiento previo del código**. Los conceptos técnicos se explican sobre la marcha y hay un glosario en la §11.
>
> **Referencias de código:** toda mención a una variable, función, clase o método cita su ubicación como `carpeta/archivo:líneas` (ej. `servicios/dashboard.py:7-47`), verificada contra el commit `d095a3a`.

---

## Mapa de lectura (empezá por acá)

| Si vos... | Leé |
|---|---|
| Tenés 5 minutos | §1 y §2 |
| Querés correr la app ya | §2 |
| Vas a tocar código | §3 a §7 |
| Tocás solo una capa | §3 + su tabla de archivos en §4 |
| Tenés que compilar el .exe | §9 |
| Querés entender los "porqué" | §7 (decisiones de diseño) |
| Venís de un rol no técnico | §1, §5 y §11 |

---

## 1. El proyecto en 5 minutos

### Qué hace la app

Gestiona el día a día de un colegio:

- **Ciclo lectivo**: el año escolar (ej. 2026), con fechas de inicio/fin. Si no existe, la app lo crea sola al arrancar (`obtener_o_crear_ciclo_actual`, `servicios/ciclo_lectivo.py:8-32`).
- **Cursos**: año + división + especialidad (Computación/GAO en 3° a 6°) + turno (Mañana/Tarde).
- **Alumnos**: legajo numérico único — `numero` es PK (`database/schema.sql:31`) — DNI, nacionalidad, curso al que pertenecen. La baja es **lógica** (se marca `activo=0` en `servicios/alumno.py:132`; columna `activo` en `database/schema.sql:37`), no se borra: el historial de asistencias se preserva.

- **Usuarios**: admin, directivo, preceptor, profesor (role `CHECK` en `database/schema.sql:57-58`) — con contraseña hasheada (bcrypt, `hashear_password`, `servicios/usuario.py:6-9`). Hoy la GUI completa es para `admin`; los otros roles autentican pero aún no tienen pantalla propia — reciben un "Bienvenido" y la ventana se cierra (`interfaz/login.py:328-330`, §10).

- **Asistencias**: dos sistemas que conviven — `lista_diaria` (`database/schema.sql:86-99`, la de la preceptora: presente/ausente/tarde/retirado, una vez por día) y `asistencia` (`database/schema.sql:103-116`, la del profesor: presente/ausente, por materia y día). La GUI actual consume `asistencia` en modo consulta vía `listar_asistencias_de_alumno` (`servicios/asistencia.py:94-111`).

- **HUB**: pantalla de inicio con métricas del ciclo (alumnos activos/dados de baja, cursos, asistencias de hoy y de la semana) y accesos rápidos (`obtener_metricas_hub`, `servicios/dashboard.py:7-47`).

### Stack tecnológico

| Componente | Tecnología | Nota |
|---|---|---|
| Lenguaje | Python 3.14 | Se usa la biblioteca estándar todo lo posible |
| GUI | PySide6 6.11 (Qt para Python) | Vive **solo** en `interfaz/` |
| Base de datos | SQLite vía `sqlite3` (stdlib) | Archivo externo `database/asistencia.db` |
| Contraseñas | bcrypt 5.0 | Única dependencia "pesada" fuera de Qt |
| Tests | `unittest` (stdlib) | 9 tests, corren sin pantalla (headless) |
| Build | PyInstaller (`main.spec`) | Genera un .exe único |

### La arquitectura en 30 segundos

Cuatro capas. Las dependencias van **en una sola dirección** (la de arriba conoce a la de abajo, nunca al revés):

```
interfaz/     GUI (PySide6) — la ÚNICA capa que conoce Qt
    ↓  llama funciones de servicio y recibe un Resultado
servicios/    Lógica de negocio — 100% libre de Qt
    ↓  with conexion()
database/     Acceso a la BD + contrato Resultado + schema
    ↓  sqlite3
asistencia.db Archivo externo con 10 tablas
```

### Las 3 reglas de oro (innegociables)

1. **`servicios/` y `database/` NUNCA importan PySide6/Qt.** Se puede verificar con un grep (da 0 resultados) y con un hecho: toda la suite de tests corre sin display. Consecuencia: el 100% de la lógica de negocio es testeable sin tocar la GUI.

2. **Toda operación pública de un servicio devuelve `Resultado(ok, mensaje, datos)`** (`database/resultado.py:2-23`, constructor en `:8-11`). Los errores de negocio *esperados* (curso duplicado, credenciales inválidas, alumno dado de baja) son **datos**, no excepciones. La UI hace `if not resultado.ok: mostrar(mensaje)` sin anidar try/except. Las excepciones *técnicas* (se cayó la BD) se capturan dentro del servicio y salen como `Resultado.error` (`database/resultado.py:17-19`).

3. **Todo acceso a la BD pasa por `conexion()`** (`database/conexion.py:31-50`), un *context manager* que hace commit si todo salió bien (`:45`), rollback + raise si algo falló (`:47-48`), y close siempre (`:50`). Nadie abre `sqlite3` por su cuenta (excepción: `crear_base_datos` en `database/crear_bd.py:6-26`, `sqlite3.connect` en `:16`, porque cuando corre la BD todavía no existe).

> **¿Por qué importa todo esto?** Porque la lógica de negocio se puede probar automáticamente sin GUI ni base real, y porque migrar a otro motor de base de datos (ej. PostgreSQL) tocaría **un solo archivo**: `database/conexion.py` (`:31-50`, el único `sqlite3.connect` de la app en `:41`).

---

## 2. Camino rápido: cómo correrla

```powershell
# 1. Instalar dependencias
pip install PySide6 bcrypt
# (agregá pyinstaller si vas a compilar el .exe)

# 2. Crear la base de datos (solo la primera vez)
python database/crear_bd.py

# 3. Cargar datos de prueba (idempotente: se puede correr mil veces)
python database/cargar_datos_prueba.py

# 4. Correr la app
python main.py
#    Login de prueba: admin / admin123

# 5. Correr los tests
python -m unittest discover -s tests
#    Esperado: "Ran 9 tests ... OK"
```

### Scripts utilitarios

| Script | Qué hace | Ojo |
|---|---|---|
| `database/verificar_bd.py` | Lista las tablas creadas en la BD (`verificar`, `database/verificar_bd.py:6-26`) | Solo lectura |
| `database/consultar_datos.py` | Consultas de ejemplo con JOINs (`mostrar_resumen`, `database/consultar_datos.py:6-65`) | Solo lectura |
| `probar_conexion.py` | Smoke test de la capa de conexión (`probar_conexion`, `probar_conexion.py:5-43`) | Solo lectura |
| `probar_servicios.py` | Smoke test de servicios de alumno/asistencia | **ESCRIBE 5 asistencias reales en la BD** (`probar_servicios.py:34-50`) |
| `migrar_a_bcrypt.py` | Migra contraseñas de texto plano a bcrypt (`migrar_contrasenas`, `migrar_a_bcrypt.py:16-93`) | One-shot idempotente: saltea las ya hasheadas (`migrar_a_bcrypt.py:48-50`) |

---

## 3. Arquitectura capa por capa

### 3.1 `database/` — el cimiento

- **`database/conexion.py`** (~50 líneas) — El corazón del acceso a datos.
  - Calcula `DB_PATH` (`database/conexion.py:28`, función `_calcular_db_path` `database/conexion.py:8-24`).
    Si la app corre **congelada** (exe de PyInstaller, `sys.frozen`, chequeo en `database/conexion.py:22-23`), la BD se busca **junto al .exe** (`:23`); en desarrollo, junto al código (`:24`).
    La BD nunca va dentro del bundle del exe porque PyInstaller onefile borra su carpeta temporal en cada ejecución (→ datos perdidos). Ver §9.
  - Expone `conexion()` (`database/conexion.py:31-50`): un *context manager* (`with conexion() as conn:`).
    Configura `row_factory=sqlite3.Row` (`database/conexion.py:42`, permite leer columnas por nombre, como un dict), hace commit al salir bien (`:45`), rollback + re-lanzamiento ante error (`:47-48`), y close siempre (`:50`).
  - **Detalle clave para testing**: `conexion()` lee la variable `DB_PATH` del módulo en cada llamada (`database/conexion.py:41`), aunque su valor inicial se calcula al importar (`:28`).
    Eso permite que los tests la reemplacen con `mock.patch` y redirijan toda la app a una BD temporal (§8).

- **`database/resultado.py`** (~23 líneas) — Define `Resultado` (`database/resultado.py:2-23`), el DTO (objeto de transferencia de datos) de dos estados.
  - Campos: `ok` (bool), `mensaje` (str), `datos` (opcional) — constructor en `:8-11`.
  - Classmethods `Resultado.exito(mensaje, datos)` (`database/resultado.py:13-15`) y `Resultado.error(mensaje)` (`database/resultado.py:17-19`).
  - Es el contrato de toda la capa de servicios.

- **`database/schema.sql`** (`:1-142`) — Las 10 tablas con sus restricciones (detalle completo en §5).

- **`database/crear_bd.py`** — `crear_base_datos()` (`database/crear_bd.py:6-26`) lee `database/schema.sql` y lo ejecuta contra un archivo nuevo (`executescript`, `database/crear_bd.py:20`).
  - No usa `conexion()` porque la BD aún no existe (problema huevo-gallina; abre `sqlite3.connect` directo en `:16`).
  - Se corre una sola vez por máquina.

- **`database/cargar_datos_prueba.py`** (~162 líneas) — `cargar_datos()` (`database/cargar_datos_prueba.py:12-158`) es un seed **idempotente**: borra todas las tablas y resetea `sqlite_sequence` antes de sembrar (`:24-26`).
  - Carga: ciclo 2026 (`:29-32`); 3 cursos, 5°1 = Computación con turno "Mañana" (`:40-44`); 5 usuarios con bcrypt (**`admin/admin123`**, `:54-60`).
  - Y además: 5 materias de 5°1 (`:72-79`); horario del lunes con recreos (`:86-107`); 30 alumnos con legajos desde 10000000 (`:116-130`); días hábiles de marzo a junio (`:134-144`).

- **`database/verificar_bd.py`** / **`database/consultar_datos.py`** — utilidades de inspección (`verificar`, `database/verificar_bd.py:6-26` / `mostrar_resumen`, `database/consultar_datos.py:6-65`; solo lectura).

### 3.2 `servicios/` — lógica de negocio (Qt-free)

Todos los módulos siguen el mismo patrón: validar → consultar/mutuar vía `conexion()` (`database/conexion.py:31-50`) → devolver `Resultado` (`database/resultado.py:2-23`). Resumen módulo por módulo (ficha completa en §4):

- **`servicios/usuario.py`** — Auth con bcrypt.
  - Hasheo y verificación: `hashear_password` (`servicios/usuario.py:6-9`), `verificar_password` (`servicios/usuario.py:12-25`).
  - `autenticar()` (`servicios/usuario.py:28-57`) con SELECT parametrizado (anti SQL-injection, `:35-39`).
  - **Mensaje genérico idéntico** para "usuario inexistente" (`:43`) y "clave errónea" (`:49`) — anti enumeración de usuarios.
  - Chequeo de `activo` (`:45-46`), y **borra la clave del dict** (`del datos_usuario["password"]`, `:52`) antes de entregarlo a la UI.

- **`servicios/alumno.py`** — CRUD de alumnos.
  - Alta con validaciones (`agregar_alumno` `servicios/alumno.py:66-101`) y listado con filtros dinámicos (`listar_alumnos` `servicios/alumno.py:104-124`).
  - **Baja lógica** (`dar_de_baja_alumno` `servicios/alumno.py:127-137`, `activo=0` en `:132`) y reactivación (`reactivar_alumno` `servicios/alumno.py:140-150`).
  - Eliminación definitiva **protegida** (`eliminar_alumno_definitivo` `servicios/alumno.py:153-171`: se niega si el alumno tiene asistencias o listas diarias, `:158-165` — protege la integridad referencial).
  - `cambiar_curso_alumno` (`servicios/alumno.py:174-187`, muta `curso_id` en `:182` — atención, esto motiva la decisión D1 en §7).

- **`servicios/curso.py`** — CRUD de cursos con reglas de negocio.
  - Constantes: años sin especialidad = 1°/2° (`ANIOS_SIN_ESPECIALIDAD` `servicios/curso.py:7`); con especialidad = 3°-6° (`ANIOS_CON_ESPECIALIDAD` `:8`); `ESPECIALIDADES_VALIDAS` `:9`; `TURNOS_VALIDOS` = ("Mañana", "Tarde") `:10`.
  - Alta con normalización (`agregar_curso` `servicios/curso.py:31-60`, validación `_validar_especialidad` `:18-28`).
  - Listado con **subconsulta correlacionada** que cuenta alumnos activos por curso (`listar_cursos` `servicios/curso.py:63-84`, subconsulta en `:73-74`).
  - Eliminación protegida (`eliminar_curso` `servicios/curso.py:87-104`).

- **`servicios/ciclo_lectivo.py`** — `obtener_o_crear_ciclo_actual()` (`servicios/ciclo_lectivo.py:8-32`).
  - Busca el ciclo del año en curso y **lo crea automáticamente si no existe** (03-01 al 12-15, fechas en `servicios/ciclo_lectivo.py:27`).
  - La app nunca se cae por falta de ciclo.

- **`servicios/asistencia.py`** — Registro y consulta.
  - `registrar_asistencia()` (`servicios/asistencia.py:7-60`) con **UPSERT** (`ON CONFLICT(alumno_numero, materia_id, fecha) DO UPDATE`, `servicios/asistencia.py:45-56`: corregir el mismo día pisa el registro en vez de fallar por UNIQUE).
  - `calcular_porcentaje_asistencia()` (`servicios/asistencia.py:63-91`) que **solo cuenta días hábiles** (subconsulta `fecha IN (SELECT ... FROM dia_habil WHERE es_habil=1)`, `:87`, no un JOIN) y usa `NULLIF` para no dividir por cero (`:80`).
  - `listar_asistencias_de_alumno()` (`servicios/asistencia.py:94-111`) devuelve una **lista cruda** (excepción honesta al contrato Resultado — la UI la envuelve en try/except).

- **`servicios/dashboard.py`** — `obtener_metricas_hub(ciclo_id)` (`servicios/dashboard.py:7-47`).
  - Las 6 métricas del HUB: alumnos activos `:16-17`, alumnos de baja `:18-19`, total de cursos `:20-21`, asistencias de hoy `:22-28`, asistencias de la semana `:30-36`, año del ciclo `:13-15`; el dict se arma en `:38-45`.
  - Las asistencias se cuentan con scoping por ciclo vía JOIN `asistencia → materia → curso` (`:24-25` y `:32-33`, la decisión D1, §7).
  - Caída de BD → `Resultado.error` (`:46-47`).

### 3.3 `interfaz/` — la GUI (PySide6)

- **`interfaz/login.py`** (~337 líneas) — `VentanaLogin` (`interfaz/login.py:37-337`).
  - Ventana de login *frameless* (sin barra de título nativa, flag en `:43`): barra de título custom (minimizar/maximizar/cerrar/arrastrar, `:64-128` y `:180-205`), fondo de imagen, tarjeta glassmorphism con sombra (`:131-143`).
  - Autentica contra `servicios.usuario.autenticar` (`interfaz/login.py:313`); si el rol es `admin`, crea `VentanaAdmin(usuario=datos)` (`interfaz/login.py:325-326`, el dict **ya viene sin password** — se borra en `servicios/usuario.py:52`) y se cierra (`interfaz/login.py:330`).
  - Contiene `resource_path()` (`interfaz/login.py:15-21`) para resolver imágenes tanto en desarrollo como dentro del exe (§9).

- **`interfaz/admin.py`** (~837 líneas, el archivo más grande — 3 clases):

  - **`PanelCursos`** (`interfaz/admin.py:133-285`): ABM de cursos.
    - Combo de año que habilita/deshabilita especialidad según la regla 1°/2° vs 3°-6° (`_actualizar_especialidad_habilitada`, `interfaz/admin.py:219-226`, consulta `servicios/curso.py:8`).
    - Tabla con columna ID oculta (`setColumnHidden(5, True)`, `interfaz/admin.py:205`).
    - Al dar de alta un curso dispara el callback `on_cambio` (definido en `interfaz/admin.py:139`, invocado en `:238-239` y `:260-261`, que refresca los combos del panel de alumnos).

  - **`PanelAlumnos`** (`interfaz/admin.py:288-563`): ABM de alumnos.
    - Filtro por curso + checkbox "mostrar inactivos" (`interfaz/admin.py:305-313`).
    - Formulario de alta que arranca oculto (`tarjeta_form.hide()`, `interfaz/admin.py:407`) y se despliega in-place (`_alternar_formulario_alta`, `:451-455`).
    - Nacionalidad con largo máximo de documento dinámico por país (dict `NACIONALIDADES`, `interfaz/admin.py:79-115`, aplicado por `_actualizar_maximo_dni`, `:444-449`).
    - Baja/reactivación/cambio de curso desde la tabla (`_dar_de_baja` `:531-539`, `_reactivar` `:541-549`, `_cambiar_curso` `:551-563`).

  - **`VentanaAdmin(usuario=None)`** (`interfaz/admin.py:566-828`, firma con default en `:569`): la ventana principal post-rediseño.
    - Resuelve el ciclo lectivo actual (llamada en `interfaz/admin.py:591-596`; si falla, muestra diálogo crítico pero **sigue viva** con `ciclo_id=None`, `:593-594`).
    - **Sidebar izquierdo** de 220px (`setFixedWidth(220)`, `interfaz/admin.py:604`): branding, 4 botones checkables en `QButtonGroup` exclusivo `:652-653` con estilo `:checked` en el QSS `:632-636`, footer con nombre/rol del usuario `:664-670`, botón "Cerrar sesión" `:672-676`.
    - **`QStackedWidget`** con 4 páginas (`interfaz/admin.py:678-690`): `[0] PanelHub, [1] PanelCursos, [2] PanelAlumnos, [3] PanelAsistencia`.
    - Wiring bidireccional: click en botón → cambia página (`idClicked→setCurrentIndex`, `:692`); cambio de página (ej. por acceso rápido del HUB) → sincroniza el botón (`currentChanged→setChecked`, `:693`).
    - Barra de título custom preservada (arrastrar/min/max/cerrar, `_armar_barra_titulo` `:722-794`).
    - Logout = `_cerrar_sesion()` (`interfaz/admin.py:715-720`, §7 D4).
    - Soporta `python -m interfaz.admin` standalone sin usuario (`:831-837`).
- **`interfaz/hub.py`** (~200 líneas) — `PanelHub(ciclo_id)` (`interfaz/hub.py:30-200`).
  - Banner de bienvenida (saludo según franja horaria `_saludo_por_hora` `interfaz/hub.py:149-155` + año del ciclo `:157-161`).
  - 5 tarjetas KPI glassmorphism (👥 activos, 🏫 cursos, 📝 asistencias hoy, 📝 semana, ⚠️ bajas — definidas en `interfaz/hub.py:93-99`).
  - Accesos rápidos "+ Agregar Alumno" / "+ Crear Curso" que **emiten señales** (`navegar_a_alumnos`, `navegar_a_cursos`, declaradas en `interfaz/hub.py:33-34`, conectadas a `emit` en `:74` y `:80`) — no navegan directamente, las conecta `interfaz/admin.py:694-695` (desacoplamiento).
  - Tabla resumen de cursos con conteo de alumnos (`_cargar_tabla_cursos`, `interfaz/hub.py:177-196`).
  - **Carga datos en `showEvent`** (`interfaz/hub.py:140-142`, cada vez que volvés a Inicio refresca; §7 D7).
  - Errores se muestran inline, nunca con diálogos modales apilados (`label_error` `interfaz/hub.py:49-52`, `_mostrar_error` `:198-200`).

- **`interfaz/asistencia_preview.py`** (~196 líneas) — `PanelAsistencia(ciclo_id)` (`interfaz/asistencia_preview.py:32-196`).
  - Vista **preliminar de solo lectura** (badge honesto "Vista preliminar", `:55-60`).
  - Selector de alumno (se refresca en `showEvent` `:40-42` vía `recargar_alumnos` `:116-142`, preservando la selección `:117` y `:134-137`) + rango de fechas (`:73-85`) + tabla de asistencias (fecha/materia/estado/observaciones, `:105-114`).
  - Guardas: fechas invertidas → mensaje explícito (`_consultar`, `interfaz/asistencia_preview.py:154-159`); servicio crudo → try/except con copy amigable (`:161-171`).
  - Lo diferido a futuro: registrar asistencia, porcentajes, lista diaria, filtros.

- **`interfaz/estilos.py`** (~93 líneas) — Paleta oscura y helpers de estilo compartidos (QSS).
  - `FUENTE_MONO` (`interfaz/estilos.py:10`), constantes `COLOR_*` (`:12-21`), `_estilo_input` (`:24-39`), `_estilo_boton` (`:42-54`), `_estilo_tabla` (`:57-75`), `_tarjeta` (QFrame glassmorphism, `:78-85`), `_etiqueta` (`:88-93`).
  - Extraído de `interfaz/admin.py` a propósito (§7 D6): lo consumen `interfaz/admin.py:35-52`, `interfaz/hub.py:18-25` y `interfaz/asistencia_preview.py:18-27` sin crear imports circulares.
  - **No importa servicios ni lógica** (`interfaz/estilos.py:6-7`, solo PySide6) — es pura vista.

### 3.4 `tests/` — transversal

- **`tests/test_usuario.py`** (3 tests)
  - Round-trip de hasheo bcrypt (`test_hashear_y_verificar_password`, `tests/test_usuario.py:14-19`).
  - Autenticación del admin del seed — depende de la BD real: deuda conocida (`test_autenticacion_admin`, `tests/test_usuario.py:21-28`).
  - Rechazo de inexistente (`tests/test_usuario.py:30-31`) con verificación de que el dict devuelto no trae la password (`assertNotIn('password', ...)`, `tests/test_usuario.py:25`).

- **`tests/test_dashboard.py`** (6 tests) — Suite **hermética** de las métricas del HUB.
  - `setUp` (`tests/test_dashboard.py:21-36`) crea una SQLite temporal con el `database/schema.sql` real (`:25-29`), la siembra con dos ciclos (2030/2031) deliberadamente distintos (`_sembrar_datos` `:48-158`), y parchea `DB_PATH` (`mock.patch`, `:31-33`).
  - Cubre: valores exactos por ciclo (`:160-181`), scoping — asistencias de OTRO ciclo no cuentan (`:183-194`), borde de la ventana semanal (hoy−7 entra, hoy−8 queda fuera, `:196-203`).
  - Y además: ciclo inexistente → ceros (`:205-214`), `ciclo_id=None` → ceros (`:216-225`), y caída de BD simulada → `Resultado.error` sin propagar excepciones (`:227-232`).

---

## 4. Ficha archivo por archivo

### Raíz

| Archivo | Qué es | Gotcha para conocer |
|---|---|---|
| `main.py` | Entry point: QApplication → VentanaLogin → `app.exec()` (`main()`, `main.py:7-11`) | `app.exec()` (`main.py:11`) bloquea (event loop); la app termina por `app.quit()` (X de la barra: `interfaz/login.py:173-178` y `interfaz/admin.py:804-808`) o por "última ventana cerrada" — clave para entender el logout |
| `main.spec` | Configuración PyInstaller | `hiddenimports=['bcrypt']` (`main.spec:9`) — sin eso el .exe crashea al loguear (§9); `console=False` (`main.spec:32`); onefile (`EXE` con binaries+datas, `main.spec:19-38`) |
| `README.txt` | Documentación original en español | Tiene drift admitido: menciona Pillow (`README.txt:24`, nadie la importa — 0 usos de `PIL` en el repo) y "contraseñas en texto plano" (`README.txt:63`, obsoleto tras bcrypt) |
| `probar_conexion.py` | Smoke test de conexión (`probar_conexion`, `probar_conexion.py:5-43`) | Solo lectura, contra la BD real |
| `probar_servicios.py` | Smoke test de servicios (`probar_servicios`, `probar_servicios.py:10-79`) | **Escribe 5 asistencias reales** (`probar_servicios.py:34-50`) — no es un unittest |
| `migrar_a_bcrypt.py` | Migración one-shot de contraseñas (`migrar_contrasenas`, `migrar_a_bcrypt.py:16-93`) | Idempotente: saltea hashes `$2b$/$2a$` (`migrar_a_bcrypt.py:48-50`); pide confirmación ("SI") o flag `-y` (`migrar_a_bcrypt.py:97-103`) |
| `generate_files.py` | Artifact histórico (untracked) | Generó un *borrador* temprado de `interfaz/hub.py` (con timer de 60s: `QTimer` + `start(60_000)` en `generate_files.py:118-121`, y callbacks); el hub final evolucionó con señales (`interfaz/hub.py:33-34`) y showEvent (`interfaz/hub.py:140-142`). No es código de la app; decisión de borrarlo pendiente |
| `apuntes/*.md` | Notas didácticas del autor | Analogías schema=plano (`apuntes/que_es_schema.md`) / BD=edificio, cursor=lapicera (`apuntes/que_es_cursor.md`), conn=context manager (`apuntes/que_es_conn.md`) |

### `database/`

| Archivo | Qué es | Gotcha |
|---|---|---|
| `database/conexion.py` | Único punto de acceso a la BD (`conexion`, `database/conexion.py:31-50`) | `DB_PATH` (`database/conexion.py:28`) se lee por llamada (`:41`) → habilita `mock.patch` en tests; BD externa al exe, ruta congelada en `:22-23` (PyInstaller borra `_MEIPASS`) |
| `database/resultado.py` | DTO `Resultado(ok, mensaje, datos)` (`database/resultado.py:2-23`) | Contrato de toda la capa de servicios |
| `database/schema.sql` | Las 10 tablas (`database/schema.sql:1-142`) | Restricciones = reglas de negocio (§5) |
| `database/crear_bd.py` | Crea la BD desde `database/schema.sql` (`crear_base_datos`, `database/crear_bd.py:6-26`) | No usa `conexion()`: `sqlite3.connect` directo en `database/crear_bd.py:16` (la BD aún no existe) |
| `database/cargar_datos_prueba.py` | Seed idempotente (`cargar_datos`, `database/cargar_datos_prueba.py:12-158`) | Borra todo y resetea `sqlite_sequence` antes de sembrar (`:24-26`); turno "Mañana" (`:41-43`) con ñ debe coincidir exacto con `TURNOS_VALIDOS` (`servicios/curso.py:10`) |
| `database/verificar_bd.py` | Lista tablas (`verificar`, `database/verificar_bd.py:6-26`) | Diagnóstico |
| `database/consultar_datos.py` | Consultas de ejemplo (`mostrar_resumen`, `database/consultar_datos.py:6-65`) | JOIN (`:29-34`), LEFT JOIN + COALESCE para recreos (`:41-48`) |

### `servicios/`

| Archivo | Qué es | Gotcha |
|---|---|---|
| `servicios/usuario.py` | Auth + bcrypt (`autenticar`, `servicios/usuario.py:28-57`) | Mensaje genérico anti-enumeración (`servicios/usuario.py:43` y `:49`); `del datos_usuario["password"]` antes de devolver (`:52`); dual-read, acepta hash y legado transitorio (`verificar_password`, `:17-23`) |
| `servicios/alumno.py` | CRUD alumnos (`agregar_alumno` `servicios/alumno.py:66-101`, `listar_alumnos` `:104-124`, etc.) | `numero` es PK sin AUTOINCREMENT (`database/schema.sql:31`, legajo de la escuela); baja lógica (`dar_de_baja_alumno`, `servicios/alumno.py:127-137`); DELETE físico protegido por FK (`eliminar_alumno_definitivo`, `:153-171`); `cambiar_curso_alumno` muta `curso_id` (`:182`, → D1) |
| `servicios/curso.py` | CRUD cursos + reglas (`agregar_curso`, `servicios/curso.py:31-60`) | Reglas "1°/2° sin especialidad" viven acá (`ANIOS_SIN_ESPECIALIDAD` `servicios/curso.py:7-8`, `_validar_especialidad` `:18-28`), no en el schema (dependen de otra columna); subconsulta correlacionada para contar alumnos activos (`listar_cursos`, `:73-74`) |
| `servicios/ciclo_lectivo.py` | Ciclo actual (`obtener_o_crear_ciclo_actual`, `servicios/ciclo_lectivo.py:8-32`) | Auto-crea el ciclo si falta (`:22-30`, lenient: la app nunca muere) |
| `servicios/asistencia.py` | Registro y consulta (`registrar_asistencia`, `servicios/asistencia.py:7-60`) | UPSERT `ON CONFLICT DO UPDATE` (`servicios/asistencia.py:45-56`); porcentaje solo sobre días hábiles (`calcular_porcentaje_asistencia`, `:63-91`, subconsulta `:87`); `listar_asistencias_de_alumno` devuelve lista cruda (`:94-111`, la UI la envuelve) |
| `servicios/dashboard.py` | Métricas del HUB (`obtener_metricas_hub`, `servicios/dashboard.py:7-47`) | JOIN de scoping `asistencia→materia→curso` (`servicios/dashboard.py:22-28` y `:30-36`, D1); `except → Resultado.error` (`:46-47`) |

### `interfaz/`

| Archivo | Qué es | Gotcha |
|---|---|---|
| `interfaz/login.py` | Ventana de login (`VentanaLogin`, `interfaz/login.py:37-337`) | Frameless (`interfaz/login.py:43`) + barra custom; drag solo fuera de la tarjeta (`mousePressEvent`, `:180-188`); `resource_path` para `_MEIPASS` (`:15-21`); rol no-admin → "Bienvenido" y cierra (`:328-330`, gap, §10) |
| `interfaz/admin.py` | Paneles + ventana principal (`PanelCursos` `interfaz/admin.py:133-285`, `PanelAlumnos` `:288-563`, `VentanaAdmin` `:566-828`) | 3 clases en 1 archivo; sidebar + QStackedWidget (`_armar_sidebar_y_stack`, `:601-705`); wiring bidireccional (`:692-695`); logout sin `app.quit()` (`_cerrar_sesion`, `:715-720`); `resource_path` duplicado de login (DRY pendiente, `:58-64` vs `interfaz/login.py:15-21`); docstring de cabecera desactualizado (`:1-18`, aún habla de rol "directivo" y `VentanaAdmin()` sin argumentos) |
| `interfaz/hub.py` | Panel HUB (`PanelHub`, `interfaz/hub.py:30-200`) | Carga en `showEvent` (no en `__init__`; `showEvent` `:140-142`, constructor `:36-41`); señales de navegación (no acoplamiento, `:33-34`); errores inline no-modales (`:49-52`) |
| `interfaz/asistencia_preview.py` | Vista preliminar read-only (`PanelAsistencia`, `interfaz/asistencia_preview.py:32-196`) | Refresh de alumnos en `showEvent` (`:40-42`); guardas de fechas invertidas (`:154-159`); try/except sobre API cruda (`:161-171`) |
| `interfaz/estilos.py` | Paleta compartida (QSS, `interfaz/estilos.py:1-93`) | Extraído para evitar import circular hub→admin (D6); no importa servicios (`:6-7`, solo PySide6) |
| `__init__.py` (todos los paquetes) | Marcadores de paquete | `database/__init__.py`, `servicios/__init__.py`, `interfaz/__init__.py`, `tests/__init__.py` — vacíos (0 bytes), deliberadamente |

---

## 5. La base de datos (10 tablas)

```
ciclo_lectivo 1──N curso 1──N materia 1──N asistencia N──1 alumno
                    │  │                                  │
                    │  └──N horario                       ├──N lista_diaria
                    └──N alumno (curso_id MUTABLE)         │
usuario 1──N (registrado_por en asistencia/lista_diaria)  │
justificacion → lista_diaria_id O asistencia_id (XOR)     │
dia_habil (fecha PK) ── filtra el % de asistencia ────────┘
```

| Tabla | Clave | Restricciones defendibles |
|---|---|---|
| `ciclo_lectivo` | id, `anio UNIQUE` (`database/schema.sql:7-8`) | Un año = un ciclo (`database/schema.sql:6-11`) |
| `curso` | id, FK ciclo (`database/schema.sql:19`, `:25`) | `UNIQUE(ciclo_id, anio, division, especialidad, turno)` (`database/schema.sql:24`) — no hay dos 5°1 Computación Mañana el mismo año. `turno` es **columna TEXT, no entidad** |
| `alumno` | **`numero` PK sin AUTOINCREMENT** (`database/schema.sql:31`) | El legajo lo define la escuela. `dni UNIQUE` (`:34`). `curso_id` FK **mutable** (`:36`, `:38`). `activo DEFAULT 1` (`:37`) → baja lógica |
| `materia` | id, `curso_id FK NOT NULL` (`database/schema.sql:46-47`) | Pertenece al curso y es **estable en el tiempo** — puente del scoping D1 |
| `usuario` | id, `username UNIQUE NOT NULL` (`database/schema.sql:55`) | `rol CHECK IN ('profesor','preceptor','directivo','admin')` (`database/schema.sql:57-58`) — rol validado a nivel BD; password bcrypt (`:56`) |
| `horario` | id, FK curso (`database/schema.sql:65`, `:74`) | **CHECK XOR** (`database/schema.sql:77-80`): recreo ⇒ materia/usuario NULL; clase ⇒ ambos NOT NULL. No existe "clase de nadie" ni "recreo con materia" |
| `lista_diaria` | id, FK alumno (`database/schema.sql:87`, `:96`) | `UNIQUE(alumno_numero, fecha)` (`database/schema.sql:98`); `estado CHECK (presente, ausente, tarde, retirado)` (`:90-91`) — la lista de la preceptora |
| `asistencia` | id, FK alumno + **FK materia** (`database/schema.sql:112-113`) | `UNIQUE(alumno_numero, materia_id, fecha)` (`database/schema.sql:115`) — blanco del UPSERT; `estado CHECK (presente, ausente)` (`:108-109`). **No tiene FK directa a curso** — de acá nace D1 |
| `justificacion` | id (`database/schema.sql:120`) | **CHECK XOR** (`database/schema.sql:130-133`): apunta a `lista_diaria_id` O `asistencia_id`, nunca a ambas |
| `dia_habil` | **`fecha` PK** (`database/schema.sql:139`) | `es_habil` + motivo (`:140-141`); el % de asistencia solo cuenta días hábiles |

**Reglas que viven en el servicio, no en el schema:** "1° y 2° no llevan especialidad" (`ANIOS_SIN_ESPECIALIDAD` y `_validar_especialidad`, `servicios/curso.py:7-8` y `:18-28`) — es una regla que depende de otra columna, más mantenible en Python que con un CHECK retorcido. El comentario del schema lo dice explícitamente (`database/schema.sql:14-16`).

---

## 6. Flujos extremo a extremo

### 6.1 Arranque → login → panel de administración

1. `main.py`: crea `QApplication` (`main.py:8`) → `VentanaLogin().mostrar()` (`main.py:9-10`, método en `interfaz/login.py:336-337`) → `app.exec()` (`main.py:11`, el event loop bloquea acá).

2. Usuario tipea + Enter/click (`btn_ingresar.clicked` y `returnPressed`, `interfaz/login.py:298-299`) → `_intentar_login` (`interfaz/login.py:302-334`) → `servicios.usuario.autenticar()` (`servicios/usuario.py:28-57`, llamada en `interfaz/login.py:313`).

3. `autenticar`:
   - SELECT parametrizado (`servicios/usuario.py:35-39`) → compara bcrypt (`servicios/usuario.py:48`, función `verificar_password` `:12-25`).
   - Si OK, **quita la password del dict** (`servicios/usuario.py:52`) → `Resultado.exito(datos=usuario)` (`servicios/usuario.py:54-57`).

4. Rol `admin` → `VentanaAdmin(usuario=datos)` (`interfaz/login.py:324-327`) → muestra admin → cierra login (`interfaz/login.py:330`).

5. `VentanaAdmin.__init__` (`interfaz/admin.py:569-599`):
   - Resuelve ciclo actual (`obtener_o_crear_ciclo_actual`, `servicios/ciclo_lectivo.py:8-32`, llamada en `interfaz/admin.py:591`; si falla → diálogo crítico pero la ventana sigue viva con `ciclo_id=None`, `interfaz/admin.py:593-594`).
   - Arma sidebar + stack con los 4 paneles recibiendo el ciclo (`_armar_sidebar_y_stack`, `interfaz/admin.py:601-705`; construcción de paneles `:680-685`).

### 6.2 El HUB carga sus métricas

1. El stack muestra la página 0 → se dispara `PanelHub.showEvent` (`interfaz/hub.py:140-142`) → `_cargar_datos()` (`interfaz/hub.py:144-147`).

2. → `servicios.dashboard.obtener_metricas_hub(ciclo_id)` (`servicios/dashboard.py:7-47`, llamada en `interfaz/hub.py:164`):
   - 6 queries (las de asistencias con JOIN `asistencia→materia→curso` filtrando ciclo: hoy `servicios/dashboard.py:22-28`, semana `:30-36`).
   - `Resultado.exito(datos={6 claves})` (`servicios/dashboard.py:38-45`).

3. El hub pinta:
   - Las tarjetas (`card.valor_label.setText`, `interfaz/hub.py:173-174`, label creado en `interfaz/hub.py:132-137`).
   - El año del ciclo en el banner (`interfaz/hub.py:172` y `_actualizar_banner` `:157-161`).
   - La tabla de cursos (`curso.listar_cursos(ciclo_id)`, `servicios/curso.py:63-84`, llamada en `interfaz/hub.py:178`, con conteo de alumnos activos por subconsulta `servicios/curso.py:73-74`).

4. Si algo falla:
   - Tarjetas quedan en "—" (valor inicial del label, `interfaz/hub.py:132`, y reset en `:167-168`).
   - Mensaje de error **inline** (no modal, `interfaz/hub.py:198-200`), sin crash.

### 6.3 Acceso rápido del HUB → navegación

1. Click en "+ Agregar Alumno" → el botón **emite la señal** `navegar_a_alumnos` (`interfaz/hub.py:33`, conectada a `.emit` en `interfaz/hub.py:74`; el hub NO conoce el stack).

2. `interfaz/admin.py` conectó esa señal a `stack.setCurrentIndex(2)` (`interfaz/admin.py:694`; la de cursos en `:695`).

3. El cambio de índice dispara `currentChanged` → lambda que hace `setChecked(True)` sobre el botón del sidebar (`interfaz/admin.py:693`) → el QSS `:checked` lo pinta de activo (`interfaz/admin.py:632-636`).

4. No hay loop infinito: setear el mismo índice no re-dispara la señal.

### 6.4 Logout ("Cerrar sesión")

1. Click → `VentanaAdmin._cerrar_sesion()` (`interfaz/admin.py:715-720`, botón y conexión en `interfaz/admin.py:672-676`).

2. Import **local** de `VentanaLogin` (`interfaz/admin.py:717`, dentro del método — evita el ciclo de imports admin↔login).

3. `self.ventana_login = VentanaLogin()` (`interfaz/admin.py:718`) — la **referencia fuerte** es deliberada: un widget Qt sin padre ni referencia Python es destruido por el garbage collector.

4. `.mostrar()` PRIMERO (`interfaz/admin.py:719`), `self.close()` después (`interfaz/admin.py:720`).

5. **Nunca `app.quit()`** — eso mataría el event loop y toda la app. La app sigue viva; el `app.quit()` real solo existe en la X de la barra de título (`interfaz/admin.py:804-808` y `interfaz/login.py:173-178`).

### 6.5 Registrar y consultar asistencia

- **Registrar** (hoy sin GUI; lo consumen scripts/futuro): `servicios.asistencia.registrar_asistencia` (`servicios/asistencia.py:7-60`).
  - Valida estado ∈ {presente, ausente} (`:21-22`), alumno existente **y activo** (`:29-34`), materia existente (`:37-42`).
  - UPSERT sobre `UNIQUE(alumno_numero, materia_id, fecha)` (`:45-56` y restricción en `database/schema.sql:115`) → `Resultado`.

- **Consultar (GUI actual)**: `PanelAsistencia._consultar` (`interfaz/asistencia_preview.py:144-190`).
  - Guardas: alumno seleccionado (`:145-149`), `desde ≤ hasta` (`:154-159`).
  - `listar_asistencias_de_alumno` (`servicios/asistencia.py:94-111`; lista cruda, JOIN materia `:106`, ORDER fecha DESC `:109`) dentro de try/except (`interfaz/asistencia_preview.py:161-171`) → filas a la tabla.
  - Read-only garantizado: este panel no llama ningún servicio de escritura (tabla con `NoEditTriggers`, `interfaz/asistencia_preview.py:110`).

### 6.6 Alta de alumno y cambio de curso (por qué existe D1)

1. Alta: `PanelAlumnos._agregar_alumno` (`interfaz/admin.py:476-503`) → `servicios.alumno.agregar_alumno` (`servicios/alumno.py:66-101`: validaciones `:68-75`, curso existe `:83-85`, INSERT `:87-93`; IntegrityError → mensaje amable `:95-101`) → recarga de tabla (`interfaz/admin.py:501`).

2. Cambio de curso: `cambiar_curso_alumno` (`servicios/alumno.py:174-187`) hace `UPDATE alumno SET curso_id=...` (`servicios/alumno.py:182`) — **el alumno se mueve, sus asistencias históricas NO** (quedan ancladas a `materia→curso`). Este detalle es exactamente lo que la decisión D1 protege (§7).

---

## 7. Decisiones de diseño y su porqué

> Esta sección es el corazón de la defensa del proyecto: cada decisión tiene problema → solución → alternativa rechazada.

### D1 — El scoping de asistencias por ciclo usa `materia`, no `alumno`

- **Problema**: la tabla `asistencia` (`database/schema.sql:103-116`) no tiene FK a curso. Para contar "asistencias del ciclo 2026" hay que llegar a `curso` por algún camino. El camino obvio es `asistencia → alumno.curso_id → curso`.

- **Trampa**: `alumno.curso_id` es **mutable** (`database/schema.sql:36`; `cambiar_curso_alumno` en `servicios/alumno.py:174-187`, `UPDATE` en `:182`). Si un alumno se cambia de curso (o repite y pasa a otro ciclo), sus asistencias históricas "migrarían" al ciclo nuevo y las métricas mentirían.

- **Solución**: contar vía `asistencia → materia → curso` — `materia.curso_id` es inmutable (`database/schema.sql:46`), así que cada asistencia queda anclada al ciclo en el que realmente ocurrió.

- **Dónde**: `servicios/dashboard.py:22-28` (query de hoy) y `servicios/dashboard.py:30-36` (query de la semana) + test de scoping en `tests/test_dashboard.py:183-194`.

### D2 — Tests sobre SQLite temporal, no sobre la BD real

- **Problema**: ¿cómo testear queries SQL sin ensuciar/corromper `asistencia.db`?

- **Alternativas rechazadas**:
  - (a) Sembrar la BD real — no hermético y un crash la corrompe.
  - (b) Mockear cursores con datos falsos — no prueba el SQL real, que ES el núcleo del cambio.

- **Solución**: `tempfile.mkstemp` (`tests/test_dashboard.py:22`) + `executescript` del `database/schema.sql` real (`tests/test_dashboard.py:25-29`) + `mock.patch("database.conexion.DB_PATH")` (`tests/test_dashboard.py:31-33`).

- **Por qué funciona**: SQL auténtico, semillas controladas (ciclos futuros 2030/2031 en `tests/test_dashboard.py:56-65` que no chocan con `date.today()`), cero contacto con la BD real. `conexion()` lee `DB_PATH` en cada llamada (`database/conexion.py:41`).

### D3 — `VentanaAdmin(usuario=None)` con default (`interfaz/admin.py:569`)

- Permite abrir el panel sin login para desarrollo/pruebas: `python -m interfaz.admin` (`interfaz/admin.py:831-837`, firma con default en `interfaz/admin.py:569`).

- Con `None`, el footer muestra "Sesión local / Modo standalone" (`_actualizar_footer_usuario`, `interfaz/admin.py:707-713`, texto en `:713`).

- **Alternativa rechazada**: un singleton de sesión global — un solo consumidor no justifica la infraestructura.

### D4 — Logout como secuencia invertida del login, sin `app.quit()`

- **Bug histórico que previene**: llamar a una ruta que hace `app.quit()` mata el event loop completo (toda la app, no solo la ventana) — ver `app.quit()` en `interfaz/login.py:178` y `interfaz/admin.py:808`.

- **Patrón** (`_cerrar_sesion`, `interfaz/admin.py:715-720`):
  - Crear `VentanaLogin` con **referencia fuerte** (`self.ventana_login = ...`, `interfaz/admin.py:718` — sin ella, PySide6 garbage-collectea el widget huérfano y la ventana nunca aparece).
  - Mostrarla (`:719`), y recién entonces `self.close()` (`:720`).

- **Tradeoff aceptado**: cada logout agrega un eslabón a la cadena de referencias (login₀ → admin → login₁ → ...). Crece acotado por sesión; se prefirió a `WA_DeleteOnClose` porque ese flag cambiaría la semántica de la X de la barra.

### D5 — `QStackedWidget` + `QButtonGroup` exclusivo con wiring bidireccional

- `QStackedWidget` (`interfaz/admin.py:678-690`) muestra una página a la vez; el estado "activo" vive en el grupo de botones (`QButtonGroup` exclusivo, `interfaz/admin.py:652-653`; QSS `:checked`, `interfaz/admin.py:632-636`).

- **Cable doble**: `idClicked → setCurrentIndex` (`interfaz/admin.py:692`) y `currentChanged → setChecked` (`interfaz/admin.py:693`). Cualquier origen de navegación (botón del sidebar O señal del HUB, `interfaz/admin.py:694-695`) deja ambos sincronizados.

- **Alternativa rechazada**: `QTabWidget` — la UI pedía sidebar con branding, footer de usuario y logout, cosas que las pestañas no ofrecen.

### D6 — Extracción de `interfaz/estilos.py`

- **Problema**: `interfaz/hub.py`, `interfaz/asistencia_preview.py` y `interfaz/admin.py` necesitan la misma paleta. Si hub importara estilos desde admin (y admin importa hub para armar el stack, `interfaz/admin.py:54`) → **ciclo de imports**.

- **Solución**: mover la paleta/helpers **verbatim** a `interfaz/estilos.py` (`:1-93`), un módulo hermano que no importa nada de la app (solo PySide6, `interfaz/estilos.py:6-7`).

- **Resultado**: los consumidores quedan en `interfaz/admin.py:35-52`, `interfaz/hub.py:18-25`, `interfaz/asistencia_preview.py:18-27`. Los paneles existentes quedaron byte-idénticos.

### D7 — El HUB carga datos en `showEvent`, no en `__init__`

- El stack mantiene todas las páginas vivas; si la carga fuera en el constructor (`PanelHub.__init__`, `interfaz/hub.py:36-41` — solo arma la UI), los KPIs quedarían congelados al abrir la app.

- Con `showEvent` (`interfaz/hub.py:140-142` → `_cargar_datos` `:144-147`), cada vuelta a Inicio refresca (sin doble lectura inicial).

- Errores → label inline (`interfaz/hub.py:49-52` y `:198-200`), nunca `QMessageBox` apilado sobre otros diálogos.

### D8 — La vista de Asistencia es preliminar y read-only

- Primera versión = consulta pura (combo de alumno + rango de fechas + tabla, `interfaz/asistencia_preview.py:64-114`). Sin escritura: menos superficie de bug mientras el flujo de registro no tiene pantalla propia.

- El badge "Vista preliminar" lo hace honesto (`interfaz/asistencia_preview.py:55-60`).

- Diferido explícito: registrar, porcentajes, lista diaria, filtros.

### Decisiones previas al rediseño (también defendibles)

- **`Resultado` vs excepciones** (`database/resultado.py:2-23`): separa "error de negocio esperado" (dato) de "bug/fallo técnico" (excepción capturada en el servicio, patrón `try/except → Resultado.error` visible p. ej. en `servicios/alumno.py:95-101`). La UI queda plana, sin try/except anidados.

- **Migración a bcrypt dual-read**: `verificar_password` acepta hash nuevo y password legada transitoriamente (`servicios/usuario.py:17-23`); el script de migración es idempotente y saltea hashes `$2b$/$2a$` (`migrar_a_bcrypt.py:48-50`). Migración sin downtime ni sesiones rotas.

- **¿bcrypt y no sha256?** sha256 es rápido y sin salt → rainbow tables y fuerza bruta sobre una fuga; bcrypt trae salt único automático (`hashear_password` con `bcrypt.gensalt()`, `servicios/usuario.py:8-9`) y work-factor lento a propósito.

- **Ventanas frameless con barra custom**: coherencia visual glassmorphism login→admin (`Qt.FramelessWindowHint`, `interfaz/login.py:43` y `interfaz/admin.py:575`). El costo (reimplementar drag/min/max/close — `interfaz/login.py:180-205` y `interfaz/admin.py:789-828` — y z-order en `resizeEvent`, `interfaz/login.py:157-162`) es deliberado.

- **Baja lógica de alumnos**: `activo=0` (`servicios/alumno.py:132`, columna `database/schema.sql:37`) preserva el historial (las FK de asistencia/lista_diaria siguen apuntando a algo, `database/schema.sql:96` y `:112`). El DELETE físico existe (`servicios/alumno.py:166`) pero se niega si hay historial (`:158-165`).

---

## 8. Testing y calidad

- **Suite**: `python -m unittest discover -s tests` → 9 tests (3 en `tests/test_usuario.py:14-31` + 6 en `tests/test_dashboard.py:160-232`), headless, exit 0.

- **Metodología**: TDD estricto en el cambio del dashboard.
  - El test se escribió PRIMERO y falló con evidencia numérica: los conteos globales daban hoy=7/semana=9, los esperados por ciclo eran 2/4 — asserts en `tests/test_dashboard.py:180-181`, el famoso `7 != 2` del RED.
  - Recién después se implementó el JOIN que lo hizo pasar (GREEN): `servicios/dashboard.py:22-28` (hoy) y `servicios/dashboard.py:30-36` (semana).

- **Hermeticidad**: patrón D2 (§7) — `tests/test_dashboard.py:22-33`. Post-corrida, `git status` limpio = la BD de desarrollo no se toca.

- **Simulación de fallos**: la caída de BD se testa parcheando `servicios.dashboard.conexion` con `side_effect=Exception` (`tests/test_dashboard.py:228`) — se parcha **donde se usa, no donde se define**.

- **GUI**: no hay capa de tests Qt automatizada (decisión documentada). Se valida con probes offscreen (`QT_QPA_PLATFORM=offscreen`: 44 aserciones de navegación/logout/wiring en la verificación del cambio) + checklist manual de 12 ítems con `python main.py`.

- **Deudas honestas** (conocidas y registradas):
  - `test_autenticacion_admin` depende del seed real `admin/admin123` (`tests/test_usuario.py:21-28`).
  - Un assert redundante en `tests/test_dashboard.py` (`:200-201` repite los de `:180-181`).
  - Conexiones sqlite de los tests cierran por GC y no por `close()` explícito (el `with sqlite3.connect(...)` de `tests/test_dashboard.py:28` y `:35` hace commit pero no close).
  - Tooltip con excepción cruda en `interfaz/asistencia_preview.py:170`.

---

## 9. Build y distribución (PyInstaller)

- **Comando**: `pyinstaller main.spec` → .exe **onefile** sin consola (`console=False`, `main.spec:32`).

- **`hiddenimports=['bcrypt']`** (`main.spec:9`): bcrypt es una extensión compilada con imports condicionales que el análisis estático de PyInstaller no ve. Sin esta línea, el .exe crasheaba al intentar loguear (único bug de build conocido, ya arreglado).

- **Imágenes**: viajan dentro del bundle (`datas` del spec, `main.spec:8`) y se resuelven con `resource_path()` (`interfaz/login.py:15-21`; duplicada en `interfaz/admin.py:58-64`). En modo frozen lee de `sys._MEIPASS` (`interfaz/login.py:17-18`, la carpeta temporal donde onefile se descomprime).

- **La BD NO viaja en el bundle**: `_MEIPASS` se borra en cada ejecución → cualquier dato escrito ahí se pierde.
  - Por eso `database/conexion.py` busca `asistencia.db` **junto al .exe** cuando la app está congelada (`_calcular_db_path`, `database/conexion.py:8-24`, chequeo `sys.frozen` en `:22-23`; el porqué está comentado en el propio código, `:14-20`).
  - Consecuencia de despliegue: en cada máquina nueva hay que correr `database/crear_bd.py` + `database/cargar_datos_prueba.py` (o copiar una BD existente) junto al exe.

- **Gaps a admitir**: no hay `requirements.txt` ni `pyproject.toml` (las dependencias viven solo en el `README.txt:16-28`); no hay CI, linter ni type-checker.

---

## 10. Estado actual y gaps conocidos

Lo que **sí** está: gestión completa de cursos y alumnos (GUI admin), HUB con métricas reales por ciclo, consulta preliminar de asistencias, login/logout con bcrypt, sidebar + navegación por stack, suite de tests headless, build a .exe.

Lo que **todavía no** (por diseño o por pendiente):

| Gap | Estado |
|---|---|
| GUI para roles no-admin (profesor/preceptor/directivo) | Autentican y reciben "Bienvenido", pero no hay pantalla — la app cierra (`interfaz/login.py:328-330`) |
| Registrar asistencia desde la GUI | El servicio existe y está probado (`registrar_asistencia`, `servicios/asistencia.py:7-60`); falta la pantalla |
| Pantalla de `lista_diaria` (preceptora) | Schema y restricciones listas (`database/schema.sql:86-99`); sin servicio ni GUI (ningún módulo de `servicios/` escribe la tabla) |
| Porcentajes de asistencia en GUI | Servicio existe (`calcular_porcentaje_asistencia`, `servicios/asistencia.py:63-91`); sin pantalla |
| `requirements.txt` / `pyproject.toml` | No existe; deps documentadas en `README.txt:16-28` |
| README desactualizado | Menciona Pillow (`README.txt:24`, sin uso) y "texto plano" (`README.txt:63`, pre-bcrypt) |
| `generate_files.py` | Artifact de proceso untracked (borrador de hub con timer, `generate_files.py:118-121`); decidir borrar o ignorar |
| `listar_cursos(None)` | Lenient: si `ciclo_id` es None no arma el WHERE (`servicios/curso.py:68`, función `:63-84`) → lista cursos de todos los ciclos |

---

## 11. Glosario mínimo

| Término | Significado en este proyecto |
|---|---|
| **Context manager** (`with ... as`) | Bloque que garantiza limpieza automática: `conexion()` hace commit/rollback/close solo |
| **DTO** | Objeto simple que solo transporta datos — `Resultado(ok, mensaje, datos)` |
| **PK / FK** | Primary key (identidad de la fila) / Foreign key (referencia a otra tabla) |
| **AUTOINCREMENT** | SQLite asigna el id automáticamente; `alumno.numero` NO lo tiene porque el legajo lo define la escuela |
| **UNIQUE** | Restricción: no hay dos filas iguales en esa combinación de columnas |
| **CHECK** | Restricción que valida valores (ej. `rol IN (...)`, XOR de horario/justificacion) |
| **UPSERT** (`ON CONFLICT DO UPDATE`) | INSERT que, si choca con UNIQUE, actualiza la fila existente en vez de fallar |
| **Baja lógica** | Marcar `activo=0` en vez de DELETE: el historial se preserva |
| **Hash / salt / bcrypt** | Hash = transformación irreversible; salt = dato aleatorio único por contraseña; bcrypt = hash lento a propósito (work factor) para resistir fuerza bruta |
| **Señal / slot (Qt)** | Mecanismo de eventos: un widget *emite* una señal, otro la *escucha* sin que se conozcan entre sí (desacoplamiento) |
| **QStackedWidget** | Contenedor que muestra una sola página a la vez (como un mazo de cartas) |
| **QButtonGroup exclusivo** | Grupo donde un solo botón puede estar checked a la vez |
| **QSS** | "CSS de Qt": hojas de estilo para pintar widgets (el `:checked` del sidebar) |
| **showEvent** | Hook de Qt que se dispara cada vez que un widget se hace visible — el HUB lo usa para refrescar datos |
| **Frameless** | Ventana sin decoración nativa; el proyecto reimplementa barra de título, arrastre y min/max/close |
| **Event loop** (`app.exec()`) | El corazón de Qt: procesa eventos hasta que alguien llama `app.quit()` o cierra la última ventana |
| **PyInstaller / onefile / `_MEIPASS`** | Compila la app a un .exe único; al correr se descomprime en una carpeta temporal (`sys._MEIPASS`) que **se borra al cerrar** |
| **hiddenimports** | Módulos que PyInstaller no detecta por análisis estático y hay que declarar a mano (bcrypt) |
| **Headless** | Correr sin pantalla — posible acá porque la lógica no toca Qt |
| **mock / patch** | Reemplazar un objeto real por uno controlado en tests (ej. `DB_PATH` por una BD temporal) |
| **TDD / RED / GREEN** | Escribir el test primero, verlo fallar por la razón correcta (RED), implementar lo mínimo para que pase (GREEN) |
| **SDD** | Spec-Driven Development: el proceso con el que se hizo el rediseño del HUB (proposal → specs → design → tasks → apply → verify), con artefactos en `openspec/` |
| **Glassmorphism** | Estilo visual de tarjetas translúcidas (`rgba(255,255,255,.04)` + bordes suaves + sombras) |

---

## 12. Preguntas frecuentes (banco rápido)

1. **¿Qué es `Resultado` y por qué no excepciones?** — DTO `ok/mensaje/datos` (`database/resultado.py:2-23`, constructor `:8-11`). Errores esperados son datos; la UI no anida try/except. Excepciones técnicas mueren en el servicio y salen como `Resultado.error` (`database/resultado.py:17-19`).

2. **¿Por qué una conexión por operación y no una global?** — SQLite es file-based y las conexiones son baratas; `conexion()` abre/commit/closea en cada operación (`database/conexion.py:31-50`, `sqlite3.connect` en `:41`, close en `:50`); evita transacciones huérfanas entre pantallas; la atomicidad coincide con la operación de negocio.

3. **¿Por qué bcrypt y no sha256?** — sha256 es rápido y sin salt (rainbow tables/brute force); bcrypt trae salt automático (`bcrypt.gensalt()`, `servicios/usuario.py:8`) y es lento a propósito (`servicios/usuario.py:6-9` y `:12-25`).

4. **¿Por qué el scoping por ciclo usa `materia` y no `alumno`?** — `alumno.curso_id` muta con los cambios de curso (`servicios/alumno.py:182`); `materia.curso_id` es estable (`database/schema.sql:46`). Vía alumno, un repitente arrastraría su historial a otro ciclo. Los JOIN de scoping: `servicios/dashboard.py:22-28` (hoy) y `:30-36` (semana), test en `tests/test_dashboard.py:183-194` (D1).

5. **¿Por qué el HUB carga en `showEvent` y no en `__init__`?** — Las páginas del stack viven todo el tiempo; `showEvent` (`interfaz/hub.py:140-142`) refresca cada vez que volvés a Inicio sin timers ni doble carga inicial — el constructor solo arma la UI (`interfaz/hub.py:36-41`) (D7).

6. **¿Cómo evitan que los tests toquen la BD real?** — SQLite temporal creada con el `database/schema.sql` real + `mock.patch("database.conexion.DB_PATH")` (`tests/test_dashboard.py:22-33`). Funciona porque la ruta se lee en cada llamada (`database/conexion.py:41`) (D2).

7. **¿Cómo se simula una caída de BD en tests?** — Parchando `servicios.dashboard.conexion` (donde se usa, no donde se define) con `side_effect=Exception` (`tests/test_dashboard.py:228`) → se verifica que salga `Resultado.error` sin propagar (`tests/test_dashboard.py:227-232`, reflejo del `except` en `servicios/dashboard.py:46-47`).

8. **¿Por qué `QStackedWidget` y no `QTabWidget`?** — La UI pedía sidebar con branding, footer de usuario y logout; el stack solo muestra páginas (`interfaz/admin.py:678-690`) y el estado activo vive en el QButtonGroup (`interfaz/admin.py:652-653`) (D5).

9. **¿Cómo se sincronizan sidebar y páginas?** — Doble cable: `idClicked→setCurrentIndex` (`interfaz/admin.py:692`) y `currentChanged→setChecked` (`interfaz/admin.py:693`). Mismo índice no re-dispara la señal → sin loop.

10. **¿Por qué el logout no usa `app.quit()`?** — `quit()` mata el event loop (toda la app, ver `interfaz/admin.py:808`). Logout = mostrar login nuevo (con referencia fuerte, si no el GC lo destruye — `interfaz/admin.py:718`) y cerrar la ventana actual (`interfaz/admin.py:715-720`) (D4).

11. **¿Qué pasa si hago logout varias veces?** — Se encadenan referencias (login₀→admin→login₁→..., eslabón en `interfaz/admin.py:718`). La app nunca muere; el costo de memoria es acotado por sesión — tradeoff explícito de D4.

12. **¿Por qué `alumno.numero` no es AUTOINCREMENT?** — Es el legajo real que asigna la escuela (`numero INTEGER PRIMARY KEY`, `database/schema.sql:31`); duplicado → IntegrityError traducido a mensaje amable (`servicios/alumno.py:95-101`).

13. **¿Baja lógica o DELETE?** — `activo=0` preserva historial FK (`dar_de_baja_alumno`, `servicios/alumno.py:127-137`); el DELETE definitivo se niega si hay asistencias/listas (`eliminar_alumno_definitivo`, `servicios/alumno.py:158-165`); los KPIs cuentan solo `activo=1` (`servicios/dashboard.py:16-17`).

14. **¿Por qué `resource_path` para imágenes pero BD externa?** — Las imágenes viajan en el bundle y se leen de `_MEIPASS` (solo lectura, ok — `interfaz/login.py:15-21`, rama frozen `:17-18`); la BD necesita escritura persistente y `_MEIPASS` se borra en cada corrida → externa junto al exe (`database/conexion.py:22-23`).

15. **¿Cuál es la regla arquitectónica innegociable y cómo se prueba?** — `servicios/`+`database/` sin Qt: grep da 0 matches y la suite completa corre headless (los 9 tests de `tests/` no necesitan display).

16. **¿Qué gaps tiene el proyecto?** — Ver §10. Admitirlos con plan suma credibilidad en una defensa.

---

*Guía generada desde el estado del repo en `main` (post-rediseño hub-sidebar, commit `d095a3a`). Artefactos formales del proceso SDD (proposal, specs, design con decisiones D1-D8, tasks, verify-report): `openspec/changes/hub-sidebar/`.*
