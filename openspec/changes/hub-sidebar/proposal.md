# Proposal: HUB Dashboard + Sidebar Navigation

## Intent

Reemplazar la navegación por pestañas (`QTabWidget`) en `interfaz/admin.py` por un **sidebar lateral izquierdo** con un **HUB/Dashboard central** que muestre métricas del colegio y accesos rápidos. El cambio moderniza la UX, centraliza la información del ciclo lectivo, y agrega logout + vista preliminar de asistencia.

## Scope

### In Scope
- **Sidebar lateral** con navegación (Inicio, Cursos, Alumnos, Asistencia) y footer de usuario con logout
- **Panel HUB** (`interfaz/hub.py`) con banner de bienvenida, grid de KPIs, accesos rápidos, tabla resumen de cursos
- **Completar `servicios/dashboard.py`** (ya existe untracked) — validar que `obtener_metricas_hub` cubre todos los KPIs del HUB
- **Vista preliminar de Asistencia** consumiendo `servicios/asistencia.py`
- **Logout**: cerrar `VentanaAdmin` y reabrir `VentanaLogin`
- **Tests unitarios** (`tests/test_dashboard.py`) con strict TDD

### Out of Scope
- Conteo de "turnos disponibles" — `turno` es columna TEXT en `curso`, no entidad independiente. Descope confirmado por schema.
- `generate_files.py` (untracked en root) — decisión pendiente: mantener o eliminar en fase apply
- Refactor de `PanelCursos` / `PanelAlumnos` — se conservan intactos como páginas del stack
- Animaciones/transiciones entre páginas — implementación inicial instantánea

## Capabilities

### New Capabilities
- `hub-dashboard`: Panel central con métricas del ciclo lectivo (alumnos activos/baja, cursos, asistencias hoy/semana) y accesos rápidos
- `sidebar-navigation`: Barra lateral izquierda con navegación por páginas, branding, footer de usuario + logout

### Modified Capabilities
- `admin-panel`: Reemplazar `QTabWidget` por `QStackedWidget` + sidebar; mantener barra de título personalizada (arrastre, min/max/close)

## Approach

1. **Servicios**: `servicios/dashboard.py` ya existe (untracked) e implementa `obtener_metricas_hub(ciclo_id) -> Resultado` con alumnos_activos, alumnos_baja, total_cursos, asistencias_hoy, asistencias_semana, ciclo_anio. Completar/validar cobertura de KPIs.
2. **Presentación**: `interfaz/hub.py` (NEW) consume `dashboard.py` y renderiza KPIs + accesos rápidos. `interfaz/admin.py` (MODIFY) reemplaza `self.tabs = QTabWidget()` (L660-681) por sidebar + `QStackedWidget` con 4 páginas: Hub, Cursos, Alumnos, Asistencia.
3. **Logout**: Sidebar footer con botón "Cerrar sesión" → `self.close()` + `VentanaLogin().show()` (inverso del flujo actual en `login.py` L325-330).
4. **Tests**: `tests/test_dashboard.py` (NEW) con unittest stdlib. Strict TDD: test primero, luego completar `dashboard.py` si faltan casos.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `interfaz/admin.py` | Modified | Reemplazar QTabWidget (L660-681) por sidebar + QStackedWidget |
| `interfaz/hub.py` | New | PanelHub(QWidget) con KPIs, banner, accesos rápidos, tabla cursos |
| `servicios/dashboard.py` | Complete | Ya existe untracked; validar/completar cobertura de KPIs |
| `tests/test_dashboard.py` | New | Tests unitarios para `obtener_metricas_hub` (strict TDD) |
| `interfaz/asistencia_preview.py` | New | Vista preliminar consumiendo `servicios/asistencia.py` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tests tocan DB real sin fixtures | Med | Usar datos de seed existentes (admin/admin123); mantener DB hermética |
| Logout pierde estado de sesión | Bajo | VentanaLogin re-crea VentanaAdmin desde cero (flujo ya probado) |
| Sidebar rompe layout existente | Bajo | Mantener barra de título personalizada intacta; solo reemplazar QTabWidget |

## Rollback Plan

Git revert del commit de apply. `interfaz/admin.py` vuelve a QTabWidget original. Archivos nuevos (`hub.py`, `asistencia_preview.py`, `test_dashboard.py`) se eliminan. `servicios/dashboard.py` se des-tracks (vuelve a untracked).

## Dependencies

- `servicios/asistencia.py` ya existe y expone funciones de asistencia
- `database/resultado.py` — contrato Resultado.exito/error (ya respetado por dashboard.py)
- `interfaz/login.py` — VentanaLogin (ya existe, se reabre en logout)

## Success Criteria

- [ ] Sidebar visible con 4 entradas (Inicio, Cursos, Alumnos, Asistencia) + footer logout
- [ ] HUB muestra 4 KPIs reales desde `obtener_metricas_hub`
- [ ] Logout cierra admin y reabre login sin errores
- [ ] `python -m unittest discover -s tests` pasa exit 0 (incluye test_dashboard.py)
- [ ] PanelCursos y PanelAlumnos funcionan idénticos dentro del stack
