# Changelog de Cambios y Modificaciones

## [2026-04-11] Refactor: Migración de consultas Lapso a PeriodoEscolarId

### Modificado
- **Backend (API)**: Se actualizaron las consultas SQL en `routes/lapsos.py` (`get_current_lapsos`, `create_lapsos`, `get_lapsos`, `list`) para utilizar la nueva clave foránea `PeriodoEscolarId` en lugar de la eliminada columna de texto `AñoEscolar`.
- **Backend (API)**: Se actualizó la consulta del reporte consolidado en `routes/assistance.py` (`get_admin_report_lapso`) para realizar un `JOIN` con la tabla `PeriodoEscolar` y extraer dinámicamente el año escolar desde sus fechas de inicio y fin. 
- **Backend (API)**: En `utils/lapso_rules.py`, se modificó la carga de lapsos para conectarse con `PeriodoEscolar` y utilizar únicamente aquellas reglas que se apliquen al período activo, aumentando la robustez temporal del sistema.
- **Formateo Seguro**: Las vistas de Frontend seguirán mostrando un texto como de costumbre, ya que las nuevas consultas en base de datos usan la función `CONCAT(EXTRACT(YEAR FROM pe."FechaInicio"), '-', EXTRACT(YEAR FROM pe."FechaFin")) AS "AñoEscolar"` para emular el formato antiguo y no romper el renderizado.

## [2026-04-10] Feat: Visualización dinámica de Notas para Administradores

### Añadido
- **Backend (API)**: Se actualizó la ruta `/calification/student/<student_id>` para realizar un `JOIN` entre las tablas `Nota` y `Lapso`. Esto permite devolver no solo la ponderación, sino a qué lapso numérico de 1 a 3 pertenece dicha nota.
- **Frontend (JS)**: Modificado `calificationsmanager.js` en el modal de Administrador para hacer fetch dual de materias e historial de calificaciones, e integrar la respuesta realizando un mapeo estricto por `MateriaId` y asignando la nota a su `LapsoNumero` correspondiente.
- **Cálculo Automático**: Aprovechando la función nativa Vanilla JS `updateSubjectSummary`, las notas inyectadas en los inputs son reconocidas inmediatamente, y la función recalcula en tiempo real el promedio de la materia, dictaminando dinámicamente si el estado final es Aprobado o Reprobado.

## [2026-04-09] Feat: Validación de días permitidos para registro de asistencia (Docente)

### Añadido
- **Backend (API)**: Nueva ruta `/assistance/allowed_days` que consulta la tabla `Horario` para devolver los días de la semana (Lunes a Viernes) en los que un docente tiene clases asignadas para una materia y sección específica.
- **Frontend (JS)**: Implementación de lógica dinámica en `assistancemanager.js` para cargar los días permitidos desde el backend al seleccionar la materia y sección.
- **Frontend (Validación)**: Se añadió una validación estricta al selector de fecha (`dateInput`). Si el usuario selecciona un día que no está en su horario para esa clase, el sistema muestra un mensaje de error descriptivo, limpia el campo de fecha y detiene el proceso de carga, asegurando la integridad de los registros de asistencia.
- **Frontend (Regla de Negocio)**: Se bloqueó la selección y el registro de fechas futuras mediante el atributo `max` en el calendario y una validación manual redundante que vacía el input y alerta al docente si intenta adelantar asistencias.
- **Frontend (UX)**: Mensajes de alerta personalizados que informan al docente exactamente qué días tiene permitidos para la sección seleccionada.

### Solucionado
- **Fix**: Se corrigió el error de validación prematura en el input de fecha de asistencias al escribir el año manualmente. Se mejoró la UX moviendo la alerta de "Día inválido" al evento de clic del botón "Cargar Estudiantes", permitiendo que el docente complete la fecha sin interrupciones.

## [2026-04-09] Feat: Validación estricta de teléfono para docentes

### Añadido
- **Frontend**: Se implementó validación de solo números y restricción de exactamente 7 dígitos para el campo de teléfono en el formulario de registro de docentes (`index.html`).
- **Backend**: Se robusteció la validación en la API para asegurar que el número telefónico contenga exactamente 7 dígitos numéricos, aplicando mensajes de error más descriptivos en las rutas de creación y actualización de docentes.

## [2026-04-09] Fix (v2): Corrección de ruta estática para Asistencias (Admin)

### Solucionado
- **Frontend (Layout)**: Se corrigió el enlace en `src/scripts/layout.js` cambiando el endpoint dinámico `/admin/asistencia/gestion` por la ruta estática `/app/admin/asistencia/admin_asistencia.html`. Este cambio resuelve el error 404 persistente cuando se navega desde el servidor de desarrollo del frontend, el cual no tenía visibilidad del endpoint de Flask.

## [2026-04-09] Fix: Corrección definitiva de enrutamiento en Asistencias (Admin)

### Solucionado
- **Backend (Config)**: Se configuró `utils/config.py` para soportar múltiples carpetas de plantillas, permitiendo que Flask busque archivos HTML tanto en la carpeta de aplicaciones como en la carpeta del frontend (`romulo-website`).
- **Backend (Router)**: Se actualizó la ruta en `routes/assistance.py` para usar `render_template` en lugar de `send_file`. El nuevo endpoint es `/admin/asistencia/gestion`, lo cual evita conflictos con rutas estáticas previas y asegura que la página se renderice con todos sus estilos y scripts.
- **Frontend (Layout)**: Se actualizaron los enlaces en `src/scripts/layout.js` y `src/components/layout/sidebar.html` para que apunten al nuevo endpoint de Flask. Esto soluciona de forma definitiva el error que mostraba un índice de directorio al usuario.



## [2026-04-06] Refactor: Período escolar automático y de solo lectura en Horarios

### Modificado
- **Backend (API)**: Se verificó la consistencia del endpoint `/school_term/get` para devolver el período escolar marcado como activo (`Activo = TRUE`).
- **Frontend (HTML)**: En la vista de gestión de horarios (`app/admin/horarios/index.html`), se reemplazó el elemento `<select>` de "Período Escolar" por un campo de texto de solo lectura (`readonly disabled`) y un campo oculto (`hidden`) para prevenir la selección manual errónea de períodos pasados.
- **Frontend (JS)**: Se actualizó `src/scripts/schedulemanager.js` para cargar automáticamente el período escolar activo al iniciar la página. Se eliminó la lógica de escucha de cambios (`change event`) en el filtro de período, forzando al sistema a trabajar siempre sobre el ciclo escolar vigente y evitar inconsistencias lógicas en la asignación de materias y docentes.

## [2026-04-06] Reparación del Módulo de Auditorías

### Solucionado
- **Backend**: Se corrigió y robusteció la consulta SQL en el método `filter` de `AuditoriaRep` (en `database/Auditoria.py`), cambiando de un `SELECT *` inseguro a un mapeo explícito de columnas de BD para evitar desajustes posicionales en la serialización de registros ante cambios de esquema.
- **Backend**: Se modificó `models/Auditoria.py` para formatear la fecha generada al formato estándar ISO 8601 (`isoformat()`), logrando así que el frontend pueda parsearla íntegramente, incluyendo la hora específica de cada acción y sin que el frontend pierda su trazabilidad en el objeto JS `Date`.
- **Frontend**: Se reparó el filtrado en cliente (`src/scripts/auditorymanager.js`); el conteo de "Acciones Hoy" ahora usa el prefijo `YYYY-MM-DD` de la fecha ISO evitando validaciones lógicas fallidas de compatibilidad, y previniendo posibles errores de variables.
- **Frontend**: La tabla principal ahora interpreta y formatea correctamente las fechas (`formattedDate`), previniendo caídas cuando la API devuelve los registros y mostrando finalmente los datos visuales.
- **Frontend**: **Fix: PDF en blanco en exportación de auditorías**. Se corrigió un error estructural donde el contenedor de reporte (`#print`) estaba anidado dentro de un elemento padre oculto durante la impresión. Se reestructuró el HTML para independizar el contenedor de impresión y se simplificó la lógica de JavaScript para delegar la visibilidad al motor de CSS mediante `@media print`.
- **Frontend**: **Feat: Paginación y botón 'Ver todo' en tabla de auditorías**. Se implementó un sistema de paginación por bloques de 50 registros para mejorar el rendimiento y la legibilidad de la vista. Se incluyeron controles de navegación (Anterior/Siguiente), indicador de rango dinámico y un modo de "Ver todo" que permite alternar entre la vista paginada y el listado completo original.
- **Frontend/Backend**: **Feat: Edición de Fecha de Fin en Período de Inscripción**. Se añadió la funcionalidad para corregir la fecha de finalización de los períodos de inscripción mediante edición inline directamente en la tabla. Se corrigieron inconsistencias en el nombrado de columnas de la base de datos en el backend para permitir actualizaciones seguras.




## [2026-04-02] Corrección en Estadísticas de Docentes

### Modificado
- **Backend**: Se corrigió el cálculo de `TotalDocentes` en la ruta `/school_term/<id>/estadisticas`. Ahora cuenta todos los docentes activos en el sistema en lugar de filtrar solo por aquellos con clases asignadas en el período.


## [2026-04-02] Validación de Edad por Grado

### Añadido
- **Frontend (UX)**: Implementación de validación en tiempo real en `studentsregister.js` para los campos de Fecha de Nacimiento y Grado.
- **Feedback Visual**: Mensaje de advertencia dinámico en el formulario de inscripción que alerta sobre inconsistencias de edad/grado y bloquea el botón de envío hasta que se corrija.
- **Backend**: Nueva función auxiliar `validar_edad_grado` que implementa reglas de negocio estrictas para la inscripción.
- **Backend**: Rangos de edad configurados: 1er Año (11-13), 2do Año (13-14), 3er Año (14-15), 4to Año (15-16), 5to Año (16-18).
- **Backend/API**: Validación de edad integrada en los endpoints `/students/create` y `/students/submit_reinscription/<id>`.

### Modificado
- **HTML**: Se eliminaron los límites de años estáticos (2008-2015) en el selector de fecha del formulario de inscripción para permitir una validación dinámica y adaptable.
- **Backend/Utils**: Función `validar_fecha_nacimiento`: Se eliminó la restricción de años fijos, convirtiéndola en una función genérica de validación de formato.
- Los procesos de registro y reinscripción ahora consultan dinámicamente el grado asignado al curso para aplicar la validación de edad correspondiente antes de cualquier operación en la base de datos.

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
