# Guía de desarrollo local: backend, frontend y prueba de endpoints

Cómo levantar el backend y la UI de Flet en tu máquina, crear el primer administrador, probar los endpoints con Swagger o curl, y ajustar la interfaz (tema, colores). Para la estrategia de despliegue por objetivo, ver `03-deployment.md`.

## Camino rápido

1. Desde la raíz del proyecto, instalá las dependencias: `uv sync`
2. Creá el administrador (también crea el esquema de la base): `uv run python -m app.cli create-admin --username admin`
3. Arrancá el servidor: `uv run uvicorn app.main:app --reload`
4. Abrí Swagger UI: http://127.0.0.1:8000/docs

## Requisitos

- Python 3.10 o superior
- [uv](https://docs.astral.sh/uv/) (gestor de dependencias del proyecto)

## Crear el administrador

El comando `create-admin` (ADR-007) es la única forma de crear la cuenta inicial: no hay bootstrap automático por variables de entorno.

```bash
uv run python -m app.cli create-admin --username admin
```

- La contraseña se ingresa oculta por consola (`getpass`); no se pasa por argumentos.
- Si omitís `--username`, te lo pide de forma interactiva.
- Si ya existe un administrador, el comando se niega y no toca nada (ver siguiente sección).

**Importante — el orden importa:** este comando ejecuta `create_all` y crea las tablas en `var/app.db`. El arranque de la app todavía no crea el esquema (fase pendiente en `app/main.py`), así que ejecutalo al menos una vez antes de usar la API; si no, las consultas fallan porque las tablas no existen.

### Más de un administrador

Para agregar **otro** administrador (múltiples admins, ADR-006), usá `--force`:

```bash
uv run python -m app.cli create-admin --username ana --force
```

`--force` solo saltea la guarda de "ya existe un admin": crea un usuario **nuevo** con rol admin y no modifica ni borra al existente. Si el nombre de usuario ya está tomado, el comando falla con `Error: el nombre de usuario ya existe.` (mismo criterio que la API, que responde 409). Alternativa con una sesión de admin ya iniciada: `POST /api/v1/users` con `"role": "admin"`.

## Arrancar el backend

```bash
uv run uvicorn app.main:app --reload
```

- URL: http://127.0.0.1:8000 — las rutas de la API viven bajo `/api/v1`.
- `--reload` reinicia al detectar cambios: solo para desarrollo local.
- **Un solo trabajador**: SQLite tiene un único escritor (NFR-11); no levantes varios procesos uvicorn contra la misma base.
- Los comandos de esta guía se ejecutan desde la raíz del proyecto (donde está `pyproject.toml`).

## Variables de entorno

Todas son opcionales en desarrollo local.

| Variable | Uso | Default |
| --- | --- | --- |
| `DOCMANAGER_DB_PATH` | Ruta del archivo SQLite | `var/app.db` |
| `DOCMANAGER_STORAGE_DIR` | Directorio de binarios | `var/storage` |
| `DOCMANAGER_SESSION_TTL_HOURS` | TTL de sesión, en horas | `12` |

`DOCMANAGER_API_URL` no figura acá porque apunta la app Flet de escritorio/móvil a una API remota; no hace falta en desarrollo web local.

## Probar los endpoints

### Swagger UI (recomendado)

Con el servidor corriendo, abrí http://127.0.0.1:8000/docs. Para las rutas protegidas, usá el botón **Authorize** y pegá el token solo (Swagger agrega el prefijo `Bearer` solo).

### curl

Primero obtené un token:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "TU_PASSWORD"}'
```

La respuesta es `{"token": "...", "user": {...}}`. Guardalo:

```bash
TOKEN="EL_TOKEN_DEVUELTO"
```

Identidad de la sesión actual:

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

Crear un documento (administrador):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title": "Resolución 123", "issuing_body": "Senasa"}'
```

Listar documentos (cualquier sesión; filtros opcionales `query`, `document_type`, `issuing_body`; `deleted` solo tiene efecto para administradores):

```bash
curl -s "http://127.0.0.1:8000/api/v1/documents?query=Resoluci%C3%B3n" \
  -H "Authorization: Bearer $TOKEN"
```

Subir el archivo de un documento (administrador; formatos: `.pdf`, `.docx`, `.xlsx`, `.odt`, `.png`, `.jpg`; máximo 25 MB):

```bash
curl -s -X PUT http://127.0.0.1:8000/api/v1/documents/1/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/ruta/al/archivo.pdf"
```

Descargarlo (cualquier sesión; 404 si el documento está borrado y no sos admin):

```bash
curl -s http://127.0.0.1:8000/api/v1/documents/1/file \
  -H "Authorization: Bearer $TOKEN" -o archivo.pdf
```

Crear un usuario normal (administrador) para probar permisos:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username": "ana", "password": "secreto", "role": "user"}'
```

La superficie completa (edición de usuarios, borrado suave, restauración) y los códigos de error están en `01-api-design.md`.

## Frontend (Flet): correr y ajustar la UI

El frontend es una app Flet 1.0.4 (desktop o browser) que consume la API con el mismo `ApiClient` en todos los objetivos. Para probarla hace falta **dos terminales**: el backend y la UI.

### Modelo mental: dos procesos, tres formas de entrar

Todo lo que sigue se entiende con este esquema:

- **Hay siempre dos procesos**: el **API** (uvicorn, puerto 8000) y la **UI** (Flet). No existen tres apps: la UI es el mismo código (`app/ui`) corriendo en dos modos — *escritorio* (ventana nativa) o *web* (la notebook la sirve como sitio web, puerto 8550).
- **El API y la UI corren en la notebook.** El celular (u otra computadora) **nunca corre Python**: solo abre un navegador apuntado al sitio web que sirve la notebook. Por eso desde cualquier dispositivo ves la misma app, con la misma base y el mismo inicio de sesión.
- **Tres formas de entrar**, todas contra el mismo API:

| Desde dónde entrás | Comando / URL | Modo |
| --- | --- | --- |
| Ventana nativa en la notebook | `uv run flet run -r --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui` | escritorio |
| Navegador de la notebook | `http://localhost:8550` (con la UI en `--web`) | web |
| Navegador del celular, misma Wi-Fi | `http://<IP-de-la-notebook>:8550` (con la UI en `--web`) | web |

En escritorio el botón de cada fila es "Descargar" (diálogo de guardado); en web es "Abrir" (el PDF se abre en una pestaña nueva — en el celular, en el visor del teléfono). Los comandos exactos de cada modo están en *Camino rápido*, *Modos de ejecución* y *Acceso desde el celular*.

### Camino rápido

1. Terminal 1 — backend: `uv run uvicorn app.main:app --reload`
2. Terminal 2 — frontend (desde la raíz del proyecto): `uv run flet run -r --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui`
3. Se abre la ventana de escritorio (o una pestaña del browser con `--web`, ver abajo) en la pantalla de inicio de sesión. Usá el administrador creado con `create-admin`.

`DOCMANAGER_API_URL` no hace falta definirla en local: el `ApiClient` ya apunta por defecto a `http://127.0.0.1:8000`.

### Modos de ejecución

| Comando | Qué hace |
| --- | --- |
| `uv run flet run -r --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui` | Escritorio, con *hot reload* recursivo (recompila al guardar cambios en `app/ui/` y subdirectorios) |
| `uv run flet run -r -w --ignore-dirs .flet,__pycache__,views/__pycache__ --host "*" -p 8550 app/ui` | Sirve la misma app en el browser (abre una pestaña sola); útil si no querés ventana nativa |
| `uv run flet run -r -n --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui` | Escritorio con la ventana arrancando oculta (`-n` / `--hidden`) |

El flag `-r` (`--recursive`) es importante: las vistas viven en `app/ui/views/`, y sin `-r` el watcher no las observa. **`--ignore-dirs` también es obligatorio en desarrollo**: los directorios listados son escritura de runtime de Flet (no de tu código); sin ellos, el propio arranque de una sesión reinicia el servidor (ver gotcha siguiente).

### Gotchas verificados (Flet 1.0.4)

- **`uv sync` puede remover `flet-cli`** del venv (no está en `pyproject.toml`). No rompas la cabeza: el siguiente `uv run flet ...` lo reinstala solo. Siempre usá `uv run flet ...`, nunca `flet ...` a secas.
- Flet 1.0 eliminó `ft.app`: el entry point (`app/ui/main.py`) usa `ft.run(main)`.
- `FilePicker` en Flet 1.0.4 es un **Service auto-registrado**: con construirlo dentro de `main()` alcanza (`context.page` ya está seteado). **No va en `page.overlay`** — ahí el renderer lo recibe como control visible y muestra un placeholder "Unknown control: FilePicker".
- El `SnackBar` pasa por `page.show_dialog(ft.SnackBar(...))`, no `page.open` (pre-1.0).
- El 401 de login no distingue contraseña incorrecta de instalación sin administrador: el hint de `create-admin` aparece ante cualquier error de autenticación.
- **La ventana de Flet puede abrir DETRÁS del browser maximizado.** Si ves solo el logo de Flet o sentís que "no abre la pantalla de login", mirá la barra de tareas por la ventana **"Gestor documentario lácteo"** y traela al frente (alt+tab o clic en el ícono). Una corrida interrumpida (Ctrl+C, cerrar la terminal) puede dejar además un hijo huérfano `python -u app/ui/main.py` y una ventana vieja clavada en el logo: `pkill -f "app/ui/main.py"`, cerrá esa ventana y reintentá.
- **El cierre imprime ruido de Flutter, no errores de la app.** Al cerrar la ventana la terminal puede mostrar `embedder.cc (…): 'FlutterEngineRemoveView' returned 'kInvalidArguments'. Remove view info was invalid. The implicit view cannot be removed.` y dos WARNING `Attempted to set message handler on an FlBinaryMessenger without an engine`. Es el teardown del embedder GTK de Flutter en Linux; el proceso vuelve al prompt igual. Preocupate solo si ves `Segmentation fault` / `Emergency stop` o si el proceso queda colgado.
- **Arranque sano en cinco líneas** (con `-v`): `Starting up UDS server on /tmp/<id>` → `Flet app has started...` → `Starting Flet View app...` → `Flet client found in cache: …` → `App session started`. Si no llegan las cinco, el proceso Python de la UI no arrancó: mirá el error de la terminal antes de culpar a la UI.
- **`-r` sin `--ignore-dirs` reinicia el servidor en cada conexión (verificado).** Flet 1.0.4 apunta el runtime de la app a `app/ui/.flet/storage/` (`TMPDIR`, `FLET_APP_STORAGE_TEMP`, cwd = `…/data`) — dentro del árbol que el watcher observa. En modo web, cada pestaña que conecta escribe `index.html`/`manifest.json` bajo `.flet/storage/temp/tmp*/`; el watcher lo toma como cambio de código y **reinicia el proceso**, la pestaña pierde el WebSocket y vuelve al logo centrado de Flet… que al reconectar repite el ciclo: la página nunca termina de cargar. En escritorio, elegir un archivo con el `FilePicker` hace lo mismo. Solución: siempre `--ignore-dirs .flet,__pycache__,views/__pycache__` (el filtro es por ruta, por eso hay que listar `views/__pycache__` aparte). Con eso, el hot reload de `*.py` sigue funcionando y las conexiones ya no reinician nada — verificado midiendo el PID del hijo antes/después de un `GET /` + handshake WebSocket: sin el flag, dos reinicios; con él, PID estable.
- **Si la pestaña web quedó colgada en el logo**, no alcanza con recargar: el servidor puede haber quedado sin listener (el CLI sigue vivo pero el puerto 8550 ya no escucha). Cerrá la corrida con Ctrl+C y volvé a arrancar con el comando de arriba; recién ahí hacé un reload duro de la pestaña (Ctrl+Shift+R).

### Ajustar colores y tema

Los puntos de customización, de global a puntual:

1. **Tema general** — `app/ui/main.py`, función `main()`: hoy está `page.theme_mode = ft.ThemeMode.SYSTEM` (sigue el sistema). Cambialo a `ft.ThemeMode.LIGHT` o `ft.ThemeMode.DARK` para forzar.
2. **Paleta de la app** — en la misma función, agregá un esquema de color Material 3 sobre la página:

   ```python
   page.theme = ft.Theme(
       color_scheme=ft.ColorScheme(
           primary=ft.Colors.INDIGO,        # color de acción principal (botones)
           secondary=ft.Colors.TEAL,        # color secundario
           error=ft.Colors.RED,             # errores
           surface=ft.Colors.WHITE,         # fondo de superficies
           on_primary=ft.Colors.WHITE,      # texto sobre el primary
       ),
   )
   ```

   Los campos aceptados de `ft.ColorScheme` (verificados contra el paquete instalado) incluyen `primary`, `on_primary`, `secondary`, `error`, `surface`, `on_surface`, `outline`, y todo el resto de la paleta MD3. Los valores son los de `ft.Colors.*` (`INDIGO`, `TEAL`, `RED`, `ORANGE`, `GREEN`, `AMBER`, `DEEP_PURPLE`, …) o strings hexadecimales.
3. **Colores puntuales por control** — las vistas usan `ft.Colors.ERROR`, `ft.Colors.ON_SURFACE_VARIANT`, etc. directamente sobre `ft.Text` (por ejemplo el texto de error en `app/ui/views/sign_in.py`). Para un color custom en un control puntual: `ft.Text("...", color="#1976D2")` o `ft.Colors.with_opacity(0.7, ft.Colors.BLACK)`.
4. **Tipografía y spacing** — los `size=`, `spacing=`, `padding=` de cada view están en `app/ui/views/sign_in.py` y `app/ui/views/catalog.py`.

Con el *hot reload* activo, guardás el archivo y la ventana refleja el cambio sin reiniciar la sesión de la API (la sesión se pierde solo si se reinicia el proceso Python de la UI — el token vive en memoria del `ApiClient`).

### Flujo completo de prueba (UI + backend real)

1. Backend arriba (terminal 1).
2. `uv run flet run -r --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui` (terminal 2).
3. Login con el administrador → catálogo (vacío al principio).
4. Subí un documento con su PDF desde Swagger o curl (sección anterior) y refrescá el catálogo para verlo.
5. Probá la búsqueda y la descarga desde la UI.

### Acceso desde el celular (modo web)

Para usar la UI desde el navegador del celular (en la misma Wi-Fi que la notebook), la API y la UI deben escuchar en la red local, no solo en localhost:

```bash
# terminal 1 — API alcanzable desde la red local
uv run uvicorn app.main:app --reload --host 0.0.0.0
# terminal 2 — UI como sitio web (la IP es la de la notebook: hostname -I)
DOCMANAGER_API_URL=http://192.168.0.83:8000 uv run flet run -r -w --ignore-dirs .flet,__pycache__,views/__pycache__ --host "*" -p 8550 app/ui
```

- El celular, en la misma red Wi-Fi, abre `http://192.168.0.83:8550`.
- Al tocar "Abrir" en una fila del catálogo, el PDF se abre en una pestaña nueva con el visor del navegador (sin diálogo de guardado) y aparece un aviso breve explicando cómo volver al catálogo (atrás del navegador o cambiando de pestaña); en escritorio el botón sigue siendo "Descargar" con diálogo de guardado.
- **Token en la URL**: el botón "Abrir" navega a `GET /documents/{id}/file?token=…&inline=true`; el token de sesión queda en el URL. Es un atajo de uso local, no de producción — en producción se usarían URLs firmadas de vida corta.
- Si la página no carga, revisá el firewall de la notebook (debe permitir los puertos 8000 y 8550 en la red local).

## Checklist

- [ ] `uv sync` terminó sin errores
- [ ] `create-admin` creó el administrador (y con eso, el esquema)
- [ ] uvicorn responde en http://127.0.0.1:8000/docs
- [ ] `POST /auth/login` devuelve un token
- [ ] `GET /auth/me` con `Authorization: Bearer $TOKEN` devuelve el usuario
- [ ] `uv run flet run -r --ignore-dirs .flet,__pycache__,views/__pycache__ app/ui` abre la pantalla de inicio de sesión
- [ ] Login con el administrador llega al catálogo

## Documentos relacionados

- `01-api-design.md` — contratos HTTP y códigos de error.
- `03-deployment.md` — estrategia de despliegue por objetivo.
- `../ui/00-ui-overview.md` — visión general de la UI.
- `../decisions/ADR-007-primer-admin-cli.md` — por qué el bootstrap es un CLI.
