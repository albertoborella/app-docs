# ADR-001: Forma de despliegue por objetivo (web, escritorio, móvil)

## Contexto

La interfaz debe llegar a tres objetivos (web, escritorio, móvil) con una sola base de código Python (Flet, decisión del usuario), y el sistema debe mantener un catálogo único compartido por todos los usuarios. El requisito de "sistema sencillo" y el hecho de que el catálogo viva en una base de datos única descartan cualquier solución con datos locales por cliente. Además, `flet.fastapi` es una API reciente que debe pinnearese.

## Decisión

Un **único proceso de API REST** es la fuente de verdad en todos los objetivos; la UI Flet siempre habla con el backend por HTTP, nunca in-process:

| | Web | Escritorio | Móvil |
|---|---|---|---|
| Proceso UI Flet | Montada en FastAPI: `app.mount("/flet-app", flet_fastapi.app(main))`, incluye `/ws` y `/upload` | `flet run` / ejecutable empaquetado; servidor Flet embebido | `flet build` apk/ipa; el mismo código Python corre en el dispositivo |
| Acceso a la API | HTTP en loopback, mismo proceso | HTTP(S) a `DOCMANAGER_API_URL` | HTTPS a `DOCMANAGER_API_URL` |
| Estado de autenticación | Token *bearer* en la memoria de sesión de Flet; verdad del lado servidor en `user_sessions` (sin cookie jar) | igual | igual |
| Desplegables | 1 proceso | App Flet + API alcanzable | App Flet + API alcanzable |

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Servidor Flet separado + API en todos los objetivos | Dos desplegables también en web: peor operación, sin beneficio. |
| Solo Flet con SQLite local por cliente | No hay catálogo compartido: rompe el requisito multiusuario. |
| API + SPA JavaScript | Viola el stack fijado por el usuario (Python/FastAPI/SQLModel/Flet). |

## Consecuencias

- **Positivas**: un solo desplegable en web; una sola base de código en los tres objetivos; sin *gateway*; un único borde de autorización HTTP, testeable de forma idéntica en todos los objetivos; aprovecha `flet.fastapi` ya verificado.
- **Negativas / riesgos**: escritorio y móvil necesitan un servidor alcanzable y configuración de URL (`DOCMANAGER_API_URL`); `flet.fastapi` es nuevo — se pinnea la versión exacta de `flet` en `pyproject.toml` y la primera tarea es un *spike* que pruebe `/ws` y la subida con selector de archivos antes de funcionalidad.
- El HTTP en loopback de web es despreciable al volumen confirmado (cientos de documentos, ~100 usuarios).

Ver también `../architecture/00-architecture.md` y `../architecture/03-deployment.md`.
