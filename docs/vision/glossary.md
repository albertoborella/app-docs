# Glosario del dominio — documentación regulatoria láctea

Términos del dominio de negocio del proyecto. Para términos SDD y del ecosistema técnico, ver `../GLOSSARY.md` en la raíz de `docs/`.

| Término | Definición |
| --- | --- |
| **Organismo regulatorio** | Autoridad oficial que impone la documentación y los requisitos que las empresas productoras de productos lácteos deben cumplir. Su jurisdicción concreta (país, entidad) no está definida en las fuentes; el sistema no la codifica. |
| **Documento oficial** | Registro de un requisito o documentación impuesta por el organismo regulatorio. Es el objeto central del catálogo. En el modelo físico: la tabla `documents`. |
| **Archivo de documento** | Binario asociado a un documento oficial (PDF, DOCX, etc.). Cada documento admite como máximo un archivo vigente en v1. En el modelo físico: la tabla `document_files`. |
| **Cuerpo emisor (issuing body)** | Texto libre introducido por el administrador que indica qué organismo emitió el documento. Sin catálogo predefinido: cualquier valor es válido. Requisito `CONFIRMADO`. |
| **Catálogo compartido** | Único repositorio de documentos de la organización, visible en su totalidad a todo usuario autenticado. No está particionado por empresa, tenant u organización. |
| **Documento obsoleto / retirado** | Documento que el administrador saca del catálogo mediante **borrado suave** (`deleted_at` con marca de tiempo). El registro y su archivo permanecen en el sistema; solo el administrador los ve en la papelera de reciclaje; son restaurables. No existe un estado "obsoleto" visible para el usuario normal ni borrado físico en v1. |
| **Papelera de reciclaje** | Vista exclusiva del administrador que lista los documentos retirados (`deleted_at IS NOT NULL`) y permite restaurarlos. |
| **Administrador del sistema** | Rol con permiso de escritura: CRUD de documentos, subida de archivos, alta/baja de cuentas. Se permiten varias cuentas de administrador (ADR-006). |
| **Usuario normal** | Rol de solo lectura: ve, busca, filtra y descarga archivos de documentos activos. No puede crear, modificar ni borrar nada. |
| **Cuenta provisionada** | Cuenta de usuario creada por un administrador. No existe auto-registro ni flujo de aprobación en el sistema. |
| **Sesión de usuario** | Registro de inicio de sesión: el servidor emite un token opaco aleatorio; solo se guarda su hash SHA-256 con fecha de expiración. Cerrar sesión o desactivar la cuenta elimina/inhabilita la sesión (ADR-002). |
| **Bootstrap del primer administrador** | Proceso de instalación fresca: tras crear las tablas, el operador ejecuta `python -m app.cli create-admin` en la terminal para crear la primera cuenta de administrador. Ninguna cuenta de administrador se crea automáticamente (ADR-007). |
| **Tenencia (tenancy)** | Pregunta de si el sistema sirve a una o varias empresas. Resuelta: **una sola organización**, catálogo único, sin multi-tenant. |
| **Búsqueda / filtro** | Búsqueda de texto libre (`LIKE` sobre metadatos indexados) y filtrado por dimensiones de metadatos (tipo de documento, cuerpo emisor; `deleted` solo para el administrador). No indexa el contenido de los archivos. |

## Términos deliberadamente sin definir

- **Jurisdicción regulatoria**: el brief no nombra país ni autoridad; el sistema guarda el cuerpo emisor como texto libre y no codifica jurisdicciones.
- **Versión de documento**: no hay semántica de versionado en v1; reemplazar el archivo sobrescribe el binario actual (sin historial de archivos).
- **Cumplimiento (compliance)**: el sistema gestiona documentos; no verifica obligaciones ni vencimientos.
