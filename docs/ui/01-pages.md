# Pantallas

Definición de pantallas, navegación y estados, derivada de las tareas de UI (fases 5 y 6 del plan), los diagramas de secuencia del diseño y los specs. La navegación fina no está especificada en detalle en las fuentes: lo que sigue es lo que el diseño compromete, sin inventar flujos.

## Inicio de sesión (ambos roles)

| Elemento | Definición |
| --- | --- |
| Campos | Usuario, contraseña |
| Acción | `POST /auth/login`; con éxito, redirige según rol |
| Error de credenciales | Mensaje en español; sin detalle de cuál de los dos campos falló |
| Estado sin administradores | 401 de la API → mensaje en español que indica al operador ejecutar `python -m app.cli create-admin` (ADR-007) |

## Catálogo (ambos roles, contenido idéntico)

| Elemento | Definición |
| --- | --- |
| Contenido | Lista de documentos no retirados (título, cuerpo emisor y metadatos disponibles) |
| Búsqueda | Texto libre sobre metadatos (`query` en `list_documents`) |
| Filtro | Dimensiones del diseño: tipo de documento, cuerpo emisor (`CONFIRMADO`) |
| Descarga | Acción "Descargar" por documento → `GET /documents/{id}/file` |
| Estado vacío | Catálogo sin documentos: mensaje en español, sin error |
| Búsqueda sin coincidencias | Lista vacía, sin error (escenario de spec) |

## Formulario de documento (administrador)

| Elemento | Definición |
| --- | --- |
| Alta | Campos del documento + envío `POST /documents` |
| Edición | Cargar valores actuales; `PATCH /documents/{id}` (modificar cualquier campo) |
| Archivo | Adjuntar o reemplazar vía selector de archivos → `PUT /documents/{id}/file` (la ruta por objetivo varía; ver `00-ui-overview.md`) |
| Errores de archivo | 415 (tipo no permitido) y 413 (tamaño excedido) con mensajes en español |

## Papelera de reciclaje (administrador)

| Elemento | Definición |
| --- | --- |
| Contenido | Documentos con `deleted_at` marcado (`GET /documents?deleted=true`) |
| Acciones | "Restaurar" (`POST /documents/{id}/restore`); el borrado físico no existe en la interfaz |
| Origen del retiro | La acción "Quitar documento obsoleto" (`DELETE /documents/{id}`) se invoca desde la vista administrativa del catálogo o del documento |
| Invisible para usuarios normales | La vista no se muestra ni se filtra para el rol `user` |

## Gestión de cuentas (administrador)

| Elemento | Definición |
| --- | --- |
| Contenido | Lista de cuentas (`GET /users`) |
| Acciones | Crear (`POST /users`), editar (`PATCH /users/{id}`): rol, activo/inactivo, contraseña administrada |
| Desactivar/reactivar | El mismo `PATCH` con `is_active`; la cuenta desactivada no puede iniciar sesión pero permanece listada |
| Sin autoservicio | Ningún "olvidé mi contraseña" ni registro propio en la interfaz |

## Estados transversales (los más fáciles de olvidar)

| Estado | Comportamiento |
| --- | --- |
| 401 (sesión perdida/expirada) | Vuelve al inicio de sesión |
| 403 | Mensaje de permiso denegado en español; la operación no se realizó |
| 404 | Documento oculto o inexistente se trata igual (sin fuga de existencia) |
| Cuenta desactivada con sesión abierta | La siguiente operación recibe 401 → inicio de sesión |
