# Visión general de la interfaz

Experiencia de usuario del Gestor de documentación oficial láctea. La UI se escribe una sola vez en **Flet** y corre en tres objetivos (ADR-001); todo el copy visible está en **español neutro** y vive únicamente en `app/ui/**` (FR-06).

## Principios

| Principio | Detalle | Fuente |
| --- | --- | --- |
| Español neutro en cada pantalla | Etiquetas, acciones y mensajes en español; sin excepciones por objetivo | spec `document-management` |
| Un solo camino de datos | Toda vista habla con la API mediante `app/ui/api_client.py` (httpx + *bearer*), también en web | ADR-003 |
| Dos mundos de permiso | El usuario normal ve catálogo; el administrador ve además las vistas de administración | spec, ADR-005 |
| Cero estados anónimos | Sin sesión no hay catálogo: la primera pantalla siempre es el inicio de sesión | spec `user-account-management` |

## Objetivos y sus diferencias

| Aspecto | Web | Escritorio | Móvil |
| --- | --- | --- | --- |
| Cómo corre | Montada en FastAPI (`/flet-app`) | `flet run app/ui` | `flet build` (APK/IPA) |
| Selección de archivo (subida) | Archivo temporal vía `/upload` de `flet.fastapi` | Ruta local del archivo | Ruta local del archivo |
| Descarga | Descarga del navegador | Diálogo de guardado | Diálogo de guardado |
| URL de API | Loopback (mismo proceso) | `DOCMANAGER_API_URL` | `DOCMANAGER_API_URL` (HTTPS) |

## Sesión en la UI

- Tras el login, el token *bearer* vive en la **memoria de la sesión de Flet**; no hay cookies.
- El rol devuelto por el login decide qué vistas se muestran.
- 401 en cualquier llamada = sesión vuelve al inicio de sesión; 403 = mensaje de permiso denegado (en español), sin cambios.

## Mapa de vistas

| Vista | Rol | Propósito | Doc |
| --- | --- | --- | --- |
| Inicio de sesión | ambos | Entrada única al sistema | `01-pages.md` |
| Catálogo | ambos | Listado, búsqueda, filtro, descarga | `01-pages.md` |
| Formulario de documento | administrador | Alta y edición de documentos | `01-pages.md` |
| Papelera de reciclaje | administrador | Documentos retirados: restaurar | `01-pages.md` |
| Gestión de cuentas | administrador | Crear/editar/desactivar cuentas, rol, contraseña | `01-pages.md` |

## Copy

El copy en español neutro se concentra en `app/ui/**` (el backend y las specs permanecen en inglés). No existe capa de internacionalización (i18n) en v1: un solo idioma por requisito.
