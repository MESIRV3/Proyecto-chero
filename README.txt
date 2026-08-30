--------------- 1. Carpetas ---------------
En la carpeta apuntes hay anotaciones de algunas funciones utilizadas en el código (Abrí los archivos con VScode)

En la carpeta Assets se van a alojar cualquier archivo estético que no contenga código como por ejemplo una imagen

En la capeta build esta estructurado todo el sistema para ejecutar como .exe el código (no toques nada)

En la carpeta database se guarda todo back-end de la app como bases de datos, operaciones, entre otros.

En la carpeta interfaz se almacenan los archivos de personalización de la app (El código que altera la parte estética)

En la carpeta servicios se almacenan todas las herramientas y servicios (dah) que proporciona la app; Como apenas se creo la interfaz de Inicio de sesión no están muy desarrollados.

En la carpeta Tests se almacenan todos los tests para asegurar el correcto funcionamiento de la app (como dije anteriormente, solo tenemos por ahora el inicio de sesión, entonces no se ha utilizado esta carpeta por ahora)

--------------- 2. FrameWorks y Librerías Utilizadas

Python (dah)

SQLite3 - Viene con Python

PySide6 - Interfaz Gráfica - pip install PySide6 (en el cmd pone esto para instalarlo)

Pillow - Manejo de imágenes - pip install Pillow

bcrypt - Hashear contraseñas - pip install bcrypt

PyInstaller - Generar .exe - pip install pyinstaller


--------------- 3. Cosas a tener en cuenta (database) ---------------

1. schema.sql es el plano
- Define las 10 tablas, columnas, tipos, restricciones
- Si lo modificás, tenés que borrar asistencia.db y volver a correr crear_bd.py
- asistencia.db no se toca a mano, solo se modifica a través de Python

2. conexion.py centraliza TODO
- Es el único archivo que abre la base
- Todos los servicios (alumno.py, asistencia.py, usuario.py) lo importan
- Si mañana cambias de SQLite a PostgreSQL, solo tocás este archivo

3. resultado.py es una clase de ayuda
- Devuelve Resultado.exito() o Resultado.error()
- Sirve para que las funciones no tiren excepciones todo el tiempo
- No tiene nada que ver con la base en sí

4. Los scripts de prueba
- cargar_datos_prueba.py se puede correr N veces
- Cada vez que corre, borra todo y vuelve a cargar
- Está para desarrollo, no para producción

5. asistencia.db es un archivo binario
- No lo abras con bloc de notas
- Para ver qué hay: consultar_datos.py o verificar_bd.py

6. El orden de ejecución inicial
crear_bd.py → crea las tablas (1 vez)
cargar_datos_prueba.py → carga datos ficticios (1 vez)
consultar_datos.py  → verifica qué hay (cuando quieras)

Cosas que NO están bien todavía
- Las contraseñas están en texto plano (hash_pendiente)
- No hay backup de la base
- No hay migraciones (si cambias el schema, borrás todo y rehacés)


--------------- 4. Cosas Clave para analizar .\interfaz\login.py 

Dependencias de Qt que usa:
- QMainWindow, QWidget → ventanas
- QVBoxLayout, QHBoxLayout, QGridLayout → distribución
- QLabel → textos e imágenes
- QLineEdit → campos de texto
- QPushButton → botones
- QFrame → la tarjeta (donde se apoya el menú de inicio de sesión)
- QGraphicsDropShadowEffect → sombra
- QMessageBox → carteles de error/éxito
- QIcon → iconos en inputs
- QFont → fuentes

Estructura visual:
- Fondo de imagen al 100% (responsivo con resizeEvent)
- Tarjeta centrada con glassmorphism (rgba(20, 20, 20, 0.65))
- Barra de título custom con Min/Max/Cerrar
- 2 inputs con iconos integrados (addAction)
- Botón píldora (iniciar sesión)

Eventos implementados:
- resizeEvent → ajusta fondo al tamaño de ventana
- mousePressEvent / mouseMoveEvent / mouseReleaseEvent → arrastrar ventana
- close() → cerrar
- showMinimized() → minimizar
- _alternar_maximizar() → alternar maximize/normal

Nota sobre la ruta de assets I --- M --- P --- O --- R --- T --- A --- N --- T --- E

En login.py las rutas son absolutas hacia MI carpeta. Si el proyecto esta en otra carpeta, hay que actualizarlas:
ASSETS_PATH = r"C:\Users\"TU USARIO"\Desktop (Es el escritorio)\"LA CARPETA QUE VOS QUIERAS"\Proyecto chero\asistencia_escolar\assets\login"



