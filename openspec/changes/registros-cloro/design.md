# Design: cloro-registro

## Architecture

### High-level architecture

The `registros-cloro` module follows the existing `app/documentos_oficiales/` architecture pattern with a layered approach:

```
Layer 1 - API (FastAPI):       Endpoints REST under /api/v1/registros-cloro
                               - Uses dependency-injected services
                               - Returns Pydantic schemas (ORM mode enabled)
                               - Auth: get_current_user / require_admin (kernel shared)

Layer 2 - Service:             Business rules and data operations
                               - cloro_registro_service.py
                               - Validates cloro ranges (< 0.5, 0.5-1.0, > 1.0)
                               - Assigns estado automaticamente
                               - Handles evidencia upload validation

Layer 3 - Repository/SQLModel: Direct SQLModel queries against SQLite (WAL)
                               - CloroRegistro table
                               - User FK relationship
                               - Indexes: (user_id, timestamp), estado

Layer 4 - UI (Flet):           Spanish-language views for mobile ingestion
                               - Quick form (~30s per measurement)
                               - History list with filters
                               - Evidence viewer
                               - Uses api_client.py existente
```

### Component diagram

```mermaid
graph TD
    A[FastAPI Server] --> B[cloro_registro_service.py]
    B --> C[SQLModel / SQLite]
    B --> D[api_client.py (Flet)]
    D --> A
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style C fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style D fill:#fff3e0,stroke:#fb8c00,stroke-width:2px
```

### Dependency diagram

```mermaid
graph LR
    subgraph Kernel Shared (por ADR-008)
        K1[core/security.py: hash_password, create_session_token]
        K2[api/deps.py: get_current_user, require_admin]
        K3[db/models.py: User, UserSession]
    end
    subgraph Registros-Cloro Module
        M1[routes/registros_cloro.py]
        M2[cloro_registro_service.py]
        M3[db/migrations.py: CloroRegistro table]
        M4[schemas.py: CloroRegistroCreate/Out/Filter]
        M5[views/registros_cloro/ (Flet)]
    end
    K1 --> M1
    K2 --> M1
    K3 -.-> M3
    M1 --> M2
    M1 --> M4
    M1 --> M5
    M2 --> M3
    style Kernel Shared fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Module fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

## API Surface

### Endpoints under `/api/v1/registros-cloro`

| Method | Path | Auth | Description | Request Schema | Response Schema |
|--------|------|------|-------------|----------------|-----------------|
| GET | `/` | user | Listado con filtros | `CloroRegistroFilter` | List[`CloroRegistroOut`] |
| GET | `/{id}` | user | Registro individual | path `id: int` | `CloroRegistroOut` |
| POST | `/` | user | Crear registro | `CloroRegistroCreate` | `CloroRegistroOut` |
| PATCH | `/{id}` | admin | Actualizar estado/evidencia | `CloroRegistroUpdate` | `CloroRegistroOut` |
| POST | `/{id}/evidencia` | admin | Subir evidencia | multipart file | `{url: str, stored: bool}` |

### Request/Response Schemas (additions to `api/schemas.py`)

```python
class CloroRegistroCreate(BaseModel):
    user_id: int
    cloro_ppm: float
    temperatura_c: float | None = None
    ph: float | None = None
    agua_temperatura_c: float | None = None
    notes: str | None = None

class CloroRegistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    timestamp: datetime
    cloro_ppm: float
    temperatura_c: float | None
    ph: float | None
    agua_temperatura_c: float | None
    estado: str  # dentro_limites / fuera_limites / revision_necesaria
    evidencia_url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

class CloroRegistroFilter(BaseModel):
    fecha_desde: str | None = None  # ISO date
    fecha_hasta: str | None = None  # ISO date
    usuario_id: int | None = None
    estado: str | None = None  # dentro_limites / fuera_limites / revision_necesaria
    cloro_min: float | None = None
    cloro_max: float | None = None

class CloroRegistroUpdate(BaseModel):
    estado: str | None = None
    evidencia_url: str | None = None
    notes: str | None = None
```

## Database Model

### Nueva tabla: `CloroRegistro` (SQLModel)

```python
class CloroRegistro(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(index=True)
    cloro_ppm: float
    temperatura_c: float | None = Field(default=None, nullable=True)
    ph: float | None = Field(default=None, nullable=True)
    agua_temperatura_c: float | None = Field(default=None, nullable=True)
    estado: str  # "dentro_limites", "fuera_limites", "revision_necesaria"
    evidencia_url: str | None = Field(default=None, nullable=True)
    notes: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now, index=True)
```

### Migración idempotente

- `Alter table` si la tabla ya existe (sin recrear)
- Índices: `idx_cloro_user_ts` en `(user_id, timestamp)`, `idx_cloro_estado` en `estado`
- No hay columnas que requieran `NOT NULL` constraints obligatorias (todos opcionales salvo `cloro_ppm` y `timestamp` a nivel de validación API)

## Validación de Negocio

### Rules de estado automático

| Condición `cloro_ppm` | Estado asignado |
|----------------------|-----------------|
| `cloro_ppm` < 0.5 | `dentro_limites` |
| 0.5 ≤ `cloro_ppm` ≤ 1.0 | `dentro_limites` |
| `cloro_ppm` > 1.0 | `fuera_limites` |
| `cloro_ppm` < 0 o `cloro_ppm` > 10 | Error 422 (validación API) |
| `timestamp` > `utc_now` + 1h | Error 422 (validación API) |
| Faltan `cloro_ppm` o `timestamp` | Error 422 (validación API) |

### Flujo de validación en service layer

1. Recibir datos del endpoint
2. Validar `cloro_ppm` en rango (0, 10] y no nulo
3. Validar `timestamp` no es fecha futura > 1h
4. Asignar `estado` automáticamente según tabla de reglas
5. Persistir en SQLite con FK a `users`
6. Devolver registro creado con estado asignado

## UI (Flet) — Vista Móvil

### Formulario de ingreso rápido (~30s)

```
┌─────────────────────────────────────┐
|   📊 Registro de Cloro               │
├─────────────────────────────────────┤
| Cloro (ppm):    [      ]             │
| Temperatura (°C): [      ]  opcional │
| pH:             [      ]  opcional   │
| Agua Temp (°C): [      ]  opcional   │
| Notas:          [                    ]│
├─────────────────────────────────────┤
|  [   ENVIAR   ]  [  CANCELAR  ]       │
└─────────────────────────────────────┘
```

### Validaciones en cliente (before send)

- `cloro_ppm` debe estar completo y ser número > 0
- `timestamp` se auto-llena con `datetime.utcnow()` (sistema)
- Si falta `cloro_ppm`, mostrar error en rojo y bloquear enviar

### Listado con filtros

```
Filtros:  [Desde: __]  [Hasta: __]  [Usuario:]  [Estado:]  [Cloro __..__]
```

### Evidencia

```
[Subir foto/archivo]  →  aceptar .png/.jpg/.pdf  < 10 MB
URL generada: https://...
```

## Rollback Plan (diseño)

Pre-apply: 
- Revertir `app/documentos_oficiales/db/migrations.py` a estado anterior
- Revertir `app/documentos_oficiales/api/schemas.py` a estado anterior
- Revertir `app/documentos_oficiales/api/routes/registros_cloro.py` a estado anterior
- Revertir `app/documentos_oficiales/ui/views/registros_cloro/` a estado anterior
- No hay datos existentes que perder — la tabla `CloroRegistro` es nueva y no afecta tablas actuales

Durante apply:
- Descartar ramas sin fusionar
- Revertir commits mergeados en orden inverso
- La base de datos y archivos subidos se conservan con el release pero no están vinculados a la nueva funcionalidad hasta nueva migration que los remueva

## Dependencies

- Python ≥ 3.10
- FastAPI + SQLModel + SQLite (WAL) + Flet (stack existente)
- Kernel shared (por ADR-008): `get_current_user`, `require_admin`, `bearer_scheme`
- `ruff check .` linter disponible
- `pytest` para verification

## Success Criteria (diseño)

- [] Diagrama de arquitectura aprobado y revisado por el equipo
- [] Superficie de API definida con schemas Pydantic completos
- [] Modelo SQL con tabla `CloroRegistro` y migration idempotente verificada
- [] Rules de validación de negocio documentadas y trazas a casos de prueba
- [] Componentes UI Flet diseñados en español, flujo ~30s verificado
- [] Dependencies con kernel shared (auth) confirmadas por ADR-008
- [] Rollback plan documentado y compatible con workflow actual

## Key Learnings (preliminares)

1. El diseño debe mantener consistencia con la arquitectura existente `app/documentos_oficiales/` (mismos patrones de importación, dependencias, convenios).
2. La extracción kernel shared por ADR-008 es crítica para el segundo módulo — debe estar completa antes de escribir cualquier route o service.
3. Los rangos de cloro (< 0.5 / 0.5-1.0 / > 1.0) son el núcleo de las reglas de negocio y deben definirse una sola vez, tanto en service como en validaciones cliente.
4. El patrón UI Flet + API FastAPI + SQLModel SQLite se mantiene coherente con el resto del proyecto.
5. El diseño facilita el presupuesto 400 líneas: el slice inicial (formulario + listado) tiene definición compacta.