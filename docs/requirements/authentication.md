# Autenticación y autorización

Cómo se identifica quién usa el sistema y qué puede hacer. Requisitos de conducta en `functional-requirements.md` (FR-11 a FR-15); reglas en `business-rules.md` (BR-03 a BR-08, BR-20). Este documento describe el modelo confirmado y la mecánica de diseño.

## Modelo (confirmado)

| Aspecto | Decisión | Estado |
| --- | --- | --- |
| Acceso | Todo uso del catálogo y de los archivos exige una cuenta con sesión iniciada. Sin acceso anónimo. | `CONFIRMADO` |
| Roles | Exactamente dos: administrador del sistema y usuario normal; cada cuenta posee uno. | `CONFIRMADO` |
| Provisionamiento | Solo el administrador crea, edita y desactiva cuentas. Sin auto-registro ni aprobaciones. | `CONFIRMADO` |
| Recuperación de contraseña | No existe flujo de autoservicio; la contraseña la administra el administrador (cambio administrado desde la interfaz de cuentas). | `CONFIRMADO` (fuera de alcance el autoservicio) |
| Primer administrador | Comando de terminal `python -m app.cli create-admin` (patrón tipo Django `createsuperuser`); la contraseña se ingresa con `getpass` (sin eco), nunca por argumentos. | Decisión de diseño, ADR-007 |

## Mecánica de sesión (decisión de diseño — ADR-002)

| Paso | Comportamiento |
| --- | --- |
| Inicio de sesión | `POST /auth/login` con usuario y contraseña → se verifica bcrypt y `is_active`; se inserta una fila en `user_sessions` con un token aleatorio de 256 bits **solo hash SHA-256** y su `expires_at`; se devuelve el token al cliente. |
| Peticiones autenticadas | Cada petición lleva `Authorization: Bearer <token>`. El dependency `get_current_user` resuelve token → sesión → usuario; rechaza token expirado, sesión inactiva o cuenta `is_active=False`. |
| Control de rol | `require_admin` encadena sobre `get_current_user`; un usuario normal en una ruta de administrador recibe 403 y el registro no cambia. |
| Cierre de sesión | `POST /auth/logout` elimina la fila de sesión. |
| Desactivación | Al desactivar una cuenta, el inicio de sesión falla de inmediato y las sesiones vigentes se invalidan en su siguiente petición. |
| Expiración | TTL de sesión de 12 h — `CONFIRMADO` (usuario); confinado a `core/security.py`. |

### Por qué no JWT ni cookies

| Alternativa | Motivo de rechazo |
| --- | --- |
| JWT | La revocación en esta escala exigiría consultar la base de todos modos; además agrega superficie criptográfica y de configuración sin beneficio. |
| Sesiones por cookie | Las apps nativas de escritorio y móvil no tienen un *cookie jar* de navegador; el token opaco por encabezado funciona igual en los tres objetivos. |

## Frontera de autorización

| Superficie | Administrador | Usuario normal | Anónimo |
| --- | --- | --- | --- |
| Listado/búsqueda/filtro de catálogo | ✅ | ✅ | ❌ 401 |
| Crear/editar documentos | ✅ | ❌ 403 | ❌ 401 |
| Borrar suave / restaurar documentos | ✅ | ❌ 403 | ❌ 401 |
| Papelera de reciclaje (documentos retirados) | ✅ | invisible (404) | ❌ 401 |
| Descargar archivo de documento activo | ✅ | ✅ | ❌ 401 |
| Descargar archivo de documento retirado | ✅ (papelera) | ❌ 404 (sin fuga de existencia) | ❌ 401 |
| Subir/reemplazar archivo | ✅ | ❌ 403 | ❌ 401 |
| Gestión de cuentas (crear/editar/desactivar) | ✅ | ❌ 403 | ❌ 401 |

## Detalles de implementación (referencia)

- Dependency `get_current_user` y `require_admin` definidas en `app/api/deps.py` con firmas PEP 604 (`X | None`).
- Hash de contraseña y mint/verificación de token en `app/core/security.py`.
- Sin rutas de registro propio: `create-admin` por CLI es la única vía de creación de administradores en una instalación nueva.
