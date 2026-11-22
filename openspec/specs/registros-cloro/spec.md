# Spec: cloro-registro

## Added Requirements

### Req: cloro_registro_ingestion_basic
**Given**: Una tecnóloga de calidad ingresa una medición de cloro a través de la UI móvil
**When**: El formulario envía `cloro_ppm` y `timestamp`
**Then**: El sistema valida que `cloro_ppm` sea un número positivo y ≤ 10, y que `timestamp` no sea fecha futura (más de 1 hora adelante es rechazado)
**And**: Si `cloro_ppm` < 0.5, el estado se asigna automaticamente a `dentro_limites`
**And**: Si `cloro_ppm` > 1.0, el estado se asigna automaticamente a `fuera_limites`
**And**: Si 0.5 ≤ `cloro_ppm` ≤ 1.0, el estado se asigna automaticamente a `dentro_limites`
**And**: El sistema devuelve 201 con el registro creado y el estado asignado

### Req: cloro_registro_historial_filtros
**Given**: Una tecnóloga de calidad solicita el listado de registros de cloro
**When**: La petición incluye filtros opcionales: `fecha_desde`, `fecha_hasta`, `usuario_id`, `estado`, `cloro_min`, `cloro_max`
**Then**: El sistema devuelve solo los registros que coinciden con todos los filtros proporcionados
**And**: Los resultados se ordenan por `timestamp` de forma descendente (más reciente primero)
**And**: Si no se proveen filtros, se devuelven todos los registros activos (sin deleted_at)

### Req: cloro_registro_evidencia_validacion
**Given**: Se intenta subir evidencia (foto/archivo) para un registro de cloro
**When**: El archivo tiene extensión `.png`, `.jpg` o `.pdf` y su tamaño es < 10 MB
**Then**: El sistema acepta el archivo y guarda la URL en el campo `evidencia_url` del registro
**And**: Si la extensión no está en la whitelist o el tamaño excede 10 MB, el sistema devuelve error 422

### Req: cloro_registro_usuario_vinculacion
**Given**: Cualquier endpoint de `registros-cloro` es llamado con un usuario autenticado
**When**: La dependencia `get_current_user` resuelve el `user_id` de la sesión activa
**Then**: Cada registro creado o actualizado tiene `user_id` vinculado al usuario autenticado
**And**: El usuario solo puede sus propios registros si no tiene rol `admin`; los admin pueden acceder a todos