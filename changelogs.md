# Changelog de Cambios y Modificaciones

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
