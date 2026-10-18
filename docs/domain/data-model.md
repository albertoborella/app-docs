# Modelo de datos

Esquema físico en SQLite, derivado del modelo SQLModel del diseño (`design.md`, sección Data Model). Tablas, columnas, índices y relaciones tal como deben existir tras `create_all`.

## Convenciones

- Motor: **SQLite en modo WAL**, con `foreign_keys=ON` (ver `../architecture/00-architecture.md`).
- Tipos: SQLModel sobre Python ≥ 3.10; opcionalidad con PEP 604 (`str | None`), nunca `Optional`.
- Sin framework de migraciones en v1: evolución por `ALTER` aditivos hasta que un cambio justifique Alembic. Las columnas opcionales nuevas de `documents` (`country`, `topic`) se añaden a bases existentes con `app/db/migrations.py` (`ensure_document_columns`, idempotente), invocado por el CLI `create-admin`.
- Los binarios **no** viven en la base: solo sus metadatos en `document_files`; los archivos en `$DOCMANAGER_STORAGE_DIR/documents/{document_id}/file`.

## Tablas y columnas

### `users`

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `id` | INTEGER | clave primaria |
| `username` | TEXT | NOT NULL, UNIQUE, indexada |
| `password_hash` | TEXT | NOT NULL (bcrypt) |
| `role` | TEXT | NOT NULL (`admin` \| `user`) |
| `is_active` | BOOLEAN | NOT NULL, default TRUE, indexada |
| `created_at` | DATETIME | NOT NULL |
| `updated_at` | DATETIME | NOT NULL |

### `user_sessions`

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `id` | INTEGER | clave primaria |
| `token_hash` | TEXT | NOT NULL, UNIQUE, indexada (SHA-256 del token opaco) |
| `user_id` | INTEGER | FK → `users.id`, indexada |
| `created_at` | DATETIME | NOT NULL |
| `expires_at` | DATETIME | NOT NULL, indexada |

### `documents`

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `id` | INTEGER | clave primaria |
| `title` | TEXT | NOT NULL, indexada (`CONFIRMADO`) |
| `issuing_body` | TEXT | NOT NULL, indexada (`CONFIRMADO`) |
| `description` | TEXT | nullable (`CONFIRMADO`) |
| `document_type` | TEXT | nullable, texto libre (`CONFIRMADO`) |
| `country` | TEXT | nullable, indexada; opcional, búsqueda por contiene |
| `topic` | TEXT | nullable, indexada; opcional, búsqueda por contiene |
| `issued_on` | DATE | nullable (`CONFIRMADO`) |
| `deleted_at` | DATETIME | nullable, indexada; NULL = activo |
| `created_at` | DATETIME | NOT NULL |
| `updated_at` | DATETIME | NOT NULL |

### `document_files`

| Columna | Tipo | Restricciones |
| --- | --- | --- |
| `id` | INTEGER | clave primaria |
| `document_id` | INTEGER | FK → `documents.id`, **UNIQUE**, indexada (1 archivo vigente por documento) |
| `original_filename` | TEXT | NOT NULL |
| `content_type` | TEXT | NOT NULL |
| `size_bytes` | INTEGER | NOT NULL |
| `sha256` | TEXT | NOT NULL, indexada |
| `stored_path` | TEXT | NOT NULL, ruta generada por el servidor |
| `uploaded_at` | DATETIME | NOT NULL |

## Índices

| Índice | Tabla | Columna(s) | Propósito |
| --- | --- | --- | --- |
| Único en `username` | `users` | `username` | Identidad de login sin duplicados. |
| Único en `token_hash` | `user_sessions` | `token_hash` | Búsqueda directa de sesión por hash. |
| `user_id` | `user_sessions` | `user_id` | Sesiones por usuario (logout / desactivación). |
| `expires_at` | `user_sessions` | `expires_at` | Chequeo de expiración. |
| `is_active` | `users` | `is_active` | Filtro de cuentas activas. |
| `title` | `documents` | `title` | Búsqueda sobre metadatos. |
| `issuing_body` | `documents` | `issuing_body` | Búsqueda y filtro por emisor. |
| `country` | `documents` | `country` | Filtro por país (búsqueda por contiene). |
| `topic` | `documents` | `topic` | Filtro por tema (búsqueda por contiene). |
| `deleted_at` | `documents` | `deleted_at` | Consultas de papelera (`deleted_at IS NOT NULL`). |
| **Parcial** | `documents` | `deleted_at WHERE deleted_at IS NULL` | Catálogo por defecto: el listado activo es el caso frecuente. |
| `document_id` (único) | `document_files` | `document_id` | Integridad de 1 a 0..1 archivo por documento. |
| `sha256` | `document_files` | `sha256` | Integridad/huella de binarios. |

> NFR-02 exige que toda columna usada por visibilidad, búsqueda y filtro esté indexada; este conjunto cubre las columnas del diseño. Las dimensiones de filtro finales son `CONFIRMADO` (usuario).

## Búsqueda

- Búsqueda actual: `SQL LIKE` sobre las columnas de metadatos indexadas (en particular `title` e `issuing_body`); los filtros de catálogo (`document_type`, `issuing_body`, `country`, `topic`) también son `LIKE` por contiene.
- Vía de mejora documentada si la revisión de rendimiento (NFR-03) no alcanza la latencia deseada: **FTS5 sobre metadatos** (no sobre el contenido de los binarios — indexar contenido está fuera de alcance).

## Relaciones (integridad referencial)

| Relación | FK | Cardinalidad |
| --- | --- | --- |
| `user_sessions.user_id` → `users.id` | sí | N a 1 |
| `document_files.document_id` → `documents.id` | sí | 1 a 0..1 (UNIQUE) |

No existen tablas de empresas, tenants, notificaciones, auditorías ni obligaciones regulatorias: ver invariantes en `domain-model.md`.
