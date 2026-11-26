# Verification Report: hub-sidebar

**Change**: hub-sidebar
**Estado verificado**: `main` @ `d095a3a` (integración completa de PR1–PR4, en sync con origin)
**Modo**: Strict TDD (`strict_tdd: true` en openspec/config.yaml; runner `unittest` disponible)
**Alcance**: verificación formal de conformidad spec-vs-implementación, holística (no por slice). Los gates de pre-PR por slice quedan registrados en obs-79/81/82/85.
**Naturaleza**: solo verificación — sin cambios de código ni commits.

---

## Resumen ejecutivo

| Veredicto global | **PASS WITH WARNINGS** |
|---|---|
| Gate 5.2 | **PASS** (4/4 sub-chequeos) |
| Escenarios spec | 19/19 cubiertos: 18 automated + 1 pending-manual (5.1 ítem 9) |
| Deferidas/out-of-scope | 4/4 genuinamente ausentes, nada colado |

**Advertencia central**: el checklist humano 5.1 sigue pendiente del usuario (es su rol por diseño) y la caja 5.1 no debe marcarse sin ejecutarlo. Nada del código verificado es bloqueante para el archive; las sugerencias carry-over son no bloqueantes.

---

## Completeness (tasks.md)

| Métrica | Valor |
|---|---|
| Tasks totales | 10 (1.1, 1.2, 2.1, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1, 5.2) |
| Tasks completas | 8 (todas las de implementación y estilos) |
| Tasks incompletas | 2 — 5.1 (checklist manual usuario) y 5.2 (gate final; **ejecutada en este reporte**, cajas sin tocar: el archive las registra) |

---

## Build & Tests Execution

**Suite (gate 5.2a)**: ✅ exit 0
```text
$ python -m unittest discover -s tests
Ran 9 tests in 1.368s — OK  (verbose: 6 de tests.test_dashboard + 3 de tests.test_usuario)
EXIT: 0
```

**Coverage**: ➖ No disponible (config `coverage: false`; no hay pytest/coverage instalado).
**Quality metrics**: ➖ No disponibles (sin ruff/mypy/black/pyproject).
**Probe de integración hermético**: ✅ 44/44 checks, exit 0
```text
$ python ".../Temp/opencode/probe_final_verify.py"   (QT_QPA_PLATFORM=offscreen, DB_PATH→SQLite temporal)
PROBE OK: 44/44 checks passed  EXIT: 0
```
Post-probe: `git status --porcelain` = solo `?? generate_files.py` → BD dev intacta (hermeticidad probada).

---

## Gate 5.2 (ejecutado aquí)

| # | Sub-chequeo | Resultado | Evidencia |
|---|---|---|---|
| a | Suite exit 0 (9 tests) | ✅ PASS | `Ran 9 tests ... OK`, exit 0 |
| b | `QTabWidget` limpio en `interfaz/` | ✅ PASS | grep full-file 0 matches (0 archivos) |
| c | `git status`: dashboard.py trackeado; generate_files.py untracked; árbol limpio | ✅ PASS | `git ls-files servicios/dashboard.py` → trackeado; status = solo `?? generate_files.py` |
| d | Invariante arquitectónica: 0 imports Qt en `servicios/` y `database/` | ✅ PASS | grep `PySide6` en ambos paquetes → 0 matches únicamente de código (coincidencias: docstrings/`sys` de PyInstaller) |

**Gate 5.2: PASS (4/4).** Cajas de tasks.md NO editadas (el archive las registra).

---

## Spec Compliance Matrix (19/19 escenarios, 11 requisitos)

Leyenda: **AUTO** = verificado-automated (test de suite o probe hermético ejecutado en esta fase); **MANU** = pending-manual (checklist 5.1); refs a líneas de HEAD d095a3a.

### hub-dashboard

| Req | Escenario | Veredicto | Evidencia |
|---|---|---|---|
| R1 Servicio métricas | Ciclo válido | ✅ AUTO | `tests/test_dashboard.py > test_ciclo_valido_devuelve_seis_claves_con_valores_correctos` — 6 claves exactas, valores 2/1/1/2/4, `ciclo_anio=2030` |
| R1 | Scoping por ciclo | ✅ AUTO | `test_scoping_excluye_asistencias_de_otro_ciclo` — ciclo A 2/4 ignora 5 de ciclo B; ciclo B 5/5. JOIN D1 (`dashboard.py:23-35`) |
| R1 | Ciclo inexistente | ✅ AUTO | `test_ciclo_inexistente...` (9999) + `test_ciclo_none...` (None): ceros + año actual (`dashboard.py:15` fallback) |
| R1 | Falla de BD | ✅ AUTO | `test_falla_de_base_de_datos_devuelve_resultado_error` — patch `servicios.dashboard.conexion` side_effect → `Resultado.error` sin propagar (`dashboard.py:46-47`) |
| R2 Tests dashboard | Suite headless | ✅ AUTO | descubierta de esta fase: 9 tests OK exit 0, incluye 6 de `test_dashboard`; hermética (BD dev intacta post-run) |
| R3 Panel HUB | Render con datos reales | ✅ AUTO | probe D7b–D7h: banner año del ciclo, KPIs exactos (2/1/1/2/3), tabla cursos 1 fila; carga única en `showEvent` (`hub.py:140-142`) — reconfirmación visual pertenece a 5.1 ítem 2 |
| R3 | Accesos rápidos | ✅ AUTO | probe D5c/D5d: `navegar_a_cursos/alumnos` → stack 1/2 + sidebar sincronizado (`hub.py:71-81`, `admin.py:694-695`) — visual en 5.1 ítem 3 |
| R3 | Error del servicio | ✅ AUTO | probe HD8a–HD8d: `obtener_metricas_hub` forzada `ok=False` → `label_error` visible no modal, tarjetas en "—", tabla 0 filas, sin crash (`hub.py:49-52,164-169,198-200`) |
| R3 tabla cursos via listar_cursos | (implícito en escenario render) | ✅ AUTO | probe D7h + `hub.py:177-196` |

### sidebar-navigation

| Req | Escenario | Veredicto | Evidencia |
|---|---|---|---|
| R4 Estructura | Sidebar visible | ✅ AUTO | probe B1–B5: sidebar 220px, branding "Asistencia Escolar", 4 entradas exactas, página 0 activa, único botón checked (`admin.py:601-705`) |
| R5 Estado activo | Cambio de página | ✅ AUTO | probe D5a (click en las 4 entradas → página + exclusividad) y D5b (sincronía inversa `currentChanged→setChecked`, `admin.py:692-693`) |
| R6 Footer/logout | Footer con usuario | ✅ AUTO | probe D3a (`usuario=None` → "Sesion local") y SN-V6c (usuario real → nombre+rol footer, `admin.py:707-713`; login pasa `usuario` en `login.py:326`) |
| R6 | Logout | ✅ AUTO | probe D4a–d: `_cerrar_sesion` crea VentanaLogin visible, admin cerrado, app viva; sin `app.quit` (`admin.py:715-720`) |
| R6 | Ciclo completo de sesión | ✅ AUTO | probe SN-V6a–d: `_intentar_login` (autenticar patcheado a éxito) → nuevo VentanaAdmin visible con footer del usuario, login cerrado (`login.py:302-334`) |

### admin-panel (delta ADDED)

| Req | Escenario | Veredicto | Evidencia |
|---|---|---|---|
| R7 Stack sin tabs | Stack sin tabs | ✅ AUTO | probe A1 (namespace de `interfaz.admin` sin `QTabWidget`), B1/B2 (stack QStackedWidget = exactamente 4 páginas en orden Hub/Cursos/Alumnos/Asistencia); grep estático 0 matches |
| R8 Paneles intactos | Wiring existente | ✅ AUTO | probe AP8a (identidad `on_cambio≈recargar_cursos`), AP8b/c end-to-end: alta de curso dispara recarga del combo de alumnos ("B" agregada → combo 2 cursos) sin refactor interno (numstat obs-85: variables confinadas a imports/init/tabs) |
| R9 Barra título | Controles de ventana | ⚠ MANU | **Checklist 5.1 ítem 9** (arrastre, doble-click, min/max/close requieren mouse real). Estático preservado: bloque barra título (`admin.py:722-828`) sin diff vs pre-PR4 (obs-85), TOOLTIP alternado en `_alternar_maximizar` (`admin.py:796-802`), cierre→app.quit solo en `_cerrar_aplicacion` (`admin.py:804-808`) |
| R10 Resolución ciclo | Falla de ciclo | ✅ AUTO | probe AP10a–c: servicio de ciclo forzado a error → `ciclo_id=None`, ventana construida con 4 páginas, sin crash (`admin.py:591-598`); QMessageBox mockeado en probe — el diálogo visual recae en runtime real (ítem implícito de 5.1) |
| R11 Preview asistencia | Consulta con datos | ✅ AUTO | probe AP11a–c: showEvent carga combo (placeholder+2 alumnos), consulta de Ana → 2 filas con fecha/materia/estado/observaciones (`asistencia_preview.py:40-42,144-190`; servicio `asistencia.py:94-111`) |
| R11 | Estado vacío | ✅ AUTO | probe AP11d: alumno sin registros en rango → 0 filas + mensaje visible, sin crash (`asistencia_preview.py:173-179`) |

**Resumen de cobertura**: 18/19 verified-automated · 1/19 pending-manual · 0 missing · 0 deviating.

### Pendiente-manual (checklist 5.1 del usuario)

El propósito de 5.1 es la validación **visual/UX** del humano; el probe headless NO lo sustituye (el diseño lo prescribe "sin tests Qt, manual con python main.py"). Los 12 ítems de 5.1 siguen abiertos para el usuario; en términos de escenarios spec, el único que permanece **exclusivamente** en evidencia manual es:

- **5.1 ítem 9 — barra de título**: arrastre (sin maximizar), doble-click maximizar/restaurar, min/max/close (AP-R9).
Recomendación: ejecutar los 12 ítems igualmente para sign-off visual; la caja 5.1 se registra en archive solo con atención del usuario.

---

## Correctness (evidencia estática post-merge)

| Req | Estado | Nota |
|---|---|---|
| HD-R1 servicio | ✅ Implemented | `dashboard.py` Qt-free, Resultado, 6 claves, JOIN por materia |
| HD-R2 tests | ✅ Implemented | unittest stdlib, hermético (tempfile + patch DB_PATH) |
| HD-R3 panel | ✅ Implemented | banner/KPIs/accesos/tabla/error inline |
| SN-R4/R5/R6 | ✅ Implemented | sidebar+QButtonGroup exclusivo, footer con identidad real |
| AP-R7/R8/R9/R10/R11 | ✅ Implemented | stack 4 páginas, paneles intactos, título conservado, ciclo lenient, preview read-only |

---

## Coherence (design D1–D8)

| Decisión | ¿Seguida? | Evidencia |
|---|---|---|
| D1 JOIN asistencia→materia→curso | ✅ Sí | `dashboard.py:23-26,31-35` (vía materia, NO vía alumno); test de scoping + borde semanal lo discriminan |
| D2 SQLite temporal + patch DB_PATH | ✅ Sí | `test_dashboard.py:22-33` exactamente el patrón D2; suite reproduce, 0 toques a BD dev |
| D3 usuario opcional (None=standalone) | ✅ Sí | `admin.py:569` firma `dict | None=None`; `login.py:326` pasa `resultado.datos`; probe D3a/SN-V6c; autenticar ya entrega datos sin password |
| D4 logout: sin app.quit | ✅ Sí | `admin.py:715-720`: import local antícírculo, ref fuerte `self.ventana_login`, mostrar→close; probe D4d (`not app.closingDown()`); `app.quit` permanece SOLO en `_cerrar_aplicacion` (barra) y login |
| D5 wiring bidireccional | ✅ Sí | `admin.py:692-693` `idClicked⇄currentChanged`; grupo exclusivo; probe D5 en ambas direcciones |
| D6 estilos.py compartido | ✅ Sí | `estilos.py` verbatim (AST-igual, obs-81); admin/hub/preview consumen solo de estilos; sin circulares |
| D7 carga en showEvent, error inline | ✅ Sí | `hub.py:140-142`; probe D7a prueba explícitamente "constructor NO carga → showEvent sí carga"; HD8 error inline no modal |
| D8 preview read-only | ✅ Sí | cero operaciones de escritura en `asistencia_preview.py`; try/except visible; guard fechas desde>hasta; badge "Vista preliminar"; probe AP11 |

**D1/D3/D4/D5/D7 re-verificados en estado post-merge** (el spot-check requerido): conformes.

---

## TDD Compliance (Strict TDD Module)

| Check | Resultado | Detalles |
|---|---|---|
| TDD Evidence reportado | ✅ | Tabla en obs-78 (fases 1–4); RED slice-1 corroborado por obs-79 (aritmética del seed: conteo global habría dado hoy=7≠2, semana=9≠4) |
| All tasks have tests gdzie aplica | ✅ | Toda la lógica testeable (servicio dashboard) tiene 6 tests; GUI sin capa de tests Qt por diseño (capabilities integration=false; checklist 5.1) |
| RED confirmed | ✅ (⚠ archiving) | RED verificado por revisión de slice (obs-79) pero no re-ejecutable: el pre-image del dashboard.py era untracked. Registro de proceso, no bloqueante |
| GREEN confirmed | ✅ | 6/6 tests de dashboard pasan en esta fase |
| Triangulacion adequate | ✅ | 6 casos con varianza de valores (2/1/1/2/4 vs 5/5 vs 0s vs error); borde hoy−7/hoy−8 explícito |
| Safety Net para archivos modificados | ✅ | Suite 9/9 en estado verde antes de cada slice (obs-78/79/81/82/85) |
| Assertion Quality | ✅ | Sin tautologías, sin ghost loops, sin mock-heavy; 1 redundancia carry-over (ver sugerencias) |

**TDD Compliance**: 6/6 checks passed.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---|---|---|
| Unit | 9 (6 nuevos + 3 preexistentes) | 2 (`tests/test_dashboard.py`, `tests/test_usuario.py`) | unittest stdlib |
| Integration | manual (5.1) + probe ad-hoc reproducible (Temp/opencode/probe_final_verify.py) | — | python main.py / offscreen |
| E2E | 0 (fuera de alcance por design.md) | — | — |

---

## Deferred / Out-of-scope audit

| Ítem deferido (proposal) | ¿Ausente? | Evidencia |
|---|---|---|
| Conteo de "turnos disponibles" | ✅ Ausente | Sin construct de turnos en `hub.py`/`dashboard.py` (la columna "Turno" de la tabla es el display preexistente de `listar_cursos`, no un contador) |
| Animaciones/transiciones | ✅ Ausente | grep `Animation|Animat` en `interfaz/` → 0; cambio de página instantáneo (probe D5a) |
| Refactor de PanelCursos/PanelAlumnos | ✅ Ausente | Internos intactos (obs-85 numstat confined; probe AP8 funciona end-to-end) |
| `generate_files.py` | ✅ Intocable | Untracked, sin modificar; decisión sigue pendiente |

**Nada colado (smuggled) desde el scope deferido.**

---

## Findings

**CRITICAL**: Ninguno.

**WARNING**:
1. **(proceso, no código) Checklist 5.1 sigue pendiente de ejecución humana.** El veredicto de este reporte es de conformidad técnica; el sign-off visual (12 ítems listados en tasks.md:44) pertenece al usuario por diseño. NO marcar 5.1 en archive sin ejecutarlo.
2. **(carry-over obs-85, histórico) Drift de etiquetas de commit en PR4**: `ca46ff8` ("logout al login") contiene solo el 1-liner de login.py mientras la implementación de `_cerrar_sesion` aterrizó en `d5858ac`; caja 4.2 invertida antes de su commit aislado; `d13e54b` tipado `style:` con contenido conductual (`fix/feat`). Todo el contenido está presente y merged — no viola spec ni design. Disposición recomendada: **won't-fix** (registrar para bisect/revert futuros).

**SUGGESTION** (nuevas, de este barrido):
1. `interfaz/hub.py:177-178` + `servicios/curso.py:63-69`: en la ruta de ciclo fallado (`ciclo_id=None`), `listar_cursos(None)` lista cursos de **todos** los ciclos (sin WHERE). No crashea (probe AP10) y el caso es lenient por diseño, pero el hub mostraría resumen trans-ciclo. Disposición: **backlog**.
2. Considerar, si la suite algún día adopta capa Qt-headless, los checks del probe (HD8/D5/D4/AP10) como unittests permanentes. Disposición: **backlog** (no bloqueante).

---

## Open Suggestions Ledger (carry-over obs-79/81/82/85)

| # | Origen | Ítem | Estado | Disposición recomendada |
|---|---|---|---|---|
| 1 | obs-85 #4 | `asistencia_preview.py:170` — tooltip `setToolTip(str(e))` expone excepción cruda (detalle dev) | **ABIERTO** (prometido cerrar en archive; copy amigable ya aterrizó en d13e54b) | **fix-at-archive**: micro-fix de 1 línea (guardar genérico o silenciar tooltip) en la primera ventana de apply; alternativa aceptada: backlog |
| 2 | obs-79 #1 | `tests/test_dashboard.py:203` — `assertNotEqual(..., 5)` redundante tras `assertEqual(..., 4)` de L201 | ABIERTO (harmless) | **backlog**: eliminar en el próximo toque de la suite |
| 3 | obs-79 #3 | `tests/test_dashboard.py:28,35` — `with sqlite3.connect(...)` no cierra la conexión explícita; liberación por GC de refcount en Windows (OSError tragado en cleanup) | ABIERTO (harmless: residuo posible en %TEMP%) | **backlog**: cerrar conn con `close()` explícito en próximo toque |
| 4 | obs-85 #1 / WARNING 2 | Drift de commits (ver WARNING 2 arriba) | ABIERTO (histórico) | **won't-fix**: registrar; no reescribir historia merged |
| 5 | obs-79 #2 | RED de slice 1 no archivado en git (pre-image untracked) | ABIERTO (proceso) | **won't-fix** para este cambio; regla para futuros slices con servicio untracked |
| 6 | obs-81 #2/#3, obs-85 #2/#3 | Drift de forecast de líneas; tipo `style:` vs `fix:`; grilla KPI fila inferior 2+3 asimétrica | ABIERTO (cosmético) | **won't-fix**: compromisos visuales/proceso aceptados explícitamente en review de slice |

**Resolvedos durante las fases (cierre verificado aquí)**:
- obs-81 W1 (4 constantes sin usar en admin) → **resuelto**: todas consumidas en el QSS del sidebar (`admin.py:605-640`).
- obs-82 #1 (import sin uso `COLOR_TEXTO_TENUE` en hub) → **resuelto**: ya no importado (`hub.py:18-25`).
- obs-82 #2 (f-string sin placeholders en hub) → **resuelto**: string plano en `hub.py:50`.
- obs-82 #4/#6 (combo stale + API privada) → **resuelto**: `recargar_alumnos()` público + `showEvent` (`asistencia_preview.py:40-42,116`); probe AP11a carga en show antes de render.
- obs-82 #5 → parcialmente resuelto (copy amigable `asistencia_preview.py:166-169`); el remanente es el ledger #1.

---

## Veredicto

**PASS WITH WARNINGS** — Los 19 escenarios de las 3 specs están cubiertos: 18 con evidencia runtime automatizada (6 tests de suite + 44/44 checks del probe hermético re-ejecutado contra `main` d095a3a) y 1 pendiente del checklist visual humano (barra de título, 5.1 ítem 9) con respaldo estático de código intacto. Gate 5.2 PASS (4/4). Deferidas genuinamente ausentes. Diseño D1–D8 fiel. Sin hallazgos CRITICAL; 2 WARNING no bloqueantes para archive (uno es proceso 5.1 humano, otro histórico de commits); 6 ítems de ledger con disposición asignada.

**Condiciones pre-archive recomendadas**:
1. Usuario ejecuta checklist 5.1 (`python main.py`) y confirma 12/12 — habilita cierre de 5.1 (el archive lo registra).
2. (Opcional, 1 línea) fix-at-archive del tooltip crudo en `asistencia_preview.py:170`.
3. `sdd-archive` puede proceder tras (1); cajas 5.1/5.2 se marcan en archive, no antes.
