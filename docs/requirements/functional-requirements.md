# Requisitos funcionales

Requisitos que el sistema debe satisfacer, derivados de las tres especificaciones del cambio `dairy-doc-manager`. Cada fila es trazable al requisito de origen en la spec. Convención mínima: `FR-nn` como identificador local; la fortaleza contractual (SHALL/MUST de la spec original) se resume en la columna "Regla".

## Gestión de documentos (spec `document-management`)

| ID | Requisito | Regla | Fuente |
| --- | --- | --- | --- |
| FR-01 | El sistema mantiene **un** catálogo compartido de documentos regulatorios respaldado por base de datos, sin partición por empresa ni tenant. Todo usuario autenticado ve el catálogo completo. | SHALL, sin excepción | spec: Shared Regulatory Document Catalog |
| FR-02 | El CRUD de documentos es **exclusivo del administrador**: crear, actualizar y eliminar. El usuario normal no puede realizar ninguna de estas operaciones. | SHALL / MUST NOT | spec: Administrator-Only Document CRUD |
| FR-03 | El usuario normal puede **ver el catálogo, buscarlo y filtrar** la lista. Una búsqueda sin coincidencias devuelve vacío, sin error. | SHALL | spec: Normal-User View, Search, and Filter |
| FR-04 | **Retirar un documento obsoleto es un borrado suave**: el registro sale del catálogo para todos los usuarios, permanece en la base de datos, es visible solo para el administrador y es restaurable. No existe borrado físico (hard delete) en v1 ni un estado "obsoleto" visible para el usuario normal. | SHALL / MUST NOT | spec: Soft-Delete Handling |
| FR-05 | El **cuerpo emisor** de cada documento se guarda como texto libre introducido por el administrador. No se distribuye ningún catálogo codificado de reguladores, países, jurisdicciones ni tipos de documento. | SHALL / MUST NOT | spec: Free-Text Issuing Body |
| FR-06 | La **interfaz está íntegramente en español neutro** en todas las pantallas (catálogo, administración, inicio de sesión). Los textos de especificaciones y los identificadores de código permanecen en inglés. | SHALL | spec: Spanish User Interface |
| FR-07 | La exclusión de alcance se verifica: no existen cumplimiento automático, aprobaciones, notificaciones, multi-tenant, OCR/indexación de contenido, rastreo del regulador, trámites, analítica, proyectos iOS/Android nativos separados, acceso anónimo, autoservicio, exportación de auditorías, exportación/backup ni borrado físico. El objetivo móvil Flet usa la misma base de código Python. | SHALL NOT | spec: Scope Exclusions |

## Almacenamiento de archivos (spec `document-file-storage`)

| ID | Requisito | Regla | Fuente |
| --- | --- | --- | --- |
| FR-08 | El sistema almacena el **binario real** de cada archivo subido (PDF y otros formatos documentales). Subida, adjunto y reemplazo de archivos son **exclusivos del administrador**; el usuario normal no sube nada. El archivo queda asociado al registro del documento. | SHALL / MUST NOT | spec: Administrator Upload and Binary Storage |
| FR-09 | El sistema **sirve los binarios a usuarios con sesión iniciada**. El acceso anónimo a archivos está prohibido. | SHALL / MUST NOT | spec: File Serving to Authenticated Users |
| FR-10 | El usuario normal **puede descargar** los archivos de documentos. Para un documento retirado (borrado suave), la descarga de un no-administrador se rechaza. | SHALL | spec: Normal-User Download |

## Cuentas de usuario y autenticación (spec `user-account-management`)

| ID | Requisito | Regla | Fuente |
| --- | --- | --- | --- |
| FR-11 | Existen **exactamente dos roles**: administrador del sistema y usuario normal. Cada cuenta posee exactamente uno. | SHALL | spec: Two Roles |
| FR-12 | El administrador **crea, edita y desactiva** cuentas de usuario. No existen auto-registro ni flujos de aprobación en ninguna parte del sistema. Una cuenta desactivada no puede iniciar sesión y su registro permanece; puede reactivarse editándola. | SHALL / MUST NOT | spec: Administrator-Only Account Provisioning |
| FR-13 | **Todo acceso al catálogo y a los archivos requiere sesión iniciada.** No hay acceso anónimo. | SHALL / MUST NOT | spec: Authentication Required |
| FR-14 | Las operaciones de gestión de cuentas están restringidas al administrador; el usuario normal no puede crear, editar ni desactivar cuentas. | SHALL / MUST NOT | spec: Authorization Boundary for Account Management |
| FR-15 | El sistema soporta hasta ~100 cuentas de usuario (volumen confirmado), con inicio de sesión y administración operativos para todas. | SHALL | spec: Account Capacity |

## Campos y dimensiones confirmados

`CONFIRMADO` (usuario) en la revisión del diseño:

- Campos del registro de documento: `title`, `description`, `document_type`, `issued_on`.
- Alcance de la búsqueda y dimensiones de filtro: `query` de texto libre sobre metadatos indexados; filtro por `document_type`, `issuing_body` y `deleted` (solo administrador).

Siguen abiertos únicamente la meta de latencia de búsqueda y el destino de despliegue y operador.

Ver `non-functional-requirements.md` (volumen e indexado) y `authentication.md` (mecánica de credenciales).
