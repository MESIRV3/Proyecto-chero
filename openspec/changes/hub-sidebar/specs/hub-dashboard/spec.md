# hub-dashboard Specification

## Purpose

Panel HUB (Inicio): métricas del ciclo, accesos rápidos, resumen de cursos. Fuente: `servicios/dashboard.py` (Qt-free, Resultado).

## Requirements

### Requirement: Servicio de métricas hub

`obtener_metricas_hub(ciclo_id)` MUST devolver `Resultado.exito` con `datos` de 6 claves: `alumnos_activos`, `alumnos_baja`, `total_cursos`, `asistencias_hoy`, `asistencias_semana`, `ciclo_anio`. Conteos MUST acotarse al ciclo (`asistencias_hoy`: fecha = hoy; `asistencias_semana`: fecha ≥ hoy−7). Ciclo inexistente/vacío: `exito` con conteos 0 y `ciclo_anio` = año actual. Falla de BD: `Resultado.error` sin propagar excepciones. MUST NOT importar Qt.

#### Scenario: Ciclo válido

- GIVEN BD seed con ciclo actual
- WHEN se llama con ese `ciclo_id`
- THEN `ok=True` y 6 claves con enteros ≥ 0

#### Scenario: Scoping por ciclo

- GIVEN asistencias de hoy de otro ciclo
- WHEN se piden métricas del ciclo actual
- THEN `asistencias_hoy` las excluye

#### Scenario: Ciclo inexistente

- GIVEN `ciclo_id` inexistente
- WHEN se llama al servicio
- THEN `ok=True`, conteos 0, `ciclo_anio` = año actual

#### Scenario: Falla de BD

- GIVEN conexión que lanza excepción
- WHEN se llama al servicio
- THEN devuelve `Resultado.error` sin propagarla

### Requirement: Tests unitarios de dashboard

`tests/test_dashboard.py` (unittest stdlib, headless) MUST cubrir los escenarios del servicio, escrito antes de completarlo (strict TDD: RED→GREEN).

#### Scenario: Suite headless

- GIVEN la suite
- WHEN se ejecuta `python -m unittest discover -s tests`
- THEN exit 0 incluyendo `test_dashboard`

### Requirement: Panel HUB

`interfaz/hub.py::PanelHub` MUST renderizar: banner con `ciclo_anio`; tarjetas KPI (estilo glassmorphism) de activos, baja, cursos y asistencias_hoy (SHOULD asistencias_semana); accesos rápidos "+ Agregar Alumno" y "+ Crear Curso"; tabla de cursos del ciclo (`listar_cursos`). Ante `Resultado.error` MUST mostrar mensaje visible sin crashear.

#### Scenario: Render con datos reales

- GIVEN ciclo con cursos y alumnos
- WHEN PanelHub se muestra
- THEN banner con año, tarjetas con valores reales y tabla de cursos

#### Scenario: Accesos rápidos

- GIVEN PanelHub en el stack
- WHEN se clickea "+ Agregar Alumno" (o "+ Crear Curso")
- THEN el stack muestra la página Alumnos (o Cursos)

#### Scenario: Error del servicio

- GIVEN métricas con `ok=False`
- WHEN PanelHub renderiza
- THEN muestra mensaje de error sin crashear
