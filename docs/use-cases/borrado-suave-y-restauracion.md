# Caso de uso: Borrado suave y restauración de documentos

Derivado del diagrama de secuencia "Soft delete + restore" de `design.md`, del spec `document-management` y del ADR-005.

## Actor

- **Administrador del sistema**.

## Precondiciones

- Sesión iniciada con rol administrador.
- El documento existe.
  - Para retirar: el documento está activo (`deleted_at IS NULL`).
  - Para restaurar: el documento está retirado (`deleted_at` con valor) y se opera desde la papelera.

## Flujo principal (retirar documento obsoleto)

1. El administrador elige "Quitar documento obsoleto" (en el catálogo o en la vista correspondiente).
2. La UI envía `DELETE /documents/{id}` con `Authorization: Bearer`.
3. El servidor aplica `require_admin`.
4. El servidor actualiza el documento: `deleted_at = now`.
5. Responde **204**; la UI lo quita de la vista.
6. El registro y su archivo permanecen en el sistema; las consultas de catálogo filtran `deleted_at IS NULL`, así que el documento desaparece de todo listado, búsqueda y filtro del usuario normal.

## Flujo principal (restaurar)

1. El administrador abre la papelera de reciclaje (documentos con `deleted_at IS NOT NULL`).
2. Selecciona "Restaurar".
3. La UI envía `POST /documents/{id}/restore`.
4. El servidor limpia el marcador: `deleted_at = NULL`.
5. Responde 200; el documento **reaparece en el catálogo** con su archivo asociado intacto.

## Flujos alternativos

### A. Usuario normal intenta retirar o restaurar

- `require_admin` rechaza con **403**; el registro no cambia.

### B. Papelera vista por usuario normal

- La vista y el filtro `deleted=true` no exponen retirados a usuarios normales: no los listan (invisibilidad por diseño).

### C. Intento de borrado físico

- No existe en la API ni en la interfaz de v1: no hay endpoint ni acción que destruya el registro o el archivo (BR-11).

### D. Documento ya retirado, reintento de DELETE

- El documento no está en el catálogo activo; la operación sobre un registro ya retirado no cambia nada significativo (la política de idempotencia fina queda a la implementación; el estado final es "retirado").

### E. Restaurar un documento cuyo archivo fue reemplazado antes de retirarlo

- La restauración solo limpia `deleted_at`; el archivo vigente asociado se conserva y vuelve a estar disponible para descarga.

## Postcondiciones

- **Retirado**: el documento no es visible ni descargable por usuarios normales; sí figura en la papelera del administrador con su archivo.
- **Restaurado**: el documento vuelve al catálogo para todos los usuarios autenticados, tal como estaba antes del retiro.
