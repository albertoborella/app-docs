# Diseño de API y contratos

Superficie HTTP del backend (`/api/v1`) y contratos del cliente usado por la UI. Derivados de `design.md` (API Surface e Interfaces/Contracts). Firmas en PEP 604 (`X | None`).

## Superficie de endpoints

| Método y ruta | Auth | Propósito |
| --- | --- | --- |
| `POST /auth/login` | pública | Inicio de sesión: devuelve token opaco y datos del usuario (rol incluido) |
| `POST /auth/logout` | cualquier sesión | Elimina la fila de sesión |
| `GET /auth/me` | cualquier sesión | Usuario de la sesión actual |
| `GET /users` | administrador | Lista de cuentas |
| `POST /users` | administrador | Crea una cuenta con rol asignado |
| `PATCH /users/{id}` | administrador | Edita cuenta: rol, `is_active`, contraseña administrada |
| `GET /documents` | cualquier sesión | Listado/búsqueda/filtro; el parámetro `deleted` es solo para administradores (papelera) |
| `POST /documents` | administrador | Crea un documento |
| `PATCH /documents/{id}` | administrador | Modifica campos del documento |
| `DELETE /documents/{id}` | administrador | Borrado suave (marca `deleted_at`) → 204 |
| `POST /documents/{id}/restore` | administrador | Restaura (limpia `deleted_at`) |
| `GET /documents/{id}/file` | cualquier sesión (404 si está borrado y el rol es usuario) | Descarga en streaming del binario; acepta `?token=` y `?inline=` para abrir desde el browser del celular (ver notas) |
| `PUT /documents/{id}/file` | administrador | Subida/reemplazo multipart del binario |

## Códigos de error

| Código | Cuándo |
| --- | --- |
| 401 | Sin autenticar o token inválido/expirado |
| 403 | Rol incorrecto (p. ej. usuario normal en una ruta de administrador) |
| 404 | Recurso oculto o inexistente (incluye descarga de documento borrado para no-administradores — sin fuga de existencia) |
| 413 | Archivo excede el límite de tamaño |
| 415 | Tipo de archivo fuera de la lista de permitidos |

## Contratos del cliente de UI (`app/ui/api_client.py`)

Un único cliente (httpx + *bearer*) para los tres objetivos (ADR-003):

```python
class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None
    def login(self, username: str, password: str) -> UserOut
    def list_documents(self, *, query: str | None = None,
                       document_type: str | None = None,
                       issuing_body: str | None = None,
                       country: str | None = None,
                       topic: str | None = None,
                       deleted: bool | None = None) -> list[DocumentOut]
    def upload_file(self, document_id: int, local_path: str) -> FileOut
    def download_file(self, document_id: int) -> bytes
```

## Contratos de dependencias (`app/api/deps.py`)

```python
def get_current_user(token: str = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User
def require_admin(user: User = Depends(get_current_user)) -> User
```

## Notas de contrato

- **Búsqueda y filtros de `GET /documents`**:

  | Parámetro | Semántica |
  | --- | --- |
  | `query` | Texto libre (`LIKE` sobre todos los campos de metadatos: `title`, `issuing_body`, `document_type`, `country`, `topic`, `description`) |
  | `document_type` | Filtro por contiene (`LIKE '%…%'`) sobre `document_type` |
  | `issuing_body` | Filtro por contiene (`LIKE '%…%'`) sobre `issuing_body` |
  | `country` | Filtro por contiene (`LIKE '%…%'`) sobre `country` (opcional) |
  | `topic` | Filtro por contiene (`LIKE '%…%'`) sobre `topic` (opcional) |
  | `deleted` | Papelera; solo efecto para administradores |

  `LIKE` en SQLite insensible a mayúsculas para ASCII; el plegado de acentos queda fuera de alcance. Las dimensiones de filtro finales son `CONFIRMADO` (usuario).
- **Papelera**: `GET /documents?deleted=true` es privilegio de administrador; para usuarios normales el parámetro no expone retirados.
- **Subida**: multipart PUT; validación de lista de formatos y límite en el servidor; la respuesta devuelve los metadatos del archivo (nombre original, tipo, tamaño, sha256).
- **Descarga (`GET /documents/{id}/file`)** — dos parámetros de consulta opcionales, pensados para que el navegador del celular abra el PDF directamente en una pestaña nueva (no puede enviar header `Authorization`):

  | Parámetro | Semántica |
  | --- | --- |
  | `token` | Credencial alternativa al header *bearer*: misma validación de sesión (`resolve_session`); ausente o inválido (y sin header) → 401. **Solo esta ruta lo acepta**; el PUT de subida y el resto de rutas siguen siendo solo header |
  | `inline` | `true` → `Content-Disposition: inline` (el visor del navegador muestra el PDF); `false` (default) → `attachment` (descarga con diálogo). La lógica de filename (fallback ASCII + `filename*=UTF-8''…`) no cambia |

  Las reglas de autorización son las mismas por ambos caminos de credencial: documento borrado → 404 para no-administradores; registro o binario ausente → 404. Si coexisten header y query, el header tiene prioridad.
- **Sesión**: el token se transmite en `Authorization: Bearer` (y como `?token=` únicamente en la descarga de archivo, por la navegación directa del browser); no hay cookies.
- La versión del prefijo es `/api/v1`: un cambio incompatible justificaría `/api/v2`.
