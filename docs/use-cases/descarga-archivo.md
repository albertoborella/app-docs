# Caso de uso: Descarga de archivo con autorización

Derivado del diagrama de secuencia "Download with authorization" de `design.md` y del spec `document-file-storage`.

## Actor

- **Usuario normal** o **Administrador** (cualquier sesión iniciada).

## Precondiciones

- Sesión iniciada (el acceso anónimo está prohibido).
- El documento existe y tiene un archivo asociado (`document_files`).
- Para el usuario normal: el documento está activo (`deleted_at IS NULL`). El administrador también puede descargar desde la papelera.

## Flujo principal

1. El actor selecciona "Descargar" en la vista del documento.
2. La UI envía `GET /documents/{id}/file` con `Authorization: Bearer`.
3. El servidor ejecuta `get_current_user`.
4. El servidor carga el documento y su `document_files`.
5. El documento está activo (o el actor es administrador): el servidor lee `documents/{id}/file` en streaming y responde 200 con los bytes y `Content-Disposition` (nombre original del archivo).
6. La UI entrega el archivo al actor:
   - Web: descarga del navegador.
   - Escritorio/móvil: diálogo de guardado.
7. El actor tiene el archivo en su dispositivo.

## Flujos alternativos

### A. Sin sesión

- Petición anónima → **401**; ningún byte se transfiere.

### B. Documento retirado y actor con rol usuario

- El servidor responde **404** (sin fuga de existencia: no se distingue "retirado" de "inexistente").

### C. Documento retirado y actor administrador

- El servidor sirve el archivo normalmente (acceso propio de la papelera de reciclaje).

### D. Documento sin archivo asociado

- El documento existe pero nunca se subió archivo: el comportamiento sigue el contrato de la ruta de descarga para un registro sin `document_files` (no afirmado con mayor detalle en el diseño; la implementación debe responder un error controlado, no un 500).

### E. Token expirado o sesión eliminada

- **401**; la UI vuelve al inicio de sesión.

## Postcondiciones

- En el flujo principal: el actor posee una copia local del binario vigente del documento.
- En el flujo B: el sistema no revela que el documento retirado existe.
