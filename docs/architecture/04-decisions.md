# Índice de decisiones técnicas

Registro de las decisiones de arquitectura del proyecto. Cada decisión vive como ADR inmutable en `../decisions/`; si una decisión cambia, se emite un ADR nuevo, nunca se edita el viejo.

| ADR | Decisión | Estado |
| --- | --- | --- |
| [ADR-001](../decisions/ADR-001-forma-despliegue-por-objetivo.md) | Forma de despliegue por objetivo: un proceso API como fuente de verdad; UI Flet montada en web, nativa en escritorio/móvil | Vigente |
| [ADR-002](../decisions/ADR-002-sesiones-opacas-servidor.md) | Autenticación con sesiones opacas en el servidor (token de 256 bits, hash SHA-256, sin JWT ni cookies) | Vigente (bcrypt y TTL: `CONFIRMADO`) |
| [ADR-003](../decisions/ADR-003-cliente-api-unico.md) | Un solo camino de cliente API (`api_client.py`) para los tres objetivos | Vigente |
| [ADR-004](../decisions/ADR-004-almacenamiento-archivos-sistema-archivos.md) | Almacenamiento de archivos en el sistema de archivos, un directorio por documento, rutas generadas por el servidor | Vigente (formatos y límite: `CONFIRMADO`) |
| [ADR-005](../decisions/ADR-005-borrado-suave.md) | Borrado suave mediante `deleted_at`; sin hard delete en v1 | Vigente |
| [ADR-006](../decisions/ADR-006-multiples-administradores.md) | Se permiten múltiples cuentas de administrador | Vigente (multi-administrador: `CONFIRMADO`; restricción futura sería aditiva) |
| [ADR-007](../decisions/ADR-007-primer-admin-cli.md) | Bootstrap del primer administrador por comando de terminal `create-admin` (patrón Django) | Vigente |

## Cómo leer este índice

- Los ADR capturan **qué se decidió y por qué**, con las alternativas descartadas; el **cómo** detallado está en `00-architecture.md`, `01-api-design.md` y `02-security.md`.
- "Vigente" significa: la decisión permanece en pie según el diseño actual; los paréntesis añaden notas de alcance (aspectos confirmados por el usuario o salvedades). Siguen abiertos únicamente el destino de despliegue y operador (ver `03-deployment.md`) y la meta de latencia de búsqueda.
