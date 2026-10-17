# Requisitos no funcionales

Restricciones de calidad, rendimiento y seguridad del cambio `dairy-doc-manager`. Los volúmenes son `CONFIRMADO`; los umbrales marcados como tales se dejan explícitos.

## Volumen y rendimiento

| ID | Requisito | Umbral | Fuente |
| --- | --- | --- | --- |
| NFR-01 | Volumen operativo confirmado del sistema. | Cientos de documentos; hasta ~100 cuentas de usuario. | specs `document-management` y `document-file-storage` |
| NFR-02 | Toda columna usada por consultas de visibilidad de catálogo, búsqueda y filtro debe estar **indexada**. | Índice presente en cada columna filtrada (en el diseño: `title`, `issuing_body`, `deleted_at` + índice parcial `WHERE deleted_at IS NULL`, entre otros). | spec `document-management`, diseño |
| NFR-03 | Antes del release debe registrarse una **revisión de rendimiento de búsqueda** con el volumen sembrado y las medidas anotadas. | Sembrado ≥ 300 documentos y 100 usuarios; tiempos de consulta medidos y escritos en el reporte. | spec, diseño, tareas (fase 8) |
| NFR-04 | La búsqueda usa `SQL LIKE` sobre metadatos indexados; si las medidas no alcanzan la meta de latencia, la vía de mejora documentada es FTS5 sobre metadatos. | Meta de latencia concreta: `PENDIENTE` de confirmación. | diseño |
| NFR-05 | El almacenamiento y la recuperación de archivos deben operar íntegros al volumen confirmado. | Cientos de archivos recuperables por usuarios autenticados, sin corrupción. | spec `document-file-storage` |

## Seguridad

| ID | Requisito | Fuente |
| --- | --- | --- |
| NFR-06 | Las contraseñas se guardan con bcrypt (biblioteca `bcrypt`, no passlib — `CONFIRMADO`); jamás en texto plano ni en logs. | diseño |
| NFR-07 | El comando de creación del primer administrador lee la contraseña con `getpass` (sin eco) y **no la acepta como argumento de línea de comandos**: nunca aparece en el historial del shell, en `ps` ni en listados de procesos. | diseño |
| NFR-08 | Endurecimiento de subida: lista de formatos permitidos, límite de tamaño (`CONFIRMADO`: 25 MB), rutas generadas por el servidor y binarios almacenados **jamás ejecutados** por el proceso. | diseño |
| NFR-09 | El token de sesión es opaco (256 bits aleatorios); en la base solo se persiste su hash SHA-256. La revocación es trivial: borrar la fila de sesión. | diseño, ADR-002 |
| NFR-10 | Errores de autorización uniformes: 401 sin autenticar, 403 rol incorrecto, 404 oculto/inexistente, 413 excede tamaño, 415 tipo no permitido. | diseño |

## Operación

| ID | Requisito | Fuente |
| --- | --- | --- |
| NFR-11 | Un **solo trabajador (worker) uvicorn** por proceso: SQLite tiene un único escritor; la arquitectura no asume escritura concurrente multi-proceso. | diseño |
| NFR-12 | Base de datos en modo WAL con claves foráneas activas (`foreign_keys=ON`). | diseño |
| NFR-13 | Sin framework de migraciones en v1: evolución del esquema mediante `ALTER` aditivos hasta que un cambio justifique Alembic. | diseño |
| NFR-14 | Los binarios viven fuera del repositorio (`var/storage/`, ignorado por git); nunca se versionan archivos de usuario. | diseño |

## Pendientes (no afirmados)

- **Destino de despliegue, operador y HTTPS**: última pregunta P0 abierta; no se afirma infraestructura.
- **Meta de latencia de búsqueda** (NFR-04): `PENDIENTE` de confirmación.
- **CI/CD, contenedores y ambientes**: las fuentes no definen estrategia; ver `../architecture/03-deployment.md`.
