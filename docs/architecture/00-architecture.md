# Arquitectura general

Vista técnica de alto nivel del Gestor de documentación oficial láctea: tecnologías, componentes y comunicación. Las decisiones grandes están registradas como ADR en `../decisions/`; los contratos en `01-api-design.md` y la seguridad en `02-security.md`.

## Stack (fijado por el usuario)

| Capa | Elección |
| --- | --- |
| Lenguaje | Python ≥ 3.10, tipado con PEP 604 (`X | None`; nunca `Optional`) |
| Backend | FastAPI + SQLModel |
| Base de datos | SQLite3 (WAL, `foreign_keys=ON`), un solo trabajador uvicorn |
| UI | Flet (web, escritorio, móvil — una sola base de código Python) |
| Cliente HTTP de la UI | httpx con encabezado *bearer* |
| Contraseñas | bcrypt |

Un solo proceso Python: la API REST es la fuente de verdad en todos los objetivos; la UI nunca accede a la base directamente (ADR-001, ADR-003).

## Flujo de datos

    Flet UI (web | escritorio | móvil)
         │  httpx + Bearer
         ▼
    FastAPI /api/v1  ── deps: get_current_user / require_admin
         ├── services ── SQLModel ── SQLite (WAL)         … metadatos
         └── file_service ── var/storage/documents/{id}/file  … binarios

1. La UI (cualquier objetivo) llama exclusivamente a la API por HTTP — en web, en loopback dentro del mismo proceso.
2. Las dependencies `get_current_user` y `require_admin` aplican autenticación y rol antes de llegar a la lógica.
3. Los servicios de dominio (`auth`, `user`, `document`, `file`) contienen las reglas; la base guarda metadatos; el sistema de archivos guarda binarios.

## Componentes

| Ruta | Rol |
| --- | --- |
| `pyproject.toml` | Dependencias pineadas: fastapi, uvicorn, sqlmodel, flet (+ `flet.fastapi`), httpx, bcrypt; pytest, ruff |
| `app/main.py` | Factoría de la app; routers; montaje de `flet.fastapi`; `create_all` |
| `app/cli.py` | `argparse` + `getpass`; comando `create-admin` (bootstrap del primer administrador, ADR-007) |
| `app/core/config.py` | Ajustes por variables de entorno (directorio de almacenamiento, TTL de sesión) |
| `app/core/security.py` | Hash/verificación de contraseñas; emisión/verificación de tokens |
| `app/db/session.py` | Motor SQLite (WAL, claves foráneas activas) |
| `app/db/models.py` | Modelos de tablas (Role, User, UserSession, Document, DocumentFile) |
| `app/services/*.py` | Reglas de dominio (`auth`, `user`, `document`, `file`) |
| `app/api/deps.py` | `get_current_user`, `require_admin` |
| `app/api/routes/*.py` | Superficie HTTP: `auth`, `users`, `documents`, `files` |
| `app/ui/**` | Vistas Flet + `api_client.py`; el copy en español neutro vive **solo** aquí |
| `tests/` | Unidad (servicios/seguridad), integración (API + SQLite temporal + almacenamiento temporal), contrato del cliente de UI |
| `var/storage/` | Binarios en runtime, ignorados por git |

## Puntos de entrada

| Comando | Propósito |
| --- | --- |
| `uvicorn app.main:app` | Web + API (un solo proceso) |
| `python -m app.cli create-admin` | Bootstrap del primer administrador en una instalación fresca |
| `flet run app/ui` | Escritorio (con `DOCMANAGER_API_URL` configurada) |
| `flet build` | Mismo entry point de UI compilado a móvil (APK/IPA) |

## Propiedades estructurales

- **Un desplegable en web**: API y UI montada comparten proceso (ADR-001).
- **Un solo punto de autorización**: todo pasa por HTTP con *bearer*; un solo camino de cliente (ADR-003).
- **Un solo escritor**: SQLite con un trabajador uvicorn; la arquitectura no asume escritura concurrente multi-proceso (NFR-11).
- **Metadatos vs. binarios separados**: la base nunca almacena archivos; el sistema de archivos nunca se ejecuta (ADR-004).
- **Bootstrap explícito**: ninguna cuenta de administrador se crea automáticamente (ADR-007).

## Documentos relacionados

- `01-api-design.md` — contratos HTTP.
- `02-security.md` — modelo de seguridad.
- `03-deployment.md` — despliegue por objetivo y arranque.
- `04-decisions.md` — índice de ADR.
- `05-development-guide.md` — arranque local, CLI del administrador y prueba de endpoints.
