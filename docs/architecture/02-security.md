# Modelo de seguridad

Autenticación, autorización y protección de datos del Gestor de documentación oficial láctea. El modelo de sesión está en el ADR-002; aquí se documenta la superficie completa y su endurecimiento.

## Autenticación

- **Todo requiere sesión**: catálogo, archivos y gestión de cuentas; las peticiones anónimas reciben 401.
- **Token opaco de 256 bits** por sesión; en la base solo vive su hash SHA-256; TTL de 12 h — `CONFIRMADO` (usuario).
- **Contraseñas**: bcrypt vía la biblioteca `bcrypt`, jamás texto plano ni logs — `CONFIRMADO` (usuario).
- **Cierre de sesión** borra la fila; **desactivar cuenta** corta inicio de sesión y sesiones en vuelo en la siguiente petición.
- **Bootstrap**: el primer administrador nace solo del comando `create-admin` con `getpass` (sin eco); la contraseña nunca se acepta por argv, por entorno ni por fixture en el repositorio (ADR-007, NFR-07).

## Autorización

Dos roles, sin permisos granulares. Frontera aplicada en las dependencies `get_current_user` y `require_admin`:

| Superficie | Administrador | Usuario normal | Anónimo |
| --- | --- | --- | --- |
| Catálogo (ver/buscar/filtrar) | ✅ | ✅ | 401 |
| CRUD de documentos, borrado suave, restauración | ✅ | 403 | 401 |
| Papelera de reciclaje | ✅ | invisible (404) | 401 |
| Descarga de documento activo | ✅ | ✅ | 401 |
| Descarga de documento retirado | ✅ | 404 | 401 |
| Subida/reemplazo de archivo | ✅ | 403 | 401 |
| Gestión de cuentas | ✅ | 403 | 401 |

Toda violación deja el registro intacto (la spec exige "no change on refusal").

## Protección de archivos (endurecimiento de subida)

| Mecanismo | Detalle |
| --- | --- |
| Lista de formatos permitidos | PDF, DOCX, XLSX, ODT, PNG, JPG — `CONFIRMADO` (usuario); fuera de lista → 415 |
| Límite de tamaño | 25 MB — `CONFIRMADO` (usuario); excede → 413 |
| Rutas generadas por el servidor | `documents/{document_id}/file`; el nombre original del cliente solo se conserva como metadato — sin *path traversal* |
| Binarios jamás ejecutados | El proceso solo los escribe y los sirve en streaming; nunca los interpreta |
| Ubicación | `$DOCMANAGER_STORAGE_DIR` (por defecto `./var/storage`), fuera de git |

## Datos

- La base guarda solo metadatos y hashes; los binarios viven en el sistema de archivos (ADR-004).
- Sin datos sensibles de terceros en el alcance: el catálogo es documentación regulatoria de la empresa.
- Exposición de proceso declarada como no aplicable: sin subprocesos, automatización de VCS/PRs ni fronteras de integración de procesos; la superficie HTTP está cubierta por los contratos y las pruebas de autorización.

## Pendientes que condicionan seguridad

- **Destino de despliegue y HTTPS**: P0 abierta; no se afirma cifrado en tránsito hasta definir el operador (las apps móviles y escritorio deberán apuntar por HTTPS a la API).
