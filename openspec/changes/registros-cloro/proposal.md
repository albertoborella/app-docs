# Proposal: registros-cloro

## Intent

Seguimiento y registro de mediciones de cloro en cadenas productoras lácteas pequeñas. El objetivo es mantener un historial digital verificable de lecturas de cloro para auditorías regulatorias, reemplazando procesos manuales en papel o spreadsheets que son propensos a errores y pérdida de datos. Las tecnólogas de calidad ingresarán mediciones (~30s por lectura) desde dispositivos móviles, el sistema validará automáticamente los rangos y asignará un estado de conformidad.

## Scope

### In Scope

- **Formulario de ingreso de medición**: captura de cloro_ppm, temperatura opcional, pH opcional, agua_temperatura opcional, notas libres. Diseño para ingreso móvil en ~30 segundos.
- **Validación automática**: rangos de cloro ( < 0.5 = dentro_limites; 0.5-1.0 = dentro_limites; > 1.0 = fuera_limites); rejection de valores negativos o > 10 ppm; timestamp requerido.
- **Asignación de estado**: `dentro_limites` / `fuera_limites` / `revision_necesaria` basado en la medición.
- **Historial listado**: vista con filtros por fecha, usuario, estado, rango de cloro ppm. Muestra: id, usuario, timestamp, cloro_ppm, estado, evidencia_url.
- **Evidencia opcional**: URL a archivo/foto subida; validación de extensión y tamaño < 10 MB.
- **Vinculación de usuario**: cada registro asociado a `user_id` quien tomó la lectura; uso de dependencias de auth existentes (`get_current_user`, `require_admin`) por ADR-008 (es el segundo módulo).
- **API REST**: endpoints GET/listado, GET/{id}, POST/crear, PATCH/{id}/actualizar estado, POST/{id}/evidencia.

### Out of Scope

- Autenticación y gestión de usuarios (ya existe en el kernel shared por ADR-008).
- Control de temperatura/pH como requisito obligatorio (son campos opcionales de enriquecimiento).
- Integración con sistemas externos de gestión de agua (solo registro local).
- Roles de permisos avanzados (solo `user` y `admin` heredados del kernel).
- Historialización completa (soft delete via `deleted_at` opcional, no versiónado).
- Despliegue en modo offline o ejecutable embebido (web HTTP cliente-server solo).

## Capabilities

### New Capabilities

- `cloro-registro-ingestion`: formulario móvil + API POST para registrar una medición de cloro con validación automática de rangos y asignación de estado.
- `cloro-historial-lecturas`: API GET con filtros por fecha, usuario, estado, rango ppm; vista de historial para tecnólogas de calidad.
- `cloro-evidencia`: subida y almacenamiento opcional de evidencia (foto/archivo) asociada a un registro.

### Modified Capabilities

- Ninguna — `openspec/specs/` está vacío; este es un nuevo dominio de requisito.

## Approach

1. **Kernel shared (por ADR-008)**: Extraer `auth_service.py`, `core/security.py`, `db/models.py` (User, UserSession) al núcleo compartido antes del primer código del módulo. Este es el segundo módulo, la extracción es crítica para evitar duplicación de sesión.
2. **Nuevo modelo SQL**: Tabla `CloroRegistro` con campos: id, user_id (FK→users), timestamp, cloro_ppm, temperatura_c (null), pH (null), agua_temperatura_c (null), estado, evidencia_url (null), notes (null), created_at, updated_at.
3. **Endpoints API**: `/api/v1/registros-cloro` con CRUD básico + filtros. Usar dependencias FastAPI existing (`get_current_user`, `require_admin`).
4. **UI Flet**: Vista en español para ingreso rápido (~30s) y listado con filtros. El cliente HTTP reutiliza `api_client.py` existente.
5. **Validación en dos niveles**: Cliente (pre-viaje, evitar envíos vacíos) y servidor (rangos, timestamps, extensiones).
6. **Ingestión móvil ~30s**: Timeout API configurado a 30s; cliente cola local en dispositivo; reintento exponencial cuando hay conexión; UI muestra estado de carga.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/registros-cloro/` | New | proposal, specs, design, tasks, verify-report |
| `openspec/config.yaml` | Later | re-run stack/test detection after module landed |
| `app/documentos_oficiales/api/` | New | routes/registros_cloro.py, schemas additions |
| `app/documentos_oficiales/services/` | New | cloro_registro_service.py con validaciones de negocio |
| `app/documentos_oficiales/db/models.py` | Modified | nueva tabla CloroRegistro (migration idempotente) |
| `app/documentos_oficiales/ui/` | New | views/registros_cloro/ en Flet, copy en español |
| `openspec/specs/` | New | domain specs for cloro-registro (después de specs) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Extracción kernel shared incompleta | Med | Verificar que auth_service, security, models queden en kernel antes de escribir cualquier código de módulo; test de importación cruzada |
| Presupuesto 400 líneas revisión excedido | Med | sdd-tasks pronostica chained PRs si el forecast indica riesgo; dividir en slices autonomos |
| Divergencia validación cliente-servidor | Bajo | Mismo código de validación en ambos lados; revisar reglas de rango y timestamps |
| Campo evidencia_url crece a blob storage | Bajo | Diseñar URL como referencia a storage path; migration futura si necesario |
| Móvil > 30s en conexiones lentas | Bajo | Timeout configurado 30s; UI muestra error amigable y cola local para reintento |

## Rollback Plan

Pre-apply: revert files `app/documentos_oficiales/api/routes/registros_cloro.py`, `app/documentos_oficiales/api/schemas.py`, `app/documentos_oficiales/db/migrations.py`, `app/documentos_oficiales/ui/views/registros_cloro/`. Durante apply: descartar ramas sin fusionar; revertir commits mergeados en orden inverso. La base de datos y archivos subidos se conservan con el release pero no están vinculados a la nueva funcionalidad hasta una nueva migration que las remueva. No hay pérdida de datos existentes — los registros de cloro son nuevos y no sobrescriben tablas existentes.

## Dependencies

- Python ≥ 3.10
- FastAPI + SQLModel + SQLite (WAL) + Flet (stack existente)
- `openspec/config.yaml` detección de testing actualizada después del landed
- Dependencias de auth existentes: `get_current_user`, `require_admin`, `bearer_scheme` (kernel shared por ADR-008)
- `ruff check .` linter disponible

## Success Criteria

- [ ] Modelo `CloroRegistro` creado en SQLite con migration idempotente; tabla existe y es queryable.
- [ ] Endpoint POST `/api/v1/registros-cloro` acepta `{cloro_ppm, timestamp, ...}` y devuelve 201 con estado asignado; valida rangos y rechaza valores inválidos.
- [ ] Endpoint GET `/api/v1/registros-cloro` con filtros `fecha_desde`, `fecha_hasta`, `usuario_id`, `estado`, `cloro_min`, `cloro_max` devuelve lista ordenada por timestamp desc.
- [ ] UI Flet en español: formulario de ingreso en ~30s + vista listado con filtros funcionales.
- [ ] Validación automática: `cloro_ppm < 0.5` → `dentro_limites`; `cloro_ppm > 1.0` → `fuera_limites`; valores fuera de rango devuelven error 422.
- [ ] Evidencia opcional: upload acepta `.png, .jpg, .pdf` < 10 MB; URL guardada en registro.
- [ ] Cada registro está vinculado a `user_id` quien tomó la lectura (usando dependencias auth existentes).
- [ ] Test suite: `pytest` pasa con cobertura mínima en las nuevas validaciones y endpoints.

### Next Step

Ready for `sdd-spec` phase: write delta specs with Given/When/Then scenarios for the new capabilities. The specs phase will create `openspec/specs/registros-cloro/spec.md` and `openspec/changes/registros-cloro/specs/registros-cloro/spec.md` (delta).

**Key Learnings**

1. La propuesta registró claramente la separación entre capabilities nuevas (ingestión + historial) y modified capabilities (ninguna, es un dominio nuevo).
2. El riesgo principal es la extracción kernel shared por ADR-008 como segundo módulo — debe verificarse antes de escribir código de módulo.
3. El budget 400 líneas requiere pronóstico de chained PRs; el slice inicial (formulario + listado) está dentro del budget si se implementa de forma compacta.
4. Las reglas de negocio de estado basado en rangos de cloro deben validarse tanto en cliente como en servidor para evitar divergencia.
5. El patrón de ingestión móvil ~30s depende del timeout API configurado y la experiencia UX de carga/reintento.