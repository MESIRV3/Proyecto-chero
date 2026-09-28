# Tasks: HUB Dashboard + Sidebar Navigation

## Review Workload Forecast

Estimated changed lines: ~760 total (1.1≈150, 1.2≈15, 2.1≈188* (*~95 son move literal), 3.1≈150, 3.2≈120, 4.1≈115, 4.2≈15, 4.3≈4, 5.x≈0).

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High
800-line budget risk: Medium (~40 de margen; split recomendado igual)

| Unit | Goal | Likely PR | ~Líneas |
|------|------|-----------|---------|
| 1 | Servicio dashboard TDD (1.1→1.2, suite verde autónoma) | PR 1 | 165 |
| 2 | Extracción estilos D6 (2.1, move mecánico) | PR 2 | 188 |
| 3 | Paneles nuevos hub/preview (3.1–3.2 sin wire) | PR 3 | 270 |
| 4 | Integración admin/login + verificación (4.x–5.x) | PR 4 | 135 |

Delivery strategy: ask-always (el orquestador pregunta antes de apply).

## Fase 1: Servicios — STRICT TDD (RED → GREEN)

- [x] 1.1 (RED) `tests/test_dashboard.py` NEW (~150 l.): SQLite temporal con `executescript(schema.sql)` + `mock.patch("database.conexion.DB_PATH")` (D2); 2 ciclos sembrados (curso→materia→asistencia; hoy−7 dentro, hoy−8 fuera). Casos: 6 claves ≥0; scoping excluye otro ciclo; ciclo inexistente/`None` → ceros + año actual; `conexion` con `side_effect` → `Resultado.error`. **Verifica**: `python -m unittest tests.test_dashboard` falla contra código actual. Cubre HD-R1+R2. Dep: —.
- [x] 1.2 (GREEN) `servicios/dashboard.py` MODIFY (~15 l.): JOIN `asistencia→materia→curso WHERE cu.ciclo_id=?` en asistencias (D1); firma/claves intactas. `git add servicios/dashboard.py` (incorporación deliberada; `generate_files.py` intocable). **Verifica**: `python -m unittest discover -s tests` exit 0. Cubre HD-R1+R2. Dep: 1.1.

## Fase 2: Estilos compartidos (D6)

- [ ] 2.1 `interfaz/estilos.py` NEW (~95 l.): mover verbatim `FUENTE_MONO`, `COLOR_*`, `_estilo_*`/`_tarjeta`/`_etiqueta` de admin.py L51–178; admin re-importa (+3/−90) → paneles byte-idénticos, sin circulares. **Verifica**: suite exit 0 + `python main.py` igual que antes. Habilita HD-R3, AP-R8/R9. Dep: —.

## Fase 3: Paneles nuevos (GUI — verificación manual)

- [ ] 3.1 `interfaz/hub.py` NEW `PanelHub(ciclo_id)` (~150 l., D7): banner `ciclo_anio`; KPIs con `_tarjeta()` (activos, baja, cursos, hoy, semana); señales `navegar_a_alumnos`/`navegar_a_cursos`; tabla `listar_cursos(ciclo_id)`; carga en `showEvent`; `ok=False` → QLabel inline sin modal/crash. **Verifica**: items 2–4 de 5.1. Cubre HD-R3. Dep: 1.2, 2.1.
- [ ] 3.2 `interfaz/asistencia_preview.py` NEW `PanelAsistencia(ciclo_id)` (~120 l., D8): combo `listar_alumnos(solo_activos=True)`; `QDateEdit` hoy−30/hoy; `listar_asistencias_de_alumno` (lista cruda → try/except visible) en tabla Fecha/Materia/Estado/Observaciones; estado vacío; badge "Vista preliminar". **Verifica**: items 5–6 de 5.1. Cubre AP-R11. Dep: 2.1.

## Fase 4: Integración admin + login

- [ ] 4.1 `interfaz/admin.py` MODIFY (~115 l., D3+D5): `VentanaAdmin(usuario=None)`; QTabWidget L660–681 → QHBoxLayout [sidebar 220px: branding, 4 botones checkable, footer usuario (`None`→"Sesión local") + "Cerrar sesión" | `QStackedWidget` 0 Hub/1 Cursos/2 Alumnos/3 Asistencia]; cable `idClicked`⇄`currentChanged` (grupo exclusivo); preservar ciclo L652–658 y `on_cambio`. **Verifica**: items 1, 7–10 de 5.1. Cubre SN-R4/R5/R6, AP-R7/R8/R10. Dep: 2.1, 3.1, 3.2.
- [ ] 4.2 `interfaz/admin.py` MODIFY (~15 l., D4): `_cerrar_sesion()` — import local `VentanaLogin`, ref en `self.ventana_login`, `mostrar()`, `self.close()`; NUNCA `app.quit()`. **Verifica**: items 11–12 de 5.1. Cubre SN-R6. Dep: 4.1.
- [ ] 4.3 `interfaz/login.py` MODIFY (L326, ~4 l.): `VentanaAdmin(usuario=usuario)` con `resultado.datos`. **Verifica**: item 1 de 5.1. Cubre SN-R6. Dep: 4.1.

## Fase 5: Verificación (19/19 escenarios)

- [ ] 5.1 Checklist manual `python main.py`: (1) sidebar+4 entradas, Inicio activo, footer con usuario; (2) KPIs reales; (3) accesos rápidos navegan/sincronizan; (4) error métricas inline; (5) consulta asistencia con datos; (6) estado vacío sin crash; (7) un solo botón activo; (8) cero QTabWidget; (9) barra de título intacta (arrastre/doble-clic/min/max/cerrar); (10) on_cambio recarga combo alumnos; (11) logout abre login, app viva; (12) re-login abre nuevo admin. Dep: 4.x.
- [ ] 5.2 Gate final: suite exit 0; grep `QTabWidget` limpio en `interfaz/`; `git status`: dashboard.py trackeado, generate_files.py sigue untracked. Dep: todo.

## Mapeo requisito → tarea

| Req | Tareas | Esc. |
|-----|--------|------|
| HD-R1 Servicio métricas | 1.1, 1.2 | 4 |
| HD-R2 Tests dashboard | 1.1, 1.2, 5.2 | 1 |
| HD-R3 Panel HUB | 3.1, 4.1, 5.1 | 3 |
| SN-R4 Estructura sidebar | 4.1, 5.1 | 1 |
| SN-R5 Estado activo | 4.1, 5.1 | 1 |
| SN-R6 Footer+logout | 4.1–4.3, 5.1 | 3 |
| AP-R7 Stack sin tabs | 4.1, 5.1, 5.2 | 1 |
| AP-R8 Paneles intactos | 2.1, 4.1, 5.1 | 1 |
| AP-R9 Barra de título | 4.1, 5.1 | 1 |
| AP-R10 Resolución ciclo | 4.1, 5.1 | 1 |
| AP-R11 Asistencia preview | 3.2, 5.1 | 2 |
