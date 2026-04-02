# Changelog de Cambios y Modificaciones

## [2026-04-01] Refactorización de Asignación de Secciones

### Añadido
- Nueva lógica de asignación para mantener un balance más equitativo de los estudiantes entre un máximo de 3 secciones por curso/año escolar.
- Función matemática `calcular_distribucion_secciones` que distribuye un total de alumnos garantizando un mínimo de 15 y máximo 30 estudiantes por cada sección activa.
- Función de backend en BD `balancear_secciones_curso` que actualiza los registros de `CursoEstudiante`.

### Modificado
- Archivo `routes/students.py`: Refactorizadas las rutas principales de registro y filtrado.
- La creación de la solicitud, tanto nueva (`/students/create`) como reinscripción (`/students/submit_reinscription`), ahora asigna la sección por defecto a `0` (quedando de forma implícita "Por asignar").
- Rutas de listado y previsualización (`/students/filter`, `/students/by_parent/<id>`): Cuando el valor numérico en la columna Sección de BD es `0`, el JSON de respuesta ahora devuelve el string "Por asignar" en vez de interpretarlo o tratar de convertirlo como A, B o C.
- Aprobación de solicitudes (`/students/approve/<id>`): Ahora el proceso de cambiar a 'inscrito' activa la función de re-distribución matemática de estudiantes dentro de las secciones correspondientes de su curso antes de hacer un commit persistente en BD.

### Eliminado
- Lógica de asignación antigua (`obtener_seccion_disponible`), la cual asignaba a la sección de manera serial hasta un máximo duro de 30 antes de desbordarse a la siguiente saltándose toda noción de balance mínimo.
