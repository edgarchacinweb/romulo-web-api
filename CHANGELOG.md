# Changelog - Sistema Don Rómulo Gallegos

## [Unreleased] - 2026-04-11

### Fixed
- **Generación de Boletas**: Corregida la duplicidad de materias en la boleta del estudiante.
  - Se añadió `DISTINCT` a la consulta de materias para evitar duplicados causados por registros múltiples en la tabla de horas académicas.
  - Se implementó una lógica de consolidación por **Nombre de Materia** en el backend. Ahora, si existen múltiples registros con el mismo nombre para un curso, se unifican en una sola fila, consolidando sus notas y sumando sus inasistencias.
  - Se prioriza el registro que contenga notas al realizar la consolidación, resolviendo el problema de filas vacías.
