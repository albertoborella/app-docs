# ADR-003: Un solo camino de cliente API para todos los objetivos

## Contexto

La UI Flet corre en web (montada en el mismo proceso FastAPI), escritorio y móvil. En web, el servicio de dominio está a un salto en proceso; en escritorio y móvil, detrás de HTTP. Sin una regla única, es tentador que web llame directamente a los servicios y oculte el borde de autorización en un objetivo.

## Decisión

Todas las vistas Flet ejecutan **todas** las operaciones a través de `app/ui/api_client.py` (httpx + encabezado *bearer*), incluida la UI web montada junto a la API: el cliente web usa HTTP en loopback como cualquier otro objetivo.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Llamadas directas a la capa de servicios en web | Duplica la lógica entre objetivos y oculta el borde de autorización en uno de ellos. |

## Consecuencias

- **Positivas**: un solo camino de código de cliente; un solo punto de aplicación de la autorización; paridad de objetivos en las pruebas (el contrato del cliente se prueba una vez con httpx simulado).
- **Negativas / riesgos**: en web se paga el costo de HTTP en loopback (despreciable al volumen confirmado); cualquier operación nueva debe pasar por `api_client.py` — es una disciplina de equipo, no un enforce del compilador.

Ver `../architecture/00-architecture.md` (flujo de datos) y el contrato en `../architecture/01-api-design.md`.
