# Tasks: cloro-registro

## Tarea 1: Modelos y migración SQL

- **Qué crear**: `app/documentos_oficiales/db/migrations.py` — nueva tabla `CloroRegistro` con campos id, user_id (FK→users), timestamp, cloro_ppm, temperatura_c (nullable), pH (nullable), agua_temperatura_c (nullable), estado, evidencia_url (nullable), notes (nullable), created_at, updated_at. Migración idempotente con `Alter table` si ya existe.
- **Sub-tareas**:
  - [ ] Añadir clase `CloroRegistro(SQLModel, table=True)` con campos y foreign keys
  - [ ] Añadir índice compuesto en `(user_id, timestamp)`
  - [ ] Añadir índice en `estado`
  - [ ] Verificar migration `upgrade()` y `downgrade()` son idempotentes
- **Presupuesto**: ~80 líneas añadidas
- **Depende de**: Ninguna (puede iniciarse inmediatamente)
- **Hace posible**: Tareas 2 y 3 (service y routes necesitan la tabla)

## Tarea 2: Schemas Pydantic y endpoints API

- **Qué crear**: `app/documentos_oficiales/api/schemas.py` — añadir `CloroRegistroCreate`, `CloroRegistroOut`, `CloroRegistroFilter`, `CloroRegistroUpdate`. `app/documentos_oficiales/api/routes/registros_cloro.py` — 5 endpoints bajo `/api/v1/registros-cloro`: GET/listado con filtros, GET/{id}, POST/crear, PATCH/{id}/actualizar estado/evidencia, POST/{id}/evidencia.
- **Sub-tareas**:
  - [ ] Añadir schemas `CloroRegistroCreate`, `CloroRegistroOut`, `CloroRegistroFilter`, `CloroRegistroUpdate` en `api/schemas.py` con `model_config = ConfigDict(from_attributes=True)`
  - [ ] Crear `routes/registros_cloro.py` con FastAPI router y dependencias `get_current_user`, `require_admin`
  - [ ] Implementar lógica de validación de rangos en el service layer (cloro < 0.5 → dentro_limites, 0.5-1.0 → dentro_limites, > 1.0 → fuera_limites)
  - [ ] Implementar endpoints con validación de timestamp no futuro > 1h
  - [ ] Implementar upload de evidencia con validación de extensión (.png/.jpg/.pdf) y tamaño < 10 MB
- **Presupuesto**: ~200 líneas añadidas (schemas + routes)
- **Depende de**: Tarea 1 (necesita la tabla SQL para los schemas y FK references)
- **Hace posible**: Tarea 4 (service layer usa los schemas) y Tarea 5 (UI usa los endpoints)

## Tarea 3: Service layer — validación de negocio

- **Qué crear**: `app/documentos_oficiales/services/cloro_registro_service.py` — lógica de validación: rangos de cloro, asignación automática de estado, persistencia en SQLite con FK a users, manejo de evidencia opcional.
- **Sub-tareas**:
  - [x] Función `validar_cloro_ppm(cloro_ppm: float) → tuple[bool, str]` que retorne `(True, "dentro_limites")` si < 0.5 o 0.5-1.0, `(False, "fuera_limites")` si > 1.0, `(False, error_422)` si < 0 o > 10
  - [x] Función `asignar_estado(cloro_ppm: float) → str` que aplique la tabla de reglas automáticas
  - [x] Función `crear_registro(db: Session, registro: CloroRegistroCreate, user_id: int) → CloroRegistro` que persista y devuelva el registro con estado asignado
  - [x] Función `listar_registros(db: Session, filtros: CloroRegistroFilter) → List[CloroRegistro]` con filtros por fecha, usuario, estado, rango ppm
  - [x] Función `subir_evidencia(db: Session, registro_id: int, file: UploadFile) → dict` que valide y guarde la URL
- **Presupuesto**: ~120 líneas
- **Depende de**: Tarea 1 (necesita el modelo SQL CloroRegistro) y Tarea 2 (usa schemas Pydantic para entrada/salida)
- **Hace posible**: Tarea 4 (routes call service) y Tarea 5 (UI consumes endpoints)

## Tarea 4: UI Flet — vista móvil de ingreso rápido

- **Qué crear**: `app/documentos_oficiales/ui/views/registros_cloro.py` — formulario de ingreso en ~30 segundos con campos: cloro_ppm (obligatorio), temperatura_c (opcional), pH (opcional), agua_temperatura_c (opcional), notes (opcional). Botón ENVIAR que llama al API POST. Vista listado con filtros por fecha, usuario, estado, rango ppm. Componente de evidencia: upload .png/.jpg/.pdf < 10 MB, muestra URL generada.
- **Sub-tareas**:
  - [x] Formulario Flet con campos validados en cliente antes de enviar
  - [x] Auto-fill de `timestamp` con `datetime.utcnow()` en el envío
  - [x] Validación en cliente: cloro_ppm debe ser número > 0 y ≤ 10; si falta, error en rojo bloquear enviar
  - [x] Listado con filtros: `fecha_desde`, `fecha_hasta`, `usuario_id`, `estado`, `cloro_min`, `cloro_max`
  - [x] Componente upload: aceptar .png/.jpg/.pdf, límite 10 MB, mostrar URL guardada en el registro
  - [x] Estilo consistente con el resto de la app: theme.py, SharedPreferences para persistencia de tema
- **Presupuesto**: ~150 líneas (incluye tests de UI)
- **Depende de**: Tarea 2 (usa schemas y endpoints API definidos) y Tarea 3 (usa service functions)
- **Hace posible**: El usuario puede ingresar mediciones desde el móvil en ~30s

## Tarea 5: Tests y verificación

- **Qué crear**: `tests/test_registros_cloro.py` — suite de tests pytest que cubra: creación de registro con validación de rangos, listado con filtros, estado automático basado en valor de cloro, upload de evidencia con validación de tipo/tamaño, errores 422 para valores inválidos. Ejecutar `pytest` y verificar que todas las tests pasan.
- **Sub-tareas**:
  - [x] Test: crear registro con cloro_ppm=0.3 → estado="dentro_limites"
  - [x] Test: crear registro con cloro_ppm=0.8 → estado="dentro_limites"
  - [x] Test: crear registro con cloro_ppm=1.2 → estado="fuera_limites"
  - [x] Test: crear registro con cloro_ppm=-1 → error 422
  - [x] Test: crear registro con cloro_ppm=15 → error 422
  - [x] Test: listado con filtros por fecha, usuario, estado devuelve solo matches
  - [x] Test: upload evidencia .txt (extensión no permitida) → error 422
  - [x] Test: upload evidencia .pdf 12MB (tamaño excedente) → error 422
  - [x] Test: timestamp futuro > 1h → error 422
- **Presupuesto**: ~100 líneas de test code + ~50 líneas de configuración = ~150 líneas
- **Depende de**: Tarea 2 (usa schemas), Tarea 3 (usa service), Tarea 4 (usa endpoints) — puede iniciarse una vez las 4 tareas anteriores estén en progreso o completadas
- **Hace posible**: La fase `sdd-verify` y el criterio de éxito "Test suite pasa con cobertura mínima en las nuevas validaciones y endpoints"

## Resumen de presupuesto de líneas

| Tarea | Líneas añadidas | Prioridad |
|-------|----------------|-----------|
| 1. Modelos y migración SQL | ~80 | Primera (puede iniciar ya) |
| 2. Schemas y endpoints API | ~200 | Segunda (después de T1) |
| 3. Service layer validación | ~120 | Tercera (después de T1, T2) |
| 4. UI Flet vista móvil | ~150 | Cuarta (después de T2, T3) |
| 5. Tests y verificación | ~150 | Quinta (última, después de T1-T4) |
| **Total** | **~700 líneas** | |

### Presupuesto de revisión (400 líneas)

El total de ~700 líneas excede el presupuesto de 400 líneas para una sola revisión. Por lo tanto, según la estrategia `ask-on-risk`, se recomendarán **chained PRs** (PRs apilados/stacked) divididos en slices más pequeños:

- **Slice A (PR #1)**: Tareas 1 + 2 (modelos SQL + schemas API) — ~280 líneas, dentro del budget
- **Slice B (PR #2)**: Tareas 3 + 4 (service layer + UI Flet) — ~270 líneas, requeriría split o size:exception
- **Slice C (PR #3)**: Tarea 5 (tests) — ~150 líneas, puede ir en el último PR

Esto mantiene cada PR dentro o cerca del budget de 400 líneas, protegiendo la revisión del autor.

### Next Step

Listo para la fase `sdd-apply` después de completar las tasks, siguiendo la estrategia de chained PRs. El delivery_strategy cached es `ask-on-risk`: se preguntará al usuario si proceder con chained PRs o size:exception cuando el forecast indique riesgo.

**Key Learnings**

1. El desglose en 5 tareas principales con sub-tareas permite un progreso incremental y revisable.
2. El budget 400 líneas requiere chained PRs: el slice inicial (T1+T2, ~280 líneas) está dentro budget, los slices subsiguientes need split o exception approval.
3. Las dependencies entre tareas son lineales: T1→T2→T3→T4→T5, pero T5 (tests) puede paralelizarse una vez las 4 tareas de implementation estén en curso.
4. El patrón "hacerlo pequeño primero" — implementar el modelo y API antes que la UI — permite retroalimentación temprana del reviewer.