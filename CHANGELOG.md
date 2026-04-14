# Changelog - Sistema Don Rómulo Gallegos

## [1.1.0] - 2026-04-14

### Added
- **Indicador de Estatus Académico en Calificaciones**: Se implementó un sistema de detección y visualización del rendimiento académico por estudiante en el módulo de Calificaciones del panel de Administrador.
  - **Backend (`routes/calification.py`)**: Nuevo endpoint `POST /calification/academic_status` que calcula el promedio final de cada materia por estudiante (promediando las notas de los 3 lapsos del período escolar activo) y cuenta cuántas materias tienen un promedio ≤ 9 (reprobadas). Solo se evalúan materias con los 3 lapsos cargados.
  - **Frontend (`calificationsmanager.js`)**: Al cargar la lista de estudiantes, se invoca automáticamente el endpoint de estatus académico. El resultado se renderiza como una etiqueta (badge) debajo del nombre del estudiante.
  - **Etiquetas visuales (`calificationsmanager.css`)**: Se añadieron estilos para dos tipos de badge con animación de entrada:
    - 🟡 **Badge Advertencia** (ámbar): `"X materia(s) pendiente(s)"` — cuando el estudiante tiene 1 o 2 materias reprobadas.
    - 🔴 **Badge Peligro** (rojo): `"Estudiante reprobado"` — cuando tiene 3 o más materias reprobadas.
    - Sin badge si tiene 0 materias reprobadas.
  - La etiqueta se actualiza dinámicamente tras guardar nuevas calificaciones, sin necesidad de recargar la página.

## [Unreleased] - 2026-04-11

### Fixed
- **Generación de Boletas**: Corregida la duplicidad de materias en la boleta del estudiante.
  - Se añadió `DISTINCT` a la consulta de materias para evitar duplicados causados por registros múltiples en la tabla de horas académicas.
  - Se implementó una lógica de consolidación por **Nombre de Materia** en el backend. Ahora, si existen múltiples registros con el mismo nombre para un curso, se unifican en una sola fila, consolidando sus notas y sumando sus inasistencias.
  - Se prioriza el registro que contenga notas al realizar la consolidación, resolviendo el problema de filas vacías.
