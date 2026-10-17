# Objetivos del sistema

Objetivos derivados del brief del producto y de los artefactos SDD del cambio `dairy-doc-manager`. Solo se listan objetivos trazables a esas fuentes; no se inventan métricas de negocio.

## Objetivos de producto

| # | Objetivo | Cómo se verifica | Estado de la fuente |
| --- | --- | --- | --- |
| O1 | Centralizar la documentación oficial en un catálogo único respaldado por base de datos, sin partición por empresa ni tenant. | Un solo catálogo; toda consulta autenticada ve los mismos documentos. | `CONFIRMADO` |
| O2 | Mantener el catálogo vigente: el administrador agrega documentos, modifica cualquier campo y retira los obsoletos (con posibilidad de restaurarlos). | CRUD completo solo con rol administrador; retirado = oculto para usuarios, recuperable. | `CONFIRMADO` |
| O3 | Permitir al usuario normal localizar la documentación: ver el catálogo, buscar, filtrar y descargar el archivo de un documento activo. | Búsqueda sin coincidencias devuelve vacío sin error; descarga devuelve el binario. | `CONFIRMADO` |
| O4 | Eliminar el acceso anónimo: catálogo y archivos exigen sesión iniciada. | Petición sin token → 401 en toda la API. | `CONFIRMADO` |
| O5 | Provisionar cuentas exclusivamente desde el administrador: crear, editar, desactivar y reactivar; sin auto-registro ni flujos de aprobación. | No existe ruta de registro propio; cuenta desactivada no puede iniciar sesión y el registro permanece. | `CONFIRMADO` |
| O6 | Entregar la interfaz íntegramente en español neutro en todas las pantallas y objetivos (web, escritorio, móvil). | Revisión de etiquetas, acciones y mensajes en cada pantalla. | `CONFIRMADO` |

## Objetivos de calidad verificables

| # | Objetivo | Umbral | Fuente |
| --- | --- | --- | --- |
| Q1 | Revisión de rendimiento de búsqueda y listado registrada antes del release, con el volumen sembrado. | ≥ 300 documentos y 100 usuarios sembrados; tiempos medidos y anotados en el reporte. | `CONFIRMADO` (spec `document-management`, diseño) |
| Q2 | Toda columna usada por visibilidad de catálogo, búsqueda y filtro debe estar indexada. | Índice cubre cada columna filtrada. | `CONFIRMADO` (spec `document-management`) |
| Q3 | El almacenamiento de archivos debe operar de forma íntegra al volumen confirmado. | Cientos de archivos recuperables por usuarios autenticados. | `CONFIRMADO` (spec `document-file-storage`) |

## Sin definir (honestidad de la fuente)

- **Objetivos de negocio cuantitativos** (adopción, reducción de tiempo de búsqueda, auditorías superadas): el brief no los define; no se inventan.
- **Meta de latencia de búsqueda**: el diseño deja el objetivo de latencia como pendiente de confirmación; la revisión Q1 registra las medidas, pero el umbral exacto aún no está fijado (`SUPUESTO — requiere confirmación`).
