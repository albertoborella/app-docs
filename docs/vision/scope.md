# Alcance — dairy-doc-manager

Fronteras del primer slice del producto, derivadas de la propuesta y de la exploración (con la corrección explícita del usuario sobre móvil). El alcance es dinámico: actualícelo cuando el proyecto crezca.

## Dentro del alcance

| Elemento | Detalle | Estado |
| --- | --- | --- |
| CRUD de documentos | Exclusivo del administrador; el usuario normal solo ve, busca y filtra. | `CONFIRMADO` |
| Almacenamiento de archivos | El administrador sube PDF y otros formatos; el sistema guarda y sirve los binarios; el usuario normal descarga. | `CONFIRMADO` (decisión P0) |
| Gestión de cuentas por el administrador | Crear, editar, desactivar cuentas; nadie se auto-registra. Ampliación de alcance explícita, fuera del brief original. | `CONFIRMADO` (adición explícita) |
| Dos roles, inicio de sesión, catálogo único sin multi-tenant | Un solo catálogo compartido por toda la organización. | `CONFIRMADO` (decisión P0) |
| Cuerpo emisor como texto libre | Sin catálogos predefinidos de reguladores, países, jurisdicciones ni tipos de documento. | `CONFIRMADO` (decisión P0) |
| Objetivo móvil Flet | Misma base de código Python compilada con `flet build`; no es un proyecto nativo Swift/Kotlin separado. | `CONFIRMADO` (corrección del usuario, 2026-10-17) |

## Fuera del alcance

Lista de no-objetivos (la exploración §6 y la propuesta la mantienen, salvo la corrección de móvil):

- Verificación automatizada de cumplimiento, análisis de brechas u obligaciones.
- Firmas electrónicas, aprobaciones o flujos de revisión editorial.
- Notificaciones o envíos de correo ("documento actualizado").
- Multi-tenant / federación multi-empresa.
- OCR o indexación de texto completo del contenido de los archivos.
- Rastreo o sincronización de documentos desde el sitio del regulador.
- Presentación de trámites o generación de reportes hacia la autoridad.
- Tableros analíticos o estadísticas más allá de un listado simple.
- Proyectos nativos iOS/Android separados de la base de código Python.
- Acceso anónimo o catálogo público.
- Funcionalidades de autoservicio (recuperación de contraseña, perfiles) más allá del inicio de sesión.
- Exportación de auditorías; exportación/backup de la base.
- Borrado físico (hard delete) en v1.

> **Corrección de alcance (2026-10-17, decisión del usuario)**: la entrada original "aplicaciones móviles nativas" contradecía la decisión explícita del stack Flet (escritorio/móvil/web) y era incorrecta. Se restringe a *proyectos* nativos iOS/Android separados. El objetivo móvil de Flet — la misma base de código Python renderizada mediante el motor Flutter — **está dentro del alcance**. Ninguna fase posterior debe reintroducir una exclusión genérica de móvil a partir de esa lista.

## Volumen y operación

| Tema | Estado |
| --- | --- |
| Volumen | `CONFIRMADO`: cientos de documentos, hasta ~100 usuarios. |
| Destino de despliegue y operador | `PENDIENTE` — última pregunta P0 abierta en el diseño; condiciona HTTPS, hosting y distribución móvil. |

## Relación con otros documentos

- Reglas y requisitos: `../requirements/`.
- Decisiones técnicas que acotan el alcance (p. ej. borrado suave sin hard delete): `../decisions/`.
