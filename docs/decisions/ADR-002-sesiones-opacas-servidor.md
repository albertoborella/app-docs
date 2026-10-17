# ADR-002: Autenticación con sesiones opacas en el servidor

## Contexto

El sistema requiere inicio de sesión para dos roles y prohíbe el acceso anónimo. La solución de autenticación debe funcionar de forma idéntica en web, escritorio y móvil (el móvil no tiene cookie jar de navegador), y la revocación debe ser trivial a la escala confirmada (cientos de documentos, ~100 usuarios). No existen flujos de autoservicio que justifiquen tokens sin estado.

## Decisión

Al iniciar sesión se emite un **token aleatorio opaco de 256 bits**; en la base de datos solo se persiste su **hash SHA-256** en `user_sessions` (con `expires_at`). Toda petición autenticada lleva `Authorization: Bearer <token>`. Las dependencies de FastAPI `get_current_user` (token → sesión → usuario; rechaza expirado, sesión muerta o `is_active=False`) y `require_admin` aplican la frontera. Cerrar sesión elimina la fila de sesión; desactivar una cuenta corta el inicio de sesión **y** las sesiones en vuelo en su siguiente petición.

Hash de contraseñas con la biblioteca mantenida `bcrypt` (no passlib) y TTL de sesión de 12 h — `CONFIRMADO` (usuario), confinado a `core/security.py`.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| JWT | A esta escala, la revocación exigiría consultar la base de todos modos; además suma superficie criptográfica y de configuración sin beneficio. |
| Sesiones por cookie | Las apps nativas de escritorio y móvil no tienen cookie jar; el patrón no es portable a los tres objetivos. |

## Consecuencias

- **Positivas**: revocación trivial en SQLite (borrar la fila); sin infraestructura de claves/firmas; una sola verdad del lado servidor; portable a los tres objetivos.
- **Negativas / riesgos**: cada petición resuelve sesión en la base (aceptable al volumen confirmado); el TTL y la librería `bcrypt` están confirmados: si cambian, el impacto queda confinado a `core/security.py`.
- La desactivación de cuentas surte efecto inmediato en la siguiente petición de sesiones ya abiertas.

Ver `../requirements/authentication.md` para el modelo completo y `../architecture/02-security.md`.
