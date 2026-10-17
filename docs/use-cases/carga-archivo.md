# Caso de uso: Carga de archivo de documento (administrador)

Derivado del diagrama de secuencia "Upload (admin)" de `design.md` y del spec `document-file-storage`.

## Actor

- **Administrador del sistema**.

## Precondiciones

- Sesión iniciada con rol administrador.
- El registro del documento existe (creado previamente con `POST /documents`); para reemplazar un archivo de un documento retirado, el administrador opera desde la papelera.
- El archivo cumple la lista de formatos permitidos y el límite de tamaño (`CONFIRMADO`: PDF, DOCX, XLSX, ODT, PNG, JPG; 25 MB).

## Flujo principal

1. El administrador elige el documento y selecciona un archivo en el selector de archivos de la UI.
   - Web: `flet.fastapi` alimenta un archivo temporal de sesión vía `/upload`.
   - Escritorio/móvil: la UI obtiene la ruta local del archivo.
2. La UI envía `PUT /documents/{id}/file` (multipart, con `Authorization: Bearer`).
3. El servidor aplica `require_admin`, valida la lista de extensiones y content-type y el límite de tamaño.
4. El servidor carga el registro del documento (debe existir; un retirado solo puede reemplazarse siendo administrador).
5. El servidor escribe el binario en `documents/{id}/file` con **ruta generada por él** (el nombre del cliente nunca toca el sistema de archivos).
6. El servidor hace *upsert* de `document_files` con `sha256`, `size_bytes`, `original_filename` y `content_type`.
7. Responde 200 con los metadatos del archivo; la UI los muestra.

## Flujos alternativos

### A. Usuario normal intenta subir o reemplazar

- `require_admin` rechaza la petición con **403**; no se almacena ningún binario.

### B. Tipo de archivo no permitido

- Validación de la lista falla → **415**; no se escribe nada.

### C. Archivo excede el límite

- Validación de tamaño falla → **413**; no se escribe nada.

### D. Documento inexistente

- El registro no existe → **404**.

### E. Reemplazo de archivo vigente

- El documento ya tiene archivo: el PUT sobrescribe el binario en el mismo lugar y actualiza los metadatos (`document_files`). No historial de versiones en v1.

### F. Documento retirado

- Un administrador puede reemplazar el archivo desde la papelera; un usuario normal ni siquiera ve el documento (la descarga responde 404).

## Postcondiciones

- El binario del documento está almacenado, asociado al registro y disponible para descarga por usuarios autenticados (del documento activo).
