# ADR-006: Se permiten múltiples administradores

## Contexto

El modelo de roles tiene exactamente dos valores (`admin` y `user`) y el administrador concentra todas las operaciones de escritura (documentos, archivos, cuentas). El brief habla en singular de "el administrador", lo que dejó abierto si debe existir exactamente una cuenta administradora (exploración, concepto 9).

## Decisión

El modelo de dos roles admite **N cuentas de administrador**; la interfaz de gestión de cuentas puede crear administradores. No se impone unicidad en v1.

`CONFIRMADO` (usuario): se admiten varias cuentas de administrador en v1; si más adelante se exigiera un único administrador a la vez, se añadiría una guardia o un índice único parcial de forma **aditiva**, sin romper el esquema existente.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Restringir a exactamente un administrador (índice único / guardia ya en v1) | El usuario nunca lo exigió; complica el aprovisionamiento inicial (si la única cuenta se bloquea, hace falta intervención directa en la base) y es un requisito no confirmado. |

## Consecuencias

- **Positivas**: operación resiliente (varias cuentas administradoras evitan el punto único de bloqueo); alta de personal administrativo sin cambios de esquema; la restricción futura, si se necesitara, es aditiva.
- **Negativas / riesgos**: la superficie de poder de escritura se distribuye entre varias personas sin registro de auditoría (el audit trail está fuera de alcance en v1); decisión `CONFIRMADO` (usuario): si la restricción cambiara, deberá emitirse un ADR nuevo (los ADR son inmutables).

Ver `../domain/entities.md` (User) y `../requirements/business-rules.md` (BR-22).
