# Design: HUB Dashboard + Sidebar Navigation

Fuentes: proposal + delta specs. Reglas: `servicios/`+`database/` sin Qt; ops devuelven `Resultado`; PanelCursos/PanelAlumnos intactos.

## Technical Approach

QTabWidget (admin.py L660-681) → sidebar 220px + `QStackedWidget` de 4 páginas; barra de título intacta. `PanelHub` (nuevo `interfaz/hub.py`) consume `obtener_metricas_hub` con asistencias acotadas al ciclo. Logout = show/close de login.py invertido. Tests RED-first sobre SQLite temporal.

## Architecture Decisions

### D1: Scoping por ciclo — JOIN asistencia→materia→curso

**Elección**: JOIN vía `materia` (`curso_id` inmutable). **Rechazada**: vía `alumno` — `cambiar_curso_alumno` lo muta y migraría asistencias históricas a otro ciclo. Sin FK directa asistencia→curso (schema.sql). Firma/`Resultado` sin cambios; `ciclo_id=None` → ceros + año actual (lenient según spec).

```sql
SELECT COUNT(*) AS t FROM asistencia a
JOIN materia m ON m.id = a.materia_id
JOIN curso cu  ON cu.id = m.curso_id
WHERE cu.ciclo_id = ? AND a.fecha = ?   -- semana: a.fecha >= ?
```

### D2: Tests — SQLite temporal + patch de `DB_PATH`

| Opción | Tradeoff | Decisión |
|---|---|---|
| Sembrar BD real + cleanup | corrupción ante crash; no hermético | ✗ |
| Cursores fake (mock puro) | no prueba el SQL real (núcleo) | ✗ |
| BD temporal (`schema.sql`) + `mock.patch("database.conexion.DB_PATH")` | SQL real, semillas controladas, cero riesgo a BD real | ✓ |

`conexion()` lee `DB_PATH` por llamada → el patch funciona (stdlib). Sembrar ciclos A/B con asistencias `fecha=hoy`: código actual (global) → RED; con JOIN → GREEN. Falla de BD: patch de `servicios.dashboard.conexion` con `side_effect=Exception`. Aditivo: `database_strategy` de config.yaml rige la suite existente.

### D3: Identidad — parámetro opcional de constructor

`VentanaAdmin(usuario: dict | None = None)`; login.py L326 pasa `resultado.datos` (sin password). `None` → footer "Sesión local"; `python -m interfaz.admin` sigue funcionando. **Rechazado**: singleton/contexto — sin infraestructura, un consumidor.

### D4: Logout — cadena de referencias fuertes, nunca `app.quit()`

```python
def _cerrar_sesion(self):
    from interfaz.login import VentanaLogin  # import local: evita ciclo admin↔login
    self.ventana_login = VentanaLogin()
    self.ventana_login.mostrar()
    self.close()      # NUNCA _cerrar_aplicacion(): app.quit() mata el loop (obs-69)
```

PySide6 borra widgets sin padre si el wrapper muere; la cadena main.py→login₀→admin→login₁ los mantiene vivos. **Tradeoff aceptado**: un eslabón por logout (acotado). **Rechazado**: `WA_DeleteOnClose` (altera el cerrar de la barra).

### D5: Navegación — QStackedWidget + QButtonGroup exclusivo

Cuerpo: QHBoxLayout [sidebar QFrame 220px, stack: 0 Hub, 1 Cursos, 2 Alumnos, 3 Asistencia]. Sidebar: branding textual (sin logo en `assets/`), 4 botones checkable (id=índice), footer usuario + "Cerrar sesión". Inicial: índice 0.

```python
grupo_nav.idClicked.connect(stack.setCurrentIndex)
stack.currentChanged.connect(lambda i: grupo_nav.button(i).setChecked(True))
```

Grupo exclusivo + QSS `:checked` = único estado activo; señales de PanelHub → `setCurrentIndex` → sidebar sincroniza solo. Se preservan `on_cambio=panel_alumnos.recargar_cursos`, ciclo resuelto antes de armar páginas (L652-658) y handlers de la barra.

### D6: Estilos compartidos — nuevo `interfaz/estilos.py`

Mover paleta `COLOR_*` y helpers `_tarjeta`/`_etiqueta`/`_estilo_*` verbatim a `interfaz/estilos.py`; admin.py re-importa → paneles byte-idénticos. **Racional**: 3 consumidores (admin, hub, asistencia_preview). **Rechazado**: hub importa de admin (circular); copy-paste. Glassmorphism = `COLOR_TARJETA` existente (rgba blanco 4%, borde, radius 16).

### D7: PanelHub — carga en `showEvent`, error inline

Banner con `ciclo_anio`; grilla KPI (`QGridLayout`, tarjetas `_tarjeta()`): activos, baja, cursos, hoy, semana (SHOULD, dato ya existe); "+ Agregar Alumno"/"+ Crear Curso" emiten `navegar_a_alumnos`/`navegar_a_cursos`; tabla vía `listar_cursos(ciclo_id)`. Cargar en `showEvent`: refresca al volver a Inicio sin doble lectura. `ok=False` → QLabel inline con `mensaje` (no modal, no se apila sobre el diálogo crítico), sin crash.

### D8: PanelAsistencia — read-only preliminar

Combo alumno vía `listar_alumnos(solo_activos=True)` (data=numero); `QDateEdit` desde/hasta (default hoy−30/hoy); "Consultar" → `listar_asistencias_de_alumno` → tabla Fecha/Materia/Estado/Observaciones (claves exactas de sus dicts). Devuelve `list` crudo (no `Resultado`) y puede lanzar → try/except con mensaje visible. Sin selección/registros → estado vacío. Badge "Vista preliminar". **Diferido**: registrar asistencia, porcentajes, lista_diaria, filtros materia/curso.

## Data Flow

    VentanaLogin ─autenticar()→ VentanaAdmin(usuario) ─→ ciclo_id (obtener_o_crear)
    Sidebar(QButtonGroup) ⇄ QStackedWidget ⇄ paneles → servicios.* → SQLite → Resultado → UI

## File Changes

| File | Action | Description |
|---|---|---|
| `tests/test_dashboard.py` | Create | 6 escenarios, BD temporal, RED-first |
| `servicios/dashboard.py` | Modify | Scoping por ciclo (D1) |
| `interfaz/estilos.py` | Create | Paleta/helpers compartidos (D6) |
| `interfaz/hub.py` | Create | `PanelHub` (D7) |
| `interfaz/asistencia_preview.py` | Create | `PanelAsistencia` (D8) |
| `interfaz/admin.py` | Modify | Sidebar+stack, `usuario`, `_cerrar_sesion`, estilos (D3-D6) |
| `interfaz/login.py` | Modify | L326: `VentanaAdmin(usuario=usuario)` |

## Interfaces / Contracts

```python
obtener_metricas_hub(ciclo_id: int | None) -> Resultado  # firma/claves sin cambios
VentanaAdmin(usuario: dict | None = None)
PanelHub(ciclo_id)        # signals: navegar_a_alumnos, navegar_a_cursos
PanelAsistencia(ciclo_id)
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit (auto) | Scoping por ciclo; borde semanal (hoy−7 entra, hoy−8 no); ciclo inexistente/`None`; falla BD → `Resultado.error` | `test_dashboard.py`: SQLite temporal + patch `DB_PATH`; strict TDD |
| Integration (manual) | Nav/estado activo, accesos rápidos, barra de título, logout→re-login, `on_cambio` | `python main.py` (sin tests Qt) |
| E2E | Fuera de alcance | — |

Suite: `python -m unittest discover -s tests` exit 0 (headless).

## Migration / Rollout

Sin migración. Orden de apply: test RED → fix dashboard (GREEN) → estilos.py → hub → asistencia_preview → integración admin/login. Rollback: git revert según proposal.

## Open Questions

Ninguna bloqueante. `generate_files.py` fuera de alcance (decisión diferida a apply).
