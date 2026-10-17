# Visión — Gestor de documentación oficial láctea

Las empresas productoras de productos lácteos deben cumplir la documentación y los requisitos oficiales impuestos por el organismo regulatorio. Ese seguimiento hoy se realiza de forma informal. El proyecto entrega un catálogo compartido: el administrador mantiene los documentos vigentes y los usuarios normales los consultan, buscan y descargan.

## Problema

| Elemento | Estado | Detalle |
| --- | --- | --- |
| Obligación regulatoria | `CONFIRMADO` | Las empresas productoras de productos lácteos deben seguir la documentación oficial del organismo regulatorio (brief del producto). |
| Gestión actual informal | `CONFIRMADO` (a nivel de declaración del problema) | El seguimiento no se resuelve bien hoy; el objetivo del proyecto es "resolver el inconveniente de gestionar la documentación oficial". |
| Fallas concretas del proceso actual | Desconocido | El brief no describe el proceso manual vigente (¿desactualización? ¿pérdida? ¿duplicados? ¿falta de búsqueda?). La exploración lo dejó como pregunta abierta; no se afirma nada más. |

## Usuarios

| Actor | Qué hace | Volumen confirmado |
| --- | --- | --- |
| Administrador del sistema | Único rol con escritura: crea, modifica y retira documentos; sube y reemplaza archivos; crea, edita y desactiva cuentas. | Se permiten varios administradores (decisión de diseño; ver `../decisions/ADR-006-multiples-administradores.md`). |
| Usuario normal | Solo lectura: ve el catálogo completo, busca, filtra y descarga archivos de documentos activos. | Hasta ~100 cuentas de usuario en total. |

No hay visitantes anónimos: todo uso del catálogo y de los archivos requiere una cuenta autenticada.

## Solución

Un catálogo único de documentos regulatorios, respaldado por una base de datos, con:

- **CRUD de documentos exclusivo del administrador** (`CONFIRMADO`).
- **Vista, búsqueda y filtro para el usuario normal** (`CONFIRMADO`).
- **Almacenamiento real de archivos**: el administrador sube PDF y otros formatos; el sistema los guarda y los sirve a los usuarios autenticados (`CONFIRMADO`).
- **Cuentas provisionadas por el administrador**: no existe auto-registro (`CONFIRMADO`; ampliación de alcance explícita respecto del brief).
- **Una sola base de código Python (Flet)** con despliegue web, escritorio y móvil (`CONFIRMADO` por decisión del usuario).

## Plataforma

La interfaz se construye una sola vez con Flet y se ejecuta en tres objetivos:

| Objetivo | Cómo corre |
| --- | --- |
| Web | UI Flet montada dentro del proceso FastAPI (`flet.fastapi`). |
| Escritorio | La misma UI empaquetada como aplicación nativa, contra la API por HTTP(S). |
| Móvil | La misma UI compilada a APK/IPA con `flet build`, contra la API por HTTPS. |

El móvil **está dentro del alcance**: es la misma base de código, no un proyecto nativo separado (corrección explícita del usuario; ver `scope.md`).

## Pendiente que afecta la visión

El **destino de despliegue y su operador** siguen sin definir (pregunta P0 abierta en el diseño). Condiciona HTTPS, hosting y distribución de la app móvil. No se afirma nada sobre ello en esta visión.

## Documentos relacionados

- `objectives.md` — objetivos verificables del sistema.
- `scope.md` — fronteras de alcance.
- `glossary.md` — términos del dominio (la raíz `../GLOSSARY.md` cubre términos SDD/técnicos).
