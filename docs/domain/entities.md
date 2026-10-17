# Entidades

Descripción detallada de cada entidad del modelo de dominio y sus atributos. Los atributos están tomados del modelo de datos del diseño (`design.md`, sección Data Model). La columna de estado preserva la distinción de las fuentes: `CONFIRMADO` = respaldado por el brief o por decisiones P0 del usuario; `CONFIRMADO` (usuario) = confirmado por el usuario en la revisión del diseño.

## Role (enumeración)

No es una tabla: es un enumeración de Python con dos valores exactos.

| Valor | Significado |
| --- | --- |
| `admin` | Administrador del sistema: único rol con escritura. |
| `user` | Usuario normal: solo lectura. |

## User (`users`)

Cuenta de acceso al sistema.

| Atributo | Tipo | Estado | Descripción |
| --- | --- | --- | --- |
| `id` | `int` (clave primaria) | diseño | Identificador interno. |
| `username` | `str` (único, indexado) | diseño | Nombre de usuario para iniciar sesión. |
| `password_hash` | `str` | `CONFIRMADO` (mecánica) | Hash bcrypt de la contraseña; jamás texto plano. |
| `role` | `Role` | `CONFIRMADO` | Rol exacto: `admin` o `user`. |
| `is_active` | `bool` (indexado, default `True`) | `CONFIRMADO` | Cuenta desactivada: no puede iniciar sesión; el registro permanece. |
| `created_at` | `datetime` | diseño | Alta de la cuenta. |
| `updated_at` | `datetime` | diseño | Última modificación. |

## UserSession (`user_sessions`)

Registro de un inicio de sesión vigente (token opaco, ADR-002).

| Atributo | Tipo | Estado | Descripción |
| --- | --- | --- | --- |
| `id` | `int` (clave primaria) | diseño | Identificador de la sesión. |
| `token_hash` | `str` (único, indexado) | diseño | SHA-256 del token; el token en claro solo lo tiene el cliente. |
| `user_id` | `int` (FK → `users.id`, indexado) | diseño | Titular de la sesión. |
| `created_at` | `datetime` | diseño | Momento del inicio de sesión. |
| `expires_at` | `datetime` (indexado) | `CONFIRMADO` (usuario) | Expiración (TTL de 12 h). |

## Document (`documents`)

Registro de una documentación oficial; el objeto central del catálogo.

| Atributo | Tipo | Estado | Descripción |
| --- | --- | --- | --- |
| `id` | `int` (clave primaria) | diseño | Identificador del documento. |
| `title` | `str` (indexado) | `CONFIRMADO` (usuario) | Título del documento. |
| `issuing_body` | `str` (indexado) | `CONFIRMADO` | Cuerpo emisor como texto libre introducido por el administrador. |
| `description` | `str \| None` | `CONFIRMADO` (usuario) | Descripción opcional. |
| `document_type` | `str \| None` | `CONFIRMADO` (usuario) | Tipo como texto libre; los catálogos de enumeración están prohibidos por requisito. |
| `issued_on` | `date \| None` | `CONFIRMADO` (usuario) | Fecha de emisión opcional. |
| `deleted_at` | `datetime \| None` (indexado) | `CONFIRMADO` (como mecanismo de borrado suave) | NULL = activo; con valor = retirado (papelera del administrador). |
| `created_at` | `datetime` | diseño | Alta del registro. |
| `updated_at` | `datetime` | diseño | Última modificación. |

## DocumentFile (`document_files`)

Metadatos del binario vigente de un documento; el archivo vive en el sistema de archivos, no en la base.

| Atributo | Tipo | Estado | Descripción |
| --- | --- | --- | --- |
| `id` | `int` (clave primaria) | diseño | Identificador del archivo. |
| `document_id` | `int` (FK → `documents.id`, **único**, indexado) | diseño | Relación 1 a 0..1 con el documento. |
| `original_filename` | `str` | `CONFIRMADO` (concepto de archivo) | Nombre original elegido por el administrador; solo se conserva como metadato. |
| `content_type` | `str` | diseño | Tipo MIME declarado; validado contra la lista de permitidos. |
| `size_bytes` | `int` | diseño | Tamaño; validado contra el límite (`CONFIRMADO`: 25 MB). |
| `sha256` | `str` (indexado) | diseño | Huella del binario. |
| `stored_path` | `str` | diseño | Ruta **generada por el servidor** (`documents/{id}/file`); nunca deriva del nombre del cliente. |
| `uploaded_at` | `datetime` | diseño | Momento de la subida. |

## Relaciones rápidas

- Un `User` tiene 0..N `UserSession`.
- Un `User` con rol `admin` crea y administra 0..N `Document`; el modelo no ata documentos a usuarios ni empresas.
- Un `Document` tiene 0..1 `DocumentFile` (único por `document_id`).
- El estado retirado no es una entidad: es el marcador `deleted_at` del propio `Document`.
