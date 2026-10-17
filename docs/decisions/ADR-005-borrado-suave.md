# ADR-005: Borrado suave mediante `deleted_at`

## Contexto

El administrador debe retirar documentos obsoletos del catálogo. El diseño de producto exige que el registro salga del catálogo para todos los usuarios, que sea recuperable y que no exista un estado "obsoleto" visible para el usuario normal; el borrado físico como única opción perdería el registro y el archivo sin retorno. La pregunta de borrado suave vs. duro (exploración P1-Q10) se resolvió a favor del suave.

## Decisión

`documents.deleted_at: datetime | None`; **NULL = activo**. La operación de borrar pone la marca de tiempo; restaurar la limpia. El borrado físico **no** se expone en la API ni en la interfaz de v1. Las consultas de catálogo filtran por defecto `deleted_at IS NULL`; existe un índice parcial sobre `deleted_at` para ese caso frecuente; la papelera del administrador consulta `deleted_at IS NOT NULL`.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Borrado físico (hard delete) | Irreversible: pierde registro y archivo; sin recuperación posible; no cumple la restauración requerida. |
| Estado "obsoleto" visible para el usuario con advertencia | La spec es explícita: no existe estado "obsoleto" visible para el usuario normal; retirado = invisible en todo listado, búsqueda y filtro. |

## Consecuencias

- **Positivas**: recuperación trivial (limpiar una columna); auditoría de fondo posible (la papelera muestra qué se retiró); cero pérdida accidental de registros; el usuario normal nunca ve retirados (sin fuga de existencia: la descarga de un retirado devuelve 404).
- **Negativas / riesgos**: toda consulta debe acordar el filtro `deleted_at IS NULL` (el diseño lo centraliza en el servicio de documentos); sin hard delete, el espacio ocupado por retirados solo crece hasta que un proceso externo depure la base (fuera de alcance en v1); el índice parcial es una optimización que debe mantenerse si cambia el esquema.

Ver BR-09 a BR-12 en `../requirements/business-rules.md` y el caso de uso `../use-cases/borrado-suave-y-restauracion.md`.
