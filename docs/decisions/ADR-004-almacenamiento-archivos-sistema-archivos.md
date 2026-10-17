# ADR-004: Almacenamiento de archivos en el sistema de archivos, un directorio por documento

## Contexto

El sistema debe guardar los binarios reales de los documentos (PDF y otros formatos) y servirlos a usuarios autenticados. El destino de despliegue sigue sin definir (P0 abierta), el volumen confirmado es de cientos de archivos, y los nombres de archivo provienen de usuarios finales: cualquier diseño debe impedir *path traversal*.

## Decisión

Almacenamiento en el sistema de archivos, con ruta generada por el servidor:

```
$DOCMANAGER_STORAGE_DIR/            # por defecto ./var/storage, ignorado por git
  documents/{document_id}/file      # un solo binario vigente por documento (v1)
```

La tabla `document_files` guarda `original_filename`, `content_type`, `size_bytes`, `sha256` y `stored_path`. **El servidor genera todas las rutas: los nombres de archivo del cliente jamás tocan el sistema de archivos** (seguro contra traversal). La subida es un PUT multipart exclusivo del administrador, con lista de formatos permitidos (PDF, DOCX, XLSX, ODT, PNG, JPG) y límite de 25 MB — `CONFIRMADO` (usuario). Reemplazar sobrescribe en el lugar; no hay versionado de archivos en v1. La descarga es un GET en streaming; los documentos borrados suaves rechazan a no-administradores (404); la papelera del administrador puede recuperarlos.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| BLOBs dentro de SQLite | Infla la base y rompe el streaming de descarga. |
| S3 / almacenamiento de objetos | El destino de despliegue se desconoce todavía; innecesariamente complejo para cientos de archivos. |

## Consecuencias

- **Positivas**: la forma más simple de operar para cientos de archivos; traslúcido detrás de `file_service` (intercambiable en el futuro); rutas inmunes a traversal; huella sha256 de cada binario.
- **Negativas / riesgos**: los formatos y el límite de 25 MB están confirmados por el usuario; el almacenamiento es local al host (si en el futuro hay varias réplicas, deberá replantearse); sin versionado de archivos, un reemplazo pierde el binario anterior.
- `var/storage/` se ignora en git: los binarios de usuarios nunca se versionan.

Ver `../architecture/02-security.md` (endurecimiento de subida) y `../domain/data-model.md`.
