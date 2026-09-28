# sidebar-navigation Specification

## Purpose

Sidebar izquierdo: branding, navegación con estado activo, footer de usuario con logout.

## Requirements

### Requirement: Estructura del sidebar

La ventana de administración MUST mostrar un sidebar izquierdo con branding y 4 entradas: Inicio, Cursos, Alumnos, Asistencia. Al abrir la ventana, Inicio MUST ser la página activa.

#### Scenario: Sidebar visible

- GIVEN VentanaAdmin visible
- WHEN se inspecciona la UI
- THEN sidebar con branding, 4 entradas y página Inicio activa

### Requirement: Navegación con estado activo

Clickear una entrada MUST mostrar al instante la página correspondiente (sin animaciones) y marcarla como único estado activo visual.

#### Scenario: Cambio de página

- GIVEN admin abierto
- WHEN se clickea "Cursos"
- THEN página Cursos visible, su entrada activa y las demás inactivas

### Requirement: Footer de usuario y logout

El sidebar MUST incluir footer con la identidad del usuario autenticado y botón "Cerrar sesión". El logout MUST cerrar VentanaAdmin y abrir una VentanaLogin nueva visible con la app viva (inverso del login); MUST NOT terminar el event loop.

#### Scenario: Footer con usuario

- GIVEN sesión iniciada desde login
- WHEN se muestra el sidebar
- THEN footer con usuario y "Cerrar sesión"

#### Scenario: Logout

- GIVEN sesión admin activa
- WHEN se clickea "Cerrar sesión"
- THEN admin se cierra, login se abre, la app sigue viva

#### Scenario: Ciclo completo de sesión

- GIVEN logout recién ejecutado
- WHEN se inicia sesión otra vez con credenciales válidas
- THEN un nuevo VentanaAdmin se abre con normalidad
