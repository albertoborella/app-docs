# Estrategia de despliegue

Cómo se arranca y distribuye el sistema por objetivo. El **destino de despliegue concreto y su operador siguen sin definir** (última pregunta P0 del diseño): este documento describe lo que el diseño ya fija, sin inventar infraestructura.

## Forma por objetivo (ADR-001)

| | Web | Escritorio | Móvil |
| --- | --- | --- | --- |
| Desplegables | 1 proceso (`uvicorn app.main:app`) | App Flet + API alcanzable | App Flet (APK/IPA) + API alcanzable |
| UI | Montada en FastAPI bajo `/flet-app` (incluye `/ws` y `/upload`) | `flet run app/ui` o ejecutable empaquetado | `flet build` con el mismo entry point |
| URL de la API | Loopback, mismo proceso | `DOCMANAGER_API_URL` | `DOCMANAGER_API_URL` (HTTPS) |

Restricción operativa fija: **un solo trabajador uvicorn** — SQLite tiene un único escritor (NFR-11).

## Variables de entorno

| Variable | Uso | Default |
| --- | --- | --- |
| `DOCMANAGER_STORAGE_DIR` | Directorio de binarios | `./var/storage` |
| `DOCMANAGER_API_URL` | URL de la API para escritorio/móvil | requerida en esos objetivos |

Los ajustes de sesión (TTL) viven en `app/core/config.py`.

## Instalación fresca

1. Desplegar la base de código y crear el esquema: `create_all` en el primer arranque de la app.
2. Crear el primer administrador en la terminal del operador:
   `python -m app.cli create-admin` (pide usuario y contraseña con `getpass`; se niega si ya existe un administrador, salvo `--force`).
3. Arrancar: `uvicorn app.main:app` (web+API) o la app Flet apuntando a `DOCMANAGER_API_URL`.

Mientras no exista ningún administrador, la API responde 401 y la interfaz muestra un mensaje en español que remite al operador al comando — no es un fallo (ADR-007).

Para desarrollo local en tu máquina (uv, `--reload`, Swagger, curl), ver `05-development-guide.md`.

## Evolución del esquema

Greenfield sin migración de datos. En v1, cambios de esquema por `ALTER` aditivos de SQLite; Alembic solo cuando un cambio rompiente lo justifique (NFR-13).

## Lo que no está definido (honestidad de la fuente)

| Tema | Estado |
| --- | --- |
| Proveedor/servidor de hosting, país, operador | `PENDIENTE` (P0 abierta) |
| HTTPS / certificados | Depende del destino; las apps escritorio/móvil deben usar HTTPS en producción |
| Contenedores (Docker/Podman) | Las fuentes no lo definen; no se afirma |
| CI/CD, ambientes (dev/staging/prod) | Las fuentes no lo definen; no se afirma |
| Distribución de la app móvil (tienda vs. sideload) | Depende del destino; no se afirma |
| Backups de base y archivos | Exportación/backup está fuera de alcance de v1 (spec); el operador deberá definirlo fuera del producto |
