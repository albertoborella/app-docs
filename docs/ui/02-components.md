# Componentes de la interfaz

Piezas reutilizables de la UI Flet comprometidas por el diseño. El catálogo completo de componentes nacerá con la implementación; aquí solo se documenta lo que el diseño y el plan de tareas ya definen, sin inventar un design system.

## Cliente de datos (compartido por todas las vistas)

| Pieza | Detalle |
| --- | --- |
| `app/ui/api_client.py` (`ApiClient`) | Cliente httpx con *bearer*; único camino de datos de los tres objetivos (ADR-003). Opera: `login`, `list_documents` (con filtros), `upload_file`, `download_file`. Se prueba con httpx simulado (contrato). |

## Controles y widgets

| Pieza | Uso | Particularidades por objetivo |
| --- | --- | --- |
| Selector de archivos (FilePicker) | Subida/reemplazo de archivo del documento (solo administrador) | Web: el archivo pasa como temporal de sesión vía `/upload` de `flet.fastapi`; escritorio/móvil: ruta local |
| Acción por fila del documento | Obtiene el binario vía `GET /documents/{id}/file` | Web (celular): botón "Abrir" — pestaña nueva con visor directo (`?token=&inline=true`), sin diálogo de guardado; al tocarlo muestra un aviso breve que explica cómo volver al catálogo (atrás del navegador o cambiando de pestaña). Escritorio: botón "Descargar" — diálogo de guardado (comportamiento original) |
| Campo de búsqueda | Alimenta `list_documents(query=...)` | Idéntico en los tres objetivos |

## Contenedores de vista (unidades de navegación)

Definidos en el plan de tareas (fases 5 y 6); el detalle visual se implementa junto con cada vista:

| Vista | Rol | Notas de composición |
| --- | --- | --- |
| Inicio de sesión | ambos | Incluye el caso cero-administradores (mensaje que remite al comando CLI) |
| Catálogo (búsqueda/filtro/descarga) | ambos | Compartida; el administrador enlaza además a las vistas de gestión |
| Formulario de documento | administrador | Alta/edición + adjunto de archivo |
| Papelera de reciclaje | administrador | Listado + restaurar |
| Vista de cuentas | administrador | Alta/edición/desactivación, rol y contraseña |

## Convención de copy

Todo texto visible de estas piezas vive en `app/ui/**` y está en español neutro; no se externaliza a i18n en v1. Si una pieza cambia, su documentación se actualiza en el mismo cambio (regla del andamiaje de `docs/`).
