# Delta for admin-panel

> Capability *Modified* sin spec principal previo: requisitos ADDED (archive creará `openspec/specs/admin-panel/spec.md`). Cambio de código: QTabWidget → sidebar + QStackedWidget.

## ADDED Requirements

### Requirement: Navegación por stack

VentanaAdmin MUST reemplazar el QTabWidget por un QStackedWidget con exactamente 4 páginas: PanelHub (Inicio), PanelCursos, PanelAlumnos, PanelAsistencia. MUST NOT quedar barra de pestañas.

#### Scenario: Stack sin tabs

- GIVEN admin abierto
- WHEN se inspecciona la navegación
- THEN stack de 4 páginas y ningún QTabWidget

### Requirement: Paneles existentes intactos

PanelCursos y PanelAlumnos MUST integrarse sin refactor interno, preservando `ciclo_id` y el wiring `on_cambio` (cambio de cursos → `PanelAlumnos.recargar_cursos`).

#### Scenario: Wiring existente

- GIVEN admin abierto
- WHEN se crea o modifica un curso en PanelCursos
- THEN el combo de cursos de PanelAlumnos se recarga

### Requirement: Barra de título personalizada

La barra frameless MUST conservar: arrastre (sin maximizar), doble-click maximizar/restaurar, minimizar, maximizar/restaurar con tooltip alternado, y cerrar que finaliza la app.

#### Scenario: Controles de ventana

- GIVEN admin abierto
- WHEN se usan arrastre, minimizar, maximizar y cerrar
- THEN se comportan igual que en la implementación actual

### Requirement: Resolución del ciclo lectivo

VentanaAdmin MUST resolver el ciclo con `obtener_o_crear_ciclo_actual()` antes de construir las páginas. Ante falla MUST mostrar diálogo crítico y abrir con `ciclo_id=None` sin crashear.

#### Scenario: Falla de ciclo

- GIVEN servicio de ciclo fallando
- WHEN se abre el admin
- THEN diálogo crítico y ventana abierta con `ciclo_id=None`

### Requirement: Página preliminar de Asistencia

`interfaz/asistencia_preview.py::PanelAsistencia` MUST ofrecer selector de alumno, rango de fechas y listado (fecha, materia, estado, observaciones) vía `listar_asistencias_de_alumno`; sin registros, estado vacío sin crashear. SHOULD identificarse como preliminar.

#### Scenario: Consulta con datos

- GIVEN alumno con asistencias en el rango
- WHEN se consulta
- THEN registros con fecha, materia, estado y observaciones

#### Scenario: Estado vacío

- GIVEN alumno sin registros en el rango
- WHEN se consulta
- THEN mensaje de estado vacío sin crashear
