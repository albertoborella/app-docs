# Caso de uso: Inicio de sesión y control de roles

Derivado del diagrama de secuencia "Sign-in + role enforcement" de `design.md`, más el arranque de una instalación fresca (ADR-007).

## Actor

- **Usuario** (cualquier rol): persona que se identifica con usuario y contraseña.
- **Operador** (rol previo al sistema): quien ejecuta la terminal de la instalación.

## Precondiciones

- La base de datos y el esquema ya existen (`create_all` ejecutado).
- La cuenta existe y está activa (fue creada por el administrador) — salvo el primer administrador, ver Flujo alternativo A.
- El cliente (web, escritorio o móvil) puede alcanzar la API.

## Flujo principal

1. El actor ingresa usuario y contraseña en la pantalla de inicio de sesión.
2. La UI envía `POST /auth/login`.
3. El servidor carga el usuario por nombre de usuario, verifica la contraseña con bcrypt y comprueba `is_active`.
4. El servidor inserta una sesión (`user_sessions`) con el hash SHA-256 de un token aleatorio de 256 bits y su expiración, y responde 200 con `{token, user{role}}`.
5. La UI guarda el token en la memoria de la sesión de Flet y muestra la pantalla correspondiente a su rol (catálogo; el administrador además tiene vistas de administración).
6. En cada petición posterior la UI envía `Authorization: Bearer <token>`; el servidor resuelve la sesión (`get_current_user`) y, si la ruta lo requiere, exige el rol (`require_admin`).
7. El actor cierra sesión: la UI llama `POST /auth/logout` y el servidor elimina la fila de sesión.

## Flujos alternativos

### A. Instalación sin administradores (bootstrap)

- El intento de login falla con 401 porque no existe ninguna cuenta.
- La UI muestra un mensaje en español que indica al operador que ejecute `python -m app.cli create-admin` en la terminal.
- El operador ejecuta el comando (pide usuario y contraseña con `getpass`, sin eco) y, con la cuenta creada, repite el flujo principal.

### B. Cuenta desactivada o contraseña incorrecta

- El servidor responde 401; no se crea sesión; la UI muestra el error en español.
- Una cuenta desactivada también es rechazada en peticiones posteriores: `get_current_user` la descarta en su siguiente petición, cortando sesiones en vuelo.

### C. Control de rol en una operación administrativa

- Un usuario normal emite, por ejemplo, `POST /documents` con su token válido.
- El servidor ejecuta `get_current_user` (pasa) y `require_admin` (falla): responde **403** y el registro queda intacto.
- Un administrador en la misma operación: el servidor persiste el documento y responde 201.

### D. Token expirado o sesión eliminada

- `get_current_user` rechaza el token (expiración TTL o fila de sesión ausente): 401 y la UI vuelve a la pantalla de inicio de sesión.

## Postcondiciones

- En el flujo principal: existe una sesión vigente y el actor opera con los permisos de su rol.
- En el flujo C con usuario normal: ningún dato cambió.
