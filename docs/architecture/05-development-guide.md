# Guía de desarrollo local: arrancar el backend y probar endpoints

Cómo levantar el backend en tu máquina, crear el primer administrador y probar los endpoints con Swagger o curl. Para la estrategia de despliegue por objetivo, ver `03-deployment.md`.

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
- Si ya existe un administrador, el comando falla. Para crear una cuenta administradora adicional (múltiples admins, ADR-006), usá `--force`.

**Importante — el orden importa:** este comando ejecuta `create_all` y crea las tablas en `var/app.db`. El arranque de la app todavía no crea el esquema (fase pendiente en `app/main.py`), así que ejecutalo al menos una vez antes de usar la API; si no, las consultas fallan porque las tablas no existen.

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

## Checklist

- [ ] `uv sync` terminó sin errores
- [ ] `create-admin` creó el administrador (y con eso, el esquema)
- [ ] uvicorn responde en http://127.0.0.1:8000/docs
- [ ] `POST /auth/login` devuelve un token
- [ ] `GET /auth/me` con `Authorization: Bearer $TOKEN` devuelve el usuario

## Documentos relacionados

- `01-api-design.md` — contratos HTTP y códigos de error.
- `03-deployment.md` — estrategia de despliegue por objetivo.
- `../decisions/ADR-007-primer-admin-cli.md` — por qué el bootstrap es un CLI.
